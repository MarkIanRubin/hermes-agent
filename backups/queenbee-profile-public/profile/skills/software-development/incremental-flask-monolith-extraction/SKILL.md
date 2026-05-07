---
name: incremental-flask-monolith-extraction
description: Safely carve route families out of a giant Flask app by introducing an app factory seam and callback-driven blueprints before moving business logic.
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [flask, refactor, monolith, blueprints, backend]
---

# Incremental Flask Monolith Extraction

Use when a Flask repo has a giant `server.py`/`app.py` and you need to modularize it without a rewrite.

## When this applies
- One giant Flask file owns app creation plus dozens/hundreds of routes
- Some `routes/` modules may exist already, but they still import back into the monolith
- The repo is too risky for a big-bang rewrite

## Core approach
1. Add a thin `app_factory.py` with `create_app()` first.
2. Change the monolith from `app = Flask(__name__)` to `app = create_app(__name__)`.
3. Extract one coherent route family at a time.
4. Make extracted route modules callback-driven instead of importing the monolith.
5. Verify after every slice with `py_compile` before moving the next family.

## Why this works
The real problem in Flask monoliths is not just route count. It is hidden coupling through globals. Callback injection lets the new blueprint depend on explicit capabilities (`save_json_file`, `ensure_auth`, `get_global_settings`) instead of `from server import ...` nonsense.

## Recommended extraction order
Start with the lowest-risk coherent family.

Good first cuts:
- location/config routes
- settings routes
- simple read/write JSON-backed endpoints

Defer until later:
- login/auth with rate limiting and cookies
- admin-only routes with lots of helper dependencies
- operations/restart/subprocess endpoints

## Blueprint pattern
Create a module like `routes/location_config.py` or `routes/auth.py`:

```python
from flask import Blueprint, jsonify, request

my_bp = Blueprint('my_bp', __name__, url_prefix='/api')

_CTX = {
    'save_json_file': None,
    'ensure_auth': [REDACTED]
}


def init_my_routes(**kwargs):
    _CTX.update(kwargs)
```

Route handlers use `_CTX` callbacks instead of importing the monolith.

Example:

```python
@my_bp.route('/settings', methods=['POST'])
def update_settings():
    ensure_auth = [REDACTED]
    if callable(ensure_auth):
        auth_response = [REDACTED]
        if auth_response is not None:
            return auth_response

    save_json_file = _CTX.get('save_json_file')
    if not callable(save_json_file):
        raise RuntimeError('save_json_file callback is not configured')

    data = request.get_json(silent=True) or {}
    save_json_file('settings.json', data)
    return jsonify({'status': 'ok'})
```

## Wiring pattern in the monolith
Only after all referenced helpers exist, initialize and register the blueprint:

```python
from routes.location_config import location_config_bp, init_location_config

init_location_config(
    save_json_file=save_json_file,
    ensure_auth=[REDACTED]
    data_dir=DATA_DIR,
)
app.register_blueprint(location_config_bp)
```

Important: register after the callbacks it needs are defined. Registering too early is the common dumb mistake.

## Safe extraction loop
For each route family:
1. Read the existing route code and its helper dependencies.
2. Add the needed callbacks to `_CTX`.
3. Copy the route into the new module with minimal changes.
4. Wire `init_*()` and `app.register_blueprint(...)` in the monolith.
5. Remove the old route from the monolith.
6. Run:
   - `python3 -m py_compile app_factory.py server.py routes/<module>.py`
7. Search to confirm the old decorator is gone from the monolith.
8. Only then move the next route.

## Verification checklist
- `py_compile` passes on the touched files
- the moved `@app.route(...)` no longer exists in the monolith
- the new `@*_bp.route(...)` exists in the route module
- no route module imports back into `server.py`

## Practical lessons learned
- App factory first. Without that seam, every later extraction is uglier.
- Callback-driven blueprints are the clean middle state between monolith and full service layer.
- Extract the same family repeatedly while the boundary is hot (for example: settings -> privacy -> AJS rules) before switching domains.
- Preserve payload compatibility when moving auth endpoints; support both old and new key names if the frontend may vary.
- Don’t touch the login endpoint too early if it includes rate limiting, cookies, lockout logic, and IP lookup. That slice deserves its own pass.
- If a blueprint needs a helper that is defined later in the monolith, inject it with a lambda or register the blueprint after the helper exists. Otherwise you'll create dumb order-of-definition failures.
- For extracted routes that previously used decorators bound to the monolith app (for example `@limiter.limit(...)`), re-apply the decorator after blueprint registration with `app.view_functions['blueprint_name.endpoint_name'] = limiter.limit(...)(app.view_functions['blueprint_name.endpoint_name'])`. This preserves rate limits without keeping the route in the monolith.
- When the old route used shared mutable state (for example a distance cache dict), inject the exact shared object into the blueprint initializer instead of creating a copy. Otherwise behavior quietly changes and cache hit rates collapse.
- After every move, search both the monolith and the new module for the route path and handler name. Duplicate route registrations can linger even when syntax is clean, and then you're debugging shadows instead of code.
- When deleting old route blocks from the monolith, remove the whole function carefully. A sloppy partial replace can leave a decorator with no `def`, which creates an `IndentationError`. Run `py_compile` immediately after every deletion.
- If you reuse an existing route module stub, audit it hard before trusting it. Old placeholder modules often use stale APIs or import back into the monolith in exactly the way you're trying to eliminate.
- `py_compile` is necessary but not sufficient before a client demo. Do one real startup smoke test too, preferably on an alternate port like `PORT=5099 python3 server.py`, because environment drift (for example missing `flask` even though the code parses) can still torpedo the run.
- If the smoke test dies on missing runtime packages, install from `requirements.txt` immediately and rerun the boot check before touching more code. A clean import/startup is more valuable than squeezing in one more extraction pass right before a demo.
- When you start breaking a giant root-served `index.html` into external JS files in a Flask app that serves the HTML manually with `send_file()`, don't assume the browser can fetch the new asset. Add an explicit Flask route (or proper static-file serving) for the extracted `.js` file and verify it with a real HTTP GET. A silent `404` on the new script will make the extracted feature look "broken" even when the JS itself is fine.

## Good next families after settings
- auth session reads/writes: `/api/logout`, `/api/me`, `/api/verify-token`, `/api/change-password`
- then user/admin auth routes
- then login

## Anti-patterns to avoid
- Don’t rewrite the app into a new framework.
- Don’t move 30 unrelated routes at once.
- Don’t let route modules import monolith globals.
- Don’t mix extraction with random feature changes.

## Output goal
By the time this skill has been applied a few times, the original `server.py` should mostly contain:
- imports
- config/constants
- helper initialization
- `init_*()` wiring
- `app.register_blueprint(...)`
- startup/bootstrap only
