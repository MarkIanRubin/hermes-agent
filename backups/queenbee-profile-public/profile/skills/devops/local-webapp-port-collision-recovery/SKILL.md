---
name: local-webapp-port-collision-recovery
description: Recover local web apps when the wrong project is listening on the expected port; verify process cwd, restart from the right repo, and test via the user-facing host/IP.
version: 1.0.0
metadata:
  hermes:
    tags: [devops, ports, local-server, webapp, troubleshooting]
    related_skills: [systematic-debugging, dogfood]
---

# Local Webapp Port Collision Recovery

## When to Use

Use when a local website/app loads the wrong project, a user says a port is mixed up, or two nearby projects share similar server commands/ports and the expected URL is serving stale or unrelated content.

Common triggers:
- “You are mixing up the ports.”
- “This port is for [project/site].”
- A browser page title/content does not match the intended app.
- Multiple `server.py`, Flask, Vite, Next, or static servers are running.
- The app must be reachable at a specific LAN/Tailscale/private IP, not only `localhost`.

## Workflow

1. **Identify the intended project and port**
   - Use repo memory/context when available.
   - Confirm the target URL shape, e.g. `http://100.x.x.x:8765/` or `http://127.0.0.1:8765/`.

2. **Check what is actually listening**

   ```bash
   lsof -nP -iTCP:<PORT> -sTCP:LISTEN || true
   ps -p <PID> -o pid,ppid,user,command
   lsof -p <PID> | grep cwd || true
   ```

   The process command alone is not enough. `python server.py` from two repos looks identical; the `cwd` tells you which app owns the port.

3. **Check adjacent known ports before killing anything**

   If the project ecosystem has known ports, inspect them too:

   ```bash
   lsof -nP -iTCP:5050 -sTCP:LISTEN || true
   lsof -nP -iTCP:8765 -sTCP:LISTEN || true
   ```

4. **Stop only the wrong owner**

   Kill the process whose `cwd` does not match the intended repo:

   ```bash
   kill <WRONG_PID>
   sleep 1
   lsof -nP -iTCP:<PORT> -sTCP:LISTEN || true
   ```

5. **Restart from the correct working directory**

   Use the terminal background process mode when available instead of shell `nohup`/`&` wrappers:

   ```bash
   cd /path/to/intended/repo
   python3 server.py
   ```

   If a parent process spawns a child, re-check the child PID and cwd after startup.

6. **Verify the binding and owner**

   ```bash
   lsof -nP -iTCP:<PORT> -sTCP:LISTEN
   for p in $(lsof -tiTCP:<PORT> -sTCP:LISTEN); do
     echo PID:$p
     ps -p $p -o pid,ppid,user,command
     lsof -p $p | grep cwd || true
   done
   ```

7. **Verify via the actual user-facing URL**

   Prefer browser verification for UI apps:

   ```text
   browser_navigate(url="http://<USER_FACING_IP>:<PORT>/")
   ```

   Confirm title, visible headings, and app-specific content. Localhost verification is not enough when the user supplied a specific LAN/Tailscale/private IP.

## Pitfalls

- `curl` may hang on large pages or private-network paths; use `curl -I --connect-timeout 2 --max-time 10` for lightweight checks, then verify in browser.
- Two Python processes both shown as `server.py` can belong to different repos. Always inspect `cwd`.
- A foreground command containing `nohup`, `&`, `disown`, or `setsid` may be blocked by Hermes; use the terminal tool’s `background=true` process tracking.
- Do not kill all servers matching `server.py`; kill only the PID bound to the wrong port/project.

## Verification Checklist

- [ ] Target port has exactly the expected listener.
- [ ] Listener cwd matches the intended repo.
- [ ] Neighboring known ports still serve their intended apps.
- [ ] User-facing host/IP loads the expected page title/content in a browser.
- [ ] Final response names the corrected port mapping plainly.
