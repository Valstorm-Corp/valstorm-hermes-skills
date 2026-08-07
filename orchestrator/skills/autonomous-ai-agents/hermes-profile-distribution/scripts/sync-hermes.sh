#!/bin/bash
set -e

# Define the profiles that make up your agentic network
PROFILES=("orchestrator") # Add others here, e.g., ("orchestrator" "coder" "qa")

# Accept destination as an argument, or default to a fallback
DEST="${1:-/Users/jared/Documents/Code/valstorm/hermes-profile}"

echo "Syncing Hermes Agent Network..."

for PROFILE in "${PROFILES[@]}"; do
  HERMES_SRC="$HOME/.hermes/profiles/$PROFILE"
  PROFILE_DEST="$DEST/$PROFILE"
  
  if [ ! -d "$HERMES_SRC" ]; then
    echo "⚠️  Warning: Source profile $PROFILE ($HERMES_SRC) does not exist. Skipping."
    continue
  fi

  echo "  -> Syncing profile: $PROFILE"
  mkdir -p "$PROFILE_DEST/skills"

  # 1. Sync the skills directory.
  rsync -a --delete \
    --exclude='valstorm-internal/' \
    --exclude='.usage.json' \
    --exclude='.usage.json.lock' \
    --exclude='.bundled_manifest' \
    --exclude='.curator_state' \
    --exclude='.curator_backups' \
    --exclude='.hub' \
    "$HERMES_SRC/skills/" "$PROFILE_DEST/skills/"

  # 2. Sync additional extension directories if they exist
  for dir in bin hooks plugins; do
    if [ -d "$HERMES_SRC/$dir" ]; then
      mkdir -p "$PROFILE_DEST/$dir"
      rsync -a --delete "$HERMES_SRC/$dir/" "$PROFILE_DEST/$dir/"
    fi
  done

  # 3. Sync the Persona (SOUL.md)
  if [ -f "$HERMES_SRC/SOUL.md" ]; then
    cp "$HERMES_SRC/SOUL.md" "$PROFILE_DEST/SOUL.md"
  fi

  # 4. Generate a sanitized config.example.yaml
  if [ -f "$HERMES_SRC/config.yaml" ]; then
    sed -E 's/([A-Za-z0-9_]*(api_key|token|secret)[A-Za-z0-9_]*:)[[:space:]]*.*$/\1 "<YOUR_SECRET_HERE>"/ig' "$HERMES_SRC/config.yaml" > "$PROFILE_DEST/config.example.yaml"
  fi
done

# 5. Write a bulletproof .gitignore into the ROOT of the public repo.
# Git ignores apply to all subdirectories automatically, so this protects ALL profiles.
cat << 'EOF' > "$DEST/.gitignore"
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
EOF

echo "✅ Hermes profile synced to $DEST!"