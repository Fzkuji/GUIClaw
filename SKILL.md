---
name: gui-agent
description: "GUI automation via Agentic Programming. Give it a task, it handles the rest — screenshot, detect, act, verify, all automatic."
---

# GUI Agent

## Usage

```python
from gui_harness.tasks.execute_task import execute_task
from gui_harness.runtime import GUIRuntime

runtime = GUIRuntime()  # auto-detects provider
result = execute_task("Open Firefox and go to google.com", runtime=runtime)
```

Or from CLI:

```bash
python3 {baseDir}/gui_harness/main.py "Open Firefox and go to google.com"
python3 {baseDir}/gui_harness/main.py --vm http://VM_IP:5000 "Click the OK button"
```

## Architecture: Tiered Decision with State Memory

Each step uses a tiered decision process, progressively falling back to more expensive methods:

```
Step: Screenshot → Identify State

Tier 0: Transition Graph Reuse (zero or minimal LLM)
  ├─ Known state + single known transition + no coordinates
  │   → Execute directly (ZERO LLM calls)
  ├─ Known state + single transition + coordinates
  │   → Template match to locate target → execute
  ├─ Known state + multiple transitions
  │   → LLM selects from choices (ONE cheap LLM call)
  └─ Unknown state or no transitions → fall through

Tier 1: Full Planning (Phase 0-5)
  Phase 0: LLM sees screenshot → decides action
    ├─ No coordinates needed → execute directly
    └─ Coordinates needed → Phase 1-5 (locate_target)
  Phase 1: GPA-GUI-Detector + OCR → N components
  Phase 2: Template match saved memory → known components
  Phase 3: LLM finds target in known components (text-only)
  Phase 4: Label unknown components one-by-one (stop when found)
  Phase 5: Cleanup

After every action:
  → Screenshot → Identify new state
  → Record (old_state, action, new_state) to transition graph
```

### Three Layers of Memory

```
┌─────────────────────────────────────────┐
│  Transition Graph (high-level)          │
│  (state, action) → next_state           │
│  Enables workflow reuse across tasks     │
├─────────────────────────────────────────┤
│  State Definitions (mid-level)          │
│  state_id → {component set}             │
│  Identified via Jaccard similarity      │
├─────────────────────────────────────────┤
│  Component Memory (low-level)           │
│  label → template image                 │
│  Matched via cv2.matchTemplate          │
│  Auto-forget after 30 consecutive misses│
└─────────────────────────────────────────┘
```

### Progressive Learning

- **1st run**: Full Tier 1 (LLM plans every step). Records transitions + learns components.
- **2nd run**: Some steps use Tier 0 (known transitions). LLM only needed for unknown parts.
- **Nth run**: Most steps are Tier 0. Only novel situations require LLM.
- **Steady state**: Entire workflow runs via template matching + transition replay. Zero LLM.

## For VMs (OSWorld)

```python
from gui_harness.adapters.vm_adapter import patch_for_vm
patch_for_vm("http://VM_IP:5000")
# Then use execute_task() normally — routes through VM HTTP API
```

## First-Time Setup

```bash
cd {baseDir}
git submodule update --init --recursive          # pull Agentic Programming
pip install -e ./libs/agentic-programming        # install Agentic Programming
pip install -e .                                 # install GUI Agent Harness
```

## Core Rules

- **Coordinates from detection only** — OCR or GPA-GUI-Detector, never guessed
- **Look before you act** — every action justified by what was observed
- **Memory saves automatically** — components, states, and transitions persist
- **Tiered decision** — always try the cheapest method first
