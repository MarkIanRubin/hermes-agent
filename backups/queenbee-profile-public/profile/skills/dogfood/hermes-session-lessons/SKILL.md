---
name: hermes-session-lessons
description: Extract real lessons from prior Hermes sessions by combining session_search with direct inspection of local session JSON transcripts, then append dated entries to a lessons file.
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [hermes, sessions, lessons, cron, transcripts, reflection]
---

# Hermes Session Lessons

Use this when asked to summarize lessons, discoveries, mistakes, or fixes from prior Hermes work — especially for a specific day.

## Why this exists

`session_search` is good for broad recall, but it can miss date-specific detail, return summaries that are too vague, or surface the wrong day. The local session JSON files under `~/.hermes/sessions/` are the source of truth when precision matters.

## Workflow

1. **Get the actual date first**
   - Use `terminal` with `date`.
   - Derive the target date explicitly (for example, yesterday).

2. **Start with `session_search` anyway**
   - Run a broad recent-session search.
   - Run keyword searches like:
     - `lesson OR learned OR fix OR bug OR mistake OR discovery OR important`
   - Use this to identify likely session IDs and titles.

3. **Do not trust `session_search` alone for day-specific extraction**
   - If the search results are broad, truncated, or not clearly limited to the target day, inspect the local transcript files directly.
   - Find candidate files in `~/.hermes/sessions/` matching the date stamp (for example `*20260418*`).

4. **Read the local session JSON files**
   - Use `read_file` for quick inspection.
   - Use `execute_code` to parse JSON if you need to inspect message arrays cleanly.
   - Look for:
     - assistant final summaries
     - tool outputs showing the real failure mode
     - concrete discoveries, not generic platitudes

5. **Extract only grounded lessons**
   Good lessons are specific and reusable, such as:
   - a failure mode and what it actually meant
   - an operational rule that would prevent repeat mistakes
   - a reliable debugging shortcut discovered during the work

   Bad lessons are fluff, generic motivation, or anything not tied to the transcript.

6. **Append in this exact format when asked to update a lessons file**
   ```md
   ## YYYY-MM-DD
   - Lesson 1
   - Lesson 2
   ```

7. **If there was no meaningful work that day, return `[SILENT]`**
   - Use silence when there are no sessions or nothing real to extract.
   - Do not invent lessons to fill the section.

## Heuristics

- Prefer the transcript over search summaries.
- Prefer concrete failure signatures over vague conclusions.
- Separate **local success** from **remote sync success** in backup jobs; they are not the same thing.
- When a git push fails with `Repository not found` and `gh auth status` shows no login, treat it as remote access/setup validation, not a generic git failure.

## Pitfalls

- Searching all of `~` is slow and noisy. Go straight to `~/.hermes/sessions/`.
- `session_search` can return the right topic but the wrong day.
- Session JSON files can be large; use targeted reads or `execute_code` instead of dumping everything.
- Do not write “lessons” that were already present in the lessons file unless you are intentionally updating the same date.

## Verification

Before finishing:
- Confirm the target date matches the section you append.
- Confirm each lesson is traceable to an actual session/tool output.
- Re-read the edited section in the lessons file.
