---
name: macos-dev-disk-space-sweep
description: Use when the user asks what is consuming disk, needs to free space, mentions DerivedData, CoreSimulator, Xcode caches, Docker, Homebrew, Codex or Claude Code storage, runner machines, or wants cleanup candidates. Runs a read-only macOS developer disk-space audit and ranks safe cleanup candidates before deletion.
---

# macOS Dev Disk Space Sweep

Use this skill for space investigations on local or SSH-accessible macOS developer machines. Start read-only, rank candidates, and ask before deleting anything.

## Safety Rules

- Do not delete on the first pass unless the user explicitly approves exact paths or categories.
- Treat CI runner workspaces as hot unless the user confirms the runner is paused or the target is disposable.
- Preserve Metal toolchains and current simulator runtimes unless the user says otherwise.
- For simulator cleanup, distinguish unavailable devices/runtimes from active named devices used for app testing.
- Verify ownership before attempting to remove another user's files.
- If a command requires sudo or another account, report the exact permission blocker and the handoff command instead of retrying noisily.

## Read-Only Sweep

Start with filesystem pressure:

```sh
df -h / /System/Volumes/Data 2>/dev/null || df -h /
```

Scan common developer storage sinks:

```sh
du -sh \
  "$HOME/Library/Developer/Xcode/DerivedData" \
  "$HOME/Library/Developer/CoreSimulator" \
  "$HOME/Library/Developer/Xcode/iOS DeviceSupport" \
  "$HOME/Library/Developer/Xcode/UserData/Previews" \
  "$HOME/Library/Caches" \
  "$HOME/.cache" \
  "$HOME/.npm" \
  "$HOME/Library/Containers/com.docker.docker" \
  "$HOME/.codex" \
  "$HOME/.claude/projects" \
  "$HOME/.claude/file-history" \
  "$HOME/Downloads" \
  "$HOME/Developer" \
  "$HOME/workspace" 2>/dev/null | sort -hr
```

Drill into the largest buckets only:

```sh
du -sh "$TARGET"/* 2>/dev/null | sort -hr | head -30
```

Useful targeted checks:

```sh
xcrun simctl list devices unavailable 2>/dev/null
xcrun simctl runtime list 2>/dev/null
brew cleanup -n 2>/dev/null
docker system df 2>/dev/null
du -sh "$HOME/.codex"/* 2>/dev/null | sort -hr
du -sh "$HOME/.claude/projects" "$HOME/.claude/file-history" 2>/dev/null   # report-only
```

## Agent Storage (Codex and Claude Code)

- `~/.claude/projects` and `~/.claude/file-history` are **report-only**. They hold Claude Code session history and memory. Report their size; never propose them as deletion targets or give a cleanup command for them.
- `~/.codex` locations (`sessions`, `worktrees`) can grow large. Old worktrees may hold uncommitted work, so check `git status` in each first, and propose archiving sessions to a location the user chooses rather than `rm`.

## Ranking Cleanup Candidates

Group findings by confidence:

- **Usually safe after confirmation**: Xcode DerivedData, module caches, old build folders, Homebrew cleanup, package manager caches, stale agent worktrees with no uncommitted work, old Downloads.
- **Needs app/tool context**: CoreSimulator devices, iOS DeviceSupport, Docker Desktop data, Hugging Face/Whisper model caches.
- **Avoid by default**: Claude Code history (`~/.claude/projects`, `~/.claude/file-history`; report-only), active runner workspaces, current simulator devices, current Metal toolchains, repo checkouts with uncommitted work.

## Report Format

Return a compact table or bullets:

- path/category
- size
- why it is likely safe or risky
- exact cleanup command, marked `read-only estimate` or `requires approval`
- expected reclaim if known

When deleting after approval:

1. Re-list the exact target.
2. Confirm ownership/permissions.
3. Run the narrow cleanup.
4. Re-check `df -h`.
5. Report before/after free space and any failures.

## Common Large Sinks

- On iOS development Macs the biggest are usually Xcode DerivedData, CoreSimulator devices and runtimes, `~/.cache/huggingface`, Docker Desktop storage, and agent sessions and worktrees (`~/.codex/sessions`, `~/.codex/worktrees`).
- On runner hosts, old simulator runtimes can be removed with `xcrun simctl runtime delete`, but runner workspaces may be actively used.
- Permission-denied cascades usually mean the target belongs to another user; stop and verify with `ls -ldeO` or `stat`.
