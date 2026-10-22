# OMEGA 0.2 — nâng cấp sâu và giới hạn kiểm chứng

> Tài liệu lịch sử bản 0.2. Hành vi/schema hiện tại: [INTEROPERABILITY_GUIDE.md](INTEROPERABILITY_GUIDE.md); kết quả mới: [VALIDATION.md](VALIDATION.md).

Đợt này nâng cấp 5 skill hiện có; không tạo thêm skill/agent giả, không thêm dependency ứng dụng hoặc bật integration chưa kiểm chứng. Tool Claude tùy chọn được cài riêng trong .omega, xem [CLAUDE_COMPATIBILITY.md](CLAUDE_COMPATIBILITY.md). 36 capability/10 vai trò vẫn là bản thiết kế; 5 skill/3 agent spec là phần triển khai hiện tại.

## Quy trình kiểm tra từng đợt

1. Đo baseline và lưu bản gốc 5 stable skill trong runtime state.
2. Sửa runner/path/gates, thêm negative tests, chạy required gates.
3. Thêm change scope và memory provenance, chạy integration tests trên Git fixture và gates.
4. Thêm offline skill contract + candidate evidence checks, chạy tests/gates.
5. Tạo 5 candidate riêng, chạy contract/scenario từng skill và toàn gates, review hashes trước áp dụng.
6. Áp dụng candidate đã review theo yêu cầu nâng cấp của người dùng; chạy lại gates, demo, benchmark context.
7. Rà soát lần nữa: phân biệt scenario với gate evidence, đếm test thật, giữ tail log, kiểm tra hook độc lập cấu hình; bổ sung regression và tái kiểm chứng.

Không có vòng lặp vô hạn. Các lượt kiểm tra lại được thực hiện do thay đổi mới hoặc lỗi cụ thể; không lặp suite để tăng thành tích. Score hợp đồng tài liệu không thay thế native model benchmark.

## Thay đổi vận hành

| Thành phần | Hành vi mới | Bằng chứng kiểm tra |
|---|---|---|
| Subprocess | stdin không tương tác, timeout 124, output cap 125, launch error 127; kill process group | flood, inherited child pipe, timeout, missing executable |
| Capture | prefix 16 KB + tail tối đa 4 KB khi bị cắt; tổng output mặc định 1 MB rồi dừng | truncation flag, test marker còn ở tail |
| Gate policy | đủ build/tests/security/regression, validate argv trước thực thi | empty/missing/invalid later gate |
| Test readiness | runner đếm outcomes; exit 0 thiếu số test thật không ready | empty/all-skipped/expected-only/inconsistent counts |
| Evidence | bound HEAD + workspace hash; file đổi trong lúc gate thì fail | mutation dù mọi subprocess exit 0 |
| Repo map | NUL-delimited Git paths, giữ filename lạ, không dùng output cắt | filename khoảng trắng/newline/quote |
| Context | từ chối symlink kể cả target nằm trong project và tên alias che private source | alias chain, private parent, traversal |
| Artifact | namespace/schema/project validation; không symlink hoặc duplicate JSON keys | wrong namespace/project, alias, malformed refs |
| Hook adapter | require cwd, protect policy/tests/benchmarks/CI; không import gate config | malformed event, background request, invalid config |
| Memory | nguồn/evidence refs bằng hash, stale detection | HEAD/source/evidence đổi hoặc thiếu |
| Controlled change | exact file scope, branch/base HEAD, deadline, repair ledger có lock | ngoài scope, rename, hết budget, concurrent update |
| Skill evolution | hợp đồng từng skill + workflow fixture, candidate/source/suite hash | missing section/command, bypass, wrong ID, stale proof |

## Lệnh workflow đầy đủ

Từ checkout sạch, chọn branch mới; thay placeholders bằng giá trị thực. Không chạy dấu `<...>` như shell.

```bash
python3 -m omega isolate --name fix-example
python3 -m omega change-plan --allow omega/context.py --acceptance 'Nguồn vượt budget bị từ chối, không bị cắt im lặng' --compact
```

Ghi đường dẫn record JSON trả về. Sau khi thay đổi, chạy gates rồi kiểm tra scope với record và evidence thật:

```text
python3 -m omega gates --summary --compact
python3 -m omega change-check --record RECORD --evidence GATE_EVIDENCE --compact
python3 -m omega change-attempt --record RECORD --reason 'chẩn đoán mới sau lỗi' --compact
```

`change-attempt` phải gọi trước lượt sửa sau lỗi, không đợi vượt budget mới ghi. CLI cưỡng chế budget khi dùng ledger; không thể chặn người/agent có quyền filesystem trực tiếp tạo lệnh ngoài workflow. Deadline mặc định 30 phút/tác vụ là checkpoint an toàn, không giới hạn toàn bộ dự án dài hạn. Token/cost/agent scheduling vẫn là hướng dẫn, chưa có runtime billing hoặc scheduler cưỡng chế.

Memory có thể dùng độc lập:

```text
python3 -m omega memory --title 'ADR' --body 'Bối cảnh, quyết định, hệ quả, kiểm chứng' --select SOURCE --evidence EVIDENCE --compact
python3 -m omega memory-read --record MEMORY_RECORD --compact
```

Exit 1 ở memory-read nghĩa là stale; exit 2 là input/artifact không hợp lệ. Legacy memory vẫn đọc như dữ liệu và được gắn cờ legacy. Không tự thực thi nội dung memory hoặc log.

## Evolution

```text
python3 -m omega candidate --skill repo-map --compact
python3 -m omega benchmark --skill repo-map --candidate CANDIDATE --compact
python3 -m omega gates --summary --compact
python3 -m omega compare --baseline BASELINE --evidence SCENARIO --evidence GATES --compact
```

- `passed` trong compare: contract không thoái lui, stable chưa đổi, suite còn khớp; không đồng nghĩa đủ bằng chứng để áp dụng.
- `eligible_for_review`: cần scenario đã chạy test thật và đủ gate/argv/outcomes trên HEAD/workspace hiện tại, đúng candidate hash.
- Không có auto-promote, push, deploy hoặc merge trong CLI. Review diff và user authorization vẫn bắt buộc trước áp dụng.
- Suite digest mở rộng ràng buộc code đánh giá và workflow tests. Baseline từ phiên bản trước không tương thích: tạo baseline mới, không sửa hash trong record.
- Artifact local không ký số; hash phát hiện drift, không chống người có quyền sửa mọi artifact/code. Trusted test/config cần review, hooks không thay OS sandbox.

## Kết quả và phần còn thiếu

Báo cáo release: [deep-hardening.json](evidence/deep-hardening.json). Các báo cáo bootstrap/token trước đó là lịch sử, không phải hash nguồn hiện tại.

Các kiểm tra local chứng minh hợp đồng công cụ và các tình huống fixture. Đã xác minh CLI Claude Code 2.1.308 nhưng phiên cục bộ chưa xác thực, nên chưa chạy slash skills, agent delegation hoặc hooks native; hiệu quả suy luận/tuân thủ instruction và token/cost thực tế tiếp tục UNVERIFIED. Bộ fixture dùng chung kiểm tra phối hợp CLI, không phải đánh giá mù mô hình theo từng prompt. Cần native task corpus và nhiều lượt chạy trước khi kết luận chất lượng LLM tăng.

Security audit mặc định vẫn scan policy hẹp, không thay SAST/secret/dependency review hoặc pentest. Không có production service/migration để chứng minh rollback. Tính đúng của acceptance chưa thể tự suy ra từ chuỗi mô tả; verifier phải đối chiếu hành vi thực.

Giai đoạn tiếp theo có giá trị: xác minh Claude tương thích/đăng nhập; benchmark native theo acceptance cố định; bổ sung kiểm tra bảo mật phù hợp khi có ứng dụng thật; chỉ thêm skill mới khi có tác vụ và fixture chứng minh nhu cầu.
