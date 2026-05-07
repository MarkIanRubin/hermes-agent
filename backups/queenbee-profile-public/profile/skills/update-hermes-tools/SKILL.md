---
name: update-hermes-tools
description: Update a local Hermes Agent source checkout, migrate config, restart the gateway, and verify what still remains.
---

# Update Hermes Tools Skill

## Purpose
Use this when Hermes is installed from source in `~/.hermes/hermes-agent` and the user wants the new features integrated, not just a package bump.

The old generic advice to upgrade a published Python package is not the right method for Mark's setup.

## When to use
- User asks for a Hermes update or says to integrate new features.
- Hermes is running from the local repo/venv.
- You need to verify the gateway and config after updating code.

## Proven workflow
1. Confirm which Hermes binary is the real one.
   - On Mark's machine, `/usr/local/bin/hermes` is a different workflow CLI.
   - The real Hermes Agent entrypoint is `~/.local/bin/hermes`.

2. Work from the source checkout at `~/.hermes/hermes-agent`.
   - Activate the repo virtualenv before Python or uv commands.
   - Use `git rev-parse --abbrev-ref HEAD` instead of `git branch --show-current` if the installed Git is old.

3. Preserve dirty local work before updating.
   - If `git status --short` is not clean, create a safety branch and commit the dirty work there before pulling `main`.
   - Example: `git checkout -b safety/hermes-update-$(date +%Y%m%d-%H%M%S) && git add <dirty-files> && git commit -m "chore: preserve local changes before update" && git checkout main`.

4. Update the git checkout and reinstall the editable package from the repo.
   - Run `git fetch origin`, check `git rev-list --left-right --count HEAD...origin/main`, then `git pull --ff-only origin main`.
   - Then verify/reinstall from the active repo venv: `python -m pip install -e .`.

5. Immediately check for config drift and status.
   - Run config check, overall status, and skills check.

6. If config is behind, run the Hermes config migration flow.

7. Restart the Hermes gateway after code or config changes.

8. Run Hermes doctor to verify the update.

## Good follow-up cleanup
- Run doctor auto-fix for anything Hermes can repair safely.
- If doctor flags browser dependency vulnerabilities, fix the repo npm dependencies from the repo root and re-run doctor.
- If doctor flags `tinker-atropos`, initialize submodules and install that editable package in the venv.

## Important finding
Installing `tinker-atropos` can fail if Git LFS is missing. If the install complains that `git-lfs` is not found while pulling Atropos submodules, install Git LFS first, initialize it, and then retry the install.

## What not to overpromise
After updating, some warnings may remain because they are upstream or credential-related, not because the update failed.

Also, `hermes --version` can still print an `Update available` line even when the repo is fully synced. Verify the real sync state with git, e.g. `git rev-list --left-right --count HEAD...origin/main`, before claiming the update missed commits.

Examples:
- WhatsApp bridge vulnerabilities in the Baileys/libsignal/protobuf chain with no automatic fix available. `npm audit fix` may bump the top-level `protobufjs` to 7.5.5, but the nested `libsignal` copy can still remain vulnerable and keep the advisory open. After running `npm audit fix`, inspect `git status`/`git diff`; it may leave `scripts/whatsapp-bridge/package-lock.json` modified even though doctor still reports the nested advisory.
- Missing optional API keys for web, browser, image generation, or RL features
- Missing OAuth logins for optional providers

Call that out plainly instead of pretending everything is fully integrated.

## Verification checklist
- Hermes reports the new version
- Config check shows the current config version
- Gateway restarts successfully
- Doctor passes core checks
- Remaining issues are clearly categorized as upstream dependency debt or missing optional credentials/config

## Notes
- Prefer `~/.local/bin/hermes` over bare `hermes` on Mark's machine.
- For Mark's source install, the right update path is the repo checkout plus editable reinstall, not a generic package-only upgrade.
- If repo-managed dependencies change, inspect git status so the scope stays intentional.
