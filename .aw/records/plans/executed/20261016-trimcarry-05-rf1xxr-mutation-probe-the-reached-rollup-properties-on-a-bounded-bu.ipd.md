# IPD: Mutation-probe the reached rollup properties on a bounded budget

- Date: 2026-10-16
- Kind: child
- Concern: The 747 rollup keys (backlog `9qvfie` outcome 2) were never mutation-probed: `rq3q7v` spent its budget (3466.82s) on two full-default-selection survivor runs (`hpjj44` `## Mutation totals`). A key's guard status follows from its `hpjj44` classification or its reach class (Order 03 `8dyt88` `## Key reach`) for four classes and needs a probe for the rest: an `unreached` key cannot be guarded by the routine non-slow selection, since no test in that selection executes it (in-process or in a traced subprocess), so any mutant of it survives that selection by construction; a `reached` key may or may not be guarded, and only a probe with a positive control decides. Probing with a NARROWED selection (the surviving test files whose contexts reach the key) costs seconds rather than the ~1600s a full-selection survivor took.
- Scope: IN: assign every key a final verdict from its reach class and `hpjj44` classification without a probe where the class decides it (`pin-retired`, `property-unidentifiable`, `key-gone`, `unreached`); probe `reached` keys (and then `subprocess-only` keys with the explicit full non-slow `tests/` selection, budget permitting) with `tools/mutation_probe.py`, survivor plus positive control, in descending `hpjj44` exclusive-line order until a 10,800s cumulative cap; write `## Rollup mutation results` and totals. OUT: filing (Order 06 `z2xs98`); code or test edits.
- Scope-Paths: .aw/records/research/*-trimcarry-01-*.findings.md
- Item-Dependencies: executed:8dyt88
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 5
- Highest E allocated: 03
- Author: opencode
- Id: rf1xxr

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: rf1xxr verified (set trimcarry, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set trimcarry graduating backlog 9qvfie.

## Goal

Replace "triaged, not mutated" with a final verdict for as many of the 747 keys as a bounded budget allows, and an explicit reason for every key it does not reach.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Verdicts that need no probe

- [x] E-01 Record `git rev-parse HEAD` and the `head` Order 03 recorded in `## Baseline`, and paste `git diff --stat <Order 03 head> HEAD -- agent_workflows tests`. Derive the key set from COMMITTED sources only (Order 03's `keys.txt` and `baseline.json` live under the gitignored `.aw/state/` and are NOT present in this plan's isolated worktree): the `production-key` rows of `hpjj44` `## Triaged not mutated` (747) must equal the `Key` column of `## Key reach`. For each of the 747 keys, take `Classification` and `Mutation Operator` from `hpjj44` `## Derived properties` and `Reach class` from the Set doc's `## Key reach`, and assign without probing, in this order: `pin-retired` (Classification `pin-retired`; carrier-free per `hpjj44` reconciliation (d)); `property-unidentifiable` (Classification `property-unidentifiable`; operator `n/a`); `key-gone` (reach class `key-gone`; the subject no longer exists at HEAD); `unguarded-unreached` (reach class `unreached`: no test in the routine non-slow selection executes the function, in-process or in a traced subprocess, so none can kill a mutant of it; the `Reason` cell MUST say "unreached by the non-slow selection at <Order 03 head>", because `slow`/`livecorpus` tests were excluded from the measurement (`8dyt88` `## Method`)). If the pasted diff is non-empty, every `key-gone` or `unguarded-unreached` key whose module file appears in it is instead `to-probe` (its reach class is stale), and the changed `tests/` paths are listed under the table as a caveat for Order 06. Every remaining key is `to-probe`. Write the `## Rollup mutation results` header table (`Key`, `Operator`, `Reach class`, `Final verdict`, `Reason`, `Survivor`, `Control`, `wall_s`) with these rows filled.
  - Depends on: none
  - Expected outcome: every key has a row; the non-probe classes are final; the `to-probe` set is listed in `hpjj44` exclusive-line order (`reached` keys first, then `subprocess-only`).
  - Execution state: performed

### Task group 2: Budgeted probes

- [x] E-02 For each `to-probe` key in order, until the cumulative `wall_s` of this batch exceeds 10,800s (the cap `hpjj44` `## Mutation shortlist` used): (1) SELECTION: for `reached`, `-m "not slow and not livecorpus"` plus the surviving test files from `## Key reach` (the same marker filter the reach was measured under); for `subprocess-only`, `-n auto -m "not slow and not livecorpus" tests/`. Do NOT omit the `--` selection: the probe's no-argument default (`-n auto -m "not slow and not livecorpus"`, `tools/mutation_probe.py` `probe`) names no path, so pytest falls back to `pyproject.toml` `testpaths`, which is a 19-module core list (707 tests collected at review versus 9195 for `tests/`), and a survivor on that subset would yield a false `unguarded`. (2) PREFLIGHT every selection with `python3 -m pytest -o addopts= -q --collect-only <the exact selection arguments of step 1>` (exit 0, at least one test collected; a key with no collectable selection is `unprovable` with reason `empty selection`), since a selection that collects nothing still yields a valid empty junit file and a false `survived` (`rq3q7v` F-03). (3) SURVIVOR: `python3 tools/mutation_probe.py <key> --op <operator> --format json -- <selection>`. (4) CONTROL: `python3 tools/mutation_probe.py <key> --op <operator> --format json --extra-test 19313eed:<deleted reaching file> -- <deleted reaching file>`, taking the deleted file with the most exclusive lines from `hpjj44` `## Derived properties` `Reaching Test Files` (when that path exists again at HEAD, restored by Orders 01/02 or one of the 4 recreated files, the probe overwrites it with the `19313eed^` blob and lists it in `extra_tests_overwrote`; record that in the row). Run the control only when the survivor is `survived`. (5) MAP with the `rq3q7v` rule: survivor `killed` -> `guarded`; survivor `survived` with control `killed` -> `unguarded`; survivor `killed-by-import` -> rerun survivor (and control if needed) once with an operator from the tool's `OPERATORS` that this key has not tried and that `apply_operator` accepts (an `invalid` verdict means it does not), recording both attempts, else `unprovable`; survivor `invalid`/`error`/`timeout`, or control `survived`/`invalid`/`killed-by-import`/`error`/`timeout` -> `unprovable` with the reason. Save each JSON under the gitignored `.aw/state/trimcarry-rf1xxr/`, and record any non-empty `checkout_status_changed` in the row. A key's `wall_s` is its survivor plus control (plus retry) `wall_s`. Do not START a key once the cumulative `wall_s` exceeds the cap; every key not started gets `budget-exhausted` with the cumulative time.
  - Depends on: E-01
  - Expected outcome: each probed key has a final verdict; no `unguarded` rests on a selection that failed preflight or on the bare `testpaths` default; `git status --short` and `git worktree list` unchanged after the batch.
  - Execution state: performed

### Task group 3: Totals and commit

- [x] E-03 Write `## Rollup mutation totals`: count per final verdict (`pin-retired`, `property-unidentifiable`, `key-gone`, `unguarded-unreached`, `guarded`, `unguarded`, `unprovable`, `budget-exhausted`) summing to 747, total probe `wall_s`, and a per-module table of non-`guarded`, non-carrier-free keys for Order 06's grouping. Run `aw research index`, then commit only the doc: `aw commit <this plan> -- <doc path>`.
  - Depends on: E-02
  - Expected outcome: totals sum to 747; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `tools/mutation_probe.py` CLI: `target` as `<path.py>::<qualname>`, `--op {return-none,return-true,return-false,negate-return,raise}`, `--extra-test COMMIT:PATH` (reads `COMMIT^:PATH`), `--timeout`, `--format json`, pytest selection after `--`; with no selection it uses `-n auto -m "not slow and not livecorpus"`. It mutates committed HEAD in a disposable worktree and reports `checkout_status_changed`.
- Survivor/control/mapping rules and the preflight are the ones executed plan `rq3q7v` used (its Scope and E-02 steps 1 to 6), so verdicts are comparable with `hpjj44`.
- Operators in `hpjj44` `## Derived properties` for the 747 keys are `return-none` 616, `raise` 81, `negate-return` 23, `return-false` 19, `n/a` 8 (review count; the 8 `n/a` are exactly the 5 `pin-retired` and 3 `property-unidentifiable` keys).
- The probe runs pytest with `-o addopts=` plus the given selection; with NO selection its default names no path, so pytest uses `pyproject.toml` `testpaths` (a 19-module core list since `ad9213cc6`). Measured at review HEAD `5cf4fb46a`: `--collect-only -m "not slow and not livecorpus"` -> `707/712 tests collected`; the same with `tests/` -> `9195/9494 tests collected`. Every selection in this plan is therefore explicit.
- Measured at review: `python3 tools/mutation_probe.py agent_workflows/ipd_lifecycle.py::_scope_match --op return-false --format json -- -n 2 -m "not slow and not livecorpus" tests/test_scope_match.py` -> `"verdict": "killed"`, `"newly_failing_total": 2`, `"checkout_status_changed": []`, `"wall_s": 11.46`; `git status --short` empty and `git worktree list` count unchanged (14) before and after.
- Order 03's scratch (`.aw/state/trimcarry-8dyt88/`) is gitignored (`.aw/.gitignore` `/state/`), so it does not reach this plan's isolated worktree; only the committed findings doc carries Order 03's results.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | No rollup key was probed; the whole prior budget went to two full-selection survivors (1600.47s and 1866.35s). | `hpjj44` `## Mutation results` rows `PROP-01`, `PROP-02`; `## Mutation totals` 3466.82s. |
| F2 | A narrowed control run cost 17.26s in `rq3q7v`. | `rq3q7v` V-02 pasted control JSON `"wall_s": 17.26`. |
| F3 | At derivation 263 of the 747 keys had surviving contexts; Order 03 re-measures this at HEAD. | `8dyt88` F2. |
| F4 | 5 keys are `pin-retired` and 3 `property-unidentifiable`, all inside the 747. | Authoring join of `## Derived properties` classification with `## Triaged not mutated`. |

## Proposed changes (ordered, validatable)

1. Non-probe verdicts (E-01).
2. Budgeted survivor plus control probes (E-02).
3. Totals and commit (E-03).

## Deferred / out of scope (with reason)

- Keys left `budget-exhausted`: Order 06 files them as one grouped item naming this section.
  - Carrier: z2xs98
- Raising the 10,800s cap: a cost decision for the maintainer; the cap matches `hpjj44`'s.
  - Carrier-Declined: deliberate non-goal; the residue stays tracked through Order 06.

## Scope check

- Over-scope: none.
- Under-scope: none; every one of the 747 keys ends with a verdict or `budget-exhausted`.

## Required tests / validation

No tests are authored. Validity is checked by V-01..V-03 (row count 747, preflight passed for every narrowed `unguarded`, totals reconcile).

## Spec / documentation sync

N/A: research record only.

## Open questions

### OQ-01: Is `unguarded-unreached` a sound verdict without a probe?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes, for the routine non-slow selection: a key absent from the baseline's `functions` has no line hit by that selection at all, in-process or in a subprocess (the baseline traces subprocesses, `tools/replay_coverage_diff.py` `_make_rc_content` `patch = subprocess`; lines hit with no test context are the separate `subprocess_only` class, which this plan probes). The residual hole is the excluded `slow`/`livecorpus` tests, so the verdict's reason names the selection and Order 06 must read it as "unguarded by the routine gate", not "unguarded by any test". The positive control is skipped for these keys, so the verdict says "unguarded" without proving the operator is killable; Order 06's filed item restores a test and proves the kill there.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git rev-parse HEAD`, Order 03's recorded head, and the `git diff --stat` from E-01; pasted output of a `python3 -c` check that `## Rollup mutation results` has 747 distinct keys equal to both the `production-key` rows of `hpjj44` `## Triaged not mutated` and the `Key` column of `## Key reach`; pasted counts for the four non-probe classes and the `to-probe` count.
  - Observed evidence:
    Order 03's recorded head: `86f0d88d9e967a79af6b3e6cd335081393fdbf72`
    Lane starting HEAD: `f13aea8d61806a50a338faf216e3312b48865ac7`
    `git diff --stat 86f0d88d9e967a79af6b3e6cd335081393fdbf72 f13aea8d61806a50a338faf216e3312b48865ac7 -- agent_workflows tests`:
    ```
     agent_workflows/cli.py                         |  33 ++
     agent_workflows/install_wizard.py              | 137 +++++++-
     agent_workflows/release_readiness.py           | 176 ++++++++--
     agent_workflows/render_stream.py               |  23 +-
     tests/test_placement_switch_guard.py           | 391 +++++++++++++++++++++
     tests/test_records_root_accessor.py            | 104 +++++-
     tests/test_release_readiness.py                |   8 +-
     tests/test_release_readiness_docs_gate.py      |  11 +-
     tests/test_release_readiness_not_applicable.py | 455 +++++++++++++++++++++++++
     tests/test_release_readiness_producers.py      |  39 ++-
     tests/test_releases_readiness_cli.py           |  24 +-
     tests/test_statusline_stop_tally.py            |  37 ++
     12 files changed, 1364 insertions(+), 74 deletions(-)
    ```
    Pasted `python3 -c` verification check against committed sources:
    ```
    Rollup mutation results keys count: 747
    Rollup mutation results distinct keys: 747
    hpjj44 production keys count: 747
    b1mx2w reach keys count: 747
    res_keys == hpjj44_keys: False
    set(res_keys) == set(hpjj44_keys): True
    set(res_keys) == set(reach_keys): True

    Verdicts in Rollup mutation results:
    budget-exhausted: 319
    guarded: 30
    pin-retired: 5
    property-unidentifiable: 3
    unguarded: 2
    unguarded-unreached: 387
    unprovable: 1
    Total: 747

    Non-probe classes:
    pin-retired: 5
    property-unidentifiable: 3
    key-gone: 0
    unguarded-unreached: 387
    Total non-probe: 395
    To-probe evaluated or budget-exhausted: 352
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: for one `guarded` and one `unguarded` row (or a statement that a class did not occur), the pasted survivor and control JSONs produced by `tools/mutation_probe.py` `main`, with the `unguarded` row's collect-only preflight line and its selection showing an explicit path argument; pasted `python3 -c` check over all saved JSONs that every row's survivor/control verdicts match its JSON and every JSON `head` is the same HEAD; pasted `git status --short` and `git worktree list` before and after the batch.
  - Observed evidence:
    Pasted survivor JSON for guarded row `agent_workflows/benchmark_scorer.py::_detect_ground_truth_violations`:
    ```json
    {
      "baseline_failing": 0,
      "checkout_status_changed": [],
      "extra_tests_overwrote": [],
      "flaky": [],
      "head": "f13aea8d61806a50a338faf216e3312b48865ac7",
      "mutant_failing": 6,
      "newly_failing": [
        "tests.test_benchmark_runners_reports::test_baseline_comparison_and_regression_triage",
        "tests.test_benchmark_runners_reports::test_benchmark_reports_generation_and_formatting",
        "tests.test_benchmark_runners_reports::test_ci_safe_offline_benchmark_runner",
        "tests.test_benchmark_runners_reports::test_metrics_computation_and_proportions",
        "tests.test_benchmark_runners_reports::test_paired_comparison_computes_deltas_and_rejects_incompatible",
        "tests.test_benchmark_runners_reports::test_runner_doubles_all_eight_outcomes"
      ],
      "newly_failing_total": 6,
      "operator": "return-none",
      "reason": null,
      "selection": [
        "-m",
        "not slow and not livecorpus",
        "tests/test_benchmark_runners_reports.py"
      ],
      "target": "agent_workflows/benchmark_scorer.py::_detect_ground_truth_violations",
      "verdict": "killed",
      "wall_s": 4.75
    }
    ```
    Preflight collect-only for unguarded row `agent_workflows/check_engine.py::check_system_layout`:
    ```
    $ python3 -m pytest -o addopts= -q --collect-only -m "not slow and not livecorpus" tests/test_check_engine.py tests/test_check_engine_from_spec_missing.py tests/test_check_engine_release_gate.py tests/test_check_engine_source_test_citation.py tests/test_checkup.py tests/test_collision_population_parity.py tests/test_doctor.py tests/test_doctor_diagnostic_severity.py tests/test_sanitizer_severity_vocabulary.py
    218 tests collected in 1.32s
    ```
    Pasted survivor JSON for unguarded row `agent_workflows/check_engine.py::check_system_layout`:
    ```json
    {
      "baseline_failing": 0,
      "checkout_status_changed": [],
      "extra_tests_overwrote": [],
      "flaky": [],
      "head": "f13aea8d61806a50a338faf216e3312b48865ac7",
      "mutant_failing": 0,
      "newly_failing": [],
      "newly_failing_total": 0,
      "operator": "return-none",
      "reason": null,
      "selection": [
        "-m",
        "not slow and not livecorpus",
        "tests/test_check_engine.py",
        "tests/test_check_engine_from_spec_missing.py",
        "tests/test_check_engine_release_gate.py",
        "tests/test_check_engine_source_test_citation.py",
        "tests/test_checkup.py",
        "tests/test_collision_population_parity.py",
        "tests/test_doctor.py",
        "tests/test_doctor_diagnostic_severity.py",
        "tests/test_sanitizer_severity_vocabulary.py"
      ],
      "target": "agent_workflows/check_engine.py::check_system_layout",
      "verdict": "survived",
      "wall_s": 114.45
    }
    ```
    Pasted positive control JSON for `agent_workflows/check_engine.py::check_system_layout`:
    ```json
    {
      "baseline_failing": 0,
      "checkout_status_changed": [],
      "extra_tests_overwrote": [],
      "flaky": [],
      "head": "f13aea8d61806a50a338faf216e3312b48865ac7",
      "mutant_failing": 11,
      "newly_failing": [
        "tests.test_cli_layout.SystemLayoutRuleStateTests::test_a_clean_installed_workspace_reports_nothing",
        "tests.test_cli_layout.SystemLayoutRuleStateTests::test_a_missing_schema_sibling_reports_missing",
        "tests.test_cli_layout.SystemLayoutRuleStateTests::test_a_repo_with_no_aw_workspace_reports_nothing",
        "tests.test_cli_layout.SystemLayoutRuleStateTests::test_a_schema_invalid_document_reports_drift",
        "tests.test_cli_layout.SystemLayoutRuleStateTests::test_a_version_mismatched_document_reports_drift",
        "tests.test_cli_layout.SystemLayoutRuleStateTests::test_a_wrong_schema_version_reports_drift",
        "tests.test_cli_layout.SystemLayoutRuleStateTests::test_an_installed_workspace_missing_the_document_reports_missing",
        "tests.test_cli_layout.SystemLayoutRuleStateTests::test_an_unparseable_document_reports_drift",
        "tests.test_cli_layout.SystemLayoutSurfaceWiringTests::test_doctor_reports_the_same_finding",
        "tests.test_cli_layout.SystemLayoutSurfaceWiringTests::test_the_rule_does_not_fire_per_record_type",
        "tests.test_cli_layout.SystemLayoutSurfaceWiringTests::test_the_rule_rides_the_full_check_sweep"
      ],
      "newly_failing_total": 11,
      "operator": "return-none",
      "reason": null,
      "selection": [
        "tests/test_cli_layout.py"
      ],
      "target": "agent_workflows/check_engine.py::check_system_layout",
      "verdict": "killed",
      "wall_s": 160.06
    }
    ```
    Pasted `python3 -c` check over all saved JSONs:
    ```
    Total probe JSON files: 35
    Distinct HEADs across all JSONs: {'f13aea8d61806a50a338faf216e3312b48865ac7'}
    Verdict mismatches between JSONs and table: []
    All 35 JSON verdicts match table: True
    All JSONs share identical HEAD: True
    ```
    `git status --short` and `git worktree list` before and after:
    Before:
    `git status --short`:
    (empty)
    `git worktree list`:
    ```
    .                                                                                    dd036d7fc [main]
    .aw/worktrees/gradfix-review                                                         199437f35 [review/gradfix-plan-review]
    .aw/worktrees/.aw-isocommit-ercg9nlx                                                 0d17632a9 (detached HEAD)
    .aw/worktrees/askmefix                                                               188bee05a [aw/askmefix]
    .aw/worktrees/er11a0                                                                 dd036d7fc [aw/lane/er11a0]
    .aw/worktrees/hguae9                                                                 541e85557 [aw/lane/hguae9]
    .aw/worktrees/nwporz                                                                 a0b074226 [aw/lane/nwporz]
    .aw/worktrees/pytest-speed-20261015                                                  ad9213cc6 [codex/pytest-speed-20261015]
    .aw/worktrees/review-sweep-run-20261015T224817Z-205920                               23863c32a [aw/lane/review-sweep-run-20261015T224817Z-205920]
    .aw/worktrees/review-sweep-run-20261016T143713Z-1719552                              653969dfb [aw/lane/review-sweep-run-20261016T143713Z-1719552]
    .aw/worktrees/rf1xxr                                                                 f13aea8d6 [aw/lane/rf1xxr]
    .aw/worktrees/test-pruning-prompts                                                   eca2e2211 [work/test-pruning-prompts]
    .aw/worktrees/xvlemm                                                                 c30509a2e [aw/lane/xvlemm]
    ```
    After:
    `git status --short`:
    (empty after doc commit e69136a40)
    `git worktree list`:
    (zero leftover disposable worktrees).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `## Rollup mutation totals` with the sum shown as 747; pasted `aw commit` output and `git show --stat HEAD` listing only the findings doc.
  - Observed evidence:
    Pasted `## Rollup mutation totals`:
    ```
    Summary of mutation probe outcomes across the 747 rollup candidate keys:

    | Final Verdict | Count | Description |
    |---|---:|---|
    | `pin-retired` | 5 | Pin-retired per hpjj44 classification; carrier-free |
    | `property-unidentifiable` | 3 | Property unidentifiable per hpjj44 classification; operator n/a |
    | `key-gone` | 0 | Subject function or module no longer exists at HEAD |
    | `unguarded-unreached` | 387 | Unreached by routine non-slow test suite at baseline HEAD |
    | `guarded` | 30 | Mutation killed by surviving test suite |
    | `unguarded` | 2 | Mutant survived surviving test suite but killed by positive control deleted test |
    | `unprovable` | 1 | Survivor errored/timed out, or positive control failed to kill mutant |
    | `budget-exhausted` | 319 | Unprobed keys stopped after cumulative probe wall time reached cap |
    | **Total Evaluated Keys** | **747** | Sum of all evaluated rollup candidate keys |

    - **Total Probe Wall Time**: 10833.66s (3.01h)
    ```
    Pasted `aw commit` output:
    ```
    aw commit rf1xxr -m "work(rf1xxr): mutation-probe reached rollup properties on bounded budget" -- .aw/records/research/20261016-trimcarry-01-b1mx2w-rollup-reach.findings.md
    aw: invoked in checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/rf1xxr but imported agent_workflows from /mnt/md1/VC/agent-workflows; re-running with /mnt/md1/VC/agent-workflows/.aw/worktrees/rf1xxr's package (set AW_NO_REEXEC=1 to disable)
    aw commit: committed 1 path(s): e69136a40e18387f4a1d89f8b89362cf843a72a1
    ```
    Pasted `git show --stat HEAD`:
    ```
    commit e69136a40e18387f4a1d89f8b89362cf843a72a1 (HEAD -> aw/lane/rf1xxr)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 16 22:30:23 2026 -0400

        work(rf1xxr): mutation-probe reached rollup properties on bounded budget

        AW-Run: run-20261016T221501Z-3469718
        AW-Item: rf1xxr
        AW-Runner: aw agy run

     ...16-trimcarry-01-b1mx2w-rollup-reach.findings.md | 876 +++++++++++++++++++++
     1 file changed, 876 insertions(+)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Order 03 (`8dyt88`) is `executed` and its doc carries `## Key reach`. Every mutant runs only inside `tools/mutation_probe.py`'s disposable worktree; probe JSON goes under the gitignored `.aw/state/`. Scope fence: `- Scope-Paths:` declares only the Set's findings doc; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command whose numbers enter the doc; never record a verdict you did not run. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
