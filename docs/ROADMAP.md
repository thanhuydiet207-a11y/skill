# Roadmap

Các mục dưới đây **chưa tồn tại** trong engine, skill hay agent. Chúng từng nằm trong `omega/catalog.json` và `docs/ARCHITECTURE.md` dưới trạng thái planned; từ 0.7.3 được tách ra đây để tài liệu chính chỉ mô tả những gì chạy được.

Chỉ nên làm một mục khi eval cho thấy nó cải thiện kết quả so với không dùng OMEGA. Kết quả giai đoạn 1 ([evals/README.md](../evals/README.md)) chưa có case nào OMEGA làm tốt hơn.

## Ưu tiên từ kết quả eval

1. ~~Cho engine chạy trên checkout chỉ đọc.~~ Đã làm ở 0.7.4: `gates` vẫn báo kết quả với `evidence: null`, `build` ghi bytecode ra thư mục tạm, `doctor` dùng config tạm. Evidence vẫn chỉ lưu trong `.omega/` của project.
2. Đo thay đổi code có kiểm soát bằng một case có workspace ghi được; đây là phần OMEGA nhắm tới nhưng chưa đo được.

## 31 capability chưa triển khai

| Nhóm | Capability |
|---|---|
| Intelligence | task-triage, dependency-map, impact-analysis, root-cause, architecture-review |
| Engineering | bug-fix, refactor, api-change, migration, integration |
| Quality | test-design, regression-analysis, security-review, performance-check, rollback-check |
| Knowledge | evidence-index, decision-record, context-pack, knowledge-refresh, handoff |
| Operations | environment-doctor, workspace-isolation, release-plan, incident-response, dependency-health, observability |
| Evolution | skill-evaluation, skill-candidate, skill-promotion, cost-review, workflow-retrospective |

## 7 vai trò agent chưa có file

Quyền trong bảng là mục tiêu policy, chưa có agent runtime.

| Agent | Quyền dự kiến | Nhiệm vụ và đầu ra |
|---|---|---|
| omega-architect | chỉ đọc | phương án, ADR, tradeoff |
| omega-security | chỉ đọc + scanner được duyệt | finding kèm tác động và bằng chứng |
| omega-test-designer | chỉ ghi tests được giao | regression fixture, negative cases |
| omega-knowledge | đọc evidence, ghi memory đã lọc | ADR, kiến thức theo commit, không bí mật |
| omega-operations | đọc config; lệnh môi trường được duyệt | dependency/service readiness; không deploy |
| omega-performance | đọc + benchmark trong sandbox | đo baseline/candidate cùng điều kiện |
| omega-evolution | đọc stable; ghi candidate riêng | benchmark, đề xuất, không tự promote |
