# Kết quả thực thi

Bản 0.7: **212 Python tests riêng biệt pass**, **15 TypeScript bridge tests pass**, một plugin omega có một skill/13 chế độ và 3 agent. Strict manifests, local marketplace install và ZIP inventory đã kiểm chứng với Claude Code 2.1.308; engine trong install cache chạy fixture đỏ → xanh. Báo cáo: [plugin-packaging.json](evidence/plugin-packaging.json); cách cài: [CLAUDE_PLUGIN.md](CLAUDE_PLUGIN.md).

## Phạm vi kiểm chứng hiện tại

- Baseline 0.6 có 204 tests; plugin packaging có 212 Python tests riêng biệt và 15 Node test cho bridge TypeScript, không cộng các lần chạy lặp thành test mới.
- Một benchmark --skill omega chạy toàn bộ Python suite, gồm 20 workflow tests, 8 interoperability CLI scenarios 10 consolidation regressions và 8 plugin packaging regressions. Các chế độ dùng chung engine; không có 13 phép đánh giá chất lượng LLM độc lập.
- Build compile Python và strict TypeScript noEmit; security là targeted Python AST/JSON/bypass/possible-secret rules trên scope .claude, agents, .claude-plugin và omega; regression gồm 3 router cases và một offline contract ràng buộc 13 mode references. Không thay SAST, dependency audit hoặc native LLM evaluation.
- Demo tạo Git fixture có bug cộng thành trừ, thấy tests đỏ trước sửa và xanh sau sửa; xác nhận branch/worktree, memory và Git baseline còn truy cập được. Không deploy hoặc rollback production.
- Benchmark efficiency kiểm tra JSON pretty/compact tương đương dữ liệu và khôi phục gate summary từ evidence. Đo UTF-8 bytes, không đo token provider hay output LLM giống hệt.
- External Python target có integration test thực thi riêng. Node built-in JUnit đã chạy thật với 1 pass/1 skip trong fixture sau sửa; Jest/Go vẫn là parser fixtures. Lệnh go version không xác nhận được Go toolchain. Không cộng test lặp hoặc skipped thành thành tích.
- Candidate/compare kiểm tra bundle/source/index/runtime freshness và yêu cầu gate + scenario evidence cho eligible_for_review. Native release luôn chưa được tự duyệt.

Source manifest trong báo cáo ràng buộc các file code/tests/benchmarks/skills/docs đã kiểm tra, loại trừ chính report để tránh self-reference. Record gates đầy đủ chứa HEAD và workspace fingerprint tại thời điểm chạy. Commit report hoặc đổi HEAD làm proof đó thành lịch sử; không tự coi proof local cũ là current sau publication. Báo cáo không có chữ ký chứng thực.

## Các giới hạn thực tế

Claude Code 2.1.308 có version/help chạy được; phiên xác thực/native task chưa được nghiệm thu. Không tự đăng ký hook hoặc MCP. Doctor trả trạng thái hiệu lực external là unknown. Không kết luận skill tương thích native từ static audit, contract score hoặc fixture kết quả A/B.

GitHub Actions workflow được cấu hình để chạy cùng checks. API Actions từ môi trường từng trả Forbidden; chỉ trạng thái CI quan sát được mới được báo là pass. Bằng chứng local và trạng thái CI là hai thông tin riêng.

Runtime fingerprint chỉ bao phủ config, source/index, metadata tool và project policy đã liệt kê; không bao phủ toàn bộ ignored dependencies, services, managed/global policy hoặc model API. Memory/benchmark local có thể bị sửa bởi người có quyền filesystem: reviewer phải đối chiếu provenance.

## Chạy lại

```bash
python3 -m omega doctor --compact
python3 -m omega gates --summary --compact
python3 benchmarks/demo.py
python3 benchmarks/token_efficiency.py
python3 benchmarks/native_runners.py
python3 benchmarks/native_runners.py --report-file
node --test integration/typescript/omega-bridge.test.mjs
python3 -m omega rollback-check --compact
```

Hoàn thành stage dự kiến trước final gates. Không chạy lặp vô hạn để tăng số liệu; chạy lại khi code, evidence hoặc điều kiện liên quan đổi. Thay benchmark suite cần baseline mới, không sửa kỳ vọng chỉ để làm xanh.

## Báo cáo lịch sử

[local-validation.json](evidence/local-validation.json) là bootstrap (21 tests); [token-efficiency.json](evidence/token-efficiency.json) là tối ưu context ban đầu; [deep-hardening.json](evidence/deep-hardening.json) là 0.2 (82 tests). Hash và trạng thái phát hành trong chúng thuộc các snapshot tương ứng, không phải trạng thái hiện tại.

[interop-upgrade.json](evidence/interop-upgrade.json) và [UPGRADE_0_3.md](UPGRADE_0_3.md) là snapshot 0.3 (144 Python tests), không phải nguồn hiện tại. TypeScript runtime chạy qua Node type stripping; 0.5 đã chạy strict tsc/noEmit và đưa vào build gate. MCP server/UI chưa triển khai.

[verification-hardening.json](evidence/verification-hardening.json) là snapshot 0.4 (176 Python, 9 Node tests), không phải nguồn hiện tại. Report-file Node/JUnit đã chạy thật với stdout người đọc riêng; Jest JSON dùng synthetic fixtures. Npm compiler dev dependencies và integrity nằm trong package-lock, không có install scripts/global install.

[report-integrity.json](evidence/report-integrity.json) và [UPGRADE_0_5.md](UPGRADE_0_5.md) là snapshot 0.5 (194 Python, 15 Node tests, 13 skill riêng). Từ 0.6 chỉ có một entry omega. Lỗi đếm subtest thất bại đang được theo dõi riêng; số tests pass trong suite không chứng minh đường báo cáo đó đã sửa.

[unified-skill.json](evidence/unified-skill.json) là snapshot 0.6 với 204 Python/15 Node tests. Từ 0.7 có native plugin install/inventory và cache-to-target fixture; đây không phải activation trace hoặc chất lượng LLM. ZIP/manifest strict validation không thay security review hoặc official directory listing approval.
