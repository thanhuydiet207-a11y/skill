# OMEGA skill-interference-benchmark

## Inputs

Các run cùng task/trial, prompt hash, model/version, acceptance và provenance; token/time thật hoặc null.

## Workflow

Chạy `python3 -m omega skill-interference-benchmark --input INPUT --compact`. Ghép đủ A, B, A+B; kiểm tra invariants rồi đọc regressions từng task. So usage theo dữ liệu có thật, không cộng số đo thiếu thành 0.

## Evidence

Trả acceptance/regressions theo arm, usage mean khi đủ dữ liệu và provenance. Fixture chỉ kiểm tra analyzer, không là đánh giá LLM.

## Failure handling

Thiếu arm, đổi model/prompt/criteria hoặc duplicate run: từ chối so sánh. Nếu combined regression, giữ stable và điều tra nguyên nhân; không sửa grader để làm xanh.

## Stop conditions

Dừng sau phân tích corpus đã định. Không gọi model, không tự promote; native_release_eligible=false và dữ liệu nhập cần review nguồn độc lập.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md. `python3 -m omega` chỉ dùng trong checkout engine; project khác dùng runner tuyệt đối và --project-root.
