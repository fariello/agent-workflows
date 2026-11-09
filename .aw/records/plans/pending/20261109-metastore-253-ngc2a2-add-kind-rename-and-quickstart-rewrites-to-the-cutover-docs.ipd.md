# IPD: Add Kind rename and quickstart rewrites to the cutover docs patch

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 5.4 (last bullet) renames `Kind` (plan role), research `kind` and prompt `Kind` to `plan_role`, `research_kind` and `prompt_kind` in documents and help text, and spec 4.1 has the installer create two quickstarts. C10a keeps both off `main` until the cutover commit. This is the fourth of four parts that build the cumulative cutover documentation patch (split from `90iqr1` E-05 `Kind` subset and E-06, round 3, research `nj8zdp`).
- Scope: In a scratch worktree with the committed patch applied, apply the `Kind` renames in documents and `cli.py` help strings, and write the two quickstarts plus their installer template text in `engine.py`; regenerate `.aw/system/cutover/metastore-docs.cutover.patch`. No live document changes; no CLI option is renamed.
- Scope-Paths: .aw/records/plans/pending/20261109-metastore-253-ngc2a2-add-kind-rename-and-quickstart-rewrites-to-the-cutover-docs.ipd.md, .aw/system/cutover/metastore-docs.cutover.patch
- Item-Dependencies: executed:9o83cr, executed:y1zihp
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 253
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ngc2a2

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 90iqr1 (round 3, research nj8zdp guidance).

## Goal

Finish the content of the cumulative cutover documentation patch: the `Kind` renames and the two quickstarts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scratch worktree

- [ ] E-01 Create a scratch git worktree (`git worktree add --detach .aw/state/ngc2a2/scratch HEAD`) and apply the committed cumulative patch in it (`git apply --index` of `.aw/system/cutover/metastore-docs.cutover.patch`, as last written by `y1zihp`). If it does not apply, stop and report.
  - Depends on: none
  - Expected outcome: the scratch worktree shows the three earlier parts' changes staged; the executing checkout is unchanged.
  - Execution state: pending

### Task group 2: rewrites (scratch worktree only)

- [ ] E-02 (the `Kind` subset of `90iqr1` E-05.) In the scratch worktree, rename `Kind` (plan role), research `kind` and prompt `Kind` to `plan_role`, `research_kind` and `prompt_kind` in every document of the `qhay6a` F-03 table (spec 5.4 last bullet). Documents only; `cli.py` is E-03.
  - Depends on: E-01
  - Expected outcome: `rg -n -w 'Kind' --type md` in the scratch worktree finds only quoted legacy examples and `Work-Kind`/`Gate-Kind` spellings that 4.5c keeps as log names `work_kind`/`gate_kind` described as such.
  - Execution state: pending

- [ ] E-03 (the `cli.py` subset of `90iqr1` E-05.) In the scratch worktree, change the `agent_workflows/cli.py` help strings so the value of `aw ipd scaffold --kind` is described as the plan role and `aw research mv --kind` as the research kind. Renaming an OPTION is a CLI contract change that this documentation patch does not make; any option rename is Order 13's code change (Carrier `cxxmyv`).
  - Depends on: E-01
  - Expected outcome: only help strings change in `cli.py`; no option name changes.
  - Execution state: pending

- [ ] E-04 (was `90iqr1` E-06.) In the scratch worktree, write the two quickstarts the installer creates (spec 4.1): `.aw/AGENT_QUICKSTART.md` (for agents: where metadata lives, `aw show`, never hand-edit logs or front matter, which commands write which field) and `.aw/QUICKSTART.md` (for people), and the installer template text in `agent_workflows/engine.py` that emits them. Both are new files; E-05's `git add -A` captures them.
  - Depends on: E-01
  - Expected outcome: both files exist in the scratch worktree and are referenced by the banner text of spec 4.1.
  - Execution state: pending

### Task group 3: package

- [ ] E-05 In the scratch worktree run `git add -A`, write `git diff --cached --binary HEAD` over the patch file in the executing checkout, remove the scratch worktree with `git worktree remove --force .aw/state/ngc2a2/scratch`, and commit through `aw commit ngc2a2 -- <this plan> .aw/system/cutover/metastore-docs.cutover.patch`. Never `git add -A` in the executing checkout; never push.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the regenerated patch lists both quickstarts as new files plus every earlier file; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The cumulative patch design and scratch-worktree location are defined in `qhay6a` OQ-01 and `90iqr1` OQ-01, OQ-03. Measured at review of `90iqr1`: `git diff HEAD` alone omits a new untracked file, hence `git add -A` in the scratch worktree.
- User-facing prose (READMEs, docs, quickstarts) carries no em or en dashes.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `90iqr1` E-05, E-06 | The `Kind` renames and quickstarts are the last content of the patch; `90iqr1` then guards and checks it. |

## Proposed changes (ordered, validatable)

1. E-01: scratch worktree with the patch applied.
2. E-02 to E-04: `Kind` renames in documents, `cli.py` help strings, quickstarts.
3. E-05: regenerate the patch and commit.

## Deferred / out of scope (with reason)

- Renaming any CLI option that carries the legacy `Kind` name: code change in the cutover commit.
  - Carrier: cxxmyv
- Patch guard test, sanitizer and patched-tree test run.
  - Carrier: 90iqr1

## Scope check

- Over-scope: none.
- Under-scope: none. `90iqr1` E-05's `Kind` subset maps to E-02 and E-03; E-06 maps to E-04.

## Required tests / validation

- V-01 to V-05 below; the patch guard test is owned by `90iqr1`.

## Spec / documentation sync

No spec change; the documents change in `cxxmyv`'s cutover commit.

## Open questions

None open.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git apply --index` command and its exit status, and the scratch worktree's `git diff --cached --stat`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n -w 'Kind' --type md` in the scratch worktree with each hit classified (quoted legacy, `Work-Kind`, `Gate-Kind`), and the diff stat of the documents changed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `cli.py` diff hunks for the `aw ipd scaffold --kind` and `aw research mv --kind` help strings, and `git diff HEAD -- agent_workflows/cli.py | rg '^[-+].*add_argument\("--'` in the scratch worktree showing no changed option name.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the content of `.aw/AGENT_QUICKSTART.md` and `.aw/QUICKSTART.md` from the scratch worktree and the `engine.py` diff hunk that emits them.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-docs.cutover.patch` with both quickstarts shown as new and `.aw/system/managed-sections.json` included, `git worktree list` showing the scratch worktree removed, and the `aw commit` output naming the commit hash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `y1zihp` is `executed` and this plan is `approved`. Documents are edited ONLY in the scratch worktree; the executing checkout changes only by this plan and the patch file.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Honesty rule: paste the ACTUAL output of every command named above; never claim a result you did not run.

Commits: commit only through `aw commit ngc2a2 -- <paths>`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
