---
name: omega-evidence-reconciler
description: Kiểm tra evidence còn dùng được sau thay đổi source, commit hoặc môi trường.
disable-model-invocation: true
---

# OMEGA evidence-reconciler

## Inputs

Record gate thật trong project hiện tại và gate config đã review; không dùng scenario thay gate proof.

## Workflow

Với file report, đọc lại cùng test_report policy để kiểm tra configured argv, argv đã render và SHA-256 content trong evidence. Report nằm ở namespace mới không chứng minh runner trung thực. Content snapshot giữ trong artifact; summary trỏ reference, không bỏ nội dung để tiết kiệm token. Thay report policy/engine/runtime thì xác minh lại; xem docs/UPGRADE_0_5.md.

Đối chiếu fingerprint có hash whitelist runtime environment và các runtime_inputs được khai tường minh; đọc lại cùng --gate-config của lúc thực thi. Process timeout/output-limit/invalid UTF-8 phủ quyết readiness dù exit code trong record là 0. Chưa ràng buộc được dependency/service/policy ngoài fingerprint phải ghi unverified, không tự coi là tương đương; xem docs/UPGRADE_0_4.md.

Chạy `python3 -m omega evidence-reconciler --record RECORD --compact` hoặc lặp --evidence. So source/mode/index, HEAD, known execution fingerprint và test outcomes; đọc lý do stale trước quyết định chạy lại.

## Evidence

Trả current/stale-source/stale-context/same-source-different-head và yêu cầu validation. Nêu rõ global policy, dịch vụ và dependencies chưa được quan sát.

## Failure handling

Artifact thiếu/schema sai/project khác hoặc metadata không khớp: không dùng làm readiness proof. Không sửa record cũ hoặc copy hash để ép hợp lệ.

## Stop conditions

Dừng khi từng record được phân loại với lý do. Không tự chạy lại toàn suite vô hạn; chỉ kiểm tra lại phần có thay đổi/lo ngại hợp lý và giữ gate bắt buộc.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
