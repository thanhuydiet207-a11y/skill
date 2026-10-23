# OMEGA workflow-handoff-contract

## Inputs

Workflow nodes, một orchestrator, owner cho Git/gates/memory, exact write paths, dependencies và budget.

## Workflow

Khai reads/writes cho exact files và read_dirs/write_dirs cho subtree; liệt kê đầy đủ nguồn đọc có thể bị writer khác thay đổi. Đặt dependency để reader đi sau writer, không dựa vào batch budget tình cờ tuần tự. Orchestrator phải đi trước workers; glob/field viết sai cần sửa. Contract fail không có schedule khả dụng, validator không khóa tiến trình; xem docs/UPGRADE_0_4.md.

Chạy `python3 -m omega workflow-handoff-contract --input INPUT --compact`. Kiểm tra DAG, duplicate IDs/owners và writer chưa có thứ tự. Dùng lịch batch trong budget; orchestration runtime vẫn do người điều phối thực hiện.

## Evidence

Trả issues, schedule, owners theo input và giới hạn. Handoff phải giữ objective, acceptance, scope và refs; không gửi toàn transcript.

## Failure handling

Có cycle, hai owner hoặc path escape: dừng giao việc và sửa contract có review. Không giải quyết bằng spawn thêm agent hoặc tạo branch/worktree chồng nhau.

## Stop conditions

Dừng khi contract đạt hoặc xung đột đã được chỉ rõ. Công cụ không dispatch agent, không thay branch hoặc tự chọn quy trình có quyền cao hơn.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
