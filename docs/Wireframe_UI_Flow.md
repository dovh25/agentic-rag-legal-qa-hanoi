# Wireframe & UI Flow Specification
# Agentic RAG Legal QA — Hà Nội

> **Loại tài liệu**: Wireframe & UI Flow (Medium Fidelity)
> **Phiên bản**: v1.1 | **Ngày**: 2026-10-04 | **Tác giả**: Vũ Huy Đô
> **Stack UI**: React / Next.js + Vanilla CSS (hoặc Tailwind v3)

---

## Mục lục

1. [Tổng quan UI Architecture](#1-tổng-quan-ui-architecture)
2. [Design System](#2-design-system)
3. [Danh sách màn hình](#3-danh-sách-màn-hình)
4. [User Flows](#4-user-flows)
5. [Wireframes chi tiết](#5-wireframes-chi-tiết)
6. [Component Library](#6-component-library)
7. [Responsive & Accessibility](#7-responsive--accessibility)
8. [Interaction States](#8-interaction-states)

---

## 1. Tổng quan UI Architecture

### 1.1 Sitemap

```mermaid
graph TD
    ROOT["/\nLanding / Home"] --> CHAT["/chat\nChat Interface"]
    ROOT --> DOCS["/documents\nDocument Browser"]
    ROOT --> ADMIN["/admin\nAdmin Panel"]
    CHAT --> CHAT_S["/chat?session=id\nTiếp tục phiên chat"]
    ADMIN --> CORPUS["/admin/corpus\nQuản lý Corpus"]
    ADMIN --> ANALYTICS["/admin/analytics\nDashboard Analytics"]
```

### 1.2 Page Layout Architecture

```mermaid
graph TB
    subgraph PAGE["Page Shell"]
        NAV["TOP NAV BAR\nLogo · Trang chủ · Hướng dẫn · Về chúng tôi · API Docs"]
        CONTENT["PAGE CONTENT\n(thay đổi theo route)"]
        FOOTER["FOOTER\nDisclaimer pháp lý · Liên hệ · VBPL link"]
    end
    NAV --> CONTENT --> FOOTER
```

---

## 2. Design System

### 2.1 Color Palette

```
Primary Colors:
  --color-primary:        #1B4F72    ← Xanh navy đậm (trust, authority)
  --color-primary-light:  #2E86C1    ← Xanh navy nhạt
  --color-primary-hover:  #154360    ← Hover state

Accent Colors:
  --color-accent:         #E67E22    ← Cam (highlight, CTA)
  --color-accent-light:   #F39C12    ← Cam nhạt

Semantic Colors:
  --color-success:        #27AE60    ← Xanh lá (answered, positive)
  --color-warning:        #F39C12    ← Vàng (clarification_needed)
  --color-danger:         #E74C3C    ← Đỏ (insufficient_evidence, error)
  --color-info:           #2980B9    ← Xanh info

Neutral Colors:
  --color-bg:             #F8F9FA    ← Background trang
  --color-bg-card:        #FFFFFF    ← Background card
  --color-bg-chat:        #EBF5FB    ← Background chat area
  --color-text-primary:   #1A1A2E    ← Văn bản chính
  --color-text-secondary: #5D6D7E    ← Văn bản phụ
  --color-border:         #D5D8DC    ← Border mặc định

Status Badge Colors:
  answered:               bg #D5F5E3, text #1E8449
  clarification_needed:   bg #FDEBD0, text #A04000
  insufficient_evidence:  bg #FDEDEC, text #922B21
```

### 2.2 Typography

```
Font Family:
  Primary: 'Inter', 'Be Vietnam Pro', sans-serif
  Monospace: 'JetBrains Mono', monospace (cho code, số hiệu văn bản)

Font Scale:
  --text-xs:   0.75rem  / 12px    ← Caption, metadata
  --text-sm:   0.875rem / 14px   ← Secondary text
  --text-base: 1rem     / 16px   ← Body text
  --text-lg:   1.125rem / 18px   ← Subheading
  --text-xl:   1.25rem  / 20px   ← Heading card
  --text-2xl:  1.5rem   / 24px   ← Page heading
  --text-3xl:  1.875rem / 30px   ← Hero heading

Font Weight:
  Regular: 400 | Medium: 500 | Semibold: 600 | Bold: 700
```

### 2.3 Spacing & Layout

```
Base unit: 4px
--space-1: 4px  --space-2: 8px   --space-3: 12px  --space-4: 16px
--space-6: 24px --space-8: 32px  --space-12: 48px

Border Radius: sm=4px  md=8px  lg=12px  xl=16px  full=9999px
Shadows: sm=0 1px 2px rgba(0,0,0,.05)  md=0 4px 6px rgba(0,0,0,.07)
```

---

## 3. Danh sách màn hình

| Screen ID | Tên màn hình | Mô tả | Persona |
|---|---|---|---|
| SCR-01 | Landing Page | Trang giới thiệu, CTA vào chat | Tất cả |
| SCR-02 | Chat Interface | Giao diện hỏi đáp chính | Tất cả |
| SCR-03 | Citation Detail Drawer | Chi tiết trích dẫn văn bản | Tất cả |
| SCR-04 | Filter Panel | Bộ lọc ngày, quận/huyện | Tất cả |
| SCR-05 | Clarification Dialog | Hệ thống hỏi lại người dùng | Tất cả |
| SCR-06 | Document Browser | Danh sách văn bản trong corpus | Luật sư, Cán bộ |
| SCR-07 | Admin Corpus Manager | Quản lý ingest văn bản | Admin |
| SCR-08 | Insufficient Evidence Screen | Không đủ căn cứ pháp lý | Tất cả |

---

## 4. User Flows

### 4.1 Flow 1: Happy Path — Single-hop Query (Người dân)

```mermaid
flowchart TD
    A([Người dùng\nLanding Page]) -->|Click 'Bắt đầu tra cứu'| B[SCR-02\nChat Interface\nEmpty State]
    B -->|Nhập câu hỏi về bồi thường\nở Đông Anh| C[Thinking State\nskeleton loader]
    C --> D{Agent Processing}
    D -->|router → single_hop\nretriever K=5\ngrader → sufficient\ngenerator| E[SCR-02\nAnswer Display\nStatus: Đã trả lời]
    E -->|Click citation card 1| F[SCR-03\nCitation Detail Drawer\nslide-in từ phải]
    F -->|Click ×| E
    E -->|Click 👍 / 👎| G[Feedback toast\nCảm ơn phản hồi!]
    E -->|Nhập câu hỏi tiếp theo| B
```

### 4.2 Flow 2: Multi-hop Query (Luật sư)

```mermaid
flowchart TD
    A([Luật sư\nChat Interface]) -->|Nhập câu hỏi so sánh\nLuật 2013 vs 2024| B[Thinking State\nProgress Indicator]
    B --> C{router → multi_hop}
    C --> D["Planner tạo 3 sub-queries\n1. Luật 45/2013 — bồi thường đất NN\n2. Luật 31/2024 — bồi thường đất NN\n3. Đất trồng cây hàng năm Đông Anh"]
    D --> E[Sub-query Progress Display\nStep 1/3 ✓ → Step 2/3 ✓ → Step 3/3 ✓]
    E --> F[SCR-02\nStructured Answer\nBảng so sánh markdown\nCitations phân theo từng luật\nProcessing: ~11s]
```

### 4.3 Flow 3: Clarification (Câu hỏi mơ hồ)

```mermaid
flowchart TD
    A([Người dùng]) -->|Nhập: 'Tôi được\nbao nhiêu tiền?'| B[Thinking State ~500ms]
    B --> C{router → clarification}
    C --> D[SCR-05\nClarification Form\n1. Loại đất?\n2. Quận/huyện?\n3. Diện tích?]
    D -->|Chọn: Đất ở, Đông Anh, 120m²\nClick Tiếp tục →| E[Câu hỏi được làm rõ\nChạy lại từ router]
    E --> F[Flow 1\nSingle-hop answer]
```

### 4.4 Flow 4: Insufficient Evidence

```mermaid
flowchart TD
    A([Người dùng]) -->|Nhập: 'Giá đất đường\nHoàng Quốc Việt?'| B[Thinking State]
    B --> C{retriever → grader}
    C -->|0/5 chunks\npass threshold| D[SCR-08\nInsufficient Evidence Response]
    D --> E{Người dùng chọn}
    E -->|Xem UBND| F[Link UBND Hà Nội]
    E -->|Xem VBPL| G[Link Cổng VBPL]
    E -->|Hỏi câu khác| A
```

### 4.5 Flow 5: Admin Corpus Ingest

```mermaid
flowchart TD
    A([Admin\n/admin/corpus]) -->|Click Thêm văn bản mới| B[Upload Modal\nKéo thả PDF/DOCX\nNhập metadata]
    B -->|Click Xử lý & Nạp| C{Ingestion Pipeline}
    C --> D[Trích xuất text ✓]
    D --> E[Chunking: 142 chunks ✓]
    E --> F[Embedding đang xử lý...]
    F --> G[Qdrant Upsert...]
    G --> H[SCR-07\nCorpus Manager\nVăn bản mới: Đã nạp\n142 chunks]
```

---

## 5. Wireframes chi tiết

> Wireframes dưới đây mô tả layout và component placement. Xem Design System (mục 2) để biết thông số màu sắc, typography, spacing.

### SCR-01: Landing Page

```mermaid
graph TB
    subgraph LANDING["SCR-01: Landing Page"]
        NAV1["NAV: ⚖️ Logo | Hướng dẫn | API | Về chúng tôi"]
        HERO["HERO SECTION\n⚖️ Tra cứu Pháp Luật Đất Đai Thành phố Hà Nội\nHỏi đáp thông minh về quy hoạch, bồi thường và tái định cư\n[ Nhập câu hỏi của bạn... ]\n[ Bắt đầu tra cứu → ]"]
        STATS["STATS ROW\n📋 50+ văn bản | ⚡ <60 giây | 🔗 Trích dẫn xác thực"]
        FAQ["CÂU HỎI THƯỜNG GẶP\n• Thu hồi đất ở Đông Anh được bồi thường như thế nào?\n• Điều kiện được tái định cư tại Hà Nội là gì?\n• Luật Đất đai 2024 thay đổi gì so với 2013?"]
        DISCLAIMER["⚠️ Hệ thống hỗ trợ tra cứu — không thay thế tư vấn pháp lý"]
        FOOTER1["FOOTER: © 2024 | VBPL | Liên hệ | Chính sách bảo mật"]
    end
    NAV1 --> HERO --> STATS --> FAQ --> DISCLAIMER --> FOOTER1
```

### SCR-02: Chat Interface (Layout)

```mermaid
graph LR
    subgraph CHAT_UI["SCR-02: Chat Interface"]
        subgraph SIDEBAR["SIDEBAR (240px)"]
            HIST["LỊCH SỬ\n• Phiên này\n• 2 ngày trước\n• 1 tuần trước"]
            FILTER["BỘ LỌC\nThời điểm: [01/08/2024 ▾]\nQuận/huyện: [Đông Anh ▾]\nLoại VB: [Tất cả ▾]\n[ Áp dụng ]"]
        end

        subgraph MAIN["CHAT AREA (flex-1)"]
            TOPBAR["⚖️ Pháp Lý Đất Đai HN   [ + Hội thoại mới ]"]
            MSGS["MESSAGE THREAD\n[User Bubble — right aligned]\n[Agent Bubble — left aligned + citations]\n[Reasoning steps collapsible]"]
            INPUT["INPUT BAR\n[ Nhập câu hỏi tiếp theo...  ] [ Gửi → ]\n⚠️ Chỉ hỗ trợ tra cứu, không phải tư vấn pháp lý"]
        end
    end
    SIDEBAR --- MAIN
```

### SCR-02: Agent Answer Bubble (Component Detail)

```mermaid
graph TB
    subgraph AGENT_MSG["Agent Message Bubble"]
        ANSWER_TEXT["📝 ANSWER TEXT\nTrả lời đầy đủ với inline citations [¹][²]\n(Markdown rendered: bold, table, list)"]
        DIVIDER["─────── TRÍCH DẪN NGUỒN ───────"]
        subgraph CIT1["Citation Card [1]"]
            C1H["Luật Đất đai 2024 (31/2024/QH15)"]
            C1D["Điều 94, Khoản 1 | Hiệu lực: 01/08/2024"]
            C1S["Score: ████████░ 0.94"]
            C1L["[ Xem toàn văn → ]"]
        end
        subgraph CIT2["Citation Card [2]"]
            C2H["NĐ 71/2024/NĐ-CP"]
            C2D["Điều 23, Khoản 2 | Hiệu lực: 01/08/2024"]
            C2S["Score: ███████░░ 0.88"]
            C2L["[ Xem toàn văn → ]"]
        end
        STATUS["✅ Đã trả lời | 3.2s | gpt-4o-mini"]
        FEEDBACK["👍 Hữu ích? [ 👍 ] [ 👎 ]"]
        RELATED["Câu hỏi liên quan:\n• Hỗ trợ tái định cư tại Đông Anh?\n• Thủ tục khiếu nại về bồi thường?"]
        REASONING["▼ 💭 Reasoning (thu gọn được)\n1. Phân loại: single_hop\n2. Retrieve: 5 chunks từ Qdrant\n3. Grade: 4/5 pass threshold\n4. Generate: tổng hợp 4 chunks"]
    end

    ANSWER_TEXT --> DIVIDER --> CIT1 & CIT2 --> STATUS --> FEEDBACK --> RELATED --> REASONING
```

### SCR-03: Citation Detail Drawer

```mermaid
graph TB
    subgraph DRAWER["SCR-03: Citation Detail Drawer (slide-in phải, width 420px)"]
        DH["Chi tiết Trích dẫn                    [ × ]"]
        DNAME["📋 LUẬT ĐẤT ĐAI 2024\nSố 31/2024/QH15"]
        DMETA["Cơ quan ban hành: Quốc hội\nNgày ban hành:    18/01/2024\nNgày hiệu lực:    01/08/2024\nTrạng thái:  ✅ Còn hiệu lực"]
        DART["Điều 94. Bồi thường về đất khi Nhà nước thu hồi đất\nKhoản 1:"]
        DQUOTE["❝ Giá đất bồi thường là giá đất cụ thể\n  do UBND cấp tỉnh quyết định tại thời điểm\n  quyết định thu hồi đất theo nguyên tắc\n  quy định tại Điều 158... ❞"]
        DSCORE["Relevance score: ████████░ 0.94"]
        DBTNS["[ 🔗 Xem toàn văn tại VBPL → ]   [ 📋 Copy trích dẫn ]"]
    end
    DH --> DNAME --> DMETA --> DART --> DQUOTE --> DSCORE --> DBTNS
```

### SCR-02: Thinking / Loading State (Multi-hop)

```mermaid
graph TB
    subgraph LOADING["Loading State — Multi-hop"]
        Q["👤 So sánh điều kiện bồi thường đất NN\n   theo Luật 2013 và Luật 2024..."]
        subgraph PROGRESS["⚖️ Đang xử lý câu hỏi của bạn..."]
            S1["✅ Phân tích câu hỏi: multi-hop"]
            S2["✅ Lập kế hoạch 3 truy vấn con"]
            S3["🔄 Tra cứu [1/3]: Luật 2013... ████░░░"]
            S4["⏳ Tra cứu [2/3]: Luật 2024..."]
            S5["⏳ Tra cứu [3/3]: Quy định Đông Anh..."]
            SK["░░░░░░░░░░░░░░ skeleton text preview ░░░░"]
        end
    end
    Q --> PROGRESS
    S1 --> S2 --> S3 --> S4 --> S5 --> SK
```

### SCR-07: Admin Corpus Manager

```mermaid
graph TB
    subgraph ADMIN_UI["SCR-07: Admin Corpus Manager"]
        ATOP["⚖️ Admin — Quản lý Corpus                    [ ← Thoát ]"]
        subgraph STATS_ROW["Thống kê tổng quan"]
            ST1["52 văn bản\ntrong corpus"]
            ST2["7,340 chunks\nđã index"]
            ST3["1,247 truy vấn\nhôm nay"]
            ST4["94.2%\nFaithfulness"]
        end
        ACTIONS["[ + Thêm văn bản mới ]  [ 🔄 Cập nhật metadata ]  [ Xuất báo cáo ]"]
        subgraph TABLE["Danh sách văn bản"]
            TH["# | Tên văn bản | Số hiệu | Chunks | Trạng thái"]
            R1["1 | Luật Đất đai 2024 | 31/2024/QH15 | 2,140 | ✅ Hiệu lực"]
            R2["2 | NĐ bồi thường, TĐC | 71/2024/NĐ-CP | 890 | ✅ Hiệu lực"]
            R3["3 | Luật Đất đai 2013 | 45/2013/QH13 | 1,850 | ⛔ Hết hiệu lực"]
        end
    end
    ATOP --> STATS_ROW --> ACTIONS --> TABLE
```

### SCR-05: Clarification Dialog (inline trong chat)

```mermaid
graph TB
    subgraph CLARIF["SCR-05: Clarification Card (inline trong chat bubble)"]
        CH["🤔 Tôi cần thêm thông tin để trả lời chính xác:"]
        Q1["1. Bạn đang hỏi về loại đất gì?\n   [ Đất ở ] [ Đất nông nghiệp ] [ Loại khác ]"]
        Q2["2. Địa bàn cụ thể:\n   [ Chọn quận/huyện ▾ ]"]
        Q3["3. Diện tích đất (tuỳ chọn):\n   [ ________ ] m²"]
        BTN["[ Tiếp tục → ]"]
    end
    CH --> Q1 --> Q2 --> Q3 --> BTN
```

---

## 6. Component Library

### 6.1 Chat Message Components

**UserMessage**
```
Properties:
  - content: string (markdown support)
  - timestamp: Date
  - sessionId: string

Visual:
  - Alignment: right
  - Background: --color-primary (dark blue)
  - Text: white
  - Border radius: 12px 12px 2px 12px (bottom-right square)
  - Max width: 75%
```

**AgentMessage**
```
Properties:
  - content: string (markdown support, table support)
  - status: "answered" | "clarification_needed" | "insufficient_evidence"
  - citations: Citation[]
  - reasoning_steps: string[]
  - route: string
  - processing_time_ms: number
  - timestamp: Date

Visual:
  - Alignment: left
  - Background: white
  - Border: 1px solid --color-border
  - Border radius: 12px 12px 12px 2px (bottom-left square)
  - Max width: 90%
  - Shadow: --shadow-sm
```

**StatusBadge**
```
Variants:
  - answered:               green bg  — "✅ Đã trả lời"
  - clarification_needed:   orange bg — "🤔 Cần làm rõ"
  - insufficient_evidence:  red bg    — "⚠️ Không đủ căn cứ"
  - loading:                gray bg   — animated dots
```

**CitationCard**
```
Properties:
  - index: number (shown as [1], [2]...)
  - document_title: string
  - document_number: string
  - article_ref: string
  - effective_date: Date
  - expiry_date: Date | null
  - source_url: string
  - relevance_score: number (0–1)
  - is_expired: boolean

Visual:
  - Compact card với left border accent color
  - Expired docs: strikethrough + red warning badge
  - Click → opens Citation Detail Drawer
  - Relevance bar: thin progress bar 0–100%
```

### 6.2 Input Components

**QueryInput**
```
Properties:
  - placeholder: "Nhập câu hỏi về pháp luật đất đai..."
  - maxLength: 500
  - onSubmit: (query: string) => void
  - isLoading: boolean
  - suggestions: string[]

Features:
  - Character counter (500 ký tự)
  - Enter → gửi, Shift+Enter → xuống dòng
  - Disabled khi isLoading
  - Auto-resize textarea
```

**FilterPanel**
```
Components:
  - DatePicker: as_of_date (mặc định = hôm nay)
  - DistrictSelect: dropdown 30 quận/huyện HN
  - DocumentTypeCheckboxes: Luật / NĐ / TT / QĐ
  - [ Reset bộ lọc ] button
```

### 6.3 Feedback Component

**FeedbackBar**
```
- Thumbs up: green on hover/active
- Thumbs down: red on hover/active
- After click: show optional comment textarea
- Submit feedback → POST /api/v1/feedback
- Toast: "Cảm ơn phản hồi của bạn!"
```

---

## 7. Responsive & Accessibility

### 7.1 Breakpoints & Layout

```mermaid
graph LR
    subgraph MOBILE["Mobile < 768px"]
        M["Single column\nNo sidebar history\nFilter trong modal"]
    end
    subgraph TABLET["Tablet 768–1024px"]
        T["Collapsible sidebar\nFilters in modal\nChat full width"]
    end
    subgraph DESKTOP["Desktop > 1024px"]
        D["3 columns:\nSidebar | Chat | Filter panel"]
    end
    MOBILE --> TABLET --> DESKTOP
```

### 7.2 Accessibility (WCAG 2.1 AA)

| Yêu cầu | Triển khai |
|---|---|
| Keyboard navigation | Tab order logic, Enter/Space cho buttons |
| Screen reader | aria-label cho tất cả icon buttons |
| Color contrast | Minimum 4.5:1 cho text, 3:1 cho UI elements |
| Focus indicator | Visible 2px outline trên focused elements |
| Loading state | aria-live="polite" thông báo khi có kết quả |
| Error state | aria-invalid + role="alert" cho error messages |
| Citation links | Descriptive link text (không dùng "click here") |

---

## 8. Interaction States

### 8.1 Query Input States

| State | Visual |
|---|---|
| Default | Border: --color-border, placeholder text |
| Focused | Border: --color-primary, blue glow shadow |
| Loading | Disabled + spinner icon |
| Error | Border: --color-danger, error message below |
| Max length | Counter turns red at 490/500 ký tự |

### 8.2 Agent Response States

```mermaid
stateDiagram-v2
    [*] --> RouterThinking : User submits query
    RouterThinking --> Retrieving : route determined
    Retrieving --> Generating : docs retrieved & graded
    Generating --> Answered : sufficient evidence
    Generating --> InsufficientEvidence : not enough context
    RouterThinking --> ClarificationNeeded : query too vague
    Answered --> [*]
    InsufficientEvidence --> [*]
    ClarificationNeeded --> RouterThinking : user clarifies
```

| State | Visual | Duration |
|---|---|---|
| Router thinking | Animated dots "Đang phân tích..." | 0–1s |
| Retrieving | Progress steps visible | 1–5s |
| Generating | Skeleton loader for text | 1–8s |
| Answered | Full response rendered | Final |
| Error | Red error card + retry button | Final |

### 8.3 Micro-animations

| Element | Animation |
|---|---|
| Chat message appear | Fade in + slide up (200ms ease-out) |
| Citation card click | Scale 0.98 → 1.0 (100ms) |
| Drawer slide-in | translateX(100%) → 0 (300ms ease-out) |
| Status badge | Fade in (150ms) |
| Feedback thumbs | Scale pulse (200ms) on click |
| Thinking dots | CSS keyframe bounce, stagger 200ms |

---

## Phụ lục: Mockup Notes

### Thiếu trong Wireframe (để Designer hoàn thiện)
- Logo & brand identity (cần thiết kế chính thức)
- Illustration/icon set phong cách nhất quán
- Dark mode variant
- Error 404 / 500 pages
- Onboarding tour (first visit)

### Design Handoff Checklist
- [ ] Figma file với component library đầy đủ
- [ ] Design tokens export (CSS variables)
- [ ] Interactive prototype cho Flow 1–4
- [ ] Asset export (SVG icons, logo)
- [ ] Spacing & layout specifications

---

*Wireframe & UI Flow v1.1 — Xem PRD.md và Brief.md để biết context đầy đủ.*
