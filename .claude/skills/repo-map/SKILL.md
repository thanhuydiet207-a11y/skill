---
name: repo-map
description: Phân tích repository với bằng chứng trước khi lập kế hoạch.
disable-model-invocation: true
---

# OMEGA repo-map

Chạy `python3 -m omega map` tại gốc repository. Đọc inventory và Git status; chỉ mở các file liên quan trong ngân sách context. Không coi số file là bằng chứng ứng dụng hoạt động. Dùng `python3 -m omega plan --complexity low` để chọn luồng. Báo các manifest, tests và giới hạn chưa biết.

Dùng checkout hiện tại; không tạo worktree trừ khi cần cô lập thay đổi xung đột đã được ủy quyền. Đọc `CLAUDE.md` và `docs/OPERATIONS.md`. CLI Python phải chạy từ gốc repository, không cần pip install.
