---
name: omega-evidence-reconciler
description: Kiểm tra evidence còn dùng được sau thay đổi source, commit hoặc môi trường.
disable-model-invocation: true
---

# OMEGA evidence-reconciler

## Inputs

Record gate thật trong project hiện tại và gate config đã review; không dùng scenario thay gate proof.

## Workflow

Chạy `python3 -m omega evidence-reconciler --record RECORD --compact` hoặc lặp --evidence. So source/mode/index, HEAD, known execution fingerprint và test outcomes; đọc lý do stale trước quyết định chạy lại.

## Evidence

Trả current/stale-source/stale-context/same-source-different-head và yêu cầu validation. Nêu rõ global policy, dịch vụ và dependencies chưa được quan sát.

## Failure handling

Artifact thiếu/schema sai/project khác hoặc metadata không khớp: không dùng làm readiness proof. Không sửa record cũ hoặc copy hash để ép hợp lệ.

## Stop conditions

Dừng khi từng record được phân loại với lý do. Không tự chạy lại toàn suite vô hạn; chỉ kiểm tra lại phần có thay đổi/lo ngại hợp lý và giữ gate bắt buộc.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
