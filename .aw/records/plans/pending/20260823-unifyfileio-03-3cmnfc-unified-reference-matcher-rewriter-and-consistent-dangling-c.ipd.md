# IPD: Unified reference matcher/rewriter and consistent dangling-citation check

- Date: 2026-08-23
- Kind: child
- Concern: Reference matching (finding citations to a file so a rename/regroup can rewrite them) is implemented three independent times with DIFFERENT coverage, and the dangling-citation checker understands different citation forms per type. `plans_refs.plan_reference_rewrites` rewrites full-name + bare-stem (+ range as a special case of bare-stem); `artifact_rename.plan_reference_rewrites` rewrites full-name + a DIFFERENT "whole-name-minus-.md" stem; `research_refs.plan_reference_rewrites` rewrites the full old filename ONLY - so a research rename ORPHANS any bare-stem citation that a plans rename would have fixed. The dangling checkers diverge too: plans recognize only the `PLAN-<id6>` handle; research recognizes `RSCH-<id6>` + a full parseable filename; NEITHER recognizes a setid citation, and plans do not flag a bare-filename citation as dangling. This is the "one unified way to IDENTIFY references to files" gap.
- Scope: Create ONE reference matcher/rewriter library and ONE dangling-citation matcher policy, and route the plans, research, and generic rename/group paths plus the check engine through them. Touch: agent_workflows/artifact_core.py (the shared dangling ENGINE `find_dangling_citations` already lives here; the new reference MATCHER must live in its OWN module - NOT in artifact_core - because it imports the Order 01 naming authority and the orchestrator's module-placement principle forbids a core->naming import; see E-02), agent_workflows/plans_refs.py (`plan_reference_rewrites`/`apply_reference_rewrites`), agent_workflows/research_refs.py (`plan_reference_rewrites`/`apply_reference_rewrites`/`find_dangling_citations`), agent_workflows/artifact_rename.py (`plan_reference_rewrites`/`apply_reference_rewrites`), agent_workflows/research_contract.py (`iter_id6_citations`), agent_workflows/plans_index.py (`_plan_cite_matcher`/`check_drift` class d), agent_workflows/research_index.py (`check_drift`), agent_workflows/check_engine.py (`check_refs` stub). Depends on Order 01 (grammar authority, to know what a stem/name IS) and Order 02 (resolver, to answer "does this cited name currently exist?"). Note: id6/setid citations are NOT rewritten and MUST remain so - they are stable across renames by design; this child only unifies the FILENAME-derived forms and makes the dangling check consistent.
- Status: approved
- Set: unifyfileio
- Order: 3
- Highest E allocated: 05
- Author: Gabriele Fariello

- Id: 3cmnfc

## Workflow history
- 2026-08-24 approved (aw set, --by-human): status set to approved

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (module-placement: matcher must NOT live in artifact_core since it imports the Order 01 authority - per orchestrator binding principle), PR-002/PR-003 (corrected apply_ ordering + id6 docstring citation overstatements), PR-004 (Order 02 dependency), OQ-01 human-resolved = option B (dead bare-filename citations flagged via Order 02 resolver; setid-dangling deferred), which makes Order 02 an unconditional hard prerequisite. Core path:line claims verified TRUE.

## Goal

Provide a single reference-matching library that, given an old->new filename map, finds and rewrites every FILENAME-derived citation form - full filename, bare stem, and range shorthand - identically for every artifact type, and a single dangling-citation matcher that recognizes the same citation-form set for every type. Route the plans, research, and generic rename/group paths through the one rewriter (fixing research's full-name-only weakness so a research rename no longer orphans stem citations), and route the check engine's per-type dangling detection through the one matcher policy. Preserve the deliberate, correct design that id6 and setid citations are NEVER rewritten (they are stable across rename/regroup because the id6 is carried into the new filename - `artifact_rename.py:111` - and the `- Id:`/`- Set:` frontmatter is preserved); this child does not touch that stability guarantee, it only unifies the filename-derived rewrites and the dangling policy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Characterize current reference behavior (safety net)

- [ ] E-01 Author `tests/test_reference_matcher_golden.py` pinning CURRENT rewrite behavior for each engine before unification: for plans, research, and a generic type, build a fixture repo where a target file is cited by full-name, bare-stem, and range shorthand in other files, run each engine's rewriter, and assert exactly which citation forms it rewrites today - explicitly capturing that research rewrites full-name ONLY (the gap) and that plans rewrite all three. Also pin the current dangling-checker recognition per type (plans: `PLAN-<id6>` only; research: `RSCH-<id6>` + full filename).
  - Depends on: none
  - Expected outcome: a green baseline that documents the divergence the unification will remove. (Set-level: this whole IPD executes only after Orders 01 and 02 are executed.)
  - Execution state: pending

### Task group 2: Build the one reference library

- [ ] E-02 Implement one reference matcher/rewriter: given a `name_map` (old->new) and, via the Order 01 authority, the stem for each name, produce the set of `RefEdit`s covering full-name, bare-stem (word-boundaried, driven ONLY by the map so unrelated same-grammar stems are never touched - preserving the plans safety property at `plans_refs.py:245`), and range shorthand (the stem-inside-`..NN` case). Provide one `apply_reference_rewrites` that applies full-name before bare-stem deterministically. Do NOT match or rewrite bare id6 or setid tokens (stable by design).
  - Depends on: E-01
  - Note (verified - MODULE PLACEMENT, resolving the orchestrator's binding principle): because this matcher imports the Order 01 naming authority to compute a stem, it MUST NOT live in `artifact_core.py` (the orchestrator `g6mbht` "Module-placement principle" forbids a `artifact_core -> artifact_naming` import; `artifact_core` may be imported BY others but must import none of them). Place the matcher in its OWN module (or in `artifact_naming.py`/`selectors.py`) so the dependency flows toward core, and record that placement as the resolution. (This corrects the Scope line's "host the shared matcher... in artifact_core.py", which held only if the matcher needed no naming import.)
  - Note (verified - reproduce the exact safety regex): the plans safety property is NOT a plain `\b` word boundary - it is a hyphen-aware negative lookaround `(?<![0-9A-Za-z-])<escaped-stem>(?![0-9A-Za-z-])` applied per map entry with `re.escape` on the literal old stem (`plans_refs.py:275-277`, reused at `:295-297`). The unified library MUST copy this exact lookaround (not `\b`) to keep byte-for-byte parity and preserve the "embedded stem in a longer hyphenated token is not matched" property.
  - Expected outcome: one library reproduces the strongest current behavior (plans' three-form rewrite) for any type, exercised directly.
  - Execution state: pending

- [ ] E-03 Implement one dangling-citation matcher policy consumed by the shared `find_dangling_citations` engine (OQ-01 resolved = option B): recognize the explicit id6 handles (`PLAN-<id6>`, `RSCH-<id6>`) uniformly, AND flag a bare-filename/bare-stem citation whose target file no longer exists, using the Order 02 resolver to confirm non-existence. Keep the "known example ids excluded" and "spec-only stems never treated as plan citations" safeguards. Do NOT add a setid dangling concept (option C explicitly deferred per OQ-01).
  - Depends on: E-01
  - Note (OQ-01 resolved -> Order 02 is a HARD prerequisite): option B checks bare-filename EXISTENCE, so E-03 requires the Order 02 resolver to answer "does this cited name still exist?". The bare-filename dangling flag MUST fire only when the resolver confirms the target does not resolve (avoid flagging prose that merely matches the grammar). Setid citations are NOT checked (deferred).
  - Expected outcome: one dangling-matcher policy shared by the plans and research drift checks, flagging dead id6 handles AND dead bare-filename citations.
  - Execution state: pending

### Task group 3: Route the engines and the checker through the library

- [ ] E-04 Re-route the rewriters: `plans_refs`, `research_refs`, and `artifact_rename` all call the E-02 library instead of their own `plan_reference_rewrites`/`apply_reference_rewrites`; delete the three local copies. This makes a `research` rename rewrite bare-stem citations (closing the orphan gap) and unifies the generic engine's stem notion with the plans one. Re-route the dangling checks: `plans_index.check_drift` class (d) and `research_index.check_drift` consume the E-03 matcher via the shared engine; `check_engine.check_refs` (currently a no-op stub) is either wired to the shared dangling check for all types or explicitly documented as delegating to per-type `check_drift`.
  - Depends on: E-02, E-03
  - Expected outcome: one rewriter and one dangling policy back every path; the three local rewriters are gone.
  - Execution state: pending

### Task group 4: Prove parity, the research fix, and id6 stability

- [ ] E-05 Add `tests/test_reference_matcher_parity.py` asserting: (a) a research rename now rewrites full-name AND bare-stem citations (the fixed gap), while plans/backlog behavior is byte-for-byte unchanged vs the E-01 golden; (b) an id6 citation (`PLAN-<id6>`/`RSCH-<id6>`) and a setid citation are NOT rewritten by any rename (stability preserved); (c) the dangling checker recognizes the same citation forms for plans and research; and confirm `pytest -n auto` is green.
  - Depends on: E-04
  - Expected outcome: reference parity, the research fix, and id6/setid stability are all proven and regression-guarded.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Three independent rewriters over one shared scan/IO base (`artifact_core.iter_scan_files`/`atomic_write`/`git_mv`): `plans_refs.plan_reference_rewrites` (full-name + bare-stem + range-as-special-case, map-driven, `plans_refs.py:239-281`); `research_refs.plan_reference_rewrites` (full-name ONLY, `research_refs.py:53-73`); `artifact_rename.plan_reference_rewrites` (full-name + whole-name-minus-.md stem, `artifact_rename.py:152-183`). The real divergence is in these `plan_reference_rewrites` (which FORMS each produces), not in `apply_reference_rewrites`: each has its own `apply_reference_rewrites` (`plans_refs.py:284`, `research_refs.py:76`, `artifact_rename.py:186`) but plans and artifact_rename already share IDENTICAL full-name-before-stem ordering; they differ only cosmetically (temp-file prefix, an OSError try/except).
- id6/setid are NEVER rewritten, by design and correctly: a rename carries the id6 into the new filename (`artifact_rename.py:111`) and preserves `- Id:`/`- Set:`; the crisp "id6 never rewritten" statements are `plans_refs.py:13` and `research_refs.py:8-9,56-58` (`plans_index.py:224-225` states the related matcher policy that bare stems/filenames resolve via the manifest, not by id).
- Dangling checkers: shared engine `artifact_core.find_dangling_citations` (`artifact_core.py:207`) parameterized by a per-area `cite_matcher`. Plans matcher `_plan_cite_matcher` recognizes ONLY `PLAN-<id6>` (`plans_index.py:220-227`); research matcher `research_contract.iter_id6_citations` recognizes `RSCH-<id6>` + full filename (`research_contract.py:50,67-81`). Neither recognizes setid; plans do not flag bare-filename citations.
- `check_engine.check_refs` is a no-op stub returning `[]` (`check_engine.py:191-196`); ref integrity is delivered indirectly via `check_content` -> per-type `check_drift`.

## Findings

The research full-name-only rewriter is a latent correctness bug: rename a research doc that another file cites by its bare stem and that citation silently rots (the dangling checker will not even flag it, since research only flags `RSCH-<id6>` + full-filename). Unifying on the plans-strength three-form rewriter fixes this and removes two duplicate implementations. Making the dangling matcher consistent means `aw check` recognizes the same citation forms regardless of type. The id6/setid non-rewriting is correct and must be preserved and explicitly tested so a future refactor does not "helpfully" start rewriting stable handles.

## Proposed changes (ordered, validatable)

1. Pin current per-engine rewrite + dangling behavior (E-01).
2. Build one reference matcher/rewriter (three forms, map-driven, no id6/setid) (E-02).
3. Build one dangling-citation matcher policy (E-03).
4. Re-route all rewriters and both drift checks to the shared library (E-04).
5. Prove parity, the research fix, and id6/setid stability (E-05).

## Deferred / out of scope (with reason)

- Rewriting id6/setid citations: explicitly OUT of scope and must stay so (stable by design).
- The naming authority and the resolver: prerequisite children (Orders 01, 02).
- Adding a setid-dangling check: deferred to OQ-01; only added if the human wants it.

## Scope check

- Over-scope: none. Only reference matching/rewriting and dangling detection are unified; id6/setid stability is untouched.
- Under-scope: none. All three rewriters and both dangling matchers are routed through the shared library.

## Required tests / validation

- Golden `tests/test_reference_matcher_golden.py` (E-01).
- Parity + research-fix + stability `tests/test_reference_matcher_parity.py` (E-05).
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Document the canonical citation forms and the "id6/setid are stable, never rewritten" invariant in the shared library docstring; update any citation/reference spec, else N/A with reason.

## Open questions

### OQ-01: Should a bare-filename/bare-stem citation to a now-MISSING file be flagged as dangling (and should setid citations be checked at all)?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human decision (2026-08-23, /plan-review): OPTION B. The unified dangling matcher recognizes the id6 handles (`PLAN-<id6>`/`RSCH-<id6>`) uniformly AND flags a bare-filename/bare-stem citation whose target file NO LONGER EXISTS, using the Order 02 resolver to confirm non-existence (crisp per-file yes/no, low false-positive risk). Setid-dangling (option C) is EXPLICITLY DEFERRED to a follow-up: a setid names a cohort not a single file, so "missing set" semantics are ambiguous and `- Set:` values appear in prose, giving high false-positive risk for little payoff; add it later only if real setid rot appears and a "missing set" rule is defined. This makes Order 02 (resolver) an UNCONDITIONAL hard prerequisite for E-03.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the golden test shows research rewriting full-name ONLY and plans rewriting all three forms, plus the current per-type dangling recognition, against pre-refactor code.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: a unit test drives the shared rewriter directly and reproduces the plans three-form rewrite for an arbitrary type, and asserts it emits NO edit for a bare id6 or setid token.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a unit test drives the shared dangling matcher and asserts it (a) recognizes `PLAN-<id6>`/`RSCH-<id6>` uniformly; (b) per OQ-01 option B, FLAGS a bare-filename/bare-stem citation whose target file no longer exists (resolver confirms non-existence) and does NOT flag one whose target still resolves; (c) does NOT flag setid citations (option C deferred); and (d) does not flag known example ids or spec-only stems.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: after re-routing, the three local rewriters are gone (shown by diff); a research rename rewrites bare-stem citations; plans/backlog rewrites match the E-01 golden exactly; both `check_drift` paths use the shared matcher.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `tests/test_reference_matcher_parity.py` passes (research fix + plans unchanged + id6/setid not rewritten + consistent dangling recognition) and `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - unify reference matching/rewriting and dangling detection - staged safely (golden -> build rewriter -> build dangling policy -> re-route -> prove), with id6/setid stability explicitly protected.

### Execution contract

1. Open questions RESOLVED: OQ-01 RESOLVED by human (2026-08-23) = option B (flag dead id6 handles AND dead bare-filename citations via the Order 02 resolver; setid-dangling deferred). PREREQUISITE GATE: this whole IPD executes only AFTER Orders 01 (grammar authority) and 02 (resolver) are EXECUTED - both are currently pending/unexecuted, so this plan is not runnable until they land.
2. Scope fence: unify ONLY reference matching/rewriting and dangling detection; route the listed engines/checkers through the shared library. Do NOT begin rewriting id6/setid citations, do NOT change the grammar (Order 01) or the resolver (Order 02). If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
