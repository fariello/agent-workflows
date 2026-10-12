# Review findings: plan l4lc6p

- Subject-Id: l4lc6p
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ca5521479` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` conforming (one `info` diagnostic `IPD-Z602` on E-03), likewise at
`--phase review-finalize` after revision.

Re-verified:
- E-01's command at review HEAD: exactly the 24 NEITHER paths of the Findings table, with matching carriers
  (98 hits over 28 carrying files); `19313eed` attribution 75.
- `EXCLUDED_CLASSES["tmp_path"]` is declared but `scan_axis_a` filters only `EXCLUDED_PLACEHOLDER_PATHS`.
- `tests/test_lift_drift_scan.py` `LiftDriftScanGuardTests` docstring cites `tests/test_liftaudit_drift.py`;
  `git log --all -- tests/test_liftaudit_drift.py` empty; `tests/test_liftaudit_stop_halts_run.py` exists with
  `LiftauditStopHaltsRunTests.test_oc_run_queue_stop_now_force_level4`; `96xtmi` F-16 names that file.
- `tests/test_docs_test_citations.py` `HISTORICAL_EXEMPTIONS` keyed precedent exists.
- `scan_target_files(Path('.'))` includes `tools/lost_guard_census.py`, `tests/test_lost_guard_census.py`,
  `tools/README.md`.
- Sibling `1ub8ex` (reviewed) declares the same census files and consumes `scan_axis_a(...).cited_paths`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness | `tools/lost_guard_census.py` `SCAN_ROOTS` includes `tools`; `PATH_CITATION_RE`; E-03 (ii) writes cited paths into the census module | The census scans itself, so every cited path written into `ACKNOWLEDGED_NON_CITATIONS` becomes a new NEITHER hit carried by `tools/lost_guard_census.py`; the plan's goal and V-03 bar (NEITHER 0) were unreachable as written. E-04's new fixture literals and E-05's README examples have the same effect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-03 (v): self-acknowledgement of table entries in the census module (no wholesale exclusion); literal-hygiene rule in E-04 and E-05; V-03 measured after E-04/E-05 and re-runs E-01. |
| PR-002 | MEDIUM | UNDER-SCOPE | C. Operability | E-03 (ii)-(iv) | A keyed exemption that no longer matches any hit would silently persist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-03 (vi) `Unused acknowledgements: M keys`, required 0 in V-03. |
| PR-003 | MEDIUM | IN-SCOPE | B/D. Probe safety | V-04 "temporary sabotage of the exemption skip in `scan_axis_a`" | Editing production source to sabotage in a shared checkout is avoidable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04/E-04 now rebind `ACKNOWLEDGED_NON_CITATIONS` to `{}` in-process. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing / baseline | V-05 "bare-suite ... summary line with no failures" | No baseline, so another party's failure blocks a correct execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline before E-02, same failing-test set by name after E-05. |
| PR-005 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Missing OQ status, scope-as-declaration/`--scope-reason`, MUST-paste rule, `aw ipd begin`, staged-set check, conditional finalize ownership, Blocks-Release statement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. |
| PR-006 | LOW | UNDER-SCOPE | Sequencing | `1ub8ex` Scope-Paths | Overlap with sibling `1ub8ex` on all three census files, and the `cited_paths` semantic change it consumes, were unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions note: the two compose, sites disjoint, no dependency edge. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to stop the exemption table counting itself? | Acknowledge a census-module hit whose target is a cited path of a table key | Exclude the census module from the scan (hides genuine citations); build the table strings by concatenation (obscures the table) | `scan_target_files` output at review; `HISTORICAL_EXEMPTIONS` keyed precedent | yes |
| D-2 | Split E-03 on the `IPD-Z602` info? | No | Split into placeholder / table / output items | one function region, one concern (implement the declared exclusions), one V-item; `IPD-Z602` is `info` | yes |
| D-3 | Dependency edge with `1ub8ex`? | No | Add `executed:1ub8ex` or reverse | acknowledged paths are all NEITHER-attributed so the reach partition over trim-deleted files is unchanged; runner isolates worktrees | yes |
