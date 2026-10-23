# OMEGA skill-interference-benchmark

## Inputs

Các run A, B và A+B trên cùng task/trial; prompt hash, model/provider/version, system/developer context có liên quan, tool permissions, sampling settings, acceptance/rubric, corpus version và provenance. Token/time thật hoặc `null`; giữ đơn vị, nguồn đo và điều kiện đo. Xác định trước metric chính, metric an toàn, quy tắc xử lý retry và ngân sách.

## Workflow

1. **Đóng băng protocol:** chạy `python3 -m omega skill-interference-benchmark --input INPUT --compact`. Trước khi đọc kết quả, ghi task corpus, acceptance/rubric, model/version, prompt/context hashes, permissions, sampling settings, retry policy, metric chính và ngưỡng regression. Không đổi tiêu chí sau khi xem arm nào tốt hơn.
2. **Ghép arm công bằng:** yêu cầu đủ A, B, A+B cho mỗi task/trial; xác minh task ID, prompt/context hash, model/version, tool permissions và điều kiện runtime khớp. Một arm thiếu hoặc chạy trên model/prompt/criteria khác thì từ chối so sánh cặp đó thay vì suy diễn.
3. **Kiểm tra tính toàn vẹn run:** phát hiện duplicate run, record bị copy, trial ID trùng, kết quả thiếu, source/skill bundle thay đổi hoặc provenance không đầy đủ. Duplicate không được tính là trial độc lập. Không cho A+B đọc đáp án/artefact chỉ có ở một arm nếu đó không phải điều kiện được chủ ý đánh giá.
4. **Đo hiệu ứng tương tác:** so acceptance và regression theo từng task giữa A, B và A+B. Phân biệt hiệu ứng riêng của A/B với phần thay đổi khi kết hợp; không kết luận rằng A+B tốt hơn chỉ vì điểm tổng cao nếu task quan trọng hoặc invariant an toàn bị suy giảm. Báo kết quả theo nhóm task và failure mode, không chỉ một điểm trung bình.
5. **Giảm nhiễu sampling/order:** khi output không deterministic, dùng nhiều trial độc lập và giữ seed/settings nếu có. Nếu có thể, cân bằng thứ tự chạy A/B/A+B để giảm cache, warm-up, rate-limit hoặc drift theo thời gian. Ghi rõ số trial, tỷ lệ thành công, phân bố/độ bất định và giới hạn lực thống kê; không chọn run tốt nhất hoặc coi một trial là bằng chứng tổng quát.
6. **Đối chiếu usage:** so token/time/latency/cost chỉ khi dữ liệu thật, cùng đơn vị và cùng phương pháp đo. Usage thiếu phải giữ `null`, không cộng thành 0 hoặc nội suy mà không ghi phương pháp. Báo mean và số mẫu khi đủ dữ liệu; nếu mẫu nhỏ hoặc phép đo không tương đương, ghi chưa thể kết luận.
7. **Review safety và regressions:** kiểm tra tool misuse, scope violations, output contract failures, timeout, retries, privacy/security regressions và side effects. Regression an toàn nghiêm trọng không được bù trừ bằng điểm chất lượng hoặc token saving. Nếu combined regression, giữ stable và điều tra nguyên nhân trước khi áp dụng.
8. **Tách fixture khỏi native evaluation:** fixture chỉ kiểm tra analyzer/schema/logic tổng hợp, không là đánh giá LLM. Kết quả manual phải ghi nguồn và giới hạn; không trộn fixture/manual với native run trong cùng metric mà không phân tầng rõ. Dữ liệu nhập cần review nguồn độc lập.
9. **Kết luận có giới hạn:** đưa ra accepted/rejected/uncertain theo acceptance đã định, nêu task nào suy giảm và điều kiện tái hiện. Benchmark chỉ hỗ trợ quyết định review; không tự promote hoặc cấp quyền phát hành.

## Evidence

Trả protocol/corpus/rubric hashes, arm/run IDs, task/trial pairs, model/prompt/runtime provenance, acceptance và regression theo arm, số trial, duplicate/missing data, safety findings, usage mean/unit/sample count khi đủ dữ liệu và uncertainty/limitations. Giữ token/time không đo được là `null`. Nêu rõ fixture, manual và native results ở các nhóm riêng.

## Failure handling

Thiếu arm, đổi model/prompt/context/criteria, duplicate run, provenance không rõ hoặc điều kiện runtime không khớp: từ chối so sánh bị ảnh hưởng và thu thập lại dữ liệu công bằng. Nếu combined regression, giữ stable và điều tra nguyên nhân; không sửa grader, loại trial thất bại hoặc thay metric để làm xanh. Không thể kết luận thì ghi `uncertain`, không tự suy ra thắng/thua.

## Stop conditions

Dừng sau khi phân tích corpus/trial đã định hoặc khi thiếu dữ liệu/quyền/ngân sách khiến so sánh không còn đáng tin. Không gọi model, không tự promote; `native_release_eligible=false` trừ khi điều kiện native release riêng được xác minh. Không chạy evolution vô hạn.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và `--project-root`.
