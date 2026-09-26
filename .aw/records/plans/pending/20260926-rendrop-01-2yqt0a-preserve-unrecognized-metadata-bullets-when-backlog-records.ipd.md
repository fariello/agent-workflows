# IPD: Preserve unrecognized metadata bullets when backlog records are re-rendered

- Date: 2026-09-26
- Kind: child
- Concern: backlog._render_item rebuilds an existing item's metadata from a fixed template, so aw backlog set --status X <path> (and set_records.close_on_answer) silently drop every unrecognized field; Blocks-Release and Graduated-To survive only through per-field re-apply patches, and even they are moved.
- Scope: IN: source-order-preserving re-render in backlog._render_item; backlog.run_set and set_records.close_on_answer switched to it; the two per-field preservation patches removed; outcome tests; one CHANGELOG line. OUT: unifying the two spellings; the positional path's legacy Kind handling; new-record rendering (run_new, promote_question_to_backlog) unchanged.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/set_records.py, tests/test_backlog.py, CHANGELOG.md
- Item-Dependencies: executed:wd6npl
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: f2kqas
- Blocks-Release: next
- Set: rendrop
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2yqt0a

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog f2kqas: make backlog._render_item preserve unrecognized metadata bullets in source order and delete the per-field re-apply patches.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `backlog._render_item` preserve every metadata bullet it does not own, in its original position, whenever it re-renders an EXISTING record, so `aw backlog set --status X <path>` and `set_records.close_on_answer` stop silently dropping fields, and the per-field re-apply patches for `Blocks-Release` and `Graduated-To` can be deleted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Order-preserving render

- [ ] E-01 Add a keyword-only `source_text: Optional[str] = None` parameter to `backlog._render_item`. When it is None, behavior is unchanged (used by `run_new` and `set_records.promote_question_to_backlog`, which build new records). When it is given, build the metadata block by walking the source's leading bullet block (the same boundary `parse_item` uses: stop at the first `## ` or the first non-blank non-`- ` line) and, for each top-level `- Key: value` line: if Key is template-owned (`Id`, `Status`, `Set`, `Priority`, `Work-Kind`, legacy `Kind`, `Summary`, `Gate-Kind`, `Gate-Ref`) emit the template's value for that key IN PLACE (legacy `- Kind:` becomes `- Work-Kind:` in place, matching the existing "only the canonical spelling is ever WRITTEN" rule; `Gate-Kind`/`Gate-Ref` are dropped when `item.status != "blocked"`); otherwise emit the line verbatim. Template-owned lines absent from the source are inserted directly after `- Status:` (gate fields) or in template order at the end of the block (anything else), which matches where `status_set.apply_status_change` inserts gate fields.
  - Depends on: none
  - Expected outcome: re-rendering an item with `- Custom-Field: keepme`, `- Graduated-To: a, b`, `- Blocks-Release: next` keeps all three lines in their original positions; a new item renders byte-identically to HEAD.
  - Execution state: pending

- [ ] E-02 In `backlog.run_set`, call `_render_item(item, body, source_text=text)`. Delete the two PRESERVATION branches only: `elif item.blocks_release: ... set_blocks_release_line(rendered, item.blocks_release)` and `elif existing_gt: ... set_graduated_to_line(rendered, ", ".join(existing_gt))` (and the now-unused `existing_gt` read). Keep the explicit-flag writes (`if br is not None`, `if set_graduated_to is not None`), which are the flags' write mechanism shared with `status_set`, not preservation patches. Rewrite the two surrounding comments to state that preservation is now the renderer's property.
  - Depends on: E-01
  - Expected outcome: `--status` preserves every unknown field with no per-field code; `--blocks-release`/`--graduated-to` flags still set and clear.
  - Execution state: pending

- [ ] E-03 In `set_records.close_on_answer`, call `_backlog._render_item(item, body, source_text=text)` so the close keeps unknown fields (including `Blocks-Release`, which today is dropped on this path: a SILENT RELEASE-GATE DROP if it were ever called on a gated item).
  - Depends on: E-01
  - Expected outcome: `close_on_answer` on an item carrying `- Custom-Field:` and `- Blocks-Release:` keeps both.
  - Execution state: pending

### Task group 2: Outcome tests

- [ ] E-04 Add tests to `tests/test_backlog.py`: (a) BOTH SPELLINGS AGREE: two identical scratch repos, one item carrying `- Blocks-Release: <planned release id6>`, `- Custom-Field: keepme`, `- Graduated-To: foo` (canonical `Work-Kind` spelling); run `cli.main(["backlog","set",<path>,"--status","parked","--dir",r1])` and `cli.main(["backlog","set","parked",<id6>,"--yes","--no-commit","--dir",r2])`; assert the metadata blocks (text before `## Workflow history`) of the two results are EQUAL and contain all three fields; (b) `--status graduated --graduated-to bar` replaces the value and keeps `Custom-Field`; (c) `--blocks-release -` removes the gate and keeps `Custom-Field`; (d) `set_records.close_on_answer` on a blocked item with `- Custom-Field: keepme` and `- Blocks-Release:` keeps both lines in the `done/` result.
  - Depends on: E-02, E-03
  - Expected outcome: four tests passing; (a) and (d) fail on the base commit.
  - Execution state: pending

### Task group 3: Record and verify

- [ ] E-05 Add one `- Fixed:` line to `## 2.0.0 (pending)` in `CHANGELOG.md`: `aw backlog set <item> --status <s>` no longer deletes metadata lines it does not recognize (for example a custom field, and previously any field without its own workaround); the item now keeps them where they were. No em or en dashes.
  - Depends on: E-02
  - Expected outcome: one new line, no dashes.
  - Execution state: pending

- [ ] E-06 Run the bare suite `python3 -m pytest`, `python3 -m agent_workflows check backlog --agent` (to confirm no live item is made non-conforming by a re-render), and `aw sanitize --agent`.
  - Depends on: E-04, E-05
  - Expected outcome: 0 failed; no new finding naming a touched file.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `backlog._render_item` is the fixed-template renderer; `status_set.apply_status_change` is the surgical line editor used by the positional spelling and preserves unknown lines by construction.
- The shared idempotent line writers in `releases` (`set_blocks_release_line`, `set_graduated_to_line`, `set_priority_line`, `set_work_kind_line`) strip then insert after `- Status:`; they are the ONE write mechanism per field for both spellings, and stay.
- Only the canonical `- Work-Kind:` spelling is ever written by `_render_item` (the "E-02: only the canonical spelling is ever WRITTEN" comment); the positional path leaves a legacy `- Kind:` untouched. So "identical metadata blocks" holds for canonical-spelling items; this plan does not change the positional path's legacy handling.
- Tests: outcome only (maintainer standing rule); no test pins renderer source, template lists, or comments.
- Commit via `aw commit 2yqt0a -- <paths>`; never push. Line numbers are at HEAD `92679444` and approximate.

## Findings

| # | Location (HEAD 92679444) | Finding |
| --- | --- | --- |
| F-1 | `backlog._render_item` (~:630-650) | Confirmed: emits exactly `Id, Status, Set, Priority, Work-Kind, Summary` plus `Gate-Kind`/`Gate-Ref` when blocked. The brief's ~:624-644 is now ~:630-650 (HEAD moved by `ooydp3`, which added a `config` import). |
| F-2 | scratch repo, measured at authoring | `- Custom-Field: keepme` survives `aw backlog set parked <id6>` (positional) and is dropped by `aw backlog set <path> --status parked`. The `--status` result also MOVED `- Graduated-To:` and `- Blocks-Release:` to directly after `- Status:` (the line writers' insert point), so even the patched fields do not keep their position. |
| F-3 | `backlog.run_set` `elif item.blocks_release:` (~:1093) and `elif existing_gt:` (~:1119) | Confirmed: the two per-field preservation patches. The brief's ~:1082-1090 / ~:1108-1114 shifted by ~6. |
| F-4 | `set_records.close_on_answer` (~:317-346) | Confirmed: `_backlog._render_item(item, body)` with no re-apply at all, so it drops EVERY field outside the template, `Blocks-Release` included. `grep -rn close_on_answer agent_workflows tests` finds no caller outside its own module docstring. Fixed anyway (brief), since it is one argument. |
| F-5 | design choice | "Re-emit unknown bullets in original order" alone is NOT enough to make the two spellings produce identical blocks: appending the unknowns after the template would still move `Blocks-Release` (which sits after `Status` in both the positional output and the line writer's insert point). The chosen render walks the SOURCE block in order and substitutes template-owned values in place, which is what makes the blocks identical. |
| F-6 | OQ-01 alternative | Routing `--status` through `status_set.apply_status_change` was rejected: that path does not run `check_engine.evaluate_blocking_close`, `decide_gate_default`, or `--evidence` (measured; see plan `wd6npl` F-7), so it would drop the release-gate close refusal. |

## Proposed changes (ordered, validatable)

1. E-01 renderer gains source-order preservation.
2. E-02 `run_set` uses it and loses the two preservation patches.
3. E-03 `close_on_answer` uses it.
4. E-04 outcome tests; E-05 CHANGELOG; E-06 verify.

## Deferred / out of scope (with reason)

- The backlog item's wider audit of "every other record renderer that rebuilds a metadata block from a fixed field list".
  - Carrier-Declined: audited at authoring. `grep -n "_render_item(" agent_workflows/*.py` shows the only other re-render of an EXISTING record is `close_on_answer` (fixed here); `run_new` and `promote_question_to_backlog` render NEW records, and `specs.run_set` edits lines surgically (`_set_status`, `_append_history`). No further renderer of this class exists at HEAD.
- Unifying the two spellings of `aw backlog set`.
  - Carrier-Declined: blocked by the positional path's missing close gate (F-6); this plan makes the two agree on metadata preservation, which the E-04(a) test pins as an outcome.
- The positional spelling leaving a legacy `- Kind:` line un-canonicalized.
  - Carrier-Declined: pre-existing, both spellings still produce a readable item (`parse_item` dual-reads), and changing the positional writer is outside this defect.

## Scope check

- Over-scope: none.
- Under-scope: none known. `promote_question_to_backlog` and `run_new` deliberately keep the `source_text=None` behavior.

## Required tests / validation

Outcome tests only (maintainer standing rule): four tests in `tests/test_backlog.py` assert what a user sees in the written file (fields present, blocks equal across spellings), driven through `cli.main` for the two spellings and through `set_records.close_on_answer` directly (it has no CLI). No test pins the template list or renderer code. Run the suite BARE: `python3 -m pytest`.

## Spec / documentation sync

No `.spec.md` is amended: no spec states that `aw backlog set` may drop fields; the backlog record contract (`.aw/records/backlog/README.md`) already treats extra fields (`Blocks-Release`, `Graduated-To`, `From-*`) as part of the record, so preserving them makes the implementation match it. `CHANGELOG.md` gains one line (E-05).

## Open questions

### OQ-01: Preserve in the renderer, or route --status through status_set.apply_status_change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Preserve in the renderer (source-order walk). Routing through `apply_status_change` would lose the release-gate close refusal, the bug gate default, and `--evidence`, which only `backlog.run_set` implements (F-6, measured). The source-order walk also makes the metadata blocks of the two spellings identical (F-5), which a template-then-extras append would not.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c` output rendering one item twice, once with `source_text=None` and once with a source containing `- Custom-Field: keepme` between `Priority` and `Work-Kind`: the first matches the HEAD template exactly, the second shows `Custom-Field` still between `Priority` and `Work-Kind`. Also paste `aw backlog new ... --apply` output file from a scratch repo compared with `diff` against the same command at the base commit showing no difference other than the id6 and date.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the F-2 reproduction re-run in a scratch repo: `diff` of the metadata blocks produced by `aw backlog set <path> --status parked` and `aw backlog set parked <id6> --yes --no-commit` printing nothing, and `grep -c "Custom-Field\|Graduated-To\|Blocks-Release"` on the `--status` result printing 3. Paste `git diff` of `backlog.run_set` showing the two `elif` preservation branches removed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a `python3 -c` call of `set_records.close_on_answer` on a scratch blocked item carrying `- Custom-Field: keepme` and `- Blocks-Release: next`, followed by `head -12` of the returned `done/` path showing both lines.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_backlog.py -o addopts="" -q -k "preserve or spelling or close_on_answer"` showing 4 passed, and the same tests run against the base commit (copy the test file into `git worktree add /tmp/opencode/base <base-sha>`) showing (a) and (d) FAIL.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff CHANGELOG.md` showing one added `- Fixed:` line under `## 2.0.0 (pending)` and `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed (any failure named as pre-existing with node id and base-commit evidence, or new), and the exit codes of `python3 -m agent_workflows check backlog --agent` (no new finding) and `aw sanitize --agent` (0).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one defect class (a fixed-template re-render dropping fields) fixed at its single root, `_render_item`, with its two existing-record callers switched over and the per-field workarounds deleted.

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a change to how `aw backlog set --status` rewrites a backlog item (unknown fields now kept in place; the positions of `Blocks-Release`/`Graduated-To` now match the positional spelling instead of being moved under `Status`), the same for the unused `close_on_answer`, four outcome tests, one CHANGELOG line.

ORDERING: `- Item-Dependencies: executed:wd6npl`. Plan `wd6npl` (bklgdryrun) edits the same function (`backlog.run_set`, the sidecar block and write guard); execute this after it. The runner enforces the edge.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`; within `backlog.py` only `_render_item` and `run_set`, within `set_records.py` only `close_on_answer`. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Genuine stop condition: a co-worker's concurrent edit to `backlog.run_set` that cannot be safely combined.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit 2yqt0a -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize 2yqt0a --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). This plan inherits `- Blocks-Release: next` from `f2kqas`; after execution set `f2kqas` `done` with `--evidence` citing the executed plan.
