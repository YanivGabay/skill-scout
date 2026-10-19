# skill-scout

Find and install **official agent skills for the libraries your project actually uses**.

Coding agents use fast-moving libraries wrong because their training data is old. More and more vendors publish official skills (Cloudflare, Remotion, Vercel, Anthropic…), but nothing tells your agent which ones match *this* project. Tools like `skills-npm` only help when a package ships a skill inside itself — most don't.

`skill-scout` reads your manifests, ignores trivial dependencies, checks what you already have, and has a subagent find the **official** skill for each library that's worth one. You approve a shortlist; it installs them at **project scope**.

```
/skill-scout

Product      Skill                     Source               Tier      Why
Cloudflare   wrangler, workers-best-…  cloudflare/skills    official  Workers/D1/R2 APIs change fast
Remotion     remotion-best-practices   remotion-dev/skills  official  Composition + render patterns
Mammoth      —                         none found
```

## Install

Works with Claude Code (skill + optional hook). Requires Python 3.11+ and Node (for `npx skills`).

```bash
npx skills add YanivGabay/skill-scout -g -a claude-code
```

Optional — a SessionStart hook that tells the agent (once) when a project has never been scouted or its dependencies changed. Offline, ~100 ms, cache stored in `~/.claude/skill-scout/`, never in your repo:

```bash
python3 ~/.claude/skills/skill-scout/scripts/install_hook.py
# remove: python3 ~/.claude/skills/skill-scout/scripts/install_hook.py --uninstall
```

## What it reads

| Ecosystem | Manifests |
|---|---|
| npm / pnpm / yarn | `package.json` (root + workspaces, depth ≤ 3) |
| Rust | `Cargo.toml` (incl. `[workspace.dependencies]`) |
| Python | `pyproject.toml` (PEP 621 + Poetry), `requirements*.txt` |

## How it decides

- **Skips trivial deps** — types, linters, formatters, tiny utilities.
- **Groups packages into products** — `@remotion/*` → Remotion, `wrangler` + `@cloudflare/*` → Cloudflare.
- **Search order** — vendor's own GitHub → skills shipped in the package → [skills.sh](https://skills.sh) → [Tessl](https://tessl.io/registry) → [Context7](https://context7.com) as a fallback.
- **Trust tiers** — `official` and `vendor-partner` are recommended; `community` only when clearly valuable and after reading its code; `unknown` never.
- **Never installs without approval.** Project scope by default.

## Prior art

- [Symposium](https://github.com/symposium-dev/symposium) — the same idea for Rust, with a curated registry and crate-shipped skills.
- [skills-npm](https://github.com/antfu/skills-npm), [skillpm](https://skillpm.dev) — link skills that npm packages ship themselves.
- [Tessl](https://tessl.io) — registry of version-accurate usage specs.

`skill-scout` is the glue: it works across ecosystems and finds skills that live *outside* the package.

## License

MIT
