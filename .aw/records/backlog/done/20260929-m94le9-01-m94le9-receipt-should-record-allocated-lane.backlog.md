- Id: m94le9
- Status: done
- Graduated-To: m94le9
- Set: m94le9
- Priority: low
- Work-Kind: followup
- Summary: Decide whether the begin receipt should record the allocated lane branch, making the lane-name enumerating resolver in plan iqtt8d unnecessary

## Workflow history
- 2026-10-07 done (aw backlog): closed by aw agy run: IPD 42ertq executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-m94le9-01-42ertq-record-the-allocated-lane-in-the-begin-receipt-so-the-scope.ipd.md); evidence .aw/records/plans/executed/20261001-m94le9-01-42ertq-record-the-allocated-lane-in-the-begin-receipt-so-the-scope.ipd.md
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: 42ertq
- 2026-09-29 created (aw backlog): Filed as the durable carrier for OQ-02 of plan iqtt8d (Set fkmjoy).

CARRIER for OQ-02 of plan `iqtt8d` (Set `fkmjoy`, from backlog `fkmjoy`).

THE QUESTION. Plan `iqtt8d` makes `check.scope-drift` find the lane an execution ACTUALLY ran in by ENUMERATING git refs (`refs/heads/aw/lane/*`) and selecting the candidate whose HEAD descends from the receipt's frozen `base_head`. It does that because nothing records WHICH lane an execution got. Should the begin receipt (or durable run state) simply record the allocated lane branch instead, so the identity is read rather than inferred?

THE CASE FOR IT. Inference from branch names is a derived answer to a question the system already knew: `worktree_lease.allocate_worktree` returns a `WorktreeHandle` carrying the exact `branch`, `lane_id` and `base_commit`, and the runner already persists those into run state as `worktree_branch`/`worktree_lane_id`/`worktree_base`. Recording it where the advisory can read it would delete a whole class of name-reconstruction bug. That class is REAL and RECURRING: `lane_branch_name`'s docstring already warns callers 'must NOT reconstruct this by hand from an id6, because allocation may attempt-scope the name', `lane_id_from_branch` exists because that mistake was measured under `resumedupe txc9l1`, and `iqtt8d` documents a SECOND instance of it in `check_engine._plan_execution_tree`.

WHY IT WAS NOT DONE IN THAT PLAN. It changes the receipt SCHEMA (`RECEIPT_SCHEMA_VERSION`), touches BOTH runners, and needs a compatibility story for receipts already on disk, while delivering nothing the resolver does not already deliver for EXISTING receipts. The resolver also keeps working for a lane allocated by a path that writes no run state (`aw work begin` allocates through the same lease and records its own lease file, not a receipt field).

THE TRAP TO AVOID, which is why this is filed as a separate decision rather than an obvious improvement. The adjacent proposal of RE-ISSUING the receipt when the runner attempt-scopes was REJECTED on in-tree evidence in `iqtt8d` (F-7): `ipd_lifecycle.refreeze_receipt`'s docstring records that a fresh `begin` recaptures `base_head` at the CURRENT head, which 'would therefore make every path the item changed INVISIBLE to the scope reconciliation', and `refreeze_receipt` deliberately KEEPS `base_head` for that reason. Any work here must ADD lane metadata WITHOUT touching `base_head`. There is also an ordering constraint: on the self-finalize path `runner_shared` calls `driver_begin` BEFORE `allocate_isolation_worktree`, so the lane does not exist when the receipt is written, and the field would have to be filled by a later update rather than at issue time.

IF ADOPTED, `iqtt8d`'s resolver becomes redundant for new receipts. That plan states that in such a case it should be SUPERSEDED rather than amended.

OWNER: maintainer (a design-direction call).

PRECONDITION: plan `iqtt8d` should be executed or retired first, since the two are alternative implementations of the same repair.
