# Claude Code: kiểm tra phiên bản thực tế

Trong đợt 0.2 đã cài **@anthropic-ai/claude-code 2.1.308** vào `.omega/tools/claude` bằng npm registry qua TLS và kiểm tra integrity chuẩn của npm. Node hiện có v24 đáp ứng engine >=22 của package. Không thêm dependency vào ứng dụng, không cài global, không commit binary/cache/state.

Lần đầu cài với `--ignore-scripts`, wrapper báo thiếu native binary. Đã đọc `install.cjs` của package: script chọn optional platform package và hardlink/copy binary vào chính thư mục package. Chạy riêng postinstall đã review làm `--version` và `--help` hoạt động. Không bỏ TLS/checksum hoặc thay expected integrity để vượt lỗi.

## Điều đã xác minh

- `--version`: 2.1.308 (Claude Code), exit 0.
- `--help`, `agents --help`, `auth status --help`: CLI chạy được.
- `auth status --json` trong CLAUDE_CONFIG_DIR riêng trả loggedIn=false, exit 1. Không có ANTHROPIC_API_KEY hoặc CLAUDE_CODE_OAUTH_TOKEN trong process hiện tại; chỉ kiểm tra presence, không đọc/in giá trị.
- `agents` ở phiên bản này quản lý background sessions; không được dùng kết quả help như bằng chứng nhận diện 3 custom subagent spec.
- Không gửi request model, không chạy session LLM, không bật hooks/MCP, không dùng cờ bỏ permissions, không đăng nhập hoặc sao chép credential.

Bản native metadata nằm trong [deep-hardening.json](evidence/deep-hardening.json). Native skill discovery, agent delegation, hook registration và chất lượng reasoning tiếp tục UNVERIFIED.

## Doctor và tái sử dụng

`python3 -m omega doctor --compact` tìm Claude trong PATH hoặc local tool trên, chạy version probe với timeout 15 giây. State được đặt tại `.omega/claude-state`; không dùng HOME giả hoặc ghi global config. Exit 0 của doctor không thay việc đọc từng capability/result.

Để tái lập tool tùy chọn (cần Node >=22 và review package):

```bash
npm install --prefix "$PWD/.omega/tools/claude" --cache "$PWD/.omega/npm-cache" --ignore-scripts --no-audit --no-fund --save-exact @anthropic-ai/claude-code@2.1.308
```

Sau cài, đọc install.cjs và metadata platform package, rồi chạy riêng `node .omega/tools/claude/node_modules/@anthropic-ai/claude-code/install.cjs` nếu phù hợp. OMEGA doctor không tự download/cài tool.

Để nghiệm thu LLM, người dùng đăng nhập bằng flow hỗ trợ của Claude hoặc cấu hình credential qua cơ chế bảo mật của môi trường. Không dán secret vào chat/Git. Sau thay đổi xác thực, kiểm tra lại operation trước khi yêu cầu thêm binding. Chỉ bắt đầu native task corpus khi có ngân sách/đích API/quyền phù hợp; không suy ra access từ biến có mặt hoặc help chạy được.

## Bản 0.3

Doctor trả hooks_enabled/mcp_enabled=unknown vì không quan sát đủ managed/user/plugin policy. Version probe không là bằng chứng discovery/permissions. Grammar CLI và hook adapter đã dùng chung; adapter vẫn chưa được đăng ký trong Claude. State probe chỉ tạo trong .omega đã review ignore và không có file tracked.
