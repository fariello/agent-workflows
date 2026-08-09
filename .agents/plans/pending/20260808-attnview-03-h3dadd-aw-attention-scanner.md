# IPD: aw attention read-only scanner and renderers (Set attnview, Order 3)

- Date: 2026-08-08
- Kind: child
- Concern: build the read-only `aw attention` command that scans the tracked trees on demand, validates each artifact against its tree contract, maps each native status to an attention class, and renders JSON or a human board to stdout (never a committed file), failing closed on any violation, so `/whatnext` and CI can consume one deterministic command.
- Scope: add `agent_workflows/attention.py` providing `aw attention` (default human board), `--format json|markdown`, `--check`, `--agent`, over the tracked trees (specs/plans/research per OQ3). Read-only: writes NOTHING to disk. Consumes the Order 01 contracts and reuses the Order 02 spec validator for the specs tree. Does NOT perform writes (owner verbs do) and does NOT rewire `/whatnext` (Order 05). Requires Orders 01 and 02 executed.
- Status: draft
- Set: attnview
- Order: 3
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: h3dadd

## Workflow history

- 2026-08-08 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created. Child of Set `attnview`, authored from the approved spec Sections 8.1, 8.3, 8.5, 8.6, 8.8; requires Orders 01 (contracts) and 02 (specs validator).

## Goal

Deliver `aw attention` as a deterministic, read-only, full-scan command: build one in-memory record set from the tracked trees, validate every artifact (fail closed, collecting all violations), map native status to the five-value class, and render byte-deterministic JSON or a human Markdown board to stdout. `--check`/`--agent` emit the house drift records and the proper exit code. It writes nothing to disk and reuses `artifact_core` primitives.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: the scan + record model

- [ ] E-01 implement the tracked-tree scan in `agent_workflows/attention.py` using `artifact_core.iter_scan_files` over the tree-policy inventory (Order 01), EXCLUDING gitignored `local/` lanes; for each artifact read its native status (spec front-matter via the Order 02 validator; plans via disposition + readiness; research via frontmatter) and build one in-memory record `{path, tree, native_status, class, id, gate?, last_history_at}`.
  - Depends on: none
  - Expected outcome: a pure builder returning the record set + a violation list for the tracked trees.
  - Execution state: pending
- [ ] E-02 apply the Order 01 `class_of(tree, native_status)` mapping to each record; an unknown/unmapped native status becomes a violation (never a default class); a newly discovered unclassified tree is a violation (`attention.unclassified-tree`).
  - Depends on: E-01
  - Expected outcome: every record carries exactly one class or contributes a named violation.
  - Execution state: pending

### Task group 2: renderers + fail-closed check

- [ ] E-03 implement the JSON renderer to the Order 01 versioned schema + canonical serialization profile (byte-deterministic: fixed key order/indentation/separators, sorted by class order then normalized path then id, LF + one final newline, no timestamps/mtime/locale); set `valid:false` + include all violations when any artifact is invalid.
  - Depends on: E-01, E-02
  - Expected outcome: `aw attention --format json` emits byte-deterministic schema-versioned output; invalid scan sets `valid:false` and exits nonzero.
  - Execution state: pending
- [ ] E-04 implement the human Markdown board (grouped by class, attention umbrella first, `blocked` shows the gate, `done`/`parked` hidden unless filtered, NO time-based windows) with deterministic per-surface escaping of descriptive fields (Section 8.8); default `aw attention` renders this.
  - Depends on: E-01, E-02
  - Expected outcome: `aw attention` prints a deterministic, escaped human board.
  - Execution state: pending
- [ ] E-05 implement `--check` and `--agent`: full scan collecting ALL violation classes (Section 8.3 + 8.8 output-safety), render via `artifact_core.render_agent_drift`, exit `drift_exit_code` (0 clean / 1 any violation; 2 could-not-run); fail closed, never skip a malformed included artifact.
  - Depends on: E-01, E-02
  - Expected outcome: `aw attention --check` fails closed with named records on any violation.
  - Execution state: pending
- [ ] E-06 wire `aw attention` into the CLI (`cli._build_parser` + `cli._dispatch`) with `--format`/`--check`/`--agent`; reachable as `aw attention` and `python -m agent_workflows attention`; confirm NO collision with the existing `aw status` verb.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: `aw attention --help` lists the flags; dispatch routes it; `aw status` is untouched.
  - Execution state: pending

### Task group 3: tests

- [ ] E-07 add `tests/test_attention.py`: mapping/coverage over the fixtures; each `--check` violation class produces a stable named violation + exit 1; determinism (identical bytes under varied `cwd`/`TZ`/`LANG`); output-safety fixtures (control-char/newline/over-length/non-http) each caught and renderers never emit raw control chars; a valid scan exits 0 and JSON is schema-valid; `aw plans index --check` and `aw research index --check` still pass unchanged (no regression). Run the file + full suite; paste actual output.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: scanner, check-classes, determinism, and safety all tested; no per-tree-tool regression; full suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_core.iter_scan_files`/`Drift`/`render_agent_drift`/`drift_exit_code` are the required primitives (N3); `SCAN_ROOTS` already covers `.agents/plans` and `.agents/docs`.
- Determinism rules (Section 8.5) forbid timestamps/mtime/locale-sensitive output; the canonical JSON profile is frozen in Order 01/E-04.
- The specs validator from Order 02 is reused for the specs tree; plans/research native-status reads use their existing modules.

## Findings

Read-only design (no committed aggregate) is the core correctness stance from the reconciled review (`b1msgn`): the aggregate is a projection, so drift-vs-disk cannot occur. The remaining correctness surface is fail-closed completeness and byte-determinism, both tested in E-07.

## Proposed changes (ordered, validatable)

1. `agent_workflows/attention.py`: scan + record model (E-01/E-02), JSON + Markdown renderers (E-03/E-04), `--check`/`--agent` (E-05).
2. `agent_workflows/cli.py`: the `aw attention` subparser + dispatch (E-06).
3. `tests/test_attention.py` (E-07).

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| Any write / committed registry | functionality | `aw attention` is read-only by design (spec Non-goals); writes are owner verbs. | Order 02 (specs); existing plans/research verbs |
| `/whatnext` rewire + CI wiring | scope | Consumer + CI are their own child. | Order 05 |
| prompts/comms trees | scope | Excluded from v1 (OQ3) unless Order 01 finalized their contracts. | Phase 3 |
| Persisted `aw attention snapshot` | complexity | Deferred until a non-CLI consumer needs it (OQ9). | Phase 2 |

## Scope check

- Over-scope: none - read-only scanner + renderers + check + CLI wiring + tests only.
- Under-scope: MUST fail closed, be byte-deterministic, cover every violation class, and enforce output safety. Missing any of these breaks the "one trustworthy deterministic command" guarantee `/whatnext` depends on.

## Required tests / validation

`python3 -m unittest discover -s tests -t .` green (paste `Ran N ... OK`); `tests/test_attention.py` passes including determinism + safety + no-regression; `aw attention --check --agent` behaves fail-closed on the fixtures; `aw plans index --check` and `aw research index --check` unchanged; `aw sanitize --agent` clean; no em/en dashes.

## Spec / documentation sync

The `aw attention` help text is self-documenting; the AGENTS.md pointer + README mention are grouped into Order 05. Note in the DECISIONS update (Order 05) that the aggregate is intentionally ephemeral.

## Open questions

### OQ-01: plans native-status source of "active"

- Blocking: no
- Status: open
- Owner: Order 01 (E-02 mapping) / plans owner
- Resolution or deferral rationale: per spec OQ5, plans map `approved`/`auto-approved` -> `ready` unless a native `executing` state exists. If the plans owner has not added `executing` by this Order, plans simply have no `active` items; the scanner does not infer execution. Not blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the builder returns records for specs/plans/research over the tracked trees, excludes `local/`, and reads native status correctly on the fixtures.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: every fixture record gets exactly one class; an unmapped status and an unclassified tree each produce the named violation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `--format json` output validates against the Order 01 schema and is byte-identical across two runs; an invalid scan sets `valid:false` and exits nonzero.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the human board groups by class with the umbrella ordering; a hostile `Gate-Summary` is escaped (no raw control chars, table not broken).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `--check` on a clean fixture exits 0; each violation-class fixture exits 1 with a stable named record; all violations are reported together (not first-only).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: `aw attention --help` and `python -m agent_workflows attention --help` show `--format/--check/--agent`; `aw status` help is unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the actual `python3 -m unittest` summary; determinism + safety + no-regression cases present and passing; `aw plans index --check` / `aw research index --check` unchanged; leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This child MUST be reviewed and approved by a human before execution. Do NOT mark it done or move it to `executed/` until every V-* item is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. The terminal lifecycle transition is a POST-gate transaction, never an E-*/V-* item. Requires Orders 01 and 02 executed first; if their symbols are absent, STOP.
