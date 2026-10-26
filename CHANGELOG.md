# Changelog

Cập nhật bản cài: `claude plugin marketplace update omega-marketplace` rồi `claude plugin update omega@omega-marketplace`.

## 0.7.3

- `omega/catalog.json` chỉ còn 13 chế độ đã triển khai. 31 capability và 7 vai trò agent chưa có file chuyển sang [docs/ROADMAP.md](docs/ROADMAP.md).
- Thêm bộ eval `evals/` cho `claude plugin eval`, so sánh có và không có plugin. Giai đoạn 1 (8 case, 3 lần mỗi nhánh) chưa có case nào OMEGA làm tốt hơn; `gates-status` kém hơn vì engine không ghi được `.omega/` trên checkout chỉ đọc. Chi tiết: [evals/README.md](evals/README.md).

## 0.7.2

- `--project-root` không phải Git repo giờ báo hướng dẫn `git init` và commit, thay cho lỗi thô `fatal: not a git repository`. Mã thoát vẫn là 2.
- Lỗi trong `setUpClass` hoặc module setup không còn làm số `passed` bị âm.

## 0.7.1

- Claude có thể tự gọi skill `omega` khi tác vụ khớp description; `/omega:omega` vẫn dùng được. Description nói rõ khi nào dùng và khi nào không.
- Subtest fail được đếm một lần cho mỗi test method; trước đó số `passed` có thể âm.
- README và `docs/CLAUDE_PLUGIN.md` có lệnh cập nhật plugin.
- TypeScript 7.0.2 và `@types/node` 24.19.2 cho build bridge.

## 0.7.0

- Đóng gói OMEGA thành plugin Claude Code với marketplace tự host trên GitHub.
