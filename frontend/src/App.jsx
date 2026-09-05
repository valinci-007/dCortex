import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import Header from "./components/Header.jsx";
import Message from "./components/Message.jsx";
import Composer from "./components/Composer.jsx";
import Samples from "./components/Samples.jsx";
import Sidebar from "./components/Sidebar.jsx";

const ACTIVE_KEY = "crew-ops-advisor:active-chat";

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
  const bottomRef = useRef(null);

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
    refreshChats();
  }, [refreshChats]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const ask = useCallback(
    async (question, chatId = activeId) => {
      const q = question.trim();
      if (!q || busy) return;
      setError(null);
      setDraft("");
      setMessages((m) => [...m, { role: "user", text: q, at: Date.now() }]);
      setBusy(true);
      try {
        const res = await api.ask(q, chatId);
        setActiveId(res.conversation_id);
        remember(res.conversation_id);
        setMessages((m) => [...m, { role: "assistant", answer: res.answer, at: Date.now() }]);
        refreshChats();
      } catch (e) {
        setError(e.message);
        setMessages((m) => [...m, { role: "assistant", answer: null, error: e.message, at: Date.now() }]);
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
        onToggleSamples={() => setSamplesOpen((v) => !v)}
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
          <div className="messages">
            {messages.length === 0 && (
              <div className="empty">
                <p className="empty-title">{active ? active.title : "Ask the desk a question."}</p>
                <p className="empty-sub">
                  Lookups, consequences, legality, cover options — every answer shows its sources and
                  the rule evidence behind it. Times are UTC; the snapshot is {context?.snapshot_utc || "…"}.
                  Conversations are saved and can be continued later.
                </p>
              </div>
            )}
            {messages.map((m, i) => (
              <Message key={i} message={m} voice={voice} directory={directory} />
            ))}
            {busy && (
              <div className="thinking">
                <span className="dot" /> <span className="dot" /> <span className="dot" />
                <span className="thinking-label">looking it up…</span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          {error && <div className="error-bar">{error}</div>}
          <Composer value={draft} onChange={setDraft} onSubmit={(q) => ask(q)} disabled={busy} voice={voice} />
        </section>
        {samplesOpen && (
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
