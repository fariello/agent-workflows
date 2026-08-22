# IPD: Output Mode Contract and Renderer Boundary

- Date: 2026-08-22
- Kind: child
- Concern: Centralize output selection and prevent command-specific format drift.
- Scope: Mode detection, typed results, renderer interface, streams, exits, and overrides.
- Status: draft
- Set: awcliux
- Order: 1
- Highest E allocated: 03
- Author: OpenAI
- Id: hd3kln

## Workflow history

- 2026-08-22 draft (OpenAI): created after parser/output audit.

## Goal

Choose output mode once and render one typed command result for either audience without changing domain behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Mode precedence

- [ ] E-01 Add a root `OutputContext`: explicit `--json`/`--format` > `--agent` > non-TTY stdout => agent > TTY stdout => human; `--no-color` changes styling only.
  - Depends on: none
  - Expected outcome: piping any command selects agent output without a flag.
  - Execution state: pending

### Material change 2: Typed result boundary

- [ ] E-02 Define stdlib result types (`CommandResult`, `Diagnostic`, `Change`, `Evidence`, `NextAction`) and make handlers return them instead of presentation strings.
  - Depends on: E-01
  - Expected outcome: both renderers consume identical facts and exit classification.
  - Execution state: pending

### Material change 3: Streams and compatibility

- [ ] E-03 Freeze stdout/stderr, schema versioning, broken-pipe behavior, explicit-format compatibility, and the automatic non-TTY migration policy.
  - Depends on: E-01
  - Expected outcome: deterministic documented bytes and exits.
  - Execution state: pending

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

Add one normative CLI output contract and link help to it.

## Open questions

### OQ-01: Which non-TTY encoding is default?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: prefer compact JSONL; use a deprecation window if byte compatibility requires it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: passing precedence tests including piped writes and explicit overrides.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes establish one output boundary.

Review and explicit approval required; do not change public default bytes until OQ-01 is resolved.
