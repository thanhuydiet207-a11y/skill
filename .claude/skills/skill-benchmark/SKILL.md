---
name: skill-benchmark
description: Đánh giá hồi quy skill bằng fixture trước khi đề xuất nâng phiên bản.
disable-model-invocation: true
---

# OMEGA skill-benchmark

Chạy `python3 -m omega benchmark` và `python3 -m omega gates`. Benchmark kiểm tra hợp đồng router/safety trên fixture; không đo chất lượng suy luận LLM. Khi thay skill, chạy `python3 -m omega candidate --skill TEN` để tạo baseline và bản sao trong `.omega/candidates/`. Chỉ sửa bản sao candidate, giữ nguyên stable; chạy `python3 -m omega compare --baseline DUONG_DAN` sau sửa. Không tự quảng bá phiên bản stable: cần tất cả gates pass, review diff và người dùng duyệt. Nếu không có Claude, đánh dấu native evaluation chưa chạy. Giữ baseline bên ngoài diff ứng viên để so sánh.

Dùng checkout hiện tại; không tạo worktree trừ khi cần cô lập thay đổi xung đột đã được ủy quyền. Đọc `CLAUDE.md` và `docs/OPERATIONS.md`. CLI Python phải chạy từ gốc repository, không cần pip install.
