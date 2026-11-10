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

### Apple Ads

These work with [searchads-cli](https://github.com/sp-hk2ldn/searchads-cli), a Go CLI for the
Apple Ads Platform API (`brew install sp-hk2ldn/tap/searchads`). The guidance is useful on its
own too.

They were distilled from Apple's official Apple Ads Certification (formerly Apple Search Ads
Certification) course materials and exam, then turned into working rules an agent can apply.

| Skill | What it does |
| --- | --- |
| [`apple-ads-certification-core`](apple-ads-certification-core/) | Campaign structure (brand, category, competitor, discovery), keyword match types, Search Match and how to read performance. |
| [`apple-ads-discovery-promotion`](apple-ads-discovery-promotion/) | The weekly discovery, promotion and isolation loop: turn search terms that convert into exact-match keywords and add negatives so campaigns don't compete with each other. |
| [`apple-ads-placements-creative`](apple-ads-placements-creative/) | Ad placements (Today tab, Search tab, search results, product pages), custom product pages and ad variations. |

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
