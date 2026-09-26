- Id: oc3mhb
- Status: blocked
- Gate-Kind: artifact
- Gate-Ref: .aw/records/specs/reviewed/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
- Set: oc3mhb
- Priority: medium
- Work-Kind: feature
- Summary: aw oc run refuses a spec selector it can now resolve, because the queue is plan-shaped; spec 25kzda 1.3/2.1 still describe graduation as shipped

## Workflow history
- 2026-09-26 same-status (aw set): Gate path corrected: spec z7nbn1 is now reviewed; graduate once it is approved.
- 2026-09-26 same-status (aw set): Gate retyped: an artifact gate naming spec z7nbn1 (graduate from it once the maintainer approves it).
- 2026-09-26 blocked (aw set): Blocked 2026-09-26: graduate from spec z7nbn1 immediately after the maintainer approves it (maintainer ruling).
- 2026-09-26 note (aw backlog): Maintainer 2026-09-26 (/askme during batch graduation): the maintainer is reviewing spec z7nbn1 now; graduate this item from z7nbn1 immediately after it is approved. Blocked on that decision gate until then.
- 2026-09-23 created (aw backlog): Filed by IPD iuxtjy (graduate Order 02), which fixed the RESOLUTION half and deliberately stopped short of dispatch per maintainer ruling on its OQ-03/OQ-04.

WHAT IS THE GAP. IPD `iuxtjy` made a spec selector resolve to the SPEC on both runner hosts, fixing a silent mis-resolution (a spec id6 matched an adopting plan's FILENAME, so naming a spec started a run about a different artifact). What it deliberately did NOT build is DISPATCH: a spec selector now produces a clear refusal naming the spec, because a run queue entry is plan-shaped.

MEASURED AT HEAD 4c1fffde, the four seams that remain:
  1. `build_dynamic_manifest` compiles `discover_plans` ALONE, so `manifest['plans']` never holds a spec.
  2. `initialize_run_core`'s queue loop reads `manifest['plans'][id6]` with a BARE SUBSCRIPT, so a spec id6 surviving expansion would raise `KeyError` rather than run.
  3. The legality derivation cannot express the action: `action_for`/`determine_action` return only `{execute, review, orchestrate}` over EVERY Kind x status pair (76 combinations checked), and neither body contains the string `plan`.
  4. `ACTION_IMPLEMENTED` is `frozenset({'review'})`, so `--action plan` fails closed. Widening it ALONE would be worse than the gap: with no derivation that can return `plan`, the refusal misreports, naming the derived action instead of the requested one.

THE TABLE IS ALREADY WRITTEN AND MUST NOT BE FORKED. `run_selection_policy._SPEC_ACTIONS` maps `approved -> plan` and `_BACKLOG_ACTIONS` maps `open -> plan`, transcribed from spec 25kzda 3.3/3.4 and read through the private `_action_for`. A maintainer ruling of 2026-09-10 (IPD `iuxtjy` OQ-04) chose: EXPOSE A PUBLIC READER over that one table and have the drivers consult it per type. Do not add a third copy.

WHY THIS IS A REAL DISCREPANCY RATHER THAN A WISH. Spec `25kzda` carries `- Status: approved` and its 1.3 lists 'Author an IPD from an approved spec' and 'Graduate an open backlog item into an IPD' as DISPOSITIONS OF `aw <host> run`, while 2.1 registers `--action plan`. Those are agreed requirements that were never implemented, so the honest record is this gap, NOT an amendment narrowing the spec to match the code.

OWNERSHIP OVERLAPS AND SHOULD BE RECONCILED BEFORE ANY WORK STARTS. Spec `z7nbn1` (universal artifact dispatch, `- Status: to-review`) 4.1 names this exact plans-only queue as 'the single structural blocker' and 4.3 records that `ACTION_PLAN` has no consumer, so it already claims this territory. Whoever picks this up should decide whether it graduates from `z7nbn1` rather than becoming a fourth parallel effort; that decision is precisely the duplication the `graduate` Set exists to prevent.

THE BACKLOG HALF IS ALSO UNBUILT AND IS SMALLER THAN EARLIER PROSE CLAIMED. There is no `discover_backlog`, but `check_engine._type_dirs(repo,'backlog')` already resolves the tree and `selectors.resolve(repo,'backlog',<id6>)` already resolves a backlog id6 to its file, so the enumeration is thin. The cost is the four seams above, which BOTH halves must cross identically. A backlog selector today refuses informatively via `describe_unresolved_plan_selector`; verified it does not silently no-op.
