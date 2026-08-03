"""5 benchmark query đã chốt cho corpus data/k4_ecommerce (xem report/REPORT_NHOM.md mục 3)."""

QUERIES = [
    {
        "text": "Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý yêu cầu đổi – trả – bảo hành của khách hàng?",
        "gold": (
            "02 ngày làm việc. Quá hạn, Tiki chủ động xử lý theo yêu cầu khách hàng "
            "(hoàn tiền hoặc tạo đơn hàng mới để đổi) và được quyền từ chối tiếp nhận "
            "khiếu nại của Nhà Bán phát sinh sau thời hạn này. Riêng mô hình NGON là "
            "tối đa 04 giờ làm việc."
        ),
        "evidence": "02 ngày làm việc",
        "filter": {"customer_role": "seller"},
    },
    {
        "text": "Thời gian bảo hành mà Nhà Bán được cam kết tối đa là bao lâu, và tính từ lúc nào?",
        "gold": (
            "Tối đa không quá 30 ngày, tính từ thời điểm Nhà Bán nhận được hàng đến khi "
            "bảo hành xong, không tính thời gian vận chuyển."
        ),
        "evidence": "tối đa không quá 30 ngày",
        "filter": None,
    },
    {
        "text": "Những loại hàng hóa nào Nhà Bán không được đăng bán trên sàn Tiki?",
        "gold": (
            "Vũ khí, chất nổ, pháo, hóa chất độc hại; thuốc lá điếu và xì gà; văn hóa "
            "phẩm đồi trụy/phản động; động thực vật hoang dã quý hiếm; ma túy và chất "
            "gây nghiện; đồ chơi nguy hiểm. Ngoài ra Tiki không hỗ trợ bán hàng cũ, đã "
            "qua sử dụng, like new, second hand."
        ),
        "evidence": "hàng cũ, đã qua sử dụng, like new, hàng second hand",
        "filter": {"customer_role": "seller"},
    },
    {
        "text": "Người tiêu dùng nên làm gì để phòng tránh rủi ro khi mua sắm trực tuyến?",
        "gold": (
            "Mua tại sàn TMĐT uy tín, được cấp phép, có thông tin liên lạc rõ ràng; "
            "chọn nhà bán có uy tín cao và đánh giá tích cực; tìm hiểu kỹ điều kiện "
            "giao dịch về bảo hành, trả lại hàng, hoàn tiền, giao nhận; tìm hiểu kỹ "
            "sản phẩm; cảnh giác với trang web lạ đòi cung cấp thông tin cá nhân hoặc "
            "đặt cọc trước."
        ),
        "evidence": "sàn giao dịch thương mại điện tử uy tín",
        "filter": {"customer_role": "buyer"},
    },
    {
        "text": "Theo Nghị định 85/2021/NĐ-CP, sàn TMĐT có trách nhiệm gì trong việc giải quyết khiếu nại của người tiêu dùng?",
        "gold": (
            "Chỉ định đầu mối tiếp nhận yêu cầu và cung cấp thông tin trực tuyến cho cơ "
            "quan quản lý nhà nước trong vòng 24 giờ; đại diện cho người bán nước ngoài "
            "trên sàn giải quyết khiếu nại của NTD; là đầu mối tiếp nhận và giải quyết "
            "khiếu nại khi một giao dịch trên sàn có nhiều hơn 02 bên tham gia."
        ),
        "evidence": "nhiều hơn 02 bên tham gia",
        "filter": None,
    },
]
