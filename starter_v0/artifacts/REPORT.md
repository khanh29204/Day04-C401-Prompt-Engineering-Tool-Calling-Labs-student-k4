# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 16:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: B1
- Members:
    + Trương Quang Minh - 2A202601212 - PM + UI design
    + Phạm Ngọc Quốc Khánh - 2A202601254 - Tool Engineer
    + Vũ Hữu Trường 2A202601694 - Tool Engineer 
    + Hoàng Trung Hải - 2A202601054 - Evaluation Designer
    + Hoàng Vũ Trung Nguyên - 2A202601076 - Evaluation Designer 
    + Phạm Anh Minh - 2A202601260 - Prompt Engineer
- Provider/model: GPT-4o

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> Cinema agent: tìm thông tin các bộ phim đang chiếu rạp hiện tại theo từ khóa/diễn viên/rạp chiếu, đề xuất và hỗ trợ đặt vé

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL và tổng hợp thành digest."

**Link dùng thử (truy cập được trong showdown):**

> Dán public URL nếu người khác cần mở từ máy riêng; localhost cũng được nếu demo trực tiếp trên máy trình chiếu. Streamlit được khuyến nghị, nhưng nhóm có thể dùng bất kỳ framework nào.
>
> URL:

## A2. Tool agent có

> Liệt kê các tool agent đang dùng. Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
| lookup | tra cứu thông tin Internet | không |
| social search | tìm trên mạng xã hội | không |
| cinema search | tra cứu rạp chiếu phim | có |
| wikipedia search | tra cứu wikipedia | có |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tôi cần xem phim Spiderman: Brand New Day trong hôm nay.
2. Tìm lịch chiếu Conan Movie 29 tại CGV Vincom Center Landmark 81 vào tối thứ Bảy tuần này, ưu tiên bản IMAX.
3. Đặt giúp mình 2 vé xem Conan Movie 29, suất khoảng 20:00 tối nay, nhưng chưa cho biết rạp.
4. Trên Twitter, khán giả đánh giá thế nào về Dune: Part Three bản IMAX? Hãy lấy 8 bài nổi bật nhất.
5. Đặt giúp mình một vé máy bay từ Hà Nội vào Đà Nẵng vào sáng mai.

## A4. Kịch bản demo đã rehearse

> Chuẩn bị 3–5 scenario. Mỗi scenario cần cho thấy tool đã làm gì và một thay đổi cụ thể giữa các version.

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| 1. Lookup showtime IMAX | `lookup` với `query="Conan Movie 29 CGV Landmark 81 IMAX"`, `topic="general"`, `timeframe="week"` | V0 hay chọn sai `social_search`; bản mới giữ nguyên cụm truy vấn và map đúng "tuần này" thành `timeframe=week`. | Re-run case `MOV_S01_lookup_imax_showtimes` |
| 2. Thiếu địa điểm thì hỏi lại | `clarify` với `response_type="text"` | Trước đây agent đoán rạp hoặc tra cứu mơ hồ; bản mới dừng đúng chỗ và hỏi thiếu thành phố/rạp trước khi gọi tool khác. | Re-run case `MOV_S02_clarify_missing_location` |
| 3. Chốt xác nhận trước thanh toán | `clarify` với `response_type="yes_no"` | V0 có xu hướng đi thẳng vào luồng mua vé; bản mới chặn ở cổng ràng buộc và yêu cầu xác nhận trước khi xử lý thanh toán. | Re-run case `MOV_S03_confirm_before_payment` |
| 4. Review phim trên Twitter | `social_search` với `query="Dune: Part Three IMAX"`, `search_type="Top"`, `limit=8` | Bản cũ hay giữ `Latest` hoặc sai limit; bản mới đổi đúng sang `Top` khi người dùng nói "nổi bật nhất" và giữ đúng 8 bài. | Re-run case `MOV_S04_social_reviews_top_imax` |
| 5. Yêu cầu ngoài phạm vi | Không gọi tool; trả lời từ chối/định hướng lại | Trước đây agent vẫn cố tra cứu hoặc gọi nhầm tool; bản mới nhận ra đây là vé máy bay nên dừng hẳn, không tiêu tốn tool call. | Re-run case `MOV_S05_out_of_scope_flight_booking` |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |  |
| v1 |  |  |  |  |  |  |
| v2 |  |  |  |  |  |  |
| v3 |  |  |  |  |  |  |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên |  |  |  |
| Optional built-in |  |  |  |
| Bonus: tool mới thứ 4 trở đi |  |  |  |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?
