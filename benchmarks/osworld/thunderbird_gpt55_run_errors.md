# OSWorld Thunderbird Domain - GPT-5.5 Run Errors

> 15 tasks | **28.6%** (2/7 officially scored so far) | started 2026-05-18

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 15 |
| Run so far | 8 |
| Officially scored | 7 |
| Pass (1.0) | 2 |
| Numeric fail (0.0) | 5 |
| Eval error / N/A | 1 |
| Not reached | 7 |
| Score so far | 28.6% (2/7) |

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
| 2 | 15c3b339 | Access Outlook account `anonym-x2024@outlook.com` | 0.0 FAIL | 15 | 131s | Same immediate model failure and screenshot-read cascade; evaluator accessibility tree did not find account |
| 3 | 7b1e1ff9 | Open Thunderbird profile management tabpage | 0.0 FAIL | 15 | 556s | Reached Troubleshooting Information but did not open expected About Profiles tab; repeated model session errors |
| 4 | 9bc3cc16 | Back up inbox email files to `~/emails.bak` | 0.0 FAIL | 15 | 156s | Started save/export flow and created folder name, but screenshot cascade prevented completion; evaluator found `/home/user/emails.bak` missing |
| 5 | 3f28fe4f | Set plain text account signature | 1.0 PASS | 7 | 67s | Reached Account Settings signature field and entered two-line signature; evaluator confirmed prefs |
| 6 | 5203d847 | Create local folder `Promotions` and filter matching inbox email subjects | 0.0 FAIL | 15 | 200s | Created local folder and opened filter editor, but did not finish filter rules/actions before step budget; evaluator found only a 25-byte `msgFilterRules.dat` |
| 7 | dd84e895 | Add a star to every email in local `Bills` folder | 0.0 FAIL | 15 | 167s | Starred at least one row, but mis-targeted later star clicks and switched focus to GIMP; screenshot-read cascade stopped the run before all messages were starred |
| 8 | 9b7bc335 | Forward every future email received by `anonym-x2024@outlook.com` | 1.0 PASS | 15 | 226s | Created `Forward all mail` filter, matched all messages, selected forward action, entered `anonym-x2024@gmail.com`, and saved it |
| 9-15 | - | Not reached | - | - | - | Continue from task 9 |

## Error Details

| # | Primary failure | Secondary symptoms | Evaluator result | Log |
|---|-----------------|--------------------|------------------|-----|
| 1 | `plan_next_action()` returned `Agent session failed` on step 1 | Screenshot read cascade on steps 2-15; conclusion got HTTP 400 invalid image | Evaluator setup failed: upload to `/home/user/Desktop/firefox_decrypt.py` returned read-only filesystem; score N/A | `task_1.log` |
| 2 | `plan_next_action()` returned `Agent session failed` on step 1 | Screenshot read cascade on steps 2-15; conclusion had one `Agent session failed` and one HTTP 400 invalid image | Evaluator checked accessibility tree and did not find `anonym-x2024@outlook.com`; score 0.0 | `task_2.log` |
| 3 | About Profiles tab was not opened | Heavy HuggingFace setup retries; repeated `verify_step()` / `plan_next_action()` model errors after opening Troubleshooting Information | Evaluator did not find `page-tab[name="About Profiles"]`; score 0.0 | `task_3.log` |
| 4 | Expected backup directory was missing | One verifier model error; screenshot read cascade on steps 12-15; conclusion got HTTP 400 invalid image | `ls -R /home/user/emails.bak` failed; score 0.0 | `task_4.log` |
| 5 | Early model/session verifier failures | Recovered and typed `Anonym\nXYZ Lab` into the account signature field | PASS; downloaded prefs file matched expected signature | `task_5.log` |
| 6 | Filter creation incomplete | Created `Promotions` local folder and entered filter name; final `plan_next_action()` failed with repeated `Agent session failed` | Evaluator downloaded 25-byte `msgFilterRules.dat`; score 0.0 | `task_6.log` |
| 7 | Not all Bills messages were starred | Mis-targeted star coordinates clicked outside Thunderbird and focused GIMP; steps 9-15 hit screenshot-read cascade; conclusion got HTTP 400 invalid image | Evaluator downloaded `global-messages-db.sqlite`; score 0.0 | `task_7.log` |
| 8 | Early model/session failures but task recovered | First three steps failed with `Agent session failed`; later steps built the filter successfully within step budget | PASS; downloaded 143-byte `msgFilterRules.dat` matched expected forwarding rule | `task_8.log` |

## Error Categories

| Category | Affected tasks | Evidence | Notes |
|----------|----------------|----------|-------|
| Opaque model/session failure | 1, 2, 3, 4, 5, 6, 7, 8 | `RuntimeError: Agent session failed` | Triggered immediate execution collapse on tasks 1-2 and slowed later tasks; some tasks recovered before final scoring. |
| Screenshot/read cascade | 1, 2, 4, 7 | `WARNING Image Read Error /tmp/gui_agent_screen.png`; `ValueError: need at least one array to stack` | Started after model/GUI failure or bad window focus. |
| Invalid image passed to model | 1, 2, 4, 7 | OpenAI HTTP 400: image data is not a valid image | Appeared during conclusion after screenshot read failures. |
| GUI target drift / wrong window focus | 7 | Star-click targets landed outside Thunderbird and focused GIMP | Caused task 7 to lose the active app before the screenshot cascade. |
| Output missing | 4 | Evaluator could not find `/home/user/emails.bak` | Export/backup flow did not complete. |
| Incomplete app configuration | 6 | Evaluator found only a minimal `msgFilterRules.dat` | Local folder was created but message filter rules were not completed. |
| Runner success after early failures | 5, 8 | Official evaluator returned 1.0 despite early model/session errors | Shows early `Agent session failed` is not always fatal when later steps recover. |
| Evaluator setup failure | 1 | Upload failed with status 500: read-only filesystem at `/home/user/Desktop/firefox_decrypt.py` | Separate from runner failure; official score is N/A. |
| HuggingFace asset download instability | 1, 3, 7 | SSL EOF retries while downloading task assets | Downloads recovered after retries/curl fallback where applicable. |
| Missing proxy config warning | 1-8 | `evaluation_examples/settings/proxy/dataimpulse.json` not found | Non-blocking so far. |

## Handoff Notes

- Continue at Thunderbird task 9 in `runs/thunderbird_all_20260518_0442`.
- Official `test_all.json` lists 15 Thunderbird tasks; the older `benchmarks/osworld/thunderbird.md` says 24 and is stale.
- Treat official evaluator score as benchmark truth. Task 1 has no score because evaluator setup failed after runner failure.
- Watch for VM filesystem state. Task 1 evaluator could not upload to `/home/user/Desktop/firefox_decrypt.py` due to a read-only filesystem.
