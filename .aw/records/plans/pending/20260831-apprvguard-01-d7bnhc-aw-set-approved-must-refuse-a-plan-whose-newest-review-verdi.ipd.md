# IPD: aw set approved must refuse a plan whose newest review verdict is negative, and refuse unanswered blocking open questions with a named override

- Date: 2026-08-31
- Kind: child
- Concern: `aw set approved` / `aw ipd set approved` has ZERO awareness of a plan's review verdict or its unanswered blocking open questions, so a blanket approval can turn a `REJECT - NEEDS REPLAN` plan into an EXECUTABLE one.
- Scope: Add one shared, typed readiness predicate and consume it from BOTH approval surfaces (`status_set.validate_transition_allowed` and `specs.run_set`), refusing a negative newest verdict with NO override and refusing unanswered blocking open questions with a named override flag recorded in history. Fix the two measured bugs in the existing prose verdict reader rather than forking it. Does NOT touch the runners' launch path, does NOT change any review artifact format, and does NOT add a verdict enum to the typed artifact beyond what the gate reads.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/cli.py, tests/test_plan_readiness.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: to-review
- Set: apprvguard
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: d7bnhc
- From-Backlog: 0zj66l
- Blocks-Release: next

## Workflow history

- 2026-08-31 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `0zj66l`, inheriting its `- Blocks-Release: next` gate. All five of the item's DESIGN QUESTIONS TO RESOLVE are answered from measured repository evidence and recorded as F-1..F-8; the one question that is genuinely the maintainer's (whether a NEGATIVE verdict should also gate `aw specs set approved`, where no review artifact type exists to read) is recorded as non-blocking OQ-02 with a defensible default. Authored review-ready, not draft.
- 2026-08-31 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `approved`, the state that licenses execution, unreachable for a plan whose own newest review said do not build it. Today the approval path reads status alone: on 2026-08-30 a blanket "I APPROVE all the reviewed IPDs" swept five `REJECT - NEEDS REPLAN` plans into `approved`, and only an unrelated pre-execution gate firing for an unrelated reason stopped them from rebuilding shipped subsystems. This plan adds ONE readiness predicate, consumed by every approval surface, that refuses a negative newest verdict outright and refuses unanswered blocking open questions unless a named flag explicitly overrides.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared readiness predicate

- [ ] E-01 Create `agent_workflows/plan_readiness.py` with `extract_newest_history_entry(text: str) -> str | None`, fixing the TWO measured bugs in `oc_runipd.extract_last_history_entry` (`oc_runipd.py:513`) rather than forking it: (a) it slices with `text.rfind("## Workflow history")` to END OF FILE, so it returns the last `- ` bullet of the FINAL section, and (b) it then takes `bullets[-1]`, which is the OLDEST entry because `status_set.py:791` INSERTS new entries directly under the heading. The new function must bound the section at the next `## ` heading and return the FIRST bullet under the heading. Return `None` when there is no history section, so an absent history is distinguishable from an empty one.
  - Depends on: none
  - Expected outcome: for every one of the 26 plans in `.aw/records/plans/pending/`, the returned string starts with `- ` followed by a date and is a real history line; specifically `extract_newest_history_entry` on `bl9q3d` no longer returns the `- Cohesion rationale: ...` line that the shipped function returns today (measured, F-2).
  - Execution state: pending

- [ ] E-02 Add `VERDICTS`, a closed mapping of the four verdict strings documented at `.aw/system/workflows/plan-review/plan-review.md:487-493` onto a polarity, to `plan_readiness.py`: `APPROVE` and `APPROVE WITH REVISIONS APPLIED` are `positive`; `REVIEWED - OPEN QUESTIONS` is `neutral`; `REJECT - NEEDS REPLAN` is `negative`. Also map the separate READINESS vocabulary from `plan-review.md:495-507` (`GO`, `GO - PENDING HUMAN APPROVAL`, `NO-GO`), whose `NO-GO` is `negative`. Do NOT invent `CONDITIONAL-GO`: it is tested for at `oc_runipd.py:536` but appears in NEITHER documented vocabulary (F-4), so keep matching it as negative for backward compatibility and add a comment recording that it is undocumented.
  - Depends on: none
  - Expected outcome: `VERDICTS` is a module-level mapping whose keys are exactly the documented strings; the longest-match ordering is explicit so `APPROVE WITH REVISIONS APPLIED` can never be classified by the `APPROVE` prefix.
  - Execution state: pending

- [ ] E-03 Add `newest_verdict(text: str) -> tuple[str | None, str]` to `plan_readiness.py` returning the classified polarity of the newest REVIEW entry and the raw entry it read. It must consider ONLY history entries that are themselves review entries (the actor or the leading status token names a review, e.g. `reviewed` or `/plan-review`), NOT the newest entry of any kind. THIS IS THE CENTRAL CORRECTNESS REQUIREMENT and it is why a naive "newest entry contains REJECT" test is wrong: measured, all THREE pending plans matching `grep REJECT` are the item-13 successors (`6lu3rq`, `m73aet`, `wlxkoz`) whose newest entry is a `to-review` entry that merely NARRATES the retired predecessor's REJECT (F-5). Classify a verdict only from a review entry's OWN stated verdict.
  - Depends on: E-01, E-02
  - Expected outcome: `newest_verdict` returns `negative` for a plan whose newest review entry states `REJECT - NEEDS REPLAN`, and returns non-negative for all three of `6lu3rq`, `m73aet`, `wlxkoz`, whose REJECT mention belongs to a predecessor.
  - Execution state: pending

- [ ] E-04 Add `approval_refusals(repo_root, plan_path, plan_text, *, allow_open_questions: bool = False) -> list[str]` to `plan_readiness.py` as the ONE predicate every approval surface consumes. It returns a human-readable refusal reason per problem found, empty meaning approval is permitted. It must compose THREE sources rather than reimplementing any: (1) `newest_verdict` from E-03 for the prose verdict; (2) the TYPED artifact via `review_findings.plan_gating_blocks(repo_root, plan_id6)` (`review_findings.py:758`), reused unchanged so the severity comparison is not forked, per the anti-fork precedent test at `tests/test_review_findings_gate.py:261`; (3) blocking open questions via `ipd_lint.parse(text).open_questions` filtered by the EXACT predicate the shipped pre-execution gate uses at `ipd_lint.py:683`, `oq.get("Blocking") == "yes" and oq.get("Status") == "open"`. The verdict refusals are NOT suppressible; only the open-question refusals are suppressed by `allow_open_questions`.
  - Depends on: E-03
  - Expected outcome: `approval_refusals` returns a non-empty list naming the verdict for a REJECTed plan even when `allow_open_questions=True`, returns a list naming `OQ-03` for `mjx7ne` when `allow_open_questions=False` and empty for it when `True`, and returns empty for a plan with no review and no blocking question.
  - Execution state: pending

### Task group 2: consume the predicate at every approval surface

- [ ] E-05 Consume `approval_refusals` in `status_set.validate_transition_allowed` (`status_set.py:449`) with a new `if rec.record_type == "plans" and norm_status == "approved":` block inserted at `status_set.py:502`, immediately after the specs block and before the backlog `blocked` block. Refuse with `return (False, <reason>)`, matching the module's existing refusal shape: the module defines NO exception class and contains no `raise`, and the precedents at `:496` (spec `--by-human`) and `:506` (backlog gate) both return the tuple. Do not invent an exception type. The pre-flight loop at `status_set.py:1217` already makes this atomic across a batch, which is what makes a blanket multi-plan approval refuse WITHOUT partially applying.
  - Depends on: E-04
  - Expected outcome: `aw ipd set approved <rejected-plan>` exits 1 with rule `status.invalid_transition`, the plan file is unmodified on disk, and no `- Approval:` line is written; a batch containing one REJECTed plan approves NONE of its members.
  - Execution state: pending

- [ ] E-06 Add the named override flag `--allow-open-questions` to every CLI surface that reaches the approval path, declared beside the existing `--by-human` at `cli.py:1098` (`aw ipd set`) and `cli.py:2692` (`aw set`), and thread it as `allow_open_questions`. It MUST NOT be implied by `--by-human` (the backlog item is explicit), and the recorded history entry must state that it was used, so an overridden approval is auditable in the artifact rather than only in a shell history. Extend the message composed at `status_set.py:523` for this case.
  - Depends on: E-05
  - Expected outcome: `aw ipd set approved <plan-with-blocking-oq>` refuses; adding `--allow-open-questions` succeeds and the resulting `## Workflow history` entry names the override; `--by-human` alone still refuses.
  - Execution state: pending

- [ ] E-07 Close the SECOND approval surface, `specs.run_set` (`specs.py:498`), which is a forked implementation reached by the `aw specs set <path> --status approved` spelling while the positional spelling routes to `status_set.run_set_command` (dual dispatch documented at `specs.py:632-634`). Consume the SAME predicate there for the open-question half and the same `--allow-open-questions` flag (`cli.py:3419`), so the gate is not bypassable by choosing a spelling. Per OQ-02 the verdict half is a no-op for specs today because `review_findings` keys reviews by `Plan-Id` (`review_findings.py:67`) and no spec review artifact type exists; implement the call so the verdict half activates automatically if one is ever added, and record that in a comment.
  - Depends on: E-06
  - Expected outcome: `aw specs set <spec> --status approved` refuses a spec carrying a blocking open question and accepts it with `--allow-open-questions`; both spellings of spec approval behave identically.
  - Execution state: pending

### Task group 3: falsifiable tests

- [ ] E-08 Add `tests/test_plan_readiness.py` covering the predicate directly, and SABOTAGE each assertion before trusting it (an assertion that cannot fail is worse than no test; this repo has already shipped vacuous isolation tests that passed against a stubbed-out notice). Required cases: the newest-review-entry discriminator (a plan whose newest entry is a `to-review` line NARRATING a predecessor's REJECT must NOT be refused, using the real `6lu3rq` shape); an older REJECT superseded by a newer APPROVE must NOT refuse; a newest REJECT must refuse; the history-ordering fix (newest-first, so a fixture with two review entries proves the newer one wins); the section-bounding fix (a fixture whose final section ends in a `- ` bullet must not have that bullet mistaken for history); `NO-GO` in the readiness vocabulary refuses; blocking-open-question refusal and its override; and the verdict refusal surviving `allow_open_questions=True`.
  - Depends on: E-04
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_plan_readiness.py` reports all tests passing, and each assertion was verified to FAIL when the corresponding predicate branch is deliberately broken.
  - Execution state: pending

- [ ] E-09 Add gate tests to `tests/test_status_set.py` beside the existing approval tests, following the established refusal and atomicity precedents (`test_invalid_status_for_artifact_type_refuses:458`, `test_type_mismatch_refuses_execution_before_changes:390`). Required cases: a REJECTed plan refuses with a nonzero exit and an UNCHANGED file; the refusal is not defeated by `--by-human`; a batch of three plans where one is REJECTed approves NONE; `--allow-open-questions` permits the OQ case and records the override in history; and the `test_custom_message_and_by_human_attestation:471` path (`draft -> approved` with `--by-human`) still returns 0 for a clean plan, proving the gate did not break the legitimate author-then-approve flow.
  - Depends on: E-05, E-06, E-07
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_status_set.py` passes with the new cases, including the unchanged-file assertion on every refusal path.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Refusal in `status_set.py` is `return (False, message)`, never a raise: the module defines no exception class and contains no `raise` statement (only `except` clauses). Precedents at `status_set.py:457`, `:496`, `:506`.
- The pre-flight loop at `status_set.py:1217` validates ALL matched records before any write, so a refusal is atomic across a batch and emits rule id `status.invalid_transition` with exit 1.
- `## Workflow history` is newest-FIRST: `status_set.py:791` uses `new_lines.insert(i + 1, hist_entry)` to prepend under the heading. The comment at `:785` says "Append" and is wrong.
- The one severity comparison is `review_findings.is_gating` (`review_findings.py:694`), and `tests/test_review_findings_gate.py:261` is an explicit anti-fork guard test. Reuse, never reimplement.
- Absent review artifact means SILENT, not blocking (`review_findings.py:768-773`): only 3 `.review.md` files exist against 403 executed plus 26 pending plans, so a fail-closed absent case would block the whole corpus.
- `- Approval:` is written only on reaching `approved` (`status_set.py:700`) and stripped when leaving it (`:688`).

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The approval path has zero verdict awareness, as reported.** `validate_transition_allowed` validates exactly three things: status validity, spec transition legality plus `--by-human`, and the backlog `blocked` gate. Nothing plan-specific exists, and a plan may legally go `draft -> approved` directly. | `status_set.py:454-511` read in full; `tests/test_status_set.py:471` asserts `draft -> approved` returns 0. |
| F-2 | **`extract_last_history_entry` is doubly broken and the existing verdict reader has NEVER fired.** It slices to end of file and then takes `bullets[-1]`, which is the OLDEST entry given newest-first insertion. Measured: `is_plan_review_approved` is `True` for **0 of 26** pending plans, and for `bl9q3d` the "history entry" it returns is `- Cohesion rationale: one architecture (adopt x03wgn)...`. | `oc_runipd.py:513-524`; measured with a loop over `.aw/records/plans/pending/*.ipd.md` calling `is_plan_review_approved` and `extract_last_history_entry`. |
| F-3 | **So `--full-auto` is safe only BY ACCIDENT.** Both call sites check `is_plan_review_approved` first (`oc_runipd.py:2930`, `:5175`), which returns `False` for every plan, so no plan is ever auto-approved. That is a bug producing safety, not a design. The queue-build site additionally swallows every exception with a bare `except Exception: pass` (`oc_runipd.py:2933-2934`), so a refusal there would be silent. | Cited call sites plus the F-2 measurement. |
| F-4 | **`CONDITIONAL-GO` is tested for but documented nowhere.** `oc_runipd.py:536` matches `Readiness:\s*(NO-GO|CONDITIONAL-GO)`, yet neither the verdict vocabulary (`plan-review.md:487-493`) nor the readiness vocabulary (`:495-507`) contains it. Kept as negative for compatibility, with the anomaly recorded rather than silently propagated. | `oc_runipd.py:534-537`; both vocabulary blocks in `plan-review.md`. |
| F-5 | **A naive newest-entry grep would FALSELY refuse three live plans, which is why E-03 discriminates review entries.** All three pending plans matching `REJECT - NEEDS REPLAN` are the item-13 successors `6lu3rq`, `m73aet`, `wlxkoz`; each one's NEWEST history line is a `to-review` entry narrating the RETIRED predecessor's REJECT (`6lu3rq` line 19: "`kaygwo` was `REJECT - NEEDS REPLAN` twice"). Refusing these would block exactly the plans that correctly replaced the rejected ones. | `grep -rlE 'REJECT - NEEDS REPLAN' .aw/records/plans/pending/` -> those 3 files; line 19 of `6lu3rq` read in full. |
| F-6 | **The typed artifact is the sound surface for SEVERITY but cannot carry the verdict today, so BOTH sources are needed.** `review_findings.py` ships closed, validated enums (`SEVERITIES`, `DECISIONS` at `:54-60`) and the ready-made `plan_gating_blocks` (`:758`) with four existing consumers. But `- Verdict:` is parsed into `ReviewDocument.verdict` (`:190`, `:643`) with NO enum, NO value validation, and NO reader anywhere in the package. Worse, the actual damage case is invisible to it: only 3 review artifacts exist, and the five REJECTed plans recorded their verdict in plan PROSE, not in any `.review.md`. A typed-only gate would have been vacuous. | `review_findings.py` cited lines; `ls .aw/records/reviews/` -> 3 files; the five REJECT verdicts read from the plans' own `## Workflow history` in `superseded/`. |
| F-7 | **The existing findings gate would NOT have caught this case either.** `check_engine._UNFIXED_DECISIONS` is `("open", "deferred")` (`check_engine.py:2514`) and deliberately EXCLUDES `replan`, which is precisely the decision a `REJECT - NEEDS REPLAN` review records. So the verdict half of this gate is genuinely new work, not a rewiring. | `check_engine.py:2509-2514` including its stated rationale. |
| F-8 | **There are TWO approval surfaces and a gate in one leaves the other open.** `specs.run_set` (`specs.py:498`) duplicates the ~30-line interactive-then-refuse block from `status_set.py:472-500` verbatim; there is no shared approval predicate. Dual dispatch is documented at `specs.py:632-634`: `--status` routes to `specs.run_set`, positional routes to `status_set.run_set_command`. | Both blocks read; `specs.py:632-634`. |

## Proposed changes (ordered, validatable)

1. New module `plan_readiness.py`: bounded newest-first history extraction (E-01), the closed verdict/readiness vocabularies (E-02), review-entry-discriminating verdict classification (E-03), and the composed `approval_refusals` predicate (E-04).
2. Gate `status_set.validate_transition_allowed` at `:502` on that predicate (E-05), and add the `--allow-open-questions` override with an auditable history entry (E-06).
3. Gate the forked spec surface identically so neither spelling bypasses it (E-07).
4. Tests: predicate-level, sabotage-verified (E-08); CLI-level refusal, atomicity, and non-regression of the clean approval path (E-09).

## Deferred / out of scope (with reason)

- **Repairing `is_plan_review_approved` and its `agy` twin in place, and rewiring `--full-auto` onto the new predicate.** The duplicate pair (`oc_runipd.py:527`, `agy_runipd.py:484`) and the bare `except Exception: pass` at `oc_runipd.py:2933` are real defects (F-3), but both runner files are the declared scope of pending `rununify` (`5e4sb6`) de-duplication and of `97df1z`, whose E-02 already proposes moving these helpers into a `plan_readiness` module. This plan therefore CREATES the module they will consume and touches neither runner, dissolving the collision instead of racing it. `--full-auto` remains safe in the interim because it shells out to `aw set approved`, which this plan gates.
- **Adding a validated `Verdict` enum to the typed review artifact.** Worth doing (F-6: the field is parsed but unvalidated and unread), but it changes an artifact contract with its own review workflow and would not have prevented the incident, since the damage case had no typed artifact at all. Belongs in its own plan.
- **Gating on the ABSENCE of any review.** Deliberately not done: it would block the legitimate author-then-approve path, and the shipped precedent is absent-means-silent (`review_findings.py:768-773`). The backlog item asked for this to be decided explicitly rather than by omission; this is the explicit decision.
- **One coherent review of the whole lifecycle-gate layer.** The backlog item notes four defects found in one session (`gjadwm`, `wwdm4g`, `v880xk`, and this). That review is a separate exercise; this plan fixes the one that produces an executable artifact.

## Scope check

- Over-scope: none. Every path in Scope-Paths is touched by a named E-item.
- Under-scope: the runner-side prose readers stay unfixed and `--full-auto` keeps consuming the broken predicate (both deferred above with the collision reason). No third approval surface exists: `grep` for callers of `validate_transition_allowed` and `specs.run_set` finds only the CLI entry points already enumerated in E-05..E-07.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_plan_readiness.py tests/test_status_set.py` for the per-test counts on the two directly-affected modules.
- The full suite BARE, `python3 -m pytest`, from the PRIMARY checkout, reconciled against the current baseline `3864 passed, 3 skipped, 4 xfailed`.
- A live end-to-end refusal against a REAL rejected plan (one of the five in `superseded/`, copied to a scratch fixture, since the tree's own plans must not be mutated by a test).
- `aw ipd lint --phase pre-transition` conforming on this plan.

## Spec / documentation sync

- No spec change: the verdict and readiness vocabularies already exist in `plan-review.md:487-507`; this plan makes them machine-readable rather than redefining them.
- `AGENTS.md` needs no edit: it already instructs agents to record approval via the tools, and this plan changes what those tools REFUSE, not the contract's prose. If E-06's flag warrants a mention, add it to the approval paragraph only after the flag exists, not speculatively.

## Open questions

### OQ-01: Should the override flag be spelled `--allow-open-questions`, or reuse an existing convention?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-03: use `--allow-open-questions`. It names exactly what it permits and cannot be confused with the verdict half, which has NO override by design. The backlog item requires only that it be a named flag, that it be recorded in history, and that `--by-human` not imply it; all three hold.

### OQ-02: Should a NEGATIVE verdict also gate `aw specs set approved`?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-03: do not add spec verdict gating now. Apply the open-question approval gate to specs, but do not define a spec-review artifact within this plan. `review_findings` keys review artifacts by `Plan-Id` (`review_findings.py:67`, `:187`, `:353`), so no formal spec verdict exists to inspect today. E-07 calls the shared predicate, allowing verdict gating to activate automatically if a spec-review type is added later. A spec-review artifact is a separate follow-up concern.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL output of a loop over all 26 `.aw/records/plans/pending/*.ipd.md` printing `extract_newest_history_entry`'s first 60 characters per plan, showing every line begins `- ` with a date; plus the before/after pair for `bl9q3d` showing the shipped function returns `- Cohesion rationale: ...` while the new one returns a dated history line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -c` output printing `VERDICTS` and showing `APPROVE WITH REVISIONS APPLIED` classifies as `positive` (NOT via the `APPROVE` prefix) and `REJECT - NEEDS REPLAN` as `negative`; plus the comment text recording that `CONDITIONAL-GO` is undocumented.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `newest_verdict` output for all three of `6lu3rq`, `m73aet`, `wlxkoz` showing NON-negative (their REJECT belongs to a predecessor), alongside output for a fixture whose newest review entry states `REJECT - NEEDS REPLAN` showing `negative`. Both halves are required: the second alone would pass with a naive grep.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `approval_refusals` output for four inputs: a REJECTed fixture with `allow_open_questions=True` (still refuses, naming the verdict), `mjx7ne` with `False` (refuses naming `OQ-03`) and with `True` (empty), and a clean plan with no review (empty). Confirm in prose that `plan_gating_blocks` was CALLED rather than reimplemented, citing the import line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the full terminal output and exit code of `aw ipd set approved` against a scratch copy of a REJECTed plan, showing exit 1 and the refusal reason; plus `git diff --stat` (or a sha256 before/after) proving the file is UNCHANGED and carries no `- Approval:` line; plus the batch case showing a three-plan selection containing one REJECTed plan approved NONE of them.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste three runs against a scratch plan carrying a blocking open question: bare (refuses), with `--by-human` only (STILL refuses, proving no implication), and with `--allow-open-questions` (succeeds); plus the resulting `## Workflow history` line showing the override recorded in the artifact.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste both spellings, `aw specs set <spec> --status approved` and the positional `aw specs set approved <selector>`, against a scratch spec with a blocking open question, showing BOTH refuse identically and both accept with `--allow-open-questions`. A single-spelling demonstration is insufficient because dual dispatch is the bypass.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the COMPLETE `python3 -m pytest -o addopts="" tests/test_plan_readiness.py` output with its per-test count and exit code, PLUS the sabotage evidence: for each of the three central assertions (review-entry discrimination, newest-first ordering, section bounding) paste the FAILING output produced when that predicate branch is deliberately broken, then confirm the break was reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the COMPLETE `python3 -m pytest -o addopts="" tests/test_status_set.py` output with per-test counts and exit code, showing the new refusal/atomicity cases AND the pre-existing `test_custom_message_and_by_human_attestation` still passing; plus the bare full-suite `python3 -m pytest` summary line reconciled against the `3864 passed, 3 skipped, 4 xfailed` baseline, with any delta explained change-by-change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. It is a SAFETY gate on the approval path itself, so the executor must be aware that a bug here can either block every legitimate approval (fail-closed too hard) or silently permit the exact accident it targets (fail-open). Both directions are covered by V-05 and V-09's non-regression case, and neither may be waived.

Execution contract: commit only files this plan changed, path-scoped, and never push. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. Do NOT edit either runner file: `oc_runipd.py` and `agy_runipd.py` are outside Scope-Paths deliberately (see Deferred), because pending `rununify` (`5e4sb6`) and `97df1z` own them.

Post-gate lifecycle: on completion move this plan to `.aw/records/plans/executed/` with `- Status: executed`, per the `ipd-lifecycle` workflow, only after every `V-*` above carries pasted evidence.
