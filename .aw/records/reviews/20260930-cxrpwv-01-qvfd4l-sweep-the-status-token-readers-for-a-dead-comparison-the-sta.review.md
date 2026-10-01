# Review findings: plan qvfd4l

- Subject-Id: qvfd4l
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (BLOCKER, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
`--phase review-finalize` reports `clean` with zero findings after revision. The plan is `- Kind: child`,
so the `IPD-S407` orchestrator child-row check does not apply.

THE PLAN'S EVIDENCE IS UNUSUALLY GOOD AND I RE-RAN ALL OF IT RATHER THAN TRUSTING IT. Every one of
F-01 through F-11 reproduces, several to the exact rendered string:

- F-01 reproduces to the number. An independent AST walk over `agent_workflows/*.py` returned 258
  code-literal legacy-token hits in 34 modules, with the same four leading per-file counts
  (`runner_shared.py` 73, `attention.py` 38, `render_stream.py` 29, `lifecycle_style.py` 15), and the
  same 15 band-B equality sites by file and token. My band-A partition returned 63 rather than the
  plan's 76, an immaterial partitioning difference.
- F-02 reproduces. `5o1jye` is in `executed/`, the diagnostics arm reads
  `elif st in ("fail-depend", "dependency-blocked")`, and the report gate reads
  `canonical_terminal_status(item.get("status")) == "fail-depend"`.
- F-03 reproduces EXACTLY, including the rendered fraction. The same three-entry queue renders
  `Progress: 2/3 [██████▋   ]  67% (2 not-run, 1 queued)` / `Total (2/3 items run)` under `not-run` and
  `Progress: 0/3 [          ]   0%` / `Total (0/3 items run)` under `not-attempted`.
- F-04 reproduces END TO END THROUGH THE REAL CLI against a synthesized three-run repo. `aw runs`
  lists all three and prints `1 fail-verify` for BOTH the raw-`fail-verify` and the raw-`partial` run;
  `aw runs --failed` lists ONLY the `partial` run, hiding the genuinely failed one; `aw runs --status
  fail-verify` lists only the raw match, and `--status partial` lists the run the table prints as
  `fail-verify`. The filter and the column contradict each other in both directions.
- F-05 reproduces, and the measurement is WIDER than the plan claimed: `fail-begin` and `fail-lane`
  return `unknown` as stated, and so do `dependency-blocked` and `merge-needs-human`, whose canonical
  twins `fail-depend`/`fail-merge` both return `failed`. Four tokens, not two. The plan's E-04 and V-04
  were widened accordingly.
- F-06 reproduces. Each of the five named families carries its stated comment, and
  `no_turn_was_attempted` is live for the legacy spellings.
- F-07 reproduces. All 15 band-B sites belong to a non-runner vocabulary (`backlog.py` gate states
  paired with `Gate-Kind`/`Gate-Ref`, `status_set.py`'s backlog gate validator, `cli.py`'s attention
  class, `verify_roles`' verdict, `runner_shared`'s verify-disposition guard). Canonicalizing any of
  them would be a defect, as the plan says.
- F-10 reproduces. `grep` for `failed_only`, `--failed`, `args.failed` across `tests/` returns zero
  hits, and `tests/test_run_dashboard.py` asserts `outcome` exactly twice.
- F-11's gate arithmetic is correct: release `f33nrj` is the single `planned` record at version 2.0.0,
  and the backlog item carries no `- Blocks-Release:`, so the gate rests on this plan's own `bug`
  classification.

THE TWO BLOCKERS ARE BOTH IN THE PLAN'S OWN INSTRUCTIONS, and both would have cost an executor a
wasted pass. They are the reason this review is not a rubber stamp on an otherwise strong plan.

FIRST, E-02 instructed an import that cannot exist. It said to compare
`runner_shared.canonical_terminal_status(status)` inside `render_stream`, but `runner_shared` imports
`render_stream` at ITS module level, so the reverse edge closes a cycle. Measured by inserting exactly
that import: `python3 -c "import agent_workflows.render_stream"` exits 1 with
`ImportError: cannot import name 'GATE_ANSWER_NEEDS_HUMAN_CODE' from partially initialized module`.
The module's own docstring states the rule and allowlists exactly `term` and `lifecycle_style`. I then
measured the function-local form and confirmed it both imports and fixes the defect (`0/3` for both
spellings). E-02 now mandates the local placement, explains why, and notes it is `render_stream`'s
first function-local import (AST-measured 0 at HEAD).

SECOND, E-04 and V-04 were mutually unsatisfiable, and the failure mode was SILENT DATA LOSS on a
shipped column. E-04 said to canonicalize before the `_FAIL` membership tests AND to keep
`substantially-complete`/`partial` reading `partial`. But `canonical_terminal_status("partial")` is
`fail-verify` and `canonical_terminal_status("substantially-complete")` is `fail-gate`, both already
`_FAIL` members, so canonicalize-first returns `partial -> failed` and
`substantially-complete -> failed`, deleting the `partial` verdict. Measured by running `_outcome`'s
own body with a leading canonicalization. V-04 then demanded both "partial still reads partial" and
"no pair disagrees with itself", which the alias table makes impossible at this surface. I measured
two candidate orderings and E-04 now mandates the raw-partial-arm-first one, which reconciles every
pair except the two the lossy alias table cannot reconcile; those two are now named, explained, and
asserted as asymmetric-by-design in E-05 rather than silently skipped. OQ-03 records the decision.

THE MOST CONSEQUENTIAL FINDING IS PR-006, A FOURTH LIVE DEFECT THE SWEEP MISSED, and it is in the same
function as F-03 and two `elif` arms below the one `5o1jye` fixed. The diagnostics block's
`driver_error` arm and its `integration_deferral` arm are both legacy-only tuples with no canonical
member. Measured by direct render: `{"status": "failed-safely", "driver_error": "boom"}` renders
`• aaaaaa: failed-safely (boom)` while `{"status": "fail-gate", "driver_error": "boom"}` renders NO
`Diagnostics / Blocked Items:` SECTION AT ALL; the same holds for `merge-refused` versus `fail-merge`
with `integration_deferral`. I then proved the combination is LIVE rather than an unreachable branch:
`decide_integration_deferral(..., policy=ON_INTEGRATION_BLOCKED_BLOCK)` returns `status='fail-merge'`,
the ladder write site sets `item['integration_deferral']`, and it calls `record_refusal` ONLY when
`cause == INTEGRATION_CAUSE_GIT_CONFLICT`, so a non-conflict terminal refusal under
`--on-integration-blocked=block` yields exactly `fail-merge` + `integration_deferral` + no `Refusal`,
which measured silent. I also confirmed the `Refusal` record DOES rescue the conflict path, so the hole
is precisely the no-refusal arms, and `runner_shared` writes `status="failed-safely"` with
`driver_error` at the missing-dispatcher refusal while both hosts write `driver_error` on `DriverError`.
This is the backlog item's own defect class repeated, so excluding it would have left the item's
commission unfinished. Added as E-06/V-06 with its own characterization requirement.

TWO OWNERSHIP CLAIMS HAD GONE STALE IN THE DAY SINCE AUTHORING, which matters because the plan deferred
work to them. `35mjqc` is no longer pending: it has EXECUTED (it is in `executed/`, `- Status: executed`)
and shipped `render_stream.progress_display_total`, so what was deconfliction is now a REGRESSION FENCE,
and the deferral's "nothing is owed because `35mjqc` carries it" is now "nothing is owed because the work
is done". `r61br4` has advanced from `reviewed` to `approved`, which strengthens rather than weakens its
exclusion. Both corrected in F-08 and in the deferral list, and `tests/test_zero_dispatch_progress_denominator.py`
added to the validation list as the fence E-02 must not break.

WHAT I DELIBERATELY DID NOT FLAG, stated so a later reader does not re-raise it. The `9jkek2` overlap on
`run_viewer`'s filter loop is real and the two plans ARE complementary: `9jkek2` E-01 explicitly requires
"DO NOT change which runs any filter selects", while this plan's E-03 changes exactly that, so they edit
the same loop for orthogonal purposes and neither subsumes the other. Whichever lands second will need to
carry the other's intent, which the runner's merge-and-revalidate gate surfaces; that is a sequencing fact,
not a plan defect. I also did not flag the plan's `Carrier-Declined` entries: each states a measured reason
why no future work is owed, and for the two "would introduce defects" cases that is the correct disposition.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | G (executability) / C (architecture) | `agent_workflows/render_stream.py` module docstring + `agent_workflows/runner_shared.py:168` `from agent_workflows.render_stream import (...)` | E-02 instructed an import that RAISES. It directed `runner_shared.canonical_terminal_status(...)` inside `render_stream`, but `runner_shared` imports `render_stream` at module level, so a module-level reverse import closes a cycle. Measured: inserting it makes `python3 -c "import agent_workflows.render_stream"` exit 1 with `ImportError: cannot import name 'GATE_ANSWER_NEEDS_HUMAN_CODE' from partially initialized module`. An executor following E-02 literally breaks every entry point, not just this feature. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now MANDATES a function-local import inside `render_run_summary_table`, cites the measured ImportError, notes the module docstring's two-import allowlist, and records that this is `render_stream`'s first function-local import (AST-measured 0 at HEAD). Verified the local form fixes the defect: `Progress: 0/3` for both spellings. The gate repeats the constraint and the validation list adds two one-line `python3 -c "import ..."` checks. |
| PR-002 | BLOCKER | IN-SCOPE | A (correctness) / D (anti-regression) | `agent_workflows/run_dashboard.py:451-482` `_SUCCESS`/`_FAIL`/`_outcome`; `agent_workflows/runner_shared.py:29172` `TERMINAL_STATUS_ALIASES` | E-04 and V-04 were MUTUALLY UNSATISFIABLE, and obeying E-04 literally silently deletes a shipped verdict. E-04 said canonicalize before the membership tests AND keep `substantially-complete`/`partial` reading `partial`; but `cts("partial")=="fail-verify"` and `cts("substantially-complete")=="fail-gate"` are both `_FAIL` members, so canonicalize-first yields `partial -> failed` and `substantially-complete -> failed` (measured by running `_outcome`'s body with a leading canonicalization). V-04 then demanded both that `partial` still read `partial` and that no alias pair disagree with itself, which cannot both hold. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now mandates an explicit ORDER: the raw `("substantially-complete","partial")` arm is evaluated FIRST and only the remainder is canonicalized. Both candidate orderings were measured; the chosen one reconciles every alias pair except the two the lossy table cannot. E-04 records why canonicalize-first is refused with the measurement, and names the surviving asymmetry as deliberate. New OQ-03 records the decision and the rejected alternative. |
| PR-003 | HIGH | IN-SCOPE | E (testing) / D | V-04 as authored, against the measured `_outcome` behavior | V-04 demanded contradictory evidence (see PR-002) and ALSO under-specified the pair check, asking for "e.g. `partial` vs `fail-verify`" from a hand-copied list rather than from the alias table. A hand-copied list cannot notice a new alias, which is the exact failure mode the plan exists to fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now requires ITERATING `TERMINAL_STATUS_ALIASES` rather than hand-copying, demands the four newly-`failed` tokens, and states the pass/fail bar precisely: exactly TWO pairs may disagree, named, and a run where a third disagrees OR where either of those two agrees by having lost its `partial` verdict FAILS the item. |
| PR-004 | HIGH | IN-SCOPE | G / D | `.aw/records/plans/executed/20260929-5hf2qy-01-35mjqc-...ipd.md` `- Status: executed`; `render_stream.progress_display_total` docstring | F-08b and a deferral entry claimed `35mjqc` was a PENDING plan owning the zero-dispatch collapse. It has EXECUTED. So the plan deferred work to a plan that already landed, and the live obligation is the opposite of what was written: not deconfliction with pending work, but NOT REGRESSING a shipped fix. Left uncorrected, an executor could reasonably treat `progress_display_total` as still-in-flight and edit around or into it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-08b rewritten to record the execution with its path and status, to name `progress_display_total` as the landed fix, and to restate the consequence as a REGRESSION FENCE. The deferral entry now reads "nothing is owed because the work is DONE, not pending". `tests/test_zero_dispatch_progress_denominator.py` added to the validation list as the guard E-02 must not break. E-02's own wording updated from "owned by pending plan" to "landed with". |
| PR-005 | MEDIUM | IN-SCOPE | G | `.aw/records/plans/pending/20260929-qbfor9-01-r61br4-...ipd.md` `- Status: approved` | F-08a and its deferral recorded `r61br4` as `- Status: reviewed`; it is now `approved` and therefore RUNNABLE. A stale status on a plan you are deferring work to is a claim a reviewer must check, and here the drift happens to strengthen the exclusion rather than weaken it, which is worth stating rather than leaving as a silent discrepancy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08a and the deferral entry now record `approved`, note that authoring recorded `reviewed`, add the missing `tests/test_attention.py` to that plan's quoted fence, and state that runnability strengthens the exclusion. |
| PR-006 | MEDIUM | UNDER-SCOPE | A / F (prevent silent failure) / D | `agent_workflows/render_stream.py` `render_run_summary_table` diagnostics block, the `driver_error` and `integration_deferral` `elif` arms; `agent_workflows/runner_shared.py` ladder write site's `if cause == INTEGRATION_CAUSE_GIT_CONFLICT: record_refusal(...)` | A FOURTH LIVE DEFECT OF THE PLAN'S OWN CLASS, in the SAME function, two arms below the one `5o1jye` fixed, which the authoring sweep classified as correct-by-construction without probing it. Both arms are legacy-only tuples with no canonical member, so a canonical `fail-gate` carrying `driver_error` and a canonical `fail-merge` carrying `integration_deferral` render NO DIAGNOSTICS SECTION AT ALL where both legacy spellings render their reason. Measured by direct render for all four combinations. Proven LIVE, not unreachable: `decide_integration_deferral(..., policy=ON_INTEGRATION_BLOCKED_BLOCK)` returns `status='fail-merge'`, the write site sets `integration_deferral`, and `record_refusal` fires only for a git-conflict cause, so a non-conflict terminal refusal produces exactly the silent combination. Also confirmed a `Refusal` DOES rescue the conflict path, isolating the hole to the no-refusal arms. Excluding this would leave the backlog item's commission unfinished on the very surface it was filed about. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-12 with the full measurement, E-06 (extend both arms to the canonical tokens by comparing canonicalized forms, reusing E-02's local import, preserving arm order and every legacy rendering byte-for-byte) and V-06 (before/after diagnostics capture for all four items, a legacy-sweep regression paste, and an arm-precedence proof that a `Refusal` still wins). E-01 extended to characterize the two silent cases at HEAD first; Concern, Scope, Goal, Proposed changes, Scope check, F-10 and the `Highest E allocated` field all reconciled from three surfaces to four. |
| PR-007 | MEDIUM | IN-SCOPE | E | V-05 as authored ("temporarily restore ONE of the three legacy-only comparisons") | V-05's fence-bites proof required reverting ONE comparison. That proves one assertion is live and leaves the others unproven, which is precisely how F-10 records these defects surviving a green suite: a module that passes is not evidence that each of its assertions can fail. With a fourth surface added the gap widens. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now requires reverting each of the FOUR comparisons in turn, naming which assertion caught each, and states why one revert is insufficient. |
| PR-008 | LOW | IN-SCOPE | G (honesty about residual risk) | Plan `## Scope check` under-scope paragraph; F-01 as authored | The under-scope paragraph claimed the sweep decided "all but three sites are already correct", presenting the triage as complete when review found it had missed a live defect. The residual risk was stated only as a hypothetical (non-literal tokens, readers outside the package) when a CONCRETE instance existed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The under-scope paragraph now records the F-12 miss explicitly and draws the bounding lesson: the enumeration is mechanical and reproducible, the triage is the weaker half, and only PROBING distinguishes a deliberate compatibility set from a dead arm. F-01 now records the independent re-run (same 258/34, same 15 band-B sites) and states plainly that it verified the enumeration while finding the triage incomplete. |
| PR-009 | LOW | IN-SCOPE | A | `agent_workflows/run_dashboard.py:452-463` `_FAIL` | F-05 measured two missing `_FAIL` members; probing every alias pair found FOUR tokens reading `unknown` that should read `failed`: `fail-begin`, `fail-lane`, and also `dependency-blocked` and `merge-needs-human`, whose canonical twins are already members. An incomplete census leaves two dispositions misclassified after the fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now adds all four members and V-04's required table includes `dependency-blocked` and `merge-needs-human` with their expected `failed` verdicts. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-02's canonicalization needs `canonical_terminal_status` inside `render_stream`, which may not import `runner_shared` at module level. Mandate a function-local import, or duplicate the alias table into `render_stream`? | Mandate a FUNCTION-LOCAL import of `canonical_terminal_status`, introduced once and shared by E-02 and E-06. | (a) Module-level import: REJECTED, measured to raise `ImportError ... partially initialized module`. (b) Duplicate `TERMINAL_STATUS_ALIASES` or a local canonicalizer into `render_stream`: REJECTED, that is two vocabularies for one fact, the exact drift class this repository extracted shared predicates to prevent, and it would make the next rename silence this surface again, which is the defect under repair. (c) Move `canonical_terminal_status` into a leaf module both can import: REJECTED as out of scope, it touches a symbol 5 modules import and would need its own plan. | `agent_workflows/runner_shared.py:168` imports `render_stream` at module level; `render_stream`'s module docstring states the rule and allowlists exactly `term` + `lifecycle_style`; measured ImportError on insertion; measured correct fix with the local form. Precedent for the local form: `artifact_audit` already does `from agent_workflows.runner_shared import canonical_terminal_status` function-locally at 4 sites, and `run_dashboard._default_cache_path` imports `runner_shared` function-locally. | yes |
| D-2 | `_outcome`'s `partial` verdict and spelling-independence are irreconcilable because the alias table is lossy. Keep the verdict, or make the surface fully spelling-independent? | KEEP the `partial` verdict; order the raw partial arm first; name and TEST the two-pair asymmetry as deliberate. | (a) Canonicalize first (E-04 as authored): REJECTED, measured to return `partial -> failed` and `substantially-complete -> failed`, deleting a shipped `COLUMNS` verdict that no backlog item asks to remove. (b) Remove `partial` from `_outcome`'s collapse to achieve full independence: REJECTED, a behavior change losing information a reader uses, outside this plan's commission. (c) Make `canonical_terminal_status` non-total so `partial` has no canonical form: REJECTED, breaks every other reader relying on totality. | `runner_shared.py:29172-29183` `TERMINAL_STATUS_ALIASES` maps `partial -> fail-verify` and `substantially-complete -> fail-gate`; `run_dashboard.py:452-463` `_FAIL` contains both targets; `_outcome`'s body re-run with a leading canonicalization measured both collapses; two candidate orderings measured and compared pair-by-pair. Recorded in the plan as OQ-03. | yes |
| D-3 | PR-006 is a defect the plan's own sweep missed. Add it to this plan, or file it as a separate backlog item? | ADD it to this plan as E-06/V-06. | (a) File a separate backlog item: REJECTED. It is the SAME defect class, in the SAME function, under the SAME fence (`render_stream.py` is already declared), found by the SAME probe technique, and the backlog item `cxrpwv` explicitly commissions the class rather than an instance; splitting it would let the item graduate with its own commission unfinished and would need a second plan to touch a file this one already touches. (b) Leave it unrecorded: REJECTED outright, it is a measured live defect on an operator-facing surface. | Backlog `cxrpwv` text: the residual "is the CLASS, NOT THE INSTANCE" and a sweep should "pin the canonical spelling behaviorally"; the plan's `- Scope-Paths:` already contains `render_stream.py`; the defect sits in the same `elif` chain as the arm `5o1jye` fixed; measured live via `decide_integration_deferral` + the conditional `record_refusal`. | yes |
| D-4 | Does the `9jkek2` overlap on `run_viewer`'s filter loop need a finding? | NO finding; it is a sequencing fact the plan already records honestly in F-09. | Raise it as a conflict finding: REJECTED, the two changes are provably orthogonal rather than contending. `9jkek2` E-01 states "DO NOT change which runs any filter selects" and reports what the filters excluded; this plan's E-03 changes what they match. Neither subsumes the other and the plan's F-09 already says so and asks a reviewer to confirm it, which I did. | `9jkek2` E-01 read in full (`- Status: reviewed`, `- Readiness: go-pending-approval`, fence `run_viewer.py` + `tests/test_run_viewer.py`); this plan's F-09 read; `AGENTS.md` records that the runner isolates each item in its own worktree and merges through a revalidation gate, so a shared file is not a runtime hazard. | yes |
| D-5 | OQ-01 and OQ-02 were authored as `resolved` with `Owner: none`. Accept, or re-open? | ACCEPT both as resolved. | Re-open them for maintainer input: REJECTED, both are answered by repository evidence rather than by maintainer preference. OQ-01's answer is forced by the same function's display path already canonicalizing (so canonical-only matching would still fail to select the legacy record the canonical word was printed for, the exact contradiction F-04 measures). OQ-02's answer is forced by F-06's per-site comments plus spec `25kzda`'s legacy-readable amendment. | `run_viewer.py:1625` `status_word = canonical_terminal_status(step.status)` and three further display sites; F-06's five named collections read with their comments; `ipd_schema.open_question_error` permits `Owner: none` for a `resolved` question (only `deferred` requires an owner). | yes |
