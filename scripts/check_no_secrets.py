#!/usr/bin/env python3
"""Small repository scanner that blocks common env/token/credential leaks.

This intentionally complements detect-secrets/gitleaks with simple project-specific rules.
It is not a replacement for a real secret scanner.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "reports",
}

SKIP_FILES = {
    ".secrets.baseline",
    ".env.example",
    "check_no_secrets.py",
}

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
    ".cfg",
    ".sh",
    ".ps1",
    ".html",
    ".css",
}

PATTERNS = [
    re.compile(
        r"(?i)(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+=]{16,}"
    ),
    re.compile(r"(?i)jira[_-]?(api[_-]?)?token\s*[:=]\s*['\"]?\S{8,}"),
    re.compile(r"(?i)authorization:\s*(bearer|basic)\s+[A-Za-z0-9_\-./+=:]{12,}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
]

ALLOWLIST_SUBSTRINGS = [
    "your_api_token",
    "JIRA_API_TOKEN=",
    "JIRA_BEARER_TOKEN=",
    "${{ secrets.GITHUB_TOKEN }}",
    "example.com",
    "token env",
]


def is_skipped(path: Path) -> bool:
    if path.name in SKIP_FILES:
        return True
    return any(part in SKIP_DIRS for part in path.parts)


def is_text_file(path: Path) -> bool:
    return path.suffix in TEXT_EXTENSIONS or path.name in {"LICENSE", "AGENTS.md", "README.md"}


def main() -> int:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if not path.is_file() or is_skipped(rel) or not is_text_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if any(allowed in line for allowed in ALLOWLIST_SUBSTRINGS):
                continue
            for pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(
                        f"{rel}:{line_no}: possible secret/env leak: {line.strip()[:120]}"
                    )
                    break
    if findings:
        print("Secret/env scan failed:\n")
        print("\n".join(findings))
        return 1
    print("Secret/env scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
