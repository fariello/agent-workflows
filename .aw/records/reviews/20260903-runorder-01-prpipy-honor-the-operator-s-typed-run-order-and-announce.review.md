# Review: Honor the operator's typed run order and announce every reordering

- Plan-Id: prpipy
- Reviewed-At: 2026-09-03
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `25d3f0b050a2fbe81d532e59ceef70066c0a63d8`, working tree clean, target plan
committed and unchanged, so the pre-review snapshot was correctly skipped per Step 1. Structural
preflight `aw ipd lint --phase author` reported `conforming` before review and
`--phase review-finalize` reported `conforming` after the revisions.

The plan's central claim is TRUE and I re-measured it rather than trusting it. `queue_sort_key`
(`oc_runipd.py:3596`) returns `(dependency_depth, setid, order, id6, position)`;
`agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` is True at this HEAD; and run
`run-20260901T042331Z-118022` records `selectors ['m73aet','6lu3rq']` with `position 1 m73aet` /
`position 2 6lu3rq` in `state.json` while `events.jsonl` shows `6lu3rq` `ipd-started` at
`2026-09-01T04:23:31` and `m73aet` at `04:44:10`. The inversion is measured fact, not inference, and
`"runmixed" < "runtrail"` explains it exactly as the plan says.

The dominant finding is that the fix was ONE-SIDED in a way the plan did not notice, because the
sort key is shared while the two surfaces that make the order VISIBLE are not. The maintainer ruled
the widening rather than accepting a recorded divergence.

Verified TRUE, beyond the above: the existing test that will invert really is at
`tests/test_runner_item_dependencies.py:745-757` with exactly the shape described; the declared-edge
guard the plan must not break really exists at `:725`; `test_position_is_never_renumbered_by_ordering`
(`:759`) and `test_missing_order_key_still_sorts` (`:769`) both exist and are correctly named as
must-stay-green; and spec `25kzda` 5.4 rule 4 really reads as quoted at `:826` with no mention of
operator order, which vindicates the plan's judgement that the SPEC is what needed the decision.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | UNDER-SCOPE | C. Architecture / G. Plan executability | `agy_runipd.print_status is oc_runipd.print_status` -> False; `agy_runipd.py:4331` (own `print_status`), `:4691` (own `--prepare-only`), `:1920` (own `initialize_run`), `:1990` (own `position` assignment); versus `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` -> True; plan's `- Scope-Paths:` omitted `agy_runipd.py` | THE PLAN WAS ONE-SIDED, and asymmetrically so, which is the worst shape. E-02's sort-key fix reaches BOTH drivers automatically because the function is genuinely shared. But the announcement's site (`initialize_run`) and the preview's site (`print_status`) are defined SEPARATELY in each runner, and `agy_runipd.py` was not in Scope-Paths. So executing the plan as written would give `aw agy run` the changed ORDERING while leaving it with no announcement and a still-misleading preview: the reordering would become silent on one host precisely because the fix for silence was not applied there. This is the same defect class the `rununify` Set exists to remove and that this repo has already been bitten by (`Heartbeat`/`stallfp-01`, where a display fix "silently did not reach `aw agy run`"). | C:Low; U:Low; S:Low; F:Medium; Overall:Low (adding a second call site to a shared formatter is bounded and mechanically verifiable) | FIXED | Maintainer ruled widen-to-both-drivers-now. Added `agent_workflows/agy_runipd.py` to Scope-Paths and to the scope fence; added E-07 requiring the antigravity wiring with V-07 demanding agy's own output for all three cases plus a single-definition check proving the message text is SHARED not copied; rewrote E-04 to build the formatter in `render_stream.py` and E-05 to fix the sort in the shared renderer; recorded as F-9. |
| PR-102 | MEDIUM | IN-SCOPE | G. Plan executability | E-04 as authored said only "at queue build"; the real anchor is `initialize_run` (`oc_runipd.py:2860`) where `position` is assigned (`for position, id6 in enumerate(queue_ids, start=1)`, `:2930`); the expressed order's source is `queue_ids` from `expand_selectors` / `state["selectors"]` | E-04 named neither the SITE to announce from nor the SOURCE of the "expressed order" it must compare against. Both are load-bearing: there is exactly one point where the queue is frozen and `position` assigned, and an announcement built anywhere else would either run before the order exists or after the first child spawns. Worse, the expressed order has no single obvious source (selectors, `queue_ids`, or the stored positions), and choosing wrongly produces a message that LOOKS truthful while comparing the wrong two lists, which is undetectable by a passing test. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now names `initialize_run` as the only correct site with the `position`-assignment line, and names `queue_ids` / `state["selectors"]` as the expressed order's source, with the reason spelled out so the executor does not re-derive it. |
| PR-103 | MEDIUM | IN-SCOPE | F. UX / A. Correctness of the claim | `oc_runipd.py:2519` `expand_selectors` accepts `all`, `reviews`, a setid, and a file path; `build_dynamic_manifest:2392` orders each set by `(order, path.name)`; measured `expand_selectors(m, ['all'])` -> 30 ids led by `wslayout` order 0..5, i.e. MANIFEST order | The plan (and the backlog item) speak throughout of "the operator's TYPED order", but `position` records REQUEST order, which equals typed order only when the selectors were literal id6 tokens. For a setid or `all`, `position` reflects manifest expansion order that the operator never typed. The plan's own Deferred section shows awareness of the expansion case for the SORT decision, but E-04's user-facing MESSAGE inherits the typed-order language, so the announcement would tell an operator "you asked for this order" about an order the manifest chose. A warning that misdescribes its own cause trains operators to ignore it, which defeats the item's whole purpose. | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires the message to say "requested order" and to reserve typed-order phrasing for the literal-id6 case; V-04 requires an expanded-selector case be pasted showing it does not claim the operator typed that order; recorded as F-10. |
| PR-104 | LOW | IN-SCOPE | A. Correctness (evidence located at its true source) | `render_stream.py:903` `queue = state.get("queue", [])`, `:929` `for idx, item in enumerate(queue)`, `:930` `pos = item.get("position", idx + 1)` | F-5 correctly says no sort is applied between `state` and the table, but locates the defect at the CALLER (`print_status` -> `render_run_summary_table`). The defect is really in the RENDERER, which iterates the stored queue and prints `position` as its leading column. That distinction decides where the fix belongs: fixed in the renderer it covers both hosts in one edit; fixed in one driver's `print_status` it must be done twice and can drift. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now cites the renderer's own lines and directs the fix there, with the explicit caveat that if the renderer cannot reach `queue_sort_key` without importing a runner, each driver sorts before calling and says so (a renderer importing a runner would be a new layering defect). Recorded as F-11. |
| PR-105 | LOW | IN-SCOPE | E. Testing and verification | V-06 as authored required "`aw check` clean for the spec file"; the repo carries pre-existing `aw check plans` errors (13, recorded in `0soncw`'s and `5e4sb6`'s own histories) | V-06 demanded an unachievable evidence bar. "Clean" cannot be produced here, so the item would either block a correct spec edit or, more likely, invite an executor to paste something narrower and call it clean - which is exactly the false-evidence pattern the honesty rule exists to prevent. Parity against a pre-measurement is both achievable and strictly more informative. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-06 now requires `aw check` BEFORE and AFTER with the finding set shown UNCHANGED for the file, and states explicitly why "clean" is the wrong bar. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-04 must persist the ordering rationale in "durable run state/events". Should the review specify WHICH (a new `state.json` key, or a new `events.jsonl` event type)? | NO. Leave the choice to the executor, and require only that the rationale be READ BACK from durable state as V-04 evidence. | (a) Mandate a new `events.jsonl` event type. Rejected: `events.jsonl` is an append-only per-item timeline (`ipd-started`, `ipd-auto-approved`), and a run-level ordering decision is not an item event, so mandating it would force an awkward shape. (b) Mandate a `state.json` key. Rejected on the same evidence: `state` is written by the shared `save_state`/`atomic_write_json` path and `818uru` is queued to move exactly those symbols, so pinning a schema detail here would create a needless collision with an approved sibling Set. | `oc_runipd.py:3047` (`save_state` writes `state.json` then `write_report`); `events.jsonl` contents of run `run-20260901T042331Z-118022` (per-item events only); `818uru`'s Scope-Paths claim `save_state`'s seam | yes |
