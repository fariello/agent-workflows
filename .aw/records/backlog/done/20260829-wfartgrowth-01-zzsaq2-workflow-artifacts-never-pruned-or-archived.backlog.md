- Id: zzsaq2
- Status: done
- Graduated-To: wfprune
- Set: wfartgrowth
- Priority: low
- Work-Kind: chore
- Summary: Nothing prunes or archives .aw/workflow-artifacts/, so per-run workflow dirs accumulate unbounded in a gitignored tree

## Workflow history
- 2026-09-26 set (aw backlog): closed by aw oc run: IPD muza7y executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260924-wfprune-01-muza7y-prune-aged-workflow-artifacts-run-dirs-with-a-dry-run-by-def.ipd.md); evidence .aw/records/plans/executed/20260924-wfprune-01-muza7y-prune-aged-workflow-artifacts-run-dirs-with-a-dry-run-by-def.ipd.md
- 2026-09-25 graduated (aw set): graduated into wfprune plan muza7y (to-review)
- 2026-08-29 created (aw backlog): Nothing prunes or archives .aw/workflow-artifacts/, so per-run workflow dirs accumulate unbounded in a gitignored tree

Found incidentally while designing the revgate Set (2026-08-29); NOT caused by that work.

.aw/workflow-artifacts/ accumulates one directory per workflow run (assess-*, advise-*, release-review,
...). Measured: 31 dirs at maxdepth 2. Nothing cycles them - grepping agent_workflows/*.py for
prune/archive/clean/retain/ttl against 'workflow-artifacts' returns exactly ONE hit, and it is
clean_delta.py:507 (a delivery-mode path filter), not a retention policy.

The tree is gitignored (.gitignore:68), which is correct for machine-local run noise, but it means growth
is invisible in the repo and nothing ever reclaims it.

WHY THIS IS ONLY LOW/MEDIUM: the contents are disposable by design and cost only disk. The reason it
surfaced at all is that set_records.py:143-158 writes the autonomous-decisions register (DECISIONS_FILE /
OPEN_QUESTIONS_FILE, :41-42) into this tree, so any DURABLE decision record placed here would be both
invisible and eventually reclaimable-by-accident. The revgate Set (c621h9 Order 04) avoids that by putting
the durable copy in the tracked review artifact and leaving this tree as the disposable convenience copy,
which is the existing convention for private/scratch copies. So the durability concern is already handled
elsewhere; what remains here is purely unbounded growth.

POSSIBLE SHAPES: an 'aw archive' verb extension covering workflow-artifacts, a retention window (keep last
N runs per workflow, or younger than a date), or an explicit 'aw clean' with a dry-run default. Do NOT
un-ignore the tree; it holds run noise and would create churn and leak-surface.

Confirm before acting that no workflow depends on an OLD run's artifacts dir still existing (the run-record
readers resolve .aw/workflow-artifacts/<workflow>/<run-id>/, e.g. run_cli's decisions/questions
inspectors), so a retention policy must not break inspection of a run a human may still want to read.
