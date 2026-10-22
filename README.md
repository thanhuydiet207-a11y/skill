# OMEGA

Hệ thống AI Engineering tối giản, có bằng chứng: Skills + Subagents + hook adapter tùy chọn. Lõi chạy bằng Python chuẩn, không dependency bên thứ ba.

```bash
python3 -m omega doctor
python3 -m omega map
python3 -m omega plan --complexity medium
python3 -m omega gates
```

- [Kiến trúc: 36 skill, 10 vai trò, phạm vi nghiệm thu](docs/ARCHITECTURE.md)
- [Cấu hình và sử dụng từng thành phần](docs/OPERATIONS.md)
- [Bằng chứng kiểm thử và giới hạn](docs/VALIDATION.md)
- [Quy tắc điều phối Claude](CLAUDE.md)

Đã tạo 5 skill và 3 agent spec. CLI được kiểm thử độc lập; Claude Code chưa có trên máy, nên chưa nghiệm thu slash skills, subagent runtime hoặc hook registration. Hook không tự kích hoạt; MCP không cần cho workflow local và tắt mặc định. 31 skill và 7 agent còn lại chỉ là thiết kế.
