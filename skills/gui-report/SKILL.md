---
name: gui-report
description: "Track and report performance of GUI agent tasks. Use at the START and END of every gui-agent workflow to measure duration, token consumption, and operation counts. Also use to view historical task data."
---

# GUI Task Report

Track every GUI task: time, tokens, and operations.

## When to Use

- **BEFORE** any gui-agent task: call `start`
- **DURING** the task: call `tick` after each screenshot/click/learn/detect/image call
- **AFTER** the task completes: call `report` with final token counts
- **On demand**: call `history` to review past tasks

## Commands

```bash
TRACKER="python3 ~/.openclaw/workspace/skills/gui-agent/skills/gui-report/scripts/tracker.py"

# 1. Start tracking (get baseline tokens from session_status first)
$TRACKER start --task "CleanMyMac cleanup" --tokens-in 3 --tokens-out 662 --cache-hits 51000

# 2. During task — increment counters as you go
$TRACKER tick screenshots
$TRACKER tick clicks
$TRACKER tick learns
$TRACKER tick image_calls
$TRACKER tick clicks -n 3    # batch increment

# 3. Optional notes
$TRACKER note "Clicked Ignore on quit dialog to protect Discord"

# 4. Final report (get final tokens from session_status)
$TRACKER report --tokens-in 50 --tokens-out 2500 --cache-hits 55000

# 5. View history
$TRACKER history
```

## Token Baseline

Get token counts from `session_status` tool:
- **Before task**: record `Tokens in`, `Tokens out`, and cached tokens
- **After task**: record again, tracker computes the delta

## Output Example

```
============================================================
📊 GUI Task Report: CleanMyMac cleanup
============================================================
⏱  Duration:    3.2min
📥 Tokens in:   2.1k (new) + 4.0k (cached)
📤 Tokens out:  1.8k
📦 Total:       7.9k
🔧 Operations:  5×screenshots, 3×clicks, 1×learns, 5×image_calls
============================================================
```

## Integration with gui-agent

In SKILL.md STEP 6 (Report):
1. `session_status` at task start → `tracker.py start`
2. `tick` inline with each operation
3. `session_status` at task end → `tracker.py report`

## Log Storage

`skills/gui-report/logs/task_history.jsonl` — one JSON per line.
`history` command shows formatted summary.
