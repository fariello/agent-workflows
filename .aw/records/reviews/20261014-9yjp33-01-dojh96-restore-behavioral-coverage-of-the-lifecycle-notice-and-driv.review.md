# Review findings: plan dojh96

- Subject-Id: dojh96
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2bea9c399` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by rendering the real prompts:
- All 12 renderings (`oc_runipd`/`agy_runipd` x `self_finalize` True/False x exec/recovery/verifier) have an empty non-ASCII set. Each contains its own mode's notice and not the opposite one, which confirms F-05 and E-03.
- Patching `ipd_lifecycle.runner_owns_lifecycle_notice` in-process to append U+2014 makes every rendering's non-ASCII set `['\u2014']`. This works because both `runner_shared` composers call the notice by module attribute.
- `pytest-subtests` is not installed (pytest 8.2.2), so a plain pytest function cannot use `subTest`.
- The deleted `DriverPromptTests._state()` carried no `options`, which confirms F-04.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Verification safety | Required tests mutation check, "then `git checkout -- agent_workflows/ipd_lifecycle.py`"; V-01 | The falsifiability step edited production source and then reverted it with a checkout. That risks committing a non-ASCII mutant, and once a docstring edit is in scope the checkout would also discard it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with an in-process `mock.patch.object` of the notice (F-06), which I demonstrated at review. The plan now forbids editing or checking out the file for the probe. |
| PR-002 | MEDIUM | UNDER-SCOPE | G. Honest documentation / lifecycle gate | `runner_owns_lifecycle_notice` docstring "no live guard currently asserts this"; `check.ipd-uncarried-obligation` (Deferred row and OQ-01) | OQ-01 deferred the docstring repoint on the grounds that the sentence "remains accurate history". It does not: its "no live guard" clause becomes false once this plan lands. The deferral and the other Deferred row also had no durable carrier, so the plan would fail its own pre-transition gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-04/V-04 (docstring-only), added `agent_workflows/ipd_lifecycle.py` to Scope-Paths, re-resolved OQ-01, and gave the remaining Deferred row `Carrier-Declined`. Added F-07. The carrier warning is cleared. |
| PR-003 | MEDIUM | IN-SCOPE | G. Executability | E-02 "under pytest `tmp_path`" plus `subTest`; `pytest-subtests` absent | E-02 combined pytest's `tmp_path` fixture with `subTest`. That works only in a `unittest.TestCase`, where `tmp_path` is not injectable. The `state` shape was also unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires a `TestCase` class. E-02 now uses `tempfile.TemporaryDirectory()` and spells out the `state` dict. |
| PR-004 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | Required tests "passes bare"; V-03 "`N passed` with no failures" | A fully green bare suite was the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed to a base-commit comparison by failing test id. The 12-rendering count is recorded as a stable matrix product, not a live count. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | Approval gate | The gate lacked the OQ status, the honesty rule, `aw ipd begin`, staged-set verification, a scope fence and runner-conditional finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all of those. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Repoint the docstring in this plan (OQ-01)? | Yes, E-04, docstring-only | Keep the deferral with a carrier (leaves a sentence this plan makes false); follow `k6twdf`'s deferral (that plan's call, not binding) | F-07; sibling `90yi49`/`9vsezc` E-04; `check.ipd-uncarried-obligation` | yes |
| D-2 | How should falsifiability be proven? | In-process patch of `ipd_lifecycle.runner_owns_lifecycle_notice` | Edit and checkout production source (commit risk, and the checkout discards E-04) | review probe F-06 | yes |
| D-3 | Test style? | `unittest.TestCase` with `subTest` and `tempfile` | pytest function with `tmp_path` (no `subTest` without `pytest-subtests`); add a dependency | pytest 8.2.2, `pytest_subtests` import fails | yes |
