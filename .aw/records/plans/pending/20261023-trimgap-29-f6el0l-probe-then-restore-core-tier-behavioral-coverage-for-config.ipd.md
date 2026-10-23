# IPD: Probe then restore core-tier behavioral coverage for config review-findings gate readers

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `yvmxs9` (Set `trimgap`) carries two production keys of `agent_workflows/config.py`, `findings_gate_threshold` and `read_review_findings_gate` (operator `return-none`), whose `wo21z5` budget probe never ran (verdict `budget-exhausted`, "budget exhausted at 10845.88s"). These two functions resolve the `review_findings_gate.block_at` threshold from `.aw/config/project.json`, which every review-findings gate (`check_engine.check_review_finding_unescalated`, `check_engine.evaluate_review_finding_escalation`, `review_findings.subject_gating_blocks`, the dependency findings gate) reads. Probing at authoring HEAD `18eca2f15` (F-01) shows BOTH `return-none` mutants SURVIVE the routine core tier, so the merge gate would stay green if threshold resolution broke. The restored control file `tests/test_plan_readiness_recheck.py` (non-core) kills `findings_gate_threshold` but NOT `read_review_findings_gate` (F-02), because its fixture writes `block_at: high`, the same value the fail-closed default yields when the reader returns None.
- Scope: Add ONE new core-marked test module, `tests/test_config_review_findings_gate.py`, holding direct behavioral tests that call `config.read_review_findings_gate` and `config.findings_gate_threshold` on isolated temp repos with varied `project.json` contents and assert the returned values (F-04 prototype). Then re-probe both keys under the full core selection. EXCLUDES any production-code change; EXCLUDES core-marking or editing `tests/test_plan_readiness_recheck.py` (it does not kill `read_review_findings_gate` anyway, F-02); EXCLUDES restoring `tests/test_review_findings_gate.py` (owned by sibling plan `p79jts`, F-05).
- Scope-Paths: tests/test_config_review_findings_gate.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: yvmxs9
- Set: trimgap
- Order: 29
- Highest E allocated: 03
- Author: opencode
- Id: f6el0l
- Approval: 2026-10-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (kill attribution to new module via newly_failing), PR-002 (budget overrun reported not failed), PR-003 (AW_HOME fallback note for missing-file case), PR-004 (execution contract) fixed; E-01 rows reproduced at 306ad1182 (F-07)

- 2026-10-23 to-review (opencode): authored from backlog `yvmxs9`. Probed both keys at HEAD `18eca2f15` under `-m core` (both `survived`) and under the restored control file `tests/test_plan_readiness_recheck.py` (`findings_gate_threshold` killed 7, `read_review_findings_gate` survived 0); prototyped four direct tests in a scratch file that failed under each key's monkeypatched `return-none` mutant and then deleted it.
- 2026-10-23 draft (opencode): created.

## Goal

Make a `return-none` mutation of `config.read_review_findings_gate` or `config.findings_gate_threshold` turn the routine core tier red, with a small, fast, core-marked module of direct behavioral tests. Done means both keys report `verdict: killed` under the full `-m core` selection with the new module committed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: add the core-tier module

- [ ] E-01 Create `tests/test_config_review_findings_gate.py` with a provenance docstring naming backlog `yvmxs9`, plan `f6el0l`, findings `wo21z5` and the control file `tests/test_plan_readiness_recheck.py`; `import pytest` and module-level `pytestmark = pytest.mark.core` (the pattern of `tests/test_engine_restored_behavior.py`); a helper that builds an isolated `tempfile.TemporaryDirectory` repo with `.aw/config/project.json` holding a given payload (or no file at all), cleaned up per test. Add these `unittest.TestCase` tests, each calling the function and asserting on its return value: (a) `read_review_findings_gate` returns the object unchanged for `{"review_findings_gate": {"block_at": "medium"}}`; (b) it normalizes a bare string `"  off "` to `{"block_at": "off"}`; (c) it returns None for a missing file, unparseable JSON, a non-object top level, and an absent key; (d) `findings_gate_threshold` returns, row by row with the row in the failure message: `medium` for `block_at: medium`, `blocker` for `" BLOCKER "`, `off` for `off`, `medium` for the bare-string form, and the fail-closed `high` for an absent file, an absent key, a typo `hgih`, and a non-string value `3`. Never read this repository's live `.aw/config/project.json`. Note for case (c) "missing file": `project_context.project_config_dir` falls back to `<AW_HOME>/projects/<id>/config/project.json` when the temp repo has no in-tree config, so the test relies on the root `conftest.py` home-isolation fixture ("Re-point AW_HOME/XDG_CONFIG_HOME at the session sandbox around every test"); do not set `AW_HOME` to a real home. All listed return values were re-measured by direct call at review HEAD `306ad1182` (F-07).
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_config_review_findings_gate.py` reports every test PASSED in well under a second (F-04 prototype: `4 passed in 0.23s`).
  - Execution state: pending

### Task group 2: commit and prove the mutants die in the core tier

- [ ] E-02 Commit the module with `aw commit f6el0l -- tests/test_config_review_findings_gate.py`, then run the routine bare gate `python3 -m pytest` and record the summary line and any `CORE TIER BUDGET EXCEEDED` block, plus the module's own cost from `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_config_review_findings_gate.py`.
  - Depends on: E-01
  - Expected outcome: bare run reports no failed tests and includes the new tests; the new module's summed call time is well under one second. A core-tier wall-time overrun is recorded verbatim, not treated as a failure of this plan: the bare run already measured `1675 passed, 11 warnings in 34.68s` (over the 30s budget) at HEAD `16d8abbb8` before this plan (F-07).
  - Execution state: pending

- [ ] E-03 For each key K in (`read_review_findings_gate`, `findings_gate_threshold`), run `python3 tools/mutation_probe.py --op return-none agent_workflows/config.py::K -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/`. `tools/mutation_probe.py` mutates in an isolated worktree cut from HEAD, so it only sees the committed module (that is why E-02 commits first). Record each `head:`, `verdict:`, `baseline_failing:`, `mutant_failing:` and `newly_failing` block in Findings. If a key reports `survived`, add the missing assertion to the module for that key, re-commit through `aw commit f6el0l`, and re-probe.
  - Depends on: E-02
  - Expected outcome: two `verdict: killed` lines under the full core selection, each with `head:` at or after the E-02 commit and a `newly_failing` list that includes at least one test id from `tests/test_config_review_findings_gate.py` (so the kill is attributable to this module, not only to another core test such as a sibling's; re-derive at execution, the count is not the bar).
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"): every test calls the two config functions on real temp files and asserts on returned values; nothing reads source.
- ISOLATED FIXTURES ONLY: the `19313eed^` control files' docstrings (`tests/test_plan_readiness_recheck.py`, `tests/test_review_findings_gate.py`) state that a threshold test reading the live `project.json` is order-dependent and breaks when a maintainer sets the key; the new module follows that.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (root `conftest.py`) under a 30s budget. Module-level `pytestmark = pytest.mark.core` applies to `unittest.TestCase` classes (`tests/test_engine_restored_behavior.py`).
- Probe tool: `tools/mutation_probe.py` (`--op`, `--extra-test COMMIT:PATH`, selection after `--`) is the tool `wo21z5` and sibling plans `2qlg0w`, `p79jts` used, so verdicts are comparable.
- Commit only through `aw commit f6el0l -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `tools/mutation_probe.py --op return-none agent_workflows/config.py::<K> -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` at HEAD `18eca2f15` | `findings_gate_threshold`: `verdict: survived`, `mutant_failing: 0` (266.21s). `read_review_findings_gate`: `verdict: survived`, `mutant_failing: 0` (369.92s). The merge gate does not guard either key. |
| F-02 | same probe tool, selection `-o addopts= -q -p no:randomly -n 6 tests/test_plan_readiness_recheck.py` at HEAD `18eca2f15` | `findings_gate_threshold`: `killed`, `mutant_failing: 7`. `read_review_findings_gate`: `survived`, `mutant_failing: 0`. The file was partly restored by `3c2499572` (only two methods carry `@pytest.mark.core`) and its `_mkrepo` writes `{"review_findings_gate": {"block_at": "high"}}`; a reader returning None makes `findings_gate_threshold` fall back to `REVIEW_GATE_DEFAULT` (`high`), the same value, so no recheck outcome changes. Core-marking more of that file would therefore not close the `read_review_findings_gate` gap. |
| F-03 | `grep -rn "findings_gate_threshold\|read_review_findings_gate" tests/` | No test calls either function directly; the only callers are `check_engine` and `review_findings` (`check_engine.check_review_finding_unescalated`, `check_engine.evaluate_review_finding_escalation`, `review_findings.subject_gating_blocks`, the `_findings_thr` resolution in the dependency check). |
| F-04 | scratch prototype `tests/scratch_yvmxs9_proto.py` (four tests: object read, bare-string read, absent/unparseable read, threshold row matrix), run in-process with each function replaced by `lambda *a, **k: None`; file deleted afterwards | Baseline: `4 passed in 0.23s`, `failing 0 of 4`. `read_review_findings_gate` mutant: `failing 3 of 4`. `findings_gate_threshold` mutant: `failing 1 of 4`. The probe tool itself could not see the uncommitted scratch file (its worktree is cut from HEAD; both runs reported `survived`, `mutant_failing: 0`), which is why E-02 commits before E-03 probes. |
| F-05 | `.aw/records/plans/pending/20261023-trimgap-27-p79jts-*.ipd.md` | Sibling `p79jts` (backlog `lzg859`) restores `tests/test_review_findings_gate.py` with `GateOutcomeTests` core-marked; its threshold rows also exercise `findings_gate_threshold` end to end. It is pending, not executed, and does not target either config key, so this plan does not depend on it and does not touch its file. The overlap is two independent guards at different layers (pure config reader here, rule wiring there). |
| F-06 | `wo21z5` `## Budget probe results` rows for both keys | Both rows: `budget-exhausted`, "budget exhausted at 10845.88s", wall 0.00; the verdicts in F-01 are the first actual measurement. |
| F-07 | review at HEAD `306ad1182`: direct calls of `config.read_review_findings_gate` / `config.findings_gate_threshold` on temp repos; `project_context.project_config_dir` rules; bare `python3 -m pytest` at `16d8abbb8` | Every E-01 row reproduces: object -> unchanged/`medium`; `"  off "` -> `{'block_at': 'off'}`/`off`; missing file, `{not json`, `[1]`, `{}` -> `None`/`high`; `" BLOCKER "` -> `blocker`; `hgih` and `3` -> `high`; bare `"medium"` -> `medium`. No test calls either function directly (F-03 holds). Missing in-tree config falls back to the AW_HOME home config, which the root `conftest.py` sandboxes. Bare run: `1675 passed, 11 warnings in 34.68s`. |

## Proposed changes (ordered, validatable)

1. E-01 creates the core-marked module of direct behavioral tests for both readers.
2. E-02 commits it and checks the bare core gate and the module's cost.
3. E-03 re-probes both keys under the full core selection against the committed tree.

## Deferred / out of scope (with reason)

- Core-marking more of `tests/test_plan_readiness_recheck.py`.
  - Carrier-Declined: no work is owed; it cannot kill `read_review_findings_gate` (F-02), and the direct tests kill both keys in under a second (F-04).
- Restoring `tests/test_review_findings_gate.py`.
  - Carrier-Declined: no work is owed here; sibling `p79jts` owns that file (F-05).

## Scope check

- Over-scope: none. Only the new test module is declared; no production file or existing test changes.
- Under-scope: none. Both backlog keys get direct killing tests (E-01) and a core-selection probe (E-03).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_config_review_findings_gate.py`: all PASSED, per-test list pasted (E-01).
- Bare `python3 -m pytest` summary line and any budget block pasted, plus the module's `--durations=0` output (E-02).
- Two `tools/mutation_probe.py` runs under `-m "core and not slow and not livecorpus" tests/`, full `head`/`target`/`operator`/`selection`/`verdict`/`baseline_failing`/`mutant_failing`/`newly_failing` output pasted, each `killed` with a `newly_failing` entry from the new module (E-03).
- `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/` both empty (no production change), where `<base>` is HEAD before execution.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore control-file tests or write direct tests?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: direct tests. The backlog remedy is "probe then restore", and the probe (F-02) shows the control file's tests cannot kill `read_review_findings_gate` because its fixture value coincides with the default. Direct calls on varied `project.json` payloads kill both mutants (F-04) and cost about 0.2s, versus the recheck file's git and review fixtures.

### OQ-02: Probe the full core selection or only the new file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: the full core selection (`-m core ... tests/`), because the gap is that the routine gate does not kill the mutants (F-01), and only a probe over that exact selection proves it closed. It costs about 4 to 6 minutes per key (F-01 wall times).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the head of `tests/test_config_review_findings_gate.py` showing the provenance docstring (naming `yvmxs9`, `f6el0l`) and `pytestmark = pytest.mark.core`; paste `grep -nE "inspect|getsource|ast\." tests/test_config_review_findings_gate.py` returning nothing; paste `python3 -m pytest -o addopts="" -v tests/test_config_review_findings_gate.py` listing every test PASSED and the summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `aw commit` output or `git show --stat HEAD` showing only `tests/test_config_review_findings_gate.py`; paste the bare `python3 -m pytest` summary line showing `passed` and no `failed`, any `CORE TIER BUDGET EXCEEDED` block verbatim (reported, not a failure of this plan), and the `--durations=0` output for the new module.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the full output of the two `tools/mutation_probe.py` runs (produced by the tool itself in E-03), each with `selection:` containing `-m core and not slow and not livecorpus tests/`, a `head:` equal to the E-02 commit or later, `verdict: killed`, and a `newly_failing` list including at least one `tests/test_config_review_findings_gate.py` test id; paste `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/`, both empty.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:
- All open questions are resolved (OQ-01, OQ-02).
- Scope fence: `- Scope-Paths:` is a declaration, not a stop condition. An out-of-scope edit that proves necessary is made and then justified at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).
- You MUST paste the ACTUAL command, runner, and probe output into each `V-*` Observed evidence; never claim a test passed or a mutant was killed that you did not run.
- Mutation checks use `tools/mutation_probe.py` only, after the E-02 commit; never hand-edit `agent_workflows/`.
- Commit only files you changed, through `aw commit f6el0l -- tests/test_config_review_findings_gate.py` (plus this plan when recording evidence); verify `git diff --cached --name-only`; never `git add -A`; never push.
- Lifecycle: after every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`. Under `aw oc run` / `aw agy run` the runner performs that transition; only an executor running by hand invokes `aw ipd finalize f6el0l` itself.
