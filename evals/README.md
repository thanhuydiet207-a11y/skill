# Eval của Tier

Mỗi case chạy hai nhánh: có plugin, và không plugin (Claude Code mặc định, Sonnet). Thư mục `fixtures/` là project mẫu không có file nào của plugin, nên nhánh không plugin là baseline sạch. `scaffold.sh` của mỗi case chép fixture vào workspace và commit.

| Case | Bậc kỳ vọng | Lỗi cài sẵn |
|---|---|---|
| `trivial-question` | direct | Không có (câu hỏi Python) |
| `tiny-bug` | direct hoặc standard | `slugify` dùng `_` thay `-`, một file |
| `ledger-bug` | standard | `parse_amount` cắt cụt số thực, dùng chung bởi 2 module; làm đỏ test ở 2 file |

Bậc kỳ vọng là nhận định ban đầu, không phải đáp án đúng duy nhất: tiêu chí đánh giá chính là tỉ lệ đạt và chi phí mỗi lượt đạt so với baseline.

Kết quả sẽ được ghi ở đây sau mỗi lần đo.
