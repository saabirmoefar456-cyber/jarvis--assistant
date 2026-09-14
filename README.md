# Jarvis Assistant

A personal, Jarvis-style AI assistant for your own PC. It runs locally on
your laptop, uses Claude as its "brain", and can:

- Chat with you by **text** or **voice** (push-to-talk).
- Run a small set of **automation tools**: open apps, open URLs, list/read/write
  files, and run shell commands — with a confirmation prompt before anything
  that changes or executes something on your machine.

This is the **core** of the assistant. Smart-home control and anything else
you want (a wake word instead of push-to-talk, more tools, a GUI, etc.) can
be added on top once this is running for you.

> This assistant runs **entirely on your own computer**. Nothing about your
> screen, files, or commands is sent anywhere except the text of your
> conversation, which goes to Anthropic's API to generate replies (and tool
> calls) — the same as any Claude chat.

## 1. Requirements

- **Windows 10/11**
- **Python 3.10+** — install from https://www.python.org/downloads/ (check
  "Add python.exe to PATH" during install)
- An **Anthropic API key** — create one at https://console.anthropic.com/settings/keys
- A microphone, only if you want to use voice mode

## 2. Setup (Windows, PowerShell)

```powershell
# 1. Get the code onto your machine (clone the repo, or unzip the files you were sent)
cd jarvis-assistant

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
copy .env.example .env
notepad .env      # paste your ANTHROPIC_API_KEY in here, then save & close
```

If `pip install` fails on `pyaudio` (needed for voice mode), install the
prebuilt wheel instead:

```powershell
pip install pipwin
pipwin install pyaudio
```

(Text mode works fine without `pyaudio` — you only need it for voice mode.)

## 3. Run it

Text mode (type to chat):

```powershell
python main.py --mode text
```

Voice mode (press Enter, then speak; it replies out loud):

```powershell
python main.py --mode voice
```

Type/say `exit` or `quit` to stop.

## 4. What it can do out of the box

Ask it things like:

- "What time is it?"
- "Open Notepad" / "Open Chrome"
- "Open github.com in my browser"
- "List the files in my Downloads folder"
- "Read the file C:\Users\me\notes.txt"
- "Create a file called todo.txt with a grocery list in it"
- "Run `ipconfig` and tell me my IP address"

Anything that **writes a file** or **runs a shell command** will ask you to
confirm (`y`/`n`) in the terminal before it actually does it — this is on by
default so the assistant can't do something on your machine you didn't
intend. You can turn this off in `.env` (`CONFIRM_DANGEROUS_ACTIONS=false`)
once you trust it, but that's not recommended.

## 5. Project layout

```
jarvis-assistant/
├── main.py              # entry point (--mode text|voice)
├── jarvis/
│   ├── config.py         # loads settings from .env
│   ├── llm.py             # Claude client + tool-use loop
│   ├── tools.py           # the automation tools the assistant can call
│   ├── voice.py           # speech-to-text / text-to-speech
│   └── assistant.py       # conversation loop tying it all together
├── requirements.txt
└── .env.example
```

## 6. Configuration (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Your Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-5` | Model used for replies. Use `claude-haiku-4-5-20251001` for a cheaper/faster option. |
| `ASSISTANT_NAME` | `Jarvis` | What it calls itself in its replies |
| `CONFIRM_DANGEROUS_ACTIONS` | `true` | Ask before writing files or running shell commands |

## 7. Extending it (next steps)

This is deliberately a small, readable core so you can grow it:

- **New tools**: add a JSON schema to `TOOL_SCHEMAS` and a matching function
  to `TOOL_IMPL` in `jarvis/tools.py`.
- **Wake word instead of push-to-talk**: swap the `input()` trigger in
  `jarvis/assistant.py`'s voice loop for a wake-word library (e.g. Picovoice
  Porcupine) and call the same `listen()`/`speak()` functions.
- **Smart-home control**: add tools in `jarvis/tools.py` that call your
  smart-home hub's API (Home Assistant, SmartThings, etc.) — same pattern as
  the existing tools.
- **Run it in the background / on startup**: wrap `python main.py --mode
  voice` in a scheduled task or a small tray app once you're happy with it.

## Safety notes

- Tool calls that touch your filesystem or run commands are shown to you and
  require confirmation by default — read them before saying yes.
- Treat your `.env` file (it holds your API key) like a password: don't
  commit it or share it. It's already in `.gitignore`.
- `run_shell_command` runs with your own user permissions and a timeout —
  it is exactly as powerful as typing the command yourself, so only approve
  commands you understand.
