# OMEGA controlled-change

## Inputs

Objective, acceptance có thể kiểm chứng, exact paths được phép sửa, target root, quyền người dùng, rollback strategy và giới hạn thời gian. Xác định một Git owner duy nhất để tránh hai framework cùng đổi branch/worktree. Nếu thiếu path, quyền, acceptance hoặc rollback cho thay đổi rủi ro cao, hỏi lại hoặc dừng; không tự suy rộng phạm vi.

## Workflow

1. **Preflight trước khi chạm trạng thái:** chạy doctor/map/plan và xác nhận repository root, branch, HEAD, working tree, staged/unstaged/untracked files, submodules/worktrees liên quan và công cụ đang sở hữu Git. Ghi lại baseline đủ để phân biệt thay đổi có sẵn với thay đổi của task. Không giả định working tree sạch.
2. **Cô lập có kiểm soát:** dùng `python3 -m omega isolate --name TEN` khi cần branch sạch. Chỉ tạo worktree/isolation khi được phép và chưa có isolation phù hợp; không sửa trực tiếp main/master, không tự checkout branch đang được owner khác dùng, không tạo isolation lồng nhau. Nếu branch/HEAD đổi sau preflight, dừng và xác nhận owner trước khi tiếp tục.
3. **Đóng phạm vi thay đổi:** chạy `python3 -m omega change-plan --allow PATH --acceptance "input → expected" --compact` với path chính xác và acceptance có thể fail khi sai. Nếu cần tính các thay đổi người dùng đã review, dùng `--include-existing` để chụp baseline. Không dùng stash/reset/clean/checkout để “dọn” working tree; không ghi đè, di chuyển hoặc xóa file không thuộc task. Xử lý merge conflict trước khi sửa.
4. **Tái hiện và sửa tối thiểu:** tái hiện trigger bằng regression có thể fail trước khi thay đổi. Sửa nhỏ nhất trong scope; mỗi lần sửa tiếp sau lỗi phải ghi nhận qua `python3 -m omega change-attempt --record RECORD --reason "chẩn đoán mới" --compact`. Không tạo task giả, đổi acceptance, bỏ regression hoặc nới allow-path để né ledger/deadline.
5. **Xác minh diff trước gates:** kiểm tra diff cả staged và unstaged, file mới/xóa/rename, generated files, secrets và file ngoài scope. Stage có chọn lọc chỉ những thay đổi dự kiến; không dùng `git add .` khi chưa xác minh toàn bộ working tree. Nếu phát hiện thay đổi ngoài scope, giữ nguyên và dừng để phân loại, không tự loại bỏ hoặc đưa vào commit.
6. **Chạy validation trên đúng trạng thái:** hoàn thành format/codegen cần thiết, sau đó chạy `python3 -m omega gates --summary --compact` và `python3 -m omega change-check --record RECORD --evidence EVIDENCE --compact`; với project khác, chỉ dùng adapter/gate config đã review nguồn và quyền thực thi. Ghi lại command, config/source hash, exit status, thời điểm, HEAD và môi trường thực thi. Nếu source/config/HEAD thay đổi sau validation thì bằng chứng cũ không còn đủ giá trị.
7. **Đánh giá kết quả độc lập:** cần cả `scope_passed` và `ready_for_review`; scope pass không chứng minh acceptance. Gate proof phải khớp source/mode/index, HEAD và execution context đã biết. Khi evidence stale hoặc mâu thuẫn, dùng evidence-reconciler và giải thích nguyên nhân; không tự làm mới hash để biến proof cũ thành hợp lệ.
8. **Review và handoff:** đọc diff cuối, đối chiếu từng acceptance, tác động phụ, compatibility, dữ liệu có thể mất và rollback đã thử/chưa thử. Xác minh runner tuyệt đối, target root và ownership contract theo `docs/INTEROPERABILITY_GUIDE.md`. Với thay đổi rủi ro cao, yêu cầu review độc lập trước merge/deploy.

## Rollback và bảo toàn dữ liệu

- Trước khi sửa, mô tả cách khôi phục riêng cho thay đổi này: các file/artifact sẽ hoàn nguyên, dữ liệu/state ngoài Git bị tác động và điều kiện kích hoạt rollback.
- Ưu tiên revert có phạm vi hoặc khôi phục artifact đã ghi nhận; không dùng `git reset --hard`, `git clean -fd`, force-push hay thao tác tương đương để khắc phục lỗi trừ khi người dùng cho phép rõ ràng và đã xác định chính xác dữ liệu bị ảnh hưởng.
- Nếu rollback có thể xóa thay đổi người dùng, làm mất dữ liệu, chạy migration hoặc tác động dịch vụ, dừng và xin xác nhận trước khi thực hiện. Không tuyên bố rollback an toàn nếu chưa kiểm tra các thay đổi phát sinh sau baseline.
- Không push, merge, publish, deploy, xóa dữ liệu, chạy migration hoặc sửa ngoài repository chỉ vì acceptance/gates đã pass; cần quyền riêng cho hành động đó.

## Evidence

Báo baseline (root/branch/HEAD và trạng thái working tree), allow-path, thay đổi có sẵn được giữ nguyên, trigger trước/sau, diff cuối, lệnh và kết quả gate, config/source hash, runtime scope, acceptance đã/chưa xác minh, rollback plan và phần global policy/dependencies/dịch vụ chưa fingerprint đầy đủ. Phân biệt rõ `not run`, `blocked`, `failed` và `passed`; không biến thiếu bằng chứng thành thành công.

## Failure handling

Ngoài scope, branch/HEAD/owner đổi, conflict, test fail, source/index/runtime drift, evidence stale hoặc rollback không rõ: dừng thay đổi có nguy cơ, giữ nguyên trạng thái hiện có và chẩn đoán nguyên nhân trước khi replan/rerun. Không tự nới paths, hạ required gate, đổi assertion, xóa thay đổi ngoài scope hoặc sửa hash/report để làm evidence hợp lệ. Nếu không thể xác minh an toàn, báo blocker cụ thể và trạng thái hiện tại.

## Stop conditions

Dừng khi acceptance và required gates đạt trong phạm vi đã kiểm chứng, hoặc hết checkpoint 30 phút/2 lượt sửa/thiếu quyền thật. Trước handoff, xác nhận không có thay đổi ngoài scope bị bỏ sót, bằng chứng khớp đúng HEAD và rollback/giới hạn còn lại được ghi rõ.