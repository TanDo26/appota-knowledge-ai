# Hiệu chỉnh ngưỡng ABSTAIN

Bộ câu hỏi: `eval/calibration.yaml` (18 câu, tách riêng khỏi bộ kiểm thử).

| Persona | Câu hỏi | Trả lời được? | Độ phủ mục đầu | Mục đầu | Đúng tài liệu? | Căn cứ mỏng? | Quyết định (M3) |
|---|---|---|---|---|---|---|---|
| linh | Công ty có hỗ trợ tiền gửi xe không? | không | 0.060 | A-EXP-01@2#2 | — | có | ABSTAIN |
| nam | Mức thưởng Tết năm nay là bao nhiêu? | không | 0.063 | B-LEAVE-01@1#1 | — | có | ABSTAIN |
| minh | Bảo hiểm sức khỏe có chi trả cho người thân không? | không | 0.087 | B-MKT-01@1#1 | — | có | ABSTAIN |
| hoa | Ngân sách team building năm nay là bao nhiêu? | không | 0.088 | A-LEAVE-01@3#1 | — | có | ABSTAIN |
| tuan | Quy trình tuyển dụng gồm mấy vòng phỏng vấn? | không | 0.156 | A-LEAVE-01@3#2 | — | không | ABSTAIN |
| linh | Công ty có xe đưa đón nhân viên không? | không | 0.182 | GRP-HR-01@2#3 | — | không | ABSTAIN |
| nam | Có được mang thú cưng đến văn phòng không? | không | 0.385 | B-REM-01@1#2 | — | không | ABSTAIN |
| linh | Hồ sơ hoàn ứng cần những giấy tờ gì? | có | 0.493 | A-EXP-01@2#2 | có | không | ABSTAIN |
| minh | Thực tập sinh có được cấp laptop không? | không | 0.509 | B-INT-01@2#4 | — | không | ABSTAIN |
| minh | Nội dung quảng cáo phải qua mấy bước duyệt? | có | 0.671 | B-MKT-01@1#1 | có | không | ANSWERED |
| tuan | Đăng ký nghỉ phép trước mấy ngày? | có | 0.688 | A-LEAVE-01@3#3 | có | không | ANSWERED |
| linh | Có được chia sẻ mã nguồn ra ngoài không? | có | 0.768 | GRP-HR-01@2#3 | có | không | ANSWERED |
| linh | Phụ cấp lưu trú khi đi công tác trong nước là bao nhiêu? | có | 0.803 | A-EXP-02@1#1 | có | không | ANSWERED |
| linh | Giờ làm việc tiêu chuẩn mỗi tuần là bao nhiêu giờ? | có | 0.856 | GRP-HR-01@2#1 | có | không | ANSWERED |
| hoa | Lịch đánh giá hiệu suất giữa năm vào tháng mấy? | có | 0.907 | A-ENG-02@1#2 | có | không | ANSWERED |
| hoa | Sự cố P1 phải phản hồi trong bao lâu? | có | 1.000 | A-ENG-01@1#2 | có | không | ANSWERED |
| minh | Thực tập sinh được phụ cấp bao nhiêu mỗi tháng? | có | 1.000 | B-INT-01@2#4 | có | không | ANSWERED |
| nam | Phòng Sản xuất game có được làm việc từ xa không? | có | 1.000 | B-REM-01@1#1 | có | không | ANSWERED |

**Ngưỡng đề xuất: 0.59** (phân loại đúng 17/18 câu).

Pipeline Mission 3 (ngưỡng + luật căn cứ mỏng): quyết định đúng 17/18 câu; luật căn cứ mỏng đổi quyết định của 0 câu.
