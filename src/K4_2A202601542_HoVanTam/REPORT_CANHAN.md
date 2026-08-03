# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hồ Văn Tâm — 2A202601542  
**Nhóm:** SPIDERMAN  
**Ngày:** 03-08-2026

## Tóm tắt phần việc

Phần việc của tôi là hoàn thiện luồng benchmark và kiểm tra retrieval ở mức chunk:

- `bench.py`: chạy cùng corpus và 5 query của nhóm, chọn strategy, in số chunk, top-3, score, provenance và A/B metadata filter.
- `check_benchmark.py`: kiểm tra Precision@3, chunk coherence, filter utility, grounding và ghi failure case.
- Bổ sung `document_version` và `retrieved_at` vào phần provenance của kết quả retrieve.

Strategy dùng cho benchmark cá nhân là `FixedSizeChunker(chunk_size=500, overlap=50)`. Tôi giữ nguyên corpus, query, gold answer và embedder giữa các lần chạy; chỉ thay strategy.

> Lưu ý: môi trường chạy hiện tại chưa cài `sentence-transformers`, nên kết quả dưới đây dùng `MockEmbedder`. MockEmbedder deterministic nhưng không biểu diễn ngữ nghĩa. Vì vậy score/retrieval chỉ dùng để kiểm tra pipeline kỹ thuật; không dùng để kết luận chất lượng semantic retrieval.

## 1. Khởi động (Warm-up)

Cosine similarity đo góc giữa hai vector embedding. Cosine cao nghĩa là hai đoạn nằm gần nhau trong không gian biểu diễn, nhưng không đảm bảo chúng chứa cùng đáp án hoặc cùng số liệu.

Với tài liệu dài 10.000 ký tự, `chunk_size=500`, `overlap=50`:

```text
step = 500 - 50 = 450
ceil((10.000 - 50) / 450) = 23 chunk
```

Nếu overlap tăng lên 100:

```text
step = 500 - 100 = 400
ceil((10.000 - 100) / 400) = 25 chunk
```

Overlap lớn hơn giúp câu trả lời bị cắt ở biên vẫn xuất hiện trong ít nhất một chunk, nhưng làm tăng số vector và nội dung trùng lặp.

## 2. Hướng tiếp cận của tôi

### Strategy `FixedSizeChunker(500, 50)`

Tôi chọn fixed-size làm baseline vì tham số rõ ràng và dễ tái lập. Mỗi chunk dài tối đa 500 ký tự, chunk kế tiếp lùi lại 50 ký tự để giữ một phần context ở biên. Đổi lại, strategy này có thể cắt giữa từ hoặc giữa câu, nên điều kiện và ngoại lệ có thể bị tách khỏi số liệu.

### Pipeline benchmark

`bench.py` dùng lại `ingest.build_knowledge_base()`:

1. Parse front matter thành metadata.
2. Chunk phần body bằng strategy được chọn.
3. Gắn `doc_id`, `chunk_index` và metadata lên từng chunk.
4. Embed và nạp vào `EmbeddingStore`.

Năm query dùng chung của nhóm giữ nguyên, trong đó Q1/Q3 lọc `customer_role=seller`, Q4 lọc `customer_role=buyer`; Q2/Q5 không lọc.

### Kiểm tra `check_benchmark.py`

Script khai báo evidence substring cho từng gold answer. Với mỗi query, script:

- kiểm tra evidence có nằm trong top-3 hay không;
- kiểm tra các term điều kiện/ngoại lệ có còn trong context không;
- so sánh kết quả có filter và không filter;
- kiểm tra câu trả lời extractive có dựa trên context retrieve không;
- in top-3, score, `doc_id`, `document_version` và lý do failure.

## 3. Hoàn thiện code — kết quả kiểm thử

Lệnh chạy:

```text
python -m pytest tests -v
```

Kết quả: **42/42 test pass**. Có warning về quyền ghi `.pytest_cache` và cấu hình `pytest-asyncio`; không có test failure.

Lệnh benchmark cá nhân:

```text
python bench.py --strategy fixed --provider mock
python check_benchmark.py --strategy fixed --provider mock
```

Kết quả nạp: **214 chunk**.

## 4. Dự đoán độ tương tự

Các giá trị dưới đây được đo bằng MockEmbedder; chúng minh họa giới hạn của embedder deterministic, không phải chất lượng semantic.

| Cặp | Dự đoán | Cosine mock | Nhận xét |
|---|---|---:|---|
| Hai câu cùng nói về hạn phản hồi đổi trả | cao | -0.0142 | Mock không nhận ra paraphrase |
| Chính sách đổi trả / công thức nấu phở | thấp | -0.0731 | Kết quả thấp phù hợp ngẫu nhiên |
| Bảo hành 30 ngày / thời hạn bảo hành 30 ngày | cao | 0.0552 | Điểm vẫn rất thấp dù nội dung gần nhau |
| Khiếu nại trên sàn / giao dịch nhiều hơn 02 bên | trung bình | -0.0604 | Có liên quan chủ đề nhưng mock không biểu diễn nghĩa |
| Hàng cũ bị cấm / đồ chơi nguy hiểm bị cấm | trung bình | -0.0769 | Cùng chủ đề listing nhưng điểm không ổn định |

Kết quả bất ngờ xác nhận rằng cosine implementation không phải vấn đề; giới hạn nằm ở cách MockEmbedder sinh vector từ hash text.

## 5. Kết quả truy xuất cá nhân

### Tổng hợp từ `check_benchmark.py`

| Q | Filter | Precision@3 | Coherence | Grounding | Evidence |
|---:|---|---|---|---|---|
| 1 | `seller` | FAIL | FAIL | FAIL | Không có |
| 2 | Không | FAIL | FAIL | FAIL | Không có |
| 3 | `seller` | FAIL | FAIL | FAIL | Không có |
| 4 | `buyer` | FAIL | FAIL | FAIL | Không có |
| 5 | Không | FAIL | FAIL | FAIL | Không có |

`check_benchmark.py` ghi nhận `precision_failures=5`. Với Q1, Q3 và Q4, A/B filter đều cho top-3 khác nhau (`CHANGED`), nhưng trong MockEmbedder run này filter chưa đưa chunk chứa evidence vào top-3.

### Top-3 thực tế

| Q | Top-1 (`score`, `doc_id`) | Top-2 | Top-3 | Kết luận |
|---:|---|---|---|---|
| 1 | 0.3793 — `moit-trach-nhiem-ban-le-hang-tieu-dung::chunk_4` | 0.3555 — cùng tài liệu, chunk 17 | 0.2521 — cùng tài liệu, chunk 14 | Đúng vùng seller nhưng không có “02 ngày làm việc” |
| 2 | 0.3520 — `moit-trach-nhiem-ban-le-hang-tieu-dung::chunk_0` | 0.3506 — `tiki-xu-ly-doi-tra-bao-hanh::chunk_2` | 0.3341 — `moit-quy-dinh-moi-luat-bvqltd-2023::chunk_9` | Không có gold bảo hành trong top-3 |
| 3 | 0.3197 — `tiki-quyen-nghia-vu-nha-ban::chunk_3` | 0.2811 — `tiki-xu-ly-doi-tra-bao-hanh::chunk_29` | 0.2639 — `tiki-quyen-nghia-vu-nha-ban::chunk_5` | Đúng chủ đề Nhà Bán nhưng không có “second hand” |
| 4 | 0.2655 — `moit-quy-dinh-moi-luat-bvqltd-2023::chunk_4` | 0.2079 — `bvntd-quy-trinh-khieu-nai-nguoi-tieu-dung::chunk_0` | 0.1989 — `moit-quy-dinh-moi-luat-bvqltd-2023::chunk_11` | Không có danh sách khuyến cáo mua sắm |
| 5 | 0.3072 — `moit-quy-dinh-moi-luat-bvqltd-2023::chunk_21` | 0.3021 — `moit-trach-nhiem-ban-le-hang-tieu-dung::chunk_31` | 0.2973 — `bvntd-kiem-soat-chat-luong-hang-hoa-tmdt::chunk_47` | Không có “nhiều hơn 02 bên” |

Agent answer ở cả năm query là: **“Không có câu chứa evidence trong top-3.”** Vì vậy grounding không đạt trong run MockEmbedder này.

### Failure case tiêu biểu — Q1

- **Query:** Nhà Bán có bao nhiêu thời gian để xác nhận phương án đổi/trả/bảo hành?
- **Gold evidence:** `02 ngày làm việc`.
- **Bằng chứng top-k:** cả ba chunk đầu đều thuộc tài liệu bán lẻ hoặc seller, nhưng không chunk nào chứa evidence; top-1 đạt score 0.3793.
- **Nguyên nhân:** MockEmbedder không biểu diễn ngữ nghĩa; score cao chỉ phản ánh vector hash gần nhau. Ngoài ra fixed-size có thể cắt câu chứa thời hạn khỏi phần context liên quan.
- **Đề xuất:** chạy lại bằng local multilingual embedding; sau đó kiểm tra overlap/chunk boundary và cân nhắc reranking theo evidence số liệu.

## 6. Reflection

Fixed-size có ưu điểm là đơn giản, nhanh và tạo được số chunk tái lập. Tuy nhiên, nó không hiểu cấu trúc FAQ/section nên có thể đưa đúng tài liệu nhưng sai đoạn. Với corpus chính sách, chunker theo heading/FAQ có khả năng giữ điều kiện và ngoại lệ tốt hơn, còn fixed-size phù hợp làm baseline đối chứng.

Kết quả MockEmbedder không được dùng để tuyên bố strategy kém về semantic retrieval. Giá trị chính của run này là chứng minh pipeline benchmark, metadata provenance, A/B filter và cách chấm ở mức chunk hoạt động đúng.

## Tự đánh giá

| Tiêu chí | Tự đánh giá | Căn cứ |
|---|---:|---|
| Khởi động | 5/5 | Hoàn thành cosine và bài toán số chunk |
| Hướng tiếp cận | 9/10 | Có strategy fixed-size và benchmark/evaluation script riêng |
| Core implementation | 30/30 | 42/42 test pass |
| Dự đoán similarity | 4/5 | Có đo lại bằng code và phân tích giới hạn mock |
| Kết quả truy xuất | Chưa kết luận semantic | MockEmbedder không phù hợp để chấm chất lượng nghĩa |
| **Tổng tạm tính** | **48/50 trước retrieval** | Cần chạy local embedder để chốt phần retrieval |

