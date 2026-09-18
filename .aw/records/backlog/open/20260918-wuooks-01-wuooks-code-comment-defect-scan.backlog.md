- Id: wuooks
- Status: open
- Set: wuooks
- Priority: low
- Work-Kind: chore
- Summary: Source-code comments are never scanned for defects and the one TODO/FIXME scanner that exists is diff-scoped and unwired

## Workflow history
- 2026-09-18 created (aw backlog): Source-code comments are never scanned for defects and the one TODO/FIXME scanner that exists is diff-scoped and unwired

Named as explicitly OUT OF SCOPE by durablecapture 01 (`rnkqrc`) and filed here so the gap has a durable carrier rather than living only in that plan's prose.

THE GAP, as `rnkqrc` measured it: `artifact_core.py` limits reading to `.md`/`.txt`, so no records-tree check can ever see a `TODO`/`FIXME` in source. A TODO/FIXME scanner does exist but is DIFF-SCOPED and UNWIRED, so it runs nowhere by default.

WHY THIS IS NOT OBVIOUSLY WORTH DOING, stated so nobody treats it as a queued task: a repository-wide comment scan is a large false-positive surface, and `rnkqrc` deliberately chose the DECLARATION route (a typed carrier field on an IPD row) over detection precisely because detection is what it could not make deterministic. Decide whether the comment surface is worth any gate at all before building one; "no, and here is why" is a legitimate resolution that closes this item.
