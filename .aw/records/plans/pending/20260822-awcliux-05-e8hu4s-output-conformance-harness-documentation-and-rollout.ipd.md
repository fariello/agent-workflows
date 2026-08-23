# IPD: Output Conformance Harness Documentation and Rollout

- Date: 2026-08-22
- Kind: child
- Concern: Prove output quality and prevent regression.
- Scope: Generated matrix, PTY/golden/schema/token tests, documentation, compatibility, and release gates.
- Status: draft
- Set: awcliux
- Order: 5
- Highest E allocated: 03
- Author: OpenAI
- Id: e8hu4s

## Workflow history

- 2026-08-22 draft (OpenAI): created to close the program with reproducible evidence.

## Goal

Replace subjective “looks good” acceptance with an exhaustive generated harness and safe rollout.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Conformance matrix

- [ ] E-01 Generate tests from the parser for every leaf under TTY, non-TTY, agent, JSON, no-color, help, usage error, domain failure, and success/preview where applicable.
  - Depends on: none
  - Expected outcome: any undeclared or untested command fails CI.
  - Execution state: pending

### Material change 2: Quality gates

- [ ] E-02 Add schema, fact-parity, ANSI/stream, deterministic-byte, accessibility, truncation, and byte/token-budget gates with reviewed golden fixtures.
  - Depends on: E-01
  - Expected outcome: correctness, readability, and efficiency are measured.
  - Execution state: pending

### Material change 3: Docs and rollout

- [ ] E-03 Publish human/agent guides, release notes, migration recipes, and compatibility schedule; run full suite and sanitizer before release.
  - Depends on: E-01, E-02
  - Expected outcome: users know auto non-TTY behavior, overrides, schema, exits, and rollback.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Existing tests cover color policy, selected universal-agent flags, help, and several families, but not every parser leaf.
- Control Python-version-dependent `argparse` color in goldens.
- Paste actual test output before reporting success.

## Findings

Selection-based tests can pass while a new leaf omits agent mode or a write emits an ambiguous receipt. Generated coverage closes this gap.

## Proposed changes (ordered, validatable)

```text
command | class | scenario | stdout_tty | stdin_tty | flags | rc |
encoding | ansi | stdout_schema | stderr_policy | golden | byte_budget
```

```python
assert run(cmd, stdout_tty=False).stdout == run(cmd + ["--agent"]).stdout
assert not ANSI_RE.search(agent.stdout + agent.stderr)
assert parse_jsonl(agent.stdout).summary["exit"] == agent.returncode
assert semantic_facts(strip_ansi(human.stdout)) == semantic_facts(agent.stdout)
assert receipt["verified"] is False if verification_was_not_run
```

Never optimize away outcome, completeness, identifiers, evidence, omitted counts, or next action.

## Deferred / out of scope (with reason)

- Proprietary-model calls in required CI and pixel screenshots are nondeterministic; schemas and ANSI goldens suffice.

## Scope check

- Over-scope: none.
- Under-scope: test Windows/narrow terminals or document the boundary.

## Required tests / validation

Run matrix tests, complete suite, packaging, `aw check all`, `aw doctor --agent`, and `aw sanitize --agent`; record versions, exits, totals, and hashes.

## Spec / documentation sync

Create a human TTY guide and agent protocol reference; update root help, README, release notes, and contributor command checklist.

## Open questions

### OQ-01: What rollout boundary applies to auto non-TTY mode?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: choose major hard cutover or one-release warning from compatibility evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: generated report has one passing row per required scenario per live leaf and zero undeclared commands.
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
- Cohesion rationale: exactly three changes establish exhaustive tests, measured quality, and controlled rollout.

Review and explicit approval required. Release stays blocked on matrix, schemas, compatibility decision, full suite, and sanitizer.
