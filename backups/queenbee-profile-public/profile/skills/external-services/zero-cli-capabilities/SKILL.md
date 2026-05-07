---
name: zero-cli-capabilities
description: Discover, install, fund, and use the Zero CLI for external paid AI/API capabilities from hosted SKILL.md instructions. Use when the user says use Zero, provides https://www.zero.xyz/SKILL.md, asks to activate paid capabilities, or needs an external service/API the agent cannot do natively.
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [zero, external-services, paid-apis, capabilities, x402, wallet, cli]
    related_skills: [hermes-agent, hermes-agent-setup]
---

# Zero CLI Capabilities

## When to Use

Use this skill for the class of tasks where the user wants the agent to discover or activate external capabilities through Zero, especially:

- The user says “use Zero” or links `https://www.zero.xyz/SKILL.md`.
- The user asks for a capability not available natively: image generation, weather, translation, business lookup, data enrichment, geolocation, scraping, currency conversion, stock prices, audio/video processing, etc.
- The task may require paid API calls, x402/MPP payment, or a wallet-funded service.

Do **not** use Zero for local files, code edits, shell commands, math, or things the current toolset already handles well.

## Setup / Discovery

1. Read the live Zero skill when the user explicitly provides it, because its instructions may change:
   ```bash
   curl -fsSL https://www.zero.xyz/SKILL.md
   ```
2. Check before installing:
   ```bash
   command -v zero || true
   zero --version 2>/dev/null || true
   ```
3. Install only if missing:
   ```bash
   command -v zero >/dev/null || curl -fsSL https://zero.xyz/install.sh | bash
   ```
4. In Hermes profile-backed shells, `zero` may install under the profile home. Export PATH for the current shell:
   ```bash
   export PATH="$HOME/.zero/bin:$PATH"
   ```
5. Verify:
   ```bash
   zero --version
   zero wallet balance
   ```

## Wallet / Funding

Zero uses a wallet identity and USDC on Base for paid calls.

- If no wallet exists, `zero init` creates one; the installer may also create it.
- In an agent/headless session, always use `--no-open` for funding URLs:
  ```bash
  zero wallet fund --no-open
  zero wallet fund --manual
  zero wallet balance
  ```
- Hand the funding URL or address to the user. Do not open one-time funding URLs yourself.

## Capability Loop

Always run the full loop; do not reuse old schemas, prices, or URLs from memory.

1. Search:
   ```bash
   ZERO_AGENT=codex zero search "image generation"
   ```
2. Inspect before calling:
   ```bash
   zero get 1 --formatted
   zero get 1
   ```
   If `bodySchema` is `null`, skip that capability rather than guessing fields.
3. Call with a cost cap:
   ```bash
   zero fetch "<url>" --max-pay 0.50
   zero fetch "<url>" -d '{"text":"hello","to":"es"}' -H "Content-Type:application/json" --max-pay 0.50
   ```
4. For programmatic handling, prefer JSON and check `ok`, not only HTTP status:
   ```bash
   zero fetch --json "<url>" --max-pay 0.50 | jq .
   ```
5. Review paid calls using the printed Run ID:
   ```bash
   zero review <runId> --accuracy 5 --value 4 --reliability 5 --content "Concrete observation about the task, latency, output quality, and any gotchas."
   ```
6. Before ending a multi-call Zero task, check missed reviews:
   ```bash
   zero runs --unreviewed
   ```

## Request Shape Rules

- `zero get` may describe an envelope with `method` and `queryParams` or `body`.
- For GET calls, encode `queryParams` into the URL query string.
- For POST calls, send only the actual JSON body with `-d`; do **not** POST the whole schema/envelope.
- Use `--max-pay` for unfamiliar capabilities.

## Hermes / Local Environment Gotchas

- On Mark’s machine, `/usr/local/bin/hermes` can be a different HERMES workflow CLI; when comparing to Hermes Skills Hub, use the actual Hermes Agent binary such as `/Users/markrubin/.hermes/hermes-agent/venv/bin/hermes` or `~/.local/bin/hermes`.
- Hermes Skills Hub and Zero are different: Hermes skills are reusable procedures/instructions; Zero is a paid executable capability/API marketplace.
- If `zero` was just installed but the shell cannot find it, export `$HOME/.zero/bin` into PATH for that command.

## Cross-Machine Sync

When syncing Hermes skills between trusted machines and the user asks to include Zero:

- Sync the Hermes profile's `skills/` directory separately from Zero state; do not clone the whole Hermes profile.
- If the user wants the same Zero wallet identity on both trusted machines, sync only the profile-home `home/.zero/config.json` over SSH and set restrictive permissions (`chmod 700 .zero`, `chmod 600 config.json`).
- Do **not** rsync the Zero CLI binary between machines; install Zero natively on the target so the correct OS/architecture build is used.
- Verify remotely with `zero --version` and `zero wallet balance` after setting `HOME` to the target Hermes profile home and adding `$HOME/.zero/bin` to PATH.
- Treat `config.json` as sensitive because it contains the wallet private key. Stop at SSH public-key setup if access fails; do not fall back to insecure copy/paste or password prompts for secrets.

## Verification

- `zero --version` works.
- `zero wallet balance` returns a balance rather than a command-not-found error.
- `zero search "<capability>"` returns ranked capabilities.
- For paid calls, the response was inspected and a review was submitted or `zero runs --unreviewed` is clean.
