# OMEGA plugin evals

Đo OMEGA bằng `claude plugin eval`, có nhánh không plugin để so sánh (Δ = điểm có plugin − không plugin).

```bash
claude plugin eval . --scaffold --trust-plugin --no-publish --case <tên-case> --allow-tools Bash
```

- `--scaffold` chạy `scaffold.sh` của case: chép bản commit HEAD của repo (kèm `node_modules` TypeScript nếu có) vào workspace và commit làm baseline. Không có cờ này thì workspace trống và mọi kết quả đều vô nghĩa.
- Case dùng Bash cần sandbox: `bubblewrap` và `socat`.
- `--case` lặp lại chỉ nhận giá trị cuối; chạy từng case một.
- Harness quét cả bản xuất cũ trong `.omega/plugin-packaging/runs/*/marketplace/evals`; tên case phải khác các bản cũ đó (`gate-report`, `no-git-root`, `change-plan`).

## Đo token và công cụ (P0 của kế hoạch 0.8)

`aggregate-result.json` chỉ có điểm, chi phí, thời gian và số lượt. Token và số lần gọi công cụ nằm trong trace của từng lượt, chỉ được giữ khi chạy với `--keep-temp`:

```bash
claude plugin eval . --scaffold --trust-plugin --no-publish --keep-temp --case <tên-case> --allow-tools Bash Edit --output-dir /tmp/run-x
python3 benchmarks/eval_metrics.py current=/tmp/run-x --json /tmp/run-x/metrics.json
```

- Token lấy từ event `result` cuối trace (số runtime báo): input, cache read, cache write, output. `mean_input_tokens` là tổng ba loại input. Lượt không có trace để token là `null`; không quy đổi byte thành token.
- Số lần gọi công cụ và skill được gọi đếm từ các khối `tool_use`.
- `cost_per_success_usd` là tổng chi phí chia số lượt đạt; không xác định khi không lượt nào đạt.
- So sánh A/B/C: chạy suite với plugin hiện tại (nhánh `with` = B, `without` = A) và với checkout của bản ứng viên (nhánh `with` = C), rồi truyền cả hai thư mục: `current=DIR1 candidate=DIR2`.
- Lượt chạy có `error` (giới hạn phiên, lỗi API, scaffold lỗi) không được chấm: báo riêng ở `errored_runs`, không tính vào tỉ lệ thành công hay token.
- Số đo đầu tiên (`fix-runner-bug-omega`, nhánh có OMEGA, 3 lượt đạt): trung bình 158.801 token input (gần hết là cache read), 1.433 token output, 7 lần gọi công cụ (Skill 1, Bash 3–4, Read 1–2, Edit 1), $0.112 mỗi lượt thành công. Nhánh không OMEGA và case `shared-helper-bug-omega` dừng vì hết giới hạn phiên, nên chưa có số so sánh.
- Giới hạn: harness tự quyết thứ tự chạy các nhánh (chưa hoán đổi được), và mỗi lượt `--keep-temp` để lại một thư mục `/tmp/claude-eval-*` khoảng 250 KB cần tự xoá.

## Baseline sạch: project `ledger` (tag `external`)

Project mẫu `evals/fixtures/ledger` không có file nào của OMEGA, nên nhánh không plugin là Claude Code thuần (0 lượt gọi skill). Lỗi cài sẵn: `parse_amount` cắt cụt sai số dấu phẩy động, làm fail test được nêu và một test ở file khác. 10 lượt mỗi nhánh, có trace, tổng $3.36. Số liệu từng lượt: [results-ledger-ab.json](results-ledger-ab.json).

| Prompt | Nhánh | Đạt | Chi phí / lượt đạt | Token input TB | Token output TB | Gọi công cụ TB | Thời gian TB |
|---|---|---|---|---|---|---|---|
| Thường | có plugin | 10/10 | $0.0767 | 116.080 | 1.478 | 6,2 | 38,9 s |
| Thường | không plugin | 10/10 | $0.0752 | 117.735 | 1.461 | 6,8 | 35,6 s |
| Nhắc OMEGA | có plugin | 10/10 | $0.1016 | 162.787 | 1.971 | 7,4 | 41,0 s |
| Nhắc OMEGA | không plugin | 9/10 | $0.0918 | 127.119 | 1.911 | 7,0 | 40,7 s |

- Prompt thường: skill được gọi 0/10 lượt; cài plugin không đổi kết quả hay chi phí (chênh 2%, trong phạm vi nhiễu).
- Prompt nhắc OMEGA: skill được gọi 10/10 lượt. Chất lượng ngang nhau: lượt trượt duy nhất của nhánh không plugin thực ra sửa đúng (`Decimal` trong `parse_amount`, 3/3 test pass), judge chấm sai. Overhead khi OMEGA chạy: +35.668 token input mỗi tác vụ (+28%), +11% chi phí mỗi lượt thành công, thời gian gần như không đổi.

### Bảng quyết định (mục 8 của PLAN_0_8)

| Mục | Nội dung |
|---|---|
| Giả thuyết | Quy trình OMEGA (skill omega) làm sửa lỗi đúng hơn hoặc rẻ hơn |
| Baseline / candidate | Claude Code không plugin / Claude Code + plugin omega 0.7.4, cùng model và prompt |
| Task | Sửa lỗi trong hàm dùng chung trên project ngoài (`ledger`) |
| Token / chi phí | +28% token input, +11% chi phí mỗi lượt thành công khi skill chạy |
| Chất lượng | Ngang nhau (10/10 so với 10/10 sau khi trừ một lượt judge chấm sai) |
| Độ trễ, công cụ | 41,0 s so với 40,7 s; 7,4 so với 7,0 lần gọi công cụ |
| Tập xác nhận | Chưa có; mới một task |
| Quyết định | `keep experimental`: không đạt ngưỡng giảm 15% của kế hoạch, và không cải thiện chất lượng. Không nên mở rộng tự gọi skill. |

## Cảnh báo: baseline của các case chép repo OMEGA không sạch

`evals/scaffold.sh` chép nguyên repo OMEGA vào workspace, kể cả `.claude/skills/omega/SKILL.md` và `.claude/CLAUDE.md`. Claude Code nạp hai file này từ thư mục làm việc, nên ở mọi case dùng scaffold đó, nhánh "không plugin" vẫn có quy tắc OMEGA trong context và có thể gọi project skill `omega`. Trong lần đo `fix-runner-bug-omega` 10 lượt mỗi nhánh, 3/10 lượt của nhánh không plugin đã gọi skill `omega`.

Không thể xoá `.claude/` khỏi bản chép vì test của repo đọc chính các file đó. Vì vậy Δ của các case dưới đây chỉ so sánh "plugin + file dự án OMEGA" với "chỉ file dự án OMEGA", không phải với Claude Code không có OMEGA. Baseline sạch dùng project mẫu ở `evals/fixtures/` (tag `external`).

Lần đo `fix-runner-bug-omega` (10 lượt mỗi nhánh, có trace, $2.32): cả hai nhánh 10/10 đạt. Có plugin: $0.108 mỗi lượt thành công, 162.133 token input, 1.417 token output, 7,0 lần gọi công cụ. Không plugin (nhưng có file dự án OMEGA): $0.125, 174.021, 1.926, 8,6.

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
- Sau khi sửa engine cho checkout chỉ đọc (0.7.4), chạy lại `gates-status` 3 lần mỗi nhánh: có OMEGA 1.00, không OMEGA 1.00 (Δ 0, $0.79). Cả 3 lần nhánh có OMEGA đều chạy được `omega gates` (4 gate pass, 217 test) và báo rõ evidence không được lưu.
- Harness cũng chạy các bản `gates-status` cũ trong `.omega/plugin-packaging/runs/*/marketplace/evals` (do `benchmarks/plugin_packaging.py` xuất ra); chúng lỗi ở bước scaffold và không tốn chi phí, nhưng làm nhiễu báo cáo. Bỏ qua các dòng có `dir` nằm trong `.omega/`.
- Chưa đo được: tỉ lệ gọi skill ở các case không có grader `tool_used`, và chất lượng trên project khác ngoài chính repo này.

## Thay đổi code có kiểm soát (tag `phase2`)

Bash trong sandbox chỉ đọc, nhưng công cụ Write/Edit ghi được vào workspace, nên case sửa code đo được. Scaffold cài sẵn một lỗi: `omega/test_runner.py` trả `>=0` thay vì `>0`, làm 3 test trong `tests/test_hardening.py` đỏ. Chạy với `--allow-tools Bash Edit`, 3 lần mỗi nhánh.

| Case | Có OMEGA | Không OMEGA | Skill được gọi | Chi phí có / không |
|---|---|---|---|---|
| `fix-runner-bug` (prompt thường) | 1.00 | 1.00 | 0/3 | $0.087 / $0.076 |
| `fix-runner-bug-omega` (prompt nhắc OMEGA) | 1.00 | 1.00 | 3/3 | $0.101 / $0.115 |

- Với yêu cầu sửa lỗi thông thường, Claude không tự gọi skill omega, dù description có nêu "sửa code có kiểm soát".
- Khi được gọi, OMEGA cho cùng kết quả: cả hai nhánh tìm đúng dòng, sửa một dòng, không đụng test, chạy lại test và báo 30/30 pass.
- Lỗi cài sẵn dễ nên cả hai nhánh đều đạt điểm tối đa; cần case khó hơn (nhiều file, có cám dỗ sửa test hoặc mở rộng phạm vi) mới phân biệt được.

## Lỗi trong hàm dùng chung (tag `phase3`)

Scaffold đổi `passed<=0` thành `passed<0` trong `normalized()` của `omega/adapters.py`, hàm dùng chung cho mọi adapter. Lỗi làm fail test được nêu trong `tests/test_hardening.py` và một test Jest không được nêu trong `tests/test_interop_core.py`. Chạy với `--allow-tools Bash Edit`, 3 lần mỗi nhánh, tổng $1.50.

| Case | Có OMEGA | Không OMEGA | Skill được gọi | Chi phí có / không |
|---|---|---|---|---|
| `shared-helper-bug` (prompt thường) | 1.00 | 0.75 | 0/3 | $0.102 / $0.103 |
| `shared-helper-bug-omega` (prompt nhắc OMEGA) | 0.75 | 0.75 | 3/3 | $0.118 / $0.175 |

- Δ +0.25 của case prompt thường là nhiễu: skill không được gọi lần nào nên plugin không ảnh hưởng.
- Khi OMEGA được gọi, hai nhánh bằng nhau. Nhánh có OMEGA tốn ít hơn ($0.118 so với $0.175, ít lượt hơn), nhưng mới có 3 lần chạy.
- Mọi lần chạy đều chạy toàn bộ suite (218 test). Cả 3 lần trượt (mỗi nhánh có một) đều cùng một cách sửa sai: thêm `run<1` thay vì khôi phục `passed<=0`. Suite vẫn xanh nhưng báo cáo chỉ có test bị skip vẫn được chấp nhận. Đây là lỗ hổng của bộ test repo, không phải của judge; đã thêm `test_counts_without_a_passing_test_are_rejected` để bắt cách sửa này.
