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

At Rivex we put that front door in `mise.toml` at the repo root. `AGENTS.md` documents the same path for humans and automation.

## Try it

From a clean macOS machine with [mise](https://mise.jdx.dev/getting-started.html) installed:

```bash
git clone git@github.com:chefaio-ios/chefaio-app-ios.git
cd chefaio-app-ios
mise trust
mise install
```

**Expected:** mise downloads and activates the pinned tools from `mise.toml`, then runs the `postinstall` hook. You should see install scripts under `Scripts/` execute — project generation, hooks, simulator prep — without running Tuist commands by hand.

Sanity-check the toolchain:

```bash
tuist version
```

**Expected:** a version string matching the pin in `mise.toml` (not whatever happened to be on your PATH yesterday).

Confirm the shared simulator exists:

```bash
xcrun simctl list devices available | grep "Rivex - Agent"
```

**Expected:** a bootable **Rivex - Agent** entry. Tests and local agent runs target that name so nobody improvises `iPhone 16` vs `iPhone 15 Pro` on day one.

If anything fails, start with `AGENTS.md` — it is the source of truth for this flow.

## What `mise install` actually owns

Think in three layers:

**1. Pinned tools (`mise.toml` → `[tools]`)**

mise installs and activates the versions the repo declares — Tuist, linters, and whatever else we have folded into the toolchain. Everyone gets the same binaries; agents included.

**2. Postinstall hook (`mise.toml` → `[hooks]`)**

After tools land, `postinstall` chains our `Scripts/install-*.sh` scripts. In practice that means:

- **Tuist project generation** — dependencies resolved and the `.xcodeproj` / workspace produced from `Project.swift`, not checked in by hand.
- **Git hooks** — format/lint gates wired locally so "forgot to run lint" is less of a personality trait.
- **Rivex - Agent simulator** — a shared destination created if missing, so `mise test` (a follow-up post) does not debate simulator names.

You do not memorize the script order. You run `mise install` once.

**3. Tuist stays behind the façade**

Contributors should not need a mental model of Tuist's install vs generate split on day zero. The install scripts call Tuist; `AGENTS.md` documents the escape hatches if you are debugging project generation.

We consolidated this wiring in a single mise pass (see PR #348 in the app repo history) so onboarding stopped being a checklist pasted into Slack.

## At Rivex we treat onboarding like an API

The contract is small:

| Input | Output |
|-------|--------|
| `mise trust` | Repo config is allowed to run on your machine |
| `mise install` | Pinned tools + postinstall scripts complete |
| Open generated Xcode project | Builds against the same Tuist graph CI sees |

That is deliberately boring. Boring onboarding is how we keep humans and agents on the same rails when the product itself is about reliable automation.

## Takeaways

- **One entry point beats a wiki.** If setup is not in version control, it will drift.
- **Pin tools, then automate side effects.** mise handles versions; `Scripts/install-*.sh` handles everything that used to be "oh right, I always run that."
- **Hide Tuist ceremony.** Generate on install; expose Tuist only when someone is actually changing project structure.

Next up in this series: why we wrap build and test behind `mise build` and `mise test` instead of raw `xcodebuild` flags — same philosophy, different layer.

---

If reproducible dev environments matter to you, [try Rivex](https://apps.apple.com/app/rivex/id6752362984) — we built the app the same way we built the repo.
