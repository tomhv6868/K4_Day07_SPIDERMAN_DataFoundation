# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Công Thành — 2A202601662
**Nhóm:** SPIDERMAN
**Ngày:** 03-08-2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector chỉ về **cùng một hướng** trong không gian embedding, tức mô hình đặt hai đoạn text vào cùng một vùng ngữ nghĩa. Cosine cao nghĩa là "nói về cùng một chuyện", **không** có nghĩa là "dùng cùng từ ngữ", và cũng không có nghĩa hai câu đúng như nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Nhà Bán phải xác nhận yêu cầu đổi trả trong 02 ngày làm việc."
- Câu B: "Người bán có 48 giờ để phản hồi đề nghị trả hàng của khách."
- Tại sao tương đồng: gần như không chung từ nào ("Nhà Bán"/"người bán", "02 ngày làm việc"/"48 giờ", "đổi trả"/"trả hàng"), nhưng cùng mô tả một nghĩa vụ — chủ thể người bán, hành động phản hồi, một hạn chót ngắn. Embedding tốt phải nhận ra chúng thay thế được cho nhau. **Đo thực tế: +0.6293.**

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách đổi trả hàng hóa trên sàn thương mại điện tử."
- Câu B: "Công thức nấu phở bò Hà Nội truyền thống."
- Tại sao khác: khác hoàn toàn về chủ đề, chủ thể lẫn mục đích; không có ngữ cảnh nào khiến câu này trả lời được cho câu kia. **Đo thực tế: +0.0978.**

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo **góc**, đã chuẩn hoá theo độ dài vector, nên một đoạn dài và một câu ngắn cùng nội dung vẫn được coi là giống nhau. Euclid phạt cả chênh lệch **độ lớn** vector — mà độ lớn thường tương quan với độ dài/tần suất từ, nên chunk dài sẽ bị đẩy ra xa query ngắn dù cùng nghĩa. Với corpus K4 có chunk dài lệch nhau rất nhiều (1.181 → 27.968 ký tự) thì khác biệt này rất đáng kể.

**Kiểm lại bằng code — và một cảnh báo quan trọng:** repo mặc định chạy `MockEmbedder`, vốn băm text bằng MD5 rồi sinh số giả ngẫu nhiên, **không hề mã hoá ngữ nghĩa**. Chạy `compute_similarity` trên **đúng 5 cặp câu của mục 4** với hai backend để so trực tiếp:

| Cặp câu | Cosine (mock) | Cosine (local) | Kỳ vọng |
|---|---|---|---|
| "đổi trả" vs "đổi trả" (trùng khít) | **+1.0000** | — | cao ✔ |
| 1. Nhà Bán 02 ngày ↔ người bán 48 giờ (cùng nghĩa) | **−0.0425** | +0.6293 | cao ✘ |
| 2. Bảo hành 30 ngày ↔ bảo hành một tháng (cùng nghĩa) | +0.1073 | +0.4514 | cao ✘ |
| 3. Chính sách đổi trả ↔ công thức nấu phở (khác chủ đề) | **+0.1038** | +0.0978 | thấp ✘ |
| 4. Cấm bán thuốc lá ↔ danh mục hàng cấm (cùng chủ đề) | +0.0088 | +0.5211 | cao ✘ |
| 5. Khiếu nại của NTD ↔ nghĩa vụ thuế (khác chủ đề) | +0.0661 | +0.3657 | thấp ✔ |

Cặp 3 — *đổi trả* với *nấu phở*, không liên quan gì nhau — được mock chấm **+0.1038**, **cao hơn** cặp 1 vốn cùng nghĩa (**−0.0425**). Đây không phải lỗi công thức cosine: `compute_similarity` vẫn đúng (vector trùng → 1, vuông góc → 0, ngược hướng → −1), và cặp trùng khít vẫn ra đúng +1.0000. Nó cho thấy `MockEmbedder` chỉ khớp được chuỗi **giống hệt nhau**; ngoài trường hợp đó, thứ tự nó tạo ra là nhiễu MD5. Cột "local" bên cạnh sắp đúng thứ tự mong đợi ở 4/5 cặp — khác biệt nằm ở backend, không nằm ở công thức. Mọi số ở mục 4 và mục 5 vì vậy đều chạy bằng `EMBEDDING_PROVIDER=local` (`paraphrase-multilingual-MiniLM-L12-v2`), không dùng mock.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Phép tính:* mỗi chunk mới chỉ tiến thêm `step = chunk_size − overlap = 500 − 50 = 450` ký tự. Chunk đầu tiên "tiêu thụ" trọn 500 ký tự, các chunk sau mỗi cái thêm 450.
> `ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> *Đáp án:* **23 chunk.** Đã chạy `len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('x'*10000))` → 23, khớp.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> **Tăng** — `ceil(9900 / 400) = 25` chunk (đã chạy, ra đúng 25). Overlap lớn thì `step` nhỏ, cần nhiều chunk hơn để phủ hết cùng một văn bản. Lý do chấp nhận đánh đổi: overlap giữ cho câu bị cắt ngang vẫn xuất hiện **nguyên vẹn ở ít nhất một chunk**. Với corpus K4 điều này rất thiết thực — một gold answer như *"tối đa không quá 30 ngày, tính từ thời điểm Nhà Bán nhận được hàng"* mà bị cắt đôi giữa hai chunk thì cả hai chunk đều không trả lời được câu hỏi. Cái giá phải trả là nhiều vector hơn (tốn storage, chậm hơn khi search) và nội dung trùng lặp có thể chiếm nhiều slot trong top-k.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+` — lookbehind nên chỗ cắt là **khoảng trắng đứng sau** dấu kết câu, do đó dấu chấm/hỏi/than ở lại cuối câu trước thay vì bị nuốt mất. Cách này phủ luôn cả `". "`, `"! "`, `"? "` và `".\n"` chỉ bằng một pattern. Edge case xử lý: text rỗng trả `[]`; `strip()` từng câu rồi lọc bỏ phần rỗng để khoảng trắng thừa hoặc dấu câu liên tiếp không sinh ra chunk rỗng; gộp câu bằng `range(0, len, limit)` nên nhóm cuối chỉ có 1–2 câu vẫn hợp lệ. Regex này cố tình đơn giản — nó sẽ cắt nhầm ở "TS." hay "1." nhưng với văn bản chính sách thì chấp nhận được.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `chunk()` chỉ lo phần vỏ (text rỗng → `[]`, cuối cùng `strip()` và bỏ chunk rỗng), toàn bộ đệ quy nằm ở `_split(text, separators)`. Thuật toán thử separator theo thứ tự ưu tiên đoạn → dòng → câu → từ → ký tự: gộp các phần liền nhau vào `buffer` chừng nào còn ≤ `chunk_size`, phần nào tự nó vẫn quá dài thì **đệ quy với danh sách separator đã cắt bớt phần đầu** — đây là chỗ đảm bảo tiến về điều kiện dừng, vì mỗi lần gọi lại luôn ngắn hơn về text *hoặc* ít hơn về separator. Có hai base case: (1) `len(text) <= chunk_size` → trả nguyên text; (2) hết separator, hoặc separator là chuỗi rỗng → cắt cứng theo `chunk_size` bằng `_fixed_slices`. Base case (2) là lý do `separators=[]` không làm hàm rơi vào đệ quy vô hạn.

**`HeadingFaqChunker`** (chiến lược cá nhân của tôi, `src/K4_2A202601662_HoangCongThanh/chunking.py`) — hướng tiếp cận:
> Ba chunker baseline đều chia theo **độ dài**; cái này chia theo **đơn vị cấu trúc** của văn bản chính sách. Ranh giới nhận ở đầu dòng bằng `^(?=(?:#{1,6}\s|[IVXLC]{1,5}\.\s|\d{1,2}\.\s))`, tức heading Markdown, mục La Mã và câu hỏi FAQ đánh số — mỗi chunk là một cặp hỏi–đáp hoặc một khoản trọn vẹn.
>
> Hai quyết định thiết kế đáng nói:
> 1. **Gắn ngữ cảnh cha vào đầu mỗi chunk** (`[Tiêu đề tài liệu — Mục La Mã]`). Corpus K4 có nhiều quy định trùng chủ đề nhưng khác phạm vi áp dụng: thời hạn xác nhận của mô hình NGON là 04 giờ còn thời hạn chung là 02 ngày làm việc. Không có tiêu đề mục thì hai chunk này gần như không phân biệt được. Ở câu 1, top-3 của tôi trả về đúng cả hai — `[… — III. MÔ HÌNH DROPSHIP]` ở rank 1 (02 ngày) và `[… — V. MÔ HÌNH NGON]` ở rank 3 (04 giờ) — nên người đọc phân biệt được ngay chúng thuộc mô hình nào. Baseline `FixedSizeChunker` cũng lấy đúng chunk ở câu này, nhưng chunk của nó không mang nhãn mục nào cả.
> 2. **Có tầng dự phòng.** Khoản nào vượt `max_chunk_size=900` được đẩy qua `RecursiveChunker`. Nếu thiếu, các bài trên moit.gov.vn (gần như không đánh số) sẽ trả về một chunk khổng lồ.
>
> **Tuning đã làm, và nó thay đổi kết quả:** bản đầu tôi cắt cả ở ý chữ cái `a) b) c)` — 183 chunk, chạy benchmark ra **6/10**. Nguyên nhân nhìn thấy được ở câu 4: danh sách khuyến cáo bị xé thành từng mẩu ngắn rời khỏi tiêu đề mục, gold answer **rớt hẳn khỏi top-3**. Bỏ ranh giới `a)` (sub-point là bộ phận của khoản cha, không đứng riêng được) → 166 chunk, lên **8/10** và câu 4 về lại rank 1. Tôi cũng quét tham số quanh điểm chốt: `min_chunk_size` ở 120 / 250 / 400 đều cho 8/10, `max_chunk_size` ở 600 cho 8/10 còn 1200 tụt xuống 7/10 (câu 5 rớt khỏi top-3 vì khoản bị gộp quá to). Nói cách khác 900/120 nằm giữa một vùng phẳng chứ không phải một đỉnh nhọn — tôi giữ 120 để chỉ có đúng một thay đổi so với bản đầu.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu in-memory: mỗi `Document` thành một dict `{id, content, metadata, embedding}` qua helper `_make_record`, **embed ngay lúc nạp** để `search` không phải tính lại. Tách riêng `_search_records(query, records, top_k)` để `search` và `search_with_filter` dùng chung một đường chấm điểm — chỉ khác nhau ở tập record đưa vào. Độ tương tự dùng `compute_similarity` (cosine) chứ không dùng thẳng `_dot`: `MockEmbedder` có chuẩn hoá vector nên hai cách cho kết quả như nhau, nhưng nếu đổi sang backend không chuẩn hoá thì dot product sẽ thiên vị chunk dài. `sort` của Python ổn định nên điểm bằng nhau vẫn giữ thứ tự nạp — kết quả tái lập được giữa các lần chạy.
>
**ChromaDB persistence (bonus task — đã làm)** — hướng tiếp cận:
> Scaffolding gợi ý bật Chroma theo kiểu "cứ `import chromadb` được là dùng". Tôi **không** làm vậy: collection của Chroma sống dai qua nhiều lần chạy, mà bộ test lại tái dùng tên collection — máy nào có cài `chromadb` sẽ thấy dữ liệu của lần chạy trước và fail, còn máy không cài thì pass. Điều kiện bật là **biến môi trường `CHROMA_PERSIST_DIR` do người dùng chủ động đặt**; không đặt thì chạy in-memory. Nhờ vậy một dòng `export` là đổi backend, mà mặc định vẫn tái lập được.
>
> Ba chỗ phải xử lý để hai nhánh cho **cùng một kết quả**, không chỉ "chạy được":
> 1. **Thang điểm.** Chroma mặc định đo khoảng cách L2, trong khi nhánh in-memory chấm bằng cosine. Tôi ép `metadata={"hnsw:space": "cosine"}` lúc tạo collection rồi quy đổi `score = 1.0 − distance`. Scaffolding để `score = −distance`, tức là điểm luôn âm và không cùng thang với `compute_similarity` — hai backend sẽ không so sánh được với nhau.
> 2. **Kiểu metadata.** `retrieved_at: 2026-08-03` trong front matter được PyYAML parse thành `datetime.date`, Chroma từ chối. `_chroma_safe` ép các kiểu không vô hướng về `str`, và **chỉ ép ở nhánh Chroma** để bản in-memory giữ nguyên giá trị gốc.
> 3. **Nạp lại.** Dùng `upsert` chứ không `add`: collection đã persist nên chạy `ingest` lần hai sẽ gặp lại đúng các id cũ; `add` báo lỗi trùng id, `upsert` ghi đè.
>
> **Đã kiểm chứng bằng hai tiến trình tách rời** (xem mục 3): tiến trình 1 nạp 166 chunk rồi thoát, tiến trình 2 mở lại thư mục và search được ngay mà không nạp lại gì.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc trước, chấm điểm sau.** Đây là điểm mấu chốt: nếu chấm điểm cả corpus rồi mới lọc thì chunk bị loại vẫn chiếm slot trong top-k, và một query lọc `seller` có thể trả về ít hơn 3 kết quả dù corpus còn thừa chunk `seller`. Lọc bằng `all(record["metadata"].get(k) == v ...)` nên `metadata_filter` nhiều khoá là phép AND; `metadata_filter` rỗng/`None` đi thẳng vào `self._store`, khớp đúng test `test_no_filter_returns_all_candidates`.
>
> Nhánh Chroma đẩy việc lọc xuống `where` của engine — vẫn là lọc trước khi chấm điểm, chỉ khác là chạy dưới engine thay vì trong Python. Có một cái bẫy: Chroma từ chối dict phẳng nhiều hơn một khoá, nên `_chroma_where` bọc lại thành `{"$and": [...]}`; thiếu bước này thì filter hai khoá (`customer_role` + `language`) sẽ lỗi trong khi bản in-memory vẫn chạy — hai nhánh lệch hành vi.
>
> `delete_document` xoá bằng cách dựng lại list không chứa record khớp, rồi so độ dài trước/sau để quyết định trả `True`/`False`. Điều kiện khớp có 3 nhánh vì `Document` vào store bằng hai đường khác nhau: nạp thẳng thì `metadata` rỗng và `id` chính là `doc_id`; nạp qua `ingest.py` thì `metadata["doc_id"]` có sẵn còn `id` là `"<doc_id>::chunk_<n>"`. Chỉ so `metadata["doc_id"]` như docstring gợi ý sẽ fail test xoá. Ở nhánh Chroma tôi **không** dùng `where={"doc_id": ...}` mà `get()` toàn bộ rồi lọc bằng chính hàm `_belongs_to_document` đó — Chroma không so prefix trên id được, dùng `where` sẽ bỏ sót nhánh khớp theo id. Collection của lab cỡ vài trăm chunk nên quét toàn bộ vẫn rẻ.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Truy xuất top-k → dựng prompt → gọi `llm_fn`, tách phần dựng prompt ra `_build_prompt` để test và đọc lại dễ. Ngữ cảnh được **đánh số `[1] [2] [3]` kèm nhãn nguồn** (`doc_id` + `customer_role`) ngay trên mỗi đoạn, và prompt yêu cầu trả lời có trích số hiệu — nhờ vậy câu trả lời truy ngược được về tài liệu gốc, đúng yêu cầu provenance của K4. Prompt ràng buộc hai điều: chỉ dùng thông tin trong ngữ cảnh, và nói rõ "tài liệu không đề cập" thay vì suy đoán — đây là hàng rào chống bịa (hallucination) khi retrieval trượt. Tôi thêm tham số `metadata_filter` để agent gọi thẳng `search_with_filter`, vì 3/5 query của nhóm cần lọc theo `customer_role`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

**CHECKPOINT 3 — phần chunking + similarity (mục 4 của lab):**

```
$ pytest tests -k "Chunker or Similarity or Compare" -v
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist          PASSED
tests/test_solution.py::TestFixedSizeChunker            (7 test)                      PASSED
tests/test_solution.py::TestSentenceChunker             (4 test)                      PASSED
tests/test_solution.py::TestRecursiveChunker            (4 test)                      PASSED
tests/test_solution.py::TestComputeSimilarity           (4 test)                      PASSED
tests/test_solution.py::TestCompareChunkingStrategies   (3 test)                      PASSED
====================== 23 passed, 19 deselected in 0.02s =======================
```

**Toàn bộ bộ test, chạy trên gói cá nhân của tôi** (`LAB_SOLUTION_PACKAGE` là biến bộ test dùng để chọn gói lời giải — mặc định là `src`):

```
$ LAB_SOLUTION_PACKAGE=src.K4_2A202601662_HoangCongThanh pytest tests/ -q
..........................................                               [100%]
42 passed in 0.02s
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

**Kiểm chứng ChromaDB persistence — hai tiến trình tách rời.** Bộ test 42 bài chỉ phủ nhánh in-memory, nên nhánh Chroma tôi kiểm bằng một kịch bản riêng: tiến trình 1 nạp corpus rồi **thoát hẳn**, tiến trình 2 khởi động mới và chỉ đọc:

```
$ export CHROMA_PERSIST_DIR=./chroma_data/check
$ python chroma_check.py write
[write] use_chroma=True
[write] đã nạp 166 chunk
$ python chroma_check.py read          # tiến trình mới, không nạp lại gì
[read] use_chroma=True
[read] collection còn 166 chunk (không nạp lại gì)
[read] search_with_filter (2 khoá) -> 3 kết quả
   score=0.2405 role=seller id=tiki-danh-muc-hang-cam-ban::chunk_0
   score=0.2360 role=seller id=tiki-xu-ly-doi-tra-bao-hanh::chunk_26
   score=0.2079 role=seller id=moit-trach-nhiem-ban-le-hang-tieu-dung::chunk_1
[read] delete_document -> True, size 166 -> 161
[read] delete lần hai -> False (kỳ vọng False)
```

Bốn thứ được xác nhận cùng lúc: dữ liệu **sống qua ranh giới tiến trình**; filter hai khoá (`customer_role` + `language`) đi qua `$and` không rò kết quả sai vai; `score` nằm đúng thang cosine `[−1, 1]` chứ không phải khoảng cách âm; `delete_document` xoá được và **idempotent** (gọi lần hai trả `False`). Điểm số ở đây thấp vì kịch bản này chạy `MockEmbedder` cho nhanh — nó kiểm luồng lưu trữ, không kiểm chất lượng ngữ nghĩa.

Phủ đủ cả 5 nhóm: `FixedSizeChunker` (7), `SentenceChunker` (4), `RecursiveChunker` (4), `ComputeSimilarity` (4), `CompareChunkingStrategies` (3), `EmbeddingStore` (8), `SearchWithFilter` (3), `DeleteDocument` (3), `KnowledgeBaseAgent` (2), cùng các test cấu trúc dự án. `HeadingFaqChunker` là lớp tôi tự thêm nên không có test sẵn; nó được kiểm gián tiếp qua benchmark ở mục 5, và tôi **không** đưa nó vào `ChunkingStrategyComparator.compare()` vì đề yêu cầu hàm đó trả về đúng ba key `fixed_size` / `by_sentences` / `recursive`.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Backend: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (`EMBEDDING_PROVIDER=local`). Ngưỡng phân loại: ≥ 0.5 là "cao". Dự đoán được ghi **trước** khi chạy.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Nhà Bán phải xác nhận yêu cầu đổi trả trong 02 ngày làm việc | Người bán có 48 giờ để phản hồi đề nghị trả hàng của khách | cao | **+0.6293** | ✔ |
| 2 | Thời gian bảo hành tối đa là 30 ngày | Sản phẩm được bảo hành trong vòng một tháng | cao | **+0.4514** | ✘ |
| 3 | Chính sách đổi trả hàng hóa trên sàn thương mại điện tử | Công thức nấu phở bò Hà Nội truyền thống | thấp | **+0.0978** | ✔ |
| 4 | Nhà Bán không được đăng bán thuốc lá điếu và xì gà | Danh mục sản phẩm bị cấm kinh doanh trên sàn | cao | **+0.5211** | ✔ |
| 5 | Người tiêu dùng có quyền khiếu nại khi hàng không đúng mô tả | Nhà Bán phải nộp thuế theo quy định pháp luật Việt Nam | thấp | **+0.3657** | ✔ |

**Đúng 4/5.**

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 2 — tôi chắc chắn nhất lại là cặp sai. "30 ngày" và "một tháng" với người đọc là **cùng một khoảng thời gian**, nhưng model chỉ cho 0.4514, thấp hơn cả cặp 1 (0.6293) vốn diễn đạt lệch nhau nhiều hơn về từ ngữ. Lý do: cặp 1 tuy khác từ nhưng cùng một *khung ngữ cảnh* (chủ thể người bán, hành động phản hồi, nghĩa vụ); còn cặp 2 đòi model **quy đổi đơn vị số học** — "30 ngày" = "một tháng" là suy luận, không phải quan hệ phân bố từ. Embedding học từ ngữ cảnh xuất hiện, nên nó nắm *chủ đề* tốt hơn nhiều so với nắm *con số*.
>
> Hệ quả trực tiếp cho lab: các gold answer của nhóm K4 gần như đều là con số ("02 ngày làm việc", "tối đa không quá 30 ngày", "500.000đ", "nhiều hơn 02 bên"). Embedding sẽ đưa đúng *vùng tài liệu* nhưng không phân biệt được chunk nào chứa đúng con số — và mục 5 dưới đây cho thấy đúng hiện tượng đó.
>
> Cặp 5 cũng đáng chú ý: 0.3657 tuy dưới ngưỡng nhưng cao hơn hẳn cặp 3 (0.0978), dù cả hai đều là "cặp không liên quan". Model nhận ra cặp 5 vẫn nằm trong cùng miền TMĐT còn cặp 3 thì lạc hẳn sang ẩm thực. Cosine không phải công tắc bật/tắt mà là một dải liên tục — chọn ngưỡng ở đâu là một quyết định thiết kế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Chiến lược của tôi: `HeadingFaqChunker(max_chunk_size=900, min_chunk_size=120)`** — chia theo cặp FAQ / khoản, có gắn ngữ cảnh mục cha (mô tả ở mục 2).

**Cấu hình chạy:** corpus `data/k4_ecommerce` (10 tài liệu) → `ingest.chunk_document()` → `HeadingFaqChunker` → **166 chunk**. Embedding `EMBEDDING_PROVIDER=local` (`paraphrase-multilingual-MiniLM-L12-v2`). Q1/Q3/Q4 chạy qua `search_with_filter` với `customer_role`; Q2/Q5 chạy `search` thường. Lệnh sinh ra bảng này: `EMBEDDING_PROVIDER=local python src/bench.py --strategy heading`.

**Câu hỏi lấy nguyên văn từ `REPORT_NHOM.md`,** không rút gọn. Đây không phải chi tiết vụn: bản báo cáo trước của tôi chấm bằng các câu hỏi tôi tự viết lại cho ngắn, và ra kết quả **khác hẳn** — riêng câu 5, bản rút gọn "Theo NĐ 85/2021, sàn TMĐT có trách nhiệm gì khi giải quyết khiếu nại?" đẩy gold answer **rớt khỏi top-3**, trong khi câu đầy đủ giữ được ở rank 2. Toàn bộ số dưới đây chạy bằng bộ câu hỏi đã chốt trong `src/bench.py`, đối chiếu một–một với bảng ở mục 3 của báo cáo nhóm.

**`llm_fn` là stub trích xuất, không phải LLM thật** — nó quét top-3 và trả lại nguyên văn câu chứa evidence, không sinh chữ mới. Repo có `OPENAI_API_KEY` trong `.env` nhưng tôi không gọi API. Vì vậy cột "Câu trả lời của Agent" ở đây đo **chất lượng retrieval**, chưa đo chất lượng sinh câu trả lời.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý yêu cầu đổi – trả – bảo hành của khách hàng? *(filter `seller`)* | `[…— III. MÔ HÌNH DROPSHIP] 8. Nhà Bán có thời gian bao lâu để xác nhận yêu cầu đổi, trả, bảo hành?` → chứa "**02 ngày làm việc**" | 0.8440 | **Có — rank 1** | Đúng gold |
| 2 | Thời gian bảo hành mà Nhà Bán được cam kết tối đa là bao lâu, và tính từ lúc nào? | `[…— I. THẮC MẮC CHUNG CHO TẤT CẢ MÔ HÌNH VẬN HÀNH] 5. Thời gian Nhà Bán cam kết bảo hành là bao lâu?` → "**tối đa không quá 30 ngày**" + "không tính thời gian vận chuyển" | 0.8121 | **Có — rank 1** | Đúng gold, đủ cả hai vế |
| 3 | Những loại hàng hóa nào Nhà Bán không được đăng bán trên sàn Tiki? *(filter `seller`)* | `[Danh mục sản phẩm cấm bán…] 3. Nhà Bán không được đăng bất kỳ sản phẩm/hình ảnh nào bị hạn chế hoặc bị cấm…` | 0.7293 | **Một phần** — đúng khoản kế bên; gold ("hàng cũ, like new, **second hand**", khoản 2) ở **rank 2** (0.7178) | Lấy được ở rank 2, không ở rank 1 |
| 4 | Người tiêu dùng nên làm gì để phòng tránh rủi ro khi mua sắm trực tuyến? *(filter `buyer`)* | `[Cảnh báo người tiêu dùng…] 2. Khuyến cáo người tiêu dùng phòng tránh rủi ro khi mua sắm trực tuyến` → trọn cả 5 ý a→e | 0.8603 | **Có — rank 1** | Đúng gold |
| 5 | Theo Nghị định 85/2021/NĐ-CP, sàn TMĐT có trách nhiệm gì trong việc giải quyết khiếu nại của người tiêu dùng? | `[Một số điểm mới…NĐ 85/2021/NĐ-CP] Thứ năm… "Chỉ định đầu mối tiếp nhận yêu cầu…"` → được 2/3 nghĩa vụ | 0.7855 | **Một phần** — gold "**nhiều hơn 02 bên**" nằm ở chunk kế tiếp, **rank 2** (0.7640) | Thiếu nghĩa vụ thứ ba nếu chỉ đọc rank 1 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**

Chấm theo `docs/SCORING.md` (2đ nếu chunk chứa gold ở top-1, 1đ nếu ở top-3, 0đ nếu không có): **3 câu top-1 + 2 câu top-3 = 8/10**.

**Đối chứng bốn chiến lược trên cùng corpus, cùng embedder, cùng 5 query chính thức:**

| Chiến lược | Số chunk | Dài TB | Gold ở top-1 | Gold trong top-3 | Điểm |
|---|---|---|---|---|---|
| `FixedSizeChunker(500, 50)` | 214 | 488 | **5/5** | **5/5** | **10/10** |
| **`HeadingFaqChunker(900, 120)` — của tôi** | **166** | 652 | 3/5 | **5/5** | **8/10** |
| `SentenceChunker(3 câu)` | 168 | 559 | 4/5 | 4/5 | 8/10 |
| `RecursiveChunker(500)` | 268 | 350 | 1/5 | 4/5 | 5/10 |

**Chiến lược của tôi không thắng — và chỗ nó thua mới là phần đáng nói.** Năm điều rút ra:

1. **`FixedSizeChunker` thắng nhờ overlap, không nhờ hiểu cấu trúc.** Hai câu tôi mất điểm (Q3, Q5) giống hệt nhau về cơ chế: gold answer nằm ở **một khoản, còn từ ngữ của câu hỏi lại khớp với khoản liền kề**. Ranh giới cấu trúc của tôi cắt đúng ngay giữa hai khoản đó nên chúng thành hai chunk, và chunk "sai" thắng điểm. Cửa sổ 500 ký tự của `FixedSizeChunker` rộng hơn một khoản nên **nuốt trọn cả hai** — Q3 chunk_2 chứa cả khoản 2 lẫn khoản 3, Q5 chunk_11 chứa cả "đại diện người bán nước ngoài" lẫn "nhiều hơn 02 bên". Nó không hiểu gì về văn bản; nó chỉ có cửa sổ rộng hơn đơn vị mà tôi chọn, cộng thêm 50 ký tự overlap phủ chỗ nối. Chunker của tôi **không có overlap nào cả** — đó là lỗ hổng thiết kế thật sự, không phải xui.
2. **Ranh giới "đúng về cấu trúc" không đồng nghĩa "đúng về truy xuất".** Tôi chọn đơn vị = một khoản vì đó là đơn vị *tác giả* viết ra. Nhưng đơn vị mà *câu hỏi* nhắm tới có khi rộng hơn: "những loại hàng hóa nào bị cấm" hỏi về cả mục, không phải một khoản. Chọn đơn vị ngữ nghĩa là chọn theo **câu hỏi**, không phải theo văn bản — đây là thứ tôi hiểu sai lúc thiết kế.
3. **Nhưng chỉ có tôi và FixedSize đạt 5/5 ở top-3.** `SentenceChunker` và `RecursiveChunker` đều **trượt hẳn Q3** (gold không có trong top-3), tức mất trắng 2 điểm chứ không phải tụt hạng. Chunker của tôi mất điểm vì *thứ hạng*, hai cái kia mất điểm vì *không tìm thấy*. Khoảng cách 8/10 với 8/10 của `SentenceChunker` giấu mất khác biệt đó.
4. **`RecursiveChunker` thua vì cắt nhỏ quá.** 268 chunk, trung bình 350 ký tự — nhỏ nhất và nhiều nhất trong bốn — nên câu hỏi FAQ bị tách khỏi câu trả lời của nó, và chỉ 1/5 câu có gold ở rank 1. Nó tôn trọng ranh giới tự nhiên, nhưng ranh giới tự nhiên ở corpus này (`\n\n` giữa từng đoạn) lại **nhỏ hơn** đơn vị ngữ nghĩa cần thiết. Đây là phiên bản cực đoan của đúng lỗi tôi mắc ở điểm 1.
5. **Ít chunk hơn không tự động tốt hơn — nhưng cũng không tự động tệ hơn.** Của tôi 166 chunk (ít nhất) được 8/10; `RecursiveChunker` 268 chunk (nhiều nhất) được 5/10; `FixedSizeChunker` 214 chunk được 10/10. Không có tương quan nào giữa số chunk và điểm. Cái quyết định là **cửa sổ có phủ trọn đơn vị mà câu hỏi nhắm tới hay không**.

**Cái `FixedSizeChunker` đánh đổi để lấy 10/10:** chunk cắt giữa từ. Top-1 của Q1 mở đầu bằng `"hành xong về cho Khách Hàng…"`, Q2 bằng `"ết bảo hành là bao lâu?"`, Q5 bằng `"tử giải quyết các khiếu nại…"` — ba trên năm câu trả về đoạn cụt đầu, và không chunk nào mang nhãn mục. Embedding chịu được nhiễu đó nên **điểm retrieval không phản ánh thiệt hại**; nhưng đưa nguyên văn vào prompt thì LLM nhận một câu cụt và không có cách nào biết đoạn này thuộc mô hình DROPSHIP hay NGON. Thang điểm của lab chấm ở bước retrieval nên `FixedSizeChunker` được trọn 10 — nếu chấm thêm ở bước sinh câu trả lời và trích nguồn, khoảng cách sẽ hẹp lại. Tôi nêu điều này như một **giới hạn của phép đo**, không phải để đòi lại điểm.

**Nếu làm tiếp, sửa đúng một chỗ:** cho `HeadingFaqChunker` overlap ở mức khoản — mỗi chunk kèm thêm khoản liền trước hoặc liền sau khi tổng độ dài vẫn dưới `max_chunk_size`. Đúng cơ chế đã cứu `FixedSizeChunker` ở Q3 và Q5, nhưng ranh giới vẫn nằm ở chỗ đọc được thay vì giữa từ. Tôi **không** triển khai trong bản nộp này, vì lúc này đã nhìn thấy đáp án của cả 5 câu — sửa tiếp là tuning theo benchmark chứ không còn là thiết kế.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Cần điền sau buổi demo — đây là quan sát trực tiếp tại buổi trình bày, không thể viết trước.* Gợi ý bám vào số liệu bảng trên khi nghe demo: (a) nhóm nào chọn ngưỡng `chunk_size` khác hẳn thì điểm đổi ra sao; (b) có nhóm nào gắn ngữ cảnh cha vào chunk như tôi không, và họ gắn ở cấp nào; (c) nhóm nào đo ở mức chunk, nhóm nào chỉ đo ở mức tài liệu.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Khởi động (Warm-up) | 5 / 5 | Cả hai bài đều trả lời và **kiểm lại bằng code**: 23 chunk / 25 chunk khớp công thức; bảng mock–local đặt cạnh nhau cho thấy `MockEmbedder` xếp cặp *đổi trả ↔ nấu phở* trên cặp cùng nghĩa. |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 | Đủ 7 mục kể cả chunker tự viết và bonus ChromaDB, nêu lý do thiết kế chứ không mô tả lại code (lọc trước-chấm sau, 3 nhánh khớp của `delete_document`, vì sao dùng cosine thay `_dot`, vì sao bỏ ranh giới `a)`, vì sao bật Chroma bằng env chứ không bằng `import` thành công). |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 | **42/42 test pass** trên chính gói cá nhân (`LAB_SOLUTION_PACKAGE=src.K4_2A202601662_HoangCongThanh`), cộng kiểm chứng Chroma persistence bằng hai tiến trình tách rời. |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 | 4/5 dự đoán đúng, và cặp sai được phân tích tới nguyên nhân (embedding nắm chủ đề tốt hơn nắm con số) rồi nối được với kết quả mục 5. |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 | 8/10 theo thang `SCORING.md`: 3 câu gold ở top-1, 2 câu ở top-3, **5/5 câu có gold trong top-3**. Đứng thứ hai sau `FixedSizeChunker` (10/10) — phân tích nguyên nhân thua ở mục 5. |
| **Tổng phần cá nhân** | **58 / 60** | |

> Điểm tự đánh giá là **dự kiến**, chưa phải điểm chấm.

### Việc còn phải làm

- [x] ~~Chốt chiến lược chunking cá nhân~~ — đã chọn và triển khai `HeadingFaqChunker` (`src/K4_2A202601662_HoangCongThanh/chunking.py`), đạt 8/10, đồng thời đáp ứng yêu cầu của `K4_VARIANT.md` là ít nhất một thành viên chia theo điều/khoản/heading/FAQ pair.
- [x] ~~(Tuỳ chọn) ChromaDB persistence~~ — **đã làm**: bật bằng `CHROMA_PERSIST_DIR`, ép không gian cosine, `upsert` để nạp lại được, `$and` cho filter nhiều khoá, `delete_document` idempotent. Kiểm chứng ở mục 3.
- [x] ~~Chấm lại bằng đúng 5 câu hỏi của `REPORT_NHOM.md`~~ — bản trước dùng câu hỏi tự rút gọn nên ra 9/10; chấm lại bằng câu hỏi chính thức ra **8/10**, và `FixedSizeChunker` từ 8/10 lên 10/10. Toàn bộ bảng ở mục 5 đã thay bằng số chạy lại được.
- [ ] Điền ô "học được gì từ thành viên khác" sau buổi demo — không thể viết trước.

### Cách chạy lại toàn bộ số liệu trong báo cáo này

```bash
python -m pip install -r requirements-local.txt
```

Bộ test, chạy trên gói cá nhân:

```bash
LAB_SOLUTION_PACKAGE=src.K4_2A202601662_HoangCongThanh python -m pytest tests/ -q
```

Bảng mục 5 — chiến lược của tôi, rồi ba baseline để đối chứng:

```bash
EMBEDDING_PROVIDER=local python src/bench.py --strategy heading
```

```bash
EMBEDDING_PROVIDER=local python src/bench.py --strategy fixed
```

Bật ChromaDB persistence (mục 2 và mục 3) — đặt biến môi trường là đủ, không phải sửa code:

```bash
CHROMA_PERSIST_DIR=./chroma_data/demo EMBEDDING_PROVIDER=local python src/bench.py --strategy heading
```

`src/bench.py` import chunker/store từ `src.K4_2A202601662_HoangCongThanh`, tức chấm đúng mã nguồn cá nhân, và giữ nguyên văn 5 câu hỏi cùng gold answer của `REPORT_NHOM.md`. Bộ số ở mục 4 và mục 5 sinh bằng `LocalEmbedder` trên `data/k4_ecommerce`; chạy bằng `MockEmbedder` sẽ ra kết quả khác hẳn và không có ý nghĩa ngữ nghĩa (xem cảnh báo ở mục 1).
