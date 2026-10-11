# Review findings: plan iksylm

- Subject-Id: iksylm
- Subject-Type: ipd
- Reviewed-At: 2026-10-11
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `69d6026db`. The plan was committed and byte-identical to the lane input, so
no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean` before review. `- Kind: child`,
so S407/S408 do not apply.

Evidence re-checked: spec `25kzda` 4.1 ("Exhaustive `ABORT RUN` set", one row "Corrupt run ledger"), 5.5 groups (a)/(b)/(c)
and its 21-row mapping table, 5.6 exit-code table (exit-4 row), 5.7; `run_evidence.ABORT_CLASSES = ("Corrupt run ledger",)`;
`runner_shared.build_fix_it_notice`, `FIX_IT_RULE_TEXT`, the per-kind counter keys, `cascade_dependency_blocked`,
`NEEDS_INPUT_KEY`, `run_exit_code`, `load_json`, `assert_child_tool_identity`; `render_stream.render_run_summary_table`
proposal lines; `oc_runipd.run_queue` `except ToolIdentityError: ... raise`; `oc_runipd.main` `except DriverError` -> 2;
sibling plans `lxb1ew` (criteria 1-6), `tha7a6` E-03 (executed), `mcbph5` E-01..E-05 (executed), `ytas91` (approved, not
executed), `w9nvq4` and `psgyzw` (executed), `62sdwr` (reviewed); helper modules `tests/test_production_correction_turn.py`
(`_HOSTS`, `_patch_host_agent`, `run_queue`) and `tests/test_silent_turn_observability.py` (`fake_opencode`).

Measured at review (scratch git repos under the gitignored `.aw/state/`, removed afterwards): an unparseable `state.json`
passed to `oc_runipd.main(["resume", <run_dir>, "--repo", <repo>])` and to `agy_runipd.main(...)`:

```text
runipd: Invalid JSON in .../.aw/state/runs/run-x/state.json: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
oc EXIT 2
agy EXIT 2
```

Existing children's modules pass at this HEAD: `python3 -m pytest tests/test_production_correction_turn.py
tests/test_hook_and_suite_fix_it.py tests/test_scope_exceeded.py` -> `26 passed in 17.22s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (E-03) | `tha7a6` E-03 Expected outcome: "A `fail-gate` carrying an `awaiting-human-decision` refusal and `needs_input` set, C dependency-blocked ... the run exiting 3"; `runner_shared.cascade_dependency_blocked` | E-03 asserted A is `needs-human` and B is `dependency-not-met`. Neither is an item status the runner writes (`tha7a6`'s own review measured this), so the assertion is unsatisfiable as written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now asserts `fail-gate` + `awaiting-human-decision` + `NEEDS_INPUT_KEY`, B `dependency-blocked`/`fail-depend` with no session, exit 3, record on main, lane tip not on main, and the summary's `proposal:` line first. F-03 added. V-03 demands each value per host. |
| PR-002 | HIGH | IN-SCOPE | Reachability (E-04) | Measured above (exit 2); spec 5.6 exit-4 row "neither driver returns this row's `4` through `run_queue`"; `runner_shared` comment "NO driver run writes one (no `ledger.jsonl`"; `runner_shared.load_json` | E-04 demanded "the run aborts with the ledger reason". A driver run has no ledger and no run-wide abort path for corrupt state: it fails before dispatch with a generic `DriverError` exit 2. The demanded observation has no code path. | Overall:Low | FIXED | Rewritten to the observable behavior: corrupt `state.json` via `resume` dispatches nothing and exits nonzero naming `state.json` (measured 2); exit 4 not asserted; the gap is recorded in E-05. F-04 added. |
| PR-003 | HIGH | IN-SCOPE | Consistency with orchestrator (E-04, E-05) | `lxb1ew` criterion 4 "must NOT be reported as 'only a corrupt ledger aborts' while [03y5g6] is open" and criterion 5; `oc_runipd.run_queue` `except ToolIdentityError` ... `raise` | E-04's expected outcome "only the corrupt-ledger run aborts" is the exact claim the orchestrator forbids, and the plan did not mention the tool-identity divergence at all. | Overall:Low | FIXED | E-04 (c) asserts the shipped tool-identity abort labelled as the `03y5g6` divergence; E-05 records it as the one named divergence; Concern, Deferred (carrier `03y5g6`) and F-05 updated. |
| PR-004 | MEDIUM | IN-SCOPE | Feasibility (E-04 push; E-05) | Spec 5.5 table rows "a push" ("Detection is unbuilt") and "verifier transport failure" (`verifier-transport-error`, "Implementing: Order 04 (`ytas91`)"); no `verifier-transport-error` in `runner_shared`; `ytas91` text never mentions transport; `aw find` for `k8n97m`, `120bhh`, `b8w5o6`, `5j73i6` -> no artifact | E-04 required driving a "push recorded" run, which nothing can produce. E-05's "no gaps" target is unreachable: the table has unbuilt rows and four owner ids that resolve to nothing, and this plan may not edit the spec. | Overall:Low | FIXED | Push recorded as undrivable (carrier `oq05nc`). E-05 now covers every row with a case or a gap reason, names the expected gaps and stale ids, and files a `bug`, `Blocks-Release: f33nrj` backlog item per uncarried gap. F-06 added; Deferred lists the carriers. |
| PR-005 | MEDIUM | IN-SCOPE | Executability / P16 (E-01, E-02) | `tests/test_production_correction_turn.py` `_HOSTS`, `_patch_host_agent`, `mod.run_queue(run_dir, retry_incomplete=False)`; counter keys `TURN_RETRY_COUNT_KEY`, `HOOK_FINALIZE_RETRY_COUNT_KEY`, `HOOK_INTEGRATION_RETRY_COUNT_KEY`, `COMBINED_RED_RETRY_COUNT_KEY` | "Drive a real `aw oc run`" cannot be done with a scripted host from a CLI subprocess; "exactly one correction spent" did not say which counter, though each kind has its own; E-02's "cross-check that Orders 04 to 07 use `build_fix_it_notice`" invited a source grep (P16). | Overall:Low | FIXED | E-01 names `run_queue` on both hosts, a tempfile scratch repo, fixture reuse from the children's modules, and the per-kind counter with others 0. E-02 asserts `prompt.count(FIX_IT_RULE_TEXT) == 1` and states the behavioral check is the cross-check, with no source reads. F-07 added. |
| PR-006 | MEDIUM | IN-SCOPE | Validation evidence | V-01..V-06 original text ("paste the module run", "or the asserting test output") | Several V-items let a passing summary stand in for the per-kind and per-host values, so an executor could claim completion without showing them. | Overall:Low | FIXED | Every V-item now demands the specific values per kind and per host, re-derived at execution, with test names as non-binding pointers. |
| PR-007 | MEDIUM | IN-SCOPE | Baseline (E-06) | `git log`: `dcd0d56a4` (authored Set fixfirst) parent `03ddbcb83`; `tb6lw3`'s first integration `e85431eae` first parent `a76fe9fc7`; `lxb1ew` Concern "Measured 2026-10-07 at HEAD `03ddbcb83`" | "the parent of `tb6lw3`'s first commit" is ambiguous (lane commit vs integration) and resolves to a commit that already contains other children's changes. | Overall:Low | FIXED | Baseline pinned to `03ddbcb83`, reproduced in a disposable worktree; V-06 says a failure that passes at baseline is a regression. |
| PR-008 | LOW | UNDER-SCOPE | Execution contract | Original gate: "Commit only the Scope-Paths ...; never push. Paste actual runner output" | No lifecycle ownership, no handling for the backlog items E-05 must file or the allowed one-line fix (both outside Scope-Paths), no defect stop rule, no dependency status note. | Overall:Low | FIXED | Gate now carries the scope fence (justify out-of-scope writes with `--scope-reason`, no stop directive), honesty rule, path-scoped commit and never-push, runner-owned finalize, and dependency status. Scope check gains the defect rule. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should E-04 assert for the corrupt-ledger run, given driver runs have no ledger? | The observed behavior: no dispatch, nonzero exit naming `state.json` (measured 2); record the missing exit-4 path as a gap. | (a) Keep "aborts with the ledger reason": rejected, unreachable. (b) Add the abort path here: rejected, plan excludes production changes. | Measurement above; spec 5.6 exit-4 row. | yes |
| D-2 | How to treat the tool-identity abort? | Assert the shipped abort as the one named divergence. | Assert it does not abort: rejected, false until `03y5g6` lands. | `lxb1ew` criteria 4 and 5; `oc_runipd.run_queue`. | yes |
| D-3 | Who files the spec-table gaps? | E-05 files a backlog item per uncarried gap at execution. | Edit the spec here: rejected, this plan only measures. Decide the list now: rejected, final only after the table is built. | Plan Scope "EXCLUDES changing any production behavior"; spec is approved. | yes |
| D-4 | Which commit is the Set baseline? | `03ddbcb83`, parent of the Set's authoring commit. | `a76fe9fc7` (first parent of tb6lw3's integration): rejected, already contains other children's changes. | `git log` above. | yes |
