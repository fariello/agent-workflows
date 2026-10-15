# Review findings: plan 8e7xrj

- Subject-Id: 8e7xrj
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author` was clean before the review and `--phase review-finalize` is clean after it. At pre-transition the only findings are the expected `IPD-S404` not-yet-performed items, so the carrier rules hold.

Evidence re-measured at review:

- `test_set_level_checks` part (c) holds the three literals (`tests/test_runwire_verifier_authority.py:633-635`).
- `rg` over `tests/` confirms F-01: the only other hit is the dynamic multiplier in `tests/test_run_exit_aggregate.py:128`.
- The partition equality evaluates `True` at the lane HEAD.
- The stop-condition command reports `17 passed in 1.41s`.
- Mutation probes ran on a scratch copy under the gitignored `tmp/`, which was deleted afterwards, with the replacement applied:
  - growth by `probe-29th-status`: `1 failed`, naming the token
  - removing `running`: `1 failed`, naming `'running'`
  - removing `integration-deferred`: `1 failed`, naming `'integration-deferred'`
  - a coordinated addition to `TERMINAL_STATES_CANONICAL` and `KNOWN_ITEM_STATUSES`: `1 passed`
- Formatter check: `ruff format --diff` on the replaced file rewrites the one-line equality into a 5-line parenthesized form.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Verification feasibility | `.pre-commit-config.yaml` `ruff-pre-commit` `rev: v0.4.4`; review probe `ruff format --diff` turns the one-line equality (145 chars) into a multi-line form | E-01 and V-01 (c) required the diff to show the exact one-line statement and "no other line changed". The ruff format hook would rewrite that statement at commit, so the committed diff could never match the evidence demanded. F-05's "zero formatting changes in `test_set_level_checks`" does not reproduce. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now spells out the `ruff format` multi-line form. V-01 (c) and Required tests item 3 accept that form, and V-01 also requires `ruff format --diff` to show no hunk inside the test. |
| PR-002 | LOW | IN-SCOPE | G. Live-artifact criteria | E-01 stop condition and V-01 (a) "all 17 tests `PASSED` (`17 passed`)"; E-01 outcome "returns only the dynamic ... multiplier" | A collected test count and a live grep population were used as bars, which the rubric forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bars are now "every collected test passed, none skipped or deselected" and "no `len(...)` compared to a fixed literal". The counts stay in the plan as context. |
| PR-003 | LOW | IN-SCOPE | G. Open-question ownership | OQ-01 `- Owner: none` | A resolved question carries the placeholder owner `none`. The workflow requires the reviewer or the plan author to be recorded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the plan force the one-line equality (for example with `# fmt: skip`) or accept the formatter's multi-line form? | Accept the multi-line `ruff format` form | `# fmt: skip` (adds a suppression comment only to preserve an evidence string); ignore it (the evidence would be unsatisfiable) | `.pre-commit-config.yaml` ruff hook; review `ruff format --diff` probe | yes |
