# HIAI — Local AI Terminal Coding Agent

HIAI is a local AI terminal coding agent powered by OpenRouter. It helps developers inspect, understand, create, and modify software projects through natural language.

## Features

- **Local-first** — runs on your machine, your code never leaves
- **OpenRouter integration** — use free or paid models via OpenRouter API
- **AI tool calling** — the AI inspects, reads, writes, and searches your project
- **Command execution** — run development commands with approval
- **Web search** — search the internet for documentation and references
- **Safe file operations** — sandboxed to your project root, write confirmations by default
- **Interactive & one-shot modes** — chat or run a single prompt
- **Cross-platform** — Linux, macOS, Windows (WSL/PowerShell)
- **Zero dependencies** — uses only Python standard library

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
export OPENROUTER_API_KEY=your-key-here
```

### Set your model

```bash
hiai config set-model openrouter/free
```

### Web search configuration

Set up Tavily for web search:

```bash
export TAVILY_API_KEY=tvly-your-key
```

Or use the config commands:

```bash
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

Every command requires confirmation by default:

```
┌─ Command execution requested ──────────────
│ Command: python -m unittest discover -v
│ Directory: /home/user/myproject
│ Timeout: 30 seconds
└────────────────────────────────────────────

Allow command? [y/N]:
```

### Allowed commands

By default, these commands are pre-approved (still ask for confirmation):

- `python`, `python3`, `pip`, `pytest`
- `npm`, `npx`, `node`
- `git`, `go`, `cargo`
- `curl`, `wget`
- `ls`, `cat`, `grep`, `find`
- And more development tools

### Security

- Dangerous commands are always rejected (`rm -rf /`, `shutdown`, etc.)
- Commands are restricted to the project root directory
- Path escape attempts are blocked
- Commands outside the allowed list require explicit approval
- Use `--yes` to auto-approve allowed commands

## Web Search

Search the internet for documentation and references:

```bash
hiai "Search the web for FastAPI documentation"
hiai "Find how to fix this Python error"
```

### Supported providers

| Provider | Environment Variable |
|----------|---------------------|
| Tavily | `TAVILY_API_KEY` |

### Configuration

```bash
# Set API key
export TAVILY_API_KEY=tvly-your-key

# Or use config
hiai config set-search-provider tavily
hiai config set-search-key
```

### Privacy

- API keys are never sent to the AI model
- Search queries are sent to the configured provider only
- Results are returned as titles, URLs, and snippets

## Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/model` | Show current model |
| `/project` | Show project root |
| `/status` | Show session info |
| `/tools` | Show available AI tools |
| `/exit` | Exit HIAI |
| `/quit` | Exit HIAI |

## Available Models

HIAI supports any OpenRouter model. Some examples:

- `openrouter/free` — default free model
- `deepseek/deepseek-chat-v3-0324:free` — DeepSeek Chat
- `google/gemini-2.5-flash` — Gemini Flash

Browse models at [openrouter.ai/models](https://openrouter.ai/models).

## Security

- All file operations are sandboxed to your project root
- Path traversal attacks are rejected
- Sensitive files (`.env`, `*.pem`, etc.) require explicit approval
- API keys are never printed or sent to the model
- File writes require confirmation by default
- Command execution requires approval by default
- Dangerous commands are always blocked
- Config file uses restricted permissions (0600)

## Architecture

```
hiai/
├── src/hiai/
│   ├── cli.py              # CLI entry point
│   ├── agent.py            # Agent loop with tool calling
│   ├── client.py           # OpenRouter HTTP client
│   ├── config.py           # Configuration management
│   ├── prompts.py          # System prompts
│   ├── permissions.py      # Safety checks
│   ├── terminal.py         # Terminal UI
│   ├── markdown.py         # Markdown formatter
│   ├── models.py           # Data structures
│   ├── exceptions.py       # Error types
│   ├── constants.py        # App constants
│   ├── tools/
│   │   ├── schemas.py      # Tool definitions
│   │   ├── filesystem.py   # File operations
│   │   ├── commands.py     # Command execution
│   │   └── executor.py     # Tool dispatch
│   └── search/
│       ├── __init__.py     # Search package
│       ├── base.py         # Provider interface
│       ├── tavily.py       # Tavily provider
│       └── provider.py     # Provider factory
└── tests/
```

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
