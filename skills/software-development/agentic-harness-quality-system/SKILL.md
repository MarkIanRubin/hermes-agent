---
name: agentic-harness-quality-system
description: "Use when hardening Hermes or any coding-agent workflow with ECC-inspired harness patterns: scoped installs, doctor/repair state, evidence-first code review, supply-chain gates, hook safety, session observability, and low-noise agent rules."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [agentic-engineering, harness, quality-gates, security, hooks, skills, verification]
    related_skills: [requesting-code-review, systematic-debugging, subagent-driven-development, hermes-agent, hermes-operations]
---

# Agentic Harness Quality System

## Overview

This skill distills the best reusable patterns extracted from `affaan-m/ECC` into Hermes-native operating rules. ECC's strongest ideas are not its branding or bulk install; they are the harness primitives underneath: install only what is needed, track what the harness owns, validate hooks before they run, make code review evidence-based, preserve session state deliberately, and fail closed on supply-chain risk.

Use this as a **quality-system overlay**, not as a giant context dump. The point is sharper agents, fewer ghosts, and verifiable work.

## When to Use

- You are improving Hermes skills, profile setup, gateway/runtime operations, or coding-agent workflows.
- You are designing rules/hooks/scripts that will affect many agents or profiles.
- A bot keeps repeating low-quality behavior: shallow review, invented findings, forgotten state, unsafe shell commands, duplicate installs, or brittle config edits.
- You are adding a new skill pack, install surface, profile template, or project workflow.
- You need a pre-commit / pre-release checklist for agent harness changes.

Do **not** use this to blindly import every ECC skill/agent/command. Bulk harness layering creates context fog. Steal patterns surgically.

## Core Pattern: Small Surface, Strong Contract

Before adding any harness behavior, define the contract:

1. **Trigger:** exactly when should this load or run?
2. **Owner:** what files/config/state does it own?
3. **Non-owner boundary:** what must it never touch?
4. **Failure mode:** warn, block, retry, or escalate?
5. **Verification:** what proves it worked?
6. **Rollback:** how do we undo it cleanly?

If you cannot answer those six, the harness change is not ready.

## Pattern 1 — Selective Install Beats Full Install

ECC's installer pattern is right: choose profile/components/targets, write managed state, and avoid stacking install methods.

Hermes adaptation:

- Install only the skills/tooling needed by the bot or project.
- Prefer explicit profile-scoped skills over dumping every skill into every active prompt.
- If a shared workflow matters to all bots, ship it as a compact skill and copy/sync it into profile skill dirs; do not bloat SOUL.md with procedure text.
- Never stack two install paths that manage the same files unless ownership is explicit.

Minimum install-state record for managed files:

```json
{
  "manager": "hermes-agentic-harness-quality-system",
  "version": "1.0.0",
  "installed_at": "ISO-8601 timestamp",
  "target_profile": "profile-name",
  "files": [
    {"path": "skills/software-development/example/SKILL.md", "sha256": "..."}
  ]
}
```

Use this for future sync scripts so `doctor`, `repair`, and `uninstall` are possible.

## Pattern 2 — Doctor / Repair / Uninstall for Harness-Owned Files

Any harness feature that writes files should have three maintenance modes:

- **doctor:** compare expected files/hashes/config keys against current state; report drift without mutating.
- **repair:** restore only managed files/keys; preserve user-owned files.
- **uninstall:** remove only files recorded in managed state; never glob-delete neighboring user work.

Operational rule:

```text
No manifest, no destructive cleanup.
```

If state is missing, produce a recovery plan instead of guessing ownership.

## Pattern 3 — Evidence-First Code Review

ECC's best review lesson is false-positive control. A review that invents issues is worse than no review because it teaches the team to ignore the reviewer.

Reviewer gate:

1. Read the surrounding code, not just the changed line.
2. For HIGH/CRITICAL findings, cite exact file/line and a concrete failure scenario.
3. Distinguish:
   - **Bug:** demonstrably wrong behavior.
   - **Risk:** plausible but unproven; explain assumptions.
   - **Suggestion:** taste/performance/maintainability only.
4. If confidence is below 80%, demote or drop.
5. A clean review is valid. Do not manufacture findings to look useful.

Use this prompt block inside reviewer subagents:

```text
Evidence rule: report a finding only if you can cite the exact changed line, the surrounding context you inspected, and the concrete failure mode. HIGH/CRITICAL requires an executable or logically unavoidable failure scenario. If the issue is speculative, mark it MEDIUM/LOW or omit it. Returning zero findings is acceptable and expected when the diff is sound.
```

## Pattern 4 — Supply-Chain Gates Fail Closed

Agent harnesses run code, load plugins, execute hooks, and touch credentials. Treat dependency changes and hook changes as security-sensitive.

Run these checks before accepting harness/runtime changes:

- Dependency install uses lifecycle-script suppression when possible (`npm ci --ignore-scripts`, equivalent for other managers).
- Lockfiles are reviewed for new packages with suspicious postinstall/preinstall scripts.
- GitHub workflows do not use dangerous `pull_request_target` checkout refs or shared caches in privileged contexts.
- Hooks do not execute untrusted paths, shell-expanded user input, or inline scripts that cannot be validated.
- Secrets are not written into config, docs, examples, logs, or install state.
- Release/publish paths use least privilege and provenance where available.

Minimum shell checks:

```bash
git diff --cached -- package-lock.json yarn.lock pnpm-lock.yaml pyproject.toml requirements*.txt
git diff --cached | grep '^+' | grep -Ei '(postinstall|preinstall|curl .*\|.*sh|wget .*\|.*sh|eval\(|exec\(|TOKEN|API_KEY|SECRET|PASSWORD)' || true
```

A match is not automatically malicious, but it must be explained before shipping.

## Pattern 5 — Hook Safety: Validate Before Runtime

Hooks are useful and dangerous. They run at the exact moment an agent is least likely to stop and reason.

Hook rules:

- Prefer small script files over long inline shell blobs.
- Use absolute or repo-root-relative paths resolved safely.
- Pass arguments as arrays where the platform supports it; avoid `eval`.
- Keep default hook profile minimal; strict gates should be opt-in or profile-specific.
- Every blocking hook must print the exact reason and the smallest corrective action.
- Async hooks must have timeouts and must not hide critical failures.

Validation checklist:

- [ ] JSON/YAML syntax valid.
- [ ] Hook event names are known by the target harness.
- [ ] Commands resolve from a clean working directory.
- [ ] Timeout exists for network/file-system scanners.
- [ ] Secret-like values are redacted from logs.
- [ ] Failure behavior is tested: pass, warn-only, block.

## Pattern 6 — Session Observability Without Memory Explosion

Useful agents preserve handoff state; bad agents dump transcripts into memory.

Hermes adaptation:

- Store durable facts in base memory only when they survive future sessions.
- Store large project/source material in MemPalace, Obsidian, or repo docs.
- Store workflow lessons as skills, not memories.
- Store operational session snapshots as bounded logs: title, goal, changed files, tests run, blockers, next action.
- Sample long logs from the tail plus explicit error windows; do not inject raw 100k-line output into prompts.

Session snapshot shape:

```markdown
# Session Snapshot
- Goal:
- Repo/profile:
- Files touched:
- Commands run:
- Verification:
- Remaining risk:
- Next action:
```

## Pattern 7 — Agent Rules Should Be Few, Sharp, and Non-Contradictory

ECC has many rules; the transferable lesson is not quantity, it is **specificity**.

Good rule:

```text
Before editing shared config, inspect current config, identify owner, create a backup, edit the smallest key, restart the process that loads it, then verify fresh logs.
```

Bad rule:

```text
Always be production-ready and secure.
```

Rule hygiene:

- Delete stale rules that no one follows.
- Merge duplicate rules into one canonical line.
- Avoid absolutes like “always TDD” unless the workflow truly requires it.
- Put project-specific doctrine in the project instructions, not global personality files.
- Put procedures in skills, not SOUL.md.

## Pattern 8 — Cross-Harness Adapters Need a Capability Matrix

When supporting Claude Code, Codex, OpenCode, Cursor, Gemini, Hermes, or custom bots, do not assume parity.

For each target harness, record:

- Skill/rule file location.
- Hook/event support.
- Tool invocation model.
- Sandbox/approval model.
- Memory/session persistence model.
- MCP support.
- Config merge behavior.
- Uninstall/repair path.

If a capability is missing, degrade explicitly. Do not silently install a no-op.

## Pattern 9 — Harness Changes Need a Real Test Surface

A serious harness repo needs tests for the boring plumbing:

- Skill/frontmatter validation.
- Command registry consistency.
- Hook schema validation.
- Install manifest resolution.
- No personal absolute paths in shipped docs/skills.
- No secrets in examples/tests.
- Installer dry-run output.
- Doctor/repair/uninstall preserving user files.
- Cross-platform path handling.
- Security workflow validation.

For Hermes changes, prefer targeted tests first, then full suite when feasible:

```bash
python -m pytest tests/ -o 'addopts=' -q
```

For Node-based harness utilities:

```bash
npm ci --ignore-scripts
npm test
```

## One-Shot Recipe — Hardening a Bot/Profile Skill Surface

1. List the profile and current skill dirs.
2. Identify shared vs profile-specific skills.
3. Remove duplicate narrow session-shaped skills only after merging their reusable lessons into an umbrella skill.
4. Add the new umbrella skill with compact triggers and concrete verification.
5. Restart or reset the bot/session so skill discovery reloads.
6. Smoke-test with a query that should trigger the skill.

## One-Shot Recipe — Reviewing a Harness PR

1. Inspect changed files and ownership boundaries.
2. Run schema/manifest validators.
3. Run dependency/hook/security scans.
4. Run targeted tests for touched surfaces.
5. Ask an independent reviewer for evidence-based findings only.
6. Check for context bloat: did this add large always-on text where a skill/reference would do?
7. Verify rollback path for any file-writing installer or migration.

## Common Pitfalls

1. **Installing everything because it is available.** More skills can make the agent worse. Install by trigger and value.
2. **No ownership manifest.** Without state, repair/uninstall becomes guesswork.
3. **Blocking hooks that do not explain the fix.** Agents will loop or bypass them.
4. **Reviewer theater.** Manufactured findings waste time and erode trust.
5. **Memory dumping.** Store durable lessons as skills; store archives in project knowledge systems.
6. **Cross-harness fantasy.** Different agents support different hooks, sandboxes, and config merge behavior.
7. **Docs as proof.** A README saying “secure” is not evidence. Tests, validators, and live smoke checks are evidence.

## Verification Checklist

- [ ] The change has a defined trigger, owner, failure mode, verification target, and rollback path.
- [ ] No global context was bloated when a skill/reference would work.
- [ ] Any managed files have an ownership/manifest story.
- [ ] Hooks/config/installers were tested in dry-run or isolated mode before live use.
- [ ] Code review findings cite evidence and do not manufacture issues.
- [ ] Supply-chain and secret scans were run for dependency/hook/workflow changes.
- [ ] The exact bot/profile/session that will use the change was restarted or told to reset.
