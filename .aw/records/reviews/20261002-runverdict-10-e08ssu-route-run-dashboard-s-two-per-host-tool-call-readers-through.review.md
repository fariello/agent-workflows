# Review findings: plan e08ssu

- Subject-Id: e08ssu
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `147c37f47`. The pending plan matched the lane input byte for byte and was already committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` both report `clean`. `- Kind: child`, so `IPD-S407` does not apply.

THE DESIGN IS SOUND AND THE KEY MEASUREMENTS REPRODUCE. I re-ran the disagreement shapes through both public entry points.
- F-07: a padded `" bash "` / `" run_command "` gives `['python3 -m pytest']` from `extract_session_commands`, but `session_stats` gives `tools={' bash ': 1}`, `categories={'shell': 1}`, `commands={}`.
- F-08: a blank command gives `missing=1, commands=[]` from one reader and `commands={'other': 1}` from the other, on both hosts.
- F-09: `subagent`/`invoke_subagent` give delegation 1 but category `other`.
- F-10: an ambiguous line is read as agy by both (`git log`).
- F-14: `FAILED` is counted by neither.
- F-12: `verifier_corroboration` imports no first-party module.
- F-04/F-05: confirmed by reading `_record_tool`'s signature and `ObservedCommand`.
- Fixtures: there are 11.
- Carriers: `1kebul` and `iuhx9d` are `bug` items carrying `Blocks-Release: next`. `8fiybc` is a `chore`. All three are already filed.
- The in-scope tests pass: `51 passed`.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G (internal consistency) | Plan E-01 field list ("seven fields") vs E-03 `command_missing` | E-01 declares seven fields, then E-03 adds an eighth (`command_missing`). V-01 demanded "all seven". An executor following E-01 literally builds a record that E-03 must reshape. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now declares eight fields, with `command_missing` defaulting to False until E-03. V-01 now says eight. |
| PR-002 | MEDIUM | IN-SCOPE | C / E (performance) | `run_dashboard._oc_line`; review interleaved timing on a 1.3 MB, 6000-line log | Review re-measured on a loaded machine. A frozen dataclass costs 2.3 us (the plan recorded 1.25), against 0.83 us for a `NamedTuple`. An interleaved simulation of the E-06 routing with a frozen dataclass came in at +7.1%. That is inside the 10% bar but narrow. Separate, non-interleaved best-of-5 timings drifted by more than 10%, so V-06's protocol could fail spuriously, or pass spuriously. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now specifies a `typing.NamedTuple`. V-06 now requires best-of-15 with old and new readers interleaved in one process. E-06 records both sets of measurements. |
| PR-003 | MEDIUM | IN-SCOPE | A / Evidence accuracy | `agent_workflows/stall_progress.py` `'"invoke_subagent"'` tuple and docstring | F-09 and E-04 claim the two extra delegation spellings have "NO in-tree exemplar", found "only in these two tables". `invoke_subagent` is in fact matched by `stall_progress` as a real agy background-task tool name. The docstring E-04 mandates would therefore record a false statement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09, E-04 and V-04 are corrected: `invoke_subagent` has one in-tree reference, `subagent` has none, and neither appears in a fixture. OQ-01's conclusion is unaffected; widening is still correct. |
| PR-004 | MEDIUM | IN-SCOPE | A / D (cache invalidation, behavior accounting) | `_StatsCache` `(size, mtime_ns)` check; plan E-04, OQ-02, F-13, Required tests | The plan calls E-04 "the ONE behavior change" and says the schema bump is required "by THIS item specifically and by no other". But E-02 changes the cached `tools` key and E-03 changes the cached `commands` histogram for an unchanged log once E-06 routes the dashboard. Both are stale-cache hazards too. Required tests also expected an existing dashboard case to change for `subagent`, but none of the existing cases uses any of the changed shapes. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04, OQ-02, F-13 and Proposed changes now list all three dashboard-visible changes, and say one bump to 3 covers them. Required tests, E-06 and V-06 now expect no edit to any pre-existing dashboard case. |
| PR-005 | MEDIUM | IN-SCOPE | E (test feasibility) | `agent_workflows/__init__.py` imports `versioning` and `_compat`; review subprocess measurement | E-07/V-07's import-purity check asserted that `verifier_corroboration` is the only `agent_workflows.*` key in `sys.modules`. It cannot pass, because the package `__init__` loads `agent_workflows._compat` and `agent_workflows.versioning`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The check is now a delta: import the package first, then assert the newly added keys are exactly `{'agent_workflows.verifier_corroboration'}`. Review measured exactly that set. |
| PR-006 | LOW | IN-SCOPE | E (live-artifact convention) | E-07 Expected outcome | E-07 named "the suite's pre-existing three failures" as the bar, which is an authoring-time live count. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Failing node ids must now be a subset of the executor's own pre-E-01 baseline. |
| PR-007 | LOW | IN-SCOPE | G (contradiction) | Scope check Under-scope (b) vs Approval gate | Under-scope said each deferred shape "carries a new backlog item the executor must file", while the gate says the items are already filed and the executor files nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Under-scope now names `1kebul`, `8fiybc` and `iuhx9d` as already filed. |
| PR-008 | LOW | IN-SCOPE | G (execution contract) | `.aw/records/plans/README.md` finalize paragraph | The gate's human-driven path said `aw ipd set executed` with no `--actor`, and that form refuses. The README names `aw ipd finalize ... --actor ... --apply` as the supported path. A related gap: the plan did not say a non-string command must keep today's `str()` form, which E-05's byte-identical contract depends on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now gives the `aw ipd finalize` form and notes that `set executed` delegates and needs `--actor`. E-01 and V-01 now pin the `str(value)` form (measured: `"['a', 'b']"` from both readers). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Which record type should `ToolCall` be? | `typing.NamedTuple` | Frozen dataclass, as authored: rejected, about 2.8x the construction cost on the hot path, which consumes most of the 10% headroom. A slots dataclass gave no gain (measured +8.4% vs +7.1%). A mutable dataclass is faster but loses immutability. | Review timing: NamedTuple 0.83 us, frozen 2.3 us, mutable 0.62 us; interleaved simulation +7.1% | yes |
| D-2 | One schema bump, or one per behavior-changing item? | One bump, 2 to 3, covering E-02 through E-04 | A bump per item: rejected, since all three ship in one plan and the cache is disposable (one re-parse). | `_StatsCache` schema gate; the module docstring's "Deleting it costs one re-parse" | yes |
| D-3 | Should E-01 keep today's `str()` coercion of a non-string command? | Yes, preserve it | Treat a non-string command as missing: rejected, because it would change `extract_session_commands` output, which F-11 freezes. | Review probe: both readers coerce `["a","b"]` to `"['a', 'b']"` | yes |
