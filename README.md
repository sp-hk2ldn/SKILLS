# Skills

Agent skills for iOS development and AI coding agents. Each folder is one skill: a `SKILL.md`
with instructions, plus any helper scripts. They work with Claude Code and Codex.

| Skill | What it does |
| --- | --- |
| [`ios-ota-install`](ios-ota-install/) | Installs a development iOS build on your own phone from a Safari link served over your Tailscale tailnet, for when Xcode cannot reach the phone. |
| [`swiftui-full-bleed-screen`](swiftui-full-bleed-screen/) | Makes SwiftUI screens paint edge to edge (no white bands at the top or bottom) while keeping buttons a safe distance from the home indicator. |
| [`review-loop`](review-loop/) | Runs three independent review agents on a bounded diff, fixes in-scope findings, and repeats until one round comes back clean. Locks scope and stops at a circuit breaker. |
| [`repo-state-checkpoint`](repo-state-checkpoint/) | Confirms the exact repo, branch, SHA and dirty state before an agent changes code, so it never works in the wrong checkout. |
| [`macos-dev-disk-space-sweep`](macos-dev-disk-space-sweep/) | Read-only audit of what fills a developer Mac (DerivedData, simulators, Docker, caches, agent worktrees), ranked by how safe each is to clear. Deletes nothing without approval. |

## Install

Copy a skill's folder into your skills directory:

```bash
git clone https://github.com/sp-hk2ldn/SKILLS.git
cp -R SKILLS/ios-ota-install ~/.claude/skills/   # Claude Code
cp -R SKILLS/ios-ota-install ~/.codex/skills/    # Codex
```

The agent picks a skill up from its `description` when your request matches, or you can name it.

## Licence

[MIT](LICENSE)
