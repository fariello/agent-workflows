# IPD: the deterministic RUN- finding-code vocabulary over the shipped evidence layer

- Date: 2026-08-30
- Kind: child
- Concern: Spec `25kzda` 4.2 specifies 13 stable `RUN-*` finding codes, each with an exact operator-facing message and a recovery command, as the deterministic checker's public vocabulary. NONE of them exists: all 13 grep to ZERO hits across `agent_workflows/` at HEAD `738980ec`. The underlying checking machinery largely DOES ship (`run_evidence.py` carries a 13-class false-completion taxonomy under `EV-*` codes; `run_ledger_store.verify_chain` proves the hash chain; `run_recovery` handles retry and unknown outcomes), so what is missing is not the detection but the STABLE NAMES, MESSAGES, and RECOVERY COMMANDS an operator and a checker can rely on. Two further small gaps are also unbuilt: `--unverifiable-ok` aggregate neutrality (ZERO hits) and the spec's 0..10 bound on the retry budget.
- Scope: Define the 13 `RUN-*` finding codes with the spec's verbatim messages and recovery commands as a thin, data-driven vocabulary layer over the SHIPPED predicates in `run_evidence.py`, mapping each code to the shipped predicate that already decides it and marking explicitly those whose underlying machinery does NOT yet exist. NARROWED BY THE SPLIT (2026-09-04): `--unverifiable-ok` aggregate neutrality moved to Order 2 (`zub5f1`) and the retry-budget 0..10 range moved to Order 3 (`sq61qd`); this plan is now the code vocabulary ALONE. Excludes creating any new checker module, excludes reimplementing any shipped predicate, excludes wiring the codes into either runner module (deferred, see OQ-01), excludes `run_recovery.py` entirely, and excludes renaming the `aw run` verb group.
- Scope-Paths: agent_workflows/run_evidence.py, tests/test_run_evidence_completion.py
- Item-Dependencies: none
- Status: reviewed
- Set: runcodes
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: wlxkoz
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history
- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): SPLIT PERFORMED at the maintainer's direction, discharging F10 / review-round-2 PR-004 and clearing the DO-NOT-EXECUTE-AS-IS block this plan carried since 2026-08-31. Three children of the SAME Set, this plan keeping its id6 and Order: Order 1 `wlxkoz` (this plan) = the 13 `RUN-*` codes and their bindings; Order 2 `zub5f1` = `--unverifiable-ok` aggregate neutrality; Order 3 `sq61qd` = the retry-budget 0..10 range. Both children were scaffolded with `aw ipd scaffold` (ids minted, names derived) and authored review-ready, not draft. THIS PLAN NARROWED: E-03 and E-04 removed with their V-items, old E-05 renumbered to E-03 and scoped to this plan's test surface only, `Highest E allocated` 05 -> 03, and `run_recovery.py` plus `tests/test_run_recovery_cli.py` dropped from Scope-Paths and from the fence. NO E-item content was rewritten and no finding was deleted: E-01/E-02 are untouched, and F5/OQ-03 (the retry default) stay as the historical record of a decision Order 3 inherits. THE OPEN QUESTION THE SPLIT HAD TO ANSWER - who owns the shared test-module edits - is answered BY FILE rather than by rule: this plan and Order 2 own `tests/test_run_evidence_completion.py`, Order 3 owns `tests/test_run_recovery_cli.py`, so no two children edit the same test file except this plan and Order 2, which must not run concurrently (recorded in both fences). No `Item-Dependencies` edges were added between the three: the parent's E-01 and E-04 both declared `Depends on: none`, so inventing an order would be a false constraint. TWO THINGS FOUND WHILE AUTHORING THE CHILDREN, neither in the parent: (1) `--unverifiable-ok`'s PRECONDITION (`--allow-unverifiable` and the interactive `run unverifiable` confirmation) is ALSO unbuilt, greping to zero, so Order 2 consumes the admission as a parameter rather than inventing a CLI surface; (2) there is NO `--retry-budget` CLI flag either, so Order 3's "validate at entry" correctly means the two helpers' `limit` parameter. `aw ipd lint --phase author` conforming on all three.
- 2026-09-01 reviewed (aw set): REVERTING MY OWN APPROVAL of a few hours ago. Review round 2 (PR-004/F10) found this plan bundles THREE independent concerns and must be SPLIT before execution: E-01/E-02 the 13 RUN-* codes in run_evidence.py, E-03 --unverifiable-ok semantics, E-04 a one-line retry-budget bounds check in a DIFFERENT module, with E-01 and E-04 both declaring Depends on: none. Round 1 treated a passing count-based size lint as clearing right-sizing, which the plan-review workflow explicitly forbids. Approved is the EXECUTABLE state, so leaving it approved would let a runner pick up a plan whose own fence now says stop. Returning to reviewed until it is split.
- 2026-08-31 approved (aw set, --by-human): Maintainer approved 2026-08-31 in session, after plan-review round 1 (m73aet APPROVE 0 findings; 6lu3rq and wlxkoz APPROVE WITH REVISIONS APPLIED, all findings FIXED in place, zero unresolved, no open questions).
- 2026-08-31 reviewed (aw set): plan-review round 1 complete; revisions applied. See .aw/records/reviews/ for the typed findings and decisions.
- 2026-08-31 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 (3 findings, all fixed). Verified at HEAD 381dbd5c: spec 25kzda 4.2 really defines exactly 13 RUN-* codes (enumerated and counted), all 13 plus unverifiable_ok/unverifiable-ok really are ZERO-hit, and DEFAULT_RETRY_LIMIT really is 2 so E-04's do-not-re-litigate instruction is current. PR-001 (MED): BOTH of this plan's test files are also in the Scope-Paths of APPROVED 0soncw, which the plan cites twice but only about the verb rename, never noticing the shared files; fixed with a coordination requirement (re-measure before editing, STOP if 0soncw landed changes) plus F8, since additive-only is a mitigation not immunity when 0soncw is rewriting the invoked command strings existing assertions contain. PR-002 (LOW): E-01 required a DATA table while citing the EV-* codes as the convention to follow, but those are docstring prose (:540-545) plus inline literals in conditionals (:561..:650), i.e. exactly what E-01 forbids; fixed by stating the data requirement wins and this plan INTRODUCES the convention. PR-003 (LOW): two citations had drifted ~15 lines (retry_budget_remaining :355 not :340, DEFAULT_RETRY_LIMIT :62 not :47); corrected. Also recorded the m73aet-before-wlxkoz ordering, deliberately NOT as a hard executed: edge since the two trailer-dependent codes are UNBOUND here by design. Two reversible decisions recorded (D-1, D-2). Review artifact: .aw/records/reviews/20260831-runcodes-01-wlxkoz-the-deterministic-run-finding-code-vocabulary.review.md
- 2026-08-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): SUPERSEDES `7f7782` (detrun-05), inheriting ONLY the residue its own second review left standing, and inheriting its `- Blocks-Release: next` gate so retiring `7f7782` does not silently drop it. `7f7782` was `REJECT - NEEDS REPLAN` twice, and its second pass REMOVED its last remaining substantive item: the fresh-verifier harness it wanted to build ships twice over (`agy_verifier.run_fresh_verifier:142` as an enforced contract, and a live runner turn at `oc_runipd.py:1663`/`:2281`), while its ledger, inspection CLI, completion checker, and resume all ship as `run_ledger_store.py`, `run_cli.py`, `run_evidence.py`, and `run_recovery.py`. This plan also DISCHARGES that plan's blocking OQ-03, which asked for the per-check mapping of the 13 codes onto existing predicates BEFORE any were written: the mapping is measured and recorded in this plan's Findings table.
- 2026-08-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give the deterministic checker the stable finding codes, exact messages, and recovery commands the spec specifies, as a thin named layer over the checking logic that already ships, so operators get actionable text and no second completion authority is created.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the code vocabulary, mapped rather than invented

- [ ] E-01 Add the 13 `RUN-*` codes to `run_evidence.py` as a DATA table (code, message template, recovery command, failure action), transcribing the message and action text VERBATIM from spec `25kzda` 4.2. Do not compose your own wording: each row of the spec's table fixes the exact operator-facing string and the failure action (`ABORT RUN`, `FAIL ITEM`, `RETRY`, `SKIP ITEM`, `SKIP DEPENDENCY-NOT-MET`, `NEEDS INPUT`), and the action semantics are load-bearing because `ABORT RUN` is an EXHAUSTIVE six-class set per spec 4.1 and no other finding may abort the queue. Keep it data, not branching logic, so the whole policy is readable in one place. MEASURED: all 13 codes grep to ZERO in the package. CORRECTED AT REVIEW (PR-002): an earlier draft told you to "follow that module's existing convention" for the parallel `EV-*` codes, which CONTRADICTS the data requirement above. There is NO `EV-*` data table: those codes are docstring prose (`run_evidence.py:540-545`) plus bare string literals inside branching logic (`:561`, `:575`, `:589`, `:602`, `:614`, `:624`, `:637`, `:650`), i.e. exactly the shape this item forbids. THE DATA REQUIREMENT WINS: build the table `EV-*` should have had, deliberately introducing the convention rather than copying the existing one. Do NOT refactor the shipped `EV-*` codes into it (out of scope); just do not cite them as the model.
  - Depends on: none
  - Expected outcome: all 13 codes exist as data with the spec's verbatim message templates, recovery commands, and failure actions; the table is a single readable structure; a test can enumerate it and compare against the spec; nothing about the shipped `EV-*` codes changes.
  - Execution state: pending

- [ ] E-02 Bind each `RUN-*` code to the SHIPPED predicate that already decides it, and mark explicitly the ones whose machinery does not exist yet. This discharges the retired plan's blocking OQ-03, which required exactly this mapping before any code was written; the measured mapping is in this plan's Findings table (F3) and MUST be re-verified rather than trusted, because HEAD moves hourly here. The three states each code can be in: BOUND (a shipped predicate decides it, so the code is a name over existing logic); UNBOUND-BY-DEPENDENCY (the predicate needs machinery another plan owns, for example the commit trailers of `runtrail-01` (`m73aet`) or the host capability contract of `hostcap-01` (`mjx7ne`)); and UNBOUND-UNBUILT (nothing decides it yet). Record the state per code IN THE TABLE. Do NOT implement a missing predicate here: an unbound code that honestly reports itself unbound is safe, whereas a code silently wired to a predicate that does not answer its question is a fail-OPEN checker.
  - Depends on: E-01
  - Expected outcome: every one of the 13 codes carries its state and, when BOUND, the shipped predicate it delegates to; no code is bound to a predicate that does not answer its question; the UNBOUND ones name the plan or the missing machinery they wait on; a reader can see at a glance how much of the checker actually decides anything.
  - Execution state: pending

- [ ] E-03 Extend the SHIPPED `tests/test_run_evidence_completion.py` rather than creating a new one. The retired plan proposed `tests/test_deterministic_checker.py`, which its review rejected because this module plus `tests/test_run_viewer.py` already cover these surfaces. NARROWED BY THE SPLIT (2026-09-04): this item no longer touches `tests/test_run_recovery_cli.py`, which now belongs to Order 3 (`sq61qd`), and it no longer covers `--unverifiable-ok` (Order 2, `zub5f1`) or the retry boundaries (Order 3). Cases MUST include: the 13 codes enumerated and each message asserted against the SPEC TEXT (so rewording fails the test); and every code's recorded state matching a live re-measurement (so the mapping cannot silently rot). Do NOT weaken, remove, or alter any existing assertion.
  - Depends on: E-01, E-02
  - Expected outcome: all cases pass; the message assertions fail if any message is reworded; the mapping test fails if a code's state stops matching reality; existing assertions in the shipped file pass unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE COMPLETION AUTHORITY ALREADY EXISTS AND MUST STAY SINGLE. `run_evidence.py` (1099 lines) holds `validate_evidence`, `validate_ledger_evidence`, `evaluate_completion`, and `is_complete`, with a documented 13-class false-completion taxonomy under `EV-*` codes. Its review said it best: building a second completion checker in the one component whose entire value is being the single trustworthy one means two disagreeing checkers, so neither can authorize completion. This plan adds NAMES over it, never a rival.
- THE SHIPPED TAXONOMY IS THE PRECEDENT TO FOLLOW. The `EV-*` codes (`EV-MISSING-OUTPUT`, `EV-FABRICATED-TEXT`, `EV-STALE-HEAD`, `EV-WRONG-CWD`, `EV-WRONG-WORKTREE`, `EV-COMMAND-MISMATCH`, `EV-EXPIRED-PROBE`, `EV-TRUNCATED-OUTPUT`, `EV-FAILED-EXIT`, `EV-ABSENT-ARTIFACT`, `EV-HASH-MISMATCH`, `EV-EXECUTOR-VERIFIER`, `EV-REDACTION-CONFLICT`) are exactly the shape this plan's table should take. Reuse the convention.
- THE LEDGER IS HASH-CHAINED AND SELF-VERIFYING. `run_ledger_store.verify_chain` (`:529`) plus `BrokenChainError` (`:71`) already decide ledger integrity, which is what `RUN-LEDGER-INTEGRITY` names. The retired plan proposed `run_ledger.py` beside `run_ledger_store.py`, at the same on-disk path; the module itself already warns against confusing its store with the drivers' `events.jsonl`.
- THE FRESH VERIFIER SHIPS TWICE. As an enforced contract (`agy_verifier.run_fresh_verifier:142`, `assert_distinct_sessions:131`, over `verify_roles.py`) and as a live runner turn (`oc_runipd.build_verifier_prompt:1663`, launched `:2281` with `fresh_session=True`). The retired plan judged this "not obviously shipped" partly from line count; its second pass corrected that, noting the module is small because it consumes a 2158-line `verify_roles.py`. LINE COUNT IS NOT AN INVENTORY.
- TERMINAL AUTHORITY IS RESERVED. `verify_roles` reserves terminal authority to the coordinator and `aw ipd finalize` owns the transition. No new checker may claim it "alone authorizes terminal transitions".
- THE VERB GROUP IS BEING RENAMED BY SOMEONE ELSE. Approved `runnamecollapse-01` (`0soncw`) owns collapsing run inspection under `aw runs` and retiring `aw run`. Do not touch that surface; note that spec 4.2's recovery commands say `aw runs show|verify`, which is where that rename lands, so transcribing the spec verbatim is consistent with it.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `agent_workflows/` (absence) | All 13 `RUN-*` codes are absent, so the checker has no stable public vocabulary and no operator-facing recovery text. This is the real, narrow gap the retired Set was circling. | each of the 13 codes greps to 0 files under `agent_workflows/` at HEAD `738980ec` |
| F2 | HIGH | retired `7f7782` E-01 | Its last surviving item was removed by its own second review after the inventory it had DEFERRED was finally done: the fresh-verifier harness ships twice. The lesson is recorded because it is the failure mode of this whole Set: deferring an inventory is how a duplicate survives a review. | `agy_verifier.run_fresh_verifier:142`; `oc_runipd.py:1663`, `:2281`; `7f7782`'s pass-2 gate text |
| F3 | HIGH | spec 4.2 vs shipped code | THE MAPPING (discharging the retired plan's blocking OQ-03, measured; re-verify before use). BOUND to shipped predicates: `RUN-LEDGER-INTEGRITY` (`run_ledger_store.verify_chain:529`, `BrokenChainError:71`); `RUN-HOST-ATTEMPT` (`run_evidence` `EV-FAILED-EXIT`/`EV-MISSING-OUTPUT`/`EV-COMMAND-MISMATCH` plus `capture_command:435`); `RUN-FRESH-VERIFIER` (`EV-EXECUTOR-VERIFIER` plus `agy_verifier.assert_distinct_sessions:131`); `RUN-CHECK-FRESHNESS` (`EV-STALE-HEAD`, `EV-WRONG-CWD`, `EV-WRONG-WORKTREE`, `EV-TRUNCATED-OUTPUT`); `RUN-FROZEN-IDENTITY` (`run_freeze` `FrozenItem:37`, `refuse_drop_or_redefine:245`, `EV-HASH-MISMATCH`); `RUN-STRUCTURE-PREFLIGHT` (`ipd_lint` phases plus `aw check`); `RUN-CROSS-TREE` (`check_engine` rules via `aw check all`); `RUN-SCOPE-DELTA` (`ipd_lifecycle._frozen_scope_paths:316`, `_reconcile_scope:1275`). UNBOUND-BY-DEPENDENCY: `RUN-COMMIT-CONTENTS` and `RUN-COMMIT-GATEWAY` need the `AW-Run:`/`AW-Item:` trailers (`runtrail-01`, `m73aet`, unbuilt); `RUN-HOST-CAPABILITY` needs the capability contract (`hostcap-01`, `mjx7ne`, approved, unexecuted). UNBOUND-UNBUILT: `RUN-BASELINE-OWNERSHIP` (needs the path-lease overlap check) and `RUN-NO-PUSH` (needs host push-denial ENFORCEMENT, the same unbuilt security boundary `hostcap-01`'s OQ-03 escalated). | each predicate read at HEAD; the `EV-*` table in `run_evidence.py`; `run_freeze.py`; `ipd_lifecycle.py` |
| F4 | HIGH | spec 4.1 | `ABORT RUN` is an EXHAUSTIVE six-class set and "no other finding may abort the whole queue". So the failure ACTION is as much a part of each code as its message, and transcribing the message while inventing the action would silently license aborting a queue on an item-local fault. That distinction is what makes independent items able to continue. | spec 4.1 abort table and its closing rule |
| F5 | MED | spec 2.1 vs `run_recovery.py` | THE SPEC AND THE CODE DISAGREED on the default retry budget: spec 2.1 says 2, the code said 3. RESOLVED 2026-08-31 by maintainer decision in favour of the spec, and applied, because the value was verifiably DORMANT (zero production callers) so the change was free; deferring it until the runner consumes this layer would have made the same edit a costly behavior change. | spec 2.1 `--retry-budget` bullet; `DEFAULT_RETRY_LIMIT` now `2`; `rg 'plan_retry\|retry_budget_remaining' agent_workflows/` returns only `run_recovery.py` itself |
| F6 | MED | spec 2.1, 4.10 | `--unverifiable-ok` is doubly constrained: it may change ONLY the aggregate exit, never an item's outcome or verification label, and it is legal ONLY after `--allow-unverifiable` or the interactive confirmation. A flag that quietly relabeled an item, or that worked standalone, would be a fail-OPEN reading of the same words. | spec 2.1 bullet; 4.10 `PROMPT-UNVERIFIABLE` row |
| F7 | LOW | retired `7f7782` proposed modules | Its `run_verifier.py`, `run_ledger.py`, and `deterministic_checker.py` would each have forked a shipped module, and `run_ledger.py` would have collided at the same on-disk path as `run_ledger_store.py`. Recorded so a successor does not resurrect them. | `7f7782`'s pass-2 prohibitions; `run_ledger_store.py:373` warning about path confusion |
| F8 | MED | approved `0soncw` vs this plan's Scope-Paths | FOUND AT REVIEW (PR-001). BOTH of this plan's test files are ALSO in the Scope-Paths of APPROVED `runnamecollapse-01` (`0soncw`): `tests/test_run_evidence_completion.py` and `tests/test_run_recovery_cli.py`. This plan cites `0soncw` twice but only about the `aw run` verb rename, and never noticed the shared files. `0soncw` is retiring `aw run` and collapsing inspection under `aw runs`, so its edits to these files are likely to rewrite invoked command strings, which can collide textually with added cases. Partially mitigated by this plan's own additive-only fence, which is why it is MED not HIGH. The remedy is coordination, not a scope change: re-measure both files immediately before editing and STOP if `0soncw` has landed changes to them. | computed by intersecting Scope-Paths across all pending plans; `0soncw`'s Scope-Paths entries 6 and 7 |
| F9 | LOW | `run_evidence.py` | FOUND AT REVIEW (PR-002). E-01 originally cited the shipped `EV-*` codes as the convention to follow WHILE requiring a data table. There is no `EV-*` data table: the codes are docstring prose (`:540-545`) plus inline literals in conditionals (`:561`, `:575`, `:589`, `:602`, `:614`, `:624`, `:637`, `:650`). Following the cited precedent would produce exactly what the item forbids. Resolved in E-01 by stating the data requirement wins and that this plan deliberately INTRODUCES the convention rather than copying it. | the cited lines, read directly |
| F10 | MED | this plan's own decomposition | **RESOLVED 2026-09-04 BY PERFORMING THE SPLIT** (Order 2 `zub5f1`, Order 3 `sq61qd`); the finding text is kept as the record of why. FOUND AT REVIEW ROUND 2 (PR-004, right-sizing): this plan BUNDLED THREE INDEPENDENT CONCERNS and had to be SPLIT before execution. E-01/E-02 are the 13 `RUN-*` code vocabulary and their bindings (`run_evidence.py`); E-03 is `--unverifiable-ok` aggregate and exit-code semantics (flag behavior); E-04 is a retry-budget 0..10 bounds check in a DIFFERENT module (`run_recovery.py`). E-01 and E-04 BOTH declare `Depends on: none`, so they were never sequentially related; E-04 is a one-line range check that merely shares a file list with a 13-code verbatim transcription task. WHY THE STRUCTURAL LINT MISSED IT: 5 E-items is the same COUNT as the sibling `6lu3rq`, and count is not density. The plan-review workflow states this explicitly: "A passing count-based size lint does NOT clear right-sizing; conceptual density must be evaluated in semantic review." Round 1 checked the lint and did not do that evaluation. WHY IT MATTERS PRACTICALLY: integration is ALL-OR-NOTHING per plan. If an executor fumbles the 13 verbatim transcriptions, the whole plan strands on its lane and the trivially safe bounds check strands with it. OPEN QUESTION FOR THE SPLIT: E-05's tests span all three concerns and touch the SAME two shipped test modules, so a split must decide whether each child carries its own additions to those files (which reintroduces the `0soncw` coordination question per child) or whether one child owns the test file edits for all. | this plan's E-item list read against its Scope-Paths; the `Depends on: none` on both E-01 and E-04; plan-review workflow Step 1 structural-preflight note |

## Proposed changes (ordered, validatable)

1. Transcribe the 13 codes, messages, recovery commands, and failure actions as data (E-01).
2. Bind each to the shipped predicate that decides it, or mark it honestly unbound (E-02).
3. Extend the shipped test module with spec-anchored, non-vacuous cases (E-03).

MOVED OUT BY THE 2026-09-04 SPLIT: `--unverifiable-ok` aggregate neutrality is Order 2 (`zub5f1`) and the retry-budget 0..10 range is Order 3 (`sq61qd`).

## Deferred / out of scope (with reason)

- WIRING THE CODES INTO `oc_runipd.py` / `agy_runipd.py`. Deferred so this plan touches neither runner, removing the `rununify` (`5e4sb6`) sequencing conflict rather than answering it. Same move that unblocked `hostcap-01` (`mjx7ne`). Consequence stated in the Scope check.
- IMPLEMENTING THE UNBOUND PREDICATES. `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` wait on the trailers (`runtrail-01`, `m73aet`); `RUN-HOST-CAPABILITY` waits on `hostcap-01` (`mjx7ne`); `RUN-BASELINE-OWNERSHIP` and `RUN-NO-PUSH` need machinery nobody has built. Naming them unbound is the deliverable; building them is not.
- ANY NEW CHECKER MODULE (`run_verifier.py`, `run_ledger.py`, `deterministic_checker.py`). Explicitly rejected (F7).
- RENAMING THE `aw run` VERB GROUP. Owned by approved `runnamecollapse-01` (`0soncw`). NOTE THE SHARED FILES (added at review, F8): `0soncw` also claims BOTH of this plan's test files, so coordinate rather than merging blind; the scope fence states the required re-measurement.
- LANDING BEFORE `runtrail-01` (`m73aet`) IS A REQUIREMENT, recorded at review. Four of the 13 codes depend on the commit trailers, and `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` are recorded UNBOUND-BY-DEPENDENCY here for exactly that reason. Deliberately NOT expressed as an `- Item-Dependencies: executed:m73aet` edge, because those two codes are unbound BY DESIGN in this plan, so this plan is genuinely runnable before `m73aet` lands; the ordering constrains the FOLLOW-UP that BINDS them, not this plan. If a future plan binds those codes, it MUST carry the hard edge.
- CHANGING THE SHIPPED RETRY DEFAULT. Reported, not changed (F5).
- CLAIMING TERMINAL AUTHORITY. `verify_roles` reserves it to the coordinator and `aw ipd finalize` owns the transition.

## Scope check

- Over-scope: none. Two shipped modules gain an additive data table and two small validations; two shipped test modules gain cases. No new module, which is the point.
- Under-scope, DELIBERATE and stated plainly: when this plan completes, no live run emits any of these codes, because the runner wiring is deferred. The vocabulary lands tested and importable and nothing consults it yet.
- Under-scope, HONEST AND CENTRAL: FOUR of the 13 codes will exist as NAMES with no predicate behind them (F3: two waiting on sibling plans, two on unbuilt machinery). That is deliberate and is why E-02 records state per code. A named-but-unbound code is safe when it says so; the danger this plan exists to avoid is a code silently bound to a predicate that does not answer its question, which is a checker that passes because nothing was checked.
- CONTENTION: `run_evidence.py` and `run_recovery.py` are shared modules, and `cli.py`/`run_cli.py`/both runners are claimed by approved `runnamecollapse-01` and `rununify`. This plan touches none of the latter. Re-read the two modules immediately before editing and verify the staged set before every commit.

## Required tests / validation

- The two SHIPPED test modules must pass with every case in E-05, and every PRE-EXISTING assertion must pass unchanged.
- ANCHOR ASSERTIONS TO THE SPEC (HARD): each message must be asserted against spec 4.2's text such that REWORDING fails the test. An assertion written from the implementation cannot detect a transcription error, which is the only defect this plan can realistically ship.
- THE MAPPING MUST BE RE-MEASURED, NOT TRUSTED: F3 was measured at a HEAD that has since moved. Re-verify each binding and paste the evidence; if a binding changed, correct the table rather than the measurement.
- FALSIFIABILITY: the message assertions must be shown FAILING when a message is reworded (V-03's sabotage), since a transcription error is the only defect this plan can realistically ship. (The `--unverifiable-ok` label-invariance and retry-boundary falsifiability requirements moved with their items to Orders 2 and 3.)
- INVOKE THE SUITE BARE: `python3 -m pytest`. `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
- VALIDATE IN THE PRIMARY CHECKOUT, NOT A SCRATCH WORKTREE: `tests/test_run_viewer.py` fails about 15 tests in a detached worktree that PASS in the primary tree, because state resolves relative to the worktree (backlog `dh0uno`). A run validated only in a scratch tree shows phantom failures.
- BASELINE IS A MEASUREMENT: take before/after counts yourself with the `git rev-parse HEAD` they were measured at.
- `aw check plans` is RED on pre-existing findings owned by other Sets (measured 901 at HEAD `7e5ba287`). Do NOT claim it passes; the bar is NO-WORSENING against your own fresh baseline.
- `aw sanitize --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- This plan implements the code-vocabulary half of spec `25kzda` 4.2. It does not change the spec text. The `--unverifiable-ok` rule of 2.1/4.10 is implemented by Order 2 (`zub5f1`) and the retry-budget range of 2.1 by Order 3 (`sq61qd`), so the Set as a whole still covers all three.
- RECORD THE PER-CODE STATE where a successor will find it, since three sibling plans (`runmixed-01` `6lu3rq` for `RUN-MIXED-TYPES`, `runtrail-01` `m73aet` for the commit codes, `hostcap-01` `mjx7ne` for `RUN-HOST-CAPABILITY`) each own one code's machinery. Without one shared record, each plan re-derives which codes exist and at least one gets it wrong.
- REPORT the spec-versus-code retry default discrepancy (F5) so the maintainer can decide which is authoritative; do not resolve it by editing either side.

## Open questions

### OQ-01: Must the code wiring wait for `rununify`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE QUESTION IS DISSOLVED, not answered, which is what lets this plan proceed now. The retired `7f7782` carried it as a BLOCKING maintainer question (its OQ-02) because its items added code to both runner modules, increasing the duplication `rununify` (`5e4sb6`) exists to remove. This plan defers the runner wiring entirely and touches neither runner, so the conflict cannot arise. The precedent is `hostcap-01` (`mjx7ne`), which dissolved the identical question the identical way at the maintainer's direction. The honest cost is in the Scope check: no live run emits these codes until a follow-up wires them.

### OQ-02: Which of the 13 codes have shipped predicates behind them?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY MEASUREMENT, and this discharges the retired plan's blocking OQ-03, which demanded exactly this mapping before any code was written. The full per-code result is Finding F3: nine BOUND to shipped predicates, two UNBOUND-BY-DEPENDENCY on sibling plans (`runtrail-01` `m73aet` for the commit trailers, `hostcap-01` `mjx7ne` for the capability contract), and two UNBOUND-UNBUILT (`RUN-BASELINE-OWNERSHIP` needs a path-lease overlap check; `RUN-NO-PUSH` needs host push-denial enforcement, the same unbuilt security boundary `hostcap-01`'s own OQ-03 escalated to the maintainer). The retired plan called this unanswerable inside a review without authoring the successor, which was correct: it is answered HERE, in the successor, as a plan finding rather than as a review verdict. E-02 requires re-verifying it rather than trusting it, because HEAD moves hourly in this repo.

### OQ-03: Is the shipped retry default (3) or the spec's (2) authoritative?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER (2026-08-31): the SPEC's 2 is
  authoritative, and the code was aligned to it in the same session rather than left as a documented
  discrepancy. MEASURED before changing it: `plan_retry`, `retry_budget_remaining` and
  `correction_required` have ZERO production callers in the package (only tests exercise them), so the
  value was DORMANT and the change cost two test edits and no behavior change. That is precisely why it
  was done NOW: once the runner wires this layer up, the same one-character edit becomes a real
  behavior change that alters how many paid model turns every failed step buys. Rationale on the
  merits, not just deference to the spec: a retry here is a CORRECTION attempt, not a network-flake
  retry, and `plan_retry`'s own contract is that "a retry cannot turn failure into success by mere
  repetition"; a corrector still failing after two passes is usually facing a plan defect rather than a
  transient fault, so a third attempt mostly buys another paid turn and delays escalation. Applied in
  `agent_workflows/run_recovery.py` (`DEFAULT_RETRY_LIMIT: int = 2`, with the reasoning recorded in a
  comment beside it). The two tests that pinned the old value now DERIVE their expectations from the
  constant, so this cannot silently drift again. E-04's remaining job is unchanged and is only the
  0..10 RANGE check, which is independent of the default.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the 13-row table. Paste a diff or side-by-side of each message against spec 4.2's corresponding row, proving VERBATIM transcription including the recovery command. Paste each row's failure action beside the spec's action column, and paste evidence that no code outside spec 4.1's six abort classes is marked `ABORT RUN` (F4). Paste evidence the shipped `EV-*` codes are unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the per-code state (BOUND / UNBOUND-BY-DEPENDENCY / UNBOUND-UNBUILT) with, for each BOUND code, the shipped predicate and a live demonstration that the predicate actually decides that code's question. Paste your OWN re-measurement of F3's mapping at the HEAD you worked at, and state explicitly any binding that changed since F3 was recorded. Paste evidence no code is bound to a predicate that does not answer its question.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both shipped test modules passing with counts, and the BARE `python3 -m pytest` summary line with the `git rev-parse HEAD` it was measured at plus your own before-baseline at that HEAD, measured in the PRIMARY checkout (not a scratch worktree; see Required tests). Paste `git diff` of both test files proving no existing assertion was weakened, removed, or altered. Paste proof the new tests are NOT VACUOUS: reword one message in the implementation and show the assertion FAILING. Paste the no-worsening comparison for `aw check plans` (both counts measured, not remembered).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 3 E-leaves in one task group, under the thresholds. One concern throughout, and now genuinely one after the 2026-09-04 split: give the checker the spec's stable code vocabulary over predicates that already ship. The two concerns that made round 2 call this plan bundled (`--unverifiable-ok`, the retry range) are now Orders 2 and 3.

Open questions: NONE is blocking. OQ-01 is DISSOLVED by deferring the runner wiring (the `hostcap-01` precedent). OQ-02 is RESOLVED by measurement and discharges the retired plan's blocking OQ-03; E-02 requires re-verifying it rather than trusting it. OQ-03 is DEFERRED to the maintainer and is non-blocking because this plan implements only the unambiguous 0..10 range and changes no default.

SPLIT PERFORMED 2026-09-04, so the earlier DO-NOT-EXECUTE-AS-IS block is DISCHARGED and removed.
Review round 2 (PR-004/F10) found this plan bundled three independent concerns; at the maintainer's
direction it was split into three children of the SAME Set, keeping this plan's id6 and Order:
Order 1 `wlxkoz` (this plan) keeps the 13 `RUN-*` codes and their bindings; Order 2 `zub5f1` takes
`--unverifiable-ok` aggregate neutrality; Order 3 `sq61qd` takes the retry-budget 0..10 range. The
three are independent (the parent's E-01 and E-04 both declared `Depends on: none`), carry NO
`Item-Dependencies` edges between them, and may execute in any order or in parallel.
THE TEST-OWNERSHIP QUESTION THE SPLIT HAD TO SETTLE is settled by file: this plan and Order 2 own
`tests/test_run_evidence_completion.py`, Order 3 owns `tests/test_run_recovery_cli.py`. Since this
plan and Order 2 share that file AND `run_evidence.py`, do NOT execute the two concurrently.

Scope fence: touch ONLY `agent_workflows/run_evidence.py` and `tests/test_run_evidence_completion.py` (test file: additive cases only; no existing assertion weakened, removed, or altered). NARROWED BY THE SPLIT (2026-09-04): do NOT touch `agent_workflows/run_recovery.py` or `tests/test_run_recovery_cli.py`, which now belong to Order 3 (`sq61qd`), and do NOT implement `--unverifiable-ok`, which belongs to Order 2 (`zub5f1`). COORDINATION REQUIREMENT added at review (F8/PR-001): APPROVED `0soncw` claims BOTH of those test files in its own Scope-Paths and is rewriting the `aw run` command surface they invoke. Before editing either file, re-measure it against `0soncw`'s current state (`git log --oneline -- <file>` plus a read of the invoked command strings); if `0soncw` has landed changes there, STOP and report rather than merging blind. Additive-only is a mitigation, not immunity: a renamed verb inside an existing assertion is still a textual collision. Do NOT create `run_verifier.py`, `run_ledger.py`, `deterministic_checker.py`, or `tests/test_deterministic_checker.py`. Do NOT edit `run_ledger_store.py`, `agy_verifier.py`, `verify_roles.py`, `run_cli.py`, `cli.py`, `oc_runipd.py`, or `agy_runipd.py`. Do NOT implement any UNBOUND predicate (F3). Do NOT claim any checker "alone authorizes terminal transitions". Do NOT rename the `aw run` verb group (owned by `0soncw`). Do NOT change `DEFAULT_RETRY_LIMIT` (OQ-03; Order 3 owns that module anyway). Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or this orchestrator, and do NOT reimplement a rule another plan owns.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at, measured in the PRIMARY checkout. Do NOT claim `aw check plans` passes; it is RED on 901 pre-existing findings owned by other Sets (measured at HEAD `7e5ba287`), and the bar is no-worsening against your own fresh baseline. Do NOT describe the checker as complete or as making runs verifiable: FOUR of the 13 codes land as names with no predicate behind them, and no live run emits any of them until a follow-up wires the runners. State both plainly in the terminal history.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never `-a`, and never push. Several sessions commit to this checkout CONCURRENTLY: run `git diff --cached --name-only` before every commit and unstage anything you did not modify, with `git restore --staged <path>`. A pre-commit hook failure INVALIDATES that check, so re-run it after any failed commit attempt before retrying. Prefer `aw commit <plan> -- <paths>`, which is immune to index pollution by construction.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
