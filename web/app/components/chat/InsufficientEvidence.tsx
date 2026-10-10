"use client";

import { cn } from "@/lib/utils";

interface InsufficientEvidenceProps {
  onNewQuery: () => void;
}

export function InsufficientEvidenceScreen({ onNewQuery }: InsufficientEvidenceProps) {
  return (
    <div className="insufficient-evidence-screen animate-fade-in">
      <div className="text-5xl mb-4">🔍</div>
      <h3 className="text-lg font-semibold text-red-700 dark:text-red-400 mb-2">
        Không đủ căn cứ pháp lý
      </h3>
      <p className="text-red-700 dark:text-red-400 mb-6 max-w-md mx-auto">
        Hệ thống không tìm thấy đủ văn bản pháp lý liên quan trong cơ sở dữ liệu để trả lời câu hỏi của bạn.
      </p>
      <div className="actions flex gap-3 justify-center flex-wrap">
        <button onClick={onNewQuery} className="btn-primary">
          Hỏi câu khác
        </button>
        <a
          href="https://vanban.chinhphu.vn"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary"
        >
          Xem Cổng VBPL
        </a>
        <a
          href="https://congbao.hanoi.gov.vn"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary"
        >
          Xem Công báo Hà Nội
        </a>
      </div>
    </div>
  );
}

export { InsufficientEvidenceScreen as InsufficientEvidence };