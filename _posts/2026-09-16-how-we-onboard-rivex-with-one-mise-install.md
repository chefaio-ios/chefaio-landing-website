---
title: How we onboard Rivex with one `mise install`
date: '2026-09-16'
author: Rivex Engineering
description: Clone the Rivex iOS repo, run mise install once, and get pinned tools,
  a generated Tuist project, git hooks, and a shared agent simulator — no brew wiki
  required.
notion_id: 3e122cfb-2af8-8163-957e-cf1de866c5af
canonical: https://rivexapp.com/blog/2026/09/16/how-we-onboard-rivex-with-one-mise-install/
tags:
- mise
- ios
---

Onboarding a new iOS engineer — or spinning up a fresh machine for an AI coding agent — should not take an afternoon of Slack archaeology. When every clone drifts on tool versions and manual setup steps, you pay for it in slow first builds, flaky local tests, and "works on my Mac" threads that never quite close.

This post is about the choices we made to fix that on the Rivex iOS codebase: what we tried first, why we landed on [mise](https://mise.jdx.dev/) as the single front door, and what still bites us. Not a product pitch — a walkthrough of trade-offs you can steal.

If you have ever joined a Tuist project where every machine had a different Tuist version — and nobody could agree which one was "right" — you know why we bothered.

## The scavenger hunt we inherited

Fresh clones used to mean a scavenger hunt:

- Which Homebrew formula pins Tuist — and does it match CI?
- Did you run `tuist install` before or after `tuist generate`?
- Which simulator name do the tests expect — and is it even installed?

None of that is hard. All of it is **friction that compounds** when a human and an agent should share the same machine state. We wanted clone → build with no tribal knowledge.

## What we tried first

**Homebrew-only.** Fine for installing a tool globally. Weak for "this project needs these versions, activated in this directory, with side effects in a fixed order." Tuist on brew might not match the Tuist your CI job runs. SwiftLint might not match either.

Manual Tuist steps in a README. Worse in a different way: easy to skip, hard to notice when skipped, invisible in code review. Someone always runs `tuist generate` before `tuist install` once, wastes twenty minutes, and posts a confused emoji in Slack.

We needed one command that pins tools and runs the post-clone ceremony — in the right order, every time.

## Why mise became the front door

The dependency order mattered to us:

1. **Pin tools first** — Tuist, linters, formatters, anything else the repo expects.
2. **Then run side effects** — project generation, hooks, simulator setup, agent bootstraps.

[Tuist recommends mise](https://tuist.dev/en/docs/guides/install-tuist) for exactly this split: one `mise.toml` declares versions, one `mise install` activates them. At Rivex we put that file at the repo root. Day-to-day commands like `mise build`, `mise test`, and `tuist generate` are documented for contributors once they are set up — but they are not the clone checklist.

And mise is not just a Tuist installer. That is the part teams miss when they stop at pinning Tuist alone.

## Try it

From a clean macOS machine with [mise installed](https://mise.jdx.dev/getting-started.html), in your project directory:

```bash
mise trust
mise install
```

Expected: mise downloads and activates the pinned tools from `mise.toml`, then runs the `postinstall` hook — Tuist dependency install, project generation, git hooks, a shared simulator, and a few agent-oriented bootstraps. You should not need to run any of that by hand.

Sanity-check the toolchain — Tuist and the linters that used to drift on their own:

```bash
tuist version
swiftlint version
swiftformat --version
```

Expected: version strings matching the pins in `mise.toml`, not whatever Homebrew happened to serve last week.

Confirm the generated workspace exists:

```bash
ls *.xcworkspace
```

Expected: a generated Xcode workspace on disk. Tuist output is gitignored, so a fresh clone will not have one until `mise install` finishes. Open it in Xcode and you are ready to build.

## What `mise install` actually does

### Layer 1 — pinned tools (`mise.toml` → `[tools]`)

A typical iOS `mise.toml` might look like this (illustrative):

```toml
[settings]
pin = true

[tools]
tuist = "4.48.2"
swiftlint = "0.57.0"
swiftformat = "0.54.5"
```

SwiftLint and SwiftFormat are the easy wins — same pin on your laptop, your teammate's machine, and CI. No more "works locally, fails in the pipeline because CI picked up a newer SwiftLint rule." Everyone gets the same binaries; agents included.

### Layer 2 — postinstall hook (`mise.toml` → `[hooks]`)

After tools land, `postinstall` runs in a fixed order:

1. `tuist install` — resolve SPM dependencies
2. `tuist generate` — produce the generated Xcode workspace from `Project.swift`
3. Bootstrap git hooks — format/lint gates locally
4. Install a shared simulator — one consistent destination for local runs and tests
5. Set up agent IDE permissions — the local access an AI coding agent needs to read files, run terminal commands, and work inside your editor without you clicking through prompts every session
6. Bootstrap shared env — API keys and config agents expect locally

Tuist runs in steps 1–2 directly in the hook. Everything after that handles the environment around the Xcode project — not project generation itself.

You do not memorize the order. You run `mise install` once.

## What bit us

A few things production (and impatient teammates) taught us that the design alone did not:

- Order matters. `tuist install` before `tuist generate` is not negotiable. We had to encode that in postinstall because READMEs do not survive contact with Monday morning.
- Pinning only Tuist is not enough. SwiftLint drift caused more "CI is broken but I cannot reproduce it" tickets than Tuist version skew ever did. Bundling linters in `mise.toml` was cheap insurance.
- **Manual steps do not scale to agents.** A human might forgive a five-step checklist. An agent will not — it needs the same deterministic entry point every time.
- **Postinstall is not free.** It adds time to every fresh clone. We accepted that trade-off over debugging mismatched environments.

## Principles we'd steal

- `mise trust` → repo config is allowed to run on your machine
- `mise install` → pinned tools + postinstall complete
- Open the generated Xcode workspace → builds against the same Tuist graph the team expects
- **One entry point beats a wiki.** If setup is not in version control, it will drift.
- One owner for pin bumps. When someone changes a version in `mise.toml`, it goes through normal PR review; everyone else re-runs `mise install`.
- **Pin tools, then automate side effects.** mise handles versions — Tuist, SwiftLint, SwiftFormat, and friends — postinstall handles the rest.
- Hide Tuist ceremony on day zero. Reach for `tuist generate` directly only when you are changing project structure.

Next up in this series: why we wrap build and test behind `mise build` and `mise test` instead of raw `xcodebuild` flags — same philosophy, different layer.

If you like how we run agent-ready iOS setups, [try Rivex on the App Store](https://apps.apple.com/app/rivex/id6752362984) — we built the product with the same discipline we use to build the repo.
