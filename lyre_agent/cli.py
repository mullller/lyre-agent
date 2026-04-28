from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
import sys

from lyre_agent import __version__
from lyre_agent.config import get_config_path, load_config
from lyre_agent.models import apply_model_switch, list_model_presets
from lyre_agent.runtime import AgentRuntime
from lyre_agent.tools.registry import default_registry
from lyre_agent.ui import build_startup_state, print_markdown, render_startup, render_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lyre-agent", description="Local-first CLI Agent")
    parser.add_argument("--quiet", action="store_true", help="suppress banner and non-essential output")
    parser.add_argument("--no-banner", action="store_true", help="do not render startup TUI")
    parser.add_argument("--cwd", default=None, help="working directory")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="print version")
    sub.add_parser("config-show", help="print resolved config")
    sub.add_parser("tool-list", help="list available tools")

    model = sub.add_parser("model", help="show, list or switch model")
    model_sub = model.add_subparsers(dest="model_command")
    model_sub.add_parser("show", help="show active model")
    model_sub.add_parser("list", help="list model presets")
    switch = model_sub.add_parser("switch", help="switch active model")
    switch.add_argument("model", help="preset alias or raw model name")
    switch.add_argument("--provider", default=None, help="provider override, e.g. openai-compatible")
    switch.add_argument("--base-url", default=None, help="OpenAI-compatible base URL")
    switch.add_argument("--api-key-env", default=None, help="environment variable containing API key")
    switch.add_argument("--config", default=None, help="config path override")

    run = sub.add_parser("run", help="run a one-shot task")
    run.add_argument("prompt", nargs="+", help="task prompt")
    run.add_argument("--cwd", default=None, help="working directory")

    chat = sub.add_parser("chat", help="start interactive chat")
    chat.add_argument("--no-banner", action="store_true", help="do not render startup TUI")
    chat.add_argument("--quiet", action="store_true", help="suppress banner")
    chat.add_argument("--cwd", default=None, help="working directory")

    # ── remote subcommand ───────────────────────────────────────────────
    remote = sub.add_parser("remote", help="manage remote Lyre Agent hosts")
    remote_sub = remote.add_subparsers(dest="remote_command")

    # remote add
    remote_add = remote_sub.add_parser("add", help="add a remote host")
    remote_add.add_argument("name", help="alias for the remote host")
    remote_add.add_argument("--host", required=True, help="hostname or IP")
    remote_add.add_argument("--user", default="root", help="SSH user (default: root)")
    remote_add.add_argument("--port", type=int, default=22, help="SSH port (default: 22)")
    remote_add.add_argument("--description", default="", help="human-friendly description")

    # remote remove
    remote_rm = remote_sub.add_parser("remove", help="remove a remote host")
    remote_rm.add_argument("name", help="alias of the remote to remove")

    # remote list
    remote_sub.add_parser("list", help="list configured remote hosts")

    # remote test
    remote_test = remote_sub.add_parser("test", help="test SSH connectivity to a remote host")
    remote_test.add_argument("name", help="alias of the remote to test")

    # remote run
    remote_run = remote_sub.add_parser("run", help="run a one-shot task on a remote host")
    remote_run.add_argument("name", help="alias of the remote host")
    remote_run.add_argument("prompt", nargs="+", help="task prompt")
    remote_run.add_argument("--cwd", default=".", help="working directory on remote")

    # remote chat
    remote_chat = remote_sub.add_parser("chat", help="start interactive chat on a remote host")
    remote_chat.add_argument("name", help="alias of the remote host")
    remote_chat.add_argument("--cwd", default=".", help="working directory on remote")

    # remote config-show
    remote_config = remote_sub.add_parser("config-show", help="show remote host config")
    remote_config.add_argument("name", help="alias of the remote host")

    # remote model-show
    remote_model = remote_sub.add_parser("model-show", help="show remote host active model")
    remote_model.add_argument("name", help="alias of the remote host")

    # remote tool-list
    remote_tools = remote_sub.add_parser("tool-list", help="list tools on remote host")
    remote_tools.add_argument("name", help="alias of the remote host")

    return parser


def _print_help() -> None:
    print(
        """Available commands:
  /help      Show this help
  /status    Show runtime status
  /model     Show active model
  /tools     List enabled tools
  /config    Print resolved config
  /clear     Clear the terminal
  /exit      Exit chat
""".strip()
    )


def _print_model(config_path: str | None = None) -> None:
    cfg = load_config(config_path)
    print(json.dumps({"model": asdict(cfg.model), "config_path": str(get_config_path(config_path))}, ensure_ascii=False, indent=2))


def _list_models() -> None:
    for preset in list_model_presets():
        print(f"  {preset.alias:<30} {preset.description}")


def _switch_model(args) -> None:
    cfg = load_config(args.config)
    cfg = apply_model_switch(
        cfg,
        args.model,
        provider=args.provider,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
        config_path=args.config,
    )
    _print_model(args.config)


def _list_tools() -> None:
    for tool in default_registry().list():
        print(f"  {tool.name}: {tool.description}")


def _run(args) -> None:
    runtime = AgentRuntime()
    workdir = args.cwd or os.getcwd()
    result = runtime.run(" ".join(args.prompt), cwd=workdir)
    print(result)


def _chat(args) -> None:
    quiet = args.quiet or os.environ.get("LYRE_NO_BANNER")
    no_banner = args.no_banner or quiet
    if not no_banner:
        cfg = load_config()
        state = build_startup_state(cfg, default_registry(), args.cwd)
        render_startup(state)

    print("Lyre Agent chat — type /help for commands, /exit to quit.")
    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            cmd_parts = user_input.split(maxsplit=1)
            cmd = cmd_parts[0].lower()
            if cmd == "/exit":
                print("Bye.")
                break
            elif cmd == "/help":
                _print_help()
            elif cmd == "/model":
                _print_model()
            elif cmd == "/tools":
                _list_tools()
            elif cmd == "/config":
                cfg = load_config()
                print(json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2))
            elif cmd == "/status":
                render_status()
            elif cmd == "/clear":
                os.system("clear" if os.name != "nt" else "cls")
            else:
                print(f"Unknown command: {cmd}. Type /help for available commands.")
        else:
            runtime = AgentRuntime()
            workdir = args.cwd or os.getcwd()
            result = runtime.run(user_input, cwd=workdir)
            print(result)


# ── Remote command handlers ─────────────────────────────────────────────────


def _remote_add(args) -> None:
    from lyre_agent.remote import remote_add

    remote = remote_add(
        name=args.name,
        host=args.host,
        user=args.user,
        port=args.port,
        description=args.description,
    )
    print(json.dumps(remote.to_dict(), ensure_ascii=False, indent=2))
    print(f"✓ Remote '{args.name}' added.")


def _remote_remove(args) -> None:
    from lyre_agent.remote import remote_remove

    if remote_remove(args.name):
        print(f"✓ Remote '{args.name}' removed.")
    else:
        print(f"Remote '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)


def _remote_list(args) -> None:
    from lyre_agent.remote import remote_list

    cfg = remote_list()
    if not cfg.remotes:
        print("No remote hosts configured. Use 'lyre-agent remote add' to add one.")
        return
    for name, host in cfg.remotes.items():
        desc = f" — {host.description}" if host.description else ""
        print(f"  {name}: {host.user}@{host.host}:{host.port}{desc}")


def _remote_test(args) -> None:
    from lyre_agent.remote import remote_test

    ok, msg = remote_test(args.name)
    if ok:
        print(f"✓ Remote '{args.name}' is reachable.")
    else:
        print(f"✗ Remote '{args.name}' test failed: {msg}", file=sys.stderr)
        sys.exit(1)


def _remote_run(args) -> None:
    from lyre_agent.remote import remote_run

    prompt = " ".join(args.prompt)
    exit_code, stdout, stderr = remote_run(args.name, prompt, cwd=args.cwd)
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    if exit_code != 0:
        sys.exit(exit_code)


def _remote_chat(args) -> None:
    from lyre_agent.remote import remote_chat

    sys.exit(remote_chat(args.name, cwd=args.cwd))


def _remote_config_show(args) -> None:
    from lyre_agent.remote import remote_config_show

    exit_code, stdout, stderr = remote_config_show(args.name)
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    sys.exit(exit_code)


def _remote_model_show(args) -> None:
    from lyre_agent.remote import remote_model_show

    exit_code, stdout, stderr = remote_model_show(args.name)
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    sys.exit(exit_code)


def _remote_tool_list(args) -> None:
    from lyre_agent.remote import remote_tool_list

    exit_code, stdout, stderr = remote_tool_list(args.name)
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    sys.exit(exit_code)


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "version":
        print(f"lyre-agent {__version__}")
    elif args.command == "config-show":
        cfg = load_config()
        print(json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "tool-list":
        _list_tools()
    elif args.command == "model":
        if args.model_command == "show":
            _print_model()
        elif args.model_command == "list":
            _list_models()
        elif args.model_command == "switch":
            _switch_model(args)
        else:
            parser.parse_args(["model", "--help"])
    elif args.command == "run":
        _run(args)
    elif args.command == "chat":
        _chat(args)
    elif args.command == "remote":
        if args.remote_command == "add":
            _remote_add(args)
        elif args.remote_command == "remove":
            _remote_remove(args)
        elif args.remote_command == "list":
            _remote_list(args)
        elif args.remote_command == "test":
            _remote_test(args)
        elif args.remote_command == "run":
            _remote_run(args)
        elif args.remote_command == "chat":
            _remote_chat(args)
        elif args.remote_command == "config-show":
            _remote_config_show(args)
        elif args.remote_command == "model-show":
            _remote_model_show(args)
        elif args.remote_command == "tool-list":
            _remote_tool_list(args)
        else:
            parser.parse_args(["remote", "--help"])
    else:
        # Default: interactive chat
        _chat(args)


if __name__ == "__main__":
    main()
