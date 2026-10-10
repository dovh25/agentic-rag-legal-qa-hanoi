"use client";

import { cn } from "@/lib/utils";

interface CitationPanelProps {
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
  onClose?: () => void;
  onCitationClick?: (citation: any) => void;
}

export function CitationPanel({
  citations,
  onClose,
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
  onClose?: () => void;
  onCitationClick?: (citation: any) => void;
}) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-4 border-t border-border pt-4 animate-slide-down">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">📚</span>
          <strong className="text-sm font-medium">Căn cứ pháp lý</strong>
        </div>
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
      className={cn(
        "citation-card group cursor-pointer transition-all hover:shadow-md hover:border-primary/50",
        "rounded-lg border border-border bg-card p-4"
      )}
      onClick={() => onClick?.(citation)}
    >
      <div className="flex items-start gap-3">
        <span className="citation-index flex-shrink-0 text-primary font-bold">
          [{index + 1}]
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="citation-title font-medium text-text-primary">
              {citation.document_title}
            </span>
            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
              {citation.document_number}
            </span>
            {citation.article_ref && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                {citation.article_ref} {citation.clause ?? ""}
              </span>
            )}
            {citation.effective_date && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                Hiệu lực: {citation.effective_date}
              </span>
            )}
            <span className="relevance-score bg-muted px-2 py-0.5 rounded text-xs font-medium text-primary">
              Độ liên quan: {Math.round((citation.relevance_score ?? 0) * 100)}%
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

export { CitationPanel };