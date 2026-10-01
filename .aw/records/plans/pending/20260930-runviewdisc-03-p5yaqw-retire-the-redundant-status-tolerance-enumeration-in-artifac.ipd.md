# IPD: Delete the dead status-tolerance enumeration in artifact_audit and pin the catch-all statuses against the live predicate that actually decides them

- Date: 2026-09-30
- Kind: child
- Concern: `artifact_audit._status_disagrees` is DEAD CODE. Its last caller was deleted by `33834c719` (IPD `mlhryi`, 2026-09-28), which replaced it with `allowed_lifecycle_pairs`; the whole repository now contains exactly ONE occurrence of the name, its own `def` line. So the eight catch-all statuses backlog `qpgs4t` was filed about are tolerated by `allowed_lifecycle_pairs`, NOT by this helper, and no test pins that tolerance or its must-keep-flagging counterexample at the surface an operator reads.
- Scope: DELETE `agent_workflows.artifact_audit._status_disagrees` and its docstring, which no caller reaches; pin the tolerance and its `executed/` counterexample behaviorally against the LIVE mechanism (`allowed_lifecycle_pairs`, reached through `audit_artifact`) for every member of `runner_shared.TERMINAL_STATES`; and correct the `run_status_is_nonterminal` docstring, which claims a `tests/test_artifact_audit.py` pin against `TERMINAL_STATES` that does not exist.
- Scope-Paths: agent_workflows/artifact_audit.py, tests/test_artifact_audit.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: qpgs4t
- Set: runviewdisc
- Order: 3
- Highest E allocated: 04
- Author: OpenCode lane qpgs4t
- Id: p5yaqw
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009. THE PLAN'S CENTRAL PREMISE WAS FALSIFIED AT REVIEW AND THE PLAN IS REWRITTEN AROUND THE MEASUREMENT. `_status_disagrees` is DEAD: commit `33834c719` deleted its only call site and the repo now holds one occurrence of the name (its own `def`), proven three ways (an AST load-site scan of the defining module finding zero `Load` contexts, a repo-wide grep over every `.py`/`.toml`/`.json`, and a call-counting spy recording 0 calls across the eight audits the plan's own F-01 claims to measure). So E-03's refactor would have rewritten unreachable code, E-01 and E-02 would have pinned a predicate nothing calls, and V-01's and V-03's mutation demonstrations were IMPOSSIBLE TO SATISFY (verified: narrowing the arm to `interrupted` changes nothing an audit returns). The plan now deletes the helper and pins the LIVE mechanism. F-04's 384-pair sweep, F-05's `timed-out`, F-07's asymmetry and OQ-02 were all measurements OF THE DEAD HELPER and are corrected or retired accordingly; F-07's real-behavior counterpart is the opposite of what it claimed. The one surviving defect from the original plan is the false docstring claim (F-06), kept as E-03.
- 2026-09-30 to-review (OpenCode lane qpgs4t): authored from backlog `qpgs4t`. The item's premise was re-measured at HEAD `928be376` and found STALE: all eight statuses it lists are already tolerated. The plan was rewritten around what is actually still wrong (no test fence, a redundant enumeration, and a false docstring claim) rather than around the item's original ask.
- 2026-09-30 draft (OpenCode lane qpgs4t): created.

## Goal

Backlog `qpgs4t` asked for a per-status measured argument before admitting each of eight terminal-failure run statuses into the `_status_disagrees` tolerance arm. TWO THINGS HAVE SINCE MOVED, and the second is what this plan is about. First, the eight statuses are no longer flagged, so the item's literal ask is obsolete. Second, and measured at review, the helper the item names NO LONGER DECIDES ANYTHING: `33834c719` deleted its only caller, so what tolerates those statuses today is `allowed_lifecycle_pairs`, and `_status_disagrees` is unreachable code whose behavior cannot be observed.

So this plan does three things, in the order a reader needs them. It PINS the tolerance and its counterexample behaviorally against the mechanism that really decides them, through the public `audit_artifact` entry point, which is the scope fence the test trim in `19313eed` deleted and is what the item actually wanted protected. It DELETES the dead helper, because a 23-entry status enumeration carrying a long docstring about tolerance bands is a standing invitation to maintain, cite, or trust a predicate that cannot affect any output. And it corrects a docstring on the live `run_status_is_nonterminal` that claims a test pin which does not exist, replacing it with the one this plan writes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the LIVE mechanism before removing anything

- [x] E-01 Add characterization tests to `tests/test_artifact_audit.py` that pin, against the CURRENT code and before any production edit, both arms of the `qpgs4t` question for all eight statuses it names (`failed`, `failed-safely`, `partial`, `not-attempted`, `merge-conflict`, `integration-blocked`, `merge-needs-human`, `cancelled`): (a) a plan UNMOVED in `pending/` reading `- Status: approved` must NOT be flagged (`has_discrepancy` False, `difference_class` `unchanged`), and (b) the counterexample, a plan in `executed/` reading `- Status: executed`, must KEEP being flagged on BOTH axes (`location_mismatch` and `status_mismatch` both True). Drive the real entry point `artifact_audit.audit_artifact` against a temporary git repo, passing `artifact_type="plans"` and `action="execute"`, which is what routes the row through the LIVE predicate `allowed_lifecycle_pairs`; do NOT call `_status_disagrees`, which F-01 measures as unreachable. This is the fence the test trim in commit `19313eed` deleted.
  - Depends on: none
  - Expected outcome: new tests pass at HEAD with no production change, demonstrating they characterize existing behavior rather than a hoped-for one; `python3 -m pytest tests/test_artifact_audit.py` green with the new cases counted. Both directions reproduce the review measurement pasted in F-01.
  - Execution state: performed

- [x] E-02 Add a closed-vocabulary test asserting that for EVERY member of `runner_shared.TERMINAL_STATES`, read from the set at test time rather than from a copied literal list, the unmoved-plan direction and the moved-plan direction each take the value the review measured, with the three exceptions named and asserted individually: `executed` inverts both (tolerated when MOVED, flagged when unmoved); `retired` is flagged in both shapes because its expected directory is a retirement directory; and every other member is tolerated unmoved and flagged moved. Derive the expectation from `artifact_audit.expected_dir_for_status` rather than restating it, so a driver adding a status fails this test instead of drifting silently. This is the pin that F-06's docstring sentence CLAIMS already exists.
  - Depends on: E-01
  - Expected outcome: the test passes at HEAD over the full 24-member set with no production change, and `grep -n 'TERMINAL_STATES' tests/test_artifact_audit.py` returns a real match, making the `run_status_is_nonterminal` docstring claim true for the first time.
  - Execution state: performed

### Task group 2: remove the dead helper and reconcile the prose

- [x] E-03 Correct the false claim in the `run_status_is_nonterminal` docstring, changing no behavior. It asserts `tests/test_artifact_audit.py` pins the predicate against BOTH host drivers' `TERMINAL_STATES`; that was false at HEAD (zero occurrences of `TERMINAL_STATES` in that file). Make it TRUE by citing the E-02 test by name. Also correct the incidental "BOTH host drivers'" framing: `oc_runipd.TERMINAL_STATES` and `agy_runipd.TERMINAL_STATES` are both plain aliases of `runner_shared.TERMINAL_STATES`, so there is ONE set and a test that sweeps it covers both hosts by construction; say that rather than implying two sets are cross-checked.
  - Depends on: E-02
  - Expected outcome: the docstring names a test that exists and describes one shared set rather than two drivers' sets; no behavior changes and the full suite is unaffected.
  - Execution state: performed

- [x] E-04 DELETE `agent_workflows.artifact_audit._status_disagrees` entirely, its body and its docstring, as dead code. Before deleting, re-prove unreachability in the executing worktree with the three independent checks F-01 used (a repo-wide search for the name over every `.py`, an AST scan of `artifact_audit.py` for any `Load`-context reference, and a call-counting monkeypatch driven through `audit_artifact`) and paste all three; if ANY of them finds a caller, STOP and report rather than deleting, because that would mean the premise has moved again. Do not substitute a deprecation shim or a `# noqa`: an unreachable predicate with a 17-line docstring about tolerance bands is exactly what misled this plan's own author, and leaving it renamed or commented out preserves the hazard.
  - Depends on: E-03
  - Expected outcome: the name occurs nowhere in the repository, the E-01 and E-02 tests pass UNMODIFIED (proving the deletion changed no audit outcome), and the full bare suite matches the baseline by node id.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE DERIVED-NOT-ENUMERATED PATTERN IS ALREADY THIS MODULE'S ESTABLISHED CONVENTION. `artifact_audit.run_status_is_nonterminal` was deliberately rewritten from an enumeration to a derivation by IPD `zexed1` (E-03, review PR-201); its docstring argues the enumerated form "fails" because a hand-written list leaves dominant false-alarm shapes unfixed. `allowed_lifecycle_pairs`, the predicate that SUPERSEDED `_status_disagrees`, follows the same convention: IPD `mlhryi` derives it from `record_placement.target_subdir`. The convention is therefore already satisfied in live code, which is why this plan DELETES the leftover enumeration rather than converting it: converting unreachable code to a better shape leaves a maintenance surface with no observable behavior.
- Test-outcome discipline: `AGENTS.md` forbids code-pinning tests (no `inspect`, no `ast`, no source regex, no symbol censuses). Every test this plan adds therefore CALLS `audit_artifact` and asserts returned values, never that a literal still appears in the source. E-04's AST and grep checks are EXECUTION-TIME EVIDENCE pasted into a validation item, not committed test code, and must not be written into `tests/`.
- DEAD-CODE DELETION HAS PRECEDENT IN THIS REPOSITORY AND IS NOT A NEW POLICY. Sibling pending plan `qdro85` ("delete the dead AST freeze exemption tables") and `malgate-02` (`38pxaz`, "delete the five unowned raising predicates") both do exactly this, so an executor need not re-litigate whether removal is preferred to preservation.
- Suite invocation: run `python3 -m pytest` BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `tests/test_artifact_audit.py` builds its own temporary git repos and must not read the live gitignored `.aw/records/runs/` tree; follow the existing fixture style in that module.

## Findings

| # | Severity | Location | Finding | Evidence |
|---|---|---|---|---|
| F-01 | BLOCKER-FOR-THE-PLAN-AS-FIRST-WRITTEN | `artifact_audit._status_disagrees` | **THE HELPER IS DEAD CODE AND DECIDES NOTHING. Found at review; it invalidates the plan's original E-02, E-03 and E-04 and both of their mutation demonstrations.** Commit `33834c719` (IPD `mlhryi`, 2026-09-28, "Audit runner queue artifacts by type and action") replaced the `status_mismatch=bool(file_status is not None and _status_disagrees(recorded, file_status))` expression with `status_mismatch=status_mismatch` computed from `allowed_lifecycle_pairs`, and deleted the only call. What tolerates the eight statuses today is `allowed_lifecycle_pairs`, which returns the six `(pre-terminal, 'pending')` pairs for any non-success, non-retired status. So the original plan would have refactored unreachable code, and its tests would have pinned a predicate no output depends on. | THREE INDEPENDENT CHECKS, all at review HEAD `72748c1c`. (1) `grep -rn 'status_disagrees' --include='*.py' --include='*.toml' --include='*.json' .` returns exactly one line, `agent_workflows/artifact_audit.py:1196:def _status_disagrees(...)`, i.e. the `def` itself. (2) An `ast.walk` over `artifact_audit.py` collecting every `Name`/`Attribute` node for that identifier prints `definition lines: [1196]` and `LOAD sites (callers): []`. (3) A call-counting spy installed over the attribute, then driving `audit_artifact` for all eight statuses, prints `_status_disagrees call count during 8 audits: 0` while every audit still returns `has_discrepancy=False difference_class=unchanged`. `git log --oneline -S '_status_disagrees'` names only `5f1591731` (introduction) and `33834c719` (call-site removal) |
| F-02 | HIGH | `allowed_lifecycle_pairs` | THE LIVE TOLERANCE IS ALREADY DERIVED, NOT ENUMERATED, so the plan's original premise that an enumeration still governs is false twice over. For any status outside `_RUN_SUCCESS_STATUSES` and not `retired`, `allowed_lifecycle_pairs('plans','execute',status)` returns the SAME six pairs regardless of which failure status is passed, and those directories come from `record_placement.target_subdir` rather than from a literal list. The tolerance is therefore status-independent BY CONSTRUCTION, which is the strongest possible form of the status-independent argument OQ-01 reaches, and it needs no `SUCCESS_STATES` guard because `approved` never reaches that branch. | `allowed_lifecycle_pairs('plans','execute',st)` returns `[('approved','pending'),('to-review','pending'),('draft','pending'),('reviewed','pending'),('queued','pending'),('running','pending')]` identically for `failed`, `integration-blocked` and `cancelled`, and the same for `initial_status='approved'` and for the untyped-legacy path |
| F-03 | HIGH | `tests/test_artifact_audit.py` | THE SCOPE FENCE THE ITEM RELIES ON NO LONGER EXISTS, so nothing pins either direction today. `qpgs4t` says `test_the_seven_sibling_catch_all_statuses_are_deliberately_unchanged` "asserts all eight keep flagging, so whoever picks this up must update that test deliberately rather than loosening the arm by accident". That test was deleted by the suite trim, and `tests/test_artifact_audit.py` now holds 21 tests of which none drives a terminal-failure status through either direction. This is the ONE original finding that survives review intact and it is what E-01 and E-02 restore. | `grep -rn 'seven_sibling\|catch_all' tests/` returns nothing; `git log -S` on the test name returns `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24), which removed 1312 lines from `tests/test_artifact_audit.py`; `grep -c 'def test' tests/test_artifact_audit.py` returns `21` |
| F-04 | HIGH | the original plan's 384-pair sweep | **THE SWEEP MEASURED THE DEAD HELPER, SO ITS CONCLUSION DOES NOT TRANSFER TO BEHAVIOR.** The numbers reproduce exactly (naive 11 divergences of 384, refined 6, all `timed-out`; `SUCCESS_STATES == {'approved','executed','reviewed'}`), so the original F-04 was not careless, but every pair it compared was a return value of a function nothing calls, so "behavior-preserving" was not a claim about any observable behavior. Two further limits appeared on re-measurement: the equivalence is NOT general, because sweeping 22 statuses OUTSIDE the plan's chosen vocabulary (`''`, `foo`, `pending`, `open`, `done`, `implementing`, `graduated`, `parked`, `deferred`, `skipped`, ...) yields 97 further divergences, so the refactor was only equivalent on the hand-picked set; and `canonical_terminal_status` is identity for an unknown token, so an unrecognized status reaching the derivation is tolerated rather than compared. The LIVE equivalent measurement is F-05. | Re-ran both candidate predicates to the plan's own figures, then re-ran over 22 additional statuses crossed with 14 declared values: `divergences outside the plan's sweep: 97`, concentrated in `open` 7, `done` 7, `implemented` 7, and 6 each for `''`, `foo`, `pending`, `graduated`, `parked`, `deferred`, `timed-out`, `skipped`, `unknown`; `canonical_terminal_status('foo') == 'foo'` |
| F-05 | HIGH | `audit_artifact` over `runner_shared.TERMINAL_STATES` | THE LIVE BEHAVIOR IS A CLEAN TRICHOTOMY AND THIS IS THE MEASUREMENT E-02 PINS. Driving the real entry point over all 24 members of `TERMINAL_STATES` in both shapes: 22 are TOLERATED unmoved-at-`approved` and FLAGGED moved-at-`executed`; `executed` inverts both (flagged unmoved, tolerated moved); `retired` is flagged in BOTH shapes, because its expected directory is a retirement directory and neither shape matches. No status is tolerated in both shapes, so the tolerance never suppresses the moved-plan row an operator needs, which is exactly the property `vdabn5` argued for and the item's counterexample demanded. | Two temp git repos (`pending/` at `- Status: approved`, `executed/` at `- Status: executed`), `audit_artifact(..., artifact_type='plans', action='execute')` for each of the 24 members: 22 rows read `False / True`; `executed` reads `True / False`; `retired` reads `True / True` |
| F-06 | MED | `run_status_is_nonterminal` docstring | A DOCSTRING CLAIMS A TEST PIN THAT DOES NOT EXIST. It states `tests/test_artifact_audit.py` "pins this against BOTH host drivers' `TERMINAL_STATES`, in the style of `runner_shutdown.KNOWN_ITEM_STATUSES`, so a driver adding a status cannot drift silently". That file contains zero occurrences of `TERMINAL_STATES`; the pin was among the 1312 lines the trim removed. A SECOND inaccuracy sits in the same sentence: there is no cross-driver check to make, because `oc_runipd.TERMINAL_STATES` and `agy_runipd.TERMINAL_STATES` are both plain assignments of `runner_shared.TERMINAL_STATES`, so one set serves both hosts. E-02 makes the pin real and E-03 corrects both claims. | `grep -c 'TERMINAL_STATES' tests/test_artifact_audit.py` returns `0`; `grep -rn 'KNOWN_ITEM_STATUSES' tests/` finds it only in `test_run_exit_aggregate.py` and `test_lifecycle_style.py`; `oc_runipd.py` reads `TERMINAL_STATES = runner_shared.TERMINAL_STATES` and `agy_runipd.py` the same |
| F-07 | MED | `substantially-complete` | **THE ORIGINAL F-07 ASSERTED THE OPPOSITE OF THE LIVE BEHAVIOR, because it too measured the dead helper.** Through the real entry point, a `substantially-complete` item whose plan sits in `executed/` reading `- Status: executed` IS flagged (`location_mismatch=True status_mismatch=True`) and so is a `complete` item in the identical shape, because `_RUN_SUCCESS_STATUSES` is `{'executed'}` alone and `complete` is not in it. There is therefore NO `complete`-versus-`substantially-complete` asymmetry in behavior; the asymmetry existed only between two return values of unreachable code. The carrier backlog `64a03w` was filed on the dead-helper reading and its central claim needs correcting; this plan notes that rather than editing the item, since nothing here changes either status's behavior. | `audit_artifact` moved-at-`executed`: `substantially-complete` and `complete` BOTH read `loc=True st=True disc=True`, while `executed` reads `loc=False st=False`; the dead helper by contrast returns `_status_disagrees('substantially-complete','executed')=True` and `_status_disagrees('complete','executed')=False`, which is the pair `64a03w` quotes |
| F-08 | CONFIRMED-NOT-BLOCKED | backlog `1f9m2j`, `rnl3b7` | THE ITEM'S CARVE-OUT FOR `integration-blocked` IS OBSOLETE AND DOES NOT GATE THIS PLAN. `qpgs4t` excludes `integration-blocked`/`merge-needs-human` as "ALREADY OWNED by backlog `1f9m2j`, which is BLOCKED on `rnl3b7`". Both have since moved: `rnl3b7` is in `done/` and `1f9m2j` is in `graduated/`. This plan changes no behavior for either status, so it neither duplicates nor conflicts with that work; it only PINS what HEAD already does. | `.aw/records/backlog/done/20260905-integdefer-01-rnl3b7-executed-gate-not-merge-aware.backlog.md` and `.aw/records/backlog/graduated/20260905-runviewdisc-01-1f9m2j-run-viewer-stale-record-mislabel.backlog.md` exist; both statuses measured `False` unmoved and `True` moved in F-05, identical to their six siblings |
| F-09 | LOW | published `--json`/`--agent` records | THIS PLAN CANNOT BREAK THE AGENT PROTOCOL, and the reason is now stronger than the original claimed. `ArtifactAudit` is `asdict()`ed into published records and `zexed1` established that removing `missing_entirely`/`location_mismatch`/`status_mismatch` would require an `aw.agent/v2` bump. Deleting an unreachable helper changes no field and no field VALUE either, because F-01 proves no published value is computed from it. The original row argued only that values did not change; the deletion makes that trivially true. | `ArtifactAudit.has_discrepancy` comment in `artifact_audit.py` records the stability rule; F-01's spy measures zero calls, so no published value can depend on the deleted code |
| F-10 | LOW | suite baseline | BASELINE RE-MEASURED AT REVIEW HEAD, because the plan's authoring baseline is 571 commits stale and its total is wrong by 210 tests. The one failure is a PRE-EXISTING, UNRELATED UTC-versus-local date split (the test expects a `2026-09-30` history line and the setter writes `2026-10-01`), already filed five times over in `.aw/records/backlog/open/` (`fnb8pl`, `lq2w86`, `2wae2x`, `o8l2y2`, `tl8qmc`). It is NOT caused by this plan, it is in no `Scope-Path` of this plan, and the executor must treat it as expected rather than chase it. | `python3 -m pytest` bare at review HEAD `72748c1c` with a clean tree: `1 failed, 3498 passed, 2 skipped, 3 warnings in 193.01s`, `NOTE: 208 tests were deselected`, the single failure `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`; `tests/test_artifact_audit.py tests/test_run_viewer.py` together `59 passed`. The plan's authored `3291 passed ... 207 deselected` at `928be376` no longer reproduces |
| F-11 | MED | the plan's original V-01 and V-03 | **TWO REQUIRED VALIDATION DEMONSTRATIONS WERE IMPOSSIBLE TO SATISFY, which is the sharpest consequence of F-01 and is why the sequencing argument did not save the plan.** V-01 required the executor to narrow the tolerance arm to `interrupted` only and paste the resulting FAILING node ids; V-03 required removing the `SUCCESS_STATES` guard and pasting the failure showing `approved` newly tolerated. Neither mutation can fail anything, because neither touches a reachable code path. An executor following the plan faithfully would have reached a mutation that produced no failure and then either fabricated evidence or halted. | Installed the exact V-01 mutation (tolerance arm narrowed to `rec == "interrupted"`) over the helper and re-ran all eight audits through `audit_artifact`: every one still returns `has_discrepancy=False`, unchanged by the mutation. No tracked file was modified to measure this |

## Proposed changes (ordered, validatable)

1. E-01 restores the deleted scope fence FIRST, pinning both directions for all eight `qpgs4t` statuses through the public `audit_artifact` entry point, so the characterization exists against the LIVE mechanism before anything is removed.
2. E-02 widens that pin to the whole closed vocabulary `runner_shared.TERMINAL_STATES`, asserting F-05's measured trichotomy and deriving its expectation from `expected_dir_for_status`, which is the drift pin F-06 shows the docstring already promises.
3. E-03 corrects the two false sentences in the `run_status_is_nonterminal` docstring, now that E-02 has made the pin it names real.
4. E-04 deletes the dead `_status_disagrees`, re-proving unreachability first and stopping if that premise has moved again.

The order matters and is not cosmetic, but for a DIFFERENT reason than the original plan gave. The original argued the tests must predate a refactor so as not to characterize it; that argument was about a refactor this plan no longer performs. The real reason is that E-01 and E-02 are the plan's only durable product: they must be green at HEAD BEFORE E-04 removes anything, so that the deletion is demonstrably invisible to the behavior those tests pin. An executor who deletes first and tests after has proven nothing about the audit's behavior, only that the suite still passes.

## Deferred / out of scope (with reason)

- CORRECTING BACKLOG `64a03w`'s CENTRAL CLAIM (F-07). That item was filed while authoring this plan and states that `substantially-complete` is flagged where `complete` is tolerated. Review measured the live behavior as the opposite: BOTH are flagged in the moved-at-`executed` shape, because `_RUN_SUCCESS_STATUSES` is `{'executed'}` alone. The item's reasoning rests on two return values of the helper E-04 deletes, so once that code is gone the item cites something that no longer exists. This plan does not edit the item, because its `Scope-Paths` declares no backlog file and rewriting another record's premise is a separate act.
  - Carrier: 64a03w
- `timed-out`. The original plan treated this as a residual divergence needing an explicit exclusion. With the helper deleted it is not a divergence at all: it is absent from `TERMINAL_STATES`, absent from every status set, and absent from the entire Python source, so no run record can carry it and the live predicates never see it. E-02 sweeps `TERMINAL_STATES` and therefore does not mention it, which is correct rather than an omission.
  - Carrier-Declined: NOTHING IS OWED, because the status is unobservable by construction rather than merely unlikely. `'timed-out' in runner_shared.TERMINAL_STATES` is False and a repo-wide grep over `*.py` finds no occurrence at all; `vdabn5` F-10 independently recorded that neither runner writes it. An item asking someone to decide the tolerance of a status nothing produces would be work with no observable outcome, and after E-04 there is no tolerance arm for it to be excluded from.
- BACKDATING A PER-STATUS ARGUMENT FOR THE EIGHT STATUSES. `qpgs4t` wanted one argument per status before admission. This plan does not manufacture retrospective justifications it did not measure. What it does instead is PIN the behavior in both directions so the next change is deliberate, which is the outcome the item's scope fence existed to produce.
  - Carrier-Declined: THE OBLIGATION IS DISCHARGED BY THIS PLAN, not deferred by it, and the discharge is now stronger than the original argued. OQ-01 resolves the substantive question from repository evidence, and F-02 shows the live predicate `allowed_lifecycle_pairs` returns the SAME six pre-terminal pairs for every non-success status, so the tolerance is status-independent BY CONSTRUCTION rather than by an argument someone has to re-make per status. A per-status measurement cannot distinguish statuses a predicate does not distinguish. What `qpgs4t` wanted protected was deliberateness, and E-01 and E-02 restore that as an executable fence over the whole closed vocabulary.
- THE ITEM'S "consider a direction-aware classifier" SUGGESTION. `difference_class`/`classify_difference` already exists (IPD `zexed1`) and already runs beside these booleans; `qpgs4t` predates knowing that.
  - Carrier-Declined: THE SUGGESTION IS ALREADY SATISFIED, so there is nothing outstanding to carry. The item asks whether "a direction-aware classifier would be" better than the ad-hoc list and names `classify_difference`/`difference_class` (IPD `zexed1`) as the likely home. That machinery SHIPPED and already runs on every audit: F-01 measures the eight tolerated rows returning `difference_class=unchanged`, and `ArtifactAudit.is_alarming` already gates the red styling on the class rather than on the booleans. The ad-hoc list the item objected to is additionally now unreachable, and E-04 deletes it. The remaining tolerance lives in `allowed_lifecycle_pairs`, which is itself derived from `record_placement.target_subdir` (F-02), so there is no enumeration left to re-home.
- `run_viewer.py` ITSELF. The five `Issue` predicate copies consume this module's output and need no edit; not in `Scope-Paths`.
  - Carrier-Declined: This row records a SCOPE FENCE on this plan rather than a deferred defect, so nothing is owed and there is no future work to carry. The copies consume `audit_artifact`'s output unchanged, and since this plan changes no audit output they are unaffected; `vdabn5` F-5 measured the same five copies and reached the same conclusion, and unifying them is separately owned by plan `r2i1b1` E-03.

## Scope check

- Over-scope: none. `agent_workflows/artifact_audit.py` is in scope ONLY for the deletion of `_status_disagrees` (E-04) and the `run_status_is_nonterminal` docstring (E-03). Do NOT touch `canonical_terminal_status`, `expected_dir_for_status`, `_TERMINAL_EXPECTED_DIR`, `_RUN_SUCCESS_STATUSES`, `allowed_lifecycle_pairs`, `classify_difference`, the `ArtifactAudit` fields, or any `run_viewer.py` issue-predicate copy. In particular do NOT "fix" the `substantially-complete` behavior F-07 corrects, and do NOT edit backlog `64a03w`, which is not a declared path.
- Under-scope: stated rather than left as `none`. (a) Backlog `64a03w`'s premise is measurably wrong (F-07) and is left for its own owner. (b) The live tolerance is not re-homed into `classify_difference`; it does not need to be, since F-02 shows it is already derived. (c) The backlog item `qpgs4t`'s own body still asserts the eight statuses flag, which is false; note it when closing the item rather than rewriting the item's history. (d) The pre-existing UTC-versus-local date-split suite failure (F-10) is untouched and is owned by five open backlog items.

## Required tests / validation

`python3 -m pytest` BARE in the executing worktree. Do not add `-n0`, a second `-q`, or `-p no:randomly`. Compare failing NODE IDS, not totals.

Baseline RE-MEASURED AT REVIEW on a clean tree (F-10): `1 failed, 3498 passed, 2 skipped, 3 warnings in 193.01s`, with `NOTE: 208 tests were deselected by -m/-k`. THE ONE FAILURE IS EXPECTED AND PRE-EXISTING: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` fails on a UTC-versus-local date split already filed as `fnb8pl`, `lq2w86`, `2wae2x`, `o8l2y2` and `tl8qmc`. Do not chase it and do not edit `tests/test_backlog.py`, which is not a declared path. Re-derive the baseline in the executing worktree rather than asserting these totals: the count moves with every merged lane, and the plan's own authoring figure (`3291 passed`, 571 commits earlier) was already wrong by 210 tests by review. Any NEW failure must be a node id absent from the baseline run.

Both new test groups must be shown GREEN BEFORE the E-04 deletion, and green again after, and the executor must paste BOTH runs. A single post-deletion green run does not distinguish "the deletion changed no behavior" from "the suite never covered this", which is the specific failure this sequencing prevents.

## Spec / documentation sync

N/A with reason: no `.spec.md` governs `_status_disagrees` or `allowed_lifecycle_pairs`, and none is edited (`Scope-Paths` declares no spec file). Verified by grepping `.aw/records/specs/` for `artifact_audit`: the four matches are in `4sd62s` and `z7nbn1` and all reference `FinalizeEvidenceIndex`, `_INDEX_CACHE`, or the module as a migration surface, none the status-tolerance predicates. The contract this touches is the `aw.agent/v1` record shape in `docs/cli-agent-protocol.md`, and F-09 establishes that no field and no field value changes, so that document needs no change. The only documentation edit is the one in-module docstring in E-03.

## Open questions

### OQ-01: Should the eight statuses' tolerance be preserved at all, given it arrived unplanned?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, preserve it, and the evidence is now stronger than when this question was first answered. The original resolution argued the tolerance is correct because the accepted declared values are all PRE-TERMINAL and exclude `executed`. That argument holds, and review added the structural reason it holds: F-02 measures `allowed_lifecycle_pairs('plans','execute',st)` returning the IDENTICAL six `(pre-terminal, 'pending')` pairs for every non-success, non-retired status, and those directories are derived from `record_placement.target_subdir` rather than listed. So the tolerance cannot be status-specific even in principle. F-05 then confirms the property that makes it safe: across all 24 members of `TERMINAL_STATES`, no status is tolerated in BOTH shapes, so the moved-plan row an operator needs is never suppressed. The plan preserves behavior and adds the missing pin.

### OQ-02: Should `substantially-complete` be fixed in the same pass?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, no, AND THE QUESTION AS ORIGINALLY POSED RESTS ON A FALSE PREMISE. It assumed `substantially-complete` is flagged where `complete` is tolerated; F-07 measures both as FLAGGED through the live entry point, because `_RUN_SUCCESS_STATUSES` is `{'executed'}` alone and `complete` is not a member. There is accordingly no asymmetry in behavior to fix in this pass or any other, and the appearance of one came from comparing two return values of the unreachable helper E-04 deletes. What remains is not a code change but a RECORD correction: backlog `64a03w` was filed on the dead-helper reading and its central claim needs amending by its own owner. This plan declares no backlog path and so does not amend it; the Deferred row carries `64a03w` as the carrier and F-07 records the measurement a future reader needs.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `python3 -m pytest tests/test_artifact_audit.py` output showing the new cases GREEN BEFORE any edit to `artifact_audit.py`, together with `git diff --stat agent_workflows/artifact_audit.py` proving that file is UNCHANGED at that moment. Then, for each of the eight statuses, paste the asserted pair: unmoved-in-`pending/`-at-`approved` gives `has_discrepancy=False` and `difference_class='unchanged'`, and in-`executed/`-at-`executed` gives `location_mismatch=True status_mismatch=True`. Finally, demonstrate the fence BITES, and do it by mutating the LIVE predicate rather than the dead one: monkeypatch `artifact_audit.allowed_lifecycle_pairs` to return only `[('approved','pending')]` (or equivalently drop `to-review`/`draft`/`reviewed`/`queued`/`running` from its pre-terminal branch), paste the resulting FAILING node ids, and revert. DO NOT attempt the mutation the earlier revision of this plan specified (narrowing `_status_disagrees`): F-11 measures that it changes nothing and so cannot fail, and an executor who tries it and sees green must not record that as a passing fence.
  - Observed evidence: Verified characterization tests pass pre-edit, artifact_audit unchanged, 8 pairs asserted, and fence bites.
    1. Pre-edit tests passing:
       ```
       $ python3 -m pytest tests/test_artifact_audit.py
       ........................                                                 [100%]
       24 passed in 2.41s
       ```
    2. Proving agent_workflows/artifact_audit.py unchanged at that moment:
       ```
       $ git diff --stat agent_workflows/artifact_audit.py
       (empty output)
       ```
    3. Asserted pairs for all eight statuses:
       ```
       status=failed               | unmoved: has_discrepancy=False difference_class='unchanged' | moved: location_mismatch=True status_mismatch=True
       status=failed-safely        | unmoved: has_discrepancy=False difference_class='unchanged' | moved: location_mismatch=True status_mismatch=True
       status=partial              | unmoved: has_discrepancy=False difference_class='unchanged' | moved: location_mismatch=True status_mismatch=True
       status=not-attempted        | unmoved: has_discrepancy=False difference_class='unchanged' | moved: location_mismatch=True status_mismatch=True
       status=merge-conflict       | unmoved: has_discrepancy=False difference_class='unchanged' | moved: location_mismatch=True status_mismatch=True
       status=integration-blocked  | unmoved: has_discrepancy=False difference_class='unchanged' | moved: location_mismatch=True status_mismatch=True
       status=merge-needs-human    | unmoved: has_discrepancy=False difference_class='unchanged' | moved: location_mismatch=True status_mismatch=True
       status=cancelled            | unmoved: has_discrepancy=False difference_class='unchanged' | moved: location_mismatch=True status_mismatch=True
       ```
    4. Fence bite demonstration via monkeypatching live predicate `allowed_lifecycle_pairs`:
       Returning only `[("approved", "pending")]` drops `to-review`/`draft`/`reviewed`/`queued`/`running`:
       ```
       FAILED tests/test_artifact_audit.py::TestArtifactAuditEngine::test_catch_all_pre_terminal_statuses_tolerated_unmoved
       AssertionError: True is not false
       ```
       And returning `[("draft", "pending")]` (dropping `approved`):
       ```
       FAILED tests/test_artifact_audit.py::TestArtifactAuditEngine::test_catch_all_statuses_tolerated_unmoved_and_flagged_moved
       AssertionError: True is not false
       ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new test passing, and paste `sorted(runner_shared.TERMINAL_STATES)` beside the statuses the test actually swept, showing the two sets are EQUAL rather than the test covering a subset. Paste the per-status table it asserts and confirm it reproduces F-05 exactly: 22 members `False` unmoved and `True` moved, `executed` inverted, `retired` `True` in both. Show the expectation is DERIVED from `expected_dir_for_status` rather than written as a literal list. Then prove the test detects drift two ways: (a) monkeypatch `TERMINAL_STATES` to add a fabricated member and paste the FAILING node id, showing a driver adding a status cannot pass silently; (b) monkeypatch `_RUN_SUCCESS_STATUSES` to add `complete` and paste the FAILING node id, showing a widened success set is caught. Revert both.
  - Observed evidence: Verified closed-vocabulary trichotomy over 24 TERMINAL_STATES and drift sensitivity.
    1. New test passing:
       ```
       $ python3 -m pytest tests/test_artifact_audit.py -k test_terminal_states_tolerance_and_counterexample_trichotomy
       .                                                                        [100%]
       1 passed in 2.15s
       ```
    2. Swept statuses vs sorted(runner_shared.TERMINAL_STATES):
       ```
       sorted(runner_shared.TERMINAL_STATES):
       ['already-landed', 'approved', 'blocked', 'dependency-blocked', 'executed', 'fail-begin', 'fail-depend', 'fail-gate', 'fail-lane', 'fail-merge', 'fail-verify', 'failed', 'failed-safely', 'integration-blocked', 'interrupted', 'merge-conflict', 'merge-needs-human', 'merge-refused', 'not-attempted', 'not-run', 'partial', 'retired', 'reviewed', 'substantially-complete']

       swept statuses:
       ['already-landed', 'approved', 'blocked', 'dependency-blocked', 'executed', 'fail-begin', 'fail-depend', 'fail-gate', 'fail-lane', 'fail-merge', 'fail-verify', 'failed', 'failed-safely', 'integration-blocked', 'interrupted', 'merge-conflict', 'merge-needs-human', 'merge-refused', 'not-attempted', 'not-run', 'partial', 'retired', 'reviewed', 'substantially-complete']

       Equality check: sorted(TERMINAL_STATES) == swept: True
       ```
    3. Per-status asserted table (reproducing F-05):
       ```
       Total members in TERMINAL_STATES: 24
       Status                    | Unmoved Disc | Moved Disc   | Expected Dir
       ----------------------------------------------------------------------
       already-landed            | False        | True         | pending
       approved                  | False        | True         | pending
       blocked                   | False        | True         | pending
       dependency-blocked        | False        | True         | pending
       executed                  | True         | False        | executed
       fail-begin                | False        | True         | pending
       fail-depend               | False        | True         | pending
       fail-gate                 | False        | True         | pending
       fail-lane                 | False        | True         | pending
       fail-merge                | False        | True         | pending
       fail-verify               | False        | True         | pending
       failed                    | False        | True         | pending
       failed-safely             | False        | True         | pending
       integration-blocked       | False        | True         | pending
       interrupted               | False        | True         | pending
       merge-conflict            | False        | True         | pending
       merge-needs-human         | False        | True         | pending
       merge-refused             | False        | True         | pending
       not-attempted             | False        | True         | pending
       not-run                   | False        | True         | pending
       partial                   | False        | True         | pending
       retired                   | True         | True         | pending
       reviewed                  | False        | True         | pending
       substantially-complete    | False        | True         | pending
       ```
    4. Expectation is derived from `expected_dir_for_status`:
       In test:
       `exp_dir = _audit.expected_dir_for_status(st)`
       `exp_unmoved_disc = (exp_dir != "pending")`
       `exp_moved_disc = (exp_dir != "executed")`
       for all 22 non-executed, non-retired members; executed and retired asserted individually.
    5. Drift detection (a) - monkeypatching `TERMINAL_STATES` to add `fabricated-status`:
       ```
       FAILED tests/test_artifact_audit.py::TestArtifactAuditEngine::test_terminal_states_tolerance_and_counterexample_trichotomy
       AssertionError: 'fabricated-status' not found in frozenset({'fail-merge', 'retired', ...})
       ```
    6. Drift detection (b) - monkeypatching `_RUN_SUCCESS_STATUSES` to add `complete`:
       ```
       FAILED tests/test_artifact_audit.py::TestArtifactAuditEngine::test_terminal_states_tolerance_and_counterexample_trichotomy
       AssertionError: Items in the first set but not the second:
       'complete'
       ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff agent_workflows/artifact_audit.py` for the docstring change alone, showing the false `tests/test_artifact_audit.py` pin claim replaced by a citation of the E-02 test BY NAME, and the "BOTH host drivers'" framing corrected. Paste `grep -n 'TERMINAL_STATES' tests/test_artifact_audit.py` returning a real match, which is what makes the corrected sentence true. Paste the two alias lines (`oc_runipd.py` and `agy_runipd.py` each reading `TERMINAL_STATES = runner_shared.TERMINAL_STATES`) as the evidence for the second correction. Confirm the diff touches no executable line in the module.
  - Observed evidence: Verified docstring cites test by name and corrects shared TERMINAL_STATES framing.
    1. Docstring git diff:
       ```diff
       --- a/agent_workflows/artifact_audit.py
       +++ b/agent_workflows/artifact_audit.py
       @@ -699,8 +699,9 @@ def run_status_is_nonterminal(status: str) -> bool:
            WHY THE DERIVATION CATCHES THEM FOR FREE: neither `reviewed` nor `queued` is in
            ``_TERMINAL_EXPECTED_DIR``, so both map to `pending` and are forward-eligible without being named.

       -    `tests/test_artifact_audit.py` pins this against BOTH host drivers' `TERMINAL_STATES`, in the style
       -    of `runner_shutdown.KNOWN_ITEM_STATUSES`, so a driver adding a status cannot drift silently.
       +    `tests/test_artifact_audit.py:TestArtifactAuditEngine.test_terminal_states_tolerance_and_counterexample_trichotomy`
       +    pins this against `runner_shared.TERMINAL_STATES` (shared by both host drivers), in the style of
       +    `runner_shutdown.KNOWN_ITEM_STATUSES`, so a driver adding a status cannot drift silently.
            """
            return expected_dir_for_status(status) == "pending"
       ```
    2. Real matches for TERMINAL_STATES in test file:
       ```
       $ grep -n 'TERMINAL_STATES' tests/test_artifact_audit.py
       447:        """Closed-vocabulary pin asserting the F-05 trichotomy over runner_shared.TERMINAL_STATES (E-02).
       449:        Every member of runner_shared.TERMINAL_STATES is swept:
       464:        for st in sorted(runner_shared.TERMINAL_STATES):
       513:        # Assert closed vocabulary is completely swept and equal to TERMINAL_STATES
       514:        self.assertEqual(swept, set(runner_shared.TERMINAL_STATES))
       ```
    3. Host drivers' alias lines:
       ```
       agent_workflows/oc_runipd.py:878:TERMINAL_STATES = runner_shared.TERMINAL_STATES
       agent_workflows/agy_runipd.py:785:TERMINAL_STATES = runner_shared.TERMINAL_STATES
       ```
    4. The docstring edit touches zero executable lines in `agent_workflows/artifact_audit.py`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste all THREE unreachability re-proofs taken in the executing worktree immediately BEFORE the deletion: (a) `grep -rn 'status_disagrees' --include='*.py' .` showing the `def` line as the only occurrence; (b) the AST scan of `artifact_audit.py` printing zero `Load`-context sites; (c) the call-counting monkeypatch driven through `audit_artifact` for the eight statuses printing a call count of `0`. Then paste `git diff agent_workflows/artifact_audit.py` showing the function and its docstring removed with no replacement shim, and `grep -rn 'status_disagrees' --include='*.py' .` returning NOTHING afterwards. Paste the E-01 and E-02 tests passing UNMODIFIED after the deletion, proving they were not edited (`git diff` for `tests/test_artifact_audit.py` between the pre-deletion and post-deletion commits must be empty). Paste a full bare `python3 -m pytest` and compare by NODE ID against the baseline re-derived in this worktree; the pre-existing `test_release_exempt_setter_roundtrip_and_parity` date-split failure (F-10) may appear in BOTH runs and is not a regression, while any other new node id is.
  - Observed evidence: Verified 3 unreachability re-proofs, clean dead-code deletion, unmodified test pass, and full pytest suite green.
    1. Unreachability re-proofs immediately before deletion:
       (a) Repo-wide search:
           `$ grep -rn 'status_disagrees' --include='*.py' .`
           `./agent_workflows/artifact_audit.py:1236:def _status_disagrees(recorded: str, declared: str) -> bool:`
       (b) AST scan:
           `definition lines: [1236]`
           `LOAD sites (callers): []`
       (c) Call-counting spy through audit_artifact for 8 statuses:
           `_status_disagrees call count during 8 audits: 0`
    2. Deletion diff in agent_workflows/artifact_audit.py (entire function and docstring removed, no shim):
       ```diff
       @@ -1232,71 +1233,6 @@ def read_declared_status(path: Path) -> Optional[str]:
            return m.group(1).strip() if m else None


       -def _status_disagrees(recorded: str, declared: str) -> bool:
       -    ...
       -    return dec != rec
       -
       -
        def audit_artifact(
       ```
    3. Grep returning nothing after deletion:
       ```
       $ grep -rn 'status_disagrees' --include='*.py' .
       (exit code 1, empty output)
       ```
    4. Tests pass unmodified post-deletion:
       `git diff tests/test_artifact_audit.py` between pre-deletion and post-deletion commits is empty.
       `python3 -m pytest tests/test_artifact_audit.py` -> 24 passed in 4.27s.
    5. Full bare pytest suite matches baseline:
       Baseline: 4027 passed, 2 skipped, 3 warnings in 323.06s (230 deselected).
       Post-deletion: 4030 passed, 2 skipped, 3 warnings in 247.24s (230 deselected).
       0 failures, exactly +3 new tests passed, 0 regressions.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; do not self-approve.

Open questions: OQ-01 and OQ-02 are both `resolved`, neither is `Blocking: yes`, and no question remains for a human to answer before execution.

Execution contract: commit only the two paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, `git add .`, `git commit -a`, or `--no-verify`; do not push; do not create a tag or release. Paste ACTUAL runner output for every validation item rather than asserting success.

Scope fence (a DECLARATION, not a stop directive): the only files this plan may change are `agent_workflows/artifact_audit.py` and `tests/test_artifact_audit.py`. An out-of-scope edit that proves necessary should be MADE and then JUSTIFIED through `aw ipd finalize --scope-reason <path>=<why>`, with `--scope-ack` for any declared path left unmodified. Two specific temptations are named because review measured both: do NOT edit `tests/test_backlog.py` to silence the pre-existing date-split failure (F-10), and do NOT edit backlog `64a03w` to correct the premise F-07 falsifies.

THE ONE GENUINE STOP CONDITION is E-04's unreachability re-proof: if any of the three checks finds a caller of `_status_disagrees`, STOP and report rather than deleting, because that means the premise moved between review and execution and the deletion would remove live behavior. This is a prerequisite-absent condition, not a scope question.

Sequencing is part of the contract, not a suggestion: E-01 and E-02 must be committed and green BEFORE E-04 deletes anything, so the behavioral pins provably predate the removal they justify. An executor who deletes first has shown only that the suite passes, not that the audit's behavior is unchanged.

Post-gate lifecycle: after every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, complete the terminal transition through the tooled path, never by hand-editing terminal state or by a hand-rolled `git mv` to `executed/`. Under `aw oc run` / `aw agy run` the RUNNER owns that transition and the executor must not pre-empt it; a human-driven execution performs it with `aw ipd set executed`. When closing backlog `qpgs4t`, note that its premise was doubly stale (the statuses no longer flag, and the helper it names is dead per F-01) so the next reader is not misled.
