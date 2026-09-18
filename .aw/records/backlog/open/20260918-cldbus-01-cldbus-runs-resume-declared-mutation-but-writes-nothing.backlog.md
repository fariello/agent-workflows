- Id: cldbus
- Status: open
- Set: cldbus
- Priority: low
- Work-Kind: chore
- Summary: aw runs resume is declared a mutation but writes nothing

## Workflow history
- 2026-09-18 created (aw backlog): aw runs resume is declared a mutation but writes nothing

MEASURED WHILE EXECUTING runanalytics Order 09 (ixis0c) E-01, by a test that derives the mutating verbs under `aw runs` from COMMAND_INVENTORY rather than hand-listing them.

`runs resume` carries `command_class="mutation"` in `agent_workflows/command_surface.py`, but it writes nothing. Its handler `run_cli._run_resume` calls `run_recovery.resume`, whose whole body is `engine.reconstruct_state()` + `detect_unknown_outcomes()` + `get_runnable_steps()`, and then prints a report. No ledger append, no file write, no commit. `run_cli`'s own module docstring says so explicitly: "`next` and `resume` sound like actions but only reconstruct state and report, which is why they are" viewers. `run_viewer.RUNS_VIEWER_LEAF_NAMES` also contains `resume`, i.e. the viewer vocabulary and the normative inventory disagree about the same leaf.

WHY IT MATTERS, beyond tidiness. `command_class` is not a label: `tests/conformance_matrix.required_scenarios` DERIVES each leaf's required conformance coverage from it. Declaring `resume` a mutation demands a `success_preview` row it does not need and, because `domain_failure` is required only for read/check/bare classes, SUPPRESSES the domain-failure scenario for a verb whose exit contract is `(0, 3)` and which genuinely has a blocking failure path (`EXIT_BLOCKED` on an interrupted side effect). So the misdeclaration costs real coverage on the one outcome `resume` exists to produce.

Its sibling `runs next` is declared `read`, and the two are described together as reconstruct-and-report verbs, which is the evidence for what `resume` should be.

NOT FIXED HERE DELIBERATELY. `command_surface.py` is in ixis0c's Scope-Paths only for ADDING the two Order 09 leaves; re-classifying an unrelated shipped leaf changes which conformance scenarios CI demands for it, which is a separate change with its own verification (the slow `output-conformance` job across Python 3.9-3.14) and should not ride inside a data-sharing plan.

SUGGESTED FIX: change `runs resume` to `command_class="read"` (matching `runs next`), then re-run `tests/test_cli_conformance_matrix.py` and `tests/test_cli_quality_gates.py` explicitly, since both are `pytest.mark.slow` and a bare suite deselects them.
