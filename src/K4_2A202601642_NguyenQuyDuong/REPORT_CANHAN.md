# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Quý Dương - 2A202601642
**Nhóm:** SPIDERMAN
**Ngày:** 03-08-2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương đồng cosine cao nghĩa là 2 vector có thể biểu diễn gần nhau và cùng chỉ về một hướng trong embedding space. Về mặt ngữ nghĩa, 2 câu của 2 vector trên có thể đều chứa nghĩa gần hoặc giống nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: “Nhà Bán phải xác nhận yêu cầu đổi trả trong 02 ngày làm việc.”
- Câu B: “Người bán có 48 giờ để phản hồi đề nghị trả hàng của khách.”
- Tại sao tương đồng: gần như không chung từ nào ("Nhà Bán"/"người bán", "02 ngày làm việc"/"48 giờ", "đổi trả"/"trả hàng"), nhưng cùng mô tả một nghĩa vụ — chủ thể người bán, hành động phản hồi, một hạn chót ngắn. Embedding tốt phải nhận ra chúng thay thế được cho nhau. **Đo thực tế: +0.6293.**

**Ví dụ có độ tương tự THẤP:**
- Câu A: “Chính sách đổi trả hàng hóa trên sàn thương mại điện tử.”
- Câu B: “Công thức nấu phở bò Hà Nội truyền thống.”
- Tại sao khác: khác hoàn toàn về chủ đề, chủ thể lẫn mục đích; không có ngữ cảnh nào khiến câu này trả lời được cho câu kia. **Đo thực tế: +0.0978.**

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine phù hợp cho text embedding vì đo góc giữa hai vector, ít bị ảnh hưởng bởi độ dài đoạn văn. Euclidean distance còn bị ảnh hưởng bởi độ lớn vector; điều này dễ làm chunk dài và câu hỏi ngắn bị coi là xa dù cùng nội dung.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* khoảng cách giữa index đánh dấu vị trí của chunk mới và chunk cũ là `step = chunk_size − overlap = 500 − 50 = 450`. Chunk đầu chiếm 500 char, mỗi chunk sau nhảy thêm 450 char.

> *Đáp án:* `round((10000-50)/450) = round(22.11) = 23` chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* `round((10000-100)/400) = round(24.75) = 25` chunks.
Overlap lớn hơn giúp câu trả lời bị cắt ở biên vẫn xuất hiện trong ít nhất một chunk, nhưng làm tăng số vector và nội dung trùng lặp.
---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`:** Duyệt từng ký tự và coi `. `, `.\n`, `! `, `? ` là điểm kết thúc câu. Mỗi câu được `strip()`, sau đó ghép tối đa `max_sentences_per_chunk` câu; text rỗng trả về `[]`. Cách này đơn giản, phù hợp văn bản chính sách, nhưng có thể hiểu nhầm dấu chấm trong chữ viết tắt hoặc số thứ tự.

**`RecursiveChunker.chunk` / `_split`:** Tôi dùng thứ tự separator đoạn `\n\n` → dòng `\n` → câu `. ` → từ → cắt cứng. Hàm gộp các phần liên tiếp tới ngưỡng `chunk_size`; phần nào vẫn quá dài sẽ gọi đệ quy với separator ưu tiên thấp hơn. Base case là text đã đủ ngắn, hoặc hết separator/đến separator rỗng thì cắt theo độ dài cố định, nên không có đệ quy vô hạn.

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
=========================================================================================================== test session starts ============================================================================================================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- D:\Workspaces\AI_in_action\K4_Day07_SPIDERMAN_DataFoundation\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Workspaces\AI_in_action\K4_Day07_SPIDERMAN_DataFoundation
plugins: anyio-4.14.2
collected 42 items                                                                                                                                                                                                                          

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                                                                                                 [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                                                                                          [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                                                                                                   [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                                                                                                    [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                                                                                                         [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                                                                                                         [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                                                                                               [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                                                                                                [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                                                                                              [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                                                                                                [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                                                                                                [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                                                                                           [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                                                                                                       [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                                                                                                 [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                                                                                                        [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                                                                                            [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                                                                                                      [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                                                                                            [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                                                                                                [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                                                                                                  [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                                                                                                    [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                                                                                          [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                                                                                               [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                                                                                                 [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                                                                                                     [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                                                                                                  [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                                                                                           [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                                                                                          [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                                                                                                     [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                                                                                                 [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                                                                                            [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                                                                                                [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                                                                                                      [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                                                                                                [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                                                                                             [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                                                                                           [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                                                                                          [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                                                                                              [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                                                                                                         [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                                                                                                  [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                                                                                                        [ 97%]*Viết
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                                                                                            [100%]

============================================================================================================ 42 passed in 0.24s ============================================================================================================
```

**Số lượng bài test vượt qua (pass):** __ / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý đổi – trả – bảo hành?" | "Nhà Bán cần bao lâu để phản hồi yêu cầu đổi/trả của khách hàng?" | cao | 0.830 | ✅ |
| 2 | "Thời gian bảo hành tối đa không quá 30 ngày, tính từ khi Nhà Bán nhận được hàng." | "Bảo hành không vượt quá 30 ngày kể từ ngày Nhà Bán nhận sản phẩm." | cao | 0.812 | ✅ |
| 3 | "Người tiêu dùng nên tìm hiểu kỹ điều kiện bảo hành, đổi trả trước khi mua hàng trực tuyến." | "Python là ngôn ngữ lập trình bậc cao, dễ đọc và có cú pháp gọn." | thấp | 0.058 | ✅ |
| 4 | "Người tiêu dùng có quyền yêu cầu đổi trả hàng hóa bị lỗi trong thời hạn quy định." | "Nhà Bán có nghĩa vụ xử lý yêu cầu đổi trả của khách hàng trong 02 ngày làm việc." | cao | 0.396 | ❌ |
| 5 | "Danh mục hàng hóa cấm bán trên sàn Tiki gồm vũ khí, chất nổ, ma túy và hàng giả." | "Prompt hệ thống cho LLM cần nêu rõ vai trò và giới hạn hành động của agent." | thấp | 0.181 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 là bất ngờ nhất: cả hai câu đều nói về "đổi trả hàng hóa" và dùng chung nhiều từ khóa, nhưng điểm cosine chỉ 0.396 — thấp hơn hẳn cặp 1/2 (cùng chủ đề, cùng vai "Nhà Bán"). Khác biệt nằm ở **vai và hướng hành động**: câu A là quyền của người tiêu dùng, câu B là nghĩa vụ của Nhà Bán kèm mốc thời hạn cụ thể. Điều này cho thấy embedding không chỉ khớp từ khóa bề mặt mà còn nhạy với chủ thể/quan hệ ngữ nghĩa trong câu — đây cũng chính là lý do tại sao lọc theo `customer_role` vẫn cần thiết dù hai tài liệu buyer/seller dùng từ vựng trùng nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời gian xác nhận đổi/trả/bảo hành (filter `seller`) | `tiki-xu-ly-doi-tra-bao-hanh` — mục 8, "02 ngày làm việc..." | 0.796 | ✅ Có, evidence "02 ngày làm việc" đúng ở top-1 | Trích đúng mục 8, nêu đúng "02 ngày làm việc" |
| 2 | Thời hạn bảo hành tối đa Nhà Bán (không filter) | `bvntd-kiem-soat-chat-luong-hang-hoa-tmdt` — nói về trách nhiệm Sàn, không có "30 ngày" | 0.789 | ⚠️ Chunk đúng chứa "30 ngày" tồn tại nhưng chỉ đứng **top-2** (score 0.769), không phải top-1 | Lệch — quote nhầm sang mốc "15 ngày, 7 ngày" của Sàn thay vì "30 ngày" của Nhà Bán |
| 3 | Hàng cấm bán trên Tiki (filter `seller`) | `tiki-danh-muc-hang-cam-ban` — "Tiki không hỗ trợ bán hàng cũ, đã qua sử dụng..." | 0.782 | ✅ Có, evidence đúng ở top-1 | Trích đúng danh mục hàng cấm + hàng cũ/second-hand |
| 4 | Phòng tránh rủi ro mua sắm trực tuyến (filter `buyer`) | `bvntd-rui-ro-mua-sam-truc-tuyen` — mục 2 "Khuyến cáo... sàn TMĐT uy tín..." | 0.859 | ✅ Có, evidence đúng ở top-1 | Trích đúng khuyến cáo (a) mua tại sàn uy tín |
| 5 | Trách nhiệm sàn TMĐT theo NĐ 85/2021 (không filter) | `moit-nghi-dinh-85-2021-tmdt` — "Thứ năm, về trách nhiệm giải quyết khiếu nại..." | 0.803 | ⚠️ Đúng tài liệu, nhưng câu chứa "nhiều hơn 02 bên" chỉ ở **top-3** | Agent chỉ trích câu mở đầu mục, thiếu đúng nội dung "02 bên" nằm ở chunk thứ 3 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 — nhưng chỉ **3/5** có evidence đúng ở **top-1** (Q1, Q3, Q4); Q2 và Q5 có evidence trong top-3 song không phải top-1 nên agent (chỉ đọc top-1 làm câu trả lời trực tiếp trong bản demo extractive) trả lời thiếu/lệch. Đây đúng là điểm khác biệt quan trọng giữa "đúng doc_id trong top-3" và "đúng nội dung ở top-1" mà rubric yêu cầu phân biệt.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 28 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **55 / 60** |
