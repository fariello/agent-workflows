# IPD: Add aw layout CLI command and workspace health check rule

- Date: 2026-09-01
- Kind: child
- Concern: Workspace layout inspection needs a dedicated CLI verb (`aw layout`) and workspace health check in `aw check` per Spec kw5y2s.
- Scope: Add `aw layout` command (supporting `--json`, `--schema`) to `agent_workflows/cli.py`, add layout consistency checking to `check_engine.py` / `doctor.py`, and author unit tests in `tests/test_cli_layout.py`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/doctor.py, tests/test_cli_layout.py
- Item-Dependencies: executed:hauwqh
- Status: to-review
- Set: wslayout
- Order: 5
- Highest E allocated: 03
- Author: antigravity
- Id: 30jug9
- From-Spec: kw5y2s

## Workflow history

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

- [ ] E-01 Add `layout` subcommand to `agent_workflows/cli.py` supporting `--json`, `--schema`, and formatted human inspection.
  - Depends on: none
  - Expected outcome: `aw layout` command works in human and agent modes.
  - Execution state: pending
  - Set-level prerequisite: `hauwqh` must be executed first; see `- Item-Dependencies:` in the metadata.
  - NAMING MUST BE JUSTIFIED BEFORE IMPLEMENTING (plan-review PR-008). `aw layout` sits one word from the
    EXISTING `aw migrate-layout`, a transactional physical-layout MIGRATION, so the two are adjacent in
    tab completion while one is read-only and the other moves files. It also overlaps `aw context`, which
    ALREADY prints the four resolved logical roots, and `aw path <root>`, which already prints one
    resolved path for scripting (`aw context --json` emits `data.logical_roots` plus
    `data.effective_framework_version`).
  - Therefore the executor MUST record, in this plan, ONE of: (a) keep `aw layout` as a new top-level
    read-only noun, stating why `aw context` cannot carry it (the likely answer: this emits the record
    CLASS vocabulary and the schema, which `context` does not model); or (b) implement it as
    `aw context --layout` / a `layout` subcommand of an existing noun. Do not choose by default. The
    project prefers existing canonical mechanisms, so option (a) needs the stated reason.
  - Whichever is chosen, the human output must make the read-only nature obvious so it is never confused
    with `aw migrate-layout`.
  - Per the maintainer's OQ-2 ruling the emitted `layout.json` is GITIGNORED, so this command MUST work
    from the in-process model even when no emitted file exists (a fresh clone has none until an install
    runs). It must not require the file to be present.

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

## Project conventions discovered (Step 0)

- `agent_workflows/cli.py`: main CLI surface.
- `agent_workflows/check_engine.py`: consistency check engine.

## Findings

- `aw layout` provides direct stdout inspection without requiring non-Python tools to parse the filesystem if they choose to shell out.
- The verb name is NOT yet settled: `aw layout` is adjacent to the existing destructive-sounding `aw migrate-layout` and overlaps `aw context` (which already emits the four resolved logical roots) and `aw path`. E-01 must record the naming justification or move the surface under an existing noun (plan-review PR-008).
- Because the emitted `layout.json` is GITIGNORED per the maintainer's OQ-2 ruling, this Order carries extra weight: `aw check`'s presence/drift rule is the ONLY loud-failure backstop for an absent or stale emitted file, since git will never show a diff for it.

## Proposed changes (ordered, validatable)

1. Add `layout` parser and runner in `agent_workflows/cli.py` (E-01).
2. Add check rule in `check_engine.py` (E-02).
3. Add unit test suite in `tests/test_cli_layout.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_cli_layout.py` passing (NEW file created by E-03), with actual output pasted.
- Full repository test suite passing bare (`python3 -m pytest`), `N passed` line pasted, zero regressions.
- `aw check reviews` accepted (net-new) AND `aw check roadmaps` still accepted, proving the union vocabulary added a type without removing one.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 6.2.

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
