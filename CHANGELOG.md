# Changelog

Cập nhật bản cài: `claude plugin marketplace update omega-marketplace` rồi `claude plugin update omega@omega-marketplace`.

## Chưa phát hành

- `benchmarks/plugin_packaging.py` không xuất `evals/` nữa, để harness eval không chạy trùng các bản sao trong `.omega/plugin-packaging/`.
- Thêm case eval sửa code có kiểm soát (`fix-runner-bug`, `fix-runner-bug-omega`); kết quả trong [evals/README.md](evals/README.md).
- Test mới chặn báo cáo có test chạy nhưng không test nào pass (ví dụ chỉ có test bị skip); eval `phase3` cho thấy cách sửa `run<1` lọt qua bộ test cũ.
- Thêm case eval `shared-helper-bug` và `shared-helper-bug-omega`.
- Project mẫu `evals/fixtures/ledger` cho baseline sạch; các case chép repo OMEGA để lộ `.claude/` cho cả nhánh không plugin. Kết quả A/B 10 lượt mỗi nhánh: khi skill chạy, +28% token input và +11% chi phí mỗi lượt thành công, chất lượng ngang nhau; quyết định `keep experimental`.
- Kế hoạch 0.8 ([docs/PLAN_0_8.md](docs/PLAN_0_8.md)), bắt đầu từ P0: `benchmarks/eval_metrics.py` đọc trace của `claude plugin eval` để báo token input/output/cache, số lần gọi công cụ, skill được gọi và chi phí trên mỗi lượt thành công.

## 0.7.4

- Chạy được trên checkout chỉ đọc: `gates` báo đủ kết quả với `evidence: null` và lý do thay vì thoát mã 2 và mất kết quả; gate `build` ghi bytecode ra thư mục tạm; `doctor` kiểm tra Claude bằng config tạm.
- Eval `gates-status` chạy lại sau bản sửa: có và không có OMEGA cùng đạt 1.00 (trước đó 0.67 so với 1.00).

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
