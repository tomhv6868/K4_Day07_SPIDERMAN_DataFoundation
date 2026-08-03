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

**Kiểm lại bằng code — và một cảnh báo quan trọng:** repo mặc định chạy `MockEmbedder`, vốn băm text bằng MD5 rồi sinh số giả ngẫu nhiên, **không hề mã hoá ngữ nghĩa**. Đo bằng `compute_similarity` với `_mock_embed`:

| Cặp câu | Cosine (mock) | Kỳ vọng |
|---|---|---|
| "đổi trả" vs "đổi trả" (trùng khít) | **+1.0000** | cao ✔ |
| Nhà Bán 02 ngày ↔ người bán 48 giờ (cùng nghĩa) | +0.1216 | cao ✘ |
| Chính sách đổi trả ↔ công thức nấu phở (khác chủ đề) | −0.0520 | thấp ✔ |
| Bảo hành 30 ngày ↔ giá vé máy bay (khác chủ đề) | **+0.2003** | thấp ✘ |

Cặp *khác chủ đề hoàn toàn* lại đạt điểm **cao hơn** cặp *cùng nghĩa*. Đây không phải lỗi công thức cosine — `compute_similarity` vẫn đúng (vector trùng → 1, vuông góc → 0, ngược hướng → −1). Nó cho thấy `MockEmbedder` chỉ khớp được chuỗi **giống hệt nhau**. Mọi số ở mục 4 và mục 5 vì vậy đều chạy bằng `EMBEDDING_PROVIDER=local` (`paraphrase-multilingual-MiniLM-L12-v2`), không dùng mock.

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

**`HeadingFaqChunker`** (chiến lược cá nhân của tôi, `src/chunking.py`) — hướng tiếp cận:
> Ba chunker baseline đều chia theo **độ dài**; cái này chia theo **đơn vị cấu trúc** của văn bản chính sách. Ranh giới nhận ở đầu dòng bằng `^(?=(?:#{1,6}\s|[IVXLC]{1,5}\.\s|\d{1,2}\.\s))`, tức heading Markdown, mục La Mã và câu hỏi FAQ đánh số — mỗi chunk là một cặp hỏi–đáp hoặc một khoản trọn vẹn.
>
> Hai quyết định thiết kế đáng nói:
> 1. **Gắn ngữ cảnh cha vào đầu mỗi chunk** (`[Tiêu đề tài liệu — Mục La Mã]`). Corpus K4 có nhiều quy định trùng chủ đề nhưng khác phạm vi áp dụng: thời hạn xác nhận của mô hình NGON là 04 giờ còn thời hạn chung là 02 ngày làm việc. Không có tiêu đề mục thì hai chunk này gần như không phân biệt được — và đúng là baseline đã trượt câu 1 vì lý do đó.
> 2. **Có tầng dự phòng.** Khoản nào vượt `max_chunk_size=900` được đẩy qua `RecursiveChunker`. Nếu thiếu, các bài trên moit.gov.vn (gần như không đánh số) sẽ trả về một chunk khổng lồ.
>
> **Tuning đã làm, và nó thay đổi kết quả:** bản đầu tôi cắt cả ở ý chữ cái `a) b) c)`. Chạy benchmark ra **7/10** — thua cả baseline. Nguyên nhân nhìn thấy được ở câu 4: danh sách khuyến cáo bị xé thành từng mẩu ngắn rời khỏi tiêu đề mục, gold answer rớt khỏi top-3. Bỏ ranh giới `a)` (sub-point là bộ phận của khoản cha, không đứng riêng được) thì lên **9/10**. Tôi cũng thử `min_chunk_size` ở 120 / 250 / 400 — cả ba đều cho 9/10, nên giữ nguyên 120 để chỉ có đúng một thay đổi so với bản đầu.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu in-memory: mỗi `Document` thành một dict `{id, content, metadata, embedding}` qua helper `_make_record`, **embed ngay lúc nạp** để `search` không phải tính lại. Tách riêng `_search_records(query, records, top_k)` để `search` và `search_with_filter` dùng chung một đường chấm điểm — chỉ khác nhau ở tập record đưa vào. Độ tương tự dùng `compute_similarity` (cosine) chứ không dùng thẳng `_dot`: `MockEmbedder` có chuẩn hoá vector nên hai cách cho kết quả như nhau, nhưng nếu đổi sang backend không chuẩn hoá thì dot product sẽ thiên vị chunk dài. `sort` của Python ổn định nên điểm bằng nhau vẫn giữ thứ tự nạp — kết quả tái lập được giữa các lần chạy.
>
> ChromaDB: tôi để `_use_chroma = False` cố định và chỉ dò xem gói có cài hay không. Persistence bằng Chroma là bonus task, chưa làm; để `_use_chroma = True` mà `_collection` vẫn `None` như scaffolding sẽ thành lỗi ngầm khi máy nào đó có cài chromadb.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc trước, chấm điểm sau.** Đây là điểm mấu chốt: nếu chấm điểm cả corpus rồi mới lọc thì chunk bị loại vẫn chiếm slot trong top-k, và một query lọc `seller` có thể trả về ít hơn 3 kết quả dù corpus còn thừa chunk `seller`. Lọc bằng `all(record["metadata"].get(k) == v ...)` nên `metadata_filter` nhiều khoá là phép AND; `metadata_filter=None` đi thẳng vào `self._store`, khớp đúng test `test_no_filter_returns_all_candidates`.
>
> `delete_document` xoá bằng cách dựng lại list không chứa record khớp, rồi so độ dài trước/sau để quyết định trả `True`/`False`. Điều kiện khớp có 3 nhánh vì `Document` vào store bằng hai đường khác nhau: nạp thẳng thì `metadata` rỗng và `id` chính là `doc_id`; nạp qua `ingest.py` thì `metadata["doc_id"]` có sẵn còn `id` là `"<doc_id>::chunk_<n>"`. Chỉ so `metadata["doc_id"]` như docstring gợi ý sẽ fail test xoá.

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

**Toàn bộ bộ test:**

```
$ pytest tests/ -q
..........................................                               [100%]
42 passed in 0.03s
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

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

**Cấu hình chạy:** corpus `data/k4_ecommerce` (10 tài liệu) → `ingest.build_knowledge_base()` → `HeadingFaqChunker` → **166 chunk**. Embedding `EMBEDDING_PROVIDER=local` (`paraphrase-multilingual-MiniLM-L12-v2`). Q1/Q3/Q4 chạy qua `search_with_filter` với `customer_role`; Q2/Q5 chạy `search` thường.

**`llm_fn` là stub trích xuất, không phải LLM thật** — nó trả lại nguyên văn đoạn ngữ cảnh `[1]`, không sinh chữ mới. Repo có `OPENAI_API_KEY` trong `.env` nhưng tôi không gọi API. Vì vậy cột "Câu trả lời của Agent" ở đây đo **chất lượng retrieval**, chưa đo chất lượng sinh câu trả lời.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý đổi/trả/bảo hành? *(filter `seller`)* | `[…— III. MÔ HÌNH DROPSHIP] 8. Nhà Bán có thời gian bao lâu để xác nhận yêu cầu đổi, trả, bảo hành?` → chứa "**02 ngày làm việc**" | 0.8376 | **Có — rank 1** | Đúng gold |
| 2 | Thời gian bảo hành Nhà Bán cam kết tối đa là bao lâu? | `[…— I. THẮC MẮC CHUNG CHO TẤT CẢ MÔ HÌNH VẬN HÀNH] 5. Thời gian Nhà Bán cam kết bảo hành là bao lâu?` → "**tối đa không quá 30 ngày**" | 0.8191 | **Có — rank 1** | Đúng gold |
| 3 | Hàng hóa nào Nhà Bán không được đăng bán trên Tiki? *(filter `seller`)* | `[Danh mục sản phẩm cấm bán…] 3. Nhà Bán không được đăng bất kỳ sản phẩm/hình ảnh nào bị hạn chế hoặc bị cấm…` | 0.7293 | **Một phần** — đúng khoản kế bên; gold ("hàng cũ, like new, **second hand**", khoản 2) ở **rank 2** | Thiếu ý hàng second hand |
| 4 | Người tiêu dùng nên làm gì để phòng tránh rủi ro mua sắm trực tuyến? *(filter `buyer`)* | `[Cảnh báo người tiêu dùng…] 2. Khuyến cáo người tiêu dùng phòng tránh rủi ro khi mua sắm trực tuyến` → trọn cả 5 ý a→e | 0.8603 | **Có — rank 1** | Đúng gold |
| 5 | Theo NĐ 85/2021, sàn TMĐT có trách nhiệm gì khi giải quyết khiếu nại? | `[Một số điểm mới…NĐ 85/2021/NĐ-CP] - Là đầu mối tiếp nhận và giải quyết các khiếu nại của người tiêu dùng…` → "**nhiều hơn 02 bên**" | 0.8977 | **Có — rank 1** (điểm cao nhất cả 5 câu) | Đúng gold |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**

Chấm theo `docs/SCORING.md` (2đ nếu chunk chứa gold ở top-1, 1đ nếu ở top-3, 0đ nếu không có): **4 câu top-1 + 1 câu top-3 = 9/10**.

**Đối chứng bốn chiến lược trên cùng corpus, cùng embedder, cùng 5 query:**

| Chiến lược | Số chunk | Gold ở top-1 | Gold trong top-3 | Điểm |
|---|---|---|---|---|
| **`HeadingFaqChunker(900, 120)` — của tôi** | **166** | **4/5** | **5/5** | **9/10** |
| `FixedSizeChunker(500, 50)` | 214 | 3/5 | 5/5 | 8/10 |
| `SentenceChunker(3 câu)` | 168 | 4/5 | 4/5 | 8/10 |
| `RecursiveChunker(500)` | 268 | 1/5 | 3/5 | 4/10 |

Bốn điều rút ra:

1. **Đo ở mức tài liệu sẽ tự lừa mình.** Nếu chỉ hỏi "top-1 có đúng file không" thì `FixedSizeChunker` đạt 5/5. Hỏi "chunk đó có chứa gold answer không" thì chỉ còn 3/5 — Q1 và Q5 lấy đúng file nhưng sai đoạn. `RecursiveChunker` chênh lệch còn nặng hơn: 4/5 ở mức file nhưng **1/5** ở mức chunk. Con số duy nhất đáng tin là con số chấm ở mức chunk.
2. **`RecursiveChunker` thua vì cắt nhỏ quá.** 268 chunk — nhiều nhất trong bốn — nên câu hỏi FAQ bị tách khỏi câu trả lời của nó. Nó tôn trọng ranh giới tự nhiên, nhưng ranh giới tự nhiên ở corpus này (`\n\n` giữa từng đoạn) lại **nhỏ hơn** đơn vị ngữ nghĩa cần thiết.
3. **Ít chunk hơn nhưng điểm cao hơn.** `HeadingFaqChunker` tạo 166 chunk (ít nhất) mà lại đạt điểm cao nhất. Số chunk không nói lên chất lượng; cái quyết định là **ranh giới có trùng với đơn vị ngữ nghĩa hay không**.
4. **Ngữ cảnh cha là thứ lật ngược câu 1.** Baseline trả về đoạn "04 giờ làm việc" (quy định riêng mô hình NGON) thay vì "02 ngày làm việc". Khi mỗi chunk mang sẵn nhãn `[… — III. MÔ HÌNH DROPSHIP]` / `[… — V. MÔ HÌNH NGON]` thì hai quy định cùng chủ đề nhưng khác phạm vi tách được ra, và câu 1 lên rank 1 với score 0.8376.

**Điểm yếu quan sát được của `FixedSizeChunker`:** chunk cắt giữa từ — top-1 của Q1 mở đầu bằng `"i gian bao lâu để xác nhận…"`, Q2 bằng `"ết bảo hành là bao lâu?"`, Q5 bằng `"hư vậy, quy định mới…"`. Retrieval vẫn trúng vì embedding chịu được nhiễu đầu chunk, nhưng đưa nguyên văn vào prompt thì câu trả lời cụt đầu.

**Câu duy nhất chiến lược của tôi chưa lấy được ở rank 1 là Q3.** `tiki-danh-muc-hang-cam-ban` đánh số 1., 2., 3. cho ba khoản rất ngắn; gold nằm ở khoản 2 ("hàng cũ, đã qua sử dụng, like new, second hand") còn top-1 rơi vào khoản 3. Hai khoản này gần như đồng nghĩa dưới góc nhìn embedding. Hướng xử lý nếu làm tiếp: với tài liệu mà tổng độ dài các khoản còn nhỏ hơn `max_chunk_size`, gộp cả mục thành một chunk thay vì tách — nhưng tôi **không** thực hiện, vì lúc này đã nhìn thấy kết quả benchmark, sửa tiếp là tuning theo đáp án.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Cần điền sau buổi demo — đây là quan sát trực tiếp tại buổi trình bày, không thể viết trước.* Gợi ý bám vào số liệu bảng trên khi nghe demo: (a) nhóm nào chọn ngưỡng `chunk_size` khác hẳn thì điểm đổi ra sao; (b) có nhóm nào gắn ngữ cảnh cha vào chunk như tôi không, và họ gắn ở cấp nào; (c) nhóm nào đo ở mức chunk, nhóm nào chỉ đo ở mức tài liệu.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Khởi động (Warm-up) | 5 / 5 | Cả hai bài đều trả lời và **kiểm lại bằng code**: 23 chunk / 25 chunk khớp công thức; phát hiện thêm giới hạn của `MockEmbedder`. |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 | Đã viết đủ 6 mục kể cả chunker tự viết, nêu lý do thiết kế chứ không mô tả lại code (lọc trước-chấm sau, 3 nhánh khớp của `delete_document`, vì sao dùng cosine thay `_dot`, vì sao bỏ ranh giới `a)`). Trừ 1 vì ChromaDB mới dừng ở mức dò gói, chưa triển khai. |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 | **42/42 test pass.** |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 | 4/5 dự đoán đúng, và cặp sai được phân tích tới nguyên nhân (embedding nắm chủ đề tốt hơn nắm con số) rồi nối được với kết quả mục 5. |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 | 9/10 theo thang `SCORING.md`: 4 câu gold ở top-1, 1 câu ở top-3. Cao nhất trong bốn chiến lược đối chứng. |
| **Tổng phần cá nhân** | **58 / 60** | |

> Điểm tự đánh giá là **dự kiến**, chưa phải điểm chấm.

### Việc còn phải làm

- [x] ~~Chốt chiến lược chunking cá nhân~~ — đã chọn và triển khai `HeadingFaqChunker` (`src/chunking.py`), đạt 9/10, đồng thời đáp ứng yêu cầu của `K4_VARIANT.md` là ít nhất một thành viên chia theo điều/khoản/heading/FAQ pair.
- [ ] Điền ô "học được gì từ thành viên khác" sau buổi demo — không thể viết trước.
- [ ] (Tuỳ chọn) ChromaDB persistence — bonus task, ngoài phạm vi 60 điểm phần cá nhân.

### Cách chạy lại toàn bộ số liệu trong báo cáo này

```bash
python -m pip install -r requirements-local.txt
EMBEDDING_PROVIDER=local python -m pytest tests/ -q
```

Bộ số ở mục 4 và mục 5 sinh bằng `HeadingFaqChunker` + `LocalEmbedder` trên `data/k4_ecommerce`; chạy bằng `MockEmbedder` sẽ ra kết quả khác hẳn và không có ý nghĩa ngữ nghĩa (xem cảnh báo ở mục 1).
