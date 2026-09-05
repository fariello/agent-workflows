- Id: ld08f1
- Status: open
- Set: durablecapture
- Priority: medium
- Work-Kind: chore
- Summary: retire TODO.md as a work surface: it holds zero items, is scanned but silently dropped by attention, and two deferred specs still gate on it

## Workflow history
- 2026-09-05 created (aw backlog): retire TODO.md as a work surface: it holds zero items, is scanned but silently dropped by attention, and two deferred specs still gate on it

THE SITUATION. `TODO.md` is functionally retired but structurally still load-bearing, which is the
worst of both worlds.

CONTENT: 31 lines, ZERO work items. It is a pointer stub - `TODO.md:3-8` says "Committed and
candidate backlog work now lives in the tracked, attention-visible BACKLOG TREE, not in this file",
and `:14` keeps a `## Notes` section as "durable context (Tier-3: not lifecycle-tracked work)".
`:25-31` records the migration provenance (IPD `crv40v`, 2026-08-13).

DEFECT 1 - SCANNED BUT SILENTLY DISCARDED. `artifact_core.py:158` lists `"TODO.md"` in
`SCAN_ROOTS`, so it IS read. But `_classify_tree` (`attention.py:196-226`) returns `None`
because no `TreePolicy` root covers it, and `attention.py:262-277` `continue`s on
`pol is None`. The `attention.unclassified-tree` drift only fires for paths under `.agents/`,
which a root-level `TODO.md` is not. So anything written there is invisible with NO warning that it
was dropped.

This was predicted verbatim by the controlling spec:
`.aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md:102-103` - "SCAN_ROOTS
already lists TODO.md, but _classify_tree returns None for it ... which is exactly why TODO.md [is
invisible]". Known, documented, still shipped.

DEFECT 2 - TWO DEFERRED SPECS GATE ON IT, AND THOSE GATES ARE DANGLING IN SUBSTANCE.
  * `.aw/records/specs/20260725-0957-01-external-delivery-and-skills.spec.md:6` - `Gate-Ref: TODO.md`
  * `.aw/records/specs/20260726-1239-01-clean-delta-and-tracking-modes.spec.md:6` - `Gate-Ref: TODO.md`

Both are `Gate-Kind: artifact`, so they VALIDATE (the file exists) while resolving to a file whose
items were migrated out from under them in August 2026. Both specs have been untouched since
2026-08-08. They pass in form and mean nothing in substance - a gate pointing at a file that can no
longer contain the thing being waited for.

DEFECT 3 - A LIVE WORKFLOW STILL SURVEYS IT. `.aw/system/workflows/whatnext/whatnext.md` still
lists `TODO.md` as a survey source. Already recorded as finding F-6 in pending IPD `i6015i`
(`:124`): "It also still points at TODO.md as a source the attention view cannot see." Cross-check
that item before touching the workflow so the two fixes do not collide.

WHAT TO DO.
  1. Repoint the two spec gates at real carriers (a backlog item or a plan), or convert them to a
     typed gate that actually expresses what they wait for. Do NOT simply delete the gates: these are
     `deferred` specs and a deferred spec MUST carry a typed `Gate-Kind`/`Gate-Ref` per the specs
     contract. While there, judge whether either spec should still be `deferred` after 4 weeks of
     silence.
  2. Decide `TODO.md`'s fate deliberately, and only then act. EITHER remove it from `SCAN_ROOTS`
     (`artifact_core.py:158`) so it is honestly out of scope, OR give it a `TreePolicy` so that
     anything written there is at least reported as unclassified drift. Silently scanning and
     discarding is the one option to eliminate. Note the `## Notes` section is deliberate Tier-3
     durable context, so DELETING the file is probably wrong; the goal is that nobody can write WORK
     there and have it vanish.
  3. Fix the `whatnext` workflow pointer, coordinating with `i6015i` F-6.
  4. Make the deprecation explicit where agents will read it. AGENTS.md currently never names
     `TODO.md` as deprecated; it only says obliquely "Do NOT keep committed backlog only in prose
     (e.g. TODO.md), where the attention view cannot see it." State it plainly.

WHY THIS MATTERS BEYOND TIDINESS. The maintainer's rule (2026-09-05) is that every known issue must
have a backlog item or a plan. `TODO.md` was historically the third option, and it is a TRAP: it
looks like a place to record work and is guaranteed to lose it. Removing it as an option is a
precondition for the enforcement rule in `jys5dp` being honest.

Current backlog tree for scale: open 46, graduated 4, blocked 3, parked 11, done 59.
