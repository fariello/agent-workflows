# Review findings: plan ge4qh3

- Subject-Id: ge4qh3
- Subject-Type: ipd
- Reviewed-At: 2026-10-24
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `746f3604f`. The plan was byte-identical to the sealed lane input and already committed at `661023f56`, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions `--phase review-finalize --agent`: `clean`. Child plan (Set `mqsitd`, Order 1), not an orchestrator.

Verified at the lane HEAD:
- F-1: `runner_shared.record_oq_answer` builds `rationale_pattern` `(?m)^-[ \t]+Resolution or deferral rationale:[^\n]*(?:\n[ \t]+[^\n]*)*` and calls `rationale_pattern.sub(rationale_line, new_block, count=1)`. Reproduced: a fixture built with `_create_plan_with_oqs(..., oqs=[{"id": "OQ-01", "rationale": "Original question context: SQLite or Postgres?"}])` ends with `- Resolution or deferral rationale: RESOLVED 2026-10-17 by w via c: x` after the call; the original text is gone.
- F-2 (stronger than the plan stated): answer `C:\new\1` raised `PatternError invalid group reference 1`; answer `C:\new` wrote `...: C:` and a following line `ew`. Neither caller wraps the call in `try` (the `aw runs answer` path beside reason "record_oq_answer failed or artifact hash moved", and the pre-flight sweep loop calling with `answer=ans_clean`).
- Present-but-empty field today yields `- Resolution or deferral rationale: RESOLVED 2026-10-17 by w via c: x` (single space).
- F-3: `test_a40_durable_artifact_write_back` OQ dict has no `rationale` key; `_create_plan_with_oqs` writes the line only `if rationale`.
- `tests/test_question_preflight.py` has no `pytestmark`/`core` marker; `python3 -m pytest --collect-only -q` collects 0 tests from it; the explicit-path run is `11 passed in 3.22s`, A40 and stale-refusal at 0.03 s each.
- Spec `6kwd2e` R1.5 and A40 require "a rationale naming the human and date" and `- Blocking:` unchanged: satisfied by the append form.
- `record_oq_answer` was introduced by `eb85f275d`, not an ancestor of tag `v1.3.0-rc.1`: the overwrite never shipped.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric A / B (trust-boundary input) | `agent_workflows/runner_shared.py:19645` `rationale_pattern.sub(rationale_line, new_block, count=1)` | F-2 said backslashes "would be interpreted"; measured, `\1` in a human answer raises `re.error` uncaught out of both callers and `\n` splits the line. E-02's third case did not assert "no exception". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-2 rewritten with the demonstration; E-01 Expected outcome and E-02 third case assert the literal write and no exception. |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric E (validation reaches the test) | `conftest.py:153` `item.get_closest_marker("core")`; `tests/test_question_preflight.py` has no core marker | The bare routine gate (the runner merge gate) collects zero tests from this module, so the regression tests for a release-blocking bug would never run in the gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 marks each new test `@pytest.mark.core` (~0.03 s each); E-03, V-02 and Required tests state what the bare gate covers. |
| PR-003 | LOW | UNDER-SCOPE | Rubric D (preserve behavior) | `_create_plan_with_oqs` writes no line for `rationale=""`; E-01 "when the existing field value is empty" | The present-but-empty field branch had no test, and naive append could emit a double space or keep trailing whitespace. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 strips trailing whitespace and specifies one separating space; E-02 adds a fourth test pinning the exact empty-field line. |
| PR-004 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan "Approval and execution gate" | Gate lacked the staged-set verification, declaration-only scope fence, and conditional `aw ipd finalize` ownership; `aw commit <this plan>` was a placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with the full contract and `aw commit ge4qh3 -- ...`. |
| PR-005 | LOW | IN-SCOPE | Shared-checkout safety; doc sync | plan "Required tests / validation" optional pre-change demo; "Spec / documentation sync" | The optional pre-change failing run named no method (an executor might `git stash`), and the CHANGELOG disposition for a bug fix was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Demo method: write tests before the E-01 edit, no stash or revert. Doc sync records no CHANGELOG entry because the defect never shipped. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Core-mark only the new tests or the whole module? | Only the four new tests | Module-level `pytestmark = pytest.mark.core` (adds ~3 s of git-subprocess tests to a 30 s budget; outside the bug's scope) | `conftest.py` core selection; `pyproject.toml` marker "author-assigned"; measured 0.03 s per new-style test | yes |
| D-2 | Does the fix need a CHANGELOG entry? | No | Add a `Fixed:` line under 2.0.0 (pending) | `git merge-base --is-ancestor eb85f275d v1.3.0-rc.1` -> not an ancestor; CHANGELOG 2.0.0 entries for the sweep and `aw runs answer` | yes |
| D-3 | Separator when appending to existing text? | Strip trailing whitespace, then one space | Newline-separated continuation line; `; ` separator | backlog `mqsitd` "append ... to existing text"; `lf4j52` E-02 "append the resolution after the existing rationale text"; keeps the field on lines the existing `rationale_pattern` already matches | yes |
