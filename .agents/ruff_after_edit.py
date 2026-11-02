"""Run `ruff check --fix` then `ruff format` on a Python file an agent just edited.

Wired up as a Cursor `afterFileEdit` hook (.cursor/hooks.json) and a Claude Code
`PostToolUse` hook (.claude/settings.json). Both pipe a JSON payload on stdin:
Cursor puts the path in `file_path`, Claude Code in `tool_input.file_path`.

Never exits with code 2 (the only code either tool treats as blocking), so a
lint/format problem or a malformed payload can't stop the agent.
"""

import contextlib
import json
import subprocess
import sys
from pathlib import Path


def edited_python_file(payload: object) -> Path | None:
    if not isinstance(payload, dict):
        return None
    raw = payload.get('file_path')
    tool_input = payload.get('tool_input')
    if raw is None and isinstance(tool_input, dict):
        raw = tool_input.get('file_path')
    if not isinstance(raw, str):
        return None
    path = Path(raw)
    return path if path.suffix == '.py' and path.is_file() else None


def main() -> None:
    path = edited_python_file(json.load(sys.stdin))
    if path is None:
        return
    for args in (['check', '--fix', '--quiet'], ['format', '--quiet']):
        subprocess.run(
            [sys.executable, '-m', 'ruff', *args, str(path)],
            capture_output=True,
            check=False,
            timeout=20,
        )


if __name__ == '__main__':
    with contextlib.suppress(ValueError, OSError, subprocess.SubprocessError):
        main()
    sys.exit(0)
