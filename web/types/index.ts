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

export interface ChatResponse {
  status: "answered" | "clarification_needed" | "insufficient_evidence";
  answer?: string;
  clarification_question?: string;
  citations: Citation[];
  reasoning_steps: string[];
  route?: string;
  sub_queries?: string[];
  processing_time_ms?: number;
  as_of_date_applied?: string;
}

export interface CitationCardProps {
  citation: Citation;
  index: number;
}

export interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
  streamingText?: string;
}

export interface ComposerProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export interface CitationPanelProps {
  citations: Citation[];
  onClose?: () => void;
}

export interface ClarificationDialogProps {
  question: string;
  onContinue: (formData: FormData) => void;
  onCancel?: () => void;
}

export interface InsufficientEvidenceProps {
  onNewQuery: () => void;
}

export interface Conversation {
  id: string;
  title: string;
  updatedAt: number;
  messages: Message[];
}

export interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
}

export interface HeaderProps {
  activeConversation?: Conversation | null;
  onNewChat: () => void;
  onThemeToggle: () => void;
  theme: "light" | "dark";
  district: string;
  onDistrictChange: (district: string) => void;
  asOfDate: string;
  onAsOfDateChange: (date: string) => void;
}

export interface HANOI_DISTRICTS {
  value: string;
  label: string;
}