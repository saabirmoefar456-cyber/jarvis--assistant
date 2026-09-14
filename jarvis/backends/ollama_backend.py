"""Ollama backend — free, fully local, offline. Talks to a local Ollama
server (http://localhost:11434 by default) running an open-source model
you've pulled yourself (e.g. `ollama pull llama3.1`). No API key, no
per-token cost, no internet needed once the model is downloaded.

Trade-off: quality is noticeably below Claude, and tool-calling reliability
depends on the model — pick one that supports tools (llama3.1, qwen2.5,
mistral-nemo, firefunction-v2 all do). See the README's Ollama section.
"""

from __future__ import annotations

from typing import Callable

import requests

from .. import config
from ..llm_common import SYSTEM_PROMPT_TEMPLATE, ToolCallDeclined
from ..tools import TOOL_SCHEMAS, dispatch


def _system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(name=config.ASSISTANT_NAME)


def _to_ollama_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        }
        for tool in TOOL_SCHEMAS
    ]


class OllamaClient:
    def __init__(self, host: str):
        self.host = host.rstrip("/")

    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": config.OLLAMA_MODEL,
                "messages": messages,
                "tools": tools,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()


def make_client() -> OllamaClient:
    return OllamaClient(config.OLLAMA_HOST)


def reply(
    client: OllamaClient,
    history: list[dict],
    user_text: str,
    on_tool_call: Callable[[str, dict], str] | None = None,
) -> str:
    run_tool = on_tool_call or (lambda name, args: dispatch(name, args))

    messages = [{"role": "system", "content": _system_prompt()}]
    messages.extend({"role": turn["role"], "content": turn["content"]} for turn in history)
    messages.append({"role": "user", "content": user_text})

    tools = _to_ollama_tools()

    for _ in range(config.MAX_TOOL_ITERATIONS):
        try:
            data = client.chat(messages, tools)
        except requests.exceptions.ConnectionError as exc:
            return (
                f"I can't reach Ollama at {config.OLLAMA_HOST} — is it installed "
                "and running? See the README's 'Free local model (Ollama)' "
                f"section. (details: {exc})"
            )
        except requests.exceptions.RequestException as exc:
            return f"Ollama request failed: {exc}"

        message = data.get("message", {})
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            return (message.get("content") or "").strip()

        messages.append(message)
        for call in tool_calls:
            function = call.get("function", {})
            name = function.get("name", "")
            args = function.get("arguments", {}) or {}
            try:
                result_text = run_tool(name, args)
            except ToolCallDeclined:
                result_text = "The user declined to run this action."
            messages.append({"role": "tool", "content": result_text})

    return (
        "I'm stuck in a loop trying to use tools for that — could you rephrase "
        "or break it into a smaller request?"
    )
