# Review findings: plan kb64ea

- Subject-Id: kb64ea
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan, Set `4qu8zm`.

Verified:
- `install_wizard.persist_project_policy`: `json.dump(proj_schema.to_dict(), f, indent=2)` and `json.dump(local_schema.to_dict(), f, indent=2)` with no newline, then `_config.sync_cutovers_on_install`, which writes `f.write("\n")` only under `if modified:`.
- `placement_switch._write_atomic_json`: `json.dump(data, f, indent=2)` then `os.replace`, no newline; used for `new_proj_schema`, `new_local_schema`, journals and receipts. The records-backend rewrite in the same module already writes `f.write("\n")`.
- Placement-switch verify phase compares hashes only for `kind == "move"` items; `config_project`/`config_local` are `kind="rewrite"`, so the added byte does not trip the verify step. Rollback tests compare restored originals, which this change does not alter.
- MEASURED: `placement_switch._write_atomic_json(tmp, {"a": 1})` -> bytes end `b'1\n}'`, `json.loads` round-trips.
- MEASURED: `python3 -m pytest --collect-only` on the four V-04 files: default filter deselects 174 of 185 tests; `test_placement_switch_execute.py`, `test_placement_switch_companion_execute.py`, `test_installer.py` are `pytestmark = pytest.mark.slow`.
- Pending plan `gbnrdf` (Set `denczr`, reviewed, `Blocks-Release: next`) adds the identical two `persist_project_policy` newline writes and a byte-stability test, Scope-Paths `agent_workflows/install_wizard.py, tests/test_reinstall_preserves_config.py`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | OVER-SCOPE | Architecture (duplicate carrier) | old E-01; plan `gbnrdf` E-01 "after `json.dump(proj_schema.to_dict(), f, indent=2)` ... add `f.write("\n")`" | E-01 makes exactly the edit plan `gbnrdf` already carries. Whichever runs second would either find the edit already done (a vacuous V-01 and a red-first test that can never be red) or, if both are dispatched concurrently, produce a conflicting double edit on the same lines. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `install_wizard.py` removed from Scope-Paths; `Item-Dependencies: executed:gbnrdf`; E-01 is now a read-only prerequisite check; Deferred names `gbnrdf` as Carrier; Findings records the duplicate. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (vacuous slow-suite run) | V-04 command without `-o addopts=""`; measured 174/185 deselected | The existing-file run named in Required tests would silently skip almost every placement-switch and installer test, which are exactly the ones exercising `_write_atomic_json`, so V-04 could not detect a regression. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Command clears `addopts`, adds `tests/test_placement_switch_guard.py`, and V-04 demands zero deselected. |
| PR-003 | MEDIUM | IN-SCOPE | Executability (red-first ordering) | old E-03 `Depends on: E-01, E-02`; V-03 "run BEFORE applying E-01/E-02 (write the test first)" | The test item depended on both fixes, contradicting V-03's write-first demand. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 depends on E-01 (check) only; E-02 depends on E-03; V-03 demands (a)/(b) PASSED and (c) FAILED before E-02, then all PASSED. |
| PR-004 | LOW | IN-SCOPE | Process (gate, OQ owner) | gate "`aw commit <plan> -- <Scope-Paths>`", "through the lifecycle tooling"; OQ-01 `Owner: none` | Placeholder commit command, no paste-actual-output rule, no scope-fence declaration, no `aw ipd finalize` / runner ownership; owner `none`. | all Low | FIXED | Gate rewritten with the full contract; owner `plan author`. |

`aw ipd lint --phase review-finalize --agent`: `clean` (one `info` `IPD-Z602` on E-03's (a)/(b)/(c) enumeration, kept: one test file, one concern).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which plan owns the `persist_project_policy` fix? | `gbnrdf`; this plan depends on `executed:gbnrdf` | Keep it here and retire `gbnrdf` (REJECTED: `gbnrdf` is already reviewed with a red-first test on its own failing acceptance test); keep both (REJECTED: double edit) | `gbnrdf` E-01, Scope-Paths, Status reviewed | yes |
| D-2 | Keep the newline for journals and receipts through `_write_atomic_json` (OQ-01)? | Yes | A config-only helper (REJECTED: extra path for no reader benefit) | readers use `json.loads`; verify phase hashes only `move` items | yes |
