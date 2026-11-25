# Review findings: ipd feol8w

- Subject-Id: feol8w
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran non-interactively in an isolated review-sweep lane worktree (run `run-20261124T195117Z-1319864`, HEAD `fa3dd7bda`). The target plan `.aw/records/plans/pending/20261121-b0en28-01-feol8w-preserve-completed-review-phase-across-full-auto-approval-an.ipd.md` was committed and unmodified, so no pre-review snapshot commit was made. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0) with two `IPD-C802` info advisories (em dashes in the runtime-demonstration reachability rule sentence). After edits, the same lint returned `clean` with zero findings.

The review read backlog item `b0en28` (graduated, `Blocks-Release: next`), the full-auto bridge in `runner_shared.execute_item_core`, `runner_shared._check_queue_item_run_state`, `runner_shared.item_needs_approval`, `render_stream.render_run_summary_table`, `artifact_audit.allowed_lifecycle_pairs` and `artifact_audit.audit_artifact`, `run_viewer.load_run_summary` and `run_viewer.audit_step_artifact`, and spec `uonrjg` Sections 0 and 7.2. Four in-memory probes (scratch scripts under `/tmp/opencode/feol8w/`, no repository writes) reproduced all three defects on the current tree and measured the simpler fix:

- `save_state` through `queued` -> `running` -> `reviewed` -> (`execute`, `queued`, `auto_approved=True`) recorded `skipped-unmapped` with `unmapped_side: source` (F-03 confirmed).
- `render_run_summary_table` printed `Outcome: QUEUED`, `Progress: 0/1 ... (1 queued)`, and `Total (0/1 items run)` (F-01 confirmed). With `exit_reason="STOPPED (Level 1: after-call)"` the banner printed `Outcome: STOPPED (Level 1: after-call)`.
- `audit_artifact(status="queued", action="execute", initial_status="to-review")` on a `pending/` plan declaring `auto-approved` returned `status_mismatch=True`, `difference_class=unknown` (F-02 confirmed). The same call on a plan declaring human `approved` returned `unchanged`.
- With `("auto-approved", "pending")` appended to the pairs, the audit returned `status_mismatch=False`, `difference_class=unchanged`, `expected_status=auto-approved` for run statuses `queued`, `interrupted`, and `failed`, with `initial_status` `to-review` and `None`.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Step T

1. No: no spec, CLI option, file format, or configuration key changes; `run_state_check` gains one outcome value (`phase-advance`) recorded in `state.json`, and the summary table gains a display label.
2. No: none of the listed guard modules are touched; the plan edits runner state checking, summary rendering, and artifact audit.
3. Yes, moderately: 5 E-items across three runtime modules (`runner_shared.py`, `render_stream.py`, `artifact_audit.py`) and four test files.
4. Yes: `- Scope-Paths:` lists every file; after revision it drops `agent_workflows/run_viewer.py`.
5. Medium: a wrong `allowed_lifecycle_pairs` edit could hide a real status disagreement in `aw runs`, and a wrong `completed_count` edit misreports run progress.

Tier: standard.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | Scope-Paths included `agent_workflows/run_viewer.py` | `run_viewer.py` removed | PR-001 |
| Goal | One long sentence; promised new metadata | Names the three outcomes; states that only existing fields are read | PR-001, clarity |
| E-01 | Run-on expected outcome | Cases (a) to (d) listed; records the `aw check all` baseline | PR-006, clarity |
| E-02 | Rewrote `initial_status`, added `review_initial_status` and `review_completed`, edited `execute_item_core` | Only `_check_queue_item_run_state` changes, keyed on existing `auto_approved` | PR-001 |
| E-03 | Required an outcome-banner change; vague `items_data` handling; `action == "execute"` only | No banner change (existing chain yields `PARTIAL`); explicit display fields beside raw values; any non-review action | PR-003, PR-004, PR-008 |
| E-04 | New `audit_artifact(auto_approved=)` parameter and `run_viewer` threading | Pair-tuple change only; misnamed branch descriptions corrected | PR-001, PR-002 |
| E-05 | Unconditional `aw ipd finalize` before the commit; demanded `aw check all` exit 0 | Gates plus baseline comparison; finalize moved to the gate section | PR-005, PR-006 |
| Project conventions | No note on `initial_status` | Adds the frozen-`initial_status` contract and the measured `approved` tolerance | PR-001 |
| Findings, diagrams, Ordered Changes, Deferred, Scope check, Open questions | Described the threaded-flag design | Match the revised design; rejected alternative recorded with `Carrier-Declined` | PR-001 |
| Spec sync | Did not cite `uonrjg` | Cites `uonrjg` Sections 0 and 7.2 | PR-009 |
| V-02 | "end-to-end `--full-auto --after-call` coverage" with no code path | Names the in-process `oc_runipd.execute_item` drive with patched `run_opencode` | PR-007 |
| V-04 | Demanded `auto_approved` threading evidence | Demands the pair matrix and the `executed` negative case | PR-001 |
| V-05 | "worktree is clean" | The commit changes only Scope-Paths | PR-006 |
| Validation rule sentence | Two em dashes | Rewritten with "such as" and commas | `IPD-C802` |

#### Issues

- None remaining. Lint reports zero findings after revision.

### Step R1

- Checked: every cited symbol exists at HEAD: `execute_item_core`, `_check_queue_item_run_state`, `map_driver_status_to_run_state`, `INTENTIONALLY_UNMAPPED_DRIVER_STATUSES`, `item_needs_approval`, `render_run_summary_table`, `resolve_item_lifecycle`, `item_is_dispatchable_work`, `canonical_terminal_status`, `allowed_lifecycle_pairs`, `audit_artifact`, `load_run_summary`, `audit_step_artifact`, `step_issue_reasons`. All ten named test files exist, as do `tests/test_oc_runipd.py::AllSelectorAndFullAutoTests::test_full_auto_reviews_approves_and_executes_plan`, `tests/test_run_viewer.py::test_dead_run_queued_and_running_steps_projected_and_flagged_as_issues`, and `tests/test_rereview_reviewed_plan.py::TestRereviewExecutionTurn`.
- Ordered Changes 3 described the three pre-terminal tuples in `allowed_lifecycle_pairs` as "queued/running, reviewed, blocked/interrupted". The function actually branches on `initial_status`, an explicit-type fallback, and a legacy untyped branch (PR-002).

### Step R2

- Checked: E/V bijection 5/5; `Highest E allocated: 05` unchanged; dependency order E-01 -> E-02/E-03/E-04 -> E-05 is acyclic. `From-Backlog: b0en28` and `Blocks-Release: next` match the backlog item. `Item-Dependencies: none` is correct for Order 1 of a one-plan Set.
- E-03's banner step was redundant: the outcome chain already returns `PARTIAL` once `completed_count > 0` and no earlier class applies (PR-003). Its `items_data` handling was unspecified (PR-004).
- E-05 ran `aw ipd finalize` unconditionally and before the work commit, with no `aw ipd begin` receipt (PR-005). It demanded `aw check all` exit 0, but the tree already reports 12 error-severity findings unrelated to this plan (measured `aw check all --agent`, exit 1) (PR-006).
- V-02 demanded runtime `--after-call` coverage without naming a reachable code path (PR-007).

### Step R3

- Checked: no new subprocess, filesystem path, network, or untrusted-input surface. The audit change widens the accepted on-disk status set by one machine-written status that is the automated form of `approved`, which the same branches already accept unconditionally; the success branches stay strict, so a plan left in `pending/` after a run claims `executed` is still flagged. No security finding.

### Step R4

- Checked (KISS): the original design rewrote the frozen `initial_status`, added two queue-item fields, and threaded an `auto_approved` flag through `audit_artifact` and `run_viewer.StepSummary`. `item_needs_approval` and the `SKIP_NOT_RUNNABLE` text in `run_selection_policy.py` both describe `initial_status` as frozen at queue build, and the probe showed one tuple edit fixes the audit for historical and new runs alike (PR-001).
- Checked (compatibility): readers of `initial_status` in `render_stream.py`, `runner_shared.py`, and `run_viewer.py` keep their current inputs, because the value is no longer rewritten. `is_review_completed_queued_execute` reads only `auto_approved` and the attempt list, which historical `state.json` files already carry. Pending plan `behm9r` changes the bridge to write `action_for(kind, "auto-approved")`, so the helper now accepts any non-review action (`orchestrate` included).
- Checked (performance): `tests/test_run_summary_table.py` is core-tier; the new tests build state in memory.

### Step S5

- Checked: no question needs a human. The design choice (pair tuple versus threaded flag) is resolved from repository evidence and recorded as D-1. OQ-01 and OQ-02 stay resolved and were amended to match.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | KISS / compatibility | `runner_shared.item_needs_approval` docstring and `run_selection_policy.py` `SKIP_NOT_RUNNABLE` text (frozen `initial_status`); probe: `audit_artifact` with `("auto-approved", "pending")` added returns `unchanged` for `initial_status` `to-review` and `None` | Rewriting `initial_status`, adding `review_initial_status`/`review_completed`, and threading `auto_approved` through `audit_artifact` and `run_viewer` breaks a documented invariant and is unnecessary. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 edits only `_check_queue_item_run_state`; E-04 is a pair-tuple change; `run_viewer.py` leaves Scope-Paths; alternative recorded as `Carrier-Declined`. |
| PR-002 | LOW | IN-SCOPE | R1 references | `artifact_audit.allowed_lifecycle_pairs` branch structure | The three pre-terminal tuples were misdescribed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and Ordered Changes 3 name the `initial_status` branch, the explicit-type fallback, and the legacy untyped branch. |
| PR-003 | LOW | IN-SCOPE | G executability | `render_run_summary_table` outcome chain; `RUN_OUTCOME_CLASS_BY_STATUS.get("queued")` is `None`; probe with `exit_reason` set | The banner edit was redundant: `PARTIAL` follows from `completed_count > 0`, and an `--after-call` stop prints `exit_reason`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states no banner change and V-03 asserts `PARTIAL` with `exit_reason` unset. |
| PR-004 | LOW | IN-SCOPE | G executability | `render_run_summary_table` `items_data` rows and the status-cell `resolve_item_lifecycle(st_val, action=it["action"], ...)` call | The plan did not say how display strings reach the row while raw values reach the resolver. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and Ordered Changes 2 add display fields beside the raw ones. |
| PR-005 | MEDIUM | IN-SCOPE | Lifecycle | E-05 text; `ipd-lifecycle` workflow; runner-owned finalize | `aw ipd finalize` was an unconditional checklist step ordered before the work commit, with no `aw ipd begin`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Finalize moved to the gate's LIFECYCLE clause: runner-owned under `aw oc run`/`aw agy run`; `begin` then `finalize` after the commit otherwise. |
| PR-006 | LOW | IN-SCOPE | V reachability | `aw check all --agent` at HEAD: exit 1, 12 errors unrelated to this plan; shared checkout | "`aw check all` exits 0" and "worktree is clean" were unreachable demands. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records a baseline; E-05/V-05 demand no new `(rule, location)` pair and a commit limited to Scope-Paths. |
| PR-007 | LOW | IN-SCOPE | V reachability | `tests/test_rereview_reviewed_plan.py::TestRereviewExecutionTurn` (patches `oc_runipd.run_opencode`, `isolate_worktree: False`) | V-02's end-to-end demand named no code path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 names the in-process `oc_runipd.execute_item` drive and the viewer functions it checks. |
| PR-008 | LOW | IN-SCOPE | Cross-plan compatibility | Pending plan `behm9r` (bridge writes `action_for(kind, "auto-approved")`) | A helper keyed on `action == "execute"` misses an auto-approved orchestrator. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The helper accepts any non-review action; V-03 covers `orchestrate`. |
| PR-009 | LOW | IN-SCOPE | Spec sync | Spec `uonrjg` Section 0 ("the word is authoritative") and Section 7.2 | The compound label was not checked against the native-word rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec sync cites `uonrjg`; the cell keeps the native word `queued` and the resolver gets the raw value, so no amendment is needed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How does `aw runs` accept an `auto-approved` plan? | Add `auto-approved` to the pre-terminal pairs in `allowed_lifecycle_pairs` | Rewrite `initial_status` (rejected: breaks the frozen contract); thread `auto_approved` through `audit_artifact` and `run_viewer` (rejected: more surface, same result) | Probe results; PR-001 | yes |
| D-2 | Which signal marks the phase advance? | Existing `auto_approved` plus the last attempt being a completed review | New `review_completed` field (rejected: historical runs lack it) | Backlog `b0en28` requires historical-run coverage | yes |
| D-3 | Review tier | standard | simple, deep | Step T answers 3 and 5 | yes |

### Plans reviewed and not reviewed

- ELIGIBLE: feol8w (reviewed; APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED)
- NOT REVIEWED: (none)
