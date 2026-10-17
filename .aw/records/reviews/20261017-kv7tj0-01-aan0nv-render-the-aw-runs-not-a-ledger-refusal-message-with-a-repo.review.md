# Review findings: plan aan0nv

- Subject-Id: aan0nv
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan, Set `kv7tj0`, no dependants.

Verified:
- `run_ledger_store.NotALedgerError.__init__`: `self.path = Path(path)`, `msg = f"{self.path} is not a run ledger file"`, `detail` appended after `": "`; raised from `RunLedgerStore._require_ledger_shape` with `self._path`.
- `run_cli._emit_not_a_ledger`: `err_msg = f"error: not a run ledger: {exc}"`, used for machine `"error"` and `_print_human(err_msg)`; `path` via `agent_schema.normalize_repo_path(exc.path, resolve_verb_repo_root(getattr(args, "dir", None)))`.
- Four `except store.NotALedgerError as exc:` arms, in `_run_show`, `_run_evidence`, `_run_verify_ledger` and `_build_engine`; `run_viewer` swallows the exception.
- `tests/test_runs_machine_output_paths.py::test_not_a_ledger_machine_path_is_relative`, `_parse_machine`, `_assert_relative`, `repo` fixture via `seed_ledger_fixture`.
- `tests/test_run_recovery_cli.py` asserts only the `not a run ledger` substring and no `corrupt`.
- MEASURED probe (`tests.conformance_matrix.run_cli`, fixture repo under `/tmp/opencode`): `runs show <foreign events.jsonl> --dir <repo>` exits 7 with the absolute path in the message in `--json`, `--agent`, and human mode; `path` is `.aw/records/runs/run-feedfeed00/events.jsonl`; `verify-ledger` and `evidence` behave the same. Human stdout begins with lowercase `error: not a run ledger: `.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Executability (ordering) | E-02/E-03 `Depends on: E-01`; Required tests "author E-02/E-03 first"; V-02/V-03 "FAILING on the unmodified `run_cli.py`" | The tests depended on E-01, so an executor following the dependency order would make the fix first, and the before-fix failure that V-02 and V-03 demand could no longer be produced without `git stash`, which the plan forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02/E-03 now `Depends on: none` and say to keep the red output; E-01 depends on E-02, E-03; Proposed changes reordered. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence (wrong claim) | E-01 Expected outcome "the human renderer measurably prints as `Error:`"; `run_cli._print_human` prints `_redact_output(text)` verbatim; probe stdout `error: not a run ledger: ...` | The claim is false: human mode prints lowercase `error:`. An executor might write a test that expects `Error:` and get a spurious failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expected outcome corrected to identical text in both modes, with the measured example; F-06 records the probe. |
| PR-003 | LOW | IN-SCOPE | Validation coverage | Required tests "`aw sanitize --agent` reports no new finding"; V-01..V-03 | The sanitizer requirement had no V-item to show it, and the routine gate demanded no exit code. | all Low | FIXED | V-03 demands the sanitizer record and `exit=`. |
| PR-004 | LOW | IN-SCOPE | Clarity | E-01 "`_run_show`-style readers"; E-02 "(or add a sibling test)" | Call sites were named vaguely and E-02 left the test shape open. | all Low | FIXED | Call sites named (`_run_show`, `_run_evidence`, `_run_verify_ledger`, `_build_engine`); E-02 parametrizes the existing test using `_parse_machine`. |
| PR-005 | LOW | IN-SCOPE | Process (gate, OQ owner) | gate paragraph; OQ-01 `Owner: none` | The gate lacked the scope-fence declaration, the "paste the actual output" rule, `aw ipd finalize` as the only path to `executed/`, and who runs it (runner or hand executor). OQ-01 listed owner `none` for an author-resolved question. | all Low | FIXED | Gate rewritten; owner `plan author`. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Normalize in the store exception instead of the CLI (OQ-01)? | CLI boundary only | Change `NotALedgerError.__str__` (REJECTED: the store has no repo root; tracebacks may want the full path) | `RunLedgerStore` constructed from a path only; F-05 | yes |
| D-2 | Order of tests vs. fix | Tests first (red), then fix | Fix first and simulate red with `git stash` (REJECTED: plan forbids `git stash` in a shared checkout) | AGENTS.md shared-checkout rule; plan Required tests | yes |
