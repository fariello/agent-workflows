# IPD: Stop the From-Spec nudge for a plan that declares no spec source or edits the cited spec

- Date: 2026-10-04
- Kind: child
- Concern: `check_engine.check_plan_spec_link_missing` (rule `check.plan-spec-link-missing`, severity `info`) flags every pending plan whose `- Concern:`, `- Scope:` or `- Scope-Paths:` mentions a known spec id6 and whose `- From-Spec:` is missing or an absent sentinel. It treats a mention as evidence that the plan was produced FROM that spec, which is a guess: a plan that amends a spec, or is merely constrained by one, mentions it too. It also cannot be silenced honestly: `ipd_schema.source_link_is_absent` maps `-`, `none` and `unresolved` alike to "absent", so writing `- From-Spec: none` (the author's explicit answer "not produced from a spec") still fires the nudge, and the shipped test `test_plan_carrying_absent_sentinel` pins that for `-`. Measured 2026-10-04: 23 live findings, nine of them on plans of Set `gradcover`, which amends `25kzda` and must NOT carry `From-Spec: 25kzda` because Order 08 (`24qw39`) counts active plans with a real `From-Spec` as that spec's continued handoff output. The rule should fire exactly when a plan mentions a spec and its author has not declared the relationship.
- Scope: IN: in `check_plan_spec_link_missing`, treat two declarations as an answer: (a) `- From-Spec:` set to an explicit "no spec source" sentinel (`none` or `-`), and (b) the plan's `- Scope-Paths:` containing the cited spec's own file path (the plan edits that spec, which `AGENTS.md` requires to be declared there); keep `unresolved` and a missing field as "not answered"; update the shipped test that pins `-` as firing, and add tests. OUT: the meaning of `-` in `aw ipd set --from-spec -` (it still REMOVES the line, so it stays "not answered"; only a written `- From-Spec: -` value counts); `source_link_is_absent` and every other caller of it (production counting, gate handoff and dangling checks keep treating `none` as no link); the rule's severity.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_from_spec_missing.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 13
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: jm27py
- Approval: 2026-10-06, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-06 approved (aw set): status set to approved
- 2026-10-04 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-005. Spec-edit exemption made literal-file only (PR-001); remedy text names all three answers and the hand-edit form of `none` (PR-002); `hm1h3l` given `- From-Spec: none` so the Set is actually silenced (PR-003); quote/case normalization and extra tests (PR-004); gate honesty rule and F-03 context (PR-005).
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 13 of Set `gradcover` at the maintainer's request (2026-10-04) to stop the nudge firing on this Set's plans "in a manner that is consistently reliable to not give false positives or false negatives". The rule is made exact by keying on what the author DECLARED rather than inferring from prose. It is independent of every other child, so it carries no dependency.

## Goal

Make `check.plan-spec-link-missing` fire exactly when a pending plan mentions a spec and its author has declared neither a `From-Spec` link, an explicit "no spec source" answer, nor an edit of that spec.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rule

- [x] E-01 In `check_plan_spec_link_missing`, before parsing citations: if the plan's `- From-Spec:` value, stripped and lowercased, is `none` or `-`, skip the plan (an explicit answer). Keep `unresolved`, an empty value and a missing field as unanswered. Define the two accepted values as a named constant in `check_engine` with a comment stating why `unresolved` is excluded, rather than editing `ipd_schema.SOURCE_LINK_ABSENT_SENTINELS`, which other callers rely on. Normalize exactly as `source_link_is_absent` does (strip whitespace and surrounding quotes, then lowercase), so `"none"` and `None` count too. Also rewrite the finding's `required` and `recovery` text so it names all three answers: link it (`aw ipd set <id6> --from-spec <spec-id6>`), write `- From-Spec: none` in the front matter when the plan is not produced from a spec (state that this is a hand edit: `aw ipd set --from-spec none` is refused as an unresolvable spec id, and `--from-spec -` removes the line), or list the spec's file in `- Scope-Paths:` when the plan edits it.
  - Depends on: none
  - Expected outcome: a pending plan citing a known spec with `- From-Spec: none` or `- From-Spec: -` produces no finding; with `unresolved`, an empty value or no field it still produces one.
  - Execution state: performed

- [x] E-02 After computing the cited id6s, drop each id6 whose spec FILE path appears LITERALLY in the plan's parsed `- Scope-Paths:` (use `ipd_schema.parse_scope_paths`; map each known id6 to its file through `_iter_spec_records` plus `_read_item_id`; compare as repo-relative POSIX paths with exact string equality). A directory or glob entry (for example `.aw/records/specs/approved/`) does NOT count even though `ipd_lifecycle._scope_match` would match it: a broad entry would silence every spec under it and is not a declaration that the plan edits THIS spec, which is a false negative. If no cited id6 remains, produce no finding; otherwise report only the remaining ones.
  - Depends on: E-01
  - Expected outcome: a plan citing `25kzda` whose Scope-Paths lists the `25kzda` spec file produces no finding; one citing `25kzda` and `r07vma` that edits only `25kzda` reports `r07vma` only; one whose Scope-Paths lists an unrelated path, or a directory that contains the cited spec's file, still reports.
  - Execution state: performed

### Task group 2: pin it

- [x] E-03 Update `tests/test_check_engine_from_spec_missing.py`: change `test_plan_carrying_absent_sentinel` so a written `- From-Spec: -` yields NO finding, naming the changed assertion and the reason in the commit message; add cases for `none` (silent), `unresolved` (fires), empty value (fires), the spec-edit exemption (silent), the partial spec-edit case (fires for the other spec only), an unrelated Scope-Paths entry (fires), a directory entry containing the cited spec's file (fires), and quoted `"none"` / uppercase `None` (silent); assert the finding's recovery text names all three answers. Run the rule over the real tree and paste the before and after finding counts with the list of plans that stopped being flagged, confirming each one declares `none`/`-` or edits the cited spec. Expected on today's tree: every `gradcover` plan stops being flagged (Order 01 `hm1h3l` cites `2vev8j` without editing it, and carries `- From-Spec: none` for that reason since the 2026-10-04 review of this plan); re-derive the list at execution rather than trusting this sentence. Prove the tests can fail by reverting E-01 and pasting the failure.
  - Depends on: E-02
  - Expected outcome: the updated file passes; the mutation fails it; on the real tree the findings that disappear are exactly the declared ones.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `source_link_is_absent` IS SHARED. It backs `From-Backlog`/`From-Spec` handling in production counting (`production_checks._read_from_backlog`), gate handoff and dangling checks; changing its sentinel set would change those. The exemption therefore lives only in this rule.
- `aw ipd set --from-spec -` REMOVES THE LINE (`releases.set_from_spec_line` returns the text with the line stripped when the value is `-`), so a plan set that way has NO field and stays "not answered". Only a value written into the file counts as an answer.
- SPEC EDITS MUST BE DECLARED IN `- Scope-Paths:` (`AGENTS.md`, "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"), so the spec-edit exemption keys on a declaration the repository already requires.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The rule skips only a usable link. It reads `- From-Spec:` and skips when `not source_link_is_absent(target)`; `source_link_is_absent` returns True for `None`, empty, `-`, `none` and `unresolved` (`SOURCE_LINK_ABSENT_SENTINELS`). | `check_plan_spec_link_missing`; `ipd_schema.source_link_is_absent` |
| F-02 | No existing plan outside Set `gradcover` writes `- From-Spec: none` or `- From-Spec: -`, so treating them as answers changes no other plan's result. | `grep -rl '^- From-Spec: none' .aw/records/plans/` returning only `gradcover` plans; the same for `-` returning nothing |
| F-03 | 23 live `check.plan-spec-link-missing` findings at authoring, nine on `gradcover` plans (24 and 10 at review on 2026-10-04, this plan's own `25kzda` citation included). Context only; V-03 re-derives. | `check_engine.check_plan_spec_link_missing(Path('.'))` over the tree |
| F-05 | There is no tool path that WRITES the new answer: `aw ipd set --from-spec none` is refused ("unresolvable spec id", the validator in `status_set.run_set_command` and `apply_status_change` checks the value against `known_spec_ids`), and `--from-spec -` removes the line (`releases.set_from_spec_line`). So `none` can only be written by hand, which the finding's remedy must say. | `status_set.py` "unresolvable spec id"; `releases.set_from_spec_line` |
| F-06 | `ipd_lifecycle._scope_match` treats a directory entry as covering every file beneath it (`.aw/records/specs/approved/` matches any approved spec), so a matcher-based exemption would let one broad entry silence every spec. | `_scope_match` docstring and its trailing-slash branch |
| F-04 | The shipped test pins the old behavior for `-`. `test_plan_carrying_absent_sentinel` writes `from_spec="-"` and asserts one finding. | the quoted test |

## Proposed changes (ordered, validatable)

1. Treat a written `none`/`-` as an explicit answer (E-01).
2. Exempt a cited spec the plan declares it edits (E-02).
3. Update and extend the tests; measure the real-tree delta; mutation proof (E-03).

## Deferred / out of scope (with reason)

- A SEPARATE `- Constrained-By:` FIELD for plans that cite a spec as a constraint. `none` already says "not produced from a spec"; a constraint relationship is not something any tool consumes today.
  - Carrier-Declined: no consumer; would add a field nothing reads
- CHANGING `source_link_is_absent`. See conventions.
  - Carrier-Declined: shared helper; changing it would alter production counting

## Scope check

- Over-scope: none. One production module and its existing test file.
- Under-scope: none.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_check_engine_from_spec_missing.py tests/test_check_engine.py -q` pasted.
- Real-tree finding counts before and after, with the plans that stopped being flagged.
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec governs this rule (its only home is the `check_engine` rule table and the comment beside it, which is updated to state the two declarations). The `AGENTS.md` paragraph mentioning `check.plan-spec-link-missing` calls it an advisory nudge "when a pending plan cites a spec without carrying the link"; that remains true and needs no change.

## Open questions

### OQ-01: Should `unresolved` also silence the rule?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: NO. `unresolved` is the scaffold's placeholder for "not decided yet" (it is in `ipd_authoring._AUTHORING_PLACEHOLDERS` for other fields), so it is the opposite of an answer; silencing it would turn the nudge's main target into a false negative.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the diff and test output for `none` (no finding), `-` (no finding), `unresolved` (finding), empty (finding), missing (finding).
  - Observed evidence:
    Diff:
    ```diff
    +_FROM_SPEC_LINE_RE = _re.compile(r"(?m)^-[ \t]*From-Spec:[ \t]*(.*?)[ \t]*$")
    +
    +# IPD jm27py E-01: explicit "no spec source" sentinels that silence check.plan-spec-link-missing.
    +# `unresolved` is deliberately excluded because it is the scaffold's placeholder for "not decided
    +# yet" (ipd_authoring._AUTHORING_PLACEHOLDERS), so treating it as an answer would turn the nudge's
    +# main target into a false negative.
    +PLAN_SPEC_LINK_NO_SOURCE_SENTINELS: FrozenSet[str] = frozenset({"-", "none"})
    ...
    +        # Check existing From-Spec (E-01: skip explicit "none" or "-")
    +        m_fs = _FROM_SPEC_LINE_RE.search(text)
    +        if m_fs is not None:
    +            raw_target = m_fs.group(1)
    +            cleaned_target = raw_target.strip().strip("\"'").strip().lower()
    +            if cleaned_target in PLAN_SPEC_LINK_NO_SOURCE_SENTINELS:
    +                continue
    +            if not _ipd_schema.source_link_is_absent(raw_target):
    +                # Valid edge already present
    +                continue
    ```
    Test output:
    ```
    tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_carrying_from_spec_unresolved PASSED [ 20%]
    tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_pending_plan_missing_edge PASSED [ 40%]
    tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_carrying_absent_sentinel PASSED [ 60%]
    tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_carrying_from_spec_none PASSED [ 80%]
    tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_carrying_empty_from_spec PASSED [100%]
    ======================= 5 passed, 32 deselected in 0.37s =======================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff and test output for the spec-edit exemption (no finding), the partial case (finding naming only the other spec), and the unrelated Scope-Paths entry (finding).
  - Observed evidence:
    Diff:
    ```diff
    +_SCOPE_PATHS_LINE_RE = _re.compile(r"(?m)^-\s*Scope-Paths:[ \t]*(.*)$")
    ...
    +    spec_files_by_id6: Dict[str, Set[str]] = {}
    +    resolved_root = repo_root.resolve()
    +    for sp, stext in _iter_spec_records(repo_root):
    +        sid = _read_item_id(stext)
    +        if sid:
    +            try:
    +                rel = sp.resolve().relative_to(resolved_root).as_posix()
    +            except (ValueError, OSError):
    +                rel = sp.as_posix()
    +            spec_files_by_id6.setdefault(sid, set()).add(rel)
    ...
    +        # E-02: drop each cited id6 whose spec file path appears literally in Scope-Paths
    +        m_sp = _SCOPE_PATHS_LINE_RE.search(text)
    +        if m_sp is not None:
    +            sp_raw = m_sp.group(1)
    +            parsed_paths, _is_gf, _errs = _ipd_schema.parse_scope_paths(sp_raw)
    +            if parsed_paths:
    +                scope_set = set(parsed_paths)
    +                cited = [
    +                    tok
    +                    for tok in cited
    +                    if not any(
    +                        spec_file in scope_set
    +                        for spec_file in spec_files_by_id6.get(tok, ())
    +                    )
    +                ]
    +                if not cited:
    +                    continue
    ```
    Test output:
    ```
    tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_editing_cited_spec_exempt PASSED [ 33%]
    tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_partial_spec_edit PASSED [ 66%]
    tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_with_unrelated_scope_paths PASSED [100%]
    ======================= 3 passed, 34 deselected in 0.34s =======================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the updated test file passing with its count and the changed assertion; the real-tree before/after counts with the list of plans no longer flagged, each shown to declare `none`/`-` or to edit the cited spec; the mutation failing and the revert passing; a grep for source-structure reads in the test file returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the two declared paths.
  - Observed evidence:
    Updated test file passing (37 passed, changed assertion: test_plan_carrying_absent_sentinel now asserts len(drifts) == 0):
    ```
    .....................................                                    [100%]
    37 passed in 2.98s
    ```

    Real-tree before/after counts:
    Before: 24 findings
    After: 13 findings
    Plans no longer flagged (11 total: 10 gradcover plans declaring - From-Spec: none, plus 1 plan editing both cited specs in Scope-Paths):
    - .aw/records/plans/pending/20261004-gradcover-02-8mabmu-make-the-coverage-probe-quote-the-work-it-found-and-credit-w.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20261004-gradcover-03-qs00nc-add-one-shared-orchestrator-review-readiness-check-and-the-a.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20261004-gradcover-04-5etev3-run-the-coverage-probe-only-where-a-run-can-retire-an-orches.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20261004-gradcover-05-26m1nb-refuse-aw-ipd-set-to-review-reviewed-and-approved-for-an-orc.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20261004-gradcover-06-r2wa38-check-the-whole-set-before-a-production-action-hands-off-a-b.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20261004-gradcover-07-nnsa2o-send-a-refused-production-or-review-action-back-for-bounded.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20261004-gradcover-08-24qw39-let-a-production-action-resume-an-unfinished-handoff-instead.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20261004-gradcover-09-52opph-re-check-every-pending-orchestrator-and-send-the-failing-one.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20261004-gradcover-10-sbiv1j-refuse-aw-backlog-set-graduated-and-aw-specs-set-implementin.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20261004-gradcover-13-jm27py-stop-the-from-spec-nudge-for-a-plan-that-declares-no-spec-so.ipd.md (- From-Spec: none)
    - .aw/records/plans/pending/20260930-lifegate-02-e25iy9-delete-the-driver-token-and-the-location-guess-and-check-the.ipd.md (Scope-Paths includes .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md and .aw/records/specs/to-review/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md)

    Mutation failure:
    Mutated PLAN_SPEC_LINK_NO_SOURCE_SENTINELS = frozenset():
    ```
    FAILED tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_carrying_absent_sentinel
    FAILED tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_carrying_from_spec_none
    FAILED tests/test_check_engine_from_spec_missing.py::TestCheckPlanSpecLinkMissing::test_plan_carrying_quoted_none_or_uppercase_none
    3 failed, 34 passed in 2.98s
    ```
    Revert passing:
    ```
    37 passed in 2.98s
    ```

    Grep for source-structure reads:
    `grep -iE "inspect|ast" tests/test_check_engine_from_spec_missing.py` exited 1 (no matches).

    Bare pytest summary reconciled:
    Baseline: `5083 passed, 2 skipped, 3 warnings in 416.60s (0:06:56)`
    Post-edit: `5092 passed, 2 skipped, 3 warnings in 254.56s (0:04:14)`
    Delta: +9 new tests passed.

    aw ipd lint conforming:
    `- >  ◕  approved     plan        20261004-gradcover-13-jm27py  [high]  [blocking]  conforming`

    aw sanitize --agent:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
