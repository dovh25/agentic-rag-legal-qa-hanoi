"use client";

import { FormEvent, useState } from "react";

type Citation = {
  document_title: string;
  document_number: string;
  article_ref?: string;
  clause?: string;
  snippet: string;
  source_url?: string;
};

type Answer = {
  status: "answered" | "clarification_needed" | "insufficient_evidence";
  answer?: string;
  clarification_question?: string;
  citations: Citation[];
  reasoning_steps: string[];
};

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [query, setQuery] = useState("");
  const [district, setDistrict] = useState("");
  const [asOfDate, setAsOfDate] = useState("");
  const [result, setResult] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/v1/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          district: district || undefined,
          as_of_date: asOfDate || undefined,
        }),
      });
      if (!response.ok) throw new Error(`API error ${response.status}`);
      setResult(await response.json());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Không thể kết nối API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header className="hero">
        <p className="eyebrow">AGENTIC RAG LEGAL QA — HÀ NỘI</p>
        <h1>Tra cứu pháp luật đất đai có căn cứ</h1>
        <p className="intro">
          Hỏi về quy hoạch, thu hồi đất, bồi thường và tái định cư. Mỗi câu trả lời đều
          kèm trích dẫn để bạn kiểm chứng tại nguồn chính thức.
        </p>
      </header>

      <form className="query-card" onSubmit={submit}>
        <label htmlFor="query">Câu hỏi của bạn</label>
        <textarea
          id="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ví dụ: Hạn mức giao đất ở tại Cầu Giấy theo quy định hiện hành?"
          rows={4}
          required
        />
        <div className="filters">
          <label>
            Quận/huyện
            <input value={district} onChange={(event) => setDistrict(event.target.value)} placeholder="Không bắt buộc" />
          </label>
          <label>
            Áp dụng tại ngày
            <input type="date" value={asOfDate} onChange={(event) => setAsOfDate(event.target.value)} />
          </label>
        </div>
        <button type="submit" disabled={loading}>
          {loading ? "Đang kiểm tra căn cứ..." : "Bắt đầu tra cứu"}
        </button>
      </form>

      {error && <p className="error" role="alert">{error}</p>}
      {result && (
        <section className={`result ${result.status}`} aria-live="polite">
          <p className="status">{result.status}</p>
          {result.answer && <p className="answer">{result.answer}</p>}
          {result.clarification_question && <p className="notice">{result.clarification_question}</p>}
          {result.status === "insufficient_evidence" && (
            <p className="notice">Chưa có đủ căn cứ trong corpus. Hãy bổ sung dữ kiện hoặc tham vấn cơ quan có thẩm quyền.</p>
          )}
          {result.citations.length > 0 && (
            <div className="citations">
              <h2>Căn cứ pháp lý</h2>
              {result.citations.map((citation, index) => (
                <article key={`${citation.document_number}-${index}`} className="citation">
                  <strong>{citation.document_title}</strong>
                  <span>{citation.document_number} · {citation.article_ref} {citation.clause}</span>
                  <p>{citation.snippet}</p>
                  {citation.source_url && <a href={citation.source_url} target="_blank" rel="noreferrer">Mở nguồn chính thức ↗</a>}
                </article>
              ))}
            </div>
          )}
        </section>
      )}
      <footer>Thông tin chỉ mang tính chất tham khảo, không thay thế tư vấn pháp lý chính thức.</footer>
    </main>
  );
}
