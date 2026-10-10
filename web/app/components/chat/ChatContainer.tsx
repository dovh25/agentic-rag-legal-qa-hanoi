"use client";

import { useState, useEffect } from "react";
import { cn, formatRelativeTime } from "@/lib/utils";
import { Header } from "@/app/components/header/Header";
import { MessageBubble } from "./MessageBubble";
import { Composer } from "./Composer";
import { ClarificationDialog } from "./ClarificationDialog";
import { InsufficientEvidence } from "./InsufficientEvidence";
import { API_URL } from "@/lib/api";

const SAMPLE_QUESTIONS = [
  "Điều kiện bồi thường khi Nhà nước thu hồi đất ở tại Hà Nội là gì?",
  "Bảng giá đất tại quận Ba Đình áp dụng từ thời điểm nào?",
  "Quy định tái định cư khi thu hồi đất để làm đường Vành đai 4?",
  "Hạn mức giao đất ở tại quận Cầu Giấy theo quy định hiện hành?",
];


export function ChatContainer() {
  const [conversations, setConversations] = useState<Array<{
    id: string;
    title: string;
    updatedAt: number;
    messages: any[];
  }>>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [error, setError] = useState("");
  const [district, setDistrict] = useState("");
  const [asOfDate, setAsOfDate] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const getThemeClass = () => `theme-${theme}`;
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const active = conversations.find((c) => c.id === activeId);

  useEffect(() => {
    const savedTheme = localStorage.getItem("luat-gpt-theme");
    if (savedTheme === "dark") setTheme("dark");

    loadConversations().then((items) => {
      setConversations(items);
      if (items[0]) setActiveId(items[0].id);
    }).catch(() => {});
  }, []);

  async function loadConversations() {
    return new Promise<Array<{
      id: string;
      title: string;
      updatedAt: number;
      messages: any[];
    }>>((resolve, reject) => {
      const request: IDBOpenDBRequest = indexedDB.open("luat-gpt-chat", 1);
      request.onupgradeneeded = () => request.result.createObjectStore("conversations", { keyPath: "id" });
      request.onsuccess = () => {
        const dbRequest = request.result.transaction("conversations").objectStore("conversations").getAll();
        dbRequest.onsuccess = () => resolve((dbRequest.result as any[]).sort((a, b) => b.updatedAt - a.updatedAt));
        dbRequest.onerror = () => reject(dbRequest.error);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async function saveConversation(conversation: any) {
    const db = await new Promise<IDBDatabase>((resolve, reject) => {
      const request: IDBOpenDBRequest = indexedDB.open("luat-gpt-chat", 1);
      request.onupgradeneeded = () => request.result.createObjectStore("conversations", { keyPath: "id" });
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    db.transaction("conversations", "readwrite").objectStore("conversations").put(conversation);
  }

  function generateId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  function toggleTheme() {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    localStorage.setItem("luat-gpt-theme", next);
  }

  function newChat() {
    const conversation = { id: generateId(), title: "Phiên chat mới", updatedAt: Date.now(), messages: [] };
    setConversations((items) => [conversation, ...items]);
    setActiveId(conversation.id);
    saveConversation(conversation).catch(console.error);
  }


  function updateConversation(conversation: any) {
    const updated = { ...conversation, updatedAt: Date.now() };
    setConversations((items) => [updated, ...items.filter((item) => item.id !== updated.id)]);
    saveConversation(updated).catch(console.error);
  }

  async function submit(event?: React.FormEvent, supplied?: string) {
    event?.preventDefault();
    const message = (supplied ?? draft).trim();
    if (!message || loading) return;
    let conversation = active;
    if (!conversation) {
      conversation = { id: generateId(), title: message.slice(0, 42), updatedAt: Date.now(), messages: [] };
      setActiveId(conversation.id);
    }
    const userMessage = { id: generateId(), role: "user", content: message, citations: [] };
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
      let completed: any = null;
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const event of events) {
          const line = event.split("\n").find((item) => item.startsWith("data: "));
          if (!line) continue;
          const payload = JSON.parse(line.slice(6)) as { type: string; response?: any; message?: string; text?: string };
          if (payload.type === "error") throw new Error(payload.message ?? "Lỗi xử lý chat.");
          if (payload.type === "text_delta") {
            setStreamingText((value) => value + (payload.text ?? ""));
          }
          if (payload.type === "message_completed" && payload.response) completed = payload.response;
        }
        if (done) break;
      }
      if (!completed) throw new Error("API không gửi message_completed.");
      const assistant = {
        id: generateId(),
        role: "assistant",
        content: completed.answer ?? completed.clarification_question ?? "Chưa có câu trả lời.",
        citations: completed.citations ?? [],
        status: completed.status,
        route: completed.route,
        reasoning_steps: completed.reasoning_steps,
        processing_time_ms: completed.processing_time_ms,
      };
      updateConversation({ ...next, messages: [...next.messages, assistant] });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Không thể kết nối API.");
    } finally {
      setLoading(false);
      setStreamingText("");
    }
  }

  function handleClarificationSubmit(formData: FormData) {
    const landType = formData.get("land_type");
    const district = formData.get("district");
    const area = formData.get("area");
    const clarifiedQuery = `${landType} tại ${district}${area ? ` diện tích ${area}m²` : ""}`;
    setDraft(clarifiedQuery);
    submit(undefined, clarifiedQuery);
  }

  return (
    <main className={cn("chat-app h-screen flex flex-col", getThemeClass())}>
      <aside
        className={cn(
          "sidebar bg-card border-r border-border flex flex-col transition-all duration-300",
          sidebarCollapsed ? "w-16" : "w-72"
        )}
        aria-label="Lịch sử phiên chat"
      >
        <div className="brand flex items-center gap-2 p-4 border-b border-border">
          <span className="text-2xl">🏛️</span>
          <strong className="text-lg font-semibold text-text-primary">Luật GPT</strong>
        </div>
        <button
          onClick={newChat}
          className="new-chat w-full justify-start gap-2 px-3 py-2.5 rounded-lg transition-colors bg-transparent border border-border text-text-primary hover:bg-accent"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>Chat mới</span>
        </button>
        <div className="history flex-1 overflow-y-auto p-3 space-y-1">
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={cn(
                "history-row flex items-center gap-2 p-2 rounded-lg transition-colors",
                activeId === conversation.id ? "bg-primary/10" : "hover:bg-accent"
              )}
              onClick={() => setActiveId(conversation.id)}
            >
              <button
                className="flex flex-col flex-1 p-2 text-left text-text-primary hover:bg-accent rounded-lg transition-colors"
                onClick={() => setActiveId(conversation.id)}
              >
                <span className="history-title font-medium truncate">{conversation.title}</span>
                <span className="history-time text-xs text-muted-foreground mt-1 block">
                  {formatRelativeTime(conversation.updatedAt)}
                </span>
              </button>
              <button
                className="p-1.5 rounded transition-colors text-muted-foreground hover:text-red-500 opacity-0 group-hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm(`Xóa phiên "${conversation.title}"?`)) {
                    setConversations(conversations.filter((c) => c.id !== conversation.id));
                  }
                }}
                aria-label={`Xóa ${conversation.title}`}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </button>
            </div>
          ))}
        </div>
        <div className="storage-note p-3 border-t border-border text-xs text-muted-foreground flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="3" width="20" height="14" rx="2" />
            <path d="M8 21h8" />
            <path d="M12 17v4" />
          </svg>
          Lịch sử chỉ lưu trên trình duyệt này.
        </div>
      </aside>

      <section className="chat-main flex-1 flex flex-col min-w-0">
        <Header
          activeConversation={active ? { id: active.id, title: active.title } : null}
          onNewChat={newChat}
          onThemeToggle={toggleTheme}
          theme={theme}
          district={district}
          onDistrictChange={setDistrict}
          asOfDate={asOfDate}
          onAsOfDateChange={setAsOfDate}
        />

        <div className="transcript flex-1 overflow-y-auto p-6 max-w-3xl mx-auto w-full" role="log" aria-live="polite">
          {!active?.messages.length && (
            <div className="welcome text-center max-w-xl mx-auto mt-20 animate-fade-in">
              <div className="welcome-icon text-6xl mb-4">⚖️</div>
              <h2 className="text-2xl font-bold text-text-primary mb-2">Hỏi Luật GPT</h2>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Hỏi luật sư ơi - Tra cứu pháp luật đất đai Hà Nội chính xác, có căn cứ, không hallucinate
              </p>
              <div className="samples grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-md mx-auto mb-6">
                {SAMPLE_QUESTIONS.map((sample) => (
                  <button
                    key={sample}
                    onClick={() => submit(undefined, sample)}
                    className="sample-btn p-4 rounded-xl border border-border bg-card text-text-primary text-left hover:border-primary hover:shadow-md transition-all"
                  >
                    {sample}
                  </button>
                ))}
              </div>
              <p className="disclaimer text-sm text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
                ⚠️ Hệ thống hỗ trợ tra cứu — không thay thế tư vấn pháp lý chính thức
              </p>
            </div>
          )}
          {active?.messages.map((message: any) => (
            <MessageBubble
              key={message.id}
              message={message}
              isStreaming={loading && message.id === active?.messages[active.messages.length - 1]?.id}
              streamingText={streamingText}
            />
          ))}
          {loading && (
            <>
              <div className="message assistant streaming animate-fade-in flex gap-3">
                <div className="avatar bg-primary text-primary-foreground flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium">⚖️</div>
                <div className="flex-1 min-w-0">
                  <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap break-words">
                    {streamingText}
                  </div>
                  <div className="streaming-indicator flex gap-1 mt-2">
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce-subtle" style={{animationDelay: "0ms"}} />
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce-subtle" style={{animationDelay: "150ms"}} />
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce-subtle" style={{animationDelay: "300ms"}} />
                  </div>
                </div>
              </div>
              <div className="typing flex items-center justify-center gap-1 text-muted-foreground italic mt-4">
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce-subtle" style={{animationDelay: "0ms"}} />
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce-subtle" style={{animationDelay: "150ms"}} />
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce-subtle" style={{animationDelay: "300ms"}} />
                Đang kiểm tra căn cứ pháp lý…
              </div>
            </>
          )}
        </div>

        {error && <div className="error mx-auto max-w-3xl p-3 rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 flex items-center gap-2">{error}</div>}

        {!loading && active && active.messages && active.messages.length > 0 && active.messages[active.messages.length - 1].status === "clarification_needed" && (
          <ClarificationDialog
            question={active.messages[active.messages.length - 1].content}
            onContinue={handleClarificationSubmit}
            onCancel={() => setDraft("")}
          />
        )}

        {!loading && active && active.messages && active.messages.length > 0 && active.messages[active.messages.length - 1].status === "insufficient_evidence" && (
          <InsufficientEvidence onNewQuery={() => setDraft("")} />
        )}

      <Composer
        onSubmit={(message) => submit(undefined, message)}
        disabled={loading}
      />
    </section>
  </main>
  );
}
