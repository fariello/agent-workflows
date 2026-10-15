# Review findings: plan 3a3hh9

- Subject-Id: 3a3hh9
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `094f7a617`. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`, 0 findings. Not an
orchestrator.

Re-measured at HEAD with a scratch root under the lane's gitignored `.aw/state/` holding `.aw/records/`
and a header appended through `RunLedgerStore.append` at `state_root(root)/run-abcdef1234/ledger.jsonl`:
`format_run_human` returned `'run-abcdef1234\n  0 steps: 0 steps'` (F-01 MATCH); the explicit directory
and `ledger.jsonl` tokens both came back unresolved from `resolve_target_runs_detailed` while the bare name
resolved (F-03 MATCH); after `step_started` S-01, `_reconstruct_workflow_from_ledger` returned only the
`step_attempt`-backed ids (F-02 MATCH). With the widening simulated, the reconstruction gave S-01
`performed` attempts 1, S-02 `running` attempts 0, run `running`, counts `{performed: 1, running: 1}`,
which is exactly what the plan's E-05 progressed case expects. `read_records` on an empty file returned `[]`,
raised `NotALedgerError` on `{"event": "not_a_ledger"}` and `UnparseableLineError` on invalid JSON, and a
pure read created no `.lock`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric D (anti-regression, unexplained behavior change) | `agent_workflows/run_cli.py` `_build_engine` (`workflow = _reconstruct_workflow_from_ledger(records)`) | E-01 edits a helper every ledger leaf uses without `--workflow`, and the plan framed it as viewer-only. Probe (ledger = header + `step_started` S-01, no `--workflow`): before, `runs status` `"steps": {}`, `runs resume` exit 0 `unknown_outcome_steps: []`, `run record --state performed` exit 2 `unknown step`; with the widening simulated, `status` lists S-01 running, `resume` exit 3 `unknown_outcome`, `record` exit 0. Running the three relevant test modules with the widening injected as a pytest plugin: 106 passed, so nothing pins either behavior. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now names the three ledger-leaf changes as expected; OQ-03 records why they are correct (`run_recovery` defines a started step with no terminal attempt as unknown outcome); new E-08/V-08 pins them in `tests/test_run_recovery_cli.py` (added to Scope-Paths); F-05 added. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric A (correctness) | `agent_workflows/run_viewer.py` `inspect_run_pid_and_runtime` (`re.search(r"-(\d+)$", run_dir.name)`) | The draft E-02 called `inspect_run_pid_and_runtime` for ledger runs. Its PID fallback reads trailing digits of the directory name, and a valid ledger id `run-<hex>` can be all digits: probe returned `pid=12345678` for `run-12345678`, so `aw runs` would print a phantom driver PID (or `live` if that PID exists). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and the proposed code set `pid`/`pid_state` to `None`, `is_live=False`, and compute runtime from the ledger timestamps; E-05 (e) tests it; F-07 added. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (test environment) | `agent_workflows/runner_shared.py` `state_root` | Tests placing a ledger at `state_root(root)` in a bare temp root write OUTSIDE it (probe: resolved under `$HOME`), which the live-runs guard does not catch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions, E-05, E-06 and section 5 require `<root>/.aw/records/`; F-06 added. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (executability) | `agent_workflows/run_viewer.py` `resolve_target_runs_detailed` | The proposed snippet used `matched`/`target_matched`, names that do not exist in the function (it uses `seen`/`resolved`/`continue` and an analytics refusal per branch), so it could not be applied as written and risked dropping the analytics guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section 3 now widens only the two membership tests and keeps each existing body; V-03 runs `AnalyticsIsolationTests` and `UnresolvableTargetRefusalTests`. |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric G (verification checklist) | plan E-05 and V-01..V-05 (draft) | No reproduce step, no failing-before demonstration, V-items keyed on test function NAMES (artifacts of test organization, not a bar), and V-05 demanded the bare suite while no E-item ran it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-06/V-06 reproduce at HEAD; E-05/E-08 require failing-before output; V-items now demand behaviors and name test ids only as non-binding pointers; new E-09/V-09 runs the bare suite and `aw sanitize`. |
| PR-006 | MEDIUM | OVER-SCOPE | Rubric F (KISS, traceability) | plan E-03 (draft) `or (p / "execution-report.md").is_file()` | Widening explicit DIRECTORY resolution to `execution-report.md`-only driver directories is not traceable to `nf84rt` and changes which driver directories an explicit path reaches. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed from Scope, E-03 and section 3; recorded under Deferred with reason. |
| PR-007 | MEDIUM | IN-SCOPE | Rubric G (right-sizing) | plan E-03 (draft) | E-03 bundled two independent deliverables in different regions of `run_viewer.py` with separate test surfaces: explicit-path resolution and the three CLI filter predicates. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split: E-03 resolver, new E-07/V-07 filters. |
| PR-008 | LOW | IN-SCOPE | Rubric C (failure handling) | `agent_workflows/run_ledger_store.py` `NotALedgerError`, `LedgerCorruption` | The draft caught bare `Exception` around the ledger read and reconstruction, which would silently hide a programming error as `unreadable_state`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both `except` clauses narrowed to `NotALedgerError`, `LedgerCorruption`, `OSError`; V-02 checks it. |
| PR-009 | LOW | IN-SCOPE | Rubric G (deferral accuracy) | `.aw/records/backlog/graduated/20261012-runledger-01-sflov4-workflow-not-persisted.backlog.md` (`Status: graduated`); sibling `o34rb3` | Deferred section called `sflov4` "open backlog" and `wf.json`; it is graduated to sibling `o34rb3`, which persists `workflow.json`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Deferred entry now names `o34rb3` and `workflow.json`; also records the untouched aggregate views and `4d3ynu`. |
| PR-010 | LOW | UNDER-SCOPE | Rubric G (execution contract, docs) | plan Approval gate (draft); `CHANGELOG.md` | The gate lacked the scope-fence declaration, the paste-the-output rule, path-scoped `aw commit`/never-push, and conditional runner/executor finalize ownership; and a user-visible `aw runs` change had no CHANGELOG line or spec/doc rationale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all elements; E-09 adds the CHANGELOG line (Scope-Paths extended); Spec/doc sync states why no spec or contract-doc edit is needed. |

`IPD-Z602` (info) remains on E-05 after revision: it is one deliverable (one test class over one fixture
shape) and was not split further. `aw ipd lint --phase review-finalize`: clean; `aw sanitize --agent`: clean.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep E-01's ledger-leaf side effect, or confine the widening to the viewer? | Keep it in the shared helper and pin it (E-08). | A viewer-private copy of the reconstruction (REJECTED: two reconstructions of one ledger would disagree, and the current `resume` exit 0 hides an unknown outcome); dropping E-01 (REJECTED: the viewer would omit started steps). | `run_recovery` module docstring ("a started step ... with no terminal `step_attempt`) is an explicit `unknown_outcome`"); F-05 probe. | yes |
| D-2 | What PID does a ledger run report? | `None`; runtime from ledger timestamps. | Call `inspect_run_pid_and_runtime` (REJECTED: phantom PID, F-07). | `run_viewer.inspect_run_pid_and_runtime`; probe. | yes |
| D-3 | Keep the `execution-report.md` explicit-directory widening? | Remove it. | Keep (REJECTED: not traceable to `nf84rt`). | backlog `nf84rt` body. | yes |
| D-4 | Do the aggregate views (`--summary-only`, `--latest-only`, `--issues`, multi-run summary) need ledger handling? | No; leave them defined over driver steps. | Add ledger rows (REJECTED: redesign beyond `nf84rt`, and zero driver steps is a true statement). | `run_viewer.build_multi_run_summary_dict` iterates `s.steps`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
