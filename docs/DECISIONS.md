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
