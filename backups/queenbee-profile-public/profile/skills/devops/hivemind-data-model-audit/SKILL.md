---
name: hivemind-data-model-audit
description: Audit HiveMind Operator SQLite data coverage and decide whether the stored data supports Demand, Money, Process, and People models.
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [hivemind, sqlite, data-audit, business-models, dashboard]
---

# HiveMind Data Model Audit

## When to use

Use this when Mark asks whether HiveMind has today's data, historical/inter-day snapshots, revenue totals, or enough database coverage to build/validate HiveMind models such as Demand Engine, Money Engine, Process Engine, People Engine, Revenue Velocity, Gantt, routing, labor, or margin.

Class of task: inspect HiveMind Operator's live SQLite/dashboard payloads and map available fields to the business models they can or cannot support.

## Repo and DB

Default repo:

```bash
cd /Users/markrubin/hivemind-operator
```

Primary DB:

```bash
data/hivemind.db
```

Tables commonly relevant:
- `daily_snapshots` — one current/upserted row per `date + location`; contains `crews_data`, `summary_data`, `jobs_count`, `completed_count`, `total_revenue`, `rep_goal`, `snapshot_date`, `two_week_future_jobs`, `two_week_future_value`
- `encrypted_json_payloads` — encrypted dashboard/Gantt/historical JSON artifacts; use filenames and `updated_at` to assess freshness without decrypting
- `revenue_booking_events` — append-only booking/revenue event tracking when populated
- `wage_daily` / `wage_alerts` — labor/wage model data when populated
- `rep_goals_2026` — goals by franchise/date
- `analyze_report_snapshots` — nearby/route analysis snapshots

## Required preflight

Always ground date-sensitive answers with the live date:

```bash
date '+%Y-%m-%d %Z'
```

Inspect schema before assuming fields:

```bash
sqlite3 data/hivemind.db '.tables'
sqlite3 data/hivemind.db '.schema daily_snapshots'
```

## Revenue / daily snapshot totals

Use local date unless Mark specifies another date:

```bash
TODAY=$(date '+%Y-%m-%d')
sqlite3 -header -column data/hivemind.db "
SELECT date, location, jobs_count, completed_count, total_revenue, updated_at
FROM daily_snapshots
WHERE date='$TODAY'
ORDER BY location;

SELECT 'TOTAL' AS label,
       COUNT(*) AS locations,
       SUM(jobs_count) AS jobs,
       SUM(completed_count) AS completed,
       ROUND(SUM(total_revenue), 2) AS total_revenue,
       ROUND(SUM(two_week_future_value), 2) AS two_week_future_value
FROM daily_snapshots
WHERE date='$TODAY';
"
```

## Inter-day vs intraday snapshot check

`daily_snapshots` is currently upserted on `UNIQUE(date, location)`, so it preserves one latest row per day/location, not a history of multiple intraday versions.

Check coverage:

```bash
sqlite3 -header -column data/hivemind.db "
SELECT 'daily_snapshots' AS table_name,
       COUNT(*) AS rows,
       MIN(date) AS min_date,
       MAX(date) AS max_date,
       MIN(created_at) AS min_created,
       MAX(updated_at) AS max_updated
FROM daily_snapshots;

SELECT date,
       COUNT(*) AS locations,
       ROUND(SUM(total_revenue),2) AS total_revenue,
       SUM(jobs_count) AS jobs,
       MAX(updated_at) AS last_updated
FROM daily_snapshots
GROUP BY date
ORDER BY date DESC
LIMIT 30;

SELECT date, location, COUNT(*) AS versions
FROM daily_snapshots
GROUP BY date, location
HAVING COUNT(*) > 1
LIMIT 10;
"
```

If the duplicate/version query is empty, say clearly: historical daily snapshots exist, but true intraday versioning does not.

## Payload field coverage audit

Use Python to inspect JSON payload contents rather than guessing from column names:

```bash
python3 - <<'PY'
import sqlite3, json, collections, datetime
DB='data/hivemind.db'
today=datetime.datetime.now().strftime('%Y-%m-%d')
conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row
rows=conn.execute("""
  SELECT location, crews_data, summary_data, jobs_count, completed_count,
         total_revenue, rep_goal, two_week_future_jobs, two_week_future_value, updated_at
  FROM daily_snapshots WHERE date=? ORDER BY location
""", (today,)).fetchall()
job_keys=collections.Counter(); fields=collections.Counter(); status=collections.Counter(); crew_keys=collections.Counter()
job_count=0; locations_with_crews=0; summary_keys=[]
for r in rows:
    crews=json.loads(r['crews_data'] or '[]')
    summary=json.loads(r['summary_data'] or '{}')
    summary_keys.append(set(summary.keys()))
    if crews: locations_with_crews += 1
    for crew in crews:
        crew_keys.update(crew.keys())
        for job in crew.get('jobs') or []:
            job_count += 1
            job_keys.update(job.keys())
            status[(job.get('status') or '').strip().lower()] += 1
            for k,v in job.items():
                if v not in (None, '', [], {}): fields[k] += 1
print('snapshot rows:', len(rows))
print('locations with crews_data:', locations_with_crews)
print('jobs found in crews_data:', job_count)
print('summary keys:', sorted(set().union(*summary_keys)) if summary_keys else [])
print('crew keys:', crew_keys.most_common())
print('job keys:', sorted(job_keys.keys()))
print('status counts:', status.most_common())
for k in ['amount','status','start','end','address','latitude','longitude','salesforceId','pipelineUrl','crew','resourceId','duration','notes']:
    print(f'nonempty {k}:', fields.get(k,0))
print(dict(conn.execute("""
  SELECT COUNT(*) AS locations, SUM(jobs_count) AS jobs_count,
         SUM(completed_count) AS completed_count,
         ROUND(SUM(total_revenue),2) AS total_revenue,
         ROUND(SUM(rep_goal),2) AS rep_goal,
         SUM(two_week_future_jobs) AS future_jobs,
         ROUND(SUM(two_week_future_value),2) AS future_value
  FROM daily_snapshots WHERE date=?
""", (today,)).fetchone()))
print('booking events today:', conn.execute('SELECT COUNT(*) FROM revenue_booking_events WHERE booking_date_et=?', (today,)).fetchone()[0])
print('wage_daily today:', conn.execute('SELECT COUNT(*) FROM wage_daily WHERE date=?', (today,)).fetchone()[0])
PY
```

## Workbook / spreadsheet coverage for Money Engine

When the DB includes imported workbook cells/sheets, audit them separately from scraped operating data. Business plan and pricing workbooks can strongly support budget, forecast, REP/goal, pricing, funnel, and planned-margin logic, but they do not prove actual costs were imported.

Look for tables/import artifacts containing workbook metadata, sheet names, and cell text/values. Search schemas dynamically because workbook import table names may vary:

```bash
sqlite3 data/hivemind.db ".tables" | tr ' ' '\n' | grep -Ei 'workbook|sheet|cell|excel|spreadsheet|price|plan|goal|budget|forecast'
```

Then inspect sheet names and row counts. Useful Money Engine workbook signals include:
- business plan / operating budget / P&L / finance forecast / monthly revenue / revenue goals / funnel
- advertising and marketing cost plans
- truck leasing, insurance, disposal, labor, or other operating-budget categories
- pricing sheets, current/new pricing, competitive/service analysis
- color legend text such as better/same/worse than budget, yellow/manual input cells, or threshold notes

Be strict in the conclusion:
- Planned budget/forecast confidence can be high from workbook coverage.
- Actual revenue confidence can be high from `daily_snapshots`.
- Actual cost/profit confidence is incomplete unless labor, fuel, disposal, truck hours, marketing actuals, and accounting/P&L actuals are populated.

## REP / goal sanity check

Do not trust `rep_goals_2026` just because the table exists. Confirm it contains the target franchise/location before using it for color coding.

```bash
sqlite3 -header -column data/hivemind.db "
SELECT franchise, COUNT(*) AS rows, MIN(date) AS min_date, MAX(date) AS max_date
FROM rep_goals_2026
GROUP BY franchise
ORDER BY franchise;
"
```

If Mark asks about Baltimore but `rep_goals_2026` only shows another franchise (for example Las Vegas), say the imported REP goal table is wrong for Baltimore in this DB snapshot and must be re-imported before REP-based daily color coding is reliable.

## Suggested first-pass Money color bands

Use these as defaults when the workbook gives no explicit thresholds:
- Revenue vs REP/goal: green `actual >= goal`; yellow `actual >= 90% of goal`; red `< 90%`.
- Budget/cost: green `actual <= budget`; yellow `actual <= 105% of budget`; red `> 105%`.
- Profit/margin: green at or above planned margin; yellow within 2 points below plan; red more than 2 points below plan.
- Velocity/pace: green projected above goal; yellow projected 90–100%; red projected below 90%.

Label confidence by input family: revenue/goal, budget plan, actual costs, and booking velocity.

## Model readiness rubric

### Usually supported by current `daily_snapshots`
- Gantt/schedule operating model: crew names, jobs, start/end, status, amount, address, lat/lng, Salesforce IDs, pipeline URLs.
- Basic Money Engine: total revenue, completed count, AJS (`total_revenue / completed_count`), open/completed counts, future booked value.
- Basic Process Engine: status distribution such as scheduled, dispatched, call ahead, en route, on site, completed, cannot complete.
- Basic People Engine: crew-level workload, route density/locations, scheduled capacity visibility.

### Usually missing or weak unless extra tables are populated
- Demand Engine: traffic/calls/leads/conversion funnel is not in `daily_snapshots`.
- True Money Engine / margin: expenses, labor cost, disposal, fuel, materials, truck hours, RPH/EPH/PPH require additional sources.
- Process friction: transition timestamps between statuses and reason codes are not present in the current job payload.
- People capacity: employee identities, wages, hours, roles, constraints, skill levels are missing unless `wage_daily` or another labor import is populated.
- Intraday modeling: `daily_snapshots` overwrites by `date + location`; add append-only events/snapshots for 9am/noon/5pm comparisons.
- Booking velocity: `revenue_booking_events` must have rows for the target date; if zero, same-day booking velocity is not populated.

## Recommended next schema when model readiness is incomplete

For intraday models, recommend an append-only table instead of overloading `daily_snapshots`:

```sql
CREATE TABLE snapshot_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  business_date TEXT NOT NULL,
  location TEXT NOT NULL,
  jobs_count INTEGER DEFAULT 0,
  completed_count INTEGER DEFAULT 0,
  total_revenue REAL DEFAULT 0,
  rep_goal REAL DEFAULT 0,
  two_week_future_jobs INTEGER DEFAULT 0,
  two_week_future_value REAL DEFAULT 0,
  summary_data TEXT,
  crews_data TEXT
);
CREATE INDEX idx_snapshot_events_date_location ON snapshot_events(business_date, location, captured_at);
```

For full Business Visualization/HiveMind models, propose imports/tables for:
- demand funnel events: traffic, calls, leads, estimates, bookings
- status transition events: job id, from_status, to_status, timestamp, source
- labor/wage facts: crew/employee, hours, wages, route date, location
- expense facts: truck hours, disposal, fuel, materials, fees

## Reporting style

Be blunt and split the answer into:
1. What the DB definitely has.
2. Which models that supports.
3. What is missing.
4. The next schema/import to add.

Do not claim "full model readiness" just because revenue totals exist. Revenue + Gantt is the spine, not the whole nervous system.
