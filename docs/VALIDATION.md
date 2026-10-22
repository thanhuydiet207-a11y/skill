# Kết quả thực thi

Bản 0.4: **176 Python tests riêng biệt pass**, **9 TypeScript bridge tests pass**, build/tests/security/regression đạt, 13 skill có offline contract và scenario CLI. Báo cáo máy đọc: [verification-hardening.json](evidence/verification-hardening.json); đánh giá từng skill và các điểm chưa hoàn thiện: [UPGRADE_0_4.md](UPGRADE_0_4.md).

## Phạm vi kiểm chứng hiện tại

- 144 tests baseline 0.3; sau nâng cấp có 176 Python tests riêng biệt và 9 Node test cho bridge TypeScript, không cộng các lần chạy lặp thành test mới.
- 5 skill nền tảng dùng chung nhóm 20 workflow tests; 8 extension dùng chung nhóm 8 scenario CLI. Chạy theo từng skill kiểm tra kết nối công cụ/contract, không phải 13 phép đánh giá chất lượng độc lập.
- Build compile Python; security là targeted Python AST/JSON/bypass/possible-secret rules trên scope .claude và omega; regression gồm 3 router cases và 13 offline contracts. Không thay SAST, dependency audit hoặc native LLM evaluation.
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
node --test integration/typescript/omega-bridge.test.mjs
python3 -m omega rollback-check --compact
```

Hoàn thành stage dự kiến trước final gates. Không chạy lặp vô hạn để tăng số liệu; chạy lại khi code, evidence hoặc điều kiện liên quan đổi. Thay benchmark suite cần baseline mới, không sửa kỳ vọng chỉ để làm xanh.

## Báo cáo lịch sử

[local-validation.json](evidence/local-validation.json) là bootstrap (21 tests); [token-efficiency.json](evidence/token-efficiency.json) là tối ưu context ban đầu; [deep-hardening.json](evidence/deep-hardening.json) là 0.2 (82 tests). Hash và trạng thái phát hành trong chúng thuộc các snapshot tương ứng, không phải trạng thái hiện tại.

[interop-upgrade.json](evidence/interop-upgrade.json) và [UPGRADE_0_3.md](UPGRADE_0_3.md) là snapshot 0.3 (144 Python tests), không phải nguồn hiện tại. TypeScript chạy qua Node type stripping; chưa chạy tsc type checker. MCP server/UI chưa triển khai.
