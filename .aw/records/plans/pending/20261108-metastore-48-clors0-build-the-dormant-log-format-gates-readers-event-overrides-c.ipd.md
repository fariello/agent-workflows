# IPD: Build the dormant log-format gates, readers, event overrides, commands and option aliases for the cutover

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` 5.2 makes the cutover ONE attended commit (`cxxmyv`, Order 13), and C10a requires `main` to read and write exactly one on-disk format at every commit. `cxxmyv` carried, inside that one attended turn, several pieces of code whose behavior only matters once logs exist: the post-cutover gates (E-05), the post-cutover readers (E-15), the event `overrides` list and the `--date` refusal (E-14), two new commands (E-06), path-bearing `rename` events (half of E-04) and the mechanism that lets the migration's one commit carry the code changes (the open question inside E-17). Each can be built and tested now WITHOUT changing `main`'s format, because `artifact_meta` already dispatches by storage format (`artifact_meta._storage_format` returns `log` only when `meta/<id6>.jsonl` exists, and no record on `main` has one until the migration) and the metadata stamp (`metadata_schema`) stays below 2 until the migration writes it. Moving them out shrinks the attended turn and lets each be reviewed and merged on its own. Split from `cxxmyv` 2026-11-07.
- Scope: `cxxmyv` E-05, E-06, E-14 and E-15, carried with their ids, each restricted to log-format records or to `metadata_schema` 2 so it is DORMANT on `main` until the cutover; E-18, the log-format half of `cxxmyv` E-04 (path-bearing and `rename` events for `aw rename`, `aw group` and `aw archive plans` when the target has a log); E-19, the one-commit mechanism of `cxxmyv` E-17 (an explicit extra-path list for `m0001`'s commit step, with the spec 5.2 step 7 amendment); and a finishing item E-20. EXCLUDES: the format switch (`cxxmyv` E-03), retiring the sidecar writer, the rename ledger, the INDEX ignore lines and skip names (`cxxmyv` E-04), the builder switch (`cxxmyv` E-07), the documentation patch (`cxxmyv` E-08), the `Kind` option renames (`cxxmyv` E-16), the rehearsal, the real migration and every real-repository demonstration (`cxxmyv` E-01, E-02, E-09 to E-13, E-17).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/check_engine.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/meta_log_append_gate.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/meta_cli.py, agent_workflows/reviews.py, agent_workflows/set_records.py, agent_workflows/artifact_rename.py, agent_workflows/plans_archive.py, agent_workflows/migrations/m0001_metadata_v2.py, .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, tests/test_cutover_log_gates.py, tests/test_cutover_log_readers.py, tests/test_event_overrides.py, tests/test_reviews_record_walkthrough_new.py, tests/test_log_rename_events.py, tests/test_m0001_extra_paths.py, tests/test_command_surface_declarations.py, .aw/records/plans/pending/20261108-metastore-48-clors0-build-the-dormant-log-format-gates-readers-event-overrides-c.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15, executed:xexn45, executed:ya4ee4
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 48
- Highest E allocated: 20
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: clors0

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from cxxmyv per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

Every piece of post-cutover behavior that does not itself change the on-disk format is built, tested on log-format fixtures and merged before the cutover, while `main` behaves byte-for-byte as before; the attended cutover then only flips the format and runs the migration.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

DORMANCY RULE, applied to every item of this plan (added at the split so the move keeps C10a): the new behavior is reached ONLY for a record whose storage format is `log` (`artifact_meta._storage_format`), for a staged `meta/*.jsonl` path, or when the resolved `metadata_schema` stamp is 2 or more. On `main` before the cutover none of these holds, so every existing command, rule and hook produces the same output as before. Each item proves both halves: its new behavior on a log-format fixture (a `tmp_path` repository whose records have `meta/<id6>.jsonl` logs and whose `project.json` carries `metadata_schema: 2`, built as `tve77h`'s synthetic-log tests and `dcerjg`'s migrated fixtures build them), and its absence on a legacy-format fixture. Item ids E-05, E-06, E-14 and E-15 are the ids these items had in `cxxmyv`; E-18 and E-19 are the moved halves of `cxxmyv` E-04 and E-17; E-20 is new.

### Task group 1: dormant post-cutover code

- [ ] E-05 Put the gates in their post-cutover form: "mirrored status differs from replayed state" and "staged log violates append rules" in `check_engine` and the hooks; the executed transition accepted only as a finalize append or an orchestrator rollup-retirement append (`t4gl15`, AC-16 case 2); and the terminal-log rules of the `meta/*.jsonl` append-only hook, accepting only the appends that spec OQ-30 allows (`9o83cr`). The `->reviewed` gate-only rule (SR-601) is NOT here: `2xwb9b` E-12 implements it over `artifact_meta.query`, which serves log-format review rows unchanged. (Dormancy: each rule applies only to a record with a log or to a staged `meta/*.jsonl`; a legacy-format executed transition keeps today's rule.) New test module `tests/test_cutover_log_gates.py`. Measured units: 2 `check_engine` rules, 1 `executed_transition_gate` branch, the OQ-30 accepted-append list (about 8 cases) in `hooks/meta_log_append_gate` (added by `t4gl15` E-05), 1 test module: about 18.
  - Depends on: none
  - Expected outcome: each gate refuses its post-cutover violation in a fixture and accepts the allowed appends; on a legacy-format fixture each gate's verdict is unchanged.
  - Execution state: pending

- [ ] E-15 Put the readers in their post-cutover form (`ffceq0` Deferred row): `last_history_at` comes from the newest post-cutover event `at` with `last_history_precision` (spec 4.4), and `aw check meta` gains the logged-path drift row (spec 4.6). (Dormancy: both apply only to log-format records.) New test module `tests/test_cutover_log_readers.py`. Measured units: 1 reader branch in `artifact_meta`, 1 `aw check meta` row in `meta_cli`, 1 test module: about 6.
  - Depends on: none
  - Expected outcome: on a log-format fixture, `last_history_at` equals the newest event's `at` with its precision; `aw check meta` reports a planted `path-drift` and reports nothing on the unplanted fixture; on a legacy-format fixture both are unchanged.
  - Execution state: pending

- [ ] E-14 Implement `4sd62s` OQ-01 as spec 4.2 states it (verified at review: spec 4.2 `overrides` bullet): every event a setter writes with `--allow-open-questions`, `--allow-terminal-reopen` or `--allow-unresolvable-release-sentinel` carries an `overrides` list naming each flag given (for example `["allow-open-questions"]`), absent when none was given; `aw specs set --date` exits nonzero with a message that names the `--message` alternative once `metadata_schema` is 2. Add behavioral tests on a migrated (log-format) fixture. (Dormancy: on a legacy-format record the phase-B legacy writer keeps rendering the flags as today's history-line actor suffix, `artifact_meta.LegacyRender`, so the bytes `main` writes do not change; `--date` keeps working while `metadata_schema` is below 2.) New test module `tests/test_event_overrides.py`. Measured units: the three flags reach `status_set` (7 references) and `plan_readiness`/`cli` (14), of which the event-building call sites are about 4; 1 `--date` branch; 1 test module: about 10.
  - Depends on: none
  - Expected outcome: a setter run with an override flag writes `overrides` on its event; a run without one writes no `overrides` key; `aw specs set --date` refuses on a migrated fixture and leaves the fixture byte-identical; on a legacy-format fixture both setter runs write the same bytes as before.
  - Execution state: pending

- [ ] E-06 Build the two commands documented by `90iqr1`: `aw reviews record` (appends one `review` event per spec 4.1a, with `review_kind`, `verdict`, optional `readiness` and `review_depth`; refuses `readiness` on a refinement event and any verdict outside the vocabulary of its kind) and `aw walkthrough new` (creates a walkthrough with its log over `set_records.write_walkthrough`). Declare both leaves in `command_surface` as mutations and change the `aw reviews` namespace description, which today says the namespace "is read-only and writes nothing". `aw meta repair` is NOT built here: `ffceq0` E-11 builds it. (Dormancy: while `metadata_schema` is below 2 both commands exit nonzero with a message naming `aw migrate metadata` and write nothing, so no log is created on `main` before the cutover; the namespace description says the two commands are available after the migration.) New test module `tests/test_reviews_record_walkthrough_new.py`. Measured units: 2 parsers and handlers in `cli`, 2 `command_surface` leaves, 1 namespace string, 1 `reviews` function, 1 `set_records` call, 1 test module: about 10.
  - Depends on: none
  - Expected outcome: `--help` of each command shows the arguments the `90iqr1` patch documents; behavioral tests pass on a migrated fixture; on an unmigrated fixture each command refuses and writes nothing; `tests/test_command_surface_declarations.py` reports no undeclared leaf.
  - Execution state: pending

- [ ] E-18 (`cxxmyv` E-04, log-format half) Write path-bearing events and `rename` events for `aw rename`, `aw group` and `aw archive plans` (`xexn45`, AC-31, AC-34) when the target record has a log: `artifact_rename.run_rename_generic`, `artifact_rename.run_group_generic` and `plans_archive.apply_shard_moves` append a `rename` event (verb `rename`, `group` or `archive`) carrying the old and new path through `artifact_meta.append`. (Dormancy: a legacy-format target keeps today's behavior, including the rename-ledger write through `record_history.record_rename`; retiring the ledger and the sidecar writer stays in `cxxmyv` E-04.) New test module `tests/test_log_rename_events.py`. Measured units: 3 call sites, 1 event shape, 1 test module with one case per verb plus one legacy case: about 8.
  - Depends on: none
  - Expected outcome: on a log-format fixture a rename, a group and an archive each append one `rename` event with the old and new path, and `aw show <id6> --history` lists the old path then the new one; on a legacy-format fixture the file bytes and the ledger line are unchanged.
  - Execution state: pending

- [ ] E-19 (`cxxmyv` E-17, mechanism half) Settle how the migration's ONE commit carries code, test and documentation changes: spec 5.2 step 7 commits "the migration's own list of paths" and the step-4a marker matches only the exact staged tree (`dcerjg` E-11), so a cutover whose code switch is uncommitted needs a supported way to stage extra paths. Add one under `agent_workflows/migrations/` (for example an explicit `--include-paths <pathspec>...` argument of `aw migrate metadata --apply` that stages the named paths BEFORE the step-4a marker is written, so the marker's `git write-tree` id covers them) and amend spec 5.2 step 7 in the same change to say so, because that step is the contract the AC-16 hooks and the step-4a marker are reviewed against. New test module `tests/test_m0001_extra_paths.py`: in a `tmp_path` fixture repository with the installed hooks, an uncommitted code change plus `--apply --include-paths` produces ONE commit holding the migrated records and the extra paths, passing every installed hook without `--force` or `--no-verify`; an extra path staged AFTER the marker is refused by the hooks. (Dormancy: the argument is inert without `--apply`, and `aw migrate metadata --apply` is not run on `main` before `cxxmyv`.) Measured units: 1 argument, 1 staging step, 1 spec paragraph, 1 test module with three cases: about 7.
  - Depends on: none
  - Expected outcome: the fixture produces one commit with both kinds of path and passes every hook; the late extra path is refused; the spec 5.2 step 7 amendment is in the diff.
  - Execution state: pending

### Task group 2: finish

- [ ] E-20 Finish: run the six new test modules, `tests/test_command_surface_declarations.py`, the existing `tests/test_m0001_*.py` modules, the bare core gate `python3 -m pytest` and `make test-all` (this plan adds code paths every later phase-B merge runs through), `aw check all --agent` and `aw check all --all --agent` on this repository (rule multisets equal those before the plan's first edit, saved to `.aw/state/clors0/before/` at the start of the first item: dormancy on `main`), `aw ipd lint` on this plan and `aw sanitize --agent`; commit through `aw commit clors0 -- <paths>` with only Scope-Paths files, never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-05, E-06, E-14, E-15, E-18, E-19
  - Expected outcome: all runs pass; the two `aw check all` multisets are unchanged; every commit's `git show --stat` lists only Scope-Paths files (or paths justified at finalize).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_meta.append` dispatches on the TARGET's storage format (`artifact_meta._storage_format`): a record with `meta/<id6>.jsonl` takes the log branch (the `tve77h` path, exercised today only by synthetic-log tests), a record without one takes the phase-B legacy branch (`append_legacy`). This is what makes log-only code dormant on `main`.
- `artifact_meta` already accepts an `overrides` envelope key (`validate_event`: "overrides must be a non-empty list when present") and the legacy branch copies it (`_prepare_legacy_events`), so E-14 changes only the callers.
- `hooks/meta_log_append_gate.py` and `artifact_meta.check_staged_log_append` are added by `t4gl15` E-05 (phase-B form); E-05 here adds the terminal-log rules.
- `aw meta repair` and `aw check meta` live in `meta_cli` (`ffceq0` E-11, `1ajqaa`).
- `set_records.write_walkthrough` writes a walkthrough today; E-06 wraps it.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `cxxmyv` Concern and Scope check (2026-11-06 review): the post-cutover gates, readers, `overrides`, the two commands and the `rename` events were placed in the cutover only because they are log-format behavior. | Log-format behavior that is reached only through a log or the schema stamp is dormant on `main`, so C10a does not require it in the cutover commit. |
| F-02 | `rg -n "_storage_format" agent_workflows/artifact_meta.py`: `log` only when `<records_root>/meta/<id6>.jsonl` exists; `rg -n "records/meta" agent_workflows`: no hit at `ac76110f4`, and `rg -c "meta/" .aw/records` finds no log directory. | No record on `main` takes the log branch before the migration. |
| F-03 | `cxxmyv` review record (2026-11-06): "feasibility risk named: the one-commit mechanism is proven only by the E-17 rehearsal". | E-19 proves the mechanism on a fixture before the attended turn; `cxxmyv` E-17 then rehearses with a known mechanism instead of possibly writing one mid-cutover. |

## Proposed changes (ordered, validatable)

1. Build and test the dormant gates (E-05), readers (E-15), `overrides` and `--date` refusal (E-14), the two commands (E-06), the `rename` events (E-18) and the extra-path mechanism with its spec amendment (E-19); the six are independent.
2. Prove dormancy on `main`, validate and commit (E-20).

## Deferred / out of scope (with reason)

- The format switch, the legacy loader move into `m0001`, `CURRENT_METADATA_SCHEMA = 2`, retiring the sidecar writer, the rename ledger, the INDEX ignore lines and the skip names, the builder switch, the documentation patch, the `Kind` option renames with the `90iqr1` F-07 test updates, the rehearsal, the real migration and the real-repository demonstrations: each changes the on-disk format or needs the migrated repository, so C10a keeps them in the one cutover commit or after it.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. Every item is post-cutover behavior that `cxxmyv` already owned; the only addition is the dormancy constraint that makes the move safe.
- Under-scope: none known. Size: 7 E-items, 22 Scope-Paths entries (13 production files, 1 spec, 7 test modules, this plan); the largest item (E-05) hides about 18 units.

## Required tests / validation

New behavioral test modules, each calling the real code or CLI on `tmp_path` fixtures and asserting on outputs, exit codes and file bytes, with a log-format case and a legacy-format (dormancy) case: `tests/test_cutover_log_gates.py` (E-05), `tests/test_cutover_log_readers.py` (E-15), `tests/test_event_overrides.py` (E-14), `tests/test_reviews_record_walkthrough_new.py` (E-06), `tests/test_log_rename_events.py` (E-18), `tests/test_m0001_extra_paths.py` (E-19). Commands: bare `python3 -m pytest`, `make test-all`, `aw check all --agent`, `aw check all --all --agent`, `aw sanitize --agent`. CONTRIBUTES to AC-16 case 2, AC-31, AC-34 and AC-7 (owned, on the real repository, by `cxxmyv`).

## Spec / documentation sync

E-19 amends spec `4sd62s` 5.2 step 7 ("the migration's own list of paths") to say how the one migration commit also carries explicitly named extra paths, because that step is the contract the AC-16 hooks and the step-4a marker are reviewed against; the spec file is in `- Scope-Paths:` for that reason (this obligation moved here from `cxxmyv`'s Spec / documentation sync section). The `overrides` key and the `--date` refusal are already in spec 4.2. User documentation of the two commands is in the `90iqr1` patch, applied by `cxxmyv` E-08.

## Open questions

### OQ-01: Why does this plan not depend on `90iqr1` like `cxxmyv` does?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `90iqr1` writes a documentation patch whose hunks include `agent_workflows/cli.py` help strings and guards it with a core test that the patch still applies to HEAD. This plan edits `cli.py` (E-06, E-14); running it AFTER the patch exists would make the patch stop applying and fail the core gate at this plan's merge. So this plan omits the `90iqr1` edge, and `9o83cr` (which `90iqr1` depends on) carries `executed:clors0`, which orders this plan before the patch is generated. Every other `cxxmyv` dependency is kept, plus `ffceq0`, `t4gl15` and `xexn45`, whose code these items extend. Recommendation strength: strong.

### OQ-02: Should the two new commands work on an unmigrated repository?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Before the cutover a `review` event or a walkthrough created through these commands would be written through the legacy branch, which has no rendering for a structured review event and would put a second spelling of review metadata on `main`; refusing until `metadata_schema` is 2 keeps one format (C10a) and matches spec 5.3, which makes commands refuse an unmigrated repository after the cutover anyway. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_cutover_log_gates.py` showing a raw transition into `executed` refused, a finalize append and a rollup-retirement append accepted, a non-append log edit refused, a `set` of `readiness` on a terminal log refused, an OQ-30 terminal append accepted, a mirror that differs from the replayed state reported, and the legacy-format cases unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_cutover_log_readers.py` showing `last_history_at` and `last_history_precision` taken from the newest event, `aw check meta` output on the fixture with the planted `path-drift` and on the clean fixture, and the legacy-format cases unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_event_overrides.py` showing an event with `overrides: ["allow-open-questions"]` after a setter run with that flag, no `overrides` key after a run without one, `aw specs set --date` refused on a migrated fixture with its message and a byte-identical fixture, and the legacy-format setter bytes unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw reviews record --help` and `aw walkthrough new --help`, the new `aw reviews --help` namespace text, the pytest summary of `tests/test_reviews_record_walkthrough_new.py` including the refusal of `readiness` on a refinement event, of an off-vocabulary verdict, and of both commands on an unmigrated fixture, and the `tests/test_command_surface_declarations.py` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-18 validates E-18
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_log_rename_events.py` with one PASSED case per verb (`rename`, `group`, `archive`), the `aw show <id6> --history` output of the fixture showing the old then the new path, and the legacy case showing unchanged bytes and ledger line.
  - Observed evidence:
  - Result: pending

- [ ] V-19 validates E-19
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_extra_paths.py` with the one-commit case (its `git show --stat` listing both migrated records and the extra paths, and the hook output without `--force` or `--no-verify`) and the late-path refusal PASSED, and the `git diff` hunk of the spec 5.2 step 7 amendment.
  - Observed evidence:
  - Result: pending

- [ ] V-20 validates E-20
  - Required evidence: paste the bare `python3 -m pytest` and `make test-all` summary lines, the `aw check all --agent` and `aw check all --all --agent` rule multiset diffs against `.aw/state/clors0/before/` (empty), `aw sanitize --agent` with zero `fail`, and `git show --stat` of every `aw commit clors0` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 7 E-items and 22 Scope-Paths entries against guides of about 6 and 12. The six work items share one concern (post-cutover behavior that is dormant on `main`), share one fixture shape (a migrated `tmp_path` repository) and one dormancy proof (E-20's unchanged rule multisets), and the Order budget of this split left no further plan number. Each item hides at most about 18 units and is verified by its own test module.

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). This plan amends a spec (E-19); the runner announces the declared spec edit before the run. Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit clors0 -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
