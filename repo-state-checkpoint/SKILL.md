---
name: repo-state-checkpoint
description: Verify an exact repository, checkout, branch, SHA, and dirty-state before code changes, release promotion, delegation, or handoff work. Use when the user gives a repo path, expected commit, setup command sequence, dirty-tree warning, release branch, worktree/clone request, or asks for precise repo location/state with no guessing.
---

# Repo State Checkpoint

Use this skill before changing code or reporting repo readiness when the task depends on the exact checkout. The goal is a small, reliable checkpoint: correct path, correct repo, correct branch/SHA, clean or explicitly blocked state.

## Core Rules

- Treat an explicit user path as authoritative. If it does not exist, stop and report the missing path; do not silently substitute a nearby repo.
- Read local guidance before edits: nearest `AGENTS.md` or `CLAUDE.md`, `README*`, release docs, or repo-specific scripts named by the user.
- If the worktree is dirty, stale, behind, detached unexpectedly, or ambiguous, do not make code changes until the blocker is reported and resolved.
- When the user gives an expected SHA or command sequence, execute it literally unless unsafe, then verify exact output.
- For release promotion, prefer repo-specific scripts/docs over generic PR or merge habits.

## Checkpoint Procedure

Run the smallest useful set:

```sh
pwd
test -d "$REPO" && cd "$REPO"
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short --branch
git fetch origin --prune
git status --short --branch
```

If an exact branch or SHA is requested:

```sh
git checkout <branch-or-ref>
git rev-parse HEAD
git status --short --branch
```

If a release path is requested, also inspect likely policy files:

```sh
rg -n "promote|release|production|main|develop|fast-forward|deploy" AGENTS.md CLAUDE.md README* docs scripts .github 2>/dev/null
```

## Report Format

Keep the checkpoint compact and concrete:

- `repo`: absolute path and `git rev-parse --show-toplevel`
- `remote`: origin URL
- `branch`: current branch/tracking state
- `HEAD`: full SHA
- `status`: clean, dirty file list, behind/ahead, detached, or missing path
- `guidance`: files/scripts found that constrain the task
- `blocker`: exact reason work cannot proceed, if any
- `next action`: the fetch/pull/checkout/branch/confirmation needed

When finishing repo work, include:

- changed files
- tests run
- branch/commit
- blockers or remaining risk

## Common Pitfalls

- Nonexistent `workdir` failures happen before repo commands run; report the exact path failure.
- A nearby similarly named checkout is only a clue, not permission to switch paths.
- Detached worktrees can be normal for automations; prefer SHA/file-path evidence over branch assumptions.
- `git add .` is too broad in messy repos. Stage only the intended files after checking `git diff --name-only`.
