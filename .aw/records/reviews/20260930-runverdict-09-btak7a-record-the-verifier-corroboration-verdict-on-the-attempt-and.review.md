# Review findings: plan btak7a

- Subject-Id: btak7a
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-401 (HIGH, fixed), PR-402 (HIGH, fixed), PR-403 (HIGH, fixed), PR-404 (MEDIUM, fixed), PR-405 (MEDIUM, fixed), PR-406 (LOW, fixed), PR-407 (LOW, fixed), PR-408 (LOW, fixed), PR-409 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `eef2a03e`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `clean` with zero findings after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. `aw check` reports no finding on
this plan, and `aw sanitize --agent` is clean.

THIS IS AN UNUSUALLY WELL-GROUNDED PLAN AND ITS CENTRAL JUDGEMENT IS RIGHT. Every structural claim I could
test re-drove correctly:

- The call site is singular and shared exactly as F-1 says. `runner_shared.execute_item_core`'s
  `if v_outcome_file.is_file():` block already parses `v_data`, calls `map_verdict`, applies
  `has_verifier_test_evidence`, writes all four evidence fields, and holds `attempt["verify_log"]` set a
  few lines above from `spawn_verifier`'s `_v_log`. Both hosts inject their `_spawn_verifier` closure into
  it, so one edit reaches both.
- F-2's hazard is real and quotes verbatim. `run_viewer` has two literal-matching `verification_status`
  sites: one badges only `verified` and `failed`, the other maps `verified` to `yes`,
  `("unverified", "verify-failed", "failed")` to `no`, and falls through to `else: v_disp = "-"`. A novel
  token would render identically to "no verification ran". This is the single most likely wrong turn and
  the plan is right to make it a finding.
- F-3 holds, against a stale in-tree comment that says otherwise. `runner_shared.write_report` is one
  shared function and both hosts' `write_report` are one-line wrappers binding only their `HostLabels`.
  Worth recording that the comment directly above each wrapper still reads "`write_report` is class (c)
  DIVERGED (the two drivers render different reports)", which is now false; that is a pre-existing docs
  defect in a file this plan touches, not something it introduced, and the plan's instruction to VERIFY
  sharing at execution rather than trust it is exactly the right posture.
- `format_verifier_evidence_section`'s byte-identical-when-empty docstring is verbatim.
- F-5 is exact: `test_execute_item_core_refuses_verified_verdict_with_empty_tests_run` names
  `execute_item_core`, and its own docstring says "Simulate outcome parsing in execute_item_core", with a
  hand-written gate in the body. It would pass if the real path were deleted.
- F-6 is exact: `_PRIOR_ATTEMPT_SAFE_KEYS` and the `_PRIOR_ATTEMPT_DRIVER_ONLY_EXAMPLES` comment listing
  `verify_log` as "absolute filesystem path to verification log" among deliberately omitted keys.
- The `StepSummary` seam is exactly as described (`tests_run` and `corrections_made` as sibling fields,
  item-then-outcome-file fallback, reaching all three renderings).
- The module-level import pin is exact: `runner_shared` has precisely two `^from agent_workflows` lines.
- Both carriers resolve: `sinhkj` is `open`, `5xgllt` is `graduated`.

THREE FINDINGS GO TO DEFECTS THAT WOULD HAVE COST THE EXECUTOR REAL TIME, and they share a shape worth
naming: each is a case where the plan's prose was accurate when written and the tree moved, or where the
plan reasoned about code it could not yet see.

PR-401, THE PLAN'S CENTRAL SAFETY PRECEDENT DOES NOT EXIST. E-05 is told to copy the shape of
`tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`, and F-4 calls it "THE SHIPPED
OUTCOME-EQUALITY PRECEDENT". That FILE was deleted in `19313eed`, 1020 lines, the same 2026-09-24 suite
trim this plan already cites for a DIFFERENT deletion (the import-pin guard, noted in its own conventions
section). I checked `19313eed^` and the class was really there at line 763, so the plan's description was
accurate and the author simply did not re-check existence. What makes this more than a citation nit is
that this plan's entire safety argument is "the no-refusal guarantee is pinned by a test of the same shape
as the precedent", and an executor told to copy a missing file either invents the shape without the
guidance or goes looking. TWO `runner_shared` COMMENTS STILL CITE THE DELETED TEST, one saying it "still
holds", so the plan inherited a dangling citation rather than minting one; that belongs to the sweep
`ikxtkj`/`gia5i7` track and I left it alone. E-05 now authors the shape from its description, may consult
the deleted version through `git show`, and is forbidden to imply the path exists.

PR-402, E-01'S PLACEMENT IS UNSAFE AND THE PLAN'S OWN GUARD WOULD HIDE IT. This is the finding I would
most want a maintainer to see, because the failure is silent. `v_data` is bound ONLY in the `else:` branch
of the outcome-parsing `try`; the exception path sets `v_unreadable = True` and leaves `v_data` unbound,
and the existing `if not v_unreadable and isinstance(v_data, dict):` line is precisely what prevents a
`NameError` there, by short-circuiting before `v_data` is named. E-01 says to compute "immediately after
`v_has_evidence`" AND to yield a verdict "for every path through the block including the unreadable-verdict
arm". Those two instructions are jointly unsatisfiable at the outer level: that path runs on the unreadable
arm, touches unbound `v_data`, and raises. And then the plan's own exception guard, which is otherwise a
good idea, converts the `NameError` into `indeterminate` with the computation's reason code, so the
recorded output is indistinguishable from a legitimate unknown. The guard would mask the bug rather than
reveal it. The fix is placement plus a distinguishable reason code: the call goes inside the guarded
region, the unreadable arm gets its `indeterminate` by INITIALIZATION before the guard, and V-01 now
requires driving the unreadable arm specifically and showing its reason code is the initialization one and
not the exception one.

PR-403, THE FUNCTION THIS PLAN CALLS HAS NO NAME. E-01 says "Call Order 08's turn-level verdict".
`bjx20r` describes that function across its E-04 in detail and never declares a symbol; grepping it for
`verifier_corroboration.<anything>` returns only the module filename. So there was no name to cite, and an
executor would have had to guess one or go reading. This is also the one claim in the plan that could not
be verified at review BY CONSTRUCTION, since `bjx20r` is `reviewed` and unexecuted so neither
`agent_workflows/verifier_corroboration.py` nor `tests/test_verifier_corroboration.py` exists yet. That is
the correct state for a dependency, and I recorded it as such rather than as a defect. E-01 now requires
reading the shipped module, reporting the real name and signature in V-01, and STOPPING on an interface
mismatch rather than adapting the call site, because a mismatch between two plans belongs in a corrective
plan.

THE REST ARE SMALLER. PR-404 records the stale `write_report` "DIVERGED" comments as a pre-existing defect
the plan's verify-at-execution instruction already handles. PR-405 adds the suite-trim caution to the
conventions section as a general rule, since this plan is bitten by that commit twice (the deleted
precedent and the deleted import-pin guard) and cites `runner_shared` comments as evidence throughout: a
comment's claim about CODE may be exact while its claim about a TEST is stale. PR-406 and PR-407 supply the
missing suite baseline and the targeted counts, with the caveat that
`tests/test_verifier_corroboration.py` cannot be run until Order 08 lands. PR-408 adds the open-questions
statement to the gate and records that the dependency is real and unmet. PR-409 removes the
self-contradictory "authored `to-review`" sentence from a gate that now carries a review verdict.

OQ-01 IS CORRECTLY LEFT WITH THE MAINTAINER AND I DID NOT RESOLVE IT. It asks whether an `uncorroborated`
turn should eventually be REFUSED. That is a risk-appetite decision against a standing ruling the
maintainer made twice, not something repository evidence settles, and P12 reserves exactly that class to
the human. The plan's handling is the best available: it ships the record, declines the refusal on two
independent grounds (the ruling, and Order 08's own F-5 measuring four ways a genuine run is unmatchable),
names what would make the question decidable (a real-corpus false-negative rate), and carries the question
on backlog `sinhkj` so it survives the plan. Its own composition is also unusually good, stating what the
maintainer is being asked in a paragraph that can be answered from itself.

NOTHING ELSE WAS FOUND WRONG, and several things are notably strong. The decision to add a SEPARATE field
rather than a `verification_status` token is correct and measurement-backed. The instruction to reach all
three renderings through one dataclass field, with the explicit warning against forking a sixth copy of a
per-item predicate, is exactly the right lesson from the `zexed1`/`r2i1b1` history. F-8's argument for why
a record-only change is worth shipping, in the maintainer's own words, is the right defense against "it
changes no behavior" and is the kind of thing most plans omit. The four `Carrier-Declined` reasonings are
substantive, and two of them (live-stream rendering is IMPOSSIBLE rather than postponed; backfilling is
PROHIBITED by an established principle) are the correct distinction between work nobody should own and
work not yet done. The spec-sync analysis is right and unusually careful: recording implements `25kzda`
Section 5.1 and owes no amendment, while a refusal WOULD owe one, which is a second independent reason the
refusal sits behind OQ-01. `Work-Kind: followup` with no release gate is correct for a record-only change
that fixes no live defect.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | IN-SCOPE | Rubric E (testing), Step 1 evidence | `git show 19313eed --stat -- tests/test_suite_baseline.py` reporting 1020 deletions; `git show 19313eed^:tests/test_suite_baseline.py` finding `class NothingRefusesOnTheBaseline` at line 763; the file absent at review HEAD | THE PLAN'S CENTRAL SAFETY PRECEDENT WAS DELETED. E-05 is told to copy `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` and F-4 calls it "the shipped outcome-equality precedent"; the file went in the same `19313eed` trim this plan cites elsewhere. Since the plan's whole safety argument is that the no-refusal guarantee is pinned by a test of that shape, an executor told to copy a missing file either invents the shape unguided or wastes time looking. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now AUTHORS the shape from its description, may consult the deleted version via `git show 19313eed^:...`, and is forbidden to write a docstring implying the path exists; the NAMING convention is kept as the durable half. F-4 rewritten with the measurement and with the two still-dangling `runner_shared` citations recorded as belonging to the `ikxtkj`/`gia5i7` sweep. V-05 requires a grep proving no present-tense citation. |
| PR-402 | HIGH | IN-SCOPE | Rubric A (correctness), G (executability) | the block's structure at review: `try: v_data = json.loads(...)` / `except: v_unreadable = True` (leaving `v_data` unbound) / `else: v_unreadable = False`, then `if not v_unreadable and isinstance(v_data, dict):` guarding every `v_data` read | E-01'S PLACEMENT WOULD TOUCH UNBOUND STATE AND THE PLAN'S OWN GUARD WOULD MASK IT. "Immediately after `v_has_evidence`" plus "a verdict for every path including the unreadable-verdict arm" is jointly unsatisfiable at the outer level: that path raises `NameError` on unbound `v_data`, and the plan's exception guard converts it to `indeterminate` with the computation's reason code, making the defect indistinguishable from a legitimate unknown. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now requires the call INSIDE the existing `not v_unreadable and isinstance(v_data, dict)` region, with the unreadable arm's `indeterminate` arriving by pre-guard INITIALIZATION, and requires the guard comment to say it is not a licence for unsafe placement. V-01 requires the whole guarded region pasted and the unreadable arm driven, failing the item if its reason code is the exception guard's. New F-4b. |
| PR-403 | HIGH | IN-SCOPE | Rubric G (executability), citation discipline | `grep -o 'verifier_corroboration\.[a-z_]*'` over `bjx20r` returns only `verifier_corroboration.py`; `bjx20r` is `reviewed` and both its output files are absent at review HEAD | THE FUNCTION THIS PLAN CALLS HAS NO NAME ANYWHERE. E-01 says "Call Order 08's turn-level verdict" and `bjx20r` describes it in prose across E-04 without declaring a symbol, so an executor must guess or go reading. This is also the one plan claim unverifiable at review by construction, since the dependency is correctly unexecuted. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now requires reading the shipped module, reporting the real symbol and signature in V-01, and STOPPING on an interface mismatch rather than adapting the call site. V-01 requires the symbol reported. New F-4c, which also records that the unverifiability is correct dependency state rather than a defect. |
| PR-404 | MEDIUM | IN-SCOPE | Step 1 evidence, documentation accuracy | both hosts' `write_report` are one-line wrappers over `runner_shared.write_report`, while the comment directly above each still reads "`write_report` is class (c) DIVERGED (the two drivers render different reports)" | F-3 IS CORRECT AND AN IN-TREE COMMENT CONTRADICTS IT. The renderer IS shared, so E-03 is one edit for both hosts; but an executor who reads the comment beside the wrapper they are about to trust will find it asserting the opposite. The comment is a pre-existing defect in a file this plan touches, not one it introduces. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded in the review narrative and left unedited, since the plan's existing instruction to VERIFY sharing at execution (and V-03's requirement to state whether it was still shared) already handles it; striking the comment is out of this plan's scope and belongs with the dangling-claim sweep. |
| PR-405 | MEDIUM | UNDER-SCOPE | Rubric D (invariants), Step 0 conventions | `19313eed` deleted both `tests/test_suite_baseline.py` (PR-401) and `tests/test_orchestrator_probe_cache.py` (already noted in the plan) | THE PLAN IS BITTEN BY ONE COMMIT TWICE AND TREATS THE TWO AS UNRELATED. It notes the import-pin guard's deletion in its conventions and separately cites a deleted precedent as live, both from `19313eed`. Since the plan cites `runner_shared` comments as evidence throughout, the general rule matters: a comment's claim about CODE may be exact while its claim about a TEST is stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a conventions bullet stating the rule, naming both deletions, instructing the executor to verify a cited test file exists before treating it as openable, and noting the dangling-citation class is tracked by `ikxtkj`/`gia5i7` and is not this plan's to sweep. |
| PR-406 | LOW | IN-SCOPE | Rubric G (live-artifact criteria) | bare `python3 -m pytest` at review HEAD: `3523 passed, 2 skipped, 3 warnings in 154.35s`, `208 deselected` | REQUIRED TESTS DEMANDED A REGRESSION RUN WITHOUT GIVING A BASELINE, so an executor had nothing to sanity-check against and no warning that the figure drifts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline recorded as CONTEXT with an explicit re-derivation instruction and the property stated (green plus exactly E-05's additions). |
| PR-407 | LOW | IN-SCOPE | Rubric E (testing) | `tests/test_verifier_evidence.py tests/test_run_viewer.py -o addopts=""` reports `53 passed`; `tests/test_verifier_corroboration.py` is absent until Order 08 executes | THE TARGETED COMMAND NAMES A FILE THAT DOES NOT EXIST YET, which is correct but unstated, so an executor running it before Order 08 lands sees a collection error with no explanation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now records the measured `53 passed` for the two existing files and states explicitly that the third is absent until the dependency executes. |
| PR-408 | LOW | UNDER-SCOPE | Rubric G (execution contract) | OQ-01 `open`, `Blocking: no`, `Owner: maintainer`, `Carrier: sinhkj` (verified `open`) | THE GATE OMITTED THE OPEN-QUESTIONS STATEMENT, so a reader could not tell from the gate whether OQ-01 holds execution (it does not) or who owns it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added an OPEN QUESTIONS paragraph naming the state, the owner, the verified carrier, and why no question gates execution; also recorded that the `executed:bjx20r` dependency is real and measurably unmet. |
| PR-409 | LOW | IN-SCOPE | Rubric G | the gate's "This plan is authored `to-review`" sentence against the plan's new `Status: reviewed` | THE GATE ASSERTED ITS OWN PRE-REVIEW STATE, which reads as self-contradictory once a review verdict is recorded in the same file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the human-approval requirement, which is the part that remains true after review. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The cited outcome-equality precedent was deleted. Restore it, cite it as history, or author the shape from its description? | AUTHOR the shape from the description, permitting a `git show` consultation, and forbid any present-tense citation. | (a) Restore `tests/test_suite_baseline.py`: rejected, the 2026-09-28 maintainer ruling (recorded on backlog `gia5i7`) says guards deleted in the trim will not be restored, and restoring 1020 lines of another subsystem's tests is far outside this plan's scope. (b) Keep citing it as the model and let the executor find it missing: rejected, that is the dangling-citation defect this repository already tracks twice, and reproducing it in a NEW plan is worse than inheriting it. | `git show 19313eed --stat` and `19313eed^` establishing the deletion and the class's prior existence; the `gia5i7` ruling against restoring trimmed pins; the plan's own reliance on the shape rather than on the file. | yes |
| D-2 | E-01's placement would touch unbound `v_data`. Relax the every-path requirement, or constrain the placement? | CONSTRAIN THE PLACEMENT: call inside the existing guarded region, and reach the unreadable arm's verdict by initialization. | (a) Drop "every path including the unreadable arm": rejected, a verifier whose outcome file is corrupt is exactly a case a reader needs a verdict for, and silently having no field there would reintroduce the ambiguity this plan exists to remove. (b) Bind `v_data = None` in the except arm so the outer placement is safe: rejected as a wider change to a block this plan is otherwise careful not to disturb, and it would alter the existing `isinstance(v_data, dict)` guard's meaning for code the plan does not own. | The block's `try`/`except`/`else` structure read at review; the `not v_unreadable` short-circuit as the existing NameError prevention; the plan's own exception guard being what would mask the failure. | yes |
| D-3 | Order 08 declares no symbol name. Invent one here, or require the executor to read it? | REQUIRE the executor to read the shipped module and report the real name, stopping on an interface mismatch. | (a) Name it in this plan (for example `turn_corroboration_verdict`): rejected, that would forge an interface commitment on a plan this one does not own, and if `bjx20r`'s executor chose differently the citation would be a confident falsehood rather than an acknowledged unknown. (b) Leave it as "Order 08's verdict function": rejected, it gives the executor nothing to verify against and no instruction on what to do if the shape differs. | `bjx20r` grepped for any `verifier_corroboration.<name>` returning only the filename; both dependency output files absent at review HEAD; the plan's existing (correct) rule that a change needed in `verifier_corroboration.py` belongs in a corrective plan. | yes |
| D-4 | OQ-01 asks whether an `uncorroborated` turn should be refused. Resolve it from repository evidence, or leave it with the maintainer? | LEAVE IT with the maintainer, unresolved. | Resolving it myself: rejected. It is a risk-appetite decision against a ruling the maintainer made twice (2026-09-08, 2026-09-20), and the evidence that would settle it (a real-corpus false-negative rate) does not exist yet and is Order 08's E-06, which the plan notes will be zero-row in a lane worktree. P12 reserves scope and risk-appetite calls to the human. | Spec `25kzda` Section 5.1 recording both rulings; `runner_shared`'s pre-work-baseline block and its four reasons; Order 08's F-5 measuring four ways a genuine run is unmatchable; backlog `sinhkj` `open` as the carrier. | yes |
| D-5 | The `write_report` "class (c) DIVERGED" comments are now false. Strike them here, or record them? | RECORD them; do not edit. | Striking them in this plan: rejected, they are not what any `E-*` touches, the plan's own V-03 already requires the executor to STATE whether sharing still holds (which surfaces the contradiction to a human), and sweeping stale claims is a tracked separate class (`ikxtkj`, `gia5i7`). | Both hosts' one-line wrappers read at review against the comment text directly above each; `runner_shared.write_report`'s single definition. | yes |

No `Reversible: no` decision was taken in this round. OQ-01 remains `open`, `Blocking: no`,
`Owner: maintainer`, with a verified carrier; it is not a finding left unfixed and so requires no
escalation. Every finding is `FIXED`.
