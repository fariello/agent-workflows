# IPD: Unfixed findings at or above the threshold must carry a blocking open question

- Date: 2026-08-29
- Kind: child
- Concern: A High or Blocker finding left `open`/`deferred` gates nothing, because severity is invisible to every deterministic gate; only a `Blocking: yes` open question stops execution today.
- Scope: Add ONE consistency rule so an unfixed finding at or above the configured threshold must carry a matching blocking open question, and make plan-review emit the findings artifact. Deliberately adds NO second enforcement gate: it reuses the pre-execution open-question gate that already works. Dependency cascade is `7nkcgp` (Order 03).
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/plan-review-long.md, tests/test_review_findings_gate.py
- Item-Dependencies: executed:15zvu6
- Status: to-review
- Set: revgate
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: plqjt7
- Blocks-Release: next

## Workflow history

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored after the maintainer chose reuse of the existing gate over a second independent severity gate, preferring fewer pieces of code.

## Goal

Make an unfixed serious finding actually stop execution, by binding it to the one gate in this repo with
a demonstrated perfect catch rate, instead of building a parallel severity gate that would have to earn
that trust from scratch.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the consistency rule

- [ ] E-01 Add a `check.review-finding-unescalated` rule that fires when a plan's CURRENT-round review
      findings (via `15zvu6`'s parser and `current_findings()`) contain a finding whose severity is at or
      above `findings_gate_threshold(repo_root)` and whose decision is `open` or `deferred`, but the plan
      has NO open question with `Blocking: yes` naming that finding id. Use `15zvu6`'s shared
      `is_gating(severity, threshold)` predicate; do NOT re-implement the severity comparison. Place the
      rule in `check_engine.py` beside the other cross-tree reference rules.
  - Depends on: none
  - Expected outcome: an unescalated gating finding is reported by `aw check`; an escalated one is not.
  - Execution state: pending

- [ ] E-02 Add the SAME rule to `ipd_lint` at the `review-finalize` and `pre-execution` checkpoints, so
      the coupling is enforced at the moment it matters rather than only in a repo-wide sweep. Reuse the
      already-parsed `doc.open_questions` list (`ipd_lint.py:162`, populated at `:258`) for the
      open-question side; do not re-parse the plan. Follow the existing `check_open_questions` shape
      (`ipd_lint.py:597`) so the diagnostic style matches its siblings.
  - Depends on: E-01
  - Expected outcome: `aw ipd lint --phase pre-execution` reports an unescalated gating finding as a
    blocking diagnostic.
  - Execution state: pending

- [ ] E-03 Document explicitly, in the rule's own comment and in the plan-review body, WHY there is no
      separate severity gate: the escalated open question is then caught by the EXISTING pre-execution
      gate at `ipd_lint.py:682-693` (`"unresolved blocking question at pre-execution"`), which has a
      measured 100% catch rate on the real corpus (28 of 28 blocking open questions inside executed
      plans were resolved before execution; zero slipped through). A future reader must not "simplify"
      this by adding the second gate that was deliberately avoided.
  - Depends on: E-01
  - Expected outcome: the design decision and its evidence are recorded where the next maintainer will
    read them.
  - Execution state: pending

### Task group 2: make reviewers emit the artifact

- [ ] E-04 Amend `.aw/system/workflows/plan-review/plan-review.md` so Step 2.2 (Record findings) writes
      the findings to the `.review.md` artifact defined by `15zvu6`, in addition to the report, and so
      Step 4 (Finalize) requires that any finding left `open`/`deferred` at or above the threshold be
      raised as a `Blocking: yes` open question in the reviewed plan. The workflow already instructs the
      reviewer to classify every finding with Severity and Decision (`plan-review.md:170-176`), so this
      makes an existing classification machine-readable rather than adding reviewer burden.
  - Depends on: none
  - Expected outcome: a plan-review run produces a `.review.md` and escalates its own unfixed gating
    findings.
  - Execution state: pending

- [ ] E-05 Mirror E-04 into `.aw/system/workflows/plan-review-long/plan-review-long.md`, which the
      workflow manifest states is kept in DELIBERATE PARITY with the single-file variant. An instruction
      added to one and not the other is a defect, not a partial improvement.
  - Depends on: E-04
  - Expected outcome: both variants carry equivalent emit-and-escalate wording.
  - Execution state: pending

### Task group 3: prove the gate fires

- [ ] E-06 Write `tests/test_review_findings_gate.py` proving, at minimum: an unescalated `high`/`open`
      finding is reported by both `aw check` and `pre-execution` lint; the same finding WITH a matching
      blocking open question is NOT reported; a `medium` finding is ignored at threshold `high` but
      caught at threshold `medium`; threshold `off` disables the rule entirely; a finding marked `fixed`
      never triggers it; and a finding that round 1 left `open` but round 2 marked `fixed` does NOT
      trigger it (current-round semantics from `15zvu6` E-03). Include the END-TO-END chain: an
      unescalated gating finding, once escalated into a blocking open question, is then caught by the
      PRE-EXISTING gate at `ipd_lint.py:682` - proving the reuse actually closes the loop rather than
      merely reporting. Assert BOTH workflow bodies contain the emit-and-escalate instruction (a parity
      assertion, so E-05 cannot silently drift).
  - Depends on: E-01, E-02, E-04, E-05
  - Expected outcome: every branch of the rule is covered, and the reuse chain is demonstrated working.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The pre-execution open-question gate already exists and is the thing being reused:
  `ipd_lint.py:682-693` blocks when `oq.get("Blocking") == "yes" and oq.get("Status") == "open"`.
- Open questions are parsed once into `List[Dict[str, str]]` (`ipd_lint.py:162`, `:258`) and diagnosed
  separately (`check_open_questions`, `:597`). This plan's rule belongs on the diagnose side, consuming
  the already-parsed list.
- plan-review ALREADY requires a Severity and a Decision on every finding
  (`plan-review.md:170-176`: severity `BLOCKER|HIGH|MEDIUM|LOW`, decision `FIXED|DEFERRED|OPEN|REPLAN`).
  This plan makes that existing classification durable; it does not invent a new reviewer obligation.
- plan-review's Fix Bar (`plan-review.md:178-197`) already says to fix everything unless Remediation
  Risk is Medium-High or High, and that effort/time/cost are never valid deferral reasons. So a
  legitimately deferred gating finding is already rare by contract, which is why escalation rather than
  outright prohibition is the right shape.
- The long variant is kept in deliberate parity per its manifest row, hence E-05 and the mechanical
  parity assertion in E-06.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Severity is invisible to every gate today. | `grep -c` for `BLOCKER`/`HIGH`/`Severity`/`Remediation Risk` in `ipd_lint.py` + `check_engine.py` returns `0` for all four |
| F-2 | The open-question gate exists and is proven. | `ipd_lint.py:682-693`; of 28 blocking open questions inside executed plans, ALL 28 were `resolved` before execution and zero reached execution unresolved |
| F-3 | Reviews ending with open questions and then executing is common, so the path is well travelled. | 48 `REVIEWED - OPEN QUESTIONS` history lines; 49 plans carry that verdict, 44 of them now `executed` |
| F-4 | Reviewers already classify severity and decision, so the data exists in prose. | `plan-review.md:170-176` |
| F-5 | The measured gap is the COUPLING, not the gate: nothing forces an unfixed High to become a blocking question. | F-1 plus the absence of any rule naming severity in either gate module |

## Proposed changes (ordered, validatable)

1. Add the consistency rule to `check_engine` using the shared `is_gating` predicate (E-01).
2. Enforce it at the two lint checkpoints where it matters (E-02).
3. Record why no second gate exists, with the evidence (E-03).
4. Make both review variants emit findings and escalate unfixed gating ones (E-04, E-05).
5. Prove every branch, including the end-to-end reuse chain (E-06).

## Deferred / out of scope (with reason)

- **A standalone severity gate that blocks directly on the finding.** Explicitly REJECTED, not merely
  deferred (maintainer preference for fewer pieces of code, 2026-08-29). The trade-off is recorded
  honestly: this design blocks on the DERIVED open question, one step removed from the finding, so its
  weakness is a reviewer who records the finding and omits the escalation. E-01/E-02 exist precisely to
  make that omission a deterministic error rather than a silent one.
- **Backfilling the 352 already-reviewed plans.** Out of scope, per `15zvu6`: their findings exist only
  in prose and scraping them is demonstrably unreliable.
- **Blocking on unresolved DECISIONS** (as opposed to findings). Owned by `c621h9` (Order 04), which
  deliberately keeps decisions report-only.
- **Gating anything at `pre-transition`.** Out of scope: by the time a plan is finalizing, execution
  already happened, so a gating finding needed to stop it earlier. `review-finalize` and
  `pre-execution` are the correct checkpoints.

## Scope check

- Over-scope: none. Two rule sites, two instruction bodies, one test file.
- Under-scope: acknowledged. This plan does NOT prevent a reviewer from mis-classifying a Blocker as a
  Medium, nor from recording no finding at all. It closes the "recorded but unescalated" hole only. A
  reviewer who never writes the finding is outside any deterministic reach, and saying otherwise would
  overclaim.

## Required tests / validation

1. `python3 -m pytest tests/test_review_findings_gate.py` green, run BARE (the repo's `addopts` already
   supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not pass `-n0`, a second `-q`, or
   `-p no:randomly`).
2. Full default suite green with counts pasted, compared against the baseline at execution time.
3. The end-to-end chain demonstrated: unescalated gating finding reported -> escalated to a blocking
   open question -> caught by the pre-existing pre-execution gate.
4. Threshold behavior demonstrated at `medium`, `high`, `blocker`, and `off`.

## Spec / documentation sync

- Both review workflow bodies change (E-04, E-05); they are the instruction surface agents load.
- `.aw/records/reviews/README.md` (from `15zvu6`) must gain the escalation rule, so the artifact's own
  documentation states the obligation.
- The rule ids (`check.review-finding-unescalated`) must be listed wherever `aw check` rules are
  documented; verify against the existing rule-id documentation and add it in the same pass as E-01.

## Open questions

### OQ-01: Should the rule require the blocking open question to NAME the finding id, or merely to exist?

- Blocking: no
- Status: resolved
- Owner: resolved during authoring
- Resolution or deferral rationale: RESOLVED - require it to NAME the finding id. A rule satisfied by any
  unrelated blocking question would be trivially defeatable and would produce false confidence: a plan
  with one unrelated blocking OQ would appear to have escalated every finding. Naming the id keeps the
  mapping one-to-one and auditable, and costs the reviewer nothing since it already assigns finding ids
  (`plan-review.md:170`, the `ID` column).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw check` reporting `check.review-finding-unescalated` for a fixture with a
    `high`/`open` finding and no matching blocking question, AND paste the same fixture WITH the
    escalation showing the rule does NOT fire. Paste `grep -n` proving the rule calls `15zvu6`'s
    `is_gating` rather than comparing severities locally.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw ipd lint --phase pre-execution` and `--phase review-finalize` on the
    unescalated fixture, showing the blocking diagnostic and a nonzero disposition; then paste both
    phases on the escalated fixture showing conforming. Paste `grep -n` showing it consumes
    `doc.open_questions` rather than re-parsing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the recorded rationale from both the code comment and the workflow body,
    and confirm it states the 28/28 measurement and the explicit instruction not to add a second gate.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the amended Step 2.2 and Step 4 wording, plus a `git diff` of the hunks
    proving the pre-existing Fix Bar and severity/decision classification were NOT weakened. Then paste
    a worked run showing a `.review.md` was emitted.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the corresponding wording from the long variant and a diff showing the two
    are equivalent. State that parity was CHECKED, not assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the test file result with counts, and paste each of these cases individually
    so none is vacuous: unescalated caught; escalated not caught; `medium` ignored at `high` but caught
    at `medium`; `off` disables; `fixed` never triggers; round-2-fixed does not trigger. Then paste the
    END-TO-END chain output proving the escalated question is caught by the pre-existing gate at
    `ipd_lint.py:682`. Finally paste the parity assertion FAILING with the instruction removed from one
    variant, and passing when restored. A guard never observed failing is not accepted.
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
with trade-offs for the maintainer to choose. A bare refusal, or an open question that restates the
obstacle without a recommendation, is not an acceptable outcome. Any question you resolve yourself while
executing MUST be recorded as a decision (see `c621h9`), so a wrong turn stays auditable.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents and runs are ACTIVE in
this checkout; verify the staged set before every commit with `git diff --cached --name-only` and never
stage, revert, or discard another party's work. Run the suite BARE. When every `V-*` item carries pasted
evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`.
