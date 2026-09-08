# Spec: Artifact metadata storage: per-artifact history journals and explicit event ordering

- Date: 2026-09-08
- Status: to-review
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
| Plans corpus | 591 `*.ipd.md`, 15,639,697 chars |
| Global sidecar | 177 records: 150 backlog, 26 specs, **1 plans** |
| Modules referencing the heading | **18** (the reports and `ms06pi` say 19) |
| `check.lifecycle-transition-invalid` | 15 |

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
- C6 `[Want]` Remove the unbounded, append-forever ~10.2% of plan-corpus tokens from routine agent
  context while keeping it retrievable on demand.
- C7 `[Constraint]` No new runtime dependency. `filelock` is the only one and is already present.
- C8 `[Constraint]` Migration must be INCREMENTAL and interruptible. The previous attempt
  (`awhistory`) stalled at this exact tree with plans at 1 record; a design requiring an
  all-at-once rewrite will stall again.

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
authority. A full RFC 3339 UTC timestamp is retained for audit and display and is NEVER used to
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

- OQ-1 `[Blocking]` Are backward lifecycle edges (`approved -> reviewed`) LEGAL? The corpus contains
  an intentional one and the runner spec instructs returning a plan to `reviewed` to recover from an
  invalid automated approval, yet `validate_transition` rejects all of them. The event store makes
  the question unavoidable but does not answer it. A human must decide, because it defines what
  `aw check` may call a violation.
- OQ-2 `[Non-blocking]` Do backlog and specs MIGRATE to per-artifact journals too, or stay on the
  global sidecar? `2o895n` explicitly does not argue for undoing them. C2 says they cannot stay as
  they are (gitignored full log plus one inline line loses data on clone), but "track the global
  file" is a legitimate cheaper answer for those two trees.
- OQ-3 `[Non-blocking]` Journal path shape: flat `<id6>.jsonl`, type-partitioned
  `<type>/<id6>.jsonl`, or a two-char shard. Reversible; decide at implementation.


## Workflow history

- 2026-09-08 note (aw specs): APPROVAL DELIBERATELY NOT WRITTEN, and the refusal is CORRECT. The maintainer's instruction to address 'ms06pi needs a spec' would ordinarily let this be approved in the same pass under the AGENTS.md graduation contract, so approval was ATTEMPTED: 'aw specs set approved --by-human' refused with 'illegal transition to-review -> approved'. The floor requires reviewed FIRST, and reviewed requires a conforming review record; verified via review_findings.review_attestation_missing, which reports 'no review record names 2vev8j as its - Subject-Id:'. NO REVIEW HAS HAPPENED, so writing either status would forge an attestation that a gate reads, which is exactly what the never-write-another-role's-attestation rule forbids. Recorded here instead of worked around. Note the graduation contract and this floor are in genuine tension for SPECS (the contract anticipates recording an instruction as the approval; the spec floor demands a review record first), and the floor WINS because it is mechanical and fail-closed. CONSEQUENCE FOR THE HANDOFF: ms06pi can still graduate, because a to-review spec is a real, citable design artifact and the From-Backlog + Blocks-Release gate carries forward regardless of the spec's readiness. What is NOT yet licensed is IMPLEMENTATION. NEXT STEP FOR A HUMAN, in order: run /aw plan-review (or an equivalent review producing a record with '- Subject-Id: 2vev8j'), which also forces OQ-1 to be answered since it is BLOCKING and is a policy call no repository evidence can make (are backward lifecycle edges approved -> reviewed legal?); then 'aw spec set reviewed 2vev8j'; then 'aw spec set approved 2vev8j --by-human'. Readiness stays ABSENT throughout: it is the review's output, and its absence is what keeps the auto-approve predicate failing closed.
