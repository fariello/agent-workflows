# IPD: Verify specs.validate_spec accepts spec 89xjll and close the attention.unsafe-field defect with evidence

- Date: 2026-10-11
- Kind: child
- Concern: `specs.validate_spec` reported `attention.unsafe-field` for spec `89xjll` because its `- Scope:` (343 chars at filing) exceeded the then single 300-char descriptive bound applied to Scope.
- Scope: Confirm on current main that `specs.validate_spec` returns no drift for `89xjll` and for every real spec, that `aw specs check` reports no `attention.unsafe-field`, and that the prose length class guard tests pass; fix forward in the validator or bound only if a re-run fails.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/attention_contract.py, tests/test_descriptive_length_classes.py, tests/test_spec_review_attestation.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: md2o3y
- Blocks-Release: next
- Set: md2o3y
- Order: 1
- Highest E allocated: 03
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: k6clui
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record 20261011-md2o3y-01-k6clui)
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005

- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready graduating backlog md2o3y; root cause and current-pass state established from repository evidence.

## Goal

Release the `next` gate on backlog `md2o3y` with executed evidence: show that `specs.validate_spec` now accepts spec `89xjll` (and the whole real specs corpus), name the change that fixed it, and confirm a behavioral regression guard already covers the fixed bound.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-run the validator that reported the defect

- [x] E-01 Call `specs.validate_spec(path, path.read_text())` on the `89xjll` spec (locate it by id6, e.g. `aw find specs 89xjll`, since its directory may change with its status; at review it is `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md`) and on every `*.spec.md` under `.aw/records/specs/` (recursive), printing each non-empty drift list as `d.rule`/`d.detail` plus the total count examined, then run `aw specs check` and record its exit code and the count of `unsafe-field` lines in its output.
  - Depends on: none
  - Expected outcome: `89xjll` returns `[]`; no spec reports an `attention.unsafe-field` drift (the corpus count is re-derived at execution; 40 at review); `aw specs check` exits 0. If some OTHER spec reports a drift whose rule is NOT `attention.unsafe-field`, it is outside this plan's defect: record it and file it with `aw backlog new` rather than fixing it here.
  - Execution state: performed

### Task group 2: Confirm the regression guards

- [x] E-02 Run `python3 -m pytest tests/test_descriptive_length_classes.py tests/test_spec_review_attestation.py -o addopts="" -k "LengthClass or Grandfathering or prose"` and, if the `-k` filter selects nothing, rerun both files without `-k`; record the summary line.
  - Depends on: none
  - Expected outcome: zero failures, including `test_spec_validation_prose_and_oneline_fields` and `test_every_real_spec_in_this_repository_still_conforms`.
  - Execution state: performed

### Task group 3: Fix forward only on failure

- [x] E-03 If E-01 or E-02 failed with an `attention.unsafe-field` on Scope/Concern/Question, repair the validator or bound within Scope-Paths (never edit the approved `89xjll` spec body to dodge the check); a change to either bound value or to which fields are prose-class is a contract change to Section 8.8 of spec `attention-registry-and-cross-tree-status`, so it MUST be made in that spec in the same commit (declared in Scope-Paths). Then re-run E-01, E-02 and the bare suite `python3 -m pytest`, comparing its failing-test names to a bare baseline taken before the edit. Otherwise record that no change was required and capture `git diff --stat -- <Scope-Paths>`.
  - Depends on: E-01, E-02
  - Expected outcome: either an empty Scope-Paths diff (expected case) or a fix confined to Scope-Paths with all re-runs passing.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Suite invocation: run bare `python3 -m pytest`; narrowed runs clear defaults with `-o addopts=""` (AGENTS.md repository development contract).
- Tests exercise behavior, not source structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); the guards call `specs.validate_spec` on real input.
- `specs.validate_spec` signature is `(path: Path, text: str) -> List[core.Drift]`; it checks Scope with `A.is_safe_prose_descriptive(scope)` and message "Scope is over-length or has control chars/newlines".
- `attention_contract.PROSE_DESCRIPTIVE_FIELDS` is `frozenset(("Scope", "Concern", "Question"))`, bound `attention_contract.MAX_PROSE_DESCRIPTIVE_LEN = 4300`, versus one-line `attention_contract.MAX_DESCRIPTIVE_LEN = 300`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | At filing (2026-10-01) the `89xjll` Scope was 343 characters, over the single 300-char bound then enforced on Scope by `specs.validate_spec`, producing `attention.unsafe-field`. | Sibling plan `oehkmh` F-1 (`git show cb3ea8546:` of the spec, measured 343). |
| F-2 | Commit `b325725d2` (`pl1lbb`) split the bound into a one-line class (300) and a prose class (4300) and moved Scope to the prose class, removing the root cause for any spec Scope. | `attention_contract.is_safe_prose_descriptive`, `MAX_PROSE_DESCRIPTIVE_LEN = 4300`. |
| F-3 | The current `89xjll` Scope line measures 367 characters (including the `- Scope: ` prefix; re-measured at review HEAD `66401aeb1`, authoring recorded 369), above 300 and accepted only because of F-2. | `grep "^- Scope:"` on the spec, `awk length`. |
| F-4 | On this worktree's base (`1feee61ca`) `specs.validate_spec` on `89xjll` returns `[]`, and `aw specs check` exits 0 with zero `unsafe-field` lines. Re-measured at review HEAD `66401aeb1`: 40 `*.spec.md` files, 0 with any drift, `89xjll` -> `[]`, `aw specs check` exit 0 with 0 `unsafe-field` lines; the E-02 `-k` filter selects both named guards (`10 passed, 26 deselected`) and the two files unfiltered give `36 passed`. | Pre-authoring runs during this turn; review re-run. |
| F-5 | A behavioral guard exists: `tests/test_descriptive_length_classes.py::test_spec_validation_prose_and_oneline_fields` asserts a 400-char Scope is clean and a 4301-char Scope drifts. No new test is required. | test name in that file. |
| F-6 | Sibling backlog `6bolin` (same root cause, test side) is carried by pending plan `oehkmh`. That plan is not modified here; the two carriers are independent so each gate is released by its own executed plan. | `.aw/records/plans/pending/20261011-6bolin-01-oehkmh-...ipd.md` |

## Proposed changes (ordered, validatable)

1. E-01: re-run `specs.validate_spec` on `89xjll` and the whole corpus, plus `aw specs check`.
2. E-02: run the existing guard tests.
3. E-03: fix forward only on failure; otherwise record an empty diff.

In the expected case this plan changes no source or test file.

## Deferred / out of scope (with reason)

- Closing `6bolin` or editing plan `oehkmh`: separate lifecycle (F-6).
  - Carrier: oehkmh
- Editing the approved `89xjll` spec body: forbidden as a way to pass the check, and unnecessary since the prose bound accepts it.
  - Carrier-Declined: a forbidden shortcut, not owed work

## Scope check

- Over-scope: none. Scope-Paths lists only files a fix-forward in E-03 could touch. The plan file itself is always written (evidence), and the attention spec is declared only for a possible Section 8.8 amendment.
- Under-scope: none. Every V-* demands command or test output, reachable by construction.

## Required tests / validation

- `specs.validate_spec` on `89xjll` returns `[]`; no real spec yields `attention.unsafe-field`; `aw specs check` exits 0 (E-01).
- `tests/test_descriptive_length_classes.py` and `tests/test_spec_review_attestation.py` guards pass (E-02).
- If code changed, the bare full suite `python3 -m pytest` passes (E-03).

## Spec / documentation sync

N/A in the expected case: no behavior change. The prose length class is already specified in spec `attention-registry-and-cross-tree-status` Section 8.8 and shipped by `pl1lbb`. That spec is declared in Scope-Paths ONLY because an E-03 fix-forward that changed a bound or a field's class would amend Section 8.8, and the runners announce declared spec edits up front; in the expected case it is not touched and is acknowledged with `--scope-ack` at finalize.

## Open questions

None. Root cause and current state were resolved from repository evidence (F-1 to F-5).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of the `specs.validate_spec` call printing `[]` for `89xjll`, the count of specs examined, and no `attention.unsafe-field` drift for any spec, and pasted `aw specs check` tail plus `exit=0` and the `unsafe-field` line count (0).
  - Observed evidence:
    ```
    $ python3 -c '
    from pathlib import Path
    from agent_workflows import specs

    p_89 = Path(".aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md")
    res_89 = specs.validate_spec(p_89, p_89.read_text())
    print(f"Spec 89xjll drift: {res_89}")

    spec_files = sorted(Path(".aw/records/specs").rglob("*.spec.md"))
    print(f"Total specs examined: {len(spec_files)}")

    unsafe_field_count = 0
    drift_count = 0
    for p in spec_files:
        drifts = specs.validate_spec(p, p.read_text())
        if drifts:
            drift_count += 1
            print(f"Drifts in {p}:")
            for d in drifts:
                print(f"  {d.rule}: {d.detail}")
                if "unsafe-field" in d.rule:
                    unsafe_field_count += 1

    print(f"Specs with drifts: {drift_count}")
    print(f"attention.unsafe-field count: {unsafe_field_count}")
    '
    Spec 89xjll drift: []
    Total specs examined: 40
    Specs with drifts: 0
    attention.unsafe-field count: 0

    $ AW_NO_REEXEC=1 aw specs check; echo "exit=$?"
    aw specs check: all specs conform. 40 specs checked.
    exit=0
    ```
    Unsafe-field line count in `aw specs check`: 0.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted pytest summary line showing zero failed, with `test_spec_validation_prose_and_oneline_fields` and `test_every_real_spec_in_this_repository_still_conforms` among the passed tests.
  - Observed evidence:
    ```
    $ python3 -m pytest tests/test_descriptive_length_classes.py tests/test_spec_review_attestation.py -o addopts="" -k "LengthClass or Grandfathering or prose" -v
    tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_the_checker_fires_on_exactly_the_unattested_reviewed_cell PASSED [ 10%]
    tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms PASSED [ 20%]
    tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_plans_are_not_made_stricter PASSED [ 30%]
    tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_the_rule_is_registered_as_an_error_with_its_invariant PASSED [ 40%]
    tests/test_descriptive_length_classes.py::DescriptiveLengthClassesTests::test_no_echo_untrusted_value_regression PASSED [ 50%]
    tests/test_descriptive_length_classes.py::DescriptiveLengthClassesTests::test_bounds_are_distinct_and_constants_defined PASSED [ 60%]
    tests/test_descriptive_length_classes.py::DescriptiveLengthClassesTests::test_hostile_shapes_unsafe_under_both_predicates PASSED [ 70%]
    tests/test_descriptive_length_classes.py::DescriptiveLengthClassesTests::test_spec_validation_prose_and_oneline_fields PASSED [ 80%]
    tests/test_descriptive_length_classes.py::DescriptiveLengthClassesTests::test_exact_boundary_pairs PASSED [ 90%]
    tests/test_descriptive_length_classes.py::DescriptiveLengthClassesTests::test_write_path_round_trip_and_agreement PASSED [100%]

    ====================== 10 passed, 26 deselected in 0.96s =======================

    $ python3 -m pytest tests/test_descriptive_length_classes.py tests/test_spec_review_attestation.py -o addopts=""
    ============================== 36 passed in 1.89s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git diff --stat` for Scope-Paths (empty in the expected case); if non-empty, also the pre-edit and post-edit bare full-suite summary lines with failing-test names showing no new failure, and, if a bound or field class changed, the spec Section 8.8 diff.
  - Observed evidence:
    ```
    $ git diff --stat -- agent_workflows/specs.py agent_workflows/attention_contract.py tests/test_descriptive_length_classes.py tests/test_spec_review_attestation.py .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
    ```
    (empty diff; no changes required to Scope-Paths)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved k6clui --by-human`); there are no open questions. Begin with `aw ipd begin k6clui`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition. In the expected (verify-only) case no declared path changes; acknowledge each declared-but-unmodified path at finalize with `--scope-ack <path>`. If an edit outside Scope-Paths proves necessary, make it and justify it with `--scope-reason <path>=<why>`. Never edit the `89xjll` spec body to pass the check.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run.

Commits: this plan's own record always changes (E/V marks and evidence), so commit it, plus any Scope-Paths you changed, through `aw commit k6clui -- <paths>`; verify `git diff --cached --name-only` before any raw commit; never push, never tag.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize k6clui`. Release gate: this plan carries `- From-Backlog: md2o3y` and the inherited `- Blocks-Release: next`; once it is executed, `aw backlog set done md2o3y` closes the item through the HANDOFF rule (this plan is its only carrier). Sibling `6bolin` (also `Blocks-Release: next`) is closed separately by its own carrier `oehkmh`.
