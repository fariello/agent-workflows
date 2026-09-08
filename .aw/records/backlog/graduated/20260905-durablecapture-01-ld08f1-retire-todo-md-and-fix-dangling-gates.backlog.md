- Id: ld08f1
- Status: graduated
- Set: durablecapture
- Priority: medium
- Work-Kind: chore
- Summary: retire TODO.md as a work surface: it holds zero items, is scanned but silently dropped by attention, and two deferred specs still gate on it

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan diof9n (durablecapture-03), carrying all four WHAT TO DO points. See the CORRECTION AND RE-MEASUREMENT section appended. All three defects confirmed live. TWO CORRECTIONS, each of which changes the work. FIRST, this item says F-6 is in 'pending IPD i6015i' and to avoid a collision; i6015i is EXECUTED, it DEFERRED the whatnext rewiring, and its own contract forbade its executor from touching that file, so there is no collision and the work is unowned. SECOND, the AGENTS.md sentence to strengthen lives at agent_workflows/engine.py:1151 inside the managed block engine.py installs into every repo, so editing AGENTS.md directly would be overwritten and never reach a managed target; the fix must edit the generator and regenerate. ALSO UNDERSTATED: TODO.md appears NINE times in whatnext.md and most are WRITE instructions, not a survey pointer, so this is redirecting a write target rather than swapping a pointer. Noted that DECISIONS.md, README.md and ARCHITECTURE.md are in the identical scanned-then-dropped state, so an invariant test must encode their exemption explicitly. Hazard recorded: sibling v7u6vm's plan m867ox also edits SCAN_ROOTS.
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

## CORRECTION AND RE-MEASUREMENT, 2026-09-08 at HEAD a2e0438a during graduation

ALL THREE DEFECTS RE-VERIFIED LIVE by importing the modules and reading the files, not by trusting
this item. Two corrections and one understatement.

DEFECT 1 CONFIRMED EXACTLY, including the mechanism that makes it silent. Measured:

    _classify_tree("TODO.md")         -> None   (silently dropped)
    _classify_tree("DECISIONS.md")    -> None   (silently dropped)
    _classify_tree("README.md")       -> None   (silently dropped)
    _classify_tree("ARCHITECTURE.md") -> None   (silently dropped)

`attention.scan`'s `pol is None` branch appends `attention.unclassified-tree` drift ONLY when the path
starts with `.agents/`, so a repository-root file is `continue`d with no violation recorded. The
controlling spec's verbatim prediction at
`.aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md:102-103` re-read and
confirmed.

DEFECT 2 CONFIRMED: both specs still carry `Gate-Kind: artifact` / `Gate-Ref: TODO.md` at `:5-6`, both
still read `- Status: deferred`, dated 2026-07-25 and 2026-07-26.

DEFECT 3 IS UNDERSTATED BY THIS ITEM, and the correction changes the size of the work. `TODO.md`
appears NINE times in `.aw/system/workflows/whatnext/whatnext.md`, and most are not a "survey source"
pointer at all: they instruct the workflow to WRITE findings INTO `TODO.md` (`:11`, `:119-121`, `:125`,
`:145`, `:150`), plus two untrusted-content rules about what may be written there (`:27`, `:133`).
So this is redirecting a WRITE TARGET, which is a behavior change to an agent-facing workflow, not a
one-line pointer swap. The write path is also the actual defect: a workflow that appends a finding to
`TODO.md` writes it exactly where the attention view cannot see it.

CORRECTION 1, AND IT INVERTS THIS ITEM'S COORDINATION INSTRUCTION. This item says finding F-6 is
recorded in "pending IPD `i6015i`" and to "cross-check that item before touching the workflow so the
two fixes do not collide". `i6015i` is EXECUTED, not pending, and it did NOT fix the pointer: it
DEFERRED the rewiring ("The workflow would benefit (F-6), but it is a prose workflow with its own
review path, and changing an agent-facing workflow is a separate concern") and its own execution
contract forbade its executor from touching the file ("Do NOT edit spec 25kzda ... or the `whatnext`
workflow"). So there is no collision to avoid and the work is unowned.

CORRECTION 2, AND WITHOUT IT THE FIX WOULD BE SILENTLY REVERTED. This item says "AGENTS.md currently
never names TODO.md as deprecated". Right about the symptom, wrong about where to fix it: the oblique
sentence it quotes lives at `agent_workflows/engine.py:1151`, inside the managed block that
`engine.py` INSTALLS into every repository. Editing `AGENTS.md` directly would be overwritten on the
next install and would never reach any managed target repo. The fix must edit the generator and
regenerate.

ONE NEW HAZARD, not present when this item was written: sibling item `v7u6vm` was graduated in the
same pass, and its plan `m867ox` ADDS a releases entry to `artifact_core.SCAN_ROOTS` while this item's
plan may REMOVE the `TODO.md` entry from the same tuple. The two plans must not execute concurrently
against it; each declares the other in its fence.

ONE THING THIS ITEM DOES NOT SAY that shapes the invariant test: `DECISIONS.md`, `README.md` and
`ARCHITECTURE.md` are in the IDENTICAL scanned-then-dropped state. So an invariant test asserting "no
SCAN_ROOTS entry classifies to None" will implicate all four, and their exemption (they are
documentation, not work surfaces, and their scan membership serves the reference tools) must be
encoded explicitly rather than special-cased quietly. Plan `diof9n` OQ-03 owns that decision.

Backlog tree for scale, updated from this item's figures: open 37, graduated 38, blocked 5, parked 12,
done 66.

GRADUATED to plan `diof9n` (durablecapture-03), which carries all four of this item's WHAT TO DO
points: the scan-fate decision, the two spec gates, the workflow write-target redirect, and the
managed-block deprecation statement.
