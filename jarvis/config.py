"""Loads assistant configuration from environment variables / .env."""

import os

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Jarvis")
CONFIRM_DANGEROUS_ACTIONS = _bool(os.getenv("CONFIRM_DANGEROUS_ACTIONS"), True)

# Which LLM answers for the assistant:
#   "ollama"    - free, fully local/offline, needs Ollama installed + a model pulled
#   "anthropic" - Claude via the Anthropic API, paid per token, higher quality
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").strip().lower()

# --- Anthropic (Claude) settings, only used when LLM_BACKEND=anthropic ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

# --- Ollama settings, only used when LLM_BACKEND=ollama ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# Tool-use loop safety valve: max tool round-trips per user turn.
MAX_TOOL_ITERATIONS = 8


def require_api_key() -> None:
    if not ANTHROPIC_API_KEY:
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set.\n"
            "Copy .env.example to .env and add your Anthropic API key, "
            "or set LLM_BACKEND=ollama in .env to run a free local model "
            "instead (see the README's 'Free local model (Ollama)' section)."
        )
