---
name: gui-workflow
description: "Save, match, and replay GUI workflows — multi-step task sequences, cross-app meta-workflows, intent matching."
---

# Workflow — Remember and Replay

## Intent Matching (STEP -1)

When you receive a GUI task, BEFORE doing anything:

1. Identify the target app
2. List workflows: `python3 agent.py workflows --app AppName`
3. Match intent to workflow — use semantic understanding, not string matching:
   - "清理电脑" → `smart_scan_cleanup`
   - "看看 Claude 用量" → `check_usage`
4. If matched → load workflow, use steps as plan
5. If no match → proceed normally, save workflow after success

## Saving a Workflow

After completing a multi-step task successfully:

```python
save_workflow("AppName", "workflow_name", [
    {"action": "open", "target": "AppName"},
    {"action": "click", "target": "ButtonName", "note": "context"},
    {"action": "wait_for", "target": "Component", "timeout": 120},
    {"action": "click", "target": "Component"},
], notes=["edge cases here"])
```

- Names: snake_case, descriptive (`smart_scan_cleanup`)
- Description: one-line, **max 30 words**

## Running a Known Workflow

Do NOT blindly replay all steps:

1. Observe current state FIRST
2. Where in the workflow am I now?
3. Skip steps already done
4. Execute ONLY the next needed step
5. After each step: verify state changed
6. State doesn't match → STOP, re-learn

## Meta-Workflows (Cross-App)

Pure orchestration — ONLY `call` steps. No raw actions (`open`, `click`).

```python
save_meta_workflow("task_name", [
    {"action": "call", "app": "Chrome", "workflow": "copy_content",
     "params": {"url": "..."}, "output_as": "$data"},
    {"action": "call", "app": "WeChat", "workflow": "send_message",
     "params": {"contact": "John", "content": "$data"}},
], description="Copy from Chrome, send via WeChat")
```

Rules:
- Every step = `{"action": "call", ...}`
- Each call specifies all params
- `output_as` for inter-step data passing
- Max nesting depth: 5

## Listing

```bash
python3 agent.py workflows --app AppName    # App-specific
python3 agent.py all_workflows              # All app + meta workflows
```
