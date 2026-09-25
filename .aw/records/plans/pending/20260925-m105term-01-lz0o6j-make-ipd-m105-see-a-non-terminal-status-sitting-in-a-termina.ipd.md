# IPD: Make IPD-M105 see a non-terminal status sitting in a terminal plan directory

- Date: 2026-09-25
- Kind: child
- Concern: `ipd_lint.lint_text` returns `DISPOSITION_LEGACY` with no diagnostics for any plan in `executed/`, `superseded/` or `not-executed/` before `check_metadata` runs. So a plan in `executed/` whose own `- Status:` reads `to-review` gets no report from any surface: `IPD-M105`, `attention.disposition-mismatch` and `doctor.artifact-status-location-drift` all stay silent.
- Scope: `agent_workflows/ipd_lint.py` (`lint_text` terminal short-circuit), `agent_workflows/ipd_schema.py` (`_check_path_status` pre-terminal message routing to `IPD-M105`), and `agent_workflows/check_engine.py` (`check_ipd_lint_reach`, which only sweeps `pending/`), plus their tests. The rest of the terminal-tree grandfathering stays unchanged.
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, agent_workflows/check_engine.py, tests/test_ipd_lint.py, tests/test_ipd_schema.py, tests/test_check_engine.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: dbslfm
- Blocks-Release: next
- Set: m105term
- Order: 1
- Highest E allocated: 06
- Readiness: go-pending-approval
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: lz0o6j

## Workflow history

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701..PR-708 all FIXED, no open blocking question. The diagnosis was confirmed exactly, but three prescriptions were driven at review and found wrong. The blast radius is 25 of 727, NOT 0 of 723, and OQ-01's whole "no cutover needed" resolution rested on that zero (all 25 are pre-cutover legacy plans with prose/upper-case status lines that a NORMALIZING reader hides). E-02 and E-04 read status through DIFFERENT readers and would have shipped two surfaces disagreeing by exactly those 25 plans. E-04 was a measured NO-OP, because `_iter_type_files`' retired filter removes every terminal-tree plan before the guard it extends. Also found: `aw ipd lint --all` derives its exit code from the disposition and would start exiting 1. Record: `.aw/records/reviews/20260925-m105term-01-lz0o6j-make-ipd-m105-see-a-non-terminal-status-sitting-in-a-termina.review.md`.
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog dbslfm; re-measured that lint, attention and doctor are all silent on a to-review plan in executed/, and that 0 of 723 terminal-tree plans currently disagree with their directory.

## Goal

A plan AUTHORED AT OR AFTER THE CUTOVER, sitting in a terminal directory whose declared status names a different disposition, yields an `IPD-M105` error from `aw ipd lint`, and `aw check` reports the SAME set of files through the SAME status reader. The rest of the terminal tree, including the 25 pre-cutover legacy plans nobody may edit, keeps its `legacy/not evaluated` grandfathering, and `aw ipd lint --all` keeps exiting 0 on this repository.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the lint rule

- [ ] E-01 In `ipd_schema._check_path_status`, change the pre-terminal message from `"pre-terminal Status must live under pending/"` to one containing `directory`, for example `"pre-terminal Status must live under the pending/ directory"`. Today `ipd_lint.check_metadata` routes to `C_META_PATH` only when `me.field == "Status" and "directory" in me.message`, and the pre-terminal arm is the ONE arm whose text omits that word, so the case is reported as the generic `IPD-M104` (measured: with `legacy=True` in `executed/`, a `to-review` status yields `('IPD-M104', 'Status: pre-terminal Status must live under pending/')`). Update the pinned expectation in `tests/test_ipd_schema.py`, which asserts the exact message string; that assertion is what makes the routing condition load-bearing, so state the new string there rather than loosening the test.
  - Depends on: none
  - Expected outcome: `lint_text(<to-review text>, directory="reusable")` reports `IPD-M105`, not `IPD-M104`, for the Status field. This proves ROUTING ONLY: `reusable` is not a terminal directory, so `lint_text` never short-circuits there and this says nothing about the terminal-tree behavior, which V-02 owns.
  - Execution state: pending

- [ ] E-02 In `ipd_lint.lint_text`, before the `_is_terminal_dir(directory) and not legacy and checkpoint != "post-transition"` short-circuit, evaluate the path/status predicate and return `LintResult(S.DISPOSITION_ERROR, [Diagnostic(0, 0, C_META_PATH, ...)])` with ONLY that diagnostic when it errors; otherwise keep returning `DISPOSITION_LEGACY` with no diagnostics, so a plan whose status agrees with its directory keeps exactly today's result. Two constraints review measured and the original item got wrong (F-5, F-6, F-7).
  1. READ THE STATUS THROUGH `plans.read_status`, NOT through `doc.meta_fields["Status"]`. The raw field is unnormalized: `ipd_lint.parse(...).meta_fields["Status"]` on executed plan `vfa1tl` returns `'EXECUTED'`, which is not in `S.TERMINAL`, falls into the pre-terminal arm and errors, while `plans.read_status` applies `normalize_status` and returns `'executed'`, which agrees with the directory. Measured: the raw reader flags 25 terminal-tree plans and the normalized reader flags 0. E-04 must use the SAME reader, because two surfaces reporting different sets for one rule is the defect `check_engine.check_ipd_lint_reach`'s own docstring exists to prevent (it records a measured zero-versus-one `check.id6-collision` disagreement between `aw check` and `aw doctor`). `ipd_schema` has no `normalize_status`; do not add one, use the shipped `plans.read_status`.
  2. GATE IT ON A DATE CUTOVER. Add an `M105_TERMINAL_CUTOVER_DATE` compact `YYYYMMDD` constant read off the plan's own `- Date:`, modelled on the shipped `ipd_lint.CITATION_ANCHOR_CUTOVER_DATE` (copy its re-measurement convention comment and its strictly-greater-than test shape). A plan with no parseable `- Date:` is treated as PRE-cutover and suppressed, the direction that constant's own `_citation_anchor_applies` takes and for its stated reason (`IPD-M101` already owns the missing-`Date` complaint). Pick a date strictly after 2026-07-11, the newest affected plan; re-derive the newest affected date at execution rather than copying that number. WHY: the 25 affected plans are dated 2026-06-30..2026-07-11 and CANNOT BE FIXED, because `AGENTS.md` forbids adding commits to a plan in `executed/` and the `ipd-executed-transition-gate` pre-commit hook enforces it. The cutover is also what keeps `aw ipd lint --all` at exit 0 (F-7).
  Add a comment citing this plan and the CORRECTED measurement (25 of 727 raw, 0 normalized), not the withdrawn "0 of 723".
  - Depends on: E-01
  - Expected outcome: a POST-cutover plan declaring `to-review` or `superseded` in `executed/` reports an `error` disposition with `IPD-M105`; `executed` in `executed/` still reports `legacy/not evaluated`; every one of the 25 PRE-cutover legacy plans still reports `legacy/not evaluated`. The same holds under an `executed/202608/` shard, because `_dir_of` resolves the anchor.
  - Execution state: pending

- [ ] E-03 Add tests in `tests/test_ipd_lint.py` covering E-02 via both `lint_text` and `lint_file` (a real file under `.aw/records/plans/executed/` and `executed/202608/` in a temp repo). Cover the three terminal directories crossed with pre-terminal, other-terminal and matching statuses; a status-less terminal file, which stays `legacy`; a PRE-cutover-dated file, which stays `legacy`; and an upper-case `- Status: EXECUTED` in `executed/`, which must stay `legacy` because the normalized reader agrees with the directory (the E-02.1 regression). Also assert the cutover constant is strictly greater than the newest affected plan date, mirroring the `CITATION_ANCHOR_CUTOVER_DATE` test.
  - Depends on: E-02
  - Expected outcome: the new tests pass with the fix and fail on the unfixed `ipd_lint.py`.
  - Execution state: pending

### Task group 2: reachability from aw check

- [ ] E-04 In `check_engine.check_ipd_lint_reach`, reach the terminal tree with the CHEAP predicate only (`plans.read_status` plus `ipd_schema._check_path_status` on the `_dir_of` anchor), keeping the FULL `lint_file` scoped to `pending/` exactly as today, which preserves the docstring's cost argument against 626+ reads and parses. Emit the existing `check.ipd-lint-diagnostic` rule with `IPD-M105` in the detail, so no new rule id is registered. Three things the original item got wrong or omitted (F-6, F-7, F-9).
  1. THE LOOP MUST PASS `include_retired=True`, or the item is a NO-OP. `check_ipd_lint_reach` calls `_iter_type_files(repo_root, "plans", include_untracked=include_untracked)` with no `include_retired`, and `_iter_type_files` skips any path where `is_retired(p, record_type)` is true; `_RETIRED_PATH_SEGMENTS` contains `executed`, `superseded` and `not-executed`. So every terminal-tree plan is filtered out BEFORE the existing `if "pending" not in p.parts: continue` guard, making that guard dead code today. Measured: the loop yields 50 files, 0 of them outside `pending/`.
  2. NAME THE DIVERGENCE HAZARD IN A COMMENT. `include_retired` is the exact flag that docstring identifies as having produced a measured zero-versus-one `check.id6-collision` disagreement between `aw check` (default False) and `doctor.py` (unconditional True). Widening it here is deliberate and must be recorded as such, with the traversal used only for the cheap predicate so the two surfaces stay comparable by construction.
  3. USE `plans.read_status`, THE SAME READER AS E-02.1, and apply the SAME cutover gate, so the two surfaces report the identical file set. Without both, they differ by 25 plans (measured).
  Note `RULE_REGISTRY["check.ipd-lint-diagnostic"]` is registered `info`, the unique severity `artifact_core.drift_exit_code` exempts (`error` -> 1, `warning` -> 1, `info` -> 0), so this half cannot move any exit code; do NOT promote it as part of this plan. Add a `tests/test_check_engine.py` case for a temp repo with a post-cutover `to-review` plan in `executed/`.
  - Depends on: E-01, E-02
  - Expected outcome: `aw check` on that temp repo reports `check.ipd-lint-diagnostic` naming `IPD-M105` for the file; `aw check plans` on this repository reports no `IPD-M105`; and the sweep's file set equals `aw ipd lint`'s on the same fixture.
  - Execution state: pending

- [ ] E-05 Run the bare suite `python3 -m pytest`.
  - Depends on: E-03, E-04
  - Expected outcome: the summary line shows 0 failed.
  - Execution state: pending

- [ ] E-06 Re-derive the two repository-wide baselines this plan must not regress, and record the numbers in the plan's evidence: `aw ipd lint --all` still exits 0 (today: `conforming=50, quarantined=0, legacy/not evaluated=727, error=0`), and `aw check plans` reports no `IPD-M105`. These are LIVE-ARTIFACT counts: re-derive them at execution time rather than asserting the authoring numbers.
  - Depends on: E-05
  - Expected outcome: `aw ipd lint --all` exits 0 with `error=0`, and `aw check plans` names no `IPD-M105`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `_dir_of` anchors on the first disposition name found in the resolved path parts, so shards resolve to their terminal directory.
- `check_engine.check_ipd_lint_reach` docstring (`k9awrq`, `02-k9awrq-D3`) deliberately scopes the full lint to `pending/` because terminal lint is empty by construction. E-04 keeps that scope for the full lint and adds only the predicate. Note the docstring's OTHER load-bearing point, which E-04 must honor: it names `include_retired` as the cause of a measured zero-versus-one `check.id6-collision` disagreement between `aw check` (default False) and `doctor.py` (unconditional True), and E-04 has to widen exactly that flag to reach the terminal tree at all (F-9).
- STATUS NORMALIZATION IS NOT SHARED BETWEEN THE TWO MODULES, and this is the single most important convention for this plan. `plans.read_status` applies `normalize_status`; `ipd_schema` has no equivalent and `ipd_lint.parse(...).meta_fields["Status"]` is raw. Picking different readers on the two surfaces is what would have made them disagree by 25 plans (F-6), so both E-02 and E-04 are bound to `plans.read_status`.
- A DATE CUTOVER IS A SHIPPED PATTERN, not an invention: `ipd_lint.CITATION_ANCHOR_CUTOVER_DATE` is a compact `YYYYMMDD` constant read off the plan's own `- Date:`, with a documented re-measurement convention, a test asserting it stays strictly greater than the newest plan date, and a stated rule that a plan with no parseable `- Date:` counts as pre-cutover. E-02.2 copies that shape rather than inventing a config key.
- `artifact_audit.audit_tracked_artifact` returns `None` for a pre-terminal declared status, for liveness safety. That module and its doctor rule are out of scope. A plan can never be live in `executed/`, because `ipd_lifecycle.finalize` writes the status and moves the file together in a coordinator-owned worktree, but changing the shared module's skip list would affect `aw runs`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Probe 2026-09-25 (`/tmp/opencode/g3/probe-m105term/`): an executed plan copied with `- Status: to-review`:

| Surface | Result |
|---|---|
| `ipd_lint.lint_text(..., directory="executed")` | `legacy/not evaluated`, `[]` |
| `ipd_lint.lint_file(<.../executed/x.ipd.md>)` | `legacy/not evaluated`, `[]` |
| `attention._plans_record` | no drift: `attention.disposition-mismatch` requires `status in plans_mod.TERMINAL` |
| `artifact_audit.audit_tracked_artifact` (doctor) | `None`: pre-terminal status is skipped |
| `lint_text(<status executed>, directory="pending")` | `IPD-M105` (the covered direction) |

So the rule that 02af026e revived (`attention.disposition-mismatch`) and the doctor rule both cover only terminal-versus-terminal, and nothing covers this case. Both re-verified at review: the attention rule is guarded by `status in plans_mod.TERMINAL`, and `audit_tracked_artifact` returns None when `expected_dir_for_status(declared) == "pending"`; each reports 0 findings over the terminal tree today.

BLAST RADIUS, CORRECTED AT REVIEW. The original claim here ("0 errors over 683+36+4 = 723") was WRONG in both the numerator and the denominator, and OQ-01's entire resolution rested on the zero.

| # | Finding | Evidence |
|---|---------|----------|
| F-5 | THE RAW-READER BLAST RADIUS IS 25 OF 727, NOT 0 OF 723. `_check_path_status` over the RAW `- Status:` value of every file in the three terminal trees (687 executed, 36 superseded, 4 not-executed, all carrying a Status field) returns 25 errors. All 25 are dated 2026-06-30..2026-07-11 and carry prose or upper-case status lines (`- Status: EXECUTED`, `- Status: EXECUTED 2026-07-03 (approved by user; ...)`). They CANNOT be fixed: `AGENTS.md` forbids adding commits to a plan in `executed/` and the `ipd-executed-transition-gate` pre-commit hook enforces it. This is why E-02.2 adds a date cutover and why OQ-01 is re-resolved. | Driven at review over `.aw/records/plans/{executed,superseded,not-executed}` with `ipd_lint._dir_of` as the anchor; newest affected date 2026-07-11. Authoring CONTEXT, re-derive at execution (E-06). |
| F-6 | THE TWO READERS DISAGREE BY EXACTLY THOSE 25. `plans.read_status` applies `normalize_status` and flags 0 terminal-tree plans; `doc.meta_fields["Status"]` is raw and flags 25 (`vfa1tl` yields `'EXECUTED'`, not in `S.TERMINAL`). The original E-02 read the raw field while E-04 prescribed `plans.read_status`, so this plan would have shipped `aw ipd lint` and `aw check` reporting different sets for one rule. That is the defect `check_ipd_lint_reach`'s docstring exists to prevent, recording a measured zero-versus-one `check.id6-collision` disagreement between `aw check` and `aw doctor`. Both items now use `plans.read_status`. | Driven at review: raw pairing 25, normalized pairing 0; `plans.read_status` returns `normalize_status(...)`; `ipd_schema` exposes no `normalize_status`. |
| F-7 | TWO EXIT-CODE SURFACES, POINTING OPPOSITE WAYS. `check.ipd-lint-diagnostic` is registered `info`, the unique severity `artifact_core.drift_exit_code` exempts (`error` -> 1, `warning` -> 1, `info` -> 0), so the `aw check` half cannot red CI even though `aw check plans` IS fail-closed in `tests.yml`. But `aw ipd lint --all` computes `exit_code = 1 if any_error else 0` from the per-file DISPOSITION, so flipping 25 plans from `legacy` to `error` would make that command start exiting 1. Today it prints `conforming=50, quarantined=0, legacy/not evaluated=727, error=0` and exits 0. The cutover is what preserves that. | Driven `artifact_core.drift_exit_code` per severity; `aw ipd lint --all` run at review; `RULE_REGISTRY["check.ipd-lint-diagnostic"]` is `("info", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-05")`. |
| F-8 | THIS PLAN NARROWS A SHIPPED DOCSTRING'S RATIONALE. `artifact_audit.audit_tracked_artifact` justifies itself with "THIS IS EXACTLY THE `IPD-M105` BLIND SPOT, which is what the doctor rule adds rather than duplicates". After E-02 the blanket claim is no longer true for the pre-terminal direction, though the rule's UNIQUE coverage (terminal-versus-terminal) is untouched. No code change is owed; the stale sentence is recorded in Deferred. | The quoted docstring sentence and its 2026-09-13 measurement note. |
| F-9 | E-04 WAS A MEASURED NO-OP. `check_ipd_lint_reach`'s loop passes no `include_retired`, and `_iter_type_files` skips every path `is_retired` calls true, which includes all three terminal segments, so the existing `if "pending" not in p.parts: continue` guard is dead code. The loop yields 50 files, 0 outside `pending/`. Reaching the tree requires `include_retired=True`, the same flag the docstring blames for the prior cross-surface divergence. | Driven at review: `len(list(_iter_type_files(repo,'plans')))` is 50, non-pending 0; `_RETIRED_PATH_SEGMENTS` contains `executed`, `superseded`, `not-executed`. |

## Proposed changes (ordered, validatable)

1. E-01: route the pre-terminal path error to `IPD-M105`.
2. E-02/E-03: evaluate the path/status predicate ahead of the terminal short-circuit, through `plans.read_status` and behind a date cutover.
3. E-04: surface the SAME set through the existing `aw check` rule, with `include_retired=True` and the same reader and cutover.
4. E-05/E-06: the bare suite, then re-derive the two repository-wide baselines.

## Deferred / out of scope (with reason)

- Changing `artifact_audit.audit_tracked_artifact` or `attention.disposition-mismatch` to cover pre-terminal statuses. With E-02 and E-04, the lint/check surface owns this and these would duplicate it. `audit_tracked_artifact`'s skip is also load-bearing beyond this rule: its docstring gives a LIVENESS reason (a pre-terminal record may be mid-flight and liveness is not readable from tracked state) and the module is shared with `aw runs`.
  - Carrier-Declined: duplicate coverage; the shared audit's liveness skip also serves `aw runs`.
- Correcting the now-narrowed sentence in `artifact_audit.audit_tracked_artifact`'s docstring (F-8). It asserts lint is exempt over the WHOLE terminal tree as its reason for existing; after E-02 that holds only for the terminal-versus-terminal direction, which remains the doctor rule's unique coverage.
  - Carrier-Declined: a docstring-accuracy correction with no behavior change and no coverage gap, in a module this plan deliberately does not touch. The narrowing is recorded here and in F-8 so the next reader of that module finds it; nothing is outstanding that a carrier would track.
- Evaluating the full lint (beyond path/status) for terminal-tree plans.
  - Carrier-Declined: that is the grandfathering the repository chose deliberately (`_is_terminal_dir` short-circuit); this bug concerns only the one predicate. `check_ipd_lint_reach`'s cost argument (626+ reads and parses) also stands, which is why E-04 widens only the cheap predicate.
- Promoting `check.ipd-lint-diagnostic` from `info` to a gating severity.
  - Carrier-Declined: its `info` registration is a recorded measurement (DECISION 02-k9awrq-D1) with its own open question (OQ-04 on that plan) owning the promotion; changing it here would move an exit code this plan has no mandate over.

## Scope check

- Over-scope: none.
- Under-scope: none. The cutover constant and the `include_retired` widening are both additions review added to make the declared goal achievable, not new goals.
- Explicitly OUT: `artifact_audit.py`, `attention.py`, `doctor.py`, the `check.ipd-lint-diagnostic` severity registration, and any edit to the 25 pre-cutover plans (forbidden by `AGENTS.md` and the `ipd-executed-transition-gate` hook).

## Required tests / validation

New tests in `tests/test_ipd_lint.py` (including the upper-case `EXECUTED` regression and the pre-cutover suppression), `tests/test_check_engine.py`, and the updated `tests/test_ipd_schema.py` expectation, shown failing before the fix. Then the bare suite. Then the two repository-wide baselines re-derived (E-06): `aw ipd lint --all` still exiting 0, and `aw check plans` naming no `IPD-M105`. The cross-surface agreement (E-02 and E-04 reporting the same file set) must be shown on one fixture, because that is the only evidence that proves F-6 is closed rather than asserted.

## Spec / documentation sync

N/A: no `.spec.md` is amended. The `ipd-spec` describes `IPD-M105` as the path/status combination rule; this plan makes it fire in a directory where it was previously unreachable, without changing its meaning.

## Open questions

### OQ-01: Date cutover or severity split instead of error everywhere?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RE-RESOLVED AT REVIEW ON A CORRECTED MEASUREMENT. The original resolution here read "0 of 723 terminal-tree plans disagree with their directory, so an error finding grandfathers nothing and needs no cutover. The default is ERROR." That zero was wrong (F-5): the real figure is 25 of 727 through the reader E-02 originally prescribed, and those 25 CANNOT be fixed, because `AGENTS.md` forbids adding commits to a plan in `executed/` and the `ipd-executed-transition-gate` hook enforces it. An unconditional error would therefore make `aw ipd lint --all` exit 1 permanently (F-7). ANSWER: a DATE CUTOVER, which is the first of the three options backlog `dbslfm` named and which the repository already ships as `ipd_lint.CITATION_ANCHOR_CUTOVER_DATE`, complete with a re-measurement convention and a strictly-greater-than test. A severity split was rejected because `warning` also drives a nonzero findings exit (measured), so it would not spare the corpus, and a permanently-warning tree is the outcome `_merge_setid_length_advisory` records the repository rejecting. Normalizing the reader (E-02.1) independently reduces the raw 25 to 0, so the cutover is belt-and-braces for anything the normalizer does not cover; both are required, for the separate reasons F-6 and F-5 give.
- Carrier-Declined: resolved in this plan by E-02.2 (the cutover) plus E-02.1 (the shared reader), both with pasted-evidence V items; nothing is outstanding for a carrier to track. A maintainer preferring a severity split instead would be making a new decision against the measurement recorded here, not discharging a deferred obligation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_ipd_schema.py -v -k path_status` output showing the updated message test passed, and a `python3 -c` snippet whose output shows `IPD-M105` (not `IPD-M104`) for `to-review` in `reusable`. This item proves MESSAGE ROUTING ONLY and must not be read as covering the terminal tree: `reusable` is not a terminal directory, so `lint_text` never short-circuits there. V-02 owns the terminal-tree behavior.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: four pastes, all from driven probes. (a) A POST-cutover fixture in `executed/` showing `error ['IPD-M105']` for `to-review` and for `superseded`, and `legacy/not evaluated []` for `executed`. (b) THE PRE-CUTOVER SUPPRESSION, proven on a REAL named plan: `lint_file` on `.aw/records/plans/executed/20260709-interactive-git-00-vfa1tl-*.ipd.md` (whose raw status is the upper-case `EXECUTED`) still returning `legacy/not evaluated` with no diagnostics. (c) THE READER PROOF (F-6): print both `plans.read_status(<that file>)` and `ipd_lint.parse(...).meta_fields["Status"]` for it, showing `'executed'` and `'EXECUTED'` respectively, and confirm the implementation uses the former. (d) The full terminal-tree count of plans the new code newly errors on, which must be 0 for this repository. Omitting (b), (c) or (d) does not validate E-02: (a) alone passes against the rejected unconditional-error design that F-5 and F-7 refute.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the pytest output for the new `tests/test_ipd_lint.py` cases, showing them passed, and the same cases run against a scratch copy of the pre-fix `ipd_lint.py`, showing them FAILED with a `legacy/not evaluated` disposition. Include the upper-case-`EXECUTED` case and the cutover-constant-is-strictly-greater assertion in the pasted output.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: three pastes. (a) The new `tests/test_check_engine.py` case passing. (b) CROSS-SURFACE AGREEMENT (F-6): on ONE fixture repo containing a post-cutover offender in `executed/` plus a pre-cutover legacy file, print the set of files `check_ipd_lint_reach` reports and the set `ipd_lint.lint_file` errors on, and show they are EQUAL. (c) Proof the sweep is not a no-op (F-9): show it reporting the fixture's terminal-tree plan, which the unfixed `include_retired`-less loop cannot do. Also paste `python3 -m agent_workflows check plans --agent 2>&1 | grep -c IPD-M105` on this repository printing `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run, showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw ipd lint --all` output showing its `counts:` line with `error=0` and its exit code 0 (the F-7 regression this item exists to catch), and `aw check plans` showing no `IPD-M105`. Re-derive both rather than restating the authoring numbers; if either differs from the recorded baseline, say so with the new figure instead of asserting the old one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Six items, one concern: making the path/status predicate reach the terminal tree from both surfaces without erroring on a corpus nobody may edit. The count grew from five at review because the two repository-wide baselines (`aw ipd lint --all` exit 0, `aw check plans` clean of `IPD-M105`) are a distinct verification surface from the unit tests and are the only place F-7's exit-code regression is observable; they were in no item before. No item introduces a second concern.

WHAT A HUMAN IS APPROVING, and this description CHANGED at review, so read it rather than the original framing. Not "make a rule fire where nothing is affected" but: make `IPD-M105` reach the three terminal directories, through one shared status reader, behind a DATE CUTOVER that permanently suppresses 25 pre-cutover legacy plans (dated 2026-06-30..2026-07-11) which carry prose or upper-case status lines and which policy forbids editing. Three things to weigh. FIRST, the plan originally asserted the blast radius was ZERO and concluded no cutover was needed; that was wrong (F-5), and approving this is approving the cutover that replaces it. SECOND, the suppression is permanent for those 25: they will never be conformant and the rule will never see them, which is the deliberate cost of not being able to fix an executed plan. THIRD, the `aw check` half cannot red CI (the rule is registered `info`, the one severity the exit code exempts) even though `aw check plans` is fail-closed in `tests.yml`; the surface that CAN change an exit code is `aw ipd lint --all`, and E-06 exists to prove it did not.

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The intended surface: in `agent_workflows/ipd_schema.py`, the pre-terminal arm's message string inside `_check_path_status` only; in `agent_workflows/ipd_lint.py`, a new `M105_TERMINAL_CUTOVER_DATE` constant with its date-applies helper plus the pre-check ahead of the `_is_terminal_dir` short-circuit in `lint_text`; in `agent_workflows/check_engine.py`, `check_ipd_lint_reach`'s traversal flag and its non-pending branch; and the three named test files. EXPLICITLY NOT IN SCOPE: `artifact_audit.py`, `attention.py`, `doctor.py` (all three Deferred, one with a stale docstring recorded in F-8); the `check.ipd-lint-diagnostic` severity registration; `_check_path_status`' other arms and their messages; the full `lint_file` sweep's pending scope, which stays as it is; `plans.normalize_status` itself; and the 25 pre-cutover plans, which must not be edited. An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-02(b)(c)(d) and V-04(b)(c). V-02(a) alone passes against the REJECTED unconditional-error design, so the pre-cutover suppression must be shown on the real named plan `vfa1tl` and the newly-erroring count must be shown as 0. V-04(b) is the only evidence that the two surfaces agree rather than merely both existing, and V-04(c) is the only evidence E-04 is not the no-op F-9 measured.

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: the re-derived count of raw-reader disagreements differs materially from 25 or its newest date is later than 2026-07-11, since the cutover floor is computed from that date and a changed corpus means re-deriving it rather than copying this plan's number; a plan authored AT OR AFTER the chosen cutover already sits in a terminal directory disagreeing with it, because that is a real live defect this plan would newly report and it needs a human decision about the plan, not a constant adjustment; or `_iter_type_files`/`is_retired` semantics have changed such that `include_retired=True` no longer selects the terminal tree, which would invalidate E-04's whole mechanism.

This plan is `reviewed` and needs explicit human approval (`Status: approved`) before execution. The executor commits only the Scope-Paths via `aw commit lz0o6j -- <paths>`, never `git add -A`, and never pushes. It inherits `- Blocks-Release: next` from backlog `dbslfm` (`Work-Kind: bug`) and discharges it, so `dbslfm` may close once this is executed and validated. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run` / `aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-06 carry pasted evidence.
