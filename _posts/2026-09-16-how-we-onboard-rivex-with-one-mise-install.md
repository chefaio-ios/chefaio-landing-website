---
title: "How we onboard Rivex with one `mise install`"
date: 2026-09-16
author: "Rivex Engineering"
description: >-
  Clone the Rivex iOS repo, run mise install once, and get pinned tools, a
  generated Tuist project, git hooks, and a shared agent simulator — no brew
  wiki required.
canonical: https://rivexapp.com/blog/2026/09/16/how-we-onboard-rivex-with-one-mise-install/
tags:
  - ios
  - mise
  - tuist
  - onboarding
categories:
  - engineering
---

Clone the repo. Run one command. Open Xcode.

That is the onboarding bar we set for the Rivex iOS app. If you have ever joined a Tuist project where Tuist itself was "whoever had 4.x last week," you know why we bothered.

## The problem we were tired of

Fresh clones used to mean a scavenger hunt:

- Which Homebrew formula pins Tuist — and does it match CI?
- Did you run `tuist install` before or after `tuist generate`?
- Which simulator name do the tests expect — and is it even installed?

None of that is hard. All of it is **friction that compounds** when a human and an agent should share the same machine state. We wanted clone → build with no tribal knowledge.

## Why brew-only and manual Tuist did not stick

Homebrew is great for "give me a tool." It is weaker for "give me **this project's** tool graph, activated in **this directory**, with **post-clone side effects** run in order."

Manual Tuist steps made things worse: they were easy to skip, hard to notice when skipped, and invisible in code review. Tuist belongs behind a single front door — not as a separate onboarding chapter.

At Rivex we put that front door in `mise.toml` at the repo root. Day-to-day commands like `mise build`, `mise test`, and `tuist generate` live in `AGENTS.md` — useful once you are set up, but not the clone checklist.

## Try it

From a clean macOS machine with [mise](https://mise.jdx.dev/getting-started.html) installed:

```bash
git clone git@github.com:chefaio-ios/chefaio-app-ios.git
cd chefaio-app-ios
mise trust
mise install
```

**Expected:** mise downloads and activates pinned tools (Tuist `4.174.2` among them), then runs the `postinstall` hook: `tuist install`, `tuist generate`, then four `Scripts/install-*.sh` helpers — without you running any of that by hand.

Sanity-check the toolchain:

```bash
tuist version
```

**Expected:** `4.174.2` — matching `mise.toml`, not whatever happened to be on your PATH yesterday.

Confirm the workspace and simulator:

```bash
ls ChefAIO.xcworkspace
xcrun simctl list devices available | grep "Rivex - Agent"
```

**Expected:** `ChefAIO.xcworkspace` on disk (generated projects are gitignored; you will not find them in a fresh clone until `mise install` runs). A bootable **Rivex - Agent** simulator entry. Tests and local agent runs target that name so nobody improvises `iPhone 16` vs `iPhone 15 Pro` on day one.

## What `mise install` actually owns

Think in three layers:

**1. Pinned tools (`mise.toml` → `[tools]`)**

mise installs and activates the versions the repo declares — Tuist `4.174.2`, linters, and the rest of the toolchain. Everyone gets the same binaries; agents included.

**2. Postinstall hook (`mise.toml` → `[hooks]`)**

After tools land, `postinstall` runs in a fixed order:

1. `tuist install` — resolve SPM dependencies
2. `tuist generate` — produce `ChefAIO.xcworkspace` from `Project.swift`
3. `Scripts/install-githooks.sh` — format/lint gates locally
4. `Scripts/install-agent-simulator.sh` — create **Rivex - Agent** if missing
5. `Scripts/install-cursor-permissions.sh` — agent IDE permissions
6. `Scripts/install-openrouter-env.sh` — local env for agent API keys

Tuist runs in steps 1–2 directly in the hook. The install scripts handle everything *around* the Xcode project — hooks, simulator, agent tooling — not project generation itself.

**3. Same path in CI**

`ci_scripts/ci_post_clone.sh` runs `mise install` and Tuist on Xcode Cloud too, so cloud builds do not drift from your laptop.

You do not memorize the order. You run `mise install` once.

## At Rivex we treat onboarding like an API

The contract is small:

| Input | Output |
|-------|--------|
| `mise trust` | Repo config is allowed to run on your machine |
| `mise install` | Pinned tools + postinstall complete |
| Open `ChefAIO.xcworkspace` | Builds against the same Tuist graph CI sees |

That is deliberately boring. Boring onboarding is how we keep humans and agents on the same rails when the product itself is about reliable automation.

We wired this in commit `f93fed1d` ("[Misc] Use mise and simulator setup") — onboarding stopped being a checklist pasted into Slack.

## Takeaways

- **One entry point beats a wiki.** If setup is not in version control, it will drift.
- **Pin tools, then automate side effects.** mise handles versions; postinstall handles Tuist + the install scripts.
- **Hide Tuist ceremony on day zero.** `mise install` runs install and generate; reach for `tuist generate` directly only when you are changing project structure.

Next up in this series: why we wrap build and test behind `mise build` and `mise test` instead of raw `xcodebuild` flags — same philosophy, different layer.

---

If reproducible dev environments matter to you, [try Rivex](https://apps.apple.com/app/rivex/id6752362984) — we built the app the same way we built the repo.
