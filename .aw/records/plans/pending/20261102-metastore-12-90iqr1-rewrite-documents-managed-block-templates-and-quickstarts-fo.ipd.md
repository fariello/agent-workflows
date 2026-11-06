# IPD: Rewrite documents, managed block, templates and quickstarts for the log format

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` section 5.4 requires every document, template, workflow and managed-block text that describes metadata FIELD SYNTAX (`- Status:`, `- Readiness:`, `- From-Backlog:`, `- Blocks-Release:`, `- Coverage:`, `- Kind:`, `## Workflow history`) to describe COMMANDS instead, and C10a forbids that text from reaching `main` before the cutover commit, because on a pre-cutover `main` it would describe a format that does not exist yet. Measured 2026-11-02: 22 workflow files under `.aw/system/workflows/` contain bullet-field or `## Workflow history` text, plus `docs/artifact-lifecycles.md`, `docs/run-analytics.md`, 5 records READMEs and the `engine.py` managed block (`engine.agents_pointer_prose`). Two commands handed to this plan by `xexn45` (a review-round recorder and `aw walkthrough new`) and the managed-block rewording handed by `9o83cr` also need documentation.
- Scope: Prepare, review and commit the complete post-cutover documentation change as ONE patch file owned by this plan; do not apply it to the live documents. Order 13 (`cxxmyv`) applies the patch inside the cutover commit.
- Scope-Paths: .aw/records/plans/pending/20261102-metastore-12-90iqr1-rewrite-documents-managed-block-templates-and-quickstarts-fo.ipd.md, .aw/system/cutover/metastore-docs.cutover.patch, tests/test_metastore_cutover_patch.py
- Item-Dependencies: executed:9o83cr
- Status: reviewed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 12
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 90iqr1
- Readiness: go-pending-approval
- Review-Depth: standard

## Workflow history
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED; review record .aw/records/reviews/20261102-metastore-12-90iqr1-rewrite-documents-managed-block-templates-and-quickstarts-fo.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Produce a reviewed, applicable patch that rewrites every document, template, workflow, README and managed-block text for the post-cutover command-based metadata model, so that Order 13 can land it in the same commit as the format change and `main` never describes a format it does not have (C10a).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: inventory

- [ ] E-01 Re-measure the documentation surface at execution time: run `rg -l -e '^- (Status|Readiness|Approval|From-Backlog|From-Spec|Blocks-Release|Coverage|Work-Kind|Kind|Release-Exempt-Kind|Release-Exempt-Ref|Gate-Kind|Gate-Ref|Scope-Exceeded|Review-Depth|Pipeline):' -e '## Workflow history' -e '`- (Status|Readiness|From-Backlog|Blocks-Release|Coverage|Kind|From-Spec)' -e 'aw-prompt' -e '--kind' .aw/system/workflows docs .aw/records/*/README.md AGENTS.md README.md CONTRIBUTING.md agent_workflows/engine.py agent_workflows/ipd_schema.py agent_workflows/cli.py .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` (39 files at review before the added roots; the bar is a disposition for every listed file, not that count). The two specs are the "ipd-spec reference documents" that spec 5.4 names; `aw-prompt` covers the staged-prompt comment form (AC-40; `docs/artifact-lifecycles.md`, `.aw/records/prompts/README.md`, `.aw/system/workflows/templates/prompts-README.md`, `.aw/system/workflows/research-prompt/research-prompt.md` at review); `--kind` and `cli.py` cover the `Kind` to `plan_role`/`research_kind`/`prompt_kind` help-text renames of spec 5.4 (`aw ipd scaffold --kind`, `aw research mv --kind` at review). A spec is a record: it gets a `rewrite` disposition only where its text instructs agents to write field syntax; its own front matter and history are migrated by `m0001`, not by this patch. and record the file list with one disposition per file (rewrite, unchanged because the text quotes legacy history, or out of scope with reason) in this plan's `## Findings`.
  - Depends on: none
  - Expected outcome: a complete per-file disposition table; no file in the `rg` output lacks a disposition.
  - Execution state: pending

### Task group 2: write the post-cutover text in a scratch worktree

- [ ] E-02 Create a scratch git worktree from the executing checkout's HEAD inside the gitignored state root (`git worktree add --detach .aw/state/90iqr1/scratch HEAD`; measured at review: 1 s, and it leaves `git status` clean) and, in it only, rewrite the managed block produced by `engine.agents_pointer_prose` and the repo-local `AGENTS.md` text below the managed block so that attestations, `Status`, `From-Backlog`, `From-Spec`, `Blocks-Release`, `Work-Kind`, `Release-Exempt-*` and `Coverage` are described as the commands that write them (`aw ipd set`, `aw specs set`, `aw backlog set`, `aw set`, `aw show <id6> --history`, `aw check meta`, `aw meta repair`), and so that the close-legitimacy rule, the `aw index plans [--check]` sentence handed by `9o83cr`, and the executed-plan rule name the post-cutover forms (spec 5.2 step 4a amendment to the AGENTS.md executed-plan rule). Regenerate the AGENTS.md managed block from the edited generator with `python3 tools/regen_agents_block.py` inside the scratch worktree, so the patch carries the matching `.aw/system/managed-sections.json` section hashes and `tests/test_agents_section_records.py::test_live_agents_md_section_records_are_current` passes on the patched tree.
  - Depends on: E-01
  - Expected outcome: in the scratch worktree, `rg -n '^- (Status|Readiness|Blocks-Release|From-Backlog):' AGENTS.md` returns only quoted legacy examples marked as such.
  - Execution state: pending

- [ ] E-03 In the scratch worktree, rewrite the review workflows: `.aw/system/workflows/plan-review/steps/s7-finalize.md` and `s5-questions.md`, `s6-rereview.md`, `r2-executability.md`, `.aw/system/workflows/spec-review/spec-review.md` and its `README.md`, and `.aw/system/workflows/plan-review-long/*.md`, replacing "write `- Readiness:` into the plan" with the review-round recorder command that `xexn45` hands here (named in E-07 as `aw reviews record`), and replacing every hand edit of status or history with the setter.
  - Depends on: E-01
  - Expected outcome: no review workflow instructs an agent to hand-write a metadata bullet or a history line.
  - Execution state: pending

- [ ] E-04 In the scratch worktree, rewrite the remaining workflow and template files from the E-01 table (`ipd-lifecycle.md`, `askme.md`, `.aw/system/workflows/assess/templates/ipd.md` and `orchestrator-ipd.md`, `.aw/system/workflows/templates/*README.md`) so templates carry the two-key front matter (`id`, `status`) and the banner of spec 4.1 instead of bullet blocks, and instructions name commands.
  - Depends on: E-01
  - Expected outcome: `aw ipd scaffold --apply` run in the scratch worktree after the Order 13 code change produces a file whose head matches the 4.1 shape (verified in Order 13; here the template text is reviewed).
  - Execution state: pending

- [ ] E-05 In the scratch worktree, rewrite the records READMEs (`.aw/records/plans/README.md`, `specs/README.md`, `backlog/README.md`, `releases/README.md`, `walkthroughs/README.md`), `docs/artifact-lifecycles.md` and `docs/run-analytics.md` field-syntax passages, the `ipd_schema.py` section-schema docstrings and help text, and every E-01 row marked `rewrite` among the ipd-spec reference documents and the `aw-prompt` documents (the prompts README and its template, `research-prompt.md`: the staged-prompt comment becomes the single leading `aw-managed-prompt` comment of spec 4.1 and OQ-25), so they describe the log and the commands. Rename `Kind` (plan role), research `kind` and prompt `Kind` to `plan_role`, `research_kind` and `prompt_kind` in every document and in the `cli.py` help strings (spec 5.4 last bullet). Renaming an OPTION (for example `aw ipd scaffold --kind`) is a CLI contract change that this documentation patch does not make: the help text describes the value as the plan role, and any option rename is Order 13's code change (Carrier `cxxmyv`).
  - Depends on: E-01
  - Expected outcome: `rg -n -w 'Kind' --type md` in the scratch worktree finds only quoted legacy examples and `Work-Kind`/`Gate-Kind` spellings that 4.5c keeps as log names `work_kind`/`gate_kind` described as such.
  - Execution state: pending

- [ ] E-06 In the scratch worktree, write the two quickstarts the installer creates (spec 4.1): `.aw/AGENT_QUICKSTART.md` (for agents: where metadata lives, `aw show`, never hand-edit logs or front matter, which commands write which field) and `.aw/QUICKSTART.md` (for people), and the installer template text in `engine.py` that emits them. Both are new files, so E-08 must capture them (see E-08).
  - Depends on: E-02
  - Expected outcome: both files exist in the scratch worktree and are referenced by the banner text of spec 4.1.
  - Execution state: pending

- [ ] E-07 In the scratch worktree, document the two commands handed by `xexn45`: the review-round recorder (`aw reviews record <subject-id6> --round <n> --kind gate|refinement --verdict <v> [--readiness ...] [--review-depth ...]`, which appends one `review` event per spec 4.1a and replaces hand-written `- Readiness:`) and `aw walkthrough new --set <set> --order <nn> --target <id6> --slug <slug> [--summary ...]`. Document them as Order 13 deliverables in the reference text; Order 13 builds them (Carrier `cxxmyv`).
  - Depends on: E-03
  - Expected outcome: the review workflows and the walkthroughs README name both commands with their arguments.
  - Execution state: pending

### Task group 3: package the patch

- [ ] E-08 From the scratch worktree, run `git add -A` (scratch only, so new files such as the two quickstarts are included; measured at review: `git diff HEAD` alone omits an untracked new file) and write `git diff --cached --binary HEAD` to `.aw/system/cutover/metastore-docs.cutover.patch` in the executing checkout, then remove the scratch worktree with `git worktree remove --force .aw/state/90iqr1/scratch`. The live documents in the executing checkout are NOT changed by this plan.
  - Depends on: E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the patch file exists and its `git apply --stat` lists both quickstart files as new; `git status --short` in the executing checkout shows only the patch file, this plan and the test module; `git worktree list` no longer lists the scratch worktree.
  - Execution state: pending

- [ ] E-09 Add `tests/test_metastore_cutover_patch.py` (marked `core`): it runs `git apply --check` of the patch against HEAD without a clone (a temporary `GIT_INDEX_FILE` filled by `git read-tree HEAD`, then `git apply --cached --check`; measured at review: 26 ms, so it fits the core budget) and asserts exit 0; asserts that the patch touches every file the E-01 table marks `rewrite` (the test holds that list as data in the test module, copied from the E-01 table, because reading the plan file would couple a test to a record that `cxxmyv` retires); and asserts that no file outside the documentation set (`.aw/system/workflows/`, `.aw/system/cutover/`, `docs/`, `.aw/records/*/README.md`, `AGENTS.md`, `agent_workflows/engine.py`, `agent_workflows/ipd_schema.py`, `.aw/AGENT_QUICKSTART.md`, `.aw/QUICKSTART.md`, `.aw/system/managed-sections.json`, the two ipd-spec reference documents, `README.md`, `CONTRIBUTING.md`, `agent_workflows/cli.py` help text) is touched. Placing the patch under `.aw/system/` ships it in the wheel and sdist (`pyproject.toml` force-includes `.aw/system`), while the installer copies `.aw/system/workflows/` but not `.aw/system/cutover/`; E-09 also runs `tests/test_installer.py` and `tests/test_installed_text_current.py` so a packaging or install-set change is caught, and `cxxmyv` E-08 deletes the file. The test reads the patch and applies it; it does not read production source.
  - Depends on: E-08
  - Expected outcome: the test passes on HEAD and fails if the patch stops applying, so a later documentation edit that conflicts is caught before the cutover.
  - Execution state: pending

- [ ] E-10 Run `aw sanitize --agent` in a scratch worktree with the patch applied (`.aw/state/90iqr1/check`, created like E-02 and removed afterwards) and confirm no `fail` that the unpatched tree does not also have; in that same patched worktree run `python3 -m pytest -o addopts="" tests/test_agents_section_records.py tests/test_installed_text_current.py tests/test_technical_writing_delivery.py tests/test_askme_command_delivery.py tests/test_authoring_coverage_guidance.py` and record which tests pass and which fail only because they assert pre-cutover text (each such failure is a test Order 13 must update, listed in `## Findings` as F-07 for `cxxmyv`); run `python3 -m pytest -o addopts="" tests/test_metastore_cutover_patch.py` and the bare core gate `python3 -m pytest` in the executing checkout; commit through `aw commit 90iqr1 -- <this plan> <the patch> tests/test_metastore_cutover_patch.py`; never `git add -A` in the executing checkout, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-09
  - Expected outcome: the sanitizer adds no `fail`; the patched-tree test run is recorded with F-07; both executing-checkout test runs pass; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Documentation of field syntax lives in workflow bodies and in the managed block generated by `engine.agents_pointer_prose`; the managed block is written into target repositories by the installer, so its text is a published contract (AGENTS.md "aw:block").
- The runner merges each execute item's isolated worktree into `main` through the merge-and-revalidate gate (AGENTS.md "The runners own ordering, isolation, and orchestrators"). A plan that edited the live documents would therefore land them on `main` at its merge. Delivering a patch file is the only form that both survives the runner's merge and keeps C10a.
- Tests must exercise code and assert on outcomes (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); applying a patch with `git apply --check` is an outcome test.
- User-facing prose (READMEs, docs) carries no em or en dashes (AGENTS.md execution contract).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -l` of bullet-field and history patterns over `.aw/system/workflows` (2026-11-02): 22 files | Every review, lifecycle and template workflow describes field syntax today. |
| F-02 | Same search over `docs/` and `.aw/records/*/README.md`: `docs/artifact-lifecycles.md`, `docs/run-analytics.md`, and the backlog, plans, releases, specs and walkthroughs READMEs | Five READMEs and two docs need rewriting. |
| F-03 | `engine.agents_pointer_prose` (`agent_workflows/engine.py`) | The managed block text is generated in code, so its rewrite is a code change in `engine.py`, still documentation-only in effect. |
| F-04 | `xexn45` Deferred rows with `Carrier: 90iqr1` | Two commands (review-round recorder, `aw walkthrough new`) must be documented here; both are built by Order 13. |
| F-05 | `9o83cr` Deferred row with `Carrier: 90iqr1` | The managed-block sentence "`aw index plans [--check]`/`aw find plans` for the manifest" must be reworded. |
| F-06 | `ya4ee4` E-01 | The description-generation prompt file is owned by Order 05, not this plan. |
| F-07 | (written by E-10) tests that fail on the patched tree only because they assert pre-cutover text | Input to `cxxmyv`, which applies the patch and must update them in the same commit. |

## Proposed changes (ordered, validatable)

1. E-01: inventory with dispositions.
2. E-02 to E-07: rewrite text in a scratch worktree only.
3. E-08 to E-10: package the patch, guard it with a test, commit.

## Deferred / out of scope (with reason)

- Applying the patch to the live documents and building the two documented commands: they must land in the cutover commit (C10a).
  - Carrier: cxxmyv
- The description-generation prompt file.
  - Carrier: ya4ee4
- Documentation for the execution record and the run index.
  - Carrier: nq1src
- Renaming any CLI option that carries the legacy `Kind` name (for example `aw ipd scaffold --kind`), and updating tests that assert pre-cutover text (F-07): both are code changes in the cutover commit.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. The plan edits no live document.
- Under-scope: none. Every item handed to `90iqr1` (F-04, F-05) is covered by E-02 and E-07; spec 5.4 bullets map to E-02 (managed block, AGENTS.md), E-03 and E-04 (workflows, templates), E-05 (READMEs, docs, `ipd_schema`, `Kind` renames) and E-06 (quickstarts).

## Required tests / validation

- `tests/test_metastore_cutover_patch.py` (E-09): the patch applies to HEAD, covers every `rewrite` file, and touches nothing outside the documentation set.
- Sanitizer on the patched tree (E-10), named test run and bare core gate pasted.
- Acceptance criteria: this plan owns none; spec 5.4 is a documentation obligation without an AC. It contributes to AC-16 (the cutover commit amends the AGENTS.md executed-plan rule, 5.2 step 4a) and to AC-40 (the staged-prompt templates), both finally demonstrated by Order 13.

## Spec / documentation sync

No spec change. This plan prepares the documentation that spec `4sd62s` section 5.4 requires; the documents themselves change in Order 13's cutover commit.

## Open questions

### OQ-01: Patch file or branch for the deferred documentation?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Patch file. The runner merges an execute item's worktree into `main`, so a branch created inside the lane would not be the deliverable the runner tracks, and a branch outside the lane is invisible to the merge gate and to `git clone`. A tracked patch file is reviewed with the plan, survives a clone, is guarded by E-09's `git apply --check` test against later drift, and Order 13 applies it in one command. Recommendation strength: strong.

### OQ-03: Where does the scratch worktree live, and how are new files captured?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: Inside the gitignored `.aw/state/90iqr1/` of the executing checkout (`.aw/.gitignore` rule `/state/`), because a runner lane's workspace is that checkout and a `/tmp` path is outside it. New files are captured with `git add -A` inside the scratch worktree and `git diff --cached --binary HEAD`. Demonstrated at review: `git worktree add --detach .aw/state/90iqr1/scratch HEAD` took 1 s and left `git status` clean; `git diff HEAD` omitted a new untracked file, while `git add -N` followed by `git diff HEAD` showed `new file`; a patch applied with `git apply --cached --check` against a temporary index from `git read-tree HEAD` in 26 ms, exit 0. Recommendation strength: strong.

### OQ-02: What if a later commit makes the patch stop applying before the cutover?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: E-09's core test fails on that commit, so the conflict is found at that commit's merge gate rather than at the cutover. The maintainer stops other work while this Set runs (spec section 7), so this is expected to be rare; Order 13 regenerates the patch if needed. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [ ] V-01 validates E-01
  - Required evidence: paste the `rg -l` command and its full file list, and the `## Findings` disposition table with one row per listed file; a file in the list with no row is a failure.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n '^- (Status|Readiness|Blocks-Release|From-Backlog):' AGENTS.md` run in the scratch worktree (only quoted legacy examples), the `git diff` hunk of `engine.agents_pointer_prose` showing the command-based wording and the reworded `aw index plans` sentence, and `python3 -m pytest -o addopts="" tests/test_agents_section_records.py` passing in the scratch worktree after `tools/regen_agents_block.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n -e 'Readiness:' -e '## Workflow history' .aw/system/workflows/plan-review .aw/system/workflows/spec-review .aw/system/workflows/plan-review-long` in the scratch worktree with each remaining hit shown to be a quoted legacy example, and one diff hunk showing `aw reviews record` in `s7-finalize.md`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the diff hunks of `assess/templates/ipd.md` and `orchestrator-ipd.md` showing the two-key front matter and banner, and `rg -c '^- (Status|Kind|Set):' .aw/system/workflows/assess/templates .aw/system/workflows/templates` in the scratch worktree returning 0 for every template file.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the diff stat for the five READMEs, `docs/artifact-lifecycles.md`, `docs/run-analytics.md` and `ipd_schema.py`, `rg -n -w 'Kind' --type md` in the scratch worktree with each hit classified (quoted legacy, `Work-Kind`, `Gate-Kind`), the diff hunks of each ipd-spec reference document and `aw-prompt` document marked `rewrite` in E-01, and the `cli.py` help-string hunks.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the content of both quickstart files from the scratch worktree and the `engine.py` diff hunk that emits them.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the diff hunks in the review workflows and the walkthroughs README that name `aw reviews record` and `aw walkthrough new` with their arguments, each marked as delivered by Order 13.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-docs.cutover.patch` (file list, with both quickstarts shown as new and `.aw/system/managed-sections.json` included), `ls -l` of the patch file, `git worktree list` showing the scratch worktree removed, and `git status --short` in the executing checkout listing only the three Scope-Paths files.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste `python3 -m pytest -o addopts="" -v --durations=0 tests/test_metastore_cutover_patch.py` with every test PASSED and its wall time; the output of the same run after deliberately corrupting one hunk of a scratch copy of the patch, showing the apply test FAILED; and the summary lines of `tests/test_installer.py` and `tests/test_installed_text_current.py` passing in the executing checkout.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste the `aw sanitize --agent` result on the patched scratch worktree beside the unpatched result (no added `fail`), the patched-tree test run with its pass and fail lines and the F-07 table, the executing-checkout named test run summary, the bare core gate summary line, and the `aw commit` output naming the commit hash.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `9o83cr` is `executed` and this plan is `approved`. Open questions: OQ-01 to OQ-03 are resolved and none is blocking. The executor edits documents ONLY in a scratch worktree under `.aw/state/90iqr1/`; the executing checkout changes only by the three Scope-Paths files.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Honesty rule: paste the ACTUAL output of the named test runs, the bare core gate and the sanitizer; never claim a result you did not run.

Commits: commit only through `aw commit 90iqr1 -- <paths>`; never `git add -A` in the executing checkout, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 90iqr1` itself.
