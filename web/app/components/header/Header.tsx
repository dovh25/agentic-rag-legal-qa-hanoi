"use client";

import { useState, useRef } from "react";
import { cn } from "@/lib/utils";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/app/components/ui/Select";
import { Button } from "@/app/components/ui/Button";
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/app/components/ui/Dialog";
import { Input } from "@/app/components/ui/Input";
import { format } from "date-fns";

interface HeaderProps {
  activeConversation: {
    id: string;
    title: string;
  } | null;
  onNewChat: () => void;
  onThemeToggle: () => void;
  theme: "light" | "dark";
  district: string;
  onDistrictChange: (district: string) => void;
  asOfDate: string;
  onAsOfDateChange: (date: string) => void;
}

const HANOI_DISTRICTS = [
  "Ba Đình", "Hoàn Kiếm", "Tây Hồ", "Long Biên", "Cầu Giấy", "Đống Đa",
  "Hai Bà Trưng", "Hoàng Mai", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm",
  "Hà Đông", "Sơn Tây", "Ba Vì", "Chương Mỹ", "Đan Phượng", "Đông Anh",
  "Gia Lâm", "Hoài Đức", "Mê Linh", "Mỹ Đức", "Phú Xuyên", "Phúc Thọ",
  "Quốc Oai", "Sóc Sơn", "Thạch Thất", "Thanh Oai", "Thanh Trì",
  "Thường Tín", "Ứng Hòa"
];

export function Header({
  activeConversation,
  onNewChat,
  onThemeToggle,
  theme,
  district,
  onDistrictChange,
  asOfDate,
  onAsOfDateChange,
}: HeaderProps) {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <header className="chat-header sticky top-0 z-40 flex items-center justify-between gap-4 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60 px-4 py-3">
      <div className="flex items-center gap-4 min-w-0">
        <p className="eyebrow text-xs font-bold uppercase tracking-wider text-primary">
          LUẬT GPT · HÀ NỘI
        </p>
        <h1 className="font-semibold text-lg text-text-primary truncate">
          {activeConversation?.title ?? "Bạn muốn tra cứu điều gì?"}
        </h1>
      </div>

      <div className="filters flex items-center gap-2 flex-wrap">
        <Select value={district} onValueChange={onDistrictChange}>
          <SelectTrigger className="w-[160px] min-w-0" aria-label="Quận/huyện">
            <SelectValue placeholder="Toàn Hà Nội" />
          </SelectTrigger>
          <SelectContent>
            <option value="">Toàn Hà Nội</option>
            {HANOI_DISTRICTS.map((d) => (
              <SelectItem key={d} value={d}>{d}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <input
          type="date"
          value={asOfDate}
          onChange={(e) => onAsOfDateChange(e.target.value)}
          aria-label="Ngày áp dụng"
          className="w-[160px] min-w-0"
        />

        <button
          onClick={onThemeToggle}
          className="theme-toggle p-2 rounded-lg border border-border bg-card text-text-primary hover:bg-accent hover:text-accent-foreground transition-colors"
          aria-label={theme === "light" ? "Chế độ tối" : "Chế độ sáng"}
        >
          {theme === "light" ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </button>

        <button
          onClick={onNewChat}
          className="ml-2 btn-primary px-4 py-2"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-1">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span className="hidden sm:inline">Chat mới</span>
        </button>
      </div>
    </header>
  );
}

export { Header };