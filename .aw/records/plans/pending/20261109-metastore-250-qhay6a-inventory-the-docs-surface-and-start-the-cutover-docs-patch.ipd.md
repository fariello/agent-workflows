# IPD: Inventory the docs surface and start the cutover docs patch with the managed block

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 5.4 requires every document, template, workflow and managed-block text that describes metadata FIELD SYNTAX to describe COMMANDS instead, and C10a forbids that text from reaching `main` before the cutover commit. Plan `90iqr1` owned the whole documentation patch in one pass (10 E-items); research `nj8zdp` guidance asks for smaller plans, so the patch is now built in four parts (this plan, `a49djh`, `y1zihp`, `ngc2a2`) and finished by `90iqr1`. This first part takes the inventory and the managed-block rewrite.
- Scope: Inventory the documentation surface with one disposition per file; in a scratch worktree only, rewrite the `engine.agents_pointer_prose` managed block and the repo-local `AGENTS.md` text; write the result as the first version of the cumulative patch `.aw/system/cutover/metastore-docs.cutover.patch`. No live document changes.
- Scope-Paths: .aw/records/plans/pending/20261109-metastore-250-qhay6a-inventory-the-docs-surface-and-start-the-cutover-docs-patch.ipd.md, .aw/system/cutover/metastore-docs.cutover.patch
- Item-Dependencies: executed:9o83cr
- Status: approved
- Readiness: go-pending-approval
- Review-Depth: complex
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 250
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: qhay6a
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-11-16 approved (aw set): status set to approved
- 2026-11-14 reviewed (antigravity/gemini): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 confirmed FIXED; scaffold removed
- 2026-11-14 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 FIXED
- 2026-11-13 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 FIXED
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 90iqr1 (round 3, research nj8zdp guidance).

## Goal

Record which documentation files the cutover must rewrite, and start the cumulative cutover documentation patch with the managed-block and `AGENTS.md` rewrite, so the later parts (`a49djh`, `y1zihp`, `ngc2a2`) extend one patch and `90iqr1` guards it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: inventory

- [ ] E-01 (was `90iqr1` E-01; owner rule and `UNASSIGNED` handling added at review 2026-11-13.) Re-measure the documentation surface at execution time: run `rg -l -e '^- (Status|Readiness|Approval|From-Backlog|From-Spec|Blocks-Release|Coverage|Work-Kind|Kind|Release-Exempt-Kind|Release-Exempt-Ref|Gate-Kind|Gate-Ref|Scope-Exceeded|Review-Depth|Pipeline):' -e '## Workflow history' -e '`- (Status|Readiness|From-Backlog|Blocks-Release|Coverage|Kind|From-Spec)' -e 'aw-prompt' -e '--kind' .aw/system/workflows docs .aw/records/*/README.md AGENTS.md README.md CONTRIBUTING.md agent_workflows/engine.py agent_workflows/ipd_schema.py agent_workflows/cli.py .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` (39 files when `90iqr1` was split, 47 at review on 2026-11-13; the bar is a disposition for every listed file, not that count). The two specs are the "ipd-spec reference documents" that spec 5.4 names; `aw-prompt` covers the staged-prompt comment form (AC-40); `--kind` and `cli.py` cover the `Kind` to `plan_role`/`research_kind`/`prompt_kind` help-text renames of spec 5.4. A spec is a record: it gets a `rewrite` disposition only where its text instructs agents to write field syntax; its own front matter and history are migrated by `m0001`, not by this patch. Record the file list with one disposition per file (rewrite, unchanged because the text quotes legacy history, or out of scope with reason) in this plan's `## Findings` as F-03, and name for each `rewrite` row which part rewrites it, as `<id6> E-<nn>`. Assign owners by the F-03 owner rule in `## Project conventions discovered`. A `rewrite` row that no rule matches (for example another `docs/` file or `.aw/records/reviews/README.md`) is written to F-03 with owner `UNASSIGNED` and listed in V-01; it is not given to a part whose E-item does not name or catch-all it, because `90iqr1` E-09 asserts the patch touches every `rewrite` file and would then fail. Do not edit a sibling plan to absorb it here; the review record of this plan hands the gap to that sibling's review (Deferred, Carrier `y1zihp`).
  - Depends on: none
  - Expected outcome: a complete per-file disposition table; no file in the `rg` output lacks a disposition, every `rewrite` row has an owner from the rule or `UNASSIGNED`, and every `UNASSIGNED` row is listed in V-01.
  - Execution state: pending

### Task group 2: managed block

- [ ] E-02 (was `90iqr1` E-02.) Create a scratch git worktree from the executing checkout's HEAD inside the gitignored state root (`git worktree add --detach .aw/state/qhay6a/scratch HEAD`). Before editing, record the baseline count of quoted field syntax in the scratch worktree's `AGENTS.md` and `agent_workflows/engine.py` with `` rg -c '`- (Status|Readiness|Approval|From-Backlog|From-Spec|Blocks-Release|Coverage|Work-Kind|Release-Exempt-Kind|Release-Exempt-Ref|Gate-Kind|Gate-Ref):' AGENTS.md agent_workflows/engine.py `` (16 and 12 at review). Then, in the scratch worktree only, rewrite the managed block produced by `engine.agents_pointer_prose` and the repo-local `AGENTS.md` text below the managed block so that attestations, `Status`, `From-Backlog`, `From-Spec`, `Blocks-Release`, `Work-Kind`, `Release-Exempt-*`, `Gate-*` and `Coverage` are described as the commands that write them (aw ipd set, aw specs set, aw backlog set, aw set, aw show <id6> --history, aw check meta, aw meta repair), and so that the close-legitimacy rule, the `aw index plans [--check]` sentence handed by `9o83cr` (after the cutover it is an alias of `aw index rebuild` and `--check` is deleted, spec 4.3), and the executed-plan rule name the post-cutover forms (spec 5.2 step 4a amendment). Leave the `` `- Kind: orchestrator` `` sentence to `ngc2a2` E-02 (the `Kind` to `plan_role` rename). Spec 5.4 says "A document must not describe a command that does not exist": before naming any command, run `aw <command> --help` from the scratch root and record the exit code; `aw meta repair` and the `meta` type of `aw check` are built by `a5ijjx` (upstream through `ffceq0` and `9o83cr`), so a nonzero exit there means `a5ijjx` has not delivered them, and the command is then named only as an Order 13 deliverable in the text, the way `a49djh` E-03 treats `aw reviews record`. Regenerate the AGENTS.md managed block from the edited generator by running `python3 -m tools.regen_agents_block` from the scratch worktree root, then `python3 -m tools.regen_agents_block --check` (expects `Up to date`), so the patch carries the matching managed-sections section hashes. Use the module form: `python3 tools/regen_agents_block.py` puts `tools/` first on `sys.path` and can import `agent_workflows` from another checkout (measured at review: the script form in a worktree imported the main checkout's package), which would regenerate from the unedited generator.
  - Depends on: E-01
  - Expected outcome: in the scratch worktree, the quoted field-syntax count is lower than the baseline, and each remaining hit is a quoted legacy example marked as such (for example the spec 5.2 step 4a quotation of the old executed-plan rule); `--check` prints `Up to date`; the live section-records test passes.
  - Execution state: pending

### Task group 3: package

- [ ] E-03 From the scratch worktree, run `git add -A` (scratch only, so new files are included) and write `git diff --cached --binary HEAD` to `.aw/system/cutover/metastore-docs.cutover.patch` in the executing checkout (this creates the cumulative patch that `a49djh`, `y1zihp` and `ngc2a2` extend); remove the scratch worktree with `git worktree remove --force .aw/state/qhay6a/scratch`; commit through `aw commit qhay6a -- <this plan> .aw/system/cutover/metastore-docs.cutover.patch`. Never `git add -A` in the executing checkout; never push.
  - Depends on: E-02
  - Expected outcome: the patch exists and lists only the managed-block files (no `__pycache__` or `.pytest_cache` path: `__pycache__/` is gitignored, and `.pytest_cache` carries its own ignore file); the executing checkout's `git status --short` shows only this plan and the patch before the commit; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Field-syntax documentation lives in workflow bodies and in the managed block generated by `engine.agents_pointer_prose`; the installer writes that block into target repositories, so its text is a published contract.
- The runner merges each execute item's isolated worktree into `main`, so editing live documents would land them on `main` early; a tracked patch file keeps C10a (see `90iqr1` OQ-01).
- The scratch worktree lives in the gitignored `.aw/state/<id6>/` of the executing checkout (see `90iqr1` OQ-03); `git diff HEAD` alone omits new untracked files, so the capture uses `git add -A` inside the scratch worktree.
- Cite code by SYMBOL, not line number.
- F-03 owner rule (E-01). Apply it per passage: a file whose passages match two rules gets one row per owner (for example the `` `- Kind: orchestrator` `` sentence in `AGENTS.md` and `engine.py` goes to rule 2 while the rest of those files goes to rule 1); otherwise the first matching rule wins. (1) `AGENTS.md`, `.aw/system/managed-sections.json` and the `engine.agents_pointer_prose` text in `agent_workflows/engine.py`: `qhay6a` E-02; (2) the installer quickstart text in `agent_workflows/engine.py`, `Kind` renames in any file, and `agent_workflows/cli.py` help text: `ngc2a2` E-02, E-03 or E-04; (3) `.aw/system/workflows/plan-review/steps/*`, `.aw/system/workflows/spec-review/*` and `.aw/system/workflows/plan-review-long/*`: `a49djh` E-02; (4) every other file under `.aw/system/workflows/` except `research-prompt/` and the prompts template: `a49djh` E-04, whose text covers "the remaining workflow and template files from the `qhay6a` F-03 table owned by this part"; (5) the five records READMEs that `y1zihp` E-02 names: `y1zihp` E-02 (the walkthroughs README also `a49djh` E-03); (6) `docs/artifact-lifecycles.md`, `docs/run-analytics.md` and `agent_workflows/ipd_schema.py`: `y1zihp` E-03; (7) the two ipd-spec reference documents and the `aw-prompt` documents (prompts README, prompts template, `research-prompt` workflow body): `y1zihp` E-04.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `90iqr1` F-01 to F-05 | Measured surface and handed-in items (managed block from `9o83cr`, two commands from `xexn45`). |
| F-02 | Round-3 split 2026-11-09 | The patch is cumulative: each later part applies the committed patch in its scratch worktree before editing, then rewrites the same file. |
| F-03 | (written by E-01) | Per-file disposition table, with the owning part for each `rewrite` row. `90iqr1` E-09 copies the `rewrite` list from this table. |
| F-04 | Review 2026-11-13: the E-01 `rg -l` run lists 47 files | Rows with no named sibling E-item before this review: `docs/cli-output-contract.md` (its `aw show --history` row text), `.aw/records/reviews/README.md`, `.aw/records/roadmaps/README.md`, and several workflow bodies (`conformance/operator-protocol.md`, `migrate/migrate.md`, `incident`, `whatnext`, `assess-all`, `assess/assess.md`, `spec/spec.md`, `verify-execution`, `release-review/templates/*`). The E-01 rule gives the workflow bodies to `a49djh` E-04 (catch-all) and marks the rest `UNASSIGNED` if they need a rewrite. A wider scan of all tracked text adds 44 `agent_workflows/*.py` parser modules, `CHANGELOG.md`, `DECISIONS.md` and `tools/gate_drop_audit.py`: code or history, not documentation, owned by the code cutover (`clors0`, `cxxmyv`); no `help=` string in `agent_workflows/` carries field syntax. `GEMINI.md` carries none of the patterns. |
| F-05 | `python3 tools/regen_agents_block.py` versus `python3 -m tools.regen_agents_block`, probe in a review worktree | The script form set `sys.path[0]` to `tools/` and imported `agent_workflows` from the main checkout (an editable install); the module form imported the worktree copy. `tests/test_agents_section_records.py` names the module form as its remedy. |
| F-06 | `rg -n '^- (Status\|Readiness\|Blocks-Release\|From-Backlog):' AGENTS.md` today: no output, exit 1 | The old E-02 outcome check already passes on the unedited file, because AGENTS.md quotes field syntax inside backticks. The quoted-form count (16 in AGENTS.md, 12 in `engine.py`) is the measure E-02 and V-02 now use. |
| F-07 | `aw check meta` today: `unknown artifact type 'meta'`, exit 2; `aw meta repair --help`: exit 2; `aw reviews record --help`: exit 2 | `aw ipd set`, `aw specs set`, `aw backlog set`, `aw set` and `aw show --history` exist with the needed flags. The `meta` commands come from `a5ijjx` (Order 140), upstream of this plan through `ffceq0` and `9o83cr`. |

```mermaid
flowchart TD
  H[executing checkout HEAD] --> S[scratch worktree .aw/state/qhay6a/scratch]
  S --> E2[E-02: rewrite engine.agents_pointer_prose and AGENTS.md]
  E2 --> R[python3 -m tools.regen_agents_block]
  R --> P[E-03: git add -A in scratch, diff to metastore-docs.cutover.patch]
  P --> A[a49djh applies patch, extends it]
  A --> Y[y1zihp applies patch, extends it]
  Y --> N[ngc2a2 applies patch, extends it]
  N --> G[90iqr1: guard test, sanitizer, patched-tree tests]
  G --> C[cxxmyv: applies patch in the cutover commit]
  E1[E-01: F-03 table with owners] --> E2
  E1 -.rewrite list.-> G
```

## Proposed changes (ordered, validatable)

1. E-01: inventory with dispositions and owning parts.
2. E-02: managed block and AGENTS.md in a scratch worktree.
3. E-03: write the cumulative patch and commit.

## Deferred / out of scope (with reason)

- Review workflows, recorder and walkthrough command docs, templates: second part.
  - Carrier: a49djh
- READMEs, docs, `ipd_schema.py` text and reference documents: third part.
  - Carrier: y1zihp
- Any F-03 `rewrite` row that E-01 marks `UNASSIGNED` (at review: candidates `docs/cli-output-contract.md`, `.aw/records/reviews/README.md`, `.aw/records/roadmaps/README.md`): the READMEs-and-docs part, whose review must add it to an E-item or record it `unchanged` before `90iqr1` copies the list.
  - Carrier: y1zihp
- `Kind` renames and quickstarts: fourth part.
  - Carrier: ngc2a2
- Patch guard test, sanitizer and patched-tree test run: finishing part.
  - Carrier: 90iqr1

## Scope check

- Over-scope: none. No live document is edited.
- Under-scope: none. Spec 5.4 managed-block and AGENTS.md bullets map to E-02; the inventory maps to E-01. Inventory rows that no sibling E-item covers are surfaced as `UNASSIGNED` and handed to `y1zihp` (Deferred) rather than rewritten here, so this plan stays at the managed block.

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

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `rg -l` command and its full file list, and the F-03 disposition table with one row per listed file and, for each `rewrite` row, the owner as `<id6> E-<nn>` from the E-01 rule or `UNASSIGNED`; paste the list of `UNASSIGNED` rows (or `none`). A listed file with no row, or a `rewrite` row whose owner E-item neither names the file nor is the `a49djh` E-04 catch-all, is a failure.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste, from the scratch worktree root, (1) the E-02 quoted field-syntax `rg -c` command run before and after the edit (after counts lower than before) and `rg -n` of the same pattern after the edit, with each remaining hit identified as a marked legacy quotation; (2) the `git diff` hunk of `engine.agents_pointer_prose` showing the command-based wording and the reworded `aw index plans` sentence; (3) the `aw <command> --help` exit code for every command the new text names, with any nonzero-exit command shown in the diff as an Order 13 deliverable; (4) `python3 -m tools.regen_agents_block` output, then `python3 -m tools.regen_agents_block --check` printing `Up to date`; (5) `python3 -m pytest -o addopts="" tests/test_agents_section_records.py` showing the module's tests passed (the live section-records test among them) with the `N passed` line.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-docs.cutover.patch` (file list exactly `agent_workflows/engine.py`, `AGENTS.md`, `.aw/system/managed-sections.json`), `git apply --check` of the patch against the executing checkout exiting 0, `git worktree list` showing the scratch worktree removed, and the `aw commit` output naming the commit hash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `9o83cr` is `executed` and this plan is `approved`. The executor edits documents ONLY in a scratch worktree under `.aw/state/qhay6a/`; the executing checkout changes only by this plan and the patch file.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Stop and report rather than editing production code outside Scope-Paths or weakening test assertions if an unexpected failure occurs on unmodified code, or if an unresolvable concurrent-edit conflict occurs.

Honesty rule: paste the ACTUAL output of every command named above; never claim a result you did not run.

Commits: commit only through `aw commit qhay6a -- <paths>`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
