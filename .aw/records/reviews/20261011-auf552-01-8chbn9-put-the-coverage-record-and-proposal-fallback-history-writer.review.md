# Review findings: plan 8chbn9

- Subject-Id: 8chbn9
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b1b2fab2b` (05:45 UTC 2026-10-12). Plan committed (`d310a1a90`) and
byte-identical to the lane input; no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` (one advisory
`IPD-Z602` info on E-01, judged single-concern: a baseline capture); `--phase review-finalize`: `clean` after revision.
Not an orchestrator.

Verified by driving the code: `coverage_record.write` under `TZ=Pacific/Honolulu` wrote `- Coverage-Checked:
2026-10-11 by m` and `- 2026-10-11 coverage pass ...` while UTC was `2026-10-12` (F-02 holds); under
`TZ=Pacific/Kiritimati` `2026-10-12`. `perform_coordinator_proposal_file` with a patched `integration_lock` yielding
`acquired=False` wrote `- 2026-10-11 created (proposal fallback): Proposal from fb0001` under Honolulu (F-03 holds).
`artifact_core.utc_history_date` exists with the cited docstring. The five TZ suites `26 passed`;
`tests/test_coverage_record.py` + `tests/test_run_proposal_channel.py` `26 passed`. Spec `2vev8j` is `approved`;
backlog `auf552` carries `- Blocks-Release: next`, inherited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric E (test exercises wrong code) | Lane env: ambient `PYTHONPATH` lists the main checkout first; a child run from a temp cwd imports the main checkout's `agent_workflows` (measured); `tests/conformance_matrix._pinned_env` prepends `REPO_ROOT` for this reason (its "F-13" comment) | E-02's child processes run from a temp directory with `TZ` and `AW_NO_REEXEC` only, so in a runner lane they would test ANOTHER checkout: the "fails at base, passes after edit" demonstration would be false in both directions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires `PYTHONPATH` with the repo root prepended; V-02 demands the child's import path pasted; F-06 added. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric E (inherited role) | `AW_EXECUTION_ROLE=worker` exported in this lane; `tests/support.execution_role` docstring ("A TEST MUST DECLARE ITS ROLE") | The fallback child inherits the ambient role, which that docstring calls a defect in both directions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 removes `AW_EXECUTION_ROLE` from the child env and pins the demonstrated call shape (temp git repo, no plan file). |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (vacuity) | E-02 "calls `pytest.skip` ... when neither zone is in a skew window" | With UTC-10 and UTC+14, exactly one zone is in skew at every instant, so "neither" can only mean a broken probe; the plan left that case as a silent skip. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 probes both zones and asserts exactly one is in skew before a case skips itself. |
| PR-004 | LOW | IN-SCOPE | Rubric G (census completeness) | `prompts._now` returns `_dt.datetime.now()` (bare); E-05 regex requires `datetime.now().` with a trailing dot | The census pattern misses bare `datetime.now()` and local `time.strftime`. (The `prompts` hit is a front-matter `Created:` date, NEITHER, so no live defect, but the census claim "every site" was not met by the command.) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 adds a second `rg` pattern. |
| PR-005 | LOW | UNDER-SCOPE | Rubric G (execution contract, specificity) | Gate; OQ-01 `Owner: none`; E-03 "Drop the `datetime` import only if ..."; E-05 CHANGELOG location | Gate lacked staged-set check, scope-as-declaration and conditional finalize wording; owner unrecorded; the import question and CHANGELOG heading were left to the executor though measurable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten; owner set; E-03 states the import is single-use (remove); E-05 names `## 2.0.0 (pending)`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the child import the code under test? | Prepend repo root to `PYTHONPATH`. | `cwd=` repo root (rejected: the coverage writer and fallback need temp trees; cwd does not beat an ambient `PYTHONPATH` entry anyway). | review import probe; `_pinned_env` F-13 comment. | yes |
| D-2 | Skip policy for the two zones? | Probe both, assert exactly one skews, skip only the non-skewed case. | Skip silently when neither (rejected: impossible state hides a broken probe). | UTC offsets -10/+14 sum to a 24h cover; review timestamps. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
