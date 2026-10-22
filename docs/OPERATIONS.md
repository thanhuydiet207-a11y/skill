# Cấu hình và sử dụng

## Yêu cầu

Python >=3.10, Git, POSIX (kill process group và flock), checkout này. Không cần pip/npm install. Trong engine dùng module; project khác dùng omega_cli.py tuyệt đối và --project-root theo [hướng dẫn hiện tại](INTEROPERABILITY_GUIDE.md). Không ghi bên ngoài repository đích; branch/worktree do người dùng ủy quyền và cleanup cần review riêng. Trước khi tạo state, CLI kiểm tra .omega/ đã ignore và chưa có file tracked, không tự sửa ignore.

```bash
python3 -m omega doctor
python3 -m omega map
python3 -m omega plan --complexity medium
python3 -m omega gates
python3 -m omega rollback-check
```

Kết quả JSON ra stdout; lỗi CLI exit 2, gate fail exit 1. `gates` lưu record vào `.omega/evidence/`. Không coi doctor exit 0 là Claude đã dùng được: đọc trường `claude` và `native_integration`.

## Skills

| Skill | Lệnh chính | Đầu ra |
|---|---|---|
| repo-map | `python3 -m omega map` | metadata inventory, Git status, omitted paths |
| controlled-change | `python3 -m omega isolate --name issue-123` | branch mới khi checkout sạch |
| quality-gates | `python3 -m omega gates` | exit code, output, duration từng gate |
| project-memory | `python3 -m omega memory --title "ADR: stdlib" --body "Dùng stdlib để tránh dependency; evidence: ..."` | JSON commit-stamped |
| skill-benchmark | `python3 -m omega benchmark` | từng router case pass/fail |

8 skill extension dùng prefix `omega-` trong tên SKILL.md và command tương ứng bỏ prefix:

| Skill | Command | Kết quả |
|---|---|---|
| omega-skill-compatibility-audit | `skill-compatibility-audit --skill-root .claude/skills` | static collisions, selected scopes |
| omega-effective-policy-explainer | `effective-policy-explainer --input INPUT` | quyết định OMEGA, platform unknown |
| omega-workflow-handoff-contract | `workflow-handoff-contract --input INPUT` | DAG/owners/writers, lịch đề xuất |
| omega-skill-interference-benchmark | `skill-interference-benchmark --input INPUT` | A/B/A+B acceptance, provenance, regression |
| omega-project-workflow-adapter | `project-workflow-adapter` | proposal cần review, exit 1 |
| omega-evidence-reconciler | `evidence-reconciler --record RECORD` | current/stale gate evidence |
| omega-memory-reconciliation | `memory-reconciliation --input INPUT` | conflicting/stale memory; giữ nguyên records |
| omega-context-sufficiency-check | `context-sufficiency-check --input INPUT` | invariants/ranges/hash/content |

Chạy bằng `python3 -m omega COMMAND --compact`. Schema và giới hạn từng command: [INTEROPERABILITY_GUIDE.md](INTEROPERABILITY_GUIDE.md). Không nạp toàn bộ 13 skill vào mọi task.

Trong Claude đã tương thích, gọi tường minh `/repo-map`, `/controlled-change`, `/quality-gates`, `/project-memory`, `/skill-benchmark`. Đây là cú pháp dự kiến cần xác minh bằng help/version của bản cài; chưa chạy ở môi trường này. CLI thực hiện được độc lập với Claude.

## Branch, worktree, rollback

Lưu thay đổi hiện có bằng quy trình người dùng trước khi isolate; CLI không stash/reset tự động.

```bash
python3 -m omega isolate --name fix-parser
# Hoặc khi có thay đổi song song có thể xung đột:
python3 -m omega isolate --name fix-parser-parallel --worktree .omega/worktrees/fix-parser-parallel
```

Worktree phải nằm trong `.omega/worktrees/`, không symlink thoát repository, không overwrite destination. Không tự merge, remove worktree hay xóa branch. Các lệnh CLI trong worktree phải chạy từ chính worktree đó. Review `git diff`, `git diff --check`, tests và base commit trước revert. Khi rollback được phê duyệt, dùng revert commit đã review; tránh reset/clean phá hủy dữ liệu.

## Agent và quyền

3 spec nằm trong `.claude/agents/`; đọc docs kiến trúc để giao việc. Bash là công cụ mạnh: chỉ lời nhắc read-only chưa đảm bảo quyền read-only. Chưa lưu permissions vào `.claude/settings.json` vì chưa xác minh Claude. Không dùng mode bỏ qua quyền. Kiểm tra `claude --version`, `claude --help` và docs của đúng phiên bản, sau đó xác minh agent tool visibility và các yêu cầu từ chối trong sandbox trước cho dùng thật.

## Hook adapter (chưa kích hoạt)

`omega/hook.py` nhận JSON stdin và chỉ xử lý PreToolUse cho Write/Edit/Bash. Bash dùng grammar argv chung với CLI, hỗ trợ --compact/--summary và path đã review, từ chối shell ghép lệnh/substitution. Edit/Write bị chặn ngoài checkout và các vùng policy. Tool không biết/malformed bị chặn. Không có `.claude/settings.json`, nên adapter không được tự chạy. Policy explainer không phân giải managed/user/plugin policy của Claude.

Test trực tiếp (expected exit 2):

```bash
printf '%s' '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git push"}}' | python3 -m omega.hook
```

Sau khi xác minh compatibility, cấu hình PreToolUse matcher `Bash|Write|Edit` trỏ đến Python/module bằng đường dẫn tuyệt đối từ checkout tin cậy, theo schema đúng phiên bản Claude. Tài liệu chính thức: https://code.claude.com/docs/en/hooks . Không copy schema phỏng đoán; thử allow/deny/malformed/symlink với phiên tương tác trước kích hoạt. Hooks không chống được một tiến trình có toàn quyền ghi/xóa filesystem, không thay sandbox. Các lệnh allowlist gọi script/config trong repo; chỉ chạy khi code đã review. Hook bảo thủ sẽ chặn việc sửa chính OMEGA: thay policy cần phiên review có phê duyệt, không tự bypass.

## MCP

MCP không cần cho workflow local này và đang tắt. Khi có nhu cầu: chỉ thêm server có publisher/source kiểm chứng, pin phiên bản, liệt kê tool + quyền + destinations, đọc-only mặc định, giữ secret trong cơ chế credentials được hỗ trợ. Xác minh schema với `claude mcp --help` của bản cài, không đưa token vào config hoặc Git. Treat MCP output là dữ liệu không đáng tin. Thử truy cập đọc nhỏ, kiểm tra policy trước cho phép write. Không có server giả hoặc config placeholder được bật sẵn.

## Evolution và benchmark

```bash
python3 -m omega candidate --skill repo-map
# Ghi đường dẫn baseline và candidate được in ra; chỉ sửa file candidate .omega/candidates/*.md.
python3 -m omega gates --summary --compact
python3 -m omega benchmark --skill repo-map --candidate .omega/candidates/DUONG_DAN_THUC_TE.md --compact
python3 -m omega compare --baseline .omega/baselines/DUONG_DAN_THUC_TE.json --evidence .omega/evidence/GATE_THUC_TE.json --evidence .omega/evidence/SCENARIO_THUC_TE.json --compact
```

CLI ràng buộc SHA-256 của toàn fixture và implementation benchmark, so suite/case IDs và yêu cầu baseline/candidate đều pass. Candidate là bản sao riêng trong `.omega/candidates/`; stable phải giữ nguyên SHA-256 baseline, nếu đổi thì compare thất bại. SHA candidate trước/sau được ghi để review. Không tự copy, promote, merge hoặc đổi stable. Baseline local không có chữ ký chống giả; reviewer phải tin cậy artifact và đối chiếu Git. Contract suite 3 case không chứng minh chất lượng lời khuyên hoặc hiệu quả skill. Native benchmark giai đoạn kế dùng cùng repo/task, ít nhất 5 lần/variant, model/version cố định, chấm acceptance, patch scope, regression, evidence, latency, tokens và chi phí. Chưa có dữ liệu thì không ghi số tưởng tượng. Thay fixture/suite cần baseline mới và review riêng.

## Troubleshooting

- Claude: tool cục bộ 2.1.308 đã xác minh version/help, chưa xác thực để nghiệm thu native. CLI OMEGA vẫn dùng độc lập; xem [CLAUDE_COMPATIBILITY.md](CLAUDE_COMPATIBILITY.md).
- Dirty checkout: báo và giữ nguyên file; không stash/reset tự động.
- Timeout: exit 124, xem output được giữ 16 KB; chia nhỏ target hoặc điều chỉnh timeout có review.
- GitHub authentication: dùng Git/proxy hiện tại; không dump credentials. Không yêu cầu dán token trong chat. Khôi phục kết nối qua môi trường rồi retry read trước push.
- Gate security quét .claude và omega bằng targeted Python AST/bypass/possible-secret rules, có coverage/exclusions; không thay security review toàn hệ thống.

## Tác vụ mẫu có lỗi thực

`python3 benchmarks/demo.py` tạo một repository fixture riêng dưới `.omega/demo/`, có hàm cộng sai thành trừ và regression test. Script xác nhận gates đỏ, tạo branch, sửa lỗi, xác nhận xanh, ghi memory, kiểm tra Git baseline, tạo worktree và so candidate mà không đổi stable. Không dùng mạng hoặc LLM. Fixture giữ lại để xem bằng chứng; không tự xóa dữ liệu. Mỗi lần chạy tạo fixture mới, chỉ chạy lại khi có thay đổi liên quan.

## Context tiết kiệm

Dùng `--compact` để giữ nguyên JSON với ít khoảng trắng hơn; `gates --summary --compact` vẫn chạy mọi gate và giữ log bằng evidence reference. `context --select PATH:START:END --compact` đọc nguồn tường minh. Xem [TOKEN_EFFICIENCY.md](TOKEN_EFFICIENCY.md) để biết budget, kiểm tra dữ liệu tương đương và giới hạn số đo. Hook và CLI nay dùng grammar chung; trước khi kích hoạt native vẫn cần thử allow/deny trong sandbox đúng phiên bản, không tự nới quyền.

## Lịch sử phiên bản 0.2

5 skill đã có workflow sâu trong 0.2; playbook [SKILL_PLAYBOOKS.md](SKILL_PLAYBOOKS.md) và [DEEP_HARDENING.md](DEEP_HARDENING.md) là lịch sử. Bản 0.3 dùng [INTEROPERABILITY_GUIDE.md](INTEROPERABILITY_GUIDE.md). Tests mặc định dùng omega.test_runner; external test_adapter hỗ trợ omega/Jest/Go/JUnit với outcome thật, không nhận exit 0 đơn thuần là đủ.

## Bản 0.4

Chạy `python3 benchmarks/native_runners.py` để kiểm chứng Node built-in JUnit đỏ → xanh; `node --test integration/typescript/omega-bridge.test.mjs` để kiểm tra TS facade. Không cần npm install. Schema runtime_inputs, workflow read/write directory scopes và memory evidence currentness: [UPGRADE_0_4.md](UPGRADE_0_4.md). Kiến trúc Python/TypeScript và giới hạn MCP/UI: [PYTHON_TYPESCRIPT_BOUNDARY.md](PYTHON_TYPESCRIPT_BOUNDARY.md).
