---
name: git-auth-backup-recovery
description: Handle git authentication failures in automated backup systems with graceful fallbacks
tags: [git, authentication, cron, backup, automation]
---

# Git Authentication & Backup Recovery

When automated git backups fail due to authentication issues, implement robust fallback strategies that ensure data preservation and clear error reporting.

## When to Use

- Cron jobs or automated scripts pushing to remote git repositories fail
- `git push` returns authentication or repository not found errors
- GitHub CLI (`gh`) authentication has expired or is missing
- Need to implement resilient backup automation

## Diagnosis Steps

1. **Check git remote status**:
   ```bash
   cd ~/target-repo && git remote -v
   git status
   ```

2. **Test authentication**:
   ```bash
   gh auth status
   git push --dry-run
   ```

3. **Identify the failure mode**:
   - Repository doesn't exist remotely
   - Authentication expired/missing
   - Network connectivity issues

## Recovery Strategy

### 1. Immediate Local Backup
Priority: Ensure data is preserved locally regardless of remote issues.

```bash
cd ~/backup-repo
cp source-files ./
git add .
git commit -m "Backup $(date '+%Y-%m-%d %H:%M:%S')"
```

### 2. Fix Authentication
For GitHub CLI issues:
```bash
gh auth login --web --hostname github.com --scopes repo
```

For SSH key issues:
```bash
ssh-keygen -t ed25519 -C "[REDACTED_EMAIL]"
gh auth refresh --scopes repo
```

### 3. Update Automation to Be Resilient

Replace brittle cron jobs with robust ones that:
- Always commit locally first
- Attempt remote push with error handling
- Report specific failure modes
- Continue operating even with remote failures

Example cron job prompt:
```
Backup files to local git repository. Copy source files, commit changes with timestamp, and attempt remote push. If push fails due to authentication, commit locally and report the issue clearly. This ensures local backup succeeds even if remote sync fails.
```

## Pitfalls

- **Don't fail silently**: Always report the specific authentication issue
- **Local backup first**: Never let remote failures prevent local commits
- **Test interactively**: `gh auth login` requires browser interaction
- **Memory management**: Update persistent notes about auth requirements
- **User coordination**: Authentication setup may require user intervention
- **Branch name mismatches are common**: A repo may have local `master` while the remote HEAD advertises `main`. Check `git branch -vv` and `git remote show origin`, then push the actual tracked branch instead of assuming `main`.
- **Ignored files can still be tracked**: Adding `.venv` or `__pycache__` to `.gitignore` does nothing for files already staged/tracked. Use `git ls-files -ci --exclude-standard` to find tracked-now-ignored files, then `git rm -r --cached` them and amend/recommit before retrying the push.
- **Large-file push failures may come from local environments**: If GitHub rejects a push for files >100 MB, first look for vendored virtualenvs, caches, or build artifacts accidentally added to the commit before considering LFS.
- **`Repository not found` is not always bad auth**: if the credential works for `https://api.github.com/user` but the repo endpoint returns 404, the backup repo may simply not exist yet. Create it first instead of wasting time rotating credentials.
- **HTTP 400 on push can mean the local backup repo history is garbage, not that GitHub is down**: if the repo was supposed to back up a handful of files but `git count-objects -vH` shows tens of thousands of objects or hundreds of MB, inspect reachable blobs with `git rev-list --objects --all | git cat-file --batch-check=... | sort -k3 -n | tail`. Nested repos, migration archives, `node_modules`, and copied application state can poison the backup repo.
- **When a backup repo is polluted, stop trying to brute-force the push**: make a safety branch/snapshot first, then rebuild a clean orphan history that tracks only the intended backup files, and push that clean history to the remote.

## Verification

1. Local commit succeeded: `git log -1 --oneline`
2. Remote push status: Check for specific error messages
3. Cron job resilience: Verify it handles auth failures gracefully
4. Documentation: Update memory/notes with authentication requirements

## Recovery Options

If remote push continues failing:
1. **Local-only mode**: Keep committing locally until auth is fixed
2. **Alternative remotes**: Configure backup remote repositories
3. **Export strategy**: Regular tar/zip exports as additional backup layer
4. **User notification**: Clear reporting of what needs manual intervention

The key principle: **Local data preservation always succeeds, remote sync is best-effort**.
