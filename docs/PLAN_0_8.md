# OMEGA 0.8 — Kế hoạch nâng cấp theo hướng đo lường trước

## 1. Mục tiêu

Chuyển OMEGA từ một bộ công cụ AI Engineering nhiều thành phần thành một lớp hỗ trợ Claude Code chỉ can thiệp khi chứng minh được lợi ích thực tế.

OMEGA chỉ được xem là cải thiện khi:
- Giữ nguyên hoặc nâng chất lượng hoàn thành tác vụ.
- Giảm tổng token hoặc chi phí trên mỗi tác vụ thành công.
- Không làm tăng đáng kể thời gian, lỗi hồi quy hoặc độ phức tạp vận hành.
- Kết quả lặp lại được trên các tác vụ chưa dùng để phát triển tính năng.

Các con số mục tiêu trong tài liệu này là tiêu chí đề xuất, chưa phải kết quả đã đạt được.

## 2. Vấn đề cần giải quyết

### 2.1. Trùng chức năng với Claude Code
Lập kế hoạch, đọc code, sửa code và chạy test đều là những khả năng Claude Code vốn đã có. Một lớp hướng dẫn bổ sung có thể chỉ làm tăng context mà không cải thiện đầu ra.

### 2.2. Đo byte không đồng nghĩa với đo token
Rút gọn JSON hoặc log có thể giảm dung lượng dữ liệu, nhưng chưa chứng minh được tổng token của phiên Claude Code giảm. Cần đo usage thực tế từ runtime/provider khi khả dụng.

### 2.3. Benchmark chưa đủ sức chứng minh lợi ích
Benchmark cần đo kết quả hoàn thành tác vụ, chất lượng, token, chi phí, số lần gọi công cụ và thời gian — không chỉ kiểm tra công cụ có chạy được.

### 2.4. Điều phối quá mức
Nhiều chế độ, skill và agent không tự động tạo ra hiệu quả. Overhead điều phối có thể lớn hơn lợi ích. Cần chọn đường thực thi theo độ phức tạp và bằng chứng.

## 3. Nguyên tắc phát triển

1. Measurement-first: đo baseline trước khi sửa.
2. Không thêm capability chỉ để tăng số lượng tính năng.
3. Tối ưu theo tổng chi phí trên mỗi tác vụ thành công, không tối ưu một chỉ số riêng lẻ.
4. Ưu tiên retrieval xác định, rẻ và dễ kiểm chứng trước khi cân nhắc embedding hoặc vector database.
5. Chỉ bật mặc định những thay đổi đã vượt qua benchmark.
6. Không tuyên bố tiết kiệm token dựa trên byte, số dòng hoặc ước lượng không được xác minh.
7. Giữ lại baseline và khả năng tắt từng tính năng để so sánh, rollback.

## 4. Lộ trình nâng cấp

### P0 — Instrumentation và benchmark

Xây nền tảng đo lường đáng tin cậy trước khi mở rộng hệ thống.

Việc cần làm:
- Ghi nhận input tokens, output tokens, cache read/write tokens và chi phí khi runtime/provider cung cấp.
- Ghi số lượt gọi công cụ, độ trễ, lỗi, test đã chạy và trạng thái hoàn thành.
- Theo dõi skill, agent, chế độ nào thực sự được kích hoạt và overhead của chúng.
- Lưu kết quả có thể tái lập theo từng task và lần chạy.
- So sánh cùng model, phiên bản, repository, yêu cầu và tiêu chí nghiệm thu.
- Reset workspace giữa các lần chạy để tránh trạng thái rò rỉ.
- Hoán đổi thứ tự chạy các nhánh để hạn chế ảnh hưởng do thứ tự.

Ba nhánh so sánh:
- A — Baseline: Claude Code không cài OMEGA.
- B — Current: OMEGA hiện tại.
- C — Candidate: OMEGA với một thay đổi mới.

Mỗi lần chỉ nên thử một thay đổi hoặc một nhóm thay đổi có quan hệ rõ ràng. Dùng các task phát triển riêng với tập task xác nhận để tránh overfit benchmark.

Bộ chỉ số:
- Input tokens.
- Output tokens.
- Cache read/write tokens (nếu có).
- Tỷ lệ hoàn thành đúng acceptance criteria.
- Lỗi hồi quy.
- Số lần gọi công cụ và thời gian hoàn thành.
- Chi phí trên mỗi tác vụ hoàn thành thành công.

Giai đoạn sàng lọc: mục tiêu tối thiểu 10 lần chạy mỗi nhánh cho mỗi task hoặc theo ngân sách phù hợp; các cải tiến có triển vọng phải được xác nhận thêm. Không coi số lần chạy cố định là bảo đảm thống kê nếu task hoặc biến động quá lớn.

### P1 — Context Intelligence

Mục tiêu: giảm context không cần thiết nhưng không bỏ sót thông tin cần để sửa đúng.

Pipeline đề xuất:
1. Parse task: mục tiêu, acceptance criteria, ràng buộc.
2. Repo retrieval: Git diff/status, tìm symbol, imports, callers, tests, cấu hình và interface liên quan.
3. Build context packet: chọn đoạn code và bằng chứng liên quan, kèm nguồn tham chiếu.
4. Sufficiency check: phát hiện dependency hoặc thông tin còn thiếu.
5. Execute and verify: mở rộng context khi bằng chứng chưa đủ; kiểm tra kết quả sau thay đổi.

Tính năng:
- Dependency-aware retrieval: tìm các nơi gọi, interface và test bị ảnh hưởng khi sửa thành phần dùng chung.
- Uncertainty-triggered retrieval: truy xuất thêm khi chưa đủ bằng chứng; không đoán chỉ để tiết kiệm token.
- Evidence reuse: tái sử dụng kết quả đã đọc hoặc test trong cùng phiên khi nguồn và trạng thái vẫn hợp lệ.
- Context budget: giới hạn context theo tác vụ nhưng cho phép mở rộng theo nhu cầu.
- Provenance: mỗi đoạn context cần truy được về file, dòng hoặc kết quả lệnh nguồn.

Thứ tự triển khai:
1. Dùng công cụ rẻ và xác định như `rg`, Git, AST và phân tích imports.
2. Đo tỷ lệ bỏ sót context và số lần truy xuất bổ sung.
3. Chỉ cân nhắc embedding/vector search nếu benchmark cho thấy phương pháp đơn giản bỏ lỡ thông tin quan trọng.

### P2 — Closed-loop Engineering

Xây workflow sửa lỗi và thay đổi code có kiểm chứng:
1. Tái hiện lỗi hoặc xác định test mục tiêu.
2. Tìm nguyên nhân dựa trên code và kết quả thực thi.
3. Sửa phạm vi nhỏ nhất có thể.
4. Chạy test mục tiêu, sau đó chạy các quality gates phù hợp.
5. Nếu thất bại, phân loại lỗi và chỉ lặp lại khi có thông tin mới hoặc giả thuyết sửa đổi.
6. Báo cáo thay đổi, test thực sự đã chạy và điều chưa xác minh.

Không áp dụng pipeline dài cho mọi tác vụ. Câu hỏi đơn giản hoặc chỉnh sửa nhỏ cần đường đi ngắn hơn.

### P3 — Adaptive Orchestration

Ba chế độ thực thi đề xuất:

- `direct`: câu hỏi đơn giản hoặc sửa nhỏ; không lập kế hoạch dài, không gọi agent không cần thiết.
- `focused`: sửa bug hoặc tính năng vừa; truy xuất dependency, sửa và kiểm thử mục tiêu.
- `deep`: refactor lớn, lỗi liên module hoặc tác vụ rủi ro; phân tích tác động, lập kế hoạch và kiểm thử mở rộng; chỉ gọi agent khi có lợi ích dự kiến.

Router cần ghi log lý do chọn chế độ. Không phân loại chỉ dựa trên độ dài prompt hoặc số file; cần xét độ bất định, số module ảnh hưởng, rủi ro và khả năng xác minh.

## 5. Benchmark và tiêu chí nghiệm thu

### Thiết kế
- Chạy A/B/C trên cùng bộ task, model, phiên bản, repository và điều kiện.
- Reset workspace trước mỗi lần chạy.
- Hoán đổi thứ tự chạy.
- Dùng tập phát triển riêng và tập xác nhận chưa dùng để tối ưu.
- Lưu raw result, cấu hình và phiên bản commit.
- Đo usage thực tế từ runtime/provider khi có thể; nếu thiếu dữ liệu phải ghi rõ là thiếu, không thay bằng byte rồi gọi là token.

### Tiêu chí đề xuất
1. Chất lượng không kém baseline: tỷ lệ hoàn thành đúng acceptance criteria phải ít nhất ngang baseline trong tập xác nhận.
2. Không bỏ qua test, an toàn hoặc tiêu chí nghiệm thu để cải thiện số liệu.
3. Mục tiêu ban đầu: giảm ít nhất 15% tổng input tokens hoặc chi phí trên mỗi tác vụ thành công, không tăng đáng kể thời gian hay lỗi hồi quy.
4. Lợi ích phải lặp lại trên các task xác nhận, không chỉ một trường hợp.
5. Nếu không đạt ngưỡng, không bật tính năng mặc định; giữ ở dạng thử nghiệm hoặc loại bỏ.

Ngưỡng 15% là mục tiêu khởi đầu để thử nghiệm, không phải định luật hay cam kết kết quả. Cần xem xét độ biến động và khoảng tin cậy khi phân tích.

## 6. Kế hoạch thực hiện theo giai đoạn

### Giai đoạn 1 — Đo lường
- Kiểm tra benchmark hiện tại và giữ lại làm baseline.
- Bổ sung usage, tool calls, latency, test result và chi phí.
- Chuẩn hóa bộ task và acceptance criteria.
- Tạo báo cáo so sánh A/B/C.

Điều kiện hoàn tất: có thể tái lập kết quả và giải thích overhead của OMEGA.

### Giai đoạn 2 — Context Intelligence
- Xây dependency-aware retrieval.
- Bổ sung context sufficiency check.
- Bổ sung evidence reuse có kiểm tra tính hợp lệ.
- Đo token, chất lượng và tỷ lệ bỏ sót context.

Điều kiện hoàn tất: giảm token/chi phí mà không giảm chất lượng trên tập xác nhận.

### Giai đoạn 3 — Workflow chuyên biệt
- Tối ưu workflow sửa lỗi, thêm tính năng và refactor.
- Dùng test thực tế, không chỉ benchmark tổng hợp.
- Chỉ thêm workflow khi nó vượt baseline.

Điều kiện hoàn tất: có bằng chứng rằng workflow cải thiện chất lượng, tốc độ hoặc chi phí.

### Giai đoạn 4 — Adaptive Router
- Xây router với các chế độ `direct`, `focused`, `deep`.
- Ghi lý do chọn chế độ.
- So sánh chi phí và kết quả của từng chế độ.
- Chỉ bật mặc định các đường đi đã được xác nhận.

Điều kiện hoàn tất: tác vụ đơn giản không bị áp quy trình nặng; tác vụ phức tạp nhận được hỗ trợ tương xứng.

## 7. Những việc chưa nên làm

- Chưa mở rộng hàng loạt capability đang planned.
- Chưa thêm nhiều agent nếu chưa có benchmark chứng minh lợi ích.
- Chưa dùng vector database/embedding cho mọi repository.
- Không tăng độ dài skill/prompt chỉ để nhắc lại khả năng Claude Code vốn đã có.
- Không coi byte giảm, log ngắn hơn hoặc số test pass của riêng OMEGA là bằng chứng đủ về tiết kiệm token hay tăng chất lượng.
- Không dùng một benchmark nhỏ làm bằng chứng tổng quát.

## 8. Bảng quyết định cho mỗi thay đổi

Với mỗi feature, ghi:
- Giả thuyết cần kiểm chứng.
- Baseline và candidate.
- Task phù hợp và task không phù hợp.
- Token/chi phí trước–sau.
- Chất lượng và lỗi hồi quy.
- Độ trễ và số lần gọi công cụ.
- Kết quả trên tập xác nhận.
- Quyết định: `promote`, `keep experimental` hoặc `remove`.

## 9. Kết luận

Mục tiêu của OMEGA không phải là trở thành framework lớn hơn. Mục tiêu là giúp Claude Code:
- Đọc ít context không cần thiết hơn nhưng vẫn đủ bằng chứng.
- Tìm nguyên nhân chính xác hơn.
- Sửa code với phạm vi nhỏ hơn.
- Xác minh kết quả bằng test thật.
- Chỉ sử dụng quy trình/agent bổ sung khi lợi ích vượt chi phí.
- Chứng minh được lợi ích bằng benchmark có đối chứng.

Thứ tự ưu tiên: **P0 đo lường → P1 Context Intelligence → P2 Closed-loop Engineering → P3 Adaptive Orchestration**.

Tài liệu này là kế hoạch kỹ thuật đề xuất, không khẳng định các tính năng đã được triển khai hoặc đạt được mức tiết kiệm cụ thể. Trước khi thay đổi kiến trúc, cần đối chiếu từng mục với mã nguồn và benchmark hiện tại của repository.
