# IPD: universal selectors and multi-target and aw show id6 resolution

- Date: 2026-08-18
- Kind: orchestrator
- Concern: TODO items 16, 17, 18. Today action-taking verbs each hand-roll target resolution and only understand one namespace: `aw show pp6y76` (an id6 handle for a RECORDS artifact) FAILS with "Action 'pp6y76' not found" because `_run_show` (cli.py:3514) -> `ActionManager.find_action_file` (actions.py:136) globs ONLY the STATE action ledger `<STATE>/actions/{open,...}/<id>-v*.md` and has no awareness of the records id6 namespace under `.aw/records/{plans,specs,research,backlog,...}` (#16, plus the confusing "Action ID or ID@generation" help). There is no shared way to name a plan/spec/prompt/etc. by id6, setid, full/partial filename, or STATUS, and no verb accepts MORE THAN ONE target (#17), nor status-based selection where it would be natural (#18).
- Scope: Ship ONE shared SELECTOR grammar module that resolves, for a given record TYPE, one-or-more tokens - each token an id6 (artifact_core.ID6_RE, artifact_core.py:39), a setid, a full/partial filename (via the clustered grammar plans_refs._CLUSTERED_RE, plans_refs.py:47), or a STATUS - to the matching record path(s), accepting MULTIPLE selectors OR-combined; and consume it to (a) fix `aw show` to also resolve a records id6/filename by routing to the records resolver (not only the action ledger) and clarify the "ID@generation" help, and (b) enable status-based selection across verbs (#18). IN: the resolver module + tests; the `aw show` routing fix + help clarification; the status-selection plumbing. OUT: the noun-verb command grammar and per-verb wiring (Set A / awcmdsurf, which DEPENDS ON this Set's resolver); the `check` engine (Set D / awcheck); help-text quality (Set B); color/pretty (Set C). This Set provides the shared selector primitive; awcmdsurf's verbs are its first consumers.
- Status: reviewed
- Set: awselect
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 1qe40j

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): high-level skeleton from TODO items 16,17,18 (shared selector grammar consumed by awcmdsurf); children to be fleshed out.
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Orchestrator for selectors; child decomposition (selector module -> aw show fix) sound; cross-Set dependency (awcmdsurf consumes the selector) truthfully stated; no phantom-verb evidence. No findings.

## Goal

Provide a single shared SELECTOR grammar so that any action on a plan/spec/prompt/etc. can name its
target(s) uniformly - by id6, setid, full/partial filename, or status - and accept more than one target
(#17, #18), and fix `aw show` so an id6 like `pp6y76` resolves to its RECORDS artifact instead of failing
in the action-ledger-only lookup (#16). This selector primitive is the dependency the awcmdsurf verbs
consume, so one resolver replaces every verb hand-rolling its own target resolution.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..02 through the IPD lifecycle in dependency order (author -> /plan-review -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing; Order 01 ships the shared selector resolver module, Order 02 fixes `aw show` id6/filename resolution and the "ID@generation" help plus status-based selection; on completion confirm the resolver is the single primitive the awcmdsurf verbs consume.
  - Depends on: none
  - Expected outcome: Orders 01..02 executed; a shared selector resolver resolves id6|setid|partial-filename|status to record path(s) with multi-selector OR; `aw show pp6y76` resolves the records artifact; status-based selection available across verbs.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Split by concern: Order 01 builds the shared selector PRIMITIVE (no verb wiring); Order 02 CONSUMES it
to fix `aw show` and enable status selection. Order 02 depends on Order 01 so it routes through the real
resolver rather than a placeholder.

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | awselect-selector-grammar (to scaffold) | Shared selector resolver module: given a record TYPE + one-or-more tokens, resolve each token as id6 (artifact_core.ID6_RE) \| setid \| partial/full filename (plans_refs._CLUSTERED_RE groups) \| status, and return the matching record path(s); accept MULTIPLE selectors OR-combined; reuse the existing finders (plans_index.run_find:346, research_index.run_find:307) and front-matter `- Id:` scan. + tests. This is the primitive the awcmdsurf verbs consume. | none |
| 02 | awselect-show-and-status (to scaffold) | Fix `aw show` (cli.py:3514 `_run_show`) to resolve a records id6/filename by routing to the records resolver (not only `ActionManager.find_action_file`, actions.py:136), so `aw show pp6y76` finds its RECORDS artifact; clarify the confusing "Action ID or ID@generation" help (#16); enable STATUS-based selection across verbs (#18) via the Order 01 resolver. + tests. | 01 |

## Completion criteria (the whole Set is done only when)

- Orders 01..02 both executed.
- The shared selector resolver resolves id6, setid, partial/full filename, and status to matching record
  path(s) for a given TYPE, and accepts more than one selector (OR-combined) where not nonsensical (#17).
- `aw show <id6>` (e.g. `aw show pp6y76`) resolves the RECORDS artifact instead of failing in the
  action-ledger-only lookup; the "ID@generation" help reads unambiguously (#16).
- Status-based selection is available wherever it is logical across verbs (#18).
- The resolver is the single shared primitive the awcmdsurf verbs consume (no per-verb hand-rolled
  resolution).
- Full serial suite green; the relevant `--check`s + `aw sanitize --agent` clean.

## Cross-IPD validation

- Order 01 (resolver primitive) MUST precede Order 02 (`aw show` + status selection consumer) so the
  consumer routes through the real resolver.
- Set A / awcmdsurf DEPENDS ON this Set: its cross-cutting verbs (find/search/index/rename/group/archive
  over a TYPE noun + selectors) consume THIS Set's selector resolver. The resolver's TYPE + token contract
  must land before awcmdsurf wires the verbs to it; keep the resolver signature stable and re-run the full
  check suite after each Order so awcmdsurf builds on a settled primitive.

## Deferred / out of scope (with reason)

- The noun-verb command grammar and per-verb argument wiring: Set A / awcmdsurf (this Set only ships the
  selector primitive it consumes).
- The `check` engine internals: Set D / awcheck.
- Help-text quality overhaul: Set B / awhelp (this Set only clarifies the one "ID@generation" string).
- Color/pretty output: Set C / awcolor.

## Scope check

- Over-scope: none - this Set is the selector primitive plus the `aw show`/status consumer only; verb
  wiring is explicitly awcmdsurf.
- Under-scope: none - Order 01 covers all four token kinds (id6, setid, partial filename, status) with
  multi-selector OR; Order 02 covers the `aw show` id6/filename fix, the help clarification (#16), and
  status-based selection (#18).

## Required tests / validation

Per-Order V-items plus the whole-Set completion criteria above; the orchestrator's E-01 verification
re-runs the full serial suite and confirms `aw show <id6>` resolves a records artifact, multi-selector +
status resolution work, and the relevant `--check`s + `aw sanitize --agent` are clean.

## Open questions

### OQ-01: When a single token is ambiguous (matches both a STATE action id and a RECORDS id6), which namespace wins, and does a partial-filename match that hits multiple records error or return all?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: To be resolved at Order 01/02 authoring. Default lean: try the
  records id6 namespace as an additive fallback so `aw show pp6y76` starts working without regressing
  existing action-ledger lookups; a partial-filename match with multiple hits returns all paths (OR
  semantics, consistent with multi-target #17) unless the verb is inherently single-target, in which case
  it errors and lists the candidates.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: both child Orders 01-02 show `Status: executed` under `.aw/records/plans/executed/`; paste demonstrations of the whole-Set completion criteria - the shared resolver returning matching path(s) for an id6, a setid, a partial filename, and a status (incl. a multi-selector OR call returning multiple paths); `aw show pp6y76` (or another real records id6) resolving its RECORDS artifact where it previously errored; the clarified "ID@generation" help string; a status-based selection working through a verb; and the full serial suite output + relevant `--check`s + `aw sanitize --agent` clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: two Orders for one coherent objective (a shared selector primitive and its first `aw show`/status consumer), split by concern - Order 01 builds the resolver, Order 02 consumes it - so each is independently reviewable/executable while keeping the primitive settled before awcmdsurf builds on it.

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The orchestrator
(opencode Opus 4.8) drives each child Order through its own lifecycle, owns all verification + path-scoped
commits (`git commit -m msg -- <path>`, never `git add -A`/`-a`), never pushes, and moves each Order (and
finally this orchestrator) to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition`
conforms and the V-items are verified with pasted evidence. Delegation to Gemini via `agy` is permitted for
sub-tasks; the orchestrator remains accountable for verification and the lifecycle transition. Any
tag/publish is Section 9, human-gated.
