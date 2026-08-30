# IPD: Unfixed findings at or above the threshold must carry a blocking open question

- Date: 2026-08-29
- Kind: child
- Concern: A High or Blocker finding left `open`/`deferred` gates nothing, because severity is invisible to every deterministic gate; only a `Blocking: yes` open question stops execution today.
- Scope: Add ONE consistency rule so an unfixed finding at or above the configured threshold must carry a matching blocking open question, and make plan-review emit the findings artifact. Deliberately adds NO second enforcement gate: it reuses the pre-execution open-question gate that already works. Dependency cascade is `7nkcgp` (Order 03).
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, agent_workflows/ipd_schema.py, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, .aw/records/reviews/README.md, tests/test_review_findings_gate.py, tests/test_plan_review_parity.py
- Item-Dependencies: executed:15zvu6
- Status: executed
- Set: revgate
- Order: 2
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: plqjt7
- Blocks-Release: next

## Workflow history
- 2026-08-30 executed (opencode its_direct/pt3-claude-opus-5-1m-us): Added check.review-finding-unescalated on both aw check and aw ipd lint (review-finalize/pre-execution), reusing the pre-existing blocking-question gate rather than adding a second severity gate; absent artifact silent, malformed reported, off disables; both review variants now emit the typed record and escalate; 43 new tests, live-corpus delta zero.
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-30 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed in place

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored after the maintainer chose reuse of the existing gate over a second independent severity gate, preferring fewer pieces of code.
- 2026-08-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; F-6..F-10 added and fixed in place (wrong long-variant file; unspecified rule placement + missing RULE_REGISTRY registration + missing terminal grandfathering; unspecified fail-open/fail-closed; missing OQ->finding naming mechanism; live-state test risk + duplicate parity harness), F-2's "100% catch rate" overclaim corrected, F-3 re-measured, E-07/E-08 added, Scope-Paths corrected.

## Goal

Make an unfixed serious finding actually stop execution, by binding it to the one gate in this repo with
a demonstrated perfect catch rate, instead of building a parallel severity gate that would have to earn
that trust from scratch.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the consistency rule

- [x] E-01 Add a `check.review-finding-unescalated` rule that fires when a plan's CURRENT-round review
      findings (via `15zvu6`'s parser and `current_findings()`) contain a finding whose severity is at or
      above `findings_gate_threshold(repo_root)` and whose decision is `open` or `deferred`, but the plan
      has NO open question with `Blocking: yes` naming that finding id. Use `15zvu6`'s shared
      `is_gating(severity, threshold)` predicate; do NOT re-implement the severity comparison.
      WIRE IT AT A NAMED POINT, because the draft said only "beside the other cross-tree reference
      rules" and the two candidate points have DIFFERENT reach (F-6): the plans-type content path
      (`check_engine.py:430-476`) is reached by BOTH `aw check plans` and the `aw check all` fan-out
      exactly once, whereas the collisions-only block (`:1186-1214`) runs ONLY in the full sweep. Use
      the PLANS-TYPE CONTENT PATH beside `check_ipd_dependencies` (`:441`), matching the documented
      reasoning there ("every dependency source is an IPD"), which is equally true of a plan's review
      findings. Scope the rule to PENDING-lane plans, following the identical grandfathering precedent
      of `check_ipd_draft_ready` (`:866-867`) and `check_lifecycle_transitions` (`:918-922`), so the
      417-file corpus of terminal plans is never retroactively litigated.
      ALSO register the rule id in `RULE_REGISTRY` (`check_engine.py:85-171`). This is NOT optional
      bookkeeping: an unregistered id silently falls back to `_DEFAULT_RULESPEC` (`:173`) with an EMPTY
      invariant id, so the finding would carry no assurance/determinism classification while the
      module's own comment claims no rule is "never SILENTLY unclassified". Classify it
      `error`/`ASSURANCE_REPOSITORY`/`DET_DETERMINISTIC`; state which catalog invariant it traces to,
      or `""` with a one-line reason if none fits.
  - Depends on: none
  - Expected outcome: an unescalated gating finding is reported by `aw check plans` AND `aw check all`;
    an escalated one is not; a terminal-dir plan is never flagged; the rule id resolves through
    `rule_spec()` to a real RuleSpec rather than the default.
  - Execution state: performed

- [x] E-02 Add the SAME rule to `ipd_lint` at the `review-finalize` and `pre-execution` checkpoints, so
      the coupling is enforced at the moment it matters rather than only in a repo-wide sweep. Reuse the
      already-parsed `doc.open_questions` list (`ipd_lint.py:162`, populated at `:258`) for the
      open-question side; do not re-parse the plan.
      PUT IT IN `lint_file`, NOT IN `lint_text`. `lint_text` is documented PURE (`ipd_lint.py:951`, "no
      I/O") and the findings live in a SEPARATE FILE under `.aw/records/reviews/`, so this check cannot
      be performed there without breaking that contract (F-5). The established precedent is exact: the
      Item-Dependencies RESOLUTION checks were deliberately moved to `lint_file` for the same reason
      (`ipd_lint.py:1017-1057`, "lint_text is PURE, so it only performs the SYNTAX-level checks here").
      Follow the same shape: gate on the checkpoint set, derive `repo_root` via the existing `.aw`/
      `.agents` ancestor walk (`:1029-1033`), and merge the extra diagnostics into the `LintResult`.
      Follow the `check_open_questions` diagnostic style (`ipd_lint.py:597`) so the message matches its
      siblings.
  - Depends on: E-01
  - Expected outcome: `aw ipd lint --phase pre-execution` and `--phase review-finalize` report an
    unescalated gating finding as a BLOCKING diagnostic; `lint_text` remains pure (no file reads added).
  - Execution state: performed

- [x] E-03 Document explicitly, in the rule's own comment and in the plan-review body, WHY there is no
      separate severity gate: the escalated open question is then caught by the EXISTING pre-execution
      gate at `ipd_lint.py:682-693` (`"unresolved blocking question at pre-execution"`).
      STATE THE EVIDENCE HONESTLY AND DO NOT REPEAT THE DRAFT'S OVERCLAIM. The draft called this a
      "measured 100% catch rate", which the corpus does NOT establish (F-7, corrected at review). What
      is actually true, and all that may be written: of 28 `Blocking: yes` open questions inside
      executed plans, all 28 are `resolved`, so no executed plan carries an unresolved blocking
      question. That is a CONSISTENCY fact, not a catch rate, for two reasons the comment must name:
      (a) `Blocking: yes` + `deferred` is ALREADY a structural error at every phase via a DIFFERENT
      rule (`ipd_schema.open_question_error`, `ipd_schema.py:1242-1243`), so `resolved` is the only
      legal terminal state and part of the 28/28 is a tautology of that rule; and (b) nothing in the
      corpus records whether the checkpoint gate ever actually STOPPED a run, so its catch rate is
      unmeasured, not perfect. Write the honest version, since this comment is the artifact a future
      maintainer will trust, and an overclaim there is worse than no claim.
      Also record the instruction a future reader must not "simplify" away: do NOT add the second,
      direct severity gate that was deliberately avoided (maintainer preference for fewer pieces of
      code, 2026-08-29), and if you believe it is needed, raise it rather than adding it silently.
  - Depends on: E-01
  - Expected outcome: the design decision is recorded where the next maintainer will read it, with a
    claim that survives being checked.
  - Execution state: performed

- [x] E-07 DECIDE AND ENCODE THE FAIL-OPEN / FAIL-CLOSED BEHAVIOR, which the draft left entirely
      unspecified even though it is this plan's single most consequential choice (F-8). Both host
      surfaces this rule rides SWALLOW EXCEPTIONS today: `lint_file`'s resolution block ends
      `except Exception: pass` (`ipd_lint.py:1054-1056`, "a repo-scan failure never masks the pure lint
      result") and every cross-tree rule in `check_types` is individually wrapped the same way
      (`check_engine.py:1191-1214`). Riding those unchanged means an unreadable or malformed review
      artifact silently PASSES the gate, which is precisely the failure this Set exists to remove.
      Encode these three cases distinctly, and make each one a deliberate, documented choice rather
      than an accident of the surrounding try/except:
      (a) NO review artifact for the plan -> the rule cannot fire and MUST stay silent. This is the
          honest consequence of the acknowledged under-scope (a reviewer who records nothing is outside
          deterministic reach) and it is also required for safety: no `.review.md` exists anywhere in
          the repo today and 417 plan files do, so a fail-closed absent case would mass-fail the entire
          corpus on day one.
      (b) Artifact PRESENT but unparseable/malformed -> FAIL CLOSED (report it). A file that exists but
          cannot be read is an error, not an absence, and treating it as an absence is the evasion path.
      (c) Threshold `off` -> the rule is disabled entirely, per `15zvu6` E-05.
      Do NOT rely on the ambient `except Exception: pass`; if the parse fails, that must produce a
      finding, not a silent pass.
  - Depends on: E-01, E-02
  - Expected outcome: absent is silent, malformed is reported, `off` disables; and none of the three
    depends on an enclosing exception swallow.
  - Execution state: performed

- [x] E-08 SETTLE HOW A BLOCKING OPEN QUESTION NAMES ITS FINDING, which OQ-01 requires but the draft
      gave no mechanism for (F-9). Measured at review: the IPD open-question parser already accepts an
      ARBITRARY `- Field: value` subfield and carries it into the parsed OQ dict
      (`ipd_lint.py:353-359`), and a plan carrying an extra `- Finding: F-3` line under an `### OQ-NN:`
      heading parses and lints `conforming` TODAY with no schema change (verified). So the mechanism
      exists; what is missing is the DECLARED convention.
      Adopt the typed subfield `- Finding: <F-id>` (not a free-text mention inside the rationale prose,
      which would make the rule a substring search and therefore both spoofable and brittle). Then
      resolve ONE follow-on question with evidence and record the answer: whether `- Finding:` must also
      join `ipd_schema.OQ_FIELDS` (`ipd_schema.py:1226-1231`, a closed 4-tuple) and the ipd-spec's
      open-question contract. Note that `OQ_FIELDS` has NO consumer in this repo (verified: it is
      defined and never read), so adding to it is documentation, not behavior; `open_question_error`
      (`:1234`) validates the four fields positionally via its own arguments and is unaffected by an
      extra subfield. Say which you did and why. Document the convention wherever an author will look
      for it, in the same pass.
  - Depends on: E-01
  - Expected outcome: the naming convention is declared, the rule matches a typed field rather than
    prose, and the schema/spec question is answered with cited evidence rather than left implicit.
  - Execution state: performed

### Task group 2: make reviewers emit the artifact

- [x] E-04 Amend `.aw/system/workflows/plan-review/plan-review.md` so Step 2.2 (Record findings,
      `plan-review.md:163-176`) writes the findings to the `.review.md` artifact defined by `15zvu6`, in
      addition to the report, and so Step 4 (Finalize, `:271-296`) requires that any finding left
      `open`/`deferred` at or above the threshold be raised as a `Blocking: yes` open question carrying
      the `- Finding: <F-id>` subfield from E-08. The workflow already instructs the reviewer to
      classify every finding with Severity and Decision (`plan-review.md:169-176`), so this makes an
      existing classification machine-readable rather than adding reviewer burden.
      Add the instruction WITHOUT weakening what is there: the Fix Bar (`:178-196`) and the
      severity/decision classification stay exactly as written. Note the rule this instruction must not
      contradict: `plan-review.md:397` states "Severity is for reporting only", and escalation is
      consistent with that (severity still does not decide whether to FIX; it decides whether an already
      UNFIXED finding must be surfaced as blocking) - say so explicitly in the added wording, or a future
      reader will read the two as being in conflict.
  - Depends on: none
  - Expected outcome: a plan-review run produces a `.review.md` and escalates its own unfixed gating
    findings; the Fix Bar and the reporting-only severity rule are intact and visibly reconciled.
  - Execution state: performed

- [x] E-05 Mirror E-04 into the long variant, which the workflow manifest states is kept in DELIBERATE
      PARITY with the single-file variant. An instruction added to one and not the other is a defect,
      not a partial improvement.
      EDIT THE CORRECT FILES. The draft named `plan-review-long/plan-review-long.md`, which is the
      92-line ORCHESTRATOR and contains neither a findings-recording step nor a finalize step (F-4,
      verified). The instructions actually live in the step files, mirroring the two sections E-04
      touches: `02-review-and-revise.md:18-37` ("1. Record findings", the severity/decision list) is
      E-04's Step 2.2 counterpart, and `03-resolve-and-finalize.md:54-68` ("2. Finalize plan state") is
      its Step 4 counterpart. Amend BOTH. Editing only the orchestrator would leave the long variant's
      reviewers with no instruction at all while a naive parity grep passed.
  - Depends on: E-04
  - Expected outcome: both variants carry equivalent emit-and-escalate wording, in the step files a
    long-variant reviewer actually loads.
  - Execution state: performed

### Task group 3: prove the gate fires

- [x] E-06 Write `tests/test_review_findings_gate.py` proving, at minimum: an unescalated `high`/`open`
      finding is reported by both `aw check` and `pre-execution` lint; the same finding WITH a matching
      blocking open question is NOT reported; a `medium` finding is ignored at threshold `high` but
      caught at threshold `medium`; threshold `off` disables the rule entirely; a finding marked `fixed`
      never triggers it; and a finding that round 1 left `open` but round 2 marked `fixed` does NOT
      trigger it (current-round semantics from `15zvu6` E-03). Add the E-07 cases: absent artifact is
      SILENT, malformed artifact is REPORTED. Add the E-01 reach cases: reported by `aw check plans` AND
      by `aw check all`, and NOT reported for a terminal-dir plan. Include the END-TO-END chain: an
      unescalated gating finding, once escalated into a blocking open question, is then caught by the
      PRE-EXISTING gate at `ipd_lint.py:682` - proving the reuse actually closes the loop rather than
      merely reporting.
      Also assert `lint_text` stayed PURE (the E-02 contract): a text-only lint of the same plan must
      NOT report the rule, since it cannot see the separate artifact.
      USE ISOLATED FIXTURE REPOS, NOT THE LIVE TREE. `tests/test_review_findings_gate.py` must build a
      tmp repo per case; asserting against this repository's own plans is a known defect class here
      (`i79rgh`, Order testinvoke-02, exists to fix exactly that), and a threshold/`project.json` test
      that reads the live config would be order-dependent and would break the moment a maintainer sets
      the key.
      Put the workflow-body PARITY assertions in `tests/test_plan_review_parity.py` rather than here:
      that file already owns single-file-vs-long parity for this exact pair and already asserts on
      `02-review-and-revise.md` and `03-resolve-and-finalize.md`
      (`tests/test_plan_review_parity.py:18-30, 195-208`), so a second parity harness would be the
      drift this repo's single-source rule forbids. Assert the emit-and-escalate instruction in
      `plan-review.md` AND in BOTH long-variant step files, so E-05 cannot silently drift.
  - Depends on: E-01, E-02, E-04, E-05, E-07, E-08
  - Expected outcome: every branch of the rule is covered from isolated fixtures, parity is enforced in
    the file that already owns parity, and the reuse chain is demonstrated working.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The pre-execution open-question gate already exists and is the thing being reused:
  `ipd_lint.py:682-693` blocks when `oq.get("Blocking") == "yes" and oq.get("Status") == "open"`.
- Open questions are parsed once into `List[Dict[str, str]]` (`ipd_lint.py:162`, `:258`) and diagnosed
  separately (`check_open_questions`, `:597`). This plan's rule belongs on the diagnose side, consuming
  the already-parsed list.
- `lint_text` is PURE by contract (`ipd_lint.py:951`) and the precedent for a repo-aware check is
  established: the Item-Dependencies resolution rules run in `lint_file` for exactly this reason
  (`:1017-1057`). This plan's rule needs a second FILE, so it belongs there too (see E-02).
- The OQ subfield parser is already open-ended: any `- Field: value` line under an `### OQ-NN:` heading
  is captured into the OQ dict (`ipd_lint.py:353-359`), so a `- Finding: F-3` subfield parses and lints
  `conforming` with NO schema change (verified at review). `ipd_schema.OQ_FIELDS` (`:1226-1231`) is a
  closed 4-tuple but has no consumer in this repo, so extending it is documentation, not behavior.
- Terminal-plan grandfathering is a settled pattern, not a judgement call: both `check_ipd_draft_ready`
  (`check_engine.py:866-867`) and `check_lifecycle_transitions` (`:918-922`) scope themselves to
  pending-lane plans so the terminal corpus is never retroactively litigated. With 417 plan files in
  tree, this rule must do the same.
- `RULE_REGISTRY` (`check_engine.py:85-171`) is the versioned rule contract, and its own comment states
  an unregistered id must never be silently unclassified (`:173`, `_DEFAULT_RULESPEC`). Registering the
  new id is therefore part of the rule, not a docs afterthought.
- Cross-tree rules ride surfaces that swallow exceptions (`check_engine.py:1191-1214`;
  `ipd_lint.py:1054-1056`). Fail-open is thus the DEFAULT unless deliberately overridden, which is why
  E-07 exists.
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
| F-1 | Severity is invisible to every gate today. CONFIRMED at review by re-running the measurement. | `grep -c` for `BLOCKER`/`HIGH`/`Severity`/`Remediation Risk` in `ipd_lint.py` + `check_engine.py` returns `0` for all four (re-measured at `364adcb`) |
| F-2 | The open-question gate exists. ITS CLAIMED "PROOF" IS WEAKER THAN THE DRAFT STATED, corrected at review: 28/28 blocking OQs in executed plans are `resolved` is a CONSISTENCY fact, not a catch rate. Part of it is tautological (`Blocking: yes` + `deferred` is already a structural error via a different rule, so `resolved` is the only legal terminal state), and nothing records whether the checkpoint gate ever actually stopped a run. The reuse is still the right design; the evidence for it must be stated honestly (E-03). | `ipd_lint.py:682-693` (the gate); measured at review: 28 blocking OQs across executed plans, all `resolved`; `ipd_schema.py:1242-1243` (the independent rule that forces `resolved`) |
| F-3 | Reviews ending with open questions and then executing is common, so the path is well travelled. RE-MEASURED at review; the plan's figures understate it. | plan text: 48 lines / 49 plans / 44 executed. Re-measured at `364adcb`: 93 `REVIEWED - OPEN QUESTIONS` lines across 51 plan files, 44 in `executed/` and 7 in `pending/` |
| F-4 | Reviewers already classify severity and decision, so the data exists in prose. | `plan-review.md:169-176` |
| F-5 | The measured gap is the COUPLING, not the gate: nothing forces an unfixed High to become a blocking question. | F-1 plus the absence of any rule naming severity in either gate module |
| F-6 | ADDED AT REVIEW (HIGH): the draft's E-05 named the WRONG FILE for the long variant. `plan-review-long/plan-review-long.md` is a 92-line orchestrator with no findings-recording step and no finalize step; the instructions E-04 amends live in the STEP files. Editing only the orchestrator would leave long-variant reviewers with no instruction while a naive parity check passed. E-05 now names both step files, and `Scope-Paths` was corrected. | `plan-review-long/plan-review-long.md` (92 lines, steps only listed at `:62-66`); the real sections are `02-review-and-revise.md:18-37` and `03-resolve-and-finalize.md:54-68` |
| F-7 | ADDED AT REVIEW (HIGH): the draft required writing an overclaim into the code. E-01's rule placement was also unspecified, and the two candidate wiring points have different reach: the plans-type content path is hit by both `aw check plans` and `aw check all`, the collisions block only by the full sweep. E-01 now names the plans-type path, requires pending-lane scoping per the two existing grandfathering precedents, and requires `RULE_REGISTRY` registration (an unregistered id silently falls back to a default with an empty invariant, contradicting the module's own no-silent-classification claim). | `check_engine.py:430-476` (plans-type content path) vs `:1186-1214` (collisions-only); `:866-867` + `:918-922` (pending-lane precedents); `:85-171` + `:173` (registry + default) |
| F-8 | ADDED AT REVIEW (HIGH): fail-open vs fail-closed was entirely unspecified, and both host surfaces default to fail-OPEN via `except Exception: pass`, so an unreadable review artifact would silently pass the very gate this Set adds. E-07 now separates the three cases: absent is silent (required, since zero `.review.md` files exist against 417 plans, so a fail-closed absent case would mass-fail the corpus), malformed is reported, `off` disables. | `ipd_lint.py:1054-1056`; `check_engine.py:1191-1214`; measured: 0 `.review.md` files, 417 `*.ipd.md` files |
| F-9 | ADDED AT REVIEW (MED, DE-RISKS OQ-01): OQ-01 requires the blocking question to NAME the finding id but the draft gave no mechanism, leaving the executor to invent one (likely a prose substring match, which is spoofable and brittle). Verified the mechanism already exists: the OQ parser captures arbitrary `- Field: value` subfields, and a plan carrying `- Finding: F-3` under an `### OQ-NN:` heading parses and lints `conforming` today with no schema change. E-08 declares the typed subfield and resolves the `OQ_FIELDS`/spec question with evidence. | `ipd_lint.py:353-359` (arbitrary subfield capture); measured: injecting `- Finding: F-3` yields `{'Finding': 'F-3', ...}` and `lint_text(..., 'review-finalize')` returns `conforming` with zero diagnostics; `ipd_schema.py:1226-1231` (`OQ_FIELDS`, no consumer in repo) |
| F-10 | ADDED AT REVIEW (MED): the draft's test plan risked the repo's known live-state defect class and a duplicate parity harness. E-06 now mandates isolated fixture repos (a threshold test reading the live `project.json` would be order-dependent and would break when a maintainer sets the key) and relocates the parity assertions into the file that already owns this exact parity pair. | `i79rgh` (Order testinvoke-02) exists to fix live-state-asserting tests; `tests/test_plan_review_parity.py:18-30` (owns both variants) and `:195-208` (already asserts on `02-review-and-revise.md`) |

## Proposed changes (ordered, validatable)

1. Add the consistency rule to `check_engine`'s plans-type content path, pending-lane scoped and
   registered in `RULE_REGISTRY`, using the shared `is_gating` predicate (E-01).
2. Enforce it at the two lint checkpoints via `lint_file`, keeping `lint_text` pure (E-02).
3. Record why no second gate exists, with an honest statement of the evidence (E-03).
4. Encode the absent / malformed / `off` behavior deliberately rather than inheriting fail-open
   (E-07).
5. Declare the `- Finding: <F-id>` subfield convention that OQ-01 depends on (E-08).
6. Make both review variants emit findings and escalate unfixed gating ones, editing the long
   variant's real step files (E-04, E-05).
7. Prove every branch from isolated fixtures, including the end-to-end reuse chain, with parity
   assertions in the existing parity test (E-06).

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
- **Retrofitting the 417 existing plan files.** Out of scope and deliberately unreachable: E-01 scopes
  the rule to pending-lane plans and E-07 makes an absent artifact silent, so no existing plan is
  flagged. This is the same grandfathering the two sibling rules already apply
  (`check_engine.py:866-867`, `:918-922`).
- **A direct prohibition on deferring a gating finding.** Not chosen: escalation, not prohibition, is
  the right shape, because the Fix Bar (`plan-review.md:188-196`) already makes a legitimately deferred
  gating finding rare and a hard prohibition would push a reviewer toward mis-classifying severity to
  get past it. Recorded here so the choice is visible rather than accidental.

## Scope check

- Over-scope: none. Two rule sites, three instruction bodies (one single-file plus the long variant's
  two step files), one new test file plus assertions added to the existing parity test.
- Under-scope: acknowledged, and WIDER than the draft admitted. This plan does NOT prevent a reviewer
  from mis-classifying a Blocker as a Medium, nor from recording no finding at all. Per E-07(a) an
  ABSENT review artifact is silent by design, so "reviewer writes no `.review.md`" is a fully open
  evasion path, not a corner case: it is the state of all 417 plans today. The honest claim is
  "a RECORDED unfixed gating finding must be escalated", not "unfixed gating findings are now caught".
  Closing the absent-artifact hole would require making emission itself gated, which no plan in this
  Set does; if that matters, it is a follow-on, and this plan should not be read as covering it.

## Required tests / validation

1. `python3 -m pytest tests/test_review_findings_gate.py tests/test_plan_review_parity.py` green, run
   BARE (the repo's `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not pass
   `-n0`, a second `-q`, or `-p no:randomly`).
2. Full default suite green with counts pasted, compared against the baseline at execution time.
3. The end-to-end chain demonstrated: unescalated gating finding reported -> escalated to a blocking
   open question -> caught by the pre-existing pre-execution gate.
4. Threshold behavior demonstrated at `medium`, `high`, `blocker`, and `off`.
5. NO-REGRESSION ON THE LIVE CORPUS demonstrated, not assumed: `aw check plans` and `aw check all` on
   THIS repository must report the same finding count before and after the change (417 plan files, zero
   `.review.md` files, so the correct delta is zero). A rule that adds findings to the existing corpus
   has failed its grandfathering requirement.
6. Fail-closed behavior demonstrated for a MALFORMED artifact, and fail-silent for an ABSENT one, as
   two separate pasted cases (E-07).

## Spec / documentation sync

- Three workflow instruction files change (E-04: `plan-review.md`; E-05: the long variant's
  `02-review-and-revise.md` and `03-resolve-and-finalize.md`); they are the instruction surface agents
  load. The orchestrator `plan-review-long.md` does NOT need editing (F-4/F-6).
- `.aw/records/reviews/README.md` (from `15zvu6`) must gain the escalation rule AND the E-07
  absent/malformed/`off` semantics, so the artifact's own documentation states both the obligation and
  the honest limit. It is in `Scope-Paths`.
- The rule id `check.review-finding-unescalated` is registered in `check_engine.RULE_REGISTRY` (E-01),
  which is where this repo's rule contract lives. Verified at review that there is NO separate
  prose catalog of rule ids to update: rule ids appear in `docs/cli-agent-protocol.md:87` and
  `docs/cli-migration.md:66` only as EXAMPLE payloads, not as an enumeration, so nothing there needs a
  new entry. Do not invent a rules-doc file; if you conclude one is needed, say so rather than adding it
  silently.
- The `- Finding: <F-id>` OQ subfield (E-08) may warrant a line in the ipd-spec's open-question contract
  (`.aw/records/specs/20260726-1340-01-ipd-spec.spec.md:26`). That spec is NOT in `Scope-Paths` and must
  not be edited by this plan; record the required amendment in the execution evidence so it is
  reconciled when the spec is next reviewed, following the same convention `7nkcgp` uses for spec
  `25kzda`.

## Open questions

### OQ-01: Should the rule require the blocking open question to NAME the finding id, or merely to exist?

- Blocking: no
- Status: resolved
- Owner: resolved during authoring
- Resolution or deferral rationale: RESOLVED - require it to NAME the finding id. A rule satisfied by any
  unrelated blocking question would be trivially defeatable and would produce false confidence: a plan
  with one unrelated blocking OQ would appear to have escalated every finding. Naming the id keeps the
  mapping one-to-one and auditable, and costs the reviewer nothing since it already assigns finding ids
  (`plan-review.md:169-176`, the `ID` column). MECHANISM ADDED AT REVIEW (F-9): the draft stated the
  requirement without saying HOW a question names a finding, which would have left the executor to
  invent a prose substring match. E-08 settles it: a typed `- Finding: <F-id>` subfield under the
  `### OQ-NN:` heading, which the existing parser already captures with no schema change
  (`ipd_lint.py:353-359`, verified at review).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `aw check plans` reporting `check.review-finding-unescalated` for a fixture
    with a `high`/`open` finding and no matching blocking question, AND paste the same fixture WITH the
    escalation showing the rule does NOT fire. Paste `aw check all` on the same fixture proving the
    rule is reached by the full sweep too (both surfaces, per F-6/F-7). Paste a TERMINAL-dir fixture
    with the same unescalated finding showing the rule stays SILENT (grandfathering proven, not
    assumed). Paste a Python session showing `check_engine.rule_spec("check.review-finding-unescalated")`
    returns a REGISTERED RuleSpec, not `_DEFAULT_RULESPEC`. Paste `grep -n` proving the rule calls
    `15zvu6`'s `is_gating` rather than comparing severities locally.
  - Observed evidence: the rule fires on an unescalated gating finding on BOTH surfaces, is silent when escalated, is silent for terminal-dir plans, and its id resolves to a registered RuleSpec.
    ```text
    ### UNESCALATED high/open, via the plans-type path  (check_types(repo, ["plans"]))
      aw check plans: 1 finding(s)
         check.review-finding-unescalated  review finding F-1 is high/open (at or above the `high`
         gate threshold) but no `Blocking: yes` open question names it
    ### SAME fixture via the FULL SWEEP  (check_types(repo, ["all"]))
      aw check all: 1 finding(s)
         check.review-finding-unescalated  review finding F-1 is high/open (at or above the `high`
         gate threshold) but no `Blocking: yes` open question names it
    ### ESCALATED (blocking OQ carrying `- Finding: F-1`): rule does NOT fire on either surface
      aw check plans: 0 finding(s)
      aw check all:   0 finding(s)
    ### TERMINAL-dir plan with the SAME unescalated finding -> SILENT (grandfathering PROVEN)
      executed/:      0 finding(s)
      superseded/:    0 finding(s)
      not-executed/:  0 finding(s)
    ### rule_spec() resolves to a REGISTERED RuleSpec, not the conservative default
      RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='')
      is _DEFAULT_RULESPEC? False    in RULE_REGISTRY? True
    ```
    Delegation to `15zvu6`'s shared predicate rather than a local severity comparison
    (`grep -n "is_gating\|_SEVERITY_RANK\|SEVERITIES" agent_workflows/check_engine.py`):
    ```text
    135:    # via the ONE shared `review_findings.is_gating` predicate, plus a literal finding-id ...
    2200:    Severity comparison is delegated to ``review_findings.is_gating``; this function does NOT
    2214:        otherwise slip past ``is_gating`` silently, which is exactly the hole being closed.
    2281:            if not _rf.is_gating(finding.severity, thr):
    ```
    The only executable reference is line 2281, the delegation itself; `_SEVERITY_RANK` and
    `SEVERITIES` appear NOWHERE in `check_engine.py`, so no severity ranking is re-implemented. Pinned
    by `RuleRegistrationTests.test_severity_comparison_is_delegated_not_reimplemented`, which greps the
    evaluator body and fails if `_SEVERITY_RANK`, `SEVERITIES.index`, or a literal `"blocker"` appears.
    Wiring point is the plans-type content path beside `check_ipd_dependencies`
    (`check_engine.py:471-484`), as E-01 mandates; the full sweep reports it EXACTLY ONCE
    (`RuleReachTests.test_reported_by_full_sweep_exactly_once`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `aw ipd lint --phase pre-execution` and `--phase review-finalize` on the
    unescalated fixture, showing the blocking diagnostic and a nonzero disposition; then paste both
    phases on the escalated fixture showing conforming. Paste `grep -n` showing it consumes
    `doc.open_questions` rather than re-parsing. Paste PROOF `lint_text` stayed pure: `grep -n` showing
    no file read was added inside `lint_text`, AND a direct `lint_text(...)` call on the unescalated
    plan text returning no such diagnostic (it cannot see the separate artifact). A version that works
    only because `lint_text` started reading files fails this item.
  - Observed evidence: both checkpoints report the rule as a blocking diagnostic, the escalated fixture is clean, and `lint_text` stays pure.
    ```text
    UNESCALATED  --phase review-finalize  disposition=error       rule reported=True
        check.review-finding-unescalated  review finding F-1 is high/open (at or above the `high`
        gate threshold) but no `Blocking: yes` open question names it
    UNESCALATED  --phase pre-execution    disposition=error       rule reported=True
        check.review-finding-unescalated  review finding F-1 is high/open (at or above the `high`
        gate threshold) but no `Blocking: yes` open question names it
    UNESCALATED  --phase pre-transition   disposition=error       rule reported=False
    ESCALATED    --phase review-finalize  rule reported=False
    ESCALATED    --phase pre-execution    rule reported=False
    ```
    `pre-transition` correctly does NOT report it (out of scope by design: execution already happened).
    The `disposition=error` on that row is from unrelated IPD-M101/IPD-H202 complaints about the
    minimal fixture stub, not from this rule.

    PURITY of `lint_text` PROVEN TWO WAYS. (1) A direct `lint_text` call on the same plan TEXT reports
    nothing, because it cannot see the separate artifact:
    ```text
    lint_text --phase review-finalize  rule reported=False
    lint_text --phase pre-execution    rule reported=False
    ```
    (2) No file read was added inside `lint_text`:
    ```text
    lint_text purity -> read_text: False | open(: False | evaluate_review: False
    ```
    Both are pinned as tests (`LintCheckpointTests.test_lint_text_stays_pure`,
    `test_lint_text_body_adds_no_file_read`). The check rides `lint_file`
    (`ipd_lint.py:_merge_review_escalation`), matching the Item-Dependencies-resolution precedent.

    CONSUMES THE ALREADY-PARSED OPEN QUESTIONS, no re-parse (`grep -n`):
    ```text
    1025:    doc = parse(text)                  # lint_file parses ONCE
    1121:                open_questions=doc.open_questions,   # the hook consumes that parse
    ```
    NOTE, and recorded as decision 02-plqjt7-D3: my first implementation called `parse(text)` a second
    time inside the hook, which is what E-02 forbids. `lint_text` returns only a `LintResult`
    (no parsed doc), so to share the parse honestly I added an OPTIONAL `doc=` keyword to `lint_text`
    (default `None` -> parses exactly as before) and `lint_file` now parses once and passes the same
    document to both sides. Purity is unaffected (a parsed value in, no I/O added) and all 119
    `tests/test_ipd_lint.py` tests remain green.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the recorded rationale from both the code comment and the workflow body.
    Confirm it (a) states the corpus fact as a CONSISTENCY fact and not as a catch rate, (b) names the
    tautology (`ipd_schema.py:1242-1243` already forces `resolved`), (c) admits the gate's actual catch
    rate is unmeasured, and (d) carries the do-not-add-a-second-gate instruction. If the text still
    says "100% catch rate" anywhere, this item FAILS: the overclaim was the finding (F-2).
  - Observed evidence: the rationale is recorded in the code comment AND the reviews README, stated as a consistency fact rather than a catch rate.
    The rationale is recorded in TWO places. (a) `agent_workflows/check_engine.py`, in the block
    header immediately above the rule ("WHY THERE IS NO SECOND, DIRECT SEVERITY GATE HERE"):
    ```text
    # THE EVIDENCE FOR THAT REUSE, STATED HONESTLY. Measured over this repo's executed plans: 28 of 28
    # `Blocking: yes` open questions are `resolved`, so no executed plan carries an unresolved blocking
    # question. That is a CONSISTENCY FACT, NOT A CATCH RATE, and it must not be written up as one, for
    # two reasons:
    #   (a) part of it is TAUTOLOGICAL. `Blocking: yes` combined with `deferred` is ALREADY a structural
    #       error at every phase via a DIFFERENT rule (`ipd_schema.open_question_error`,
    #       `ipd_schema.py:1242-1243`), so `resolved` is the only legal terminal state a blocking question
    #       can reach. The corpus could hardly show anything else.
    #   (b) nothing in the corpus records whether the checkpoint gate EVER ACTUALLY STOPPED A RUN. Its
    #       true catch rate is UNMEASURED, not perfect.
    # The reuse is still the right design (one mechanism, already wired into `begin`/`finalize`), but its
    # justification is "fewer moving parts", not "proven infallible".
    #
    # DO NOT "SIMPLIFY" THIS BY ADDING THE DIRECT SEVERITY GATE. A second gate that blocks on the finding
    # itself was CONSIDERED AND DELIBERATELY REJECTED (maintainer preference for fewer pieces of code,
    # 2026-08-29), not merely left undone. ... If you believe the
    # direct gate is needed anyway, RAISE IT rather than adding it silently.
    ```
    (b) `.aw/records/reviews/README.md`, section "Why escalation, and not a direct block on the
    finding", which states the same 28/28 figure as a consistency fact, names the tautology, admits the
    catch rate is unmeasured, and concludes "The justification for reuse is fewer moving parts, not
    proven infallibility."

    Checking the four required properties: (a) stated as a CONSISTENCY fact in both - yes; (b) names
    the tautology and cites `ipd_schema.py:1242-1243` - yes; (c) admits the actual catch rate is
    unmeasured - yes; (d) carries the do-not-add-a-second-gate instruction - yes, in the code comment.
    The forbidden overclaim is ABSENT from the whole tree:
    ```console
    $ grep -rn "100% catch rate" --include='*.py' --include='*.md' . \
        | grep -v '^\./\.aw/worktrees' | grep -v 'plqjt7.*\.ipd\.md'
    (no output)
    ```
    The phrase survives ONLY inside this plan's own F-2/E-03/V-03 text, where it is quoted as the
    overclaim to avoid. It appears in NO shipped artifact: not in `check_engine.py`, not in
    `ipd_lint.py`, and not in the reviews README or either review workflow.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the amended Step 2.2 and Step 4 wording, plus a `git diff` of the hunks
    proving the pre-existing Fix Bar (`plan-review.md:178-196`) and the severity/decision classification
    (`:169-176`) were NOT weakened. Paste the sentence reconciling escalation with "Severity is for
    reporting only" (`:397`); absent that reconciliation this item fails. Then paste a worked run
    showing a `.review.md` was emitted.
  - Observed evidence: Step 2.2 and Step 4 are amended additively, the Fix Bar and classification are intact, and the reporting-only rule is explicitly reconciled.
    Amended Step 2.2 of `.aw/system/workflows/plan-review/plan-review.md` (added after the existing
    Severity/Decision classification list, which is untouched):
    ```markdown
    Write the findings to BOTH places:

    1. The findings table in the final report (below).
    2. A typed review record, `.aw/records/reviews/<...>.review.md`, using the same columns.

    The record is what makes a severity readable by tooling. Before it, severity survived only as prose,
    so a `HIGH` left unfixed gated nothing. This is a transcription of the classification you already
    made, not a second classification.

    Append a new `## Round <n>` for a re-review rather than editing an earlier round: the gate reads only
    the CURRENT (last) round, so a finding you raised in round 1 and fixed in round 2 correctly stops
    counting against the plan.
    ```
    Amended Step 4 (Finalize), added as a new confirmation bullet:
    ```markdown
    - The typed review record was written, and every finding left `OPEN` or `DEFERRED` at or above the
      repository's gate threshold (`review_findings_gate.block_at` in `.aw/config/project.json`, default
      `HIGH`) is ALSO raised in the plan as an open question carrying `- Blocking: yes` and
      `- Finding: <ID>` naming that finding. `check.review-finding-unescalated` enforces this, and the
      escalated question is then caught by the existing `pre-execution` gate, so an unfixed serious
      finding actually stops execution instead of merely being reported.

      This does NOT contradict "Severity is for reporting only" below. Severity still does not decide
      whether to FIX anything: the Fix Bar alone does that, on Remediation Risk. Severity decides only
      whether a finding you have ALREADY decided not to fix must be surfaced as blocking. Reporting rule
      unchanged; escalation is about visibility of an unfixed finding, not about the fix decision.
    ```
    That second paragraph IS the required reconciliation with `plan-review.md`'s "Severity is for
    reporting only", and it is asserted mechanically by
    `ReviewFindingsEmitAndEscalateParityTests.test_escalation_reconciled_with_reporting_only_severity`.

    NOTHING WEAKENED, proven by the diff being purely ADDITIVE in both hunks:
    ```console
    $ git diff --numstat -- .aw/system/workflows/plan-review/plan-review.md
    24      0       .aw/system/workflows/plan-review/plan-review.md
    ```
    24 insertions, ZERO deletions, so no pre-existing line could have been altered or removed. The Fix
    Bar and the severity/decision classification are additionally pinned by
    `test_fix_bar_and_classification_not_weakened`, which asserts the literal Fix Bar sentence, the
    "Effort, time, cost, and tokens are never valid deferral reasons" rule, and both vocabularies still
    appear.

    Worked run showing an emitted artifact (the writer from `15zvu6` producing the record this
    instruction demands, then the gate reading it back):
    ```text
    wrote  <tmp>/.aw/records/reviews/20260829-demo-01-aaa111-gate.review.md
    parsed back: plan_id=aaa111  rounds=1  current_findings=1  (F-1 high/open)
    gate on it: check.review-finding-unescalated  review finding F-1 is high/open ...
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the amended wording from BOTH long-variant step files
    (`02-review-and-revise.md` and `03-resolve-and-finalize.md`) and a diff showing each is equivalent to
    its single-file counterpart. State explicitly that `plan-review-long.md` (the orchestrator) was
    correctly NOT the edit target, per F-6. State that parity was CHECKED, not assumed.
  - Observed evidence: both long-variant STEP files carry equivalent wording; the orchestrator was correctly not the edit target.
    `plan-review-long.md` (the 92-line ORCHESTRATOR) was correctly NOT the edit target, per F-6: it
    only lists the steps and contains neither a findings-recording nor a finalize section, so editing it
    would have left long-variant reviewers with no instruction while a naive parity grep passed. It is
    unmodified:
    ```console
    $ git diff --name-only -- .aw/system/workflows/plan-review-long/
    .aw/system/workflows/plan-review-long/02-review-and-revise.md
    .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md
    ```
    `02-review-and-revise.md` section "1. Record findings" gained the EMISSION wording, identical in
    substance to E-04's Step 2.2 (the numbered list drops the "(below)" back-reference, which does not
    apply in the long variant):
    ```markdown
    Write the findings to BOTH places:

    1. The findings table in the final report.
    2. A typed review record, `.aw/records/reviews/<...>.review.md`, using the same columns.

    The record is what makes a severity readable by tooling. Before it, severity survived only as prose,
    so a `HIGH` left unfixed gated nothing. This is a transcription of the classification you already
    made, not a second classification.

    Append a new `## Round <n>` for a re-review rather than editing an earlier round: the gate reads only
    the CURRENT (last) round, so a finding you raised in round 1 and fixed in round 2 correctly stops
    counting against the plan.
    ```
    `03-resolve-and-finalize.md` section "2. Finalize plan state" gained the ESCALATION bullet, matching
    E-04's Step 4 including the reporting-only reconciliation (re-flowed to the section's
    semicolon-terminated bullet style):
    ```markdown
    - the typed review record was written, and every finding left `OPEN` or `DEFERRED` at or above the
      repository's gate threshold (`review_findings_gate.block_at` in `.aw/config/project.json`, default
      `HIGH`) is ALSO raised in the plan as an open question carrying `- Blocking: yes` and
      `- Finding: <ID>` naming that finding. `check.review-finding-unescalated` enforces this, and the
      escalated question is then caught by the existing `pre-execution` gate, so an unfixed serious
      finding actually stops execution instead of merely being reported. This does NOT contradict
      "Severity is for reporting only": severity still does not decide whether to FIX anything (the Fix
      Bar alone does that, on Remediation Risk), only whether a finding you have ALREADY decided not to
      fix must be surfaced as blocking;
    ```
    Both hunks are purely additive:
    ```console
    $ git diff --numstat -- .aw/system/workflows/plan-review-long/
    13      0       .aw/system/workflows/plan-review-long/02-review-and-revise.md
    9       0       .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md
    ```
    PARITY WAS CHECKED, NOT ASSUMED, and the check was OBSERVED FAILING (see V-06 for the two negative
    controls): removing the escalation from `03` alone failed 2 assertions, and removing the emission
    from `02` alone failed 1, each restored to green.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the test file result with counts, and paste each of these cases individually
    so none is vacuous: unescalated caught; escalated not caught; `medium` ignored at `high` but caught
    at `medium`; `off` disables; `fixed` never triggers; round-2-fixed does not trigger. Then paste the
    END-TO-END chain output proving the escalated question is caught by the pre-existing gate at
    `ipd_lint.py:682`. Paste `grep -n` proving every fixture is a tmp repo and NO assertion reads this
    repository's live plans or live `project.json` (the `i79rgh` defect class). Finally paste the parity
    assertion in `tests/test_plan_review_parity.py` FAILING with the instruction removed from one
    variant, and passing when restored. A guard never observed failing is not accepted.
  - Observed evidence: 59 tests pass and every required case is shown individually, including the end-to-end reuse chain and two observed guard failures.
    ```console
    $ python3 -m pytest tests/test_review_findings_gate.py tests/test_plan_review_parity.py
    bringing up nodes...
    ...........................................................              [100%]
    59 passed in 2.45s
    ```
    (39 in the new gate file, 20 in the parity file. Run BARE, per the plan.)

    EACH REQUIRED CASE INDIVIDUALLY, so none is vacuous:
    ```text
    unescalated caught                : 1 finding  check.review-finding-unescalated (F-1 high/open)
    escalated NOT caught              : 0 findings
    medium @ threshold high           : 0 findings
    medium @ threshold medium         : 1 finding  (F-1 medium/open)
    medium @ threshold blocker        : 0 findings
    threshold off                     : 0 findings  (rule disabled)
    decision `fixed`                  : 0 findings
    round1 open -> round2 fixed       : 0 findings  (current-round semantics)
    round1 fixed -> round2 open       : 1 finding   (converse: reopened is live again)
    decision `deferred`               : 1 finding   (a deferral is unfixed and must gate)
    ```
    END-TO-END CHAIN, proving the reuse closes the loop rather than merely reporting
    (`EndToEndReuseChainTests.test_escalation_is_then_caught_by_the_preexisting_pre_execution_gate`):
    ```text
    step 1  unescalated, --phase pre-execution:
              check.review-finding-unescalated  reported   ; IPD-S404 absent
    step 2  add `### OQ-01` with `- Blocking: yes` + `- Finding: F-1`
    step 3  same plan, --phase pre-execution:
              check.review-finding-unescalated  ABSENT
              IPD-S404  OQ-01: unresolved blocking question at pre-execution
              disposition=error
    ```
    IPD-S404 is the PRE-EXISTING gate at `ipd_lint.py:681-693`, untouched by this plan. The test also
    asserts the loop is CLOSABLE (`test_the_loop_is_closable_by_resolving_the_question`): fixing the
    finding and resolving the question silences both, so no plan is permanently stuck.

    EVERY FIXTURE IS A TMP REPO; NO ASSERTION READS LIVE STATE (the `i79rgh` defect class):
    ```console
    $ grep -n "mkdtemp\|REPO_ROOT\|SOURCE_PLANS\|Path(\"\.aw" tests/test_review_findings_gate.py
    50:    d = Path(tempfile.mkdtemp(prefix="aw_revgate02_"))
    ```
    The ONLY repo construction is `mkdtemp`; `REPO_ROOT`, `SOURCE_PLANS`, and any literal `.aw` root
    path are absent, so no test reads this repository's plans or its live `project.json`. Every
    threshold case writes the key into its OWN fixture via `_set_threshold`, so the suite is
    order-independent and cannot break when a maintainer sets the real key. Each `_RepoCase` tears its
    tmp tree down.

    PARITY GUARD OBSERVED FAILING, then passing when restored (a guard never seen to fail is not
    accepted). Control 1, escalation removed from the long variant's `03` only:
    ```console
    $ python3 -m pytest tests/test_plan_review_parity.py -k ReviewFindingsEmitAndEscalate
    E  AssertionError: 'Severity is for reporting only' not found in '# Step 3: Resolve, finalize...'
       : 03-resolve-and-finalize.md must quote the reporting-only rule it reconciles with
    FAILED ...::test_escalation_requirement_in_both_variants
    FAILED ...::test_escalation_reconciled_with_reporting_only_severity
    2 failed, 2 passed in 1.86s
    ```
    Control 2, emission removed from the long variant's `02` only:
    ```console
    E  AssertionError: '.aw/records/reviews/' not found in '# Step 2: Review and revise...'
       : 02-review-and-revise.md must instruct the reviewer to write the typed review record
    FAILED ...::test_findings_record_emission_in_both_variants
    1 failed, 3 passed in 1.96s
    ```
    Restored (and both files verified byte-identical to their pre-control backups via `diff`):
    ```console
    $ python3 -m pytest tests/test_plan_review_parity.py
    ....................                                                     [100%]
    20 passed in 1.89s
    ```
    Parity assertions live in `tests/test_plan_review_parity.py`, the file that already owns this exact
    pair, and they target the long variant's STEP FILES rather than the orchestrator.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste three distinct runs on the SAME plan fixture: (a) with NO `.review.md`,
    showing the rule is SILENT; (b) with a MALFORMED `.review.md`, showing it is REPORTED (a silent pass
    here fails this item, since that is the evasion path F-8 identified); (c) with threshold `off`,
    showing the rule is disabled. Then paste the NO-REGRESSION check from the live corpus: `aw check
    plans` and `aw check all` finding counts on THIS repository before and after, which must be equal
    (417 plans, zero review artifacts). Paste `grep -n` showing the malformed case produces a finding
    from an explicit branch, not from an enclosing `except Exception: pass`.
  - Observed evidence: absent is silent, malformed is reported, `off` disables, and the live corpus shows a ZERO delta.
    THE THREE MODES, on the SAME plan fixture, varying only the artifact/threshold:
    ```text
    (a) NO .review.md          -> SILENT   : 0 finding(s)
    (b) MALFORMED .review.md   -> REPORTED : 1 finding(s)
          check.review-finding-unescalated  review artifact for plan aaa111 is malformed (REV-R001),
          so its findings cannot be checked for escalation
    (c) threshold off          -> DISABLED : 0 finding(s)
    ```
    The malformed finding is reported at the REVIEW path (the file to repair), not the plan path. A
    fourth case is also covered because it is the same evasion: an unrecognized SEVERITY (`hgih`) would
    slip past `is_gating` silently, so the parser diagnostic makes it a malformed-report too
    (`FailureModeTests.test_malformed_row_with_unknown_severity_is_reported`).

    THE MALFORMED BRANCH IS EXPLICIT, NOT AN ENCLOSING SWALLOW (`grep -n`):
    ```text
    2251:        doc = _rf.parse_review_file(review_path)
    2252:        if doc.diagnostics:
    2253:            # (b) present but malformed -> FAIL CLOSED. Reported at the REVIEW path, ...
    ```
    The finding comes from `if doc.diagnostics:` inside the evaluator. Pinned by
    `test_malformed_branch_is_explicit_not_an_exception_swallow`, which greps the evaluator body for
    that branch. `parse_review_file` never raises by contract (`15zvu6`), so the branch, not an
    exception handler, is what decides. The `except Exception: pass` in `_merge_review_escalation`
    covers only a repo-scan failure and is documented as NOT being the malformed path.

    NO-REGRESSION ON THE LIVE CORPUS, MEASURED BEFORE AND AFTER (not assumed):
    ```console
    $ aw check plans   BEFORE: 15 findings across 428 plans
    $ aw check plans   AFTER : 15 findings across 428 plans
                               15  check.lifecycle-transition-invalid
    $ aw check all     BEFORE: 95 findings          AFTER: 95 findings
       35  adopted-without-consumer
        3  backlog.summary-unsafe
       15  check.lifecycle-transition-invalid
        6  check.name-nonconformant
       28  check.setid-collision
        1  dangling-citation
        7  stale-state-to-promote
    $ diff baseline_check_all.txt after_check_all.txt
    *** BEFORE/AFTER IDENTICAL: zero drift on the live corpus ***
    ```
    Delta is EXACTLY ZERO and the per-rule breakdown is byte-identical, as required (428 plan files,
    zero `.review.md` files, so every live plan is the (a) absent case). Zero
    `check.review-finding-unescalated` findings appear in the live tree. Also verified against an
    isolated many-plan fixture (`GrandfatheringTests`): 12 pending + 10 terminal plans with no reviews
    produce 0 findings.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the declared convention text, and a plan fixture whose blocking OQ carries
    `- Finding: F-3` being MATCHED by the rule, alongside one whose blocking OQ names a DIFFERENT finding
    id showing it does NOT satisfy the requirement (proving the match is per-finding, per OQ-01, and not
    "any blocking question will do"). Paste `grep -n` proving the rule reads the typed subfield rather
    than substring-searching the rationale prose. State whether `- Finding:` was added to
    `ipd_schema.OQ_FIELDS`, with the reason and the cited evidence for the choice, and note the ipd-spec
    amendment that was recorded for later reconciliation rather than edited here.
  - Observed evidence: the convention is declared, matched per-finding as a typed field, and the OQ_FIELDS question is answered with cited evidence.
    THE DECLARED CONVENTION, in `agent_workflows/ipd_schema.py` above `OQ_FIELDS`:
    ```text
    #: `Finding` is the plqjt7 E-08 convention: a blocking question ESCALATING an unfixed review finding
    #: names it as `- Finding: F-3` (comma-separate several). `check.review-finding-unescalated` matches
    #: THIS TYPED FIELD, never the rationale prose - a substring search over prose would be spoofable by
    #: any incidental mention and brittle against rewording. It is OPTIONAL: only a question escalating a
    #: gating finding needs it.
    ```
    and, for authors, in `.aw/records/reviews/README.md` ("Enforcement: unfixed gating findings must be
    escalated") with a worked `### OQ-03:` example, plus the finalize step of BOTH review variants.

    MATCHED PER-FINDING, NOT "ANY BLOCKING QUESTION WILL DO" (this is OQ-01's requirement):
    ```text
    blocking OQ carries `- Finding: F-1`, finding is F-1  -> 0 findings  (SATISFIED)
    blocking OQ carries `- Finding: F-9`, finding is F-1  -> 1 finding   (NOT satisfied)
          check.review-finding-unescalated  review finding F-1 is high/open ... but no
          `Blocking: yes` open question names it
    blocking OQ with NO `- Finding:` subfield             -> 1 finding   (NOT satisfied)
    NON-blocking question naming F-1                      -> 1 finding   (NOT satisfied)
    prose mentioning "F-1" in the rationale, no subfield  -> 1 finding   (NOT satisfied)
    one question naming `- Finding: F-1, F-2` (2 findings)-> 0 findings  (both satisfied)
    `- Finding: f-1` (lowercase)                          -> 0 findings  (case-insensitive on the id)
    ```
    The prose case is the important negative: a substring search would have accepted it.

    READS THE TYPED SUBFIELD, NOT THE PROSE (`grep -n` in `check_engine.py`):
    ```text
    2146:        raw = str(oq.get("Finding", "")).strip()
    2150:            tok = token.strip().strip(".`").upper()
    ```
    The matcher reads only the `Finding` KEY from the parsed OQ dict. It never inspects
    `"Resolution or deferral rationale"` (absent from the function entirely), so prose cannot satisfy
    it.

    THE `OQ_FIELDS` QUESTION, ANSWERED WITH EVIDENCE (recorded in full as decision 02-plqjt7-D2):
    `Finding` WAS added to `ipd_schema.OQ_FIELDS`. Cited basis:
    ```console
    $ grep -rn "OQ_FIELDS" --include=*.py .
    ./agent_workflows/ipd_schema.py:1226:OQ_FIELDS: Tuple[str, ...] = (
    ```
    ONE hit, its own definition: the tuple has NO consumer, so adding to it is DOCUMENTATION, not
    behavior. `open_question_error` (`ipd_schema.py:1234`) validates its four fields POSITIONALLY via
    its own arguments and is unaffected by an extra subfield. Verified the subfield needs no schema
    change to work: a plan carrying `- Finding: F-1` parses to `{'Finding': 'F-1', ...}` and
    `check_open_questions` returns zero diagnostics
    (`FindingNamingConventionTests.test_finding_subfield_does_not_break_structural_lint`). The comment
    records both facts, including that `Finding` must stay if `OQ_FIELDS` is ever made a closed
    allowlist.

    SPEC AMENDMENT RECORDED FOR LATER RECONCILIATION, NOT EDITED HERE (the ipd-spec is deliberately not
    in `Scope-Paths`): `.aw/records/specs/20260726-1340-01-ipd-spec.spec.md:26` should gain a line
    naming the OPTIONAL `- Finding: <F-id>` open-question subfield and its meaning (it escalates a
    review finding at or above the gate threshold; matched as a typed field, never as prose). Same
    convention `7nkcgp` uses for spec `25kzda`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and requires explicit human approval before execution. `reviewed` means the
review occurred; it is NOT approval, GO, or permission to execute.

SEQUENCING: this plan depends on `executed:15zvu6` (Order 01), which supplies the `.review.md` parser,
`current_findings()`, `findings_gate_threshold`, and `is_gating`. Do NOT begin until `15zvu6` is in
`.aw/records/plans/executed/`; every E-item here consumes one of those symbols, so starting early means
inventing them twice.

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
