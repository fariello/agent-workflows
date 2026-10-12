# Review findings: plan akhwp7

- Subject-Id: akhwp7
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `f8bb627f2`. Plan committed and byte-identical to the lane input; no
pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an orchestrator.

Verified by reading and driving the code. `backlog.run_check` computes `items_count` and the `summary` wording only
inside `if ctx.is_agent or ctx.is_json:` and the human branch prints `aw backlog check: all backlog items conform.` /
`{len(drift)} violation(s).` (F-1 holds). `attention.run`'s `if check:` block hoists `summary` above the agent branch
and the human branch prints only `the view is valid.`; the no-project climb branch prints the same literal (F-2 holds).
`research_refs.run_check_refs` and `leak_sanitizer.main` compute no examined count; `--agent` records in a throwaway
repo carry no `checked` key (F-3, F-4 hold). `result_types.CommandResult.to_agent_record` emits `checked` from
`data["checked"]`. `leak_sanitizer.scan_working_tree_counted` exists with the cited shape. Every F-5 pinned substring
was re-located with `rg`. `tests/test_validator_nonsurveyable_dir.py` asserts `assertNotIn("0", proc_bl.stdout)` (F-6
holds). No doc or spec quotes a countless line (`rg` over `.aw/records/specs`, `docs`, `README.md`: none).

Measured side effect during review: a probe ran `aw backlog new --summary "Probe item" ... --apply` in a bare
`git init` directory under `/tmp/opencode/`; it climbed to a stray `/tmp/.aw/records` ancestor and wrote
`/tmp/.agents/backlog/open/20261012-o1ocmb-01-o1ocmb-probe-item.backlog.md` plus one `/tmp/.aw/records/history.jsonl`
line. The reviewer's sandbox refused cleanup outside `/tmp/opencode/`; the maintainer should delete `/tmp/.agents/`
and the trailing `o1ocmb` history line. This is the evidence behind PR-001.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric E (test isolation) | `agent_workflows/project_context.py` `find_project_root` / `resolve_verb_repo_root`; review probe: bare temp repo `attention --check --json` -> `12 items checked`; anchored repo -> `0 items checked` | E-04/E-07 said "empty initialized repo" and E-02/E-04 created items with no anchoring; a bare `init_repo` dir is not a project, so `backlog check`/`attention --check`/`research check-refs` climb to any ancestor `.aw/` and the zero tests would be host-dependent (and `backlog new` writes OUTSIDE the temp dir). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the fixture-anchoring convention and F-9; E-02/E-04/E-07 and V-03/V-06 require `.aw/records/<tree>` before the first CLI call. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (executability) | `aw backlog new --help`; probe: `--title` -> `unrecognized arguments`, `--summary` alone -> `--priority and --work-kind required` | The plan's `aw backlog new ... --apply` was underspecified; the obvious `--title` spelling (used by `specs new` in the same test file) fails. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02/E-04 pin `backlog new --summary "Probe item" --priority low --work-kind chore --apply`; F-10 added. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (test mechanics) | `tests/test_agent_checked_count.py` `_run_cli_with_fallback` (no `env` param; `AW_UNFIXED_TREE` branch copies `os.environ`); `leak_sanitizer.main` prints human verdict to stderr | E-10 required XDG isolation and asserted "human surface" without saying how the env reaches the child or which stream to read. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-10 requires an `os.environ` override, the positional `dir` arg, and stderr assertions. |
| PR-004 | LOW | IN-SCOPE | Rubric E (vacuity) | E-04 original "or ... the integer `--json` reports" fallback; review measured `1 items checked, 0 violations` on the anchored fixture | The hedged expectation made the nonzero attention test's bar undefined. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 asserts the measured string AND cross-checks `--json` `evidence[0].value.items`. |
| PR-005 | LOW | UNDER-SCOPE | Rubric D (caller census) | `agent_workflows/research_index.py` `RF.find_dangling_citations(repo_root, research_root)`; `tests/test_validator_nonsurveyable_dir.py` `test_control_empty_but_real_project_clean` | E-05 named only `plans_index` as an untouched caller; `research_index` also calls the uncounted research wrapper. The empty-project backlog assertion beside the specs `0 specs checked.` line stayed countless. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/F-3 name both callers; E-02/V-02 strengthen the empty-project backlog assertion. |
| PR-006 | LOW | IN-SCOPE | Rubric G (execution contract) | Gate section | Gate said the plan "requires `/plan-review`", lacked the outside-runner finalize path, and did not name the `AW_UNFIXED_TREE` before/after mechanism; V-03's "outside any project" run did not say how to prove the cwd is outside one. E-03 did not state info-only drift behavior. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate updated (conditional finalize, `AW_UNFIXED_TREE`); V-03 requires `find_project_root()` output first; E-03 keeps `if drift:` and states the info-only outcome. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep OQ-01 (in-place edits, not `HumanRenderer`)? | Keep the author's in-place resolution. | Renderer migration (rejected: restyles four outputs and breaks F-5 absence/presence assertions; `121j2r` precedent). | `.aw/records/plans/executed/20260929-uwerb5-01-121j2r-...ipd.md` OQ-01; F-5 `rg` results. | yes |
| D-2 | How to make zero-count fixtures deterministic? | Anchor with `.aw/records/<tree>` inside the temp repo. | Set a climb ceiling env var (rejected: none exists in `project_context.find_project_root`); always pass `--dir` (rejected: changes the tested invocation shape). | review probe F-9; existing `test_backlog_check_agent_emits_checked_zero_on_empty_tree` fixture. | yes |
| D-3 | Should attention's info-only drift path print drift lines plus `0 violations`? | Yes, keep `if drift:` unchanged. | Re-key on `exit_code` (rejected: would hide info lines the human sees today, a behavior change outside scope). | `attention.run` `if drift:` block; `check_engine` `attention.lane-superseded` RuleSpec. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
