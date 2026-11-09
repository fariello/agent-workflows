# IPD: Inventory the docs surface and start the cutover docs patch with the managed block

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 5.4 requires every document, template, workflow and managed-block text that describes metadata FIELD SYNTAX to describe COMMANDS instead, and C10a forbids that text from reaching `main` before the cutover commit. Plan `90iqr1` owned the whole documentation patch in one pass (10 E-items); research `nj8zdp` guidance asks for smaller plans, so the patch is now built in four parts (this plan, `a49djh`, `y1zihp`, `ngc2a2`) and finished by `90iqr1`. This first part takes the inventory and the managed-block rewrite.
- Scope: Inventory the documentation surface with one disposition per file; in a scratch worktree only, rewrite the `engine.agents_pointer_prose` managed block and the repo-local `AGENTS.md` text; write the result as the first version of the cumulative patch `.aw/system/cutover/metastore-docs.cutover.patch`. No live document changes.
- Scope-Paths: .aw/records/plans/pending/20261109-metastore-250-qhay6a-inventory-the-docs-surface-and-start-the-cutover-docs-patch.ipd.md, .aw/system/cutover/metastore-docs.cutover.patch
- Item-Dependencies: executed:9o83cr
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 250
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: qhay6a

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 90iqr1 (round 3, research nj8zdp guidance).

## Goal

Record which documentation files the cutover must rewrite, and start the cumulative cutover documentation patch with the managed-block and `AGENTS.md` rewrite, so the later parts (`a49djh`, `y1zihp`, `ngc2a2`) extend one patch and `90iqr1` guards it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: inventory

- [ ] E-01 (was `90iqr1` E-01, verbatim.) Re-measure the documentation surface at execution time: run `rg -l -e '^- (Status|Readiness|Approval|From-Backlog|From-Spec|Blocks-Release|Coverage|Work-Kind|Kind|Release-Exempt-Kind|Release-Exempt-Ref|Gate-Kind|Gate-Ref|Scope-Exceeded|Review-Depth|Pipeline):' -e '## Workflow history' -e '`- (Status|Readiness|From-Backlog|Blocks-Release|Coverage|Kind|From-Spec)' -e 'aw-prompt' -e '--kind' .aw/system/workflows docs .aw/records/*/README.md AGENTS.md README.md CONTRIBUTING.md agent_workflows/engine.py agent_workflows/ipd_schema.py agent_workflows/cli.py .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` (39 files at review before the added roots; the bar is a disposition for every listed file, not that count). The two specs are the "ipd-spec reference documents" that spec 5.4 names; `aw-prompt` covers the staged-prompt comment form (AC-40); `--kind` and `cli.py` cover the `Kind` to `plan_role`/`research_kind`/`prompt_kind` help-text renames of spec 5.4. A spec is a record: it gets a `rewrite` disposition only where its text instructs agents to write field syntax; its own front matter and history are migrated by `m0001`, not by this patch. Record the file list with one disposition per file (rewrite, unchanged because the text quotes legacy history, or out of scope with reason) in this plan's `## Findings` as F-03, and name for each `rewrite` row which part rewrites it (`qhay6a` E-02, `a49djh`, `y1zihp`, or `ngc2a2`).
  - Depends on: none
  - Expected outcome: a complete per-file disposition table; no file in the `rg` output lacks a disposition or an owning part.
  - Execution state: pending

### Task group 2: managed block

- [ ] E-02 (was `90iqr1` E-02.) Create a scratch git worktree from the executing checkout's HEAD inside the gitignored state root (`git worktree add --detach .aw/state/qhay6a/scratch HEAD`) and, in it only, rewrite the managed block produced by `engine.agents_pointer_prose` and the repo-local `AGENTS.md` text below the managed block so that attestations, `Status`, `From-Backlog`, `From-Spec`, `Blocks-Release`, `Work-Kind`, `Release-Exempt-*` and `Coverage` are described as the commands that write them (aw ipd set, aw specs set, aw backlog set, aw set, aw show <id6> --history, aw check meta, aw meta repair), and so that the close-legitimacy rule, the `aw index plans [--check]` sentence handed by `9o83cr`, and the executed-plan rule name the post-cutover forms (spec 5.2 step 4a amendment). Regenerate the AGENTS.md managed block from the edited generator with the regen tool (`python3 tools/regen_agents_block.py`) inside the scratch worktree, so the patch carries the matching managed-sections section hashes and the live section-records test passes on the patched tree.
  - Depends on: E-01
  - Expected outcome: in the scratch worktree, `rg -n '^- (Status|Readiness|Blocks-Release|From-Backlog):' AGENTS.md` returns only quoted legacy examples marked as such.
  - Execution state: pending

### Task group 3: package

- [ ] E-03 From the scratch worktree, run `git add -A` (scratch only, so new files are included) and write `git diff --cached --binary HEAD` to `.aw/system/cutover/metastore-docs.cutover.patch` in the executing checkout (this creates the cumulative patch that `a49djh`, `y1zihp` and `ngc2a2` extend); remove the scratch worktree with `git worktree remove --force .aw/state/qhay6a/scratch`; commit through `aw commit qhay6a -- <this plan> .aw/system/cutover/metastore-docs.cutover.patch`. Never `git add -A` in the executing checkout; never push.
  - Depends on: E-02
  - Expected outcome: the patch exists and lists only the managed-block files; the executing checkout's `git status --short` shows only this plan and the patch before the commit; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Field-syntax documentation lives in workflow bodies and in the managed block generated by `engine.agents_pointer_prose`; the installer writes that block into target repositories, so its text is a published contract.
- The runner merges each execute item's isolated worktree into `main`, so editing live documents would land them on `main` early; a tracked patch file keeps C10a (see `90iqr1` OQ-01).
- The scratch worktree lives in the gitignored `.aw/state/<id6>/` of the executing checkout (see `90iqr1` OQ-03); `git diff HEAD` alone omits new untracked files, so the capture uses `git add -A` inside the scratch worktree.
- Cite code by SYMBOL, not line number.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `90iqr1` F-01 to F-05 | Measured surface and handed-in items (managed block from `9o83cr`, two commands from `xexn45`). |
| F-02 | Round-3 split 2026-11-09 | The patch is cumulative: each later part applies the committed patch in its scratch worktree before editing, then rewrites the same file. |
| F-03 | (written by E-01) | Per-file disposition table, with the owning part for each `rewrite` row. `90iqr1` E-09 copies the `rewrite` list from this table. |

## Proposed changes (ordered, validatable)

1. E-01: inventory with dispositions and owning parts.
2. E-02: managed block and AGENTS.md in a scratch worktree.
3. E-03: write the cumulative patch and commit.

## Deferred / out of scope (with reason)

- Review workflows, recorder and walkthrough command docs, templates: second part.
  - Carrier: a49djh
- READMEs, docs, `ipd_schema.py` text and reference documents: third part.
  - Carrier: y1zihp
- `Kind` renames and quickstarts: fourth part.
  - Carrier: ngc2a2
- Patch guard test, sanitizer and patched-tree test run: finishing part.
  - Carrier: 90iqr1

## Scope check

- Over-scope: none. No live document is edited.
- Under-scope: none. Spec 5.4 managed-block and AGENTS.md bullets map to E-02; the inventory maps to E-01.

## Required tests / validation

- V-01 to V-03 below; the patch guard test is owned by `90iqr1`.

## Spec / documentation sync

No spec change. This plan prepares part of the documentation that spec `4sd62s` section 5.4 requires; the documents change in `cxxmyv`'s cutover commit.

## Open questions

### OQ-01: Why a cumulative patch rather than one patch per part?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Several parts edit the same file (`engine.py` in E-02 here and in `ngc2a2`; the review workflows in `a49djh` twice). Separate fragments would conflict; one cumulative patch, applied and regenerated by each part, keeps the single-file design that `cxxmyv` applies. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `rg -l` command and its full file list, and the F-03 disposition table with one row per listed file and an owning part for each `rewrite` row; a listed file with no row is a failure.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n '^- (Status|Readiness|Blocks-Release|From-Backlog):' AGENTS.md` run in the scratch worktree (only quoted legacy examples), the `git diff` hunk of `engine.agents_pointer_prose` showing the command-based wording and the reworded `aw index plans` sentence, and `python3 -m pytest -o addopts="" tests/test_agents_section_records.py` in the scratch worktree after the regen tool, showing `test_live_agents_md_section_records_are_current` PASSED.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-docs.cutover.patch` (file list: `agent_workflows/engine.py`, `AGENTS.md`, `.aw/system/managed-sections.json`), `git worktree list` showing the scratch worktree removed, and the `aw commit` output naming the commit hash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `9o83cr` is `executed` and this plan is `approved`. The executor edits documents ONLY in a scratch worktree under `.aw/state/qhay6a/`; the executing checkout changes only by this plan and the patch file.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Honesty rule: paste the ACTUAL output of every command named above; never claim a result you did not run.

Commits: commit only through `aw commit qhay6a -- <paths>`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
