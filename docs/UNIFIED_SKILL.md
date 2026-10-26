# OMEGA 0.6: một skill, 13 chế độ (từ 0.7.5 còn 5; tám chế độ mở rộng chuyển sang [EXTENSIONS.md](EXTENSIONS.md))

> Snapshot thiết kế consolidation 0.6. Bản 0.7 giữ một skill này và đóng gói plugin; xem [CLAUDE_PLUGIN.md](CLAUDE_PLUGIN.md) để cài và gọi /omega:omega. Các số liệu 204 tests bên dưới thuộc snapshot 0.6.

## Cách dùng

Trong Claude Code, gọi entry duy nhất:

```text
/omega phân tích repository này và chỉ ra rủi ro
/omega sửa lỗi đang được mô tả, giữ API và chạy kiểm thử
/omega quality-gates kiểm tra thay đổi hiện tại
/omega kiểm tra xung đột với các skill khác đang dùng
```

Đây là yêu cầu cho Claude điều phối theo skill, không phải Python tự diễn giải ngôn ngữ tự nhiên. Engine vẫn chạy bằng argv đã review. Frontmatter không đặt disable-model-invocation: Claude có thể tự gọi khi tác vụ khớp description, người dùng vẫn gọi tường minh được. Phiên local mới xác minh Claude Code 2.1.308 bằng version/help; native activation và reasoning chưa nghiệm thu.

Phải có checkout chứa omega, omega_cli.py, docs và skill bundle để dùng công cụ. Chỉ đưa SKILL.md vào Claude Web không làm `python3 -m omega` xuất hiện. Nếu môi trường chỉ đọc hướng dẫn, ghi **manual guidance only / engine not run**; không tạo kết quả giả hoặc nhận phiên đó là benchmark engine.

## Cấu trúc và tải theo nhu cầu

```text
.claude/skills/omega/
  SKILL.md                  # entry/routing và quy tắc dùng chung
  references/*.md           # 13 quy trình từ các skill trước
omega/modes.json            # mode -> commands và reference
omega/catalog.json          # 13 chế độ đã triển khai; phần chưa làm ở docs/ROADMAP.md
```

Các tài liệu reference không có frontmatter skill và không mang tên SKILL.md. Nội dung quy trình cũ được giữ nguyên khi chuyển; chỉ bỏ frontmatter đăng ký riêng. Không có 13 alias skill ẩn hoặc skill placeholder. Ba agent spec vẫn ở agents/; gộp skill không chứng minh agent runtime đã chạy.

Entry có bảng để đọc đúng reference theo ý định. Không preload tất cả tài liệu. Plan chỉ đọc metadata, trả skills=[omega], modes và references của intent; không gửi nội dung reference vào packet và không tự dispatch agent. Với bước cần công cụ khác, đọc reference tương ứng tại thời điểm dùng. Contract validator đọc các tài liệu để hash/kiểm tra integrity; việc đó không phải nạp tất cả vào context của model.

## Chuyển từ bản 0.5

| Trước | Từ 0.6 |
|---|---|
| /repo-map, /quality-gates, các slash skill riêng | /omega với tác vụ hoặc mode ID cũ |
| 13 SKILL.md | Một .claude/skills/omega/SKILL.md + 13 references |
| --skill repo-map hoặc tên extension | --skill omega; tên cũ bị từ chối với migration hint |
| plan.skills chứa nhiều tên cũ | plan.skills=[omega]; modes giữ tên chế độ được chọn |
| extensions.json là registry skill bổ sung | modes.json chứa cả 13 chế độ |
| router-contract-v1 | router-contract-v2; cần baseline mới |

Các command chức năng như map, plan, gates, context, memory, memory-read, isolate, change-plan/check/attempt, audit và tám command interoperability giữ nguyên. Hook grammar và bridge đọc Python tiếp tục dùng cùng CLI. Một skill không cấp quyền mới, không tự cài dependency hoặc kích hoạt hook/MCP.

## Benchmark và bằng chứng

```bash
python3 -m omega candidate --skill omega --compact
# Sửa đúng candidate được in ra; giữ stable và references baseline.
python3 -m omega benchmark --skill omega --candidate .omega/candidates/FILE_THUC_TE.md --compact
python3 -m omega gates --summary --compact
python3 -m omega compare --baseline .omega/baselines/BASELINE_THUC_TE.json --evidence .omega/evidence/SCENARIO_THUC_TE.json --evidence .omega/evidence/GATES_THUC_TE.json --compact
node --test integration/typescript/omega-bridge.test.mjs
```

Benchmark --skill omega chạy toàn bộ Python regressions, gồm workflow nền tảng và interoperability, thay vì chọn một nhóm theo tiền tố tên. Gate build tiếp tục compile Python và strict TypeScript noEmit; Node integration tests chạy riêng. Chạy lặp không được cộng thành test mới hoặc chất lượng LLM.

Contract kiểm tra entry, 13 mode references, commands từng mode và các resources liên kết. Bundle hash gồm reference markdown và docs nhận diện được theo liên kết bắc cầu; vòng tham chiếu được deduplicate, symlink/missing file bị từ chối. Giới hạn 64 resources, mỗi file <=1 MiB và tổng <=1 MiB; entry <=8192 bytes. Đây là phạm vi liên kết được validator hỗ trợ, không phát hiện mọi tài nguyên động hoặc thay OS sandbox.

Sửa reference hoặc docs liên quan sau scenario làm bundle cũ hết hiệu lực; sửa suite/engine làm baseline cũ không tương thích. Không dùng score 100 để tuyên bố chất lượng suy luận, tự promote hoặc so v1/v2 như cùng suite. Migration này có baseline 0.5 và kiểm tra hồi quy riêng; cần tạo baseline v2 mới cho evolution tiếp theo.

## Nghiệm thu và giới hạn

204 Python tests và 15 Node bridge tests đạt trong lượt kiểm tra consolidation; báo cáo snapshot: [unified-skill.json](evidence/unified-skill.json). Mười test mới kiểm tra entry discovery, các intent, mode coverage, reference bị thiếu/sửa/bypass/symlink, resource budget, transitive hash và migration hint. Bộ Node/JUnit và demo Git được chạy riêng; không tính lại thành test mới của Python suite.

Một entry gọn hơn tổng 13 tài liệu giúp người dùng gọi thống nhất. Chưa có số token provider hoặc thí nghiệm native để kết luận output không đổi hay chất lượng tăng. Báo cáo thử nghiệm sample do người dùng gửi là dữ liệu tham khảo, không thay bằng chứng kích hoạt. Lỗi đếm subtest thất bại phát hiện ở 0.5 đã sửa sau migration này, kèm regression test riêng.

Rollback dùng reviewed revert commit và kiểm thử lại từ baseline Git; không reset/clean/xóa state. Hook/MCP/native agents chưa kích hoạt; native Claude A/B và token/cost tiếp tục unverified.
