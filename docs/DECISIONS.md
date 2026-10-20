# Nhật ký quyết định

Ghi mọi thay đổi so với Mission 1 và mọi quyết định phát sinh khi code. Câu trả lời cho câu hỏi bắt buộc 2 lấy từ file này, không viết lại theo trí nhớ.

Định dạng: **ngày · quyết định · lý do · case liên quan**.

---

## Thay đổi so với Mission 1 (chốt khi duyệt kế hoạch, 12/10/2026)

| # | Mission 1 | Mission 2 | Lý do | Case liên quan |
|---|---|---|---|---|
| D01 | Postgres + pgvector + BGE-M3 | BM25 trong bộ nhớ | Streamlit Cloud không có sẵn DB; model ~2GB sát giới hạn tài nguyên bản miễn phí và khởi động chậm; kho nhỏ nên BM25 đủ. **Đánh đổi:** kém với câu diễn đạt khác | TC10 |
| D02 | Metadata ở cấp tài liệu | Thêm `topic key` + `applies_to` ở cấp mục | Luật ưu tiên chỉ áp được khi biết hai đoạn nói về cùng một quy định; một bản nội quy Tập đoàn chứa nhiều chủ đề và nhiều đối tượng | TC05, TC09 |
| D03 | ~40 câu hỏi kiểm thử | 12 case sâu + ma trận rò rỉ | Đề yêu cầu "điều học được" cho từng case; ưu tiên chiều sâu | Tất cả |
| D04 | Chỉ có chế độ LLM | Thêm chế độ trích nguyên văn | Kiểm thử lõi độc lập với LLM; demo không chết khi hết quota | Tất cả |
| D05 | Thứ tự luật: phiên bản → cấp → loại | Thêm luật "đối tượng" | Persona thử việc / thực tập cần mục riêng trong cùng tài liệu | TC01, TC09 |

---

## Quyết định phát sinh khi code

| Ngày | Quyết định | Lý do | Case liên quan |
|---|---|---|---|
| 12/10/2026 | Thêm canary token vào A-ENG-02 (ngoài A-SAL-01 như kế hoạch) | Ma trận rò rỉ kiểm được cả tài liệu giới hạn theo vai trò, không chỉ theo đơn vị | Ma trận rò rỉ |
| 12/10/2026 | Một lỗi metadata cố ý: A-EXP-01@2 khai `supersedes: A-EXP-01@1` nhưng bản 1 không có trong kho | Để linter có một cảnh báo thật hiển thị ở tab "Dữ liệu"; test khẳng định linter chỉ báo đúng các cảnh báo dự kiến | — |
| 12/10/2026 | Ngưỡng `ABSTAIN` dựa trên **độ phủ câu hỏi** (tỉ lệ thông tin của câu hỏi, trọng số IDF, có mặt trong mục đầu), không dựa trên điểm BM25 thô | Điểm BM25 không chuẩn hoá được giữa các persona có kho khác nhau. Độ phủ nằm trong [0, 1]; term không có trong kho của người hỏi nhận IDF tối đa, nên khái niệm lạ trong câu hỏi (MBA, khung lương với người không có quyền) kéo độ phủ xuống. Thống kê chỉ tính trên mục đã qua lọc nên tài liệu bị ẩn không ảnh hưởng điểm | TC04, TC07, TC11 |
| 12/10/2026 | Chốt ngưỡng độ phủ = **0.59**, chọn **một lần** từ bộ hiệu chỉnh riêng `eval/calibration.yaml` (18 câu, không trùng bộ test), **trước** lần chạy eval đầu tiên | Quy tắc chọn định trước: độ chính xác cao nhất, rồi chọn ngưỡng giữa khoảng trống rộng nhất. Kết quả 17/18. Câu sai: "Hồ sơ hoàn ứng cần những giấy tờ gì?" (0.49) bị từ chối nhầm. Ngưỡng 0.44 cũng đạt 17/18 nhưng sai theo hướng ngược lại ("Thực tập sinh có được cấp laptop không?", 0.51, sẽ bị trả lời bừa). Chấp nhận từ chối nhầm hơn trả lời sai. Số liệu: `eval/results/calibration.md` | TC07, TC09, TC10, TC11 |
| 12/10/2026 | Stopword, cụm từ chung bị loại khỏi câu hỏi ("quy định", "chính sách", "công ty"...) và từ điển đồng nghĩa (`core/text.py`) viết **trước** lần chạy eval đầu tiên | Tránh chỉnh từ điển theo từng test case. Ghi nhận: từ điển có cụm "làm ở nhà → làm việc từ xa" vì đó là cách nói phổ biến nhất; nếu TC10 đạt thì là nhờ dòng này, không phải nhờ BM25 hiểu nghĩa | TC01, TC10 |
| 12/10/2026 | Bỏ "họ", "chị", "bao", "chúng" khỏi stopword; xử lý "bao nhiêu", "bao lâu", "làm sao" thành cụm bị loại khỏi câu hỏi | Sau khi bỏ dấu, các từ này trùng với từ nội dung: "hồ sơ", "hỗ trợ", "chi phí", "báo trước", "bảo mật", "chứng từ". Phát hiện khi xem cách tách term, trước khi chạy eval | — |
| 12/10/2026 | Nhận diện câu hỏi dữ liệu cá nhân (`OUT_OF_SCOPE`) bằng mẫu có **đại từ ngôi thứ nhất** + từ chỉ số dư ("tôi còn bao nhiêu", "lương của tôi") | Để câu hỏi chính sách như "phép còn lại có được chuyển không" hay "quy định nghỉ phép của tôi" không bị chặn nhầm | TC01, TC08 |
| 12/10/2026 | **Phát hiện sau eval lần 1 (chưa sửa):** TC01 và TC02 phía Linh *đạt theo tiêu chí tự động* nhưng trích mục "Nghỉ không lương" (A-LEAVE-01@3#4) thay vì "Số ngày phép năm" (#1). Với TC02 ("được nghỉ phép bao nhiêu ngày") câu trả lời là **sai nội dung** | Tiêu đề tài liệu được ghép vào mọi mục khi đánh chỉ mục, nên 5 mục của chính sách nghỉ phép gần như hoà điểm (4.52 / 4.28 / 4.27...); mục đầu thắng nhờ một chữ "nghỉ" thừa. Quy tắc "chủ đề = topic của mục điểm cao nhất" thành may rủi khi các mục hoà điểm. **Bài học:** kỳ vọng trong `cases.yaml` viết ở cấp tài liệu nên không bắt được lỗi; chỉ phát hiện khi đọc câu trả lời. `cases.yaml` giữ nguyên. Theo quy tắc P4 (các case khác thất bại giữ làm bằng chứng), việc sửa để sang P7 | TC01, TC02 |
| 14/10/2026 | Gemini chỉ viết lại câu trả lời ở trạng thái `ANSWERED` / `ANSWERED_WITH_NOTE`. `CONFLICT`, `ABSTAIN`, `OUT_OF_SCOPE` luôn do code trả lời | LLM không được chọn ngầm một bên khi có mâu thuẫn, và không có cơ hội bịa số liệu cá nhân. Ghi chú (bản sắp hiệu lực, FAQ lệch) vẫn do code sinh, không qua LLM | TC06, TC08 |
| 14/10/2026 | Hậu kiểm số cho phép thêm thâm niên trong hồ sơ và từng phần của ngày tháng (31/03 → 31, 3) | Để "31 tháng 3" không bị chặn nhầm khi nguồn ghi "31/03". Chưa cho phép số suy ra (14 + 1 = 15); xử lý sau khi xem kết quả chạy thật (P7) | TC01, TC02, TC05 |
| 14/10/2026 | **Rủi ro đã xảy ra:** `gemini-2.5-flash` (model mặc định trong kế hoạch) trả 404 "no longer available to new users"; nhiều model 3.x trả 503 "high demand". Đổi mặc định sang danh sách `gemini-3.5-flash-lite, gemini-3.1-flash-lite, gemini-3.8-flash`, thử lần lượt khi gặp 404 / 429 / 503 | Hạn mức free tier tính theo từng model nên chuyển model cũng giúp khi hết lượt. Danh sách mặc định luôn được nối sau giá trị `GEMINI_MODEL` cấu hình, nên Secrets cũ vẫn chạy | TC12, mọi case chế độ Gemini |
| 14/10/2026 | **Sửa lỗi TC01/TC02 (P7):** chủ đề chính = chủ đề có **tổng điểm BM25 cao nhất** trong các mục top-5 đạt ngưỡng độ phủ, thay cho chủ đề của riêng mục đầu | Lỗi thật phát hiện khi đọc kết quả eval lần 1 (các case vẫn "đạt" theo tiêu chí tự động). Trước: Linh hỏi "được nghỉ phép bao nhiêu ngày" nhận mục Nghỉ không lương; chế độ Gemini thì từ chối (TC02 chưa đạt). Sau: cả hai chế độ trích A-LEAVE-01@3#1, 14/14 lượt đạt. Ngưỡng từ chối không đổi (vẫn dựa trên mục đầu), nên hiệu chỉnh không bị ảnh hưởng. Hạn chế còn lại: câu hỏi rộng như TC01 vẫn chỉ được trả lời một chủ đề | TC01, TC02 |
| 14/10/2026 | **Giữ hậu kiểm số chặt** sau khi thấy đúng căng thẳng đã dự đoán: TC02 chế độ Gemini viết "15 ngày" (14 + 1 vì đủ 5 năm thâm niên) → bị chặn → hiện trích nguyên văn | Nới lỏng bằng cách chấp nhận mọi tổng/hiệu của các số trong nguồn sẽ cho lọt cả "13 ngày" (14 − 1, trùng số của bản cũ đã lưu trữ), là kiểu sai nguy hiểm nhất. Câu trả lời dự phòng vẫn đúng, chỉ kém cá nhân hoá. Hướng làm sau: buộc model ghi phép tính ("14 + 1 = 15") để hậu kiểm kiểm phép tính; vẫn không kiểm được điều kiện áp dụng (đủ 5 năm hay chưa) | TC02 |
| 14/10/2026 | Biến môi trường `GEMINI_MODEL` / `GEMINI_API_KEY` được chụp lại lúc nạp module | Đọc `st.secrets` làm Streamlit chép `secrets.toml` vào `os.environ`, ghi đè ngầm giá trị đặt từ môi trường (phát hiện khi lượt eval Gemini vẫn thử model cũ trước) | — |

---

# Mission 3 — Cải tiến (20/10/2026)

Cách làm giữ như Mission 2: đọc yêu cầu → chạy thử code M2 để tìm chỗ hỏng thật → viết kỳ vọng (`eval/cases_m3.yaml`) và chạy trên code M2 **trước** khi sửa `core/` (lần chạy 0: `eval/results/m3/run0_before_core_changes.md`) → cài đặt → chạy lại → đọc từng câu trả lời. Báo cáo đầy đủ: [`MISSION3.md`](../MISSION3.md).

## Đối chiếu M2 với 5 yêu cầu chung (chạy thử 20/10, trước khi quyết định)

| Yêu cầu | M2 làm được | Chỗ hỏng thật tìm thấy khi chạy |
|---|---|---|
| R1 Phiên bản & thời điểm | Lọc theo trạng thái, cửa sổ hiệu lực, `supersedes`; ghi chú bản sắp hiệu lực; chọn ngày tra cứu | (a) Câu hỏi có năm/ngày bị **từ chối**: "2025" bị coi là từ lạ → độ phủ 0.35. (b) Đặt ngày tra cứu 01/06/2025: trả **mức sàn Tập đoàn 12 ngày** thay vì chính sách Công ty A năm 2025 (13 ngày), vì bản `archived` bị loại cả với ngày nằm trong cửa sổ hiệu lực của nó |
| R2 Quyền theo bối cảnh | ACL theo đơn vị và vai trò, 0 rò rỉ | Hỏi về đối tượng khác người hỏi đều bị từ chối: HR hỏi về nhân sự thử việc, thực tập sinh hỏi về nhân sự chính thức, trưởng phòng hỏi về nhóm con (TC11) — vì lọc theo hợp đồng/đơn vị **của người hỏi** |
| R3 Mâu thuẫn giữa nguồn/cấp | R1–R5, cờ lệch FAQ, `CONFLICT` cùng cấp | Cấp con thấp hơn mức sàn (`floor`) của cấp cha: linter cảnh báo nhưng câu trả lời **vẫn đưa số của cấp con**, không nói gì |
| R4 Từ chối / nói rõ khi thiếu căn cứ | Ngưỡng độ phủ, `ABSTAIN`, `OUT_OF_SCOPE` | "Tuần này tôi không lên công ty…" trả lời tự tin vì "lên" khớp "trở lên" (đã ghi ở M2). Số liệu: đây là câu duy nhất qua ngưỡng mà không khớp cụm từ nào và không khớp đủ các từ |
| R5 Kiểm chứng nguồn | Thẻ nguồn (tài liệu, phiên bản, mục, ngày), trace | Ở chế độ Gemini người dùng **không xem được nguyên văn** đoạn đã dùng; không thấy nguồn nào bị loại và vì sao; không thấy lịch sử phiên bản |

## Quyết định

| Ngày | Quyết định | Lý do | Case |
|---|---|---|---|
| 20/10/2026 | **Ưu tiên 1 — tách "ai hỏi" khỏi "hỏi về ai, vào lúc nào"** (`core/context.py`). Quyền xem luôn theo người hỏi; phạm vi và đối tượng theo *đối tượng của câu hỏi*; hiệu lực theo *thời điểm của câu hỏi* | Là gốc chung của các lỗi R1 và R2 ở trên. Một thay đổi cấu trúc thay cho nhiều bản vá | M3-01…M3-08 |
| 20/10/2026 | `archived` = "hết hiệu lực", không phải "chưa từng có hiệu lực": dùng được khi ngày tính nằm trong cửa sổ hiệu lực, và bắt buộc có `effective_to` (linter). `draft` không bao giờ dùng | Sửa lỗi (b) của R1. Bản nháp A-LEAVE-01@4 (16 ngày, 2027) vẫn không lọt vào câu trả lời cho năm 2027 | M3-02, M3-03 |
| 20/10/2026 | Năm/ngày trong câu hỏi là **ngữ cảnh, không phải từ khoá**: dời ngày tính và bị bỏ khỏi truy vấn tìm kiếm (thay bằng dấu ngắt để không tạo bigram giả). "Năm Y" = 01/01/Y; năm hiện tại không dời; nhiều mốc khác nhau → không dời, nói rõ | Sửa lỗi (a) của R1. Chọn 01/01 vì đơn giản, giải thích được; thay đổi giữa năm của năm được hỏi không được nêu (giới hạn ghi trong README) | M3-01, M3-04, M3-05 |
| 20/10/2026 | **Không** đọc mốc thời gian tương đối ("năm sau", "năm trước", "năm ngoái") | Trong kho này chúng thường là *nội dung* câu hỏi ("phép chuyển sang năm sau"), không phải thời điểm. Đọc sai sẽ dời ngày của câu hỏi TC05 | — |
| 20/10/2026 | Câu trả lời cho thời điểm khác hôm nay luôn kèm quy định đang áp dụng hôm nay (nếu khác); với tương lai thêm "quy định tại … vẫn có thể thay đổi" | Người hỏi về 2027 không được hiểu nhầm đó là cam kết | M3-01, M3-03, M3-04 |
| 20/10/2026 | **Trả lời câu hỏi mở TC11: được xem thì được tra cứu.** Câu hỏi nêu rõ đơn vị (alias trong `org.yaml`) hoặc loại hợp đồng khác người hỏi → trả lời quy định của đối tượng đó, dòng đầu câu trả lời ghi "… không áp dụng cho bạn". Kỳ vọng cũ của TC11 giữ nguyên trong `cases.yaml`, đánh dấu `changed_in_m3` | Quản lý tra chính sách nhóm mình, HR tra quy định thử việc là nhu cầu thật. Không mở rộng quyền: ACL vẫn tính theo người hỏi, nên tra cứu chỉ *thu hẹp* tập tài liệu. Dòng "không áp dụng cho bạn" được code chèn vào chính câu trả lời (cả khi Gemini viết), không phụ thuộc model | M3-06, M3-07, TC11 |
| 20/10/2026 | **Không** tra cứu đơn vị thuộc **công ty khác**: trả `ABSTAIN` chung, lý do hiện bên cạnh | Thực tập sinh Công ty B chỉ xem được tài liệu cấp Tập đoàn; nếu tra cứu "Công ty A", hệ thống sẽ trình bày mức sàn 12 ngày như thể là quy định Công ty A (thật là 14). Trả lời sai có nhãn còn tệ hơn từ chối | M3-08 |
| 20/10/2026 | "chính thức" chỉ được hiểu là loại hợp đồng khi đi với danh từ chỉ người ("nhân sự/nhân viên chính thức"); alias đơn vị chỉ khai báo cách gọi không trùng giữa hai công ty ("phòng nhân sự" không phải alias) | "Khi nào ký hợp đồng chính thức?" là câu hỏi của người thử việc, không phải câu hỏi về nhân sự chính thức | test_context.py |
| 20/10/2026 | **Ưu tiên 2 — trạng thái mới `CLARIFY`** khi mục đầu qua ngưỡng nhưng chỉ khớp âm tiết rời: không khớp cụm từ (bigram) nào của câu hỏi và không khớp đủ mọi từ. Hiện các từ đã khớp / không khớp và tối đa 3 mục gần nhất, ghi rõ "chưa chắc là câu trả lời". Không qua Gemini | Luật không có tham số để chỉnh. Kiểm trên bộ hiệu chỉnh M2 (không viết cho luật này): đổi quyết định của **0/18** câu (`eval/results/m3/calibration.md`). **Bằng chứng mỏng:** trong bộ M3 luật này chỉ đổi kết quả của đúng 1 câu (câu gốc); 4 câu mới không có câu trả lời thì M2 cũng đã từ chối | M3-09 |
| 20/10/2026 | **Không** dùng cách "hai chủ đề điểm gần nhau → hỏi lại" | Số liệu chạy thử: ở câu gốc, chủ đề làm việc từ xa chỉ có độ phủ 0.37 (dưới ngưỡng), nên cách này không bắt được đúng lỗi cần sửa | M3-09 |
| 20/10/2026 | Mọi câu trả lời hiện dòng **"Căn cứ"**: từ của câu hỏi có / không có trong nguồn được trích (cụm liền nhau gộp lại; từ đồng nghĩa hiện theo chữ của tài liệu) | Người dùng tự thấy câu trả lời dựa trên khớp mạnh hay yếu, không cần mở trace | M3-09 |
| 20/10/2026 | **Ưu tiên 3 — cấp con dưới mức sàn của cấp cha → `CONFLICT`**: hiện cả hai, gắn cờ cả hai chủ sở hữu, nêu lý do. Không tự áp mức sàn | Phép so dùng con số đầu tiên của mỗi mục — đủ để *phát hiện*, không đủ để *phán xử*: B-GAME-01 ghi 10 ngày nhưng "bù 3 ngày sau mỗi đợt phát hành", có thể vẫn hợp lệ. Mức sàn chỉ xét với đúng đối tượng nó bảo vệ (nhân sự chính thức) | M3-10 |
| 20/10/2026 | **Ưu tiên 4 — kiểm chứng:** mỗi nguồn kèm nguyên văn đã dùng (đúng đoạn gửi cho Gemini) và mã nội dung (12 ký tự SHA-256); "Nguồn đã xem xét nhưng không dùng" kèm lý do; lịch sử phiên bản của tài liệu được trích. Chỉ liệt kê phiên bản người hỏi được xem; mọi trường mới nằm trong `public_view()` nên ma trận rò rỉ kiểm cả chúng | Ở chế độ Gemini đây là cách duy nhất để người dùng đối chiếu câu viết lại với văn bản gốc | M3-11 |
| 20/10/2026 | Thêm dữ liệu: B-GAME-01 (bẫy dưới mức sàn), A-PLT-02 (danh bạ trực chỉ nhóm Platform xem, canary `CANARY-PLT-5W9Z` — kiểm tra tra cứu nhóm con không mở rộng quyền của trưởng phòng), persona Quân (chính thức, Sản xuất game). Hai unit test M2 đổi vì số lượng (19→21 tài liệu, 5→6 persona; linter có thêm cảnh báo `below_floor` dự kiến) | Bẫy cho R2, R3. Thêm tài liệu cũng là phép thử hồi quy: thống kê BM25 của Linh đổi nhưng 12/14 câu trả lời M2 giống từng byte | M3-08, M3-10 |
| 20/10/2026 | `eval/compare.py`: lấy `core/` của commit M2 từ git, chạy **cùng dữ liệu, cùng bộ kiểm** với code M3. Thêm cột "hành vi đúng" tách "trả lời sai" khỏi "không báo thông tin mà M2 không có" | Để con số trước/sau không thổi phồng: 4/14 lượt "chưa đạt" của M2 chỉ vì thiếu trường mới | before_after.md |

## Phát hiện khi kiểm thử Mission 3

| Ngày | Phát hiện | Xử lý | Case |
|---|---|---|---|
| 20/10/2026 | **Lần chạy 0 (code M2):** "Con ốm thì tôi được nghỉ chăm con mấy ngày?" bị coi là câu hỏi dữ liệu cá nhân (`OUT_OF_SCOPE`): bỏ dấu thì "con mấy" (con cái) trùng "còn mấy" (số dư). Câu này viết trước khi chạy, không nhắm vào lỗi này | Câu hỏi có dấu được kiểm trên chính chữ có dấu ("còn"); câu không dấu vẫn kiểm như M2 | M3-09 |
| 20/10/2026 | Khi viết kỳ vọng M3-07: với người hỏi thử việc ở Công ty A, FAQ (mục chung "14 ngày" cho nhân sự chính thức) sẽ bị gắn cờ "lệch" so với mục riêng thử việc — báo động giả | Mục chung cấp thấp hơn không được so với câu trả lời chỉ gồm mục dành riêng cho loại hợp đồng khác | M3-07 |
| 20/10/2026 | Dòng "Căn cứ" ban đầu liệt kê từng cặp âm tiết chồng nhau ("phụ cấp", "cấp trực", "trực on") và chữ không dấu với từ đồng nghĩa ("làm viec tu xa") — thấy khi chạy giao diện | Gộp cặp liền nhau thành cụm; từ đồng nghĩa hiện theo chữ của tài liệu | test_m3.py |

## Chủ động chưa làm

| Việc | Vì sao chưa làm |
|---|---|
| Tìm kiếm ngữ nghĩa (embedding) | Sửa được từ chối nhầm kiểu "giấy tờ"/"hồ sơ", nhưng không nằm trong 5 yêu cầu, buộc hiệu chỉnh lại ngưỡng, và là thay đổi dễ gây hồi quy nhất. Lớp lọc chạy trước tìm kiếm giữ nguyên nên có thể thêm sau mà không đụng tới phần quyền |
| Phát hiện mâu thuẫn không có con số ("được" / "không được") | Cần LLM hoặc mô hình NLI để phán; không kiểm được ổn định bằng test. Rủi ro cho người dùng thấp hơn: R3 vẫn chọn đúng nguồn thứ bậc cao, chỉ thiếu cờ báo chủ sở hữu |
| Mốc thời gian tương đối, thay đổi giữa năm | Xem quyết định ở trên |
| Câu hỏi nhiều chủ đề, hội thoại nhiều lượt, SSO thật | Không thuộc 5 yêu cầu; giữ phạm vi |
| Cá nhân hoá phép tính (14 + 1 = 15 ngày cho Linh) | Hậu kiểm số vẫn chặn; câu trả lời dự phòng đúng nhưng kém cá nhân hoá (giới hạn từ M2, chưa đổi) |
| Change Request | Chưa được chỉ định (20/10/2026). Chỗ thêm case: cuối `eval/cases_m3.yaml` |
