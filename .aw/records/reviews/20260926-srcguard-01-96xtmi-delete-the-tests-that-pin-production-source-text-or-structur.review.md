# Review findings: plan 96xtmi

- Subject-Id: 96xtmi
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree. Structural preflight `aw ipd lint --phase author --detail`
CONFORMED (exit 0, no advisory) before revision. No pre-review snapshot was needed: `git status
--short` was empty, so the plan was committed and unmodified.

THE AUTHORITY IS GENUINE AND I READ IT RATHER THAN TAKING IT SECOND HAND. Backlog `xelvyi`'s history
carries the maintainer ruling verbatim ("no tests that try to prevent text or code from changing"),
records the reclassification to `chore` with the release gate removed, and explains the reasoning the
plan inherits. The plan's evidence for WHY such tests are wrong is also exact. I split each named
function's docstring from its source and confirmed all three docstring-only passes: every one of
`check_status_untooled`, `check_release_gate_consistency` and `check_scope_drift` appears in
`check_commit_invariants`'s DOCSTRING as well as its code, `orchestrator_row_conformance` appears in
`enforce_orchestrator_shape_gate`'s docstring, and `enforce_spec_edit_ack_gate(` occurs exactly once
in `initialize_run_core` and NOT in its docstring, so the plan is right that a single docstring
mention would break that `== 1`. Both cited commits are real (`94b00d37` "drop source-text pins
redundant with behavioral coverage", `19313eed` "trim test suite from 9,136 to under 2,000 tests") and
`tests/test_run_flag_surface.py` is indeed gone. OQ-03 is right too: `rg -n "def test_no_blocking_mode"
tests/test_platform_lock.py` returns nothing, so the AST-converted guard the backlog item describes is
no longer at HEAD.

I ALSO CHECKED THE PLAN'S SAFETY CLAIMS RATHER THAN ITS REASONING, because the risk here is lost
coverage. Every named existing behavioral test that a DELETE row leans on EXISTS: I resolved ten of
them by name (`test_the_refusal_is_visible_on_the_summary_itself`,
`test_the_send_back_symbols_are_reachable_from_both_hosts`, the three fcntl-blocked platform-lock
tests, `test_non_conforming_run_leaves_no_run_dir_no_session_no_worktree`, both
`..._stop_now_force_level4` twins, `test_unattended_without_flag_REFUSES_and_records_it`, and
`test_exhaustiveness_guard_non_vacuous`), plus `PlanBucketRecognitionTests` with three `plan_bucket(`
call sites, `ConsumerAgreementTests`, and `tests/test_record_placement.py`. I also drove the R2
replacement design end to end in a child interpreter with a blocking `sys.meta_path` finder:
`ipd_schema`, `ipd_lint` and `ipd_authoring` all import cleanly under it and `platform_lock` FAILS on
`filelock`, exactly as the plan states, and `sys.stdlib_module_names` is 3.10+ against a
`requires-python = ">=3.9"`, so the `skipUnless` guard is correctly reasoned. R1's premise holds as
well: `check_commit_invariants` composes exactly those three rules and does not mention
`check_live_bug_gate`, so the negative assertion the plan wants is real.

**THE CENSUS WAS INCOMPLETE, AND THE MISSES WERE OUTSIDE THE FENCE, WHICH MEANS THE PLAN'S OWN FINAL
PROOF WOULD HAVE LIED.** This is the finding that justifies the review. I wrote an independent sweep
shaped differently from the plan's and found three live, passing pins it did not list:

  * `tests/test_isolation_per_action.py::LaunchSiteWiringStructuralTests::test_execute_item_core_does_not_read_isolate_worktree_directly`
    counts `get("isolate_worktree"` in `inspect.getsource(runner_shared.execute_item_core)` and asserts
    zero. The class is literally named `...StructuralTests` and its docstring says "Test structural
    wiring".
  * `tests/test_lane_input_manifest.py::test_revise_lane_inputs_has_no_production_caller` walks the AST
    of every module under `Path(lane_containment.__file__).parent` and asserts the call-site list is
    empty.
  * `tests/test_aw_upgrade_test.py::test_default_sandbox_root_is_computed_not_hardcoded` asserts
    `"DEFAULT_SANDBOX_ROOT = Path("` is absent from `upgrade_rehearsal.py`'s text, which is the exact
    reword-and-it-passes / mention-it-in-a-comment-and-it-fails shape the ruling names.

I confirmed all three pass today (`19 passed` on the two I could narrow cheaply). Each traces to a
specific hole in the authored predicate: an existence-test-only reading of `Path(mod.__file__).parent`,
a `REPO_ROOT / "agent_workflows" / "<f>.py"` read that the anchoring heuristic did not treat as a hit,
and an anchoring requirement applied to `inspect.getsource` at all. And because `- Scope-Paths:` was
DERIVED from the census, all three files were also outside the fence, so E-06 would have re-run the
same blind predicate, reported the expected two KEEP rows, and shipped with three pins alive. The
deliverable to fix is the predicate, not the row list, which is why E-01 now names the three missing
signals and why a census finding exactly 34 is now a FAILED E-01.

**"ALREADY COVERED BY TEST X" WAS A CLAIM ON ROUGHLY TWO DOZEN ROWS, AND THIS REPOSITORY ALREADY RULED
THAT SUCH CLAIMS GET PROVEN.** I verified the named tests EXIST, which is necessary and not
sufficient: existing is not the same as catching the defect. The standard is already set in the tree,
in the very file one of my new findings lives in. `tests/test_lane_input_manifest.py`'s module
docstring records that a prior review proposed four deletions and then REINSTATED all four "after
per-branch sabotage proved each is the sole guard catching its defect", and justified a different
deletion by showing that sabotaging `SEALED_FILE_MODE` from `0o444` to `0o644` reddens the kept test.
Applying that here costs one reverted line per row and is the only thing separating "coverage
survives" from "coverage was asserted", so E-02 now requires it and rows whose named test stays green
are promoted to REPLACE.

ON F-37, THE ONE ROW I WOULD NOT DELETE MECHANICALLY, and where I nearly got it wrong. It is an AST
structure pin, so the ruling covers it, and the naive disposition is DELETE. But it is the SOLE guard
for spec `7ckptx` R3.4 and it was itself introduced BY AN EARLIER REVIEW (PR-802) as the "outcome
test" replacing a docstring pin, so deleting it reverses a prior reviewer's remedy. What resolved it
is the spec's own text, which I went and read: R3.4 is WITHDRAWN, and it says the mechanism "may still
be built ... but nothing in this spec now requires a caller for it; a plan that implements it MUST
state that it has no consumer rather than implying one". That obligation is DOCUMENTARY. There is no
behavior to observe because the requirement is the ABSENCE of a caller, so the honest disposition is
delete the scan and discharge R3.4 in prose, and explicitly NOT to write a replacement test, which
could only be theatre. I flagged it in the gate as the one judgement the maintainer may want to
overrule.

ON WHAT THIS PLAN RISKS, sized honestly because it is unusual. It touches no production file, so
nothing shipped can regress and the failure mode is one-directional: lost coverage. That is why every
defense I added is about proving coverage survives rather than protecting behavior, and it is also why
the suite result is nearly worthless as evidence here. Deleting a test always makes the suite pass, so
"green after the deletions" proves only that nothing ELSE broke. I said so in the gate, in Required
tests, and in V-07, because reporting a green suite as if it settled the coverage question is the most
likely honest-looking mistake an executor could make on this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | UNDER-SCOPE | E. testing; G. executability | independent AST sweep found `tests/test_isolation_per_action.py::test_execute_item_core_does_not_read_isolate_worktree_directly` (`getsource` count), `tests/test_lane_input_manifest.py::test_revise_lane_inputs_has_no_production_caller` (`ast.walk` over the package), `tests/test_aw_upgrade_test.py::test_default_sandbox_root_is_computed_not_hardcoded` (`assertNotIn` over `upgrade_rehearsal.py`); `19 passed` confirming two of them live | **THE CENSUS MISSED THREE LIVE PINS AND THE FENCE INHERITED THE HOLE, SO E-06 WOULD HAVE REPORTED SUCCESS WITH ALL THREE ALIVE.** Each miss traces to a specific predicate gap: `Path(mod.__file__).parent` treated only as an existence test rather than a walk root, a `REPO_ROOT / "agent_workflows" / "<f>.py"` read not recognized by the anchoring heuristic, and an anchoring requirement applied to `inspect.getsource` at all. Because `- Scope-Paths:` was derived from the census, all three files were also undeclared, so the plan could neither delete nor even see them. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Three rows added (F-36/F-37/F-38) with dispositions; the three files added to `- Scope-Paths:`; E-01 now names the three missing SIGNALS and declares a 34-hit census a FAILURE; E-06 must re-run the WIDENED predicate plus an `rg` cross-check; the Concern, summary, Scope check and gate all record the incompleteness. |
| PR-402 | HIGH | UNDER-SCOPE | D. anti-regression; E. testing | `tests/test_lane_input_manifest.py` module docstring: a prior review REINSTATED four proposed deletions "after per-branch sabotage proved each is the sole guard catching its defect", and justified another via a `SEALED_FILE_MODE` `0o444`->`0o644` sabotage | **EVERY "ALREADY COVERED BY X" WAS AN UNPROVEN CLAIM ACROSS ~24 DELETE ROWS.** I verified the named tests EXIST, which does not establish that they CATCH the defect the deleted test caught. The repository has already ruled on exactly this: a prior review reversed its own four proposed deletions once it measured them. Without the measurement, this plan's central safety argument rests on inspection. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 now requires, per DELETE row naming an existing test, a one-line sabotage of the claimed-covered behavior showing the NAMED test goes RED, reverted; a row whose named test stays green is promoted to REPLACE. Structural rows with no behavior to break state that instead. V-02 demands the pairs; a Step 0 convention records the precedent. |
| PR-403 | MEDIUM | IN-SCOPE | A. correctness; F. honest documentation | spec `7ckptx`: "R3.4 WITHDRAWN by R3.3a ... a plan that implements it MUST state that it has no consumer rather than implying one"; `tests/test_lane_input_manifest.py` docstring calls the test the "outcome test ... verifying zero production call sites" introduced per PR-802 | **THE F-37 ROW WOULD HAVE SILENTLY REVERSED AN EARLIER REVIEW'S REMEDY AND DROPPED A SPEC OBLIGATION.** It is the sole guard for R3.4 and was itself written by a prior review as the replacement for a docstring pin. Deleting it as a routine AST pin would leave R3.4's "MUST state that it has no consumer" undischarged and make the test module's own docstring false. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-37's disposition is DELETE WITH A PROSE OBLIGATION, resolved from the spec's own withdrawal text: the requirement is documentary (the absence of a caller is not observable behavior), so E-04 deletes the scan, writes the no-consumer statement into the module docstring, and corrects the now-false docstring description. The row explicitly forbids writing a substitute test, which could only be theatre. Flagged in the gate as the one call a maintainer may want to overrule. |
| PR-404 | MEDIUM | IN-SCOPE | E. verification (a proof that cannot fail) | authored E-06 re-runs the census; the authored predicate cannot see F-36/F-37/F-38 by construction | **THE FINAL PROOF USED THE SAME BLIND INSTRUMENT AS THE BASELINE.** A post-change census run with the authored predicate necessarily reports the two expected KEEP rows whether or not the three missed pins survive, so the plan's terminal evidence was incapable of detecting its own central defect. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 must use the WIDENED E-01 predicate and additionally paste `rg -n "inspect\.getsource\|getsourcelines" tests`, accounting for every surviving line; V-06 states that re-running the narrow predicate proves nothing and is a failed validation. |
| PR-405 | MEDIUM | IN-SCOPE | E. verification (evidence that does not support its claim) | deleting a test always makes a suite pass; authored V-07 presents the green suite as the outcome evidence | **A GREEN SUITE IS NEARLY MEANINGLESS AS COVERAGE EVIDENCE ON A DELETION PLAN, AND THE PLAN LEANED ON IT.** The after-minus-before failing-node comparison proves nothing ELSE broke, which is worth having, but it cannot show that the deleted guards' behavior is still guarded. Reporting it as if it did is the most plausible honest-looking error available here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | An explicit limit added to Required tests, the gate ("A GREEN SUITE IS NOT EVIDENCE ON THIS PLAN"), and V-07, each pointing at the sabotage pairs as the load-bearing evidence. |
| PR-406 | LOW | IN-SCOPE | G. executability | authored E-04 handles mixed behavioral/source tests generically | The three review-found rows each need DIFFERENT handling (whole-class deletion, assert-only deletion keeping a real behavioral call, and deletion-plus-prose), which a generic instruction would get wrong in at least one case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 gains a clause naming each of the three and its shape, including removing the emptied `LaunchSiteWiringStructuralTests` class, keeping `default_sandbox_root()`'s two real assertions, and renaming a test whose name would then misdescribe it. |
| PR-407 | LOW | IN-SCOPE | C. architecture (a fence derived from a fallible census) | `- Scope-Paths:` was built from the census, so a census miss becomes a fence hole | The coupling between census and fence was unstated, so an executor finding a new hit would face a choice between leaving a pin alive and making an undeclared edit, with no guidance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Scope check now states the coupling, instructs that a newly-found hit's file be ADDED (the sanctioned out-of-fence edit for this plan) and justified with `--scope-reason` at finalize, and records that no production file changes so the only risk is lost coverage. |
| PR-408 | LOW | IN-SCOPE | A. correctness (an unverified premise in a REPLACE row) | F-06 names a `failed-safely` requeue in `run_queue`'s `if retry_incomplete:` branch; I could not confirm from reading that the branch is specific to that status rather than a broader terminal set | The replacement test's assertion may need a different shape than the row implies. Not a defect in the plan (the behavior named is real and the test is the right idea), but an unverified premise an executor should know is unverified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-40 naming it a risk to resolve at E-03 by driving the branch, and noting that V-03's per-replacement sabotage will surface a mis-shaped assertion. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The census missed three live pins. Add rows for them, or fix the predicate and let the executor re-derive? | BOTH: widen the PREDICATE with the three named signals AND add the three rows with dispositions, and declare their files. | (a) Add rows only: rejected, the rows would be deleted while the predicate that missed them still governs E-06, so the final proof stays blind and a fourth pin of the same shape survives. (b) Fix the predicate only and let E-01 rediscover them: rejected, it discards measured evidence and leaves the fence short, so an executor whose script differs slightly would not know three specific pins are known to exist. (c) Split them into a follow-up plan: rejected, they are the same defect in the same sweep and the plan's whole claim is completeness; shipping a "delete all source pins" plan that knowingly leaves three is worse than delaying it. | Independent AST sweep at this HEAD; `19 passed` confirming two of the three live; each miss traced to a specific authored-predicate gap. | yes |
| D-2 | Should "covered by test X" rows be sabotage-proven, or is naming plus existence enough? | SABOTAGE-PROVEN, per row. | (a) Existence check only, which is what I could do in review: rejected as insufficient by this repository's own precedent, where a prior review REINSTATED four proposed deletions after sabotage showed each was the sole guard. (b) Sabotage only the rows I judged risky: rejected, the judgement of which are risky is exactly what the measurement exists to replace, and the cost is one reverted line per row. (c) Require it only for REPLACE rows (already required): rejected, REPLACE rows are the SAFE ones; the DELETE rows are where coverage can silently vanish. | `tests/test_lane_input_manifest.py` module docstring recording both the reinstatement and the `SEALED_FILE_MODE` sabotage justification; I verified ten named substitutes exist but could not verify any of them catches its defect. | yes |
| D-3 | F-37 is the sole guard for spec `7ckptx` R3.4 and was written by a prior review. Delete it, keep it as an exception, or replace it? | DELETE the scan and discharge R3.4 IN PROSE; write no substitute test; flag it for the maintainer. | (a) Keep it as a deliberate exception to the ruling: rejected as the reviewer's call to make alone, but offered to the maintainer in the gate since it is a legitimate preference. (b) Replace it with a behavioral test: rejected, there is none to write. The requirement is the ABSENCE of a production caller, which no amount of calling the code can observe; an import-only or `hasattr` test would be theatre that looks like coverage. (c) Delete it silently as a routine AST pin: rejected, it reverses an earlier reviewer's remedy and drops a spec obligation without a record. | Spec `7ckptx`: "R3.4 WITHDRAWN by R3.3a ... a plan that implements it MUST state that it has no consumer rather than implying one" - a documentary obligation; the test module's docstring attributing the test to PR-802. | yes |
| D-4 | Is the green suite acceptable as this plan's outcome evidence? | NO. Demote it explicitly to a no-regression check and name the sabotage pairs as the real evidence. | (a) Leave V-07 as authored: rejected, deleting tests always greens a suite, so the evidence does not support the claim it is offered for, and an executor could honestly report success having proven nothing about coverage. (b) Drop the suite run: rejected, it genuinely proves nothing ELSE broke, which is worth having as long as it is not oversold. | Elementary property of test deletion; the plan's own V-07 wording presented the suite and the collected-count delta as the outcome. | yes |
| D-5 | Three review-found rows need three different edit shapes. Instruct generically or per row? | PER ROW, naming each shape. | (a) Generic "delete the source-reading statements": rejected, it would delete `default_sandbox_root()`'s real assertions in F-38 or leave an empty class behind in F-36. (b) Leave the shapes to executor judgement: rejected, the whole point of the row is to remove judgement about what is a pin and what is behavior. | Read each of the three tests: F-36's class holds only that test, F-38 mixes one text assert with two real behavioral asserts, F-37 carries a spec obligation. | yes |

### Deferred and open

- (none). All eight findings were FIXED in place. None reached Medium-High or High Remediation Risk, so
  the Fix Bar permitted no deferral. PR-401 and PR-402 are the two Medium-overall ones, both on the
  functionality axis, and both were fixed by making the plan PROVE things it had asserted rather than
  by reducing its scope.
- No question required the human, and both authored open questions were verified rather than accepted:
  OQ-01's ruling is quoted verbatim on backlog `xelvyi`, and OQ-03's claim that the `blocking=True`
  guard is absent at HEAD was re-measured (`rg` returns nothing). OQ-02's KEEP-NOT-A-PIN reasoning for
  the two leak self-clean tests is sound: they assert a property of shipped CONTENT that a package
  consumer could observe, and they do not fail when code is restructured.
- One judgement is surfaced FOR the maintainer without blocking: F-37's delete-plus-prose disposition,
  which reverses an earlier review's remedy for a WITHDRAWN spec requirement. It is raised in the gate
  rather than as a `Blocking: yes` question because the plan is executable and correct as revised, and
  because the alternative (keep one AST pin as an exception) is a preference rather than a correctness
  question.
- No `Reversible: no` decision was made. All five decisions are plan-text choices on an unexecuted
  plan.

HONEST LIMITS, stated because they bound what this round proves. FIRST, and most important: I verified
that every named substitute test EXISTS but I did NOT sabotage-prove that any of them catches its
defect. That is precisely the gap PR-402 makes the plan close, and it means my review does not
establish that the ~24 DELETE rows are safe; it establishes that the plan must prove it. SECOND, my
census sweep is differently shaped from the plan's and found three pins it missed, which is evidence
that a THIRD shape could find a fourth; neither census is provably complete, and the widened predicate
inherits that limit. I chose signals that catch the three observed misses rather than claiming a
general definition. THIRD, I did not run the full suite: this review changed no code, and E-07 owns
that. FOURTH, I could not confirm F-06's premise about which statuses `retry_incomplete` requeues
(recorded as F-40), so one REPLACE row's assertion shape remains unvalidated. FIFTH, I did not audit
the KEEP-NOT-A-PIN reasoning against the maintainer's intent beyond the text of the ruling; if the
maintainer considers a sanitizer-over-shipped-file test a source-reading test, F-13 and F-17 would
also become deletions, and only they can settle that.
