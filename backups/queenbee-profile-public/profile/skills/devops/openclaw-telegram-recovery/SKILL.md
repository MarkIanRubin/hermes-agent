---
name: openclaw-telegram-recovery
description: Recover OpenClaw Telegram when imported settings break the bot or cause polling conflicts.
version: 1.0.0
author: [REDACTED]
license: MIT
---

# OpenClaw Telegram Recovery

Use when Telegram stops working after importing settings, reinstalling OpenClaw, or moving configs between machines.

## What usually breaks

1. `~/.openclaw/config.json` is incomplete or stale after import.
2. `plugins.allow` omits `telegram`, which disables the plugin even if `channels.telegram.enabled=true` elsewhere.
3. A second runner is polling the same Telegram bot token, causing:
   `409 Conflict: terminated by other getUpdates request`

## Fast diagnosis

1. Compare both config files:
   - `~/.openclaw/config.json`
   - `~/.openclaw/openclaw.json`
2. Check runtime status:
   - `openclaw status --deep`
   - `openclaw channels list --json`
   - `openclaw doctor --deep --non-interactive`
3. Check logs for Telegram startup and conflicts:
   - `openclaw logs | tail -n 120`
   Look for:
   - `[default] starting provider (@YourBot)`
   - `getUpdates conflict`
4. Inspect running processes:
   - `ps aux | grep -i '[o]penclaw'`
   - `ps -Ao pid,ppid,command | egrep 'openclaw|telegram|hermes|entry.js gateway'`
   - `lsof -nP -iTCP -sTCP:ESTABLISHED | egrep '149\.154|91\.108|openclaw|node|python'`

## Repair steps

### Case 1: imported config dropped Telegram
Patch `~/.openclaw/config.json` so it contains all three:

- `plugins.allow` includes `telegram`
- `plugins.entries.telegram.enabled = true`
- `channels.telegram` exists with the bot token and policy

If `~/.openclaw/openclaw.json` is still correct, copy the `channels.telegram` block from there into `~/.openclaw/config.json`.

Always make a timestamped backup before editing.

### Case 2: Telegram plugin disabled by allowlist
After OpenClaw 2026.3.28, `plugins.allow` behaves like a hard allowlist. If it only contains `openclaw-codex-app-server`, Telegram will not start even when channel config looks valid.

Fix by adding:

```json
"plugins": {
  "allow": ["openclaw-codex-app-server", "telegram"],
  "entries": {
    "telegram": {"enabled": true}
  }
}
```

Then restart:

- `openclaw gateway restart`

Verify:

- `openclaw status --deep`
- `openclaw channels list --json`
- `openclaw logs | tail -n 80`

Expected evidence:
- Telegram shows `ON` / `OK`
- logs include `[default] starting provider (@HiveMind2_bot)` or equivalent

### Case 3: 409 polling conflict
If logs show:

`409 Conflict: terminated by other getUpdates request`

then another bot consumer is still running with the same token.

Check for other local runners, especially:
- another OpenClaw gateway
- Hermes gateway
- old Python wrapper processes
- another machine using the same imported token

A concrete offender previously found:
- `/Users/.../.local/bin/hermes gateway`

Important: Hermes may show up in process listings as a Python process, not as `hermes` in the command name. A real example was:
- `/Library/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python /Users/.../.local/bin/hermes gateway`

So if `lsof` shows an extra Telegram connection but `ps` output looks clean, inspect the PID directly with:
- `ps -p <pid> -o pid,ppid,etime,command`

Kill the extra process and re-check logs.

If conflict persists after killing obvious local processes, assume another machine or service still owns the token.

## Hermes multi-bot / migration confusion diagnosis

Use this flow when a user says they have multiple Hermes Telegram bots, but some are dead or flaky — especially after an OpenClaw → Hermes migration.

1. Inventory actual running gateways first; don't trust bot names from memory.
   - `launchctl list | grep -i hermes`
   - `launchctl list | grep -i openclaw`
   - `ls -1 ~/Library/LaunchAgents | grep -Ei 'hermes|openclaw'`
   - `hermes profile list`
2. Check whether there are really multiple Hermes profiles/services.
   - A single `ai.hermes.gateway` launchd service plus only the `default` profile means only one Hermes Telegram bot can be running cleanly.
   - Old tokens in `~/.openclaw/openclaw*.json` are migration artifacts unless a matching OpenClaw or Hermes profile service is actually loaded.
3. Search for Telegram bot tokens without printing secrets.
   - Prefer hashing/fingerprinting tokens with `sha256(token)[:12]` and using Telegram `getMe` to map each token to a bot username.
   - Check at least:
     - `~/.hermes/.env`
     - `~/.hermes/config.yaml`
     - `~/.hermes/profiles/*/.env`
     - `~/.hermes/profiles/*/config.yaml`
     - `~/.openclaw/config.json`
     - `~/.openclaw/openclaw.json`
     - `~/.openclaw/openclaw-config/*.json`
     - `~/.openclaw/archive-configs/**/*.json`
     - `~/Library/LaunchAgents/*hermes*.plist`
     - `~/Library/LaunchAgents/*openclaw*.plist`
   - If a user names a bot username but no matching valid token appears, do not create a dummy profile. A Telegram username is not enough to run a polling gateway; require the BotFather token.
   - To prove absence, report the set of valid `getMe` usernames found, the services/profiles checked, and the searched locations — but never print tokens.
4. Verify each token directly against Telegram before editing configs.
   - `getMe` confirms bot identity.
   - `getWebhookInfo` confirms webhook state.
   - `deleteWebhook` clears webhook mode if the bot should use polling.
5. Separate transport health from agent-response health.
   - Gateway logs showing `Connected to Telegram (polling mode)` prove the Telegram transport is up.
   - If the bot receives messages but never replies, inspect LLM/provider errors before blaming Telegram.
   - Real Hermes failure pattern: `openai-codex` / `gpt-5.x` non-streaming calls timing out for 700–1000s, iteration-budget exhaustion, or provider API errors. That feels like a flaky bot even when Telegram is connected.
6. For multiple Hermes bots, create one Hermes profile and one service per bot.
   - Do not try to make three bots share one `~/.hermes/.env` and one `ai.hermes.gateway` service.
   - Use profile-specific homes under `~/.hermes/profiles/<name>/`, each with its own `.env` token, allowed users, config, logs, and gateway service.
7. Treat old OpenClaw configs as evidence, not as active services.
   - A valid token found in OpenClaw archives does not mean that bot is currently running.
   - A stale `ai.openclaw.gateway.plist` may exist even when no OpenClaw gateway is loaded.

## Hermes multi-bot repair pattern

When valid Telegram bot tokens are found in old OpenClaw configs but only one Hermes gateway is installed, migrate each real bot into its own Hermes profile/service instead of trying to run multiple bots from one `~/.hermes/.env`.

1. Verify token identity without leaking secrets.
   - Fingerprint tokens with `sha256(token)[:12]`.
   - Use Telegram `getMe` to map fingerprint → `@bot_username`.
   - Use `getWebhookInfo` to ensure `url` is empty when using polling.
   - Ignore invalid/401 tokens found in docs, examples, shell history, or backups.
2. Create one Hermes profile per extra valid bot.
   - `hermes profile create <profile> --clone --no-alias`
   - Profile home becomes `~/.hermes/profiles/<profile>/`.
   - Put that bot's `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`, and optionally `TELEGRAM_HOME_CHANNEL` in the profile `.env`.
   - If the user supplies a BotFather token directly, validate it first with `getMe`, report only the bot username/id and a `sha256(token)[:12]` fingerprint, then write it only to the target profile `.env`.
   - Keep secrets in `.env`; keep model, terminal cwd, and prefill path in `config.yaml`.
   - When cloning a profile, remove deprecated `MESSAGING_CWD` from the new profile `.env` and set `terminal.cwd` in `config.yaml` instead; otherwise Hermes will warn on gateway startup.
3. Install one launchd service per profile on macOS.
   - Default profile: `ai.hermes.gateway`
   - Named profile: `ai.hermes.gateway-<profile>`
   - Command: `hermes --profile <profile> gateway install --force && hermes --profile <profile> gateway start`
   - Verify with `launchctl list | egrep 'ai\.hermes|ai\.openclaw'` and profile-scoped `hermes --profile <profile> gateway status`.
4. Disable stale OpenClaw launchd after migration if it is no longer intended to own a token.
   - `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/ai.openclaw.gateway.plist 2>/dev/null || true`
   - Do this after the replacement Hermes profile is installed, not before token recovery.
5. Fix “flaky bot” behavior by checking model/provider logs, not just Telegram transport.
   - If logs show `openai-codex` / `gpt-5.x` non-streaming calls timing out for 700–1000s, Telegram is not the primary failure.
   - For Mark's Hermes Telegram gateways, OpenRouter `anthropic/claude-sonnet-4` was a reliable replacement for flaky Codex gateway replies.
   - Patch both default and profile configs consistently: `model.provider`, `model.default`, `fallback_model`, `agent.gateway_timeout`, and `agent.max_turns`.
6. Remove deprecated `MESSAGING_CWD` from `.env` once `terminal.cwd` is set in `config.yaml`.
   - Hermes now warns that `MESSAGING_CWD` should move to config.

Example profile/service commands:

```bash
hermes profile create hivemind2 --clone --no-alias
# edit ~/.hermes/profiles/hivemind2/.env with its Telegram token and allowed users
hermes --profile hivemind2 gateway install --force
hermes --profile hivemind2 gateway start
hermes --profile hivemind2 gateway status
```

## Verification for Hermes Telegram bots

Transport verification should include both API-level and service-level checks:

1. `getMe` for each token returns the expected bot username.
2. `getWebhookInfo` shows no webhook URL when polling is expected.
3. `sendMessage` to the allowed/home chat succeeds from each bot token. This proves outbound Telegram delivery, though not full inbound agent roundtrip.
4. Do not call `getUpdates` while the Hermes gateway service is running for that token. Telegram allows only one long-poller; a manual verification call can create a self-inflicted `409 Conflict` that looks like a duplicate bot. If inbound polling must be tested with `getUpdates`, stop the intended gateway first, run one short call, then restart and verify logs.
5. `launchctl list` shows one `ai.hermes.gateway[-profile]` service per bot and no stale `ai.openclaw.gateway` unless intentionally kept.
6. Each gateway log shows `Connected to Telegram (polling mode)`.
7. When checking for conflict recovery after a token rotation or restart, filter log events by timestamp after the restart. Old `polling conflict` lines from before the fresh `Connected to Telegram` line can make a healthy rotated token look broken.
8. `launchctl list` may briefly show a negative `LastExitStatus` (for example `-15`) from the prior process killed during restart. Do not treat that alone as failure if the service has a live PID, the log shows a fresh connection, and outbound Telegram API tests succeed.
9. For full end-to-end confidence, send an inbound message to each bot and confirm the gateway produces an agent reply without model/provider timeout errors.

## Secret hygiene for pasted Telegram tokens

When the user supplies a BotFather token directly in chat/CLI:

1. Validate it with `getMe`, but only report the bot username/id and `sha256(token)[:12]` fingerprint.
2. Write the token only into the intended profile `.env`; do not place it in `config.yaml`, launchd plists, logs, notes, or final summaries.
3. Redact the token from local Hermes command history after operations, especially:
   - `~/.hermes/.hermes_history`
4. If you used shell snippets containing the token, avoid printing `ps auxeww` output verbatim; diagnostic shells can include the token in argv/env and create false-positive leak/poller evidence.

## Final verification

Success requires all of these:

1. `openclaw status --deep` shows Telegram `OK` when repairing OpenClaw itself
2. `openclaw channels list --json` includes Telegram under chat accounts when repairing OpenClaw itself
3. `openclaw logs` no longer shows repeated `getUpdates conflict`
4. For Hermes migrations, each real bot has its own profile-scoped gateway service
5. Test inbound/outbound behavior from Telegram

## Extra lessons worth remembering

- `~/.openclaw/openclaw.json` can look perfectly healthy while the imported `~/.openclaw/config.json` is still the file sabotaging Telegram. Check both, not one.
- `openclaw doctor --deep --non-interactive` may warn that Telegram is in "first-time setup mode" even when status shows the bot is technically OK. That warning does not clear a polling conflict.
- A very specific repeat offender is Hermes running as:
  - `/Users/.../.local/bin/hermes gateway`
  If Hermes and OpenClaw share a Telegram token, they will fight forever.
- Best fix when running both systems: let OpenClaw keep its bot and give Hermes a separate Telegram bot token. Separate bots beat endless 409 conflicts.
- If Hermes appears connected to Telegram but still does not reply, check Hermes model/provider too — Telegram transport can be healthy while the LLM backend is failing every response.

## Hermes-specific follow-up

If the user says the Hermes/QueenBee Telegram bot is configured but still not working:

1. Check for token reuse between OpenClaw and Hermes.
   - OpenClaw token often lives in `~/.openclaw/openclaw.json`
   - Hermes token often lives in `~/.hermes/.env` as `TELEGRAM_BOT_TOKEN`
   - On this family of setups, the intended separate Hermes token may also already exist in `~/.openclaw/openclaw-config/openclaw-second.json`
   - If both use the same bot token, split them immediately by copying the separate Hermes token into `~/.hermes/.env`
2. Verify the target bot token directly with Telegram API:
   - `getMe`
   - `deleteWebhook`
   - `getWebhookInfo`
   This confirms the bot identity and ensures no webhook is blocking polling.
3. Check Hermes runtime status:
   - `hermes status`
   - `hermes gateway status`
   - `tail -n 80 ~/.hermes/logs/gateway.log`
4. If Hermes Telegram connects but replies still fail, inspect Hermes logs for model/provider errors.
   A real failure seen in the field:
   - provider `openai-codex`
   - model `openai-codex/gpt-5.4`
   - HTTP 400: model not supported for the current ChatGPT/Codex account
5. Fix Hermes by switching to a working provider/model pair before retrying Telegram.
   Example recovery:
   - `hermes config set model.provider openrouter`
   - `hermes config set model.default openai/gpt-4o-mini`
6. Restart Hermes gateway after changing token or model.
   - If direct `pkill` of the old gateway is blocked or unreliable, do not thrash there forever; update the token/model, then start Hermes again and verify the new bot is the one polling.
7. Install/start Hermes gateway as a launchd service so it survives shell exit:
   - `hermes gateway install`
   - `hermes gateway start`
   - `hermes gateway status`

Expected healthy Hermes evidence:
- gateway log shows `Connected and polling for Telegram updates`
- repeated successful `getUpdates` requests for the Hermes bot token
- no repeated `getUpdates conflict`
- no model/provider 400 errors during reply generation

## Last-resort fix

If you cannot find the duplicate poller fast, rotate the bot token in BotFather and update only the intended machine. That forcibly evicts every stale runner.

Before rotating, do one useful discriminator:
1. Stop the intended Hermes profile service.
2. Run a single `getUpdates?timeout=5` call with the token.
3. If that one-off call succeeds while the service is stopped, but conflicts resume immediately after the service starts, inspect for local duplicate long-pollers and wrapper commands with the token in their environment/argv:
   - `ps auxeww | grep -F '<token>'` only in a local secure terminal, then redact output in reports.
   - `launchctl list | egrep 'hermes|openclaw'`
   - `lsof -nP -iTCP -sTCP:ESTABLISHED | egrep '149\\.154|91\\.108|Python|node'`
   Beware that your own diagnostic shell/script can appear in `ps auxeww` with the token; do not mistake the current diagnostic command for the stale poller.

## Pitfalls

- Don’t trust only `~/.openclaw/openclaw.json`; imported setups may still be reading or damaging `~/.openclaw/config.json`.
- “Telegram OK” in status can still coexist with inbound polling conflicts. Read the logs.
- Fixing config alone is not enough if another process is still polling.
