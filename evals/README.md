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
