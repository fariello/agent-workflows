# IPD: Move the attnview spec fixture consumers onto the record builder

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 6 requires test data from ONE shared record builder in phase B. `9rgn2w` E-10 converted 26 tracked `.md` fixtures and seven consuming modules in one item. Research `nj8zdp` guidance (about one file per E-item, at most 5 E-items) splits it: this part moves the three modules that read `tests/fixtures/attnview/specs-valid/` onto builder recipes, one module per item.
- Scope: Part of the round-3 split of `9rgn2w` E-10 (2026-11-09, research `nj8zdp` guidance): the attnview consumers (E-22 to E-24 one module each, E-25 the two named modules that read no fixture plus the finish). EXCLUDES: deleting the fixture files (`z4x192`, `9zcuyh`); the orchestrator fixture (`b3eilr`); the `violations/` and `review-pilot/plans/` sets (kept literal); production code.
- Scope-Paths: tests/test_attention_contract.py, tests/test_specs_verbs.py, tests/test_specs_releases_unsafe_field.py, tests/test_attention.py, tests/test_attention_stem.py, .aw/records/plans/pending/20261109-metastore-174-7fpc8v-move-the-attnview-spec-fixture-consumers-onto-the-record-bui.ipd.md
- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:j6o96i
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 174
- Highest E allocated: 25
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7fpc8v

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 9rgn2w (round 3, research nj8zdp guidance).

## Goal

The three test modules that read the attnview `specs-valid` fixtures build those specs with `RecordBuilder.spec(...)` instead, with identical per-test outcomes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Item ids E-01, E-02, E-10 and E-13 are the ids these items had in `59aiyh` and `9rgn2w`; they are kept so that every reference between them (for example "E-13's `full-before.txt`", "the builder's `raw_fields=` escape (E-01)") still points at the right item across the family. New ids added by the round-3 split start at E-15.

### Task group 1: one consumer per item

- [ ] E-22 (part of `9rgn2w` E-10, round-3 split 2026-11-09) In `tests/test_attention_contract.py`, replace each read of a `tests/fixtures/attnview/specs-valid/*.md` file with a builder recipe: build the nine valid specs (one per spec native status: `approved`, `deferred`, `draft`, `implemented`, `implementing`, `parked`, `reviewed`, `superseded`, `to-review`) with `RecordBuilder.spec(...)` into a temporary directory and iterate over those files where the test now globs `FIX / "specs-valid"`. The reads are in `FixtureParseTests.test_valid_specs_have_bare_enum_status_and_map`. The `violations/` reads stay literal: their purpose is malformed legacy input (`9rgn2w` E-10 rule 2). Keep every assertion unchanged.
  - Depends on: none
  - Expected outcome: the module's per-test outcome list (batch-rule step-2 command over `tests/test_attention_contract.py` alone) is identical before and after, and the module no longer reads `specs-valid`.
  - Execution state: pending

- [ ] E-23 (part of `9rgn2w` E-10, round-3 split 2026-11-09) In `tests/test_specs_verbs.py`, replace each read of a `tests/fixtures/attnview/specs-valid/*.md` file with a builder recipe: build the nine valid specs (one per spec native status: `approved`, `deferred`, `draft`, `implemented`, `implementing`, `parked`, `reviewed`, `superseded`, `to-review`) with `RecordBuilder.spec(...)` into a temporary directory and iterate over those files where the test now globs `FIX / "specs-valid"`. The reads are in `CheckTests.test_valid_specs_pass`. The `violations/` reads stay literal: their purpose is malformed legacy input (`9rgn2w` E-10 rule 2). Keep every assertion unchanged.
  - Depends on: none
  - Expected outcome: the module's per-test outcome list (batch-rule step-2 command over `tests/test_specs_verbs.py` alone) is identical before and after, and the module no longer reads `specs-valid`.
  - Execution state: pending

- [ ] E-24 (part of `9rgn2w` E-10, round-3 split 2026-11-09) In `tests/test_specs_releases_unsafe_field.py`, replace each read of a `tests/fixtures/attnview/specs-valid/*.md` file with a builder recipe: build the nine valid specs (one per spec native status: `approved`, `deferred`, `draft`, `implemented`, `implementing`, `parked`, `reviewed`, `superseded`, `to-review`) with `RecordBuilder.spec(...)` into a temporary directory and iterate over those files where the test now globs `FIX / "specs-valid"`. The reads are in `test_non_regression_valid_specs_fixtures`. The `violations/` reads stay literal: their purpose is malformed legacy input (`9rgn2w` E-10 rule 2). Keep every assertion unchanged.
  - Depends on: none
  - Expected outcome: the module's per-test outcome list (batch-rule step-2 command over `tests/test_specs_releases_unsafe_field.py` alone) is identical before and after, and the module no longer reads `specs-valid`.
  - Execution state: pending

### Task group 2: check and finish

- [ ] E-25 Check the two remaining named consumers and finish: `9rgn2w` E-10 names `tests/test_attention.py` and `tests/test_attention_stem.py` as attnview consumers, but at `3d0ddb845` neither reads `tests/fixtures/attnview/` (`rg -n "FIX|fixtures" ` finds only the Set name `attnview` in prose and a backlog filename); re-run that search, and convert any read it now finds by the E-22 recipe, else record `no fixture read`. Then run the batch-rule step-2 command over the five modules, the bare core gate `python3 -m pytest`, and commit through `aw commit 7fpc8v -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-22, E-23, E-24
  - Expected outcome: the search result for each of the two modules is recorded; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
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
| F-05 | 26 tracked `.md` fixtures carry `^- (Id\|Status):` (`fixtures/attnview/specs-valid` 9, `fixtures/attnview/violations` 7, `fixtures/review-pilot/plans` 9, `fixtures/conforming-orchestrator.md` 1; unchanged at `ac76110f4`); 8 test modules contain `aw-prompt` (7 at review); 60 `ipd_lint.lint_text(` calls in 11 test modules | The builder needs a text form and a prompt form; the review-pilot corpus stays literal (E-10). |
| F-42 | `rg -n "FIX\b|specs-valid|violations/|CONFORMING_ORCHESTRATOR|ORCH_IPD"` per module at `3d0ddb845`: `test_attention_contract` 5, `test_specs_verbs` 4, `test_specs_releases_unsafe_field` 5, `test_attention` 0, `test_attention_stem` 0, `test_ipd_lint` 17, `test_ipd_schema` 24 (all `CONFORMING_ORCHESTRATOR`/`ORCH_IPD`); `git ls-files tests/fixtures | grep attnview` lists 9 `specs-valid` and 8 `violations` files plus `README.md` | The attnview `specs-valid` set is read by three modules; `violations/` stays literal (`9rgn2w` E-10 rule 2); `test_attention` and `test_attention_stem` read no fixture file. |

## Proposed changes (ordered, validatable)

1. Convert each consumer module (E-22 to E-24).
2. Check the other two named modules, run, commit (E-25).

## Deferred / out of scope (with reason)

- Deleting the converted `specs-valid` files and updating the fixture README.
  - Carrier: z4x192
- The `support.CONFORMING_ORCHESTRATOR` fixture.
  - Carrier: b3eilr
- The review-pilot corpus stays literal legacy input.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. No production module changes.
- Under-scope: none known. Size: 4 E-items, 5 work Scope-Paths; each E-22 to E-24 edits one module.

## Required tests / validation

Each module is validated by an identical per-test outcome list before and after. Commands: the batch-rule step-2 command per module, the bare core gate `python3 -m pytest`.

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

- [ ] V-22 validates E-22
  - Required evidence: paste the empty `diff` of the before and after outcome lists of `tests/test_attention_contract.py` (batch-rule step-2 command over that module alone), and `rg -n "specs-valid" tests/test_attention_contract.py` printing nothing while `rg -n "violations" tests/test_attention_contract.py` still lists the literal violation reads.
  - Observed evidence:
  - Result: pending

- [ ] V-23 validates E-23
  - Required evidence: paste the empty `diff` of the before and after outcome lists of `tests/test_specs_verbs.py` (batch-rule step-2 command over that module alone), and `rg -n "specs-valid" tests/test_specs_verbs.py` printing nothing while `rg -n "violations" tests/test_specs_verbs.py` still lists the literal violation reads.
  - Observed evidence:
  - Result: pending

- [ ] V-24 validates E-24
  - Required evidence: paste the empty `diff` of the before and after outcome lists of `tests/test_specs_releases_unsafe_field.py` (batch-rule step-2 command over that module alone), and `rg -n "specs-valid" tests/test_specs_releases_unsafe_field.py` printing nothing while `rg -n "violations" tests/test_specs_releases_unsafe_field.py` still lists the literal violation reads.
  - Observed evidence:
  - Result: pending

- [ ] V-25 validates E-25
  - Required evidence: paste `rg -n "attnview|specs-valid|violations/" tests/test_attention.py tests/test_attention_stem.py` output with the reading of each hit (prose or fixture read), the outcome-list `diff` of any module E-25 changed (empty), the bare `python3 -m pytest` summary line, and every `aw commit 7fpc8v` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `g5hpbb`, `tve77h`, `xexn45`, `j6o96i` are executed. Every open question is resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if the work cannot be done without a production change, stop and report the missing capability.

Honesty rule: run every command a V-item names and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 7fpc8v -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
