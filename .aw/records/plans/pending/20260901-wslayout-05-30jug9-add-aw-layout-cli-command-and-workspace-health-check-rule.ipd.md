# IPD: Add aw layout CLI command and workspace health check rule

- Date: 2026-09-01
- Kind: child
- Concern: Workspace layout inspection needs a dedicated CLI verb (`aw layout`) and workspace health check in `aw check` per Spec kw5y2s.
- Scope: Add `aw layout` command (supporting `--json`, `--schema`) to `agent_workflows/cli.py`, add layout consistency checking to `check_engine.py` / `doctor.py`, and author unit tests in `tests/test_cli_layout.py`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/doctor.py, agent_workflows/command_surface.py, tests/conformance_matrix.py, tests/test_cli_layout.py
- Item-Dependencies: executed:hauwqh,executed:zvk796
- Status: to-review
- Readiness: no-go
- Set: wslayout
- Order: 5
- Highest E allocated: 03
- Author: antigravity
- Id: 30jug9
- From-Spec: kw5y2s

## Workflow history
- 2026-09-04 to-review (aw set): Applied deterministic plan-review repairs; controlling spec kw5y2s awaits renewed human approval.

- 2026-09-04 reviewed (antigravity): /aw plan-review-long: APPROVE WITH REVISIONS APPLIED; PR-019, PR-022, PR-023 fixed (added eleven-clause execution contract, structured findings evidence table, conventions, bare-suite validation with baseline re-measurement, and readiness).
- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - PR-004 (existing `aw context --json` already emits logical_roots), PR-008 (`aw layout` collides with `aw migrate-layout`), PR-007.
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).
- 2026-09-01 to-review (aw set): plan-review PR-007: metadata now matches the orchestrator sequence table

## Goal

Provide user-facing and agent-facing inspection via `aw layout` and automated health verification during `aw check`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: CLI Verb Implementation

- [ ] E-01 Add the read-only `layout` command across `agent_workflows/cli.py` and `agent_workflows/command_surface.py`, supporting `--json`, `--schema`, agent output, and formatted human inspection.
  - Depends on: none
  - Expected outcome: `aw layout` command works in human and agent modes.
  - Execution state: pending
  - Set-level prerequisites: `hauwqh` and `zvk796` must both be executed first; see `- Item-Dependencies:` in the metadata. `hauwqh` supplies emission behavior, while `zvk796` supplies the `reviews` noun required by V-03.
  - NAMING DECISION RESOLVED BY MAINTAINER (2026-09-03, OQ-01): Option (a) chosen. Add a new top-level
    read-only `aw layout` verb. It exposes the record-class vocabulary and JSON Schema, neither of which
    `aw context` models; `aw context` remains the inspector for resolved logical roots and `aw path <root>`
    remains the scripting surface for one resolved path. Although `aw migrate-layout` is adjacent in
    tab completion, its transactional physical-layout migration purpose is distinct from read-only model
    inspection. Human output must make the read-only nature obvious.
  - Per the maintainer's OQ-2 ruling the emitted `layout.json` is GITIGNORED, so this command MUST work
    from the in-process model even when no emitted file exists (a fresh clone has none until an install
    runs). It must not require the file to be present.
  - CLI output contract: route the handler through `select_output(args)`, `CommandResult`, and `get_renderer`; add a `CommandDeclaration` and the read-only `LIVE_SAFE_LEAVES` scenario. Validate human, `--agent`, `--json`, `--no-color`, and usage-error parity, including ANSI-free agent output and exit 0/1/2 behavior.

### Task group 2: Workspace Health Check

- [ ] E-02 Add layout verification rule (`check.system-layout-missing` / `check.system-layout-drift`) to `agent_workflows/check_engine.py` and `doctor.py`.
  - Depends on: E-01
  - Expected outcome: `aw check` verifies that installed `.aw/system/layout.json` exists and is valid.
  - Execution state: pending
  - THIS RULE IS REQUIRED, NOT OPTIONAL, and its importance rose because of the maintainer's OQ-2 ruling
    (plan-review PR-004): since the emitted artifacts are GITIGNORED, a fresh clone legitimately has
    NONE, so this check is the only loud-failure backstop that tells a user or CI job to run an install
    before a non-Python tool tries to read the layout.
  - Consequence for severity: "missing" must NOT be a hard error in a repo that has simply never been
    installed, or `aw check` would fail on every fresh clone by design. Distinguish (a) no AW workspace
    at all, (b) an installed workspace whose `layout.json` is absent (the real defect this catches), and
    (c) present but version-mismatched or schema-invalid (`drift`). State the chosen severity for each.
  - `check.system-layout-drift` compares the emitted `framework_version` against the installed
    `.aw/system/VERSION`; that is what makes a stale emitted file detectable at all, given it is not in
    git and therefore has no diff to review.

### Task group 3: Unit Tests

- [ ] E-03 Author unit tests in `tests/test_cli_layout.py` (NEW FILE; it does not exist today) covering `aw layout`, `aw layout --json`, and `aw layout --schema`.
  - Depends on: E-01, E-02
  - Expected outcome: `pytest tests/test_cli_layout.py` passes cleanly.
  - Execution state: pending
  - Must also cover the three `aw check` cases from E-02 (clean / missing / drift) and the fresh-clone
    no-workspace case, so the new rule's severity choices are pinned by tests rather than by prose.
  - Must include the union-vocabulary CLI fence (plan-review PR-001): assert `aw check reviews` is
    accepted (net-new per the maintainer ruling) AND `aw check roadmaps` still is, so a future edit that
    silently drops a live type fails here as well as in `wpu5zu`'s model test.
  - Must cover the command declaration and live conformance matrix scenario required for every new read-only CLI leaf; run the full conformance suite (`make test-all`) before finalizing this child.

## Project conventions discovered (Step 0)

- `agent_workflows/cli.py`: main CLI surface.
- `agent_workflows/check_engine.py`: consistency check engine.
- `agent_workflows/doctor.py`: comprehensive read-only repository health inspector.
- Controlling spec `kw5y2s` Section 6.2 is `approved` again (re-measured at round 5; the round-4 `to-review` claim is stale). Its `aw layout` naming resolution and gitignored layout.json handling are unchanged, and the spec is immutable during execution.
- `aw layout` is a read-only inspection verb; distinct from transactional `aw migrate-layout`.
- Because `.aw/system/layout.json` is gitignored, `aw layout` must fall back to the in-process model if the file is absent on a fresh clone.
- `check.system-layout-missing` and `check.system-layout-drift` rules distinguish (a) no workspace (clean/skip), (b) installed workspace with missing layout (defect), and (c) installed workspace with version/schema drift (defect).
- Python 3.9 is the floor (`pyproject.toml:12`).

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **`aw layout` provides direct stdout inspection without requiring non-Python tools to parse filesystem files.** Emits human-readable overview, `--json`, and `--schema`. | Spec Section 6.2; `cli.py`. |
| F-2 | **Naming decision is resolved by the maintainer (OQ-01).** `aw layout` is added as a new top-level read-only verb because it exposes the record-class vocabulary and schema, which `aw context` does not model. | Maintainer resolution on OQ-01. |
| F-3 | **`aw check` layout rules are the essential loud-failure backstop.** Because emitted layout files are gitignored via `.aw/.gitignore`, git cannot show diffs; `check.system-layout-missing` and `check.system-layout-drift` catch absent or out-of-date files. | `check_engine.py`; `doctor.py`. |
| F-4 | **`tests/test_cli_layout.py` is newly created by this plan.** Covers `aw layout` modes, the three check engine states, and the union vocabulary CLI fence (`aw check reviews` and `aw check roadmaps`). | E-03 / V-03 notes; file verified absent before execution. |
| F-5 | **Concurrent scope collision on `agent_workflows/cli.py`.** Declared by 13 pending plans. Re-measurement required immediately before execution. | Measured `grep -l` over pending plans. |

## Proposed changes (ordered, validatable)

1. Add `layout` parser and runner in `agent_workflows/cli.py` (E-01).
2. Add check rules in `check_engine.py` and integrate with `doctor.py` (E-02).
3. Author unit test suite in `tests/test_cli_layout.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none. `tests/test_cli_layout.py`, `agent_workflows/command_surface.py`, and `tests/conformance_matrix.py` are in `Scope-Paths` because every new read-only CLI leaf must declare and exercise the output contract.
- Concurrent-scope collision (PR-010): `agent_workflows/cli.py` is declared by 13 pending plans. Re-measure immediately before execution.

## Required tests / validation

- `python3 -m pytest tests/test_cli_layout.py` passing (NEW file created by E-03), with actual output pasted.
- Bare full repository suite `python3 -m pytest` from the PRIMARY checkout, with baseline re-measured on unmodified HEAD at execution time.
- `aw check reviews` accepted (net-new) AND `aw check roadmaps` still accepted, proving the union vocabulary added a type without removing one.
- `aw check --agent` showing no new diagnostic class (expecting the six `tk1gqo` reports).
- `aw sanitize --agent` passing clean.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 6.2. Spec is `approved`; do NOT edit it.
- Update `--help` text in CLI parser for `aw layout`.

## Open questions

### OQ-01: Should the layout surface be a new top-level `aw layout` verb, or live under an existing noun?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-008
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-03: add a new read-only `aw layout` verb. It exposes the record-class vocabulary and JSON Schema, neither of which `aw context` models; `aw context` remains the inspector for resolved logical roots and `aw path <root>` remains the scripting surface for one resolved path. Although `aw migrate-layout` is adjacent in completion, its transactional migration purpose is distinct from read-only model inspection.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `aw layout --json` and `aw layout --schema` emit expected JSON documents; paste
    both outputs, and confirm the `--json` document validates against the `--schema` document.
  - PLUS the recorded naming decision (PR-008): quote the justification written into E-01, naming which
    option was chosen and why `aw context` could not carry it. An unrecorded default is a FAILED
    validation.
  - PLUS the no-emitted-file case (OQ-2 consequence): run the command in a workspace where
    `.aw/system/layout.json` does NOT exist and paste output proving it still succeeds from the
    in-process model.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw check` includes the layout verification rule; paste output from THREE cases:
    (a) an installed workspace with a valid emitted file (clean), (b) an installed workspace with the
    file deleted (reports `check.system-layout-missing`), (c) a version-mismatched file (reports
    `check.system-layout-drift`).
  - PLUS the fresh-clone case: paste evidence that a repo with no AW workspace does NOT fail this rule,
    since the emitted file is gitignored and legitimately absent until an install runs.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_cli_layout.py` passes cleanly with the ACTUAL runner
    output pasted, and the NEW file is present in the commit.
  - PLUS the union-vocabulary surface proof (PR-001): paste `aw check reviews` succeeding (it errors
    today with "unknown artifact type 'reviews'") and `aw check roadmaps` STILL succeeding, proving the
    Set added a type without removing one.
  - PLUS the BARE FULL SUITE: `python3 -m pytest` (bare) with the `N passed` summary line pasted and zero
    regressions, as this is the Set's final child and the last gate before the orchestrator's E-02.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE EXTERNAL SPEC GATE IS CLEARED (re-measured at plan-review round 5): controlling spec `kw5y2s` is `- Status: approved` with a `--by-human` attestation, so `ipd-lifecycle.md:16` is satisfied. The round-4 "reopened" wording was accurate when written and then outlived its premise: the plans were demoted at commit `298be4b2` (00:10:38 -0400) and the corrected spec was re-approved 459 seconds later at `3e05c2ba` (00:18:17 -0400). RE-VERIFY the spec's `- Status:` line yourself before starting rather than trusting this paragraph; if it is not `approved`, STOP (a genuinely absent prerequisite). The only remaining gate is ordinary human approval of this plan.

Execution contract:

1. Human approval of this plan is required before execution. There are no unresolved blocking questions: OQ-01 is `Status: resolved` by the maintainer.
2. Serial prerequisites: `hauwqh` (Order 04) AND `zvk796` (Order 02) MUST reach `executed` before starting this plan. The emitted-layout behavior comes from Order 04, while `aw check reviews` requires the new noun from Order 02.
3. RE-MEASURE CONCURRENT SCOPE COLLISIONS IMMEDIATELY BEFORE EXECUTION: `agent_workflows/cli.py` is declared by 13 pending plans. If concurrent edits are in flight, verify mergeability before editing.
4. Read-only verb: `aw layout` must be strictly read-only, clearly distinguished from `aw migrate-layout`.
5. Missing-file tolerance: `aw layout` must function from in-process defaults when `.aw/system/layout.json` does not exist on disk (fresh clone).
6. Non-failing missing check on fresh clone: `check.system-layout-missing` must not report an error on a repo without an installed AW workspace.
7. Validation requires ACTUAL pasted runner output; never claim a pass without running the commands.
8. Shared checkout discipline: commit only files this plan changed, path-scoped. Verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged`. Never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
9. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`).
10. Scope fence: declared paths are `agent_workflows/cli.py`, `agent_workflows/check_engine.py`, `agent_workflows/doctor.py`, and `tests/test_cli_layout.py`. An out-of-scope edit requires `--scope-reason`, and an unmodified declared path requires `--scope-ack`. Do NOT stop over a scope question. DO stop and report if a concurrent-edit conflict cannot be safely combined.
11. Expect the `check.lifecycle-transition-invalid` diagnostic; it is a known tooling defect (backlog `tk1gqo`) and must not be "fixed" by reordering the history.
12. On completion, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <AGENT/MODEL> --message <SUMMARY> --apply`, and move the plan to `.aw/records/plans/executed/` with `- Status: executed`. The lifecycle transition is a POST-gate step, never an E-item.
