# IPD: Add the shared test record builder and convert the tracked record fixtures

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13) changes the builder and not hundreds of test files. Measured 2026-11-07 at `ac76110f4`: 323 Python files under `tests/` carry 6,820 F-01 legacy lines, 92 private record-building helpers live in 62 test modules, `support.ready_plan_text` has 30 calls in 15 modules, and 26 tracked `.md` fixtures carry `- Id:` or `- Status:` bullets. Part 1 of the split of `59aiyh` (Order 10): this part captures every baseline, builds and tests the builder, and converts the tracked fixtures; Orders 38 to 40 (`x05v02`, `7qxey9`, `nbfg7w`) move the test modules onto it in subsets of at most 25 modules each.
- Scope: `59aiyh` E-13 (baselines), E-01 (the builder), E-02 (its tests) and E-10 (tracked `.md` fixtures), carried verbatim with their original ids so their cross-references stay valid, plus a finishing commit item E-14. EXCLUDES: every test-module batch (Orders 38 to 40 and `59aiyh` E-09); the switch-point proof, the F-06 census and the full-suite comparison (`59aiyh` E-11, E-12); changing production code; the review-pilot corpus (`tests/fixtures/review-pilot/plans/`, kept literal); the log format (Order 13).
- Scope-Paths: tests/record_builder.py, tests/test_record_builder.py, tests/support.py, tests/fixtures/record_builder/**, tests/fixtures/attnview/**, tests/fixtures/conforming-orchestrator.md, tests/test_attention.py, tests/test_attention_stem.py, tests/test_attention_contract.py, tests/test_specs_verbs.py, tests/test_specs_releases_unsafe_field.py, tests/slow_allowlist.txt, .aw/records/plans/pending/20261107-metastore-37-9rgn2w-add-the-shared-test-record-builder-and-convert-the-tracked-r.ipd.md
- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 37
- Highest E allocated: 14
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9rgn2w

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 59aiyh per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

One tested `tests/record_builder.py` exists that writes every record type through `artifact_meta`, `support.ready_plan_text` is a thin call into it with identical bytes, the tracked record fixtures that tests copy or lint are builder output, and every baseline the later parts compare against is captured before the first edit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Item ids E-01, E-02, E-10 and E-13 are the ids these items had in `59aiyh`; they are kept so that every reference between them (for example "E-13's `full-before.txt`", "the builder's `raw_fields=` escape (E-01)") still points at the right item. The batch-rule references to E-03 to E-09 inside the carried text mean the batch items of Orders 38 to 40 and `59aiyh` E-09.

### Task group 1: baselines and the builder

- [ ] E-13 Capture every baseline BEFORE any edit, under the gitignored `.aw/state/59aiyh/`:
  - the bare `python3 -m pytest` summary line and wall time (`core-before.txt`);
  - the full-suite outcome list (`full-before.txt`), using the E-12 command;
  - `aw check --agent` output (`check-before.jsonl`);
  - the F-01 `rg` count over `tests/` (`legacy-before.txt`);
  - the E-09 helper count (`helpers-before.txt`);
  - the golden bytes of `support.ready_plan_text(**kwargs)` for every distinct argument set its call sites use at HEAD, plus the default call. They go in `tests/fixtures/record_builder/ready_plan_text_golden.json`, a tracked generated file whose generating command E-02 writes in its module docstring.
  - Depends on: none
  - Split addition (2026-11-07): because `.aw/state/` is gitignored and does not travel between lane worktrees, also paste into this plan, as table F-10, the first line of `core-before.txt` with its wall time, the `legacy-before.txt` count, the `helpers-before.txt` count, the line count of `full-before.txt` and of `check-before.jsonl`, and the commit id at which all of them were taken; `59aiyh` E-11 and E-12 compare against F-10, and regenerate `full-before.txt` and `check-before.jsonl` at that commit (in a temporary `git worktree add` under `.aw/state/59aiyh/`) when they run in a different worktree.
  - Expected outcome: all six files exist with modification times earlier than the first edit to `tests/support.py` or `tests/record_builder.py`; F-10 is written.
  - Execution state: pending
- [ ] E-01 Create `tests/record_builder.py` with one `RecordBuilder(repo_root)` and one method per type: `plan(...)`, `spec(...)`, `backlog(...)`, `research(...)`, `release(...)`, `prompt(...)`, `walkthrough(...)` and `review(subject, rounds=...)`. Each method takes registry field names (`status`, `set`, `order`, `plan_role`, `item_dependencies`, `blocks_release`, `from_backlog`, `readiness`, `approval`, `gate_kind`, `gate_ref`, `short_description`, ...), `history=[...]` events, `body=` prose (and, for plans, `open_questions=`), `disposition=` (a non-default lifecycle directory) and `raw_fields={legacy_name: text}` (inserted verbatim into the metadata block after the validated write and never validated; ONLY for tests whose input is deliberately invalid, F-08). Each method returns the created `Path`. Rules:
  - VALIDATION. Every field name and value outside `raw_fields` is validated through the `artifact_meta` registry (`artifact_meta.registry_fields`, `artifact_meta.validate_new_events`), so a misspelled field fails the test at build time.
  - WRITING (phase B). The builder writes through `artifact_meta`, as spec `4sd62s` section 7 step 6 requires: the file form calls `artifact_meta.create` (whose phase-B branch renders through `write_legacy`, `xexn45` E-01) and `artifact_meta.append` for `history=` events, with the fixture repository as the project that `artifact_meta` resolves (the fixture repository carries `.aw/`, without which `project_context` finds no project). The text form calls `artifact_meta.render_legacy_text(text, events)` (`xexn45` E-11). The builder has NO renderer of its own, so the cutover changes the format by changing `artifact_meta` and `RECORD_FORMAT`, never by editing a second copy of the format in the tests. Plans start from `ipd_authoring.build_skeleton`, as `support.ready_plan_text` does today; other types start from the minimal heading and body that today's creating command emits. Review records have no `artifact_meta` writer in phase B (no CLI writes them; `xexn45` defers the review-recording command), so `review(...)` renders through `review_findings.render_review` and writes with `review_findings.write_review`.
  - PLACEMENT. The file goes at `artifact_naming.build_clustered_name` under the type's records directory and default disposition: `pending/` for a plan, `artifact_types.TYPE_BACKENDS` for the other types.
  - DETERMINISM. `when=` defaults to the fixed day `2026-08-24` (the `support.ready_plan_text` default) and is never read from the clock, so built bytes are reproducible.
  - TEXT FORM. `text_only=True` returns the string without writing, for tests that pass text (`ipd_lint.lint_text`, merge-stage helpers).
  - SWITCH. One module-level constant, `RECORD_FORMAT`, names the format: `"legacy"` now; Order 13 adds `"log"`.
  - SUPERSESSION. `support.ready_plan_text` becomes a thin call into `plan(..., text_only=True)` with the same signature and the same bytes.
  - Depends on: E-13
  - Expected outcome: `RecordBuilder(tmp).plan(status="approved", set="demo", order=1)` writes a plan that `aw ipd lint` and `artifact_meta.read` accept; `plan(stauts="approved")` raises naming `stauts`; `plan(raw_fields={"Status": "EXECUTED"})` writes the literal line.
  - Execution state: pending
- [ ] E-02 Add `tests/test_record_builder.py` (core). Tests:
  - (a) ROUND TRIP. For each of the eight types, a built record round-trips through `artifact_meta.read` with every field equal to the builder input.
  - (b) LINT. A built plan with `support.ready_plan_text`'s defaults lints `conforming` at the `pre-execution` checkpoint.
  - (c) VISIBILITY. One fixture repository holds one record of each type. ONE call each of `aw find`, `aw attention --format json` and `aw check all --agent` sees every built record.
  - (d) GOLDEN. `support.ready_plan_text` reproduces the E-13 golden bytes for every captured argument set (30 call expressions at review).
  - (e) PARITY. For plan, spec, backlog, research, release and prompt, the builder's file and the file the production creating command writes (`aw ipd scaffold`, `aw specs new`, `aw backlog new`, `aw research new`, `aw releases new`, `aw prompts new`, each with `--apply`) for the same fields give equal `artifact_meta.read` states, so a builder record is a record the toolkit itself would write. Review is excluded because no CLI creates review records; its rounds are checked by (a) through `review_findings.parse_review_text`.
  - (f) REFUSALS. An unknown field, an illegal status for the type and a `short_description` over 300 characters each raise.
  - Depends on: E-01
  - Expected outcome: every test passes; the module's total wall time under `-n 0` stays under 10 s, because (c) and (e) start CLI subprocesses (if it exceeds 10 s, (c) and (e) move to a separate module listed in `tests/slow_allowlist.txt` and the core module keeps (a), (b), (d) and (f)) (measured at review: about 0.4 s for `aw find`, 2.4 s for `aw attention --format json` and 0.9 s for `aw check all --agent` in an empty fixture repository).
  - Execution state: pending
### Task group 2: tracked fixtures and finish

- [ ] E-10 Convert the tracked `.md` fixtures that tests copy into a repository or lint as records. Re-derive the list with `git ls-files tests/fixtures tests/benchmark_fixtures | grep '\.md$' | xargs grep -l -E '^- (Id|Status):'` (26 at review: `tests/fixtures/attnview/specs-valid` 9, `tests/fixtures/attnview/violations` 7, `tests/fixtures/review-pilot/plans` 9, `tests/fixtures/conforming-orchestrator.md` 1). Rules:
  - A fixture that a test copies or lints is replaced by a builder recipe in the consuming test. The consumers are `test_attention.py`, `test_attention_stem.py`, `test_attention_contract.py`, `test_specs_verbs.py`, `test_specs_releases_unsafe_field.py` (attnview), and `test_ipd_lint.py` and `test_ipd_schema.py` through `support.CONFORMING_ORCHESTRATOR`. Because the orchestrator fixture is a `Path` used by name, `support.CONFORMING_ORCHESTRATOR` becomes a builder-generated file written once per test session under a temporary directory, so its consumers stay unchanged.
  - A fixture whose purpose is malformed legacy input (the `violations` set) stays literal and is listed.
  - `tests/fixtures/review-pilot/plans/` stays literal and is listed. `tools/review_pilot.py` reads it by `manifest.json` filename as a frozen corpus of real plans whose `defects.json` entries quote exact text, so its tracked files must exist and must not change. Order 13 decides its fate with the migrated corpus.
  - Depends on: E-02
  - Expected outcome: the consuming modules' before/after `diff` is empty; the converted and kept fixture lists, each with its reason, are pasted.
  - Execution state: pending
- [ ] E-14 Finish this part: run `python3 -m pytest -o addopts="" -n 0 -v tests/test_record_builder.py`, the consuming modules named in E-10, and the bare core gate `python3 -m pytest`, and commit through `aw commit 9rgn2w -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (New finishing item for this part; the original's full-suite comparison stays in `59aiyh` E-12.)
  - Depends on: E-10
  - Expected outcome: all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
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

Measured 2026-11-07 at `ac76110f4` (the split measurement); F-04, F-05 and F-09 copied from `59aiyh` (measured at review).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -c --glob '*.py' -e '- (Id\|Status\|Set\|Kind\|Blocks-Release\|Readiness\|Item-Dependencies\|Scope-Paths\|From-Backlog\|From-Spec\|Work-Kind\|Priority\|Order\|Date\|Gate-Kind\|Gate-Ref\|Approval\|Subject-Id\|Verdict\|Graduated-To):\|## Workflow history' tests` lists 323 files with 6,820 lines (318 batch files after the 5 EXCLUDED `tests/test_artifact_meta_*.py` files) | Batch input for Orders 38 to 40 and `59aiyh` E-09. |
| F-04 | 92 matches of the E-09 helper pattern in 62 modules at `ac76110f4` (89 at review); `support.ready_plan_text` has 30 calls in 15 modules | E-13 captures the helper count; E-02 (d) covers every captured `ready_plan_text` argument set. |
| F-05 | 26 tracked `.md` fixtures carry `^- (Id\|Status):` (`fixtures/attnview/specs-valid` 9, `fixtures/attnview/violations` 7, `fixtures/review-pilot/plans` 9, `fixtures/conforming-orchestrator.md` 1; unchanged at `ac76110f4`); 8 test modules contain `aw-prompt` (7 at review); 60 `ipd_lint.lint_text(` calls in 11 test modules | The builder needs a text form and a prompt form; the review-pilot corpus stays literal (E-10). |
| F-09 | At review, in an empty installed fixture repository: `aw find plans` 0.47 s, `aw attention --format json` 2.4 s, `aw check all --agent` 0.9 s; `aw install` into a fresh repository 4.6 s | E-02's bound is 10 s with a stated fallback. |
| F-10 | (written by E-13) baseline summary for later parts | Read by `59aiyh` E-11 and E-12. |

## Proposed changes (ordered, validatable)

1. Capture the baselines, then build and test the shared builder (E-13, E-01, E-02).
2. Convert the tracked `.md` fixtures, run, commit (E-10, E-14).

## Deferred / out of scope (with reason)

- The test-module batches G1 to G6 and the first half of G7.
  - Carrier: x05v02
- The switch-point proof, the F-06 census, the second half of G7 with the shared helpers, and the full-suite comparison.
  - Carrier: 59aiyh
- The review-pilot corpus stays literal legacy input.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. No production module changes. The seven consuming test modules change only in how they obtain the converted fixtures.
- Under-scope: none known. Size: 5 E-items in 2 task groups, 13 Scope-Paths (two are fixture directories); per-item units: E-13 6 baselines, E-01 1 module with 8 methods, E-02 6 test groups, E-10 26 fixtures and 7 consuming modules (17 converted, 9 kept literal), E-14 1 run.

## Required tests / validation

New core test module: `tests/test_record_builder.py`. CONTRIBUTES to AC-1b (owned by `cxxmyv`) by supplying the single switch point. Commands: `tests/test_record_builder.py`, the E-10 consuming modules, the bare core gate `python3 -m pytest`.

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

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c` output that builds one record of each of the eight types in a temporary fixture repository with `RecordBuilder` and prints, for each, the created path and the `artifact_meta.read(<id6>)` status, set and order; `aw ipd lint <built plan>` ending in `conforming`; the exception message raised for `plan(stauts="approved")`, naming `stauts`; the bytes of the line written by `plan(raw_fields={"Status": "EXECUTED"})`; and `rg -n "def |import" tests/record_builder.py` output showing that the module imports `artifact_meta` for writing and defines no metadata renderer of its own (the verbatim `raw_fields=` line insertion is the one permitted text edit).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_record_builder.py` with every test PASSED: one round-trip test per type, the lint test, the `aw find`/`aw attention`/`aw check` visibility test, the golden test over every argument set in `tests/fixtures/record_builder/ready_plan_text_golden.json`, the six-type parity test, and the three refusal tests. Paste the total duration (under 10 s, or the moved module named in `tests/slow_allowlist.txt` with its own PASSED run).
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste `git ls-files tests/fixtures tests/benchmark_fixtures | grep '\.md$' | xargs grep -l -E '^- (Id|Status):'` before and after; the converted and kept lists, each path with its reason (the `violations` set and `review-pilot/plans` kept); `git status --short tests/fixtures/review-pilot` printing nothing; and the empty `diff` of the before/after outcome lists of every consuming module named in E-10.
  - Observed evidence:
  - Result: pending
- [ ] V-13 validates E-13
  - Required evidence: paste `ls -l --time-style=full-iso .aw/state/59aiyh/ tests/fixtures/record_builder/ready_plan_text_golden.json` and `git log --reverse --format='%H %ci %s' -- tests/record_builder.py | head -1` (the commit that adds the module, which does not exist at review), showing every baseline file older than that commit; the first line of `core-before.txt`; the line count of `full-before.txt`; the number of argument sets in the golden file; and the F-10 table.
  - Observed evidence:
  - Result: pending
- [ ] V-14 validates E-14
  - Required evidence: paste the `tests/test_record_builder.py` run with every test PASSED, the bare `python3 -m pytest` summary line and wall time beside F-10's `core-before.txt` line, and every `aw commit 9rgn2w` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `g5hpbb`, `tve77h` and `xexn45` are executed. OQ-01 is resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if the builder cannot be written without a production change, stop and report the missing capability.

Honesty rule: run `tests/test_record_builder.py`, the consuming modules and the bare `python3 -m pytest` core gate, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 9rgn2w -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
