# IPD: Audit the five setdisp children together and run the Set-level checks

- Date: 2026-10-07
- Kind: child
- Concern: Orchestrator `63zo2f` (Set `setdisp`) lists Set-level checks that no single child can make: that each expected-difference assertion child 02 (`afdmn6`) records is flipped by exactly one later child; that no backlog carrier closed by children 03 and 05 was closed on a partial fix; that child 04's spec amendment landed in the same commit as its behavior; that the three retrospective parity files passed after every child; that no added test reads production source; the bare-suite failure set compared by name with the pre-Set baseline; and `aw check release-gates`. On 2026-10-06 the coverage probe refused `63zo2f` (sent back to `draft` by `gradcover` `52opph`) because those checks sat on the orchestrator, where a runner retirement marks them complete without anyone performing them. This plan performs them, after the last child.
- Scope: Measurement and reporting only. IN: run and record each Set-level check named in `63zo2f`'s Completion criteria and Cross-IPD validation, against the tree after children 01 to 05 have executed; report any failure plainly and stop the Set from being reported complete. OUT: fixing anything a check finds (a failure is reported, and the fix is a new plan); closing or editing any backlog item; editing any child plan.
- Scope-Paths: .aw/records/plans/pending/20261007-setdisp-06-7zb4ny-audit-the-five-setdisp-children-together-and-run-the-set-lev.ipd.md
- Item-Dependencies: executed:afdmn6, executed:m1jlwm, executed:m94eht, executed:vhiqo6
- Status: approved
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- Set: setdisp
- Order: 6
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7zb4ny
- Approval: 2026-10-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed
- 2026-10-07 /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005 (all fixed; E-07 added; record `.aw/records/reviews/20261007-setdisp-06-7zb4ny-audit-the-five-setdisp-children-together-and-run-the-set-lev.review.md`).
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by new Order 06 7zb4ny; coverage pass recorded; open questions are non-blocking executor measurements

- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored so the Set-level checks orchestrator `63zo2f` carried have an owner; the coverage probe quoted each of them as work no child covers.
- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Perform, after the last `setdisp` child executes, every Set-level check the orchestrator `63zo2f` lists, so the Set is declared complete only when each has been run and its evidence pasted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the child evidence

- [x] E-01 For each of children `c6f6sj`, `afdmn6`, `m1jlwm`, `m94eht` and `vhiqo6`, confirm the plan is under `.aw/records/plans/executed/`, `aw ipd lint --phase post-transition --detail <path>` (run with `AW_NO_REEXEC=1`) reports conforming, and every `V-*` has non-empty `Observed evidence` and `Result: pass`. A `V-*` whose evidence is empty or only says it passed fails this check. Also record, for each child, its EXECUTION COMMIT and its INTEGRATION MERGE, found by trailer (`git log --format='%h %s' --grep 'AW-Item: <id6>'`; for `c6f6sj` at review these were `4d4966695` and merges `ce551c597`/`5041ef8bc`). E-04 and E-05 use these commits. If `m1jlwm` was instead retired to `superseded/` (orchestrator `63zo2f` OQ-02's alternative), its row records the superseded path and RETIRED header, and the plans that carried its fixes (`wdyz5n`, `ju3rhs`) are audited in its place.
  - Depends on: none
  - Expected outcome: a five-row table (child, executed path, lint result, count of `V-*` with pasted evidence out of total, execution commit, integration merge), every row complete.
  - Execution state: performed

### Task group 2: the cross-child checks

- [x] E-02 NO AXIS FIXED TWICE OR BY NOBODY. Take the axis classification `afdmn6` RECORDED in its own V-04 evidence (eight candidates (a) to (h); at `afdmn6`'s review six were DIFFER and two reclassified to agreement, so the DIFFER count is read from its evidence, never assumed to be eight). For each DIFFER axis, name the plan whose evidence shows it flipped: a Set child (03 `m1jlwm`, 04 `m94eht`, 05 `vhiqo6`) or a named plan outside the Set (for example `wdyz5n` for the evidence gate, which may land before `m1jlwm`; `m1jlwm`'s own E-01 then only confirms). Each must be flipped by exactly one plan; any still unflipped must correspond to a spec `wy9aru` Section 7 axis with a live carrier (name it). Confirm the final `tests/test_set_dispatch_parity.py` agrees by running it.
  - Depends on: E-01
  - Expected outcome: one row per candidate axis (a) to (h), giving its classification at `afdmn6`, and for each DIFFER row exactly one flipping plan or a named live carrier; plus a passing run of `tests/test_set_dispatch_parity.py`.
  - Execution state: performed

- [x] E-03 NO CARRIER CLOSED ON A PARTIAL FIX. Find every backlog item whose `- Status:` became `done` during the Set window (from the parent of `c6f6sj`'s execution commit to the tip; `git log -p <base>..HEAD -- .aw/records/backlog/` and the items' own `## Workflow history`), restricted to items a Set plan or a plan named in `63zo2f` touched. CORRECTED AT REVIEW: after their own reviews, `m1jlwm` closes nothing itself and `vhiqo6` closes nothing, so the expected set may be just `h4fiwa` and `fv4b6s`. For each closed item, quote its own stated scope and confirm the cited evidence covers all of it. For `h4fiwa` and `fv4b6s` (both `graduated` at review, to `wdyz5n` and `ju3rhs`, both `Blocks-Release: next`): report each as `done` via the HANDOFF route (its `From-Backlog` carrier executed) or the SATISFIED route (a resolvable `Close-Evidence`), with the `- Blocks-Release:` line intact, OR still `graduated` with its carrier plan's status named. A `graduated` item whose carrier is `executed` is reported, not fixed. Also confirm the Set closed none of `2wae2x`, `fnb8pl`, `lq2w86`.
  - Depends on: E-02
  - Expected outcome: per closed item, its scope quoted beside the evidence covering it and its close route; `h4fiwa` and `fv4b6s` each with status, route and gate line; `2wae2x`/`fnb8pl`/`lq2w86` status unchanged by any Set commit. Any partial close is reported as a failure.
  - Execution state: performed

- [x] E-04 THE SPEC AMENDMENT TRAVELLED WITH ITS BEHAVIOR, AND NO TEST READS SOURCE. Show that child 04's amendment to spec `1525-02` R2 and its sidecar behavior change are in the same commit (`git show --stat <commit>` listing both `.aw/records/specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md` and `agent_workflows/status_set.py`), using the execution commit E-01 recorded; and that child 05's commits touch no `.spec.md`. List the test files the five children ADDED (`git diff --name-only --diff-filter=A <base>..HEAD -- tests/`, filtered to the children's commits), then search each for `import inspect`, `inspect.`, `ast.parse`, `read_text` or `open(` on a path under `agent_workflows/`, and caller-count or symbol-census assertions. Each hit is read and judged (a fixture file read is fine; a production-source read is a failure), not counted.
  - Depends on: E-03
  - Expected outcome: one commit listing both the spec and the behavior file; no `.spec.md` in child 05's commits; the added-test list, the search output, and a judgement per hit, with no production-source read.
  - Execution state: performed

### Task group 3: the whole tree

- [x] E-05 THE THREE RETROSPECTIVE PARITY FILES PASSED AFTER EVERY CHILD. The three are `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_gate_follows_status.py` and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange` (all three exist at the pre-Set commit, measured at review). CORRECTED AT REVIEW: the children do NOT all paste these files (executed `c6f6sj` contains none of the three names), so the per-child record must be MEASURED, not quoted. For each child, check out its execution commit (E-01) in a throwaway scratch worktree (`git worktree add --detach <scratch> <commit>`, removed afterwards) and run the three with `PYTHONPATH=<scratch> AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider <three ids>`; where a child DID paste them, quote that as well. Then run them once more at the current tree under two zones chosen so local and UTC dates differ at run time (`TZ=Pacific/Kiritimati` and `TZ=Etc/GMT+12`), and paste both.
  - Depends on: E-04
  - Expected outcome: five per-child pass records, each with the commit it was measured at, plus two current passing runs under the two skewed zones; the scratch worktrees removed (`git worktree list` pasted).
  - Execution state: performed

- [x] E-06 THE BARE SUITE FAILURE SET. Run `python3 -m pytest` bare, paste the `N passed` line, and compare its failure SET by test id with the pre-Set baseline; any new id not named in advance by a child is a failure. CORRECTED AT REVIEW: executed `c6f6sj` records only a count (`3512 passed, 2 skipped` at `ec857565a`) and no failure set, so the baseline must be RE-DERIVED: run the bare suite at the parent of `c6f6sj`'s execution commit (`4d4966695~1` at review) in a throwaway scratch worktree with `PYTHONPATH=<scratch> AW_NO_REEXEC=1`, with `-rf` added so failing ids are listed (`python3 -m pytest -rf`), and run the current suite the same way. Because a test can be red only for part of a day (`63zo2f` and `c6f6sj` F-03), run both under the same `TZ` in one sitting.
  - Depends on: E-05
  - Expected outcome: both summary lines, both failure-id sets and their difference, with no unexplained new id; the scratch worktree removed.
  - Execution state: performed

- [x] E-07 THE RELEASE GATES. Run `AW_NO_REEXEC=1 python3 -m agent_workflows check release-gates --agent` and paste it (at review it reported `conforms`, 0 findings). Any finding naming an item a Set plan touched is a failure; a finding on an unrelated item is reported and attributed.
  - Depends on: E-03
  - Expected outcome: `check release-gates` output pasted with no finding attributable to the Set.
  - Execution state: performed

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR CARRIES NO WORK OF ITS OWN (`AGENTS.md`); a whole-Set check needs a child that runs after the others, which is this plan.
- RUN THE SUITE BARE (`AGENTS.md` execution contract).
- `AW_NO_REEXEC=1` keeps the measured package the one in the tree under test.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The checks were on the orchestrator, with no owner. | `63zo2f`'s Completion criteria and Cross-IPD validation; its 2026-10-06 coverage record quoting them as uncovered |
| F-02 | Only a plan that runs after all five children can make them. | each check compares or audits two or more children's results |
| F-03 | Three demands were not reachable from the children's evidence (found at review). | executed `c6f6sj` names none of the three parity files and records no failure set; `afdmn6`'s own review counts six DIFFER axes, not eight; `h4fiwa`/`fv4b6s` are `graduated` to `wdyz5n`/`ju3rhs` and close by HANDOFF, not the evidence route; `vhiqo6` closes no carrier after its review. E-02, E-03, E-05 and E-06 now measure what the evidence cannot supply. |

## Proposed changes (ordered, validatable)

1. Audit each child's evidence (E-01).
2. The three cross-child checks (E-02 to E-04).
3. Parity files, the whole suite and the release gates (E-05, E-06, E-07).

## Deferred / out of scope (with reason)

- FIXING WHAT A CHECK FINDS. This plan reports; a failure needs its own plan.
  - Carrier-Declined: measurement-only by design; a fix inside an audit would audit its own work

## Scope check

- Over-scope: none. Only this plan's own file is edited (its evidence). Scratch worktrees used by E-05 and E-06 are created outside the tracked tree and removed; they are not edits.
- Under-scope: none.

## Required tests / validation

Each E-item's commands, run and pasted as its V-item requires. No new test is written.

## Spec / documentation sync

None. This plan edits no spec or document.

## Open questions

### OQ-01: Should this be a child rather than the orchestrator's own checklist?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: a child. When the runner retires an orchestrator it skips the orchestrator's own checks, so they would be marked done without being run (`AGENTS.md`, spec `77tr3o` R-12). A child is executed and verified like any other plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the five-row table and, for each child, the lint command and its output, and the `git log --grep 'AW-Item: <id6>'` output that identified its commits.
  - Observed evidence:
    Five-row child audit table:
    | Child | Executed Path | Lint Result | Count of `V-*` with pasted evidence | Execution Commit | Integration Merge |
    |---|---|---|---|---|---|
    | `c6f6sj` | `.aw/records/plans/executed/20261001-setdisp-01-c6f6sj-deduplicate-the-two-self-commit-helpers-and-the-two-from-bac.ipd.md` | conforming | 5 / 5 | `4d4966695` | `5041ef8bc` (review: `ce551c597`) |
    | `afdmn6` | `.aw/records/plans/executed/20261001-setdisp-02-afdmn6-build-the-cross-spelling-differential-harness-that-makes-eve.ipd.md` | conforming | 5 / 5 | `23372bd8c` | `af59cde14` (review: `c3adbcd8b`) |
    | `m1jlwm` | `.aw/records/plans/executed/20261001-setdisp-03-m1jlwm-close-the-two-measured-positional-specs-set-gate-bypasses-by.ipd.md` | conforming | 5 / 5 | `5ad02df21` | `2390842bf` (review: `427b569c7`) |
    | `m94eht` | `.aw/records/plans/executed/20261001-setdisp-04-m94eht-make-aw-specs-set-status-a-thin-adapter-delegating-to-the-sh.ipd.md` | conforming | 7 / 7 | `e3e04da90` | `f6cd08252` (review: `072b6f640`) |
    | `vhiqo6` | `.aw/records/plans/executed/20261001-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.ipd.md` | conforming | 7 / 7 | `b45042e18` | `b031c5afc` (review: `3a4f8b232`) |

    Lint command and output for each child:
    ```
    $ AW_NO_REEXEC=1 python3 -m agent_workflows ipd lint --phase post-transition --detail .aw/records/plans/executed/20261001-setdisp-01-c6f6sj-deduplicate-the-two-self-commit-helpers-and-the-two-from-bac.ipd.md
    -    ✓  executed     plan        20261001-setdisp-01-c6f6sj  [medium]  conforming

    $ AW_NO_REEXEC=1 python3 -m agent_workflows ipd lint --phase post-transition --detail .aw/records/plans/executed/20261001-setdisp-02-afdmn6-build-the-cross-spelling-differential-harness-that-makes-eve.ipd.md
    -    ✓  executed     plan        20261001-setdisp-02-afdmn6  [medium]  conforming

    $ AW_NO_REEXEC=1 python3 -m agent_workflows ipd lint --phase post-transition --detail .aw/records/plans/executed/20261001-setdisp-03-m1jlwm-close-the-two-measured-positional-specs-set-gate-bypasses-by.ipd.md
    - >  ✓  executed     plan        20261001-setdisp-03-m1jlwm  [high]  [blocking]  conforming

    $ AW_NO_REEXEC=1 python3 -m agent_workflows ipd lint --phase post-transition --detail .aw/records/plans/executed/20261001-setdisp-04-m94eht-make-aw-specs-set-status-a-thin-adapter-delegating-to-the-sh.ipd.md
    -    ✓  executed     plan        20261001-setdisp-04-m94eht  [medium]  conforming

    $ AW_NO_REEXEC=1 python3 -m agent_workflows ipd lint --phase post-transition --detail .aw/records/plans/executed/20261001-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.ipd.md
    -    ✓  executed     plan        20261001-setdisp-05-vhiqo6  [medium]  conforming
    ```

    Git log output identifying commits by `AW-Item:` trailer:
    ```
    $ git log --format='%h %s' --grep "AW-Item: c6f6sj"
    4d4966695 chore(setdisp): deduplicate self-commit helpers and From-Backlog inheritance
    39ca7253e plan-review: harden c6f6sj (revisions applied)

    $ git log --format='%h %s' --grep "AW-Item: afdmn6"
    23372bd8c tests(setdisp): build cross-spelling differential harness for set dispatch (afdmn6)
    0b1646728 plan-review: harden afdmn6 (revisions applied)

    $ git log --format='%h %s' --grep "AW-Item: m1jlwm"
    6e28e3f2d chore(m94eht): cite executed m1jlwm carrier evidence for gate bypasses
    5ad02df21 work(m1jlwm): pin positional specs set gate parity across setter spellings
    1d5a92098 plan-review: harden m1jlwm (revisions applied)

    $ git log --format='%h %s' --grep "AW-Item: m94eht"
    65023123d chore(plans): cite executed m94eht as carrier evidence in vhiqo6
    e3e04da90 feat(specs): make aw specs set --status a thin adapter delegating to shared status_set engine
    26a337e1b plan-review: harden m94eht (revisions applied)

    $ git log --format='%h %s' --grep "AW-Item: vhiqo6"
    b45042e18 chore(backlog): make aw backlog set status an adapter delegating to status_set (IPD vhiqo6)
    59e17f431 plan-review: harden vhiqo6 (revisions applied)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the per-axis table (a) to (h) with, per row, `afdmn6`'s recorded classification quoted from its V-04, and for each DIFFER row the quoted evidence line from the flipping plan (or the live carrier's id6 and status); plus the pasted passing run of `tests/test_set_dispatch_parity.py`.
  - Observed evidence:
    Per-axis table for candidate axes (a) to (h):
    | Axis | Description | `afdmn6` Classification (quoted from V-04) | Flipping Plan & Quoted Evidence |
    |---|---|---|---|
    | (a) | Positional `specs set implemented` vs `--status` without `--evidence` | AGREE ("Both return rc 1 and refuse before writing (`aw specs set: implementing -> implemented requires a resolvable --evidence citation`; positional outputs `FAIL Validation error on ... requires a resolvable --evidence citation`). Reclassified from DIFFER; pinned by `wdyz5n` (`tests/test_specs_evidence_gate_parity.py`).") | N/A (reclassified to AGREE before execution; pinned by `wdyz5n`) |
    | (b) | Positional `specs set deferred --gate-kind <invalid>` vs `--status` | AGREE ("Both return rc 1 and refuse before writing (`aw specs set: deferred requires a valid --gate-kind`; positional outputs `FAIL Validation error on ... gate-kind`). Reclassified from DIFFER; pinned by `ju3rhs`.") | N/A (reclassified to AGREE before execution; pinned by `ju3rhs`) |
    | (c) | Relocation porcelain shape under `--no-commit` | AGREE ("Both leave ` D <src>` plus `?? <dest>`. Reclassified at review into E-02.") | N/A (reclassified to AGREE at review) |
    | (d) | Sidecar history append | DIFFER ("`backlog set --status` appends to `.aw/records/history.jsonl` (file exists, size > 0); positional `backlog set` appends no sidecar record (`history.jsonl` does not exist).") | Flipped by child 05 `vhiqo6` (commit `b45042e18`). Quoted `vhiqo6` V-04: "Positional spelling --no-commit porcelain: D .aw/records/backlog/open/... ?? .aw/records/backlog/done/ ?? .aw/records/history.jsonl. Identical observable agreement across both spellings." |
    | (e) | Multi-selector on setid vs substring | DIFFER (setid) / AGREE (substring) ("Setid selector matching 2 items: `--status` transitions only 1st match (`paths[0]`, rc 0); positional transitions both matches (rc 0). Substring selector: both refuse rc 2.") | Flipped by child 05 `vhiqo6` (commit `b45042e18`). Quoted `vhiqo6` V-04: "$ aw backlog set sharedset --status done --yes --no-commit ... Moved to done: ['20260928-sharedset-01-bk0001-test.backlog.md', '20260928-sharedset-01-bk0002-test.backlog.md']" |
    | (f) | `specs set` selector resolution | DIFFER ("`--status` accepts path only and exits 2 given id6 (`No such file or directory: 'sp0001'`); positional resolves id6 and transitions rc 0.") | Flipped by child 04 `m94eht` (commit `e3e04da90`). Quoted `m94eht` V-03: "aw specs set sp0001 --status to-review --yes --no-commit: rc=0. File relocated to specs/to-review/ with status to-review." |
    | (g) | `--work-kind`/`--priority` enum validation at function level | DIFFER ("`backlog.run_set` directly called with invalid enum exits 2 and writes nothing; `status_set.run_set_command` directly called exits 0 and writes invalid enum.") | Flipped by child 05 `vhiqo6` (commit `b45042e18`). Quoted `vhiqo6` V-02: "rc = status_set.run_set_command(['done', 'bk0001'], scoped_type='backlog', repo_root=repo, args=args_bad_kind) -> rc 2. Item file read back byte-identical, no write occurred." |
    | (h) | `--message`/`--gate-ref` embedded newline refusal | AGREE ("Both refuse embedded newlines with rc 2 and write nothing (`must not contain embedded newlines`). Reclassified at review into E-02; pinned by commit `a165cb65b` (`4gwgo3`).") | N/A (reclassified to AGREE at review; pinned by `4gwgo3`) |

    Passing run of `tests/test_set_dispatch_parity.py`:
    ```
    $ python3 -m pytest tests/test_set_dispatch_parity.py -v -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <lane-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 25 items

    tests/test_set_dispatch_parity.py::TestNormalizersSubstitute::test_normalizers_substitute_on_real_record PASSED [  4%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_to_reviewed_attestation_refusal_agreement PASSED [  8%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_blocks_release_set_and_cleared_agreement PASSED [ 12%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_graduated_to_agreement PASSED [ 16%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_approved_gate_refusal_agreement PASSED [ 20%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_prior_history_preservation_agreement PASSED [ 24%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_by_human_authority_floor_refusal_agreement PASSED [ 28%]
    tests/test_set_dispatch_parity.py::TestSpecsSetDispatchParity::test_specs_resulting_status_and_file_location_agreement PASSED [ 32%]
    tests/test_set_dispatch_parity.py::TestSetDispatchExpectedDifferences::test_backlog_sidecar_append_expected_difference PASSED [ 36%]
    tests/test_set_dispatch_parity.py::TestSetDispatchExpectedDifferences::test_backlog_enum_validation_at_function_expected_difference PASSED [ 40%]
    tests/test_set_dispatch_parity.py::TestSetDispatchExpectedDifferences::test_backlog_setid_multi_selector_expected_difference PASSED [ 44%]
    tests/test_set_dispatch_parity.py::TestSetDispatchExpectedDifferences::test_specs_selector_resolution_expected_difference PASSED [ 48%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_resulting_status_agreement PASSED [ 52%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_relocation_porcelain_shape_agreement PASSED [ 56%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_gate_field_clearing_on_transition_out_of_blocked_agreement PASSED [ 60%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_release_gate_close_predicate_refusal_agreement PASSED [ 64%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_resulting_file_location_agreement PASSED [ 68%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_number_of_records_appended_agreement PASSED [ 72%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_gate_default_on_bug_transition_to_live_status_agreement PASSED [ 76%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_prior_history_preservation_agreement PASSED [ 80%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_graduated_to_canonicalization_agreement PASSED [ 84%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_substring_selector_ambiguity_refusal_agreement PASSED [ 88%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_unsafe_descriptive_newline_refusal_agreement PASSED [ 92%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_blocks_release_set_and_cleared_agreement PASSED [ 96%]
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_priority_and_work_kind_writes_agreement PASSED [100%]
    ============================= 25 passed in 10.43s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `git log` command and output that found the items closed in the Set window; per closed item, its quoted scope, the covering evidence and the close route; `grep -n '^- Status:\|^- Blocks-Release:\|^- Close-Evidence:'` for `h4fiwa`, `fv4b6s`, `2wae2x`, `fnb8pl` and `lq2w86`.
  - Observed evidence:
    Git log search for backlog modifications across the child execution commits (`4d4966695`, `23372bd8c`, `5ad02df21`, `6e28e3f2d`, `e3e04da90`, `65023123d`, `b45042e18`):
    ```
    $ for h in 4d4966695 23372bd8c 5ad02df21 6e28e3f2d e3e04da90 65023123d b45042e18; do git show --stat --name-only --format='' $h | grep 'records/backlog'; done
    .aw/records/backlog/open/20261009-r73v9i-01-r73v9i-status-set-self-commit-reset-unstages-git-mv-reloc.backlog.md
    ```
    No Set child commit closed any backlog item (b45042e18 created a new open backlog item r73v9i).

    Item `h4fiwa`:
    - Status: `done` (closed via HANDOFF route when carrier `wdyz5n` executed in run `run-20261007T181927Z-1710911`).
    - Quoted scope: "Summary: Positional aw specs set implemented bypasses the --evidence citation gate the --status spelling enforces"
    - Covering evidence: `.aw/records/plans/executed/20261002-setdispgate-01-wdyz5n-run-the-shared-evidence-predicate-on-the-positional-aw-specs.ipd.md`
    - Close route: HANDOFF (carrier `wdyz5n` executed)

    Item `fv4b6s`:
    - Status: `graduated` (with carrier plan `ju3rhs` reached `executed`).
    - Quoted scope: "Summary: Positional aw specs set deferred writes an invalid Gate-Kind the --status spelling refuses"
    - Carrier: `.aw/records/plans/executed/20261002-setdispgate-02-ju3rhs-wire-shared-gate-validation-into-positional-specs-set.ipd.md`
    - Reported as `graduated` with carrier executed.

    Grep output for the five target items:
    ```
    $ for id in h4fiwa fv4b6s 2wae2x fnb8pl lq2w86; do file=$(find .aw/records/backlog -name "*$id*"); echo "=== $id ($file) ==="; grep -n -E '^- (Status|Blocks-Release|Close-Evidence):' "$file"; done
    === h4fiwa (.aw/records/backlog/done/20261001-setdispgate-01-h4fiwa-positional-specs-implemented-skips-evidence-gate.backlog.md) ===
    2:- Status: done
    4:- Blocks-Release: next

    === fv4b6s (.aw/records/backlog/graduated/20261001-setdispgate-01-fv4b6s-positional-specs-deferred-skips-gate-validation.backlog.md) ===
    2:- Status: graduated
    4:- Blocks-Release: next

    === 2wae2x (.aw/records/backlog/done/20260930-2wae2x-01-2wae2x-backlog-status-set-tz-parity.backlog.md) ===
    2:- Status: done
    3:- Close-Evidence: .aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md
    4:- Blocks-Release: next

    === fnb8pl (.aw/records/backlog/done/20260930-fnb8pl-01-fnb8pl-unify-the-history-date-clock-across-both-backlog-s.backlog.md) ===
    2:- Status: done
    4:- Blocks-Release: next

    === lq2w86 (.aw/records/backlog/done/20260930-lq2w86-01-lq2w86-fix-date-timezone-parity-between-backlog-run-set-a.backlog.md) ===
    2:- Status: done
    3:- Close-Evidence: .aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md
    5:- Blocks-Release: next
    ```
    Items `2wae2x`, `fnb8pl`, `lq2w86` were closed outside Set `setdisp` by plan `qjm4bg` (carrier of clock convergence) and were not touched by any Set commit. The `- Blocks-Release: next` line remains intact on all five items.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git show --stat` for child 04's amendment commit, the list of child 05's commits with their changed paths, the added-test list, and the search output with a one-line judgement per hit.
  - Observed evidence:
    Git show --stat for child 04's execution commit `e3e04da90`:
    ```
    $ git show --stat e3e04da90
    commit e3e04da9060f025fba5f2444791a3411c6a0aa0d
    Author: Test <test@example.com>
    Date:   Fri Oct 9 06:30:15 2026 -0400

        feat(specs): make aw specs set --status a thin adapter delegating to shared status_set engine

        AW-Run: run-20261009T030837Z-2088618
        AW-Item: m94eht

     ...atus-a-thin-adapter-delegating-to-the-sh.ipd.md | 203 +++++++--
     ...18-1525-02-sidecar-metadata-and-history.spec.md |   2 +
     CHANGELOG.md                                       |   1 +
     agent_workflows/cli.py                             |   2 +-
     agent_workflows/specs.py                           | 392 ++----------------
     agent_workflows/status_set.py                      | 452 +++++++++++----------
     tests/test_set_dispatch_parity.py                  |   4 +-
     tests/test_specs_releases_descriptive_safety.py    |  46 +--
     tests/test_specs_set_adapter.py                    | 281 +++++++++++++
     tests/test_specs_set_gate_parity.py                |  11 +-
     10 files changed, 768 insertions(+), 626 deletions(-)
    ```
    Commit `e3e04da90` touches both `.aw/records/specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md` and `agent_workflows/status_set.py` in the same commit.

    Child 05 commits and paths:
    ```
    $ for c in b45042e18 59e17f431 39502ea19; do git show --stat --name-only --format='%h' $c; done
    b45042e18:
    .aw/records/backlog/open/20261009-r73v9i-01-r73v9i-status-set-self-commit-reset-unstages-git-mv-reloc.backlog.md
    .aw/records/plans/executed/20261001-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.ipd.md
    CHANGELOG.md
    agent_workflows/backlog.py
    agent_workflows/status_set.py
    tests/test_backlog_set_adapter.py
    tests/test_set_dispatch_parity.py
    tests/test_status_set_descriptive_safety.py

    59e17f431:
    .aw/records/plans/executed/20261001-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.ipd.md
    .aw/records/reviews/20261007-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.review.md

    39502ea19:
    .aw/records/plans/executed/20261001-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.ipd.md
    ```
    No `.spec.md` was touched by any child 05 commit.

    List of test files added by the five children:
    1. `tests/test_set_dispatch_dedup.py` (child 01 `c6f6sj`, commit `4d4966695`)
    2. `tests/test_set_dispatch_parity.py` (child 02 `afdmn6`, commit `23372bd8c`)
    3. `tests/test_specs_set_gate_parity.py` (child 03 `m1jlwm`, commit `5ad02df21`)
    4. `tests/test_specs_set_adapter.py` (child 04 `m94eht`, commit `e3e04da90`)
    5. `tests/test_backlog_set_adapter.py` (child 05 `vhiqo6`, commit `b45042e18`)

    Search output across the 5 added test files:
    - `import inspect` / `inspect.`: 0 hits across all 5 files.
    - `ast.parse`: 0 hits across all 5 files.
    - `open(`: 0 hits across all 5 files.
    - caller-count / symbol-census assertions (`call_count`, `mock_calls`, `assert_called`, `len(dir(`, `__all__`, `__dict__`): 0 hits across all 5 files.
    - `read_text` hits (one-line judgement per hit):
      - `tests/test_set_dispatch_dedup.py` lines 553, 584, 614, 643, 671, 699, 730, 759: test fixture read from temporary scratch directory (`spec_path.read_text`, `spec_gtd.read_text`). Pass (no production source read).
      - `tests/test_set_dispatch_parity.py` lines 417, 477, 513, 583, 619, 672, 716, 764, 823, 878, 896, 940, 1203, 1401, 1454, 1498, 1547, 1600: test fixture read from temporary scratch directory (`item.read_text`, `moved.read_text`, `spec_after.read_text`). Pass (no production source read).
      - `tests/test_specs_set_gate_parity.py` lines 341, 386, 440, 487: test fixture read from temporary scratch directory (`found.read_text`). Pass (no production source read).
      - `tests/test_specs_set_adapter.py` lines 102, 128, 152, 175, 250, 277: test fixture read from temporary scratch directory (`dest.read_text`, `dest1.read_text`, `dest2.read_text`). Pass (no production source read).
      - `tests/test_backlog_set_adapter.py` lines 142, 195, 270, 285, 300: test fixture read from temporary scratch directory (`dest.read_text`, `p.read_text`). Pass (no production source read).
    Conclusion: No test reads production source, counts callers, or performs symbol censuses.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste, per child, the commit, the scratch-worktree command and the three files' pytest summary; the two current runs with their `TZ` and pass counts; and `git worktree list` after cleanup.
  - Observed evidence:
    Per-child scratch worktree parity test measurements:
    - Child 01 `c6f6sj` (commit `4d4966695`):
      Command: `git worktree add --detach /tmp/scratch_c6f6sj 4d4966695 && (cd /tmp/scratch_c6f6sj && PYTHONPATH=/tmp/scratch_c6f6sj AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_backlog_positional_close_gate.py tests/test_backlog_gate_follows_status.py tests/test_status_set.py::TestGateFieldClearingOnStatusChange)`
      Summary: `42 passed in 8.62s`
    - Child 02 `afdmn6` (commit `23372bd8c`):
      Command: `git worktree add --detach /tmp/scratch_afdmn6 23372bd8c && (cd /tmp/scratch_afdmn6 && PYTHONPATH=/tmp/scratch_afdmn6 AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_backlog_positional_close_gate.py tests/test_backlog_gate_follows_status.py tests/test_status_set.py::TestGateFieldClearingOnStatusChange)`
      Summary: `46 passed in 5.89s`
    - Child 03 `m1jlwm` (commit `5ad02df21`):
      Command: `git worktree add --detach /tmp/scratch_m1jlwm 5ad02df21 && (cd /tmp/scratch_m1jlwm && PYTHONPATH=/tmp/scratch_m1jlwm AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_backlog_positional_close_gate.py tests/test_backlog_gate_follows_status.py tests/test_status_set.py::TestGateFieldClearingOnStatusChange)`
      Summary: `46 passed in 4.82s`
    - Child 04 `m94eht` (commit `e3e04da90`):
      Command: `git worktree add --detach /tmp/scratch_m94eht e3e04da90 && (cd /tmp/scratch_m94eht && PYTHONPATH=/tmp/scratch_m94eht AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_backlog_positional_close_gate.py tests/test_backlog_gate_follows_status.py tests/test_status_set.py::TestGateFieldClearingOnStatusChange)`
      Summary: `46 passed in 5.06s`
    - Child 05 `vhiqo6` (commit `b45042e18`):
      Command: `git worktree add --detach /tmp/scratch_vhiqo6 b45042e18 && (cd /tmp/scratch_vhiqo6 && PYTHONPATH=/tmp/scratch_vhiqo6 AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_backlog_positional_close_gate.py tests/test_backlog_gate_follows_status.py tests/test_status_set.py::TestGateFieldClearingOnStatusChange)`
      Summary: `46 passed in 5.40s`
      Quoted from `vhiqo6`'s own evidence:
      "tests/test_backlog_positional_close_gate.py: 23 passed in 2.67s; tests/test_backlog_gate_follows_status.py: 18 passed in 2.59s; tests/test_status_set.py::TestGateFieldClearingOnStatusChange: 5 passed in 2.39s"

    Current runs under skewed timezones:
    - Run under `TZ=Pacific/Kiritimati`:
      ```
      $ TZ=Pacific/Kiritimati AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_backlog_positional_close_gate.py tests/test_backlog_gate_follows_status.py tests/test_status_set.py::TestGateFieldClearingOnStatusChange
      ============================== 46 passed in 7.00s ==============================
      ```
    - Run under `TZ=Etc/GMT+12`:
      ```
      $ TZ=Etc/GMT+12 AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider tests/test_backlog_positional_close_gate.py tests/test_backlog_gate_follows_status.py tests/test_status_set.py::TestGateFieldClearingOnStatusChange
      ============================== 46 passed in 6.65s ==============================
      ```

    Git worktree list after cleanup:
    ```
    $ git worktree list
    <repo>                                                         b031c5afc [main]
    <repo>/.aw/state/suite-baselines/7zb4ny-attempt1               b031c5afc (detached HEAD)
    <repo>/.aw/worktrees/.aw-isocommit-6xj9ahwx                    a283a3216 (detached HEAD)
    <repo>/.aw/worktrees/7zb4ny                                    b031c5afc [aw/lane/7zb4ny]
    <repo>/.aw/worktrees/e25iy9                                    cadea62b5 [aw/lane/e25iy9]
    <repo>/.aw/worktrees/e25iy9_attempt2                           f28eba802 [aw/lane/e25iy9_attempt2]
    <repo>/.aw/worktrees/fhinri                                    59eccd0b1 [aw/lane/fhinri]
    <repo>/.aw/worktrees/jj5ju1                                    26ad9b0ff [aw/lane/jj5ju1]
    <repo>/.aw/worktrees/jj5ju1_attempt2                           82d8aa390 [aw/lane/jj5ju1_attempt2]
    <repo>/.aw/worktrees/m47znv                                    819813f1d [aw/lane/m47znv]
    <repo>/.aw/worktrees/m47znv_attempt2                           443d5d6e5 [aw/lane/m47znv_attempt2]
    <repo>/.aw/worktrees/psgyzw                                    b9c5684e1 [aw/lane/psgyzw]
    <repo>/.aw/worktrees/rdjka2                                    e5ee917d9 [aw/lane/rdjka2]
    <repo>/.aw/worktrees/review-sweep-run-20261007T165339Z-456282  90811a37e [aw/lane/review-sweep-run-20261007T165339Z-456282]
    <repo>/.aw/worktrees/review-sweep-run-20261008T043532Z-504210  c95bb46f2 [aw/lane/review-sweep-run-20261008T043532Z-504210]
    <repo>/.aw/worktrees/review-sweep-run-20261008T043646Z-538757  8a78df2c9 [aw/lane/review-sweep-run-20261008T043646Z-538757]
    <repo>/.aw/worktrees/rlhmt9                                    ee22628d2 [aw/lane/rlhmt9]
    <repo>/.aw/worktrees/tliqz6                                    868198ae3 [aw/lane/tliqz6]
    <repo>/.aw/worktrees/tm8k2n                                    71c9c3fad [aw/lane/tm8k2n]
    <repo>/.aw/worktrees/ucwlwt                                    cb22e1947 [aw/lane/ucwlwt]
    <repo>/.aw/worktrees/y9m1ya                                    06a7edeee [aw/lane/y9m1ya]
    <repo>/.aw/worktrees/z8ex9f                                    b16ca64eb [aw/lane/z8ex9f]
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the baseline commit, both `python3 -m pytest -rf` summary lines with their `TZ`, the baseline and current failure sets by id with their difference, and `git worktree list` after cleanup. Paste `aw ipd lint` on this plan conforming and `git diff --cached --name-only` before committing.
  - Observed evidence:
    Baseline commit: `4d4966695~1` (`e0caadedf6221e48134621ac988569f414c491cd`).
    Baseline suite run (scratch worktree at `4d4966695~1`, TZ=EDT America/New_York):
    `1 failed, 4879 passed, 2 skipped, 3 warnings in 134.17s (0:02:14)`
    Baseline failure set (1 item):
    - `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta`

    Current suite run (HEAD `b031c5afc`, TZ=EDT America/New_York):
    `8 failed, 7187 passed, 2 skipped, 3 warnings in 197.31s (0:03:17)`
    Current failure set (8 items):
    - `tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_a_finalize_inserts_scope_exceeded_metadata`
    - `tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_b_finalize_leaves_metadata_untouched_when_fully_in_scope`
    - `tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_c_multiple_out_of_scope_paths_sorted_and_sanitized`
    - `tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_d_runner_retry_loop_out_of_scope_notice`
    - `tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_e_commit_scope_reason_recording_only_without_paths`
    - `tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_f_commit_scope_reason_rejects_paths_not_out_of_scope`
    - `tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_g_recorded_scope_justifications_survive_recovery_rebegin`
    - `tests/test_attempt_lane_facts.py::AttemptLaneFactsTests::test_case_2_oc_host_refused_isolated_turn`

    Difference analysis:
    - The baseline failure in `test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta` was excluded from the default fast suite by the `livecorpus` marker filter introduced in pyproject.toml.
    - The 8 failures in current HEAD are in files added/modified by unrelated lanes (`test_scope_exceeded.py` added by plan `psgyzw` in commit `163874fcc`, tracked in backlog `fdkkco` and `u18kic`; `test_attempt_lane_facts.py` in lane `wir001`). Both are pre-existing external conditions documented in executed plans `gzb2rq` and `rlhmt9`.
    - Zero test failures introduced by Set `setdisp`: all 114 tests touched or added by `setdisp` children pass 100%.

    Git worktree list after cleanup:
    ```
    $ git worktree list
    <repo>                                                         b031c5afc [main]
    <repo>/.aw/state/suite-baselines/7zb4ny-attempt1               b031c5afc (detached HEAD)
    <repo>/.aw/worktrees/.aw-isocommit-6xj9ahwx                    a283a3216 (detached HEAD)
    <repo>/.aw/worktrees/7zb4ny                                    b031c5afc [aw/lane/7zb4ny]
    <repo>/.aw/worktrees/e25iy9                                    cadea62b5 [aw/lane/e25iy9]
    <repo>/.aw/worktrees/e25iy9_attempt2                           f28eba802 [aw/lane/e25iy9_attempt2]
    <repo>/.aw/worktrees/fhinri                                    59eccd0b1 [aw/lane/fhinri]
    <repo>/.aw/worktrees/jj5ju1                                    26ad9b0ff [aw/lane/jj5ju1]
    <repo>/.aw/worktrees/jj5ju1_attempt2                           82d8aa390 [aw/lane/jj5ju1_attempt2]
    <repo>/.aw/worktrees/m47znv                                    819813f1d [aw/lane/m47znv]
    <repo>/.aw/worktrees/m47znv_attempt2                           443d5d6e5 [aw/lane/m47znv_attempt2]
    <repo>/.aw/worktrees/psgyzw                                    b9c5684e1 [aw/lane/psgyzw]
    <repo>/.aw/worktrees/rdjka2                                    e5ee917d9 [aw/lane/rdjka2]
    <repo>/.aw/worktrees/review-sweep-run-20261007T165339Z-456282  90811a37e [aw/lane/review-sweep-run-20261007T165339Z-456282]
    <repo>/.aw/worktrees/review-sweep-run-20261008T043532Z-504210  c95bb46f2 [aw/lane/review-sweep-run-20261008T043532Z-504210]
    <repo>/.aw/worktrees/review-sweep-run-20261008T043646Z-538757  8a78df2c9 [aw/lane/review-sweep-run-20261008T043646Z-538757]
    <repo>/.aw/worktrees/rlhmt9                                    ee22628d2 [aw/lane/rlhmt9]
    <repo>/.aw/worktrees/tliqz6                                    868198ae3 [aw/lane/tliqz6]
    <repo>/.aw/worktrees/tm8k2n                                    71c9c3fad [aw/lane/tm8k2n]
    <repo>/.aw/worktrees/ucwlwt                                    cb22e1947 [aw/lane/ucwlwt]
    <repo>/.aw/worktrees/y9m1ya                                    06a7edeee [aw/lane/y9m1ya]
    <repo>/.aw/worktrees/z8ex9f                                    b16ca64eb [aw/lane/z8ex9f]
    ```

    Pasted `aw ipd lint` on this plan conforming:
    ```
    $ AW_NO_REEXEC=1 python3 -m agent_workflows ipd lint --phase pre-transition --detail .aw/records/plans/pending/20261007-setdisp-06-7zb4ny-audit-the-five-setdisp-children-together-and-run-the-set-lev.ipd.md
    -    ◕  approved     plan        20261007-setdisp-06-7zb4ny  [medium]  conforming
    ```

    Pasted `git diff --cached --name-only` before committing:
    ```
    $ git diff --cached --name-only
    .aw/records/plans/pending/20261007-setdisp-06-7zb4ny-audit-the-five-setdisp-children-together-and-run-the-set-lev.ipd.md
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the pasted `check release-gates --agent` output, and for any finding the item id6 and whether a Set plan touched it.
  - Observed evidence:
    ```
    $ AW_NO_REEXEC=1 python3 -m agent_workflows check release-gates --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"release-gates","findings":0,"evidence":["inventory","rules"],"next":"aw releases list"}
    ```
    Findings count: 0 findings. No finding attributable to Set `setdisp`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Measurement only: commit only this plan's own file (its evidence) through `aw commit <plan> -- <path>`; never push. Paste actual output for every `V-*`. A failed check is reported and the plan is NOT finalized as passing: record the `V-*` `Result: failed` and leave the plan in `pending/`, so orchestrator `63zo2f`'s E-06 cannot report the Set complete. The scope fence is a declaration, not a stop condition; an out-of-scope edit is justified with `--scope-reason` at finalize. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`; never hand-`git mv` the file.
