"""Claude (Anthropic API) backend — paid, hosted, highest quality.

A single call to `reply()` sends the conversation to Claude, and if Claude
wants to call one or more tools, runs them (via jarvis.tools.dispatch,
through `on_tool_call` so the caller can gate/confirm dangerous ones) and
feeds the results back, looping until Claude produces a final text reply.
"""

from __future__ import annotations

from typing import Callable

import anthropic

from .. import config
from ..llm_common import SYSTEM_PROMPT_TEMPLATE, ToolCallDeclined
from ..tools import TOOL_SCHEMAS, dispatch


def _system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(name=config.ASSISTANT_NAME)


def make_client() -> anthropic.Anthropic:
    config.require_api_key()
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def reply(
    client: anthropic.Anthropic,
    history: list[dict],
    user_text: str,
    on_tool_call: Callable[[str, dict], str] | None = None,
) -> str:
    run_tool = on_tool_call or (lambda name, args: dispatch(name, args))

    messages = [{"role": turn["role"], "content": turn["content"]} for turn in history]
    messages.append({"role": "user", "content": user_text})

    for _ in range(config.MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            system=_system_prompt(),
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                result_text = run_tool(block.name, block.input)
            except ToolCallDeclined:
                result_text = "The user declined to run this action."
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return (
        "I'm stuck in a loop trying to use tools for that — could you rephrase "
        "or break it into a smaller request?"
    )
