# Review findings: plan aeq7f8

- Subject-Id: aeq7f8
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Re-verified at lane HEAD `7504fd60`. Every claim in the plan's own Findings table (F-1 through F-5)
was re-derived by grep or direct call and reproduced, with one count corrected (F-5: 12 approved
specs, not 13; the conclusion that none has a live linked plan is unchanged and was re-derived).

THE TWO HIGH FINDINGS ARE ONE ROOT CAUSE AND THE PLAN'S OWN DESIGN CONTRADICTS THE CODE IT CITES.
`execute_item_core` derives exactly one boolean, `is_review = action == "review"`, and eleven or more
gates key on it. A `plan` action is therefore an EXECUTE turn everywhere that matters: it runs the
test suite, it reaches the finalize block and calls `_call_driver_finalize` on a path resolved from
`configured_file` (the SPEC), it calls `process_backlog_close`, and it integrates through
merge-and-revalidate. The plan's OQ-02 resolves the opposite and justifies it by citing
`integration_action_for_item`'s rationale, but that function returns `execute` for a `plan` action,
measured. So the intended design is WORK, not a confirmation, and the authored instruction ("E-01
confirms this against the code at execution") pointed the executor at agreement that is not there.

This is a plan introducing a THIRD kind of turn into a dispatcher that has only ever known two, and
the authored checklist treated that as a parenthetical inside E-03 ("with the E-01-chosen
isolation"). The largest single change in the revision is promoting it to its own item with an
enumerated per-gate answer, and proving it by patching the execute-path collaborators to fail if
called rather than by asserting the arm exists.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | high | UNDER-SCOPE | A. Correctness / C. Architecture | `execute_item_core`: `is_review = action == "review"`, then `if self_finalize and not is_review` (clean base), `integration_gate_relevant = self_finalize and not is_review and ...` -> `run_suite_check`, `if not is_review and disposition in ("executed","fail-gate","substantially-complete")` -> `resolve_plan_path(finalize_repo, item["configured_file"], item["id6"])` -> `_call_driver_finalize`, `process_backlog_close`, `if not is_review: handle_turn_failure_retry`, the lane-preservation branch, and `integrate_lane_branch` | A `plan` ACTION FALLS THROUGH EVERY `not is_review` GATE AND WOULD `aw ipd finalize` THE SPEC. The dispatcher classifies turns by one boolean, so production silently takes the execute path: suite check, finalize against a `.spec.md`, backlog close, merge-and-revalidate integration, execute-path retry classification. The plan's E-03 mentioned isolation only, so nothing in the authored checklist would have produced a production arm, and the finalize call is the sharpest edge because it acts on the source artifact rather than on a produced plan. | C:Medium; U:Medium; S:Low; F:High; Overall:Medium | FIXED | New E-03 is a dedicated item requiring every `is_review` decision point to be enumerated with an explicit `plan` answer and reason, explicitly forbidding `is_review = action in ("review","plan")` (which would also inherit the review prompt builder, the review disposition rung and the `--full-auto` bridge), and naming the required answers (no suite check, no finalize, no backlog close, review-style integration). E-01 now builds that enumeration; E-09 proves it by patching each collaborator to fail the test if called. Recorded as the plan's own F-6. |
| PR-002 | high | IN-SCOPE | A. Correctness / G. Plan executability | `integration_action_for_item({"action":"plan"})` -> `execute`; `resolve_isolation` returns `{"execute": ..., "review": ...}` only; `isolation_for_action({"isolate_execute":True,"isolate_review":False,"isolate_worktree":True},"plan")` -> True by fallback; the call site `isolate = isolation_for_action(options, "review" if is_review else "execute")` | OQ-02's RESOLUTION IS FALSE AS WRITTEN and the plan treats the question as settled. It asserts the production turn's integration "is the REVIEW-style integration without suite revalidation" because `integration_action_for_item`'s rationale "applies"; that function keys on `action == "review"` and returns `INTEGRATION_ACTION_EXECUTE` for everything else, so the rationale does not apply by construction. Isolation has the same defect: no `isolate_plan` key is ever written, so a `plan` action silently falls back to `isolate_worktree`, and the call site asks for EXECUTE isolation regardless. An executor reading OQ-02 would look for agreement, fail to find it, and either fabricate it or ship the execute path. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | OQ-02 rewritten to separate the INTENT (which stands and is correct) from the false claim that the code already agrees, with both measurements; E-03 owns extending both helpers or recording a deliberate decision to share the review key; V-03 demands the post-change value of `integration_action_for_item({"action":"plan"})`. Recorded as F-7. |
| PR-003 | medium | UNDER-SCOPE | G. Plan executability / scope | `render_stream.render_run_summary_table` is the run summary, imported and called by both hosts at three sites each; `- Scope-Paths:` as authored omits `render_stream.py`; the Scope check says "if E-05 must edit it, declare it at finalize with `--scope-reason`" | THE RENDERER E-05 MUST EDIT IS UNDECLARED, AND THE PLAN'S SCOPE CHECK INVERTS THE CONTRACT. `write_report` is in `runner_shared` (declared), but the end-of-run RUN SUMMARY is `render_stream.render_run_summary_table`. A path known at authoring to be needed belongs in the declaration, because the runner announces declared scope BEFORE the run and reconciles it at finalize; deferring it to a `--scope-reason` converts a foreseeable edit into an after-the-fact justification. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `render_stream.py` added to `- Scope-Paths:`; the Under-scope bullet rewritten to state it is declared and to name the declared-but-unmodified fallback (`--scope-ack`) rather than the reverse. Recorded as F-8. |
| PR-004 | medium | IN-SCOPE | C. Architecture / E. Testing | `grep -n "generated_next_actions\|Generated next actions" agent_workflows/*.py` -> no hits; `write_report`'s docstring: `run_viewer.load_run_summary` "takes `cols[5].strip()` verbatim" and an executor changing that column "must keep it BARE" | THE DURABLE FIELD AND THE REPORT BLOCK ARE BOTH NEW WITH NO PRECEDENT, and the plan presents them as if following a convention. Nothing named `generated_next_actions` exists, so its shape, its resume behavior and its interaction with `run_viewer`/`aw runs show` are unspecified. The report table is parsed POSITIONALLY by `run_viewer.load_run_summary`, so a careless new column would break run parsing for every run, not only production runs. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into its own E-06, which states the field is new, requires the block on BOTH surfaces, and requires the existing report columns to stay byte-identical with `run_viewer.load_run_summary` still parsing the run; V-06 demands a before/after column diff. Recorded as F-9. |
| PR-005 | medium | IN-SCOPE | A. Correctness / F. UX | the preservation block: `if wt_handle is not None and not is_review and item.get("status") != "executed": lane_containment.record_lane_preserved(...)` | E-04's QUARANTINE PROMISE NAMES NO MECHANISM, AND THE MECHANISM THAT EXISTS IS GATED ON `not is_review`. "Produced files stay committed on the lane and are reported as quarantined-not-integrated (never merged to main) so a human can inspect them" is a claim, not an instruction. The shipped behavior is `record_lane_preserved`, and a `plan` action satisfies its guard TODAY only because PR-001's misclassification makes it an execute turn. Once the production arm lands, the preservation must be wired deliberately or a failed production discards its lane at teardown, losing exactly the files the gate tells a human to inspect. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-05 now names `record_lane_preserved`, states why the guard no longer covers production after E-03, and requires it wired and asserted; E-09 asserts a failed production leaves its lane recorded with its path; V-05 demands the record. Recorded as F-10. |
| PR-006 | low | IN-SCOPE | G. Plan executability | the `handle_turn_failure_retry` call site under `if not is_review:` and its comment "EXECUTE TURNS ONLY. A review turn's dispositions mean something different ... Widening this to reviews would spend the correction budget on a class another mechanism already re-attempts" | E-04 PHRASED A DESIGN DECISION AS A TABLE LOOKUP. It asks the executor to use the correction budget "only if its classification table admits it", but the helper is restricted to execute turns by a deliberate guard with a recorded reason, so whether production may spend the budget is a question about which class production belongs to. As written, an executor could read the classification table, find the disposition listed, and wire a retry the surrounding design excludes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 states it as a design decision to be recorded with its reason, and requires that if production does not get the budget the plan says plainly that CONFORMANCE fails on first violation and why that is acceptable. Recorded as F-11. |
| PR-007 | low | IN-SCOPE | F. UX | the refusal string, which states the review rule, and whose recovery is `{labels.review_command}`; plus the not-implemented branch "Only --action review is available" | E-05's INSTRUCTION TO "FIX ITS HARDCODED `--action review` WORDING TO NAME THE REQUESTED ACTION" UNDERSTATES THE CHANGE. Three parts of the message are review-specific: the illegality sentence asserting the rule for review, the closing recovery command, and the not-implemented branch above it. Naming the action alone would leave a `--action plan` refusal whose explanation and recovery are both about review. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 names all three parts and requires each to derive from the requested action; V-07 demands the refused output show an explanation and recovery about `plan`, plus an unchanged `--action review` refusal as a control. Recorded as F-12. |
| PR-008 | low | IN-SCOPE | Evidence accuracy | re-measured: 12 approved specs; the only spec with live linked plans is `z7nbn1` itself (6 live, status `implementing`) | F-5's spec count is 13 in the plan and 12 at this HEAD. The CONCLUSION (no approved spec has a live linked plan, so the duplicate clause starts clean) re-derived correctly and is the load-bearing part, but the number is a live population stated as a fact, and the duplicate clause is exactly where a stale baseline would matter. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 corrected with the re-measurement and the reason the conclusion survives; E-01's expected outcome already re-derives it. |
| PR-009 | low | UNDER-SCOPE | E. Testing | root `conftest.py` autouse home-isolation fixture | E-06's instruction to isolate `AW_HOME` per test is redundant: the root `conftest.py` already re-points it at a session sandbox around every test. The identical finding was raised and fixed on this Set's Order 01 and Order 04 plans, so leaving it here would make the Set internally inconsistent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 records that `AW_HOME` needs no per-test handling and names the existing fixture. |
| PR-010 | low | UNDER-SCOPE | G. Right-sizing and conceptual density | rubric G diagnostics (a)/(b)/(c) on E-03, E-04, E-05 and E-06 as authored; `aw ipd lint` `IPD-Z602` during the revision | E-04 bundled the verifier run, the retry policy, the quarantine claim, the setter call, the next-actions record and the item disposition; E-05 bundled the report block, `ACTION_IMPLEMENTED`, the refusal rewrite and a resume-path read; E-06 bundled seven test cases spanning the verifiers, the lifecycle and the report. All answered YES to (a), (b) and (c). Splitting had substantive effect rather than cosmetic: the production arm (PR-001) and the quarantine mechanism (PR-005) were each buried as a clause, which is how both came to read as confirmations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-01..E-11: E-03 (production arm), E-04 (the turn), E-05 (verify/transition/quarantine), E-06 (report), E-07 (`--action plan`), E-08 (outcome tests), E-09 (lifecycle-arm and report-only tests), E-10 (verifier units), E-11 (suite). `Highest E allocated` raised to 11, V-* rebuilt to an 11-item bijection; `aw ipd lint --phase review-finalize` reports 0 findings and `check_density` reports no advisory. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Is the missing production arm repairable inside this plan, or does it need a REPLAN or a separate Set member? | Repairable: promote it to its own E-item (E-03) inside this plan | REPLAN; split the arm into a new Order between 04 and 05; leave it as a clause of the production turn | The plan's SHAPE is sound and its verifier design is good; exactly one thing was mis-sized, and the fix is an enumeration over an existing function plus two helper extensions, all in already-declared paths. Remediation Risk is Medium (many gates, but each answer is local and testable). Splitting it into a separate Set member would create an item whose only consumer is this plan, and REPLAN would discard correct work on the three `SPEC-PLAN` verifiers. | yes |
| D-2 | Should `plan` reuse `is_review` (by widening it) or get a third classification? | A third classification, e.g. `is_production` | Widen `is_review = action in ("review","plan")`; add a `not_execute` boolean | Widening is the cheap route and it silently inherits four things production must NOT have: the review PROMPT builder, the review sweep-session sharing, the review DISPOSITION rung (which decides `reviewed` from an artifact status), and the `--full-auto` approval bridge. Each would be a separate defect discovered at runtime. A third classification forces each gate to be answered on its merits, which is what the review found missing. | yes |
| D-3 | Does production get the execute path's correction budget for a CONFORMANCE retry? | Do not decide for the implementer: require the decision recorded with its reason, and require the no-retry case to be stated plainly | Decide yes here; decide no here; leave E-04's table-lookup phrasing | `25kzda` 4.8 says `RETRY, then FAIL ITEM`, and the shipped helper is restricted to execute turns by a deliberate guard whose comment gives a reason that may or may not apply to production. Choosing needs the classification table in front of the implementer. What is not acceptable is the authored phrasing, which reads as a lookup and would let a retry be wired past a design boundary without anyone noticing. | yes |
| D-4 | Declare `render_stream.py` now, or justify it at finalize as the plan proposed? | Declare it now | Leave it to `--scope-reason` at finalize; route the summary edit through `runner_shared` to avoid the declaration | The runner ANNOUNCES declared scope before a run starts, so a foreseeable edit left undeclared defeats the announcement's purpose and turns reconciliation into paperwork. Routing around it to avoid a declaration would be tail-wagging: the summary renderer legitimately lives there. The declared-but-unmodified case costs one `--scope-ack`, which is the cheap direction. | yes |
| D-5 | Split the four over-dense items, or accept them because the count-based size lint passes? | Split into eleven items with an 11-item V bijection | Accept; add a "Size assessment: exception" rationale | Rubric G's diagnostics answer YES on (a), (b) and (c) for four items, and the workflow states a passing count-based size lint does not clear conceptual density. The split was load-bearing rather than tidy: the two HIGH findings and the quarantine gap were each a trailing clause of a larger item, which is precisely why they read as confirmations of existing behavior instead of as work. `IPD-Z602` fired during the revision and is now clear. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is FIXED; none was DEFERRED or left OPEN, so no `- Blocking: yes` escalation under Step 4 is
owed either.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> `conforming`, exit 0, 0 findings (before edits).
- `aw ipd lint --phase review-finalize --agent <plan>` -> `conforming`, exit 0, 0 findings (after
  edits). Two findings fired mid-revision and are cleared: `IPD-S401` (an `Execution state` line I
  dropped while renumbering, repaired) and `IPD-Z602` on E-07 (reworded). `ipd_lint.check_density`
  called directly reports no advisory on any of the 11 E-items.
- F-1 re-grepped: `ACTION_PLAN` appears only as its definition, its `ACTION_ORDER` membership, the two
  table rows, and one `runner_shared` docstring mention.
- F-2 re-read: `ACTION_IMPLEMENTED = frozenset(("review",))`, and `enforce_requested_action`'s
  not-implemented branch read verbatim (which produced PR-007).
- F-3 re-grepped: the three `SPEC-PLAN-*` codes and the five `BACKLOG-*` codes have zero hits in
  source files.
- F-4 re-measured by direct call, including `TRANSITION_AUTHORITY["->implemented"]`'s `evidence: True`,
  which is why this plan must never set it.
- F-5 re-measured over the corpus: 12 approved specs; live `From-Spec` plans exist only for `z7nbn1`
  (6, status `implementing`), so zero approved specs have a live linked plan. This gave PR-008.
- PR-001's gate set derived by AST-bounding `execute_item_core` and locating every `is_review` branch
  point, then reading each one.
- PR-002 measured by direct call: `integration_action_for_item({"action":"plan"})` -> `execute`;
  `isolation_for_action` with a policy disabling review isolation shows `plan` falling back rather
  than reading a policy; `resolve_isolation`'s return keys read as `execute`/`review` only.
- PR-004 measured by grep (`generated_next_actions` absent) and by reading `write_report`'s docstring
  on the positional column parse.
- PR-005 measured by reading the preservation block and its guard.
- The `close_backlog_item` precedent E-05 cites was read and confirms the gated `--status` spelling and
  why the positional form is unsafe.
- `aw check reviews` -> `checked 388, errors 0, warnings 0`.
- `aw sanitize --agent` -> `outcome: clean, findings: 0`.
- `python3 -m pytest` (bare, as the execution contract requires), actual final line:

      2598 passed, 2 skipped, 3 warnings in 42.35s

  This is the unchanged baseline the plan's V-11 compares against; this review's edits touch only
  `.aw/records/` files. ONE HONEST NOTE FOR V-11: three turns earlier on this lane the same bare
  invocation reported `1 failed, 2549 passed, 2 skipped` at
  `tests/test_scope_match.py::ScopeMatchUnitTests::test_pathological_glob_avoids_exponential_time`,
  a wall-clock threshold (0.1191s against 0.1s) missed under load. It has passed on every run since,
  including this one, and passes in isolation, so it is load-sensitive rather than broken. V-11's
  after-minus-before failing node-ID SET is the right instrument, since a node that flakes on one side
  must be re-run rather than reported as a regression.
