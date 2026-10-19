# 未来船票 AI 插件市场

给 Claude Code 和 Codex 用的插件市场。目前有一个插件：

- **canvas（未来船票画布）**：连接画布管理 MCP（`https://gate.goticket.cn/api/mini/mcp`），以你自己的 mark-system 账号查项目和需求进度、提设计需求、生成图片。权限和前端完全一致。

仓库里只有连接地址和使用说明，没有任何密钥。

## 安装

### Claude Code

```bash
claude plugin marketplace add isjianjian/goticket-plugins
claude plugin install canvas@goticket
```

也可以在 Claude Code 会话里输入：

```text
/plugin marketplace add isjianjian/goticket-plugins
/plugin install canvas@goticket
```

装好后重开会话（或运行 `/reload-plugins`），输入 `/mcp`，选择 `plugin:canvas:canvas_management` 完成认证：浏览器会打开授权页，用 **mark-system 小程序**扫码并在手机上确认。

### Codex（命令行和 Desktop 通用）

```bash
codex plugin marketplace add isjianjian/goticket-plugins
codex plugin add canvas@goticket
```

安装时会打开授权页，用 mark-system 小程序扫码确认。Codex Desktop 也可以在添加市场后重启应用，在插件目录里选择"未来船票"市场安装。

## 使用

直接用自然语言说就行，比如"看一下我在画布上待处理的需求"。也可以在输入框里直接调用技能：

| 技能 | Claude Code | Codex | 用途 |
| --- | --- | --- | --- |
| 总入口 | `/canvas:canvas` | 输入 `$` 选 `canvas:canvas` | 确认登录和空间、调用规则 |
| 查进度 | `/canvas:progress` | `canvas:progress` | 我的待办、我发起的需求、项目需求状态（只读） |
| 提需求 | `/canvas:new-requirement` | `canvas:new-requirement` | 在项目里提设计需求，确认后才创建 |
| 生成图片 | `/canvas:image` | `canvas:image` | 选模型、报价，确认积分后再生成 |
| 登录排障 | `/canvas:login-help` | `canvas:login-help` | 扫码后仍未登录、invalid_grant 等 |

会改数据或扣积分的操作（创建、提交、分配、生图等），都会先把要做的事列给你，等你确认后才执行。

## 更新和卸载

```bash
# Claude Code
claude plugin marketplace update goticket
claude plugin update canvas@goticket
claude plugin uninstall canvas@goticket

# Codex
codex plugin marketplace upgrade goticket
codex plugin remove canvas@goticket
```

## 常见问题

- **之前手动加过 `canvas_management`**：装插件前先删掉手动加的那个（`claude mcp remove canvas_management` 或 `codex mcp remove canvas_management`），否则会看到两套相同的工具。
- **扫码后仍显示未登录、提示 invalid_grant**：多个客户端同时用同一份授权时容易出现。关掉其他客户端，清除 `canvas_management` 的授权后，只用一个客户端重新扫码。详见 `/canvas:login-help`。
- **Claude Desktop / claude.ai 网页版**：暂不支持。服务端还没有放行 Claude 网页的回调地址。

## 目录结构

```
.agents/plugins/marketplace.json   Codex 市场清单
.claude-plugin/marketplace.json    Claude Code 市场清单
plugins/canvas/
  .codex-plugin/plugin.json        Codex 插件清单（输入框图标、推荐指令）
  .claude-plugin/plugin.json       Claude Code 插件清单
  .mcp.json                        两边共用的 MCP 配置
  skills/                          两边共用的技能
  assets/                          图标
```

改了插件内容后，记得同时更新两个 `plugin.json` 里的 `version`，用户才会收到更新。
