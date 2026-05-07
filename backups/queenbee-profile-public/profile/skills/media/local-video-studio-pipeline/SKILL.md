---
name: local-video-studio-pipeline
description: "Build a local video/movie studio workspace: inventory local footage, inspect metadata with ffprobe, extract stills with ffmpeg, transcribe audio with Whisper, and generate a browsable storyboard."
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [video, movie-studio, ffmpeg, ffprobe, whisper, storyboard, local-media]
---

# Local Video Studio Pipeline

## When to use

Use this when the user wants to set up or continue a local movie/video studio, organize raw clips, inspect a folder of videos, generate stills/contact sheets, transcribe local video/audio, create a storyboard/review page, or prepare footage for later editing/publishing.

Class of task: turn scattered local media files into a repeatable local production workspace with inventory, metadata, stills, transcripts, and a browsable storyboard.

## Preconditions

Check tools first:

```bash
command -v ffmpeg
command -v ffprobe
command -v whisper || true
python3 --version
```

If Whisper is missing but transcription is required, install or use the existing environment that has `whisper`. For CPU/macOS CLI transcription, pass `--fp16 False` to avoid FP16/GPU warnings/failures.

## Recommended workspace

```bash
STUDIO="$HOME/projects/movie-studio"
mkdir -p "$STUDIO"/{source,assets,transcripts,metadata,stills,clips,scripts,exports}
```

Folder roles:

- `source/` — optional copies/symlinks of raw source footage
- `metadata/` — inventories and ffprobe analysis
- `stills/` — generated frame grabs/contact-sheet stills
- `transcripts/` — Whisper transcripts
- `clips/` — extracted working clips
- `assets/` — music, voiceover, images, graphics
- `exports/` — storyboard pages and final renders
- `scripts/` — repeatable pipeline tools

## Pipeline shape

1. **Inventory** local videos from obvious roots such as `~/Downloads`, project folders, iCloud exports, or a user-specified source directory.
2. **Analyze** each file with `ffprobe -print_format json -show_format -show_streams`.
3. **Extract stills** with `ffmpeg` at early/mid/late timestamps, e.g. 15%, 50%, 85% of duration.
4. **Transcribe** short clips with audio using Whisper; skip no-audio clips and long clips unless explicitly requested.
5. **Generate storyboard HTML** showing clip name, duration, resolution, audio presence, stills, transcript preview, and original path.
6. **Verify** counts and render the storyboard in a local browser/server.

## Useful implementation pattern

Create a single Python script, e.g. `scripts/movie_studio.py`, with subcommands:

```bash
python3 scripts/movie_studio.py inventory --limit 100
python3 scripts/movie_studio.py analyze --limit 20
python3 scripts/movie_studio.py transcribe --limit 12 --model tiny
python3 scripts/movie_studio.py storyboard --limit 20
```

Key details:

- Slugify filenames for stable output names.
- Store absolute source paths in JSON so files do not need to be copied.
- Preserve both raw inventory and analyzed metadata.
- Use `Path.relative_to(STUDIO)` for storyboard image links when stills are inside the workspace.
- Normalize Whisper output filenames because the CLI writes files using the original basename, not necessarily the slug.

Whisper CLI command that worked reliably on macOS CPU:

```bash
whisper "$VIDEO" --model tiny --language en --fp16 False --output_dir transcripts --output_format txt
```

Use `tiny` for fast rough transcripts; use `base` or better when text quality matters.

## Verification checklist

Run these before saying the studio is ready:

```bash
python3 -m py_compile scripts/movie_studio.py
test -s metadata/video-inventory.json
test -s metadata/video-analysis.json
test -s exports/storyboard.html
python3 - <<'PY'
import json, pathlib
root = pathlib.Path('.')
print('inventory_count', len(json.loads((root/'metadata/video-inventory.json').read_text())))
print('analysis_count', len(json.loads((root/'metadata/video-analysis.json').read_text())))
print('stills_count', len(list((root/'stills').glob('*.jpg'))))
print('transcript_count', len([p for p in (root/'transcripts').glob('*.txt') if not p.name.endswith('.error.txt')]))
print('error_count', len(list((root/'transcripts').glob('*.error.txt'))))
PY
```

Browser verification:

```bash
python3 -m http.server 8093
# open http://127.0.0.1:8093/exports/storyboard.html?verify=ready
```

In the browser console, check:

```js
(() => ({
  cards: document.querySelectorAll('.clip-card').length,
  images: document.querySelectorAll('.clip-card img').length,
  transcripts: [...document.querySelectorAll('.transcript')].filter(p => !p.textContent.includes('No transcript')).length,
  title: document.title,
  overflowX: document.documentElement.scrollWidth - innerWidth
}))()
```

Expected: storyboard title present, card/image counts match outputs, no horizontal overflow, no console errors.

## Pitfalls

- Don't call the studio finished just because inventory/stills exist; transcription and storyboard verification may still be incomplete.
- `search_files` over all of `/Users` can time out. Prefer targeted roots like `~/Downloads` and known project directories.
- Some video files may fail `ffprobe`; keep the item with an `error` field rather than crashing the whole run.
- No-audio videos are normal; skip transcription for those.
- Future publishing/rendering is a separate layer: clip selection, narration/script generation, music/voiceover assets, and final ffmpeg render recipes.
- Browser vision may fail in some Hermes/Codex sessions; still verify with DOM counts, console errors, file existence, and optional screenshot path.
