# IPD: Converge the eight duplicate history-clock reports onto the two plans that already own the fix, closing each with cited evidence so no release gate is dropped

- Date: 2026-10-01
- Kind: child
- Concern: REVIEW NOTE 2026-10-07: the cluster has largely converged since authoring (see PR-001); the residual is two closes and two notes, and the authored text below is kept as the record of 2026-10-01. Authored: EIGHT separate release-gated backlog items report ONE defect, and six of them are still `open` with no carrier. `fnb8pl`, `tl8qmc`, `jvw1kg`, `2wae2x`, `o8l2y2`, `doe2fo` and `lq2w86` plus the already-graduated `7qvs1c` and `a2zpzq` all describe `backlog.py` stamping `## Workflow history` from the LOCAL clock while `status_set.py` stamps UTC. The production fix and its enforcing guard are ALREADY OWNED by two `to-review` plans (`5ivkdh` from `7qvs1c`, `ayhveg` from `a2zpzq`), and BOTH explicitly defer sibling-item closure naming `fnb8pl` as its carrier. So this item's residual work is not the clock: it is the convergence. Two concrete costs, each measured rather than asserted. FIRST, `aw attention` counts seven live release blockers where one defect exists, so the blocker set for the next release overstates the remaining work sevenfold. SECOND, two of the items record a diagnosis that is now FALSE: `fnb8pl` and `tl8qmc` both state that `test_release_exempt_setter_roundtrip_and_parity` fails, but commit `da04c5cf0` added a date mask to that test, and it now PASSES inside a live skew window (measured under `TZ=Pacific/Honolulu`, `1 passed`), so a reader triaging by that symptom looks for a red test that no longer exists while the real defect is live.
- Scope: REVIEW-REVISED 2026-10-07: IN is now (a) a dated correction note on `fnb8pl` and `tl8qmc`, (b) closing the two duplicates that still have NO live carrier (`2wae2x`, `open`; `lq2w86`, `graduated` to the SUPERSEDED `rfyrvp`) citing the executed `5ivkdh`, and (c) verifying, WITHOUT editing, that `tl8qmc` and `o8l2y2` stay graduated to their own live carriers (`dmrbqa`, `5xq2ng`), which own residual work that is NOT a duplicate. `jvw1kg` and `doe2fo` are already `done` and are not touched. Authored: IN: give each of the six uncarried duplicate items a terminal disposition that PRESERVES the release gate rather than dropping it, correct the two stale diagnoses with a dated note, and record the convergence so a later reader can see one defect and one owner instead of eight reports. OUT, each with a reason recorded under "Deferred": the production clock fix (owned by `5ivkdh`); the enforcing timezone guard (owned by `ayhveg`); the `resolve_evidence_artifact` gate hole found while authoring this plan and filed as `7lfe87`; filename dates, which `DECISIONS.md` D55 rules LOCAL; and the dispatch-fork unification owned by the `setdisp` Set.
- Scope-Paths: .aw/records/backlog/graduated/20260930-fnb8pl-01-fnb8pl-unify-the-history-date-clock-across-both-backlog-s.backlog.md, .aw/records/backlog/done/20260930-tl8qmc-01-tl8qmc-local-versus-utc-history-date-split.backlog.md, .aw/records/backlog/open/20260930-2wae2x-01-2wae2x-backlog-status-set-tz-parity.backlog.md, .aw/records/backlog/graduated/20260930-lq2w86-01-lq2w86-fix-date-timezone-parity-between-backlog-run-set-a.backlog.md
- Item-Dependencies: executed:5ivkdh, executed:ayhveg
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: fnb8pl
- Blocks-Release: next
- Set: fnb8pl
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: qjm4bg
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-08 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): Scope-Paths corrected to follow `tl8qmc` graduated->done (its carrier `dmrbqa` executed 2026-10-07). Run run-20261007T181927Z-1710911 refused dispatch (fail-gate, scope-target-stale moved-terminal). Path-only correction. PREMISE DRIFT FOR THE EXECUTOR: E-04 and V-05 expect `tl8qmc` still `graduated`; it is now `done` through its own carrier, which is the convergence this plan wanted, so verify it as done rather than refusing.
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED via /plan-review; PR-001..PR-008 all FIXED. Reviewed at HEAD `c97763c85`; lint `author` and `review-finalize` conforming. The design held but the premise had drifted: `5ivkdh` executed, and the cluster mostly converged (`jvw1kg`/`doe2fo`/`7qvs1c` done; `tl8qmc`/`o8l2y2`/`a2zpzq` graduated to live carriers; `lq2w86` graduated to the SUPERSEDED `rfyrvp`; only `2wae2x` open), leaving six Scope-Paths stale (PR-001). Closing `tl8qmc` would have dropped a gate on `dmrbqa`'s unshipped sidecar work (PR-002). E-03 now closes only `2wae2x` and `lq2w86`, E-04 is verify-only, and `fnb8pl` is already graduated (PR-003). E-02 now names the mask-removing commit `3c55295a3` (PR-004). The skew-window claim was false between 10:00 and 14:00 UTC (PR-005). The `valid: true` bar was unsatisfiable (PR-006). The suite count is now re-derived and finalize ownership made conditional (PR-007). Goal restated (PR-008). The `executed:ayhveg` edge is still unmet (`ayhveg` reviewed, pending), so the runner will hold this plan dependency-blocked until it executes. Findings in `.aw/records/reviews/20261001-fnb8pl-01-qjm4bg-converge-the-eight-duplicate-history-clock-reports-onto-the.review.md`.

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `fnb8pl`. The authoring turn found that `fnb8pl`'s OWN described work (unify the clock) is already owned by two `to-review` plans that each name `fnb8pl` as the carrier for sibling closure, so this plan was scoped to the convergence rather than duplicating a ninth copy of the fix. The defect was reproduced live at HEAD `dce6228bb` under `TZ=Pacific/Honolulu` (local `2026-10-01`, UTC `2026-10-02`): the two spellings wrote `- 2026-10-01 same-status (aw backlog): m` and `- 2026-10-02 same-status (aw set): m`. A previously unfiled gate hole was MEASURED while verifying the close route and filed as backlog `7lfe87`. Bare suite baseline at authoring: `5 failed, 4586 passed, 2 skipped` (all five failures pre-existing and untouched by this plan, which edits no `.py` file).

## Goal

Leave no history-clock duplicate WITHOUT a live owner, without dropping any release gate and
without rewriting another item's recorded diagnosis dishonestly. (Revised at review 2026-10-07: the
authored "ONE live owner" is no longer the right target, because two duplicates have since been
graduated to carriers owning genuinely distinct residual work, `dmrbqa` and `5xq2ng`, which must
keep their own gates.)

This plan writes NO production code and NO test code. It is a RECORDS convergence: the behavioral
fix is `5ivkdh`'s and the enforcing guard is `ayhveg`'s, and this plan deliberately depends on both
so that it can cite SHIPPED work as the reason each duplicate closes, rather than asserting a fix
that has not landed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: confirm the premise still holds before changing any record

- [ ] E-01 Re-verify, at execution time, that BOTH owning plans are `executed` and that the clock defect is actually GONE, and refuse to proceed if either is false. This is its own item and it comes first because every later item CLOSES a release-gated record on the strength of this claim; closing seven blockers on the strength of a stale reading is precisely the silent gate drop the close predicate exists to prevent.

    STATE AT REVIEW (2026-10-07, HEAD `c97763c85`), recorded so the executor knows which half is still outstanding: `5ivkdh` is under `executed/` (commit `3c55295a3`); `ayhveg` is still in `pending/` at `Status: reviewed`, so the `executed:ayhveg` edge is UNMET and the runner will mark this plan `dependency-blocked` until it executes. That is the intended behavior, not a defect. The driven reproduction already PASSES at review (both spellings wrote the UTC date `2026-10-07` under `TZ=Pacific/Honolulu`, local `2026-10-06`); it must be re-driven at execution because a later commit could regress it.

    CONFIRM THE TWO CARRIERS BY DISPOSITION, NOT BY STATUS LINE ALONE. `5ivkdh` and `ayhveg` must each be in `.aw/records/plans/executed/`. Read the disposition directory as well as the `- Status:` field, because `check_engine._carrier_is_executed` is what the close gate itself consults and a hand-edited status line without the move is exactly the untooled-transition case the repository already guards.

    THEN CONFIRM THE BEHAVIOR, BY DRIVING IT RATHER THAN BY READING THE SOURCE. Reproduce the original divergence check inside a skew window: in a throwaway temp repository (never the live tree), drive both `aw backlog set` spellings (`aw backlog set <id> --status parked` and `aw backlog set parked <id>`) against two identical fixture items under `TZ=Pacific/Honolulu` and under `TZ=Pacific/Kiritimati`, and require that the history date each writes equals the UTC date. Print the local and UTC dates for each zone: Honolulu (UTC-10) is in a skew window from 14:00 to 24:00 UTC and Kiritimati (UTC+14) from 00:00 to 10:00 UTC, so at most ONE is skewed at any moment, and between 10:00 and 14:00 UTC NEITHER is. If neither printed pair differs, re-run inside a window or add a zone that is skewed at that hour; a run with no skewed zone proves nothing. Do NOT assert that any module calls `datetime.timezone.utc`; that is a code-structure pin forbidden by GUIDING_PRINCIPLES P16 and by the `AGENTS.md` no-code-pinning rule.

    IF EITHER CHECK FAILS, STOP AND REPORT, changing no record. This is a genuinely unsafe precondition (the prerequisite work does not exist), which the plans README's execution contract distinguishes from a scope question, so halting is correct here rather than proceeding and justifying at finalize.
  - Depends on: none
  - Expected outcome: both `5ivkdh` and `ayhveg` are confirmed present under `.aw/records/plans/executed/` with a terminal status; a driven reproduction in at least one zone whose local date DIFFERS from the UTC date shows BOTH setter spellings recording the UTC date; the pre-change BASELINE of `aw attention --blocking next --json` and `aw check all --agent` is captured for E-05; the exact commands and their pasted output are recorded; no record has been modified yet.
  - Execution state: pending

### Task group 2: correct the two diagnoses that are now false

- [ ] E-02 APPEND a dated correction note to `fnb8pl` and `tl8qmc` recording that their stated symptom no longer reproduces, using `aw backlog note` and WITHOUT editing their original prose. Both items state that `test_release_exempt_setter_roundtrip_and_parity` fails. The symptom changed TWICE, and the note must record both so the trail is traceable: commit `da04c5cf0` ("histlabel(jbipfa): give the shared backlog history writer its transition label") first MASKED the date in that test (its comment read "This clock skew is live bug fnb8pl (out of scope for jbipfa), so dates are normalized by shape"); then commit `3c55295a3` (`5ivkdh`) REMOVED that mask, so the test now compares dates literally and passes because the clock is FIXED, not because it is masked. Measured at review inside a live skew window (`TZ=Pacific/Honolulu`, local `2026-10-06`, UTC `2026-10-07`): `1 passed`.

    APPEND, NEVER REWRITE, AND THE DISTINCTION IS NOT COSMETIC. The original diagnosis was TRUE when it was written, and the symptom changed because a later commit masked it. Editing the original text would destroy the record of a real measurement and assert a history that did not happen (GUIDING_PRINCIPLES P4); `ayhveg` reached the same conclusion and deferred the rewrite for exactly this reason. A dated note adds to the record instead.

    SAY WHAT THE READER SHOULD LOOK AT INSTEAD, since a correction that only negates is a dead end: the note must name BOTH commits and point at the driven reproduction as the authoritative check. On `tl8qmc` the note must ALSO say that the item stays `graduated` to `dmrbqa`, which owns a residual LOCAL-clock site (`record_history.append`/`append_rename`) that `5ivkdh` explicitly deferred, so a reader does not mistake the note for a closure.
  - Depends on: E-01
  - Expected outcome: `fnb8pl` and `tl8qmc` each carry a new dated `## Workflow history` note stating the test-failure symptom no longer reproduces, naming `da04c5cf0` (mask added) and `3c55295a3` (mask removed, fix shipped) and giving the driven reproduction instead, with `tl8qmc`'s note also naming its live carrier `dmrbqa`; every pre-existing history record and all original prose in both files is byte-identical to before.
  - Execution state: pending

### Task group 3: close the duplicates, preserving every gate

- [ ] E-03 Close the two duplicates that still have NO live carrier, `2wae2x` and `lq2w86`, through the tooled setter, citing the EXECUTED owning plan as evidence, one item per call. REVIEW-REVISED 2026-10-07 (PR-001): the authored five-item batch is obsolete. `jvw1kg` and `doe2fo` were already closed `done` by their own executed carriers (`9wcei0`, `840y6i`) and must NOT be touched. `o8l2y2` is `graduated` to the reviewed plan `5xq2ng`, which owns NON-duplicate work (keeping `check.lifecycle-transition-invalid` meaningful once history dates stop varying), so closing it here would orphan that plan's gate; it is left alone and verified in E-04. That leaves `2wae2x` (`open`, no carrier, body is the same two-clock divergence) and `lq2w86` (`graduated` to `rfyrvp`, which was RETIRED to `superseded/` on 2026-10-03 in favor of `9wcei0`, so this item's only carrier is dead; leaving it `graduated` would keep a release blocker alive with no live owner).

    USE THE SATISFIED ROUTE WITH AN EXECUTED PLAN PATH: `aw backlog set done <id6> --evidence .aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md --message <reason>`. The gate's three legitimate routes are HANDOFF, SATISFIED and DE-GATED (`check_engine.evaluate_blocking_close`), and SATISFIED is the honest one here because the work genuinely shipped. Measured at review with `--dry-run --agent`: the SATISFIED call returns `outcome clean, exit 0` for both items, and the same call WITHOUT `--evidence` returns `outcome findings, exit 1`, so the gate is live on both. For `lq2w86` the `--message` must name `rfyrvp` as superseded and `9wcei0` (the plan that absorbed its scope, also executed) so the handoff chain is legible.

    DO NOT USE `--blocks-release -`. De-gating asserts the item never blocked the release, which is FALSE for a live release-gated bug; it would also hide the item from the blocker view rather than recording that it was fixed. Both routes exit 0, so the gate will not stop the wrong choice and the reason for it must be the author's.

    CITE A PATH UNDER `executed/`, NOT A PENDING ONE, EVEN THOUGH THE GATE WOULD ACCEPT EITHER. Measured 2026-10-01 at HEAD `dce6228bb`: citing the then-pending `ayhveg` returned `outcome clean, exit 0, findings 0` on a gated item, because `check_engine.resolve_evidence_artifact` checks only that the path is safe, in-tree, existing and under `.aw/records/`, never the cited artifact's lifecycle. That hole is filed as `7lfe87` (still `open` at review) and is NOT this plan's to fix; what this plan owes is not to exploit it.
  - Depends on: E-01
  - Expected outcome: `2wae2x` and `lq2w86` are `done` and relocated under `.aw/records/backlog/done/`, each closed by a separate tooled call citing the EXECUTED `5ivkdh` path, each retaining its `- Blocks-Release: next` line, and each carrying a history record naming the plan that fixed it; `jvw1kg`, `doe2fo` and `o8l2y2` are byte-identical to before; every call's output is pasted.
  - Execution state: pending

- [ ] E-04 VERIFY, WITHOUT EDITING, that the two duplicates carrying live NON-duplicate carriers are still correctly gated: `tl8qmc` `graduated` to `dmrbqa` and `o8l2y2` `graduated` to `5xq2ng`, each carrier still in `pending/` or `executed/` (not `superseded/` or `not-executed/`) and each carrying `- From-Backlog:` pointing back at its item and `- Blocks-Release: next`. REVIEW-REVISED 2026-10-07 (PR-002): the authored E-04 closed `tl8qmc` here. That is now WRONG: `tl8qmc` graduated on 2026-10-02 to `dmrbqa`, which owns the gitignored history sidecar's LOCAL-clock sites that `5ivkdh` explicitly deferred, so the defect `tl8qmc` reports is NOT fully shipped and closing it would drop a gate on unshipped work. Its close belongs to `dmrbqa`'s own finalize through the HANDOFF route. If either carrier has been retired by execution time, do not close the item on a guess: record the finding and leave it, because choosing the next carrier is a maintainer decision.
  - Depends on: E-01
  - Expected outcome: pasted evidence that `tl8qmc` and `o8l2y2` are each `graduated`, each named carrier exists in a live or executed disposition with a matching `- From-Backlog:` and `- Blocks-Release: next`, and neither item file was modified by this plan apart from E-02's note on `tl8qmc`.
  - Execution state: pending

- [ ] E-05 Leave `fnb8pl` ITSELF alone apart from E-02's note, and verify the cluster is actually converged rather than assuming the calls did it. REVIEW-REVISED 2026-10-07 (PR-003): `fnb8pl` is ALREADY `graduated` (`2026-10-01 graduated (aw backlog): graduated by run ...: qjm4bg`), so the authored premise that the runner would graduate it is spent. This plan carries `- From-Backlog: fnb8pl`, so the HANDOFF route closes it when this plan executes (a runner closes it in the same run, as it did for `jvw1kg` and `doe2fo`); writing a status onto it here would forge a transition this plan does not perform.

    VERIFY BY QUERY, NOT BY RE-READING THE FILES JUST EDITED. Run `aw attention --blocking next --json` and confirm `2wae2x` and `lq2w86` now carry `attention_class: done`, while `fnb8pl`, `tl8qmc`, `o8l2y2` and `a2zpzq` are still `active`. NOTE: `--blocking next` lists `done` items too (measured: `jvw1kg` appears with class `done`), so the check is on the CLASS, not on absence. Compare `violations` against the E-01 baseline rather than requiring `valid: true`: at review the view was already `valid: false` from five unrelated `attention.lane-stranded` violations, so the bar is NO NEW violation, not an absolute value this plan cannot control. Then run `aw check` and confirm no new `check.blocking-item-closed-without-gate`, `check.from-backlog-dangling` or duplicate-id finding appeared relative to the pre-change run.

    CAPTURE THE BEFORE STATE IN E-01's EVIDENCE OR THIS CHECK IS UNFALSIFIABLE. A findings count means nothing without its baseline, so the comparison must be against output captured before any record changed, not against a remembered number.
  - Depends on: E-03, E-04
  - Expected outcome: `fnb8pl` is left exactly as this plan found it except for E-02's appended note, with no status change written by this plan; `aw attention --blocking next` shows `2wae2x` and `lq2w86` as `done` and introduces no violation absent from the baseline; `aw check` shows no new gate, dangling-link or duplicate-id finding against the baseline; both before and after outputs are pasted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A release-gated backlog item cannot be closed `done` casually: `check_engine.evaluate_blocking_close` fails closed unless one of HANDOFF, SATISFIED or DE-GATED applies. Verified live on this item: `aw backlog set done fnb8pl --dry-run --agent` returns `"outcome":"findings","exit":1` with rule `check.blocking-item-closed-without-gate`.
- `graduated` is explicitly legitimate for a gated item and drops nothing: that branch of `evaluate_blocking_close` returns `graduated preserves gate ... (item stays a release blocker; 'done' still requires handoff, evidence, or explicit de-gating)`. This is why the runner's `graduated` transition on `fnb8pl` is safe and why E-05 leaves it alone.
- Plans legitimately carry records paths in `- Scope-Paths:`. Precedent in the pending tree: `j7dsci` declares seven `.aw/records/` artifacts including three individual `.backlog.md` files, and `qkwu1r` declares one.
- `- From-Backlog:` is SINGLE-VALUED in fact (`ipd_schema.META_FROM_BACKLOG`, "ratified single-valued in fact by plan okp2o4, Set fbcardinal"). One plan therefore cannot graduate all eight items by field, which is the mechanical reason this cluster needs a convergence plan rather than a multi-valued link.
- `aw backlog note` accepts `--date` to override the history date; `aw backlog set` does not. E-02 uses `note`, so it is unaffected by the clock defect it describes.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| F-01 | The defect is LIVE at HEAD `dce6228bb`, not merely historical. REVIEW UPDATE 2026-10-07: NO LONGER LIVE for the backlog setter. `5ivkdh` executed (commit `3c55295a3`); re-driven at review HEAD `c97763c85` under `TZ=Pacific/Honolulu` (local `2026-10-06`, UTC `2026-10-07`) both spellings wrote `- 2026-10-07 parked`, rc 0. | Driven in this lane under `TZ=Pacific/Honolulu` against two identical fixtures: the `--status` spelling wrote `- 2026-10-01 same-status (aw backlog): m` and the positional spelling wrote `- 2026-10-02 same-status (aw set): m`, both `rc 0`. | The cluster describes a real, current bug, so closing the duplicates must cite a shipped fix rather than declare them obsolete. |
| F-02 | EIGHT items report this one defect, SEVEN of them gated and live. REVIEW UPDATE 2026-10-07 (PR-001): re-measured, the cluster has mostly converged. `jvw1kg`, `doe2fo`, `7qvs1c` are `done` (own carriers executed); `fnb8pl` (this plan), `tl8qmc` (`dmrbqa`), `o8l2y2` (`5xq2ng`), `a2zpzq` (`ayhveg`) are `graduated` to live carriers; `lq2w86` is `graduated` to `rfyrvp`, which is SUPERSEDED; only `2wae2x` is still `open`. | `fnb8pl`, `tl8qmc`, `jvw1kg`, `2wae2x`, `o8l2y2`, `doe2fo`, `lq2w86` all `open`; `7qvs1c` and `a2zpzq` `graduated`; every one carries `- Blocks-Release: next`. | `aw attention`'s blocker set for the next release overstates the remaining work sevenfold. |
| F-03 | The production fix is ALREADY OWNED and review-ready. REVIEW UPDATE 2026-10-07: `5ivkdh` is now EXECUTED. | `5ivkdh` (authored as `to-review`, `From-Backlog: 7qvs1c`) declares `Scope-Paths` covering `artifact_core.py`, `backlog.py`, `specs.py`, `status_set.py`, `releases.py` and `readiness_recheck.py`, and routes every history writer onto one UTC helper. | A ninth plan re-fixing the clock would collide with it. This plan must converge records, not duplicate code. |
| F-04 | The enforcing guard is ALSO owned, by a second plan that found a family `5ivkdh` does not cover. REVIEW UPDATE 2026-10-07: `ayhveg` is `reviewed` in `pending/`, NOT yet executed, so this plan's `executed:ayhveg` edge is unmet and the runner will hold it `dependency-blocked`. | `ayhveg` (authored as `to-review`, `From-Backlog: a2zpzq`) measured the SPEC-family divergence ("in none of the eight items and in no plan's `Scope-Paths`") and builds a timezone-parameterized guard. | Both carriers must be executed before a duplicate can honestly close, hence the two `Item-Dependencies` edges. |
| F-05 | BOTH owning plans explicitly defer sibling closure AND NAME `fnb8pl` AS ITS CARRIER. | Each carries a Deferred row: "THE SIX SIBLING CARRIERS ARE NOT CLOSED ... `- Carrier: fnb8pl`" and "THE SEVEN SIBLING ITEMS ARE NOT CLOSED ... `- Carrier: fnb8pl`". | This plan's scope is not invented; it is the obligation two reviewed-ready plans already handed to this item. |
| F-06 | TWO items record a diagnosis that is now FALSE. REVIEW UPDATE 2026-10-07: the mask `da04c5cf0` added was later REMOVED by `3c55295a3` (`5ivkdh`), whose diff deletes the "This clock skew is live bug fnb8pl" comment; the test now passes because the clock is fixed, so E-02 names both commits. | `fnb8pl` and `tl8qmc` both state `test_release_exempt_setter_roundtrip_and_parity` fails; under `TZ=Pacific/Honolulu` it reports `1 passed`. Commit `da04c5cf0` added the mask, whose comment names "live bug fnb8pl". | A triager searching for the red test finds green and may close the cluster as fixed while the defect is live. E-02 corrects this by appending, not rewriting. |
| F-07 | The `--evidence` close route accepts a PENDING plan, so the SATISFIED gate can be satisfied by unshipped work. | `aw backlog set done 2wae2x --evidence <pending ayhveg path> --dry-run --agent` returned `"outcome":"clean","exit":0,"findings":0` on a gated item. `check_engine.resolve_evidence_artifact` tests only safety, in-tree-ness, existence and an `.aw/records/` prefix, never lifecycle, while its own docstring says "an executed IPD". | A real gate hole, FILED as `7lfe87` (bug, gated). Not fixed here; E-03 declines to exploit it by citing only an `executed/` path. |
| F-08 | No production clock site remains outside the two owning plans' declared scope. REVIEW CORRECTION 2026-10-07 (PR-002): FALSE as stated. `record_history.append`/`append_rename` stamp the history sidecar from the LOCAL clock, `5ivkdh` explicitly DEFERRED it ("THE GITIGNORED HISTORY SIDECAR IS NOT CONVERTED HERE"), and plan `dmrbqa` (carrier of `tl8qmc`) owns it. This is why E-04 no longer closes `tl8qmc`. | The local-clock history writers are `backlog._reattach_history` and the two `created` renderers in `backlog._render_item`, `specs._today`'s callers, `releases.render_new_release`'s ISO line, and `readiness_recheck`'s `today`; all are inside `5ivkdh`'s `Scope-Paths`. `set_records.close_on_answer` delegates its history write to `backlog._reattach_history`, so it is fixed transitively. | Confirms there is no leftover code fix for this plan to claim, which is why it is records-only. |

## Proposed changes (ordered, validatable)

1. Re-verify the premise: both carriers `executed`, the clock divergence gone when DRIVEN in a zone proven to be skewed, and capture the `aw attention`/`aw check` baseline. Refuse to touch any record otherwise (E-01).
2. Append a dated correction note to `fnb8pl` and `tl8qmc`, naming the mask-added (`da04c5cf0`) and mask-removed (`3c55295a3`) commits and giving the driven reproduction in place of the test; `tl8qmc`'s note also names its live carrier `dmrbqa` (E-02).
3. Close the two duplicates that have no live carrier, `2wae2x` and `lq2w86`, one call at a time through the tooled setter, citing the EXECUTED `5ivkdh`, each retaining its gate line (E-03).
4. Verify, without editing, that `tl8qmc` and `o8l2y2` stay graduated to live carriers that own non-duplicate work (E-04).
5. Leave `fnb8pl`'s status alone (already `graduated`; the HANDOFF route closes it when this plan executes) and verify convergence through `aw attention` and `aw check` against the E-01 baseline (E-05).

## Deferred / out of scope (with reason)

- THE PRODUCTION CLOCK FIX IS NOT MADE HERE. `5ivkdh` owns it, declares all six production paths, and this plan takes a hard `executed:5ivkdh` dependency on it. Re-fixing it would collide with a review-ready plan.
  - Carrier: 5ivkdh
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md
- THE ENFORCING TIMEZONE GUARD IS NOT BUILT HERE. `ayhveg` owns it, including the SPEC-family divergence that no filed item mentions. This plan depends on it rather than reproducing it.
  - Carrier: ayhveg
  - Carrier-Evidence: .aw/records/plans/executed/20261001-a2zpzq-01-ayhveg-give-the-utc-history-date-ruling-a-durable-cross-spelling-gu.ipd.md
- THE `resolve_evidence_artifact` GATE HOLE IS NOT FIXED HERE (F-07). It is a distinct defect in the close predicate, not in the clock, and fixing a shared gate predicate while closing items through that same gate would make this plan both the subject and the judge of its own close calls.
  - Carrier: 7lfe87
- FILENAME DATE PREFIXES ARE NOT TOUCHED. `DECISIONS.md` D55 ("Human-facing timestamps use LOCAL time, not UTC") is a current ruling that deliberately reverses an earlier UTC directive. The two clocks compose as written, and reversing D55 would need its own maintainer decision.
  - Carrier-Declined: not a defect; D55 is a deliberate, current ruling.
- THE DISPATCH FORK IS NOT UNIFIED. The `setdisp` Set moves both setter spellings onto one engine, and spec `wy9aru` Section 7 assigns that work there, explicitly listing the UTC-versus-local axis as owned by this cluster rather than by unification. This plan is correct whether `setdisp` lands before or after, because it changes records only.
  - Carrier: fcnz1r
- THE ITEMS WITH LIVE OR SHIPPED CARRIERS ARE NOT RE-TRANSITIONED. REVIEW-REVISED 2026-10-07: `jvw1kg`, `doe2fo` and `7qvs1c` are already `done`; `a2zpzq` (`ayhveg`), `tl8qmc` (`dmrbqa`) and `o8l2y2` (`5xq2ng`) are `graduated` with their gates intact and their carriers named; `graduated` already keeps them in the blocker view, and their closure belongs to whoever finalizes their own carriers.
  - Carrier-Declined: not a defect; `graduated` preserves the gate and the correct closer is each item's own carrier plan.
- PRE-EXISTING SUITE FAILURES ARE NOT FIXED. The bare suite measured `5 failed, 4586 passed, 2 skipped` at authoring (a live-artifact figure, re-derive it at execution; see Required tests 6), in `test_run_finding_reachability`, `test_typecheck_gate`, `test_statusline_behavior`, `test_spec_review_attestation` and `test_verbose_flag_reach`. None involves the history clock and this plan edits no `.py` file.
  - Carrier-Declined: unrelated to this plan's subject; it changes no code, so it can neither cause nor fix them.
- NO HISTORIC RECORD IS REWRITTEN TO THE UTC CLOCK. Records already written carry whichever clock wrote them. Restamping committed history would assert dates that were never recorded (GUIDING_PRINCIPLES P4).
  - Carrier-Declined: not a defect; the existing records are the honest history.

## Scope check

- Over-scope: none. Every declared path is one of the four backlog items this plan edits (`fnb8pl`, `tl8qmc` notes; `2wae2x`, `lq2w86` closes) at its CURRENT location, and no `.py`, test, or doc file is declared or touched. The two closes MOVE `2wae2x` and `lq2w86` into `backlog/done/`. Those destinations are deliberately NOT declared: a not-yet-existing path under `.aw/records/` is reported by `check.scope-path-target-stale` as an `error` against this pending plan (measured at review). If finalize's scope reconciliation reports either `done/` path as out of scope, justify it with `--scope-reason <path>="rename target of a declared item closed by E-03"`.
- Under-scope: `jvw1kg`, `doe2fo`, `7qvs1c` (done), `a2zpzq` and `o8l2y2` (graduated to live carriers) are deliberately NOT declared, because their gates are already preserved or discharged; so is `fnb8pl`'s own status transition, which belongs to the HANDOFF close at this plan's execution. The `7lfe87` gate hole is filed rather than fixed. Each is recorded under "Deferred" with its carrier.

## Required tests / validation

This plan changes no code, so there is no unit test to add; its validation is the OBSERVABLE STATE
of the records tree plus the driven behavioral precondition.

1. PRECONDITION, driven not read: both carriers present under `.aw/records/plans/executed/`, and both
   `aw backlog set` spellings recording the UTC date in at least one zone whose printed local date
   differs from the UTC date. `TZ=Pacific/Honolulu` and `TZ=Pacific/Kiritimati` are NOT always
   bracketing (they are 24 hours apart, so between 10:00 and 14:00 UTC neither is skewed); the run
   must print local and UTC dates and is invalid if no zone shows a difference.
2. RECORDS INTEGRITY: `aw attention --blocking next --json` shows `2wae2x` and `lq2w86` with
   `attention_class: done` and introduces no violation absent from the E-01 baseline (the view was
   already `valid: false` at review from unrelated stranded lanes).
3. NO NEW FINDINGS: `aw check` shows no new `check.blocking-item-closed-without-gate`,
   `check.from-backlog-dangling` or duplicate-id finding against the baseline captured in E-01.
4. GATE PRESERVED: every closed item still carries its `- Blocks-Release: next` line, proving the
   SATISFIED route was used rather than DE-GATED.
5. NO COLLATERAL EDIT: `git diff --cached --name-only` at commit lists only paths from
   `- Scope-Paths:`.
6. SUITE UNCHANGED: a bare `python3 -m pytest` run BEFORE the first record edit and AFTER the last
   reports the same failing set, with both actual summary lines pasted. The authoring-time
   `5 failed` is context, not the bar: the failing set is a live artifact and must be re-derived.

## Spec / documentation sync

No spec amendment is required, and `- Scope-Paths:` declares no `.spec.md` file.

Spec `2vev8j` Section 4.4 ("One timezone for every writer") already RULES this defect in UTC's favor
and is `approved`, so this plan consumes a settled ruling rather than changing a contract. The
implementing amendment, if any is needed, belongs to `5ivkdh`, which owns the production change.
Spec `wy9aru` Section 7 already records this axis as owned by `2wae2x` / `fnb8pl` / `lq2w86` rather
than by the dispatch Set, so convergence here is consistent with it and needs no edit to it.

## Open questions

### OQ-01: Should the duplicates close `done`, or be retired some other way?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence. `done` through the tooled SATISFIED route is correct. The backlog vocabulary has no "duplicate" status, and in-repo precedent closes duplicates `done` with the reason in the history message: `iyca6n` records `- 2026-09-26 done (aw set): DONE: duplicate of shw0eh (done)`, and `ifju82`, `xdwa5t`, `js1oun` and `dtml3p` were each closed `done` during a triage with `duplicate of <id6>` in the record. `parked` is wrong because it WARNs and hides a gate that is genuinely being resolved; `--blocks-release -` is wrong because it asserts the item never blocked the release.

### OQ-02: Does closing the duplicate gated reports weaken the release gate?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED mechanically. No, PROVIDED the two `Item-Dependencies` edges hold. The gate exists so a release cannot ship with an unfixed blocker; after `5ivkdh` and `ayhveg` are `executed` the defect is fixed AND guarded, so the seven reports describe shipped work and the SATISFIED route is the honest closure (`check_engine.evaluate_blocking_close`). The gate would be weakened only by closing them BEFORE the carriers execute, which is exactly what E-01 refuses to do and what F-07's hole would otherwise permit. REVIEW ADDENDUM 2026-10-07: it would ALSO be weakened by closing a duplicate whose carrier owns residual, unshipped work, which is why `tl8qmc` (`dmrbqa`) and `o8l2y2` (`5xq2ng`) are no longer closed here (PR-002).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: the output of a listing showing `5ivkdh` and `ayhveg` each under `.aw/records/plans/executed/` with their `- Status:` lines; AND the pasted output of the driven reproduction in a throwaway temp repository showing the history date written by BOTH setter spellings equal to the UTC date, with the printed local and UTC dates for every zone tried and at least one zone whose local date DIFFERS from UTC (a run with no skewed zone is NOT evidence); AND the pre-change baseline output of `aw attention --blocking next --json` (the cluster's ids, their `attention_class`, and the `violations` list) and `aw check all --agent`, plus the baseline bare-suite summary line, that V-05 compares against. No assertion about any module's source text is acceptable as evidence here.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the new history note quoted verbatim from each of `fnb8pl` and `tl8qmc`, showing it names commits `da04c5cf0` and `3c55295a3` and gives the driven reproduction, and on `tl8qmc` names `dmrbqa` as its live carrier; AND `git diff` of both files showing ONLY added lines (no `-` line), so the correction was APPENDED and nothing was rewritten.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the pasted output of the two separate `aw backlog set done ... --evidence ...` calls (`2wae2x`, `lq2w86`), each showing exit 0; AND for each item its post-change path under `.aw/records/backlog/done/`, its retained `- Blocks-Release: next` line, and its new history record (for `lq2w86` naming `rfyrvp` superseded and `9wcei0`); AND the cited evidence path shown to be under `.aw/records/plans/executed/` rather than `pending/`, which is the F-07 hole this item declines to exploit; AND `git status --short` showing `jvw1kg`, `doe2fo` and `o8l2y2` unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: for `tl8qmc` and `o8l2y2`: the `- Status:` line (`graduated`) and path; the carrier plan (`dmrbqa`, `5xq2ng`) path showing a live or executed disposition, with its `- From-Backlog:` and `- Blocks-Release:` lines; AND `git diff --stat` showing `o8l2y2` untouched and `tl8qmc` touched only by E-02's added lines. If a carrier was found retired, paste that and the recorded finding instead, with the item left unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `fnb8pl`'s `- Status:` shown still `graduated` and its path still under `.aw/records/backlog/graduated/`, proving this plan wrote no status onto its own source item; AND post-change `aw attention --blocking next --json` output showing `2wae2x` and `lq2w86` with class `done`, and its `violations` compared SIDE BY SIDE with V-01's baseline showing no new entry; AND post-change `aw check all --agent` compared SIDE BY SIDE with V-01's baseline showing no new `check.blocking-item-closed-without-gate`, `check.from-backlog-dangling`, `check.scope-path-target-stale` or duplicate-id finding; AND the actual final summary line of a bare `python3 -m pytest` run showing the same failing set as V-01's baseline and no new one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT, binding on whoever executes this plan:

1. ALL OPEN QUESTIONS ARE RESOLVED. OQ-01 and OQ-02 are both `Status: resolved` from cited
   repository evidence, and neither is `Blocking`. Nothing here awaits a maintainer decision.
2. BOTH `Item-Dependencies` EDGES ARE HARD. `executed:5ivkdh` and `executed:ayhveg` must both hold
   before any record is changed, and E-01 re-checks them AT DISPATCH rather than trusting this
   plan's authoring-time reading. If either is unmet, STOP and report: that is a genuinely missing
   prerequisite, not a scope question.
3. SCOPE FENCE (a DECLARATION, not a stop directive). Touch only the backlog files named in `- Scope-Paths:` (four items, two of which move to `done/`; the `done/` rename targets are justified at finalize as described in the Scope check). This plan
   changes NO `.py` file, no test, and no spec. Do not expand scope casually; if the work genuinely
   requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope
   reconciliation at finalize.
4. HARD MUST, HONESTY. When you report that validation passed, paste the ACTUAL command output.
   Never claim a run you did not perform. Every `V-*` above demands pasted evidence, and V-01 and
   V-05 demand a BEFORE/AFTER comparison that cannot be satisfied from memory.
5. USE THE TOOLED SETTER, NEVER A HAND EDIT. Every status change goes through `aw backlog set` and
   every note through `aw backlog note`. A hand-edited status is the untooled transition the
   repository's own gates exist to catch.
6. DO NOT WRITE A STATUS ONTO `fnb8pl`, `tl8qmc`, `o8l2y2`, `jvw1kg` or `doe2fo`. `fnb8pl` is already
   `graduated` and is closed by the HANDOFF route when this plan executes; the others are owned by
   their own carriers or already `done`. Writing a status here would forge a transition this plan
   does not perform or drop a gate on unshipped work.
7. COMMIT ONLY THIS PLAN'S OWN PATHS, through `aw commit <plan> -- <paths>`. Never `git add -A`,
   never bare `git add`, never `-a`, never `--no-verify`, and never push. Verify the staged set with
   `git diff --cached --name-only` before committing.
8. LIFECYCLE MOVE ON COMPLETION. If a runner (`aw oc run` / `aw agy run`) is driving this plan, the
   runner OWNS the finalize and the executor must not call it. If executed by hand, finalize with
   `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`, which runs the
   pre/post-transition gates, reconciles changed paths against the reviewed `Scope-Paths`, writes
   the attributed history newest-first, moves the plan to `.aw/records/plans/executed/`, and makes
   the path-scoped lifecycle commit as one transaction. Do not hand-move the file and do not claim
   `executed` until `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
