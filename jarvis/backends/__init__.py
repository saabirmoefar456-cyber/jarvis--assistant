"""LLM backends. Each backend module exposes:

    make_client() -> a client object (whatever `reply` needs)
    reply(client, history, user_text, on_tool_call=None) -> str

`history` is a plain list of {"role": "user"|"assistant", "content": str}
turns from earlier in the conversation (backend-agnostic — no tool-call
detail is persisted across turns, only the visible text). `user_text` is
the newest user message. `reply` resolves any tool calls Claude/the model
makes during this turn (via `on_tool_call`, or jarvis.tools.dispatch if
omitted) and returns the final assistant text for this turn.
"""
