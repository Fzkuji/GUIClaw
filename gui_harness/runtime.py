"""
gui_harness.runtime — GUIRuntime: routes LLM calls through OpenClaw gateway.

OpenClaw agent IS the runtime. It accumulates context in its own session,
so each @agentic_function only sends its own content (no Context tree injection).

This is configured via summarize={"depth": 0, "siblings": 0} on each
@agentic_function decorator.

Usage:
    from gui_harness.runtime import GUIRuntime

    runtime = GUIRuntime()  # uses localhost:18789 by default

    @agentic_function(summarize={"depth": 0, "siblings": 0})
    def observe(task):
        return runtime.exec(content=[
            {"type": "text", "text": f"Find: {task}"},
            {"type": "image", "path": "/tmp/screenshot.png"},
        ])
"""

from __future__ import annotations

import base64
import mimetypes
import os
from typing import Optional

from agentic.runtime import Runtime

GUI_SYSTEM_PROMPT = """\
You are a GUI automation agent.

Your role:
- Analyze screenshots, OCR results, and detected UI elements
- Identify target elements and their exact pixel coordinates
- Decide the best actions to achieve the given task
- Return structured JSON responses as requested

Rules:
- ALWAYS use coordinates from OCR/detector output — never estimate from visual inspection
- Be precise: wrong coordinates break automation
- Report exactly what you see; do not hallucinate UI elements
"""


class GUIRuntime(Runtime):
    """
    Routes LLM calls through OpenClaw gateway (/v1/chat/completions).

    OpenClaw agent accumulates context in its own session, so we use
    summarize={"depth": 0, "siblings": 0} on @agentic_function decorators
    to skip Context tree injection. Each exec() call sends only its own
    content blocks.

    Args:
        gateway_url:  OpenClaw gateway URL (default: http://localhost:18789).
        auth_token:   Gateway auth token (or OPENCLAW_GATEWAY_TOKEN env var).
        model:        Model name (default: anthropic/claude-sonnet-4-6).
        system:       System prompt.
        max_tokens:   Max response tokens.
        timeout:      Request timeout in seconds.
    """

    def __init__(
        self,
        gateway_url: str = "http://localhost:18789",
        auth_token: str = None,
        model: str = "anthropic/claude-sonnet-4-6",
        system: str = None,
        max_tokens: int = 4096,
        timeout: float = 120.0,
    ):
        super().__init__(model=model)
        self.gateway_url = gateway_url.rstrip("/")
        self.auth_token = auth_token or os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")
        self.system = system or GUI_SYSTEM_PROMPT
        self.max_tokens = max_tokens
        self.timeout = timeout

    def _call(
        self,
        content: list[dict],
        model: str = "default",
        response_format: Optional[dict] = None,
    ) -> str:
        """Send content to OpenClaw gateway."""
        import httpx

        use_model = model if model != "default" else self.model

        # Convert content blocks to OpenAI format
        user_content = []
        for block in content:
            converted = self._convert_block(block)
            if converted:
                user_content.append(converted)

        messages = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": user_content},
        ]

        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        payload = {
            "model": use_model,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        response = httpx.post(
            f"{self.gateway_url}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _convert_block(self, block: dict) -> Optional[dict]:
        """Convert a content block to OpenAI chat format."""
        block_type = block.get("type", "text")

        if block_type == "text":
            return {"type": "text", "text": block["text"]}

        if block_type == "image":
            if "url" in block:
                return {"type": "image_url", "image_url": {"url": block["url"]}}
            if "data" in block:
                mt = block.get("media_type", "image/png")
                return {"type": "image_url", "image_url": {"url": f"data:{mt};base64,{block['data']}"}}
            if "path" in block:
                path = block["path"]
                mt = mimetypes.guess_type(path)[0] or "image/png"
                with open(path, "rb") as f:
                    data = base64.b64encode(f.read()).decode("utf-8")
                return {"type": "image_url", "image_url": {"url": f"data:{mt};base64,{data}"}}

        if "text" in block:
            return {"type": "text", "text": block["text"]}
        return None
