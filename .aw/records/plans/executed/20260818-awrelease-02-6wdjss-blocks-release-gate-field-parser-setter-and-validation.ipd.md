# IPD: blocks-release gate field parser setter and validation

- Date: 2026-08-18
- Kind: child
- Concern: awrelease Order 02 (spec 20260818-1525-03, RELEASE BLOCKER; TODO item 35). Add the item-side `Blocks-Release:` field so a backlog item / spec / plan can DECLARE it gates a release (distinct from being blocked-BY). Add a setter to write/clear it, teach the item front-matter parsers to read it, and add a validation that the value resolves to an existing release record (from Order 01) or the literal `next`.
- Scope: `agent_workflows/backlog.py` + `agent_workflows/specs.py` (parse + set `Blocks-Release`), `agent_workflows/cli.py` (the `--blocks-release` option on `backlog set` / `specs set`), `agent_workflows/check_engine.py` or `agent_workflows/releases.py` (dangling-release validation), + tests. IN: read/write the field, a `--blocks-release <release-id6|next|->` CLI option (`-` clears), and a `check.blocks-release-dangling` Drift when the value does not resolve. OUT: the releases CLASS (Order 01, done); AGENTS.md docs (Order 03); attention SURFACING of the blocker set (awdoctor Set).
- Status: executed
- Set: awrelease
- Order: 2
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 6wdjss

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from spec 20260818-1525-03 + investigation (backlog parse_item backlog.py:90 + field regexes :57-61; backlog run_set backlog.py + cli.py:1450; specs run_set specs.py:330; releases class from Order 01).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Verified backlog field regexes/parse_item/BacklogItem (backlog.py:57/90/65), specs _read_gate template, and that validation is the check_blocks_release FUNCTION (its own V-04 correctly asks for the function's Drift, not a verb). `next`=exactly-one-planned rule is deterministic. No findings.
- 2026-08-18 executed (opencode Opus 4.8): E-01..E-05 performed, V pass; Blocks-Release field/setter + check_blocks_release; full serial suite 1067 passed 1 skipped.

## Goal

Give items a machine-readable way to declare "I gate release X": a `Blocks-Release:` front-matter field
(value = a release id6 or `next`), a `--blocks-release` setter on `backlog set`/`specs set`, parser
support so tools can read it, and a validation flagging a value that resolves to no release record.
This is the data the awdoctor Set later surfaces as "what blocks the release".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Order 01 (the releases class + `agent_workflows/releases.py`) MUST be present. Make
the edits at the exact anchors. The field is OPTIONAL on any item; absence means "does not gate a release".

### Task group 1: parse the field

- [x] E-01 Teach the backlog parser to read `Blocks-Release`. In `agent_workflows/backlog.py`, add a field regex next to the others (backlog.py:57-61): `_BLOCKS_RELEASE_RE = re.compile(r"^- Blocks-Release:[ \t]*(?P<value>\S+)[ \t]*$")`, add a `blocks_release: Optional[str]` field to the `BacklogItem` dataclass, and populate it in `parse_item` (backlog.py:90) via the same field-extraction loop (add `("blocks_release", _BLOCKS_RELEASE_RE)`). Absent -> None.
  - Depends on: none
  - Expected outcome: `parse_item("- Id: aaa111\n- Blocks-Release: next\n").blocks_release == "next"`; absent -> None.
  - Execution state: performed
- [x] E-02 Teach the specs reader to read `Blocks-Release` similarly. In `agent_workflows/specs.py`, add a small `_read_blocks_release(lines) -> Optional[str]` mirroring `_read_gate` (specs.py:93), matching `^- Blocks-Release:\s*(\S+)\s*$` within the metadata block.
  - Depends on: none
  - Expected outcome: a spec with `- Blocks-Release: r1a2b3` reads back `r1a2b3`; absent -> None.
  - Execution state: performed

### Task group 2: the setter

- [x] E-03 Add a `--blocks-release` option to `backlog set` (cli.py:1450 block) and `specs set` (the specs set parser): `--blocks-release` with `dest="blocks_release"`, `default=None`, help `"Declare this item gates a release: a release id6, 'next', or '-' to clear."`. In `backlog.run_set` and `specs.run_set`, when `blocks_release` is provided: if the value is `-`, REMOVE any existing `- Blocks-Release:` line; else set/replace the `- Blocks-Release: <value>` line in the metadata block (insert after the `- Set:`/`- Status:` line if absent). Leave the rest of the transition behavior unchanged.
  - Depends on: E-01,E-02
  - Expected outcome: `aw backlog set <item> --status open --blocks-release next` writes `- Blocks-Release: next`; `--blocks-release -` removes it; round-trips through the parser.
  - Execution state: performed

### Task group 3: validation (dangling release ref)

- [x] E-04 Add a resolver + validation: in `agent_workflows/releases.py` (from Order 01) add `resolve_release(repo_root, value) -> Optional[Path]` returning the release record for a value that is a release id6 (scan `.aw/records/releases/*.release.md` for `- Id: <value>`) or `next` (the single release whose `- Status:` is `planned`); None if unresolved. Then add a check: a function `check_blocks_release(repo_root) -> List[Drift]` that scans backlog+specs+plans items for a `Blocks-Release` value and emits `Drift(path, "check.blocks-release-dangling", "Blocks-Release '<v>' does not resolve to a release record")` when `resolve_release` returns None. Wire it into the awcheck engine's `check_refs` seam (check_engine.py from awcheck Order 01) if that module is present; else expose it for the engine to import later (note as a follow-up).
  - Depends on: E-01,E-02
  - Expected outcome: an item with `Blocks-Release: nonexistent` yields a `check.blocks-release-dangling` Drift; `Blocks-Release: next` with a planned release present yields none.
  - Execution state: performed

### Task group 4: tests

- [x] E-05 Add `tests/test_blocks_release.py` (`BlocksReleaseTests`): `test_backlog_parse_field` (parse_item reads it), `test_specs_read_field`, `test_setter_set_and_clear` (`--blocks-release next` then `-` via run_set), `test_dangling_flagged` (unresolvable value -> Drift), `test_next_resolves` (a planned release makes `next` resolve, no drift). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: the tests pass; full serial suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Backlog field regexes + `parse_item` + `BacklogItem` (backlog.py:57-61/90); the extraction loop makes adding a field a 3-line change.
- specs `_read_gate` (specs.py:93) is the template for `_read_blocks_release`.
- Setters: `backlog set` parser cli.py:1450 + `backlog.run_set`; `specs set` parser + `specs.run_set` (specs.py:330). They already edit metadata lines in place (gate fields), so adding one field follows the same pattern.
- The releases class + `agent_workflows/releases.py` come from Order 01; `resolve_release` belongs there.
- `next` = the single release record with `- Status: planned` (per spec 1525-03 OQ-2); an explicit id6 also allowed.
- Drift rule id: `check.blocks-release-dangling` (namespaced under `check.`).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Item parsers + setters already edit bullet fields. | Adding `Blocks-Release` follows the exact gate-field pattern; low risk. |
| F2 | `next` needs a unique planned release. | resolve_release picks the single planned release; if zero or many, that is itself a condition the check can note (keep simple: None if not exactly one). |
| F3 | Validation seam is check_engine.check_refs (awcheck Order 01). | Fold in if present; else expose for later wiring - avoids a hard cross-Set ordering requirement. |

## Proposed changes (ordered, validatable)

1. backlog parse field (E-01). 2. specs read field (E-02). 3. `--blocks-release` setter on both (E-03). 4. resolve_release + dangling check (E-04). 5. tests + suite (E-05).

## Deferred / out of scope (with reason)

- The releases class: Order 01 (done). AGENTS.md BLOCKS-RELEASE vs BLOCKED-BY docs: Order 03.
- Attention surfacing of the blocker set: awdoctor Set (reads this field).
- Plans-side setter (plan metadata): backlog + specs cover the common cases; a plan can carry the field and be validated by check_blocks_release, but a dedicated plan setter is deferred (note as follow-up).

## Scope check

- Over-scope: none - the field, its setter on the two main item types, and its validation.
- Under-scope: none for the gate MECHANISM - parse + set + validate are covered; surfacing is the awdoctor Set by design.

## Required tests / validation

`tests/test_blocks_release.py` (E-05) + the full serial suite. Each V-item pins one E.

## Spec / documentation sync

No AGENTS.md change here (Order 03 documents the concept). No spec transition (orchestrator advances spec 1525-03 when the Set completes).

## Open questions

### OQ-01: if `next` resolves to zero or multiple planned releases, error or warn?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: `resolve_release(...,"next")` returns None unless EXACTLY ONE planned release exists; a `Blocks-Release: next` with zero/many planned releases therefore surfaces as `check.blocks-release-dangling` drift (the maintainer should have exactly one active planned release). Deterministic and safe.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `parse_item` reading `Blocks-Release: next` and absent->None.
  - Observed evidence: Verified: backlog+specs parse the field, --blocks-release sets/clears, check_blocks_release flags dangling + next resolves (test_blocks_release 5 pass); suite 1067p/1s.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste the specs `_read_blocks_release` reading a value and absent->None.
  - Observed evidence: Verified: backlog+specs parse the field, --blocks-release sets/clears, check_blocks_release flags dangling + next resolves (test_blocks_release 5 pass); suite 1067p/1s.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `aw backlog set <item> --status open --blocks-release next` writing the line, and `--blocks-release -` clearing it.
  - Observed evidence: Verified: backlog+specs parse the field, --blocks-release sets/clears, check_blocks_release flags dangling + next resolves (test_blocks_release 5 pass); suite 1067p/1s.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste a dangling value flagged (`check.blocks-release-dangling`) and `next` resolving cleanly with a planned release present.
  - Observed evidence: Verified: backlog+specs parse the field, --blocks-release sets/clears, check_blocks_release flags dangling + next resolves (test_blocks_release 5 pass); suite 1067p/1s.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste `pytest tests/test_blocks_release.py -p no:xdist -q` passing + the full serial suite tail.
  - Observed evidence: Verified: backlog+specs parse the field, --blocks-release sets/clears, check_blocks_release flags dangling + next resolves (test_blocks_release 5 pass); suite 1067p/1s.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the touched files
path-scoped (never `git add -A`), never pushes, and transitions only after `aw ipd lint --phase
pre-transition` conforms and every V is `pass`. Order 02 of awrelease (RELEASE BLOCKER); depends on
Order 01 (the releases class). Order 03 documents the concept in AGENTS.md.
