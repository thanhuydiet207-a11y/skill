---
name: omega-skill-compatibility-audit
description: Kiểm tra xung đột tên, hook và workflow khi kết hợp các bộ skill.
disable-model-invocation: true
---

# OMEGA skill-compatibility-audit

## Inputs

Roots skill/config hook tường minh, phạm vi được phép đọc và workflow contract nếu có.

## Workflow

Chạy `python3 -m omega skill-compatibility-audit --skill-root .claude/skills --compact`; lặp --skill-root/--hook-config khi đã được phép đọc. Không cài hoặc chạy skill đang kiểm tra. Đọc findings, complete_for_selected_roots và phạm vi chưa quan sát; chỉ so sánh identity, metadata, hook events và contract được cung cấp.

## Evidence

Trả roots đã quét, hashes, các tên trùng, event chồng và điều cần native test. passed không phải chứng nhận tương thích.

## Failure handling

Syntax YAML chưa hỗ trợ hoặc source thiếu/symlink: đánh dấu cần review; không tự gọi là skill không hợp lệ với Claude. Không bỏ qua root chưa quét để báo hoàn tất.

## Stop conditions

Dừng khi ma trận xung đột/phần chưa biết đủ rõ để chọn một workflow owner; không tự tắt plugin, sửa policy hoặc nâng quyền.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
