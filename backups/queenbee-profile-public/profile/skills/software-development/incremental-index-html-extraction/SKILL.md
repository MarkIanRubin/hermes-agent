---
name: incremental-index-html-extraction
description: Safely extract large feature islands out of a monolithic index.html into standalone JS files in a Flask app, including the static-serving and regression checks that are easy to miss.
---

When to use
- A giant `index.html` has multiple inline `<script>` blocks and needs to be modularized without rewriting the whole frontend.
- The app is Flask-backed and does not automatically serve arbitrary JS files from the repo root.
- You need to reduce risk while extracting hot UI areas like maps, Nearby, exports, route optimization, or route-state logic.

Core lesson
- Do not just cut JS out of `index.html` and assume it will load.
- In this HiveMind-style setup, every extracted file needs an explicit Flask route (or another confirmed static-serving path), or the browser will get a 404 and the feature will die.

Recommended approach
1. Extract by feature island, not by arbitrary line range.
   - Good slices:
     - Nearby / Recently Booked
     - Route Optimization
     - Route-state / URL sync helpers
     - Gantt rendering helpers
   - Bad slices:
     - random 500-line chunks
     - mixed-domain code with shared initialization everywhere

2. Choose the smallest coherent next cut.
   - Start with a hot but self-contained block.
   - Avoid cutting shared globals and render loops until smaller islands are already separated.

3. Copy the exact inline block into a new file.
   - Preserve function names and global assignments like `window.toggleRecentlyBooked = ...`
   - Preserve surrounding indentation only if harmless; JS can live fine as-is in the new file.
   - Replace the old inline block with a `<script defer src="...">` tag.

4. Add an explicit Flask route for the new JS file.
   - Pattern in `server.py`:

```python
@app.route('/feature-name.js')
def serve_feature_name_js():
    return send_file(STATIC_DIR / 'feature-name.js', mimetype='application/javascript')
```

   - Do this immediately after extraction, not later.
   - Reuse the style of existing routes like `/config.js` and `/store.js`.

5. Restart the actual server instance you are testing.
   - A route can exist in source and still 404 if the running server is stale.
   - Verify which PID is listening on the port before trusting results.
   - If a restart seems to succeed but the old behavior remains, check the listener and kill the actual process bound to the port:

```bash
lsof -iTCP:5050 -sTCP:LISTEN -n -P
kill <pid>
PORT=5050 python3 server.py > /tmp/hm5050.log 2>&1 &
```

6. Verify the extracted asset directly.
   - Check in browser or via HTTP:

```bash
python3 - <<'PY'
import urllib.request
with urllib.request.urlopen('http://127.0.0.1:5050/feature-name.js', timeout=10) as r:
    print(r.status, r.headers.get_content_type(), r.read(40))
PY
```

   - Expected: `200 application/javascript`
   - If you get `404`, the feature is still broken regardless of how clean the code looks.

7. Re-verify the feature behavior, not just the file load.
   - For Nearby extraction, confirm Nearby opens and functions exist.
   - For Route Optimization extraction, confirm optimization controls still run.
   - For Route-state extraction, confirm tab URLs and popstate behavior still work.

8. Keep backend compile checks running after each frontend extraction.
   - They will not catch browser regressions, but they do catch accidental Python route mistakes.

```bash
python3 -m py_compile server.py app_factory.py routes/auth.py routes/location_config.py routes/optimizer.py routes/dashboard.py routes/__init__.py db.py
```

Verification checklist
- `index.html` references the new script tag.
- The moved globals/functions are no longer inline in `index.html`.
- The new JS file exists and contains the moved functions.
- Flask serves the file with HTTP 200.
- The live server on the target port has been restarted after the route addition.
- The UI feature still works.

Known pitfalls
- Forgetting to add a Flask route for the new JS file.
- Restarting the wrong server or not restarting at all, then chasing fake 404s.
- Extracting code that depends on symbols declared later in the page without checking load order.
- Mixing route-state helpers with feature logic; keep them separate.
- Assuming successful Python compile means the frontend extraction worked.

Good extraction order for this codebase style
1. Nearby / Recently Booked
2. Route Optimization
3. Route-state / URL sync
4. Location/dashboard view orchestration (`changeMainLocation`, `updateDashboardForMainLocation`, historical mode helpers)
5. Gantt/dashboard core (`renderGantt`, timeline playback, `loadDataForDate`, `init`, hero syncing)
6. Revenue Velocity / dashboard analytics (`updateVelocityCard`, stats bars, progress ticks, mobile stats)
7. Tab-specific heavy domains after that

What was learned here
- Nearby broke immediately after extraction because the JS file was not served by Flask.
- Route Optimization, Route-state, Location/dashboard view, Gantt/dashboard core, and Revenue Velocity all had the exact same failure mode until explicit routes were added.
- A fake restart can waste time; verify the actual listener PID with `lsof` and kill the real process if the old server is still bound to the port.
- The safest path is repeated small extractions plus direct HTTP verification of each new asset.
