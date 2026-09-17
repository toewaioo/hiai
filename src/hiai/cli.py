"""CLI entry point for HIAI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hiai import __version__
from hiai.agent import Agent
from hiai.config import (
    load_config,
    require_api_key,
    reset_config,
    save_config,
    set_api_key,
    set_base_url,
    set_model,
    set_provider,
    set_rate_limit,
    show_config,
)
from hiai.exceptions import APIKeyError, ConfigError, HIAIError
from hiai.markdown import print_markdown
from hiai.models import AppConfig
from hiai.terminal import (
    _c,
    error,
    info,
    print_banner,
    print_config_display,
    print_stats,
    prompt_api_key,
    success,
    warning,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the default (chat/one-shot) mode."""
    parser = argparse.ArgumentParser(
        prog="hiai",
        description="HIAI — Local AI Coding Agent (OpenRouter & Groq)",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"HIAI {__version__}",
    )
    parser.add_argument(
        "--project", "-p",
        type=str,
        default=".",
        help="Project directory to work in",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="Override model for this invocation",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        default=False,
        help="Auto-approve file writes without confirmation",
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        default=False,
        help="Resume the previous conversation from .hiai/session.json",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        default=False,
        help="Stream responses token-by-token as they arrive",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        default=False,
        help="Suppress non-essential output (stats, detail lines)",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="One-shot prompt (if provided, runs and exits)",
    )
    return parser


def cmd_config_show() -> None:
    """Show configuration."""
    config = show_config()
    print_config_display(config)


def cmd_config_set_key() -> None:
    """Set API key interactively."""
    config = load_config()
    key = prompt_api_key(config.provider)
    if key:
        set_api_key(key)
        success("API key saved.")
    else:
        warning("No key entered.")


def cmd_config_set_model(model: str) -> None:
    """Set model."""
    if not model:
        error("Usage: hiai config set-model <model>")
        return
    set_model(model)
    success(f"Model set to: {model}")


def cmd_config_set_base_url(url: str) -> None:
    """Set base URL."""
    if not url:
        error("Usage: hiai config set-base-url <url>")
        return
    set_base_url(url)
    success(f"Base URL set to: {url}")


def cmd_config_set_provider(provider: str) -> None:
    """Set provider."""
    if not provider:
        error("Usage: hiai config set-provider <openrouter|groq>")
        return
    try:
        set_provider(provider)
        success(f"Provider set to: {provider}")
    except ConfigError as e:
        error(str(e))


def cmd_config_reset() -> None:
    """Reset configuration."""
    reset_config()
    success("Configuration reset to defaults.")


def cmd_config_set_search_provider(provider: str) -> None:
    """Set search provider."""
    if not provider:
        error("Usage: hiai config set-search-provider <provider>")
        return
    from hiai.config import set_search_provider as _set
    _set(provider)
    success(f"Search provider set to: {provider}")


def cmd_config_set_search_key() -> None:
    """Set search API key interactively."""
    from hiai.terminal import _c
    print(_c("yellow", "Enter your Tavily API key (or other search provider key):"))
    try:
        key = input(_c("bold", "API Key: ")).strip()
    except (EOFError, KeyboardInterrupt):
        key = ""
    if key:
        from hiai.config import set_search_key as _set
        _set(key)
        success("Search API key saved.")
    else:
        warning("No key entered.")


def cmd_config_set_search_max_results(value: str) -> None:
    """Set max search results."""
    try:
        n = int(value)
    except (ValueError, TypeError):
        error("Usage: hiai config set-search-max-results <1-10>")
        return
    from hiai.config import set_search_max_results as _set
    _set(n)
    success(f"Max search results set to: {n}")


def cmd_config_set_rate_limit(value: str) -> None:
    """Set max API requests per minute."""
    try:
        n = int(value)
    except (ValueError, TypeError):
        error("Usage: hiai config set-rate-limit <1-100>")
        return
    set_rate_limit(n)
    success(f"Rate limit set to: {n}/min")


def cmd_models() -> None:
    """Handle models subcommand."""
    config = load_config()
    print(f"  Current provider: {config.provider}")
    print(f"  Current model: {config.model}")
    print(f"  Base URL:      {config.base_url}")
    print()
    print("  To change provider:")
    print("    hiai config set-provider <openrouter|groq>")
    print()
    print("  To change model:")
    print("    hiai config set-model <model-id>")
    print()
    print("  Examples (OpenRouter):")
    print("    openrouter/free")
    print("    deepseek/deepseek-chat-v3-0324:free")
    print("    google/gemini-2.5-flash")
    print()
    print("  Examples (Groq):")
    print("    llama-3.3-70b-versatile")
    print("    llama-3.1-8b-instant")
    print("    mixtral-8x7b-32768")


def run_interactive(agent: Agent, project_dir: Path, quiet: bool = False) -> None:
    """Run interactive chat mode."""
    print_banner(str(project_dir), agent.config.model)

    while True:
        try:
            user_input = input("\033[1m\033[36mhiai>\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            info("Goodbye!")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            handled = _handle_slash_command(user_input, agent, project_dir, quiet)
            if handled:
                continue

        try:
            response = agent.chat(user_input)
            if response:
                if agent.stream:
                    print()  # newline after streamed tokens
                else:
                    print()
                    print_markdown(response)
            if not quiet:
                print_stats(agent._last_tokens_in, agent._last_tokens_out, agent._last_turn_elapsed)
        except HIAIError as e:
            error(str(e))
        except KeyboardInterrupt:
            print()
            info("Interrupted.")
        except Exception as e:
            error(f"Unexpected error: {e}")


def _handle_slash_command(user_input: str, agent: Agent, project_dir: Path, quiet: bool) -> bool:
    """Handle an interactive slash command. Returns True if handled."""
    parts = user_input.split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("/exit", "/quit"):
        info("Goodbye!")
        # Persist the session on exit for easy resume
        try:
            agent.save_history()
        except Exception:
            pass
        sys.exit(0)
    elif cmd == "/help":
        _show_help()
    elif cmd == "/clear":
        agent.clear_history()
        success("Conversation cleared.")
    elif cmd == "/model":
        if arg:
            agent.config.model = arg
            success(f"Model set to: {arg}")
        else:
            print(f"  Model: {agent.config.model}")
    elif cmd == "/project":
        print(f"  Project: {project_dir}")
    elif cmd == "/status":
        status = agent.get_status()
        for k, v in status.items():
            print(f"  {k}: {v}")
    elif cmd == "/tools":
        _show_tools()
    elif cmd == "/save":
        path = arg if arg else None
        try:
            saved = agent.save_history(path)
            success(f"History saved to {saved}")
        except Exception as e:
            error(f"Could not save history: {e}")
    elif cmd == "/load":
        path = arg if arg else None
        if agent.load_history(path):
            success("History loaded.")
        else:
            warning("No saved history found (or unreadable).")
    elif cmd == "/history":
        sessions = agent.list_history()
        if not sessions:
            info("No saved sessions.")
        else:
            print(_c("bold", "Saved sessions:"))
            for s in sessions:
                try:
                    size = s.stat().st_size
                    print(f"  {_c('cyan', s.name)}  ({size} bytes)")
                except OSError:
                    print(f"  {_c('cyan', s.name)}")
    elif cmd == "/retry":
        info("Re-running last turn...")
        try:
            response = agent.retry_last_turn()
            if response is None:
                warning("No previous turn to retry.")
            else:
                print()
                print_markdown(response)
                if not quiet:
                    print_stats(agent._last_tokens_in, agent._last_tokens_out, agent._last_turn_elapsed)
        except HIAIError as e:
            error(str(e))
        except Exception as e:
            error(f"Retry failed: {e}")
    else:
        warning(f"Unknown command: {cmd}. Type /help for available commands.")
    return True


def _show_help() -> None:
    """Show available commands."""
    print("""
  Commands:
    /help            Show this help message
    /clear           Clear conversation history
    /model [name]    Show or set the current model
    /project         Show project root
    /status          Show session information
    /tools           Show available AI tools
    /save [path]     Save conversation history (default: .hiai/session.json)
    /load [path]     Load conversation history
    /history         List saved sessions
    /retry           Re-run the last user turn
    /exit            Exit HIAI (saves session for --resume)
    /quit            Exit HIAI (saves session for --resume)
""")


def _show_tools() -> None:
    """Show available AI tools."""
    from hiai.tools.schemas import get_tool_definitions

    tools = get_tool_definitions()
    print(_c("bold", "Available tools:"))
    print()
    for tool in tools:
        func = tool.get("function", {})
        name = func.get("name", "?")
        desc = func.get("description", "")
        print(f"  {_c('green', '✓')} {_c('cyan', name)}")
        print(f"    {_c('dim', desc)}")
    print()


def run_one_shot(agent: Agent, prompt: str, quiet: bool = False) -> None:
    """Run a single prompt and print the response."""
    try:
        response = agent.chat(prompt)
        if response:
            if agent.stream:
                print()  # newline after streamed tokens
            else:
                print_markdown(response)
            if not quiet:
                print_stats(agent._last_tokens_in, agent._last_tokens_out, agent._last_turn_elapsed)
    except HIAIError as e:
        error(str(e))
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        sys.exit(1)


def build_config_parser() -> argparse.ArgumentParser:
    """Build the `hiai config` subparser tree."""
    parser = argparse.ArgumentParser(
        prog="hiai config",
        description="View and edit HIAI configuration.",
    )
    sub = parser.add_subparsers(dest="config_command", required=False)

    sub.add_parser("show", help="Show current configuration")
    sub.add_parser("set-key", help="Set the AI provider API key interactively")
    p = sub.add_parser("set-model", help="Set the model identifier")
    p.add_argument("model", help="Model identifier, e.g. openrouter/free")
    p = sub.add_parser("set-provider", help="Set the provider (openrouter|groq)")
    p.add_argument("provider", help="openrouter or groq")
    p = sub.add_parser("set-base-url", help="Set the API base URL")
    p.add_argument("url", help="Base URL, e.g. https://openrouter.ai/api/v1")
    p = sub.add_parser("set-search-provider", help="Set the web search provider")
    p.add_argument("provider", help="Search provider name, e.g. tavily")
    sub.add_parser("set-search-key", help="Set the search API key interactively")
    p = sub.add_parser("set-search-max-results", help="Set max web search results (1-10)")
    p.add_argument("value", type=int, help="Maximum number of results (1-10)")
    p = sub.add_parser("set-rate-limit", help="Set max API requests per minute (1-100)")
    p.add_argument("value", type=int, help="Requests per minute (1-100)")
    sub.add_parser("reset", help="Reset configuration to defaults")
    return parser


_CONFIG_DISPATCH = {
    "show": lambda a: cmd_config_show(),
    "set-key": lambda a: cmd_config_set_key(),
    "set-model": lambda a: cmd_config_set_model(a.model),
    "set-provider": lambda a: cmd_config_set_provider(a.provider),
    "set-base-url": lambda a: cmd_config_set_base_url(a.url),
    "set-search-provider": lambda a: cmd_config_set_search_provider(a.provider),
    "set-search-key": lambda a: cmd_config_set_search_key(),
    "set-search-max-results": lambda a: cmd_config_set_search_max_results(str(a.value)),
    "set-rate-limit": lambda a: cmd_config_set_rate_limit(str(a.value)),
    "reset": lambda a: cmd_config_reset(),
}


def _run_config(args: list[str]) -> None:
    """Handle the `hiai config` subcommand tree with proper argparse."""
    parser = build_config_parser()
    parsed = parser.parse_args(args)
    sub = parsed.config_command or "show"
    handler = _CONFIG_DISPATCH.get(sub)
    if handler is None:
        error(f"Unknown config command: {sub}")
        sys.exit(1)
    handler(parsed)


def _run_models(args: list[str]) -> None:
    """Handle the `hiai models` subcommand."""
    # Accept --help/-h via a tiny parser; otherwise just show models.
    parser = argparse.ArgumentParser(prog="hiai models", description="Show current model and examples.")
    parser.parse_args(args)
    cmd_models()


def main() -> None:
    """Main entry point.

    Routing:
      hiai            -> interactive chat (default mode)
      hiai <prompt>   -> one-shot prompt (default mode)
      hiai config ... -> configuration subcommands
      hiai models     -> show model info
    """
    argv = sys.argv[1:]

    if not argv:
        _run_main_mode(argv)
        return

    first = argv[0]
    if first == "config":
        _run_config(argv[1:])
        return
    if first == "models":
        _run_models(argv[1:])
        return

    _run_main_mode(argv)


def _run_main_mode(args: list[str]) -> None:
    """Handle main interactive/one-shot mode."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    project_dir = Path(parsed.project).resolve()
    if not project_dir.exists():
        error(f"Project directory does not exist: {project_dir}")
        sys.exit(1)

    config = load_config(project_dir)

    if parsed.model:
        config.model = parsed.model

    try:
        require_api_key(config)
    except APIKeyError as e:
        error(str(e))
        sys.exit(1)

    # Enable streaming automatically when the user asks for it OR when stdout
    # is a TTY and the user hasn't passed --quiet (responsive interactive UX).
    stream = bool(parsed.stream) or (sys.stdout.isatty() and not parsed.quiet and not parsed.prompt)

    agent = Agent(
        config=config,
        project_root=project_dir,
        auto_approve=parsed.yes,
        stream=stream,
    )

    if parsed.resume:
        if agent.load_history():
            success("Resumed previous conversation.")
        else:
            info("No saved session found; starting fresh.")

    if parsed.prompt:
        prompt_text = " ".join(parsed.prompt)
        run_one_shot(agent, prompt_text, quiet=parsed.quiet)
    else:
        try:
            run_interactive(agent, project_dir, quiet=parsed.quiet)
        except KeyboardInterrupt:
            print()
            info("Goodbye!")
        except Exception as e:
            error(f"Fatal error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
