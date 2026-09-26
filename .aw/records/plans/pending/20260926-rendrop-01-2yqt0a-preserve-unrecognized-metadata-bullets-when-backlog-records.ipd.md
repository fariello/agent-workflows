# IPD: Preserve unrecognized metadata bullets when backlog records are re-rendered

- Date: 2026-09-26
- Kind: child
- Concern: backlog._render_item rebuilds an existing item's metadata from a fixed template, so aw backlog set --status X <path> (and set_records.close_on_answer) silently drop every unrecognized field AND every line of prose written before the ## Workflow history heading; Blocks-Release and Graduated-To survive only through per-field re-apply patches, and even they are moved.
- Scope: IN: source-order-preserving re-render in backlog._render_item, including the pre-history prose region; backlog.run_set and set_records.close_on_answer switched to it; a release-gate refusal on close_on_answer so its new preservation cannot manufacture a done item with a live gate; the two per-field preservation patches removed; outcome tests; two CHANGELOG lines. OUT: unifying the two spellings; the positional path's legacy Kind handling; new-record rendering (run_new, promote_question_to_backlog) unchanged; new validate_item rules for a duplicate bullet or a stale Gate-Summary; widening the commit-staged scope of check.blocking-item-closed-without-gate.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/set_records.py, tests/test_backlog.py, CHANGELOG.md
- Item-Dependencies: executed:wd6npl
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: f2kqas
- Blocks-Release: next
- Set: rendrop
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2yqt0a

## Workflow history
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed in place
- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED in place. Added E-07 (preserve prose written before `## Workflow history`, the larger destruction the plan left unfixed: 6 live items, one losing 2620 of 3063 bytes), E-08 (gate `close_on_answer`'s close on `evaluate_blocking_close`, because E-03's preservation otherwise manufactures a `done` item with a live release gate that no shipped check sees), E-09 (four tests for the added defects), four hard rules on E-01's walk (dedupe the two kind spellings, drop a non-blocked `Gate-Summary`, pass an unparseable bullet through, never reorder), `--no-commit` on every `cli.main` in the tests, V-07/V-08/V-09, and F-7..F-12. Watermark 06 -> 09.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog f2kqas: make backlog._render_item preserve unrecognized metadata bullets in source order and delete the per-field re-apply patches.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `backlog._render_item` preserve every metadata bullet it does not own, in its original position, whenever it re-renders an EXISTING record, so `aw backlog set --status X <path>` and `set_records.close_on_answer` stop silently dropping fields, and the per-field re-apply patches for `Blocks-Release` and `Graduated-To` can be deleted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Order-preserving render

- [ ] E-01 Add a keyword-only `source_text: Optional[str] = None` parameter to `backlog._render_item`. When it is None, behavior is unchanged (used by `run_new` and `set_records.promote_question_to_backlog`, which build new records). When it is given, build the metadata block by walking the source's leading bullet block (the same boundary `parse_item` uses: stop at the first `## ` or the first non-blank non-`- ` line) and, for each top-level `- Key: value` line: if Key is template-owned (`Id`, `Status`, `Set`, `Priority`, `Work-Kind`, legacy `Kind`, `Summary`, `Gate-Kind`, `Gate-Ref`) emit the template's value for that key IN PLACE, otherwise emit the line verbatim. Template-owned lines absent from the source are inserted directly after `- Status:` (gate fields) or in template order at the end of the block (anything else), which matches where `status_set.apply_status_change` inserts gate fields.
  - FOUR RULES THE WALK MUST OBEY, each fixing a defect this shape would otherwise introduce (review PR-002, PR-003, PR-005; all measured, see F-7/F-8/F-10):
  - (1) EMIT EACH TEMPLATE-OWNED KEY AT MOST ONCE. An item carrying BOTH `- Kind: chore` and `- Work-Kind: bug` is legal today (`parse_item` dual-reads, canonical wins, `validate_item` reports nothing: measured) and a naive in-place substitution emits `- Work-Kind: bug` TWICE, which `validate_item` also does not catch (measured). Track emitted keys; the legacy `- Kind:` line is substituted in place ONLY when no `- Work-Kind:` line was already emitted for it, and is otherwise DROPPED.
  - (2) DROP A GATE FIELD WHEN THE ITEM IS NOT `blocked`, AND DROP `Gate-Summary` THE SAME WAY. `Gate-Kind`/`Gate-Ref` are dropped when `item.status != "blocked"` (as HEAD's template already does). `- Gate-Summary:` is NOT template-owned and NOT on `BacklogItem.__slots__`, yet `aw set blocked <item> --gate-summary ...` writes one onto a backlog item (measured, F-8), so a verbatim walk would PRESERVE a stale gate summary onto a `done` item and `validate_item` would not flag it (it tests only `gate_kind`/`gate_ref`: measured, zero drift). Treat `Gate-Summary` as a gate field for the drop rule: keep it in place when `item.status == "blocked"`, drop it otherwise. Use the shared `attention_contract.GATE_SUMMARY_RE`, never a fresh pattern.
  - (3) AN UNPARSEABLE BULLET IS EMITTED VERBATIM, NOT DROPPED. The walk must key on `- Key: value` shape; a bullet that does not match (a continuation line, an indented sub-bullet, a bare `- text` line) is passed through unchanged, so the renderer never becomes a second silent-drop path.
  - (4) DO NOT REORDER WHAT THE SOURCE ALREADY ORDERED. The insert points above apply only to a key ABSENT from the source; a key present in the source keeps its source position even when that differs from the template order. This is the property F-5 identifies as what makes the two spellings agree.
  - Depends on: none
  - Expected outcome: re-rendering an item with `- Custom-Field: keepme`, `- Graduated-To: a, b`, `- Blocks-Release: next` keeps all three lines in their original positions; a new item (`source_text=None`) renders byte-identically to HEAD; an item carrying both `- Kind:` and `- Work-Kind:` emits exactly one `- Work-Kind:`; a non-`blocked` item's `- Gate-Summary:` is dropped.
  - Execution state: pending

- [ ] E-07 FIX THE HEADER-PROSE DESTRUCTION THIS PLAN WOULD OTHERWISE LEAVE IN PLACE (review PR-001, measured F-9). `_strip_metadata_and_history` returns ONLY the text AFTER the history block, so any prose between the metadata bullets and `## Workflow history` is DELETED by every `--status` write. Measured on the live tree: 6 of 620 items carry such prose, and re-rendering `20260919-a3ugp1-01-a3ugp1-...` through `_render_item` + `_reattach_history` shrank it from 3063 to 443 bytes, destroying the entire bug report while the positional spelling preserved it. Fix INSIDE `_render_item`'s `source_text` walk, which is the one place that already has the source text: capture the source region between the end of the leading bullet block and the `## Workflow history` heading and re-emit it, verbatim, between the metadata block and that heading. When `source_text` is None nothing changes. Do NOT widen `_strip_metadata_and_history` instead: `_reattach_history` splits on `"\n## Workflow history"` and reassembles head + history + trailing body, so a body returned from that function lands AFTER the history block and would relocate the prose rather than preserve it.
  - Depends on: E-01
  - Expected outcome: `aw backlog set <path> --status parked` on an item with prose before `## Workflow history` preserves that prose in place, byte for byte; the metadata block plus that prose region matches what the positional spelling produces.
  - Execution state: pending

- [ ] E-08 CLOSE THE RELEASE-GATE HOLE E-03 OPENS, rather than opening it (review PR-004, measured F-11). E-03 makes `close_on_answer` PRESERVE `- Blocks-Release:` while transitioning an item to `done`. That is the right preservation and the wrong outcome on its own: it manufactures exactly the `done` + live-gate state `check_engine.evaluate_blocking_close` exists to refuse, and the shipped backstop cannot see it (measured: `evaluate_blocking_close` returns `legitimate=False, severity='error'` on such an item, while `check_release_gates` and `check_release_gate_consistency` both return ZERO findings on the same tree, because rule 1 is commit-staged-scoped and `close_on_answer` never stages). So in `close_on_answer`, after rendering and BEFORE `core.atomic_write`, call `check_engine.evaluate_blocking_close(repo_root, backlog_path, "done", item_text=rendered)` and, when the verdict is `not legitimate and severity == "error"`, RAISE `ValueError` carrying `verdict.reason` and `verdict.fixes` and write nothing. This function has no CLI and already raises `ValueError` on a validation failure in its sibling `promote_question_to_backlog`, so raising is its established refusal shape; do not invent an exit code here.
  - Depends on: E-03
  - Expected outcome: `close_on_answer` on a gated item with no handoff and no evidence raises `ValueError` naming the gate and writes no file; on an ungated item, or one whose gate is handed off to a `From-Backlog` carrier, it closes as before.
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

- [ ] E-04 Add tests to `tests/test_backlog.py` for the PRESERVATION surface: (a) BOTH SPELLINGS AGREE: two identical scratch repos, one item carrying `- Blocks-Release: <planned release id6>`, `- Custom-Field: keepme`, `- Graduated-To: foo` (canonical `Work-Kind` spelling); run `cli.main(["backlog","set",<path>,"--status","parked","--dir",r1,"--no-commit"])` and `cli.main(["backlog","set","parked",<id6>,"--yes","--no-commit","--dir",r2])`; assert the metadata blocks (text before `## Workflow history`) of the two results are EQUAL and contain all three fields; (b) `--status graduated --graduated-to bar` replaces the value and keeps `Custom-Field`; (c) `--blocks-release -` removes the gate and keeps `Custom-Field`; (d) `set_records.close_on_answer` on a blocked item with `- Custom-Field: keepme` and an ALREADY-HANDED-OFF `- Blocks-Release:` (a `From-Backlog` carrier plan with the same gate, so E-08 permits the close) keeps both lines in the `done/` result. PASS `--no-commit` ON EVERY `cli.main` CALL: `_add_commit_flags` is declared on this parser and `--yes` is read as commit consent (`_offer_records_commit`'s `assume_yes`), so a test that omits it can self-commit into the fixture repo (spelling A silently skipped the commit in a scratch repo only because HEAD was unresolvable: measured at review, F-12).
  - Depends on: E-02, E-03
  - Expected outcome: four tests passing; (a) and (d) fail on the base commit.
  - Execution state: pending

- [ ] E-09 Add the tests for the THREE defects review added, in `tests/test_backlog.py` (and `tests/test_set_records.py` if that is where `set_records` is exercised; otherwise keep them beside (d) in `tests/test_backlog.py`): (a) HEADER PROSE SURVIVES (E-07): an item carrying a paragraph between its bullets and `## Workflow history` goes through `cli.main(["backlog","set",<path>,"--status","parked","--dir",r,"--no-commit"])` and the paragraph is still there, in place; assert against the positional spelling's output too, since that path already preserves it; (b) NO DUPLICATE `Work-Kind` (E-01 rule 1): an item carrying both `- Kind: chore` and `- Work-Kind: bug` re-renders with exactly ONE `- Work-Kind:` line; (c) STALE `Gate-Summary` IS DROPPED (E-01 rule 2): a `blocked` item carrying `- Gate-Summary:` transitioned to `done` comes out with no `Gate-Summary` line; (d) GATED CLOSE REFUSED (E-08): `close_on_answer` on an item carrying `- Blocks-Release: <planned>` with no `From-Backlog` carrier and no evidence raises `ValueError`, and the item is STILL in `blocked/` with its bytes unchanged.
  - Depends on: E-07, E-08
  - Expected outcome: four tests passing; all four fail on the base commit (the first three because the behavior does not exist, the fourth because `close_on_answer` at base drops the gate entirely rather than refusing).
  - Execution state: pending

### Task group 3: Record and verify

- [ ] E-05 Add `- Fixed:` lines to `## 2.0.0 (pending)` in `CHANGELOG.md` covering BOTH user-visible losses this plan stops: (1) `aw backlog set <item> --status <s>` no longer deletes metadata lines it does not recognize (for example a custom field, and previously any field without its own workaround); the item now keeps them where they were; (2) it no longer deletes prose written between an item's metadata bullets and its `## Workflow history` heading (E-07), which is the larger of the two losses (thousands of bytes of a bug report, measured). No em or en dashes.
  - Depends on: E-02, E-07
  - Expected outcome: two new lines, no dashes.
  - Execution state: pending

- [ ] E-06 Run the bare suite `python3 -m pytest`, `python3 -m agent_workflows check backlog --agent` (to confirm no live item is made non-conforming by a re-render), and `aw sanitize --agent`.
  - Depends on: E-04, E-05, E-09
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
| F-7 | review, `backlog.parse_item:342-356` + `validate_item:427-462` | AN ITEM MAY CARRY BOTH SPELLINGS OF THE KIND FIELD AND NOTHING FLAGS IT. Measured: an item with `- Kind: chore` AND `- Work-Kind: bug` parses to `kind='bug'` (canonical wins, by design) and `validate_item` returns `[]`. A naive in-place substitution therefore emits `- Work-Kind: bug` TWICE, and `validate_item` returns `[]` on THAT too (measured). Hence E-01 rule (1). |
| F-8 | review, the `--gate-summary` flag on `aw set` (`cli.py`, `"--gate-summary", dest="gate_summary"` on the untyped `p_set` parser) + `status_set.apply_status_change` (the `gate_status = _GATE_STATUS_BY_TYPE.get(rec.record_type)` branch) + `backlog.BacklogItem.__slots__` | `- Gate-Summary:` REACHES A BACKLOG ITEM AND IS NOT TEMPLATE-OWNED. `aw set blocked <item> --gate-kind ... --gate-ref ... --gate-summary ...` wrote `- Gate-Summary: waiting on a ruling` onto a backlog item (measured, exit 0), because `status_set._GATE_STATUS_BY_TYPE` maps `"backlog": "blocked"` and the gate-write branch emits all three lines (`gate_lines.append(f"- Gate-Summary: {gs}")`). It is absent from `BacklogItem.__slots__`, so a verbatim walk would preserve it onto a `done` item; `validate_item` on such an item returns `[]` (measured), so nothing would catch it. Hence E-01 rule (2). |
| F-9 | review, `backlog._strip_metadata_and_history:1301-1316` + live tree | THE PLAN AS AUTHORED LEAVES A LARGER DESTRUCTION UNFIXED THAN THE ONE IT FIXES. `_strip_metadata_and_history` returns only the text AFTER the history block, so prose between the bullets and `## Workflow history` is deleted by every `--status` write. 6 of 620 live items carry such prose (measured by scanning the tree). Re-rendering `.aw/records/backlog/open/20260919-a3ugp1-01-a3ugp1-approval-gate-refuses-askme-resolved-plans.backlog.md` through `_render_item` + `_reattach_history` took it from 3063 bytes to 443, destroying the whole bug report; the positional spelling preserved it. That is a strictly worse loss than a dropped one-line field, and it is the same defect (a fixed-template rebuild discarding what it does not own). Hence E-07. |
| F-10 | review, `backlog.parse_item:321-328` | THE BULLET-BLOCK BOUNDARY IS SHARED AND MUST NOT BE RE-DERIVED. `parse_item` stops at the first `## ` or the first non-blank line that does not start with `- `; an INDENTED sub-bullet therefore ENDS the block (measured: a `  - indented sub bullet` under `- Summary:` stopped the scan, so a later `- Custom-Field:` was never parsed). E-01's walk must use this same boundary and pass a non-matching bullet through verbatim (rule 3), or it becomes a second silent-drop path. |
| F-11 | review, `set_records.close_on_answer:317-346` + `check_engine.check_release_gate_consistency:4029-4055` | E-03 AS AUTHORED OPENS A RELEASE-GATE HOLE INSTEAD OF CLOSING ONE. Preserving `- Blocks-Release:` through a transition to `done` manufactures exactly the state `evaluate_blocking_close` refuses, and the shipped backstop CANNOT see it: measured on a scratch tree, `evaluate_blocking_close` returned `legitimate=False, severity='error'` on such an item while `check_release_gates` and `check_release_gate_consistency` both returned ZERO findings, because rule 1 iterates `_staged_backlog_done_items` (commit-staged only, grandfathering everything else) and `close_on_answer` never stages. Today the field is dropped, which is a different bug and not this one. Hence E-08. |
| F-12 | review, `cli._add_commit_flags(p_backlog_set)` (commented `# selfcommit jgcm68 E-01/E-05`) + `cli._offer_records_commit` (its `assume_yes = bool(getattr(args, "commit", False) or (getattr(args, "yes", False) and not is_agent_or_json))`) | E-04's ORIGINAL SPELLING A COULD SELF-COMMIT INTO THE FIXTURE. `_offer_records_commit` treats `--yes` as commit consent (`assume_yes`) and `--commit` outright. In a scratch repo with no initial commit the commit merely warned ("cannot resolve HEAD"), so the omission looked harmless; in a fixture that DOES commit (the shape `tests/test_specs_status_dirs.py` uses) it would commit. Every `cli.main` in E-04/E-09 therefore passes `--no-commit`. |

## Proposed changes (ordered, validatable)

1. E-01 renderer gains source-order preservation, under the four rules (dedupe the kind spellings, drop a non-blocked gate field including `Gate-Summary`, pass an unparseable bullet through, never reorder what the source ordered).
2. E-07 the same renderer preserves prose written before `## Workflow history` (the larger loss, F-9).
3. E-02 `run_set` uses it and loses the two preservation patches.
4. E-03 `close_on_answer` uses it; E-08 gates its close on `evaluate_blocking_close` so preservation does not manufacture a dropped release gate (F-11).
5. E-04 and E-09 outcome tests; E-05 CHANGELOG; E-06 verify.

## Deferred / out of scope (with reason)

- The backlog item's wider audit of "every other record renderer that rebuilds a metadata block from a fixed field list".
  - Carrier-Declined: audited at authoring. `grep -n "_render_item(" agent_workflows/*.py` shows the only other re-render of an EXISTING record is `close_on_answer` (fixed here); `run_new` and `promote_question_to_backlog` render NEW records, and `specs.run_set` edits lines surgically (`_set_status`, `_append_history`). No further renderer of this class exists at HEAD.
- Unifying the two spellings of `aw backlog set`.
  - Carrier-Declined: blocked by the positional path's missing close gate (F-6); this plan makes the two agree on metadata preservation, which the E-04(a) test pins as an outcome.
- The positional spelling leaving a legacy `- Kind:` line un-canonicalized.
  - Carrier-Declined: pre-existing, both spellings still produce a readable item (`parse_item` dual-reads), and changing the positional writer is outside this defect.
- A `validate_item` rule for a DUPLICATE metadata bullet, or for a `Gate-Summary` on a non-blocked item.
  - Deferred (review PR-002/PR-003): measured at review that `validate_item` returns `[]` for BOTH states (F-7, F-8), so neither is caught anywhere today. This plan makes its own renderer never produce them (E-01 rules 1 and 2), which is the part it owns. Adding validator rules would flag whatever pre-existing items carry those shapes and belongs in its own item; the live tree carries none today (measured: `aw check backlog --agent` conforms, and the field census over 620 items shows only `Gate-Kind`/`Gate-Ref` twice and no `Gate-Summary` at all). FILE A BACKLOG ITEM for the two validator rules when this plan executes; not gating.
- Making `check.blocking-item-closed-without-gate` see a close that was never git-staged.
  - Deferred (review PR-004): the rule is commit-staged-scoped BY DESIGN and its own comment states the grandfathering rationale, so widening it is a policy change with a corpus-wide blast radius, not a fix inside this defect. E-08 closes the hole this plan would otherwise open by gating at the writer instead, which is where `backlog.run_set` already gates.

## Scope check

- Over-scope: none. E-07 and E-08 are additions review made, and both are the SAME defect at the SAME root: E-07 is a fixed-template rebuild discarding source content it does not own (the exact concern in `- Concern:`, measured larger than the field loss), and E-08 is the release-gate consequence of E-03's preservation, which this plan introduces and must therefore own.
- Under-scope: none known after review. `promote_question_to_backlog` and `run_new` deliberately keep the `source_text=None` behavior.

## Required tests / validation

Outcome tests only (maintainer standing rule): eight tests (four in E-04 for the preservation surface, four in E-09 for the defects review added) assert what a user sees in the written file (fields present, prose present, no duplicate bullet, no stale gate summary, blocks equal across spellings, a refused gated close leaving the file untouched), driven through `cli.main` for the two spellings and through `set_records.close_on_answer` directly (it has no CLI). Every `cli.main` call passes `--no-commit` (F-12). No test pins the template list or renderer code. Run the suite BARE: `python3 -m pytest`.

## Spec / documentation sync

No `.spec.md` is amended: no spec states that `aw backlog set` may drop fields or prose; the backlog record contract (`.aw/records/backlog/README.md`) already treats extra fields (`Blocks-Release`, `Graduated-To`, `From-*`) as part of the record, so preserving them makes the implementation match it. `CHANGELOG.md` gains two lines (E-05).

## Open questions

### OQ-01: Preserve in the renderer, or route --status through status_set.apply_status_change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Preserve in the renderer (source-order walk). Routing through `apply_status_change` would lose the release-gate close refusal, the bug gate default, and `--evidence`, which only `backlog.run_set` implements (F-6, measured). The source-order walk also makes the metadata blocks of the two spellings identical (F-5), which a template-then-extras append would not.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c` output rendering one item twice, once with `source_text=None` and once with a source containing `- Custom-Field: keepme` between `Priority` and `Work-Kind`: the first matches the HEAD template exactly, the second shows `Custom-Field` still between `Priority` and `Work-Kind`. Also paste `aw backlog new ... --apply` output file from a scratch repo compared with `diff` against the same command at the base commit showing no difference other than the id6 and date. PLUS one render per rule: (1) a source carrying BOTH `- Kind: chore` and `- Work-Kind: bug` renders with `grep -c '^- Work-Kind:'` printing exactly `1`; (2) a `- Gate-Summary:` line on an item rendered with `item.status == "done"` is ABSENT from the output and PRESENT when rendered `blocked`; (3) a source whose bullet block contains a non-`Key: value` bullet renders that bullet verbatim (paste both input and output); (4) a source ordering `Summary` BEFORE `Priority` renders in that same source order, not template order.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the F-2 reproduction re-run in a scratch repo: `diff` of the metadata blocks produced by `aw backlog set <path> --status parked` and `aw backlog set parked <id6> --yes --no-commit` printing nothing, and `grep -c "Custom-Field\|Graduated-To\|Blocks-Release"` on the `--status` result printing 3. Paste `git diff` of `backlog.run_set` showing the two `elif` preservation branches removed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a `python3 -c` call of `set_records.close_on_answer` on a scratch blocked item carrying `- Custom-Field: keepme` and a HANDED-OFF `- Blocks-Release: next` (a `From-Backlog` carrier plan with the same gate present in the fixture, so E-08 permits the close), followed by `head -12` of the returned `done/` path showing both lines.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_backlog.py -o addopts="" -q -k "preserve or spelling or close_on_answer"` showing 4 passed, and the same tests run against the base commit (copy the test file into `git worktree add /tmp/opencode/base <base-sha>`) showing (a) and (d) FAIL.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff CHANGELOG.md` showing two added `- Fixed:` lines under `## 2.0.0 (pending)` (one for the dropped fields, one for the dropped header prose) and `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed (any failure named as pre-existing with node id and base-commit evidence, or new), and the exit codes of `python3 -m agent_workflows check backlog --agent` (no new finding) and `aw sanitize --agent` (0).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the F-9 reproduction AFTER the fix, on a COPY of the real item (never mutate the tracked tree): copy `.aw/records/backlog/open/20260919-a3ugp1-01-a3ugp1-approval-gate-refuses-askme-resolved-plans.backlog.md` into a scratch repo, run `aw backlog set <copy> --status parked --dir <scratch> --no-commit`, and paste `wc -c` before and after showing the size preserved (3063 bytes of content retained, not 443), plus a `diff` of the region between the metadata block and `## Workflow history` in the before and after files printing NOTHING. Also paste the same item through the POSITIONAL spelling in a second scratch repo and `diff` the two results' pre-history regions, printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste a `python3 -c` call of `set_records.close_on_answer` on a scratch `blocked` item carrying `- Blocks-Release: <planned release id6>` with NO `From-Backlog` carrier and no evidence: the call must raise `ValueError` (paste the traceback's final line showing the gate named), `ls` of the `done/` dir must show it EMPTY, and `sha256sum` of the source item must be unchanged from before the call. Then paste the SAME call with a `From-Backlog` carrier plan present, succeeding and returning a `done/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `python3 -m pytest tests/test_backlog.py -o addopts="" -q -k "header_prose or duplicate_work_kind or gate_summary or gated_close"` (adjust the `-k` to the real test names) showing 4 passed, and the same four run against the base commit worktree showing ALL FOUR fail. Name each failure's reason in one line so a reader can see the test detects the defect rather than a fixture error.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one defect class (a fixed-template re-render discarding source content it does not own) fixed at its single root, `_render_item`, with its two existing-record callers switched over and the per-field workarounds deleted. The two items review added stay inside that cohesion: E-07 is the SAME discarding at the SAME root applied to prose instead of a field (measured larger, F-9), and E-08 is the release-gate consequence of E-03's own preservation, which this plan introduces and so must own (F-11).

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a change to how `aw backlog set --status` rewrites a backlog item, in three parts. (1) Unknown metadata fields are now KEPT IN PLACE, and the positions of `Blocks-Release`/`Graduated-To` now match the positional spelling instead of being moved under `Status`, so the two spellings of one verb agree. (2) Prose written between an item's metadata bullets and its `## Workflow history` heading is no longer DELETED; 6 live items carry such prose today and one of them loses 2620 of its 3063 bytes on any `--status` write (measured, F-9). (3) `set_records.close_on_answer` (no CLI caller today) both preserves unknown fields AND gains a release-gate refusal, so preserving `Blocks-Release` through a close cannot silently manufacture a `done` item carrying a live gate that no shipped check can see (measured, F-11). Plus eight outcome tests and two CHANGELOG lines.

ORDERING: `- Item-Dependencies: executed:wd6npl`. Plan `wd6npl` (bklgdryrun) edits the same function (`backlog.run_set`, the sidecar block and write guard); execute this after it. The runner enforces the edge.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`; within `backlog.py` only `_render_item` and `run_set`, within `set_records.py` only `close_on_answer`. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Genuine stop condition: a co-worker's concurrent edit to `backlog.run_set` that cannot be safely combined.

DO NOT MUTATE A TRACKED BACKLOG ITEM WHILE VALIDATING. V-07 names a real item as its fixture; COPY it into a scratch repo. The tracked tree is not a test fixture and `.aw/records/backlog/` is outside this plan's `- Scope-Paths:`.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit 2yqt0a -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize 2yqt0a --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). This plan inherits `- Blocks-Release: next` from `f2kqas`; after execution set `f2kqas` `done` with `--evidence` citing the executed plan.
