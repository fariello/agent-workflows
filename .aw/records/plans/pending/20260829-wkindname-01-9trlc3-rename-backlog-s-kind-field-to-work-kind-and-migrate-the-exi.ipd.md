# IPD: rename backlog's Kind field to Work-Kind and migrate the existing items

- Date: 2026-08-29
- Kind: child
- Concern: Backlog records work nature in a field named `- Kind:`, but that token is already used for two unrelated things elsewhere (an IPD's structural kind, and research's document type), so the field cannot keep this name once plans and specs gain the same concept. The maintainer chose one consistent name. Renaming it touches 88 tracked items in a checkout other agents are committing to, and `backlog.py` also parses a DISTINCT `- Gate-Kind:` field that a careless substring rename would silently corrupt.
- Scope: Rename the on-disk work-nature field from `- Kind:` to `- Work-Kind:` in `backlog.py`, migrate the 87 existing backlog ITEMS behind a dual-read window so the tree never stops parsing, update `.aw/records/backlog/README.md` and any other documentation naming the old spelling, and reconcile the `backlog new` flag declaration in `command_surface.py` if a `--work-kind` spelling is added. Excludes adding the field to plans or specs (child 02 owns that), excludes renaming the in-code vocabulary symbol, excludes any change to `Gate-Kind`, and excludes making the field OPTIONAL: backlog requires it today and this is a pure rename that preserves that.
- Scope-Paths: agent_workflows/backlog.py, .aw/records/backlog, agent_workflows/command_surface.py, tests/test_backlog_work_kind_rename.py
- Item-Dependencies: none
- Status: to-review
- Set: wkindname
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 9trlc3
- Blocks-Release: next
- From-Backlog: 1ap48y

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 /plan-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-002/PR-003/PR-005/PR-007 plus the Set-wide PR-001, all FIXED in place. The plan's core judgement is sound and its best instinct is verified: dual-read genuinely must precede the rewrite, and anchoring on the full-line pattern is genuinely necessary because `backlog.py` does parse a distinct `- Gate-Kind:` through a shared matcher. Two fixes were the difference between a plan that passes and one that fails its own validation. THE COUNTS WERE WRONG (F1b): the 88 items and 2 `Gate-Kind` items this plan asserted as pass conditions are TREE-WIDE GREP counts; `backlog._iter_items` reads 87 items (86 `.backlog.md` plus one legacy-named `done/...-e06-scenario-token-test-bindings.md`) and excludes `README.md`, and the `Gate-Kind` ITEM count is 1. So "88 carry the new spelling, 0 carry the old" was unsatisfiable, and the README is DOCUMENTATION that must be edited rather than data to migrate; enumeration is now derived from the parser and a new E-06 owns the README. THE CLEAN-CHECK REQUIREMENT WAS UNACHIEVABLE (F7): `aw backlog check` is already RED with 3 pre-existing `backlog.summary-unsafe` violations unrelated to this rename, so requiring clean at three points would have forced either a fabricated pass or edits outside the fence; now no-worsening keyed on the absence of any `backlog.kind-invalid` finding. Also: REQUIREDNESS IS PRESERVED, not relaxed (F5) - backlog rejects an absent value today and must still, correcting the Set's false "optional on all three" premise, with E-02/E-04 and V-02/V-04 now proving it; `command_surface.py` ADDED to Scope-Paths with new E-05, because `backlog new` DOES declare `--kind` in `legacy_flags` so child 02's undeclared-`--priority` finding does not transfer here (F6); and the 10 EXISTING test modules that emit the old spelling as fixture data are now named as the dual-read window's best real-caller evidence, required to pass UNEDITED and fenced against mass-editing (F8). Stale baseline refreshed: fast suite `2927 passed, 3 skipped, 4 xfailed` at `be49ac4`. Lints `conforming` at review-finalize with zero diagnostics and zero advisories. E-count 4 -> 6, one task group added; still standard size. OQ-01 unchanged (keep `--kind` as an alias).
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): split out of the approved plan `a6cej0` (now superseded) at the maintainer's direction, carrying its rename task group. The rename itself is the maintainer's decision, made against my recommendation to defer it; their reasoning was that two names for one concept is worse design, and they accepted the larger migration. Measurement done for that decision and carried here: `backlog.py` is the sole consumer, 88 items carry the field, and `Gate-Kind` is a live collision hazard on 2 items.

## Goal

Get backlog onto the field name the whole repo will use, without the tree ever failing to parse and without touching the unrelated gate field that shares the word.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: accept both spellings, then move

- [ ] E-01 Add a DUAL-READ window to `backlog.py` before anything is rewritten: accept `- Work-Kind:` and `- Kind:` on read, preferring the new spelling when both somehow appear. Anchor on the full-line field pattern, never on the bare token `Kind`, because the same module parses a distinct `- Gate-Kind:` field. This lands FIRST so that at no point during the migration does a partially converted tree fail to parse; a plan that rewrites files before dual-read exists has created a window where `aw backlog check` is broken.
  - Depends on: none
  - Expected outcome: an item with the old spelling parses; an item with the new spelling parses; a tree containing BOTH parses and `aw backlog check` is clean; `- Gate-Kind:` still parses unchanged.
  - Execution state: pending

- [ ] E-02 Make `backlog.py` WRITE the new spelling: update the item renderer and the creation path so a newly created item carries `- Work-Kind:`, and update the module's own documented field list (its docstring enumerates the field by name). Keep the in-code vocabulary symbol name as it is; only the on-disk field name changes. PRESERVE REQUIREDNESS: the validator rejects an item with no work-nature value today (`backlog.kind-invalid`) and must still reject one after the rename. This plan does NOT make the field optional on backlog; that asymmetry with plans and specs is the Set's intended outcome, so if making it optional seems necessary, STOP and report. Per OQ-01 add `--work-kind` as the preferred CLI spelling and KEEP `--kind` as an accepted alias.
  - Depends on: E-01
  - Expected outcome: a newly created item carries `- Work-Kind:`; the validator accepts a valid value, still REJECTS an absent one, and still rejects an out-of-vocabulary one; the module's documented field list matches what it writes; both `--kind` and `--work-kind` work.
  - Execution state: pending

- [ ] E-05 Reconcile the `backlog new` FLAG DECLARATION with the parser, which is a step child 02's reasoning does not cover and would mislead you if borrowed. Child 02 correctly found that `--priority` is UNDECLARED in `command_surface.COMMAND_INVENTORY`'s `legacy_flags` for `ipd set` and `specs set`, and concluded that file stays out of scope. That does NOT hold here: `backlog new` DOES declare `--kind` in its `legacy_flags` tuple, so adding `--work-kind` in E-02 without touching the declaration leaves the declared and accepted flag sets divergent on the one command where the flag is actually declared. Add `--work-kind` alongside the retained `--kind` there. Nothing asserts that tuple is exhaustive today, so this is correctness of the declaration rather than a test forcing your hand; do it because the declaration exists and is now wrong, and keep the edit to that one tuple.
  - Depends on: E-02
  - Expected outcome: `backlog new`'s `legacy_flags` lists both `--work-kind` and `--kind`; the declared set matches what the parser accepts; no other declaration is touched.
  - Execution state: pending

- [ ] E-06 Update `.aw/records/backlog/README.md`, the human-facing field list that names the old spelling, plus any other documentation hit found by grep. This file is DOCUMENTATION, not an item: the parser skips it by name, so E-03's migration does not and must not rewrite it, and it is the reason a tree-wide grep reports one more file than there are items. Leaving it stale would reintroduce the exact naming confusion the rename removes.
  - Depends on: E-03
  - Expected outcome: `README.md` documents `- Work-Kind:`; no documentation outside `Scope-Paths` needs editing, or any such hit is reported rather than edited.
  - Execution state: pending

### Task group 2: migrate the corpus, prove nothing else moved

- [ ] E-03 Rewrite the field in the existing items, with a script anchored on the full-line pattern from E-01. Enumerate the target set with `backlog._iter_items` rather than a grep, so it is exactly what the tool reads: 87 items at `be49ac4`, and NOT the widely quoted 88, which counts the README the parser skips (F1b explains the discrepancy and E-06 owns that file). Re-measure the count at your own HEAD before rewriting, since other sessions add items continuously. Then re-verify the `- Gate-Kind:` item count is unchanged at 1 and that item still parses, since substring corruption of that field is the specific hazard here. Change nothing but the one field line per file.
  - Depends on: E-02
  - Expected outcome: every parsed item carries `- Work-Kind:` and none carries `- Kind:` (87 at `be49ac4`, re-measured at yours); the `Gate-Kind` item count is unchanged at 1 and that item parses; `git diff` shows exactly one changed line per migrated item and no other edits.
  - Execution state: pending

- [ ] E-04 Add `tests/test_backlog_work_kind_rename.py` covering: an item with the NEW spelling parses and validates; an item with the OLD spelling still parses through the dual-read window; a tree containing both spellings validates with no work-nature finding; a newly created item is written with the new spelling; an out-of-vocabulary value is still rejected; REQUIREDNESS PRESERVED, namely that an item with NO work-nature field is still rejected as `backlog.kind-invalid` (F5), which must fail against an implementation that made the field optional; and the `Gate-Kind` guard, namely that an item carrying `- Gate-Kind:` parses with its gate intact and that field is never rewritten. Build every case on a throwaway tree rather than the live records, because the live backlog is being modified by other sessions while this runs. Separately, do NOT rewrite the 10 EXISTING test modules that emit the old spelling as fixture data (F8): the dual-read window should keep them green unchanged, and they are the best proof E-01 works on real callers. If one of them breaks, fix `backlog.py`, not the fixture.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the module passes; the dual-read case fails against an implementation that only accepts the new spelling; the requiredness case fails against an implementation that made the field optional; the `Gate-Kind` case fails against a substring-based rename; the 10 pre-existing old-spelling fixture modules pass UNEDITED.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `backlog.py` is the ONLY module that reads this field. Every `.kind` access outside it belongs to a different concept (a gate kind, an artifact type, a research document kind, or an unrelated change record), so the rename does not ripple into other modules.
- The module parses `- Gate-Kind:` through a shared matcher alongside its own fields, which is precisely why a substring rename is unsafe here rather than merely inelegant.
- The vocabulary is a frozen set of five members and is validated on both read and creation, so the tests already have a rejection path to extend.
- The backlog tree is live shared state: other sessions create and transition items continuously, and three items appeared in it during the graduation sweep that produced this plan. The migration must therefore be a single quick pass, re-counted immediately, not a long interactive edit.
- The superseded `a6cej0` holds the full evidence for the maintainer's decision to rename; cite it rather than re-deriving the argument.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `backlog.py` | The corruption hazard that shapes this whole plan: the module parses a DISTINCT `- Gate-Kind:` field, so any rename anchored on the token `Kind` rather than the full-line field pattern produces `Gate-Work-Kind` and silently breaks the gate contract. Every E-item here anchors on the full line, and E-03 and E-04 verify the count afterwards. The ITEM count is 1, not the 2 originally recorded here (see F1b). | `grep -rl '^- Gate-Kind:' .aw/records/backlog/` = 2 files, of which one is `README.md`; the only ITEM carrying it is `blocked/20260829-mergedirty-01-h1ksy6-pre-merge-dirty-check-scope.backlog.md` |
| F1b | HIGH | `.aw/records/backlog/`; `backlog._iter_items` | THE COUNTS THIS PLAN VALIDATES AGAINST WERE WRONG, and because E-03 makes them a pass/fail assertion the plan would have failed its own validation. `grep -rl '^- Kind:'` returns 88 FILES but the parser reads 87 ITEMS: it globs `*.md` and excludes only `README.md`, so it includes one legacy-named item without the `.backlog.md` suffix and excludes the README. The README is DOCUMENTATION carrying the field list, so it must be EDITED (now E-06), never migrated as data. The same off-by-one inflated `Gate-Kind` from its true 1 item to 2. Corrected everywhere and the enumeration is now derived from the parser rather than a grep. | measured at `be49ac4`: `backlog._iter_items(Path('.'))` returns 87 paths; `find .aw/records/backlog -name '*.backlog.md'` = 86, all carrying the field; the extra parsed item is `done/20260817-awphysical-01-xd78mr-e06-scenario-token-test-bindings.md`; `_iter_items` excludes only `README.md` |
| F2 | HIGH | `.aw/records/backlog/` | The migration size: 87 parsed items carry the field. The CODE change is one module, so the risk here is file-count and concurrency, not complexity. | `backlog._iter_items` = 87 items at `be49ac4`; the commonly quoted 88 is a tree-wide grep including `README.md` (F1b) |
| F5 | HIGH | `backlog.py:178`; `ipd_schema.py:199` | THE FIELD IS REQUIRED ON BACKLOG AND THIS PLAN MUST NOT CHANGE THAT, which the Set's original completion criteria contradicted by promising the field would be "optional on all three so an artifact without it still validates". Backlog validates the field on read and an item with no work-nature line is a hard error TODAY. Since this plan is a pure rename, that requirement survives it, so after the Set lands backlog REQUIRES the field while plans and specs will not. The asymmetry is intended: the Set delivers ONE NAME, not one requiredness. Stated here because an executor reading the orchestrator's old wording could have "fixed" the mismatch by weakening a live contract across 87 records. | measured at `be49ac4`: an item with no `- Kind:` yields `backlog.kind-invalid: kind not in ['bug','chore','feature','followup','security']: None`, exit 1; `backlog.py:178` validates unconditionally; by contrast `META_PRIORITY` sits in `META_RECOGNIZED` and not `META_REQUIRED` |
| F6 | MED | `command_surface.py:946` | THE PRECEDENT CHILD 02 RELIES ON DOES NOT COVER THIS PLAN. Child 02 measured that `--priority` is undeclared in `legacy_flags` for `ipd set` and `specs set` and concluded `command_surface.py` stays out of scope; correct for child 02. But `backlog new` DOES declare `--kind` in its `legacy_flags`, so adding the `--work-kind` spelling OQ-01 calls for leaves the declaration and the parser divergent on the one command where the flag is declared. Now owned by E-05 with `command_surface.py` added to `Scope-Paths`. | `COMMAND_INVENTORY` for `backlog new` -> `(..., '--priority', '--kind', '--slug', ...)`; for `ipd set` and `specs set` -> no `--priority` |
| F7 | HIGH | `aw backlog check` | THE PLAN'S CENTRAL VALIDATION REQUIREMENT WAS UNACHIEVABLE, the same defect class the earlier review caught in the sibling plan's CLI-conformance requirement. This plan required `aw backlog check` CLEAN at three points as the whole justification for the dual-read window, but the command is already RED at 3 pre-existing `backlog.summary-unsafe` violations unrelated to this rename and outside this plan's fence. An executor would have had to fabricate a pass or edit three unrelated items. Converted to a NO-WORSENING requirement keyed on the absence of any `backlog.kind-invalid` finding. | measured at `be49ac4`: `aw backlog check` exits 1 reporting `3 violation(s)`, all `backlog.summary-unsafe`, on `20260819-awagyfalseerror-01-uhbdt1`, `20260820-awhistignore-01-f7w55w`, `20260820-awinstallfix-01-av9hni` |
| F8 | MED | `tests/` | THE MIGRATION'S REAL REGRESSION SURFACE, unmentioned by the plan and larger than its declared one. 10 test modules write a backlog-style `- Kind: <member>` line as fixture data. None is in `Scope-Paths`, which is right, but the plan never said what should happen to them. The correct answer strengthens the plan: the dual-read window should keep them GREEN UNCHANGED, making them the best available proof that E-01 works on real callers rather than only on the new test's throwaway trees. Mass-editing them to the new spelling would destroy the only in-suite coverage of the old spelling this plan promises to keep accepting. | measured at `be49ac4`: `grep -rln -- '- Kind: \(chore\|bug\|feature\|security\|followup\)' tests/*.py` returns 10 modules including `test_backlog.py`, `test_from_backlog.py`, `test_status_set.py`, `test_release_gate_close.py` |
| F3 | MED | `backlog.py` | The rename is CONTAINED because no other module reads the field. This is what makes the plan small in code terms and is worth stating so a reviewer does not go looking for downstream consumers. | the only work-nature reads are inside `backlog.py`; other `.kind` hits are gate, artifact-type, research-kind, or change-record uses |
| F4 | MED | ordering | Dual-read MUST precede the rewrite. Without it, the instant the first item is converted the tree contains a spelling the parser rejects, so `aw backlog check` fails until the last item lands, and any concurrent session reading the backlog sees a broken tree in between. | the parser validates the field on read and rejects an out-of-vocabulary or missing value |

## Proposed changes (ordered, validatable)

1. Accept both spellings on read, anchored on the full-line pattern (E-01).
2. Write the new spelling, and decide the CLI flag alias (E-02).
3. Rewrite the 88 items and re-verify `Gate-Kind` is untouched (E-03).
4. Prove dual-read, creation, rejection, and the `Gate-Kind` guard (E-04).

## Deferred / out of scope (with reason)

- Adding `Work-Kind` to plans and specs is child 02 (`ng2blv`), which declares `executed:9trlc3`. This plan must not touch the schema, the spec contract, or the check engine.
- Renaming the in-code vocabulary SYMBOL. Only the on-disk field name is in question; renaming the symbol would churn child 02's imports for no gain.
- Removing the dual-read window. It stays after the migration as cheap insurance, since an old-spelling item can still arrive from a long-lived branch or a stash. Retiring it is a later cleanup, not this plan's business.
- Any change to `Gate-Kind` itself.

## Scope check

- Over-scope: none. `backlog.py` carries the reader, writer, and validator; the records tree is the corpus being migrated; the test file is new.
- Under-scope, DECLARED: documentation outside these paths may name the old field spelling. Grep the docs tree; if a hit lies outside `Scope-Paths`, STOP and report rather than editing it, and record which files need a follow-up. The orchestrator assigns doc updates to this child, so if the only hits are inside `backlog.py`'s own docstring the obligation is already met.
- The backlog records tree is shared live state. Migrate in one pass, and if another session has an item staged or dirty, do NOT sweep it into your commit; verify the staged set before committing rather than trusting the path scope.

## Required tests / validation

- `tests/test_backlog_work_kind_rename.py` must pass with every case in E-04, built on throwaway trees rather than the live records.
- Falsifiability is specific: the dual-read case must FAIL against an implementation accepting only the new spelling, and the `Gate-Kind` case must FAIL against a substring-based rename. Paste both failures.
- `aw backlog check` must be NO WORSE at THREE points, and all three must be pasted: before the migration, DURING it with a tree containing both spellings, and after. The middle one is the whole justification for E-01. NOT "clean": measured at `be49ac4` the command already exits 1 with 3 pre-existing `backlog.summary-unsafe` violations (`20260819-awagyfalseerror-01-uhbdt1`, `20260820-awhistignore-01-f7w55w`, `20260820-awinstallfix-01-av9hni`) that have nothing to do with this rename and sit outside this plan's business. Demanding clean would be an unachievable requirement that pushes an executor either to fabricate a pass or to edit three unrelated items. The real property to prove is that NO `backlog.kind-invalid` finding appears at any of the three points and that the pre-existing finding set is unchanged. Take your own baseline first; do not reuse this count.
- The existing backlog tests must pass unchanged. Locate them by name first; if one asserts the old field spelling as correct, it is a characterization test of the pre-rename contract and updating it is legitimate, but it must be called out in the record rather than quietly edited, and it must be added to `Scope-Paths` first.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""` (or `make test` / `make test-all`). Do NOT add `-n auto` or a second `-q`. They are NOT interchangeable: the bare run carries `-m 'not slow'`, so `slow`-marked modules are skipped by it entirely.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite at `be49ac4` during this review: `2927 passed, 3 skipped, 4 xfailed`. The `2880` reading at `df731f1` recorded when this plan was authored is already stale, which is exactly the point. Take your own readings with their HEAD.
- EXISTING TESTS EMIT THE OLD SPELLING AS FIXTURE DATA. Measured at `be49ac4`, 10 test modules write a backlog-style `- Kind: <member>` line into fixtures (`test_backlog.py`, `test_backlog_blocking_close_gate.py`, `test_backlog_graduated.py`, `test_agentadhere_policy_engine.py`, `test_auto_index_on_mutation.py`, `test_check_engine_spec_handoff.py`, `test_from_backlog.py`, `test_history_routing.py`, `test_release_gate_close.py`, `test_status_set.py`). The dual-read window from E-01 is what should keep them GREEN UNCHANGED, so treat them as the real regression signal for E-01: if any of them breaks, dual-read is not working and the fix belongs in `backlog.py`, not in the fixtures. Do not mass-edit them to the new spelling; that would delete the only in-suite coverage of the old spelling this plan promises to keep accepting. Note these files are NOT in `Scope-Paths`, which is deliberate.
- Post-migration counts must be pasted, DERIVED FROM THE PARSER not a tree grep: every parsed item carrying the new spelling and none the old (87 at `be49ac4`), and the `Gate-Kind` ITEM count unchanged at 1. If you paste 88 and 2 you have counted `README.md` as data (F1b); state the exclusion explicitly so the numbers are checkable.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- Update `backlog.py`'s own documented field list as part of E-02, since it enumerates the field by name.
- Grep the docs tree for the old field spelling and fix any hit that falls inside `Scope-Paths`; report anything outside it rather than reaching for it.
- Record in the terminal history that the dual-read window is deliberately RETAINED after the migration, so a later reader does not mistake it for dead code and remove it without thought.

## Open questions

### OQ-01: Keep `--kind` as a CLI alias, or replace it outright?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP IT AS AN ALIAS, add `--work-kind` as the preferred spelling. The house pattern for a renamed surface is to accept the old form rather than break a caller, and the cost here is one line of argument parsing. Breaking `--kind` would fail any script, habit, or agent instruction that uses it, for no benefit beyond tidiness, and the field's on-disk name (the thing that actually needed to be consistent) is already fixed by this plan. E-02 records the decision; if the executor finds the alias genuinely awkward to wire, that is a finding to report rather than a licence to break the flag.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the dual-read implementation showing it anchors on the full-line field pattern and not the bare token. Paste an old-spelling item and a new-spelling item both parsing. Paste `aw backlog check` clean against a tree deliberately containing BOTH spellings, which is the state the migration passes through. Paste an item carrying `- Gate-Kind:` parsing with its gate values intact.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a newly created item showing `- Work-Kind:` on disk. Paste the validator accepting it, rejecting an out-of-vocabulary value, and STILL REJECTING an item with the field absent, which proves requiredness was preserved rather than quietly relaxed (F5). Paste the module's documented field list matching what it now writes. Paste both `--kind` and `--work-kind` working, per OQ-01's kept alias.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the counts after migration, DERIVED FROM THE PARSER and not from a tree-wide grep: parsed items carrying `- Work-Kind:` = every item (87 at `be49ac4`, re-measured at your HEAD), parsed items carrying `- Kind:` = 0, and items carrying `- Gate-Kind:` = 1. State explicitly that `README.md` is excluded from all three because the parser skips it, so a reviewer can tell your numbers from the misleading 88/2 a `grep -rl` produces (F1b). Paste `aw backlog check` before and during and after with NO `backlog.kind-invalid` finding and the pre-existing `backlog.summary-unsafe` set unchanged; do NOT claim clean (F7). Paste a `git diff` excerpt for two or three migrated items showing exactly ONE changed line each and no incidental reformatting. Paste `git diff --cached --name-only` before your commit proving no other session's file was swept in.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the full test module passing. Paste FALSIFIABILITY as actual failures: the dual-read case failing when only the new spelling is accepted, and the `Gate-Kind` case failing under a substring-based rename. Paste the requiredness-preserved case passing and show it FAILS against an implementation that made the field optional. Confirm every case used a throwaway tree, not the live records.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `backlog new` `legacy_flags` tuple showing BOTH `--work-kind` and the retained `--kind`. Paste a comparison of the declared flag set against what the parser actually accepts (`aw backlog new --help`) showing they agree. Paste `git diff --stat` for `command_surface.py` showing only that one declaration changed, and confirm no `ipd set` or `specs set` declaration was touched.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `.aw/records/backlog/README.md` diff showing the field list now names `- Work-Kind:`. Paste a grep for the old full-line spelling across tracked documentation showing either no remaining hits or only hits outside `Scope-Paths`, which must be REPORTED rather than edited. Paste proof the README was NOT migrated as an item, namely that its diff is a documentation edit and that the parser's item enumeration never included it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 4 E-leaves across 2 task groups, well under the thresholds. One concern throughout: move backlog's field to its new name safely. Right-sizing per leaf: E-01 dual-read, E-02 write side, E-03 the corpus rewrite, E-04 the tests.

Open questions: ALL RESOLVED. OQ-01 keeps `--kind` as an alias. The decision to rename at all is the maintainer's, recorded in the superseded `a6cej0`; this plan implements it and does not relitigate it.

Scope fence: touch ONLY `agent_workflows/backlog.py`, the backlog records tree, the `backlog new` declaration in `agent_workflows/command_surface.py` (E-05 only, that one tuple), and the new test file. Do NOT touch the IPD schema, the spec contract, the check engine, or the CLI beyond backlog's own flag (child 02 owns those). Do NOT modify `Gate-Kind` handling. Do NOT rename the in-code vocabulary symbol. Do NOT make the field optional on backlog: it is required today and this is a pure rename (F5). Do NOT edit the 10 existing test modules that carry the old spelling as fixture data (F8); they must pass unedited through the dual-read window. If it seems to need more, STOP and report.

CONCURRENCY RULE, not optional: the backlog tree is live shared state and other sessions create and transition items continuously; three new items appeared in it while this plan was being written. Do the migration in ONE pass and re-count immediately. If an item is dirty or staged by someone else, leave it and report it rather than migrating it under them. Before every commit run `git diff --cached --name-only` and unstage anything that is not yours; at least one concurrent session had unrelated files STAGED while this plan was authored, so a path-scoped commit alone is not sufficient protection.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run, and never reuse this plan's recorded baseline as if freshly measured.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
