# Review findings: plan jy7439

- Subject-Id: jy7439
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `3dc559634`. The plan was already committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`, plus one `info` advisory, `IPD-Z602` on E-04 ("may bundle multiple concerns"). That advisory is accepted: E-04 is a single mutation sweep with one deliverable and one V item, so the enumerated mutations are its inputs, not separate concerns. Child plan (Set `trimgap`, Order 10), test-only.

Verified in the lane (scratch restore of `tests/test_lifecycle_fixtures.py` and scratch mutations of `agent_workflows/lifecycle_fixtures.py`, all removed or reverted; `git diff agent_workflows/` empty; `git status` clean apart from the plan and this record):
- `19313eed^:tests/test_lifecycle_fixtures.py` exists with the 17 tests and classes the plan names; no file at HEAD. `run_fixture` raises the `ValueError` listing known names; `IsolatedEnv.restore_aw_home` pops `AW_HOME` when `_prev_aw_home is None` (F-05 confirmed by reading).
- Restored file plus E-02 (a)..(c): `20 passed in 2.85s`; bare collect `tests/test_lifecycle_fixtures.py: 20`; `ruff check --select F` clean.
- Mutations (a)..(i): all KILLED as F-08 states. Two extra mutations were also KILLED: human file overwritten before `apply`, and `_migrator` pointed at `base_dir`. `_snapshot_tree -> {}` SURVIVED (`20 passed`).
- A scratch fourth test (`run_unsupported_host` with `render_probe_commands` patched to write a file and then raise) passed at HEAD and killed that mutation.
- Bare `python3 -m pytest`: with the file `774 passed in 38.75s`; without it `753 passed in 34.04s` and `CORE TIER BUDGET EXCEEDED` on a 12-CPU host. The overrun is pre-existing (F-06, backlog `o58dro`); the module costs about 2.8s serial.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Anti-regression (refuse-before-mutation verdict) | `lifecycle_fixtures._snapshot_tree`; `run_unsupported_host` / `run_no_credential` (`no_mutation = before == after`); review mutation `20 passed` | The Goal covers each fixture's `mutated` flag and its pass/refusal verdict. But the before/after snapshot those verdicts rest on is unguarded, because no real refusal writes anything. A broken snapshot would hide a refusal that DID mutate the repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-02 (d), mutation E-04 (j), and F-09. The E-02 class now has four tests; Scope, Proposed changes, Required tests, V-02 and V-04 are updated to match. |
| PR-002 | LOW | IN-SCOPE | Validation (command cannot produce the stated value) | V-01 `python3 -m pytest --collect-only -q \| rg -c test_lifecycle_fixtures` "reporting 20" | `--collect-only -q` prints one `path: N` line per file, so `rg -c` prints `1`. Measured. | all Low | FIXED | V-01 now pastes the `path: N` line and matches N to the V-03 count. |
| PR-003 | LOW | IN-SCOPE | Executability / live-artifact bar | E-01, E-03, V-03 ("17", "20 passed") | No disposition rule for a restored test that fails, and test counts were used as the pass bar. | all Low | FIXED | Added the Set's disposition rule to E-01. The bars are now all-pass, with counts kept as context. E-05 states that a pre-existing budget overrun is reported, not worked around by un-marking tests. |
| PR-004 | LOW | IN-SCOPE | Execution contract | gate paragraph | The gate had no honesty rule, no staged-set check, no scope-fence wording, and no conditional finalize ownership. | all Low | FIXED | Gate rewritten as an execution contract. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 errors, plus the accepted `IPD-Z602` info advisory.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to guard `_snapshot_tree`? | A fourth E-02 test that makes a refusal write a file through a patched `render_probe_commands` | A direct `_snapshot_tree` unit assertion (pins a private helper rather than the verdict) | Goal "`mutated` flag"; review probe | yes |
| D-2 | File a backlog item for the F-05 `AW_HOME` removal, as the plan left for the reviewer? | No item; recorded in Deferred | File a `chore` | `AGENTS.md` "INEFFICIENCY A USER CAN NOTICE"/perceptible-impact rule; F-05 no observed effect; root `conftest.py` home sandbox | yes |
| D-3 | Treat `IPD-Z602` on E-04 as a right-sizing finding? | No; accepted advisory | Split E-04 into one item per mutation | E-04 has one deliverable and one V item | yes |
