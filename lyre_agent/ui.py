from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

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


def _tool_chips(tools: list[str]) -> str:
    return "  ".join(f"[black on green] {name} [/black on green]" for name in tools)


def render_startup(state: StartupState) -> None:
    try:
        from rich import box
        from rich.align import Align
        from rich.console import Console, Group
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
    except Exception:
        render_plain_startup(state)
        return

    console = Console()

    title = Text.assemble(
        ("♪ ", "bold magenta"),
        ("Lyre", "bold white"),
        (" Agent", "bold cyan"),
        (f"  v{state.version}", "dim"),
    )
    subtitle = Text("local-first developer agent", style="dim")

    meta = Table.grid(expand=True)
    meta.add_column(ratio=1)
    meta.add_column(ratio=1)
    meta.add_row(
        f"[cyan]Workspace[/cyan]\n[white]{_compact_path(state.workspace)}[/white]",
        f"[cyan]Model[/cyan]\n[white]{state.model}[/white]",
    )
    meta.add_row(
        f"[cyan]Profile[/cyan]\n[white]{state.profile}[/white]",
        f"[cyan]Session[/cyan]\n[white]{state.session}[/white]",
    )
    meta.add_row(
        f"[cyan]Safety[/cyan]\n[green]{state.safety}[/green]",
        f"[cyan]Tools[/cyan]\n{_tool_chips(state.tools)}",
    )

    body_items = [
        Align.left(title),
        Align.left(subtitle),
        "",
        meta,
    ]
    if state.warnings:
        body_items.extend(["", "\n".join(f"[yellow]⚠ {warning}[/yellow]" for warning in state.warnings)])

    panel = Panel(
        Group(*body_items),
        title="[dim]startup[/dim]",
        subtitle="[dim]/help commands · /status details · /exit quit[/dim]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def render_plain_startup(state: StartupState) -> None:
    print(f"♪ Lyre Agent v{state.version}")
    print("local-first developer agent\n")
    print(f"Workspace: {_compact_path(state.workspace)}")
    print(f"Model:     {state.model}")
    print(f"Profile:   {state.profile}")
    print(f"Session:   {state.session}")
    print(f"Safety:    {state.safety}")
    print(f"Tools:     {', '.join(state.tools)}")
    for warning in state.warnings:
        print(f"Warning:   {warning}")
    print("\n/help commands · /status details · /exit quit\n")


def render_status(state: StartupState) -> None:
    try:
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
    except Exception:
        render_plain_startup(state)
        return

    table = Table(show_header=False, box=None, pad_edge=False)
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
    Console().print(Panel(table, title="[bold cyan]Lyre Status[/bold cyan]", border_style="cyan", box=box.ROUNDED))


def print_markdown(text: str) -> None:
    try:
        from rich.console import Console
        from rich.markdown import Markdown
    except Exception:
        print(text)
        return
    Console().print(Markdown(text))
