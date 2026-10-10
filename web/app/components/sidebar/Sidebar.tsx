"use client";

import { useState, useRef, useEffect } from "react";
import { cn, formatRelativeTime } from "@/lib/utils";
import { Conversation } from "@/types";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
  onRename,
  isCollapsed = false,
  onToggleCollapse,
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);

  const filteredConversations = conversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group conversations by time
  const groupedConversations = filteredConversations.reduce((acc, conv) => {
    const date = new Date(conv.updatedAt);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    let groupKey = "Cũ hơn";
    if (date.toDateString() === today.toDateString()) {
      groupKey = "Hôm nay";
    } else if (date.toDateString() === yesterday.toDateString()) {
      groupKey = "Hôm qua";
    } else if (date > new Date(today.getTime() - 7 * 86400000)) {
      groupKey = "Tuần này";
    }

    if (!acc[groupKey]) acc[groupKey] = [];
    acc[groupKey].push(conv);
    return acc;
  }, {} as Record<string, Conversation[]>);

  return (
    <aside
      className={cn(
        "sidebar bg-card border-r border-border flex flex-col transition-all duration-300",
        isCollapsed ? "w-16" : "w-72"
      )}
      aria-label="Lịch sử phiên chat"
    >
      {/* Brand */}
      <div className="brand flex items-center gap-2 p-4 border-b border-border">
        {!isCollapsed && (
          <>
            <span className="text-2xl">🏛️</span>
            <strong className="text-lg font-semibold text-text-primary">Luật GPT</strong>
          </>
        )}
      </div>

      {/* New Chat Button */}
      <button
        onClick={onNewChat}
        className={cn(
          "new-chat w-full justify-start gap-2 px-3 py-2.5 rounded-lg transition-colors",
          isCollapsed && "px-2 justify-center"
        )}
        aria-label="Chat mới"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        {!isCollapsed && <span className="font-medium text-sm">Chat mới</span>}
      </button>

      {/* Search */}
      {!isCollapsed && (
        <div className="p-3 border-b border-border">
          <div className="relative">
            <input
              ref={searchRef}
              type="text"
              placeholder="Tìm kiếm hội thoại..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 bg-muted border border-border rounded-lg text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Tìm kiếm hội thoại..."
              aria-label="Tìm kiếm hội thoại"
            />
          </div>
        </div>
      )}

      {/* Conversation History */}
      <div className="history flex-1 overflow-y-auto p-3 space-y-1">
        {Object.entries(groupedConversations).map(([group, convs]) => (
          <div key={group} className="space-y-1">
            <div className="px-2 py-1 text-xs font-medium text-muted-foreground uppercase tracking-wider">
              {group}
            </div>
            {convs.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={conversation.id === activeId}
                isCollapsed={isCollapsed}
                onSelect={onSelect}
                onDelete={onDelete}
                onRename={onRename}
              />
            ))}
          </div>
        ))}

        {/* Empty state */}
        {conversations.length === 0 && (
          <div className="p-4 text-center text-muted-foreground text-sm">
            Chưa có cuộc hội thoại nào
          </div>
        )}
      </div>

      {/* Storage Note */}
      {!isCollapsed && (
        <div className="storage-note p-3 border-t border-border">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="3" width="20" height="14" rx="2" />
              <path d="M8 21h8" />
              <path d="M12 17v4" />
            </svg>
            Lịch sử chỉ lưu trên trình duyệt này
          </div>
        </div>
      )}

      {/* Collapse Toggle */}
      <button
        onClick={onToggleCollapse}
        className="absolute bottom-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-muted border border-border flex items-center justify-center hover:bg-muted/50 transition-colors"
        aria-label={isCollapsed ? "Mở rộng sidebar" : "Thu gọn sidebar"}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          {isCollapsed ? (
            <>
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </>
          ) : (
            <>
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 12 12 12 5" />
              <polyline points="19 12 12 12 5 12" />
            </>
          )}
        </svg>
      </button>
    </aside>
  );
}

function ConversationItem({
  conversation,
  isActive,
  isCollapsed,
  onSelect,
  onDelete,
  onRename,
}: {
  conversation: Conversation;
  isActive: boolean;
  isCollapsed: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect(conversation.id);
  };

  const handleDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    const title = window.prompt("Tên phiên chat", conversation.title)?.trim();
    if (title) {
      onRename(conversation.id, title.slice(0, 80));
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(false);
    if (window.confirm(`Xóa phiên "${conversation.title}"?`)) {
      onDelete(conversation.id);
    }
  };

  const handleRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(false);
    const title = window.prompt("Tên phiên chat", conversation.title)?.trim();
    if (title) {
      onRename(conversation.id, title.slice(0, 80));
    }
  };

  return (
    <div className="relative group">
      <div
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        className={cn(
          "history-row w-full rounded-lg transition-colors",
          isActive && "bg-primary/10 border-l-2 border-primary"
        )}
        aria-label={conversation.title}
        aria-current={isActive ? "true" : "false"}
      >
        {!isCollapsed && (
          <button
            className="flex flex-col flex-1 p-2 text-left text-text-primary hover:bg-accent rounded-lg transition-colors"
            onClick={handleClick}
            onDoubleClick={handleDoubleClick}
          >
            <span className="history-title font-medium truncate">
              {conversation.title}
            </span>
            <span className="history-time text-xs text-muted-foreground mt-1 block">
              {formatRelativeTime(conversation.updatedAt)}
            </span>
          </button>
        )}
        <button
          className={cn(
            "p-1.5 rounded transition-colors text-muted-foreground hover:text-red-500",
            isCollapsed ? "mx-auto" : "absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100"
          )}
          onClick={onDelete}
          aria-label={`Xóa ${conversation.title}`}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>
    );
  }

export { Sidebar };