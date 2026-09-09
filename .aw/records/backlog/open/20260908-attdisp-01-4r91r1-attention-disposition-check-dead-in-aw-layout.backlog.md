- Id: 4r91r1
- Status: open
- Set: attdisp
- Priority: high
- Work-Kind: bug
- Summary: aw attention's disposition-mismatch check is silently dead in the .aw layout: its path guard tests a legacy prefix that never matches, and its index would be wrong even if it did

## Workflow history
- 2026-09-08 created (aw backlog): FOUND 2026-09-08 by measurement while checking, at the maintainer's challenge, whether a tracked-only status-versus-directory audit already existed (during the review of 6ltz1y OQ-03). Maintainer approved filing. TWO INDEPENDENT BUGS IN FOUR LINES at attention.py:900-916. BUG 1: the guard rel.startswith('.agents/plans/') never matches, because _rel_posix (:241) returns an un-normalized path and this repository's plans are at .aw/records/plans/..., so disp is '' and the mismatch branch is unreachable. The normalization DOES exist at _classify_tree (:245) but is local to that function and is not applied to the rel passed into _plans_record at :370, so the code was written for the legacy layout and silently stopped working when .aw became default. BUG 2: rel.split('/')[2] would yield 'plans' under the .aw layout, so merely widening the prefix test would NOT fix it. MEASURED both ways: an .aw-layout plan in executed/ carrying Status: superseded produces NO drift, while the byte-identical file under .agents/ produces attention.disposition-mismatch. Priority HIGH because aw attention is the designated 'what needs attention' answer, is consumed by agents, and aw attention --check is fail-closed for CI, so a silent clean verdict is worse than an absent rule; and because the SAME invariant's other enforcement surface (IPD-M105) has its own separate gap filed as dbslfm, leaving both surfaces blind. The fix must address the layout coupling at its root rather than one branch (grep for other .agents/ assumptions first), must reuse an existing shard-safe disposition helper rather than a third index-arithmetic version, and must measure the corpus blast radius before enabling, since the branch has never run on real data. No Blocks-Release set: needs the blast-radius number first.

/tmp/opencode/b2.md
