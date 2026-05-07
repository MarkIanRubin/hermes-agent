---
name: hermes-agent-setup
description: Help users configure Hermes Agent — CLI usage, setup wizard, model/provider selection, tools, skills, voice/STT/TTS, gateway, and troubleshooting. Use when someone asks to enable features, configure settings, or needs help with Hermes itself.
version: 1.1.0
author: [REDACTED]
tags: [setup, configuration, tools, stt, tts, voice, hermes, cli, skills]
---

# Hermes Agent Setup & Configuration

Use this skill when a user asks about configuring Hermes, enabling features, setting up voice, managing tools/skills, or troubleshooting.

## Key Paths

- Config: `~/.hermes/config.yaml`
- API keys: `~/.hermes/.env`
- Skills: `~/.hermes/skills/`
- Hermes install: `~/.hermes/hermes-agent/`
- Venv: `~/.hermes/hermes-agent/venv/`

## CLI Overview

Hermes is used via the `hermes` command (or `python -m hermes_cli.main` from the repo).

### Core commands:

```
hermes                          Interactive chat (default)
hermes chat -q "question"       Single query, then exit
hermes chat -m MODEL            Chat with a specific model
hermes -c                       Resume most recent session
hermes -c "project name"        Resume session by name
hermes --resume SESSION_ID      Resume by exact ID
hermes -w                       Isolated git worktree mode
hermes -s skill1,skill2         Preload skills for the session
hermes --yolo                   Skip dangerous command approval
```

### Configuration & setup:

```
hermes setup                    Interactive setup wizard (provider, API keys, model)
hermes model                    Interactive model/provider selection
hermes config                   View current configuration
hermes config edit              Open config.yaml in $EDITOR
hermes config set KEY VALUE     Set a config value directly
hermes login                    Authenticate with a provider
hermes logout                   Clear stored auth
hermes doctor                   Check configuration and dependencies
```

### Tools & skills:

```
hermes tools                    Interactive tool enable/disable per platform
hermes skills list              List installed skills
hermes skills search QUERY      Search the skills hub
hermes skills install NAME      Install a skill from the hub
hermes skills config            Enable/disable skills per platform
```

### Gateway (messaging platforms):

```
hermes gateway run              Start the messaging gateway
hermes gateway install          Install gateway as background service
hermes gateway status           Check gateway status
```

### Session management:

```
hermes sessions list            List past sessions
hermes sessions browse          Interactive session picker
hermes sessions rename ID TITLE Rename a session
hermes sessions export ID       Export session as markdown
hermes sessions prune           Clean up old sessions
```

### Other:

```
hermes status                   Show status of all components
hermes cron list                List cron jobs
hermes insights                 Usage analytics
hermes update                   Update to latest version
hermes pairing                  Manage DM authorization codes
```

## Setup Wizard (`hermes setup`)

The interactive setup wizard walks through:
1. **Provider selection** — OpenRouter, Anthropic, OpenAI, Google, DeepSeek, and many more
2. **API key entry** — stores securely in the env file
3. **Model selection** — picks from available models for the chosen provider
4. **Basic settings** — reasoning effort, tool preferences

Run it from terminal:
```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
python -m hermes_cli.main setup
```

To change just the model/provider later: `hermes model`

## Safely Porting Hermes Tuning Between Profiles

Use this when a user wants to move Hermes tuning, skills, or Telegram coding context from one Hermes home/profile to another profile-backed bot (for example default `~/.hermes` → `~/.hermes/profiles/<bot>`).

Do **not** copy an active Hermes home wholesale. That drags secrets, bot identity, sessions, logs, locks, stale state, and provider credentials into the target bot. Treat the task as three separate lanes:

1. **Code** — use git. First inspect and snapshot dirty work in the target repo:
   ```bash
   git -C /path/to/repo status --short
   git -C /path/to/repo diff --stat
   git -C /path/to/repo checkout -b backup/before-hermes-profile-sync
   git -C /path/to/repo add <intentional files>
   git -C /path/to/repo commit -m "Snapshot before Hermes profile sync"
   ```
2. **Skills** — dry-run `rsync` from source skills to target profile skills:
   ```bash
   rsync -avni ~/.hermes/skills/ ~/.hermes/profiles/<profile>/skills/
   # if sane:
   rsync -av ~/.hermes/skills/ ~/.hermes/profiles/<profile>/skills/
   ```
3. **Config/auth** — diff and cherry-pick. Do not overwrite `config.yaml`, `.env`, or `auth.json` unless the user explicitly wants the same model/auth/bot identity.

Before planning a sync, inspect:
```bash
# profiles
find ~/.hermes/profiles -maxdepth 1 -mindepth 1 -type d -print

# key config values
python3 - <<'PY'
from pathlib import Path
import yaml, json
for root in [Path.home()/'.hermes', *Path.home().glob('.hermes/profiles/*')]:
    cfgp=root/'config.yaml'
    if not cfgp.exists(): continue
    cfg=yaml.safe_load(cfgp.read_text()) or {}
    print('\n##', root)
    print('model=', cfg.get('model'))
    print('terminal.cwd=', (cfg.get('terminal') or {}).get('cwd'))
    print('toolsets=', cfg.get('toolsets'))
    print('memory=', cfg.get('memory'))
PY
```

Always exclude runtime/secret/state paths from profile syncs:
```bash
rsync -avni \
  --exclude '.env' \
  --exclude 'auth.json' \
  --exclude 'profiles/' \
  --exclude 'logs/' \
  --exclude 'sessions/' \
  --exclude 'cache/' \
  --exclude 'state.db*' \
  --exclude 'gateway.pid' \
  --exclude 'gateway.lock' \
  --exclude 'cron/.tick.lock' \
  --exclude '.hermes_history' \
  --exclude 'hermes-agent/' \
  ~/.hermes/ ~/.hermes/profiles/<profile>/
```

For Telegram bots, keep each profile's `.env` Telegram token isolated. Copying `.env` is changing bot identity. Cron jobs (`cron/jobs.json`) also need separate review because delivery targets and profile context can be wrong.

After intentional profile changes, restart and verify the affected gateway:
```bash
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway-<profile>
launchctl print gui/$(id -u)/ai.hermes.gateway-<profile> | egrep 'state =|pid =|last exit code|program ='
tail -80 ~/.hermes/profiles/<profile>/logs/gateway.log
```

### Keeping Skills in Sync Across Two Trusted Machines

Use this when the user runs Hermes on a small fixed set of trusted machines and wants one profile's skills to stay synchronized between them. Treat this as a **skills/config sync**, not a full Hermes-home clone.

Recommended pattern:
1. Pick one source of truth, e.g. `Lifeislucky -> macmini`.
2. Create a dedicated SSH key for the sync and add only the public key to the target machine's `~/.ssh/authorized_keys`.
3. Sync only `$HERMES_HOME/skills/` with `rsync -az --delete` after verifying the target path.
4. Do **not** sync `.env`, `auth.json`, sessions, logs, caches, gateway locks, or whole profile homes unless explicitly requested.
5. For Zero, sync the profile's `home/.zero/config.json` only between trusted machines if the user wants the same wallet identity. Do **not** rsync the Zero CLI binary; install it natively on the target so architecture-specific builds are correct.
6. Verify remotely with a count of `SKILL.md` files, `zero --version`, and `zero wallet balance`.

Skeleton:
```bash
SRC_PROFILE=/Users/<user>/.hermes/profiles/<profile>
DST=remoteuser@remotehost
DST_PROFILE=/Users/<remoteuser>/.hermes/profiles/<profile>
KEY="$SRC_PROFILE/home/.ssh/hermes-skills-sync"

ssh-keygen -t ed25519 -f "$KEY" -N '' -C "hermes-skills-sync"  # if missing
cat "$KEY.pub"  # user adds this to target authorized_keys

ssh -i "$KEY" -o IdentitiesOnly=yes "$DST" "mkdir -p '$DST_PROFILE/skills' '$DST_PROFILE/home/.zero'"
rsync -az --delete -e "ssh -i '$KEY' -o IdentitiesOnly=yes" \
  "$SRC_PROFILE/skills/" "$DST:$DST_PROFILE/skills/"

# Optional/sensitive: same Zero wallet identity on both trusted machines.
rsync -az -e "ssh -i '$KEY' -o IdentitiesOnly=yes" \
  "$SRC_PROFILE/home/.zero/config.json" "$DST:$DST_PROFILE/home/.zero/config.json"
ssh -i "$KEY" "$DST" "chmod 700 '$DST_PROFILE/home/.zero'; chmod 600 '$DST_PROFILE/home/.zero/config.json'"

# Install Zero natively on target if absent.
ssh -i "$KEY" "$DST" "export HOME='$DST_PROFILE/home'; export PATH=\"\$HOME/.zero/bin:\$PATH\"; command -v zero >/dev/null || curl -fsSL https://zero.xyz/install.sh | bash"
ssh -i "$KEY" "$DST" "export HOME='$DST_PROFILE/home'; export PATH=\"\$HOME/.zero/bin:\$PATH\"; find '$DST_PROFILE/skills' -name SKILL.md | wc -l; zero --version; zero wallet balance"
```

Security note: Zero `config.json` contains a wallet private key. Only sync it to machines the user explicitly trusts, over SSH, with restrictive file permissions. If SSH access fails, stop at the public-key authorization step rather than falling back to password prompts or copying secrets another way.

## Auditing and Cleaning Duplicate macOS Gateway LaunchAgents

Use this when Hermes on macOS has confusing gateway behavior, duplicate profile bots, stale background sessions, or multiple `hermes` binaries on PATH. The class of problem is: **Hermes is installed/running from multiple entrypoints or LaunchAgents, so first inventory the live processes and service definitions before removing anything.**

Survey first:
```bash
# Which Hermes binary is being used?
command -v -a hermes 2>/dev/null || true
ls -l /usr/local/bin/hermes ~/.local/bin/hermes 2>/dev/null || true
file /usr/local/bin/hermes ~/.local/bin/hermes 2>/dev/null || true

# Active Hermes/gateway processes
ps aux | grep -i '[h]ermes\|[g]ateway' | sed -n '1,160p'

# macOS user LaunchAgents
find ~/Library/LaunchAgents /Library/LaunchAgents -maxdepth 1 -iname '*hermes*' -print 2>/dev/null
```

Inspect LaunchAgent payloads before touching them:
```bash
python3 - <<'PY'
from pathlib import Path
import plistlib, json
for p in sorted(Path.home().glob('Library/LaunchAgents/*hermes*.plist')):
    try:
        d = plistlib.loads(p.read_bytes())
        print(json.dumps({
            'file': str(p),
            'label': d.get('Label'),
            'program_arguments': d.get('ProgramArguments'),
            'run_at_load': d.get('RunAtLoad'),
            'keep_alive': d.get('KeepAlive'),
        }, indent=2))
    except Exception as e:
        print(p, e)
PY
```

Cleanup rules:
- Keep the active profile LaunchAgent the user is chatting through unless explicitly replacing it.
- Do not delete profile LaunchAgents blindly; unload/disable stale ones first, and keep a backup copy of the `.plist`.
- On Mark's machine, `/usr/local/bin/hermes` may be an unrelated HERMES workflow CLI. Prefer `~/.local/bin/hermes` or `python -m hermes_cli.main` for Hermes Agent commands.
- Kill stale interactive `~/.local/bin/hermes` processes only after confirming they are not the active gateway process.

Safe unload/backup pattern:
```bash
uid=$(id -u)
label='ai.hermes.gateway-oldprofile'
plist="$HOME/Library/LaunchAgents/$label.plist"
mkdir -p "$HOME/Library/LaunchAgents/disabled-hermes"
launchctl bootout "gui/$uid/$label" 2>/dev/null || true
mv "$plist" "$HOME/Library/LaunchAgents/disabled-hermes/"  # reversible
launchctl print "gui/$uid/$label" 2>/dev/null || true
```

After cleanup, verify the kept gateway:
```bash
label='ai.hermes.gateway-queen_bee_obsidian'
launchctl kickstart -k "gui/$(id -u)/$label"
launchctl print "gui/$(id -u)/$label" | egrep 'state =|pid =|last exit code|program ='
tail -80 ~/.hermes/profiles/queen_bee_obsidian/logs/gateway.log
```

### Fixing `hermes` PATH collisions on macOS

Use this when `hermes --version` invokes a different tool even though `~/.local/bin/hermes` exists.

1. Confirm the collision and the real user home. In profile-backed Telegram sessions, `$HOME` may point at a Hermes profile home, so test Mark's shell with `HOME=/Users/markrubin`:
   ```bash
   command -v -a hermes 2>/dev/null || true
   ls -l /usr/local/bin/hermes /Users/markrubin/.local/bin/hermes 2>/dev/null || true
   file /usr/local/bin/hermes /Users/markrubin/.local/bin/hermes 2>/dev/null || true
   env HOME=/Users/markrubin zsh -ic 'echo HOME=$HOME; whence -a hermes; type hermes; hermes --version 2>&1 | head -8'
   ```
2. Back up shell startup files before editing:
   ```bash
   backup="$HOME/.hermes/backups/shell-path-$(date +%Y%m%d-%H%M%S)"
   mkdir -p "$backup"
   cp -p ~/.zshrc ~/.zprofile ~/.profile ~/.bash_profile "$backup"/ 2>/dev/null || true
   ```
3. In `~/.zshrc` and `~/.zprofile`, prefer zsh's `path` array over only prepending `PATH`. zsh can keep `PATH` entries unique, so a later duplicate `~/.local/bin` may not move to the front with plain `export PATH="$HOME/.local/bin:$PATH"`.
   ```zsh
   # Hermes command cleanup
   path=("$HOME/.local/bin" ${path:#$HOME/.local/bin})
   export PATH
   alias hermes-agent="$HOME/.local/bin/hermes"
   alias hermes-workflow="/usr/local/bin/hermes"
   ```
4. Verify in a clean Mark shell, not the profile-home shell:
   ```bash
   env HOME=/Users/markrubin zsh -ic 'echo FIRST_PATH=${path[1]}; whence -a hermes; type hermes; hermes --version 2>&1 | head -6; alias hermes-workflow; hermes-workflow version 2>&1 | head -4'
   ```

Do not delete `/usr/local/bin/hermes` just to fix command resolution. Preserve it under an explicit alias like `hermes-workflow` unless the user explicitly asks to remove that separate workflow CLI.

## Skills Configuration (`hermes skills`)

Skills are reusable instruction sets that extend what Hermes can do.

### Managing skills:

```bash
hermes skills list              # Show installed skills
hermes skills search "docker"   # Search the hub
hermes skills install NAME      # Install from hub
hermes skills config            # Enable/disable per platform
```

### Per-platform skill control:

`hermes skills config` opens an interactive UI where you can enable or disable specific skills for each platform (cli, telegram, discord, etc.). Disabled skills won't appear in the agent's available skills list for that platform.

### Loading skills in a session:

- CLI: `hermes -s skill-name` or `hermes -s skill1,skill2`
- Chat: `/skill skill-name`
- Gateway: type `/skill skill-name` in any chat

## Voice Messages (STT)

Voice messages from Telegram/Discord/WhatsApp/Slack/Signal are auto-transcribed when an STT provider is available.

### Provider priority (auto-detected):
1. **Local faster-whisper** — free, no API key, runs on CPU/GPU
2. **Groq Whisper** — free tier, needs GROQ_API_KEY
3. **OpenAI Whisper** — paid, needs VOICE_TOOLS_OPENAI_KEY

### Setup local STT (recommended):

```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
pip install faster-whisper
```

Add to config.yaml under the `stt:` section:
```yaml
stt:
  enabled: true
  provider: local
  local:
    model: base  # Options: tiny, base, small, medium, large-v3
```

Model downloads automatically on first use (~150 MB for base).

### Setup Groq STT (free cloud):

1. Get free key from https://console.groq.com
2. Add GROQ_API_KEY to the env file
3. Set provider to groq in config.yaml stt section

### Verify STT:

After config changes, restart the gateway (send /restart in chat, or restart `hermes gateway run`). Then send a voice message.

## Voice Replies (TTS)

Hermes can reply with voice when users send voice messages.

### TTS providers (set API key in env file):

| Provider | Env var | Free? |
|----------|---------|-------|
| ElevenLabs | ELEVENLABS_API_KEY | Free tier |
| OpenAI | VOICE_TOOLS_OPENAI_KEY | Paid |
| Kokoro (local) | None needed | Free |
| Fish Audio | FISH_AUDIO_API_KEY | Free tier |

### Voice commands (in any chat):
- `/voice on` — voice reply to voice messages only
- `/voice tts` — voice reply to all messages
- `/voice off` — text only (default)

## Enabling/Disabling Tools (`hermes tools`)

### Interactive tool config:

```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
python -m hermes_cli.main tools
```

This opens a curses UI to enable/disable toolsets per platform (cli, telegram, discord, slack, etc.).

### After changing tools:

Use `/reset` in the chat to start a fresh session with the new toolset. Tool changes do NOT take effect mid-conversation (this preserves prompt caching and avoids cost spikes).

### Common toolsets:

| Toolset | What it provides |
|---------|-----------------|
| terminal | Shell command execution |
| file | File read/write/search/patch |
| web | Web search and extraction |
| browser | Browser automation (needs Browserbase) |
| image_gen | AI image generation |
| mcp | MCP server connections |
| voice | Text-to-speech output |
| cronjob | Scheduled tasks |

## Installing Dependencies

Some tools need extra packages:

```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate

pip install faster-whisper    # Local STT (voice transcription)
pip install browserbase       # Browser automation
pip install mcp               # MCP server connections
```

## Config File Reference

The main config file is `~/.hermes/config.yaml`. Key sections:

```yaml
# Model and provider
model:
  default: anthropic/claude-opus-4.6
  provider: openrouter

# Agent behavior
agent:
  max_turns: 90
  reasoning_effort: high    # xhigh, high, medium, low, minimal, none

# Voice
stt:
  enabled: true
  provider: local           # local, groq, openai
tts:
  provider: elevenlabs      # elevenlabs, openai, kokoro, fish

# Display
display:
  skin: default             # default, ares, mono, slate
  tool_progress: full       # full, compact, off
  background_process_notifications: all  # all, result, error, off
```

Edit with `hermes config edit` or `hermes config set KEY VALUE`.

## Gateway Commands (Messaging Platforms)

| Command | What it does |
|---------|-------------|
| /reset or /new | Fresh session (picks up new tool config) |
| /help | Show all commands |
| /model [name] | Show or change model |
| /compact | Compress conversation to save context |
| /voice [mode] | Configure voice replies |
| /reasoning [effort] | Set reasoning level |
| /sethome | Set home channel for cron/notifications |
| /restart | Restart the gateway (picks up config changes) |
| /status | Show session info |
| /retry | Retry last message |
| /undo | Remove last exchange |
| /personality [name] | Set agent personality |
| /skill [name] | Load a skill |

## Troubleshooting

### Voice messages not working
1. Check stt.enabled is true in config.yaml
2. Check a provider is available (faster-whisper installed, or API key set)
3. Restart gateway after config changes (/restart)

### Telegram images arrive but Hermes says it cannot see them
This is a prompt/context issue, not necessarily a Telegram ingestion failure.

What to verify first:
1. Check `~/.hermes/logs/gateway.log` for lines like:
   - `Cached user photo at ...`
   - `Flushing photo batch ... with 1 image(s)`
2. If those lines exist, Hermes did receive the image.
3. Check the session transcript under `~/.hermes/sessions/` for the user turn. Hermes should be injecting text like:
   - `[The user sent an image~ Here's what I can see: ...]`
   - `vision_analyze with image_url: ...`

If the bot still replies with stuff like:
- `I can't see the image directly`
- `send a URL`
- `share it as a file or link`

then patch the prompt text in these files to force the model to use the provided description:
- `~/.hermes/hermes-agent/gateway/run.py`
- `~/.hermes/hermes-agent/cli.py`
- `~/.hermes/hermes-agent/run_agent.py`

Use wording like:
- `You already have a usable description of the image above.`
- `Do not say you cannot see the image or ask for a URL first.`
- `If the user asks whether you can see the image, answer yes and summarize what you see.`
- `Answer from this description, and if you need more detail, call vision_analyze ...`

After patching:
1. Run `python3 -m py_compile` on the edited Hermes files
2. Restart the gateway with `hermes gateway restart`
3. Re-test by sending a Telegram screenshot with a direct debugging question

Blunt rule: if the log says the photo was cached and flushed, Telegram is not the problem. The reply behavior is.

### Tool not available
1. Run `hermes tools` to check if the toolset is enabled for your platform
2. Some tools need env vars — check the env file
3. Use /reset after enabling tools

### Model/provider issues
1. Run `hermes doctor` to check configuration
2. Run `hermes login` to re-authenticate
3. Check the env file has the right API key

### Changes not taking effect
- Gateway: /reset for tool changes, /restart for config changes
- CLI: start a new session

### Skills not showing up
1. Check `hermes skills list` shows the skill
2. Check `hermes skills config` has it enabled for your platform
3. Load explicitly with `/skill name` or `hermes -s name`
