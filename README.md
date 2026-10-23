# OMEGA

Hệ thống AI Engineering đóng gói thành **plugin Claude Code**: một skill omega, 13 chế độ nội bộ và 3 agent. Python stdlib làm lõi; TypeScript là bridge điều phối/giao tiếp. Runtime Python dùng stdlib; TypeScript bridge không có dependency ứng dụng, type-check dùng dev tools đã pin.

```text
/plugin marketplace add thanhuydiet207-a11y/skill
/plugin install omega@omega-marketplace
```

Hoặc: `/plugin install omega --marketplace thanhuydiet207-a11y/skill`. Khởi động lại phiên rồi gọi `/omega:omega phân tích repository này`. [Cài đặt, ZIP và kiểm chứng plugin](docs/CLAUDE_PLUGIN.md).

Entry duy nhất là [.claude/skills/omega/SKILL.md](.claude/skills/omega/SKILL.md); references chỉ đọc khi cần. Plugin chứa Python engine và dùng đường dẫn cache tuyệt đối để thao tác project đích. Trong checkout nguồn vẫn có local `/omega`. Chỉ tải SKILL.md vào Claude Web không cài engine.

```bash
# Cài dev tools cần cho full engine build; không chạy lifecycle scripts:
npm ci --prefix integration/typescript --ignore-scripts --no-audit --no-fund --cache "$PWD/.omega/npm-cache"
python3 -m omega doctor
python3 -m omega map
python3 -m omega plan --complexity medium
python3 -m omega gates
```

- [Kiến trúc: 36 capability gốc + 8 extension, 10 vai trò](docs/ARCHITECTURE.md)
- [Cấu hình và sử dụng từng thành phần](docs/OPERATIONS.md)
- [Bằng chứng kiểm thử và giới hạn](docs/VALIDATION.md)
- [Quy tắc điều phối Claude](.claude/CLAUDE.md)

**Bản 0.7: plugin + marketplace tự host trên GitHub**, giữ một skill omega, 13 quy trình, 3 agent và toàn bộ CLI chức năng. Catalog có 44 capability: 13 đã triển khai dưới dạng chế độ của omega, 31 còn planned; 7 vai trò agent khác là thiết kế.

[Cách dùng và chuyển sang một skill](docs/UNIFIED_SKILL.md) · [Python core + TypeScript bridge, MCP/UI boundary](docs/PYTHON_TYPESCRIPT_BOUNDARY.md) · [Hướng dẫn sử dụng](docs/INTEROPERABILITY_GUIDE.md).

Đã xác minh Claude Code 2.1.308: strict validation hai manifest, cài local marketplace vào config riêng, inventory bản cài và ZIP, engine trong install cache chạy project fixture đỏ → xanh. Chưa có trace phiên suy luận để nghiệm thu skill/agent reasoning hoặc token model. Plugin không đăng ký hook/MCP; managed/user policy bên ngoài vẫn chưa quan sát đầy đủ.

Tối ưu context không đổi quality gates: [Token efficiency](docs/TOKEN_EFFICIENCY.md).

Báo cáo lịch sử 0.2: [Deep hardening](docs/DEEP_HARDENING.md). Kết quả hiện tại được phân biệt rõ trong [Validation](docs/VALIDATION.md).


## Dùng OMEGA như skill trong ChatGPT

Tạo ZIP có `SKILL.md` tương thích ChatGPT cùng các reference Markdown:

```bash
python3 tools/export_chatgpt_skill.py
```

File đầu ra: `.omega/chatgpt-export/omega-chatgpt.zip`. Sau đó mở ChatGPT desktop → Skills (hoặc Plugins → Skills) → Create → Upload from computer. Tính năng này phụ thuộc gói tài khoản và chính sách workspace. Bản export mang theo hướng dẫn/tài liệu, **không** cài Python engine, Claude hooks hay MCP. Xem [hướng dẫn đầy đủ](docs/CHATGPT_SKILLS.md).
