# Review findings: plan cqxq2a

- Subject-Id: cqxq2a
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `66401aeb1` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `python3 -m pytest tests/test_cli_quality_gates.py tests/test_conformance_matrix_structure.py` -> `22 passed in 7.70s`; no `pytestmark` in either module.
- `check_findings.human.golden` lines 7 and 11 carry `--to-id6 --apply` and `--rename --apply`.
- `rg -lw` per symbol: `ANSI_RE` (2 test files), `GOLDEN_DIR` (1), `build_matrix`, `required_scenarios`, `USAGE_ERROR_FLAG` (1 each).
- Twelve goldens = `_fixtures()` (4 names) x {agent, human, json}; `_golden_path`, `_read_or_write_golden` (raises `FileNotFoundError` when absent and UPDATE unset) as cited.
- Orphan probe: `touch .../zzz_orphan.human.golden` -> `14 passed`; probe removed, `git status --short tests/fixtures/` empty.
- `l8wvv3`, `dq9bj9`, `9i2hge` executed; `34iwyp` reviewed; `2wowfy` graduated.
- Backlog `krwj2o`: now `graduated` to this plan (run `run-20261012T005606Z-2321569`), `chore`, no `Blocks-Release`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked approval command, `aw ipd begin`, scope-as-declaration with `--scope-reason`, the MUST-paste rule, staged-set check, and conditional runner/executor finalize ownership; it said "move this plan to executed/ through the tooled lifecycle" without naming the owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with every element; E-01 premise stop kept as the one legitimate stop. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing / baseline | E-04 "report the failure set against the base" | No baseline was taken before the edit, so "no new failure" had nothing to compare to. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records a pre-edit bare baseline with failing-test names; E-04/V-04 compare by name. |
| PR-003 | LOW | IN-SCOPE | Evidence currency | Concern "would sit `open` forever"; F-05 grep result | Backlog `krwj2o` is now `graduated` to this plan, and the grep now also returns this plan and the INDEX. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-05 updated; gate states the item carries no release gate. |
| PR-004 | LOW | IN-SCOPE | Executability | E-04 (b) `mv read_clean.json.golden aside` | Destination unspecified; moving it to another name inside the fixture dir would itself be an "extra" golden and confound the probe. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Probe moves it to a gitignored path outside `tests/fixtures/`. |
| PR-005 | LOW | IN-SCOPE | E. Testing | E-03 | Under pytest-randomly a regeneration run could execute the inventory test before the writers; and a future added suffix fails as "extra". Both were unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states both behaviors and requires the missing-file message to mention regeneration. |
| PR-006 | LOW | IN-SCOPE | Open questions | OQ-01, OQ-02 `- Owner: none` | Owner `none` on resolved questions is not meaningful; these are author decisions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does closing `krwj2o` need a handoff proof? | No; it has no `Blocks-Release`, so `aw backlog set done` needs no gate proof | Require executed carrier anyway | `AGENTS.md` close-legitimacy rule applies only to items carrying `Blocks-Release`; item front matter | yes |
