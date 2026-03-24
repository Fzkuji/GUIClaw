# Memory 重构规划

> 创建日期：2026-03-23
> 状态：✅ 已完成（2026-03-24）
> 
> **注意：此文档为历史记录，描述了从 profile.json 到 4 文件拆分存储的重构过程。**

## 核心原则

1. **Memory 完全自治** — 遗忘、合并、清理全自动，LLM 只调用接口、消费结果
2. **拆分存储** — components / states / transitions 各自独立文件
3. **遗忘基于检测频率** — 每次 detect_all 自动更新活跃度，连续 N 次未匹配 → 删除

## 问题总结

| 问题 | 当前 | 期望 |
|------|------|------|
| 组件只增不减 | `learn_from_screenshot` 只加组件 | 不出现的组件自动遗忘 |
| 状态靠命名区分 | `before_X` / `after_X` 命名 | 状态由包含的组件集合定义 |
| transitions 无限追加 | 每次操作 append | 基于状态去重，相同转移只增加 count |
| profile 无法自动瘦身 | 手动 cleanup | 遗忘机制 + 自动合并 |
| 组件缺少活跃度追踪 | 只有 `learned_at` | 需要 `last_seen`、`seen_count`、`consecutive_misses` |

## 新存储结构

```
memory/apps/chromium/sites/united_com/
├── meta.json              # 全局元数据
├── components.json        # 组件注册表（含活跃度字段）
├── states.json            # 状态定义（由组件集合定义）
├── transitions.json       # 状态转移图（dict，去重）
├── components/            # 组件模板图片
└── pages/                 # 页面截图
```

### meta.json

```json
{
  "app": "chromium",
  "domain": "united.com",
  "detect_count": 47,
  "last_updated": "2026-03-23 15:30:00",
  "img_size": [1920, 1080],
  "forget_threshold": 15
}
```

### components.json

```json
{
  "Travel_info": {
    "type": "text",
    "source": "ocr",
    "rel_x": 661, "rel_y": 188,
    "w": 80, "h": 20,
    "icon_file": "components/Travel_info.png",
    "label": "Travel info",
    "confidence": 0.95,
    "page": "homepage",
    "learned_at": "2026-03-23 02:20:00",
    "last_seen": "2026-03-23 15:30:00",
    "seen_count": 12,
    "consecutive_misses": 0
  }
}
```

### states.json

```json
{
  "s_a3f2c1": {
    "name": "homepage",
    "description": "United Airlines 首页，预订表单和导航栏",
    "defining_components": ["nav_bar", "book_button", "Travel_info", "Miles_toggle"],
    "visible_texts": ["United", "Book", "Travel info", "My trips"],
    "first_seen": "2026-03-23 02:20:00",
    "last_seen": "2026-03-23 15:30:00",
    "visit_count": 5
  }
}
```

### transitions.json

```json
{
  "s_a3f2c1|click:Travel_info|s_b7d4e2": {
    "from_state": "s_a3f2c1",
    "action": "click:Travel_info",
    "to_state": "s_b7d4e2",
    "count": 3,
    "last_used": "2026-03-23 15:30:00",
    "success_rate": 1.0
  }
}
```

## 遗忘机制

每次调用 `learn_from_screenshot()` 或 `match_all_components()` 时自动触发：

1. `detect_all()` → 得到当前页面的组件列表 `detected_set`
2. `meta.detect_count += 1`
3. 遍历 `components.json` 中所有组件：
   - 如果 `name ∈ detected_set` → `last_seen = now`, `seen_count += 1`, `consecutive_misses = 0`
   - 如果 `name ∉ detected_set` → `consecutive_misses += 1`
4. 遗忘检查（只在 `detect_count > forget_threshold` 时触发，避免早期误删）：
   - `consecutive_misses >= forget_threshold` → 删除组件 + 图片文件
   - 清理 `states` 中引用该组件的 `defining_components`
   - 如果某 state 的 `defining_components` 被清空 → 删除该 state
   - 如果 transition 引用了被删除的 state → 删除该 transition

### 匹配判断

- OCR 文本组件：检测到的 text 中 label 完全匹配或模糊匹配 >0.9
- GPA 图标组件：模板匹配 confidence > 0.8
- 坐标容差：位置偏移 <30px 也算匹配

## 状态合并

在 `learn_from_screenshot()` 保存阶段自动触发：

1. 从当前检测到的组件中筛选 `seen_count >= 2` 的稳定组件 → `stable_set`
2. 遍历 `states.json`，计算每个 state 的 `defining_components` 与 `stable_set` 的 Jaccard 相似度
3. 最高相似度 > 0.7 → 匹配到已有状态，更新 `visit_count`
4. 所有 < 0.7 → 创建新状态
5. 合并检查：遍历所有状态对，Jaccard > 0.85 → 合并
   - 保留 `visit_count` 更高的状态
   - 更新 `transitions.json` 中的引用

## Transitions 去重

- Dict 结构，key = `from_state|action|to_state`
- 相同操作只更新 `count` 和 `last_used`
- from/to state 被合并/删除时自动更新引用

## API 接口

LLM 只调用这几个函数，内部全自动：

```python
learn_from_screenshot(img_path, domain, app_name, page_name)
match_all_components(app_name, img, threshold)
record_page_transition(before_img, after_img, click_label, click_pos, domain)
find_path(app_name, from_state, to_state)
```

## 迁移

旧格式（单个 profile.json）自动迁移到新格式：

```python
def migrate_profile_if_needed(app_dir):
    """检测到旧 profile.json → 拆分为 meta/components/states/transitions"""
```

## 实施阶段

| Phase | 内容 | 状态 |
|-------|------|------|
| 1 | 拆分存储 + 迁移兼容 | 🔄 |
| 2 | 组件活跃度 + 遗忘机制 | ⬜ |
| 3 | 状态由组件定义 + 合并 | ⬜ |
| 4 | Transitions 去重 | ⬜ |
| 5 | 更新 SKILL.md + gui-memory 文档 | ⬜ |
