# HIAI — Local AI Terminal Coding Agent

HIAI is a local AI terminal coding agent powered by OpenRouter (with optional Groq support). It helps developers inspect, understand, create, and modify software projects through natural language while keeping all code and data on the user's machine.

## Features

- **Local-first** — Your code never leaves your machine
- **Dual provider support** — OpenRouter (default) or Groq
- **AI tool calling** — The agent can read/write files, search code, run commands, and search the web
- **Safe file operations** — Sandboxed to your project root with write confirmations by default
- **Command execution** — Run development commands with user approval
- **Web search** — Search the internet for documentation and references (Tavily)
- **Interactive & one-shot modes** — Chat or run a single prompt
- **Cross-platform** — Linux, macOS, Windows (WSL/PowerShell)
- **Zero required dependencies** — Uses only Python standard library

## Installation

### Quick install (Linux/macOS/WSL)

```bash
curl -fsSL https://raw.githubusercontent.com/toewaioo/hiai/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/toewaioo/hiai/main/install.ps1 | iex
```

### From source

```bash
git clone https://github.com/toewaioo/hiai.git
cd hiai
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

### Set your API key

```bash
hiai config set-key
```

Or set the environment variable:

```bash
export OPENROUTER_API_KEY=your-key-here   # for OpenRouter
export GROQ_API_KEY=your-key-here         # for Groq
```

### Choose your provider

```bash
hiai config set-provider openrouter   # default
hiai config set-provider groq
```

### Set your model

```bash
hiai config set-model openrouter/free          # default free model
hiai config set-model deepseek/deepseek-chat-v3-0324:free
hiai config set-model google/gemini-2.5-flash
hiai config set-model llama-3.3-70b-versatile  # Groq example
```

### Web search configuration (optional)

```bash
export TAVILY_API_KEY=tvly-your-key   # or
hiai config set-search-provider tavily
hiai config set-search-key
hiai config set-search-max-results 5
```

### Show configuration

```bash
hiai config show
```

## Usage

### Interactive mode

```bash
hiai
```

Starts an interactive session where you can chat with the AI agent.

### One-shot mode

```bash
hiai "Create a Python calculator"
hiai "Fix the bug in main.py"
hiai "Explain the authentication flow"
```

### Project directory

```bash
hiai --project ./my-project "Create a README"
hiai -p ~/projects/myapp
```

### Auto-approve writes

```bash
hiai --yes "Create the requested files"
```

### Model override

```bash
hiai --model deepseek/deepseek-chat-v3-0324:free "Explain this project"
```

### Resume session

```bash
hiai --resume
```

### Streaming responses

```bash
hiai --stream "Write a detailed explanation"
```

## AI Tools

HIAI provides 6 tools to the AI agent:

| Tool | Description |
|------|-------------|
| `read_file` | Read a UTF-8 text file inside the project |
| `write_file` | Create or replace a UTF-8 text file |
| `list_files` | List files and directories |
| `search_files` | Search text inside project files |
| `run_command` | Run a local development command |
| `web_search` | Search the internet for information |

## Command Execution

The AI can run development commands with your approval:

```bash
hiai "Run the Python tests"
hiai "Check git status"
hiai "Install dependencies"
```

Every command requires confirmation by default. Use `--yes` to auto-approve allowed commands.

## Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/model` | Show or set the current model |
| `/project` | Show project root |
| `/status` | Show session information |
| `/tools` | Show available AI tools |
| `/save [path]` | Save conversation history (default: `.hiai/session.json`) |
| `/load [path]` | Load conversation history |
| `/history` | List saved sessions |
| `/retry` | Re-run the last user turn |
| `/exit` / `/quit` | Exit HIAI (saves session for `--resume`) |

## Available Models

HIAI supports any OpenRouter or Groq model. Examples:

- `openrouter/free` — default free model
- `deepseek/deepseek-chat-v3-0324:free` — DeepSeek Chat
- `google/gemini-2.5-flash` — Gemini Flash
- `llama-3.3-70b-versatile` — Groq model
- `llama-3.1-8b-instant` — Groq model

Browse OpenRouter models at [openrouter.ai/models](https://openrouter.ai/models).

## Security

- All file operations are sandboxed to your project root
- Path traversal attacks are rejected
- Sensitive files (`.env`, `*.pem`, etc.) require explicit approval
- API keys are never printed or sent to the model
- File writes require confirmation by default
- Command execution requires approval by default
- Dangerous commands are always blocked
- Config file uses restricted permissions (0600)

## Development

```bash
# Install dev dependencies
pip install -e .

# Run tests
make test
python -m unittest discover -s tests -v

# Lint
make lint
ruff check src/ tests/

# Clean
make clean
```

## License

MIT License. See [LICENSE](LICENSE) for details.