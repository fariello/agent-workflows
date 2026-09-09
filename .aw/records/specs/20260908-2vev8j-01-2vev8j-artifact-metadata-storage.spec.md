# Spec: Artifact metadata storage: per-artifact history journals and explicit event ordering

- Date: 2026-09-08
- Status: reviewed
- Id: 2vev8j
- Author: aw specs new
- Scope: Where aw-owned artifact metadata lives: front matter stays inline; unbounded workflow history moves to git-tracked per-artifact JSONL keyed by id6, ordered by an explicit per-artifact seq
- From-Backlog: ms06pi
- Blocks-Release: next
- Canonical: true

## 1. Problem statement

`## Workflow history` has NO ENFORCED ORDERING, and four mutually incompatible orderings ship
simultaneously with no spec adjudicating any of them. The status TOOLS PREPEND
(`status_set.py:885`, `new_lines.insert(i + 1, hist_entry)`), human and agent AUTHORS APPEND, the
specs and backlog writers REPLACE (keeping only the latest line, `specs.py:342-346`), and
`record_history.append` is order-free. The reader assumes newest-first and REVERSES
(`ipd_lifecycle.py:773`, `events.reverse()`). A file touched by both a tool and an author therefore
holds two opposite orderings and no fixed-direction reader can be right about both halves.

The visible symptom is `check.lifecycle-transition-invalid`: 15 diagnostics at HEAD `57143149`
against plans that are NOT malformed, reporting impossible backwards transitions such as
`to-review -> draft`. Backlog `tk1gqo` catalogues it; three reader-only fixes were measured and all
three failed (reverse = 15, stable date sort = 32 i.e. WORSE, date-plus-lifecycle-rank = 3 but it
INFERS order from the forward-only invariant and cannot represent a legitimate same-day re-review
after approval). The residual 3 are real cross-day round trips that NO reader can distinguish from a
genuine violation, because THE DURABLE RECORD DOES NOT CARRY ENOUGH INFORMATION to reconstruct the
sequence. That is a STORAGE-DESIGN defect, which is why this spec exists rather than a parser patch.

The maintainer ruled 2026-09-05 to research the storage question BEFORE touching the reader again; an
interim patch taking the count from 15 to 3 was written, measured, and DELIBERATELY REVERTED rather
than committed. `aw check plans` stays red on this rule meanwhile, BY DECISION.

## 2. Evidence

Research prompt `27rjro` was answered by four independent reports, reconciled in `6mye7n`
(`.aw/records/research/reference/202609/`). All four INDEPENDENTLY recommended the same design, which
is the strongest evidence available here: `takpys` (GPT-5.6 Sol High, the only one citing a commit,
`4763eb8d`), `2o895n` (Sonnet 5 High), `xn6f6u` (Gemini 3.1 Pro High), `pavnai` (Gemini 3.8 Flash
High). A fifth report was excluded because its own author's note says it never read the repository.

Measured in-repo at HEAD `57143149` on 2026-09-08, and these supersede every figure in the reports:

| Fact | Value |
|---|---|
| Plans corpus | 604 `*.ipd.md`, 16,270,178 chars |
| Global sidecar | 182 records: 153 backlog, 28 specs, **1 plans** |
| Modules referencing the heading | **18** (the reports and `ms06pi` say 19) |
| `check.lifecycle-transition-invalid` | 15 |

THESE COUNTS DRIFT FAST AND THAT IS ITSELF EVIDENCE. Re-measured at review time (2026-09-08, hours
after authoring), the corpus had moved from 591 plans / 15,639,697 chars to the values above: +13
plans and +630,481 chars in one working session. The sidecar moved 177 -> 182 records with plans
still at 1. So an implementer MUST re-derive every absolute number and percentage at implementation
time rather than quoting this table; the two figures that are STABLE and load-bearing are the
PLANS-AT-1 sidecar count (the migration has not moved) and the 18-module refactor surface.

Three findings verified here rather than taken on trust, two of which CORRECT the reports:

- E1 `[Measured]` "Append-only, so line order is irrelevant and concurrent-append git merges rarely
  conflict" (`record_history.py:3-5`) is FALSE. Two branches each appending ONE different line to the
  same one-line JSONL file produce an ordinary content conflict on merge. This is the empirical core
  of the case against a single global file, and it matters doubly because `aw oc run` gives each
  execute item an ISOLATED WORKTREE by default, so the global file is a conflict magnet on the normal
  execution path.
- E2 `[Measured]` The two Gemini reports contradict each other on write safety and 3.1 Pro is WRONG:
  `record_history.append` (`record_history.py:41-71`) does a bare `open(p, "a")` write with NO
  `filelock`, no atomic replace, and no `fsync`. `filelock` is already the sole runtime dependency.
- E3 `[Measured]` A SECOND LIVE DEFECT, caught by `takpys` alone and confirmed in the contract text:
  `attention_contract.py:32-33` defines `last_history_at` as "the date of the LAST record in file
  order" while the plan writers PREPEND, so for any tool-touched plan the attention view reads the
  OLDEST record and calls it the newest.
- E4 `[Measured]` The most damaging current defect is SILENT DATA LOSS, not token cost. Specs and
  backlog have ALREADY had their inline history slimmed to one line (`specs.py:342-346`) while the
  only full log is GITIGNORED (`.aw/.gitignore:11`), so a fresh clone gets NEITHER copy. 176 of the
  177 sidecar records exist only on the maintainer's machine.

## 3. Criteria

- C1 `[Must]` Ordering is EXPLICIT and READ, never inferred from file position, line order, or dates.
- C2 `[Must]` A fresh clone carries the full durable history of every artifact. This is what E4 breaks
  today and is non-negotiable.
- C3 `[Must]` Two agents transitioning DIFFERENT artifacts never contend for the same file. Per E1
  this is a correctness property under isolated worktrees, not a performance nicety.
- C4 `[Must]` Front-matter current state stays INLINE and human-diffable. A `Status: reviewed ->
  approved` visible in a review diff is worth more than the ~4.7% it costs.
- C5 `[Must]` No writer may record an event for a transition that did not happen, and no status
  change may succeed while its durable history write silently fails.
- C6 `[Want]` Remove the unbounded, append-forever history from routine agent context while keeping it
  retrievable on demand. DIRECTIONAL, NOT A TARGET: the ~10.2% figure is inherited from the reports and
  is not re-derived here (see 3c), so no acceptance criterion asserts a percentage. What IS testable is
  that history no longer lives in the artifact body, which AC-6 and AC-8 cover.
- C7 `[Constraint]` No new runtime dependency. `filelock` is the only one and is already present.
- C8 `[Constraint]` Migration must be INCREMENTAL and interruptible. The previous attempt
  (`awhistory`) stalled at this exact tree with plans at 1 record; a design requiring an
  all-at-once rewrite will stall again.

## 3a. Non-goals

Named because a reader would otherwise reasonably assume each is in scope.

- N1 NOT a rewrite of the existing artifact prose, front-matter grammar, or any status vocabulary.
  Only the HISTORY storage and its ordering change.
- N2 NOT a decision about whether backward lifecycle edges are legal. The event store EXPOSES that
  contradiction (see OQ-1) and deliberately does not resolve it.
- N3 NOT a migration of backlog and specs off the global sidecar in this spec's scope. C2 forces a
  fix for their clone-time data loss, but WHICH fix is OQ-2.
- N4 NOT a performance or query-latency project. A SQLite cache is PERMITTED (4.6) and specified as
  disposable; building it is not required by any acceptance criterion here.
- N5 NOT the two out-of-scope defects in Section 7, which are filed separately so this spec does not
  silently absorb them.

## 3b. Acceptance criteria

Every MUST criterion in Section 3 maps to at least one criterion here, and every criterion names the
EVIDENCE that would satisfy it, so a reviewer can refuse a false claim of completion. The failure and
refusal paths are included deliberately, not only the happy path.

| ID | Covers | Criterion | Evidence that satisfies it |
|---|---|---|---|
| AC-1 | C1 | A reader of any artifact's history obtains events in a single unambiguous order that does NOT depend on file position, line order, or dates. | A test that writes events in one order, reads them back, and asserts the sequence; plus a test that SHUFFLES the journal lines on disk and asserts the read order is UNCHANGED. |
| AC-2 | C1, C6 | `events.reverse()` and every date-sort / lifecycle-rank tiebreak are GONE from the read path. | `grep` for `events.reverse` returns no hit in `ipd_lifecycle.py`; `check.lifecycle-transition-invalid` reports 0 on migrated plans, with the count pasted. |
| AC-3 | C2 | A fresh clone carries the full durable history of every migrated artifact. | Clone the repo to a new directory, read a migrated artifact's history, and paste the full event list obtained with NO access to the original working tree. |
| AC-4 | C3 | Two agents transitioning DIFFERENT artifacts never write the same file. | A test asserting the journal path is a pure function of `<id6>`; plus a two-branch merge test on two different artifacts' journals that merges CLEANLY (the converse of E1). |
| AC-5 | C3, C5 | Two concurrent writers to the SAME artifact cannot interleave or lose an event. | A concurrency test with two processes appending under the lock, asserting every event is present, `seq` is contiguous, and no line is malformed. |
| AC-6 | C4 | Front-matter current state remains inline and a status change is still visible in a review diff. | A `git diff` of a status transition showing the `- Status:` change, pasted. |
| AC-7 | C5 | A REFUSED or `--dry-run` transition leaves NO event, and a failed history write FAILS the status change rather than succeeding silently. | A test that refuses a transition and asserts the journal is byte-unchanged; a test with the journal write forced to fail, asserting the status did NOT change. |
| AC-8 | 4.5 | The single inline line is byte-reproducible from the journal head, and NO gate depends on its content. | A drift check that regenerates the line and byte-compares; plus a test that EVICTS the `executed` line (via `executed -> superseded`) and asserts IPD-S405 still passes. |
| AC-9 | 4.7, C8 | Legacy lines are imported without inventing precision, and no false transition failure is reported across them. | For a plan with legacy history: every original raw line is present in the journal with an `ordering_confidence` marker, and forward-transition validation reports nothing across pre-checkpoint records. |
| AC-10 | C7 | No new runtime dependency. | `pyproject.toml` `dependencies` is unchanged, pasted. |
| AC-11 | C8 | Migration is interruptible: a partially migrated corpus is a VALID state that both readers handle. | With one artifact migrated and one not, the same read API returns correct history for BOTH, with output pasted. |

## 3c. Honest limits

What this spec does NOT prove, stated so no consumer over-reads it:

- It does NOT prove the design is optimal. It proves four independent reports converged on it, which
  is strong evidence of soundness and NOT a proof of optimality.
- It does NOT establish the token savings. The percentages in Section 2 are inherited from the reports
  and the absolute counts drift within hours (see the note under the evidence table). Treat C6 as a
  DIRECTIONAL want whose magnitude is unmeasured here.
- It DOES now resolve whether a backward lifecycle edge is legal (4.8, maintainer decision), but it
  does NOT enumerate the full set of legal backward edges. Only `approved -> reviewed` is named; any
  other edge is illegal until the lifecycle contract enumerates it, and an implementation must fail
  closed rather than infer legality.
- It does NOT specify the event schema field-by-field. It fixes the ORDERING AUTHORITY (`seq`), the
  LOCATION (per-artifact, keyed on id6), and the AUTHORITY SPLIT; the concrete field list is
  implementation work constrained by the acceptance criteria above.
- Its migration sequencing is a PLAN, not a measured result. The claim that lint-gate-first makes the
  migration incremental is reasoned from the previous stall, not demonstrated.

## 4. Design decisions

### 4.1 The split is by FIELD LIFETIME, not by storage technology

BOUNDED CURRENT STATE stays inline; UNBOUNDED HISTORY moves out. `takpys` frames it correctly: "The
core tradeoff is not 'Markdown versus a database.' It is bounded current state versus unbounded
history."

### 4.2 History lives in git-tracked, append-only, PER-ARTIFACT JSONL keyed by `<id6>`

One journal per stable artifact identity, TRACKED (not gitignored, which is what E4 punishes). Keyed
on the IMMUTABLE `<id6>`, NOT on the artifact basename or directory: this repo renames and moves
artifacts constantly (`pending/` to `executed/`, re-slugs, regroups), so a name-derived path would
have to be moved by every lifecycle transition. This DECIDES AGAINST `2o895n`'s
`<basename>.history.jsonl` proposal, on a property of this repo that report could not observe.

### 4.3 Ordering is an explicit per-artifact `seq`; timestamps are for display only

Every event carries a contiguous per-artifact integer `seq`. That, and nothing else, is the ordering
authority. `seq` ORIGIN, stated because 4.7 introduces a checkpoint and the two must agree: for a
MIGRATED artifact `seq` 0 is the checkpoint event and real events start at 1; for an artifact BORN
under this contract `seq` starts at 1 with no checkpoint. Contiguity is per artifact, with no gaps in
either case. A full RFC 3339 UTC timestamp is retained for audit and display and is NEVER used to
order. All four reports agree; `2o895n` calls `seq` "the one piece of this recommendation I'd call
non-negotiable" and `takpys` states the consequence: "Timestamps are never the sequencing authority.
That eliminates both the day-granularity defect and the UTC-versus-local-date inversion."

This ANSWERS `tk1gqo`'s question ("is inline history normatively OLDEST-FIRST or NEWEST-FIRST?")
NEITHER WAY. The contract is to stop depending on direction at all. The reader gets SIMPLER: drop
`events.reverse()`, the date sort, and the lifecycle-rank tiebreak.

### 4.4 One timezone for every writer

The UTC-versus-local defect (`tk1gqo`'s second defect) is INDEPENDENT and needs its own fix: `seq`
alone leaves timestamps still claiming an evening action happened tomorrow. Every writer, tool and
human-facing helper alike, records UTC; local time is a RENDER-TIME concern only.

### 4.5 Exactly ONE inline history line remains, as a pure cache

The reports SPLIT here and this spec settles it. `xn6f6u` and `takpys` say strip the block entirely;
`pavnai` and `2o895n` say keep one line for `git diff` legibility. `pavnai`'s justification is WRONG
on its own terms ("the latest entry of an executed plan is always `executed`" fails the moment a plan
goes `executed -> superseded`), which is exactly `xn6f6u`'s eviction argument. But `xn6f6u`'s
CONCLUSION does not follow either, because it treats IPD-S405's current shape as immovable when the
rule must be rewritten anyway.

DECISION: keep ONE inline line AND make IPD-S405 read the history API, so NO GATE DEPENDS ON THE
LINE'S CONTENT. Eviction then becomes harmless by construction and the review-diff legibility is
kept. The line is a GENERATED VIEW and MUST be byte-reproducible from the journal head, with a drift
check and an `--apply` repair, matching this repo's existing generated-view convention.

### 4.6 SQLite only as a gitignored, disposable cache

Never the git-carried authority. All four reports reject a tracked binary in a system whose durable
state model is git diff and line merge. A rebuildable index under `.aw/state/` is permitted and needs
no merge.

### 4.7 Legacy lines are imported WITHOUT inventing precision

Preserve each legacy line verbatim as a `legacy` event carrying the observed day, its original file
ordinal, and an `ordering_confidence` marker (`known` / `inferred-from-git` / `unknown`). Start the
real chain from a `seq` 0 checkpoint accepting the current inline snapshot, and do NOT run
forward-transition validation across unordered pre-checkpoint records. This is what lets the 3
irreducible cross-day cases stop being false failures WITHOUT fabricating an order, and it is why
`aw check plans` can go green honestly.

### 4.8 A backward lifecycle edge is LEGAL as an explicit recovery transition

MAINTAINER DECISION, 2026-09-08, made during spec review in answer to OQ-1 (finding SR-007). This
resolves the spec's only blocking question.

THE CONTRADICTION IT SETTLES: `validate_transition` rejects EVERY backward rank movement, so
`approved -> reviewed` is illegal; yet the corpus contains an INTENTIONAL `approved -> reviewed ->
approved` round trip and the runner spec instructs returning a plan to `reviewed` to recover from an
invalid automated approval. The tooling forbade what the documented recovery procedure required.

THE DECISION: such an edge is LEGAL. `approved -> reviewed` is a NAMED RECOVERY TRANSITION, and
`validate_transition` must be taught to permit it rather than treating every rank decrease as wrong.

WHAT FOLLOWS, and an implementer must not miss the second point:

1. The residual `check.lifecycle-transition-invalid` cases that no reader could classify are
   RECLASSIFIED AS VALID, not suppressed. That is what lets the rule reach 0 HONESTLY rather than by
   weakening the check, and it is the difference between fixing `tk1gqo` and hiding it.
2. THE FORWARD-ONLY INVARIANT IS GONE, and that is a real cost accepted deliberately. `aw check` may
   no longer infer that a rank decrease is a defect, so the transition table must ENUMERATE which
   backward edges are legal instead of deriving legality from rank order. An implementation that
   simply removes the rank comparison would permit EVERY backward edge, which is NOT what was decided.
3. The set of legal backward edges beyond `approved -> reviewed` is NOT fixed here. Enumerate it in
   the plan status lifecycle contract (the IPD spec is the natural home) as part of the implementing
   work, and treat any edge not enumerated as illegal (fail closed).

ALTERNATIVE REJECTED: treating the corpus round trip as a defect and changing the runner's recovery
instruction. Rejected because it contradicts shipped behavior and a working recovery procedure, and
would require inventing a replacement mechanism for a problem that already has one.

IRREVERSIBILITY: this changes a PUBLIC CONTRACT (which statuses a plan may legally move between), so
artifacts authored under it will rely on it. Reversing it later would retroactively invalidate those
histories.

## 5. Constraints the implementation MUST bind

Verified at HEAD; an implementation that ignores either will break a shipped gate.

- IPD-S405 (`ipd_lint.py:66`, emitted `:793-801`) REQUIRES a plan with `Status: executed` to carry an
  `executed` `## Workflow history` entry at post-transition. Rewrite it to query the history API
  rather than to scan Markdown. Per `takpys` this makes it STRONGER, not weaker: it can then validate
  event identity, parentage, actor, and a typed transition instead of finding a plausible prose line
  anywhere in the file.
- `aw attention`'s `last_history_at` (`attention_contract.py:32-33`) must derive from the journal head,
  and per E3 its CURRENT rule is already wrong for prepending writers, so this is a bug fix and not
  merely a port.
- 18 modules reference the heading and are the refactor surface: `ipd_lifecycle`, `plan_readiness`,
  `attention`, `doctor`, `releases`, `backlog`, `hooks/status_untooled_gate`, `ipd_lint`, `status_set`,
  `set_records`, `cli`, `engine`, `check_engine`, `selectors`, `review_findings`, `attention_contract`,
  `specs`, `record_history`. No caller may parse the Markdown block directly once the API exists.

## 6. Migration

The four reports' plans are COMPLEMENTARY, not competing, and combine as:

1. LINT GATE FIRST, ZERO DATA MIGRATION (`2o895n`). Make IPD-S405 accept a byte-reproducible
   generated line, and stop the fixed-direction interpretation of unsequenced legacy history. Pure
   tooling, reversible, testable against the existing corpus without touching one artifact. This is
   the step that makes everything after it incremental, satisfying C8.
2. EXPORT THE LOCAL SIDECAR BEFORE ANYTHING ELSE. Per E4, 176 of 177 records are unrecoverable local
   state. Never discard it silently.
3. ONE STRICT HISTORY API with per-artifact locking (`filelock`, C7), atomic write plus `fsync`, and
   a two-file transaction. Fail closed on missing, malformed, duplicate, gapped, or forked history.
4. ROUTE EVERY WRITER, and fix the write-order bugs in Section 7 while there.
5. GRANDFATHER THE TERMINAL DIRECTORIES (`pavnai`): `executed/`, `superseded/`, `not-executed/` are
   frozen audit archives; sequence lint applies to `pending/`.
6. NEW ARTIFACTS BORN v2 BEHIND A CI RATCHET (`takpys`), then LAZY MIGRATE-ON-WRITE for the rest. The
   ratchet is the ANTI-STALL mechanism, and it is required because this same migration already
   stalled once at this exact tree.

Do NOT normalize the corpus to one prepend/append convention as the primary fix. It satisfies a
parser while contradicting the convention the executed corpus follows, and `tk1gqo` already
considered and rejected it.

## 7. Out of scope, and filed separately

Both are real and neither is a storage decision. They must NOT be absorbed silently into this work.

- A LIFECYCLE POLICY GAP. `validate_transition` rejects every backward rank movement, but the plan
  status write path applies no transition table before writing a nonterminal status, and the corpus
  contains an INTENTIONAL `approved -> reviewed -> approved` reversal. Per `takpys`: "A sequenced
  event store will expose this policy inconsistency; it will not decide whether such rollback
  transitions are legal." Someone must DECIDE whether rollback edges are legal.
- WRITE-ORDER BUGS in the existing sidecar path. Specs append the event BEFORE validating and writing
  the Markdown, and backlog appends BEFORE its close-legitimacy gate and BEFORE the dry-run/apply
  decision, so a `--dry-run` PREVIEW or a REFUSED transition can leave a phantom event. This violates
  C5 today and is worth its own item.

## 8. Open questions

- OQ-1 `[RESOLVED 2026-09-08 by the maintainer]` See decision 4.8. A backward lifecycle edge is
  LEGAL as an explicit recovery transition. The question is retained rather than deleted so the
  reasoning that produced 4.8 stays visible.
- OQ-2 `[Non-blocking]` Do backlog and specs MIGRATE to per-artifact journals too, or stay on the
  global sidecar? `2o895n` explicitly does not argue for undoing them. C2 says they cannot stay as
  they are (gitignored full log plus one inline line loses data on clone), but "track the global
  file" is a legitimate cheaper answer for those two trees.
- OQ-3 `[Non-blocking]` Journal path shape: flat `<id6>.jsonl`, type-partitioned
  `<type>/<id6>.jsonl`, or a two-char shard. Reversible; decide at implementation.


## Workflow history

- 2026-09-08 note (aw specs): /spec-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; SR-001..SR-007 all FIXED. Ready for the human approval gate; the caveat a human should weigh is that this was a SELF-REVIEW (same session as authoring), so the design is re-measured but not independently judged. Next step: aw spec set approved 2vev8j --by-human. No Readiness field was written (prohibition (a): a spec has no such field and inventing one creates a machine signal no consumer may act on).
