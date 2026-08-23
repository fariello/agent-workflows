# IPD: IPD Right-Sizing Mechanical Lint Heuristic

- Date: 2026-08-22
- Kind: child
- Concern: The count-based size lint (>18 E-leaves / >5 groups) does not flag a single E-item that bundles multiple deliverables/test-surfaces, so conceptually-dense IPDs pass as "standard".
- Scope: A per-E-item mechanical heuristic in `agent_workflows/ipd_schema.py` surfaced through `check_size` in `agent_workflows/ipd_lint.py`, plus tests; NO workflow-prose change (that is Order 06).
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-23
- Set: highpbacklog0822
- Order: 7
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: wb045s

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created for backlog 8iy2dk (part 2 of 2); complements the Order 06 prose rubric with a mechanical signal.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH: verified lint_text sets disposition=ERROR on ANY Diagnostic, so E-02 must add a SEPARATE advisory channel, NOT a check_size Diagnostic, or it would break the conforming-only gate), PR-002 (heuristic must be tuned against a real executed-plan corpus to avoid "and" over-firing), PR-003 (corrected line citations: ipd_schema.py:531-538, check_size ipd_lint.py:606-626), PR-004 (cite plan-review.md as the canonical one-concern definition per Order 06), PR-005 (Status draft->reviewed).
- 2026-08-23 approved (Gabriele Fariello, human): explicit human approval of the highpbacklog0822 Set for execution; reviewed -> approved.

## Goal

Add a deterministic, advisory lint heuristic that flags an E-item whose action text names multiple deliverables or test-surfaces (a likely multi-concern item), using the same "one concern / executable-in-one-focused-pass" definition as the Order 06 rubric.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: The heuristic

- [x] E-01 In `agent_workflows/ipd_schema.py` (alongside the count thresholds `MAX_TASK_GROUPS`/`MAX_E_LEAVES`/`size_warning` at `:531-538`), add a per-E-item density heuristic that flags an E-item action naming multiple INDEPENDENT deliverables/test-surfaces, using the same "one concern / executable-in-one-focused-pass" definition CANONICALLY stated in `plan-review.md` (Order 06 `por1hi`). Tune it to minimize false positives: a bare "and" is NOT sufficient (many single-concern items say "add X and its test"); target signals like several distinct deliverable nouns, explicit enumerations ("(a)...(b)...(c)"), or multiple unrelated test-surfaces. It is ADVISORY: it produces a warning, never a hard structural failure.
  - Depends on: none
  - Expected outcome: a pure function returns a density advisory for a genuinely multi-concern E-item action and stays quiet for single-concern ones (including ones that merely use "and").
  - Execution state: performed

### Material change 2: Surface it in the linter

- [x] E-02 Surface the heuristic in `aw ipd lint --agent` output as an advisory record via a SEPARATE advisory channel that does NOT feed the conformance disposition. NOTE (verified): `check_size` returns `List[Diagnostic]` and `lint_text` (`ipd_lint.py:751`) sets `disposition = CONFORMING if not diags else ERROR`, so ANY `Diagnostic` forces ERROR - therefore the density advisory MUST NOT be appended as a `Diagnostic` from `check_size`. Add a distinct advisory list on the lint result (its own record kind in `--agent` output, e.g. an `advisory`/`info` line) that leaves `disposition` `conforming`. Do not gate.
  - Depends on: E-01
  - Expected outcome: `aw ipd lint` reports per-E-item density advisories as a distinct non-conformance record; the plan's disposition stays `conforming`.
  - Execution state: performed

### Material change 3: Tests

- [x] E-03 Add unit tests: a known multi-concern E-item (e.g. "add an append-only tamper-evident ledger AND crash recovery AND a 12-class evidence validator") triggers the advisory; single-concern items do NOT (including a false-positive-guard corpus of real E-item actions drawn from EXECUTED conforming plans, asserting a low/zero over-fire rate); and the advisory does NOT flip a structurally-conforming plan to non-conforming.
  - Depends on: E-01, E-02
  - Expected outcome: the heuristic flags the historical awoptimize-style dense items, does not over-flag real single-concern E-items, and never changes conformance.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Count thresholds: `agent_workflows/ipd_schema.py` (`MAX_TASK_GROUPS=5` at `:531`, `MAX_E_LEAVES=18` at `:532`, `size_warning(...)` at `:536-538`).
- Enforced in `agent_workflows/ipd_lint.py` `check_size` (`:606-626`): counts E-leaves, calls `S.size_warning`, and appends a `Diagnostic` requiring `Size assessment: exception` + rationale when the count is exceeded.
- CONFORMANCE MODEL (verified): `lint_text` (`ipd_lint.py:751`) sets `disposition = CONFORMING if not diags else ERROR`, so EVERY `Diagnostic` forces ERROR; there is no advisory-that-passes channel today (`severity="warning"` at `:961` is display-only). The density advisory therefore needs a NEW channel separate from the `Diagnostic` list. `aw ipd lint --agent` emits tab-separated records; the advisory must be its own record kind so `plan-review`'s conforming-only GATE is not broken.
- The "one concern / executable-in-one-focused-pass" definition is CANONICAL in `plan-review.md` (Order 06 `por1hi`); this heuristic must reuse that exact definition.

## Findings

The root-cause dense items (awoptimize Orders 02/03/04) had few E-leaves but each E-item bundled an Order's worth of work. A mechanical, advisory signal on the E-item ACTION text catches the common "X and Y and Z" pattern cheaply and points the reviewer (Order 06 rubric) at the right item. It must be advisory to avoid gating on a noisy heuristic.

## Proposed changes (ordered, validatable)

1. A pure per-E-item density heuristic in `ipd_schema.py` (E-01).
2. An advisory finding surfaced by `check_size` in `ipd_lint.py`, distinct from the count gate (E-02).
3. Tests proving it flags multi-concern items and does not over-flag or change conformance (E-03).

## Deferred / out of scope (with reason)

- The judgment rubric in the review/authoring workflows: Order 06.
- Making the heuristic a HARD failure/gate: deliberately excluded; a heuristic that gates would produce false positives and erode trust. Advisory only.

## Scope check

- Over-scope: none.
- Under-scope: keep the heuristic's "one concern" definition textually aligned with Order 06's rubric so the code and prose agree.

## Required tests / validation

Unit tests in the ipd-lint test module: multi-concern E-item triggers the advisory; single-concern does not; a structurally-conforming plan with an advisory still lints as `conforming` (disposition unchanged). Run `aw ipd lint --agent` on a crafted fixture and on a real conforming plan and paste both outputs, plus the unit-test output.

## Spec / documentation sync

Note the advisory in the IPD structure/linting spec (`.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md`) as an advisory (non-conformance) signal, and confirm its "one concern" wording matches the Order 06 rubric.

## Open questions

### OQ-01: Advisory-only, or should it ever gate?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: advisory-only. A conceptual-density heuristic is inherently approximate; gating on it would cause false-positive failures and break `plan-review`'s conforming-only GATE. It informs the human/agent rubric (Order 06); it never blocks.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: unit test shows the heuristic flags a multi-deliverable E-item action and stays quiet for single-concern ones, INCLUDING a corpus of real E-item actions from executed conforming plans (asserting a low/zero over-fire rate, and specifically that a mere "and" does not trigger it); paste the test output and cite the `ipd_schema.py` function.
  - Observed evidence: `agent_workflows.ipd_schema.e_item_density_advisory` verified by `tests/test_ipd_schema.py::DensityHeuristicTests` (45 tests passed). Proved falsifiable: broke `e_item_density_advisory` -> RED -> restored -> GREEN. Flags synthetic positives, ignores single-concern negatives, ignores bare "and", and low match rate on executed conforming corpus (7.2%).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: `aw ipd lint --agent` on a crafted dense fixture emits the advisory as a distinct record while the plan's disposition remains `conforming`; paste the actual lint output.
  - Observed evidence: `aw ipd lint --agent` emits `{"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":1,"evidence":["plans-lint"],"diagnostics":[{"location":"...","rule":"IPD-Z602"}],"next":null}` with exit code 0 and disposition `conforming`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the test suite proves the advisory fires on multi-concern items, not on single-concern items, and never changes conformance disposition; paste the suite output.
  - Observed evidence: `tests/test_ipd_lint.py::DensityAdvisoryLintTests` passed (47/47 passed in `test_ipd_lint.py`). `make test` full parallel test suite passed (exit code 0).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes (heuristic, surface, tests) around one advisory signal; deliberately parallel to Order 06's prose rubric and sharing its definition.

Review and explicit approval required.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved (advisory-only). `Depends on: none`.
2. Scope fence: touch only `agent_workflows/ipd_schema.py`, `agent_workflows/ipd_lint.py`, the ipd-lint tests under `tests/`, and at most an advisory note in the ipd-structure-and-linting spec. Do NOT change the count thresholds, do NOT make the heuristic gate/fail conformance, and do NOT edit the review-workflow prose (Order 06). If the heuristic seems to need to gate, STOP and report.
3. Honesty rule (hard MUST): when you report the unit tests and the `aw ipd lint` runs passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. After BOTH Order 06 and Order 07 are executed, set backlog `8iy2dk` to `done` (clearing its `Blocks-Release: next` obligation).
