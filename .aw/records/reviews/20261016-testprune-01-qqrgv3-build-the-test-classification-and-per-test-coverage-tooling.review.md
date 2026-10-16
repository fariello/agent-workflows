# Review findings: plan qqrgv3

- Subject-Id: qqrgv3
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `bb20c263b`. Plan committed and byte-identical to the lane input,
so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an orchestrator.

Re-probe of the E-01/E-02 design (scratch under gitignored `.aw/state/`, removed afterwards): a hookwrapper
calling `Coverage.current().switch_context(nodeid)` and re-serializing `COVERAGE_PROCESS_CONFIG` with
`context=nodeid`, rcfile `branch/parallel/patch = subprocess`, `COVERAGE_CORE=ctrace`,
`coverage run -m pytest tests/test_status_set.py -n 4`: 26.9s wall; after `coverage combine`,
`has_arcs` True, 111 contexts (110 collected node ids plus `""`), 16 node ids hit
`agent_workflows/__main__.py` (subprocess-only path), 929898 arc rows, 35 MB data file; a unique-arc
SQL group-by over it took 0.7s. API checks: coverage 7.15.0 has `Coverage.current`,
`CoverageConfig.serialize/deserialize`, `CoverageData.measured_contexts/set_query_context/contexts_by_lineno`;
`coverage.patch` reads `COVERAGE_PROCESS_CONFIG`. pytest-cov 7.1.0 is installed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D (cross-plan consistency) | `83nnyn` E-01 "`--cov-context=test --cov-branch`"; `vgus66` E-01 "`--cov=agent_workflows --cov-branch --cov-context=test`" | The two consumers of this baseline tell executors to measure with pytest-cov contexts, not this plan's plugin. Context names and subprocess attribution differ, so every before/after comparison would report spurious lost coverage or hide real loss, which defeats the Set's "no lost line" proof. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now records the baseline DIR/HEAD and edits `83nnyn`/`vgus66` E-01 (both pending) to use `percov_run` + `percov_analyze --compare`; Scope-Paths extended; F-7 added; V-07 demands the diff. |
| PR-002 | MEDIUM | IN-SCOPE | E (trustworthy measurement) | E-02 (pre-review) no handling of a failing run | A failing test truncates its coverage; a decision table built from such a run would mark tests marginal on bad data. | all Low | FIXED | `meta.json` records `pytest_exit`; E-07 refuses a run with failures; E-06 tests the refusal; V-02 demands `pytest_exit: 0`. |
| PR-003 | MEDIUM | IN-SCOPE | G (executability) | E-03 (pre-review) "collected in `junit.xml` but no context" | junit `classname`/`name` do not round-trip parametrized node ids, so the `no_coverage` join would be wrong. | all Low | FIXED | E-02 writes `collected.txt` from `--collect-only -q`; E-03 joins on it; junit used for durations only. |
| PR-004 | MEDIUM | IN-SCOPE | G (executability) | E-05 (pre-review) "markers from `pytest --collect-only`" | `--collect-only -q` prints no markers. | all Low | FIXED | Added uncollected `tests/tools/markers_dump.py` collect-time plugin. |
| PR-005 | MEDIUM | IN-SCOPE | D (invariant: core protected) | `8wfzb5` Scope "so the `core` marker exists and is protected"; E-05 fixed rules (pre-review) | The classifier could propose deleting a `core` test, breaking `hguae9`'s module/leaf coverage; protected families were defined by vague names; rule precedence was undefined. | all Low | FIXED | `core` never `delete-candidate`; explicit printed protected-module list; stated precedence; E-06 and V-05 cover both. |
| PR-006 | MEDIUM | IN-SCOPE | C (tool interaction) | pytest-cov 7.1.0 installed | `coverage run -m pytest` with pytest-cov loaded risks a second collector. | all Low | FIXED | E-02 passes `-p no:cov`; F-8 added. |
| PR-007 | LOW | IN-SCOPE | G (accuracy, cross-plan) | `hguae9` E-02 (reviewed) creates `tests/tools/__init__.py` | E-01 "Create `tests/tools/__init__.py`" collides with the dependency's file; empty-context and teardown attribution unspecified; output DIR location and size unstated; scale of E-03 unaddressed. | all Low | FIXED | E-01 adds beside existing file and resets context; E-02 gitignored DIR guidance with size; E-03 one-pass sets, ignore `""`; E-06 respects core budget. |
| PR-008 | LOW | IN-SCOPE | G (execution contract) | plan gate (pre-review) | Gate lacked scope-fence wording, the paste-actual-output MUST, conditional finalize ownership. | all Low | FIXED | Gate rewritten. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How do consumers measure? | Through this plan's `percov_run`/`percov_analyze --compare`, edited into `83nnyn`/`vgus66` E-01 by E-07. | Leave pytest-cov flags (REJECTED: non-comparable contexts); edit those plans now in this review (REJECTED: they are separate review subjects; the owning plan carries the fix). | probe above; plan-review "fix in the owning plan". | yes |
| D-2 | Node-id denominator source? | `--collect-only -q` written to `collected.txt`. | junit (REJECTED: lossy for parametrized ids). | pytest output format. | yes |
| D-3 | Are `core` tests deletable? | Never `delete-candidate`. | Allow with `hguae9` re-measure (REJECTED: `8wfzb5` defers core membership to `hguae9`). | `8wfzb5` Deferred section. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
