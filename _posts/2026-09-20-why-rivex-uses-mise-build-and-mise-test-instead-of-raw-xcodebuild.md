---
title: Why Rivex uses `mise build` and `mise test` instead of raw `xcodebuild`
date: '2026-09-20'
author: Rivex Engineering
description: How Rivex turns xcodebuild flag soup into stable mise build and mise
  test verbs for humans and agents — plus a short look at Promptfoo on the same rails.
notion_id: 3e122cfb-2af8-8154-8bb6-e36812d77ef9
canonical: https://rivexapp.com/blog/2026/09/20/why-rivex-uses-mise-build-and-mise-test-instead-of-raw-xcodebuild/
tags:
- mise
- ios
- dx
---

In [the last post](https://rivexapp.com/blog/2026/09/16/how-we-onboard-rivex-with-one-mise-install/), we pinned the Rivex iOS toolchain behind one `mise install`. That fixed "which Tuist / SwiftLint am I on?" It did not fix the next failure mode: five engineers (and one coding agent) each inventing a slightly different `xcodebuild` line.

This post is about the choices we made to turn build and test into stable mise verbs — what we tried first, why wrappers won, what still bites us, and a short look at running Promptfoo the same way. Steal the pattern; skip the product pitch.

## The flag soup we inherited

Ask three people how they build the app and you get three command lines. One uses `-project`. Another uses the generated workspace. Someone hard-codes a simulator name that does not exist on the agent's Mac. Derived Data lands in three different folders. Signing flags that work in Xcode break headless runs. Logs dump raw `xcodebuild` noise nobody reads.

None of that is exotic. All of it drifts. Humans forgive it with muscle memory. Agents do not — they invent destinations from training data and confidently fail.

We wanted one allowlisted vocabulary: `mise build` and `mise test`.

## What we tried first

**Document the golden xcodebuild line.** Docs rot. The day someone adds a scheme or moves Derived Data, half the team is still on the wiki version. Agents ignore the wiki and invent flags.

**Shell aliases in each person's profile.** Great until a new hire (or a fresh agent sandbox) has none of them. Not reviewable. Not versioned with the repo.

**"Just open Xcode and hit Cmd-B."** Fine for interactive humans. Useless for agents, headless smoke, and "same command in CI-like runs."

We needed verbs in the repo — next to `mise.toml` — that encode the contract once.

## Why mise tasks became the daily verbs

Dependency order again:

1. **Pin tools first** (post #1) — Tuist, linters, formatters, beautifiers.
2. **Then pin the invocation** — build and test call thin wrappers that freeze the knobs humans argue about.

At Rivex, `mise build` and `mise test` are mise tasks that run shared wrappers. Publicly, think of those wrappers as owning a small fixed set of decisions:

- Prefer the generated workspace over ad-hoc `-project` guesses
- Default scheme when you do not pass one
- Stable Derived Data location so caches are not mystery meat
- Shared simulator destination (a named environment every machine prepares at install time — no UUID archaeology in the post)
- Signing off for headless builds so local agent runs do not hang on keychain prompts
- Log beautifier from the pinned toolchain so failures are scannable

The point is not "never touch `xcodebuild`." The point is: if you are building Rivex (or cloning this pattern), you should not invent a new flag soup for the happy path.

## Try it

After `mise install` from post #1, in your project directory:

```bash
mise build
mise test
```

**Expected:** a successful compile (and tests) using the repo's defaults — same scheme/workspace/destination story your teammates and agents get — without you pasting a private wiki command.

Optional shape if your wrappers accept a scheme argument:

```bash
mise build MyScheme
```

**Expected:** same contract, named scheme.

Illustrative `mise.toml` task shape (scrubbed):

```toml
[tasks.build]
run = "scripts/build.sh"

[tasks.test]
run = "scripts/test.sh"
```

Use whatever script names fit your repo. Keep the idea: mise is the front door; the script freezes knobs.

## The quiet hero: a shared simulator destination

Most "agent cannot run tests" threads are destination improvisation. If install prepares one shared simulator name and build/test always target it, humans and agents stop guessing OS runtimes. We treat that destination as part of the onboarding contract from post #1, not as a flag you reinvent per PR.

## Honest local vs Xcode Cloud note

Xcode Cloud is a different runner. In our setup it uses mise for **toolchain and generate parity** with local machines. That is not the same claim as "Cloud always executes the identical local `mise build` script." This post is about standardizing the **local and agent** vocabulary so day-to-day work stops drifting. Cloud parity is a follow-up story, not a freebie of wrapping xcodebuild.

## What bit us

- **Wrappers without pins are theater.** If SwiftLint or xcbeautify still come from random brew, you only moved the drift.
- **Agents will call raw xcodebuild unless you teach them not to.** Document the allowlist (`mise build` / `mise test`) in contributor and agent docs. Permissions and skills should prefer the verbs.
- **Run intent is not build intent.** "Boot sim, install, launch" is a third verb if you need it. Stuffing launch into `mise build` confuses everyone.
- **Cloud honesty matters.** Over-claiming "CI runs mise test" when Cloud only does install+generate earns distrust fast.

## Same rails for prompt smoke: Promptfoo via mise

Once build/test are mise tasks, Promptfoo is the same pattern for prompts: pin Node + Promptfoo in `mise.toml`, add a task that runs a harness folder (config + cases + asserts). Production prompts stay single-source conceptually (copy or symlink into the harness — do not scatter forever-copies). Default to a local provider; optional cloud provider via flags and a local env API key.

Scrubbed shapes:

```bash
mise prompt_eval hello-world
mise prompt_eval my-harness -n 3
```

Treat this as a **manual smoke / regression aid**, not a hard CI gate, unless your team deliberately promotes it. The win is the same as build: one verb, pinned tools, less improvisation.

## Principles we'd steal

- **Pin tools, then pin verbs.** `mise install` without `mise build` only solves half the drift.
- **Encode knobs in the repo, not in muscle memory.** Workspace vs project, Derived Data, destination, signing for headless — pick once.
- **Allowlist what agents may run.** If raw `xcodebuild` is still the documented path, agents will take it.
- **Be honest about Cloud.** Toolchain parity ≠ identical build scripts.
- **Reuse the pattern for evals.** Promptfoo-via-mise is just another task on the same rails.

Next up: either collapsing lint behind one `mise lint`, or Mac ↔ Xcode Cloud parity — same philosophy, different layer.

If you like how we design agent-operable iOS contracts, [try Rivex on the App Store](https://apps.apple.com/app/rivex/id6752362984) — we build the product with the same discipline we use to build the repo.

