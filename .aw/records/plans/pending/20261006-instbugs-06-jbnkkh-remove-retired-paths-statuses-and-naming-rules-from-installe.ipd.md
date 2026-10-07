# IPD: Remove retired paths, statuses and naming rules from installed READMEs, ignore blocks and install messages

- Date: 2026-10-06
- Kind: child
- Concern: Defects D08 and D09 of research report `l6cbbb`, present at HEAD `474b037a9` in a scratch `.aw`-layout target. D08: the installed `.aw/records/research/README.md` (from `.aw/system/workflows/templates/agents-docs-research-README.md`) still lists `intake | landed, not yet triaged | hot root` and says "Hot states (`intake`/`active`)" and "`INDEX.md` shows the most-recent-N plus intake", although `research_contract.STATUSES` is `{"todo", "active", "reference", "archive"}` and `intake` survives only in `STATUS_NORMALIZATIONS` (`{"intake": "todo"}`); it never says hot states are statuses in the flat root rather than directories; and it cites `.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md`, which no target has (specs are not installed). D09: the install prints "use the gitignored untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/." (`engine.py`) and "Read and execute .agents/workflows/index.md, then the workflow body." (`engine.py`; also `cli.py` "Or from any agent: 'Read and execute .agents/workflows/index.md'"); the installed comms README begins `# .agents/comms/` and says "See the agent-comms convention spec under `.agents/docs/specs/`" (template text in `engine.py`); the root `.gitignore` `aw:untracked` block says "the .agents/plans lifecycle rules say IPDs live under .agents/plans/" and "e.g. .agents/plans/pending/untracked/"; the installed specs README (`agents-docs-specs-README.md`) says specs are "Named `YYYYMMDD-HHMM-NN-<slug>.md`", contradicting the installed AGENTS.md (new specs use the id6 grammar via `aw specs new`).
- Scope: IN: make every one of those texts LAYOUT-AWARE (the `.aw` layout names `.aw/...` paths; a kept legacy `.agents/` layout keeps its own paths, since `--keep-legacy` is supported) or layout-neutral; switch the research README to `todo`, state that hot states are statuses in the flat root (not directories), and label `intake` as a legacy alias; replace the uninstalled spec citation with a reference that resolves in a target (`aw research --help` and the installed `.aw/system/workflows/index.md`); make the specs README state the current id6 grammar minted by `aw specs new` with legacy names grandfathered; add a bundle-scan test. OUT: `.agents/skills/` (the cross-tool Agent Skills location the installer deliberately writes; NOT retired); code docstrings and comments citing `.agents/docs/specs/...` (not installed into targets, not agent-facing in a target); the managed AGENTS.md block (Order 07 `ka0g86`).
- Scope-Paths: .aw/system/workflows/templates/agents-docs-research-README.md, .aw/system/workflows/templates/agents-docs-specs-README.md, agent_workflows/engine.py, agent_workflows/cli.py, tests/test_installed_text_current.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: instbugs
- Order: 6
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: jbnkkh

## Workflow history

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 06 of Set `instbugs` after grepping a fresh HEAD install (`474b037a9`) and the install log for every stale string the report names, and locating each string's source.

## Goal

Nothing an install writes or prints for an `.aw`-layout target points at the retired `.agents/` record layout, names a non-canonical research status as current, or contradicts the current spec naming grammar, and a test keeps it that way.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: fresh `.aw`-layout install into a temp git repo with output captured; run `grep -rnE "\.agents/(plans|prompts|comms|docs|workflows)" AGENTS.md .gitignore .aw/.gitignore .aw/records <log>` and `grep -n "intake" .aw/records/research/README.md` and `grep -n "Named" .aw/records/specs/README.md`.
  - Depends on: none
  - Expected outcome: the inventory of stale strings pasted (the report's list plus any others found). The AGENTS.md hits are recorded and left to Order 07.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 Research README template: replace `intake` with `todo` in the states table and prose; add one sentence that `todo`/`active` are STATUS values of documents kept flat in this directory's root, not subdirectories, and that the raw-drop directory for external material is `.aw/inbox/` (adopted with `aw adopt`); label `intake` as a legacy alias normalized to `todo`; replace the spec-path citation with "see `aw research --help` and `.aw/system/workflows/index.md`".
  - Depends on: E-01
  - Expected outcome: the installed research README names only `research_contract.STATUSES` members as statuses (plus `intake` labelled legacy) and cites only paths a target has.
  - Execution state: pending

- [ ] E-03 Specs README template: state that new specs are created with `aw specs new` and named `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md`, and that legacy `YYYYMMDD-HHMM-NN-<slug>.spec.md` names remain valid (grandfathered).
  - Depends on: E-02
  - Expected outcome: the installed specs README agrees with the installed AGENTS.md on spec naming.
  - Execution state: pending

- [ ] E-04 Layout-aware engine and CLI text: derive the paths in the post-install "untracked lanes" note, the "Universal fallback ... Read and execute <workflows index>" line (engine and `cli.py`), the comms README template heading and spec pointer, and the root `.gitignore` `aw:untracked` block examples from the target layout (the same `target_layout` value `update_agents_pointer` and `agents_pointer_prose` already receive), so an `.aw` target reads `.aw/records/prompts/untracked/`, `.aw/records/comms/untracked/`, `.aw/system/workflows/index.md`, `.aw/records/plans/...`; the comms README drops the uninstalled-spec pointer in favor of its own content. The root `.gitignore` block back-fill must rewrite the old block text on upgrade (the block is framework-managed between `aw:block` markers).
  - Depends on: E-03
  - Expected outcome: in an `.aw` target, none of these texts contains `.agents/plans`, `.agents/prompts`, `.agents/comms`, `.agents/docs` or `.agents/workflows`; in a `--keep-legacy` target they still name the legacy paths that exist there.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_installed_text_current.py`: (a) fresh `.aw`-layout install into a temp git repo with captured stdout; scan the captured output, root `.gitignore`, `.aw/.gitignore` and every file under `.aw/records/` for `\.agents/(plans|prompts|comms|docs|workflows)` and fail on any hit (the managed AGENTS.md block is scanned by Order 07's test, not here); (b) parse the installed research README's status table and assert every status token is in `research_contract.STATUSES` or is explicitly labelled as a legacy alias present in `STATUS_NORMALIZATIONS`; (c) upgrade case: seed a root `.gitignore` carrying the old `aw:untracked` block text, reinstall, assert the scan is clean. Prove (a) can fail by restoring the old post-install note and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails (a); no test reads production source (the scan reads INSTALLED output in a temp repo, which is the product's observable behavior).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The installer supports both layouts (`--to-aw`, `--keep-legacy`); `agents_pointer_prose(target_layout)` and `update_agents_pointer(..., target_layout=...)` already branch on the layout, so the fix reuses that value.
- `research_contract` is the status authority (`STATUSES`, `HOT_STATUSES`, `STATUS_NORMALIZATIONS`); the rename to `todo` was rstodo Order `p3o9je`.
- `.agents/skills/` is written on purpose for cross-tool skill discovery (scratch install wrote `.agents/skills/*/SKILL.md`); it is excluded from the scan.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Research README template uses `intake` and cites an uninstalled spec. | `agents-docs-research-README.md` line 38 "| `intake` | landed, not yet triaged | hot root |", lines 43-44, line 9 spec path |
| F-02 | Install log prints retired lane paths and fallback. | scratch log line "or use the gitignored untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/."; upgrade log "Read and execute .agents/workflows/index.md, then the workflow body." |
| F-03 | Installed comms README and root `.gitignore` block cite `.agents/`. | scratch `.aw/records/comms/README.md` line 1 `# .agents/comms/`, line 52 "spec under `.agents/docs/specs/`"; root `.gitignore` "e.g. .agents/plans/pending/untracked/" |
| F-04 | Specs README naming is the legacy grammar. | scratch `.aw/records/specs/README.md` line 6 "Named `YYYYMMDD-HHMM-NN-<slug>.md` (local time)." |
| F-05 | The INDEX "COMMITTED" advice the report quotes is already gone. | installed research README: "Both are GENERATED, GITIGNORED, LOCAL views" (D15 second half fixed at HEAD) |

## Proposed changes (ordered, validatable)

1. Research README (E-02).
2. Specs README (E-03).
3. Layout-aware engine and CLI text (E-04).
4. Bundle scan and status test (E-05).

## Deferred / out of scope (with reason)

- THE MANAGED AGENTS.md BLOCK and the general dangling-reference check.
  - Carrier: ka0g86

## Scope check

- Over-scope: none.
- Under-scope: code docstrings in `agent_workflows/*.py` that cite `.agents/docs/specs/...` are not installed into a target and are not agent-facing there; left alone.

## Required tests / validation

- `tests/test_installed_text_current.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- N/A for specs: the READMEs are brought into line with existing specs and `research_contract`.

## Open questions

### OQ-01: Should legacy-layout targets also be moved off `.agents/` text?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: no. A `--keep-legacy` target really has `.agents/` paths, so naming them there is correct; the defect is naming them in an `.aw` target.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit grep inventory with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the installed research README's states table and the new flat-root sentence and citation from a post-edit fresh install.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the installed specs README naming paragraph.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the E-01 grep re-run on a post-edit fresh `.aw` install and its log (no hits outside AGENTS.md), and the same lines from a `--keep-legacy` install showing legacy paths.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: D08 and D09 are the same defect class (installed text that names retired or wrong things) with one shared test fixture and scan.

EXECUTION CONTRACT. Execute E-items in order. Commit only files changed for this plan through `aw commit jbnkkh -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed jbnkkh`.
