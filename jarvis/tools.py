"""The tools (actions) the assistant is allowed to take on your machine.

Each tool has:
  - a JSON schema entry in TOOL_SCHEMAS, describing it to Claude
  - a Python function in TOOL_IMPL that actually performs it

To add a new tool: add both, following the existing pattern.

Tools marked DANGEROUS_TOOLS write to disk or execute commands, and are
gated behind a confirmation prompt (see jarvis/assistant.py) when
CONFIRM_DANGEROUS_ACTIONS is enabled.
"""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

# Tool names that assistant.py should ask the user to confirm before running.
DANGEROUS_TOOLS = {"write_text_file", "run_shell_command"}

SHELL_COMMAND_TIMEOUT_SECONDS = 30
MAX_FILE_READ_BYTES = 200_000  # don't dump huge files into the conversation


def get_current_datetime(_args: dict) -> str:
    now = _dt.datetime.now()
    return now.strftime("%A, %d %B %Y, %I:%M %p")


def list_directory(args: dict) -> str:
    path = Path(args.get("path") or ".").expanduser()
    if not path.exists():
        return f"Error: path does not exist: {path}"
    if not path.is_dir():
        return f"Error: not a directory: {path}"
    entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    lines = []
    for entry in entries:
        kind = "dir" if entry.is_dir() else "file"
        lines.append(f"[{kind}] {entry.name}")
    return "\n".join(lines) if lines else "(empty directory)"


def read_text_file(args: dict) -> str:
    path = Path(args["path"]).expanduser()
    if not path.exists():
        return f"Error: file does not exist: {path}"
    if not path.is_file():
        return f"Error: not a file: {path}"
    data = path.read_bytes()
    if len(data) > MAX_FILE_READ_BYTES:
        return (
            f"Error: file is too large to read in full "
            f"({len(data)} bytes, limit {MAX_FILE_READ_BYTES})."
        )
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return "Error: file does not look like a text file (couldn't decode as UTF-8)."


def write_text_file(args: dict) -> str:
    path = Path(args["path"]).expanduser()
    content = args.get("content", "")
    append = bool(args.get("append", False))
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        f.write(content)
    action = "Appended to" if append else "Wrote"
    return f"{action} {path} ({len(content)} characters)."


def open_application(args: dict) -> str:
    name = args["name"]
    try:
        if sys.platform.startswith("win"):
            os.startfile(name)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", name])
        else:
            subprocess.Popen([name])
        return f"Opened {name}."
    except Exception as exc:  # noqa: BLE001 - surface any failure to the model
        return f"Error opening '{name}': {exc}"


def open_url(args: dict) -> str:
    url = args["url"]
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url} in your default browser."


def run_shell_command(args: dict) -> str:
    command = args["command"]
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=SHELL_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {SHELL_COMMAND_TIMEOUT_SECONDS}s."
    output = (result.stdout or "") + (result.stderr or "")
    output = output.strip() or "(no output)"
    if len(output) > 4000:
        output = output[:4000] + "\n... (truncated)"
    return f"Exit code {result.returncode}\n{output}"


TOOL_SCHEMAS = [
    {
        "name": "get_current_datetime",
        "description": "Get the current local date and time on the user's machine.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_directory",
        "description": "List the files and subdirectories in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list, e.g. C:\\Users\\me\\Downloads. Defaults to the current directory.",
                }
            },
        },
    },
    {
        "name": "read_text_file",
        "description": "Read the contents of a text file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Full path to the file to read."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_text_file",
        "description": (
            "Write text to a file, creating it (and any missing parent folders) "
            "if needed. Use append=true to add to an existing file instead of "
            "overwriting it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Full path to the file to write."},
                "content": {"type": "string", "description": "Text content to write."},
                "append": {
                    "type": "boolean",
                    "description": "If true, append instead of overwriting. Default false.",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "open_application",
        "description": (
            "Open a desktop application by name, e.g. 'notepad', 'chrome', 'calc'. "
            "On Windows this is the same as running the program's name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Application name or path to launch."}
            },
            "required": ["name"],
        },
    },
    {
        "name": "open_url",
        "description": "Open a URL in the user's default web browser.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "The URL to open."}},
            "required": ["url"],
        },
    },
    {
        "name": "run_shell_command",
        "description": (
            "Run a shell command on the user's machine and return its output. "
            "Use this for things like checking network info, disk space, running "
            "a script, etc. Prefer the more specific tools above when they fit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command line to execute."}
            },
            "required": ["command"],
        },
    },
]

TOOL_IMPL = {
    "get_current_datetime": get_current_datetime,
    "list_directory": list_directory,
    "read_text_file": read_text_file,
    "write_text_file": write_text_file,
    "open_application": open_application,
    "open_url": open_url,
    "run_shell_command": run_shell_command,
}


def dispatch(name: str, args: dict) -> str:
    """Run the tool `name` with `args` and return its text result."""
    impl = TOOL_IMPL.get(name)
    if impl is None:
        return f"Error: unknown tool '{name}'."
    try:
        return impl(args)
    except Exception as exc:  # noqa: BLE001 - never let a tool crash the assistant
        return f"Error running tool '{name}': {exc}"
