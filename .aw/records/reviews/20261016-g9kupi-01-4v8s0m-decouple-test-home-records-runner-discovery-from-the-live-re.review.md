# Review findings: plan 4v8s0m

- Subject-Id: 4v8s0m
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `0bff78ca6`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. Not an orchestrator.

Verified:
- `tests/test_records_root_accessor.py:590-598` reads the `kfnfji` plan from `REPO_ROOT / ".aw/records/plans/pending/..."`; `ls .aw/records/plans/*/*kfnfji*` finds it only in `executed/` (finalized in `3f3121d63`).
- `python3 -m pytest tests/test_records_root_accessor.py -o addopts="" -q -k runner_discovery` -> `1 failed, 17 deselected`.
- The module is not listed in `pyproject.toml` `testpaths`, so the bare routine gate never collects it.
- OQ-01 (a HOW question) was demonstrated with a scratch test under the gitignored `.aw/state/` reusing `home_records_env` and `run_aw`: refusals `IPD-H202`, `IPD-M104`, `IPD-M113`, `IPD-M107` in turn (exit 2), then with the full field and section set `1 passed`, stdout `Run order (1 item(s)): 01 zq9fx1` and `fixtset 01 zq9fx1 -`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric G (HOW question undemonstrated) | plan OQ-01 "Determined empirically during E-01"; probe refusals `IPD-H202`/`IPD-M104`/`IPD-M113`/`IPD-M107` from `[RUN-STRUCTURE-PREFLIGHT]` | OQ-01 was resolved with a deferred "determine empirically" clause, and its predicted minimum (scaffold plus `Status: approved`) is refused by the runner preflight. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Demonstrated at review; E-01 lists the exact required fields and sections; OQ-01 cites the demonstration; finding F-5 added; Owner set to reviewer. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric E (evidence feasibility) | plan V-01 grep `REPO_ROOT / \".aw/records`; `tests/test_records_root_accessor.py:591-592` splits `REPO_ROOT` and the path across lines | V-01's grep pattern never matched even the broken file, so it could not prove the read was removed. E-01's outcome "no path under REPO_ROOT / .aw/records" was ambiguous with `REPO_ROOT` legitimately used by `run_aw`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now greps `kfnfji\|cleantgt\|plans/pending/2026\|REPO_ROOT` with expected surviving matches stated; E-01 outcome restated as "reads no file from the repo's .aw/records tree". |
| PR-003 | LOW | IN-SCOPE | Rubric E (gate coverage) | `pyproject.toml` `testpaths` (module absent); plan E-03/V-03 | The plan implied the bare routine gate exercises this test; it does not. Also V-03 carried an extra `-q`, which AGENTS.md says hides the summary line, and gave no way to show a failure pre-existing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/V-03 state the module is outside `testpaths`, drop the extra `-q`, require the count re-derived at execution, and define "pre-existing". |
| PR-004 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan `## Approval and execution gate` | The gate lacked the honesty rule, scope-fence declaration, staged-set verification, conditional runner/hand finalize ownership, and release-gate inheritance note. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all contract elements. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What minimum metadata must the fixture carry to be queued? | The field and H2 set listed in E-01, including synthetic `Readiness`/`Approval` and a `/plan-review` history verdict. | Scaffold plus `Status: approved` only (REJECTED: refused by preflight); marking the test `livecorpus` (REJECTED: the test asserts no corpus property). | Review-time probe output (F-5); `tests/test_records_root_accessor.py:582` `test_home_records_runner_discovery`. | yes |
| D-2 | May a test fixture carry `Readiness`/`Approval` values no review produced? | Yes, inside a throwaway `tmp_path` home-records dir only. | Mocking the preflight (REJECTED: weakens the behavioral assertion). | AGENTS.md "NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD" governs tracked plans; the fixture is not a record. | yes |
| D-3 | Which fixture id6? | `zq9fx1`, Set `fixtset`. | Any other unused id6 (equivalent). | `grep -rl zq9fx1 .aw/records agent_workflows tests` matched only this plan. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
