---
name: review-loop
description: "Run a strict, scope-locked multi-agent code review and repair loop for project repositories. Use when the user asks for review-loop, three-clean-review, repeated /review passes, PR readiness, review-until-clean, or wants in-scope issues found by review agents fixed automatically before re-review. Applies to a specific PR, feature, or bounded diff; unrelated or pre-existing findings are reported separately and never expanded into the repair loop without user approval."
---

# Review Loop

## Overview

Use this skill to turn `/review` into a closed, **scope-locked** loop: review a specific PR, feature, or bounded diff with three independent subagents, fix eligible in-scope issues, verify, then review again until three clean reviews are received in the same round. Keep the main agent as orchestrator and final reviewer; treat subagent output as evidence to inspect, not truth to blindly merge.

This is not a general repository audit, security-hardening exercise, or license to fix every real issue a reviewer can discover. Reviewers may inspect adjacent code to understand the changed behavior, but the repair scope remains closed-world.

## Scope Contract

Before launching reviewers, write down a compact scope contract containing:

- The user-requested change or PR being reviewed.
- The base and head/diff being reviewed.
- The explicit allowed paths for automatic repair.
- The direct behavior and regression surface that count as in scope.
- Known unrelated dirty files or subsystems that are excluded.
- Targeted verification commands.

If there is no PR, scope is the user-requested change plus the files already changed specifically for it. Do not silently define scope as the repository's entire dirty diff when that diff contains unrelated work.

The allowed-path list is locked once the first review round starts. Reading direct callers, consumers, and configuration outside it is allowed when necessary to understand impact. Editing outside it, adding a new subsystem, or changing the architecture/trust model requires user approval before continuing.

### Finding eligibility

A finding is eligible to enter the automatic repair loop only when all are true:

1. It is caused by the scoped diff, is a direct regression exposed by that diff, or prevents the user-requested behavior from being correct and safe.
2. It can be fixed within the locked allowed paths and the original design intent.
3. It is concrete and evidenced by files, lines, behavior, or a reproducible command.

The following are out of scope even when technically valid:

- Pre-existing defects unrelated to the changed behavior.
- General hardening opportunities in an adjacent subsystem.
- Architectural redesigns, new test seams, migrations, or trust-boundary changes not required by the PR.
- Findings that require broadening the allowed paths or changing product behavior.

Record out-of-scope findings separately. They do not reset the clean-review count and must not be fixed automatically. A severe out-of-scope finding may be called out as a separate release risk, but it still requires explicit user approval for repair.

## Completion Rule

Classify review as done only when all are true:

- Three independent review passes in the latest round report no new eligible in-scope issues.
- Required checks or targeted verification have passed, or any unrun checks are explicitly reported with the reason.
- The orchestrator has inspected the final diff after fixes.

If any pass finds a new eligible in-scope issue, fix it and reset the clean-review count to zero. Out-of-scope findings do not prevent a reviewer from being clean for the scoped change. Do not count the orchestrator's own inspection as one of the three clean reviews.

Completion never overrides the scope contract or the circuit breaker below. If clean completion would require scope expansion, stop and ask rather than expanding the work.

## Workflow

1. Establish scope.
   - Read repo instructions such as `AGENTS.md` or `CLAUDE.md`.
   - Inspect branch, dirty state, and the relevant diff.
   - Write the scope contract above, including exclusions and locked allowed paths.
   - Separate the scoped diff from unrelated dirty work before prompting reviewers.

2. Launch three independent review subagents.
   - Use available subagent or delegation tools when possible. If the exact tool is not loaded, search for multi-agent/subagent tools first.
   - Give each subagent the repo path, scope contract, scoped diff or branch/base, and a clear instruction to review only, not patch.
   - Explicitly state that adjacent code may be inspected for impact but unrelated or pre-existing issues must be classified out of scope, not turned into repair requests.
   - Keep prompts independent; do not leak findings from one reviewer into another before all three return.
   - If real subagents are unavailable, state the limitation and perform three separate review passes with the lenses below. Mark the result as a fallback, not subagent-backed.

3. Use three different review lenses.
   - Reviewer A, correctness and regressions: logic bugs, edge cases, data contracts, API behavior, state handling.
   - Reviewer B, tests and verification: missing coverage, failing or skipped checks, flaky paths, setup gaps, test quality.
   - Reviewer C, architecture and risk: architectural, concurrency, performance, security/privacy, UX, or operational consequences introduced by the scoped change. This is not a whole-system audit.

4. Triage findings.
   - Apply the finding-eligibility test before treating any finding as actionable.
   - Keep only concrete, eligible in-scope issues grounded in files, lines, behavior, or commands in the repair queue.
   - Deduplicate overlapping findings across reviewers.
   - Reject justified no-ops and speculative preferences; record why they are not being changed if useful.
   - Put valid but out-of-scope findings in a separate follow-up list; do not repair them and do not reset the clean count.

5. Fix eligible in-scope issues automatically.
   - Modify only locked allowed paths and keep fixes narrowly scoped to the reviewed change.
   - Prefer reverting a problematic repair over widening the architecture to preserve it.
   - Do not add a new subsystem, test-only production seam, persistence format, public API, trust boundary, installer/release mechanism, or unrelated hardening layer without explicit user approval.
   - Preserve user changes and unrelated dirty work.
   - Follow project delegation policy. If a repo asks for a separate worker model for mechanical patching, delegate bounded fixes, then inspect the worker report and diff before integrating.
   - Stop and ask the user before destructive, risky, production-mutating, or scope-expanding changes. Do not continue reviewing a proposed scope expansion while waiting.

6. Verify after fixes.
   - Run targeted tests, linters, type checks, builds, or smoke paths that match the changed surface.
   - If a command cannot run because of missing environment or credentials, capture the exact blocker and use the next best local verification.

7. Repeat review rounds.
   - After every fix, start a fresh round with three independent reviews.
   - The clean count is the number of independent reviews in the current round that report no new eligible in-scope issues.
   - Any new eligible in-scope issue resets the count to zero after it is fixed.
   - Stop only at three clean reviews in one round.

## Circuit Breaker

Without a different limit explicitly supplied by the user, pause the automatic loop at the first of:

- Three total review rounds.
- Two repair cycles.
- Thirty minutes of elapsed loop work.
- A proposed fix that requires any scope-contract expansion.

At the circuit breaker, stop making changes and report: current round, in-scope findings fixed, remaining in-scope blockers, out-of-scope follow-ups, checks run, and the exact approval needed to continue. Do not launch another review round automatically. A circuit-breaker pause is an incomplete review checkpoint, not a clean result.

## Subagent Prompt Shape

Use concise prompts like:

```text
Review the changes in <absolute repo path> using the <lens> lens.
Scope contract: <user-requested behavior, base/head, allowed paths, direct regression surface, exclusions>.
Review only defects caused by this scoped change or direct regressions necessary to make it correct and safe. You may inspect adjacent code for impact, but do not audit the whole repository. Classify pre-existing issues, general hardening, architectural redesigns, and fixes requiring paths outside the allowlist as OUT_OF_SCOPE; they do not make this review unclean.
Do not modify files. Return eligible findings with severity, file/line, evidence, and a short in-scope fix. List any OUT_OF_SCOPE observations separately. If no eligible in-scope issue is found, say exactly "CLEAN".
```

## Reporting

While working, report concise progress: review round, elapsed time, eligible in-scope findings, out-of-scope observations, fixes made, checks run, and current clean count. Final response should state whether review is done or paused at the circuit breaker, list scoped fixes, summarize verification, and call out unrun checks and separate follow-ups.
