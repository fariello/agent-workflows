# IPD: Install-time layout.json and schema emission in engine.py

- Date: 2026-09-01
- Kind: child
- Concern: Non-Python tools require a machine-readable `.aw/system/layout.json` and `.aw/system/layout.schema.json` in the target repository. Emitting them during repository installation ensures zero git drift and version alignment with `.aw/system/VERSION`.
- Scope: Update `agent_workflows/engine.py` to write `.aw/system/layout.json` and `.aw/system/layout.schema.json` during `engine.install_into_repo()` (the only emission site; `/aw setup-repo` inherits it transitively), gitignore them via the framework-owned `.aw/.gitignore`, and add integration test coverage in `tests/test_engine_install.py`.
- Scope-Paths: agent_workflows/engine.py, .aw/.gitignore, tests/test_engine_install.py
- Item-Dependencies: executed:wpu5zu
- Status: to-review
- Readiness: no-go
- Set: wslayout
- Order: 4
- Highest E allocated: 03
- Author: antigravity
- Id: hauwqh
- From-Spec: kw5y2s

## Workflow history
- 2026-09-04 to-review (aw set): Applied deterministic plan-review repairs; controlling spec kw5y2s awaits renewed human approval.

- 2026-09-04 reviewed (antigravity): /aw plan-review-long: APPROVE WITH REVISIONS APPLIED; PR-019, PR-021, PR-022, PR-023 fixed (corrected engine function name to install_into_repo, added eleven-clause execution contract, structured findings evidence table, conventions, bare-suite validation with baseline re-measurement, and readiness).
- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - PR-002 (tests/test_engine_install.py and tests/test_setup_repo_cli.py do not exist), PR-003 (`aw setup-repo` is not a CLI verb), PR-004 (trackedness of emitted layout.json unstated), PR-007.
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).
- 2026-09-01 to-review (aw set): plan-review PR-007: metadata now matches the orchestrator sequence table

## Goal

Ensure `engine.install_into_repo()` bakes `.aw/system/layout.json` and `.aw/system/layout.schema.json` into target workspaces alongside `.aw/system/VERSION` (and `/aw setup-repo` inherits it transitively).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Engine Install Integration

- [ ] E-01 Update `agent_workflows/engine.py` (`install_into_repo`) to call `layout.build_default_layout().to_json(framework_version)` and `layout.build_default_layout().to_schema()` and write `.aw/system/layout.json` and `.aw/system/layout.schema.json` during installation.
  - Depends on: none
  - Expected outcome: Target repository `.aw/system/` directory receives layout.json and schema.
  - Execution state: pending
  - Set-level prerequisite: `wpu5zu` must be executed first; see `- Item-Dependencies:` in the metadata.
  - THE ONLY EMISSION SITE IS `engine.install_into_repo()` (plan-review PR-003, PR-021). `/aw setup-repo` (alias
    `/setup-repo`) is an AGENT SLASH-COMMAND backed by a workflow BODY
    (`.aw/system/workflows/setup-repo/setup-repo.md`), NOT a CLI verb and NOT a Python entry point, so it
    has no call site to wire. The order is the REVERSE of what this plan originally assumed: `aw install`
    runs FIRST and then RECOMMENDS `/setup-repo` as a follow-up conformance pass
    (`agent_workflows/engine.py:3581-3597`, "NEXT STEP ... run /setup-repo"). `/aw setup-repo` therefore
    inherits emission transitively at zero cost. `aw update` is not a verb either; `aw install` is the
    idempotent update path. Do NOT add emission code to the workflow body.
  - Write mode `0o644`, deterministic byte output (stable key order) so a re-install of the same version
    is a no-op rather than a rewrite.

### Task group 2: Installation Verification Tests

- [ ] E-02 Add the `.aw/.gitignore` entries so the emitted layout artifacts are never committed, per the maintainer's OQ-2 ruling.
  - Depends on: E-01
  - Expected outcome: `.aw/.gitignore` carries `system/layout.json` and `system/layout.schema.json`, and a freshly installed repo shows neither file in `git status`.
  - Execution state: pending
  - MAINTAINER RULING 2026-09-01 (plan-review PR-004 / OQ-2): the emitted files are GITIGNORED, via a
    `.gitignore` INSIDE the `.aw/` directory. This matches the `ila6vl` decision on generated manifests
    and this spec's own anti-drift rationale (committing generated output would defeat the reason
    install-time emission exists).
  - USE THE EXISTING FRAMEWORK-OWNED FILE, do not create a new mechanism: `.aw/.gitignore` already
    exists and already carries exactly this convention for four other generated/box-local paths
    (`.aw/.gitignore:1-15`), and its header states it "lives inside the framework-owned `.aw/` tree; it
    is NOT the user's root `.gitignore`". Add `system/layout.json` and `system/layout.schema.json`
    (paths are relative to `.aw/`), with a one-line comment naming this plan, in the same style as the
    existing entries. The installer MUST NEVER touch the user's root `.gitignore`.
  - The installer must ensure the entries exist idempotently (no duplicate lines on re-install) for
    repos whose `.aw/.gitignore` predates this change.

- [ ] E-03 Create `tests/test_engine_install.py` verifying that fresh and updated installs emit valid, gitignored `layout.json` and `layout.schema.json`.
  - Depends on: E-01, E-02
  - Expected outcome: Test suite validates install-time file generation, schema validity, and gitignored status.
  - Execution state: pending
  - CORRECTED (plan-review PR-002): `tests/test_engine_install.py` DOES NOT EXIST at review time, so
    this is a CREATE, not an edit. `tests/test_setup_repo_cli.py` also does not exist and is DROPPED
    from scope: per PR-003 there is no `setup-repo` CLI surface to test.
  - Must assert, in a temporary repo: both files are written; `layout.json` validates against the
    emitted `layout.schema.json`; `framework_version` matches the installed `.aw/system/VERSION`; a
    second install of the same version rewrites nothing (determinism); and `git status --porcelain`
    shows NEITHER file, proving the E-02 ignore actually takes effect.

## Project conventions discovered (Step 0)

- `agent_workflows/engine.py`: primary workspace installer (`engine.install_into_repo`, lines 5420-5560).
- `.aw/.gitignore`: framework-owned ignore file; header specifies it lives inside the `.aw/` tree and the user's root `.gitignore` is never touched.
- Controlling spec `kw5y2s` Section 6.1 is `to-review` after its maintainer-directed API terminology correction; do not execute until renewed human approval restores the gate. Its GITIGNORED emission ruling and `engine.install_into_repo()` sole-emission ruling remain unchanged.
- Emitted files: `.aw/system/layout.json` and `.aw/system/layout.schema.json` mode `0o644`, with deterministic byte serialization (stable keys) so re-install is a no-op.
- Python 3.9 is the floor (`pyproject.toml:12`).

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **`engine.install_into_repo()` in `engine.py` is the sole emission site.** `/aw setup-repo` is an agent slash-command backed by a workflow body with no Python call site, and inherits emission transitively without code of its own. | `agent_workflows/engine.py:3581-3597,5420-5560`; workflow index. |
| F-2 | **The emitted layout artifacts are gitignored via `.aw/.gitignore`.** Avoids git churn and maintains parity with `ila6vl` manifest ruling; user's root `.gitignore` remains untouched. | `.aw/.gitignore:1-16`; maintainer ruling on OQ-02. |
| F-3 | **`tests/test_engine_install.py` is newly created by this plan.** Asserts install-time generation, schema validity, and gitignore enforcement in a temporary repo. `tests/test_setup_repo_cli.py` was dropped because no such CLI surface exists. | E-03 / V-03 notes; file verified absent before execution. |
| F-4 | **Deterministic serialization is required.** Re-running `install_into_repo` on an unchanged version must leave the emitted files byte-identical (no rewrites or timestamp drift). | E-01 / V-01 notes. |
| F-5 | **Concurrent scope must be measured at execution time.** The prior `6knsrx` example is superseded; inspect current pending declarations for `engine.py` immediately before editing. | Current pending-plan board. |

## Proposed changes (ordered, validatable)

1. Wire layout emission in `agent_workflows/engine.py` `install_into_repo` (E-01).
2. Add `.aw/.gitignore` entries (E-02).
3. Author integration tests in `tests/test_engine_install.py` (E-03).

## Deferred / out of scope (with reason)

- CLI verb `aw layout` is in Order 05 (30jug9).

## Scope check

- Over-scope: none.
- Under-scope: none. `tests/test_engine_install.py` is newly created by E-03 and is in `Scope-Paths`.
- Concurrent-scope collision: the prior `6knsrx` example is superseded. Re-measure current pending declarations immediately before execution.

## Required tests / validation

- `python3 -m pytest tests/test_engine_install.py` passing (NEW file created by E-03), with actual output pasted.
- Bare full suite `python3 -m pytest` from the PRIMARY checkout, with baseline re-measured on unmodified HEAD at execution time.
- `git check-ignore -v` confirming both emitted artifacts are ignored via `.aw/.gitignore`.
- NOTE: `tests/test_setup_repo_cli.py` was REMOVED from scope (plan-review PR-002/PR-003): it does not exist and there is no `setup-repo` CLI surface to test.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 6.1. Spec is `approved`; do NOT edit it.
- No user-facing documentation changes owned by this installer wiring.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: in a temporary repo, `engine.install_into_repo()` (via `aw install`) writes BOTH
    `.aw/system/layout.json` and `.aw/system/layout.schema.json` at mode `0o644`. Paste a directory
    listing showing both files and their mode, plus the emitted `framework_version` matching that repo's
    `.aw/system/VERSION`.
  - PLUS determinism: install twice at the same version and paste evidence the second run leaves both
    files byte-identical (e.g. matching `sha256sum` before and after).
  - PLUS the negative check for PR-003: confirm no emission code was added to
    `.aw/system/workflows/setup-repo/setup-repo.md` (it is a workflow body, not an entry point), e.g.
    paste `git diff --name-only` showing that path is untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `.aw/.gitignore` contains `system/layout.json` and `system/layout.schema.json`;
    paste the relevant lines of the file.
  - PLUS proof the ignore WORKS in a freshly installed temporary repo: paste
    `git status --porcelain` showing NEITHER emitted file appears, and
    `git check-ignore -v .aw/system/layout.json .aw/system/layout.schema.json` naming `.aw/.gitignore`
    as the source of the rule.
  - PLUS proof the user's ROOT `.gitignore` was NOT modified by the installer (paste `git diff --
    .gitignore` showing no change), since the ruling is explicit that only the framework-owned file is
    touched.
  - PLUS idempotency: re-run the install and paste evidence no duplicate lines were appended.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_engine_install.py` passes cleanly with the ACTUAL
    runner output pasted, and the NEW file is present in the commit.
  - PLUS the BARE FULL SUITE: `python3 -m pytest` (bare) with the `N passed` summary line pasted, zero
    regressions, since this plan changes the installer that every other install test depends on.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE EXTERNAL SPEC GATE IS REOPENED: controlling spec `kw5y2s` is `to-review` after the maintainer-directed API terminology correction. `ipd-lifecycle.md:16` blocks execution until renewed human approval is recorded.

Execution contract:

1. Human approval of this plan is required before execution. There are no unresolved blocking questions.
2. Serial prerequisite: `wpu5zu` (Order 01) MUST reach `executed` before starting this plan, as this plan imports `agent_workflows/layout.py`.
3. RE-MEASURE CONCURRENT SCOPE COLLISIONS IMMEDIATELY BEFORE EXECUTION: the prior `6knsrx` example is superseded, so inspect current pending declarations for `agent_workflows/engine.py`. If concurrent edits are in flight, verify mergeability before editing.
4. Emission site invariant: Wire emission solely into `engine.install_into_repo()`; do not add Python code to workflow bodies or non-existent verbs.
5. Gitignore invariant: Add entries only to `.aw/.gitignore`; never modify the target user's root `.gitignore`.
6. File mode and determinism: Write at mode `0o644` with stable key order.
7. Validation requires ACTUAL pasted runner output; never claim a pass without running the commands.
8. Shared checkout discipline: commit only files this plan changed, path-scoped. Verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged`. Never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
9. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`).
10. Scope fence: declared paths are `agent_workflows/engine.py`, `.aw/.gitignore`, and `tests/test_engine_install.py`. An out-of-scope edit requires `--scope-reason`, and an unmodified declared path requires `--scope-ack`. Do NOT stop over a scope question. DO stop and report if a concurrent-edit conflict cannot be safely combined.
11. Expect the `check.lifecycle-transition-invalid` diagnostic; it is a known tooling defect (backlog `tk1gqo`) and must not be "fixed" by reordering the history.
12. On completion, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <AGENT/MODEL> --message <SUMMARY> --apply`, and move the plan to `.aw/records/plans/executed/` with `- Status: executed`. The lifecycle transition is a POST-gate step, never an E-item.
