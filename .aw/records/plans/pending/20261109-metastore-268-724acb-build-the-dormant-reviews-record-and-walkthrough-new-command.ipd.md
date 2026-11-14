# IPD: Build the dormant reviews record and walkthrough new commands

- Date: 2026-11-09
- Kind: child
- Concern: `clors0` E-06 built two commands that `90iqr1` documents, `aw reviews record` and `aw walkthrough new`. They refuse while `metadata_schema` is below 2, so they are dormant on `main` (C10a). Round-3 split (research `nj8zdp`): one item per command plus the declarations.
- Scope: `clors0` E-06, split: `aw reviews record`; `aw walkthrough new`; the two `command_surface` leaves and the `aw reviews` namespace text. `aw meta repair` is NOT here (`ffceq0` E-11).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/reviews.py, agent_workflows/set_records.py, agent_workflows/command_surface.py, tests/test_reviews_record_walkthrough_new.py, tests/test_command_surface_declarations.py, .aw/records/plans/pending/20261109-metastore-268-724acb-build-the-dormant-reviews-record-and-walkthrough-new-command.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15, executed:xexn45, executed:ya4ee4
- Status: reviewed
- Readiness: go-pending-approval
- Review-Depth: complex
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 268
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 724acb

> Written to .aw/system/workflows/technical-writing/technical-writing.md. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.

## Workflow history

- 2026-11-14 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 FIXED
- 2026-11-14 /plan-review (antigravity/gemini): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 FIXED; review record .aw/records/reviews/20261109-metastore-268-724acb-build-the-dormant-reviews-record-and-walkthrough-new-command.review.md
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from clors0 (round 3, research nj8zdp guidance).

## Goal

Both commands exist with the arguments the documentation patch describes, work on a migrated fixture, and refuse on an unmigrated one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

DORMANCY RULE, applied to every item of this plan (added at the split so the move keeps C10a): the new behavior is reached ONLY for a record whose storage format is `log` (`artifact_meta._storage_format`), for a staged `meta/*.jsonl` path, or when the resolved `metadata_schema` stamp is 2 or more. On `main` before the cutover none of these holds, so every existing command, rule and hook produces the same output as before. Each item proves both halves: its new behavior on a log-format fixture (a `tmp_path` repository whose records have `meta/<id6>.jsonl` logs and whose `project.json` carries `metadata_schema: 2`, built as `tve77h`'s synthetic-log tests and `dcerjg`'s migrated fixtures build them), and its absence on a legacy-format fixture.

### Task group 1: work

- [ ] E-01 Before the first edit, save the dormancy baseline: run `mkdir -p .aw/state/724acb/before/ && aw check all --agent` and `aw check all --all --agent` on this repository and store each rule multiset under `.aw/state/724acb/before/` (this is this plan's share of `clors0` E-20's baseline).
  - Depends on: none
  - Expected outcome: two baseline files exist under `.aw/state/724acb/before/`.
  - Execution state: pending

- [ ] E-02 (part of `clors0` E-06.) Build `aw reviews record`: a parser and handler in `agent_workflows/cli.py` calling a new function in `agent_workflows/reviews.py` that appends one `review` event per spec 4.1a, with `review_kind`, `verdict`, optional `readiness` and `review_depth`; it refuses `readiness` on a refinement event and any verdict outside the vocabulary of its kind. (Dormancy: while `metadata_schema` is below 2 it exits nonzero with a message naming `aw migrate metadata` and writes nothing.) Add its cases to `tests/test_reviews_record_walkthrough_new.py`.
  - Depends on: E-01
  - Expected outcome: on a migrated fixture one `review` event is appended; the two refusals fire; on an unmigrated fixture the command refuses and writes nothing.
  - Execution state: pending

- [ ] E-03 (part of `clors0` E-06.) Build `aw walkthrough new`: a parser and handler in `agent_workflows/cli.py` that creates a walkthrough with its log over `set_records.write_walkthrough`, with the same dormancy refusal. Add its cases to `tests/test_reviews_record_walkthrough_new.py`.
  - Depends on: E-01
  - Expected outcome: on a migrated fixture a walkthrough and its log are created; on an unmigrated fixture the command refuses and writes nothing.
  - Execution state: pending

- [ ] E-04 (part of `clors0` E-06.) Declare both leaves in `agent_workflows/command_surface.py` as mutations and change the `aw reviews` namespace description, which today says the namespace "is read-only and writes nothing", to say the two commands are available after the migration.
  - Depends on: E-02, E-03
  - Expected outcome: `tests/test_command_surface_declarations.py` reports no undeclared leaf; `aw reviews --help` shows the new text.
  - Execution state: pending

- [ ] E-05 Finish this part (its share of `clors0` E-20): run `tests/test_reviews_record_walkthrough_new.py` and `tests/test_command_surface_declarations.py`, the bare core gate `python3 -m pytest`, `aw check all --agent` and `aw check all --all --agent` (rule multisets must equal the E-01 baseline: dormancy on `main`), and `aw sanitize --agent`; commit through `aw commit 724acb -- <paths>` with only Scope-Paths files; never push.
  - Depends on: E-04
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
| F-01 | `aw reviews --help` (per `cxxmyv` F-06) | The namespace says it "is read-only and writes nothing"; E-04 changes it. |

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["E-01: Save dormancy baseline to .aw/state/724acb/before/"] --> E02["E-02: Build aw reviews record command"]
    E01 --> E03["E-03: Build aw walkthrough new command"]
    E02 --> E04["E-04: Command surface declarations and namespace help update"]
    E03 --> E04
    E04 --> E05["E-05: Dormancy verification and commit"]
```

1. E-01: baseline.
2. E-02, E-03: one command each; E-04 declarations.
3. E-05: dormancy check, commit.

## Deferred / out of scope (with reason)

- Gates, readers, overrides, rename events, extra-path mechanism and the final whole-family dormancy check.
  - Carrier: clors0

## Scope check

- Over-scope: none.
- Under-scope: none. `clors0` E-06 maps to E-02, E-03 and E-04.

## Required tests / validation

New behavioral module `tests/test_reviews_record_walkthrough_new.py`; `tests/test_command_surface_declarations.py`; the dormancy multiset diff.

## Spec / documentation sync

No spec change.

## Open questions

### OQ-01: Why does this plan not depend on `90iqr1` like `cxxmyv` does?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `90iqr1` writes a documentation patch whose hunks include `agent_workflows/cli.py` help strings and guards it with a core test that the patch still applies to HEAD. This plan edits `cli.py` (E-06, E-14); running it AFTER the patch exists would make the patch stop applying and fail the core gate at this plan's merge. So this plan omits the `90iqr1` edge, and `9o83cr` (which `90iqr1` depends on) carries `executed:clors0`, which orders this plan before the patch is generated. Every other `cxxmyv` dependency is kept, plus `ffceq0`, `t4gl15` and `xexn45`, whose code these items extend. Recommendation strength: strong.

### OQ-02: Should the two new commands work on an unmigrated repository?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Before the cutover a `review` event or a walkthrough created through these commands would be written through the legacy branch, which has no rendering for a structured review event and would put a second spelling of review metadata on `main`; refusing until `metadata_schema` is 2 keeps one format (C10a) and matches spec 5.3, which makes commands refuse an unmigrated repository after the cutover anyway. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/724acb/before/` and the rule-count line of each saved multiset.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw reviews record --help` and the `tests/test_reviews_record_walkthrough_new.py -k reviews_record` run with one PASSED node id each for the append, the refinement `readiness` refusal, the off-vocabulary verdict refusal and the unmigrated refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw walkthrough new --help` and the `tests/test_reviews_record_walkthrough_new.py -k walkthrough` run with one PASSED node id each for creation and the unmigrated refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new `aw reviews --help` namespace text and the `tests/test_command_surface_declarations.py` result line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste one result line per named test module (`tests/test_reviews_record_walkthrough_new.py` and `tests/test_command_surface_declarations.py`), the two `aw check all` multiset diffs against `.aw/state/724acb/before/` (empty), the bare core gate summary line beside them, `aw sanitize --agent` with zero `fail`, and `git show --stat` of every `aw commit 724acb` commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Safety rule: uncommitted changes and untracked files you did not create are not yours; never revert, stage, commit, discard, reformat, or "clean up" another party's work.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Honesty rule: paste the ACTUAL output; never claim a result you did not run.

Commits: only through `aw commit 724acb -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize 724acb` (never a hand git mv), after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When aw oc run or aw agy run executes the plan, the runner performs the finalize; a hand executor runs aw ipd finalize 724acb itself.
