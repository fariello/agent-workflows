# Review: Derive the deselect notice's category list from the run's own marker filter

- Subject-Id: qsz23k
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at the lane HEAD:

- The hardcoded parenthetical in `tests/deselect_notice.py` `pytest_terminal_summary` matches F-01.
- `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` is unchanged.
- The default collect-only run prints `NOTE: 232 tests were deselected`, matching F-06.
- The targeted module reports `4 passed`.
- CI's `-m slow` step exists in `.github/workflows/tests.yml`.

A three-marker probe fixture loaded the real plugin and reproduced F-02's wrong sentence in the `-m slow`, `-m '' -k` and `-m 'not (...)'` cases. It also confirmed that `config.option.markexpr` is readable on the xdist coordinator, as F-03 states. A probe of the E-02 rule confirmed F-04 and showed that `not android` is not split mid-token.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Correctness (A) / UX (F) | `tests/deselect_notice.py` `pytest_terminal_summary`; review probe: default `addopts` plus `-k 'not test_b'` gives `MARKEXPR='not slow and not livecorpus and not gpu' KW='not test_b'` and `1 passed, 3 deselected` (2 by marker, 1 by `-k`) | Branch (a) of E-03 credits the whole count to the named marker categories. In the most common developer invocation, the default filter plus `-k`, most of the count comes from `-k`, so the notice would still misattribute it. That is the same kind of falsehood the plan exists to remove. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10. E-03 branch (a) now also names a `-k`/`--deselect` contribution when `config.option.keyword` or `config.option.deselect` is non-empty. E-04, V-04, V-06 and the negative control gained a mixed case. |
| PR-002 | LOW | IN-SCOPE | Live-artifact criteria (G) | plan V-06(a) "expect 8 after E-04 and E-05" | The bar was a collected test count, which is an artifact of how the tests are organized. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bar is now "every pre-existing and every added case is listed as passed". |
| PR-003 | LOW | IN-SCOPE | Execution contract (G) | plan gate "STOP CONDITION ... STOP if the E-06 control does not fail ALL FOUR" | A control case that passes is a defect in the plan's own test, which the executor can fix. A stop there strands the turn, contrary to the 2026-09-01 scope-fence ruling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded so the executor fixes the case, re-runs the control, and leaves V-06 `failed` until all five control cases fail. |
| PR-004 | LOW | IN-SCOPE | Plan metadata | plan OQ-01 `- Owner: none` | A question resolved on the author's authority should record that owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should OQ-01's split (names when the reader can parse exactly, verbatim otherwise) stand without asking the maintainer? | Keep it | Verbatim-only; a general expression parser | `zb81ah` OQ-01 options as quoted in the plan; F-04 probe re-run at review | yes |
| D-2 | How should a count that mixes marker and `-k`/`--deselect` sources be described? | Name the categories and say that `-k`/`--deselect` also contributed | Try to split the count per source, which pytest does not expose per source to this hook | Review probe of `config.option.keyword` and `config.option.deselect` on the coordinator | yes |
