---
name: live-edit
description: 在 Claude 桌面端的内置浏览器里打开未来船票画布，直接在画布上加节点、写文案和提示词、连线、分组、贴便签、生成图片、局部重绘（只改图里的一部分），用户在浏览器面板里实时看到。用户说"打开画布""在画布上做/加/排…""直接在画布里改""把图里的…换成/改成…"时使用。需要能在网页里执行 JavaScript 的浏览器工具（Claude 桌面端内置浏览器，或 Claude in Chrome）。
---

# 在内置浏览器里直接操作画布

画布页面自带一个给 Agent 用的接口 `window.__canvasAgentBridge__`。在浏览器里打开画布后，用浏览器工具执行 JS 调它，效果和用户亲手操作一样：实时同步给协作者，并自动保存。

**前提**：要有能在网页里执行 JS 的浏览器工具。Claude 桌面端用内置浏览器（`preview_start`、`navigate`、`javascript_tool`、`tabs_context`、`computer`），也可以用 Claude in Chrome。都没有时告诉用户这个技能需要 Claude 桌面端，其余需求交给 `canvas`、`progress`、`new-requirement`、`image` 技能（它们走 MCP，不能改画布内容）。

操作身份是内置浏览器里登录的账号，不是 MCP 的授权；协作者会实时看到你的每一步。

## 1. 打开画布

1. 确定画布 ID：用户给的，或用 `canvas_project` 查（见 `canvas` 技能）。不知道也可以先打开再用 `listProjects` 查。
2. 用 `preview_start` 打开 `https://b.goticket.cn/#/infinite-canvas/index?projectId=<画布ID>`（不带 `projectId` 会打开上次的画布）。
3. 地址变成 `#/login` 说明没登录：先用 `tabs_context` 确认浏览器面板是显示状态，再请用户在面板里用微信扫码，然后执行下面这段等登录完成（每次最多等 40 秒；没等到就再执行一次，等了两三轮还没登录就再问用户）：

   ```js
   await new Promise((resolve) => {
     const started = Date.now();
     const t = setInterval(() => {
       if (!location.hash.startsWith('#/login')) { clearInterval(t); resolve({ loggedIn: true, url: location.href }); }
       else if (Date.now() - started > 40000) { clearInterval(t); resolve({ loggedIn: false }); }
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

`javascript_tool` 支持顶层 `await`，最后一个表达式就是返回值；单次调用最多跑约 45 秒，超时会报错，所以所有等待都用 `timeoutMs: 30000` 分段等。每次调用都这样开头：

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
- 做完用 `zoomToFit` 或 `focusViewport` 让用户在面板里看到结果，再用标题和内容总结改了什么。改过已有节点的，说明原来的内容，用户要还原时按原值改回。
