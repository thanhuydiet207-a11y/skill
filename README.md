# OMEGA

Hệ thống AI Engineering có bằng chứng: **một skill `/omega`**, 13 chế độ nội bộ, Subagents và hook adapter tùy chọn. Python stdlib làm lõi; TypeScript là bridge điều phối/giao tiếp. Runtime Python dùng stdlib; TypeScript bridge không có dependency ứng dụng, type-check dùng dev tools đã pin.

Trong Claude Code gọi `/omega phân tích repository này` hoặc `/omega sửa lỗi … và chạy kiểm thử`. Entry duy nhất là [.claude/skills/omega/SKILL.md](.claude/skills/omega/SKILL.md); hướng dẫn từng chế độ nằm trong references và chỉ đọc khi cần. Cần checkout đầy đủ để chạy Python engine; chỉ tải SKILL.md vào Claude Web không cài engine.

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
- [Quy tắc điều phối Claude](CLAUDE.md)

**Bản 0.6: gộp 13 skill thành một `omega`**, giữ 13 quy trình trong references, 3 agent spec và toàn bộ CLI chức năng. Catalog có 44 capability: 13 đã triển khai dưới dạng chế độ của omega, 31 còn planned; 7 vai trò agent khác là thiết kế.

[Cách dùng và chuyển sang một skill](docs/UNIFIED_SKILL.md) · [Python core + TypeScript bridge, MCP/UI boundary](docs/PYTHON_TYPESCRIPT_BOUNDARY.md) · [Hướng dẫn sử dụng](docs/INTEROPERABILITY_GUIDE.md).

Đã xác minh CLI Claude Code 2.1.308 bằng version/help. Chưa có phiên xác thực để nghiệm thu slash skills, subagent runtime, hook registration hay đo token model. Hook không tự kích hoạt; MCP local không được cấu hình. Trạng thái managed/user/plugin bên ngoài vẫn chưa quan sát được.

Tối ưu context không đổi quality gates: [Token efficiency](docs/TOKEN_EFFICIENCY.md).

Báo cáo lịch sử 0.2: [Deep hardening](docs/DEEP_HARDENING.md). Kết quả hiện tại được phân biệt rõ trong [Validation](docs/VALIDATION.md).
