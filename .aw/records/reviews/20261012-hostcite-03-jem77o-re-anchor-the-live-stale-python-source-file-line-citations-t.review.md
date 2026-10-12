# Review findings: plan jem77o

- Subject-Id: jem77o
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `d63a85cc5`. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author` and `--phase review-finalize` were clean; the info-level `IPD-C801` hits are the stale offsets the plan quotes in order to delete them, and `IPD-Z602` on E-02 is judged a single concern (five comment rewrites, one pass, one V-item; D-2).

Re-verified at review HEAD:
- All eight cited sites exist as quoted (`agy_runipd.py` "`oc_runipd.py:8766`", "`oc_runipd.py:8645`", "`oc_runipd.py:8834`"; `runner_shared.py` "`ipd_lifecycle.py:3989`", "`cli.py:8487-8512`"; `selectors.py` "`status_set.py:132-133`"; `tests/test_oc_runipd.py` "`oc_runipd.py:4823`"; `tests/test_runner_shared.py` "`oc_runipd.py:3477-3478`", "`agy_runipd.py:2190`").
- Every replacement anchor resolves: `oc_runipd.run_queue` comment "`register_signal_report` is called again after each state reload so the report never runs off a stale snapshot" precedes its first `register_signal_report(run_dir, state)`, and a `register_signal_report` follows `retry_deferred_integrations(run_dir, state, poll=True, ask=True)` inside `run_queue`; `ipd_lifecycle._complete_after_commit` carries "# Consume the begin receipt"; `cli._find_type_records` carries "# All other types"; `status_set._ID_RE`/`_STATUS_RE` match `^-\s*Id:`/`^-\s*Status:`; `plan_repo = Path(work_dir) if work_dir else repo` exists only in `runner_shared.execute_item_core`; `oc_runipd.initialize_run` writes `"validate"`/`"no_audit"`, `agy_runipd.initialize_run` writes `"no_verify"`.
- `pyuw4v` is `reviewed`/`go-pending-approval`; `agent_workflows/source_offsets.py` does not exist yet (the edge `executed:pyuw4v` is correct).
- Census re-measured with a throwaway script implementing `pyuw4v` E-02's rules: 7 findings (F-06).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Live-artifact criterion / D. Anti-regression | review census: 7 findings; `oc_runipd.py:4823` now lands on "`# instead of being told the frozen value cannot change (DECISION 06-kgpptv-D5).`" | The census is a live population and has already drifted from 8 to 7: the `tests/test_oc_runipd.py` site is no longer DETECTED but is still wrong. E-01's "expect the 8 sites" and an executor following "every reported site is in scope" could skip E-03(a) and leave a known-wrong citation in place. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now re-derives the census, states it is not a bar, and requires every named E-02/E-03 site to be fixed whether flagged or not; added F-06; V-02 and V-03 require every named site rewritten and add an `rg` absence check. |
| PR-002 | LOW | IN-SCOPE | G. Execution contract | Approval gate | The gate lacked an open-question status line and conditional runner ownership of `aw ipd begin`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added both. |
| PR-003 | LOW | IN-SCOPE | G. OQ ownership | OQ-01 `- Owner: none` | The resolved question recorded no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep E-03(a) though the detector no longer flags it? | Keep, and require it explicitly | Drop it as "not reported" (leaves a wrong citation); refresh the offset (new expiring copy) | `rg` shows the quoted line only in `runner_shared.execute_item_core`; `fnbtta` idiom; spec Section 10.2 | yes |
| D-2 | Split E-02 per `IPD-Z602`? | No | Split into five E-items (five trivial V-items for one comment sweep) | Same concern, same edit type, one diff verified by one V-item | yes |
