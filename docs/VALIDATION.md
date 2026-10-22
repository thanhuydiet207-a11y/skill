# Kết quả thực thi

Bản 0.2 hiện tại: **82 tests pass**, required gates, demo và benchmark context đạt. Mỗi skill có offline contract và workflow scenario evaluation; xem [deep-hardening.json](evidence/deep-hardening.json) và [giới hạn kiểm chứng](DEEP_HARDENING.md). Các báo cáo bootstrap/token bên dưới là bằng chứng lịch sử, không phải hash nguồn hiện tại.

Demo mới đã sửa trường hợp timestamp/size cache Python khiến test đọc bytecode cũ khi fixture sửa nhanh: compile bắt buộc với `checked-hash`; không xóa cache hoặc trì hoãn bằng sleep.

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

## Lịch sử kiểm tra ban đầu và các giới hạn

- Ban đầu không tìm thấy Claude. Đợt 0.2 đã cài tool cục bộ 2.1.308 và chạy version/help; chưa có phiên xác thực nên slash skills/native agents/hooks vẫn chưa được nghiệm thu.
- Tải docs chính thức `https://code.claude.com/docs/en/{hooks,sub-agents,skills}` trả HTTP 403. Không đoán schema rồi bật hook.
- Kiểm tra Git đầu tiên báo thiếu xác thực; thao tác sau đó đã thành công qua cấu hình sẵn có, không thêm token. Đã push commit triển khai `0f4033c4ce46940dd6ecd192d7a25e59b9bad36d` lên `omega/bootstrap` và đối chiếu SHA remote bằng `git ls-remote`.
- CI workflow đã được push. `gh run list` qua `api.github.com` trả `Forbidden`; trạng thái thực thi CI chưa xác minh được từ môi trường này. Không tạo PR hoặc merge vào main.
- Bộ đếm token/cost, điều phối Claude tự động, native multi-run evaluation, SAST và 31 skill/7 agent roadmap chưa triển khai.

## Chạy lại khi có thay đổi liên quan

```bash
python3 -m omega gates
python3 benchmarks/demo.py
python3 -m omega rollback-check
```

Không chạy lặp vô hạn để tăng số lượng kết quả. Thay đổi benchmark cần baseline mới và review; không sửa kỳ vọng chỉ để làm xanh.
