# Review findings: plan y1vjzp

- Subject-Id: y1vjzp
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e63fcc2a8`. The plan was byte-identical to the lane input. `aw ipd lint --phase author --agent`: `clean`. Child plan. Prerequisites `epsti7` and `mtmqlm` are `reviewed`, not executed, so `awaiting-human` and the stored qids do not exist in code yet; their contracts were read from those plans.

Verified:
- `render_stream.format_statusline_lines` renders a 4-line rectangular box; the bottom border holds the tally (left), run id (centre) and stop badge (right). `Statusline._render_lines_unlocked` reads `self.state`; `print_final_statusline` is the closing render. Both hosts construct `Statusline(..., run_dir=run_dir, state=state)`. Rendered a sample box at review: 120 columns per line.
- No BEL is written anywhere in the runners. Presentation overrides are `--quiet`/`--raw` (`runner_shared.add_output_mode_flags`, `options["output_mode"]`) and `--as-agent`; there is no `--plain`.
- `attention.get_active_runs_map` maps `canonical_run_status(raw) or raw`; measured `canonical_run_status("awaiting-human") == "awaiting-human"`, `_RUN_PRIORITY_ORDER.get("awaiting-human") is None`, `_RUN_STATUS_ALIASES` lacks it. `_render_table_row` slices the run column to 14 characters. `_resolve_run_lifecycle("awaiting-human").stage == "waiting-input"`; `_resolve_run_lifecycle("question").stage == "unknown"`.
- `attention.render_json` keys are append-only per its `stranded_lanes` comment; liveness is `run_viewer.driver_holder_state` (flock acquirability).
- Spec `6kwd2e` R4a.3-R4a.6, R9.6, A10d-A10h, A46 read as cited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (label) | agent_workflows/attention.py `_resolve_run_lifecycle`; `lifecycle_style` `("awaiting-human", WAITING_INPUT)` | The chosen label `question` resolves to lifecycle stage `unknown`, losing the waiting-input glyph and color, and would itself be an unrecognized run status in filters and priority. Priority 0 also lets any other live run's status for the same id6 win. | all Low | FIXED | E-03 uses `awaiting-human` (fits the 14-character column, resolves to waiting-input), adds it to `_RUN_STATUS_ALIASES` with alias `question`, and ranks it below `running`. OQ-01 / D-1. |
| PR-002 | HIGH | IN-SCOPE | Executability (bell wiring) | plan E-02; no BEL anywhere; `epsti7` E-02/E-06 park branches | The plan named no call site for the bell, cited a nonexistent `--plain` override, and gave no ordering between persisting `bell_rung` and writing, so a crash could double-ring and a first park on a non-TTY could consume the bell. | all Low | FIXED | E-02 defines `ring_bell_on_first_park`, called from both park branches; gated on TTY, `output_mode == "clean"`, not agent mode; persist-then-write; set only when actually written. |
| PR-003 | MEDIUM | IN-SCOPE | Correctness (count source) | plan E-01 "read from the queue items' open questions"; spec A10d | Undefined counting source (items or questions, which file); a per-second render must not do inbox I/O. | all Low | FIXED | Pure `parked_question_count(state)` from stored qids, fallback `item["questions"]`; fixtures for 1-per-item and 2-on-1. |
| PR-004 | MEDIUM | IN-SCOPE | UI/regression (layout) | `format_statusline_lines` bottom border; `test_format_statusline_user_example_box_layout` byte-pins the default box | "on the bottom border" did not name a segment, a collision with the stop badge, truncation, or the zero-question byte-identity that existing tests pin. | all Low | FIXED | E-01 places the badge in the stop-badge slot, moves it to the col 3-4 span when a stop is shown, keeps rectangularity, and keeps zero-question output byte-identical. |
| PR-005 | MEDIUM | UNDER-SCOPE | Right-sizing | plan E-03 (label + count + human + JSON) | E-03 bundled two independent surfaces (the run-column label and a new run-level count in two output formats); `aw ipd lint` raised `IPD-Z602`. | all Low | FIXED | Split: E-03 label, new E-05 count (`get_parked_question_counts`, human line printed without `--runs`, appended JSON key `parked_questions`); V-05 added. |
| PR-006 | MEDIUM | IN-SCOPE | Testing (liveness reachability) | `run_viewer.driver_holder_state` flock probe; plan E-04 "with a live driver lock" | A lock FILE alone reads as not live; the test would silently show nothing. | all Low | FIXED | E-04 holds `driver.lock` from a helper process during the assertion and runs the existing statusline and attention suites. |
| PR-007 | LOW | IN-SCOPE | Process | Required tests `-q` | `-q` hides `N passed`; the regression suites were not in the command. | all Low | FIXED | Dropped `-q`; added statusline and attention suites. |

`aw ipd sync --apply` assigned E-05/V-05. `aw ipd lint --phase review-finalize --agent`: `clean` (the earlier `IPD-Z602` cleared by the split).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which run label for a parked item? (OQ-01) | `awaiting-human`, with `question` as a filter alias. | `question` (REJECTED: resolves to stage `unknown`, measured); `waiting` (REJECTED: a second invented word for one status). | `_resolve_run_lifecycle` measurement; spec R4a.6 only requires an explicit non-fallback, non-blocked label. | yes |
| D-2 | When is the bell suppressed? | Non-TTY, `--quiet`, `--raw`, agent mode. | Also suppress under `NO_COLOR` (REJECTED: NO_COLOR governs color, not sound; spec says the presentation override flags). | spec R4a.5; `runner_shared.add_output_mode_flags`. | yes |
| D-3 | Does the attention parked-count line require `--runs`? | No, printed whenever a live run holds one. | Only under `--runs` (REJECTED: R4a.6 "without the human knowing to run a run-specific verb"). | spec R4a.6. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
