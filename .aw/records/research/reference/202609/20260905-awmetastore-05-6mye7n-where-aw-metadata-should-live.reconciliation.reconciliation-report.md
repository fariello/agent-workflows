---
id: 6mye7n
created: 20260908
set: awmetastore
order: 05
topic: [artifact-storage, token-cost, history, schema]
model: reconciliation
kind: reconciliation-report
status: reference
outcome: adopted
summary: Consolidated finding across GPT-5.6 Sol High, Sonnet 5 High, Gemini 3.1 Pro High and Gemini 3.8 Flash High: all four converge on inline front matter plus git-tracked per-artifact JSONL history keyed by id6, ordered by an explicit per-artifact seq rather than by date; the live-verified disagreements are the inline residue, IPD-S405, and write locking
consumed-by: [ms06pi, tk1gqo]
---

# Where `aw` artifact metadata should live: consolidated finding

Synthesis of four independent research reports answering prompt `27rjro`, written to close the gate
on backlog `ms06pi` (and its symptom `tk1gqo`). This document is the one an implementer should read;
the four sources stay in the set for provenance.

| Source | id6 | Model | Read the live code? |
|---|---|---|---|
| 01 | `takpys` | GPT-5.6 Sol High | YES, at a named commit (`4763eb8d`, `main`, 2026-09-04), with ~20 file+line citations and its own re-measurement |
| 02 | `2o895n` | Sonnet 5 High | PARTLY, and says so in a section 0: no clone, browser fetches only |
| 03 | `xn6f6u` | Gemini 3.1 Pro High | YES for code (8 file+line citations); no commit sha, no re-measurement |
| 04 | `pavnai` | Gemini 3.8 Flash High | YES, claims a live checkout, re-measured the corpus and corrected four prompt figures |

A fifth report (Gemini 3.1 Pro DeepThink) was produced and DELIBERATELY EXCLUDED on the maintainer's
instruction: it states in its own author's note that network restrictions prevented it from reading
the repository, so it reasoned from the prompt's prose alone. It is not in this set.

## 1. The answer, and it is unanimous

All four reports independently recommend THE SAME DESIGN. There is no split decision to adjudicate on
the central question:

> Keep the compact current-state front matter INLINE in the Markdown. Move the unbounded
> `## Workflow history` OUT, into GIT-TRACKED, APPEND-ONLY, PER-ARTIFACT JSONL keyed by the stable
> `<id6>`. Order it by an EXPLICIT PER-ARTIFACT `seq` integer, never by parsing dates. Allow SQLite
> only as a gitignored, disposable, rebuildable cache, never as the git-carried authority.

Four models, four different verification postures, one design. Also unanimously REJECTED:

- A SINGLE GLOBAL history file as the durable authority (which is what the repo has today).
- GIT-TRACKED SQLITE, as an unmergeable binary in a system whose durable state model is git diff.
- MOVING FRONT MATTER OUT, because the saving is roughly a fifth of history's and it costs the
  `Status: reviewed -> approved` visibility in a review diff.
- A ONE-TIME BULK REORDER of the corpus as the primary fix, since it satisfies a parser while leaving
  the writers producing the order the corpus contradicts. `tk1gqo` had already reached this
  conclusion independently; all four reports agree.

The framing worth keeping is GPT-5.6's: "The core tradeoff is not 'Markdown versus a database.' It is
bounded current state versus unbounded history." That is why the answer splits by FIELD LIFETIME
rather than by storage technology.

## 2. What I verified myself, because the reports disagree and some numbers are stale

Every claim in this section was measured in THIS repository at HEAD `57143149` on 2026-09-08, and
several results differ from all four reports. Trust these over the reports where they conflict.

### 2.1 The corpus is materially BIGGER than every report was told

| Metric | Prompt / `ms06pi` | GPT-5.6 (`4763eb8d`) | Gemini 3.8 (live) | MEASURED HERE, 2026-09-08 |
|---|---|---|---|---|
| `*.ipd.md` files | 483 | 482 | 489 | **591** |
| Total characters | 10,823,121 | 10,788,984 | 11,594,780 | **15,639,697** |

The corpus grew ~22% in characters since the newest report and ~45% since the prompt. So the
token-cost case is STRONGER than any report argues, not weaker, and the percentage splits (front
matter ~4.7 to 5.5%, history ~10.2%, tool-owned ~15 to 15.6%) should be re-derived at implementation
time rather than quoted from any of these documents.

### 2.2 The global sidecar's plan count is still 1, which is the real finding

Measured: **177 records total, 150 `backlog` / 26 `specs` / 1 `plans`.** The prompt said 128
(108/19/1) and Gemini 3.8 said 164. Every source and this measurement agree on the number that
matters: PLANS = 1. The `awhistory` migration stalled at the plans tree and has not moved since,
while backlog and specs kept accruing. Plans remain the only tree carrying full inline history, which
is exactly why the ordering ambiguity lives there and nowhere else.

### 2.3 "Append-only files rarely conflict" is FALSE, and it is a load-bearing comment in the code

`record_history.py:41-55` states in its own docstring: "Append-only, so order is irrelevant."
GPT-5.6 challenged the related no-conflict premise with a two-branch trial. I reproduced it here:
two branches each appending ONE different line to the same one-line JSONL file produce an ORDINARY
CONTENT CONFLICT on merge. This is the empirical core of the case against the global file, and it is
verified, not argued.

Consequence for THIS repo specifically, which no report could know: `aw oc run` gives each execute
item an ISOLATED WORKTREE by default (`isolate_worktree`) whose changes return through a merge gate.
A single global history file is therefore a conflict magnet on the repository's normal execution
path, not in a hypothetical.

### 2.4 `record_history.append` does NOT lock, so Gemini 3.1 Pro is wrong and Gemini 3.8 is right

The two Gemini reports directly contradict each other: 3.1 Pro asserts "JSONL appends are
atomic-safe"; 3.8 says the function "lacks file locking; concurrent multi-process writes interleave
and corrupt JSON lines." Measured: `record_history.append` (`record_history.py:41-71`) does a bare
`with open(p, "a") ... f.write(...)` with NO `filelock`, no atomic replace, and no `fsync`.
**Gemini 3.8 is correct; Gemini 3.1 Pro's claim is false and must not be relied on.** `filelock` is
already the sole runtime dependency, so the fix needs no new one.

### 2.5 `aw attention`'s `last_history_at` is ALREADY inconsistent with the plan writers

`attention_contract.py:32-33` specifies `last_history_at` as "the date of the LAST record in file
order". Plan writers PREPEND (`status_set.py`). So for any plan touched by a tool, the contract reads
the OLDEST record and calls it the latest. GPT-5.6 alone caught this ("even though plan writers now
prepend. That rule is already inconsistent across artifact types"); I confirmed it in the contract
text. This is a live second defect, independent of the reader bug `tk1gqo` reports, and it must be
fixed as part of the same change rather than discovered afterward.

### 2.6 The reader bug is still present and has WORSENED

`events.reverse()` is still at `ipd_lifecycle.py:773` (reports cite `:771` and `:770-771`; the line
moved). `aw check plans` now reports **15** `check.lifecycle-transition-invalid` diagnostics, against
the 9 `tk1gqo` recorded when filed. All four reports use the 15 figure, which happens to be current.

## 3. The three real disagreements, and how to settle each

Everything above is settled. These are not.

### 3.1 Does ONE inline history line remain? (the sharpest conflict)

- **Gemini 3.1 Pro: NO.** Strip the block entirely. Its argument is concrete: if you keep only the
  latest line, a later `superseded` event EVICTS the `executed` line, "permanently breaking
  IPD-S405".
- **Gemini 3.8 and Sonnet 5: YES, keep exactly one line** (~25 tokens) for `git diff` legibility.
  Gemini 3.8's counter-argument: "the latest entry of an executed plan is always `executed`".
- **GPT-5.6: NO** ("I do not recommend retaining it"), but concedes that if kept it must be a
  byte-reproducible projection of the journal head.

Gemini 3.8's counter-argument is WRONG ON ITS OWN TERMS, and the repo proves it: a plan can move
`executed -> superseded`, at which point the latest entry is no longer `executed`. That is precisely
3.1 Pro's eviction case. But 3.1 Pro's CONCLUSION does not follow either, because it treats
IPD-S405's current shape as immovable when every report agrees the rule must be rewritten anyway.

RECOMMENDED RESOLUTION: keep ONE inline line, but make IPD-S405 query the history API rather than the
Markdown block, so the inline line is a pure CACHE with no gate depending on its content. Then
eviction is harmless by construction, and the `git diff` legibility that Sonnet 5 and Gemini 3.8
value is preserved. Sonnet 5's added condition is the one that makes this safe: the inline line must
be BYTE-REPRODUCIBLE from the journal head, with a drift check and an `--apply` repair, matching this
repo's existing "generated views must be byte-reproducible from their source" convention.

### 3.2 Is the migration LAZY or BATCHED?

- **Sonnet 5: lazy only.** Migrate an artifact when something next writes to it. "Never schedule a
  single ~500-file rewrite commit." Its strongest point, and the one I would not compromise: relax
  the lint gate FIRST, with ZERO data migration, because that step is reversible and needs no
  corpus rewrite. It also diagnoses WHY the prior attempt stalled: a central-file design "implicitly
  forced an all-or-nothing migration for any tree it touched."
- **Gemini 3.8: grandfather the terminal dirs** (`executed/`, `superseded/`, `not-executed/`) as
  frozen audit archives, applying the sequence lint only to `pending/`.
- **GPT-5.6: bounded batches** with a dry-run report, terminal plans first, then active sets one at a
  time under locks, plus a CI RATCHET forbidding new v1 artifacts.

These are complementary, not exclusive, and the synthesis is: lint-gate change first (Sonnet 5),
grandfather the terminal dirs (Gemini 3.8), new artifacts born v2 behind a CI ratchet (GPT-5.6), then
lazy migrate-on-write for whatever remains. The ratchet is the anti-stall mechanism, and this matters
because the SAME migration already stalled once at exactly this tree.

### 3.3 Sidecar path layout

`.aw/records/history/<id6>.jsonl` (Gemini 3.1 Pro) vs `<type>/<id6>.jsonl` (Gemini 3.8) vs a
two-char shard `<xx>/<id6>.jsonl` (GPT-5.6) vs alongside the artifact as
`<basename>.history.jsonl` (Sonnet 5). Low-stakes and reversible, but note ONE asymmetry that decides
it: Sonnet 5's alongside-the-artifact layout ties the history path to the artifact's NAME and
DIRECTORY, so a `git mv` through the lifecycle (`pending/` to `executed/`) must move the sidecar too,
and a re-slug renames it. Every other layout keys on the IMMUTABLE `<id6>`, which GPT-5.6 states
explicitly: keyed on `Id` "not the artifact name, so artifact renames do not move the journal." Since
this repo renames and moves artifacts CONSTANTLY, key the path on `<id6>`, not the basename.

## 4. What the reports agree on that is easy to under-weight

- **ORDERING COMES FROM `seq`, NOT FROM TIME.** All four converge here, and GPT-5.6 puts it most
  sharply: "Timestamps are never the sequencing authority. That eliminates both the day-granularity
  defect and the UTC-versus-local-date inversion." Sonnet 5 calls `seq` "the one piece of this
  recommendation I'd call non-negotiable." Keep a full UTC timestamp for display and correlation
  ONLY.
- **THE TIMEZONE DEFECT IS SEPARATE AND NEEDS ITS OWN FIX.** `tk1gqo` recorded it as a second defect;
  Sonnet 5 insists neither fix alone suffices: "`seq` alone leaves timestamps still lying about
  'future' entries; UTC-only timestamps alone still can't order a same-day round-trip losslessly."
- **DO NOT INVENT PRECISION FOR LEGACY LINES.** GPT-5.6 is the most careful: import them verbatim as
  `legacy` events carrying the observed day, their original file ordinal, and an
  `ordering_confidence` marker (`known` / `inferred-from-git` / `unknown`), then start the real chain
  from a `seq` 0 checkpoint and do NOT run forward-transition validation across unordered legacy
  records. This is what lets the 3 irreducible cross-day `approved -> reviewed` cases stop being
  false failures without fabricating an order.
- **THE MOST DAMAGING CURRENT DEFECT IS SILENT DATA LOSS, NOT TOKEN COST.** GPT-5.6 alone spotted it:
  specs and backlog have ALREADY had their inline history slimmed to one line, while the only full
  log is GITIGNORED (`.aw/.gitignore:11`, confirmed). So a fresh clone gets NEITHER copy for those
  trees. My measurement makes this concrete: 176 of the 177 sidecar records are specs/backlog
  history that exists ONLY on this machine. FIRST ACTION IN ANY IMPLEMENTATION: export and preserve
  that file before touching anything, because it is unrecoverable local state.

## 5. Two defects reported here that are OUTSIDE the storage question

Both are real and neither is a storage-design decision. They deserve their own backlog items rather
than being absorbed silently into this work.

1. **A LIFECYCLE POLICY GAP (GPT-5.6).** `validate_transition` rejects every backward rank movement,
   but the plan-status write path applies no transition table before writing a nonterminal status,
   and the corpus contains an INTENTIONAL `approved -> reviewed -> approved` reversal. Its warning is
   the important part: "A sequenced event store will expose this policy inconsistency; it will not
   decide whether such rollback transitions are legal." Someone must DECIDE whether rollback edges
   are legal; the storage change only makes the question unavoidable.
2. **WRITE-ORDER BUGS IN THE EXISTING SIDECAR PATH (GPT-5.6).** Specs append the history event BEFORE
   validating and writing the Markdown, and backlog appends BEFORE its close-legitimacy gate and
   before the dry-run/apply decision, so a `--dry-run` PREVIEW or a REFUSED transition can leave a
   phantom event. Worth verifying and filing independently; it is a correctness bug in shipped code
   regardless of where history ends up living.

## 6. How to read the sources

- Want the DESIGN SPEC (schema fields, invariants, phased plan, effort estimate)? Read `takpys`
  (GPT-5.6). It is the most rigorous, the only one with a named commit, and the only one that
  re-derived the diagnostic counts and ran its own git experiment. It also correctly flags four
  prompt errors.
- Want the MIGRATION STRATEGY and the reason the last attempt stalled? Read `2o895n` (Sonnet 5). Its
  lint-gate-first sequencing is the key insight, and its section 0 is a model of honest verification
  accounting. Treat its corpus numbers as the prompt's, exactly as it instructs.
- Want the CURRENT MEASUREMENTS and a module-by-module migration table? Read `pavnai` (Gemini 3.8).
  Note its one unsupported claim: a "5,377 passing tests" baseline appears once with no runner output
  and no commit sha.
- `xn6f6u` (Gemini 3.1 Pro) is the most concise statement of the design and contributes the
  IPD-S405 eviction argument, but it re-uses the prompt's numbers without checking them and its
  "JSONL appends are atomic-safe" claim is FALSE in this codebase (2.4). Read it last.

## 7. Recommended next step

`ms06pi` can now be graduated. This finding answers its question; it does NOT author the design. The
graduating work should carry a SPEC (the storage contract, the event schema, the ordering rule, and
the authority split), because 19 modules read `## Workflow history` today and the change alters a
contract every one of them depends on. `tk1gqo` should stay gated on that spec rather than on the
research prompt, since fixing the reader alone was already ruled out and remains wrong.
