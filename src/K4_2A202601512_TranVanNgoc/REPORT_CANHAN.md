# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Văn Ngọc — 2A202601512  
**Nhóm:** SPIDERMAN  
**Ngày:** 03-08-2026

> Phần nhóm (corpus, metadata schema, 5 benchmark query và gold answer) xem `report/REPORT_NHOM.md`.

## 1. Khởi động (Warm-up) — Cá nhân

### Độ tương tự Cosine

**Cosine cao nghĩa là gì?**  Hai embedding có hướng gần nhau trong không gian vector, nên model xem nội dung của chúng gần nghĩa. Điểm này đo mức tương đồng ngữ nghĩa hơn là số từ giống hệt nhau.

**Ví dụ cao:**

- Câu A: “Nhà Bán phải xác nhận yêu cầu đổi trả trong 02 ngày làm việc.”
- Câu B: “Người bán có 48 giờ để phản hồi đề nghị trả hàng của khách.”
- Lý do: cùng nói về nghĩa vụ phản hồi đổi trả của người bán, dù cách diễn đạt và đơn vị thời gian khác nhau.

**Ví dụ thấp:**

- Câu A: “Chính sách đổi trả hàng hóa trên sàn thương mại điện tử.”
- Câu B: “Công thức nấu phở bò Hà Nội truyền thống.”
- Lý do: khác miền chủ đề và không thể dùng câu này để trả lời câu kia.

Cosine phù hợp cho text embedding vì đo góc giữa hai vector, ít bị ảnh hưởng bởi độ dài đoạn văn. Euclidean distance còn bị ảnh hưởng bởi độ lớn vector; điều này dễ làm chunk dài và câu hỏi ngắn bị coi là xa dù cùng nội dung.

### Bài toán Chunking

Với `chunk_size=500`, `overlap=50`, mỗi chunk mới tiến `500 - 50 = 450` ký tự:

`ceil((10000 - 50) / 450) = ceil(22.11) = 23` chunks.

Nếu `overlap=100`, bước tiến còn 400 ký tự:

`ceil((10000 - 100) / 400) = ceil(24.75) = 25` chunks.

Overlap lớn tạo nhiều vector hơn, nhưng giúp một câu nằm gần ranh giới xuất hiện trọn vẹn trong ít nhất một chunk.

## 2. Hướng tiếp cận của tôi

### Chunking

**`SentenceChunker.chunk`:** Duyệt từng ký tự và coi `. `, `.\n`, `! `, `? ` là điểm kết thúc câu. Mỗi câu được `strip()`, sau đó ghép tối đa `max_sentences_per_chunk` câu; text rỗng trả về `[]`. Cách này đơn giản, phù hợp văn bản chính sách, nhưng có thể hiểu nhầm dấu chấm trong chữ viết tắt hoặc số thứ tự.

**`RecursiveChunker.chunk` / `_split`:** Tôi dùng thứ tự separator đoạn `\n\n` → dòng `\n` → câu `. ` → từ → cắt cứng. Hàm gộp các phần liên tiếp tới ngưỡng `chunk_size`; phần nào vẫn quá dài sẽ gọi đệ quy với separator ưu tiên thấp hơn. Base case là text đã đủ ngắn, hoặc hết separator/đến separator rỗng thì cắt theo độ dài cố định, nên không có đệ quy vô hạn.

**Chiến lược benchmark cá nhân:** `RecursiveChunker(chunk_size=400)`. Đây là cấu hình duy nhất tôi thay đổi khi so sánh; corpus, 5 query, metadata filter và embedder phải giữ giống các thành viên khác.

### EmbeddingStore

**`add_documents` + `search`:** Mỗi `Document` được chuyển thành record có `id`, `content`, `metadata`, `embedding`; embedding được tạo ngay khi nạp. Khi không dùng ChromaDB, `search` embed query, tính dot product với từng embedding và chọn `top_k` lớn nhất bằng `nlargest`. Nếu ChromaDB sẵn sàng, store gọi API `add`/`query` của collection và đổi dấu distance để score lớn hơn nghĩa là gần hơn.

**`search_with_filter` + `delete_document`:** Với in-memory, metadata được lọc trước bằng điều kiện tất cả key/value đều khớp, rồi mới tính score; như vậy chunk sai vai trò không chiếm chỗ trong top-3. `delete_document` dựng lại list, bỏ record có `metadata['doc_id']` đúng bằng `doc_id`, rồi so sánh kích thước trước/sau để trả về `True` hoặc `False`.

### KnowledgeBaseAgent

`answer()` lấy top-3 chunk, đánh số từng đoạn cùng `doc_id`, sau đó ghép chúng vào prompt. Prompt yêu cầu chỉ trả lời từ context và nói rõ khi context không đủ; cuối cùng gọi `llm_fn` để sinh câu trả lời. Nếu store trống hoặc không có kết quả, agent trả thông báo tiếng Việt thay vì gọi LLM.

## 3. Hoàn thiện code

Lệnh đã chạy:

```text
python -m unittest tests.test_solution
..........................................
----------------------------------------------------------------------
Ran 42 tests in 0.009s

OK
```

**Số lượng bài test vượt qua:** **42 / 42**.

## 4. Dự đoán độ tương tự

Các số dưới đây đo bằng backend thực tế hiện tại: `mock embeddings fallback`. Dự đoán “cao/thấp” là dự đoán theo nghĩa của câu trước khi đo.

| Cặp | Câu A / Câu B (rút gọn) | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---:|---|
| 1 | Xác nhận đổi trả 02 ngày / phản hồi trả hàng 48 giờ | cao | -0.1529 | Không |
| 2 | Bảo hành tối đa 30 ngày / bảo hành một tháng | cao | 0.0971 | Không |
| 3 | Chính sách đổi trả TMĐT / công thức phở bò | thấp | -0.1321 | Có |
| 4 | Cấm bán thuốc lá, xì gà / danh mục hàng cấm | cao | -0.0157 | Không |
| 5 | Quyền khiếu nại của NTD / nghĩa vụ nộp thuế | thấp | -0.0446 | Có |

Điều bất ngờ là ba cặp cùng nghĩa đều không cho điểm cao. Nguyên nhân là `MockEmbedder` băm nội dung để tạo vector quyết định được, không học ngữ nghĩa; vì vậy nó chỉ phù hợp unit test, không phù hợp kết luận chất lượng retrieval. Khi nhóm thống nhất chạy `EMBEDDING_PROVIDER=local`, cần đo lại bảng này.

## 5. Kết quả truy xuất của tôi

**Cấu hình chạy:** corpus `data/k4_ecommerce` (10 tài liệu) → `build_knowledge_base()` → `RecursiveChunker(chunk_size=400)` → **356 chunks**. Backend thực chạy là **mock embeddings fallback**. Q1/Q3 lọc `seller`, Q4 lọc `buyer`; Q2/Q5 không lọc.

| # | Query | Document gold | Top-1 thực tế | Score | Gold trong top-3? |
|---|---|---|---|---:|---|
| 1 | Thời gian xác nhận đổi/trả/bảo hành | `tiki-xu-ly-doi-tra-bao-hanh` | `moit-trach-nhiem-ban-le-hang-tieu-dung` | 0.236 | Không |
| 2 | Thời gian bảo hành tối đa | `tiki-xu-ly-doi-tra-bao-hanh` | `bvntd-kiem-soat-chat-luong-hang-hoa-tmdt` | 0.369 | Không |
| 3 | Hàng hóa cấm đăng bán trên Tiki | `tiki-danh-muc-hang-cam-ban` | `moit-trach-nhiem-ban-le-hang-tieu-dung` | 0.289 | Không |
| 4 | Phòng tránh rủi ro mua sắm trực tuyến | `bvntd-rui-ro-mua-sam-truc-tuyen` | `moit-quy-dinh-moi-luat-bvqltd-2023` | 0.257 | Không |
| 5 | Trách nhiệm sàn theo NĐ 85/2021 | `moit-nghi-dinh-85-2021-tmdt` | `bvntd-kiem-soat-chat-luong-hang-hoa-tmdt` | 0.381 | Không |

**Số câu có chunk gold trong top-3:** **0 / 5** với mock embedding. Đây là kết quả sơ bộ kỹ thuật, không dùng để kết luận strategy Recursive kém hơn strategy khác: embedding hiện tại không biểu diễn ngữ nghĩa. Cần chạy lại đúng 5 query bằng embedder mà benchmark owner chốt (ví dụ local) trước khi ghi điểm retrieval cuối cùng.

`bench.py` hiện in retrieval nên chưa gọi agent để sinh câu trả lời. Khi cần cột agent answer, dùng cùng top-3 retrieval làm context cho `KnowledgeBaseAgent`; không đánh giá chất lượng LLM từ lần chạy mock này.

**Điều học được:** Cần đánh giá ở mức chunk chứa gold answer, không chỉ nhìn top-1 có cùng document hay không. Metadata filter vẫn hoạt động về mặt phạm vi (Q1/Q3 chỉ xét seller, Q4 chỉ xét buyer), nhưng filter không thể bù cho embedding không mang ngữ nghĩa.

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 9 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 4 / 5 |
| Kết quả truy xuất | Chờ chạy lại bằng embedder chung |
| **Tổng phần cá nhân** | **Chưa chốt** |
