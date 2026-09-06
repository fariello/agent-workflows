# IPD: Add aw layout CLI command and workspace health check rule

- Date: 2026-09-01
- Kind: child
- Concern: Workspace layout inspection needs a dedicated CLI verb (`aw layout`) and workspace health check in `aw check` per Spec kw5y2s.
- Scope: Add `aw layout` command (supporting `--json`, `--schema`) to `agent_workflows/cli.py`, add layout consistency checking to `check_engine.py` / `doctor.py`, and author unit tests in `tests/test_cli_layout.py`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/doctor.py, agent_workflows/command_surface.py, tests/conformance_matrix.py, tests/test_cli_layout.py
- Item-Dependencies: executed:hauwqh,executed:zvk796
- Status: executed
- Readiness: go-pending-approval
- Set: wslayout
- Order: 5
- Highest E allocated: 03
- Author: antigravity
- Id: 30jug9
- From-Spec: kw5y2s

## Workflow history
- 2026-09-06 executed (aw oc run): aw oc run self-finalize: 30jug9 verified (set wslayout, attempt 1).
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 6: APPROVE WITH REVISIONS APPLIED; PR-301; GO - PENDING HUMAN APPROVAL. Verified at HEAD `16777ccc`, tree clean, plan committed and unchanged. Lint conforming at both checkpoints. CLAIMS RE-MEASURED LIVE: `aw layout` genuinely does NOT exist (argparse rejects it and lists every real verb), so E-01 is correctly net-new; `aw migrate-layout` DOES exist, so F-2's adjacency concern is real and its read-only-vs-transactional distinction is the right resolution; and `aw check reviews` still errors with "unknown artifact type 'reviews'", which is precisely the fence E-03 must assert flips to accepted while `aw check roadmaps` stays accepted. THE FINDING (PR-301, LOW, fixed): the `cli.py` contention count was stale - the plan says 13 pending plans declare it, measured 10 at this HEAD, the drop being siblings that executed. Corrected in F-5 and the Scope check, with the point made explicitly that any number written in a plan is a snapshot and the re-measurement clause is what actually protects the edit. Its dependency edge (`executed:hauwqh,executed:zvk796`) is correct and non-obvious: it needs `hauwqh` for emission behavior and `zvk796` for the `reviews` noun V-03 asserts. No open questions.
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

- [x] E-01 Add the read-only `layout` command across `agent_workflows/cli.py` and `agent_workflows/command_surface.py`, supporting `--json`, `--schema`, agent output, and formatted human inspection.
  - Depends on: none
  - Expected outcome: `aw layout` command works in human and agent modes.
  - Execution state: performed
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

- [x] E-02 Add layout verification rule (`check.system-layout-missing` / `check.system-layout-drift`) to `agent_workflows/check_engine.py` and `doctor.py`.
  - Depends on: E-01
  - Expected outcome: `aw check` verifies that installed `.aw/system/layout.json` exists and is valid.
  - Execution state: performed
  - SEVERITY CHOSEN (DECISION 05-30jug9-D1): both rules are `warning`, and both are SILENT unless
    the install marker `.aw/system/VERSION` is present. State (a) no marker -> no finding; state (b)
    marker + document absent -> `check.system-layout-missing`; state (c) marker + document present
    but stale/unparseable/schema-invalid -> `check.system-layout-drift`. `warning` is still LOUD:
    `artifact_core.drift_exit_code` fails the gate for anything that is not `info`, so `aw check`
    exits 1. Gating on the marker (rather than weakening severity) is what keeps a fresh clone
    passing.
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

- [x] E-03 Author unit tests in `tests/test_cli_layout.py` (NEW FILE; it does not exist today) covering `aw layout`, `aw layout --json`, and `aw layout --schema`.
  - Depends on: E-01, E-02
  - Expected outcome: `pytest tests/test_cli_layout.py` passes cleanly.
  - Execution state: performed
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
| F-5 | **Concurrent scope collision on `agent_workflows/cli.py`.** RE-MEASURED AT EXECUTION 2026-09-06: **4** pending plans declare it, not 10 and not the original 13. Two of the four are this Set's own files (this plan and its orchestrator `rh5tt6`), so only **2** are genuinely external (`ygzq71` and `p7xhhm`, both Set `runprofile`). The figure moved twice, which is the point the re-measurement clause makes: any number written in a plan is a snapshot, and the clause is what protects the edit. No conflict arose - the edits landed cleanly and the pre-existing undeclared `oc profile *` leaves (another Set's in-flight work) were left untouched. | `grep -l 'agent_workflows/cli.py' .aw/records/plans/pending/*.ipd.md \| wc -l` -> 4 at HEAD 90aeb99c (was 10 at 16777ccc, 13 when first written) |
| F-6 | **The new check rule fires on THIS repository, and that is correct.** This worktree carries the tracked install marker `.aw/system/VERSION` and no `.aw/system/layout.json` (gitignored per spec 2.3), which is exactly the state (b) the rule reports. `aw check` therefore gains one class, 15 findings/4 classes -> 16/5. It is a TRUE POSITIVE, not a regression: exempting a source checkout would blind the rule in the one repo this project's maintainers and CI use, and would make it untestable in place. No fail-closed CI gate observes it (none runs bare `aw check` or `aw doctor`), and the remedy (`aw install`) is proven to clear it. | DECISION 05-30jug9-D5; before/after `aw check --agent` class counts; `.github/workflows/tests.yml:142-170`; `emit_layout_artifacts` on a copy -> clean |
| F-7 | **`aw check reviews` was ALREADY accepted before this plan ran.** The plan's premise that it "errors today with unknown artifact type" was true when written and is now stale: prerequisite `zvk796` (Order 02, a declared `Item-Dependencies` edge of this plan) made `reviews` a type noun. V-03's assertions are therefore regression FENCES inherited from Order 02, not behavior introduced here, and are recorded as such rather than claimed as new. | DECISION 05-30jug9-D4; `aw check reviews --agent` -> `outcome: conforms, exit 0` at HEAD 90aeb99c; `artifact_types.py:37` |

## Proposed changes (ordered, validatable)

1. Add `layout` parser and runner in `agent_workflows/cli.py` (E-01).
2. Add check rules in `check_engine.py` and integrate with `doctor.py` (E-02).
3. Author unit test suite in `tests/test_cli_layout.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none. `tests/test_cli_layout.py`, `agent_workflows/command_surface.py`, and `tests/conformance_matrix.py` are in `Scope-Paths` because every new read-only CLI leaf must declare and exercise the output contract.
- Concurrent-scope collision (PR-010): RE-MEASURED AT EXECUTION (2026-09-06, HEAD `90aeb99c`): `agent_workflows/cli.py` is declared by **4** pending plans, of which only 2 are external to this Set (`ygzq71`, `p7xhhm`; the other two are this plan and its orchestrator). Earlier snapshots said 10 (2026-09-04) and 13 (as first written); both were accurate when written. No concurrent edit conflicted. The five undeclared `oc profile *` parser leaves visible in the conformance matrix are ANOTHER Set's in-flight work and were deliberately left untouched.
- Actual files changed: `agent_workflows/cli.py`, `agent_workflows/check_engine.py`, `agent_workflows/doctor.py`, `agent_workflows/command_surface.py`, `tests/conformance_matrix.py`, `tests/test_cli_layout.py` (new). Every one is a declared `Scope-Paths` entry; no declared path went unmodified, so no `--scope-ack` is needed, and no out-of-scope edit was made, so no `--scope-reason` is needed.

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

- [x] V-01 validates E-01
  - Required evidence: `aw layout --json` and `aw layout --schema` emit expected JSON documents; paste
    both outputs, and confirm the `--json` document validates against the `--schema` document.
  - PLUS the recorded naming decision (PR-008): quote the justification written into E-01, naming which
    option was chosen and why `aw context` could not carry it. An unrecorded default is a FAILED
    validation.
  - PLUS the no-emitted-file case (OQ-2 consequence): run the command in a workspace where
    `.aw/system/layout.json` does NOT exist and paste output proving it still succeeds from the
    in-process model.
  - Observed evidence: `aw layout --json` and `aw layout --schema` both exit 0 and their documents
    cross-validate (`jsonschema.validate: PASS` plus a stdlib structural check in the committed test);
    the naming decision is recorded in `cli.py` and asserted by a test; the no-emitted-file case
    succeeds from the in-process model (this worktree IS that case); read-only is proven by a
    byte-level filesystem snapshot across all four output modes. Detail follows.
    - `aw layout` exists as a NET-NEW verb. Before this plan (unmodified HEAD `90aeb99c`),
      `python3 -m agent_workflows layout` printed
      `agent-workflows: error: argument <command>: invalid choice: 'layout' (choose from 'install',
      'setup', ..., 'migrate-layout', ...)`. It now resolves.
    - `aw layout --json` (exit 0), abridged at the record-class list for length; the full document is
      reproduced by the command:

      ```json
      {
        "schema": "aw.agent/v1",
        "command": "layout",
        "status": "clean",
        "exit_code": 0,
        "summary": "workspace layout model (in-process)",
        "verified": true,
        "complete": true,
        "diagnostics": [],
        "changes": [],
        "evidence": [
          {"key": "record_classes", "value": 11, "status": "verified", "detail": ""},
          {"key": "logical_roots", "value": 4, "status": "verified", "detail": ""}
        ],
        "next_actions": [],
        "data": {
          "layout": {
            "schema_version": 1,
            "framework_version": "1.2.1",
            "logical_roots": {
              "system": ".aw/system",
              "config": ".aw/config",
              "state": ".aw/state",
              "records": ".aw/records"
            },
            "record_classes": {
              "plans": {
                "subpath": "plans",
                "pattern": "*.ipd.md",
                "description": "Implementation Plan Documents (IPDs)",
                "lifecycle_subdirs": ["pending", "executed", "superseded", "not-executed", "reusable"],
                "aliases": ["plan"]
              },
              "specs": {"subpath": "specs", "pattern": "*.spec.md", "description": "Architectural specifications and proposals", "aliases": ["spec"]}
            },
            "state_classes": {"durable": {"install": "durable/install.json"}, "runtime": {"transactions": "runtime/transactions"}},
            "traversal_exclusions": [".git", ".system_generated", "__pycache__", "runs", "scratch", "temp", "tmp"]
          },
          "source": "in-process",
          "repo_root": "<repo>"
        }
      }
      ```

    - `aw layout --schema` (exit 0), head:

      ```json
      {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "AgentWorkflowsLayout",
        "type": "object",
        "required": [
          "schema_version",
          "framework_version",
          "logical_roots",
          "record_classes",
          "state_classes",
          "traversal_exclusions"
        ],
        "properties": {
          "schema_version": {"type": "integer", "enum": [1]},
          "framework_version": {"type": "string"},
      ```

    - THE `--json` DOCUMENT VALIDATES AGAINST THE `--schema` DOCUMENT. Verified two ways. With the
      real validator (available in this environment, though NOT a project dependency):

      ```text
      jsonschema.validate: PASS
      all required keys present: ['schema_version', 'framework_version', 'logical_roots', 'record_classes', 'state_classes', 'traversal_exclusions']
      schema_version in enum: OK
      logical_roots required subset: OK
      additionalProperties:false satisfied: OK
      ```

      And structurally in the committed test (`test_the_json_document_validates_against_the_emitted_schema`),
      which uses only the stdlib because `jsonschema` is in neither the runtime deps nor the `[test]`
      extra, so a test importing it would pass or fail on the environment rather than on the code.
    - THE NAMING DECISION IS RECORDED IN CODE, not merely in this plan. `cli.py` `_DESCRIPTIONS["layout"]`
      and the `_run_layout` docstring both state the chosen option and the reason: `aw layout` exposes
      the RECORD-CLASS VOCABULARY and the JSON SCHEMA, neither of which `aw context` models
      (`aw context` reports resolved logical root PATHS; `aw path <root>` prints one resolved path for
      scripting), and it is distinguished from the adjacent TRANSACTIONAL `aw migrate-layout`. The
      committed test `test_help_text_states_the_read_only_nature` asserts the rendered `--help` carries
      both `READ-ONLY` and a pointer to `migrate-layout`, so the justification cannot silently rot.
    - THE NO-EMITTED-FILE CASE, which is the DEFAULT state of this very worktree
      (`.aw/system/layout.json` is gitignored per spec 2.3 and absent here). `aw layout` human output:

      ```text
      AW Workspace Layout Model
      INFO           Read-only inspection; nothing is written or moved.
      INFO           Schema version:    1
      INFO           Framework version: 1.2.1
      INFO           Source:            in-process model (no emitted .aw/system/layout.json; it is gitignored and written by 'aw install')
      ```

      And the machine-readable form reports `"source": "in-process"` with no `source_path` and no
      `emitted_error` (a plain absence is the EXPECTED state, so it is not surfaced as a problem).
      Exit 0 in both modes. The reverse direction is proven too: against a really-installed temporary
      repo, `aw layout --repo <tmp> --json` reports `"source": "emitted"` with
      `"source_path": "<tmp>/.aw/system/layout.json"`, and the test asserts the payload equals the
      file's own bytes-parsed content rather than a coincidentally-equal in-process render.
    - READ-ONLY IS PROVEN AGAINST THE FILESYSTEM, not asserted in prose:
      `test_no_workspace_file_changes_in_any_mode` snapshots every file's BYTES under an installed
      workspace, runs all four modes (human, `--json`, `--agent`, `--schema`), and asserts the
      snapshot is unchanged; `test_does_not_create_the_emitted_file_it_could_not_find` asserts the
      command does not helpfully write the document it failed to find.
    - Output-contract parity: `--agent` is ANSI-free with its record `exit` equal to the process
      return code; piped human output is plain; `--help` exits 0; an unknown flag exits 2; and
      `--schema --json` together exit 2 as a usage error (they name two different documents).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `aw check` includes the layout verification rule; paste output from THREE cases:
    (a) an installed workspace with a valid emitted file (clean), (b) an installed workspace with the
    file deleted (reports `check.system-layout-missing`), (c) a version-mismatched file (reports
    `check.system-layout-drift`).
  - PLUS the fresh-clone case: paste evidence that a repo with no AW workspace does NOT fail this rule,
    since the emitted file is gitignored and legitimately absent until an install runs.
  - Observed evidence: all four states verified against REAL installed temporary repositories -
    (a) clean -> no findings, (d) no AW workspace -> no findings (the fresh-clone guarantee),
    (b) document deleted -> `check.system-layout-missing` (warning), (c) version stale ->
    `check.system-layout-drift` (warning); the same four states verified end-to-end through
    `aw check`'s own sweep and through `aw doctor`; the one new class on this repo is a true
    positive reaching no fail-closed CI gate, with its remedy proven. Detail follows.
    - THE FOUR STATES, each against a REAL temporary repository built by a REAL `aw install` (not a
      hand-faked directory), showing the full enriched finding shape:

      ```text
      --- (a) installed + valid emitted file
         (no findings)
      --- (d) no AW workspace (fresh clone)
         (no findings)
      --- (b) installed, document DELETED
         rule=check.system-layout-missing severity=warning
         location=.aw/system/layout.json
         detail=installed workspace (version 1.2.1) has no emitted layout document; non-Python consumers cannot read the hierarchy until an install regenerates it
         observed='absent' required="present (emitted by 'aw install')"
         recovery=run 'aw install <tmp>' to regenerate the emitted layout document
      --- (c) installed, framework_version STALE
         rule=check.system-layout-drift severity=warning
         location=.aw/system/layout.json
         detail=emitted layout document is stale: framework_version '0.0.1-definitely-stale' does not match the installed VERSION ('1.2.1')
         observed='0.0.1-definitely-stale' required='1.2.1'
         recovery=run 'aw install <tmp>' to regenerate the emitted layout document
      ```

    - THE SAME FOUR STATES THROUGH `aw check`'s OWN SWEEP (`check_types(root, ["all"])`), proving the
      rule is WIRED and not merely implemented:

      ```text
      --- (a) installed + valid emitted    check_types(all) rules: (none)
      --- (d) no AW workspace              check_types(all) rules: (none)
      --- (b) document deleted             check_types(all) rules: ['check.system-layout-missing']
      --- (c) version stale                check_types(all) rules: ['check.system-layout-drift']
      ```

    - THE FRESH-CLONE GUARANTEE, stated as the falsifiable claim it is: case (d) has no
      `.aw/system/VERSION`, so the rule returns `[]`. This is the single `if` in
      `check_system_layout` that keeps `aw check` from failing on every fresh clone by design (the
      emitted files are gitignored, so EVERY fresh clone lacks them). The committed test
      `test_a_repo_with_no_aw_workspace_reports_nothing` is the only test that fails if that gate is
      deleted, which is precisely why it exists.
    - LIVE ON THIS REPOSITORY, `aw check --agent` before vs after. This worktree is state (b): it has
      the tracked install marker `.aw/system/VERSION` (1.2.1) and no `layout.json`.

      ```text
      BEFORE (unmodified HEAD 90aeb99c): outcome findings exit 1 findings 15
        check.from-backlog-dangling: 1
        check.from-backlog-gate-mismatch: 1
        check.lifecycle-transition-invalid: 5
        check.name-nonconformant: 8

      AFTER:                             outcome findings exit 1 findings 16
        check.from-backlog-dangling: 1
        check.from-backlog-gate-mismatch: 1
        check.lifecycle-transition-invalid: 5
        check.name-nonconformant: 8
        check.system-layout-missing: 1
      ```

      THE DELTA IS EXACTLY THE NEW RULE, and it is a TRUE POSITIVE, not a regression. See
      DECISION 05-30jug9-D5 for why it is neither suppressed nor exempted for a source checkout:
      exempting the source checkout would blind the rule in the one repository this project's
      maintainers and CI actually use, and would make it untestable in place. THE REMEDY IS PROVEN,
      on a copy rather than on the live worktree: `emit_layout_artifacts(<copy>)` takes
      `['check.system-layout-missing']` to `(clean)`.
    - NO FAIL-CLOSED GATE SEES IT, measured rather than assumed. `.github/workflows/tests.yml` gates
      on `aw check plans` (:155), `aw check releases` (:159), `aw specs check` (:142) and
      `aw attention --check` (:145); it never runs bare `aw check` or `aw doctor`. Because the rule
      rides ONLY the once-per-full-sweep `collisions` seam, each gated command is unaffected:
      `aw check plans` exit 1 with only the pre-existing `check.lifecycle-transition-invalid`,
      `aw check releases` exit 0, `aw attention --check` byte-identical to its unmodified-HEAD
      output (same single pre-existing `attention.duplicate-id`).
    - SEVERITY IS A DECISION, NOT A DEFAULT. Both rules are registered in `RULE_REGISTRY` as
      `warning` / `repository` / `deterministic`; an UNREGISTERED rule would silently inherit
      `error` from `_DEFAULT_RULESPEC`. `warning` is still LOUD:
      `test_warning_severity_still_fails_the_gate` asserts `drift_exit_code` returns 1 for each,
      because only `info` is advisory.
    - `aw doctor` REPORTS THE SAME FINDING from the SAME shared function (so the two surfaces cannot
      diverge): `probe_environment(<repo with deleted document>)` yields
      `check.system-layout-missing`, and yields neither rule on a clean installed workspace. Live on
      this repository, `aw doctor --agent` includes
      `LAYOUT RULE: check.system-layout-missing .aw/system/layout.json`.
    - THE RULE IS READ-ONLY AND NOT PER-TYPE: `test_the_rule_is_read_only` byte-snapshots the
      workspace across a rule run; `test_the_rule_does_not_fire_per_record_type` asserts exactly ONE
      finding from the full sweep (not eleven duplicates) and NONE from `aw check plans`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_cli_layout.py` passes cleanly with the ACTUAL runner
    output pasted, and the NEW file is present in the commit.
  - PLUS the union-vocabulary surface proof (PR-001): paste `aw check reviews` succeeding (it errors
    today with "unknown artifact type 'reviews'") and `aw check roadmaps` STILL succeeding, proving the
    Set added a type without removing one.
  - PLUS the BARE FULL SUITE: `python3 -m pytest` (bare) with the `N passed` summary line pasted and zero
    regressions, as this is the Set's final child and the last gate before the orchestrator's E-02.
  - Observed evidence: `tests/test_cli_layout.py` (new file) passes `41 passed in 18.05s`; the BARE
    full suite goes from a re-measured baseline `35 failed, 5079 passed` to `35 failed, 5120 passed`
    with the sorted FAILED sets byte-identical under `diff` (zero regressions, +41 = the new tests);
    `aw check reviews` exits 0 and `aw check roadmaps` is still an accepted noun (exit 1 on a
    pre-existing NAME finding, not a rejection); `aw sanitize --agent` is clean. Detail follows.
    - THE NEW FILE'S OWN SUITE. `tests/test_cli_layout.py` did not exist before this plan and is
      created by it. Run with the configured defaults cleared so the per-test counts are visible
      (`-o addopts=""`), which the AGENTS.md contract names as the correct way to narrow a run:

      ```text
      $ python3 -m pytest tests/test_cli_layout.py -o addopts="" -q
      .........................................                                [100%]
      41 passed in 18.05s
      ```

    - THE BARE FULL SUITE, run exactly as the contract requires (`python3 -m pytest`, no added
      flags), with the baseline RE-MEASURED on unmodified HEAD `90aeb99c` immediately before the work
      rather than quoted from a review round:

      ```text
      BASELINE (unmodified HEAD 90aeb99c):
      35 failed, 5079 passed, 3 skipped, 4 xfailed in 102.81s (0:01:42)

      AFTER:
      35 failed, 5120 passed, 3 skipped, 4 xfailed in 106.32s (0:01:46)
      ```

      ZERO REGRESSIONS, and proven by set comparison rather than by counts: the sorted `FAILED` lines
      were captured before and after and `diff` reports them BYTE-IDENTICAL (35 both times, no line
      added and none removed). The `+41 passed` delta is exactly the new file's 41 tests. The 35
      pre-existing failures are unrelated to this plan and concentrate in
      `tests/test_run_viewer.py` (14), `tests/test_oc_runipd.py` (7),
      `tests/test_agy_runipd_cli.py` (6), `tests/test_next_ordering.py` (4),
      `tests/test_ipd_lifecycle_cli.py` (2), plus one each in
      `tests/test_novalnomerge_integration.py` and `tests/test_worker_role_refusal.py`; none touch
      `cli.py`'s layout verb, `check_engine.py`'s layout rule, or `doctor.py`'s probe.
    - THE UNION-VOCABULARY FENCE, both nouns live:

      ```text
      $ python3 -m agent_workflows check reviews --agent
      {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"reviews","findings":0,"evidence":["inventory","rules"],"next":null}
      EXIT=0

      $ python3 -m agent_workflows check roadmaps --agent
      {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"roadmaps","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":".aw/records/roadmaps/20260712-1426-agent-workflows-bounded-iteration-skills-roadmap-for-consideration.roadmap.md","rule":"check.name-nonconformant"}],"next":"run 'aw rename roadmaps ...'"}
      EXIT=1
      ```

      BOTH ARE ACCEPTED NOUNS. `roadmaps` exits 1 on a pre-existing NAME finding, which is a DOMAIN
      result, categorically different from the `outcome: error, exit 2, unknown artifact type`
      rejection an unaccepted noun produces; the closed-vocabulary half is proven separately by
      `test_an_unknown_type_is_still_rejected` (`aw check definitely-not-a-type` -> exit 2 with
      `unknown artifact type` on the human path).
      HONEST PROVENANCE (DECISION 05-30jug9-D4): `aw check reviews` is ALREADY accepted at this HEAD,
      delivered by this plan's declared dependency `zvk796` (Order 02), whose job was to source the
      CLI vocabulary from the layout model. The plan's "it errors today" wording was true when
      written and is now a stale snapshot. These assertions are therefore REGRESSION FENCES inherited
      from Order 02 rather than behavior introduced here, which is exactly the purpose the plan
      states for them ("a future edit that silently drops a live type fails here"). Nothing is
      claimed as newly added that was not.
    - VOCABULARY IDENTITY, not mere agreement: `test_both_types_are_in_the_cli_vocabulary` asserts
      `tuple(artifact_types.ARTIFACT_TYPES) == layout.build_default_layout().artifact_types()`, so the
      CLI surface and the model `aw layout` prints are the SAME vocabulary rather than two lists that
      happen to match today.
    - CONFORMANCE SUITE (`make test-all` scope). `python3 -m pytest tests/test_cli_conformance_matrix.py`
      reports `2 failed, 9 passed`, and the two failures are PRE-EXISTING and NOT this plan's: they are
      the five undeclared `oc profile *` leaves belonging to another Set in flight. Confirmed by
      running the same file at unmodified HEAD (`git stash`), which reports the SAME
      `2 failed, 9 passed` with the same two test ids. The new `layout` leaf passes every live scenario
      gate in that file (ANSI-free agent stream, agent `exit` equal to the process rc, plain non-TTY
      and NO_COLOR output, `--help` exit 0, bad-flag exit 2, human/agent fact parity).
    - `aw sanitize --agent`:

      ```text
      {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
      EXIT=0
      ```
  - Result: pass

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
