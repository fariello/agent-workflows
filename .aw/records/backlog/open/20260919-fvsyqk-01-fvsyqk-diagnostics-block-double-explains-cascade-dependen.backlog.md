- Id: fvsyqk
- Status: open
- Blocks-Release: next
- Set: fvsyqk
- Priority: medium
- Work-Kind: bug
- Summary: render_stream's diagnostics block renders a cascade-blocked dependency with two contradictory reasons, e.g. 'executed:aaa111 (target reviewed) (blocked)'

## Workflow history
- 2026-09-19 created (aw backlog): render_stream's diagnostics block renders a cascade-blocked dependency with two contradictory reasons, e.g. 'executed:aaa111 (target reviewed) (blocked)'

MEASURED 2026-09-19 at HEAD 7562ca6c while executing plan m85gxh. The key 'unsatisfied_dependencies' has TWO producers writing DIFFERENT shapes. (1) Each driver's drain path writes a BARE token list plus a separate 'unsatisfied_dependency_reasons' map from dependency_status_detailed. (2) cascade_dependency_blocked writes the reason INTO the token itself (dead.append(f'{edge.canonical()} (target {st})')) and writes NO reason map at all. render_stream.render_run_summary_table's diagnostics block reads both with a single fallback: ', '.join(f'{d} ({reasons.get(d, "blocked")})' for d in deps). For producer (2) that renders 'executed:aaa111 (target reviewed) (blocked)', i.e. the already-embedded reason followed by a contradictory placeholder, on the surface an operator reads at 3am. USER-PERCEPTIBLE: the line is operator-facing output whose two parenthetical reasons disagree, so a reader cannot tell which is authoritative; filed 'bug' on that basis rather than on redundancy. Plan m85gxh's own renderer (run_selection_policy.render_queue_dispositions) fixes this for ITS line by omitting the placeholder when no reason was recorded, and pins it with tests/test_run_selection_policy.py::test_a_dependency_token_that_already_carries_its_reason_is_not_double_explained. render_stream.py was OUTSIDE that plan's scope fence (it is owned by orchprobe r2i1b1's diagnostics work), so the divergence is reported here rather than edited there. Candidate fixes: have cascade_dependency_blocked write the reason map like the drain path does (preferred, since it makes the two producers agree), or drop the placeholder in the renderer.
