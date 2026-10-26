# OMEGA 0.6 — kết hợp skill và chạy trên project khác

## Những gì đã thực thi được

OMEGA có một skill omega với 5 mode references; tám lệnh phân tích dưới đây không còn là chế độ, hướng dẫn gốc ở [EXTENSIONS.md](EXTENSIONS.md); xem [UNIFIED_SKILL.md](UNIFIED_SKILL.md). Tám command phân tích interoperability chạy local bằng Python chuẩn. Chúng không cài skill ngoài, không gọi model/MCP, không tự dispatch agent, không sửa policy hoặc chọn người thắng cho quyết định kỹ thuật. Một proposal hoặc static check không phải chứng nhận tương thích native.

5 skill cũ giữ tên để không phá lời gọi đã có. 8 skill mới dùng tiền tố `omega-` để giảm trùng tên. Đây là tên file/frontmatter, không phải khẳng định plugin namespace đã được Claude đăng ký. OMEGA không tự có quyền ưu tiên cao hơn skill khác.

## Runner và repository đích

Trong checkout OMEGA có thể dùng `python3 -m omega`. Ở project khác, dùng đường dẫn tuyệt đối đến runner đã review và root Git tường minh:

```text
python3 /ABS/OMEGA/omega_cli.py --project-root /ABS/PROJECT map --compact
python3 /ABS/OMEGA/omega_cli.py --project-root /ABS/PROJECT gates --gate-config .omega/configs/gates.json --summary --compact
```

Không chỉ copy thư mục SKILL.md rồi giả định module omega đã tồn tại ở project khác. Không dùng module omega do project đích tình cờ cung cấp. Runner chọn engine từ vị trí cài, target từ flag; state nằm ở .omega của target. Review ignore cho `.omega/` trước khi ghi state; CLI từ chối ghi nếu chưa ignore hoặc có state tracked, không tự sửa .gitignore/global config. Gate config ngoài engine phải được chỉ định rõ, chứa schema=1, đủ bốn argv build/tests/security/regression và test_adapter. Không tự cài dependency.

## Policy và trạng thái hiệu lực

Hook adapter và command `effective-policy-explainer` dùng chung grammar với CLI. Cho phép các cờ đã biết, từ chối shell composition/substitution, command tùy ý, root mismatch, path private/escape và background request. Không cho phép mọi Bash để làm workflow chạy được. Hook vẫn **chưa đăng ký/kích hoạt** trong Claude.

`doctor` trả hooks_enabled/mcp_enabled=`unknown` khi chưa phân giải cấu hình platform. `effective-policy-explainer` chỉ giải thích OMEGA, trả platform_decision=unknown. Native permissions, managed/user/plugin hooks có thể từ chối thêm; output allowed=true không cấp quyền thực thi.

## Input document

Các command nhận --input là JSON <=1 MB trong project, hoặc `.omega/inputs/*.json`; gate policies ở `.omega/configs/*.json`. Không symlink, duplicate keys, NaN/Infinity hoặc nesting quá sâu. Không ghi secret trong input. Lệnh chỉ đọc nội dung theo schema, không thực thi lệnh trong tài liệu. Output có thể là thông tin project: review trước khi chia sẻ.

## Compatibility audit

```text
python3 -m omega skill-compatibility-audit --skill-root .claude/skills --hook-config .claude/settings.json --compact
```

Chỉ quét roots/config được chọn: tối đa 8 roots, 128 skill, 512 thư mục/root. Không mặc định đọc `~/.claude` hoặc managed settings. Trùng tên, hook chồng event và workflow ownership được gắn cờ; ngôn ngữ trong prompt chỉ là signal, không chứng minh side effect. YAML ngoài safe subset yêu cầu review; không được gọi là native-invalid chỉ vì parser OMEGA không hỗ trợ. `passed` chỉ là static checks, native_compatibility_verified luôn false.

## Workflow handoff

Input:

```json
{"max_agents":2,"nodes":[
  {"id":"main","role":"orchestrator","agents":0,"owns":["workflow","git"]},
  {"id":"implement","role":"worker","after":["main"],"writes":["src/app.py"]},
  {"id":"verify","role":"reviewer","after":["implement"],"owns":["gates"]}
]}
```

`workflow-handoff-contract --input INPUT` kiểm tra DAG, một orchestrator đi trước workers, tối đa một owner/resource và unordered reader/writer hoặc writer/writer. writes/reads khai exact files, write_dirs/read_dirs khai subtree; không hỗ trợ glob hoặc node field viết sai. Invalid contract trả schedule rỗng. Chỉ orchestrator được khai báo agents=0; worker không được bỏ chi phí agent. Trả lịch batch trong budget không vượt cấu hình engine và tối đa 2 agent; không tự tạo agent. Không yêu cầu workflow không dùng memory phải có owner memory. Plan có thể nhận JSON `{intent,complexity,conflict,workflow}` để chọn một trong change/investigate/verify/knowledge/evolve/interoperability. Intent là đầu vào tường minh, không phải tự suy luận từ mọi prompt.

## Project workflow adapter và test outcomes

`project-workflow-adapter` đọc manifest và đề xuất build/test cho Node/Go/Python. Nó trả proposal-needs-review và exit 1, không tự viết config hay cài gói. Cần chọn security/regression thật theo dự án; không biến compile thành security assurance. Config hợp lệ về hình thức vẫn là executable policy cần review.

Adapters: omega marker; Jest JSON; Go `test -json`; JUnit XML. Exit zero, zero-test, all-skipped, counts mâu thuẫn, structured output bị cắt hoặc XML entity không đủ để pass. Go package-pass không tính là test. Jest adapter chỉ phù hợp khi script test thực sự xuất Jest JSON. Kiểm thử local có Python target thật; Node built-in JUnit đã có benchmark thực thi thật; Jest/Go vẫn là parser fixtures. Không tuyên bố đã chạy mọi framework native. Đề xuất npm/Jest mặc định không được coi là clean JSON vì stdout/stderr có thể trộn log; proposal yêu cầu review thay vì xuất command không bảo đảm phù hợp.

## Evidence và scope

Fingerprint nguồn gồm nội dung, permission mode và Git index entries. Known execution fingerprint thêm interpreter/tool metadata, config, hash policy project, hash whitelist environment và optional runtime_inputs tường minh; không đọc/in secret hoặc credential values. Không đại diện toàn bộ dependencies bị ignore, managed/global policy, API, model hoặc môi trường dịch vụ.

`evidence-reconciler --record RECORD` hoặc lặp --evidence phân biệt current, stale-source, stale/unbound execution context, cùng source nhưng khác HEAD và record không phải gate thành công. Không sửa report cũ hoặc tự coi khác HEAD là đạt. Input source/index thay đổi sau check thì chạy lại phần cần thiết. Stage thay đổi dự kiến trước final gates để không làm proof cũ sau đó.

`change-plan --include-existing` chỉ dùng khi đã review thay đổi người dùng hiện có. Snapshot baseline giúp giữ file ngoài scope nguyên trạng, không stash/reset. Merge conflict chưa giải quyết bị từ chối. `change-check` phân biệt scope_passed và ready_for_review; scope pass không thay gate/acceptance. CLI budget chỉ cưỡng chế khi dùng ledger, không là OS sandbox.

## Memory reconciliation

`memory --key database-choice ...` gắn decision key. `memory-reconciliation --input INPUT` nhận `{records:[PATH,...]}`, nhóm theo key/title, báo body khác nhau và stale refs, giữ nguyên mọi record. Khác câu chữ là tín hiệu cần review, chưa chứng minh hai ý mâu thuẫn. `memory-read` phân loại stale soft (chỉ HEAD) và hard (nguồn/evidence drift); vẫn yêu cầu review khi stale.

Không tự nhập memory ngoài project, không đồng bộ global hoặc chọn mới nhất làm chân lý. Chia sẻ liên-worktree/máy chưa được tự động hóa; project identity và provenance cần review riêng trước mở tính năng đó.

## Context sufficiency

Tạo packet bằng context --select; có thể dùng --input task JSON để giữ acceptance/constraints. Input của `context-sufficiency-check`:

```json
{"requirements":{"acceptance":["hành vi cần đạt"],"constraints":["không cài dependency"],"sources":[{"path":"src/app.py","start":1,"end":20}]},"packet":{"task":{"acceptance":["hành vi cần đạt"],"constraints":["không cài dependency"]},"sources":[]}}
```

Tool so task invariants, ranges bắt buộc, nội dung thực và full-file hash. Packet thiếu nguồn ở ví dụ trên sẽ fail. Không tự suy ra dependencies chưa được người điều phối liệt kê, không dùng packet nhỏ làm bằng chứng chất lượng không đổi. Giữ byte budget, không cắt âm thầm.

## Skill interference benchmark

`skill-interference-benchmark --input INPUT` nhận `{runs:[...]}`; mỗi run có task_id, trial, arm=A/B/A+B, model, model_version, grader_version, prompt_sha256 (hash task prompt chung, không phải toàn prompt chứa skill), skill_bundles (map label A/B tới SHA-256 bundle), acceptance (boolean theo cùng tiêu chí), provenance=fixture/native/manual, tokens và duration_ms (nullable). Arm A phải khai đúng bundle A, B khai B, A+B khai cả hai; hash từng bundle giữ cố định toàn corpus. Grader version cũng giữ cố định.

Bắt buộc ghép đủ ba arm cho cùng task/trial, prompt/model/version/criteria giữ cố định, không trùng run, không trộn provenance. Báo regression khi một baseline đạt nhưng tổ hợp fail; usage thiếu là null, không phải 0. Đây là analyzer của dữ liệu nhập, không xác thực được dữ liệu provider hoặc chất lượng semantic grading. Native release không được tự phê duyệt; không phát request model từ tool này.

Fixture trong tests/test_new_skill_workflows.py và tests/test_interop_safety.py chỉ chứng minh logic xử lý kết quả, không là thành tích LLM hoặc tỷ lệ tiết kiệm token. Native A/B cần phiên đã xác thực, ngân sách và corpus/grader độc lập; hiện chưa chạy. Prompt và acceptance phải cố định theo từng task qua các trial; mỗi task có thể có criteria riêng. Không regression vẫn chưa đủ nếu toàn bộ A+B không đạt acceptance.

## Skill contracts và release

Frontmatter safe subset chấp nhận metadata/license và các trường nhận biết, không tự chạy hooks/commands. Section rỗng không đạt advanced contract. Contract completeness không là quality score: quality_evaluated=false và quality_score=null. Candidate bundle hash ràng buộc SKILL.md cùng các references nhận diện được; vẫn cần kê khai/review tài nguyên động chưa được phát hiện tự động.

Ghi candidate trước sửa, benchmark đúng pattern workflow, gates cùng source/runtime, compare kèm cả evidence. `eligible_for_review` chỉ là offline tooling review; native_release_eligible=false. CLI không tự promote, push hoặc deploy. Bản sửa stable cần user authorization đã có và review diff; sau áp dụng chạy lại kiểm tra.

## Cập nhật 0.4

Security gate quét .claude và omega bằng targeted static rules; source bị thiếu/symlink/binary/quá budget làm fail, generated __pycache__ có exclusions tường minh. Memory CLI kiểm tra source/runtime của evidence đính kèm; blob không đổi chưa đủ current. Gate config thêm optional runtime_inputs. Chi tiết và bằng chứng: docs/UPGRADE_0_4.md. Python core và TypeScript facade: docs/PYTHON_TYPESCRIPT_BOUNDARY.md; MCP server/UI vẫn chưa triển khai.

## Cập nhật 0.5

Test_report optional cho Jest/JUnit dùng .omega/reports/{run_id}/FILENAME và {report_path} trong đúng args tests; nội dung report được lưu/hash, summary có reference, không tái sử dụng report cũ. Full engine build thêm strict TypeScript compiler từ dev tools đã pin; bridge có tổng request budget, deadline stdin và cancellation. Schema, setup, kiểm chứng/giới hạn: docs/UPGRADE_0_5.md.

## Consolidation 0.6

Plan trả skills=[omega], modes và references theo intent. Các tên capability cũ còn là mode IDs trong catalog, không là entry SKILL.md. Evolution dùng --skill omega, router-contract-v2 và baseline mới. Benchmark skill chạy toàn Python suite; bundle hash theo cả reference và docs bắc cầu nhận diện được. Chỉ đọc reference đang cần khi điều phối; validator hash trên filesystem không là model preload. CLI chức năng/argv policy giữ nguyên.
