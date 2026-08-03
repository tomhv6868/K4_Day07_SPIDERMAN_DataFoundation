import type { Metadata } from "next";
import { Shell } from "@/components/Shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "VinUni Knowledge Base — Demo K4 SPIDERMAN",
  description:
    "Demo RAG trên corpus chính sách thương mại điện tử Việt Nam: trò chuyện có hiển thị từng bước truy xuất và quản lý kho tài liệu.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
