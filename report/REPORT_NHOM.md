# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [SPIDERMAN]
**Thành viên:** [
Nguyễn Quý Dương - 2A202601642  
Trần Văn Ngọc - 2A202601512 - TrNgoc2301
Hoàng Công Thành - 2A202601662 - stephHoang30
Nguyễn Hoàng Bảo Minh - 2A202601626 - minhmap123
Hồ Văn Tâm - 2A202601542 - tomhv6868
]
**Ngày:** [03-08-2026]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Đổi trả – hoàn tiền – khiếu nại trong TMĐT Việt Nam, nhìn từ **hai phía**: nghĩa vụ của người bán trên sàn (quy định sàn Tiki) và quyền của người mua (Luật BVQLNTD 2023, Nghị định 85/2021/NĐ-CP, khuyến cáo của cơ quan bảo vệ người tiêu dùng).

### Danh sách tài liệu (Data Inventory)

Corpus: `data/k4_ecommerce/` — 10 tài liệu, thu thập ngày **2026-08-03** bằng `scripts/fetch_public_pages.py` rồi làm sạch bằng `scripts/clean_k4_corpus.py`. Danh sách URL đầu vào ở `data/urls.csv`; kiểm kê một–một ở `data/k4_ecommerce/sources.csv`.

| # | Tên tài liệu (`doc_id`) | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `tiki-xu-ly-doi-tra-bao-hanh` — FAQ xử lý đổi/trả/bảo hành cho Nhà Bán | hocvien.tiki.vn/faq/cau-hoi-thuong-gap-ve-xu-ly-doi-tra-bao-hanh/ | 2026-08-03 / not-stated | 13.589 | `seller`, `returns-policy`, `vi` |
| 2 | `tiki-quyen-nghia-vu-nha-ban` — Quyền và nghĩa vụ của Nhà Bán và Tiki | hocvien.tiki.vn/faq/quyen-va-nghia-vu-cua-nha-ban-va-tiki/ | 2026-08-03 / not-stated | 5.243 | `seller`, `seller-obligations`, `vi` |
| 3 | `tiki-danh-muc-hang-cam-ban` — Danh mục sản phẩm cấm bán trên sàn Tiki | hocvien.tiki.vn/faq/danh-muc-san-pham-cam-ban-tren-sgd-tmdt-tiki/ | 2026-08-03 / not-stated | 2.183 | `seller`, `listing-policy`, `vi` |
| 4 | `tiki-quy-dinh-tu-khoa-san-pham` — Quy định từ khóa trong nội dung sản phẩm | hocvien.tiki.vn/faq/quy-dinh-tu-khoa-trong-noi-dung-san-pham/ | 2026-08-03 / not-stated | 1.181 | `seller`, `listing-policy`, `vi` |
| 5 | `moit-trach-nhiem-ban-le-hang-tieu-dung` — Trách nhiệm BVQLNTD của tổ chức, cá nhân bán lẻ | moit.gov.vn/tin-tuc/bao-chi-voi-nguoi-dan/…ban-le-hang-tieu-dun.html | 2026-08-03 / 2024-08-20 | 15.836 | `seller`, `seller-obligations`, `vi` |
| 6 | `bvntd-rui-ro-mua-sam-truc-tuyen` — Cảnh báo rủi ro khi mua sắm trực tuyến | dnvntd.bvntd.gov.vn/canh-bao-nguoi-tieu-dung-truoc-cac-rui-ro-khi-mua-sam-truc-tuyen-a1622 | 2026-08-03 / not-stated | 5.082 | `buyer`, `consumer-guidance`, `vi` |
| 7 | `moit-quy-dinh-moi-luat-bvqltd-2023` — Quy định mới tại Luật BVQLNTD 2023 | moit.gov.vn/tin-tuc/bao-chi-voi-nguoi-dan/mot-so-quy-dinh-moi-tai-luat-…-2023.html | 2026-08-03 / 2023-06-29 | 12.936 | `buyer`, `consumer-rights`, `vi` |
| 8 | `bvntd-quy-trinh-khieu-nai-nguoi-tieu-dung` — Tiếp nhận, giải quyết khiếu nại của NTD | bvntd.gov.vn/tintuc_sukien/thong-tin-ve-viec-tiep-nhan-giai-quyet-yeu-cau-khieu-nai-cua-nguoi-tieu-dung/ | 2026-08-03 / not-stated | 3.660 | `buyer`, `complaint-handling`, `vi` |
| 9 | `moit-nghi-dinh-85-2021-tmdt` — Điểm mới BVQLNTD trong Nghị định 85/2021/NĐ-CP | moit.gov.vn/tin-tuc/thong-bao/mot-so-diem-moi-ve-bao-ve-quyen-loi-nguoi-tieu-dung…html | 2026-08-03 / 2021-10-18 | 5.933 | `both`, `legal-framework`, `vi` |
| 10 | `bvntd-kiem-soat-chat-luong-hang-hoa-tmdt` — Kiểm soát chất lượng hàng hóa trong TMĐT | bvntd.gov.vn/tintuc_sukien/kiem-soat-chat-luong-hang-hoa-trong-thuong-mai-dien-tu…/ | 2026-08-03 / not-stated | 27.968 | `both`, `quality-control`, `vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

**Ghi chú về nguồn:** cả 10 URL đều qua kiểm tra `robots.txt` bằng `RobotFileParser` trước khi tải, giãn cách ≥ 2 giây/request, không đăng nhập và không vượt CAPTCHA. Một số nguồn TMĐT phổ biến (thegioididong.com, fptshop.com.vn, sendo.vn) **bị `robots.txt` chặn nên nhóm đã loại bỏ**, không tìm cách đi vòng. Tài liệu #8 là bản tin tiếp nhận khiếu nại của Cục CT&BVNTD (số liệu tháng 10/2019, cơ quan nay là Ủy ban Cạnh tranh Quốc gia) — giữ lại vì đây là tài liệu duy nhất mô tả kênh khiếu nại chính thức, nhưng cần lưu ý độ cũ khi trích gold answer.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string (slug, trùng tên file) | `tiki-xu-ly-doi-tra-bao-hanh` | Khoá duy nhất để gắn chunk về đúng tài liệu gốc và cho `delete_document()` hoạt động. |
| `customer_role` | enum: `buyer` / `seller` / `both` | `seller` | **Trường phân vai bắt buộc của K4.** Cùng một từ khoá "đổi trả" xuất hiện ở cả tài liệu người mua lẫn người bán; lọc theo vai loại được nửa corpus không liên quan. Phân bố: 5 `seller`, 3 `buyer`, 2 `both`. |
| `category` | enum: `returns-policy`, `seller-obligations`, `listing-policy`, `consumer-rights`, `consumer-guidance`, `complaint-handling`, `legal-framework`, `quality-control` | `listing-policy` | Tách hai loại câu hỏi dễ lẫn của cùng một vai: quy định *đăng bán* và quy trình *đổi trả* đều thuộc `seller`. |
| `source_url` | URL | `https://hocvien.tiki.vn/faq/...` | Truy vết nguồn gốc để kiểm chứng gold answer; hiển thị kèm câu trả lời của agent. |
| `retrieved_at` | date `YYYY-MM-DD` | `2026-08-03` | Cho biết dữ liệu cũ bao lâu — chính sách TMĐT thay đổi thường xuyên. |
| `document_version` | date hoặc `not-stated` | `2021-10-18` | Phân biệt bản Nghị định 85/2021 với Luật 2023 khi cả hai cùng nói về trách nhiệm sàn TMĐT. |
| `language` | ISO 639-1 | `vi` | Corpus hiện toàn tiếng Việt; giữ trường này để mở rộng sang nguồn tiếng Anh mà không phải đổi schema. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

> **Trạng thái: bản đề xuất — Benchmark owner chốt trước khi ai chạy benchmark.** Cả 5 gold answer dưới đây đã kiểm chứng là trích được nguyên văn từ corpus. Sau khi chốt thì không đổi nữa.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý yêu cầu đổi – trả – bảo hành của khách hàng? <br>*(dùng `metadata_filter={"customer_role": "seller"}`)* | **02 ngày làm việc.** Quá hạn, Tiki chủ động xử lý theo yêu cầu khách hàng (hoàn tiền hoặc tạo đơn hàng mới để đổi) và được quyền từ chối tiếp nhận khiếu nại của Nhà Bán phát sinh sau thời hạn này. Riêng mô hình NGON là tối đa 04 giờ làm việc. | `tiki-xu-ly-doi-tra-bao-hanh` — mục I.4 và III.8 |
| 2 | Thời gian bảo hành mà Nhà Bán được cam kết tối đa là bao lâu, và tính từ lúc nào? | **Tối đa không quá 30 ngày**, tính từ thời điểm Nhà Bán nhận được hàng đến khi bảo hành xong, **không tính thời gian vận chuyển**. | `tiki-xu-ly-doi-tra-bao-hanh` — mục I.5 |
| 3 | Những loại hàng hóa nào Nhà Bán không được đăng bán trên sàn Tiki? <br>*(dùng `metadata_filter={"customer_role": "seller"}`)* | Vũ khí, chất nổ, pháo, hóa chất độc hại; thuốc lá điếu và xì gà; văn hóa phẩm đồi trụy/phản động; động thực vật hoang dã quý hiếm; ma túy và chất gây nghiện; đồ chơi nguy hiểm. Ngoài ra **Tiki không hỗ trợ bán hàng cũ, đã qua sử dụng, like new, second hand**. | `tiki-danh-muc-hang-cam-ban` — mục 1 và 2 |
| 4 | Người tiêu dùng nên làm gì để phòng tránh rủi ro khi mua sắm trực tuyến? <br>*(dùng `metadata_filter={"customer_role": "buyer"}`)* | Mua tại sàn TMĐT uy tín, được cấp phép, có thông tin liên lạc rõ ràng; chọn nhà bán có uy tín cao và đánh giá tích cực; **tìm hiểu kỹ điều kiện giao dịch về bảo hành, trả lại hàng, hoàn tiền, giao nhận**; tìm hiểu kỹ sản phẩm; cảnh giác với trang web lạ đòi cung cấp thông tin cá nhân hoặc đặt cọc trước. | `bvntd-rui-ro-mua-sam-truc-tuyen` — mục 2, ý a→e |
| 5 | Theo Nghị định 85/2021/NĐ-CP, sàn TMĐT có trách nhiệm gì trong việc giải quyết khiếu nại của người tiêu dùng? | Chỉ định đầu mối tiếp nhận yêu cầu và cung cấp thông tin trực tuyến cho cơ quan quản lý nhà nước (**trong vòng 24 giờ** kể từ khi tiếp nhận); **đại diện cho người bán nước ngoài** trên sàn giải quyết khiếu nại của NTD; là **đầu mối tiếp nhận và giải quyết khiếu nại** khi một giao dịch trên sàn có **nhiều hơn 02 bên** tham gia. | `moit-nghi-dinh-85-2021-tmdt` — mục "Thứ năm", Khoản 11 Điều 36 |

**Vì sao bộ câu hỏi này chứng minh được giá trị của metadata:** Q1 và Q3 hỏi bằng từ khoá ("đổi trả", "hàng hóa không được bán") trùng với ngôn ngữ của tài liệu phía người mua — không lọc `customer_role` thì chunk từ `bvntd-*` và `moit-*` sẽ cạnh tranh trong top-3. Q4 là trường hợp ngược lại: lọc `buyer` để loại 5 tài liệu `seller`. Q2 và Q5 cố ý **không** cần filter để làm đối chứng.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
