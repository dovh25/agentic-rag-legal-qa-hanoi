import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tra cứu pháp luật đất đai Hà Nội",
  description: "Agentic RAG Legal QA — câu trả lời có căn cứ và trích dẫn.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
