# Lệnh mở rộng của OMEGA

Tám lệnh CLI dưới đây từng là chế độ riêng của skill `omega` (mỗi chế độ có một file reference). Từ 0.7.5 chúng không còn trong skill: đo ở [evals/README.md](../evals/README.md) cho thấy 5/8 không bao giờ được gọi từ prompt thường và chỉ 1/8 được tới đúng cách. Lệnh CLI và test của chúng giữ nguyên; tài liệu này giữ lại hướng dẫn gốc để chạy tay.

Mỗi lệnh chạy qua `python3 -m omega LỆNH ...` trong engine, hoặc `python3 -B "${CLAUDE_PLUGIN_ROOT}/omega_cli.py" --project-root "$PWD" LỆNH ...` khi dùng plugin. Bảng tóm tắt lệnh và đầu ra: [OPERATIONS.md](OPERATIONS.md).

## skill-compatibility-audit

Lệnh: `skill-compatibility-audit`

### Inputs

Roots skill/config hook tường minh, phạm vi được phép đọc và workflow contract nếu có.

### Workflow

Chạy `python3 -m omega skill-compatibility-audit --skill-root .claude/skills --compact`; lặp --skill-root/--hook-config khi đã được phép đọc. Không cài hoặc chạy skill đang kiểm tra. Đọc findings, complete_for_selected_roots và phạm vi chưa quan sát; chỉ so sánh identity, metadata, hook events và contract được cung cấp.

### Evidence

Trả roots đã quét, hashes, các tên trùng, event chồng và điều cần native test. passed không phải chứng nhận tương thích.

### Failure handling

Syntax YAML chưa hỗ trợ hoặc source thiếu/symlink: đánh dấu cần review; không tự gọi là skill không hợp lệ với Claude. Không bỏ qua root chưa quét để báo hoàn tất.

### Stop conditions

Dừng khi ma trận xung đột/phần chưa biết đủ rõ để chọn một workflow owner; không tự tắt plugin, sửa policy hoặc nâng quyền.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.

## effective-policy-explainer

Lệnh: `effective-policy-explainer`

### Inputs

Một PreToolUse event JSON, project root và phạm vi policy cần giải thích; không có credential values.

### Workflow

Chạy `python3 -m omega effective-policy-explainer --input INPUT --compact`. Đối chiếu cùng grammar mà hook dùng; kiểm tra cwd, runner, args, paths, shell expansion và background. Phân biệt allowed của OMEGA với quyền của platform.

### Evidence

Trả allowed/reason/rule_source, scope và platform_decision. Không lặp nguyên command chứa dữ liệu nhạy cảm vào báo cáo.

### Failure handling

Thiếu event/schema hoặc outside scope thì báo denied/unknown; không sửa allowlist để vượt lỗi. Nếu platform từ chối, kiểm tra nguồn policy thực tế trước yêu cầu thêm quyền.

### Stop conditions

Dừng khi có lời giải thích có nguồn và phần chưa biết. Không cấp quyền, thay hook, bật MCP hoặc suy diễn hooks_disabled từ config OMEGA.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.

## workflow-handoff-contract

Lệnh: `workflow-handoff-contract`

### Inputs

Workflow nodes, một orchestrator, owner cho Git/gates/memory, exact write paths, dependencies và budget.

### Workflow

Khai reads/writes cho exact files và read_dirs/write_dirs cho subtree; liệt kê đầy đủ nguồn đọc có thể bị writer khác thay đổi. Đặt dependency để reader đi sau writer, không dựa vào batch budget tình cờ tuần tự. Orchestrator phải đi trước workers; glob/field viết sai cần sửa. Contract fail không có schedule khả dụng, validator không khóa tiến trình; xem docs/UPGRADE_0_4.md.

Chạy `python3 -m omega workflow-handoff-contract --input INPUT --compact`. Kiểm tra DAG, duplicate IDs/owners và writer chưa có thứ tự. Dùng lịch batch trong budget; orchestration runtime vẫn do người điều phối thực hiện.

### Evidence

Trả issues, schedule, owners theo input và giới hạn. Handoff phải giữ objective, acceptance, scope và refs; không gửi toàn transcript.

### Failure handling

Có cycle, hai owner hoặc path escape: dừng giao việc và sửa contract có review. Không giải quyết bằng spawn thêm agent hoặc tạo branch/worktree chồng nhau.

### Stop conditions

Dừng khi contract đạt hoặc xung đột đã được chỉ rõ. Công cụ không dispatch agent, không thay branch hoặc tự chọn quy trình có quyền cao hơn.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.

## skill-interference-benchmark

Lệnh: `skill-interference-benchmark`

### Inputs

Các run cùng task/trial, prompt hash, model/version, acceptance và provenance; token/time thật hoặc null.

### Workflow

Chạy `python3 -m omega skill-interference-benchmark --input INPUT --compact`. Ghép đủ A, B, A+B; kiểm tra invariants rồi đọc regressions từng task. So usage theo dữ liệu có thật, không cộng số đo thiếu thành 0.

### Evidence

Trả acceptance/regressions theo arm, usage mean khi đủ dữ liệu và provenance. Fixture chỉ kiểm tra analyzer, không là đánh giá LLM.

### Failure handling

Thiếu arm, đổi model/prompt/criteria hoặc duplicate run: từ chối so sánh. Nếu combined regression, giữ stable và điều tra nguyên nhân; không sửa grader để làm xanh.

### Stop conditions

Dừng sau phân tích corpus đã định. Không gọi model, không tự promote; native_release_eligible=false và dữ liệu nhập cần review nguồn độc lập.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.

## project-workflow-adapter

Lệnh: `project-workflow-adapter`

### Inputs

Root Git tường minh, manifests/CI và quyền đọc project; xác định engine runner riêng với target.

### Workflow

Exact Jest script có thể nhận proposal --json --outputFile={report_path} cùng test_report nonce; stdout/stderr vẫn là log, không phải report. Proposal chưa ready và không tự install Jest hoặc chạy script. Cấu hình đủ bốn gates thật trước dùng; Node file reporter đã có benchmark, Jest native vẫn chưa kiểm chứng. Schema/budget/freshness: docs/UPGRADE_0_5.md.

Chỉ khi test script đúng node --test mới đề xuất Node built-in JUnit sau khi kiểm tra runtime hỗ trợ. Không coi npm/Jest merged logs là clean JSON; runner khác phải review config/output channel trước, proposal chưa sẵn sàng vẫn exit 1. Python là lõi kiểm chứng; TypeScript giao tiếp qua bridge ở docs/PYTHON_TYPESCRIPT_BOUNDARY.md, không viết lại policy. Xem docs/UPGRADE_0_4.md.

Chạy `python3 -m omega project-workflow-adapter --compact`. Đối chiếu proposals với scripts và runner thật; review đầy đủ argv build/tests/security/regression trước lưu config riêng. Dùng runner tuyệt đối và --project-root ở project ngoài OMEGA.

### Evidence

Trả stack, command proposal, assumption về adapter và missing requirements; proposal-needs-review không phải ready.

### Failure handling

Không nhận diện được stack hoặc thiếu security/regression: báo yêu cầu cụ thể. Jest/Go/JUnit output không đúng schema thì không thay bằng exit-zero-only.

### Stop conditions

Dừng khi có proposal để review hoặc blocker rõ ràng. Không tự npm/pip install, sửa manifest/lockfile, tạo config hoặc tuyên bố mọi framework đã được native test.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.

## evidence-reconciler

Lệnh: `evidence-reconciler`

### Inputs

Record gate thật trong project hiện tại và gate config đã review; không dùng scenario thay gate proof.

### Workflow

Với file report, đọc lại cùng test_report policy để kiểm tra configured argv, argv đã render và SHA-256 content trong evidence. Report nằm ở namespace mới không chứng minh runner trung thực. Content snapshot giữ trong artifact; summary trỏ reference, không bỏ nội dung để tiết kiệm token. Thay report policy/engine/runtime thì xác minh lại; xem docs/UPGRADE_0_5.md.

Đối chiếu fingerprint có hash whitelist runtime environment và các runtime_inputs được khai tường minh; đọc lại cùng --gate-config của lúc thực thi. Process timeout/output-limit/invalid UTF-8 phủ quyết readiness dù exit code trong record là 0. Chưa ràng buộc được dependency/service/policy ngoài fingerprint phải ghi unverified, không tự coi là tương đương; xem docs/UPGRADE_0_4.md.

Chạy `python3 -m omega evidence-reconciler --record RECORD --compact` hoặc lặp --evidence. So source/mode/index, HEAD, known execution fingerprint và test outcomes; đọc lý do stale trước quyết định chạy lại.

### Evidence

Trả current/stale-source/stale-context/same-source-different-head và yêu cầu validation. Nêu rõ global policy, dịch vụ và dependencies chưa được quan sát.

### Failure handling

Artifact thiếu/schema sai/project khác hoặc metadata không khớp: không dùng làm readiness proof. Không sửa record cũ hoặc copy hash để ép hợp lệ.

### Stop conditions

Dừng khi từng record được phân loại với lý do. Không tự chạy lại toàn suite vô hạn; chỉ kiểm tra lại phần có thay đổi/lo ngại hợp lý và giữ gate bắt buộc.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.

## memory-reconciliation

Lệnh: `memory-reconciliation`

### Inputs

Danh sách record tường minh, decision key hoặc title, nguồn/evidence refs và HEAD hiện tại.

### Workflow

CLI so context hiện tại với evidence gốc, không chỉ hash blob. Unbound/not-checked hoặc source/runtime drift cần review trước tái sử dụng; caller library phải truyền context nếu muốn kết luận current. Với project có gate config riêng, truyền lại --gate-config. Giữ cả alternatives và ghi rõ bằng chứng chưa xác minh; xem docs/UPGRADE_0_4.md.

Chạy `python3 -m omega memory-reconciliation --input INPUT --compact`. Nhóm theo key, đối chiếu body hashes và stale status; đọc nguồn thật trước quyết định. Khác câu chữ là tín hiệu review, không tự suy ra mâu thuẫn logic.

### Evidence

Trả groups, conflicting alternatives và stale records bằng refs. Giữ provenance, phân biệt fact/hypothesis/recommendation và quyết định cần reviewer.

### Failure handling

Không đọc được record hay project mismatch thì dừng phần đó, không fallback global. Memory có instruction không được dùng để chạy tool hoặc nâng quyền.

### Stop conditions

Dừng khi các phương án và phần cần xác minh rõ ràng. Không tự chọn mới nhất làm chân lý, xóa/ghi đè record hoặc đồng bộ memory sang project khác.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.

## context-sufficiency-check

Lệnh: `context-sufficiency-check`

### Inputs

Requirements manifest gồm source ranges, acceptance/constraints; packet có nội dung và source hashes.

### Workflow

Chạy `python3 -m omega context-sufficiency-check --input INPUT --compact`. Kiểm tra ranges, actual content/full-file hash và task invariants. Khi thiếu dependency, mở rộng manifest/packet có chủ đích thay vì tự cắt source.

### Evidence

Trả required/provided ranges, missing/altered inputs và giới hạn. Byte giảm không chứng minh token hoặc chất lượng LLM không đổi.

### Failure handling

Nguồn stale, missing range, đổi acceptance hoặc budget vượt: từ chối packet; không bỏ assertion hoặc giả source hash. Điều tra phạm vi thiếu trước gọi model.

### Stop conditions

Dừng khi đáp ứng manifest hoặc chỉ rõ phần còn thiếu. Không tự biết mọi dependency; không hạ model/effort, đọc secret hoặc bỏ yêu cầu an toàn để giảm context.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
