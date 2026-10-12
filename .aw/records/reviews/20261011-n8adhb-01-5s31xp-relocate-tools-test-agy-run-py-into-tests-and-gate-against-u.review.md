# Review findings: plan 5s31xp

- Subject-Id: 5s31xp
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b1b2fab2b`. The plan was committed (`4b4aa83ad`) and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before; `--phase review-finalize`:
`clean` after revision. Not an orchestrator.

Verified: `testpaths = ["tests"]`; the five F-02 paths; `tools/test_agy_run.py` `44 passed` with `-o addopts=""`;
`TOOLS_DIR = Path(__file__).resolve().parent` is the only location dependency; a scratch copy at `tests/test_agy_run.py`
with the repointed `TOOLS_DIR` gave `44 passed in 1.90s` (copy removed, tree clean); no `tools/*.py` module name shadows
a `tests/` import except `runner_fork_scan`, which `tests/test_runner_fork_scan_constants.py` already loads from `tools/`
the same way; backlog `3rj8wr` and `byz9pj` exist under `open/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric D/E (guard red on arrival) | Review: `git ls-files` pattern set minus collected `path::` files (`python3 -m pytest --collect-only -q -o addopts= -m "" -p no:randomly`) lists `tests/test_lift_drift_scan.py`; its body is an empty `unittest.TestCase` "Retired under IPD 96xtmi" | E-02's exemption list was "exactly the four measured entries", but a fifth tracked pattern file is uncollected, so the new guard would fail the default suite on the real tree and block every lane merge. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 exempts it with its `96xtmi` reason; F-08 added; deletion explicitly deferred with Carrier-Declined. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric C/D (lane-blocking fragility) | `.aw/records/research/.../prototype/tests/test_broker.py`; `pyproject.toml` `livecorpus` marker comment | Per-file exemption of a research-record path makes any agent that ships a `test_*.py` in a record turn the default suite red, the exact lane-blocking cost `livecorpus` was created to avoid. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `EXEMPT_PREFIXES = (".aw/",)` with reason, outside the stale check; helper unit test and V-02 (4) cover it; git-unavailable path skips with reason. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (unsatisfiable evidence) | Review: `python3 -m pytest --collect-only -q tools/test_agy_run.py` prints `tools/test_agy_run.py: 44` (configured `-q` + `-q` = `-qq`), so the V-01 grep for `::` returns 0 | V-01 (3) and E-01's outcome demanded a count from a command shape that cannot produce it; the bar was also a count. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Commands use `-o addopts=""`; bar is pre-move set equals post-move set. |
| PR-004 | LOW | UNDER-SCOPE | Rubric E (baseline) | V-03 "full bare suite ... with 0 failed" | No baseline was recorded, so a pre-existing failure would make V-03 unsatisfiable or be misattributed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records a `-rf` baseline; V-03 compares failing ids. |
| PR-005 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Gate paragraph; OQ owners `none`; F-07 timing | Gate lacked paste-actual-output, staged-set check, scope-as-declaration, conditional finalize ownership (it implied a hand move); owners unrecorded; F-07's 3.7s re-measured at 9.8s. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten; owners set; F-07 and E-02 cost updated against the 240s wall arm. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to treat `tests/test_lift_drift_scan.py`? | Exempt with its `96xtmi` reason. | Delete it (rejected: out of this plan's scope and owned by `96xtmi` cleanup); count zero-item modules as collected (rejected: hides a genuinely empty module). | file body; review collection diff. | yes |
| D-2 | Per-file or prefix exclusion for `.aw/`? | Prefix `.aw/`. | Per-file (rejected: any agent's research record can turn the default suite red). | `pyproject.toml` `livecorpus` comment. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
