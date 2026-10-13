# IPD: Prove build_report yields GO with the subprocess gates live on a synthetic clean tree

- Date: 2026-10-12
- Kind: child
- Concern: Backlog `r4a4ab` recorded that `aw ipd lint --all` exited 1 on this repository's live tree (no longer true at review HEAD `03363cbc8`, where it exits 0; see F-01), so `release_readiness.gate_ipd_lint` fails and `release_readiness.build_report` can never return GO against it. As a result no test asserts a GO verdict with the two shelling-out gates (`gate_leak_scan`, `gate_ipd_lint`) actually running: the existing GO test passes `run_subprocess_gates=False`, so the end-to-end GO path through real subprocesses is unproven.
- Scope: Add hermetic behavioral tests to `tests/test_release_readiness.py` that build a synthetic clean repository in `tmp_path`, call `build_report` with `run_subprocess_gates=True`, and assert GO; then add one nonconforming pending plan to the same synthetic tree and assert the verdict flips to NO-GO with `failing_gates() == ["ipd_lint"]`. The live tree's lint state is NOT touched and NOT asserted on: whether it is red or green at any moment is a property of other agents' pending plans (livecorpus hazard).
- Scope-Paths: tests/test_release_readiness.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: r4a4ab
- Set: r4a4ab
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 514wv3
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog r4a4ab; findings re-measured at HEAD 58f0f7fe5.

## Goal

Prove, with both subprocess gates live and no coupling to this repository's own records corpus, that `release_readiness.build_report` returns GO on a clean tree and NO-GO naming exactly `ipd_lint` when a nonconforming plan appears. That restores the coverage the deleted GO-on-clean-tree and ipd-lint-all-phases arms intended, without the livecorpus hazard the backlog item names.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure

- [ ] E-01 At execution HEAD, record the HEAD sha and re-derive the premise. Run `python3 -m agent_workflows ipd lint --all >/dev/null 2>&1; echo exit=$?` and `python3 -m agent_workflows ipd lint --all 2>&1 | grep counts:` and record both; either exit code is acceptable and neither stops the plan, because the tests never read the live tree (F-01). Run `grep -n "run_subprocess_gates" tests/test_release_readiness.py` and confirm that every existing `build_report` call in that file passes `run_subprocess_gates=False` (so no existing test drives GO through live subprocess gates). If a test already asserts GO with live subprocess gates on a synthetic tree, STOP AND REPORT: the work is already done.
  - Depends on: none
  - Expected outcome: HEAD sha, the live lint exit code and counts line, and the grep output are recorded; the grep confirms no live-gate GO test of `build_report` exists. (`tests/test_release_readiness_child_pin.py` asserts each gate individually returns 0 on this tree shape; that is NOT a `build_report` GO test and does not trigger the stop, F-06.)
  - Execution state: pending

### Task group 2: Add the tests

- [ ] E-02 In `tests/test_release_readiness.py`, add a helper that extends the existing `_build_synthetic_root` fixture into a tree both subprocess gates accept: run `git init -q` in the synthetic root (the leak scanner refuses a non-git directory, as `tests/test_release_readiness_child_pin.py` documents) and create an empty `.aw/records/plans/pending/` so `ipd lint --all` locates a plans tree instead of exiting 2. Then add `test_build_report_go_with_live_subprocess_gates`, which sets `GIT_CEILING_DIRECTORIES` to `tmp_path` via `monkeypatch`, calls `rr.build_report(suite_passed=True, residual_risk_signed=True, residual_risk_signer=<non-empty>, repo_root=root)` with the default `run_subprocess_gates=True`, and asserts `rep.verdict == rr.VERDICT_GO`, `rep.failing_gates() == []`, and that the `leak_scan` and `ipd_lint` gates are both present in `rep.gates` with `passed is True` and `evidence["returncode"] == 0`. Do not modify any existing test.
  - Depends on: E-01
  - Expected outcome: the new test exists, drives both real subprocess gates, and passes.
  - Execution state: pending
- [ ] E-03 In the same file, add `test_build_report_nonconforming_plan_flips_only_ipd_lint`, which builds the same synthetic tree, first asserts GO as in E-02, then writes a deliberately nonconforming pending plan (for example `.aw/records/plans/pending/20261012-x-01-abcdef-x.ipd.md` containing only `# IPD: x` and `- Status: to-review`), calls `build_report` again, and asserts `rep.verdict == rr.VERDICT_NO_GO`, `rep.failing_gates() == ["ipd_lint"]`, and the `ipd_lint` gate's `evidence["returncode"] == 1`. This proves the GO in E-02 is not vacuous: the ipd_lint gate really reads the tree it is pointed at.
  - Depends on: E-02
  - Expected outcome: the new test exists and passes, showing the verdict tracks the synthetic tree's plan conformance.
  - Execution state: pending

### Task group 3: Verify

- [ ] E-04 Run the new tests in isolation with `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py`, then run the full fast suite BARE as `python3 -m pytest`. If anything fails, re-run the same selection at the base commit before blaming this change and report the comparison.
  - Depends on: E-03
  - Expected outcome: the file passes in isolation including both new tests, and the bare suite passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior and assert outcomes, never read source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). Both new tests call `build_report` and assert on its returned report.
- A test that asserts a property over this repository's own `.aw/records/` tree is `livecorpus` and is deselected by default because any agent's plan can turn it red (`pyproject.toml` marker text "livecorpus: asserts a property over EVERY artifact"). The new tests use only a `tmp_path` tree, so they are not livecorpus.
- `tests/test_release_readiness_child_pin.py` (`test_gates_do_not_execute_decoy_package_in_caller_repo_root`) already shows the minimal tree both gates accept: a `git init` directory with `.aw/records/plans/pending/`. The new tests reuse that shape.
- The existing GO test, `test_build_report_clean_tree_is_go`, passes `run_subprocess_gates=False`; the plan dyiasf restored it that way on purpose (backlog `r4a4ab` body, "Plan dyiasf discharges what it owes the finding").
- Suite contract: run bare as `python3 -m pytest` (AGENTS.md "HOW TO RUN THE SUITE").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | HISTORICAL, re-measured at review: at authoring HEAD 58f0f7fe5 the live tree was red with 1 error plan (`ipd lint --all` exit=1, `counts: conforming=69, quarantined=0, legacy/not evaluated=1323, error=1`). At review HEAD `03363cbc8` it is GREEN: exit=0, `counts: conforming=117, quarantined=0, legacy/not evaluated=1324, error=0`. The live state flips with other agents' plans, which is exactly why the tests must not depend on it. | `python3 -m agent_workflows ipd lint --all` at both HEADs (review PR-001). |
| F-02 | HISTORICAL: the authoring-time error was `IPD-Q501` on plan `15db4k` (OQ-01), a deliberately BLOCKING maintainer question. `15db4k` has since been resolved and is in `plans/executed/`. | `.aw/records/plans/executed/20261011-4xtpvg-02-15db4k-...ipd.md`. |
| F-03 | Whenever the live tree is red because a pending plan carries a blocking question, a NO-GO from `gate_ipd_lint` is the CORRECT verdict, and greening the tree is never this plan's job. The principle stands even though the live tree happens to be green today. | F-01, F-02; backlog `r4a4ab` "the red is a property of OTHER agents' pending plans". |
| F-04 | The real gap is coverage: no test proves GO through live subprocess gates. A probe at HEAD 58f0f7fe5 against a synthetic tree (git init, empty `pending/`, CHANGELOG `## 1.0.0`, `.aw/system/VERSION` `1.0.0`, `docs/`) returned `GO []` in about 1.1s; adding a two-line nonconforming plan returned `NO-GO ['ipd_lint']`. Reproduced at review HEAD `03363cbc8`: `GO [] [('leak_scan', {'returncode': 0}), ('ipd_lint', {'returncode': 0})]`, then `NO-GO ['ipd_lint']` with `ipd_lint` `returncode: 1` for the E-03 plan name. Review also confirmed both tree preconditions are load-bearing: without `git init` `leak_scan` returns 2; without `pending/` `ipd_lint` returns 2. | Authoring probe; review probe (PR-002). |
| F-05 | Run time is load-sensitive: about 1.1s at authoring, but 10.6 to 11.9s at review under load average ~115, where `test_release_readiness_child_pin.py::test_gates_do_not_execute_decoy_package_in_caller_repo_root` (same two gates, not marked `slow`) took 9.25s. The new tests therefore match an existing unmarked precedent and are left unmarked; E-03 spawns the gates twice, so it costs about double. | Review timing (PR-003). |
| F-06 | Each gate is already proven to return 0 individually on this tree shape by `test_gates_do_not_execute_decoy_package_in_caller_repo_root` (calls `gate_leak_scan` / `gate_ipd_lint` directly). What is unproven is the AGGREGATE: `build_report` with `run_subprocess_gates=True` reaching GO, and the verdict flipping on tree content. That is this plan's actual delta. | `tests/test_release_readiness_child_pin.py`; `grep -n run_subprocess_gates tests/test_release_readiness.py` -> lines 339, 354, 370, 431, all `False` (review PR-002). |

## Proposed changes (ordered, validatable)

1. Re-measure the premise at execution HEAD (E-01).
2. Add a GO test with live subprocess gates on a synthetic tree (E-02).
3. Add a NO-GO flip test proving the ipd_lint gate reads that tree (E-03).
4. Run the file and the bare suite (E-04).

## Deferred / out of scope (with reason)

- Resolving `15db4k` OQ-01 or any other plan's lint error to make the live tree green: maintainer-owned decision in another author's plan (F-02, F-03).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- A livecorpus test asserting GO on the live tree: it would be red today by a correct verdict, and any agent's plan could turn it red again (backlog `r4a4ab` "documented livecorpus hazard").
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Changing `gate_ipd_lint` semantics (for example ignoring `IPD-Q501`): that would let a release ship past a blocking open question, weakening the gate.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none. Only `tests/test_release_readiness.py` changes; no production code changes.
- Under-scope: none. The backlog item's actionable consequence is that no test asserts `build_report` GO with live gates; E-02 and E-03 supply that assertion hermetically (F-06), and F-03 records why the live tree's state is left alone.

## Required tests / validation

1. `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py` passes, including the two new tests (E-04).
2. Bare `python3 -m pytest` passes (E-04).
3. `aw ipd lint` on this plan conforms.

## Spec / documentation sync

N/A: no behavior, CLI surface, or contract changes; only tests are added. The `release_readiness` module docstring already describes the gates these tests exercise.

## Open questions

None. Whether to make the live tree green was answered from repository evidence (F-01, F-03): the live tree's state belongs to other agents' plans (and is green at review HEAD regardless), and the tests deliberately do not depend on it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste the execution HEAD sha, the `exit=N` line and `counts:` line from the live `ipd lint --all`, and the verbatim `grep -n "run_subprocess_gates" tests/test_release_readiness.py` output showing every pre-existing call passes `run_subprocess_gates=False`. A pre-existing live-gate GO test makes this FAIL (stop and report).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste the diff hunk adding the helper and `test_build_report_go_with_live_subprocess_gates`, showing it calls `build_report` without `run_subprocess_gates=False` and asserts GO, an empty `failing_gates()`, and `returncode == 0` for both `leak_scan` and `ipd_lint`. Paste `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py -k live_subprocess_gates` output showing `1 passed`. Paste `git diff --stat` showing only `tests/test_release_readiness.py` changed and no existing test function removed or edited.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste the diff hunk adding `test_build_report_nonconforming_plan_flips_only_ipd_lint`, showing the GO assertion before the plan is written and the NO-GO, `failing_gates() == ["ipd_lint"]`, `returncode == 1` assertions after. Paste `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py -k flips_only_ipd_lint` output showing `1 passed`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the actual final summary line of `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py` (zero failures, count including the two new tests) and of a bare `python3 -m pytest` run (`N passed`, zero failures attributable to this change; paste the base-commit comparison for any failure).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). No open questions remain. The executor follows the agent execution contract: commit only `tests/test_release_readiness.py` and this plan through `aw commit 514wv3 -- <paths>`, never `git add -A`, never push, and paste the ACTUAL runner output for every test claim. Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is justified at finalize with `--scope-reason`. E-01's stop (the work already exists) is a genuine prerequisite stop, not a scope stop. Lifecycle: once `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence, the plan moves to `executed/`: under `aw oc run` / `aw agy run` the runner owns that finalize, so do not run `aw ipd finalize` or `git mv` yourself; executed by hand, run `aw ipd finalize 514wv3`. Never `git mv` the plan by hand. This plan asserts nothing about the live tree's lint state (F-01, F-03).
