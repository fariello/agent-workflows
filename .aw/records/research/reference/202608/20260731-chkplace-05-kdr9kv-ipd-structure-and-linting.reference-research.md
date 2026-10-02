---
id: kdr9kv
created: 20260802
set: chkplace
order: 05
topic: []
model:
kind: reference-research
status: reference
outcome: adopted
summary: Migrated from 20260731-chkplace-05-kdr9kv-ipd-structure-and-linting.reference-research.md.
consumed-by: []
---
# Specification: IPD structure, stable E-*/V-* mapping, lifecycle state, and deterministic linting

- Date: 2026-08-02
- Status: DRAFT for maintainer approval; not yet an approved convention
- Supersedes for review: `20260802-1904-01-ipd-structure-and-linting.spec.md`
- Origin: checklist-placement and instruction-audit research study
- Implementation state: no IPD has executed against this specification
- Scope: new and nonterminal Implementation Plan Documents (IPDs); legacy terminal IPDs are grandfathered as defined in Section 12

Evidence base: `.agents/docs/research/20260731-checklist-placement/`, containing three independent model reports and a consolidated reconciliation. This specification adopts the study's high-confidence recommendations and makes additional engineering decisions needed to produce an implementable, deterministic contract.

## 1. Purpose and problem statement

The IPD convention places an execution checklist, `## Detailed Implementation Checklist (TODO)`, near the beginning and a validation checklist, `## Validation and cross-check (verify before reporting done)`, near the end. A capable model authoring a real IPD Set moved the execution checklist to the bottom in seven of seven files despite the intended convention.

The best current explanation is an instruction-system defect, not a demonstrated model-attention failure. The convention used relational phrases such as “near the top” and “near the end,” did not enumerate a complete structural contract, did not define the unit of the execution-to-validation mapping, and did not provide deterministic enforcement. A capable model could therefore produce a coherent but unintended structure without violating a precisely stated invariant.

This specification converts deterministic properties into deterministic checks and reserves model or human judgment for semantic questions. The implementation MUST distinguish:

- **Deterministic structure and state:** heading identity and order, identifier syntax and uniqueness, execution-to-validation cardinality, required fields, legal checkbox/result combinations, parseable question status, plan-kind schema, and lifecycle/path consistency.
- **Semantic judgment:** completeness of the plan, whether an action is meaningfully atomic, correctness of proposed changes, adequacy and authenticity of evidence, whether a question is genuinely blocking, and whether a plan is appropriately scoped.

The deterministic checker reduces the modeled defect surface when it runs successfully. It does not make an IPD correct, prevent every possible defect, or replace semantic review.

## 2. Adopted research findings and limits

The following findings control this design:

- The optimal physical placement of the two checklists is unknown. No located study directly tested these IPD layouts in iterative coding-agent execution. Top execution and bottom validation is a defensible provisional default, not a proven optimum.
- Physical placement is a secondary control. Atomic actions, observable expected outcomes, independently inspectable evidence, a distinct validation pass, and rejectable lifecycle gates more directly address false completion.
- “Lost in the middle” is principally a retrieval finding and does not prove where an execution checklist belongs.
- Provider guidance about instruction placement varies by model and task. It supports boundary salience and phase-local reminders, not one universal physical order.
- Execution and validation are distinct semantic states and SHOULD remain separate by default.
- A mutable checklist MUST NOT be duplicated. Short immutable phase instructions MAY be repeated at the relevant boundary.
- A linter can reject modeled structural and state defects. It cannot establish semantic coverage, code correctness, evidence truth, or meaningful atomicity.
- The dissenting proposal to merge execution and validation for weaker models was not supported by direct comparative evidence. A merged-ledger variant remains an experimental possibility, not part of the version 1 contract.

This specification does not assert that checklist placement prevents premature completion, evidence generation forces chain-of-thought, structural linting prevents all drift, or weaker models are always more position-sensitive.

## 3. Normative language and canonical source of truth

The terms `MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative.

One machine-readable IPD schema MUST be the canonical source for:

- supported IPD kinds;
- required and optional headings by kind;
- heading order and permitted optional-section intervals;
- exact checklist heading text;
- front-matter fields and allowed values;
- identifier grammar;
- execution and validation field grammar;
- lint checkpoints and legal state combinations;
- warning thresholds;
- legacy applicability.

Templates, documentation, embedded workflow instructions, and the linter MUST be generated from this schema or tested against it. Duplicated rubric or template content MUST have a parity test. A version label alone is insufficient.

The implementation IPD MAY select the schema's repository path after confirming repository conventions. The selected path MUST then be authoritative and documented; no second independently maintained structural definition is permitted.

## 4. Document parsing and applicability

### 4.1 Markdown parsing

The linter MUST parse Markdown structurally or use an equivalent fence-aware parser. It MUST NOT identify headings or checkboxes with naïve whole-file regular expressions.

For structural checks, the parser MUST ignore apparent headings and task markers inside:

- fenced code blocks;
- indented code blocks;
- YAML or other supported front matter;
- quoted examples when the Markdown parser represents them as block quotations.

Required section headings are top-level H2 nodes outside those constructs. “Immediately after” and “immediately before” refer to adjacency in the sequence of top-level H2 nodes, not physical line adjacency. Content is expected between adjacent H2 headings.

### 4.2 Plan-kind selection

A canonical front-matter field MUST identify the IPD kind. At minimum, the schema MUST distinguish ordinary child IPDs from orchestrator IPDs. The linter MUST select the heading schema from this field and MUST reject a missing or unknown kind for new IPDs.

The ordinary and orchestrator templates MAY have different complete H2 sequences, but both MUST satisfy these invariants:

- the execution checklist heading occurs exactly once and is the next H2 after `## Goal`;
- the validation checklist heading occurs exactly once and is the H2 immediately before `## Approval and execution gate`.

### 4.3 Front matter and H2 order are separate contracts

Front matter is not an H2 section and MUST be validated separately. The ordinary child-IPD H2 sequence is:

1. `## Workflow history`
2. `## Goal`
3. `## Detailed Implementation Checklist (TODO)`
4. `## Project conventions discovered (Step 0)`
5. `## Findings`
6. `## Proposed changes (ordered, validatable)`
7. `## Deferred / out of scope`
8. `## Scope check`
9. `## Required tests / validation`
10. `## Spec / documentation sync`
11. `## Open questions`
12. `## Validation and cross-check (verify before reporting done)`
13. `## Approval and execution gate`

Before implementation, the implementation IPD MUST compare this sequence with the current canonical child template. If `## Project conventions discovered (Step 0)` or any other existing required section is intentionally being removed or renamed, that change MUST be recorded as a separate design decision rather than occurring incidentally through template generation.

The orchestrator sequence MUST be enumerated completely in the canonical schema. “Uses its own order” without an enumerated schema is not sufficient.

Optional H2 sections, if any, MUST be named explicitly and assigned a permitted interval between two required headings. Unenumerated H2 sections MUST produce an error for new IPDs unless the schema explicitly permits extension headings.

## 5. Stable execution and validation identifiers

### 5.1 Identifier grammar

- An execution identifier MUST match `E-[0-9]{2,}`.
- A validation identifier MUST match `V-[0-9]{2,}`.
- Identifiers are scoped to one IPD.
- The initial sequence SHOULD use `E-01`, `E-02`, and so forth.
- More than 99 items remains syntactically representable, although the plan-size warning and semantic review should make such a plan exceptional.
- An identifier is stable once assigned. Reordering an item MUST NOT change its identifier.
- Gaps are legal and MUST NOT trigger renumbering.
- New items receive the next unused numeric suffix greater than the highest suffix previously assigned in that IPD.

### 5.2 Execution checklist grammar

Only executable leaves in `## Detailed Implementation Checklist (TODO)` are checkboxes. Grouping headings and descriptive parent items MUST NOT be checkboxes.

Each executable leaf MUST have this logical shape:

```markdown
- [ ] E-01 <one observable action>
  - Depends on: <comma-separated E-* identifiers or none>
  - Expected outcome: <observable result>
  - Execution state: pending
```

`Depends on:` is optional only when the schema defines its absence as equivalent to `none`. `Expected outcome:` and `Execution state:` are REQUIRED.

Allowed execution states are:

- `pending`: action has not been performed;
- `performed`: action was performed; this does not mean it was validated;
- `blocked`: action cannot currently be performed and the reason is recorded in an indented `Execution note:` field;
- `failed`: the action was attempted but did not complete successfully and the reason is recorded in `Execution note:`.

The execution checkbox and state MUST agree:

| Execution state | Checkbox |
|---|---|
| `pending` | unchecked |
| `performed` | checked |
| `blocked` | unchecked |
| `failed` | unchecked |

`Execution note:` is REQUIRED for `blocked` and `failed` and OPTIONAL otherwise.

### 5.3 Validation checklist grammar and bijection

For every `E-NN`, exactly one `V-NN` MUST exist, and `V-NN` MUST target `E-NN`. Every `V-NN` MUST target an existing execution item. Matching numeric suffixes are the canonical mapping; additional many-to-one or one-to-many mappings are not permitted in version 1.

Multiple validation items MAY cite the same independently captured artifact or test run. The one-to-one row mapping does not require duplicate execution of the same test.

Each validation row MUST have this logical shape:

```markdown
- [ ] V-01 validates E-01
  - Required evidence: <falsifiable evidence criterion authored before approval>
  - Observed evidence:
  - Result: pending
```

Allowed validation results are:

- `pending`: validation has not completed;
- `pass`: required evidence was inspected and supports the expected outcome;
- `blocked`: validation cannot currently be completed and the reason is recorded in `Observed evidence:`;
- `failed`: inspected evidence does not support the expected outcome, with the failure recorded in `Observed evidence:`.

The validation checkbox, result, and evidence MUST agree:

| Result | Checkbox | Observed evidence |
|---|---|---|
| `pending` | unchecked | empty |
| `pass` | checked | nonempty |
| `blocked` | unchecked | nonempty explanation |
| `failed` | unchecked | nonempty failure evidence |

The execution and validation states MUST also agree:

- A validation result of `pass` or `failed` requires the matching execution state to be `performed`.
- A validation result of `blocked` MAY correspond to an execution state of `pending`, `blocked`, `failed`, or `performed`, but the observed-evidence explanation MUST identify the blocking condition.
- A matching execution state of `blocked` or `failed` MUST NOT have validation result `pass`.

### 5.4 Evidence requirements

`Required evidence:` is authored before approval and MUST describe evidence capable of revealing failure, not merely a confirmation instruction. Examples include:

- a diff or repository location showing the intended change;
- a tool-captured command, arguments, exit status, and retained output artifact;
- a test report or structured result file;
- a generated artifact with an independently inspectable path or identifier;
- a documented human observation when tool capture is impossible.

`Observed evidence:` SHOULD point to independently inspectable state. Model-pasted or model-narrated output is not automatically external evidence. When tooling permits, command evidence SHOULD be captured by the tool or wrapper that ran the command and referenced by path, digest, run identifier, or other durable locator.

The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.

### 5.5 Checkboxes outside the two checklist sections

Checkboxes outside the execution and validation sections are governed by their section-specific schema. The linter MUST NOT misclassify approval-gate, reviewer, or other permitted checkboxes as `E-*` or `V-*` items. Inside the execution section, every task-list leaf MUST be an `E-*` item. Inside the validation section, every task-list leaf MUST be a `V-*` item.

## 6. Tool-assisted authoring

The `aw ipd` command group SHOULD provide separate, explicit operations:

- `aw ipd scaffold`: create a new conformant IPD skeleton from the canonical schema and template;
- `aw ipd sync`: assign IDs to new execution leaves, add missing pending validation skeletons, and report inconsistencies without changing existing stable IDs;
- `aw ipd lint`: perform read-only deterministic checks.

### 6.1 Synchronization safety

`aw ipd sync` MUST be non-destructive by default:

- It MUST preserve every existing `E-*` and `V-*` identifier.
- It MUST preserve nonempty `Required evidence:`, `Observed evidence:`, notes, results, and checkbox state.
- It MUST NOT reorder user-authored actions or validation rows unless an explicit safe formatting operation is separately requested.
- It MAY remove a pending `V-*` row automatically only when its matching `E-*` was removed before approval and the validation row contains no observed evidence, nonpending result, or manual content.
- It MUST refuse destructive synchronization after execution has begun.
- If an approved or executing plan requires structural changes, the tool MUST stop and require the plan's existing amendment/re-review workflow, including a workflow-history entry.

Authors MAY write action text manually. They SHOULD use `aw ipd sync` rather than hand-assigning identifiers or copying validation skeletons.

## 7. Blocking-question grammar

Every question under `## Open questions` MUST be represented by an H3 and structured fields:

```markdown
### OQ-01: <question>

- Blocking: yes
- Status: open
- Owner: <person, role, agent, event, or none>
- Resolution or deferral rationale:
```

Allowed values are:

- `Blocking:`: `yes` or `no`;
- `Status:`: `open`, `resolved`, or `deferred`.

State rules:

- `Blocking: yes` and `Status: open` is permitted during authoring and review but rejected at `pre-execution`.
- `Blocking: yes` and `Status: deferred` is invalid.
- `Status: resolved` requires a nonempty `Resolution or deferral rationale:`.
- `Status: deferred` requires `Blocking: no`, a nonempty owner or trigger, and a nonempty rationale.
- `Status: open` with `Blocking: no` MAY remain at execution start if the semantic reviewer confirms that it cannot alter correctness, security, scope, architecture, acceptance criteria, or any current `E-*` or `V-*` item.

The linter checks the declared fields and their consistency. The semantic reviewer decides whether the author's `Blocking:` classification is credible.

If there are no open questions, the section MUST contain one canonical non-question marker defined by the schema, rather than a fabricated `OQ-*` entry.

## 8. Plan-size warning and cohesion exception

The version 1 default warning thresholds are:

- more than 5 task-group H3 sections inside the execution checklist; or
- more than 18 executable `E-*` leaves.

Exceeding either threshold does not automatically invalidate the plan. It requires a size assessment in `## Approval and execution gate`:

```markdown
- Size assessment: standard
- Cohesion rationale: not required
```

Allowed size assessments are:

- `standard`: neither threshold is exceeded;
- `exception`: a threshold is exceeded and the plan remains cohesive enough to keep intact.

For `exception`, `Cohesion rationale:` MUST contain a substantive one-sentence explanation. The linter emits a warning for the exceeded threshold and an error if the required exception rationale is missing or inconsistent. Semantic review determines whether the rationale is adequate or whether the work should become an orchestrated Set.

The thresholds are warnings and review triggers, not targets. Authors MUST NOT pad a small plan to approach them or split a cohesive plan merely to avoid them.

## 9. Lint checkpoints and lifecycle state

### 9.1 Persisted status versus lint checkpoint

The plan's persisted `Status:` and the linter's checkpoint are distinct concepts. `Status:` records the repository lifecycle state. A lint checkpoint specifies the transition or review boundary being evaluated.

The required lint checkpoints are:

- `author`: structural validity while drafting;
- `review-finalize`: readiness to leave review;
- `pre-execution`: readiness to begin execution;
- `pre-transition`: readiness to perform the terminal lifecycle transaction;
- `post-transition`: correctness after that transaction.

The canonical schema MUST map every supported persisted status and directory to the checks safe to run automatically. The implementation MUST preserve the repository's existing status vocabulary unless a separate migration decision changes it.

`aw ipd lint FILE` MAY infer a conservative default check from front matter and path, but it MUST NOT infer that a transition gate is being requested. Gatekeeping calls MUST specify the checkpoint explicitly:

```bash
aw ipd lint --phase pre-execution FILE
aw ipd lint --phase pre-transition FILE
aw ipd lint --phase post-transition FILE
```

An incompatible `Status:`, directory, kind, and requested phase combination MUST be an error.

### 9.2 State rules by checkpoint

| Checkpoint | Minimum state requirements |
|---|---|
| `author` | Required structure is present; IDs and mappings are valid for all authored items; execution may remain `pending`; validation results remain `pending`; placeholders are allowed only where the schema explicitly permits them during drafting. |
| `review-finalize` | No structural placeholders remain; every action has an observable expected outcome; every validation row has nonplaceholder required evidence; the size assessment is consistent; structural question fields are valid. Semantic adequacy is reviewed separately. |
| `pre-execution` | `review-finalize` passes; no declared blocking question remains unresolved; the persisted lifecycle state authorizes execution; no action has an illegal pre-execution state. |
| `pre-transition` | Every current `E-*` is checked with `Execution state: performed`; every `V-*` is checked with `Result: pass`; every `Observed evidence:` is nonempty; no unresolved blocking condition remains; the plan is not already in a terminal directory or status. |
| `post-transition` | `pre-transition` evidence remains valid; terminal status, workflow-history entry, terminal directory, and lifecycle commit agree under repository conventions. |

An item that becomes unnecessary MUST be removed or superseded through the plan's amendment and re-review process. The executor MUST NOT call an incomplete item “unreachable” to pass `pre-transition`.

## 10. Deterministic linter contract

`aw ipd lint` MUST make no model calls, require no network access, and perform no writes.

For a new or migrated IPD, it MUST check at least:

1. front matter parses and required fields have allowed values;
2. plan kind selects a known schema;
3. required H2 headings occur exactly once and in canonical order;
4. optional headings occur only where permitted;
5. the execution heading is the next H2 after `## Goal`;
6. the validation heading is the H2 immediately before `## Approval and execution gate`;
7. execution identifiers and validation identifiers match the grammar and are unique;
8. every `E-*` has exactly one matching `V-*`, and every `V-*` targets its matching `E-*`;
9. task-list items within each checklist section use the correct identifier family;
10. required execution, validation, question, and size-assessment fields exist;
11. checkbox, execution-state, validation-result, and evidence-presence combinations are legal;
12. dependency targets exist, are not self-references, and do not form a detectable cycle;
13. declared question fields and states are structurally consistent for the requested checkpoint;
14. size thresholds and exception fields are consistent;
15. persisted status, directory, plan kind, requested checkpoint, and legacy applicability are compatible;
16. terminal status, history, directory, and lifecycle-commit metadata agree at `post-transition` to the extent repository state makes them deterministically observable;
17. existing Markdown style rules delegated to this command, including the no-em/en-dash rule, are applied only to authored prose outside code, front matter values exempted by schema, and other explicitly excluded constructs.

The linter MAY detect exact prohibited lifecycle commands or reserved markers inside the execution checklist, but it MUST NOT claim semantic certainty that arbitrary prose does or does not describe a lifecycle transition. The template excludes terminal transition from the execution list; semantic review enforces the general prohibition.

Diagnostics SHOULD use stable rule codes and include file and source location, for example:

```text
path/to/plan.md:84:1 IPD-E201 duplicate execution id E-04
```

Recommended exit behavior:

- `0`: no errors; warnings may be present;
- `1`: one or more conformance errors;
- `2`: invocation, parser, schema-loading, or internal-tool failure.

The tool MUST distinguish a conforming result from inability to run. An internal failure MUST never be reported as a passing lint.

### 10.1 Hard boundary

A passing lint means only that the document conforms to the modeled structural and state contract for the requested checkpoint. It does not establish:

- semantic coverage;
- correctness or safety of proposed changes;
- whether an action is meaningfully atomic;
- truth, relevance, independence, or sufficiency of observed evidence;
- correctness of blocking/nonblocking classification;
- successful execution outside deterministically observable repository state.

## 11. Lifecycle gate and terminal transaction

Terminal `Status:` change, workflow-history update, `git mv`, and lifecycle commit MUST NOT be `E-*` or `V-*` items whose completion is required before transition.

The executor MUST run `aw ipd lint --phase pre-transition FILE`. Only after it exits `0` may the workflow perform the terminal transaction:

1. append the required workflow-history entry;
2. set the terminal `Status:`;
3. move the IPD to its required terminal directory with `git mv`;
4. create the required path-scoped lifecycle commit;
5. run `aw ipd lint --phase post-transition MOVED_FILE`;
6. report the lifecycle commit identifier and any post-transition failure.

The transaction SHOULD be implemented so that failure before commit leaves an observable, recoverable state. The workflow MUST NOT report successful terminal transition if the post-transition check fails.

## 12. Review integration and enforcement

Once `aw ipd lint` exists, `plan-review`, `plan-review-long`, and the execution/lifecycle workflows MUST invoke it at their applicable checkpoints. They MUST NOT replace invocation with a prose instruction to “apply the same checks.”

- Structural preflight runs before semantic review.
- A structural error becomes a distinct structural finding and MUST be repaired before semantic review can produce a passing verdict.
- After review edits, `review-finalize` lint runs again.
- Execution fails closed if `pre-execution` lint cannot run or returns nonzero.
- Terminal transition fails closed if `pre-transition` lint cannot run or returns nonzero.
- Post-transition failure is reported as incomplete lifecycle finalization and MUST be repaired; it is not silently treated as success.

During the bootstrap implementation that creates the tool, the implementation IPD MAY use an explicit manual preflight. That exception ends when the linter is available. The review record MUST say `machine preflight unavailable: bootstrap` rather than imply machine verification occurred.

Pre-commit or CI integration MAY be deferred from version 1, provided all authoritative review, execution, and transition workflows invoke the linter unconditionally. Repository hook integration remains recommended defense in depth.

## 13. Rollout and legacy behavior

### 13.1 New and existing nonterminal plans

- Every IPD created after adoption MUST use the new schema.
- Existing nonterminal IPDs MUST be migrated, re-authored, or explicitly quarantined before authoritative review or execution under the new convention.
- Repository-wide lint SHOULD target new and migrated nonterminal IPDs.
- The already drafted, uncommitted research-org IPD Set is re-authored after this IPD-system Set lands, consistent with the maintainer's IPD-system-first sequencing decision.

### 13.2 Grandfathered terminal plans

Existing terminal IPDs are not retrofitted. Repository-wide lint skips them unless explicitly requested.

Direct lint of a grandfathered file MUST behave explicitly rather than silently pass:

- without a legacy flag, report `legacy/not evaluated` and a non-passing informational outcome defined by the CLI contract;
- with an explicit legacy option, run only the reduced legacy checks defined in the canonical schema;
- with an explicit migration option or after manual migration, run the current schema.

Legacy files MUST NOT be described as conforming to the new contract merely because they were skipped.

## 14. Canonical authored example

```markdown
## Goal

<short goal>

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the
action. That mark is not validation.

### Task group 1: <short title>

- [ ] E-01 `<file>` (`<symbol>`): <one observable action>.
  - Depends on: none
  - Expected outcome: <observable result>
  - Execution state: pending

<Project conventions, Findings, Proposed changes, Deferred / out of scope,
Scope check, Required tests / validation, Spec / documentation sync>

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a
`V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: <falsifiable evidence criterion>
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

<approval, execution, pre-transition, and post-transition rules>
```

The canonical no-open-questions marker MUST be defined once in the schema. The example above uses `No open questions.` provisionally.

## 15. Required implementation components

The implementation IPD Set MUST cover:

1. the canonical machine-readable schema and schema tests;
2. ordinary child and orchestrator templates generated from or checked against the schema;
3. `ipd-spec` updates and removal of ambiguous “near” language;
4. `aw ipd scaffold`;
5. non-destructive `aw ipd sync`;
6. read-only `aw ipd lint` with explicit checkpoints;
7. the execution/validation state model and stable-ID rules;
8. structured open-question and size-exception grammar;
9. lifecycle-gate and post-transition fixes;
10. structural-preflight integration into `plan-review`, `plan-review-long`, `review-rubric`, and execution/lifecycle workflows;
11. parity tests for embedded and standalone rubric/report-template content;
12. documentation, DECISIONS pointer, and thin `AGENTS.md` pointer;
13. migration or quarantine of existing nonterminal IPDs;
14. dogfooding against this repository's nonterminal IPDs;
15. tests and fixtures defined in Section 16.

The E-*/V-* convention remains IPD-specific and does not alter the research-org convention directly. The research-org IPD Set is re-authored to this shape after the IPD-system Set lands.

## 16. Required tests and acceptance criteria

The implementation MUST include table-driven fixtures covering at least:

### 16.1 Parser and heading tests

- conforming ordinary and orchestrator plans;
- missing, duplicate, renamed, and out-of-order required headings;
- an apparent H2 inside fenced code, indented code, and block quotation;
- optional headings in allowed and disallowed intervals;
- invalid or missing plan kind;
- front matter containing heading-like text.

### 16.2 Identifier and synchronization tests

- duplicate and malformed IDs;
- missing, duplicate, and orphaned validation mappings;
- more than 99 syntactically valid IDs;
- reordering without renumbering;
- adding an item assigns the next unused suffix;
- gaps remain stable;
- synchronization preserves authored evidence and state;
- destructive synchronization is refused after execution begins;
- removed pending draft item removes only its untouched pending validation skeleton.

### 16.3 State-machine tests

- every legal and illegal execution checkbox/state pair;
- every legal and illegal validation checkbox/result/evidence combination;
- cross-state conflicts between each E and V pair;
- checkpoint-specific placeholder rules;
- `pre-transition` rejects any nonperformed E, nonpassing V, unchecked V, or empty observed evidence;
- `post-transition` checks status/history/path/commit consistency.

### 16.4 Question and size tests

- open blocking question rejected at `pre-execution`;
- resolved blocking question accepted with rationale;
- deferred blocking question rejected;
- deferred nonblocking question requires owner/trigger and rationale;
- size warning at each threshold boundary;
- missing and present exception rationale;
- standard assessment rejected when thresholds are exceeded.

### 16.5 Enforcement and legacy tests

- authoritative workflows fail closed on linter exit `1` or `2`;
- bootstrap-unavailable state is labeled accurately;
- repository scans skip grandfathered terminal files without calling them conforming;
- direct legacy-file invocation reports explicit legacy disposition;
- migrated legacy file is checked under the current schema;
- diagnostics contain stable rule code, file, and source location.

Acceptance requires all tests to pass, parity checks to pass, and dogfood lint to pass for every migrated nonterminal IPD. Semantic review remains a separate acceptance gate.

## 17. Deferred experiment and open implementation details

The controlled authoring/review and execution/false-completion experiment proposed by the research is deferred. Top-execution/bottom-validation remains explicitly provisional and MUST NOT be described as empirically optimal.

The following implementation details may be resolved in the implementation IPD without changing this design:

- exact canonical-schema file path;
- Markdown parsing library;
- precise CLI spelling for legacy and migration options;
- exact mapping from the repository's existing persisted statuses to conservative default lint checks;
- whether pre-commit and CI integration lands in version 1 or a follow-up, provided authoritative workflow invocation is mandatory in version 1.

The following are not open decisions:

- IDs are stable and are never automatically renumbered.
- Explicit `--phase` is required at transition gates.
- The linter is read-only and fail-closed in authoritative workflows.
- Execution and validation remain separate physical sections in version 1.
- The mutable checklist is never duplicated.
- Semantic review remains mandatory.

## 18. Approval and next step

This specification is paused for human approval. After approval, author an orchestrated IPD Set for the components in Section 15. Do not begin implementation before that Set is reviewed and approved under the applicable bootstrap rules.

After the IPD-system Set lands:

1. migrate or re-author applicable nonterminal IPDs;
2. re-author the research-org Set to the new structure;
3. run dogfood lint and semantic review;
4. record adoption in DECISIONS and the relevant documentation;
5. consider the deferred controlled experiment if empirical layout optimization becomes valuable.
