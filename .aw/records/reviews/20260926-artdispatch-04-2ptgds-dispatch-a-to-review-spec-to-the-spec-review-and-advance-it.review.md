# Review findings: plan 2ptgds

- Subject-Id: 2ptgds
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Re-verified at lane HEAD `9c94ff0b`. Every claim in the plan's own Findings table (F-1 through F-5)
was re-derived by direct call, by reading the cited symbol verbatim, or by reproducing the behavior on
a scratch repository, and every one reproduced. F-4 was additionally reproduced END TO END, which the
author had only cited: the setter refuses without a record, succeeds with one, and MOVES the spec from
`to-review/` to `reviewed/`. That move turned out to matter (F-10).

THE ONE HIGH FINDING IS THAT A CLAUSE WRITTEN AS POLICY IS ACTUALLY A CRASH. The plan's scope (d)
says the `--full-auto` approval bridge "is NEVER applied to a spec", and E-03 asks the executor to
"ensure" it is skipped. Both read as statements about intent. The code disagrees: the bridge's FIRST
statement is `resolve_plan_path(...)`, it sits OUTSIDE the `try:` that opens on the next line, and
plan `mxzogk` (already EXECUTED) makes that call fail closed on a `.spec.md`. So the first
`--full-auto` run whose spec review SUCCEEDS raises `DriverError` out of `execute_item_core`, both
hosts catch it item-locally, and the item is recorded `failed-safely` with a resolver message after a
review that actually worked. An executor reading "ensure it is skipped" would plausibly satisfy
themselves that no spec-specific code calls the bridge and move on, which is exactly the reasoning
that leaves the crash in.

Three MEDIUM findings share a shape worth naming once: the plan asserts that an existing shared
mechanism already does what a spec needs, and in each case the mechanism keys on something a spec does
not have. `item_needs_approval` keys on `action != "review"` (F-7). `classify_review_writes` keys on
the id6 appearing in the PATH (F-8). And `reconcile_disposition`'s position in the call order means
the artifact it reads may exist only as uncommitted lane files (F-9). None is fatal; all three are
places where "confirm X already works" had to become "make X work".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | high | UNDER-SCOPE | A. Correctness / D. Anti-regression | `execute_item_core`'s `--full-auto` bridge read verbatim; `oc_runipd.run_queue`'s `except DriverError as exc: runnable["status"] = "failed-safely"`; plan `mxzogk` scope (b) | THE `--full-auto` BRIDGE CRASHES ON A SPEC RATHER THAN NEEDING A POLICY SKIP. The bridge is `if is_review and disposition in ("reviewed","approved") and full_auto:` and its FIRST statement is `plan_curr = resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])`, OUTSIDE the `try:` that opens on the following `set_plan_approved`. Executed plan `mxzogk` makes `resolve_plan_path` raise `DriverError` naming the detected type for a `.spec.md`. So the first `--full-auto` run whose spec review SUCCEEDS raises out of `execute_item_core` and the item lands `failed-safely` with a resolver message AFTER a successful review. Scope (d) and E-03 both describe this as skipping a policy, so nothing in the plan would have produced the guard. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | New E-04 requires an explicit `queue_entry_type(item) != "ipd"` guard placed BEFORE the resolve, forbids widening the `try` (which would convert the crash into a silent skip and lose the diagnostic for a genuine plan-path failure), and E-08's first case must FAIL against a build without it with the `driver_error` pasted. Recorded as the plan's own F-6. |
| PR-002 | medium | IN-SCOPE | A. Correctness / F. UX | `item_needs_approval("reviewed","review")` -> False; `item_needs_approval("to-review","review")` -> False; `grep -n NEEDS_INPUT_KEY` -> definition plus ONE write site, in the queue builder | E-03's `item_needs_approval` CLAIM IS FALSE TWICE OVER, so the human-approval gate spec `25kzda` 3.3 mandates has no reporter on the spec path. (1) The predicate returns `(action != "review") and status == "reviewed"`, False by construction for a review item. (2) `NEEDS_INPUT_KEY` is written ONCE by the queue builder from the frozen `initial_status` and never recomputed, so a to-review spec freezes `needs_input: False` and stays there. The plan path is not a counterexample and explains the asymmetry: a reviewed plan's gate appears because the full-auto bridge REQUEUES it as `action: execute`/`status: queued` and the next derivation sets the flag; a spec has no execute action and gets no second pass. The authored instruction ("confirm the spec path records the approval gate as `needs_input`") would have the executor confirm something impossible and then either weaken the claim silently or edit a predicate the plan path depends on. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | New E-05 requires a reader census of `NEEDS_INPUT_KEY` and a RECORDED choice between a post-turn durable write and reporting from the disposition, explicitly forbidding any change to `item_needs_approval`'s semantics. New OQ-02 raises the question the plan answered wrongly. E-08 asserts the gate on the run record and summary rather than on the predicate, with a control that the plan answers are unchanged. Recorded as F-7. |
| PR-003 | medium | IN-SCOPE | A. Correctness | `classify_review_writes([...], id6="aaaaaa")` allows both id6-bearing paths; `discover_specs` over the corpus -> 1 of 19 id-bearing specs whose filename lacks its id6 (`4w7d6s`, legacy naming); all 12 `Subject-Type: spec` records carry their subject id6; `commit_review_shared_output`'s `elif str(id6) in cand` | E-04's PREMISE ("`classify_review_writes` keys on the id6, which the spec path and the record path both carry") IS TRUE FOR THE RECORD AND NOT UNIVERSALLY TRUE FOR THE SPEC. Both scope helpers substring-match the id6 against the PATH, so a spec whose filename does not contain its id6 has its OWN FILE classified out of scope and left uncommitted in the lane, where teardown is the only thing that sees it. One such spec exists today and the repository GRANDFATHERS pre-cutover legacy spec names indefinitely, so this is a supported naming shape rather than a defect to fix elsewhere. The records are clean, so the exposure is exactly the spec file, which is the one file the review must not lose. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 (formerly E-04) now requires the allowed set for a non-`ipd` entry to include the artifact's OWN resolved path from `queue_artifact_path` in addition to the substring rule, so scope never depends on a convention the repository does not enforce; E-01 enumerates the legacy-named populations as live figures; E-08's scope case must fail against a build relying on the substring rule alone. Recorded as F-8. |
| PR-004 | medium | UNDER-SCOPE | A. Correctness / C. Architecture | call order inside `execute_item_core`: `reconcile_disposition` precedes `commit_review_lane_output`, which precedes `integrate_review_lane_branch`, which precedes the bridge; `review_findings.subject_review_records` reads with `open()`; the review rung already uses `source = plan_repo or repo` | E-03 READS THE OUTCOME BEFORE THE OUTPUT IS COMMITTED AND NEVER SAYS WHICH TREE. At disposition time the spec's new `- Status:` and its review record may exist only as UNCOMMITTED working-tree files in the lane, and are certainly not in main. The gate is survivable and in fact correct ONLY because both predicates are filesystem reads; the obvious alternative readings (consult main, or consult git) each yield a gate that refuses every correct review. The plan's parenthetical "(lane copy when isolated, as the plan branch reads `plan_repo`)" gestures at this but states neither the ordering nor the filesystem-read dependency, so an executor has no way to know which of their options is the safe one. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now states the ordering, names `source = plan_repo or repo` as the root to pass to BOTH predicates, requires a comment at the call site, and E-01 must paste the trace table with a CALL-ORDER column showing the disposition ahead of the commit and the integration, plus evidence that both reads are filesystem reads. Recorded as F-9. |
| PR-005 | low | IN-SCOPE | A. Correctness / G. Plan executability | reproduced: `aw specs set --status reviewed` moved `to-review/...` -> `reviewed/...`; the frozen path's `is_file()` is False afterwards; `discover_specs` returns the new path under the same id6 | THE SPEC MOVES DIRECTORY ON `reviewed`, SO THE FROZEN `configured_file` IS STALE ON EXACTLY THE SUCCESS PATH, and the plan never says so. Its instruction to resolve through `queue_artifact_path` HANDLES this (that helper resolves a spec through `discover_specs`, which keys on `- Id:` and is location-independent), but with no reason given, an executor optimizing to a cheaper `repo / item["configured_file"]` read would silently reintroduce the bug and observe it only as a spurious `fail-gate` on the one path that matters. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states the move as the REASON for `queue_artifact_path` and forbids the cheap read; E-01 reproduces the move and shows `discover_specs` resolving the new path; E-07 case (2) asserts the advanced case passes while the spec has moved. Recorded as F-10. |
| PR-006 | low | IN-SCOPE | G. Plan executability / prose | `commit_review_shared_output` writes "... Path-scoped to the plan under review and its review record; hooks ran normally." as the COMMIT BODY, in addition to the docstring sentence E-04 quotes | E-04 NAMES ONE PLAN-SHAPED STRING AND THERE ARE TWO. The function's docstring and the commit message it writes both read "Path-scoped to the plan under review and its review record". Generalizing only the docstring leaves the commit body asserting "the plan under review" for a spec review, which lands in permanent git history where it cannot be corrected in place. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 requires BOTH strings generalized and V-06 demands both pasted. Recorded as F-11. |
| PR-007 | low | IN-SCOPE | E. Testing | `integration_action_for_item` returns `INTEGRATION_ACTION_REVIEW` when `str(item.get("action") or "") == "review"`, with no reference to artifact type | E-04's integration sentence ("must treat a spec lane exactly as a plan review lane") reads as work to be done, and it is already true BY CONSTRUCTION: the predicate keys on `item["action"]`, not on the artifact type, so a spec review lane already takes the no-revalidation arm. Left as authored, an executor might edit a correct shared predicate to "make" a spec take a path it already takes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 states the verification result and instructs confirming it BY TEST rather than editing it; V-06 demands the predicate's answer for a spec entry. |
| PR-008 | low | IN-SCOPE | E. Testing | root `conftest.py` autouse home-isolation fixture | E-05's instruction to isolate `AW_HOME` per test is redundant: the repository's root `conftest.py` already re-points `AW_HOME` at a session sandbox around EVERY test via an autouse fixture. Harmless, but a second mechanism invites drift, and the identical finding was raised and fixed on this Set's Order 01 plan (`7icz68` PR-012), so repeating it here would leave the Set internally inconsistent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 records that `AW_HOME` needs no per-test handling and names the existing fixture, instructing the executor not to add a second mechanism. |
| PR-009 | low | UNDER-SCOPE | G. Right-sizing and conceptual density | rubric G diagnostics (a)/(b)/(c) on E-03 and E-05 as authored; `ipd_lint.check_density` after the split | E-03 bundled the disposition rung, the `--full-auto` bridge skip, and the approval-gate reporting question, which are three independent code regions with three independent test-surfaces, and the two latter each turned out to carry a defect of its own (PR-001, PR-002). E-05 bundled six test cases spanning four regions. Both answered YES to (a), (b) and (c). Splitting was not cosmetic here: folding the bridge crash into E-03 is precisely what let it read as a policy aside. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-03 (disposition), E-04 (bridge guard), E-05 (gate mechanism), E-06 (scoping), E-07 (dispatch/outcome tests), E-08 (crash-fix, gate and scope tests), E-09 (scratch run + suite). `Highest E allocated` raised to 9, V-* rebuilt to a 9-item bijection, dependency edges re-pointed; `check_density` reports no advisory. |
| PR-010 | low | IN-SCOPE | F. UX / G. Plan executability | the gate section as authored | THE GATE DESCRIBED THE HAPPY PATH ONLY. It stated the dispatch, the record gate and the approval stop accurately, and mentioned none of the three seams a human should know are being changed, one of which (the bridge) is a crash on the success path and one of which (the scoping) can lose the reviewed spec's own file. A human approving the authored gate would be approving the intent without being told what the implementation must repair. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now carries a paragraph naming all three seams with what each one does today, and states the behavioral dependency on `mxzogk` that makes E-04 necessary. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Is the `--full-auto` bridge crash this plan's to fix, or `mxzogk`'s regression to own? | Fix here, as a new E-04 | Defer to a corrective plan against `mxzogk`; treat it as already covered by scope (d) | `mxzogk` is correct: a plan resolver SHOULD refuse a spec, and that refusal is the whole point of its fail-closed change. The crash exists only because THIS plan routes a spec into a code path whose first statement is that resolver, so the guard belongs to the plan that creates the reachability. Remediation Risk is Low (one conditional, ahead of one call) and directly testable, so the Fix Bar does not permit deferral. | yes |
| D-2 | Guard the bridge with a type test, or widen its `try` to absorb the `DriverError`? | Type test placed BEFORE the resolve | Widen the `try`; catch and ignore `DriverError` around the resolve | Widening the `try` converts a crash into a SILENT skip and destroys the diagnostic for a genuine plan-path failure, which is a real class (`mxzogk`'s own concern lists three fail-open modes it turns into refusals). The type test says what is actually true: a spec has no approval bridge. It also keeps the bridge's behavior for plans byte-identical, which a broadened `except` would not. | yes |
| D-3 | Which mechanism should report a reviewed spec's approval gate? | Do not decide for the implementer: require a reader census and a RECORDED choice between a post-turn durable write and reporting from the disposition | Decide the durable write here; decide the disposition route here; leave the authored `item_needs_approval` claim in place | Both mechanisms are defensible and the deciding evidence is a census of who reads `NEEDS_INPUT_KEY` and whether each tolerates a post-turn write, which the implementer has in front of them and I do not without reading every reporting surface. What is NOT acceptable is the authored state, which asserts a mechanism that returns False by construction: that is a claim an executor would either propagate or quietly drop. Raised as OQ-02, non-blocking. | yes |
| D-4 | Fix the legacy-named-spec scope gap here, or rename the one offending spec? | Fix the scope rule: include the artifact's resolved path in the allowed set | Rename `4w7d6s` to carry its id6; accept the gap and document it | Renaming treats a supported shape as a defect: the repository explicitly grandfathers pre-cutover legacy spec names indefinitely, so a rule that only works for the new grammar will break again on the next grandfathered artifact and will do so by silently dropping a file. Including the resolved path is a strictly smaller assumption than "the filename contains the id6" and costs one lookup the item already performs. | yes |
| D-5 | Split the over-dense E-03 and E-05, or accept them because the count-based size lint passes? | Split into nine items with a 9-item V bijection | Accept; add a "Size assessment: exception" rationale | Rubric G's diagnostics answer YES on (a), (b) and (c) for both, and the workflow states a passing count-based size lint does not clear conceptual density. The split had substantive effect rather than cosmetic: the bridge crash and the approval-gate gap were each buried as a trailing clause of E-03, which is why both read as confirmations rather than as work. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is FIXED; none was DEFERRED or left OPEN, so no `- Blocking: yes` escalation under Step 4 is
owed either. OQ-02 is deliberately `Blocking: no`: the evidence needed to resolve it is in the
repository rather than with the human, and E-05 plus E-08 force the choice to be made and recorded.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> `conforming`, exit 0, 0 findings (before edits).
- `aw ipd lint --phase review-finalize --agent <plan>` -> `conforming`, exit 0, 0 findings (after
  edits), and `ipd_lint.check_density` called directly reports no advisory on any of the 9 E-items.
- F-1 re-read verbatim: `command = f"/plan-review {rel_path}"` in `build_review_prompt`.
- F-2 re-read verbatim, including that the resolve is `resolve_plan_path(source, ...)` with
  `source = plan_repo or repo`, which is what makes E-03's lane read available at all.
- F-3 re-read verbatim, and the surrounding block's structure inspected, which is what produced
  PR-001: the resolve is outside the `try`.
- F-4 reproduced END TO END on a scratch git repo: `aw specs set <spec> --status reviewed` exits 1
  with "to-review -> reviewed requires evidence that a review OCCURRED ... refused (file unchanged)"
  and `reason: no review record names aaaaaa as its `- Subject-Id:``; after writing a conforming
  record, `review_attestation_missing` returns `None` and the same command exits 0 and MOVES the file
  to `.aw/records/specs/reviewed/`.
- F-5 confirmed: both `.opencode/commands/spec-review.md` and `.claude/commands/spec-review.md` exist.
- The call order inside `execute_item_core` derived by AST-bounding the function and locating each
  collaborator, giving PR-004's ordering table.
- `review_findings.review_attestation_missing` and `subject_review_records` read to confirm the
  filesystem-read property (`open(path)` over `iter_review_files`/`review_dirs`).
- `item_needs_approval` called directly for the four (status, action) combinations that matter, and
  `NEEDS_INPUT_KEY`'s write sites counted, giving PR-002.
- `classify_review_writes` called on a synthetic spec lane; the corpus scanned for id-bearing specs
  whose filename lacks the id6 (1 of 19) and for spec review records in the same shape (0 of 12),
  giving PR-003.
- `integration_action_for_item` read, giving PR-007.
- `aw check reviews` -> `checked 384, errors 0, warnings 0`.
- `aw sanitize --agent` -> `outcome: clean, findings: 0`.
- `python3 -m pytest` (bare, as the execution contract requires), actual final line:

      2590 passed, 2 skipped, 3 warnings in 39.84s

  This is the unchanged baseline the plan's V-09 compares against; this review's edits touch only
  `.aw/records/` files. ONE HONEST NOTE FOR V-09: two turns earlier on this lane the same bare
  invocation reported `1 failed, 2549 passed, 2 skipped` at
  `tests/test_scope_match.py::ScopeMatchUnitTests::test_pathological_glob_avoids_exponential_time`,
  a wall-clock threshold (0.1191s against 0.1s) missed under load. It passes now and in isolation, so
  it is load-sensitive rather than broken; V-09's after-minus-before failing node-ID SET is the right
  instrument, since a node that flakes on one side must be re-run rather than reported as a
  regression.
