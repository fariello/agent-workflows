# IPD: one shared needs-review predicate and the draft admission gate

- Date: 2026-09-04
- Kind: child
- Concern: THE REVIEW SWEEP AND THE DISPATCH TABLE DISAGREE ABOUT WHAT NEEDS REVIEW, and the disagreement is invisible. `determine_action` routes BOTH `to-review` AND `draft` to a review action (`oc_runipd.py:2409-2415`), while the `reviews` selector's membership test filters `status == "to-review"` alone (`:2252-2261`). So a complete `draft` plan named EXPLICITLY is reviewed, and the SAME plan is silently absent from the sweep. That is exactly the class of bug a single predicate prevents and two copies produce, and there ARE two copies: `_needs_review` is duplicated verbatim inside a closure in each runner, differing only in one loop variable name (`setid` versus `_setid`). Spec `25kzda` 2.4a, amended 2026-09-04, now makes the rule normative: membership MUST derive from the Section 3 dispatch table, implemented ONCE, "so an item the table routes to review and an item the sweep selects are the same set BY CONSTRUCTION". The same amendment adds Section 2.5a, which resolves the second half honestly: a complete draft is not silently swept up either, because promoting `draft` to `to-review` is a lifecycle write the operator did not name, so it passes a FRONT-LOADED admission gate (`run drafts` interactively, `--allow-drafts` unattended) asked once before any session rather than mid-run.
- Scope: Replace the two duplicated `_needs_review` closures with ONE shared predicate derived from the dispatch table, and implement spec 2.5a's draft admission gate on top of it. Three deliverables: the shared predicate, the gate's pure policy (preview, confirmation, refusal) beside the mixed-type gate it is modeled on, and the runner wiring that calls both. EXCLUDES cross-type discovery, so the predicate is structured to accept a type but ships knowing only IPDs (`5slbpi` widens it); excludes the review record's shape (`eyh1fu`); excludes every other spec 2.1 flag (`uyeko5`); excludes changing what a review turn DOES.
- Scope-Paths: agent_workflows/run_selection_policy.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_run_selection_policy.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:76gsmv
- Status: to-review
- Set: revsweep
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 6ypimw
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history
- 2026-09-04 to-review (aw set): set Item-Dependencies to executed:76gsmv

- 2026-09-04 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored with the `revsweep` Set. THE DRAFT ASYMMETRY IS THE FINDING THAT JUSTIFIES THIS PLAN and it was measured, not assumed: `oc_runipd.py:2252-2261` tests `st == "to-review"` while `:2409-2415` returns `review` for `to-review` AND `draft`, so the sweep and the router disagree, and the duplication in `agy_runipd.py:1347-1357` means fixing one copy leaves the other wrong. Verified by diff during research that the two selector branches produce exactly ONE hunk (the loop variable), which is what makes them a true duplicate rather than two evolved implementations. THE GATE'S SHAPE IS INHERITED, NOT INVENTED: spec 2.5a was written to mirror Section 2.5's mixed-type gate (resolve, preview, confirm, then work), because the maintainer's requirement was explicitly that the question be FRONT-LOADED rather than asked mid-run, and because `run_selection_policy.py` already ships that exact shape as tested pure code (`decide:576`, `render_action_preview:474`, `is_confirmation_accepted:543`, verbatim refusal at `:306`). So E-03 EXTENDS a proven module rather than writing a second gate, and the plan forbids a second copy explicitly. TWO ASYMMETRIES DELIBERATELY PRESERVED FROM THE SPEC, both recorded so an executor does not "simplify" them into a uniform rule: an INCOMPLETE draft is always a skip with findings and NO flag admits it (spec 3.2 already ruled that, and one unfinished draft must not deny review to the finished items beside it), and an ungated complete draft is EXCLUDED while the rest of the queue PROCEEDS, unlike the mixed-type refusal which starts no work at all, because a mixed selection means the operator's intent is unclear whereas the remaining items' intent is not in doubt. ONE HAZARD MEASURED AND ROUTED: `run_selection_policy.decide` currently has ZERO callers (the whole mixed-type gate is dead code), and `uyeko5` is the named owner of that call site; this plan therefore adds the DRAFT gate's policy to the module and wires the DRAFT gate only, and must not be read as fixing the dead mixed-type gate.

## Goal

Make the review sweep's membership and the dispatch table's routing the same set by construction, with one predicate instead of two copies, and admit complete drafts through a front-loaded gate rather than silently or never.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the divergence, then remove its cause

- [ ] E-01 Write the failing-first DIVERGENCE TEST before touching either runner: assert that for every plan status, membership in the `reviews` sweep equals "the dispatch table gives this status a review action". It MUST FAIL at current HEAD on the `draft` case, for BOTH hosts, because that is the bug.
  Drive it from the dispatch routing rather than from a hand-written status list, so the property survives a future status addition. This test is worth more than the refactor below: the refactor removes today's divergence, the test prevents tomorrow's.
  - Depends on: none
  - Expected outcome: one property test, failing at HEAD on `draft` for both hosts. Paste the failure.
  - Execution state: pending

- [ ] E-02 Extract ONE shared needs-review predicate and DELETE both closures. Put it where the selection policy already lives (`run_selection_policy.py`), not in a runner: the module is already the declared home of per-type status-to-action tables (`_IPD_ACTIONS:126`, `_SPEC_ACTIONS:140`, `_ACTION_TABLES:175`) and is already pure, which is what makes it testable without a host.
  DERIVE MEMBERSHIP FROM THE ACTION TABLE, do not restate it. The predicate is "the table gives this (type, status) a review action", so `ACTION_REVIEW` is the single source of truth and the `to-review`-only string comparison disappears rather than being corrected. A corrected copy would still be a copy.
  MIND THE ONE THING THE TABLES DELIBERATELY OMIT: `_IPD_ACTIONS` excludes `draft` and `reviewed` ON PURPOSE (`:127-131`), because those rows branch on content completeness, `--full-auto`, or `--action`, which the pure module cannot see. So the predicate MUST take the completeness answer as an INPUT rather than computing it, and `ACTION_UNDETERMINED` must not be silently treated as "needs review". The completeness input comes from `ipd_authoring.authoring_placeholders_resolved` (`:122`), which is the existing anchored, conservative check the `check.ipd-draft-ready-to-review` rule already uses; do NOT write a second completeness heuristic.
  PRESERVE THE TERMINAL-DIRECTORY EXCLUSION that both closures perform (`/executed/`, `/superseded/`, `/not-executed/`, `/reusable/`): it is not redundant with status, because a directory and status can disagree and spec 3.2 makes that mismatch a red abort rather than a review.
  - Depends on: E-01
  - Expected outcome: one predicate, both closures deleted, E-01 passing on both hosts; a grep shows no second membership test; completeness is an input, not a recomputation; the terminal-directory exclusion survives.
  - Execution state: pending

### Task group 2: the draft admission gate

- [ ] E-03 Implement spec 2.5a's gate as PURE POLICY beside the mixed-type gate, in the same module and the same shape: a preview naming the drafts, an exact-phrase confirmation (`run drafts`), a flag path (`--allow-drafts`), and the verbatim `[RUN-DRAFTS-EXCLUDED]` refusal from spec 2.5a.
  REUSE, DO NOT REIMPLEMENT. `is_confirmation_accepted` (`:543`) already implements exact-phrase matching with no case folding and no synonyms, `render_action_preview` (`:474`) already renders aligned per-type counts, and `Verdict` (`:266`) is already the typed return. Generalize those rather than adding a parallel set; a second confirmation implementation is how `y` eventually gets accepted somewhere.
  KEEP IT PURE: the module takes no TTY and no filesystem, and its docstring records that the caller performs the prompt and hands the typed response in, "which is what makes every branch testable". Do not break that to make wiring easier.
  IMPLEMENT THE TWO ASYMMETRIES EXACTLY, because a uniform rule would be wrong in both directions. (a) An INCOMPLETE draft is a SKIP WITH FINDINGS at every flag setting, never admitted, never an abort. (b) An ungated COMPLETE draft is EXCLUDED and the REST OF THE QUEUE PROCEEDS, which differs from the mixed-type refusal that starts no work at all; spec 2.5a states the reason and the code should carry it as a comment so nobody "fixes" the inconsistency.
  ALSO IMPLEMENT THE COMBINED CASE: when a selection is both mixed-type and draft-admitting, BOTH previews print together and BOTH confirmations are collected in ONE interaction before any work starts. That is the maintainer's actual requirement (front-load every question); collecting them serially across two prompts, or asking the second after the first item ran, defeats it.
  - Depends on: E-02
  - Expected outcome: the gate exists as pure policy reusing the shipped primitives; both asymmetries implemented and commented with their reasons; the combined mixed-plus-draft case collects both confirmations in one interaction; the refusal text matches spec 2.5a verbatim.
  - Execution state: pending

- [ ] E-04 Wire the gate into BOTH runners at the single point where the queue is built, BEFORE it is frozen and before any lease or session, passing the real TTY state and the flag.
  REGISTER `--allow-drafts` ON BOTH HOSTS' `run`/`start` parsers, and on `resume` with `default=None` following the existing pattern (`--full-auto` is re-declared that way so an omitted flag cannot clobber frozen state). Record the admitted set, the counts, the preview, and the response-or-flag in the run ledger, as spec 2.5a requires.
  DO NOT WIRE THE MIXED-TYPE GATE. `run_selection_policy.decide` has zero callers today and `uyeko5` E-02 is its named owner; two plans adding that call site is a merge conflict at best and a double gate at worst. If `uyeko5` has already landed its call site, ADD TO IT rather than adding a second one, and say which case applied.
  A HONEST LIMIT TO RECORD, not to fix: with IPD-only discovery there are no specs in the queue, so the COMBINED mixed-plus-draft path cannot be triggered by any real invocation yet. Prove it at the seam (constructed classification) and state plainly that it is proven correct and not proven fired, exactly as `uyeko5` V-02 is required to do for the mixed gate. Do not let a green test imply a live combined gate.
  - Depends on: E-03
  - Expected outcome: `--allow-drafts` parses on both hosts and on resume with `default=None`; the gate is called once per host at queue build; the ledger records the admission facts; the mixed-type call site is not duplicated; the untriggerable combined path is stated as such.
  - Execution state: pending

- [ ] E-05 Make the predicate's SIGNATURE type-aware while its KNOWLEDGE stays IPD-only, so `5slbpi` widens coverage without reopening this work. The predicate accepts a type and consults `_ACTION_TABLES`, which already carries a `spec` table; discovery still enumerates only plans, because `runner_shared.discover_plans` walks only the two plans trees.
  DO NOT ADD SPEC DISCOVERY HERE and do not pretend to. The gap is a real one (`5slbpi` owns it) and a predicate that accepts `spec` while nothing can supply one must SAY SO at its definition, so a later reader does not conclude cross-type sweeping works. Do NOT add `--type` either; that is `uyeko5`'s and spec 2.2/2.3's.
  - Depends on: E-04
  - Expected outcome: the predicate takes a type and answers correctly for `spec` when handed one directly; discovery is unchanged and documented as IPD-only; no `--type` flag is added; the limit is stated at the definition rather than implied.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `run_selection_policy.py` IS THE DECLARED HOME of per-type status-to-action policy and is deliberately PURE (no TTY, no filesystem), with its docstring recording that purity is what makes every branch testable. Its tables also deliberately OMIT the rows that branch on something status cannot reveal, mapping them to `ACTION_UNDETERMINED` rather than guessing. A predicate added here must respect both properties.
- `Verdict.WAIVES` and `decide`'s docstring record that `allow_mixed` is deliberately the ONLY override that predicate accepts, "so this predicate can never become the place another gate is waived". `--allow-drafts` is therefore a SEPARATE decision function, not a second parameter bolted onto `decide`.
- THE MODULE IS DEAD CODE TODAY (`decide` has zero callers), by the deliberate choice of executed plan `6lu3rq`, whose scope excluded wiring. `uyeko5` owns the mixed-type call site. This plan must add the draft wiring without racing that.
- `ipd_authoring.authoring_placeholders_resolved` is the EXISTING completeness check, anchored to exact scaffold marker strings so narrative prose containing "TODO" does not count. It is already what `check.ipd-draft-ready-to-review` uses. A second completeness heuristic would diverge from the nudge rule.
- BOTH RUNNERS ARE THE HIGHEST-CONTENTION FILES IN THE REPO, and `uyeko5` is sequenced behind the `rununify` consolidation for exactly that reason.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | **THE SWEEP AND THE ROUTER DISAGREE ABOUT `draft`, which is this plan's central defect.** A complete draft named explicitly IS reviewed; the same draft is silently absent from `reviews`. Neither behavior is announced, so the sweep quietly under-selects. | `oc_runipd.py:2252-2261` (`return st == "to-review" and not is_non_pending`) versus `:2409-2415` (`if norm in ("to-review", "draft"): return "review"`) |
| F-2 | THE PREDICATE IS A TRUE VERBATIM DUPLICATE, not two evolved implementations: diffing the two selector branches with comments stripped yields exactly one hunk, the loop variable name. So a one-sided fix leaves the other host wrong, and the shape itself is the bug. | verified during research: oc `:2244-2282` versus agy `:1339-1375` differ only `setid` versus `_setid`; backlog `cnwy8g` tracks the wider 40-symbol duplication |
| F-3 | THE `all` SELECTOR ALREADY INCLUDES `draft` while `reviews` excludes it, so the two selectors in the same function disagree about the same status. This is corroboration that the divergence is accidental rather than a deliberate policy about drafts. | `oc_runipd.py:2286-2292` (`actionable_statuses` contains `"draft"`); `:2252-2261` (`_needs_review` does not) |
| F-4 | THE GATE PRIMITIVES ALL SHIP ALREADY, tested, which is why E-03 is an extension rather than a build: exact-phrase confirmation, aligned per-type preview, typed verdict, and a verbatim-refusal precedent. Writing a second confirmation path would risk accepting `y` somewhere. | `run_selection_policy.py:543` (`is_confirmation_accepted`), `:474` (`render_action_preview`), `:266` (`Verdict`), `:306` (`REFUSAL_TEMPLATE`), 26 tests in `tests/test_run_selection_policy.py` |
| F-5 | THE ACTION TABLES DELIBERATELY OMIT `draft` AND `reviewed`, mapping them to `ACTION_UNDETERMINED`, because those rows branch on content completeness, `--full-auto`, or `--action`. So the predicate CANNOT compute draft membership from status alone and must take completeness as an input; treating `ACTION_UNDETERMINED` as "needs review" would sweep up incomplete stubs. | `run_selection_policy.py:126-138` with the rationale comment at `:127-131`; `ACTION_UNDETERMINED:109`; `_action_for:323` |
| F-6 | A COMPLETENESS CHECK ALREADY EXISTS and is anchored conservatively, so E-02 must consume it rather than write a heuristic. It is already the basis of the `check.ipd-draft-ready-to-review` nudge, so a second version would make the nudge and the sweep disagree about the same draft. | `ipd_authoring.authoring_placeholders_resolved:122-133`; `ipd_lint.py:1003`; rule at `check_engine.py:245-247` |
| F-7 | THE MIXED-TYPE GATE IS DEAD CODE AND ANOTHER PLAN OWNS ITS CALL SITE, so this plan must not wire it. Two plans adding the same call site is a conflict; a double gate is worse. | `run_selection_policy.decide:576` has zero callers (measured); `uyeko5` E-02 is the declared owner and its F-2 records the same measurement |
| F-8 | THE COMBINED MIXED-PLUS-DRAFT PATH CANNOT FIRE ON A REAL INVOCATION YET, because discovery is IPD-only and neither runner has `--type`, so no selection can contain two types. E-04 must prove it at the seam and label it correct-not-fired, or a green test will be misread as a live gate, exactly as `uyeko5` F-9 warns for the mixed gate. | `runner_shared.discover_plans:614-639` (walks only the two plans trees); `--type` greps to zero in both runners; `run_selection_policy.py:635` short-circuits `gate_applied=False` when not mixed |
| F-9 | THE POPULATION IS TINY AND THAT IS NOT THE ARGUMENT. At authoring: 1 plan at `to-review`, 0 plans at `draft`, 2 specs at `draft`. So the draft gate has NO plan to gate today, and its justification is correctness of the predicate rather than volume. Recorded so nobody claims a throughput win. | `aw find plans --status to-review` returns 1 (`uyeko5`); `--status draft` returns 0; 2 draft specs measured by direct grep |

## Proposed changes (ordered, validatable)

1. Failing-first property test that sweep membership equals dispatch-table routing, failing at HEAD on `draft` for both hosts (E-01).
2. One shared predicate derived from the action table, both closures deleted, completeness taken as an input from the existing anchored check (E-02).
3. The draft gate as pure policy reusing the shipped confirmation/preview/verdict primitives, with both asymmetries and the combined case (E-03).
4. Runner wiring at queue build, `--allow-drafts` on both hosts including resume, ledger records, without touching the mixed-type call site (E-04).
5. A type-aware signature with honestly IPD-only knowledge, so `5slbpi` widens coverage without reopening this (E-05).

## Deferred / out of scope (with reason)

- WIRING THE MIXED-TYPE GATE (`decide`'s missing call site). Owned by `uyeko5` E-02 (F-7). Two owners of one call site is a conflict, and this plan's gate is a sibling decision function, not a parameter on `decide`.
- CROSS-TYPE DISCOVERY, so the sweep can actually reach a spec: `5slbpi`, which needs `eyh1fu` first. E-05 makes the signature ready and states the limit rather than implying coverage.
- `--type` AND MULTI-TYPE SELECTION: spec 2.2/2.3, and the reason the combined gate path is untriggerable (F-8). Registering it would mean teaching the runner to discover and dispatch non-IPD artifacts, which is the whole per-type dispatch table.
- EVERY OTHER SPEC 2.1 FLAG: `uyeko5`.
- THE REVIEW RECORD'S SHAPE and anything about what a review turn produces: `eyh1fu`.
- CHANGING `all`'s MEMBERSHIP. F-3 notes `all` already includes `draft`, which corroborates the bug, but altering `all` is a behavior change to a second selector with its own blast radius and no spec amendment behind it. Recorded, not touched.

## Scope check

- Over-scope: none. Every edit removes a duplicated membership test, implements a spec-2.5a-declared gate, or wires one of the two.
- Under-scope, DELIBERATE and stated plainly: after this plan the sweep still enumerates only IPDs, so the draft gate can gate only plans, and at authoring there are ZERO draft plans to gate (F-9). The gate is therefore correct and largely unexercised in production until `5slbpi` lands spec discovery. That is stated rather than dressed up, and it is why E-05 prepares the signature instead of the coverage.
- Under-scope: the combined mixed-plus-draft path is proven at the seam only, because no real invocation can produce two types yet (F-8).

## Required tests / validation

- E-01's property test, FAILING at pre-change HEAD on the `draft` case and passing after, for BOTH hosts. This is the load-bearing evidence for task group 1: a test that only checked `to-review` would have passed against the buggy code.
- A grep proving ONE membership predicate exists and both closures are gone. The refactor's whole value is the absence of the second copy, so its absence must be shown, not asserted.
- The predicate answering correctly for a COMPLETE draft and an INCOMPLETE draft, with completeness supplied by `authoring_placeholders_resolved` rather than a new heuristic, shown.
- `ACTION_UNDETERMINED` NOT treated as needs-review, shown explicitly (that is the failure mode that would sweep up stubs).
- The gate: exact phrase `run drafts` accepted, `y` and empty REJECTED, `--allow-drafts` honored unattended, and the verbatim `[RUN-DRAFTS-EXCLUDED]` refusal matching spec 2.5a character for character.
- BOTH ASYMMETRIES demonstrated: an incomplete draft skipped-with-findings at every flag setting, and an ungated complete draft EXCLUDED while the remaining queue PROCEEDS (not a refused run).
- The combined mixed-plus-draft case collecting BOTH confirmations in ONE interaction before any work starts, proven at the seam, and LABELED as proven-correct-not-proven-fired (F-8).
- `--allow-drafts` on both hosts including `resume` with `default=None`; an omitted flag on resume does not clobber frozen state.
- The ledger carrying the admitted set, counts, preview, and response-or-flag.
- Evidence that the mixed-type call site was NOT duplicated; state whether `uyeko5` had landed.
- Both driver suites green plus `tests/test_run_selection_policy.py`.
- Full suite BARE (`python3 -m pytest`), compared against your own pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (backlog `dh0uno`).
- `aw check plans` NO-WORSENING against your own fresh baseline; do NOT claim it passes.

## Spec / documentation sync

- This plan implements spec `25kzda` 2.4a (the needs-review selector and its one-predicate rule) and 2.5a (the draft admission gate), both amended 2026-09-04. It MUST NOT change that text; if execution proves the spec wrong, amend it with `aw specs note` and say so rather than diverging silently.
- `76gsmv` documents the selector for operators. If this plan changes what the sweep SELECTS (it does: complete drafts become admissible), the help text `76gsmv` wrote must be re-checked for accuracy in the same change, since it is user-facing documentation that would otherwise become a false claim.
- `--allow-drafts`'s own `--help` text must state that it admits complete drafts only and cannot admit an incomplete one, so an operator is not misled into thinking it forces review of a stub.

## Open questions

### OQ-01: Should an ungated complete draft be EXCLUDED-and-proceed, or should it refuse the whole run like the mixed-type gate?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED by spec 2.5a as EXCLUDED-and-proceed, and recorded here because the asymmetry with Section 2.5's refuse-everything gate looks like an inconsistency and will invite someone to "fix" it. The reason the two differ: a MIXED selection means the operator's intent is genuinely unclear, so starting any work risks doing the wrong thing, whereas an ungated draft is one item's admission and the remaining items' intent is not in doubt, so refusing the whole run would punish the clear items for the unclear one. E-03 must carry this reason as a comment beside the branch.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the property test FAILING at pre-change HEAD, with the failure naming the `draft` divergence for BOTH hosts, then passing after. Paste the test showing membership is compared against the DISPATCH ROUTING rather than a hand-written status list, since that is the property that survives a future status addition.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a grep proving exactly ONE membership predicate exists and BOTH `_needs_review` closures are DELETED (paste the before-grep too, showing two). Paste the predicate showing membership derives from `ACTION_REVIEW` in the action table rather than a `to-review` string comparison. Paste the predicate answering correctly for a complete AND an incomplete draft, with completeness coming from `authoring_placeholders_resolved` and NOT a new heuristic. Paste evidence that `ACTION_UNDETERMINED` is NOT treated as needs-review. Paste evidence the terminal-directory exclusion survives.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the exact phrase `run drafts` accepted and `y`/empty REJECTED. Paste the `[RUN-DRAFTS-EXCLUDED]` refusal beside spec 2.5a's text, character for character. Paste evidence the shipped primitives were REUSED (the confirmation and preview functions are the existing ones, generalized, not new copies) and that `decide` did not acquire a second override, which its own docstring forbids. Paste BOTH asymmetries: an incomplete draft skipped-with-findings at every flag setting, and an ungated complete draft excluded while the rest proceeds. Paste the combined mixed-plus-draft case collecting both confirmations in ONE interaction.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `--allow-drafts` in `--help` for BOTH hosts and on `resume` with `default=None`, plus a resume with the flag omitted showing the frozen value survived. Paste the ledger record carrying the admitted set, counts, preview, and response-or-flag. Paste a grep proving the mixed-type `decide` call site was NOT duplicated, and STATE whether `uyeko5` had landed its call site. STATE PLAINLY, as a limitation and not a success, that the combined mixed-plus-draft path cannot be triggered by any real invocation yet (IPD-only discovery, no `--type`), so it is proven correct and NOT proven fired.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the predicate's signature accepting a type, and paste it answering correctly for a `spec` handed to it directly. Paste evidence discovery is UNCHANGED and that the IPD-only limit is stated AT THE DEFINITION, not merely in this plan. Confirm no `--type` flag was added. Then both driver suites, `tests/test_run_selection_policy.py`, and the bare full suite with counts, compared against your own pre-change measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 5 E-leaves across 2 task groups, one concern: make sweep membership and dispatch routing the same set, then admit drafts through a front-loaded gate. Task group 1 is the predicate (test, then extraction); task group 2 is the gate (pure policy, wiring, then the type-aware signature). E-02 and E-03 are separate because one removes a duplicate and the other adds a decision function, with different test surfaces; E-04 is separate from E-03 because purity is the module's stated invariant and wiring is where it would be broken.

Open questions: OQ-01 is RESOLVED (excluded-and-proceed, with the reason recorded so the asymmetry is not "fixed" later). No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It depends on `- Item-Dependencies: executed:76gsmv`, because `76gsmv` documents the selector for operators and this plan changes what that selector SELECTS (complete drafts become admissible); landing them in the other order would publish help text that is immediately stale.

Scope fence: touch ONLY `agent_workflows/run_selection_policy.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/runner_shared.py`, `tests/test_run_selection_policy.py`, `tests/test_oc_runipd.py`, and `tests/test_agy_runipd_cli.py`. Do NOT wire the mixed-type gate (`uyeko5` owns that call site). Do NOT add a second override parameter to `decide`, which its own docstring forbids. Do NOT add `--type`, spec discovery, or any other spec 2.1 flag. Do NOT write a second completeness heuristic; consume `authoring_placeholders_resolved`. Do NOT change `all`'s membership. Do NOT break the module's purity to simplify wiring. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is (1) E-01's property test observed FAILING on the `draft` case, because a test written against `to-review` alone would have passed against the bug, and (2) the ABSENCE of the second predicate, since the refactor's whole value is that the duplicate is gone. Do NOT report the combined mixed-plus-draft gate as firing in production; it cannot yet. Do NOT claim the sweep covers specs. Do NOT claim a throughput improvement: there were ZERO draft plans at authoring (F-9), so this is a correctness fix.

Execution contract: RE-READ both runner modules immediately before editing and locate every site BY SYMBOL, never by the line numbers in this plan: these are the highest-contention files in the repo and 11 other unexecuted plans declare them. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
