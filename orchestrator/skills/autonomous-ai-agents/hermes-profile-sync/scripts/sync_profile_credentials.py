#!/usr/bin/env python3
"""Sync model config and provider credentials from one Hermes profile to another (or to all).

Enter API keys once in a "source" profile (usually `default`); this script
copies the model.default/model.provider setting and every API-key credential
in that profile's pooled auth store into one or more target profiles, without
ever printing secret values or requiring you to re-enter them.

Design notes (why it works this way):
- Model config is read/written via `hermes -p <profile> config get/set ...`
  (shells out to the real CLI) rather than hand-parsing YAML, so it stays
  correct across Hermes config-schema changes and needs zero third-party
  Python dependencies.
- Credentials are synced two ways, matching how Hermes stores them:
    1. api_key / manual  -> re-added to the target via `hermes auth add`.
    2. api_key / env:VAR -> the VAR=value line is copied into the target
       profile's .env file (Hermes resolves these at runtime from env).
- OAuth and gh_cli-derived credentials are device/session-bound and are
  SKIPPED by default (copying a live OAuth token to another profile can
  invalidate or race with the original session). Pass --include-oauth to
  force it anyway.
- Idempotent: re-running detects already-matching values (same access token,
  same env var value) and skips them instead of creating duplicate pooled
  credentials (a real failure mode we hit doing this by hand).

Requires only the `hermes` CLI on PATH. Pure stdlib Python — no pip installs.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_hermes(profile: str | None, args: list[str], capture=True) -> subprocess.CompletedProcess:
    cmd = ["hermes"]
    if profile:
        cmd += ["-p", profile]
    cmd += args
    return subprocess.run(cmd, capture_output=capture, text=True)


def profile_dir(profile: str | None) -> Path:
    """Resolve a profile's home directory via `hermes config path`.

    Works for the unnamed default profile (profile=None) and named profiles,
    including ones backed by symlinks (e.g. shared team distributions) — the
    OS follows the symlink transparently when we open files under it.
    """
    r = run_hermes(profile, ["config", "path"])
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"Could not resolve config path for profile {profile!r}: {r.stderr.strip()}")
    return Path(r.stdout.strip()).parent


def list_other_profiles(exclude: str | None) -> list[str]:
    """Return every configured profile name, excluding `exclude` and the unnamed default."""
    r = run_hermes(None, ["profile", "list"])
    if r.returncode != 0:
        raise RuntimeError(f"hermes profile list failed: {r.stderr.strip()}")
    names = []
    for line in r.stdout.splitlines():
        line = line.strip().lstrip("\u25c6").strip()  # strip the "current profile" marker glyph
        if not line or line.lower().startswith("profile") or set(line) <= {"\u2500", " "}:
            continue
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        if name.lower() == "default" or name == exclude:
            continue
        names.append(name)
    return names


def config_get(profile: str | None, key: str) -> str | None:
    r = run_hermes(profile, ["config", "get", key])
    if r.returncode != 0:
        return None
    value = r.stdout.strip()
    return value or None


def config_set(profile: str, key: str, value: str) -> tuple[bool, str]:
    r = run_hermes(profile, ["config", "set", key, value])
    return r.returncode == 0, (r.stdout.strip() or r.stderr.strip())


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip()
    return values


def write_env_var(path: Path, key: str, value: str, dry_run: bool) -> str:
    """Set key=value in an env file, replacing an existing line for that key. Returns action taken."""
    existing = read_env_file(path)
    if existing.get(key) == value:
        return "unchanged"
    lines = path.read_text().splitlines() if path.exists() else []
    replaced = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") and not stripped.startswith("#"):
            new_lines.append(f"{key}={value}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        new_lines.append(f"{key}={value}")
    if dry_run:
        return "would add" if not replaced else "would update"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(new_lines) + "\n")
    path.chmod(0o600)
    return "updated" if replaced else "added"


def sync_model_config(source_profile: str | None, target_profile: str, dry_run: bool) -> list[str]:
    notes = []
    default_model = config_get(source_profile, "model.default")
    provider = config_get(source_profile, "model.provider")
    if not default_model or not provider:
        notes.append("source profile has no model.default/model.provider set — skipped model sync")
        return notes
    if dry_run:
        notes.append(f"[dry-run] would set model.default={default_model}, model.provider={provider}")
        return notes
    for key, value in (("model.default", default_model), ("model.provider", provider)):
        ok, msg = config_set(target_profile, key, value)
        notes.append((f"set {key} = {value}" if ok else f"FAILED setting {key}: {msg}"))
    return notes


def load_auth_pool(profile_dir_path: Path) -> dict:
    auth_file = profile_dir_path / "auth.json"
    if not auth_file.exists():
        return {}
    with auth_file.open() as f:
        return json.load(f)


def sync_credentials(
    source_profile: str | None,
    target_profile: str,
    include_oauth: bool,
    dry_run: bool,
) -> list[str]:
    notes: list[str] = []
    src_dir = profile_dir(source_profile)
    tgt_dir = profile_dir(target_profile)

    src_auth = load_auth_pool(src_dir)
    tgt_auth = load_auth_pool(tgt_dir)
    src_pool = src_auth.get("credential_pool", {})
    tgt_pool = tgt_auth.get("credential_pool", {})

    src_env = read_env_file(src_dir / ".env")
    tgt_env_path = tgt_dir / ".env"

    if not src_pool:
        notes.append("source profile has no pooled credentials (auth.json missing/empty)")

    for provider, creds in src_pool.items():
        existing_tokens = {
            c.get("access_token") or c.get("api_key")
            for c in tgt_pool.get(provider, [])
        }
        for cred in creds:
            auth_type = cred.get("auth_type")
            source = cred.get("source", "")
            label = cred.get("label", provider)

            if source == "gh_cli" or (auth_type == "oauth" and not include_oauth):
                notes.append(f"{provider}/{label}: skipped ({source or auth_type}, device/session-bound; use --include-oauth to force)")
                continue

            if source.startswith("env:"):
                var_name = source.split(":", 1)[1]
                value = src_env.get(var_name)
                if value is None:
                    notes.append(f"{provider}/{label}: source references env:{var_name} but it's not set in source .env — skipped")
                    continue
                action = write_env_var(tgt_env_path, var_name, value, dry_run)
                notes.append(f"{provider}/{label}: env var {var_name} {action} in target .env")
                continue

            token = cred.get("access_token") or cred.get("api_key")
            if not token:
                notes.append(f"{provider}/{label}: no portable secret value found — skipped")
                continue
            if token in existing_tokens:
                notes.append(f"{provider}/{label}: identical credential already present in target — skipped (no duplicate)")
                continue
            if dry_run:
                notes.append(f"[dry-run] {provider}/{label}: would add via `hermes auth add {provider}`")
                continue
            cred_type = "oauth" if auth_type == "oauth" else "api-key"
            r = run_hermes(
                target_profile,
                ["auth", "add", provider, "--type", cred_type, "--api-key", token, "--label", f"synced-from-{source_profile or 'default'}"],
            )
            if r.returncode != 0:
                notes.append(f"{provider}/{label}: FAILED to add — {r.stderr.strip()}")
            else:
                notes.append(f"{provider}/{label}: added to target ({r.stdout.strip()})")
                existing_tokens.add(token)
    return notes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=None, help="Source profile name (default: the unnamed default profile)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--target", help="Target profile name")
    group.add_argument("--target-all", action="store_true", help="Sync into every other configured profile")
    parser.add_argument("--include-oauth", action="store_true", help="Also copy OAuth/gh_cli-derived credentials (risky — session/device bound)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing anything")
    parser.add_argument("--skip-model", action="store_true", help="Only sync credentials, not model.default/model.provider")
    args = parser.parse_args()

    source_label = args.source or "default"

    if args.target_all:
        targets = list_other_profiles(exclude=args.source)
        if not targets:
            print("No other profiles found to sync into.")
            return
    else:
        targets = [args.target]

    for target in targets:
        print(f"\n=== Syncing {source_label} -> {target} ===")
        if not args.skip_model:
            for note in sync_model_config(args.source, target, args.dry_run):
                print(f"  [model] {note}")
        for note in sync_credentials(args.source, target, args.include_oauth, args.dry_run):
            print(f"  [auth]  {note}")

    print("\nDone." + (" (dry run — no changes written)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
