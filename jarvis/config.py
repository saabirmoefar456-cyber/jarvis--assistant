"""Loads assistant configuration from environment variables / .env."""

import os

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Jarvis")
CONFIRM_DANGEROUS_ACTIONS = _bool(os.getenv("CONFIRM_DANGEROUS_ACTIONS"), True)

# Anthropic tool-use loop safety valve: max tool round-trips per user turn.
MAX_TOOL_ITERATIONS = 8


def require_api_key() -> None:
    if not ANTHROPIC_API_KEY:
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set.\n"
            "Copy .env.example to .env and add your Anthropic API key, "
            "then run this again."
        )
