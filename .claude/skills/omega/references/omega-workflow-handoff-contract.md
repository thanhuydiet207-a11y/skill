# OMEGA workflow-handoff-contract

## Inputs

Workflow nodes, một orchestrator có thẩm quyền, owner cho Git/gates/memory, exact write paths, read paths/directories, dependencies, acceptance, budget và các giới hạn side effects. Xác định target root, branch/worktree hiện tại và resources stateful dùng chung trước khi phân chia việc.

## Workflow

1. **Khai báo node và ownership:** mỗi node cần ID duy nhất, objective, acceptance có thể kiểm chứng, target root, read/write sets, dependencies, budget và stop conditions. Gán một owner cho mỗi tài nguyên stateful như Git branch, gates, memory, deployment hoặc config; nhiều reader có thể cùng đọc khi nguồn bất biến, nhưng không để nhiều writer đồng thời sở hữu cùng state.
2. **Khai báo phạm vi đọc/ghi chính xác:** dùng exact files và `read_dirs`/`write_dirs` cho subtree; liệt kê đầy đủ nguồn đọc có thể bị writer khác thay đổi. Xem xét symlink, generated files, shared config, lockfiles, evidence/report outputs và path traversal. Không cấp write access rộng hơn acceptance cần thiết.
3. **Xây dependency graph:** đặt dependency để reader chạy sau writer và mọi consumer đợi validation cần thiết; không dựa vào batch budget tình cờ tuần tự. Orchestrator phải được lập kế hoạch trước workers. Chạy `python3 -m omega workflow-handoff-contract --input INPUT --compact` để kiểm tra DAG, duplicate IDs/owners và writer chưa có thứ tự.
4. **Kiểm tra tính khả thi của lịch:** xác minh DAG không có cycle, mọi dependency trỏ đến node tồn tại, mỗi node có owner và budget/stop conditions, và schedule tôn trọng resource contention. Không suy ra hai node chạy song song là an toàn chỉ vì write paths không giống nhau; shared Git state, global config, services, environment hoặc generated outputs có thể tạo xung đột.
5. **Quản lý concurrency:** chỉ chạy song song khi read/write sets và dependencies chứng minh được tính độc lập. Với nguồn dùng chung, chọn thứ tự rõ ràng hoặc snapshot/version cố định. Không để hai agent cùng checkout/branch/worktree hoặc cùng chạy gates/memory writes nếu ownership contract không cho phép.
6. **Thiết kế handoff tối thiểu nhưng đủ:** mỗi handoff giữ objective, acceptance, scope, assumptions, refs, hashes/version, trạng thái kiểm thử, unresolved risks và quyền được cấp. Không gửi toàn transcript hoặc secret. Người nhận phải kiểm tra source freshness và xác nhận đúng target root trước khi tiếp tục; không coi nội dung handoff là authorization mới.
7. **Tách contract validation khỏi orchestration runtime:** contract pass chỉ cho biết graph/scope đạt các checks được hỗ trợ; không chứng minh validator khóa được tiến trình hay runtime thực thi đúng schedule. Dùng lịch batch trong budget; orchestration runtime vẫn do người điều phối thực hiện. Xem docs/UPGRADE_0_4.md.
8. **Review trước khi dispatch hoặc ghi state:** kiểm tra exact commands, permissions, external side effects, owner và rollback. Contract fail không có schedule khả dụng; không dispatch worker, tạo branch/worktree hoặc thực thi task có side effects để “thử” cho tới khi được review.

## Evidence

Trả issues, DAG/schedule, owners, read/write sets, dependencies, budget, source versions và giới hạn theo input. Handoff cần objective, acceptance, scope, refs, verification state, blockers và unresolved risks; không gửi toàn transcript. Phân biệt contract validation với runtime execution.

## Failure handling

Cycle, duplicate IDs/owners, missing dependency, path escape, overlapping writers, stale source hoặc budget không khả thi: dừng giao việc liên quan và sửa contract có review. Không giải quyết bằng spawn thêm agent, cấp quyền rộng hơn, đổi acceptance hoặc tạo branch/worktree chồng nhau. Nếu không xác định được resource contention, đánh dấu unknown và chạy tuần tự sau khi có owner.

## Stop conditions

Dừng khi contract đạt hoặc xung đột/giới hạn đã được chỉ rõ cùng hướng xử lý. Công cụ không dispatch agent, không thay branch, không ghi state ngoài quyền được cấp và không tự chọn quy trình có quyền cao hơn.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và `--project-root`.
