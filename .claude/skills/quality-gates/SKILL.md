---
name: quality-gates
description: Chạy build, tests, security, regression với bằng chứng exit code.
disable-model-invocation: true
---

# OMEGA quality-gates

Chạy `python3 -m omega gates`; đọc từng exit code, timeout và output. Gates không thay thế review bảo mật; audit chỉ kiểm tra hẹp được tài liệu hóa. Không bỏ qua gate thất bại. Nếu fail: phân loại setup/bug, tối đa 2 lượt sửa trong 30 phút rồi báo blocker. Kiểm tra rollback bằng `python3 -m omega rollback-check`. Không thực hiện rollback phá hủy tự động.

Dùng checkout hiện tại; không tạo worktree trừ khi cần cô lập thay đổi xung đột đã được ủy quyền. Đọc `CLAUDE.md` và `docs/OPERATIONS.md`. CLI Python phải chạy từ gốc repository, không cần pip install.
