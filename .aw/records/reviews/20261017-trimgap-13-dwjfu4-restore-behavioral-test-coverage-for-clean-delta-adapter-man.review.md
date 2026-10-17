# Review findings: plan dwjfu4

- Subject-Id: dwjfu4
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `316482e76`. The plan was already committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 13), test-only.

Verified in the lane (scratch restore of `tests/test_clean_delta.py` and scratch mutations of `agent_workflows/clean_delta.py`, all removed or reverted; `git diff agent_workflows/` empty, `git status` clean apart from the plan and this record):
- `19313eed^:tests/test_clean_delta.py` exists; `tests/test_clean_delta.py` does not exist at HEAD; the docstring cites `clean_delta.py:338`/`:342`. `b1mx2w` has 9 `clean_delta.py::` rows marked `unguarded-unreached`, matching F-01.
- With `import pytest` and `pytestmark = pytest.mark.core` inserted: bare collect `tests/test_clean_delta.py: 24`; isolated run `24 passed in 2.29s`; bare `python3 -m pytest` `777 passed in 26.14s`.
- Mutation sweep over the restored file: E-03 (a), (b), (c) and E-04 (c), (d), (e) KILLED. E-04 (a) (drift always `clean`) and (b) (managed block repaired as a shim) SURVIVED with `24 passed`.
- Two scratch tests (drift a repaired shim, then re-repair; repaired `AGENTS.md` carries `<!-- /aw:block -->` and a codex uninstall removes it) passed at HEAD and killed (a) and (b) respectively.
- `_compute_sha256` constant-return mutation killed by `TargetDeltaTests::test_every_kind_of_change_is_detected_and_classified` (through `snapshot_target_state`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D/E. Coverage (goal not met; validation would fail) | `clean_delta.detect_adapter_drift` (`if h == entry.generated_hash or entry.ownership_marker in content:`); `clean_delta.repair_adapters` (`if entry.adapter_kind == AdapterKind.MANAGED_SECTION_BLOCK.value:`); review mutations `24 passed` | E-04 (a) and (b) survive every restored test: no test drifts an installed adapter and no test inspects a repaired `AGENTS.md`. E-04's Expected outcome is unattainable as written, and the Goal (drift detection and repair guarded) is not met. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-06/V-06 with two behavioral tests (values observed at review, F-05). E-04 now depends on E-06 and names which tests kill (a) and (b). |
| PR-002 | MEDIUM | IN-SCOPE | Evidence (claim contradicted) | F-04; `clean_delta.snapshot_target_state` (`snap.file_hashes[rel_p] = _compute_sha256(text)`) | F-04 said `_compute_sha256` has no caller besides the manifest builder and drift detector; `snapshot_target_state` also calls it. E-04 also never mutated `_compute_sha256`, even though F-04 says E-04 does. | all Low | FIXED | Corrected F-04; added E-04 (f) (constant return), killed by `TargetDeltaTests`. |
| PR-003 | LOW | IN-SCOPE | G. Executability (insertion hazard; no failure disposition) | E-01 "add `import pytest` and a module-level `pytestmark`"; `from agent_workflows.clean_delta import (` | The import block ends in a parenthesized multi-line import, so a naive insertion can produce a `SyntaxError` (seen on sibling `9gjvrq`). There was also no rule for a restored test that fails. | all Low | FIXED | E-01 says to insert after the last complete import statement, and carries the Set's disposition rule. |
| PR-004 | LOW | IN-SCOPE | G. Live-artifact bar | E-01/E-02/V-01/V-02 "24 tests" | A collected test count was used as the pass bar. | all Low | FIXED | Bars are now all-pass plus selection by the core tier, re-derived at execution; 24 kept only as context. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate had no honesty rule, no staged-set check, no scope-fence wording, and no conditional finalize ownership. The 26s of 30s budget headroom was not called out. | all Low | FIXED | Gate rewritten as an execution contract; Required tests demand the wall time. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to close the two surviving mutations? | Append two tests in the restored file (E-06) | Drop mutations (a)/(b) from E-04 (would weaken the Goal) | Goal line "drift detection, repair"; review probe results | yes |
| D-2 | Keep verbatim restore (OQ-01) despite PR-001? | Yes, restore verbatim and append | Rewrite the module | F-03/F-05 all 24 pass unmodified | yes |
