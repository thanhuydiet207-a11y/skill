# HUTAO — OMEGA Engineering Plugin

Hệ thống AI Engineering đóng gói thành **plugin Claude Code**: một skill omega, 13 chế độ nội bộ và 3 agent. Python stdlib làm lõi; TypeScript là bridge điều phối/giao tiếp. Runtime Python dùng stdlib; TypeScript bridge không có dependency ứng dụng, type-check dùng dev tools đã pin.

```text
/plugin marketplace add thanhuydiet207-a11y/hutao
/plugin install omega@omega-marketplace
```

Hoặc: `/plugin install omega --marketplace thanhuydiet207-a11y/hutao`. Khởi động lại phiên rồi gọi `/omega:omega phân tích repository này`. [Cài đặt, ZIP và kiểm chứng plugin](docs/CLAUDE_PLUGIN.md).

Entry duy nhất là [.claude/skills/omega/SKILL.md](.claude/skills/omega/SKILL.md); references chỉ đọc khi cần. Plugin chứa Python engine và dùng đường dẫn cache tuyệt đối để thao tác project đích. Trong checkout nguồn vẫn có local `/omega`. Chỉ tải SKILL.md vào Claude Web không cài engine.

```bash
# Cùng object JSON, chỉ giảm whitespace ngoài string:
python3 -m omega plan --complexity medium --compact

# Đọc vùng mã nguồn được chọn rõ ràng:
python3 -m omega context --select omega/context.py:1:20 --compact

# Chạy đủ mọi gate, tóm tắt output thành công bằng evidence references:
python3 -m omega gates --summary --compact

# Đo dung lượng và kiểm tra tương đương dữ liệu:
python3 benchmarks/token_efficiency.py
```

- [Kiến trúc](docs/ARCHITECTURE.md)
- [Cấu hình và vận hành](docs/OPERATIONS.md)
- [Bằng chứng kiểm thử và giới hạn](docs/VALIDATION.md)
- [Tiết kiệm context, giữ nguyên dữ liệu và tiêu chí đầu ra](docs/TOKEN_EFFICIENCY.md)
- [Tích hợp RTK tùy chọn, có kiểm soát](docs/RTK_INTEGRATION.md)
- [Quy tắc điều phối Claude](.claude/CLAUDE.md)

**OMEGA 0.7** là plugin + marketplace tự host trên GitHub, trong repository HUTAO. Giữ một skill omega, 13 quy trình, 3 agent và toàn bộ CLI chức năng. Catalog có 44 capability: 13 đã triển khai dưới dạng chế độ của omega, 31 còn planned; 7 vai trò agent khác là thiết kế.

[Cách dùng và chuyển sang một skill](docs/UNIFIED_SKILL.md) · [Python core + TypeScript bridge, MCP/UI boundary](docs/PYTHON_TYPESCRIPT_BOUNDARY.md) · [Hướng dẫn sử dụng](docs/INTEROPERABILITY_GUIDE.md).

Đã xác minh Claude Code 2.1.308: strict validation hai manifest, cài local marketplace vào config riêng, inventory bản cài và ZIP, engine trong install cache chạy project fixture đỏ → xanh. Chưa có trace phiên suy luận để nghiệm thu skill/agent reasoning hoặc token model. Plugin không đăng ký hook/MCP; managed/user policy bên ngoài vẫn chưa quan sát đầy đủ.

Không tuyên bố mức tiết kiệm token thực tế hoặc chất lượng LLM không đổi chỉ từ số byte; xem [Token efficiency](docs/TOKEN_EFFICIENCY.md) và [RTK integration](docs/RTK_INTEGRATION.md).

Báo cáo lịch sử 0.2: [Deep hardening](docs/DEEP_HARDENING.md). Kết quả hiện tại được phân biệt rõ trong [Validation](docs/VALIDATION.md).
