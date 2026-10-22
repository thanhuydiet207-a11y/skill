---
name: skill-benchmark
description: Đánh giá hồi quy skill bằng fixture trước khi đề xuất nâng phiên bản.
disable-model-invocation: true
---

# OMEGA skill-benchmark

## Inputs

Tên trong 5 skill đã triển khai, mục tiêu thay đổi, baseline/candidate riêng, fixture version và acceptance không đổi. Các skill planned chưa được coi là khả dụng.

## Workflow

1. Chạy `python3 -m omega candidate --skill TEN --compact` trước sửa. Giữ nguyên stable; chỉ sửa bản sao .omega/candidates được trả. Baseline cũ không dùng được sau khi engine/fixture/config thay đổi.
2. Candidate phải có Inputs/Workflow/Evidence/Failure handling/Stop conditions, command thực thi được và permission tối thiểu. Đọc phần skill-benchmark trong `docs/SKILL_PLAYBOOKS.md`; không preload toàn catalog.
3. Chạy `python3 -m omega benchmark --skill TEN --candidate PATH --compact`. Đọc từng contract check và scenario outcome; lưu evidence đúng candidate hash. Score là độ đầy đủ tài liệu, không phải điểm reasoning của model.
4. Chạy `python3 -m omega gates --summary --compact`; sau đó `python3 -m omega compare --baseline BASELINE --evidence SCENARIO --evidence GATES --compact`. Cần eligible_for_review=true, không chỉ passed=true.
5. Review diff và user authorization trước áp dụng. CLI không tự promote/merge. Sau áp dụng, chạy lại gates, demo và benchmark context có liên quan; lưu hash trước/sau và giới hạn native evaluation.
6. Khi có Claude tương thích và được xác thực, thêm nhiều lượt baseline/candidate trên cùng task corpus/model/version; đo acceptance, false claims, regression, input/output/cache tokens, latency/cost. Không hạ model/effort hoặc sửa kỳ vọng chỉ để làm số đẹp.

## Evidence

Trả baseline/candidate hashes, suite hash, source state, HEAD, contract checks, scenario record, gate record và quyết định review. Native quality luôn UNVERIFIED nếu chưa chạy model; byte saving không được gọi là token saving đã đo.

## Failure handling

Stable đổi trước review: dừng promotion và kiểm tra diff, không reset người dùng. Candidate đổi sau test hoặc evidence stale: chạy lại phần bị ảnh hưởng. Suite hash đổi: tạo baseline mới và review lý do, không vá report. Thiếu evidence không được tự điền pass.

## Stop conditions

Không thay stable trước khi benchmark/gates đạt và có quyền review/apply từ người dùng. Hết budget thì báo blocker, không loop self-improvement vô hạn. Local contract pass không chứng minh model tuân thủ skill hoặc ứng dụng không có lỗi; ghi rõ phạm vi đã kiểm chứng.

Chạy CLI từ gốc checkout hiện tại, không cần pip install. Quy tắc tổng quát: CLAUDE.md.
