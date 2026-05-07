---
name: moego-ai-co-pilot-development
category: ai
description: Develop, debug, and operate the MoeGo AI Shotgun Copilot — a bookmarklet-based observer that captures MoeGo chat context and drafts replies via AI.
---

## Skill: MoeGo AI Copilot (Shotgun Observer)

### Architecture

The copilot has three components:

1. **Harness UI** — `moego-harness.html`, served at `/moego` by the HiveMind server. Dark-themed single-page app with buttons: Refresh Captured Context, Analyze + Draft Reply, Summarize Thread, Copy Suggested Reply.
2. **Bookmarklet** — JavaScript injected into MoeGo pages via a draggable bookmarklet link. Scrapes DOM for chat messages, posts captured context to `/api/moego/context` (POST).
3. **Server endpoints** (in `server.py`):
   - `GET /api/moego/context` — returns the last captured context
   - `POST /api/moego/context` — stores context from the bookmarklet
   - `POST /api/moego/analyze` — calls AI to analyze the thread and draft replies
   - `GET /api/moego/bookmarklet` — returns the bookmarklet JS source

### Key Files
- `/Users/markrubin/hivemind-operator/moego-harness.html` — the UI (buttons, JS logic, bookmarklet display)
- `/Users/markrubin/hivemind-operator/server.py` — all API endpoints, AI helper function `_call_ai_helper`

### Debugging Checklist

#### "Analysis failed" (most common)
The `/api/moego/analyze` endpoint calls `_call_ai_helper()` which tries AI backends in priority order:

1. **Direct OpenAI** — needs `OPENAI_API_KEY` env var. Uses `gpt-5.4` model via `openai` Python package.
2. **Local OpenClaw gateway** — needs `OPENCLAW_TOKEN` env var + gateway running locally. Hits `GATEWAY_BASE/v1/chat/completions`.
3. **External OpenClaw gateway** — needs `OPENCLAW_TOKEN` + `OPENCLAW_GATEWAY_URL` pointing to non-localhost.
4. **Last resort gateway** — same token, same base, different error handling.

If ALL fail, returns: `"All AI methods failed: OPENCLAW_TOKEN is not configured."`

**Fix:** Ensure the server process has at least one of these env vars set when launched. Check with:
```bash
curl -s -X POST http://127.0.0.1:PORT/api/moego/analyze \
  -H 'Content-Type: application/json' \
  -d '{"mode":"draft_reply","clientId":"","instruction":"test"}'
```

#### "No data" / garbage context
The bookmarklet scrapes ALL text from whatever page it's run on. If fired on the calendar (`/calendar/grooming`) instead of a message thread, you get appointment data, pet breeds, and UI labels instead of messages.

**Fix:** The bookmarklet must be clicked on a MoeGo **message/conversation thread page**, not the calendar or dashboard.

DOM selectors used: `[data-message-id]`, `[class*="message"]`, `[class*="bubble"]`, `[class*="chat-item"]`, `[role="listitem"]`, etc. Fallback scrapes leaf text nodes from `SPAN/DIV/P/LI` elements.

#### Server Port
The correct port for the HiveMind dashboard is **5050** (set via `PORT=5050` env var). `server.py` defaults to 5000 but `server-unified.py` and all internal API references use 5050. Always start with `PORT=5050 python3 server.py`. macOS AirPlay Receiver often grabs port 5000, which causes silent conflicts.

#### Endpoint detection
The harness auto-detects the server by probing ports 5050-5060, 3000-3002, plus `location.origin` and any `?endpoint=` query param or localStorage value. If the server runs on a non-standard port (e.g., 8008), either:
- Set the endpoint manually in the UI input field
- Pass `?endpoint=http://127.0.0.1:8008` in the URL
- It should auto-detect if the server responds to `GET /api/moego/context`

#### Refresh auto-triggers analyze
`refreshContext()` automatically calls `analyze('draft_reply', { silent: true })` after loading context (line ~233). So if analyze fails, refreshing context will silently fail the analysis too — check console for 500 errors.

### Pitfalls
- The `.env` file may not have `OPENCLAW_TOKEN` — the server prints a warning at startup: "WARNING: OPENCLAW_TOKEN not set"
- `server.py` is ~15K lines. The `_call_ai_helper` function starts around line 860. The analyze route is elsewhere — search for `'/api/moego/analyze'`.
- The bookmarklet URL is dynamically generated using the current endpoint value. If endpoint changes, re-drag or re-copy the bookmarklet.
- Client ID can be set in the UI or via `sessionStorage('moego-client-hint')`. The bookmarklet also tries to extract it from the MoeGo URL's `clientId` query param.
- Hard Reset clears localStorage, sessionStorage, posts a reset payload to the server, then re-detects and refreshes.

### Queen Bee Menu Integration (completed)

MoeGo Copilot is accessible from the Queen Bee admin dropdown in the HiveMind dashboard. It's embedded as an iframe tab:

- **Desktop**: Queen Bee ▾ → 🐾 MoeGo Copilot (between Tasks and World)
- **Mobile**: slide-out menu item `#mobileMoegoLink`
- **Tab content**: `<div id="moego-tab">` with an iframe loading `/moego`

To add more tools to Queen Bee, follow this pattern:
1. Add a `<button>` inside `#queenBeePanel` in index.html (~line 123 area)
2. Add a `<a class="mobile-menu-item">` in `#mobileMenu` (~line 97 area)
3. Create a `<div id="NEWTAB-tab" class="tab-content">` for the view
4. The `switchTab()` JS function handles showing/hiding tabs automatically
5. Admin-only items need a guard in `switchTab()` and visibility toggle on login

#### Iframe Embedding X-Frame-Options Pitfall
The UI overhaul branch (`claude/admiring-pascal`) added security headers: `X-Frame-Options: DENY` and `frame-ancestors 'none'` on all responses. This **blocks iframe embedding** of any internal page.

Fix: Add the path to `EMBEDDABLE_SAME_ORIGIN_PATHS` in server.py (~line 423). This set controls which paths get `SAMEORIGIN` / `frame-ancestors 'self'` instead of `DENY`. Currently includes: `/workflow-board.html`, `/workflow-sim.html`, `/moego`.

If you add a new iframe-embedded tool tab and it shows "localhost refused to connect" inside the dashboard, this is the first thing to check.

### Phase 1 Design Philosophy
Human-in-the-loop only. The copilot reads and suggests — it never clicks or types in MoeGo autonomously. The user copies the draft and pastes it manually.
