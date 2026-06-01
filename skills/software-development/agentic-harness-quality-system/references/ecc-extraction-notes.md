# ECC Extraction Notes

Source reviewed: `https://github.com/affaan-m/ECC`

Local clone inspected at commit `64cd1ba fix: surface warn-only PreToolUse hooks (#2084)`.

Verification run:

```bash
cd /tmp/ecc-review
npm ci --ignore-scripts
npm test
```

Result: `2582 passed, 0 failed`.

## Keep

- Selective install / component manifests instead of blanket installs.
- Doctor / repair / uninstall operations backed by managed state.
- Evidence-first code review guardrails, especially false-positive control.
- Hook schema validation and timeout/failure-mode discipline.
- Supply-chain IOC scanning, workflow security tests, and no-personal-path validation.
- Session/status snapshots that summarize action, verification, and next step.
- Cross-harness capability thinking: adapters must declare what each harness supports.

## Do Not Import Wholesale

- 249 skills / 79 commands as an always-on surface.
- Large generic rules such as universal TDD or universal immutability.
- Claude-Code-specific hook assumptions without Hermes adaptation.
- Marketing language as operating doctrine.

## Hermes Strategy

Use ECC as a quarry:

1. Convert useful patterns into compact Hermes skills.
2. Keep heavy examples in references.
3. Sync important skills into active profiles.
4. Add validators/scripts only when the workflow repeats enough to justify maintenance.
