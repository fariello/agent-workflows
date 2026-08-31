- Id: sd2wz5
- Status: open
- Set: sd2wz5
- Priority: medium
- Work-Kind: chore
- Summary: spec 25kzda's corrected infrastructure paragraph has itself gone stale: From-Spec shipped but is still listed as net-new

## Workflow history
- 2026-08-31 created (aw backlog): spec 25kzda's corrected infrastructure paragraph has itself gone stale: From-Spec shipped but is still listed as net-new

FOUND by auditing every live spec for stale "does not exist yet" claims (the tmp/human-todo-asap.md item 2 audit). Result of that audit, so it is not repeated: only ONE spec carries such claims at all.

## The audit, and its scope

Searched all 24 specs for stale-existence claims (`does not exist`, `not yet built`, `must be built`, `net-new`, `nonexistent`, `no such verb`, etc.). Only the 5 specs whose status can still MISLEAD a graduating Set matter (3 `approved`, 1 `implementing`, 2 `deferred`); an `implemented` or `superseded` spec cannot mislead a new plan the same way.

Hits: `prompt-purity-lint` 0, `research-lifecycle-reliability` 0, `c4gd2h runner-lifecycle-graceful-quit` 0, `external-delivery-and-skills` 0, `clean-delta-and-tracking-modes` 0, and `25kzda aw-run-deterministic-run-and-verify` **4**.

So the false-premise problem that destroyed the `detrun` Set is confined to `25kzda`. No other spec family inherited it. That half of the audit is CLOSED.

## The remaining defect: the correction is now itself partly stale

`25kzda` was corrected at `a59f2c5` on 2026-08-30 to stop claiming the dependency infrastructure was unbuilt. That corrected paragraph (`:22-31`) now lists what is "STILL NET-NEW and to be built", and one of its five items has since shipped:

  1. **`From-Spec` (absent from `ipd_schema.META_RECOGNIZED`)** - **STALE**. Verified live: `META_FROM_SPEC in META_RECOGNIZED` is `True`. Shipped in `8c437188` (merged `b0eb74e6`), together with `check.from-spec-dangling`. This is the exact residue of retired plan `bmh754`, whose retirement banner records it as landed.
  2. `AW-Run:`/`AW-Item:` commit trailers - claim HOLDS (0 hits; owned by pending `runtrail-01` `m73aet`).
  3. prompt `Run contract` block - claim HOLDS (0 hits).
  4. per-host capability descriptor - claim is now MISLEADING rather than false. `host_sandbox_profile.py` ships a typed, probed capability contract (from `1o4eif`), and pending `hostcap-01` (`mjx7ne`) is scoped to EXTEND it, not create it. The runner-safety half (commit gateway, deny-push, fresh verifier session) genuinely does not exist, so the honest wording is "partially shipped; extend, do not create".
  5. `aw hooks install` (no such verb today) - claim HOLDS (verb absent).

## Why this matters rather than being pedantry

This is the SAME failure mode, one generation on. A Set graduated from this spec today would read "STILL NET-NEW: `From-Spec`" and could add a second `From-Spec` recognition path, which is precisely the duplication the correction existed to prevent. Item 4 could likewise send someone to create a parallel capability module, which is exactly the defect that killed `a54m79` and forced `hostcap-01` to be written.

The deeper point, worth deciding separately: a spec that enumerates "what is not built yet" acquires a maintenance burden that nothing enforces. This paragraph has now gone stale TWICE. Options include (a) keep correcting it as things land, (b) delete the enumeration and let plans measure current state themselves, which is what every recent plan review actually does, or (c) keep it but mark it explicitly as a point-in-time snapshot with its measurement date and commit, so a reader knows to re-verify. (b) or (c) look better than (a); the audit found that plan reviews already re-measure regardless, so the list's real function is to warn, not to inform.

## Suggested fix

Add an `aw specs note` entry recording the re-measurement, and amend the paragraph: move `From-Spec` from "still net-new" to the shipped list citing `8c437188`, and reword the capability-descriptor item as partially shipped with `host_sandbox_profile.py` named as the owner to extend. Do NOT change the design; this is a factual-status correction, the same class as `a59f2c5` itself.

Note the spec is `approved`, so it stays approved: a factual-status note is not a design change (that precedent is `a59f2c5`).
