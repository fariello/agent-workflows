# IPD: Unify artifact file finding, reference matching, and naming (one library each)

- Date: 2026-08-23
- Kind: orchestrator
- Concern: The agent_workflows package has THREE separate concerns each implemented multiple times independently, so `aw` verbs disagree on how to find a file, how to detect a reference to a file, and how to build/validate a filename. This causes real inconsistencies: the same `<selector>` can resolve under one verb and fail under another; a `research` rename orphans stem citations that a `plans` rename would rewrite; and the filename grammar is re-encoded in ~6 regexes plus triplicated facet tables that must be hand-synchronized.
- Scope: Orchestrates a five-child Set that consolidates (1) filename NAMING/grammar (build + validate), (2) selector-to-file RESOLUTION, and (3) reference MATCHING/rewriting + dangling-citation checking into one canonical library each, then (4) adds an additive, non-authoritative rename/regroup history ledger, and (5) enforces the filename identity-slot id6-uniqueness invariant (DECISIONS.md D140) in `aw check`/`aw doctor` and fixes the one existing violator. Touches agent_workflows/{artifact_core.py,artifact_types.py,artifact_rename.py,plans_refs.py,research_refs.py,research_contract.py,plans_index.py,research_index.py,selectors.py,status_set.py,check_engine.py,ipd_lint.py,ipd_authoring.py,doctor.py,backlog.py,specs.py,record_history.py}, .aw/system/workflows/setup-repo/tools/normalize_plan_names.py, one on-disk walkthrough (Order 05), and the test suite. Does NOT change any on-disk filename grammar, citation syntax, or manifest schema in a user-visible way (pure internal consolidation, byte-for-byte behavior preserved) except where a child explicitly fixes a divergence and documents it (Order 01 migrates walkthroughs to the facet form; Order 05 renames the one identity-slot violator).
- Status: reviewed
- Set: unifyfileio
- Order: 0
- Highest E allocated: 04
- Author: Gabriele Fariello
- Id: g6mbht

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED (orchestrator only; the four children were read as evidence, not individually reviewed - use /aw plan-review-long for the full 5-plan batch). PR-002 (added a binding Module-placement principle + import-direction cross-IPD test, resolving the core-vs-naming placement inconsistency between Order 01 and Order 03); PR-003 (E-01 + completion criteria now require each child's single blocking OQ be human-resolved before that child executes); PR-001 (review-completeness: children not individually reviewed here - recommended next step). Verified all four children exist with cited Ids/orders and lint conforming.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): re-review after Order 05 (9a655p, id6-identity-slot enforcement) was added and Order 01 grew (now blocking OQ-02/OQ-04/OQ-05). APPROVE WITH REVISIONS APPLIED - synchronized the orchestrator to the actual 6-member Set: PR-001 (updated "four-child"/"01->04" to five children throughout Scope/Goal/E-01/E-02/V-01/V-02/cohesion/lifecycle); PR-002 (E-01 blocking-OQ ledger was stale/wrong - now enumerates all resolved blocking OQs across Orders 01-04 accurately); PR-003 (added Order 05's identity-slot deliverable to Completion criteria + Cross-IPD validation, incl. the 05-after-01-E-06 sequencing so no double-rename); PR-004 (reflected Order 01's resolved OQ-02/04/05 decisions in Scope/Goal). Verified all six members via `aw find plans unifyfileio` and each child's OQ blocking/resolved status.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): re-review (same target, no external change). APPROVE WITH REVISIONS APPLIED - PR-001 (child-table cited FULL untruncated filenames for Orders 03/04 that do not exist on disk; the real names are scaffold-truncated `...dangling-c.ipd.md` / `...workflow-s.ipd.md` - corrected both cited paths so all five child-table filenames now resolve to real files, verified). No other findings; the prior workflow-history lines' "four children"/"01-04" wording is a correct HISTORICAL record of earlier runs and was intentionally left unedited (append-only history).

## Goal

Establish, across the whole `agent_workflows` package, exactly ONE canonical implementation of each of three cross-cutting file concerns, so every `aw` verb (and every workflow tool) behaves identically:

1. **One way to NAME files** - a single filename-grammar authority module that both BUILDS and VALIDATES every artifact type's name (plans, research, specs, prompts, backlog, walkthroughs, roadmaps, releases), replacing the ~6 duplicated regexes and 3 duplicated facet tables that exist today. (Child Order 01.)
2. **One way to FIND files** - a single selector-to-file resolver that accepts the full selector vocabulary (direct path, id6, setid, status, bare stem, filename substring) identically for every verb, replacing the three independent resolvers (`selectors.resolve_one`, `artifact_rename.find_target_record`, `status_set.match_selector`) and the path-only `backlog set` outlier. (Child Order 02.)
3. **One way to IDENTIFY references to a file** - a single reference matcher/rewriter that detects and rewrites every citation form (full filename, bare stem, range shorthand) consistently for every type, plus a single dangling-citation matcher policy so `aw check` recognizes the same citation forms everywhere. This fixes the current divergence where `research` rewrites full-filename ONLY (orphaning stem/range citations that a `plans` rename would fix) and where dangling checks understand different forms per type. (Child Order 03.)

Then, on that unified base, add ONE additive audit trail and ONE identity-invariant enforcement:

4. **A rename/regroup history ledger** - an optional record type appended to the EXISTING git-tracked, id6-keyed, append-only sidecar `.aw/records/history.jsonl`, recording `{id6, from_name, to_name, verb, actor, date}` on every rename/regroup, so a future `aw` audit/undo verb (and grouping-history queries) do not have to walk git. It is ADDITIVE: id6 already guarantees citation stability and `git mv` already records moves, so the ledger is a convenience, never a new source of truth. (Child Order 04.)
5. **Identity-slot id6 enforcement** - make `aw check`/`aw doctor` fail closed when a file's filename identity-slot id6 is not that file's own unique identity (DECISIONS.md D140), closing the gap that let a foreign id6 in a filename slot pass `aw check`, and fix the one existing violator (the `p7dqwz` walkthrough). (Child Order 05.)

Non-goal: this Set does NOT redesign the filename grammar, change citation syntax, alter the manifest schema, or finish the id6 rollout to id6-less legacy types (that is called out as a dependency risk in Order 01, not a deliverable here).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Orchestrate the five-child unification Set

- [ ] E-01 Confirm the five child IPDs (Orders 01-05) are authored, `aw ipd lint`-conforming, and their dependency order is recorded in the child table below; do not execute any child until (a) its `Depends on` predecessors are executed and their manifests are clean, AND (b) every BLOCKING open question that child carries is human-resolved. The blocking-OQ ledger across the Set (all currently RESOLVED at /plan-review): Order 01 OQ-02 (walkthrough canonical form -> migrate to facet), OQ-04 (normalize_plan_names imports the authority), OQ-05 (walkthrough mints its own id6 + typed source ref); Order 02 OQ-01 (kind-aware ambiguity + `--force`); Order 03 OQ-01 (dangling policy for bare-filename/setid); Order 04 OQ-01 (id6-less ledger by endpoint case). Orders 01 OQ-01/OQ-03 and Order 05 OQ-01/OQ-02 are non-blocking. A child with any unresolved blocking OQ is NO-GO and MUST NOT be executed.
  - Depends on: none
  - Expected outcome: the Set is coherent and each child is ready for per-child human approval, blocking-OQ resolution, and sequential execution.
  - Execution state: pending

- [ ] E-02 After all five children are executed, run the cross-IPD validation below (single grammar authority, single resolver, single reference library, ledger additive-only, identity-slot invariant enforced) and confirm no regressions in the full suite; then transition this orchestrator to executed.
  - Depends on: E-01
  - Expected outcome: the whole Set is verified consistent and the orchestrator is closed.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (Id) | What it does | Depends on |
|---|---|---|---|
| 01 | `20260823-unifyfileio-01-o6b8l3-canonical-artifact-naming-and-filename-grammar-authority.ipd.md` | ONE module that builds + validates every artifact filename; collapses the ~6 grammar regexes and 3 facet tables into one authority all callers use. | none |
| 02 | `20260823-unifyfileio-02-laykok-unified-selector-to-file-resolver.ipd.md` | ONE selector-to-file resolver replacing `resolve_one` / `find_target_record` / `match_selector` / `backlog set` path-only; identical selector vocabulary everywhere. | Order 01 |
| 03 | `20260823-unifyfileio-03-3cmnfc-unified-reference-matcher-rewriter-and-consistent-dangling-c.ipd.md` | ONE reference matcher/rewriter (all citation forms, all types) + ONE dangling-citation matcher policy; fixes research full-name-only weakness. | Orders 01, 02 |
| 04 | `20260823-unifyfileio-04-52zgqr-additive-rename-and-regroup-history-ledger-on-the-workflow-s.ipd.md` | Additive `{id6,from_name,to_name,verb,actor,date}` records on the existing `history.jsonl`; one write helper, one call per engine. | Order 03 |
| 05 | `20260823-unifyfileio-05-9a655p-enforce-filename-identity-slot-id6-uniqueness-in-aw-check-an.ipd.md` | Make `aw check`/`aw doctor` enforce that a file's filename identity-slot id6 is its own unique identity (DECISIONS.md D140); fix the one existing violator (`p7dqwz` walkthrough). | Order 01 |

Execution order MUST be 01 -> 02 -> 03 -> 04, with 05 executable any time after 01 (it depends only on the naming authority's slot accessor). Rationale: naming is the foundation (both the resolver and the reference matcher need the canonical grammar to parse/build names); the resolver is needed before the reference library so the reference library can reuse it for "does this cited name currently exist?"; the ledger sits on the unified rename path delivered by 03; the identity-slot enforcement (05) needs only the Order 01 grammar to parse a filename's id6 slot. Each child is independently valuable and independently executable once its predecessors land, but reversing the order forces re-work.

## Completion criteria (the whole Set is done only when)

- Exactly ONE module owns filename BUILD+VALIDATE for all eight artifact types; the previously-duplicated grammar regexes (`artifact_rename._UNIFORM_RE`, `plans_refs._CLUSTERED_RE`, `normalize_plan_names._CLUSTERED_RE`, `plans_index.check_drift` inline clustered regex) and facet tables (`plans_refs.ARTIFACT_TYPE_FACETS`, `normalize_plan_names._ARTIFACT_TYPE_FACETS`, `check_engine._TYPE_FACET`, `status_set` suffix map) are removed or reduced to a single re-exported definition, verified by a test that asserts no second copy of the clustered grammar exists.
- Exactly ONE selector resolver backs every verb; `resolve_one`, `find_target_record`, and `match_selector` are collapsed to one (or two are thin shims over the third); a table-driven test asserts the SAME `<selector>` resolves identically across `rename`, `group`, `set`, `show`, and `find`.
- Exactly ONE reference matcher/rewriter is called by the plans, research, and generic rename/group paths; a test asserts a `research` rename now rewrites bare-stem citations (the current gap) and that plans/backlog/etc behavior is byte-for-byte unchanged; the dangling-citation checker recognizes the same citation-form set for every type.
- The rename ledger appends an id6-keyed `{from_name,to_name,verb}` record on every rename/regroup, is append-only, records the id6-less->id6 and both-id6-less endpoint cases (Order 04's resolution), and is proven NON-authoritative (deleting the ledger does not change any `aw` command's correctness, only the audit-trail query).
- `aw check`/`aw doctor` enforce the identity-slot id6 invariant (D140): a file whose filename identity-slot id6 is not its own identity is flagged, the one existing violator (the `p7dqwz` walkthrough) has been renamed to its own id6 with a typed `Target-Id:` reference, and `aw check all` reports zero identity-slot findings (Order 05).
- Every BLOCKING open question was human-resolved before its child executed (Order 01 OQ-02/OQ-04/OQ-05, Order 02 OQ-01, Order 03 OQ-01, Order 04 OQ-01); no child was executed with an open blocking OQ.
- The module-placement principle above held: no `artifact_core -> artifact_naming/selectors/reference-matcher` import was introduced.
- `pytest -n auto` is green and `aw check all` shows no NEW findings attributable to this Set.

## Module-placement principle (binding on all children)

To keep the three unified concerns from colliding or creating bad import cycles, the children MUST follow one placement principle:

- **Naming/grammar authority** (Order 01) lives in its OWN module (`artifact_naming.py` is the expected choice per Order 01 OQ-01), NOT inside `artifact_core.py`, because `artifact_core.py` deliberately excludes filename-grammar (it holds only id6/kebab/IO primitives). It may import `artifact_core` primitives.
- **Selector resolver** (Order 02) lives in `selectors.py`.
- **Reference matcher/rewriter** (Order 03) lives beside the existing `find_dangling_citations`/`iter_scan_files` in `artifact_core.py` ONLY IF it does not need to import the naming authority; if it DOES need the naming authority (to compute a stem), it MUST live in its own module (or in `selectors.py`/`artifact_naming.py`) so the dependency flows toward core, never core -> naming. The allowed import direction is: `artifact_naming`, `selectors`, and the reference matcher may import `artifact_core`; `artifact_core` MUST NOT import any of them. Order 03's executor MUST honor this and, if it forces the matcher out of core, record that as its resolution rather than creating a core -> naming import.

This resolves the latent cross-IPD placement inconsistency (Order 01 keeps grammar out of core while Order 03 initially proposed hosting the matcher in core): the guardrail above lets Order 03 choose core only when it introduces no core -> naming import.

## Cross-IPD validation

- **No second grammar copy:** a test greps the package for the clustered-grammar regex signature and asserts exactly one canonical definition remains (all others import it).
- **No bad import direction:** a test asserts `artifact_core` does not import `artifact_naming`/`selectors`/the reference matcher (import direction flows toward core only).
- **Resolver parity:** a parametrized test drives one fixture repo with one `<selector>` of each kind (path/id6/setid/status/stem/substring) through every verb's resolution entry point and asserts identical resolved paths (or identical clean "no match" for kinds a verb intentionally rejects, with the rejection itself uniform).
- **Reference parity + research fix:** a test renames a research doc that is cited by full-name AND by bare stem in another file and asserts BOTH are rewritten (today only full-name is); the same test for a plan is unchanged.
- **Ledger additivity:** a test performs a rename with the ledger present and with the ledger file deleted mid-flight and asserts the rename result (files moved, citations rewritten, exit code) is identical; only the ledger query differs.
- **Identity-slot invariant enforced:** after Order 05, `aw check all` flags a fixture whose slot id6 is not its own identity and is clean on a conformant tree; the one on-disk `p7dqwz` violator carries its own id6 + typed `Target-Id:` and no longer collides (Order 05 sequenced AFTER Order 01 E-06's walkthrough migration - no double-rename).
- **Whole-suite regression:** `pytest -n auto` green; paste the actual runner output in each child's V-items and in E-02 here.

## Deferred / out of scope (with reason)

- Redesigning the filename grammar, changing citation syntax, or changing the manifest schema: out of scope; this Set is pure internal consolidation that preserves on-disk behavior.
- Finishing the id6 rollout to the id6-less legacy types (specs/prompts/roadmaps/releases/walkthroughs): out of scope, but Order 01 MUST document exactly which types lack an id6 and how the unified naming authority represents them, and Order 04 MUST handle the id6-less case (skip-or-synthetic-key) without erroring.
- Wiring `comms` verbs (it is in `ARTIFACT_TYPES` with no `TYPE_BACKENDS` entry): out of scope; note only.
- An `aw` audit/undo verb built ON the ledger: out of scope for this Set (the ledger is the substrate; the verb is a future plan). Order 04 delivers only the durable record.

## Scope check

- Over-scope: none. Each child is a single unification concern; the ledger is deliberately minimal and additive.
- Under-scope: none. The three "one way" goals plus the ledger cover the user's stated requirement ("one unified way to find files, one to identify references, one to name files") and the rename-history question.

## Required tests / validation

- Each child carries its own falsifiable V-items with pasted evidence.
- This orchestrator's E-02 runs the Cross-IPD validation above after all children land and pastes `pytest -n auto` output.

## Open questions

### OQ-01: Should the unified naming authority live in `artifact_core.py` or a new `artifact_naming.py` module?

- Blocking: no
- Status: open
- Owner: Order 01 executor (record the choice in Order 01)
- Resolution or deferral rationale: `artifact_core.py`'s docstring today deliberately keeps filename-grammar OUT of core (it holds only id6/kebab/IO primitives). Consolidating the grammar there would reverse that stated boundary. A new `artifact_naming.py` that imports core primitives is likely cleaner. Order 01 MUST decide and record; this does not block the orchestrator.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `aw ipd lint --agent` reports `conforming` for all five child IPDs (Orders 01-05) and this orchestrator; the child table lists all five with the recorded dependency order (01->02->03->04, plus 05 after 01); the Set-wide blocking-OQ ledger in E-01 is accurate.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: after all five children are executed, the Cross-IPD validation tests pass (including the identity-slot invariant) and `pytest -n auto` is green (pasted); `aw check all` shows no new Set-attributable findings (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: a single program - "one canonical library per file concern" plus the identity-slot invariant that depends on the naming authority - decomposed into five dependency-ordered children so each is executable and verifiable in one focused pass.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and delegated to Order 01. No blocking open question remains at the orchestrator level. Each child carries its own open questions and must resolve them before its own execution.
2. Scope fence: this orchestrator only coordinates; it makes NO product code changes itself. All code changes happen in the children within their own scope fences. Do not expand any child's scope; if a child seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this Set's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: execute children in order 01->02->03->04, with 05 any time after 01; each transitions to executed on its own completion; then, after E-01 and E-02 here are performed and V-01/V-02 verified with pasted evidence, append the `## Workflow history` line, set this orchestrator `Status: executed`, `git mv` it from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
