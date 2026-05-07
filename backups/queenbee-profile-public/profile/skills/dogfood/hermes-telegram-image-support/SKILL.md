---
name: hermes-telegram-image-support
description: Fix Hermes when Telegram screenshots are received but the assistant still replies that it cannot see images.
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [hermes, telegram, vision, gateway, debugging]
---

# Hermes Telegram Image Support

Use when Hermes receives Telegram photo messages but answers with generic junk like "I can't see the image directly" instead of using the screenshot for UI debugging.

## Symptoms
- Telegram bot receives photo messages
- Gateway appears alive and polling
- Hermes replies with text such as:
  - "I can't see the image directly"
  - "provide the image URL"
  - "share the image as a file or link"
- User expects OpenClaw-style screenshot debugging

## Root cause pattern
Usually the image ingestion is already working.
The failure is often prompt/context behavior after ingestion, not Telegram transport.

Another common failure is **auxiliary vision routing to a text/Codex provider**. If `vision_analyze` or `browser_vision` returns an error like `gpt-...-codex model is not supported` or a Codex/ChatGPT-account vision rejection, Telegram transport is not the problem: Hermes is trying to run the vision auxiliary task through the main Codex model.

## Class-first fallback when vision tooling fails
Use this pattern when the user sends a screenshot and asks for a UI/file change, but `vision_analyze` or `browser_vision` fails because of a provider/model error.

Do not stop at “vision failed.” The image file path is still usable.

Fallback ladder:
1. Inspect basic image metadata:
   ```bash
   file /path/to/image.jpg
   sips -g pixelWidth -g pixelHeight /path/to/image.jpg 2>/dev/null || true
   ```
2. Try opening the local image in the browser so you can at least preserve a screenshot artifact:
   ```text
   browser_navigate url=file:///absolute/path/to/image.jpg
   ```
3. Run local OCR if text is visible:
   ```bash
   tesseract /path/to/image.jpg stdout --psm 6 2>/dev/null
   ```
4. Search the relevant project for OCR text fragments, then edit the source directly:
   ```bash
   grep -R "visible text fragment" /path/to/project
   ```
5. Verify the change by searching for removed text and, when possible, serving the page locally and checking the DOM/browser snapshot.

This is especially useful for static site edits where the screenshot contains distinctive copy like headings, labels, or nav text.

## First verify ingestion
Check the Hermes gateway log:

```bash
python3 - <<'PY'
from pathlib import Path
p=Path('/Users/markrubin/.hermes/logs/gateway.log')
for line in p.read_text(errors='ignore').splitlines()[-150:]:
    if 'Cached user photo' in line or 'Flushing photo batch' in line or 'Sending response' in line:
        print(line)
PY
```

Good signs:
- `Cached user photo at ...`
- `Flushing photo batch ... with 1 image(s)`
- later `Sending response ...`

If those lines exist, Telegram image intake is working.

## Inspect the bad session directly
Look at the saved session JSON/JSONL and confirm the image description was injected into the user turn.
Search for phrases like:
- `[The user sent an image~ Here's what I can see:`
- `vision_analyze with image_url:`

If that text is present but the assistant still says it cannot see the image, the model is ignoring weak instructions.

## Fix: route auxiliary vision to a real multimodal model
If the error mentions Codex or an unsupported `gpt-...-codex` model, set the profile's auxiliary vision provider/model explicitly instead of relying on `provider=main`:

```bash
/Users/markrubin/.local/bin/hermes --profile queen_bee_obsidian config set auxiliary.vision.provider openrouter
/Users/markrubin/.local/bin/hermes --profile queen_bee_obsidian config set auxiliary.vision.model openai/gpt-4o-mini
/Users/markrubin/.local/bin/hermes --profile queen_bee_obsidian gateway restart
/Users/markrubin/.local/bin/hermes --profile queen_bee_obsidian gateway status
```

Then verify with an actual cached image path:

```text
vision_analyze image_url=/absolute/path/to/cache/images/img_xxx.jpg question="Summarize this image in one sentence."
```

Use the real profile name and Hermes binary for the machine; on Mark's setup, `/usr/local/bin/hermes` may be a different workflow CLI, while `/Users/markrubin/.local/bin/hermes --profile queen_bee_obsidian` targets this gateway.

## Fix: harden the injected image prompt
Patch these files:
- `~/.hermes/hermes-agent/gateway/run.py`
- `~/.hermes/hermes-agent/cli.py`
- `~/.hermes/hermes-agent/run_agent.py`

Update the image-note text so it explicitly says:
- the assistant already has a usable description of the image
- do NOT say it cannot see the image
- do NOT ask for a URL first
- if the user asks whether you can see the image, answer yes and summarize what you see
- if more detail is needed, call `vision_analyze`

## Recommended instruction text
Use language close to this:

```text
[You already have a usable description of the image above. Do not say you cannot see the image or ask for a URL first. If the user asks whether you can see the image, answer yes and summarize what you see. Answer from this description, and if you need more detail, call vision_analyze with image_url: ...]
```

## Restart Hermes after patching
Compile and restart:

```bash
python3 -m py_compile /Users/markrubin/.hermes/hermes-agent/gateway/run.py /Users/markrubin/.hermes/hermes-agent/cli.py /Users/markrubin/.hermes/hermes-agent/run_agent.py
hermes gateway restart
hermes gateway status
```

## Verify runtime health
Confirm the gateway is actually polling after restart:
- `Connected and polling for Telegram updates`
- `getUpdates` calls continue in the log

If the bot stops responding entirely after edits, the usual issue is just that the gateway was down or not restarted cleanly.

## What to tell the user to test
Ask them to send a screenshot and prompt it with something direct:
- `Can you see this image? Answer yes and summarize it.`
- `Use this screenshot to debug the UI. Do not say you can't see it.`

Important: test with a NEW image turn after the restart. Old bad replies in a saved Telegram session can make it look like the patch failed when you're really just reading pre-fix responses.

## Important lesson
If the logs show photo caching and photo-batch flushes, don't waste time blaming Telegram. The bug is in prompt/agent behavior unless the gateway itself is down.

## Extra field note
If the user says the bot suddenly stopped responding after a patch, check whether the Hermes gateway service is actually still running before debugging prompt behavior further. A clean `hermes gateway start`/`restart` can be the whole fix.
