# OMEGA context-sufficiency-check

## Inputs

Requirements manifest có source ranges, acceptance/constraints, task invariants và dependencies cần thiết; packet chứa nội dung thực, source identity/hash và phạm vi trích xuất. Ghi rõ mục tiêu task, budget, target project/root và nguồn authoritative. Không đưa secrets hoặc dữ liệu không cần thiết vào packet.

## Workflow

1. **Đóng băng yêu cầu trước khi thu gọn context:** xác định acceptance, constraints, safety invariants, các file/range bắt buộc, version/commit và dependency cần thiết. Không suy ra rằng một range là đủ chỉ vì nó khớp từ khóa.
2. **Xác minh packet:** chạy `python3 -m omega context-sufficiency-check --input INPUT --compact`. Kiểm tra range bounds, overlap/gap, actual content/full-file hash, source version, encoding/truncation và task invariants. Hash chỉ xác minh bytes trong phạm vi đã băm; không chứng minh nguồn authoritative hoặc dependency đầy đủ.
3. **Kiểm tra ngữ cảnh phụ thuộc:** bao gồm định nghĩa được gọi tới, caller/callee liên quan, schema/config, error handling, tests, policy/tool permission và các side effects cần thiết cho acceptance. Nếu dependency chưa xác định, ghi rõ unknown; mở rộng manifest/packet có chủ đích thay vì tự cắt source hoặc đoán.
4. **Giữ nguyên semantics:** so packet với source gốc để phát hiện bỏ sót điều kiện, negation, exceptions, ordering, scope, types, invariants và failure paths. Không paraphrase nội dung normative nếu việc đó làm mất ràng buộc; giữ nguyên exact text hoặc trỏ đến range/hash có thể kiểm chứng.
5. **Xử lý budget có kiểm soát:** khi packet vượt budget, ưu tiên loại nội dung trùng lặp hoặc không liên quan đã được xác định, rồi chạy lại kiểm tra. Không bỏ acceptance/assertion, safety constraints, nguồn quan trọng hoặc bằng chứng trái chiều chỉ để vừa budget. Byte giảm không chứng minh token, chất lượng LLM hoặc instruction adherence không đổi.
6. **Đánh giá trước khi gửi model/tool:** kiểm tra manifest và packet cùng một source revision; nếu source/acceptance/dependency đổi sau khi tạo packet, đánh dấu stale và tạo lại. Không gọi model hoặc thực thi hành động rủi ro nếu các input bắt buộc còn thiếu hoặc sai nguồn. Người dùng phải được thông báo phần thiếu có thể ảnh hưởng quyết định.
7. **Bảo vệ dữ liệu:** chỉ truyền dữ liệu tối thiểu cần thiết. Redact credentials, private keys, tokens và thông tin cá nhân không cần thiết; không đọc secret chỉ để lấp khoảng trống context. Nếu việc redaction có thể thay đổi semantics, dừng và tìm cách cung cấp nguồn an toàn hơn.

## Evidence

Trả manifest/version, source revision, required/provided/missing ranges, file hashes, dependency coverage, invariant checks, budget và các giới hạn chưa giải quyết. Phân biệt `complete`, `incomplete`, `stale`, `blocked` nếu engine hỗ trợ; nếu không, giữ trạng thái gốc của engine và mô tả kết quả rõ ràng. Không tuyên bố packet đầy đủ nếu dependencies chỉ được giả định.

## Failure handling

Nguồn stale, missing range, hash/content mismatch, encoding/truncation, acceptance đổi hoặc budget vượt: từ chối packet và điều tra phạm vi thiếu trước khi gọi model. Không bỏ assertion, giả source hash, nới acceptance hoặc chọn nguồn khác âm thầm. Nếu không xác định được dependency cần thiết, báo blocker/unknown thay vì tự chứng nhận đủ.

## Stop conditions

Dừng khi packet đáp ứng manifest đã đóng băng hoặc phần còn thiếu/không thể xác minh được liệt kê rõ. Không tự nhận biết mọi dependency, không hạ model/effort, không đọc secret và không bỏ yêu cầu an toàn để giảm context.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và `--project-root`.
