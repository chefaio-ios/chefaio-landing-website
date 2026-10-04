---
title: Swift Predicates crash after archive
date: '2026-10-03'
author: Rivex Engineering
description: 'A generic SwiftData #Predicate that compares id crashes when the archived
  app creates it. Debug does not. The fix builds the comparison from a concrete id
  key path.'
notion_id: 3ef22cfb-2af8-8199-93e0-c747c1467491
canonical: https://rivexapp.com/blog/2026/10/03/swift-predicates-crash-after-archive/
tags:
- ios
---

A shared lookup knew each stored model only as a generic type. The protocol on that type required an `id`. The lookup built its fetch with the predicate macro inside that generic, comparing the model's `id` to the id you asked for.

That line crashed when an archived app reached predicate creation. A direct build did not show it. A debug run did not show it either.

This post covers that crash, what we think causes the archive-only failure, and the change that removed the generic macro. It is not a product behavior.

## What causes the crash

The lookup is generic over the model. The protocol is enough for the compiler to accept this shape:

```swift
protocol StoredItem: PersistentModel {
    var id: UUID { get }
}

func existing<Model: StoredItem>(
    _ context: ModelContext,
    id: UUID
) throws -> Model? {
    let predicate = #Predicate<Model> { $0.id == id }
    let descriptor = FetchDescriptor<Model>(predicate: predicate)
    return try context.fetch(descriptor).first
}
```

The names above are illustrative. The real code used the same shape: one generic parameter, a protocol that only required `id`, and `#Predicate` comparing that `id`.

Creating that predicate is the line that crashed. The archived process reached it and trapped. The same function, built and run for debugging, did not.

A direct build here means the normal debug build you run from Xcode. Archive means the archived app, then a run of that archive. Those are different binaries. The debug one did not hit this crash.

## What we think is going on

This section is our account of the failure, not a measurement from the binary.

The generic predicate is fine while debugging. After archive, creating that predicate crashes. We believe the archived build strips the generic function, so the archived app hits a bad access when it tries to build the predicate. We have not shown a missing symbol, and we are not claiming a specific optimizer pass.

Public reports are related. They are not this crash, and we are not treating debug-versus-release as the same fact as archive-then-run.

- [Lost hours integrating SwiftData](https://clive819.github.io/posts/lost-hours-integrating-swiftdata/) (Clive Liu, 2025-11-27). A generic `ModelContext.fetch` with `#Predicate { model.id == id }` was fine in debug and crashed immediately in release. The crash was `EXC_BREAKPOINT` in key-path lookup (`PersistentModel.graph_keyPathToString` / `Schema.KeyPathCache`). The author's fix was to stop the generic predicate helper and create the fetch descriptor at the call site.
- [SwiftData runtime crash using Predicate macro with a protocol-based generic model](https://stackoverflow.com/questions/79717995/swiftdata-runtime-crash-using-predicate-macro-with-a-protocol-based-generic-model) (2025-07-29). A generic `#Predicate` on a protocol property crashes with `EXC_BREAKPOINT`. The fix described there is to store a key path on the protocol and build the predicate with `PredicateExpressions.build_KeyPath`. That thread does not discuss debug versus release.
- [SwiftData predicate does not handle protocol witness](https://forums.swift.org/t/swiftdata-predicate-does-not-handle-protocol-witness/68256). A generic `#Predicate` crashes. A later note on that thread says extending `PersistentModel` the same way crashes on Release only.
- [Xcode Previews, Predicate, and KeyPath issues](https://forums.swift.org/t/xcode-previews-predicate-and-keypath-issues/80782). Generics and protocols make `PredicateExpressions` key paths miss the schema. The author says device and simulator were fine, and guesses those runs were debug rather than release.

None of those pages describe an archiver stripping a generic function, then a bad access only after archive. Use them as neighboring reports.

## What we tried in between

Before the key-path change, we tried nesting evaluation inside the macro. The idea was to evaluate a small predicate on the id value instead of writing the comparison on the generic model:

```swift
let predicate = #Predicate<Model> { model in
    #Predicate<UUID> { $0 == id }.evaluate(model.id)
}
```

That version did not hold. It is not the line that crashed, and it is not the current lookup. We are not claiming a public write-up of this attempt.

## The fix

Stop using the predicate macro on the generic model.

Each concrete model supplies a key path for its `id`. The shared lookup builds the equality from that key path. `PredicateExpressions` is enough for the public shape:

```swift
protocol StoredItem: PersistentModel {
    static var identifier: KeyPath<Self, UUID> { get }
}

extension StoredItem {
    static func idEquals(_ id: UUID) -> Predicate<Self> {
        let idPath = identifier
        return Predicate<Self>({ input in
            PredicateExpressions.build_Equal(
                lhs: PredicateExpressions.build_KeyPath(
                    root: input,
                    keyPath: idPath
                ),
                rhs: PredicateExpressions.build_Arg(id)
            )
        })
    }
}
```

A concrete model then sets `identifier` to `\.id` on its own type, not on the protocol. The generic lookup calls that helper and puts the result on `FetchDescriptor`. It does not call `#Predicate` on the generic model.

The property name `identifier` above is illustrative. The point is the split: the protocol no longer only offers `id` as a value the macro can see. The concrete type offers a key path, and the predicate is built from that key path.

## Post-mortem

Test the TestFlight build directly. A debug build is not a stand-in for it.

Archiving changes the code enough that this crash stays invisible in Debug. The same lookup created its predicate in a debug run and crashed when the archived app created it. If the only run you trust is the debug one, you will ship that crash.

## What we would repeat

- Do not write `#Predicate` against a generic model whose protocol only exposes `id`.
- If several models share one lookup, take a key path from the concrete type and build the comparison with `PredicateExpressions`.
- Treat archive-then-run as its own check. A debug run not crashing does not mean the archived app will create the same predicate.
- Label an optimizer or archiver explanation as a belief unless you have a binary measurement. We do not have that measurement for the strip.
