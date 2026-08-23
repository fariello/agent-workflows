# IPD: Output Mode Contract and Renderer Boundary

- Date: 2026-08-22
- Kind: child
- Concern: Centralize output selection and prevent command-specific format drift.
- Scope: Mode detection, typed results, renderer interface, streams, exits, and overrides.
- Status: approved
- Approval: Gabriele Fariello 2026-08-23 (aw set)
- Set: awcliux
- Order: 1
- Highest E allocated: 03
- Author: OpenAI
- Id: hd3kln

## Workflow history
- 2026-08-23 approved (aw set): status set to approved

- 2026-08-22 draft (OpenAI): created after parser/output audit.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (blocking OQ-01 resolved: hard cutover), PR-002 (Drift/spec-1525-01 reconciliation in E-03 + sync), PR-003 (execution contract added), PR-004 (V-02/V-03 concrete evidence), PR-005 (E-02 scope clarified vs Order 04), PR-006 (Status draft->reviewed).

## Goal

Choose output mode once and render one typed command result for either audience without changing domain behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Mode precedence

- [x] E-01 Add a root `OutputContext`: explicit `--json`/`--format` > `--agent` > non-TTY stdout => agent > TTY stdout => human; `--no-color` changes styling only.
  - Depends on: none
  - Expected outcome: piping any command selects agent output without a flag.
  - Execution state: performed

### Material change 2: Typed result boundary

- [x] E-02 Define stdlib result types (`CommandResult`, `Diagnostic`, `Change`, `Evidence`, `NextAction`) and the renderer interface that consumes them; migrate ONE reference handler (`doctor`, the agreed reference view) to return a typed result so both renderers are exercised end to end. Full per-command migration is Order 04, not here.
  - Depends on: E-01
  - Expected outcome: both renderers consume identical facts and exit classification from one typed result on at least the reference handler; the boundary exists for Order 04 to adopt.
  - Execution state: performed

### Material change 3: Streams and compatibility

- [x] E-03 Freeze stdout/stderr, schema versioning, broken-pipe behavior, explicit-format compatibility, and the automatic non-TTY migration policy (hard cutover, per OQ-01). Record the decision on how the new `CommandResult`/`aw.agent/v1` machine convention relates to the existing `Drift`/`render_agent_drift`/`drift_exit_code` convention (`agent_workflows/artifact_core.py:247-266`): whether it subsumes, wraps, or replaces it, and confirm the `0`/`1`/`2` exit semantics carry over unchanged. Two live machine conventions are not allowed.
  - Depends on: E-01
  - Expected outcome: deterministic documented bytes and exits, and exactly one machine-output convention with a recorded `Drift`-relationship decision.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `term.py` already handles TTY, `NO_COLOR`, `FORCE_COLOR`, `TERM=dumb`, and 256-color statuses.
- Machine output currently varies among JSON, JSONL, TSV, path-only text, and unchanged plain views; many writes lack `--agent`.
- Preserve root/subparser `--no-color` and dry-run safety.

## Findings

At the audited commit, `attention --agent` and `find --agent` are byte-identical to piped plain output, while `status --agent` uses JSON and `doctor --agent` uses TSV. Direct printing couples handlers to presentation.

## Proposed changes (ordered, validatable)

```python
def select_output(args, stdout):
    if explicit_format(args): return explicit_context(args)
    if args.agent or not stdout.isatty(): return agent_context()
    return human_context(color=should_color(stdout))
```

Human progress goes to stderr. Agent stdout contains records only; domain failures are records, while unencodable/cannot-start failures may use stderr. Exit `0` is completed/clean, `1` is completed with negative domain result/findings, and `2` is usage/cannot-run, unless a versioned command contract says otherwise.

## Deferred / out of scope (with reason)

- Layout is Order 02; record fields are Order 03; migration is Order 04.

## Scope check

- Over-scope: none.
- Under-scope: stdin TTY controls prompting, not audience; test that distinction.

## Required tests / validation

Truth-table stdout/stdin TTY, agent/JSON flags, `--no-color`, `NO_COLOR`, `FORCE_COLOR`, and `TERM=dumb`; assert one renderer call and fact parity.

## Spec / documentation sync

Add one normative CLI output contract and link help to it. This contract SUPERSEDES the machine-output requirement in the implemented, release-blocking spec `20260818-1525-01-command-surface-redesign.spec.md` G6 (which mandates reusing `Drift`/`drift_exit_code`); Order 05 updates or supersedes that spec via `aw specs` so the repository does not carry two conflicting machine conventions. Record the `Drift`-relationship decision (E-03) in the new contract.

## Open questions

### OQ-01: Which non-TTY encoding is default?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: HARD CUTOVER to compact `aw.agent/v1` JSONL now, no deprecation window (maintainer decision 2026-08-22 via /plan-review on orchestrator awcliux-00 OQ-01; consistent with the pre-release hard cutover already accepted in spec `20260818-1525-01`). Non-TTY/piped stdout selects `aw.agent/v1` immediately. Consequence: any consumer parsing the current piped bytes (`status` JSON, `render_agent_drift` TSV, `find`/`search` path lines) breaks at the release; Order 05 documents this loudly in release notes and the migration guide, and the `Drift`-relationship decision (E-03) governs how the TSV wire form is retired or retained.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: passing precedence tests including piped writes and explicit overrides.
  - Observed evidence: `tests/test_output_mode.py` (11 passed): truth-table tests verify explicit format > agent flag > non-TTY stdout (automatic agent mode) > TTY stdout (human mode), with --no-color, NO_COLOR, FORCE_COLOR, stdin TTY independence, and broken pipe handling.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the result types (`CommandResult`, `Diagnostic`, `Change`, `Evidence`, `NextAction`) and renderer interface exist; a test drives the reference handler (`doctor`) through BOTH renderers from one typed result and asserts identical outcome facts (status, counts, paths, evidence, exit classification). Paste the passing test output and name the module/line of the type definitions.
  - Observed evidence: `CommandResult`, `Diagnostic`, `Change`, `Evidence`, `NextAction` defined in `agent_workflows/result_types.py:141-267` and renderers in `agent_workflows/renderers.py:27-135`. `tests/test_renderer_boundary.py` (4 passed) drives `doctor.inspect_repo` through `HumanRenderer` and `AgentRenderer` asserting identical outcome facts (status, counts, paths, evidence, exit classification).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the normative CLI output contract documents frozen stdout/stderr split, schema version, broken-pipe behavior, explicit-format compatibility, hard-cutover non-TTY policy, and the `Drift`-relationship decision; a test asserts the documented exit codes (`0` clean, `1` findings, `2` cannot-run) and that no second machine convention remains (either `Drift` callers migrated or `render_agent_drift` explicitly retained as the wire form). Paste the passing test output and cite the contract section.
  - Observed evidence: `docs/cli-output-contract.md` documents frozen stdout/stderr split (Section 4), schema version `aw.agent/v1` (Section 5), broken pipe handling (Section 4), explicit-format compatibility (Section 1), hard-cutover non-TTY policy (Section 6), and Drift-relationship decision (Section 7, CommandResult/aw.agent/v1 subsumes and replaces legacy Drift TSV). `tests/test_output_contract.py` (5 passed) asserts 0/1/2 exit codes and single machine convention.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes establish one output boundary.

Review and explicit approval required. OQ-01 is resolved (hard cutover), so the public default-byte change is authorized under this contract; still do not ship it without the Order 05 migration guide and release notes.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved (hard cutover); no blocking question remains.
2. Scope fence: touch only `agent_workflows/cli.py` (root `OutputContext`/`select_output` wiring, near the existing `_build_parser()` at `cli.py:423` and the shared `--no-color` parent at `cli.py:424-427`), a NEW result-types module and a NEW renderer module (stdlib only, no new dependency), the reference-handler wiring in `agent_workflows/doctor.py`, and their tests under `tests/`. Do NOT migrate other command handlers here (that is Order 04) and do NOT change any command's domain behavior. If the boundary seems to require touching another handler or a domain module, STOP and report.
3. Honesty rule (hard MUST): when you report the precedence/parity/exit tests passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. Requires nothing from siblings (Order 01 has `Depends on: none`); Orders 02/03 may start only after this plan is executed.
