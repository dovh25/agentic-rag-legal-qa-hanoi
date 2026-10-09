"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Citation = {
  doc_id: string;
  document_title: string;
  document_number: string;
  article_ref?: string;
  clause?: string;
  snippet: string;
  source_url?: string;
};
type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
};
type Conversation = { id: string; title: string; updatedAt: number; messages: Message[] };
type ChatResponse = {
  status: "answered" | "clarification_needed" | "insufficient_evidence";
  answer?: string;
  clarification_question?: string;
  citations: Citation[];
  reasoning_steps: string[];
};

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const DB_NAME = "legal-qa-chat";
const STORE = "conversations";
const samples = [
  "Điều kiện bồi thường khi Nhà nước thu hồi đất ở tại Hà Nội là gì?",
  "Bảng giá đất tại quận Ba Đình áp dụng từ thời điểm nào?",
  "Quy định tái định cư khi thu hồi đất để làm đường Vành đai 4?",
  "Hạn mức giao đất ở tại quận Cầu Giấy theo quy định hiện hành?",
];

function uid() {
  return crypto.randomUUID();
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: "id" });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
async function readConversations(): Promise<Conversation[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const request = db.transaction(STORE).objectStore(STORE).getAll();
    request.onsuccess = () => resolve((request.result as Conversation[]).sort((a, b) => b.updatedAt - a.updatedAt));
    request.onerror = () => reject(request.error);
  });
}
async function saveConversation(conversation: Conversation) {
  const db = await openDb();
  db.transaction(STORE, "readwrite").objectStore(STORE).put(conversation);
}
async function deleteConversation(id: string) {
  const db = await openDb();
  db.transaction(STORE, "readwrite").objectStore(STORE).delete(id);
}

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState("");
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [error, setError] = useState("");
  const [district, setDistrict] = useState("");
  const [asOfDate, setAsOfDate] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">("light");

  const active = useMemo(() => conversations.find((item) => item.id === activeId), [conversations, activeId]);

  useEffect(() => {
    const savedTheme = window.localStorage.getItem("legal-qa-theme");
    if (savedTheme === "dark") setTheme("dark");
    readConversations().then((items) => {
      setConversations(items);
      if (items[0]) setActiveId(items[0].id);
    }).catch(() => setError("Không thể mở lịch sử chat trên trình duyệt."));
  }, []);

  function toggleTheme() {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    window.localStorage.setItem("legal-qa-theme", next);
  }

  function newChat() {
    const conversation = { id: uid(), title: "Phiên chat mới", updatedAt: Date.now(), messages: [] };
    setConversations((items) => [conversation, ...items]);
    setActiveId(conversation.id);
    saveConversation(conversation).catch(() => setError("Không thể lưu phiên chat cục bộ."));
  }
  async function removeChat(id: string) {
    await deleteConversation(id);
    const remaining = conversations.filter((item) => item.id !== id);
    setConversations(remaining);
    setActiveId(remaining[0]?.id ?? "");
  }
  function renameChat(conversation: Conversation) {
    const title = window.prompt("Tên phiên chat", conversation.title)?.trim();
    if (title) updateConversation({ ...conversation, title: title.slice(0, 80) });
  }
  function updateConversation(conversation: Conversation) {
    const updated = { ...conversation, updatedAt: Date.now() };
    setConversations((items) => [updated, ...items.filter((item) => item.id !== updated.id)]);
    saveConversation(updated).catch(() => setError("Không thể lưu phiên chat cục bộ."));
  }

  async function submit(event?: FormEvent, supplied?: string) {
    event?.preventDefault();
    const message = (supplied ?? draft).trim();
    if (!message || loading) return;
    let conversation = active;
    if (!conversation) {
      conversation = { id: uid(), title: message.slice(0, 42), updatedAt: Date.now(), messages: [] };
      setActiveId(conversation.id);
    }
    const userMessage: Message = { id: uid(), role: "user", content: message, citations: [] };
    const context = conversation.messages.slice(-12);
    const next = { ...conversation, title: conversation.messages.length ? conversation.title : message.slice(0, 42), messages: [...conversation.messages, userMessage] };
    updateConversation(next);
    setDraft("");
    setError("");
    setLoading(true);
    setStreamingText("");
    try {
      const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, context, district: district || undefined, as_of_date: asOfDate || undefined }),
      });
      if (!response.ok || !response.body) throw new Error(`API error ${response.status}`);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let completed: ChatResponse | null = null;
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const event of events) {
          const line = event.split("\n").find((item) => item.startsWith("data: "));
          if (!line) continue;
          const payload = JSON.parse(line.slice(6)) as { type: string; response?: ChatResponse; message?: string };
          if (payload.type === "error") throw new Error(payload.message ?? "Lỗi xử lý chat.");
          if (payload.type === "text_delta") {
            const text = (payload as { text?: string }).text ?? "";
            setStreamingText((value) => value + text);
          }
          if (payload.type === "message_completed" && payload.response) completed = payload.response;
        }
        if (done) break;
      }
      if (!completed) throw new Error("API không gửi message_completed.");
      const assistant: Message = {
        id: uid(),
        role: "assistant",
        content: completed.answer ?? completed.clarification_question ?? "Chưa có câu trả lời.",
        citations: completed.citations ?? [],
      };
      updateConversation({ ...next, messages: [...next.messages, assistant] });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Không thể kết nối API.");
    } finally {
      setLoading(false);
      setStreamingText("");
    }
  }

  return (
    <main className={`chat-app theme-${theme}`}>
      <aside className="sidebar" aria-label="Lịch sử phiên chat">
        <div className="brand"><span>⚖</span><strong>Legal QA Hà Nội</strong></div>
        <button className="new-chat" onClick={newChat}>＋ Chat mới</button>
        <div className="history">
          {conversations.map((conversation) => (
            <div className={`history-row ${conversation.id === activeId ? "selected" : ""}`} key={conversation.id}>
              <button onClick={() => setActiveId(conversation.id)} onDoubleClick={() => renameChat(conversation)}>{conversation.title}</button>
              <button className="delete" aria-label={`Xóa ${conversation.title}`} onClick={() => removeChat(conversation.id)}>×</button>
            </div>
          ))}
        </div>
        <p className="storage-note">Lịch sử chỉ lưu trên trình duyệt này.</p>
      </aside>
      <section className="chat-main">
        <header className="chat-header">
          <div><p className="eyebrow">AGENTIC RAG · HÀ NỘI</p><h1>{active?.title ?? "Bạn muốn tra cứu điều gì?"}</h1></div>
          <div className="filters">
            <input aria-label="Quận huyện" value={district} onChange={(event) => setDistrict(event.target.value)} placeholder="Quận/huyện" />
            <input aria-label="Ngày áp dụng" type="date" value={asOfDate} onChange={(event) => setAsOfDate(event.target.value)} />
            <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label="Đổi giao diện sáng tối">{theme === "light" ? "☾" : "☀"}</button>
          </div>
        </header>
        <div className="transcript" aria-live="polite">
          {!active?.messages.length && (
            <div className="welcome">
              <h2>Hỏi đáp pháp luật có căn cứ</h2>
              <p>Mỗi câu trả lời được kiểm chứng với văn bản chính thức. Hãy bắt đầu bằng một câu hỏi mẫu:</p>
              <div className="samples">{samples.map((sample) => <button key={sample} onClick={() => submit(undefined, sample)}>{sample}</button>)}</div>
            </div>
          )}
          {active?.messages.map((message) => (
            <article className={`message ${message.role}`} key={message.id}>
              <div className="avatar">{message.role === "user" ? "Bạn" : "AI"}</div>
              <div className="message-body"><p>{message.content}</p>
                {message.citations.length > 0 && <div className="citations"><strong>Căn cứ pháp lý</strong>{message.citations.map((citation, index) => <div className="citation" key={`${citation.doc_id}-${index}`}><b>[{index + 1}] {citation.document_title}</b><small>{citation.document_number} · {citation.article_ref} {citation.clause}</small><p>{citation.snippet}</p>{citation.source_url && <a href={citation.source_url} target="_blank" rel="noreferrer">Mở nguồn chính thức ↗</a>}</div>)}</div>}
              </div>
            </article>
          ))}
          {loading && streamingText && <article className="message assistant"><div className="avatar">AI</div><div className="message-body"><p>{streamingText}</p></div></article>}
          {loading && <div className="typing" role="status">Đang kiểm tra căn cứ pháp lý…</div>}
        </div>
        {error && <p className="error" role="alert">{error}</p>}
        <form className="composer" onSubmit={submit}>
          <textarea value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submit(); } }} placeholder="Nhập câu hỏi tiếp theo…" rows={2} disabled={loading} />
          <button type="submit" disabled={loading || !draft.trim()}>{loading ? "…" : "Gửi"}</button>
          <small>Enter để gửi · Shift+Enter xuống dòng · Chỉ mang tính tham khảo pháp lý</small>
        </form>
      </section>
    </main>
  );
}
