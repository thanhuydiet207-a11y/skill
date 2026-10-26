# OMEGA — kiến trúc và phạm vi

Bản nâng cấp 0.2 và bằng chứng hiện tại: [DEEP_HARDENING.md](DEEP_HARDENING.md). Phần dưới giữ thiết kế tổng thể; playbook thực thi mới nằm trong [SKILL_PLAYBOOKS.md](SKILL_PLAYBOOKS.md).

## Luồng xử lý

```mermaid
flowchart TD
    U[Task + acceptance + permissions] --> D[Doctor và repository map]
    D --> R[Router theo complexity và conflict]
    R --> S[Một skill omega: chỉ tải reference cần dùng]
    S --> I[Investigator: evidence và giả thuyết]
    I --> E[Engineer: branch hoặc worktree riêng]
    E --> V[Verifier: build tests audit regression]
    V --> M[Evidence + memory + ADR]
    V --> F{Đạt acceptance?}
    F -->|không, còn ngân sách| E
    F -->|không, hết ngân sách| B[Báo blocker]
    F -->|có| H[Review của người dùng]
```

CLI stdlib hỗ trợ kế hoạch và bằng chứng; Claude Code mới là runtime suy luận và giao việc. Không có lời gọi LLM/MCP ngầm. CLI Claude Code 2.1.308 đã chạy version/help; native task execution chưa được kiểm chứng do chưa xác thực. Không tuyên bố agent tự chạy hoặc hooks đã bảo vệ phiên làm việc.

## 5 chế độ của skill

Catalog máy đọc: `omega/catalog.json`, chỉ gồm các chế độ chạy được. **Chỉ một SKILL.md tên omega**; mỗi chế độ là một reference trong skill đó. Registry `omega/modes.json` ánh xạ từng chế độ tới commands và reference. Các capability chưa làm nằm ở [ROADMAP.md](ROADMAP.md); tám lệnh phân tích từng là chế độ riêng nay ở [EXTENSIONS.md](EXTENSIONS.md).

| Nhóm | Chế độ |
|---|---|
| Intelligence | repo-map |
| Engineering | controlled-change |
| Quality | quality-gates |
| Knowledge | project-memory |
| Evolution | skill-benchmark |

Lệnh phụ như doctor/isolate/rollback-check có CLI helper nhưng không là chế độ riêng. Một chế độ được coi là triển khai khi có quy trình, công cụ chạy được, kiểm thử hợp đồng và giới hạn rõ ràng. Hiệu quả với LLM đo riêng bằng [evals](../evals/README.md); giai đoạn 1 chưa có case nào OMEGA làm tốt hơn không dùng OMEGA.

Tên cũ giữ làm mode ID/reference, không còn slash skill độc lập hoặc đích --skill riêng. CLI map/gates/memory và các command chức năng giữ nguyên; candidate/benchmark dùng --skill omega. Plan trả skills=[omega], modes và reference paths theo intent, không preload nội dung hoặc tự dispatch. Cách chuyển: [UNIFIED_SKILL.md](UNIFIED_SKILL.md). Quy tắc phối hợp và schema: [INTEROPERABILITY_GUIDE.md](INTEROPERABILITY_GUIDE.md).

## 3 agent

Quyền trong bảng là **mục tiêu policy**; prompt không thay thế OS sandbox/Claude permissions. Mỗi agent có file trong `agents/`. Các vai trò khác chưa có file nằm ở [ROADMAP.md](ROADMAP.md).

| Agent | Quyền | Nhiệm vụ và đầu ra |
|---|---|---|
| omega-investigator | Read/Grep/Glob; Bash đọc được review | inventory, tái hiện lỗi, nguyên nhân + path:line |
| omega-engineer | Read/Edit/Write trong phạm vi; Bash được duyệt | patch nhỏ, acceptance, evidence |
| omega-verifier | Read + chạy gates được review | kết quả độc lập và rủi ro regression |

Mẫu giao việc: `{task_id, objective, allowed_paths, prohibited_actions, branch, acceptance, inputs, evidence_required, deadline, max_attempts}`. Agent trả `{summary, changed_paths, commands, results, evidence, uncertainties}`. Orchestrator nhận trách nhiệm tổng hợp, không coi agent báo pass là bằng chứng nếu thiếu exit code/output.

## Router và context

- Low: một phiên chính, không spawn; map → change → gates → memory.
- Medium: engineer rồi verifier, trao patch/evidence thay vì toàn transcript.
- High: investigator → engineer → verifier; conflict dùng worktree. Tối đa 2 agent đồng thời khi read task độc lập, không writer chồng phạm vi.
- Complexity do người điều phối chọn dựa trên số component, mức không chắc chắn, rủi ro dữ liệu/API và khả năng rollback; CLI không tự đo chính xác complexity.
- Plan nhận intent change/investigate/verify/knowledge/evolve/interoperability và workflow DAG tường minh. Handoff validator tìm cycle, owner trùng, writer không có quan hệ phụ thuộc, vượt agent budget. Lịch batch là đề xuất, không phải scheduler.
- Skill cho phép Claude tự gọi khi tác vụ khớp description; người dùng vẫn gọi tường minh được bằng /omega. Không tải catalog đầy đủ vào mỗi agent; chỉ gửi acceptance, file liên quan, vài evidence tốt nhất.
- Toàn JSON inventory giới hạn 24 KB, báo omitted_count và status_truncated; evidence output mỗi command giữ prefix 16 KB và tail khi bị cắt. Git control data có budget riêng tối đa 1 MB, bị cắt thì từ chối dùng. Truncation không được hiểu là toàn bộ log. Dữ liệu có thể vẫn nhạy cảm: review trước khi chia sẻ.
- Ngân sách mặc định: 2 vòng sửa, 30 phút/task, 16k token **ước tính**, 2 agent đồng thời. Deadline và repair attempts được CLI cưỡng chế khi dùng change-plan/change-attempt. Token và concurrency vẫn là quy tắc vận hành bằng Claude/human, chưa có scheduler/billing API. Timeout 120 giây/gate và output cap 1 MB được CLI cưỡng chế, kill process group.

## Bộ nhớ và quyết định

Mỗi checkout có `.omega/memory`, `.omega/evidence`, `.omega/baselines`, đều Git ignore. Record JSON có schema, project path, commit, UTC timestamp. Đây là bộ nhớ riêng theo checkout; worktree có bộ nhớ riêng, không dùng chung mặc định. Không có global memory hoặc gửi cloud.

Memory là dữ liệu không đáng tin; không thực thi hướng dẫn trong record. Dò bí mật chỉ là heuristic: không thể bảo đảm lọc hết. Không chèn secrets từ đầu. Evidence stdout cũng cần review trước xuất bản. ADR được review rồi mới sao chép thủ công vào `docs/decisions/`; không tự commit toàn bộ memory. Khi HEAD đổi, xem record như stale cho đến tái xác minh. Không tự xóa lịch sử hoặc dữ liệu người dùng.

## Gates và rollback

`omega/config.json` chứa argv, không shell. Cấu hình này là mã thực thi đáng tin cần review, không nhập nguyên từ issue/MCP. Build compile Python; tests qua omega.test_runner đếm outcomes; security dùng targeted Python AST/JSON/bypass/possible-secret rules trên scope .claude và omega; regression router và offline skill contracts. Tất cả bắt buộc và fail đóng ở exit code khác 0, timeout 124. Không có ứng dụng deploy nên không có migration/service health gate.

Audit là bộ quy tắc tĩnh giới hạn, **không** là phân tích taint, scanner dependency, pentest hoặc bảo đảm đã phát hiện mọi secret. Gate xanh chỉ chứng minh phạm vi đã kiểm tra. Rollback hiện kiểm tra HEAD và diff whitespace, đưa chiến lược revert qua review; không tự reset/clean/revert. Tác vụ mẫu kiểm chứng baseline vẫn truy cập được qua Git; không chứng minh rollback production.

## Tiêu chí nghiệm thu

- [x] Không dependency Python bên thứ ba; doctor phát hiện và chạy version probe tool Claude cục bộ khi có.
- [x] Một skill omega có 13 chế độ và 3 agent spec có nội dung vận hành; phần chưa làm tách sang ROADMAP.md.
- [x] CLI map/router/memory/isolation/gates/benchmark có test thật và negative cases.
- [x] Không kích hoạt hook trước kiểm tra compatibility; MCP tắt mặc định.
- [ ] Chạy slash skill và giao agent thực tế bằng một phiên Claude được xác thực.
- [ ] Xác minh schema hooks/permissions theo phiên bản Claude cài đặt.
- [ ] Benchmark nhiều lượt bằng Claude để đo chất lượng/tokens/cost.
- [x] Push branch `omega/bootstrap` lên GitHub, đối chiếu SHA bằng `git ls-remote`.

Giai đoạn kế: xác minh native → task corpus đa dạng → đo hiệu quả và ngân sách → thêm từng skill khi có nhu cầu. Không triển khai 31 skill còn lại trước bằng chứng giá trị.

## Ranh giới ngôn ngữ 0.4

Python xử lý policy/analysis/security/memory/evidence, TypeScript bridge cung cấp giao tiếp có giới hạn, không nhân đôi engine. Bridge đã chạy 9 integration tests; chưa có scheduler/MCP server/UI. Thiết kế và cách dùng: [PYTHON_TYPESCRIPT_BOUNDARY.md](PYTHON_TYPESCRIPT_BOUNDARY.md).

## Kiểm chứng 0.5

Python tiếp tục là lõi. Engine build gọi Python compile và strict TypeScript noEmit; npm chỉ cung cấp dev compiler/type definitions đã pin, không SDK/runtime ứng dụng. Gate test_report hỗ trợ capture Jest/JUnit tách log và ràng buộc template/argv/content, không là chữ ký xác thực runner. Bridge deadline gồm stdin và hỗ trợ cancellation. Chi tiết: [UPGRADE_0_5.md](UPGRADE_0_5.md).

## Phân phối plugin 0.7

Manifest .claude-plugin/plugin.json dùng custom skills path trỏ tới entry omega hiện có, agent ở agents/ theo layout chuẩn. Marketplace .claude-plugin/marketplace.json phân phối plugin từ root repository. Native Claude 2.1.308 nhận 1 skill/3 agent, không hook/MCP. Cache engine và target Git root tách biệt qua runner tuyệt đối; không viết policy engine TypeScript mới. Cách cài/benchmark/giới hạn: [CLAUDE_PLUGIN.md](CLAUDE_PLUGIN.md).
