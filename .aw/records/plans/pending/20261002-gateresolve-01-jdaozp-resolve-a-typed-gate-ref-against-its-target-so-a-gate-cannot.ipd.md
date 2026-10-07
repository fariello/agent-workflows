# IPD: Resolve a typed gate ref against its target so a gate cannot point at nothing or outlive its blocker

- Date: 2026-10-02
- Kind: child
- Concern: Backlog `2rnswc` asks whether a typed `Gate-Ref` should be RESOLVED against its target rather than only shape-checked, since `artifact`, `decision` and `todo` refs all validate today while potentially pointing at nothing. The `decision` kind was closed by executed plan `jge900` (`check.decision-ref-dangling`), which explicitly deferred the general question here. TWO MEASURED DEFECTS REMAIN, and the second is the one the item did not anticipate. FIRST, NO RESOLUTION: `attention_contract.validate_gate_ref` dispatches `artifact` to `_ARTIFACT_REF_RE` and `todo` to `_TODO_ID_RE` and returns, so a ref naming nothing validates (driven at HEAD `989a01fcc`: `validate_gate_ref('artifact', 'nosuchfile')` and `validate_gate_ref('todo', 'zzzzzz')` are both True), and no `check_engine` rule resolves either kind (searched the registry: the only gate-ref resolution rule is `check.decision-ref-dangling`; `backlog.gate-summary-unexpected` and `backlog.gate-descriptive-unsafe` are shape/presence rules). SECOND, AND THIS IS THE LIVE FAILURE: a gate can OUTLIVE ITS BLOCKER and nothing notices. Every one of the three live gates in the corpus points at a target that is ALREADY TERMINAL OR INACTIVE, so all three are stale, not merely unresolved. Driven over `backlog.parse_item` and `specs._read_gate` at HEAD `989a01fcc`, then resolved through `check_engine.build_dependency_index` and classified through `attention_contract.class_of`: `adgtqb` (`blocked`, `Blocks-Release: next`, `Work-Kind: bug`) carries `Gate-Kind: artifact` / `Gate-Ref: yvvf98`, and `yvvf98` reached `executed` on 2026-09-09 (commit `648def884 lifecycle(yvvf98): finalize yvvf98 -> executed`), which `class_of('plans','executed')` maps to `done`; the two `deferred` specs carry `Gate-Kind: todo` refs `ju93oc` and `m15n3k`, both of which resolve to backlog items whose own status is `parked`, which `class_of` maps to `parked`. So a bug that gates the next release has sat `blocked` for 23 days behind a gate that was discharged, and the repository's own history shows this exact failure already cost a manual catch: commit `7a1e7d062 backlog(h1ksy6): unblock - its artifact gate pointed at the retired 2c122z` records a human finding a gate pointing at a superseded plan and writing in that very commit message "Noted, not filed: aw check did not flag the dangling Gate-Ref when its target was superseded."
- Scope: IN: (1) a resolution helper in `check_engine` that maps a typed `(kind, ref)` onto its in-tree target through the SHIPPED `build_dependency_index` plus a path probe, returning a verdict, with NO new traversal of its own; (2) `check.gate-ref-dangling` at `error`, reporting a well-formed `artifact` or `todo` ref that resolves to NEITHER a repo-relative path NOR any artifact id6 (the hole the item filed); (3) `check.gate-ref-discharged` at `warning`, reporting a gate whose target resolves but whose `attention_contract.class_of` is `done` or `parked`, which is the stale-gate failure measured on all three live gates and the one the `h1ksy6` commit asked for; (4) both rules riding the existing `types == ["all"]` full-sweep seam in their own `try`/`except` beside `check_decision_ref_dangling`; (5) behavior-only tests on throwaway trees, including the three live shapes, a falsifiable negative per rule, and the managed-target-repo case; (6) an amendment to the governing spec Section 8.4, which today says only that `Gate-Ref` is "validated per kind" and must now also state that an in-tree kind is RESOLVED and that a discharged gate is reported; (7) a CHANGELOG entry.
  OUT: resolving `issue` and `external` (not resolvable in-tree, settled below and recorded in the spec amendment rather than left as a reader's inference) and `date` (shape IS its semantics; a past date is not a defect this plan judges); ADDING FILE IO TO `attention_contract`, which is deliberately data-plus-validators and whose `class_of` is documented PURE, so resolution stays in `check_engine` per the shipped dangling-family split; CHANGING `validate_gate_ref` or any per-kind regex (this plan adds resolution beside shape validation and alters no shape); UNBLOCKING `adgtqb` or editing either `deferred` spec, because this plan builds the DETECTOR and a maintainer decides each disposition (E-07 reports them, and `adgtqb` carries a release gate whose close is predicate-governed); resolving `Release-Exempt-Kind:`/`Release-Exempt-Ref:`, which `jge900` F-15 handed here and which is deliberately still deferred below for a measured reason; and re-deriving the runner/queue behavior `AGENTS.md` already settles.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_gate_ref_resolution.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: 2rnswc
- Set: gateresolve
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: jdaozp
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-03 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007. Re-verified the three discharged live gates at lane HEAD a30553683. Contained the path probe (todo refs admit ..), added an unknown verdict for an empty index and a non-id6 todo ref, fixed contradictory case (12), restricted sweeps to live carriers, replaced pinned live counts with a re-derived census set, required the decision-rule severity asymmetry be stated, and completed the execution contract.

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `2rnswc`. Answered the item's OPEN question (which kinds to resolve, at what severity) from driven repository evidence rather than leaving it for the reviewer, and CORRECTED three stale measurements the item carries (its `Gate-Ref: TODO.md` claim, its D156 figure, and its one-gate count), the first of which review `jge900` explicitly asked this item's taker to re-measure. Found a defect the item did not anticipate: all three live gates are not merely unresolved but DISCHARGED, including a release-blocking bug gated behind a plan executed 23 days ago. Two rules at two severities, with the split argued from the shipped registry precedents.

## Goal

Make a typed gate ref a CHECKED reference rather than a well-formed string, so that a gate cannot point at a target that does not exist, and cannot silently outlive the work it was waiting for. The second half is the live failure: three of three gates in the corpus are stale right now, one of them holding a release-blocking bug `blocked` behind a plan that finished on 2026-09-09.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: resolve a typed ref

- [x] E-01 Add a named resolution helper to `check_engine` that takes a repo root, a gate kind and a gate ref and returns a verdict for ONE gate, without walking the tree itself. It must accept a prebuilt index so a sweep over N gates builds the index ONCE; measured, `build_dependency_index` costs about 400ms cold and 276ms warm on this corpus of 2275 indexed id6, so a per-gate rebuild would be the user-perceptible inefficiency `AGENTS.md` classes as a defect. Resolution order and the reason for it: FIRST probe the ref as a repo-relative path, because the spec defines an `artifact` ref as "repo-relative POSIX path (optional Markdown anchor)" and a path is the kind's declared meaning; strip any `#anchor` before the probe, since `_ARTIFACT_REF_RE` admits one and `Path('x.md#a')` would never exist. SECOND, resolve the ref as an artifact id6 through `build_dependency_index`, because EVERY live gate in the corpus is in fact an id6 and not a path (driven: `(root/'yvvf98').exists()` is False while the index resolves it to the executed plan), so a path-only resolver would report all three as dangling and be wrong about all three. Return enough for both rules to act: whether it resolved, by which route, and for an id6 hit the target's record type, status and path. THREE GUARDS ARE PART OF THE HELPER'S CONTRACT, each measured at review (PR-001, PR-002, PR-003): (a) CONTAIN THE PATH PROBE. `_TODO_ID_RE` admits `..` (driven: `validate_gate_ref('todo', '../../etc/passwd')` is True, while `_ARTIFACT_REF_RE` refuses it), so a bare `(root/ref).exists()` resolves OUTSIDE the repository; accept the path route only when the resolved candidate is inside the resolved repo root, and otherwise fall through to the id6 route. (b) RETURN A THIRD VERDICT, `unknown`, distinct from unresolved. `build_dependency_index` SWALLOWS any inventory exception and returns an EMPTY index (its body: `except Exception: return _DepIndex(owners)`), so "not in the index" cannot by itself mean "names nothing": on an empty index an id6 ref must be `unknown`, never unresolved. An empty index is a sound failure signal because the carrier itself is an inventoried record, so a working inventory over a tree carrying any gate is never empty. (c) ONLY AN ID6-SHAPED REF IS JUDGED BY THE INDEX. Section 8.4 defines a `todo` ref as "a TODO id", and a managed target repo may use its own TODO-id namespace (`T-12`, `TODO-42` both pass `_TODO_ID_RE`, driven) that this repository has no way to resolve; this repo's `TODO.md` carries no TODO-id namespace at all (F-10). So a `todo` ref that is neither an in-repo path nor id6-shaped (the shipped `artifact_core.ID6_RE`, `\A[0-9a-z]{6}\Z`) is `unknown`, not unresolved. An `artifact` ref is DECLARED a path, so an `artifact` ref that is neither an in-repo path nor a resolving id6 IS unresolved. DO NOT add file IO to `attention_contract`: that module is deliberately data-plus-validators (driven: it contains no `open`, `read_text`, `Path` or `rglob`) and its `class_of` is documented PURE, which is why `jge900`'s conventions section records that resolution CANNOT live in `validate_gate_ref` and must follow the dangling-family split (shape in the contract module, resolution in a `check_engine` sweep).
  - Depends on: none
  - Expected outcome: the helper resolves `yvvf98` to the executed plan via the id6 route and a real repo-relative path (for example `CHANGELOG.md`) via the path route; it reports unresolved for an `artifact` ref that is neither and for an id6-shaped `todo` ref absent from a non-empty index; it reports `unknown` for a non-id6 `todo` ref such as `T-12`, for any id6 ref against an empty index, and never resolves a `..` ref that escapes the root by the path route; an `#anchor` suffix does not defeat the path route; and one index serves many gates.
  - Execution state: performed

- [x] E-02 Register `check.gate-ref-dangling` in `check_engine.RULE_REGISTRY` at `error` with invariant `I-07`, and add the sweep that emits it for a well-formed `artifact` or `todo` ref resolving to NEITHER a path NOR an id6. The severity is the shipped dangling-family tier and the argument for it is F-13; do not re-derive it here. THE REGISTRY COMMENT MUST NAME THE ASYMMETRY WITH ITS CLOSEST SIBLING (PR-006): `check.decision-ref-dangling`, the existing gate-ref resolution rule, is registered `warning`, so after this plan a dangling `decision` gate is a warning while a dangling `artifact` or `todo` gate is an error. State in the comment why that is acceptable: the decision rule resolves against a repo-local log that may be legitimately incomplete and was deliberately tiered as its `check.review-dangling` twin, whereas an id6 or path ref resolves against the artifact inventory that IS the repository's identity authority, the same authority `check.from-backlog-dangling` (`error`) resolves against. Do not change the decision rule's tier. Enumerate gates through the EXISTING parsers (`backlog.parse_item`, `specs._read_gate`) rather than a new reader. SKIP a ref that is absent or fails `validate_gate_ref`, because that is `backlog.gate-ref-invalid` / `attention.gate-malformed` already and `check_review_dangling` establishes the no-double-report rule in its own code ("a missing/malformed Subject-Id is the parser's diagnostic, not this rule's"). Handle ONLY `artifact` and `todo`, since `decision` is already owned by `check.decision-ref-dangling` and reporting it twice would be one defect under two ids. Report ONLY the helper's `unresolved` verdict, never `unknown` (E-01 guards b and c), so an unbuildable index or a foreign TODO-id namespace produces silence rather than an `error` on every gate. CONSIDER ONLY LIVE GATE CARRIERS, meaning a backlog item at `blocked` and a spec at `deferred`: gate fields on any other status are already `backlog.gate-unexpected` / the spec's "gate fields present on a non-deferred spec" finding, and judging their ref as well would be the double report the previous sentence forbids (PR-004).
  - Depends on: E-01
  - Expected outcome: `aw check all` runs the rule; a backlog item or spec whose `artifact` or `todo` ref names neither a path nor an id6 yields exactly one `check.gate-ref-dangling` finding at `error`; each of the three LIVE gates yields none from this rule, because all three resolve; a malformed ref yields none; a `decision` ref yields none from this rule.
  - Execution state: performed

- [x] E-03 Register `check.gate-ref-discharged` in `check_engine.RULE_REGISTRY` at `warning` with invariant `I-07`, and add the sweep that reports a gate whose target RESOLVES but is no longer live, meaning `attention_contract.class_of(record_type, status)` returns `done` or `parked`. The severity argument is F-13; do not re-derive it here. THIS IS THE RULE THE CORPUS ACTUALLY NEEDS and it is distinct from E-02: E-02 answers "does the referent exist", this answers "is the referent still blocking anything", and all three live gates fail only the second. DERIVE LIVENESS FROM `class_of`, NEVER FROM A HAND-WRITTEN STATUS LIST, because that mapping is the single documented authority for what a native status means and a second list would be the forked vocabulary the registry comments repeatedly warn against. Treat a `class_of` that RAISES as "unknown, do not report" rather than as discharged (F-08 measures 81 inventoried records that raise), and likewise never judge a PATH-route target discharged, since a path carries no status. Apply the same live-carrier restriction as E-02 (blocked backlog item, deferred spec only), for the same no-double-report reason.
  - Depends on: E-01
  - Expected outcome: each of the three live gates (`adgtqb` -> `yvvf98` executed/done; the two `deferred` specs -> `ju93oc`/`m15n3k` parked) yields exactly one `check.gate-ref-discharged` finding at `warning` (the authoring census; the live bar is set equality with a census re-derived at execution, per V-03); a gate pointing at a live target (for example a `pending` plan or an `open` backlog item) yields none; a path-route target yields none; an unmapped status yields none rather than a false positive.
  - Execution state: performed

- [x] E-04 Wire both sweeps into the `types == ["all"]` full-sweep branch of `check_types`, each in its own `try`/`except`, immediately beside the `check_decision_ref_dangling` call, so the three gate-ref rules sit together and a defect in one degrades the sweep rather than breaking `aw check`. Build the dependency index ONCE and share it across both rules rather than letting each build its own (E-01's measured 400ms cold is the reason). Do NOT add either rule to `RELEASE_GATE_RULES` or to `check_release_gates`: that tuple is the release-gate family and has a parity test pinning its membership (`tests/test_check_engine_release_gate.py` asserts the constant), and a gate ref is not a release gate, notwithstanding that the one live `artifact` gate happens to sit on a release-blocking item.
  - Depends on: E-02, E-03
  - Expected outcome: `aw check all` emits both rules; a per-type run such as `aw check backlog` does not run either sweep, matching the documented behavior of its neighbours at that seam; neither rule appears in `RELEASE_GATE_RULES` and that constant's parity test still passes.
  - Execution state: performed

### Task group 2: prove it, amend the contract, and report the three live gates

- [x] E-05 Write `tests/test_gate_ref_resolution.py` covering both rules by BEHAVIOR on throwaway trees, never by reading production source (`AGENTS.md`, GUIDING_PRINCIPLES P16). Required cases: (1) the helper resolves an id6 to its artifact and a repo-relative path to that path, and reports unresolved otherwise; (2) an `#anchor` suffix does not defeat the path route; (3) a dangling `artifact` ref yields exactly one `check.gate-ref-dangling`; (4) a dangling `todo` ref likewise; (5) a resolvable-and-live ref yields NO finding from either rule; (6) a malformed ref yields none from either rule, pinning the no-double-report boundary; (7) a `decision` ref yields none from EITHER new rule, pinning that `check.decision-ref-dangling` keeps sole ownership of that kind; (8) a gate whose target is `executed` yields exactly one `check.gate-ref-discharged`, which is the `adgtqb` shape; (9) a gate whose target is a `parked` backlog item likewise, which is the two `deferred` specs' shape; (10) a target whose `(record_type, status)` pair `class_of` cannot map yields NO discharged finding, the false-positive guard E-03 names; (11) a path-route target yields no discharged finding, since a path has no status; (12) THE MANAGED-TARGET-REPO CASE, stated precisely because the original wording contradicted case (3) (PR-002): the carrier is itself an inventoried record, so "a tree carrying gates but no records" cannot exist and the index is never empty there. The portability guarantee is instead that a gate whose ref the repository CANNOT judge yields no finding: a `todo` ref in a foreign TODO-id namespace (`T-12`) yields nothing from either rule, and the helper with an EMPTY index (simulating the swallowed inventory failure in `build_dependency_index`) yields `unknown` and no finding for an id6 ref; (13) one falsifiable negative PER RULE asserting the rule id and severity the finding actually carries, each demonstrated failing when inverted; (14) a `todo` ref of `../`-escaping shape pointing at a file that exists OUTSIDE the throwaway root does NOT resolve by the path route (PR-001); (15) a gate on a NON-live carrier (an `open` backlog item, or a spec not at `deferred`) yields nothing from either new rule (PR-004). Use the shipped house style for this module family (`unittest.TestCase`, `tempfile.TemporaryDirectory`, hand-written minimal records), and give each backlog fixture the full bullet block including `- Set:`, since an incomplete one draws an unrelated `backlog.set-missing` finding that would make a polarity assertion lie.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: all fifteen cases pass; every assertion is on a returned value, an exit code or an emitted finding; no test reads the live `.aw/records/` for a sweep case; the two falsifiable negatives each fail when inverted.
  - Execution state: performed

- [x] E-06 Amend Section 8.4 of the governing spec `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` so the contract states what the code now enforces, and declare it (it is named in `- Scope-Paths:`). Today that section says only that `Gate-Ref` "is validated per kind" and then gives the per-kind SHAPES; nothing says a ref is resolved, and nothing says what happens when a gate's target completes. The amendment must state: that a ref of an IN-TREE kind (`artifact`, `todo`, `decision`) is resolved against the repository as well as shape-validated; that `issue` and `external` are DELIBERATELY shape-only because neither is resolvable in-tree, and that `date` is shape-only because its shape IS its semantics, so a later reader does not read the asymmetry as an oversight; that a gate whose target has become `done` or `parked` is REPORTED, with the named rule; and the PORTABILITY LIMIT, that resolution is only as complete as the repository's own records, so a ref the repository cannot judge (a `todo` ref outside the id6 namespace, or any ref when the artifact inventory cannot be built) is reported by neither rule, while an `artifact` ref, which is DECLARED a repo path, that names neither an in-repo path nor a resolving id6 is reported as dangling. State also that the path route is CONTAINED to the repository root. AMENDING AN IMPLEMENTED SPEC IS THE CORRECT ROUTE, not a defect to avoid: `AGENTS.md` states a plan that changes behavior a spec describes SHOULD carry the amendment in the same change, and the alternative here would be code enforcing a contract the spec does not describe. Also record the disposition of the spec's OWN open question OQ6, which asks for "the `Gate-Ref` validators per kind ... and `external` acceptance rule": `jge900` settled the `decision` shape and this plan settles resolution, so OQ6's remaining surface should be stated rather than left ambiguous. Do NOT change the spec's `- Status:`, do NOT touch any other section, and do NOT weaken a shipped shape rule (the Section 8.8 `issue`-URL restriction in particular stays exactly as written).
  - Depends on: E-02, E-03
  - Expected outcome: Section 8.4 states resolution, the shape-only kinds with their reason, the discharged-gate rule, and the portability limit; OQ6's disposition is recorded; no other section of the spec is modified and the spec's status is unchanged.
  - Execution state: performed

- [x] E-07 Report the three live stale gates to the maintainer WITHOUT repairing them, and add the CHANGELOG entry. Reporting is the deliverable: this plan ships a detector, and each of the three carriers needs a human disposition this plan has no authority to choose. State for each what the detector found and what the options are: `adgtqb` is `blocked` with `Blocks-Release: next` and `Work-Kind: bug` behind `yvvf98`, which is `executed`, so either the bug is fixed (close it, which is predicate-governed because it carries a release gate) or it is not (repoint the gate at whatever actually remains); and the two `deferred` specs point at `parked` backlog items, which is a gate waiting on work nobody is doing. DO NOT edit any of the three in this plan: `AGENTS.md` makes a release-blocking item's close fail closed without preserved-or-released evidence, and judging whether a measured bug is actually fixed is a maintainer call on evidence, not a side effect of shipping a checker. If executing this plan makes editing them look necessary to get a green sweep, that is the discharged rule working as designed at `warning`; report it in V-07 and leave the records untouched rather than editing them to quiet the output. The CHANGELOG entry names both new rules in the file's existing style, as user-facing prose with no em or en dashes.
  - Depends on: E-05
  - Expected outcome: the three live gates are reported with their measured verdicts and the options for each, none of the three records is modified by this plan, and `CHANGELOG.md` carries one entry naming both rules.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A RULE'S SEVERITY IS A RECORDED DECISION WITH SHIPPED PRECEDENTS ON BOTH SIDES, not a style choice. `check_engine.RULE_REGISTRY` maps each rule id to a `RuleSpec(severity, assurance, determinism, invariant)`, and `rule_spec` returns an error-severity `_DEFAULT_RULESPEC` for anything unregistered, so an unregistered rule is silently an `error`. The dangling family splits deliberately: `check.from-backlog-dangling` and `check.from-spec-dangling` are `error`, while `check.review-dangling` is `warning` with its registry comment stating why (a review left behind by a superseded subject is "UNTIDY, not dangerous"). E-02 matches the `error` precedent and E-03 the `warning` one, each with the reason stated at the item.
- `warning` STILL FAILS THE CHECK EXIT CODE. `artifact_core.drift_exit_code` returns 1 for any finding whose severity is not `info`, so the `error`/`warning` choice is about which LIFECYCLE GATES consume a finding, not about whether it is visible. `info` is the only tier that cannot fail anything, and `_CARRIER_LEGACY_SEVERITY` is the in-tree precedent for choosing it deliberately (a grandfathered population). Neither new rule has a grandfathered population, so `info` is wrong for both.
- `attention_contract` IS DATA PLUS VALIDATORS WITH NO FILE IO, and `class_of` is documented PURE, depending only on `(tree, native_status)` and never inferring from prose, dates or mtime. Driven: the module contains no `open`, `read_text`, `Path` or `rglob`. Resolution needs the filesystem, so it cannot go in `validate_gate_ref`; the shipped split (shape in the contract module, resolution in a `check_engine` sweep) is what backlog `2rnswc` itself points at and what `jge900` followed.
- `class_of` IS NOT TOTAL OVER WHAT THE INVENTORY ACTUALLY HOLDS, which is why E-03 must treat a raise as unknown. Driven over `status_set.inventory_all_artifacts` at HEAD `989a01fcc`: 2331 records inventoried, 2250 classify, and 81 raise, comprising `('plans', None)` 24, `('prompts', None)` 20, `('walkthroughs', None)` 24, `('research', None)` 9, `('roadmaps', None)` 1, `('roadmaps','archive')` 1, `('roadmaps','reference')` 1 and `('plans','EXECUTED')` 1. The mapping is total over each tracked tree's declared ENUM; it is not total over every status string on disk.
- CODE IS CITED BY SYMBOL OR QUOTED STRING, with a line number only ever appended to one of those and never standing alone, because an offset expires before the plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this plan names a symbol, quotes content, or cites a commit hash.
- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE (`AGENTS.md`, GUIDING_PRINCIPLES P16). No test may read production source via `inspect`, `ast`, regex or substring search, assert a caller count or symbol census, or pin a docstring or comment banner. E-05 is written to that rule.
- THE SUITE IS RUN BARE as `python3 -m pytest`, because `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'` (quoted). Adding `-n0` makes it several times slower, a second `-q` suppresses the `N passed` line this plan must paste, and `-p no:randomly` disables the order randomization that surfaces order dependence.
- A SWEEP TEST MUST USE A THROWAWAY TREE, not the live records. Other sessions modify `.aw/records/` concurrently (this checkout is shared, per `AGENTS.md`), and `tests/test_decision_ref_resolution.py` is the in-tree model for the pattern: every sweep case builds a `TemporaryDirectory`, and the one live-corpus case asserts a FLOOR rather than a pinned count precisely because the corpus drifts.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **NO RULE RESOLVES AN `artifact` OR `todo` GATE REF, which is the hole the item filed.** `validate_gate_ref` dispatches `artifact` to `_ARTIFACT_REF_RE` and `todo` to `_TODO_ID_RE`, both pure anchored regexes, and returns. The only gate-ref resolution rule in the registry is `check.decision-ref-dangling`, added by `jge900`. | Driven at HEAD `989a01fcc`: `validate_gate_ref('artifact','nosuchfile')` and `validate_gate_ref('todo','zzzzzz')` both return True. Registry searched for gate rules: only `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.live-bug-ungated`, `backlog.gate-summary-unexpected`, `backlog.gate-descriptive-unsafe` and `check.decision-ref-dangling`, none of which resolves an `artifact` or `todo` ref. |
| F-02 | **ALL THREE LIVE GATES ARE DISCHARGED, NOT DANGLING, and that is the failure worth building for.** Every one resolves, so E-02 alone would report zero; every one points at a target that is terminal or inactive, so E-03 reports three. This inverts the item's framing, which expected "a gate can be repointed or outlived and nothing detects it" to be a contract question with a one-record blast radius: the outliving has ALREADY HAPPENED on every gate in the repository. | Driven at HEAD `989a01fcc` over `backlog._iter_items` + `backlog.parse_item` (889 items) and `specs._spec_files` + `specs._read_gate` (40 specs), then resolved via `build_dependency_index` and classified via `class_of`. `adgtqb` (`blocked`): `artifact`/`yvvf98` -> plans/executed/**done**. `20260725-0957-01-external-delivery-and-skills.spec.md` (`deferred`): `todo`/`ju93oc` -> backlog/parked/**parked**. `20260726-1239-01-clean-delta-and-tracking-modes.spec.md` (`deferred`): `todo`/`m15n3k` -> backlog/parked/**parked**. Path probe for all three: `(root/ref).exists()` is False, so all three are id6 refs. |
| F-03 | **A RELEASE-BLOCKING BUG HAS BEEN BLOCKED BEHIND FINISHED WORK FOR 23 DAYS.** `adgtqb` carries `- Status: blocked`, `- Blocks-Release: next` and `- Work-Kind: bug`, gated on `yvvf98`. `yvvf98` finalized to `executed` on 2026-09-09. The item was last touched on 2026-09-13, four days AFTER its gate target completed, by a sweep that gated ten bug items on the next release, so nothing in that touch re-examined the gate. Its own body also asserts premises that are now FALSE: it says `.aw/records/plans/INDEX.json` is TRACKED and NOT ignored, and the fix would make the ignore true. Both are now the opposite, which is consistent with `yvvf98` having landed. Whether the bug is fully fixed is a maintainer judgement (E-07 reports, does not decide). | `git log -1 --format=%h %ad` for `yvvf98`'s executed path: `648def884 2026-09-09 lifecycle(yvvf98): finalize yvvf98 -> executed`. For `adgtqb`: `151bcc86a 2026-09-13 backlog: gate the ten carrier-less bug items on the next release`. Driven at HEAD `989a01fcc`: `git ls-files --error-unmatch .aw/records/plans/INDEX.json` reports it is NOT tracked, and `git check-ignore -v` resolves it to `.aw/.gitignore:45 records/plans/INDEX.json`, so it IS ignored. `.aw/.gitignore` carries all four anchored INDEX entries. |
| F-04 | **THIS EXACT FAILURE ALREADY COST A MANUAL CATCH AND THE REPOSITORY ASKED FOR THIS RULE IN WRITING.** Commit `7a1e7d062` unblocked `h1ksy6` after a human discovered its `Gate-Kind: artifact` / `Gate-Ref: 2c122z` pointed at a plan retired to `superseded/`, which "would have left this item blocked forever". That commit message ends with the request this plan answers: "Noted, not filed: aw check did not flag the dangling Gate-Ref when its target was superseded." So the need is evidenced by a past incident, not inferred from a hypothetical. | `git show 7a1e7d062` read in full; quoted strings are verbatim from its message. |
| F-05 | **THE SHIPPED INDEX ALREADY RESOLVES EVERY LIVE REF, so E-01 adds a lookup and not a resolver.** `build_dependency_index` returns id6 -> [(record_type, status, path)] built from `status_set.inventory_all_artifacts`, and it is the precedent for typed edge resolution: `_resolve_edge` already returns `ok`/`dangling`/`ambiguous` against it for `Item-Dependencies`. All three live refs resolve through it; zero id6 in the corpus are ambiguous. | Driven at HEAD `989a01fcc`: index holds 2275 id6, of which 0 map to more than one owner. `idx.owners['yvvf98']` -> `[('plans','executed', '.../20260906-idxuntrack-02-yvvf98-...ipd.md')]`; `ju93oc` and `m15n3k` each -> one `('backlog','parked', ...)`. |
| F-06 | **BUILDING THE INDEX PER GATE WOULD BE A USER-PERCEPTIBLE DEFECT, which is why E-01 takes a prebuilt one.** Measured 400ms cold and 276ms warm for one `build_dependency_index` over this corpus. Three gates today is 1.2s; the rules are permanent and the corpus grows. `AGENTS.md` classes inefficiency a user can notice as a `bug`, and a sweep that rebuilds an index per record is exactly the shape of the measured `aw find` double-read defect (backlog `59t9x5`, reclassified `chore` -> `bug` for about 128ms of a 530ms command). | Timed at HEAD `989a01fcc` with two successive calls in one process: 400ms then 276ms. |
| F-07 | **A PATH-ONLY RESOLVER WOULD BE WRONG ABOUT EVERY LIVE GATE, and a path probe is still required.** No live ref is a path: all three are id6 and `(root/ref).exists()` is False for each. But the spec DEFINES an `artifact` ref as a repo-relative POSIX path with an optional anchor, and `_ARTIFACT_REF_RE` admits exactly that, so a path ref is legal and must resolve. Hence both routes, with the path probe stripping any `#anchor` first, since `Path('TODO.md#notes')` cannot exist. | Driven: `(root/'yvvf98').exists()`, `(root/'ju93oc').exists()`, `(root/'m15n3k').exists()` all False, while each resolves as an id6. `validate_gate_ref('artifact','TODO.md#notes')` is True and `validate_gate_ref('todo','TODO.md#notes')` is False (`_TODO_ID_RE` admits no `#`), so the anchor case is reachable for `artifact` only. Spec Section 8.4 quoted: "`artifact` = repo-relative POSIX path (optional Markdown anchor)". |
| F-08 | **`class_of` MUST BE THE LIVENESS AUTHORITY, AND IT RAISES OFTEN ENOUGH THAT A RAISE CANNOT MEAN DISCHARGED.** It is the single documented mapping from a native status to an attention class, and it maps `executed` -> `done`, `parked`/`superseded`/`not-executed` -> `parked`, `approved`/`reusable`/`open` -> `ready`. But 81 inventoried records raise, so E-03 must treat a raise as unknown or it would invent findings on records whose status it cannot interpret. | Driven at HEAD `989a01fcc`: 2250 of 2331 inventoried records classify; the 81 that raise are `('plans',None)` 24, `('walkthroughs',None)` 24, `('prompts',None)` 20, `('research',None)` 9, `('roadmaps',None)` 1, `('roadmaps','archive')` 1, `('roadmaps','reference')` 1, `('plans','EXECUTED')` 1. Also driven: `class_of('plans','pending')` RAISES (plans carry disposition in the directory, readiness in `Status:`), so a plans target's liveness must be read from the status the inventory reports, not guessed. |
| F-09 | **`issue`, `external` AND `date` ARE CORRECTLY SHAPE-ONLY, and saying so in the spec is part of the deliverable.** `issue` is an absolute http(s) URL and resolving it means a network fetch, which no `aw check` rule performs and which would make a deterministic rule nondeterministic; Section 8.8 additionally says `external` refs are "treated as opaque data, never as a fetchable/executable target". `date` has no referent: its shape is its meaning. The item's OPEN question asked which kinds to resolve; this is the answer and its reason, recorded in the spec by E-06 rather than left as a reader's inference. | Spec Section 8.8 quoted. `RULE_REGISTRY` determinism vocabulary is `DET_DETERMINISTIC`/`DET_HEURISTIC`/`DET_ATTESTED`; no shipped rule performs network IO. `validate_gate_ref` dispatches `issue` to `_HTTP_URL_RE`, `date` to `_DATE_RE`, and `external` to a nonempty check. |
| F-10 | **THE ITEM CARRIES THREE STALE MEASUREMENTS, one of which its own review asked this taker to re-measure.** (a) It says two deferred specs' "Gate-Ref: TODO.md still validates after the awaited content was migrated away"; they carry `Gate-Kind: todo` with id6 refs `ju93oc`/`m15n3k`, and review `jge900` PR-005 recorded this exact error and said it "is recorded here so whoever takes `2rnswc` re-measures rather than inheriting it". (b) It says `DECISIONS.md` "stops at D156"; it now stops at D158, and `jge900` F-14 measured the log growing 153 -> 156 over three weeks, so a pinned count was always the wrong bar. (c) It says "Exactly ONE item in the live corpus carries a gate at all", true of the BACKLOG tree only; the corpus carries three gates across two trees. The item's question is unaffected and its requirements are not edited by this plan; the corrected measurements are recorded here so the next reader does not inherit them. | (a) driven over `specs._read_gate`, both gates are `todo` with id6 refs; `jge900`'s review record read. (b) `check_engine.parse_decision_ids` returns 158 at HEAD `989a01fcc`. (c) the three-gate census in F-02. Separately, `TODO.md` at HEAD carries no checkbox items and no TODO-id tokens (driven: 0 of each), so a `todo` ref has no TODO-id namespace to resolve against at all, which is why `_TODO_ID_RE` refs are in practice id6. |
| F-11 | **NO PENDING PLAN COLLIDES SEMANTICALLY, and no dependency edge is owed.** Three pending plans declare `agent_workflows/attention_contract.py` (`qpw45x`, `0obt4k`, and `nllamb`); this plan declares that file NOT AT ALL, so even file-level overlap is absent there. `0obt4k` and `qpw45x` are output-safety work (the Section 8.8 control-character predicate and Markdown escaping) and neither touches resolution. Two pending plans declare `agent_workflows/check_engine.py` alongside other subjects (`1znlxy`, duplicate metadata bullets on specs); none adds a gate-ref rule. `AGENTS.md` also settles the runtime question: each execute item gets its own isolated worktree, so declared file overlap is not a concurrency hazard. | Each plan's `- Scope-Paths:` read. `0obt4k` and `qpw45x` searched: their `validate_gate_ref` mentions are to the output-safety validator path, with no `Gate-Ref` resolution, no `build_dependency_index` and no `class_of`. |
| F-14 | (review PR-001) **THE PATH PROBE CAN ESCAPE THE REPOSITORY for a `todo` ref.** `_TODO_ID_RE` admits `..`, `_ARTIFACT_REF_RE` does not. | Driven: `validate_gate_ref('todo','../../etc/passwd')` True, `validate_gate_ref('artifact','../x')` False; `(tmp/'../../etc/passwd').exists()` True. |
| F-15 | (review PR-002/PR-003) **AN UNRESOLVED VERDICT NEEDS A THIRD STATE.** `build_dependency_index` returns an empty index on ANY inventory exception (`except Exception: return _DepIndex(owners)`), and a managed repo's `todo` refs may use a non-id6 TODO-id namespace (`T-12`, `TODO-42` both validate). Without `unknown`, an inventory failure or a foreign namespace turns every gate into an `error`. Separately, the original case (12) asserted silence for exactly the shape case (3) asserts an error for, since the carrier is itself inventoried. | Driven: empty tmp tree index has 0 owners; a tmp tree with one blocked backlog item indexes that item (with or without `git init`); `validate_gate_ref('todo','T-12')` True. |
| F-16 | (review PR-004) **GATE FIELDS ON A NON-LIVE CARRIER ARE ALREADY A FINDING.** `backlog.gate-unexpected` ("gate fields present on a non-blocked item") and the spec's "gate fields present on a non-deferred spec" own that case, so the new rules consider only blocked items and deferred specs. | `backlog.py` and `specs.py` drift emitters read. |
| F-12 | **THE SWEEP SHIPS WITH A KNOWN, INTENDED NONZERO COUNT, so the validation bar is census-equality rather than clean.** E-02 adds zero findings to the live corpus (all three gates resolve) and E-03 adds exactly three. The baseline at HEAD `989a01fcc` is 89 findings over 2546 records, so the tree is already red on unrelated rules and "no worsening" is not the right bar either: the expected change at authoring was 89 -> 92, with the three new ones being precisely the three records F-02 names; this is CONTEXT, and the executable bar is the re-derived census set in V-03. | `aw check all` at HEAD `989a01fcc`: "89 finding(s) detected across 2546 all", exit 1. Existing finding families include `check.ipd-uncarried-obligation`, `check.plan-spec-link-missing`, `check.scope-path-target-stale` and `check.name-nonconformant`; none is `check.gate-ref-*`. |
| F-13 | **THE TWO SEVERITIES ARE SET BY THE SHIPPED REGISTRY AND BY ONE STATED JUDGEMENT, not by preference.** E-02 takes `error` because the two registered rules whose subject is a typed link naming nothing, `check.from-backlog-dangling` and `check.from-spec-dangling`, are both `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`, and a gate ref with no referent is that same defect class. `check.review-dangling` is `warning` for a reason that does NOT transfer, quoted from its registry comment: a review left behind by a superseded subject is "UNTIDY, not dangerous". A gate naming nothing IS dangerous, because it is the stated authority for an artifact being `blocked`, which `attention_contract` documents as "work is intended to continue but a named GATE prevents progress". E-03 takes `warning` on the one judgement in this plan: a DISCHARGED gate is a record needing a human disposition rather than a malformed record, and `error` would additionally turn the sweep red on three records this plan deliberately does not edit, converting a detector into a forced edit of a release-gated item. `warning` still fails the exit code, so nothing is hidden. | Registry entries and comments read at the three named rule ids. `artifact_core.drift_exit_code` returns 1 for any severity that is not `info`. The `blocked` class definition is quoted from the `attention_contract` module docstring. |

## Proposed changes (ordered, validatable)

1. `check_engine`: a named gate-ref resolution helper taking `(repo_root, kind, ref, index)` and returning a verdict with the resolution route and, for an id6 hit, the target's record type, status and path. No new traversal; no IO added to `attention_contract`.
2. `check_engine.RULE_REGISTRY`: `check.gate-ref-dangling` at `error` with invariant `I-07`, matching the `from-backlog`/`from-spec` dangling tier.
3. `check_engine`: the sweep emitting that rule for `artifact` and `todo` refs that resolve to neither a path nor an id6, skipping absent, malformed and `decision` refs.
4. `check_engine.RULE_REGISTRY`: `check.gate-ref-discharged` at `warning` with invariant `I-07`.
5. `check_engine`: the sweep emitting that rule for a gate whose resolved target classifies `done` or `parked` via `class_of`, treating a `class_of` raise and a path-route target as unknown.
6. `check_engine.check_types`: both sweeps wired into the `types == ["all"]` branch in their own `try`/`except` beside `check_decision_ref_dangling`, sharing one dependency index. Neither is added to `RELEASE_GATE_RULES`.
7. `tests/test_gate_ref_resolution.py`: fifteen behavior-only cases on throwaway trees, with a falsifiable negative per rule.
8. `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`: Section 8.4 amended to state resolution, the shape-only kinds and their reason, the discharged-gate rule, the portability limit, and OQ6's disposition.
9. `CHANGELOG.md`: one entry naming both rules.

## Deferred / out of scope (with reason)

- REPAIRING THE THREE LIVE STALE GATES. E-07 reports them; this plan does not edit them. `adgtqb` carries `- Blocks-Release: next`, and `AGENTS.md` makes a release-blocking item's close FAIL CLOSED unless the gate is provably handed off, satisfied with cited evidence, or explicitly cleared; deciding which applies requires judging whether the measured dirty-index bug is actually fixed, which is a maintainer call on evidence. The two `deferred` specs point at `parked` work, so their disposition is a scheduling decision. A checker that edits the records it judges is also how a detector's own evidence gets destroyed.
  - Carrier: 2rnswc
- RESOLVING A `Release-Exempt-Ref:`. `jge900` F-15 handed this here, and it is deliberately still deferred: the pair shares `GATE_KINDS` and `validate_gate_ref` but is a RELEASE-EXEMPTION assertion rather than a blocking gate, so "discharged" has no meaning for it (an exemption does not stop being true when its referent completes), and only the dangling half would transfer. No live record carries the pair (driven: zero across `.aw/records/`, only README prose), so there is nothing to measure a rule against and no way to know whether it would ship green. Filing a rule for an empty population is the gold-plating `jge900` D-1 refused for the analogous case.
  - Carrier: 2rnswc
- RESOLVING `issue` AND `external` REFS. Neither is resolvable in-tree: `issue` would require a network fetch, which no `aw check` rule performs and which would break the deterministic-rule contract, and Section 8.8 states `external` refs are "treated as opaque data, never as a fetchable/executable target" (F-09). E-06 records this as a decided asymmetry in the spec rather than leaving it as an apparent omission.
  - Carrier-Declined: the question is ANSWERED, not postponed, and the answer is recorded in the spec by E-06; a carrier would imply unfinished work.
- JUDGING A PAST `date` GATE. `date` has no referent to resolve, and whether a past date means a gate expired is a policy question about what a date gate asserts, not a reference-integrity defect. No live record carries one.
  - Carrier-Declined: no live record carries a `date` gate and no defect is measured; filing a carrier for a hypothetical would add a record nothing drives.
- WIDENING ANY PER-KIND SHAPE REGEX. This plan adds resolution beside shape validation and changes no shape. `jge900` already widened `_DECISION_ID_RE`, and touching `_ARTIFACT_REF_RE` or `_TODO_ID_RE` would be an unrequested contract change.
  - Carrier-Declined: no change is proposed or needed; the shapes are correct for what they validate.

## Scope check

- Over-scope: none. Every E-item serves either the resolution hole the item filed (E-01, E-02), the discharged-gate failure measured on every live gate (E-03), their wiring (E-04), their proof (E-05), the contract the code now enforces (E-06), or the report the three live findings require (E-07).
- Under-scope: the plan does not repair the three stale gates it finds, by design and with the reason recorded above. A reader should expect `aw check all` to report three `check.gate-ref-discharged` findings AFTER this plan executes, and that is the plan succeeding, not failing.
- Under-scope, deliberate: `Release-Exempt-Ref:` is not resolved, for a reason stronger than scheduling (no live population, and "discharged" is meaningless for an exemption), so backlog `2rnswc` keeps the carrier.
- Under-scope, deliberate: resolution is only as complete as the repository's own records. In a managed target repo with few or no artifacts, both rules emit little or nothing. That is the correct behavior (it is the portability lesson `jge900` PR-001 measured) and E-06 records it in the spec so nobody is told they have a check they do not have.

## Required tests / validation

- `python3 -m pytest` run BARE, with the `N passed` summary line and its HEAD pasted. Also `tests/test_gate_ref_resolution.py` run directly for per-case visibility.
- `aw check all` BEFORE and AFTER with the HEAD of each. The bar is NOT a clean tree and NOT no-worsening: measure your own baseline (89 findings over 2546 records at HEAD `989a01fcc`) and demonstrate the delta consists ONLY of the two new rule ids, with every pre-existing finding unchanged: zero `check.gate-ref-dangling` if every live gate still resolves, and `check.gate-ref-discharged` on exactly the set an independent execution-time census identifies (V-03). Compare finding SETS by `(rule, location)` before and after, not totals, because other lanes move the baseline; the authoring figures (89 before, 3 new, at `989a01fcc`) are context only (PR-005).
- `aw ipd lint` on this plan, conforming.
- Driven before-and-after for each defect: a dangling `artifact` ref and a dangling `todo` ref each going from undetected to one `error` finding; and each of the three live gates going from undetected to one `warning` finding naming its resolved target's status.
- THE FALSE-POSITIVE GUARDS, driven and pasted, each of which is a case where a naive implementation would be wrong: a `class_of`-unmappable target yields no discharged finding; a path-route target yields no discharged finding; a malformed ref yields nothing from either rule; a `decision` ref yields nothing from either new rule; a `todo` ref the repository cannot judge (a non-id6 TODO id, or any id6 against an empty index) yields nothing; and a gate on a non-live carrier yields nothing from either new rule.
- Confirmation that `RELEASE_GATE_RULES` is unchanged and its parity test still passes, and that a per-type run (`aw check backlog`) runs neither new sweep.

## Spec / documentation sync

- A SPEC AMENDMENT IS DECLARED AND IS A DELIVERABLE. `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` is named in `- Scope-Paths:` and amended by E-06. The reason is the one `AGENTS.md` gives: this plan changes behavior the spec describes, so the amendment belongs in the same change rather than leaving code enforcing a contract the spec is silent about. Section 8.4 currently specifies only per-kind SHAPES and says `Gate-Ref` "is validated per kind"; after E-06 it also states that an in-tree kind is RESOLVED, which kinds are deliberately shape-only and why, that a discharged gate is reported, and the portability limit. The spec's `- Status:` is NOT changed and no other section is touched; the Section 8.8 `issue`-URL restriction in particular is preserved verbatim.
- The spec's own OQ6 ("the `Gate-Ref` validators per kind ... and `external` acceptance rule") is the open question this plan closes for resolution, as `jge900` closed it for the `decision` shape. E-06 records its disposition rather than leaving it to look unanswered.
- `CHANGELOG.md` is updated by E-07.
- No README change is proposed. `.aw/records/backlog/README.md` already documents the gate fields and, since `jge900` E-05, carries the maintainer-ruling citation section; the new rules are checker behavior, which the registry and the spec describe.

## Open questions

### OQ-01: Each of the three live gates needs a maintainer disposition, and `adgtqb` in particular needs a judgement this plan cannot make: is the dirty-index bug actually fixed now that `yvvf98` is executed?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: adgtqb
- Resolution or deferral rationale: NOT BLOCKING, because every E-item is correct regardless of the answer: the resolution hole and the discharged-gate hole are defects whether or not any particular carrier is then unblocked, and E-07 deliberately REPORTS rather than repairs. The question is raised because the answer belongs to the maintainer on two counts. First, `adgtqb` carries `- Blocks-Release: next` and `- Work-Kind: bug`, so closing it is predicate-governed and needs either a handoff carrier or cited evidence; the circumstantial evidence is strong (its two load-bearing premises are now false at HEAD: `.aw/records/plans/INDEX.json` is untracked and is ignored via `.aw/.gitignore`), but "the premises inverted" is not the same as "every symptom the item records is gone", and asserting the latter without driving a finalize would be exactly the unverified completion claim the execution contract forbids. Second, the two `deferred` specs are gated on `parked` backlog items, which is a scheduling choice (unpark the work, repoint the gate, or accept the specs stay deferred) rather than a defect.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste a driven demonstration of the helper on the LIVE repo for all three routes: `yvvf98` resolving by the id6 route with its reported record type, status and path; a real repo-relative path (for example `CHANGELOG.md`) resolving by the path route; and a ref that is neither reporting unresolved. Paste the anchored case showing a path ref with `#anchor` still resolving by the path route and stating that the anchor was stripped before the probe. Paste the three guard verdicts driven on throwaway trees: a `todo` ref `../<...>` naming a file that exists OUTSIDE the root does NOT resolve by the path route; a `todo` ref `T-12` returns `unknown`; and an id6 ref against an empty `_DepIndex` returns `unknown`, not unresolved. Then paste the EFFICIENCY evidence, which is the reason this item has a shape at all: show that the helper accepts a prebuilt index and that resolving all three live gates builds the index ONCE, with your own re-measured `build_dependency_index` timing (authoring measured 400ms cold / 276ms warm over 2275 id6; re-measure rather than quoting those). Finally state in writing that `agent_workflows/attention_contract.py` is NOT in this plan's `- Scope-Paths:` and was not modified, and paste `git diff --stat` for it showing no change, since the no-IO property of that module is the constraint this item is built around.
  - Observed evidence:
    Driven resolution routes on live repository:
    ```python
    >>> idx = check_engine.build_dependency_index(repo_root)
    >>> check_engine.resolve_gate_ref(repo_root, 'artifact', 'yvvf98', index=idx)
    GateRefResolution(verdict='resolved', route='id6', record_type='plans', status='executed', path='.../.aw/records/plans/executed/20260906-idxuntrack-02-yvvf98-untrack-the-four-generated-index-manifests-and-reconcile-sta.ipd.md')
    >>> check_engine.resolve_gate_ref(repo_root, 'artifact', 'CHANGELOG.md', index=idx)
    GateRefResolution(verdict='resolved', route='path', record_type=None, status=None, path='CHANGELOG.md')
    >>> check_engine.resolve_gate_ref(repo_root, 'artifact', 'nosuchfile.md', index=idx)
    GateRefResolution(verdict='unresolved', route=None, record_type=None, status=None, path=None)
    ```
    Anchored case (`#anchor` stripped before probe):
    ```python
    >>> check_engine.resolve_gate_ref(repo_root, 'artifact', 'CHANGELOG.md#anchor', index=idx)
    GateRefResolution(verdict='resolved', route='path', record_type=None, status=None, path='CHANGELOG.md')
    ```
    The anchor was stripped via `ref.split('#', 1)[0]` before checking candidate path existence.

    Three guard verdicts driven on throwaway trees:
    ```python
    # Guard (a): Escaped path probe
    >>> check_engine.resolve_gate_ref(root, 'todo', '../outside.txt')
    GateRefResolution(verdict='unknown', route=None, record_type=None, status=None, path=None)
    # Guard (c): Foreign TODO-id namespace
    >>> check_engine.resolve_gate_ref(root, 'todo', 'T-12')
    GateRefResolution(verdict='unknown', route=None, record_type=None, status=None, path=None)
    # Guard (b): Empty index
    >>> check_engine.resolve_gate_ref(root, 'todo', 'zzzzzz', index=check_engine._DepIndex({}))
    GateRefResolution(verdict='unknown', route=None, record_type=None, status=None, path=None)
    ```

    Efficiency evidence:
    Re-measured `build_dependency_index` timing on this corpus (2416 id6 indexed):
    Cold: 1584.0ms
    Warm: 1260.1ms
    Resolving all three live gates (`yvvf98`, `ju93oc`, `m15n3k`) with a single prebuilt index passes `index=idx` to `resolve_gate_ref`, executing the 3 lookups in under 1ms total without rebuilding the inventory index.

    No-IO constraint confirmation:
    `agent_workflows/attention_contract.py` is NOT declared in `- Scope-Paths:` and was not modified.
    `git diff --stat HEAD agent_workflows/attention_contract.py` output:
    (empty - no modifications)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `RULE_REGISTRY` entry as committed, showing `error` severity and invariant `I-07`, and state which two shipped rules set that precedent (`check.from-backlog-dangling`, `check.from-spec-dangling`) and why `check.review-dangling`'s `warning` was rejected, quoting its "UNTIDY, not dangerous" rationale and saying why a gate is not in that class. Paste a driven before-and-after on a throwaway tree for a dangling `artifact` ref and a dangling `todo` ref: undetected before, exactly one `check.gate-ref-dangling` at `error` after, for each. Paste the registry comment naming the `check.decision-ref-dangling` (`warning`) asymmetry and its reason. Paste the no-double-report boundaries: a gate on a non-live carrier (an `open` backlog item) yields nothing from this rule, a `unknown` verdict yields nothing, a malformed ref yields nothing from this rule, a `decision` ref yields nothing from this rule (ownership stays with `check.decision-ref-dangling`), and an absent ref yields nothing. Paste the LIVE-CORPUS result showing ZERO `check.gate-ref-dangling` findings, and state explicitly that zero is the EXPECTED outcome because all three live gates resolve (F-02), not evidence that the rule is inert; the dangling behavior is demonstrated on the throwaway trees above.
  - Observed evidence:
    `RULE_REGISTRY` entry as committed:
    ```python
    # gateresolve jdaozp E-02: a Gate-Kind: artifact or todo ref that resolves to neither an in-repo path
    # nor an id6 in the artifact inventory. Registered `error` with invariant I-07, matching the shipped
    # `check.from-backlog-dangling` and `check.from-spec-dangling` dangling-family tier (an unresolvable
    # identity reference).
    # ASYMMETRY WITH CLOSEST SIBLING `check.decision-ref-dangling` (registered `warning`): acceptable
    # because the decision rule resolves against a repo-local markdown log (DECISIONS.md) that may be
    # legitimately incomplete and was deliberately tiered as its `check.review-dangling` twin ("UNTIDY,
    # not dangerous"), whereas an id6 or path ref resolves against the artifact inventory that IS the
    # repository's identity authority, the same authority `check.from-backlog-dangling` (`error`)
    # resolves against. A dangling gate reference naming nothing is dangerous because it is the stated
    # authority for an artifact being `blocked`. Deterministic: literal path and index membership.
    "check.gate-ref-dangling": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    ```
    Precedent and severity rationale:
    The two shipped rules setting the `error` precedent are `check.from-backlog-dangling` and `check.from-spec-dangling` (both registered `error` with invariant `I-07`), policing identity references that point at nothing. `check.review-dangling` is registered `warning` because a review left behind by a superseded subject is "UNTIDY, not dangerous". A dangling gate is not in that class: a gate is the stated authority for an artifact being `blocked`, so pointing at nothing is dangerous and invalidates the blocking premise.

    Driven before-and-after on throwaway trees:
    Before (prior to jdaozp): neither rule existed, 0 findings emitted.
    After:
    - Dangling `artifact` ref (`nonexistent/doc.md`): exactly one finding:
      `Drift(location='.../item.backlog.md', rule='check.gate-ref-dangling', detail="Gate-Ref 'nonexistent/doc.md' does not resolve to any in-tree path or artifact id6", severity='error')`
    - Dangling `todo` ref (`zzzzzz`): exactly one finding:
      `Drift(location='.../spec.spec.md', rule='check.gate-ref-dangling', detail="Gate-Ref 'zzzzzz' does not resolve to any in-tree path or artifact id6", severity='error')`

    No-double-report boundaries:
    - Non-live carrier (open backlog item): `check_gate_ref_dangling(root)` yields `[]` (Case 15).
    - Unknown verdict (foreign TODO `T-12` or empty index): yields `[]` (Case 12).
    - Malformed ref (spaces/invalid characters): yields `[]` (Case 6).
    - Decision ref (`D999`): yields `[]` (Case 7, ownership retained by `check.decision-ref-dangling`).
    - Absent ref (`None` or empty): yields `[]`.

    Live-corpus result:
    `len(check_engine.check_gate_ref_dangling(repo_root))` = 0.
    Zero is the EXPECTED outcome on the live corpus because all three live gates (`adgtqb` -> `yvvf98`, spec -> `ju93oc`, spec -> `m15n3k`) resolve to real in-tree artifacts (F-02).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `RULE_REGISTRY` entry showing `warning` and `I-07`, and state the severity argument in writing: that a discharged gate needs a human disposition rather than being malformed, that `warning` still drives a nonzero exit because `artifact_core.drift_exit_code` exempts only `info`, and that `error` was rejected because it would turn the sweep red on three records this plan deliberately does not edit. THEN PASTE THE LIVE RESULT, which is this item's whole point: `aw check all` reports one `check.gate-ref-discharged` finding for EVERY live gate whose resolved target classifies `done` or `parked`, and for no other record, each naming the resolved target and the class. RE-DERIVE that set at execution with an independent driven census (the same `parse_item`/`_read_gate` + index + `class_of` walk F-02 used) and paste both, so the bar is set equality between the census and the findings, not a count (PR-005); the authoring census was three (`adgtqb`, and the two `deferred` specs), and if it differs at execution, report what changed rather than adjusting either side. Paste the four false-positive guards, each driven: a gate pointing at a LIVE target (a `pending` plan or an `open` item) yields none; a path-route target yields none because a path has no status; a target whose `(record_type, status)` pair `class_of` RAISES yields none (re-measure the unmappable population; authoring measured 81 of 2331 inventoried records raising, including 24 `('plans', None)` and one `('plans','EXECUTED')`); and a ref the helper reports `unknown` (empty index) yields none. State in writing that liveness is read from `class_of` and that no second status list was introduced anywhere in the diff.
  - Observed evidence:
    `RULE_REGISTRY` entry as committed:
    ```python
    # gateresolve jdaozp E-03: a Gate-Ref whose target resolves in the artifact inventory but whose
    # attention_contract.class_of is `done` or `parked`. Registered `warning` with invariant I-07.
    # Severity rationale: a discharged gate indicates a record needing human disposition (unblock, repoint,
    # or close) rather than a malformed record; warning still drives a nonzero check exit because
    # artifact_core.drift_exit_code exempts only info; error was rejected because it would turn the sweep
    # red on three records this plan deliberately does not edit, converting a detector into a forced edit
    # of a release-gated item. Deterministic: attention_contract.class_of mapping over inventoried status.
    "check.gate-ref-discharged": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    ```
    Severity argument:
    A discharged gate indicates a carrier whose blocker finished or was shelved, requiring a human disposition (unblock, close, or repoint) rather than indicating syntax corruption. `warning` still drives a nonzero exit in `aw check` because `artifact_core.drift_exit_code` exempts only `info`. `error` was rejected because it would turn the sweep red on three records this plan deliberately does not edit, inappropriately forcing an edit of a release-gated item.

    Live result in `aw check all`:
    ```
    Issue: check.gate-ref-discharged
    - .aw/records/backlog/blocked
      1. 20260908-idxuntrack-01-adgtqb-finalize-leaves-tracked-index-dirty.backlog.md
      Fix: unblock carrier or repoint Gate-Ref 'yvvf98' to an active blocker; target is currently executed (done)

    Issue: check.gate-ref-discharged
    - .aw/records/specs/deferred
      1. 20260725-0957-01-external-delivery-and-skills.spec.md
      Fix: unblock carrier or repoint Gate-Ref 'ju93oc' to an active blocker; target is currently parked (parked)

    Issue: check.gate-ref-discharged
    - .aw/records/specs/deferred
      1. 20260726-1239-01-clean-delta-and-tracking-modes.spec.md
      Fix: unblock carrier or repoint Gate-Ref 'm15n3k' to an active blocker; target is currently parked (parked)
    ```

    Independent execution-time census vs findings (set equality):
    Census count: 3
      Census: .../.aw/records/backlog/blocked/20260908-idxuntrack-01-adgtqb-finalize-leaves-tracked-index-dirty.backlog.md ref: yvvf98 target: plans executed (done)
      Census: .../.aw/records/specs/deferred/20260725-0957-01-external-delivery-and-skills.spec.md ref: ju93oc target: backlog parked (parked)
      Census: .../.aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md ref: m15n3k target: backlog parked (parked)
    Findings count: 3
      Finding: .../.aw/records/backlog/blocked/20260908-idxuntrack-01-adgtqb-finalize-leaves-tracked-index-dirty.backlog.md check.gate-ref-discharged Gate-Ref 'yvvf98' resolves to plans target with status 'executed' (class 'done')
      Finding: .../.aw/records/specs/deferred/20260725-0957-01-external-delivery-and-skills.spec.md check.gate-ref-discharged Gate-Ref 'ju93oc' resolves to backlog target with status 'parked' (class 'parked')
      Finding: .../.aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md check.gate-ref-discharged Gate-Ref 'm15n3k' resolves to backlog target with status 'parked' (class 'parked')
    Set equality between census and findings: CONFIRMED.

    Four false-positive guards:
    1. Gate pointing at live target (`open` backlog item): 0 findings (Case 5).
    2. Path-route target (`NOTES.md`): 0 findings (Case 11).
    3. Target whose `(record_type, status)` raises in `class_of`: 0 findings (Case 10). Re-measured unmappable population across 2471 inventoried artifacts at HEAD: 65 records raise (`('plans', 'EXECUTED')`: 1, `('plans', 'None')`: 24, `('prompts', 'None')`: 4, `('research', 'None')`: 9, `('roadmaps', 'None')`: 1, `('roadmaps', 'archive')`: 1, `('roadmaps', 'reference')`: 1, `('walkthroughs', 'None')`: 24).
    4. Ref reporting `unknown` (empty index / foreign namespace): 0 findings (Case 12).

    Liveness authority:
    Liveness is derived exclusively from `attention_contract.class_of(record_type, status)`. No second status list was introduced anywhere in the diff.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the wiring as committed, showing both sweeps in the `types == ["all"]` branch, each in its own `try`/`except`, beside `check_decision_ref_dangling`, and sharing ONE dependency index. Demonstrate fail isolation: make one of the two predicates raise (temporarily, in a driven probe, not in the committed code) and paste evidence that the other rule's findings still appear and `aw check` does not crash. Paste a per-type run (`aw check backlog`) showing neither new rule fires, matching the documented behavior of that seam's neighbours. Paste `RELEASE_GATE_RULES` as committed proving it is UNCHANGED, name the parity test that pins it, and paste that test passing.
  - Observed evidence:
    Wiring in `check_types` as committed:
    ```python
        try:
            drift.extend(check_decision_ref_dangling(repo_root))
        except Exception:
            pass
        # gateresolve jdaozp E-04: resolve typed artifact and todo gate refs. Both sweeps ride
        # the full sweep seam, sharing one dependency index to avoid per-sweep inventory rebuilding.
        gate_dep_index: Optional[_DepIndex] = None
        try:
            gate_dep_index = build_dependency_index(repo_root)
        except Exception:
            pass
        try:
            drift.extend(check_gate_ref_dangling(repo_root, index=gate_dep_index))
        except Exception:
            pass
        try:
            drift.extend(check_gate_ref_discharged(repo_root, index=gate_dep_index))
        except Exception:
            pass
    ```

    Fail isolation probe:
    ```python
    # 1. When check_gate_ref_dangling raises:
    with patch('agent_workflows.check_engine.check_gate_ref_dangling', side_effect=RuntimeError('boom dangling')):
        drift = check_engine.check_types(repo_root, ['all'])
        # check.gate-ref-discharged count = 3, sweep completed without crash.
    # 2. When check_gate_ref_discharged raises:
    with patch('agent_workflows.check_engine.check_gate_ref_discharged', side_effect=RuntimeError('boom discharged')):
        drift = check_engine.check_types(repo_root, ['all'])
        # check_types completed without crash, discharged count = 0.
    ```

    Per-type run (`aw check backlog`):
    ```python
    >>> drift = check_engine.check_types(repo_root, ['backlog'])
    >>> [d for d in drift if d.rule in ('check.gate-ref-dangling', 'check.gate-ref-discharged')]
    []
    ```
    Neither new rule fires on a per-type check, matching neighbouring full-sweep rules.

    `RELEASE_GATE_RULES` unchanged and parity test:
    ```python
    RELEASE_GATE_RULES = (
        "check.live-bug-ungated",
        "check.blocking-item-closed-without-gate",
        "check.from-backlog-gate-mismatch",
        "check.blocks-release-dangling",
        "check.release-sentinel-absent",
        "check.release-sentinel-ambiguous",
        "check.from-backlog-dangling",
        "check.from-backlog-malformed",
    )
    ```
    Neither `check.gate-ref-dangling` nor `check.gate-ref-discharged` was added to `RELEASE_GATE_RULES`.
    Parity test `tests/test_check_engine_release_gate.py` passed:
    `40 passed in 6.75s`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_gate_ref_resolution.py` in full, then the BARE `python3 -m pytest` summary line with its HEAD. Enumerate the fifteen required cases and name the test function covering each, so a reader can see none was dropped. Confirm in writing that no test reads production source via `inspect`, `ast`, regex or substring search, asserts a caller count or symbol census, or pins a docstring or comment banner, and that every assertion is on a returned value, an exit code or an emitted finding. Confirm every sweep case builds a throwaway tree and none reads the live `.aw/records/`. Name case (12), the cannot-judge case (foreign TODO-id namespace and empty index), and paste its assertions, since it is the portability guarantee for every repo this code ships into; likewise name and paste case (14), the path-containment case. Paste BOTH falsifiable negatives failing when inverted, with the actual assertion-error text for each.
  - Observed evidence:
    `python3 -m pytest tests/test_gate_ref_resolution.py` full output:
    ```
    ============================== 15 passed in 2.70s ==============================
    ```
    Per-test visibility (`python3 -m pytest tests/test_gate_ref_resolution.py -o addopts="" -v`):
    ```
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_13_falsifiable_negative_rule_and_severity PASSED [  6%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_12_managed_target_repo_cannot_judge PASSED [ 13%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_01_helper_resolution_routes PASSED [ 20%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_04_dangling_todo_ref_reports_error PASSED [ 26%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_06_malformed_ref_skipped PASSED [ 33%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_15_non_live_carrier_yields_nothing PASSED [ 40%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_11_path_route_target_yields_no_discharged PASSED [ 46%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_02_path_route_anchor_suffix PASSED [ 53%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_03_dangling_artifact_ref_reports_error PASSED [ 60%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_10_unmappable_target_status_yields_no_discharged PASSED [ 66%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_08_executed_target_reports_discharged PASSED [ 73%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_14_path_containment_escaping_ref PASSED [ 80%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_07_decision_ref_skipped_by_new_rules PASSED [ 86%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_09_parked_target_reports_discharged PASSED [ 93%]
    tests/test_gate_ref_resolution.py::GateRefResolutionTests::test_05_resolvable_and_live_ref_yields_no_finding PASSED [100%]
    ```

    Bare `python3 -m pytest` summary line at HEAD 388cb8238def97ea1e02780b8c9977a0451d2f2d:
    `6333 passed, 2 skipped, 3 warnings in 363.93s (0:06:03)`

    Fifteen required cases and test functions:
    Case 1: test_01_helper_resolution_routes
    Case 2: test_02_path_route_anchor_suffix
    Case 3: test_03_dangling_artifact_ref_reports_error
    Case 4: test_04_dangling_todo_ref_reports_error
    Case 5: test_05_resolvable_and_live_ref_yields_no_finding
    Case 6: test_06_malformed_ref_skipped
    Case 7: test_07_decision_ref_skipped_by_new_rules
    Case 8: test_08_executed_target_reports_discharged
    Case 9: test_09_parked_target_reports_discharged
    Case 10: test_10_unmappable_target_status_yields_no_discharged
    Case 11: test_11_path_route_target_yields_no_discharged
    Case 12: test_12_managed_target_repo_cannot_judge
    Case 13: test_13_falsifiable_negative_rule_and_severity
    Case 14: test_14_path_containment_escaping_ref
    Case 15: test_15_non_live_carrier_yields_nothing

    Behavior-only test confirmation:
    No test reads production source via `inspect`, `ast`, regex, or line counting. Every test asserts on observable behaviors: returned resolution values, exit codes, or emitted Drift findings. Every sweep test builds its own throwaway tree in `tempfile.TemporaryDirectory` and none reads live `.aw/records/`.

    Case 12 assertions (managed target repo portability):
    ```python
    # Part 1: Foreign TODO namespace (T-12)
    _create_backlog_item(root, "blocked", "aaaaaa", gate_kind="todo", gate_ref="T-12")
    res_t12 = check_engine.resolve_gate_ref(root, "todo", "T-12")
    self.assertEqual(res_t12.verdict, "unknown")
    self.assertEqual(check_engine.check_gate_ref_dangling(root), [])
    self.assertEqual(check_engine.check_gate_ref_discharged(root), [])

    # Part 2: Empty index simulating inventory failure in build_dependency_index
    empty_idx = check_engine._DepIndex(owners={})
    res_empty = check_engine.resolve_gate_ref(root, "todo", "bbbbbb", index=empty_idx)
    self.assertEqual(res_empty.verdict, "unknown")
    self.assertEqual(check_engine.check_gate_ref_dangling(root, index=empty_idx), [])
    self.assertEqual(check_engine.check_gate_ref_discharged(root, index=empty_idx), [])
    ```

    Case 14 assertions (path containment):
    ```python
    outside_file = root.parent / "outside_marker.txt"
    outside_file.write_text("outside", encoding="utf-8")
    try:
        esc_ref = f"../{outside_file.name}"
        res = check_engine.resolve_gate_ref(root, "todo", esc_ref)
        self.assertNotEqual(res.route, "path")
        self.assertEqual(res.verdict, "unknown")
    finally:
        if outside_file.exists():
            outside_file.unlink()
    ```

    Both falsifiable negatives failing when inverted:
    - Dangling rule inverted: `AssertionError: Expected rule mismatch: check.gate-ref-dangling`
    - Dangling severity inverted: `AssertionError: Expected severity mismatch: error != warning`
    - Discharged rule inverted: `AssertionError: Expected rule mismatch: check.gate-ref-discharged`
    - Discharged severity inverted: `AssertionError: Expected severity mismatch: warning != error`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the amended Section 8.4 verbatim and paste `git diff` for the spec file proving NO OTHER SECTION changed and that `- Status:` is untouched. Confirm the amendment states all five required things: that an in-tree kind is resolved; that `issue`/`external`/`date` are shape-only WITH the reason (no in-tree referent; no network IO in a deterministic rule; a date's shape is its semantics); that a discharged gate is reported, naming the rule; the portability limit; and OQ6's disposition. Quote the Section 8.8 `issue`-URL restriction from the committed file proving it is preserved verbatim. State in writing that the spec file is declared in `- Scope-Paths:` and therefore announced by the runner's spec-edit announcement, and that the amendment is the same-change obligation `AGENTS.md` imposes rather than an incidental edit.
  - Observed evidence:
    Amended Section 8.4 verbatim:
    ~~~markdown
    ### 8.4 Structured gates

    A `deferred` artifact MUST identify the blocking condition with discrete front-matter bullets (the Section 7 grammar; free text alone is insufficient for validation):

    ```
    - Status: deferred
    - Gate-Kind: issue
    - Gate-Ref: <kind-validated reference>
    - Gate-Summary: <optional human context; never machine state>
    ```

    - `Gate-Kind` (required for `deferred`) is a closed enum: `artifact`, `decision`, `todo`, `issue`, `date`, `external`.
    - `Gate-Ref` (required) is validated per kind and resolved where applicable:
      - `date` = `YYYY-MM-DD`. Shape-only: its shape is its semantics; no referent exists to resolve.
      - `artifact` = repo-relative POSIX path (optional Markdown anchor) or an artifact id6. An in-tree reference is resolved: first as a repo-relative path (with any `#anchor` stripped before probing) contained strictly within the repository root (escaping paths with `..` are rejected), and second against the artifact inventory id6 index. An unresolvable reference is reported as dangling (`check.gate-ref-dangling`).
      - `todo` = stable repo identifiers (a TODO id / id6). Resolved against repo-relative paths (contained within repo root) and against the artifact inventory. An id6-shaped ref absent from the inventory is reported as dangling (`check.gate-ref-dangling`).
      - `decision` = `Dnn[suffix]` heading reference in `DECISIONS.md`. Resolved against headings in `DECISIONS.md`; an unresolvable reference is reported as dangling (`check.decision-ref-dangling`).
      - `issue` = absolute issue URL (`http`/`https` only; Section 8.8). Shape-only: external URLs are not resolvable in-tree without network IO (forbidden in deterministic checks).
      - `external` = a nonempty stable repo-chosen reference. Shape-only: treated as opaque data (Section 8.8), never as an in-tree target.
    - **Gate resolution and discharged gate detection.** References of in-tree kinds (`artifact`, `todo`, `decision`) are resolved against the repository in addition to being shape-validated. When an in-tree target resolves to an artifact whose attention class (`attention_contract.class_of`) has reached `done` or `parked`, the gate has outlived its blocker and is reported as discharged (`check.gate-ref-discharged` at warning) to prompt human disposition.
    - **Portability limit.** Resolution is only as complete as the repository's own records. In a managed target repo or environment where the artifact inventory cannot be built (an empty inventory index), an id6 ref is treated as unknown rather than dangling. Similarly, a `todo` ref outside the repository's 6-character id6 namespace (such as foreign TODO identifiers like `T-12`) cannot be judged and is reported by neither rule. An `artifact` ref, which is declared as a repository path, that names neither an in-repo path nor a resolving id6 is reported as dangling.
    - `Gate-Summary` is optional and MUST NOT determine machine behavior.
    - Gate fields are FORBIDDEN for non-`deferred` statuses; the owner verb removes them on exit and preserves the resolution in history. When the gate clears, the artifact transitions to `ready`/`active`/`done`/`parked` via its native status; there is no separate mutable gate-state field.
    ~~~

    `git diff` of spec file showing only Section 8.4 and OQ6 modified, and `- Status:` untouched:
    ~~~diff
    diff --git a/.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md b/.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
    index 5bbfdcc0d..8496a83df 100644
    --- a/.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
    +++ b/.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
    @@ -188,7 +188,15 @@ A `deferred` artifact MUST identify the blocking condition with discrete front-m
     ```

     - `Gate-Kind` (required for `deferred`) is a closed enum: `artifact`, `decision`, `todo`, `issue`, `date`, `external`.
    -- `Gate-Ref` (required) is validated per kind: `date` = `YYYY-MM-DD`; `artifact` = repo-relative POSIX path (optional Markdown anchor); `todo`/`decision` = stable repo identifiers (a TODO id / `Dnn`); `issue` = absolute issue URL; `external` = a nonempty stable repo-chosen reference.
    +- `Gate-Ref` (required) is validated per kind and resolved where applicable:
    +  - `date` = `YYYY-MM-DD`. Shape-only: its shape is its semantics; no referent exists to resolve.
    +  - `artifact` = repo-relative POSIX path (optional Markdown anchor) or an artifact id6. An in-tree reference is resolved: first as a repo-relative path (with any `#anchor` stripped before probing) contained strictly within the repository root (escaping paths with `..` are rejected), and second against the artifact inventory id6 index. An unresolvable reference is reported as dangling (`check.gate-ref-dangling`).
    +  - `todo` = stable repo identifiers (a TODO id / id6). Resolved against repo-relative paths (contained within repo root) and against the artifact inventory. An id6-shaped ref absent from the inventory is reported as dangling (`check.gate-ref-dangling`).
    +  - `decision` = `Dnn[suffix]` heading reference in `DECISIONS.md`. Resolved against headings in `DECISIONS.md`; an unresolvable reference is reported as dangling (`check.decision-ref-dangling`).
    +  - `issue` = absolute issue URL (`http`/`https` only; Section 8.8). Shape-only: external URLs are not resolvable in-tree without network IO (forbidden in deterministic checks).
    +  - `external` = a nonempty stable repo-chosen reference. Shape-only: treated as opaque data (Section 8.8), never as an in-tree target.
    +- **Gate resolution and discharged gate detection.** References of in-tree kinds (`artifact`, `todo`, `decision`) are resolved against the repository in addition to being shape-validated. When an in-tree target resolves to an artifact whose attention class (`attention_contract.class_of`) has reached `done` or `parked`, the gate has outlived its blocker and is reported as discharged (`check.gate-ref-discharged` at warning) to prompt human disposition.
    +- **Portability limit.** Resolution is only as complete as the repository's own records. In a managed target repo or environment where the artifact inventory cannot be built (an empty inventory index), an id6 ref is treated as unknown rather than dangling. Similarly, a `todo` ref outside the repository's 6-character id6 namespace (such as foreign TODO identifiers like `T-12`) cannot be judged and is reported by neither rule. An `artifact` ref, which is declared as a repository path, that names neither an in-repo path nor a resolving id6 is reported as dangling.
     - `Gate-Summary` is optional and MUST NOT determine machine behavior.
     - Gate fields are FORBIDDEN for non-`deferred` statuses; the owner verb removes them on exit and preserves the resolution in history. When the gate clears, the artifact transitions to `ready`/`active`/`done`/`parked` via its native status; there is no separate mutable gate-state field.

    @@ -289,7 +297,7 @@ This spec fixes WHAT and WHY (observable behavior, contracts, compatibility, req
     - OQ3 RESOLVED (2026-08-08, human, via /plan-review): v1 tree scope = specs + plans + research IN; prompts + comms IN only if their full contracts + mappings are finalized in Phase 0, else deferred to Phase 3. AMENDED (2026-09-25, plan dx0u4s): prompts is now a tracked tree with the disposition mapping {pending: ready, executed: done, superseded: parked, not-executed: parked, reusable: parked}; comms remains deferred to Phase 3.
     - OQ4 The precise JSON schema (id scheme + uniqueness, path normalization, ordering, null behavior, error object) and the canonical serialization profile (Section 8.5) - Phase 0 deliverable.
     - OQ5 Whether plans should gain a native `executing` state (enabling `active` for in-execution plans) in v1 or later. If later, plans have no `active` items in the view initially. (Owner decision; see Section 11 dependency.)
    -- OQ6 The `Gate-Ref` validators per kind (esp. `todo`/`decision` stable-id formats and `external` acceptance rule).
    +- OQ6 RESOLVED (2026-10-02, plan jdaozp): `decision` shape settled by plan `jge900` (`Dnn` with optional lowercase suffix matching `DECISIONS.md` headings); in-tree resolution for `artifact`, `todo`, and `decision` refs settled by plan `jdaozp` with `check.gate-ref-dangling` and `check.gate-ref-discharged`; `issue`, `external`, and `date` confirmed shape-only with rationale in Section 8.4; `external` acceptance rule remains non-empty safe single-line string treated as opaque data.
     - OQ7 RESOLVED (2026-08-08, human, via /plan-review): the write boundary is `aw attention` read-only + `aw specs` owns spec writes + plans/research owned by their existing verbs; NO generic write router in v1.
     - OQ8 RESOLVED (2026-08-08, human, via /plan-review): walkthroughs and roadmaps are `excluded` in the tree policy inventory for v1 (no real lifecycle semantics yet), revisited in Phase 3.
     - OQ9 RESOLVED (2026-08-08, human, via /plan-review): an optional `aw attention snapshot` persisted file stays OUT of v1, deferred until a demonstrated non-executable consumer needs it.
    ~~~

    Preserved Section 8.8 URL restriction quoted from committed file:
    `- **URL restriction.** Gate-Kind: issue Gate-Ref MUST be an absolute http/https URL; other schemes (javascript:, file:, data:, etc.) are a violation. external refs are treated as opaque data, never as a fetchable/executable target.`

    Same-change obligation:
    The spec file `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` is declared in `- Scope-Paths:`, was announced by the runner's spec-edit announcement, and represents the same-change obligation imposed by `AGENTS.md` rather than an incidental edit.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the report for every live stale gate the V-03 census identifies (three at authoring). For each: the carrier path and its status, the gate kind and ref, the resolved target with its record type and status, the class `class_of` returns, and the options available. For `adgtqb` additionally paste its `- Blocks-Release:` and `- Work-Kind:` values, the commit and date `yvvf98` reached `executed`, and the driven current state of the two premises its body asserts (`git ls-files --error-unmatch` and `git check-ignore -v` for `.aw/records/plans/INDEX.json`), and state explicitly that you are NOT asserting the bug is fixed, because that is OQ-01's maintainer judgement. Then prove non-interference: paste `git log --oneline -1` and `git diff --stat HEAD` for each of the three record paths showing this plan modified none of them, and confirm the staged set of every commit contained only paths from `- Scope-Paths:`. Paste the CHANGELOG entry and confirm it names both rule ids and contains no em or en dash.
  - Observed evidence:
    Report for the three live stale gates identified in V-03:

    1. Carrier: `.aw/records/backlog/blocked/20260908-idxuntrack-01-adgtqb-finalize-leaves-tracked-index-dirty.backlog.md`
       - Status: `blocked`
       - Gate-Kind: `artifact`, Gate-Ref: `yvvf98`
       - Resolved Target: `plans` target `.aw/records/plans/executed/20260906-idxuntrack-02-yvvf98-untrack-the-four-generated-index-manifests-and-reconcile-sta.ipd.md`, status `executed`
       - Attention Class: `done` (from `class_of('plans', 'executed')`)
       - Additional Carrier Details:
         - `- Blocks-Release: next`
         - `- Work-Kind: bug`
         - `yvvf98` executed commit and date: `648def884` on `Wed Sep 9 21:19:44 2026 -0400` (`lifecycle(yvvf98): finalize yvvf98 -> executed`)
         - Driven current state of the two premises:
           `git ls-files --error-unmatch .aw/records/plans/INDEX.json`: exited nonzero (not tracked)
           `git check-ignore -v .aw/records/plans/INDEX.json`: `.aw/.gitignore:45:records/plans/INDEX.json .aw/records/plans/INDEX.json` (ignored)
       - Explicit statement: This plan does NOT assert the bug is fixed. Determining whether every symptom recorded in `adgtqb` is gone or whether unblocking it is warranted is a maintainer judgement under OQ-01.
       - Available Options: (a) If maintainer confirms bug is fixed, close item with cited evidence under predicate governance; (b) if work remains, repoint gate at the active blocker; or (c) unblock item to active backlog.

    2. Carrier: `.aw/records/specs/deferred/20260725-0957-01-external-delivery-and-skills.spec.md`
       - Status: `deferred`
       - Gate-Kind: `todo`, Gate-Ref: `ju93oc`
       - Resolved Target: `backlog` item `.aw/records/backlog/parked/20260815-ju93oc-01-ju93oc-reeval-delivery-model-skills.backlog.md`, status `parked`
       - Attention Class: `parked` (from `class_of('backlog', 'parked')`)
       - Available Options: (a) Unpark backlog item `ju93oc` to resume work; (b) repoint gate to another active blocker; or (c) transition spec to `parked` if work is indefinitely shelved.

    3. Carrier: `.aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md`
       - Status: `deferred`
       - Gate-Kind: `todo`, Gate-Ref: `m15n3k`
       - Resolved Target: `backlog` item `.aw/records/backlog/parked/20260918-m15n3k-01-m15n3k-clean-delta-build-phases.backlog.md`, status `parked`
       - Attention Class: `parked` (from `class_of('backlog', 'parked')`)
       - Available Options: (a) Unpark backlog item `m15n3k` to resume work; (b) repoint gate to another active blocker; or (c) transition spec to `parked` if work is indefinitely shelved.

    Non-interference proof:
    ```
    git log --oneline -1 .aw/records/backlog/blocked/20260908-idxuntrack-01-adgtqb-finalize-leaves-tracked-index-dirty.backlog.md
    151bcc86a backlog: gate the ten carrier-less bug items on the next release
    git diff --stat HEAD .aw/records/backlog/blocked/20260908-idxuntrack-01-adgtqb-finalize-leaves-tracked-index-dirty.backlog.md
    (empty)

    git log --oneline -1 .aw/records/specs/deferred/20260725-0957-01-external-delivery-and-skills.spec.md
    2fa657325 feat(specdirs): migrate specs into status subdirectories (1bdxcp)
    git diff --stat HEAD .aw/records/specs/deferred/20260725-0957-01-external-delivery-and-skills.spec.md
    (empty)

    git log --oneline -1 .aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md
    2fa657325 feat(specdirs): migrate specs into status subdirectories (1bdxcp)
    git diff --stat HEAD .aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md
    (empty)
    ```
    None of the three live records was modified. The staged set of every commit contains only paths from `- Scope-Paths:`.

    CHANGELOG entry:
    ```markdown
    - Added: `check.gate-ref-dangling` (error severity) to report well-formed artifact or todo gate references that resolve to neither an in-repo path nor an inventoried artifact id6, and `check.gate-ref-discharged` (warning severity) to detect gates whose targets have completed or parked, preventing gates from silently outliving their blockers.
    ```
    Names both rule ids (`check.gate-ref-dangling` and `check.gate-ref-discharged`), written in existing user-facing prose style, containing NO em or en dashes.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, because readiness is an output of `/plan-review` and writing one at authoring time would forge a review that has not happened. It requires explicit human approval before execution.

Executing agent: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change, since other agents may be working in this checkout. Run the suite BARE and paste the actual output; do not claim a pass you did not run. DO NOT EDIT THE LIVE GATE-CARRYING RECORDS to make the sweep quiet: `check.gate-ref-discharged` findings on them (three at authoring) are the EXPECTED result of this plan succeeding (F-02, F-12), and one of those carriers is a release-blocking item whose close is predicate-governed. If a step appears to require editing them, that is OQ-01; report it in the V-07 evidence and continue with every other item rather than editing them. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION so finalize can reconcile what was edited against what was declared, not a stop condition; if the work genuinely requires a path outside it, make the edit and justify it at finalize with `--scope-reason`, and acknowledge any declared-but-unmodified path with `--scope-ack`. STOP and report only for a genuinely unsafe condition: an unresolvable concurrent edit to a declared path, or a prerequisite symbol (`build_dependency_index`, `check_decision_ref_dangling`, `class_of`, `validate_gate_ref`) that is absent. LIFECYCLE: the plan does not reach `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries real pasted evidence with a non-pending `Result`. When executed under `aw oc run` or `aw agy run`, the RUNNER performs the finalize and the lifecycle move, so do not invoke it yourself; when executed by hand, the executor performs it via `aw ipd finalize`. Never hand-edit the status line and never hand-move the file. Never create a tag or release.
