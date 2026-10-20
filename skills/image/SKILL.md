---
name: image
description: 用未来船票画布生成图片（会扣当前空间的积分）。用户说"生成一张图""出个图""用画布画…"时使用；先选模型、报价，用户确认积分后才创建任务，再取回结果。
---

# 生成图片

先按 `canvas` 技能确认登录和当前空间。积分从当前空间扣，所以要让用户知道是哪个空间。

## 1. 选模型

调 `canvas_image_models`。用户没指定时，按需求推荐一个，并说明可选的尺寸（如 1K、2K、4K）和质量档位。

## 2. 报价

调 `canvas_image_quote`（`model_code`，以及 `image_size`、`quality`），拿到这次要扣的积分。这一步不扣费。

## 3. 确认

把这些告诉用户并等明确同意：

- 当前空间
- 模型、画幅比例、尺寸、质量
- 提示词（整理后的版本）
- 参考图（如果有）
- 预计扣除的积分

用户没有明确同意，就不要调用生成。

## 4. 创建任务

用户同意后调 `canvas_image_generate`，带上 `model_code`、`prompt`、选好的参数和 `confirm=true`。

- 参考图是公开链接：用 `reference_image_urls`（HTTPS，最多 10 张）。
- 参考图是本地文件或用户贴的图：用 `reference_image_files` 传 base64，推荐 `data:image/png;base64,...` 格式。单张不超过 10 MiB，合计不超过 25 MiB。

## 5. 取结果

任务是异步的。用返回的 `task_id` 调 `canvas_image_result`，没完成时隔一会儿再查（不要连续高频轮询），完成后把图片链接给用户。失败时转述原因，不要自动换参数重试，以免重复扣积分。
