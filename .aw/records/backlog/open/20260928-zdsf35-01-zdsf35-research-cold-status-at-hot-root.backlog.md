- Id: zdsf35
- Status: open
- Set: zdsf35
- Priority: low
- Work-Kind: chore
- Summary: 35 research docs carry a cold status (reference/archive) while sitting at the hot root, so the physical tier contradicts the frontmatter status

## Workflow history
- 2026-09-28 created (aw backlog): 35 research docs carry a cold status (reference/archive) while sitting at the hot root, so the physical tier contradicts the frontmatter status

MEASURED 2026-09-28 while authoring plan 4a8yws (backlog 5u7mug), which fixes the aw set WRITE path that could create the mirror-image state.

Of 123 conformant research docs (64 in cold shards, 59 at the hot root), 35 carry a normalized status of 'reference' or 'archive' while living at the research root rather than in a 'reference/YYYYMM' or 'archive/YYYYMM' shard. Example: 20260726-awdeliv-00-cnkyvn-aw-delivery-and-clean-delta.gpt56.research-report.md is 'status: reference' at the root.

The reverse direction is CLEAN: zero docs carry a hot status ('todo'/'active') inside a cold shard. Shard-month placement is also exact for the docs that ARE sharded (0 path mismatches), so this is a TIER problem only, not a date-math problem.

WHY THIS IS A CHORE AND NOT A BUG: the readers key on the frontmatter STATUS, not the path, so no answer is wrong. Measured: 'aw find research reference' locates all 35 root-dwelling docs correctly. '.aw/records/research/README.md' documents the intended invariant ('Hot states (todo/active) stay flat at this directory's root and cluster by name. Cold states live in monthly YYYYMM shards'), so the corpus contradicts documented layout without producing a user-visible wrong answer. Most of these carry a 'Migrated from ...' note, so this is migration residue.

REMEDY SHAPE (two parts, in this order):
1. A bulk 'aw research promote' pass to move the 35 docs into their shards. 'aw research promote <id6> --to reference' already computes the correct target (research_archive._shard_subpath) and works; measured 'aw research promote cnkyvn --to reference' previews 'would set cnkyvn status=reference and move to reference/202607/...'.
2. THEN a status-versus-tier DRIFT rule in 'aw research index --check' / 'aw check'. It must come second: measured, nothing currently detects a tier mismatch at all (a scratch repo clean before a stranding write is still 'index --check: clean' after it), and a rule shipped before the migration would fire on all 35 docs immediately and turn the tree red. Spec 5tapom Section 5 item 2 already contemplates drift rules in that checker.

NOT FIXED IN 4a8yws: that plan's scope is the aw set vocabulary (agent_workflows/status_set.py + its tests). It refuses the WRITE that would strand a doc going hot-into-cold; it moves no existing file and adds no checker rule.
