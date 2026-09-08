- Id: ms06pi
- Status: graduated
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
- 2026-09-08 graduated (aw set): GRADUATED to spec 2vev8j (.aw/records/specs/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md), which carries - From-Backlog: ms06pi and inherits this item's - Blocks-Release: next, so the release gate is provably handed off rather than dropped. GRADUATED, NOT DONE: the design is settled and handed off; no code is written. THE GATE IS ANSWERED. Research prompt 27rjro is consumed: five reports adopted 2026-09-08 and reconciled in 6mye7n. Four independent models reached the SAME design without conferring (front matter stays INLINE; unbounded ## Workflow history moves to git-tracked, append-only, PER-ARTIFACT JSONL keyed by the immutable id6; ordering by an explicit per-artifact seq, never by parsing dates; SQLite only as a gitignored disposable cache), and all four independently reject the single global file, tracked SQLite, moving front matter out, and bulk-reordering the corpus. WHERE THE REPORTS SPLIT, THE SPEC ADJUDICATES RATHER THAN PICKING A SIDE. On the inline residue (spec 4.5): keep exactly ONE line AND make IPD-S405 read the history API, because pavnai's justification is wrong on its own terms (executed -> superseded breaks 'the latest entry is always executed', which is precisely xn6f6u's eviction argument) while xn6f6u's conclusion assumes IPD-S405 is immovable when the rule must be rewritten anyway. On the journal path (spec 4.2): key on the IMMUTABLE id6, deciding AGAINST 2o895n's basename-derived sidecar, on a property of this repo that report could not observe (artifacts are renamed and moved constantly). THREE CLAIMS RE-MEASURED AT HEAD 57143149 RATHER THAN INHERITED, all superseding this item's own figures: the corpus is 591 plans / 15,639,697 chars, not the 483 / 10,823,121 recorded here, so the token case is STRONGER not weaker and every percentage must be re-derived at implementation; the heading is referenced by 18 modules, not the 19 this item and all four reports state; and record_history.py's own docstring claim that append-only files 'rarely conflict' is EMPIRICALLY FALSE (two branches appending one line each to the same JSONL conflict on merge), which matters doubly because aw oc run isolates every execute item in its own worktree, making the global file a conflict magnet on the normal execution path. TWO DEFECTS FOUND WHILE ANSWERING THIS, both recorded in the spec as OUT OF SCOPE so they are not absorbed silently: attention_contract.py:32-33 defines last_history_at as the LAST record in file order while the plan writers PREPEND, so the attention view reads the OLDEST record and calls it newest (a live bug, caught by takpys alone); and the specs/backlog writers append their sidecar event BEFORE validation and BEFORE the dry-run/apply decision, so a PREVIEW or a REFUSED transition can leave a phantom event. FIRST ACTION FOR THE IMPLEMENTER, ahead of any code: export and preserve .aw/records/history.jsonl. 176 of its 177 records are specs/backlog history that exists ONLY on this machine, because that inline history was already slimmed to one line while the sidecar is gitignored, so a fresh clone has NEITHER copy. This is the most damaging CURRENT defect and it is unrecoverable local state. THE SPEC IS AT to-review, NOT approved, and that is deliberate: aw specs set refused approved because the anti-self-approval floor requires a review record naming 2vev8j, and none exists. Design is handed off; IMPLEMENTATION IS NOT YET LICENSED. The spec's OQ-1 is BLOCKING and needs a human: whether backward lifecycle edges (approved -> reviewed) are legal is a policy call the event store exposes but cannot answer.
- 2026-09-08 blocked (aw set): GATE SATISFIED IN SUBSTANCE; Gate-Ref re-pointed from the prompt's PATH to its stable id6 27rjro because the prompt moved to reference/202609/ when the set was promoted, leaving the old path dangling. THE RESEARCH HAS LANDED. Five reports were adopted from .aw/inbox/ into the awmetastore set on 2026-09-08 and reconciled: takpys (GPT-5.6 Sol High), 2o895n (Sonnet 5 High), xn6f6u (Gemini 3.1 Pro High), pavnai (Gemini 3.8 Flash High), plus the consolidated finding 6mye7n. A Gemini 3.1 Pro DeepThink report was DELIBERATELY EXCLUDED on maintainer instruction: its own author's note says network restrictions prevented it reading the repository, so it reasoned from the prompt's prose alone. THE ANSWER IS UNANIMOUS ACROSS ALL FOUR: keep compact current-state front matter INLINE; move the unbounded ## Workflow history to GIT-TRACKED, APPEND-ONLY, PER-ARTIFACT JSONL keyed by the stable id6; order by an EXPLICIT PER-ARTIFACT seq integer, never by parsing dates; allow SQLite only as a gitignored disposable cache, never as the git-carried authority. Unanimously rejected: a single global history file as durable authority (what the repo has today), git-tracked SQLite, moving front matter out, and a one-time bulk reorder of the corpus (which this item and tk1gqo had already rejected independently). MEASURED IN-REPO AT HEAD 57143149 DURING RECONCILIATION, and these supersede every figure in the reports: the corpus is 591 *.ipd.md / 15,639,697 chars, materially bigger than the 483/10.8M this item records and than the newest report's 489/11.6M, so the token case is STRONGER not weaker and the percentage splits must be re-derived at implementation time rather than quoted. The global sidecar now holds 177 records, 150 backlog / 26 specs / 1 plans: the plans count is STILL 1, confirming the migration never moved. events.reverse() is still at ipd_lifecycle.py:773 and aw check plans reports 15 check.lifecycle-transition-invalid. THREE THINGS I VERIFIED THAT CORRECT OR EXTEND THE REPORTS. (1) 'Append-only files rarely conflict', asserted in record_history.py:41-55's own docstring, is FALSE: a two-branch trial where each branch appends ONE different line to the same one-line JSONL produces an ordinary content conflict on merge. That is the empirical core of the case against the global file, and it matters doubly here because aw oc run gives each execute item an isolated worktree by default, so the global file is a conflict magnet on the normal execution path. (2) The two Gemini reports contradict each other on write safety and GEMINI 3.1 PRO IS WRONG: record_history.append (record_history.py:41-71) does a bare open(p,'a') write with NO filelock, no atomic replace, no fsync, so Gemini 3.8's interleaving-corruption claim is correct. filelock is already the sole runtime dependency. (3) A SECOND LIVE DEFECT no report but GPT-5.6 caught, confirmed in the contract text: attention_contract.py:32-33 defines last_history_at as 'the date of the LAST record in file order' while plan writers PREPEND, so for any tool-touched plan the contract reads the OLDEST record and calls it the latest. Fix it in the same change. THE THREE OPEN DISAGREEMENTS, with the reconciliation's recommended settlement: whether one inline history line remains (keep ONE, but make IPD-S405 query the history API so no gate depends on the line's content, which defuses Gemini 3.1 Pro's eviction argument AND Gemini 3.8's mistaken 'latest entry is always executed' premise, since executed -> superseded breaks it); lazy vs batched migration (complementary: relax the lint gate FIRST with zero data migration per Sonnet 5, grandfather the terminal dirs per Gemini 3.8, new artifacts born v2 behind a CI ratchet per GPT-5.6, then lazy migrate-on-write); and sidecar path layout (key on the IMMUTABLE id6, NOT on the artifact basename as Sonnet 5 proposed, because this repo renames and moves artifacts constantly). FIRST ACTION FOR WHOEVER IMPLEMENTS: export and preserve the local .aw/records/history.jsonl before touching anything. 176 of its 177 records are specs/backlog history that exists ONLY on this machine, because that inline history was already slimmed to one line while the sidecar is gitignored (.aw/.gitignore:11), so a fresh clone has NEITHER copy. GPT-5.6 alone spotted this and it is unrecoverable local state. Read 6mye7n before authoring; it names which source to read for what and flags each one's unsupported claims. This item is NOT graduated by this note: it is unblocked to the extent its gate is answered, and graduation needs a spec because 19 modules read ## Workflow history and this changes a contract all of them depend on.
- 2026-09-05 blocked (aw set): Gate-Kind corrected from the invalid 'research' to 'artifact' (closed vocabulary artifact|decision|todo|issue|date|external, attention_contract.py:389). The gate is a real in-tree file, the research prompt, so 'artifact' is the right kind; 'research' was rejected by aw check backlog as backlog.gate-kind-invalid.
- 2026-09-05 created (aw backlog): Decide where aw-only artifact metadata lives (inline md vs sidecar JSONL vs sqlite) and finish the awhistory plans migration with real timestamps; tk1gqo is a symptom of the deferred b0behn follow-up
