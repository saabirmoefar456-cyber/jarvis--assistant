# Jarvis Assistant

A personal, Jarvis-style AI assistant for your own PC. It runs locally on
your laptop and can:

- Chat with you by **text** or **voice** (push-to-talk).
- Run a small set of **automation tools**: open apps, open URLs, list/read/write
  files, and run shell commands — with a confirmation prompt before anything
  that changes or executes something on your machine.

Its "brain" is swappable between two backends (`LLM_BACKEND` in `.env`):

- **`ollama` (default)** — a free, open-source model running entirely on
  your own machine. No API key, no cost, no internet needed once the model
  is downloaded. Lower quality than Claude; needs Ollama installed. See
  [Free local model (Ollama)](#free-local-model-ollama-no-cost) below.
- **`anthropic`** — Claude via the Anthropic API. Paid per token (cheap —
  see [Anthropic (Claude) setup](#anthropic-claude-setup-paid) below), but
  noticeably more capable.

This is the **core** of the assistant. Smart-home control and anything else
you want (a wake word instead of push-to-talk, more tools, a GUI, etc.) can
be added on top once this is running for you.

> This assistant runs **entirely on your own computer**. With `LLM_BACKEND=ollama`
> nothing ever leaves your machine. With `LLM_BACKEND=anthropic`, the text of
> your conversation (and tool calls) goes to Anthropic's API to generate
> replies — the same as any Claude chat.

## 1. Requirements

- **Windows 10/11**
- **Python 3.10+** — install from https://www.python.org/downloads/ (check
  "Add python.exe to PATH" during install)
- Either **[Ollama](https://ollama.com/download)** (free, local — default) or
  an **Anthropic API key** from https://console.anthropic.com/settings/keys
  (paid, see backend comparison above)
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

# 4. Copy the config template
copy .env.example .env
```

Then set up whichever backend you want (Ollama is the default and needs no
`.env` edits beyond what's below; Anthropic needs an API key pasted in) —
see the two sections right after this one.

If `pip install` fails on `pyaudio` (needed for voice mode), install the
prebuilt wheel instead:

```powershell
pip install pipwin
pipwin install pyaudio
```

(Text mode works fine without `pyaudio` — you only need it for voice mode.)

## Free local model (Ollama, no cost)

This is the default backend (`LLM_BACKEND=ollama` in `.env.example`) — no
signup, no API key, nothing leaves your laptop.

```powershell
# 1. Install Ollama
winget install Ollama.Ollama
# (or download the installer from https://ollama.com/download)

# 2. Pull a model that supports tool calling — llama3.1 is a solid default
#    (~4.7 GB download, wants ~8 GB RAM free to run comfortably)
ollama pull llama3.1

# 3. Ollama runs as a background service after install — check it's up:
ollama list
```

That's it — `python main.py --mode text` will now talk to your local model.
If `.env` doesn't already say so, make sure it has:

```
LLM_BACKEND=ollama
OLLAMA_MODEL=llama3.1
```

Want a different local model? Any Ollama model that supports tools works —
`qwen2.5`, `mistral-nemo`, and `firefunction-v2` are other good options; just
`ollama pull <name>` and set `OLLAMA_MODEL=<name>` in `.env`. A model
**without** tool-calling support will still chat, but can't use any of the
automation tools (it'll just say it can't help with those).

## Anthropic (Claude) setup (paid)

Higher quality, costs a small amount per use (see pricing note below).

```powershell
notepad .env
```

Set:

```
LLM_BACKEND=anthropic
ANTHROPIC_API_KEY=sk-ant-...   # from https://console.anthropic.com/settings/keys
```

There's no permanent free tier for the API itself — it's pay-per-token, with
at most a small trial credit for new accounts. In practice it's inexpensive
for personal use: the cheapest current model (`claude-haiku-4-5`, set via
`CLAUDE_MODEL` in `.env`) is $1 / $5 per million input/output tokens — a
chatty day of use is typically well under $1. `claude-sonnet-5` (the
default) costs more but is noticeably better at following complex requests
and using tools correctly.

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
│   ├── config.py          # loads settings from .env
│   ├── llm.py             # picks a backend based on LLM_BACKEND, dispatches to it
│   ├── llm_common.py       # system prompt + shared exception used by both backends
│   ├── backends/
│   │   ├── anthropic_backend.py  # Claude client + tool-use loop
│   │   └── ollama_backend.py     # local Ollama client + tool-use loop
│   ├── tools.py           # the automation tools the assistant can call
│   ├── voice.py           # speech-to-text / text-to-speech
│   └── assistant.py       # conversation loop tying it all together
├── requirements.txt
└── .env.example
```

## 6. Configuration (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `LLM_BACKEND` | `ollama` | `ollama` (free, local) or `anthropic` (paid, Claude) |
| `OLLAMA_HOST` | `http://localhost:11434` | Where your local Ollama server is running |
| `OLLAMA_MODEL` | `llama3.1` | Which pulled Ollama model to use |
| `ANTHROPIC_API_KEY` | *(required if `LLM_BACKEND=anthropic`)* | Your Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-5` | Model used for replies when on the Anthropic backend. Use `claude-haiku-4-5` for a cheaper/faster option. |
| `ASSISTANT_NAME` | `Jarvis` | What it calls itself in its replies |
| `CONFIRM_DANGEROUS_ACTIONS` | `true` | Ask before writing files or running shell commands |

## 7. Extending it (next steps)

This is deliberately a small, readable core so you can grow it:

- **New tools**: add a JSON schema to `TOOL_SCHEMAS` and a matching function
  to `TOOL_IMPL` in `jarvis/tools.py` — both backends pick it up automatically.
- **Wake word instead of push-to-talk**: swap the `input()` trigger in
  `jarvis/assistant.py`'s voice loop for a wake-word library (e.g. Picovoice
  Porcupine) and call the same `listen()`/`speak()` functions.
- **Smart-home control**: add tools in `jarvis/tools.py` that call your
  smart-home hub's API (Home Assistant, SmartThings, etc.) — same pattern as
  the existing tools.
- **Another LLM backend**: add a new module under `jarvis/backends/` with the
  same `make_client()` / `reply()` shape and register it in `jarvis/llm.py`'s
  `_BACKENDS` dict.
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
