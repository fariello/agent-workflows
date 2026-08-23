# IPD: Remove raw terminal-transition bypasses and strengthen history lint

- Date: 2026-08-23
- Kind: child
- Concern: Even after `aw ipd finalize` exists (Orders 04/05), the raw `aw set executed` / `aw ipd set executed` plan-terminal path still works - it moves the plan and writes a generic `executed (aw set)` actor with no receipt, no scope comparison, and no captured gate evidence. That is the exact bypass that produced the p7dqwz false-fidelity record. Until it is removed and the history lint rejects generic-actor terminal entries, the gates are optional.
- Scope: Make raw plan-to-terminal transitions refuse and point to `aw ipd finalize`, and strengthen post-transition history lint. Touch: agent_workflows/status_set.py (refuse plan `executed`/terminal transitions, preserve nonterminal plan transitions and non-plan artifact terminal transitions), agent_workflows/cli.py (the `set`/`ipd set` routing + help), agent_workflows/ipd_lint.py (post-transition: require a non-generic actor/model + nonempty summary), and tests/test_status_set.py + tests/test_ipd_lint.py + tests/test_ipd_lifecycle_cli.py. Does NOT build begin/finalize (Orders 03/04) - it depends on them existing.
- Status: draft
- Set: ipdgates
- Order: 6
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: wezhxg

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (decomposition of 39fz2x E-05).

## Goal

Close the raw terminal-transition bypass so no public CLI path can move an IPD to `executed` without the begin receipt, scope comparison, three lint gates, attributed history, and lifecycle commit. Make `aw set executed`, `aw ipd set executed`, and equivalent plan terminal aliases REFUSE a direct plan-to-terminal transition and point the operator to `aw ipd finalize`, while PRESERVING nonterminal plan transitions (draft/to-review/reviewed/approved) and non-plan artifact status changes (specs/backlog/etc). Strengthen post-transition lint so an executed plan history entry MUST identify a non-generic actor/model and a nonempty summary, rejecting `executed (aw set): ...`-style entries.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Refuse the raw plan-terminal transition

- [ ] E-01 In `status_set.py` (and the `cli.py` `set`/`ipd set` routing), make a request to move a PLAN to a terminal status (`executed`, and any terminal plan alias) REFUSE with a clear message pointing to `aw ipd finalize <plan>`; PRESERVE nonterminal plan transitions (draft/to-review/reviewed/approved) and PRESERVE non-plan artifact terminal transitions (specs/backlog/prompts/etc). No expert escape hatch (39fz2x OQ-02: none) - recovery from a broken finalizer is STOP-and-report or a separately-documented repair path that cannot claim a successful execution.
  - Depends on: none
  - Expected outcome: `aw set executed <plan>` / `aw ipd set executed <plan>` refuse and redirect to `aw ipd finalize`; other transitions are unchanged.
  - Execution state: pending

### Task group 2: Strengthen attribution lint

- [ ] E-02 Strengthen post-transition lint in `ipd_lint.py`: an `executed` plan's `## Workflow history` MUST have a terminal entry whose actor is a non-generic agent/model identifier (reject `aw set`, empty, or a placeholder) AND a nonempty summary. A generic or empty actor/summary is a post-transition conformance error. (Grandfather already-executed terminal records so this does not retroactively fail the existing executed tree; apply the stricter rule to transitions performed after this ships, consistent with Order 02's cutoff.)
  - Depends on: none
  - Expected outcome: post-transition lint rejects generic-actor/empty-summary terminal entries going forward without failing the grandfathered executed tree.
  - Execution state: pending

### Task group 3: Prove no bypass and compatibility

- [ ] E-03 Add tests: (`tests/test_status_set.py` / `tests/test_ipd_lifecycle_cli.py`) every raw plan-to-terminal alias refuses with a single `aw ipd finalize` next action, while nonterminal plan transitions and non-plan terminal transitions retain behavior; (`tests/test_ipd_lint.py`) post-transition lint rejects a generic/empty actor/summary and accepts a real agent/model + summary, and does not fail a grandfathered pre-cutoff executed record; and CLI help/workflow docs advertise no bypass. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02
  - Expected outcome: no public CLI path reaches plan `executed` except via `aw ipd finalize`, compatibility for other transitions is proven, and attribution lint is enforced forward without retroactive breakage.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `status_set.py` currently accepts plan `executed`, writes/moves the file, auto-refreshes indexes, and swallows index exceptions (`status_set.py:580,617`); it is the exact bypass. The p7dqwz executed record carries `- 2026-08-23 executed (aw set): status set to executed`.
- `aw set` is untyped (transitions plans/specs/prompts/backlog); only the PLAN terminal transition is being removed - the others stay.
- 39fz2x OQ-02 (human-inherited): no raw terminal escape hatch.
- Depends on `aw ipd finalize` (Orders 04/05) existing, since the refusal message and the only-supported path point at it.

## Findings

Removing the bypass is what makes the gates mandatory rather than optional. It must be surgical: only the plan-to-terminal transition is removed; nonterminal plan transitions and all non-plan artifact transitions are load-bearing and must be preserved. The attribution lint prevents a future generic-actor terminal entry from recurring, but must grandfather the existing executed tree to avoid mass retroactive failure.

## Proposed changes (ordered, validatable)

1. Refuse raw plan-to-terminal transitions, redirect to `aw ipd finalize`, preserve all other transitions (E-01).
2. Strengthen post-transition attribution lint (non-generic actor + nonempty summary), grandfathering existing executed records (E-02).
3. Prove no-bypass + compatibility + attribution-lint-forward-only (E-03).

## Deferred / out of scope (with reason)

- Building begin/finalize: Orders 03/04 (dependencies).
- General git policy outside IPD terminal transitions: out of scope.

## Scope check

- Over-scope: none.
- Under-scope: none; bypass removal, attribution lint, and compatibility/no-bypass tests are included.

## Required tests / validation

- `tests/test_status_set.py`, `tests/test_ipd_lint.py`, `tests/test_ipd_lifecycle_cli.py` per E-03.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Update the IPD lifecycle spec + workflow doc + `.aw/records/plans/README.md` + `CONTRIBUTING.md` + CLI help (via managed verbs) so terminal transition is documented ONLY as `aw ipd finalize` and no bypass is advertised.

## Open questions

### OQ-01: Is the attribution-lint stricter rule forward-only (grandfather the existing executed tree) or repo-wide?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO (human). The existing executed tree contains records with generic actors (e.g. p7dqwz's `executed (aw set)`). Options: (A) forward-only - apply the stricter actor/summary rule only to transitions after this ships, grandfathering existing executed records (consistent with Order 02's cutoff; no mass retroactive lint failure); (B) repo-wide - fail lint on ANY executed record with a generic actor, forcing a cleanup of historical records (large retroactive churn, and terminal records are supposed to be immutable). (A) is strongly preferred and consistent with the immutable-terminal-record convention; the executor MUST confirm before E-02.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: tests show `aw set executed <plan>` and `aw ipd set executed <plan>` refuse with a single `aw ipd finalize` next action; nonterminal plan transitions (draft/to-review/reviewed/approved) and non-plan artifact terminal transitions still succeed unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: post-transition lint rejects a generic (`aw set`) or empty actor and an empty summary, and accepts a real agent/model + nonempty summary; per OQ-01's resolution it does NOT fail a grandfathered pre-cutoff executed record.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the no-bypass, compatibility, and attribution tests pass; CLI help/workflow docs advertise no bypass; `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - remove the raw plan-terminal bypass and enforce attributed terminal history, surgically preserving all other transitions.

### Execution contract

1. Open questions RESOLVED: OQ-01 (attribution lint forward-only vs repo-wide) MUST be resolved by a human before E-02.
2. Scope fence: touch ONLY `status_set.py`, `cli.py` (set/ipd set routing + help), `ipd_lint.py` (post-transition attribution), the three named test files, and the lifecycle doc/spec/README/CONTRIBUTING via managed verbs. Do NOT build begin/finalize. Preserve nonterminal plan transitions and non-plan artifact terminal transitions. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, transition via `aw ipd finalize` - append the `## Workflow history` line, set `Status: executed`, move the plan, path-scoped lifecycle commit - and if the finalizer cannot finalize this plan, STOP and report (never fall back to the raw transition this very plan just removed).
