# OMEGA

Hệ thống AI Engineering tối giản, có bằng chứng: Skills + Subagents + hook adapter tùy chọn. Lõi chạy bằng Python chuẩn, không dependency bên thứ ba.

```bash
python3 -m omega doctor
python3 -m omega map
python3 -m omega plan --complexity medium
python3 -m omega gates
```

- [Kiến trúc: 36 capability gốc + 8 extension, 10 vai trò](docs/ARCHITECTURE.md)
- [Cấu hình và sử dụng từng thành phần](docs/OPERATIONS.md)
- [Bằng chứng kiểm thử và giới hạn](docs/VALIDATION.md)
- [Quy tắc điều phối Claude](CLAUDE.md)

**Bản 0.3: nâng cấp 5 skill nền tảng và thêm 8 skill hoạt động bằng CLI**, tổng 13 SKILL.md và 3 agent spec. Catalog có 44 mục; 31 skill và 7 vai trò còn lại là thiết kế, không có file giả.

[Hướng dẫn kết hợp skill, policy, workflow, adapters và evidence](docs/INTEROPERABILITY_GUIDE.md). [Đánh giá từng skill và các giới hạn còn lại](docs/UPGRADE_0_3.md).

Đã xác minh CLI Claude Code 2.1.308 bằng version/help. Chưa có phiên xác thực để nghiệm thu slash skills, subagent runtime, hook registration hay đo token model. Hook không tự kích hoạt; MCP local không được cấu hình. Trạng thái managed/user/plugin bên ngoài vẫn chưa quan sát được.

Tối ưu context không đổi quality gates: [Token efficiency](docs/TOKEN_EFFICIENCY.md).

Báo cáo lịch sử 0.2: [Deep hardening](docs/DEEP_HARDENING.md). Kết quả hiện tại được phân biệt rõ trong [Validation](docs/VALIDATION.md).
