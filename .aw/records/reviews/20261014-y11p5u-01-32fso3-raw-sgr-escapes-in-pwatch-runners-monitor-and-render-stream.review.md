# Review findings: plan 32fso3

- Subject-Id: 32fso3
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`dc5e5ba1b`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` conforming after revisions.

Re-verified at review HEAD:
- `term.resolve_color_depth`, `term.color_16_for_index`, `term.DEPTH_NONE/16/256`, `term.COLOR_DEPTHS`, `Term.lifecycle_depth` exist (`agent_workflows/term.py`).
- `color_16_for_index`: `214->33`, `196->31`, `67->36`, `16->31`, `81->96`, `186->33`, `220->93`, `203->31`, `255->37`, `241->90`, `48->36` (F-03 confirmed).
- `Palette(True)("boom","red","bold")` at pin `16` emits `\x1b[31;1mboom\x1b[0m`; `Palette.__call__` has no depth check (F-01 confirmed for that surface).
- `pwatch.py` C_* constants at lines 31-59; runner decoration `\033[38;5;81m` in `pwatch.main`; `runners_monitor.render_runner_table` and `run_table_dashboard` literals as the plan cites.
- `render_stream.make_badge`, `format_stop_badge`, `format_tally_badge`, `format_statusline_lines` literals as cited.
- `format_run_summary_box` does NOT exist; the `color = pal.enabled` site and `c_bold..c_reset` literals are in `render_stream.render_run_summary_table`.
- `tools/pwatch.py` re-exports every `agent_workflows.pwatch` attribute; `tools/watch-agy.py` imports it.
- `.github/workflows/tests.yml` matrix: ubuntu, macos, windows. `pwatch.read_processes` raises `RuntimeError` without `/proc`.
- With `NO_COLOR=1`, `term.resolve_color_depth(override=True)` returns `256`.
- `tests/test_term.py` stale `F-08` / `cvtg9u` text present in both class docstrings and the `Cell 3` comment.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Executability / evidence | `agent_workflows/render_stream.py:3946` `render_run_summary_table`; `color = pal.enabled` at :3986 | The plan names `format_run_summary_box` in Scope, Goal, E-03, E-04, Proposed changes, and V-03. No such function exists, so an executor could not find the target. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every reference was renamed to `render_run_summary_table`, and E-03 step 5 notes the correction. Added F-06 with the probe counts measured at review (pin `none` emits 40 SGR escapes). |
| PR-002 | HIGH | UNDER-SCOPE | E. Portability / test isolation | `.github/workflows/tests.yml` matrix `windows-latest`, `macos-latest`; `agent_workflows/pwatch.py:239` `read_processes` raises without `/proc`; `runners_monitor.sample_runners` sleeps and reads `/proc` | The E-04 tests drive `pwatch.main` and `run_table_dashboard` but did not say to isolate them from the real process table or runners. They would error on macOS and Windows CI, and on Linux they would depend on whatever the host is running. Signal handlers set by the entry points were not restored either. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires patching `read_processes`, `find_active_runners`, `extract_journey_info`, and `sample_runners`, a `_FakeTTY` stdout, restored signal handlers, and counting SGR escapes only. V-04 asks for proof of the patches. |
| PR-003 | MEDIUM | IN-SCOPE | D. Anti-regression | plan E-02/E-03/V-02/V-03 "byte-identical to HEAD"; V-02 compared escape counts only | The plan claims pin `256` output stays byte-identical, but the only evidence demanded was escape counts. No pre-edit byte capture existed, and E-02's index constants dropped the bold prefix without saying `bold=True` is needed at each former bold site. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now writes a pre-edit pin-`256` `repr` dump from a fixed probe under `/tmp`. V-02, V-03, and V-06 require an empty `diff` against it. E-02 lists which constants were bold. |
| PR-004 | MEDIUM | IN-SCOPE | C. Compatibility | `tools/pwatch.py:25-31` re-export loop and docstring | E-02 deleted the 18 `pwatch.C_*` constants. F-05 claimed nothing else references them, but `tools/pwatch.py` re-exports them on purpose for operator code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 keeps the constants as deprecated 256-tier aliases that no render path uses. F-05 was corrected and the Scope check updated. |
| PR-005 | MEDIUM | IN-SCOPE | E. Testing correctness | `agent_workflows/term.py:547` `resolve_color_depth` (rung 1 delegated to `should_color(override=...)`); probe `NO_COLOR=1` -> `256` | E-02/E-03 helpers resolve with `override=True`, which skips `NO_COLOR`. The `NO_COLOR=1` test cells, if run through the library functions, would fail for a reason the plan did not anticipate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-07. The `NO_COLOR=1` cells in E-04 are now limited to the CLI entry points, which resolve depth with the stream. |
| PR-006 | LOW | IN-SCOPE | G. Right-sizing | plan E-02 (two modules), E-04 (docstrings plus new tests) | E-02 combined two modules with separate test surfaces, and E-04 combined a comment-only edit with a new test class. Each needed several unrelated checks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split out E-06 (`runners_monitor`, with V-06) and E-07 (`tests/test_term.py` docstrings, with V-07). Dependencies, Proposed changes, gate order, and `Highest E allocated: 07` were updated to match. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The scope-fence wording read as a prohibition rather than a declaration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded as a declaration that names the `--scope-reason` route. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Delete or keep `pwatch.C_*` constants? | Keep as unused deprecated aliases | Delete (breaks re-export surface); rewrite them as depth-aware properties (module constants cannot be) | `tools/pwatch.py:25-31` re-export docstring | yes |
| D-2 | Where must `NO_COLOR` be asserted? | Only via `pwatch.main` / `run_table_dashboard` | Make library helpers re-read `NO_COLOR` (second color decision, the defect `z8ddk0` closed per `term.resolve_color_depth` docstring) | `agent_workflows/term.py:547` docstring; review probe | yes |
| D-3 | How to prove pin-256 byte identity? | Pre-edit `/tmp` repr dump and post-edit diff | Escape counts only (cannot catch byte drift) | rubric D; plan's own "byte-identical" claim | yes |
| D-4 | Is a spec amendment needed? | No | Amend `uonrjg` | `uonrjg` already defines one depth package-wide; this plan brings non-`Term` surfaces into line with it | yes |
