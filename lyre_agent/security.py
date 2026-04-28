from __future__ import annotations

import shlex

DENY_PATTERNS = [
    "rm -rf /",
    "mkfs",
    ":(){ :|:& };:",
]
HIGH_RISK_PREFIXES = ["rm", "sudo", "git push", "kubectl delete", "terraform apply"]
MEDIUM_RISK_PREFIXES = ["pip install", "npm install", "pnpm install", "docker build"]


def classify_command(command: str) -> str:
    normalized = " ".join(shlex.split(command)) if command.strip() else ""
    for pattern in DENY_PATTERNS:
        if pattern in normalized:
            return "deny"
    for prefix in HIGH_RISK_PREFIXES:
        if normalized == prefix or normalized.startswith(prefix + " "):
            return "high"
    for prefix in MEDIUM_RISK_PREFIXES:
        if normalized == prefix or normalized.startswith(prefix + " "):
            return "medium"
    return "low"
