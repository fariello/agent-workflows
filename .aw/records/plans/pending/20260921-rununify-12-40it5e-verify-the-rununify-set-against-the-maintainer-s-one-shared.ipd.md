# IPD: Verify the rununify Set against the maintainer's one-shared-codebase directive and establish the missing characterization baseline

- Date: 2026-09-21
- Kind: child
- Concern: Two distinct pieces of work sit unperformed on the Order-0 orchestrator `5e4sb6` (its E-02 and E-03), and the runner RETIRES an orchestrator once every child is `executed` while deliberately SKIPPING the pre-transition E/V checkpoint. ALL ELEVEN OTHER CHILDREN ARE ALREADY `executed`, so retirement is imminent and both items would be marked complete having never been performed. MEASURED 2026-09-22 by the coverage probe, which refused a 34-set launch naming `5e4sb6` (event `orchestrator-probe-gate`, emitted at `runner_shared.py` symbol `run_orchestrator_probe_gate`). THE MECHANISM IS VERIFIED IN CODE AT REVIEW HEAD, not taken on the run log's word: `runner_shared.evaluate_set_retirement` gates retirement on every child being exactly `executed`, and running it against this repo now returns `eligible=False`, `reason=unfinished-children`, `detail="Set 'rununify' has 1 child(ren) that are not 'executed': 40it5e (to-review)"`. So THIS PLAN'S EXISTENCE IS ITSELF THE HOLD, and the hold lasts exactly as long as this plan is unexecuted. AND THE MEASUREMENT THAT MAKES THIS SUBSTANTIVE RATHER THAN CLERICAL, stated in its CORRECTED form because the original figure was wrong in the direction that changes the verdict: at HEAD `73e370ae` there are 58 symbols defined in BOTH runners totalling 2757 agy definition lines, but 34 of those have BOTH sides delegating into `runner_shared` and 1 has one side delegating, which is the extraction SUCCEEDING rather than duplication. The genuine residue is 23 symbols / 661 agy lines, and only TWO of them (`_lane_reclaim_prompt`, `disable_lane_prompt`, 50 agy lines) are both near-identical and free of any shared call. The five large functions the original 58/2711 headline leaned on - `run_queue`, `main`, `build_parser`, `expand_selectors`, `reclaim_lanes_on_interrupt` - ALL delegate on both sides already. So the maintainer's 2026-09-16 directive ("at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code") is SUBSTANTIALLY MET with a named residue, not unmet; retiring `5e4sb6` without recording that residue is what this plan prevents.
- Scope: Perform `5e4sb6`'s E-02 and E-03 as real agent turns, and report the Set's true state against the directive. IN: an AST-level, REPO-WIDE single-implementation measurement whose classification is of each symbol's BODY (delegating or not), never of its NAME; a per-symbol disposition of every symbol in the RESIDUE (genuinely host-specific versus still-redundant); the characterization baseline E-02 requires, authored now with its LATENESS STATED and aimed at symbols that are STILL FORKED at execution HEAD; and an honest verdict on whether the Set is done. OUT: performing the unification of any remaining symbol - if the measurement shows redundancy remains, this plan REPORTS it and `runresidue` (`gqo6if`) owns the work, because unifying a forked function is not a verification task. ALSO OUT: pinning a symbol that has ALREADY been unified. A characterization test over `agy_runipd.build_prompt` (a one-line delegation at review HEAD) tests `runner_shared` through two aliases while claiming to test two hosts, which is worse than no test because it reports coverage that does not exist.
- Scope-Paths: .aw/records/plans/pending, tests/test_rununify_characterization.py, .aw/records/research, tools, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: approved
- Work-Kind: chore
- Priority: medium
- Readiness: go-pending-approval
- From-Backlog: dhuape
- Blocks-Release: next
- Set: rununify
- Order: 12
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 40it5e
- Approval: 2026-09-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-23 approved (aw set): Backfilled Priority and Work-Kind by inheritance from source backlog item dhuape (planprio Order 02, plan 8u6770, E-03); no lifecycle transition occurred.
- 2026-09-23 approved (aw set): status set to approved
- 2026-09-22 reviewed (aw set): Release gate and graduation link recorded through the setter rather than hand-written (PR-005): this Set descends from backlog dhuape, which carries Blocks-Release: next, and the gate is inherited rather than re-decided per child.
- 2026-09-22 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. THE PLAN'S PURPOSE IS SOUND AND ITS HEADLINE NUMBER WAS WRONG, which is the dominant finding and is exactly the failure mode the plan was written to prevent in someone else. PR-001: the Concern, Goal, F-02 and OQ-01's opening paragraph all led with "58 symbols still defined in both runners, 2711 agy lines ... the directive is NOT met", while OQ-01's own resolution paragraph already CORRECTED that to a 20-symbol residue. Re-measured independently at review HEAD `73e370ae`: 58 shared symbols / 2757 agy lines, of which 34 BOTH-DELEGATE and 1 one-side-delegates, leaving 23 / 661; under a strict "neither side calls any shared symbol AND similarity >= 0.95" test only TWO (`_lane_reclaim_prompt`, `disable_lane_prompt`). All five large functions the headline named already delegate on both sides (`run_queue` makes 8 `runner_shared` calls on EACH side, not 10 as OQ-01 says). The stale figure is now removed from every load-bearing position rather than left standing beside its own correction. PR-002 (BLOCKER): E-03's four named target symbols were measured and TWO NO LONGER EXIST in either runner - `extract_session_id` is defined ONLY in `runner_shared`, and `build_parser`'s agy definition is a 296-line delegating body, not the uncovered fork the item describes; `integrate_lane_branch` is a 25-line wrapper over `runner_shared.integrate_lane_branch` and `build_prompt` is a ONE-LINE delegation. So E-03 as written directed an executor to pin "the pre-Set fork" of symbols that have already been unified, which would have produced a suite testing `runner_shared` while claiming to test two hosts. E-03 re-scoped onto the residue. PR-003 (HIGH): the cited precedent `tests/test_wtiso_characterization.py` WAS DELETED on 2026-09-18 by commit `d4dd6b88` ("retire change-detector tests over code text and prose"), whose message states it "asserted three diagnosed DEFECTS still exist"; four `test_rununify_*_characterization.py` files were likewise folded into their non-characterization twins by `7ebc2964`. Following a deleted precedent invites re-creating the exact class of test this repo just retired; E-03 now cites the LIVE precedent (`tests/test_rununify_run_queue.py` and its three kin, 320 tests collected) and carries the anti-change-detector constraint. PR-004 (HIGH): the 95-vs-21 suite asymmetry F-04 presents as current is 2026-08-30 data; measured now it is 284 oc / 97 agy, so the asymmetry is 2.9x not 4.5x and `integrate_lane_branch` has 13 referencing test files, not zero. PR-005 (HIGH): the plan carried NO `Blocks-Release`, so this Set's inherited 2.0.0 gate (`dhuape`, `Blocks-Release: next`, carried by the parent and by children 01/02) died at this plan; added, with `From-Backlog: dhuape`. PR-006 (MEDIUM): E-01 was told to "re-derive rather than trust" a figure produced by a scanner that does not exist in-tree, so E-01 now COMMITS its scanner. PR-007 (MEDIUM): V-02 demanded the ten largest still-shared symbols, which by agy line count are all BOTH-DELEGATE and therefore not the interesting set; re-pointed at the residue. PR-008 (LOW): E-04's claim that `runresidue`/`gqo6if` "covers the residue" verified TRUE for the 20-symbol loose set and its E-05 depends on this plan's test file, which is a real edge recorded here. Structural preflight `aw ipd lint --phase author` conforming before, `--phase review-finalize` conforming after. OQ-01 was already resolved by the maintainer; a NEW OQ-02 is raised `Blocking: no` carrying `- Finding: PR-002`.

- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after the orchestrator coverage gate refused run `run-20260922T003414Z-1020752`, naming `5e4sb6` as carrying work no child covers. THE PARENT'S E-02 EXPLICITLY SANCTIONS THIS SHAPE: "if the repo's conventions make a test-only change count as product code, it becomes child 00 instead, executed before child 01." That window has closed - all eleven children are executed - so E-02 is authored here with its lateness declared rather than pretended away. E-03's content is lifted from the parent unchanged.
- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Tell the truth about whether `rununify` achieved what the maintainer asked for, and leave behind the
characterization baseline the Set was supposed to have. THE HONEST ANSWER, on the review's re-measurement at
HEAD `73e370ae`, IS "SUBSTANTIALLY, WITH A NAMED RESIDUE", and that phrasing is deliberate in both
directions. It is not "unmet": of 58 symbols defined in both runners, 34 have BOTH sides delegating into
`runner_shared` and the five large functions the original framing leaned on all delegate already, so the
extraction largely WORKED. It is also not "met": 23 symbols carrying 661 agy definition lines have neither
side delegating, and at least two of those are duplication rather than host shape. Recording that residue
before the orchestrator retires is the whole deliverable, because a Set that reports unqualified success is
one nobody revisits.

A NOTE ON THE METRIC, because this plan exists to correct a number and must not introduce a new bad one.
COUNTING SYMBOL NAMES DEFINED IN BOTH FILES IS THE WRONG METRIC and is what produced the discarded
"58 symbols / 2711 lines / directive unmet" headline: the sanctioned de-duplicated form in this Set is one
real implementation in `runner_shared` plus a THIN PER-HOST WRAPPER at the original name (the parent's
"injected-parameter mechanism" note records that the maintainer's 2026-09-03 `818uru` OQ-02 ruling
ESTABLISHED that shape), so a successfully de-duplicated symbol still has its name in both files BY DESIGN.
Any measurement this plan reports must therefore classify the symbol's BODY, and must say which test it
used.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the Set against the directive

- [ ] E-01 COMMIT A SCANNER that measures single-implementation AST-LEVEL and REPO-WIDE, then paste its output at execution HEAD. A SCRIPT, NOT A PASTED TRANSCRIPT: the parent's own PR-006-equivalent lesson is that its baseline came from an ad-hoc scan nobody can re-run, which is precisely why its headline figure could not be re-derived and why that figure was then quoted wrongly for a day. Commit the scanner under `tools/` so a reader re-derives every number in this plan with one command. THE PAIRWISE CHECK IS KNOWN-BLIND and the parent says so (F10): "a pairwise check passes while a third copy sits in another module, which is exactly the state measured today". So compare each runner symbol against ALL of `agent_workflows/*.py`.
  CLASSIFY BODIES, NOT NAMES, and print the test used beside each count. A symbol whose name is in both files but whose two bodies both delegate into `runner_shared` is the SANCTIONED de-duplicated form (one real implementation plus a thin per-host wrapper at the original name), so counting names reports the extraction's SUCCESS as its failure. Emit, per shared symbol: both line counts, whether each side's body references `runner_shared`, how many distinct `runner_shared.*` attributes each side calls, and a host-token-normalized similarity ratio. Then report the classes separately: BOTH-DELEGATE, ONE-SIDE-DELEGATES, NEITHER-DELEGATES, plus the class (d) re-fork count (a runner symbol also defined in a non-runner module) and the count with exactly one definition repo-wide.
  THE REVIEW'S MEASUREMENT IS THE STARTING POINT AND MUST BE RE-DERIVED, NOT TRUSTED (HEAD `73e370ae`): 58 symbols in both runners / 2757 agy definition lines, splitting 34 BOTH-DELEGATE, 1 ONE-SIDE-DELEGATES, 23 NEITHER-DELEGATES (661 agy lines). Under a strict test (neither side calls any `runner_shared` symbol AND normalized similarity >= 0.95) only two qualify: `_lane_reclaim_prompt` (46 agy lines, 0.974) and `disable_lane_prompt` (4, 1.000). DO NOT re-derive the DISCARDED figure: "58 symbols / 2711 agy lines / directive unmet" counted NAMES and is wrong; `run_queue` (549/456), `main` (340/234), `build_parser` (387/296), `expand_selectors` (199/183) and `reclaim_lanes_on_interrupt` (252/252) ALL delegate on both sides. If your scan disagrees with these numbers, report the disagreement with your HEAD rather than silently adopting either figure.
  - Depends on: none
  - Expected outcome: a committed scanner under `tools/` runnable in one command, its pasted output at execution HEAD, the class counts EACH labelled with the test that produced it, and the per-symbol table. A single residue number without its test named FAILS this item, and so does a count of symbol names presented as a duplication count.
  - Execution state: pending

- [ ] E-02 DISPOSITION EVERY RESIDUE SYMBOL AS HOST-SPECIFIC OR STILL-REDUNDANT, per symbol, with evidence. The subject is E-01's NEITHER-DELEGATES and ONE-SIDE-DELEGATES classes, NOT every symbol whose name appears twice: a BOTH-DELEGATE symbol is already one implementation and dispositioning it would be busywork that pads the table and buries the 23 entries that matter. This is the judgement E-01's raw count cannot make: a symbol still forked is NOT automatically a defect, because the maintainer's own test is "one host does A, the other NOT A" - a real capability difference is legitimately host-shaped. Apply THAT test, and for each symbol record which side is authoritative and why, or that both are needed and why.
  A SIMILARITY RATIO IS EVIDENCE, NOT A DECISION, and the residue contains counterexamples in both directions that make this concrete: `_lane_reclaim_prompt` at 0.974 similarity may be pure duplication while `set_plan_approved` at 0.521 and `route_recovery_turn` at 0.080 (79 oc lines against 10 agy) may be real capability differences. Do not let the number decide, and do not report a threshold as a disposition. CHECK FOR A RECORDED IMMOVABILITY BEFORE CALLING SOMETHING REDUNDANT: `disable_lane_prompt` writes a module-level `global` that must stay per-runner and is PINNED by `UnmovableSymbolTests` in `tests/test_runner_shared.py` (the parent's child-table note records this as one of its documented exceptions to "100%"), so its 1.000 similarity is not evidence of a defect. A disposition that contradicts an existing pin without naming it FAILS.
  Do NOT unify anything here (see the deferral list).
  - Depends on: E-01
  - Expected outcome: a per-symbol table with a disposition and evidence for every residue symbol from E-01 (NEITHER-DELEGATES plus ONE-SIDE-DELEGATES), an explicit still-redundant count reconciling with E-01's output, and the pinned-immovable symbols named as such rather than counted as residue; immortalized under `.aw/records/research/` with `aw research new` (do not hand-name it), since `runresidue` starts from it.
  - Execution state: pending

- [ ] E-03 WRITE THE CHARACTERIZATION BASELINE OVER THE SYMBOLS THAT ARE STILL FORKED, AND DECLARE THAT IT IS LATE. The parent's E-02 asks for tests pinning CURRENT observable behavior of both hosts "BEFORE any child reconciles anything". That precondition is UNSATISFIABLE NOW: all eleven other children have executed, so what this suite can pin is post-reconciliation behavior, not the pre-Set baseline, and it therefore CANNOT retroactively prove the reconciliations preserved behavior. Write it anyway and say exactly that, because its forward value is real and has a NAMED CONSUMER: `runresidue`'s E-05 extends this file to pin each symbol it is about to share.
  THE SUBJECT IS E-02's RESIDUE, NOT THE PARENT'S 2026-08-30 UNCOVERED LIST, and this correction is load-bearing rather than editorial. Two of the four symbols that list names NO LONGER EXIST as forks at review HEAD: `extract_session_id` is defined ONLY in `runner_shared` (absent from both runners), and `build_prompt`'s agy definition is a ONE-LINE delegation into `runner_shared.build_prompt`; `integrate_lane_branch` is a 25-line wrapper whose docstring states "the IMPLEMENTATION is the single shared `runner_shared.integrate_lane_branch`"; only `build_parser` still carries a substantial per-host body, and even it delegates. A test pinning `agy_runipd.build_prompt` would therefore exercise `runner_shared` through two aliases while REPORTING two-host coverage, which is worse than no test. So pin the symbols E-02 dispositioned as residue, PRIORITIZING the ones whose agy side the existing suites do not reach.
  FOLLOW THE LIVE PRECEDENT, NOT THE DELETED ONE. The parent cites `tests/test_wtiso_characterization.py`; that file was DELETED on 2026-09-18 in commit `d4dd6b88` ("retire change-detector tests over code text and prose"), whose message records that it "asserted three diagnosed DEFECTS still exist" for fix-plans that are all superseded. Four `test_rununify_*_characterization.py` files were likewise folded into their behavioral twins by `7ebc2964`. The LIVE precedent is `tests/test_rununify_run_queue.py` and its kin (`_main`, `_build_parser`, `_initialize_run`), which is where this repo now keeps two-host behavioral pins. ASSERT ON OBSERVABLE BEHAVIOR, NOT ON SOURCE TEXT: no line-count pin, no `SequenceMatcher` ratio assertion, no frozen closure census, because those are exactly what `d4dd6b88` retired and re-creating them would be reverting a maintainer decision from four days earlier under a new filename.
  - Depends on: E-02
  - Expected outcome: `tests/test_rununify_characterization.py` committed and passing, pinning both hosts' OBSERVABLE behavior for symbols E-02 recorded as still forked, with a module docstring that (a) states plainly it was authored AFTER the reconciliations and therefore pins present behavior rather than the pre-Set baseline, (b) names which symbols it pins and why those and not the parent's 2026-08-30 list, and (c) records that `tests/test_wtiso_characterization.py` was deleted by `d4dd6b88` so a later reader does not go looking for it. A suite containing a source-text or line-count assertion FAILS this item even if it passes.
  - Execution state: pending

- [ ] E-04 STATE THE SET'S VERDICT AGAINST THE DIRECTIVE, in one place, and do not soften it in EITHER direction. Using E-01 and E-02, answer: is there "one code base shared by the two runners that contains 100% of the otherwise redundant code"? If E-02's still-redundant residue is non-empty the literal answer is NO, and this item must say so plainly, name the residue, and cite its carrier - NOT mark the Set complete because eleven children executed.
  AND THE OPPOSITE FAILURE IS EQUALLY FORBIDDEN, which is why this item was revised: a bare "NO, unmet" built on a symbol-NAME count would ALSO be false, and that is the verdict this plan originally carried. The review measured 34 of 58 shared symbols with BOTH sides delegating and every one of the five large functions already delegating, so a verdict that does not distinguish "one implementation plus two host wrappers" from "two implementations" is not a measurement. Report the verdict as literal-NO WITH ITS MAGNITUDE: state the residue count, the agy line total, the test that produced both, and say explicitly which of the Set's work SUCCEEDED. The maintainer's own resolution of OQ-01 records the target phrasing: "substantially met, with a named residue".
  THE CARRIER ALREADY EXISTS AND MUST BE NAMED BY ID: `runresidue` / `gqo6if` (`.aw/records/plans/pending/20260921-runresidue-01-gqo6if-close-the-runner-unification-residue-share-the-last-forked-s.ipd.md`), authored 2026-09-22 at the maintainer's direction in the same session that resolved OQ-01, precisely so this verdict cites a real carrier rather than a promise. So this item does NOT propose a follow-up: it CONFIRMS that plan covers the residue E-02 measured and reports any residue symbol it does not name. Verified at review time to name `reclaim_lanes_on_interrupt` plus the stop/lifecycle/lock clusters and to report its own residue as a 7-to-20 RANGE with both tests stated; reconcile your count against BOTH of its numbers rather than only the one that matches. ALSO RECORD THE DEPENDENCY DIRECTION, because it is a real edge and is currently undeclared: `gqo6if` E-05 extends `tests/test_rununify_characterization.py`, the file THIS plan's E-03 creates, and `gqo6if` carries `Item-Dependencies: none`. Note in the verdict whether that edge should be declared.
  Either way, paste a bare `python3 -m pytest`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: an explicit YES/NO verdict with its measured basis AND its magnitude (residue count, agy line total, the test used, and what succeeded), the named residue, confirmation that `gqo6if` covers it with any gap named, a note on the undeclared `gqo6if` E-05 dependency edge, and the pasted suite summary. A bare "unmet" with no magnitude FAILS this item exactly as a bare "met" would.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN, and the remedy for a parent carrying uncovered work is to ADD A CHILD, never to delete the parent's items: that checklist is what makes a hand-run `execute <setid>` complete when no runner is involved (`AGENTS.md`). This plan adds coverage and changes nothing on `5e4sb6` except its child table.
- THE PARENT ALREADY ANTICIPATED THIS PLAN'S SHAPE for E-02: "if the repo's conventions make a test-only change count as product code, it becomes child 00 instead, executed before child 01." The window closed, so E-03 here declares its lateness rather than claiming the precondition was met.
- THE MAINTAINER'S 2026-09-16 DIRECTIVE IS THE DEFINITION OF DONE and supersedes narrower readings of any child scope: 100 percent of otherwise-redundant code shared. The parent records that every child's OQ-03 resolved to this, and that deferral routes offered at review were REFUSED on this basis.
- SOURCE-READING TESTS ARE WORK, NOT VETOES (the parent's supporting ruling of 2026-09-16): 44 test files in this repository assert on the SHAPE of source, so a test that pins a duplication is a thing to update, not a reason to abandon a unification.
- AND A SOURCE-READING TEST IS NO LONGER SOMETHING TO AUTHOR, which is the newer ruling and the one that binds E-03. Commit `d4dd6b88` (2026-09-18, maintainer) retired "tests that assert code/prose HAS NOT CHANGED, keeping tests that assert behavior", on the stated reasoning that "a git repository already records when text changes; a test that fails on a legitimate reword costs author time and catches no defect". It deleted line-count pins, `SequenceMatcher` ratio assertions and AST closure censuses from the `rununify` suites, and deleted `tests/test_wtiso_characterization.py` outright. The two rulings are consistent: an EXISTING shape-pin is re-based deliberately rather than treated as a veto, and a NEW test asserts behavior.
- THE SANCTIONED DE-DUPLICATED FORM LEAVES THE SYMBOL NAME IN BOTH RUNNERS. The parent's child-breakdown note records the maintainer's 2026-09-03 `818uru` OQ-02 ruling as ESTABLISHING the mechanism: `runner_shared` owns the real function taking each outside dependency as a parameter, and each runner keeps a one-line wrapper at the ORIGINAL name and signature. Any measurement in this plan must therefore classify bodies, never names.
- THE PARENT ALSO RECORDS DOCUMENTED EXCEPTIONS TO "100%" that are not unfinished work: ten symbols carrying a per-host wrapper (which IS the de-duplicated form) and `disable_lane_prompt`, which writes a module-level `global` that must stay per-runner and is pinned by `UnmovableSymbolTests` in `tests/test_runner_shared.py`. E-02 must not report a pinned-immovable symbol as residue.
- A RELEASE GATE IS INHERITED, NOT RE-DECIDED PER CHILD (`AGENTS.md` "Release gates"): a plan graduating from a backlog item inherits its `Blocks-Release`. This Set descends from `dhuape` (`Blocks-Release: next`), so this plan carries the gate and `From-Backlog`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `runner_shared.evaluate_set_retirement` run against this repo at HEAD `73e370ae`; the probe gate at `runner_shared` symbol `run_orchestrator_probe_gate`, event `orchestrator-probe-gate` | The coverage probe refused a 34-set launch naming `5e4sb6` as carrying work no child covers. RE-VERIFIED IN CODE RATHER THAN FROM THE RUN LOG, because the run directory is gitignored and not present in a lane: `evaluate_set_retirement(repo, 'rununify')` returns `eligible=False`, `reason=unfinished-children`, `detail="Set 'rununify' has 1 child(ren) that are not 'executed': 40it5e (to-review)"`. Eleven of twelve children are `executed`; THIS PLAN is the twelfth and is the only thing holding retirement. So E-02 and E-03 would tick unperformed the moment this plan executes, which is precisely why its verdict must be written before it finalizes. |
| F-02 | HIGH | E-01's scanner output at review HEAD `73e370ae`, classifying each shared symbol's BODY | THE RESIDUE IS 23 SYMBOLS / 661 AGY LINES, NOT 58 / 2711, and this row was CORRECTED at review (it formerly read BLOCKER on the 58 figure, which is the same error this plan exists to prevent in the orchestrator). Of 58 symbols defined in both runners (2757 agy definition lines), 34 have BOTH sides delegating into `runner_shared` and 1 has one side delegating: that is the sanctioned de-duplicated form (one real implementation plus a thin per-host wrapper at the original name) and counting it as duplication reports the extraction's success as its failure. Every large function the old figure leaned on already delegates on BOTH sides: `run_queue` (549/456, 8 `runner_shared` calls per side), `main` (340/234), `build_parser` (387/296), `expand_selectors` (199/183), `reclaim_lanes_on_interrupt` (252/252). Under a strict test (neither side calls any shared symbol AND normalized similarity >= 0.95) only TWO qualify, `_lane_reclaim_prompt` (46 agy lines, 0.974) and `disable_lane_prompt` (4, 1.000), and the second is PINNED immovable. So the directive is substantially met with a named residue; whether each residue symbol is redundant or legitimately host-shaped is what E-02 decides. |
| F-03 | HIGH | `git log` on `tests/test_wtiso_characterization.py` -> deleted in `d4dd6b88`; `git show --stat 7ebc2964` | THE CITED PRECEDENT NO LONGER EXISTS, AND WAS DELETED ON PURPOSE. `tests/test_rununify_characterization.py` is indeed absent, but so is `tests/test_wtiso_characterization.py`: commit `d4dd6b88` (2026-09-18) "retire change-detector tests over code text and prose" removed it, recording that it "asserted three diagnosed DEFECTS still exist" for fix-plans that are all superseded. The same sweep, and `7ebc2964` before it, folded four `test_rununify_*_characterization.py` files into their behavioral twins and deleted source-text pins (`len(getsourcelines(main)) == 309`, `SequenceMatcher` ratios, AST closure censuses). An executor following the parent's citation would re-create the retired form under a new name, reverting a four-day-old maintainer decision. E-03 now cites the live precedent (`tests/test_rununify_run_queue.py` and kin) and forbids source-text assertions. |
| F-04 | MEDIUM | `python3 -m pytest --collect-only -o addopts="" -q` on each suite at HEAD `73e370ae`; `grep -rl integrate_lane_branch tests/` | THE SUITE ASYMMETRY IS REAL BUT ITS NUMBERS ARE 2026-08-30 DATA AND HAVE MOVED IN THE FAVORABLE DIRECTION. Measured now: 284 opencode runner tests (`test_oc_runipd.py` + `_cli` + `_shim`) against 97 agy (`test_agy_runipd_cli.py` + `_shim`), so the ratio is 2.9x rather than 4.5x, and the `rununify` files alone collect 320 tests. `integrate_lane_branch` now has 13 referencing files under `tests/`, not zero. The asymmetry still justifies a baseline; the SPECIFIC HOLE the parent named has largely closed, which is why E-03 aims at E-02's residue instead of the parent's list. |
| F-05 | LOW | `5e4sb6` E-01 execution note | E-01 is already `performed` with a DECLARED GAP: 46 of 52 class (c) symbols were left undecided because mechanical signals were silent, and the note says recording a guess would be worse than recording the gap. E-02 here inherits that unfinished judgement for whatever remains forked, and should follow the same honesty. |
| F-06 | HIGH | AST inspection of both runners at review HEAD `73e370ae` | E-03's FOUR NAMED TARGETS ARE LARGELY ALREADY UNIFIED, which made the item as written unexecutable as intended. `extract_session_id` is defined ONLY in `runner_shared` and is absent from both runners. `build_prompt` is a ONE-LINE delegation on the agy side. `integrate_lane_branch` is a 25-line wrapper whose own docstring says "the IMPLEMENTATION is the single shared `runner_shared.integrate_lane_branch`". Only `build_parser` retains a substantial body, and it too delegates. A characterization suite over these would test `runner_shared` through two aliases while reporting two-host coverage: a test that manufactures false confidence, which is worse than the absence it replaces. |
| F-07 | MEDIUM | `.aw/records/backlog/graduated/20260828-dhuape-01-dhuape-unify-runners.backlog.md`; `Blocks-Release` on `5e4sb6` and on children `2r306y`/`818uru` | THE SET'S RELEASE GATE DIED AT THIS PLAN. Backlog `dhuape` carries `Blocks-Release: next` and `Status: graduated`; the parent `5e4sb6` carries `Blocks-Release: next` and `From-Backlog: dhuape`; children 01 and 02 carry the gate. This plan carried NEITHER field, so the last child of a release-blocking Set did not declare the gate it inherits, and `aw attention`'s release-blocker set could not see it. `Blocks-Release` is a recognized optional IPD field (`ipd_schema.META_BLOCKS_RELEASE`), so there was no schema obstacle; note the 2.0.0 release record's "IPD sets that cannot yet carry the field" interim note is now STALE. Both fields added. |
| F-08 | LOW | `20260921-runresidue-01-gqo6if-...ipd.md` front matter and E-05 | AN UNDECLARED CROSS-PLAN EDGE. `gqo6if` E-05 says to "extend `tests/test_rununify_characterization.py` (authored by `40it5e`; create it if that plan has not executed)", while carrying `Item-Dependencies: none`. The fallback makes it safe rather than broken, so this is LOW, but the ordering preference is real and is invisible to the runner's dependency-depth sort. E-04 now records it for the maintainer rather than either plan silently assuming an order. |

## Proposed changes (ordered, validatable)

1. Commit a body-classifying, repo-wide scanner and paste its output with the test behind each count (E-01).
2. Disposition every RESIDUE symbol as host-specific or still-redundant, with evidence (E-02).
3. Write the characterization baseline over the STILL-FORKED symbols, declaring its lateness (E-03).
4. State the Set's verdict against the directive with its magnitude, softening it in neither direction (E-04).

## Deferred / out of scope (with reason)

- UNIFYING ANY REMAINING SYMBOL. Unifying a forked function is not a verification task, and doing it inside a
  plan whose job is to MEASURE would destroy the independence of the measurement. E-04 confirms the carrier
  covers what E-02 found rather than proposing new work.
  - CARRIER RE-POINTED AT EXECUTION TIME, and the re-pointing is itself a measurement this plan owes its
    reader. The row named `gqo6if`, which was `pending` when this plan was reviewed on 2026-09-22 and reached
    `executed` on 2026-09-23 (commit `525442c4`, integrated before this turn's HEAD). So the row's original
    carrier is terminal and `check.ipd-uncarried-obligation` correctly refused the commit: a deferral pointing
    at an executed plan names nothing that will revisit it. `gqo6if` did NOT close the residue, it PARTITIONED
    it, and its research `fedqe6` records where each part went, so the live carriers are those parts and not a
    single successor plan. E-02 re-derives the partition at THIS head rather than trusting it.
  - Carrier: 1f7xno
  - Carrier: 2yjc5l
  - Carrier: 2t4v1j
- `5e4sb6` E-01. Already `performed`, with its gap declared. This plan does not re-open it, though E-02
  inherits the same per-symbol judgement question for whatever is still forked.
  - Carrier-Declined: NOT AN OBLIGATION THIS PLAN INCURS, and filing one would misrepresent a recorded
    decision as debt. The parent's E-01 is `performed` with its gap DECLARED in its own execution note, on the
    explicit reasoning that "recording a guess per symbol would be worse than recording the gap" - and the
    maintainer had bounded that slice to the inventory alone. The undecided symbols the gap names are not
    lost: the ones that are still forked arrive here as E-02's residue, and the ones that were since shared
    needed no decision. So the residual work is carried by E-02 and by `gqo6if`, not by a new record.
- RETROACTIVELY PROVING BEHAVIOR PRESERVATION. It cannot be done: the baseline that would have proven it
  had to exist before the children ran, and it did not. E-03 states this rather than implying the new suite
  closes the gap.
  - Carrier-Declined: IMPOSSIBLE, not deferred, so there is no obligation any record could discharge. The
    evidence that would prove the eleven executed children preserved behavior had to be captured BEFORE they
    ran; that moment has passed and no future plan can recover it. Filing a carrier would assert that someone
    could still do this, which is false and would leave a permanently unclosable item on the board. The
    honest artifact is the statement itself, which E-03's docstring and V-03 both require on disk.
- PINNING A SYMBOL THAT IS ALREADY UNIFIED. Deliberately excluded rather than merely unmentioned, because the
  item originally directed it (F-06): a test over a one-line delegation reports two-host coverage it does not
  have, so the residue is the only legitimate subject for a two-host pin.
  - Carrier-Declined: AN EXCLUSION OF SOMETHING HARMFUL, which owes nothing to anybody. This row records that
    a proposed action was found counterproductive and dropped, not that useful work was postponed: a pin over
    `runner_shared` reached through two host aliases manufactures coverage rather than measuring it. There is
    no future plan that should do it, so a carrier would file an item whose correct resolution is to refuse it.
- RE-BASING OR DELETING ANY EXISTING GUARD. Several `rununify` suites deliberately assert a symbol is STILL
  double-defined as a tripwire (`tests/test_rununify_run_queue.py`'s `STILL_DOUBLE_DEFINED` table names its
  own purpose). This plan unifies nothing, so it must trip none of them; a guard that fires here is a finding
  about the measurement, not a guard to update.
  - Carrier-Declined: NOTHING IS OWED, because this row forbids an ACTION rather than postponing one, and that
    became visible when the original carrier (`gqo6if`) went terminal. Re-pointing it at another plan would be
    worse than leaving it dangling: it would file "re-base a guard" as debt on a plan that has no reason to do
    it, when the correct future behavior is that NO plan re-bases a guard as a side effect of measuring. A
    guard that fires while this plan runs is a defect in the measurement, and that path already has a real
    carrier: this turn's defect report and the backlog item it would file. Verified at execution: none fired
    (V-01 and the bare suite in V-04 record it).

## Scope check

- Over-scope: none. Two paths were newly declared at review. `tools` is for E-01's scanner: the plan is
  required to re-derive a figure whose original scanner does not exist in-tree, and a measurement nobody can
  re-run is the exact defect that produced the number this plan corrects. `tests/test_orchestrator_retirement.py`
  is a CONSEQUENCE of this plan's own lifecycle rather than new work: that suite pins this plan's literal
  `Status:` string in its live-Sets table, so every transition of this plan requires re-pointing the row, and
  declaring the path is what lets `aw ipd finalize` reconcile that edit instead of flagging it as drift.
- Under-scope: none. The parent carries E-01 (performed), E-02 and E-03; this plan covers the parent's E-02
  via its own E-03, and the parent's E-03 via its own E-01/E-02/E-04.

## Required tests / validation

`tests/test_rununify_characterization.py` is authored by E-03 and must pass; paste its output. E-04
additionally requires a bare `python3 -m pytest` (bare means BARE: `pyproject.toml` `addopts` already
supplies `-q -n auto --dist=worksteal -m 'not slow'`, so do not add `-n0`, a second `-q`, or
`-p no:randomly`).

BASELINE IS A MEASUREMENT, NOT A CONSTANT: take your own pre-change count at your own HEAD and compare
against THAT, never against a number written in a plan. This plan changes no runner logic, so the invariant
is parity plus exactly the tests E-03 adds. If any pre-existing test MOVES, that is a finding to report,
not a delta to explain away, and the `rununify` guard suites are the likely tripwire (see the deferral list).

EXPECT `tests/test_orchestrator_retirement.py` TO GO RED WHEN YOU TRANSITION THIS PLAN, and re-point it
rather than being surprised by it. `RealRepositorySets::test_every_live_set_reaches_its_measured_verdict_for_its_measured_reason`
asserts the REAL repository state of seven live Sets, and its `rununify` row pins THIS plan's literal
`Status:` string (it read `to-review`, and the review's transition to `reviewed` turned it red; the review
re-pointed it, which is why `tests/test_orchestrator_retirement.py` is now in `Scope-Paths`). Your own
transition to `executed` will flip the Set to ELIGIBLE with all twelve children executed, so that row needs
re-pointing again, in the same change. THE TEST'S OWN RULE GOVERNS HOW: re-measure and re-point, NEVER
loosen, and specifically do not widen the asserted status set to admit several values at once, which would
stop the row detecting anything. The urgency is stated in the test itself: lane integration is gated on a
bare whole-repo pytest, so one red row here refuses integration for EVERY lane that finishes afterwards.

ONE PRE-EXISTING FAILURE IS NOT YOURS, recorded so you do not chase it or claim it as a regression. At
review HEAD `73e370ae`, `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
fails, and it fails identically with this plan's changes reverted. It is environment-dependent (it asserts
on the inherited process environment). Re-check it against a clean HEAD before attributing it to your work,
and report it as pre-existing if it is still red.

## Spec / documentation sync

N/A for contracts; no spec pins the runners' internal structure and this plan changes no behavior. Two
records do need touching. E-02's per-symbol disposition is immortalized under `.aw/records/research/` via
`aw research new`, because `gqo6if` starts from it. The only structural plan edit is the child-table row on
`5e4sb6`, which already exists (Order 12) and must not be re-added.

NOTED BUT NOT OWNED HERE: the 2.0.0 release record's "Interim: IPD sets that cannot yet carry the field"
note is stale, since `Blocks-Release` is now a recognized optional IPD field (`ipd_schema.META_BLOCKS_RELEASE`)
and this plan carries it. Correcting that note is a separate change in a record this plan does not declare,
so E-04 reports it rather than editing it.

## Open questions

### OQ-01: If E-02 shows the directive is unmet, should `5e4sb6` still be allowed to retire as `executed`?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: F-02
- Resolution or deferral rationale: RAISED BY THE AUTHOR, and it is genuinely the maintainer's call because it is about what a completed Set MEANS, not about code. THE MEASUREMENT AS RAISED (SUPERSEDED - read the correction two paragraphs down before acting on any figure here): 58 symbols are still defined in both runners (2711 agy lines) while the directive asks for 100 percent of otherwise-redundant code shared and the Set expected only five host-shaped functions as residue, so on that evidence eleven children executed and the Set's own definition of done was not reached. TWO READINGS, and they lead to different records. (a) RETIRE IT ANYWAY: the eleven children each did what they were scoped to do, the Set's children are complete, and the residue becomes a NEW Set with its own plans; `5e4sb6` retires `executed` and this plan's E-04 verdict is the honest record of what remains. (b) DO NOT RETIRE IT: the directive is the definition of done and it is unmet, so retiring records a false completion; the parent should stay pending until a further child closes the residue, which keeps the obligation visible in `aw attention` instead of in a research file nobody re-reads. RECOMMENDATION: (a), on the reasoning that a Set's completion means its CHILDREN are complete and that carrying a parent open indefinitely is how a Set becomes a permanent fixture - provided E-04's verdict is recorded prominently and a follow-up Set is actually filed, which this plan's E-04 requires. BLOCKING because it decides whether this plan's own completion should leave the parent retirable, and because (b) would mean authoring a further child instead.
  RESOLVED 2026-09-22 BY THE MAINTAINER (asked through `/askme`): OPTION (a), RETIRE IT, AND FILE THE RESIDUE AS NEW WORK IMMEDIATELY. Their words: "Mark it done, file the rest as new work ... BUT Write the plan NOW. Don't wait." So the retirement is NOT conditional on the residue being closed, and the follow-up is NOT left as a promise this plan's E-04 merely requires: the follow-up Set `runresidue` was authored in the same session and is on disk before this question was closed, which removes the one risk the recommendation rested on (that a deferred follow-up never gets filed).
  THE NUMBER IN THE PARAGRAPH ABOVE IS WRONG AND IS CORRECTED HERE, because the maintainer decided on the corrected figure and a later reader must not re-derive the stale one. The question was raised citing 58 symbols and 2711 agy lines. RE-MEASURED 2026-09-22 at HEAD `f763be8c` by classifying each shared symbol's BODY rather than counting its NAME: of 57 symbols defined in both runners, 32 have BOTH sides delegating to `runner_shared` (a host-shaped shell over one real implementation, which is the extraction SUCCEEDING), 3 have agy delegating while oc keeps the body, 2 the reverse, and only 20 symbols totalling about 667 agy lines have NEITHER side delegating. The 58/2711 figure counted a genuinely-shared function as duplicated because each host still wraps it. So the residue is 20 symbols, not 58, and the largest functions the original figure leaned on (`run_queue` 456 lines, `main`, `build_parser`, `expand_selectors`, `retry_deferred_integrations`) are all ALREADY delegating - `run_queue` makes 10 calls into `runner_shared`. The Set therefore came much closer to the directive than the raw name count implied, and the honest verdict E-04 must record is 'substantially met, with a named 20-symbol residue' rather than 'unmet'.
  ONE MEASURED DUPLICATION IS WORTH NAMING because it is not a host difference at all: `reclaim_lanes_on_interrupt` is 252 lines on EACH side at 0.998 similarity after host-token normalisation (the earlier figure of 174 lines was measured at `f763be8c`; re-measured at review HEAD `73e370ae` it is 252/252, and the SIMILARITY is the load-bearing number either way). That is copied code, and `gqo6if` E-03 correctly takes it first.
  THIRD RE-MEASUREMENT AT REVIEW HEAD `73e370ae`, recorded because these figures have now moved twice and a fourth reader must be able to see the trend rather than pick one number: 58 symbols in both runners / 2757 agy definition lines, splitting 34 BOTH-DELEGATE, 1 ONE-SIDE-DELEGATES, 23 NEITHER-DELEGATES (661 agy lines). That is consistent with the paragraph above (20 at `f763be8c`, 23 here) rather than contradicting it, and the DECISION the maintainer made is unaffected: the residue is a few dozen symbols and hundreds of lines, not 58 symbols and 2711 lines. Two details of the paragraph above are corrected: `run_queue` makes 8 `runner_shared` calls per side, not 10, and `retry_deferred_integrations` is better named among the delegating large functions than `expand_selectors` alone. E-01 re-derives all of this from a COMMITTED scanner so the next reader does not have to trust any of these three measurements.

### OQ-02: Should this plan's characterization baseline exist at all, given that its four named targets are already unified?

- Blocking: no
- Status: resolved
- Owner: reviewer (resolved from repository evidence; raised for the maintainer's awareness)
- Finding: F-06
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE, and recorded rather than silently edited because it changes what E-03 delivers. The item as authored aimed the baseline at `integrate_lane_branch`, `build_parser`, `extract_session_id` and `build_prompt`, citing the parent's 2026-08-30 zero-agy-coverage measurement. Measured at review HEAD `73e370ae`, that list has largely dissolved: `extract_session_id` is defined ONLY in `runner_shared`, `build_prompt`'s agy body is a one-line delegation, `integrate_lane_branch` is a 25-line wrapper over the shared implementation, and only `build_parser` keeps a substantial body while still delegating. `integrate_lane_branch` now has 13 referencing test files where the parent measured zero, and the suite asymmetry is 284/97 rather than 95/21.
  SO THE ORIGINAL SUBJECT IS GONE. Three readings were considered. (a) DROP E-03 as obsolete: rejected, because the residue E-02 measures is genuinely forked two-host code and `gqo6if` E-05 explicitly plans to extend this file before it changes any of it, so the file has a named consumer and real forward value. (b) KEEP THE ORIGINAL FOUR TARGETS: rejected as actively harmful - a pin over a one-line delegation exercises `runner_shared` through two aliases while reporting two-host coverage, manufacturing confidence rather than evidence, which is the failure class this whole plan exists to catch. (c) RE-POINT E-03 AT E-02's RESIDUE: chosen. It preserves the deliverable, gives it a subject that is actually forked, and keeps the dependency on E-02 that the item already declared.
  RAISED RATHER THAN BURIED because a maintainer reading "characterization baseline for `rununify`" will reasonably expect the parent's named symbols, and will find a different set. NON-BLOCKING because the repository answered it unambiguously and the chosen option preserves rather than reduces the plan's scope; reversible by editing E-03 if the maintainer wants the original four pinned anyway.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the COMMITTED scanner's in-tree path (a pasted transcript with no committed script FAILS, since the whole point is that the next reader re-runs it), the command a reader invokes, its full output, the class counts EACH labelled with the test that produced it, and the HEAD. Quote the per-symbol rows for the residue. THREE SPECIFIC FAILURES, each because it has already happened once in this Set's history: a count of symbol NAMES presented as a duplication count FAILS (the discarded 58/2711 figure); a single residue number with no test named FAILS; and a pairwise runner-to-runner comparison alone FAILS, because the parent's F10 records that such a check passes while a third copy sits in another module.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the `aw research new` artifact path (tool-created, not hand-named), plus the per-symbol table quoted for EVERY residue symbol (NEITHER-DELEGATES plus ONE-SIDE-DELEGATES; the count is roughly two dozen, so quoting all of them is feasible and is required), each with a disposition and its evidence, plus the explicit still-redundant count reconciling with E-01's output. NOT "the ten largest still-shared symbols", which this item formerly demanded: by agy line count the ten largest are all BOTH-DELEGATE, so that bar would have been satisfied entirely by symbols that are already one implementation. A disposition of "host-specific" asserted without applying the maintainer's "one host does A, the other NOT A" test FAILS for that symbol, and so does a disposition whose only stated basis is a similarity ratio. A symbol pinned immovable (e.g. `disable_lane_prompt` under `UnmovableSymbolTests`) counted as residue rather than named as a documented exception FAILS.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/test_rununify_characterization.py` output, plus the module docstring quoted showing it states the suite was authored AFTER the reconciliations and cannot prove behavior preservation retrospectively. THREE ADDITIONAL FAILURE CONDITIONS. A suite that implies it is the pre-Set baseline FAILS even if it passes. A suite pinning a symbol that E-01 classified BOTH-DELEGATE FAILS for that symbol: name each pinned symbol and show it is in E-02's residue. And a suite containing a source-text assertion FAILS - no `getsourcelines` length pin, no `SequenceMatcher` ratio assertion, no frozen AST census - because commit `d4dd6b88` retired exactly those four days before this plan was authored; state affirmatively that you checked for this class.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the verdict quoted verbatim, its measured basis AND its magnitude (residue count, agy line total, the test used, and which of the Set's work succeeded), the named residue, the confirmation that `gqo6if` covers it with any uncovered residue symbol named, the note on `gqo6if` E-05's undeclared dependency on this plan's test file, and the bare `python3 -m pytest` summary line. TWO SYMMETRIC FAILURES: a verdict of YES that does not reconcile with E-02's residue count FAILS, and so does a bare NO or "unmet" carrying no magnitude, because that is the verdict this plan originally held and the review measured it false. A verdict citing 58 symbols or 2711 lines as the residue FAILS outright.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY files this plan changed, path-scoped; never `git add -A`; never push.
When reporting tests passed, paste the ACTUAL runner output. Do NOT mark an `E-*` item performed for work
not done, and do NOT fill a `V-*` `Observed evidence` block with anything but observed output.

THE HONESTY RULE THAT MATTERS MOST HERE is E-04's verdict, AND IT CUTS BOTH WAYS. This plan exists because a
Set was about to report success, so the obvious pressure on its executor is to write a verdict that lets the
Set close. Three moves are forbidden on that side: calling a symbol host-specific without applying the
maintainer's own "one host does A, the other NOT A" test, writing a YES verdict that does not reconcile with
E-02's residue count, and quietly dropping a residue symbol `gqo6if` does not cover.

BUT THE OPPOSITE PRESSURE IS REAL AND THIS PLAN ALREADY YIELDED TO IT ONCE, which is why the rule is stated
symmetrically. As authored, this plan led with "58 symbols still defined in both runners, the directive is
NOT met" while its own OQ-01 resolution already recorded that figure as wrong; the review re-measured and
found 34 of those 58 have BOTH sides delegating, meaning the number counted the extraction's SUCCESS as its
failure. A pessimistic verdict is not automatically the honest one. So: report the magnitude, name the test
that produced every count, and say plainly what the eleven children DID achieve. A NO verdict with its
magnitude is a successful outcome for this plan. A NO verdict without one is the same defect in the other
direction, and it is worse here than elsewhere because this plan's entire authority is that it measured
carefully.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:` (`.aw/records/plans/pending`,
`tests/test_rununify_characterization.py`, `.aw/records/research`, `tools`). Specifically: UNIFY NOTHING - if
redundancy remains, report it. Do NOT edit either runner, and do not edit `runner_shared`. Do not re-base or
delete any existing guard: several `rununify` suites deliberately assert a symbol is STILL double-defined as a
tripwire, and since this plan changes no code none of them should move; one that fires is a finding about the
measurement. If the work genuinely requires a path outside the fence, make the edit and justify it, since
`aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every
declared-but-unmodified path carries a `--scope-ack`.

SHARED-CHECKOUT NOTE, load-bearing rather than boilerplate for this Set: both runner modules are the
highest-contention files in the repository and the parent records them dirty from a concurrent session at its
own authoring time. This plan only READS them, so contention cannot corrupt its output, but it CAN move its
numbers mid-run. Record the `git rev-parse HEAD` your scan was taken at, and if the runners change under you,
re-scan rather than mixing figures from two HEADs.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`.

OQ-01 IS ANSWERED AND THIS PLAN IS NOT WAITING ON IT. The maintainer resolved it on 2026-09-22 through
`/askme`: retire `5e4sb6`, and file the residue as new work immediately, which `runresidue` (`gqo6if`)
already is. So no blocking question remains open here; OQ-02 is `Blocking: no` and resolved from evidence.
WHAT THIS PLAN'S COMPLETION MECHANICALLY CAUSES, stated because it is the plan's whole reason for existing:
`runner_shared.evaluate_set_retirement` currently refuses to retire `rununify` naming THIS plan as the one
unfinished child, so the moment this plan reaches `executed` the parent becomes retirement-eligible and its
E-02/E-03 tick without an agent turn. That is the sanctioned outcome ONLY because this plan performs both
items and records the verdict. An executor who marks this plan executed without E-04's verdict on disk has
caused exactly the false completion the plan was written to prevent.
