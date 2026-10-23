# OMEGA quality-gates

## Inputs

Acceptance, diff/risk map, project root và đủ argv build/tests/security/regression đã review. Với project khác, gate config phải tường minh; không dùng command của engine để tuyên bố project đích đạt.

## Trust boundary trước khi thực thi

Coi `--gate-config`, adapter, package scripts, test runner, build scripts và các executable được gọi là **mã có thể thực thi**, không phải dữ liệu cấu hình vô hại.

- Xác minh nguồn gốc của config (được người dùng/repo tin cậy phê duyệt hay đến từ PR, issue, artifact, dependency hoặc workspace không tin cậy). Không chạy config mới chỉ vì schema/argv hợp lệ.
- Review chính xác executable, argv, working directory, biến môi trường, file đầu vào/đầu ra, script/package lifecycle và tiến trình con. Xem cả lệnh gián tiếp mà package script hoặc adapter khởi chạy.
- Phân loại tác dụng phụ: ghi/xóa file, truy cập credential, mạng, cài dependency, sửa Git state, gọi dịch vụ ngoài hoặc chạy code tải về. Không cho phép quyền rộng hơn cần thiết cho acceptance.
- `shell=False`, allowlist tên lệnh, timeout và output cap giảm một số rủi ro nhưng **không phải sandbox**. Một executable được phép vẫn có thể chạy code nguy hiểm hoặc dùng toàn bộ quyền của tiến trình cha.
- Chạy lệnh không tin cậy trong sandbox/VM/container riêng với quyền tối thiểu, mạng bị chặn mặc định, filesystem đích chỉ mở ở mức cần thiết và không mount secrets. Nếu không thể review hoặc cô lập đủ, đánh dấu **blocked / not run**, nêu lý do và yêu cầu người có thẩm quyền phê duyệt; không tự nới quyền.
- Không chạy lệnh phá hủy hoặc thay đổi trạng thái bên ngoài scope (deploy, publish, push, xóa dữ liệu, migration, gửi dữ liệu ra ngoài) nếu chưa có authorization rõ ràng.

## Workflow

Với Jest/JUnit có log trộn, review test_report .omega/reports/{run_id}/FILENAME và đúng một {report_path} trong args tests. File report phải mới, bounded, không symlink/hardlink, không đổi sau tests; exit failure/timeout/output cap không được overridden. Dùng python3 benchmarks/native_runners.py --report-file để nghiệm thu Node thật. Full engine build gồm Python compile + strict TypeScript noEmit từ dev tools đã pin; đọc docs/UPGRADE_0_5.md trước setup.

Kiểm tra cả aggregate JUnit root/nested và terminal Go package; timeout/output-limit/invalid UTF-8 luôn phủ quyết success marker. Runtime_inputs chỉ khai file dependency cần ràng buộc và không private. Node built-in JUnit có benchmark thật `python3 benchmarks/native_runners.py`; Jest/Go vẫn cần nghiệm thu native. Đọc docs/UPGRADE_0_4.md theo nhu cầu.

1. Hoàn tất trust review ở trên trước khi thực thi. Dùng project-workflow-adapter chỉ để lấy proposal; security/regression còn thiếu phải được cấu hình thật, không thay bằng lệnh luôn trả 0.
2. Chạy `python3 -m omega gates --summary --compact` trong engine; target ngoài dùng runner tuyệt đối, `--project-root` và `--gate-config`. Chỉ chạy sau khi config được review và môi trường thực thi phù hợp. Mở output qua evidence refs khi cần, không chạy lại chỉ để xem log.
3. Đối chiếu outcomes với adapter omega/Jest/Go/JUnit. Zero tests, all-skipped, inconsistent counts hoặc truncated structured output không đủ ready; Go package-pass không phải test. Fixture parser pass không chứng minh mọi framework đã chạy native.
4. Kiểm tra workspace_unchanged và execution_unchanged. Format/codegen/index thay đổi trong hoặc sau gate làm proof cũ; chạy sau bước ghi file có chủ đích và nêu phần môi trường chưa quan sát.
5. Với auth/untrusted input/subprocess/filesystem/API/schema, bổ sung review/negative tests đúng rủi ro. Audit mặc định chỉ scan policy hẹp, không phải SAST/secret/dependency assurance.
6. Chạy `python3 -m omega rollback-check --compact`; review base commit và chiến lược revert. Chi tiết adapter, evidence và giới hạn ở docs/INTEROPERABILITY_GUIDE.md.

## Evidence

Trả argv, nguồn và hash của config, adapter, outcome counts, source/runtime fingerprint, duration, timeout/output-limit/truncation và artifact path. Ghi rõ sandbox/permissions/network policy đã áp dụng hoặc vì sao không áp dụng; phân biệt failed/skipped/unrun, rollback strategy và rollback thật đã thực thi. Không ghi secret vào report.

## Failure handling

Exit 124 timeout, 125 output flood, 127 launch failure: đọc prefix/tail, kiểm chứng diagnosis rồi thu hẹp target hoặc sửa prerequisite hợp lệ. Giữ verification và assertions; nếu sửa code thì dùng repair ledger, không lặp vô hạn. Nếu config hoặc executable không đáng tin, dừng trước khi chạy và báo **blocked / not run**; không xem việc gate chưa chạy là pass.

## Stop conditions

Required check fail/unexplained/unrun hoặc evidence stale thì không báo ready. Chỉ kết luận trong phạm vi runner và môi trường đã quan sát; hooks/MCP unknown và CLI allowed không cấp quyền platform. Không gọi là sandboxed trừ khi isolation được thiết lập và xác minh thực tế.
