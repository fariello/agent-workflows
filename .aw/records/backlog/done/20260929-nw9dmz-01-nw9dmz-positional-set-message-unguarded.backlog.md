- Id: nw9dmz
- Status: done
- Graduated-To: nw9dmz
- Blocks-Release: next
- Set: nw9dmz
- Priority: medium
- Work-Kind: bug
- Summary: The positional aw <tree> set <status> <selector> spelling writes an unvalidated --message into a record history, so a newline in it forges a workflow history record on every tree the shared setter serves

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw agy run: IPD 4gwgo3 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-nw9dmz-01-4gwgo3-refuse-an-unsafe-descriptive-value-at-the-shared-cross-tree.ipd.md); evidence .aw/records/plans/executed/20260930-nw9dmz-01-4gwgo3-refuse-an-unsafe-descriptive-value-at-the-shared-cross-tree.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 4gwgo3
- 2026-09-29 created (aw backlog): The positional aw <tree> set <status> <selector> spelling writes an unvalidated --message into a record history, so a newline in it forges a workflow history record on every tree the shared setter serves

FILED AS THE CARRIER for the positional-spelling row in plan `uz05bl` (Set `qbz8i1`), which guards the `--status` spelling of `aw specs set` and `aw specs note` but cannot reach the positional one. It is the SAME residue that executed plan `dtg7dz` deferred for the backlog tree in its finding F-15, so this item replaces that plan's carrier pointer at `qbz8i1` with a durable owner of its own.

WHY ONE ITEM RATHER THAN ONE PER TREE: the positional spelling dispatches to the SHARED cross-tree setter `status_set.run_set_command` rather than to each tree's own `run_set`, so there is exactly one unguarded call site and it serves plans, specs, releases, prompts and backlog at once. `agent_workflows/runner_shared.py` already documents this dispatch split at length for a different reason ("THE `--status` SPELLING IS DELIBERATE AND LOAD-BEARING ... positional dispatches to `status_set.run_set_command`, which does NOT run the shared release-gate close predicate").

MEASURED FOR THE BACKLOG TREE 2026-09-28 (`dtg7dz` F-15, driven through the real CLI in a fresh `git init` fixture): `python3 -m agent_workflows backlog set parked <id6> --message $'note\n- Blocks-Release: next'` exited **0** and wrote `- Blocks-Release: next` as a history line at zero `validate_item` drift. THE OTHER FOUR TREES ARE INFERRED FROM THE SHARED DISPATCH AND HAVE NOT BEEN DRIVEN; whoever fixes this MUST measure each tree rather than trusting the inference, and should expect the harm to be provenance forgery (a fabricated `approved ... --by-human` history record) rather than a smuggled metadata bullet, since the value lands in the history body.

WHY IT WAS DEFERRED TWICE RATHER THAN FOLDED INTO EITHER FIX: a guard in the shared setter changes behavior for five trees in one edit, and a length bound shaped for one tree would regress the others. The per-tree measurement of committed history-record messages over the 300-character `MAX_DESCRIPTIVE_LEN` bound is: specs 59/146 (40.4%), backlog 531/1483 (35.8%), plans 1549/3990 (38.8%), max 5667 characters. So the correct fix is LINE INTEGRITY ONLY (newline, carriage return, control characters; NOT length), which is the `bound_length=False` mode both shipped helpers already implement. Closing it is a cross-tree contract decision about whether the shared setter bounds a message at all, plus one uniform guard.
