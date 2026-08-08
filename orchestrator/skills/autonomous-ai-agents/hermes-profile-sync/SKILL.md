---
name: hermes-profile-sync
description: "Sync model config and API credentials across profiles."
version: 0.1.0
author: Jared, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes-agent, profiles, credentials, auth, multi-profile, onboarding]
    related_skills: [hermes-agent]
---

# Hermes Profile Sync Skill

Copy the `model.default`/`model.provider` setting and every pooled API-key
credential from one Hermes profile into one or many other profiles, using
`scripts/sync_profile_credentials.py`. Enter API keys once (in `default`,
or any profile you designate as source); every other profile — including
ones added later — inherits them without retyping secrets or ever printing
them to the terminal.

## When to Use

- Standing up a new Hermes profile (`hermes profile create <name>`) and it
  needs the same model + provider credentials as an existing profile.
- Onboarding a teammate onto a shared multi-profile Hermes setup: they enter
  keys once into `default`, then fan them out to every other profile.
- After adding a new API key to `default` (e.g. a new provider), propagating
  it to all existing profiles in one pass.
- Don't use for: syncing OAuth-derived or `gh_cli`-derived credentials by
  default — those are session/device-bound and copying them can break the
  original session (opt in explicitly with `--include-oauth` if you understand
  the risk).

## Prerequisites

- `hermes` CLI on PATH (script shells out to it for all config reads/writes —
  never hand-parses profile YAML/JSON on the config side).
- Pure Python 3 stdlib — no `pip install` needed.
- Source profile must already have credentials configured (`hermes auth add`
  or the interactive setup wizard) and a `model.default`/`model.provider` set.
- Target profile(s) must already exist (`hermes profile create <name>`,
  or `hermes profile list` to confirm).

## How to Run

```
terminal(command="python3 ~/.hermes/skills/autonomous-ai-agents/hermes-profile-sync/scripts/sync_profile_credentials.py --target <profile> --dry-run")
```

Always dry-run first, read the output, then re-run without `--dry-run` to
apply. The script never prints secret values — only provider/label names and
action taken (added / updated / unchanged / skipped).

## Quick Reference

```
# Preview a single-profile sync from the default profile
python3 scripts/sync_profile_credentials.py --target orchestrator --dry-run

# Apply it
python3 scripts/sync_profile_credentials.py --target orchestrator

# Fan out to every other configured profile in one pass
python3 scripts/sync_profile_credentials.py --target-all

# Use a non-default profile as the source
python3 scripts/sync_profile_credentials.py --source team-lead --target new-hire

# Credentials only, leave the target's model choice untouched
python3 scripts/sync_profile_credentials.py --target orchestrator --skip-model

# Force-copy OAuth/gh_cli credentials too (understand the risk first)
python3 scripts/sync_profile_credentials.py --target orchestrator --include-oauth
```

## Procedure

1. **Confirm profiles exist.** `hermes profile list` — note exact target
   name(s). Create any missing target with `hermes profile create <name>`
   first; the sync script does not create profiles.
2. **Dry-run the sync** for each target (or `--target-all`). Read every line
   of output — it enumerates each credential provider/label and exactly what
   will happen (add / update env var / skip as duplicate / skip as
   OAuth-session-bound).
3. **Apply** by re-running the same command without `--dry-run`.
4. **Verify per target** (see Verification below) — confirm the model line
   and `auth list` output for that profile.
5. **New profile added later?** Just re-run `--target-all` from the source
   profile; already-synced profiles show `unchanged`/`identical...skipped`
   and cost nothing extra.

## Pitfalls

- **Profile must exist before syncing.** The script resolves paths via
  `hermes -p <profile> config path`; a nonexistent profile name fails with
  "Could not resolve config path" rather than silently creating one.
- **OAuth and `gh_cli` credentials are skipped by default.** This is
  deliberate — an OAuth access/refresh token is generally tied to one device
  session; forcing a copy with `--include-oauth` can knock the source session
  logged-out or race token refreshes between profiles.
- **`env:VAR` sourced credentials sync via `.env`, not the pooled-auth store.**
  If the source profile's provider credential resolves from an environment
  variable (common for `ANTHROPIC_API_KEY`, etc.), the value is copied into
  the target profile's own `.env` file (not the shared shell environment) —
  each profile keeps an independent `.env`.
- **Different pre-existing key with the same label ≠ a duplicate.** The
  script dedupes by comparing actual secret value, not by label/provider
  name. If the target profile already has its own distinct key for a
  provider, the synced key is added as an *additional* pooled credential
  (so both remain usable / rotatable) rather than overwriting the existing
  one.
- **Model sync requires model.default AND model.provider both set** in the
  source profile — if either is missing, model sync is skipped with a note
  and only credentials sync.

## Verification

After running (non-dry-run):

```
terminal(command="hermes -p <target> profile show <target>")
terminal(command="hermes -p <target> auth list")
```

Confirm:
- `Model:` line matches the source profile's model/provider.
- `auth list` shows an entry for every provider the source had (new entries
  usually appear as `synced-from-<source>` unless an identical credential
  already existed, in which case none was added — check the dry-run log for
  the reason).
