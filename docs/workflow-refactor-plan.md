# Workflow 重构规划

> 创建日期：2026-03-24
> 状态：✅ 已完成（2026-03-24）
> 
> **注意：此文档为历史记录，描述了从像素对比到目标状态分层验证的重构过程。**

## 核心原则

1. **不判断"有没有变化"，只判断"有没有到达目标状态"**
2. **已知优先，未知才用模型** — template match → detect_all → LLM，逐级升级
3. **workflow 是导航图，不是录制宏** — 记录状态转移关系，运行时 BFS 寻路

## 分层验证策略

```
Level 0: Template Match（~0.3s，0 token）
  → 目标状态的 defining_components 在不在屏幕上
  → 成功 → 完成

Level 1: detect_all（~2s，0 token）
  → Level 0 失败，完整检测当前页面
  → 识别到已知状态 → 重新寻路
  → 识别到未知状态 → 升级 Level 2

Level 2: LLM 视觉理解（~5s，有 token 消耗）
  → 截图发给 LLM 判断怎么回事
  → LLM 决策下一步（fallback 到探索模式）
```

## 改动清单

### 1. app_memory.py

**删除**：
- `assess_change()` — 不需要像素对比了

**新增**：
- `quick_template_check(app_dir, component_names, img=None)` — 只匹配指定组件，不做全量检测
- `identify_current_state(states, detected_components, components_data)` — 从 identify_or_create_state 拆出纯识别部分（不创建新状态）
- `load_workflows(app_dir)` / `save_workflows(app_dir, workflows)` — workflows.json 读写

**修改**：
- `record_page_transition()` — 去掉 assess_change 调用

### 2. agent.py

**删除**：
- 旧的 `run_workflow()` — 替换为 execute_workflow

**新增**：
- `execute_workflow(app_name, target_state, domain=None, img_path=None)` — 分层验证的 workflow 执行

```python
def execute_workflow(app_name, target_state, domain=None, img_path=None):
    """执行 workflow：自动寻路到目标状态。

    1. 识别当前状态
    2. find_path 到目标
    3. 逐步执行，每步用最低成本验证：
       - Level 0: template match 目标状态的 defining_components
       - Level 1: detect_all + identify_current_state
       - Level 2: 返回 fallback 让 LLM 接管

    Args:
        app_name: 应用名
        target_state: 目标状态 ID（s_xxxxx）
        domain: 网站域名（browser 场景）
        img_path: 当前截图路径（远程 VM 传入，本机 None 自动截图）

    Returns:
        ("success", state_id) — 到达目标
        ("fallback", current_state_id, step_index, reason) — 需要 LLM 接管
        ("error", message) — 无法执行
    """
```

### 3. workflows.json 格式

存在每个 app/site 目录下（和 meta.json 同级）：

```json
{
  "check_baggage_fee": {
    "target_state": "s_c8e5f3",
    "description": "Navigate to baggage fee calculator",
    "created_at": "2026-03-23 15:30:00",
    "last_run": "2026-03-23 16:00:00",
    "run_count": 3,
    "success_count": 2
  }
}
```

### 4. gui-workflow/SKILL.md

更新为目标状态验证模式，去掉像素对比内容。

## quick_template_check 详细设计

```python
def quick_template_check(app_dir, component_names, img=None):
    """只检查指定组件是否在屏幕上。

    比 match_all_components 快——只匹配需要的几个模板，不遍历整个 profile。

    Args:
        app_dir: app/site 目录路径
        component_names: 要检查的组件名列表
        img: 预加载的截图（None 则自动截图）

    Returns:
        (matched_names, total_names, ratio)
        matched_names: set of matched component names
    """
```

## 执行流程详细

### 自动模式（有已知路径）

```
任务 → 截图 → detect_all → identify_current_state → s_a
  → find_path(s_a, target) → [(click:X, s_b), (click:Y, s_c)]
  → Step 1: click X
    → Level 0: quick_template_check(s_b 的 defining_components)
    → matched 6/8 (75%) > 0.7 → 确认到达 s_b ✅
  → Step 2: click Y
    → Level 0: quick_template_check(s_c 的 defining_components)
    → matched 2/8 (25%) < 0.7 → 升级 Level 1
    → Level 1: detect_all → identify_current_state → s_unknown
    → 不是预期的 s_c → 返回 ("fallback", s_unknown, 1, "Expected s_c")
```

### 探索模式（无路径，LLM 主导）

```
任务 → 截图 → detect_all → identify_current_state → s_a
  → find_path(s_a, target) → None（没路径）
  → LLM 决策：看截图，决定点 Travel_info
  → 点击 → 截图 → detect_all → identify_or_create_state → s_b（新状态）
  → 记录 pending: s_a --click:Travel_info--> s_b
  → LLM 继续决策...
  → 到达目标 → confirm_transitions → 下次有路径了
```
