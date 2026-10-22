---
name: controlled-change
description: Thực hiện thay đổi có kiểm soát trong branch hoặc worktree riêng.
disable-model-invocation: true
---

# OMEGA controlled-change

## Inputs

Objective, acceptance kiểm chứng được, danh sách file chính xác, quyền được cấp và rollback strategy. Bảo toàn thay đổi sẵn có; không stash/reset/clean tự động.

## Workflow

1. Chạy doctor/map/plan. Từ checkout sạch, dùng `python3 -m omega isolate --name TEN`; chỉ dùng `--worktree .omega/worktrees/TEN` cho việc xung đột đã được ủy quyền. Không sửa trực tiếp main/master.
2. Trước sửa, chạy `python3 -m omega change-plan --allow PATH --acceptance "input → expected" --compact`. Lặp --allow/--acceptance theo nhu cầu; lưu record được trả. Mỗi task có deadline và tối đa 2 lượt sửa sau lỗi.
3. Tái hiện trigger, viết hoặc dùng regression có thể fail đúng nguyên nhân. Thay đổi nhỏ trong scope; không trộn refactor không liên quan hoặc tự thêm dependency.
4. Khi có lỗi, ghi hypothesis và phép kiểm chứng; trước lượt sửa tiếp chạy `python3 -m omega change-attempt --record RECORD --reason "chẩn đoán mới" --compact`. Không lặp lại lệnh không có thông tin mới.
5. Chạy `python3 -m omega gates --summary --compact`; dùng `python3 -m omega change-check --record RECORD --evidence EVIDENCE --compact`. Review diff và acceptance thủ công; scope pass chưa chứng minh chức năng.
6. Chạy rollback-check, ghi evidence/memory và bàn giao cho verifier độc lập khi rủi ro đủ lớn. Xem phần controlled-change trong `docs/SKILL_PLAYBOOKS.md` khi cần chi tiết.

## Evidence

Trả base HEAD, branch, change-plan, changed paths, trigger trước/sau, gate record, acceptance đã/chưa xác minh, rollback strategy và rủi ro. Phân biệt code đã sửa với hành vi đã chạy thành công.

## Failure handling

Ngoài scope/branch/HEAD thay đổi: dừng sửa, review kế hoạch mới; không tự mở rộng scope. Evidence stale: kiểm tra source thay đổi gì rồi chạy lại checks liên quan. Nếu lỗi setup, sửa setup được phép; lỗi application cần regression. Không che fail bằng đổi assertion.

## Stop conditions

Dừng khi acceptance và mọi required gate đạt trên source hiện tại, hoặc hết deadline/2 lượt sửa/thiếu quyền thật sự. Không tạo task mới để né budget. Không push, deploy, xóa dữ liệu hay sửa ngoài repository nếu chưa có user authorization cho hành động đó.

Chạy CLI từ gốc checkout hiện tại, không cần pip install. Quy tắc tổng quát: CLAUDE.md.
