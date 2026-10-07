# Review findings: plan jei45f

- Subject-Id: jei45f
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `281875ca4`. The plan was committed and byte-identical to the sealed lane input, so no
pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before revision and
`--phase review-finalize --agent` was clean after it.

Re-verified by reading code and by subprocess runs (`PYTHONPATH=<lane>`, `AW_NO_REEXEC=1`, `HOME` isolated, `cwd` in a temp dir):
- `specs.run_check` resolves via `resolve_verb_repo_root`, reads `target = getattr(args, "path", None)`, and only calls `_spec_files(repo_root)` on the no-positional branch (F-02, F-04 hold).
- `backlog.run_check` resolves and iterates `_iter_items(repo_root)` with no guard; `backlog.run_set`'s `--gate-dir` branch is the `is_project_dir` + `return 2` precedent (F-08 holds).
- `attention.run` is the reference refusal: three summaries, `NextAction("aw install .")` gated on `git_root_for_message`, `cannot-run` at exit 2, human `EXIT_CANNOT_RUN` (= 2) (F-06 holds).
- `docs/cli-output-contract.md` contains the quoted Anti-Greenwashing Invariant and "never infer completion from prose" (F-03 holds).
- Reproduced: `--dir <deep>` greenwash for both validators (`"checked":0`, `verified:true`); root control `1 specs checked.` / backlog `"checked":1`; bare-from-subdir climb `checked:1`; `specs check <file> --dir <deep>` `1 specs checked.`.
- `command_surface` declares `specs check` and `backlog check` with `exit_contract=(0, 1, 2)`, so exit 2 stays inside the declared contract; `spec check` is an alias with `canonical_command="specs check"`.
- `.github/workflows/tests.yml` runs `python -m agent_workflows specs check` at the checkout root; unaffected.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Anti-regression / plan-internal consistency | plan OQ-02 "refuse in BOTH cases"; E-01/E-02/E-03 Expected outcomes and V-01..V-03 covered only `--dir <subdir>`; measured bare `aw specs check --agent` outside any project emits `"outcome":"clean","verified":true,"checked":0` at exit 0 | OQ-02 resolves that the bare no-project case must refuse too, but no E-item outcome, test case or V-item demanded it, so an executor could satisfy every V-item with an `if explicit_dir` guard and leave the greenwash. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 states the guard keys on the resolved root, not on `--dir`; E-01/E-02/E-03 outcomes, the matrix (row v), V-01, V-02 and V-03 now require the bare no-project refusal. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing / fixture executability | review runs: `aw install . --records-backend repository` non-interactive -> "Noninteractive first install requires complete policy choices"; with `--preset/--delivery-mode` -> "pass --yes to proceed" / "aborted; nothing changed."; `aw backlog new` requires `--work-kind` and `--priority` | The fixture recipe E-03 mandates does not produce a project when run non-interactively, so the test would build an empty fixture and its root control would fail (or an executor would loosen it). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10 with the working recipe (`--yes --preset local-only --delivery-mode tracked --records-backend repository`, required `new` flags) and permitted a hand-built `.aw/records/` fixture, as existing tests use. |
| PR-003 | LOW | UNDER-SCOPE | E. Fixture isolation | `resolve_verb_repo_root` docstring hazard 3 ("`$HOME` is commonly a project root"); F-07 home-backend redirect | E-03 did not require isolating `HOME`, so the no-project case and the records backend depend on the executing machine. | all Low | FIXED | E-03/V-03 require `HOME` pointed at a temp dir and `find_project_root(<outside cwd>) is None` asserted first. |
| PR-004 | LOW | IN-SCOPE | E. Validation commands | `tests/test_specs.py` does not exist; `run_check` is exercised in process by `tests/test_specs_verbs.py`, `tests/test_specs_recursive_read.py`, `tests/test_backlog.py` | The focused test command named a nonexistent file and omitted the in-process `run_check` suites most likely to catch an over-broad guard. | all Low | FIXED | Focused command corrected and the reason for each file stated. |
| PR-005 | LOW | UNDER-SCOPE | G. Control precision / user impact | `backlog check` human line carries no count; `command_surface` `spec check` alias | The "nonzero checked" root control was stated for specs only, though the backlog `--agent` record carries `checked`; and the gate did not mention the `aw spec check` alias or the bare-outside-project behavior change. | all Low | FIXED | Root control now nonzero on `--agent` for both validators; Expected outcome and gate name the alias, the bare case, and that CI at the root is unaffected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Must the bare no-project case be tested and validated, given OQ-02 already resolved it? | Yes, added to E-01..E-03 and V-01..V-03 | Leave it as an OQ-only statement | plan OQ-02; review measurement of the bare greenwash; `attention.run` refuses both | yes |
| D-2 | Fixture: mandate `aw install` or allow hand-built? | Allow either, provided the nonzero root control holds | Mandate `aw install` only | `tests/test_specs_recursive_read.py` and `tests/test_backlog.py` use hand-built trees; `is_project_dir` accepts `.aw/records` | yes |
