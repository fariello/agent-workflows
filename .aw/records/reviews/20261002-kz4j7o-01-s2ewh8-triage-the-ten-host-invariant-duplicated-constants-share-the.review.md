# Review findings: plan s2ewh8

- Subject-Id: s2ewh8
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `ca03f0c56`. The plan was committed (`cf9267454`, authoring only; no code landed) and byte-identical to the sealed lane input (rev-7); no snapshot needed. `- Kind: child`, so `IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author` clean before review.

Re-verified at HEAD: all ten names still defined in both hosts; `OUTPUT_MODES`, `_ID_RE`, `_STATUS_RE`, `_close_process_streams` have no reader (`git grep` hits are only the defining lines, unrelated same-named regexes in other modules, and a docstring mention in `tests/test_runner_shared.py`); `agy_runipd` uses `re.` only at the two compiles, `oc_runipd` also at `re.search(r'"model"...`; `DEFAULT_RUNBOOK_TEXT` equal across hosts (667 chars) and absent from `runner_shared`; `LANE_PROMPT_TIMEOUT` 180.0 on both hosts, absent from `runner_shared`, equal to `GATE_PROMPT_TIMEOUT`; `runner_shared.DEFAULT_STALL_TIMEOUT` exists at 900.0 and the hosts hold distinct shadows; grace pair 5.0/2.0 on both hosts and absent from `runner_shared`; `tests/test_oc_runipd.py` rebinds `driver._SIGINT_GRACE_SECONDS`; `test_question_timeouts_are_180s` and `LanePromptSuppressionTests` exist; the host-vs-host sweep is as quoted; `ruff --select F401,F821` passes on both hosts; `tools/ipdrunner/test_runagy.py` is `11 failed, 14 passed` at HEAD; `sznlsf` still approved.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E validation / live baseline | E-02 "The bare suite count is UNCHANGED"; F-11 three failures; commit `8c460a9a1` "Fix baseline test failures on main (spec scope length, readiness invariant, reachability test, selector containment test)" | E-02's bar was a passed count (an artifact of test organization), and the three named baseline failures were plausibly fixed after authoring, so an executor could misattribute or mis-match. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02, V-02 and Required tests now compare by failing node-id set against an execution-time baseline; F-11 notes `8c460a9a1` may have removed the three. |
| PR-002 | LOW | IN-SCOPE | Evidence staleness | `b02ohu` and `76ic0k` are in `.aw/records/plans/executed/` | The plan called both "approved" siblings still removing AST walks; both have executed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every mention now reads "executed sibling". |
| PR-003 | MEDIUM | IN-SCOPE | G execution contract / scope fence | Scope check "IF AN EXECUTOR FINDS IT MUST EDIT `tests/test_runner_shared.py`, STOP"; gate "STOP if the fix appears to require ... editing `tests/test_hostdedup_third_host.py`"; gate "move this plan ... through the tooled transition" | Out-of-scope-edit STOP directives contradict the 2026-09-01 scope-fence ruling; lifecycle ownership (runner vs hand) and the backlog close were unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both converted to declarations justified with `--scope-reason`; `HostLabels` kept as a design prohibition recorded as a deferred question; gate names runner ownership, hand `aw ipd begin`/`finalize s2ewh8`, `--scope-ack`, and the `kz4j7o` close. The two genuine-hazard STOPs (reader found, host values diverge) and the no-AST STOP are kept. |
| PR-004 | LOW | UNDER-SCOPE | D anti-regression | `tools/ipdrunner/runagy.py` "for _k, _v in vars(agy_runipd).items()"; `tools/ipdrunner/test_runagy.py` bare `re.search` calls | Removing `agy_runipd`'s `import re` also removes `re` from the shim's re-exported globals; E-03 did not ask whether anything reads it there. Measured: those `re.search` calls are inside a generated script with its own `import ... re`, so no reader exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires the shim check and records the review measurement. |
| PR-005 | LOW | IN-SCOPE | Documentation honesty | `tests/test_runner_shared.py` `test_codefined_constants_host_vs_host_equality` docstring "Non-UPPER_CASE co-defined symbols (such as _close_process_streams)" | Deleting `_close_process_streams` makes that docstring example stale; the file is undeclared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 notes the stale example, allows leaving it, and requires `--scope-reason` if corrected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep the `HostLabels` STOP as a stop? | Convert to a prohibition plus deferred question | keep STOP (contradicts scope-fence ruling); drop entirely (loses F-07 design guard) | plan-review Step 4 scope-fence wording; F-07 | yes |
| D-2 | Declare `tests/test_runner_shared.py` to fix the stale docstring? | No; note it and allow a justified out-of-scope edit | add to Scope-Paths (widens a high-contention file for prose only) | docstring is not asserted; P16 | yes |
