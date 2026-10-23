# OMEGA 0.5: report riêng, kiểm tra kiểu và deadline xuyên suốt

> Snapshot lịch sử 0.5. Bản 0.6 gộp thành một skill omega; xem [UNIFIED_SKILL.md](UNIFIED_SKILL.md). Các số liệu dưới đây thuộc snapshot 0.5.

## Kết quả thực tế

194 Python tests và 15 Node tests của bridge pass; build gate giờ gồm compile Python và strict TypeScript type-check không emit. Có 13 skill hoạt động; đợt này cập nhật nội dung 4 skill qua candidate/benchmark/gates/compare, không thêm agent hoặc placeholder. Bằng chứng: [report-integrity.json](evidence/report-integrity.json).

Hai lỗi đã tái hiện ở bản 0.4: capture log UTF-8 hợp lệ nhưng cắt giữa ký tự bị đánh dấu invalid_utf8; CLI TypeScript có thể chờ stdin không EOF vô hạn vì timeout chỉ bắt đầu lúc gọi Python. Type-check đầy đủ còn phát hiện TS2345 ở project root có thể undefined. Cả ba đã sửa và có kiểm chứng tương ứng.

## Test report độc lập stdout/stderr

Config schema=1 thêm optional test_report cho Jest/JUnit. Mỗi lần chạy dùng UUID mới, không tái sử dụng/xóa/ghi đè report cũ bằng engine. Template bắt buộc `.omega/reports/{run_id}/FILENAME`; chỉ một `{report_path}` trong args của gate tests, không ở executable hoặc gate khác. Path được render thành argv, không shell.

Ví dụ phần cấu hình cần review cùng **đủ bốn gate thực tế** của dự án:

```json
{
  "schema": 1,
  "test_adapter": "jest",
  "test_report": ".omega/reports/{run_id}/jest.json",
  "gates": {
    "build": ["npm", "run", "build"],
    "tests": ["npm", "test", "--", "--json", "--outputFile={report_path}"],
    "security": ["npm", "run", "security"],
    "regression": ["npm", "run", "regression"]
  }
}
```

Đây là schema/example cho project có các scripts được review, không khẳng định scripts đó tồn tại ở mọi repo. Không chạy proposal tự động hoặc cài Jest. Với pytest/JUnit, dùng flag report của runner đã được xác minh, cùng `{report_path}`. Với Node built-in, có benchmark thực thi thật:

```bash
python3 benchmarks/native_runners.py --report-file
```

Benchmark chạy hai reporter Node: log người đọc ở stdout và JUnit ở file riêng, kiểm chứng đỏ → sửa → xanh, hai namespace khác nhau, 1 pass/1 skipped có chủ ý sau sửa. Jest JSON vẫn dùng fixture và proposal; chưa chạy native Jest/Go hoặc pytest trong đợt này.

Report tối đa 256 KiB, UTF-8, regular file một hard link, trong namespace mới. Missing/FIFO/symlink/hardlink/quá lớn/đổi trong lúc đọc đều fail. Nội dung và identity được chụp sau tests, kiểm tra lại sau gates còn lại. Timeout, process failure, output cap hoặc report fail không được ghi đè thành pass. Lưu content + SHA-256 trong evidence; gate summary chỉ trả content_ref, không âm thầm bỏ bằng chứng. Compare/change-check/reconciler xác minh cả template, argv thực tế, adapter và hash report.

Freshness chứng minh file mới trong workflow đã review, không xác thực rằng một runner bất kỳ thật sự chạy tests. Lệnh test có toàn quyền ghi output vẫn có thể giả report như giả marker. Artifact local không có chữ ký; không coi mechanism này là sandbox hoặc provider attestation. Report/log có thể chứa dữ liệu nhạy cảm: runtime artifacts được ignore, cần review trước xuất bản. Không tự đồng bộ/xuất bản report của project.

## Parser và capture

Validate Jest assertionResults khi được cung cấp: không cho chi tiết trái tổng, interrupted/runtime error/suite fail hoặc danh sách rỗng báo pass. Go phải có run trước terminal và không có test event sau final package; JUnit testcase phải ở đúng container. Đây là kiểm tra cấu trúc, không xác nhận nguồn report.

UTF-8 được validate theo toàn luồng bằng incremental decoder; prefix/tail bị cắt vẫn có thể hiển thị replacement character và luôn có flag truncated. Không tuyên bố khôi phục phần log đã bỏ. Dữ liệu thực sự không hợp lệ ở ngoài prefix vẫn được phát hiện. Report riêng giúp output người đọc không bị nhầm thành JSON/XML kết quả.

## TypeScript: kiểm tra đầy đủ, không chỉ type stripping

Runtime bridge vẫn không có dependency ứng dụng bên thứ ba. Để type-check, thêm đúng hai dev dependencies đã pin: TypeScript 5.9.3 và @types/node 24.19.0, cùng một transitive type package trong package-lock.json. Đã cài với TLS/integrity chuẩn npm, `--ignore-scripts`, không global install, cache trong .omega. Không cài SDK MCP/frontend/Jest.

```bash
npm ci --prefix integration/typescript --ignore-scripts --no-audit --no-fund --cache "$PWD/.omega/npm-cache"
python3 -m omega gates --summary --compact
node --test integration/typescript/omega-bridge.test.mjs
```

Full engine gates cần Node 24 và dev tools trên; không tự install nếu thiếu. Python CLI đọc/phân tích vẫn dùng stdlib. External project có gate config riêng, không bắt dùng toolchain của engine để build ứng dụng. `tsconfig.json` bật strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes, erasableSyntaxOnly và noEmit; build gate bắt buộc chạy compiler.

Suite hash ràng buộc source/tsconfig/lock, prune node_modules và __pycache__, từ chối symlink trong cây source engine. Không hash toàn bộ dependency tree hoặc coi lock là chứng nhận files đã cài không bị sửa. Node_modules được ignore, không commit vendor/compiler.

## Deadline và cancellation

CLI bridge nhận `--timeout-ms N` (1..60000, mặc định 15000) cho cả đọc stdin và gọi Python. Stdin không EOF sẽ timeout/destroy; không giữ phiên treo. API cũng giới hạn tổng request 16 KiB, có AbortSignal; hủy/timeout/output cap kill process group, đóng pipes và chờ child close trước reject. Không trả partial JSON như success. Không là OS quota đối với tiến trình cố tình thoát process group hoặc attacker có toàn quyền filesystem.

## Giới hạn còn lại

- Native Claude discovery/agents/hooks/reasoning chưa nghiệm thu; token/cost provider chưa đo. Không suy ra chất lượng LLM từ contract score hoặc số tests.
- MCP server và UI chưa triển khai; TypeScript hiện là facade local đọc dữ liệu.
- Security là targeted Python rules, chưa có taint/dependency/TS AST security assurance.
- Memory vẫn local, unsigned; workflow validator chưa dispatch hoặc khóa OS writer.
- Jest/Go/pytest native cần toolchain/corpus phù hợp; không tự cài thêm để tạo thành tích. CI chỉ báo verified khi quan sát được Actions, không suy ra từ local pass.
