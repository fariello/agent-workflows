- Id: cwf2bo
- Status: done
- Graduated-To: partset
- Blocks-Release: next
- Set: cwf2bo
- Priority: high
- Work-Kind: bug
- Summary: aw partition splits an orchestrator from its Set's children and admits orchestrators whose children cannot run, so every shard holding one ends fail-depend

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD 8t28wj executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261010-partset-01-8t28wj-keep-each-set-s-orchestrator-with-its-children-in-aw-partiti.ipd.md); evidence .aw/records/plans/executed/20261010-partset-01-8t28wj-keep-each-set-s-orchestrator-with-its-children-in-aw-partiti.ipd.md
- 2026-10-11 graduated (aw set): graduated to plan 8t28wj (Set partset)
- 2026-10-10 created (aw backlog): aw partition splits an orchestrator from its Set's children and admits orchestrators whose children cannot run, so every shard holding one ends fail-depend

MEASURED 2026-10-09: one 'aw partition -t plans -n 3' produced the three parallel runs run-20261009T013333Z-334392, run-20261009T024714Z-1667714 and run-20261009T030837Z-2088618. Five orchestrators were placed in a different shard from all of their children (axozpe/dirsilent shard 0 vs children shard 1; i18yaz/runwire 0 vs 1; u4glub/lifegate 0 vs 2; m0kl28/netnsfilter 0 vs 2; l4vw9o/denypush 2 vs 1), and each ended fail-depend children-not-in-this-run. Cause: agent_workflows/partition.py clusters only by declared Item-Dependencies (in_selection_edges, components); an orchestrator is joined to its children by Set membership, not by an edge, and all five declare 'Item-Dependencies: none'. Second defect: partition does not check that an admitted orchestrator's unfinished children are themselves runnable, so m0kl28 was admitted while children 2j4pd0 and wn956n were to-review and could not execute in any shard. Required behavior: (1) an orchestrator and every unfinished child of its Set land in the SAME shard (cluster like a dependency); (2) an orchestrator whose Set has an unfinished child that is not runnable or not selectable is EXCLUDED with a stated reason rather than emitted to fail. Membership is available from runner_shared.read_set_membership.
