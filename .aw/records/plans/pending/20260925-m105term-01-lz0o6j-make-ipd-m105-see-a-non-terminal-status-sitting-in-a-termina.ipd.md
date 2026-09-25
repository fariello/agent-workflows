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
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: lz0o6j

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog dbslfm; re-measured that lint, attention and doctor are all silent on a to-review plan in executed/, and that 0 of 723 terminal-tree plans currently disagree with their directory.

## Goal

A plan sitting in a terminal directory whose declared status names a different disposition yields an `IPD-M105` error from `aw ipd lint`, and the same error is reachable from `aw check`. The rest of the terminal tree keeps its `legacy/not evaluated` grandfathering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the lint rule

- [ ] E-01 In `ipd_schema._check_path_status`, change the pre-terminal message from `"pre-terminal Status must live under pending/"` to one containing `directory`, for example `"pre-terminal Status must live under the pending/ directory"`. Today `ipd_lint.check_metadata` routes to `C_META_PATH` only when the message contains `"directory"`, so this case is reported as the generic `IPD-M104` (measured: with `legacy=True` in `executed/`, a `to-review` status yields `('IPD-M104', 'Status: pre-terminal Status must live under pending/')`). Update the pinned expectation in `tests/test_ipd_schema.py`.
  - Depends on: none
  - Expected outcome: `lint_text(<to-review text>, directory="reusable")` reports `IPD-M105`, not `IPD-M104`, for the Status field.
  - Execution state: pending

- [ ] E-02 In `ipd_lint.lint_text`, before the `_is_terminal_dir(directory) and not legacy and checkpoint != "post-transition"` short-circuit, read the declared `Status` from `doc.meta_fields`. When `ipd_schema._check_path_status(status, directory)` returns an error, return `LintResult(S.DISPOSITION_ERROR, [Diagnostic(0, 0, C_META_PATH, ...)])` with ONLY that diagnostic. Otherwise keep returning `DISPOSITION_LEGACY` with no diagnostics. A plan whose status agrees with its directory therefore keeps exactly today's result, and only the path/status predicate is evaluated for the terminal tree. Add a comment citing this plan and the "measured 0 of 723" baseline.
  - Depends on: E-01
  - Expected outcome: `to-review` in `executed/` reports an `error` disposition with `IPD-M105`; `superseded` in `executed/` reports `IPD-M105`; `executed` in `executed/` still reports `legacy/not evaluated` with no diagnostics. The same holds under a `executed/202608/` shard, because `_dir_of` resolves the anchor.
  - Execution state: pending

- [ ] E-03 Add tests in `tests/test_ipd_lint.py` covering E-02 via both `lint_text` and `lint_file` (a real file under `.aw/records/plans/executed/` and `executed/202608/` in a temp repo). Cover the three terminal directories crossed with pre-terminal, other-terminal and matching statuses, and include a status-less terminal file, which stays `legacy`.
  - Depends on: E-02
  - Expected outcome: the new tests pass with the fix and fail on the unfixed `ipd_lint.py`.
  - Execution state: pending

### Task group 2: reachability from aw check

- [ ] E-04 In `check_engine.check_ipd_lint_reach`, for plans NOT in `pending/`, run only the cheap path/status predicate (`plans.read_status` plus `ipd_schema._check_path_status` on the `_dir_of` anchor) instead of a full `lint_file`, which is what the docstring's "guaranteed empty" note warns against spending on 626+ files. Emit the existing `check.ipd-lint-diagnostic` rule with `IPD-M105` in the detail, so no new rule id is registered. Add a `tests/test_check_engine.py` case for a temp repo with a `to-review` plan in `executed/`.
  - Depends on: E-01
  - Expected outcome: `aw check` on that temp repo reports `check.ipd-lint-diagnostic` naming `IPD-M105` for the file, and `aw check` on this repository reports none.
  - Execution state: pending

- [ ] E-05 Run the bare suite `python3 -m pytest`.
  - Depends on: E-03, E-04
  - Expected outcome: the summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `_dir_of` anchors on the first disposition name found in the resolved path parts, so shards resolve to their terminal directory.
- `check_engine.check_ipd_lint_reach` docstring (`k9awrq`, `02-k9awrq-D3`) deliberately scopes the full lint to `pending/` because terminal lint is empty by construction. E-04 keeps that scope for the full lint and adds only the predicate.
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

So the rule that 02af026e revived (`attention.disposition-mismatch`) and the doctor rule both cover only terminal-versus-terminal, and nothing covers this case. Blast radius: `_check_path_status` over every plan in the three terminal trees (683 executed, 36 superseded, 4 not-executed) returns 0 errors. Because of that, the backlog's cutover-versus-severity decision needs no date cutover.

## Proposed changes (ordered, validatable)

1. E-01: route the pre-terminal path error to `IPD-M105`.
2. E-02/E-03: evaluate only the path/status predicate ahead of the terminal short-circuit.
3. E-04: surface it through the existing `aw check` rule.

## Deferred / out of scope (with reason)

- Changing `artifact_audit.audit_tracked_artifact` or `attention.disposition-mismatch` to cover pre-terminal statuses. With E-02 and E-04, the lint/check surface owns this and these would duplicate it.
  - Carrier-Declined: duplicate coverage; the shared audit's liveness skip also serves `aw runs`.
- Evaluating the full lint (beyond path/status) for terminal-tree plans.
  - Carrier-Declined: that is the grandfathering the repository chose deliberately (`_is_terminal_dir` short-circuit); this bug concerns only the one predicate.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

New tests in `tests/test_ipd_lint.py`, `tests/test_check_engine.py`, and the updated `tests/test_ipd_schema.py` expectation, shown failing before the fix. Then the bare suite, and `aw check` on this repository to confirm the 0-finding baseline.

## Spec / documentation sync

N/A: no `.spec.md` is amended. The `ipd-spec` describes `IPD-M105` as the path/status combination rule; this plan makes it fire in a directory where it was previously unreachable, without changing its meaning.

## Open questions

### OQ-01: Date cutover or severity split instead of error everywhere?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: The backlog asked for the blast radius to be counted first. Measured: 0 of 723 terminal-tree plans disagree with their directory, so an error finding grandfathers nothing and needs no `config.dependency_cutover_date` cutover. The default is ERROR.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_ipd_schema.py -v -k path_status` output showing the updated message test passed, and a `python3 -c` snippet whose output shows `IPD-M105` (not `IPD-M104`) for `to-review` in `reusable`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a `python3 -c` probe that prints the `lint_text` disposition and codes for `to-review`/`superseded`/`executed` in `executed/`. It must show `error ['IPD-M105']`, `error ['IPD-M105']`, and `legacy/not evaluated []` respectively.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the pytest output for the new `tests/test_ipd_lint.py` cases, showing them passed, and the same cases run against a scratch copy of the pre-fix `ipd_lint.py`, showing them FAILED with a `legacy/not evaluated` disposition.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the pytest output for the new `tests/test_check_engine.py` case, showing it passed. Also paste `python3 -m agent_workflows check 2>&1 | grep -c IPD-M105` on this repository, printing `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run, showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Commit through `aw commit <this plan> -- <Scope-Paths>`; never push. Move the plan to `executed/` via the lifecycle only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence.
