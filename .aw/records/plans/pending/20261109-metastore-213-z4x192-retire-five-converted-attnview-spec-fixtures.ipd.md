# IPD: Retire five converted attnview spec fixtures

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 6: once no test reads the tracked attnview `specs-valid` fixtures, they are dead legacy-format copies that the cutover would otherwise have to rewrite. `9rgn2w` E-10 removed them inside one large item; research `nj8zdp` guidance splits the deletion into plans of at most 8 files.
- Scope: Part of the round-3 split of `9rgn2w` E-10 (2026-11-09, research `nj8zdp` guidance): delete 5 of the 9 converted `specs-valid` fixtures. EXCLUDES: the `violations/` set and `review-pilot/plans/` (kept literal); the consumer conversion (`7fpc8v`); production code.
- Scope-Paths: tests/fixtures/attnview/specs-valid/approved.md, tests/fixtures/attnview/specs-valid/deferred.md, tests/fixtures/attnview/specs-valid/draft.md, tests/fixtures/attnview/specs-valid/implemented.md, tests/fixtures/attnview/specs-valid/implementing.md, .aw/records/plans/pending/20261109-metastore-213-z4x192-retire-five-converted-attnview-spec-fixtures.ipd.md
- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:j6o96i, executed:7fpc8v
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 213
- Highest E allocated: 28
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: z4x192

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 9rgn2w (round 3, research nj8zdp guidance).

## Goal

The 5 named `specs-valid` fixtures, which no test reads any more, are deleted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Item ids E-01, E-02, E-10 and E-13 are the ids these items had in `59aiyh` and `9rgn2w`; they are kept so that every reference between them (for example "E-13's `full-before.txt`", "the builder's `raw_fields=` escape (E-01)") still points at the right item across the family. New ids added by the round-3 split start at E-15.

### Task group 1: delete fixtures

- [ ] E-26 (part of `9rgn2w` E-10, round-3 split 2026-11-09) Delete the converted fixtures `tests/fixtures/attnview/specs-valid/approved.md`, `tests/fixtures/attnview/specs-valid/deferred.md`, `tests/fixtures/attnview/specs-valid/draft.md` with `git rm`, after confirming `rg -n "specs-valid" tests` lists no reader of them (Order 174, `7fpc8v`, moved every reader onto builder recipes).
  - Depends on: none
  - Expected outcome: the named files are gone and no test references them.
  - Execution state: pending

- [ ] E-27 (part of `9rgn2w` E-10, round-3 split 2026-11-09) Delete the converted fixtures `tests/fixtures/attnview/specs-valid/implemented.md`, `tests/fixtures/attnview/specs-valid/implementing.md` with `git rm`, after confirming `rg -n "specs-valid" tests` lists no reader of them (Order 174, `7fpc8v`, moved every reader onto builder recipes).
  - Depends on: none
  - Expected outcome: the named files are gone and no test references them.
  - Execution state: pending

### Task group 2: finish

- [ ] E-28 Finish: Run the batch-rule step-2 command over `tests/test_attention_contract.py`, `tests/test_specs_verbs.py` and `tests/test_specs_releases_unsafe_field.py` and the bare core gate `python3 -m pytest`; commit through `aw commit z4x192 -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-26, E-27
  - Expected outcome: the three modules' outcome lists match their Order 174 after-lists; all runs pass; every commit is path-scoped to Scope-Paths.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Interface names from Order 02 (`tve77h`): `artifact_meta.registry_fields(type)`, `artifact_meta.validate_event`, `artifact_meta.validate_new_events(type, events, *, records_root, migration_import=False)`, `artifact_meta.read(id6) -> State`, `artifact_meta.create(...)` and `artifact_meta.append(id6, events, *, expect_seq)`. Order 02's `create`/`append` write the log format; `2xwb9b` E-03 adds the phase-B legacy branch of `append` and `xexn45` E-01 routes the phase-B branch of `create` and `append` through `write_legacy`, with `render_legacy_text(text, events)` (`xexn45` E-11) as the same renderer over a string. In phase B the on-disk format is the bullet format; the legacy loader reads it into the cache.
- `review_findings.render_review` (pure) and `review_findings.write_review` render and write a `.review.md` record; no CLI calls `write_review` (`xexn45` Findings).
- The existing shared plan builder is `support.ready_plan_text`, which is "BUILT FROM THE REAL GENERATOR (`ipd_authoring.build_skeleton`)" and then fills the fields a draft leaves open; the builder keeps that approach for plans, so a scaffold change still reaches every fixture.
- Shared test plumbing lives in `tests/support.py` (`init_repo`, `git`, `run_cli`, `pinned_env`, `ready_plan_text`, `scope_drift_repo`); `tests/repo_template.py` (`copy_template_repo`) gives a pre-built repository; there is no `tests/conftest.py`, and the root `conftest.py` owns tier selection.
- Tests are behavioral (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); core modules set `pytestmark = pytest.mark.core`; `slow` tests are listed in `tests/slow_allowlist.txt`; `pyproject.toml` `addopts` deselects `slow` and `livecorpus`, so a complete comparison passes `-m ""`, and `pytest-randomly` is installed, so a deterministic order needs `-p no:randomly`.
- `tests/fixtures/review-pilot/` is the input corpus of `tools/review_pilot.py` (`manifest.json` names each plan file, `defects.json` quotes exact text to plant), and `tests/test_review_pilot.py` copies the whole directory into its fixture repository.
- Filenames come from `artifact_naming.build_clustered_name` and parse with `artifact_naming.parse_clustered`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4` (the split measurement) unless a row says otherwise; carried from `9rgn2w`.

| Id | Evidence | Finding |
|---|---|---|
| F-42 | `rg -n "FIX\b|specs-valid|violations/|CONFORMING_ORCHESTRATOR|ORCH_IPD"` per module at `3d0ddb845`: `test_attention_contract` 5, `test_specs_verbs` 4, `test_specs_releases_unsafe_field` 5, `test_attention` 0, `test_attention_stem` 0, `test_ipd_lint` 17, `test_ipd_schema` 24 (all `CONFORMING_ORCHESTRATOR`/`ORCH_IPD`); `git ls-files tests/fixtures | grep attnview` lists 9 `specs-valid` and 8 `violations` files plus `README.md` | The attnview `specs-valid` set is read by three modules; `violations/` stays literal (`9rgn2w` E-10 rule 2); `test_attention` and `test_attention_stem` read no fixture file. |

## Proposed changes (ordered, validatable)

1. Delete the named fixtures.
2. Run the consumers and the core gate, commit.

## Deferred / out of scope (with reason)

- Converting the consumer modules.
  - Carrier: 7fpc8v
- The `violations/` set stays literal malformed input (`9rgn2w` E-10 rule 2).
  - Carrier: 9rgn2w

## Scope check

- Over-scope: none. No production module changes.
- Under-scope: none known. Size: 3 E-items, 5 work Scope-Paths.

## Required tests / validation

Validated by the unchanged outcomes of the three consumer modules and the bare core gate.

## Spec / documentation sync

No spec change; implements the builder half of `4sd62s` section 6 and section 7 step 6.

## Open questions

### OQ-01: Which prior Orders does the builder depend on?

- Blocking: no
- Status: resolved
- Owner: plan-review (round 1 of `59aiyh`, decision D-1)
- Resolution or deferral rationale: `tve77h` and `xexn45` (and `g5hpbb`, added 2026-11-07), carried from `59aiyh` OQ-02: only `xexn45` gives `artifact_meta.create` a phase-B legacy branch (`write_legacy`) and adds `render_legacy_text`, so depending only on `tve77h` would force the builder to carry its own renderer. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-26 validates E-26
  - Required evidence: paste `rg -n "specs-valid" tests` (no reader), and `git status --short tests/fixtures/attnview/specs-valid/` listing each of `tests/fixtures/attnview/specs-valid/approved.md`, `tests/fixtures/attnview/specs-valid/deferred.md`, `tests/fixtures/attnview/specs-valid/draft.md` as deleted.
  - Observed evidence:
  - Result: pending

- [ ] V-27 validates E-27
  - Required evidence: paste `rg -n "specs-valid" tests` (no reader), and `git status --short tests/fixtures/attnview/specs-valid/` listing each of `tests/fixtures/attnview/specs-valid/implemented.md`, `tests/fixtures/attnview/specs-valid/implementing.md` as deleted.
  - Observed evidence:
  - Result: pending

- [ ] V-28 validates E-28
  - Required evidence: paste the PASSED/FAILED counts of `tests/test_attention_contract.py`, `tests/test_specs_verbs.py` and `tests/test_specs_releases_unsafe_field.py` each (unchanged from Order 174), the bare `python3 -m pytest` summary line, and every `aw commit z4x192` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `g5hpbb`, `tve77h`, `xexn45`, `j6o96i`, `7fpc8v` are executed. Every open question is resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if the work cannot be done without a production change, stop and report the missing capability.

Honesty rule: run every command a V-item names and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit z4x192 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
