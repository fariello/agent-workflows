# Review findings: plan j77z5h

- Subject-Id: j77z5h
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `72da75876` (probes ran at the lane's committed `d3a4d10c6`). The plan was byte-identical to the lane input and already committed at `e9f4b066f` (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 31), new test module only.

Verified at the lane HEAD:
- Every F-03 return value reproduces exactly by direct call (`Palette.status`, `_status_glyph_char` both modes, `_gate_ref_display` with `long` keyword-only, `cite_review_entry`, `format_spec_impact_announcement` with `pal=Palette(False)`); signatures match the plan's calls.
- The gap is open: `cite_review_entry` `return-none` under `-m core tests/test_plan_readiness.py` survived (0); `Palette.status` `return-none` under `-m core tests/` survived (0, 700.57s).
- `tests/test_render_residual_helpers.py` does not exist; no collision.
- `conftest.pytest_collection_modifyitems` selects by the `core` marker, so module-level `pytestmark` is sufficient; no registration needed.
- Sibling `a5drqh` is now `approved` (not executed) and excludes `_gate_ref_display`; the scope split holds.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (tests must be collected) | `pyproject.toml` `[tool.pytest.ini_options]` sets no `python_classes`; scratch module with plain `class RunnerStatusAndGlyphTests:` gave `no tests ran`, exit 5 | E-01 to E-04 named classes `*Tests` with no base class. pytest only collects `Test*` classes or `unittest.TestCase` subclasses, so a literal executor would write tests that never run; E-06's probes would then report `survived` (or a 0-test baseline) and the plan's goal fails. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every class now subclasses `unittest.TestCase` (repo convention); E-01 states why; E-01 expected outcome requires the tests be collected; F-06 records the measurement. |
| PR-002 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` "Move the plan to `.aw/records/plans/executed/` only after ..." | Gate implied a hand move to `executed/`, lacked the hard-MUST paste-actual-output rule, the no-production-change rule and the `--scope-reason`/`--scope-ack` reconciliation detail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: `aw ipd finalize` with conditional runner/executor ownership, honesty MUST, production fence. |
| PR-003 | MEDIUM | IN-SCOPE | Validation (satisfiable bar) | `conftest.pytest_sessionfinish` sets `session.exitstatus = 1` when enforced; sibling `bli2ba` review: 1675 passed, 34.61s, exit 1 on this 12-CPU host | E-05/V-05 did not say how to judge the bare gate's exit status when the pre-existing enforced budget overrun makes it exit 1 with all tests green. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 accept exit 1 only when solely from the enforced budget block listing no test from the new module; ruff import layout also specified to avoid a mutating-hook rejection. |
| PR-004 | LOW | IN-SCOPE | Evidence currency | plan F-05 and OQ-01 "`a5drqh` is `to-review`"; `a5drqh` front matter `Status: approved` | Stale status of the sibling plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 and OQ-01 updated; conclusion unchanged (not executed). |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the new classes be made collectable? | Subclass `unittest.TestCase` | Rename to `Test*` plain classes; add `python_classes` to pyproject (out of scope, global) | F-06; repo convention in `tests/test_run_analytics_telemetry.py`, `tests/test_attention_stem.py` | yes |
| D-2 | Does a pre-existing enforced core-budget overrun fail E-05? | No, unless a new-module test is among the listed slowest | Exit-0 bar (unsatisfiable on this host) | `conftest.pytest_sessionfinish`; `bli2ba` review D-1 | yes |
| D-3 | Keep the direct `_gate_ref_display` test despite `a5drqh` now approved? | Keep | Depend on `a5drqh` | OQ-01; `a5drqh` not executed and excludes the key | yes |
