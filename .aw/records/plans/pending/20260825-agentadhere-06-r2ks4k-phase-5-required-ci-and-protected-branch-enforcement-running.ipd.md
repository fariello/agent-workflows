# IPD: Phase 5: required CI and protected-branch enforcement running the same policy engine

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 5 + section 7.8: required CI on a protected branch is the ONLY non-bypassable authority boundary rated "Very high" - a clean, remote environment running the same policy engine, validating committed artifacts, and blocking merge on findings, with branch protection that also protects the policy/workflow files themselves from being weakened without approval. CI already runs the test suite (`.github/workflows/tests.yml` `unittest` job) and a fail-closed `aw specs check` + `aw attention --check` gate (`attention-check` job); what is MISSING is a fail-closed CI invocation of the full phase-1 `aw check` engine over the remaining committed artifact types (plans, backlog, releases) and documented protected-branch enforcement of the required check + the policy/CI-definition files themselves.
- Scope: Add the required-CI + protected-branch DELTA on top of the existing CI (do NOT recreate what `tests.yml` already does): (1) extend the existing fail-closed CI gate so a clean, remote environment runs the SAME phase-1 `aw check` engine (machine-readable via `aw check --agent`/`--json`; there is NO `--format json` flag) over the committed workflow artifacts NOT yet gated (plans/backlog/releases conformance, scope, release gates), publishing machine-readable evidence and failing the job on any finding; REUSE the running test suite rather than duplicating it; (2) document/configure branch protection to REQUIRE the check and disallow ordinary bypass actors, and to protect the policy/hook/CI definition files from being weakened without approval (findings 7.8); (3) ensure the CI-run engine and the local `aw check` produce identical results (no divergence). This is the authoritative repository boundary; it does NOT attempt authority-invariant guarantees (external signing/push broker - deferred set). Should land LAST in the set so it gates on a stable engine.
- Scope-Paths: .github/, agent_workflows/check_engine.py, agent_workflows/cli.py, docs/, tests/
- Status: approved
- Set: agentadhere
- Order: 6
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: r2ks4k
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 approved (aw set): status set to approved

- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 `--format json` corrected to `--agent`/`--json`, PR-002 E-01 rescoped to EXTEND existing CI (tests.yml already runs the suite + specs/attention gate), PR-003 gate execution contract added, PR-004 V-01..V-03 concrete falsifiable evidence, PR-005 OQ-01 resolved (executor lands workflow+docs; human applies protection), PR-006 Status draft->reviewed, PR-007 split E-02 into branch-protection docs (E-02) + parity test (E-03)
- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Extend the existing CI so the required, fail-closed gate runs the same phase-1 `aw check` engine (via `--agent`/`--json`) over the committed artifact types not yet gated (plans/backlog/releases) alongside the already-running test suite, and document protected-branch enforcement that requires the check and protects the policy/hook/CI files themselves from being weakened without approval - the authoritative, non-bypassable repository boundary.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: CI gate over committed artifacts

- [ ] E-01 EXTEND the existing fail-closed CI gate (the `attention-check` job in `.github/workflows/tests.yml`, which already runs `aw specs check` + `aw attention --check --agent`) so a clean CI environment also runs the SAME phase-1 `aw check` engine over the committed artifact types NOT yet gated - `aw check plans`, `aw check backlog`, `aw check releases` (or `aw check all`) - emitting machine-readable evidence via `aw check --agent` (JSONL) / `--json` and FAILING the job on any finding. There is NO `aw check --format json` flag; use `--agent`/`--json`. Do NOT add a second test-run step: the `unittest` job already runs the full suite (`tests.yml:64`). Call the SHIPPED engine (`python -m agent_workflows check ...`), never a forked/inlined policy, so CI and local `aw check` cannot diverge.
  - Depends on: none
  - Expected outcome: on a tree with a seeded plan/backlog/release conformance violation the extended CI gate exits nonzero and blocks; on a clean tree it passes; the gate invokes the shipped `aw check` engine (no duplicated policy) and the test suite is not duplicated.
  - Execution state: pending

### Task group 2: branch-protection enforcement (documented)

- [ ] E-02 Document (and, as a human-gated admin action per OQ-01, configure) branch protection on the default branch that REQUIRES the extended CI gate as a required status check, disallows ordinary bypass actors, and protects the policy/hook/CI definition files (`.github/workflows/`, `agent_workflows/check_engine.py`, the hook definitions) from being weakened without approval (findings 7.8) - e.g. a required review / CODEOWNERS entry for those paths. The EXECUTOR lands only the in-repo artifacts (the docs in RELEASING.md/CONTRIBUTING.md/AGENTS.md and any CODEOWNERS file); ENABLING GitHub branch protection is a repo-admin action left to the human (OQ-01). Honestly state that branch protection is a remote/authority control the local toolkit cannot self-enforce.
  - Depends on: E-01
  - Expected outcome: the required-check + bypass + policy-file-protection policy is documented in the repo, and any in-repo enforcement artifact (CODEOWNERS) is present; the human step to enable protection is called out explicitly.
  - Execution state: pending

### Task group 3: CI/local parity

- [ ] E-03 Add a test/assertion that the CI-run gate and a local `aw check` invocation produce IDENTICAL findings on the same tree (no divergence), asserting the CI gate calls the same shipped `check_engine` entry point rather than a forked policy.
  - Depends on: E-01
  - Expected outcome: a parity test passes, proving CI and local `aw check` agree on the same rule ids/findings for the same tree, and that the CI gate invokes the shipped engine (grep/import proof of no fork).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The repo ALREADY has CI under `.github/workflows/`: `tests.yml` runs the full suite (`unittest` job, `tests.yml:64`), builds/imports the wheel (`wheel` job), runs the CLI output-conformance harness (`output-conformance` job), AND runs a fail-closed `aw specs check` + `aw attention --check --agent` gate (`attention-check` job, `tests.yml:109-132`). Plus `secret-scan.yml` and `local-leaks.yml`. This phase EXTENDS the existing fail-closed gate; it does NOT create a fresh workflow and MUST NOT duplicate the running test suite.
- `aw check` (`check_engine`) is the single engine the local hooks (phase 4) already call; CI must call the SAME one via the shipped CLI (`python -m agent_workflows check ...`, machine-readable with `--agent`/`--json`; there is NO `--format json` flag), never a forked policy.
- Missing gate: `aw check plans` / `aw check backlog` / `aw check releases` (plan/backlog/release conformance) is NOT yet run in CI - that is the concrete delta this phase adds.
- Findings 7.8: protect the workflow/policy/CI files themselves and disallow bypass actors; this is the "Very high" authority boundary for repository invariants. The repo has no CODEOWNERS and no documented branch-protection policy today.
- Enabling GitHub branch protection is a repo-admin action outside an executor's authority (OQ-01); the executor lands in-repo artifacts (docs + CODEOWNERS), the human enables protection.

## Findings

CI is the smallest change with the largest assurance gain precisely because it reuses the phase-1 engine and the existing fail-closed `attention-check` job; the real work is a one-line-scale extension of that gate to `aw check plans`/`backlog`/`releases` plus documented branch protection. The risk is divergence between CI and local, mitigated by a parity assertion (E-03), and overselling a local/docs control as an authority boundary, mitigated by the honesty note that branch protection is a remote control the human enables.

## Proposed changes (ordered, validatable)

1. `.github/workflows/tests.yml`: EXTEND the existing fail-closed `attention-check` gate to also run `aw check plans`/`backlog`/`releases` (or `aw check all`) via the shipped engine, failing on any finding; do NOT duplicate the test-run step.
2. Branch-protection docs (RELEASING.md/CONTRIBUTING.md/AGENTS.md) + optional CODEOWNERS for policy/CI files (require check, protect policy files, disallow bypass); the human enables GitHub protection (OQ-01).
3. `tests/`: parity between the CI-run gate and local `aw check` (same findings, shipped engine, no fork); seeded conformance violation fails, clean passes.

## Deferred / out of scope (with reason)

- Authority-invariant guarantees (external signing, push broker, remote transition service): deferred external-signing set; CI enforces repository invariants, not non-forgeable provenance.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- The extended CI gate fails on a seeded plan/backlog/release conformance violation and passes on a clean tree (paste the reproduced command result); it does not duplicate the test run.
- The CI-run gate and local `aw check` produce identical findings on the same tree, both from the shipped `check_engine` (parity, no fork).
- The branch-protection policy (required check, disallow bypass, protect policy/hook/CI files) is documented and any in-repo CODEOWNERS artifact is present; the human enables the remote protection (executor changes no remote settings).

## Spec / documentation sync

- Document the required CI gate + branch-protection policy in RELEASING.md / CONTRIBUTING.md / AGENTS.md as the authoritative boundary, honestly noting that enabling GitHub branch protection is a human repo-admin action and that CI does not provide authority-invariant provenance (deferred external-signing set).

## Open questions

### OQ-01: This child edits .github/ and branch protection - is that within an executor's authority, or a human-gated step?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED (split by boundary). Editing the in-repo CI workflow file (`.github/workflows/tests.yml`) is normal code an executor lands and validates like any other change (E-01). AUTHORING the branch-protection documentation and any in-repo enforcement artifact (a CODEOWNERS file) is also in-repo work the executor lands (E-02). ENABLING GitHub branch protection (required-status-check + bypass restrictions + policy-file protection settings) is a repo-ADMIN action on the remote that an executor cannot and must not perform; it is left to the human and called out explicitly in E-02 and the gate. The executor therefore lands workflow + docs + CODEOWNERS; the human applies remote protection. Not a blocker for execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: (a) paste the added/edited lines of `.github/workflows/tests.yml` showing the fail-closed step invoking `python -m agent_workflows check` over plans/backlog/releases (or `all`) with `--agent`/`--json` (and confirm NO second test-run step was added); (b) locally reproduce the CI gate: run the exact command against a tree with a SEEDED plan/backlog/release conformance violation and paste the nonzero exit + finding output; (c) run the same command against the clean tree and paste exit 0; (d) NO-FORK proof: paste the grep/inspection showing the CI step calls the shipped `agent_workflows check` entry point and defines no inlined/duplicated policy.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: (a) paste the added branch-protection documentation (from RELEASING.md/CONTRIBUTING.md/AGENTS.md) stating the required-check policy, the disallow-ordinary-bypass rule, and protection of the policy/hook/CI-definition files (findings 7.8); (b) paste any in-repo enforcement artifact added (e.g. `CODEOWNERS` entries covering `.github/workflows/`, `agent_workflows/check_engine.py`, and the hook files); (c) confirm the docs HONESTLY state that enabling GitHub branch protection is a repo-admin action the human performs and that it is a remote/authority control the local toolkit cannot self-enforce (paste the passage); (d) confirm NO remote settings were changed by the executor.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: (a) paste the parity test run showing the CI-run gate and a local `aw check` invocation produce the SAME findings (same rule ids) on the same tree; (b) paste the assertion/grep proving the CI gate calls the shipped `check_engine` entry point (no forked policy), so CI and local cannot diverge.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: three E-items, each a single focused pass with its own verification surface - E-01 (extend the CI fail-closed gate to run `aw check` over plans/backlog/releases), E-02 (branch-protection docs + CODEOWNERS, human enables remote protection), E-03 (CI/local parity test). All three center on the same shipped `check_engine` and the existing `attention-check` gate, so they form one cohesive child.

### Open questions resolved

- OQ-01 (is editing .github/ + branch protection within an executor's authority, or human-gated): RESOLVED (split by boundary) - the executor lands the in-repo CI workflow edit (E-01), the branch-protection docs, and any CODEOWNERS artifact (E-02); ENABLING GitHub branch protection on the remote is a repo-admin action left to the human and called out explicitly. Not a blocker.

### Execution contract

- Scope fence: touch ONLY the files in `Scope-Paths` - `.github/` (extend `tests.yml`; optionally add `CODEOWNERS`), `agent_workflows/check_engine.py` and `agent_workflows/cli.py` (only if a genuine gap in the shipped `aw check` surface is found), `docs/` and the named docs (RELEASING.md/CONTRIBUTING.md/AGENTS.md) for the branch-protection policy, and `tests/` for the parity test. Do NOT recreate what `tests.yml` already runs (the full suite, the specs/attention gate); EXTEND the existing fail-closed gate. Do NOT build the phase 2/3/4 layers. If the work seems to need files outside this fence, STOP and report.
- No-fork MUST: the CI gate MUST invoke the SHIPPED `aw check` engine (`python -m agent_workflows check ...`) so CI and local `aw check` come from the SAME `check_engine` and can never diverge (V-01d/V-03b prove it). Do NOT inline or fork policy in the workflow.
- Authority honesty (hard MUST): branch protection is a REMOTE/authority control the local toolkit cannot self-enforce; enabling it is a human repo-admin action. The docs and refusal/enforcement artifacts MUST say so. CI on a protected branch is the authoritative repository boundary; it does NOT provide authority-invariant provenance (deferred external-signing set). Do NOT present in-repo docs or a CODEOWNERS file as if they enforce protection by themselves.
- Honesty rule (hard MUST): when a V-item reports a CI gate / `aw check` / test run passed or failed, paste the ACTUAL runner/command output; never claim a result you did not run.
- Commit rule: commit ONLY this child's own changed files, path-scoped (`git commit -m <msg> -- <paths>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically). Because CI should land LAST in the set, finalize this child only after children 01-05 are executed and the engine is stable.
