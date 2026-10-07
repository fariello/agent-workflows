# IPD: Restore the reusable-plan fail-open guard for plan_already_finalized and correct its dead test citations

- Date: 2026-10-02
- Kind: child
- Concern: `ipd_lifecycle.plan_already_finalized`'s docstring forbids substituting `run_selection_policy.is_in_terminal_directory` for its `executed`-bucket predicate and asserts that `tests/test_finidem_double_finalize.ReusablePlanIsNotAlreadyFinalized` "fails if the substitution is ever made". That file does not exist, so the asserted tripwire does not fire and the forbidden substitution is unguarded. Authoring also found a SECOND dangling citation of the same dead file that the backlog item does not mention (the `FINDING_RECEIPT_*` distinctness comment), and measured that the substitution's real consequence is WORSE than the backlog item states: it is not merely a misclassification at `finalize_precheck`, it converts a driver-seam refusal into exit code 0.
- Scope: Add behavioral coverage at `tests/test_finidem_reusable_not_finalized.py` that drives the shipped predicate and the shipped driver seam over a synthesized repo, asserting (a) `plan_already_finalized` answers False for a `reusable/` plan and True for an `executed/` one, (b) a receipt-less reusable plan classifies `receipt-never-issued` and NOT `receipt-consumed-already-finalized`, and (c) `runner_shared.finalize_outcome` keeps a nonzero refusal for that plan. Then repoint BOTH dangling citations in `ipd_lifecycle.py` at tests that actually exist. EXCLUDES widening any `aw check` rule to scan source docstrings (owned by `j7daih`), the other 87 dangling source citations measured during authoring (owned by `iosmvn`, `9vfxhn`, and per-path items), and restoring any other class from the deleted file.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_finidem_reusable_not_finalized.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: tvv8gg
- Set: tvv8gg
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: pud8rp
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 (MEDIUM, fixed: E-04/V-04 gain an `executed/` positive contrast at the driver seam so the nonzero assertion cannot pass vacuously), PR-002 (MEDIUM, fixed: gate's unconditional `aw ipd finalize` made conditional on runner ownership), PR-003 (LOW, fixed: E-01/E-05/V-06 name the exact mutation and use `git grep` so the `.pyc` binary match is not counted), PR-004 (LOW, fixed: F-05 purge date corrected to 2026-09-23). Re-measured at HEAD `ca03f0c56`: dead file absent, two `git grep` citation sites, `if bucket != "executed"` present, `/reusable/` in `TERMINAL_DIRECTORY_SEGMENTS`, deletion by `19313eed7`, no surviving reusable+finalize guard; scratch-repo probe gave precheck `(1, receipt-never-issued)`, `finalize_outcome` 1 for reusable and 0 for an `executed/` plan, and under the in-process substitution `(1, receipt-consumed-already-finalized)` with `finalize_outcome` 0.

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `tvv8gg`. The item carries NO `- Blocks-Release:` gate and its `- Work-Kind:` is `chore`, so none is invented here; `chore` is inherited and F-06 re-derives why that classification is correct. EVERY FACTUAL CLAIM IN THE ITEM VERIFIES at HEAD `1ed8ee3bc470f2a98d2219a4ba36c9cf5e28b240`: `ls tests/test_finidem_double_finalize.py` reports "No such file or directory"; `plan_already_finalized` still reads the `executed` bucket (`bucket != "executed"` returns False early); and the measured predicate answers `already=False, bucket='reusable'` for a `/reusable/` path while `is_in_terminal_directory` answers True for that same path with `_IPD_ACTIONS["reusable"] == "execute"`. AUTHORING CORRECTS THE ITEM ON TWO POINTS THAT CHANGE THE WORK, which is why E-01 re-derives them rather than trusting this plan. FIRST, the item says "the only occurrence of `ReusablePlanIsNotAlreadyFinalized` anywhere in the tree is the docstring line", which is true of that SYMBOL but understates the defect: `grep -rn test_finidem_double_finalize agent_workflows/ tools/ docs/ *.md` returns TWO lines, the docstring at `plan_already_finalized` and a `#:` comment above `FINDING_RECEIPT_NEVER_ISSUED` claiming the finding ids are "pinned distinct by" the same dead file. Fixing only the named one leaves a second false claim in the same module, so F-02 scopes both. SECOND, the item's harm model stops at classification ("a never-issued begin receipt would read as consumed and the run would proceed with NO execution authority"); authoring INJECTED the forbidden substitution and measured the seam, finding that `finalize_precheck` still REFUSES (exit 1) with the wrong finding, and that the actual exit-0 conversion happens one layer out at `runner_shared.finalize_outcome`, whose `finalize_already_done` delegate returned True and rewrote the refusal to "finalize is a NO-OP ... proceeds to integration". That is what makes E-04 demand a driver-seam assertion rather than a predicate-only one, and it is the difference between a guard that would have caught the real fail-open and one that would not. THE DELETED COVERAGE WAS BEHAVIORAL, NOT A CODE-STRUCTURE PIN, measured by reading it at `git show 98f82ed92:tests/test_finidem_double_finalize.py`: the class called the real predicate and the real `finalize_precheck` over a scratch git repo and asserted on returned verdicts and finding tuples, reading no production source text. It went out in `19313eed7` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24), a bulk size trim, NOT in `80db6750c` ("delete 366 tests that pinned code structure instead of behaviour", 2026-09-22). That ordering matters because it means `GUIDING_PRINCIPLES.md` P16 does NOT forbid restoring this coverage in its original shape, unlike the P16-deleted guards named in sibling item `rdl9lh`. OWNERSHIP WAS CHECKED BEFORE SCOPING: `python3 tools/lost_guard_census.py --dedupe` names `tvv8gg` as the sole owning item for this basename ("Match basis: basename substring"), and rollup `iosmvn` does not list it, so a per-item fix is correct and does not collide.

## Goal

Make the fail-open substitution that `plan_already_finalized`'s docstring forbids actually fail a test when made, and make both of that module's citations of the deleted `tests/test_finidem_double_finalize.py` name tests that exist, so an engineer reading either claim is told the truth about what protects the predicate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure before changing anything

- [ ] E-01 RE-DERIVE, at execution HEAD, the five facts this plan rests on, rather than trusting the numbers written here or in the backlog item. (1) That `tests/test_finidem_double_finalize.py` is still absent, and that `git grep -n test_finidem_double_finalize -- agent_workflows tools docs '*.md'` still returns exactly TWO citation sites (use `git grep`, not `grep -rn`: the latter also reports a `binary file matches` line for `agent_workflows/__pycache__/ipd_lifecycle.*.pyc`, which is not a citation) (the `plan_already_finalized` docstring and the `#:` comment above `FINDING_RECEIPT_NEVER_ISSUED`); if the count has changed, correct F-02's scope in writing. (2) That `plan_already_finalized` still keys on the `executed` bucket, by reading its body for the quoted string `if bucket != "executed"`. (3) That `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` still contains `/reusable/` and `_IPD_ACTIONS["reusable"]` is still `ACTION_EXECUTE`, since the whole hazard disappears if either changed. (4) WHICH COMMIT deleted the file, via `git log --oneline --all --diff-filter=D -- tests/test_finidem_double_finalize.py`, and whether its subject is the SIZE TRIM (`19313eed7`) or the code-structure-pin deletion (`80db6750c`); authoring measured the former, and if that is wrong then P16 may forbid the restoration shape this plan chose and the plan must stop and report rather than proceeding. (5) That NO surviving test already covers the reusable case, by searching `tests/` for `plan_already_finalized`, for `FINDING_RECEIPT_ALREADY_FINALIZED`, and for `plans/reusable` in combination with `finalize`; authoring measured the only two finding-constant uses in `tests/test_ipd_lifecycle_cli.py` and neither involves a reusable plan. IF A SURVIVING GUARD IS FOUND, STOP AND REPORT: the work then collapses to the citation correction alone and this plan is over-scoped.
  - Depends on: none
  - Expected outcome: a recorded execution-HEAD measurement of all five facts with the HEAD sha stated, each confirmed or corrected in writing, plus an explicit STOP if fact (5) finds existing coverage or fact (4) contradicts the size-trim attribution.
  - Execution state: pending

### Task group 2: Restore the guard, which is what makes the citation honest

- [ ] E-02 ADD `tests/test_finidem_reusable_not_finalized.py` with a fixture that synthesizes a scratch git repo (NOT the live checkout) and places a lint-clean completed plan under `.aw/records/plans/reusable/`. Follow the established local pattern rather than inventing one: `tests/test_ipd_lifecycle_cli.py`'s `_init_git` (which also writes the `.gitignore` entry for `.aw/state/` so a receipt never dirties the tree), `_completed_plan_text`, and `_commit_all`. Call `support.declare_execution_role(self)` in `setUp`, as every lifecycle test class in that module does, so the coordinator/worker role does not leak between `-n auto` workers. DO NOT import the private helpers from `test_ipd_lifecycle_cli` across modules; either reuse a shared helper in `tests/support.py` if one already exposes this, or define the fixture locally in the new file, and state in the module docstring which choice was made and why. The fixture is a separate E-item from the assertions because every later item depends on it and a wrong fixture (a plan that does not lint, or a repo with no commit) makes all three assertions fail for reasons unrelated to the property.
  - Depends on: E-01
  - Expected outcome: the new test file exists with a working scratch-repo fixture that places a completed plan under `reusable/`, and a trivial smoke assertion over it passes.
  - Execution state: pending

- [ ] E-03 ADD to that file the PREDICATE assertions, which are the counterfactual the docstring's warning turns on. Assert all four in the one test: `run_selection_policy.is_in_terminal_directory(<reusable path>)` is True (the rejected predicate ADMITS reusable, which is why it must not be substituted); `_IPD_ACTIONS["reusable"]` equals `ACTION_EXECUTE` (so such a plan is re-dispatched, not complete); `runner_shared.plan_bucket(<reusable path>)` is `"reusable"`; and `ipd_lifecycle.plan_already_finalized(...).already` is False for that path while it is True for a plan placed under `executed/`. Assert the POSITIVE and NEGATIVE cases in the same test so a future edit cannot satisfy it by making the predicate answer False for everything, which is the vacuous-pass failure mode `GUIDING_PRINCIPLES.md` P16 warns about under "Never weaken an assertion so it passes everywhere".
  - Depends on: E-02
  - Expected outcome: a passing test asserting the reusable/executed discrimination on the shipped predicate plus the two `run_selection_policy` counterfactual facts, with the executed-path case included so the assertion cannot pass vacuously.
  - Execution state: pending

- [ ] E-04 ADD the two CONSEQUENCE assertions, at the two seams the substitution actually damages, because a predicate-only guard would not have caught the real fail-open. FIRST, at the classification seam: `ipd_lifecycle.finalize_precheck(root, <reusable plan>)` returns `EXIT_FINDINGS` with `FINDING_RECEIPT_NEVER_ISSUED` present and `FINDING_RECEIPT_ALREADY_FINALIZED` ABSENT, and leaves the plan file unmoved. SECOND, at the driver seam: feeding that same refusal through `runner_shared.finalize_outcome(root, <reusable plan>, <id6>, code, message)` returns a NONZERO exit code, and `runner_shared.finalize_already_done(...)` is False. PAIR that with a POSITIVE CONTRAST in the same test: for a plan placed under `executed/` in the same scratch repo, `finalize_already_done` is True and `finalize_outcome(..., 1, <msg>)` returns 0, so the nonzero assertion cannot pass vacuously because `finalize_outcome` refuses everything (for example if the existence/containment guards from `1fzist` reject the fixture path). Construct both plan paths under the scratch repo root and pass that root as `repo`, since `finalize_already_done` returns False for a path not contained in `repo`. The second (driver-seam) assertion is the one that matters and is why this is not folded into E-03: authoring measured that under the forbidden substitution `finalize_precheck` still refuses (exit 1, wrong finding) while `finalize_outcome` converts the refusal to exit 0 with "finalize is a NO-OP ... proceeds to integration", so a guard that stopped at the finding tuple would miss the integration-without-authority outcome entirely. Assert on the EXIT CODE and the finding CONSTANTS, never by substring-matching refusal prose.
  - Depends on: E-03
  - Expected outcome: passing assertions that a receipt-less reusable plan refuses with `receipt-never-issued` (not `receipt-consumed-already-finalized`), stays unmoved, and still carries a nonzero exit code through `finalize_outcome`, alongside the `executed/` contrast for which `finalize_outcome` returns 0.
  - Execution state: pending

- [ ] E-05 PROVE THE GUARD IS SENSITIVE BY MUTATION and record the verbatim output, since an insensitive guard is exactly the hollow pin this plan exists to replace. TEMPORARILY substitute `is_in_terminal_directory` for the `executed`-bucket check in `plan_already_finalized` (the precise substitution its docstring forbids): replace the line `if bucket != "executed":` with `if not run_selection_policy.is_in_terminal_directory(plan_path):` (importing the module locally inside the function), leaving every other line unchanged. Run the new test file, and confirm it FAILS. Then RESTORE and confirm `git status --porcelain agent_workflows/ipd_lifecycle.py` is clean and the test passes again. DO THIS WITH A RESTORING WRAPPER (write the mutation, run, restore in a `finally`), never by hand-editing and remembering to undo it: a mutation left behind would commit the exact fail-open defect this plan forbids. Authoring's run of this measured the predicate flipping to `already=True, bucket='reusable'` and the driver seam flipping from exit 1 to exit 0; record what the test actually reports, because that message is what a future engineer will have to act on.
  - Depends on: E-04
  - Expected outcome: pasted evidence of the new test failing under the injected substitution and passing after restoration, a clean `git status --porcelain` for the mutated path, and the verbatim failure message.
  - Execution state: pending

### Task group 3: Correct the citations the guard now backs

- [ ] E-06 REPLACE BOTH dangling citations of `tests/test_finidem_double_finalize.py` in `agent_workflows/ipd_lifecycle.py`, and run the full fast suite. (a) In `plan_already_finalized`'s docstring, the sentence asserting that `tests/test_finidem_double_finalize.ReusablePlanIsNotAlreadyFinalized` "fails if the substitution is ever made" must name the new file and the test within it that E-05 proved sensitive. (b) In the `#:` comment above `FINDING_RECEIPT_NEVER_ISSUED`, the claim that the finding ids are "pinned distinct by `tests/test_finidem_double_finalize.py`" must EITHER name a surviving test that genuinely asserts their distinctness OR be rewritten to drop the pin claim; authoring found no surviving distinctness assertion, so do not repoint it at a test that does not make that assertion, which would recreate this defect in a new place. PRESERVE every other sentence in both comment blocks verbatim, in particular the OQ-02 fail-closed rationale and the "COMMIT IS CORROBORATION, NOT A REQUIREMENT" paragraph: this item changes citations, not the module's documented design. THEN run the full fast suite BARE as `python3 -m pytest` with no added flags, since `pyproject.toml`'s `addopts` already supplies `-q -n auto --dist=worksteal`; if any failure appears, re-run the same selection at the base commit before attributing it to this change and report the comparison either way.
  - Depends on: E-05
  - Expected outcome: no occurrence of `test_finidem_double_finalize` remains anywhere in `agent_workflows/ipd_lifecycle.py`, each replacement names a test that exists and actually asserts the cited property, unrelated prose is byte-unchanged, and a bare full-suite run's `N passed` summary is captured.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `GUIDING_PRINCIPLES.md` P16 forbids tests that read production source with `inspect`, `ast`, regex, or substring search, and forbids assertions on symbol censuses or caller counts. Every assertion this plan adds calls a shipped function over a synthesized repo and asserts on returned values, so none of it is a code-structure pin. P16's "Verify test sensitivity with mutation" bullet is what E-05 discharges.
- The repository test convention for lifecycle behavior is a scratch git repo built by `tests/test_ipd_lifecycle_cli.py`'s `_init_git` / `_completed_plan_text` / `_commit_all`, with `support.declare_execution_role` entered in `setUp`. The `.gitignore` written by `_init_git` is load-bearing: the begin receipt lives under `.aw/state/`, so without it a receipt write dirties the worktree.
- Assert on finding CONSTANTS (`ipd_lifecycle.FINDING_RECEIPT_NEVER_ISSUED`), never on refusal prose. The module's own `#:` comment says the constants exist "so no one has to match refusal PROSE", and the deleted guard followed that rule.
- Dangling test citations in this repository are triaged per-path with `python3 tools/lost_guard_census.py --dedupe`, which maps a basename to its owning backlog item. Check ownership before scoping, because three sibling items (`iosmvn`, `9vfxhn`, `3tov52`) and a rollup already claim other paths.
- Two citation checkers already ship and NEITHER covers source docstrings: `check_engine.check_spec_test_citations` scans spec normative bodies only, and `tests/test_docs_test_citations.py` scans `docs/**/*.md` plus five enumerated root prose docs. That is why the backlog item's "`aw check` has no rule for a dead test citation in a docstring" is correct, and why closing that gap is a different item (`j7daih`).

## Findings

| Id | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | The cited guard file does not exist, so the docstring's tripwire claim is false. | `ls tests/test_finidem_double_finalize.py` -> "No such file or directory" at HEAD `1ed8ee3bc`. | The core of the item verifies; the work is real. |
| F-02 | There are TWO dangling citations of that file in the module, not one. The item names only the docstring. | `grep -rn test_finidem_double_finalize agent_workflows/ tools/ docs/ *.md` returns the `plan_already_finalized` docstring line and a `#:` comment above `FINDING_RECEIPT_NEVER_ISSUED` claiming the finding ids are "pinned distinct by" that file. | E-06 fixes both. Fixing only the named one would leave a second false claim in the same module. |
| F-03 | The forbidden substitution is live-reachable and inverts the predicate. | Injecting `is_in_terminal_directory` in place of the bucket check flipped `plan_already_finalized` for a `/reusable/` path from `already=False, bucket='reusable'` to `already=True, bucket='reusable'`; restored clean afterwards. | The hazard is real and mutation-detectable, so E-05's sensitivity proof is achievable. |
| F-04 | The item's harm model is INCOMPLETE and understates the defect. `finalize_precheck` still refuses under the substitution; the exit-0 conversion happens at the driver seam. | Under the mutation, precheck returned `EXIT_FINDINGS` (code 1) with `('receipt-consumed-already-finalized',)` instead of `receipt-never-issued`; `finalize_already_done` returned True and `finalize_outcome` rewrote the refusal to exit 0 ("finalize is a NO-OP for reu777 ... proceeds to integration"). Baseline: exit 1, `receipt-never-issued`, "no execution authority". | E-04 must assert at BOTH seams. A predicate-only guard would not have caught the integration-without-authority outcome. |
| F-05 | The deleted coverage was BEHAVIORAL and was removed by a size trim, not by the P16 code-structure-pin purge. | `git show 98f82ed92:tests/test_finidem_double_finalize.py` shows `ReusablePlanIsNotAlreadyFinalized` calling the real predicate and `finalize_precheck` over a scratch repo, asserting on verdicts and finding tuples, reading no source text. `git log --diff-filter=D` names `19313eed7` ("trim test suite from 9,136 to under 2,000 tests", 2026-09-24), while the P16 purge `80db6750c` is 2026-09-23 (re-measured at review via `git log -1 --format=%ad`). | P16 permits restoring this in its original shape. Contrast sibling `rdl9lh`, whose deleted guard WAS a source parse and may not come back as written. |
| F-06 | `chore` is the correct Work-Kind, as the item argues. | The shipped predicate still reads the `executed` bucket (`if bucket != "executed"`), so no user-perceptible defect exists today; what is missing is the tripwire plus a false claim about the test suite. | Inherit `chore`; invent no release gate. If someone DOES make the substitution, that resulting defect is a `bug`. |
| F-07 | No surviving test covers the reusable case at any seam. | The only uses of the finding constants in `tests/` are two lines in `test_ipd_lifecycle_cli.py` (`test_finalize_precheck_precedence_over_receipt_refusals`), whose cases are an unbegun PENDING plan, a genuinely finalized plan, and a stale receipt; no test anywhere combines `plans/reusable` with `finalize`. | The gap is genuine, so E-01's fact (5) is expected to confirm rather than stop the plan. |
| F-08 | This citation is owned solely by `tvv8gg`, and the broader sweep is owned elsewhere. | `python3 tools/lost_guard_census.py --dedupe` -> "Owning item: tvv8gg [open] ... Match basis: basename substring"; rollup `iosmvn` does not name it. Authoring measured 89 dangling citations across 29 files in `agent_workflows/`. | Scope to this one path. The sweep and the missing checker rule stay out (see Deferred). |

## Proposed changes (ordered, validatable)

1. Re-derive the five load-bearing facts at execution HEAD, with an explicit stop condition if surviving coverage exists or the deletion attribution contradicts F-05 (E-01).
2. Add `tests/test_finidem_reusable_not_finalized.py` with a scratch-repo fixture placing a completed plan under `reusable/` (E-02).
3. Assert the predicate discrimination plus the `run_selection_policy` counterfactual, including the positive `executed/` case so it cannot pass vacuously (E-03).
4. Assert the consequences at both the classification seam and the driver seam, on exit codes and finding constants (E-04).
5. Prove the guard fails under the exact forbidden substitution, via a restoring wrapper, and record the message (E-05).
6. Repoint both dangling citations, preserving all unrelated prose, and run the bare full suite (E-06).

## Deferred / out of scope (with reason)

- WIDENING `aw check` TO SCAN SOURCE DOCSTRINGS for dangling test citations. Backlog `j7daih` ("Add check rule preventing live source comments from citing nonexistent test files") owns this and explicitly sequences it "once the baseline cleanup is complete". This plan is one unit of that baseline cleanup, so implementing the rule here would both collide with `j7daih` and fire on the 87 citations this plan does not fix.
- THE OTHER 87 DANGLING CITATIONS measured across 29 files in `agent_workflows/`. Owned by rollup `iosmvn` (trim-attributable, unowned paths), `9vfxhn` (non-trim deletion events), and dedicated per-path items. `tools/lost_guard_census.py --dedupe` names a distinct owner for this basename, and the established repository pattern is a per-item fix.
- RESTORING THE OTHER CLASSES from the deleted file (`TheSecondFinalizeOfTheSamePlan`, `PlanAlreadyFinalizedPredicate`, `BothHostsDriverFinalizeIsIdempotent`, `TheWorkerRoleCannotDelegateAroundTheGuard`, and others). The item scopes itself to "the reusable-plan half" and those classes assert different properties; restoring roughly 30 tests would also re-add bulk the `19313eed7` trim deliberately removed. A reviewer who wants them should file a separate item.
- ADDING A DISTINCTNESS TEST for the `FINDING_RECEIPT_*` constants. E-06(b) permits REWRITING that comment to drop its unproven pin claim rather than authoring new coverage, because the item's scope is the reusable-plan guard. Authoring found no surviving distinctness assertion; creating one is a legitimate follow-up but is not what this item asks for.
- TOUCHING `runner_shared.finalize_already_done`'s existence/containment guards. Plan `1fzist` (`rfhiu2-01`) owns that adjacent hole, and the item records that it "deliberately does NOT touch `plan_already_finalized`". E-04 only READS `finalize_outcome` as an assertion target and changes nothing there.

## Scope check

- Over-scope: none. Both `Scope-Paths` entries are required: `tests/test_finidem_reusable_not_finalized.py` is the restored guard, and `agent_workflows/ipd_lifecycle.py` holds both citations plus the mutation site E-05 temporarily edits and restores.
- Under-scope: The missing `aw check` rule for docstring citations is NOT fixed here, so a future dangling docstring citation in this module will still go undetected by tooling; `j7daih` owns that and this plan's Deferred section records the handoff. The `FINDING_RECEIPT_*` distinctness property may end up documented-but-unpinned if E-06(b) takes the rewrite branch, which is a deliberate narrowing to the item's stated "reusable-plan half" rather than an oversight.

## Required tests / validation

- The new `tests/test_finidem_reusable_not_finalized.py`, run bare and passing, covering the predicate discrimination (E-03) and both consequence seams (E-04).
- A mutation run proving the new file FAILS under the exact substitution the docstring forbids, with the production file restored byte-clean afterwards (E-05).
- A bare `python3 -m pytest` full fast-suite run with its `N passed` summary pasted, plus a pre-existing-versus-caused determination for any failure (E-06).
- A post-change `grep` proving no occurrence of `test_finidem_double_finalize` remains in `agent_workflows/ipd_lifecycle.py` and that each replacement citation resolves to a file on disk (V-06).

## Spec / documentation sync

N/A with reason. This plan changes two source comments and adds one test file. It alters no public contract, no CLI surface, no artifact grammar, and no lifecycle rule, so no `.spec.md` is amended and no `Scope-Paths` entry names a spec. The `ipd-structure-and-linting` spec is CITED (Step 0, for the citation-style rule) but not modified. `CHANGELOG.md` is deliberately not touched: this is internal test and comment hygiene with no user-visible behavior change.

## Open questions

### OQ-01: Should the `FINDING_RECEIPT_*` distinctness comment be repointed at a new test or rewritten to drop its pin claim?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, toward "either, with one forbidden option". Authoring searched `tests/` and found no surviving assertion that `FINDING_RECEIPT_NEVER_ISSUED` and `FINDING_RECEIPT_ALREADY_FINALIZED` are distinct strings, so the comment's "pinned distinct by" claim is false exactly as the docstring's claim is. E-06(b) therefore permits two branches and FORBIDS the third: name a test that genuinely asserts distinctness, or drop the pin claim; never repoint at a test that does not make the assertion, because that recreates the defect in a new place. The choice is left to execution because it depends on what E-01 fact (1) measures at execution HEAD. This is non-blocking: either branch leaves the module free of false claims, which is the plan's goal.

### OQ-02: Should the new guard live in a new file or be appended to `tests/test_ipd_lifecycle_cli.py`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED toward a NEW FILE, `tests/test_finidem_reusable_not_finalized.py`. Three reasons from repository evidence. (1) A citation must name a stable location, and `test_ipd_lifecycle_cli.py` is a large multi-concern module whose name does not describe this property, so a reader following the citation would have to hunt. (2) The repository's live pattern for a restored single-property guard is a dedicated narrowly-named file: sibling plan `d8sc5n` (`lanedangling-02`) creates `tests/test_worktree_lease_stdlib_only.py` for exactly this reason. (3) A new file carries no risk of disturbing the existing module's fixtures, which `tests/test_ipd_lifecycle_cli.py` shares across many classes. E-02 requires the module docstring to state whether the fixture was reused from `tests/support.py` or defined locally, so the cross-module-import question is answered in writing at execution time rather than guessed here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: The execution HEAD sha, plus pasted command output for each of the five facts: the `ls` of the dead file, the `git grep` citation count, the `executed`-bucket read, the `TERMINAL_DIRECTORY_SEGMENTS` / `_IPD_ACTIONS["reusable"]` values, the `git log --diff-filter=D` deletion attribution, and the three surviving-coverage searches. Each fact must be explicitly marked CONFIRMED or CORRECTED. If fact (5) found surviving coverage or fact (4) contradicted the size-trim attribution, the evidence must show the plan STOPPED.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The new file's path and module docstring, showing the stated choice between reusing a `tests/support.py` helper and defining the fixture locally. Pasted output of a run of the new file showing the fixture builds a scratch repo with the plan at a `.aw/records/plans/reusable/` path, and showing the plan lints clean at the pre-transition checkpoint (or an explicit statement of why a lint-clean plan is not required for these assertions).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted passing output of the predicate test, plus the asserted values: `is_in_terminal_directory` True for the reusable path, `_IPD_ACTIONS["reusable"]` equal to `ACTION_EXECUTE`, `plan_bucket` `"reusable"`, `plan_already_finalized(...).already` False for reusable AND True for the `executed/` path. The executed-path assertion must be visibly present, since it is what rules out a vacuous pass.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted passing output showing, for the receipt-less reusable plan, that `finalize_precheck` returned `EXIT_FINDINGS` with `FINDING_RECEIPT_NEVER_ISSUED` present and `FINDING_RECEIPT_ALREADY_FINALIZED` absent, that the plan file is still at its original path, that `finalize_already_done` is False, and that `finalize_outcome` returned a NONZERO code; plus the `executed/` contrast assertions (`finalize_already_done` True, `finalize_outcome` 0) visibly present in the same test. Evidence must also show the assertions reference the finding CONSTANTS rather than matching refusal prose.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted output of the new test file FAILING with the substitution injected, including the verbatim failure message; pasted output of it PASSING after restoration; and `git status --porcelain agent_workflows/ipd_lifecycle.py` showing empty output after the mutation was reverted. Evidence must show the mutation was applied and reverted by a restoring wrapper (the `finally` branch ran), not by hand.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted output of `git grep -n test_finidem_double_finalize -- agent_workflows` returning nothing (exit 1), plus the before/after text of both edited comment blocks showing each new citation names a path that `ls` resolves and that unrelated sentences (the OQ-02 fail-closed rationale, the corroboration-not-requirement paragraph) are unchanged. For branch (b), evidence must show EITHER the named test asserting distinctness OR that the pin claim was dropped. Plus the bare `python3 -m pytest` summary line with its `N passed` count, and for any failure a comparison run at the base commit attributing it as pre-existing or caused.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and requires explicit human approval before execution; its `- Readiness:` field was written by the 2026-10-07 `/plan-review` (see Workflow history and the typed review record).

The executing agent must: commit ONLY the two declared `Scope-Paths` entries, through `aw commit <plan> -- <paths>`, never `git add -A` and never `--no-verify`; paste ACTUAL runner output for every suite claim rather than asserting success; and run the suite BARE as `python3 -m pytest`, since `pyproject.toml`'s `addopts` already supplies `-q -n auto --dist=worksteal` and added flags such as `-n0` or a second `-q` would slow the run or suppress the summary line V-06 requires.

ONE EXECUTION-SPECIFIC HAZARD, stated because this plan deliberately mutates a shipped file: E-05 injects the exact fail-open substitution that `plan_already_finalized` forbids. That mutation MUST be applied and reverted by a restoring wrapper whose `finally` branch rewrites the original bytes, and V-05 requires a clean `git status --porcelain` for that path as proof. A mutation accidentally committed would ship the integration-without-authority defect F-04 measured. Do not stage `agent_workflows/ipd_lifecycle.py` until that check is green.

After every `E-*` is `performed` and every `V-*` is `pass` with concrete pasted evidence, run `aw ipd lint --phase pre-transition`. The terminal transition then happens through the tooled lifecycle, which moves this plan to `.aw/records/plans/executed/`: when the plan runs as a managed lane under `aw oc run` / `aw agy run`, the RUNNER owns `begin`/`finalize`, so leave the plan in `pending/` with its evidence recorded and say so; only when executing by hand outside a runner, run `aw ipd finalize pud8rp --actor <agent/model> --message <summary> --apply` yourself. Do not hand-edit the terminal state or `git mv` the plan. Scope fence: the two `Scope-Paths` entries are a declaration; an out-of-scope edit that proves necessary is made and then justified with `--scope-reason` at finalize, not a reason to stop. After execution (not before), backlog `tvv8gg` may be closed `done` with `--evidence` citing the executed plan; it carries no `- Blocks-Release:`.
