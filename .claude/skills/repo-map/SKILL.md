---
name: repo-map
description: Phân tích repository với bằng chứng trước khi lập kế hoạch.
disable-model-invocation: true
---

# OMEGA repo-map

## Inputs

Task, acceptance, repository hiện tại và phạm vi đã được giao. Nếu chưa rõ mục tiêu, lập inventory trước; không suy đoán quyền sửa hoặc chạy dịch vụ.

## Workflow

1. Chạy `python3 -m omega doctor --compact` và `python3 -m omega map --compact`. Đọc Git status, toolchain, manifests, lockfiles, CI, tests và mục omitted. Không dump environment hoặc credential.
2. Tìm entry point, callers, cấu hình và regression liên quan bằng truy vấn hẹp. Nạp nguồn bằng `python3 -m omega context --select PATH:START:END --compact`; mở rộng khi còn dependency chưa biết.
3. Tách observed facts, hypotheses và unknowns. Mỗi hypothesis có cách bác bỏ bằng test hoặc functional request; không coi tên file hay port mở là bằng chứng hành vi.
4. Chọn `python3 -m omega plan --complexity medium --compact`; thêm `--conflict` khi writer có thể xung đột. Low không spawn agent, tối đa 2 agent độc lập đồng thời.
5. Đọc đúng phần repo-map trong `docs/SKILL_PLAYBOOKS.md` khi cần; trả kế hoạch thay đổi tối thiểu và checks bắt buộc/optional.

## Evidence

Trả branch/HEAD, current changes, source path:line/hash, dependency/test map liên quan, commands đã chạy, điều chưa biết và acceptance đề xuất. Không gửi toàn repository hoặc toàn log vào handoff.

## Failure handling

Nếu Git output bị cắt hoặc encoding sai: dừng dùng inventory đó và báo cần thu hẹp/tăng giới hạn có review. Nếu thiếu runtime/credentials: hoàn thành phần đọc độc lập, báo operation cụ thể bị chặn. Không tự cài gói hay sửa source để “khảo sát”.

## Stop conditions

Dừng khi đủ dữ kiện giao tác vụ có scope/acceptance/checks, hoặc một prerequisite thật sự ngăn phần việc còn lại. Chưa tái hiện thì không kết luận nguyên nhân; inventory chưa đầy đủ thì không tuyên bố đã đọc hết.

Chạy CLI từ gốc checkout hiện tại, không cần pip install. Quy tắc tổng quát: CLAUDE.md.
