# 未来船票 AI 插件

**canvas（未来船票画布）**：连接画布管理 MCP（`https://gate.goticket.cn/api/mini/mcp`），以你自己的 mark-system 账号查项目和需求进度、提设计需求、生成图片。权限和前端完全一致。首次使用会打开授权页，用 **mark-system 小程序**扫码并在手机上确认。

图文版安装和使用说明：**https://b.goticket.cn/plugins/**（可以直接把这个链接发给同事）。

仓库里只有连接地址和使用说明，没有任何密钥。

## 支持的客户端

| 客户端 | 安装方式 | 带技能 | 状态 |
| --- | --- | --- | --- |
| [Claude Code](#claude-code) | 插件市场 | 是 | 已实测 |
| [Codex](#codex) | 插件市场 | 是 | 已实测 |
| [Cursor](#cursor) | 一键安装 MCP + 技能命令 | 是 | 按官方格式适配，待实测 |
| [VS Code（Copilot）](#vs-code) | 一键安装 MCP / 插件 | 是 | 按官方格式适配，待实测 |
| [Gemini CLI](#gemini-cli) | 扩展 | 是 | 按官方格式适配，待实测 |
| [Antigravity](#antigravity) | 插件 | 是 | 按官方格式适配，待实测 |
| [Kimi Code CLI](#kimi-code-cli) | 插件 | 是 | 按官方格式适配，待实测 |
| [WorkBuddy（国际版、国内版）](#workbuddy) | 插件市场 | 是 | 国际版（WorkBuddy AI 5.8.4）已实测安装；专家形态的连接引导待实测 |
| [Trae（国际版、国内版）](#trae) | 手动添加 MCP + 技能命令 | 是 | 按官方格式适配，待实测 |
| [Windsurf](#windsurf) | 手动添加 MCP + 技能命令 | 是 | 按官方格式适配，待实测 |

几种"技能命令"用的是开源的 [skills](https://github.com/vercel-labs/skills) 工具，需要本机装有 Node.js。它只是把 `skills/` 里的说明文件复制到客户端的技能目录，不会运行任何脚本。

## 安装

### Claude Code

```bash
claude plugin marketplace add isjianjian/goticket-plugins
claude plugin install canvas@goticket
```

也可以在 Claude Code 会话里输入 `/plugin marketplace add isjianjian/goticket-plugins`，再 `/plugin install canvas@goticket`。

装好后重开会话（或运行 `/reload-plugins`），输入 `/mcp`，选择 `plugin:canvas:canvas_management` 完成认证。

### Codex

命令行和 Desktop 通用：

```bash
codex plugin marketplace add isjianjian/goticket-plugins
codex plugin add canvas@goticket
```

安装时会打开授权页。Codex Desktop 也可以在添加市场后重启应用，在插件目录里选择"未来船票"市场安装。

### Cursor

1. 安装 MCP：打开 [一键安装到 Cursor](https://cursor.com/install-mcp?name=canvas_management&config=eyJ1cmwiOiJodHRwczovL2dhdGUuZ290aWNrZXQuY24vYXBpL21pbmkvbWNwIn0%3D)，在 Cursor 里确认安装，然后在 MCP 设置里点 `canvas_management` 的登录按钮。
2. 安装技能：

   ```bash
   npx skills add isjianjian/goticket-plugins -g -a cursor
   ```

新版 Cursor 也可以在 设置 → Plugins 的搜索框里粘贴 `https://github.com/isjianjian/goticket-plugins`，一次装上 MCP 和技能。用了这种方式就不要再做上面两步。

### VS Code

需要 GitHub Copilot 的 Agent 模式。

- **只装 MCP**：打开 [一键安装到 VS Code](https://insiders.vscode.dev/redirect/mcp/install?name=canvas_management&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fgate.goticket.cn%2Fapi%2Fmini%2Fmcp%22%7D)，或运行：

  ```bash
  code --add-mcp '{"name":"canvas_management","type":"http","url":"https://gate.goticket.cn/api/mini/mcp"}'
  ```

- **MCP 和技能一起装**（Agent 插件，预览功能）：命令面板运行 `Chat: Install Plugin From Source`，输入 `https://github.com/isjianjian/goticket-plugins`。

首次调用工具时，VS Code 会提示登录，按提示打开授权页扫码。

### Gemini CLI

```bash
gemini extensions install https://github.com/isjianjian/goticket-plugins
```

启动 `gemini` 后输入 `/mcp auth canvas_management` 完成认证。

### Antigravity

- **Antigravity CLI**：

  ```bash
  agy plugin install https://github.com/isjianjian/goticket-plugins
  ```

- **Antigravity IDE**：把仓库放进全局插件目录，然后重启：

  ```bash
  git clone https://github.com/isjianjian/goticket-plugins ~/.gemini/config/plugins/canvas
  ```

  只想加 MCP 的话：Agent 面板 → MCP Servers → Manage MCP Servers → View raw config，在 `mcpServers` 里加上：

  ```json
  "canvas_management": { "serverUrl": "https://gate.goticket.cn/api/mini/mcp" }
  ```

### Kimi Code CLI

在 Kimi Code CLI 里输入：

```text
/plugins install https://github.com/isjianjian/goticket-plugins
/reload
```

然后在终端运行 `kimi mcp auth canvas_management` 完成认证。

### WorkBuddy

国际版和国内版的插件格式相同。这个插件在 WorkBuddy 里以**专家**形态提供：装上之后在「专家·技能·连接器」里能直接找到「未来船票画布」，召唤它对话就行，不用自己配 MCP。

1. 打开「插件」页 →「添加市场」，填 `https://github.com/isjianjian/goticket-plugins`（也可以填 `isjianjian/goticket-plugins`），然后在市场里安装 `canvas`。
2. 回到「专家·技能·连接器」→「专家」，找到「未来船票画布（画布协作助手）」，点进去开始对话。
3. 第一次对话会弹出「未来船票画布」的连接引导卡，点**连接**打开授权页，用 mark-system 小程序扫码确认。
4. 连好的 MCP 统一出现在**连接器 → 自定义连接器**里，之后不会再重复引导。

> 为什么做成专家形态：WorkBuddy 桌面端只对**专家会话**做 MCP 依赖引导——它读 `plugin.json` 里的 `dependencies.mcpServers`（这里指向 `.mcp.json`）和每个 server 的 `x-workbuddy.auth.type = "oauth"`，据此弹出连接卡并走 OAuth。纯技能型插件（只写 `mcpServers`、没有 `expertType`）能装上，但桌面端不会自动注册其中的 MCP。

用 CodeBuddy Code 命令行的话：

```bash
codebuddy plugin marketplace add isjianjian/goticket-plugins
codebuddy plugin install canvas@goticket
```

国内网络访问 GitHub 不稳定时，可以只手动加 MCP：在 WorkBuddy 的 MCP 设置里添加：

```json
{
  "mcpServers": {
    "canvas_management": { "type": "http", "url": "https://gate.goticket.cn/api/mini/mcp" }
  }
}
```

### Trae

国际版和国内版步骤相同。

1. 添加 MCP：设置 → MCP → 添加 → 手动配置，粘贴：

   ```json
   {
     "mcpServers": {
       "canvas_management": { "url": "https://gate.goticket.cn/api/mini/mcp" }
     }
   }
   ```

2. 安装技能（国际版用 `trae`，国内版用 `trae-cn`）：

   ```bash
   npx skills add isjianjian/goticket-plugins -g -a trae
   npx skills add isjianjian/goticket-plugins -g -a trae-cn
   ```

   也可以在 设置 → 规则和技能 里手动导入 `skills/` 下的各个技能。

### Windsurf

1. 在 `~/.codeium/windsurf/mcp_config.json` 的 `mcpServers` 里加上：

   ```json
   "canvas_management": { "serverUrl": "https://gate.goticket.cn/api/mini/mcp" }
   ```

   保存后在 Cascade 的 MCP 面板里刷新，按提示登录。

2. 安装技能：

   ```bash
   npx skills add isjianjian/goticket-plugins -g -a windsurf
   ```

## 使用

直接用自然语言说就行，比如"看一下我在画布上待处理的需求"。支持技能的客户端也可以直接调用：

| 技能 | Claude Code | Codex | 其他客户端 | 用途 |
| --- | --- | --- | --- | --- |
| 总入口 | `/canvas:canvas` | 输入 `$` 选 `canvas:canvas` | `canvas` | 确认登录和空间、调用规则 |
| 查进度 | `/canvas:progress` | `canvas:progress` | `progress` | 我的待办、我发起的需求、项目需求状态（只读） |
| 提需求 | `/canvas:new-requirement` | `canvas:new-requirement` | `new-requirement` | 在项目里提设计需求，确认后才创建 |
| 生成图片 | `/canvas:image` | `canvas:image` | `image` | 选模型、报价，确认积分后再生成 |
| 登录排障 | `/canvas:login-help` | `canvas:login-help` | `login-help` | 扫码后仍未登录、invalid_grant 等 |
| 直接改画布 | `/canvas:live-edit` | — | — | 仅 Claude 桌面端：在内置浏览器里打开画布，直接加节点、写提示词、连线、生成，实时可见 |

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

# Gemini CLI
gemini extensions update canvas
gemini extensions uninstall canvas

# 用 skills 命令装的技能
npx skills update -g
npx skills remove -g canvas progress new-requirement image login-help
```

Kimi Code CLI 在 `/plugins` 的已安装列表里更新或移除；WorkBuddy 和 Cursor 在各自的插件管理里更新。

## 常见问题

- **WorkBuddy 里插件装上了，但连接器里没有 `canvas_management`**：WorkBuddy 桌面端只对专家会话做 MCP 依赖引导，所以要用**专家**入口（「专家·技能·连接器」→「未来船票画布」）开始对话，才会弹连接卡。直接在普通对话里问画布是不会带出 MCP 的，可以按上面「手动加 MCP」兜底。
- **之前手动加过 `canvas_management`**：装插件前先删掉手动加的那个（例如 `claude mcp remove canvas_management`、`codex mcp remove canvas_management`），否则会看到两套相同的工具。
- **扫码后仍显示未登录、提示 invalid_grant**：多个客户端同时用同一份授权时容易出现。关掉其他客户端，清除 `canvas_management` 的授权后，只用一个客户端重新扫码。详见 `login-help` 技能。
- **Claude Desktop / claude.ai 网页版**：暂不支持。服务端还没有放行 Claude 网页的回调地址。

## 目录结构

插件本身就在仓库根目录，各客户端读各自的清单，共用 `skills/` 和同一个 MCP 地址：

```
.claude-plugin/        Claude Code 插件清单和市场清单
.codex-plugin/         Codex 插件清单（输入框图标、推荐指令）
.agents/plugins/       Codex 市场清单
.cursor-plugin/        Cursor 插件清单和市场清单
.codebuddy-plugin/     WorkBuddy / CodeBuddy 插件清单和市场清单
.kimi-plugin/          Kimi Code CLI 插件清单
gemini-extension.json  Gemini CLI 扩展清单
plugin.json            Antigravity 插件清单
mcp_config.json        Antigravity 的 MCP 配置
.mcp.json              Claude Code、Codex、WorkBuddy 的 MCP 配置
agents/                WorkBuddy 专家形态的 Agent 定义（canvas.md）
avatars/               专家头像
skills/                所有客户端共用的技能
assets/                图标
scripts/version.py     统一查看和修改版本号
```

改了插件内容后运行 `python3 scripts/version.py <新版本号>`，一次改掉所有清单里的版本号，用户才会收到更新。
