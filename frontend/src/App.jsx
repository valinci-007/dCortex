import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import Header from "./components/Header.jsx";
import Message from "./components/Message.jsx";
import Composer from "./components/Composer.jsx";
import Samples from "./components/Samples.jsx";
import Sidebar from "./components/Sidebar.jsx";
import Watchlist from "./components/Watchlist.jsx";

const ACTIVE_KEY = "crew-ops-advisor:active-chat";
const DEV_KEY = "crew-ops-advisor:dev";

// Developer view: traces, timings, cost, provider and PII badges, sample questions. Off by
// default — a controller sees the answer, its reasoning and a trust signal. ?dev=1 turns it on.
function readDev() {
  try {
    const q = new URLSearchParams(window.location.search).get("dev");
    if (q != null) return q !== "0" && q !== "false";
    return localStorage.getItem(DEV_KEY) === "1";
  } catch {
    return false;
  }
}

function remember(id) {
  try {
    if (id) localStorage.setItem(ACTIVE_KEY, id);
    else localStorage.removeItem(ACTIVE_KEY);
  } catch {
    // storage unavailable — fine
  }
}

function remembered() {
  try {
    return localStorage.getItem(ACTIVE_KEY);
  } catch {
    return null;
  }
}

// Stored messages come back as {role, content, answer}; the UI renders {role, text|answer}.
function toView(m) {
  return m.role === "user"
    ? { role: "user", text: m.content, at: Date.parse(m.created_at) }
    : { role: "assistant", answer: m.answer, at: Date.parse(m.created_at) };
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [context, setContext] = useState(null);
  const [chats, setChats] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState(null);
  const [samplesOpen, setSamplesOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false); // narrow windows: slide-in panel
  const [voice, setVoice] = useState(null);
  const [directory, setDirectory] = useState(null); // crew id → name, joined locally (PII minimal mode)
  const [watchlist, setWatchlist] = useState(null);
  const [watchOpen, setWatchOpen] = useState(false);
  const [dev, setDev] = useState(readDev);
  const toggleDev = () => {
    setDev((v) => {
      try {
        localStorage.setItem(DEV_KEY, v ? "0" : "1");
      } catch {
        // ignore
      }
      if (v) setSamplesOpen(false);
      return !v;
    });
  };
  const bottomRef = useRef(null);
  const listRef = useRef(null);

  const refreshChats = useCallback(async () => {
    try {
      setChats(await api.chats());
    } catch (e) {
      setError(`Could not load conversations: ${e.message}`);
    }
  }, []);

  const openChat = useCallback(async (id) => {
    if (!id) {
      setActiveId(null);
      setMessages([]);
      remember(null);
      return;
    }
    try {
      const data = await api.chat(id);
      setActiveId(id);
      setMessages(data.messages.map(toView));
      remember(id);
      setError(null);
    } catch (e) {
      setError(`Could not open conversation: ${e.message}`);
      setActiveId(null);
      setMessages([]);
      remember(null);
    }
  }, []);

  useEffect(() => {
    api.health().then(setHealth).catch((e) => setError(`API unreachable: ${e.message}`));
    api
      .context()
      .then((ctx) => {
        setContext(ctx);
        // In minimal PII mode the model only ever sees crew ids; names are joined here, in
        // the controller's browser, from the local directory.
        if (ctx.pii_mode === "minimal") api.directory().then(setDirectory).catch(() => {});
      })
      .catch(() => {});
    api.voice().then(setVoice).catch(() => {});
    api.watchlist().then(setWatchlist).catch(() => {});
    refreshChats();
  }, [refreshChats]);

  useEffect(() => {
    // follow the latest answer in a conversation; a new chat opens at the top of its home screen
    if (messages.length === 0) listRef.current?.scrollTo({ top: 0 });
    else bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const ask = useCallback(
    async (question, chatId = activeId) => {
      const q = question.trim();
      if (!q || busy) return;
      setError(null);
      setDraft("");
      const pendingId = `p${Date.now()}`;
      setMessages((m) => [
        ...m,
        { role: "user", text: q, at: Date.now() },
        { role: "assistant", pending: true, id: pendingId, steps: [], text: "", phase: null, at: Date.now() },
      ]);
      setBusy(true);
      const patchPending = (fn) =>
        setMessages((m) => m.map((msg) => (msg.id === pendingId ? fn(msg) : msg)));
      const onEvent = (ev) => {
        if (ev.type === "tool_call") {
          patchPending((msg) => ({ ...msg, steps: [...msg.steps, { label: ev.label, done: false }], phase: null }));
        } else if (ev.type === "tool_done") {
          patchPending((msg) => {
            const steps = msg.steps.slice();
            const i = steps.findLastIndex((s) => !s.done && s.label === ev.label);
            const step = { label: ev.label, done: true, ok: ev.ok, summary: ev.summary, ms: ev.elapsed_ms };
            if (i === -1) steps.push(step);
            else steps[i] = step;
            return { ...msg, steps };
          });
        } else if (ev.type === "text") {
          patchPending((msg) => ({ ...msg, text: msg.text + ev.text }));
        } else if (ev.type === "phase") {
          patchPending((msg) => ({ ...msg, phase: ev.text }));
        }
      };
      try {
        const res = await api.askStream(q, chatId, onEvent);
        setActiveId(res.conversation_id);
        remember(res.conversation_id);
        setMessages((m) =>
          m.map((msg) => (msg.id === pendingId ? { role: "assistant", answer: res.answer, at: Date.now() } : msg)),
        );
        refreshChats();
      } catch (e) {
        setError(e.message);
        setMessages((m) =>
          m.map((msg) => (msg.id === pendingId ? { role: "assistant", answer: null, error: e.message, at: Date.now() } : msg)),
        );
      } finally {
        setBusy(false);
      }
    },
    [activeId, busy, refreshChats],
  );

  // On first load: a ?q= deep link starts a new chat; otherwise reopen the last chat.
  const booted = useRef(false);
  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) {
      ask(q, null);
      return;
    }
    const last = remembered();
    if (last) openChat(last);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const newChat = () => {
    setSidebarOpen(false);
    openChat(null);
  };

  const selectChat = (id) => {
    setSidebarOpen(false);
    openChat(id);
  };

  const renameChat = async (chat) => {
    const title = window.prompt("Rename conversation", chat.title);
    if (!title || title.trim() === chat.title) return;
    try {
      await api.renameChat(chat.id, title.trim());
      refreshChats();
    } catch (e) {
      setError(e.message);
    }
  };

  const deleteChat = async (chat) => {
    if (!window.confirm(`Delete "${chat.title}"? This cannot be undone.`)) return;
    try {
      await api.deleteChat(chat.id);
      if (chat.id === activeId) await openChat(null);
      refreshChats();
    } catch (e) {
      setError(e.message);
    }
  };

  const active = chats.find((c) => c.id === activeId) || null;
  return (
    <div className="app">
      <Header
        health={health}
        context={context}
        chat={active}
        busy={busy}
        samplesOpen={samplesOpen}
        onToggleSamples={() => {
          setWatchOpen(false);
          setSamplesOpen((v) => !v);
        }}
        watchCount={watchlist?.count ?? null}
        watchOpen={watchOpen}
        onToggleWatch={() => {
          setSamplesOpen(false);
          setWatchOpen((v) => !v);
        }}
        dev={dev}
        onToggleDev={toggleDev}
        onNewChat={newChat}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
      />
      <main className="main">
        {sidebarOpen && <div className="scrim" onClick={() => setSidebarOpen(false)} aria-hidden="true" />}
        <Sidebar
          chats={chats}
          activeId={activeId}
          busy={busy}
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          onNew={newChat}
          onSelect={selectChat}
          onRename={renameChat}
          onDelete={deleteChat}
        />
        <section className="chat">
          <div className="messages" ref={listRef}>
            {messages.length === 0 && (
              <div className="empty">
                <p className="empty-title">{active ? active.title : "Ask the desk a question."}</p>
                <p className="empty-sub">
                  {dev
                    ? `Lookups, consequences, legality, cover options — every answer shows its sources and the rule evidence behind it. Times are UTC; the snapshot is ${context?.snapshot_utc || "…"}. Conversations are saved and can be continued later.`
                    : "Rosters and reserves, duty limits, sick calls and delays, cover options. Every answer explains its reasoning; conversations are kept. Times are UTC."}
                </p>
                {!active && watchlist && (
                  <div className="empty-watch">
                    <Watchlist watchlist={watchlist} directory={directory} onPick={(q) => ask(q)} dev={dev} />
                  </div>
                )}
              </div>
            )}
            {messages.map((m, i) => (
              <Message key={i} message={m} voice={voice} directory={directory} dev={dev} />
            ))}

            <div ref={bottomRef} />
          </div>
          {error && <div className="error-bar">{error}</div>}
          <Composer value={draft} onChange={setDraft} onSubmit={(q) => ask(q)} disabled={busy} voice={voice} dev={dev} />
        </section>
        {watchOpen && (
          <aside className="drawer">
            <Watchlist
              watchlist={watchlist}
              directory={directory}
              dev={dev}
              compact
              onPick={(q) => {
                setDraft(q);
                setWatchOpen(false);
              }}
            />
          </aside>
        )}
        {dev && samplesOpen && (
          <aside className="drawer">
            <Samples
              samples={context?.samples || []}
              onPick={(q) => {
                setDraft(q);
                setSamplesOpen(false);
              }}
              disabled={busy}
            />
          </aside>
        )}
      </main>
    </div>
  );
}
