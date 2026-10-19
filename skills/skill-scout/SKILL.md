---
name: skill-scout
description: Find and install official agent skills for the libraries a project actually uses. Scans package.json (incl. workspaces), Cargo.toml and pyproject/requirements, skips trivial dependencies, checks which skills are already installed, then a subagent searches for official vendor skills and returns a vetted shortlist to install at project scope. Use when the user runs /skill-scout, asks "what skills should this project have", "find skills for my dependencies", "are there official skills for X in this repo", or when a SessionStart note says the project's dependencies changed since the last scout.
---

# Skill Scout

Match a project's real dependencies to official agent skills, then install only what the user approves, at project scope.

## Workflow

### 1. Inventory

Run from the project root:

```bash
python3 <skill-dir>/scripts/deps.py
```

It prints JSON: significant `dependencies` (name, version, ecosystem, dev flag, manifest), `skipped_trivial`, and `installed_skills` (global, project, plugins). If `dependencies` is empty, say so and stop.

### 2. Route Rust crates to Symposium

If `ecosystems` includes `cargo`, do not search for per-crate Rust skills — [Symposium](https://github.com/symposium-dev/symposium) does that natively from crate-authored plugins, version-matched and kept in sync. Remove `cargo` dependencies from the candidate list and handle them by the `symposium` status in the inventory:

- **installed + initialized** → offer to run `cargo agents sync` in the project (it installs whatever its registry matches, plus a general Rust best-practices skill).
- **installed, not initialized** → `cargo agents init` is interactive; ask the user to run `! cargo agents init` themselves and recommend **project** hook scope so it doesn't hook every non-Rust session.
- **not installed** → recommend it in the final table as one row ("Rust crates → Symposium"), with install `cargo binstall symposium` (or `cargo install symposium`) followed by the init step above. Never install it unasked.

Rust tooling that is not a crate concern (e.g. a deploy platform used by the Rust service) still goes through the normal search below. npm and Python dependencies in the same repo are always searched normally.

### 3. Shortlist candidates

From the dependency list, keep the ones likely to deserve a skill (platforms, frameworks, fast-moving SDKs, ORMs, browser/test tooling — see `references/sources.md` → "Worth a skill vs not"). Group related packages under one product (e.g. `@remotion/*` → Remotion, `wrangler` + `@cloudflare/*` → Cloudflare). Drop any product already covered by an installed skill or plugin.

### 4. Search with a subagent

Spawn one `general-purpose` subagent (two in parallel if there are more than ~10 products) with:
- the product list (package names + versions),
- the full text of `references/sources.md`,
- the instruction to return, per product: best skill found (repo + skill name), trust tier, a one-line reason it helps, the exact install command, or "none found".

Instruct the subagent to research only — never install anything.

### 5. Present and confirm

Show one table: product → skill → source → tier → why. Then ask which to install (AskUserQuestion, multi-select). Default to recommending only `official` and `vendor-partner` items. Never install without an explicit yes.

### 6. Install and record

For each approved skill, run the project-scope install command from `references/sources.md`, then verify the skill directory exists under `.claude/skills/`. Finally record the scout so the SessionStart hook stays quiet until dependencies change:

```bash
python3 <skill-dir>/scripts/cache.py mark
```

If the user declines everything, record it anyway with `cache.py mark --dismiss`. Mention that project installs create `skills-lock.json`, and let the user decide whether to commit it.

## SessionStart hook (optional)

`scripts/cache.py check` is a ~100ms, offline check meant for a SessionStart hook: it prints a one-line context note only when the project has never been scouted or its significant dependencies changed. The cache lives in `~/.claude/skill-scout/cache.json`, never in the project. Install or remove the hook with:

```bash
python3 <skill-dir>/scripts/install_hook.py            # install
python3 <skill-dir>/scripts/install_hook.py --uninstall
```

When that note appears, mention `/skill-scout` once; do not run it unprompted.
