- Id: csjq81
- Status: graduated
- Graduated-To: csjq81
- Set: csjq81
- Priority: low
- Work-Kind: chore
- Summary: The dependency diagnostics line prints the dependency token twice, because dependency_status_detailed's reason strings already begin with the token the renderer parenthesizes them after

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053059Z-3200713: p22nrx
- 2026-09-28 created (aw backlog): Filed at /plan-review of plan 5o1jye.

MEASURED 2026-09-28 at HEAD 04352120 while reviewing plan `5o1jye` (from backlog `fvsyqk`).

Every reason string `dependency_status_detailed` produces is PREFIXED WITH ITS OWN TOKEN, because `edge_satisfied` composes each refusal as `f"{tok}: ..."`. Both consumers then compose `<token> (<reason>)`, so the token appears twice on one line.

Measured through the real functions, not by reading source:

    reason: executed:5o1jye: external target 5o1jye is 'to-review' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)
    render_run_summary_table line:
      • eee555: dependency-blocked (executed:5o1jye (executed:5o1jye: external target 5o1jye is 'to-review' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)))

WHY `chore` AND NOT `bug`: the line states ONE authoritative reason, so nothing on it disagrees with anything else and no reader is misled about the facts. It is verbose, and the nesting is hard to scan, but there is no wrong answer and no measurable wait. This is deliberately distinguished from `fvsyqk`, which was `bug` because its two parenthetical reasons DISAGREED and a reader could not tell which was authoritative.

THE FIX IS NOT AS LOCAL AS IT LOOKS, which is why it is filed rather than folded into a nearby plan. The reason strings are read by at least four surfaces: `render_stream.render_run_summary_table`'s diagnostics block, `runner_shared.write_report`'s `## Dependency blocks (why)` section (which renders `- <token>: <reason>`, so the duplication shows there too), the `dependency-blocked` event's `reasons` map in `events.jsonl` (durable, already on disk in many run directories), and `run_selection_policy.derive_item_disposition`, which SUBSTRING-MATCHES the prose to pick its external-versus-in-run disposition code. So stripping the prefix at the producer changes a durable record format and touches a live code-selection predicate; stripping it at each renderer duplicates logic across two modules and leaves the events stream as-is.

FIX DIRECTION (not decided): probably have the renderers print the reason ALONE when it already starts with `<token>:`, since that keeps the durable event records byte-identical and needs no change to the predicate that matches the prose. Decide whether `write_report`'s `- <token>: <reason>` form wants the same treatment.

Plan `5o1jye` does not fix this; it only constrains its own NEW cascade prose (E-02) not to add a third instance of the pattern, and records the measurement as its F-11.
