---
name: hivemind-rep-goals-import
description: Import HiveMind REP goal spreadsheets into the SQLite `rep_goals_2026` table, including Google Sheets auth failures and local XLSX fallbacks.
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [hivemind, sqlite, rep-goals, spreadsheets, google-sheets, xlsx]
---

# HiveMind REP Goals Import

## When to use

Use this when Mark asks to import, refresh, verify, or repair REP/Revenue Expense Predictor goals for a HiveMind location/franchise from a Google Sheet, downloaded Excel workbook, planning master workbook, or local XLSX/CSV.

Class of task: turn business-planning spreadsheet goals into durable HiveMind SQLite rows in `data/hivemind.db`, then update/verify the dashboard-facing REP goal JSON.

## Repo and target table

```bash
cd /Users/markrubin/hivemind-operator
DB=data/hivemind.db
```

Target schema:

```bash
sqlite3 data/hivemind.db '.schema rep_goals_2026'
```

Expected table shape:

```sql
rep_goals_2026(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  franchise TEXT NOT NULL,
  rep_goal REAL NOT NULL,
  month INTEGER,
  day INTEGER,
  UNIQUE(franchise, date)
)
```

Known franchise/location mapping lives in `tools/scrape-rep-goals.py` (`FRANCHISE_MAP`). Examples:
- `Baltimore GJ` -> `baltimore`
- `Las Vegas Metro GJ` -> `las_vegas`

## Preflight

1. Follow repo coordination rules if present, but do not let missing `agent-coord` block the import.
2. Check date and current DB state:

```bash
date '+%Y-%m-%d %Z'
sqlite3 -header -column data/hivemind.db "
SELECT franchise, COUNT(*) rows, ROUND(SUM(rep_goal),0) total, MIN(month), MAX(month)
FROM rep_goals_2026
GROUP BY franchise
ORDER BY franchise;
"
```

3. Back up the DB before writing:

```bash
cp -p data/hivemind.db "data/hivemind.db.backup-before-rep-import-$(date '+%Y%m%d-%H%M%S')"
```

## Access order for Google Sheets sources

If Mark gives a Google Sheets URL, extract the sheet ID and gid, then try in order:

1. Hermes Google Workspace auth/API (`google-workspace` skill):

```bash
python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py --check
```

2. Anonymous CSV export URLs:

```bash
python3 - <<'PY'
import urllib.request
sid='SHEET_ID'; gid='GID'
for url in [
 f'https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}',
 f'https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&gid={gid}',
 f'https://docs.google.com/spreadsheets/d/{sid}/pub?gid={gid}&single=true&output=csv',
]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30) as r:
            print(r.status, r.geturl(), r.headers.get('content-type'))
            print(r.read(500).decode('utf-8','replace'))
    except Exception as e:
        print(url, type(e).__name__, e)
PY
```

3. Browser/Safari extraction if the sheet is visible there. Remember: browser login and Hermes OAuth are separate.
4. Local fallback: search `~/Downloads` and repo data/backups for matching workbooks. Planning master workbooks often contain hyperlinks to REP sheets.

## Local XLSX fallback

If `openpyxl` is missing, do **not** stop. `.xlsx` files are ZIPs with XML. Use stdlib parsing.

Useful discovery commands:

```bash
python3 - <<'PY'
from pathlib import Path
import time
for root in [Path('/Users/markrubin/Downloads'), Path('/Users/markrubin/hivemind-operator/data')]:
    print('\nROOT', root)
    if root.exists():
        files=[]
        for p in root.rglob('*') if root.name != 'data' else root.glob('*'):
            if p.is_file() and p.suffix.lower() in {'.csv','.xlsx','.xls','.ods'}:
                files.append((p.stat().st_mtime, p.stat().st_size, str(p)))
        for mt,size,path in sorted(files, reverse=True)[:40]:
            print(time.strftime('%Y-%m-%d %H:%M', time.localtime(mt)), size, path)
PY
```

Find whether a workbook references the target Google Sheet:

```bash
python3 - <<'PY'
from zipfile import ZipFile
from pathlib import Path
needle='SHEET_ID_OR_UNIQUE_TEXT'.encode()
for p in Path('/Users/markrubin/Downloads').glob('*.xlsx'):
    try:
        z=ZipFile(p)
        for n in z.namelist():
            if (n.endswith('.xml') or n.endswith('.rels')) and needle in z.read(n):
                print('FOUND', p, n)
                raise SystemExit
    except Exception:
        pass
print('not found')
PY
```

List workbook sheet names and relationship targets:

```bash
python3 - <<'PY'
from zipfile import ZipFile
import xml.etree.ElementTree as ET
p='/path/to/workbook.xlsx'
z=ZipFile(p)
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
wb=ET.fromstring(z.read('xl/workbook.xml'))
rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
relmap={r.attrib['Id']:r.attrib['Target'] for r in rels}
for s in wb.find('m:sheets',ns):
    rid=s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
    print(s.attrib.get('sheetId'), s.attrib.get('name'), relmap.get(rid))
PY
```

## Purpose-built importers

Before writing a one-off parser, check `tools/` for a location/workbook importer. For Baltimore 2026, `tools/import-baltimore-rep-workbook.py` already imports `/Users/markrubin/Downloads/[BAL] REP 2026.xlsx`, preserves the raw workbook grid, parses daily REP rows and monthly metrics, syncs `rep_goals_2026`, and creates a DB backup:

```bash
cd /Users/markrubin/hivemind-operator
python3 tools/import-baltimore-rep-workbook.py
```

Expected Baltimore 2026 evidence from that importer:
- `daily_model_rows`: 365
- `integrity_check`: `ok`
- `rep_goals_2026` includes `Baltimore GJ` with 365 rows
- `data/rep-goals.json` includes `baltimore` after running `python3 tools/scrape-rep-goals.py`

Use the generic parsing steps below when no purpose-built importer exists.

## Parsing daily REP goals from a REP workbook

For current REP files, the daily goals are usually in the `B6Daily` sheet:
- Column B: franchise name (e.g. `Baltimore GJ`)
- Column C: Excel serial date
- Column F: total daily REP goal
- One row per day, expected 365 rows for a full non-leap year

Excel serial date conversion:

```python
from datetime import date, timedelta
excel_date = lambda n: date(1899, 12, 30) + timedelta(days=int(float(n)))
date_label = lambda d: f"{d.strftime('%a')} {d.month}/{d.day}/{d.year}"
```

Import pattern:

```python
conn.executemany('''
INSERT INTO rep_goals_2026(date, franchise, rep_goal, month, day)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(franchise, date) DO UPDATE SET
  rep_goal=excluded.rep_goal,
  month=excluded.month,
  day=excluded.day
''', parsed_rows)
```

Do not rely on lexicographic `MIN(date)`/`MAX(date)` because dates are stored as labels like `Thu 1/1/2026`. Verify chronological range by ordering `month, day`.

## Required verification

After import:

```bash
sqlite3 -header -column data/hivemind.db "
SELECT franchise, COUNT(*) rows, ROUND(SUM(rep_goal),0) total, MIN(month) min_month, MAX(month) max_month
FROM rep_goals_2026
GROUP BY franchise
ORDER BY franchise;

SELECT date, franchise, rep_goal
FROM rep_goals_2026
WHERE franchise='FRANCHISE NAME'
ORDER BY month, day
LIMIT 3;

SELECT date, franchise, rep_goal
FROM rep_goals_2026
WHERE franchise='FRANCHISE NAME'
ORDER BY month DESC, day DESC
LIMIT 3;

PRAGMA integrity_check;
"
```

Then refresh dashboard-facing current goals:

```bash
python3 tools/scrape-rep-goals.py
cat data/rep-goals.json
```

Expected success evidence:
- Full-year import count is 365 rows for a non-leap-year 2026 franchise.
- `PRAGMA integrity_check` returns `ok`.
- `tools/scrape-rep-goals.py` prints the location key and today's dollar goal.
- `data/rep-goals.json` contains the mapped location key.

## Pitfalls

- Google Sheets `401 Unauthorized` is common; immediately pivot to authenticated browser extraction or local workbook search instead of banging on the same URL.
- Hermes Google token and Safari/Chrome login are separate auth states.
- The Google Sheet URL may point to a workbook already downloaded locally under a human name like `[BAL] REP 2026.xlsx`.
- `openpyxl` may not be installed; parse XLSX as ZIP/XML with Python stdlib before installing dependencies.
- Preserve existing franchises: use `ON CONFLICT(franchise, date)` upsert for the target franchise, not a table wipe.
- Backups are cheap. Make one before import.
