# Eval của Tier

Mỗi case chạy hai nhánh: có plugin, và không plugin (Claude Code mặc định, Sonnet). Thư mục `fixtures/` là project mẫu không có file nào của plugin, nên nhánh không plugin là baseline sạch. `scaffold.sh` của mỗi case chép fixture vào workspace và commit.

| Case | Bậc kỳ vọng | Lỗi cài sẵn |
|---|---|---|
| `trivial-question` | direct | Không có (câu hỏi Python) |
| `tiny-bug` | direct hoặc standard | `slugify` dùng `_` thay `-`, một file |
| `ledger-bug` | standard | `parse_amount` cắt cụt số thực, dùng chung bởi 2 module; làm đỏ test ở 2 file |

Bậc kỳ vọng là nhận định ban đầu, không phải đáp án đúng duy nhất: tiêu chí đánh giá chính là tỉ lệ đạt và chi phí mỗi lượt đạt so với baseline.

## Kết quả

Nhánh không plugin là Claude Code mặc định (Sonnet). Mỗi ô là 5 lượt. Số liệu từng lượt: `results/round1-router-v1.json`, `results/round2-router-v2.json`.

**Vòng 1, router v1** (chưa có bước tìm nơi gọi). Router xếp **cả 15 lượt là `direct`**, không giao việc lần nào; mọi việc do Haiku tự làm.

| Case | Đạt: plugin / mặc định | Chi phí mỗi lượt đạt: plugin / mặc định |
|---|---|---|
| `trivial-question` | 4/5 / 5/5 | $0.0037 / $0.0443 |
| `tiny-bug` | 5/5 / 5/5 | $0.0046 / $0.0595 |
| `ledger-bug` | 4/5 / 5/5 | $0.0100 / $0.0751 |

**Vòng 2, router v2** (bắt buộc tìm nơi gọi trước khi tự sửa; hàm dùng chung đã biết nguyên nhân thuộc `standard`). Đo lại 2 case có code, cả hai nhánh.

| Case | Router chọn | Đạt: plugin / mặc định | Chi phí mỗi lượt đạt: plugin / mặc định |
|---|---|---|---|
| `tiny-bug` | `direct` 5/5 (Haiku) | 5/5 / 5/5 | $0.0050 / $0.0589 |
| `ledger-bug` | `standard` 5/5 (Haiku định tuyến, Sonnet sửa) | 5/5 / 4/5 | $0.0576 / $0.0863 |

- Bản v2 giao đúng việc: lỗi một file làm thẳng bằng Haiku (rẻ hơn khoảng 92%), lỗi ở hàm dùng chung được giao cho Sonnet. Với `ledger-bug`, gộp hai vòng nhánh mặc định đạt 9/10 với chi phí mỗi lượt đạt khoảng $0.080, so với $0.058 của plugin v2 (thấp hơn khoảng 28%).
- Token input của `ledger-bug` khi giao việc cao hơn (khoảng 197k so với 93k–110k) vì cả Haiku lẫn Sonnet cùng đọc; chi phí vẫn thấp hơn nhờ phần lớn token do Haiku xử lý. `eval_metrics.py` cộng token theo từng model.
- Mỗi lượt giao việc qua `tier-standard` mất khoảng 53 giây so với khoảng 32 giây khi một model làm thẳng.

### Giới hạn (quan trọng)

- **Có nguy cơ khớp quá mức vào bộ đo.** Bản v2 được sửa dựa trên chính các lượt của `ledger-bug`, rồi đo lại cũng trên case đó. Chưa có tập xác nhận gồm tác vụ chưa dùng khi sửa. Chưa thể coi v2 là cải thiện cho đến khi đo trên tác vụ mới.
- Chỉ 5 lượt mỗi ô; chênh lệch một lượt (0,2 điểm) nằm trong nhiễu của judge.
- `trivial-question` chưa đo lại với v2. Lượt trượt ở vòng 1 có thể do judge chấm khắt khe về chi tiết "tuple hash được".
- Chưa có case khó (nguyên nhân chưa rõ, liên module, có rủi ro) nên bậc `deep` (Opus) **chưa từng được gọi** và chưa được kiểm chứng.
- Khoá `effort` chưa quan sát được; chỉ model phục vụ lượt chạy đọc được từ trace.
