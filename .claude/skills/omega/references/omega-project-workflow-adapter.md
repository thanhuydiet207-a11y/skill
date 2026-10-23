# OMEGA project-workflow-adapter

## Inputs

Root Git tường minh, manifests/CI có thể đọc, stack/runtime version và quyền đọc project; xác định engine runner riêng với target project. Chỉ đề xuất cấu hình từ evidence hiện có. Không giả định project cho phép cài package, sửa manifest/lockfile hoặc chạy lifecycle scripts.

## Workflow

1. **Nhận diện stack từ nguồn thật:** chạy `python3 -m omega project-workflow-adapter --compact`. Đối chiếu package manifests, lockfiles, CI workflows, scripts và runtime version; phân biệt command khai báo với command thực sự được CI/maintainer dùng. Nếu nhiều package/workspace hoặc monorepo, xác định đúng target root và phạm vi từng gate.
2. **Đánh giá proposal, không thực thi:** proposal là dữ liệu để review, không phải quyền chạy command. Không cài dependencies, gọi package manager, chạy lifecycle scripts, sửa manifest/lockfile hoặc tạo config trong bước nhận diện. Trước khi bất kỳ command nào được thực thi, review nguồn script, argv, cwd, environment, child processes và side effects; nếu không đủ trust/isolation thì giữ `blocked/not-run`.
3. **Xác minh command và output channel:** exact Jest script có thể nhận proposal `--json --outputFile={report_path}` cùng test_report nonce; stdout/stderr vẫn là log, không phải report. Proposal chưa ready và không tự install Jest hoặc chạy script. Kiểm tra report được tạo đúng path, có schema/nonce/hash theo policy và không bị nhầm với merged console output. Runner khác phải review config/output channel trước; không dùng exit code 0 làm thay cho report hợp lệ.
4. **Đánh giá gate coverage:** cấu hình đủ bốn gates thật trước khi dùng; xác định rõ build/typecheck, unit/integration tests, security checks và regression/acceptance. Node file reporter đã có benchmark, Jest native vẫn chưa kiểm chứng. Schema/budget/freshness: docs/UPGRADE_0_5.md. Nếu thiếu gate bắt buộc, ghi blocker thay vì đề xuất config có vẻ xanh nhưng coverage không đủ.
5. **Chọn adapter theo bằng chứng:** chỉ khi test script đúng `node --test` mới đề xuất Node built-in JUnit sau khi kiểm tra runtime hỗ trợ. Không suy ra tương thích từ tên package hoặc output mẫu. Python là lõi kiểm chứng; TypeScript giao tiếp qua bridge ở docs/PYTHON_TYPESCRIPT_BOUNDARY.md, không viết lại policy. Xem docs/UPGRADE_0_4.md.
6. **Review command đầy đủ:** kiểm tra argv chính xác của build/tests/security/regression, shell behavior, glob/path expansion, timeout, output cap, working directory, env vars, report paths, permissions và khả năng spawn child process. Shell=False, allowlist, timeout hoặc output cap không tự tạo sandbox. Không dùng command chứa deployment/publish/delete/migration hay external side effects nếu chưa có authorization riêng.
7. **Ràng buộc config vào target:** trước khi lưu config riêng, xác minh target root, repo identity, lockfile/runtime, report policy, required gates và evidence freshness. Proposal cần ghi source refs/hash, assumptions và unknowns. Dùng runner tuyệt đối và `--project-root` ở project ngoài OMEGA; không để config cho một project được áp dụng ngầm vào project khác.
8. **Giữ proposal reviewable:** chỉ đề xuất thay đổi tối thiểu, mô tả chính xác command/report/gate cần thiết và cách kiểm chứng. Không tuyên bố adapter native-ready khi chỉ có fixture, sample output hoặc static inspection. Proposal chưa sẵn sàng vẫn exit 1 theo contract hiện tại.

## Evidence

Trả stack/runtime và target root, source refs/hash, command proposal, output channel, gates được/không được bao phủ, assumptions, quyền thực thi cần thiết, report schema/freshness và missing requirements. Phân biệt `proposal-needs-review`, `blocked`, `not-run` và `ready` theo trạng thái engine; không tự nâng trạng thái nếu native adapter chưa được kiểm chứng.

## Failure handling

Không nhận diện được stack, target root mơ hồ, command/source không đáng tin, thiếu security/regression, output schema không hợp lệ hoặc runtime không hỗ trợ: báo yêu cầu cụ thể và giữ proposal chưa sẵn sàng. Jest/Go/JUnit output không đúng schema thì không thay bằng exit-zero-only. Không tự cài package, hạ gate, đổi output policy hoặc sửa manifest để vượt lỗi.

## Stop conditions

Dừng khi có proposal đủ thông tin để review hoặc blocker rõ ràng. Không tự npm/pip install, sửa manifest/lockfile, tạo config hay tuyên bố mọi framework đã được native test. Project ngoài OMEGA dùng runner tuyệt đối và `--project-root`.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md.
