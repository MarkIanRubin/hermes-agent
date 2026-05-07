---
name: git-submodule-push-handling
description: Handle git repositories with submodules during automated push operations, especially when submodules have permission restrictions
tags: [git, submodules, automation, cron, push, permissions]
---

# Git Submodule Push Handling

Handle automated git operations in repositories containing submodules, especially when upstream permissions vary between parent and submodule repositories.

## When to Use

- Automated cron jobs pushing changes to repositories with submodules
- Mixed changes across parent repository and submodules
- Submodule upstream permission restrictions
- Embedded git repository situations

## Workflow

### 1. Initial Assessment
```bash
cd ~/target-repo
git status
```
Look for:
- `modified: path/to/submodule (modified content)` - indicates submodule changes
- `modified: path/to/submodule (new commits)` - indicates submodule reference updates

### 2. Commit Parent Repository Changes First
```bash
# Add and commit regular file changes
git add -A
git status
git commit -m "Update main repository files"
```

### 3. Handle Submodule Changes
```bash
# Navigate to submodule
cd path/to/submodule
git status

# Commit submodule changes locally
git add -A
git commit -m "Auto-commit: update submodule configuration and code changes"

# Attempt upstream push (may fail with permissions)
git push
```

### 4. Handle Push Failures Gracefully
If submodule push fails with 403/permission denied:
- Don't error out - this is expected for read-only upstream submodules
- Continue with parent repository operations
- The local commits are preserved

### 5. Update Parent Repository Submodule Reference
```bash
cd .. # back to parent repo
git add path/to/submodule
git commit -m "Update submodule reference"
git push
```

## Common Issues & Solutions

### Embedded Git Repository Warning
```
warning: adding embedded git repository: path/to/submodule
hint: You've added another git repository inside your current repository.
```

**Solution:** This is expected when submodules aren't properly configured. The workflow above handles this gracefully.

### Missing .gitmodules
If `.gitmodules` file is missing, treat the submodule as an embedded repository rather than trying to fix submodule configuration during automated operations.

### Permission Denied on Submodule Push
```
remote: Permission to upstream/repo.git denied to username.
fatal: unable to access 'https://github.com/upstream/repo.git/': The requested URL returned error: 403
```

**Solution:** Expected behavior. Continue with parent repository operations. The submodule changes are committed locally and the parent repo reference will be updated.

### Repository Not Found
```
remote: Repository not found.
fatal: repository 'https://github.com/user/repo.git/' not found
```

**Common causes:**
- Repository doesn't exist yet
- Private repository without proper access tokens
- Authentication method mismatch (SSH vs HTTPS)

**Solution:** In automated contexts, document the failure but preserve local commits. Manual intervention needed for authentication setup.

### SSH Authentication Failures
```
[REDACTED_EMAIL]: Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Solution:** Switch to HTTPS temporarily, or document the need for SSH key setup. Don't attempt key generation in automated contexts.

## Automation Considerations

- Always commit parent repository changes first to avoid losing work
- Handle submodule push failures gracefully - don't fail the entire operation
- Preserve local submodule commits even if upstream push fails
- Update parent repository submodule references regardless of submodule push success

## Pitfalls

- Don't attempt to fix submodule configuration during automated runs
- Don't fail the entire operation if one component can't push upstream
- Don't use `git submodule update` when .gitmodules is missing/corrupted
- Don't recursively delete .git directories without understanding the implications

## Exit Strategy

If operations get complex or require user intervention:
1. Commit what you can
2. Document what's left to do
3. Exit gracefully rather than risking data loss
