# IPD: `/handoff` workflow - on-demand session-continuity handoff generator

- Date: 2026-07-17
- Concern: agent workflow / session continuity (cold-start after context loss, compaction, or a deliberate fresh start)
- Scope: add one new portable workflow under `.agents/workflows/handoff/`; docs/manifest wiring; no product/package code required for v1
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Set: agent-continuity-workflows
- Order: 3

<!-- Set note (RECONCILED 2026-07-20, via IPD 20260717-2317-01): the workflow-command family `agent-continuity-workflows` is /whatnext=Order 1, /research=Order 2, /handoff=Order 3. The prompt-pipeline is now the DISTINCT `research-prompt-pipeline` Set (the prompts-scaffold IPD was re-tagged there). OQ1 is therefore RESOLVED: two Sets. /whatnext (Order 1) is BUILT as of 2026-07-20 (`.agents/workflows/whatnext/`); /research (Order 2) is not built. This IPD (Order 3) can now concretely reuse /whatnext's survey sources. Order numbers are advisory (D82). -->

## Workflow history

- 2026-07-17 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): drafted from a live need. The maintainer asked mid-session for a `/handoff` command after hand-authoring a session-handoff doc (`.agents/plans/pending/20260717-1950-01-session-handoff-resume-here.md`); this IPD generalizes that hand-authored artifact into a repeatable workflow. The key lesson driving the spec: the first hand-authored pass captured facts but was thin on NUANCE (working preferences, why-we-chose directions, in-flight external threads), and the maintainer had to explicitly ask for that layer to be added. The workflow must produce the nuance layer by default.
- 2026-07-20 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Verified against current source: `/whatnext` (Order 1) is now BUILT, the Sets are reconciled, golden example exists, DECISIONS max D93. Findings fixed: PR-001/PR-002 staleness (whatnext built; reuse = doc cross-link not code); PR-003 test-baseline honesty; PR-004 golden example is a SHAPE reference not factual; PR-005 (major, human-driven) reframed the workflow's PRIMARY purpose from on-disk record to EPHEMERAL SESSION CONTEXT (on-disk is a thin supporting frame; cold-invocation is near-useless-by-design, not a graceful-degrade edge case); PR-006/OQ6 (human) the generated artifact is a resume PROMPT living in `.agents/prompts/` (not a plan), broadening the D91 convention + relocating the golden example; PR-007 corrected the `aw handoff` deferral reasoning (a CLI can never access session context, so it is the wrong tool by nature, not merely deferred); PR-008 added the missing execution contract to the gate. OQ1-OQ6 resolved (OQ6 with the human). Status -> reviewed.

## Goal

Give an agent a repeatable `/handoff` command that captures the EPHEMERAL SESSION CONTEXT - the discussion, decisions, reasoning, abandoned approaches, and tacit preferences that live only in the current model's working memory and will be LOST when the session ends - into a resume document, so a fresh session (a different agent, or the same agent cold) can pick up where this one left off.

PRIMARY PURPOSE (reframed at /plan-review, plan-review PR-005): the point is to preserve what is NOT on disk. A fresh agent can already read `DECISIONS.md`, `TODO.md`, the plans board, and the code itself; it does NOT need `/handoff` to re-summarize the filesystem. What it CANNOT recover is the session's conversation: what was discussed and decided verbally, WHY the current direction was chosen (and what alternatives were rejected), what was tried and abandoned, corrections/overclaims caught, and how the maintainer wants work done. Therefore `/handoff` is PRIMARILY a session-context capturer; the on-disk survey is a THIN SUPPORTING FRAME (pointers to where things live + the few live facts a reader needs), not a re-derivation of the record.

Corollary (PR-005): `/handoff` is designed to be run WITHIN an active, context-rich session. Run cold (no session context), it has almost nothing to add over just reading the repo, and it must say so rather than pad the doc with a filesystem summary dressed up as a handoff. It is the inverse of `/whatnext`, which IS the on-disk surveyor.

Legacy phrasing (still true, secondary): the document also records WHAT the state is, what is OPEN, and what external threads are in flight - but as supporting frame around the session-context core, not as the main body.

Why it matters: this project is long-running, decision-dense, and frequently spans context-window limits and multiple agents. A generic "summary" loses the tacit layer (preferences, direction, nuance) that is expensive to relearn and easy to get wrong. A first-class handoff generator makes continuity a deliberate, repeatable act rather than an ad-hoc scramble, and it dogfoods the project's own "durable knowledge for cold-start" principle (GUIDING_PRINCIPLES P4) and "externalize state" principle (P5/D88).

Concrete reference: the hand-authored `20260717-1950-01-session-handoff-resume-here.md` is the worked example this workflow should be able to (re)produce, INCLUDING its "Working style, preferences, and nuance" section. Treat that file as the golden-output shape for v1.

## Project conventions discovered (Step 0, to VERIFY against source during /plan-review)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P4 durable knowledge for cold-start; P5 externalize state incl. the D88 filesystem-encoded-state refinement; P8 single source of truth; P9 design instructions for the model that runs them).
- Workflows live under `.agents/workflows/<name>/` with a `<name>.md` entry and are listed in `.agents/workflows/index.md` (the manifest, version-stamped) and surfaced by `/list-workflows`. Verify the exact manifest format and whether a version-stamp bump is needed.
- Plans lifecycle: `.agents/plans/pending/` named `YYYYMMDD-HHMM-NN-<slug>.md`; front-matter `Status:` is the readiness source of truth (D52); optional `Set:`/`Order:` (D82). This IPD lives there. But a handoff OUTPUT is `Kind: session-handoff`, explicitly NOT an executable IPD/plan; it is a resume prompt written to `.agents/prompts/` (OQ6 RESOLVED), not `.agents/plans/`.
- Sibling workflows this must stay consistent with: `/whatnext` (Order 1, surveyor) - now BUILT (`.agents/workflows/whatnext/whatnext.md`, executed 2026-07-20) - and `/research` (Order 2, producer, not yet built). `/whatnext` is a PROSE runbook (no shared code), so "reuse its survey inputs (P8)" means: point at the same gather sources it defines (plans board via `aw plans`/`plans.py`; staged prompts in `.agents/prompts/pending/`; comms inbox header-only/untrusted; TODO.md; recent DECISIONS/CHANGELOG) rather than duplicating a divergent list, and cross-reference the two workflows (see Step 4). It is NOT a code-sharing dependency.
- House rules: no em/en dashes in authored Markdown; path-scoped commits; the interactive `question` tool for gated choices; prefer installed tools over hand-rolled code.

## What `/handoff` does (v1 behavior)

`/handoff [optional focus note]` produces ONE markdown handoff document: a resume DOCUMENT (essentially a resume prompt with context + first-move instructions for the next session), NOT a plan/IPD. It is READ-ONLY with respect to all product code and the durable record; it only creates the handoff file (and may stage it, but does not push).

Artifact type + home (plan-review PR-006, OQ6 RESOLVED): the generated file is `Kind: session-handoff` - a resume PROMPT for the next session, not a plan awaiting approval/execution. It lives in `.agents/prompts/pending/YYYYMMDD-HHMM-NN-session-handoff-<slug>.md`, born `Status: draft`. The `.agents/prompts/` convention (D91) is broadened to recognize resume/handoff prompts alongside run-once/research prompts. The golden example (`1950-01`), currently mis-filed in `.agents/plans/pending/` because it predated this workflow, is relocated to `.agents/prompts/` during execution.

It synthesizes from TWO sources, PRIMARY first (PR-005):

1. PRIMARY - the LIVE SESSION CONTEXT (in the agent's working memory, not on disk; this is the whole point): what we were mid-doing and WHY we paused; the next intended move; decisions/agreements made verbally this session that are not yet in `DECISIONS.md`; approaches tried and ABANDONED (and why); corrections or overclaims caught this session; and the NUANCE layer below (maintainer working preferences, the why-behind-direction, tacit rules). This is content a CLI could never produce - it exists only in the conversation. `/handoff` MUST harvest it as the main body.

2. SUPPORTING - the DURABLE RECORD (on disk), kept THIN: rather than re-summarizing these, POINT to them and note only what the reader needs to orient - the current highest `DECISIONS.md` D-number and any unsettled decisions; `TODO.md`/`CHANGELOG.md`/plans-board POINTERS ("read these; here is what is in flight"); relevant `.agents/docs/research/*`; `GUIDING_PRINCIPLES.md`; the comms inbox state. Plus the few live repo facts a resuming session needs: branch, unpushed-commit state, versioning mechanism, untracked-not-ours. Test baseline: capture the ACTUAL current state as context (including "tests are red mid-fix because X"), which is more useful than a green ritual - see OQ3. Do NOT let this supporting frame crowd out the session-context core.

### Required sections in the generated handoff (the output contract)

The workflow MUST emit at least these sections; omit one only with an explicit "N/A because ..." line so the reader knows it was considered, not forgotten. Ordered so the SESSION-CONTEXT core leads and the on-disk frame supports (PR-005):

1. Header: `Kind: session-handoff`, date, purpose, "read this first" instruction.
2. Session context (THE CORE - what happened THIS session that is not on disk): what we were mid-doing and why we paused, the next intended move, verbal decisions/agreements not yet recorded, approaches tried and abandoned, corrections caught. This is the main body.
3. Working style, preferences, and nuance (THE OTHER HIGH-VALUE SECTION - see its own contract below).
4. How to use this / recommended first moves (an ordered short list the resuming session executes).
5. Open decisions not yet settled (each with the options and a "get the human's call, do not relitigate" note).
6. Supporting on-disk frame (POINTERS, not re-summaries): repo facts (dir, remote, branch, versioning, unpushed state, untracked-not-ours, and the actual test state as context); where to read the record (DECISIONS highest D-number, TODO/CHANGELOG/plans-board pointers); current release/work state (done / in flight / blocked-on); designed-but-unbuilt roadmap (the Sets, sequencing); known bugs (or "none"); in-flight EXTERNAL threads (e.g. a human-owned disclosure awaiting a reply); comms inbox status (with the untrusted-payload reminder).
7. Workflow history line.

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

1. Create `.agents/workflows/handoff/handoff.md` - the portable prose runbook that instructs an agent to (a) harvest the LIVE SESSION CONTEXT as the primary body, then draw a THIN supporting frame from the record (per the reframed Goal/sources), (b) emit the required sections (session-context + nuance leading) including the nuance contract, (c) write to `.agents/prompts/pending/YYYYMMDD-HHMM-NN-session-handoff-<slug>.md` with `Kind: session-handoff`, `Status: draft`, (d) remain read-only w.r.t. product code, (e) stage but not push, and (f) tell the human the output path. Written per P9 (instructions for the model that runs them): explicit output contract, a terminal checklist/exit-gate the model must satisfy (the compaction-recovery doc's lesson: models honor an explicit end-of-section tick-list far better than scattered prose).
2. Add a short `.agents/workflows/handoff/README.md` if the sibling workflows carry one (match convention; else fold into the entry file).
3. Register `/handoff` in `.agents/workflows/index.md` and anywhere `/list-workflows` reads, with a one-line description. Bump the manifest version stamp if the convention requires it (verify).
4. Cross-link with the now-BUILT `/whatnext` (plan-review PR-001/PR-002): in `/handoff`, point its survey step at the SAME gather sources `/whatnext` defines (do not fork a divergent list), and state the distinction - `/whatnext` is the short actionable ordering, `/handoff` is the fuller narrative snapshot (facts + nuance). Add a one-line cross-reference in `whatnext.md` pointing to `/handoff` for the full cold-start snapshot. Both are prose runbooks, so this is a documentation cross-link, NOT code sharing.
5. Include, inside the workflow, a pointer to the golden-output example as a STRUCTURAL / shape reference only (its sections + the nuance layer), NOT a factual one - that file is a mid-session draft snapshot with now-stale specifics (D90-era release scope, unpushed-commit counts, `VERSION 1.2.1`). The generator copies its SHAPE, never its stale facts (plan-review PR-004).
6. Broaden the `.agents/prompts/` convention (OQ6) to recognize resume/handoff prompts alongside run-once/research prompts: update `.agents/prompts/README.md`, the `prompts-README.md` source template, and the `.agents/docs/README.md` cross-reference so `Kind: session-handoff` is a documented prompt kind that stages in `.agents/prompts/`.
7. Relocate the golden example from `.agents/plans/pending/20260717-1950-01-session-handoff-resume-here.md` to `.agents/prompts/` (`git mv`, normalize the name to the prompts convention), and update tracked references to its old path (including this IPD's pointer and any TODO/plans mentions).

## Deferred / out of scope (v1)

- An `aw handoff` CLI helper as the GENERATOR. Corrected reasoning (plan-review PR-007): this is not merely "deferred" - a CLI is fundamentally the WRONG tool for `/handoff`'s core job. The primary value is capturing EPHEMERAL SESSION/CONVERSATION context, which lives only in the LLM's working memory and is inaccessible to any Python process. A CLI could only scrape the filesystem - the LOW-value part - and can never produce the session-context body. At most, a future `aw handoff` could be a HELPER that dumps the on-disk facts for the LLM to fold in; it can never be the generator. So `/handoff` is irreducibly an LLM prose workflow, by nature, not just "v1 prose, code later."
- Auto-detection of "context is about to overflow / compaction imminent" to trigger `/handoff` automatically. Out of scope; `/handoff` is invoked deliberately.
- Encrypting or access-controlling the handoff. It is a tracked repo doc; sensitive context is handled by the "keep it out, add a pointer" rule, not by protecting the file.
- Multi-session merge / diffing of successive handoffs.

## Open questions (resolved at /plan-review unless noted)

1. Sets reconciliation: RESOLVED (done 2026-07-20 via IPD `20260717-2317-01`). TWO distinct Sets: `agent-continuity-workflows` (whatnext=1, research=2, handoff=3) and `research-prompt-pipeline` (the prompts pipeline). No action here.
2. Status the generated file is born with: RESOLVED - `draft` (a snapshot for a human to read/trust, not a plan to critique).
3. RUN the suite vs cite: RESOLVED (human) - do NOT run the suite as a ritual. `/handoff` is about transferring context, not closing out the project; it is fine to hand off a repo with failing/uncommitted/unpushed work. Capture the ACTUAL current state (e.g. "tests red mid-fix because X") as context. Run the suite only if it is cheap AND does not distract from the primary goal (an accurate session-context handoff); accuracy of the handoff is paramount, not a green checkmark.
4. Behavior when run with little/no live context: RESOLVED (human) - this is the opposite of an edge case. `/handoff` is INTENDED to run WITHIN a context-rich session; that ephemeral context is most of the value. Run cold, it can add little the reader could not get by reading the repo, and it must SAY SO rather than pad with a filesystem summary. (Contrast `/whatnext`, the on-disk surveyor.) Never fabricate session nuance.
5. Filename slug: RESOLVED - `session-handoff-<short-focus-or-'resume'>`, dated `YYYYMMDD-HHMM-NN-...`.
6. RESOLVED (human): the handoff document lives in `.agents/prompts/` - it IS a resume prompt for the next session. Consequences the executor must handle:
   - The generated file goes to `.agents/prompts/pending/YYYYMMDD-HHMM-NN-session-handoff-<slug>.md`, `Kind: session-handoff`, `Status: draft`. (When consumed/superseded it can move through the prompts lifecycle buckets like any staged prompt.)
   - BROADEN the `.agents/prompts/` convention (D91) so it explicitly covers resume/handoff prompts, not only "run-once/research prompts queued to run." Update `.agents/prompts/README.md` (and the `prompts-README.md` template + the `.agents/docs/README.md` cross-reference note) so a session-handoff is a recognized prompt kind. This keeps the dir's meaning honest rather than shoehorning a mismatch.
   - RELOCATE the golden example `20260717-1950-01-session-handoff-resume-here.md` from `.agents/plans/pending/` to `.agents/prompts/` (it is a handoff/resume prompt mis-filed as a plan). `git mv` it, normalize the name to the prompts convention, and update any references (this IPD, and any tracked mentions).
   - Note: the `.agents/prompts/pending/` file `20260717-1450-01-ses-...compacted.md` is a related session-recovery artifact already in prompts; the handoff convention should acknowledge that family.

## Dependencies / sequencing

- Independent enough to build alone, but specified to reuse `/whatnext` (Order 1) survey inputs; natural order is whatnext -> research -> handoff. Order numbers are advisory (D82).
- No dependency on the broker line (IPD 2/3/4) or the prompt-pipeline Set, except the soft P8 "reuse the survey" tie to `/whatnext`.
- 1.3.0-era (a new workflow/convention), consistent with the other continuity workflows.

## Validation plan

- The workflow is prose (irreducibly - it needs the LLM's session context; see Deferred), so validation is: (a) run `/handoff` in a real, context-rich session and confirm the SESSION-CONTEXT and NUANCE sections are substantive and dominate (not a filesystem re-summary) - this is the primary acceptance test; (b) confirm all required sections are present (or explicitly N/A); (c) confirm the output is written to the CHOSEN home (OQ6) with `Kind: session-handoff`, `Status: draft`, NOT into `.agents/plans/`; (d) confirm it made NO product-code changes and did not push; (e) confirm `/list-workflows` / the manifest lists `/handoff`; (f) `tests/test_dir_readmes.py` passes (the new `handoff/README.md` is required by its Category-2 check); (g) diff the generated doc against the golden example (`1950-01`) for STRUCTURAL parity only (shape, not stale facts). Full suite `python -m pytest -q` stays green (current baseline 293 passed, 1 skipped). No unit tests for the prose itself.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (added at /plan-review, PR-008; per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first; `git mv` the relocated golden example (Step 7) and commit both paths. When reporting tests/validation, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope (e.g. the `.agents/prompts/` convention broaden touches shared templates - keep it minimal). Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. On human approval, set `Status: approved` (+ the `Approval:` line), execute the ordered changes, run the validation, sync docs; commit path-scoped (no push).
2. Set the terminal `Status: executed` and `git mv` this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`. Plan files are named `YYYYMMDD-HHMM-NN-<slug>.md`.
