"use client";

import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

interface ComposerProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function Composer({ onSubmit, disabled, placeholder }: ComposerProps) {
  const [draft, setDraft] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [draft]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const message = draft.trim();
    if (!message || disabled) return;
    setDraft("");
    onSubmit(message);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <form className="composer" onSubmit={handleSubmit}>
      <div className="composer-input-wrapper">
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? "Nhập câu hỏi về pháp luật đất đai Hà Nội… (Enter để gửi, Shift+Enter xuống dòng)"}
          rows={2}
          disabled={disabled}
          aria-label="Câu hỏi pháp lý"
          className={cn(
            "composer-textarea",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        />
        <button
          type="submit"
          disabled={disabled || !draft.trim()}
          className="send-button"
          aria-label={disabled ? "Đang xử lý..." : "Gửi câu hỏi"}
        >
          {disabled ? (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="spinner"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
              <path d="M12 2a10 10 0 0 1 10 10" strokeOpacity="1" />
            </svg>
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>
      <div className="composer-hints">
        <span>Enter để gửi · Shift+Enter xuống dòng</span>
        <span>⚠️ Chỉ mang tính tham khảo pháp lý</span>
      </div>
    </form>
  );
}

export { Composer };