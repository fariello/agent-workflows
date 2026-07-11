# IPD: Plan readiness-status vocabulary, workflow-history provenance, and commit-not-push discipline

- Date: 2026-07-11
- Concern: plan/prompt lifecycle - capturing READINESS within the pending phase, recording which
  workflows have touched an artifact, and making the commit history show a plan moving through the
  pipeline. Plus the documentation reconciliation those changes require.
- Scope: the IPD template + the plan-mutating workflow bodies (`assess`, `assess-all`, `plan-review`,
  `spec`, `migrate`, `incident`) + a new `aw plans` status board + docs (lifecycle prose, AGENTS.md,
  `.agents/plans/README.md`, DECISIONS). Does NOT change disposition directories (the five-state dir
  set from D45/D47 is unchanged) or the filename convention (D48/D50 unchanged).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-11 drafted (its_direct/pt3-claude-opus-4.8-1m-us): initial draft from an interactive
  design session; status vocabulary + visibility + provenance + commit discipline decided with the
  maintainer.
- 2026-07-11 promoted to `to-review` (its_direct/pt3-claude-opus-4.8-1m-us): approach committed;
  OQ1 resolved (born-`to-review`, `draft` opt-in); remaining open questions are refinement-level and
  left for `/plan-review` to interrogate.
- 2026-07-11 folded in audience/teachability consideration (its_direct/pt3-claude-opus-4.8-1m-us):
  most users are not discussion-first; added change #11 (teach draft-vs-to-review; `/plan-review`
  names an unready plan) + background rationale.

## Goal

Give plans an honest, at-a-glance-able notion of READINESS (stub -> ready-to-execute) that is
separate from DISPOSITION (which terminal bucket), record on each artifact WHICH workflows have run
against it, and make each plan-mutating workflow COMMIT (never push) at natural points so the git
history shows a plan progressing (notably a before/after snapshot around `/plan-review`). This
serves provenance and "knowing what happened" - core to a framework whose value is honest,
reproducible process (P2/P4).

## Background / the two axes

The current lifecycle collapses two orthogonal things into directories:
- **Disposition** (terminal outcome): `pending -> executed / superseded / not-executed`, plus
  standing `reusable`. This is the directory set (D45/D47) and stays as-is.
- **Readiness** (maturity WITHIN pending): stub -> fleshed out -> reviewed/hardened -> ready to
  execute. This has NO home today; everything pre-execution is just "pending", so a one-line stub
  and an approved, hardened IPD look identical from the tree.

This IPD adds readiness as an enumerated front-matter `Status:` field (source of truth), keeps
directories = disposition, and does NOT create readiness subfolders (which would cause a
combinatorial dir explosion and rename-churn on every transition).

### Audience / teachability consideration (maintainer, 2026-07-11)

The `draft` vs `to-review` distinction assumes the author can judge "is my approach committed?"
That judgment is NOT universal. The maintainer works discussion-first (settle understanding in
dialogue, THEN write an IPD), so ~90% of the maintainer's IPDs are genuinely review-ready at
creation. But people the maintainer teaches are often surprised by the up-front discussion; the more
common instinct is prompt -> generate -> run -> iterate, where the thinking happens IN the artifact
and execution, not before. For that (likely median) user, a first-draft IPD is usually NOT
approach-committed - it is closer to `draft` - but they will not self-label it so, and the
born-`to-review` default will let them run `/plan-review` on a still-forming plan and hit the exact
"this isn't decided yet" churn.

Design consequence (do NOT reverse the born-`to-review` default - that would tax the 90%): instead,
the framework must TEACH the distinction (P3 self-documenting) and let TOOLING supply the judgment
the expert user has internalized, rather than assuming accurate self-labeling. Two levers: (a)
`/getting-started`, `/spec` (the fuzzy-idea front door), and the IPD template must define and teach
`draft` vs `to-review` and point uncertain users at `/spec` FIRST; (b) `/plan-review` should
recognize an approach-not-committed plan and say so kindly ("this reads as still-`draft`; here is
what to decide before review is useful") instead of only emitting findings against a moving target.
This converts the maintainer's tacit discussion-first skill into explicit, transferable framework
guidance - which is the whole point of a framework. Captured as change #11.

## Decisions taken (maintainer, 2026-07-11)

1. **Readiness = an enumerated `Status:` field in the IPD front-matter (source of truth);
   directories remain disposition-only.** Purely additive; no directory renames (non-disruptive to
   the ~146 current cloners). Formalizes the existing free-text `Status:` line into a closed set.
2. **Status vocabulary (lowercase-kebab, consistent with the slug/dir conventions):**
   - Pre-terminal (file in `pending/`): `draft` (stub or partial; do NOT review/execute - absorbs
     "stub") -> `to-review` (author says complete; ready for `/plan-review` or human review) ->
     `reviewed` (`/plan-review` done + revisions applied; awaiting human sign-off) -> `approved`
     (human signed off; ready to execute).
   - Terminal (file in the matching dir; `Status:` MIRRORS the dir): `executed`, `superseded`,
     `not-executed`.
   - Standing: `reusable`.
    - Longest path: `draft -> to-review -> reviewed -> approved -> executed`. Terminal `superseded`/
      `not-executed` are reachable from ANY pre-terminal state (the "abandon at any step but keep"
      case; retire with the `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` header +
      `git mv`).
    - **`draft` is a SIDE-ENTRANCE, not the front door (resolves OQ1; maintainer 2026-07-11):** a
      normally-drafted IPD is BORN `to-review` (the ~90% case - thorough proposals from `/assess`,
      `/spec`, `/migrate`, `/incident`, or a careful agent draft are review-ready at creation, so we
      do NOT tax them with a mandatory `draft` step). `draft` is used ONLY when creation is
      explicitly a stub / "capture this, work on it later" (the ~10% case). So `draft -> to-review`
      is an OPTIONAL promotion the author makes, not a gate everything passes through. Cleaner
      provenance too: no empty `draft->to-review` commit for the common case.
    - **`to-review` gates on APPROACH-COMMITTED, not all-questions-resolved (maintainer
      2026-07-11):** a `to-review` plan MAY (and usually will) carry open questions. `to-review`
      means the APPROACH is decided and the proposed changes are concrete enough to critique - it
      does NOT mean every question is answered. `/plan-review` is an INTERROGATION that is expected
      to SURFACE, REFRAME, and add open questions (and apply fixes), not merely gate a settled plan.
      Only APPROACH-DEFINING questions ("is this even the right shape?") must be resolved before
      `to-review`; refinement/detail/edge-case questions are review's job. Litmus: "could a reviewer
      not in the design conversation give useful, non-speculative findings?" If yes -> `to-review`.
3. **"Approved after edits" is NOT a separate status.** Operationally identical to `approved`
   (ready to execute); the "with revisions" fact is provenance, captured by the plan-review entry in
   the Workflow-history section (and optionally a one-line `Approval:` note), not a status value.
4. **Visibility = front-matter is truth + a first-class `aw plans` board.** No status token in the
   filename (avoids re-churning the D48/D50 convention and a two-sources-of-truth divergence where
   `ls` could lie). `aw plans` renders a grouped, counted, colored board (UPPERCASING the states for
   scannability); an optional generated `.agents/plans/STATUS.md` index covers the no-CLI / GitHub-web
   case. `ls` never lies because status is not in the name.
5. **Workflow-history provenance on the artifact.** Each mutating workflow appends a dated line to a
   `## Workflow history` section in the IPD (and prompt, where applicable): date, workflow,
   agent/model, and a one-line outcome (e.g. plan-review verdict + finding IDs). The `Status:` field
   shows the CURRENT state; Workflow history shows the PATH taken.
6. **Commit-not-push discipline across the plan-mutating pipeline** (`assess`, `assess-all`,
   `plan-review`, `spec`, `migrate`, `incident`): each commits its output at natural points and NEVER
   pushes. `/plan-review` specifically does a TWO-COMMIT before/after: on start, if the target IPD
   has uncommitted changes, commit it as a pre-review snapshot; then apply revisions and commit the
   hardened result - so history shows the plan before and after review.

## Project conventions discovered (Step 0)

- IPD template: `.agents/workflows/assess/templates/ipd.md`; header currently
  `- Status: PENDING (awaiting human approval; not executed)` (free text).
- `assess` ALREADY commits (assess.md step 7: "Commit the IPD and the run record ... Do not commit
  unrelated changes ... keep local only if the user asks"; do-not-push implied). `plan-review` does
  NOT commit today (it revises in place; committing is left ad hoc) - this is the gap behind the
  before/after request. `spec`, `migrate`, `incident`, `assess-all` have no commit guidance.
- Disposition dirs + retirement convention: D45/D47. Filename convention: D48/D50. Both unchanged.
- `aw` CLI: `agent_workflows/cli.py` (verbs install/setup/uninstall/list/status). A `plans` verb is
  net-new. Config/board are stdlib-only, zero runtime deps (D46).
- Latest DECISIONS entry: D51 (this IPD would add D52).
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

### 1. Formalize the `Status:` vocabulary in the IPD template
Update `templates/ipd.md`: replace the free-text status line with the enumerated set + a short
legend comment listing the allowed values and the longest path. Default for a NEW assess IPD:
`to-review` (assess produces a complete proposal) - but a stub created by hand/agent starts `draft`.
Add the `## Workflow history` section and an optional `Approval:` line to the template.

### 2. Add the `## Workflow history` provenance section + appender convention
Define the one-line format: `- YYYY-MM-DD /<workflow> (<agent/model>): <one-line outcome>`. Document
that every mutating workflow APPENDS (never rewrites) a line. Applies to IPDs and to prompts that go
through the pipeline.

### 3. Wire the status transitions + Workflow-history + commit contract into each workflow body
- `assess` / `assess-all`: set `Status: to-review` on the IPD it writes; append a Workflow-history
  line; keep its existing commit (confirm NEVER push). (assess-all writes one consolidated IPD.)
- `plan-review`: TWO-COMMIT before/after (change #6 detail below); set `Status: reviewed` on the
  hardened plan (it does not self-approve); append a Workflow-history line with the verdict + finding
  IDs; commit, never push.
- `spec`: commit the spec artifact (never push); append a Workflow-history line.
- `migrate` / `incident`: they emit IPDs; set `Status: to-review` (or `draft` if explicitly a stub);
  append a Workflow-history line; commit, never push.
- Human approval (outside a workflow) sets `Status: approved` (+ `Approval:` note). Execution sets
  the terminal `Status:` and `git mv`s to the matching dir. Document who/what performs each
  transition.

### 4. `/plan-review` two-commit before/after (the provenance centerpiece)
Add to plan-review's controlling file: at START, if the target IPD has uncommitted changes, commit
it verbatim as `plan: pre-review snapshot of <slug>` (staged + committed, never pushed). Then do the
review + in-place revisions as today, set `Status: reviewed`, append the Workflow-history line, and
commit as `plan-review: harden <slug> (revisions applied)`. If the plan was already committed and
unchanged at start, the pre-review snapshot is skipped (nothing to snapshot) - note this so it is not
a bug. Never push (matches the framework's stage/commit-not-push, no-remote-changes posture, P10).

### 5. New `aw plans` status board (visibility)
Add an `aw plans` CLI verb: scan `.agents/plans/*` (and optionally `.agents/prompts/*`), read each
IPD's `Status:` front-matter, and print a board grouped by disposition dir and readiness, with
counts and color (UPPERCASED state labels; honors NO_COLOR/isatty via the existing `term.py`).
Flags: filters like `--pending`, `--status <s>`, and `--write-index` to (re)generate
`.agents/plans/STATUS.md`. Reads front-matter only (single source of truth); never renames. Stdlib
only. (Design detail in Open Questions.)

### 6. Backward compatibility for existing free-text `Status:`
Define the mapping so old artifacts remain valid, not errors: `PENDING (...)` -> treated as
`to-review` (or `draft` if clearly a stub) for board grouping; `EXECUTED ...` -> `executed`; etc.
Unrecognized/legacy status strings are shown under a `legacy/unknown` group by the board and are NOT
flagged as failures. Do NOT rewrite historical executed IPDs' status lines (P4); only new/edited
plans adopt the enum.

### 7. Optional gating (verify / release-review / normalizer)
Decide (Open Question) whether to ADD machine checks: e.g. `verify`/a test asserts a terminal
`Status:` matches its directory, and release-review warns on an `approved`-but-unexecuted plan
(release-review already warns on pending plans generally). Keep any gate advisory-first to avoid
breaking downstream repos with legacy status text.

### 8. Documentation reconciliation (the doc-update you asked for)
Update every forward-facing site that describes the lifecycle to include the readiness statuses,
the Workflow-history convention, and the commit-not-push/pipeline-provenance behavior:
`.agents/workflows/assess/assess.md` (Step 0 lifecycle), `assess/templates/ipd.md`,
`setup-repo/setup-repo.md` (lifecycle contract it writes into targets), `index.md`, this repo's
`AGENTS.md` AGENT-PLANS block, `.agents/plans/README.md` (the generated overview + its template
`templates/plans-README.md`), README/ARCHITECTURE where the lifecycle/`aw` verbs are described, and
CONTRIBUTING. Keep it single-source (P8): the canonical enum lives in one place (the template +
DECISIONS) and others reference it.

### 9. DECISIONS D52
Record the readiness-status vocabulary, the metadata-not-filename visibility decision (+ why:
divergence risk / convention stability), the born-`to-review`/`draft`-opt-in default (+ the
audience/teachability rationale), the "`to-review` gates on approach-committed, not
all-questions-resolved" semantics, the Workflow-history convention, the commit-not-push +
plan-review two-commit contract, the `aw plans` board, the backward-compat mapping, and the
`/plan-review`-names-an-unready-plan behavior (change #11).

### 10. Tests
- Template/vocabulary: a test (or `verify` check) that the enum set is documented consistently and
  that a terminal status matches its dir on this repo's own plans (drift-guard, like the filename
  one).
- `aw plans`: board groups by disposition + readiness, counts correct, NO_COLOR plain output,
  legacy/unknown status handled, `--write-index` produces `STATUS.md`; reads front-matter only,
  renames nothing.
- Backward-compat: an old free-text `PENDING (...)` / `EXECUTED ...` artifact is grouped correctly
  and not errored.
- Full suite green.

### 11. Teach the `draft` vs `to-review` judgment; `/plan-review` names an unready plan (audience)
Per the audience/teachability consideration above - the framework must not assume every author can
judge "is my approach committed?" (the maintainer's discussion-first habit is tacit skill; the
median prompt->generate->iterate user's first draft is usually NOT approach-committed). Two parts:
- **Teach the distinction (P3):** `/getting-started`, `/spec` (the fuzzy-idea front door), and the
  IPD template define `draft` vs `to-review` in plain language, with the litmus ("could a reviewer
  not in your head give useful findings?") and a pointer: if unsure your approach is settled, run
  `/spec` FIRST. This is prose in the existing docs (folds into change #8's doc set), not new
  machinery.
- **`/plan-review` recognizes an approach-not-committed plan and says so KINDLY:** when the target
  reads as still-forming (approach undecided, changes too vague to critique, or `Status: draft`),
  `/plan-review` should lead with "this reads as still a draft - here is what to decide before
  review is useful" and list the approach-level gaps, rather than only emitting findings against a
  moving target. It still proceeds if asked, but names the state first. This converts the expert's
  tacit judgment into a tool-supported, teachable one. (Prose change to
  `plan-review/plan-review.md`; no code.)
Do NOT reverse the born-`to-review` default (decision 2) - that would tax the ~90% who are genuinely
review-ready at creation.

## Deferred / out of scope

- Changing disposition directories or the filename convention (D45/D47/D48/D50) - unchanged.
- A status token in the filename (rejected: divergence risk + convention churn; see decision 4).
- Auto-transitioning status without a workflow/human action (status changes are made by the
  workflow that performs the step or by the human approver; no daemon).
- Pushing - never; commit-only (P10).

## Scope check (P6 / P7)

Additive and non-disruptive: no dir renames, no filename change, legacy status text stays valid.
The new surface is one CLI verb (`aw plans`) + front-matter conventions + workflow-prose additions.
Directories still carry disposition (one axis); status carries readiness (the other) - no
combinatorial folder explosion. General-case: every repo benefits; nothing personal is hardcoded.

## Required tests / validation

Automated per change #10; full `python3 -m unittest discover -s tests -t .` green. Manual: create a
`draft` stub, flesh to `to-review`, run `/plan-review` and confirm TWO commits (pre-review snapshot +
hardened) and `Status: reviewed` + a Workflow-history line; approve -> `approved`; execute ->
`executed` + `git mv`; run `aw plans` and confirm the board reflects each state; confirm nothing was
pushed; confirm a legacy free-text IPD still groups sanely.

## Spec / documentation sync

This IPD includes the doc reconciliation (change #8) + DECISIONS D52 (change #9). No workflow
BEHAVIOR changes beyond the added commit points and metadata; no code-execution behavior changes.

## Open questions

1. **IPD default status:** should `/assess`, `/spec`, `/migrate`, `/incident` set the IPD they emit
   to `to-review` (proposed - they produce a complete proposal), or `draft` (let the human bump it to
   `to-review` when ready)? Hand-created stubs start `draft` regardless.
2. **Gating strictness (change #7):** advisory-only (board + warnings) for v1, or add a hard
   `verify`/test gate ("terminal status must match dir"; "do not execute a non-`approved` plan")?
   Leaning advisory-first to protect downstream repos with legacy status text.
3. **`aw plans` scope:** plans only, or plans + prompts by default? And is `STATUS.md` generated
   on-demand (`--write-index`) only, or refreshed automatically by `aw install` (more moving parts)?
4. **Prompts:** prompts are more free-form than IPDs; do they get the FULL status enum + Workflow
   history, or a lighter subset (e.g. just Workflow history, no readiness enum)?
5. **`assess-all`:** it writes one consolidated IPD; confirm the single-IPD status/history model fits
   (vs. per-concern sub-entries).

## Approval and execution gate

This IPD is a proposal (currently `draft`; not yet `to-review`). It MUST be fleshed out (open
questions resolved), moved to `to-review`, optionally `/plan-review`ed to `reviewed`, and
human-`approved` before execution. It is NOT auto-executed. On approval: implement changes 1-10, run
validation, commit (never push), then set `Status: executed` and `git mv` to
`.agents/plans/executed/`. This plan will itself be the first artifact to exercise the new
commit-not-push + Workflow-history + status-transition conventions (dogfooding).
