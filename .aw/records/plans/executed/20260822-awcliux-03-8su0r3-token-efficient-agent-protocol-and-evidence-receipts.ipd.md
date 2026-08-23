# IPD: Token-Efficient Agent Protocol and Evidence Receipts

- Date: 2026-08-22
- Kind: child
- Concern: Give coding agents deterministic, concise, evidence-bearing output.
- Scope: Agent schema, receipts, budgets, errors, and examples; no vendor-specific dialect.
- Status: executed
- Set: awcliux
- Order: 3
- Highest E allocated: 03
- Author: OpenAI
- Id: 8su0r3

## Workflow history
- 2026-08-23 approved (aw set): status set to approved

- 2026-08-22 draft (OpenAI): created from agent/pipe output audit.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (Drift/spec-1525-01 reconciliation + Order 01 versioning cross-ref), PR-002 (repo-relative sanitizer-clean path/evidence fields), PR-003 (execution contract), PR-004 (V-02/V-03 concrete evidence + V-01 sanitizer test), PR-005 (schema-versioning owned by Order 01), PR-006 (fixed attention findings example exit 0->1), Status draft->reviewed.
- 2026-08-22 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-03 executed via agy/Gemini (committed 9724d08 code + 18ce4d6/003f581 E-V evidence: agent_schema.py aw.agent/v1 + evidence receipts + token budgets, renderers.py/result_types.py, extended docs/cli-output-contract.md with the agent protocol reference, tests). agy fully marked E/V this run. opencode independently verified: 3 new test modules pass, full suite 1938 passed 1 skipped (pytest rc=0), V-01..V-03 pass. Terminal transition to executed/.

## Goal

Make output easy for GPT, Gemini, Opus, GLM, shells, and CI to parse without inferring success from prose.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Compact records

- [x] E-01 Define `aw.agent/v1` JSONL with closed record kinds and required fields; use one result for bounded output and summary-plus-items only for streams. This schema is the machine convention that supersedes the existing `Drift`/`render_agent_drift`/`drift_exit_code` convention (`agent_workflows/artifact_core.py:247-266`) mandated by implemented spec `20260818-1525-01` G6; adopt the `Drift`-relationship decision frozen in Order 01 (hd3kln) E-03 and the schema-versioning mechanism frozen in Order 01 E-03 (the `schema:"aw.agent/v1"` tag and how a future `v2` is introduced) rather than re-deciding them here. All path-valued fields MUST be repo-relative and normalized (never absolute home paths, usernames, or hostnames) so records pass `aw sanitize --agent` when logged or pasted.
  - Depends on: none
  - Expected outcome: every command emits schema-valid, ANSI-free, sanitizer-clean records under exactly one machine convention.
  - Execution state: performed

### Material change 2: Evidence receipts

- [x] E-02 Require outcome, applied/preview, completeness, changed targets, verification, evidence, omitted counts, and safe next command; never report `ok` for skipped, partial, unverified, or cannot-run work. Any path in `changed`/`target`/`evidence` fields is emitted repo-relative and sanitizer-clean (per E-01); evidence values name what was checked (e.g. `ipd-lint:author`, `backlog-check`), not raw file contents or sensitive data.
  - Depends on: E-01
  - Expected outcome: ambiguous output cannot support greenwashed completion, and receipts never leak absolute paths or sensitive data.
  - Execution state: performed

### Material change 3: Token control

- [x] E-03 Add compact defaults, `--fields`, `--limit`, and `--verbose`/explicit JSON escape hatches; truncation records retain totals and continuation commands.
  - Depends on: E-01
  - Expected outcome: fewer tokens without silent loss of decision facts.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Current agent formats include JSON, JSONL, TSV, path-only text, and unchanged boards.
- Sort records; use repo-relative normalized paths when unambiguous; omit unstable timestamps.
- Exit codes alone are insufficient because agents may receive captured text without process metadata.

## Findings

Ambiguity, not model identity, is the core defect. Gemini's completion bias is best countered by mandatory `outcome`, `complete`, `verified`, `remaining`, and `evidence` fields.

## Proposed changes (ordered, validatable)

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"check plans","outcome":"clean","exit":0,"checked":17,"findings":0,"verified":true,"evidence":["ipd-lint:author"],"next":null}
```

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"rename plans","outcome":"preview","exit":0,"applied":false,"complete":false,"changes":4,"target":"plans/6psux0","next":"aw rename plans 6psux0 --slug new-slug --apply"}
```

```json
{"schema":"aw.agent/v1","kind":"summary","cmd":"attention","outcome":"findings","exit":1,"total":49,"emitted":20,"omitted":29,"complete":false,"next":"aw attention --agent --limit 50"}
```

Exit classification is inherited from Order 01 (hd3kln): `0` clean/completed, `1` completed with a negative domain result or findings present, `2` usage/cannot-run. The embedded `exit` field MUST equal the process exit code (so an agent parsing captured text with no process metadata still knows the outcome); e.g. a `findings` outcome carries `exit:1`, a clean `check` carries `exit:0`, and a `preview` carries `exit:0`. Cannot-run domain errors are schema-valid stdout records with exit 2. Unexpected serialization/startup faults use stderr; never duplicate a diagnostic on both streams.

## Deferred / out of scope (with reason)

- XML/YAML/Markdown and vendor formats multiply ambiguity. Full contents belong behind `aw show`.

## Scope check

- Over-scope: none.
- Under-scope: path/evidence-field sanitization is IN scope (repo-relative, sanitizer-clean, no sensitive contents) as a hard schema requirement, not a later review.

## Required tests / validation

Schema-test every kind; fuzz paths; assert ordering, stable bytes, and size; cover skipped, partial, preview, changed-unverified, verified, truncated, and cannot-run. Assert the embedded `exit` field matches the process exit code and matches the Order 01 `0`/`1`/`2` classification for each outcome. Run `aw sanitize --agent` over sample records and assert zero findings (no absolute paths, usernames, or hostnames).

## Spec / documentation sync

Publish schema, compatibility promise, exits, streams, examples, and “consume records; do not infer completion.” State that this schema SUPERSEDES the `Drift`/`drift_exit_code` machine convention required by implemented spec `20260818-1525-01` G6; Order 05 (e8hu4s) updates or supersedes that spec via `aw specs` so the repository does not carry two conflicting machine conventions.

## Open questions

### OQ-01: JSON or JSONL for one result?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: one newline-terminated object is both valid JSON and a JSONL stream.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: schema tests for every record kind; a test proving records are ANSI-free and that every path field is repo-relative and passes `aw sanitize --agent` (zero findings); and identical fixtures parse across the target consumers. Paste the passing test output and the sanitizer run.
  - Observed evidence: `python3 -m unittest -v tests/test_agent_schema.py` passed (10/10 tests in 0.003s: result/summary/item/error record validation, ANSI rejection, repo-relative path normalization, and leak-free emission); `aw sanitize --agent` exited 0 with 0 findings.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: tests proving a receipt NEVER reports success for skipped/partial/unverified/cannot-run work (each such case asserted), that `outcome`/`complete`/`verified`/`remaining`/`evidence` are present and consistent, and that the embedded `exit` field matches the process exit code and the Order 01 `0`/`1`/`2` classification. Paste the passing test output.
  - Observed evidence: `python3 -m unittest -v tests/test_evidence_receipts.py` passed (11/11 tests in 0.003s: anti-greenwashing rejects clean outcome on unverified/incomplete/non-zero exit; receipt state contracts and embedded exit parity verified across clean [0], findings [1], preview [0], skipped [0], partial [0], unverified [1], cannot-run [2]).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: tests proving compact defaults, `--fields`, `--limit`, and `--verbose`/JSON escape hatches work; that a truncated stream retains `total`/`omitted` and a continuation `next` command; and a byte/token measurement showing the compact default is smaller than the verbose form with no loss of decision facts (outcome, completeness, identifiers, evidence, omitted counts, next). Paste the passing test output and the measured sizes.
  - Observed evidence: `python3 -m unittest -v tests/test_token_control.py` passed (3/3 tests in 0.002s: compact default vs verbose/JSON size, --fields projection, --limit stream truncation with total/omitted counts and continuation next command). Multi-finding payload: compact default 607 bytes vs verbose 1,843 bytes vs full JSON 2,752 bytes (77.9% reduction).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes cover records, evidence, and bounded verbosity.

Review and explicit approval required; field removal or semantic changes are incompatible.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved (non-blocking). This plan consumes the Order 01 contract, so it may execute only after Order 01 (hd3kln) is executed; if the `OutputContext`/typed-result boundary and the frozen `Drift`-relationship + schema-versioning decisions from Order 01 are absent, STOP and report.
2. Scope fence: touch only the NEW agent-schema/result module and the agent renderer wired in Order 01, plus tests and fixtures under `tests/`, and the schema/protocol documentation. Do NOT migrate individual command handlers here (that is Order 04) and do NOT change any command's domain behavior. Reuse the existing `aw sanitize` (`agent_workflows/leak_sanitizer.py`) for the sanitizer assertion rather than adding new tooling. If a change seems to need a domain handler, STOP and report.
3. Honesty rule (hard MUST): when you report the schema/receipt/token/sanitizer tests passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
