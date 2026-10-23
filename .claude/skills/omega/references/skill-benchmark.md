# OMEGA skill-benchmark

## Inputs

Skill trong registry hiện tại, mục tiêu thay đổi, baseline/candidate tách biệt, acceptance cố định, task corpus, grader/rubric, model/provider/version (nếu có), sampling settings, dependencies/resources và ngân sách. Skill planned chưa được coi là có thể chạy. Trước khi đo, xác định loại tuyên bố cần hỗ trợ: contract completeness, tool/runtime correctness, instruction adherence, task quality, hoặc chi phí/độ trễ; một loại không tự chứng minh loại khác.

## Workflow

Full engine build phải qua strict TypeScript compiler/noEmit bên cạnh Python tests; bridge Node tests là nghiệm thu riêng, không dùng type stripping thay type-check. Suite hash gồm source/tsconfig/package-lock, prune node_modules và __pycache__, từ chối source symlink. Giữ native quality và token provider là unknown cho đến evaluation thật; xem docs/UPGRADE_0_5.md.

1. **Đóng băng protocol trước khi chạy:** ghi mục tiêu, acceptance, corpus/version, rubric, điều kiện pass/fail, model/provider/version, prompt, temperature/sampling settings, tool permissions, timeout, retry policy và ngân sách. Không thay rubric, chọn task hoặc loại trial sau khi xem kết quả nếu không ghi thành một protocol version mới và chạy lại baseline lẫn candidate.
2. **Chụp baseline/candidate:** chạy `python3 -m omega candidate --skill TEN --compact` trước sửa. Chỉ sửa candidate, giữ stable và tài nguyên baseline; bundle hash ràng buộc SKILL.md cùng references nhận diện được. Ghi raw hash và bundle hash; bảo đảm baseline/candidate không vô tình trỏ cùng bundle, và không để candidate đọc tài nguyên hoặc đáp án riêng của baseline ngoài giao thức.
3. **Kiểm tra nội dung và quyền:** viết section có nội dung thực và commands có thể chạy. Metadata/license trong safe YAML subset được chấp nhận; syntax chưa hỗ trợ cần review. Review quyền tool, side effects và trust boundary trước benchmark có thực thi lệnh. Contract completeness không phải quality score, không chứng minh instruction adherence.
4. **Chạy benchmark cấu trúc:** chạy `python3 -m omega benchmark --skill TEN --candidate PATH --compact`. Đọc contract, suite/bundle hashes và đúng workflow pattern cho foundation hoặc extensions; tooling scenarios không đánh giá model đọc prompt. Xác nhận fixture, mock và kết quả native được phân loại riêng; fixture pass chỉ chứng minh behavior của fixture.
5. **Chạy gates và đối chiếu:** chạy `python3 -m omega gates --summary --compact`, rồi `python3 -m omega compare --baseline BASELINE --evidence SCENARIO --evidence GATES --compact`. Cần `eligible_for_review=true` với source/index/runtime hiện tại, nhưng `native_release_eligible` vẫn false cho đến khi điều kiện native riêng được thỏa. Không coi trạng thái review là tự động cho phép promote/release.
6. **Đánh giá native có kiểm soát:** khi có model/provider và corpus/grader phù hợp, chạy baseline và candidate trên cùng task, prompt, quyền, giới hạn và tiêu chí. Dùng nhiều trial khi sampling không deterministic; ghi seed nếu có, số trial, thất bại, retry và phân bố kết quả thay vì chỉ chọn run tốt nhất. Nếu corpus nhỏ hoặc mẫu thiếu lực thống kê, nêu rõ bất định; không tuyên bố cải thiện tổng quát từ một vài ví dụ.
7. **Kiểm tra regression và nhiễu:** báo riêng task mới cải thiện, task giữ nguyên, task suy giảm, lỗi an toàn/quyền công cụ, timeout và chi phí. Kiểm tra các trường hợp đối kháng và task ngoài happy path. Với phối hợp nhiều skill, dùng skill-interference-benchmark trên các run A/B/A+B cùng task/model/prompt/criteria; nếu có thể, lặp lại theo thứ tự cân bằng để giảm ảnh hưởng thứ tự và cache. Dữ liệu fixture/manual không được trình bày như native result; không bịa token/time bị thiếu.
8. **Đóng băng bằng chứng và review:** sau khi benchmark, xác minh raw/bundle hash, suite hash, model/runtime/config và candidate vẫn khớp. Review diff, tool permissions, bundle resources, user authorization rồi mới áp dụng. Sau áp dụng chạy checks liên quan. Đọc docs/INTEROPERABILITY_GUIDE.md; CLI không tự promote hoặc gọi model. Mọi thay đổi candidate, rubric, suite hoặc runtime có ảnh hưởng đều làm bằng chứng tương ứng stale và cần retest.

## Evidence

Trả raw/bundle hashes baseline và candidate, suite/corpus/rubric hashes hoặc phiên bản, contract checks, scenario/gate records, model/provider/runtime scope, số trial, pass/fail theo nhóm, regressions, timeout/retry, chi phí/token/độ trễ nếu thực sự được đo, và phần native chưa chạy. Nêu rõ giới hạn mẫu và điều kiện không được fingerprint. Score offline là completeness; dùng `quality_evaluated=false`/`quality_score=null` cho offline check. Không suy ra tiết kiệm token từ kích thước log hoặc suy ra chất lượng từ contract score.

## Failure handling

Stable/resource/suite/rubric/model/runtime thay đổi, baseline/candidate bị nhiễm lẫn, candidate đổi sau test, trial thiếu hoặc stale proof: dừng apply, ghi nguyên nhân, tạo protocol/baseline mới khi cần và retest công bằng. Không sửa hash/report/acceptance để làm xanh, loại trial thất bại không có quy tắc định trước, hoặc chọn metric sau khi thấy kết quả. YAML ngoài subset không đồng nghĩa native-invalid. Nếu grader không đáng tin hoặc không thể đánh giá nhất quán, báo blocker thay vì khẳng định chất lượng.

## Stop conditions

Không áp dụng stable trước benchmark/gates/review theo quyền đã có. Native A/B chỉ chạy khi có authentication, corpus/grader và ngân sách phù hợp; không hứa chất lượng hay token saving từ log bytes hoặc fixture. Dừng khi protocol đã chạy đủ trong ngân sách hoặc điều kiện dữ liệu/môi trường không đáp ứng; báo rõ blocker, kết quả đã biết và phần chưa được xác minh. Không tự loop evolution vô hạn.
