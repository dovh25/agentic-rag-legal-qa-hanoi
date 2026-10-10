import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { generateId } from "@/lib/utils";

export interface Citation {
  doc_id: string;
  document_title: string;
  document_number: string;
  article_ref?: string;
  clause?: string;
  snippet: string;
  source_url?: string;
  relevance_score?: number;
  effective_date?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  status?: "answered" | "clarification_needed" | "insufficient_evidence";
  route?: string;
  reasoning_steps?: string[];
  processing_time_ms?: number;
  timestamp: number;
}

export interface Conversation {
  id: string;
  title: string;
  updatedAt: number;
  messages: Message[];
}

interface ChatState {
  conversations: Conversation[];
  activeId: string | null;
  isLoading: boolean;
  streamingText: string;
  error: string | null;
  district: string;
  asOfDate: string;
  sidebarCollapsed: boolean;
  sidebarOpen: boolean;
  theme: "light" | "dark";

  // Actions
  setConversations: (conversations: Conversation[]) => void;
  setActiveConversation: (id: string) => void;
  newChat: () => void;
  deleteConversation: (id: string) => Promise<void>;
  renameConversation: (id: string, title: string) => void;
  addMessage: (conversationId: string, message: Message) => void;
  updateMessage: (conversationId: string, messageId: string, updates: Partial<Message>) => void;
  setLoading: (loading: boolean) => void;
  setStreamingText: (text: string) => void;
  setError: (error: string | null) => void;
  setDistrict: (district: string) => void;
  setAsOfDate: (date: string) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: "light" | "dark") => void;
  toggleTheme: () => void;
  newChat: () => void;
  submitQuery: (message: string) => Promise<void>;
}

const HANOI_DISTRICTS = [
  "Ba Đình", "Hoàn Kiếm", "Tây Hồ", "Long Biên", "Cầu Giấy", "Đống Đa",
  "Hai Bà Trưng", "Hoàng Mai", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm",
  "Hà Đông", "Sơn Tây", "Ba Vì", "Chương Mỹ", "Đan Phượng", "Đông Anh",
  "Gia Lâm", "Hoài Đức", "Mê Linh", "Mỹ Đức", "Phú Xuyên", "Phúc Thọ",
  "Quốc Oai", "Sóc Sơn", "Thạch Thất", "Thanh Oai", "Thanh Trì",
  "Thường Tín", "Ứng Hòa"
];

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function formatRelativeTime(timestamp: number): string {
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Vừa xong";
  if (diffMins < 60) return `${diffMins} phút trước`;
  if (diffHours < 24) return `${diffHours} giờ trước`;
  if (diffDays < 7) return `${diffDays} ngày trước`;
  return new Date(timestamp).toLocaleString("vi-VN", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  });
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: [],
      activeId: null,
      isLoading: false,
      streamingText: "",
      error: null,
      district: "",
      asOfDate: "",
      sidebarCollapsed: false,
      sidebarOpen: false,
      theme: "light",

      setConversations: (conversations) => set({ conversations }),

      setActiveConversation: (id) => set({ activeId: id }),

      newChat: () => {
        const conversation = {
          id: generateId(),
          title: "Phiên chat mới",
          updatedAt: Date.now(),
          messages: [],
        };
        set((state) => ({
          conversations: [conversation, ...state.conversations],
          activeId: conversation.id,
        }));
      },

      deleteConversation: async (id) => {
        set((state) => {
          const remaining = state.conversations.filter((c) => c.id !== id);
          return {
            conversations: remaining,
            activeId: remaining[0]?.id ?? null,
          };
        });
      },

      renameConversation: (id, title) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, title: title.slice(0, 80) } : c
          ),
        }));
      },

      addMessage: (conversationId, message) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === conversationId
              ? { ...c, messages: [...c.messages, message], updatedAt: Date.now() }
              : c
          ),
        }));
      },

      updateMessage: (conversationId, messageId, updates) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === messageId ? { ...m, ...updates } : m
                  ),
                }
                : c
          ),
        }));
      },

      setLoading: (loading) => set({ isLoading: loading }),
      setStreamingText: (text) => set({ streamingText: text }),
      setError: (error) => set({ error }),
      setDistrict: (district) => set({ district }),
      setAsOfDate: (date) => set({ asOfDate: date }),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
      toggleTheme: () => set((state) => ({ theme: state.theme === "light" ? "dark" : "light" })),

      newChat: () => {
        const conversation = {
          id: generateId(),
          title: "Phiên chat mới",
          updatedAt: Date.now(),
          messages: [],
        };
        set((state) => ({
          conversations: [conversation, ...state.conversations],
          activeId: conversation.id,
        }));
      },

      submitQuery: async (message: string) => {
        const { activeId, conversations, district, asOfDate } = get();
        let activeId = activeId;

        let conversation = conversations.find((c) => c.id === activeId);
        if (!conversation) {
          conversation = {
            id: generateId(),
            title: message.slice(0, 42),
            updatedAt: Date.now(),
            messages: [],
          };
          activeId = conversation.id;
          set({ conversations: [conversation, ...get().conversations], activeId });
        }

        const userMessage = {
          id: generateId(),
          role: "user" as const,
          content: message,
          citations: [],
        };

        const context = conversation.messages.slice(-12);
        const next = {
          ...conversation,
          title: conversation.messages.length ? conversation.title : message.slice(0, 42),
          messages: [...conversation.messages, userMessage],
        };

        get().addMessage(conversation.id, userMessage);
        set({ isLoading: true, streamingText: "", error: "" });

        try {
          const response = await fetch("/api/v1/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message,
              context: context.map((m) => ({
                role: m.role,
                content: m.content,
              })),
              district: get().district || undefined,
              as_of_date: get().asOfDate || undefined,
            }),
          });

          if (!response.ok || !response.body) {
            throw new Error(`API error ${response.status}`);
          }

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
              const payload = JSON.parse(line.slice(6)) as {
                type: string;
                response?: any;
                message?: string;
                text?: string;
              };

              if (payload.type === "error") throw new Error(payload.message ?? "Lỗi xử lý chat.");
              if (payload.type === "text_delta") {
                set((state) => ({ streamingText: state.streamingText + (payload.text ?? "") }));
              }
              if (payload.type === "message_completed" && payload.response) {
                completed = payload.response;
              }
            }
            if (done) break;
          }

          if (!completed) throw new Error("API không gửi message_completed.");

          const assistant = {
            id: generateId(),
            role: "assistant" as const,
            content: completed.answer ?? completed.clarification_question ?? "Chưa có câu trả lời.",
            citations: completed.citations ?? [],
            status: completed.status,
            route: completed.route,
            reasoning_steps: completed.reasoning_steps,
            processing_time_ms: completed.processing_time_ms,
          };

          get().addMessage(conversation.id, assistant);
          get().updateConversation(next);
        } catch (error) {
          set({ error: error instanceof Error ? error.message : "Không thể kết nối API." });
        } finally {
          set({ isLoading: false, streamingText: "" });
        }
      },
    }),
    {
      name: "luat-gpt-chat",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        conversations: state.conversations,
        activeId: state.activeId,
        district: state.district,
        asOfDate: state.asOfDate,
        sidebarCollapsed: state.sidebarCollapsed,
        theme: state.theme,
      }),
    }
  )
);