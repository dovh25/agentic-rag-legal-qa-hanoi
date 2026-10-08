"use client";

import { FormEvent, useState } from "react";

type Citation = {
  doc_id: string;
  document_title: string;
  document_number: string;
  article_ref?: string | null;
  clause?: string | null;
  snippet: string;
  source_url?: string | null;
  effective_date?: string | null;
  relevance_score?: number | null;
};

type QueryResponse = {
  query: string;
  status: "answered" | "clarification_needed" | "insufficient_evidence";
  answer?: string | null;
  citations: Citation[];
  reasoning_steps: string[];
  route?: string | null;
  sub_queries: string[];
  clarification_question?: string | null;
  processing_time_ms?: number | null;
  as_of_date_applied?: string | null;
};

type ChatMessage = {
  query: string;
  response: QueryResponse;
};

const districts = [
  "Ba Đình",
  "Hoàn Kiếm",
  "Tây Hồ",
  "Long Biên",
  "Cầu Giấy",
  "Đống Đa",
  "Hai Bà Trưng",
  "Hoàng Mai",
  "Thanh Xuân",
  "Nam Từ Liêm",
  "Bắc Từ Liêm",
  "Hà Đông",
  "Sơn Tây",
  "Ba Vì",
  "Chương Mỹ",
  "Đan Phượng",
  "Đông Anh",
  "Gia Lâm",
  "Hoài Đức",
  "Mê Linh",
  "Mỹ Đức",
  "Phú Xuyên",
  "Phúc Thọ",
  "Quốc Oai",
  "Sóc Sơn",
  "Thạch Thất",
  "Thanh Oai",
  "Thanh Trì",
  "Thường Tín",
  "Ứng Hòa",
];

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function statusLabel(status: QueryResponse["status"]): string {
  if (status === "answered") return "Đã trả lời";
  if (status === "clarification_needed") return "Cần làm rõ";
  return "Không đủ căn cứ";
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [district, setDistrict] = useState("");
  const [asOfDate, setAsOfDate] = useState(today);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submitQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submittedQuery = query.trim();
    if (!submittedQuery || loading) return;

    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: submittedQuery,
          as_of_date: asOfDate,
          district: district || null,
          max_results: 5,
        }),
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`API trả về ${response.status}: ${detail}`);
      }
      const result = (await response.json()) as QueryResponse;
      setMessages((current) => [...current, { query: submittedQuery, response: result }]);
      setQuery("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Không thể kết nối API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Trang chủ Tra cứu pháp luật đất đai Hà Nội">
          <span className="brand-mark" aria-hidden="true">⚖</span>
          <span>Pháp luật đất đai <strong>Hà Nội</strong></span>
        </a>
        <a className="api-link" href={`${apiBase}/docs`} target="_blank" rel="noreferrer">
          Tài liệu API
        </a>
      </header>

      <section className="content">
        <div className="intro">
          <p className="eyebrow">TRA CỨU CÓ CĂN CỨ · CẬP NHẬT THEO THỜI ĐIỂM</p>
          <h1>Hỏi đáp pháp luật đất đai Hà Nội</h1>
          <p className="intro-copy">
            Tra cứu quy định về đất đai, quy hoạch, thu hồi đất, bồi thường và tái định cư.
            Câu trả lời kèm trích dẫn để bạn đối chiếu văn bản gốc.
          </p>
        </div>

        <section className="filters" aria-label="Bộ lọc tra cứu">
          <label>
            Thời điểm áp dụng
            <input
              type="date"
              value={asOfDate}
              onChange={(event) => setAsOfDate(event.target.value)}
            />
          </label>
          <label>
            Quận, huyện hoặc thị xã
            <select value={district} onChange={(event) => setDistrict(event.target.value)}>
              <option value="">Toàn thành phố / không chỉ định</option>
              {districts.map((name) => <option key={name} value={name}>{name}</option>)}
            </select>
          </label>
        </section>

        <section className="conversation" aria-label="Nội dung tra cứu" aria-live="polite">
          {messages.length === 0 && (
            <div className="empty-state">
              <span className="empty-icon" aria-hidden="true">⌕</span>
              <h2>Bắt đầu tra cứu</h2>
              <p>Ví dụ: “Điều kiện bồi thường đất nông nghiệp khi thu hồi tại Đông Anh?”</p>
            </div>
          )}
          {messages.map(({ query: asked, response }, index) => (
            <article className="exchange" key={`${index}-${asked}`}>
              <p className="user-question">{asked}</p>
              <div className="answer-card">
                <div className="answer-heading">
                  <span className={`status-badge ${response.status}`}>
                    {statusLabel(response.status)}
                  </span>
                  <span className="response-meta">
                    {response.as_of_date_applied && `Áp dụng đến ${response.as_of_date_applied}`}
                    {response.processing_time_ms != null &&
                      ` · ${(response.processing_time_ms / 1000).toFixed(1)} giây`}
                  </span>
                </div>
                {response.answer && <p className="answer-text">{response.answer}</p>}
                {response.clarification_question && (
                  <p className="clarification">{response.clarification_question}</p>
                )}
                {response.citations.length > 0 && (
                  <section className="citations" aria-label="Trích dẫn nguồn">
                    <h3>Căn cứ pháp lý</h3>
                    {response.citations.map((citation, citationIndex) => (
                      <article className="citation" key={`${citation.doc_id}-${citationIndex}`}>
                        <div className="citation-title">
                          <span className="citation-number">[{citationIndex + 1}]</span>
                          <strong>{citation.document_title}</strong>
                        </div>
                        <p className="citation-meta">
                          {citation.document_number}
                          {citation.article_ref && ` · ${citation.article_ref}`}
                          {citation.clause && ` · ${citation.clause}`}
                          {citation.effective_date && ` · Hiệu lực ${citation.effective_date}`}
                        </p>
                        <blockquote>{citation.snippet}</blockquote>
                        {citation.source_url && (
                          <a href={citation.source_url} target="_blank" rel="noreferrer">
                            Mở nguồn chính thức →
                          </a>
                        )}
                      </article>
                    ))}
                  </section>
                )}
                {response.reasoning_steps.length > 0 && (
                  <details className="reasoning">
                    <summary>Các bước xử lý</summary>
                    <ol>{response.reasoning_steps.map((step, i) => <li key={i}>{step}</li>)}</ol>
                  </details>
                )}
              </div>
            </article>
          ))}
          {loading && <p className="loading" role="status">Đang tra cứu căn cứ pháp lý…</p>}
          {error && <p className="error" role="alert">{error}</p>}
        </section>

        <form className="query-form" onSubmit={submitQuery}>
          <label className="visually-hidden" htmlFor="query">Câu hỏi pháp lý</label>
          <textarea
            id="query"
            value={query}
            maxLength={500}
            rows={3}
            placeholder="Nhập câu hỏi về pháp luật đất đai…"
            onChange={(event) => setQuery(event.target.value)}
            disabled={loading}
            required
          />
          <div className="form-actions">
            <span className={query.length >= 490 ? "counter near-limit" : "counter"}>
              {query.length}/500
            </span>
            <button type="submit" disabled={loading || !query.trim()}>
              {loading ? "Đang xử lý…" : "Tra cứu →"}
            </button>
          </div>
        </form>
        <p className="disclaimer">
          Thông tin chỉ nhằm hỗ trợ tra cứu, không thay thế tư vấn pháp lý chính thức hoặc quyết
          định của cơ quan nhà nước có thẩm quyền.
        </p>
      </section>
    </main>
  );
}
