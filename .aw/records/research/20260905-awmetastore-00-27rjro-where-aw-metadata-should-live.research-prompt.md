---
id: 27rjro
created: 20260905
set: awmetastore
order: 00
topic: [artifact-storage, token-cost, history, schema]
model:
kind: research-prompt
status: todo
outcome: none-yet
summary: Where aw-only artifact metadata (front matter, workflow history, readiness, disposition) should be stored: inline markdown, sidecar JSON/JSONL, or a database, optimizing agent token cost against tooling correctness
consumed-by: []
priority: high
---

# Research request: where should tool-owned artifact metadata live?

You are being asked to research and recommend a storage design for a real, working open-source
toolkit. Please read the codebase before answering; it is public:

    https://github.com/fariello/agent-workflows

That repository IS the system under discussion. Everything below describes its current behavior, and
you should verify the claims against the source rather than taking them on trust. Where this prompt
and the code disagree, the code is right and I want to know about the discrepancy.

Return your answer as a DOWNLOADABLE MARKDOWN (`.md`) FILE, so it can be committed back into the
repository as a research report.

## 1. What the system is

`agent-workflows` (CLI name `aw`) coordinates AI coding agents through a documented workflow. Its
durable state is a tree of Markdown "artifacts" under `.aw/records/`, one file per unit of work:

- **plans** (`*.ipd.md`, "Implementation Plan Documents") - the largest and most numerous type
- **specs**, **backlog** items, **research** documents, **releases**, **walkthroughs**, **prompts**

Every artifact carries two kinds of content in ONE file:

1. **Prose written for, and read by, AI agents and humans**: the goal, the implementation checklist,
   the findings, the validation criteria. This is the point of the file.
2. **Structured metadata owned and consumed almost exclusively by the `aw` CLI**: a front-matter
   block of `- Key: value` lines (`Id`, `Status`, `Set`, `Order`, `Readiness`, `Scope-Paths`,
   `Item-Dependencies`, `Blocks-Release`, `From-Backlog`, `From-Spec`, ...) plus an append-only
   `## Workflow history` section recording every lifecycle transition.

Example of the metadata (real, trimmed):

```markdown
# IPD: wire the spec 2.1 run flag surface onto both host runners

- Date: 2026-09-03
- Kind: child
- Scope-Paths: agent_workflows/oc_runipd.py, tests/test_oc_runipd.py
- Item-Dependencies: executed:818uru
- Status: reviewed
- Readiness: go-pending-approval
- Set: runflags
- Order: 1
- Id: uyeko5
- Blocks-Release: next

## Workflow history

- 2026-09-04 reviewed (opencode/model-name): plan-review round 1: APPROVE WITH REVISIONS
  APPLIED; PR-001..PR-005 (5 findings, all FIXED in place...) [continues for 2000+ characters]
- 2026-09-03 to-review (opencode/model-name): Authored at the maintainer's direction after...
```

## 2. The question

**Should this tool-owned metadata stay inline in the Markdown artifacts, move to sidecar files
(per-artifact JSON, or one central JSONL / SQLite database), or some hybrid? And in what format?**

The tension: an AI agent must read and often rewrite this metadata on every interaction with a file,
spending context and tokens on data it does not reason about, while the `aw` CLI needs it to be
reliably machine-parseable. Optimize **token cost and agent context efficiency against tooling
correctness and human legibility**, and design accordingly.

## 3. Measured evidence from the live repository

Measure these yourself; here is what I get at the time of writing.

**Corpus size and metadata share** (483 `*.ipd.md` files under `.aw/records/plans/`, chars, and
tokens estimated at 4 chars/token):

| Component | Characters | Est. tokens | Share |
|---|---|---|---|
| Total plans corpus | 10,823,121 | ~2,705,780 | 100% |
| Front-matter blocks | 512,880 | ~128,220 | 4.7% |
| `## Workflow history` | 1,101,804 | ~275,451 | 10.2% |
| **Tool-owned subtotal** | **1,614,684** | **~403,671** | **14.9%** |

Median plan is 17,031 chars; median history block is 1,692 chars; the largest history block is
15,801 chars, and the worst offender is 20.0% history by volume. History grows without bound because
it is append-only and each entry is a prose paragraph.

**A partial migration already happened, and stalled.** The `awhistory` Set of plans (ids `x97z83`,
`im90a5`, `b0behn`, `cizkf4`, all under `.aw/records/plans/executed/`) built exactly the sidecar this
question contemplates: a single global append-only `.aw/records/history.jsonl`, plus a writer module
(`agent_workflows/record_history.py`) and a read verb. **Specs and backlog were routed to it and
their inline history slimmed to the latest single line. Plans were deliberately EXCLUDED.** The
scope of `b0behn` states the reason verbatim:

> EXPLICIT GUARD - PLANS/IPD `## Workflow history` (this Order touches ONLY specs.py + backlog.py;
> it MUST NOT slim any plan/IPD history, because `ipd_lint` IPD-S405 requires the inline `executed`
> entry at post-transition; the IPD lifecycle transition + research writers are a separate
> follow-up, not this Order).

Consequences to verify: `.aw/records/history.jsonl` currently holds 128 records, of which **108 are
backlog, 19 specs, and exactly 1 plans**. So the largest tree by far is the one still carrying full
inline history, and the migration's own follow-up was never done. Please treat "finish that
migration" as one candidate answer, not as the assumed answer.

**The sidecar as built would not, by itself, fix the correctness bug below**, because its `date`
field is day-granular (`"date": "20260819"`), exactly like the inline format.

## 4. The concrete bug that motivated this question

This is the failure that exposed the design question, and a good answer should say whether the
recommended design eliminates it structurally or merely relocates it.

`## Workflow history` has **no enforced ordering convention**, because two classes of writer
disagree and always have:

- The **status-setting tools** (`aw set`, `aw spec set`, `aw ipd dependencies set`) **PREPEND**, so
  they produce newest-first.
- **Human and AI authors** **APPEND**, so they produce oldest-first. The ~480-plan executed corpus
  is oldest-first.

A file touched by both therefore contains BOTH orderings, separated by a blank line, and no
fixed-direction parser can be correct about it. The reader
(`agent_workflows/ipd_lifecycle.py`, `_plan_status_events`) called `events.reverse()` on a hardcoded
newest-first assumption, so it derived a first transition of `to-review -> draft` (backwards) and the
validation rule `check.lifecycle-transition-invalid` reported **15 diagnostics against plans that
were never malformed**. That rule is fail-closed in CI, so the repository's own CI is red because of
it.

**Why the obvious fixes are unsatisfying**, all verified experimentally:

- *Sort by date instead of trusting file order.* Better, but insufficient: dates are day-granular
  with NO time component, and a same-day burst (`draft -> to-review -> reviewed` within one day) is
  the normal case. A stable date-only sort measured **worse**: 15 diagnostics became 32.
- *Sort by date, break ties by lifecycle rank* (`draft < to-review < reviewed < approved <
  executed`). Takes it to 3 diagnostics. But it INFERS sequence from the domain invariant rather
  than knowing it, and it cannot represent a legitimate same-day round trip (a plan re-reviewed
  after approval, which the repository's own spec explicitly permits).
- *Normalize the corpus to one ordering.* Rewrites nearly 500 files, and leaves the writers still
  disagreeing unless they are all changed too.

The root cause is arguably not the parser at all: **the durable record does not carry enough
information to reconstruct the sequence**, and it is stored in a format where an append and a
prepend are equally valid.

## 5. Constraints any recommendation must respect

1. **The prose must stay in Markdown.** Agents read these files; the narrative is the product. This
   question is only about the tool-owned metadata.
2. **Humans read and hand-edit these files, including in code review and `git diff`.** A design that
   makes an artifact's state invisible in a diff, or only knowable by running a tool, has a real
   cost - please weigh it rather than dismissing it.
3. **Git is the transport and the audit log.** Artifacts are committed. Consider merge-conflict
   behavior: a single central file that every concurrent agent appends to is a conflict magnet,
   which is a live concern because multiple agents work in one checkout simultaneously.
4. **The package is deliberately near-stdlib-only** (one runtime dependency, `filelock`). A design
   requiring a heavy dependency needs to justify it. Note SQLite is in the Python standard library.
5. **19 modules currently reference `## Workflow history`** (`attention.py`,
   `attention_contract.py`, `backlog.py`, `check_engine.py`, `cli.py`, `doctor.py`, `engine.py`,
   `ipd_lifecycle.py`, `ipd_lint.py`, `ipd_schema.py`, `plan_readiness.py`, `record_history.py`,
   `releases.py`, `review_findings.py`, `selectors.py`, `set_records.py`, `specs.py`,
   `status_set.py`, `status_untooled_gate.py`). Migration cost is real; please estimate it.
6. **A linter rule (`ipd_lint` IPD-S405) currently REQUIRES an inline `executed` history entry**, and
   `aw attention` derives a `last_history_at` timestamp from the inline record date. Any design must
   say what happens to these.
7. **Nothing is publicly released yet**, so breaking changes to the on-disk format are permitted if
   justified. A migration is acceptable; silent data loss is not.

## 6. What I want from you

Please deliver:

1. **A recommendation**, stated plainly, with the reasoning that decides it. If the answer is
   "it depends", say what it depends on and give a decision rule.
2. **A comparison of the realistic options**, at minimum: (a) status quo inline; (b) inline
   front-matter but history in a sidecar; (c) all tool-owned metadata in per-artifact sidecars;
   (d) one central append-only JSONL; (e) SQLite as the source of truth with generated views;
   (f) any hybrid you think better. For each: token/context effect, parse robustness, merge-conflict
   behavior under concurrent agents, human diff legibility, crash/partial-write safety, and
   migration cost.
3. **An explicit answer on the ordering bug**: does your design make transition order
   unambiguous by construction? What timestamp granularity and what identity/sequence fields do you
   recommend, and why? (Note a second observed defect worth accounting for: the tools stamp history
   dates in UTC while authors write local dates, so an evening action is dated one day in the
   future relative to hand-written lines in the same file.)
4. **A single-source-of-truth position**: if data is duplicated between Markdown and a sidecar,
   which one wins, how is drift detected, and how is it repaired? The repository's own convention is
   that generated views must be byte-reproducible from their source and drift must be a detectable
   finding rather than a silent divergence.
5. **A migration path** that is incremental and safe, given that ~500 artifacts and 19 modules are
   affected and that agents are actively working in the tree. Note the previous attempt stalled
   precisely at the largest tree; say how yours avoids that.
6. **What you would NOT do**, and why. Explicit rejected alternatives are as useful to me as the
   recommendation.

Cite specific files, and line numbers where you can, so the answer is checkable. Where you are
uncertain or the evidence is thin, say so rather than guessing; a clearly flagged unknown is more
useful than a confident invention.
