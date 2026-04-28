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
        print(f"{preset.alias}\t{preset.provider}\t{preset.name}\t{preset.description}")


def _switch_model(args) -> int:
    cfg = load_config(args.config)
    apply_model_switch(
        cfg,
        args.model,
        provider=args.provider,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
        config_path=args.config,
    )
    _print_model(args.config)
    return 0


def _chat(cwd: str | None = None, show_banner: bool = True) -> int:
    cfg = load_config()
    registry = default_registry()
    runtime = AgentRuntime(config=cfg, tools=registry)
    state = build_startup_state(cfg, registry, cwd=cwd)

    if show_banner:
        render_startup(state)

    while True:
        try:
            prompt = input("lyre ❯ ").strip()
        except EOFError:
            print()
            break
        if not prompt:
            continue
        if prompt in {"exit", "quit", "/exit", "/quit", "/q"}:
            break
        if prompt == "/help":
            _print_help()
            continue
        if prompt == "/status":
            render_status(state)
            continue
        if prompt == "/model":
            _print_model()
            continue
        if prompt == "/tools":
            for tool in registry.list():
                print(f"{tool.name}\t{tool.description}")
            continue
        if prompt == "/config":
            print(json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2))
            continue
        if prompt == "/clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue

        print_markdown(runtime.run(prompt, cwd=cwd))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        return _chat(cwd=args.cwd, show_banner=not (args.quiet or args.no_banner))

    if args.command == "version":
        print(f"lyre-agent {__version__}")
        return 0
    if args.command == "config-show":
        print(json.dumps(load_config().to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "tool-list":
        for tool in default_registry().list():
            print(f"{tool.name}\t{tool.description}")
        return 0
    if args.command == "model":
        if args.model_command in {None, "show"}:
            _print_model()
            return 0
        if args.model_command == "list":
            _list_models()
            return 0
        if args.model_command == "switch":
            return _switch_model(args)
    if args.command == "run":
        prompt = " ".join(args.prompt)
        print(AgentRuntime().run(prompt, cwd=args.cwd))
        return 0
    if args.command == "chat":
        show_banner = not (
            getattr(args, "quiet", False)
            or getattr(args, "no_banner", False)
            or os.environ.get("LYRE_NO_BANNER") == "1"
        )
        return _chat(cwd=args.cwd, show_banner=show_banner)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
