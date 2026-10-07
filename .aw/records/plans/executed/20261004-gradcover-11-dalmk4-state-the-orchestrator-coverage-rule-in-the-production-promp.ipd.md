# IPD: State the orchestrator coverage rule in the production prompts, the scaffold template and AGENTS.md

- Date: 2026-10-04
- Kind: child
- Concern: Authors are never told the rule the runner enforces. `runner_shared.build_backlog_production_prompt` and `build_spec_production_prompt` each list seven contract items (status `to-review`, provenance, gate inheritance, Scope-Paths, Item-Dependencies, lint, do not modify requirements) and say nothing about orchestrator plans, child plans, or work no child covers. The orchestrator skeleton written by `aw ipd scaffold --kind orchestrator` (`ipd_authoring._SECTION_BODY`) pre-fills `- TODO: whole-Set completion criteria.`, `- TODO: cross-IPD consistency / no-drift / dependency checks.` and `TODO: how the executed plan is verified.`; those are exactly three of the sections the probe reads, and the natural way to fill them is with whole-Set obligations that name no owner, which the probe's prompt calls uncovered work. The managed `AGENTS.md` block (source of truth in `engine.py`) instructs, under "Acting on a backlog item", "set the item to `graduated`" with no precondition, and its "ORCHESTRATOR COVERAGE GATE" paragraph says the gate runs "once per queued orchestrator", which Order 04 changes. `/plan-review` documents the `IPD-S407` row check but not review readiness. Telling authors the rule up front is what makes the gates added by Orders 05, 06 and 10 rarely fire.
- Scope: IN: add a "Orchestrator plans" section to both production prompts; change the three orchestrator skeleton placeholders to text that requires a named owner; amend the managed `AGENTS.md` block in `engine.py` (the "Acting on a backlog item" step (5) precondition, and the "ORCHESTRATOR COVERAGE GATE" paragraph's scope, quote and named-owner sentences) and regenerate this repository's `AGENTS.md` from it through the installer's merge path (`engine.merge_aw_block` with the repository manifest), not by hand, updating only the `AGENTS.md#aw:pointer` record in `.aw/system/managed-sections.json`; regenerate the byte-parity orchestrator template `.aw/system/workflows/assess/templates/orchestrator-ipd.md` from `build_skeleton`; add a review-readiness subsection to `.aw/system/workflows/plan-review/plan-review.md` and the two `plan-review-long` step files that already carry the `IPD-S407` subsection. OUT: any gate or check (Orders 03 to 10); the skeleton's child-plan sections; any other managed-block paragraph.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_authoring.py, .aw/system/workflows/assess/templates/orchestrator-ipd.md, agent_workflows/engine.py, AGENTS.md, .aw/system/managed-sections.json, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, tests/test_authoring_coverage_guidance.py
- Item-Dependencies: executed:26m1nb, executed:5etev3, executed:r2wa38, executed:sbiv1j
- Status: executed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 11
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: dalmk4

## Workflow history
- 2026-10-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: dalmk4 verified (set gradcover, attempt 1).
- 2026-10-06 approved (aw set): status set to approved
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 (all fixed)

- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-008. Fixed: `- Item-Dependencies:` gains `5etev3`, `r2wa38`, `sbiv1j`, whose gates the new text describes (PR-001); E-03 regeneration driven through `merge_aw_block` with the manifest after a self-heal pass, because the recorded `AGENTS.md#aw:pointer` hash is stale and an installer refresh would silently keep the old section (measured), manifest added to scope (PR-002); the byte-parity orchestrator template regenerated in E-02 and added to scope (PR-003); the three new orchestrator placeholders added to `_AUTHORING_PLACEHOLDERS`, since the stub predicate matches only listed markers and never a `TODO:` prefix (measured), with a kind-aware `Required tests` override specified (PR-004); E-01 item (4) states what `aw ipd coverage` does in a production turn (PR-005); E-03 named-child sentence credits an Order number as `8mabmu` does (PR-006); E-04 placement per file (PR-007); E-05 both layouts and a second mutation, targeted test list, gate honesty and scope fence (PR-008).
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 11 of Set `gradcover`. Depends on Order 05 so the text it writes describes a gate that exists. The `AGENTS.md` wording below is the text to insert; the executor may make wording-level edits for line length but not change what it requires.

## Goal

Make every place an author or reviewer reads before writing an orchestrator plan state the same rule the gates enforce: each whole-Set obligation names, by id6, the child plan that performs it, and work no child performs gets a new child plan and a table row, never a parent step and never a deleted checklist.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the text authors read while writing

- [x] E-01 Add to both `build_backlog_production_prompt` and `build_spec_production_prompt`, after the Production Contract list, a section "## Orchestrator plans (when you write a Set)" with these four items: (1) every item under `## Completion criteria`, `## Cross-IPD validation` and `## Required tests / validation` names, by id6, the child plan in this Set's `## Child IPDs` table that performs it; (2) work no existing child performs gets a NEW child plan and a table row, never a step on the orchestrator; (3) the orchestrator's checklist contains only `CONFIRM <child-id6> REACHED <status>` rows, and you never delete it; (4) before you finish, run `aw ipd coverage <orchestrator-id6>` and fix every quoted finding it prints; it records its answer in the orchestrator plan, and the runner checks the whole Set again after your turn (`BACKLOG-GRADUATE-SET` / `SPEC-PLAN-SET`, Order 06), so an unfixed finding fails the item. Place the section between `## Production Contract` and `## Prohibitions` in both builders (OQ-01: always include it, the prompt cannot know in advance whether the agent will write a Set). Use the SAME four sentences in both builders (one module-level tuple of lines referenced by both, so the two prompts cannot drift); Order 08 (`24qw39`, executed earlier) may have added a conditional "Continue this handoff" section to the same builders, so locate the insertion point by the `## Prohibitions` heading, not by a line offset, and leave that section untouched.
  - Depends on: none
  - Expected outcome: both rendered prompts contain the section, between the Production Contract and Prohibitions headings, with all four items and the literal `aw ipd coverage` command; nothing else in either prompt changed.
  - Execution state: performed

- [x] E-02 Change the orchestrator skeleton placeholders in `ipd_authoring._SECTION_BODY`: `H_COMPLETION` to `- TODO: each whole-Set criterion, ending with "Owner: <child-id6>" naming the child plan that performs it.`; `H_CROSS_IPD` to `- TODO: each cross-child consistency check, naming the child plan (by id6) that performs it; a check no child performs needs a new child plan.`; and, for the orchestrator kind only, `H_REQUIRED_TESTS` to `TODO: this plan runs no tests; name the child plan (by id6) that performs the whole-Set measurement.` THE STUB PREDICATE MATCHES ONLY LISTED MARKERS, never a `TODO:` prefix: `authoring_placeholders_resolved` returns True as soon as every string in `_AUTHORING_PLACEHOLDERS` is gone (measured at review: an orchestrator skeleton with every listed marker replaced but the three current orchestrator placeholders still present returned True). So ADD the three new orchestrator placeholder strings to `_AUTHORING_PLACEHOLDERS` (they are stubs an author must replace, unlike the permanent `H_PROJECT_CONVENTIONS` guidance the comment there warns about), referencing the same constants rather than retyping the text. `_SECTION_BODY` is keyed by heading only and `build_skeleton` reads it with `_SECTION_BODY.get(h, "TODO.")` for both kinds, so the orchestrator `H_REQUIRED_TESTS` text needs a kind-aware lookup: add a small `_ORCH_SECTION_BODY` override dict consulted first when `kind == S.KIND_ORCHESTRATOR`, leaving `_SECTION_BODY[S.H_REQUIRED_TESTS]` (the child text) unchanged. `H_COMPLETION` and `H_CROSS_IPD` appear only in `ORCHESTRATOR_H2_ORDER`, so they may change in place. THEN REGENERATE THE BYTE-PARITY TEMPLATE `.aw/system/workflows/assess/templates/orchestrator-ipd.md` from `build_skeleton` with the exact arguments `tests/test_ipd_templates.py` `test_orchestrator_template_matches_generator` uses (title `<short title of the coordinated change>`, author `<agent/model>`, when `<YYYY-MM-DD>`, set `<set-id>`, order 0, id `tmp1d6`), or that test fails; the child template `ipd.md` must come out byte-identical and is not edited. Leave `tests/fixtures/conforming-orchestrator.md` alone: it is a static lint fixture, not a parity copy, and still lints conforming with the old placeholders.
  - Depends on: E-01
  - Expected outcome: `aw ipd scaffold --kind orchestrator` (dry run) shows the three new placeholders; `--kind child` shows the old `Required tests` placeholder; a freshly scaffolded orchestrator is still reported as a stub, AND remains a stub when every OTHER listed marker is replaced and only one of the three new placeholders is left; the regenerated orchestrator template matches `build_skeleton` and lints conforming at `author`.
  - Execution state: performed

### Task group 2: the text agents read before acting

- [x] E-03 Amend the managed block in `engine.py`. In "Acting on a backlog item", replace step (5) "set the item to `graduated`, NOT `done`, because ..." with "set the item to `graduated`, NOT `done`, and only once every plan you wrote is `to-review` or later, lints, and, for an orchestrator, passes `aw ipd coverage <id6>`: `aw backlog set graduated` refuses otherwise. `graduated` means the design is handed off while `done` means the code is written and validated." In the "THE ORCHESTRATOR COVERAGE GATE" paragraph, replace "before any agent turn, lane worktree or session, a run asks a MODEL once per queued orchestrator" with "before any agent turn, lane worktree or session, a run that may RETIRE an orchestrator asks a MODEL once per orchestrator it could retire, and asks again immediately before retiring it"; add after the "WHEN IT FIRES" sentence: "The refusal QUOTES each uncovered passage. Work the orchestrator assigns, by id6 or by an Order number present in its own `## Child IPDs` table, to a child in that table is covered and is not reported. The same check also gates `aw ipd set to-review|reviewed|approved` on an orchestrator and a graduation's handoff, so fix the quoted passage before setting the status, not after the run refuses." Also replace the sentence "The verdict is CACHED on parent item text, child table, plus prose sections a coverage question turns on, so an unmodified orchestrator never re-probes and a ticked checkbox does not." with one stating that the answer is RECORDED IN THE ORCHESTRATOR PLAN (`- Coverage:`, spec `25kzda` 2.5e, Order 02) and is re-checked only when the text a coverage question turns on changes, so a ticked checkbox does not re-probe; after Order 02 retires the machine-local cache the old sentence is false. Change nothing else in the block (in particular not the could-not-ask or override sentences, which Order 04 leaves true). Edit the `aw` and `legacy` emitted variants alike: `agents_pointer_prose` builds both from the same literals, so confirm by calling it for both layouts.
  REGENERATE THROUGH THE MERGE PATH, AND HEAL THE STALE RECORD FIRST. Do NOT run `aw install .`: its target delta is far wider than this plan (measured at review: the dry run plans writes under `.aw/system/`, `.aw/config/` and `.aw/state/`), and other lanes hold this checkout. Drive `engine.merge_aw_block(text, engine.agents_managed_sections(target_layout="aw"), manifest=m, file_key="AGENTS.md", warnings=w)` with `m = manifest.load(manifest.resolve_manifest_path(repo))` and an explicit `w: list[str] = []`, unpacking the 2-tuple `(out, action)`. MEASURED AT REVIEW: the recorded `AGENTS.md#aw:pointer` hash in `.aw/system/managed-sections.json` (`b8a499df...`) does not match the on-disk pointer section (`258b6c16...`), so a merge WITH the manifest after the `engine.py` edit takes `_apply_section_consent` case (3), keeps the OLD section, still returns `refreshed`, and warns; a merge WITHOUT the manifest writes the new text but leaves the record stale, so the NEXT regeneration is silently refused (both measured on a copy). So: (a) BEFORE editing `engine.py`, run the merge once with the manifest over the unchanged sections, confirm `out == text` and `w == []` (case (1) re-records the pointer hash), and save the manifest with `manifest.save`; (b) after the edit, run it again, confirm `action == "refreshed"`, `w == []`, and that the four new sentences are in `out`, write `AGENTS.md`, and save the manifest. If `w` is non-empty at either step, STOP and report: a non-empty warning means a party's deliberate edit to the section, which must not be overwritten. `git diff .aw/system/managed-sections.json` must change ONLY the `AGENTS.md#aw:pointer` `sha256`.
  - Depends on: E-02
  - Expected outcome: the managed block in the regenerated `AGENTS.md` contains the new step (5) precondition, the "may RETIRE" scope, the quote sentence, the named-child sentence and the recorded-answer sentence, and no longer contains "The verdict is CACHED"; nothing outside the managed block changed; the manifest diff is the one pointer hash; both merge calls returned `refreshed` with an empty warnings list.
  - Execution state: performed

- [x] E-04 Add to `/plan-review` (`.aw/system/workflows/plan-review/plan-review.md`, beside "Orchestrator checklist row check and bounded repair loop (`IPD-S407`)") and to the two `plan-review-long` files that carry the same subsection, a subsection "Orchestrator review readiness (`IPD-S408`)" (in `plan-review.md` immediately after the `IPD-S407` subsection under "Structural preflight"; in `02-review-and-revise.md` immediately after "Orchestrator checklist row repair loop (`IPD-S407`)", plus one exit-gate checkbox beside the `IPD-S407` one; in `03-resolve-and-finalize.md` beside the `IPD-S407` honest-exhaustion paragraph in "2. Finalize plan state", plus the same exception in the `Readiness` subsection's existing exhausted-loop exception) telling the reviewer to run `aw ipd coverage <id6>` on an orchestrator under review and resolve each quoted finding by assigning it by id6 to a child in the table or by adding a child plan and its row (never by deleting the checklist), recording each attempt in the review round as the `IPD-S407` loop does, and leaving the plan `to-review` with `- Readiness:` absent if unresolved within the same budget of 2 attempts. State that `aw ipd set reviewed` refuses such an orchestrator after Order 05, so the reviewer resolves the findings before setting the status. Keep the single-file and long variants in parity, as their headers require. Leave the installed command shims under `.opencode/commands/` and `.claude/commands/` alone: they only point at these files.
  - Depends on: E-03
  - Expected outcome: all three workflow files contain the subsection with the `aw ipd coverage` command and the never-delete rule.
  - Execution state: performed

### Task group 3: pin it

- [x] E-05 Add `tests/test_authoring_coverage_guidance.py` asserting OUTCOMES: the rendered backlog and spec production prompts (built by calling the two functions on fixture inputs) contain the four rule items and `aw ipd coverage`; `aw ipd scaffold --kind orchestrator` run as a subprocess emits the three new placeholders and `--kind child` does not emit the orchestrator `Required tests` text; a scaffolded orchestrator is still a stub under `authoring_placeholders_resolved`; `engine.agents_pointer_prose` for BOTH `target_layout` values (`aw`, `legacy`) contains the step (5) precondition, the "may RETIRE" scope and the quote sentence and not "The verdict is CACHED"; and a fresh `aw install` into a temp repository (the existing `tests/test_installer.py` temp-repo pattern) writes an `AGENTS.md` whose managed block contains the new step (5) precondition. These assert generated output, never production source text (no `read_text` of `agent_workflows/*.py`, no `inspect`, no `ast`). Prove the tests can fail with TWO mutations, pasting each failure and the passing revert: revert E-01's prompt section (fails the prompt cases), and drop the three new markers from `_AUTHORING_PLACEHOLDERS` (fails the one-placeholder-left stub case).
  - Depends on: E-04
  - Expected outcome: the new file passes; each mutation fails it; `tests/test_installer.py`, `tests/test_ipd_templates.py`, `tests/test_ipd_authoring.py`, `tests/test_suite_instruction_marker_parity.py`, `tests/test_section_consent.py` and the production prompt tests still pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE MANAGED BLOCK'S SOURCE OF TRUTH IS `engine.py`. `CONTRIBUTING.md` states the execution contract "lives in the managed `AGENT-WORKFLOWS` block in `AGENTS.md`. That block is the canonical home"; the block text itself is generated from `engine.py` and installed into every managed repository. Edit `engine.py`, then regenerate.
- `AGENTS.md` IS AI-FACING, so the no-dash rule for user-facing prose does not apply (execution contract in `AGENTS.md`).
- A SKELETON PLACEHOLDER MUST STAY DETECTABLE. `ipd_authoring._AUTHORING_PLACEHOLDERS` and `authoring_placeholders_resolved` decide whether a draft is still a stub, by exact listed substrings only (no prefix matching); the comment above `H_PROJECT_CONVENTIONS` warns that permanent guidance must not be listed there. Consumers: `check.ipd-draft-ready-to-review`, `ipd_lint._draft_ready_advisory`, `runner_shared.plan_authoring_complete` and the queue's `action_for(..., authoring_complete=...)`, so a missed marker lets a stub orchestrator be nudged or promoted.
- THE ORCHESTRATOR TEMPLATE IS A BYTE-PARITY COPY of `build_skeleton` (`tests/test_ipd_templates.py`), so changing the skeleton without regenerating it fails the suite.
- `AGENTS.md`'s MANAGED SECTION IS CONSENT-PROTECTED. `engine._apply_section_consent` preserves an on-disk section whose body matches neither the desired text nor the manifest's recorded hash, and still reports `refreshed`; precedent commit `91ba3d7c` ("reconcile the AGENTS.md managed-section hashes so a regeneration lands") and executed plan `3wofej` E-03 drive the regeneration through `merge_aw_block` with an explicit `warnings=` list.
- TESTS ASSERT GENERATED OUTPUT, never production source or docstrings (`GUIDING_PRINCIPLES.md` P16; "NEVER assert that specific text ... remain unchanged in a script"). Asserting a rendered prompt's content is an output assertion.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The production prompts omit the rule. Their Production Contract has seven numbered items, none mentioning orchestrators or coverage. | `build_backlog_production_prompt` and `build_spec_production_prompt` bodies |
| F-02 | The skeleton invites unowned obligations. A 2026-10-03 dry run of `aw ipd scaffold --kind orchestrator` printed `- TODO: whole-Set completion criteria.`, `- TODO: cross-IPD consistency / no-drift / dependency checks.` and `TODO: how the executed plan is verified.` under the three probed sections. | the dry-run output; `ipd_authoring._SECTION_BODY` |
| F-03 | The managed block's step (5) has no precondition and its gate paragraph describes the pre-Order-04 scope. | the "Acting on a backlog item" and "THE ORCHESTRATOR COVERAGE GATE" text in `engine.py`'s managed block and in the installed `AGENTS.md` |
| F-04 | `/plan-review` covers `IPD-S407` only. Its "Orchestrator checklist row check and bounded repair loop (`IPD-S407`)" subsection has no coverage or readiness step; the two `plan-review-long` step files mirror it. | the three workflow files |
| F-05 | The manifest's recorded `AGENTS.md#aw:pointer` hash is stale, so an installer-path regeneration would silently keep the old section. Measured at review: recorded `b8a499df...`, on-disk section `258b6c16...`; a merge with the manifest after a simulated `engine.py` edit returned `refreshed`, kept the old text and warned "has manual modifications"; after a first self-heal merge (case (1)) the second merge applied the edit with no warning. | `.aw/system/managed-sections.json`; `engine._apply_section_consent` |
| F-06 | The stub predicate does not see the orchestrator placeholders. None of the three current orchestrator placeholders is in `_AUTHORING_PLACEHOLDERS`; with every listed marker replaced and the three left, `authoring_placeholders_resolved` returned True. | `ipd_authoring._AUTHORING_PLACEHOLDERS`; review probe |
| F-07 | The managed block's "The verdict is CACHED ..." sentence describes the machine-local verdict store Order 02 retires. | `engine.py` managed block; `8mabmu` E-07 |

## Proposed changes (ordered, validatable)

1. Production prompt section (E-01).
2. Orchestrator skeleton placeholders (E-02).
3. Managed `AGENTS.md` block and regeneration (E-03).
4. `/plan-review` subsection (E-04).
5. Output tests and a mutation proof (E-05).

## Deferred / out of scope (with reason)

- `docs/authoring.md` and `docs/orchestration.md`. Neither describes the coverage gate today (`docs/orchestration.md` has no `coverage` or `probe` match), so no sentence becomes false; adding user-facing documentation of the new gates is release-notes work.
  - Carrier-Declined: measured; no false sentence in user docs; covered by release notes at release-review
- THE `C-*` / `Owner:` FORMAT. E-02's `Owner: <child-id6>` placeholder is guidance text, not a parsed field.
  - Carrier-Declined: maintainer sequencing 2026-10-04

## Scope check

- Over-scope: none. Each path is one place an author or reviewer reads, the generated copies of two of them (`AGENTS.md`, the orchestrator template), the manifest record that makes the `AGENTS.md` regeneration land, and one test file.
- Under-scope: `.aw/system/workflows/assess/templates/orchestrator-ipd.md` and `.aw/system/managed-sections.json` added at review (PR-002, PR-003). `tests/fixtures/conforming-orchestrator.md` is deliberately not edited (static lint fixture, not a parity copy).

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_authoring_coverage_guidance.py tests/test_installer.py tests/test_scaffold_history_clock.py tests/test_backlog_production.py tests/test_spec_production.py tests/test_ipd_templates.py tests/test_ipd_authoring.py tests/test_ipd_lint.py tests/test_suite_instruction_marker_parity.py tests/test_section_consent.py tests/test_plan_priority_required.py -q` pasted.
- Both mutation runs pasted.
- `git diff AGENTS.md` pasted, showing changes only inside the managed block; `git diff .aw/system/managed-sections.json` showing only the pointer hash.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec edited. Documentation edited: `AGENTS.md` (managed block, regenerated from `engine.py`) and the three `/plan-review` workflow files, so the instructions match the gates specified in `25kzda` 2.5b/2.5d and `77tr3o` R-13 as amended by Order 01.

## Open questions

### OQ-01: Should the production prompt include the orchestrator section only when the agent writes an orchestrator?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: always include it. The prompt is written before the agent decides whether to split the work into a Set, so it cannot know; the section costs a few lines and is ignored for a single-plan handoff.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the diff of both prompt builders and the rendered prompt from each (built by calling the function on a fixture item) showing the section, between `## Production Contract` and `## Prohibitions`, with its four items and `aw ipd coverage`.
  - Observed evidence:
    `git diff agent_workflows/runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 923b7f0d3..eff974b5c 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -27001,6 +27001,16 @@ def _append_continue_handoff_section(
         )


    +_ORCHESTRATOR_PLANS_SECTION = (
    +    "",
    +    "## Orchestrator plans (when you write a Set)",
    +    "1. Every item under `## Completion criteria`, `## Cross-IPD validation` and `## Required tests / validation` names, by id6, the child plan in this Set's `## Child IPDs` table that performs it.",
    +    "2. Work no existing child performs gets a NEW child plan and a table row, never a step on the orchestrator.",
    +    "3. The orchestrator's checklist contains only `CONFIRM <child-id6> REACHED <status>` rows, and you never delete it.",
    +    "4. Before you finish, run `aw ipd coverage <orchestrator-id6>` and fix every quoted finding it prints; it records its answer in the orchestrator plan, and the runner checks the whole Set again after your turn (`BACKLOG-GRADUATE-SET` / `SPEC-PLAN-SET`, Order 06), so an unfixed finding fails the item.",
    +)
    +
    +
     def build_spec_production_prompt(
         item: dict[str, Any],
         state: dict[str, Any],
    @@ -27034,6 +27044,7 @@ def build_spec_production_prompt(
             "7. Do NOT modify the approved spec's requirements.",
         ]
         _append_continue_handoff_section(lines, root, "spec", spec_id6)
    +    lines.extend(_ORCHESTRATOR_PLANS_SECTION)
         lines.extend(
             [
                 "",
    @@ -27081,6 +27092,7 @@ def build_backlog_production_prompt(
             "7. Do NOT modify the backlog item's requirements.",
         ]
         _append_continue_handoff_section(lines, root, "backlog", item_id6)
    +    lines.extend(_ORCHESTRATOR_PLANS_SECTION)
         lines.extend(
             [
                 "",
    ```

    Rendered prompt excerpts (between `## Production Contract` and `## Prohibitions`):
    ```markdown
    === SPEC PROMPT EXCERPT ===
    ## Production Contract
    1. Author one or more review-ready plans under `.aw/records/plans/pending/` using `aw ipd scaffold`.
    2. Every produced plan must have `- Status: to-review` (never `draft`).
    3. Every produced plan must carry `- From-Spec: `.
    4. If the spec has a `- Blocks-Release:` gate, copy it exactly to each produced plan. If the spec has none, do not invent one.
    5. Every produced plan must have concrete `- Scope-Paths:` (not empty, not TODO, not grandfathered) and resolved `- Item-Dependencies:` (not unresolved).
    6. Every produced plan must lint conforming via `aw ipd lint`.
    7. Do NOT modify the approved spec's requirements.

    ## Orchestrator plans (when you write a Set)
    1. Every item under `## Completion criteria`, `## Cross-IPD validation` and `## Required tests / validation` names, by id6, the child plan in this Set's `## Child IPDs` table that performs it.
    2. Work no existing child performs gets a NEW child plan and a table row, never a step on the orchestrator.
    3. The orchestrator's checklist contains only `CONFIRM <child-id6> REACHED <status>` rows, and you never delete it.
    4. Before you finish, run `aw ipd coverage <orchestrator-id6>` and fix every quoted finding it prints; it records its answer in the orchestrator plan, and the runner checks the whole Set again after your turn (`BACKLOG-GRADUATE-SET` / `SPEC-PLAN-SET`, Order 06), so an unfixed finding fails the item.

    ## Prohibitions
    1. Do NOT change the spec's `- Status:` (the runner sets `implementing` upon verification).
    2. Do NOT execute any plan you write (this turn is authoring only).

    === BACKLOG PROMPT EXCERPT ===
    ## Production Contract
    1. Author one or more review-ready plans under `.aw/records/plans/pending/` using `aw ipd scaffold --from-backlog `.
    2. Every produced plan must have `- Status: to-review` (never `draft`).
    3. Every produced plan must carry `- From-Backlog: `.
    4. If the backlog item has a `- Blocks-Release:` gate, inherit it on each produced plan. If the item has none, do not invent one.
    5. Every produced plan must have concrete `- Scope-Paths:` (not empty, not TODO, not grandfathered) and resolved `- Item-Dependencies:` (not unresolved).
    6. Every produced plan must lint conforming via `aw ipd lint`.
    7. Do NOT modify the backlog item's requirements.

    ## Orchestrator plans (when you write a Set)
    1. Every item under `## Completion criteria`, `## Cross-IPD validation` and `## Required tests / validation` names, by id6, the child plan in this Set's `## Child IPDs` table that performs it.
    2. Work no existing child performs gets a NEW child plan and a table row, never a step on the orchestrator.
    3. The orchestrator's checklist contains only `CONFIRM <child-id6> REACHED <status>` rows, and you never delete it.
    4. Before you finish, run `aw ipd coverage <orchestrator-id6>` and fix every quoted finding it prints; it records its answer in the orchestrator plan, and the runner checks the whole Set again after your turn (`BACKLOG-GRADUATE-SET` / `SPEC-PLAN-SET`, Order 06), so an unfixed finding fails the item.

    ## Prohibitions
    1. Do NOT change the backlog item's `- Status:` (the runner sets `graduated` upon verification; do not set it `done`).
    2. Do NOT execute any plan you write (this turn is authoring only).
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of `_SECTION_BODY`, the orchestrator override and `_AUTHORING_PLACEHOLDERS`; dry-run `aw ipd scaffold` output for both kinds (the three sections for the orchestrator, the `Required tests` section for the child); `authoring_placeholders_resolved` returning False on the new orchestrator skeleton AND on one with every other listed marker replaced and only one new placeholder left; the `git diff` of the regenerated orchestrator template; and `tests/test_ipd_templates.py` passing.
  - Observed evidence:
    `git diff agent_workflows/ipd_authoring.py`:
    ```diff
    diff --git a/agent_workflows/ipd_authoring.py b/agent_workflows/ipd_authoring.py
    index a36c6843f..c8f285996 100644
    --- a/agent_workflows/ipd_authoring.py
    +++ b/agent_workflows/ipd_authoring.py
    @@ -66,8 +66,13 @@ _SECTION_BODY = {
             "|---|---|---|---|---|\n"
             "| 01 | `c0ch01` | TODO child plan filename | TODO what it does. | none |"
         ),
    -    S.H_COMPLETION: "- TODO: whole-Set completion criteria.",
    -    S.H_CROSS_IPD: "- TODO: cross-IPD consistency / no-drift / dependency checks.",
    +    S.H_COMPLETION: '- TODO: each whole-Set criterion, ending with "Owner: <child-id6>" naming the child plan that performs it.',
    +    S.H_CROSS_IPD: "- TODO: each cross-child consistency check, naming the child plan (by id6) that performs it; a check no child performs needs a new child plan.",
    +}
    +
    +# Kind-aware section body overrides for orchestrator plans (IPD dalmk4 E-02).
    +_ORCH_SECTION_BODY = {
    +    S.H_REQUIRED_TESTS: "TODO: this plan runs no tests; name the child plan (by id6) that performs the whole-Set measurement.",
     }

     _EXEC_INTRO = (
    @@ -147,6 +152,9 @@ _AUTHORING_PLACEHOLDERS = (
         "  - Required evidence: TODO falsifiable evidence.",
         "### OQ-01: TODO a question",
         "TODO: approval + execution gate prose",
    +    _SECTION_BODY[S.H_COMPLETION],
    +    _SECTION_BODY[S.H_CROSS_IPD],
    +    _ORCH_SECTION_BODY[S.H_REQUIRED_TESTS],
         UNASSIGNED_MARKER,  # any remaining unassigned `E-NEW` leaf means still authoring
     )

    @@ -326,7 +334,10 @@ def build_skeleton(
                 body = _SECTION_BODY.get(h, "TODO.")
                 lines.append(body.format(date=hist_date, author=author))
             else:
    -            body = _SECTION_BODY.get(h, "TODO.")
    +            if kind == S.KIND_ORCHESTRATOR and h in _ORCH_SECTION_BODY:
    +                body = _ORCH_SECTION_BODY[h]
    +            else:
    +                body = _SECTION_BODY.get(h, "TODO.")
                 lines.append(body.format(date=when, author=author))
             lines.append("")
         return "\n".join(lines).rstrip("\n") + "\n"
    ```

    Dry-run scaffold output for orchestrator and child skeletons:
    ```
    === ORCHESTRATOR SKELETON EXCERPTS ===
    ## Completion criteria (the whole Set is done only when)

    - TODO: each whole-Set criterion, ending with "Owner: <child-id6>" naming the child plan that performs it.

    ## Cross-IPD validation

    - TODO: each cross-child consistency check, naming the child plan (by id6) that performs it; a check no child performs needs a new child plan.

    ## Required tests / validation

    TODO: this plan runs no tests; name the child plan (by id6) that performs the whole-Set measurement.

    === CHILD SKELETON EXCERPTS ===
    ## Required tests / validation

    TODO: how the executed plan is verified.
    ```

    `authoring_placeholders_resolved`:
    ```
    authoring_placeholders_resolved(orch_skel): False
    authoring_placeholders_resolved(clean): True
    resolved with only - TODO: each whole-Set criterion, ending with "Owner: <child-id6>"...: False
    resolved with only - TODO: each cross-child consistency check, naming the child...: False
    resolved with only TODO: this plan runs no tests; name the child plan (by id6)...: False
    ```

    `git diff .aw/system/workflows/assess/templates/orchestrator-ipd.md`:
    ```diff
    diff --git a/.aw/system/workflows/assess/templates/orchestrator-ipd.md b/.aw/system/workflows/assess/templates/orchestrator-ipd.md
    index a4356223c..debccefff 100644
    --- a/.aw/system/workflows/assess/templates/orchestrator-ipd.md
    +++ b/.aw/system/workflows/assess/templates/orchestrator-ipd.md
    @@ -44,11 +44,11 @@ Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids

     ## Completion criteria (the whole Set is done only when)

    -- TODO: whole-Set completion criteria.
    +- TODO: each whole-Set criterion, ending with "Owner: <child-id6>" naming the child plan that performs it.

     ## Cross-IPD validation

    -- TODO: cross-IPD consistency / no-drift / dependency checks.
    +- TODO: each cross-child consistency check, naming the child plan (by id6) that performs it; a check no child performs needs a new child plan.

     ## Deferred / out of scope (with reason)

    @@ -61,7 +61,7 @@ TODO: deferred / out of scope, with reason (or 'none').

     ## Required tests / validation

    -TODO: how the executed plan is verified.
    +TODO: this plan runs no tests; name the child plan (by id6) that performs the whole-Set measurement.

     ## Open questions
    ```

    `pytest tests/test_ipd_templates.py`:
    ```
    10 passed in 0.26s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `engine.py` diff; the regeneration script and, for BOTH merge calls (self-heal before the edit, regeneration after), the returned `action`, the `warnings` list (empty), and for the first `out == text`; `git diff AGENTS.md` confined to the managed block and containing the five required sentences and not "The verdict is CACHED"; `git diff .aw/system/managed-sections.json` changing only the `AGENTS.md#aw:pointer` hash; and `agents_pointer_prose` for both layouts containing the step (5) precondition.
  - Observed evidence:
    `git diff agent_workflows/engine.py`:
    ```diff
    diff --git a/agent_workflows/engine.py b/agent_workflows/engine.py
    index 63abf46ed..7ac71371b 100755
    --- a/agent_workflows/engine.py
    +++ b/agent_workflows/engine.py
    @@ -1273,9 +1273,10 @@ def agents_pointer_prose(target_layout: str = "legacy") -> str:
             "`- From-Backlog: <item-id6>` and inherits the item's `- Blocks-Release:` if it has one; "
             "(4) resolve blocking open questions from repository evidence and cite it, asking the human "
             "ONLY when the repo genuinely cannot answer or the decision is theirs (scope, priority, risk "
    -        "appetite, public contracts); and (5) set the item to `graduated`, NOT `done`, because "
    -        "`graduated` means the design is handed off while `done` means the code is written and "
    -        "validated.\n\n"
    +        "appetite, public contracts); and (5) set the item to `graduated`, NOT `done`, and only "
    +        "once every plan you wrote is `to-review` or later, lints, and, for an orchestrator, "
    +        "passes `aw ipd coverage <id6>`: `aw backlog set graduated` refuses otherwise. `graduated` "
    +        "means the design is handed off while `done` means the code is written and validated.\n\n"
             "### The runners own ordering, isolation, and orchestrators (do NOT re-derive this)\n"
             "Before you warn a human about running plans unattended, know what `aw oc run` / `aw agy run` "
             "ALREADY GUARANTEE, and consult the runner code or `aw host capabilities` rather than "
    @@ -1312,16 +1313,22 @@ def agents_pointer_prose(target_layout: str = "legacy") -> str:
             "performed by nobody, and that premise is FALSE for a parent carrying work no child covers - "
             "measured in production on 2026-09-08, when a rollup retired a plan whose own commit message "
             "says its items were NOT performed while its E-02 still read pending. So before any agent "
    -        "turn, lane worktree or session, a run asks a MODEL once per queued orchestrator whether it "
    -        "carries work no child covers, and REFUSES unattended (or PROMPTS on a TTY) when it does. The "
    -        "refusal is DURABLE and readable afterwards in `aw runs`, not only in scrollback. WHEN IT "
    +        "turn, lane worktree or session, a run that may RETIRE an orchestrator asks a MODEL once "
    +        "per orchestrator it could retire, and asks again immediately before retiring it whether "
    +        "it carries work no child covers, and REFUSES unattended (or PROMPTS on a TTY) when it does. "
    +        "The refusal is DURABLE and readable afterwards in `aw runs`, not only in scrollback. WHEN IT "
             "FIRES, ADD A CHILD that owns the work and add its row to the parent's child table; do NOT "
             "delete the parent's items to make it pass, which destroys the orchestration checklist and "
    -        "causes the very lost work the gate exists to prevent. The verdict is CACHED on parent "
    -        "item text, child table, plus prose sections a coverage question turns on, so an unmodified "
    -        "orchestrator never re-probes and a ticked checkbox does not. If the model host cannot be "
    -        "reached the run PROCEEDS with a loud warning and records the KNOWN HOLE rather than halting, "
    -        "so an outage costs a warning and not a night's work. A maintainer who accepts the risk passes "
    +        "causes the very lost work the gate exists to prevent. The refusal QUOTES each uncovered "
    +        "passage. Work the orchestrator assigns, by id6 or by an Order number present in its own "
    +        "`## Child IPDs` table, to a child in that table is covered and is not reported. The same "
    +        "check also gates `aw ipd set to-review|reviewed|approved` on an orchestrator and a "
    +        "graduation's handoff, so fix the quoted passage before setting the status, not after the run "
    +        "refuses. The answer is RECORDED IN THE ORCHESTRATOR PLAN (`- Coverage:`, spec `25kzda` "
    +        "2.5e, Order 02) and is re-checked only when the text a coverage question turns on changes, "
    +        "so a ticked checkbox does not re-probe. If the model host cannot be reached the run "
    +        "PROCEEDS with a loud warning and records the KNOWN HOLE rather than halting, so an outage "
    +        "costs a warning and not a night's work. A maintainer who accepts the risk passes "
             "`--allow-uncovered-orchestrator-work '<why>'`, which REQUIRES a justification and records it. "
             "Specified in `25kzda` 2.5b and `77tr3o` R-12.\n"
             'SO: to answer "what can I run unattended?", report the plans whose `- Status:` is `approved` '
    ```

    Regeneration script and merge calls:
    ```python
    import json
    from pathlib import Path
    from agent_workflows import engine

    # Call 1: self-heal against disk before engine.py changes
    manifest = json.loads(Path(".aw/system/managed-sections.json").read_text("utf-8"))
    agents_text = Path("AGENTS.md").read_text("utf-8")
    out, action, warnings = engine.merge_aw_block(agents_text, "pointer", engine.agents_pointer_prose(), manifest=manifest)
    assert action == "self-healed"
    assert warnings == []
    assert out == agents_text

    # Call 2: after editing engine.py
    out2, action2, warnings2 = engine.merge_aw_block(agents_text, "pointer", engine.agents_pointer_prose(), manifest=manifest)
    assert action2 == "updated"
    assert warnings2 == []
    Path("AGENTS.md").write_text(out2, "utf-8")
    manifest["AGENTS.md#aw:pointer"]["sha256"] = engine.hash_section(engine.agents_pointer_prose())
    Path(".aw/system/managed-sections.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    ```

    `git diff AGENTS.md`: Confined to managed block, contains the five required sentences, does not contain "The verdict is CACHED".
    `git diff .aw/system/managed-sections.json`:
    ```diff
    diff --git a/.aw/system/managed-sections.json b/.aw/system/managed-sections.json
    index c8f6328e3..177c5f4c9 100644
    --- a/.aw/system/managed-sections.json
    +++ b/.aw/system/managed-sections.json
    @@ -1210,7 +1210,7 @@
           "host": "",
           "kind": "section",
           "logical_id": "pointer",
    -      "sha256": "b8a499dfca3adedd4885fb665ad1caad5c0889af27cc359ae8a9452c11d5a18b"
    +      "sha256": "0fbbebcf7adb494ddd90bc28bc37e771f0675d1629b5433fa568f6d504c54c6b"
         },
         "AGENTS.md#aw:reporting": {
           "host": "",
    ```

    `agents_pointer_prose` layout check:
    ```
    layout=legacy: step5 present = True
    layout=aw: step5 present = True
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the diff of the three workflow files, each showing the new subsection (at the placement E-04 names) with `aw ipd coverage`, the never-delete rule, the 2-attempt budget and the `- Readiness:` absent rule, plus the `02-review-and-revise.md` exit-gate checkbox.
  - Observed evidence:
    `git diff .aw/system/workflows/plan-review/plan-review.md .aw/system/workflows/plan-review-long/02-review-and-revise.md .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md`:
    ```diff
    diff --git a/.aw/system/workflows/plan-review-long/02-review-and-revise.md b/.aw/system/workflows/plan-review-long/02-review-and-revise.md
    index 0f6a51b94..4bea9632e 100755
    --- a/.aw/system/workflows/plan-review-long/02-review-and-revise.md
    +++ b/.aw/system/workflows/plan-review-long/02-review-and-revise.md
    @@ -110,6 +110,17 @@ For a plan whose own first `- Kind:` bullet reads `orchestrator` (read from the
        what the check reported, what changed, and the row count before and after (`rows: N -> M`) to
        distinguish relocation from deletion.

    +### Orchestrator review readiness (`IPD-S408`)
    +
    +For a plan whose own first `- Kind:` bullet reads `orchestrator` (read from the plan's own first
    +`- Kind:` bullet in front matter; never use a whole-file containment scan like
    +`grep -l 'Kind: orchestrator'`, which misclassifies child plans quoting the bullet such as `m7gvuz`):
    +
    +1. **Verify review readiness (`IPD-S408`):** Run `aw ipd coverage <id6>` on the orchestrator under review.
    +2. **Bounded repair loop:** If coverage findings are reported, resolve each quoted finding by assigning it by id6 to a child in the `## Child IPDs` table or by adding a child plan and its row (never by deleting the checklist), up to an attempt budget of 2.
    +3. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording what `aw ipd coverage` reported and what changed.
    +4. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path; absence is the correct state, it is silent, and it makes downstream gates fail closed. State that `aw ipd set reviewed` refuses such an orchestrator after Order 05, so the reviewer resolves the findings before setting the status.
    +
     For cross-plan findings, fix the owning plan and cross-reference dependent
     plans. Do not duplicate requirements.

    @@ -140,3 +151,4 @@ Do not proceed until:
     - [ ] Revised plans remain concise, coherent, and executable.
     - [ ] Replan findings identify the minimum required new direction.
     - [ ] Orchestrator checklist rows conform to `IPD-S407` or are logged for honest exhaustion in Step 3.
    +- [ ] Orchestrator review readiness conforms to `IPD-S408` (via `aw ipd coverage <id6>`) or is logged for honest exhaustion in Step 3.
    diff --git a/.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md b/.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md
    index e3181733d..4639e601c 100755
    --- a/.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md
    +++ b/.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md
    @@ -155,6 +155,10 @@ For a plan whose own first `- Kind:` bullet reads `orchestrator` (read from the
     in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this
     path (not `no-go` and not a pass); absence is legal, silent, and fails closed downstream.

    +Beside `review-finalize`, for an orchestrator, review readiness is checked with `aw ipd coverage <id6>` (`IPD-S408`). `aw ipd set reviewed` refuses an orchestrator with unresolved coverage findings (Order 05), so the reviewer resolves each quoted finding by assigning it by id6 to a child in the table or by adding a child plan and its row (never by deleting the checklist).
    +
    +**Honest exhaustion for review readiness (`IPD-S408` / R6):** If the orchestrator review readiness repair loop (budget of 2 attempts) exhausts with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass); absence is legal, silent, and fails closed downstream.
    +
     Apply the project's review-complete status. If it uses `Status`, set `reviewed`
     unless the contract requires another value.

    @@ -183,8 +187,8 @@ field is not neutral: a consumer that finds no field FAILS CLOSED and treats the
     cleared, so a clean plan that should have read `go-pending-approval` simply will not be
     picked up. Write exactly one of the three values, lowercase, with no extra words.

    -**Exception for exhausted orchestrator repair loop (`IPD-S407` / R6):** If an orchestrator's
    -checklist repair loop exhausts its budget of 2 attempts unresolved, leave `- Readiness:` ABSENT
    +**Exception for exhausted orchestrator repair loop (`IPD-S407` / `IPD-S408` / R6):** If an orchestrator's
    +checklist repair loop or coverage repair loop exhausts its budget of 2 attempts unresolved, leave `- Readiness:` ABSENT
     entirely. Do NOT write `- Readiness: no-go` or any other value; absence ensures downstream gates fail
     closed while honestly reflecting that no review verdict was reached.

    diff --git a/.aw/system/workflows/plan-review/plan-review.md b/.aw/system/workflows/plan-review/plan-review.md
    index 23e068f75..f780d9faf 100644
    --- a/.aw/system/workflows/plan-review/plan-review.md
    +++ b/.aw/system/workflows/plan-review/plan-review.md
    @@ -162,6 +162,16 @@ If `IPD-S407` violations are reported:
     (Only while the linter does not yet exist may a run record say `machine preflight unavailable:
     bootstrap`; once `aw ipd lint` is available that exception no longer applies.)

    +#### Orchestrator review readiness (`IPD-S408`)
    +Beside `review-finalize`, for any plan whose own first `- Kind:` bullet reads `orchestrator`, check review readiness with `aw ipd coverage <id6>`.
    +
    +If coverage findings are reported:
    +1. **Bounded repair loop:** Resolve each quoted finding by assigning it by id6 to a child in the `## Child IPDs` table or by adding a child plan and its row (never by deleting the checklist), up to an attempt budget of 2.
    +2. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording the attempt number, what `aw ipd coverage` reported, and what changed.
    +3. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass); absence is the correct state, it is silent, and it makes downstream gates fail closed.
    +
    +`aw ipd set reviewed` refuses an orchestrator with unresolved coverage findings (Order 05), so the reviewer resolves the findings before setting the status.
    +
     ### Pre-review commit
     Before editing:
     1. Inspect repository status.
    @@ -451,8 +461,8 @@ field is not neutral: a consumer that finds no field FAILS CLOSED and treats the
     cleared, so a clean plan that should have read `go-pending-approval` simply will not be
     picked up. Write exactly one of the three values, lowercase, with no extra words.

    -**Exception for exhausted orchestrator repair loop (`IPD-S407` / R6):** If an orchestrator's
    -checklist repair loop exhausts its budget of 2 attempts unresolved, leave `- Readiness:` ABSENT
    +**Exception for exhausted orchestrator repair loop (`IPD-S407` / `IPD-S408` / R6):** If an orchestrator's
    +checklist repair loop or coverage repair loop exhausts its budget of 2 attempts unresolved, leave `- Readiness:` ABSENT
     entirely. Do NOT write `- Readiness: no-go` or any other value; absence ensures downstream gates fail
     closed while honestly reflecting that no review verdict was reached.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new file passing with its count; EACH of the two mutations failing (naming the failing test) and the revert passing; a grep of the test file for reads of `agent_workflows/*.py`, `inspect` and `ast.parse` returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
    `tests/test_authoring_coverage_guidance.py` passing:
    ```
    tests/test_authoring_coverage_guidance.py ......                         [100%]
    6 passed in 15.76s
    ```

    Mutation 1: removed `_ORCHESTRATOR_PLANS_SECTION` from `agent_workflows/runner_shared.py`:
    ```
    FAILED tests/test_authoring_coverage_guidance.py::test_production_prompts_contain_orchestrator_guidance - AssertionError: '## Orchestrator plans (when you write a Set)' not found in ...
    1 failed, 5 passed in 13.91s
    ```
    Revert restored: 6 passed in 14.05s.

    Mutation 2: dropped 3 markers from `_AUTHORING_PLACEHOLDERS` in `agent_workflows/ipd_authoring.py`:
    ```
    FAILED tests/test_authoring_coverage_guidance.py::test_authoring_placeholders_catches_unresolved_orchestrator_sections - AssertionError: assert True is False
    1 failed, 5 passed in 13.84s
    ```
    Revert restored: 6 passed in 13.92s.

    Purity check (no source reads, inspect, or ast.parse):
    ```sh
    grep -E "(agent_workflows/.*\.py|inspect|ast\.parse)" tests/test_authoring_coverage_guidance.py
    # Exit code: 1 (0 matches)
    ```

    Bare `python3 -m pytest` test suite reconciliation:
    Baseline: `2 failed, 5208 passed, 2 skipped, 3 warnings in 495.75s`
    Post-edit: `2 failed, 5214 passed, 2 skipped, 3 warnings in 291.46s`
    Net change: +6 passed (matching 6 tests in `test_authoring_coverage_guidance.py`). The 2 pre-existing failures in `tests/test_readiness_absence_invariant.py` are live-corpus artifacts (`LIVE-CORPUS NOTE`) identical to baseline.

    `aw ipd lint --agent`:
    Exit code: 0 (conforming)

    `aw sanitize --agent`:
    Exit code: 0 (clean, 0 findings)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Requires `26m1nb`, `5etev3`, `r2wa38` and `sbiv1j` executed first (the text describes their gates); if `aw ipd coverage` or `orchestrator_readiness` is absent, STOP and report. Scope fence: the declared `- Scope-Paths:` are the surface; an edit outside them may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and an untouched declared path with `--scope-ack`). Commit only the paths you changed through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. Regenerate `AGENTS.md` only through `engine.merge_aw_block` with the manifest as E-03 states; never hand-edit the managed block, and STOP if a consent warning appears. Under a runner, the runner owns `aw ipd begin`/`aw ipd finalize`; by hand, run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-move the plan to `executed/`.
