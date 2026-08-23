# IPD: Output Conformance Harness Documentation and Rollout

- Date: 2026-08-22
- Kind: child
- Concern: Prove output quality and prevent regression.
- Scope: Generated matrix, PTY/golden/schema/token tests, documentation, compatibility, and release gates.
- Status: reviewed
- Set: awcliux
- Order: 5
- Highest E allocated: 03
- Author: OpenAI
- Id: e8hu4s

## Workflow history

- 2026-08-22 draft (OpenAI): created to close the program with reproducible evidence.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (blocking OQ-01 resolved: hard cutover), PR-002 (E-03 supersede spec 1525-01 G6 + loud byte-break docs), PR-003 (execution contract + release-record note + no tag/publish), PR-004 (V-02/V-03 concrete evidence), PR-005 (paste actual gating output), PR-006 (pin argparse color in goldens), Status draft->reviewed.

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

- [ ] E-02 Add schema, fact-parity, ANSI/stream, deterministic-byte, accessibility (ASCII-glyph fallback), truncation, and byte/token-budget gates with reviewed golden fixtures. Normalize or pin the Python-version-dependent `argparse` color/help output in goldens (e.g. force `--no-color`/`NO_COLOR` and a fixed COLUMNS in the harness) so goldens do not flake across CI Python versions.
  - Depends on: E-01
  - Expected outcome: correctness, readability, and efficiency are measured and goldens are stable across supported Python versions.
  - Execution state: pending

### Material change 3: Docs and rollout

- [ ] E-03 Publish human/agent guides, release notes, migration recipes, and compatibility schedule; LOUDLY document the hard-cutover byte break (piped `status` JSON, `render_agent_drift` TSV, and `find`/`search` path lines all become `aw.agent/v1`) in release notes and the migration guide; and update or supersede the implemented spec `20260818-1525-01-command-surface-redesign.spec.md` G6 via `aw specs` so the repository no longer mandates the retired `Drift` machine convention. Run full suite and sanitizer before release.
  - Depends on: E-01, E-02
  - Expected outcome: users know the auto non-TTY hard cutover, overrides, schema, exits, and rollback; and no implemented spec still mandates a superseded machine convention.
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
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: HARD CUTOVER now, no compatibility window (maintainer decision 2026-08-22 via /plan-review, recorded on orchestrator awcliux-00 OQ-01 and Order 01 hd3kln OQ-01; consistent with the pre-release hard cutover in spec `20260818-1525-01`). This plan therefore does NOT build a deprecation-window path; instead E-03 documents the byte break loudly in release notes and the migration guide and supersedes spec 1525-01 G6.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: generated report has one passing row per required scenario per live leaf and zero undeclared commands.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the quality gates run and pass - schema-valid records, human/agent fact parity, ANSI-free agent streams, deterministic bytes, ASCII-glyph fallback, truncation totals retained, and a byte/token-budget check per leaf; goldens are stable across the supported Python versions (argparse color pinned). Paste the passing gate output and note the Python versions exercised.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the human TTY guide and agent protocol reference exist and describe the hard-cutover auto non-TTY behavior, overrides, schema, exits, and rollback; release notes/migration guide name the byte break; spec `20260818-1525-01` G6 is updated/superseded (cite the `aw specs` change); and the full suite, `aw check all`, `aw doctor --agent`, and `aw sanitize --agent` all pass. Paste the ACTUAL runner output with versions, exits, totals, and hashes.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes establish exhaustive tests, measured quality, and controlled rollout.

Review and explicit approval required. Release stays blocked on matrix, schemas, compatibility decision (resolved: hard cutover), full suite, and sanitizer. If the program is release-blocking, record it once via a `Blocks-Release: next` field on the owning item and the release record under `.aw/records/releases/` (per AGENTS.md "Release gates"), not in prose.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved (hard cutover); no blocking question remains. This plan proves and gates the whole Set, so it may execute only AFTER Order 04 (10jpsa) is executed; if the migrated surface or per-leaf contract declarations are absent, STOP and report.
2. Scope fence: touch only the test harness and fixtures under `tests/`, CI workflow files, the documentation (human TTY guide, agent protocol reference, README, root help text, contributor command checklist, release notes), and the `aw specs` update to spec `20260818-1525-01`. Do NOT change command DOMAIN behavior or the renderers here; if a conformance failure reveals a code defect, fix it in the owning child's scope or a corrective IPD and STOP-and-report rather than widening this plan.
3. Honesty rule (hard MUST): when you report the matrix, full suite, `aw check all`, `aw doctor --agent`, or `aw sanitize --agent` passed, paste the ACTUAL runner output (versions, exits, totals, hashes); never claim a pass you did not run. This is the release-gating evidence.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push. Never create a git tag, GitHub Release, or PyPI upload here (that is release-review Section 9 after an explicit human GO).
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. The orchestrator (awcliux-00) transitions after this plan.
