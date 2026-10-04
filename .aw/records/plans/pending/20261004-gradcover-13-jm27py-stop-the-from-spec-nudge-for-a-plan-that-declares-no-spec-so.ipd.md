# IPD: Stop the From-Spec nudge for a plan that declares no spec source or edits the cited spec

- Date: 2026-10-04
- Kind: child
- Concern: `check_engine.check_plan_spec_link_missing` (rule `check.plan-spec-link-missing`, severity `info`) flags every pending plan whose `- Concern:`, `- Scope:` or `- Scope-Paths:` mentions a known spec id6 and whose `- From-Spec:` is missing or an absent sentinel. It treats a mention as evidence that the plan was produced FROM that spec, which is a guess: a plan that amends a spec, or is merely constrained by one, mentions it too. It also cannot be silenced honestly: `ipd_schema.source_link_is_absent` maps `-`, `none` and `unresolved` alike to "absent", so writing `- From-Spec: none` (the author's explicit answer "not produced from a spec") still fires the nudge, and the shipped test `test_plan_carrying_absent_sentinel` pins that for `-`. Measured 2026-10-04: 23 live findings, nine of them on plans of Set `gradcover`, which amends `25kzda` and must NOT carry `From-Spec: 25kzda` because Order 08 (`24qw39`) counts active plans with a real `From-Spec` as that spec's continued handoff output. The rule should fire exactly when a plan mentions a spec and its author has not declared the relationship.
- Scope: IN: in `check_plan_spec_link_missing`, treat two declarations as an answer: (a) `- From-Spec:` set to an explicit "no spec source" sentinel (`none` or `-`), and (b) the plan's `- Scope-Paths:` containing the cited spec's own file path (the plan edits that spec, which `AGENTS.md` requires to be declared there); keep `unresolved` and a missing field as "not answered"; update the shipped test that pins `-` as firing, and add tests. OUT: the meaning of `-` in `aw ipd set --from-spec -` (it still REMOVES the line, so it stays "not answered"; only a written `- From-Spec: -` value counts); `source_link_is_absent` and every other caller of it (production counting, gate handoff and dangling checks keep treating `none` as no link); the rule's severity.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_from_spec_missing.py
- Item-Dependencies: none
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 13
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: jm27py

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 13 of Set `gradcover` at the maintainer's request (2026-10-04) to stop the nudge firing on this Set's plans "in a manner that is consistently reliable to not give false positives or false negatives". The rule is made exact by keying on what the author DECLARED rather than inferring from prose. It is independent of every other child, so it carries no dependency.

## Goal

Make `check.plan-spec-link-missing` fire exactly when a pending plan mentions a spec and its author has declared neither a `From-Spec` link, an explicit "no spec source" answer, nor an edit of that spec.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rule

- [ ] E-01 In `check_plan_spec_link_missing`, before parsing citations: if the plan's `- From-Spec:` value, stripped and lowercased, is `none` or `-`, skip the plan (an explicit answer). Keep `unresolved`, an empty value and a missing field as unanswered. Define the two accepted values as a named constant in `check_engine` with a comment stating why `unresolved` is excluded, rather than editing `ipd_schema.SOURCE_LINK_ABSENT_SENTINELS`, which other callers rely on.
  - Depends on: none
  - Expected outcome: a pending plan citing a known spec with `- From-Spec: none` or `- From-Spec: -` produces no finding; with `unresolved`, an empty value or no field it still produces one.
  - Execution state: pending

- [ ] E-02 After computing the cited id6s, drop each id6 whose spec FILE path appears in the plan's parsed `- Scope-Paths:` (use `ipd_schema.parse_scope_paths` and the spec record paths already walked by `_iter_spec_records`, compared as repo-relative POSIX paths; a directory or glob entry that covers the spec file counts only if it resolves to that file through the same matcher `aw ipd finalize`'s scope check uses, otherwise it does not). If no cited id6 remains, produce no finding; otherwise report only the remaining ones.
  - Depends on: E-01
  - Expected outcome: a plan citing `25kzda` whose Scope-Paths lists the `25kzda` spec file produces no finding; one citing `25kzda` and `r07vma` that edits only `25kzda` reports `r07vma` only; one whose Scope-Paths lists an unrelated directory still reports.
  - Execution state: pending

### Task group 2: pin it

- [ ] E-03 Update `tests/test_check_engine_from_spec_missing.py`: change `test_plan_carrying_absent_sentinel` so a written `- From-Spec: -` yields NO finding, naming the changed assertion and the reason in the commit message; add cases for `none` (silent), `unresolved` (fires), empty value (fires), the spec-edit exemption (silent), the partial spec-edit case (fires for the other spec only), and an unrelated Scope-Paths entry (fires). Run the rule over the real tree and paste the before and after finding counts with the list of plans that stopped being flagged, confirming each one declares `none`/`-` or edits the cited spec. Prove the tests can fail by reverting E-01 and pasting the failure.
  - Depends on: E-02
  - Expected outcome: the updated file passes; the mutation fails it; on the real tree the findings that disappear are exactly the declared ones.
  - Execution state: pending

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
| F-03 | 23 live `check.plan-spec-link-missing` findings at authoring, nine on `gradcover` plans. | `aw check plans --agent` filtered by rule |
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

- [ ] V-01 validates E-01
  - Required evidence: paste the diff and test output for `none` (no finding), `-` (no finding), `unresolved` (finding), empty (finding), missing (finding).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff and test output for the spec-edit exemption (no finding), the partial case (finding naming only the other spec), and the unrelated Scope-Paths entry (finding).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the updated test file passing with its count and the changed assertion; the real-tree before/after counts with the list of plans no longer flagged, each shown to declare `none`/`-` or to edit the cited spec; the mutation failing and the revert passing; a grep for source-structure reads in the test file returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the two declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
