# Review findings: plan yx9xsa

- Subject-Id: yx9xsa
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree at HEAD `de9b241c`. Structural preflight `aw ipd lint --phase
author --agent` returned `clean` BEFORE any revision and `--phase review-finalize --agent` returns
`clean` after. No pre-review snapshot was needed: `git status --porcelain` was empty.

THE PLAN'S CENTRAL MEASUREMENT IS EXACTLY RIGHT AND I RE-DERIVED IT RATHER THAN TRUSTING IT. The
probe reproduces `22 failed` on `tests/test_ipd_lifecycle_cli.py`, and F-1's per-class breakdown is
correct cell for cell (FinalizeTests 5, TheORDINARYFinalize... 4, RollbackFailureSemanticsTests 4,
ReconciliationTests 3, AdditiveScopeWideningTests 3, DelegationAndBypassRemovalTests 2,
ParenthesizedActorIsRefusedBeforeAnyWrite 1). The class census is right (11 classes, exactly one
declaration, at `BeginCliTests`), F-3's dead-file claim is right, and F-4's correction of the backlog
item's stale 42 is right. The authored `15 passed` is now `16` only because commit `7bed5478` added a
test after the authoring HEAD; the plan's expected `37 passed` is likewise 38 now, which is why I
replaced both counts with a re-derivation requirement rather than a new number that will rot the same
way.

I ALSO VERIFIED THE FIX ITSELF WORKS, on one class and then on the whole file, because a plan whose
entire deliverable is a one-line fixture change should not reach approval on a theory of the
mechanism. Adding the declaration to `FinalizeTests.setUp` alone turns its 5 failures into
`5 passed`; applied to all ten classes the file is `38 passed` under the probe. I reverted every code
edit afterwards, so the tree I hand back is unmodified apart from the plan and this record.

**THE DEFECT IS LIVE TODAY, WITH NO PLUGIN, UNDER A RUNNER THE REPOSITORY ITSELF SHIPS.** This is the
most consequential thing I found, and it strengthens rather than weakens the plan. Both the authored
Concern and the backlog item frame `conftest.py`'s scrub as the general mask, so the failure is only
observable through a contrived probe. But that scrub is in a PYTEST conftest, and `python3 -m unittest`
never imports it. The `Makefile` ships `test-serial: python3 -m unittest discover -s tests -t .`, and
`CONTRIBUTING.md` documents it as the minimal-environment fallback. Measured:
`AW_EXECUTION_ROLE=worker python3 -m unittest tests.test_ipd_lifecycle_cli` gives
`Ran 38 tests in 3.619s` / `FAILED (failures=27)` with `AW-LIFECYCLE-ROLE-001` in the messages, and
`env -u AW_EXECUTION_ROLE` on the same command gives `OK`. That is not a hypothetical: a runner lane
turn exports the marker, so any agent told to use the serial fallback in a lane sees 27 red failure
records today. (27 records over 22 distinct methods, because a `subTest` reports per sub-case; I
checked that the method set is the same 22.) The plan's verification was pytest-only and therefore
structurally blind to the case where the bug actually bites, so E-04 now runs `unittest` too.

**THE SUITE CONTAINS ONE MORE INSTANCE OF THE SAME DEFECT AND THE AUTHORED SCOPE WOULD HAVE SHIPPED
WITHOUT IT.** The plan probed one file; I probed the whole suite, which costs 38 seconds. Exactly one
failure lies outside `test_ipd_lifecycle_cli.py`:
`tests/test_orchestrator_retirement.py::TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence`,
which drives `LC.finalize` on the ambient environment and gets the role refusal (exit 2) where it
asserts `EXIT_FINDINGS` (1). The fix is one line on the shared `RollupTransitionCase.setUp`, which is
the `setUp` for 15 subclasses; measured, the whole file then reports `42 passed` under the probe. Two
reasons this belongs here rather than in a follow-up. First, it is the same one-line fix found in the
same sweep. Second and decisively, this plan's own strongest verification is a suite-wide probe
reporting clean, and with this test left red that evidence cannot exist, so the plan would have had to
either narrow its claim or explain away a failure it knew about.

AND I CHECKED THE OBVIOUS WAY THAT ADDITION COULD DO HARM. `tests/test_orchestrator_retirement.py`
contains `TheWorkerRoleIsRefused`, whose entire purpose is the refusal a coordinator declaration
suppresses. It is safe, and for a principled reason rather than by luck: it passes an EXPLICIT
`env={LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER}` to every call, which is exactly the shape
`tests/support.py`'s `worker_role` docstring prescribes so that a refusal test cannot pass vacuously
off an ambient value. I ran it under the probe with the base-class declaration in place and it passes.
V-02 now requires that specific run, so an executor cannot satisfy E-02 in a way that guts it.

**THE CONFTEST COMMENT HAS THREE DEAD REFERENCES, NOT TWO, AND THE AUTHORED ITEM WOULD HAVE PRESERVED
THE WORST ONE.** F-3 names the two hits on `tests/test_role_declaration_guard.py`. The same trim
commit `19313eed` also deleted `tests/test_worker_role_refusal.py`, which the block cites in its
`WHY NOT RELAX THE GUARD TEST` paragraph, and the `HONEST LIMITS` paragraph builds a claim on
`test_driver_own_process_is_not_worker_role`, which exists nowhere in the tree. The authored E-item
said to keep that paragraph "minus its dead cross-reference" - but its SUBJECT is what is gone, so the
result would be shipped code asserting the repository has a live guard for the scrub when it has none.
E-03 now replaces the paragraph with the true statement (no shipped test asserts the invariance, which
is why a one-off probe is the check) and V-03 greps for all four strings rather than two.

A NOTE ON WHAT THIS PLAN DOES NOT BUY, since the maintainer will want it visible at approval. With
structural guards declined AND the guard file that once asserted scrub invariance deleted, nothing
stops a future test class silently inheriting the role again. That is a maintainer decision recorded on
2026-09-26, not an oversight, so I recorded the residual in the Deferred section and did not argue with
it. I also declined to widen scope into `CONTRIBUTING.md` for the `test-serial` documentation gap; the
fact now lives in the `conftest.py` comment beside the scrub it describes.

ON CONCURRENCY, which matters because two live plans touch one file. Pending plan `a6xbso`
(`- Status: reviewed`) declares `conftest.py` and edits the same comment region, and its own review
recorded this exact stale cross-reference as its F-12 with "not ours to fix". So the correction is
genuinely unowned until this plan takes it, which is right, but the two edits collide. The Scope check
and a gate stop condition now tell whichever executes second to rebase rather than overwrite. There is
no overlap with sibling `tcx2ok` (testhyg Order 02), whose declared paths I checked.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | UNDER-SCOPE | E. testing and verification; F. honest documentation | `Makefile` `test-serial: python3 -m unittest discover -s tests -t .`; `conftest.py`'s `os.environ.pop("AW_EXECUTION_ROLE", None)` is in a PYTEST conftest; measured `AW_EXECUTION_ROLE=worker python3 -m unittest tests.test_ipd_lifecycle_cli` -> `Ran 38 tests in 3.619s` / `FAILED (failures=27)`, and `env -u AW_EXECUTION_ROLE` on the same command -> `OK` | **THE DEFECT IS LIVE UNDER `make test-serial` TODAY, WITH NO PLUGIN, AND THE PLAN'S VERIFICATION COULD NOT SEE IT.** The Concern treats the scrub as the general mask, making the failure look reachable only through a contrived probe. `unittest` loads no conftest, so the repository's own documented serial fallback is red on any shell exporting the marker, which is the ordinary condition inside a runner lane turn. A pytest-only verification is structurally blind to the one case where the bug actually bites. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern rewritten with the `unittest` measurement; Goal now names both documented runners; a Step 0 convention records that the scrub is pytest-only; E-04 adds the `unittest` before/after leg; V-04 requires its two summary lines; E-03 requires the `conftest.py` comment to state the limit. Recorded as plan F-5. |
| PR-902 | HIGH | UNDER-SCOPE | D. anti-regression; E. testing | `PYTHONPATH=<workspace>/roleplug python3 -m pytest -p reassert_worker` -> `23 failed, 2575 passed, 2 skipped, 3 warnings in 37.82s`; the 23rd is `tests/test_orchestrator_retirement.py::TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence` failing `AssertionError: 2 != 1 : AW-LIFECYCLE-ROLE-001: ...`; with one declaration on `RollupTransitionCase.setUp` that file measures `42 passed` under the same probe | **THE SUITE HAS ONE MORE INSTANCE OF THE IDENTICAL DEFECT AND THE PLAN SCOPED ONE FILE.** The plan probed only its target file. A whole-suite probe (38s) finds exactly one other failure, fixable by one line on a shared base class covering 15 subclasses. Beyond completeness, it is load-bearing for this plan's own evidence: the strongest verification available here is a suite-wide probe reporting clean, which cannot exist while that test stays red. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `tests/test_orchestrator_retirement.py` added to `- Scope-Paths:` and to Scope; new E-02 makes the single base-class declaration with an explicit prohibition on per-subclass `setUp` and on touching `TheWorkerRoleIsRefused`; V-02 requires the file's before/after under the probe AND a standalone passing run of `TheWorkerRoleIsRefused`; E-04 adds the suite-wide probe leg. Recorded as plan F-6. |
| PR-903 | MEDIUM | IN-SCOPE | A. correctness (a false statement would ship); F. honest documentation | `git ls-files tests/test_worker_role_refusal.py tests/test_role_declaration_guard.py` -> empty for both; `git show 19313eed --name-only` lists both deleted; `grep -rn "def test_driver_own_process_is_not_worker_role" --include=*.py .` -> nothing; `conftest.py` cites the two files at four lines and builds its `HONEST LIMITS` paragraph on that test | **THE COMMENT HAS THREE DEAD REFERENCES AND THE AUTHORED ITEM WOULD HAVE KEPT THE WORST.** E-02-as-authored said to keep the `test_driver_own_process_is_not_worker_role` paragraph "minus its dead cross-reference", but that test does not exist, so the retained paragraph would assert the repository has a live guard for the scrub when it has none. Fixing two of three stale citations while preserving a claim about a nonexistent test is a worse outcome than leaving the block alone, because it looks freshly verified. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 rewritten to name all three dead references, to REPLACE rather than trim the paragraph with the true statement (no shipped test asserts the invariance, which is why the probe is the check), and to add the pytest-only sentence; V-03 greps all four strings and requires the replacement to be described in words. Recorded as plan F-8. |
| PR-904 | MEDIUM | IN-SCOPE | E. verification (a recipe an executor may be unable to run) | `6vozur` E-05 text ("NOT the hardcoded `/tmp/opencode/roleplug` the authoring session used ... an isolated lane may not be able to write it"), its review PR-703, and its V-05 evidence recording `Plugin path: .aw/state/roleplug/_aw_reassert_role.py (inside workspace)`; `.aw/.gitignore` ignores `/state/`; this review's own tooling refused the `/tmp/opencode` path | **THE PROBE RECIPE HARDCODES A MACHINE-LOCAL PATH OUTSIDE THE WORKSPACE, WHICH THIS REPOSITORY HAS ALREADY MEASURED AS UNWRITABLE FROM A LANE.** An executed plan hit exactly this, had its review flag it, and relocated to a gitignored in-workspace path. Repeating the same recipe re-imports a solved defect, and the executor's likely workaround (an env-var export) is a measured false pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 requires the plugin be written inside the workspace under gitignored `.aw/state/roleplug/`, citing `6vozur`; a Step 0 convention records it; the gate's commit paragraph names that path instead of `/tmp`. Recorded as plan F-7. |
| PR-905 | MEDIUM | IN-SCOPE | E. verification (evidence that does not support its claim) | `conftest.py` scrubs the marker at import, so a bare suite is green before and after; `6vozur` F-7 measured `AW_EXECUTION_ROLE=worker python3 -m pytest` reporting `6 passed` against an UNFIXED file | **THE PLAN LEANED ON A BARE GREEN SUITE, WHICH IS MEANINGLESS HERE, AND DID NOT WARN AGAINST THE ONE SHORTCUT THAT LIES.** Every behavior this plan changes is invisible to a bare pytest run by construction, so "bare suite green" is a no-regression check only. Worse, the obvious simplification of the probe reports green against the unfixed tree, and an executor taking it would conclude the findings were wrong. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | An explicit honest limit added to Required tests; V-04 requires the bare suite be LABELLED a no-regression check and states the env-var spelling satisfies no part of the item; the gate's honesty rule names both measured false passes. |
| PR-906 | MEDIUM | IN-SCOPE | G. plan executability (a live count as an acceptance bar) | Authored E-01 `Expected outcome` "all 11 classes"; E-03 `Expected outcome` "after `0 failed` (37 passed)"; measured today `38 tests collected`, because `7bed5478` added `test_rollback_restores_recorded_index_entry_not_head` after the authoring HEAD; `61ef21d8` is NOT an ancestor of the review HEAD | **TWO SUCCESS CRITERIA WERE AUTHORED AS COUNTS THAT HAD ALREADY DRIFTED BEFORE REVIEW.** The expected `37 passed` is wrong at review HEAD and would present an executor with an apparent mismatch on a correct fix; the class count is a live population in a file under active edit. The repository's re-derivation convention applies. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01's outcome now demands the declaration count EQUAL a freshly derived class count, with 11 stated as context; E-04's outcome states the PROPERTY first and labels every number as review context to be re-derived; the Findings preamble records both HEADs and the intervening commit. |
| PR-907 | LOW | UNDER-SCOPE | G. plan executability (execution contract) | Authored gate: no stop conditions, `aw commit <plan>` with a placeholder, "the runner owns it in a lane" without the executor branch, no `git mv` prohibition; `a6xbso` (`- Status: reviewed`) declares `conftest.py` and its review F-12 names this same comment defect as not-its-to-fix | THE GATE OMITTED THE CONCURRENCY HAZARD AND PARTS OF THE STANDARD CONTRACT. Two live plans edit the same `conftest.py` comment region, which is a real collision in a shared checkout, and the plan said nothing. The finalize sentence also named only the runner's ownership without the executor branch, and carried no prohibition on a hand-rolled `git mv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gained two stop conditions (a non-reproducing BEFORE probe, and a concurrent `conftest.py` edit by `a6xbso` with an instruction to rebase and report), the real plan id in the commit command, the conditional runner/executor finalize ownership with the `git mv` prohibition, and a WHAT A HUMAN IS APPROVING paragraph matching the widened scope. A Scope check CONCURRENCY NOTE records the overlap. |
| PR-908 | LOW | IN-SCOPE | F. honest documentation | Plan title vs. the widened `- Scope-Paths:`; the Deferred section's single row; `check_engine.evaluate_durable_carrier` semantics for a declined obligation | THE TITLE NAMED ONE FILE AND "TEN CLASSES" AFTER SCOPE GREW TO THREE FILES, AND ONE RESIDUAL WENT UNRECORDED. A title that under-describes a plan misleads every index that lists it. Separately, review found the deleted guard harness (the thing that once asserted scrub invariance) is not restored by this plan and had no recorded disposition here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Title broadened to name both test files; a second Deferred row records the guard-file restoration as out of scope with a `Carrier-Declined:` pointing at `6vozur` F-8 where it already lives; the first Deferred row now states the residual risk the maintainer accepted (nothing prevents a future class inheriting again). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | A second file carries the same defect (PR-902). Widen this plan, or file a follow-up? | WIDEN: add `tests/test_orchestrator_retirement.py` and one base-class declaration. | (a) Follow-up backlog item: rejected, it is the same one-line fix found in the same sweep, and it would leave this plan unable to produce its own best evidence (a clean suite-wide probe). (b) Declare every one of the 15 subclasses individually for symmetry with the other file: rejected, the shared `setUp` exists precisely so one declaration covers them, and 15 edits multiply the chance of touching an assertion. (c) Narrow this plan's verification to one file so the other's redness is out of view: rejected outright, that hides a known defect to protect a claim. | Whole-suite probe `23 failed, 2575 passed, 2 skipped`; the 23rd named and its `AssertionError: 2 != 1 : AW-LIFECYCLE-ROLE-001`; `42 passed` on that file with the base-class declaration; `RollupTransitionCase` is the `setUp` for 15 subclasses. | yes |
| D-2 | Does declaring the coordinator role on `RollupTransitionCase` make `TheWorkerRoleIsRefused` vacuous (the D-1 risk)? | NO, and require the proof in V-02 rather than asserting it. | (a) Exclude that class from the base-class declaration with an override: rejected as unnecessary complexity once measured, and an override is itself a way to reintroduce inheritance. (b) Declare the role per-subclass and skip that one: rejected for the same reason as D-1 (b), and it would leave the file with two rules. (c) Assert the safety in prose without a run: rejected, this is exactly the class of claim that must be measured, since the failure mode is a test that passes while checking nothing. | `TheWorkerRoleIsRefused` passes explicit `env={LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER}` at every call; `tests/support.py`'s `worker_role` docstring prescribes that shape for precisely this reason; measured `42 passed` including that class under the probe with the declaration in place. | yes |
| D-3 | The `unittest` exposure (PR-901) is a documentation gap too. Fix `CONTRIBUTING.md` here? | NO: record the fact in the `conftest.py` comment beside the scrub, and leave `CONTRIBUTING.md` alone. | (a) Add a `CONTRIBUTING.md` sentence: rejected as over-scope for a fixture-correction plan, and it belongs with the `test-serial` documentation rather than with a role declaration; the workflow's default for over-scope is removal or explicit deferral. (b) Say nothing anywhere: rejected, the pytest-only limit is the reason the per-class declaration is the ONLY protection under `unittest`, so a reader of the scrub needs it. | The scrub lives in `conftest.py`, which is where a reader encounters the claim; `Makefile` `test-serial` and `CONTRIBUTING.md`'s description of it are a separate surface. | yes |
| D-4 | The `conftest.py` paragraph about `test_driver_own_process_is_not_worker_role` (PR-903). Trim its cross-reference as authored, or replace it? | REPLACE it with the true statement: no shipped test asserts the scrub's invariance today. | (a) Trim as authored: rejected, the paragraph's subject is a test that does not exist, so trimming leaves a false claim looking freshly verified. (b) Delete the whole paragraph: rejected, the pytest-only/observability point is worth keeping and is what motivates the probe; only the dead subject must go. (c) Restore the deleted guard file so the paragraph becomes true again: rejected as clearly over-scope (222 lines with its own restoration decision, already recorded as `6vozur` F-8). | `grep -rn "def test_driver_own_process_is_not_worker_role" --include=*.py .` returns nothing; `git show 19313eed --name-only` lists both guard files deleted; `6vozur` F-8 and its review PR-704 own the restoration question. | yes |
| D-5 | Authored counts had already drifted (PR-906). Update the numbers, or change the criterion? | CHANGE THE CRITERION to a re-derived property, keeping the measured numbers as context. | (a) Just correct 37 to 38 and 11 to 11: rejected, it rots again on the next commit to the file, and the repository's live-artifact convention exists for exactly this. (b) Drop the numbers entirely: rejected, an executor needs a comparison point to notice when reality diverges wildly from the authoring measurement. | Measured `38 tests collected`; `7bed5478` added a test after the authoring HEAD; `61ef21d8` is not an ancestor of `de9b241c`; the plan-review rubric's live-artifact re-derivation convention. | yes |
| D-6 | Two live plans edit the same `conftest.py` comment region (PR-907). Re-scope one, or record the collision? | RECORD it, in the Scope check and as a gate stop condition telling whoever runs second to rebase and report. | (a) Remove `conftest.py` from this plan and let `a6xbso` carry the comment fix: rejected, `a6xbso`'s own review explicitly declined it as not-its-to-fix, so the correction would become unowned. (b) Say nothing and let git sort it out: rejected, the edits are in the same comment block, and the repository's shared-checkout rule forbids overwriting a co-worker's change. | `a6xbso` `- Scope-Paths:` includes `conftest.py` and it is `- Status: reviewed`; its review PR-1209 / F-12 records this same stale reference with "not this plan's to repair". | yes |

### Deferred and open

- (none). All eight findings were FIXED in place. None reached Medium-High or High Remediation Risk:
  every repair was a plan-text change verified by measurement, and the two HIGH-severity ones were
  fixed by ADDING one file, one declaration and one verification leg rather than by narrowing any
  claim. The Fix Bar therefore permitted no deferral, and because nothing was left `OPEN` or
  `DEFERRED` no escalation to a `- Blocking: yes` question was required.
- The single authored open question (OQ-01, `pytest_runtest_setup` versus `pytest_configure`) was
  re-verified rather than accepted: the `pytest_runtest_setup` shape reproduces `22 failed` at this
  HEAD, and the deleted guard file's canonical `_REASSERT_PLUGIN` used `pytest_configure`, so both
  shapes are attested in this repository and the plan's choice is the stricter one. Its resolution
  stands, and the re-confirmation is recorded in the plan.
- Two `Carrier-Declined` rows now sit in the Deferred section (the declined structural guard, and the
  unrestored guard file). The second points at `6vozur` F-8 where the obligation already lives, so no
  new carrier is filed for it.
- No `Reversible: no` decision was made. All six decisions are plan-text choices on an unexecuted
  plan, plus one measured safety judgement (D-2) whose proof is now demanded in V-02 rather than
  resting on my authority.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I executed the FIX but not the
PLAN: I applied the declarations to measure them and then reverted every code edit, so the tree I hand
back contains no implementation, and my `38 passed` / `42 passed` numbers come from my patch and not
from the executor's. SECOND, my whole-suite probe used `pytest_runtest_setup`, which re-asserts the
marker before each test; a different ambient mechanism (a value set once and later cleared, or one
leaked by a test) could expose a different set, so "exactly one other failing test" is a claim about
THIS probe shape and not about every possible role leak. THIRD, I measured the `unittest` path on
`tests.test_ipd_lifecycle_cli` only, not on a full `python3 -m unittest discover`, so I know that one
module is red under `make test-serial` with the marker exported and I do not know the serial suite's
total. FOURTH, the bare-suite baselines I cite are from this lane at this HEAD in a shared checkout and
will differ at execution; they are comparison points, not bars. FIFTH, I did not verify that
`a6xbso`'s `conftest.py` edit and this plan's are textually combinable line by line, only that both
target the same comment block, which is why the gate asks for a rebase and a report rather than
promising a clean merge.
