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

That is the onboarding bar we set for the Rivex iOS app. If you have ever joined a Tuist project where every machine had a different Tuist version — and nobody could agree which one was "right" — you know why we bothered.

## The problem we were tired of

Fresh clones used to mean a scavenger hunt:

- Which Homebrew formula pins Tuist — and does it match CI?
- Did you run `tuist install` before or after `tuist generate`?
- Which simulator name do the tests expect — and is it even installed?

None of that is hard. All of it is **friction that compounds** when a human and an agent should share the same machine state. We wanted clone → build with no tribal knowledge.

## Why brew-only and manual Tuist did not stick

Homebrew is great for "give me a tool." It is weaker for "give me **this project's** tool graph, activated in **this directory**, with **post-clone side effects** run in order."

Manual Tuist steps made things worse: they were easy to skip, hard to notice when skipped, and invisible in code review. Tuist belongs behind a single front door — not as a separate onboarding chapter.

At Rivex we put that front door in `mise.toml` at the repo root. [Tuist recommends mise](https://tuist.dev/en/docs/guides/install-tuist) as the tool manager for exactly this reason — one file pins versions, one command installs them. Day-to-day commands like `mise build`, `mise test`, and `tuist generate` are documented for contributors once they are set up, but they are not the clone checklist.

## Try it

From a clean macOS machine with [mise](https://mise.jdx.dev/getting-started.html) installed, in your project directory:

```bash
mise trust
mise install
```

**Expected:** mise downloads and activates the pinned tools from `mise.toml`, then runs the `postinstall` hook — Tuist dependency install, project generation, git hooks, a shared simulator, and a few agent-oriented bootstraps. You should not need to run any of that by hand.

Sanity-check the toolchain — Tuist and the linters that used to drift on their own:

```bash
tuist version
swiftlint version
swiftformat --version
```

**Expected:** version strings matching the pins in `mise.toml`, not whatever Homebrew happened to serve last week.

Confirm the generated workspace exists:

```bash
ls *.xcworkspace
```

**Expected:** a generated Xcode workspace on disk. Tuist output is gitignored, so a fresh clone will not have one until `mise install` finishes. Open it in Xcode and you are ready to build.

## What `mise install` actually owns

Think in two layers:

**1. Pinned tools (`mise.toml` → `[tools]`)**

mise installs and activates every version the repo declares — not just Tuist. A typical iOS `mise.toml` might look like this (illustrative):

```toml
[settings]
pin = true

[tools]
tuist = "4.48.2"
swiftlint = "0.57.0"
swiftformat = "0.54.5"
```

That is the whole point of starting from Tuist with mise: you get Tuist *and* the satellite tools in one install. SwiftLint and SwiftFormat are the easy wins — same pin on your laptop, your teammate's machine, and CI. No more "works locally, fails in the pipeline because CI picked up a newer SwiftLint rule."

Everyone gets the same binaries; agents included.

**2. Postinstall hook (`mise.toml` → `[hooks]`)**

After tools land, `postinstall` runs in a fixed order:

1. `tuist install` — resolve SPM dependencies
2. `tuist generate` — produce the generated Xcode workspace from `Project.swift`
3. Bootstrap git hooks — format/lint gates locally
4. Install a shared simulator — one consistent destination for local runs and tests
5. Set up agent IDE permissions
6. Bootstrap shared env — API keys and config agents expect locally

Tuist runs in steps 1–2 directly in the hook. Everything after that handles the environment *around* the Xcode project — hooks, simulator, agent tooling — not project generation itself.

You do not memorize the order. You run `mise install` once.

## At Rivex we treat onboarding like an API

The contract is small:

| Input | Output |
|-------|--------|
| `mise trust` | Repo config is allowed to run on your machine |
| `mise install` | Pinned tools + postinstall complete |
| Open the generated Xcode workspace | Builds against the same Tuist graph the team expects |

That is deliberately boring. Boring onboarding is how we keep humans and agents on the same rails when the product itself is about reliable automation. Once we moved setup into `mise.toml`, onboarding stopped being a checklist pasted into Slack.

## Takeaways

- **One entry point beats a wiki.** If setup is not in version control, it will drift.
- **Pin tools, then automate side effects.** mise handles versions — Tuist, SwiftLint, SwiftFormat, and friends — postinstall handles the rest.
- **Hide Tuist ceremony on day zero.** `mise install` runs install and generate; reach for `tuist generate` directly only when you are changing project structure.

Next up in this series: why we wrap build and test behind `mise build` and `mise test` instead of raw `xcodebuild` flags — same philosophy, different layer.

---

If reproducible dev environments matter to you, [try Rivex](https://apps.apple.com/app/rivex/id6752362984) — we built the app the same way we built the repo.
