---
name: controlled-change
description: Thực hiện thay đổi có kiểm soát trong branch hoặc worktree riêng.
disable-model-invocation: true
---

# OMEGA controlled-change

## Inputs

Objective, acceptance kiểm chứng được, exact paths, quyền người dùng, root đích và rollback strategy. Xác định một owner cho Git để tránh hai framework cùng đổi branch hoặc tạo worktree.

## Workflow

1. Chạy doctor/map/plan; dùng `python3 -m omega isolate --name TEN` khi cần branch sạch. Worktree chỉ cho xung đột đã được ủy quyền; không tạo lồng isolation có sẵn hoặc sửa trực tiếp main/master.
2. Chạy `python3 -m omega change-plan --allow PATH --acceptance "input → expected" --compact`. Nếu có thay đổi người dùng đã được review, thêm --include-existing để chụp baseline; không stash/reset/clean. Merge conflict phải giải quyết trước.
3. Tái hiện trigger bằng regression có thể fail, sửa tối thiểu trong scope. Trước lượt sửa sau lỗi chạy `python3 -m omega change-attempt --record RECORD --reason "chẩn đoán mới" --compact`; không né ledger/deadline bằng task giả mới.
4. Hoàn thành format/codegen và stage các thay đổi dự kiến trước final validation. Chạy `python3 -m omega gates --summary --compact`, rồi `python3 -m omega change-check --record RECORD --evidence EVIDENCE --compact` với config adapter đã review nếu là project khác.
5. Cần scope_passed và ready_for_review; passed về scope riêng không chứng minh acceptance. Gate proof phải khớp source/mode/index, HEAD và known execution context; dùng evidence-reconciler khi chưa rõ vì sao stale.
6. Review diff/acceptance/rollback và handoff độc lập theo rủi ro. Đọc docs/INTEROPERABILITY_GUIDE.md cho runner tuyệt đối, target root và ownership contract.

## Evidence

Trả baseline, scope, existing changes được giữ, trigger trước/sau, gate record và acceptance đã/chưa xác minh. Chỉ ra global policy/dependencies/dịch vụ chưa được fingerprint đầy đủ.

## Failure handling

Ngoài scope, branch/HEAD đổi, source/index/runtime drift: dừng sửa và review nguyên nhân trước replan/rerun. Không tự nới paths, hạ required gate, đổi assertion hoặc ghi lại hash để làm evidence hợp lệ.

## Stop conditions

Dừng khi acceptance và required gates đạt trong phạm vi đã kiểm chứng, hoặc hết checkpoint 30 phút/2 lượt sửa/thiếu quyền thật. Không push/deploy/xóa dữ liệu hoặc sửa ngoài repository nếu chưa có user authorization tương ứng.
