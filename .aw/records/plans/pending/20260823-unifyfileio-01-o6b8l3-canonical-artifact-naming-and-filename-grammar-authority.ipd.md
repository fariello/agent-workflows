# IPD: Canonical artifact naming and filename-grammar authority

- Date: 2026-08-23
- Kind: child
- Concern: The artifact filename grammar (`YYYYMMDD-<setid>-NN-<id6>-<slug>[.<facet>].md` and the legacy `YYYYMMDD-HHMM-NN-<slug>` / `<slug>-walkthrough.md` / dated-slug forms) is re-encoded in at least six independent regex/format sites across five modules, plus the `.<type>.md` facet enum is triplicated. These copies must be hand-synchronized; they have already drifted (e.g. walkthroughs validate against a `.walkthrough.md` facet form the builder never produces). There is no single authority that BOTH builds AND validates a name for every artifact type.
- Scope: Create ONE canonical naming/grammar authority module and route every builder and validator through it. Touch: agent_workflows/artifact_rename.py (the `_UNIFORM_RE`/`_LEGACY_TIMESTAMP_RE`/`_WALKTHROUGH_*_RE`/`_DATED_SLUG_FACET_RE` regexes + `compute_target_name`), agent_workflows/plans_refs.py (`_CLUSTERED_RE`, `_BARE_STEM_RE`, `clustered_name`, `ARTIFACT_TYPE_FACETS`), agent_workflows/research_contract.py (`_CORE_RE`, `parse_name`, `format_name`), agent_workflows/plans_index.py (the inline clustered regex in `check_drift`), agent_workflows/check_engine.py (`_TYPE_FACET`, `check_names`), agent_workflows/status_set.py (suffix map / `detect_artifact_type`), agent_workflows/ipd_authoring.py (name derivation), .aw/system/workflows/setup-repo/tools/normalize_plan_names.py (`_NEW_RE`, `_CLUSTERED_RE`, `_LEGACY_RES`, `_ARTIFACT_TYPE_FACETS`, `is_conformant`, `parse_name`), and the naming tests. Does NOT change the grammar itself - byte-for-byte identical names must be produced/accepted.
- Status: draft
- Set: unifyfileio
- Order: 1
- Highest E allocated: 05
- Author: Gabriele Fariello
- Id: o6b8l3

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.

## Goal

Introduce a single filename-grammar authority (one module) that is the ONLY place that knows how an artifact filename is shaped, exposing two dual operations per artifact type - BUILD (assemble a conformant name from components) and PARSE/VALIDATE (decompose a name into components, or report non-conformance) - and re-route every existing builder and validator to call it. After this child, adding or changing the grammar for a type is a one-file edit, and it is structurally impossible for a builder to emit a name a validator rejects (or vice versa) because they share one definition. The grammar itself does not change: every name produced or accepted today must be produced or accepted identically.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Characterize and lock current behavior (safety net first)

- [ ] E-01 Author a characterization test suite `tests/test_naming_authority_golden.py` that pins the CURRENT observable naming behavior BEFORE any refactor: for every artifact type (plans, research, specs, prompts, backlog, walkthroughs, roadmaps, releases), assert the exact filename produced by the current builder for a fixed set of component inputs, and the exact parse/validate result (conformant/non-conformant + extracted components) of the current validators for a fixed set of names, INCLUDING the legacy forms and the known walkthrough facet-vs-suffix divergence. This is the golden baseline the refactor must not break.
  - Depends on: none
  - Expected outcome: a green golden suite that will turn red if the unification changes any produced/accepted name.
  - Execution state: pending

### Task group 2: Build the single authority

- [ ] E-02 Create the canonical naming module (per OQ-01: a new `agent_workflows/artifact_naming.py` importing `artifact_core` primitives, unless Order 01 records the `artifact_core.py` alternative) exposing, for each artifact type, a `build_name(components) -> str` and a `parse_name(name) -> ParsedName | None` (plus a `is_conformant(name, type) -> bool` thin wrapper), with ONE definition of the clustered grammar, ONE definition of each legacy form, and ONE facet-enum table. Include research's `.<model>.<kind>` facets as that type's handler. Do not wire callers yet.
  - Depends on: E-01
  - Expected outcome: one module fully specifies build+parse+validate for all eight types and passes the golden suite when exercised directly.
  - Execution state: pending

### Task group 3: Re-route builders and validators to the authority

- [ ] E-03 Re-route the BUILDERS to the authority: `plans_refs.clustered_name`, `research_contract.format_name`, and `artifact_rename.compute_target_name` (all five legacy branches) call the new module instead of their own local grammar; delete the now-dead local format logic or reduce it to a re-export. Keep `ipd_authoring`'s name derivation on the authority (it currently reaches into `plans_refs._CLUSTERED_RE`).
  - Depends on: E-02
  - Expected outcome: every filename BUILD path goes through the one authority; golden build assertions still green.
  - Execution state: pending

- [ ] E-04 Re-route the VALIDATORS to the authority: `normalize_plan_names.is_conformant`/`parse_name` (the conformance authority consumed by `check_engine.check_names` and `ipd_lint`), `plans_refs._CLUSTERED_RE`/`_BARE_STEM_RE`, `plans_index.check_drift`'s inline clustered regex, `research_contract.parse_name`/`_CORE_RE`, and `check_engine._TYPE_FACET` + `status_set` suffix detection all consult the one authority; remove the duplicate regexes and the triplicated facet enum, leaving a single definition others import. Resolve the walkthrough facet-vs-suffix divergence explicitly (per OQ-02) so the builder and validator agree.
  - Depends on: E-02
  - Expected outcome: every filename VALIDATE/parse/facet-detect path goes through the one authority; the clustered-grammar regex exists in exactly one place.
  - Execution state: pending

### Task group 4: Prove single-source and no drift

- [ ] E-05 Add `tests/test_naming_authority_single_source.py` asserting (a) the golden suite (E-01) still passes unchanged after re-routing; (b) a grep-style structural assertion that the clustered-grammar regex signature and the facet enum each appear in exactly ONE module (all other modules import them); (c) round-trip property: for every type, `parse_name(build_name(c)) == c` and `build_name(parse_name(n)) == n` for conformant `n`; and confirm `pytest -n auto` is green.
  - Depends on: E-03, E-04
  - Expected outcome: the authority is provably the single source, with round-trip and no-second-copy guarantees.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The grammar is re-encoded in at least six regex/format sites: `artifact_rename._UNIFORM_RE` (`artifact_rename.py:20-23`), `plans_refs._CLUSTERED_RE` (`plans_refs.py:48-51`), `normalize_plan_names._CLUSTERED_RE` (`normalize_plan_names.py:116-119`), the inline clustered regex in `plans_index.check_drift` (`plans_index.py:246-248`), `research_contract._CORE_RE`/`parse_name` (`research_contract.py:229-231,265-317`), plus the five legacy branches inside `artifact_rename.compute_target_name` (`artifact_rename.py:88-149`).
- The `.<type>.md` facet enum is triplicated: `plans_refs.ARTIFACT_TYPE_FACETS` (`plans_refs.py:33-42`), `normalize_plan_names._ARTIFACT_TYPE_FACETS` (`normalize_plan_names.py:114`), and the suffix maps in `check_engine._TYPE_FACET` (`check_engine.py:29-37`) and `status_set` (`status_set.py:142-155`).
- BUILDERS: `plans_refs.clustered_name` (`plans_refs.py:147-167`, also called by `ipd_authoring.py:272`), `research_contract.format_name` (`research_contract.py:255-262`), and `artifact_rename.compute_target_name` (`artifact_rename.py:88`) for the six generic types.
- VALIDATORS / conformance authority: `normalize_plan_names.is_conformant`/`parse_name` (`normalize_plan_names.py:206-220,172-203`) is consumed by `check_engine.check_names` (`check_engine.py:112`) and `ipd_lint._name_conformant` (`ipd_lint.py:72`).
- `research` is deliberately excluded from `check_engine.check_names` (`check_engine.py:118-119`) and has its own grammar - the unified authority must treat research as a type with extra facets, not force it into the plans grammar.
- Known divergence: `check_engine._TYPE_FACET["walkthroughs"]="walkthrough"` expects a `.walkthrough.md` facet, but the builder (`artifact_rename._WALKTHROUGH_*_RE`) produces the `-walkthrough.md` SUFFIX form; `normalize_plan_names.is_conformant` does not recognize the suffix form. This is a real latent bug the unification will surface and must resolve.

## Findings

Because the grammar lives in six+ places, the codebase has already drifted (the walkthrough facet-vs-suffix mismatch above) and cannot be safely evolved: changing the grammar requires editing multiple regexes that no test proves are in sync. Consolidating to one authority with a round-trip property makes the grammar a single, testable, evolvable definition and eliminates the class of "builder emits what the validator rejects" bugs.

## Proposed changes (ordered, validatable)

1. Pin current behavior with a golden characterization suite (E-01).
2. Build the one naming authority module (build + parse + validate + facets, research included) (E-02).
3. Re-route all builders to it (E-03).
4. Re-route all validators + facet detection to it; resolve the walkthrough divergence (E-04).
5. Prove single-source, round-trip, and no-regression (E-05).

## Deferred / out of scope (with reason)

- Changing the grammar or adding id6 to the id6-less legacy types: out of scope; E-02 MUST document how the authority represents id6-less types (specs/prompts/roadmaps/releases/walkthroughs) but not change them.
- The selector resolver and reference matcher: separate children (Orders 02, 03) that DEPEND on this authority.

## Scope check

- Over-scope: none. Only the grammar definition is consolidated; behavior is preserved.
- Under-scope: none. Every builder, validator, and facet-enum copy identified in Step 0 is re-routed or removed.

## Required tests / validation

- Golden characterization suite `tests/test_naming_authority_golden.py` (E-01) green before and after.
- Single-source + round-trip suite `tests/test_naming_authority_single_source.py` (E-05).
- Resolution of the walkthrough facet-vs-suffix divergence covered by an explicit test.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- If a naming spec exists under `.aw/records/specs/` (e.g. the uniform-artifact-naming work), update it to point at the single authority module. Otherwise add a short note in the module docstring designating it the canonical grammar and record N/A for specs.

## Open questions

### OQ-01: Where does the naming authority live - `artifact_core.py` or a new `artifact_naming.py`?

- Blocking: no
- Status: open
- Owner: Order 01 executor
- Resolution or deferral rationale: `artifact_core.py`'s docstring deliberately keeps filename-grammar OUT of core. A new `artifact_naming.py` importing core primitives preserves that boundary and is the likely choice; record the decision in E-02.

### OQ-02: How is the walkthrough facet-vs-suffix divergence resolved - normalize the builder to `.walkthrough.md`, or teach the validator the `-walkthrough.md` suffix?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO (human). The two forms disagree today (`check_engine._TYPE_FACET` vs `artifact_rename._WALKTHROUGH_*_RE`). The unification forces one canonical walkthrough name shape. Option A: keep the existing on-disk `-walkthrough.md` suffix (what files actually use) and fix the validator/facet table to accept it (no file renames). Option B: migrate walkthroughs to `.walkthrough.md` facet form (requires renaming existing walkthrough files + citation rewrites). Option A is lower risk (no on-disk churn); the executor MUST get a human decision before E-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `tests/test_naming_authority_golden.py` runs green against the pre-refactor code and covers all eight types plus legacy forms and the walkthrough case.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the new authority module, exercised directly in a test, reproduces every golden build+parse result for all eight types (research facets included).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: after re-routing builders, the golden BUILD assertions are still green and the local format logic in `plans_refs`/`research_contract`/`artifact_rename` is gone or a re-export (shown by diff).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: after re-routing validators, `aw check all` name-conformance results are unchanged for conformant files; the walkthrough divergence is resolved per OQ-02 with a passing test; the clustered regex and facet enum each exist in exactly one module.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `tests/test_naming_authority_single_source.py` passes (single-source grep assertion + round-trip property for all types) and `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - consolidate the filename grammar into a single build+validate authority - staged safely (golden net -> build -> re-route -> prove).

### Execution contract

1. Open questions RESOLVED: OQ-01 delegated to the executor (record in E-02); OQ-02 (walkthrough canonical form) MUST be resolved by a human before E-04.
2. Scope fence: consolidate ONLY the filename grammar (build/parse/validate/facets) into one authority and re-route the callers listed in Scope. Do NOT change the grammar, add id6 to legacy types, or touch the selector resolver or reference matcher (later children). If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
