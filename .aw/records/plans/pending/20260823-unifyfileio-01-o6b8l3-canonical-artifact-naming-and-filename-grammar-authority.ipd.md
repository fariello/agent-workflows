# IPD: Canonical artifact naming and filename-grammar authority

- Date: 2026-08-23
- Kind: child
- Concern: The artifact filename grammar (`YYYYMMDD-<setid>-NN-<id6>-<slug>[.<facet>].md` and the legacy `YYYYMMDD-HHMM-NN-<slug>` / `<slug>-walkthrough.md` / dated-slug forms) is re-encoded in at least six independent regex/format sites across five modules, plus the `.<type>.md` facet enum is triplicated. These copies must be hand-synchronized; they have already drifted (e.g. walkthroughs validate against a `.walkthrough.md` facet form the builder never produces). There is no single authority that BOTH builds AND validates a name for every artifact type.
- Scope: Create ONE canonical naming/grammar authority module and route every builder and validator through it. Touch: agent_workflows/artifact_rename.py (the `_UNIFORM_RE`/`_LEGACY_TIMESTAMP_RE`/`_WALKTHROUGH_*_RE`/`_DATED_SLUG_FACET_RE` regexes + `compute_target_name`), agent_workflows/plans_refs.py (`_CLUSTERED_RE`, `_BARE_STEM_RE`, `clustered_name`, `ARTIFACT_TYPE_FACETS`), agent_workflows/research_contract.py (`_CORE_RE`, `parse_name`, `format_name`), agent_workflows/plans_index.py (the inline clustered regex in `check_drift`), agent_workflows/check_engine.py (`_TYPE_FACET`, `check_names`), agent_workflows/status_set.py (suffix map / `detect_artifact_type`), agent_workflows/ipd_authoring.py (name derivation), .aw/system/workflows/setup-repo/tools/normalize_plan_names.py (`_NEW_RE`, `_CLUSTERED_RE`, `_LEGACY_RES`, `_ARTIFACT_TYPE_FACETS`, `is_conformant`, `parse_name`), and the naming tests. Does NOT change the grammar itself - byte-for-byte identical names must be produced/accepted.
- Status: reviewed
- Set: unifyfileio
- Order: 1
- Highest E allocated: 06
- Author: Gabriele Fariello
- Id: o6b8l3

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. PR-001 (closed-vs-open facet policy divergence between plans_refs._CLUSTERED_RE and artifact_rename._UNIFORM_RE - added OQ-03 + E-02 guidance); PR-002 (normalize_plan_names is a stdlib-only standalone bootstrap tool - added OQ-04 + E-04 constraint); PR-003 (strengthened V-05 single-source to include facet policy). OQ-02 resolved by human: MIGRATE walkthroughs to .walkthrough.md facet form (added E-06/V-06 migration). OQ-04 resolved by human: normalize_plan_names imports the authority (E-04 must verify setup-repo pre-install import path). Accepted advisory IPD-Z602 on E-04 (single cohesive concern - validator re-routing - with two OQ-gated constraints, not independent deliverables). Verified grammar-site claims at artifact_rename.py:20-38, plans_refs.py:44-55, check_engine.py:29-37, normalize_plan_names.py:107-114.
- 2026-08-23 note (opencode its_direct/pt3-claude-opus-4.8-1m-us): added blocking OQ-05 (walkthrough builder mints its OWN id6; source-plan link is a typed frontmatter field, never the identity slot) per DECISIONS.md D140. The on-disk `p7dqwz` walkthrough fix rides the E-06 walkthrough migration; the `aw check`/`aw doctor` identity-slot enforcement is a separate new child IPD in this Set. Additive OQ only; E-items unchanged (the pre-existing E-04 IPD-Z602 advisory was already accepted above).

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

- [ ] E-02 Create the canonical naming module (per OQ-01: a new `agent_workflows/artifact_naming.py` importing `artifact_core` primitives, unless Order 01 records the `artifact_core.py` alternative) exposing, for each artifact type, a `build_name(components) -> str` and a `parse_name(name) -> ParsedName | None` (plus a `is_conformant(name, type) -> bool` thin wrapper), with ONE definition of the clustered grammar, ONE definition of each legacy form, and ONE facet-enum table. Include research's `.<model>.<kind>` facets as that type's handler. Reconcile the CLOSED-vs-OPEN facet divergence (per OQ-03): `plans_refs._CLUSTERED_RE` uses a CLOSED facet enum (`_FACET_ALT` at `plans_refs.py:44`) while `artifact_rename._UNIFORM_RE` uses an OPEN facet pattern (`[a-z0-9.-]+` at `artifact_rename.py:22`) - the authority MUST pick one canonical facet policy (the closed enum is the safer default, matching the check-engine facet map); any resulting change in which names are ACCEPTED is a golden-suite diff that MUST be confirmed against the E-01 baseline and, if it changes acceptance for real files, surfaced to the human. Do not wire callers yet.
  - Depends on: E-01
  - Expected outcome: one module fully specifies build+parse+validate for all eight types and passes the golden suite when exercised directly.
  - Execution state: pending

### Task group 3: Re-route builders and validators to the authority

- [ ] E-03 Re-route the BUILDERS to the authority: `plans_refs.clustered_name`, `research_contract.format_name`, and `artifact_rename.compute_target_name` (all five legacy branches) call the new module instead of their own local grammar; delete the now-dead local format logic or reduce it to a re-export. Keep `ipd_authoring`'s name derivation on the authority (it currently reaches into `plans_refs._CLUSTERED_RE`).
  - Depends on: E-02
  - Expected outcome: every filename BUILD path goes through the one authority; golden build assertions still green.
  - Execution state: pending

- [ ] E-04 Re-route the VALIDATORS to the authority: `plans_refs._CLUSTERED_RE`/`_BARE_STEM_RE`, `plans_index.check_drift`'s inline clustered regex, `research_contract.parse_name`/`_CORE_RE`, and `check_engine._TYPE_FACET` + `status_set` suffix detection all consult the one authority; remove the duplicate regexes and the triplicated facet enum, leaving a single definition others import. Make the walkthrough builder/validator both use the `.walkthrough.md` FACET form (OQ-02 resolved: migrate); the one-time rename+citation-rewrite of existing suffix-form files is E-06. CONSTRAINT on `normalize_plan_names` (per OQ-04): `.aw/system/workflows/setup-repo/tools/normalize_plan_names.py` provides `is_conformant`/`parse_name`, the conformance authority consumed by `check_engine.check_names` (`check_engine.py:112`) and `ipd_lint` (`ipd_lint.py:72`) - BUT it is a STANDALONE bootstrap tool that imports ONLY stdlib (verified: no `agent_workflows` import) so it can run before the package is installed. Do NOT introduce an `agent_workflows` import into it merely to dedupe. Either (a) leave its grammar copy in place and add a test asserting it stays byte-identical to the authority's definition (drift guard without a runtime dependency), or (b) if the human decides a dependency is acceptable, make it import the authority - but the DEFAULT is (a). If (a), `normalize_plan_names` is an intentional, tested exception to "exactly one copy," documented in E-05's single-source assertion.
  - Depends on: E-02
  - Expected outcome: every filename VALIDATE/parse/facet-detect path in the `agent_workflows` package goes through the one authority; the clustered-grammar regex exists in exactly one place in the package, with `normalize_plan_names` either delegating or a tested byte-identical exception per OQ-04.
  - Execution state: pending

### Task group 4: Prove single-source and no drift

- [ ] E-06 Migrate existing walkthrough files from the `-walkthrough.md` suffix form to the canonical `.walkthrough.md` facet form (OQ-02 resolved: migrate): rename each on-disk walkthrough via `git mv` and rewrite its inbound citations across `.aw/`, using the (Order 03) reference-rewriter if available or the existing per-area rewriter otherwise; verify `aw check walkthroughs` (or `aw check all`) reports the migrated files as name-conformant afterward. This is a one-time data migration gated on E-04's builder/validator agreeing on the facet form.
  - Depends on: E-04
  - Expected outcome: no `-walkthrough.md` suffix-form files remain; all walkthroughs are facet-form and name-conformant, with citations intact.
  - Execution state: pending

- [ ] E-05 Add `tests/test_naming_authority_single_source.py` asserting (a) the golden suite (E-01) still passes unchanged after re-routing; (b) a grep-style structural assertion that the clustered-grammar regex signature AND the facet-enum table AND the facet POLICY (closed-vs-open, per OQ-03) each appear in exactly ONE module in the `agent_workflows` package (all other package modules import them), with `normalize_plan_names` either delegating or covered by the OQ-04 byte-identical drift-guard test as the single documented exception; (c) round-trip property: for every type, `parse_name(build_name(c)) == c` and `build_name(parse_name(n)) == n` for conformant `n`; and confirm `pytest -n auto` is green.
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
- Under-scope: none. Every builder, validator, and facet-enum copy identified in Step 0 is re-routed or removed (with `normalize_plan_names` handled per OQ-04 - delegated or a tested byte-identical exception, never a silent second copy).

## Required tests / validation

- Golden characterization suite `tests/test_naming_authority_golden.py` (E-01) green before and after.
- Single-source + round-trip suite `tests/test_naming_authority_single_source.py` (E-05).
- Walkthrough migration to the `.walkthrough.md` facet form verified (no suffix-form files remain; migrated files name-conformant; citations intact) (E-06, V-06).
- `normalize_plan_names` importing the authority does not break setup-repo's pre-install invocation path (verified in E-04 per OQ-04).
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
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review): MIGRATE walkthroughs to the `.walkthrough.md` FACET form (Option B). The authority's walkthrough BUILDER emits the facet form; existing on-disk `-walkthrough.md` suffix files MUST be renamed to the facet form and their inbound citations rewritten (E-06). This makes walkthroughs uniform with the other types at the cost of a one-time migration.

### OQ-03: Which facet policy is canonical - the CLOSED enum (plans_refs) or the OPEN pattern (artifact_rename)?

- Blocking: no
- Status: open
- Owner: Order 01 executor
- Resolution or deferral rationale: `plans_refs._CLUSTERED_RE` restricts the `.<facet>.md` facet to the known type enum (`plans_refs.py:44`); `artifact_rename._UNIFORM_RE` accepts any `[a-z0-9.-]+` facet (`artifact_rename.py:22`). The authority must adopt one. Closed enum is the safer default (rejects typo'd/unknown facets, matches `check_engine._TYPE_FACET`). Executor decides and records in E-02; any change to which real names are ACCEPTED must be a confirmed golden-suite diff (non-blocking because the golden net catches it, but if it flips acceptance for a real file, surface to the human).

### OQ-04: Should the standalone `normalize_plan_names` bootstrap tool take a runtime dependency on the naming authority, or stay standalone with a drift-guard test?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review): make `normalize_plan_names` IMPORT the naming authority (Option B) - true single copy. CONSEQUENCE the executor MUST handle in E-04: this tool runs during setup-repo; verify WHETHER it is invoked before `agent_workflows` is importable. If setup-repo can run it pre-install, E-04 MUST make the authority importable at that point (e.g. ensure the package is on the path by then, or vendor the authority into an import location the bootstrap can reach) - if that cannot be guaranteed safely, STOP and report rather than silently breaking pre-install setup. Confirm the setup-repo invocation path as part of E-04.

### OQ-05: Does the walkthrough builder mint the walkthrough its OWN id6, and how is the source-plan link expressed?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review) per DECISIONS.md D140: the `<id6>` in the `YYYYMMDD-<setid>-NN-<id6>` identity slot is the UNIQUE IDENTITY of that one file. Therefore the walkthrough builder (already migrating walkthroughs to the `.walkthrough.md` facet form, OQ-02) MUST mint each walkthrough its OWN id6 in the identity slot and MUST NOT reuse the source plan's id6 there; the optional plan link is a TYPED frontmatter field (`Target-Id:`/`References: <id6>`), not the identity slot. Today one on-disk walkthrough violates this (`20260823-artifactenginefix-01-p7dqwz-execution.walkthrough.md` carries the plan's `p7dqwz` in its slot and declares no `- Id:`). The E-06 walkthrough migration in this Set MUST additionally give that file its own id6 + a typed `Target-Id: p7dqwz` and rewrite any inbound citation. NOTE: the `aw check`/`aw doctor` ENFORCEMENT of "a filename-slot id6 must equal the file's own declared Id" (the check `tmp/find_id6_dupes.py` performs; today `check_collisions` reads only the frontmatter `- Id:` line, `check_engine.py:199,237`, and never inspects the filename slot) is a distinct code change tracked as a new child IPD in this Set - do not fold that enforcement into Order 01.

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
- [ ] V-06 validates E-06
  - Required evidence: no `-walkthrough.md` suffix-form files remain (shown by a repo scan); `aw check all` reports the migrated walkthroughs as name-conformant (pasted); a spot-checked inbound citation to a migrated walkthrough resolves to the new facet-form name (no dangling citation).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - consolidate the filename grammar into a single build+validate authority - staged safely (golden net -> build -> re-route -> prove).

### Execution contract

1. Open questions RESOLVED: OQ-01 and OQ-03 delegated to the executor (record in E-02); OQ-02 (walkthrough canonical form) and OQ-04 (normalize_plan_names dependency) MUST be resolved by a human before E-04.
2. Scope fence: consolidate ONLY the filename grammar (build/parse/validate/facets) into one authority and re-route the callers listed in Scope. Do NOT change the grammar, add id6 to legacy types, or touch the selector resolver or reference matcher (later children). If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
