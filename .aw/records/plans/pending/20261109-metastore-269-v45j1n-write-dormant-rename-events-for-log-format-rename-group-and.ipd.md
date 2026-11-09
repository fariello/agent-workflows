# IPD: Write dormant rename events for log-format rename, group and archive

- Date: 2026-11-09
- Kind: child
- Concern: `clors0` E-18 (the log-format half of `cxxmyv` E-04) writes `rename` events for three verbs when the target has a log; dormant on `main`, where no record has a log (C10a). Round-3 split (research `nj8zdp`): one item per call site.
- Scope: `clors0` E-18, split by call site: `artifact_rename.run_rename_generic`, `artifact_rename.run_group_generic`, `plans_archive.apply_shard_moves`, each with its case in `tests/test_log_rename_events.py`. Retiring the ledger and sidecar writer is NOT here (`g45vyv`).
- Scope-Paths: agent_workflows/artifact_rename.py, agent_workflows/plans_archive.py, tests/test_log_rename_events.py, .aw/records/plans/pending/20261109-metastore-269-v45j1n-write-dormant-rename-events-for-log-format-rename-group-and.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15, executed:xexn45, executed:ya4ee4
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 269
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: v45j1n

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from clors0 (round 3, research nj8zdp guidance).

## Goal

On log-format records, rename, group and archive each append one `rename` event with the old and new path; legacy behavior is unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

DORMANCY RULE, applied to every item of this plan (added at the split so the move keeps C10a): the new behavior is reached ONLY for a record whose storage format is `log` (`artifact_meta._storage_format`), for a staged `meta/*.jsonl` path, or when the resolved `metadata_schema` stamp is 2 or more. On `main` before the cutover none of these holds, so every existing command, rule and hook produces the same output as before. Each item proves both halves: its new behavior on a log-format fixture (a `tmp_path` repository whose records have `meta/<id6>.jsonl` logs and whose `project.json` carries `metadata_schema: 2`, built as `tve77h`'s synthetic-log tests and `dcerjg`'s migrated fixtures build them), and its absence on a legacy-format fixture.

### Task group 1: work

- [ ] E-01 Before the first edit, save the dormancy baseline: run `aw check all --agent` and `aw check all --all --agent` on this repository and store each rule multiset under `.aw/state/v45j1n/before/` (this is this plan's share of `clors0` E-20's baseline).
  - Depends on: none
  - Expected outcome: two baseline files exist under `.aw/state/v45j1n/before/`.
  - Execution state: pending

- [ ] E-02 (part of `clors0` E-18.) In `artifact_rename.run_rename_generic`, when the target record has a log, append a `rename` event (verb `rename`) carrying the old and new path through `artifact_meta.append`; a legacy-format target keeps today's behavior, including the rename-ledger write through `record_history.record_rename`. Add the `rename` case and the legacy case to `tests/test_log_rename_events.py`.
  - Depends on: E-01
  - Expected outcome: on a log-format fixture a rename appends one `rename` event and `aw show <id6> --history` lists the old path then the new one; on a legacy-format fixture the file bytes and the ledger line are unchanged.
  - Execution state: pending

- [ ] E-03 (part of `clors0` E-18.) In `artifact_rename.run_group_generic`, the same for verb `group`, with its case in `tests/test_log_rename_events.py`.
  - Depends on: E-01
  - Expected outcome: on a log-format fixture a group appends one `rename` event with verb `group`.
  - Execution state: pending

- [ ] E-04 (part of `clors0` E-18.) In `plans_archive.apply_shard_moves`, the same for verb `archive`, with its case in `tests/test_log_rename_events.py`.
  - Depends on: E-01
  - Expected outcome: on a log-format fixture an archive appends one `rename` event with verb `archive`.
  - Execution state: pending

- [ ] E-05 Finish this part (its share of `clors0` E-20): run `tests/test_log_rename_events.py`, the bare core gate `python3 -m pytest`, `aw check all --agent` and `aw check all --all --agent` (rule multisets must equal the E-01 baseline: dormancy on `main`), and `aw sanitize --agent`; commit through `aw commit v45j1n -- <paths>` with only Scope-Paths files; never push.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the named modules pass; both `aw check all` multisets are unchanged; every commit's `git show --stat` lists only Scope-Paths files.
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
| F-01 | `clors0` E-18 measurement | 3 call sites, 1 event shape, 1 test module: about 8 units, now one call site per item. |

## Proposed changes (ordered, validatable)

1. E-01: baseline.
2. E-02 to E-04: one call site each.
3. E-05: dormancy check, commit.

## Deferred / out of scope (with reason)

- Gates, readers, overrides, commands, extra-path mechanism and the final whole-family dormancy check.
  - Carrier: clors0
- Retiring the rename ledger and the sidecar writer.
  - Carrier: g45vyv

## Scope check

- Over-scope: none.
- Under-scope: none. `clors0` E-18 maps to E-02, E-03 and E-04.

## Required tests / validation

New behavioral module `tests/test_log_rename_events.py`; the dormancy multiset diff.

## Spec / documentation sync

No spec change.

## Open questions

### OQ-01: Why does this plan not depend on `90iqr1` like `cxxmyv` does?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `90iqr1` writes a documentation patch whose hunks include `agent_workflows/cli.py` help strings and guards it with a core test that the patch still applies to HEAD. This plan edits `cli.py` (E-06, E-14); running it AFTER the patch exists would make the patch stop applying and fail the core gate at this plan's merge. So this plan omits the `90iqr1` edge, and `9o83cr` (which `90iqr1` depends on) carries `executed:clors0`, which orders this plan before the patch is generated. Every other `cxxmyv` dependency is kept, plus `ffceq0`, `t4gl15` and `xexn45`, whose code these items extend. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/v45j1n/before/` and the rule-count line of each saved multiset.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `tests/test_log_rename_events.py -k rename` run with the `rename` and legacy cases PASSED, and the `aw show <id6> --history` output of the fixture showing the old then the new path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `tests/test_log_rename_events.py -k group` run with its PASSED node id and the event line it asserts.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `tests/test_log_rename_events.py -k archive` run with its PASSED node id and the event line it asserts.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste one result line per named test module (`tests/test_log_rename_events.py`), the two `aw check all` multiset diffs against `.aw/state/v45j1n/before/` (empty), the bare core gate summary line beside them, `aw sanitize --agent` with zero `fail`, and `git show --stat` of every `aw commit v45j1n` commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL output; never claim a result you did not run. Commits: only through `aw commit v45j1n -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
