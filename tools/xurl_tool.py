#!/usr/bin/env python3
"""X/Twitter API tool backed by the official ``xurl`` CLI.

The tool is intentionally a thin, conservative wrapper: it never accepts inline
credentials, never runs verbose/trace mode, and returns JSON-ish command output
without reading ``~/.xurl`` into model context.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, List

from tools.registry import registry, tool_error

_FORBIDDEN_FLAGS = {
    "--bearer-token",
    "--consumer-key",
    "--consumer-secret",
    "--access-token",
    "--token-secret",
    "--client-id",
    "--client-secret",
    "--verbose",
    "-v",
}


def _candidate_paths() -> List[str]:
    paths: List[str] = []
    found = shutil.which("xurl")
    if found:
        paths.append(found)
    home = Path.home()
    paths.extend([
        str(home / ".local" / "bin" / "xurl"),
        "/opt/homebrew/bin/xurl",
        "/usr/local/bin/xurl",
    ])
    # Preserve order while deduplicating.
    return list(dict.fromkeys(paths))


def _xurl_bin() -> str | None:
    for path in _candidate_paths():
        if Path(path).is_file() and os.access(path, os.X_OK):
            return path
    return None


def check_xurl_requirements() -> bool:
    return _xurl_bin() is not None


def _parse_args(arguments: str | List[str]) -> List[str]:
    if isinstance(arguments, list):
        return [str(arg) for arg in arguments]
    return shlex.split(str(arguments or ""))


def _reject_unsafe(args: List[str]) -> str | None:
    for arg in args:
        flag = arg.split("=", 1)[0]
        if flag in _FORBIDDEN_FLAGS:
            return f"Forbidden xurl flag in agent sessions: {flag}"
    return None


def xurl(arguments: str | List[str], timeout_seconds: int = 60) -> str:
    """Run the official xurl CLI with safe argument handling."""
    binary = _xurl_bin()
    if not binary:
        return tool_error("xurl is not installed or not executable on PATH/~/.local/bin")

    try:
        args = _parse_args(arguments)
    except ValueError as exc:
        return tool_error(f"Could not parse xurl arguments: {exc}")

    unsafe = _reject_unsafe(args)
    if unsafe:
        return tool_error(unsafe)

    timeout = max(1, min(int(timeout_seconds or 60), 300))
    env = os.environ.copy()
    env["PATH"] = f"{Path(binary).parent}:{env.get('PATH', '')}"

    try:
        proc = subprocess.run(
            [binary, *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return tool_error(f"xurl timed out after {timeout} seconds")
    except Exception as exc:
        return tool_error(f"xurl failed to start: {exc}")

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    payload: dict[str, Any] = {
        "success": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": stdout[:20000],
        "stderr": stderr[:8000],
    }
    if stdout:
        try:
            payload["json"] = json.loads(stdout)
        except Exception:
            pass
    return json.dumps(payload, ensure_ascii=False)


XURL_SCHEMA = {
    "name": "xurl",
    "description": (
        "Run the official xurl CLI for X/Twitter API reads and writes. "
        "Arguments are passed as CLI args, e.g. 'whoami', 'followers -n 20', "
        "or '/2/users/me'. Never accepts inline secrets or verbose mode. "
        "Confirm user intent before write actions like post/reply/like/follow/DM."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "arguments": {
                "type": "string",
                "description": "xurl arguments as a shell-style string, excluding the leading 'xurl'.",
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Timeout in seconds, clamped to 1..300.",
                "default": 60,
            },
        },
        "required": ["arguments"],
    },
}


registry.register(
    name="xurl",
    toolset="xurl",
    schema=XURL_SCHEMA,
    handler=lambda args, **kw: xurl(
        arguments=args.get("arguments", ""),
        timeout_seconds=args.get("timeout_seconds", 60),
    ),
    check_fn=check_xurl_requirements,
    emoji="𝕏",
    max_result_size_chars=30_000,
)
