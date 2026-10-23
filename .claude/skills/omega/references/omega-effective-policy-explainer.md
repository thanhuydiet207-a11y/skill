# OMEGA effective-policy-explainer

## Inputs

Một PreToolUse event JSON nguyên bản, project root đã xác định và câu hỏi/phạm vi policy cần giải thích. Không yêu cầu credential values; redact secret/token và nội dung nhạy cảm khỏi bản sao dùng để phân tích. Phải biết đang kiểm tra policy của OMEGA, platform hay cả hai.

## Workflow

1. **Xác minh đầu vào:** chạy `python3 -m omega effective-policy-explainer --input INPUT --compact`. Kiểm tra schema/event type, project root, timestamp nếu có, và nguồn lấy event. Event thiếu trường quan trọng, bị cắt hoặc không rõ provenance thì báo unknown; không tự điền giá trị còn thiếu.
2. **Dùng đúng policy parser:** đối chiếu cùng grammar/version mà hook dùng tại thời điểm event. Không suy diễn kết quả từ regex gần giống, docs cũ hoặc policy khác phiên bản. Ghi lại parser/engine version và hash của policy/config nếu có.
3. **Phân tích hành động cụ thể:** kiểm tra cwd, runner/executable, args đã parse, paths sau chuẩn hóa, shell expansion, environment, redirection và background/child process. Phân biệt argv literal với shell command string; không thực thi command chỉ để giải thích nó. Kiểm tra path traversal, symlink, path alias, glob expansion và khác biệt giữa path tương đối với project root/cwd.
4. **Tách quyết định theo lớp:** báo riêng `omega_decision` (allowed/denied/unknown và rule source), `platform_decision` (allow/deny/approval required/unknown nếu event chứng minh được) và `effective_outcome` chỉ khi có đủ bằng chứng về cả lớp cần thiết. Allowed của OMEGA không đồng nghĩa platform cho phép hoặc command an toàn; platform approval cũng không chứng minh policy OMEGA đã cho phép.
5. **Giải thích quy tắc:** chỉ rõ rule ID/source, scope, lý do match/non-match, điều kiện còn thiếu và tác động của cwd/args/paths. Phân biệt explicit allow, explicit deny, default behavior và không có rule phù hợp. Không tự coi absent rule là allow hoặc deny nếu grammar/version chưa xác định semantics.
6. **Giữ policy bất biến:** không sửa allowlist, hook, MCP, platform permission hoặc policy config trong lúc giải thích. Nếu user muốn thay đổi policy, xử lý thành một task riêng với scope, authorization, diff và validation rõ ràng.
7. **Bảo vệ dữ liệu:** báo cáo command/args đã redact; không lặp nguyên command chứa token, password, private key, cookie hoặc payload riêng tư. Chỉ trích đoạn tối thiểu cần để giải thích rule; nếu redaction che mất dữ kiện quyết định, nêu rõ giới hạn thay vì khôi phục secret.
8. **Đối chiếu nguồn từ chối:** nếu platform từ chối hoặc yêu cầu approval, xác định policy thực tế ở lớp đó trước khi đề xuất quyền bổ sung. Không dùng OMEGA output làm bằng chứng về trạng thái hooks/MCP/platform nếu không có nguồn độc lập.

## Evidence

Trả event identity/provenance, project root, parser/engine version, policy/config hash khi có, `omega_decision`, `platform_decision`, `effective_outcome` nếu xác định được, rule source/ID, scope và các giả định chưa xác minh. Không lặp dữ liệu nhạy cảm. Phân biệt rõ `allowed`, `denied`, `approval required` và `unknown`; không gộp chúng thành một trạng thái thành công/thất bại.

## Failure handling

Thiếu event/schema, project mismatch, parser/version không rõ, command bị cắt, path/args không thể chuẩn hóa hoặc policy nguồn không truy cập được: trả `unknown`/denied theo đúng semantics đã biết và nêu blocker. Không sửa allowlist để vượt lỗi, không thực thi command để “thử xem”, và không suy diễn platform decision từ config OMEGA. Nếu các lớp policy mâu thuẫn, giữ nguyên kết quả riêng từng lớp và chuyển sang review.

## Stop conditions

Dừng khi lời giải thích có nguồn, scope, quyết định riêng từng lớp và phần chưa biết rõ ràng. Không cấp quyền, thay hook, bật MCP, thực thi command hoặc suy diễn `hooks_disabled` từ config OMEGA. Nếu cần thay đổi quyền, xin authorization riêng và xác minh lại sau thay đổi.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và `--project-root`.
