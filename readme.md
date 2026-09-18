# HIAI — Local AI Terminal Coding Agent

> **HIAI** is a local-first AI coding assistant that runs entirely on your machine. It leverages the OpenRouter and Groq APIs to inspect, create, and modify software projects through natural language — keeping your code and data fully under your control.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Local-first** | All code and data remain on your machine — nothing leaves your system |
| **Dual Provider** | OpenRouter (default) or Groq with seamless switching |
| **AI Tool Calling** | Read/write files, search code, execute commands, and query the web |
| **Safe Execution** | Sandboxed to your project root with configurable approval gates |
| **Command Execution** | Run development tools with per-command user consent |
| **Web Search** | Tavily-powered internet research for documentation and references |
| **Interactive & One-shot** | Chat interactively or run a single prompt and exit |
| **Session Persistence** | Auto-save, resume, and manage conversation history |
| **Streaming Responses** | Token-by-token streaming for responsive feedback |
| **Cross-platform** | Linux, macOS, Windows (WSL / PowerShell) |
| **Zero Dependencies** | Built on Python standard library only |

---

## 🚀 Installation

### Quick Install (Linux / macOS / WSL)

```bash
curl -fsSL https://raw.githubusercontent.com/toewaioo/hiai/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/toewaioo/hiai/main/install.ps1 | iex
```

### From Source

```bash
git clone https://github.com/toewaioo/hiai.git
cd hiai
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## ⚙️ Configuration

### Set Your API Key

```bash
hiai config set-key
```

Or via environment variable:

```bash
export OPENROUTER_API_KEY=your-key-here   # for OpenRouter
export GROQ_API_KEY=your-key-here          # for Groq
```

### Choose Your Provider

```bash
hiai config set-provider openrouter   # default
hiai config set-provider groq
```

### Select a Model

```bash
hiai config set-model openrouter/free                    # default free model
hiai config set-model deepseek/deepseek-chat-v3-0324:free
hiai config set-model google/gemini-2.5-flash
hiai config set-model llama-3.3-70b-versatile            # Groq example
hiai config set-model llama-3.1-8b-instant               # Groq example
```

### Web Search (Tavily)

```bash
export TAVILY_API_KEY=tvly-your-key
```

Or configure via CLI:

```bash
hiai config set-search-provider tavily
hiai config set-search-key
hiai config set-search-max-results 5
```

### View Configuration

```bash
hiai config show
```

---

## 📖 Usage

### Interactive Mode

```bash
hiai
```

Starts an interactive session with a persistent conversation loop.

### One-shot Mode

```bash
hiai "Create a Python calculator"
hiai "Fix the bug in main.py"
hiai "Explain the authentication flow"
```

### Target a Project Directory

```bash
hiai --project ./my-project "Create a README"
hiai -p ~/projects/myapp
```

### Streaming Responses

```bash
hiai --stream "Write a detailed explanation"
```

### Auto-Approve Writes

```bash
hiai --yes "Create the requested files"
```

### Override the Model

```bash
hiai --model deepseek/deepseek-chat-v3-0324:free "Explain this project"
```

### Resume a Previous Session

```bash
hiai --resume
```

### Suppress Stats Output

```bash
hiai --quiet "Run the tests"
```

---

## 🔧 AI Tools

HIAI provides **six tools** to the AI agent:

| Tool | Description |
|------|-------------|
| `read_file` | Read a UTF-8 text file within the project |
| `write_file` | Create or replace a UTF-8 text file |
| `list_files` | List files and directories recursively |
| `search_files` | Search text patterns across project files |
| `run_command` | Execute approved local development commands |
| `web_search` | Search the internet via Tavily for references |

---

## ⌨️ Command Execution

The AI can execute development commands with your explicit approval:

```bash
hiai "Run the Python tests"
hiai "Check git status"
hiai "Install dependencies"
```

### Approval Behavior

- **Every command requires confirmation by default** — you see a structured prompt before execution.
- Use `--yes` to auto-approve safe, allowlisted commands.
- Dangerous commands are **always rejected** regardless of mode.

### Allowed Commands (Allowlist)

By default, common development tools are pre-approved:

- **Python**: `python`, `python3`, `pip`, `pytest`
- **JavaScript**: `npm`, `npx`, `node`
- **Version Control**: `git`
- **Systems**: `go`, `cargo`, `make`, `cmake`
- **Shell**: `ls`, `cat`, `grep`, `find`, `curl`
- **More**: `docker`, `ruff`, `black`, `mypy`, `eslint`, `gcc`, `java`, `ruby`, and more

Commands outside the allowlist trigger a permission prompt with a **deny-by-default** recommendation.

### Security

- Commands execute only within the **project root** directory
- Path traversal and escape attempts are **blocked**
- Dangerous commands (`rm -rf /`, `shutdown`, `mkfs`, etc.) are **always rejected**
- `os.system()`, `eval()`, and `exec()` are **never used**
- Subprocess execution with structured arguments and timeouts
- Use `--yes` to auto-approve allowed commands — **never recommended for untrusted projects**

---

## 🌐 Web Search

Search the internet for documentation, package information, error explanations, and more:

```bash
hiai "Search the web for the latest FastAPI documentation"
hiai "Find how to fix this Python error"
```

### Supported Provider

| Provider | Environment Variable |
|----------|---------------------|
| Tavily | `TAVILY_API_KEY` |

### Privacy

- API keys are **never** sent to the AI model
- Search queries are sent **only** to the configured provider
- Results are returned as titles, URLs, and snippets
- Credentials are never printed or stored in project files

---

## 📡 Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/model [name]` | Show or set the current model |
| `/project` | Show project root directory |
| `/status` | Display session information |
| `/tools` | List all available AI tools |
| `/save [path]` | Save conversation history (default: `.hiai/session.json`) |
| `/load [path]` | Load a saved conversation |
| `/history` | List all saved sessions |
| `/retry` | Re-run the last user turn |
| `/search <query>` | Directly invoke web search |
| `/run <command>` | Request command execution via the permission system |
| `/exit`, `/quit` | Exit HIAI (session auto-saved for `--resume`) |

---

## 🧠 Available Models

HIAI supports any OpenRouter or Groq model:

- `openrouter/free` — Default free model
- `deepseek/deepseek-chat-v3-0324:free` — DeepSeek Chat
- `google/gemini-2.5-flash` — Gemini Flash
- `llama-3.3-70b-versatile` — Groq model
- `llama-3.1-8b-instant` — Groq model

Browse all models at [openrouter.ai/models](https://openrouter.ai/models).

---

## 🔒 Security

- **Sandboxed file operations** — All file access is restricted to the project root
- **Path traversal protection** — Escape attempts are rejected immediately
- **Sensitive file approval** — `.env`, `*.pem`, and similar files require explicit consent
- **API key isolation** — Keys are never printed, logged, or sent to the model
- **Write confirmations** — File writes require approval by default
- **Command approvals** — Command execution requires consent by default
- **Dangerous command blocking** — Destructive operations are always rejected
- **Restricted config permissions** — Configuration files use `0600` permissions

---

## 🏗️ Architecture

```
hiai/
├── src/hiai/
│   ├── cli.py              # CLI entry point and argument parsing
│   ├── agent.py            # Agent loop with tool-calling logic
│   ├── client.py           # OpenRouter / Groq HTTP client
│   ├── config.py           # Configuration management (load/save/set)
│   ├── prompts.py          # System prompt templates
│   ├── permissions.py      # Safety and permission checks
│   ├── terminal.py         # Terminal UI, formatting, and user prompts
│   ├── markdown.py         # Markdown response formatter
│   ├── models.py           # Data structures (AppConfig, ToolResult, etc.)
│   ├── exceptions.py       # Error types and exceptions
│   ├── constants.py        # Application constants and defaults
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── schemas.py      # OpenAI-compatible tool definitions
│   │   ├── filesystem.py   # File read/write/list/search operations
│   │   ├── commands.py     # Command execution with safety policy
│   │   └── executor.py     # Tool registry and dispatch
│   └── search/
│       ├── __init__.py
│       ├── base.py         # Provider interface and data classes
│       ├── provider.py     # Provider factory and search entry point
│       └── tavily.py       # Tavily search provider implementation
└── tests/                  # Unit tests for all modules
```

---

## 🛠️ Development

```bash
# Install in development mode
pip install -e .

# Run all tests
make test
python -m unittest discover -s tests -v

# Lint the codebase
make lint
ruff check src/ tests/

# Clean build artifacts
make clean
```

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.
