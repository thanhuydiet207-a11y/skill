# OMEGA — kiến trúc và phạm vi v0.1

## Luồng xử lý

```mermaid
flowchart TD
    U[Task + acceptance + permissions] --> D[Doctor và repository map]
    D --> R[Router theo complexity và conflict]
    R --> S[Chỉ tải skill cần dùng]
    S --> I[Investigator: evidence và giả thuyết]
    I --> E[Engineer: branch hoặc worktree riêng]
    E --> V[Verifier: build tests audit regression]
    V --> M[Evidence + memory + ADR]
    V --> F{Đạt acceptance?}
    F -->|không, còn ngân sách| E
    F -->|không, hết ngân sách| B[Báo blocker]
    F -->|có| H[Review của người dùng]
```

CLI stdlib hỗ trợ kế hoạch và bằng chứng; Claude Code mới là runtime suy luận và giao việc. Không có lời gọi LLM/MCP ngầm. Native runtime chưa được kiểm chứng trên máy này. Không tuyên bố agent tự chạy hoặc hooks đã bảo vệ phiên làm việc.

## 36 skill, 6 nhóm

Catalog máy đọc: `omega/catalog.json`. Mỗi nhóm có 6 capability. **Chỉ 5 mục in đậm được triển khai** bằng SKILL.md và lệnh CLI có test. Các tên còn lại là roadmap, không có file giả.

| Nhóm | Skill |
|---|---|
| Intelligence | **repo-map**, task-triage, dependency-map, impact-analysis, root-cause, architecture-review |
| Engineering | **controlled-change**, bug-fix, refactor, api-change, migration, integration |
| Quality | **quality-gates**, test-design, regression-analysis, security-review, performance-check, rollback-check |
| Knowledge | **project-memory**, evidence-index, decision-record, context-pack, knowledge-refresh, handoff |
| Operations | environment-doctor, workspace-isolation, release-plan, incident-response, dependency-health, observability |
| Evolution | **skill-benchmark**, skill-evaluation, skill-candidate, skill-promotion, cost-review, workflow-retrospective |

Capabilities phụ như doctor/isolate/rollback-check có CLI helper nhưng chưa thành skill độc lập. Một skill được coi là triển khai khi có quy trình, công cụ chạy được, kiểm thử hợp đồng và giới hạn rõ ràng; hiệu quả của skill với LLM là nghiệm thu riêng chưa đạt.

## 10 vai trò chuyên môn

Quyền trong bảng là **mục tiêu policy**; prompt không thay thế OS sandbox/Claude permissions. 3 hàng đầu có file trong `.claude/agents/`, 7 hàng sau chưa tạo agent runtime.

| Agent | Trạng thái | Quyền dự kiến | Nhiệm vụ và đầu ra |
|---|---|---|---|
| omega-investigator | spec đã tạo | Read/Grep/Glob; Bash đọc được review | inventory, tái hiện lỗi, nguyên nhân + path:line |
| omega-engineer | spec đã tạo | Read/Edit/Write trong phạm vi; Bash được duyệt | patch nhỏ, acceptance, evidence |
| omega-verifier | spec đã tạo | Read + chạy gates được review | kết quả độc lập và rủi ro regression |
| omega-architect | thiết kế | chỉ đọc | phương án, ADR, tradeoff |
| omega-security | thiết kế | chỉ đọc + scanner được duyệt | finding kèm tác động và bằng chứng |
| omega-test-designer | thiết kế | chỉ ghi tests được giao | regression fixture, negative cases |
| omega-knowledge | thiết kế | đọc evidence, ghi memory đã lọc | ADR, kiến thức theo commit, không bí mật |
| omega-operations | thiết kế | đọc config; lệnh môi trường được duyệt | dependency/service readiness; không deploy |
| omega-performance | thiết kế | đọc + benchmark trong sandbox | đo baseline/candidate cùng điều kiện |
| omega-evolution | thiết kế | đọc stable; ghi candidate riêng | benchmark, đề xuất, không tự promote |

Mẫu giao việc: `{task_id, objective, allowed_paths, prohibited_actions, branch, acceptance, inputs, evidence_required, deadline, max_attempts}`. Agent trả `{summary, changed_paths, commands, results, evidence, uncertainties}`. Orchestrator nhận trách nhiệm tổng hợp, không coi agent báo pass là bằng chứng nếu thiếu exit code/output.

## Router và context

- Low: một phiên chính, không spawn; map → change → gates → memory.
- Medium: engineer rồi verifier, trao patch/evidence thay vì toàn transcript.
- High: investigator → engineer → verifier; conflict dùng worktree. Tối đa 2 agent đồng thời khi read task độc lập, không writer chồng phạm vi.
- Complexity do người điều phối chọn dựa trên số component, mức không chắc chắn, rủi ro dữ liệu/API và khả năng rollback; CLI không tự đo chính xác complexity.
- Skill `disable-model-invocation: true` chủ ý chỉ gọi tường minh. Không tải catalog đầy đủ vào mỗi agent; chỉ gửi acceptance, file liên quan, vài evidence tốt nhất.
- Metadata inventory giới hạn 24 KB; output mỗi command giữ tối đa 16 KB. Truncation không được hiểu là toàn bộ log. Dữ liệu có thể vẫn nhạy cảm: review trước khi chia sẻ.
- Ngân sách mặc định: 2 vòng sửa, 30 phút/task, 16k token **ước tính**, 2 agent đồng thời. Đây là quy tắc vận hành bằng Claude/human, chưa có scheduler/billing API cưỡng chế. Timeout 120 giây cho từng gate được CLI cưỡng chế và kill process group.

## Bộ nhớ và quyết định

Mỗi checkout có `.omega/memory`, `.omega/evidence`, `.omega/baselines`, đều Git ignore. Record JSON có schema, project path, commit, UTC timestamp. Đây là bộ nhớ riêng theo checkout; worktree có bộ nhớ riêng, không dùng chung mặc định. Không có global memory hoặc gửi cloud.

Memory là dữ liệu không đáng tin; không thực thi hướng dẫn trong record. Dò bí mật chỉ là heuristic: không thể bảo đảm lọc hết. Không chèn secrets từ đầu. Evidence stdout cũng cần review trước xuất bản. ADR được review rồi mới sao chép thủ công vào `docs/decisions/`; không tự commit toàn bộ memory. Khi HEAD đổi, xem record như stale cho đến tái xác minh. Không tự xóa lịch sử hoặc dữ liệu người dùng.

## Gates và rollback

`omega/config.json` chứa argv, không shell. Cấu hình này là mã thực thi đáng tin cần review, không nhập nguyên từ issue/MCP. Build compile Python; tests unittest; security audit policy config; regression router fixture. Tất cả bắt buộc và fail đóng ở exit code khác 0, timeout 124. Không có ứng dụng deploy nên không có migration/service health gate.

Audit hiện **không** là SAST, scanner dependency, pentest hoặc secret scanner. Gate xanh chỉ chứng minh phạm vi đã kiểm tra. Rollback hiện kiểm tra HEAD và diff whitespace, đưa chiến lược revert qua review; không tự reset/clean/revert. Tác vụ mẫu kiểm chứng baseline vẫn truy cập được qua Git; không chứng minh rollback production.

## Tiêu chí nghiệm thu

- [x] Không dependency bên thứ ba; doctor phát hiện Claude vắng mặt.
- [x] 36 capability được phân nhóm; 5 skill và 3 agent có nội dung vận hành.
- [x] CLI map/router/memory/isolation/gates/benchmark có test thật và negative cases.
- [x] Không kích hoạt hook trước kiểm tra compatibility; MCP tắt mặc định.
- [ ] Chạy slash skill và giao agent thực tế bằng một phiên Claude được xác thực.
- [ ] Xác minh schema hooks/permissions theo phiên bản Claude cài đặt.
- [ ] Benchmark nhiều lượt bằng Claude để đo chất lượng/tokens/cost.
- [ ] Push GitHub khi có quyền xác thực hoạt động.

Giai đoạn kế: xác minh native → task corpus đa dạng → đo hiệu quả và ngân sách → thêm từng skill khi có nhu cầu. Không triển khai 31 skill còn lại trước bằng chứng giá trị.
