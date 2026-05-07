---
name: ios-simulator-runtime-cleanup
description: Remove installed iOS Simulator runtimes/volumes on macOS, including stubborn CoreSimulator disk images, and verify reclaimed storage correctly.
version: 1.0.0
author: [REDACTED]
license: MIT
metadata:
  hermes:
    tags: [apple, macos, xcode, coresimulator, storage, cleanup]
---

# iOS Simulator Runtime Cleanup

Use this when a Mac is low on disk space and `diskutil apfs list` shows many APFS containers named like `iOS 18.4 Simulator`, `iOS 26.2 Simulator`, etc.

This is specifically for Xcode/CoreSimulator runtime disk images, not just individual simulator devices.

## What this fixes

- Many APFS containers mounted under `/Library/Developer/CoreSimulator/Volumes/...`
- Large `iOS xx.x Simulator` entries in Disk Utility / APFS
- `xcrun simctl list runtimes` showing multiple installed runtimes
- Low disk space caused by simulator runtime images

## Important lessons

- `xcrun simctl delete unavailable` is not enough if the runtimes are still installed.
- `xcrun simctl runtime delete all` is the real removal command for installed runtimes.
- After deletion starts, plain-text `xcrun simctl list runtimes` can still show stale entries while `xcrun simctl runtime list -j` already reports none.
- If deletion gets stuck in `Deleting`, restart CoreSimulator services.
- Disk free space may not visibly jump immediately; APFS accounting can lag until services restart or the machine reboots.

## Procedure

1. Inspect installed runtimes and devices:

```bash
xcrun simctl list runtimes
xcrun simctl list devices available
xcrun simctl runtime list -v
```

2. Shut down all simulator devices:

```bash
xcrun simctl shutdown all
```

3. Remove all installed simulator runtimes:

```bash
xcrun simctl runtime delete all
```

4. Verify whether CoreSimulator still thinks runtimes exist:

```bash
xcrun simctl list runtimes
xcrun simctl runtime list -j
```

5. If runtimes are stuck in `Deleting`, restart the simulator services:

```bash
killall -9 com.apple.CoreSimulator.CoreSimulatorService 2>/dev/null || true
killall -9 simdiskimaged 2>/dev/null || true
sleep 2
xcrun simctl list runtimes
```

6. Verify cleanup on disk:

```bash
du -sh "$HOME/Library/Developer/CoreSimulator" 2>/dev/null || true
find "$HOME/Library/Developer/CoreSimulator/Volumes" -maxdepth 2 -mindepth 1 2>/dev/null
find "$HOME/Library/Developer/CoreSimulator/Cryptex/Images/bundle" -maxdepth 2 -mindepth 1 2>/dev/null
```

7. Verify APFS containers are gone:

```bash
diskutil apfs list
```

You should no longer see the extra simulator containers (for example `disk5`, `disk7`, `disk9`, etc. with names like `iOS 26.2 Simulator`).

8. Check free space:

```bash
df -h /System/Volumes/Data /
```

## Verification standards

Strong evidence of success is:

- `xcrun simctl runtime list -j` returns `{}` or zero entries
- `~/Library/Developer/CoreSimulator` is nearly empty
- `diskutil apfs list` no longer shows the simulator APFS containers

## Pitfalls

- Do not confuse simulator devices with simulator runtimes. Deleting devices does not remove the large runtime images.
- Do not trust only the human-readable `simctl list runtimes` output during teardown; check JSON output too.
- If free space barely changes immediately after cleanup, that does not automatically mean deletion failed. Check APFS container removal and directory contents first.
- If space still does not return after verified deletion, reboot and re-check `df -h` and `diskutil apfs list`.

## When to reboot

Reboot if all of the following are true:

- Runtime JSON output is empty
- CoreSimulator directories are empty
- APFS simulator containers are gone
- But Finder/System Settings still shows nearly the old free-space number

That usually means storage accounting has not caught up yet.
