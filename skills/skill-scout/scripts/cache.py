#!/usr/bin/env python3
"""Per-project scout cache, stored outside the repo so projects stay clean.

Usage:
  cache.py check [project_dir]            -> prints SessionStart hook JSON when a scout is due
  cache.py mark  [project_dir] [--dismiss] -> records the current dependency hash as handled
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deps import collect  # noqa: E402

CACHE = Path(os.environ.get("SKILL_SCOUT_CACHE", "~/.claude/skill-scout/cache.json")).expanduser()


def load():
    try:
        return json.loads(CACHE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save(data):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(CACHE)


def check(root: Path):
    info = collect(root)
    if not info["dependencies"]:
        return
    entry = load().get(str(root))
    if entry and entry.get("hash") == info["hash"]:
        return
    reason = "has never been scouted" if not entry else "dependencies changed since the last scout"
    message = (f"skill-scout: this project ({len(info['dependencies'])} significant "
               f"{'/'.join(info['ecosystems'])} dependencies) {reason}. Mention once, briefly, that "
               "running /skill-scout can find official agent skills for its libraries. Do not run it unprompted.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": message}}))


def mark(root: Path, dismissed: bool):
    info = collect(root)
    data = load()
    data[str(root)] = {"hash": info["hash"], "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "dismissed": dismissed}
    save(data)
    print(f"skill-scout: recorded {info['hash']} for {root}{' (dismissed)' if dismissed else ''}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("check", "mark"):
        sys.exit(__doc__)
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    root = Path(args[0] if args else os.getcwd()).resolve()
    try:
        if sys.argv[1] == "check":
            check(root)
        else:
            mark(root, "--dismiss" in sys.argv)
    except Exception as exc:  # a hook must never break session start
        if sys.argv[1] == "mark":
            raise
        print(f"skill-scout check skipped: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
