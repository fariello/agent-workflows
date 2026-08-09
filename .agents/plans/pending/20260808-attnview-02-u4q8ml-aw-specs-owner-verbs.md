# IPD: aw specs owner verbs (Set attnview, Order 2)

- Date: 2026-08-08
- Kind: child
- Concern: give the specs tree a machine-legible status + history and the OWNER write verbs that maintain them, so status transitions and `## Workflow history` are made by a validating tool (not hand-edited prose), enforcing the transition/authority table (human token for `approved`, cited evidence for `implemented`) and typed gates.
- Scope: add `agent_workflows/specs.py` (or equivalent) providing `aw specs set`/`note`/`check`, wired as an `aw specs` namespace. Consumes the Order 01 contracts (status enum, transition/authority table, gate validators, history grammar, output safety). Does NOT build the cross-tree `aw attention` scanner (Order 03) and does NOT migrate the existing specs (Order 04). Requires Order 01 executed.
- Status: reviewed
- Set: attnview
- Order: 2
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: u4q8ml

## Workflow history

- 2026-08-08 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created. Child of Set `attnview`, authored from the approved spec Sections 7 (transitions/authority), 8.2 (owner verbs), 8.4 (gates), 8.8 (output safety); requires the Order 01 contracts.
- 2026-08-08 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. FIXED L2-01 (HIGH, security: enforce the anti-self-approval floor - `approved` mechanism must not be agent-satisfiable; V-03 asserts a no-TTY `set --status approved` is refused; do not assume flag names, consume the Order 01 frozen mechanism; escalate to Order 01 if its mechanism is hollow), L2-02 (state that `implemented` enforcement is presence + format + resolvability, not semantic verification), L2-03 (V-03 asserts the deferred gate add/remove round-trip + history-preserved resolution), L2-04 (V-03/V-04 assert no git index change after set/note). Status draft -> reviewed.

## Goal

Deliver `aw specs set`/`note`/`check`: `set` validates a requested transition against the frozen authority table, updates the spec `- Status:` and typed gate fields, appends exactly one `## Workflow history` record, validates the full result in memory, and atomically replaces the single file; `note` appends one history record only; `check` validates one spec (or all specs) against the contract. `approved` requires the human-approval token and is never settable by an agent; `implemented` requires cited implementation evidence. No writes stage/commit/push git.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: spec validation + the check verb

- [ ] E-01 implement spec contract validation in `agent_workflows/specs.py` reusing the Order 01 contracts: required bare-enum `- Status:`, the metadata grammar (no trailing prose on `- Status:`/`- Gate-*`), the `## Workflow history` grammar, the gate rules (gate fields required iff `deferred`, per-kind `Gate-Ref` validators, output-safety on descriptive fields).
  - Depends on: none
  - Expected outcome: a pure `validate_spec(path/text) -> [Drift]` covering every spec contract violation class.
  - Execution state: pending
- [ ] E-02 add `aw specs check [PATH]` (default all specs under `.agents/docs/specs/`) rendering the house `location<TAB>rule<TAB>detail` via `artifact_core.render_agent_drift`, exit `drift_exit_code` (0/1; 2 could-not-run), fail closed.
  - Depends on: E-01
  - Expected outcome: `aw specs check` validates one or all specs and fails closed on any violation.
  - Execution state: pending

### Task group 2: the write verbs

- [ ] E-03 implement `aw specs set PATH --status STATUS [--gate-kind K --gate-ref R --gate-summary S] --message TEXT` plus WHATEVER approval/evidence mechanism Order 01 froze (do NOT assume specific flag names; consume the Order 01 contract): validate the transition against the Order 01 authority table; enforce that `approved` requires the frozen human-approval token and `implemented` requires the frozen evidence citation (refuse otherwise, leaving the file byte-identical); add gate fields on entering `deferred` and remove them on leaving (gate fields forbidden on a non-`deferred` result, resolution recorded in history); update `- Status:`; append exactly one `## Workflow history` record; validate the complete result in memory; then `artifact_core.atomic_write` the single file. Never stage/commit/push. SECURITY FLOOR (spec F11): the enforced `approved` mechanism MUST be one an executing agent cannot satisfy autonomously (per Order 01's frozen floor); enforcement of `implemented` is presence + format-validity + resolvability of the citation (an existing `executed/` IPD path), NOT semantic verification that the work truly happened - state this limit so V-03 does not over-claim.
  - Depends on: E-01
  - Expected outcome: a validating, single-file, atomic status writer that enforces the authority table and the anti-self-approval floor.
  - Execution state: pending
- [ ] E-04 implement `aw specs note PATH --message TEXT`: append exactly one `## Workflow history` record; change nothing else; atomic single-file write; no git.
  - Depends on: E-01
  - Expected outcome: a history-append-only verb.
  - Execution state: pending
- [ ] E-05 wire the `aw specs` namespace into the CLI (`cli._build_parser` subparser + `cli._dispatch` route), following the `aw plans`/`aw research` pattern; reachable as `aw specs <verb>` and `python -m agent_workflows specs <verb>`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `aw specs set`/`note`/`check` are live CLI verbs; `aw specs --help` lists them.
  - Execution state: pending

### Task group 3: tests

- [ ] E-06 add `tests/test_specs_verbs.py` covering: `set` legal transition succeeds (status + one history record + atomic write); illegal transition refused byte-identical; `approved` without the token refused; `implemented` without evidence refused; gate fields added/removed across `deferred` entry/exit; `note` appends one record and changes nothing else; `check` catches each violation class from the Order 01 fixtures. Run the file + full suite; paste actual output.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: all `aw specs` behaviors tested against the Order 01 fixtures; full suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- CLI extension pattern: two edit points in `agent_workflows/cli.py` (`_build_parser`, `_dispatch`), mirroring `plans-index`/`research` (`cli.py` around lines 148-360).
- `artifact_core.atomic_write` and the `Drift`/`render_agent_drift`/`drift_exit_code` convention are the required primitives (N3).
- `aw status` already exists (`cli.py:144`); this child adds `aw specs`, NOT a status verb.

## Findings

Depends on the Order 01 contracts being frozen; no code findings until then. The authority table (spec Section 7) is the load-bearing correctness surface: an agent must not be able to set `approved`/`implemented`.

## Proposed changes (ordered, validatable)

1. `agent_workflows/specs.py`: `validate_spec` (E-01), `check`/`set`/`note` entrypoints (E-02/E-03/E-04).
2. `agent_workflows/cli.py`: the `aw specs` subparser + dispatch (E-05).
3. `tests/test_specs_verbs.py` (E-06).

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| The cross-tree `aw attention` scanner | scope | Attention is read-only + cross-tree; specs writes are owner-local. | Order 03 |
| Migrating the existing ~8 specs | scope | The verb exists here; the one-time migration is its own child. | Order 04 |
| plans/research write verbs | scope | Those trees already own their writes; no new router (OQ7). | none (existing verbs) |

## Scope check

- Over-scope: none - only the specs owner verbs + CLI wiring + tests.
- Under-scope: MUST enforce the authority table (human token for `approved`, evidence for `implemented`), typed gates, single-file atomic writes, and the history-append contract. Missing any leaves the "agent cannot self-approve" guarantee unmet.

## Required tests / validation

`python3 -m unittest discover -s tests -t .` green (paste `Ran N ... OK`); `tests/test_specs_verbs.py` passes including the refuse-`approved`/refuse-`implemented` cases; `aw specs check` runs clean on the repo's specs (after Order 04 migration; before it, expect the known pre-migration violations); `aw sanitize --agent` clean; no em/en dashes.

## Spec / documentation sync

Update `.agents/docs/specs/README.md` to document the required spec status + history and the `aw specs` verbs. AGENTS.md pointer update is Order 05's job (grouped with the whatnext/CI wiring) to keep this child code-scoped.

## Open questions

### OQ-01: approval-token UX

- Blocking: no
- Status: open
- Owner: Order 01 (E-06) freezes the mechanism; this child consumes it
- Resolution or deferral rationale: whether the human token is an interactive confirm, a signed marker, or a flag paired with a non-agent-satisfiable proof is decided in Order 01, which MUST freeze it with the anti-self-approval floor (a bare string flag alone is insufficient). This child enforces whatever Order 01 froze AND verifies (V-03) that a no-TTY `set --status approved` is refused. If Order 01's frozen mechanism turns out agent-satisfiable, raise a blocking cross-plan finding against Order 01 rather than shipping a hollow gate. Not blocking at authoring time.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `validate_spec` flags each spec violation class in the Order 01 fixtures (missing/unknown status, trailing prose, bad gate, deferred-without-gate, unsafe descriptive field).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `aw specs check` on a clean fixture exits 0; on each violating fixture exits 1 with a named `location<TAB>rule<TAB>detail` record.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a legal `set` updates status + appends exactly one history record + atomic write; an illegal transition leaves the file byte-identical; `--status approved` in a non-interactive/agent-like (no-TTY) context WITHOUT the frozen human token is refused; `--status implemented` without a well-formed, resolvable evidence citation is refused; entering `deferred` adds valid `Gate-*` fields and leaving `deferred` removes them with the resolution recorded in history; AND after `set`, `git status` shows only the working-tree file changed (nothing staged, no commit, no push).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `aw specs note` appends exactly one history record and leaves status + all other content unchanged (diff shows only the appended line); after `note`, the git index is unchanged (nothing staged/committed/pushed).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `aw specs --help` and `python -m agent_workflows specs --help` list `set`/`note`/`check`; dispatch routes each.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the actual `python3 -m unittest` summary; the refuse-approved and refuse-implemented cases are present and pass; leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This child MUST be reviewed and approved by a human before execution. Do NOT mark it done or move it to `executed/` until every V-* item is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. The terminal lifecycle transition is a POST-gate transaction, never an E-*/V-* item. Requires Order 01 executed first; if the Order 01 contract symbols are absent, STOP.
