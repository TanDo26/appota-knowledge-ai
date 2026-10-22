# Bộ kiểm thử Mission 2 (hồi quy) — chế độ `gemini`

Chạy lúc 2026-10-20 20:14 · code `d40d1df-dirty` · ngày tra cứu mặc định 2026-10-15

## Tổng hợp

- Lượt chạy đạt: **13/13** · case đạt (mọi lượt của case): **11/11** · đổi kỳ vọng có chủ đích: 1 lượt
- Đúng trạng thái: 13/13 · nguồn kỳ vọng nằm trong nguồn trích: 10/10
- Từ chối đúng: 2/2 · từ chối nhầm: 0
- Ma trận rò rỉ: **0 rò rỉ** trên 96 lượt (6 persona × 16 câu hỏi)
- Câu trả lời do Gemini viết: 10 · rơi về trích nguyên văn: 0
- Theo loại: Bắt buộc 2/2 · Tốt 1/1 · Phiên bản 1/1 · Phân quyền 2/2 · Mâu thuẫn 1/1 · Khó 2/2 · Từ chối 1/1 · Có thể thất bại 2/2 · Chế độ Gemini 1/1

## Từng lượt chạy

| Case | Loại | Persona | Câu hỏi | Kỳ vọng | Thực tế | Nguồn trích | Kết quả |
|---|---|---|---|---|---|---|---|
| TC01 | Bắt buộc | linh | Quy định nghỉ phép của tôi như thế nào? | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | A-LEAVE-01@3#1 | Đạt |
| TC01 | Bắt buộc | minh | Quy định nghỉ phép của tôi như thế nào? | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | B-INT-01@2#2 | Đạt |
| TC02 | Tốt | linh | toi duoc nghi phep bao nhieu ngay | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | A-LEAVE-01@3#1 | Đạt |
| TC03 | Phiên bản | linh | Tôi được làm việc từ xa mấy ngày một tuần? | ANSWERED_WITH_NOTE | ANSWERED_WITH_NOTE | GRP-REM-01@2#1 | Đạt |
| TC04 | Phân quyền | minh | Khung lương kỹ sư Công ty A là bao nhiêu? | ABSTAIN | ABSTAIN | — | Đạt |
| TC04 | Phân quyền | tuan | Khung lương kỹ sư Công ty A là bao nhiêu? | ANSWERED | ANSWERED | A-SAL-01@1#1 | Đạt |
| TC05 | Mâu thuẫn | linh | Phép năm chưa dùng có được chuyển sang năm sau không? | ANSWERED_WITH_NOTE | ANSWERED_WITH_NOTE | A-LEAVE-01@3#2 | Đạt |
| TC06 | Khó | linh | Hạn nộp hồ sơ hoàn ứng là bao lâu? | CONFLICT | CONFLICT | A-EXP-01@2#2, A-EXP-02@1#2 | Đạt |
| TC07 | Từ chối | linh | Công ty có hỗ trợ học phí MBA không? | ABSTAIN | ABSTAIN | — | Đạt |
| TC08 | Khó | linh | Tôi còn bao nhiêu ngày phép? | OUT_OF_SCOPE | OUT_OF_SCOPE | A-LEAVE-01@3#1 | Đạt |
| TC09 | Có thể thất bại | nam | Tôi đang thử việc thì có được nghỉ phép không? | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | B-LEAVE-01@1#4 | Đạt |
| TC10 | Có thể thất bại | linh | Muốn làm ở nhà vài hôm thì có được không? | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED_WITH_NOTE | GRP-REM-01@2#1 | Đạt |
| TC11 | Dữ liệu không rõ | hoa | Phụ cấp trực on-call của nhóm Platform là bao nhiêu? | ABSTAIN | ANSWERED | A-PLT-01@1#1 | Đổi kỳ vọng có chủ đích → M3-06 — được xem thì được tra cứu, ghi rõ không áp dụng cho người hỏi (kỳ vọng cũ không còn đúng) |
| TC12 | Chế độ Gemini | linh | Hệ thống chấm công mới dùng thế nào? | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | GRP-ANN-01@1#1, GRP-ANN-01@1#2 | Đạt |

## Ma trận rò rỉ

Không phát hiện ID tài liệu giới hạn hay canary token nào trong bất kỳ trường công khai nào (context, nguồn trích, câu trả lời, ghi chú, cờ, đầu mối, trace, ngữ cảnh truy vấn, nguồn đã xem xét, lịch sử phiên bản, gợi ý) của persona không có quyền.

## Chi tiết

### TC01 · linh — Đạt

**Câu hỏi:** Quy định nghỉ phép của tôi như thế nào?  
**Trạng thái:** ANSWERED · **chủ đề:** leave.annual_days · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: leave.annual_days 8.87 > leave.unpaid 4.69 > leave.carry_over 4.13 > leave.request 3.91.
- R3 Loại tài liệu: policy được ưu tiên, bỏ A-FAQ-01@1#1.
- R4 Cấp tổ chức: CO_A thắng (cấp cha chỉ đặt mức sàn), bỏ GRP-HR-01@2#2.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

Nhân sự chính thức được 14 ngày phép năm hưởng nguyên lương; cứ đủ 5 năm thâm niên được cộng thêm 1 ngày [S1].

### TC01 · minh — Đạt

**Câu hỏi:** Quy định nghỉ phép của tôi như thế nào?  
**Trạng thái:** ANSWERED · **chủ đề:** leave.annual_days · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 3: leave.annual_days 7.61.
- Chỉ có 1 nguồn, không cần phân xử.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

Theo quy định dành cho thực tập sinh, bạn không có ngày phép năm hưởng lương [S1].

### TC02 · linh — Đạt

**Câu hỏi:** toi duoc nghi phep bao nhieu ngay  
**Trạng thái:** ANSWERED · **chủ đề:** leave.annual_days · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: leave.annual_days 9.98 > leave.unpaid 5.07 > leave.carry_over 4.64 > leave.request 4.41.
- R3 Loại tài liệu: policy được ưu tiên, bỏ A-FAQ-01@1#1.
- R4 Cấp tổ chức: CO_A thắng (cấp cha chỉ đặt mức sàn), bỏ GRP-HR-01@2#2.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

Bạn là nhân viên chính thức có thâm niên 6 năm, bạn được 14 ngày phép năm hưởng nguyên lương và được cộng thêm 1 ngày do có đủ 5 năm thâm niên [S1].

### TC03 · linh — Đạt

**Câu hỏi:** Tôi được làm việc từ xa mấy ngày một tuần?  
**Trạng thái:** ANSWERED_WITH_NOTE · **chủ đề:** remote.days_per_week · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: remote.days_per_week 23.31 > remote.request 19.87.
- Chỉ có 1 nguồn, không cần phân xử.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

Bạn được làm việc từ xa tối đa 2 ngày mỗi tuần khi quản lý trực tiếp đồng ý, nhưng lưu ý không làm việc từ xa vào thứ Hai vì có họp giao ban [S1].

**Ghi chú:**

- Sắp thay đổi: từ 01/01/2027, Chính sách làm việc từ xa phiên bản 3 có hiệu lực và quy định: “Nhân sự được làm việc từ xa tối đa 3 ngày mỗi tuần khi quản lý trực tiếp đồng ý. Không làm việc từ xa vào thứ Hai vì có họp giao ban.”

### TC04 · minh — Đạt

**Câu hỏi:** Khung lương kỹ sư Công ty A là bao nhiêu?  
**Trạng thái:** ABSTAIN · **chủ đề:** None · **độ phủ:** 0.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** Phòng Nhân sự Công ty B (hr.b@example.com) · **chế độ trả lời:** extractive

**Resolver / trace:**

- Câu hỏi về đơn vị thuộc công ty khác: không tra cứu.

**Câu trả lời:**

Mình chưa tìm thấy quy định nào trả lời được câu hỏi này trong các tài liệu áp dụng cho bạn, nên không đưa ra câu trả lời để tránh sai.

### TC04 · tuan — Đạt

**Câu hỏi:** Khung lương kỹ sư Công ty A là bao nhiêu?  
**Trạng thái:** ANSWERED · **chủ đề:** salary.band · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: salary.band 17.80.
- Chỉ có 1 nguồn, không cần phân xử.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

Khung lương khối Kỹ thuật được quy định như sau: Kỹ sư bậc 1 từ 18.000.000 đến 25.000.000 đồng/tháng, Kỹ sư bậc 2 từ 25.000.000 đến 38.000.000 đồng/tháng, và Kỹ sư bậc 3 (Senior) từ 38.000.000 đến 55.000.000 đồng/tháng [S1].

### TC05 · linh — Đạt

**Câu hỏi:** Phép năm chưa dùng có được chuyển sang năm sau không?  
**Trạng thái:** ANSWERED_WITH_NOTE · **chủ đề:** leave.carry_over · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: leave.carry_over 65.28.
- R3 Loại tài liệu: policy được ưu tiên, bỏ A-FAQ-01@1#2.
- R3 Lệch: A-FAQ-01@1#2 ghi 5, khác nguồn thắng → gắn cờ cho chủ sở hữu.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

Số ngày phép năm chưa sử dụng của bạn được chuyển sang năm sau tối đa 3 ngày và phải sử dụng hết trước ngày 31/03 [S1].

**Ghi chú:**

- FAQ Nhân sự Công ty A (A-FAQ-01@1) ghi khác: “Được. Bạn được chuyển tối đa 5 ngày phép chưa dùng sang năm sau và cần dùng hết trước ngày 31/03.”. Câu trả lời theo nguồn có thứ bậc cao hơn; đã gắn cờ để Nhân sự Công ty A cập nhật.

### TC06 · linh — Đạt

**Câu hỏi:** Hạn nộp hồ sơ hoàn ứng là bao lâu?  
**Trạng thái:** CONFLICT · **chủ đề:** expense.claim_deadline · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** Phòng Hành chính Công ty A (admin.a@example.com), Phòng Tài chính Công ty A (finance.a@example.com) · **chế độ trả lời:** extractive

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: expense.claim_deadline 40.84.
- R5 Mâu thuẫn: tài liệu cùng cấp, cùng loại nhưng khác số liệu (A-EXP-01@2: 30; A-EXP-02@1: 15). Không tự chọn.

**Câu trả lời:**

Các tài liệu đang hiệu lực nói khác nhau về vấn đề này. Hệ thống **không tự chọn** bên nào:

[S1] Quy trình hoàn ứng chi phí — phiên bản 2, mục 2. Thời hạn nộp hồ sơ, hiệu lực từ 01/03/2026
> Hồ sơ hoàn ứng cho mọi khoản chi, kể cả chi phí công tác, phải nộp trong vòng 30 ngày kể từ ngày phát sinh chi phí. Hồ sơ nộp muộn cần Giám đốc tài chính phê duyệt ngoại lệ.

[S2] Quy trình công tác phí — phiên bản 1, mục 2. Thời hạn thanh toán, hiệu lực từ 01/06/2025
> Hồ sơ hoàn ứng chi phí công tác (vé máy bay, khách sạn, phụ cấp lưu trú) phải nộp trong vòng 15 ngày kể từ ngày kết thúc chuyến công tác.

Lý do: Các tài liệu cùng cấp, cùng loại nhưng ghi số liệu khác nhau; không có luật nào để chọn một bên.

Đã báo mâu thuẫn cho chủ sở hữu tài liệu: Phòng Hành chính Công ty A, Phòng Tài chính Công ty A. Trong lúc chờ, bạn nên hỏi trực tiếp các đơn vị này trước khi làm theo.

### TC07 · linh — Đạt

**Câu hỏi:** Công ty có hỗ trợ học phí MBA không?  
**Trạng thái:** ABSTAIN · **chủ đề:** None · **độ phủ:** 0.104 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** Phòng Nhân sự Công ty A (hr.a@example.com) · **chế độ trả lời:** extractive

**Resolver / trace:**

- Độ phủ câu hỏi 0.10 < ngưỡng 0.59: không có mục đủ liên quan.

**Câu trả lời:**

Mình chưa tìm thấy quy định nào trả lời được câu hỏi này trong các tài liệu áp dụng cho bạn, nên không đưa ra câu trả lời để tránh sai.

### TC08 · linh — Đạt

**Câu hỏi:** Tôi còn bao nhiêu ngày phép?  
**Trạng thái:** OUT_OF_SCOPE · **chủ đề:** leave.annual_days · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** Phòng Nhân sự Công ty A (hr.a@example.com) · **chế độ trả lời:** extractive

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: leave.annual_days 12.72 > leave.carry_over 8.03.
- R3 Loại tài liệu: policy được ưu tiên, bỏ A-FAQ-01@1#1.
- R4 Cấp tổ chức: CO_A thắng (cấp cha chỉ đặt mức sàn), bỏ GRP-HR-01@2#2.

**Câu trả lời:**

Đây là thông tin cá nhân của bạn, không có trong kho tài liệu nên mình không đưa ra con số. Bạn xem trên Cổng nhân sự HRM (https://hrm.example.com). Xem mục "Ngày phép của tôi" hoặc "Phiếu lương của tôi" sau khi đăng nhập.

**Quy định áp dụng cho bạn:**

[S1] Chính sách nghỉ phép Công ty A — phiên bản 3, mục 1. Số ngày phép năm, hiệu lực từ 01/01/2026
> Nhân sự chính thức được 14 ngày phép năm hưởng nguyên lương; cứ đủ 5 năm thâm niên được cộng thêm 1 ngày.

### TC09 · nam — Đạt

**Câu hỏi:** Tôi đang thử việc thì có được nghỉ phép không?  
**Trạng thái:** ANSWERED · **chủ đề:** leave.annual_days · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: leave.annual_days 9.25 > leave.request 5.28.
- R2 Đối tượng: B-LEAVE-01@1 có mục riêng cho Thử việc (B-LEAVE-01@1#4), bỏ mục chung B-LEAVE-01@1#1.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

Trong thời gian thử việc, bạn chưa được hưởng phép năm. Tuy nhiên, khi có việc riêng, bạn được nghỉ không lương tối đa 3 ngày và phải báo trước cho quản lý trực tiếp [S1].

### TC10 · linh — Đạt

**Câu hỏi:** Muốn làm ở nhà vài hôm thì có được không?  
**Trạng thái:** ANSWERED_WITH_NOTE · **chủ đề:** remote.days_per_week · **độ phủ:** 0.744 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: remote.days_per_week 21.38 > remote.request 18.36.
- Chỉ có 1 nguồn, không cần phân xử.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

Bạn được làm việc từ xa tối đa 2 ngày mỗi tuần khi quản lý trực tiếp đồng ý, nhưng lưu ý không làm việc từ xa vào thứ Hai vì có họp giao ban [S1].

**Ghi chú:**

- Sắp thay đổi: từ 01/01/2027, Chính sách làm việc từ xa phiên bản 3 có hiệu lực và quy định: “Nhân sự được làm việc từ xa tối đa 3 ngày mỗi tuần khi quản lý trực tiếp đồng ý. Không làm việc từ xa vào thứ Hai vì có họp giao ban.”

### TC11 · hoa — Đổi kỳ vọng có chủ đích → M3-06 — được xem thì được tra cứu, ghi rõ không áp dụng cho người hỏi (kỳ vọng cũ không còn đúng)

**Câu hỏi:** Phụ cấp trực on-call của nhóm Platform là bao nhiêu?  
**Trạng thái:** ANSWERED · **chủ đề:** oncall.allowance · **độ phủ:** 1.0 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: oncall.allowance 31.70 > oncall.compensatory 18.61.
- Chỉ có 1 nguồn, không cần phân xử.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

_Đây là quy định cho đơn vị Công ty A › Kỹ thuật › Platform — không áp dụng cho bạn (Công ty A › Kỹ thuật). Chỉ gồm tài liệu bạn được quyền xem._

Theo quy định dành cho đơn vị Công ty A › Kỹ thuật › Platform (không áp dụng cho bạn), thành viên nhóm Platform được phụ cấp 300.000 đồng cho mỗi ngày trực on-call ngày thường và 600.000 đồng cho mỗi ngày trực cuối tuần hoặc ngày lễ [S1].

**Chưa đạt vì:**

- trạng thái ANSWERED, kỳ vọng ABSTAIN
- trích nguồn không được phép A-PLT-01@1

### TC12 · linh — Đạt

**Câu hỏi:** Hệ thống chấm công mới dùng thế nào?  
**Trạng thái:** ANSWERED · **chủ đề:** attendance.system · **độ phủ:** 0.754 · **tính theo ngày:** 2026-10-15  
**Đầu mối:** — · **chế độ trả lời:** gemini

**Resolver / trace:**

- Chọn chủ đề theo tổng điểm các mục liên quan trong top 5: attendance.system 46.75.
- Model gemini-3.5-flash-lite · hậu kiểm đạt: nguồn trích hợp lệ, mọi con số có trong nguồn hoặc hồ sơ

**Câu trả lời:**

Bạn đăng nhập bằng tài khoản email công ty trên ứng dụng chấm công ChamCong Go (được cài từ cổng phần mềm nội bộ). Khi đến, bạn bấm "Check-in" và khi về bấm "Check-out" trên ứng dụng trong lúc điện thoại đang kết nối wifi văn phòng [S1, S2]. Nếu quên chấm công, bạn cần gửi giải trình trên ứng dụng trong vòng 3 ngày làm việc, quá hạn sẽ tính là nghỉ không phép [S2].

