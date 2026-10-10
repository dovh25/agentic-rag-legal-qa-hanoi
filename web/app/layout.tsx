import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tra cứu Pháp luật Đất đai Hà Nội",
  description: "Agentic RAG Legal QA — câu trả lời có căn cứ, trích dẫn văn bản chính thức.",
  keywords: ["pháp luật", "đất đai", "Hà Nội", "bồi thường", "tái định cư", "thu hồi đất", "quy hoạch"],
  authors: [{ name: "Agentic RAG Legal QA Team" }],
  openGraph: {
    title: "Tra cứu Pháp luật Đất đai Hà Nội",
    description: "Hệ thống hỏi đáp pháp luật đất đai thông minh cho Hà Nội",
    type: "website",
    locale: "vi_VN",
  },
  twitter: {
    card: "summary_large_image",
    title: "Tra cứu Pháp luật Đất đai Hà Nội",
    description: "Hệ thống hỏi đáp pháp luật đất đai thông minh cho Hà Nội",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="chat-app theme-light">
        {children}
      </body>
    </html>
  );
}