---
name: canvas
description: 未来船票画布（mark-system）的总入口。用户提到画布、画布项目、设计需求、需求任务、流程节点、空间、画布积分或画布生图时使用；先用它确认登录和空间，再按需交给 new-requirement、progress、image、live-edit 等技能。
---

# 未来船票画布

通过 `canvas_management` MCP 以用户本人的 mark-system 账号操作画布。权限和前端完全一致：用户在前端看不到、改不了的，这里也不行。

## 开始前

1. 调 `canvas_auth_status` 确认已登录、当前空间是哪个。
   - 没登录或工具报 401：告诉用户在客户端里对 `canvas_management` 重新授权（会打开授权页，用 mark-system 小程序扫码确认）。不要反复重试。
2. 用户说的是另一个空间（个人 / 某个组织）时，先 `canvas_list_spaces`，再用 `canvas_switch_space` 切过去，切完向用户说明当前空间。

## 管理类工具怎么调

`canvas_project`、`canvas_requirement`、`canvas_requirement_category`、`canvas_workflow`、`canvas_guide` 只接受固定的 `action`，参数不能猜：

1. `canvas_operations` 传 `domain`（project / requirement / category / workflow / guide），找到要用的 action。
2. `canvas_operation_contract` 传 `domain` 和 `action`，拿到完整参数 schema、示例和前置条件。
3. 按 contract 组装参数再调用。

管理类工具（上面五个，以及 `canvas_operation_contract`）在同一个会话里**一次只能跑一个**：一个调用返回后再发下一个，不要并行，否则会报"Another management request is active"。

常用 action：

| 想做的事 | 工具 | action |
| --- | --- | --- |
| 项目列表 / 详情 | `canvas_project` | `list`、`get`、`get_by_pid` |
| 我的需求任务 | `canvas_requirement` | `my_tasks` |
| 我发起的需求 | `canvas_requirement` | `my_requests` |
| 某个项目的需求 | `canvas_requirement` | `canvas_list` |
| 需求详情、时间线、当前可做的动作 | `canvas_requirement` | `get`、`timeline`、`actions` |
| 新建需求 | `canvas_requirement` | `create` |

## 安全规则（必须遵守）

- **先读后写**：能用查询回答的，不调用写操作。
- **写操作先确认**：创建、更新、分配、提交、完成、取消、删除、切换流程，以及会扣积分的生图，调用前把"要做什么、对哪个项目或需求、关键参数"用一两句话告诉用户，等用户明确同意再调用。
- **危险操作**：contract 标明需要 `confirm=true` 的，只有在用户明确同意后才传 `confirm=true`，绝不默认带上。
- **不要伪造身份**：不要传账号、操作人、空间归属、积分归属这类字段，它们由服务端按当前登录用户和空间决定。
- **不退出登录**：除非用户明确要求，不调用 `canvas_logout`。
- 回答时用项目名、需求标题，不要只给数字 ID；有链接或 projectId 时一并给出。

## 直接改画布内容

这些 MCP 工具管项目和需求，不能在画布上加节点、连线、写提示词。用户想直接在画布上做东西时，按 `live-edit` 技能在内置浏览器里打开画布操作（需要 Claude 桌面端）。只想让用户在浏览器里看到画布时，`canvas_browser_link` 能生成一个免扫码的一次性链接（2 分钟有效、只能用一次、等同登录凭证）：只给当前用户本人点开，提醒尽快打开、不要转发，也不要写进文件。

## 登录问题

遇到 `invalid_grant`、反复要求重新登录、或"已登录但没有工具"，按 `login-help` 技能处理。
