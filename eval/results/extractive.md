# Kết quả eval — chế độ `extractive`

Chạy lúc 2026-10-12 20:16 · commit `73740e7` · ngày tra cứu 2026-10-15

## Tổng hợp

- Lượt chạy đạt: **14/14** · case đạt (mọi lượt của case): **12/12**
- Đúng trạng thái: 14/14 · nguồn kỳ vọng nằm trong nguồn trích: 10/10
- Từ chối đúng: 3/3 · từ chối nhầm: 0
- Ma trận rò rỉ: **0 rò rỉ** trên 80 lượt (5 persona × 16 câu hỏi)
- Theo loại: Bắt buộc 2/2 · Tốt 1/1 · Phiên bản 1/1 · Phân quyền 2/2 · Mâu thuẫn 1/1 · Khó 2/2 · Từ chối 1/1 · Có thể thất bại 2/2 · Dữ liệu không rõ 1/1 · Chế độ Gemini 1/1

## Từng lượt chạy

| Case | Loại | Persona | Kỳ vọng | Thực tế | Nguồn trích | Kết quả |
|---|---|---|---|---|---|---|
| TC01 | Bắt buộc | linh | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | A-LEAVE-01@3#4 | Đạt |
| TC01 | Bắt buộc | minh | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | B-INT-01@2#2 | Đạt |
| TC02 | Tốt | linh | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | A-LEAVE-01@3#4 | Đạt |
| TC03 | Phiên bản | linh | ANSWERED_WITH_NOTE | ANSWERED_WITH_NOTE | GRP-REM-01@2#1 | Đạt |
| TC04 | Phân quyền | minh | ABSTAIN | ABSTAIN | — | Đạt |
| TC04 | Phân quyền | tuan | ANSWERED | ANSWERED | A-SAL-01@1#1 | Đạt |
| TC05 | Mâu thuẫn | linh | ANSWERED_WITH_NOTE | ANSWERED_WITH_NOTE | A-LEAVE-01@3#2 | Đạt |
| TC06 | Khó | linh | CONFLICT | CONFLICT | A-EXP-01@2#2, A-EXP-02@1#2 | Đạt |
| TC07 | Từ chối | linh | ABSTAIN | ABSTAIN | — | Đạt |
| TC08 | Khó | linh | OUT_OF_SCOPE | OUT_OF_SCOPE | A-LEAVE-01@3#1 | Đạt |
| TC09 | Có thể thất bại | nam | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | B-LEAVE-01@1#4 | Đạt |
| TC10 | Có thể thất bại | linh | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED_WITH_NOTE | GRP-REM-01@2#1 | Đạt |
| TC11 | Dữ liệu không rõ | hoa | ABSTAIN | ABSTAIN | — | Đạt |
| TC12 | Chế độ Gemini | linh | ANSWERED / ANSWERED_WITH_NOTE | ANSWERED | GRP-ANN-01@1#1, GRP-ANN-01@1#2 | Đạt |

## Ma trận rò rỉ

Không phát hiện ID tài liệu giới hạn hay canary token nào trong context, nguồn trích, câu trả lời, ghi chú, cờ và đầu mối của persona không có quyền.

## Chi tiết

### TC01 · linh — Đạt

**Câu hỏi:** Quy định nghỉ phép của tôi như thế nào?  
**Trạng thái:** ANSWERED · **chủ đề:** leave.unpaid · **độ phủ:** 1.0  
**Đầu mối:** —

**Resolver / trace:**

- Chỉ có 1 nguồn, không cần phân xử.

**Câu trả lời:**

[S1] Chính sách nghỉ phép Công ty A — phiên bản 3, mục 4. Nghỉ không lương, hiệu lực từ 01/01/2026
> Nhân sự được nghỉ không lương tối đa 30 ngày mỗi năm khi quản lý trực tiếp và Phòng Nhân sự cùng phê duyệt.

### TC01 · minh — Đạt

**Câu hỏi:** Quy định nghỉ phép của tôi như thế nào?  
**Trạng thái:** ANSWERED · **chủ đề:** leave.annual_days · **độ phủ:** 1.0  
**Đầu mối:** —

**Resolver / trace:**

- Chỉ có 1 nguồn, không cần phân xử.

**Câu trả lời:**

[S1] Sổ tay thực tập sinh — phiên bản 2, mục 2. Nghỉ phép, hiệu lực từ 01/05/2026
> Thực tập sinh không có ngày phép năm hưởng lương.

### TC02 · linh — Đạt

**Câu hỏi:** toi duoc nghi phep bao nhieu ngay  
**Trạng thái:** ANSWERED · **chủ đề:** leave.unpaid · **độ phủ:** 1.0  
**Đầu mối:** —

**Resolver / trace:**

- Chỉ có 1 nguồn, không cần phân xử.

**Câu trả lời:**

[S1] Chính sách nghỉ phép Công ty A — phiên bản 3, mục 4. Nghỉ không lương, hiệu lực từ 01/01/2026
> Nhân sự được nghỉ không lương tối đa 30 ngày mỗi năm khi quản lý trực tiếp và Phòng Nhân sự cùng phê duyệt.

### TC03 · linh — Đạt

**Câu hỏi:** Tôi được làm việc từ xa mấy ngày một tuần?  
**Trạng thái:** ANSWERED_WITH_NOTE · **chủ đề:** remote.days_per_week · **độ phủ:** 1.0  
**Đầu mối:** —

**Resolver / trace:**

- Chỉ có 1 nguồn, không cần phân xử.

**Câu trả lời:**

[S1] Chính sách làm việc từ xa — phiên bản 2, mục 1. Số ngày làm việc từ xa, hiệu lực từ 01/07/2026
> Nhân sự được làm việc từ xa tối đa 2 ngày mỗi tuần khi quản lý trực tiếp đồng ý. Không làm việc từ xa vào thứ Hai vì có họp giao ban.

**Ghi chú:**

- Sắp thay đổi: từ 01/01/2027, Chính sách làm việc từ xa phiên bản 3 có hiệu lực và quy định: “Nhân sự được làm việc từ xa tối đa 3 ngày mỗi tuần khi quản lý trực tiếp đồng ý. Không làm việc từ xa vào thứ Hai vì có họp giao ban.”

### TC04 · minh — Đạt

**Câu hỏi:** Khung lương kỹ sư Công ty A là bao nhiêu?  
**Trạng thái:** ABSTAIN · **chủ đề:** None · **độ phủ:** 0.18  
**Đầu mối:** Phòng Nhân sự Công ty B (hr.b@example.com)

**Resolver / trace:**

- Độ phủ câu hỏi 0.18 < ngưỡng 0.59: không có mục đủ liên quan.

**Câu trả lời:**

Mình chưa tìm thấy quy định nào trả lời được câu hỏi này trong các tài liệu áp dụng cho bạn, nên không đưa ra câu trả lời để tránh sai.

### TC04 · tuan — Đạt

**Câu hỏi:** Khung lương kỹ sư Công ty A là bao nhiêu?  
**Trạng thái:** ANSWERED · **chủ đề:** salary.band · **độ phủ:** 1.0  
**Đầu mối:** —

**Resolver / trace:**

- Chỉ có 1 nguồn, không cần phân xử.

**Câu trả lời:**

[S1] Khung lương khối Kỹ thuật — phiên bản 1, mục 1. Khung lương kỹ sư, hiệu lực từ 01/01/2026
> Kỹ sư bậc 1: 18.000.000 – 25.000.000 đồng/tháng. Kỹ sư bậc 2: 25.000.000 – 38.000.000 đồng/tháng. Kỹ sư bậc 3 (Senior): 38.000.000 – 55.000.000 đồng/tháng. Mã kiểm soát tài liệu: CANARY-SAL-7Q2X.

### TC05 · linh — Đạt

**Câu hỏi:** Phép năm chưa dùng có được chuyển sang năm sau không?  
**Trạng thái:** ANSWERED_WITH_NOTE · **chủ đề:** leave.carry_over · **độ phủ:** 1.0  
**Đầu mối:** —

**Resolver / trace:**

- R3 Loại tài liệu: policy được ưu tiên, bỏ A-FAQ-01@1#2.
- R3 Lệch: A-FAQ-01@1#2 ghi 5, khác nguồn thắng → gắn cờ cho chủ sở hữu.

**Câu trả lời:**

[S1] Chính sách nghỉ phép Công ty A — phiên bản 3, mục 2. Chuyển phép sang năm sau, hiệu lực từ 01/01/2026
> Số ngày phép năm chưa sử dụng được chuyển sang năm sau tối đa 3 ngày và phải sử dụng hết trước ngày 31/03. Phép chuyển sang quá hạn không được thanh toán thành tiền.

**Ghi chú:**

- FAQ Nhân sự Công ty A (A-FAQ-01@1) ghi khác: “Được. Bạn được chuyển tối đa 5 ngày phép chưa dùng sang năm sau và cần dùng hết trước ngày 31/03.”. Câu trả lời theo nguồn có thứ bậc cao hơn; đã gắn cờ để Nhân sự Công ty A cập nhật.

### TC06 · linh — Đạt

**Câu hỏi:** Hạn nộp hồ sơ hoàn ứng là bao lâu?  
**Trạng thái:** CONFLICT · **chủ đề:** expense.claim_deadline · **độ phủ:** 1.0  
**Đầu mối:** Phòng Hành chính Công ty A (admin.a@example.com), Phòng Tài chính Công ty A (finance.a@example.com)

**Resolver / trace:**

- R5 Mâu thuẫn: tài liệu cùng cấp, cùng loại nhưng khác số liệu (A-EXP-01@2: 30; A-EXP-02@1: 15). Không tự chọn.

**Câu trả lời:**

Các tài liệu đang hiệu lực nói khác nhau về vấn đề này. Hệ thống **không tự chọn** bên nào:

[S1] Quy trình hoàn ứng chi phí — phiên bản 2, mục 2. Thời hạn nộp hồ sơ, hiệu lực từ 01/03/2026
> Hồ sơ hoàn ứng cho mọi khoản chi, kể cả chi phí công tác, phải nộp trong vòng 30 ngày kể từ ngày phát sinh chi phí. Hồ sơ nộp muộn cần Giám đốc tài chính phê duyệt ngoại lệ.

[S2] Quy trình công tác phí — phiên bản 1, mục 2. Thời hạn thanh toán, hiệu lực từ 01/06/2025
> Hồ sơ hoàn ứng chi phí công tác (vé máy bay, khách sạn, phụ cấp lưu trú) phải nộp trong vòng 15 ngày kể từ ngày kết thúc chuyến công tác.

Đã báo mâu thuẫn cho chủ sở hữu tài liệu: Phòng Hành chính Công ty A, Phòng Tài chính Công ty A. Trong lúc chờ, bạn nên hỏi trực tiếp các đơn vị này trước khi làm theo.

### TC07 · linh — Đạt

**Câu hỏi:** Công ty có hỗ trợ học phí MBA không?  
**Trạng thái:** ABSTAIN · **chủ đề:** None · **độ phủ:** 0.103  
**Đầu mối:** Phòng Nhân sự Công ty A (hr.a@example.com)

**Resolver / trace:**

- Độ phủ câu hỏi 0.10 < ngưỡng 0.59: không có mục đủ liên quan.

**Câu trả lời:**

Mình chưa tìm thấy quy định nào trả lời được câu hỏi này trong các tài liệu áp dụng cho bạn, nên không đưa ra câu trả lời để tránh sai.

### TC08 · linh — Đạt

**Câu hỏi:** Tôi còn bao nhiêu ngày phép?  
**Trạng thái:** OUT_OF_SCOPE · **chủ đề:** leave.annual_days · **độ phủ:** 1.0  
**Đầu mối:** Phòng Nhân sự Công ty A (hr.a@example.com)

**Resolver / trace:**

- R3 Loại tài liệu: policy được ưu tiên, bỏ A-FAQ-01@1#1.
- R4 Cấp tổ chức: CO_A thắng (cấp cha chỉ đặt mức sàn), bỏ GRP-HR-01@2#2.

**Câu trả lời:**

Đây là thông tin cá nhân của bạn, không có trong kho tài liệu nên mình không đưa ra con số. Bạn xem trên Cổng nhân sự HRM (https://hrm.example.com). Xem mục "Ngày phép của tôi" hoặc "Phiếu lương của tôi" sau khi đăng nhập.

**Quy định áp dụng cho bạn:**

[S1] Chính sách nghỉ phép Công ty A — phiên bản 3, mục 1. Số ngày phép năm, hiệu lực từ 01/01/2026
> Nhân sự chính thức được 14 ngày phép năm hưởng nguyên lương; cứ đủ 5 năm thâm niên được cộng thêm 1 ngày.

### TC09 · nam — Đạt

**Câu hỏi:** Tôi đang thử việc thì có được nghỉ phép không?  
**Trạng thái:** ANSWERED · **chủ đề:** leave.annual_days · **độ phủ:** 1.0  
**Đầu mối:** —

**Resolver / trace:**

- R2 Đối tượng: B-LEAVE-01@1 có mục riêng cho Thử việc (B-LEAVE-01@1#4), bỏ mục chung B-LEAVE-01@1#1.

**Câu trả lời:**

[S1] Chính sách nghỉ phép Công ty B — phiên bản 1, mục 4. Nhân sự thử việc, hiệu lực từ 01/01/2026
> Trong thời gian thử việc, nhân sự chưa được hưởng phép năm. Khi có việc riêng, nhân sự thử việc được nghỉ không lương tối đa 3 ngày và phải báo trước cho quản lý trực tiếp. Phép năm được tính từ ngày ký hợp đồng chính thức.

### TC10 · linh — Đạt

**Câu hỏi:** Muốn làm ở nhà vài hôm thì có được không?  
**Trạng thái:** ANSWERED_WITH_NOTE · **chủ đề:** remote.days_per_week · **độ phủ:** 0.741  
**Đầu mối:** —

**Resolver / trace:**

- Chỉ có 1 nguồn, không cần phân xử.

**Câu trả lời:**

[S1] Chính sách làm việc từ xa — phiên bản 2, mục 1. Số ngày làm việc từ xa, hiệu lực từ 01/07/2026
> Nhân sự được làm việc từ xa tối đa 2 ngày mỗi tuần khi quản lý trực tiếp đồng ý. Không làm việc từ xa vào thứ Hai vì có họp giao ban.

**Ghi chú:**

- Sắp thay đổi: từ 01/01/2027, Chính sách làm việc từ xa phiên bản 3 có hiệu lực và quy định: “Nhân sự được làm việc từ xa tối đa 3 ngày mỗi tuần khi quản lý trực tiếp đồng ý. Không làm việc từ xa vào thứ Hai vì có họp giao ban.”

### TC11 · hoa — Đạt

**Câu hỏi:** Phụ cấp trực on-call của nhóm Platform là bao nhiêu?  
**Trạng thái:** ABSTAIN · **chủ đề:** None · **độ phủ:** 0.381  
**Đầu mối:** Văn phòng Phòng Kỹ thuật Công ty A (eng.a@example.com)

**Resolver / trace:**

- Độ phủ câu hỏi 0.38 < ngưỡng 0.59: không có mục đủ liên quan.

**Câu trả lời:**

Mình chưa tìm thấy quy định nào trả lời được câu hỏi này trong các tài liệu áp dụng cho bạn, nên không đưa ra câu trả lời để tránh sai.

### TC12 · linh — Đạt

**Câu hỏi:** Hệ thống chấm công mới dùng thế nào?  
**Trạng thái:** ANSWERED · **chủ đề:** attendance.system · **độ phủ:** 0.757  
**Đầu mối:** —

**Resolver / trace:**


**Câu trả lời:**

[S1] Thông báo hệ thống chấm công mới — phiên bản 1, mục 1. Thay đổi hệ thống chấm công, hiệu lực từ 01/10/2026
> Từ ngày 01/11/2026, toàn Tập đoàn chuyển từ máy chấm công vân tay sang ứng dụng chấm công ChamCong Go (tên giả lập). Nhân sự cài ứng dụng từ cổng phần mềm nội bộ và đăng nhập bằng tài khoản email công ty.

[S2] Thông báo hệ thống chấm công mới — phiên bản 1, mục 2. Cách chấm công trên ứng dụng, hiệu lực từ 01/10/2026
> Bấm "Check-in" khi đến và "Check-out" khi về trên ứng dụng, trong lúc điện thoại đang kết nối wifi văn phòng. Quên chấm công thì gửi giải trình trên ứng dụng trong vòng 3 ngày làm việc; quá hạn sẽ tính là nghỉ không phép.

