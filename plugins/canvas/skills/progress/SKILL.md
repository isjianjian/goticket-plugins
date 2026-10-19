---
name: progress
description: 查未来船票画布上的进度：我待处理的需求任务、我发起的需求到哪一步了、某个项目下所有需求的状态。用户问"我有什么要做的""需求进度""项目进展"时使用。只读，不会修改任何数据。
---

# 查进度

先按 `canvas` 技能确认登录和空间。这个技能只做查询，不调用任何写操作。

## 看用户想查哪一种

| 用户在问 | 调用 |
| --- | --- |
| 我要处理的、我的待办 | `canvas_requirement`，`action=my_tasks` |
| 我提的需求、我发起的 | `canvas_requirement`，`action=my_requests` |
| 某个项目的需求 | 先 `canvas_project` 的 `list` 或 `get_by_pid` 找到项目，再 `canvas_requirement`，`action=canvas_list` |
| 某一条需求的细节 | `canvas_requirement` 的 `get`，需要时加 `timeline`（经过了哪些步骤）和 `actions`（现在能做什么） |
| 有没有新通知 | `canvas_requirement`，`action=notice_summary` |

参数以 `canvas_operation_contract` 返回的为准，分页参数没给时用默认第一页。

## 怎么回答

- 按状态分组汇总：待处理、进行中、待确认、已完成等，每组给数量，再列重点条目（标题、项目、当前节点、截止时间、处理人）。
- 先说最需要用户动手的：快到期、退回修改、等用户确认的。
- 条目很多时只列前 10 条，并说明总数和怎么继续看。
- 不要替用户执行"已读""领取""开始处理"之类的动作；用户要做时，按 `canvas` 技能的写操作规则先确认。
