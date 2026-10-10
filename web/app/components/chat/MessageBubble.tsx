"use client";

import { cn, formatRelativeTime } from "@/lib/utils";

interface MessageBubbleProps {
  message: {
    id: string;
    role: "user" | "assistant";
    content: string;
    citations: Array<{
      doc_id: string;
      document_title: string;
      document_number: string;
      article_ref?: string;
      clause?: string;
      snippet: string;
      source_url?: string;
      relevance_score?: number;
      effective_date?: string;
    }>;
    status?: "answered" | "clarification_needed" | "insufficient_evidence";
    route?: string;
    reasoning_steps?: string[];
    processing_time_ms?: number;
    timestamp: number;
  };
  isStreaming?: boolean;
  streamingText?: string;
  onCitationClick?: (citation: any) => void;
}

export function MessageBubble({ message, isStreaming, streamingText, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const content = isStreaming && streamingText ? streamingText : message.content;

  return (
    <div
      className={cn(
        "flex gap-3 animate-fade-in",
        message.role === "user" && "flex-row-reverse"
      )}
      data-message-id={message.id}
    >
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium",
          message.role === "user"
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        )}
      >
        {message.role === "user" ? "👤" : "⚖️"}
      </div>

      <div className={cn("flex-1 min-w-0", message.role === "user" ? "text-right" : "")}>
        <div className="flex items-center gap-2 mb-1">
          {!message.role === "user" && (
            <span className="text-xs font-medium text-muted-foreground">
              Luật GPT
            </span>
          )}
          {message.status && (
            <StatusBadge status={message.status} />
          )}
          {message.processing_time_ms && (
            <span className="text-xs text-muted-foreground px-2 py-0.5 rounded bg-muted">
              ⏱ {message.processing_time_ms}ms · {message.route ?? "single_hop"}
            </span>
          )}
          <span className="text-xs text-muted-foreground">
            {formatRelativeTime(message.timestamp)}
          </span>
        </div>

        <div
          className={cn(
            "prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap break-words",
            message.role === "user" ? "text-right" : ""
          )}
        >
          {isStreaming ? streamingText : message.content}
        </div>

        {message.citations && message.citations.length > 0 && (
          <CitationPanel
            citations={message.citations}
            onCitationClick={onCitationClick}
          />
        )}

        {message.reasoning_steps && message.reasoning_steps.length > 0 && (
          <ReasoningSteps steps={message.reasoning_steps} />
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: "answered" | "clarification_needed" | "insufficient_evidence" }) {
  const variants = {
    answered: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    clarification_needed: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
    insufficient_evidence: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  };

  const labels = {
    answered: "✅ Đã trả lời",
    clarification_needed: "🤔 Cần làm rõ",
    insufficient_evidence: "⚠️ Không đủ căn cứ",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        variants[status]
      )}
    >
      {labels[status]}
    </span>
  );
}

function CitationPanel({
  citations,
  onCitationClick,
}: {
  citations: Array<{
    doc_id: string;
    document_title: string;
    document_number: string;
    article_ref?: string;
    clause?: string;
    snippet: string;
    source_url?: string;
    relevance_score?: number;
    effective_date?: string;
  }>;
  onCitationClick?: (citation: any) => void;
}) {
  return (
    <div className="mt-4 border-t border-border pt-4 animate-slide-down">
      <div className="flex items-center justify-between mb-3">
        <strong className="text-sm font-medium">📚 Căn cứ pháp lý</strong>
        <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
          {citations.length} nguồn
        </span>
      </div>
      <div className="space-y-3">
        {citations.map((citation, index) => (
          <CitationCard
            key={`${citation.doc_id}-${index}`}
            citation={citation}
            index={index}
            onClick={onCitationClick}
          />
        ))}
      </div>
    </div>
  );
}

function CitationCard({
  citation,
  index,
  onClick,
}: {
  citation: {
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
  index: number;
  onClick?: (citation: any) => void;
}) {
  const scorePercent = Math.round((citation.relevance_score ?? 0) * 100);

  return (
    <div
      className="citation-card group cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
      onClick={() => onClick?.(citation)}
    >
      <div className="flex items-start gap-3">
        <span className="citation-index flex-shrink-0">[{index + 1}]</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="citation-title font-medium text-text-primary">
              {citation.document_title}
            </span>
            <span>{citation.document_number}</span>
            {citation.article_ref && (
              <span>{citation.article_ref} {citation.clause}</span>
            )}
            {citation.effective_date && (
              <span>Hiệu lực: {citation.effective_date}</span>
            )}
            <span className="relevance-score bg-muted px-2 py-0.5 rounded text-xs font-medium text-primary">
              Độ liên quan: {scorePercent}%
            </span>
          </div>
          <p className="citation-snippet mt-2 text-sm text-gray-600 dark:text-gray-300 line-clamp-3">
            {citation.snippet}
          </p>
          {citation.source_url && (
            <a
              href={citation.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="citation-link mt-2 inline-flex items-center gap-1 text-sm font-medium text-primary hover:text-primary-light"
            >
              Xem toàn văn tại Cổng VBPL ↗
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function ReasoningSteps({ steps }: { steps: string[] }) {
  if (!steps || steps.length === 0) return null;

  return (
    <details className="reasoning-steps mt-4">
      <summary className="flex items-center gap-2 cursor-pointer text-sm font-medium text-amber-700 dark:text-amber-400">
        💭 Quá trình suy luận (nhấn để xem)
      </summary>
      <ol className="mt-2 pl-6 space-y-1">
        {steps.map((step, i) => (
          <li key={i} className="text-sm text-gray-600 dark:text-gray-400">
            {step}
          </li>
        ))}
      </ol>
    </details>
  );
}

export { MessageBubble };