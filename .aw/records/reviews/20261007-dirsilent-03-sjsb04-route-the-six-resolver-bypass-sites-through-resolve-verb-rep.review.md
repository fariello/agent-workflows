# Review findings: plan sjsb04

- Subject-Id: sjsb04
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `7b607c4dd`. The plan was committed and byte-identical to the sealed lane input, so no
pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before revision and
`--phase review-finalize --agent` was clean after it.

Re-verified (code reads; subprocess runs with `PYTHONPATH=<lane>`, `AW_NO_REEXEC=1`, `HOME=<tmp>`):
- The bypass expression `Path(getattr(args, "dir", None) or os.getcwd())` appears exactly six times. An AST walk attributes them to `cli._run_record_history`, `cli._run_graduation`, `cli._run_find`, `cli._run_search`, `cli._run_check` and `doctor.run` (F-01 holds).
- Fixture installed with `--yes --preset local-only --delivery-mode tracked --records-backend repository`, run bare from `src/deep`: `aw check` gave `CONFORMS 0 all checked`; `find backlog` gave `no matching backlog`; `search probe` gave `FINDINGS no matching lines` (exit 1); `record-history <id6>` gave `no sidecar history`; and `doctor` gave `Repository: ... (<p>/src/deep)` / `Version: not installed ... [not-installed]` (F-02, F-04 hold).
- `resolve_verb_repo_root`'s body matches F-05.
- A probe in a scratch copy of the tree (resolver plus `is_project_dir` refusal at the five sites) ran the full suite: `9 failed, 5222 passed`. Three of those failures are attributable to the refusal (F-10).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression / scope paths | `tests/test_fields_flag_reach.py:130` and `tests/test_verbose_flag_reach.py:113` (`cli.main(["check","plans","--agent","--dir", <bare tempdir>])`); `tests/test_agent_surface_conformance.py:62` (`(temp_dir / ".aw").mkdir()`) | E-03's refusal makes three shipped tests fail, because their fixtures are non-projects that rely on the greenwash. The tests sit outside `- Scope-Paths:` and the plan did not anticipate them. The executor would have hit an unexplained suite delta, and might have "fixed" it by widening the accepted exit codes, which would gut those tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10. E-03 now requires fixture-only repairs that turn each fixture into a real minimal project, and forbids widening the exit codes. The three files were added to Scope-Paths, and V-03 demands the before/after proof. |
| PR-002 | HIGH | IN-SCOPE | D. Domain invariant ($HOME hazard) | `project_context.resolve_verb_repo_root` docstring hazard 3. Measured: `resolve_verb_repo_root()` returns `<H>` from an uninstalled git repo under an AW-root `HOME`, and `doctor --dir <that>` reports `Repository: ... (<H>)` | Replacing the root in `doctor.run` with the plain resolver would make `aw doctor` diagnose `$HOME` instead of the repo the operator is standing in. That is the commonest `doctor` use case (before install). | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now bounds `doctor`'s bare climb at cwd's git root, using `project_context._find_git_root` locally and leaving the resolver untouched. Added F-11; E-04, Required tests, V-02 and V-04 pin it. The survey verbs deliberately stay unbounded so they match their resolver-calling siblings. |
| PR-003 | MEDIUM | IN-SCOPE | E. Fixture executability | measured: `aw install . --records-backend repository` non-interactive installs nothing; `backlog new` requires `--work-kind`/`--priority` | E-04's fixture recipe would build an empty fixture, making every comparison vacuous or failing. | all Low | FIXED | E-04 now gives the complete recipe (or allows a hand-built fixture) and requires an isolated `HOME`. |
| PR-004 | LOW | IN-SCOPE | E. Baseline accuracy | `tests/test_selector_type_containment.py` passed in the review scratch run | The plan asserted this file was "ALREADY FAILING", as a stable fact. | all Low | FIXED | Reworded to "was failing at authoring; re-measure". The repaired fixture files were added to the focused run. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the three greenwash-dependent tests be handled? | Repair fixtures into real minimal projects; never widen exit codes | Widen the accepted exit codes; exempt `check` from the refusal | F-10 probe; the tests assert projection/verbosity/conformance, not non-project behavior | yes |
| D-2 | Bound `doctor`'s climb at the git root? | Yes, locally in `doctor.run` | Plain resolver (retargets `$HOME`); leave `doctor` non-climbing (keeps F-04's falsehood) | F-11 measurement; resolver docstring hazard 3; scope fence forbids editing the resolver | yes |
| D-3 | Apply the same bound to the five survey verbs? | No | Bound all six | Siblings `specs check`/`backlog check` already climb unbounded; the plan's goal is consistency with them | yes |
