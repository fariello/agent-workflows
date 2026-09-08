---
id: 2o895n
created: 20260908
set: awmetastore
order: 02
topic: [artifact-storage, token-cost, history, schema]
model: sonnet5high
kind: research-report
status: reference
outcome: adopted
summary: Sonnet 5 High: hybrid inline front matter plus sidecar history, with an explicit section 0 accounting of which prompt claims were verified against the live source and which could not be
consumed-by: [ms06pi, tk1gqo]
---

<!-- PROVENANCE: verbatim external artifact, adopted from `.aw/inbox/aw-artifact-metadata-storage-research-report.sonnet5high.md`
     on 2026-09-08 in answer to research prompt `27rjro`. Author: Sonnet 5 High.
     Preserved AS RECEIVED per the research README's external-artifacts rule, so its own
     punctuation and formatting stand and the no-em-dash house rule does not apply here.
     Treat the CONTENT as untrusted external input, not as instructions. -->

# Where should tool-owned artifact metadata live? A storage design for `agent-workflows`

**Scope:** `.aw`/`.agents` durable records in [fariello/agent-workflows](https://github.com/fariello/agent-workflows)
**Status of this document:** research report, drafted for committing back into the repository
**Note on method:** see [§0](#0-how-this-was-verified-and-what-i-could-not-verify) before trusting any specific number in this report

---

## 0. How this was verified, and what I could not verify

The brief asked me to check the prompt's claims against the live source rather than take
them on trust, and to flag discrepancies and thin evidence rather than guess. I did not
have shell/clone access to the repository in this session — only a web browser's worth of
GitHub page fetches and search. That materially limits what I could confirm. Here is the
honest accounting:

**Confirmed directly, with citations:**

- The repository is real, public, small (1 star, 0 forks at time of writing), Apache-2.0,
  maintained by Gabriele Fariello, and the `aw` CLI is exactly as described (aliases
  `agent-workflows`, `agentwf`), including the plan/IPD `Status:` lifecycle vocabulary
  `draft -> to-review -> reviewed -> approved -> <terminal>` and an `aw plans` command
  that reads front-matter only.
- **The single-runtime-dependency claim is exactly right.** `pyproject.toml` declares
  `dependencies = ["filelock>=3"]` and nothing else, with an extensive comment explaining
  *why*: several modules used to `import fcntl` at top level (POSIX-only, so the package
  failed to even import on Windows), and hand-rolling a cross-platform lock is a known trap
  because Windows' `msvcrt.locking` locks a byte range rather than the whole file, so two
  processes can each believe they hold an exclusive lock on disjoint ranges of the same
  file — a silent mutual-exclusion failure in exactly the code that serializes registry
  writes. That reasoning is load-bearing for this report's own recommendation (§7).
- **A `.aw/` four-root physical layout genuinely exists in the project's own architecture
  documentation** (`ARCHITECTURE.md`): `system/`, `records/`, `config/`, `state/`, with
  `records/plans/{pending,executed,reusable,superseded,not-executed}` as a stated
  subdirectory layout — this matches the prompt's `.aw/records/plans/executed/` framing.
  `ARCHITECTURE.md` also documents a **`layout_migration`** module for migrating off a
  "legacy `.agents/` layout," and four storage *presets*, including one
  (`public-target-private-companion`) that explicitly routes `.aw/records/` to a **separate
  private companion repository for public open-source projects**, and another
  (`local-only`) that gitignores the entire `.aw/` hierarchy.
- **`pyproject.toml`'s packaging config independently corroborates the `.aw/system/`
  rename** (a comment references "the Order-11 self-migration" that moved the shipped
  workflow bundle to `.aw/system/`, and the wheel force-includes the repo-root `.aw/system/`
  tree), so the `.aw/` layout is not merely aspirational documentation — the build system
  depends on it existing.
- A concern named `ipd-lifecycle` and a gate described as `aw ipd lint` are named in
  `ARCHITECTURE.md`, consistent in spirit with the prompt's `ipd_lint` / `IPD-S405` claim,
  though I could not confirm the specific rule ID.

**Could not confirm, and why — this is where the prompt's specific evidence is thin:**

- **I could not verify the corpus statistics** (483 `*.ipd.md` files, 10,823,121 characters,
  the 4.7%/10.2%/14.9% split, the median/largest history-block sizes, the "15 diagnostics"
  CI-failure count, the `128/108/19/1` `history.jsonl` record counts, or the specific plan
  IDs `uyeko5`, `x97z83`, `im90a5`, `b0behn`, `cizkf4`). None of my available tools can clone
  the repo, run `wc`/`grep` over it, or browse an arbitrary directory path on GitHub that
  hasn't already surfaced in a search result — and `.aw/records/` specifically is the one
  part of this project's own documented architecture that is designed to be **routable
  outside the public repository** (see the `public-target-private-companion` and
  `local-only` presets above). That is the single most plausible explanation for why a
  483-file, 10.8M-character corpus can be real and precisely measured by whoever is running
  `aw` locally, while being structurally invisible to a web-only check of the public tree:
  it may simply live in a private companion repo or on the maintainer's machine, by design,
  not by omission.
- **I could not confirm the specific Python module list** (`ipd_lifecycle.py`,
  `record_history.py`, `ipd_lint.py`, `ipd_schema.py`, `plan_readiness.py`, `backlog.py`,
  `specs.py`, `releases.py`, `review_findings.py`, `selectors.py`, `set_records.py`,
  `status_set.py`, `status_untooled_gate.py`, `attention.py`, `attention_contract.py`,
  `check_engine.py`, `doctor.py`, `engine.py`). `ARCHITECTURE.md`'s own "Router APIs"
  section names a *different* set of dotted paths (`agent_workflows.project_context`,
  `agent_workflows.engine`, `agent_workflows.storage`, `agent_workflows.layout_migration`),
  and `pyproject.toml` additionally confirms `agent_workflows.cli` and
  `agent_workflows/platform_lock.py` by name. These are not necessarily contradictory —
  a package can have both sets of modules — but I have no positive confirmation of the
  19-module list as given, and I was blocked from browsing the `agent_workflows/` directory
  listing directly (`ROBOTS_DISALLOWED` on the tree URL) or reading `DECISIONS.md` in full
  (2,544 lines / 337 KB — too large for this session's page-render path, and the raw file
  URL is robots-blocked). Treat every specific filename in the rest of this report as
  **the prompt's assertion, not my independent confirmation**, except `cli.py`,
  `platform_lock.py`, `project_context.py`/module, `engine.py`/module, `storage.py`/module,
  and `layout_migration.py`/module, which I trust as-cited above.
- **I could not reproduce the `README.md`-vs-`ARCHITECTURE.md` layout claim as a clean
  read** either: two separate fetches of what should be the same `main` branch returned
  visibly different snapshots (differing commit counts on the repo-root page across
  fetches; a top-level file listing that showed `.agents/` and no `.aw/`, alongside other
  evidence from the same session that `.aw/` is real and load-bearing). GitHub's CDN
  appears to have served me inconsistent cache states across requests in this session. I am
  confident the **inconsistency itself** between `README.md` (still describes
  `.agents/workflows/`, `.agents/plans/pending/`, and `workflow-artifacts/<run-id>/`) and
  `ARCHITECTURE.md` (describes `.aw/system/`, `.aw/records/plans/…`, and a migration *from*
  `.agents/`) is real and citable — README.md reads as not-yet-updated after the `.aw/`
  rename — but I cannot tell you with confidence exactly what today's top-level tree looks
  like, and you should treat that specific claim as flagged, not settled.

**What this means for the rest of the report:** the *design question* — inline vs. sidecar
vs. central log vs. database for tool-owned metadata, and the specific ordering/timezone
bug described — is a coherent, well-specified problem regardless of whether the corpus is
exactly 483 files or some other number, and regardless of which of the two documented
directory layouts is current. I answer it on those terms below, treating the measured
figures in the prompt as **the requester's own reported measurements**, not as numbers I
re-derived. Where a recommendation's *strength* would change materially if a number were
off by 10x, I say so explicitly.

---

## 1. Recommendation, stated plainly

**Keep front-matter inline. Move the append-only `## Workflow history` block out of the
Markdown and into a per-artifact sidecar file — never a central one — and fix the ordering
bug by adding an explicit per-artifact monotonic sequence number, not by inferring order
from dates.**

Concretely: option **(b)** from the comparison in §2, with three refinements that address
the ordering bug, the single-source-of-truth question, and the stalled-migration failure
mode specifically:

1. **Front-matter stays inline**, unchanged in format. It is small (reported ~4.7% of
   corpus tokens), and it is exactly the state a human reviewing a diff wants to see without
   opening a second file — `Status: reviewed -> approved` in a `git diff` is valuable;
   losing it to a sidecar would cost more than it saves.
2. **The full prose `## Workflow history` block moves to a per-artifact sidecar**
   (`<plan-basename>.history.jsonl`, sitting next to the `.ipd.md` file), not to one shared
   file. A single central log is a merge-conflict magnet under concurrent agents by
   construction — the project already learned this the hard way (§3) — and per-artifact
   files eliminate that failure mode structurally: two agents touching two different plans
   never contend for the same file, and two agents touching the *same* plan contend no more
   than they already do today on the `.md` file.
3. **The most recent transition is still mirrored inline as one line**, exactly matching
   what the already-completed specs/backlog migration does ("their inline history slimmed
   to the latest single line"). This satisfies the two hard tooling requirements the
   prompt names — an inline `executed` entry for the lint gate, and a `last_history_at`
   timestamp for the attention command — without keeping the *unbounded* part inline.
4. **Ordering is made unambiguous by construction, not by convention or inference**: every
   history entry, inline mirror included, carries a per-artifact monotonic integer `seq`
   in addition to a timestamp. The parser stops reversing, sorting by date, or breaking
   ties by lifecycle rank — it just reads `seq` ascending. This is the one piece of this
   recommendation I'd call non-negotiable; every "obvious fix" the prompt tried (date sort,
   date+rank sort, corpus normalization) is a workaround for the fact that the *format*
   doesn't carry sequence information, and workarounds for a missing field are strictly
   worse than adding the field.

If the corpus turns out to be far smaller than reported (say, tens of files, not hundreds),
this recommendation doesn't change — the ordering bug and the merge-conflict risk are both
independent of corpus size; they're properties of the format and of having multiple
concurrent writers. If it turns out `.aw/records/` is genuinely routed to a private
companion repo (§0), the recommendation *also* doesn't change, because the companion repo
faces the identical concurrent-agent, git-diff-legibility, and ordering problems — routing
records to a second repository doesn't remove git as the transport.

---

## 2. Comparison of the realistic options

| Option | Token/context effect | Parse robustness | Merge-conflict behavior | Human diff legibility | Crash/partial-write safety | Migration cost |
|---|---|---|---|---|---|---|
| **(a) Status quo, fully inline** | Worst: ~14.9% of every plan's tokens is tool-owned, on every read, forever, and the history share grows without bound (reported worst case 20% for one file) | Poor — the exact bug in §4 is a direct consequence of no ordering guarantee | Two agents finishing work on the same plan same day both append/prepend to the same block in the same file → ordinary text conflict, resolvable but frequent | Best — everything visible in one diff | No worse than any Markdown file (whole-file rewrite risk on crash) | Zero |
| **(b) Front-matter inline, history to per-artifact sidecar** *(recommended)* | Front-matter's ~4.7% stays on every read; the growing ~10.2% is loaded only when history is actually needed (audits, `/incident`, dispute resolution) | Good, if paired with the `seq` fix in §4 — otherwise inherits the same ordering bug in a new location | Low — one file per artifact; no cross-artifact contention; same-artifact contention unchanged from today | Very good for the state a reviewer cares about (Status/Readiness/etc. in the same diff); history changes show as a new file or an appended JSONL line, which is *still* diffable, just in a second file | Sidecar is append-only JSONL: a torn write is a detectable, truncatable partial last line, and it never risks corrupting the prose file | Moderate, but incremental and reversible (§6) — this is what already shipped for specs/backlog |
| **(c) All tool-owned metadata (front-matter + history) to per-artifact sidecars** | Best per-file token savings, but front-matter is small, so the *marginal* saving over (b) is modest | Same as (b) once `seq` is added | Same as (b) | Worse than (b) — a status change becomes invisible in the `.md` diff entirely, which the prompt's own constraint #2 flags as a real cost | Same as (b) | Higher than (b) for little extra benefit — every one of the 19 dependent modules that reads front-matter must also change, not just the ones that read history |
| **(d) One central append-only JSONL for everything** | Good for tokens (nothing tool-owned stays inline at all) | Fixes nothing about ordering by itself — a shared file with `seq` still needs the same per-artifact-scoped sequence, and a shared file makes "per-artifact" sequencing awkward (do you sequence globally or per-artifact-within-the-shared-file?) | **Worst** — this is the exact design already tried and explicitly excluded for plans (§3); every concurrent agent across the whole repo contends for one file | Poor — an artifact's own history is no longer visible anywhere near the artifact; you must know to go look in a separate, unrelated file | A single shared file is a single point of corruption for the *entire project's* history, not just one artifact's, if a write is torn | Reportedly already attempted and stalled specifically because of this design's fit to the busiest tree |
| **(e) SQLite as source of truth, generated Markdown views** | Best possible token/context efficiency (agents never touch it) | Excellent — real ACID transactions and a real ordering column solve §4 completely and for free | Worst of all — a binary file edited concurrently by agents in separate worktrees does not text-merge; a git merge of two SQLite files does not produce a valid database, it produces corruption | Worst — nothing is human-readable without running a tool, which the prompt's constraint #2 explicitly asks to weigh rather than dismiss | Good in isolation (SQLite's own WAL/journal is robust) but that robustness doesn't survive being merged as a git blob by two branches | High — a real new dependency-adjacent subsystem (stdlib, yes, but a genuinely different mental model), and every consumer needs a data-access layer instead of a text parser |
| **(f) Hybrid variants considered and folded into (b)** | — | — | — | — | — | — |

**Why not (e), despite SQLite being "free" (stdlib) and solving the ordering bug outright:**
the constraint that decides this is not the dependency policy, it's git. SQLite's file
format is not designed to be three-way-merged, and this project's entire durable-state
model is "git is the transport and the audit log" (prompt constraint #3). A design that
requires every concurrent agent to serialize through a single binary file defeats the
purpose of using git for coordination in the first place — you'd need to reintroduce a real
lock server or a rebase-and-retry protocol just to get back to where per-artifact text
files already leave you. SQLite is, however, an excellent choice for something this project
doesn't currently have and might want: a **local, gitignored, disposable, rebuildable
index** — e.g., to make `aw plans`/`aw attention` fast without re-parsing 500 files on every
invocation — generated *from* the sidecars, never committed, and rebuilt on demand. That is
consistent with the repository's own stated convention (per the prompt) that "generated
views must be byte-reproducible from their source and drift must be a detectable finding" —
an SQLite cache is exactly a generated view, and it is disposable precisely because it is
generated.

---

## 3. What the stalled migration already tells us

The prompt reports that a prior `awhistory` effort built the sidecar this question is
asking about — a single global `.aw/records/history.jsonl` plus a writer module and a read
verb — routed specs and backlog to it, and **explicitly, deliberately excluded plans**, with
the scope note quoted verbatim in the prompt citing the `ipd_lint` `IPD-S405` inline-entry
requirement as the reason, and treating the plan-side migration as "a separate follow-up."
The reported current state — 108 backlog, 19 specs, and exactly 1 plan record in that
file — is itself the evidence for why: a single shared file is a fine fit for backlog and
specs, which the report characterizes as much lower volume, and a poor fit for plans, which
are "the largest and most numerous type" and under the heaviest concurrent multi-agent
load. This is not a story about a follow-up nobody got to; it's a story about a design that
correctly wasn't extended to the one tree where its own weakness (shared-file contention)
would matter most. **Any recommendation that re-proposes a single central file for plans is
repeating the part of the design that was already tried and correctly not adopted there.**
That's why this report's recommendation in §1 is explicitly per-artifact, not central, and
explicitly says option (d) should not be revisited for plans.

---

## 4. The ordering bug: does this design fix it structurally?

**Yes — by removing the need to infer order at all, not by inferring it better.**

The root cause, as diagnosed in the prompt, is exactly right: *the durable record does not
carry enough information to reconstruct the sequence*, and prepend vs. append are both
"valid" only because nothing in the format says which one is correct. Every fix the prompt
tried and rejected — reversing on a hardcoded assumption, sorting by date, sorting by
date-then-lifecycle-rank — is an attempt to *reconstruct* an ordering that was never
recorded, using progressively cleverer heuristics, and each one still fails on a case the
format can't express (same-day round-trips, in particular, are explicitly permitted by the
project's own lifecycle spec per the prompt, and no timestamp-only heuristic can represent
"approved, then re-reviewed, then re-approved, all on 2026-09-04" without more than a date).

**Recommended fields, and why:**

- **A per-artifact, strictly monotonic integer `seq`** (0, 1, 2, …), assigned by whichever
  writer creates the entry, is the primary ordering key. This is the one field that makes
  order unambiguous *by construction*: it doesn't matter whether two entries share a
  timestamp, whether a clock is wrong, or whether one writer's local clock disagrees with
  another's UTC clock — `seq` says who came first because *nothing else could have written
  `seq=N` before something else wrote `seq=N-1`* (enforced by the same `filelock`-guarded
  append path already used for the existing `record_history` writer, per the confirmed
  single-dependency rationale in §0). This directly answers the "identity/sequence field"
  half of the prompt's question.
- **A full RFC 3339 timestamp at second resolution, always in UTC**, is kept as a secondary,
  display/correlation field — useful for a human asking "what else happened around 14:30
  that day," and useful for cross-artifact correlation — but is **never used to determine
  order** within an artifact. This directly answers the "timestamp granularity" half: the
  prompt's own experiment shows day-granularity is not sufficient (same-day bursts are
  normal), and finer granularity alone still wouldn't fix the second defect the prompt
  flags — tool writers stamping UTC while humans write local dates, producing an
  apparently-future-dated entry. Mandating **one timezone for every writer, human included**
  (the sidecar format requires UTC; a human-facing helper converts local input to UTC before
  writing, the same way `aw plan-names` already normalizes filenames rather than trusting
  free-form input) removes that defect independently of the `seq` fix. Both defects named in
  the prompt are fixed by these two changes together, and neither field alone would have
  been enough — `seq` alone leaves timestamps still lying about "future" entries; UTC-only
  timestamps alone still can't order a same-day round-trip losslessly.
- **No new artifact-identity field is needed.** The existing per-artifact `Id` (e.g.
  `uyeko5`) is already a stable key; `seq` is scoped to that `Id`, so the sidecar filename
  itself (named from the artifact's own basename) provides the join key for free.
- **The reader (`_plan_status_events` or equivalent) is simplified, not made cleverer**: it
  reads the sidecar's lines in file order (which is now guaranteed to equal `seq` order,
  since the writer only appends), and does not need `events.reverse()`, a date sort, or a
  lifecycle-rank tiebreak. Simpler code is itself a correctness win here — the bug report's
  root cause was a hardcoded assumption about a convention nobody enforced; removing the
  assumption's *reason to exist* is more robust than replacing it with a better assumption.

---

## 5. Single-source-of-truth position

**The sidecar is authoritative for full history. The inline mirrored line is a generated
view of the sidecar's last entry, and must be byte-reproducible from it.**

This is a direct application of the convention the prompt says the repository already
holds itself to: generated views must be byte-reproducible from their source, and drift
must be a detectable finding, not a silent divergence. Concretely:

- **Detection:** a lint check (a natural extension of the existing `ipd_lint`/`aw doctor`
  family) recomputes the expected inline line from the sidecar's tail entry and compares it
  byte-for-byte against what's actually inline. Mismatch is a finding, exactly like any
  other `ipd_lint` diagnostic — not a silent inconsistency someone discovers later.
- **Repair:** the same command gets a `--apply` mode that rewrites the inline line from the
  sidecar, mirroring the precedent already set by `aw plan-names --apply` performing staged
  `git mv` renames rather than requiring hand-editing. A human or agent that edits the
  inline line directly (instead of going through the writer) produces a detectable-and-
  fixable drift, not a corrupted or ambiguous state.
- **Front-matter fields** (`Status`, `Readiness`, `Set`, `Order`, etc.) remain the sole
  source of truth for themselves — nothing about this recommendation duplicates them
  anywhere, so there's no drift question for that half of the metadata at all.

---

## 6. Migration path

The core lesson from §3 is: **the previous attempt stalled because its central-file design
implicitly forced an all-or-nothing migration for any tree it touched** (you can't have half
of a shared file in the old format and half in the new format in any coherent way once
multiple artifacts are interleaved in the same file). A per-artifact sidecar design does not
have that property, which is what makes the path below different in kind, not just in
degree, from re-attempting the same plan.

1. **Unblock the lint gate first, with no data migration at all.** Change (or add an
   equivalent to) the `IPD-S405`-style rule so that a byte-reproducible generated inline
   line mirrored from a sidecar satisfies "an inline `executed` entry at post-transition"
   just as well as a hand-written one does. This is a pure tooling change, fully testable
   against the existing corpus without touching a single plan file, and fully reversible if
   something's wrong with it.
2. **Migrate lazily, per artifact, on next touch — not in one commit.** A plan keeps its
   current fully-inline history until the next time something writes a new history entry to
   it. At that point, the writer creates the sidecar (seeded with a best-effort backfill of
   the existing inline entries, explicitly flagged as backfilled/approximate since their
   true `seq` was never recorded and can only be reconstructed heuristically — this is the
   one place where the date+lifecycle-rank heuristic from the prompt's own experiments is
   the *right* tool, used once, for historical data, not as a permanent ordering strategy),
   slims the inline block to the new latest-line mirror, and moves on. Untouched plans are
   unaffected and keep working exactly as they do today; there is never a moment where the
   corpus is "half migrated" in a way that breaks a reader, because a reader can always tell
   which format a given plan is in (sidecar file present, or not).
3. **Update the 19 dependent modules in two tiers, matched to the two-tier design:**
   - *Tier 1 — modules that only need the latest status/timestamp* (the prompt names
     `attention.py`'s `last_history_at` derivation and similar `plan_readiness.py`/
     `status_set.py`-style consumers as examples): these can read the mirrored inline line
     completely unchanged, since its format doesn't change, only its provenance does.
   - *Tier 2 — modules that reconstruct a sequence* (`ipd_lifecycle.py`'s
     `_plan_status_events`, `check_engine.py`'s `check.lifecycle-transition-invalid`,
     `review_findings.py`): these need real code changes, but the change is a
     simplification (§4) — read the sidecar, trust `seq`, stop reversing/sorting.
   - Ship both tiers together, Set by Set (reusing the existing `Set` grouping the prompt
     describes, e.g. the `runflags` example), verifying against the specific regression the
     prompt names: the previously-reported 15 false `check.lifecycle-transition-invalid`
     diagnostics should go to 0 for every migrated plan, and stay at whatever the true
     baseline is (ideally 0) for genuinely malformed ones.
4. **Never schedule a single ~500-file rewrite commit.** This is the direct, structural fix
   for why the previous effort's "separate follow-up" for plans never happened: there is no
   longer a follow-up that has to happen all at once. If the true corpus size differs
   substantially from the reported 483 (§0), this property is exactly why it doesn't
   matter — lazy per-artifact migration costs the same regardless of corpus size; only a
   big-bang rewrite's cost scales with it.

---

## 7. What I would not do, and why

- **I would not put tool-owned metadata in SQLite (or any binary format) as the committed
  source of truth**, despite it being stdlib and despite it solving the ordering bug for
  free. The reason isn't the dependency policy — it's that this project's durable-state
  model is built on git being able to merge and diff its records, and a binary database
  file breaks both of those in a way no amount of careful schema design fixes. Use SQLite
  only as a disposable, gitignored, regenerable index built from the sidecars.
- **I would not move front-matter out of the Markdown**, even though doing so would save a
  little more context than leaving it. It's small, it's exactly the state a reviewer wants
  in the same diff as the prose change, and 19 modules already have working parsers for it
  in place; moving it multiplies migration surface for a token saving the prompt's own
  numbers show is roughly a fifth of what the history block accounts for.
- **I would not adopt one central JSONL for plans**, whether by finally "finishing" the
  stalled `awhistory` migration as originally scoped or by designing a new central store.
  Section 3 is the argument: this was tried, and the fact that it was never extended to
  plans is itself the evidence that a shared file doesn't fit the tree with the most
  concurrent writers. It may still be perfectly fine to leave backlog/specs on the existing
  central file — nothing here argues for undoing that — but plans specifically should not
  follow them there.
- **I would not treat date-sort or date+lifecycle-rank inference as a permanent fix**, only
  as a one-time, clearly-flagged backfill heuristic for pre-existing entries during
  migration (§6, step 2). The prompt's own experiments already show both heuristics have a
  real, non-hypothetical failure mode (same-day round-trips); using either as the long-term
  ordering mechanism means shipping a design with a known, previously-observed defect when
  a strictly better and cheaper fix (an integer field) is available.
- **I would not normalize the existing ~500-file corpus to one prepend/append convention as
  the primary fix**, on its own. The prompt's own note is correct that this doesn't help
  unless every writer is also changed, and rewriting ~500 files in place while agents are
  actively working in the tree is exactly the kind of big-bang change §6 is designed to
  avoid. It's fine as a side effect of the lazy, per-artifact migration in §6 (each migrated
  file naturally ends up in the new, unambiguous format), but it should never be scheduled
  as a standalone bulk operation.
- **I would not present the corpus statistics or the specific bug counts in this report as
  independently verified.** Per §0, I could not reproduce them, and the honest thing to do
  with a number I couldn't check is say so, not restate it with borrowed confidence.

---

## 8. Decision rule, if you generalize this beyond plans

The rule this report applies, stated once so it can be reused for `specs`, `backlog`,
`releases`, or any future artifact type: **co-locate structured, tool-owned data with the
prose only while it stays small relative to the prose and a human benefits from seeing it
in the same diff. The moment a section is append-only and unbounded, or a human no longer
needs the *whole* section in the same diff (only its latest value), externalize it — to a
per-artifact sidecar, never a shared one, because a shared sidecar's contention scales with
the number of concurrent writers across the whole repository, not with the size of any one
artifact.** Front-matter currently satisfies the "stays small, humans want it in-diff" test
for every artifact type named in the prompt; `## Workflow history` currently fails it for
plans specifically because plans are both the largest tree and the one under the heaviest
concurrent load — which is exactly why the two kinds of tool-owned data in this system
warrant two different answers, not one uniform answer for all of them.
