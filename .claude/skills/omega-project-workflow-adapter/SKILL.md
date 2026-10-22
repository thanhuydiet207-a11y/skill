---
name: omega-project-workflow-adapter
description: Đề xuất build/test adapter phù hợp repository đích mà không tự cài dependency.
disable-model-invocation: true
---

# OMEGA project-workflow-adapter

## Inputs

Root Git tường minh, manifests/CI và quyền đọc project; xác định engine runner riêng với target.

## Workflow

Chạy `python3 -m omega project-workflow-adapter --compact`. Đối chiếu proposals với scripts và runner thật; review đầy đủ argv build/tests/security/regression trước lưu config riêng. Dùng runner tuyệt đối và --project-root ở project ngoài OMEGA.

## Evidence

Trả stack, command proposal, assumption về adapter và missing requirements; proposal-needs-review không phải ready.

## Failure handling

Không nhận diện được stack hoặc thiếu security/regression: báo yêu cầu cụ thể. Jest/Go/JUnit output không đúng schema thì không thay bằng exit-zero-only.

## Stop conditions

Dừng khi có proposal để review hoặc blocker rõ ràng. Không tự npm/pip install, sửa manifest/lockfile, tạo config hoặc tuyên bố mọi framework đã được native test.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
