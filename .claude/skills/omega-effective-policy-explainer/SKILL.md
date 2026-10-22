---
name: omega-effective-policy-explainer
description: Giải thích quyết định OMEGA cho một tool request khi có nhiều nguồn policy.
disable-model-invocation: true
---

# OMEGA effective-policy-explainer

## Inputs

Một PreToolUse event JSON, project root và phạm vi policy cần giải thích; không có credential values.

## Workflow

Chạy `python3 -m omega effective-policy-explainer --input INPUT --compact`. Đối chiếu cùng grammar mà hook dùng; kiểm tra cwd, runner, args, paths, shell expansion và background. Phân biệt allowed của OMEGA với quyền của platform.

## Evidence

Trả allowed/reason/rule_source, scope và platform_decision. Không lặp nguyên command chứa dữ liệu nhạy cảm vào báo cáo.

## Failure handling

Thiếu event/schema hoặc outside scope thì báo denied/unknown; không sửa allowlist để vượt lỗi. Nếu platform từ chối, kiểm tra nguồn policy thực tế trước yêu cầu thêm quyền.

## Stop conditions

Dừng khi có lời giải thích có nguồn và phần chưa biết. Không cấp quyền, thay hook, bật MCP hoặc suy diễn hooks_disabled từ config OMEGA.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
