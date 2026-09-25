- Id: dtrect
- Status: graduated
- Graduated-To: carrierauth
- Set: dtrect
- Priority: medium
- Work-Kind: feature
- Summary: Deferred-section carrier subfields have no authoring or scaffold support, so an author must hand-write the typed field aw ipd scaffold does not emit

## Workflow history
- 2026-09-25 graduated (aw set): graduated into carrierauth (plan vtkfq8); verified live at 8e74dcac
- 2026-09-18 created (aw backlog): Deferred-section carrier subfields have no authoring or scaffold support, so an author must hand-write the typed field aw ipd scaffold does not emit

durablecapture 01 (`rnkqrc`) added the typed carrier vocabulary (`ipd_schema.CARRIER_FIELDS`) and the gate that reads it, but NOT authoring support for it. Measured 2026-09-18: `aw ipd scaffold` emits a `## Deferred / out of scope (with reason)` section with no carrier subfield and no hint that one is now required, and there is no verb that adds one to an existing row.

WHY THIS MATTERS RATHER THAN BEING COSMETIC: the plan's own spec-sync section states "a refusal an author cannot act on is what trains people to bypass gates (`gjadwm`)". The refusal message does name all three fixes, so it is actionable, but from 20260919 onward every newly authored plan must hand-write a field the scaffolding never mentions, which is exactly the discoverability gap that produces hand-rolled or omitted metadata.

CANDIDATE SHAPES (not decided here): emit a commented carrier placeholder in the scaffold's deferred section; teach `aw ipd sync` to report a deferred row missing a carrier at author time as an ADVISORY (never blocking, since blocking early is what E-05 forbids); or add `aw ipd carrier <plan> <row> --carrier <id6>`.

OUT OF SCOPE for `rnkqrc`, whose declared `Scope-Paths` were `check_engine.py`, `ipd_lint.py`, `ipd_schema.py` and its own test file; `ipd_authoring.py` and the templates were not declared and were deliberately not touched.
