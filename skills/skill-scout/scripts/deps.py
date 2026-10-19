#!/usr/bin/env python3
"""List a project's significant dependencies and the agent skills already installed.

Usage: deps.py [project_dir] [--hash-only]
Prints JSON. Only reads manifests; never touches node_modules or the network.
"""
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import tomllib
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", "target", "dist", "build", ".venv", "venv", ".next", ".astro", ".wrangler"}

TRIVIAL_EXACT = {
    "typescript", "tslib", "prettier", "eslint", "husky", "lint-staged", "rimraf", "cross-env",
    "concurrently", "nodemon", "ts-node", "tsx", "dotenv", "chalk", "clsx", "classnames", "uuid",
    "nanoid", "lodash", "lodash-es", "ms", "debug", "zod-to-json-schema", "postcss", "autoprefixer",
    "npm-run-all", "npm-run-all2", "globals", "picocolors", "commander", "yargs", "semver",
    "serde_json", "anyhow", "thiserror", "log", "env_logger", "once_cell", "lazy_static", "rand",
    "pytest", "black", "ruff", "mypy", "flake8", "isort", "python-dotenv", "setuptools", "wheel",
}
TRIVIAL_PREFIXES = ("@types/", "eslint-", "@eslint/", "prettier-", "@typescript-eslint/", "@babel/",
                    "@tsconfig/", "babel-", "types-")


def is_trivial(name: str) -> bool:
    return name in TRIVIAL_EXACT or name.startswith(TRIVIAL_PREFIXES)


def major(version) -> str:
    if not isinstance(version, str):
        version = str(version.get("version", "")) if isinstance(version, dict) else ""
    if version.startswith(("workspace:", "file:", "link:", "git", "http")):
        return "local"
    m = re.search(r"\d+", version)
    return m.group(0) if m else "*"


def walk_manifests(root: Path, filename: str, max_depth: int = 3):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_depth = len(Path(dirpath).relative_to(root).parts)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        if rel_depth >= max_depth:
            dirnames[:] = []
        if filename in filenames:
            found.append(Path(dirpath) / filename)
    return found


def npm_deps(root: Path):
    deps = []
    for pj in walk_manifests(root, "package.json"):
        try:
            data = json.loads(pj.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for section, dev in (("dependencies", False), ("devDependencies", True), ("peerDependencies", False)):
            for name, ver in (data.get(section) or {}).items():
                deps.append({"name": name, "version": str(ver), "ecosystem": "npm", "dev": dev,
                             "manifest": str(pj.relative_to(root))})
    return deps


def cargo_deps(root: Path):
    deps = []
    for ct in walk_manifests(root, "Cargo.toml"):
        try:
            data = tomllib.loads(ct.read_text())
        except (OSError, tomllib.TOMLDecodeError):
            continue
        sections = [("dependencies", False), ("dev-dependencies", True), ("build-dependencies", True)]
        tables = [data] + ([data["workspace"]] if isinstance(data.get("workspace"), dict) else [])
        for table in tables:
            for section, dev in sections:
                for name, ver in (table.get(section) or {}).items():
                    deps.append({"name": name, "version": ver if isinstance(ver, str) else str(ver.get("version", "")) if isinstance(ver, dict) else "",
                                 "ecosystem": "cargo", "dev": dev, "manifest": str(ct.relative_to(root))})
    return deps


def python_deps(root: Path):
    deps = []
    for pp in walk_manifests(root, "pyproject.toml", max_depth=2):
        try:
            data = tomllib.loads(pp.read_text())
        except (OSError, tomllib.TOMLDecodeError):
            continue
        for spec in (data.get("project", {}).get("dependencies") or []):
            name = re.split(r"[<>=!~\[; ]", spec, maxsplit=1)[0].strip()
            if name:
                deps.append({"name": name.lower(), "version": spec[len(name):].strip(), "ecosystem": "pypi",
                             "dev": False, "manifest": str(pp.relative_to(root))})
        poetry = data.get("tool", {}).get("poetry", {}).get("dependencies") or {}
        for name, ver in poetry.items():
            if name.lower() != "python":
                deps.append({"name": name.lower(), "version": str(ver), "ecosystem": "pypi", "dev": False,
                             "manifest": str(pp.relative_to(root))})
    for req in [Path(p) for p in glob.glob(str(root / "requirements*.txt"))]:
        for line in req.read_text(errors="ignore").splitlines():
            line = line.split("#")[0].strip()
            if not line or line.startswith("-"):
                continue
            name = re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0].strip()
            if name:
                deps.append({"name": name.lower(), "version": line[len(name):].strip(), "ecosystem": "pypi",
                             "dev": "dev" in req.name, "manifest": req.name})
    return deps


def skill_names(pattern: str):
    return sorted({Path(p).parent.name for p in glob.glob(os.path.expanduser(pattern))})


def installed_skills(root: Path):
    return {
        "global": skill_names("~/.claude/skills/*/SKILL.md"),
        "project": sorted(set(skill_names(str(root / ".claude/skills/*/SKILL.md")))
                          | set(skill_names(str(root / ".agents/skills/*/SKILL.md")))),
        "plugins": skill_names("~/.claude/plugins/cache/*/*/*/skills/*/SKILL.md"),
    }


def symposium_status():
    binary = shutil.which("cargo-agents") or (
        str(Path("~/.cargo/bin/cargo-agents").expanduser())
        if Path("~/.cargo/bin/cargo-agents").expanduser().exists() else None)
    return {"installed": bool(binary),
            "initialized": Path("~/.symposium/config.toml").expanduser().exists()}


def collect(root: Path):
    all_deps = npm_deps(root) + cargo_deps(root) + python_deps(root)
    seen, significant, skipped = set(), [], set()
    for d in all_deps:
        key = (d["ecosystem"], d["name"])
        if key in seen:
            continue
        seen.add(key)
        if is_trivial(d["name"]) or major(d["version"]) == "local":
            skipped.add(d["name"])
        else:
            significant.append(d)
    significant.sort(key=lambda d: (d["ecosystem"], d["dev"], d["name"]))
    fingerprint = "\n".join(f'{d["ecosystem"]}:{d["name"]}@{major(d["version"])}' for d in significant)
    return {
        "project": str(root),
        "ecosystems": sorted({d["ecosystem"] for d in significant}),
        "hash": hashlib.sha256(fingerprint.encode()).hexdigest()[:16],
        "dependencies": significant,
        "skipped_trivial": sorted(skipped),
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0] if args else os.getcwd()).resolve()
    result = collect(root)
    if "--hash-only" in sys.argv:
        print(result["hash"] if result["dependencies"] else "")
        return
    result["installed_skills"] = installed_skills(root)
    if "cargo" in result["ecosystems"]:
        result["symposium"] = symposium_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
