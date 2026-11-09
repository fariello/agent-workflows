# IPD: Add README, docs and reference document rewrites to the cutover docs patch

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 5.4 requires the records READMEs, the user docs, the `ipd_schema.py` help text, the two ipd-spec reference documents and the staged-prompt documents to describe the log and the commands instead of field syntax; C10a keeps that text off `main` until the cutover commit. This is the third of four parts that build the cumulative cutover documentation patch (split from `90iqr1` E-05, round 3, research `nj8zdp`). The `Kind` renames of E-05 went to `ngc2a2`.
- Scope: In a scratch worktree with the committed patch applied, rewrite the field-syntax passages of the five records READMEs, two docs, `ipd_schema.py` docstrings and help text, and every `qhay6a` F-03 `rewrite` row among the reference and `aw-prompt` documents; regenerate `.aw/system/cutover/metastore-docs.cutover.patch`. No live document changes.
- Scope-Paths: .aw/records/plans/pending/20261109-metastore-252-y1zihp-add-readme-docs-and-reference-document-rewrites-to-the-cutov.ipd.md, .aw/system/cutover/metastore-docs.cutover.patch
- Item-Dependencies: executed:9o83cr, executed:a49djh
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 252
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: y1zihp

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 90iqr1 (round 3, research nj8zdp guidance).

## Goal

Extend the cumulative cutover documentation patch so the READMEs, docs, schema help text and reference documents describe the log and the commands.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scratch worktree

- [ ] E-01 Create a scratch git worktree (`git worktree add --detach .aw/state/y1zihp/scratch HEAD`) and apply the committed cumulative patch in it (`git apply --index` of `.aw/system/cutover/metastore-docs.cutover.patch`, as last written by `a49djh`). If it does not apply, stop and report.
  - Depends on: none
  - Expected outcome: the scratch worktree shows the `qhay6a` and `a49djh` changes staged; the executing checkout is unchanged.
  - Execution state: pending

### Task group 2: rewrites (scratch worktree only; subsets of `90iqr1` E-05)

- [ ] E-02 In the scratch worktree, rewrite the field-syntax passages of the records READMEs: `.aw/records/plans/README.md`, `.aw/records/specs/README.md`, `.aw/records/backlog/README.md`, `.aw/records/releases/README.md` and `.aw/records/walkthroughs/README.md` (the walkthroughs README already carries `a49djh`'s command text; keep it), so they describe the log and the commands.
  - Depends on: E-01
  - Expected outcome: `rg -n '^- (Status|Readiness|Blocks-Release|From-Backlog):'` over the five READMEs finds only quoted legacy examples marked as such.
  - Execution state: pending

- [ ] E-03 In the scratch worktree, rewrite the field-syntax passages of `docs/artifact-lifecycles.md` and `docs/run-analytics.md`, and the section-schema docstrings and help text in `agent_workflows/ipd_schema.py`, so they describe the log and the commands.
  - Depends on: E-01
  - Expected outcome: no passage in the three files tells a reader to write a metadata bullet or a history line except as a quoted legacy example.
  - Execution state: pending

- [ ] E-04 In the scratch worktree, rewrite every `qhay6a` F-03 row marked `rewrite` among the two ipd-spec reference documents (the implemented `ipd-spec` and `ipd-structure-and-linting` specs) and the `aw-prompt` documents (the prompts README, its template under the shared templates directory, and the research-prompt workflow body): the staged-prompt comment becomes the single leading `aw-managed-prompt` comment of spec 4.1 and OQ-25. Leave the specs' own front matter and history alone (`m0001` migrates them).
  - Depends on: E-01
  - Expected outcome: each listed document marked `rewrite` describes the log, the commands and the `aw-managed-prompt` comment.
  - Execution state: pending

### Task group 3: package

- [ ] E-05 In the scratch worktree run `git add -A`, write `git diff --cached --binary HEAD` over the patch file in the executing checkout, remove the scratch worktree with `git worktree remove --force .aw/state/y1zihp/scratch`, and commit through `aw commit y1zihp -- <this plan> .aw/system/cutover/metastore-docs.cutover.patch`. Never `git add -A` in the executing checkout; never push.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the regenerated patch lists the earlier parts' files plus every file edited by E-02 to E-04; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The cumulative patch design and scratch-worktree location are defined in `qhay6a` OQ-01 and `90iqr1` OQ-01, OQ-03.
- User-facing prose (READMEs, docs) carries no em or en dashes (AGENTS.md execution contract).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `90iqr1` F-02 | Five READMEs (backlog, plans, releases, specs, walkthroughs) and two docs need rewriting. |
| F-02 | `90iqr1` E-01 at review | The `aw-prompt` documents measured were `docs/artifact-lifecycles.md`, the prompts README, its template and the research-prompt workflow body; the authoritative list is `qhay6a` F-03. |

## Proposed changes (ordered, validatable)

1. E-01: scratch worktree with the patch applied.
2. E-02 to E-04: READMEs; docs and `ipd_schema.py`; reference and prompt documents.
3. E-05: regenerate the patch and commit.

## Deferred / out of scope (with reason)

- The `Kind` to `plan_role`/`research_kind`/`prompt_kind` renames (the rest of `90iqr1` E-05) and the quickstarts.
  - Carrier: ngc2a2
- Applying the patch to live documents: cutover commit (C10a).
  - Carrier: cxxmyv

## Scope check

- Over-scope: none.
- Under-scope: none. The README, docs, `ipd_schema`, reference-document and prompt-document subsets of `90iqr1` E-05 map to E-02, E-03 and E-04; its `Kind` subset is in `ngc2a2`.

## Required tests / validation

- V-01 to V-05 below; the patch guard test is owned by `90iqr1`.

## Spec / documentation sync

No spec change; the documents change in `cxxmyv`'s cutover commit.

## Open questions

None open. Patch design questions are resolved in `90iqr1` and `qhay6a`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git apply --index` command and its exit status, and the scratch worktree's `git diff --cached --stat` listing the `qhay6a` and `a49djh` files.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the diff stat line for each of the five READMEs (plans, specs, backlog, releases, walkthroughs), and `rg -n '^- (Status|Readiness|Blocks-Release|From-Backlog):'` run on each README in the scratch worktree with every hit classified as a quoted legacy example.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste one diff hunk per file for `docs/artifact-lifecycles.md`, `docs/run-analytics.md` and `agent_workflows/ipd_schema.py`, showing command-based wording.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the diff hunks of each reference document and `aw-prompt` document that `qhay6a` F-03 marks `rewrite`, one per document, and `rg -n 'aw-prompt'` over those documents in the scratch worktree with each remaining hit classified.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-docs.cutover.patch` (earlier files plus each file from V-02 to V-04), `git worktree list` showing the scratch worktree removed, and the `aw commit` output naming the commit hash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `a49djh` is `executed` and this plan is `approved`. Documents are edited ONLY in the scratch worktree; the executing checkout changes only by this plan and the patch file.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Honesty rule: paste the ACTUAL output of every command named above; never claim a result you did not run.

Commits: commit only through `aw commit y1zihp -- <paths>`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
