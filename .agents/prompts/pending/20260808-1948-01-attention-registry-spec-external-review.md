---
Kind: run-once
Status: pending
Created: 2026-08-08
Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
Targets: gpt-5.6 (Codex) and Gemini (run separately, compare)
Reviews-spec: .agents/docs/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
Grounding-research: .agents/docs/research/20260808-attention-registry-cross-tree-status-and-whatnext-00-bv6n38-attention-registry-cross-tree-status-and-whatnext.survey.md
Results-go-to: .agents/docs/research/ (file each returned .md as a review artifact)
---

# Operator note (NOT part of the prompt; do not upload this section)

This file stages a run-once external-review prompt. Upload EVERYTHING below the
`=== BEGIN UPLOAD-READY PROMPT ===` marker (or copy from that marker to the end) to gpt-5.6 and,
separately, to Gemini. Each is self-contained. Save each returned `.md` under `.agents/docs/research/`,
then move this prompt to `.agents/prompts/executed/`.

=== BEGIN UPLOAD-READY PROMPT ===

You are a senior software architect and API/CLI design reviewer. I am giving you a functional and
design specification for a new command-line tool and a cross-cutting convention. Your job is to
critically review it and return actionable feedback. Be rigorous, specific, and willing to disagree;
do not rubber-stamp. Prioritize correctness, simplicity, and long-term maintainability over praise.

At the very end, return your entire review as a single DOWNLOADABLE markdown (`.md`) file (provide it
as a file I can download, named `attention-registry-spec-review-<your-model-name>.md`). Do not put the
review only in the chat body; produce the downloadable file.

## Context you need

This is a Python project called `agent-workflows`: a stdlib-only (zero runtime dependencies, Python 3.9
compatible) toolkit installed into other repositories to give AI coding agents reusable, machine-checkable
"workflows" and conventions. It ships an importable package exposing an `aw` CLI (e.g. `aw plans`,
`aw research`, `aw ipd`, `aw sanitize`). Durable artifacts live under an `.agents/` directory tree, split
into several "artifact trees":

- `.agents/plans/` - implementation plan documents (IPDs). Has directory-as-disposition
  (pending/executed/superseded/not-executed/reusable), a front-matter `Status:` readiness enum
  (draft, to-review, reviewed, approved, auto-approved; terminal executed/superseded/not-executed;
  standing reusable), an appended `## Workflow history` section, and a tool-generated INDEX
  (`aw plans index --check` fails on drift).
- `.agents/docs/research/` - research/analysis docs. Tool-owned front-matter `status:` enum
  (intake, active, reference, archive), with an INDEX and `--check`.
- `.agents/prompts/` and `.agents/comms/` - operational queues with their own disposition dirs / status.
- `.agents/docs/specs/` - design specs (like this one). Currently FLAT files with a FREE-FORM prose
  status line, NO history section, NO manifest.
- `.agents/docs/walkthroughs/` and `.agents/docs/roadmaps/` - narrative/intent docs, no status tracking.

There is a shared internal module (`artifact_core`) providing reusable primitives: a deterministic file
walker, a `Drift` record type with a machine-readable renderer (tab-separated `location<TAB>rule<TAB>detail`)
and a `drift_exit_code` (0 clean / 1 drift) convention that every `--check` command reuses, plus id
generation, shard-by-week math, atomic file writes, and git-mv helpers.

There is a `/whatnext` workflow whose job is to answer "what needs attention across the repo?" Today it
does this at RUNTIME by having a large language model read raw files, directories, git status, and a
TODO.md every invocation. That is token-expensive, non-deterministic, and it never scans specs, research,
roadmaps, or walkthroughs at all, so any deferred/unbuilt work described in a spec is invisible unless a
human manually copied it into TODO.md.

Note: an `aw status` command ALREADY EXISTS (it reports installer/version state), so the new tool is
named `aw attention` to avoid collision.

## What I want you to review

The spec below proposes: (1) a small tree-agnostic "attention class" vocabulary + a pure mapping from each
tree's native status to a class; (2) requiring a standardized status + history on trees that lack one
(specs first); (3) a deterministic `aw attention` scanner that emits a committed registry
(`.agents/ATTENTION.md` + `.agents/ATTENTION.json`) with a `--check` drift gate; (4) write verbs
(`aw attention set` / `aw attention note`) that update status + append history atomically; (5) rewiring
`/whatnext` to READ the registry instead of re-scouring.

## Specific questions to answer (in addition to any issues you find)

1. Is the "keep each tree's native status enum, standardize only a pure (tree, status) -> attention-class
   MAPPING" abstraction the right call, versus forcing one unified status enum across all trees? What
   breaks either way? Critique the proposed four classes (needs-attention, in-flight, done, parked) and
   the mapping in Section 6.
2. Registry shape: one roll-up file `.agents/ATTENTION.*` vs per-tree registries plus a roll-up (OQ3).
   Which, and why, given the goal is a cheap single read for `/whatnext` and a stable CI `--check`?
3. The WRITE verbs vs tool-owned trees (OQ7): should `aw attention set` DELEGATE to the owning tool
   (`aw plans`/`aw research`) for those trees, be read-only for them, or own writes uniformly? What is
   the cleanest, least-surprising, least-duplicative design?
4. How should a `deferred`/gated artifact express its GATE (OQ4) so the registry can render the blocker
   and `/whatnext` can prioritize? Propose a concrete front-matter field and format.
5. Is `--check` correctly scoped (registry-vs-disk drift + contract violations: missing/unknown status,
   deferred-without-gate)? Any determinism or CI pitfalls?
6. Failure modes and drift: where could the registry silently diverge from truth, and how would you
   prevent it by construction?
7. Phasing (Section 13): is v1 (specs standardization + scanner/registry over already-structured trees +
   whatnext-as-reader) the right first slice? Anything mis-scoped, missing, or that should move earlier
   or later?
8. Simpler alternative: is there a materially simpler design that meets the goals (Section 3) with less
   machinery? If so, describe it concretely.
9. Naming, CLI ergonomics, and the interaction with the existing `aw plans`/`aw research`/`aw ipd`
   surface: anything confusing, redundant, or inconsistent?
10. Concrete edits: list the specific changes you would make to the spec (by section), and flag any
    requirement (Section 9) or acceptance criterion (Section 10) that is untestable, ambiguous, or wrong.

Structure your returned `.md` as: (a) a one-paragraph overall assessment; (b) the strongest concerns
ranked; (c) answers to questions 1-10; (d) a concrete list of proposed spec edits; (e) any smaller nits.
Use plain ASCII punctuation (no em or en dashes).

## The spec under review

```markdown
# Spec: attention registry and cross-tree status model (aw attention)

## 1. One-line summary
A deterministic, stdlib-only tool (aw attention) that scours the standardized .agents/ artifact trees,
maps each artifact's native status onto a small tree-agnostic ATTENTION class, and maintains a committed
registry (.agents/ATTENTION.md + .agents/ATTENTION.json) of what needs attention, what is in flight, what
is done, and what is parked; plus write verbs that update an artifact's status and append its history
atomically, so /whatnext and CI READ the registry instead of re-deriving state at runtime.

## 2. Problem / motivation
The repo already has a mature, machine-legible state model, but it is applied UNEVENLY, and the one
workflow that answers "what needs attention?" (/whatnext) re-derives that answer at runtime by having the
LLM read raw files, directories, git, and TODO.md every single invocation.
- Uneven state: plans/, prompts/, comms/, and research/ have machine-legible state; specs/,
  walkthroughs/, and roadmaps/ do NOT (specs carry a free-form prose Status bullet, no history, no
  manifest). Specs routinely describe UNBUILT or DEFERRED work, which is invisible to /whatnext today
  unless a human transcribed it into TODO.md.
- Runtime re-derivation is costly and non-deterministic: /whatnext walks raw sources each run at token
  cost that scales with corpus size, yet most of the answer is a pure function of on-disk state, and it
  never scans specs/research/roadmaps/walkthroughs.
Fix: standardize status/filenames/locations; let a cheap deterministic tool scour once and emit a
registry; let the SAME tool WRITE status transitions and history so the registry stays true by
construction; make /whatnext a thin READER.

## 3. Goals (each testable)
- G1 [Must] Define a small, tree-agnostic ATTENTION-CLASS vocabulary and a pure mapping from each tree's
  native status to a class, WITHOUT forcing one status enum onto trees that have their own.
- G2 [Must] Standardize and REQUIRE a machine-legible status on trees that lack one (specs first), plus
  an appended ## Workflow history convention, lifted from the plans model.
- G3 [Must] Provide aw attention (READ): a deterministic scanner that regenerates a committed registry
  (.agents/ATTENTION.md human view + .agents/ATTENTION.json machine view) grouped by attention class,
  with a --check drift gate (CI-wireable) and a --agent machine-readable mode, reusing the existing
  Drift/render_agent_drift/drift_exit_code convention.
- G4 [Must] Provide write verbs (aw attention set / aw attention note) that update an artifact's status
  and append a dated history line atomically and self-recordingly, then refresh the registry.
- G5 [Must] Rewire /whatnext to READ the registry as its primary source and escalate to deep reading only
  for the specific flagged items.
- G6 [Must] Reuse artifact_core; zero runtime deps; Python 3.9 compatible; ship in the importable package
  as aw attention and python -m agent_workflows attention.
- G7 [Should] Design the FULL cross-tree vision as the north star, but scope the FIRST build phase to:
  specs standardization, the scanner + registry over the already-structured trees plus specs, and
  whatnext-as-reader. Later: walkthroughs/roadmaps and the full write-verb surface.
- G8 [Must] Never break existing citation paths or existing per-tree tooling.

## 4. Non-goals
- NOT replacing the per-tree lifecycles or their enums; the registry sits ABOVE them.
- NOT moving specs into disposition subdirectories in v1 (breaks existing citation paths for ~8 files).
- NOT a daemon/watch/service; run-on-demand / run-in-CI, like aw plans index.
- NOT a task manager; it reflects existing state, does not invent work.
- NOT replacing TODO.md (the human backlog for un-artifacted ideas).
- NOT auto-committing beyond what a verb explicitly does (path-scoped, never push).

## 5. Users / actors and scenarios
- /whatnext (primary consumer): reads .agents/ATTENTION.json, presents needs-attention + in-flight,
  escalates to reading only flagged artifacts.
- A human maintainer: reads .agents/ATTENTION.md; runs aw attention set <spec> implemented when a spec
  ships; trusts --check in CI.
- An executing agent: after finishing, runs aw attention set/note to record transition + history.
- CI: runs aw attention --check to gate that on-disk status + the registry agree.

## 6. The attention-class model (load-bearing)
Each tree keeps its NATIVE status. The registry defines a pure function class_of(tree, native_status) ->
AttentionClass. Proposed classes:
- needs-attention: work defined but not moving and something is required to advance it. E.g. spec
  approved-but-not-implemented; spec/plan draft/to-review/reviewed; research intake; any deferred WITH an
  open gate.
- in-flight: actively being worked. E.g. plan approved/auto-approved under execution; research active.
- done: terminal-success. E.g. plan executed; spec implemented/canonical; research reference.
- parked: deliberately not active, kept for record. E.g. plan superseded/not-executed; research archive;
  spec superseded; a deferred item whose gate is a deliberate decision.
Rationale: preserves every existing enum and tool while giving ONE scanner a uniform answer. A
deferred/gated artifact SHOULD cite its gate so the registry renders the blocker.

## 7. Standardized status + history contract
- Specs (v1): REQUIRE a front-matter Status from a closed enum: draft -> reviewed -> approved ->
  implemented, plus terminal superseded and standing deferred (which MUST carry a gate). Normalize the
  current free-form prose values to the enum. canonical reference specs map to implemented (or a distinct
  value - open question).
- ## Workflow history: every spec (and every tree the registry writes to) gains an appended history
  section, one dated line per touch, lifted from the plans convention.
- Tool-owned trees (plans/research): NO new field; the registry reads their existing status and the
  mapping does the rest.

## 8. Functional design
8.1 aw attention (READ/regenerate): scans standardized trees via iter_scan_files, reads native status,
maps to a class, regenerates .agents/ATTENTION.json (machine: path, tree, native_status, class, id, gate?,
last_history_date) and .agents/ATTENTION.md (human board grouped by class, needs-attention first, bounded
hot-window with overflow, gated items showing blocker). --check recomputes and diffs against committed
files, emits Drift records, exits drift_exit_code; also flags contract violations (missing/unknown status,
deferred without gate). --agent prints tab-separated records. Deterministic and pure.
8.2 aw attention set <artifact> <status> and note <artifact> <text> (WRITE): set validates the status
against the tree enum, rewrites front-matter via atomic_write, appends a history line, refreshes the
registry; for tool-owned trees it DELEGATES to the owning verb or refuses and points at it. note appends a
history line only. Both are explicit, self-recording, path-scoped-committable; the tool does not commit.
8.3 /whatnext integration: Step 1 gains a FIRST source (read .agents/ATTENTION.json), keeping existing
sources as fallback/reconcile for what the registry cannot know.

## 9. Requirements
Functional: F1 pure class_of covering every native status; unknown -> contract-violation drift, never a
silent drop. F2 deterministic registry regenerate. F3 --check exits nonzero on registry-vs-disk drift OR
missing required status OR unknown status OR deferred lacking a gate. F4 --agent tab-separated. F5 set
updates+history+refresh atomically, validates, delegates/refuses for tool-owned trees. F6 note
appends+refresh. F7 specs REQUIRE closed-enum Status + history; a one-time migration normalizes ~8 specs.
F8 /whatnext reads the registry first.
Non-functional: N1 stdlib only, zero deps, Python 3.9. N2 ships in the importable package as aw attention
+ python -m agent_workflows attention, NOT a per-target tools/ script. N3 reuses artifact_core; no fork.
N4 name is aw attention (aw status already exists). N5 --check deterministic/stable. N6 no em/en dashes.

## 10. Acceptance criteria
A1 aw attention lists the three deferred specs in needs-attention with gates, and the two implemented
specs in done. A2 --check exits 0 after regenerate, nonzero after any hand-edit. A3 aw attention set
<spec> implemented flips status, appends history, and a following --check is clean. A4 a spec with no
Status / unknown value / deferred-without-gate makes --check fail with a contract-violation naming the
file. A5 existing aw plans index --check and aw research index --check still pass. A6 /whatnext produces
its board from the registry and reads only flagged artifacts thereafter. A7 full unittest suite green with
new tests for the mapping, scanner, --check, and write verbs.

## 11. Constraints and dependencies
Depends on artifact_core and the per-tree status conventions; the CLI wiring pattern (a new attention.py
module with run(args)->int wired at two edit points in cli.py). The registry location .agents/ATTENTION.*
must be scaffolded by the installer. The spec migration touches ~8 files once, no citation change.

## 12. Open questions
OQ1 exact attention-class enum + full per-tree mapping table; does canonical map to done/implemented or
its own value? OQ2 keep native status fields + standardize only the mapping (leaning yes) vs one unified
field? OQ3 one registry file vs per-tree + roll-up (leaning one roll-up)? OQ4 how a deferred/gated
artifact expresses its gate (a Blocked-by:/Gate: field citing a TODO line or Dnn)? OQ5 registry
required-in-sync + CI-gated (leaning yes) vs advisory? OQ6 specs flat-with-Status (leaning yes) vs
disposition subdirs (rejected: breaks citations)? OQ7 write verbs vs tool-owned trees: delegate vs
read-only-for-those-trees (leaning read-only for tool-owned, write for the newly-standardized)? OQ8 do
walkthroughs have an attention status or are they always done (leaning excluded/always-done)? OQ9 does the
spec migration land in the same phase as the scanner (leaning yes)?

## 13. Out-of-scope / future (phasing)
Phase 1 (first build): specs status+history standardization + one-time normalization; attention.py
scanner + .agents/ATTENTION.* registry + --check + --agent over already-structured trees plus specs;
/whatnext reads the registry. Phase 2: full write-verb surface incl. delegation + CI wiring of --check.
Phase 3: walkthroughs and roadmaps adoption and roll-up refinements.
```

Return your review now as a downloadable `.md` file named
`attention-registry-spec-review-<your-model-name>.md`.
