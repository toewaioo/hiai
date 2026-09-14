HIAI — Complete Local AI Terminal Coding Agent

ROLE

You are a senior Python engineer, CLI developer, AI agent architect, and security-focused software engineer.

Build a complete, production-quality, open-source terminal AI coding agent called HIAI.

HIAI must run locally on the user's computer and connect to OpenRouter using the user's own API key. It must support free OpenRouter models, AI tool calling, safe local file operations, interactive chat, one-shot prompts, configuration management, and curl-based installation.

Do not create a demo, mockup, pseudocode project, or incomplete skeleton. Build a genuinely working application with all source files, working imports, tests, documentation, and installation scripts.

---

1. PROJECT IDENTITY

Project name: HIAI

CLI command:

hiai

Description:

«HIAI is a local AI terminal coding agent powered by OpenRouter. It helps developers inspect, understand, create, and modify software projects through natural language.»

Primary goals:

1. Simple installation.
2. Easy manual API key configuration.
3. Free-model support through OpenRouter.
4. Reliable AI tool-calling loop.
5. Safe local file access.
6. Modern terminal user experience.
7. Cross-platform support.
8. Clean, maintainable Python architecture.
9. Complete documentation.
10. No mandatory paid AI provider or external Python SDK.

---

2. TARGET PLATFORMS

Support:

- Linux
- macOS
- Windows WSL
- Windows PowerShell / CMD where practical

Required Python version:

Python 3.10+

Use cross-platform Python APIs wherever possible.

Do not assume:

- Bash exists on native Windows.
- "/home/user" exists.
- Linux-only permissions always work.
- "~/.config" is the correct configuration directory on every OS.

Use platform-appropriate configuration directories.

Recommended:

- Linux: "~/.config/hiai/config.json"
- macOS: "~/Library/Application Support/hiai/config.json"
- Windows: "%APPDATA%/hiai/config.json"

Use "pathlib.Path".

---

3. REQUIRED PROJECT STRUCTURE

Create this complete structure:

hiai/
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── install.sh
├── uninstall.sh
├── install.ps1
├── Makefile
│
├── src/
│   └── hiai/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── constants.py
│       ├── exceptions.py
│       ├── models.py
│       ├── client.py
│       ├── agent.py
│       ├── prompts.py
│       ├── permissions.py
│       ├── terminal.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── registry.py
│       │   ├── schemas.py
│       │   ├── filesystem.py
│       │   └── executor.py
│       └── utils/
│           ├── __init__.py
│           ├── paths.py
│           └── json_utils.py
│
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_paths.py
    ├── test_filesystem.py
    ├── test_agent.py
    ├── test_client.py
    └── test_cli.py

You may add more files if they improve quality, but do not remove required functionality.

Use a "src" layout and configure the package correctly in "pyproject.toml".

---

4. CORE CLI COMMANDS

Implement all of these:

Interactive mode

hiai

Starts an interactive AI terminal session.

Example:

╦ ╦╦╔═╗╦
╠═╣║╠═╝║
╩ ╩╩╩  ╩

HIAI — Local AI Coding Agent

Project: /home/user/myproject
Model: openrouter/free

hiai>

User can type:

Create a beautiful responsive landing page.

The AI inspects the project, plans changes, requests tools, and writes files after confirmation.

One-shot mode

hiai "Create a Python calculator"

hiai "Explain the authentication flow"

hiai "Fix the bug in main.py"

hiai "Create a responsive portfolio website"

Project option

hiai --project ./my-project "Create a README"

hiai -p ~/projects/myapp

The selected directory becomes the allowed project root.

Auto-approve option

hiai --yes "Create the requested files"

This must be an explicit opt-in.

Default behavior must always ask before every write operation.

Model option

hiai --model openrouter/free "Explain this project"

The command-line model must override the configured model for that invocation only.

API key option

Support:

hiai config set-key

hiai config show

hiai config set-model openrouter/free

hiai config set-base-url https://openrouter.ai/api/v1

hiai config reset

Model command

hiai models

Show the configured model and explain how to select another model.

If implemented, optionally fetch available models from OpenRouter's models endpoint. Do not make network access mandatory for displaying local configuration.

Session commands

Inside interactive mode:

/help
/clear
/exit
/quit
/model
/project
/status

Implement:

- "/help": show available commands.
- "/clear": clear conversation history.
- "/exit": exit.
- "/quit": exit.
- "/model": show current model.
- "/project": show project root.
- "/status": show session information.

---

5. OPENROUTER INTEGRATION

Use OpenRouter's OpenAI-compatible Chat Completions API.

Default base URL:

https://openrouter.ai/api/v1

Chat endpoint:

/v1/chat/completions

Correctly combine the base URL and endpoint without accidentally producing:

/v1/v1/chat/completions

Use:

POST /chat/completions

when the configured base URL already ends in "/api/v1".

Support:

OPENROUTER_API_KEY

API key priority:

1. Explicit CLI option if implemented.
2. Environment variable.
3. Local configuration file.
4. Otherwise show a helpful configuration error.

Default model:

openrouter/free

Allow any user-supplied OpenRouter model ID.

Examples:

openrouter/free
deepseek/deepseek-chat-v3-0324:free
google/gemini-2.5-flash

Do not hardcode obsolete model IDs as guaranteed free models.

The application must never claim a model is free without verifying its current availability or clearly labeling it as user-configured.

HTTP implementation

Use Python standard library:

urllib.request
urllib.error
json

No required third-party OpenAI SDK.

Create a clean client abstraction.

The client must:

- Send correct JSON.
- Set "Authorization: Bearer <key>".
- Set "Content-Type: application/json".
- Support configurable timeout.
- Parse successful JSON.
- Parse API error responses.
- Handle HTTP errors.
- Handle network errors.
- Handle timeouts.
- Handle malformed JSON.
- Handle empty choices.
- Never print the API key.
- Never include the API key in exception messages.

Use a user-agent or OpenRouter attribution headers where appropriate.

Optional HTTP features

Implement if practical:

- Streaming responses.
- Retry with exponential backoff.
- Configurable timeout.
- Max retry count.
- Friendly rate-limit messages.

Do not retry blindly on every error.

---

6. AI TOOL-CALLING AGENT

Build a real agent loop.

The AI must be able to:

1. Receive the user prompt.
2. Inspect the project using tools.
3. Request file operations.
4. Receive tool results.
5. Continue reasoning.
6. Make additional tool calls.
7. Return a final answer.

The loop must support multiple iterations.

Example:

User:
Create a FastAPI project.

HIAI:
I will inspect the project first.

Tool call:
list_files

Tool result:
No files found.

Tool call:
write_file
main.py

Tool result:
Write approved.

Tool call:
write_file
requirements.txt

Tool result:
Write approved.

HIAI:
Created the FastAPI project.

Required message handling

Support OpenRouter/OpenAI-compatible messages:

{
  "role": "system",
  "content": "..."
}

{
  "role": "user",
  "content": "..."
}

{
  "role": "assistant",
  "content": "...",
  "tool_calls": []
}

{
  "role": "tool",
  "tool_call_id": "call_123",
  "content": "..."
}

Correctly preserve assistant tool calls in the conversation history.

Correctly preserve tool call IDs.

Correctly parse JSON arguments.

Handle multiple tool calls returned in a single assistant message.

Execute tool calls in a controlled manner.

Return tool results as JSON strings.

Do not execute arbitrary Python or shell commands from model-generated text.

Tool call failures

If the model returns malformed tool arguments:

- Do not crash.
- Return a useful error to the model.
- Continue when possible.

If a tool fails:

- Return structured error information.
- Show the user a concise explanation.
- Allow the model to adapt.

Add a maximum agent iteration limit:

20 iterations by default

Make it configurable.

Prevent infinite loops.

---

7. SYSTEM PROMPT

Create a dedicated "prompts.py".

Use a system prompt similar to:

You are HIAI, a local AI coding agent.

You help developers understand, create, debug, and modify software projects.

You have access to tools for inspecting and editing files inside the selected project directory.

Rules:

1. Inspect the project before making changes when necessary.
2. Use list_files to understand the project structure.
3. Use read_file to inspect relevant files.
4. Use search_files to locate code.
5. Use write_file to create or replace files.
6. Do not invent existing file contents when inspection is needed.
7. Keep changes focused on the user's request.
8. Never execute shell commands.
9. Never access files outside the project root.
10. Never expose API keys or secrets.
11. Explain important changes after completing a task.
12. If a tool fails, adapt and try again when reasonable.
13. Do not claim that tests passed unless tests were actually run.
14. Do not claim that code was written unless the write tool succeeded.
15. Respect user permission decisions.
16. If the request is ambiguous, ask a concise clarification.

Add project context:

Current project root:
{project_root}

Do not include sensitive environment variables in the system prompt.

---

8. REQUIRED FILE TOOLS

Implement exactly these core tools.

8.1 read_file

Schema:

{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "Read a UTF-8 text file inside the project.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        }
      },
      "required": ["path"],
      "additionalProperties": false
    }
  }
}

Behavior:

- Accept a relative path.
- Resolve it safely.
- Reject paths outside the project.
- Reject directories.
- Reject missing files.
- Read UTF-8 text.
- Return structured JSON.
- Limit maximum file size.
- Handle binary files safely.
- Do not follow symlinks outside the project.

Example result:

{
  "status": "success",
  "path": "main.py",
  "content": "print('Hello')",
  "bytes": 15
}

8.2 write_file

Schema:

{
  "type": "function",
  "function": {
    "name": "write_file",
    "description": "Create or replace a UTF-8 text file inside the project.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "content": {
          "type": "string"
        }
      },
      "required": ["path", "content"],
      "additionalProperties": false
    }
  }
}

Behavior:

- Ask user permission before writing.
- Show the target path.
- Show whether the file is new or existing.
- Show content size.
- Reject unsafe paths.
- Create parent directories when allowed.
- Write UTF-8.
- Use atomic replacement where practical.
- Return structured result.
- Never overwrite without permission unless "--yes" is active.

Example:

┌─ File write requested ───────────────
│ Path: src/main.py
│ Operation: Create
│ Size: 1.2 KB
└──────────────────────────────────────

Allow write? [y/N]:

Result:

{
  "status": "written",
  "path": "src/main.py",
  "bytes": 1200
}

Denied:

{
  "status": "cancelled",
  "path": "src/main.py",
  "message": "User denied the write operation."
}

8.3 list_files

Schema:

{
  "type": "function",
  "function": {
    "name": "list_files",
    "description": "List files and directories inside the project.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string",
          "default": "."
        },
        "recursive": {
          "type": "boolean",
          "default": true
        }
      },
      "additionalProperties": false
    }
  }
}

Behavior:

- List project files.
- Support recursive listing.
- Exclude common large/generated directories.
- Exclude ".git", "node_modules", virtual environments, caches, and build outputs by default.
- Never leave the project root.
- Limit result count.
- Return directories and files clearly.

Example:

{
  "status": "success",
  "path": ".",
  "files": [
    "README.md",
    "main.py",
    "src/",
    "src/app.py"
  ]
}

8.4 search_files

Schema:

{
  "type": "function",
  "function": {
    "name": "search_files",
    "description": "Search text inside UTF-8 project files.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string"
        },
        "path": {
          "type": "string",
          "default": "."
        },
        "max_results": {
          "type": "integer",
          "minimum": 1,
          "maximum": 100,
          "default": 50
        }
      },
      "required": ["query"],
      "additionalProperties": false
    }
  }
}

Behavior:

- Search recursively.
- Case-insensitive by default.
- Return file path.
- Return line number.
- Return matching text.
- Skip binary files.
- Skip large files.
- Skip ignored directories.
- Limit results.
- Handle invalid UTF-8 safely.

Example:

{
  "status": "success",
  "query": "FastAPI",
  "matches": [
    {
      "path": "main.py",
      "line": 1,
      "text": "from fastapi import FastAPI"
    }
  ]
}

---

9. SECURITY REQUIREMENTS

Security is a first-class feature.

Project root sandbox

All file tools must operate within the selected project root.

Reject:

../../etc/passwd

Reject absolute paths outside the project.

Reject symlink escapes.

Do not use unrestricted:

os.system(...)

subprocess.run(...)

eval(...)

exec(...)

The initial version must not include a shell execution tool.

API key security

- Never print the API key.
- Never include it in tool results.
- Never send it to the model.
- Never write it into project files.
- Never commit it.
- Never put it in README examples as a real key.
- Use restricted config file permissions where supported.
- Support environment variable configuration.

File write security

- Confirm every write by default.
- Make "--yes" explicit.
- Show target path.
- Do not write outside project root.
- Use atomic file replacement.
- Handle permission errors gracefully.
- Do not silently modify unrelated files.

Sensitive file handling

Implement a configurable policy to warn or block access to common secret files:

.env
.env.*
*.pem
*.key
id_rsa
id_ed25519
credentials.json
secrets.json

Default recommendation:

- Do not automatically read likely secret files.
- Require explicit user approval for sensitive file reads.
- Never expose detected secret contents in logs.

If this adds complexity, implement a safe warning system first and document it.

---

10. CONFIGURATION

Implement a configuration manager.

Configuration fields:

{
  "model": "openrouter/free",
  "base_url": "https://openrouter.ai/api/v1",
  "api_key": "",
  "timeout": 120,
  "max_iterations": 20,
  "max_read_bytes": 1000000,
  "max_write_bytes": 2000000,
  "theme": "auto"
}

Use a platform-appropriate config path.

Commands:

hiai config set-key
hiai config set-model openrouter/free
hiai config set-base-url https://openrouter.ai/api/v1
hiai config show
hiai config reset

Do not display the actual API key.

Show:

API key: configured

or:

API key: not configured

Support environment variable override.

Make configuration errors friendly.

---

11. TERMINAL USER EXPERIENCE

Build a clean terminal UI using standard library only unless an optional dependency is justified.

Required:

- Clear prompts.
- Colored output where supported.
- Graceful fallback when color is unavailable.
- Tool call status.
- Tool result status.
- Error messages.
- Keyboard interrupt handling.
- EOF handling.
- No traceback for normal user errors.
- Clean exit.

Example:

HIAI is thinking...

⚙ Tool: list_files
✓ Tool completed

⚙ Tool: read_file
✓ Tool completed

⚙ Tool: write_file
┌─ File write requested ─────────────
│ Path: index.html
└────────────────────────────────────

Allow write? [y/N]:

Do not make color or Unicode mandatory for functionality.

Support:

NO_COLOR

when appropriate.

---

12. CLI ARCHITECTURE

Use clean separation:

cli.py

- Argument parsing.
- Command dispatch.
- Interactive mode.
- One-shot mode.
- Error handling.

config.py

- Load config.
- Save config.
- API key management.
- Model management.
- Platform paths.

client.py

- OpenRouter HTTP client.
- Request handling.
- Error handling.
- Optional streaming.

agent.py

- Conversation state.
- Agent loop.
- Tool dispatch.
- Iteration limits.

tools/registry.py

- Tool definitions.
- Tool registration.
- Tool lookup.

tools/filesystem.py

- Safe path resolution.
- File reads.
- File writes.
- Directory listing.
- Text search.

permissions.py

- Write confirmation.
- Sensitive file confirmation.
- "--yes" handling.

terminal.py

- Output formatting.
- Color.
- Status messages.
- Input helpers.

models.py

Use dataclasses or typed structures for:

- Configuration.
- Tool results.
- Agent settings.
- API errors.

---

13. INSTALLATION

Linux / macOS / WSL

Create "install.sh".

Requirements:

- Detect Python 3.10+.
- Create a virtual environment.
- Install HIAI.
- Install the "hiai" executable.
- Support "$HOME/.local/bin".
- Do not require root by default.
- Print helpful PATH instructions.
- Fail safely.
- Do not overwrite unrelated files.

Command:

curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/hiai/main/install.sh | bash

The curl installer must genuinely work.

Do not write an installer that downloads only one script while expecting other source files to magically exist.

Choose one reliable approach:

1. Download a GitHub release archive.
2. Download the complete project archive.
3. Download all required files.
4. Use a packaged release.

Document the chosen approach.

Windows

Create "install.ps1".

Support:

irm https://raw.githubusercontent.com/YOUR_USERNAME/hiai/main/install.ps1 | iex

The script must:

- Detect Python.
- Create a virtual environment.
- Install the package.
- Create a usable "hiai" command.
- Print PATH instructions.
- Avoid requiring administrator privileges by default.

Do not claim native Windows support if it has not been tested.

Uninstall

Provide:

hiai uninstall

or a documented uninstall script.

Do not delete API key configuration silently.

---

14. PYPROJECT.TOML

Use a correct modern Python package configuration.

Requirements:

- Package name: hiai.
- Version.
- Description.
- Python requirement.
- README.
- License.
- Console script.
- Src layout.
- Test configuration if needed.

Console entry point:

[project.scripts]
hiai = "hiai.cli:main"

Make sure:

pip install .

actually works.

Make sure:

hiai --help

actually works after installation.

---

15. TESTING

Write real tests.

Use Python "unittest" if avoiding external dependencies.

Test:

Configuration

- Load default config.
- Save config.
- Load saved config.
- Environment variable overrides config.
- Missing API key.
- Invalid config.
- API key not printed.

Path security

- Valid relative path.
- Reject "../".
- Reject outside absolute path.
- Project root handling.
- Symlink escape handling where supported.

Filesystem

- Read file.
- Write file.
- Create parent directories.
- Denied write.
- List files.
- Search files.
- Binary file handling.
- Large file handling.
- Missing file handling.

Agent

Mock HTTP client responses.

Test:

- Simple assistant response.
- One tool call.
- Multiple tool calls.
- Tool result insertion.
- Invalid tool arguments.
- Tool failure.
- Max iterations.
- API errors.

Do not use real API keys in tests.

Do not require internet access for unit tests.

CLI

Test:

hiai --help
hiai --version
hiai config show

Use subprocess tests if appropriate.

---

16. DOCUMENTATION

Write a complete README.