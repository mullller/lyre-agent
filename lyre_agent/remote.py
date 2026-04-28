from __future__ import annotations

from dataclasses import asdict
import json
import subprocess
import sys

from lyre_agent.config import (
    RemoteConfig,
    RemoteHost,
    load_remote_config,
    save_remote_config,
)


# ── Remote host management ─────────────────────────────────────────────────


def remote_add(
    name: str,
    host: str,
    user: str = "root",
    port: int = 22,
    description: str = "",
) -> RemoteHost:
    """Add a remote host and persist to remotes.json."""
    cfg = load_remote_config()
    remote = RemoteHost(name=name, host=host, user=user, port=port, description=description)
    cfg.add(remote)
    save_remote_config(cfg)
    return remote


def remote_remove(name: str) -> bool:
    """Remove a remote host by name. Returns True if removed."""
    cfg = load_remote_config()
    if name not in cfg.remotes:
        return False
    cfg.remove(name)
    save_remote_config(cfg)
    return True


def remote_list() -> RemoteConfig:
    """List all configured remote hosts."""
    return load_remote_config()


def remote_get(name: str) -> RemoteHost | None:
    """Get a single remote host by name."""
    return load_remote_config().get(name)


# ── SSH helpers ─────────────────────────────────────────────────────────────


def _ssh_flags(host: RemoteHost) -> list[str]:
    """Build SSH command flags from RemoteHost."""
    flags = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=10",
    ]
    if host.port != 22:
        flags.extend(["-p", str(host.port)])
    flags.append(f"{host.user}@{host.host}")
    return flags


def _ssh_test(host: RemoteHost) -> tuple[bool, str]:
    """Test SSH connectivity and python3 availability on remote host."""
    # Test SSH connection
    cmd = _ssh_flags(host) + ["echo", "ssh-ok"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return False, f"SSH connection failed: {result.stderr.strip() or 'exit code ' + str(result.returncode)}"
        if "ssh-ok" not in result.stdout:
            return False, "SSH connected but unexpected response"
    except subprocess.TimeoutExpired:
        return False, "SSH connection timed out after 15s"
    except FileNotFoundError:
        return False, "ssh command not found on local machine"

    # Test python3
    cmd = _ssh_flags(host) + ["python3", "--version"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False, "python3 not found on remote host"
    except FileNotFoundError:
        return False, "ssh command not found"
    except subprocess.TimeoutExpired:
        return False, "python3 check timed out"

    return True, "OK"


def _ssh_exec(host: RemoteHost, remote_cmd: str, timeout: int = 180) -> tuple[int, str, str]:
    """Execute a command on remote host via SSH. Returns (exit_code, stdout, stderr)."""
    cmd = _ssh_flags(host) + [remote_cmd]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def _ssh_interactive(host: RemoteHost, remote_cmd: str) -> int:
    """Start an interactive SSH session with inherited stdio."""
    cmd = _ssh_flags(host) + ["-t", remote_cmd]
    proc = subprocess.run(cmd)
    return proc.returncode


# ── High-level remote operations ────────────────────────────────────────────


def remote_test(name: str) -> tuple[bool, str]:
    """Test connectivity to a remote host."""
    host = remote_get(name)
    if not host:
        return False, f"Remote '{name}' not found. Use 'lyre-agent remote add' first."
    return _ssh_test(host)


def remote_run(name: str, prompt: str, cwd: str = ".", timeout: int = 180) -> tuple[int, str, str]:
    """Run a one-shot task on the remote host via SSH."""
    host = remote_get(name)
    if not host:
        return 1, "", f"Remote '{name}' not found. Use 'lyre-agent remote add' first."

    # Build lyre-agent run command with safe quoting
    import shlex

    remote_cmd = f"cd {shlex.quote(cwd)} && python3 -m lyre_agent.cli run {shlex.quote(prompt)}"
    return _ssh_exec(host, remote_cmd, timeout=timeout)


def remote_chat(name: str, cwd: str = ".") -> int:
    """Start an interactive chat session on the remote host."""
    host = remote_get(name)
    if not host:
        print(f"Remote '{name}' not found. Use 'lyre-agent remote add' first.", file=sys.stderr)
        return 1

    import shlex

    remote_cmd = f"cd {shlex.quote(cwd)} && python3 -m lyre_agent.cli chat"
    return _ssh_interactive(host, remote_cmd)


def remote_config_show(name: str) -> tuple[int, str, str]:
    """Show remote host's lyre-agent config."""
    host = remote_get(name)
    if not host:
        return 1, "", f"Remote '{name}' not found."

    remote_cmd = "python3 -m lyre_agent.cli config-show"
    return _ssh_exec(host, remote_cmd)


def remote_model_show(name: str) -> tuple[int, str, str]:
    """Show remote host's active model."""
    host = remote_get(name)
    if not host:
        return 1, "", f"Remote '{name}' not found."

    remote_cmd = "python3 -m lyre_agent.cli model show"
    return _ssh_exec(host, remote_cmd)


def remote_tool_list(name: str) -> tuple[int, str, str]:
    """List tools on remote host."""
    host = remote_get(name)
    if not host:
        return 1, "", f"Remote '{name}' not found."

    remote_cmd = "python3 -m lyre_agent.cli tool-list"
    return _ssh_exec(host, remote_cmd)
