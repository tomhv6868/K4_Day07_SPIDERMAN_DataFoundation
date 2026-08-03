
# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Hoàng Bảo Minh
**Nhóm:** Spiderman
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding trỏ theo hướng gần giống nhau trong không gian nhiều chiều (giá trị gần 1), nghĩa là hai đoạn văn bản mang ý nghĩa/chủ đề gần nhau theo cách mô hình embedding "hiểu", bất kể chúng có dùng chung từ ngữ hay không.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý đổi – trả – bảo hành?"
- Câu B: "Nhà Bán cần bao lâu để phản hồi yêu cầu đổi/trả của khách hàng?"
- Tại sao tương đồng: cùng hỏi về mốc thời hạn xử lý yêu cầu đổi/trả/bảo hành, chỉ khác cách diễn đạt.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Người tiêu dùng nên làm gì để phòng tránh rủi ro khi mua sắm trực tuyến?"
- Câu B: "Python là ngôn ngữ lập trình bậc cao, dễ đọc và có cú pháp gọn."
- Tại sao khác: chủ đề hoàn toàn khác nhau (bảo vệ người tiêu dùng vs. ngôn ngữ lập trình), không chia sẻ khái niệm hay vốn từ chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ quan tâm hướng của vector, không quan tâm độ dài (magnitude) — nên không bị lệch khi văn bản dài/ngắn khác nhau khiến vector có norm lớn/nhỏ khác nhau; Euclidean distance thì nhạy với magnitude này nên dễ đánh giá sai mức độ tương đồng ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `step = chunk_size - overlap = 500 - 50 = 450`. Chunk đầu bắt đầu tại vị trí 0; lặp `start += step` cho đến khi `start + chunk_size >= 10000`. Số vòng lặp: `ceil((10000 - 500) / 450) + 1 = ceil(9500/450) + 1 = 22 + 1 = 23`.
> *Đáp án:* **23 chunks** (đã kiểm chứng lại bằng cách chạy trực tiếp `FixedSizeChunker(500, 50).chunk(...)` trên văn bản 10,000 ký tự).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Overlap tăng lên 100 → `step = 400` → số chunk tăng thành **25 chunks** (nhiều hơn vì mỗi bước tiến ngắn hơn). Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa hai chunk liên tiếp — tránh trường hợp một câu/ý quan trọng bị cắt đứt giữa dòng và không chunk nào chứa được trọn vẹn thông tin đó, đổi lại là tốn thêm dung lượng lưu trữ do nội dung trùng lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Không dùng regex mà quét từng ký tự thủ công: khi gặp `.`/`!`/`?` và ký tự theo sau là dấu cách hoặc xuống dòng thì coi đó là ranh giới cuối câu, cắt câu tại đó. Các câu được nhóm lại theo `max_sentences_per_chunk`. Edge case đã xử lý: văn bản không có dấu kết câu nào (trả về `[text.strip()]` nếu còn nội dung, `[]` nếu rỗng) và phần "tail" còn dư sau vòng quét cuối cùng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thử tách văn bản theo danh sách separator ưu tiên giảm dần (`\n\n` → `\n` → `. ` → `" "` → `""`); nếu một phần sau khi tách vẫn còn dài hơn `chunk_size`, gọi đệ quy `_split` với separator kế tiếp cho riêng phần đó. Base case: đoạn hiện tại đã ngắn hơn `chunk_size` (trả nguyên đoạn) hoặc hết separator để dùng (buộc cắt cứng theo `chunk_size`). Các phần nhỏ được gộp dần lại (`current_parts`) miễn còn dưới ngưỡng kích thước, giúp chunk bám gần biên đoạn văn/câu tự nhiên hơn fixed-size.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` gọi `embedding_fn` cho từng `Document`, gắn `doc_id` vào metadata rồi lưu bản ghi (`id`, `content`, `metadata`, `embedding`) — dùng ChromaDB nếu import được, ngược lại append vào list `self._store`. `search` embed câu hỏi rồi tính độ tương tự bằng `_dot` (dot product) giữa vector câu hỏi và mọi embedding đã lưu; vì các embedder đều chuẩn hoá vector về norm 1 nên dot product ở đây tương đương cosine similarity. Dùng `heapq.nlargest` để lấy top-k mà không cần sort toàn bộ danh sách.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước** khi tính similarity: `search_with_filter` duyệt `self._store`, giữ lại các record khớp mọi cặp key-value trong `metadata_filter`, rồi mới chạy `_search_records` (cùng logic dot-product top-k) trên tập đã lọc — cách này tránh so sánh similarity với các chunk chắc chắn không thuộc phạm vi cần tìm. `delete_document` xoá theo `doc_id` bằng cách rebuild `self._store` chỉ giữ record có `metadata["doc_id"] != doc_id` (hoặc gọi `collection.delete(ids=...)` nếu dùng Chroma).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Nếu store trống hoặc không có kết quả, trả thông báo tiếng Việt rõ ràng ngay, không gọi LLM. Ngược lại, lấy top-k chunk (qua `search` hoặc `search_with_filter` nếu có `metadata_filter`), đánh số `[1]`, `[2]`... kèm `(source: doc_id)` để truy vết, rồi ghép vào prompt theo thứ tự cố định: Instruction (chỉ dùng context, nói rõ khi context không đủ, trả lời bằng tiếng Việt) → Context → Question → nhãn `Answer:`. Prompt hoàn chỉnh được truyền cho `llm_fn` — agent không tự sinh câu trả lời, chỉ chịu trách nhiệm dựng đúng ngữ cảnh có căn cứ (grounding).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ .venv/bin/python -m pytest tests/ -v
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================== 42 passed in 0.07s ===============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý đổi – trả – bảo hành?" | "Nhà Bán cần bao lâu để phản hồi yêu cầu đổi/trả của khách hàng?" | cao | 0.830 | ✅ |
| 2 | "Thời gian bảo hành tối đa không quá 30 ngày, tính từ khi Nhà Bán nhận được hàng." | "Bảo hành không vượt quá 30 ngày kể từ ngày Nhà Bán nhận sản phẩm." | cao | 0.812 | ✅ |
| 3 | "Người tiêu dùng nên tìm hiểu kỹ điều kiện bảo hành, đổi trả trước khi mua hàng trực tuyến." | "Python là ngôn ngữ lập trình bậc cao, dễ đọc và có cú pháp gọn." | thấp | 0.058 | ✅ |
| 4 | "Người tiêu dùng có quyền yêu cầu đổi trả hàng hóa bị lỗi trong thời hạn quy định." | "Nhà Bán có nghĩa vụ xử lý yêu cầu đổi trả của khách hàng trong 02 ngày làm việc." | cao | 0.396 | ❌ |
| 5 | "Danh mục hàng hóa cấm bán trên sàn Tiki gồm vũ khí, chất nổ, ma túy và hàng giả." | "Prompt hệ thống cho LLM cần nêu rõ vai trò và giới hạn hành động của agent." | thấp | 0.181 | ✅ |

*(Đo bằng `LocalEmbedder` — `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, `EMBEDDING_PROVIDER=local`.)*

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 là bất ngờ nhất: cả hai câu đều nói về "đổi trả hàng hóa" và dùng chung nhiều từ khóa, nhưng điểm cosine chỉ 0.396 — thấp hơn hẳn cặp 1/2 (cùng chủ đề, cùng vai "Nhà Bán"). Khác biệt nằm ở **vai và hướng hành động**: câu A là quyền của người tiêu dùng, câu B là nghĩa vụ của Nhà Bán kèm mốc thời hạn cụ thể. Điều này cho thấy embedding không chỉ khớp từ khóa bề mặt mà còn nhạy với chủ thể/quan hệ ngữ nghĩa trong câu — đây cũng chính là lý do tại sao lọc theo `customer_role` vẫn cần thiết dù hai tài liệu buyer/seller dùng từ vựng trùng nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Chạy bằng `LocalEmbedder` (`EMBEDDING_PROVIDER=local`), strategy **RecursiveChunker(chunk_size=400)**, 356 chunk nạp từ `data/k4_ecommerce`. Cột "Có liên quan" kiểm bằng chuỗi `evidence` khai trong `data/benchmark_queries.py`, không chỉ nhìn `doc_id`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời gian xác nhận đổi/trả/bảo hành (filter `seller`) | `tiki-xu-ly-doi-tra-bao-hanh` — mục 8, "02 ngày làm việc..." | 0.796 | ✅ Có, evidence "02 ngày làm việc" đúng ở top-1 | Trích đúng mục 8, nêu đúng "02 ngày làm việc" |
| 2 | Thời hạn bảo hành tối đa Nhà Bán (không filter) | `bvntd-kiem-soat-chat-luong-hang-hoa-tmdt` — nói về trách nhiệm Sàn, không có "30 ngày" | 0.789 | ⚠️ Chunk đúng chứa "30 ngày" tồn tại nhưng chỉ đứng **top-2** (score 0.769), không phải top-1 | Lệch — quote nhầm sang mốc "15 ngày, 7 ngày" của Sàn thay vì "30 ngày" của Nhà Bán |
| 3 | Hàng cấm bán trên Tiki (filter `seller`) | `tiki-danh-muc-hang-cam-ban` — "Tiki không hỗ trợ bán hàng cũ, đã qua sử dụng..." | 0.782 | ✅ Có, evidence đúng ở top-1 | Trích đúng danh mục hàng cấm + hàng cũ/second-hand |
| 4 | Phòng tránh rủi ro mua sắm trực tuyến (filter `buyer`) | `bvntd-rui-ro-mua-sam-truc-tuyen` — mục 2 "Khuyến cáo... sàn TMĐT uy tín..." | 0.859 | ✅ Có, evidence đúng ở top-1 | Trích đúng khuyến cáo (a) mua tại sàn uy tín |
| 5 | Trách nhiệm sàn TMĐT theo NĐ 85/2021 (không filter) | `moit-nghi-dinh-85-2021-tmdt` — "Thứ năm, về trách nhiệm giải quyết khiếu nại..." | 0.803 | ⚠️ Đúng tài liệu, nhưng câu chứa "nhiều hơn 02 bên" chỉ ở **top-3** | Agent chỉ trích câu mở đầu mục, thiếu đúng nội dung "02 bên" nằm ở chunk thứ 3 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 — nhưng chỉ **3/5** có evidence đúng ở **top-1** (Q1, Q3, Q4); Q2 và Q5 có evidence trong top-3 song không phải top-1 nên agent (chỉ đọc top-1 làm câu trả lời trực tiếp trong bản demo extractive) trả lời thiếu/lệch. Đây đúng là điểm khác biệt quan trọng giữa "đúng doc_id trong top-3" và "đúng nội dung ở top-1" mà rubric yêu cầu phân biệt.

**A/B filter vs. không filter:** với Q1 (filter `seller`), bật filter loại được đối thủ cạnh tranh `bvntd-kiem-soat-chat-luong-hang-hoa-tmdt` khỏi vị trí top-1 — có tác dụng thật. Ngược lại Q3, Q4 cho **cùng kết quả bất kể có filter hay không** vì với embedding ngữ nghĩa thật (local), câu hỏi đã đủ đặc trưng để tự tách đúng tài liệu — filter ở đây là lớp an toàn dự phòng hơn là yếu tố quyết định.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> So với lúc benchmark bằng `MockEmbedder` (toàn bộ 5/5 query "evidence_found=False"), chuyển sang `LocalEmbedder` cải thiện rõ retrieval nhưng vẫn lộ ra thất bại tinh vi hơn: chunk đúng tài liệu có thể đứng top-2/top-3 vì các đoạn trong cùng file bàn cùng chủ đề nên điểm sát nhau — đúng như cảnh báo "chấm ở mức chunk, không chỉ doc_id" của lab. Bài học là recursive chunking theo `chunk_size=400` đôi khi tách câu chứa số liệu quan trọng (VD "30 ngày", "nhiều hơn 02 bên") ra một chunk riêng cạnh chunk giới thiệu chủ đề, khiến nó thua điểm dù nội dung mới là câu trả lời đúng.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |

*Trừ điểm ở mục 5 vì 2/5 query (Q2, Q5) chunk đúng không lọt top-1 nên câu trả lời agent bị lệch — cần cải thiện chunking hoặc top_k để phần trình bày phản ánh đúng hạn chế còn tồn tại, không tính là hoàn hảo.*