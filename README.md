# Tier

Plugin cho Claude Code tự chọn model và mức effort theo độ phức tạp của tác vụ. Luồng chính chạy bằng agent `tier-router` (Haiku, effort thấp): nó tự trả lời việc đơn giản và giao việc khó hơn cho agent Sonnet (effort trung bình) hoặc Opus (effort cao).

```text
/plugin marketplace add thanhuydiet207-a11y/skill
/plugin install tier@tier-marketplace
```

Khởi động lại phiên để áp dụng. Plugin có `settings.json` đặt `tier-router` làm agent mặc định, nên **mọi phiên** có bật plugin đều chạy qua bộ định tuyến. Tắt bằng `claude plugin disable tier` khi không muốn.

## Ba bậc

| Bậc | Ai làm | Model, effort | Khi nào |
|---|---|---|---|
| direct | `tier-router` | Haiku, low | Câu hỏi, giải thích, tra cứu, hoặc sửa hiển nhiên trong một file không ai phụ thuộc |
| standard | `tier-standard` | Sonnet, medium | Lỗi hoặc tính năng trong vài file, có cách kiểm chứng |
| deep | `tier-deep` | Opus, high | Nguyên nhân chưa rõ liên module, sửa code dùng chung hoặc interface, refactor, có rủi ro, hoặc standard không làm xong |

Router chọn bậc theo 4 tín hiệu: phạm vi ảnh hưởng, mức bất định, rủi ro, khả năng kiểm chứng. Không dựa vào độ dài prompt. Câu trả lời mở đầu bằng một dòng `Tier: ... - lý do`. Nếu standard báo chạm code dùng chung hoặc không xong, router nâng lên deep đúng một lần.

## Đo

Mọi thay đổi phải có số liệu so với Claude Code mặc định (không plugin) trước khi được coi là cải thiện.

```bash
claude plugin eval . --scaffold --trust-plugin --no-publish --keep-temp --allow-tools Bash Edit --output-dir /tmp/run
python3 tools/eval_metrics.py tier=/tmp/run --json /tmp/run/metrics.json
```

Bảng gồm tỉ lệ đạt, chi phí mỗi lượt đạt, token theo model, agent nào được giao việc và model nào thực sự phục vụ. Các lượt có `error` (hết giới hạn phiên, lỗi API) được đếm riêng. `--keep-temp` để lại thư mục `/tmp/claude-eval-*` cần xoá tay. Kết quả: [evals/README.md](evals/README.md). Test của công cụ đo: `python3 -m unittest discover -s tools`.

## Giới hạn đã biết

- Khoá `effort` trong agent không có cách quan sát việc áp dụng; chỉ `model` được xác nhận (model phục vụ lượt chạy đọc được từ trace).
- Phân loại do Haiku làm nên có thể sai: giao thừa gây tốn, giao thiếu gây làm sai. Số liệu trong `evals/README.md` cho biết mức độ.
- Plugin áp dụng cho cả phiên, không theo từng tác vụ; chưa có cách bật theo project ngoài việc bật/tắt plugin.
