from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil

from lyre_agent import __version__
from lyre_agent.config import AgentConfig
from lyre_agent.tools.registry import ToolRegistry


@dataclass(slots=True)
class StartupState:
    version: str
    profile: str
    workspace: str
    model: str
    tools: list[str]
    session: str
    safety: str
    warnings: list[str]


def build_startup_state(config: AgentConfig, registry: ToolRegistry, cwd: str | None = None) -> StartupState:
    workspace = str(Path(cwd or config.workspace.root).expanduser().resolve())
    model = f"{config.model.provider} / {config.model.name}"
    tools = registry.names()
    warnings: list[str] = []
    if config.model.api_key_env and not os.environ.get(config.model.api_key_env):
        warnings.append(f"missing env: {config.model.api_key_env}")
    return StartupState(
        version=__version__,
        profile=os.environ.get("LYRE_PROFILE", "default"),
        workspace=workspace,
        model=model,
        tools=tools,
        session="new",
        safety="approvals on",
        warnings=warnings,
    )


def _compact_path(path: str) -> str:
    home = str(Path.home())
    if path.startswith(home):
        return "~" + path[len(home):]
    return path


def render_startup(state: StartupState) -> None:
    try:
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
    except Exception:
        render_plain_startup(state)
        return

    console = Console()
    width = shutil.get_terminal_size((80, 24)).columns
    if width >= 74:
        logo = Text(
            "██╗     ██╗   ██╗██████╗ ███████╗\n"
            "██║     ╚██╗ ██╔╝██╔══██╗██╔════╝\n"
            "██║      ╚████╔╝ ██████╔╝█████╗  \n"
            "██║       ╚██╔╝  ██╔══██╗██╔══╝  \n"
            "███████╗   ██║   ██║  ██║███████╗\n"
            "╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝",
            style="bold cyan",
        )
        subtitle = Text("\nLocal-first CLI Agent for Developer Workflows", style="dim")
        title = Text.assemble(logo, subtitle)
    else:
        title = Text.assemble(("LYRE", "bold cyan"), ("\nlocal-first developer agent", "dim"))

    console.print(Panel(title, border_style="cyan", box=box.ROUNDED, padding=(1, 2)))

    table = Table(show_header=False, box=box.SIMPLE_HEAVY, border_style="bright_black", pad_edge=False)
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value", style="white")
    table.add_row("Version", state.version)
    table.add_row("Profile", state.profile)
    table.add_row("Workspace", _compact_path(state.workspace))
    table.add_row("Model", state.model)
    table.add_row("Tools", "  ".join(f"[green]{name} ✓[/green]" for name in state.tools))
    table.add_row("Session", state.session)
    table.add_row("Safety", f"[green]{state.safety}[/green]")
    if state.warnings:
        table.add_row("Warnings", "  ".join(f"[yellow]! {item}[/yellow]" for item in state.warnings))
    console.print(table)
    console.print("[dim]Type /help for commands, /status for details, /exit to quit.[/dim]\n")


def render_plain_startup(state: StartupState) -> None:
    print(f"Lyre Agent {state.version}")
    print("Local-first CLI Agent for Developer Workflows\n")
    print(f"Profile:   {state.profile}")
    print(f"Workspace: {_compact_path(state.workspace)}")
    print(f"Model:     {state.model}")
    print(f"Tools:     {', '.join(state.tools)}")
    print(f"Session:   {state.session}")
    print(f"Safety:    {state.safety}")
    for warning in state.warnings:
        print(f"Warning:   {warning}")
    print("\nType /help for commands, /status for details, /exit to quit.\n")


def render_status(state: StartupState) -> None:
    try:
        from rich.console import Console
        from rich.table import Table
    except Exception:
        render_plain_startup(state)
        return

    table = Table(title="Lyre Status", show_lines=False)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")
    table.add_row("Version", state.version)
    table.add_row("Profile", state.profile)
    table.add_row("Workspace", _compact_path(state.workspace))
    table.add_row("Model", state.model)
    table.add_row("Tools", ", ".join(state.tools))
    table.add_row("Session", state.session)
    table.add_row("Safety", state.safety)
    table.add_row("Warnings", ", ".join(state.warnings) if state.warnings else "none")
    Console().print(table)


def print_markdown(text: str) -> None:
    try:
        from rich.console import Console
        from rich.markdown import Markdown
    except Exception:
        print(text)
        return
    Console().print(Markdown(text))
