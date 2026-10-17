# Review findings: plan r20rid

- Subject-Id: r20rid
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e34dd644b`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `tests/test_compat_migration_rollback.py` is absent at HEAD; `grep -rln compat_migration tests` hits only
  `tests/test_core_module_coverage.py` (F-02 correct). `git show 19313eed^:...` restores 618 lines.
- The unmodified deleted module passes at HEAD: `41 passed in 1.67s`. Under coverage (data file in
  gitignored `tmp/`): `TOTAL 390 44 89%`, all 36 `b1mx2w` keys entered, missing lines include 151-161
  (`CompatSurface.validate`) and 615 (`detect_state`'s `return STATE_PARTIAL`).
- `tests.support.init_repo`, `clean_git_env`, `git` exist with the signatures the plan uses; root
  `conftest.py` loads `tests.git_config_guard`.
- E-04's exact assertions run as written: `validate()` returns the six named problems in order;
  `check_contract` with a `dataclasses.replace` owner variant reports `surface 'exit-codes': bad owner 'not-an-owner'`.
- `tools/mutation_probe.py` CLI: `--op {return-none,return-true,return-false,negate-return,raise}`,
  `--format json`, positional pytest args; `ProbeResult` has every field V-07 names. No "return empty
  list" operator exists.
- CI `tests.yml` runs `python -m pytest tests/ -n auto -rfEs` (unmarked module is load-bearing there).
- `.coverage` at the repo root is NOT gitignored (`git check-ignore -v .coverage` exit 1); `tmp/` is.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric D/F (silent failure) | `19313eed^:tests/test_compat_migration_rollback.py` `RollbackTests.test_recover_interrupted_migration_completes_it` "except Exception:\n            pass" | The plan removed the `skipTest` escape but kept a second swallow: the fault-injected `execute_migration` sits in `except Exception: pass`, so any crash (not just the injected interruption) counts as the interruption. Demonstrated (F-09) the injection raises `MigrationError`. | all Low | FIXED | E-02 now has part (b) replacing it with `assertRaises(MigrationError)`; V-02 greps for `except Exception` and demands the block. F-06 updated. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric D (evidence contradicts claim) | plan E-03 "the partial state by `test_recover_interrupted_migration_completes_it`"; `agent_workflows/compat_migration.py:615` `CompatMigrator.detect_state` "return STATE_PARTIAL" unexecuted | E-03 justified dropping the constant arm by claiming every state is asserted behaviorally, but nothing asserts `STATE_PARTIAL`: the recover arm checks `status_migration()`, and coverage shows the `return STATE_PARTIAL` line never runs. Dropping the arm would leave that state unpinned. Demonstrated (F-09) `detect_state()` returns `partial` then `current`. | all Low | FIXED | E-03 adds `STATE_PARTIAL` before-recovery and non-partial after-recovery assertions to the recover arm, names each covering arm, and depends on E-02 (same test). V-03 rewritten. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (falsifiability unproven) | plan E-04 "without it a mutant making `validate` always return `[]` survives"; E-07 `--op return-none ...::CompatSurface.validate` over the whole file | E-07's probe for `validate` used `return-none` over the whole file, which the PRE-EXISTING arms already kill (F-10: 9 failures without E-04), so it proved nothing about the new arm; the `[]` mutant E-04 targets has no probe operator. | all Low | FIXED | E-07 narrows that probe to the new test node; E-04 adds a scratch `mock.patch.object(..., lambda self: [])` run whose expected outcome is the new arm failing (F-10 baseline 0 failures). V-04/V-07 demand both. |
| PR-004 | LOW | IN-SCOPE | Rubric G (executability) | plan E-05 `coverage run` with default data file; `git check-ignore -v .coverage` exit 1; key extraction with `[A-Za-z_.]` yields 35 (`_sha256_*` -> `_sha`) | The default `.coverage` lands at the untracked repo root, and the natural key regex truncates two keys, producing a false 35. The coverage JSON function-map lookup was unspecified. | all Low | FIXED | E-05 sets `COVERAGE_FILE=<scratch>/.coverage`, gives the exact `grep -o` with digits, names the `functions` map lookup, and reports `missing` and `unentered`. V-05 aligned. |
| PR-005 | LOW | IN-SCOPE | Rubric G (bar conventions) | plan E-01 "`git status --short` ... shows no change to ... `.git/config`"; E-03/E-04/V-03/V-04/V-07 "40 tests"/"41 passed" | `git status` cannot show `.git/config`, so that proof was impossible; and collected test counts were used as V bars, which the rubric forbids (test-organization artifacts). E-01 also did not say both seeding tests (four git calls) need the clean env or that `from tests import support` is required. | all Low | FIXED | E-01 names the import, both seeding tests and four calls, and cites the guard plugin as the proof; counts are now context with "every collected test passed, 0 failed" as the bar; V-01 greps for leftover `user.email=`/raw init. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Prove E-04's `[]` mutant is killed, given the probe tool has no such operator? | Scratch `unittest.mock.patch.object` run, plus narrowing the `return-none` probe to the new node | Adding a `return-empty` operator to `tools/mutation_probe.py` (production-tool change, out of this test-only scope); dropping the claim | `tools/mutation_probe.py` `OPERATORS`; F-10 measurement | yes |
| D-2 | Keep dropping `test_all_install_states_are_reachable_names`, or keep it because `STATE_PARTIAL` is otherwise unasserted? | Drop it and add a behavioral `detect_state() == STATE_PARTIAL` assertion | Keep the constant-pinning arm (violates AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE") | AGENTS.md; F-09 demonstration | yes |
