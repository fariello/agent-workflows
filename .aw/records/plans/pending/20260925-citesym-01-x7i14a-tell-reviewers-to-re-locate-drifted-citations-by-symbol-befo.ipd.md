# IPD: Tell reviewers to re-locate drifted citations by symbol before calling them false

- Date: 2026-09-25
- Kind: child
- Concern: The review workflows (`plan-review`, `plan-review-long`, `spec-review`, `verify-execution`) mandate `path:line` evidence but never say what to do when a cited line no longer holds the cited construct, so reviewers decide per run whether line drift is a false claim or cosmetic. The AUTHORING half of backlog `yos8rq` already shipped (plan `mzc019`, spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`); the REVIEW half did not, and `mzc019` explicitly scoped it OUT ("any change to how REVIEWS cite code").
- Scope: IN: one disposition rule in the evidence step of each of the four review workflows (re-locate by symbol or quoted string; drift whose anchor resolves is at most LOW; an anchor that does not resolve is a real evidence finding), and a recommendation that the reviewer's OWN evidence cells carry a symbol beside `path:line`. OUT: changing the `path:line` format or the findings-table column; any lint (the `hesb87` promotion decision owns that); the authoring rule (already in Section 10.2); retrofitting existing plans or reviews.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/01-discover-and-snapshot.md, .aw/system/workflows/spec-review/spec-review.md, .aw/system/workflows/verify-execution/verify-execution.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: yos8rq
- Set: citesym
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: x7i14a

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog yos8rq; re-measured that the authoring rule shipped via mzc019 (spec Section 10.2, IPD-C801, scaffold guidance) while grep over the four review workflows finds no re-locate or drift disposition beside any "Verify material claims with `path:line`" step, so only the review half remains.

## Goal

Give every reviewer the same rule for a stale line citation, so drift stops producing inconsistent findings or wasted revision rounds, and make reviewers' own evidence survive drift.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the rule, once per review workflow

- [ ] E-01 In `.aw/system/workflows/plan-review/plan-review.md`, section "## Step 1: Evidence and pre-review snapshot", replace item "4. Verify material claims with `path:line` evidence." with a two-part item: (a) verify by locating the cited construct by its SYMBOL or quoted string, treating the line number as a hint (spec `ipd-structure-and-linting` Section 10.2 states the same posture for authors); (b) disposition: anchor resolves and only the line moved = no finding, or at most one LOW batched finding per plan noting the drift; anchor does not resolve anywhere, or resolves to something that contradicts the claim = a real evidence finding at the severity of the claim it supports; a bare `path:line` with no anchor that no longer matches = search for the described construct before judging, and record which case applied. Also, in the findings-table field "**Evidence:** `path:line`.", append "plus the symbol or a quoted string, for example the symbol `mod.func_name` beside its path and line".
  - Depends on: none
  - Expected outcome: the Step 1 item and the Evidence field carry the rule; no other line changes.
  - Execution state: pending

- [ ] E-02 Mirror the same rule in `.aw/system/workflows/plan-review-long/01-discover-and-snapshot.md` item "4. Verify material claims with `path:line` citations.", worded identically to E-01 (the README says the long variant is "Kept in deliberate parity with the single-file" workflow).
  - Depends on: E-01
  - Expected outcome: the two variants' evidence steps say the same thing.
  - Execution state: pending

- [ ] E-03 In `.aw/system/workflows/spec-review/spec-review.md`, extend the step item beginning "4. Verify material claims with `path:line` evidence. A spec's measured claim" with the same re-locate-by-symbol rule and disposition, keeping the existing "re-measure it rather than trusting it" sentence.
  - Depends on: E-01
  - Expected outcome: spec-review's evidence step carries the rule.
  - Execution state: pending

- [ ] E-04 In `.aw/system/workflows/verify-execution/verify-execution.md`, extend the "**Evidence discipline**: re-open the actual `path:line` and diff" bullet with: locate the construct by symbol or quoted string when the line has moved; a moved-but-resolvable anchor is not a gap; an unresolvable one is. (`intent-audit.md` inherits this discipline by its own words "inherited from `verify-execution.md`", so it is not edited.)
  - Depends on: E-01
  - Expected outcome: verify-execution's evidence discipline carries the rule.
  - Execution state: pending

### Task group 2: suite

- [ ] E-05 Run the bare suite `python3 -m pytest` and record the summary line (the workflows ship in the wheel via `pyproject.toml` `".aw/system" = "agent_workflows/_data/.aw/system"`, and installer tests read them).
  - Depends on: E-04
  - Expected outcome: no new failures relative to the pre-change baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Do NOT add prose-pin tests: `tests/test_spec_review_attestation.py` class `WorkflowPackageTests` docstring explains the repo deliberately removed tests asserting English sentences in workflow markdown ("such a test fails on every legitimate reword and catches no defect"). Validation is therefore grep plus the suite.
- `.aw/system/managed-sections.json` records a sha256 for `plan-review.md` that ALREADY does not match the file at HEAD (`7c98...` recorded vs `48fb...` actual), so the executor should not treat a hash mismatch there as caused by this plan and should not edit that file.
- Workflow text is AI-facing, so the no-dash rule for user-facing prose does not apply.

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-1 | Authoring half is DONE: spec Section 10.2 defines (a) symbol, (b) quoted string, (c) line only appended; scaffold emits it; `IPD-C801` advises. | `ipd_authoring` scaffold string "Cite code by SYMBOL"; `ipd_lint` constant `"IPD-C801"`; plan `mzc019` in `executed/` |
| F-2 | `mzc019` Scope OUT explicitly lists "any change to how REVIEWS cite code", so the review half has no other owner. | `mzc019` `- Scope:` |
| F-3 | No review workflow mentions re-locating or drift in its evidence step: grep for `symbol` across the four workflow dirs matches only the unrelated "prerequisite whose symbols are absent" scope-fence sentence. | grep over `.aw/system/workflows/{plan-review,plan-review-long,spec-review,verify-execution}` |
| F-4 | The spec already states the reader-side posture for OLD plans ("treat it as a HINT and locate the construct by symbol"), but only in the IPD spec, which reviewers are not pointed at from their evidence step. | spec Section 10.2 paragraph "ENFORCEMENT IS ADVISORY-ONLY AND DATE-GATED" |
| F-5 | There is no separate workflow source tree; `.aw/system/workflows/` is the source and is packaged into the wheel. | `pyproject.toml` force-include `".aw/system"`; `git ls-files` shows no other `plan-review.md` besides host shims |

## Proposed changes (ordered, validatable)

1. E-01 plan-review. 2. E-02 plan-review-long. 3. E-03 spec-review. 4. E-04 verify-execution. 5. E-05 suite.

## Deferred / out of scope (with reason)

- A lint that checks `path:line (symbol)` citations still resolve (backlog option 3).
  - Carrier: hesb87
- Adding the rule to the `AGENTS.md` "real citations" clause via `engine.py`.
  - Carrier-Declined: the authoring contract already lives in the IPD spec and the scaffold, which is where authors meet it; widening the managed block for every installed repo is not needed for the review fix.

## Scope check

- Over-scope: none.
- Under-scope: `plan-review-long/02-review-and-revise.md` field "Evidence: `path:line`." and `report-template.md` are not edited; the step-01 rule governs how evidence is gathered, and the format recommendation in E-01 is optional guidance. A reviewer may add them if parity is judged to require it.

## Required tests / validation

Grep evidence per file, `aw ipd lint` on this plan, and the bare suite. No new test (see conventions).

## Spec / documentation sync

N/A: spec `ipd-structure-and-linting` Section 10.2 already states the rule for authors and the reader posture; this plan points reviewers at it and changes no spec.

## Open questions

### OQ-01: Should a moved-but-resolvable citation produce NO finding or a LOW one?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFAULT: at most ONE batched LOW per plan ("N citations drifted, all re-located by symbol"), because the drift is real information for the author but must not cost a revision round. The executor writes the default; a maintainer preferring "no finding" changes one clause.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff .aw/system/workflows/plan-review/plan-review.md` showing only the Step 1 item 4 and the Evidence field changed, and `grep -n -i "by symbol\|drift" .aw/system/workflows/plan-review/plan-review.md` returning the new lines (it returns none before).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `01-discover-and-snapshot.md` and a side-by-side quote showing its item 4 text matches E-01's.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `spec-review.md` showing the rule added and the "re-measure it rather than trusting it" sentence retained.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diff of `verify-execution.md` evidence-discipline bullet; paste `git diff --name-only` confirming `intent-audit.md` is untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `python3 -m pytest` summary line; list and baseline-compare any failing node ids.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires `/plan-review` then explicit human approval before execution. Commit via `aw commit <plan> -- <paths>`, never push; transition with `aw ipd finalize` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
