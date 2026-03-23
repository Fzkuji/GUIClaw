# gui-report 设计文档

> 最后更新：2026-03-24

## 核心目的

追踪每个 GUI 任务的性能数据：时间、token 消耗、操作次数。用于：
- 对比不同策略的效率
- 发现性能瓶颈（哪步最慢？哪步 token 最多？）
- Benchmark 结果量化

## 当前状态

✅ **完全自动化**。tracker 在第一次 `detect_all` / `learn_from_screenshot` 时自动启动，所有计数器自动 tick，task 名自动从 app/domain 推断。

## 自动化设计决策

### 为什么自动化？

之前 `start` 和 `report` 需要手动调用，实际上从未被使用过。自动化消除了这个问题：
- tracker 在 `_tracker_auto_tick()` 检测到无 state file 时自动启动
- task 名从 `learn_from_screenshot` 的 `app_name/domain` 自动推断
- `execute_workflow()` 完成时自动打印 `auto_report()` 摘要
- 正式 `report` 命令仍可用于生成完整报告并保存到日志

### auto-tick 集成点

#### app_memory.py
- `_tracker_auto_tick(counter)`: 所有检测/学习函数调用此函数
- `_tracker_auto_start()`: 自动初始化 tracker state (task="auto")
- `_tracker_update_task(name)`: `learn_from_screenshot` 自动更新 task 名
- `quick_template_check()`: 自动 tick `workflow_level0`

#### agent.py
- `_tick(counter)`: 封装 tracker 调用（best-effort）
- `_auto_report()`: 获取摘要字符串
- `execute_workflow()` 内部：
  - Level 0 成功 → tick `workflow_auto_steps`
  - Level 1 检测后 → tick `workflow_level1`
  - Level 1 成功 → tick `workflow_auto_steps`
  - Level 2 fallback → tick `workflow_level2` + `workflow_explore_steps`
  - 完成时打印 `auto_report()` 摘要

### 计数器

| Counter | 自动 | 含义 |
|---------|------|------|
| screenshots | ✅ | 截图次数 |
| clicks | ✅ | 点击次数 |
| learns | ✅ | learn_from_screenshot 调用次数 |
| transitions | ✅ | 状态转移记录次数 |
| ocr_calls | ✅ | OCR 调用次数 |
| detector_calls | ✅ | GPA-GUI-Detector 调用次数 |
| image_calls | ❌ 手动 | LLM 视觉分析次数 |
| workflow_level0 | ✅ | quick_template_check 验证次数 |
| workflow_level1 | ✅ | detect_all 完整验证次数 |
| workflow_level2 | ✅ | fallback to LLM 次数 |
| workflow_auto_steps | ✅ | 自动模式执行的步数 |
| workflow_explore_steps | ✅ | 探索模式（需要 LLM）的步数 |

### Token 追踪

通过读取 OpenClaw 的 sessions.json 获取任务开始和结束时的 token 数，计算差值。

### auto_report() vs report()

| | auto_report() | report() |
|---|---|---|
| 输出 | 返回字符串 | print 到 stdout |
| state file | 不删除（继续运行） | 删除（tracker 结束）|
| 日志 | 不保存 | 保存到 task_history.jsonl |
| 用途 | workflow 中间摘要 | 任务最终报告 |

### 安全性

- 所有 tracker 操作都在 try/except 里，失败静默忽略
- tick_counter 的 JSON 读写用 try/except 保护（不会因并发破坏主流程）
- tracker 是 best-effort — 任何错误不影响 GUI 操作

## 理想流程

```
第一次 detect_all → tracker 自动启动 (task="auto")
learn_from_screenshot → 更新 task 名为 "app_name/domain"
  → 操作中各计数器自动 tick
  → execute_workflow 完成时打印 auto_report
任务结束 → tracker report（可选）
  → 输出完整报告
  → 保存到 logs/task_history.jsonl
  → 清除 state file
```
