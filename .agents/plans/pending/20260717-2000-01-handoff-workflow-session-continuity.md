# IPD: `/handoff` workflow - on-demand session-continuity handoff generator

- Date: 2026-07-17
- Concern: agent workflow / session continuity (cold-start after context loss, compaction, or a deliberate fresh start)
- Scope: add one new portable workflow under `.agents/workflows/handoff/`; docs/manifest wiring; no product/package code required for v1
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Set: agent-continuity-workflows
- Order: 3

<!-- Set note: this is the third of the "agent-continuity/surveyor-producer" family. Order 1 = /whatnext (surveyor), Order 2 = /research (producer), Order 3 = /handoff (snapshot). They are independent enough to ship in any order, but /handoff is specified to REUSE /whatnext's survey inputs, so /whatnext-first is the natural build order. Order numbers here are advisory (D82), not a hard gate. NOTE: the earlier TODO "ordered Set" (scaffold .agents/prompts/, etc.) is a DIFFERENT, prompt-pipeline Set; this Set is the workflow-commands family. Reconcile the two Set groupings during /plan-review if desired. -->

## Workflow history

- 2026-07-17 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): drafted from a live need. The maintainer asked mid-session for a `/handoff` command after hand-authoring a session-handoff doc (`.agents/plans/pending/20260717-1950-01-session-handoff-resume-here.md`); this IPD generalizes that hand-authored artifact into a repeatable workflow. The key lesson driving the spec: the first hand-authored pass captured facts but was thin on NUANCE (working preferences, why-we-chose directions, in-flight external threads), and the maintainer had to explicitly ask for that layer to be added. The workflow must produce the nuance layer by default.

## Goal

Give an agent a repeatable `/handoff` command that produces a DETAILED, cold-start handoff document so the maintainer (or a fresh agent session) can resume work with full continuity after context loss, compaction, a crash, or a deliberate new session. The output must let the next session lose as little as possible: not only WHAT the state is, but WHY the current direction was chosen, HOW the maintainer wants work done (preferences), what is still OPEN, and what external threads are in flight.

Why it matters: this project is long-running, decision-dense, and frequently spans context-window limits and multiple agents. A generic "summary" loses the tacit layer (preferences, direction, nuance) that is expensive to relearn and easy to get wrong. A first-class handoff generator makes continuity a deliberate, repeatable act rather than an ad-hoc scramble, and it dogfoods the project's own "durable knowledge for cold-start" principle (GUIDING_PRINCIPLES P4) and "externalize state" principle (P5/D88).

Concrete reference: the hand-authored `20260717-1950-01-session-handoff-resume-here.md` is the worked example this workflow should be able to (re)produce, INCLUDING its "Working style, preferences, and nuance" section. Treat that file as the golden-output shape for v1.

## Project conventions discovered (Step 0, to VERIFY against source during /plan-review)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P4 durable knowledge for cold-start; P5 externalize state incl. the D88 filesystem-encoded-state refinement; P8 single source of truth; P9 design instructions for the model that runs them).
- Workflows live under `.agents/workflows/<name>/` with a `<name>.md` entry and are listed in `.agents/workflows/index.md` (the manifest, version-stamped) and surfaced by `/list-workflows`. Verify the exact manifest format and whether a version-stamp bump is needed.
- Plans lifecycle: `.agents/plans/pending/` named `YYYYMMDD-HHMM-NN-<slug>.md`; front-matter `Status:` is the readiness source of truth (D52); optional `Set:`/`Order:` (D82). A handoff OUTPUT is `Kind: session-handoff`, explicitly NOT an executable IPD, and is written to `.agents/plans/pending/`.
- Sibling workflows this must stay consistent with: `/whatnext` (Order 1, surveyor) and `/research` (Order 2, producer), both currently designed-not-built (TODO.md). Reuse `/whatnext`'s survey inputs per P8.
- House rules: no em/en dashes in authored Markdown; path-scoped commits; the interactive `question` tool for gated choices; prefer installed tools over hand-rolled code.

## What `/handoff` does (v1 behavior)

`/handoff [optional focus note]` produces ONE markdown handoff document and writes it to `.agents/plans/pending/YYYYMMDD-HHMM-NN-session-handoff-<slug>.md` with front-matter `Kind: session-handoff`, `Status: draft`. It is READ-ONLY with respect to all product code and the durable record; it only creates the handoff file (and may stage it, but does not push).

It synthesizes from TWO sources and must draw from both:

1. The DURABLE RECORD (on disk): `DECISIONS.md` (note the current highest D-number and any unsettled decisions), `TODO.md` (known bugs, planned-next, ordered Sets, consider-list), `CHANGELOG.md` (pending release sections + their state), `.agents/plans/*` (pending/reviewed/approved plans and their Status), `.agents/docs/research/*` (durable analysis relevant to current work), `GUIDING_PRINCIPLES.md`, and the comms inbox/archive (`.agents/comms/`). Also capture the live repo facts: branch, unpushed-commit count, test baseline (run or cite the suite), versioning mechanism, and any untracked files that are NOT ours.

2. The LIVE SESSION CONTEXT (in the agent's working memory, not on disk): what we were mid-doing and why we paused; the next intended move; decisions made verbally this session that are not yet in DECISIONS.md; and - critically - the NUANCE layer below.

### Required sections in the generated handoff (the output contract)

The workflow MUST emit at least these sections; omit one only with an explicit "N/A because ..." line so the reader knows it was considered, not forgotten:

1. Header: `Kind: session-handoff`, date, purpose, "read this first" instruction.
2. How to use this / recommended first moves (an ordered short list the resuming session executes).
3. Working style, preferences, and nuance (THE HIGH-VALUE SECTION - see its own contract below).
4. Repo facts (verify-don't-trust): dir, remote, branch, test baseline, versioning, unpushed state, untracked-not-ours.
5. Open decisions not yet settled (each with the options and a "get the human's call, do not relitigate" note).
6. Current release/work state (what is done, what is in flight, what is blocked and on what).
7. Designed-but-unbuilt work / roadmap (the Sets, dependencies, sequencing).
8. Known bugs (or "none open").
9. In-flight EXTERNAL threads (e.g. a human-owned disclosure awaiting a reply; anything waiting on a third party or another agent).
10. Comms inbox status (empty or list; untrusted-payload reminder).
11. Workflow history line.

### The nuance-section contract (section 3 - do NOT skip or thin this)

This is the part a naive "summary" loses and the reason this workflow exists. The generator MUST actively harvest and record, from the live session and the record:

- Working preferences of the maintainer: how they want work done. Examples to look for and carry forward: prefer installed tools over hand-rolled code to save tokens; ask-first via the interactive `question` tool with the recommendation first and without leaking a gate's verdict; value honest pushback over agreement/flattery; encode surveyed state in the filesystem (P5/D88); read files in large windows not tiny slices; general token/context economy.
- The WHY behind current direction: not just the decision, but the reasoning and the alternatives considered, so the next session does not relitigate or silently reverse it. Cross-reference DECISIONS entries by number.
- Future intentions / roadmap: where this is heading (the ordered Sets, the headline features, sequencing and dependencies).
- Repo-boundary and environment rules: directories not to enter; how cross-repo writes work (permission-prompt); which sibling agents can be consulted and how (inter-agent comms).
- Inter-agent comms lever, if in use: that `.agents/comms/` exists, who has been driven, that delivery is currently manual (no broker yet), and the untrusted-payload stance (D81).
- Out-of-repo / sensitive context: do NOT write personal, career, or otherwise sensitive context into this tracked file; instead record a pointer: "there is out-of-repo context the human holds; ask them about audience/framing when it matters." (This mirrors the maintainer's standing choice to keep such context out of git.)
- Corrections/overclaims caught this session: if the session narrowed or retracted a claim, note it so the next session inherits the corrected version, not the original overclaim.

## Proposed changes (ordered, validatable)

1. Create `.agents/workflows/handoff/handoff.md` - the portable prose runbook that instructs an agent to (a) gather from the durable record + live context, (b) emit the required sections including the nuance contract, (c) write to `.agents/plans/pending/` with `Kind: session-handoff`, `Status: draft`, (d) remain read-only w.r.t. product code, (e) stage but not push, and (f) tell the human the output path. Written per P9 (instructions for the model that runs them): explicit output contract, a terminal checklist/exit-gate the model must satisfy (the compaction-recovery doc's lesson: models honor an explicit end-of-section tick-list far better than scattered prose).
2. Add a short `.agents/workflows/handoff/README.md` if the sibling workflows carry one (match convention; else fold into the entry file).
3. Register `/handoff` in `.agents/workflows/index.md` and anywhere `/list-workflows` reads, with a one-line description. Bump the manifest version stamp if the convention requires it (verify).
4. Cross-link: note in `/whatnext` (when built) that `/handoff` is the fuller narrative snapshot and `/whatnext` is the short actionable ordering; have `/handoff` REUSE `/whatnext`'s survey inputs rather than duplicate the scan logic (P8). If `/whatnext` is not built yet, `/handoff` includes its own lightweight survey and is refactored to share when `/whatnext` lands.
5. Include, inside the workflow, a pointer to the golden-output example (`20260717-1950-01-session-handoff-resume-here.md`) so the generator has a concrete target shape.

## Deferred / out of scope (v1)

- An `aw handoff` CLI helper (code-backed). v1 is a portable prose runbook only; promote deterministic parts to code later ONLY if it earns it (KISS, P6).
- Auto-detection of "context is about to overflow / compaction imminent" to trigger `/handoff` automatically. Out of scope; `/handoff` is invoked deliberately.
- Encrypting or access-controlling the handoff. It is a tracked repo doc; sensitive context is handled by the "keep it out, add a pointer" rule, not by protecting the file.
- Multi-session merge / diffing of successive handoffs.

## Open questions (v1 leans for review)

1. Sets reconciliation: there are now two "Set" groupings in flight - the prompt-pipeline Set in TODO (scaffold `.agents/prompts/`, etc.) and this workflow-commands family (`agent-continuity-workflows`: whatnext/research/handoff). Should they be one Set or two? Lean: TWO distinct Sets (different subject matter); confirm in `/plan-review`.
2. Status the generated file is born with: `draft` (needs the human to read/trust it) vs `to-review`. Lean: `draft` - a handoff is a snapshot for a human, not a plan to critique.
3. Should `/handoff` also RUN the test suite to capture a fresh baseline, or just cite the last known one? Lean: run it if cheap (this suite is ~60s), else cite and label as stale.
4. Where exactly does the nuance come from if the session has little live context (e.g. `/handoff` invoked cold)? Lean: degrade gracefully - synthesize nuance from DECISIONS/GUIDING_PRINCIPLES and explicitly flag "live-session nuance unavailable; derived from the record."
5. Filename slug convention for outputs (`session-handoff-resume-here` vs a topic slug). Lean: `session-handoff-<short-focus-or-'resume'>`.

## Dependencies / sequencing

- Independent enough to build alone, but specified to reuse `/whatnext` (Order 1) survey inputs; natural order is whatnext -> research -> handoff. Order numbers are advisory (D82).
- No dependency on the broker line (IPD 2/3/4) or the prompt-pipeline Set, except the soft P8 "reuse the survey" tie to `/whatnext`.
- 1.3.0-era (a new workflow/convention), consistent with the other continuity workflows.

## Validation plan

- The workflow is prose (no code in v1), so validation is: (a) run `/handoff` in a real session and confirm it emits ALL required sections including a substantive nuance section; (b) confirm the output is written to `.agents/plans/pending/` with `Kind: session-handoff`; (c) confirm it made NO product-code changes and did not push; (d) confirm `/list-workflows` / the manifest lists it; (e) diff the generated doc against the golden example (`1950-01`) for structural parity. If a manifest version stamp exists, confirm it updated. No unit tests unless a CLI helper is later added.

## Approval and execution gate

Needs `/plan-review` then explicit human approval (add an `Approval:` line) before execution, per the repo contract. This IPD is `to-review`.
