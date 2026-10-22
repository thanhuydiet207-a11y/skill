# OMEGA 0.3: đánh giá và nâng cấp có kiểm chứng

> Báo cáo lịch sử 0.3. Bản hiện tại và những giới hạn đã được xử lý thêm: [UPGRADE_0_4.md](UPGRADE_0_4.md).

## Phạm vi hoàn thành

Nâng cấp lần lượt 5 skill nền tảng, thêm 8 skill với command và scenario thật; không tạo thêm agent hoặc placeholder. Catalog giữ 36 capability gốc và 8 extension, tổng 44 mục/6 nhóm: 13 implemented, 31 planned. 3 agent spec hiện có giữ nguyên quyền và chưa nghiệm thu native. Tooling dùng Python stdlib, không cài dependency mới trong đợt này.

Báo cáo máy đọc hiện tại: [interop-upgrade.json](evidence/interop-upgrade.json). Các số liệu 0.1/0.2 trong báo cáo cũ chỉ có giá trị lịch sử. Contract completeness không đo chất lượng suy luận; quality_score=null, native_release_eligible=false là chủ ý.

## Thứ tự sửa

Ưu tiên những lỗi đã tái hiện được: hook không nhận lệnh được tài liệu khuyến nghị; runner thao tác nhầm engine khi ở project khác; kết quả test chỉ có exit code; evidence không thấy chmod/index drift; chấm skill rỗng đạt 100; sau đó mới thêm các extension phục vụ phối hợp và đánh giá.

Stable cũ được snapshot; 5 candidate được benchmark/gates/compare trước khi áp dụng. Sau áp dụng chạy lại gates và workflow. Các review tiếp theo bổ sung regression cho lỗ hổng mới phát hiện; suite thay đổi nên tạo baseline mới, không gọi các score khác suite là cải thiện định lượng. Final validation kiểm tra lại cả 13 skill, source bundle và runtime đang dùng. Không có bước tự promote từ số điểm.

## Đánh giá từng skill

| Skill | Phần đã tốt hơn, có kiểm thử | Phần còn thiếu và hướng xử lý |
|---|---|---|
| repo-map | inventory có phân loại, byte budget cho toàn JSON, số file bị bỏ và status_truncated; runner tách engine/target | Không phải dependency graph hay phân tích semantic. Reviewer chọn source/dependencies theo task; chỉ thêm dependency-map khi có corpus chứng minh nhu cầu. |
| controlled-change | ledger acceptance/scope/budget; giữ dirty baseline có chủ ý; fingerprint nội dung/mode/index; scope_passed tách ready_for_review | Không khóa tiến trình writer và không hiểu acceptance ngữ nghĩa. Phân quyền sandbox, owner/worktree và review vẫn bắt buộc; scheduler chưa triển khai. |
| quality-gates | đủ bốn gate; adapter omega/Jest/Go/JUnit; reject zero/allskip/inconsistent/truncated; known runtime fingerprint | Security gate chỉ dò bypass pattern; không phải SAST hay secret scan. Chọn scanner/gate phù hợp target và review argv; Jest/Go/JUnit mới kiểm thử parser fixture. |
| project-memory | decision key, evidence/source refs và soft/hard stale; từ chối state không ignore/đã tracked | Không đồng bộ memory liên-worktree/máy; lọc secrets bằng heuristic. Review ADR thủ công trước chia sẻ; chưa tự import/global learning. |
| skill-benchmark | section rỗng không đạt; hash tài nguyên tham chiếu; evidence gate + scenario + source/runtime; native claim tách riêng | Offline contract không đo độ đúng của lời khuyên. Cần native corpus, model/grader cố định và nhiều trial; dữ liệu local không có chữ ký. |
| omega-skill-compatibility-audit | roots tường minh, duplicate skill name, overlap hook event, workflow conflict; parser safe subset; không execute prompt/hook | Không suy ra mọi xung đột ngữ nghĩa; không giải quyết native precedence. Dùng explicit roots và thử phối hợp native khi có xác thực. |
| omega-effective-policy-explainer | chung grammar hook/CLI, nguồn rule và scope; shell composition bị từ chối | Không phân giải managed/user/plugin permission. platform_decision=unknown; cần native allow/deny probes trước đăng ký hook. |
| omega-workflow-handoff-contract | DAG, owner duy nhất, unordered writer và cap agent; worker không được khai chi phí 0 | Chỉ exact file paths, không glob/directory ownership; không dispatch/lock. Liệt kê đúng files, cô lập writer và review task plan. |
| omega-skill-interference-benchmark | A/B/A+B matched, hash skill bundle/prompt, model/grader/version/provenance cố định; all-combined acceptance và regressions | Dữ liệu import có thể sai hoặc giả. Cần độc lập kiểm tra grader/provider; tool không gọi model và không tự duyệt native release. |
| omega-project-workflow-adapter | đọc manifest Node/Go/Python; đề xuất command/adapter và phần gate còn thiếu; không install/write | Không đảm bảo npm test là Jest, không suy ra lệnh security thật. Mọi proposal exit 1 đến khi người điều phối cấu hình và chạy target. |
| omega-evidence-reconciler | current/stale-source/stale-runtime/different-head phân biệt; exact gates/outcomes | Known runtime không bao phủ toàn dependencies/service/global policy. Thay môi trường ngoài fingerprint vẫn cần revalidate. |
| omega-memory-reconciliation | nhóm decision key, giữ cả alternatives, báo stale/body khác nhau | Khác câu chữ chưa phải mâu thuẫn logic; không chọn mới nhất làm đúng. Người có ngữ cảnh quyết định và ghi ADR mới. |
| omega-context-sufficiency-check | giữ acceptance/constraints, ranges, full-file hash và nguyên văn nội dung; reject task sai kiểu/nguồn quá lớn | Không thể biết manifest đã liệt kê hết dependency. Giữ bước điều tra và mở rộng packet khi còn thiếu, không dùng packet nhỏ để hứa output LLM giống hệt. |

## Ưu tiên và phối hợp với skill khác

OMEGA không đặt mình cao hơn permissions của platform hoặc yêu cầu người dùng. Tài liệu tham khảo, issue, memory, output MCP và prompt của skill bên ngoài là nguồn cần đánh giá trong phạm vi đã được giao, không tự cấp quyền. Frontmatter/manual invocation không thay sandbox.

Phân biệt hai việc: Claude chọn/resolve skill name theo runtime đã cài; người điều phối chọn workflow owner cho task. Phần đầu chưa kiểm chứng native nên OMEGA không công bố bảng precedence giữa managed/user/project/plugin. Phần sau đã có validator: chọn một orchestrator, tối đa một owner workflow/Git/gates/memory khi resource được dùng. Skill chuyên môn trả artifact, không tự mở workflow thứ hai, push/deploy hoặc promote.

| Kết hợp | Rủi ro từ các file đã đọc ở phiên bản pin | Cách phối hợp được đề xuất; chưa phải thử nghiệm native |
|---|---|---|
| obra/superpowers | bootstrap/worktree/finishing workflow có thể chồng với OMEGA controlled-change | Chọn một bên sở hữu workflow và Git. Bên kia chỉ làm implementation/review có scope; không tạo hai worktree hoặc lặp verify tự động. |
| affaan-m/everything-claude-code | hooks/agents/learning có thể chồng event và vòng đời memory | Audit hook config tường minh; không bật global learning từ memory local; giao một owner cho memory/gates. |
| github/spec-kit | plan/implement có chu kỳ và acceptance riêng | Dùng spec đã duyệt làm input acceptance; Spec Kit sở hữu workflow hoặc bàn giao bằng contract, OMEGA cung cấp evidence/gates. |
| anthropics/skills, skill-creator | metadata/frontmatter và evaluation lifecycle khác contract OMEGA | Safe parser báo unsupported cần review, không kết luận skill native sai; không dùng contract score thay eval của skill-creator. |

Nguồn đã đọc ở các commit cụ thể, không cài/chạy plugin ngoài:

- [anthropics/skills](https://github.com/anthropics/skills/tree/dbd4588f9e1033efb41dad4bef2f7947c8993d44)
- [obra/superpowers](https://github.com/obra/superpowers/tree/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b)
- [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code/tree/90606c8315ee09cafc303515c5f33024db6b9882)
- [github/spec-kit](https://github.com/github/spec-kit/tree/27d14e20c187c1f2916540ea201ecbdc9f8ed588)
- [anthropics/claude-code](https://github.com/anthropics/claude-code/tree/5ed799e5cc56bea9efff57398ca43e31d82784ff)

Đây là static review các file chọn lọc, không phải quét toàn GitHub hoặc chứng nhận mọi phiên bản tương thích. Re-audit khi version/config đổi. Lệnh và schema từng thành phần: [INTEROPERABILITY_GUIDE.md](INTEROPERABILITY_GUIDE.md).

## Rà soát sau triển khai

| Lỗi/thiếu sót phát hiện thật | Xử lý và evidence kiểm tra |
|---|---|
| Target unittest không import được module của target khi runner nằm ở engine | Thêm target cwd cho test runner; integration test chạy thực tế trên Git checkout Python riêng. |
| Worker khai agents=0 để lọt budget, cap workflow không theo config | Chỉ orchestrator được 0; cap khai báo không được cao hơn config; regression test lịch cap=1. |
| A/B cho phép đổi prompt giữa trial hoặc không regression dù tất cả arm fail | Prompt cố định theo task; combined acceptance cũng bắt buộc, regression tests âm. |
| A/B chưa ràng buộc phiên bản skill/grader | Bắt khai bundle digests đúng arm và grader_version cố định; reject drift. |
| Input malformed gây lỗi không có chẩn đoán phù hợp; nguồn context đọc quá lớn | Kiểm tra task/result type, bounded source/JSON và depth/collection budget; reject trước xử lý tiếp. |
| Hook inventory có duplicate key/deep JSON/unknown type, nguy cơ echo command nhạy cảm | Dùng bounded JSON chung, limit hook rows, chỉ hash command payload/matcher; negative fixtures. |
| State có thể vào Git, map envelope lớn hơn budget | Refuse state nếu chưa ignore hoặc đã tracked; bound toàn inventory và báo omission/truncation. |

## Việc chưa làm và lộ trình

1. Nghiệm thu native có xác thực: discovery 13 skill, agent tools, thứ tự hook và allow/deny thực tế; không bật hook bằng schema đoán. CLI Claude 2.1.308 chỉ được kiểm tra metadata/version/help.
2. Corpus đa dự án và mô hình: chạy actual Jest/Go/JUnit pipelines, adapter cho runner khác khi có nhu cầu; thêm security scanner phù hợp từng target.
3. Native A/B/A+B nhiều trial, output acceptance chấm độc lập, usage từ provider. Chỉ sau đó kết luận chất lượng hoặc token/cost; JSON byte savings hiện tại không chứng minh mức tiết kiệm token.
4. Nếu tác vụ thực tế cần: project identity/memory export có provenance, dependency-map và semantic impact analysis. Đây là ý tưởng/roadmap, chưa có implementation hoặc lời hứa tự động.

Không mở thêm hàng chục skill để đủ số lượng. Ưu tiên đóng các giới hạn trên bằng dữ liệu thật; mọi thay đổi stable tiếp theo phải có candidate và kiểm chứng theo cùng điều kiện.
