HIAI — Add Command Execution and Web Search Tools

ROLE

You are a senior Python developer and AI agent engineer working on an existing project called HIAI.

HIAI is a local AI terminal coding agent powered by OpenRouter.

The project already has:

- Python CLI.
- OpenRouter API client.
- AI tool-calling agent loop.
- "read_file".
- "write_file".
- "list_files".
- "search_files".
- Configuration management.
- Interactive mode.
- One-shot mode.
- Safe write confirmation.
- Project-root sandbox.

YOUR TASK

Add ONLY these two new AI tools:

1. "run_command" — execute local terminal commands.
2. "web_search" — search the internet and return useful results to the AI.

Do not rebuild the existing HIAI project from scratch.

Do not replace working files unnecessarily.

Inspect the repository first, understand the existing architecture, and integrate the features into the current codebase.

Preserve all existing functionality.

---

1. NEW TOOL: run_command

Purpose

Allow the AI agent to execute approved local development commands inside the selected project directory.

Examples:

Run the Python tests.

Install the dependencies.

Run the development server.

Check the Git status.

Run npm install.

The AI must be able to request a command through a structured tool call.

Tool name

run_command

Tool schema

Use the OpenAI-compatible function tool format already used by HIAI.

{
  "type": "function",
  "function": {
    "name": "run_command",
    "description": "Run an approved local development command inside the selected project directory.",
    "parameters": {
      "type": "object",
      "properties": {
        "command": {
          "type": "string",
          "description": "The command to execute."
        },
        "timeout": {
          "type": "integer",
          "description": "Maximum execution time in seconds.",
          "minimum": 1,
          "maximum": 300,
          "default": 30
        }
      },
      "required": ["command"],
      "additionalProperties": false
    }
  }
}

---

2. COMMAND EXECUTION SECURITY

This is the most important part of the feature.

The AI is allowed to request commands, but the user must remain in control.

Default behavior

Every command must require confirmation.

Example:

┌─ Command execution requested ──────────────
│ Command: python -m unittest discover -v
│ Directory: /home/user/myproject
│ Timeout: 30 seconds
└────────────────────────────────────────────

Allow command? [y/N]:

Only execute the command after the user explicitly approves.

A denied command must not execute.

Return a structured result:

{
  "status": "cancelled",
  "message": "User denied command execution."
}

Explicit auto-approve mode

Support the existing HIAI option:

hiai --yes "Run the tests and fix errors"

When "--yes" is enabled, commands may run without asking for every command.

However:

- Keep dangerous-command protection enabled.
- Do not bypass safety validation.
- Document that "--yes" allows model-requested commands to execute.
- Do not silently enable auto-approve.

Project directory restriction

Commands must execute with:

cwd = selected project root

Do not allow the model to choose an arbitrary working directory outside the project root.

If a command tries to change directory, validate the resulting path and keep it within the allowed project.

Reject path escapes.

---

3. SAFE COMMAND POLICY

Implement a dedicated command security module.

Recommended file:

src/hiai/tools/commands.py

Or integrate into the existing tools package if that matches the architecture.

Block dangerous commands

By default, reject clearly destructive or dangerous operations, including:

rm -rf /
rm -rf ~
mkfs
format
diskpart
shutdown
reboot
halt
poweroff
dd if=
:(){ :|:& };:

Also block attempts to:

- Delete the entire project recursively.
- Modify system directories.
- Format disks.
- Disable security tools.
- Install persistence.
- Access SSH private keys.
- Read password stores.
- Exfiltrate secrets.
- Download and execute arbitrary remote scripts.
- Run commands that intentionally bypass the safety policy.

Do not rely only on naive substring checks.

Use a safer execution design.

Shell handling

Prefer:

subprocess.run(
    args,
    cwd=project_root,
    capture_output=True,
    text=True,
    timeout=timeout,
)

For maximum safety, use structured argument execution rather than passing arbitrary strings to a shell.

If shell syntax is required for legitimate development commands, implement a clearly documented shell mode with stricter approval and safety checks.

Do not use:

os.system(command)

Do not use:

eval(command)

Do not use:

exec(command)

Do not allow unrestricted model-generated shell execution.

Recommended initial scope

For the first implementation, support common development commands such as:

python
python3
pip
pytest
npm
node
npx
git
go
cargo
php
composer
curl

Make the allowlist configurable.

Do not assume all commands are safe just because they are in the allowlist. Arguments must also be validated.

For commands outside the allowlist:

Command is not in the allowed command policy.
Allow this command? [y/N]:

Default recommendation: deny.

---

4. COMMAND RESULT FORMAT

Return structured JSON to the model.

Example successful result:

{
  "status": "success",
  "command": "python -m unittest discover -v",
  "exit_code": 0,
  "stdout": "All tests passed.",
  "stderr": "",
  "timed_out": false
}

Example failed result:

{
  "status": "error",
  "command": "python main.py",
  "exit_code": 1,
  "stdout": "",
  "stderr": "ModuleNotFoundError: No module named 'fastapi'",
  "timed_out": false
}

Example timeout:

{
  "status": "timeout",
  "command": "npm run dev",
  "exit_code": null,
  "stdout": "",
  "stderr": "",
  "timed_out": true
}

Requirements:

- Capture stdout.
- Capture stderr.
- Return exit code.
- Return timeout status.
- Limit output size.
- Avoid flooding the AI context.
- Preserve enough output for debugging.
- Handle missing executables.
- Handle permission errors.
- Handle Unicode output.
- Handle Windows and Unix differences.

Do not claim a command succeeded unless it actually returned successfully.

---

5. NEW TOOL: web_search

Purpose

Allow HIAI to search the internet for:

- Programming documentation.
- Framework documentation.
- Package information.
- Error explanations.
- Current software versions.
- Security advisories.
- Technical examples.
- General research.

Example prompts:

Search the web for the latest FastAPI documentation.

Search how to fix this Python error.

Find the official OpenRouter tool calling documentation.

Search for the latest Laravel API changes.

Tool name

web_search

Tool schema

{
  "type": "function",
  "function": {
    "name": "web_search",
    "description": "Search the internet for relevant information and return search results with titles, URLs, and snippets.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The search query."
        },
        "max_results": {
          "type": "integer",
          "description": "Maximum number of results.",
          "minimum": 1,
          "maximum": 10,
          "default": 5
        }
      },
      "required": ["query"],
      "additionalProperties": false
    }
  }
}

---

6. WEB SEARCH PROVIDER

Implement a provider abstraction.

Recommended file:

src/hiai/search/
├── __init__.py
├── base.py
└── provider.py

Or use a simpler design compatible with the existing project.

Provider priority

Support at least one real web search provider.

Recommended options:

Option A — Tavily API

Use Tavily Search API.

Configuration:

TAVILY_API_KEY

Option B — Brave Search API

Use Brave Search API.

Configuration:

BRAVE_SEARCH_API_KEY

Option C — Self-hosted or alternative provider

Allow future providers through a clean interface.

Do not hardcode one provider in a way that prevents future extensions.

Important

Do not use OpenRouter's API key as a web search key unless the provider explicitly supports web search through that API.

OpenRouter model tool calling and external web search are separate capabilities.

If the project does not have a web search provider configured, return a helpful message:

{
  "status": "error",
  "message": "Web search is not configured. Set TAVILY_API_KEY or configure another supported provider."
}

Do not fake search results.

Do not return made-up URLs.

Do not claim to have searched the web when the search request failed.

---

7. TAVILY IMPLEMENTATION

If Tavily is selected as the default provider, implement it using Python standard library HTTP requests.

Endpoint:

https://api.tavily.com/search

Use the provider's current official API documentation to verify request format.

Expected request shape:

{
  "api_key": "YOUR_TAVILY_API_KEY",
  "query": "FastAPI latest documentation",
  "max_results": 5
}

Never send the Tavily key to the AI model.

Never print the key.

Never store it in project files.

Tavily result normalization

Normalize provider results into:

{
  "status": "success",
  "query": "FastAPI latest documentation",
  "results": [
    {
      "title": "FastAPI Documentation",
      "url": "https://example.com/docs",
      "snippet": "Useful documentation summary."
    }
  ]
}

Support:

- HTTP errors.
- Timeouts.
- Invalid JSON.
- Missing API key.
- Empty results.
- Rate limits.
- Result count limits.

Use a timeout.

Do not expose raw provider credentials in exceptions.

---

8. SEARCH PROVIDER CONFIGURATION

Add configuration fields:

{
  "search_provider": "tavily",
  "search_api_key": "",
  "search_max_results": 5
}

Prefer environment variables for API keys:

export TAVILY_API_KEY="tvly-your-key"

Support:

hiai config set-search-provider tavily

hiai config set-search-key

hiai config search-show

Or use an equivalent command structure consistent with the existing CLI.

The actual API key must never be shown.

If multiple providers are supported, allow selection:

hiai config set-search-provider brave

---

9. AGENT LOOP INTEGRATION

Register both tools in the existing tool registry.

The AI should receive all existing tools plus:

run_command
web_search

The agent loop must already support multiple tool calls. Preserve that behavior.

Example:

User:
Search the web for the latest FastAPI installation instructions, then create a project.

HIAI:
⚙ Tool: web_search

Search query:
latest FastAPI installation instructions

✓ web_search

⚙ Tool: write_file

Path:
requirements.txt

Allow write? [y/N]:

Another example:

User:
Run the tests and fix any errors.

HIAI:
⚙ Tool: run_command

Command:
python -m unittest discover -v

Allow command? [y/N]:

If the command fails:

1. Return stdout/stderr to the model.
2. Let the model analyze the error.
3. Let the model inspect files.
4. Let the model modify files after approval.
5. Let the model run the tests again after approval.

Do not claim the problem is fixed unless the test command succeeds.

---

10. SYSTEM PROMPT UPDATES

Update the existing HIAI system prompt.

Add:

You now have access to:

1. read_file
2. write_file
3. list_files
4. search_files
5. run_command
6. web_search

Use run_command to execute local development commands when needed.

Use web_search to find current online information, documentation, and technical references.

Rules:

- Never execute commands without user permission unless explicit auto-approve mode is enabled.
- Never use commands to bypass security restrictions.
- Never access files outside the project root.
- Do not claim tests passed unless they actually passed.
- Do not claim web search results unless the search tool returned them.
- Use official documentation when possible.
- Prefer inspecting the local project before changing it.
- Keep command execution focused on the user's request.
- Do not expose API keys or secrets.

Do not put API keys into the system prompt.

---

11. CLI OPTIONS

Preserve existing commands.

Add:

hiai --allow-commands "Run the tests"

Only implement this if it fits the existing permission model.

Recommended simpler approach:

hiai "Run the tests"

Always asks before commands.

hiai --yes "Run the tests"

Auto-approves safe, allowed commands.

Do not add a dangerous unrestricted mode.

Interactive commands

Add:

/tools

Show all available tools.

Example:

Available tools:

✓ read_file
✓ write_file
✓ list_files
✓ search_files
✓ run_command
✓ web_search

Optional:

/search <query>

This should directly invoke the web search tool if configured.

Optional:

/run <command>

This should directly request command execution through the same permission system.

Do not create a second unsafe execution path for slash commands.

---

12. TERMINAL UX

Use the existing terminal formatting.

For command calls:

⚙ Tool: run_command
⌘ Command: python -m unittest
📁 Directory: ./project

For search calls:

⚙ Tool: web_search
🔎 Query: latest FastAPI documentation

For results:

✓ Command completed
✓ Search completed
✗ Command failed
✗ Search failed

Show a concise summary.

Do not dump huge outputs to the terminal by default.

Keep the full structured result available to the agent.

---

13. CROSS-PLATFORM REQUIREMENTS

Support:

- Linux.
- macOS.
- Windows WSL.
- Windows PowerShell / CMD where practical.

Do not assume:

bash
sh
grep
cat
ls

exist on every platform.

Use platform-aware commands where possible.

For example:

- "python" vs "python3".
- "dir" vs "ls".
- Windows executable lookup.
- Windows path separators.
- Windows subprocess behavior.
- Process timeout handling.

The file tools must continue using "pathlib".

Do not break existing installation.

---

14. TESTING

Add unit tests for both tools.

Command tests

Test:

- Allowed command.
- Denied command.
- Permission prompt.
- "--yes".
- Timeout.
- Nonzero exit code.
- Missing executable.
- stdout capture.
- stderr capture.
- Output truncation.
- Project root working directory.
- Dangerous command rejection.
- Path escape attempt.
- Windows compatibility where practical.

Never run destructive commands in tests.

Use harmless commands such as:

python -c "print('hello')"

Use platform-aware alternatives when necessary.

Web search tests

Mock the HTTP provider.

Test:

- Successful search.
- Missing API key.
- HTTP error.
- Timeout.
- Invalid JSON.
- Empty result.
- Result normalization.
- Max result limit.
- API key not exposed.

Never use real API keys in tests.

Do not require internet access for unit tests.

Agent tests

Test:

- "run_command" tool call.
- "web_search" tool call.
- Multiple tool calls.
- Tool result insertion.
- Tool errors.
- Denied command.
- Search provider failure.
- Max iterations.

---

15. DOCUMENTATION

Update README.md.

Add:

Command execution

hiai "Run the tests"

Explain:

- Permission behavior.
- "--yes".
- Allowed commands.
- Timeout.
- Security restrictions.
- Project directory.

Web search

hiai "Search the web for FastAPI documentation"

Explain:

- Supported provider.
- API key setup.
- Search result format.
- Rate limits.
- Network requirement.
- Privacy considerations.

Configuration

Document:

export TAVILY_API_KEY="tvly-your-key"

Or:

hiai config set-search-key

Never include real keys.

Security warning

Explain that command execution gives the AI the ability to run local programs. Users should review commands before approving them.

Do not recommend "--yes" for untrusted prompts or unknown projects.

---

16. FILES TO CREATE OR MODIFY

Inspect the existing project and modify the correct files.

Likely files:

src/hiai/agent.py
src/hiai/cli.py
src/hiai/config.py
src/hiai/prompts.py
src/hiai/permissions.py
src/hiai/tools/registry.py
src/hiai/tools/executor.py
src/hiai/tools/schemas.py

New files may include:

src/hiai/tools/commands.py
src/hiai/search/base.py
src/hiai/search/tavily.py
src/hiai/search/__init__.py
tests/test_commands.py
tests/test_search.py

Do not create duplicate tool registries.

Do not break existing imports.

Do not remove the existing file sandbox.

Do not remove write confirmation.

---

17. ACCEPTANCE CRITERIA

The feature is complete only when:

Existing tools

All existing tools still work:

read_file
write_file
list_files
search_files

Command tool

This works:

hiai "Run the Python tests"

The AI can request "run_command".

The user is asked for permission.

The command executes inside the project root.

The result is returned to the AI.

The AI can continue after the result.

Web search

With a configured provider:

hiai "Search the web for the latest FastAPI documentation"

The AI can request "web_search".

The provider returns real results.

The results contain titles, URLs, and snippets.

The results are returned to the AI.

Security

- Commands require confirmation by default.
- Dangerous commands are rejected.
- No unrestricted shell execution.
- Project root is enforced.
- API keys are not exposed.
- Web search credentials are not exposed.
- No arbitrary code execution through "eval" or "exec".

Tests

All tests pass.

Installation

Existing install scripts still work.

No mandatory dependency is added without updating package configuration.

Documentation

README explains both tools.

---

18. DEVELOPMENT WORKFLOW

Follow this process exactly.

Step 1 — Inspect existing project

Read:

- Project tree.
- Existing tool registry.
- Agent loop.
- Configuration.
- CLI.
- Permission system.
- Tests.
- Package configuration.

Step 2 — Plan integration

Identify the minimum files to modify.

Do not rebuild the project.

Step 3 — Implement run_command

Implement:

- Tool schema.
- Command executor.
- Permission handling.
- Safe policy.
- Structured result.
- Timeout.
- Tests.

Step 4 — Implement web_search

Implement:

- Provider abstraction.
- Tavily or another real provider.
- Configuration.
- API key handling.
- Result normalization.
- Tests.

Step 5 — Integrate into agent

Register both tools.

Update system prompt.

Preserve the existing agent loop.

Step 6 — Update CLI

Add configuration commands and tool display.

Preserve existing commands.

Step 7 — Update documentation

Explain setup and usage.

Step 8 — Run tests

Run the appropriate commands:

python -m compileall src
python -m unittest discover -s tests -v
pip install .
hiai --help

Run a harmless local command test.

Run a mocked web search test.

Step 9 — Review security

Check command execution, path handling, API key handling, and permission prompts.

Step 10 — Final response

Report:

1. Files changed.
2. New features.
3. Commands supported.
4. Web search provider.
5. Security behavior.
6. Tests run.
7. Known limitations.
8. How to configure and use the new features.

Do not claim tests passed unless they were actually executed.

---

FINAL INSTRUCTION

Implement this feature now in the existing HIAI repository.

Do not rebuild the entire project.

Do not provide only pseudocode.

Do not leave core functionality incomplete.

Add the two new tools:

run_command
web_search

Make them work with the existing OpenRouter agent loop, permission system, CLI, and project sandbox.

Preserve all existing features.

Build, test, and document the implementation.