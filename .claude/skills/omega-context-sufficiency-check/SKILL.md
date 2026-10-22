---
name: omega-context-sufficiency-check
description: Kiểm tra packet context có giữ nguồn và yêu cầu bắt buộc trước khi tối ưu token.
disable-model-invocation: true
---

# OMEGA context-sufficiency-check

## Inputs

Requirements manifest gồm source ranges, acceptance/constraints; packet có nội dung và source hashes.

## Workflow

Chạy `python3 -m omega context-sufficiency-check --input INPUT --compact`. Kiểm tra ranges, actual content/full-file hash và task invariants. Khi thiếu dependency, mở rộng manifest/packet có chủ đích thay vì tự cắt source.

## Evidence

Trả required/provided ranges, missing/altered inputs và giới hạn. Byte giảm không chứng minh token hoặc chất lượng LLM không đổi.

## Failure handling

Nguồn stale, missing range, đổi acceptance hoặc budget vượt: từ chối packet; không bỏ assertion hoặc giả source hash. Điều tra phạm vi thiếu trước gọi model.

## Stop conditions

Dừng khi đáp ứng manifest hoặc chỉ rõ phần còn thiếu. Không tự biết mọi dependency; không hạ model/effort, đọc secret hoặc bỏ yêu cầu an toàn để giảm context.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
