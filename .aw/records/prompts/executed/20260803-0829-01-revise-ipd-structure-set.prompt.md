# Revise and harden the `ipd-structure` specification and IPD Set

You are a senior software and systems architect, specification engineer, deterministic-tooling designer, and expert in agent-executable Implementation Plan Documents (IPDs). You are working in the `fariello/agent-workflows` repository.

Your assignment is to revise the IPD-structure specification and the complete `20260802-1944-*` IPD Set so that they are internally consistent, executable by another coding agent, faithful to the repository's actual conventions, and capable of bootstrapping the deterministic IPD linter without circularity or hidden design gaps.

This is a document-and-plan revision task. Modify the specification, the orchestrator, and the six child IPDs as needed. Do not implement the schema, parser, linter, authoring commands, workflow enforcement, or migration described by the IPDs. Do not execute the IPDs. Do not mark the specification approved, approve any IPD, or claim human decisions that are not documented. Obey all repository-level instructions. Never push. If the repository requires a commit for this editing task, use only path-scoped commits containing files changed by this task.

## Primary files

Read these files completely before editing:

1. `.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md`
2. `.agents/plans/pending/20260802-1944-00-ipd-structure-orchestrator.md`
3. `.agents/plans/pending/20260802-1944-01-canonical-ipd-schema.md`
4. `.agents/plans/pending/20260802-1944-02-ipd-lint-parser-and-state-machine.md`
5. `.agents/plans/pending/20260802-1944-03-ipd-scaffold-and-sync.md`
6. `.agents/plans/pending/20260802-1944-04-templates-and-spec-and-defect-fixes.md`
7. `.agents/plans/pending/20260802-1944-05-review-preflight-and-enforcement.md`
8. `.agents/plans/pending/20260802-1944-06-migrate-nonterminal-and-adopt.md`

Also inspect all live sources that currently define or repeat IPD structure, lifecycle, templates, or generated instructions, including at least:

- `AGENTS.md`
- `.agents/plans/README.md`
- `.agents/workflows/templates/plans-README.md`
- `.agents/workflows/assess/templates/ipd.md`
- `.agents/workflows/assess/templates/orchestrator-ipd.md`
- `.agents/workflows/plan-review/plan-review.md`
- every file under `.agents/workflows/plan-review-long/`
- `agent_workflows/engine.py`, especially `agents_pointer_prose()`
- `agent_workflows/plans.py`
- `agent_workflows/cli.py`
- `DECISIONS.md`
- the current inventory of nonterminal and terminal IPDs
- any actual workflow that governs execution or terminal lifecycle transition

Search rather than assume. If a referenced file or authoritative workflow does not exist, treat that as a design fact the revised plans must address explicitly.

## Current reviewed baseline and valid partial revisions

The current repository includes a `/plan-review` revision in commits `670a067` and `6395496`. Inspect the current branch rather than assuming those commits are still HEAD. Preserve the valid portions of that work:

- Order 04 now correctly depends on Orders 01, 02, and 03 because its validation invokes the Order-02 linter.
- Orders 01 and 04 now explicitly require a fully enumerated orchestrator heading schema.
- Order 02 now explicitly owns direct grandfathered-file disposition, reduced `--legacy` checking, stable diagnostics, and related tests.

Do not duplicate, remove, or weaken those valid corrections. They are only partial corrections and do not establish that the Set is structurally sound.

All seven IPDs are now marked `Status: reviewed`. Their appended `/plan-review` history claims that a bootstrap manual preflight found no blocker or high-severity defect and that the Set is ready for human approval. Treat those statements as historical claims, not as proof. In particular, the actual Order-00 H2 sequence still places `## Detailed Implementation Checklist (TODO)` near the bottom even though newly added prose claims that it appears immediately after `## Goal`. The specification also remains marked as a draft while the IPDs call it approved.

Mechanically extract and inspect the real H2 sequence of every file. Never accept prose describing a file's structure as evidence of its actual structure.

## Governing objectives

The revised artifacts must achieve all of the following:

1. One exact, machine-checkable IPD structural contract.
2. No contradiction among the specification, schema plan, linter plan, authoring-tool plan, templates, review workflows, lifecycle instructions, migration plan, or bootstrap IPDs.
3. A bootstrap sequence in which the linter created by Order 02 accepts every later unexecuted child at its applicable checkpoint.
4. Stable `E-*` and `V-*` identity that remains valid after reordering, gaps, and permitted pre-approval deletion.
5. Fail-closed structural enforcement while preserving a hard boundary between deterministic checks and semantic review.
6. Exact coverage of the specification's required tests and acceptance criteria, not broad phrases that allow mandatory cases to be missed.
7. Proportionate implementation. Do not turn the schema into a heavyweight schema-engine project.
8. Small, cohesive child IPDs with explicit scope fences, exact affected files or bounded discovery instructions, observable outcomes, and independently inspectable validation evidence.

## Required corrections

Address every item below. Do not merely mention these issues in a report; revise the artifacts so the issues are resolved.

### 1. Make the bootstrap IPDs conform to their own proposed contract

The current specification enumerates exact child headings such as `## Findings` and `## Deferred / out of scope`, while the live template and child IPDs use `## Findings (drivers)` and `## Deferred / out of scope (with reason)`.

The specification also says that, for both child and orchestrator IPDs, the execution checklist is the next top-level H2 after `## Goal`. The current orchestrator template and Order-00 IPD place the execution checklist near the bottom.

Choose one exact heading contract and make the specification, bootstrap IPDs, schema plan, and intended template changes agree. Prefer preserving useful established live-template heading names when that does not weaken determinism. Move the orchestrator execution checklist immediately after `## Goal` unless you identify and document a stronger invariant. Resolve whether child and orchestrator validation headings are identical or intentionally kind-specific; do not leave this implicit.

Manually conform all seven bootstrap IPDs to the chosen new structure. Do not rely on the not-yet-created linter to repair the files that create it.

### 2. Define the metadata syntax precisely

The repository's IPDs currently use a bullet metadata block after the H1, not YAML front matter. The specification and plans ambiguously call this “front matter,” while also discussing YAML front matter as a Markdown construct the parser must ignore.

Define the canonical IPD metadata block precisely, including:

- its physical location;
- field syntax;
- required, optional, and conditional fields;
- duplicate and unknown-field behavior;
- `Kind`, `Status`, `Approval`, `Set`, and `Order` rules;
- all existing readiness statuses, including `auto-approved` if it remains supported;
- permitted path/status/kind/order combinations;
- the orchestrator's `Order: 0` exception to any general 1-based child-order rule.

Prefer retaining the existing bullet metadata format unless repository evidence justifies migration. Use “YAML front matter” only for actual YAML front matter.

### 3. Make stable-ID allocation enforceable after deletion

The current design permits a pre-approval execution item and untouched validation skeleton to be removed. Once the highest assigned ID is deleted, the remaining document does not reveal that the suffix was previously used. A later sync can therefore reuse it, violating the stable and monotonically increasing identity rule.

Choose and specify a lightweight persistent mechanism, such as an allocation watermark or explicit tombstone, that prevents reuse of any previously assigned suffix. Include it in the canonical schema, parser/linter behavior where applicable, `sync` behavior, templates or metadata where applicable, and tests. Explicitly test deleting the highest assigned item and then adding another item.

Do not weaken stable identity merely to avoid recording allocation history.

### 4. Define quarantine before implementing the linter

Order 06 currently defers the quarantine mechanism until migration even though Orders 01 and 02 must define and implement repository-scan applicability. It also promises that all nonterminal IPDs pass or are quarantined while leaving the research-org Set pending and intentionally not re-authored until after this Set.

Define quarantine semantics in the specification and Order 01, implementable behavior in Order 02, and application of that already-defined behavior in Order 06. Specify:

- how quarantine is represented;
- which plans may be quarantined and who authorizes it;
- whether the plan remains in `pending/` or moves;
- how direct lint behaves;
- how repository-wide lint reports it;
- whether the result is passing, nonpassing informational, warning, or error;
- the recorded reason, owner/trigger, and expiry or follow-up condition;
- how the research-org Set is handled during this bootstrap.

Do not silently skip quarantined files or describe them as conforming.

### 5. Eliminate or parity-check every duplicated structural instruction

The old relational and size language is repeated in generated and source documents, including `AGENTS.md`, `agent_workflows/engine.py`, the plans README and its template, and the current IPD templates.

Revise Orders 04 through 06 so every relevant generated file and generator/template source is explicitly covered. Replace the old always-loaded structural prose with a thin pointer to the authoritative spec and `aw ipd` commands; do not merely add a new line while leaving the old independent contract in place.

Specify which content is generated, which is hand-maintained, and which parity tests prevent drift. Include both sides of every generated-source relationship in scope and validation.

### 6. Identify the authoritative execution and lifecycle enforcement mechanism

Order 05 refers vaguely to “the execution/lifecycle workflow docs.” Determine what actually exists. If there is no authoritative general IPD execution/transition workflow, the revised design must explicitly choose whether to create one, introduce a dedicated transactional command, or enforce the gates through specifically named existing mechanisms.

Name the exact files to create or modify, the authoritative entry point, each lint checkpoint it invokes, and how exit codes `1` and `2` fail closed. Specify recovery behavior when failure occurs before or after the lifecycle commit. Do not leave a required enforcement path as discovery-time improvisation.

### 7. Make all mandatory acceptance cases explicit

Compare the specification's full required-test and acceptance sections against the execution and validation items in Orders 01 through 06. Add explicit coverage for every case, including at least:

- conforming child and orchestrator plans;
- missing, duplicate, renamed, and out-of-order headings;
- headings and checkboxes inside fenced code, indented code, block quotations, YAML front matter, and the canonical bullet metadata block;
- optional headings in allowed and forbidden intervals;
- invalid or missing kind and metadata fields;
- malformed, duplicate, missing, and orphaned identifiers;
- more than 99 syntactically valid identifiers;
- stable gaps, reordering, highest-ID deletion, and next-ID allocation without reuse;
- preservation of authored state and evidence during sync;
- default dry-run or preview behavior and explicit apply behavior for every writing command;
- all legal and illegal execution checkbox/state combinations;
- all legal and illegal validation checkbox/result/evidence combinations;
- all E/V cross-state conflicts;
- every checkpoint, including full `post-transition` status/history/path/commit consistency;
- all blocking-question and size-threshold boundaries;
- every supported persisted status, including `auto-approved` if retained;
- linter exit `0`, `1`, and `2` and fail-closed workflow behavior for `1` and `2`;
- diagnostics containing stable code, path, line, and column;
- direct grandfathered-file invocation without a legacy option;
- explicit reduced legacy checking;
- migrated legacy-file checking under the current schema;
- quarantine behavior;
- no-em/en-dash checking only in authored prose, with code and every intended exempt construct tested;
- intentionally desynchronized and missing dependency/template parity fixtures;
- repository dogfood that distinguishes conforming, quarantined, grandfathered, and erroneous plans without calling skipped files conforming.

Do not bury these cases solely inside phrases such as “checkpoint cases,” “legacy rules,” or “full state tests.” Group them sensibly, but make coverage auditable from the IPDs.

### 8. Resolve the approval-state contradiction truthfully

The specification currently says it is a draft for maintainer approval, while the orchestrator describes it as approved and maintainer-adopted.

Inspect the repository evidence. Do not infer or fabricate human approval. If explicit approval is not recorded, describe the document consistently as the maintainer-adopted working specification pending formal approval, and make approval of the specification an explicit prerequisite to executing the Set. If explicit approval is recorded, cite it and update the status/provenance consistently.

### 9. Preserve the deterministic-versus-semantic boundary

The linter may check field presence, grammar, recognized placeholders, state consistency, and other modeled properties. It cannot determine whether an action is meaningfully atomic, an expected outcome is genuinely observable, evidence is falsifiable or sufficient, a question is truthfully nonblocking, or the implementation is correct.

Revise Orders 02 and 05 so every checkpoint clearly separates deterministic lint requirements from semantic reviewer responsibilities. Do not let `review-finalize` or any help text overclaim semantic certainty.

### 10. Harden authoring-command safety

Make the writing behavior of `aw ipd scaffold` and `aw ipd sync` explicit rather than leaving it in discovery notes. Specify default preview/dry-run behavior, explicit apply behavior, overwrite refusal, atomic or recoverable writes, preservation rules, refusal after execution begins, actionable diagnostics, and exit codes. Add matching execution and validation items.

### 11. Correct the post-review lifecycle state without rewriting history

The current `/plan-review` entries are part of append-only workflow history. Do not delete or rewrite them merely because this deeper review found defects they missed. Instead:

1. Follow the repository's actual amendment and re-review convention if one exists.
2. Append a dated corrective workflow-history entry explaining that substantive post-review structural revisions were required and that the earlier manual-preflight verdict is superseded for readiness purposes.
3. Return every substantively revised IPD to `Status: to-review`, or the repository-defined equivalent that truthfully requires a fresh review. Do not leave a materially changed plan marked `reviewed` solely because an earlier version was reviewed.
4. Require a new independent `/plan-review` after the revisions. The revising agent must not review or approve its own substantive revision unless repository policy explicitly permits that workflow and records the distinction.
5. Do not change any plan to `approved`; human approval remains separate.

If repository policy requires a different readiness transition, cite the exact rule and apply it consistently across the Set.

## Revision standards

For every revised IPD:

1. Preserve the ordered Set unless a change is necessary to eliminate a dependency or bootstrap defect.
2. Keep each child within the stated size thresholds or provide a real cohesion exception.
3. Use stable `E-*`/`V-*` mappings with one executable leaf per observable action.
4. Put exact file paths and symbols in checklist items when known.
5. Where a path genuinely cannot be known until execution, bound discovery tightly and specify the decision rule and permitted file class.
6. Give every `E-*` an observable expected outcome.
7. Give every `V-*` falsifiable required evidence that could reveal failure.
8. Keep implementation and validation distinct.
9. Do not include terminal lifecycle transition as an `E-*` or `V-*` item.
10. Keep nonblocking implementation choices open only when the plan supplies sufficient constraints and decision criteria for another competent agent to decide safely.
11. Do not use an open question to postpone a contract needed by an earlier child.
12. Preserve the repository's no-em/en-dash rule in authored Markdown.

## Required working procedure

1. Inspect the current repository and record the actual structural/lifecycle sources, current nonterminal inventory, plan statuses, and latest workflow-history entries.
2. Build a requirements-to-IPD coverage matrix privately or in a temporary working artifact. Map every normative specification requirement and acceptance case to a specific `E-*` and `V-*` item.
3. Identify contradictions, dependency inversions, unspecified authoritative paths, and requirements mentioned only in prose.
4. Revise the specification first so it states one coherent contract.
5. Revise Order 00 and Orders 01 through 06 to implement that exact contract in a valid dependency order.
6. Manually perform the bootstrap structural preflight on every revised IPD. Generate and retain a mechanical H2-sequence listing for each file; then check exact H2 order, metadata, E/V bijection, dependencies, question grammar, size assessment, scope boundaries, and gate consistency. A prose assertion that a heading is correctly placed is not evidence.
7. Cross-check the Set against every required implementation component and every acceptance case in the revised specification.
8. Confirm that the specification itself has a nonempty, relevant diff. If the contract needed correction but only the IPDs changed, the assignment is incomplete.
9. Inspect the final diff for accidental implementation work, unrelated changes, contradictions, stale terminology, unsupported approval claims, and prohibited em/en dashes.
10. Update readiness status and append corrective workflow history as required by Correction 11.
11. Run relevant existing documentation or repository tests only if they can validate these document revisions without implementing the pending plans. Paste actual output for anything claimed to pass.

## Completion criteria

Do not report completion unless all of the following are true:

- The specification contains one internally consistent contract.
- The specification has a nonempty, relevant diff unless inspection proves, with cited evidence, that no specification correction was necessary.
- All seven bootstrap IPDs manually conform to that contract.
- Order 02 can be implemented without inventing quarantine, metadata, legacy, checkpoint, or stable-ID semantics.
- Orders 03 through 06 would pass the proposed linter after Order 02 lands, subject only to normal lifecycle-state progression.
- Every specification requirement and acceptance case maps to an explicit execution and validation item.
- Every affected generated/source instruction pair is covered by an edit and parity strategy.
- The authoritative execution/transition enforcement path is named and fully scoped.
- The research-org Set has an explicit, truthful bootstrap disposition.
- The approval status is truthful and consistent.
- Every substantively revised IPD has truthful readiness status, an append-only corrective history entry, and an explicit requirement for fresh independent review.
- No product implementation described by the IPDs was performed.

## Final response

Return a concise but complete report containing:

1. the overall result: revised successfully, revised with blockers, or unable to revise;
2. every file changed;
3. the key contract decisions made, especially headings, metadata syntax, ID watermark/tombstone, quarantine, legacy behavior, and lifecycle enforcement;
4. any Set/dependency changes and why;
5. the mechanical H2-sequence listing and manual bootstrap-preflight result for each of the seven IPDs;
6. the requirements/acceptance coverage result and any remaining gap;
7. actual output from every command or test claimed to pass;
8. every readiness-status and workflow-history change, including how the earlier `/plan-review` verdict was preserved but superseded for readiness;
9. every unresolved decision requiring human approval;
10. confirmation that no implementation IPD was executed and nothing was pushed.

If a required correction depends on a human policy choice that cannot safely be inferred, make all noncontroversial revisions, leave the affected item explicitly blocked, and ask one self-contained decision question. Do not silently choose a new lifecycle policy or claim approval.
