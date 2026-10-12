# Review findings: plan nzzu8n

- Subject-Id: nzzu8n
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `d2bbf1ded`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`: `clean` before review;
`--phase review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Demonstrations run at review (temp dirs and detached worktrees under the system temp dir, all removed; the lane's
`git status --short` stayed empty):
- `--rootdir "$PWD" <tmp>/test_p.py` (the authored design) took `1 passed in 64.54s` for a one-assert test. The same
  file without `--rootdir` ran in 0.34s, and `tests/test_run_freeze.py` placed at its own path in a worktree of `HEAD`
  ran in 0.61s (`12 passed in 0.15s`). `git worktree add --detach` took 0.76s.
- `tests/test_shared_checkout_contract.py` from `19313eed^`: `6 failed, 4 passed` from a bare temp dir with
  `PYTHONPATH=<repo>`, but `10 passed` at its own path in a tree of `HEAD`.
- From a temp dir, a probe printed `AW_HOME= None`. Inside a worktree it printed `AW_HOME= /tmp/aw-test-home-...`,
  so the root conftest's home sandbox applies only in-tree.
- Exit codes: an import of a missing module gives exit 2 with `ModuleNotFoundError` in the junit XML. A syntax error
  gives exit 2 with `collection failure` and no `ModuleNotFoundError`. A file with no tests gives exit 5.
- Population: of the 298 test files `19313eed` deleted, 85 use `__file__`, 137 use `subprocess`, and 18 paths exist
  at HEAD.
- A process-group kill (`start_new_session` + `os.killpg`) returned at the 2s timeout for a test that spawns a 60s
  grandchild.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness (replay fidelity) | Original Scope/E-01 ("into `tempfile.mkdtemp()`/<basename>"); `conftest.py:140` `_HOME_KEYS`; review demo (F-05) | A bare temp dir changes outcomes. 85 of the 298 deleted files anchor on `Path(__file__)`, and the conftest home sandbox does not reach a file outside the rootdir. Product-sound files would read `fail` (demonstrated: 6 spurious failures), and their tests could touch the real `AW_HOME`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each blob is now replayed at its original path inside a throwaway detached worktree of `HEAD`, the same isolation `g55j1e` uses. Fixture case (g) asserts both effects. OQ-02 and D-1 record the choice. |
| PR-002 | HIGH | IN-SCOPE | C operability | Original E-01 `--rootdir <repo_root>`; review demo (F-04) | `--rootdir <repo>` with the file outside it took about 65s per one-assert file. Across the 209-file population in Order 05 that is roughly 4 hours of overhead. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The worktree design drops `--rootdir`, with `cwd=<wt>`. F-04 records the measured costs. |
| PR-003 | MEDIUM | IN-SCOPE | A classification | Original E-01 ("exit 2 or 4 or 5 ... otherwise `error-collect`"); review demo (F-07) | Exit 4 (usage error) and exit 5 (no tests collected) are not collection errors, and exit 3, signals and a missing junit file were unclassified. Order 05 would misread these files. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The verdict set now adds `no-tests` (exit 5) and a residual `error`. Exit 2 is split on junit `<error>` text. An `error_line` field is added for Order 05's spot checks. The Scope check cross-references the Order 05 mapping to `replay-env-limited`. |
| PR-004 | MEDIUM | IN-SCOPE | C failure handling | F-06 (137 of 298 use `subprocess`); original E-01 `subprocess.TimeoutExpired` | Killing only the direct pytest child on timeout can orphan grandchildren, which keep running and can hold the worktree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The child now runs with `start_new_session=True`, and a timeout calls `os.killpg` with SIGKILL (demonstrated). The cleanup `finally` removes and prunes the worktree. These are listed as invariants. |
| PR-005 | MEDIUM | UNDER-SCOPE | E testing / G live-count bar | Original E-02 (three cases plus timeout); V-01 "12 per-test outcomes"; V-02 "five verdict classes" | `error-collect` was untested, and V-02 counted five classes when E-02 exercised four. V-01 used a hard-coded test count as its bar. There was no sensitivity check, no CLI subprocess run, and no `--from-json` test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now has seven cases plus an overwrite case, each verdict except the residual `error` has a dedicated case, and the CLI runs as a subprocess with `--from-json`. V-01 re-derives the count with `--collect-only`. V-02 maps each class to its case and adds a scratch-copy sensitivity run. |
| PR-006 | MEDIUM | IN-SCOPE | G interface contract (cross-plan) | `sk2rbf` E-04 calls `replay_file(..., python_prefix=..., extra_env=...)`; `1ub8ex` E-01 JSON shape | The CLI did not define the JSON output shape, the exit codes, or what `--from-json` reads. Under the new worktree design, Order 04 would need the replay root to relativize coverage paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now pins the result fields, including `replay_root` and `head`, the JSON form, exit codes, and that `--from-json` reads each record's `path`. Order 04 (`sk2rbf`) is outside this ledger, so it is not edited. Its executor should use `replay_root` when mapping coverage paths. |
| PR-007 | LOW | UNDER-SCOPE | G execution contract; AGENTS.md no-dash rule | Original gate paragraph; E-03; Required tests (no baseline capture) | The gate lacked the scope-fence declaration, honesty rule, invariants and staged-set check. The README item lacked the no-dash rule. Nothing captured the execution-start baseline the final check compares against. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate is itemized to match sibling `g55j1e`. E-03 and V-03 carry the no-dash rule. A baseline capture is added to Required tests and to the gate's Order. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Bare temp dir or worktree of `HEAD`? | Detached worktree, with the blob at its original path. | Bare temp dir plus `PYTHONPATH`, which was rejected because the review demo produced spurious failures and no home sandbox. A `git archive` copy was also rejected: it costs about the same, and the worktree matches `g55j1e`. | Review demos (F-04, F-05); `g55j1e` E-01 Worktree bullet. | yes |
| D-2 | How should exit 4/5 and other odd exits be classified? | Add `no-tests` (exit 5) and a residual `error`. | Fold both into `error-collect`, which was rejected because it conflates environment problems with collection errors. | pytest `ExitCode`; review demo (F-07). | yes |
| D-3 | Should Order 04's consumer be edited for `replay_root`? | No. Expose the field and note it in PR-006. | Edit `sk2rbf` now, which was rejected because it is outside this review's ledger. | plan-review Step 0.1 ledger rule. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
