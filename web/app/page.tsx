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
  relevance_score?: number;
  effective_date?: string;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  status?: "answered" | "clarification_needed" | "insufficient_evidence";
  route?: string;
  reasoning_steps?: string[];
  processing_time_ms?: number;
};

type Conversation = { id: string; title: string; updatedAt: number; messages: Message[] };

type ChatResponse = {
  status: "answered" | "clarification_needed" | "insufficient_evidence";
  answer?: string;
  clarification_question?: string;
  citations: Citation[];
  reasoning_steps: string[];
  route?: string;
  sub_queries?: string[];
  processing_time_ms?: number;
  as_of_date_applied?: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const DB_NAME = "legal-qa-chat";
const STORE = "conversations";

const SAMPLE_QUESTIONS = [
  "Điều kiện bồi thường khi Nhà nước thu hồi đất ở tại Hà Nội là gì?",
  "Bảng giá đất tại quận Ba Đình áp dụng từ thời điểm nào?",
  "Quy định tái định cư khi thu hồi đất để làm đường Vành đai 4?",
  "Hạn mức giao đất ở tại quận Cầu Giấy theo quy định hiện hành?",
];

const HANOI_DISTRICTS = [
  "Ba Đình", "Hoàn Kiếm", "Tây Hồ", "Long Biên", "Cầu Giấy", "Đống Đa",
  "Hai Bà Trưng", "Hoàng Mai", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm",
  "Hà Đông", "Sơn Tây", "Ba Vì", "Chương Mỹ", "Đan Phượng", "Đông Anh",
  "Gia Lâm", "Hoài Đức", "Mê Linh", "Mỹ Đức", "Phú Xuyên", "Phúc Thọ",
  "Quốc Oai", "Sóc Sơn", "Thạch Thất", "Thanh Oai", "Thanh Trì",
  "Thường Tín", "Ứng Hòa"
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

function formatDate(timestamp: number): string {
  return new Date(timestamp).toLocaleString("vi-VN", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  });
}

function StatusBadge({ status }: { status: Message["status"] }) {
  const styles = {
    answered: "bg-success text-white",
    clarification_needed: "bg-warning text-white",
    insufficient_evidence: "bg-danger text-white",
  };
  const labels = {
    answered: "✅ Đã trả lời",
    clarification_needed: "🤔 Cần làm rõ",
    insufficient_evidence: "⚠️ Không đủ căn cứ",
  };
  const statusValue = status ?? "answered";
  return (
    <span className={`status-badge ${styles[statusValue]}`}>
      {labels[statusValue]}
    </span>
  );
}

function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const scorePercent = Math.round((citation.relevance_score ?? 0) * 100);
  return (
    <div className="citation-card" key={`${citation.doc_id}-${index}`}>
      <div className="citation-header">
        <span className="citation-index">[{index + 1}]</span>
        <span className="citation-title">{citation.document_title}</span>
      </div>
      <div className="citation-meta">
        <span>{citation.document_number}</span>
        {citation.article_ref && <span>{citation.article_ref} {citation.clause}</span>}
        {citation.effective_date && <span>Hiệu lực: {citation.effective_date}</span>}
        <span className="relevance-score">Độ liên quan: {scorePercent}%</span>
      </div>
      <p className="citation-snippet">{citation.snippet}</p>
      {citation.source_url && (
        <a href={citation.source_url} target="_blank" rel="noopener noreferrer" className="citation-link">
          Xem toàn văn tại Cổng VBPL ↗
        </a>
      )}
    </div>
  );
}

function ReasoningSteps({ steps }: { steps: string[] }) {
  if (!steps || steps.length === 0) return null;
  return (
    <details className="reasoning-steps">
      <summary>💭 Quá trình suy luận (nhấn để xem)</summary>
      <ol>
        {steps.map((step, i) => (
          <li key={i}>{step}</li>
        ))}
      </ol>
    </details>
  );
}

function ClarificationDialog({ question, onContinue }: { question: string; onContinue: (event: React.FormEvent<HTMLFormElement>) => void }) {
  return (
    <div className="clarification-dialog">
      <div className="clarification-icon">🤔</div>
      <p className="clarification-text">Tôi cần thêm thông tin để trả lời chính xác:</p>
      <form onSubmit={onContinue} className="clarification-form">
        <div className="form-group">
          <label>1. Loại đất:</label>
          <select name="land_type" required>
            <option value="">Chọn loại đất</option>
            <option value="đất ở">Đất ở</option>
            <option value="đất nông nghiệp">Đất nông nghiệp</option>
            <option value="đất thương mại dịch vụ">Đất thương mại dịch vụ</option>
            <option value="khác">Loại khác</option>
          </select>
        </div>
        <div className="form-group">
          <label>2. Quận/huyện tại Hà Nội:</label>
          <select name="district" required>
            <option value="">Chọn quận/huyện</option>
            {HANOI_DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>3. Diện tích đất (m² - tùy chọn):</label>
          <input type="number" name="area" placeholder="Ví dụ: 120" min="0" />
        </div>
        <button type="submit" className="btn-primary">Tiếp tục →</button>
      </form>
    </div>
  );
}

function InsufficientEvidenceScreen({ onNewQuery }: { onNewQuery: () => void }) {
  return (
    <div className="insufficient-evidence-screen">
      <div className="icon">⚠️</div>
      <h3>Không đủ căn cứ pháp lý</h3>
      <p>Hệ thống không tìm thấy đủ văn bản pháp lý liên quan trong cơ sở dữ liệu để trả lời câu hỏi của bạn.</p>
      <div className="actions">
        <button className="btn-primary" onClick={onNewQuery}>Hỏi câu khác</button>
        <a href="https://vanban.chinhphu.vn" target="_blank" rel="noopener noreferrer" className="btn-secondary">
          Xem Cổng VBPL
        </a>
        <a href="https://congbao.hanoi.gov.vn" target="_blank" rel="noopener noreferrer" className="btn-secondary">
          Xem Công báo Hà Nội
        </a>
      </div>
    </div>
  );
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
  const [showReasoning, setShowReasoning] = useState(false);

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
          const payload = JSON.parse(line.slice(6)) as { type: string; response?: ChatResponse; message?: string; text?: string };
          if (payload.type === "error") throw new Error(payload.message ?? "Lỗi xử lý chat.");
          if (payload.type === "text_delta") {
            setStreamingText((value) => value + (payload.text ?? ""));
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

  function handleClarificationSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const landType = formData.get("land_type");
    const district = formData.get("district");
    const area = formData.get("area");
    const clarifiedQuery = `${landType} tại ${district}${area ? ` diện tích ${area}m²` : ""}`;
    setDraft(clarifiedQuery);
    submit(undefined, clarifiedQuery);
  }

  return (
    <main className={`chat-app theme-${theme}`}>
      <aside className="sidebar" aria-label="Lịch sử phiên chat">
        <div className="brand">
          <span>⚖</span>
          <strong>Tra cứu Pháp luật Đất đai HN</strong>
        </div>
        <button className="new-chat" onClick={newChat}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>Chat mới</span>
        </button>
        <div className="history">
          {conversations.map((conversation) => (
            <div className={`history-row ${conversation.id === activeId ? "selected" : ""}`} key={conversation.id}>
              <button onClick={() => setActiveId(conversation.id)} onDoubleClick={() => renameChat(conversation)}>
                <span className="history-title">{conversation.title}</span>
                <span className="history-time">{formatDate(conversation.updatedAt)}</span>
              </button>
              <button className="delete" aria-label={`Xóa ${conversation.title}`} onClick={() => removeChat(conversation.id)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          ))}
        </div>
        <p className="storage-note">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="3" width="20" height="14" rx="2"></rect>
            <path d="M8 21h8"></path>
            <path d="M12 17v4"></path>
          </svg>
          Lịch sử chỉ lưu trên trình duyệt này.
        </p>
      </aside>
      <section className="chat-main">
        <header className="chat-header">
          <div>
            <p className="eyebrow">AGENTIC RAG · HÀ NỘI</p>
            <h1>{active?.title ?? "Bạn muốn tra cứu điều gì?"}</h1>
          </div>
          <div className="filters">
            <select value={district} onChange={(e) => setDistrict(e.target.value)} aria-label="Quận/huyện">
              <option value="">Toàn Hà Nội</option>
              {HANOI_DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
            <input type="date" value={asOfDate} onChange={(e) => setAsOfDate(e.target.value)} aria-label="Ngày áp dụng" />
            <button className="theme-toggle" onClick={toggleTheme} aria-label={theme === "light" ? "Chế độ tối" : "Chế độ sáng"}>
              {theme === "light" ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5"></circle>
                  <line x1="12" y1="1" x2="12" y2="3"></line>
                  <line x1="12" y1="21" x2="12" y2="23"></line>
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                  <line x1="1" y1="12" x2="3" y2="12"></line>
                  <line x1="21" y1="12" x2="23" y2="12"></line>
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                </svg>
              )}
            </button>
          </div>
        </header>
        <div className="transcript" aria-live="polite" role="log">
          {!active?.messages.length && (
            <div className="welcome">
              <div className="welcome-icon">⚖️</div>
              <h2>Hỏi đáp pháp luật có căn cứ</h2>
              <p>Mỗi câu trả lời được kiểm chứng với văn bản chính thức. Hãy bắt đầu bằng một câu hỏi mẫu:</p>
              <div className="samples">
                {SAMPLE_QUESTIONS.map((sample) => (
                  <button key={sample} onClick={() => submit(undefined, sample)}>
                    {sample}
                  </button>
                ))}
              </div>
              <p className="disclaimer">⚠️ Hệ thống hỗ trợ tra cứu — không thay thế tư vấn pháp lý chính thức</p>
            </div>
          )}
          {active?.messages.map((message) => (
            <article className={`message ${message.role}`} key={message.id}>
              <div className="avatar">{message.role === "user" ? "Bạn" : "AI"}</div>
              <div className="message-body">
                <div className="message-header">
                  <span className="role-label">{message.role === "user" ? "👤 Bạn" : "🤖 AI"}</span>
                  {message.status && <StatusBadge status={message.status} />}
                  {message.processing_time_ms && (
                    <span className="processing-time">
                      ⏱ {message.processing_time_ms}ms · {message.route ?? "single_hop"}
                    </span>
                  )}
                </div>
                <p>{streamingText && message.id === active?.messages[active.messages.length - 1]?.id ? streamingText : message.content}</p>
                {message.citations.length > 0 && (
                  <div className="citations">
                    <div className="citations-header">
                      <strong>📚 Căn cứ pháp lý</strong>
                      <span className="citation-count">{message.citations.length} nguồn</span>
                    </div>
                    {message.citations.map((citation, index) => (
                      <CitationCard citation={citation} index={index} />
                    ))}
                  </div>
                )}
                <ReasoningSteps steps={message.reasoning_steps ?? []} />
              </div>
            </article>
          ))}
          {loading && (
            <>
              <article className="message assistant streaming">
                <div className="avatar">AI</div>
                <div className="message-body">
                  <p>{streamingText}</p>
                  <div className="streaming-indicator">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </article>
              <div className="typing" role="status">
                <span></span><span></span><span></span>
                Đang kiểm tra căn cứ pháp lý…
              </div>
            </>
          )}
        </div>
        {error && <p className="error" role="alert">{error}</p>}
        {!loading && active && active.messages.length > 0 && active.messages[active.messages.length - 1].status === "clarification_needed" && (
          <ClarificationDialog
            question={active.messages[active.messages.length - 1].content}
            onContinue={handleClarificationSubmit}
          />
        )}
        {!loading && active && active.messages.length > 0 && active.messages[active.messages.length - 1].status === "insufficient_evidence" && (
          <InsufficientEvidenceScreen onNewQuery={() => setDraft("")} />
        )}
        <form className="composer" onSubmit={submit}>
          <div className="composer-input-wrapper">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  submit();
                }
              }}
              placeholder="Nhập câu hỏi về pháp luật đất đai Hà Nội… (Enter để gửi, Shift+Enter xuống dòng)"
              rows={2}
              disabled={loading}
              aria-label="Câu hỏi pháp lý"
            />
            <button type="submit" disabled={loading || !draft.trim()} className="send-button">
              {loading ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="spinner">
                  <circle cx="12" cy="12" r="10" strokeOpacity="0.25"></circle>
                  <path d="M12 2a10 10 0 0 1 10 10" strokeOpacity="1"></path>
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              )}
            </button>
          </div>
          <div className="composer-hints">
            <span>Enter để gửi · Shift+Enter xuống dòng</span>
            <span>⚠️ Chỉ mang tính tham khảo pháp lý</span>
          </div>
        </form>
      </section>
    </main>
  );
}