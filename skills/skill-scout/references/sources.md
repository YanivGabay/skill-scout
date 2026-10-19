# Where official skills live, and how to judge them

## Search order (stop at the first tier that has a good match)

1. **Vendor's own GitHub** — the org that publishes the package.
   - npm: read `repository` from `https://registry.npmjs.org/<name>/latest` (scoped names: encode `/` as `%2F`).
   - crates: `https://crates.io/api/v1/crates/<name>` → `crate.repository`.
   - PyPI: `https://pypi.org/pypi/<name>/json` → `info.project_urls`.
   - Then look for skills: `gh search code "filename:SKILL.md" --owner <org>`, a dedicated repo (`<org>/skills`, `<org>/agent-skills`, `<org>/<product>-skills`), or `skills/*/SKILL.md` inside the main repo.
   - Known examples: `cloudflare/skills`, `remotion-dev/skills`, `vercel-labs/agent-skills`, `vercel-labs/agent-browser`, `anthropics/skills`, `supabase-community/...`, `stripe/...`.
2. **Skills shipped inside the package** — `skills/*/SKILL.md` in the published tarball/crate. (`npx skills experimental_sync` handles npm; Symposium handles Rust crates.)
3. **skills.sh registry** — `npx -y skills find <query>`; check the security assessment on `https://skills.sh/<owner>/<repo>`.
4. **Tessl registry** — `https://tessl.io/registry` has version-accurate usage specs for many libraries. Mention as an option; installing needs the Tessl CLI/account.
5. **Context7** — not a skill; an MCP that fetches current docs on demand. Suggest only when nothing better exists and the library is heavily used.

## Trust tiers (report one per candidate)

| Tier | Meaning | Default |
|---|---|---|
| `official` | Published by the same org/maintainers as the package | Recommend |
| `vendor-partner` | Published by a company the vendor links to from its own docs | Recommend with note |
| `community` | Third-party; popular (stars, installs) and recently maintained | Only if clearly valuable; flag it |
| `unknown` | Anything else | Do not recommend |

Before recommending a non-official skill, read its SKILL.md and scripts. Skills run with the agent's full permissions — reject anything that downloads and executes code, exfiltrates data, or asks for credentials.

## Worth a skill vs not

Worth it: frameworks and platforms with real API surface or conventions the model gets wrong — deploy/runtime platforms (Cloudflare, Vercel, Supabase), frameworks (Next.js, Astro, Remotion), SDKs with fast-moving APIs (Anthropic, OpenAI, Stripe, Paddle), ORMs, test/browser tooling (Playwright).

Not worth it: small utilities, parsers, polyfills, React itself, anything the model already uses correctly.

## Install commands

- Project scope, Claude Code only (preferred): `npx -y skills add <owner>/<repo> -s <skill-name> -a claude-code -y`
- List a repo's skills first: `npx -y skills add <owner>/<repo> -l`
- Global (only when the user asks): add `-g`.
- Project installs create `skills-lock.json`; tell the user so they can decide whether to commit it.
