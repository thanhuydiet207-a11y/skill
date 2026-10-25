# OMEGA 0.7 — plugin cho Claude Code

## Cài từ GitHub

Trong Claude Code:

```text
/plugin marketplace add thanhuydiet207-a11y/hutao
/plugin install omega@omega-marketplace
```

Hoặc một lệnh trên phiên bản hỗ trợ option marketplace:

```text
/plugin install omega --marketplace thanhuydiet207-a11y/hutao
```

Khởi động lại phiên Claude Code để áp dụng, rồi gọi:

```text
/omega:omega phân tích repository hiện tại
/omega:omega sửa lỗi đang mô tả, giữ API và chạy kiểm thử
```

CLI tương ứng có thể dùng `claude plugin marketplace add thanhuydiet207-a11y/hutao`, `claude plugin install omega@omega-marketplace --scope user` và `claude plugin list --json`. Có thể chọn scope project/local theo chính sách của project; không copy settings từ môi trường thử nghiệm.

Định dạng này dành cho plugin Claude Code. Chỉ upload SKILL.md hoặc ZIP như tài liệu trong Claude Web không thực thi engine. Bản đã kiểm chứng là Claude Code **2.1.308**; kiểm tra `claude --version` và `claude plugin --help` ở máy dùng thật. Cài đặt/discovery đã được thử, phiên suy luận native và hiệu quả token vẫn chưa nghiệm thu.

## Thành phần

| Thành phần | Nguồn |
|---|---|
| Manifest plugin omega | .claude-plugin/plugin.json |
| Marketplace omega-marketplace | .claude-plugin/marketplace.json, source ./ |
| Một skill, 13 mode references | .claude/skills/omega/SKILL.md và references/ |
| Ba agent | agents/omega-investigator.md, omega-engineer.md, omega-verifier.md |
| Python engine | omega_cli.py và omega/ |

Manifest khai custom skills path để giữ một nguồn SKILL.md. Agents dùng thư mục chuẩn agents/: native inventory phải hiện **1 skill, 3 agents, 0 hooks, 0 MCP servers**. Không đăng ký hook, MCP, startup command, permission override, installer script hoặc dependency tự cài. Agent tool list/prompt không thay permissions/sandbox của host; vẫn cần review lệnh thực tế.

Trong checkout nguồn, `/omega` là project skill. Bản cài plugin dùng namespace `/omega:omega`. Nếu bật plugin ngay trong chính checkout OMEGA, có thể thấy cả hai cách gọi từ cùng nguồn; không có file alias thứ hai. File .claude/CLAUDE.md phục vụ bảo trì checkout, không được coi là context tự động của plugin. Skill/agent mang quy tắc thiết yếu và đọc policy của project đích.

## Tiết kiệm token mà không cắt chất lượng

Các tối ưu tích hợp sẵn là tùy chọn và lossless theo contract đã kiểm tra:

- `--compact` giảm whitespace ngoài JSON string; parse lại phải cho cùng object.
- `context --select PATH[:START:END]` chỉ gửi nguồn được chọn tường minh, giữ nội dung, dòng và hash; vượt budget thì báo lỗi, không âm thầm bỏ nguồn.
- `gates --summary --compact` vẫn chạy mọi gate, giữ kết quả và mã thoát; log thành công có thể được tham chiếu trong evidence. Lỗi vẫn phải hiện đủ để điều tra.
- RTK là tùy chọn ở cấp shell, không phải dependency plugin. Không tự cài hoặc sửa shell config. Nếu summary không đủ rõ, chạy lệnh gốc và xem raw output.

Hướng dẫn và giới hạn: [TOKEN_EFFICIENCY.md](TOKEN_EFFICIENCY.md), [RTK_INTEGRATION.md](RTK_INTEGRATION.md). Số byte không chứng minh số token billing hoặc chất lượng LLM không đổi; cần A/B trên cùng task/model/gates và đọc token usage từ runtime/provider.

## Chạy engine trong project khác

Plugin đã chứa Python engine; không pip install vào project và không chạy module omega do project cung cấp. Claude Code cung cấp `${CLAUDE_PLUGIN_ROOT}` cho tài nguyên plugin. Ví dụ, sau khi xác nhận cwd đúng Git root đích:

```bash
python3 -B "${CLAUDE_PLUGIN_ROOT}/omega_cli.py" --project-root "$PWD" map --compact
python3 -B "${CLAUDE_PLUGIN_ROOT}/omega_cli.py" --project-root "$PWD" plan --complexity medium --compact
```

Tất cả ví dụ `python3 -m omega COMMAND ...` trong references là cách viết ngắn cho checkout engine. Khi dùng plugin phải thay bằng runner tuyệt đối như trên; không chạy module từ cwd. Nếu thiếu biến plugin root, dùng đường dẫn được runtime xác minh, không tự đoán. Runtime Python cần >=3.10, Git và POSIX cho process groups/flock. TypeScript bridge vẫn tùy chọn; target Python workflow không cần cài Node/npm dev tools của engine.

Read operations kiểm tra đúng project. State/gates/memory ghi vào target .omega/, chỉ khi ignore đã review và không tracked; không tự sửa .gitignore. External gates cần đủ bốn argv được review qua --gate-config .omega/configs/FILE.json. Không dùng engine build làm bằng chứng ứng dụng target đã build. Engine entrypoint tắt ghi bytecode và ví dụ dùng -B để không sửa plugin cache; fixture còn kiểm tra cache không đổi sau red → fix → green.

Candidate/compare/benchmark skill chỉ dùng trong checkout engine có Git và prerequisites đã review. Không evolution tại cache plugin hoặc ghi sang repo nguồn từ tác vụ target.

## Thử local và xuất ZIP

Từ checkout sạch hoặc sau khi stage đầy đủ các file dự kiến:

```bash
python3 benchmarks/plugin_packaging.py
```

Lệnh xuất chỉ file Git tracked vào namespace mới .omega/plugin-packaging/runs/…/marketplace và omega.zip, kèm JSON path/hash. Không đóng gói .git, .omega, node_modules hoặc ghi chú untracked; từ chối symlink và vượt budget (512 files, mỗi file 1 MiB, tổng 8 MiB). Không cài dependency, không cleanup/xóa artifact cũ. Output cho biết HEAD và hashes của working bytes; HEAD một mình không chứng minh checkout sạch. ZIP dùng timestamp cố định; cùng bytes/path và toolchain thì nội dung ZIP xác định.

Thử phiên local không ghi cấu hình cài đặt thường dùng:

```bash
claude --plugin-dir /ABS/CHECKOUT
# Hoặc path omega.zip thực tế do benchmark vừa tạo:
claude --plugin-dir /ABS/omega.zip
```

Native install probe tùy chọn, chỉ chạy khi đã có binary Claude tin cậy:

```bash
python3 benchmarks/plugin_packaging.py --claude /ABS/claude
```

Probe tạo CLAUDE_CONFIG_DIR riêng dưới .omega, validate strict cả hai manifest, thêm marketplace local, cài user scope trong state riêng, đọc inventory từ bản cài và từ ZIP, gọi engine trong **install cache** với project fixture độc lập. Fixture cố tình có omega.py khác để kiểm tra không import nhầm, có bug cộng thành trừ để thấy tests đỏ rồi xanh, và đối chiếu cache trước/sau. Không gửi prompt/model request hoặc thay config Claude của người dùng. Logs khi lỗi được giữ trong native-commands.json; không dùng output thiếu/thất bại làm pass.

Khi chạy validate bằng tay, chỉ rõ từng manifest:

```bash
claude plugin validate .claude-plugin/plugin.json --strict --json
claude plugin validate .claude-plugin/marketplace.json --strict --json
```

Validate thư mục chứa cả hai có thể chọn marketplace thay plugin; không dùng một lần validate để tuyên bố cả hai đã đạt. Đây là kiểm tra plugin tự host trên GitHub; chưa nộp lên official plugin directory hoặc hoàn tất tiêu chí listing riêng. Không tự chọn license cho chủ repository.

## Kiểm chứng và giới hạn

Bằng chứng snapshot: [plugin-packaging.json](evidence/plugin-packaging.json). Plugin lifecycle/discovery không chứng minh Claude đã dùng skill/agent để giải tác vụ. Model auth, activation trace của phiên suy luận, A/B, token/cost và native quality tiếp tục unverified; projected token cost của inventory chỉ là ước tính.

Npm dev tools đã pin vẫn cần nếu phát triển và chạy full engine build; plugin install không tự cài chúng. Build/tests/security/regression kiểm tra scope cụ thể, không là chứng nhận toàn diện. Hook adapter vẫn có trong source để review sau, chưa được plugin đăng ký. Bộ đếm subtest thất bại cũ là known issue riêng, chưa sửa bởi việc đóng gói.

Chỉ update plugin sau review diff, benchmark/gates. Rollback plugin bằng phiên bản/commit đã review và quy trình cài đặt hỗ trợ của Claude Code; dữ liệu .omega trong target là state project riêng, không tự xóa khi đổi plugin.
