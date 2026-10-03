# Review findings: plan p5yaqw

- Subject-Id: p5yaqw
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (BLOCKER, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `72748c1c`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
`--phase review-finalize --agent` reports `clean` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply. `aw check` reports 69 findings across the tree and NONE
on this plan, before or after.

THE PLAN'S CENTRAL PREMISE IS FALSE AND THE WHOLE PLAN TURNS ON IT. `artifact_audit._status_disagrees`,
the function the plan exists to refactor, is DEAD CODE. Commit `33834c719` (IPD `mlhryi`, 2026-09-28)
replaced the expression `status_mismatch=bool(file_status is not None and _status_disagrees(recorded,
file_status))` with `status_mismatch=status_mismatch` computed from `allowed_lifecycle_pairs`, and in so
doing deleted the only call site. I proved this three independent ways rather than trusting one grep,
because the claim invalidates most of the plan and a reviewer who gets it wrong does real damage:

1. `grep -rn 'status_disagrees' --include='*.py' --include='*.toml' --include='*.json' .` over the whole
   repository returns exactly ONE line, `agent_workflows/artifact_audit.py:1196:def _status_disagrees(`,
   which is the definition itself. No test, no module, no config names it.
2. An `ast.walk` over `artifact_audit.py` collecting every `Name` and `Attribute` node for that
   identifier prints `definition lines: [1196]` and `LOAD sites (callers): []`. A grep can miss a
   dynamic access; this rules out a textual reference I mis-filtered.
3. A call-counting spy installed over the module attribute, then driving `audit_artifact` against
   temporary git repos for all eight statuses the plan's own F-01 claims to measure, prints
   `_status_disagrees call count during 8 audits: 0` while every audit still returns
   `has_discrepancy=False difference_class=unchanged`. This is the decisive one: it shows the OUTCOMES the
   plan attributes to the helper are produced without it being entered.

`git log --oneline -S '_status_disagrees'` names only `5f1591731` (which introduced it) and `33834c719`
(which removed the call), consistent with all three.

WHAT THAT COSTS THE PLAN, item by item, is worth stating because the damage is not uniform. E-03's
refactor would have rewritten unreachable code. E-01 and E-02 would have written tests that pass or fail
on a predicate no output depends on; E-02 explicitly asserted `_status_disagrees` equals a derived
predicate, which is a test of nothing an operator can see. E-04's second clause would have rewritten the
docstring of a function about to be deleted. And worst, V-01 and V-03 each REQUIRED a mutation
demonstration that cannot possibly fail: V-01 told the executor to narrow the tolerance arm to
`interrupted` and paste the failing node ids, V-03 to remove the `SUCCESS_STATES` guard and paste
`approved` becoming tolerated. I installed V-01's exact mutation and re-ran the eight audits: every one
still returns `has_discrepancy=False`, unchanged. An executor following this plan in good faith would
reach a mutation that produced no failure and then either fabricate the evidence or halt mid-plan. That
is the specific failure mode the repository's "paste the actual runner output" rule exists to catch, and
here the plan itself would have forced the choice.

SO THE PLAN IS REWRITTEN AROUND WHAT IS ACTUALLY TRUE, keeping its one surviving defect and its one
surviving goal. The surviving goal is the scope fence (original F-03, which I verified intact and which is
the item's real ask): nothing pins the tolerance or its counterexample at the surface an operator reads,
and `tests/test_artifact_audit.py` now holds 21 tests none of which drives a terminal-failure status in
either direction. The surviving defect is the false docstring claim (original F-06). To those the revision
adds the deletion of the dead helper, and replaces the plan's measurements of the dead helper with
measurements of the LIVE mechanism.

THE LIVE BEHAVIOR, MEASURED, because the plan now needs a true baseline to pin. Driving `audit_artifact`
over all 24 members of `runner_shared.TERMINAL_STATES` in both shapes yields a clean trichotomy: 22
members are TOLERATED unmoved-at-`approved` and FLAGGED moved-at-`executed`; `executed` inverts both;
`retired` is flagged in BOTH shapes because its expected directory is a retirement directory. No status is
tolerated in both shapes, which is precisely the property `vdabn5` argued for and the item's
counterexample demanded, and it is a stronger statement than the plan's eight-status probe. The tolerance
itself is already DERIVED, not enumerated: `allowed_lifecycle_pairs('plans','execute',st)` returns the
identical six `(pre-terminal,'pending')` pairs for every non-success, non-retired status, from
`record_placement.target_subdir` rather than a literal list. So the plan's convention argument ("this
module prefers derivation") was correct and already SATISFIED in live code, which is the reason to delete
the leftover rather than convert it.

WHAT THE PLAN GOT RIGHT, since most of its measurements reproduce. F-04's 384-pair sweep reproduces to
the digit (naive 11 divergences, refined 6, all `timed-out`; `SUCCESS_STATES == {'approved','executed',
'reviewed'}`), so its author was careful, merely measuring the wrong function. F-02's git archaeology on
`05e77dfc` is accurate, F-03's deleted-test archaeology is accurate, F-05's `timed-out` absence is
accurate, F-06's docstring claim is accurate, and F-08's two backlog relocations are accurate. The
Carrier-Declined reasoning throughout is substantive rather than formulaic. The sequencing argument
(tests before the change) is the right instinct and is kept, with a corrected rationale.

TWO FURTHER MEASUREMENT LIMITS I found in F-04 and recorded, because they bear on how far a reader may
trust an equivalence sweep. The claimed equivalence is NOT general: sweeping 22 statuses outside the
plan's chosen vocabulary (`''`, `foo`, `pending`, `open`, `done`, `graduated`, `parked`, `deferred`,
`skipped`, ...) against 14 declared values yields 97 further divergences, so "behavior-preserving" held
only on the hand-picked set. And `canonical_terminal_status` is identity for an unknown token, so an
unrecognized status would have been tolerated by the derivation rather than compared. Neither matters now
that the code is deleted, but a future reader reaching for the same refactor shape should know the sweep
was narrower than it reads.

F-07 IS THE OPPOSITE OF THE TRUTH, and it has already propagated into a committed record. The plan claims
`substantially-complete` is flagged where `complete` is tolerated. Through the live entry point BOTH are
flagged in the moved-at-`executed` shape, because `_RUN_SUCCESS_STATUSES` is `{'executed'}` alone and
`complete` is not a member. There is no asymmetry in behavior. The appearance of one came from comparing
`_status_disagrees('substantially-complete','executed')` (True) with
`_status_disagrees('complete','executed')` (False), both dead. Backlog `64a03w` was filed from this
finding while the plan was authored and quotes exactly that pair as its central evidence, so it now
documents a difference that is not observable and cites code this plan deletes. I corrected the plan's row
and OQ-02, and left the item itself alone: it is not a declared `Scope-Path`, and rewriting another
record's premise is a separate act with its own owner. The Deferred row carries `64a03w` and F-07 now
carries the live measurement a future reader needs.

THE BASELINE WAS STALE AND WRONG IN BOTH DIRECTIONS. The plan asserts `3291 passed, 2 skipped` with `207
deselected` at `928be376`, which is 571 commits behind review HEAD. A bare run on a clean tree gives
`1 failed, 3498 passed, 2 skipped, 3 warnings in 193.01s` with `208 deselected`, so the total was wrong by
210 tests. The single failure is PRE-EXISTING and UNRELATED: `tests/test_backlog.py::
BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` expects a `2026-09-30` history
line where the setter writes `2026-10-01`, a UTC-versus-local date split already filed five times over
(`fnb8pl`, `lq2w86`, `2wae2x`, `o8l2y2`, `tl8qmc`). The plan said "any post-change failure must be a node
id absent from that green run", which would have sent an executor chasing a defect in a file the plan may
not touch. The revision names the failure, names its owners, forbids editing `tests/test_backlog.py`, and
requires the baseline be RE-DERIVED rather than compared against a literal, since the count moves with
every merged lane.

THREE SMALLER FIXES. The gate hand-wrote the instruction "do not hand-write a `- Readiness:` field" into
a plan now carrying one as a review output, which reads as self-contradictory once a review has run; it is
removed and replaced by the open-questions statement and a real scope fence, which the gate lacked
entirely. The post-gate lifecycle unconditionally instructed `aw ipd set executed`, which is wrong under a
runner that owns the transition; it is now conditional. And the spec-sync section asserted that no
`.spec.md` governs the predicate without showing the check; I grepped `.aw/records/specs/` and the four
`artifact_audit` matches are all `FinalizeEvidenceIndex`, `_INDEX_CACHE`, or migration-surface references
in `4sd62s` and `z7nbn1`, so the claim is true and the evidence is now in the plan.

NOTHING ELSE WAS FOUND WRONG. The `Scope-Paths` are right and minimal. `From-Backlog: qpgs4t` resolves.
`Work-Kind: chore` is correct and needs no `Blocks-Release`: nothing user-visible is wrong today, since
the dead helper produces no output and the missing test is a coverage gap rather than a defect an operator
can perceive. The four E-items remain well right-sized (one concern each, one focused pass each, and each
maps to exactly one V-item). The E/V bijection holds. No `Blocking: yes` question exists, so no lint gate
is tripped. The sibling plan `qvfd4l` explicitly lists `artifact_audit._status_disagrees` among sites it
leaves alone as "correct by construction because it accepts both spellings deliberately", which is a
second record carrying the same mistaken belief that the helper is live; I note it here rather than
editing that plan, since it is out of scope and its own conclusion (do not touch it) remains right.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | Rubric A (correctness), D (invariants), G (executability) | `agent_workflows/artifact_audit.py` `def _status_disagrees`; commit `33834c719` replacing `status_mismatch=bool(file_status is not None and _status_disagrees(recorded, file_status))` with `status_mismatch=status_mismatch` | THE PLAN'S SUBJECT IS DEAD CODE. `_status_disagrees` has had no caller since `33834c719` (IPD `mlhryi`, 2026-09-28); the repository contains one occurrence of the name, its own `def`. The live tolerance is `allowed_lifecycle_pairs`. So E-03's refactor would rewrite unreachable code and E-01/E-02 would pin a predicate no output depends on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Plan re-scoped: the helper is now DELETED (E-04) rather than refactored, the tests pin the LIVE mechanism through `audit_artifact` with `artifact_type`/`action` set (E-01), and the Concern, Scope, Goal, Proposed changes and Scope check are rewritten around the measurement. New F-01 records all three unreachability proofs; new F-02 records that the live predicate is already derived. |
| PR-002 | BLOCKER | IN-SCOPE | Rubric E (testing), Step 1 evidence honesty | plan V-01 and V-03 mutation clauses; measured by installing V-01's exact mutation | TWO REQUIRED VALIDATION DEMONSTRATIONS WERE IMPOSSIBLE TO SATISFY. V-01 required narrowing the tolerance arm to `interrupted` and pasting failing node ids; V-03 required removing the `SUCCESS_STATES` guard and pasting `approved` becoming tolerated. Neither mutation can fail anything. Measured: with the arm narrowed to `rec == "interrupted"`, all eight audits still return `has_discrepancy=False`. A faithful executor would have had to fabricate evidence or halt. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | V-01's mutation retargeted at the LIVE predicate (monkeypatch `allowed_lifecycle_pairs` to return one pair) with an explicit prohibition on the old mutation and a warning not to record its green result as a pass. V-02 gains two real drift mutations (`TERMINAL_STATES` and `_RUN_SUCCESS_STATUSES`). V-03 becomes docstring-only evidence; V-04 becomes the deletion's three-way unreachability re-proof. New F-11 records the measurement. |
| PR-003 | HIGH | IN-SCOPE | Rubric A (correctness), Step 1 evidence | plan F-07 against `audit_artifact` moved-at-`executed`; `_RUN_SUCCESS_STATUSES == frozenset({'executed'})` | F-07 ASSERTS THE OPPOSITE OF THE LIVE BEHAVIOR. It claims `substantially-complete` is flagged where `complete` is tolerated. Both are FLAGGED through the real entry point, because `complete` is not in `_RUN_SUCCESS_STATUSES` either. The asymmetry existed only between two return values of dead code, and it has already propagated into committed backlog `64a03w`, whose central evidence is that pair. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-07 rewritten with the live measurement and an explicit note that it reverses the original claim. OQ-02 rewritten: the question rested on a false premise, there is no behavior to fix, and what remains is a RECORD correction owned by `64a03w`. The Deferred row now describes correcting that item (carrier `64a03w`) rather than fixing code, and the Scope check forbids editing it here. |
| PR-004 | HIGH | IN-SCOPE | Rubric E (testing), Rubric G (live-artifact criteria) | plan F-10 and Required tests; bare `python3 -m pytest` on a clean tree at review HEAD | THE BASELINE IS STALE AND ITS "any post-change failure" RULE WOULD MISFIRE. The plan asserts `3291 passed, 2 skipped, 207 deselected` at `928be376`, 571 commits back; the real figure is `1 failed, 3498 passed, 2 skipped, 208 deselected`, wrong by 210 tests. The one failure is a pre-existing UTC-versus-local date split in `tests/test_backlog.py`, filed five times over, which an executor following the plan would have treated as a regression caused by their own change. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-10 rewritten with the review-HEAD measurement, the failing node id, and its five owning backlog ids. Required tests now names the failure as EXPECTED, forbids editing `tests/test_backlog.py`, and requires the baseline be re-derived in the executing worktree rather than compared against a literal. V-04 states the failure may appear in both runs without being a regression. |
| PR-005 | MEDIUM | IN-SCOPE | Step 1 evidence, Rubric D | plan F-04; 22 additional statuses crossed with 14 declared values | F-04's EQUIVALENCE IS NARROWER THAN IT READS. The figures reproduce exactly, but sweeping statuses outside the plan's chosen vocabulary yields 97 further divergences (`open` 7, `done` 7, `implemented` 7, six each for `''`, `foo`, `pending`, `graduated`, `parked`, `deferred`, `skipped`, `unknown`), and `canonical_terminal_status` is identity for an unknown token, so an unrecognized status would have been newly tolerated. "Behavior-preserving" held only on the hand-picked set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 rewritten to credit the reproduction, state plainly that it measured the dead helper, and record both limits with the 97-divergence measurement and the identity-canonicalization note, so a future reader reaching for the same refactor shape knows what the sweep did not cover. |
| PR-006 | MEDIUM | UNDER-SCOPE | Rubric E (testing) | plan E-02 as authored; `sorted(runner_shared.TERMINAL_STATES)` (24 members) | E-02's PIN WAS AN EQUIVALENCE BETWEEN TWO PREDICATES, NOT A BEHAVIORAL PROPERTY, so even setting PR-001 aside it would not have pinned anything an operator reads, and it restated the vocabulary as a literal list of 23 plus aliases, which is the hand-maintained enumeration the plan objects to, relocated into a test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 rewritten to sweep `runner_shared.TERMINAL_STATES` read AT TEST TIME, assert the measured trichotomy from F-05, and derive its expectation from `expected_dir_for_status` rather than restating it. V-02 requires showing the swept set EQUALS the live set rather than covering a subset, and adds the fabricated-member mutation that makes a driver's new status fail the test. |
| PR-007 | MEDIUM | UNDER-SCOPE | Rubric G (execution contract) | plan gate as authored | THE GATE LACKED A SCOPE FENCE ENTIRELY, instructed the executor NOT to hand-write `- Readiness:` in a plan that now carries one as a review output (self-contradictory once read post-review), and made the lifecycle transition an UNCONDITIONAL `aw ipd set executed`, which is wrong under `aw oc run`/`aw agy run` where the runner owns it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: added a declaration-style scope fence naming the two files and the two specific out-of-scope temptations review measured, added the open-questions statement, named the ONE genuine stop condition (a found caller at E-04's re-proof, a prerequisite-absent condition rather than a scope question), removed the `- Readiness:` instruction, and made the terminal transition conditional on runner versus human execution. |
| PR-008 | LOW | IN-SCOPE | Rubric A, documentation accuracy | plan E-04(a) and F-06; `oc_runipd.py` and `agy_runipd.py` each reading `TERMINAL_STATES = runner_shared.TERMINAL_STATES` | THE DOCSTRING'S SECOND INACCURACY WAS UNNOTICED. Both the docstring and the plan speak of "BOTH host drivers' `TERMINAL_STATES`" as if two sets were cross-checked; both are plain aliases of one `runner_shared` set, so a test sweeping it covers both hosts by construction and there is no cross-driver check to make. The plan would have fixed the false test-pin claim while preserving the misleading framing beside it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 (formerly E-04(a)) now corrects BOTH sentences and states the single-set fact; F-06 records the alias measurement; V-03 requires pasting the two alias lines as evidence. |
| PR-009 | LOW | IN-SCOPE | Rubric G, spec sync | plan Spec/documentation sync section | THE SPEC-SYNC "N/A" RESTED ON AN UNSHOWN CHECK. It asserts no `.spec.md` governs the predicate without evidence, which is exactly the shape of claim this plan's own F-06 finds rotting elsewhere in the module. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section now cites the grep: the four `artifact_audit` matches under `.aw/records/specs/` are in `4sd62s` and `z7nbn1` and all reference `FinalizeEvidenceIndex`, `_INDEX_CACHE`, or the module as a migration surface, none the status-tolerance predicates. The claim is true and now checkable. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `_status_disagrees` is dead. Delete it, refactor it anyway, or mark the plan `REJECT - NEEDS REPLAN`? | DELETE it, and re-scope the plan around pinning the live mechanism. The plan's goal (a scope fence over the eight statuses) and one of its findings (the false docstring claim) survive intact, so the repair is bounded. | (a) `REJECT - NEEDS REPLAN`: rejected because the plan's real deliverable is the restored test fence, which is valid, needed, and unaffected by the premise error; replanning would discard correct work and lose the author's accurate git archaeology. (b) Refactor the dead code to the derived shape anyway: rejected, it produces a tidier unreachable function and leaves the hazard that misled this author in place. (c) Leave the helper and only add tests: rejected, a 23-entry enumeration with a 17-line docstring about tolerance bands is actively misleading, and two separate records (`64a03w`, `qvfd4l`) already reason from it as if live. | `33834c719`'s diff removing the call; the three unreachability proofs in F-01; dead-code deletion precedent in sibling pending plans `qdro85` and `38pxaz`. | yes |
| D-2 | What should the tests pin, now that the equivalence pin is meaningless? | The measured trichotomy over the whole closed vocabulary `runner_shared.TERMINAL_STATES`, read at test time, with the expectation derived from `expected_dir_for_status`. | (a) Pin only the eight statuses `qpgs4t` names: rejected as weaker than available; the live predicate does not distinguish statuses (F-02), so sweeping the full set costs nothing and catches a driver adding one. (b) Pin a literal list of expected values: rejected, that relocates the hand-maintained enumeration into the test, which is the practice the plan objects to. | F-05's 24-member measurement through `audit_artifact`; `allowed_lifecycle_pairs` returning identical pairs for every non-success status; AGENTS.md P16 (test outcomes, not structure). | yes |
| D-3 | Backlog `64a03w`'s central claim is measurably false (PR-003). Correct it here, or leave it? | Leave the item; record the correction in the plan's F-07 and name `64a03w` as the carrier. | (a) Edit the item in this review: rejected, it is not a declared `Scope-Path`, this review's own contract is to edit planning documents for the plan under review, and silently rewriting another record's premise removes the evidence of how it got there. (b) Add a Scope-Path for it: rejected as scope creep on a plan that changes no behavior for either status. | The item's own text quoting the two `_status_disagrees` return values; F-07's live measurement; the repository rule that a record's history is not rewritten in place. | yes |
| D-4 | The plan's suite baseline is stale and one test fails for an unrelated reason. Update the figure, or convert it to a re-derivation? | Both: record the review measurement WITH the failing node id and its five owning backlog items, and require the executor to re-derive rather than compare against the literal. | (a) Update the number only: rejected, it is a live artifact count that will drift again before execution (it already drifted by 210 across 571 commits), which is exactly the live-artifact criterion the rubric forbids as a bar. (b) Delete the baseline: rejected, an executor needs to know the one failure is expected or they will chase it into a file the plan may not touch. | Bare `python3 -m pytest` at review HEAD on a clean tree; the five open date-split backlog items; plan-review Rubric G's live-artifact re-derivation convention. | yes |
| D-5 | Sibling plan `qvfd4l` (status `reviewed`, readiness `go-pending-approval`) lists `_status_disagrees` as a site "correct by construction", reasoning from it as live. Correct that plan too? | No. Note it in this review record only. | (a) Edit `qvfd4l`: rejected, it is outside this review's scope ledger, and its CONCLUSION (do not touch the site) remains correct whatever the reason, so no executor is misled into a wrong action. (b) File a backlog item: rejected, once `p5yaqw` executes the symbol is gone and that plan's OUT list simply names something absent, which is harmless and self-resolving. | `qvfd4l`'s Scope line listing the symbol among sites left alone; F-01's unreachability proofs; this plan's E-04 deleting the symbol. | yes |

No `Reversible: no` decision was taken in this round. Both open questions are `resolved` and neither is
`Blocking: yes`, so no finding required escalation into the plan as a blocking question: every finding is
`FIXED`.
