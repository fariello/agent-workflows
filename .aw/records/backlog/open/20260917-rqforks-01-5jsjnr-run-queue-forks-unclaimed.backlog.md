- Id: 5jsjnr
- Status: open
- Set: rqforks
- Priority: medium
- Work-Kind: chore
- Summary: Nine of run_queue's eleven still-forked dependencies are claimed by no rununify child, so the Set cannot reach 100% de-duplication for it

## Workflow history
- 2026-09-17 created (aw backlog): Measured while executing rununify Order 08 (ty3cj6) E-01/E-04

## The gap

The maintainer's 2026-09-16 directive for the `rununify` Set is that at the end of it "there should
be one code base shared by the two runners that contains 100% of the otherwise redundant code". For
`run_queue` the Set as authored cannot reach that, and the shortfall is measurable rather than a
matter of taste.

Measured at HEAD `24932638`, `run_queue` closes over 41 module-level names, of which ELEVEN are real
forks (defined independently in both runners). Who lifts them:

| Symbol | Owning sibling | Does that sibling lift it? |
|---|---|---|
| `render_continuation_hint` | `tx6q0h` (04) E-02 | YES, named explicitly |
| `write_report` | `tx6q0h` (04) E-04 | YES, and it repairs a live `run_viewer` badge defect |
| `driver_actor` | `tx6q0h` (04) E-05 | NO, DELIBERATELY REFUSED: a host CAPABILITY difference (oc reads a profile subsystem that greps to zero in `agy_runipd.py`, so lifting ships dead branches) |
| `disable_lane_prompt` | pinned by `tests/test_runner_shared.py::UnmovableSymbolTests` | NEVER. Writes `_LANE_PROMPT_DISABLED` through `global` while each host's diverged `_lane_reclaim_prompt` reads its own copy |
| `execute_item` | `yrqyxb` (07), EXECUTED | NO: that plan measured and guarded rather than splitting; its own analysis recommends extracting cohesive blocks first |
| `_observe_between_turn_stop` | none | NO |
| `_record_deliberate_stop` | none | NO |
| `reconcile_interrupted` | none | NO |
| `requeue_interrupted` | none | NO |
| `reclaim_lanes_on_interrupt` | none | NO |
| `retry_deferred_integrations` | none | NO |

So TWO of eleven clear through sibling work, ONE is refused on evidence a later plan cannot simply
overrule, ONE can never move, and SEVEN are claimed by no plan in the Set at all.

## The part that is good news, and is the actionable half

FOUR of the seven unclaimed forks are CLOSURE-CLEAN TODAY, i.e. every module-level name they close
over already resolves in `runner_shared` (or is stdlib, or is the sanctioned `save_state` wrapper).
They are liftable right now, individually, without `run_queue` moving at all:

| Symbol | oc / agy code lines | Differing code lines | Closure |
|---|---|---|---|
| `_observe_between_turn_stop` | 33 / 27 | 12 | clean (`sys`, `Path`, `runner_stop`) |
| `_record_deliberate_stop` | 19 / 17 | 8 | clean (adds `append_jsonl`, `utc_now`) |
| `requeue_interrupted` | 39 / 32 | 15 | clean (same set) |
| `reconcile_interrupted` | 69 / 69 | 2 | clean (adds `extract_session_id`, `resolve_plan_path`, `plan_bucket`, `save_state`) |

`reconcile_interrupted` is notable: 69 code lines on both hosts differing by TWO. `reclaim_lanes_on_interrupt`
is similarly near-identical (134/134, two differing lines) but is NOT clean, because it closes over
both `disable_lane_prompt` and `_lane_reclaim_prompt`, the pair sibling `i3d6ml` measured as sharing
an unmovable module global (its backlog `8hx3g3`).

## Suggested work

Author a child (or extend `tx6q0h`) to lift the four closure-clean forks as individual acts, each
with its own behavioral pin. That reduces `run_queue`'s fork count from eleven to five without
touching the dispatch loop, and it is the first two steps of the sequence plan `ty3cj6`'s E-04
recommends. Then decide explicitly whether `driver_actor` and `disable_lane_prompt` are PERMANENT
host hooks, since if they are, "100% de-duplication" for this function means a shared core plus a
hook carrying exactly those two, and that is worth stating as the target rather than discovering.
