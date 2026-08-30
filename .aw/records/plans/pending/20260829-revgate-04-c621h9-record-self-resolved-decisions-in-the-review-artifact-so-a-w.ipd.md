# IPD: Record self-resolved decisions in the review artifact so a wrong turn is auditable

- Date: 2026-08-29
- Kind: child
- Concern: Agents are instructed to resolve obstacles themselves rather than refuse, but a self-resolved judgement call is recorded nowhere the maintainer will see it, so an agent can take a road trip in the wrong direction invisibly.
- Scope: Make a reviewer or executor RECORD each decision it made instead of asking, into the tracked `## Decisions` section defined by `15zvu6`, and give the maintainer one command to audit them. Also fix the location defect: the existing autonomous-decisions register writes into gitignored `.aw/workflow-artifacts/`.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/plan-review-long.md, agent_workflows/review_findings.py, agent_workflows/reviews.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/check_engine.py, .aw/records/reviews/README.md, tests/test_review_decisions.py
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

- [ ] E-04 Add a read-only `aw reviews decisions [<selector>]` verb that prints the recorded decisions
      for one plan, a Set, or the whole tree, reading the `## Decisions` sections through `15zvu6`'s
      parser. Support `--agent`/`--json` per the house machine-output contract, and `--irreversible` to
      filter to the rows that matter most. Read-only: it makes no writes. Put the implementation in a new
      `agent_workflows/reviews.py` rather than inside `cli.py`, matching the owner-verb shape used by
      `specs`/`backlog` (a module with a `run_*` entry point that `cli.py` dispatches to); emit through
      the `CommandResult`/`select_output`/`get_renderer` pipeline rather than a bare `print`.
      NOTE THIS CREATES THE `reviews` CLI NAMESPACE: verified that `aw reviews` is NOT a valid top-level
      command today, and that `15zvu6` does NOT add one (its `Scope-Paths` has no `cli.py`), so this verb
      brings the noun into existence. Register it at the two `cli.py` edit points AND declare it, because
      the declaration is MANDATORY, not optional: every parser leaf must carry an entry in
      `command_surface.COMMAND_INVENTORY` or `find_undeclared_leaves` reports it. Model the declaration
      on an existing READ-ONLY verb (a `query`/`read` class, NOT the `mutation`/`dry_run_default` shape
      used by `specs new`), since this verb writes nothing. `command_surface.py` is in `Scope-Paths`.
      BE HONEST ABOUT THE BASELINE: `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`
      is ALREADY FAILING with 59 undeclared leaves (measured at `f02c64e`, F-9), so it will not go green
      from your change. Do NOT declare the other 59. Prove only that `reviews decisions` is not in the
      reported set and that the count did not grow.
  - Depends on: none
  - Expected outcome: `aw reviews --help` and `aw reviews decisions --help` work, the verb is declared in
    `COMMAND_INVENTORY` with a read-only class, `find_undeclared_leaves` does not report it, the
    pre-existing 59 undeclared leaves are untouched, and a maintainer can answer "what did the agents
    decide without asking me?" in one command instead of grepping the corpus.
  - Execution state: pending

- [ ] E-05 DO NOT "FIX" `set_records`; it is not the defect this plan thought it was, and touching it
      would damage a working design. The draft called `set_records.py:152-153` a LOCATION DEFECT because
      `.aw/workflow-artifacts/` is gitignored. That premise is REFUTED by the module itself (F-7): the
      untracked projections are DELIBERATE ("Local run projections written under the untracked
      run-artifacts dir (the local authoritative run convention)") and they already HAVE a tracked
      counterpart, because the same module writes a TRACKED walkthrough to `.aw/records/walkthroughs/`
      (`render_walkthrough:166`, `write_walkthrough:200`) and `promote_local_checkpoints:411` exists
      precisely to promote an untracked decision checkpoint into that tracked walkthrough BEFORE
      releasing another lane, with the stated purpose that "a crash never loses a recorded decision".
      So the untracked/tracked split is the same disposable-projection-plus-durable-record convention
      this plan cites as its own precedent, already implemented. There is no lost-decision defect to fix.
      Two further facts remove the motive: `set_records` is the SET-COORDINATION register (execset Order
      02), not the review path, and `write_local_projections` has NO production caller at all today (only
      two tests call it), so it is not the surface through which plan-review decisions would flow.
      WHAT THIS ITEM ACTUALLY OWES: nothing in `set_records`. Instead, make the review path's durability
      explicit where it belongs, which is the tracked `## Decisions` section in `15zvu6`'s `.review.md`
      artifact that E-01 through E-04 already use. State in the review artifact README (see Spec sync)
      that the tracked `.review.md` is the source of truth for review-time decisions and that
      `set_records`' untracked projections are a DIFFERENT, Set-coordination surface with its own
      tracked walkthrough. If you find a real gap in the Set path while doing this, file it as a separate
      backlog item; do NOT widen this plan into `set_records.py`.
  - Depends on: E-04
  - Expected outcome: `set_records.py` is UNMODIFIED (prove it with a diff); the review path's tracked
    source of truth is documented as the `.review.md` `## Decisions` section; and the distinction between
    the two registers is recorded so a later agent does not "fix" the Set one either.
  - Execution state: pending

### Task group 3: prove it cannot silently regress

- [ ] E-06 Write `tests/test_review_decisions.py` proving: a decisions row round-trips; the
      `aw reviews decisions` verb prints a recorded decision and exits per the house contract;
      `--irreversible` filters correctly; the machine mode is ANSI-free and parses as JSON; and BOTH
      workflow bodies contain the decision-recording instruction (a parity assertion, so E-02 cannot
      silently drift). Include the adversarial case: a review artifact whose decision row claims
      `Reversible: no` with NO escalation must be reported by `aw check`, since an unescalated
      irreversible self-decision is the exact failure this plan exists to prevent.
      THE `aw check` RULE IS THIS PLAN'S TO BUILD, which the draft never stated: it asked E-06 to prove
      `aw check` reports the unescalated-irreversible case, but no E-item created that rule and no sibling
      owns it (verified: `plqjt7` owns the findings-threshold rule and `7nkcgp` the dependency cascade;
      neither mentions decisions or `Reversible`). So add `check.review-decision-unescalated` to
      `check_engine.py` as part of this item, registered in the `RuleSpec` table beside the other
      review/backlog cross-reference rules, at `"warning"` severity to stay consistent with this plan's
      report-only posture (OQ-01) and with `check.orphaned-live-blocker` as the advisory precedent.
      `check_engine.py` is in `Scope-Paths`. Enumerate review files through the record-path authority that
      `15zvu6` E-09 registers, never a hardcoded `.aw/records/reviews` string.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the mechanism is covered, and the adversarial guard is demonstrated firing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The mechanism partly EXISTS and is well shaped: `set_records.py:41-42` defines `DECISIONS_FILE` and
  `OPEN_QUESTIONS_FILE`, `write_local_projections` (`:143-158`) writes them, and real examples under
  `.aw/workflow-artifacts/assess-*/` show a genuinely useful format (concern/scope, method, verdict
  rationale, what was intentionally NOT done and why, assumptions, open questions for the user). This
  plan should REUSE that VOCABULARY (the field shape) rather than invent a new one.
- `.aw/workflow-artifacts/` is gitignored (`.gitignore:68`), but that is NOT a defect and E-05 must not
  "fix" it (F-7, corrected at review). The untracked projections are the deliberate "local authoritative
  run convention" and they already have a tracked counterpart: `set_records` writes a TRACKED walkthrough
  and `promote_local_checkpoints` promotes untracked decision state into it so a crash never loses a
  recorded decision. That module is also the SET-COORDINATION register, not the review path, and
  `write_local_projections` has no production caller. Reuse its format; leave its plumbing alone.
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
| F-1 | Self-resolution is already widespread and already unauditable. RE-MEASURED at review: the figures are a live measurement, not a constant, and they GREW between authoring and review, which strengthens rather than weakens the case. | plan text: 112 entries across 92 plans. Re-measured at `93da8af`: 115 `Resolution or deferral rationale: RESOLVED` entries across 95 plans; no consolidated view exists |
| F-7 | ADDED AT REVIEW (HIGH): E-05's "LOCATION DEFECT" premise is REFUTED, and acting on it would have damaged a working design. The untracked `decisions.md` is DELIBERATE, not a bug, and it already HAS a tracked counterpart: `set_records` writes a TRACKED walkthrough to `.aw/records/walkthroughs/` and `promote_local_checkpoints` exists specifically to promote an untracked decision checkpoint into it before releasing another lane, with the stated purpose that "a crash never loses a recorded decision". So the module already implements the disposable-projection-plus-durable-record convention this plan cites as its own precedent. Two further facts remove the motive entirely: `set_records` is the SET-COORDINATION register (execset Order 02), a different surface from the review path, and `write_local_projections` has NO production caller today (only two tests call it), so review decisions would never flow through it. E-05 rewritten to leave `set_records.py` untouched and to document the review path's own tracked source of truth instead. | `set_records.py:5-11` (module docstring naming the untracked dir "the local authoritative run convention"), `:166` `render_walkthrough`, `:200` `write_walkthrough` ("Write a TRACKED walkthrough"), `:411-441` `promote_local_checkpoints` ("so a crash never loses a recorded decision"); `grep -rn write_local_projections` finds only `tests/test_exec_set_workflow.py:74` and `tests/test_set_coordination.py:446` |
| F-8 | ADDED AT REVIEW (HIGH): E-06 required `aw check` to report the unescalated-irreversible case, but NO E-item created that rule and no sibling owns it, so the plan demanded validation evidence for a mechanism it never built. Verified the two siblings that touch `check_engine.py` cover different subjects: `plqjt7` the findings threshold, `7nkcgp` the dependency cascade; neither mentions decisions or `Reversible`. E-06 now builds `check.review-decision-unescalated` itself, and `check_engine.py` was added to `Scope-Paths`. | `plqjt7` Scope-Paths + Concern (threshold/blocking open question); `7nkcgp` Scope-Paths + Concern (dependency cascade); no occurrence of `Reversible` or `decision` in either plan's E-items |
| F-9 | ADDED AT REVIEW (HIGH): E-04 creates a NEW CLI namespace and would have been undeclarable within the stated fence. Verified `aw reviews` is not a valid top-level command and that sibling `15zvu6` does NOT add one (no `cli.py` in its `Scope-Paths`), so this verb brings the noun into existence. Every parser leaf MUST carry a `command_surface.COMMAND_INVENTORY` entry or `find_undeclared_leaves` reports it, yet `command_surface.py` was absent from `Scope-Paths`. Also note the declaration test is ALREADY RED at baseline with 59 undeclared leaves, so it cannot serve as a green gate. | `aw reviews decisions` -> `invalid choice: 'reviews'`; `15zvu6` Scope-Paths has no `cli.py`; `pytest tests/test_command_surface_declarations.py -m ''` at `f02c64e`: `AssertionError: 59 != 0` |
| F-10 | ADDED AT REVIEW (MED): the plan's Spec sync correctly flagged the command-surface requirement but pointed at the wrong test (`tests/test_cli_conformance_matrix.py`); the assertion that fails for an undeclared leaf is `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` via `find_undeclared_leaves`. Corrected so the executor runs the test that actually gates. | `test_command_surface_declarations.py:46-52` contains the `find_undeclared_leaves` assertion; the conformance matrix module enumerates leaves for a different purpose |
| F-2 | plan-review has never written a decisions register. | `.aw/workflow-artifacts/` has a `release-review` dir but no `plan-review` dir |
| F-3 | Even when written, the register is invisible to the repo. | `.gitignore:68` ignores `.aw/workflow-artifacts/`; `set_records.py:152-153` writes the register there |
| F-4 | The existing register format is good and worth reusing. | e.g. `.aw/workflow-artifacts/assess-bugs/20260715-205322/decisions.md` records scope, method, verdict rationale, deliberate non-actions with reasons, assumptions, and open questions for the user |
| F-5 | The resolve-before-refusing rule increases the volume of silent decisions, so the audit trail is a precondition for it, not a nicety. | Maintainer instruction 2026-08-29 requiring agents to find a strong recommended path before refusing |
| F-6 | Parity between the two review variants is a documented property that mechanical drift would break. | The plan-review-long manifest row states the two are kept in deliberate parity |

## Proposed changes (ordered, validatable)

1. Require a recorded decision for every self-resolved question, in both review variants (E-01, E-02).
2. Distinguish reversible from irreversible, and escalate the irreversible (E-03).
3. Give the maintainer one read-only command to audit decisions, creating and DECLARING the `reviews`
   CLI namespace (E-04).
4. Document the review path's tracked source of truth and leave the Set-coordination register alone
   (E-05, rewritten at review: there is no location defect to fix).
5. Prove all of it, adding the `aw check` rule the adversarial guard needs, with a firing guard (E-06).

## Deferred / out of scope (with reason)

- **Retro-recording the 112 existing self-resolutions.** Out of scope: they are already written as prose
  inside their plans' open-question sections, which is auditable if imperfect, and manufacturing typed
  decision rows from them would be re-authoring history rather than recording it.
- **The same treatment for EXECUTION-time decisions.** Partially deferred: this plan covers the review
  path, which is where the resolve-before-refusing rule bites hardest and where 112 instances already
  exist. Execution-time self-decisions deserve the same audit trail, but the executor writes into a
  plan's own V-item evidence, which is a different seam and a different instruction surface. Recorded
  here so it is not forgotten; a follow-up should cover it.
- **Un-ignoring `.aw/workflow-artifacts/`.** Explicitly rejected: it holds machine-local run noise, and
  tracking all of it would create leak and churn problems.
- **Any change to `set_records.py`.** Rejected at review (F-7). The drafted "location defect" does not
  exist: the untracked projections are deliberate, they already have a tracked walkthrough counterpart
  with a promotion path built so a crash never loses a decision, that module is the Set-coordination
  register rather than the review path, and its writer has no production caller. Reuse its field
  vocabulary; do not touch its plumbing. If a real gap turns up in the Set path, file a backlog item.
- **Gating on decisions.** Out of scope and now RESOLVED rather than open (OQ-01): an unescalated
  irreversible decision is REPORTED by the new `check.review-decision-unescalated` rule at warning
  severity, but nothing blocks, because `plqjt7` owns the gating machinery and GUIDING_PRINCIPLES 6 warns
  against gold-plating a third overlapping enforcement path. E-03's escalation-at-decision-time is the
  preventive control; the check is the backstop.

## Scope check

- OVER-SCOPE FOUND AND REMOVED AT REVIEW: the drafted E-05 would have modified `set_records.py` to fix a
  "location defect" that does not exist (F-7). That module's untracked projections are deliberate and
  already paired with a tracked walkthrough plus a promotion path, it serves Set coordination rather than
  the review path, and its writer has no production caller. E-05 now documents the review path's own
  tracked source of truth and explicitly leaves `set_records.py` alone; `set_records.py` is NOT in
  `Scope-Paths`.
- UNDER-SCOPE FOUND AND FIXED AT REVIEW, two items. E-06 demanded `aw check` evidence for a rule no
  E-item built and no sibling owns (F-8), so E-06 now builds `check.review-decision-unescalated` and
  `check_engine.py` joined `Scope-Paths`. E-04 creates a new CLI namespace whose MANDATORY
  `COMMAND_INVENTORY` declaration was outside the fence (F-9), so `command_surface.py` and a new
  `agent_workflows/reviews.py` joined `Scope-Paths`, as did `.aw/records/reviews/README.md`, which the
  Spec sync section already required this plan to amend.
- Otherwise over-scope: none. Instruction text, one read-only verb, one advisory check rule, and tests.
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
- The new `aw reviews decisions` verb must be declared in `command_surface.COMMAND_INVENTORY`, and the
  assertion that actually gates an undeclared leaf is
  `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` via
  `find_undeclared_leaves`, NOT `tests/test_cli_conformance_matrix.py` as the draft stated (F-10,
  corrected). Add the declaration in the same pass as E-04, and remember that test is already red with 59
  pre-existing undeclared leaves (F-9), so the provable claim is "my leaf is not among them".
- `agent_workflows/reviews.py` is a NEW module hosting the read-only verb, keeping `cli.py` to
  registration and dispatch as the other owner verbs do.

## Open questions

### OQ-01: Should an unescalated irreversible self-decision block execution, or only be reported?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as REPORT-ONLY, from repository evidence rather
  than as a bare preference, so this plan carries no open question into approval. Three principles decide
  it. GUIDING_PRINCIPLES 10 ("Safety and reversibility") asks for "staged, reversible changes and a clear
  record of what was done", which is exactly a recorded, queryable decision row; it does NOT ask for a
  block. GUIDING_PRINCIPLES 6 (KISS, and the explicit warning that "fix by default invites gold-plating")
  argues against adding a second enforcement gate when a sibling in the same Set already owns the gating
  machinery: `plqjt7` (Order 02) holds the threshold gate and `7nkcgp` (Order 03) the dependency cascade,
  and neither mentions decisions, so a blocking rule here would be a third, overlapping enforcement path.
  GUIDING_PRINCIPLES 11 supports the shape actually chosen: the deterministic part (detecting an
  unescalated `Reversible: no` row) belongs in a tested check with an `--agent` mode, which is what E-06
  now builds. The plan's own Scope check already states detection-after-the-fact as the honest claim, and
  E-03 independently requires the irreversible case be escalated at DECISION time, which is the real
  preventive control; the check is the backstop that catches a reviewer who skipped it. Note the residual
  risk plainly: report-only means a reviewer who both skips E-03's escalation and ignores the warning
  still proceeds. If that is observed in practice, the fix is to raise this ONE rule's severity, not to
  add a gate. Revisit then.

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
  - Required evidence: paste `git diff --stat -- agent_workflows/set_records.py` showing it is UNMODIFIED,
    since E-05 was rewritten at review to leave that module alone (F-7). Paste the evidence that refutes
    the original premise, so the record shows WHY it was not "fixed": the `promote_local_checkpoints`
    docstring and the `write_walkthrough` "Write a TRACKED walkthrough" line, plus a grep showing
    `write_local_projections` has no production caller. Then paste the README text documenting that the
    tracked `.review.md` `## Decisions` section is the review path's source of truth and that the
    Set-coordination register is a separate surface. Confirm `.aw/workflow-artifacts/` is still ignored.
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
