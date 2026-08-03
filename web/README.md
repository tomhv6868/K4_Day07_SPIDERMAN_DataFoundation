# Demo frontend — VinUni Knowledge Base (K4 · SPIDERMAN)

Giao diện demo cho pipeline RAG ở `src/`. Hai trang:

1. **`/` — Trò chuyện.** Giao diện chat; mỗi câu trả lời có bảng tiến trình thu gọn,
   bấm mũi tên để mở ra xem từng bước pipeline đang chạy: nạp mô hình nhúng → nạp
   index → áp bộ lọc metadata → tìm kiếm vector (kèm top-k chunk, điểm cosine,
   `doc_id`, link nguồn) → sinh câu trả lời. Các bước đẩy về qua SSE theo thời gian
   thực, không phải hiệu ứng giả.
2. **`/documents` — Kho tài liệu.** Thống kê corpus, bảng 10 tài liệu với
   `customer_role`, `category`, số chunk theo chiến lược đang chọn, phiên bản,
   link nguồn; bấm tiêu đề để mở toàn văn đã làm sạch.

Màu lấy từ `vinuni_logo.svg`: xanh `#134d8b`, đỏ `#c72127`. Giao diện sáng.

## Chạy

Cần **hai** tiến trình. Từ thư mục gốc repo:

```bash
EMBEDDING_PROVIDER=local .venv/bin/python -m uvicorn api.server:app --port 8010
```

Backend tự nạp sẵn model + index lúc khởi động (~15 giây) để câu hỏi đầu tiên
không phải chờ. Xem `GET /api/health` — `"warm": true` là xong.

```bash
npm --prefix web run dev
```

Mở http://localhost:3000. Cổng backend cấu hình ở `web/.env.local` (`BACKEND_URL`);
Next.js proxy `/api/*` sang đó nên không vướng CORS.

## Ghi chú

- **Câu trả lời sinh bằng OpenAI** (`gpt-4.1-mini`, streaming từng token). Mỗi lượt
  hỏi gửi câu hỏi + `top_k` chunk ngữ cảnh lên OpenAI và **tính phí vào
  `OPENAI_API_KEY` trong `.env`**. Prompt do chính `KnowledgeBaseAgent` dựng —
  backend chỉ bắt lại prompt đó để stream, không viết lại logic.
  - Đổi model: `OPENAI_CHAT_MODEL=gpt-4o-mini`
  - Tắt hẳn, quay về stub trích xuất offline: `DEMO_LLM=stub`
  - Nếu gọi OpenAI lỗi, backend tự lùi về stub và hiện một bước lỗi trong trace —
    demo không chết giữa chừng.
- `EMBEDDING_PROVIDER` nhận `local` | `openai` | `mock`. Dùng `local` cho khớp số
  liệu trong báo cáo. Bỏ trống sẽ rơi về `MockEmbedder` (băm MD5) — điểm tương đồng
  chỉ là nhiễu.
- Chọn `FixedSize (500/50)` sẽ thấy vài chunk mở đầu bằng chữ cụt ("ết bảo hành là
  bao lâu?") — đặc tính thật của chunker cắt theo ký tự, không phải lỗi hiển thị.
  Đây là điểm hay để nói khi demo: LLM vẫn trả lời đúng vì nó đọc cả 3 chunk.

## Lưu ý khi phát triển

Đừng chạy `next build` trong lúc `next dev` đang chạy — hai lệnh dùng chung thư mục
`.next/` và sẽ phá manifest của nhau (triệu chứng: trang render ra nhưng bấm nút
không ăn vì client bundle không hydrate). Nếu lỡ: dừng dev server, `rm -rf web/.next`,
chạy lại.
