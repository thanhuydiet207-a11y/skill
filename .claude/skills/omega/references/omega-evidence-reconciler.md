# OMEGA evidence-reconciler

## Inputs

Record gate thật thuộc đúng project/target root, evidence artifact nguyên gốc và gate config đã review tại thời điểm chạy. Không dùng scenario, mock, manual fixture hoặc summary thay gate proof. Xác định câu hỏi cần trả lời: source drift, context drift, execution failure, artifact integrity hay thiếu dữ liệu.

## Workflow

1. **Lấy artifact và provenance:** ghi record ID, project/root, thời điểm, source/mode/index, HEAD, gate config identity, command/argv, exit status và artifact reference. Đọc artifact từ nguồn đã được xác định; nếu thiếu artifact hoặc không xác định được nguồn gốc, phân loại unverified thay vì tái tạo nội dung từ summary.
2. **Kiểm tra report và policy:** với file report, đọc lại cùng test_report policy để kiểm tra configured argv, argv đã render và SHA-256 content trong evidence. So sánh bytes/hash với artifact hiện tại; phân biệt missing, mismatch và content thực sự giống nhau. Report nằm ở namespace mới không chứng minh runner trung thực. Content snapshot giữ trong artifact; summary trỏ reference, không bỏ nội dung để tiết kiệm token. Thay report policy/engine/runtime thì xác minh lại; xem docs/UPGRADE_0_5.md.
3. **Xác minh fingerprint thực thi:** đối chiếu fingerprint có hash whitelist runtime environment và các runtime_inputs được khai tường minh; đọc lại cùng `--gate-config` của lúc thực thi. Process timeout/output-limit/invalid UTF-8 phủ quyết readiness dù exit code trong record là 0. Chưa ràng buộc được dependency/service/policy ngoài fingerprint phải ghi unverified, không tự coi là tương đương; xem docs/UPGRADE_0_4.md.
4. **Chạy reconciliation:** dùng `python3 -m omega evidence-reconciler --record RECORD --compact` hoặc lặp `--evidence`. So source/mode/index, HEAD, known execution fingerprint, artifact hash và test outcomes; đọc lý do stale trước khi quyết định validation bổ sung. Chỉ dùng runner trong checkout engine; project khác dùng runner tuyệt đối và `--project-root`.
5. **Phân loại từng record riêng:**  
   - `current`: mọi trường bắt buộc, artifact và context đã khớp theo chính sách hiện tại. Chỉ có nghĩa là current trong phạm vi fingerprint được quan sát, không chứng minh runner hoặc môi trường bên ngoài hoàn toàn đáng tin.  
   - `stale-source`: source, index, mode, config/policy hoặc artifact có liên quan đã đổi.  
   - `stale-context`: runtime input, dependency, service hoặc execution context thay đổi/không khớp.  
   - `same-source-different-head`: source liên quan có vẻ giống nhưng HEAD khác; cần xác minh phạm vi phụ thuộc và policy, không tự coi là equivalent.  
   - `unverified/invalid`: thiếu artifact, schema sai, project mismatch, fingerprint không đủ hoặc metadata mâu thuẫn.  
   Không nâng cấp trạng thái bằng suy đoán; nếu engine dùng tên trạng thái khác, giữ nguyên trạng thái engine trả về và giải thích bằng ngôn ngữ rõ ràng.
6. **Chọn validation tối thiểu đủ dùng:** xác định thay đổi nào làm bằng chứng stale và chạy lại đúng gate/phần bị ảnh hưởng khi có thể. Chạy toàn suite khi dependency rộng, tác động chéo hoặc chính sách yêu cầu. Không bỏ required gate chỉ vì rerun tốn kém; nếu không đủ ngân sách/quyền thì ghi blocked/not-run.
7. **Giữ nguyên lịch sử:** lưu kết quả reconciliation mới dưới record/evidence mới theo workflow engine. Không sửa record cũ, copy hash, chỉnh timestamp hoặc thay metadata để ép bằng chứng thành current. Giữ cả kết quả cũ và lý do bị thay thế.

## Evidence

Trả record/artifact reference, project/root, trạng thái gốc và trạng thái reconciliation, lý do cho từng phân loại, các trường đã so sánh, validation cần chạy và phần global policy/service/dependency chưa quan sát. Phân biệt rõ `current`, `stale`, `invalid`, `blocked` và `not-run`; không tuyên bố readiness chỉ từ exit code 0 hoặc một hash trùng.

## Failure handling

Artifact thiếu/schema sai/project khác, hash/argv/config không khớp, runtime timeout/output-limit/encoding error hoặc metadata mâu thuẫn: không dùng làm readiness proof. Giữ nguyên record cũ, ghi blocker và thu thập bằng chứng từ nguồn đúng. Không sửa record cũ hoặc copy hash để ép hợp lệ. Nếu chưa thể phân biệt source drift với context drift, báo cả hai khả năng và chỉ rõ trường còn thiếu.

## Stop conditions

Dừng khi từng record được phân loại với lý do và hành động tiếp theo cụ thể. Không tự chạy lại toàn suite vô hạn; chỉ kiểm tra lại phần có thay đổi/lo ngại hợp lý và giữ gate bắt buộc. Không tự promote/release/deploy chỉ vì reconciliation trả current.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và `--project-root`.
