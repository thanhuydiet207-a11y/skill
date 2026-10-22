# Kết quả thực thi

Bằng chứng máy đọc: [local-validation.json](evidence/local-validation.json), gồm argv, exit code, duration, output, hash nguồn và kết quả demo. Log local đầy đủ theo mức giữ output nằm trong `.omega/` (không commit). Record được review thủ công, không phải chứng thực ký số.

## Đã chạy

- Python 3.12.14; Git 2.52.0; không cài package mới.
- Build `compileall`: exit 0.
- 21 unittest: pass, gồm router, catalog, candidate/stable lifecycle, thay suite, command failure, timeout, shell literal, path traversal, symlink escape, dirty tree, memory filtering và hook deny.
- Regression: 3 router contract cases pass. Đây không phải số liệu hiệu quả LLM.
- Security gate: narrow bypass-pattern audit pass; không phải SAST/dependency/security assurance toàn diện.
- Demo: test cộng số fail trước sửa và pass sau sửa; branch `omega/demo-fix`, worktree riêng, memory/evidence, baseline Git truy xuất được, candidate pass và stable giữ nguyên.
- `rollback-check`: HEAD hợp lệ và diff check exit 0; không rollback production.
- Candidate baseline/candidate compare: pass; không promote hoặc sửa stable.

## Lỗi thực tế đã xử lý

| Vấn đề | Xử lý |
|---|---|
| Candidate ban đầu so với file stable trực tiếp | Tạo candidate riêng, reject nếu stable đổi |
| Benchmark chỉ so tên suite và ID | Hash full fixture và implementation vào baseline |
| Output Git có thể cắt im lặng | Flag truncation và từ chối dùng Git control data thiếu |
| Hook có thể sửa `.env` | Chặn `.env` và `.env.*`; adapter vẫn tắt |

## Chưa xác minh / blocker

- Không tìm thấy executable `claude`; không có phiên bản Claude để xác minh. Chưa chạy slash skills hoặc native agents/hooks.
- Tải docs chính thức `https://code.claude.com/docs/en/{hooks,sub-agents,skills}` trả HTTP 403. Không đoán schema rồi bật hook.
- `git ls-remote origin refs/heads/main` báo `could not read Username for 'https://github.com'`. Quyền đọc ở phiên onboarding trước không bảo đảm quyền hiện tại.
- CI workflow được thêm nhưng chưa chạy trên GitHub. Push/PR chỉ có thể xác nhận khi remote nhận commit.
- Bộ đếm token/cost, điều phối Claude tự động, native multi-run evaluation, SAST và 31 skill/7 agent roadmap chưa triển khai.

## Chạy lại khi có thay đổi liên quan

```bash
python3 -m omega gates
python3 benchmarks/demo.py
python3 -m omega rollback-check
```

Không chạy lặp vô hạn để tăng số lượng kết quả. Thay đổi benchmark cần baseline mới và review; không sửa kỳ vọng chỉ để làm xanh.
