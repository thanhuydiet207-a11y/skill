---
name: omega-workflow-handoff-contract
description: Kiểm tra phân công và lịch phối hợp khi nhiều skill hoặc agent cùng làm việc.
disable-model-invocation: true
---

# OMEGA workflow-handoff-contract

## Inputs

Workflow nodes, một orchestrator, owner cho Git/gates/memory, exact write paths, dependencies và budget.

## Workflow

Chạy `python3 -m omega workflow-handoff-contract --input INPUT --compact`. Kiểm tra DAG, duplicate IDs/owners và writer chưa có thứ tự. Dùng lịch batch trong budget; orchestration runtime vẫn do người điều phối thực hiện.

## Evidence

Trả issues, schedule, owners theo input và giới hạn. Handoff phải giữ objective, acceptance, scope và refs; không gửi toàn transcript.

## Failure handling

Có cycle, hai owner hoặc path escape: dừng giao việc và sửa contract có review. Không giải quyết bằng spawn thêm agent hoặc tạo branch/worktree chồng nhau.

## Stop conditions

Dừng khi contract đạt hoặc xung đột đã được chỉ rõ. Công cụ không dispatch agent, không thay branch hoặc tự chọn quy trình có quyền cao hơn.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
