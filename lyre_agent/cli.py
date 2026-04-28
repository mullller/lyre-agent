from __future__ import annotations

import argparse
import json
import sys

from lyre_agent import __version__
from lyre_agent.config import load_config
from lyre_agent.runtime import AgentRuntime
from lyre_agent.tools.registry import default_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lyre-agent", description="Local-first CLI Agent")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="print version")
    sub.add_parser("config-show", help="print resolved config")
    sub.add_parser("tool-list", help="list available tools")

    run = sub.add_parser("run", help="run a one-shot task")
    run.add_argument("prompt", nargs="+", help="task prompt")
    run.add_argument("--cwd", default=None, help="working directory")

    sub.add_parser("chat", help="start interactive chat")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
    if args.command == "run":
        prompt = " ".join(args.prompt)
        print(AgentRuntime().run(prompt, cwd=args.cwd))
        return 0
    if args.command == "chat":
        runtime = AgentRuntime()
        print("lyre-agent chat. Type 'exit' or 'quit' to leave.")
        while True:
            try:
                prompt = input("> ").strip()
            except EOFError:
                break
            if prompt in {"exit", "quit"}:
                break
            if prompt:
                print(runtime.run(prompt))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
