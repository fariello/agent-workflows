# IPD: unverifiable-ok aggregate neutrality within its two spec constraints

- Date: 2026-09-03
- Kind: child
- Concern: Spec `25kzda` 2.1 and 4.10 specify `--unverifiable-ok`, a flag that makes an unverifiable item NEUTRAL in the aggregate exit code while leaving the item's own outcome and verification label untouched. It does not exist: `unverifiable_ok` and `unverifiable-ok` both grep to ZERO hits in `agent_workflows/`. The flag is DOUBLY CONSTRAINED and both constraints are the point - it may change ONLY the aggregate, never an item's outcome or label (4.10's `PROMPT-UNVERIFIABLE` row), and it is LEGAL ONLY after contractless prompts were admitted by `--allow-unverifiable` or the interactive `run unverifiable` confirmation. A flag that quietly relabeled an item, or that worked standalone, would be a fail-OPEN reading of the same words.
- Scope: Implement the aggregation predicate PURELY (testable with no live run) so an unverifiable item contributes 1 to the aggregate exit by default and 0 under the flag, prove the item's outcome and verification label are byte-identical either way, and refuse the flag when its precondition is absent. Excludes the 13 `RUN-*` codes (Order 1, `wlxkoz`), excludes the retry-budget range (Order 3, `sq61qd`), excludes BUILDING `--allow-unverifiable` or the interactive confirmation (both unbuilt; see F-3 and OQ-01), and excludes wiring anything into either runner module.
- Scope-Paths: agent_workflows/run_evidence.py, tests/test_run_evidence_completion.py
- Item-Dependencies: none
- Status: to-review
- Set: runcodes
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: zub5f1
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history

- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): SPLIT OUT OF `wlxkoz` (Order 1) at the maintainer's direction, discharging that plan's F10 / review-round-2 PR-004 (three independent concerns bundled; must be split before execution). This child carries the parent's E-03. MEASURED AT AUTHORING rather than inherited: `unverifiable_ok`/`unverifiable-ok` still grep to ZERO in the package, so the flag is genuinely unbuilt. A FINDING THE PARENT DID NOT RECORD, and it shapes this plan (F-3): the flag's PRECONDITION is also unbuilt - `--allow-unverifiable` and the interactive `run unverifiable` confirmation both grep to zero, surviving only as a prose mention in `run_selection_policy.py:168`. So "refuse when the precondition is absent" cannot be implemented against a real flag today, and E-02 therefore implements the refusal against an explicit PARAMETER rather than inventing a CLI surface this plan does not own. Recorded as non-blocking OQ-01 with a defensible default. The parent's E-05 test-ownership question is settled for this child: it touches ONLY `tests/test_run_evidence_completion.py`, never `tests/test_run_recovery_cli.py` (Order 3's file), so the two children cannot collide over a shared test file.

## Goal

Make an unverifiable item skippable in the AGGREGATE without ever making it look verified, so an operator can finish a run with a known-unverifiable step and still cannot be misled about that step's own result.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the aggregation predicate, and the constraint that makes it safe

- [ ] E-01 Add the aggregation predicate to `agent_workflows/run_evidence.py` as a PURE function: given the per-item outcomes (or the already-computed per-item completion results) and an `unverifiable_ok: bool`, return the aggregate verdict/exit contribution. Pure means NO live run, NO ledger, NO subprocess: it takes data and returns a value, so the whole rule is testable in isolation. Default (`False`): an unverifiable item contributes 1 to the aggregate exit. Under the flag: it contributes 0, i.e. NEUTRAL, not success.
  BE PRECISE ABOUT "NEUTRAL": neutral means the item does not make the aggregate fail; it must NOT mean the item is counted as complete, and it must NOT suppress any OTHER item's contribution. Read the shipped exit-code table (`run_cli.py:35-40`, where 0=success/complete, 1=incomplete/invalid-evidence, 2=invocation error) and make the contribution consistent with it rather than inventing a parallel numbering.
  DO NOT WIRE IT INTO A RUNNER and do not add a CLI flag: this plan lands the predicate and its tests only (the parent deferred runner wiring to dissolve the `rununify` sequencing conflict, and that reasoning is inherited).
  - Depends on: none
  - Expected outcome: a pure predicate in `run_evidence.py`; an unverifiable item contributes 1 by default and 0 under the flag; other items' contributions are unchanged in both cases; no runner and no CLI touched.
  - Execution state: pending

- [ ] E-02 Enforce the PRECONDITION: `unverifiable_ok` is legal ONLY when contractless prompts were explicitly admitted. Passing it alone must be REFUSED, not silently honored, because silently honoring it is the fail-open reading (spec 2.1).
  IMPLEMENT IT AGAINST AN EXPLICIT PARAMETER, NOT A FLAG THAT DOES NOT EXIST. MEASURED (F-3): `--allow-unverifiable` and the interactive `run unverifiable` confirmation are BOTH unbuilt (zero hits; only a prose mention at `run_selection_policy.py:168`). So the predicate takes the admission as an explicit argument (for example `unverifiable_admitted: bool`) and refuses when `unverifiable_ok=True` while admission is `False`. The refusal must state which precondition is missing. When the real flag is built, it binds to this parameter; do NOT invent the CLI surface here.
  - Depends on: E-01
  - Expected outcome: `unverifiable_ok=True` with admission `False` is refused with a message naming the missing precondition; with admission `True` it is honored; the refusal is a typed error or an explicit result, consistent with how `run_evidence.py` already reports refusals rather than a bare assert.
  - Execution state: pending

- [ ] E-03 Extend the SHIPPED `tests/test_run_evidence_completion.py` additively; do NOT create a new module and do NOT weaken, remove, or alter any existing assertion. The load-bearing case is the INVARIANT, so make it explicit: for the SAME unverifiable item, run the aggregation with the flag off and on and assert the item's OWN outcome and verification label are IDENTICAL in both, while only the aggregate differs. A test that checks only the aggregate would pass even if the implementation relabeled the item, which is the exact defect spec 4.10 forbids.
  Also cover: the aggregate differing in BOTH directions (off -> contributes, on -> neutral); the precondition refusal from E-02; a run whose OTHER items fail still failing under the flag (so neutrality is not blanket suppression); and the predicate being exercised with NO live run, which is what E-01's purity buys.
  - Depends on: E-01, E-02
  - Expected outcome: all cases pass; the label-invariance assertion is present and would fail if the item were relabeled; existing assertions in the shipped file pass unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `run_evidence.py` is the SINGLE completion authority (`evaluate_completion:804`, `is_complete:1081`, plus a 13-class `EV-*` false-completion taxonomy). Its own review established that a second completion checker means two disagreeing checkers, so neither can authorize completion. This plan adds an AGGREGATION rule over it, never a rival verdict.
- The exit-code table is already fixed and documented (`run_cli.py:11-14`, `:35`): 0 success/complete, 1 incomplete/invalid evidence, 2 invocation error, 7 not-a-ledger. Any contribution this plan computes must be consistent with it.
- The module reports evidence failures as structured reasons rather than raising for expected conditions (`reasons.append(...)`, e.g. `:991`). Match that for an expected refusal; reserve raising for genuine misuse.
- `redaction_blocks_verification` (`:719-724`) is the existing precedent for "verification could not conclude", which is the same family of condition as unverifiable. Read it before designing a new one.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The flag is entirely unbuilt: `unverifiable_ok` and `unverifiable-ok` both grep to ZERO hits under `agent_workflows/`. Re-measured at authoring, not inherited from the parent. | `rg 'unverifiable' agent_workflows/*.py` returns ONE line, a prose comment at `run_selection_policy.py:168` |
| F-2 | The constraint is what matters, not the flag. Spec 4.10's `PROMPT-UNVERIFIABLE` row and 2.1 together mean the flag may change ONLY the aggregate: an implementation that relabeled the item would satisfy a naive aggregate test while breaking the actual contract. That is why E-03's label-invariance case is the load-bearing one. | spec `25kzda` 2.1 bullet; 4.10 `PROMPT-UNVERIFIABLE` row |
| F-3 | **FOUND AT AUTHORING; the parent did not record it, and it changes E-02's shape.** The flag's PRECONDITION is ALSO unbuilt: `--allow-unverifiable` and the interactive `run unverifiable` confirmation both grep to zero and survive only as prose. So "refuse when the precondition is absent" has no real flag to read. E-02 therefore takes the admission as an explicit PARAMETER rather than inventing a CLI surface this plan does not own. | `rg 'allow.unverifiable\|allow_unverifiable' agent_workflows/` -> only the prose mention at `run_selection_policy.py:168` |
| F-4 | "Neutral" is ambiguous and the ambiguity is dangerous. Neutral must mean "does not make the aggregate fail", NOT "counted as complete" and NOT "suppresses other items". The shipped exit table already distinguishes complete (0) from incomplete (1), so the predicate must not collapse them. | `run_cli.py:11-14`, `:35-40` |
| F-5 | SPLIT PROVENANCE: this is the parent's E-03, which had `Depends on: E-01` only for the table it did not actually need, and which shared a Scope-Paths list with a 13-code transcription task and a retry-budget check in a different module. | parent `wlxkoz` F10 / review round 2 PR-004 |
| F-6 | NO TEST-FILE CONTENTION WITH SIBLINGS. This child touches only `tests/test_run_evidence_completion.py`; Order 3 owns `tests/test_run_recovery_cli.py`. Order 1 also claims this file, so this child and Order 1 must not run concurrently on it. | this plan's Scope-Paths against `wlxkoz`'s and `sq61qd`'s |
| F-7 | CONTENTION TO CHECK, inherited from the parent: APPROVED `0soncw` also claims `tests/test_run_evidence_completion.py` and is rewriting the `aw run` command strings its assertions invoke. Additive-only is a mitigation, not immunity. | parent F8; `0soncw`'s Scope-Paths |

## Proposed changes (ordered, validatable)

1. Add the pure aggregation predicate with default and flagged behavior (E-01).
2. Enforce the precondition against an explicit admission parameter, refusing the standalone flag (E-02).
3. Extend the shipped test module, with label-invariance as the load-bearing case (E-03).

## Deferred / out of scope (with reason)

- BUILDING `--allow-unverifiable` OR the interactive `run unverifiable` confirmation. Both unbuilt (F-3). They are a user-facing admission surface with their own interactive-confirmation design; this plan consumes the admission as a parameter so it binds cleanly when they exist. See OQ-01.
- ADDING THE `--unverifiable-ok` CLI FLAG ITSELF. Same reason: the predicate is the deliverable here, and the CLI surface belongs with the admission flag it depends on.
- THE 13 `RUN-*` CODES: Order 1 (`wlxkoz`).
- THE RETRY-BUDGET RANGE: Order 3 (`sq61qd`).
- WIRING INTO `oc_runipd.py` / `agy_runipd.py`. Inherited from the parent, which deferred runner wiring to dissolve the `rununify` (`5e4sb6`) sequencing conflict rather than answer it.

## Scope check

- Over-scope: none. One shipped module gains a pure predicate; one shipped test module gains cases.
- Under-scope, DELIBERATE and stated plainly: when this plan completes, NO operator can pass `--unverifiable-ok`, because neither it nor its precondition flag exists as a CLI surface. The predicate lands tested and importable and nothing consults it yet. That is the same honest position the parent took about the 13 codes, and it is why the flag work is named in Deferred rather than implied.

## Required tests / validation

- THE LABEL-INVARIANCE CASE IS MANDATORY: same unverifiable item, flag off and on, item outcome and verification label IDENTICAL, only the aggregate different. Without it the suite cannot detect the one defect spec 4.10 forbids.
- The aggregate must be shown differing in BOTH directions, and a run with other failing items must still fail under the flag (neutrality is not blanket suppression).
- The precondition refusal must be shown, naming the missing admission.
- The predicate must be exercised with NO live run, proving E-01's purity.
- Every PRE-EXISTING assertion in `tests/test_run_evidence_completion.py` passes unchanged.
- Full suite BARE (`python3 -m pytest`), compared against YOUR OWN pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (`tests/test_run_viewer.py` shows ~15 phantom failures in a detached worktree; backlog `dh0uno`).
- `aw check plans` NO-WORSENING against your own fresh baseline; do NOT claim it passes.

## Spec / documentation sync

- Implements the `--unverifiable-ok` rule of spec `25kzda` 2.1 and 4.10. No spec text changes.
- Record in the predicate's docstring that the CLI flag and its precondition flag are NOT yet built and that the admission arrives as a parameter, so the next reader does not conclude the feature is user-reachable.

## Open questions

### OQ-01: Should this plan also build `--allow-unverifiable`, or only consume the admission?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT BLOCKING, and the default is to consume only. Spec 2.1 makes `--unverifiable-ok` legal only after contractless prompts were admitted by `--allow-unverifiable` or the interactive `run unverifiable` confirmation, and MEASUREMENT shows neither exists (F-3). Building them here would add an interactive-confirmation surface, which is a different concern with its own UX and its own fail-open risks, and bundling it is precisely what got the parent plan split. So this plan takes the admission as an explicit parameter and the refusal is fully testable today; when the flags are built they bind to that parameter with no rework. If you want the flags in this plan, say so and they become their own E-items with their own confirmation design.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate's signature and body showing it is PURE (no ledger, no subprocess, no run directory). Paste the aggregate for an unverifiable item with the flag OFF (contributes 1) and ON (contributes 0). Paste a case proving neutrality is NOT blanket suppression: a run whose other items fail must still fail under the flag. State how the contribution maps onto the shipped exit table (`run_cli.py:35`) rather than a parallel numbering.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the refusal when `unverifiable_ok=True` and admission is `False`, showing the message names the missing precondition, and the honored case when admission is `True`. Confirm NO CLI flag was added (paste a grep showing `--unverifiable-ok` and `--allow-unverifiable` are still absent from the CLI), since inventing the surface is outside this plan's fence.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the LABEL-INVARIANCE test and its output: the same unverifiable item under flag off and on, with the item's own outcome and verification label shown IDENTICAL in both and only the aggregate differing. Then PROVE IT IS NOT VACUOUS: deliberately make the implementation relabel the item under the flag, paste the assertion FAILING, and revert. An invariance test never observed failing does not establish the invariant, and this is the one defect spec 4.10 forbids. Paste `git diff tests/test_run_evidence_completion.py` proving no existing assertion was altered, plus the bare full-suite summary with its HEAD compared against your own pre-change baseline, measured in the primary checkout.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 3 E-leaves, one task group, one concern: make an unverifiable item neutral in the aggregate without ever making it look verified.

Open questions: OQ-01 (build the admission flags here, or consume only) is non-blocking with a defensible default recorded. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution.

Scope fence: touch ONLY `agent_workflows/run_evidence.py` and `tests/test_run_evidence_completion.py` (test file: additive cases only; no existing assertion weakened, removed, or altered). Do NOT add any CLI flag (`--unverifiable-ok` or `--allow-unverifiable`) and do NOT build the interactive confirmation. Do NOT touch `run_recovery.py` (Order 3 owns it). Do NOT touch either runner module. Do NOT create a new test module or a second completion authority. SIBLING COORDINATION (F-6): Order 1 (`wlxkoz`) also claims `tests/test_run_evidence_completion.py` and `run_evidence.py`, so do not execute this child concurrently with it; re-read both files immediately before editing. COORDINATION, inherited (F-7): APPROVED `0soncw` also claims that test file and is rewriting the command strings its assertions invoke; re-measure it (`git log --oneline -- <file>`) before editing and report rather than merging blind if it has landed changes. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is V-03's SABOTAGE: the label-invariance test must be observed FAILING against a deliberately relabeling implementation, because that is the only defect this plan can realistically ship. Do NOT describe the flag as available to operators: neither it nor its precondition exists as a CLI surface when this plan completes, and the Scope check says so. Do NOT claim `aw check plans` passes; the bar is no-worsening against your own fresh baseline.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Several sessions commit to this checkout CONCURRENTLY: run `git diff --cached --name-only` before every commit and unstage anything you did not modify with `git restore --staged <path>`, and re-run that check after any failed commit attempt, since a hook failure invalidates it. Prefer `aw commit <plan> -- <paths>`.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
