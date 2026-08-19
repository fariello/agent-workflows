# IPD: shared selector resolver module

- Date: 2026-08-18
- Kind: child
- Concern: awselect Order 01 (spec 20260818-1525-01; TODO items 17, 18). Build ONE shared, self-contained selector-resolver module that, given a record TYPE and one-or-more selector tokens, resolves each token as an id6, a setid, a partial/full filename, or a status, and returns the matching record file path(s). This is a PURE PRIMITIVE with no CLI wiring: Order 02 and the awcmdsurf verbs consume it. Building it as its own module with its own tests keeps this Order small and unambiguous.
- Scope: ONE new module `agent_workflows/selectors.py` + ONE new test file `tests/test_selectors.py`. IN: a `resolve_selectors(repo_root, record_type, tokens)` function + small helpers, reusing `artifact_core.ID6_RE` and reading each record's front-matter `- Id:`/`- Status:`/`- Set:` and its filename. OUT: any change to `cli.py`, to `aw show`, to any existing module, or to any verb (all of that is Order 02 / awcmdsurf). This Order adds a NEW file and a NEW test file ONLY.
- Status: reviewed
- Set: awselect
- Order: 1
- Highest E allocated: 06
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: axkviw

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade detail (atomic steps, exact anchors, explicit test skeleton) from spec + investigation (artifact_core.ID6_RE artifact_core.py:39; resolve_record_read_paths record_producers.py:597; _RECORD_CLASS_SUBPATHS record_producers.py:125).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Pure new module (selectors.py) + tests; verified artifact_core.ID6_RE + resolve_record_read_paths reuse; the fallback chain (id6->status->setid->filename) is deterministic; no interaction with existing code. No findings.

## Goal

Add a new pure module `agent_workflows/selectors.py` that turns human selector tokens (id6, setid,
filename fragment, or status) into concrete record file paths for a given record type, supporting many
tokens at once (OR-combined, de-duplicated). It touches nothing else, so it is safe and independently
testable; later work wires it into `aw show` and the cross-cutting verbs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Do EXACTLY the steps below, in order. Create only the two files named in Scope. Do
NOT edit `cli.py` or any existing module. After each code step, run the matching V-item command and
paste its output. Use 4-space indentation and `from __future__ import annotations` at the top.

### Task group 1: create the module skeleton + type->tree resolution

- [ ] E-01 Create the new file `agent_workflows/selectors.py` with this exact header and imports, and nothing else yet:
  ```python
  """Shared selector resolver: turn selector tokens (id6 | setid | filename fragment | status)
  into concrete record file paths for a record type. Pure (no CLI, no writes). Consumed by
  `aw show` and the cross-cutting verbs (awselect Order 02 + awcmdsurf)."""

  from __future__ import annotations

  import re
  from pathlib import Path
  from typing import List

  from agent_workflows import artifact_core as _core
  from agent_workflows import record_producers as _rp
  ```
  - Depends on: none
  - Expected outcome: the file imports cleanly (`python3 -c "import agent_workflows.selectors"` exits 0).
  - Execution state: pending
- [ ] E-02 Add a function `record_dirs(repo_root: Path, record_type: str) -> List[Path]` that returns the directories to search for a record type. Implement it by calling `_rp.resolve_record_read_paths(record_type, target_repo=str(repo_root))` and returning only the existing directories from that list. Wrap the call in `try/except Exception: return []` so an unknown type yields an empty list rather than raising.
  ```python
  def record_dirs(repo_root: Path, record_type: str) -> List[Path]:
      """Directories to search for a record type (primary + any legacy read path)."""
      try:
          paths = _rp.resolve_record_read_paths(record_type, target_repo=str(repo_root))
      except Exception:
          return []
      return [p for p in paths if p.is_dir()]
  ```
  - Depends on: E-01
  - Expected outcome: `record_dirs(repo_root, "plans")` returns a list containing the repo's `.aw/records/plans` dir; `record_dirs(repo_root, "bogus")` returns `[]`.
  - Execution state: pending

### Task group 2: per-file metadata reads

- [ ] E-03 Add three small readers that extract front-matter fields from a record file's text, matching the existing bullet-metadata format used across the repo (e.g. `- Id: abc123`). Use these EXACT regexes (they mirror plans_index/backlog parsers):
  ```python
  _ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
  _STATUS_RE = re.compile(r"(?m)^- Status:\s*(\S+)\s*$")
  _SET_RE = re.compile(r"(?m)^- Set:\s*(.+?)\s*$")

  def _read_id(text: str) -> str | None:
      m = _ID_RE.search(text)
      return m.group(1) if m else None

  def _read_status(text: str) -> str | None:
      m = _STATUS_RE.search(text)
      return m.group(1) if m else None

  def _read_setid(text: str) -> str | None:
      m = _SET_RE.search(text)
      if not m:
          return None
      # The set-id is the first whitespace token before any '(' (mirrors plans_index.set_terse_id).
      return m.group(1).split("(")[0].strip().split()[0] if m.group(1).strip() else None
  ```
  - Depends on: E-01
  - Expected outcome: `_read_id("- Id: abc123\n")=="abc123"`; `_read_status("- Status: approved\n")=="approved"`; `_read_setid("- Set: demo (Demo Set)\n")=="demo"`.
  - Execution state: pending

### Task group 3: single-token resolution

- [ ] E-04 Add `resolve_one(repo_root: Path, record_type: str, token: str) -> List[Path]` that resolves ONE token against one type's record dirs. Rules, checked IN THIS ORDER, returning ALL files that match the FIRST rule that produces any match:
  1. If `_core.ID6_RE.match(token)` (an exact 6-char id6): return every `*.md` file under `record_dirs` whose front-matter `- Id:` equals `token`.
  2. Else if `token` is one of the known statuses (accept any non-empty token here; match against the file's `- Status:`): return every `*.md` whose `_read_status` equals `token`.
  3. Else treat `token` as a setid: return every `*.md` whose `_read_setid` equals `token`.
  4. Else treat `token` as a filename fragment: return every `*.md` whose `path.name` CONTAINS `token`.
  Note: rules 2-4 can each match; apply them as a fallback chain (try id6; if none, try status; if none, try setid; if none, try filename-substring). Walk files with `dir.rglob("*.md")`, skipping any file named `README.md`, `INDEX.md`, or `STATUS.md`. De-duplicate the result (a file matched once). Read each file with `p.read_text(encoding="utf-8")` inside `try/except OSError: continue`.
  - Depends on: E-02,E-03
  - Expected outcome: given a plans dir with a plan `- Id: abc123` `- Status: approved` `- Set: demo`, `resolve_one(root,"plans","abc123")`, `resolve_one(root,"plans","approved")`, `resolve_one(root,"plans","demo")`, and `resolve_one(root,"plans","<a filename fragment>")` each return that plan's path.
  - Execution state: pending

### Task group 4: multi-token public API

- [ ] E-05 Add the public `resolve_selectors(repo_root: Path, record_type: str, tokens: List[str]) -> List[Path]` that calls `resolve_one` for EACH token and returns the OR-union of all matches, de-duplicated, sorted by path. An empty `tokens` list returns `[]`. This is the function Order 02 + awcmdsurf import.
  ```python
  def resolve_selectors(repo_root, record_type, tokens):
      seen = {}
      for tok in tokens:
          for p in resolve_one(repo_root, record_type, tok):
              seen[str(p)] = p
      return [seen[k] for k in sorted(seen)]
  ```
  - Depends on: E-04
  - Expected outcome: `resolve_selectors(root,"plans",["abc123","def456"])` returns both plans' paths (union), sorted, no duplicates; `resolve_selectors(root,"plans",[])==[]`.
  - Execution state: pending

### Task group 5: tests

- [ ] E-06 Create `tests/test_selectors.py` with a `unittest.TestCase` subclass `SelectorResolverTests` that builds a tmp repo fixture and asserts each resolution mode. Write EXACTLY these test methods (build the fixture in `setUp` using `tempfile.TemporaryDirectory`; create `.aw/records/plans/pending/` and write two plan files: `A` with `- Id: aaa111`/`- Status: approved`/`- Set: demo` and slug `alpha`, `B` with `- Id: bbb222`/`- Status: draft`/`- Set: other` and slug `beta`):
  - `test_resolve_by_id6`: `resolve_selectors(root,"plans",["aaa111"])` returns exactly `[A]`.
  - `test_resolve_by_status`: `["approved"]` returns exactly `[A]`; `["draft"]` returns exactly `[B]`.
  - `test_resolve_by_setid`: `["demo"]` returns exactly `[A]`.
  - `test_resolve_by_filename_fragment`: `["beta"]` returns exactly `[B]`.
  - `test_multiple_tokens_union`: `["aaa111","bbb222"]` returns `[A, B]` (sorted), no duplicates.
  - `test_empty_and_unknown`: `resolve_selectors(root,"plans",[])==[]`; `resolve_selectors(root,"bogus",["x"])==[]`.
  Then run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04,E-05
  - Expected outcome: all six test methods pass; full serial suite green (this Order only ADDS files).
  - Execution state: pending

## Project conventions discovered (Step 0)

- id6 primitive: `artifact_core.ID6_RE = re.compile(r"\A[0-9a-z]{6}\Z")` (artifact_core.py:39); `is_valid_id6` (:45).
- Record-tree resolution: `record_producers.resolve_record_read_paths(<class>, target_repo=...)` (record_producers.py:597) returns `[primary, legacy?]` Paths; classes are keys of `_RECORD_CLASS_SUBPATHS` (record_producers.py:125): plans/specs/research/prompts/comms/walkthroughs (roadmaps/backlog resolvable too).
- Bullet front-matter format `- Field: value` is universal; id6 line matches `^- Id:\s*([0-9a-z]{6})\s*$`, set-id is the first token before `(` (mirrors plans_index.set_terse_id, plans_index.py:66).
- Non-record basenames to skip when walking: README.md / INDEX.md / STATUS.md.
- This module is a PRIMITIVE: no argparse, no writes, no dependency on cli.py. Keep it importable in isolation.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | id6/tree/front-matter primitives already exist. | The resolver composes existing helpers; it invents no new grammar. |
| F2 | Multiple resolution modes overlap. | Apply a deterministic fallback chain (id6 -> status -> setid -> filename) so a token resolves predictably. |
| F3 | Pure module, new file only. | Zero risk to existing behavior; the full suite must stay green with only additions. |

## Proposed changes (ordered, validatable)

1. New `selectors.py` header/imports (E-01). 2. `record_dirs` (E-02). 3. front-matter readers (E-03). 4. `resolve_one` fallback chain (E-04). 5. `resolve_selectors` OR-union public API (E-05). 6. `tests/test_selectors.py` + full suite (E-06).

## Deferred / out of scope (with reason)

- Wiring the resolver into `aw show` and enabling status-selection in verbs: awselect Order 02.
- Consumption by the cross-cutting verbs: awcmdsurf (Set A).
- Any change to existing modules or cli.py: explicitly OUT (this Order adds two new files only).

## Scope check

- Over-scope: none - one new module + its test.
- Under-scope: none for the PRIMITIVE - all four selector modes + multi-token union are covered and tested.

## Required tests / validation

`tests/test_selectors.py` (E-06, six named methods) + the full serial suite. Each V-item pins one E.

## Spec / documentation sync

No doc/AGENTS.md change (the module is internal plumbing; the user-facing grammar is documented when awcmdsurf lands). No spec transition here (the orchestrator advances the spec when the Set completes).

## Open questions

### OQ-01: should a token that is BOTH a valid id6 shape AND a filename fragment prefer id6?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: YES - the fallback chain tries id6 FIRST (E-04 rule order), so an exact 6-char base36 token resolves as an id6; only if no id6 matches does it fall through to status/setid/filename. This is deterministic and documented in E-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "import agent_workflows.selectors; print('ok')"` printing `ok`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a Python snippet showing `record_dirs(repo_root,"plans")` includes `.aw/records/plans` and `record_dirs(repo_root,"bogus")==[]`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `_read_id`/`_read_status`/`_read_setid` returning the expected values for the sample lines in E-03's Expected outcome.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `resolve_one` results for the id6, status, setid, and filename-fragment cases over the fixture (each returns the expected plan path).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `resolve_selectors(...,["aaa111","bbb222"])` returning both paths sorted+deduped, and the empty-list case returning `[]`.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the `pytest tests/test_selectors.py -p no:xdist -q` result (6 passed) AND the tail of the full serial suite (`python3 -m pytest -p no:xdist`) showing no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the two new files
path-scoped (never `git add -A`), never pushes, and the plan moves to `.aw/records/plans/executed/`
only after `aw ipd lint --phase pre-transition` conforms and every V-item is `pass`. Order 01 of
awselect; Order 02 (aw show fix + status selection) depends on this module.
