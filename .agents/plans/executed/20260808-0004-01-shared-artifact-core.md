# IPD: shared artifact-organization core (Set `plans-adopter`, Order 1)

- Date: 2026-08-08
- Kind: child
- Concern: extract the area-agnostic pieces of the shipped research-org machinery into ONE shared module so plans (and later prompts/comms/walkthroughs) reuse them instead of forking: the `<id6>` primitive, the weekly-shard date math, the dangling-citation detector, the tiered-manifest + `--check` drift shape, and the deterministic writing-command safety helpers.
- Scope: create `agent_workflows/artifact_core.py` and refactor `research_contract`/`research_index`/`research_refs`/`research_archive` to import from it, with NO behavior change (the research tests pass unchanged). No plans behavior yet. Requires the approved spec `.agents/docs/specs/20260808-0004-01-artifact-organization-plans-adopter.spec.md`.
- Status: executed
- Set: plans-adopter
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-08 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `plans-adopter`; the shared foundation every later child builds on. Authored from spec `20260808-0004-01` Section 4.1.
- 2026-08-08 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-006 corrected the 'welded to RESEARCH_ROOT' mis-statement (the root is already a param; the real coupling is the name-grammar/citation-matcher, which E-03 parameterizes).
- 2026-08-08 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): built `agent_workflows/artifact_core.py` (id6, kebab, shard math, atomic-write/git-mv, scan roots, area-parameterized dangling detector, Drift shape) + refactored research_contract/refs/cmd/index to import+re-export it (no behavior change) + `tests/test_artifact_core.py` (15). Product commit 30e45ba; 71 research tests pass unchanged, 15 core tests pass; full suite green apart from the known non-reproducible test_undo flake (passes standalone); leak-clean; no em/en dashes. All E-01..E-06 performed and V-01..V-06 pass.
- 2026-08-08 /plan-review (Antigravity Agent): APPROVE; (none)

## Goal

Produce `agent_workflows/artifact_core.py` as the single home for the area-agnostic primitives, and refactor the four research modules to delegate to it so the id/shard/detector/manifest logic exists ONCE. Preserve the research public API and behavior exactly (a pure refactor from research's point of view); establish the seam plans will import in Orders 02 to 07.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: extract the core

- [x] E-01 create `agent_workflows/artifact_core.py` with the `<id6>` primitives moved from `research_contract` (alphabet, length, `is_valid_id6`, the word-boundary and `RSCH-`/full-name citation matchers factored to accept a caller-supplied filename-parse predicate), pure and stdlib-only.
  - Depends on: none
  - Expected outcome: id6 validate/generate/scan helpers live in the core; identical results to today.
  - Execution state: performed
- [x] E-02 move the weekly-shard date math (`shard_dirname`, `is_valid_shard_dirname`, `shard_for_date`, `SHARD_DIR_RE`) into the core.
  - Depends on: E-01
  - Expected outcome: shard helpers live in the core; `202607-W27` style output unchanged.
  - Execution state: performed
- [x] E-03 move the dangling-citation detector primitive and the tracked-text scan-root iteration into the core as an area-parameterized function. NOTE the real coupling: `research_refs.find_dangling_citations` and `_current_id6s` ALREADY take `research_root` as a parameter (the ROOT is not welded), and `SCAN_ROOTS`/`iter_scan_files` are already generic; the research-SPECIFIC parts to parameterize out are the name-grammar/current-id resolver (`parse_name`) and the citation matcher (`iter_id6_citations`, incl. the `RSCH-` handle). The core function takes the scan roots + a current-id resolver + a citation matcher as arguments. Keep the atomic-write + `git mv` helpers in the core.
  - Depends on: E-01
  - Expected outcome: a single `find_dangling_citations`-style core function both research and plans can call with their own name-grammar/citation-matcher.
  - Execution state: performed
- [x] E-04 move the tiered-manifest + `--check` SHAPE into the core (a generic drift-record type, the byte-compare stale-view check, the `--agent` tab-separated output + 0/1/2 exit-code convention) so both areas share the gate structure; area-specific entry/render stays in each area's module.
  - Depends on: E-01
  - Expected outcome: the drift/`--check` scaffolding is defined once; research's four drift classes still function.
  - Execution state: performed

### Task group 2: refactor research to import the core, and test

- [x] E-05 refactor `research_contract`/`research_index`/`research_refs`/`research_archive` to import the moved primitives from `artifact_core` (re-export where a symbol is part of the research public API) with NO behavior change.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the research modules delegate to the core; no research symbol is silently dropped.
  - Execution state: performed
- [x] E-06 add `tests/test_artifact_core.py` (id6 validate/generate/scan; shard math; the parameterized dangling detector; the drift/`--check` shape) AND confirm the EXISTING research tests pass UNCHANGED; run the file plus the full suite and paste both.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: new core tests pass; `test_research_*` pass unchanged; full suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Precedent modules: `agent_workflows/research_contract.py` (pure contract), `research_index.py`, `research_refs.py`, `research_archive.py` are the source of the primitives being lifted. `ipd_schema.py` is the style model for a pure, stdlib-only, table-driven contract module.
- Test runner: stdlib `unittest` (`python3 -m unittest discover -s tests -t .`), NOT pytest (CONTRIBUTING.md).
- No behavior change to research is the hard invariant: `test_research_contract`/`test_research_index`/`test_research_refs`/`test_research_archive` must pass without edits (edits to those test files are a red flag that behavior drifted).
- House rule: no em/en dashes in authored Markdown; external artifacts verbatim.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C1-1 | HIGH | Low | architect | consistency | Without a shared core, plans would fork id6/shard/detector/manifest logic and drift from research. | spec 3, 4.1 |
| C1-2 | MEDIUM | Medium | integrity | no-regression | The extraction must not change research behavior; unchanged research tests are the guardrail. | spec 4.1 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.1 | id6 primitives -> core (matchers parameterized by a filename-parse predicate) | `agent_workflows/artifact_core.py` (new) | Low | E-01 |
| 2 | 4.1 | shard date math -> core | `agent_workflows/artifact_core.py` | Low | E-02 |
| 3 | 4.1 | dangling detector + scan-root + atomic-write/git-mv -> core (area-parameterized) | `agent_workflows/artifact_core.py` | Medium | E-03 |
| 4 | 4.1 | manifest/`--check` shape -> core | `agent_workflows/artifact_core.py` | Medium | E-04 |
| 5 | 4.1 | research modules import the core, re-export public symbols, no behavior change | `agent_workflows/research_*.py` | Medium | E-05 |
| 6 | 4.1 | tests + unchanged-research-suite guardrail | `tests/test_artifact_core.py` | Low | E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Any plans behavior (`Id`, manifest, regroup, shards, migration) | n/a | scope | This child only extracts the shared core. | Orders 02 to 07 |
| A unified `aw <area>` verb surface | n/a | scope | Verbs stay area-native (spec 4.1). | Not planned |

## Scope check

- Over-scope: none - extract + refactor + test only. No new user-facing behavior.
- Under-scope: MUST leave research behavior identical (unchanged research tests) while exposing the core primitives for plans to import.

## Required tests / validation

New `tests/test_artifact_core.py`: id6 validate/generate/scan; shard `shard_for_date`/round-trip; the area-parameterized dangling detector; the drift/`--check` shape + `--agent` output + exit codes. Run `python3 -m unittest tests.test_artifact_core -v` then the full suite `python3 -m unittest discover -s tests -t .`; PASTE both (the `Ran N tests ... OK` summary), confirming the research tests pass unchanged. Leak-clean; no em/en dashes.

## Spec / documentation sync

No spec change (this executes spec 4.1). A short module docstring in `artifact_core.py` states it is the shared area-agnostic core and names its consumers.

## Open questions

### OQ-01: re-export vs. import-site rewrite for research public symbols

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: keep the research modules' PUBLIC symbols importable from their current locations (re-export the moved primitives) so external callers and the research tests do not break; only the DEFINITION moves to the core. This preserves the no-behavior-change invariant with the least churn.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a test showing `artifact_core` id6 validate/generate/scan match the prior `research_contract` behavior (same accept/reject cases).
  - Observed evidence: `tests/test_artifact_core.py::Id6Tests` pass: `is_valid_id6` accepts `k7m2xq`/`000000`, rejects 5/7-char and uppercase; `iter_id6_in_text("see k7m2xq here") == ["k7m2xq"]`; `generate_id6` avoids a forced collision. `research_contract` now re-exports these (`ID6_ALPHABET/ID6_LENGTH/ID6_RE/ID6_WORD_RE/is_valid_id6/iter_id6_in_text = _core.*`), and `tests.test_research_contract` passes unchanged (71 research tests OK).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste a test showing `shard_for_date` and shard-name round-trip produce the same output as before (e.g. `20260701` -> `202607-W27`).
  - Observed evidence: `ShardTests` pass: `shard_for_date("20260701") == "202607-W27"`; `shard_dirname("202607", 30) == "202607-W30"`; `is_valid_shard_dirname` accepts/rejects correctly. `research_contract` re-exports `shard_dirname`/`is_valid_shard_dirname`/`shard_for_date`/`SHARD_DIR_RE` from the core; `test_research_archive` (which relies on `shard_for_date`) passes unchanged.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste a test showing the area-parameterized dangling detector flags a stale full-name cite and does NOT flag a bare English word or a stable-id cite to a present file.
  - Observed evidence: `DanglingTests` pass: with a caller-supplied `cite_matcher`, a stale `CITE-zqzqzq` is flagged, a present `CITE-aaaaaa` is not, bare words (`design prompt naming`) are not flagged, and `exclude_root` skips the area's own tree. `research_refs.find_dangling_citations` now delegates to `_core.find_dangling_citations` with research's resolver + matcher; `test_research_refs` (stale/present/bare-word cases) passes unchanged.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste a test showing the core drift/`--check` shape (a drift record + `--agent` tab-separated line + exit 0/1/2).
  - Observed evidence: `DriftShapeTests` pass: `render_agent_drift([Drift("f.md:1","some-rule","detail")])` emits a tab-separated line; `drift_exit_code` returns 1 with drift and 0 without. `research_index.Drift` re-exports `_core.Drift`; `test_research_index` `--check` tests pass unchanged.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: confirm the research modules import the core and re-export public symbols; cite that no `test_research_*` file was edited.
  - Observed evidence: `research_contract`, `research_refs`, `research_cmd`, `research_index` each `from agent_workflows import artifact_core as _core` and re-export the moved symbols (id6/kebab/shard/SCAN_ROOTS/iter_scan_files/atomic-write/git-mv/Dangler/Drift/generate_id6). The Order-01 product commit `30e45ba` touched NO `tests/test_research_*` file (only the four research modules + the new core + the new core test); `git show 30e45ba --stat` confirms.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m unittest tests.test_artifact_core -v` + the full-suite `Ran N tests ... OK` summary; confirm `test_research_*` pass unchanged; leak-clean.
  - Observed evidence: `python3 -m unittest tests.test_artifact_core` -> `Ran 15 tests ... OK`. Research suite `tests.test_research_*` -> `Ran 71 tests ... OK` (unchanged). Full suite `python3 -m unittest discover -s tests -t .` -> `Ran 643 tests in 153.783s / FAILED (failures=1, skipped=1)` where the single failure is the KNOWN non-reproducible `test_undo_removes_prompts_scaffold` flake (confirmed: passes standalone `Ran 1 test ... OK`; unrelated to this change, which touches no prompts/undo code). `aw sanitize --agent` exit 0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires the approved spec `20260808-0004-01`. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence (including the UNCHANGED research suite); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds scope (core extraction + no-behavior-change refactor only). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
