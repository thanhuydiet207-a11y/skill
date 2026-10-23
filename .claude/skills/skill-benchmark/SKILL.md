---
name: skill-benchmark
description: Đánh giá hồi quy skill bằng fixture trước khi đề xuất nâng phiên bản.
disable-model-invocation: true
---

# OMEGA skill-benchmark

## Inputs

Skill trong registry hiện tại, mục tiêu thay đổi, baseline/candidate riêng, acceptance cố định và dependencies/resources liên quan. Skill planned chưa được coi là có thể chạy.

## Workflow

Full engine build phải qua strict TypeScript compiler/noEmit bên cạnh Python tests; bridge Node tests là nghiệm thu riêng, không dùng type stripping thay type-check. Suite hash gồm source/tsconfig/package-lock, prune node_modules và __pycache__, từ chối source symlink. Giữ native quality và token provider là unknown cho đến evaluation thật; xem docs/UPGRADE_0_5.md.

1. Chạy `python3 -m omega candidate --skill TEN --compact` trước sửa. Chỉ sửa candidate, giữ stable và tài nguyên baseline; bundle hash ràng buộc SKILL.md cùng references nhận diện được.
2. Viết section có nội dung thực và commands có thể chạy. Metadata/license trong safe YAML subset được chấp nhận; syntax chưa hỗ trợ cần review. Contract completeness không phải quality score, không chứng minh instruction adherence.
3. Chạy `python3 -m omega benchmark --skill TEN --candidate PATH --compact`. Đọc contract, suite/bundle hashes và đúng workflow pattern cho foundation hoặc extensions; tooling scenarios không đánh giá model đọc prompt.
4. Chạy `python3 -m omega gates --summary --compact`; sau đó `python3 -m omega compare --baseline BASELINE --evidence SCENARIO --evidence GATES --compact`. Cần eligible_for_review=true với source/index/runtime hiện tại, nhưng native_release_eligible vẫn false.
5. Với phối hợp nhiều skill, dùng skill-interference-benchmark trên các run A/B/A+B cùng task/model/prompt/criteria. Dữ liệu fixture/manual không được trình bày như native result; không bịa token/time bị thiếu.
6. Review diff, tool permissions, bundle resources, user authorization rồi mới áp dụng. Sau áp dụng chạy checks liên quan. Đọc docs/INTEROPERABILITY_GUIDE.md; CLI không tự promote hoặc gọi model.

## Evidence

Trả raw/bundle hashes trước/sau, contract checks, scenario/gate records, runtime scope và phần native chưa chạy. Score là completeness; quality_evaluated=false/quality_score=null cho offline check.

## Failure handling

Stable/resource/suite thay đổi, candidate đổi sau test hoặc stale proof: dừng apply, review diff và tạo baseline/retest đúng nguyên nhân. Không sửa hash/report/acceptance để làm xanh. YAML ngoài subset không đồng nghĩa native-invalid.

## Stop conditions

Không áp dụng stable trước benchmark/gates/review theo quyền đã có. Native A/B chỉ chạy khi có authentication, corpus/grader và ngân sách phù hợp; không hứa chất lượng hay token saving từ log bytes hoặc fixture. Hết budget thì báo blocker, không tự loop evolution vô hạn.
