---
name: hermes-telegram-coding-context
description: Configure Hermes so Telegram chats open with the correct repo working directory and coding context instead of a stale default workspace.
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [hermes, telegram, gateway, repo-context, coding]
---

# Hermes Telegram Coding Context

Use when Hermes works in Telegram but has no useful coding context, starts in the wrong directory, or behaves like it has no idea which repo it should be working in.

## Symptoms
- Telegram bot responds, but acts contextless for coding tasks
- Terminal/file operations default to the wrong workspace
- Bot starts in an old OpenClaw workspace or home directory
- User wants to "pick up coding in Telegram" from the current repo

## Root cause pattern
Hermes gateway messaging sessions should use `terminal.cwd` in `config.yaml` as the durable default working directory. Older setups may still have `MESSAGING_CWD` in `.env`; that setting is deprecated and now produces gateway warnings.

Repo-specific coding context also needs a prefill message file so Telegram sessions start with project instructions instead of waking up blank.

## Working approach
Set both:
1. `terminal.cwd` in `config.yaml` to the target repo
2. `HERMES_PREFILL_MESSAGES_FILE` in `.env` and/or `prefill_messages_file` in `config.yaml` to a repo-specific JSON prefill
3. Remove deprecated `MESSAGING_CWD` from `.env` after `terminal.cwd` is set.

Then restart the Hermes gateway.

## Files to edit
- `~/.hermes/.env`
- `~/.hermes/config.yaml`
- a new prefill JSON file, e.g. `~/.hermes/prefill-telegram-coding.json`

## Recommended prefill structure
Create a JSON array of system messages with content like:
- default repo path
- default working directory
- project-specific workflow constraints
- current architectural focus / active refactor areas

Example content:

```json
[
  {
    "role": "system",
    "content": "You are operating from Telegram as a coding agent for the hivemind-operator repo. Default working directory: /Users/markrubin/hivemind-operator. Treat that repo as the primary context unless the user explicitly switches projects."
  },
  {
    "role": "system",
    "content": "Project rules: use Safari scraper flow via tools/scrape-all.py by default; do not switch to Chrome/CDP unless asked."
  },
  {
    "role": "system",
    "content": "Current focus: hivemind-operator refactor and UI work. Frontend is being split out of index.html into standalone JS modules."
  }
]
```

## Exact settings
In `~/.hermes/.env`:

```bash
HERMES_PREFILL_MESSAGES_FILE=/Users/markrubin/.hermes/prefill-telegram-coding.json
```

Do not keep `MESSAGING_CWD` here; it is deprecated. If present from an old setup or cloned profile, remove it after setting `terminal.cwd`.

In `~/.hermes/config.yaml`:

```yaml
prefill_messages_file: /Users/markrubin/.hermes/prefill-telegram-coding.json
terminal:
  cwd: /Users/markrubin/hivemind-operator
```

Set `terminal.cwd` explicitly to the target repo when you want Telegram coding sessions to operate there reliably.

## Why both env + config
- `.env` is what the gateway actually loads at startup
- `config.yaml` keeps the setup durable and discoverable
- Hermes gateway checks both env and config for prefill message files

## Restart step
After changes:

```bash
hermes gateway restart
hermes gateway status
```

## Verification
Check:
- gateway restarted cleanly
- `~/.hermes/.env` contains `MESSAGING_CWD` and `HERMES_PREFILL_MESSAGES_FILE`
- `~/.hermes/config.yaml` contains `prefill_messages_file`
- `terminal.cwd` in config points at the target repo when you want Telegram coding to live there full-time
- Telegram bot can answer a repo-awareness prompt correctly

Suggested Telegram test prompt:

```text
Open hivemind-operator and tell me what repo you are in, what branch you're on, and what the current frontend breakup files are.
```

Even better: remove wiggle room and ask it to inspect the repo root explicitly:

```text
Open /Users/markrubin/hivemind-operator and list these repo-root files if they exist: nearby-recently-booked.js, route-optimization.js, route-state.js, location-dashboard-view.js, gantt-dashboard-core.js, revenue-velocity.js, dashboard-refresh-meta.js.
```

## Pitfalls
- Existing Telegram conversations may still carry stale conversation state; a fresh prompt or fresh thread tests the setup better
- This does not inject the entire current terminal chat transcript into Telegram; it gives correct repo/workdir defaults and startup coding context
- If `TERMINAL_CWD` is explicitly set in config, it can override the `MESSAGING_CWD` fallback
- The bot may hallucinate a `/frontend` directory even when extracted JS files live in the repo root; put that fact directly into the prefill if needed
- Keep `MESSAGING_CWD` and `TERMINAL_CWD` aligned in gateway startup. If one points at the repo and the other points at an old OpenClaw workspace, the bot can appear to have repo access while still loading stale context
- If the bot suddenly stops replying after config changes, check `hermes gateway status` and recent gateway logs first. In practice the gateway can drop and make this look like a context problem when it is really an uptime problem

## Related note
If Telegram image support is also broken, use the separate `hermes-telegram-image-support` skill. This skill is about repo coding context, not screenshot ingestion.
