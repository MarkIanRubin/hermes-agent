HiveMind BI: future funnel = Salesforce scheduled_date; failed same-day scrapes should carry prior values, not zero totals.
§
Core lessons: fix systems not symptoms; change approach after two failures; prefer one clear writer per mutation path; verify before claiming fixed.
§
Core lessons: verify with the best available evidence, ideally real browser checks for UI, and never say fixed before confirmation or ask Mark to debug what tools can inspect.
§
On Mark's Mac, one VNC outage was caused by actual system sleep, not a screensharingd crash or normal idle settings.
§
hivemind-operator: $HOME/hivemind-operator; service com.hivemind.dashboard-server; root AGENTS.md/CLAUDE.md hold bot coding rules. Okta may need macOS Node auth; choose saved user-id row for password; MFA via phone+Send code then read-mfa-code.py (fallback get-mfa-code.scpt); stuck Safari scrape pages: refresh twice, then reopen/re-auth once.
§
MoeGo/browser automation can blank pages or drop sessions during navigation/calendar work; refresh snapshots often, expect re-login, and distrust temporary all-zero calendar states until the week fully reloads.
§
For MoeGo Scott Lab on QueenBee, if local OPENAI_API_KEY is missing, reuse the OPENAI_API_KEY from $HOME/hivemind-operator/.env.
§
For Scott Lab/MoeGo work: use real MoeGo data only; nearby-route filtering applies only to route suggestions, while day Gantt/day summary must always use full-day MoeGo jobs.
§
Mark has a NousResearch account/API key available as a fallback provider if the direct OpenAI GPT-4.5-style setup stops working; don't switch unless needed.
§
For MoeGo message scrapes, Mark wants incremental backfill only: scrape back only to the last known message/date, not full re-scrapes of entire history.
§
For Scott Lab/MoeGo message scraping, Mark wants incremental capture to stop once existing data is reached, with a hard maximum lookback of 30 days—do not keep walking back older history by default.
§
For pendulum sonification/video-analysis outputs, Mark wants the reference grid added back onto the finished video, not just separate analysis previews.
