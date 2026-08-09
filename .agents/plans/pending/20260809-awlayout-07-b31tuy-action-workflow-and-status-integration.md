# IPD: Action workflow and status integration

- Date: 2026-08-09
- Kind: child
- Concern: Extend D125's attention projection with AW actions, surface them in status and guidance workflows, and close `setup-repo` only after successful setup.
- Scope: action-source mapping in `agent_workflows/attention_contract.py` and `agent_workflows/attention.py`, action-facing CLI summaries, `.agents/workflows/whatnext/whatnext.md`, `.agents/workflows/setup-repo/setup-repo.md`, relevant getting-started workflow text and shims, and focused attention and workflow integration tests.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 7
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: b31tuy

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): replaced the competing direct `/whatnext` query with a native action source in D125's existing read-only attention projection.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L7-01 [Med-High] (the SHIPPED D125 scanner is repo-relative - iter_scan_files over SCAN_ROOTS, _rel_posix raises on external paths - so E-01 cannot read an external `state/actions/` root as written; add an external-root discovery branch + non-repo-relative item path, name attention.py as in-scope). L7-02 (specify HOW the action mapping coexists with the repo-relative `TreePolicy.root` contract - a new external source, not a fake root). L7-05 (declare the Order 01 context resolver as a DIRECT dependency; currently Depends on 06 only). L7-07 [MEDIUM] (V-01 requires a fail-closed external-state violation but the frozen closed `RULE_IDS` catalog has none; add a stable rule id). Positive: correctly EXTENDS (not forks) D125, keeps aw attention read-only, aw todo owns writes, and the 4-row action->class mapping matches §12.7 (no `active`).
- 2026-08-09 author revision (Codex GPT-5): addressed L7-01, L7-02, L7-05, and L7-07 by defining a separate resolver-driven external source, a safe logical item path, a stable fail-closed rule ID, and direct dependencies on Orders 01 and 06 without changing repo-relative `TreePolicy` semantics.

## Goal

Make unresolved AW setup and maintenance work visible where users ask what to do next, without mixing it with project tasks. Ensure setup completion is based on a successful terminal workflow outcome, not merely on invoking the workflow.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Query and guidance integration

- [ ] E-01 Extend `attention_contract.py` and `attention.py` with an `ExternalSourcePolicy` for AW actions that is scanned after the existing repo-relative `TREE_POLICY` pass. Resolve its root through Order 01, never pass external files to `_rel_posix` or `TreePolicy.root`, emit non-secret logical item paths `aw-state/actions/<lifecycle>/<filename>`, map `open` to `ready`, `completed` to `done`, and `dismissed` and `superseded` to `parked`, and add stable rule ID `attention.external-state-invalid` for unavailable, ambiguous, malformed, unsafe, or escaping roots.
  - Depends on: none
  - Expected outcome: `aw attention --format json` remains the sole cross-tree projection and includes clearly labeled AW operational actions without inferring from prose, timestamps, or install history.
  - Execution state: pending
- [ ] E-02 Update `/whatnext` to continue querying `aw attention --format json` first, stop on `valid: false`, present projected open AW actions in a separate category with the exact resolving command, and continue with normal project recommendations.
  - Depends on: E-01
  - Expected outcome: `setup-repo` persists in `/whatnext` results until completed or dismissed without hiding unrelated project work.
  - Execution state: pending
- [ ] E-03 Update `/setup-repo` to inspect the action, perform its existing setup contract, and complete the latest open generation only after the terminal success summary; leave it open after cancellation, interruption, partial failure, or validation failure.
  - Depends on: E-02
  - Expected outcome: action state reflects achieved setup rather than attempted setup.
  - Execution state: pending

### Task group 2: Orientation and parity

- [ ] E-04 Update installed getting-started and post-install orientation so users see the initial action, its purpose, and the short complete or dismiss commands without exposing record content.
  - Depends on: E-03
  - Expected outcome: fresh-install guidance and later status output teach one consistent action model.
  - Execution state: pending
- [ ] E-05 Add integration tests for open, completed, dismissed, interrupted, and superseded setup actions; regenerate derived command shims and run parity checks through repository tooling.
  - Depends on: E-04
  - Expected outcome: packaged workflow bodies, generated shims, and CLI behavior remain synchronized.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Packaged workflow bodies are authoritative; generated host shims must be regenerated, not hand-edited.
- D125 makes `aw attention --format json` the first and only cross-tree attention input for `/whatnext`; the workflow must stop when that view is invalid.
- `aw todo` owns action mutations and direct queries; `aw attention` is read-only and maps native action state exhaustively.
- Repo-relative artifacts continue to use `TREE_POLICY`, `iter_scan_files`, and `_rel_posix`. AW actions use a separate external-source iterator and a logical, non-filesystem display path, so no fake repo-relative root or absolute machine path enters the contract.
- Workflow completion must include validation evidence before state mutation.
- Agent-facing commands need deterministic, prompt-free output.

## Findings

| Event | `setup-repo` result |
|---|---|
| Workflow merely starts | remain open |
| User cancels or agent stops early | remain open |
| Validation fails | remain open |
| Terminal success summary is reached | complete latest open generation |
| User explicitly dismisses | move to dismissed |

## Proposed changes (ordered, validatable)

1. Add the action native-source mapping to the existing attention projection.
2. Consume that projection in a distinct `/whatnext` category without adding another aggregator.
3. Tie setup completion to successful terminal state.
4. Align first-run guidance.
5. Verify workflow, shim, and package parity.

## Deferred / out of scope (with reason)

- General project TODO aggregation and a second status registry are excluded; this integration extends D125's existing projection only.
- Record-producing path changes are Order 08.
- Automatic reminders or background processes are not part of the CLI workflow model.

## Scope check

- Over-scope: no new action schema, generic write router, persisted attention snapshot, project task system, scheduler, or storage backend.
- Under-scope: native-source mapping, fail-closed attention behavior, status, `/whatnext`, `/setup-repo`, first-run orientation, lifecycle outcomes, shims, and tests are covered.

## Required tests / validation

- `python3 -m unittest discover -s tests -p '*action*' -v`
- `python3 -m unittest tests.test_attention_contract tests.test_attention -v`
- `python3 -m agent_workflows attention --check`
- `python3 -m agent_workflows shim generate`
- `python3 -m agent_workflows parity`
- `python3 -m unittest discover -s tests -v`

## Spec / documentation sync

- Keep workflow semantics aligned with the canonical 2026-08-09 layout specification and Order 06 action schema.
- Preserve D125's attention JSON versioning, deterministic ordering, fail-closed behavior, output safety, and read-only boundary.
- Regenerate every derived host representation changed by workflow-body edits.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: contract and scanner tests cover every action directory, prove the existing `TREE_POLICY` is unchanged, prove external items bypass `_rel_posix`, assert logical `aw-state/actions/...` paths contain no machine root, and produce `attention.external-state-invalid` for unavailable, ambiguous, malformed, traversal, symlink-escaping, or unreadable state. Deterministic ordering, redaction, output safety, and ANSI-free JSON and agent output also pass.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `/whatnext` contract fixtures prove attention JSON is consumed first, invalid views stop processing, an open setup action includes its resolution command, and resolved actions leave the ready category.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: workflow tests prove only the validated terminal success path completes the action; all incomplete paths preserve it.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: fresh-install transcript and installed getting-started content show the same action name and short commands.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: focused and full tests pass, shim generation is clean on a second run, and parity reports no drift.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: the workflow experience is one consumer-facing slice of the Order 06 action contract.

STOP if Order 01 or Order 06 is incomplete. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.
