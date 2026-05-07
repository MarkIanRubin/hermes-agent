#!/usr/bin/env bash
set -euo pipefail

# One-way sync: Lifeislucky -> macmini.
# Source of truth: queen_bee_obsidian profile on Lifeislucky.

LOCAL_PROFILE="/Users/markrubin/.hermes/profiles/queen_bee_obsidian"
LOCAL_PROFILE_HOME="$LOCAL_PROFILE/home"
LOCAL_SKILLS="$LOCAL_PROFILE/skills/"
LOCAL_ZERO_CONFIG="$LOCAL_PROFILE_HOME/.zero/config.json"

REMOTE_HOST="100.124.65.7"
REMOTE_USER="queenbee"
REMOTE="$REMOTE_USER@$REMOTE_HOST"
REMOTE_PROFILE="$HOME/.hermes/profiles/queen_bee_obsidian"
REMOTE_PROFILE_HOME="$REMOTE_PROFILE/home"
REMOTE_SKILLS="$REMOTE_PROFILE/skills/"
REMOTE_ZERO_DIR="$REMOTE_PROFILE_HOME/.zero"

SSH_KEY="$LOCAL_PROFILE_HOME/.ssh/hermes_macmini_sync"
SSH_OPTS=(-i "$SSH_KEY" -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new)

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

if [[ ! -d "$LOCAL_SKILLS" ]]; then
  echo "Missing local skills dir: $LOCAL_SKILLS" >&2
  exit 1
fi

if [[ ! -f "$SSH_KEY" ]]; then
  echo "Missing SSH key: $SSH_KEY" >&2
  exit 1
fi

log "Checking macmini SSH access"
ssh "${SSH_OPTS[@]}" "$REMOTE" "hostname >/dev/null"

log "Preparing remote Hermes profile dirs"
ssh "${SSH_OPTS[@]}" "$REMOTE" "mkdir -p '$REMOTE_SKILLS' '$REMOTE_ZERO_DIR'"

log "Syncing Hermes skills"
rsync -az --delete \
  -e "ssh -i '$SSH_KEY' -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new" \
  --exclude '.DS_Store' \
  "$LOCAL_SKILLS" "$REMOTE:$REMOTE_SKILLS"

if [[ -f "$LOCAL_ZERO_CONFIG" ]]; then
  log "Syncing Zero wallet/config for queen_bee_obsidian profile"
  rsync -az \
    -e "ssh -i '$SSH_KEY' -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new" \
    "$LOCAL_ZERO_CONFIG" "$REMOTE:$REMOTE_ZERO_DIR/config.json"
  ssh "${SSH_OPTS[@]}" "$REMOTE" "chmod 700 '$REMOTE_ZERO_DIR' && chmod 600 '$REMOTE_ZERO_DIR/config.json'"
else
  log "No local Zero config found at $LOCAL_ZERO_CONFIG; skipping wallet/config"
fi

log "Ensuring Zero CLI exists on macmini profile home"
ssh "${SSH_OPTS[@]}" "$REMOTE" "export HOME='$REMOTE_PROFILE_HOME'; export PATH=\"\$HOME/.zero/bin:\$PATH\"; command -v zero >/dev/null || curl -fsSL https://zero.xyz/install.sh | bash >/dev/null"

log "Remote verification"
ssh "${SSH_OPTS[@]}" "$REMOTE" "export HOME='$REMOTE_PROFILE_HOME'; export PATH=\"\$HOME/.zero/bin:\$PATH\"; test -d '$REMOTE_SKILLS' && echo skills_count=\$(find '$REMOTE_SKILLS' -name SKILL.md | wc -l | tr -d ' '); zero --version 2>/dev/null || true; zero wallet balance 2>/dev/null || true"

log "Done"
