# OSWorld VLC Domain - GPT-5.5 Run Errors

> 17 tasks | **75.0%** (3/4 officially scored so far) | started 2026-05-18

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 17 |
| Run so far | 4 |
| Officially scored | 4 |
| Pass (1.0) | 3 |
| Numeric fail (0.0) | 1 |
| Eval error / N/A | 0 |
| Not reached | 13 |
| Score so far | 75.0% (3/4) |

**Test environment:** Ubuntu VM at `172.16.105.130`, 1920x1080, `openai-codex/gpt-5.5` via GUI Agent Harness

**Run directory:** `runs/vlc_all_20260518_0310`

**Command pattern:**

```bash
.venv/bin/python benchmarks/osworld/run_osworld_task.py <task_index> \
  --domain vlc \
  --vm 172.16.105.130 \
  --max-steps 15 \
  --provider openai-codex \
  --model gpt-5.5
```

## Detailed Results

| # | Task ID | Instruction | Score | Steps | Time | Notes |
|---|---------|-------------|-------|-------|------|-------|
| 1 | 59f21cfb | Play desktop music video in VLC | 1.0 PASS | 6 | 72s | Passed after several early `Agent session failed` planning/verification errors |
| 2 | 8ba5ae7a | Set VLC recordings folder to Desktop | 1.0 PASS | 8 | 150s | Clean GUI path through Preferences > Input/Codecs |
| 3 | 8f080098 | Convert music video song to MP3 | 0.0 FAIL | 15 | 284s | Loaded source video but got stuck around the profile dropdown; evaluator could not find `Baby Justin Bieber.mp3` |
| 4 | bba3381f | Start streaming Apple HLS URL in VLC | 1.0 PASS | 10 | 152s | Recovered from a model/session target lookup failure; evaluator saw VLC playing `master.m3u8` |
| 5-17 | - | Not reached | - | - | - | Continue from task 5 |

## Error Details

| # | Primary failure | Secondary symptoms | Evaluator result | Log |
|---|-----------------|--------------------|------------------|-----|
| 1 | Multiple `plan_next_action()` / `verify_step()` model errors | Recovered by known component match and double-clicked desktop video | PASS; VLC status playing | `task_1.log` |
| 2 | No blocking error observed | Missing proxy config warning only | PASS; `vlcrc` recording path verified | `task_2.log` |
| 3 | Failed to select the MP3 conversion profile and start export | Repeated clicks on/near profile field; no output file created | Missing `/home/user/Desktop/Baby Justin Bieber.mp3`; score 0.0 | `task_3.log` |
| 4 | `find_target_in_known()` returned `Agent session failed` once | First URL open attempt showed an error dialog, then retry succeeded | PASS; VLC status playing and URL filename matched | `task_4.log` |

## Error Categories

| Category | Affected tasks | Evidence | Notes |
|----------|----------------|----------|-------|
| Opaque model/session failure | 1, 4 | `RuntimeError: Agent session failed` | Not fatal in these VLC runs; both tasks recovered and passed. |
| Output missing | 3 | Evaluator could not retrieve expected MP3 file | The runner never reached a completed conversion/export. |
| Profile/dropdown interaction failure | 3 | Repeated attempts to click the VLC Convert profile field | Likely needs stronger VLC-specific memory or direct profile-selection strategy. |
| Missing proxy config warning | 1-4 | `evaluation_examples/settings/proxy/dataimpulse.json` not found | Non-blocking for current VLC tasks. |

## Handoff Notes

- Continue at VLC task 5 in `runs/vlc_all_20260518_0310`.
- Treat official evaluator score as benchmark truth. Task 3 conclusion sounded partially successful, but official score is 0.0 because the MP3 file was missing.
- VLC task count in official `test_all.json` is 17; the older `benchmarks/osworld/vlc.md` says 15 and should not be used as the task count for this GPT-5.5 run.
