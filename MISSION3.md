# Mission 3 — Cải tiến

> Toàn bộ tổ chức, người, tài liệu và số liệu đều là **giả lập**.

Tiếp tục trên sản phẩm Mission 2 (commit `d40d1df`), không làm lại. Quyết định và lý do nằm ngay trong báo cáo này (mục 2.3 và 4). Bảng trước/sau sinh tự động: [`eval/results/m3/before_after.md`](eval/results/m3/before_after.md).

**Change Request:** B2 — Khác quyền truy cập (nhận 22/10/2026), xem [mục 4](#4-change-request-b2--khác-quyền-truy-cập).

---

## 1. Tóm tắt

Mission 2 trả lời đúng cho đúng người — nhưng chỉ khi câu hỏi là *"quy định nào áp dụng cho tôi, hôm nay"*. Chạy thử theo 5 yêu cầu mới cho thấy mọi câu hỏi lệch khỏi khuôn đó đều hỏng: hỏi về năm 2025 thì bị từ chối, đặt ngày tra cứu về 2025 thì trả **sai số**, trưởng phòng hỏi về nhóm con hay HR hỏi về nhân sự thử việc đều bị từ chối.

Thay đổi lớn nhất của Mission 3 là **tách ba thứ trước đây bị gộp vào "người hỏi"**:

| | Quyết định | Lấy từ |
|---|---|---|
| **Ai hỏi** | quyền xem (ACL) | hồ sơ người hỏi — không bao giờ đổi |
| **Hỏi về ai** | phạm vi đơn vị, loại hợp đồng | câu hỏi nếu nêu rõ, mặc định là người hỏi |
| **Hỏi về lúc nào** | phiên bản có hiệu lực | câu hỏi nếu nêu năm/ngày, mặc định là ngày tra cứu |

Kèm ba thay đổi nhỏ hơn: hỏi lại khi căn cứ chỉ là vài âm tiết khớp ngẫu nhiên; báo mâu thuẫn khi cấp dưới thấp hơn mức sàn cấp trên; cho người dùng xem nguyên văn, lịch sử phiên bản và nguồn bị loại.

**Kết quả** (cùng dữ liệu, cùng bộ kiểm, chỉ khác code): phần cải tiến R1–R5 **11/25 → 25/25** lượt đạt (tính riêng hành vi: 15/25 → 25/25); bộ Mission 2 không hồi quy (13/13, 12/14 câu trả lời giống từng byte); **0 rò rỉ** trên 186 lượt.

**Change Request B2** (mục 4): người không có quyền nhận đúng phần mình được xem, và mọi thứ họ thấy **giống hệt khi tài liệu mật không tồn tại** — 0 khác biệt trên 465 lượt kiểm. Đóng thêm một kênh lộ mà dữ liệu chưa chạm tới, và chuyển rủi ro còn lại sang chủ sở hữu tài liệu qua linter. CR-01 đạt 3/4; lượt chưa đạt được giữ nguyên và giải thích.

---

## 2. Before → After

### 2.1 M2 — trước cải tiến

Pipeline: persona → lọc cứng (quyền, phạm vi, đối tượng, trạng thái, cửa sổ hiệu lực) → BM25 trên phần còn lại → resolver theo luật → trả lời (Gemini có hậu kiểm, hoặc trích nguyên văn). 12 case, 14/14 lượt đạt, 0 rò rỉ / 80 lượt.

### 2.2 Vấn đề / yêu cầu mới — M2 hỏng ở đâu

Trước khi quyết định, mình viết câu hỏi theo đúng 5 yêu cầu và chạy trên code M2:

| Yêu cầu | Chỗ hỏng thật (chạy trên code M2) |
|---|---|
| **R1** Phiên bản & thời điểm | "Năm 2025 tôi được bao nhiêu ngày phép?" → **từ chối** ("2025" bị coi là từ lạ, độ phủ 0.35). Đặt ngày tra cứu 01/06/2025 → trả **mức sàn Tập đoàn 12 ngày**, sai: năm 2025 Công ty A áp dụng 13 ngày (bản 2, nay đã lưu trữ) — bản `archived` bị loại kể cả với ngày nằm trong cửa sổ hiệu lực của nó. "Tháng 3/2026…làm việc từ xa" → trả 2 ngày của bản hiện hành, tháng 3/2026 thật là 1 ngày |
| **R2** Quyền theo bối cảnh | Trưởng phòng hỏi phụ cấp của nhóm con (TC11), HR hỏi về nhân sự thử việc, thực tập sinh hỏi về nhân sự chính thức → đều **từ chối**, vì lọc theo đơn vị và hợp đồng *của người hỏi* |
| **R3** Mâu thuẫn giữa các cấp | Quy định cấp phòng thấp hơn mức sàn của Tập đoàn: linter có cảnh báo, nhưng câu trả lời vẫn đưa số của cấp phòng, không nói gì |
| **R4** Chưa đủ căn cứ | "Tuần này tôi không lên công ty vài ngày được không?" → trả lời tự tin bằng thủ tục xin nghỉ, chỉ vì "lên" khớp "trở lên". "Con ốm thì tôi được nghỉ chăm con mấy ngày?" → bị coi là hỏi số dư cá nhân ("con mấy" trùng "còn mấy" khi bỏ dấu) |
| **R5** Kiểm chứng nguồn | Ở chế độ Gemini, người dùng không xem được nguyên văn đoạn đã dùng; không thấy nguồn nào bị loại và vì sao; không thấy lịch sử phiên bản |

Lần chạy này được lưu nguyên trạng: [`eval/results/m3/run0_before_core_changes.md`](eval/results/m3/run0_before_core_changes.md) (kỳ vọng đã viết, `core/` chưa sửa).

### 2.3 Quyết định: thay đổi gì, không thay đổi gì

**Thay đổi, theo thứ tự ưu tiên:**

1. **Ngữ cảnh truy vấn** (`core/context.py`, R1 + R2) — gốc chung của phần lớn lỗi ở trên.
   - Năm / ngày / tháng trong câu hỏi dời ngày tính hiệu lực và bị bỏ khỏi truy vấn tìm kiếm (là ngữ cảnh, không phải từ khoá). "Năm Y" = 01/01/Y; năm hiện tại không dời; nhiều mốc khác nhau → không dời, nói rõ.
   - `archived` = "hết hiệu lực", không phải "chưa từng có": dùng được khi ngày tính nằm trong cửa sổ hiệu lực. `draft` không bao giờ dùng.
   - Câu hỏi nêu rõ đơn vị (cách gọi khai báo trong `org.yaml`) hoặc loại hợp đồng khác người hỏi → trả lời quy định của đối tượng đó. **Quyền xem vẫn tính theo người hỏi**, nên tra cứu chỉ có thể thu hẹp, không mở rộng những gì họ thấy.
   - Mọi câu trả lời khác "cho bạn, hôm nay" có dòng đầu nói rõ thời điểm / đối tượng ("… **không áp dụng cho bạn**"). Dòng này do code chèn vào chính câu trả lời, kể cả khi Gemini viết.
   - **Trả lời câu hỏi nghiệp vụ còn mở của TC11:** được xem thì được tra cứu, kèm nhãn. Kỳ vọng cũ của TC11 giữ nguyên trong `cases.yaml`, đánh dấu "đổi có chủ đích".
2. **`CLARIFY` + dòng "Căn cứ"** (R4): mục đầu qua ngưỡng nhưng không khớp cụm từ nào của câu hỏi và không khớp đủ mọi từ → không trả lời, chỉ ra từ đã khớp / chưa khớp và các mục gần nhất ("chưa chắc là câu trả lời"). Mọi câu trả lời đều hiện dòng "Căn cứ".
3. **Dưới mức sàn → `CONFLICT`** (R3): hiện cả hai nguồn, nêu lý do, gắn cờ cả hai chủ sở hữu. Không tự áp mức sàn, vì phép so chỉ dùng con số đầu tiên của mỗi mục.
4. **Kiểm chứng** (R5): mỗi nguồn kèm nguyên văn đã dùng và mã nội dung; danh sách "nguồn đã xem xét nhưng không dùng" kèm lý do; lịch sử phiên bản — chỉ những phiên bản người hỏi được xem.

**Chủ động không làm:**

| Việc | Vì sao |
|---|---|
| Tìm kiếm ngữ nghĩa (embedding) | Sửa được từ chối nhầm ("giấy tờ" ≠ "hồ sơ"), nhưng không nằm trong 5 yêu cầu, buộc hiệu chỉnh lại ngưỡng, và dễ gây hồi quy nhất. Lớp lọc quyền chạy trước tìm kiếm, nên thêm sau không đụng tới phần quyền |
| Tra cứu đơn vị thuộc **công ty khác** | Thực tập sinh Công ty B chỉ xem được tài liệu Tập đoàn; tra cứu "Công ty A" sẽ trình bày mức sàn 12 ngày như thể là quy định Công ty A (thật là 14). Trả lời sai có nhãn còn tệ hơn từ chối |
| Mốc thời gian tương đối ("năm sau", "năm ngoái") | Trong kho này chúng thường là *nội dung* câu hỏi ("phép chuyển sang năm sau") |
| "Hai chủ đề điểm gần nhau → hỏi lại" | Số liệu: ở câu gốc, chủ đề làm việc từ xa chỉ có độ phủ 0.37, nên cách này không bắt được đúng lỗi cần sửa |
| Mâu thuẫn không có con số ("được"/"không được") | Cần LLM/NLI để phán, không kiểm ổn định bằng test; câu trả lời vẫn theo đúng nguồn thứ bậc cao, chỉ thiếu cờ báo chủ sở hữu |
| Cá nhân hoá phép tính (14 + 1 = 15), câu hỏi nhiều chủ đề, SSO | Không thuộc 5 yêu cầu |

### 2.4 M3 — sau cải tiến

```
Người hỏi ─► [1] Ngữ cảnh ─► [2] Lọc cứng ─────────► [3] BM25 ─► [4] Resolver ─► [5] Trả lời + hậu kiểm
             ai hỏi / hỏi     quyền: người hỏi          trên phần    R1…R5 + dưới      ANSWERED · CONFLICT · ABSTAIN
             về ai / lúc nào  phạm vi, đối tượng:        còn lại;     mức sàn           OUT_OF_SCOPE · CLARIFY (mới)
             (code)           đối tượng câu hỏi          căn cứ mỏng  = CONFLICT        + nguyên văn, mã nội dung,
                              hiệu lực: thời điểm hỏi    → CLARIFY                      phiên bản, nguồn bị loại
```

Ví dụ trước → sau (trích nguyên văn, ngày tra cứu 15/10/2026):

| Người hỏi · câu hỏi | M2 | M3 |
|---|---|---|
| Linh · "Năm 2025 tôi được bao nhiêu ngày phép?" | `ABSTAIN` | *Theo các tài liệu có hiệu lực ngày 01/01/2025…* — 13 ngày (bản 2); ghi chú: hôm nay áp dụng bản 3, 14 ngày |
| Linh · ngày tra cứu 01/06/2025 · "Tôi được nghỉ phép bao nhiêu ngày?" | 12 ngày (mức sàn Tập đoàn) — **sai** | 13 ngày (bản 2) |
| Linh · "Năm 2027 tôi được bao nhiêu ngày phép?" | `ABSTAIN` | 14 ngày (bản 3; bản nháp 16 ngày không dùng) + "quy định tại 01/01/2027 vẫn có thể thay đổi" |
| Hoa (trưởng phòng) · "Phụ cấp trực on-call của nhóm Platform là bao nhiêu?" | `ABSTAIN` | *Đây là quy định cho đơn vị … Platform — không áp dụng cho bạn* — 300.000 / 600.000 đồng |
| Hoa · "Số điện thoại trực của nhóm Platform là gì?" (tài liệu chỉ nhóm Platform xem) | `ABSTAIN` | `ABSTAIN` — tra cứu không mở rộng quyền |
| Tuấn (HR) · "Nhân sự thử việc ở Công ty A có được nghỉ phép năm không?" | `ABSTAIN` | mục "Nhân sự thử việc", ghi rõ không áp dụng cho Tuấn |
| Minh (thực tập, Công ty B) · "Nhân viên chính thức Công ty A được mấy ngày phép năm?" | `ABSTAIN` | `ABSTAIN` — chủ động không tra cứu công ty khác |
| Linh · "Tuần này tôi không lên công ty vài ngày được không?" | trả lời tự tin bằng thủ tục xin nghỉ | `CLARIFY`: chỉ khớp “lên”, “ngày”, không có “tuần” → hỏi lại |
| Quân (chính thức, Sản xuất game) · "Tôi được bao nhiêu ngày phép năm?" | 10 ngày, không cảnh báo | `CONFLICT`: 10 ngày của phòng thấp hơn mức sàn 12 ngày của Tập đoàn |

### 2.5 Bằng chứng

**Cùng bộ kiểm, cùng dữ liệu, code M2 vs M3** (`python -m eval.compare`; `core/` của M2 lấy thẳng từ git):

| Bộ kiểm thử | Code | Lượt đạt | Hành vi đúng* | Từ chối nhầm | Rò rỉ | Giao thoa** |
|---|---|---|---|---|---|---|
| Mission 3 (29 lượt = 25 cải tiến + 4 Change Request) | M2 | 13/29 | 18/29 | 7 | 0 / 186 | 0 / 465 |
| Mission 3 (29 lượt = 25 cải tiến + 4 Change Request) | **M3** | **28/29** | **28/29** | 1 | 0 / 186 | 0 / 465 |
| Mission 2 (14 lượt) | M2 | 13/13 + 1 đổi có chủ đích | 13/13 | 0 | 0 / 96 | 0 / 160 |
| Mission 2 (14 lượt) | **M3** | **13/13** + 1 đổi có chủ đích | 13/13 | 0 | 0 / 96 | 0 / 160 |

\* *Hành vi đúng* bỏ qua các kỳ vọng về thông tin Mission 2 vốn không xuất ra (ngày tính, tra cứu cho ai, nguyên văn…), để không tính "thiếu trường" là "trả lời sai".
\*\* *Giao thoa* (thêm cho Change Request, mục 4): số lượt mà một tài liệu mật làm thay đổi bất cứ thứ gì người không được xem nó nhìn thấy.

| Yêu cầu | M2: đạt · hành vi đúng | M3: đạt · hành vi đúng |
|---|---|---|
| R1 Phiên bản & thời điểm | 0/5 · 1/5 | 5/5 · 5/5 |
| R2 Quyền theo bối cảnh | 5/9 · 6/9 | 9/9 · 9/9 |
| R3 Mâu thuẫn giữa các cấp | 1/2 · 1/2 | 2/2 · 2/2 |
| R4 Chưa đủ căn cứ | 5/7 · 5/7 | 7/7 · 7/7 |
| R5 Kiểm chứng nguồn | 0/2 · 2/2 | 2/2 · 2/2 |
| CR B2 Khác quyền truy cập (mục 4) | 2/4 · 3/4 | 3/4 · 3/4 |

Đọc bảng: R5 không đổi *hành vi* — câu trả lời của M2 vốn đúng; cái M3 thêm là *khả năng kiểm chứng* câu trả lời đó. Khác biệt hành vi lớn nhất nằm ở R1 và R2.

Không hồi quy:
- **12/14** câu trả lời của bộ Mission 2 **giống từng byte** với kết quả Mission 2 đã commit. Hai lượt khác: TC06 thêm một dòng "Lý do:" cho mâu thuẫn; TC11 đổi có chủ đích.
- **83** unit test của Mission 2 chạy trên code M3: 81 đạt nguyên trạng, 2 đổi vì số lượng dữ liệu (19→21 tài liệu, 5→6 persona, thêm cảnh báo linter dự kiến). Tổng cộng **118** unit test.
- Hiệu chỉnh ngưỡng (bộ 18 câu riêng): ngưỡng vẫn 0.59, 17/18; luật "căn cứ mỏng" đổi quyết định của **0/18** câu ([`eval/results/m3/calibration.md`](eval/results/m3/calibration.md)).
- **0 rò rỉ / 186 lượt** (174 trước Change Request), với 3 tài liệu mật: 2 của M2 và **A-PLT-02** (danh bạ trực chỉ nhóm Platform xem, có canary) được cài riêng để tấn công tính năng tra cứu. Ma trận kiểm cả các trường mới (ngữ cảnh, nguồn đã xem xét, lịch sử phiên bản, gợi ý của `CLARIFY`).
- **Chế độ Gemini** (`gemini-3.5-flash-lite`, 20/10/2026, [`m3_gemini.md`](eval/results/m3/m3_gemini.md), [`m2_gemini.md`](eval/results/m3/m2_gemini.md)): bộ M3 25/25, bộ M2 13/13 (+ TC11 đổi có chủ đích), 0 rò rỉ ở cả hai (174 và 96 lượt; context gửi Gemini cũng được kiểm). Bộ M3 chạy lại ngày 22/10 cùng Change Request: 28/29, 0 rò rỉ / 186, 0 giao thoa / 465 (mục 4.5). Câu trả lời tra cứu giữ đúng khung "không áp dụng cho bạn"; TC12 vẫn không làm theo chỉ thị nhúng. 3 câu ở bộ M3 rơi về trích nguyên văn, cả 3 vì Gemini tự cộng thâm niên (13 + 1 = 14, 14 + 1 = 15) và hậu kiểm số chặn — giới hạn đã biết từ M2. Đáng chú ý: với câu "năm 2025", con số Gemini tự tính (**14**) trùng đúng số của *phiên bản hiện hành* — chính loại nhầm lẫn khiến M2 quyết định không nới hậu kiểm.

Quy trình: kỳ vọng `cases_m3.yaml` viết trước khi sửa `core/` và đã chạy trên code M2 (lần chạy 0, lưu lại). Mọi câu trả lời của lần chạy cuối được đọc lại bằng mắt — nhờ vậy thấy hai câu ngoài bộ test ở mục 2.6.

### 2.6 Giới hạn còn lại

Theo kết quả chạy, không theo dự đoán:

1. **Bằng chứng cho `CLARIFY` mỏng.** Trong bộ M3 nó chỉ đổi đúng 1 câu (câu gốc từ M2); 4 câu mới không có câu trả lời thì M2 cũng đã từ chối. Luật chỉ bắt khớp *âm tiết rời*; khớp ngẫu nhiên ở mức *cụm từ* vẫn lọt. Câu ngoài bộ test, chạy trên cả hai phiên bản:

   | Câu hỏi | M2 và M3 | Đánh giá |
   |---|---|---|
   | Nam · "Khi nào tôi được ký hợp đồng chính thức?" | trả lời bằng mục nghỉ phép thử việc (khớp cụm "hợp đồng chính thức") | Sai chủ đề, tự tin. Kho không có quy định về thời gian thử việc |
   | Tuấn · "Khung lương khối kỹ thuật là bao nhiêu?" | trích mục *Nguyên tắc xét tăng lương* thay vì *Khung lương kỹ sư* | Sai mục: tiêu đề tài liệu ghép vào mọi mục nên hai mục gần hoà điểm (cùng gốc với lỗi TC02 của M2) |
   | Linh · "Tháng 3/2026 tôi được làm việc từ xa mấy ngày?" | M2: 2 ngày (bản hiện hành) · **M3: 1 ngày** (bản có hiệu lực tháng 3/2026) | M3 đúng |

2. **Hiểu "lúc nào" và "về ai" dựa trên luật.** Năm/ngày tuyệt đối và cách gọi đơn vị khai báo sẵn thì hiểu; "năm sau", "bên game", "team Plat" thì không. "Năm Y" tính tại 01/01/Y nên thay đổi giữa năm của năm được hỏi không được nêu. Ngày/tháng không có năm ("tháng 3") không bị đoán; câu trả lời nói rõ đang tính theo ngày nào (mục 2.7).
3. **Metadata sai → trả lời sai một cách tự tin** (giữ nguyên từ M2). Thêm một chỗ phụ thuộc: cửa sổ hiệu lực của bản lưu trữ phải đúng.
4. **Danh tính là ô chọn persona.** Toàn bộ kiểm soát quyền đúng *với giả định* danh tính đúng.
5. **Từ chối nhầm vì khác từ** ("giấy tờ" / "hồ sơ") chưa sửa — chủ động để lại (mục 2.3).

### 2.7 Sửa thêm sau lần chạy lại ngày 22/10/2026

| Phát hiện | Sửa | Bằng chứng |
|---|---|---|
| Câu hỏi có ngày/tháng nhưng **không có năm** ("Tháng 3 tôi được làm việc từ xa mấy ngày một tuần?") bị bỏ qua mốc thời gian **mà không nói gì**: trả 2 ngày của bản hiện hành, trong khi tháng 3/2026 là 1 ngày | Không đoán năm: hỏi vào tháng 10 thì "tháng 3" có thể là tháng 3 vừa qua hoặc sắp tới, còn "trước 31/03" thường là hạn chót chứ không phải thời điểm hỏi. Câu trả lời giữ ngày tra cứu, và dòng đầu (code chèn, giữ nguyên cả khi Gemini viết) nói rõ: *"Câu hỏi nhắc tới “Tháng 3” nhưng không nêu năm; mình trả lời theo các tài liệu có hiệu lực ngày tra cứu …; hãy ghi rõ năm (ví dụ “tháng 3/2026”)"*. Không nhận "24/7", "1/2 ngày", "6 tháng 1 lần" (`core/context.py`, `core/pipeline.py`) | 3 unit test mới. Không câu nào trong hai bộ kiểm có ngày/tháng thiếu năm, nên mọi câu trả lời của cả hai bộ giữ nguyên từng byte; hiệu chỉnh giữ nguyên |
| Lần chạy Gemini ngày 22/10: câu trả lời của Hoa (M3-06) kết thúc bằng "**[context]**" — Gemini lấy tên thẻ `<context>` trong prompt làm nhãn trích dẫn. Hậu kiểm chỉ kiểm nhãn dạng `[S1]` nên để lọt. Không phải rò rỉ (nội dung thẻ là thông tin người hỏi được thấy), nhưng người dùng thấy một nhãn lạ | Kiểm 1 coi **mọi** nhãn trong ngoặc vuông là trích dẫn ("[S1, S2]" là hai nhãn) và bắt phải là nguồn đã cung cấp; nếu không, câu trả lời rơi về trích nguyên văn (`core/answer.py`) | 2 unit test mới. Chạy lại bộ M3 ở chế độ Gemini sau khi sửa: 28/29, 0 rò rỉ / 186, 0 giao thoa / 465, không còn nhãn lạ nào. Lần này Gemini không viết nhãn lạ nên bản sửa chưa phải ra tay; nó được kiểm bằng unit test |

---

## 3. Bộ kiểm thử Mission 3

Chạy: `python -m eval.run_eval` (bộ M3) · `python -m eval.run_eval --suite m2` (hồi quy) · `python -m eval.compare` (trước/sau) · `pytest`.

| Đề yêu cầu | Đáp ứng |
|---|---|
| Chạy lại test quan trọng của M2 | Toàn bộ 12 case / 14 lượt + ma trận rò rỉ + 83 unit test M2, trên code M3 ([`m2_extractive.md`](eval/results/m3/m2_extractive.md)) |
| ≥ 3 test cho phần cải tiến | 11 case / 25 lượt ([`cases_m3.yaml`](eval/cases_m3.yaml), [`m3_extractive.md`](eval/results/m3/m3_extractive.md)) + 35 unit test mới |
| ≥ 1 test cho Change Request | CR-01 (4 lượt, B2) + ma trận không giao thoa (465 lượt bộ M3, 160 lượt bộ M2) + 7 unit test ([`test_change_request.py`](tests/test_change_request.py)) — mục 4 |
| ≥ 1 edge case / tình huống khó | M3-03 (năm 2027: bản nháp không được lọt), M3-05 (năm không có quy định), M3-08 (tra cứu không mở rộng quyền, tự xưng chức danh), M3-10 Nam (mức sàn chỉ xét đúng đối tượng) |
| ≥ 1 regression test | Bộ M2 đầy đủ; M3-09 (f)(g): câu trả lời được không bị `CLARIFY` chặn nhầm; M3-06 Linh: thành viên nhóm vẫn nhận như cũ |

| Case | YC | Kỳ vọng | Kết quả (M3) | Điều học được |
|---|---|---|---|---|
| M3-01 | R1 | Năm 2025 → bản 2 (13 ngày) + nhắc bản hiện hành | Đạt | Năm trong câu hỏi là ngữ cảnh; để nó làm từ khoá thì hệ thống từ chối |
| M3-02 | R1 | Ngày tra cứu 01/06/2025 → bản 2, không phải mức sàn | Đạt | `archived` phải dùng được trong cửa sổ hiệu lực, nếu không tính năng "đổi ngày tra cứu" của M2 trả sai |
| M3-03 | R1 · edge | Năm 2027 → bản 3, không bản nháp 16 ngày | Đạt | Câu hỏi về tương lai cần cảnh báo "còn có thể thay đổi" |
| M3-04 | R1 | Từ 01/01/2027 → bản 3 + quy định hôm nay | Đạt | — |
| M3-05 | R1 · edge | Năm 2020 → từ chối | Đạt | Không có quy định thì không lấy bản hiện hành thay vào |
| M3-06 | R2 | Hoa tra cứu nhóm con (có nhãn); Linh như cũ; Minh từ chối | Đạt | Thay kỳ vọng TC11 — quyết định nghiệp vụ, ghi ở mục 2.3 |
| M3-07 | R2 | HR hỏi về thử việc; thực tập sinh hỏi về chính thức | Đạt | Viết kỳ vọng này làm lộ một báo động giả: FAQ cho nhân sự chính thức bị gắn cờ "lệch" với mục thử việc — đã sửa |
| M3-08 | R2 · bảo mật | Không tra cứu công ty khác; trưởng phòng không thấy tài liệu chỉ nhóm con xem; tự xưng chức danh vô hiệu | Đạt | Tra cứu thu hẹp, không mở rộng quyền — kiểm bằng canary mới |
| M3-09 | R4 | Câu gốc + 4 câu mới không có câu trả lời: không trả lời tự tin; 2 câu trả lời được: vẫn trả lời | Đạt | Lần chạy 0 bắt được lỗi không dự đoán ("con mấy"/"còn mấy"). Bằng chứng cho luật mới mỏng (mục 2.6) |
| M3-10 | R3 | Quân: `CONFLICT` dưới mức sàn; Nam (thử việc): không ảnh hưởng | Đạt | Mức sàn chỉ áp cho đúng đối tượng nó bảo vệ |
| M3-11 | R5 | Nguyên văn + mã nội dung; FAQ trong "đã xem xét"; bản 2 trong lịch sử | Đạt | Nguyên văn được kiểm khớp từng ký tự với tài liệu |
| CR-01 | CR | Cùng câu hỏi: Tuấn (HR) nhận đầy đủ từ A-SAL-01; Linh nhận phần FAQ mình được xem, giống hệt khi A-SAL-01 không tồn tại | 3/4 — Linh hỏi "bậc 2" bị từ chối chung thay vì nhận lời chỉ dẫn ở FAQ | Lọc quyền từ M2 đã đúng; cái thiếu là phép thử đủ mạnh để chứng minh, và một kênh lộ qua quan hệ thay thế (mục 4) |

---

## 4. Change Request B2 — Khác quyền truy cập

> Hai người dùng hỏi cùng một câu nhưng một người không được phép truy cập tài liệu chứa câu trả lời đầy đủ. (Nhận 22/10/2026.)

### 4.1 Hiểu yêu cầu

Mission 2 đã có trường hợp "một người có quyền, một người không có gì để xem" (TC04: thực tập sinh hỏi khung lương → câu từ chối chung). Điểm mới của B2 nằm ở chữ *đầy đủ*: người không có quyền vẫn xem được **một phần** câu trả lời từ tài liệu khác. Câu hỏi thật là hệ thống được nói gì với người đó.

Dữ liệu cũ không có tình huống này (cả 3 tài liệu mật đều không có tài liệu công khai cùng chủ đề), nên mình thêm [`A-FAQ-02`](data/docs/A-FAQ-02_v1.md), FAQ lương thưởng mà mọi nhân sự Công ty A xem được. Mục 1 nói *khi nào* xét tăng lương (tháng 4) nhưng không nói *tăng tối đa bao nhiêu*; con số 15% chỉ có trong A-SAL-01, tài liệu chỉ Phòng Nhân sự xem. Mục 2 nói khung lương không công bố chung và nên hỏi ai.

### 4.2 Quyết định

| Câu hỏi | Tuấn (HR, xem được A-SAL-01) | Linh (kỹ sư, không xem được) |
|---|---|---|
| "Khi nào được xét tăng lương và mức tăng tối đa là bao nhiêu?" | Đầy đủ: tháng 4, tối đa 15%, không vượt trần của bậc (chính sách thắng FAQ) | Đúng phần Linh được xem: tháng 4, mức tăng do Phòng Nhân sự thông báo riêng |

Nguyên tắc: **mọi thứ Linh thấy phải giống hệt khi A-SAL-01 không tồn tại** — câu trả lời, trạng thái, nguồn, ghi chú, cờ, đầu mối, trace, nguồn đã xem xét, lịch sử phiên bản. Hệ thống không nói "có thông tin đầy đủ hơn mà bạn chưa được xem", vì chính câu đó tiết lộ có một tài liệu mật về chủ đề này. Với khung lương thì vô hại; với "kế hoạch tái cấu trúc" thì không. Đây cũng là lý do M2 dùng một câu từ chối chung cho cả "không có dữ liệu" lẫn "không có quyền".

Nguyên tắc đó để lại hai việc, mỗi việc giao cho người làm được:

- **Người không có quyền cần biết hỏi thêm ở đâu** → chủ sở hữu viết điều đó vào tài liệu họ xem được (A-FAQ-02 mục 2). Tiết lộ hay không là quyết định của chủ sở hữu, không phải điều hệ thống tự suy ra từ tài liệu bị ẩn.
- **Phần được xem có thể *khác* phần bị ẩn** (ví dụ FAQ ghi 10%, chính sách mật ghi 15%) → không cảnh báo được người hỏi mà không làm lộ tài liệu, nên cảnh báo **chủ sở hữu**, lúc xuất bản, bằng linter.

### 4.3 Chẩn đoán trước khi sửa (lần chạy 0)

Dữ liệu và kỳ vọng CR-01 được viết trước, rồi chạy trên code chưa sửa ([`run0_before_cr.md`](eval/results/m3/run0_before_cr.md)):

- **Lọc quyền đã đúng từ M2.** Linh nhận FAQ, không có 15%, tên hay mã của A-SAL-01. Ma trận không giao thoa (mới, mục 4.4) cho **0 khác biệt / 465 lượt**. Lần chạy đầu báo 81 khác biệt, nhưng tất cả do lỗi của chính bộ kiểm: nó so bộ đếm tài liệu bị loại ở những câu dừng trước bước lọc. Mình sửa bộ kiểm, không sửa hệ thống.
- **Một kênh lộ dữ liệu chưa chạm tới**, tìm thấy khi đọc code: một phiên bản bị coi là "đã thay thế" dựa trên *mọi* phiên bản, kể cả bản người hỏi không được xem. Nếu bản v2 mật thay thế bản v1 công khai, người không có quyền mất v1, tức câu trả lời đổi vì một tài liệu họ không thấy. Test dựng đúng tình huống này **chưa đạt** trên code cũ.
- **Linh hỏi "Khung lương kỹ sư bậc 2 là bao nhiêu?" bị từ chối chung** thay vì nhận lời chỉ dẫn ở FAQ mục 2 (độ phủ 0.44 < 0.59, vì FAQ không nhắc "kỹ sư", "bậc 2"). An toàn, đúng đầu mối Phòng Nhân sự Công ty A, nhưng không như kỳ vọng.

### 4.4 Thay đổi

| Thay đổi | Ở đâu | Vì sao |
|---|---|---|
| Chỉ phiên bản người hỏi **được xem** mới loại được phiên bản khác | `core/access.py`, `filter_for` | Đóng kênh lộ ở trên. Người không xem được v2 tiếp tục nhận v1 (có thể đã cũ); đổi lại, linter báo chủ sở hữu |
| Luật linter `visibility_gap` | `core/lint.py`, `_visibility_checks` | Báo khi (a) một nguồn mà người không xem được tài liệu mật vẫn xem được, cùng chủ đề, cùng áp dụng cho họ, ghi con số tài liệu mật không có; (b) bản mới ít người được xem hơn bản nó thay thế. Xét mọi tổ hợp đơn vị × vai trò × loại hợp đồng. Chỉ hiện ở chế độ kiểm định |
| Kỳ vọng `same_as_without` và ma trận **không giao thoa** | `eval/run_eval.py` | Mạnh hơn ma trận rò rỉ (chỉ tìm ID và canary): một con số được diễn đạt lại, một trạng thái khác, một nguồn biến mất cũng làm lộ tài liệu. Với mỗi tài liệu mật × mỗi persona không được xem × mọi câu hỏi: chạy trên kho đầy đủ và trên kho bỏ tài liệu đó, so mọi trường người dùng thấy. Chỉ được khác tổng số tài liệu bị ẩn, và phải giảm đúng số tài liệu đã bỏ |
| Dữ liệu A-FAQ-02, case CR-01 (4 lượt), 7 unit test | `data/`, `eval/cases_m3.yaml`, [`tests/test_change_request.py`](tests/test_change_request.py) | |
| Chỉ số "Giao thoa" trong tab Kiểm thử | `app.py` | |

**Chủ động không làm:**

| Việc | Vì sao |
|---|---|
| Nói với người hỏi "có thông tin đầy đủ hơn, bạn chưa có quyền xem" | Tiết lộ sự tồn tại của tài liệu mật. Nếu doanh nghiệp muốn, cách đúng là một trường metadata do chủ sở hữu bật cho từng tài liệu (mặc định tắt), kèm luồng xin quyền. Đó là quyết định nghiệp vụ, không phải thứ hệ thống tự suy ra |
| Từ chối khi phần được xem bị tài liệu mật ghi đè | Một lời từ chối "bất thường" khi có tài liệu công khai khớp câu hỏi cũng là một cách lộ. Linter xử lý từ gốc |
| Ẩn tổng số tài liệu "Không có quyền xem" trong trace | Con số không phụ thuộc câu hỏi nên không nói gì về chủ đề. Nếu doanh nghiệp coi cả con số này là nhạy cảm, chỉ cần bỏ một dòng giao diện |
| Hạ ngưỡng hoặc thêm từ khoá để Linh nhận FAQ mục 2 | Là chỉnh theo test; đây là giới hạn đã biết của tìm kiếm từ vựng |

### 4.5 Bằng chứng

| | Code M2 | Code M3 + Change Request |
|---|---|---|
| CR-01 (4 lượt): đạt · hành vi đúng | 2/4 · 3/4 | 3/4 · 3/4 |
| Không giao thoa, bộ M3 (3 tài liệu mật × 5 persona không được xem × 31 câu hỏi) | 0 / 465 | **0 / 465** |
| Không giao thoa, bộ M2 | 0 / 160 | **0 / 160** |
| Rò rỉ (ID, canary) | 0 / 186 | **0 / 186** |

Đọc bảng: về hành vi, CR-01 trên code M2 và code mới như nhau. Kiến trúc "lọc trước, tìm sau" từ M2 đã đáp ứng B2 trên dữ liệu thật; lượt "chưa đạt" thêm của M2 chỉ vì M2 không liệt kê nguồn đã xem xét. Change Request đóng góp ba thứ khác. Thứ nhất, nó **chứng minh** điều đó bằng một phép thử mạnh hơn. Thứ hai, nó **đóng** một kênh lộ mà dữ liệu hiện tại chưa chạm tới: test `test_hidden_new_version_does_not_retire_the_version_others_see` chưa đạt trên code cũ và đạt sau khi sửa. Thứ ba, nó **chuyển** rủi ro còn lại sang người sửa được (linter).

Không hồi quy: **125** unit test đạt (118 cũ + 7 mới; 1 test cũ đổi số lượng tài liệu 21 → 22). 14/14 câu trả lời bộ M2 giống hệt lần commit Mission 3. Bộ M3 có 24/25 câu giống hệt; lượt khác duy nhất là gợi ý thứ ba của một câu `CLARIFY`, vì thống kê BM25 dịch nhẹ khi kho có thêm tài liệu, còn quyết định không đổi. Hiệu chỉnh vẫn ngưỡng 0.59, đúng 17/18. Linter trên dữ liệu thật không có cảnh báo mới, vì FAQ được viết nhất quán với chính sách.

Chế độ Gemini (`gemini-3.5-flash-lite`, bộ M3 chạy lại đầy đủ ngày 22/10/2026, [`m3_gemini.md`](eval/results/m3/m3_gemini.md)): 28/29 như chế độ trích nguyên văn, 0 rò rỉ / 186, 0 giao thoa / 465. CR-01 đạt 3/4; câu trả lời của Linh chỉ nói tháng 4 và "Phòng Nhân sự thông báo riêng", không tự thêm con số nào, hậu kiểm đạt. Các câu rơi về trích nguyên văn đều là câu Gemini tự cộng thâm niên, như 20/10 (3 câu ở lần chạy đầu, 2 câu ở lần chạy lại sau mục 2.7). Đọc lại câu M3-02 mà Gemini viết ở lần chạy lại ("13 ngày … cộng thêm 1 ngày do đủ 5 năm thâm niên", không nêu tổng nên qua hậu kiểm): đúng theo bản 2, nhưng Gemini dùng thâm niên *hiện tại* (6 năm) cho ngày tra cứu 01/06/2025. Kết luận không đổi ở đây; điều cần biết là hồ sơ người hỏi không được tính lại theo thời điểm hỏi. Lượt "bậc 2" bị từ chối trước khi tới Gemini.

### 4.6 Giới hạn còn lại

1. **Phần được xem có thể thiếu mà không ai nói ra.** Linh hỏi "mức tăng tối đa", FAQ chỉ nói "thông báo riêng". Dòng "Căn cứ" lẽ ra liệt kê "tối đa" là từ không tìm thấy, nhưng khi bỏ dấu, "tối đa" thành "toi da", trùng "tôi đã", và cả hai đều là stopword nên bị loại khỏi câu hỏi. Đây là cùng loại lỗi với "con mấy"/"còn mấy" ở mục 2.2.
2. **Lời chỉ dẫn của chủ sở hữu không tới được câu hỏi chi tiết** (CR-01, Linh, "bậc 2", chưa đạt). Người hỏi nhận câu từ chối chung, kèm đúng đầu mối Phòng Nhân sự Công ty A.
3. **Linter chỉ so con số**, giống luật mức sàn: FAQ ghi "được" còn chính sách mật ghi "không được" thì không bắt được.
4. **Không giao thoa được kiểm trên các câu hỏi của bộ test** (31 câu × 5 persona × 3 tài liệu), không phải mọi câu có thể hỏi. Kênh qua quan hệ thay thế được kiểm bằng unit test vì dữ liệu thật không có trường hợp này.