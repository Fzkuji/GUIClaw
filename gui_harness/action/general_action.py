"""
gui_harness.action.general_action — general-purpose action executed by the agent.

Unlike GUI actions (click, type, etc.) which are specific operations,
general_action gives the agent a sub-task description and lets it use
any available tools to complete it: shell commands, file I/O, keyboard
shortcuts, web browsing, etc.

The agent runs in interactive mode with full tool access (Bash, Read,
Write, etc.) and reports the result when done.
"""

from __future__ import annotations

from agentic import agentic_function


@agentic_function(summarize={"depth": 0, "siblings": 0})
def general_action(sub_task: str, task_context: str = "", runtime=None) -> dict:
    """Execute a sub-task on a remote Ubuntu VM using any available tools.

    You have full freedom to use any tools and methods:
    - Run shell commands (bash) via the VM's API
    - Read and write files on the VM
    - Install packages
    - Anything else you need

    IMPORTANT constraints:
    - You are operating on a REMOTE Ubuntu VM, NOT on local macOS.
      All commands and file operations must target the VM via its API.
      Do NOT use local macOS commands, local file paths, or local applications.
    - When extracting or copying data (descriptions, names, numbers, text),
      always read directly from source files. Do NOT generate or paraphrase
      content from your own knowledge — copy verbatim from the actual data.
    - When you need data from a website (e.g., IMDB, Wikipedia, etc.), use
      curl with proxy to fetch the actual webpage HTML and parse it with Python.
      Do NOT rely on your own knowledge to generate website content.
    - If curl/requests returns empty content, HTTP error, WAF challenge (202),
      or you cannot get real data, you MUST return success=false.
      NEVER fall back to generating data from your own knowledge.

    Return JSON:
    {
      "success": true/false,
      "output": "what you did and the result",
      "error": null or "error description"
    }
    """
    from gui_harness.utils import parse_json

    if runtime is None:
        raise ValueError("general_action() requires a runtime argument")
    rt = runtime

    # Build data with VM access info
    data_parts = []
    if task_context:
        data_parts.append(task_context)
    data_parts.append(f"Sub-task: {sub_task}")

    try:
        from gui_harness.action import input as _action_input
        vm_url = getattr(_action_input, '_vm_url', None)
        if vm_url:
            data_parts.append(f"""VM API endpoint: {vm_url}
Run commands:  curl -s -X POST {vm_url}/execute -H 'Content-Type: application/json' -d '{{"command": "YOUR_COMMAND", "shell": true}}'
Read files:    curl -s -X POST {vm_url}/execute -H 'Content-Type: application/json' -d '{{"command": "cat /path/to/file", "shell": true}}'
Fetch web via proxy: curl -s --proxy http://172.16.82.1:6152 'URL'""")
    except Exception:
        pass

    reply = rt.exec(content=[
        {"type": "text", "text": "\n\n".join(data_parts)},
    ])

    try:
        return parse_json(reply)
    except Exception:
        return {"success": True, "output": reply[:500]}
