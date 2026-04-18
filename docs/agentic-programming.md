# OpenProgram Integration

> GUI Agent Harness is powered by [OpenProgram](https://github.com/Fzkuji/OpenProgram) — the reference implementation of the **Agentic Programming** paradigm: Python functions with LLM-driven docstrings become autonomous agents.
>
> *Agentic Programming* = the paradigm (decorator + context tree + meta functions).
> *OpenProgram* = the product (the `openprogram` Python package).

## Core Concept

Every LLM-calling function in GUI Agent Harness is an `@agentic_function` (imported from `openprogram`). The docstring is the prompt. The function signature defines the interface. The framework handles context management and provider abstraction.

```python
from openprogram import agentic_function

@agentic_function(summarize={"depth": 0, "siblings": 0})
def plan_next_action(task, img_path, component_info, ..., runtime=None) -> dict:
    """Decide the next action to take toward completing the task.

    You are a GUI automation agent. Choose one action to execute next.
    ...
    """
    reply = runtime.exec(content=[
        {"type": "text", "text": context},
        {"type": "image", "path": img_path},
    ])
    return parse_json(reply)
```

## Function Hierarchy

```
gui_agent()                        ← top-level loop, @agentic_function
    │
    └── gui_step()                 ← one step, @agentic_function (orchestration)
            │
            ├── verify_step()      ← LLM leaf: check previous action result
            ├── plan_next_action() ← LLM leaf: decide next action
            └── general_action()   ← LLM leaf: free-form command execution
```

**Orchestration functions** (`gui_agent`, `gui_step`) coordinate the flow but don't call `runtime.exec()` directly. They call child `@agentic_function`s.

**Leaf functions** (`verify_step`, `plan_next_action`, `general_action`) each call `runtime.exec()` exactly once and return structured data.

## Context Flow

The `summarize` parameter controls what context each function sees:

| Function | `summarize` | What it sees |
|----------|-------------|-------------|
| `gui_agent` | `siblings: -1` | All previous gui_agent calls |
| `gui_step` | `siblings: -1, compress: True` | All previous gui_steps (compressed) |
| `verify_step` | `depth: 0, siblings: 0` | Only its own input (relies on CLI session for history) |
| `plan_next_action` | `depth: 0, siblings: 0` | Only its own input (relies on CLI session for history) |

With Claude Code CLI as the provider, session persistence (`--session-id` + `--continue`) gives the LLM memory across steps without duplicating context.

## LLM Provider

Runtime selection is delegated to OpenProgram. `openprogram.providers.create_runtime()` auto-detects the best available provider:

| Priority | Provider | Cost |
|----------|----------|------|
| 1 | OpenClaw | Subscription |
| 2 | Claude Code CLI | Subscription |
| 3 | Anthropic API | Per token |
| 4 | OpenAI API | Per token |

```python
from openprogram.providers import create_runtime

runtime = create_runtime(provider="auto")                        # auto-detect
runtime = create_runtime(provider="claude-code")                 # force Claude Code
runtime = create_runtime(provider="claude-code", model="opus")   # specific model
```

## Key Files

```
gui_harness/
├── main.py                    # gui_agent() — top-level loop, uses openprogram.providers.create_runtime
├── tasks/
│   └── execute_task.py        # gui_step, verify_step, plan_next_action, _dispatch
├── action/
│   ├── input.py               # Mouse/keyboard (local + VM targets)
│   └── general_action.py      # Free-form LLM action with Bash tools
├── perception/
│   └── screenshot.py          # Screenshot capture
├── planning/
│   ├── component_memory.py    # Template matching + state graph
│   └── learn.py               # First-time component learning
└── adapters/
    └── vm_adapter.py          # Redirect I/O to remote VM
```
