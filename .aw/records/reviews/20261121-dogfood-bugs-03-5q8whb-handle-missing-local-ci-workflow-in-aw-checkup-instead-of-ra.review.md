# Review findings: ipd 5q8whb

- Subject-Id: 5q8whb
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `e29e38eb1af8c77ad5470d23e4fd78ce20bb03ea` in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261121-dogfood-bugs-03-5q8whb-handle-missing-local-ci-workflow-in-aw-checkup-instead-of-ra.ipd.md` was committed and clean at turn start, so no pre-review snapshot commit was needed. It is Order 3 of Set `dogfood-bugs` (orchestrator `p2zmjs`) and graduated from backlog `bj3x5x`. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0).

AW-TIER: standard

### Step T

1. Yes, minor: the user-visible `reason` text that `aw checkup`, `aw attention`, and `aw doctor` display changes. No CLI flag, schema field, or status value changes.
2. No: the change adds no permission, credential, or external call; it removes a `gh` call.
3. No: the plan held 3 E-items (5 after review) in one module plus tests and docs.
4. Yes: `- Scope-Paths:` is present. Review added `tests/test_checkup.py`, `README.md`, and `CHANGELOG.md`.
5. Low: the status stays `UNKNOWN`, and `runner_shared.decide_red_ci_gate` treats `UNKNOWN` as warn-only, so no gate decision changes.

`AW-TIER: standard`

### Step R1

- Checked: `agent_workflows/checkup.py::read_ci_status` (196-373; `wf`/`br` resolved at 210-211, `gh` command built at 213, `FileNotFoundError` reason `gh: command not found` at 236), `CIRunResult` (117-127), `CiHealth`, `perform_checkup` (459, `preserve_failing_on_unknown` at 518), `format_checkup_line` (539), `run_checkup_cli` (828). `agent_workflows/config.py::ci_checkup_workflow` (2656; default `tests.yml`, blank or non-string falls back to the default). `agent_workflows/engine.py:6722` `SECRET_SCAN_CI = ".github/workflows/secret-scan.yml"` (written at 7509). `agent_workflows/runner_shared.py::decide_red_ci_gate` (26080; `UNKNOWN` proceeds with a warning). `tests/test_checkup.py` (`_init_repo` 40-49, `_create_gh_stub` 52, `gh_env` fixture, ten `gh_env` tests, `test_ci_shape_unknown_no_gh` 177-186). `tests/support.py::make_fake_executable` (667). `.aw/system/workflows/setup-repo/setup-repo.md` `### 5. CI baseline for the stack` (185). `README.md` `### Periodic CI checkup` (262-280). `CHANGELOG.md` `## 2.0.0 (pending)`. Every citation resolved.
- Found F1: `tests/test_checkup.py::_init_repo` creates no `.github/` directory, so the E-01 short-circuit would stop ten existing `gh`-stub tests from reaching the stub and would break the `command not found` assertion. The file was not in Scope-Paths. Fixed with E-04.
- Found F7: `README.md` documents `ci_checkup_workflow` and `CHANGELOG.md` carries a pending `## 2.0.0` section, yet the plan updated neither for a user-visible change. Fixed with E-05.

### Step R2

- Checked: the E/V bijection after `aw ipd sync --apply` (E-01..E-05 to V-01..V-05, `Highest E allocated: 05`), `Depends on` order, Scope-Paths completeness, and V-item evidence specificity.
- Found F1 (also): the gating rule appeared three ways (E-01 "while root is a git repository"; Proposed change 1 "`.github/workflows` directory exists (or `.git` exists ...)"; Step 0 "OR check existing test fixtures carefully"), so an executor had to choose. Fixed: one rule (bare `.yml`/`.yaml` filename and `.is_file()` is False) stated identically in the diagram, E-01, Proposed changes, and V-01, with the rejected `.github/workflows/` gate and its reason recorded in Step 0.
- Found F2: E-01's clause "when a test explicitly mocks `subprocess.run` on a synthetic temp dir" described test structure, not behavior, and no test mocks `subprocess.run` (they use a `gh` stub on `PATH`). Removed.
- Found F3: "without path traversal" was undefined. Fixed: a bare filename contains no `/` or `\`; any other value goes to `gh` unchanged.
- Found F4: the reason string differed between the Goal diagram and E-01's expected outcome. Fixed: one exact string in both.
- Found F6: V-01..V-03 named no units and did not demand evidence that `gh` was not spawned; sync created V-04/V-05 with placeholders. Fixed: each V-item names its test cases or diff lines, demands the stub call-log result, and states a fail condition.

### Step R3

- Checked (full form): the new check reads one path under `root / ".github" / "workflows"` with `.is_file()`. Restricting the check to bare filenames (no `/` or `\`) means a configured value cannot direct the check outside `.github/workflows/`, and values with separators still go only to `gh` as an argv element, as today. No shell, no new subprocess, no new output of local paths (the reason names the repo-relative path only), and no credential handling. Removing a `gh` call reduces network egress.
- No security finding.

### Step R4

- Checked: correctness (the short-circuit returns before `gh`, so `preserve_failing_on_unknown` in `perform_checkup` still keeps a prior `FAILING` record on the run-start path, unchanged), edge cases (no `.github/` at all, configured absent workflow while `tests.yml` exists, numeric workflow ID, `.YML` case), performance (one `stat`, no git subprocess), operability (the reason names both remedies), and tests (`tests/test_red_ci_stop.py` and `tests/test_clean_target_control_state.py` mock `run_start_checkup`/`perform_checkup`, so they are unaffected). `.agents/skills/setup-repo/SKILL.md` needs no regeneration: `host_adapters.compute_workflow_semantic_digest` hashes the body path, not its content.
- Found F5: E-02 named no target section and said nothing about the generated skill pointer. Fixed: E-02 names `### 5. CI baseline for the stack`, the two choices, ask-before-change, the conformant classification, and that the pointer needs no regeneration.
- Found F8: the Goal said `aw attention` and `aw doctor` "fail"; they display the saved reason. "Over-scope: none / Under-scope: none" was false after F1 and F7. Required tests used the `tests/test_checkup*.py` glob, which already matched the new module. Fixed: Goal wording, Scope check, and a precise pytest command with `-o addopts=""`.

### Proofreading

Checked the plan against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | 4 Scope-Paths; Scope omitted fixture and docs | Added `tests/test_checkup.py`, `README.md`, `CHANGELOG.md`; Scope names both | F1, F7 |
| Goal and diagram | "failing with a raw ... 404"; diagram reason differed from E-01; no bare-filename branch | Says what `attention`/`doctor` display; states status is unchanged and why the gate is unaffected; diagram shows both branches and the exact reason | F4, F8; requirement 12 |
| E-01 | Three-way gating rule; test-structure clause; undefined "path traversal" | One rule, defined bare filename, `.is_file()`, no git subprocess, rejected alternative stated | F1, F2, F3 |
| New E-04 | Absent | Fixture commits `tests.yml`; custom-workflow test commits `custom-ci.yml`; no assertion weakened | F1 |
| E-02 | No target section | Names step 5, both choices, ask-before-change, conformant rule, pointer note | F5 |
| New E-05 | Absent | README sentence and CHANGELOG `- Fixed:` bullet, no dashes | F7 |
| E-03 | Four cases, no call-log evidence | Seven cases (a)-(g) asserting on the `gh` stub log, including the rendered line | F6 |
| Step 0, Proposed changes, Scope check, Required tests, Spec sync | Contradictory rule; false "none" claims; glob | Consistent rule and order; accurate scope claims; precise command; spec search result | F1, F8 |
| V-01..V-05 | Unit-free; two placeholders | Each names units, the call-log result, and a fail condition | F6 |
| Approval and execution gate | Bare cohesion line | Cohesion reason and execution order | Followability |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |

### Step S5

- Checked: the plan has no open questions. Each judgement call this review made is recorded in Decisions D1-D3 and is reversible. Nothing needs a human answer before approval.

### Pass 2

- Re-read the revised plan end to end. The gating rule, reason string, and case list are identical in the Goal diagram, E-01, E-03, Proposed changes, Step 0, and V-01/V-03. `aw ipd lint --phase review-finalize --agent` returned `clean` (exit 0; info only: `IPD-Z603`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | HIGH | UNDER-SCOPE | R1 / R2 / Correctness | tests/test_checkup.py:40-49 `_init_repo` creates no `.github/`; tests/test_checkup.py:186 asserts `command not found`; plan E-01, Proposed change 1, Step 0 note | The gating rule was stated three incompatible ways, and the natural reading would regress ten existing `gh`-stub tests in a file outside Scope-Paths. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | One rule everywhere; E-04 updates the fixture; `tests/test_checkup.py` added to Scope-Paths. |
| F2 | MEDIUM | IN-SCOPE | R2 / Behavior spec | plan E-01 clause "when a test explicitly mocks `subprocess.run`" | Production behavior was defined in terms of test structure. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Clause removed; behavior defined by inputs only. |
| F3 | MEDIUM | IN-SCOPE | R2 / R3 / Definition | plan E-01 "without path traversal" | The filename test was undefined. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Bare filename: `.yml`/`.yaml` suffix, case-insensitive, no `/` or `\`. |
| F4 | LOW | IN-SCOPE | R2 / Consistency | plan Goal diagram node D vs E-01 expected outcome | Two different reason strings. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | One exact string. |
| F5 | LOW | IN-SCOPE | R4 / Executability | .aw/system/workflows/setup-repo/setup-repo.md:185 `### 5. CI baseline for the stack` | E-02 named no section and no handling of the generated skill pointer. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-02 names the section, choices, consent rule, and pointer note. |
| F6 | MEDIUM | IN-SCOPE | R2 / Evidence | plan V-01..V-03; `aw ipd sync` placeholders on V-04/V-05; tests/test_checkup.py:52 `_create_gh_stub` | V-items named no units and did not demand proof that `gh` was not spawned. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Each V-item names cases, the stub call-log result, and a fail condition. |
| F7 | LOW | UNDER-SCOPE | R1 / Docs | README.md:274 `ci_checkup_workflow` bullet; CHANGELOG.md `## 2.0.0 (pending)` | A user-visible behavior change had no user documentation. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-05 adds a README sentence and a CHANGELOG bullet. |
| F8 | LOW | IN-SCOPE | R4 / Accuracy | plan Goal, `## Scope check`, `## Required tests / validation` | The Goal overstated the symptom, the scope claims were false, and the test glob duplicated the new module. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Goal, Scope check, and test command corrected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D1 | When does the short-circuit apply? | Whenever `wf` is a bare `.yml`/`.yaml` filename and `.github/workflows/<wf>` is not a file | Only when `.github/workflows/` exists; only inside a git repository | A fresh repository with no `.github/` is the common case and must get the actionable reason; the fixture is cheap to update | yes |
| D2 | Add a new `CiHealth` value? | No; keep `UNKNOWN` with a new reason | `NOT_CONFIGURED` | Plan's own deferral; `decide_red_ci_gate` already treats `UNKNOWN` as warn-only | yes |
| D3 | Document in README and CHANGELOG? | Yes, one sentence and one bullet | Leave docs unchanged | README already documents `ci_checkup_workflow`; the change is user-visible | yes |
