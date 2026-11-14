# Review findings: plan b3eilr

- Subject-Id: b3eilr
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `954ee61a3` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-217-b3eilr-generate-the-conforming-orchestrator-fixture-from-the-shared.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). The baseline consumer test suites passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_ipd_lint.py tests/test_ipd_schema.py` printed `103 passed in 62.25s (0:01:02)`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Single bullet from split | Added newest-first review history entry with verdict and findings PR-001..PR-005 | MD-15, Section 7.2 |
| `## Detailed Implementation Checklist` (E-32, E-34) | E-32 described writing once per test session under tempdir without noting import-time evaluation or xdist process isolation; E-34 used bare `rg -n "conforming-orchestrator"` | E-32 specifies `RecordBuilder.plan(kind="orchestrator", text_only=True, ...)` written to process-isolated temp file with `atexit` cleanup; E-34 specifies word-bounded `\bconforming-orchestrator\b` to avoid collisions with `nonconforming-orchestrator-rows` | PR-001, PR-003 |
| `## Project conventions discovered`, `## Findings` | Cites F-42; lacked notes on import-time binding of `CONFORMING_ORCHESTRATOR` and substring collisions | Added import-time evaluation convention and repository facts F-43 and F-44 | PR-001, PR-003 |
| `## Proposed changes` | Ordered list of 3 steps, no diagram | Ordered list of 4 steps plus Mermaid `flowchart TD` | PR-004 (Requirement 12b) |
| `## Validation and cross-check` (V-32, V-34) | V-32 cited `ipd_lint.lint_text` on file paths; V-34 cited bare `rg -n "conforming-orchestrator"` | V-32 cites `ipd_lint.lint_file` side by side for both paths; V-34 specifies word-bounded `\bconforming-orchestrator\b` | PR-002, PR-003 |
| `## Approval and execution gate` | Incomplete lifecycle transition; scope stop rather than narrow prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), declaration scope fence, and narrow safety stop if `tests/record_builder.py` is absent | PR-005 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Changes an internal test fixture helper constant (`support.CONFORMING_ORCHESTRATOR`) and deletes a test fixture (`tests/fixtures/conforming-orchestrator.md`); no public CLI, API, file format, or configuration contract changes.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact plan with 4 execution items (E-32..E-35) in 2 task groups across 2 work Scope-Paths (`tests/support.py` and `tests/fixtures/conforming-orchestrator.md`).
4. Yes. `- Scope-Paths:` explicitly declares all modified paths.
5. Yes. A defect in `tests/support.py`'s fixture generation (e.g. failure during import-time evaluation or cross-worker race conditions in `pytest-xdist`) could break test execution in `tests/test_ipd_lint.py` and `tests/test_ipd_schema.py`.

AW-TIER: standard

### Step R1

- Checked: `tests/support.py::CONFORMING_ORCHESTRATOR`; `tests/fixtures/conforming-orchestrator.md`; `tests/test_ipd_lint.py` (`IpdLintCliTests.EXITS`, `test_conforming_orchestrator_fixture_is_clean`, `test_agent_output_is_agent_v1_jsonl_no_prose`); `tests/test_ipd_schema.py::ORCH_IPD`; `agent_workflows/ipd_lifecycle.py::ROLLUP_REFUSED_NONCONFORMING_ROWS`; `tests/test_orchestrator_retirement.py`; and governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Section 6, Section 7 step 6).
- Verified that `CONFORMING_ORCHESTRATOR` and `ORCH_IPD` are referenced at module and class definition level in `tests/test_ipd_lint.py` and `tests/test_ipd_schema.py`, confirming they are evaluated at import time (PR-001).
- Verified that `tests/fixtures/conforming-orchestrator.md` contains the 12 canonical orchestrator H2 headings matching `ipd_authoring.build_skeleton(kind="orchestrator", ...)` and that both lint as `conforming` at `checkpoint="author"` (PR-001, PR-002).
- Verified that bare `rg -n "conforming-orchestrator"` matches `nonconforming-orchestrator-rows` in `ipd_lifecycle.py:5032` and `test_orchestrator_retirement.py:5401`, whereas word-bounded `\bconforming-orchestrator\b` targets only `tests/support.py:19` (PR-003).

### Step R2

- Checked: 1:1 bijection between E-32..E-35 and V-32..V-35; `- Scope-Paths:` completeness; `- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:j6o96i`; and verification reachability.
- Corrected V-32 to cite `ipd_lint.lint_file` rather than `ipd_lint.lint_text` because both targets are `Path` objects (PR-002).
- Bounded V-34 search pattern to `\bconforming-orchestrator\b` so the verification demand that no readers remain is cleanly reachable and falsifiable (PR-003).

### Step R3

- Checked: security, file operations, and temporary file isolation.
- Using a process-isolated temporary file path in `tempfile.gettempdir()` with `atexit` unlinking ensures test runs do not create permanent clutter or race between concurrent processes.

### Step R4

- Checked: conceptual density, right-sizing, anti-regression, and operability.
- The plan is well-sized (4 execution items, 2 work paths) with clean separation of generation (E-32), consumer verification (E-33), tracked fixture deletion (E-34), and gate validation (E-35).
- Generating the fixture via `RecordBuilder.plan(kind="orchestrator", text_only=True, ...)` reuses the canonical authoring scaffold generator (`ipd_authoring.build_skeleton`), ensuring changes to skeleton templates automatically propagate to the orchestrator test fixture.

### Step S5

- Checked: no unresolved open questions; OQ-01 is resolved. All five review decisions (D-1..D-5) are recorded and verified (`Reversible: yes`).

### Pass 2

- Re-read all revised sections of `b3eilr`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R1 / R2 / R4-A / R4-C | `.aw/records/plans/pending/20261109-metastore-217-b3eilr-generate-the-conforming-orchestrator-fixture-from-the-shared.ipd.md:38-42`; `tests/test_ipd_lint.py:1582`; `tests/test_ipd_schema.py:59` | `CONFORMING_ORCHESTRATOR` is bound at class/module definition time in both consumer test modules, and `RecordBuilder` requires `repo_root` unless `text_only=True` is used. An unspecified generation mechanism risks import-time failures, circular imports, or worker collision races under `pytest-xdist`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified in E-32 that `tests/support.py` generates the fixture via `RecordBuilder.plan(kind="orchestrator", text_only=True, ...)` to a process-isolated temporary file with `atexit` cleanup (very strong). |
| PR-002 | MEDIUM | IN-SCOPE | R2 / R4-E | `.aw/records/plans/pending/20261109-metastore-217-b3eilr-generate-the-conforming-orchestrator-fixture-from-the-shared.ipd.md:120-123`; `agent_workflows/ipd_lint.py:540-575` | V-32 required evidence demands calling `ipd_lint.lint_text` directly on file paths, which raises `AttributeError` or fails type checking because `lint_text` expects string content. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated V-32 required evidence to cite `ipd_lint.lint_file` side by side for both the generated path and the tracked fixture (very strong). |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R2 | `.aw/records/plans/pending/20261109-metastore-217-b3eilr-generate-the-conforming-orchestrator-fixture-from-the-shared.ipd.md:48-51,130-133`; `agent_workflows/ipd_lifecycle.py:5032`; `tests/test_orchestrator_retirement.py:5401` | Bare `rg -n "conforming-orchestrator"` matches unrelated constant `nonconforming-orchestrator-rows`, making the demand that `rg` show "no reader" unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed search pattern in E-34 and V-34 to word-bounded `\bconforming-orchestrator\b` (strong). |
| PR-004 | MEDIUM | IN-SCOPE | Proofreading / R6 | `.aw/records/plans/pending/20261109-metastore-217-b3eilr-generate-the-conforming-orchestrator-fixture-from-the-shared.ipd.md:81-86`; `.aw/system/workflows/technical-writing/technical-writing.md:40-46` | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` (strong). |
| PR-005 | MEDIUM | IN-SCOPE | Gate / Lifecycle | `.aw/records/plans/pending/20261109-metastore-217-b3eilr-generate-the-conforming-orchestrator-fixture-from-the-shared.ipd.md:140-153`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:33-46` | The gate lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`"), framed the scope fence as a stop directive rather than a declaration, and lacked a narrow safety stop for missing prerequisite modules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reconciled gate with standard execution contract, declaration scope fence, and narrow unsafe-condition prerequisite stop (strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `support.CONFORMING_ORCHESTRATOR` generate the fixture without requiring a git repository context or risking cross-process races? | Call `RecordBuilder.plan(kind="orchestrator", text_only=True, ...)` and write the string to a process-isolated temporary file in `tempfile.gettempdir()` with `atexit` cleanup | Call `RecordBuilder(repo_root).plan(...)` with a dummy directory (fails if `project_context` requires `.aw/`); share a single hardcoded temp file across processes (races under `pytest-xdist`); keep tracked fixture (violates `4sd62s` section 6) | `4sd62s` section 6; `tests/support.py::ready_plan_text`; `tests/record_builder.py` (`j6o96i` E-01/E-16) | yes |
| D-2 | Which lint function should V-32 cite for validating the generated orchestrator fixture against `tests/fixtures/conforming-orchestrator.md`? | Cite `ipd_lint.lint_file` side by side, expecting both to report `conforming` | Keep `ipd_lint.lint_text(path)` (fails because `lint_text` takes string content, not a `Path` object) | `tests/test_ipd_lint.py:537`; `agent_workflows/ipd_lint.py::lint_file` | yes |
| D-3 | How should E-34/V-34 search for references to `conforming-orchestrator` to ensure no consumers remain before deletion? | Use word-bounded pattern `\bconforming-orchestrator\b` | Bare substring `rg -n "conforming-orchestrator"` (matches unrelated symbol `nonconforming-orchestrator-rows` in `ipd_lifecycle.py` and `test_orchestrator_retirement.py`) | `tests/support.py::CONFORMING_ORCHESTRATOR`; `agent_workflows/ipd_lifecycle.py:5032`; `tests/test_orchestrator_retirement.py:5401` | yes |
| D-4 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in `Proposed changes` showing the generation, verification, deletion, and test-gate pipeline | No diagram (violates Requirement 12b and plan authoring prompt instruction); state diagram (less fitting for a sequential batch task) | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-5 | How should the execution gate specify scope fence declarations, safety stops, and lifecycle transition ownership? | State scope fence as a declaration with `--scope-reason` and `--scope-ack`, add narrow unsafe-condition stop for missing prerequisite `tests/record_builder.py`, and state conditional runner/executor finalize ownership with "never a hand `git mv`" | Omit safety stop or instruct executor to stop on out-of-scope edits (violates 2026-09-01 maintainer ruling); omit runner conditional ownership | `.aw/system/workflows/plan-review/steps/s7-finalize.md:37-46`; `AGENTS.md` "Agent execution contract" | yes |
