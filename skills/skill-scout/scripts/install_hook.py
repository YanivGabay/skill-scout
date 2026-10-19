#!/usr/bin/env python3
"""Register (or remove) the skill-scout SessionStart hook in ~/.claude/settings.json.

Usage: install_hook.py [--uninstall]
Idempotent. Writes a timestamped backup before changing the file.
"""
import json
import shutil
import sys
import time
from pathlib import Path

SETTINGS = Path("~/.claude/settings.json").expanduser()
CACHE_SCRIPT = Path(__file__).resolve().parent / "cache.py"
COMMAND = f'python3 "{CACHE_SCRIPT}" check'
MARKER = "skill-scout"


def main():
    settings = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
    groups = settings.setdefault("hooks", {}).setdefault("SessionStart", [])

    groups[:] = [g for g in groups
                 if not any(MARKER in h.get("command", "") and "cache.py" in h.get("command", "")
                            for h in g.get("hooks", []))]
    if "--uninstall" not in sys.argv:
        groups.append({"matcher": "startup",
                       "hooks": [{"type": "command", "command": COMMAND, "timeout": 10}]})
    if not groups:
        settings["hooks"].pop("SessionStart")

    if SETTINGS.exists():
        shutil.copy2(SETTINGS, SETTINGS.with_name(f"settings.json.bak-{time.strftime('%Y%m%d-%H%M%S')}"))
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
    print(("Removed" if "--uninstall" in sys.argv else "Installed") + f" skill-scout SessionStart hook in {SETTINGS}")


if __name__ == "__main__":
    main()
