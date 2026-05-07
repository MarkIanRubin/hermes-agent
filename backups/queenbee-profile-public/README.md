# QueenBee Hermes Mind Backup (public-safe)

Generated: 2026-05-07T18:40:49

This is a sanitized backup of the QueenBee Hermes profile for disaster recovery.
It recreates the mind/configuration shape without publishing secrets.

## Included

- `profile/SOUL.md` — identity/frameworks.
- `profile/memories/` — curated memory/user profile with contact fields redacted.
- `profile/config.yaml` — Hermes config with secrets, tokens, chat IDs, and delivery targets redacted.
- `profile/skills/` — installed/custom procedural skills and references.
- `profile/cron/jobs.json` — sanitized schedules/prompts when present.
- `profile/.env.example` — variable names only.
- `default-home/` — sanitized default Hermes home files.

## Excluded on purpose

- real `.env` values
- `auth.json`, OAuth refresh tokens, credential pools
- Telegram/Discord chat IDs and delivery targets
- sessions/transcripts, logs, caches, audio, screenshots, sqlite DBs, pid/lock files
- browser/API cookies and runtime state

This repo is public, so raw secrets do **not** belong here.

## Restore sketch

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
mkdir -p ~/.hermes/profiles/queen_bee_obsidian
rsync -av backups/queenbee-profile-public/profile/ ~/.hermes/profiles/queen_bee_obsidian/
cp ~/.hermes/profiles/queen_bee_obsidian/.env.example ~/.hermes/profiles/queen_bee_obsidian/.env
# Fill .env manually, then re-authenticate OAuth providers:
hermes --profile queen_bee_obsidian login --provider openai-codex
hermes --profile queen_bee_obsidian setup gateway
hermes --profile queen_bee_obsidian doctor --fix
hermes --profile queen_bee_obsidian gateway restart
```

## Backup stats

- Files copied: 612
- Skill/reference files copied: 592
