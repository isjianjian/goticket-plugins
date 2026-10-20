---
name: live-edit
description: 在 Claude 桌面端的内置浏览器里打开未来船票画布，直接在画布上加节点、写文案和提示词、连线、分组、贴便签、生成图片，用户在浏览器面板里实时看到。用户说"打开画布""在画布上做/加/排…""直接在画布里改"时使用。需要能在网页里执行 JavaScript 的浏览器工具（Claude 桌面端内置浏览器，或 Claude in Chrome）。
---

# 在内置浏览器里直接操作画布

画布页面自带一个给 Agent 用的接口 `window.__canvasAgentBridge__`。在浏览器里打开画布后，用浏览器工具执行 JS 调它，效果和用户亲手操作一样：实时同步给协作者，并自动保存。

**前提**：要有能在网页里执行 JS 的浏览器工具。Claude 桌面端用内置浏览器（`preview_start`、`navigate`、`javascript_tool`、`tabs_context`、`computer`），也可以用 Claude in Chrome。都没有时告诉用户这个技能需要 Claude 桌面端，其余需求交给 `canvas`、`progress`、`new-requirement`、`image` 技能（它们走 MCP，不能改画布内容）。

操作身份是内置浏览器里登录的账号，不是 MCP 的授权；协作者会实时看到你的每一步。

## 1. 打开画布

1. 确定画布 ID：用户给的，或用 `canvas_project` 查（见 `canvas` 技能）。不知道也可以先打开再用 `listProjects` 查。
2. 用 `preview_start` 打开 `https://b.goticket.cn/#/infinite-canvas/index?projectId=<画布ID>`（不带 `projectId` 会打开上次的画布）。
3. 地址变成 `#/login` 说明没登录：先用 `tabs_context` 确认浏览器面板是显示状态，再请用户在面板里用微信扫码，然后执行下面这段等登录完成（最多等 100 秒，没等到就再问用户）：

   ```js
   await new Promise((resolve) => {
     const started = Date.now();
     const t = setInterval(() => {
       if (!location.hash.startsWith('#/login')) { clearInterval(t); resolve({ loggedIn: true, url: location.href }); }
       else if (Date.now() - started > 100000) { clearInterval(t); resolve({ loggedIn: false }); }
     }, 1000);
   })
   ```

4. 等接口就绪、协作连上、并且确实是目标画布：

   ```js
   const want = '342'; // 目标画布 ID
   await new Promise((resolve) => {
     const started = Date.now();
     const tick = async () => {
       const b = window.__canvasAgentBridge__;
       try {
         if (b && b.isReady()) {
           const p = await b.exec({ action: 'ping' });
           if (p.collaborationStatus === 'connected' && (!want || p.projectId === want)) return resolve(p);
         }
       } catch (e) {}
       if (Date.now() - started > 30000) return resolve({ timeout: true, url: location.href });
       setTimeout(tick, 500);
     };
     tick();
   })
   ```

5. 换画布用 `switchProject`（`{ action: 'switchProject', projectId }`），再执行第 4 步。不要靠 `navigate` 到同一个地址，hash 地址相同时页面不会刷新。

## 2. 怎么调

`javascript_tool` 支持顶层 `await`，最后一个表达式就是返回值。每次调用都这样开头：

```js
const b = window.__canvasAgentBridge__;
const p = await b.exec({ action: 'ping' });
if (p.projectId !== '342') throw new Error('浏览器里的画布已经换成 ' + p.projectId);
```

用户可能在面板里自己切过画布，所以**每次写操作前都核对 `projectId`**。

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

看画布现状用这段，只返回要用的字段（`getGraph` 原始结果很大）：

```js
const g = await b.exec({ action: 'getGraph' });
({
  nodes: g.nodes.map(n => ({ id: n.id, type: n.type, x: n.x, y: n.y, w: n.width, h: n.height, title: n.data?.title, text: (n.data?.content || n.data?.prompt || '').slice(0, 60), image: n.data?.url || null })),
  connections: g.connections.map(c => [c.fromNode, c.toNode, c.type || 'reference']),
  groups: g.groups.map(x => ({ id: x.id, title: x.title, members: x.memberNodeIds })),
  pins: g.textPins.map(x => ({ id: x.id, text: x.text, on: x.targetId })),
})
```

## 3. 可用操作

只用下表这些。都是 `await b.exec({ action, ...参数 })`。

| 想做的事 | action | 参数 |
| --- | --- | --- |
| 当前画布、协作状态 | `ping`、`getProject` | — |
| 画布概况（节点数、是否空闲） | `getGraphSummary` | — |
| 全部内容 | `getGraph` | 按上面的方式精简后再返回 |
| 单个节点 | `getNode` | `target` |
| 按文字找节点 | `findNodes` | `query`，可选 `type`、`limit`；返回整节点，自己挑字段 |
| 我的画布列表 | `listProjects` | `page`、`pageSize` |
| 新建画布（会自动切过去） | `createProject` | `name`，可选 `description` |
| 切换画布 | `switchProject` | `projectId` |
| 加节点 | `createNode` | `kind`（`text` / `image`）、`x`、`y`、`data` |
| 改内容、位置、尺寸 | `updateNode` | `target`，`data` 或 `x`、`y`、`width`、`height` |
| 移动 | `moveNode` | `target`、`x`、`y` |
| 删节点 | `deleteNode` | `target`（先征得用户同意，见第 6 节） |
| 连线 | `connectNodes` | `from`、`to`，可选 `type`：不传是参考，`fusion` 融合，`repaint` 重绘 |
| 删连线 | `deleteConnection` | `target`（连线 ID） |
| 改提示词 | `setPrompt` | `target`、`prompt` |
| 分组 | `createGroup` | `nodes`（节点 ID 数组）、`title` |
| 便签 | `createTextPin` / `updateTextPin` / `deleteTextPin` | 新建要 `targetType: 'node'`、`target`、`text`；改和删用便签 ID 作 `target` |
| 可选模型和默认参数 | `getGenerationCatalog` | — |
| 生成图片（扣积分） | `generateNode` | `target`，可选 `count`（见第 4 节） |
| 等生成结果 | `waitForGeneration` | `target`、`timeoutMs` |
| 让用户看到某处 / 看全图 | `focusViewport` / `zoomToFit` | `target` / — |

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
4. `generateNode`（`target`），然后用 `waitForGeneration`（`target`、`timeoutMs: 60000`）分段等。超时不会报错，而是返回当前状态；`completed` 为真之前接着等。完成后用 `getNode` 取 `data.url`，有 `data.error` 就如实告诉用户。

## 5. 必须注意（容易出错）

1. **永远带上 `target`**，指定节点不要用 `nodeId`（会被忽略）。没传 `target` 时，接口会改到用户当前正在编辑或选中的节点上，可能改错别人的东西。
2. **记住真实 ID**：`createNode` 的返回值里有 `id`，后面都用它。`alias` 只存在页面内存里，刷新或换画布后就失效。ID 丢了就用 `getGraph`、`findNodes` 重新找。
3. **建便签必须带 `targetType`**，否则报 `INVALID_PIN_TARGET`。
4. **文字节点连到图片节点时**，会自动在图片提示词末尾追加 `{{text:<文字节点ID>}}`，不要再手动加一遍。
5. **结果要精简**：`getGraph`、`findNodes` 会返回完整节点数据，按需挑字段，别整个返回。
6. **多人协作**：动手前看 `getGraphSummary` 的 `busy.idle`，正在生成或同步时先等一等。只改这次任务相关的节点。
7. **不要用撤销、重做来改正错误**：画布的撤销记录和你的操作不是一一对应的，按快照回退可能连带撤掉更早的改动，甚至撤掉协作者的改动。要还原就做反向操作：改内容前先用 `getNode` 记下原值，需要时改回去；新建错了就删掉自己建的那个。
8. **不要用**：撤销、重做（`undo`、`redo`）；工具栏和编辑态相关的操作（`enterEdit`、`exitEdit`、`activateTool`、`toolbarAction`、涂鸦、裁剪、标记等）；批量操作 `batch`、`transaction`；整图替换 `replaceGraph`；直接调页面方法的 `callCanvasMethod`、`callNodeMethod`；删除画布 `deleteProject`；提交需求结果（需求流程交给 `new-requirement`、`progress` 技能）。

## 6. 安全规则

- 按用户的要求一次说清要做什么（例如"在画布 342 上加 2 个文字节点和 1 个图片节点并连线"），用户同意后直接做完，不用每一步都问。
- **以下每次都要单独确认**：删除节点、连线或便签；改动不是这次新建的节点；生成图片（扣积分）；新建或切换画布。
- 删除前先说明要删哪些（标题或内容摘要）。一次要删很多节点时分几次删，服务端的删除保护拦下来就停下告诉用户，不要设法绕过。
- 做完用 `zoomToFit` 或 `focusViewport` 让用户在面板里看到结果，再用标题和内容总结改了什么。改过已有节点的，说明原来的内容，用户要还原时按原值改回。
