---
name: gui-setup
description: "First-time setup for GUI Agent on a new Mac — install dependencies, models, configure permissions."
---

# Setup — New Machine

```bash
git clone https://github.com/Fzkuji/GUIClaw.git
cd GUIClaw
bash scripts/setup.sh
```

Installs: cliclick, Python 3.12, PyTorch, ultralytics, OpenCV, GPA-GUI-Detector (40MB → `~/GPA-GUI-Detector/`)

**Accessibility permissions required**: System Settings → Privacy & Security → Accessibility → Add Terminal / OpenClaw

## Scripts

| Script | Purpose |
|--------|---------|
| `agent.py` | **Unified entry point** — all GUI ops go through here |
| `ui_detector.py` | Detection engine (YOLO + OCR + Swift window info) |
| `app_memory.py` | Per-app visual memory (learn/detect/click/verify) |
| `gui_agent.py` | Legacy task executor (send_message, read_messages) |
| `template_match.py` | Template matching utilities |
| `setup.sh` | First-run setup |

All scripts use venv: `source ~/gui-agent-env/bin/activate`

## Models

| Model | Size | Auto-installed | Purpose |
|-------|------|----------------|---------|
| **GPA-GUI-Detector** | 40MB | ✅ `~/GPA-GUI-Detector/model.pt` | UI element detection |
| OmniParser V2 | 1.1GB | ❌ | Alt detection (weaker) |
| GUI-Actor 2B | 4.5GB | ❌ | End-to-end grounding (experimental) |

## Path Conventions

- Venv: `~/gui-agent-env/`
- Model: `~/GPA-GUI-Detector/model.pt`
- Memory: `<skill-dir>/memory/apps/<appname>/`
- All paths use `os.path.expanduser("~")`, NOT hardcoded usernames

## Scene Index (Reference)

| Scene | Location | Goal |
|-------|----------|------|
| **Atomic Actions** | `actions/_actions.yaml` | click, type, paste, detect... |
| **WeChat** | `scenes/wechat/` | Send/read messages |
| **Discord** | `scenes/discord.yaml` | Send/read messages |
| **Telegram** | `scenes/telegram.yaml` | Send/read messages |
| **1Password** | `scenes/1password.yaml` | Retrieve credentials |
| **VPN Reconnect** | `scenes/vpn-reconnect.yaml` | Reconnect GlobalProtect |

Scene files are reference only — not executable.
