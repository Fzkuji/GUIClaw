# OSWorld Thunderbird Domain - GPT-5.5 Run Errors

> 15 tasks | no officially scored tasks yet | started 2026-05-18

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 15 |
| Run so far | 1 |
| Officially scored | 0 |
| Pass (1.0) | 0 |
| Numeric fail (0.0) | 0 |
| Eval error / N/A | 1 |
| Not reached | 14 |
| Score so far | N/A |

**Test environment:** Ubuntu VM at `172.16.105.130`, 1920x1080, `openai-codex/gpt-5.5` via GUI Agent Harness

**Run directory:** `runs/thunderbird_all_20260518_0442`

**Command pattern:**

```bash
.venv/bin/python benchmarks/osworld/run_osworld_task.py <task_index> \
  --domain thunderbird \
  --vm 172.16.105.130 \
  --max-steps 15 \
  --provider openai-codex \
  --model gpt-5.5
```

## Detailed Results

| # | Task ID | Instruction | Score | Steps | Time | Notes |
|---|---------|-------------|-------|-------|------|-------|
| 1 | dfac9ee8 | Remove account `anonym-x2024@outlook.com` | N/A EVAL_ERROR | 15 | 181s | Runner hit immediate model failure then screenshot-read cascade; evaluator setup failed uploading `firefox_decrypt.py` to read-only VM Desktop |
| 2-15 | - | Not reached | - | - | - | Continue from task 2 |

## Error Details

| # | Primary failure | Secondary symptoms | Evaluator result | Log |
|---|-----------------|--------------------|------------------|-----|
| 1 | `plan_next_action()` returned `Agent session failed` on step 1 | Screenshot read cascade on steps 2-15; conclusion got HTTP 400 invalid image | Evaluator setup failed: upload to `/home/user/Desktop/firefox_decrypt.py` returned read-only filesystem; score N/A | `task_1.log` |

## Error Categories

| Category | Affected tasks | Evidence | Notes |
|----------|----------------|----------|-------|
| Opaque model/session failure | 1 | `RuntimeError: Agent session failed` | Triggered immediate execution collapse. |
| Screenshot/read cascade | 1 | `WARNING Image Read Error /tmp/gui_agent_screen.png`; `ValueError: need at least one array to stack` | Started after the first model failure. |
| Invalid image passed to model | 1 | OpenAI HTTP 400: image data is not a valid image | Appeared during conclusion after screenshot read failures. |
| Evaluator setup failure | 1 | Upload failed with status 500: read-only filesystem at `/home/user/Desktop/firefox_decrypt.py` | Separate from runner failure; official score is N/A. |
| HuggingFace asset download instability | 1 | SSL EOF retry while downloading `firefox_decrypt.py` | Download recovered; upload failed afterward. |
| Missing proxy config warning | 1 | `evaluation_examples/settings/proxy/dataimpulse.json` not found | Non-blocking so far. |

## Handoff Notes

- Continue at Thunderbird task 2 in `runs/thunderbird_all_20260518_0442`.
- Official `test_all.json` lists 15 Thunderbird tasks; the older `benchmarks/osworld/thunderbird.md` says 24 and is stale.
- Treat official evaluator score as benchmark truth. Task 1 has no score because evaluator setup failed after runner failure.
- Watch for VM filesystem state. Task 1 evaluator could not upload to `/home/user/Desktop/firefox_decrypt.py` due to a read-only filesystem.
