# Review findings: plan 1ub8ex

- Subject-Id: 1ub8ex
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b1b2fab2b`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; `--phase
review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Verified at review: `python3 tools/lost_guard_census.py --summary 19313eed` prints "Uncited deleted files: 209 files
holding 3585 removed functions" (9.4s); `19313eed` deletes 298 files, all `tests/test_*.py`, so every deleted path is
a test file; the 4 recreated paths match the plan; `annotate_candidate_file` over the 209 gives 31 pin / 3,554
behavioral, 19 mixed, 0 all-pin, and `total_funcs == len(extract_test_functions(...))` for every file; F-02 holds
(`main` argparse has no list-emitting flag; `ReachPartition` is counts only); `main` uses `Path.cwd()`; no
`.spec.md` cites `lost_guard_census`. Downstream consumers of the JSON: `nzzu8n` E-01 and `sk2rbf` E-04
(`--from-json`), `8d0qsg` E-01/E-02. Scratch-copy mutation method for V-02 demonstrated: copying the tool and its
test under `/tmp/opencode/` and mutating `annotate_candidate_file`'s pin test to `if False:` gave `1 failed, 4 passed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric A/G (reproducibility) | Plan Concern and F-04 ("16 import nothing ... 1 imports only ... 134 distinct"); review probe over `git show 19313eed^:<path>` | The `imports` parse rule was unspecified and the authoring counts are not reproducible: under an `ast.walk` rule there are 13 empty files, 3 `wtiso_gate` importers (1 importing only it), 140 modules; module-level-only parsing gives 18. A tool whose numbers depend on an unstated rule defeats the census's reproducibility goal and seeds wrong figures into `8d0qsg` F-02. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 pins the rule (all nodes, `level == 0`, `from agent_workflows import N` counted only when `N` was a module at `<commit>^`); Concern and F-04 corrected with measured figures and the rule-dependence stated. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric C/G (interface contract) | `tools/lost_guard_census.py` `main` (`do_all` computed from section flags); `nzzu8n` E-01, `sk2rbf` E-04 `--from-json` | E-01 did not say whether `--uncited` suppresses the default `--all` run, what `--format json` does without `--uncited`, the JSON shape for several commits, or that JSON stdout must be pure. Each gap would break the `--from-json` handoff that two later plans consume. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01: `--uncited` joins the `do_all` exclusion list and is not added to `--all`; JSON is one flat sorted list, each record carrying `commit`, stdout only; `--format json` alone exits 2; record keys enumerated. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric D/E (anti-regression, test design) | `tests/test_lost_guard_census.py` `_setup_repo` (counts asserted by `test_synthetic_census_computation` and others); `test_cli_summary_output_and_rules` (subprocess with `cwd=repo`) | E-02 allowed extending `_setup_repo`, which would change counts four existing tests pin, and prescribed in-process `main(...)` "with cwd set", which changes the process cwd under xdist. It also did not exercise the function-local import rule or the text totals line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires a sibling fixture, subprocess CLI calls with `cwd=repo`, a function-local import case, a text-totals vs `--summary` equality check and the exit-2 case. |
| PR-004 | MEDIUM | UNDER-SCOPE | Rubric G (live-artifact criteria), D | E-01 Expected outcome ("prints 209 rows"); Required tests ("baseline run taken at execution start") with no item capturing it | The expected outcome used a live count (209) that drifts as comments change; no item captured the execution-start bare-suite baseline the V-03 comparison needs; nothing checked that existing sections stay unchanged. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expected outcome re-derives equality at execution with 209 as context; V-01 captures the baseline and a before/after `--summary` diff; V-03 compares failing node ids. |
| PR-005 | LOW | UNDER-SCOPE | Rubric E (sensitivity evidence) | V-02 (one mutant); E-02 Expected outcome ("would fail if the cited file were included") | Only the `recreated_at_head` mutant was demanded, so the cited-exclusion and import-rule sensitivity claims were unproven; the scratch-copy method was not spelled out. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 demands three mutants with the exact scratch-copy command, demonstrated at review. |
| PR-006 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Plan "Approval and execution gate" (one paragraph) | Gate lacked the scope fence as a declaration with `--scope-reason`/`--scope-ack`, staged-set verification, and the invariants. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten as an itemized contract. |
| PR-007 | LOW | IN-SCOPE | AGENTS.md execution contract (no dashes in user-facing prose); `plan-review.md` 3.1 item 5 | E-03 (README); OQ-01 `- Owner: none` | `tools/README.md` is user-facing and the plan did not carry the no-em/en-dash rule; a resolved question named no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and V-03 carry the rule; OQ-01 owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which import parse rule defines `imports`? | All nodes via `ast.walk`; `level == 0` only; `from agent_workflows import N` counts `N` only if it was a module at `<commit>^`. | Module-level only (misses 5 files that import inside functions); counting every imported name (would treat re-exports as modules). | Review probe: 13 vs 18 empty files; no non-module `from agent_workflows import` occurs today, so the existence check costs nothing now and prevents a silent misreport later. | yes |
| D-2 | JSON shape for several positional commits? | One flat list, each record carrying `commit`. | A dict keyed by commit. Rejected: `--from-json` consumers (`nzzu8n` E-01) expect "every listed path", which a flat list serves directly. | `nzzu8n` E-01; OQ-01. | yes |
| D-3 | What does `--format json` do without `--uncited`? | `parser.error` (exit 2). | Ignore it and print text. Rejected: a consumer would get unparsable output silently (P: prevent silent failure). | Rubric F "Prevent silent failure". | yes |
| D-4 | Is `--uncited` part of `--all`? | No; it is a section flag that suppresses the default all-run. | Add it to `--all`. Rejected: would change the existing default output, which the plan's Scope OUT forbids. | Plan Scope OUT ("changing any existing census count or counting rule"); `main` `do_all`. | yes |
| D-5 | Does "at HEAD" mean the working tree or `git ls-tree HEAD`? | Working tree, as the census already does. | `git ls-tree`. Rejected: inconsistent with `scan_axis_a`'s `dangling_paths`, which reads disk. | `scan_axis_a` (`(repo_root / p).is_file()`). | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
