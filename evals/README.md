# OMEGA plugin evals

Đo OMEGA bằng `claude plugin eval`, có nhánh không plugin để so sánh (Δ = điểm có plugin − không plugin).

```bash
claude plugin eval . --scaffold --trust-plugin --no-publish --case <tên-case> --allow-tools Bash
```

- `--scaffold` chạy `scaffold.sh` của case: chép bản commit HEAD của repo (kèm `node_modules` TypeScript nếu có) vào workspace và commit làm baseline. Không có cờ này thì workspace trống và mọi kết quả đều vô nghĩa.
- Case dùng Bash cần sandbox: `bubblewrap` và `socat`.
- `--case` lặp lại chỉ nhận giá trị cuối; chạy từng case một.
- Harness quét cả bản xuất cũ trong `.omega/plugin-packaging/runs/*/marketplace/evals`; tên case phải khác các bản cũ đó (`gate-report`, `no-git-root`, `change-plan`).

## Kết quả bước 0 (1 lần chạy mỗi nhánh, chưa có ý nghĩa thống kê)

| Case | Có OMEGA | Không OMEGA | Ghi chú |
|---|---|---|---|
| `empty-suite` | 1.00 | 1.00 | Điều tra code thuần; cả hai nhánh chỉ đúng file và dòng |
| `doctor-outside-git-plan` | 1.00 | 1.00 | Lập kế hoạch; cả hai đạt |
| `gates-status` | 0.00 | 1.00 | Workspace của sandbox chỉ đọc, engine không tạo được `.omega/`; skill cấm thay bằng lệnh tự chạy nên dừng ở "chưa chạy". Nhánh không plugin chạy thẳng `unittest` (215 test) và báo trung thực |

Phát hiện: OMEGA không chạy được trên checkout chỉ đọc vì cả `doctor` lẫn `gates` đều ghi state vào `.omega/` trong project.

## Kết quả giai đoạn 1 (8 case, 3 lần mỗi nhánh)

Chạy với `--tag phase1 --runs 3 --scaffold --allow-tools Bash`. Điểm là trung bình 3 lần; chi phí là trung bình mỗi lần chạy.

| Case | Có OMEGA | Không OMEGA | Δ | Chi phí có / không |
|---|---|---|---|---|
| `doctor-outside-git-plan` | 1.00 | 1.00 | 0 | $0.270 / $0.249 |
| `empty-suite` | 1.00 | 1.00 | 0 | $0.168 / $0.137 |
| `gates-status` | 0.67 | 1.00 | −0.33 | $0.096 / $0.156 |
| `hook-status` | 1.00 | 1.00 | 0 | $0.105 / $0.100 |
| `jest-report` | 1.00 | 1.00 | 0 | $0.113 / $0.082 |
| `quick-question` | 1.00 | 0.67 | +0.33 | $0.030 / $0.028 |
| `release-files` | 1.00 | 1.00 | 0 | $0.101 / $0.102 |
| `stale-evidence` | 1.00 | 1.00 | 0 | $0.094 / $0.113 |

Trung bình mỗi lần chạy: $0.122 có OMEGA, $0.121 không OMEGA. Tổng chi phí giai đoạn 1 khoảng $6.8.

- Chưa có case nào OMEGA làm tốt hơn. Δ +0.33 của `quick-question` là nhiễu: plugin không tham gia (skill được gọi 0/3 lần, đúng mong muốn), và nhánh không plugin sai một lần ở câu hỏi Python đơn giản. Độ nhiễu của judge với 3 lần chạy vì thế khoảng ±0.33.
- `gates-status` là thiệt hại thật: skill được gọi 3/3 lần, engine không ghi được `.omega/` trong workspace chỉ đọc, và skill cấm tự chạy lệnh thay engine. Nhánh không plugin chạy thẳng từng lệnh gate và báo được nhiều hơn.
- Grader của `stale-evidence` và `quick-question` đã sửa sau lần chạy đầu (tiêu chí quá hẹp; thiếu `min: 0`); số liệu trong bảng là của lần chạy lại sau khi sửa.
- Chưa đo được: thay đổi code có kiểm soát (workspace của eval chỉ đọc), tỉ lệ gọi skill ở các case không có grader `tool_used`, và chất lượng trên project khác ngoài chính repo này.
