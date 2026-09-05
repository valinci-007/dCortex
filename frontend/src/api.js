// Thin client for the Crew Ops Advisor backend API.

import { recordingFilename } from "./audio.js";

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ? JSON.stringify(body.detail) : detail;
    } catch {
      // keep statusText
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json();
}

export const api = {
  voice: () => request("/api/voice"),
  transcribe: async (recording, language) => {
    const form = new FormData();
    form.append("audio", recording, recordingFilename(recording));
    if (language) form.append("language", language);
    const res = await fetch("/api/transcribe", { method: "POST", body: form });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        detail = (await res.json()).detail || detail;
      } catch {
        // keep statusText
      }
      throw new Error(`${res.status} ${detail}`);
    }
    return res.json();
  },
  speak: async (text, language) => {
    const res = await fetch("/api/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language: language || null }),
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.blob();
  },
  health: () => request("/api/health"),
  directory: () => request("/api/directory"),
  watchlist: (date, chatId) => {
    const q = new URLSearchParams();
    if (date) q.set("date", date);
    if (chatId) q.set("chat_id", chatId);
    const qs = q.toString();
    return request(`/api/watchlist${qs ? `?${qs}` : ""}`);
  },
  resetScenario: (chatId) => request(`/api/chats/${chatId}/scenario/reset`, { method: "POST" }),
  context: () => request("/api/context"),
  tools: () => request("/api/tools"),
  chats: () => request("/api/chats"),
  chat: (id) => request(`/api/chats/${id}`),
  createChat: (title) =>
    request("/api/chats", { method: "POST", body: JSON.stringify({ title: title || null }) }),
  renameChat: (id, title) =>
    request(`/api/chats/${id}`, { method: "PATCH", body: JSON.stringify({ title }) }),
  deleteChat: (id) => request(`/api/chats/${id}`, { method: "DELETE" }),
  ask: (question, conversationId) =>
    request("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question, conversation_id: conversationId || null }),
    }),
  /** Streaming ask: calls onEvent for every progress event; resolves with the `done` payload
   *  (same shape as /api/ask). Rejects if the stream ends without one. */
  askStream: async (question, conversationId, onEvent) => {
    const res = await fetch("/api/ask/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, conversation_id: conversationId || null }),
    });
    if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}`);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let done = null;
    for (;;) {
      const { value, done: closed } = await reader.read();
      if (closed) break;
      buffer += decoder.decode(value, { stream: true });
      let cut;
      while ((cut = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, cut);
        buffer = buffer.slice(cut + 2);
        const line = frame.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue; // keep-alive comment
        const event = JSON.parse(line.slice(6));
        if (event.type === "done") done = event;
        else if (event.type === "error") throw new Error(event.detail || "request failed");
        else onEvent?.(event);
      }
      if (done) break;
    }
    if (!done) throw new Error("the answer stream ended early");
    return done;
  },
};
