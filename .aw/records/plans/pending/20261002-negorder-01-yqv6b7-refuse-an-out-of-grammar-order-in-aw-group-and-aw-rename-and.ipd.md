# IPD: Refuse an out-of-grammar --order in aw group and aw rename, and make the Order substitution regex fail safe instead of silently duplicating the field

- Date: 2026-10-02
- Kind: child
- Concern: Backlog `bmhoxe` measured that `aw group plans <id6> --set <s> --order -1 --rename --apply` and `aw rename plans --id <id6> --order -1 --apply` both exit 0 and corrupt the plan twice: the front matter gains a SECOND `- Order: -1` line (so `aw ipd lint` reports `IPD-M102: Order: duplicate field`), and the file is renamed with a double hyphen where the two-digit `NN` facet belongs (`20260920-negset--1-hhh888-orch.ipd.md`). A later repair with `--order 0` folds the broken prefix into the slug (`...-negset-00-hhh888-negset-1-orch.ipd.md`). Cause, read in code: `plans_refs._ORDER_LINE_RE` is `(?m)^- Order:\s*(\d+)\s*$`, which cannot match a minus sign, so `plans_refs._set_metadata`'s substitution finds nothing, its early-return guard is False, and the insertion branch appends a second `- Order:` line; the name builder formats the order into the `NN` facet without a range check. The existing Kind-conditional refusal (`plans_refs._validate_plan_order`, executed plan `qhcojn`) only fires for `Kind: child`, so a plan with no `- Kind:` line is not protected, and 102 plans in this tree carry none.
- Scope: IN: an unconditional range check on the RESOLVED order, per plan, at both write sites (`plans_refs.plan_set_assign` for `aw group plans`, and the `aw rename plans` path in `plans_refs` that resolves `order` before calling `_validate_plan_order`), refusing a value outside 0 to 99 with exit 2 and nothing written, and NOT overridable by `--allow-invalid-order` (that flag overrides the Kind rule, not the grammar); make `_set_metadata` fail safe by widening `_ORDER_LINE_RE` to `-?\d+` and asserting the result carries exactly one `- Order:` line; apply the same widening to `artifact_rename._ORDER_LINE_RE`, its twin; a regression test. OUT: the Kind-conditional rule (`qhcojn`, executed; `xvi55d`, pending); repairing existing plans (the corpus is clean, re-measured at execution); any other verb.
- Scope-Paths: agent_workflows/plans_refs.py, agent_workflows/artifact_rename.py, tests/test_plans_order_grammar.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: low
- From-Backlog: bmhoxe
- Blocks-Release: next
- Set: negorder
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: yqv6b7

## Workflow history
- 2026-10-07 /plan-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004 (all fixed; record `.aw/records/reviews/20261007-negorder-01-yqv6b7-refuse-an-out-of-grammar-order-in-aw-group-and-aw-rename-and.review.md`)
- 2026-10-07 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed
- 2026-10-07 to-review (aw set): authored from backlog bmhoxe; all placeholders replaced, lints conforming

- 2026-10-06 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored the plan body from backlog `bmhoxe`, whose measurements and proposed fix are complete; every placeholder replaced. The item's "IF BUILT" section is the design; the range 0 to 99 is the two-digit `NN` facet the uniform naming grammar defines.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw group plans` and `aw rename plans` refuse any resolved Order that the filename grammar cannot hold, before writing anything, on every plan whether or not it declares a Kind; and make the Order rewrite unable to leave two `- Order:` lines in a file.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: refuse an out-of-grammar order

- [ ] E-01 Add `plans_refs._order_grammar_error(order) -> Optional[str]` returning a message when `order` is not an integer in 0 to 99 inclusive (the two-digit `NN` facet), naming the value and the allowed range. Call it in `plan_set_assign` on each plan's RESOLVED order (`start_order + i`, or the preserved order) BEFORE `_validate_plan_order`, returning `(None, err)` so the caller exits 2 with nothing written. Do not let `allow_invalid_order` bypass it.
  - Depends on: none
  - Expected outcome: `aw group plans <id6> --set s --order -1 --apply` exits 2, prints the range error, and leaves the file byte-identical; the same command WITHOUT `--apply` (preview) also exits 2, since `plan_set_assign` runs before `apply_renames`; `--order 99` on two plans resolves 99 then 100, refuses the second, and writes nothing for either (the whole batch is planned before any write, so an early `(None, err)` leaves both files untouched); `--order 98` on two plans (98, 99) succeeds.
  - Execution state: pending

- [ ] E-02 Call the same check on the `aw rename plans` path in `plans_refs` after `order` is resolved (from `--order`, the front matter, or the filename) and before `_validate_plan_order`, returning exit 2 with nothing written; again not overridable by `--allow-invalid-order`.
  - Depends on: E-01
  - Expected outcome: `aw rename plans --id <id6> --order -1 --apply` exits 2 with the range error and the file unchanged; a plan with no `- Kind:` line is refused the same way.
  - Execution state: pending

### Task group 2: make the rewrite fail safe

- [ ] E-03 Widen `_ORDER_LINE_RE` in `plans_refs` and `artifact_rename` to `(?m)^- Order:\s*(-?\d+)\s*$`, and in `plans_refs._set_metadata` assert after the rewrite that the text contains exactly one line matching `^- Order:` (raise a `ValueError` naming the plan otherwise). CORRECTED AT REVIEW: no caller turns that `ValueError` into a refusal today. `plans_refs.apply_renames` calls `_set_metadata` with no `try`, then `_core.atomic_write` and `_core.git_mv`, plan by plan, so a raise on plan 2 of a batch would surface as a traceback AFTER plan 1 was rewritten and moved. So ALSO: in `apply_renames`, compute every plan's new text in a first pass BEFORE any write or `git_mv`, and catch `ValueError` in `run_set_assign` and `run_mv` around `apply_renames`, printing `error: <message>` and returning `MutationResult(2)`. With E-01/E-02 in place this branch is a backstop unreachable from the CLI on valid input, which is why the test drives `_set_metadata` directly to reach it. Check every reader of `_ORDER_LINE_RE` (`_preserved_order`, the rename path's `om`, `artifact_rename`'s two uses) still behaves for a non-negative value, and record each in the evidence.
  - Depends on: E-02
  - Expected outcome: `_set_metadata` on a text with `- Order: -1` substitutes in place and never inserts a second line; a text carrying an Order line the widened regex still cannot match (for example `- Order: x1`) raises rather than writing a duplicate; and a raise inside `apply_renames` leaves every plan in the batch byte-identical and unmoved, reported as exit 2 by both verbs.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_plans_order_grammar.py` driving `python -m agent_workflows group plans` and `rename plans` as subprocesses in a temporary repository seeded with `--records-backend repository`, covering: negative order on a Kind-less plan and on a `Kind: child` plan, both verbs; 99 allowed and 100 refused; `--allow-invalid-order` not bypassing the range check; file bytes unchanged after every refusal; `aw ipd lint` on the plan reporting no `IPD-M102` after each case; and the bmhoxe repair sequence (`--order 0` after a refused `-1`) leaving a well-formed name. Prove the test can fail with TWO mutations, each reverted: (M1) remove the E-01/E-02 range-check calls ONLY, and paste the failure, which with E-03's widened regex in place is the exit-0 and malformed `--1` filename assertion, NOT a duplicate field (the widened substitution now matches `-1` in place); (M2) remove the range-check calls AND restore the old `(\d+)` regex, and paste the `IPD-M102` duplicate-field failure, which is bmhoxe's original corruption.
  - Depends on: E-03
  - Expected outcome: the new file passes; M1 fails on the exit code and filename, M2 reproduces bmhoxe's duplicate-field corruption and fails it; `tests/test_group_verb_policy.py` and `tests/test_plans_group_order_preservation.py` still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE KIND RULE IS A SEPARATE CHECK. `plans_refs._validate_plan_order` (executed plan `qhcojn`) consults `ipd_schema.validate_metadata` only for `Kind: child`; pending plan `xvi55d` adds the orchestrator half. The grammar check here is unconditional and runs first, so it does not depend on either.
- `--allow-invalid-order` OVERRIDES THE KIND RULE ONLY. Its message reads "pass --allow-invalid-order to override" next to a Kind finding; an out-of-grammar order can never produce a valid filename, so overriding it would always corrupt.
- ORDER IS RESOLVED PER PLAN: `plan_set_assign` computes `start_order + i`, so the check must run on each resolved value, not on the flag (backlog `bmhoxe`, "Evaluate the RESOLVED order per plan").
- MEASURE WITH THE PACKAGE PINNED to the tree under test (`PYTHONPATH=<tree>`, `AW_NO_REEXEC=1`), and seed fixtures with `--records-backend repository`.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Both verbs corrupt on a negative order, exit 0. | backlog `bmhoxe` measurement at HEAD `ee1f2eff2`: `aw group plans hhh888 --set negset --order -1 --rename --apply` produced two `- Order: -1` lines and the name `20260920-negset--1-hhh888-orch.ipd.md`; `aw rename plans --id kkk555 --order -1 --apply` the same |
| F-02 | The regex cannot match a minus, so substitution misses and insertion duplicates. | `plans_refs._ORDER_LINE_RE` is `(?m)^- Order:\s*(\d+)\s*$`; `_set_metadata` substitutes, then returns early only if both lines match, else inserts after `- Id:` |
| F-03 | The Kind rule does not cover Kind-less plans. | `plans_refs._validate_plan_order` returns None unless `_read_kind(text) == ipd_schema.KIND_CHILD`; 102 plans carry no `- Kind:` (backlog `bmhoxe`) |
| F-04 | `artifact_rename` carries a twin regex with the same blind spot. | `artifact_rename._ORDER_LINE_RE` is the same pattern, used to rewrite and to match front-matter Order lines |
| F-05 | The corpus is clean, so nothing needs repair. | backlog `bmhoxe`: 0 of 1135 plan files carry a negative Order or a non-two-digit cluster facet; re-measure at execution |

## Proposed changes (ordered, validatable)

1. Unconditional 0 to 99 check on each resolved order in `aw group plans` (E-01) and `aw rename plans` (E-02), not overridable.
2. Widen both Order regexes and assert a single Order line after the rewrite (E-03).
3. Subprocess tests on both verbs with a mutation reproducing bmhoxe (E-04).

## Deferred / out of scope (with reason)

- THE ORCHESTRATOR HALF OF THE KIND RULE. Owned by pending plan `xvi55d`.
  - Carrier: xvi55d
- OTHER ARTIFACT TYPES' `aw group`/`aw rename`. They route through `artifact_rename`, whose regex E-03 widens; their name builder `compute_target_name` is not shown to accept an out-of-range order, and no measurement shows a defect there.
  - Carrier-Declined: not measured as broken; E-03's regex widening removes the shared duplicate-line trap

## Scope check

- Over-scope: none. Two production modules and one test file. The `apply_renames` pre-pass and the `ValueError` handling in `run_set_assign`/`run_mv` (added at review) are inside `plans_refs.py`, already declared.
- Under-scope: none known.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_plans_order_grammar.py tests/test_group_verb_policy.py tests/test_plans_group_order_preservation.py -q` pasted.
- Re-measure the corpus (no negative Order, no non-two-digit facet) and paste the counts.
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec edited. The uniform naming grammar (`YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md`, `NN` two digits) is already stated in `AGENTS.md` and `.aw/records/plans/README.md`; this plan makes the two verbs enforce it.

## Open questions

### OQ-01: Should Order 0 to 99 be enforced, or only non-negative?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: 0 to 99. The backlog item asks for non-negative, but the defect it measured is a value the `NN` facet cannot hold, and 100 has the same problem (a three-digit facet the grammar does not define). The upper bound costs nothing: the largest Order in the corpus is far below it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the `plan_set_assign` diff and the subprocess outputs for `--order -1` (exit 2, message, file unchanged by checksum) the same command without `--apply` (exit 2), the `--order 99` two-plan case (resolved 100 refused, nothing written for either, both checksums unchanged), and the `--order 98` two-plan case succeeding.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rename-path diff and the outputs for `--order -1` on a Kind-less plan and a `Kind: child` plan, and for `--order -1 --allow-invalid-order` still refused.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both regex diffs and the `_set_metadata` assertion; paste the unit result for a `- Order: -1` text (substituted, one line) and for the unmatchable-Order-line case (raises); paste the `apply_renames` first-pass diff and the `run_set_assign`/`run_mv` `ValueError` handling, plus a run showing a forced raise exits 2 with every plan in the batch unchanged by checksum and unmoved; list each other reader of the regex (`_preserved_order`, `run_mv`'s `om`, `artifact_rename`'s substitution and its line-match) with its checked behavior for a non-negative value.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test file passing with its count; mutation M1's failure (exit code/filename) and mutation M2's `IPD-M102` duplicate-field failure, each reverted; the two existing test files passing; the corpus re-measurement; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual output for every `V-*`. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`. Backlog `bmhoxe` carries `- Blocks-Release: next`, inherited here; it closes `done` only when this plan executes.
