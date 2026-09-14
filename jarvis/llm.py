"""Claude client and the tool-use loop.

A single call to `reply()` sends the conversation to Claude, and if Claude
wants to call one or more tools, runs them (via jarvis.tools.dispatch,
through `on_tool_call` so the caller can gate/confirm dangerous ones) and
feeds the results back, looping until Claude produces a final text reply.
"""

from __future__ import annotations

from typing import Callable

import anthropic

from . import config
from .tools import TOOL_SCHEMAS, dispatch

SYSTEM_PROMPT_TEMPLATE = """\
You are {name}, a helpful personal assistant running on the user's own \
computer. You can chat normally, and you can use tools to take real \
actions on their machine (open apps, open URLs, read/list/write files, \
run shell commands).

Guidelines:
- Be concise and conversational; you're often heard out loud, not just read.
- Use a tool whenever it would actually answer the request (e.g. don't guess \
the time or a file's contents — look them up).
- Before running something destructive or hard to undo (deleting/overwriting \
important files, etc.), say what you're about to do; the user will be asked \
to confirm risky actions separately.
- If a tool call fails or is declined, tell the user plainly and suggest an \
alternative instead of retrying blindly.
"""


class ToolCallDeclined(Exception):
    """Raised by an on_tool_call callback to refuse a tool call."""


def _system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(name=config.ASSISTANT_NAME)


def reply(
    client: anthropic.Anthropic,
    messages: list[dict],
    on_tool_call: Callable[[str, dict], str] | None = None,
) -> str:
    """Send `messages` (Anthropic message format) to Claude, resolve any tool
    calls, and return the final assistant text. `messages` is mutated in
    place with the full exchange (including tool_use/tool_result turns) so
    the caller's conversation history stays in sync.

    `on_tool_call(name, input) -> str` runs a tool call and returns its
    result text. If omitted, tools run directly via jarvis.tools.dispatch.
    Raise ToolCallDeclined from it to record a tool call as refused.
    """
    run_tool = on_tool_call or (lambda name, args: dispatch(name, args))

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


def make_client() -> anthropic.Anthropic:
    config.require_api_key()
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
