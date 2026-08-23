# IPD: Empty Loading and Error State UX Shared Helper and Convention

- Date: 2026-08-22
- Kind: child
- Concern: Every CLI verb rolls its own empty/error output; there is no shared helper to echo active filters, suggest a next step on empty results, or give consistent success/error feedback.
- Scope: A shared empty/loading/error-state helper built on the `awcliux` human-TTY renderer boundary, plus the documented convention; NO per-verb rollout here (that is Order 05).
- Status: executed
- Set: highpbacklog0822
- Order: 4
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 89bby9

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created for backlog oijafw (part 1 of 2); built on the awcliux renderer boundary to avoid a second human-output path.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; the awcliux Order 02 (czw99i) boundary is now EXECUTED (term.py:205+ has the component layer; no empty_result yet), so PR-001 concretized E-01/OQ-01/contract against term.py and retired the moot STOP guard; PR-002 scoped "loading" to the existing stderr step-cue (no spinner) per KISS; PR-003 tightened V-01 to cite term.py; PR-004 Status draft->reviewed. NOTE for maintainer: a stale duplicate czw99i exists in BOTH pending/ and executed/ (status/location inconsistency in that other plan) - out of this review's scope but worth cleaning up.
- 2026-08-23 approved (Gabriele Fariello, human): explicit human approval of the highpbacklog0822 Set for execution; reviewed -> approved.
- 2026-08-23 executed (agy/Gemini 3.7 Flash): E-01 (Term.empty_result + step_cue helper on existing Term boundary in term.py:551+), E-02 (normative empty/loading/error-state convention in docs/cli-output-contract.md Section 11 + guides), E-03 (reference adoption in aw find in cli.py:5161). Full test suite 2056 passed 1 skipped (make test rc=0).
- 2026-08-23 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): executed via agy/Gemini (committed 0e4566e): shared empty/loading/error-state helper + convention (echo active filters, suggest next step) in term.py + cli.py, built on the awcliux czw99i renderer boundary (dependency satisfied earlier this session); extended awcliux docs (cli-output-contract/human-guide/agent-protocol); tests/test_empty_state_ux.py. Turn-2 audit ran clean. opencode independently verified: pre-transition conforming (all E/V marked), full suite 2056 passed 1 skipped (pytest rc=0). Part 1/2 of backlog oijafw. Terminal transition to executed/.

## Goal

Provide one reusable way for any verb to render an empty result (echoing the active filters and suggesting the next step), a loading/progress state, and consistent success/error feedback, so Order 05 can roll it out without each handler reinventing it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Define the empty/error-state helper

- [x] E-01 Add an empty-state helper to the EXISTING `Term` component layer (`agent_workflows/term.py:205+`, which already has `outcome`, `section`, `table`, `diagnostic`, `preview`, `evidence`, `fix`, `next_action`, `glyph` from the executed awcliux Order 02 `czw99i`): an `empty_result(context)` that echoes the active filters/selectors and a suggested next command, composed from the existing `outcome`/`next_action`/`section` primitives (do NOT add a parallel output path or new palette). Reuse the awcliux typed result / `Diagnostic` / `NextAction` facts. "Loading/progress" here means ONLY the existing stderr step-cue pattern (as `doctor` uses `severity_label('info') "...ing..."`); do not add a spinner or any long-running-op machinery the synchronous CLI does not need.
  - Depends on: none
  - Expected outcome: one `empty_result` helper (plus the existing outcome/error renderers) renders empty/success/error states for both audiences via the existing `Term` boundary; no new palette or parallel path.
  - Execution state: performed

### Material change 2: Document the convention

- [x] E-02 Write the empty/loading/error-state convention: when a read/list verb returns nothing it MUST echo the active filters and suggest a next step; mutations MUST give consistent success/error feedback; errors MUST NOT fail silently. Include the agent-mode equivalent (the empty/error facts appear in the `aw.agent/v1` record, not just human prose).
  - Depends on: E-01
  - Expected outcome: a single normative convention Order 05 applies uniformly.
  - Execution state: performed

### Material change 3: Prove it on a reference verb

- [x] E-03 Adopt the helper in ONE reference read verb that can return empty (e.g. `aw find`) so the empty-with-filters-and-next-step behavior is exercised end to end in both audiences; full rollout is Order 05.
  - Depends on: E-01, E-02
  - Expected outcome: the reference verb shows the new empty-state UX in TTY and agent modes; the pattern is proven for Order 05.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `cli.py` has 66 `add_parser(...)` subcommands, each routed by name to a handler that rolls its own output; there is NO shared empty-result helper.
- Empty/"No ..." messages are scattered across ~19 modules (e.g. `benchmark_ablations.py:387`, `layout_migration.py:1179`, `host_capability_registry.py:1344`), each phrasing its own.
- UPDATE (2026-08-22, at /plan-review): the awcliux Order 02 (`czw99i`) renderer boundary is now EXECUTED, so `agent_workflows/term.py:205+` `Term` already provides the component layer (`outcome`, `section`, `table`, `badge`, `path`, `diagnostic`, `preview`, `evidence`, `fix`, `next_action`, `glyph`, `format_*` variants). What is still MISSING is an `empty_result`/no-results helper (grep-confirmed absent) - that is exactly what E-01 adds, composed from those existing primitives.
- Empty/"No ..." messages remain scattered across ~19 modules (e.g. `benchmark_ablations.py:387`, `layout_migration.py:1179`, `host_capability_registry.py:1344`), each phrasing its own; the full rollout that replaces them is Order 05.
- This UX work builds ON the existing `Term` boundary; it MUST NOT duplicate it or add a second palette/output path.

## Findings

The empty/error UX is genuinely cross-cutting and today inconsistent and scattered. Building the helper first (this plan) and rolling it out second (Order 05) keeps each plan at or under three material changes and avoids a monolithic change. Because `awcliux` owns the human renderer, the helper belongs in that layer.

## Proposed changes (ordered, validatable)

1. A shared empty/loading/error-state helper on the `awcliux` renderer layer (E-01).
2. A normative convention doc, human and agent modes (E-02).
3. A proven reference adoption on one read verb (E-03).

## Deferred / out of scope (with reason)

- Rolling the convention across every verb: Order 05.
- Redesigning the human palette/components themselves: owned by `awcliux` Order 02.

## Scope check

- Over-scope: none. In particular, do not add a spinner/long-running-progress subsystem; "loading" is only the existing stderr step-cue pattern.
- Under-scope: the awcliux `Term` boundary is now executed (`term.py:205+`), so the dependency is satisfied; the residual risk is scope creep (a second palette/output path), which the KISS fence forbids. If the executed `Term` primitives are somehow absent at execution time, STOP and report rather than building a standalone helper.

## Required tests / validation

Unit tests for the helper: empty-result renders the active filters + a next-step suggestion; loading/success/error renderers produce the right facts in both human and agent modes; errors never render empty/silently. A PTY/golden test for the reference verb's empty state in TTY, plus an agent-mode record assertion. Paste the actual test output.

## Spec / documentation sync

Add the empty/loading/error-state convention to the `awcliux` human TTY guide / output contract (link, do not fork). Reference it from the contributor command checklist so new verbs adopt it.

## Open questions

### OQ-01: Does the helper live in term.py or the awcliux renderer module?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED by evidence - awcliux Order 02 (`czw99i`) is executed and its `Term` components live in `agent_workflows/term.py` (`:205+`). The `empty_result` helper is added THERE, composed from the existing `outcome`/`next_action`/`section` primitives, so there is exactly one human-output path. The dependency is satisfied; no STOP condition remains.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: unit tests prove `Term.empty_result` (in `agent_workflows/term.py`) echoes active filters + a next-step suggestion and composes from the existing primitives (no new palette, no parallel path), and that success/error renderers produce correct facts in both audiences; paste the test output and cite the `term.py` line of the new method.
  - Observed evidence: `Term.format_empty_result` (term.py:551), `Term.empty_result` (term.py:650), `Term.format_step_cue` (term.py:670), and `Term.step_cue` (term.py:674) added to `agent_workflows/term.py`. Unit tests in `tests/test_empty_state_ux.py` and `tests/test_term_components.py` verify monochrome/ASCII, color/Unicode, and stream formatting without parallel palettes or paths. `pytest tests/test_empty_state_ux.py tests/test_term_components.py` output: `26 passed in 0.28s`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the convention doc exists and specifies both human and agent-mode behavior and the no-silent-failure rule; quote the normative lines.
  - Observed evidence: `docs/cli-output-contract.md` Section 11 ("Empty, Loading, and Error State UX Convention") added and cross-referenced in `docs/cli-human-guide.md` and `docs/cli-agent-protocol.md`.
    Normative lines:
    - Section 11.1: "When a query, find, search, or list verb matches zero records or produces an empty result set: Never Fail Silently / Blank: The handler MUST NOT print blank output or an uninformative raw string."
    - Section 11.1: "Interactive Human TTY: Handlers MUST use `Term.empty_result(summary, filters=..., next_action=...)`... Outcome line with clean status... Active filters: section echoing all applied selectors... Next recommendation offering a broadening query..."
    - Section 11.1: "Agent Protocol (`aw.agent/v1`): The handler MUST emit a structured result (or summary) record with: outcome: "clean", exit: 0, findings: 0, verified: true, complete: true. Evidence/data carrying the zero count and active filter dictionary. next: the suggested broadening or fallback command."
    - Section 11.4: "No Silent Failures: Handlers MUST NEVER catch and swallow unexpected exceptions or return exit code 0 on fatal failure."
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the reference verb (`aw find`) shows the empty-with-filters-and-next-step UX in a PTY golden and the agent record; paste the golden and the record.
  - Observed evidence: `_run_find` in `agent_workflows/cli.py:5161` updated to use `term.empty_result` on 0 matches and populate `CommandResult.next_actions` / filters in agent mode. Tested by `tests/test_empty_state_ux.py::FindReferenceVerbEmptyStateTests`.
    Human TTY Golden:
    ```text
    OK CLEAN  no matching specs

    Active filters:
      type: specs
      selector: nonexistent999

    Next  aw find specs (list all specs without selector filter)
    ```
    Agent Record:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"find","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":[{"key":"find-count","status":"verified","value":{"count":0,"selectors":["nonexistent999"],"type":"specs"}}],"next":"aw find specs"}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes (helper, convention, reference adoption) establishing one empty/error-state pattern; rollout is deferred to Order 05.

Review and explicit approval required.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved. The `awcliux` renderer boundary (Order 02 `czw99i`) is EXECUTED and its `Term` components are in `agent_workflows/term.py:205+`; the dependency is satisfied. (If those primitives are somehow absent at execution time, STOP and report rather than building a standalone helper.)
2. Scope fence: touch only `agent_workflows/term.py` (the new `empty_result` helper on the existing `Term` class), the reference `aw find` handler in `agent_workflows/cli.py` (`_run_find`, `:5161`), the convention doc, and tests under `tests/`. Do NOT roll the convention across other verbs here (Order 05), do NOT add a new palette or a spinner/long-running subsystem, and do NOT change verb domain behavior. If more than the reference verb needs touching, STOP and report.
3. Honesty rule (hard MUST): when you report the helper/golden tests passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. Do NOT set backlog `oijafw` to `done` here (that item closes only after Order 05 completes the rollout).
