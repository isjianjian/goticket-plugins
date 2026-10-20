---
name: live-edit
description: 在浏览器里打开未来船票画布，直接在画布上加节点、写文案和提示词、连线、分组、贴便签、生成图片、局部重绘（只改图里的一部分），用户在画布上实时看到。用户说"打开画布""在画布上做/加/排…""直接在画布里改""把图里的…换成/改成…"时使用。需要能在网页里执行 JavaScript 的浏览器工具：Claude 桌面端用内置浏览器（preview_start + javascript_tool），WorkBuddy / CodeBuddy 用 agent-browser 技能（agent-browser eval）或 playwright-cli 技能（run-code）。
---

# 在浏览器里直接操作画布

画布页面自带一个给 Agent 用的接口 `window.__canvasAgentBridge__`。在浏览器里打开画布后，用浏览器工具执行 JS 调它，效果和用户亲手操作一样：实时同步给协作者，并自动保存。

## 0. 先选执行通道

`window.__canvasAgentBridge__` 只有执行 JS 才碰得到。按客户端选通道：

| 客户端 | 通道 | 打开页面 | 执行 JS |
| --- | --- | --- | --- |
| Claude 桌面端 | 内置浏览器 | `preview_start` / `navigate` | `javascript_tool` |
| Claude in Chrome | 浏览器扩展 | 直接用当前标签页 | `javascript_tool` |
| WorkBuddy / CodeBuddy | `agent-browser` 技能 | `agent-browser open <url>` | `agent-browser eval` |
| WorkBuddy / CodeBuddy（没装 agent-browser） | `playwright-cli` 技能 | `playwright-cli goto <url>` | `playwright-cli run-code` |

**不要因为当前客户端没有 `javascript_tool` 就判定技能不可用**，也不要改成"我写个脚本另开一个浏览器窗口，你能看到，只是不在对话面板里"再让用户降级接受 —— 那是把工具缺失说成了能力边界。WorkBuddy 里 `agent-browser` 和 `playwright-cli` 都是官方技能，能做的事和 Claude 桌面端一样。

WorkBuddy 的「预览面板」（`present_files` 打开网页的那个）确实只能看、不能注入 JS，App 也没开 CDP 端口，所以不要试图驱动它。用 `agent-browser` 起独立 Chromium 窗口即可：画布协作走服务端，用户在任意设备的画布页上都看得到改动实时出现。

`agent-browser` 没装时先装：让用户从「专家·技能·连接器」启用 **agent-browser** 技能（它加载时会自动装 CLI 和 Chromium），或手动 `npm install -g agent-browser && agent-browser install`。装完 `agent-browser --version` 能出版本号才算好。

操作身份是这个浏览器里登录的账号，不是 MCP 的授权；协作者会实时看到你的每一步。

## 1. 打开画布

1. **确定画布 ID**：用户给的，或用 `canvas_project` 查（见 `canvas` 技能）。不指定就打开上次的画布。
2. **拿一次性登录链接**：调 MCP 工具 `canvas_browser_link`（`project_id` 填画布 ID）。打开这个链接会直接以当前用户登录并进入画布，不用扫码，也会沿用 MCP 的当前空间。链接 2 分钟内有效、只能用一次，等同登录凭证：**直接在浏览器里打开，不要贴到回复里，也不要写进文件或发给别人**。
3. **打开链接**：Claude 桌面端用 `preview_start`（已有画布标签页就用 `navigate`）；WorkBuddy 用 `agent-browser open "<链接>"`。页面会自动刷新一次来完成登录。
4. **等画布就绪**：执行这一行，它会等到登录完成、画布加载好、协作连上，最多 40 秒：

   ```js
   await window.__goticketAgent__.openCanvas({ projectId: '342' })
   ```

   - 返回 `ready: true` 就可以开始操作。
   - `needLogin: true`：链接过期或已用过。重新调 `canvas_browser_link` 再打开；MCP 不可用时，先确认浏览器窗口还停在画布页（Claude 用 `tabs_context`，WorkBuddy 用 `agent-browser snapshot`），再请用户在那个窗口里用微信扫码，然后再执行这一行。
   - `timedOut: true`：再执行一次；还不行就看返回里的 `lastError`。
   - 提示"页面跳转，脚本被中断"：那是登录后的自动刷新，再执行一次即可。
5. **换画布**：已经在画布页时，同样执行 `openCanvas({ projectId: '新ID' })`，它会负责切换和等待。

## 2. 怎么调

**Claude 桌面端**：`javascript_tool` 支持顶层 `await`，最后一个表达式就是返回值；单次调用最多跑约 45 秒，超时会报错，所以所有等待都用 `timeoutMs: 30000` 分段等。每次调用都这样开头：

```js
const b = window.__canvasAgentBridge__;
const p = await b.exec({ action: 'ping' });
if (p.projectId !== '342') throw new Error('浏览器里的画布已经换成 ' + p.projectId);
```

**WorkBuddy**：用 `agent-browser eval`。JS 里有中文和多层引号，直接写在命令行会被 shell 吃掉，统一走 base64：

```bash
JS='（把下面的 JS 原样放这里）'
agent-browser eval -b "$(printf '%s' "$JS" | base64 | tr -d '\n')"
```

`eval` 会不会等 Promise 没有文档保证，所以**不要写裸 `await`**，用"先落结果、再回读"两段式，任何实现都跑得通：

```js
// 第一段：发起，结果写进 window.__canvasOut，最后一行立刻返回
window.__canvasOut = { done: false };
(async () => {
  const b = window.__canvasAgentBridge__;
  try { window.__canvasOut = { done: true, value: await b.exec({ action: 'ping' }) }; }
  catch (e) { window.__canvasOut = { done: true, error: String((e && e.message) || e) }; }
})();
'started'
```

```js
// 第二段：回读，没 done 就隔一两秒再来一次
JSON.stringify(window.__canvasOut)
```

`agent-browser` 是持久守护进程，`open` 之后每条 `eval` 都在同一个页面里跑，登录态、画布状态、`__canvasOut` 都在，所以整场只 `open` 一次、结束 `close` 一次。**不要每步都重新 open**，否则登录链接会被浪费掉（只能用一次）。

`playwright-cli run-code` 原生支持 async，可以一步到位：

```bash
playwright-cli run-code "async page => await page.evaluate(async () => {
  const b = window.__canvasAgentBridge__;
  const p = await b.exec({ action: 'ping' });
  if (p.projectId !== '342') throw new Error('浏览器里的画布已经换成 ' + p.projectId);
  return p;
})"
```

用户可能在浏览器里自己切过画布，所以**每次写操作前都核对 `projectId`**。

写操作用下面的写法：每一步单独捕获错误，一步失败不会丢掉前面的结果，返回值也只留 ID：

```js
const out = [];
const run = async (req) => {
  try { const v = await b.exec(req); out.push({ ok: true, action: req.action, id: v && v.id }); return v; }
  catch (e) { out.push({ ok: false, action: req.action, error: (e.code || '') + ' ' + e.message }); return null; }
};
const brief = await run({ action: 'createNode', kind: 'text', x: 0, y: 0, data: { title: '海报需求', content: '…' } });
const poster = await run({ action: 'createNode', kind: 'image', x: 560, y: 0, data: { prompt: '…', model: 'image_hd', aspectRatio: '3:4', imageSize: '1K' } });
if (brief && poster) await run({ action: 'connectNodes', from: brief.id, to: poster.id });
out
```

看画布现状用 `getGraphBrief`，它只返回 ID、位置尺寸、截短的文字和图片网址，不带图片数据：

```js
await b.exec({ action: 'getGraphBrief' })
```

返回 `nodes`（`id`、`type`、`x`、`y`、`w`、`h`，有的话还有 `title`、`text`、`image`、`repaintOf`、`loading`、`error`）、`connections`（`[起点, 终点, 类型, 连线ID]`）、`groups`、`pins`，以及 `idle`（是否空闲）。

## 3. 可用操作

只用下表这些。都是 `await b.exec({ action, ...参数 })`。

| 想做的事 | action | 参数 |
| --- | --- | --- |
| 当前画布、协作状态 | `ping`、`getProject` | — |
| 画布概况（节点数、是否空闲） | `getGraphSummary` | — |
| 全部内容（精简） | `getGraphBrief` | — |
| 单个节点 | `getNode` | `target` |
| 按文字找节点 | `findNodes` | `query`，可选 `type`、`limit`；返回整节点，自己挑字段 |
| 我的画布列表 | `listProjects` | `page`、`pageSize` |
| 新建画布（会自动切过去） | `createProject` | `name`，可选 `description` |
| 切换画布 | `switchProject` | `projectId` |
| 加节点 | `createNode` | `kind`（`text` / `image`）、`x`、`y`、`data` |
| 改内容、位置、尺寸 | `updateNode` | `target`，`data` 或 `x`、`y`、`width`、`height` |
| 移动 | `moveNode` | `target`、`x`、`y` |
| 删节点 | `deleteNode` | `target`（先征得用户同意，见第 7 节） |
| 连线 | `connectNodes` | `from`、`to`，可选 `type`：不传是参考，`fusion` 融合，`repaint` 重绘 |
| 删连线 | `deleteConnection` | `target`（连线 ID） |
| 改提示词 | `setPrompt` | `target`、`prompt` |
| 分组 | `createGroup` | `nodes`（节点 ID 数组）、`title` |
| 便签 | `createTextPin` / `updateTextPin` / `deleteTextPin` | 新建要 `targetType: 'node'`、`target`、`text`；改和删用便签 ID 作 `target` |
| 可选模型和默认参数 | `getGenerationCatalog` | — |
| 生成图片（扣积分） | `generateNode` | `target`，可选 `count`（见第 4 节） |
| 等生成结果 | `waitForGeneration` | `target`、`timeoutMs` |
| 让用户看到某处 / 看全图 | `focusViewport` / `zoomToFit` | `target` / — |
| 清掉选中、编辑状态 | `resetInteractionState` | — |
| 准备局部重绘（不生成） | `prepareRepaint` | 见第 5 节；不要单独调 `setInpaintingSelection`、`repaintRegion` |

节点内容字段：

- 文字节点 `data`：`title`、`content`。
- 图片节点 `data`：`prompt`、`model`（模型编码，如 `image_fast`、`image_hd`）、`aspectRatio`（如 `3:4`）、`imageSize`（`1K` / `2K` / `4K`）、`quality`（只有支持的模型才有）、`count`。生成结果在 `data.url`。
- 提示词里写 `{{text:<文字节点ID>}}`，生成时会替换成那个文字节点的内容。

坐标是画布坐标。新建文字节点默认 360×220，图片节点 1024×1024；横向排列时图片之间留约 1100 的间距，文字放在图片左侧或上方，避免压在一起。

## 4. 生成图片

生成会扣积分，必须先报价、等用户确认：

1. 读页面当前空间（积分从这里扣）：`JSON.parse(localStorage.getItem('mark_current_space') || 'null')`，得到 `spaceType`、`spaceId`、`name`。
2. 用 MCP 报价，一次只调一个工具：`canvas_list_spaces`（同时初始化会话）→ 当前空间不同就 `canvas_switch_space` 切到同一个 → `canvas_image_quote`（`model_code` 用节点的 `model`，`image_size` 用 `imageSize`，有档位再带 `quality`）。报价是单张价格，要乘以 `count`。
3. 告诉用户"将从「空间名」扣 N 积分，生成 X 张"，等明确同意。
4. `generateNode`（`target`），然后用 `waitForGeneration`（`target`、`timeoutMs: 30000`）分段等。超时不会报错，而是返回当前状态；`completed` 为真之前接着等。完成后用 `getNode` 取 `data.url`，有 `data.error` 就如实告诉用户。

## 5. 局部重绘（只改图里的一部分）

用于"把图里的包换成…""给模特戴上项链""去掉背景里的人"这类只改一块的需求。原理：从原图裁出一块正方形，建一个"重绘子节点"单独生成，生成完画布会自动把结果贴回原图。

1. **确认原图**：目标是有图的图片节点（`data.url` 不为空）。
2. **定区域**，二选一：
   - **用户自己框（最准）**：请用户在画布里点那张图，用节点工具栏的"修复"工具框选并确认，画布会自动建好重绘子节点。然后用 `getGraphBrief` 找从原图连出、`type` 为 `repaint` 的那条连线，它指向的就是子节点。对它 `updateNode` 设固定参数（`aspectRatio: '1:1'`、`model: 'image_pro'`、`imageSize: '2K'`），把补充参考图连到它，用 `setPrompt` 写提示词，格式是"基于{{ref:0}}当前局部画面，<要改什么>。参考{{ref:1}}的<借鉴什么>。只修改指定区域，其余保持不变。保持与局部底图一致的光影、材质、清晰度、颗粒与边缘衔接。"，再从第 4 步继续。
   - **你看图估计**：把 `data.url` 下载到临时目录，用 Read 看图，用"占整张图的比例"给出目标区域 `x`、`y`、`w`、`h`（0 到 1）。放大倍数用 1.25；戴在身上的饰品（项链、吊坠、戒指、手链、耳环）用 2.25，并把最小边长设为 800。
3. **建子节点**：调 `prepareRepaint`。它会把区域扩成正方形、建子节点、设固定参数（1:1、`image_pro`、2K）、把补充参考图连到子节点、按标准格式写提示词，**不会生成**：

   ```js
   await b.exec({
     action: 'prepareRepaint',
     target: 'node_xxx',                               // 原图节点 ID
     box: { x: 0.318, y: 0.481, w: 0.131, h: 0.14 },   // 目标区域，占整张图的比例
     preset: 'estimate',                               // 用户给了准确区域用 exact，看图估计用 estimate，饰品用 accessory
     edit: '把草编包换成红色皮革手提包，保持手的姿势和提包方式',
     refs: [],                                         // 补充参考图：[{ target: '图片节点ID', purpose: '借鉴什么' }]
   })
   ```

   返回 `childId`（子节点）、`crop`（裁出那块图的网址；还没上传完时为 `null`，`cropPending` 为真，稍后用 `getGraphBrief` 看）、`parentUrl`（原图当前地址，第 6 步要用）、`prompt`、`square`（像素区域）。`image_pro` 不可用时加 `model: 'image_creative', quality: 'high'`。

4. **检查裁剪**：返回的 `crop` 是裁出来的那块图（`{{ref:0}}`）的网址，下载用 Read 看一眼，确认目标完整在里面、周围留了一点余量。不对就删掉这个子节点（它是你建的），调整 `BOX` 重来。这一步不扣积分。
5. **报价并确认**：按第 4 节报价，模型固定 `image_pro`、尺寸 `2K`，告诉用户从哪个空间扣多少积分，等同意。
6. **生成**：对子节点 `generateNode`，再用 `waitForGeneration`（子节点、`timeoutMs: 30000`）分段等完成。完成后画布会自动把结果贴回原图，用 `waitForNodeOutputPersisted`（`target` 是原图，`previousUrl` 是第 3 步返回的 `parentUrl`，`timeoutMs: 30000`）确认原图已更新，再 `focusViewport` 给用户看。
7. **不满意**：改子节点的提示词后，对同一个子节点再 `generateNode`，不要重新建子节点。

生成前子节点的 `data.url` 就是裁图本身，不代表已经生成过；以 `waitForGeneration` 返回的 `status: 'succeeded'` 为准。

注意：

- 子节点的参数固定为 1:1、`image_pro`、`2K`，不要改。正方形是为了贴回原图时不变形。
- `{{ref:0}}` 永远是裁出来的局部。补充参考图（比如要换成的那件商品）按顺序是 `{{ref:1}}`、`{{ref:2}}`，并且**连到子节点，不要连到原图**。
- 用 Read 看图时，图片可能被缩小显示，所以区域一律用比例表示，不要用像素。
- 读子节点时不要把 `referenceImages` 整个返回：裁图上传前是几十万字符的 `data:` 地址。看子节点用 `getGraphBrief`。

## 6. 必须注意（容易出错）

1. **永远指定节点**：用 `target`（`nodeId` 也可以）。什么都不传时，接口会改到用户当前正在编辑或选中的节点上，可能改错别人的东西。
2. **记住真实 ID**：`createNode` 的返回值里有 `id`，后面都用它。`alias` 只存在页面内存里，刷新或换画布后就失效。ID 丢了就用 `getGraphBrief`、`findNodes` 重新找。
3. **建便签必须带 `targetType`**，否则报 `INVALID_PIN_TARGET`。
4. **文字节点连到图片节点时**，会自动在图片提示词末尾追加 `{{text:<文字节点ID>}}`，不要再手动加一遍。
5. **结果要精简**：看全图用 `getGraphBrief`；`getNode`、`findNodes` 会返回完整节点数据，按需挑字段，别整个返回。
6. **多人协作**：动手前看 `getGraphSummary` 的 `busy.idle`，正在生成或同步时先等一等。只改这次任务相关的节点。
7. **不要用撤销、重做来改正错误**：画布的撤销记录和你的操作不是一一对应的，按快照回退可能连带撤掉更早的改动，甚至撤掉协作者的改动。要还原就做反向操作：改内容前先用 `getNode` 记下原值，需要时改回去；新建错了就删掉自己建的那个。
8. **不要用**：撤销、重做（`undo`、`redo`）；工具栏和编辑态相关的操作（`enterEdit`、`exitEdit`、`activateTool`、`toolbarAction`、涂鸦、裁剪、标记等，局部重绘只走第 5 节的流程）；批量操作 `batch`、`transaction`；整图替换 `replaceGraph`；直接调页面方法的 `callCanvasMethod`、`callNodeMethod`；删除画布 `deleteProject`；提交需求结果（需求流程交给 `new-requirement`、`progress` 技能）。

## 7. 安全规则

- 按用户的要求一次说清要做什么（例如"在画布 342 上加 2 个文字节点和 1 个图片节点并连线"），用户同意后直接做完，不用每一步都问。
- **以下每次都要单独确认**：删除节点、连线或便签；改动不是这次新建的节点；生成图片和局部重绘（扣积分）；新建或切换画布。
- 删除前先说明要删哪些（标题或内容摘要）。一次要删很多节点时分几次删，服务端的删除保护拦下来就停下告诉用户，不要设法绕过。
- 做完用 `zoomToFit` 或 `focusViewport` 让用户在画布上看到结果，再用标题和内容总结改了什么。改过已有节点的，说明原来的内容，用户要还原时按原值改回。
