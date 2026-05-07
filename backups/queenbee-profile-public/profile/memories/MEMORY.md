*Curated learnings and context. Operational details in TOOLS.md. Personal details in USER.md.*
§
---
§
Core Lessons: **Fix the System, Not the Symptom** — Think holistically. Find root cause. Ask "what else?"
§
Core Lessons: **Never say "fixed"** — Say "I've pushed a change, please check"
§
Core Lessons: **When the same approach fails twice, change the approach entirely**
§
Core Lessons: **One function, one writer** — No duplicate mutation paths
§
Core Lessons: **VERIFY BEST EVIDENCE** — UI: real page/browser when possible. Deploys: real worktree/assets/Git status, not hardcoded version labels.
§
Core Lessons: **Use Mark's actual state when debugging** — Same login, same mode, same lifecycle; my browser state is not his state.
§
Core Lessons: **Alert on failure immediately** — Don't wait for Mark to find it
§
Core Lessons: **Dead code breeds bugs** — Remove it
§
Core Lessons: **Never ask Mark to debug** — I have the tools. Use them.
§
Business Context: 1-800-GOT-JUNK: **AJS** $525 · **Truck cost** $50/hr · **Cancellation rates** Day 0: 10% → Day 8+: 39%
§
Ops Note: HiveMind no longer uses the Excel schedule component in the scrape/import pipeline; dashboard rebuilds should rely on Gantt-only data.
§
Port ownership: BusinessVisualization owns local port 8765; HiveMind stays off 8765. QueenBee BV server runs via LaunchAgent `com.businessvisualization.localserver`; logs: `$HOME/Library/Logs/businessvisualization-localserver*.log`.
§
Mark machines: /usr/local/bin/hermes is HERMES workflow CLI; Hermes Agent is ~/.local/bin/hermes or python -m hermes_cli.main in ~/.hermes/hermes-agent venv. UpDogs MacBook Air account `updogmobilegrooming` may need `~/.local/bin` in `.zshenv` for Hermes PATH. Node v24.15.0/npm 11.12.1 in ~/.local/bin on QueenBee+lifeislucky; lifeislucky .zshenv exposes PATH.
§
BV Money Model: hosted SVG. Mark means visible rendered alignment under visible headers (bbox/vision), not abstract SVG math. Keep “Zoom”; anchored playback; Expenses fit; scale to Revenue; one Marketing/ROAS; first gear Awareness.
§
Lifeislucky git HTTPS auth uses credential-store; no `gh`. Clear GitHub-specific gh helpers, add empty helper then store.
