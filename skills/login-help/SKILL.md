---
name: login-help
description: 排查未来船票画布 MCP（canvas_management）的登录问题：扫码后仍提示未登录、工具列表为空、invalid_grant、反复要求重新授权、401/403/404/503。用户说"画布连不上""登录不了""工具没了"时使用。
---

# 画布登录排障

先调 `canvas_auth_status`。能调通说明登录正常，问题在别处；调不通再按下面的现象处理。

| 现象 | 原因 | 让用户这样做 |
| --- | --- | --- |
| 401，或提示需要重新认证 | 授权过期或已撤销 | 在客户端里对 `canvas_management` 重新授权，用 mark-system 小程序扫码确认 |
| `invalid_grant` | 刷新凭证已被轮换、过期或撤销 | 见下面"invalid_grant" |
| 扫码确认后仍显示未登录、工具数为 0 | 多半是旧的失效凭证还在，或者有别的进程在用同一份凭证 | 先清除 `canvas_management` 的旧凭证，再重新授权一次 |
| 503 | 服务端暂时不可用 | 稍后再试；持续出现时联系管理员，不要反复扫码 |
| 403 | 没有这个空间或项目的权限 | 这是正常的权限拒绝，重新扫码也不会增加权限，找有权限的人处理 |
| 404 session | 会话已失效 | 重新连接一次即可，不需要重新扫码 |

## invalid_grant

同一份授权被多个进程同时刷新时，服务端会把旧的刷新凭证判为重复使用，出于安全撤销整组授权。处理方式：

1. 关掉同时在用这个 MCP 的其他客户端（另一个窗口、命令行、IDE 插件、后台任务）。
2. 只清除 `canvas_management` 的授权，再重新授权：
   - Codex：`codex mcp logout canvas_management`，再 `codex mcp login canvas_management`
   - Claude Code：在 `/mcp` 里选 `canvas_management` 清除认证，再重新认证
   - Gemini CLI：`/mcp auth canvas_management`
   - Kimi Code CLI：`kimi mcp auth canvas_management`
   - Cursor、VS Code、Trae、Windsurf、Antigravity、WorkBuddy 等桌面端：在 MCP 设置里找到 `canvas_management`，退出登录或断开后重新连接
3. 用一个客户端重新扫码，确认能看到工具后再打开其他客户端。

## 不要做的事

- 不要让用户把 token、授权码或回调链接贴到对话里。
- 不要一失败就让用户反复扫码；先按上表判断原因。
