---
name: quality-gates
description: Chạy build, tests, security, regression với bằng chứng exit code.
disable-model-invocation: true
---

# OMEGA quality-gates

## Inputs

Change objective, acceptance, diff/risk map, gate config đã review và source state hiện tại. Phân biệt required checks với optional trước khi chạy; không hạ required thành optional sau khi fail.

## Workflow

1. Review argv trong omega/config.json: build/tests/security/regression đều bắt buộc. Không dùng shell expansion, credential trong command hoặc mode bỏ bảo vệ.
2. Chạy `python3 -m omega gates --summary --compact`. Đọc từng exit code, timeout/output-limit/truncation và workspace_unchanged. Mở success log qua evidence reference khi cần, không chạy lại chỉ để xem output.
3. Kiểm tra runner đã chạy test thật: pass/fail/error/skipped/expected failure/unexpected success tách riêng. Empty/all-skipped không sẵn sàng. Test phải phủ trigger, negative path và regression có liên quan, không chỉ đếm số lượng.
4. Với subprocess/filesystem/untrusted input/auth/API/schema, bổ sung review và negative tests tương ứng. Security audit mặc định chỉ scan policy hẹp; không gọi đó là security assurance toàn hệ thống.
5. Chạy `python3 -m omega rollback-check --compact`; đối chiếu base commit và chiến lược revert. Production/migration rollback cần bài kiểm riêng, không tự reset/clean/revert.
6. Xem phần quality-gates trong `docs/SKILL_PLAYBOOKS.md` khi điều tra fail; giữ nguyên tiêu chí acceptance và đầu ra người dùng.

## Evidence

Trả từng gate: argv, outcome, duration, test counts, source fingerprint và artifact path. Liệt kê failed/skipped/unrun cùng lý do; nêu rõ scope của security scan, phần output đã cắt và rollback nào chưa được thực thi.

## Failure handling

Exit 124: timeout; 125: output flood; 127: không khởi chạy. Đọc prefix được giữ, thu hẹp target và kiểm chứng diagnosis. File nguồn đổi trong lúc chạy làm evidence không đáng dùng. Nếu sửa lỗi, dùng repair ledger; tối đa 2 lượt trong deadline, không vô hiệu assertion hoặc bypass verification.

## Stop conditions

Chỉ báo đạt trong phạm vi checks đã chạy và source còn khớp evidence. Bất kỳ required gate fail/unexplained/unrun thì không tuyên bố ready. Khi hết budget hoặc cần credential/quyền bên ngoài, báo blocker chính xác và phần đã xác minh.

Chạy CLI từ gốc checkout hiện tại, không cần pip install. Quy tắc tổng quát: CLAUDE.md.
