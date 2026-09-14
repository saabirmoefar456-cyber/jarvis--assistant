"""Picks the LLM backend (see jarvis/backends/) based on config.LLM_BACKEND
and exposes one interface regardless of which is active:

    make_client() -> a client object
    reply(client, history, user_text, on_tool_call=None) -> str

This is the only module the rest of the app (jarvis/assistant.py) talks to —
it doesn't know or care whether Claude or a local Ollama model is answering.
"""

from __future__ import annotations

from typing import Callable

from . import config
from .backends import anthropic_backend, ollama_backend
from .llm_common import ToolCallDeclined

__all__ = ["make_client", "reply", "ToolCallDeclined"]

_BACKENDS = {
    "anthropic": anthropic_backend,
    "ollama": ollama_backend,
}


def _backend():
    name = config.LLM_BACKEND
    if name not in _BACKENDS:
        raise SystemExit(
            f"Unknown LLM_BACKEND '{name}' in .env — use 'anthropic' or 'ollama'."
        )
    return _BACKENDS[name]


def make_client():
    return _backend().make_client()


def reply(
    client,
    history: list[dict],
    user_text: str,
    on_tool_call: Callable[[str, dict], str] | None = None,
) -> str:
    return _backend().reply(client, history, user_text, on_tool_call=on_tool_call)
