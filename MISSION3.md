# Mission 3 — Cải tiến

> Toàn bộ tổ chức, người, tài liệu và số liệu đều là **giả lập**.

Tiếp tục trên sản phẩm Mission 2 (commit `d40d1df`), không làm lại. Nhật ký quyết định chi tiết: [`docs/DECISIONS.md`](docs/DECISIONS.md) (phần Mission 3). Bảng trước/sau sinh tự động: [`eval/results/m3/before_after.md`](eval/results/m3/before_after.md).

**Change Request:** chưa được chỉ định tại thời điểm viết (20/10/2026). Chỗ thêm case: cuối [`eval/cases_m3.yaml`](eval/cases_m3.yaml).

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

**Kết quả** (cùng dữ liệu, cùng bộ kiểm, chỉ khác code): bộ Mission 3 **11/25 → 25/25** lượt đạt (tính riêng hành vi: 15/25 → 25/25); bộ Mission 2 không hồi quy (13/13, 12/14 câu trả lời giống từng byte); **0 rò rỉ** trên 174 lượt.

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

| Bộ kiểm thử | Code | Lượt đạt | Hành vi đúng* | Từ chối nhầm | Rò rỉ |
|---|---|---|---|---|---|
| Mission 3 (25 lượt) | M2 | 11/25 | 15/25 | 6 | 0 / 174 |
| Mission 3 (25 lượt) | **M3** | **25/25** | **25/25** | 0 | 0 / 174 |
| Mission 2 (14 lượt) | M2 | 13/13 + 1 đổi có chủ đích | 13/13 | 0 | 0 / 96 |
| Mission 2 (14 lượt) | **M3** | **13/13** + 1 đổi có chủ đích | 13/13 | 0 | 0 / 96 |

\* *Hành vi đúng* bỏ qua các kỳ vọng về thông tin Mission 2 vốn không xuất ra (ngày tính, tra cứu cho ai, nguyên văn…), để không tính "thiếu trường" là "trả lời sai".

| Yêu cầu | M2: đạt · hành vi đúng | M3: đạt · hành vi đúng |
|---|---|---|
| R1 Phiên bản & thời điểm | 0/5 · 1/5 | 5/5 · 5/5 |
| R2 Quyền theo bối cảnh | 5/9 · 6/9 | 9/9 · 9/9 |
| R3 Mâu thuẫn giữa các cấp | 1/2 · 1/2 | 2/2 · 2/2 |
| R4 Chưa đủ căn cứ | 5/7 · 5/7 | 7/7 · 7/7 |
| R5 Kiểm chứng nguồn | 0/2 · 2/2 | 2/2 · 2/2 |

Đọc bảng: R5 không đổi *hành vi* — câu trả lời của M2 vốn đúng; cái M3 thêm là *khả năng kiểm chứng* câu trả lời đó. Khác biệt hành vi lớn nhất nằm ở R1 và R2.

Không hồi quy:
- **12/14** câu trả lời của bộ Mission 2 **giống từng byte** với kết quả Mission 2 đã commit. Hai lượt khác: TC06 thêm một dòng "Lý do:" cho mâu thuẫn; TC11 đổi có chủ đích.
- **83** unit test của Mission 2 chạy trên code M3: 81 đạt nguyên trạng, 2 đổi vì số lượng dữ liệu (19→21 tài liệu, 5→6 persona, thêm cảnh báo linter dự kiến). Tổng cộng **118** unit test.
- Hiệu chỉnh ngưỡng (bộ 18 câu riêng): ngưỡng vẫn 0.59, 17/18; luật "căn cứ mỏng" đổi quyết định của **0/18** câu ([`eval/results/m3/calibration.md`](eval/results/m3/calibration.md)).
- **0 rò rỉ / 174 lượt**, với 3 tài liệu mật: 2 của M2 và **A-PLT-02** (danh bạ trực chỉ nhóm Platform xem, có canary) được cài riêng để tấn công tính năng tra cứu. Ma trận kiểm cả các trường mới (ngữ cảnh, nguồn đã xem xét, lịch sử phiên bản, gợi ý của `CLARIFY`).
- **Chế độ Gemini** (`gemini-3.5-flash-lite`, 20/10/2026, [`m3_gemini.md`](eval/results/m3/m3_gemini.md), [`m2_gemini.md`](eval/results/m3/m2_gemini.md)): bộ M3 25/25, bộ M2 13/13 (+ TC11 đổi có chủ đích), 0 rò rỉ ở cả hai (174 và 96 lượt; context gửi Gemini cũng được kiểm). Câu trả lời tra cứu giữ đúng khung "không áp dụng cho bạn"; TC12 vẫn không làm theo chỉ thị nhúng. 3 câu ở bộ M3 rơi về trích nguyên văn, cả 3 vì Gemini tự cộng thâm niên (13 + 1 = 14, 14 + 1 = 15) và hậu kiểm số chặn — giới hạn đã biết từ M2. Đáng chú ý: với câu "năm 2025", con số Gemini tự tính (**14**) trùng đúng số của *phiên bản hiện hành* — chính loại nhầm lẫn khiến M2 quyết định không nới hậu kiểm.

Quy trình: kỳ vọng `cases_m3.yaml` viết trước khi sửa `core/` và đã chạy trên code M2 (lần chạy 0, lưu lại). Mọi câu trả lời của lần chạy cuối được đọc lại bằng mắt — nhờ vậy thấy hai câu ngoài bộ test ở mục 2.6.

### 2.6 Giới hạn còn lại

Theo kết quả chạy, không theo dự đoán:

1. **Bằng chứng cho `CLARIFY` mỏng.** Trong bộ M3 nó chỉ đổi đúng 1 câu (câu gốc từ M2); 4 câu mới không có câu trả lời thì M2 cũng đã từ chối. Luật chỉ bắt khớp *âm tiết rời*; khớp ngẫu nhiên ở mức *cụm từ* vẫn lọt. Câu ngoài bộ test, chạy trên cả hai phiên bản:

   | Câu hỏi | M2 và M3 | Đánh giá |
   |---|---|---|
   | Nam · "Khi nào tôi được ký hợp đồng chính thức?" | trả lời bằng mục nghỉ phép thử việc (khớp cụm "hợp đồng chính thức") | Sai chủ đề, tự tin. Kho không có quy định về thời gian thử việc |
   | Tuấn · "Khung lương khối kỹ thuật là bao nhiêu?" | trích mục *Nguyên tắc xét tăng lương* thay vì *Khung lương kỹ sư* | Sai mục: tiêu đề tài liệu ghép vào mọi mục nên hai mục gần hoà điểm (cùng gốc với lỗi TC02 của M2) |
   | Linh · "Tháng 3/2026 tôi được làm việc từ xa mấy ngày?" | M2: 2 ngày (bản hiện hành) · **M3: 1 ngày** (bản có hiệu lực tháng 3/2026) | M3 đúng |

2. **Hiểu "lúc nào" và "về ai" dựa trên luật.** Năm/ngày tuyệt đối và cách gọi đơn vị khai báo sẵn thì hiểu; "năm sau", "bên game", "team Plat" thì không. "Năm Y" tính tại 01/01/Y nên thay đổi giữa năm của năm được hỏi không được nêu.
3. **Metadata sai → trả lời sai một cách tự tin** (giữ nguyên từ M2). Thêm một chỗ phụ thuộc: cửa sổ hiệu lực của bản lưu trữ phải đúng.
4. **Danh tính là ô chọn persona.** Toàn bộ kiểm soát quyền đúng *với giả định* danh tính đúng.
5. **Từ chối nhầm vì khác từ** ("giấy tờ" / "hồ sơ") chưa sửa — chủ động để lại (mục 2.3).

---

## 3. Bộ kiểm thử Mission 3

Chạy: `python -m eval.run_eval` (bộ M3) · `python -m eval.run_eval --suite m2` (hồi quy) · `python -m eval.compare` (trước/sau) · `pytest`.

| Đề yêu cầu | Đáp ứng |
|---|---|
| Chạy lại test quan trọng của M2 | Toàn bộ 12 case / 14 lượt + ma trận rò rỉ + 83 unit test M2, trên code M3 ([`m2_extractive.md`](eval/results/m3/m2_extractive.md)) |
| ≥ 3 test cho phần cải tiến | 11 case / 25 lượt ([`cases_m3.yaml`](eval/cases_m3.yaml), [`m3_extractive.md`](eval/results/m3/m3_extractive.md)) + 35 unit test mới |
| ≥ 1 test cho Change Request | **Chưa có Change Request được chỉ định** — sẽ thêm `CR-01` khi có |
| ≥ 1 edge case / tình huống khó | M3-03 (năm 2027: bản nháp không được lọt), M3-05 (năm không có quy định), M3-08 (tra cứu không mở rộng quyền, tự xưng chức danh), M3-10 Nam (mức sàn chỉ xét đúng đối tượng) |
| ≥ 1 regression test | Bộ M2 đầy đủ; M3-09 (f)(g): câu trả lời được không bị `CLARIFY` chặn nhầm; M3-06 Linh: thành viên nhóm vẫn nhận như cũ |

| Case | YC | Kỳ vọng | Kết quả (M3) | Điều học được |
|---|---|---|---|---|
| M3-01 | R1 | Năm 2025 → bản 2 (13 ngày) + nhắc bản hiện hành | Đạt | Năm trong câu hỏi là ngữ cảnh; để nó làm từ khoá thì hệ thống từ chối |
| M3-02 | R1 | Ngày tra cứu 01/06/2025 → bản 2, không phải mức sàn | Đạt | `archived` phải dùng được trong cửa sổ hiệu lực, nếu không tính năng "đổi ngày tra cứu" của M2 trả sai |
| M3-03 | R1 · edge | Năm 2027 → bản 3, không bản nháp 16 ngày | Đạt | Câu hỏi về tương lai cần cảnh báo "còn có thể thay đổi" |
| M3-04 | R1 | Từ 01/01/2027 → bản 3 + quy định hôm nay | Đạt | — |
| M3-05 | R1 · edge | Năm 2020 → từ chối | Đạt | Không có quy định thì không lấy bản hiện hành thay vào |
| M3-06 | R2 | Hoa tra cứu nhóm con (có nhãn); Linh như cũ; Minh từ chối | Đạt | Thay kỳ vọng TC11 — quyết định nghiệp vụ, ghi trong DECISIONS |
| M3-07 | R2 | HR hỏi về thử việc; thực tập sinh hỏi về chính thức | Đạt | Viết kỳ vọng này làm lộ một báo động giả: FAQ cho nhân sự chính thức bị gắn cờ "lệch" với mục thử việc — đã sửa |
| M3-08 | R2 · bảo mật | Không tra cứu công ty khác; trưởng phòng không thấy tài liệu chỉ nhóm con xem; tự xưng chức danh vô hiệu | Đạt | Tra cứu thu hẹp, không mở rộng quyền — kiểm bằng canary mới |
| M3-09 | R4 | Câu gốc + 4 câu mới không có câu trả lời: không trả lời tự tin; 2 câu trả lời được: vẫn trả lời | Đạt | Lần chạy 0 bắt được lỗi không dự đoán ("con mấy"/"còn mấy"). Bằng chứng cho luật mới mỏng (mục 2.6) |
| M3-10 | R3 | Quân: `CONFLICT` dưới mức sàn; Nam (thử việc): không ảnh hưởng | Đạt | Mức sàn chỉ áp cho đúng đối tượng nó bảo vệ |
| M3-11 | R5 | Nguyên văn + mã nội dung; FAQ trong "đã xem xét"; bản 2 trong lịch sử | Đạt | Nguyên văn được kiểm khớp từng ký tự với tài liệu |

---

## 4. Ba câu quyết định bắt buộc

### 4.1 Sau khi nhận yêu cầu mới, bạn đã ưu tiên thay đổi điều gì và chủ động chưa làm điều gì? Vì sao?

Mình không bắt đầu từ danh sách tính năng mà chạy thử Mission 2 với câu hỏi theo đúng 5 yêu cầu. Lỗi nặng nhất nằm ở R1 và R2 (hành vi đúng 1/5 và 6/9): hỏi về năm 2025 bị từ chối, đặt ngày về 2025 thì trả **sai số**, trưởng phòng hay HR hỏi về người khác đều bị từ chối. Các lỗi này cùng một gốc — M2 coi người hỏi vừa là người *được xem*, vừa là người *được áp dụng*, và luôn tính *hôm nay*. Vì vậy **ưu tiên số 1** là tách *ai hỏi* (quyền), *hỏi về ai* (phạm vi) và *hỏi về lúc nào* (phiên bản), với một nguyên tắc không đổi: quyền luôn tính theo người hỏi. Sau đó, theo mức nghiêm trọng: hỏi lại thay vì trả lời khi căn cứ chỉ là vài âm tiết khớp ngẫu nhiên (lỗi thật từ M2), báo mâu thuẫn khi cấp dưới thấp hơn mức sàn, và cho xem nguyên văn để kiểm chứng.

Chủ động **chưa làm**: tìm kiếm ngữ nghĩa — sửa được từ chối nhầm, nhưng không nằm trong 5 yêu cầu, phải hiệu chỉnh lại ngưỡng và là thay đổi dễ gây hồi quy nhất; tra cứu sang **công ty khác** — vì người hỏi chỉ thấy tài liệu Tập đoàn nên sẽ nhận mức sàn 12 ngày trình bày như quy định Công ty A (thật là 14), sai có nhãn còn tệ hơn từ chối; mốc thời gian tương đối — "năm sau" trong kho này thường là nội dung câu hỏi; phát hiện mâu thuẫn không có số — cần LLM để phán, không kiểm được ổn định.

### 4.2 Thay đổi nào tạo ra khác biệt lớn nhất giữa sản phẩm Mission 2 và Mission 3? Bạn dùng bằng chứng nào để kết luận phiên bản mới tốt hơn?

**Tách "ai hỏi" khỏi "hỏi về ai, vào lúc nào".** Tính theo hành vi, nó đưa R1 từ 1/5 lên 5/5 và R2 từ 6/9 lên 9/9 — phần lớn khác biệt hành vi giữa hai phiên bản — và trả lời câu hỏi nghiệp vụ còn mở của Mission 2 (TC11).

Bằng chứng:
1. **Cùng bộ kiểm, cùng dữ liệu, chỉ khác code** — `eval/compare.py` lấy `core/` của commit Mission 2 từ git và chạy cạnh code mới: bộ Mission 3 **11/25 → 25/25**; tính riêng hành vi (bỏ các trường M2 vốn không có) **15/25 → 25/25**.
2. **Không hồi quy:** bộ Mission 2 vẫn 13/13 (TC11 đổi có chủ đích, kỳ vọng cũ vẫn để trong file); **12/14 câu trả lời giống từng byte**; 81/83 unit test cũ đạt nguyên trạng (2 đổi vì số lượng dữ liệu); hiệu chỉnh ngưỡng không đổi (17/18), luật mới đổi 0/18 quyết định.
3. **An toàn không giảm:** 0 rò rỉ / 174 lượt, gồm một tài liệu mật mới cài riêng để tấn công tính năng tra cứu.
4. **Quy trình chống tự lừa:** kỳ vọng viết và chạy trên code cũ *trước* khi sửa (lần chạy 0 lưu lại); mọi câu trả lời được đọc lại — nhờ vậy ghi được cả những câu M3 vẫn sai (mục 2.6), không chỉ con số đạt.

Giới hạn của bằng chứng: bộ 25 lượt do chính mình viết. Con số "25/25" dễ đẹp; bằng chứng mạnh hơn là từng lỗi cụ thể của M2, có giải thích nguyên nhân, kèm việc không hồi quy.

### 4.3 Nếu sản phẩm này được đưa cho người dùng thật vào ngày mai, rủi ro hoặc giới hạn lớn nhất còn lại là gì? Bạn sẽ ưu tiên xử lý nó như thế nào?

**Điều kiện tiên quyết, không phải rủi ro:** danh tính hiện là ô chọn persona. Mọi kiểm soát quyền đúng *với giả định* danh tính đúng — ngày mai ai cũng chọn được "Tuấn (HR)" để xem khung lương. Không đưa cho người dùng thật trước khi nối SSO và lấy đơn vị, vai trò, loại hợp đồng từ hệ thống nhân sự.

**Rủi ro lớn nhất sau đó: câu trả lời sai nhưng tự tin**, ở những chỗ code không tự phát hiện được:
- câu hỏi khớp ngẫu nhiên ở mức cụm từ ("Khi nào tôi được ký hợp đồng chính thức?" → trả mục nghỉ phép thử việc), hoặc chọn nhầm mục trong cùng tài liệu ("khung lương" → mục xét tăng lương) — cả hai đã thấy khi chạy;
- metadata sai (phạm vi, đối tượng, ngày hiệu lực) — hệ thống tin metadata tuyệt đối;
- người dùng thật diễn đạt đa dạng hơn bộ 25 câu do mình viết, nên tỉ lệ thật chưa đo được.

**Ưu tiên xử lý:**
1. **Thí điểm có đo:** một công ty, tài liệu HR thật; mỗi câu trả lời có nút "đúng / sai / không liên quan"; ghi log câu hỏi + trace (tôn trọng quyền riêng tư). Mục tiêu đầu tiên là *đo* tỉ lệ sai-tự-tin trên câu hỏi thật, rồi mới sửa.
2. **Metadata là cổng xuất bản:** linter chặn đăng tài liệu có lỗi (thiếu ngày, chồng phiên bản, dưới mức sàn); chủ sở hữu duyệt topic / đối tượng (có thể để LLM gợi ý, người duyệt).
3. **Chặn sai-tự-tin bằng dữ liệu thật:** dùng log thí điểm làm bộ hiệu chỉnh mới, rồi mới thêm tìm kiếm ngữ nghĩa *phía sau* lớp lọc quyền hiện có và kiểm "mục được chọn có thật sự trả lời câu hỏi" — đo bằng chính log đó, không bằng bộ test tự viết.
