# Review findings: plan 8t28wj

- Subject-Id: 8t28wj
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `66401aeb1` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `partition.in_selection_edges` / `partition.components` cluster only on `item_dependencies`; `partition.collect` raises "ineligible for runner dispatch" for any resolved selector path whose action is skip, enforces `require_homogeneous_action` and slices `max_count` before returning.
- `runner_shared.read_set_membership`, `SetMember.is_orchestrator`, `set_retirement_terminal_statuses` (= `ipd_schema.TERMINAL`), `evaluate_set_retirement`, `find_unauthored_child_rows` exist as cited; `children-not-in-this-run` is `ORCH_REASON_CHILDREN_NOT_IN_RUN`, produced by `decide_orchestrator_dispatch`, not by `evaluate_set_retirement` (which yields `unfinished-children`).
- `action_for_status('ipd', ...)`: to-review -> review, reviewed -> undetermined, approved -> execute, executed -> skip.
- `agent_schema.validate_agent_record`: exit 2 requires outcome `cannot-run` or `error`.
- `cli._run_partition` passes the stdout `term`; `Term(stream=...)` judges color per stream; `term.set_color_override` is applied process-wide by `cli.main`.
- Reproduction on the E-01 fixture (scratch repo under gitignored `.aw/state/`): `aw partition -t plans approved -n 3 --run none --json` -> `[achl01, aorch0]`, `[achl02, bchl02]`, `[achl03, borch0]` (premise holds). `aw partition -t plans setb` -> exit 2 `item 'bchl01' with status 'executed' is ineligible`.
- Live corpus: `approved` -> 3 candidates `j7dsci` (Set `tf4jz5`, no orchestrator), `m0kl28` (netnsfilter, all children terminal, retirement eligible), `ytas91` (Set `fixfirst`, orchestrator `lxb1ew` and children `62sdwr`, `iksylm` `reviewed`).
- `--allow-mixed`, `--allow-drafts`, `--allow-uncovered-orchestrator-work` exist in `agent_workflows/*.py` (OQ-02 naming basis holds).
- No spec or doc under `docs/`/`README.md` describes `aw partition`.
- Backlog `cwf2bo`: `bug`, `Blocks-Release: next`, graduated to `partset`; plan carries From-Backlog and the gate.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Correctness | `partition.collect` selector loop "is ineligible for runner dispatch"; measured `aw partition -t plans setb` exit 2 | The plan's recommended fix "select the Set by its setid" and E-06 (e) "selecting by setid passes" are unreachable: a setid selector errors on any finished member, i.e. on nearly every real Set. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-08 (1): a setid selector skips finished members; an explicit id6 of a finished plan still errors. V-08 demands both. |
| PR-002 | HIGH | UNDER-SCOPE | A. Correctness | `partition.collect` `require_homogeneous_action` check; `run_partition` passes `True` | A Set mixing approved and to-review members trips the generic "mixed actions" error inside `collect` before any Set classification, so E-04's refusal could never fire for the plan's own canonical case when the to-review member is selected. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-08 (3): plans defer homogeneity until after classification; differing Set members become BLOCKED `needs-<action>`; non-Set mixes keep the existing message. |
| PR-003 | MEDIUM | UNDER-SCOPE | A. Correctness | `partition.collect` `max_count` slice | `--max` is applied inside `collect`, so the classifier cannot know which members `--max` excluded or compute N for "raise --max to N". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 (2): factor truncation into a helper `collect` still calls; `run_partition` truncates after collecting so exclusions are known; N defined. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness | `runner_shared.evaluate_set_retirement` checks 2 and 4; `find_unauthored_child_rows` | "COMPLETE-ABLE" ignored the runner's other refusal causes (no children, unauthored or unparseable child table), so partition could still emit an orchestrator guaranteed to fail, violating OQ-01 "never run an orchestrator that cannot successfully execute". The E-01 fixture as written (no child table) would itself trip this. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds the retirement preconditions with cause `orchestrator-cannot-retire`; E-01 fixture must carry a child table; E-06 (j) tests it. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness / D. Anti-regression | live corpus Set `tf4jz5` (no orchestrator); E-02 classification rules | Classifying every Set would refuse orchestrator-less Sets (or finished-orchestrator Sets) whose unselected siblings are unfinished, a regression with no retirement to protect. Also an unselected unfinished orchestrator was not classified at all. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 classifies only Sets with an unfinished orchestrator; the orchestrator itself is a classified member; E-06 (h) covers the no-orchestrator Set. |
| PR-006 | MEDIUM | IN-SCOPE | B/E. Machine output contract | `agent_schema.validate_agent_record` exit-2 rule; `test_cli_partition_json_shape` exact key set | `--agent` refusal shape was unspecified (exit 2 needs `cannot-run`/`error`), JSON stdout placement unstated, and `--allow-partial-sets` output change could break the pinned success key set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 specifies JSON on stdout, agent record `exit 2`/`cannot-run`, validated; E-05 adds `held_back_orchestrators` only when non-empty; V-04/V-05 demand them. |
| PR-007 | MEDIUM | IN-SCOPE | F. UX | `cli._run_partition` passes stdout `term`; `Term(stream=...)` | Coloring stderr with the stdout-bound term mis-detects color when stdout is piped; refusal must use a stderr-bound term. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and conventions name `Term(stream=sys.stderr)` with the process-wide override; E-06 (g) adds `NO_COLOR`. |
| PR-008 | MEDIUM | IN-SCOPE | E. Testing / live criteria | E-07 live run; corpus measured at review | E-07's live bar was output-shaped and the bare suite demanded fully green with no baseline; the corpus drifts and other parties own failures. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07/V-07 now state a re-derived property and a by-name baseline comparison, with the review-time measurement as context only. |
| PR-009 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked OQ status, `aw ipd begin`, scope-as-declaration with `--scope-reason`/`--scope-ack` (needed for the declared-but-unedited `tests/test_partition.py`), the MUST-paste rule, staged-set check, conditional finalize ownership, and the release-gate handoff. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten; Scope check notes the `--scope-ack`. |
| PR-010 | LOW | IN-SCOPE | Evidence / clarity | F-05; E-01 "tests use `tmp_path`"; E-01 "E-05's tests"; E-03 oversized wording; E-04 example | F-05 attributed `children-not-in-this-run` to `evaluate_set_retirement`; E-01 fixture location contradicted itself and cited the wrong E for tests; E-03 "notes the imbalance" had no surface; E-04 example uses a historical state and an informal approval command. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 corrected, F-07..F-09 added; E-01 fixture in gitignored scratch, cites E-06; E-03 names the `note:` line and the optional-edges keyword; E-04 example labelled historical, fix uses `aw ipd set approved <id6> --by-human`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | When one selected Set cannot finish, refuse the whole batch or drop only that Set? | Refuse the whole batch (no commands, exit 2) | Emit other Sets and drop the incomplete one with a warning | OQ-01 maintainer text "Refuse the run ... without a special arg"; fail-closed; dropping silently is what `--allow-partial-sets` opts into | yes |
| D-2 | Which Sets are classified? | Only Sets with an unfinished orchestrator on disk | Every Set with a selected member | F-05/OQ-01 concern is orchestrator failure; orchestrator-less Sets have no retirement; avoids regression on `tf4jz5` | yes |
| D-3 | How does a setid selector treat finished members? | Skip them; id6 selectors of finished plans still error | Keep erroring; add a new flag | F-08 measurement; plan's own fix hint requires it | yes |
| D-4 | Where is homogeneity checked for plans? | After Set classification in `run_partition`, Set members becoming BLOCKED | Keep in `collect` | F-09; otherwise the canonical refusal never fires | yes |
| D-5 | Do retirement preconditions (children exist, child table authored) count toward COMPLETE-ABLE? | Yes, cause `orchestrator-cannot-retire` | Only child statuses | OQ-01 "never run an orchestrator that cannot successfully execute"; `evaluate_set_retirement` checks 2 and 4 | yes |
