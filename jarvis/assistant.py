"""Ties config + llm + tools + voice together into a conversation loop."""

from __future__ import annotations

from . import config, llm, voice
from .llm import ToolCallDeclined
from .tools import DANGEROUS_TOOLS, dispatch


def _confirm(name: str, args: dict) -> bool:
    print(f"\n[{config.ASSISTANT_NAME} wants to run tool] {name}({args})")
    answer = input("Allow this? [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def _run_tool_with_confirmation(name: str, args: dict) -> str:
    if config.CONFIRM_DANGEROUS_ACTIONS and name in DANGEROUS_TOOLS:
        if not _confirm(name, args):
            raise ToolCallDeclined()
    else:
        print(f"[running tool] {name}({args})")
    return dispatch(name, args)


class Assistant:
    def __init__(self):
        self.client = llm.make_client()
        self.messages: list[dict] = []

    def ask(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})
        return llm.reply(self.client, self.messages, on_tool_call=_run_tool_with_confirmation)

    def run_text_loop(self) -> None:
        print(f"{config.ASSISTANT_NAME} is ready. Type 'exit' to quit.\n")
        while True:
            try:
                user_text = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_text:
                continue
            if user_text.lower() in ("exit", "quit"):
                break
            reply_text = self.ask(user_text)
            print(f"{config.ASSISTANT_NAME}: {reply_text}\n")

    def run_voice_loop(self) -> None:
        print(
            f"{config.ASSISTANT_NAME} is ready (voice mode).\n"
            "Press Enter, then speak. Say 'exit' or 'quit' to stop.\n"
        )
        while True:
            try:
                input("Press Enter to talk...")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            try:
                user_text = voice.listen()
            except Exception as exc:  # noqa: BLE001 - keep the loop alive on any STT hiccup
                print(f"(didn't catch that: {exc})")
                continue
            print(f"You said: {user_text}")
            if user_text.strip().lower() in ("exit", "quit"):
                break
            reply_text = self.ask(user_text)
            print(f"{config.ASSISTANT_NAME}: {reply_text}\n")
            voice.speak(reply_text)
