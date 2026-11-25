# IPD: Preserve Concern and Scope bullets in fixture_codemod._plan_site

- Date: 2026-11-21
- Kind: child
- Concern: `tools/fixture_codemod.py::_plan_site` currently skips `Concern` and `Scope` bullets on Implementation Plan Document (IPD) fixtures because those two required schema fields are absent from `agent_workflows/artifact_meta.py::registry_fields("ipd")`. When a rewritten test fixture calls `tests/record_builder.py::RecordBuilder.plan`, `agent_workflows/ipd_authoring.py::build_skeleton` supplies `Concern: TODO.` and `Scope: TODO.` placeholders. Leaving those placeholders behind causes `agent_workflows/ipd_authoring.py::authoring_placeholders_resolved` to return `False`, suppresses `check.ipd-draft-ready-to-review` in `agent_workflows/ipd_lint.py` and `agent_workflows/check_engine.py`, alters `- Scope:` fallback detail extraction in attention readers, breaks `- Scope: sample.` text replacements in IPD lint tests, and triggers apply-time `not-equivalent` refusals. At the authoring commit `39400b74c`, 54 test modules carried `"- Concern: "` or `"- Scope: "` literals. Executed plan `59aiyh` has since moved most of them onto `RecordBuilder(..., raw_fields=...)` by hand, so at review HEAD only 6 modules remain, and the codemod refuses all 8 of their sites for other reasons (`legacy-format subject`, `setter-byte assertion`). The defect remains live for every future codemod run over an IPD fixture.
- Scope: IN: (1) update `tools/fixture_codemod.py::_plan_site` to preserve `Concern` and `Scope` bullets on `inferred_type == "ipd"` fixtures by emitting canonical `"Concern"` and `"Scope"` entries into `raw_fields` without setting `has_invalid_input` (keeping `rewrite_class == "standard"` when no invalid field is present); (2) add a fixture module `tests/fixtures/fixture_codemod/ipd_concern_scope.py.txt` containing static and f-string IPD `Concern` and `Scope` fixtures exercised against `authoring_placeholders_resolved`, `ipd_lint.lint_text`, and `- Scope:` text preservation; (3) add fast core-tier behavioral tests in `tests/test_fixture_codemod.py` covering `--dry-run --format json` output, rendered `RecordBuilder().plan` output, lowercase label normalization, single-variable f-string expressions, coexistence with invalid fields, and non-IPD record isolation while keeping `tests/test_fixture_codemod.py` under its 10-second serial wall-time limit; and (4) add a subprocess `--apply` equivalence and rewritten-suite pytest test in `tests/test_fixture_codemod_slow.py` with its node ID documented in `tests/slow_allowlist.txt`. OUT: changing `tests/record_builder.py::RecordBuilder.plan` or `agent_workflows/ipd_authoring.py::build_skeleton`, adding `- Concern:` or `- Scope:` to `tools/fixture_codemod.py::F01_PATTERN`, rewriting repository test modules (`59aiyh` and batch plans), or addressing sibling backlog items `e0wwtc` and `lufe6m`.
- Scope-Paths: tools/fixture_codemod.py, tests/test_fixture_codemod.py, tests/test_fixture_codemod_slow.py, tests/fixtures/fixture_codemod/ipd_concern_scope.py.txt, tests/slow_allowlist.txt
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Review-Depth: standard
- Short-Description: Preserve IPD Concern and Scope bullets via raw_fields in fixture_codemod._plan_site instead of dropping them to build_skeleton TODO placeholders.
- Work-Kind: bug
- Priority: medium
- From-Backlog: b1j6bl
- Blocks-Release: next
- Set: b1j6bl
- Order: 1
- Highest E allocated: 04
- Author: antigravity/gemini
- Id: kbh055

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-25 reviewed (uri/its_direct/pt3-claude-opus-5.5-1m-us): plan-review (standard): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed; review record .aw/records/reviews/20261121-b1j6bl-01-kbh055-preserve-concern-and-scope-bullets-in-fixture-codemod-plan-s.review.md
- 2026-11-21 to-review (aw set): Authored review-ready child plan graduated from backlog b1j6bl
- 2026-11-21 draft (antigravity/gemini): created.

## Goal

Ensure `tools/fixture_codemod.py::_plan_site` preserves `Concern` and `Scope` metadata bullets on IPD fixtures through `RecordBuilder.plan(..., raw_fields=...)` instead of dropping them, so rewritten IPD test fixtures overwrite `build_skeleton`'s `TODO.` placeholders, keep `rewrite_class == "standard"`, pass `ipd_lint` and placeholder-completeness checks, and avoid `not-equivalent` refusals.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Preserve IPD Concern and Scope bullets in the codemod

- [ ] E-01 Update `tools/fixture_codemod.py::_plan_site` where `norm in ("concern", "scope") and inferred_type == "ipd"` so it maps `norm` to canonical key `"Concern"` or `"Scope"` and sets `raw_fields_code[canon_label] = vexpr.code` before continuing. Do not set `has_invalid_input = True` for `Concern` or `Scope`, so valid IPD fixtures stay `rewrite_class == "standard"` while any invalid sibling field (such as `- Status: EXECUTED`) still sets `has_invalid_input = True` and coexists in `raw_fields`. Replace the branch's comment `# Template-owned IPD skeleton bullets (not in REGISTRY["ipd"]).` with one that says the bullets are not registry fields and so travel through `raw_fields` to overwrite the skeleton placeholders. Confirm `tools/fixture_codemod.py::F01_PATTERN` and non-IPD handling remain unchanged: a `- Concern:` bullet on a spec still refuses with `unsupported-shape` ("unknown field 'Concern' for record type 'spec'").
  - Depends on: none
  - Expected outcome: `tools/fixture_codemod.py::_plan_site` emits `raw_fields={'Concern': ..., 'Scope': ...}` (for static strings, mixed f-strings, single-placeholder f-strings, and lowercase `- concern:`/`- scope:` bullets) with `rewrite_class == "standard"`, overwriting `build_skeleton`'s `Concern: TODO.` and `Scope: TODO.` lines via `tests/record_builder.py::_apply_raw_fields` and `agent_workflows/artifact_meta.py::set_legacy_bullet_line`.
  - Execution state: pending

### Task group 2: Add behavioral fixture, core tests, and slow equivalence proof

- [ ] E-02 Add `tests/fixtures/fixture_codemod/ipd_concern_scope.py.txt` (never named `test_*.py` under `tests/fixtures/`) and fast core-tier behavioral tests in `tests/test_fixture_codemod.py` (using zero `inspect`, `ast`, or production source regex reads per `GUIDING_PRINCIPLES` P16):
  1. The fixture module contains exactly four F-01 sites, each a string literal bound to `text` inside its own `test_*` function, and each function asserts on `text` so that the assertions hold both on the original literal and on the `RecordBuilder().plan(...)` call the codemod substitutes: (i) a static IPD with `- Status: draft`, real `- Concern:` and `- Scope:` values, and every other required field, asserting `agent_workflows/ipd_authoring.py::authoring_placeholders_resolved(text)` is `True`, `agent_workflows/ipd_lint.py::C_DRAFT_READY` is among the codes in `ipd_lint.lint_text(text, checkpoint="author").advisories`, and `artifact_meta.read_text(text, record_type="ipd").fields["concern"]` equals the literal value; (ii) an IPD using a lowercase `- concern:` label and a single-placeholder `f"- Scope: {scope_var}\n"`, asserting both values through `read_text` and that `"Scope: TODO."` is absent; (iii) an IPD with `- Status: EXECUTED` and a `- Concern:` value, asserting the concern value; and (iv) a spec carrying `- Concern:`. Do NOT assert `lint_text(...).disposition == "conforming"` on site (i) unless its literal carries every required heading: a literal lacking them lints `error` (`IPD-H202`) while the skeleton-built rewrite lints `conforming`, so that assertion would itself cause a `not-equivalent` refusal. These fixture assertions execute only when E-03 runs the codemod's equivalence proof and the rewritten module under pytest; the core module does not run them.
  2. In `tests/test_fixture_codemod.py`, add tests that stage the fixture with `_stage_fixture_in_temp_repo` and make ONE `_run_codemod(repo, "--dry-run", "--format", "json", <target>)` call, asserting from its report: `totals["sites"] == 4`, `totals["rewrites"] == 3`, `totals["standard_rewrites"] == 2`, `totals["invalid_input_rewrites"] == 1`, `totals["refusals"] == 1`; sites (i) and (ii) have `rewrite_class == "standard"` and `raw_fields` keys exactly `{"Concern", "Scope"}` (site (ii) with value code `scope_var`, proving lowercase normalization and the single-placeholder case); site (iii) has `rewrite_class == "invalid-input"` and `raw_fields` keys `{"Status", "Concern"}`; site (iv) refuses with `reason == "unsupported-shape"`; and the target file is byte-identical afterwards. Add one more test that evaluates site (i)'s static `replacement` string with `RecordBuilder` in scope and asserts the rendered text contains the fixture's `- Concern:` and `- Scope:` lines and neither `Concern: TODO.` nor `Scope: TODO.`. Each subprocess call costs about 1.1 s and the module measured `11 passed in 7.96s` at review, so add no second subprocess call.
  3. Run `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_fixture_codemod.py`. If the total exceeds the 10-second serial bound (`j2xjtt` E-09/E-10), move the new dry-run test to `tests/test_fixture_codemod_slow.py` and list its node ID in `tests/slow_allowlist.txt`, as `j2xjtt` prescribes.
  - Depends on: E-01
  - Expected outcome: `tests/test_fixture_codemod.py` passes all existing and new tests in under 10 seconds under `-n 0` with zero unlisted slow tests.
  - Execution state: pending

- [ ] E-03 Add a subprocess `--apply` equivalence test in `tests/test_fixture_codemod_slow.py`, modeled on `test_case_h_rewritten_fixture_module_tests_pass`, that stages `tests/fixtures/fixture_codemod/ipd_concern_scope.py.txt` with `_stage_fixture_in_temp_repo` and runs `_run_codemod(repo, "--apply", "--format", "json", <target>)`. Assert `returncode == 0`; `totals["rewrites"] == 3`, `totals["refusals"] == 1`, and `totals["by_reason"]["not-equivalent"] == 0`; `modules[0]["changed"]` and `modules[0]["proof"]["equivalent"]` are `True` and `before_hash == after_hash`; the rewritten file contains `RecordBuilder().plan(` and `'Concern':` and still contains the spec literal; and a nested `python3 -m pytest -o addopts= -m "" -p no:randomly -n 0 -v <rewritten target>` run from `support.REPO_ROOT` with `support.pinned_env()` exits 0. Record the new node ID in `tests/slow_allowlist.txt` beside `test_case_g` and `test_case_h`. Reference measurement from the review (scratch copy, outside the repository): the unpatched tool refuses sites (i) to (iii) as `not-equivalent`; the patched tool rewrites all three with zero `not-equivalent`.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_fixture_codemod_slow.py` passes with zero `not-equivalent` refusals and zero unlisted slow-test warnings.
  - Execution state: pending

### Task group 3: Validate repository gates and commit

- [ ] E-04 After the final edit, run every repository gate: `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_fixture_codemod.py`, `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_fixture_codemod_slow.py`, bare `python3 -m pytest`, `make test-all`, `make typecheck` (it covers `agent_workflows/` only, so it is a no-regression gate here), and `aw sanitize --agent`. Verify `rg -n "inspect\.|getsource" tests/test_fixture_codemod.py tests/test_fixture_codemod_slow.py` produces no matches. Then commit only modified `- Scope-Paths:` files via `aw commit kbh055 -- <paths>`. Pre-transition lint and finalize are NOT part of this item: they run after every `V-*` reads `pass` (see the gate's POST-GATE LIFECYCLE clause), because pre-transition lint refuses while this item is still `pending`.
  - Depends on: E-03
  - Expected outcome: All targeted, core-tier, thorough-tier, typecheck, and leak-scan checks pass, and the commit changes only `- Scope-Paths:` files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/record_builder.py::RecordBuilder.plan` validates keyword arguments via `_validate_fields("ipd", check_fields)` against `agent_workflows/artifact_meta.py::registry_fields("ipd")` and builds the base IPD text via `agent_workflows/ipd_authoring.py::build_skeleton`, which emits `Concern: TODO.` and `Scope: TODO.`. `RecordBuilder.plan` already applies `raw_fields=` last via `tests/record_builder.py::_apply_raw_fields` -> `agent_workflows/artifact_meta.py::set_legacy_bullet_line`.
- Existing hand-written tests in `tests/test_finalize_sendback.py` and `tests/test_attention.py` already supply `Concern` and `Scope` on `RecordBuilder.plan` using `raw_fields={"Concern": ..., "Scope": ...}`.
- `tools/fixture_codemod.py::_plan_site` already uses `raw_fields_code` without setting `has_invalid_input = True` for valid non-skeleton IPD roles (`tools/fixture_codemod.py::_is_known_ipd_non_skeleton_role`), keeping `rewrite_class == "standard"`.
- `agent_workflows/artifact_meta.py::set_legacy_bullet_line` matches `^- <label>:` case-sensitively inside `metadata_region`, so passing lowercase `"concern"` or `"scope"` would insert a duplicate line while leaving `Concern: TODO.` or `Scope: TODO.` intact. Mapping `norm` to `"Concern"` and `"Scope"` overwrites the skeleton placeholders in place.
- `tests/test_fixture_codemod.py` enforces a 10-second serial wall-time bound under `-n 0` (`j2xjtt` E-09/E-10, `n0li9v` E-13; baseline measured at `11 passed in 8.35s` by the author and `11 passed in 7.96s` at review), and `tests/test_fixture_codemod_slow.py` hosts slower subprocess `--apply` equivalence tests whose node IDs are listed in `tests/slow_allowlist.txt` (baseline measured at `2 passed in 5.47s`).
- Cite code by repository-relative `path::Symbol` identifiers or quoted strings rather than bare line numbers (`IPD-C801`).

## Findings

| Id | Source inspected | Finding |
|---|---|---|
| F-01 | `tools/fixture_codemod.py::_plan_site` | The branch `elif norm in ("concern", "scope") and inferred_type == "ipd": continue` silently discards `Concern` and `Scope` metadata bullets on every rewritten IPD fixture. |
| F-02 | `agent_workflows/ipd_authoring.py::build_skeleton`, `_AUTHORING_PLACEHOLDERS` | `build_skeleton` emits `Concern: TODO.` and `Scope: TODO.`, both listed in `_AUTHORING_PLACEHOLDERS`. Because `RecordBuilder.plan` receives neither field when `fixture_codemod` drops them, `authoring_placeholders_resolved` returns `False`, suppressing `check.ipd-draft-ready-to-review` in `agent_workflows/ipd_lint.py::_draft_ready_advisory` and `agent_workflows/check_engine.py::check_ipd_draft_ready`, and breaking `tests/test_run_selection_policy.py::_COMPLETE_PLAN` (`authoring_placeholders_resolved` becomes `False` instead of `True`) and `tests/test_ipd_lint.py::_conforming_child` (missing `- Scope: sample.` breaks `.replace("- Scope: sample.", ...)` insertions of `- Scope-Paths:` and suppresses draft readiness). |
| F-03 | `tests/test_readers_attention.py::test_short_description_wins_over_extract_detail_fallback` | When `- Scope:` is dropped, `- Scope: Fallback scope paragraph.` becomes `Scope: TODO.`, changing `detail_text` from `"Fallback scope paragraph."` to `"TODO."` and causing `not-equivalent` refusal. |
| F-04 | `git grep` for `"- Concern: "` or `"- Scope: "` literals over `tests/test_*.py` at `39400b74c` and at review HEAD; `tools/fixture_codemod.py::analyze_module` over the HEAD matches | At authoring, 54 modules carried such literals. Executed plan `59aiyh` has since rewritten most of them by hand onto `RecordBuilder(..., raw_fields={"Concern": ..., "Scope": ...})` (for example `tests/test_gradcover_end_to_end.py`, `tests/test_companion_doctor_and_carriers.py`), so at review HEAD 6 modules remain and the codemod refuses all 8 of their sites for unrelated reasons (`legacy-format subject`, `setter-byte assertion`). The fix therefore protects future codemod runs and the fixture suite; it changes no current repository test module. |
| F-05 | `python3 -m pytest -o addopts="" -n 0 -v --durations=0` on `tests/test_fixture_codemod.py` and `tests/test_fixture_codemod_slow.py` | Baseline passes (`11 passed in 8.35s` in `tests/test_fixture_codemod.py` and `2 passed in 5.47s` in `tests/test_fixture_codemod_slow.py`). Adding subprocess `--apply` equivalence tests to `tests/test_fixture_codemod.py` would push it near or above the 10-second limit, so `--dry-run` and fast in-process checks belong in `tests/test_fixture_codemod.py` while `--apply` equivalence stays in `tests/test_fixture_codemod_slow.py`. |

## Proposed changes (ordered, validatable)

The entity-relationship diagram below maps the components and test surfaces connected by this fix:

```mermaid
erDiagram
    FIXTURE_CODEMOD ||--o{ RECORDBUILDER_PLAN : "emits raw_fields Concern and Scope"
    RECORDBUILDER_PLAN ||--|| BUILD_SKELETON : "starts from TODO placeholders"
    RECORDBUILDER_PLAN ||--o{ SET_LEGACY_BULLET_LINE : "overwrites Concern and Scope in metadata_region"
    SET_LEGACY_BULLET_LINE ||--o{ IPD_LINT_AND_PLACEHOLDER_CHECKS : "satisfies authoring_placeholders_resolved and Scope readers"
    CODEMOD_TESTS ||--o{ FIXTURE_CODEMOD : "verifies dry-run, standard class, and apply equivalence"
```

The flowchart below shows the bullet-mapping branches in `tools/fixture_codemod.py::_plan_site` and the execution order (`E-01` through `E-04`):

```mermaid
flowchart TD
    E01["E-01: Update _plan_site to map IPD Concern and Scope into raw_fields"] --> E02["E-02: Add ipd_concern_scope.py.txt and fast core tests in test_fixture_codemod.py"]
    E02 --> E03["E-03: Add apply equivalence test in test_fixture_codemod_slow.py and slow_allowlist.txt"]
    E03 --> E04["E-04: Run all test, typecheck, and leak gates and commit"]

    B["Parse IPD metadata bullet in _plan_site"] --> C{"norm in concern or scope?"}
    C -->|Yes| D["Set raw_fields_code['Concern' or 'Scope'] = vexpr.code; keep has_invalid_input unchanged"]
    C -->|No| F["Map through registry_fields and validate static values"]
    F -->|Valid| G["Emit keyword argument with standard rewrite_class"]
    F -->|Invalid| H["Set raw_fields_code and has_invalid_input = True"]
    D --> I["RecordBuilder.plan calls set_legacy_bullet_line to overwrite TODO. placeholders"]
```

1. **Preserve IPD `Concern` and `Scope` in `tools/fixture_codemod.py::_plan_site` (`E-01`)**: Replace the dropping `continue` branch with canonical `raw_fields_code["Concern"]` / `raw_fields_code["Scope"]` assignment without setting `has_invalid_input = True`.
2. **Add fixture and fast core-tier behavioral tests (`E-02`)**: Add `tests/fixtures/fixture_codemod/ipd_concern_scope.py.txt` and tests in `tests/test_fixture_codemod.py` covering static, f-string, single-placeholder, lowercase-label, invalid-sibling, and non-IPD behavior while keeping serial runtime under 10 seconds.
3. **Add subprocess `--apply` equivalence test (`E-03`)**: Add a slow equivalence test in `tests/test_fixture_codemod_slow.py` verifying zero `not-equivalent` refusals and passing rewritten-module pytest execution, and record its node ID in `tests/slow_allowlist.txt`.
4. **Verify all gates and commit (`E-04`)**: Run targeted, core-tier, thorough-tier, `mypy`, and leak-scan gates, then commit via `aw commit kbh055 -- <paths>`. Pre-transition lint and finalize follow in the gate's POST-GATE LIFECYCLE clause.

## Deferred / out of scope (with reason)

- Rewriting repository test modules carrying IPD `Concern` and `Scope` sites onto `RecordBuilder` (already done by hand for most of them):
  - Carrier: 59aiyh
  - Carrier-Evidence: .aw/records/plans/executed/20261102-metastore-10-59aiyh-move-test-data-to-one-shared-record-builder-over-artifact-me.ipd.md
- Fixing `tools/fixture_codemod.py` dropping H1 heading titles on backlog and prompt records:
  - Carrier: e0wwtc
- Fixing `tools/fixture_codemod.py::_is_body_or_oq_kwarg` misclassifying full record literals passed via `body=` to non-`RecordBuilder` helpers:
  - Carrier: lufe6m
- Adding `concern` and `scope` keyword parameters to `tests/record_builder.py::RecordBuilder.plan` or modifying `agent_workflows/ipd_authoring.py::build_skeleton`:
  - Carrier-Declined: `RecordBuilder.plan` validates keyword fields strictly against `registry_fields("ipd")`, already supports `Concern` and `Scope` via `raw_fields=`, and existing tests (`tests/test_finalize_sendback.py`, `tests/test_attention.py`) use `raw_fields={"Concern": ..., "Scope": ...}` without altering `RecordBuilder.plan` or `tests/test_record_builder.py::RecordBuilderGoldenTests.test_golden_ready_plan_text`.
- Adding `- Concern:` or `- Scope:` to `tools/fixture_codemod.py::F01_PATTERN`:
  - Carrier-Declined: `F01_PATTERN` is the established F-01 census regex (`y3uowx`); expanding it would sweep prose bullets mentioning `- Scope:` or `- Concern:` that are not record fixtures, while real IPD fixtures already match `F01_PATTERN` via `- Id:`, `- Status:`, `- Kind:`, `- Set:`, or `- Date:`.

## Scope check

- Over-scope: none. `- Scope-Paths:` names only `tools/fixture_codemod.py`, `tests/test_fixture_codemod.py`, `tests/test_fixture_codemod_slow.py`, `tests/fixtures/fixture_codemod/ipd_concern_scope.py.txt`, and `tests/slow_allowlist.txt`.
- Under-scope: none. Covers static and dynamic IPD `Concern` and `Scope` preservation, lowercase normalization, `standard` vs `invalid-input` rewrite classification, placeholder resolution, `ipd_lint` readiness advisories, `- Scope:` preservation, core-tier budget, and full subprocess `--apply` equivalence.

## Required tests / validation

- Targeted core codemod suite (must stay under 10 seconds under `-n 0`):
  `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_fixture_codemod.py`
- Targeted slow equivalence codemod suite:
  `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_fixture_codemod_slow.py`
- Repository gates:
  - `python3 -m pytest`
  - `make test-all`
  - `make typecheck`
  - `aw sanitize --agent`
- Lifecycle gate, after every `V-*` reads `pass`: `aw ipd lint --phase pre-transition --agent .aw/records/plans/pending/20261121-b1j6bl-01-kbh055-preserve-concern-and-scope-bullets-in-fixture-codemod-plan-s.ipd.md` reports `conforming`.

## Spec / documentation sync

N/A with reason: internal defect fix in `tools/fixture_codemod.py::_plan_site`; `tools/README.md` (`fixture_codemod.py`) does not document dropping `Concern` or `Scope`, and no CLI flags, refusal reason codes, or specification contracts change.

## Open questions

### OQ-01: Should fixture_codemod._plan_site emit Concern and Scope via raw_fields or add keyword parameters to RecordBuilder.plan?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence in `tests/record_builder.py::RecordBuilder.plan`, `tests/record_builder.py::_apply_raw_fields`, `agent_workflows/artifact_meta.py::registry_fields`, `tests/test_finalize_sendback.py`, `tests/test_attention.py`, and `tools/fixture_codemod.py::_is_known_ipd_non_skeleton_role`. `Concern` and `Scope` are non-registry IPD schema fields, `RecordBuilder.plan` enforces `registry_fields("ipd")` on keyword arguments, `RecordBuilder.plan` already overwrites `build_skeleton`'s `Concern: TODO.` and `Scope: TODO.` lines when passed `raw_fields={"Concern": ..., "Scope": ...}`, and `tools/fixture_codemod.py::_plan_site` already uses `raw_fields` without setting `has_invalid_input = True` for valid non-skeleton IPD field values. Emitting canonical `"Concern"` and `"Scope"` entries into `raw_fields` in `_plan_site` fixes the drop directly with minimal blast radius.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result (which are reachable by construction), name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff -- tools/fixture_codemod.py` hunk showing `Concern` and `Scope` mapped to canonical `"Concern"` and `"Scope"` entries in `raw_fields_code` without setting `has_invalid_input = True`, with `F01_PATTERN` and non-IPD behavior unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff --stat -- tests/fixtures/fixture_codemod/ipd_concern_scope.py.txt tests/test_fixture_codemod.py`; the new test functions' assertion lines on `totals` (sites 4, rewrites 3, standard 2, invalid-input 1, refusals 1), on each site's `rewrite_class` and `raw_fields` keys, on site (iv)'s `unsupported-shape` reason, on the unchanged target bytes, and on the rendered site (i) text; actual output of `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_fixture_codemod.py` showing every test `PASSED`, the total under 10 seconds, and `0 unlisted slow tests`; and `rg -n "inspect\.|getsource" tests/test_fixture_codemod.py` returning no matches.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff -- tests/test_fixture_codemod_slow.py tests/slow_allowlist.txt` hunks (the new node ID listed beside `test_case_g` and `test_case_h`); the new test's assertion lines on `rewrites == 3`, `not-equivalent == 0`, `proof.equivalent`, `before_hash == after_hash`, and the nested pytest exit code 0; actual output of `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_fixture_codemod_slow.py` showing the new test `PASSED` with `0 unlisted slow tests`; and `rg -n "inspect\.|getsource" tests/test_fixture_codemod_slow.py` returning no matches.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the actual summary lines of bare `python3 -m pytest`, `make test-all`, and `make typecheck`; the `aw sanitize --agent` result record (`"outcome":"clean"`); and `git show --stat` of the `aw commit kbh055` commit(s), listing only `- Scope-Paths:` files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`- Status: approved` or authorized automated approval) and with `- Item-Dependencies: none` confirmed. All open questions are resolved (`OQ-01`).

SCOPE FENCE. `- Scope-Paths:` declares `tools/fixture_codemod.py`, `tests/test_fixture_codemod.py`, `tests/test_fixture_codemod_slow.py`, `tests/fixtures/fixture_codemod/ipd_concern_scope.py.txt`, and `tests/slow_allowlist.txt`. Do not expand scope casually; if execution genuinely requires editing a file outside the fence, make the edit and justify it in two-way scope reconciliation at finalize (`--scope-reason`), and acknowledge any declared-but-unmodified path with `--scope-ack`. Stop and report only on a genuinely unsafe condition such as an unresolvable concurrent-edit conflict or missing prerequisite symbols in `tools/fixture_codemod.py` (`_plan_site`, `_template_to_value_expr`, `_parse_bullet_site`).

HONESTY. Every `V-*` evidence block must paste actual observed runner output from commands run after the final edit; never claim success you did not run.

COMMIT. Commit only files changed for this plan through `aw commit kbh055 -- <paths>`; verify `git diff --cached --name-only` contains only your paths; never use `git add -A`, bare `git add`, or `git commit -a`; never push without an explicit human request.

POST-GATE LIFECYCLE. Once every `E-*` item has `Execution state: performed`, every `V-*` item has `Result: pass`, and `aw ipd lint --phase pre-transition` reports `conforming`, the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`. When `aw oc run` or `aw agy run` executes this plan, the runner owns the begin receipt and the finalize. When this plan is executed by hand or by a direct agent turn, start with `aw ipd begin kbh055 --actor <agent/model>` and end, after the work commit, with `aw ipd finalize kbh055 --actor <agent/model> --message "<summary>" --apply`. This plan inherits `- Blocks-Release: next` from backlog `b1j6bl`, so closing `b1j6bl` as `done` after execution follows the executed-carrier handoff path.
