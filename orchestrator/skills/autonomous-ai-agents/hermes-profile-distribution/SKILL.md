---
name: hermes-profile-distribution
description: Use when packaging Hermes profiles for distribution.
---

# Distributing Hermes Profiles (Agentic Networks)

Hermes intelligence (Skills, System Prompts, Scripts) can be safely distributed to teams or the public using a Git-backed "Agentic Network" pattern.

This pattern allows Valstorm (or any external system) to distribute entire networks of specialized Hermes profiles without interfering with the user's default installation or leaking private data.

## The Architecture
1. **The Network Repository:** A single Git repository containing multiple subdirectories, one for each profile (e.g., `orchestrator/`, `coder/`, `qa/`).
2. **Profile Isolation:** Users continue using their standard Hermes install. The network repo is cloned to a hidden staging area (e.g., `~/.hermes/.valstorm-network`) and the profile subdirectories are **symlinked** into `~/.hermes/profiles/`.
3. **Seamless Updates:** A simple `git pull` in the hidden staging area instantly updates skills across all symlinked profiles.

## Profile Structure
Inside the Git repository, each profile directory (e.g., `orchestrator/`) should contain:
*   `skills/` - The shared intelligence.
*   `SOUL.md` - (Optional) The core system prompt/persona.
*   `bin/`, `hooks/`, `plugins/` - (Optional) Supporting code.
*   `config.example.yaml` - A sanitized template of the configuration.

## Data Privacy & Security (The Root `.gitignore`)
To prevent leaking personal chats, SQLite databases, API keys, or local usage tracking, the **root** of the published Git repository MUST contain this exact `.gitignore`:

```gitignore
# Local Hermes State & Secrets
config.yaml
sessions.db
state.db
state.db-shm
state.db-wal
verification_evidence.db
cache/
memories/
.env
.hermes_history
logs/
sessions/
pastes/
interrupt_debug.log
*_cache.json
auth.json
auth.lock
skills/.usage.json*
skills/.curator_*
```
Because it is at the root, Git will enforce these exclusions across all profile subdirectories.

## Preventing Proprietary IP Leaks
If you are developing public skills in the same profile where you develop private/proprietary skills:
1. Place all private skills in a specific subdirectory (e.g., `skills/valstorm-internal/`).
2. Update your extraction script (e.g., `sync-hermes.sh`) to explicitly exclude that directory when building the public repo:
   `--exclude='valstorm-internal/'`

## Extraction Script (sync-hermes.sh)
The recommended way to maintain this network is a bash script that pulls the required assets from your live Hermes installation and drops them into the external Git repo folder. See `scripts/sync-hermes.sh` for the reference implementation.