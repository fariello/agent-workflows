# Review: Render the Section 5 lifecycle glyph in the run summary table Status cell

- Subject-Id: qhpov0
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so I skipped the pre-review snapshot. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

I verified the plan's measured claims against the lane checkout:

- `Palette(False).lifecycle_glyph(blocked, width=2)` returns `'⚠︎ '`, while `Palette(False, use_unicode=False)` returns `'! '`. This confirms F-04.
- `visible_width` returns 7 for `blocked` and 9 for `⚠︎ blocked`. This confirms F-03.
- The malformed token resolves to the `unknown` stage, whose glyph is `?` in both modes.
- The spec `uonrjg` quotations at Sections 9.1, 9.2, 9.4, R10.3 and 11 item 2 resolve verbatim.

I then prototyped E-01..E-03 directly in `render_stream.render_run_summary_table`, ran the bare suite against the prototype, and reverted it (`git status` clean afterwards). The prototype exposed three gaps that the plan's own text did not predict:

- six test failures in three files, where the plan predicted one assertion in one file;
- a mypy gate failure;
- that four further failures were pre-existing. Each of those four also failed with the prototype removed, so they are unrelated to this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Testing / anti-regression (D, E) | `tests/test_zero_dispatch_outcome.py` `test_changed_shape_byte_identity` (byte-pinned row `│ reviewed │`); `tests/test_zero_dispatch_progress_denominator.py` `test_single_reviewed_shape_byte_identical_to_pinned_output`; `tests/test_run_summary_malformed_entry.py` `w_row[5] == "executed"`, `r[5] == "reviewed"` | F-06 claimed that one existing test breaks and that "no other existing test asserts on the `Status` cell's exact text". The review prototype made 6 tests in 3 files fail. Two of those files were not in `Scope-Paths`, and E-05's outcome ("no other test edited") could not be met. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote F-06 with the measured failures. Added both files to `Scope-Paths`. E-05 now names each deliberate snapshot update (spec Section 12 permits these), requires exact new cell text instead of a weakened containment check, and requires re-deriving the broken set at execution time. V-05 now asks for the diff of every edited test. |
| PR-002 | MEDIUM | UNDER-SCOPE | Correctness / E-04 goal (A) | `render_run_summary_table` `format_progress_bar(completed_count, display_total, width=10)` and the banner literal `(In: {tot_in_str} │ Out: ...`; measured `U+2502`, `U+2588` in a `use_unicode=False` render; `PYTHONIOENCODING=ascii` direct `runner_shared.print_status` raises `UnicodeEncodeError` | E-04's expected outcome, "prints the ASCII fallback instead of a ... `UnicodeEncodeError`", cannot be met by E-04 alone. The table's ASCII mode still emits `│` in the banner and `█` in the progress bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-09 and E-06/V-06. E-06 passes `use_unicode` to the progress bar and uses `vl` for the banner separators, with Unicode-mode bytes unchanged. Reworded E-04's outcome. E-05 gained check (f), which asserts no code point above U+007F. |
| PR-003 | MEDIUM | IN-SCOPE | Executability (G) | prototype of E-02: `agent_workflows/render_stream.py` `Unsupported operand types for + ("str" and "bool")` from `tests/test_typecheck_gate.py` | The naive `glyph + st_val` fails the shipped mypy gate because `items_data` values are inferred as a union type. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires `str(st_val)` and cites the gate. `tests/test_typecheck_gate.py` was added to the targeted validation command. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence accuracy / executability | `runner_shared.print_status` (`Palette(should_color(sys.stdout))`, no `should_unicode` binding); `runner_shared.should_color` docstring on the module-level import guard; `tests/test_lost_guard_census.py` `test_no_new_module_level_first_party_import_in_runner_shared` | F-05 and E-04 said "six" call sites, but all seven omit `use_unicode`. The cited `Palette(..., use_unicode=should_unicode(...))` contrast is a per-item attempt palette, not a summary call. E-04 claimed that `should_unicode` "is already re-exported", which is false for `runner_shared`, where a module-level import is refused by a guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected F-05 and E-04 to seven sites, each named by its enclosing function. E-04 now prescribes a function-local import in `print_status`, following the module's existing convention. |
| PR-005 | MEDIUM | IN-SCOPE | Validation feasibility / safety (E, B) | plan V-04 "`aw oc run --help`-adjacent status path ... under `AW_ASCII_ONLY=1`"; plan V-05 "via `git stash` of the production hunks"; AGENTS.md shared-checkout rule | V-04's demonstration was vague, and on a UTF-8 stream it would not exercise the encode failure. V-05 told the executor to `git stash`, which can sweep a co-worker's uncommitted work in a shared checkout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now prescribes a concrete `PYTHONIOENCODING=ascii` `print_status` run on a minimal `state.json`, which the review showed fails today, plus an `AW_ASCII_ONLY=1` run. V-05 uses a detached temporary worktree at a recorded `<base>`. |
| PR-006 | LOW | IN-SCOPE | Execution contract (G) | plan "Approval and execution gate" | The gate did not state that open questions are resolved, that `Scope-Paths` is a declaration with no stop clause, or the conditional finalize ownership between runner and executor. It also said `phdpbf` "is set `graduated` ... by the runner", but that already happened. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all contract elements. The finalize step is runner-owned under `aw oc/agy run` and executor-owned by hand. Hand `git mv` is forbidden. |
| PR-007 | LOW | IN-SCOPE | Clarity | plan E-03, E-05(c) | E-03 did not say that the raw cell must use the unstyled marker. E-05(c) asked for a VS-bearing glyph in the ASCII-box mode, which ASCII mode cannot contain. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now names `style=False` for the raw cell. E-05(c) clarifies what ASCII mode proves. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should OQ-01 (render the glyph at all) stay resolved without asking the maintainer? | Keep it resolved yes | Re-open OQ-01 for maintainer ruling | Spec `uonrjg` Section 9.1 "glyph MUST immediately precede either id6 or status", Section 11 item 2 "Glyph and color are redundant cues", and Section 12 "Human snapshot changes are expected where the new marker is introduced" | yes |
| D-2 | Should the two ASCII-mode leaks (banner `│`, progress `█`) be fixed in this plan or filed separately? | Fix here as E-06 | File a backlog item and narrow E-04's outcome | Same function and same `use_unicode` parameter; without the fix, E-04's stated outcome is unreachable (measured `UnicodeEncodeError`); spec Section 9.3 requires the ASCII fallback under stream capability | yes |
| D-3 | Should the broken byte-pinned snapshots be updated, or should the plan avoid widening the box? | Update them as deliberate snapshot changes | Keep the column width fixed, which is impossible once the glyph is added | Spec `uonrjg` Section 12; precedent `attention.py` "Status column's width grows from 8 to 10" | yes |
