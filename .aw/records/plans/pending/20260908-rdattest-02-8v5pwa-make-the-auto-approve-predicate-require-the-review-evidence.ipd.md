# IPD: Make the auto-approve predicate require the review evidence IPD-M107 already demands

- Date: 2026-09-08
- Kind: child
- Concern: `plan_readiness.is_plan_review_approved` believes a `- Readiness:` field without checking that a review produced it. `IPD-M107` closed the LINT layer (a fabricated field is a blocking finding and `aw ipd begin` refuses), but the PREDICATE is unchanged and still returns True for a hand-written value, and that predicate is what `--full-auto` consumes to promote `reviewed -> auto-approved` (CORRECTED AT REVIEW: `auto-approved`, a shipped sibling ready-to-execute tier, NOT human `approved`; see E-05 and `set_plan_approved`'s docstring) and flip an item's queue action to `execute`. The defect is unchanged by that correction: an UNREVIEWED plan reaches an EXECUTABLE tier. So the artifact is caught while the DECISION stays credulous: the field is read FIRST and the history is consulted only when the field is ABSENT, which means a forged field short-circuits the very evidence check that would expose it. Measured live at review HEAD `84258553`: a plan with `- Readiness: go` and a history containing no review at all returns True.
- Scope: Make the predicate require review evidence in the plan's own history when the `- Readiness:` field is present, so field and history must AGREE. MECHANISM CORRECTED AT REVIEW: use the STRONGER discriminator already defined in this same module (`is_review_history_entry`), NOT `ipd_lint._REVIEW_EVIDENCE_RE`, because that pattern matches a bare MENTION anywhere in the history and therefore accepts three measured forgeries (PR-701); and do NOT import `ipd_lint`, whose dependency surface is far larger than this plan's F-5 claimed (PR-702). This adds no second definition of "attested" and no new import, so it is strictly better than either option the backlog item offered. Add the test the item calls the real deliverable: the predicate returns False for a forged field. Preserve every other decision this predicate makes (out-of-vocab refusal, absent-field prose fallback, the blocking-open-question refusal) and keep the module stdlib-cheap and driver-agnostic, since both host drivers import it.
- Scope-Paths: agent_workflows/plan_readiness.py, tests/test_plan_readiness.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: rdattest
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8v5pwa
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: 754txs

## Workflow history
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-701 (BLOCKER: chosen mechanism did not stop a forgery) through PR-706 all FIXED. Readiness go-pending-approval.

- 2026-09-10 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701..PR-706, all FIXED, no deferrals. Structural lint conformed at `author` and again at `review-finalize`. Typed record at `.aw/records/reviews/20260910-rdattest-02-8v5pwa-...review.md`.
  ONE FINDING IS A BLOCKER AND IT IS THE WHOLE REVIEW: THE CHOSEN MECHANISM DID NOT FIX THE DEFECT (PR-701). The plan reused `ipd_lint._REVIEW_EVIDENCE_RE`, which matches a MENTION anywhere in the history rather than an actual review record. I ran three forgeries: a `to-review` line saying "I mention plan-review in passing", a `draft` line containing the word `APPROVE`, and a non-review line containing `REJECT`. ALL THREE PASS, and each is exactly the forged field this plan exists to refuse. Since the authored tests covered only the bare no-evidence case, the suite would have gone green on a gate that still returned True, and the backlog item would have been closed. A security fix that looks done and is not is worse than an open item.
  THE CORRECT PRIMITIVE WAS ALREADY IN THE FILE BEING EDITED. `plan_readiness.is_review_history_entry` (`:355-375`) parses a record and requires a review token in the record's own status/workflow MIDDLE; it refuses all three forgeries and accepts a real `/plan-review` record, and it is ALREADY consumed by `newest_verdict` and `approval_refusals`. So it adds no second definition of "attested" and no import, dissolving both horns of the dilemma the backlog item posed (duplicate the rule versus import the lint module). The item's framing was reasonable and simply did not know the primitive existed.
  THE PLAN'S IMPORT-SAFETY CLAIM WAS FALSE AND WOULD HAVE BEEN ACTED ON (PR-702). F-5 said `ipd_lint` imports only stdlib plus `ipd_schema`/`term`; an AST walk shows it also imports `attention`, `check_engine`, `ipd_authoring`, `record_producers`, `renderers`, `result_types` inside functions, reaching `engine`, `artifact_core`, `plans`, `selectors`, `runner_shared`. Both drivers import `plan_readiness`, so the authored route would have put the CLI/renderer stack behind a hot predicate, violating the item's own stdlib-cheap constraint.
  THE SAFETY ARGUMENT WAS INVERTED, NOT JUST STALE (PR-703). The plan and the item both lead with "0 of 65 Readiness plans flip". The real count is 139, and zero flips under the AUTHORED mechanism is a SYMPTOM of that mechanism being too weak to bite. Under the corrected mechanism exactly ONE flips, and it is a true positive: `5e4sb6`'s newest record is an `approved` record, not a review, and its real verdict was REVIEWED - OPEN QUESTIONS while its field says `go`. That is a stronger argument for fail-closed, not a weaker one.
  THREE SMALLER CORRECTIONS. The drivers promote to `auto-approved`, never human `approved` (PR-704), which the Concern and Goal both got wrong; the defect survives the correction but the wording overstated it. The suite baseline was wrong in both halves and its real failure is caused by another party's gitignored `opencode-recovery/`, which an executor had an incentive to delete (PR-705). And the in-code documentation obligation is wider than stated, while four cited driver line numbers had already drifted (PR-706).
  OQ-02 ADDED, non-blocking: the corrected mechanism means lint and predicate now define "attested" differently, which contradicts this plan's original one-definition goal. Recorded with three costed routes and the position that the divergence is correct, since a lint nudge may be permissive and a security gate may not.
  DISCLOSURE: same repository and same model family as the plan's author, so this is closer to a self-review than an independent one.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `754txs`. NOTE ON THE GATE FIELD: this item carries NO `- Blocks-Release:`, so this plan inherits none; it is `Work-Kind: security` at `Priority: high` but the maintainer did not gate it, and I have not added a gate the item does not carry. NOTHING IN THIS ITEM IS OBSOLETE. Verified at HEAD `8b4e1570` by RUNNING it, not reading it: a fixture plan carrying `- Readiness: go` and a history whose only line is `- 2026-09-08 to-review (someone): authored, NO review ever happened.` yields `is_plan_review_approved(...) == True`. The decision order the item describes is intact at `plan_readiness.py:297-327`: `read_readiness` first (`:312`), return on a valid value (`:313-315`), refuse OUTRIGHT on a present-but-out-of-vocab value (`:316-320`), and fall back to prose ONLY when the field is absent (`:322-327`). FOUR LIVE CONSUMERS, both hosts, so the blast radius is real: `oc_runipd.py:2968` and `:6718`, `agy_runipd.py:1988` and `:3988`. TWO MEASUREMENTS THAT DE-RISK THIS CONSIDERABLY AND ANSWER THE ITEM'S OWN STATED COST. The item's honest worry is that "a legitimate review that wrote the field but whose history line does not match the evidence pattern would newly fail closed", and it treats that as the price of the fix. I MEASURED THE PRICE AND IT IS ZERO TODAY: across every tracked plan, 65 carry a `Readiness` field, and the number whose auto-approve verdict would FLIP from True to False under the proposed change is 0. So the fail-closed direction costs nothing against the current corpus, which converts the item's main objection from a real cost into a bounded risk about FUTURE phrasings. SECOND, the item asks (its option 2) whether the predicate should call the lint rule directly and worries about the import direction, since `plan_readiness` is consumed by both drivers and "whatever it imports must stay stdlib-cheap and driver-agnostic". I verified this is SAFE: `ipd_lint` imports only `argparse`, `re`, `pathlib`, `typing`, plus `ipd_schema` and `term`; it names no driver module; and it does NOT import `plan_readiness` (the only mentions are comments), so there is no cycle. The anti-divergence guard `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests::test_shared_rule_modules_are_not_modified_by_the_runner` forbids `ipd_lint`/`check_engine` NAMING a driver, which this change does not do. So option 2 is available and is what E-01 implements, giving ONE definition of "attested" rather than two.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the promotion decision as sceptical as the lint rule. A forged `- Readiness:` should not be able to carry a plan from `reviewed` to `approved` under `--full-auto`, and the fix should leave exactly one definition of what "a review attested this" means.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: require agreement between field and history

- [x] E-01 Make `is_plan_review_approved` (re-locate BY SYMBOL) require review evidence in the plan's own `## Workflow history` even when the `- Readiness:` field is present and valid, so field and history must AGREE. The GOAL is unchanged from authoring; the MECHANISM is corrected below, twice, and both corrections are measured.
  DO NOT REUSE `ipd_lint._REVIEW_EVIDENCE_RE`. USE `plan_readiness.is_review_history_entry`, WHICH IS ALREADY IN THIS FILE (review PR-701). This is the single most important change to this plan, because the authored mechanism does not actually stop a forged field. `_REVIEW_EVIDENCE_RE` is `(?i)\b(?:/?plan-review(?:-long)?\b|APPROVE\b|NO-GO\b|REJECT\b)` applied to the WHOLE history text, so it matches a MENTION anywhere in any record. MEASURED at review, all three by running them: a plan whose only history line is `- 2026-09-08 to-review (a): authored. I mention plan-review in passing.` PASSES it; so does `- 2026-09-08 draft (a): created. The word APPROVE appears here.`; so does a line containing `REJECT`. Each of those is exactly the forged field this plan exists to refuse, and each would still return True. By contrast `is_review_history_entry` (`plan_readiness.py:355-375`) parses the record and requires a review token in the record's own STATUS/WORKFLOW MIDDLE (between the date and the `(actor)`), so it returns False for all three forgeries and True for a real `- 2026-09-08 /plan-review (m): APPROVE ...` record. Verified at review.
  SO THE ITEM'S OPTION 2 IS NOT ACTUALLY AVAILABLE AS WRITTEN, AND OPTION 1 IS NOT WHAT IT LOOKS LIKE EITHER. The item framed the choice as "call the lint rule" versus "re-implement the check", and warned that re-implementing creates a second definition of "attested". That framing is right about duplication and wrong about the facts: the STRONGER discriminator is ALREADY DEFINED IN THIS VERY MODULE and is already consumed by `newest_verdict` and `approval_refusals`, so using it creates NO new definition at all. There is nothing to duplicate and no import to add. This is strictly better than both options the item offered, which is why it is chosen over them.
  DO NOT IMPORT `ipd_lint` FROM `plan_readiness`; the plan's F-5 safety claim is FALSE (review PR-702). F-5 states `ipd_lint` "imports only `argparse`, `re`, `pathlib`, `typing`, `ipd_schema` and `term`". MEASURED by AST at review: `ipd_lint` also imports `agent_workflows.attention`, `agent_workflows.check_engine`, `agent_workflows.ipd_authoring`, `agent_workflows.record_producers`, `agent_workflows.renderers` and `agent_workflows.result_types`. Those are function-scoped rather than module-scoped, which is why a casual read missed them, but they are real: `check_engine` imports `engine`, and `attention` pulls in `artifact_core`, `backlog`, `plans`, `releases`, `research_index`, `run_viewer`, `selectors`, `specs` and `runner_shared`. `plan_readiness` is imported by BOTH drivers and by `status_set`/`ipd_schema`, and the item's own constraint is that whatever it imports "must stay stdlib-cheap and driver-agnostic". An `ipd_lint` edge would pull the CLI/renderer stack behind a predicate two drivers call in a hot loop. Since the chosen mechanism is already local, this trap is avoided entirely rather than mitigated; the correction is recorded so nobody restores the import later believing F-5.
  KEEP THE ABSENT-FIELD PATH UNTOUCHED. Only the FIELD-PRESENT branch gains the agreement requirement. The absent branch already goes through `history_verdict_approves`, and E-02 owns proving it unchanged.
  - Depends on: none
  - Expected outcome: a plan with a valid `- Readiness:` and no REVIEW RECORD in its history returns False, including when the history merely MENTIONS `plan-review`/`APPROVE`/`REJECT` in a non-review record; a plan with a real review record returns True; NO new definition of "attested" is added, NO new import is added to `plan_readiness`, and `ipd_lint` is not imported.
  - Execution state: performed

- [x] E-02 PRESERVE THE OTHER THREE DECISIONS this predicate makes, each verified separately, because the risk here is widening or narrowing the gate by accident. (a) A PRESENT BUT OUT-OF-VOCAB value must still refuse OUTRIGHT and must NOT fall through to prose (`:316-320`); its comment explains why (falling back could approve a plan whose author meant `no-go`). (b) An ABSENT field must still fall back to the corrected newest history record via `history_verdict_approves(extract_newest_history_entry(text))` (`:323`), which is the back-compat path for plans reviewed before the field existed. (c) The unresolved-blocking-open-question refusal must still apply (`:325-326`). ALSO PRESERVE the documented boundary that this function does NOT read `- Status:` (`:304-305`): the caller independently requires `Status: reviewed`, and pulling that in here would widen the gate's meaning.
  - Depends on: E-01
  - Expected outcome: all four behaviors demonstrated individually against fixtures, unchanged from HEAD `8b4e1570`.
  - Execution state: performed

- [x] E-03 Re-measure the CORPUS EFFECT at execution time and report it, because this is a behavior change to a shipped gate and the maintainer's decision rests on its cost. Evaluate, over every tracked plan file, how many carry a `Readiness` field and how many would have their auto-approve verdict FLIP from True to False.
  THE AUTHORED NUMBERS ARE STALE AND THE COST IS NO LONGER ZERO (review PR-703). Re-measured at review HEAD `84258553`: 615 tracked plan files, **139** carry `Readiness` (not 65, more than double), and **127** return True today. Under the authored weak-pattern mechanism, 0 would flip, which is exactly why that mechanism is too weak to be worth shipping. Under the CORRECTED mechanism of E-01, **exactly 1** flips: `.aw/records/plans/pending/20260829-rununify-00-5e4sb6-unify-the-two-host-runners-onto-one-shared-runner-library-ph.ipd.md`.
  THAT ONE FLIP IS CLASSIFIED, so the executor is not left to judge it fresh: it is a GENUINE MISMATCH and refusing it is CORRECT. Its newest history record is `- 2026-09-03 approved (opencode ...)`, an APPROVAL record, not a review record, so nothing in its newest entry attests a readiness. Its review DID happen further down (`- 2026-08-30 reviewed (...): /plan-review: REVIEWED - OPEN QUESTIONS`), and note what that verdict says: OPEN QUESTIONS, whose own readiness would be NO-GO, while the plan carries `- Readiness: go`. So this is a plan whose field disagrees with its own review, which is precisely the class this plan exists to catch. It is already `Status: approved` by a human, so refusing AUTO-approval costs nothing operationally.
  DECIDE AND STATE WHETHER THE DISCRIMINATOR SCANS THE NEWEST RECORD ONLY OR ANY RECORD, because that choice is what produced the single flip and it is the one design question left in E-01. Scanning ANY record admits `5e4sb6` (it does contain a review record); scanning the NEWEST record only refuses it. RECOMMENDED: scan ANY record for the ATTESTATION question, because the question here is "did a review ever produce this field", not "what is the newest verdict" (which `newest_verdict`/`approval_refusals` already own and which would duplicate a second gate's job). Under that recommendation the corpus flip count is 0 and the forgeries are still refused, since a forged plan has NO review record anywhere. State which you implemented and re-measure accordingly; if you scan any-record, confirm the three measured forgeries still return False.
  If any OTHER plan flips, do not silently accept it: name it and say whether it is a genuine unattested field (correct to refuse) or a legitimate review the discriminator misses (a finding to report, not a reason to weaken the check).
  - Depends on: E-01
  - Expected outcome: a freshly measured count of Readiness-carrying plans and flipping plans, every flip individually classified, and the newest-record-versus-any-record choice stated with its measured flip count.
  - Execution state: performed

### Task group 2: the test the item calls the real deliverable

- [x] E-04 Add the forged-field test, which the item names explicitly: "add a test asserting the predicate returns False for a forged field. That test is the real deliverable; the incident showed the predicate returning True four times in a row with nothing behind it." Put it in `tests/test_plan_readiness.py`, which already owns this surface (`PredicateTruthTableTests` at `:319` is the natural home; the readiness-reader fixtures are at `:279-311`). Cover, as separate assertions: a forged `go` with no review evidence (False); the same plan with a `/plan-review` line added (True); an out-of-vocab value (False, and NOT via the prose path); an absent field with an approving history (True, back-compat preserved); an absent field with a rejecting history (False).
  ADD THE THREE MENTION-FORGERY CASES, WHICH ARE THE ONES THAT ACTUALLY DISCRIMINATE THE TWO MECHANISMS (review PR-701). Each of these PASSES the authored plan's `_REVIEW_EVIDENCE_RE` approach and therefore would have shipped a gate that still returns True; all three were run at review. (a) history whose only record is `- <date> to-review (a): authored. I mention plan-review in passing.` -> must be False. (b) `- <date> draft (a): created. The word APPROVE appears here.` -> must be False. (c) a non-review record containing `REJECT` -> must be False. Without these three, a passing suite would NOT prove the fix does what the plan claims, which is exactly the "test that restates current behavior" trap this E-item was written to avoid.
  PROVE THE TEST BITES, and be precise about which assertion proves what: assert the forged-field case FAILS against pre-change code (stash the fix and re-run). Note that the plain forged case would ALSO fail under the weak pattern, so it alone does not distinguish the mechanisms; the three mention-forgery cases are what prove the CHOSEN mechanism was necessary.
  - Depends on: E-01, E-02
  - Expected outcome: eight assertions covering the forged, attested, corrupt, back-compat-approve, back-compat-reject and THREE mention-forgery cases; the forged case fails before the fix and passes after; the mention-forgery cases demonstrably distinguish the chosen discriminator from the rejected pattern.
  - Execution state: performed

- [x] E-05 Confirm the four DRIVER call sites still behave, since the point of the change is to harden a decision those drivers make and a shared-module change reaches both hosts at once. Re-locate them BY SYMBOL (grep `is_plan_review_approved(`), because both files are the most heavily edited in the repository. THE PLAN'S LINE NUMBERS HAD ALREADY DRIFTED at review and are corrected here so a reader is not misled: they are `oc_runipd.py:2936` and `:6931` (not `:2968`/`:6718`), and `agy_runipd.py:1974` and `:3988` (not `:1988`).
  CORRECT THE PROMOTION THE PLAN DESCRIBES: IT IS `auto-approved`, NOT `approved` (review PR-704). This plan's Concern and Goal both say the predicate promotes `reviewed -> approved`, and the drivers do not do that. All four sites call `set_plan_approved`, whose docstring is explicit that it transitions to `auto-approved` and NOT to human `approved`, precisely so the machine never asserts the human-approval attestation (`oc_runipd.py:735-759`, fullauto `97df1z` OQ-02). `auto-approved` is a shipped sibling ready-to-execute tier (`ipd_schema.READY_TO_EXECUTE`) that the schema forbids from carrying the human `Approval:` field. The defect this plan fixes is REAL and unchanged (a forged field still licenses execution), but state it accurately: an unreviewed plan reaches an EXECUTABLE tier, without ever claiming a human approved it.
  FOR EACH SITE state what the call gates (the two `status == "reviewed" and full_auto` sites assign the queue status; the two `is_review and disposition in ("reviewed","approved")` sites also set `item["action"] = "execute"`) and confirm a newly-False verdict is SAFE: the plan is simply not auto-approved, with no exception and no mislabelled queue action. NOTE that two of the four wrap the call in `try/except Exception: pass`, so an exception there would be SILENTLY swallowed and the plan left un-promoted; that is fail-closed and therefore acceptable, but say so explicitly rather than relying on it, and confirm the other two are not similarly silent about a raise.
  DO NOT MODIFY THE DRIVERS: this is a read-and-report obligation, and the anti-divergence guard requires the shared rule to stay in the shared module.
  - Depends on: E-04
  - Expected outcome: a per-call-site account (symbol, line as found, what it gates, behavior on a False verdict, whether a raise is swallowed) confirming no driver edit is needed; the `auto-approved` versus `approved` distinction stated correctly; no driver file modified.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The predicate's decision order is deliberate and documented: valid field wins, out-of-vocab refuses outright, absence falls back to prose. `ipd_schema.py:230` and `:317` both record that ABSENT MEANS UNKNOWN and the consumer fails closed on None. The defect is not the order; it is that a valid-looking field is accepted with no provenance.
- `IPD-M107`'s rule is deliberately EVIDENCE-based rather than authorship-based, and `ipd_lint.py` records why at length: a review legitimately writes the field in the same pass that sets `reviewed`, and `plan-review-long` can leave a plan at `to-review` with a recorded NO-GO. So keying on history evidence admits both while refusing a value with nothing behind it. That reasoning transfers to the predicate verbatim, which is why sharing the predicate is right.
- THE EVIDENCE PATTERN IS A MENTION-MATCHER, NOT AN ATTESTATION CHECK. `_REVIEW_EVIDENCE_RE` (`ipd_lint.py:728-730`) matches `/plan-review`, `plan-review-long`, `APPROVE`, `NO-GO`, `REJECT` case-insensitively ANYWHERE in the history text. It is adequate for a LINT NUDGE (its actual job: catch an author who wrote the field with no review in sight) and inadequate for a SECURITY GATE. Do not reuse it here; see F-11.
- THE RIGHT PRIMITIVE IS ALREADY IN THE FILE: `plan_readiness.is_review_history_entry` (`:355-375`) parses a record and requires a review token in the record's own status/workflow MIDDLE. Its docstring calls this discriminator "THE CENTRAL CORRECTNESS REQUIREMENT of the approval gate" and records the measured reason a naive any-mention test is wrong: every pending plan matching `REJECT - NEEDS REPLAN` is a SUCCESSOR narrating its retired predecessor's rejection. That is the same class of false read this plan would have shipped in the opposite direction.
- `plan_readiness` ALREADY COMPOSES THREE ATTESTATION SOURCES in `approval_refusals` (`:424+`): the prose verdict via `newest_verdict`, the TYPED review artifact via `review_findings.subject_gating_blocks`, and unresolved blocking questions. So the module already knows how to be sceptical; `is_plan_review_approved` is the one predicate in it that is not.
- `ipd_lint` IS NOT STDLIB-CHEAP (F-5 corrected). Its module header is, but it imports `attention`, `check_engine`, `ipd_authoring`, `record_producers`, `renderers` and `result_types` inside functions, and those reach `engine`, `artifact_core`, `plans`, `selectors`, `runner_shared` and more. `plan_readiness` must not import it.
- `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` enforces that shared rule modules do not name a driver and that the runner stays a CONSUMER of shared rules. Respect it: the fix belongs in the shared module, not in either driver.
- `plan_readiness` exists BECAUSE this logic was duplicated once already: its docstring records that `is_plan_review_approved` and its history helper lived twice, once per driver. Adding a second definition of "attested" would repeat exactly that mistake.
- `IPD-M107` is already covered by tests at `tests/test_ipd_lint.py:255-334`, including a corpus scan, so the lint half needs no new coverage here.
- The `apprvguard` history in `plan_readiness.py:330-338` records the concrete harm this whole area exists to prevent: a blanket "I APPROVE all the reviewed IPDs" once swept five plans whose own review said `REJECT - NEEDS REPLAN` into `approved`. That is the same failure class as a forged field.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | THE DEFECT IS LIVE, measured by running it: a fixture plan with `- Readiness: go` and a history containing no review returns True from `is_plan_review_approved`. | measured at `8b4e1570` |
| F-2 | The field is read FIRST and short-circuits the history check, so a forged field bypasses the evidence the lint rule requires. | `plan_readiness.py:312-315`, with the prose fallback reached only at `:322-327` |
| F-3 | The predicate has FOUR live consumers across both hosts, so this is a shipped-gate change and not a local one. | `oc_runipd.py:2968`, `:6718`; `agy_runipd.py:1988`, `:3988` |
| F-4 | ~~THE ITEM'S STATED COST IS ZERO AGAINST THE CURRENT CORPUS: 65 carry a `Readiness` field and 0 would flip.~~ **SUPERSEDED AT REVIEW (PR-703): BOTH NUMBERS ARE STALE AND THE FRAMING WAS MISLEADING.** Re-measured at `84258553`: 615 tracked plan files, **139** carry `Readiness` (not 65), **127** return True today. Under the AUTHORED weak mechanism 0 flip, which is a symptom of that mechanism being too weak rather than evidence of safety. Under the CORRECTED mechanism exactly **1** flips (`5e4sb6`), and that flip is correct (see F-11). | re-measured at review over `git ls-files .aw/records/plans` |
| F-5 | ~~The item's option 2 is SAFE: `ipd_lint` imports only `argparse`, `re`, `pathlib`, `typing`, `ipd_schema`, `term`.~~ **FALSE, CORRECTED AT REVIEW (PR-702).** An AST walk shows `ipd_lint` ALSO imports `agent_workflows.attention`, `check_engine`, `ipd_authoring`, `record_producers`, `renderers` and `result_types`. They are FUNCTION-SCOPED (which is why a module-header read missed them) but real: `check_engine` imports `engine`; `attention` pulls in `artifact_core`, `backlog`, `plans`, `releases`, `research_index`, `run_viewer`, `selectors`, `specs`, `runner_shared`. Importing `ipd_lint` from `plan_readiness` would put the CLI/renderer stack behind a predicate both drivers call in a loop, violating the item's own stdlib-cheap constraint. Moot under the corrected mechanism, which adds no import at all. | AST walk at review |
| F-11 | **THE STRONGER DISCRIMINATOR ALREADY EXISTS IN THE FILE BEING EDITED, AND THE PLAN'S CHOSEN PATTERN DOES NOT STOP A FORGERY.** `_REVIEW_EVIDENCE_RE` matches a MENTION anywhere in the history: three forged fixtures (a `to-review` line mentioning `plan-review`, a `draft` line containing `APPROVE`, a non-review line containing `REJECT`) all PASS it, so the authored fix would still return True for each. `plan_readiness.is_review_history_entry` requires a review token in the record's own status/workflow MIDDLE and returns False for all three while accepting a real `/plan-review` record. It is already consumed by `newest_verdict` and `approval_refusals`, so using it creates no second definition and needs no import. | all four cases run at review; `plan_readiness.py:355-375` |
| F-12 | **THE DRIVERS PROMOTE TO `auto-approved`, NOT `approved`, so this plan's Concern and Goal misdescribe the gate they harden.** All four call sites call `set_plan_approved`, documented as deliberately transitioning `reviewed -> auto-approved` and never to human `approved`, so the machine never asserts the human attestation (fullauto `97df1z` OQ-02). `auto-approved` is in `ipd_schema.READY_TO_EXECUTE`, so the security defect is unchanged (an unreviewed plan becomes executable), but the plan's wording overstates it. | `oc_runipd.py:735-759`; `ipd_schema.py:265-267` |
| F-13 | THE PLAN'S FOUR CITED DRIVER LINE NUMBERS HAD ALREADY DRIFTED before execution: the real sites are `oc_runipd.py:2936`/`:6931` and `agy_runipd.py:1974`/`:3988`, not `:2968`/`:6718`/`:1988`/`:3988`. E-05 already says to re-locate by symbol, which is why this is an accuracy correction rather than a hazard. | grep at review |
| F-14 | TWO OF THE FOUR CALL SITES WRAP THE PREDICATE IN `try/except Exception: pass`, so a raise is silently swallowed and the plan is left un-promoted. That is fail-closed and therefore acceptable, but it means an implementation bug in the new code path could be INVISIBLE at those two sites rather than loud. E-05 must state this rather than rely on it. | `oc_runipd.py:2935-2941`; `agy_runipd.py:1973-1979` |
| F-15 | A THIRD, STRICTLY STRONGER ATTESTATION ALREADY EXISTS AND IS NEARLY UNIVERSAL, so it is worth naming even though this plan does not adopt it: `review_findings.review_attestation_missing` requires a CONFORMING typed `.review.md` record naming the plan as `Subject-Id`. Measured at review: of the 139 Readiness-carrying plans, **137** have one and only 2 do not. Not adopted here (see the deferred list) because it would make the predicate read the reviews tree, a materially bigger change than the item asked for. | measured at review; `review_findings.py:826+` |
| F-6 | The anti-divergence guard constrains the shape of the fix but does not forbid it: it requires shared rule modules not to NAME a driver, and requires the runner to be a consumer of shared rules. | `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests::test_shared_rule_modules_are_not_modified_by_the_runner` |
| F-7 | The lint half is genuinely done and well covered, so this plan is the missing half rather than a re-do: `IPD-M107` is asserted at six places including a corpus scan. | `tests/test_ipd_lint.py:255`, `:263`, `:266`, `:286`, `:304`, `:321`, `:334` |
| F-8 | This item carries NO `- Blocks-Release:` field, so no gate is inherited. Recorded because it is `Work-Kind: security` at `Priority: high` and a reader might expect one. | backlog `754txs` front matter |
| F-9 | The same failure class has already caused real harm here, which is why fail-closed is the right direction: a blanket approval once swept five REJECT-ed plans into `approved`. | `plan_readiness.py:330-338` |
| F-10 | The residual window the item describes is real and this plan closes it: the mitigation was the EXECUTION boundary (`aw ipd begin`), leaving the predicate reachable directly on an unlinted plan and by any future caller that does not lint first. | backlog `754txs`, "HONEST SCOPE OF THE CURRENT MITIGATION" |

## Proposed changes (ordered, validatable)

1. Require history evidence even when the field is present, using the in-module `is_review_history_entry` discriminator rather than `ipd_lint`'s mention-matcher, and without adding any import (E-01).
2. Preserve the out-of-vocab refusal, the absent-field prose fallback, the blocking-question refusal, and the no-`Status`-read boundary (E-02).
3. Re-measure the corpus flip count at execution time and classify every flip (E-03).
4. Add the forged-field test the item names as the real deliverable, proven to fail before the fix (E-04).
5. Report the behavior at all four driver call sites without modifying either driver (E-05).

## Deferred / out of scope (with reason)

- BOTH OF THE ITEM'S OFFERED OPTIONS, superseded at review by a third that is strictly better than either (PR-701). Option 1 (re-implement the check locally) was rightly rejected for creating a second definition of "attested". Option 2 (import and call the lint rule) is rejected because its pattern does not actually stop a forgery (F-11) and because the import is not cheap (F-5 corrected). The chosen route uses `is_review_history_entry`, ALREADY DEFINED IN THIS MODULE and already consumed by two of its functions, so it duplicates nothing and imports nothing. The item's dilemma was real but rested on not knowing that primitive existed.
- CHANGING WHAT `IPD-M107` ITSELF ACCEPTS, or making the lint rule share this predicate. Deliberately out of scope, and note the consequence honestly: after this plan the LINT layer keeps its looser mention-matcher while the PREDICATE uses the stricter discriminator, so the two layers no longer define "attested" identically. That is the correct trade for now (a lint nudge may be permissive; a security gate may not, and tightening `IPD-M107` would change a shipped lint contract and could newly fail plans in the tree), but it IS a divergence and a future reader should know it was chosen rather than overlooked. Raised as OQ-02.
- ADOPTING THE TYPED REVIEW RECORD as the attestation (`review_findings.review_attestation_missing`), which is strictly stronger than any history-prose check and is already nearly universal: 137 of the 139 Readiness-carrying plans have a conforming record (F-15). Not adopted because it would make this predicate read the reviews TREE (a repo-root-relative lookup) rather than the plan text alone, changing its signature and cost for both drivers, which is materially more than the item asked for. Named as the natural next hardening step rather than left undiscovered.
- MAKING THE PREDICATE READ `- Status:`. Explicitly documented as the caller's responsibility, and folding it in would widen the gate's meaning rather than harden its provenance.
- AUDITING OR REWRITING THE 65 PLANS that carry a `Readiness` field. None of them flips (F-4), and `IPD-M107` plus its corpus test already police the tree.
- HARDENING ANY OTHER `--full-auto` PROMOTION INPUT. The item is scoped to this predicate; a broader audit of what `--full-auto` trusts would be a legitimate but separate piece of work.

## Scope check

- Over-scope: ONE PATH BEYOND THE TWO DECLARED, added at execution and justified here rather than discovered later. `agent_workflows/plan_readiness.py` and `tests/test_plan_readiness.py` are as declared. The third is `tests/test_oc_runipd.py`, where `_repo_with_statuses`'s `reviewed` fixture gains ONE review history record. IT IS NOT OPTIONAL AND IT IS NOT SCOPE CREEP: without it this change silently makes `test_alias_refuses_a_reviewed_plan_even_with_full_auto_present` VACUOUS. That test pins an ORDERING (the `--action review is illegal` gate must fire BEFORE the auto-approval) via the assertion that the plan file still reads `- Status: reviewed`, and its own docstring calls that "the load-bearing one". The fixture carried a bare `- Readiness: go` over a history of only `approved`/`draft` records, so after this change the predicate can no longer clear it and the status survives whatever the ordering. MEASURED on the fixture: pre-change the predicate cleared it (True, assertion falsifiable), post-change it did not (False, assertion vacuous), and with the record prepended it clears it again (True). The edit is three lines of fixture plus a comment recording that measurement; it CHANGES NO ASSERTION and RELAXES NO GATE, it restores the reachability an existing assertion depends on. The alternative -- leaving it -- would ship a green suite hiding a disabled ordering check, which is precisely the "test that restates current behavior" trap E-04 was written to avoid, one layer out. A whole-suite scan for other affected fixtures found this one only; the other three approving-`Readiness:` fixtures in the suite are genuinely attested. The DRIVERS remain deliberately out of scope and unmodified: E-05 is read-and-report and the anti-divergence guard requires the rule to stay shared. `tests/test_oc_runipd.py` is a test fixture, not a driver.
- Under-scope, EXPANDED AT REVIEW so the residual gaps are named rather than discovered later: the lint rule is unchanged, so the two layers now define "attested" differently (OQ-02); no plan file is audited or rewritten, so `5e4sb6` keeps a `- Readiness: go` that its own review's REVIEWED - OPEN QUESTIONS verdict does not support (it is already human-`approved`, so nothing automated depends on the field, and correcting a third party's plan is outside this fence); the typed review record, which is strictly stronger and already covers 137 of 139 Readiness-carrying plans, is NOT adopted (F-15); and no other `--full-auto` promotion input is examined. The chosen mechanism also does NOT verify that the review's verdict was POSITIVE, only that a review record exists: a plan whose review said NO-GO but whose field says `go` is refused only if `- Readiness:` is out-of-vocab or the newest-record variant is chosen. That asymmetry is acceptable because `IPD-M107`, `approval_refusals` and human approval all sit on that path, but state it rather than implying the field is now fully trustworthy.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line and judge on the DELTA. THE AUTHORED BASELINE IS WRONG IN BOTH HALVES (review PR-705). Re-measured at HEAD `84258553`: `2 failed, 5957 passed, 3 skipped, 2 xfailed`, and the named `test_orchestrator_retirement` PASSES (`112 passed` in isolation). The two real failures are `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` and `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`; the second passes in isolation and fails on a 30-second subprocess timeout under `-n auto`, so treat it as load-sensitive, not as your regression. Compare failing NODE IDS, never totals.
- DO NOT TOUCH `opencode-recovery/`. The reporting-contract failure is caused by that GITIGNORED directory (`.gitignore:49`) holding another party's session transcripts that quote the reporting-contract prose. Per the shared-checkout rule it is not yours: do not delete, move, or clean it to green the suite.
- `python3 -m pytest tests/test_plan_readiness.py tests/test_ipd_lint.py tests/test_runner_item_dependencies.py` for the focused surface, the last of these because the anti-divergence guard constrains this change's shape.
- The E-03 corpus measurement, re-run at execution time and pasted.
- The forged-field reproduction run by hand before and after, showing True then False.

## Spec / documentation sync

No `.spec.md` file defines the auto-approve predicate's provenance requirement, so none is edited and none is declared in `Scope-Paths`. VERIFIED AT REVIEW rather than assumed.
THE IN-CODE DOCUMENTATION MUST BE CORRECTED BY E-01, and review found the obligation is WIDER than the plan stated. The plan names the module docstring and the `is_plan_review_approved` docstring (the "structured signal is authoritative and beats any prose" claim). Those are necessary but not sufficient: the SAME three-way ordering is asserted as shared house rule in at least three further places that will become misleading, and each says the field is authoritative with prose read only on absence: `newest_verdict`'s docstring ("`approval_refusals` consults the field FIRST and reaches this function only as a fallback, matching the three-way rule `is_plan_review_approved` already implements"), `approval_refusals`'s docstring item 1 ("in the SAME three-way order `is_plan_review_approved` uses: a valid field is authoritative and prose is never read"), and `ipd_schema.py:230` / `:317` ("ABSENT MEANS UNKNOWN ... the consumer `plan_readiness.is_plan_review_approved` FAILS CLOSED on None"). The `ipd_schema` notes stay TRUE (they are about absence) and need no edit; the two `plan_readiness` cross-references become FALSE for the field-present case and MUST be corrected, or the module will document a rule its own code no longer follows. NOTE `approval_refusals` is a DIFFERENT gate (human approval) whose ordering this plan does NOT change, so correct the cross-reference wording without implying its behavior changed.
The `AGENTS.md` guidance already tells agents never to hand-write `- Readiness:` and needs no change; this plan makes the gate enforce what that guidance already says.

## Open questions

### OQ-01: If a future legitimate review phrases its history line outside `_REVIEW_EVIDENCE_RE`, should the predicate widen or should the review be corrected?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, and RE-GROUNDED AT REVIEW because the numbers and the mechanism both changed. Of the 139 Readiness-carrying plans measured at review, exactly ONE flips under the corrected mechanism (`5e4sb6`), and it flips CORRECTLY: its newest record is an `approved` record rather than a review, and its actual review verdict was REVIEWED - OPEN QUESTIONS while the field says `go`. So the cost is not zero any more, but the one instance is a true positive, which strengthens rather than weakens the case. Fail-closed is correct here because the failure mode is a plan NOT being auto-approved, which a human resolves in one command, versus an unreviewed plan reaching an executable tier, which is the incident that created this Set. RECOMMENDATION: correct the review's phrasing rather than widen the discriminator. NOTE the widening argument is now WEAKER, not stronger, than when this question was written: E-01 no longer shares the lint pattern, so widening the discriminator would no longer weaken `IPD-M107`, but the discriminator it uses (`is_review_history_entry`) is consumed by `newest_verdict` and `approval_refusals`, so widening it would weaken the human-approval gate instead. Either way, widening reaches a second gate; the specific gate changed.

### OQ-02: Is it acceptable that the lint layer and the predicate now define "attested" DIFFERENTLY?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED AT REVIEW (PR-701), non-blocking, and stated because the plan's original design goal was explicitly "exactly ONE definition of what 'a review attested this' means" and the corrected mechanism does not deliver that. After this plan, `IPD-M107` keeps its permissive mention-matcher (`_REVIEW_EVIDENCE_RE`) while the auto-approve predicate uses the stricter record-parsing discriminator (`is_review_history_entry`). MY POSITION, and why I did not treat the divergence as a defect to fix here: the two layers have genuinely different jobs. A LINT NUDGE should be permissive, because its purpose is to tell an author "you wrote a review output while authoring" and a false positive there is friction on every plan. A SECURITY GATE must not be, because its false negative is an unreviewed plan reaching an executable tier, which is the incident that created this Set. Tightening `IPD-M107` to match would be a change to a shipped LINT contract, could newly fail plans already in the tree, and is covered by a corpus test with its own expectations, so it needs its own justification and its own measurement. THREE ROUTES if the maintainer wants convergence: (a) leave it, documenting that lint is a nudge and the predicate is the gate (recommended, and what this plan does); (b) tighten `IPD-M107` to use the discriminator, which needs a corpus measurement of newly-failing plans first; (c) adopt the typed review record in BOTH (F-15: 137 of 139 plans already have one), which is the strongest end state and the largest change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the forged-field reproduction BEFORE (True) and AFTER (False) using the same fixture, plus the same fixture with a `/plan-review` history line added showing True after the fix. PASTE THE THREE MENTION-FORGERY CASES (F-11) returning False after the fix, since those are what prove the chosen discriminator was necessary and the rejected pattern insufficient. Paste the `git diff` of the predicate. Paste a grep proving NO new definition of the evidence rule was added and that `plan_readiness` does NOT import `ipd_lint` (F-5 corrected, F-11). State which discriminator you called and, if you did not use `is_review_history_entry`, justify that against the three measured forgeries.
  - Observed evidence: DISCRIMINATOR USED: `plan_readiness.is_review_history_entry`, reached through a new in-module helper `history_has_review_record` that walks the BOUNDED history section and asks the existing discriminator of each record. `ipd_lint._REVIEW_EVIDENCE_RE` was NOT used and `ipd_lint` is NOT imported, per the review's PR-701/PR-702 corrections.

    SAME FIXTURE, BEFORE (lane base HEAD `b83a6cd9`, fix stashed) then AFTER. One script, six cases, run twice:

    BEFORE (pre-change code):
    ```
    A forged `go`, history has NO review at all                  -> True
    MENTION FORGERY (a): to-review record MENTIONING plan-review -> True
    MENTION FORGERY (b): draft record containing the word APPROVE -> True
    MENTION FORGERY (c): non-review record containing REJECT     -> True
    ATTESTED: same plan with a real /plan-review record added    -> True
    ATTESTED via a `reviewed` record                             -> True
    ```

    AFTER (fix applied):
    ```
    A forged `go`, history has NO review at all                  -> False
    MENTION FORGERY (a): to-review record MENTIONING plan-review -> False
    MENTION FORGERY (b): draft record containing the word APPROVE -> False
    MENTION FORGERY (c): non-review record containing REJECT     -> False
    ATTESTED: same plan with a real /plan-review record added    -> True
    ATTESTED via a `reviewed` record                             -> True
    ```
    All four forgeries flip True -> False while both attested shapes stay True, and the ONLY difference between row 1 and row 5 is one genuine `/plan-review` record. The three MENTION cases are what discriminate the mechanisms: each PASSES `_REVIEW_EVIDENCE_RE` (asserted mechanically by `test_the_rejected_mention_matcher_would_have_accepted_the_forgeries`), so the authored route would have shipped a gate still returning True for each.

    GIT DIFF OF THE PREDICATE (the behavioral change; the docstring corrections are in the same commit):
    ```
    @@ -362,7 +386,10 @@ def is_plan_review_approved(plan_path: Path) -> bool:

         readiness = _schema.read_readiness(text)
         if readiness is not None:
    -        # The STRUCTURED signal is authoritative and beats any prose in the history line.
    +        # The STRUCTURED signal decides the ANSWER and beats any prose verdict in the history, but it
    +        # must first be ATTESTED: a field no review produced asserts a clearance that never happened.
    +        if not history_has_review_record(text):
    +            return False
             return readiness in _schema.READINESS_APPROVABLE
         if _READINESS_FIELD_PRESENT_RE.search(text):
    ```
    plus the new `history_has_review_record`, whose body is seven lines over EXISTING primitives (`_history_section_lines`, `HISTORY_RECORD_RE`, `is_review_history_entry`):
    ```
        for line in _history_section_lines(text or ""):
            candidate = line.strip()
            if not HISTORY_RECORD_RE.match(candidate):
                continue
            if is_review_history_entry(candidate):
                return True
        return False
    ```

    NO NEW DEFINITION OF THE EVIDENCE RULE AND NO `ipd_lint` IMPORT. Every reference to the rejected pattern is PROSE; the only code references are the pre-existing primitives, and line 508 is the ONE new call:
    ```
    $ grep -n "ipd_lint\|_REVIEW_EVIDENCE_RE\|REVIEW_WORDS\|_REVIEW_PREFIX\|is_review_history_entry" agent_workflows/plan_readiness.py
    94:    "is_review_history_entry",                                              <- __all__, pre-existing
    325:    The test is the one the shipped pre-execution gate already uses (``ipd_lint.py``'s  <- prose, pre-existing
    423:# parentheses did not match at all, so `is_review_history_entry` returned False,         <- comment, pre-existing
    446:_REVIEW_WORDS = frozenset(("reviewed", "re-reviewed", "review", "re-review"))            <- pre-existing
    447:_REVIEW_PREFIX = "/plan-review"                                                         <- pre-existing
    450:def is_review_history_entry(entry: str) -> bool:                                        <- pre-existing
    468:        if lowered in _REVIEW_WORDS or lowered.startswith(_REVIEW_PREFIX):              <- pre-existing
    492:    IT REUSES :func:`is_review_history_entry` RATHER THAN A MENTION-MATCHER,             <- new prose
    493:    of the fix. ``ipd_lint._REVIEW_EVIDENCE_RE`` scans the WHOLE history text             <- new prose
    499:    `ipd_lint` for this (`ipd_lint` reaches `attention`, `check_engine`,                  <- new prose
    508:        if is_review_history_entry(candidate):                                  <- THE ONE NEW CALL
    523:    1. Only REVIEW records are consulted (:func:`is_review_history_entry`),               <- prose, pre-existing
    552:        if not is_review_history_entry(candidate):                      <- pre-existing (newest_verdict)
    601:       predicate rather than a third copy. Note it is STRICTER than ``ipd_lint``'s        <- prose, pre-existing
    ```
    An AST walk over the whole module (which catches FUNCTION-SCOPED imports, the shape that made F-5's claim false) shows the import set is unchanged and holds no `ipd_lint`:
    ```
    line 71   from __future__ import annotations
    line 73   import re
    line 74   from pathlib import Path
    line 75   from typing import Dict, List, Optional, Sequence, Tuple
    line 77   from agent_workflows import ipd_schema
    line 78   from agent_workflows.attention import _history_section_lines
    line 79   from agent_workflows.attention_contract import HISTORY_RECORD_RE
    line 656  from agent_workflows import review_findings         <- pre-existing, inside approval_refusals
    ```
    `ReadinessFieldMustBeAttestedTests::test_plan_readiness_does_not_import_ipd_lint` re-runs that AST walk as an assertion, so the constraint is ENFORCED rather than merely observed here.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: four separate demonstrations with their inputs and returned values: (a) an out-of-vocab `Readiness` returns False AND is shown not to consult the prose path; (b) an absent field with an approving history returns True; (c) an unresolved blocking open question returns False; (d) proof the function still does not read `- Status:` (for example a plan whose `Status` is `draft` but whose review approved returns True from this function alone).
  - Observed evidence: Four demonstrations, each over its own fixture, run as a separate script after the fix (the fifth is the unreadable-path case, kept because it is the other fail-closed boundary):
    ```
    (a) OUT-OF-VOCAB field over APPROVING prose (must be False, and must NOT use the prose path)
          is_plan_review_approved            -> False
          the prose path WOULD have approved  -> True (history_verdict_approves of the newest record)
          so a True prose answer + a False verdict proves the prose path was NOT taken
    (b) ABSENT field with an APPROVING history (must be True; back-compat preserved)
          -> True
          ABSENT field with a REJECTING history (must be False)
          -> False
    (c) unresolved BLOCKING open question under an approving verdict, NO field (must be False)
          -> False
          the same plan with the question RESOLVED (must be True)
          -> True
    (d) the function still does NOT read `- Status:`: a DRAFT plan with an ATTESTED go field
          Status: draft, Readiness: go-pending-approval, real review record -> True
          (True proves Status is still the CALLER's gate, not this predicate's)
    (e) unreadable path still fails closed (no crash) -> False
    ```
    READ EACH ONE AS THE CLAIM IT MAKES. (a) is the row that could have been faked: a False here is only meaningful beside the SECOND line showing the prose WOULD have said True, so the refusal can only have come from the out-of-vocab branch and not from prose agreeing by accident. Note the new provenance check does NOT reach this branch at all: `read_readiness` normalizes a corrupt value to None, so control never enters the field-present-and-valid arm. (b) proves only the FIELD-PRESENT branch gained the requirement, in both directions, so back-compat is not shown by a path that says yes to everything. (c) shows the fallback is still a CONJUNCTION and that resolving a question still clears it. (d) is the no-widening claim: a `draft` plan answers True from this function alone, so `Status` remains the caller's gate.

    ALSO PINNED BY THE SUITE, so these are regressions and not one-off observations: `PredicateTruthTableTests::test_the_whole_decision_order_answers_every_plan_shape` (16 rows, unchanged and still green), plus the new `test_the_corrupt_field_still_refuses_without_consulting_the_prose` and `test_the_predicate_still_does_not_read_status`, which assert (a) and (d) mechanically.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the freshly measured counts (plans carrying `Readiness`; plans returning True today; plans whose verdict flips) from a script run at execution time, not the authoring-time numbers and not review's (139/127/1 at `84258553`), since the corpus moves daily. State the newest-record-versus-any-record choice you implemented and its measured flip count. If any plan flips, paste its name and classify it. If `5e4sb6` flips, confirm the review classification (its newest record is an `approved` record, not a review, and its actual review verdict was REVIEWED - OPEN QUESTIONS against a `- Readiness: go` field, so refusing it is correct).
  - Observed evidence: CHOICE IMPLEMENTED: ANY RECORD, which is E-03's own recommendation. Measured at execution time over `git ls-files .aw/records/plans`, with the PRE-change decision order reimplemented locally in the same script so both answers come from one run rather than from two module versions:
    ```
    tracked plan files:                         694
    carry a `- Readiness:` field:               244
    PRE-change  is_plan_review_approved True:   238
    POST-change is_plan_review_approved True:   238
    FLIP True->False (newly refused):           0
    FLIP False->True (newly approved, must be 0): 0
    ```
    The corpus has MOVED SUBSTANTIALLY since review, which is why re-measuring was required rather than optional: 694 tracked plans against review's 615, and 244 carrying the field against review's 139 (authoring said 65). So all three authored/reviewed numbers are stale, and the flip count had to be re-derived.

    NOTHING FLIPS, AND THE ZERO IS NOT THE AUTHORED ZERO. The authored plan also predicted 0 flips, but under the WEAK mention-matcher, where 0 was a symptom of the mechanism not biting (PR-703). This 0 is under the STRICT discriminator, and it is measured alongside a second number that proves the mechanism does bite: a NEWEST-RECORD variant of the same rule flips 237 of the 238, because a reviewed plan's newest record is routinely a later `approved`/`executed`/maintainer record rather than the review. Both numbers from the same script:
    ```
    FLIP True->False, ANY-record:    0
    FLIP True->False, NEWEST-record: 237
    ```
    That contrast is the whole justification for the any-record choice and is recorded in `history_has_review_record`'s docstring so the next reader does not "tighten" it into a 237-plan lockout.

    `5e4sb6` DOES NOT FLIP, AND REVIEW'S CLASSIFICATION OF IT IS CONFIRMED-BUT-SUPERSEDED. Review predicted this one plan would flip, on the newest-record reading. Measured directly:
    ```
    plan: 20260829-rununify-00-5e4sb6-unify-the-two-host-runners-onto-one-shared-runner-library-ph.ipd.md
    today: True
      [0] review=False - 2026-09-16 approved (maintainer directive recorded by opencode/...): SET UNBLOCKED. All
      [1] review=False - 2026-09-03 approved (opencode ...): CHILDREN 01 AND 02 AUTHORED from E-01's inventory,
      [2] review=False - 2026-09-03 approved (opencode ...): SEQUENCING GATE RE-POINTED from `wtiso` to `lanectn
      [3] review=False - 2026-09-03 approved (opencode ...): PARTIAL EXECUTION OF E-01 ONLY, deliberately bounde
      [4] review=False - 2026-08-30 approved (aw set): status set to approved
      [5] review=True  - 2026-08-30 reviewed (opencode (its_direct/...)): /plan-review: REVIEWED - OPEN QUESTIONS; PR-001..
      any review record present: True
    ```
    Review's FACTS are exactly right: its newest record is an `approved` record and not a review, and its real review verdict was REVIEWED - OPEN QUESTIONS while its field says `go`. Its newest record has since become a 2026-09-16 maintainer `approved` record, which does not change that. What changed is the CHOSEN RULE: under any-record the plan is attested (record [5] is a genuine review), so it does not flip. THIS IS CORRECT FOR THIS PLAN'S SCOPE, and the residual is named honestly rather than quietly fixed: the gate now asks PROVENANCE ("did a review write this field"), not AGREEMENT WITH THE VERDICT, so a plan whose review said OPEN QUESTIONS while its field says `go` is still admitted here. That asymmetry is already recorded in the Scope check and is covered on the human path by `approval_refusals` and by the plan already being human-`approved`; closing it would be the verdict-agreement check this plan deliberately does not build (it would duplicate `newest_verdict`'s job and give one plan two verdict gates).

    NO PLAN FLIPS IN THE OTHER DIRECTION EITHER (0 newly approved), which matters because a fail-closed change that accidentally widened the gate would be the worse defect and a flip count alone would not show it.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the EIGHT new assertions' source and names, their passing result, AND the forged-field assertion FAILING against pre-change code (stash the fix and re-run). Paste the three mention-forgery assertions specifically, since they are what distinguish the chosen mechanism from the rejected one; confirm each would have PASSED (wrongly) under `_REVIEW_EVIDENCE_RE`. Paste the `python3 -m pytest tests/test_plan_readiness.py` summary line.
  - Observed evidence: NEW CLASS `ReadinessFieldMustBeAttestedTests` in `tests/test_plan_readiness.py`, seven test methods carrying NINE table rows plus the separate claims. The plan asked for eight assertions covering six named cases plus the three mention forgeries; the table carries all nine (the extra row is the not-newest attested case, which is what justifies the any-record choice), and the cases the plan wanted as standalone claims are standalone because they assert something a row cannot.

    THE TABLE ROWS (`ATTESTATION_TABLE`, each row `(case, plan text, expected answer, why)`), by case and expectation:
    ```
    a FORGED `go` with no review evidence at all                          -> False
    MENTION FORGERY: a `to-review` record MENTIONING plan-review          -> False
    MENTION FORGERY: a `draft` record containing the word APPROVE         -> False
    MENTION FORGERY: a non-review record narrating a predecessor's REJECT -> False
    the SAME forged plan with a real `/plan-review` record added          -> True
    an ATTESTED field whose review record is NOT the newest               -> True
    a field PRESENT but OUT OF VOCAB, over approving prose                -> False
    an ABSENT field with an approving history                             -> True
    an ABSENT field with a REJECTING history                              -> False
    ```
    THE THREE MENTION-FORGERY FIXTURES, verbatim, since they are the discriminating ones:
    ```
    FORGED_MENTIONS_PLAN_REVIEW = "- 2026-09-08 to-review (a): authored. I mention plan-review in passing."
    FORGED_MENTIONS_APPROVE     = "- 2026-09-08 draft (a): created. The word APPROVE appears here."
    FORGED_MENTIONS_REJECT      = "- 2026-09-08 to-review (a): supersedes a plan whose review said REJECT - NEEDS REPLAN."
    ```
    THE SEVEN METHODS, all passing:
    ```
    $ python3 -m pytest tests/test_plan_readiness.py::ReadinessFieldMustBeAttestedTests -o addopts="" -v
    test_the_corrupt_field_still_refuses_without_consulting_the_prose PASSED    [ 14%]
    test_a_plan_with_no_history_section_has_no_review_evidence PASSED          [ 28%]
    test_the_provenance_helper_reads_any_record_in_the_bounded_section PASSED  [ 42%]
    test_the_predicate_still_does_not_read_status PASSED                       [ 57%]
    test_plan_readiness_does_not_import_ipd_lint PASSED                        [ 71%]
    test_the_rejected_mention_matcher_would_have_accepted_the_forgeries PASSED [ 85%]
    test_a_readiness_field_is_honored_only_when_a_review_record_accounts_for_it PASSED [100%]
    ============================== 7 passed in 0.19s ===============================
    ```

    THE TESTS BITE: run against PRE-CHANGE code (`git stash push -- agent_workflows/plan_readiness.py`, tests kept), FOUR of the seven fail and the failure names all four forged rows returning True:
    ```
    E       AssertionError: Lists differ: ["  a FORGED `go` with no review evidence [1620 chars]ion"] != []
    E         a FORGED `go` with no review evidence at all:
    E           expected False, got True
    E         MENTION FORGERY: a `to-review` record MENTIONING plan-review:
    E           expected False, got True
    E         MENTION FORGERY: a `draft` record containing the word APPROVE:
    E           expected False, got True
    E         MENTION FORGERY: a non-review record narrating a predecessor's REJECT:
    E           expected False, got True
    FAILED ...::test_a_plan_with_no_history_section_has_no_review_evidence
    FAILED ...::test_the_rejected_mention_matcher_would_have_accepted_the_forgeries
    FAILED ...::test_the_provenance_helper_reads_any_record_in_the_bounded_section
    FAILED ...::test_a_readiness_field_is_honored_only_when_a_review_record_accounts_for_it
    4 failed, 3 passed in 0.50s
    ```
    Note WHICH assertion proves WHAT, as the plan required. The plain forged row fails pre-change, but it would ALSO have been fixed by the rejected mention-matcher, so it does not distinguish the mechanisms. The three MENTION rows do, and their claim is asserted directly rather than argued: `test_the_rejected_mention_matcher_would_have_accepted_the_forgeries` imports `ipd_lint` IN THE TEST and asserts, per forgery, that `_REVIEW_EVIDENCE_RE.search(history)` is NOT None (i.e. the rejected pattern ACCEPTS it) while `history_has_review_record` is False (the shipped mechanism refuses it). It passes, so all three would have PASSED WRONGLY under `_REVIEW_EVIDENCE_RE` and a suite carrying only the plain forged row would have gone green over an unfixed gate. That test also fails closed in the other direction: if `IPD-M107` is ever tightened to match (OQ-02 route (b)), it goes red and the divergence has been closed deliberately rather than drifting shut.

    WHOLE-FILE SUMMARY LINE:
    ```
    $ python3 -m pytest tests/test_plan_readiness.py -o addopts="" -q
    ........................................                                 [100%]
    40 passed in 0.63s
    ```
    40 against 33 before the change, i.e. the 7 new methods with no pre-existing test disturbed.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: for each of the four call sites, paste the symbol name and surrounding lines AS FOUND at execution time (proving they were re-located, not copied from this plan, whose numbers had already drifted per F-13), state what the call gates, state the behavior on a False verdict, and state whether a raise is swallowed by a surrounding `try/except Exception: pass` (F-14). Confirm the promotion target is `auto-approved` and not human `approved` (F-12). Paste `git status --porcelain` showing neither driver file was modified. Paste the bare `python3 -m pytest` summary line and the `tests/test_runner_item_dependencies.py` result, comparing failing NODE IDS to the RE-MEASURED baseline (`2 failed, 5957 passed` at `84258553`, node ids in the required-tests section), not the wrong figure this plan was authored with; confirm any pre-existing failure is pre-existing and do not attempt to green it.
  - Observed evidence: THE CALL SITES HAVE MOVED MODULE, NOT JUST LINE, AND THERE ARE NOW TWO RATHER THAN FOUR. This is exactly why E-05 said to re-locate BY SYMBOL, and it is a bigger drift than F-13 anticipated: the `rununify` Set has since split `initialize_run` and `execute_item` into shared cores, so BOTH former per-host pairs are now ONE shared call each in `runner_shared.py`, reached by both hosts. Neither `oc_runipd.py:2936`/`:6931` nor `agy_runipd.py:1974`/`:3988` exists as a call any more. Full symbol grep as found:
    ```
    $ grep -rn "is_plan_review_approved" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/runner_shared.py
    oc_runipd.py:95:    is_plan_review_approved,                       <- import from plan_readiness
    oc_runipd.py:466:    "is_plan_review_approved",                     <- __all__ re-export
    oc_runipd.py:3416:        is_plan_review_approved_fn=is_plan_review_approved,   <- INJECTION into the shared core
    agy_runipd.py:141:from agent_workflows.plan_readiness import is_plan_review_approved
    agy_runipd.py:2182:        is_plan_review_approved_fn=is_plan_review_approved,  <- INJECTION into the shared core
    runner_shared.py:6091:        owner="plan_readiness.is_plan_review_approved",  <- RunPolicyFlag metadata for --full-auto
    runner_shared.py:12989:    is_plan_review_approved_fn: Any = None,        <- shared initialize_run parameter
    runner_shared.py:13198:                if is_plan_review_approved_fn(p_path):     <- CALL SITE 1
    runner_shared.py:13930:    from agent_workflows.plan_readiness import is_plan_review_approved
    runner_shared.py:13991:    is_plan_review_approved = getattr(driver_module, "is_plan_review_approved", is_plan_review_approved)
    runner_shared.py:15241:        if is_plan_review_approved(plan_curr):                      <- CALL SITE 2
    ```

    CALL SITE 1, `runner_shared.py:13198`, inside the shared `initialize_run` queue build (the former `oc_runipd`/`agy_runipd` pair; both hosts inject the predicate at `oc_runipd.py:3416` and `agy_runipd.py:2182`). As found:
    ```
        if status == "reviewed" and full_auto and p_path:
            try:
                if is_plan_review_approved_fn(p_path):
                    set_plan_approved_fn(repo, id6)
                    status = "auto-approved"
            except Exception:
                pass
    ```
    WHAT IT GATES: the QUEUE STATUS at queue-build time. A True verdict clears the plan on disk and sets the local `status` to `auto-approved`, which then feeds `action_for(kind, status)` two lines later and so decides the item's queue ACTION. BEHAVIOR ON A NEWLY-FALSE VERDICT: the `if` is simply not taken, `status` stays `reviewed`, and `action_for` derives a review action. No exception, no mislabelled action, nothing else reads the verdict. RAISE SWALLOWED: YES, by `except Exception: pass`. That is fail-closed (the plan is left un-promoted) and therefore acceptable, but it is stated rather than relied on: a bug in the new code path would be INVISIBLE here rather than loud, which is why V-01's direct reproduction and the new unit tests, not the driver's behavior, are this change's evidence.

    CALL SITE 2, `runner_shared.py:15241`, in the shared post-turn disposition handler. As found:
    ```
        full_auto = state.get("options", {}).get("full_auto", False)
        auto_approved = False
        if is_review and disposition in ("reviewed", "approved") and full_auto:
            plan_curr = resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])
            if is_plan_review_approved(plan_curr):
                try:
                    set_plan_approved(repo, item["id6"])
                    run_action = state.get("options", {}).get("action")
                    if run_action != "review":
                        item["action"] = "execute"
                        item["status"] = "queued"
                    item["auto_approved"] = True
    ```
    WHAT IT GATES: the review-to-execute BRIDGE after a review turn finishes. A True verdict clears the plan, flips `item["action"]` to `execute` and `item["status"]` to `queued` (unless the whole run's action is `review`), marks `auto_approved`, and appends an `ipd-auto-approved` event. BEHAVIOR ON A NEWLY-FALSE VERDICT: the branch is skipped entirely, so the item keeps its `reviewed` disposition and its review action, `auto_approved` stays False, and no event is written; a human then approves it in one command. RAISE SWALLOWED: NO, not for the predicate. Note the difference from site 1 carefully, because F-14 got this half right and the placement matters: the `try` here opens AFTER the predicate call, so it guards `set_plan_approved` and the state writes, and a raise from the PREDICATE would propagate out of this handler. That is louder than site 1, which is the safer of the two shapes for surfacing an implementation bug, and it is another reason the new code path is deliberately pure and exception-free (it only walks lines and matches regexes already used by `newest_verdict`).

    PROMOTION TARGET CONFIRMED `auto-approved`, NOT HUMAN `approved` (F-12 upheld). Both sites call `set_plan_approved`, whose two host definitions (`oc_runipd.py:875`, `agy_runipd.py:972`) shell out to `aw set auto-approved <id6> --actor "aw oc run --full-auto" --yes --no-commit`, with no `--by-human` anywhere, and whose docstring records the OQ-02 resolution that the machine must not assert the human attestation. `auto-approved` is in `ipd_schema.READY_TO_EXECUTE` (`ipd_schema.py:267`), so the defect this plan fixes is REAL and precisely stateable: a forged field let an unreviewed plan reach an EXECUTABLE tier, without ever claiming a human approved it. The `--full-auto` flag's own help at `runner_shared.py:6091` names this predicate as its `owner`, which is the shipped statement that this predicate IS the gate.

    NEITHER DRIVER MODIFIED (read-and-report honored; the anti-divergence guard keeps the rule shared):
    ```
    $ git status --porcelain
     M .aw/records/plans/pending/20260908-rdattest-02-8v5pwa-make-the-auto-approve-predicate-require-the-review-evidence.ipd.md
     M agent_workflows/plan_readiness.py
     M tests/test_oc_runipd.py
     M tests/test_plan_readiness.py
    ```
    `oc_runipd.py`, `agy_runipd.py` and `runner_shared.py` are all absent from that list, i.e. E-05 was read-and-report as required and the shared-module change reached both hosts with no per-host edit. `tests/test_oc_runipd.py` IS an out-of-fence path and is justified in the Scope check below; it is a TEST FIXTURE, not a driver.

    ONE OUT-OF-FENCE EDIT WAS REQUIRED, AND FINDING IT IS WHY THIS V-ITEM IS NOT JUST A LINE COUNT. My first draft of this evidence asserted that the host driver fixtures "pass BECAUSE their histories carry a real `reviewed`/`/plan-review` record, so they are attested under the new rule". I then CHECKED that claim instead of shipping it, and it was FALSE for one fixture out of four, in a way a green suite could not reveal. `_repo_with_statuses` (`tests/test_oc_runipd.py:3966`) builds its `reviewed` plan from `_CONFORMING_PLAN` plus a bare `- Readiness: go`, and that template's history holds only `approved` and `draft` records, so the fixture was UNATTESTED under the new rule. Measured on that exact fixture:
    ```
    the revw01 fixture, if the --full-auto auto-approval were reached:
      PRE-change  would clear it -> True   (Status would become auto-approved: the assertion COULD fail)
      POST-change would clear it -> False  (Status stays reviewed regardless: the assertion is VACUOUS)
    ```
    THE CONSEQUENCE IS A SILENTLY VACUOUS TEST, not a red one, which is the worse failure mode. `test_alias_refuses_a_reviewed_plan_even_with_full_auto_present` exists to pin an ORDERING: that the `--action review is illegal` gate fires BEFORE the auto-approval, and its own docstring calls the status assertion "the load-bearing one: if the gate ran AFTER the auto-approval, the plan file would have been mutated to `auto-approved`". Once the predicate cannot clear the fixture at all, `- Status: reviewed` survives whether the gate runs first or not, so the test passes for the wrong reason and would no longer catch the ordering regression it was written for. FIXED by PREPENDING one review record to the helper's `reviewed` fixture (newest-first, as `aw set` writes), which restores reachability: `is_plan_review_approved` -> True on the rebuilt fixture, so the ordering claim is falsifiable again. `tests/test_oc_runipd.py` -> `212 passed`.

    THE BLAST RADIUS WAS MEASURED RATHER THAN ASSUMED, by scanning every test source for a plan literal carrying an approving `- Readiness:` and asking the predicate about each: `_repo_with_statuses` was the ONLY unattested one. The other three are genuinely attested and needed no edit, which is what my original claim got right: `test_run_flag_surface._PROBE_PLAN` (`- 2026-09-05 reviewed (test): APPROVE`), `test_oc_runipd`'s `p_field` and `test_agy_runipd_cli`'s `clear` (both `reviewed (aw set)` records). The `--full-auto` end-to-end test's fake reviewer also writes a `/plan-review` record, so it stays attested by construction.

    BARE SUITE, and the baseline comparison is by NODE ID as instructed:
    ```
    $ python3 -m pytest
    1 failed, 7239 passed, 3 skipped, 2 xfailed, 3 warnings in 101.07s (0:01:41)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```
    THE AUTHORED AND REVIEWED BASELINES ARE BOTH STALE AND NEITHER FAILURE THEY NAME IS PRESENT. Review's baseline was `2 failed, 5957 passed` at `84258553` with node ids `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` and `test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`; BOTH now PASS, and the suite has grown to 7240 tests. So the comparison is against a freshly established baseline, done the only way that settles it: by reverting my own change.

    THE ONE FAILURE IS PRE-EXISTING, ENVIRONMENTAL, AND ALREADY FILED. Proven by reverting, not argued: with `agent_workflows/plan_readiness.py` and `tests/test_plan_readiness.py` stashed at base HEAD `b83a6cd9`, the same node id fails identically (`1 failed in 0.29s`). Its cause is the AMBIENT environment, not the code: the test asserts `OPENCODE_CONFIG_CONTENT not in main_env` while the env under inspection is built by merging `os.environ`, and this agent turn itself is launched with that variable exported, so the key is present for reasons unrelated to the code under test. Measured both directions:
    ```
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped -o addopts="" -q
    1 passed in 0.27s

    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest
    7240 passed, 3 skipped, 2 xfailed, 3 warnings in 103.14s (0:01:43)
    ```
    So the suite is FULLY GREEN with the ambient leak removed, and my delta is `+1 test file's 7 new tests, 0 new failures`. It was NOT greened in any other way: the test was not edited, skipped, or weakened. It is already carried by backlog item `to77re` (`Status: open`, `Work-Kind: bug`, `Blocks-Release: next`), filed on 2026-09-20 from another lane, whose text describes this exact assertion and this exact cause.

    FOCUSED SURFACES, including the anti-divergence guard that constrains this change's SHAPE:
    ```
    $ python3 -m pytest tests/test_plan_readiness.py tests/test_ipd_lint.py tests/test_runner_item_dependencies.py -o addopts="" -q
    ........................................................................ [ 59%]
    ..................................................                       [100%]
    122 passed in 8.03s
    ```
    `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` passes, which is the mechanical confirmation that the rule stayed in the shared module and no driver was taught its own copy. Both host driver CLI surfaces were run too (`tests/test_run_flag_surface.py tests/test_agy_runipd_cli.py` -> `147 passed`), since they exercise the `--full-auto` auto-approve path end to end with a `Readiness: go` fixture, and `tests/test_oc_runipd.py` -> `212 passed` after the fixture repair above.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

It must not be executed until a human sets it `approved` with `aw ipd set approved <plan> --by-human`. THE `- Readiness:` FIELD ON THIS PLAN IS NOW `/plan-review`'s ATTESTED OUTPUT, written by the review that also recorded a verdict in `## Workflow history`, which is exactly the field-plus-evidence agreement this plan makes the predicate demand; the author correctly omitted it, and a reader should note the reflexive point that this plan's own field is now attested by the mechanism it hardens.
THE COST ARGUMENT HAS MOVED, so do not approve on the authored version of it: F-4's "zero cost" rested on the WEAK mechanism, and zero flips under that mechanism is evidence it was too weak, not evidence it was safe (PR-703). Under the corrected mechanism exactly ONE plan flips out of 139 carrying the field, and that one is a TRUE POSITIVE whose field disagrees with its own review verdict. That is a stronger argument for the fail-closed direction than the original, not a weaker one.

Scope fence: touch ONLY the two paths in `- Scope-Paths:`. Do NOT modify either driver (`oc_runipd.py`, `agy_runipd.py`): E-05 is read-and-report, and the anti-divergence guard requires the rule to stay shared. Do NOT add an `ipd_lint` import to `plan_readiness` (F-5 corrected: it is not stdlib-cheap). Do NOT change `_REVIEW_EVIDENCE_RE` or `IPD-M107` (OQ-02 owns that question). Do NOT edit `5e4sb6` or any other plan file to make a measurement come out differently. Do NOT touch `opencode-recovery/` to green the suite; it is another party's work and its failure is pre-existing. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD: this plan hardens the predicate that decides whether a plan may be auto-approved, so it must NOT be executed under `--full-auto` on the strength of its own change, and its own approval must come from a human. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
