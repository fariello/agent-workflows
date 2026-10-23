# Review findings: plan qx3ppg

- Subject-Id: qx3ppg
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `3969bf382`. The plan was byte-identical to the lane input and already committed (`e9f4b066f`), so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean` before and after revisions. Child plan (Set `trimgap`, Order 30), two restored test modules.

Verified at the lane HEAD (recorded in the plan as F-07):
- Neither target file exists at HEAD; both blobs exist at `19313eed^` (151 lines, 9 `def test_`; 7 `def test_` methods). `19313eed` is the suite-trim commit.
- Both blobs pass from a gitignored scratch dir: `16 passed in 1.25s`.
- `--extra-test` probes reproduce F-04/F-05: `classify_commit_refusal` killed 0/3, `apply_renames` killed 0/3, `_dirs` killed 0/4.
- Core-marked copies pass under `-m core` (9 and 7); unmarked copies are fully deselected.
- Pinned pre-commit `ruff` v0.4.4: `All checks passed!` on both marked copies (with `import pytest` placed between the stdlib block and `from agent_workflows import cli`).
- Bare gate before any change: `1675 passed, 11 warnings`, exit 0, with `CORE TIER BUDGET EXCEEDED` (`63.97s`) marked not enforced on an oversubscribed host.
- Symbols resolve: `ipd_lifecycle.classify_commit_refusal`, `plans_refs.apply_renames`, `plans_refs._dirs`; `conftest.pytest_collection_modifyitems` selects `core` only on a bare (testpaths) invocation.
- Precedents `y4bt1c`, `pdemar` are executed; sibling `2qlg0w` is pending.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Evidence accuracy | old E-02 "It has no module docstring"; `git show 19313eed^:tests/test_awcmdsurf_mutation_verbs.py` line 1 `"""Tests for awcmdsurf Order 03: ..."""` | The file has a module docstring, so the instruction to add one would create a second string literal or confuse the executor; V-02's diff demand would then mismatch. | all Low | FIXED | E-02 now appends the provenance line to the existing docstring and places `import pytest` where ruff accepts it (verified); V-02 diff wording matched. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (unsatisfiable proof) | old V-03 `--collect-only -q tests/...` "under the bare (core) selection"; review probe: an UNMARKED copy collected 9 under the explicit path and 0 under `-m core` | An explicit-path collection bypasses the core filter (`conftest.pytest_collection_modifyitems` applies only to testpaths runs), so V-03 could pass with `pytestmark` missing, the very defect the plan exists to fix. | all Low | FIXED | E-03, V-03 and Required tests now use `--collect-only -q -m core`. |
| PR-003 | MEDIUM | IN-SCOPE | Validation bar vs pre-existing state | bare run at `3969bf382` before any change: `Core tier wall time: 63.97s exceeded budget of 30.00s`, "not enforced: host oversubscribed" | E-03 did not say whether a budget overrun fails the plan, though the host already exceeds it before any change. | all Low | FIXED | E-03 says an overrun is recorded verbatim and is not a failure; the bar is no failures (sibling `f6el0l` rule). |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` | It lacked conditional runner/executor ownership of `aw ipd finalize` and implied a hand move to `executed/`; no staged-set check; no `--scope-ack`; the no-production-change check covered only committed history. | all Low | FIXED | Gate rewritten as an itemized execution contract; the production check adds `git status --short -- agent_workflows/`. |
| PR-005 | LOW | IN-SCOPE | Live counts as bar | E-01/E-02 "reports 9 passed" / "7 passed" | A collected test count is an artifact of test organization and must not be the bar on its own. | all Low | FIXED | Expected outcomes and V-01/V-02 require every test to pass and the count to equal the `def test_` census of the `19313eed^` blob, re-derived at execution. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does `import pytest` go in the mutation-verbs module? | Between the stdlib block and `from agent_workflows import cli` | After the first-party import (ruff I001 under some versions) | pinned pre-commit ruff v0.4.4 `All checks passed!` on the scratch copy | yes |
| D-2 | Does a pre-existing core-tier wall-time overrun fail this plan? | No, record it verbatim | Keep implicit under-budget bar (unsatisfiable on this host) | bare run `63.97s` at `3969bf382`; sibling `f6el0l` D-2 | yes |
| D-3 | Which collection proves core membership? | `--collect-only -q -m core <files>` | Bare `--collect-only` grep (works, but lists 1,600+ items) | review probe on marked and unmarked scratch copies | yes |
