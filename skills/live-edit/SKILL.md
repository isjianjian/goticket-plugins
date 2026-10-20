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
| 局部重绘 | 按第 5 节的流程 | 不要单独调 `setInpaintingSelection`、`repaintRegion` |

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

## 5. 局部重绘（只改图里的一部分）

用于"把图里的包换成…""给模特戴上项链""去掉背景里的人"这类只改一块的需求。原理：从原图裁出一块正方形，建一个"重绘子节点"单独生成，生成完画布会自动把结果贴回原图。

1. **确认原图**：目标是有图的图片节点（`data.url` 不为空）。
2. **定区域**，二选一：
   - **用户自己框（最准）**：请用户在画布里点那张图，用节点工具栏的"修复"工具框选并确认，画布会自动建好重绘子节点。然后用 `getGraph` 找从原图连出、`type` 为 `repaint` 的那条连线，它指向的就是子节点。对它补上第 3 步代码里建子节点之后的部分：`updateNode` 设固定参数、连补充参考图、按同样格式写提示词，再从第 4 步继续。
   - **你看图估计**：把 `data.url` 下载到临时目录，用 Read 看图，用"占整张图的比例"给出目标区域 `x`、`y`、`w`、`h`（0 到 1）。放大倍数用 1.25；戴在身上的饰品（项链、吊坠、戒指、手链、耳环）用 2.25，并把最小边长设为 800。
3. **建子节点**：改好开头的参数后运行下面这段。它会把区域扩成正方形、建子节点、设固定参数、连补充参考图、写提示词，**不会生成**：

   ```js
   // ---- 参数 ----
   const PROJECT = '342';
   const PARENT = 'node_xxx';                             // 原图节点 ID
   const BOX = { x: 0.318, y: 0.481, w: 0.131, h: 0.14 }; // 目标区域，占整张图的比例
   const EXPAND = 1.25;                                   // 用户给了准确区域用 1，看图估计的 1.25，饰品 2.25
   const MIN_SIDE = 0;                                    // 最小边长（像素），饰品 800
   const EDIT = '把草编包换成红色皮革手提包，保持手的姿势和提包方式';
   const REFS = [];                                       // 补充参考图：[{ id: '图片节点ID', purpose: '借鉴什么' }]
   // ---- 流程 ----
   const b = window.__canvasAgentBridge__;
   if ((await b.exec({ action: 'ping' })).projectId !== PROJECT) throw new Error('画布已切换');
   const parent = await b.exec({ action: 'getNode', target: PARENT });
   if (parent.type !== 'image' || !parent.data?.url) throw new Error('目标不是有图的图片节点');
   const { width: W, height: H } = (await b.exec({ action: 'getNodeVisualBasis', target: PARENT })).imageSize;
   const t = { x: BOX.x * W, y: BOX.y * H, w: BOX.w * W, h: BOX.h * H };
   const side = Math.min(Math.max(Math.max(t.w, t.h) * EXPAND, MIN_SIDE), W, H);
   const sx = Math.min(Math.max(t.x + t.w / 2 - side / 2, 0), W - side);
   const sy = Math.min(Math.max(t.y + t.h / 2 - side / 2, 0), H - side);
   const r6 = (v) => Math.round(v * 1e6) / 1e6;
   // 原图要在视野里，页面才会渲染重绘工具；偶尔还没渲染好就等半秒重试
   await b.exec({ action: 'focusViewport', target: PARENT });
   let sel = null;
   try {
     for (let i = 0; i < 5 && !sel; i++) {
       try {
         sel = await b.exec({
           action: 'setInpaintingSelection', target: PARENT, confirm: true, waitForCreation: true,
           rect: { kind: 'rect', space: 'normalized', x: r6(sx / W), y: r6(sy / H), w: r6(side / W), h: r6(side / H) },
           imageSize: { width: W, height: H }, templateImageSize: { width: W, height: H },
           workingSelection: { x: r6(sx), y: r6(sy), w: r6(side), h: r6(side) },
           targetSelection: { x: r6(t.x), y: r6(t.y), w: r6(t.w), h: r6(t.h) },
           targetNormalizedSelection: { kind: 'rect', space: 'normalized', ...BOX },
           selectionWorkflow: 'explicit-rect', contextExpandFactor: EXPAND,
         });
       } catch (e) { if (i === 4) throw e; await new Promise((r) => setTimeout(r, 500)); }
     }
   } finally {
     await b.exec({ action: 'resetInteractionState' });
   }
   const child = sel && (sel.createdRepaintNodeId || sel.repaintNodeId);
   if (!child) throw new Error('没有建出重绘子节点');
   await b.exec({ action: 'updateNode', target: child, data: { aspectRatio: '1:1', model: 'image_pro', imageSize: '2K' } });
   for (const ref of REFS) await b.exec({ action: 'connectNodes', from: ref.id, to: child });
   const prompt = ['基于{{ref:0}}当前局部画面，' + EDIT.replace(/[。.！!]+$/, '') + '。']
     .concat(REFS.map((ref, i) => `参考{{ref:${i + 1}}}的${ref.purpose || '款式与细节'}。`))
     .concat(['只修改指定区域，其余保持不变。', '保持与局部底图一致的光影、材质、清晰度、颗粒与边缘衔接。']).join('');
   await b.exec({ action: 'setPrompt', target: child, prompt });
   // 裁出的图先是页面本地图片（很大的 data: 地址），上传完才变成网址；只返回网址
   const cropUrl = async () => { const r = ((await b.exec({ action: 'getNode', target: child })).data.referenceImages || [])[0]; return typeof r === 'string' ? r : r?.url || ''; };
   let crop = await cropUrl();
   for (let i = 0; i < 30 && !/^https?:/.test(crop); i++) { await new Promise((r) => setTimeout(r, 1000)); crop = await cropUrl(); }
   ({ child, crop: /^https?:/.test(crop) ? crop : '裁图还没上传完，稍后用 getNode 再看', prompt })
   ```

4. **检查裁剪**：返回的 `crop` 是裁出来的那块图（`{{ref:0}}`）的网址，下载用 Read 看一眼，确认目标完整在里面、周围留了一点余量。不对就删掉这个子节点（它是你建的），调整 `BOX` 重来。这一步不扣积分。
5. **报价并确认**：按第 4 节报价，模型固定 `image_pro`、尺寸 `2K`，告诉用户从哪个空间扣多少积分，等同意。
6. **生成**：记下原图当前的 `data.url`，对子节点 `generateNode`，再用 `waitForGeneration`（子节点、`timeoutMs: 60000`）分段等完成。完成后画布会自动把结果贴回原图，用 `waitForNodeOutputPersisted`（`target` 是原图，`previousUrl` 是刚才记下的地址，`timeoutMs: 60000`）确认原图已更新，再 `focusViewport` 给用户看。
7. **不满意**：改子节点的提示词后，对同一个子节点再 `generateNode`，不要重新建子节点。

注意：

- 子节点的参数固定为 1:1、`image_pro`、`2K`，不要改。正方形是为了贴回原图时不变形。`image_pro` 不可用时改用 `image_creative`，并把 `quality` 设为 `high`。
- `{{ref:0}}` 永远是裁出来的局部。补充参考图（比如要换成的那件商品）按顺序是 `{{ref:1}}`、`{{ref:2}}`，并且**连到子节点，不要连到原图**。
- 用 Read 看图时，图片可能被缩小显示，所以区域一律用比例表示，不要用像素。
- 读子节点时不要把 `referenceImages` 整个返回：裁图上传前是几十万字符的 `data:` 地址。

## 6. 必须注意（容易出错）

1. **永远带上 `target`**，指定节点不要用 `nodeId`（会被忽略）。没传 `target` 时，接口会改到用户当前正在编辑或选中的节点上，可能改错别人的东西。
2. **记住真实 ID**：`createNode` 的返回值里有 `id`，后面都用它。`alias` 只存在页面内存里，刷新或换画布后就失效。ID 丢了就用 `getGraph`、`findNodes` 重新找。
3. **建便签必须带 `targetType`**，否则报 `INVALID_PIN_TARGET`。
4. **文字节点连到图片节点时**，会自动在图片提示词末尾追加 `{{text:<文字节点ID>}}`，不要再手动加一遍。
5. **结果要精简**：`getGraph`、`findNodes` 会返回完整节点数据，按需挑字段，别整个返回。
6. **多人协作**：动手前看 `getGraphSummary` 的 `busy.idle`，正在生成或同步时先等一等。只改这次任务相关的节点。
7. **不要用撤销、重做来改正错误**：画布的撤销记录和你的操作不是一一对应的，按快照回退可能连带撤掉更早的改动，甚至撤掉协作者的改动。要还原就做反向操作：改内容前先用 `getNode` 记下原值，需要时改回去；新建错了就删掉自己建的那个。
8. **不要用**：撤销、重做（`undo`、`redo`）；工具栏和编辑态相关的操作（`enterEdit`、`exitEdit`、`activateTool`、`toolbarAction`、涂鸦、裁剪、标记等，局部重绘只走第 5 节的流程）；批量操作 `batch`、`transaction`；整图替换 `replaceGraph`；直接调页面方法的 `callCanvasMethod`、`callNodeMethod`；删除画布 `deleteProject`；提交需求结果（需求流程交给 `new-requirement`、`progress` 技能）。

## 7. 安全规则

- 按用户的要求一次说清要做什么（例如"在画布 342 上加 2 个文字节点和 1 个图片节点并连线"），用户同意后直接做完，不用每一步都问。
- **以下每次都要单独确认**：删除节点、连线或便签；改动不是这次新建的节点；生成图片和局部重绘（扣积分）；新建或切换画布。
- 删除前先说明要删哪些（标题或内容摘要）。一次要删很多节点时分几次删，服务端的删除保护拦下来就停下告诉用户，不要设法绕过。
- 做完用 `zoomToFit` 或 `focusViewport` 让用户在面板里看到结果，再用标题和内容总结改了什么。改过已有节点的，说明原来的内容，用户要还原时按原值改回。
