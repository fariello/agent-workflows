# Specification: IPD structure, stable E-*/V-* mapping, lifecycle state, and deterministic linting

- Date: 2026-08-02
- Status: implemented
- Canonical: true
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us), original draft
- Revised by: an external gpt-5.6 review (revision + change-rationale filed under the research bundle below). The maintainer asked to LOOK AT this gpt-5.6-revised draft; the maintainer has NOT formally approved it and has NOT adopted it as the working spec. It remains a draft pending maintainer review and approval.
- Origin: checklist-placement and instruction-audit research study
- Implementation state: no IPD has executed against this specification. Formal maintainer approval of THIS specification is an explicit prerequisite to executing the implementation IPD Set (see Section 18).
- Scope: new and nonterminal Implementation Plan Documents (IPDs); legacy terminal IPDs are grandfathered as defined in Section 13

Evidence base: `.agents/docs/research/20260731-checklist-placement/`, containing three independent model reports, a consolidated reconciliation, and the gpt-5.6 revision + change-rationale that produced this version. This draft takes up the study's high-confidence recommendations and makes additional engineering decisions needed to produce an implementable, deterministic contract, subject to maintainer review.

Maintainer scope caveats applied to the implementation IPD Set (not open design questions, but boundaries on how far to go):

- The "one canonical machine-readable schema" of Section 3 is a strong SHOULD and a direction, NOT a mandate to build a heavyweight schema-and-generator subsystem if a proportionate mechanism (for example one shared constants module plus parity tests) achieves single-source-of-truth. The implementation IPD chooses the lightest mechanism that prevents cross-file drift; it MUST NOT balloon the Set into a schema-engine project.
- The canonical H2 sequence in Section 4.3 was VERIFIED against the current child template (`.agents/workflows/assess/templates/ipd.md`) on 2026-08-02 and matches it, including `## Project conventions discovered (Step 0)` which the original draft had dropped. The implementation IPD's discovery step MUST re-confirm the live template order at execution time before generating anything.

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
- metadata-block fields and allowed values (see Section 4.4);
- identifier grammar;
- the E-* allocation watermark field and its rules (see Section 5.6);
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

A canonical metadata-block field (`- Kind:`, see Section 4.4) MUST identify the IPD kind. At minimum, the schema MUST distinguish ordinary child IPDs from orchestrator IPDs. The linter MUST select the heading schema from this field and MUST reject a missing or unknown kind for new IPDs.

The ordinary and orchestrator templates have different complete H2 sequences (both fully enumerated in Section 4.3), but both MUST satisfy these invariants:

- the execution checklist heading occurs exactly once and is the next H2 after `## Goal`;
- the validation checklist heading occurs exactly once and is the H2 immediately before `## Approval and execution gate`.

Both invariants apply to the orchestrator kind as well as the child kind. The orchestrator's coordination sections (`## Child IPDs, sequence, and dependencies`, `## Completion criteria`, `## Cross-IPD validation`) follow the execution checklist, not precede it.

### 4.3 The metadata block and H2 order are separate contracts

The metadata block (Section 4.4) is not an H2 section and MUST be validated separately. Both H2 sequences below match the live templates verified on 2026-08-02 (`.agents/workflows/assess/templates/ipd.md` and `.agents/workflows/assess/templates/orchestrator-ipd.md`), except that the orchestrator's execution checklist is moved to immediately after `## Goal` to satisfy the Section 4.2 invariant (the live orchestrator template currently places it near the bottom, a defect the implementation Set repairs; see Order 04).

The ordinary child-IPD H2 sequence is:

1. `## Workflow history`
2. `## Goal`
3. `## Detailed Implementation Checklist (TODO)`
4. `## Project conventions discovered (Step 0)`
5. `## Findings`
6. `## Proposed changes (ordered, validatable)`
7. `## Deferred / out of scope (with reason)`
8. `## Scope check`
9. `## Required tests / validation`
10. `## Spec / documentation sync`
11. `## Open questions`
12. `## Validation and cross-check (verify before reporting done)`
13. `## Approval and execution gate`

The orchestrator-IPD H2 sequence is:

1. `## Workflow history`
2. `## Goal`
3. `## Detailed Implementation Checklist (TODO)`
4. `## Child IPDs, sequence, and dependencies`
5. `## Completion criteria (the whole Set is done only when)`
6. `## Cross-IPD validation`
7. `## Deferred / out of scope (with reason)`
8. `## Scope check`
9. `## Required tests / validation`
10. `## Open questions`
11. `## Validation and cross-check (verify before reporting the Set complete)`
12. `## Approval and execution gate`

Heading names are the live-template names, chosen as the single exact contract for both spec and templates: `## Findings` (bare), `## Deferred / out of scope (with reason)`, `## Project conventions discovered (Step 0)`. The child and orchestrator validation headings are intentionally kind-specific: the child uses `## Validation and cross-check (verify before reporting done)` and the orchestrator uses `## Validation and cross-check (verify before reporting the Set complete)`. The linter selects the correct validation-heading text by kind. Both are the H2 immediately before `## Approval and execution gate`.

The orchestrator omits `## Findings`, `## Proposed changes (ordered, validatable)`, `## Spec / documentation sync`, and `## Project conventions discovered (Step 0)` (it changes no product files itself) and adds the three coordination sections. Both sequences are enumerated completely in the canonical schema; "uses its own order" without an enumerated schema is not sufficient.

Before implementation, the implementation IPD MUST compare both sequences with the current canonical templates. Any intentional removal or rename of an existing required section MUST be recorded as a separate design decision rather than occurring incidentally through template generation. Moving the orchestrator execution checklist to immediately after `## Goal` is such a recorded decision (Order 04).

Optional H2 sections, if any, MUST be named explicitly and assigned a permitted interval between two required headings. Unenumerated H2 sections MUST produce an error for new IPDs unless the schema explicitly permits extension headings.

### 4.4 The metadata block

The repository's IPDs carry a bullet-list metadata block, NOT YAML front matter. This specification retains the bullet metadata block; repository evidence (every tracked IPD and both live templates) does not justify migrating to YAML. The term "YAML front matter" in this specification refers ONLY to actual YAML front matter, which is a Markdown construct the parser ignores for structural checks (Section 4.1); the parser MUST NOT treat the bullet metadata block as YAML.

Physical location: the metadata block is the contiguous run of top-level `- Field: value` bullet lines immediately following the H1 title and preceding the first H2 (`## Workflow history`). An HTML comment block MAY follow the metadata block before the first H2 without breaking it.

Field syntax: one field per line, `- <Field>: <value>`, `<Field>` in the exact case shown below. A field appearing more than once is a duplicate-field error. A `- <Field>:` line whose `<Field>` is not a recognized field is an unknown-field error for new IPDs unless the schema explicitly permits extension fields.

Required fields (all IPDs): `Date`, `Kind`, `Concern`, `Scope`, `Status`, `Author`.

Optional field (all IPDs): `Highest E allocated` (the allocation watermark, Section 5.6; REQUIRED once any `E-*` has been assigned).

Recognized-but-optional field (all IPDs): `Scope-Paths` (Section 4.5) is a recognized field that is NOT in the always-required set; its requirement is CONDITIONAL at the ready-to-execute lint gate (Section 9.2), not at the always-on `author` metadata check.

Conditional fields:

- `Set` and `Order` are REQUIRED together when the IPD belongs to an ordered Set and MUST both be absent otherwise; one present without the other is an error.
- `Approval` is REQUIRED when and only when `Status: approved`; it records the human sign-off (for example `approved by <name> <date>`). It MUST be absent for every other status.
- `Quarantine`, `Quarantine owner`, and `Quarantine follow-up` are REQUIRED together on a quarantined nonterminal plan (Section 13.3) and MUST all be absent otherwise; any one present without the other two is an error.
- `Scope-Paths` is REQUIRED at the `pre-execution` checkpoint and for any plan whose `Status` is at the ready-to-execute tier (`approved`/`auto-approved`); it is OPTIONAL at every earlier drafting/review phase and on terminal (grandfathered) records. See Section 4.5 for its grammar and Section 9.2 for the checkpoint rule.

Field rules:

- `Kind`: one of `child` or `orchestrator`. Missing or unknown kind is an error for new IPDs.
- `Status`: one of the recognized readiness values (Section 9.1); it is the single source of truth for readiness. Directories carry disposition; `Status` carries readiness.
- `Set`: a lowercase-kebab identifier shared by the ordered Set.
- `Order`: an integer. For `Kind: orchestrator`, `Order` MUST be `0` (the orchestrator exception to the otherwise 1-based child rule). For `Kind: child`, `Order` MUST be an integer `>= 1`. An orchestrator with `Order` other than `0`, or a child with `Order: 0` or a non-positive `Order`, is an error.

Permitted path/status/kind/order combinations:

- A pre-terminal `Status` (Section 9.1) requires the file to live under `.agents/plans/pending/` (or the standing `reusable/` directory for `Status: reusable`).
- A terminal `Status` (`executed`, `superseded`, `not-executed`) requires the file to live in the matching terminal directory; `Status` mirrors the directory.
- `Kind: orchestrator` requires `Order: 0`; `Kind: child` requires `Order >= 1`.
- Any combination of persisted `Status`, directory, kind, and requested lint checkpoint that the schema does not permit MUST be an error (Section 9.1).

The metadata block is validated separately from the H2 order. A metadata-block error and an H2-order error are distinct diagnostics.

### 4.5 The `Scope-Paths` allowlist (machine-readable declared scope)

`Scope-Paths` is a recognized-but-optional metadata field that declares, in a machine-comparable form, the repo-relative paths a plan is permitted to change. Free-form `- Scope:` prose is not comparable against the actually-changed paths, so an executor can silently expand file scope and no deterministic check catches it. `Scope-Paths` is the substrate the finalize transaction (the `aw ipd finalize` two-way scope reconciliation) compares against the real changed paths.

Value grammar. The `Scope-Paths` value is EITHER the reserved sentinel `grandfathered` OR a comma-separated allowlist of repo-relative literal paths and bounded pathspecs:

- Repo-relative only: an absolute path (leading `/` or `\`) or a Windows drive/UNC path is an error.
- No parent escape: any `..` path segment is an error (a plan cannot scope outside the repo).
- No repo-wide blast radius: a bare `*` or `**`, a root-level glob (a first segment of `*`/`**`, or a single-segment filename glob such as `*.py` at the repo root), and the repo root itself (`.`, `./`, `/`) are errors.
- Bounded pathspecs are allowed: an entry whose leading segment is a concrete directory bounds the blast radius, so `tests/`, `agent_workflows/**`, `agent_workflows/*.py`, and `docs/**/*.md` are all legal.
- The sentinel `grandfathered` is a WHOLE-VALUE marker; it MUST NOT be mixed with real path entries.

Implicit lifecycle-artifact allowances. A plan's own lifecycle artifacts are always in scope and need NOT be listed: the plan file itself under `.aw/records/plans/**` and the manifest/index refresh (`.aw/records/plans/INDEX.md`, `.aw/records/**/index.md`). A GENERATED file the plan produces is NOT implicitly exempt; it MUST be declared like any other path.

The grandfather sentinel. To introduce `Scope-Paths` without retroactively blocking the already-reviewed pending backlog, a pre-cutoff plan carries the explicit per-plan marker `Scope-Paths: grandfathered` (a reserved value of the field). The lint gate treats `grandfathered` as advisory-satisfied (non-blocking); a plan declaring a real allowlist is validated against the grammar above (a malformed allowlist is a blocking error); a plan with NO `Scope-Paths` field at all is hard-required (blocked) at the ready-to-execute gate. The marker is stored in the plan's own metadata block so it travels with the plan and is auditable in git. New or independently re-reviewed plans are expected to declare a real allowlist rather than carry the sentinel.

## 5. Stable execution and validation identifiers

### 5.1 Identifier grammar

- An execution identifier MUST match `E-[0-9]{2,}`.
- A validation identifier MUST match `V-[0-9]{2,}`.
- Identifiers are scoped to one IPD.
- The initial sequence SHOULD use `E-01`, `E-02`, and so forth.
- More than 99 items remains syntactically representable, although the plan-size warning and semantic review should make such a plan exceptional.
- An identifier is stable once assigned. Reordering an item MUST NOT change its identifier.
- Gaps are legal and MUST NOT trigger renumbering.
- New items receive the next unused numeric suffix greater than the highest suffix EVER assigned in that IPD, as recorded by the allocation watermark of Section 5.6, not merely the highest suffix currently present. This survives deletion of the current highest item.

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

### 5.6 Allocation watermark (never reuse a deleted suffix)

Pre-approval deletion of the current highest `E-*` item and its untouched pending `V-*` skeleton is permitted (Section 6.1). Without a persistent record, the remaining document would not reveal that the deleted suffix was ever used, and a later `sync` could reuse it, violating stable and monotonically increasing identity.

To prevent reuse, each IPD carries an allocation watermark in its metadata block:

```markdown
- Highest E allocated: NN
```

- `NN` is the largest numeric suffix EVER assigned to an `E-*` item in this IPD, whether or not that item still exists.
- The field is REQUIRED once any `E-*` item has been assigned; before the first `E-*` is assigned it MAY be `00` or absent (the schema fixes which; the recommended initial value is `00`).
- `aw ipd sync` MUST allocate the next suffix as `Highest E allocated + 1` and MUST then advance `Highest E allocated` to the newly allocated value. It MUST NOT decrease the watermark.
- The watermark MUST be greater than or equal to the largest `E-*` suffix currently present in the document; a watermark smaller than a present `E-*` suffix is an error.
- Deleting the current highest `E-*` item MUST NOT decrease the watermark; the tombstone survives as the watermark value.

The watermark is the chosen lightweight persistent mechanism (an explicit per-IPD tombstone), preferred over per-item tombstone rows because it adds one metadata line rather than retaining dead checklist rows. The canonical schema owns the field definition, the parser reads it, `sync` maintains it, the templates include it, and Section 16.2 tests deleting the highest item and then adding another to confirm no reuse.

## 6. Tool-assisted authoring

The `aw ipd` command group SHOULD provide separate, explicit operations:

- `aw ipd scaffold`: create a new conformant IPD skeleton from the canonical schema and template;
- `aw ipd sync`: assign IDs to new execution leaves, maintain the allocation watermark, add missing pending validation skeletons, and report inconsistencies without changing existing stable IDs;
- `aw ipd lint`: perform read-only deterministic checks.

### 6.1 Synchronization safety

`aw ipd sync` MUST be non-destructive by default:

- It MUST preserve every existing `E-*` and `V-*` identifier.
- It MUST preserve nonempty `Required evidence:`, `Observed evidence:`, notes, results, and checkbox state.
- It MUST NOT reorder user-authored actions or validation rows unless an explicit safe formatting operation is separately requested.
- It MAY remove a pending `V-*` row automatically only when its matching `E-*` was removed before approval and the validation row contains no observed evidence, nonpending result, or manual content. Removing the row MUST NOT decrease the allocation watermark (Section 5.6).
- It MUST refuse destructive synchronization after execution has begun.
- If an approved or executing plan requires structural changes, the tool MUST stop and require the plan's existing amendment/re-review workflow, including a workflow-history entry.

Authors MAY write action text manually. They SHOULD use `aw ipd sync` rather than hand-assigning identifiers or copying validation skeletons.

### 6.2 Writing-command safety contract

`aw ipd scaffold` and `aw ipd sync` are the only `aw ipd` operations that write files (`aw ipd lint` is read-only, Section 10). Both MUST follow this safety contract, defined here rather than in implementation discovery:

- Default behavior is preview/dry-run: the command prints the diff or the file it WOULD write and makes no filesystem change unless `--apply` (or the repository's established apply flag) is passed explicitly. This mirrors the repository's existing write-tool precedent (dry-run by default, explicit `--apply`).
- `aw ipd scaffold` MUST enforce that every scaffolded plan carries `Set`/`Order` metadata and that the destination path (derived or explicit `--path`) follows the canonical clustering grammar (`YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md`) unless `--legacy-name` is passed.
- `aw ipd scaffold` MUST refuse to overwrite an existing path unless an explicit overwrite flag is passed; the default is refusal with an actionable diagnostic.
- Writes MUST be atomic or recoverable (for example write-to-temp-then-rename), so an interrupted apply never leaves a partially written IPD.
- `aw ipd sync` MUST preserve all authored content per Section 6.1 and MUST refuse to write after execution has begun (Section 6.1), directing the author to the amendment/re-review workflow.
- Both commands MUST emit actionable diagnostics and use the exit-code contract of Section 10 (`0` success, `1` a refusal or conformance problem the caller must fix, `2` invocation/internal failure); an internal failure MUST NOT be reported as a successful write.

The canonical schema and Order 03 own the exact flag spellings; the behavior above is fixed by this specification and is tested (Section 16.2).

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

### 8.1 Per-E-item density heuristic (advisory)

In addition to the count-based structural thresholds above, the linter evaluates each `E-*` item using a deterministic density heuristic (`IPD-Z602`) that flags action text appearing to bundle multiple independent deliverables or test-surfaces.

The heuristic evaluates whether each E-item addresses exactly **one concern** and is **executable in one focused pass** (aligned with the canonical definition in `plan-review.md` and `review-rubric.md`). It detects signals such as explicit multi-part deliverable enumerations, multiple independent test-surfaces across subsystems, or chained coordinate conjunctions joining distinct major deliverables.

This signal is strictly ADVISORY:
- It produces an informational diagnostic (`IPD-Z602`) surfaced through `aw ipd lint` output and `--agent` result records.
- It does NOT fail structural conformance or gate lifecycle transitions (a structurally-valid plan with an advisory retains `conforming` disposition and exit code 0).
- Semantic reviewers and authors use the advisory alongside the review rubric to determine whether an item should be split into smaller child IPDs.

## 9. Lint checkpoints and lifecycle state

### 9.1 Persisted status versus lint checkpoint

The plan's persisted `Status:` and the linter's checkpoint are distinct concepts. `Status:` records the repository lifecycle state. A lint checkpoint specifies the transition or review boundary being evaluated.

The persisted readiness vocabulary is the repository's existing vocabulary (authoritative source: `agent_workflows/plans.py`; DECISIONS D52 and D65) and MUST be preserved unless a separate migration decision changes it. The recognized values are:

- pre-terminal (file lives in `.agents/plans/pending/`): `draft`, `to-review`, `reviewed`, `approved`, `auto-approved`;
- terminal (file lives in the matching directory; `Status` mirrors the directory): `executed`, `superseded`, `not-executed` (`done` is an accepted alias for `executed`);
- standing: `reusable`.

`auto-approved` is a real, supported value (D65): a sibling of `approved` at the ready-to-execute tier that records an automated checker (not a human) clearing a low-complexity mechanical corrective; it is NOT human approval. The schema and linter MUST recognize it. The metadata block (Section 4.4) carries these values in the `- Status:` field, which is the single source of truth for readiness; the orchestrator exception is that `Kind: orchestrator` uses `Order: 0` while children use `Order >= 1`.

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
| `pre-execution` | `review-finalize` passes; no declared blocking question remains unresolved; the persisted lifecycle state authorizes execution; no action has an illegal pre-execution state; a `Scope-Paths` value is present (Section 4.5) - a plan with NO `Scope-Paths` field is a blocking error, a `Scope-Paths: grandfathered` marker is advisory-satisfied (non-blocking), and a real allowlist is validated against the Section 4.5 grammar (malformed is a blocking error). This same `Scope-Paths` requirement also applies to any plan whose persisted `Status` is at the ready-to-execute tier (`approved`/`auto-approved`), so an approved plan cannot slip through without it. |
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
14. size thresholds and exception fields are consistent, and per-E-item density advisories (`IPD-Z602`) are surfaced advisory-only;
15. persisted status, directory, plan kind, requested checkpoint, and legacy applicability are compatible;
16. terminal status, history, directory, and lifecycle-commit metadata agree at `post-transition` to the extent repository state makes them deterministically observable (`IPD-S405`: an executed plan carries an `executed` workflow-history entry);
17. RETIRED: the no-em/en-dash style rule (formerly rule code IPD-D701) is no longer checked by this command. The no-dash convention is a user-facing prose rule only (GUIDING_PRINCIPLES P13, the AGENTS.md execution contract); IPDs are internal/AI-facing artifacts, so the linter does not flag dashes in them. Any other Markdown style rules delegated to this command are applied only to authored prose outside code, with front matter values exempted by schema and other explicitly excluded constructs.

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

At execution START, the authoritative single-IPD entry `aw ipd begin <plan> --actor <agent/model>` runs the `pre-execution` gate and, on conformance, freezes the plan's requirements and `Scope-Paths` and writes a LOCAL, gitignored execution-start receipt under `.aw/state/ipd-lifecycle/<id6>.receipt.json` binding `{plan Id, plan content digest, frozen requirement/scope digest, base HEAD, actor/model, timestamp}`. The receipt is the durable, independently-inspectable proof that the approved plan and its scope passed the gate at a specific base HEAD; it is fail-closed (any non-conforming/unrunnable gate, an unversioned/ambiguous base HEAD, an uncommitted change to a path INSIDE the plan's frozen `Scope-Paths`, a missing actor, or an interrupted write leaves NO valid receipt and therefore NO execution authority), atomic, and resumable. The baseline dirty-check is PATH-OVERLAP-scoped, not whole-tree (the same OQ-01 path-overlap rule that governs receipt lifetime): `begin` refuses only when uncommitted work touches the plan's own `Scope-Paths`; uncommitted work on DISJOINT paths is allowed so a concurrent multi-agent workflow (one agent executing while others edit unrelated paths) is not thrashed. It PERSISTS across unrelated intervening commits and is invalidated only by a change to the plan's own content digest or by an intervening commit that touched a path inside the plan's `Scope-Paths` (that path-overlap collision check is enforced by the finalize transaction, not by `begin`). The receipt mutates no tracked file and is never committed.

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

Once `aw ipd lint` exists, `plan-review`, `plan-review-long`, and the authoritative execution/lifecycle enforcement path (Section 12.1) MUST invoke it at their applicable checkpoints. They MUST NOT replace invocation with a prose instruction to “apply the same checks.”

- Structural preflight runs before semantic review.
- A structural error becomes a distinct structural finding and MUST be repaired before semantic review can produce a passing verdict.
- After review edits, `review-finalize` lint runs again.
- Execution fails closed if `pre-execution` lint cannot run or returns nonzero.
- Terminal transition fails closed if `pre-transition` lint cannot run or returns nonzero.
- Post-transition failure is reported as incomplete lifecycle finalization and MUST be repaired; it is not silently treated as success.

During the bootstrap implementation that creates the tool, the implementation IPD MAY use an explicit manual preflight. That exception ends when the linter is available. The review record MUST say `machine preflight unavailable: bootstrap` rather than imply machine verification occurred.

Pre-commit or CI integration MAY be deferred from version 1, provided all authoritative review, execution, and transition workflows invoke the linter unconditionally. Repository hook integration remains recommended defense in depth.

### 12.1 The authoritative execution and lifecycle enforcement path

Repository fact verified on 2026-08-02: there is NO authoritative general IPD execution or pre-transition workflow in `.agents/workflows/`. `verify-execution` is POST-execution only (it cross-checks an already-executed plan and never gates `pre-execution` or `pre-transition`). Therefore an "execution/lifecycle workflow docs" reference cannot be satisfied by an existing file, and the design MUST create the missing authoritative path rather than point at nothing.

Decision: the implementation Set creates a new authoritative execution-and-transition workflow document, `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md` (with a sibling `README.md`), owned by Order 05. It is the single authoritative entry point for beginning execution of an approved IPD and for performing the terminal lifecycle transaction. Its exact lint checkpoints are:

- at execution start, it MUST run `aw ipd lint --phase pre-execution FILE`; execution proceeds only on exit `0`;
- at the terminal transaction, it MUST run `aw ipd lint --phase pre-transition FILE`, perform the Section 11 transaction only on exit `0`, then run `aw ipd lint --phase post-transition MOVED_FILE`.

Fail-closed rules for this path:

- exit `1` (conformance error) blocks the transition and is surfaced as a structural finding to repair; the workflow MUST NOT proceed;
- exit `2` (invocation/parser/internal failure) blocks the transition and MUST NOT be treated as a pass; the tool being unable to run is a hard stop, not a skip;
- before the lifecycle commit, a failure leaves the plan in its pre-transition directory and status with no partial move (recoverable by re-running after repair);
- after the lifecycle commit, a failing `post-transition` check is reported as incomplete lifecycle finalization and repaired with a corrective follow-up; it is never reported as a successful transition.

The only permitted exception is the labeled bootstrap exception (`machine preflight unavailable: bootstrap`) that applies solely while this implementation Set is creating the tool, and it ends when `aw ipd lint` exists. Section 15 lists this workflow as a required implementation component and Order 05 names the exact file to create; Section 16.3 and 16.5 test the fail-closed behavior for exit `1` and exit `2` and the full `post-transition` consistency check.

## 13. Rollout and legacy behavior

### 13.1 New and existing nonterminal plans

- Every IPD created after adoption MUST use the new schema.
- Existing nonterminal IPDs MUST be migrated, re-authored, or explicitly quarantined (Section 13.3) before authoritative review or execution under the new convention.
- Repository-wide lint SHOULD target new and migrated nonterminal IPDs and MUST report quarantined plans explicitly (Section 13.3), never silently skipping them or calling them conforming.
- The already drafted, uncommitted research-org IPD Set is re-authored after this IPD-system Set lands, consistent with the maintainer's IPD-system-first sequencing decision. During this bootstrap it is explicitly quarantined (Section 13.3), not migrated in place, because it is deliberately not being pursued in its current shape and will be re-authored to the new schema immediately after this Set. Its bootstrap disposition is therefore `quarantined` with reason "pending re-authoring to the new schema after the IPD-system Set", owner "the IPD-system Set follow-up", and follow-up condition "re-author to the new schema".

### 13.2 Grandfathered terminal plans

Existing terminal IPDs are not retrofitted. Repository-wide lint skips them unless explicitly requested.

Direct lint of a grandfathered file MUST behave explicitly rather than silently pass:

- without a legacy flag, report `legacy/not evaluated` and a non-passing informational outcome defined by the CLI contract;
- with an explicit legacy option, run only the reduced legacy checks defined in the canonical schema;
- with an explicit migration option or after manual migration, run the current schema.

Legacy files MUST NOT be described as conforming to the new contract merely because they were skipped.

### 13.3 Quarantine of nonterminal plans

Quarantine is a first-class disposition for a nonterminal IPD that is not yet migrated and not being pursued in its current shape, so it must not block adoption yet must never be silently skipped or reported as conforming. Quarantine semantics are defined here and in Order 01 (schema), implemented in Order 02 (linter behavior), and applied in Order 06 (migration).

Representation: quarantine is declared in the metadata block (Section 4.4) by a `- Quarantine:` field whose value is a short reason, together with `- Quarantine owner:` and `- Quarantine follow-up:` fields. A plan with a `- Quarantine:` field is a quarantined plan; the three fields are required together (one present without the others is an error).

- Which plans may be quarantined: only nonterminal (pre-terminal) IPDs. A terminal plan is grandfathered (Section 13.2), not quarantined.
- Who authorizes it: the maintainer, or an agent acting under an explicit maintainer decision recorded in the plan's workflow history; the recorded owner names the authorizer or triggering follow-up.
- Location: the plan REMAINS in `.agents/plans/pending/` (it is not moved); the metadata field marks it. This avoids inventing a new directory and keeps the plan visible on the board.
- Direct lint behavior (`aw ipd lint FILE` on a quarantined file): report an explicit `quarantined` disposition and a non-passing informational outcome (distinct from both `pass` and `legacy/not evaluated`); do not run the full new-schema conformance checks against it and do not report it as conforming.
- Repository-wide lint behavior: report quarantined plans in a distinct `quarantined` category with their recorded reason; they are neither counted as conforming nor silently dropped. The repository scan MUST distinguish conforming, quarantined, grandfathered, and erroneous plans.
- Outcome classification: `quarantined` is a non-passing informational outcome; it is not `pass`, not a warning, and not a hard error. Repository-wide lint MUST NOT report overall success while treating a quarantined plan as if it conformed, and MUST make the quarantined count visible.
- Recorded fields: `- Quarantine:` (reason), `- Quarantine owner:` (owner or trigger), `- Quarantine follow-up:` (the expiry or follow-up condition, for example "re-author to the new schema after the IPD-system Set").

Quarantine MUST NOT be used to pass a plan that should be an error; a structurally broken plan that is being actively pursued is an error, not a quarantine.

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

1. the canonical machine-readable schema and schema tests, including the metadata-block contract (Section 4.4), the allocation watermark (Section 5.6), and quarantine semantics (Section 13.3);
2. ordinary child and orchestrator templates generated from or checked against the schema, with the orchestrator execution checklist immediately after `## Goal`;
3. `ipd-spec` updates and removal of ambiguous “near” language;
4. `aw ipd scaffold` with the writing-command safety contract (Section 6.2);
5. non-destructive `aw ipd sync` with watermark maintenance (Section 5.6) and the writing-command safety contract (Section 6.2);
6. read-only `aw ipd lint` with explicit checkpoints, legacy disposition, and quarantine disposition;
7. the execution/validation state model and stable-ID rules including the allocation watermark;
8. structured open-question and size-exception grammar;
9. lifecycle-gate and post-transition fixes;
10. structural-preflight integration into `plan-review`, `plan-review-long`, `review-rubric`, and the NEW authoritative execution-and-transition workflow `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md` (Section 12.1), which does not exist today and MUST be created;
11. parity tests for embedded and standalone rubric/report-template content, and replacement of the always-loaded structural prose in `agent_workflows/engine.py` `agents_pointer_prose()` (and the regenerated `AGENTS.md`) with a thin pointer;
12. documentation, DECISIONS pointer, and thin `AGENTS.md` pointer;
13. migration or explicit quarantine (Section 13.3) of existing nonterminal IPDs, including the explicit bootstrap quarantine of the research-org Set;
14. dogfooding against this repository's nonterminal IPDs, distinguishing conforming, quarantined, grandfathered, and erroneous plans;
15. tests and fixtures defined in Section 16.

The E-*/V-* convention remains IPD-specific and does not alter the research-org convention directly. The research-org IPD Set is re-authored to this shape after the IPD-system Set lands.

## 16. Required tests and acceptance criteria

The implementation MUST include table-driven fixtures covering at least:

Each case below is mandatory. The implementation IPD Set MUST map each case to an explicit execution (`E-*`) and validation (`V-*`) item; a case MUST NOT be absorbed silently into a broad phrase such as "checkpoint cases" or "full state tests".

### 16.1 Parser, heading, and metadata tests

- conforming ordinary (child) plan;
- conforming orchestrator plan;
- missing required heading;
- duplicate required heading;
- renamed required heading;
- out-of-order required headings;
- an apparent H2 inside a fenced code block;
- an apparent H2 inside an indented code block;
- an apparent H2 inside a block quotation;
- an apparent H2 inside YAML front matter;
- a heading-like or checkbox-like line inside the canonical bullet metadata block treated as metadata, not structure;
- optional heading in an allowed interval (accepted);
- optional heading in a forbidden interval (rejected);
- invalid or unknown plan kind;
- missing plan kind;
- invalid or missing required metadata field;
- duplicate metadata field;
- unknown metadata field for a new IPD;
- an orchestrator with `Order` other than `0`, and a child with `Order: 0` or non-positive `Order`, each rejected;
- an incompatible status/directory/kind/checkpoint combination rejected.

### 16.2 Identifier, watermark, and synchronization tests

- duplicate IDs;
- malformed IDs;
- missing validation mapping;
- duplicate validation mapping;
- orphaned validation mapping (a `V-*` with no matching `E-*`);
- more than 99 syntactically valid IDs;
- reordering without renumbering;
- adding an item assigns the next unused suffix;
- gaps remain stable;
- deleting the highest assigned `E-*` (and its untouched pending `V-*`) then adding a new item assigns a suffix ABOVE the watermark, never reusing the deleted suffix;
- a metadata watermark smaller than a present `E-*` suffix is an error;
- synchronization preserves authored evidence and state;
- destructive synchronization is refused after execution begins;
- removed pending draft item removes only its untouched pending validation skeleton;
- every writing command (`scaffold`, `sync`) defaults to dry-run/preview and writes only under explicit apply;
- `scaffold` refuses to overwrite an existing path without an explicit overwrite flag;
- an interrupted or failed write leaves no partially written IPD (atomic/recoverable).

### 16.3 State-machine and lifecycle tests

- every legal and illegal execution checkbox/state pair;
- every legal and illegal validation checkbox/result/evidence combination;
- every E/V cross-state conflict between a matching pair;
- checkpoint-specific placeholder rules;
- `pre-transition` rejects any nonperformed E, nonpassing V, unchecked V, or empty observed evidence;
- `post-transition` checks full status/history/path/commit consistency after the transaction.

### 16.4 Question and size tests

- open blocking question rejected at `pre-execution`;
- resolved blocking question accepted with rationale;
- deferred blocking question rejected;
- deferred nonblocking question requires owner/trigger and rationale;
- size warning at each threshold boundary (group threshold and leaf threshold);
- missing exception rationale rejected;
- present exception rationale accepted;
- `standard` assessment rejected when a threshold is exceeded.

### 16.5 Status, enforcement, legacy, quarantine, and parity tests

- every supported persisted status is recognized, including `auto-approved`;
- authoritative workflows fail closed on linter exit `1`;
- authoritative workflows fail closed on linter exit `2`;
- linter exit `0`, `1`, and `2` are distinct and never conflated;
- bootstrap-unavailable state is labeled accurately (`machine preflight unavailable: bootstrap`);
- repository scans skip grandfathered terminal files without calling them conforming;
- direct grandfathered-file invocation WITHOUT a legacy option reports explicit `legacy/not evaluated`;
- explicit reduced legacy checking under the legacy option;
- migrated legacy file is checked under the current schema;
- quarantined nonterminal file reports the explicit `quarantined` disposition (not a pass, not silently skipped);
- diagnostics contain a stable rule code, file path, line, and column;
- the retired no-em/en-dash rule is NOT enforced: an IPD containing em/en dashes still lints conforming (the convention is user-facing prose only, GUIDING_PRINCIPLES P13);
- an intentionally desynchronized parity fixture fails, and a missing required dependency (for example `report-template.md`) fails explicitly;
- repository dogfood distinguishes conforming, quarantined, grandfathered, and erroneous plans, and never calls a skipped file conforming.

Acceptance requires all tests to pass, parity checks to pass, and dogfood lint to pass (conforming plans pass; quarantined and grandfathered plans report their explicit dispositions) for the repository's nonterminal IPDs. Semantic review remains a separate acceptance gate.

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
- The allocation watermark records the highest suffix ever assigned and is never decreased, so a deleted suffix is never reused.
- Explicit `--phase` is required at transition gates.
- The linter is read-only and fail-closed in authoritative workflows.
- The metadata block is a bullet list, not YAML front matter.
- The authoritative execution-and-transition path is a NEW workflow (`.agents/workflows/ipd-lifecycle/ipd-lifecycle.md`), created by this Set (Section 12.1).
- Quarantine is a metadata-declared, explicitly reported, non-passing disposition (Section 13.3).
- Execution and validation remain separate physical sections in version 1.
- The mutable checklist is never duplicated.
- Semantic review remains mandatory.

## 18. Approval and next step

This specification was APPROVED by the human maintainer on 2026-08-03 ("Approved. Go."), after the independent Codex gpt-5.6 review of the implementation Set and the provenance correction. Prerequisite (a) formal maintainer approval of THIS specification is now satisfied. Prerequisite (b) the implementation Set was independently reviewed (Codex gpt-5.6, 2026-08-03) and approved by the maintainer in the same instruction; execution proceeds in dependency order (Order 01 through 06), pausing only to STOP-and-report on a genuine blocker, out-of-scope decision, or unresolved question. The components to implement are in Section 15.

After the IPD-system Set lands:

1. migrate or re-author applicable nonterminal IPDs;
2. re-author the research-org Set to the new structure;
3. run dogfood lint and semantic review;
4. record adoption in DECISIONS and the relevant documentation;
5. consider the deferred controlled experiment if empirical layout optimization becomes valuable.

## Workflow history

- 2026-08-26 note (aw specs): Section 11: begin baseline dirty-check is Scope-Paths-scoped (path-overlap, ipdgates-03 OQ-01), not whole-tree; disjoint dirt allowed to preserve concurrent multi-agent workflow (beginscope vaq9qf E-03)
