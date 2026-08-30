# IPD: Record self-resolved decisions in the review artifact so a wrong turn is auditable

- Date: 2026-08-29
- Kind: child
- Concern: Agents are instructed to resolve obstacles themselves rather than refuse, but a self-resolved judgement call is recorded nowhere the maintainer will see it, so an agent can take a road trip in the wrong direction invisibly.
- Scope: Make a reviewer or executor RECORD each decision it made instead of asking, into the tracked `## Decisions` section defined by `15zvu6`, and give the maintainer one command to audit them. Also fix the location defect: the existing autonomous-decisions register writes into gitignored `.aw/workflow-artifacts/`.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/plan-review-long.md, agent_workflows/review_findings.py, agent_workflows/cli.py, tests/test_review_decisions.py
- Item-Dependencies: executed:15zvu6
- Status: to-review
- Set: revgate
- Order: 4
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: c621h9
- Blocks-Release: next

## Workflow history

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored on maintainer instruction that decisions which would have been open questions, but for the resolve-before-refusing rule, must remain auditable.

## Goal

Make "the agent decided this itself" a durable, reviewable fact. The resolve-before-refusing rule is
right, but it converts questions into silent choices; this plan keeps the rule and removes the silence,
so a maintainer can find a wrong turn after the fact instead of discovering it in the code.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make recording mandatory, not optional

- [ ] E-01 Amend the plan-review workflow body (`.aw/system/workflows/plan-review/plan-review.md`,
      Step 3.1 "Build the question set" and 3.2, which today say to resolve from authoritative evidence
      and cite the source) to require that EVERY question resolved from evidence rather than asked is
      recorded as a row in the review artifact's `## Decisions` section. State the rule positively: a
      resolved question is not "gone", it is a recorded decision with an alternative that was rejected
      and a basis that can be checked. Keep the existing citation requirement.
  - Depends on: none
  - Expected outcome: the workflow instruction demands a decision row for each self-resolution.
  - Execution state: pending

- [ ] E-02 Mirror the same amendment into `plan-review-long`
      (`.aw/system/workflows/plan-review-long/plan-review-long.md`), which the manifest states is kept
      in DELIBERATE PARITY with the single-file variant. Parity is a documented property, so an
      instruction added to one and not the other is a defect.
  - Depends on: E-01
  - Expected outcome: both variants carry identical decision-recording wording.
  - Execution state: pending

- [ ] E-03 Require a `Reversible: yes|no` judgement on each decision row and require that an
      IRREVERSIBLE self-made decision ALSO be surfaced, not merely logged: it must either be raised as a
      blocking open question, or carry an explicit note that the maintainer was told. The distinction is
      the point of the whole plan: a reversible wrong turn costs a rewrite, an irreversible one cannot
      be undone, and the resolve-before-refusing rule must not silently authorize the latter.
  - Depends on: E-01
  - Expected outcome: the instruction distinguishes reversible from irreversible self-resolution and
    escalates the irreversible case.
  - Execution state: pending

### Task group 2: give the maintainer one command

- [ ] E-04 Add a read-only `aw reviews decisions [<selector>]` verb (registered in
      `agent_workflows/cli.py`) that prints the recorded decisions for one plan, a Set, or the whole
      tree, reading the `## Decisions` sections through `15zvu6`'s parser. Support `--agent`/`--json`
      per the house machine-output contract, and `--irreversible` to filter to the rows that matter
      most. Read-only: it makes no writes.
  - Depends on: none
  - Expected outcome: a maintainer can answer "what did the agents decide without asking me?" in one
    command instead of grepping 92 plans.
  - Execution state: pending

- [ ] E-05 Fix the LOCATION defect for the pre-existing autonomous-decisions register: `set_records`
      writes `decisions.md` and `open-questions.md` into the run-artifacts dir
      (`set_records.py:152-153`), but `.aw/workflow-artifacts/` is GITIGNORED (`.gitignore:68`), so
      those decisions are invisible in the repository and are lost with the untracked tree. Make the
      durable copy land in the tracked review artifact (or a tracked sibling), keeping the untracked
      projection as the disposable convenience copy, exactly as the plans/walkthroughs convention
      already treats a private scratch copy as disposable and the tracked one as the source of truth.
      Do NOT un-ignore `.aw/workflow-artifacts/` wholesale; that directory holds machine-local run noise.
  - Depends on: E-04
  - Expected outcome: an autonomous decision survives in a tracked file; the gitignored copy remains a
    convenience only.
  - Execution state: pending

### Task group 3: prove it cannot silently regress

- [ ] E-06 Write `tests/test_review_decisions.py` proving: a decisions row round-trips; the
      `aw reviews decisions` verb prints a recorded decision and exits per the house contract;
      `--irreversible` filters correctly; the machine mode is ANSI-free and parses as JSON; and BOTH
      workflow bodies contain the decision-recording instruction (a parity assertion, so E-02 cannot
      silently drift). Include the adversarial case: a review artifact whose decision row claims
      `Reversible: no` with NO escalation must be reported by `aw check`, since an unescalated
      irreversible self-decision is the exact failure this plan exists to prevent.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the mechanism is covered, and the adversarial guard is demonstrated firing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The mechanism partly EXISTS and is well shaped: `set_records.py:41-42` defines `DECISIONS_FILE` and
  `OPEN_QUESTIONS_FILE`, `write_local_projections` (`:143-158`) writes them, and real examples under
  `.aw/workflow-artifacts/assess-*/` show a genuinely useful format (concern/scope, method, verdict
  rationale, what was intentionally NOT done and why, assumptions, open questions for the user). This
  plan should REUSE that shape rather than invent a new vocabulary.
- But `.aw/workflow-artifacts/` is gitignored (`.gitignore:68`), so nothing written there is auditable
  from the repository. That is the location defect E-05 fixes.
- `plan-review` does NOT use the register today: `.aw/workflow-artifacts/` contains a `release-review`
  directory but no `plan-review` one, so review-time self-resolutions have never been recorded through
  this path.
- The plan-review manifest row states the long variant is kept in "deliberate parity" with the
  single-file one, which is why E-02 exists and why E-06 asserts parity mechanically.
- The repo already treats a private/scratch copy as disposable and the tracked copy as the source of
  truth (the AGENTS.md rule about brain/memory dirs). E-05 follows that precedent instead of inventing
  a new durability rule.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Self-resolution is already widespread and already unauditable. | 112 `Resolution or deferral rationale: RESOLVED` entries across 92 plans; no consolidated view exists |
| F-2 | plan-review has never written a decisions register. | `.aw/workflow-artifacts/` has a `release-review` dir but no `plan-review` dir |
| F-3 | Even when written, the register is invisible to the repo. | `.gitignore:68` ignores `.aw/workflow-artifacts/`; `set_records.py:152-153` writes the register there |
| F-4 | The existing register format is good and worth reusing. | e.g. `.aw/workflow-artifacts/assess-bugs/20260715-205322/decisions.md` records scope, method, verdict rationale, deliberate non-actions with reasons, assumptions, and open questions for the user |
| F-5 | The resolve-before-refusing rule increases the volume of silent decisions, so the audit trail is a precondition for it, not a nicety. | Maintainer instruction 2026-08-29 requiring agents to find a strong recommended path before refusing |
| F-6 | Parity between the two review variants is a documented property that mechanical drift would break. | The plan-review-long manifest row states the two are kept in deliberate parity |

## Proposed changes (ordered, validatable)

1. Require a recorded decision for every self-resolved question, in both review variants (E-01, E-02).
2. Distinguish reversible from irreversible, and escalate the irreversible (E-03).
3. Give the maintainer one read-only command to audit decisions (E-04).
4. Make the durable copy tracked, fixing the gitignored-location defect (E-05).
5. Prove all of it, including a firing adversarial guard (E-06).

## Deferred / out of scope (with reason)

- **Retro-recording the 112 existing self-resolutions.** Out of scope: they are already written as prose
  inside their plans' open-question sections, which is auditable if imperfect, and manufacturing typed
  decision rows from them would be re-authoring history rather than recording it.
- **The same treatment for EXECUTION-time decisions.** Partially deferred: this plan covers the review
  path, which is where the resolve-before-refusing rule bites hardest and where 112 instances already
  exist. Execution-time self-decisions deserve the same audit trail, but the executor writes into a
  plan's own V-item evidence, which is a different seam and a different instruction surface. Recorded
  here so it is not forgotten; a follow-up should cover it.
- **Un-ignoring `.aw/workflow-artifacts/`.** Explicitly rejected in E-05: it holds machine-local run
  noise, and tracking all of it would create leak and churn problems. Only the decisions record needs
  durability.
- **Gating on decisions.** Out of scope: an unescalated irreversible decision is reported (E-06's
  adversarial case) but this plan does not block execution on it, because the gating machinery belongs to
  `plqjt7` and stacking a second gate here would duplicate it.

## Scope check

- Over-scope: none. Instruction text, one read-only verb, one location fix, and tests.
- Under-scope: acknowledged. This plan makes decisions VISIBLE and AUDITABLE; it does not prevent a bad
  decision, and it does not block execution when one is recorded. Detection after the fact is the honest
  claim. Prevention would require a human gate on every self-resolution, which would defeat the
  resolve-before-refusing rule the maintainer asked for.

## Required tests / validation

1. `python3 -m pytest tests/test_review_decisions.py` green, run BARE (the repo's `addopts` already
   supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not pass `-n0` or a second `-q`).
2. Full default suite green with counts pasted.
3. A worked end-to-end demonstration: review a scratch plan, self-resolve one question, and show the
   decision appearing in `aw reviews decisions` output.
4. The parity assertion demonstrated failing: remove the instruction from one variant and show E-06's
   parity test catches it.

## Spec / documentation sync

- Both workflow bodies change (E-01, E-02); they are the instruction surface agents load, so this IS the
  documentation.
- `.aw/records/reviews/README.md` (created by `15zvu6`) must gain the decisions-section convention and
  the `Reversible` semantics.
- The new `aw reviews decisions` verb must be declared in the command surface, or the conformance test
  `tests/test_cli_conformance_matrix.py` will fail; check `command_surface.py` and add the declaration
  in the same pass as E-04.

## Open questions

### OQ-01: Should an unescalated irreversible self-decision block execution, or only be reported?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: not blocking, because E-06 reports it either way and this plan is
  landable as report-only. RECOMMENDATION: report only, for now. Blocking would put a second gate beside
  `plqjt7`'s, and the maintainer's stated preference is fewer pieces of code where possible; a reported
  row plus the `aw reviews decisions --irreversible` view already gives the audit trail that was the
  actual ask. Revisit if a real wrong turn slips through despite being reported.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the amended Step 3 wording from `plan-review.md`, showing it requires a
    recorded decision row for each self-resolved question and that the pre-existing citation requirement
    survived. Paste a `git diff` of the hunk proving no other instruction was weakened.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the corresponding wording from `plan-review-long.md` and a diff showing the
    two variants' decision-recording text is equivalent. State explicitly that parity was checked, not
    assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `Reversible` instruction, and paste the escalation rule for the
    irreversible case. Then paste a worked example of each: one reversible decision recorded and left as
    a row, one irreversible decision recorded AND escalated, showing the two are treated differently.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw reviews decisions` human output for a fixture with at least two
    decisions, the `--irreversible` filtered output, and the `--agent` output showing it parses as JSON
    and contains no ANSI escape (`\x1b[`). Paste the exit codes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git check-ignore -v` for the OLD location proving it is ignored, then show
    the new durable copy is TRACKED (`git ls-files` finds it) after a review. Confirm
    `.aw/workflow-artifacts/` is still ignored, i.e. the fix did not un-ignore the noisy tree.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the test file result with counts, AND the adversarial guard OBSERVED
    FAILING: construct a review artifact with `Reversible: no` and no escalation, paste `aw check`
    reporting it, then fix the fixture and paste the clean run. Also paste the parity test failing when
    the instruction is removed from one variant, then passing when restored. A guard never seen to fail
    is not accepted as evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

RESOLVE-BEFORE-REFUSING (maintainer instruction, 2026-08-29): if you hit an obstacle while executing
this plan, you MUST first do the work of finding a strong recommended path from repository evidence.
Reporting "cannot proceed" is a LAST resort, acceptable only when you can state (a) what you tried,
(b) the specific evidence that blocks each candidate approach, and (c) a concrete recommended option
with trade-offs for the maintainer to choose. This plan is itself the audit trail for that rule, so any
question you resolve while executing it MUST be recorded as a decision row in this plan's own review
artifact: practice what the plan installs.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents and runs are ACTIVE in
this checkout; verify the staged set before every commit with `git diff --cached --name-only` and never
stage, revert, or discard another party's work. Run the suite BARE. When every `V-*` item carries pasted
evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`.
