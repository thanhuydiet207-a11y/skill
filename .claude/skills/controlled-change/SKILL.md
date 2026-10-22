---
name: controlled-change
description: Thực hiện thay đổi có kiểm soát trong branch hoặc worktree riêng.
disable-model-invocation: true
---

# OMEGA controlled-change

Chạy doctor, map, plan. Kiểm tra thay đổi có sẵn; không reset hoặc ghi đè. Dùng `python3 -m omega isolate --name TEN` tạo branch từ HEAD chỉ khi working tree sạch. Nếu cần song song, dùng `--worktree .omega/worktrees/TEN` trong repository. Xác định acceptance và đường rollback trước sửa. Chỉ sửa phạm vi giao; tối đa 2 lần sửa lỗi. Chạy gates, lưu evidence và báo diff. Không push, deploy hoặc xóa dữ liệu nếu chưa được người dùng cho phép riêng.

Dùng checkout hiện tại; không tạo worktree trừ khi cần cô lập thay đổi xung đột đã được ủy quyền. Đọc `CLAUDE.md` và `docs/OPERATIONS.md`. CLI Python phải chạy từ gốc repository, không cần pip install.
