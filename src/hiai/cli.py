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
    show_config,
)
from hiai.exceptions import APIKeyError, ConfigError, HIAIError
from hiai.models import AppConfig
from hiai.terminal import (
    error,
    info,
    print_banner,
    print_config_display,
    prompt_api_key,
    success,
    warning,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="hiai",
        description="HIAI — Local AI Coding Agent powered by OpenRouter",
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
    key = prompt_api_key()
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


def cmd_config_reset() -> None:
    """Reset configuration."""
    reset_config()
    success("Configuration reset to defaults.")


def cmd_models() -> None:
    """Handle models subcommand."""
    config = load_config()
    print(f"  Current model: {config.model}")
    print(f"  Base URL:      {config.base_url}")
    print()
    print("  To change model:")
    print("    hiai config set-model <model-id>")
    print()
    print("  Examples:")
    print("    openrouter/free")
    print("    deepseek/deepseek-chat-v3-0324:free")
    print("    google/gemini-2.5-flash")


def run_interactive(agent: Agent, project_dir: Path) -> None:
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
            cmd = user_input.lower()

            if cmd in ("/exit", "/quit"):
                info("Goodbye!")
                break
            elif cmd == "/help":
                _show_help()
            elif cmd == "/clear":
                agent.clear_history()
                success("Conversation cleared.")
            elif cmd == "/model":
                print(f"  Model: {agent.config.model}")
            elif cmd == "/project":
                print(f"  Project: {project_dir}")
            elif cmd == "/status":
                status = agent.get_status()
                for k, v in status.items():
                    print(f"  {k}: {v}")
            else:
                warning(f"Unknown command: {cmd}. Type /help for available commands.")
            continue

        try:
            response = agent.chat(user_input)
            if response:
                print()
                print(response)
        except HIAIError as e:
            error(str(e))
        except KeyboardInterrupt:
            print()
            info("Interrupted.")
        except Exception as e:
            error(f"Unexpected error: {e}")


def _show_help() -> None:
    """Show available commands."""
    print("""
  Commands:
    /help     Show this help message
    /clear    Clear conversation history
    /model    Show current model
    /project  Show project root
    /status   Show session information
    /exit     Exit HIAI
    /quit     Exit HIAI
""")


def run_one_shot(agent: Agent, prompt: str) -> None:
    """Run a single prompt and print the response."""
    try:
        response = agent.chat(prompt)
        if response:
            print(response)
    except HIAIError as e:
        error(str(e))
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        _run_main_mode(sys.argv[1:])
        return

    if sys.argv[1] == "config":
        _run_config(sys.argv[2:])
        return
    elif sys.argv[1] == "models":
        cmd_models()
        return

    _run_main_mode(sys.argv[1:])


def _run_config(args: list[str]) -> None:
    """Handle config subcommand."""
    if not args:
        cmd_config_show()
        return

    sub = args[0]

    if sub == "show":
        cmd_config_show()
    elif sub == "set-key":
        cmd_config_set_key()
    elif sub == "set-model":
        value = args[1] if len(args) > 1 else ""
        cmd_config_set_model(value)
    elif sub == "set-base-url":
        value = args[1] if len(args) > 1 else ""
        cmd_config_set_base_url(value)
    elif sub == "reset":
        cmd_config_reset()
    else:
        error(f"Unknown config command: {sub}")
        sys.exit(1)


def _run_main_mode(args: list[str]) -> None:
    """Handle main interactive/one-shot mode."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    project_dir = Path(parsed.project).resolve()
    if not project_dir.exists():
        error(f"Project directory does not exist: {project_dir}")
        sys.exit(1)

    config = load_config()

    if parsed.model:
        config.model = parsed.model

    try:
        require_api_key(config)
    except APIKeyError as e:
        error(str(e))
        sys.exit(1)

    agent = Agent(
        config=config,
        project_root=project_dir,
        auto_approve=parsed.yes,
    )

    if parsed.prompt:
        prompt_text = " ".join(parsed.prompt)
        run_one_shot(agent, prompt_text)
    else:
        try:
            run_interactive(agent, project_dir)
        except KeyboardInterrupt:
            print()
            info("Goodbye!")
        except Exception as e:
            error(f"Fatal error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
