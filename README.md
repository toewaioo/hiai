# HIAI — Local AI Terminal Coding Agent

HIAI is a local AI terminal coding agent powered by OpenRouter. It helps developers inspect, understand, create, and modify software projects through natural language.

## Features

- **Local-first** — runs on your machine, your code never leaves
- **OpenRouter integration** — use free or paid models via OpenRouter API
- **AI tool calling** — the AI inspects, reads, writes, and searches your project
- **Safe file operations** — sandboxed to your project root, write confirmations by default
- **Interactive & one-shot modes** — chat or run a single prompt
- **Cross-platform** — Linux, macOS, Windows (WSL/PowerShell)
- **Zero dependencies** — uses only Python standard library

## Installation

### Quick install (Linux/macOS/WSL)

```bash
curl -fsSL https://raw.githubusercontent.com/hiai-ai/hiai/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/hiai-ai/hiai/main/install.ps1 | iex
```

### From source

```bash
git clone https://github.com/hiai-ai/hiai.git
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

## Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/model` | Show current model |
| `/project` | Show project root |
| `/status` | Show session info |
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
- Config file uses restricted permissions (0600)

## Architecture

```
hiai/
├── src/hiai/
│   ├── cli.py          # CLI entry point
│   ├── agent.py        # Agent loop with tool calling
│   ├── client.py       # OpenRouter HTTP client
│   ├── config.py       # Configuration management
│   ├── prompts.py      # System prompts
│   ├── permissions.py  # Safety checks
│   ├── terminal.py     # Terminal UI
│   ├── models.py       # Data structures
│   ├── exceptions.py   # Error types
│   ├── constants.py    # App constants
│   └── tools/
│       ├── schemas.py     # Tool definitions
│       ├── filesystem.py  # File operations
│       └── executor.py    # Tool dispatch
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
# hiai
