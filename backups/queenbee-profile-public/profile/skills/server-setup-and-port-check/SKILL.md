---
name: Server Setup and Port Check
version: 1.0
description: A skill to guide users on setting up a server while ensuring there are no port conflicts.
---

# Overview
This skill outlines the process for setting up a local server and the importance of checking for port conflicts before launching.

## Steps
1. **Pick a free port deliberately**:
   - If the user requested a specific port, check it with `lsof -i :<port>`.
   - If the request comes from a screenshot of a browser `ERR_CONNECTION_REFUSED`, extract the URL/port from the screenshot before choosing a new port. Vision tools may fail; use OCR as fallback:
     ```bash
     tesseract /path/to/screenshot.jpg stdout 2>/dev/null | grep -Eo '127\.0\.0\.1[^ ]*|localhost[^ ]*|:[0-9]{4,5}|http[^ ]+'
     # If OCR is noisy, try alternate page segmentation modes:
     for psm in 3 4 6 11 12; do tesseract /path/to/screenshot.jpg stdout --psm $psm 2>/dev/null | grep -Eo ':[0-9]{4,5}'; done
     ```
     Start the server on the port already shown in the browser when possible, so the user can simply refresh the failed tab.
   - If any free port is acceptable, ask the OS for one instead of guessing:
     ```bash
     python3 - <<'PY'
     import socket
     s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()
     PY
     ```
2. **Select Alternative Port**: If the chosen port is in use, select an alternative port from the OS-provided result rather than cycling common ports blindly.
3. **Update Server Configuration**: Modify the server code/env to run on the selected port when the app requires configuration. For static sites, no code change is needed.
4. **Run or Restart the Server**:
   - For restarts, first identify the active listener and command line before killing anything:
     ```bash
     lsof -nP -iTCP:<port> -sTCP:LISTEN || true
     ps aux | grep -E '[s]erver|[f]lask|[g]unicorn|[u]vicorn|[n]ode|[v]ite' || true
     ```
   - If a similarly named process is running on a different port, verify its working directory before assuming it is the target app. On macOS/Linux:
     ```bash
     ps -p <pid> -o pid,ppid,etime,command
     lsof -Pan -p <pid> -i || true
     lsof -Pan -p <pid> | grep cwd || true
     ```
     A `server.py` from another repo on another port is not evidence that the requested preview server is healthy; start the correct repo/port and then verify routes.
   - Inspect existing start scripts before using them; they may point at a stale virtualenv or old path. If a script fails because `.venv`/`venv` differs, use the environment that the existing process or project actually uses and note the mismatch.
   - Static site quick path:
     ```bash
     python3 -m http.server <port> --bind 127.0.0.1
     ```
   - Use the background/process tool when available so the server keeps running while you verify it. Do not put `nohup`, `disown`, `setsid`, or shell-level `&` inside a foreground terminal command if the tool supports `background=true`; start it as a tracked background process instead.
   - After killing an old listener, re-check the port before starting. A supervisor/launch agent may immediately respawn the server under a new PID; if the new listener is healthy, treat the restart as successful rather than starting a duplicate.
   - If a delayed/background-tool watch alert says an old server matched `Serving HTTP`, do not assume a new duplicate exists. Verify the actual listener with `lsof -nP -iTCP:<port> -sTCP:LISTEN` and, if available, the tool's process list. The port listener is the source of truth; report stale/noisy alerts separately.
   - If the server is supporting the user's browser preview, leave it running after verification. Do not kill it just because QA is done unless it was explicitly a disposable test server or you are replacing it with a persistent service. If you must stop it, tell the user the exact URL will go down and provide the restart command.
5. **Verify the Server**:
   - Poll the background process or check the command output.
   - Probe the expected routes/assets before browser QA so missing static files are caught immediately:
     ```bash
     python3 - <<'PY'
     import urllib.request
     port = '<port>'
     for path in ['/', '/styles.css', '/app.js']:
         url = f'http://127.0.0.1:{port}{path}'
         with urllib.request.urlopen(url, timeout=5) as r:
             print(path, r.status, r.headers.get('content-type'), len(r.read()))
     PY
     ```
     Adjust the asset list for the actual app (`/build.html`, `/main.js`, `/assets/...`, etc.).
   - Open `http://127.0.0.1:<port>/` in the browser when browser tools are available.
   - Check the browser console after navigation and after key interactions.
   - For visual/static-site work, verify key layout counts and clipping with DOM geometry (`getBoundingClientRect`) if screenshot vision is unavailable.
   - Report the exact local URL.

## Importance
- Prevents errors related to port conflicts.
- Ensures seamless server operation without interruptions.
