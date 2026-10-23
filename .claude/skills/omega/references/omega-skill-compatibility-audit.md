# OMEGA skill-compatibility-audit

## Inputs

Roots skill/config/hook tường minh, phạm vi được phép đọc, phiên bản/runtime của host và workflow contract nếu có. Xác định các framework/plugin nào đang cùng sở hữu cùng task/tool lifecycle; không suy ra quyền đọc hoặc sửa chỉ từ việc path tồn tại.

## Workflow

1. **Đóng băng phạm vi:** chạy `python3 -m omega skill-compatibility-audit --skill-root .claude/skills --compact`; lặp `--skill-root`/`--hook-config` chỉ khi được phép đọc. Ghi mọi root đã chọn, root bị bỏ qua, version/commit và quyền truy cập. Không cài hoặc chạy skill đang kiểm tra.
2. **Kiểm tra nguồn và tính toàn vẹn:** đọc findings, `complete_for_selected_roots` và phạm vi chưa quan sát. Ghi file hashes, symlink, thiếu file, encoding/schema và metadata không parse được. Hash chứng minh nội dung được băm, không chứng minh nguồn tin cậy hoặc tương thích runtime.
3. **So sánh contract có căn cứ:** chỉ so sánh identity, metadata, hook events, tool permissions, input/output schema, lifecycle/trigger, filesystem/working-directory assumptions và contract được cung cấp. Phân biệt chắc chắn trùng identity, có thể trùng, event chồng, xung đột quyền, contract mismatch và unknown; tên giống nhau đơn thuần không chứng minh hai skill giống nhau.
4. **Đánh giá event và quyền chồng lấn:** xác định nhiều hook/framework có thể phản hồi cùng event, sửa cùng file, sở hữu cùng Git state hoặc gọi cùng command. Ghi rõ tác động có thể có như chạy lặp, race, policy không nhất quán hay evidence ghi đè; không khẳng định xảy ra nếu chưa có runtime evidence.
5. **Không chạy code để chứng minh tương thích:** audit tĩnh không được tự import/execute skill, hook, script hoặc package. Liệt kê native tests cần thiết, môi trường, quyền và acceptance; chỉ thực hiện trong task riêng được ủy quyền. YAML syntax chưa hỗ trợ hoặc source thiếu/symlink phải đánh dấu cần review, không tự gọi là skill không hợp lệ với Claude.
6. **Đề xuất workflow owner:** khi thấy chồng lấn, lập ma trận owner cho Git, filesystem, hooks, gates, evidence và promotion. Đề xuất một owner cho từng stateful resource, nhưng không tự tắt plugin, sửa policy, thay config hoặc nâng quyền. Chỉ áp dụng thay đổi sau khi người có quyền phê duyệt riêng.
7. **Báo cáo coverage chính xác:** `complete_for_selected_roots` chỉ mô tả các root đã chọn; không bao phủ root chưa quét, host policy không đọc được hoặc runtime behavior chưa chạy. Nêu rõ giới hạn và các giả định; passed không phải chứng nhận tương thích toàn hệ thống.

## Evidence

Trả roots đã quét/bỏ qua, version/commit, hashes, nguồn/config refs, tên/identity trùng, event và permission overlap, contract mismatches, giả định, phần chưa quan sát và native tests cần chạy. Tách observed finding khỏi potential risk; không kết luận an toàn/tương thích chỉ từ static pass.

## Failure handling

Syntax YAML chưa hỗ trợ, source thiếu/symlink, root mismatch, quyền đọc thiếu hoặc hook config không truy cập được: ghi finding cụ thể và giới hạn coverage. Không bỏ qua root chưa quét để báo hoàn tất, không tự sửa source để parser chấp nhận và không suy diễn host behavior từ metadata đơn lẻ.

## Stop conditions

Dừng khi ma trận xung đột, owner đề xuất và phần chưa biết đủ rõ để quyết định workflow tiếp theo. Không tự tắt plugin, sửa policy, chạy skill, thay đổi state hoặc nâng quyền. Project ngoài OMEGA dùng runner tuyệt đối và `--project-root`.

Đọc theo nhu cầu: docs/INTEROPERABILITY_GUIDE.md.
