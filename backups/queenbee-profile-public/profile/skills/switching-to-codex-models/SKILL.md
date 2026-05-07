---
name: switching-to-codex-models
description: Switch the Hermes Agent default model by editing config.yaml. The model is locked at session start — changes take effect next session.
tags: [hermes, config, model-switching]
---

# Switching Hermes Agent Models

## When to Use
User asks to switch Hermes models/providers (e.g., "switch to GPT-5.5", "use Claude Opus", "change model"), including profile-scoped gateway bots under `~/.hermes/profiles/<name>/`.

## Key Facts
- The model is set at session start and CANNOT be changed mid-session for an existing CLI chat.
- Gateway/profile config changes require a gateway restart before Telegram/Discord/etc. bot sessions use the new model.
- Default config file: `~/.hermes/config.yaml`
- Profile config file: `~/.hermes/profiles/<profile>/config.yaml`
- The relevant fields are `model.default` and `model.provider`.
- OpenAI Codex OAuth credentials live in `auth.json`, not `.env`. Profile-scoped gateways may need the default `~/.hermes/auth.json` OpenAI Codex provider/credential_pool copied or merged into `~/.hermes/profiles/<profile>/auth.json`.
- Do NOT attempt terminal commands like `hermes model set`, `codex-agent`, `hivemind-agent` — none of these exist.

## Steps

1. Identify scope first:
   - Default CLI/gateway: `~/.hermes/config.yaml` and `~/.hermes/auth.json`
   - Named profile gateway: `~/.hermes/profiles/<profile>/config.yaml` and `~/.hermes/profiles/<profile>/auth.json`

2. Read the current config to confirm the active model/provider:
   ```bash
   python3 - <<'PY'
   from pathlib import Path
   import yaml
   for p in [Path.home()/'.hermes/config.yaml', *Path.home().glob('.hermes/profiles/*/config.yaml')]:
       if p.exists():
           cfg=yaml.safe_load(p.read_text()) or {}
           print(p, cfg.get('model'))
   PY
   ```

3. Edit the target config(s):
   ```yaml
   model:
     default: gpt-5.5             # or openai/gpt-5.4, anthropic/claude-opus-4.6, etc.
     provider: openai-codex       # set explicitly when user asks for Codex auth
     base_url: null               # clear stale provider-specific overrides
     api_key: '[REDACTED]'
   ```

4. For profile-scoped OpenAI Codex switches, ensure the profile has the same Codex OAuth auth as the default profile:
   - Confirm default `~/.hermes/auth.json` has `providers.openai-codex` and/or `credential_pool.openai-codex`.
   - Merge those entries into `~/.hermes/profiles/<profile>/auth.json`.
   - Set profile `active_provider` to `openai-codex`.
   - Preserve unrelated profile credentials like `openrouter` unless deliberately removing them.
   - Keep `auth.json` mode `0600`.

5. For slow GPT-5.x/Codex gateway bots, set generous timeouts in each target config:
   ```yaml
   agent:
     gateway_timeout: 900
     api_timeout: 900
   ```

6. Restart any affected gateway service so messaging bots pick up the new config:
   ```bash
   launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway-<profile>
   # default profile service is usually ai.hermes.gateway
   ```

7. Verify:
   - Config shows the requested `model.default` and `model.provider`.
   - Profile `auth.json` has `active_provider: openai-codex` and a non-empty OpenAI Codex credential pool.
   - `launchctl print gui/$(id -u)/ai.hermes.gateway[-profile]` shows a running PID.
   - Profile gateway logs show a fresh `Connected to Telegram (polling mode)` / gateway running line after restart.

8. Tell the user: CLI model changes take effect on the **next session**; gateway bot changes take effect after the gateway restart.

## Common Model Strings
- `gpt-5.5` (Codex/ChatGPT backend on this machine)
- `openai/gpt-5.4`
- `anthropic/claude-opus-4.6`
- `anthropic/claude-sonnet-4`
- `openai/gpt-5.2-codex`

## Pitfalls
- Do NOT try to change the current running CLI chat's model mid-session; start a new session.
- Do restart gateway services for profile-backed Telegram/Discord/etc. bots; otherwise they keep running with the old config.
- Do NOT fabricate terminal commands to switch models. Direct config/auth edits or `hermes model` are the reliable paths.
- Do not put OAuth tokens in `.env` or final summaries. For OpenAI Codex, handle `auth.json` and redact/summarize only.
- When verifying Telegram gateways, do not call `getUpdates` while the service is already polling; that creates a fake 409 conflict.
- If `hermes setup` is available, that's an alternative interactive way to change settings, but direct config edit is faster and more reliable for multiple profiles.
