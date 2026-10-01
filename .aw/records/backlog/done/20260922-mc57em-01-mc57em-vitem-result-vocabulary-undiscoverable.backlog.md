- Id: mc57em
- Status: done
- Graduated-To: vresultvocab
- Set: mc57em
- Priority: low
- Work-Kind: chore
- Summary: the IPD validation-result vocabulary is 'pass' but every V-item's own instruction and the lint error say nothing about it

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw oc run: IPD uh9jsk executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-vresultvocab-01-uh9jsk-state-the-accepted-validation-result-vocabulary-where-an-aut.ipd.md); evidence .aw/records/plans/executed/20260930-vresultvocab-01-uh9jsk-state-the-accepted-validation-result-vocabulary-where-an-aut.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053059Z-3200713: uh9jsk
- 2026-09-22 created (aw backlog): the IPD validation-result vocabulary is 'pass' but every V-item's own instruction and the lint error say nothing about it

FOUND while executing plan i4ak5n.

WHAT IS WRONG. A V-item is scaffolded with `- Result: pending` and its 'Required evidence' prose never states what the terminal value must be. Writing the natural word `verified` produces eight instances of two lint findings each (`IPD-S402: unknown validation result 'verified'` and `IPD-S404: not 'pass' at pre-transition`), and the message names the rejected value without naming the accepted one, so the fix is a guess or a source read.

COST. One failed lint round trip per plan for anyone who has not memorized the enum. Small, and that is why this is filed `chore` rather than `bug`: nothing is wrong with the ANSWER the tool gives, and no user waits on a slow path. It is purely a discoverability cost.

POSSIBLE SHAPES. Have IPD-S402 enumerate the accepted vocabulary in its own message (the cheapest fix and probably sufficient); or have `aw ipd sync` write the vocabulary into the scaffolded V-item as a comment; or accept `verified` as an alias.
