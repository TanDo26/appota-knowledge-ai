# Hiệu chỉnh ngưỡng ABSTAIN

Bộ câu hỏi: `eval/calibration.yaml` (18 câu, tách riêng khỏi bộ kiểm thử).

| Persona | Câu hỏi | Trả lời được? | Độ phủ mục đầu | Mục đầu | Đúng tài liệu? |
|---|---|---|---|---|---|
| linh | Công ty có hỗ trợ tiền gửi xe không? | không | 0.060 | A-EXP-01@2#2 | — |
| nam | Mức thưởng Tết năm nay là bao nhiêu? | không | 0.063 | B-LEAVE-01@1#1 | — |
| minh | Bảo hiểm sức khỏe có chi trả cho người thân không? | không | 0.087 | B-MKT-01@1#1 | — |
| hoa | Ngân sách team building năm nay là bao nhiêu? | không | 0.088 | A-LEAVE-01@3#1 | — |
| tuan | Quy trình tuyển dụng gồm mấy vòng phỏng vấn? | không | 0.156 | A-LEAVE-01@3#2 | — |
| linh | Công ty có xe đưa đón nhân viên không? | không | 0.181 | GRP-HR-01@2#3 | — |
| nam | Có được mang thú cưng đến văn phòng không? | không | 0.385 | B-REM-01@1#2 | — |
| linh | Hồ sơ hoàn ứng cần những giấy tờ gì? | có | 0.492 | A-EXP-01@2#2 | có |
| minh | Thực tập sinh có được cấp laptop không? | không | 0.509 | B-INT-01@2#4 | — |
| minh | Nội dung quảng cáo phải qua mấy bước duyệt? | có | 0.671 | B-MKT-01@1#1 | có |
| tuan | Đăng ký nghỉ phép trước mấy ngày? | có | 0.688 | A-LEAVE-01@3#3 | có |
| linh | Có được chia sẻ mã nguồn ra ngoài không? | có | 0.770 | GRP-HR-01@2#3 | có |
| linh | Phụ cấp lưu trú khi đi công tác trong nước là bao nhiêu? | có | 0.802 | A-EXP-02@1#1 | có |
| linh | Giờ làm việc tiêu chuẩn mỗi tuần là bao nhiêu giờ? | có | 0.856 | GRP-HR-01@2#1 | có |
| hoa | Lịch đánh giá hiệu suất giữa năm vào tháng mấy? | có | 0.907 | A-ENG-02@1#2 | có |
| hoa | Sự cố P1 phải phản hồi trong bao lâu? | có | 1.000 | A-ENG-01@1#2 | có |
| minh | Thực tập sinh được phụ cấp bao nhiêu mỗi tháng? | có | 1.000 | B-INT-01@2#4 | có |
| nam | Phòng Sản xuất game có được làm việc từ xa không? | có | 1.000 | B-REM-01@1#1 | có |

**Ngưỡng đề xuất: 0.59** (phân loại đúng 17/18 câu).
