# IPD: Spend the frozen retry budget on a retryable failure so the correction layer stops being dormant

- Date: 2026-09-08
- Kind: child
- Concern: Spec `25kzda` 2.1's correction budget is fully built, fully tested, range-validated, operator-settable and frozen into run state, and then never spent. `plan_retry` and `retry_budget_remaining` have ZERO production callers: they appear only in `run_recovery.py` (their definitions) and `tests/test_run_recovery_cli.py`, and neither host runner imports the module for anything but the range check. So a failed run item today gets zero automatic correction attempts, and an operator who passes `--retry-budget 5` gets a value that is validated, resolved, frozen into `state.json`, and read by nothing. Re-verified at review, HEAD `09beb137`: the frozen value really is on disk (`options.retry_budget: 2` in each of the three newest run `state.json` files) and really is read by nothing.
  THE PLAN'S CENTRAL MECHANISM CANNOT BE PERFORMED IN THE DECLARED FILES, AND THIS IS THE ONE THING A MAINTAINER MUST SETTLE BEFORE EXECUTION (review, F-12, PR-001, escalated as BLOCKING OQ-03). `plan_retry` and `retry_budget_remaining` are not free functions over a run's `state.json`: both take a `run_engine.RunEngine` as their first positional argument (`run_recovery.py:269-277`, `:415-417`), both call `engine.reconstruct_state()`, and `RunEngine.__init__` REQUIRES a `run_ledger_store.RunLedgerStore` (`run_engine.py:117-127`) over a hash-chained `ledger.jsonl`. NO DRIVER RUN HAS ONE, measured three ways at review: `find .aw/records/runs -name ledger.jsonl` returns 0 files across 143 run directories; `rg -c 'run_ledger_store|RunLedgerStore' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` matches nothing in either driver (exit 1); and neither driver imports `run_engine` at all. Spec `25kzda`'s own preamble concedes it at `:28`: "the ledger is built but UNWIRED". The two worlds do not even share a state vocabulary: `plan_retry` refuses any step not in `run_state.STATE_FAILED`/`STATE_BLOCKED` (`run_recovery.py:295-303`), while a driver queue item carries `failed-safely`/`partial`/`interrupted` from a DIFFERENT closed set (`oc_runipd.py:317-334`, `runner_shutdown.py:64-83`). So E-03's instruction to spend the budget through those helpers and "DO NOT reimplement any of that in the runner" has no executable form inside `oc_runipd.py`/`agy_runipd.py`: there is no engine to pass and nothing constructs one. A sibling plan exists for exactly this gap (`i1hlgx`, `reviewed`, `go-pending-approval`, "Say plainly that no driver run writes a ledger"), and both it and executed `7wei1o` name "whether driver runs should WRITE a `ledger.jsonl` at all" as a genuine, out-of-scope DESIGN question. That question is therefore not this plan's to answer silently, and OQ-03 puts the three available shapes to the maintainer.
- Scope: Wire CONSUMPTION only. On a RETRYABLE failure class, spend the frozen budget through the shipped helpers: issue a correction attempt, invalidate stale evidence, and escalate on exhaustion. Non-retryable classes stay non-retryable at every budget, and the frozen budget must not change on resume. Adds no flag, no new budget semantics, and no repository-policy tier.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_retry_consumption.py, tests/test_runner_refork_guard.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: retrywire
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: xipfy1
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: trjfyy
- Blocks-Release: next

## Workflow history
- 2026-09-22 execution performed, awaiting the driver's finalize (opencode its_direct/pt3-claude-opus-5-1m-us, run `run-20260922T024054Z-2245533` position 16, lane `aw/lane/xipfy1`): THIS ENTRY DOES NOT CLAIM THE TERMINAL TRANSITION, which only `aw ipd finalize` may write and which this worker lane is correctly refused. It records that the work is complete and verified. E-01..E-07 performed and V-01..V-07 verified with pasted evidence, at HEAD `d1d6b6eb` in lane `aw/lane/xipfy1` under run `run-20260922T024054Z-2245533`. Bare suite: `1 failed, 8206 passed, 3 skipped, 2 xfailed`, the single failure being `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, which is the IDENTICAL node id that failed in the pre-change baseline measured at the same HEAD (`1 failed, 8157 passed`) and is ENVIRONMENTAL rather than mine: it requires `OPENCODE_CONFIG_CONTENT` to be absent for a non-isolated turn, that variable is set in this turn's own runner environment and leaks into the child pytest, and `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py` gives `76 passed` with no source change. Compared by NODE ID, not by count, per the plan's instruction. NOTE the plan's own recorded baseline is STALE (it names `tests/test_reporting_contract.py::ParityTests::...`, which passes at this HEAD, and a total ~2200 lower).
  BUILT UNDER OQ-03's RESOLVED SHAPE (b), the maintainer's 2026-09-10 decision: the budget is spent in the drivers' own `state.json`/`events.jsonl` substrate, reusing the shipped helpers' SEMANTICS without calling the ledger-bound `plan_retry`/`retry_budget_remaining`, which require a `RunEngine` over a `ledger.jsonl` no driver run has. RE-VERIFIED at execution that those two helpers are still called only from `run_recovery.py` and their own tests, so this change did not deepen the dormancy it was written to end; it wires the CLASS the plan targeted instead. All four semantics OQ-03 enumerated are preserved (failed attempt preserved, idempotency key, escalate-not-loop, evidence invalidation) and the ACCEPTED DUPLICATION IS STATED IN THE CODE with a pointer to the still-open ledger question, as OQ-03 explicitly demands, with a test asserting that note exists. Nothing here decides whether drivers should ever write a ledger; that stays open.
  ONE SUBSTANTIVE NARROWING OF THE PLAN AS WRITTEN, recorded prominently because it changes what shipped. E-01's allowlist is `{failed-safely}` ALONE, not `{failed-safely, partial}`. THREE reasons, the third measured: approved sibling plan `dy9ymn` already owns re-dispatching a `partial` item behind a NARROW "provably attempted nothing" predicate whose scope says "EXCLUDES retrying any item that produced ANY evidence of work", so a blanket retry here would be strictly broader than the predicate that plan exists to build; `partial` is ALSO what a verifier DOWNGRADE writes, so retrying it would spend correction budget on a rejected verdict sibling `1bfppy` is separately wiring; and it BROKE FIVE SHIPPED TESTS that pin `partial` as terminal (four in `tests/test_defect_report.py::RescoreAfterAReaskTests`, whose whole subject is an item that answered honestly it is still partial, plus `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_verifier_gate`). Recorded as DECISION 16-xipfy1-D1.
  TWO DEFECTS THE WORK ITSELF SURFACED AND HAD TO ROUTE AROUND. FIRST, the obvious delivery channel for the correction packet is INERT on the default path: `lane_containment.prior_attempt_summary` projects an ALLOWLIST for an ISOLATED turn and isolation is the DEFAULT, so a packet left on the attempt record is stripped before it reaches the prompt (`finalize_refused` survives only because it IS in that allowlist, and widening it belongs to `lane_containment`, which this plan does not declare). The packet is therefore rendered as its own prompt notice, with a test asserting it survives an isolated render. Filed as backlog `ytrz7u`. SECOND, `labels.command` already carries the verb, so the exhaustion remedy first rendered `aw oc run run xipfy1`; caught ONLY because V-05 demands RENDERED output rather than a state dict, fixed, and pinned for both hosts. Filed as backlog `6if6ko`. A third finding, that spec 5.5's retry classes are enumerated in a vocabulary no driver disposition uses so every consumer must invent the mapping, is filed as backlog `rb4wgj`.
  SCOPE-PATHS WIDENED ADDITIVELY, before commit and declared rather than concealed: `tests/test_runner_refork_guard.py` was added, because E-07 requires registering the shared symbols in that module's `REFORK_TABLE` and the original declaration omitted it. Spec 5.5a's additive-widening conditions hold (one path ADDED, none removed, a literal file path, receipt carries a frozen-region digest). NO `.spec.md` file was edited, so no spec amendment is claimed; the 5.3-versus-substrate tension OQ-03 exposed is recorded in the spec-sync section rather than resolved here, and `rb4wgj` carries the mapping gap.
  E-07's IMPORT BAR WAS MEASURED AS A DELTA, never asserted as an absence, per the plan's F-14 correction: agy-to-oc imports counted by AST are 4 module-level + 4 function-level = 8 BEFORE and 8 AFTER, unchanged, because the six new symbols are imported from `runner_shared` and never through the peer driver.
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> neutral (not negative). Specifically, both blocking questions were answered on 2026-09-10 (build on the drivers' own substrate; land `1bfppy` first) and the findings they escalated, PR-001 and PR-002, are now closed in review round 2. Performed at HEAD `5692797e` at the maintainer's explicit instruction of 2026-09-10, who was shown that 12 of 15 `no-go` plans were held by stale bookkeeping and chose to have them fixed with evidence recorded rather than re-reviewed. This is the SECOND such cleanup in one session; the durable fix is plan `qhy3i3` E-07, authored and awaiting approval. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-10 reviewed (aw set): plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001..PR-009, seven FIXED, PR-001 and PR-002 escalated as blocking OQ-03/OQ-01; Readiness no-go pending those answers

- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001..PR-009, seven FIXED and two escalated as blocking (PR-001 -> OQ-03, PR-002 -> OQ-01 restated); Readiness `no-go` pending those two answers. Reviewed at HEAD `09beb137`; `aw ipd lint --phase author` reported only the expected `IPD-Q501` (OQ-01 blocking and open) before review, and `--phase review-finalize` after the revisions. DISCLOSURE: the same model family authored the plan, so this is close to a self-review; its value rests on what was EXECUTED, not re-read.
  THE FINDING THAT DECIDES WHETHER THIS PLAN CAN BE EXECUTED AT ALL is PR-001 (BLOCKER): the two helpers this plan exists to call take a `RunEngine` over a hash-chained `ledger.jsonl`, and no driver run has one. Measured three independent ways (0 `ledger.jsonl` files across 143 run dirs; zero `run_ledger_store`/`RunLedgerStore` references in either driver; neither driver imports `run_engine`), corroborated by the spec's own `:28` concession and by sibling plan `i1hlgx` which exists solely to make that gap honest to operators. The state vocabularies are disjoint too (`STATE_FAILED`/`STATE_BLOCKED` versus `failed-safely`/`partial`/`interrupted`). So E-03 as written has no executable form in the declared `Scope-Paths`, and an executor would discover that only after E-01 and E-02 were done. Escalated as OQ-03 with three shapes rather than resolved here, because choosing one is a design decision (does a driver run write a ledger?) that two other plans explicitly refuse to make.
  FOUR CLAIMS IN THE PLAN WERE MEASURED FALSE AND ARE CORRECTED IN PLACE. (1) OQ-01's premise expired: `wyw936` is no longer `open` with no plan, it reads `- Status: graduated` and is owned by `1bfppy` (`reviewed`, `go-pending-approval`), so the recommended option (a) now exists and the question changes from "absorb scope or ship a hole" to a simple ordering choice. (2) The suite baseline is wrong in both halves and names a test that PASSES: bare `python3 -m pytest` at HEAD gives `1 failed, 5958 passed, 3 skipped, 2 xfailed`, the failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` caused by ANOTHER party's gitignored `opencode-recovery/` tree, and `tests/test_orchestrator_retirement.py` is `112 passed`. An executor holding the stated baseline could read a co-worker's artifacts as their own regression and delete files that are not theirs. (3) E-06 cites "`tests/test_run_viewer.py:1-30` documents that 23 tests reading it fail in a fresh checkout"; that file's header documents the fixture RULE and no such count appears anywhere in it. The rule is real and worth keeping; the number is invented. (4) E-07's named guard is in the wrong file: `AntiDivergenceGuardTests` (`tests/test_runner_item_dependencies.py:1552`) polices dependency-regex re-forking, and the guard that actually asserts cross-host object identity is `tests/test_runner_refork_guard.py`; separately, `agy_runipd` ALREADY imports from `oc_runipd` at four module-level sites plus several function-level ones, so "gained no NEW import" must be measured as a delta against a counted baseline, never as an absence.
  THREE MORE GAPS, EACH ONE AN EXECUTOR WOULD HAVE HIT. E-04's evidence-invalidation seam exists but is INSIDE `plan_retry` itself (`run_recovery.py:329-345`, appending a `correction` record carrying `invalidates_seq`), so the item's "locate the seam or stop" instruction resolves to "it is already done for you, and only in the engine world" - which is PR-001 again from a second direction. E-05 cites `r2i1b1` as possibly-not-landed; it is `approved` and still in `pending/`, and its `Scope-Paths` overlap this plan's in three files, so the real risk is merge ordering rather than availability. And the plan's own F-11 ("no surface greps `orchestrator-deferred`") is TRUE but understates the constraint: the diagnostics renderer reads a specific FIELD NAME (`driver_error`, `render_stream.py:2166-2171`) for exactly three statuses, so a reason written under any other key reaches no surface no matter which status carries it.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `trjfyy`, inheriting its `Blocks-Release: next` gate. THE ITEM'S SEQUENCING GATE IS NOW SATISFIED, which is the main change since it was filed: it says "Gate this behind `uyeko5`, which owns the flag and the frozen value; wiring consumption first would have nothing to read the operator's budget from." `uyeko5` is now EXECUTED (`.aw/records/plans/executed/20260903-runflags-01-uyeko5-...ipd.md`, `- Status: executed`), so the flag, its precedence and the frozen value all exist and this plan has something to read. Consequently `Item-Dependencies: none` is correct rather than an oversight. THE DORMANCY CLAIM STILL HOLDS, re-verified at HEAD `a2e0438a` by symbol search rather than by trusting the item's line numbers: `plan_retry` (`run_recovery.py:269`) and `retry_budget_remaining` (`:415`) appear ONLY in their own module and in `tests/test_run_recovery_cli.py`. ONE PART OF THE ITEM IS NOW STALE AND IS RECORDED SO NOBODY RE-DERIVES IT: the item says the three symbols including `validate_retry_budget` have zero production callers, but `validate_retry_budget` (`:136`) IS now called in production, by `runner_shared.resolve_retry_budget` (`:1764`), which `uyeko5` added. So the RANGE CHECK is wired and only the two SPENDING helpers remain dormant; that narrows this plan to consumption and is why the range bound is explicitly out of scope. Also verified the frozen value genuinely exists to be read: `freeze_run_policy_flags` resolves `--retry-budget` to its effective integer via `resolve_retry_budget` (`runner_shared.py:1836-1837`) precisely so no later reader has to re-resolve it, which is exactly the property a consumption loop needs on resume.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the correction budget do something. An operator who sets a budget should see a failed item get bounded, evidence-invalidating correction attempts, and see escalation when the budget runs out, instead of a single failure and a silently unused number in `state.json`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: decide what may be retried, before wiring anything

- [x] E-01 Define the RETRYABLE failure classes explicitly, as a shared table in `runner_shared.py`, and derive nothing implicitly. START FROM SPEC 5.5's ENUMERATION, which names five retryable and ten never-retryable classes verbatim (see the spec-sync section, where they are quoted); map each onto the drivers' disposition vocabulary and EXCLUDE any driver status that does not map to exactly one spec class, recording why. The runners' disposition vocabulary is `executed|substantially-complete|partial|blocked|failed-safely` (`oc_runipd.py:4837`), and `failed-safely` is assigned both to a genuine driver error and, per the comment at `oc_runipd.py:5852-5853`, to cases the classifier can conflate with a DELIBERATE OPERATOR STOP. That conflation is the single most important hazard here: retrying an operator's deliberate stop would spend paid model turns fighting the operator. So the table must be an ALLOWLIST of retryable classes, never a denylist of non-retryable ones, and a class the classifier is known to conflate must be excluded until it can be told apart. State per class WHY it is or is not retryable.
  - Depends on: none
  - Expected outcome: one shared allowlist naming each retryable class with its justification; a deliberate operator stop is provably NOT in it.
  - Execution notes: `TURN_RETRYABLE_DISPOSITIONS` (an ALLOWLIST) plus the 20-row `TURN_RETRY_CLASSIFICATION` table in `runner_shared.py`, each row carrying its per-class justification. NARROWED DURING EXECUTION, and this is the one substantive departure from the plan as written: the allowlist is `{failed-safely}` ALONE, not `{failed-safely, partial}`. `partial` was excluded because (a) approved sibling plan `dy9ymn` already owns re-dispatching a `partial` item behind a NARROW 'provably attempted nothing' predicate whose scope says 'EXCLUDES retrying any item that produced ANY evidence of work', so a blanket retry here would be strictly broader than the predicate that plan exists to build; (b) `partial` is also what a VERIFIER DOWNGRADE writes, so retrying it would spend correction budget on a rejected verdict `1bfppy` is separately wiring; and (c) it was MEASURED to break five shipped tests that pin `partial` as terminal (four in `tests/test_defect_report.py::RescoreAfterAReaskTests`, whose whole subject is an item that answered honestly it is still partial, plus `tests/test_oc_runipd.py::VerifierGateAndRunnerBugTests::test_verifier_gate`). The deliberate-operator-stop hazard the item names is handled by reading the `stopped` record DIRECTLY in `turn_failure_is_retryable` rather than trusting it to have been mapped to `interrupted`.
  - Execution state: performed

- [x] E-02 Read the FROZEN budget, never the live `args`, so a resumed run cannot change its own budget mid-flight. `freeze_run_policy_flags` (`runner_shared.py`, the `retry_budget` branch at `:1836-1837`) resolves the flag to its effective integer at freeze time expressly so "the frozen state holds the value that will actually be used (never a bare `None` that a later reader has to re-resolve, and re-resolve differently)". Consume that frozen integer. Do NOT call `resolve_retry_budget` again in the loop: it reads `args`, and the docstring above it records that re-reading `args` on every resume "would silently change meaning between the first turn and the last". Note `0` IS A LEGAL BUDGET meaning no retries (`run_recovery.py:69-70` warns a falsy check must not treat it as unset), so the guard must be `is None`-shaped, not truthiness-shaped.
  - Depends on: E-01
  - Expected outcome: the loop reads the frozen integer; a `--retry-budget 0` run performs zero retries rather than falling back to the default 2; a resumed run uses the originally frozen value.
  - Execution notes: `turn_retry_decision` reads `frozen_retry_budget(state)` and `turn_retry_budget_remaining` reports the remainder; neither calls `resolve_retry_budget`, which is asserted by a source test. `frozen_retry_budget` already shipped with the `is None`-shaped guard (`zzcrlo`), so this item CONSUMES it rather than re-writing it; that reuse is the correct outcome and is recorded so nobody looks for a second reader.
  - Execution state: performed

### Task group 2: spend it through the shipped helpers

- [x] E-03 Spend budget through `plan_retry` (`run_recovery.py:269`) rather than counting attempts in the runner, so the ledger-backed semantics the helpers already implement and test are the ones that ship. `plan_retry` appends a retry record and does NOT delete the failed attempt (pinned by `tests/test_run_recovery_cli.py:124-131`), is idempotent on a repeated `idempotency_key` (`:133-143`), and raises `RetryLimitExceededError` (`run_recovery.py:87`) once the budget is exhausted (`tests/test_run_recovery_cli.py:145-160`). Use `retry_budget_remaining` (`:415`) to report what is left rather than recomputing it. DO NOT reimplement any of that in the runner: the whole reason this layer is dormant rather than missing is that the semantics already exist and only the call site is absent.
  THIS ITEM IS GATED ON OQ-03 AND MUST NOT BE STARTED WHILE IT IS OPEN (review, PR-001). As written this instruction has NO EXECUTABLE FORM in the declared `Scope-Paths`, and the reason is mechanical rather than stylistic: both helpers take a `run_engine.RunEngine` first positional argument (`run_recovery.py:269-277`, `:415-417`) and immediately call `engine.reconstruct_state()`; `RunEngine` requires a `RunLedgerStore` over a `ledger.jsonl` (`run_engine.py:117-127`); and no driver run has one (0 files across 143 run dirs, zero store references in either driver, neither driver imports `run_engine`). There is therefore no engine to pass and nothing in either driver constructs one. The state vocabularies are also disjoint: `plan_retry` raises `NoRetryableStateError` for any step not in `run_state.STATE_FAILED`/`STATE_BLOCKED` (`run_recovery.py:295-303`), and a driver queue item never holds either value (`oc_runipd.py:317-334`). Whichever shape OQ-03 selects, RE-STATE this item to match it before performing it, and do NOT quietly satisfy it by writing a second attempt-counting implementation in the runner: that is precisely what this item forbids, and doing it while citing this item would make the plan's own prohibition the justification for violating it.
  - Depends on: E-02
  - Gated on: OQ-03 (blocking; see the item body). This is stated here rather than in `Depends on`, which the linter requires to hold only `E-*` ids.
  - Expected outcome: a retryable failure produces a retry record via `plan_retry`, the failed attempt is preserved, and remaining budget is reported from `retry_budget_remaining`.
  - Execution notes: performed, UNDER OQ-03's RESOLVED SHAPE (b), and re-stated as that answer requires before performing. The maintainer's 2026-09-10 answer directs the budget to be spent in the drivers' own `state.json`/`events.jsonl` substrate, reusing the shipped helpers' SEMANTICS without calling the ledger-bound functions, because `plan_retry`/`retry_budget_remaining` require a `RunEngine` over a `ledger.jsonl` no driver run has. RE-VERIFIED AT EXECUTION: `rg 'plan_retry|retry_budget_remaining'` still matches only `run_recovery.py` and `tests/test_run_recovery_cli.py`, so the helpers remain uncalled from production and nothing here made that worse. All four semantics OQ-03 enumerated are preserved and each is named at the implementation site: the failed attempt is PRESERVED (the driver appends attempts and this path deletes none), an IDEMPOTENCY KEY bounds a double spend (`turn_retry_idempotency_key`), exhaustion ESCALATES rather than looping, and stale evidence is INVALIDATED. The accepted duplication is stated IN THE CODE with a pointer to the still-open ledger question, as OQ-03 explicitly demands, and a test asserts that note exists.
  - Execution state: performed

- [x] E-04 Issue a CORRECTION packet containing only the FAILED predicates, and invalidate stale evidence, per spec `25kzda` 5.5 / 4.2 / 5.2 as the item requires. A correction attempt is not a re-run of the whole item: re-sending the full task would both cost more and invite the model to redo work that passed. Equally, evidence captured by the FAILED attempt must not be allowed to satisfy the retried attempt, or a correction could inherit the very evidence that was wrong.
  THE INVALIDATION SEAM WAS LOCATED AT REVIEW, SO DO NOT RE-DERIVE IT, AND NOTE WHERE IT LIVES (review, F-13). It is INSIDE `plan_retry` (`run_recovery.py:329-345`): for every live evidence seq bound to the step (`_step_evidence_seqs`, `:237`) it appends a `correction` record carrying `invalidates_seq`, and `set_lifecycle.make_invalidation_records` (`:66`) reuses the same idiom for the integration case. There is no second invalidation path to write, and writing one would fork this idiom. But the seam is ENGINE-SIDE: it appends through `engine.store`, so it is reachable only if OQ-03 selects a shape where an engine exists. This is PR-001 from a second direction and is why this item is gated on that answer too. The plan's original instruction ("if no such seam exists, say so and stop") is answered: the seam exists, in a substrate the drivers do not have.
  ALSO SETTLE WHAT "ONLY THE FAILED PREDICATES" MEANS BEFORE WRITING IT, because the correction packet is the one deliverable here with no shipped implementation. `run_packet.build_step_packet` (`:229`) builds a bounded step packet from a WORKFLOW mapping and a `step_id`, not from a driver queue item, and nothing renders a failed-predicate-only variant today. If OQ-03's chosen shape routes through the driver prompt instead, say plainly which existing prompt-construction path carries the correction and what is omitted from it, rather than describing the packet abstractly.
  - Depends on: E-03
  - Expected outcome: the correction packet names only failed predicates; evidence from the failed attempt cannot satisfy the retry; both demonstrated on a fixture.
  - Execution notes: performed, and the delivery channel had to be CORRECTED after measurement. `turn_correction_packet` builds a packet naming only failed predicates; `invalidate_turn_evidence` is the ONE producer of the `correction`/`invalidates_attempt` record, deliberately the same idiom as the engine-side seam inside `plan_retry` and `set_lifecycle.make_invalidation_records`, and it CLEARS `verification_status`/`last_outcome` rather than merely annotating them (a stale-but-present field is read by `run_viewer` and by `integration_is_earned`, so annotating alone would leave dead evidence satisfying those readers). THE FIRST DELIVERY SHAPE WAS INERT AND IS RECORDED SO IT IS NOT RE-TRIED: carrying the packet on the attempt record for `Prior attempt:` to interpolate FAILS on an isolated turn, because `lane_containment.prior_attempt_summary` projects an ALLOWLIST (`_PRIOR_ATTEMPT_SAFE_KEYS`, measured: no `turn_correction` entry) and isolation is the DEFAULT. `finalize_refused` works that way only because it IS in that allowlist, and widening it belongs to `lane_containment`, which this plan does not declare. So the packet is rendered as its own prompt notice (`build_correction_notice`), which needs no allowlist entry and cannot be silently projected away; a test asserts it survives an isolated render.
  - Execution state: performed

- [x] E-05 ESCALATE on exhaustion instead of looping or silently giving up. When `plan_retry` raises `RetryLimitExceededError`, the item must reach a terminal disposition that says the budget was spent and how many attempts it bought, so an operator can tell "failed once" from "failed after two corrections".
  THE READ-SURFACE CONSTRAINT IS TIGHTER THAN "PER-ITEM STATE", AND THIS IS THE PART THAT SILENTLY FAILS (review, F-11 as corrected). The run summary's diagnostics block reads ONE FIELD NAME for exactly THREE statuses: `render_stream.py:2166-2171` emits a diagnostic line only when the status is `failed-safely`, `merge-needs-human`/`merge-refused` (renamed 2026-09-21 from `integration-blocked`/`merge-conflict`, whose pre-rename spellings are also still listed) AND the item carries a `driver_error` key (the `dependency-blocked` and `interrupted` branches read their own distinct keys, `:2157-2165` and `:2172-2173`). So a reason written under a NEW key, or carried on a status outside that set, renders nowhere even though it sits in per-item state. Verify by RENDERING: call `render_stream.render_run_summary_table` on a fixture item and paste the output showing your reason present, not merely the state dict showing the field set.
  ALSO PICK A STATUS FROM THE CLOSED SET. Both drivers' `TERMINAL_STATES` (`oc_runipd.py:317-334`) and `runner_shutdown.KNOWN_ITEM_STATUSES` (`:64-83`) are closed vocabularies, and `runner_shutdown.observe_ledger` (`:299-325`) declares a run INCOHERENT when any queue item holds a status outside the second one. Inventing a new status for budget exhaustion would therefore make every subsequent shutdown observation report the run as broken. Reuse an existing terminal status and carry the exhaustion facts in a field.
  ON `r2i1b1`: it is `approved` and still in `.aw/records/plans/pending/`, so it has NOT landed, and its `Scope-Paths` overlap this plan's in three files (`runner_shared.py`, `oc_runipd.py`, `agy_runipd.py`) plus `render_stream.py`. NOTE THE SCOPE CONSEQUENCE: the rendering check above CALLS `render_stream` from a test and requires no edit to it, so `render_stream.py` stays out of `Scope-Paths` deliberately; if you conclude the renderer itself must change (a new status or key needing a new branch), that is `r2i1b1`'s territory and belongs in a declaration and a justification, not in a quiet edit. Re-check its disposition at execution time: if it has executed, USE its shared refusal record rather than adding a parallel field; if it has not, keep to the existing `driver_error` key and say so, so the two do not collide.
  - Depends on: E-03
  - Expected outcome: budget exhaustion yields a terminal disposition naming the attempts spent, visible on a read surface, with no unbounded loop.
  - Execution notes: Exhaustion writes `TURN_RETRY_EXHAUSTED_STATUS = 'failed-safely'`, an EXISTING member of both drivers' `TERMINAL_STATES` and of `runner_shutdown.KNOWN_ITEM_STATUSES`, so no new status is invented and `observe_ledger` still reports the run coherent (verified). The reason names the attempts spent and reaches the read surface through `r2i1b1`'s ONE `Refusal` writer rather than a new key, which matters because the diagnostics block's legacy arm reads the specific key `driver_error` for only three statuses while a `Refusal` renders for ANY status. `r2i1b1` HAD landed at execution time (it is in `.aw/records/plans/executed/`), so its shared refusal record was USED rather than a parallel field added, which is what the item instructed for that case. `render_stream.py` was NOT edited, so it stayed out of Scope-Paths as the plan intended.
  - Execution state: performed

### Task group 3: prove the boundaries, not just the happy path

- [x] E-06 Test the matrix with FIXTURES, never against live run records: `.aw/records/runs/` is gitignored with zero tracked files, so a test keyed to live runs is unrunnable in CI and in every lane worktree. The RULE is documented in `tests/test_run_viewer.py:1-5` and again at `:22-27` ("a new test must NOT read the live repository via `dir='.'`"), and that module's fixture helpers are the pattern to copy. CORRECTED AT REVIEW: the plan cited that header as documenting "23 tests reading it fail in a fresh checkout"; no such count appears in the file (75 test functions, no `23`), so cite the RULE and not the invented number.
  Cover, as separate cases: a retryable failure at budget 2 gets exactly 2 correction attempts then escalates; the SAME failure at budget 0 gets none and escalates immediately; a NON-retryable class gets none at ANY budget including 10 (the item's explicit requirement); a deliberate operator stop is never retried; a resumed run keeps its originally frozen budget even if a different `--retry-budget` is passed to the resume; and `plan_retry`'s idempotency means a repeated attempt key does not double-spend.
  MEASURE THE PRE-CHANGE FAILURE AT YOUR OWN HEAD, NOT AT `a2e0438a`. Two of these six cases are ALREADY GREEN before any change and must not be presented as proving the wiring: the resume case is already guaranteed by `refuse_frozen_flags_on_resume` (`runner_shared.py:2131-2152`), which REFUSES `--retry-budget` on resume outright rather than letting it override, and the idempotency case is already pinned by `tests/test_run_recovery_cli.py:133-143`. Both are still worth writing as regression coverage; state plainly which cases are new behavior and which are characterization, and paste the pre-change result for each rather than asserting a single blanket failure.
  - Depends on: E-04, E-05
  - Expected outcome: six fixture cases passing in a bare worktree; the budget-2 case fails before the change, with the two already-green cases labelled as characterization rather than proof.
  - Execution notes: `tests/test_retry_consumption.py`, 49 tests, entirely FIXTURE-BASED: every state dict is built in-process and the two cases needing a run directory use `tempfile`, so nothing reads `.aw/records/runs/` and nothing passes `dir='.'`. All six required boundary cases are covered and EACH IS LABELLED new-behavior or characterization, per the item's instruction: budget 2 gives exactly 2 then escalates (new), budget 0 gives none (new), a non-retryable class gives none at budget 10 (new), a deliberate stop is never retried (new), a resume keeps the frozen budget (characterization: already guaranteed by `refuse_frozen_flags_on_resume`, which REFUSES the flag outright), and a repeated idempotency key does not double-spend (characterization of an already-pinned property re-proved on the NEW substrate, which has its own key).
  - Execution state: performed

- [x] E-07 Confirm both hosts share the wiring by OBJECT IDENTITY, not by grep, per the anti-re-fork discipline the `rununify` work established. Both runners must reach the same consumption function rather than each carrying a near-copy, which is the exact drift `run_recovery`'s own history warns about and which `plan_readiness` was created to end. The shared symbol must live in `runner_shared.py`.
  USE THE RIGHT GUARD; THE ONE THE PLAN NAMED POLICES SOMETHING ELSE (review, F-14). `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` (`:1552`) checks that neither driver re-introduces a private dependency REGEX or the deleted `_DEPS_RE`/`_read_deps` parser; it makes no cross-host identity assertion. The guard that does is `tests/test_runner_refork_guard.py`, whose `SymmetricReForkGuardTests::test_every_runner_attribute_is_the_owning_modules_object` (`:287`) asserts object identity against a `REFORK_TABLE` of `Owned(symbol, owning_module, drivers)` rows. A new `runner_shared`-owned symbol belongs in THAT table. Read the comment at `tests/test_runner_item_dependencies.py:1616-1630` first: it explains why an `oc_runipd`-OWNED shared symbol cannot go in `REFORK_TABLE` and lives in `_SHARED_NAMES` instead. Pick the correct home for the symbol you actually add and say why.
  "NO NEW CROSS-DRIVER IMPORT" MUST BE A COUNTED DELTA, NOT AN ABSENCE. `agy_runipd` already imports from `oc_runipd` at four module-level sites (`:273`, `:315`, `:340`, `:1385`) plus several function-level ones (for example `:2310`, `:2319`, `:2326`, `:2338`), so any test or grep asserting zero such imports would fail against unmodified code and any claim of "no cross-driver import" is simply false. Count them before the change, count them after, and paste both numbers.
  - Depends on: E-06
  - Expected outcome: an identity assertion showing both hosts resolve to the same function object, registered in the correct guard table; the oc-to-agy import count unchanged, with the before and after counts pasted.
  - Execution notes: Six symbols re-exported from `runner_shared` into BOTH drivers in the `as <same-name>` form and registered in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE`, which is the correct table rather than the one the plan named: `AntiDivergenceGuardTests` polices dependency REGEXES and makes no cross-host identity assertion, while `REFORK_TABLE`'s `Owned(symbol, owner, drivers)` rows assert exactly the object identity this item demands, and `_SHARED_NAMES` is for `oc_runipd`-OWNED names (these are `runner_shared`-owned). The CLASSIFICATION TABLE is registered too, not only the functions, because a host carrying its own copy would agree about the mechanism and disagree about which failures are retryable. THE IMPORT DELTA IS COUNTED, not asserted absent: agy->oc imports measured by AST BEFORE = 4 module-level + 4 function-level = 8; AFTER = 4 + 4 = 8, UNCHANGED (the new symbols come from `runner_shared`, never through the peer driver). `tests/test_runner_refork_guard.py` was added to `Scope-Paths` as an ADDITIVE widening before commit, since E-07 requires editing it and the original declaration omitted it.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The budget layer is DORMANT, not missing: `plan_retry` (`run_recovery.py:269`), `retry_budget_remaining` (`:415`), `RetryLimitExceededError` (`:87`) and `validate_retry_budget` (`:136`) all exist and are tested. Only the spending call site is absent.
- `validate_retry_budget` IS now wired in production, via `runner_shared.resolve_retry_budget` (`:1764`), which `uyeko5` added. The item's claim that all three symbols have zero callers is stale for this one; the range bound is therefore out of scope here.
- `DEFAULT_RETRY_LIMIT` is 2 and the reasoning is recorded at `run_recovery.py:53-64`: a retry is a CORRECTION attempt, "a retry cannot turn failure into success by mere repetition", so a corrector still failing after two passes usually faces a plan defect and a third attempt mostly buys another paid turn. That is the cost model this plan must respect.
- `0` is a LEGAL budget meaning no retries, and `run_recovery.py:69-70` explicitly warns that a falsy check must not treat it as unset.
- The MIDDLE precedence tier (repository policy) is deliberately NOT implemented and deliberately NOT faked: `resolve_retry_budget`'s docstring says so and points at backlog `dh3us4`. Do not add it here.
- The frozen value is resolved at freeze time on purpose (`runner_shared.py:1836-1837`), so a resumed run reads a stable integer. Re-reading `args` per turn is the documented mistake.
- `failed-safely` is used both for a real driver error and for cases the classifier can confuse with a deliberate operator stop (`oc_runipd.py:5852-5853`). That is why E-01 is an allowlist.
- Both hosts are expected to share such logic through `runner_shared.py`, and an anti-divergence guard tests for re-forking.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | THE SEQUENCING GATE IS SATISFIED: `uyeko5`, which the item names as the prerequisite owning the flag and the frozen value, has EXECUTED. | `.aw/records/plans/executed/20260903-runflags-01-uyeko5-...ipd.md`, `- Status: executed` |
| F-2 | The two spending helpers are still dormant at HEAD: `plan_retry` and `retry_budget_remaining` appear only in `run_recovery.py` and `tests/test_run_recovery_cli.py`. | symbol search at `a2e0438a` |
| F-3 | ONE CLAIM IN THE ITEM IS STALE, which narrows this plan: `validate_retry_budget` now HAS a production caller, `runner_shared.resolve_retry_budget`. | `run_recovery.py:136` called at `runner_shared.py:1764` |
| F-4 | The frozen budget exists to be read, resolved to an effective integer at freeze time specifically so no later reader re-resolves it. | `runner_shared.py:1836-1837` and the docstring above it |
| F-5 | `0` is a legal budget and must not be treated as unset by a truthiness check. | `run_recovery.py:69-70` |
| F-6 | The repository-policy tier is deliberately absent and tracked elsewhere, so this plan must not add it. | `resolve_retry_budget` docstring; backlog `dh3us4` (`blocked`) |
| F-7 | `failed-safely` conflates a driver error with a possible deliberate operator stop, so a denylist approach would retry an operator's stop. | `oc_runipd.py:5852-5853`, `:5883`, `:5905` |
| F-8 | The helpers' semantics are already pinned by tests, so the runner must call them rather than reimplement: retry preserves the failed attempt, is idempotent per key, and raises on exhaustion. | `tests/test_run_recovery_cli.py:124-131`, `:133-143`, `:145-160`, `:215-227` |
| F-9 | The cost model is explicit and argues for a small budget: a correction attempt is a paid model turn and repetition alone cannot fix a plan defect. | `run_recovery.py:53-64` |
| F-10 | The adjacent items are genuinely distinct and neither closes this: `dh3us4` covers only the policy tier and PRESUMES consumption exists, and `sq61qd` (executed) added only the range check and its own history says the helpers "remain DORMANT". | backlog `dh3us4`; `.aw/records/plans/executed/...sq61qd...ipd.md` |
| F-11 | A reason recorded only in `events.jsonl` reaches no read surface, AND per-item state is not sufficient either: the diagnostics renderer reads the specific key `driver_error` for exactly three statuses, so a reason under any other key renders nowhere. | no surface greps `orchestrator-deferred`; `render_stream.py:2166-2171` (three statuses, `driver_error` key) versus `:2157-2165` / `:2172-2173` (other keys) |
| F-12 | THE PLAN'S CENTRAL MECHANISM IS UNREACHABLE FROM THE DECLARED FILES. Both helpers require a `RunEngine` over a `ledger.jsonl`; no driver run has one, neither driver imports `run_engine`, and the two state vocabularies are disjoint. | `run_recovery.py:269-277`, `:415-417`, `:295-303`; `run_engine.py:117-127`; 0 `ledger.jsonl` in 143 run dirs; `rg -c 'run_ledger_store\|RunLedgerStore'` on both drivers -> no match; spec `25kzda:28`; `oc_runipd.py:317-334` |
| F-13 | The evidence-invalidation seam EXISTS and is inside `plan_retry` itself, appending a `correction` record with `invalidates_seq`; `set_lifecycle` reuses the same idiom. So E-04's "locate it or stop" is answered, and the answer is engine-side. | `run_recovery.py:329-345`, `:237`; `set_lifecycle.py:66-95` |
| F-14 | E-07 named the wrong guard, and its "no new cross-driver import" bar is unmeasurable as stated: `AntiDivergenceGuardTests` polices dependency regexes, the identity guard is `test_runner_refork_guard.py`, and `agy_runipd` already imports from `oc_runipd` at four module-level sites. | `tests/test_runner_item_dependencies.py:1552-1613`, `:1616-1630`; `tests/test_runner_refork_guard.py:262-336`; `agy_runipd.py:273`, `:315`, `:340`, `:1385` |
| F-15 | OQ-01's premise expired: `wyw936` is `graduated`, not `open`, and is owned by plan `1bfppy` (`reviewed`, `go-pending-approval`, `From-Backlog: wyw936`), so the recommended option (a) is now available. | backlog `wyw936` `- Status: graduated`; `1bfppy` front matter `:17-25` |
| F-16 | The stated suite baseline is wrong in both halves and blames a test that passes. | bare `python3 -m pytest` at `09beb137` -> `1 failed, 5958 passed, 3 skipped, 2 xfailed`, failing `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`; `tests/test_orchestrator_retirement.py` -> `112 passed`; `.gitignore:49` |
| F-17 | Two of E-06's six cases are already green before any change: resume-freeze is enforced by a REFUSAL, and idempotency is already pinned. | `runner_shared.py:2131-2152`; `tests/test_run_recovery_cli.py:133-143` |
| F-18 | Budget exhaustion cannot introduce a new item status: the status set is closed and `observe_ledger` declares a run incoherent on any value outside it. | `oc_runipd.py:317-334`; `runner_shutdown.py:64-83`, `:299-325` |
| F-19 | `r2i1b1` has NOT landed (`approved`, still in `pending/`) and overlaps this plan in three files, so the relationship is merge ordering rather than availability. | `.aw/records/plans/pending/20260907-orchprobe-01-r2i1b1-...ipd.md:8-11` |

## Proposed changes (ordered, validatable)

0. SETTLE OQ-03 FIRST (which substrate the budget is spent in), then re-state E-03/E-04 and `Scope-Paths` to match the chosen shape. Steps 1 and 2 below are valid under every shape and may be authored against any of them; steps 3 to 5 are not.
1. Define the retryable-class ALLOWLIST with per-class justification (E-01).
2. Read the frozen budget, treating 0 as legal (E-02).
3. Spend it through `plan_retry`/`retry_budget_remaining` (E-03).
4. Send a correction packet of only failed predicates and invalidate stale evidence (E-04).
5. Escalate on exhaustion to a terminal disposition visible on a read surface (E-05).
6. Test the six boundary cases with fixtures (E-06).
7. Assert both hosts share the wiring by object identity (E-07).

## Deferred / out of scope (with reason)

- THE REPOSITORY-POLICY PRECEDENCE TIER. Owned by backlog `dh3us4` (`blocked` on `uyeko5`), and `resolve_retry_budget` deliberately does not fake it. Adding it here would take over another item's scope.
- THE 0..10 RANGE BOUND. Already shipped by executed plan `sq61qd` and already reached at parse time through `resolve_retry_budget`. Re-checking it in the loop is the off-by-one the existing comment warns about.
- THE `--retry-budget` FLAG, ITS PRECEDENCE AND ITS FREEZING. Shipped by executed `uyeko5`. This plan consumes that value and adds no flag.
- ROUTING `CORRECTION_REQUIRED` BACK TO RUNNABLE. That is backlog `wyw936` (open, `Blocks-Release: next`), which the item calls "adjacent but distinct" and notes never mentions the budget helpers. The two should be SEQUENCED together (a correction route with no budget is unbounded; a budget with no correction route is dead), and OQ-01 carries that to the reviewer rather than absorbing another open item's scope.
- INTEGRATION-RETRY COUNTS. The item is emphatic and correct: re-attempting a MERGE costs a `git status` and a `git merge-tree` and repetition genuinely can succeed, so it is a different knob with a much larger default. Nothing here changes it.

## Scope check

- Over-scope: none as declared. Two runner modules, the shared module they both use, and one new test module.
- Under-scope: the policy tier, the range bound, the flag surface, `wyw936`'s verdict routing, and integration retries are all left alone (see Deferred).
- SCOPE-PATHS MAY BE INSUFFICIENT, DEPENDING ON OQ-03, AND THAT IS THE HONEST STATE (review, PR-001). The declared four paths fit shape (b) only. Shape (a) needs whatever wires a ledger into the drivers; shape (c) needs `run_cli.py` and/or `ipd_set_plan.py`/`set_lifecycle.py` and drops one or both runner modules. Do NOT execute against the current declaration under shape (a) or (c): re-declare `Scope-Paths` first, because the runners announce declared paths before a run starts and the finalize gate reconciles what was actually changed against what was declared. Note also that E-05's rendering check CALLS `render_stream` from a test and needs no edit to it, so `render_stream.py` is deliberately absent; if the renderer itself must change, that is `r2i1b1`'s scope.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. BASELINE RE-MEASURED AT REVIEW (HEAD `09beb137`): `1 failed, 5958 passed, 3 skipped, 2 xfailed in 54.60s`. The one failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, and its cause is ANOTHER PARTY'S gitignored `opencode-recovery/` tree (`.gitignore:49`, 1746 files of session transcripts) tripping a contract-prose parity assertion. DO NOT "fix" it and DO NOT delete that directory: it is not yours, and the shared-checkout rule forbids touching it. `tests/test_orchestrator_retirement.py` PASSES (`112 passed`), so the plan's original baseline named a test that is green and a count that is 310 low. Compare failing NODE IDS, never totals: other agents land tests continuously, so the total moves within a day. Expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_retry_consumption.py tests/test_run_recovery_cli.py` for the focused surface. The existing recovery tests must pass UNMODIFIED: they pin the helper semantics this plan consumes.
- The six boundary cases from E-06, each with its own pasted result.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

Spec `25kzda` (`aw run deterministic run and verify`, `- Status: approved`) sections 2.1, 4.1, 4.2, 5.2 and 5.5 already SPECIFY this behavior, so this plan IMPLEMENTS the spec rather than amending it and no `.spec.md` file is declared in `Scope-Paths`. RE-READ AT REVIEW, AND SECTION 5.5 IS TIGHTER THAN THE PLAN'S PROSE, so quote it rather than paraphrasing: it enumerates FIVE retryable classes (host spawn failure; host nonzero exit that did not create an ambiguous side effect; missing artifact or failed deterministic check for which a bounded correction is safe; missing or stale validation evidence; verifier transport failure) and TEN never-retryable ones (out-of-scope mutation; overlapping ownership or lease conflict; corrupt ledger; unknown commit or transaction outcome; unauthorized status change; human approval gate; hook bypass attempt; push attempt; changed frozen requirements; any non-idempotent external action whose outcome is unknown), and states that "a human gate and dependency-not-met outcome are state gates, not retryable failures". E-01's allowlist must be derived from THAT list, mapped onto the drivers' actual disposition vocabulary, with any driver status that cannot be mapped to exactly one spec class EXCLUDED and the reason recorded. NOTE THE TENSION OQ-03 EXPOSES: 5.5 says budget may not be spent when the ledger is corrupt, and Section 5.3 lists "frozen retry budget, and remaining retries" among the LEDGER's required contents, so the spec plainly assumes the ledger substrate. If OQ-03 selects shape (b), the implementation will satisfy 5.5's retry SEMANTICS on a substrate 5.3 does not describe; say so plainly in the executed plan and state whether that requires a spec amendment (in which case declare the spec path first, per the plan-may-amend-a-spec rule) or is an acceptable implementation-detail difference, since 5.3 says "the storage location is an implementation detail; the data contract is not". Two obligations follow. FIRST, the executor must READ those sections and reconcile the implementation against them, reporting any place the spec demands something this plan does not do (a spec that describes dormant behavior is exactly how this item arose). SECOND, `--retry-budget`'s `--help` text currently discloses that the middle precedence tier is unimplemented; if wiring consumption changes what that flag observably does, the help text must be updated in the same change so the flag stops describing a dormant layer. If the executor concludes the spec itself is wrong about the correction protocol, declare the spec path in `Scope-Paths` and justify the amendment BEFORE editing, per the plan-may-amend-a-spec rule.

## Open questions

### OQ-01: Must `wyw936` land with or before this plan, since a correction route and a correction budget are only useful together?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): OPTION (a), LAND `1bfppy` FIRST, THEN THIS PLAN, giving the full correction loop. Option (b) land-alone was declined, and a HARD `- Item-Dependencies:` edge was deliberately NOT taken: the reviewer recommended against it and the maintainer agreed, because neither plan breaks the other, so an enforced edge would block this plan on a PREFERENCE rather than a correctness constraint and would leave it waiting indefinitely if `1bfppy` is not approved. Contrast `xo3244` OQ-03 in the same round, where an edge WAS declared because the wrong order silently fails; here the wrong order merely half-builds.
  SO THIS IS A SEQUENCING PREFERENCE, NOT A GATE, and it must be honored by whoever approves rather than by the runner. `- Item-Dependencies:` on this plan stays as it was.
  THE EXPIRED PREMISE IS CONFIRMED EXPIRED, re-measured at HEAD `e8f4b2ed`. This question was authored on the finding that "`wyw936` is still `open` with no plan", which made option (a) impossible. Today backlog `wyw936` reads `- Status: graduated`, and plan `1bfppy` carries `- From-Backlog: wyw936`, `- Status: reviewed`, `- Readiness: go-pending-approval`, `- Blocks-Release: next`. So option (a) costs an APPROVAL, not a graduation, and the option (c) the plan once contemplated is dead.
  THE RISK OF LANDING ALONE IS UNCHANGED AND IS WHY THE ORDER MATTERS: the budget would become spendable on failures the runner already classifies as failures, while the verdict path that SHOULD trigger a correction still records success, so the most valuable trigger stays disconnected. The item's own framing holds: "a correction route with no budget is unbounded and a budget with no correction route is dead."
  THE SHARED-FILE OVERLAP IS MERGE ORDERING, NOT A HAZARD, and was verified rather than assumed: both plans declare `runner_shared.py`, `oc_runipd.py` and `agy_runipd.py` in `Scope-Paths`. Each execute item runs in an isolated worktree and returns through the merge-and-revalidate gate, so co-declared files are not a concurrency risk; whichever lands second simply merges onto the first.

### OQ-02: Should a correction attempt be visible as a separate ATTEMPT in the run summary, or folded into the item's single row?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE FROM THE CODE, recorded so the answer is deliberate. The run summary and `execution-report.md` already render an `Attempts` count per item, sourced from `len(item["attempts"])` (`oc_runipd.py:3202-3208`), and the driver appends one record per attempt (`:6068`). `plan_retry` likewise PRESERVES the failed attempt rather than replacing it, so both substrates support showing both. RECOMMENDATION: let the attempt count reflect corrections (it already would, since each attempt appends a record) and put the ESCALATION reason in the per-item surface from E-05, rather than adding a new column. Confirm by rendering a fixture run before choosing, since a column change is a contract change for anything parsing that table. Verified at review that the `Attempts` column already exists, so no new column is needed for the count itself.

### OQ-03: The shipped helpers need a `RunEngine` over a `ledger.jsonl` that no driver run has. Which substrate should the budget actually be spent in?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): OPTION (b), SPEND THE BUDGET IN THE DRIVERS' OWN `state.json`/`events.jsonl` SUBSTRATE, reusing the shipped helpers' SEMANTICS without calling the ledger-bound functions. Three alternatives were declined: (a) wire the drivers to a ledger first (rejected as a large separate piece of work this plan's `Scope-Paths` do not cover, which would block the retry improvement behind it), retiring this plan in favor of ledger-first (rejected because a recoverable failure is currently not retried at all), and deferring until the ledger question is settled separately (rejected, though offered, since two other plans already flag it as open).
  THE MEASUREMENT WAS RE-VERIFIED AT HEAD `e8f4b2ed`, not carried over on trust, because it is what makes the plan-as-written unbuildable. `plan_retry` takes `engine: run_engine.RunEngine` as its FIRST parameter (`run_recovery.py:269-277`). ZERO `ledger.jsonl` files exist across 143 run directories, and `grep -c` for `run_engine|RunLedgerStore|run_ledger_store` returns 0 in BOTH `oc_runipd.py` and `agy_runipd.py`. Spec `25kzda:29` concedes it in its own words: "the ledger is built but UNWIRED". THE VOCABULARIES ARE ALSO DISJOINT: `run_recovery.py:295-303` refuses anything outside `STATE_FAILED`/`STATE_BLOCKED`, while a driver item carries `failed-safely`, `partial`, `interrupted`, `substantially-complete`, `dependency-blocked`, `integration-blocked`, `merge-conflict` and others (`oc_runipd.py:317-334`). So the declared instruction has no executable form.
  THE ACCEPTED COST IS DUPLICATION, AND IT MUST BE STATED IN THE CODE, NOT ONLY HERE. This is a SECOND implementation of retry semantics, which this repository normally refuses, so the executor MUST record at the implementation site that the shipped helpers in `run_recovery.py` remain the INTENDED long-term home and that this substrate choice was a deliberate maintainer decision of 2026-09-10, with a pointer to the ledger-wiring question. Without that note the next reader will read the duplication as an accident and either delete it or fork it further.
  WHAT MUST BE PRESERVED FROM THE HELPERS' SEMANTICS, since only the substrate changes: preserve the failed attempt rather than overwriting it, carry an idempotency key so a retry cannot double-spend, escalate when the budget is exhausted rather than looping, and invalidate stale evidence from the superseded attempt. A re-implementation that keeps the budget arithmetic but drops evidence invalidation would be the dangerous half.
  THIS ANSWER DOES NOT SETTLE WHETHER DRIVERS SHOULD EVER WRITE A LEDGER. That question stays open and is explicitly declined by `i1hlgx` ("whether drivers SHOULD write a ledger is genuinely open") and by executed `7wei1o` (the remaining half of backlog `zrzfkw`). Nobody may cite this answer as a decision to abandon the ledger design; it is a decision about where THIS plan's retry work lives.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the allowlist source with the per-class justification comments, AND paste a table of every disposition value in the runners' vocabulary with its retryable verdict. Explicitly show that a deliberate operator stop is NOT retryable, naming the code path that distinguishes it (or, if it cannot be distinguished, showing that the conflated class is excluded).
  - Observed evidence: see the pasted evidence below.
    ALLOWLIST SOURCE (`runner_shared.py`), with its justification comment:

    ```python
    #: WHY `partial` IS **NOT** HERE, decided during execution ... `partial` means the turn RAN and fell
    #: short ... re-dispatching every such item is ALREADY OWNED by approved sibling plan `dy9ymn` ...
    #: whose scope says in terms: "EXCLUDES retrying any item that produced ANY evidence of work".
    TURN_RETRYABLE_DISPOSITIONS: frozenset[str] = frozenset({"failed-safely"})
    ```

    EVERY DISPOSITION IN THE RUNNERS' VOCABULARY WITH ITS VERDICT (printed from the shipped table):

    ```text
    disposition                retryable  reason (first 68 chars)
    ------------------------------------------------------------------------------------------------
    failed-safely              True       spec 5.5 'host spawn failure' / 'host nonzero exit': the turn failed
    partial                    False      the turn RAN and fell short, which spec 5.5 does not put in the host
    executed                   False      success; there is nothing to correct
    substantially-complete     False      the work landed but a gate refused. Its ONE retryable sub-class (a r
    reviewed                   False      a review outcome, not a failed execution
    approved                   False      a review outcome, not a failed execution
    blocked                    False      spec 5.5: 'a human gate and dependency-not-met outcome are state gat
    dependency-blocked         False      spec 5.5's state gate: the unmet edge is the cause, and repetition c
    not-attempted              False      nothing ran, so there is no failure to correct
    integration-blocked        False      owned by the INTEGRATION DEFERRAL LADDER, which has its own budget a
    merge-conflict             False      as `integration-blocked`: the integration ladder owns it
    merge-needs-human          False      as `integration-blocked`: the integration ladder owns it
    merge-refused              False      as `integration-blocked`: the integration ladder owns it
    integration-deferred       False      NON-TERMINAL and already awaiting the integration ladder's own re-at
    merge-retry                False      as `integration-deferred`: the integration ladder owns it
    merge-unchecked            False      as `integration-deferred`: the integration ladder owns it
    interrupted                False      an INTERRUPT is not a failure of the work. `requeue_interrupted` alr
    unknown_outcome            False      spec 5.5's 'unknown commit or transaction outcome' and 'any non-idem
    queued                     False      not a finished turn; it has not run yet
    running                    False      not a finished turn; it is still in flight

    ALLOWLIST: ['failed-safely']
    uncovered in oc TERMINAL_STATES : []
    uncovered in agy TERMINAL_STATES: []
    uncovered in KNOWN_ITEM_STATUSES: []
    ```

    A DELIBERATE OPERATOR STOP IS NOT RETRYABLE, and the code path that distinguishes it is named: the
    `stopped` record is read DIRECTLY in `turn_failure_is_retryable` rather than trusted to have been
    mapped to `interrupted` by `reconcile_disposition` (whose own comment records that WITHOUT that branch
    a stop reconciles as `failed-safely`, which IS in the allowlist - so this is the conflated class the
    item required be excluded):

    ```text
      stop  -> (False, 'the turn ended in a DELIBERATE OPERATOR STOP, which is an intent and not a
                        failure; retrying it would spend paid model turns fighting the operator')
      plain -> (True, "disposition 'failed-safely' is in spec 5.5's retryable host-failure class")
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a fixture run's `state.json` frozen `retry_budget` value and a trace or print showing the loop READ that value rather than calling `resolve_retry_budget`. Paste the `--retry-budget 0` case proving zero retries occur (not the default 2), which is what proves the `is None` guard rather than a truthiness check.
  - Observed evidence: see the pasted evidence below.
    THE FROZEN VALUE IS READ, not `args`. Fixture run state and the loop's read:

    ```text
    fixture state.json options: {"retry_budget": 0}
    frozen_retry_budget(state)  -> 0
    decision at budget 0        -> retry=False exhausted=True budget=0 attempts=0
    --retry-budget 0 result     -> failed-safely | corrections spent: 0
    ```

    THE `--retry-budget 0` CASE PROVES THE `is None` GUARD RATHER THAN A TRUTHINESS CHECK: zero
    corrections occur, not the default 2. The two reads are measurably different, which a truthy check
    would make equal:

    ```text
    frozen_retry_budget({"options": {"retry_budget": 0}}) -> 0
    frozen_retry_budget({"options": {}})                  -> 2
    ```

    THE LOOP DOES NOT RE-RESOLVE THE FLAG, asserted on source rather than claimed:
    `test_the_decision_does_not_re_resolve_the_flag` requires `frozen_retry_budget(state)` present and
    `resolve_retry_budget(` ABSENT in `turn_retry_decision`. Both hold (49 passed).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: FIRST paste the maintainer's answer to OQ-03 and the re-stated E-03 it produced; a `V-03` marked complete while OQ-03 is open is invalid on its face. Then paste the retry records produced for one retryable failure showing the FAILED attempt still present alongside the retry, the value returned by `retry_budget_remaining` after each spend, and a grep proving the runner calls the helpers rather than counting attempts itself. If the chosen shape means the runner does NOT call `plan_retry` directly, state exactly what does and show the call chain from the driver to it.
  - Observed evidence: see the pasted evidence below.
    FIRST, OQ-03'S ANSWER AND THE RE-STATED ITEM. OQ-03 is `Status: resolved`, answered by the
    maintainer 2026-09-10: OPTION (b), spend the budget in the drivers' own `state.json`/`events.jsonl`
    substrate, reusing the shipped helpers' SEMANTICS without calling the ledger-bound functions, because
    `plan_retry`/`retry_budget_remaining` take a `RunEngine` over a `ledger.jsonl` that no driver run has.
    E-03 was therefore re-stated before performing (see its execution state) from "call `plan_retry`" to
    "reuse its four semantics on the driver substrate, and say so in the code".

    RE-VERIFIED AT EXECUTION that the helpers are still uncalled from production, so this change did not
    make the dormancy worse:

    ```text
    $ rg -n "plan_retry|retry_budget_remaining" --type py
    agent_workflows/run_recovery.py   (definitions + its own docstrings)
    tests/test_run_recovery_cli.py    (its tests)
    ```

    THE RUNNER DOES NOT COUNT ATTEMPTS ITSELF; it calls the ONE shared decision. Every call site:

    ```text
    $ rg -n "handle_turn_failure_retry\(|turn_retry_decision\(" agent_workflows/*.py
    agent_workflows/runner_shared.py:3552:def turn_retry_decision(
    agent_workflows/runner_shared.py:3786:def handle_turn_failure_retry(
    agent_workflows/runner_shared.py:3812:    decision = turn_retry_decision(item, state, disposition, attempt_no)
    agent_workflows/runner_shared.py:19556:            disposition = handle_turn_failure_retry(
    ```

    THE CALL CHAIN FROM EACH DRIVER, since the chosen shape means the runner does NOT call `plan_retry`
    directly (the item requires this be stated exactly):

    ```text
    oc_runipd.execute_item  -> runner_shared.execute_item_core(...)   present=True
    agy_runipd.execute_item -> runner_shared.execute_item_core(...)   present=True
    runner_shared.execute_item_core -> handle_turn_failure_retry -> turn_retry_decision -> frozen_retry_budget
      handle_turn_failure_retry calls turn_retry_decision? True
      turn_retry_decision calls frozen_retry_budget?       True
    ```

    THE FAILED ATTEMPT IS PRESERVED ALONGSIDE THE RETRY, and remaining budget is REPORTED rather than
    recomputed by the caller:

    ```text
    disposition returned                     : queued
    FAILED attempt PRESERVED                 : [1] (was [1])
    turn_retry_budget_remaining after spend 1: 1
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the correction packet actually sent, showing it names ONLY the failed predicates and not the passing ones, and name the construction path that built it by symbol. Paste a demonstration that evidence captured by the failed attempt does NOT satisfy the retried attempt: the `correction` record carrying `invalidates_seq` and the retried attempt re-collecting evidence. Confirm you reused the seam at `run_recovery.py:329-345` (or `set_lifecycle.make_invalidation_records`) and wrote NO second invalidation path; a grep showing exactly one producer of `invalidates_seq` per substrate satisfies this.
  - Observed evidence: see the pasted evidence below.
    THE CORRECTION PACKET ACTUALLY SENT, read back from the attempt record, showing it names ONLY
    failed predicates and NOT the passing summary that was present on the outcome:

    ```json
    {
      "kind": "correction",
      "attempt": 1,
      "of": 2,
      "idempotency_key": "xipfy1:attempt-1",
      "failed_predicates": [
        "the previous turn ended 'failed-safely' without a terminal transition",
        "incomplete requirement reported by the turn itself: E-03 not performed"
      ],
      "evidence_invalidated": true,
      "instruction": "This is a BOUNDED CORRECTION, not a fresh execution. Address ONLY the failed
                      predicates listed here; work that already passed must not be redone. Evidence
                      captured by the failed attempt has been INVALIDATED and may not be reused -
                      re-collect it."
    }

    passing summary ("A PASSING THING THAT MUST NOT BE RE-SENT") present in packet? False
    ```

    THE CONSTRUCTION PATH, NAMED BY SYMBOL as the item demands: `runner_shared.turn_correction_packet`
    builds it and `runner_shared.build_correction_notice` renders it into the next turn's prompt through
    `build_prompt`. `run_packet.build_step_packet` is deliberately NOT used: it builds from a WORKFLOW
    mapping and a `step_id`, neither of which a driver queue item has.

    THE PROMPT-CONSTRUCTION PATH HAD TO CHANGE AND THE REASON IS MEASURED, stated plainly because the
    first shape was INERT on the default path. Carrying the packet for `Prior attempt:` to interpolate
    fails on an ISOLATED turn, and isolation is the DEFAULT:

    ```text
    turn_correction in lane_containment._PRIOR_ATTEMPT_SAFE_KEYS? False
    ```

    So it is rendered as its own notice instead. RENDERED OUTPUT on an ISOLATED turn (the default path):

    ```text
    ## This is a BOUNDED CORRECTION attempt (1 of 2)

    The previous attempt FAILED and the run is spending one unit of its correction budget on
    this turn. Address ONLY the failed predicates below. Work that already passed must NOT be
    redone: this is a correction, not a fresh execution, and redoing passing work risks undoing it.

    Failed predicates:
      - the previous turn ended 'failed-safely' without a terminal transition
      - incomplete requirement reported by the turn itself: E-03 not performed
      - incomplete requirement reported by the turn itself: V-02 evidence empty

    Evidence captured by the FAILED attempt has been INVALIDATED and may not be reused ...
    ```

    EVIDENCE FROM THE FAILED ATTEMPT CANNOT SATISFY THE RETRY. The `correction` record carrying the
    superseded attempt, and the fields actually cleared so the retried attempt must RE-COLLECT them:

    ```json
    [
      {
        "at": "2026-09-22T08:44:37+00:00",
        "kind": "correction",
        "invalidates_attempt": 1,
        "invalidated": ["last_outcome", "verification_status"],
        "reason": "the turn failed (failed-safely) in a retryable class, so the item is being handed
                   back to a correction turn carrying only the predicates that failed; correction
                   attempt 1 of 2"
      }
    ]
    verification_status after invalidation: None
    last_outcome after invalidation       : None
    ```

    EXACTLY ONE PRODUCER PER SUBSTRATE, asserted on source by
    `test_there_is_exactly_ONE_producer_of_invalidation_records`: one
    `item.setdefault(TURN_RETRY_INVALIDATIONS_KEY` site, one `def invalidate_turn_evidence(`, one key
    definition. The engine-side seam inside `plan_retry` (`run_recovery.py:329-345`) is UNTOUCHED and was
    not forked; this record deliberately reuses its `correction`/`invalidates_*` idiom.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the exhaustion case end to end: the `RetryLimitExceededError` being raised, the resulting terminal disposition, and the recorded attempts-spent count. Then paste RENDERED output, not state: call `render_stream.render_run_summary_table` on the fixture (or `aw runs` on a fixture run) and show your reason text actually appearing in the Diagnostics block. Show the status you chose is a member of BOTH `oc_runipd.TERMINAL_STATES` and `runner_shutdown.KNOWN_ITEM_STATUSES`, and paste `runner_shutdown.observe_ledger` returning coherent for the resulting queue. State whether `r2i1b1` had landed at execution time and which record shape was used.
  - Observed evidence: see the pasted evidence below.
    THE EXHAUSTION CASE END TO END at budget 2, three attempts:

    ```text
      attempt 1 -> queued
      attempt 2 -> queued
      attempt 3 -> failed-safely

    FINAL status: failed-safely | corrections spent: 2
    ```

    The escalation is the driver-substrate equivalent of `RetryLimitExceededError` ("escalate rather than
    loop"): the third failure does NOT buy a third correction, so total dispatches are bounded at
    `budget + 1`, pinned as a COUNT for budgets 0, 1, 2 and 5.

    THE STATUS IS A MEMBER OF BOTH CLOSED VOCABULARIES, and the resulting queue is still coherent:

    ```text
    status in oc TERMINAL_STATES?    True
    status in KNOWN_ITEM_STATUSES?   True
    observe_ledger -> True | 1 item(s), all in a defined state
    ```

    RENDERED OUTPUT, not state. `render_stream.render_run_summary_table` on the fixture, showing the
    reason and the attempts-spent count actually appearing in the Diagnostics block:

    ```text
    Diagnostics / Blocked Items:
      • xipfy1: failed-safely (the turn failed (failed-safely) in a retryable class and the run's
        correction budget is exhausted (2 of 2 correction attempts spent), so the item is FAILED rather
        than re-dispatched)
        → remedy: read the failed attempts before re-running: a correction budget spent without success
          usually means a PLAN DEFECT rather than a transient fault, so repetition will not fix it.
          Inspect them with `aw runs show <run-id>`, correct the plan or the environment, then re-run
          with `aw oc run xipfy1` (or `aw oc run resume <run-id> --retry-incomplete`). Do NOT discard
          the lane: the partial work is preserved there
    ```

    A DEFECT THE RENDERED CHECK CAUGHT, recorded because it is exactly why V-05 demands rendering rather
    than a state dict: the remedy first printed `aw oc run run xipfy1`, since `labels.command` ALREADY
    carries the verb. Invisible in state, obvious rendered. Fixed and pinned for both hosts
    (`test_the_remedy_names_a_RUNNABLE_command_on_both_hosts`).

    `r2i1b1` HAD LANDED at execution time (`.aw/records/plans/executed/20260907-orchprobe-01-r2i1b1-...`),
    so its SHARED refusal record was USED (`record_refusal`, code `turn-retry`) rather than a parallel
    field added, which is what the item instructed for that case. `render_stream.py` was NOT edited and
    stayed out of `Scope-Paths`, as the plan intended.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste all six cases with their results: budget 2 gives exactly 2 attempts then escalates; budget 0 gives none; a non-retryable class gives none at budget 10; a deliberate stop is never retried; a resume keeps the frozen budget despite a different flag value; a repeated idempotency key does not double-spend. For EACH case state whether it is new-behavior proof or characterization, and paste its PRE-CHANGE result measured at your own HEAD (named): the budget-2 case must fail, and the resume and idempotency cases are expected to pass already, for the reasons in F-17. Paste proof the tests are fixture-based (the fixture setup, and a run with `.aw/records/runs/` absent or with `dir=` pointed at a temp root, never `dir="."`).
  - Observed evidence: see the pasted evidence below.
    ALL SIX CASES, each with its result and its new-behavior/characterization label, from
    `tests/test_retry_consumption.py` (49 tests, `49 passed`):

    ```text
    1. budget 2 -> exactly 2 corrections then escalate  NEW            ['queued','queued','failed-safely']
    2. budget 0 -> no corrections, escalate immediately  NEW           failed-safely, 0 spent
    3. non-retryable class at budget 10 -> none          NEW           blocked/dependency-blocked/
                                                                       integration-blocked/unknown_outcome
                                                                       all returned UNCHANGED, 0 spent
    4. deliberate operator stop -> never retried         NEW           refused even at budget 10
    5. resume keeps the originally frozen budget         CHARACTERIZATION
    6. repeated idempotency key does not double-spend    CHARACTERIZATION
    ```

    WHY 5 AND 6 ARE LABELLED CHARACTERIZATION (the item required this be stated rather than presented as
    proof): case 5 is already guaranteed by `refuse_frozen_flags_on_resume`, which REFUSES `--retry-budget`
    on resume OUTRIGHT rather than letting it override (`retry_budget` is in the `RESUME_REFUSE` set,
    verified), and case 6's engine-side twin is already pinned by `tests/test_run_recovery_cli.py`. Both
    are still written, because this substrate has its OWN implementation of each property.

    PRE-CHANGE RESULT MEASURED AT MY OWN HEAD, `d1d6b6eb` (not at the plan's stale `a2e0438a`), by
    stashing only the three source files and `test_runner_refork_guard.py` and running the new test module
    against unmodified sources:

    ```text
    $ git stash push -- agent_workflows/runner_shared.py agent_workflows/oc_runipd.py \
          agent_workflows/agy_runipd.py tests/test_runner_refork_guard.py
    $ python3 -m pytest tests/test_retry_consumption.py -o addopts=""
    38 failed, 4 passed in 0.97s
    ```

    The budget-2 case is among the 38 FAILURES, as the plan requires. The 4 that PASS pre-change are
    exactly the characterization-adjacent ones that assert already-shipped properties: the resume refusal
    (`test_retry_budget_is_refused_on_resume_rather_than_allowed_to_override`), the frozen `0`-vs-unset
    guard and the malformed-value fallback (both already shipped by `zzcrlo`), and the "neither host
    carries its own copy" negative. AFTER restoring: `49 passed`.

    FIXTURE-BASED, PROVEN: every state dict is constructed in-process by the `_item`/`_state` helpers, and
    the two cases needing a run directory build it under `tempfile.TemporaryDirectory()` via `_run_dir`,
    which `mkdir`s only `outcomes/`. No test reads `.aw/records/runs/`, and no test passes `dir="."`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste an object-identity assertion (`oc_mod.<symbol> is agy_mod.<symbol>` or equivalent through `runner_shared`) and its True result, plus the guard-table row you added and which table it went in (`test_runner_refork_guard.REFORK_TABLE` or `test_runner_item_dependencies._SHARED_NAMES`) with the reason. Paste the oc-to-agy import count BEFORE and AFTER (they must match; a bare "no cross-driver import" claim is false, see F-14). Paste `tests/test_runner_refork_guard.py` and `tests/test_runner_item_dependencies.py` both passing. Paste the bare `python3 -m pytest` summary line AND the failing node-id list, compared to the re-measured baseline by NODE ID rather than by count.
  - Observed evidence: see the pasted evidence below.
    OBJECT-IDENTITY ASSERTION AND ITS TRUE RESULT, for all six shared symbols:

    ```text
      oc.TURN_RETRYABLE_DISPOSITIONS is agy.TURN_RETRYABLE_DISPOSITIONS -> True ; both are runner_shared's -> True
      oc.TURN_RETRY_CLASSIFICATION   is agy.TURN_RETRY_CLASSIFICATION   -> True ; both are runner_shared's -> True
      oc.turn_failure_is_retryable   is agy.turn_failure_is_retryable   -> True ; both are runner_shared's -> True
      oc.turn_retry_decision         is agy.turn_retry_decision         -> True ; both are runner_shared's -> True
      oc.turn_retry_budget_remaining is agy.turn_retry_budget_remaining -> True ; both are runner_shared's -> True
      oc.handle_turn_failure_retry   is agy.handle_turn_failure_retry   -> True ; both are runner_shared's -> True
    ```

    THE GUARD-TABLE ROWS ADDED, and WHICH TABLE AND WHY. They went in
    `tests/test_runner_refork_guard.py::REFORK_TABLE`, NOT `test_runner_item_dependencies._SHARED_NAMES`:
    `_SHARED_NAMES` exists for `oc_runipd`-OWNED names that agy must bind (its own comment records that
    `REFORK_TABLE` structurally cannot host one, since naming a runner as `owner` would make the AST half
    forbid that runner's own definition), and every symbol here is `runner_shared`-OWNED, so both halves
    of `REFORK_TABLE`'s contract apply unchanged. The plan named `AntiDivergenceGuardTests`; that class
    polices dependency REGEXES and makes no cross-host identity assertion, so it was the wrong guard.

    ```python
        Owned("TURN_RETRYABLE_DISPOSITIONS", "runner_shared", BOTH),
        Owned("TURN_RETRY_CLASSIFICATION", "runner_shared", BOTH),
        Owned("turn_failure_is_retryable", "runner_shared", BOTH),
        Owned("turn_retry_decision", "runner_shared", BOTH),
        Owned("turn_retry_budget_remaining", "runner_shared", BOTH),
        Owned("handle_turn_failure_retry", "runner_shared", BOTH),
    ```

    THE oc-TO-agy IMPORT COUNT, BEFORE AND AFTER, counted by AST rather than asserted absent (the plan's
    F-14 correction: a bare "no cross-driver import" claim would be FALSE, since agy already imports from
    oc at eight sites):

    ```text
    BEFORE (HEAD d1d6b6eb): module-level=4 [415, 477, 513, 555]  function-level=4 [1797, 2349, 2359, 2371]  TOTAL=8
    AFTER                  : module-level=4 [438, 500, 536, 578]  function-level=4 [1820, 2372, 2382, 2394]  TOTAL=8
    ```

    UNCHANGED at 8 (line numbers shifted only because the new re-export block sits above them). The new
    symbols are imported from `runner_shared`, never through the peer driver.

    BOTH GUARD MODULES PASS:

    ```text
    $ python3 -m pytest tests/test_runner_refork_guard.py tests/test_runner_item_dependencies.py
    69 passed in 17.51s
    ```

    BARE SUITE SUMMARY LINE, and the failing NODE ID compared to the baseline BY NODE ID rather than by
    count (the plan's own instruction, since other agents land tests continuously):

    ```text
    $ python3 -m pytest
    1 failed, 8206 passed, 3 skipped, 2 xfailed, 3 warnings in 111.60s (0:01:51)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```

    BASELINE AT MY OWN HEAD `d1d6b6eb`, measured BEFORE any edit: `1 failed, 8157 passed, 3 skipped,
    2 xfailed` failing THE SAME SINGLE NODE ID. So the failing set is IDENTICAL and this change introduced
    no failure. THAT FAILURE IS ENVIRONMENTAL, NOT MINE, and is proven so rather than asserted: the test
    requires `OPENCODE_CONFIG_CONTENT` to be ABSENT for a non-isolated turn, and it is present in THIS
    TURN'S OWN runner environment, which leaks into the child pytest. Unsetting it turns the module green
    with no source change:

    ```text
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts=""
    76 passed in 9.02s
    ```

    NOTE the plan's recorded baseline (`1 failed, 5958 passed`, failing
    `tests/test_reporting_contract.py::ParityTests::...`) is itself STALE: that test passes at my HEAD and
    the count has grown by ~2200. Compared by node id, as instructed, rather than by total.

    FOCUSED SURFACE, with `tests/test_run_recovery_cli.py` UNMODIFIED (`git diff --name-only tests/` lists
    only `test_runner_refork_guard.py`):

    ```text
    $ python3 -m pytest tests/test_retry_consumption.py tests/test_run_recovery_cli.py
    89 passed in 4.16s
    $ python3 -m pytest tests/test_retry_consumption.py tests/test_run_recovery_cli.py >/dev/null 2>&1; echo $?
    0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. TWO BLOCKING QUESTIONS ARE OPEN AND EITHER ONE REFUSES EXECUTION AT EVERY LINT CHECKPOINT. OQ-03 is the one that decides whether this plan is executable at all: the helpers it exists to call require a run ledger that no driver run has, so its answer may change `Scope-Paths` and rewrite E-03. OQ-01 is a sequencing preference about `1bfppy` (which owns `wyw936`) and is now an ordering choice between two reviewed plans rather than a request to absorb unowned scope. ANSWER OQ-03 FIRST: OQ-01's answer does not change under any shape, but OQ-03's answer may make OQ-01's subject moot.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE CONTENTION AND THE COST: `oc_runipd.py` and `agy_runipd.py` are the most heavily edited files in the repository, so re-locate every citation BY SYMBOL at execution time and never by the line numbers above; and be aware this plan makes the runner spend PAID MODEL TURNS on corrections, so a wiring error is expensive rather than merely wrong, which is why E-01's allowlist and E-06's budget-0 case come before anything else. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
