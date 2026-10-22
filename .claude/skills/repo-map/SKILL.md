---
name: repo-map
description: Phân tích repository với bằng chứng trước khi lập kế hoạch.
disable-model-invocation: true
---

# OMEGA repo-map

## Inputs

Objective, acceptance và root Git đích tường minh. Xác định engine ở đâu trước khi đọc/sửa; không coi thư mục làm việc tình cờ là project cần thao tác.

## Workflow

1. Trong engine dùng `python3 -m omega doctor --compact` và `python3 -m omega map --compact`. Project khác phải dùng runner tuyệt đối với --project-root; không copy riêng SKILL.md rồi chạy module không rõ nguồn.
2. Đọc metadata manifest/CI/test/source và omitted_count; truy vấn entry point, callers, lockfile, toolchain và regression liên quan. Inventory không phải dependency graph đã hoàn chỉnh.
3. Chỉ nạp nguồn cần thiết bằng context --select. Khi có task manifest, giữ acceptance/constraints và dùng context-sufficiency-check để kiểm tra packet; không gọi byte saving là token saving đã đo.
4. Chạy `python3 -m omega plan --complexity medium --compact` hoặc cung cấp --input với intent/complexity/conflict/workflow rõ ràng. Với nhiều bộ skill, chạy skill-compatibility-audit và chọn đúng một orchestrator trước giao việc.
5. Tách observed facts, hypotheses và unknowns; mỗi giả thuyết có test có thể bác bỏ. Đọc đúng phần cần trong docs/INTEROPERABILITY_GUIDE.md, không preload toàn bộ skill/catalog.

## Evidence

Trả project/branch/HEAD, current changes, source path:line/hash, phần inventory bị giới hạn, dependencies cần xem tiếp và checks bắt buộc/optional. Doctor unknown về hook/MCP không có nghĩa chúng bị tắt.

## Failure handling

Git control vượt giới hạn/encoding sai hoặc thiếu root engine: dừng dùng kết quả thiếu, báo operation cụ thể và phần vẫn xác minh được. Không tự cài gói hoặc chạy script của bộ skill đang kiểm tra để “khảo sát”.

## Stop conditions

Dừng khi có đủ source, scope, acceptance và workflow owner để giao việc, hoặc một prerequisite thật sự chặn tiến triển. Không kết luận nguyên nhân khi chưa tái hiện; không nói đã đọc toàn repo khi còn omitted.
