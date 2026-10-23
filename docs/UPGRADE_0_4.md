# OMEGA 0.4: giảm báo xanh sai và làm rõ phạm vi vận hành

> Báo cáo lịch sử 0.4. Bản mới: [UPGRADE_0_5.md](UPGRADE_0_5.md).

## Đã hoàn thành

Lõi vẫn Python stdlib; bổ sung TypeScript bridge không dependency theo khuyến nghị của người dùng. Có 13 skill hoạt động, không thêm placeholder hoặc agent runtime. Bằng chứng mới: [verification-hardening.json](evidence/verification-hardening.json). Bản 0.3 là lịch sử, không suy ra hiệu quả native từ số test tăng.

| Điểm yếu đã tái hiện | Nâng cấp | Kiểm chứng |
|---|---|---|
| JUnit root khai errors=1 nhưng có testcase pass vẫn được chấp nhận | So aggregate tests/failures/errors/skipped ở root và nested suites; reject outcome ngoài testcase | Negative fixtures cho root/nested và actual Node JUnit |
| Go test pass nhưng thiếu final package vẫn pass | Mọi package có terminal; test run/terminal khớp; reject duplicate hoặc package failure | Parser regression; chưa chạy Go toolchain native |
| Marker success kèm timed_out=true vẫn pass | Process flags invalid/timeout/output-limit luôn phủ quyết readiness; marker cuối và unique | Regression cho adapter và gate record |
| Evidence blob không đổi nhưng nguồn/runtime phía sau đã đổi | Memory-read/reconcile kiểm tra context của evidence, báo unbound/not-checked/stale | Test nguồn đổi, env đổi và library không có context |
| Fingerprint bỏ qua ignored dependency và runtime options | runtime_inputs tường minh + hash whitelist environment + hash Python engine | Test file bị ignore và NODE_OPTIONS đổi; không in giá trị |
| Handoff chỉ phát hiện hai writer cùng exact file | read/write file + directory scopes, orchestrator đi trước, reject glob/typo | Reader/writer race, nested directory, tương tự prefix và ordered cases |
| Security gate chỉ dò literal trong .claude | Bounded static Python AST + JSON bypass + high-confidence possible-secret rules; thêm omega vào scope | Aliases/shell/dynamic execution/pickle/YAML/TLS; redaction; symlink/size/binary |
| Đề xuất npm/Jest JSON có thể trộn banners/stderr | Chỉ đề xuất Node built-in JUnit khi nhận đúng script; Jest/runner khác cần config review | Actual Node fixture; proposal vẫn exit 1, không install/write |
| TS bridge có nguy cơ tách policy và vượt budget | Facade chỉ gọi Python, whitelist read commands, bounded spawn không shell | 9 test TypeScript runtime với Python thật |

## Security rules

`python3 -m omega audit --select .claude --select omega --compact` là security gate hiện tại. Dò AST calls eval/exec, os.system/popen, một số subprocess shell/dynamic kwargs, pickle, unsafe yaml.load, requests verify=False và unverified SSL context. Hỗ trợ một số import aliases; không là phân tích taint hoặc chứng minh data flow an toàn.

Text scan báo possible-secret literal bằng rule/path/line, không echo matched value hoặc surrounding source. JSON được parse bounded/unique-key để kiểm tra permission mode và disableAllHooks. Không áp dụng tự động finding thành sửa policy/quyền. Source và coverage có SHA-256, không có model call hoặc command từ source được thực thi.

Chọn tối đa 32 roots/files, 256 files/directories, 1 MB/file và 4 MB tổng. Missing/binary/symlink/oversized/parse-error làm scan không đầy đủ và fail. Generated __pycache__ được loại khỏi directory scan và ghi vào exclusions; chọn explicit file bytecode vẫn fail, không xóa cache để làm xanh. JavaScript/TypeScript chỉ có text rules, chưa có AST/security assurance tương ứng. Không quét dependencies hoặc bảo đảm đã lọc mọi secret.

## Runtime và memory

Gate config schema=1 thêm optional `runtime_inputs:["node_modules/.package-lock.json", ".venv/pyvenv.cfg"]`. Chỉ kê file thực sự có và cần ràng buộc: tối đa 32, 1 MB/file, 8 MB tổng, trong project, không private/symlink. Thiếu hoặc vượt giới hạn bị từ chối trước khi chạy gate. Không tự quét/cài dependencies; hash file này không chứng minh toàn bộ dependency tree.

Known environment whitelist chỉ lưu SHA-256 hoặc null: PATH, PYTHONPATH/PYTHONHASHSEED/PYTHONOPTIMIZE, NODE_OPTIONS/NODE_PATH, GOWORK/GOTOOLCHAIN/GOPROXY/GOSUMDB/GOCACHE. Không dump env hoặc credential values. Hash không phải cơ chế lưu secret; services/model/managed/global policy và env khác vẫn ngoài phạm vi.

`memory-read` và `memory-reconciliation` nhận context hiện tại ở CLI. Nếu external project có gate config/runtime_inputs riêng, truyền lại cùng --gate-config. Memory có evidence unbound hoặc context drift cần review; không tự sửa/xóa record. Library memory_status không được đưa context trả not-checked và requires_validation, không tự khẳng định evidence current. Evidence về test fail vẫn có thể là nguồn hợp lệ nếu context khớp; factual correctness vẫn cần người review.

Ledger repair đọc lại bằng bounded JSON và kiểm tra schema/project sau khi lấy lock; kiểm tra kích thước trước khi ghi. Đây là cooperative lock cho local ledger, không chống actor có toàn quyền sửa filesystem.

## Workflow scopes

Node bổ sung `reads`, `read_dirs`, `write_dirs`; writes vẫn là exact file list cũ. Directory scope bao gồm descendants; src không chồng với src-other. Reader/writer hoặc writer/writer không có dependency sẽ fail kể cả batch budget vô tình xếp tuần tự: lịch tình cờ không thay dependency contract. Từng worker phải có orchestrator trong ancestors. Invalid workflow không trả actionable schedule. Không tự suy ra đường dẫn undeclared, không scheduler/OS lock, không dispatch Claude.

## Kiểm chứng và phần còn yếu

176 Python unittest riêng biệt pass, 9 test Node cho TypeScript bridge pass. Native runner fixture có 2 testcase: 1 pass, 1 skipped có chủ ý; trước sửa phép cộng thì đỏ, sau sửa xanh. Không cộng số chạy lặp hoặc skipped vào số test đạt. Các nhóm scenario theo skill vẫn dùng chung và không là đánh giá chất lượng độc lập.

Node built-in JUnit đã chạy thật trên Git target riêng bằng engine Python. Lệnh go version ở môi trường trả “Unknown option”, nên Go/Jest vẫn chỉ có parser fixtures; không tự cài toolchain. Claude version/auth metadata được quan sát riêng; native skill/agent/hook reasoning chưa được nghiệm thu và token provider chưa được đo.

Kiến trúc TypeScript/MCP/UI và cách chạy bridge: [PYTHON_TYPESCRIPT_BOUNDARY.md](PYTHON_TYPESCRIPT_BOUNDARY.md). Chưa triển khai MCP server/UI, không đăng ký hook hoặc mở port. Bước tiếp theo cần use case/native credentials và corpus độc lập; không thể đóng những giới hạn đó bằng thêm contract tests.

Fingerprint engine ràng buộc các file Python/JSON của package omega và omega_cli.py, kể cả khi project đích ở checkout khác. Thay implementation OMEGA làm evidence cũ stale; không chỉ dựa vào version string hoặc target workspace.
