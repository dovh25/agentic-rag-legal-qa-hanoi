import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tra cứu Pháp luật Đất đai Hà Nội",
  description:
    "Tra cứu quy định đất đai, quy hoạch, thu hồi đất, bồi thường và tái định cư tại Hà Nội.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
