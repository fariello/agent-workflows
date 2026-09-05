- Id: ms06pi
- Status: blocked
- Gate-Kind: artifact
- Gate-Ref: .aw/records/research/20260905-awmetastore-00-27rjro-where-aw-metadata-should-live.research-prompt.md
- Blocks-Release: next
- Set: awmetastore
- Priority: high
- Work-Kind: chore
- Summary: Decide where aw-only artifact metadata lives (inline md vs sidecar JSONL vs sqlite) and finish the awhistory plans migration with real timestamps; tk1gqo is a symptom of the deferred b0behn follow-up

MAINTAINER DIRECTION 2026-09-05: research this BEFORE touching the reader again. Asked whether to
land an interim parser fix or investigate first, the maintainer chose to research it properly, so an
interim patch that took `check.lifecycle-transition-invalid` from 15 findings to 3 was written,
measured, and then DELIBERATELY REVERTED rather than committed. CI stays red on that gate meanwhile.
That is the intended state, not an oversight.

WHY THIS IS AN ARCHITECTURE QUESTION AND NOT A PARSER BUG. `tk1gqo` reports 15
`check.lifecycle-transition-invalid` diagnostics against plans that are not malformed. The cause is
that `## Workflow history` has no enforced ordering: the status TOOLS (`aw set`, `aw spec set`,
`aw ipd dependencies set`) PREPEND while human and agent AUTHORS APPEND, so a file touched by both
holds both orderings and no fixed-direction reader can be right. Three fixes were tried and measured:

- reverse (shipped behavior, `ipd_lifecycle.py` `_plan_status_events`): 15 findings;
- sort by date, stable: 32 findings, WORSE, because `date` is day-granular so same-day bursts
  (`draft -> to-review -> reviewed` in one day) carry no sequence and ties fell back to whichever
  writer touched the file last;
- sort by date, tiebreak by lifecycle rank: 3 findings, but it INFERS the order from the forward-only
  invariant rather than knowing it, and cannot represent a legitimate same-day re-review after
  approval, which spec `25kzda:267` explicitly permits.

The residual 3 are real cross-day `approved -> reviewed` round trips. No reader can separate those
from a genuine backwards transition, because THE DURABLE RECORD DOES NOT CARRY ENOUGH INFORMATION to
reconstruct the sequence. That is a storage-design defect, which is why it is filed here rather than
as a follow-up to the parser.

THE MIGRATION THIS FINISHES ALREADY EXISTS AND STALLED AT THE BIGGEST TREE. The `awhistory` Set
(`x97z83`, `im90a5`, `b0behn`, `cizkf4`, all executed) built the global append-only sidecar
`.aw/records/history.jsonl` plus `agent_workflows/record_history.py`, routed SPECS and BACKLOG to it,
and slimmed their inline history to the latest single line. `b0behn`'s scope excluded plans verbatim:
"EXPLICIT GUARD - PLANS/IPD `## Workflow history` ... it MUST NOT slim any plan/IPD history, because
`ipd_lint` IPD-S405 requires the inline `executed` entry at post-transition; the IPD lifecycle
transition + research writers are a separate follow-up, not this Order." Measured: the sidecar holds
128 records, 108 backlog / 19 specs / 1 plans. So plans are the ONLY tree still carrying full inline
history, which is exactly why the ambiguity lives there and nowhere else.

MOVING PLANS TO THE SIDECAR AS BUILT WOULD NOT FIX IT. The sidecar's own `date` field is day-granular
(`"date": "20260819"`), identical in precision to the inline format, so the tie problem reproduces.
Real timestamps are part of the work, not an optional extra. Related second defect recorded in
`tk1gqo`: the tools stamp history dates in UTC while authors write LOCAL dates, so an evening action
is dated one day in the future relative to hand-written lines in the same file.

MEASURED COST OF THE STATUS QUO, which is the other half of the question (maintainer note `tmp/notes.md`
item 3: agents pay to read and rewrite metadata they never reason about). Across 483 `*.ipd.md`:
total 10,823,121 chars (~2.7M tokens); front matter 512,880 (4.7%); `## Workflow history` 1,101,804
(10.2%); tool-owned subtotal 1,614,684 chars, ~404k tokens, 14.9% of the corpus. Median plan 17,031
chars, median history 1,692, largest history 15,801 (one plan is 20.0% history). History is
append-only prose, so it grows without bound.

BLAST RADIUS TO SIZE BEFORE DESIGNING: 19 modules reference `## Workflow history` (`attention.py`,
`attention_contract.py`, `backlog.py`, `check_engine.py`, `cli.py`, `doctor.py`, `engine.py`,
`ipd_lifecycle.py`, `ipd_lint.py`, `ipd_schema.py`, `plan_readiness.py`, `record_history.py`,
`releases.py`, `review_findings.py`, `selectors.py`, `set_records.py`, `specs.py`, `status_set.py`,
`status_untooled_gate.py`). Two consumers constrain any design directly: `ipd_lint` IPD-S405 REQUIRES
an inline `executed` entry, and `aw attention` derives `last_history_at` from the inline record date.

DO NOT resolve this by reordering the plan histories. That satisfies a parser while contradicting the
convention the executed corpus follows, and `tk1gqo` already considered and rejected it.

## Workflow history
- 2026-09-05 blocked (aw set): Gate-Kind corrected from the invalid 'research' to 'artifact' (closed vocabulary artifact|decision|todo|issue|date|external, attention_contract.py:389). The gate is a real in-tree file, the research prompt, so 'artifact' is the right kind; 'research' was rejected by aw check backlog as backlog.gate-kind-invalid.
- 2026-09-05 created (aw backlog): Decide where aw-only artifact metadata lives (inline md vs sidecar JSONL vs sqlite) and finish the awhistory plans migration with real timestamps; tk1gqo is a symptom of the deferred b0behn follow-up
