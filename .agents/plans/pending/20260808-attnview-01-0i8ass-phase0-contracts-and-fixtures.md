# IPD: Phase 0 contracts and fixtures (Set attnview, Order 1)

- Date: 2026-08-08
- Kind: child
- Concern: freeze the load-bearing CONTRACTS the rest of the Set builds against, and the fixture corpus that tests them, so no later child has to invent product behavior. This resolves the approved spec's Phase-0 open questions OQ1/OQ2/OQ4/OQ6/OQ10 into written, testable contracts.
- Scope: author contract documents/fixtures ONLY; write NO product code and NO scanner/verb yet. Deliverables: the five-value attention-class enum + exhaustive per-tree mapping tables (specs, plans, research; prompts/comms deferred per OQ3); the `## Workflow history` record grammar (OQ2); the versioned JSON output schema + canonical serialization profile (OQ4); the `Gate-Kind`/`Gate-Ref` per-kind validators (OQ6); the human-approval-token + implementation-evidence mechanism for `aw specs set` (OQ10); the tree policy inventory; and fixture repos covering every native status and every `--check` violation class. Requires the approved spec `.agents/docs/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`.
- Status: draft
- Set: attnview
- Order: 1
- Highest E allocated: 08
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 0i8ass

## Workflow history

- 2026-08-08 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created. Child of Set `attnview`; the foundation Orders 02 to 05 build against, authored from the approved spec Sections 6, 7, 8.3, 8.4, 8.5, 8.8 and Phase 0 (Section 13).

## Goal

Turn the spec's design into frozen, machine-checkable contracts plus a fixture corpus, so Orders 02 to 05 implement against fixed inputs rather than open questions. Produce a single contract module home for the attention-class enum and the per-tree mapping tables, a written JSON/serialization/history/gate contract, and fixtures that exercise every native status and every violation class. No runtime scanner or write verb is built here.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: the attention-class enum and per-tree mapping tables (OQ1)

- [ ] E-01 create the contract home `agent_workflows/attention_contract.py` (stdlib-only, Python 3.9) defining the closed five-value `AttentionClass` enum (`ready`, `active`, `blocked`, `done`, `parked`) and the TREE POLICY INVENTORY (each tree is `tracked` with an owner + mapping, or `excluded` with a rationale; specs/plans/research tracked, prompts/comms/walkthroughs/roadmaps excluded in v1 per OQ3/OQ8).
  - Depends on: none
  - Expected outcome: the enum and tree-policy inventory exist in one importable module; no scanner logic yet.
  - Execution state: pending
- [ ] E-02 define the EXHAUSTIVE per-tree `class_of(tree, native_status)` mapping tables as data next to each tree's native enum: specs (from spec Section 7), plans (over `plans.PRE_TERMINAL`+`TERMINAL`+`STANDING`), research (over `research_contract.STATUSES`). Every native value maps to exactly one class; no default fallthrough. Record where each fragment lives so an enum change and its mapping change co-locate.
  - Depends on: E-01
  - Expected outcome: a total mapping over every current native status of specs/plans/research; unknown value -> violation, never a default.
  - Execution state: pending

### Task group 2: the metadata, JSON, gate, and approval contracts (OQ2/OQ4/OQ6/OQ10)

- [ ] E-03 write the `## Workflow history` record grammar (OQ2): the exact per-record shape and whether `last_history_at` is a date or an RFC-3339 UTC timestamp, reconciling the plans date convention with the JSON contract's precise-timestamp preference. Capture it as a documented, parseable grammar (a regex/spec + examples).
  - Depends on: E-01
  - Expected outcome: one written history-record grammar the migration (Order 04) and `aw specs` (Order 02) both target.
  - Execution state: pending
- [ ] E-04 write the versioned JSON output schema (OQ4): required/optional fields, exact types, null behavior, enum values, path normalization, id scheme + uniqueness, ordering, `schema_version`/`mapping_version` semantics, and the `violations` error object; AND the canonical serialization profile (key order, indentation, separators, ASCII-escaping) per spec Section 8.5. Record as a schema doc + a machine-usable shape.
  - Depends on: E-01, E-02
  - Expected outcome: a frozen JSON API contract + canonical serialization profile the scanner (Order 03) renders to.
  - Execution state: pending
- [ ] E-05 write the gate contract (OQ6): `Gate-Kind` closed enum (`artifact`/`decision`/`todo`/`issue`/`date`/`external`) and the per-kind `Gate-Ref` validators (`date`=YYYY-MM-DD; `artifact`=repo-relative POSIX path + optional anchor; `todo`/`decision`=stable repo ids; `issue`=absolute http(s) URL; `external`=nonempty opaque), plus the output-safety rules (spec Section 8.8: single-line, length-bounded, control-char rejection, per-surface escaping, http(s)-only issue URLs, descriptive-fields-are-data).
  - Depends on: E-01
  - Expected outcome: a written, testable gate + output-safety contract.
  - Execution state: pending
- [ ] E-06 write the approval/authority contract (OQ10): the transition/authority table (spec Section 7) as data (legal transitions + who/what each requires), the concrete human-approval token mechanism for `reviewed -> approved` (chosen candidate, e.g. an explicit `--approved-by <human>` recorded in history), and the implementation-evidence-citation format required for `implementing -> implemented`.
  - Depends on: E-01
  - Expected outcome: a frozen transition/authority + approval-token + evidence-citation contract `aw specs set` (Order 02) enforces.
  - Execution state: pending

### Task group 3: fixtures and the contract test

- [ ] E-07 build a fixture corpus under `tests/fixtures/attnview/` covering every native status of specs/plans/research (each mapping to its class) AND every `--check` violation class from spec Section 8.3/8.8 (missing/unknown status, unmapped status, missing/malformed/contradictory gate, deferred-without-gate, non-http issue URL, control-char/newline/over-length descriptive field, duplicate id, duplicate path, disposition-vs-terminal mismatch, unclassified tree).
  - Depends on: E-01, E-02, E-05
  - Expected outcome: a deterministic fixture set Orders 02 and 03 test against.
  - Execution state: pending
- [ ] E-08 add `tests/test_attention_contract.py` asserting the mapping is TOTAL over each tracked tree's native enum (coverage test: mapping keys == declared enum; fails on missing or extra), the enum/tree-policy shapes are well-formed, and the gate/history/JSON grammars parse their positive fixtures and reject their negative ones. Run the file and the full suite; paste actual output.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: contract tests pass; full suite green; the coverage test is the guard that catches a future enum change without a mapping update.
  - Execution state: pending

## Project conventions discovered (Step 0)

- IPD authoring per `.agents/docs/specs/20260726-1340-01-ipd-spec.md`; scaffold/sync/lint via `aw ipd`; stdlib-only, Python 3.9 (D46); tests are stdlib `unittest` (`python3 -m unittest discover -s tests -t .`).
- The contract module should sit beside the existing per-tree contracts (`plans.py`, `research_contract.py`) so the mapping fragments co-locate with the native enums (spec Section 6).
- Existing native enums to map exhaustively: `plans.PRE_TERMINAL`/`TERMINAL`/`STANDING` (`agent_workflows/plans.py:25-27`) and `research_contract.STATUSES` (`agent_workflows/research_contract.py:130`); the spec enum is in spec Section 7.

## Findings

This is the first Phase-0 child; findings are the spec's own Phase-0 open questions (OQ1/OQ2/OQ4/OQ6/OQ10) which this child resolves into written contracts. No code findings yet.

## Proposed changes (ordered, validatable)

1. `agent_workflows/attention_contract.py`: the class enum + tree-policy inventory (E-01) and the per-tree mapping tables (E-02).
2. Contract docs (in-module docstrings or a `.agents/docs/specs/` companion) for the history grammar (E-03), JSON schema + serialization (E-04), gate validators + output safety (E-05), and the approval/authority contract (E-06).
3. `tests/fixtures/attnview/` fixture corpus (E-07) and `tests/test_attention_contract.py` (E-08).

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| The `aw attention` scanner + renderers | scope | This child only freezes contracts + fixtures. | Order 03 |
| The `aw specs` write verbs | scope | Contracts here; the verb consumes them. | Order 02 |
| prompts/comms mapping tables | scope | Excluded from v1 unless finalized here (OQ3); default is defer. | Phase 3 |

## Scope check

- Over-scope: none - no runtime scanner/verb is built; only contracts + fixtures + a contract test.
- Under-scope: the child MUST resolve OQ1/OQ2/OQ4/OQ6/OQ10 into frozen, tested contracts and build fixtures for every status + every violation class. Anything less forces a later child to invent product behavior.

## Required tests / validation

`python3 -m unittest discover -s tests -t .` green (paste the `Ran N tests ... OK` line); `tests/test_attention_contract.py` passes including the totality/coverage assertion; `aw sanitize --agent` clean; no em/en dashes.

## Spec / documentation sync

Record the resolved OQ1/OQ2/OQ4/OQ6/OQ10 outcomes back into the approved spec's Section 12 (mark them RESOLVED with a pointer to this child), since the spec explicitly named them Phase-0 deliverables.

## Open questions

### OQ-01: history record - date or timestamp

- Blocking: no
- Status: open
- Owner: this child (E-03)
- Resolution or deferral rationale: the plans convention uses a date; the JSON `last_history_at` wants a precise instant. E-03 chooses and freezes one grammar; not blocking because either choice is implementable and the choice is recorded before Order 02/04 consume it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `agent_workflows/attention_contract.py` imports; the five-value enum and the tree-policy inventory are present with specs/plans/research tracked and the rest excluded-with-rationale.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the coverage test shows the mapping keys equal each tracked tree's declared native enum (specs, `plans` PRE_TERMINAL+TERMINAL+STANDING, `research_contract.STATUSES`); no default fallthrough exists.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the history-record grammar parses the positive fixtures and rejects malformed ones; the date-vs-timestamp choice is documented.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the JSON schema doc enumerates fields/types/ordering/versioning/error-object; a sample record round-trips through the canonical serialization to byte-identical output.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: each `Gate-Kind` validator accepts its valid fixture and rejects its invalid one; the output-safety rules reject the control-char/newline/over-length/non-http fixtures.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: the transition/authority table is present as data; the approval-token mechanism and evidence-citation format are specified concretely enough for Order 02 to enforce.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: `tests/fixtures/attnview/` contains a fixture for every native status and every named violation class; list them.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste the actual `python3 -m unittest` summary; confirm the totality/coverage assertion is present and passing; leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This child MUST be reviewed and approved by a human before execution. Do NOT mark it done or move it to `executed/` until every V-* item is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. The terminal lifecycle transition (set `Status: executed`, `git mv` to `.agents/plans/executed/`) is a POST-gate transaction, never an E-*/V-* item.
