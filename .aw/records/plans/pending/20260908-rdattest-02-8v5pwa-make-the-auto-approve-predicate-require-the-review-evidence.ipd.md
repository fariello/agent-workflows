# IPD: Make the auto-approve predicate require the review evidence IPD-M107 already demands

- Date: 2026-09-08
- Kind: child
- Concern: `plan_readiness.is_plan_review_approved` believes a `- Readiness:` field without checking that a review produced it. `IPD-M107` closed the LINT layer (a fabricated field is a blocking finding and `aw ipd begin` refuses), but the PREDICATE is unchanged and still returns True for a hand-written value, and that predicate is what `--full-auto` consumes to promote `reviewed -> approved` and flip an item's queue action to `execute`. So the artifact is caught while the DECISION stays credulous: the field is read FIRST and the history is consulted only when the field is ABSENT, which means a forged field short-circuits the very evidence check that would expose it. Measured live: a plan with `- Readiness: go` and a history containing no review at all returns True.
- Scope: Make the predicate require the SAME history evidence `IPD-M107` requires, so field and history must AGREE, by calling the lint rule's existing evidence predicate rather than defining "attested" a second time. Add the test the item calls the real deliverable: the predicate returns False for a forged field. Preserve every other decision this predicate makes (out-of-vocab refusal, absent-field prose fallback, the blocking-open-question refusal) and keep the module stdlib-cheap and driver-agnostic, since both host drivers import it.
- Scope-Paths: agent_workflows/plan_readiness.py, tests/test_plan_readiness.py
- Item-Dependencies: none
- Status: to-review
- Set: rdattest
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8v5pwa
- From-Backlog: 754txs

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `754txs`. NOTE ON THE GATE FIELD: this item carries NO `- Blocks-Release:`, so this plan inherits none; it is `Work-Kind: security` at `Priority: high` but the maintainer did not gate it, and I have not added a gate the item does not carry. NOTHING IN THIS ITEM IS OBSOLETE. Verified at HEAD `8b4e1570` by RUNNING it, not reading it: a fixture plan carrying `- Readiness: go` and a history whose only line is `- 2026-09-08 to-review (someone): authored, NO review ever happened.` yields `is_plan_review_approved(...) == True`. The decision order the item describes is intact at `plan_readiness.py:297-327`: `read_readiness` first (`:312`), return on a valid value (`:313-315`), refuse OUTRIGHT on a present-but-out-of-vocab value (`:316-320`), and fall back to prose ONLY when the field is absent (`:322-327`). FOUR LIVE CONSUMERS, both hosts, so the blast radius is real: `oc_runipd.py:2968` and `:6718`, `agy_runipd.py:1988` and `:3988`. TWO MEASUREMENTS THAT DE-RISK THIS CONSIDERABLY AND ANSWER THE ITEM'S OWN STATED COST. The item's honest worry is that "a legitimate review that wrote the field but whose history line does not match the evidence pattern would newly fail closed", and it treats that as the price of the fix. I MEASURED THE PRICE AND IT IS ZERO TODAY: across every tracked plan, 65 carry a `Readiness` field, and the number whose auto-approve verdict would FLIP from True to False under the proposed change is 0. So the fail-closed direction costs nothing against the current corpus, which converts the item's main objection from a real cost into a bounded risk about FUTURE phrasings. SECOND, the item asks (its option 2) whether the predicate should call the lint rule directly and worries about the import direction, since `plan_readiness` is consumed by both drivers and "whatever it imports must stay stdlib-cheap and driver-agnostic". I verified this is SAFE: `ipd_lint` imports only `argparse`, `re`, `pathlib`, `typing`, plus `ipd_schema` and `term`; it names no driver module; and it does NOT import `plan_readiness` (the only mentions are comments), so there is no cycle. The anti-divergence guard `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests::test_shared_rule_modules_are_not_modified_by_the_runner` forbids `ipd_lint`/`check_engine` NAMING a driver, which this change does not do. So option 2 is available and is what E-01 implements, giving ONE definition of "attested" rather than two.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the promotion decision as sceptical as the lint rule. A forged `- Readiness:` should not be able to carry a plan from `reviewed` to `approved` under `--full-auto`, and the fix should leave exactly one definition of what "a review attested this" means.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: require agreement between field and history

- [ ] E-01 Make `is_plan_review_approved` (`agent_workflows/plan_readiness.py:297-327`) require review evidence in the plan's own `## Workflow history` even when the `- Readiness:` field is present and valid. Implement the item's OPTION 2 (call the lint rule rather than re-defining "attested"), because the alternative creates a second definition of attestation that can drift from `IPD-M107` exactly as the field and the history drifted in the first place. Reuse `ipd_lint`'s existing evidence predicate `_REVIEW_EVIDENCE_RE` / `check_readiness_attestation` (`ipd_lint.py:699-724`) rather than copying its pattern. THE IMPORT IS SAFE AND WAS VERIFIED, not assumed: `ipd_lint` imports only `argparse`, `re`, `pathlib`, `typing`, `ipd_schema` and `term`; it names no driver module; and it does not import `plan_readiness`, so there is no cycle. Keep the import at module scope only if that holds at execution time; if a cycle has appeared, import lazily inside the function rather than duplicating the pattern.
  - Depends on: none
  - Expected outcome: a plan with a valid `- Readiness:` and NO review evidence in its history returns False; a plan with both returns True; there is exactly ONE definition of the evidence pattern in the package.
  - Execution state: pending

- [ ] E-02 PRESERVE THE OTHER THREE DECISIONS this predicate makes, each verified separately, because the risk here is widening or narrowing the gate by accident. (a) A PRESENT BUT OUT-OF-VOCAB value must still refuse OUTRIGHT and must NOT fall through to prose (`:316-320`); its comment explains why (falling back could approve a plan whose author meant `no-go`). (b) An ABSENT field must still fall back to the corrected newest history record via `history_verdict_approves(extract_newest_history_entry(text))` (`:323`), which is the back-compat path for plans reviewed before the field existed. (c) The unresolved-blocking-open-question refusal must still apply (`:325-326`). ALSO PRESERVE the documented boundary that this function does NOT read `- Status:` (`:304-305`): the caller independently requires `Status: reviewed`, and pulling that in here would widen the gate's meaning.
  - Depends on: E-01
  - Expected outcome: all four behaviors demonstrated individually against fixtures, unchanged from HEAD `8b4e1570`.
  - Execution state: pending

- [ ] E-03 Re-measure the CORPUS EFFECT at execution time and report it, because this is a behavior change to a shipped gate and the maintainer's decision rests on its cost. Evaluate, over every tracked `.ipd.md`, how many plans carry a `Readiness` field and how many would have their auto-approve verdict FLIP from True to False. MEASURED AT AUTHORING TIME AS 65 carrying the field and 0 flipping, but the corpus changes daily and a fresh number is the only honest one. If any plan WOULD flip, do not silently accept it: name each one and say whether it is a genuine unattested field (correct to refuse) or a legitimate review whose phrasing the pattern misses (in which case the pattern, not the plan, may need widening).
  - Depends on: E-01
  - Expected outcome: a freshly measured count of Readiness-carrying plans and flipping plans, with every flip individually classified.
  - Execution state: pending

### Task group 2: the test the item calls the real deliverable

- [ ] E-04 Add the forged-field test, which the item names explicitly: "add a test asserting the predicate returns False for a forged field. That test is the real deliverable; the incident showed the predicate returning True four times in a row with nothing behind it." Put it in `tests/test_plan_readiness.py`, which already owns this surface and already has fixtures for the readiness reader (`:279-311`). Cover, as separate assertions: a forged `go` with no review evidence (False); the same plan with a `/plan-review` line added (True); an out-of-vocab value (False, and NOT via the prose path); an absent field with an approving history (True, back-compat preserved); an absent field with a rejecting history (False). Assert the test FAILS against HEAD `8b4e1570` for the forged case, so it is proven to bite rather than to restate current behavior.
  - Depends on: E-01, E-02
  - Expected outcome: five assertions covering the forged, attested, corrupt, back-compat-approve and back-compat-reject cases; the forged case fails before the fix and passes after.
  - Execution state: pending

- [ ] E-05 Confirm the four DRIVER call sites still behave, since the point of the change is to harden a decision those drivers make and a shared-module change reaches both hosts at once. The consumers are `oc_runipd.py:2968` and `:6718`, and `agy_runipd.py:1988` and `:3988`; re-locate them BY SYMBOL at execution time rather than by these line numbers, because both files are the most heavily edited in the repository and moved thousands of lines in a day. For each, state what the call gates (queue-action assignment versus the later promotion) and confirm a newly-False verdict produces a SAFE outcome there: the plan simply is not auto-approved, rather than an exception or a mislabelled queue action. DO NOT MODIFY THE DRIVERS: this item is a read-and-report obligation, and the anti-divergence guard requires the shared rule to stay in the shared module.
  - Depends on: E-04
  - Expected outcome: a per-call-site account (symbol, what it gates, behavior on a False verdict) confirming no driver edit is needed; no driver file modified.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The predicate's decision order is deliberate and documented: valid field wins, out-of-vocab refuses outright, absence falls back to prose. `ipd_schema.py:230` and `:317` both record that ABSENT MEANS UNKNOWN and the consumer fails closed on None. The defect is not the order; it is that a valid-looking field is accepted with no provenance.
- `IPD-M107`'s rule is deliberately EVIDENCE-based rather than authorship-based, and `ipd_lint.py` records why at length: a review legitimately writes the field in the same pass that sets `reviewed`, and `plan-review-long` can leave a plan at `to-review` with a recorded NO-GO. So keying on history evidence admits both while refusing a value with nothing behind it. That reasoning transfers to the predicate verbatim, which is why sharing the predicate is right.
- The evidence pattern is `_REVIEW_EVIDENCE_RE` (`ipd_lint.py:697-699`), matching `/plan-review`, `plan-review-long`, `APPROVE`, `NO-GO` and `REJECT` case-insensitively. Reuse it; do not copy it.
- `ipd_lint` is stdlib-cheap (`argparse`, `re`, `pathlib`, `typing`) plus `ipd_schema` and `term`, names no driver, and does not import `plan_readiness`. That is what makes the item's option 2 available.
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
| F-4 | THE ITEM'S STATED COST IS ZERO AGAINST THE CURRENT CORPUS: of all tracked plans, 65 carry a `Readiness` field and 0 would flip from True to False under the proposed change. | measured over `git ls-files .aw/records/plans` at `8b4e1570` |
| F-5 | The item's option 2 is SAFE, contrary to its own stated worry about the import direction: `ipd_lint` imports only `argparse`, `re`, `pathlib`, `typing`, `ipd_schema`, `term`, names no driver, and does not import `plan_readiness`, so there is no cycle. | read at `8b4e1570`; the only `plan_readiness` mentions in `ipd_lint.py`/`ipd_schema.py` are comments |
| F-6 | The anti-divergence guard constrains the shape of the fix but does not forbid it: it requires shared rule modules not to NAME a driver, and requires the runner to be a consumer of shared rules. | `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests::test_shared_rule_modules_are_not_modified_by_the_runner` |
| F-7 | The lint half is genuinely done and well covered, so this plan is the missing half rather than a re-do: `IPD-M107` is asserted at six places including a corpus scan. | `tests/test_ipd_lint.py:255`, `:263`, `:266`, `:286`, `:304`, `:321`, `:334` |
| F-8 | This item carries NO `- Blocks-Release:` field, so no gate is inherited. Recorded because it is `Work-Kind: security` at `Priority: high` and a reader might expect one. | backlog `754txs` front matter |
| F-9 | The same failure class has already caused real harm here, which is why fail-closed is the right direction: a blanket approval once swept five REJECT-ed plans into `approved`. | `plan_readiness.py:330-338` |
| F-10 | The residual window the item describes is real and this plan closes it: the mitigation was the EXECUTION boundary (`aw ipd begin`), leaving the predicate reachable directly on an unlinted plan and by any future caller that does not lint first. | backlog `754txs`, "HONEST SCOPE OF THE CURRENT MITIGATION" |

## Proposed changes (ordered, validatable)

1. Require history evidence even when the field is present, by calling the lint rule's predicate (E-01).
2. Preserve the out-of-vocab refusal, the absent-field prose fallback, the blocking-question refusal, and the no-`Status`-read boundary (E-02).
3. Re-measure the corpus flip count at execution time and classify every flip (E-03).
4. Add the forged-field test the item names as the real deliverable, proven to fail before the fix (E-04).
5. Report the behavior at all four driver call sites without modifying either driver (E-05).

## Deferred / out of scope (with reason)

- OPTION 1 FROM THE ITEM (re-implement the same history check inside `plan_readiness` rather than calling the lint rule). Rejected on the module's own history: this file exists because the logic was duplicated per driver once already, and a second definition of "attested" is the same mistake that let the field and the history disagree. Option 2 is chosen and F-5 shows it is safe.
- CHANGING WHAT `IPD-M107` ITSELF ACCEPTS. Its pattern and rationale are already reviewed and tested; this plan consumes it unchanged. If E-03 finds a legitimate review whose phrasing the pattern misses, that is a finding to report, and widening the pattern would be a change to the LINT contract needing its own justification.
- MAKING THE PREDICATE READ `- Status:`. Explicitly documented as the caller's responsibility, and folding it in would widen the gate's meaning rather than harden its provenance.
- AUDITING OR REWRITING THE 65 PLANS that carry a `Readiness` field. None of them flips (F-4), and `IPD-M107` plus its corpus test already police the tree.
- HARDENING ANY OTHER `--full-auto` PROMOTION INPUT. The item is scoped to this predicate; a broader audit of what `--full-auto` trusts would be a legitimate but separate piece of work.

## Scope check

- Over-scope: none. Two files, both required by E-01 and E-04. The drivers are deliberately NOT in `Scope-Paths` even though E-05 reads them, because E-05 is a read-and-report obligation and the anti-divergence guard requires the rule to stay shared.
- Under-scope: the lint rule is unchanged; no plan file is audited or rewritten; no other auto-approve input is examined.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_plan_readiness.py tests/test_ipd_lint.py tests/test_runner_item_dependencies.py` for the focused surface, the last of these because the anti-divergence guard constrains this change's shape.
- The E-03 corpus measurement, re-run at execution time and pasted.
- The forged-field reproduction run by hand before and after, showing True then False.

## Spec / documentation sync

No `.spec.md` file defines the auto-approve predicate's provenance requirement, so none is edited and none is declared in `Scope-Paths`. The authoritative documentation is in code and MUST be corrected by E-01: `plan_readiness`'s module docstring and the `is_plan_review_approved` docstring both currently state that the structured field "wins" and "beats any prose in the history line" (`:300-302`, `:314`), which will no longer be true once the field must AGREE with the history. Leaving that text in place would make the module document the credulous behavior this plan removes. The `AGENTS.md` guidance already tells agents never to hand-write `- Readiness:` and needs no change; this plan makes the gate enforce what that guidance already says.

## Open questions

### OQ-01: If a future legitimate review phrases its history line outside `_REVIEW_EVIDENCE_RE`, should the predicate widen or should the review be corrected?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, and measurably not urgent: zero of 65 Readiness-carrying plans flip today (F-4), so no such phrasing exists in the corpus. The item names this as the fix's real cost, and the honest answer is that fail-closed is correct here because the failure mode is a plan NOT being auto-approved, which a human can resolve in one command, versus an unreviewed plan being executed, which is the incident that created this Set. RECOMMENDATION: correct the review's phrasing rather than widen the pattern, since `/plan-review` is the writer and can be made to emit a matching line; widening the pattern weakens the same check at the lint layer too, because E-01 deliberately shares it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the forged-field reproduction BEFORE (True) and AFTER (False) using the same fixture, plus the same fixture with a `/plan-review` history line added showing True after the fix. Paste the `git diff` of the predicate and a grep proving the evidence pattern is defined ONCE in the package (in `ipd_lint`) and referenced, not copied, by `plan_readiness`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: four separate demonstrations with their inputs and returned values: (a) an out-of-vocab `Readiness` returns False AND is shown not to consult the prose path; (b) an absent field with an approving history returns True; (c) an unresolved blocking open question returns False; (d) proof the function still does not read `- Status:` (for example a plan whose `Status` is `draft` but whose review approved returns True from this function alone).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the freshly measured counts (plans carrying `Readiness`; plans whose verdict flips) from a script run at execution time, not the authoring-time numbers. If any plan flips, paste its name and the classification (genuinely unattested versus phrasing the pattern misses).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the five new assertions' source and names, their passing result, AND the forged-field assertion FAILING against pre-change code (stash the fix and re-run). Paste the `python3 -m pytest tests/test_plan_readiness.py` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: for each of the four call sites, paste the symbol name and surrounding lines AS FOUND at execution time (proving they were re-located, not copied from this plan), state what the call gates, and state the behavior on a False verdict. Paste `git status --porcelain` showing neither driver file was modified. Paste the bare `python3 -m pytest` summary line and the `tests/test_runner_item_dependencies.py` result, and compare to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, which is doubly appropriate given that this plan is about forged values of that exact field. A reviewer should note F-4: the item's own stated cost for this change measures as zero against the current corpus, which is the strongest argument for taking the fail-closed direction now.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD: this plan hardens the predicate that decides whether a plan may be auto-approved, so it must NOT be executed under `--full-auto` on the strength of its own change, and its own approval must come from a human. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
