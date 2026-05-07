---
name: hivemind-stale-scrape-debugging
description: Diagnose HiveMind when a scrape finishes but the app still shows stale dashboard data because remote pull is overwriting local files.
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [hivemind, scraper, stale-data, launchd, replit, sync]
---

# Hivemind stale scrape debugging

Use this when Mark says some version of:
- "the scraper completed but the data is old"
- "I just scraped and the dashboard still shows a few days ago"
- local files look freshly modified but payload timestamps are stale

## The actual failure pattern

A local scrape can succeed, then get silently overwritten by the remote pull agent.

Typical signals:
- file `mtime` is current
- but JSON payload fields like `scrapedAt` or `dataDate` are days old
- `dashboard-data-*.json` and `gantt-scraped-*.json` both show stale payload timestamps
- `data/settings.local.json` has `"syncMode": "remote"`
- launchd service `com.hivemind.remote-pull` is active
- `tools/pull-data-from-replit.py` is running and re-pulling stale Replit files onto local disk

## Investigation steps

1. Check local override first

Read:
- `data/settings.local.json`
- `data/settings.json`

If local override says `remote`, assume local scrape output may be getting clobbered.

2. Compare file mtime vs payload freshness

For several files like:
- `data/dashboard-data-baltimore.json`
- `data/gantt-scraped-baltimore.json`

Inspect:
- filesystem mtime
- top-level `scrapedAt`
- `meta.scrapedAt`
- `dataDate`
- `meta.generatedAt`

If mtime is now-ish but payload timestamps are old, the file was rewritten with stale content.

3. Check for active remote pull agents

Run:
- `launchctl list | egrep 'com.hivemind.remote-pull|hivemind'`
- `ps aux | egrep '[p]ull-data-from-replit|com.hivemind.remote-pull'`

Also inspect:
- `logs/remote-pull.launchd.log`
- `tools/hourly-gantt-sync.sh`

Key behavior in `tools/hourly-gantt-sync.sh`:
- if sync mode is `remote`, it runs `python3 tools/pull-data-from-replit.py`
- that overwrites local dashboard/gantt files with remote copies

4. Confirm remote overwrite instead of scrape failure

Look for this mismatch:
- `data/scrape-history.json` shows fresh run timestamps
- local dashboard/gantt JSON payloads still contain old `scrapedAt`

That means the scrape may have finished, but the remote pull won the race afterward.

## Fix

1. Stop the remote pull LaunchAgent

Example:
- `launchctl bootout gui/501/com.hivemind.remote-pull`

2. Switch local override back to local-push mode

Set `data/settings.local.json` to:

```json
{
  "syncMode": "local_push_remote"
}
```

3. Verify it is actually stopped

- `launchctl list | egrep 'com.hivemind.remote-pull|hivemind'`
- ensure `com.hivemind.remote-pull` no longer appears
- ensure no `pull-data-from-replit.py` process remains

4. Rerun the scraper

After the overwrite path is disabled, rerun the scraper so local files become truly fresh again.

Preferred command for one location:
- `python3 tools/scrape-all.py --location baltimore`

Then rebuild dashboard payload explicitly if needed:
- `python3 tools/multi-location-import.py --location baltimore`

## Important caveat

Fixing remote overwrite does **not** fix scraper integrity contamination.

There is also a separate local-tooling failure mode on newer Python builds:
- `tools/scrape-all.py` can fail on Python 3.13 with `SyntaxError: f-string expression part cannot include a backslash`
- the offending pattern is inline expressions like `js.replace('"', '\\"')` inside f-strings used for AppleScript wrappers
- fix by precomputing the escaped string first, e.g. `escaped_js = js.replace('"', '\\"')`, then interpolate `{escaped_js}` inside the f-string

If the scrape succeeds but immediate dashboard rebuild fails, check missing import dependencies too:
- `pandas` was previously required by `tools/multi-location-import.py` before the Excel path was removed
- HiveMind now rebuilds dashboard data from Gantt-only data; do not chase `openpyxl`/Excel issues in the active scrape path
- if rebuild fails, focus on the actual active dependency chain and current import script errors instead of dead Excel code

If files are still wrong after disabling remote pull, investigate Safari/Field Service territory contamination separately. In this repo, contaminated scrapes have previously produced foreign-location payloads like Las Vegas data inside Baltimore files.

Critical lesson from later incidents: there are TWO integrity layers and they can drift.
- `tools/scrape-all.py` has scrape-time validation rules
- `tools/multi-location-import.py` has rebuild/import integrity rules

If Somerset, Jersey Shore, or another location suddenly throws false integrity warnings after a good scrape, check both files for stale pattern maps. Do not fix only one side.

Also check for duplicated hardcoded validation tables. `tools/scrape-all.py` previously had:
- `SCRAPE_LOCATION_INTEGRITY_RULES`
- plus a separate `EXPECTED_PATTERNS` dict inside `validate_scraped_data()`

That duplication is a bug magnet. Prefer making `validate_scraped_data()` derive from the shared integrity rule map so one update fixes both paths.

Field notes from live franchise changes:
- Somerset now matches current signals like `FPUS156`, `Middlesex`, `Mercer`, `1 North`, `2 East`, `3 West`, `4 Central`
- Jersey Shore now matches current signals like `FPUS394`, directional territories, and gemstone crews (`Bronze`, `Diamond`, `Ruby`, `Emerald`, `Aquamarine`)
- Old signatures like `FPUS020` or `FPUS030` can produce bogus warnings even when the scrape is correct

If the fresh Gantt file looks right but the dashboard-data file looks foreign, rebuild the dashboard payload after fixing integrity rules:
- `python3 tools/multi-location-import.py --location somerset`
- `python3 tools/multi-location-import.py --location jerseyshore`

So the order is:
1. stop remote overwrite
2. rerun scrape
3. if data is still wrong, debug scraper integrity next
4. if warnings persist, update BOTH integrity-rule layers and rebuild dashboard-data

## Verification checklist

After rerunning scrape, verify:
- `mtime` is current
- `scrapedAt` is current
- `dataDate` matches expected current day
- sample jobs/territory in local files belong to the requested location
- dashboard UI reflects the same current payload

## Blunt rule

If Mark says the scrape finished but the app still shows old data, check `settings.local.json` and launchd before touching the scraper. Otherwise you'll waste time fixing the wrong damn thing.
