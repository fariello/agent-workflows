# IPD: compact attention board with urgency and blocking columns

- Date: 2026-08-18
- Kind: child
- Concern: awdoctor Order 01 (TODO items 37, 36). The human attention board (`aw attention` colored view) repeats the full repo-relative path on every line, so a class of 15 backlog items prints its `.aw/records/backlog/...` prefix 15 times and the board is wide and noisy. Make the board COMPACT: group each attention class's items by their common directory prefix, print that prefix ONCE in the section header, then print BARE filenames underneath. Add a compact per-line urgency/age marker (from `Item.last_history_at`) and a blocking marker (from `Item.gate`). The machine surfaces (`--agent`/plain `[tree] path (status)` and `--format json`) MUST stay byte-identical (full paths, no new fields); only the colored human board is compacted.
- Scope: ONE edited module `agent_workflows/attention.py` (the `render_board` builder attention.py:436-517, its section-header line attention.py:486, and the two per-item line builders attention.py:507 (colored) + attention.py:515 (plain)) + ONE new test file `tests/test_attention_compact.py`. IN: header-prefix grouping + bare-filename lines + urgency + blocking markers in the COLORED branch of `render_board` only. OUT: any change to `scan`, to `render_json` (attention.py:362), to the plain/`--agent` line (attention.py:515) shape, to `attention_contract.py`, or to the CLI (attention.py:525+). No new Item fields; the markers derive from the EXISTING `Item.last_history_at` and `Item.gate`.
- Status: reviewed
- Set: awdoctor
- Order: 1
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: zi9kjl

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO items 1,33,36,37 (Set awdoctor).
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against attention.py:362/419/436-517; colored-branch isolation and machine output stability sound; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.

## Goal

Compact the colored human attention board so a class prints its common directory prefix once (in the
section header) and each item as a bare filename plus two tiny markers: an urgency/age glyph derived
from `Item.last_history_at` and a blocking glyph derived from `Item.gate`. Keep the plain/`--agent`
line (attention.py:515) and the JSON (attention.py:362) byte-for-byte unchanged so machines and grep
keep their fixed, full-path shape.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Do EXACTLY the steps below, in order. Edit ONLY `render_board` in
`agent_workflows/attention.py` (the colored branch) and create ONLY `tests/test_attention_compact.py`.
Do NOT touch `scan`, `render_json`, the plain-branch line at attention.py:515, `attention_contract.py`,
or the CLI. Use 4-space indentation; the file already has `from __future__ import annotations`. After
each code step, run the matching V-item command and paste its output.

### Task group 1: header-prefix grouping + bare filenames

- [ ] E-01 In `render_board` (attention.py:436), when `colored` is true, compute each class group's common directory prefix and print it in the section header, then print BARE filenames. Add a helper ABOVE `render_board` (after `_colorize_tree_segment`, near attention.py:434):
  ```python
  import posixpath

  def _common_dir_prefix(items: "List[Item]") -> str:
      """Longest common DIRECTORY prefix (POSIX) shared by every item's path, '' if none.

      Uses the directory of each path (never a partial filename), so the returned prefix always
      ends at a '/' boundary. Empty when the group spans more than one top directory.
      """
      dirs = [posixpath.dirname(it.path) for it in items]
      if not dirs:
          return ""
      common = posixpath.commonpath(dirs) if all(dirs) else ""
      return (common + "/") if common else ""
  ```
  Then, inside the `for cls in A.ATTENTION_CLASS_ORDER:` loop (attention.py:465), in the COLORED branch only, compute `prefix = _common_dir_prefix(group)` and append it to the header. Replace the header emit at attention.py:486 so the colored path reads:
  ```python
  if colored:
      prefix = _common_dir_prefix(group)
      prefix_txt = f" {prefix}" if prefix else ""
      lines.append(f"## {cls} ({len(group)}){header_extra}{prefix_txt}")
  else:
      lines.append(f"## {cls} ({len(group)}){header_extra}")
  ```
  Then in the colored per-item builder (attention.py:500-507) strip the shared prefix from the displayed path BEFORE coloring: after computing `path_txt = _colorize_tree_segment(term, it.path, it.tree)`, if `prefix and it.path.startswith(prefix)` compute the bare name `it.path[len(prefix):]` and colorize the tree segment of THAT bare remainder instead (call `_colorize_tree_segment(term, it.path[len(prefix):], it.tree)`); when the prefix already contains the `/tree/` segment the bare remainder is just the filename, which colorizes to itself unchanged. Emit `f"- {path_txt} ({status_txt}){inline_gate}"` as before (attention.py:507) with `path_txt` now the bare name. Do NOT change the plain `else` branch (attention.py:508-515): it still emits `f"- [{it.tree}] {it.path} ({status_word}){suffix}"` with the FULL path.
  - Depends on: none
  - Expected outcome: for a class whose items all live under `.aw/records/backlog/open/`, the colored header reads `## ready (N) .aw/records/backlog/open/` and each colored line is `- <bare-filename> (<status>)`; the plain/`--agent` line and JSON are unchanged.
  - Execution state: pending

### Task group 2: urgency + blocking markers

- [ ] E-02 In the COLORED per-item builder only (attention.py:500-507), add two compact leading markers derived from EXISTING Item fields, so the line becomes `- <blk><age> <bare> (<status>){inline_gate}`. Add a small helper ABOVE `render_board`:
  ```python
  import datetime as _dt

  def _age_marker(last_history_at: "Optional[str]") -> str:
      """One-char urgency glyph from an item's last-history ISO date (YYYY-MM-DD), '.' if unknown.

      Buckets by age: '!' > 30d (stale), '~' 8-30d, ' ' <= 7d (fresh), '.' when no history date.
      Pure: compares against datetime.date.today(); no mtime, no locale (dates are ISO strings).
      """
      if not last_history_at:
          return "."
      try:
          d = _dt.date.fromisoformat(last_history_at[:10])
      except ValueError:
          return "."
      age = (_dt.date.today() - d).days
      if age > 30:
          return "!"
      if age > 7:
          return "~"
      return " "

  def _block_marker(gate: "Optional[Dict[str, str]]") -> str:
      """'#' when the item carries a gate (blocked/gated), ' ' otherwise. Pure."""
      return "#" if gate else " "
  ```
  In the colored branch build `marker = _block_marker(it.gate) + _age_marker(it.last_history_at)` and emit `lines.append(f"- {marker} {path_txt} ({status_txt}){inline_gate}")`. Keep `inline_gate` (attention.py:501-506) exactly as-is (it still shows a differing gate ref for non-BLOCKED classes). Do NOT add markers to the plain branch (attention.py:508-515) and do NOT add fields to JSON.
  - Depends on: E-01
  - Expected outcome: a colored line for an item with a >30d `last_history_at` and no gate starts `- ! <bare> ...`; an item with a gate starts `- #<glyph> <bare> ...`; an item with `last_history_at=None` and no gate starts `-  . <bare> ...`; the plain line and JSON are unchanged.
  - Execution state: pending

### Task group 3: tests

- [ ] E-03 Create `tests/test_attention_compact.py` with a `unittest.TestCase` subclass `AttentionCompactTests` that builds a small `List[attention.Item]` in code (no disk fixture needed - `render_board` is pure over items+drift) and renders it three ways. Write EXACTLY these methods (build two READY items both under `.aw/records/backlog/open/` named `a.md` and `b.md`, one with `last_history_at` set 40 days before `datetime.date.today()` and one `None`; and one BLOCKED item with a `gate={"kind":"issue","ref":"#7"}`):
  - `test_colored_header_carries_common_prefix`: render with `term=T.Term(color=True)` (force color on); assert the READY header line contains `.aw/records/backlog/open/` and that the two READY item lines contain the BARE names `a.md`/`b.md` but do NOT repeat `.aw/records/backlog/open/a.md` verbatim.
  - `test_colored_markers`: in the colored render assert the 40-day item's line contains the stale glyph `!` and the gated item's line contains the blocking glyph `#`.
  - `test_plain_lines_keep_full_paths`: render with `term=T.Term(color=False)`; assert each line matches the stable `- [tree] <full-path> (<status>)` shape (e.g. contains `[backlog] .aw/records/backlog/open/a.md (`) and contains NO prefix-stripped bare-name line.
  - `test_json_unchanged`: `json.loads(attention.render_json(items, []))` has every item's `path` equal to its full repo-relative path and NO new keys beyond the existing set `{id,path,tree,native_status,attention_class,gate,last_history_at}`.
  Then run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02
  - Expected outcome: all four methods pass; full serial suite green (this Order only edits the colored render branch + adds one test file).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `render_board` (attention.py:436-517) has TWO branches keyed by `colored = bool(getattr(term, "color", False))` (attention.py:452): the colored HUMAN board and the plain MACHINE board. Only the colored branch is compacted here.
- Section header is emitted at attention.py:486 (`## {cls} ({len(group)}){header_extra}`); the colored per-item line at attention.py:507; the plain per-item line at attention.py:515 (`- [{it.tree}] {it.path} ({status_word}){suffix}`) - the latter is the STABLE grep/agent shape and must not change.
- `Item` (attention.py:34-42) already carries `path`, `tree`, `native_status`, `gate` (`Optional[Dict[str,str]]` with `kind`/`ref`), and `last_history_at` (`Optional[str]`, an ISO date from `A.last_history_at`, never mtime - attention_contract.py:434). No new field is needed; both markers derive from these.
- `render_json` (attention.py:362) emits a FIXED key set + fixed key order; determinism doc (attention.py:11-13) forbids timestamps/mtime/locale. The age marker uses `datetime.date.today()` for HUMAN display only, never in JSON.
- `_colorize_tree_segment` (attention.py:419) colors a `/tree/` segment in place and is a no-op when the segment is absent, so colorizing a bare filename is safe.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | The board already splits colored vs plain branches. | Compaction is confined to the colored branch; the machine shape is untouched by construction. |
| F2 | Both markers derive from existing `Item` fields (`last_history_at`, `gate`). | No `scan`/contract/JSON change; the change is render-only. |
| F3 | JSON determinism forbids mtime/timestamps. | The `today()` comparison lives ONLY in the human age glyph, never in JSON, so determinism of machine output is preserved. |

## Proposed changes (ordered, validatable)

1. `_common_dir_prefix` helper + colored header-prefix + bare-filename lines (E-01). 2. `_age_marker`/`_block_marker` helpers + compact markers on colored lines (E-02). 3. `tests/test_attention_compact.py` + full suite (E-03).

## Deferred / out of scope (with reason)

- Top-of-board notices for setup-needed / release-blockers: awdoctor Order 02.
- The aggregated `aw doctor` verb: awdoctor Order 03.
- Any change to `scan`, `render_json`, the plain line, `attention_contract.py`, or the CLI: explicitly OUT.

## Scope check

- Over-scope: none - one edited render branch + one new test file.
- Under-scope: none - prefix grouping, bare filenames, and BOTH markers are covered, and the machine-unchanged guarantee is tested (E-03 `test_plain_lines_keep_full_paths` + `test_json_unchanged`).

## Required tests / validation

`tests/test_attention_compact.py` (E-03, four named methods) + the full serial suite. Each V-item pins one E; V-03 additionally proves the machine surfaces are unchanged.

## Spec / documentation sync

No spec transition here (the orchestrator advances any spec when the Set completes). No AGENTS.md change: the board is a human-facing readout and the machine contract (`--agent`/JSON) is unchanged, so no documented interface moves.

## Open questions

### OQ-01: should the age buckets (7d / 30d) be configurable?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: NO - fixed 7d/30d buckets keep the marker deterministic and dependency-free for this Order. A configurable threshold is a follow-up if a user asks; it does not gate the compaction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python snippet rendering two same-directory READY items with `term=T.Term(color=True)` showing the header contains the common prefix `.aw/records/backlog/open/` and the item lines carry BARE names.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a colored render showing the stale-item line contains `!` and the gated-item line contains `#`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_attention_compact.py -p no:xdist -q` (4 passed) AND the tail of the full serial suite (`python3 -m pytest -p no:xdist`) showing no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the edited
`agent_workflows/attention.py` and the new `tests/test_attention_compact.py` path-scoped (never
`git add -A`), never pushes, and the plan moves to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every V-item is `pass`. Order 01 of awdoctor;
Orders 02 (notices) and 03 (`aw doctor`) build on this compacted board.
