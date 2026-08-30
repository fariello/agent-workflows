# IPD: rename backlog's Kind field to Work-Kind and migrate the existing items

- Date: 2026-08-29
- Kind: child
- Concern: Backlog records work nature in a field named `- Kind:`, but that token is already used for FOUR unrelated things elsewhere (an IPD's structural kind, research's 17-member document type, a comms message kind, and backlog's own `Gate-Kind`), so the field cannot keep this name once plans and specs gain the same concept. The maintainer chose one consistent name. Renaming it touches 87 parsed items in a checkout other agents are committing to, and `backlog.py` also parses a DISTINCT `- Gate-Kind:` field that a careless substring rename would silently corrupt.
- Scope: Rename the on-disk work-nature field from `- Kind:` to `- Work-Kind:` in `backlog.py`, migrate the 87 existing backlog ITEMS behind a dual-read window so the tree never stops parsing, update `.aw/records/backlog/README.md` and any other documentation naming the old spelling, and reconcile the `backlog new` flag declaration in `command_surface.py` if a `--work-kind` spelling is added. Excludes adding the field to plans or specs (child 02 owns that), excludes renaming the in-code vocabulary symbol, excludes any change to `Gate-Kind`, and excludes making the field OPTIONAL: backlog requires it today and this is a pure rename that preserves that.
- Scope-Paths: agent_workflows/backlog.py, .aw/records/backlog, agent_workflows/command_surface.py, tests/test_backlog_work_kind_rename.py
- Item-Dependencies: none
- Status: executed
- Set: wkindname
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 9trlc3
- Blocks-Release: next
- From-Backlog: 1ap48y

## Workflow history
- 2026-08-30 executed (opencode (its_direct/pt3-claude-opus-5-1m-us)): Backlog's work-nature field renamed to Work-Kind behind a dual-read window landed first, so the tree never stopped parsing mid-migration. 91 items migrated (enumerated with backlog._iter_items, NOT a grep, which would have counted README.md as data and reported 92); Gate-Kind item count unchanged at 1 and that item still parses, verified because a substring-anchored rename would have produced Gate-Work-Kind; requiredness PRESERVED (an absent value is still backlog.kind-invalid), so the Set unifies the field's NAME and not its requiredness; --kind kept as an alias per OQ-01; README.md edited as documentation rather than migrated as data. 26 new tests, with three load-bearing negatives each shown FAILING against the specific mis-implementation it guards. The 12 pre-existing old-spelling fixture modules pass UNEDITED, which is the real proof dual-read works on live callers. Suite +26 passing on both invocations with a byte-identical pre-existing failure set. The dual-read window is deliberately RETAINED as insurance against an old-spelling item arriving from a long-lived branch; it is not dead code. [Scope reconciliation - out-of-scope agent_workflows/cli.py: E-02/OQ-01 require --work-kind as the preferred flag with --kind kept as an alias, and backlog new's argparse declarations live here; the plan's scope fence explicitly permits 'the CLI beyond backlog's own flag', so omitting this path from Scope-Paths was an oversight. Edit confined to that one flag block (+15/-3). See DECISION 02-9trlc3-D2.; in-scope-unmodified .aw/records/backlog: modified in commit 91cd3fa2 (receipt base); 91 items migrated plus the README; in-scope-unmodified agent_workflows/backlog.py: modified in commit 91cd3fa2, which is this receipt's own base_head, so finalize cannot see it; dual-read, canonical write, docstring; in-scope-unmodified agent_workflows/command_surface.py: modified in commit 91cd3fa2 (receipt base); --work-kind added to backlog new legacy_flags; in-scope-unmodified tests/test_backlog_work_kind_rename.py: created in commit 91cd3fa2 (receipt base); 26 cases]
- 2026-08-30 approved (aw set, --by-human): Approved by the maintainer: 'I APPROVE all the reviewed IPDs' (2026-08-30 session, verbatim standing instruction before stepping away).
- 2026-08-30 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 fixed in place. Corrected two would-have-failed validations (backlog REQUIRES the field so the Set unifies name not requiredness; the 88/2 counts are tree-wide greps while the parser reads 87 items and 1 Gate-Kind item) and one unachievable gate (aw backlog check is already red on 3 unrelated violations, now no-worsening). Also: two validation mechanisms not one, command_surface.py added to child 01 because backlog new does declare --kind, orchestrator scope narrowed off the shared pending/ dir, 10 old-spelling fixture modules must pass unedited, and E-01 recorded as a manual obligation the runner rollup does not perform. Baselines re-measured at be49ac4 (2927 passed, 3 skipped, 4 xfailed). All three lint conforming at review-finalize.

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 /plan-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-002/PR-003/PR-005/PR-007 plus the Set-wide PR-001, all FIXED in place. The plan's core judgement is sound and its best instinct is verified: dual-read genuinely must precede the rewrite, and anchoring on the full-line pattern is genuinely necessary because `backlog.py` does parse a distinct `- Gate-Kind:` through a shared matcher. Two fixes were the difference between a plan that passes and one that fails its own validation. THE COUNTS WERE WRONG (F1b): the 88 items and 2 `Gate-Kind` items this plan asserted as pass conditions are TREE-WIDE GREP counts; `backlog._iter_items` reads 87 items (86 `.backlog.md` plus one legacy-named `done/...-e06-scenario-token-test-bindings.md`) and excludes `README.md`, and the `Gate-Kind` ITEM count is 1. So "88 carry the new spelling, 0 carry the old" was unsatisfiable, and the README is DOCUMENTATION that must be edited rather than data to migrate; enumeration is now derived from the parser and a new E-06 owns the README. THE CLEAN-CHECK REQUIREMENT WAS UNACHIEVABLE (F7): `aw backlog check` is already RED with 3 pre-existing `backlog.summary-unsafe` violations unrelated to this rename, so requiring clean at three points would have forced either a fabricated pass or edits outside the fence; now no-worsening keyed on the absence of any `backlog.kind-invalid` finding. Also: REQUIREDNESS IS PRESERVED, not relaxed (F5) - backlog rejects an absent value today and must still, correcting the Set's false "optional on all three" premise, with E-02/E-04 and V-02/V-04 now proving it; `command_surface.py` ADDED to Scope-Paths with new E-05, because `backlog new` DOES declare `--kind` in `legacy_flags` so child 02's undeclared-`--priority` finding does not transfer here (F6); and the 10 EXISTING test modules that emit the old spelling as fixture data are now named as the dual-read window's best real-caller evidence, required to pass UNEDITED and fenced against mass-editing (F8). Stale baseline refreshed: fast suite `2927 passed, 3 skipped, 4 xfailed` at `be49ac4`. Lints `conforming` at review-finalize with zero diagnostics and zero advisories. E-count 4 -> 6, one task group added; still standard size. OQ-01 unchanged (keep `--kind` as an alias).
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): split out of the approved plan `a6cej0` (now superseded) at the maintainer's direction, carrying its rename task group. The rename itself is the maintainer's decision, made against my recommendation to defer it; their reasoning was that two names for one concept is worse design, and they accepted the larger migration. Measurement done for that decision and carried here: `backlog.py` is the sole consumer, 88 items carry the field, and `Gate-Kind` is a live collision hazard on 2 items.

## Goal

Get backlog onto the field name the whole repo will use, without the tree ever failing to parse and without touching the unrelated gate field that shares the word.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: accept both spellings, then move

- [x] E-01 Add a DUAL-READ window to `backlog.py` before anything is rewritten: accept `- Work-Kind:` and `- Kind:` on read, preferring the new spelling when both somehow appear. Anchor on the full-line field pattern, never on the bare token `Kind`, because the same module parses a distinct `- Gate-Kind:` field. This lands FIRST so that at no point during the migration does a partially converted tree fail to parse; a plan that rewrites files before dual-read exists has created a window where `aw backlog check` is broken.
  - Depends on: none
  - Expected outcome: an item with the old spelling parses; an item with the new spelling parses; a tree containing BOTH parses and `aw backlog check` reports NO work-nature finding on it (not "clean": the live tree already carries 3 unrelated `backlog.summary-unsafe` violations, F7); `- Gate-Kind:` still parses unchanged.
  - Execution state: performed

- [x] E-02 Make `backlog.py` WRITE the new spelling: update the item renderer and the creation path so a newly created item carries `- Work-Kind:`, and update the module's own documented field list (its docstring enumerates the field by name). Keep the in-code vocabulary symbol name as it is; only the on-disk field name changes. PRESERVE REQUIREDNESS: the validator rejects an item with no work-nature value today (`backlog.kind-invalid`) and must still reject one after the rename. This plan does NOT make the field optional on backlog; that asymmetry with plans and specs is the Set's intended outcome, so if making it optional seems necessary, STOP and report. Per OQ-01 add `--work-kind` as the preferred CLI spelling and KEEP `--kind` as an accepted alias.
  - Depends on: E-01
  - Expected outcome: a newly created item carries `- Work-Kind:`; the validator accepts a valid value, still REJECTS an absent one, and still rejects an out-of-vocabulary one; the module's documented field list matches what it writes; both `--kind` and `--work-kind` work.
  - Execution state: performed

- [x] E-05 Reconcile the `backlog new` FLAG DECLARATION with the parser, which is a step child 02's reasoning does not cover and would mislead you if borrowed. Child 02 correctly found that `--priority` is UNDECLARED in `command_surface.COMMAND_INVENTORY`'s `legacy_flags` for `ipd set` and `specs set`, and concluded that file stays out of scope. That does NOT hold here: `backlog new` DOES declare `--kind` in its `legacy_flags` tuple, so adding `--work-kind` in E-02 without touching the declaration leaves the declared and accepted flag sets divergent on the one command where the flag is actually declared. Add `--work-kind` alongside the retained `--kind` there. Nothing asserts that tuple is exhaustive today, so this is correctness of the declaration rather than a test forcing your hand; do it because the declaration exists and is now wrong, and keep the edit to that one tuple.
  - Depends on: E-02
  - Expected outcome: `backlog new`'s `legacy_flags` lists both `--work-kind` and `--kind`; the declared set matches what the parser accepts; no other declaration is touched.
  - Execution state: performed

### Task group 2: migrate the corpus, prove nothing else moved

- [x] E-03 Rewrite the field in the existing items, with a script anchored on the full-line pattern from E-01. Enumerate the target set with `backlog._iter_items` rather than a grep, so it is exactly what the tool reads: 87 items at `be49ac4`, and NOT the widely quoted 88, which counts the README the parser skips (F1b explains the discrepancy and E-06 owns that file). Re-measure the count at your own HEAD before rewriting, since other sessions add items continuously. Then re-verify the `- Gate-Kind:` item count is unchanged at 1 and that item still parses, since substring corruption of that field is the specific hazard here. Change nothing but the one field line per file.
  - Depends on: E-02
  - Expected outcome: every parsed item carries `- Work-Kind:` and none carries `- Kind:` (87 at `be49ac4`, re-measured at yours); the `Gate-Kind` item count is unchanged at 1 and that item parses; `git diff` shows exactly one changed line per migrated item and no other edits.
  - Execution state: performed

- [x] E-06 Update `.aw/records/backlog/README.md`, the human-facing field list that names the old spelling, plus any other documentation hit found by grep. This file is DOCUMENTATION, not an item: the parser skips it by name, so E-03's migration does not and must not rewrite it, and it is the reason a tree-wide grep reports one more file than there are items. It is a hand-maintained tracked file, not installer-generated, so editing it here is sufficient and nothing regenerates it back. Leaving it stale would reintroduce the exact naming confusion the rename removes.
  - Depends on: E-03
  - Expected outcome: `README.md` documents `- Work-Kind:`; no documentation outside `Scope-Paths` needs editing, or any such hit is reported rather than edited.
  - Execution state: performed

- [x] E-04 Add `tests/test_backlog_work_kind_rename.py` covering: an item with the NEW spelling parses and validates; an item with the OLD spelling still parses through the dual-read window; a tree containing both spellings validates with no work-nature finding; a newly created item is written with the new spelling; an out-of-vocabulary value is still rejected; REQUIREDNESS PRESERVED, namely that an item with NO work-nature field is still rejected as `backlog.kind-invalid` (F5), which must fail against an implementation that made the field optional; and the `Gate-Kind` guard, namely that an item carrying `- Gate-Kind:` parses with its gate intact and that field is never rewritten. Build every case on a throwaway tree rather than the live records, because the live backlog is being modified by other sessions while this runs. Separately, do NOT rewrite the 10 EXISTING test modules that emit the old spelling as fixture data (F8): the dual-read window should keep them green unchanged, and they are the best proof E-01 works on real callers. If one of them breaks, fix `backlog.py`, not the fixture.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the module passes; the dual-read case fails against an implementation that only accepts the new spelling; the requiredness case fails against an implementation that made the field optional; the `Gate-Kind` case fails against a substring-based rename; the 10 pre-existing old-spelling fixture modules pass UNEDITED.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `backlog.py` is the ONLY module that reads this field. Every `.kind` access outside it belongs to a different concept (a gate kind, an artifact type, a research document kind, a comms message kind, or an unrelated change record), so the rename does not ripple into other modules.
- The `Kind` token is booked FOUR other times, not two as this plan's Concern originally said: `ipd_schema.KINDS` (`child`/`orchestrator`), `research_contract.KINDS` (17 document-type members, not the 18 quoted elsewhere in this Set), `comms.KINDS` (`ask`/`reply`/`task`/`handoff`/`fyi`), and backlog's own `Gate-Kind`. All are disjoint from the work-nature set, which is what makes `Work-Kind` a correctness fix rather than a stylistic one.
- `.aw/records/backlog/README.md` is a hand-maintained TRACKED file, not installer-generated: nothing in `engine.py` writes its field list. So E-06's edit is durable and will not be regenerated away.
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
| F9 | HIGH | this plan, E-06 vs task groups | A SELF-CONTRADICTION INTRODUCED BY THE PRIOR REVIEW PASS, and the kind a dependency-ordered runner acts on literally: E-06 was appended to Task group 1 ("accept both spellings, then move") while declaring `Depends on: E-03`, which lives BELOW it in Task group 2. So the checklist read top-to-bottom told an executor to update the README before the migration it documents, and the group heading mislabeled the work. The E/V bijection and the lint both passed regardless, because neither checks that a group's members are reachable in listed order. Moved E-06 into Task group 2 after E-03, where its dependency reads forward. | E-06 declared `Depends on: E-03` while appearing at file position above the `### Task group 2` heading that contains E-03; `aw ipd lint` reported `conforming` with zero diagnostics in that state |
| F10 | HIGH | this plan, required-tests vs scope fence | A DIRECT CONTRADICTION between two of this plan's own requirements, one of which was pre-existing and one added by the prior review, giving an executor written permission for the exact edit the fence forbids. The required-tests list said that if an existing test asserts the old spelling, "updating it is legitimate ... it must be added to `Scope-Paths` first", while the very next bullet and the scope fence say the 10 old-spelling fixture modules must pass UNEDITED and are deliberately NOT in `Scope-Paths`. Under the permissive reading an executor could edit away the only in-suite coverage of the old spelling this plan promises to keep accepting, and call it compliant. The permission is withdrawn: a failing old-spelling test is evidence dual-read is broken, so the fix belongs in `backlog.py`. | the two bullets stood adjacent in `## Required tests / validation`; the scope fence separately forbids editing those modules |
| F11 | MED | this plan, E-01 and V-01 vs F7 | The prior pass corrected the "must be clean" requirement in the Required-tests section but left the SAME unachievable wording in E-01's expected outcome and V-01's required evidence, so the plan simultaneously told the executor that `aw backlog check` must be clean and that it cannot be. Both now ask for the absence of a `backlog.kind-invalid` finding and require the executor to state which tree was measured, since the assertion IS satisfiable on a throwaway fixture tree and is not on the live one. | E-01 read "`aw backlog check` is clean" and V-01 read "paste `aw backlog check` clean" while F7 records the command already exiting 1 on 3 unrelated violations |
| F12 | LOW | this plan's Concern; `research_contract.KINDS` | Two counting errors in the plan's own framing, both now corrected because the plan uses them as its justification. The Concern said the `Kind` token collides with "two unrelated things"; it is FOUR (IPD structural kind, research document type, comms message kind, backlog's own `Gate-Kind`). And research's vocabulary is 17 members, not the 18 asserted here and in the sibling plan. Neither changes a decision, but a plan whose stated rationale is a collision count should state the count correctly, and the understated 2 makes the rename look more optional than it is. | measured at `ce1ae8e`: `len(research_contract.KINDS)` = 17; `ipd_schema.KINDS` = `{child, orchestrator}`; `comms.KINDS` = `('ask','reply','task','handoff','fyi')`; `A.GATE_KINDS` backs `Gate-Kind` |
| F13 | LOW | `.aw/records/backlog/README.md`; `engine.py` | Checked so E-06 is not a wasted edit: the backlog README is a hand-maintained TRACKED file, not installer-generated. Nothing in `engine.py` writes its field list, so the E-06 edit is durable and no later `aw install` regenerates the old spelling back over it. Had it been generated, E-06 would have needed to edit the generator instead, and `engine.py` is not in `Scope-Paths`. | `git ls-files .aw/records/backlog/README.md` tracks it; `grep` for the field-list string in `agent_workflows/*.py` matches only `backlog.py:23` (the module docstring) and `cli.py:2991` (the flag help), never a README writer |
| F3 | MED | `backlog.py` | The rename is CONTAINED because no other module reads the field. This is what makes the plan small in code terms and is worth stating so a reviewer does not go looking for downstream consumers. | the only work-nature reads are inside `backlog.py`; other `.kind` hits are gate, artifact-type, research-kind, or change-record uses |
| F4 | MED | ordering | Dual-read MUST precede the rewrite. Without it, the instant the first item is converted the tree contains a spelling the parser rejects, so `aw backlog check` fails until the last item lands, and any concurrent session reading the backlog sees a broken tree in between. | the parser validates the field on read and rejects an out-of-vocabulary or missing value |

## Proposed changes (ordered, validatable)

1. Accept both spellings on read, anchored on the full-line pattern (E-01).
2. Write the new spelling, keeping `--kind` as an alias and requiredness intact (E-02).
3. Reconcile the `backlog new` flag declaration with the parser (E-05).
4. Rewrite the parsed items (87 at `be49ac4`) and re-verify `Gate-Kind` is untouched (E-03).
5. Update the backlog README's field list (E-06).
6. Prove dual-read, creation, rejection, requiredness, and the `Gate-Kind` guard (E-04).

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
- The existing backlog tests must pass UNCHANGED, and this plan does NOT license editing them. An earlier revision of this line said updating an old-spelling test was "legitimate if called out", which directly contradicts the fence and the next bullet; that permission is WITHDRAWN. A test asserting the old spelling is exactly what the dual-read window exists to keep passing, so if one fails, the defect is in `backlog.py` and the fix belongs there. Should you find a test that genuinely cannot pass under dual-read, that is a finding to REPORT and a reason to stop, not a licence to edit the fixture.
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

- [x] V-01 validates E-01
  - Required evidence: paste the dual-read implementation showing it anchors on the full-line field pattern and not the bare token. Paste an old-spelling item and a new-spelling item both parsing. Paste `aw backlog check` against a tree deliberately containing BOTH spellings, which is the state the migration passes through, showing NO `backlog.kind-invalid` finding; on a throwaway fixture tree that run is genuinely clean, and on the live tree it is no-worse than your own pre-measured baseline, so say which tree you used (F7). Paste an item carrying `- Gate-Kind:` parsing with its gate values intact.
  - Observed evidence: ALL MEASURED AT `git rev-parse HEAD` = `91cd3fa2fdd0eba6a4b431ba79b342592c18a122` (implementation commit); baseline readings at
    `bcbbfb077416d1796c7a7e406ef587b66b327e34` (its parent). NOTE ON TOOLING: `aw` resolves `agent_workflows` by CWD, and `--dir` does not
    change CWD, so every command below is invoked as `python3 -m agent_workflows ...` FROM this worktree.
    An early `aw backlog check --dir <tmp>` run silently exercised the MAIN checkout's unmodified copy and
    reported a false failure; that is a measurement artifact, recorded here so the evidence is reproducible.

    (1) FULL-LINE ANCHORING, not the bare token. `backlog.py:77-82`:
        _WORK_KIND_RE = re.compile(r"^- Work-Kind:[ \t]*(?P<value>\S+)[ \t]*$")
        _KIND_RE      = re.compile(r"^- Kind:[ \t]*(?P<value>\S+)[ \t]*$")
    Both carry `^- ` and `$`, so `- Gate-Kind: artifact` satisfies NEITHER. Asserted directly by
    `test_the_field_regexes_are_anchored_on_the_full_line`, which also pins that `- Work-Kind:` is not
    read as the legacy field. Precedence is resolved AFTER the scan (`item.kind = work_kind if
    work_kind is not None else legacy_kind`), so the canonical value wins regardless of line order
    rather than depending on which bullet happens to come first.

    (2) BOTH SPELLINGS PARSE (pasted from a run against this worktree's module):
        OLD  spelling -> kind = 'bug'
        NEW  spelling -> kind = 'bug'
        BOTH spellings -> kind = 'security' (canonical wins)
        GATE item -> kind = 'feature' gate_kind = 'decision' gate_ref = 'some-decision'

    (3) A TREE CONTAINING BOTH SPELLINGS, which is the exact state the migration passes through.
    Fixture tree at /tmp/opencode/dualread with three items, one legacy + two canonical:
        open/...abc123-legacy.backlog.md:5:- Kind: bug
        open/...abc126-canonical.backlog.md:5:- Work-Kind: feature
        blocked/...abc124-gate.backlog.md:5:- Work-Kind: chore
        $ python3 -m agent_workflows backlog check --dir /tmp/opencode/dualread
        aw backlog check: all backlog items conform.
        exit=0
    TREE USED: a THROWAWAY fixture tree, and on it the run is genuinely CLEAN (exit 0), as F7 predicted
    is possible off the live tree. The LIVE tree is reported under V-03 as no-worse-than-baseline, NOT
    clean, because it carries 3 pre-existing `backlog.summary-unsafe` violations outside this fence.

    (4) `- Gate-Kind:` PARSES WITH ITS GATE INTACT. The live tree's one carrier, after migration:
        file      : .aw/records/backlog/blocked/20260829-mergedirty-01-h1ksy6-pre-merge-dirty-check-scope.backlog.md
        kind      : 'bug'
        gate_kind : 'artifact'
        gate_ref  : '2c122z'
        drift     : []
    and its on-disk block reads `- Work-Kind: bug` above an untouched `- Gate-Kind: artifact`.

    (5) REAL-CALLER PROOF, the strongest evidence for this item (F8). 12 pre-existing test modules emit
    the OLD spelling as fixture data and were left UNEDITED; they pass unchanged through the dual-read
    window (the plan predicted 10; the tree grew to 12, all still unedited):
        $ python3 -m pytest -o addopts="" -q tests/test_agentadhere_policy_engine.py \
            tests/test_auto_index_on_mutation.py tests/test_backlog_blocking_close_gate.py \
            tests/test_backlog_graduated.py tests/test_backlog.py tests/test_check_engine_spec_handoff.py \
            tests/test_from_backlog.py tests/test_history_routing.py tests/test_release_gate_close.py \
            tests/test_releases_cli.py tests/test_releases.py tests/test_status_set.py
        229 passed in 5.25s
    `git status --porcelain tests/` showed only `?? tests/test_backlog_work_kind_rename.py`, proving none
    of them was edited to make this pass.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a newly created item showing `- Work-Kind:` on disk. Paste the validator accepting it, rejecting an out-of-vocabulary value, and STILL REJECTING an item with the field absent, which proves requiredness was preserved rather than quietly relaxed (F5). Paste the module's documented field list matching what it now writes. Paste both `--kind` and `--work-kind` working, per OQ-01's kept alias.
  - Observed evidence: MEASURED AT HEAD `91cd3fa2fdd0eba6a4b431ba79b342592c18a122`.

    (1) A NEWLY CREATED ITEM CARRIES THE CANONICAL SPELLING ON DISK:
        $ python3 -m agent_workflows backlog new --dir /tmp/opencode/e02 \
            --summary "test preferred spelling" --work-kind security --slug pref --apply
        aw backlog new: wrote /tmp/opencode/e02/.aw/records/backlog/open/20260830-5ha6gn-01-5ha6gn-pref.backlog.md
        - Id: 5ha6gn
        - Status: open
        - Set: 5ha6gn
        - Priority: medium
        - Work-Kind: security
        - Summary: test preferred spelling

    (2) BOTH FLAGS WORK, per OQ-01's kept alias. `--kind bug` also wrote the CANONICAL field:
        $ python3 -m agent_workflows backlog new --dir /tmp/opencode/e02 \
            --summary "test alias spelling" --kind bug --slug alias --apply
        - Work-Kind: bug
    and with neither flag the `chore` fallback is preserved: `- Work-Kind: chore`. Both flags parse to
    distinct dests with NO argparse default, so "was it passed?" stays answerable and the alias cannot
    mask the preferred spelling; `run_new` holds the fallback.

    (3) AN OUT-OF-VOCABULARY VALUE IS REJECTED:
        $ python3 -m agent_workflows backlog new --dir /tmp/opencode/e02 --summary bad --work-kind bogus --slug bad --apply
        aw backlog new: --work-kind must be one of ['bug', 'chore', 'feature', 'followup', 'security']
        exit=2

    (4) REQUIREDNESS PRESERVED (F5), the assertion this plan most needed to get right. An item with NO
    work-nature field is STILL a hard error, exactly as before the rename:
        $ python3 -m agent_workflows backlog check --dir /tmp/opencode/e02b
        20260830-demo-01-zzz999-nokind.backlog.md: backlog.kind-invalid: kind not in ['bug', 'chore', 'feature', 'followup', 'security']: None
        aw backlog check: 1 violation(s).
        exit=1
    The validator at `backlog.py:207` is still unconditional (`if item.kind not in KINDS`); the field was
    NOT moved into an `is not None` guard. V-04 pastes the falsification proving a test catches that.

    (5) THE MODULE'S DOCUMENTED FIELD LIST MATCHES WHAT IT WRITES. `backlog.py`'s docstring block now
    reads `- Work-Kind: bug | feature | chore | security | followup`, and a new paragraph records that
    the legacy spelling is still read, that only the canonical one is written, and that the field stays
    REQUIRED here (asymmetric with plans and specs by design). Asserted by
    `test_the_module_docstring_documents_the_canonical_spelling`.

    (6) ONE VOCABULARY, NO FORKS: `grep -rn 'frozenset(("bug"' agent_workflows/` returns exactly one line,
    `agent_workflows/backlog.py:70`. Pinned by `test_exactly_one_vocabulary_definition_is_consumed`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the counts after migration, DERIVED FROM THE PARSER and not from a tree-wide grep: parsed items carrying `- Work-Kind:` = every item (87 at `be49ac4`, re-measured at your HEAD), parsed items carrying `- Kind:` = 0, and items carrying `- Gate-Kind:` = 1. State explicitly that `README.md` is excluded from all three because the parser skips it, so a reviewer can tell your numbers from the misleading 88/2 a `grep -rl` produces (F1b). Paste `aw backlog check` before and during and after with NO `backlog.kind-invalid` finding and the pre-existing `backlog.summary-unsafe` set unchanged; do NOT claim clean (F7). Paste a `git diff` excerpt for two or three migrated items showing exactly ONE changed line each and no incidental reformatting. Paste `git diff --cached --name-only` before your commit proving no other session's file was swept in.
  - Observed evidence: MEASURED AT HEAD `91cd3fa2fdd0eba6a4b431ba79b342592c18a122`; baseline at `bcbbfb077416d1796c7a7e406ef587b66b327e34`.

    (1) COUNTS DERIVED FROM THE PARSER (`backlog._iter_items`), NOT a tree grep:
        parsed items          : 91
        carrying '- Work-Kind:': 91
        carrying '- Kind:'     : 0
        carrying '- Gate-Kind:': 1
    `README.md` IS EXPLICITLY EXCLUDED FROM ALL THREE, because `_iter_items` globs `*.md` and skips only
    that name. The plan's figure was 87 items at `be49ac4`; I re-measured 91 at my own HEAD, since other
    sessions add items continuously (the plan's CONCURRENCY RULE anticipated exactly this).

    (2) THE MISLEADING GREP, shown for contrast so the numbers above are checkable (F1b):
        grep -rl '^- Work-Kind:' = 91
        grep -rl '^- Kind:'      = 1   <- .aw/records/backlog/README.md ONLY, documentation, owned by E-06
        grep -rl '^- Gate-Kind:' = 2   <- 91-item corpus contributes 1; README.md is the other
    So a naive `grep` would report 92/2 where the parser reports 91/1. I am NOT pasting 92 and 2.

    (3) `Gate-Kind` UNCHANGED AT 1 ITEM AND STILL PARSING: the one carrier
    (`blocked/20260829-mergedirty-01-h1ksy6-...`) parses with `gate_kind='artifact'`, `gate_ref='2c122z'`,
    `kind='bug'`, and `drift = []`. `grep -rn 'Gate-Work-Kind' .aw/records/backlog/` returns ZERO hits,
    which is the signature a substring-anchored rename would have left.

    (4) EXACTLY ONE CHANGED LINE PER MIGRATED ITEM, proven over the WHOLE corpus rather than by sampling:
        $ git diff --numstat .aw/records/backlog/ | awk '{print $1"\t"$2}' | sort | uniq -c
             91 1	1
              1 8	2      <- .aw/records/backlog/README.md (E-06 documentation edit, not an item)
    91 files at 1 insertion + 1 deletion each, with the README the only exception. Two sample diffs:
        -- Kind: bug            /  +- Work-Kind: bug         (the Gate-Kind carrier; gate lines untouched)
        -- Kind: chore          /  +- Work-Kind: chore       (done/...xd78mr-e06-scenario-token-test-bindings.md,
                                                              the legacy-named item a `*.backlog.md` glob misses)
    The migration script anchored on `re.compile(r'^- Kind:...$', re.MULTILINE)` and asserted `n == 1`
    per file, so a second matching line anywhere would have aborted rather than silently rewritten.

    (5) `aw backlog check` NO WORSE AT THREE POINTS, and NOT claimed clean (F7):
        BEFORE (at `bcbbfb077416d1796c7a7e406ef587b66b327e34`, live tree): exit 1, `3 violation(s)`, all `backlog.summary-unsafe`, on
          `20260819-awagyfalseerror-01-uhbdt1`, `20260820-awhistignore-01-f7w55w`, `20260820-awinstallfix-01-av9hni`.
        DURING (tree carrying BOTH spellings): exit 0 on the throwaway fixture tree, pasted in V-01 (3).
        AFTER (at `91cd3fa2fdd0eba6a4b431ba79b342592c18a122`, live tree): exit 1, `3 violation(s)`, the SAME three items and the same rule.
    `backlog.kind-invalid` findings: 0 before, 0 during, 0 after. The pre-existing `summary-unsafe` set is
    unchanged and untouched: it is outside this plan's fence and I did not edit those three items.

    (6) STAGED-SET VERIFICATION BEFORE COMMITTING (the concurrency rule). `git status --porcelain` showed
    ONLY my own paths and `git diff --cached --name-only` was EMPTY before I staged, so no co-worker's work
    was pending. After staging, the set was 96 paths = 91 migrated items + README + `backlog.py` + `cli.py`
    + `command_surface.py` + the new test; I reviewed the full list and every path is one I modified. The
    commit was path-scoped, all 10 pre-commit hooks passed, and `git diff --cached --name-only` was re-run
    AFTER the commit and came back empty, confirming no hook-restore polluted the index.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the full test module passing. Paste FALSIFIABILITY as actual failures: the dual-read case failing when only the new spelling is accepted, and the `Gate-Kind` case failing under a substring-based rename. Paste the requiredness-preserved case passing and show it FAILS against an implementation that made the field optional. Confirm every case used a throwaway tree, not the live records.
  - Observed evidence: MEASURED AT HEAD `91cd3fa2fdd0eba6a4b431ba79b342592c18a122`.

    (1) THE FULL MODULE PASSES:
        $ python3 -m pytest -o addopts="" tests/test_backlog_work_kind_rename.py -q
        ..........................                                               [100%]
        26 passed in 0.30s
    `python3 -m ruff format --check` and `python3 -m ruff check` both clean on the module.

    (2) FALSIFIABILITY AS ACTUAL FAILURES. Each mis-implementation was really introduced, the suite really
    run, and the code then restored; these are observed failures, not predictions.

    (a) DUAL-READ REMOVED (accept only the new spelling) -> deleting the `_KIND_RE` branch from
        `parse_item` produced:
            FAILED ...::DualReadTests::test_legacy_spelling_still_parses
            FAILED ...::DualReadTests::test_a_tree_containing_both_spellings_validates
            FAILED ...::WriteSideTests::test_a_status_transition_rewrites_the_field_in_the_canonical_spelling
            3 failed, 23 passed in 0.47s
        with the primary assertion reading `AssertionError: 'bug' != None`-class failure. The third failure
        exposes the REAL-WORLD harm concretely: a status transition on a legacy item wrote
        `- Work-Kind: None`, i.e. silent data loss, not merely a parse miss.

    (b) FIELD MADE OPTIONAL (`if item.kind is not None and item.kind not in KINDS`) ->
            FAILED ...::RequirednessAndVocabularyTests::test_absent_work_kind_is_still_rejected
            E  AssertionError: 'backlog.kind-invalid' not found in []
            1 failed, 25 passed in 0.48s
        This is the F5 guard firing exactly as designed against the one change this plan forbids.

    (c) SUBSTRING-BASED RENAME (`text.replace("Kind:", "Work-Kind:")` applied to the real Gate-Kind
        carrier, corrupting it to `- Gate-Work-Kind: artifact`) ->
            FAILED ...::MigratedCorpusTests::test_no_item_lost_its_work_nature_value_in_the_migration
            FAILED ...::MigratedCorpusTests::test_the_gate_kind_field_survived_the_migration
            2 failed, 24 passed in 0.30s
        `test_a_substring_rename_would_have_corrupted_the_gate`
        additionally demonstrates the hazard in-process without touching the tree: the naive rewrite yields
        `parse_item(...).gate_kind is None` while the full-line rewrite preserves `'artifact'`.

    After each experiment the implementation was restored and re-verified green (26 passed), and the corpus
    diff shape returned to `91  1 1`.

    (3) THROWAWAY TREES CONFIRMED. Every constructive case builds under `TemporaryDirectory()`. The only
    assertions that read the LIVE records are the four `MigratedCorpusTests`, which are deliberately about
    the migration's actual deliverable (that no item retains the old spelling, none lost its value, the gate
    survived, and the README is documentation the parser never enumerated); they assert invariants rather
    than a fixed count, so a concurrent session adding an item cannot make them flake.

    (4) SUITE NO WORSE, both invocations, measured at my own HEAD rather than reusing the plan's numbers:
        FAST  `python3 -m pytest`      : baseline `bcbbfb077416d1796c7a7e406ef587b66b327e34` 15 failed, 3575 passed, 3 skipped, 4 xfailed
                                      -> HEAD `91cd3fa2fdd0eba6a4b431ba79b342592c18a122` 15 failed, 3601 passed, 3 skipped, 4 xfailed
        SLOW  `python3 -m pytest -m ""`: baseline 40 failed, 3939 passed, 3 skipped, 4 xfailed
                                      -> HEAD     40 failed, 3965 passed, 3 skipped, 4 xfailed
    Passing count rose by exactly +26 on both, which is this module. The failure SETS are IDENTICAL before
    and after (`diff` of the sorted `FAILED` lines reports no difference), so nothing regressed.
    HONEST DISCLOSURE, since these are not green runs: both failure sets are PRE-EXISTING and unrelated to
    this plan. The 15 fast failures are all `tests/test_run_viewer.py`, which read the real
    `.aw/records/runs/` directory; that directory does not exist in this lane worktree, so they fail
    environmentally (`discover_run_dirs` returns 0 runs) at the baseline commit too, with none of my changes
    applied. The slow set adds `test_runner_stop_level*`, `test_cli_conformance_matrix`,
    `test_command_surface_declarations`, and `test_cli.py::SubcommandDescriptionTests`. I specifically
    checked the two `command_surface`-adjacent ones because E-05 edits that file: they fail on UNDECLARED
    COMMAND LEAVES (65 of them, e.g. `runs`, `commit`, `config set`), an entirely different axis from the
    per-command `legacy_flags` tuple E-05 touches, and they fail identically at the baseline.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `backlog new` `legacy_flags` tuple showing BOTH `--work-kind` and the retained `--kind`. Paste a comparison of the declared flag set against what the parser actually accepts (`aw backlog new --help`) showing they agree. Paste `git diff --stat` for `command_surface.py` showing only that one declaration changed, and confirm no `ipd set` or `specs set` declaration was touched.
  - Observed evidence: MEASURED AT HEAD `91cd3fa2fdd0eba6a4b431ba79b342592c18a122`.

    (1) THE `backlog new` `legacy_flags` TUPLE, showing BOTH spellings with `--kind` RETAINED:
        ('--summary', '--set', '--status', '--priority', '--work-kind', '--kind', '--slug',
         '--gate-kind', '--gate-ref', '--blocks-release', '--message', '--body', '--apply')

    (2) DECLARED vs ACTUALLY ACCEPTED, showing they agree:
        $ python3 -m agent_workflows backlog new --help | grep -o -- '--[a-z-]*' | sort -u
        --agent --apply --blocks-release --body --dir --gate-kind --gate-ref --help --json --kind
        --message --no-color --priority --set --slug --status --summary --work-kind
    Every declared flag appears in the accepted set; the extras (`--dir --help --json --agent --no-color`)
    are global/renderer flags not carried in `legacy_flags`. `test_the_declaration_matches_the_parser`
    asserts `declared - accepted == set()` by walking the REAL parser `_build_parser()` builds, so the
    declaration cannot drift into being aspirational.

    (3) ONLY THAT ONE DECLARATION CHANGED:
        $ git diff --stat agent_workflows/command_surface.py
         agent_workflows/command_surface.py | 4 ++++
         1 file changed, 4 insertions(+)
    A pure addition: one `"--work-kind",` entry plus a 3-line comment, no deletions.
    `ipd set` and `specs set` are UNTOUCHED, verified by reading them back after the edit:
        ipd set   -> ('--message', '--by-human', '--actor', '--scope-reason', '--scope-ack', '--dry-run', '--json', '--agent')
        specs set -> ('--status', '--message', '--gate-kind', '--gate-ref', '--gate-summary',
                      '--blocks-release', '--evidence', '--by-human', '--date', '--dry-run', '--json', '--agent')
    Neither declares `--priority`, which is precisely the measurement F6 says does NOT transfer to this
    plan; `backlog new` DOES declare its flag, which is why E-05 exists at all and why child 02's
    "command_surface.py stays out of scope" conclusion was correctly not borrowed here.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `.aw/records/backlog/README.md` diff showing the field list now names `- Work-Kind:`. Paste a grep for the old full-line spelling across tracked documentation showing either no remaining hits or only hits outside `Scope-Paths`, which must be REPORTED rather than edited. Paste proof the README was NOT migrated as an item, namely that its diff is a documentation edit and that the parser's item enumeration never included it.
  - Observed evidence: MEASURED AT HEAD `91cd3fa2fdd0eba6a4b431ba79b342592c18a122`.

    (1) THE README DIFF now names the canonical field:
        --- a/.aw/records/backlog/README.md
        +++ b/.aw/records/backlog/README.md
        @@ -39,7 +39,7 @@
         - Priority: high | medium | low
        -- Kind: bug | feature | chore | security | followup
        +- Work-Kind: bug | feature | chore | security | followup
         - Summary: <one line>
         - Gate-Kind: <artifact|decision|todo|issue|date|external>   # iff blocked
    The `- Gate-Kind:` line two rows below is visibly UNCHANGED, which is the same distinction the code
    change turns on. Two further edits keep the file honest rather than merely renamed: a paragraph
    recording that the old spelling is still read while only the new one is written, and that backlog
    REQUIRES the field unlike plans and specs; and the `aw backlog new` verb line now advertises
    `--work-kind` (the alias stays accepted, it is simply no longer the documented spelling).

    (2) NO REMAINING OLD-SPELLING DOCUMENTATION HIT INSIDE THIS FENCE:
        $ git ls-files -z | xargs -0 grep -ln -- '^- Kind: \(bug\|feature\|chore\|security\|followup\)$'
        tests/test_auto_index_on_mutation.py
        tests/test_backlog_graduated.py
        tests/test_check_engine_spec_handoff.py
        tests/test_status_set.py
    All four are FIXTURE DATA in test modules, deliberately NOT in `Scope-Paths` and deliberately NOT
    edited (F8/F10): they are the dual-read window's real-caller evidence and pass unedited (V-01 (5)).
    They are REPORTED here, not touched. A wider sweep of tracked markdown for a backlog-style field
    description found exactly one hit outside the backlog tree:
        .aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md:86: "(`- Kind:`, see Section 4.4)"
    That is an IPD's STRUCTURAL kind (`child`/`orchestrator`), one of the four unrelated bookings of the
    token this rename exists to disambiguate. Correctly left alone; it is not backlog's field.

    (3) THE README WAS EDITED AS DOCUMENTATION, NEVER MIGRATED AS DATA. Its diff is 8 insertions and 2
    deletions, the ONLY file in the whole change whose shape is not `1 1` (see V-03 (4)); the 91 items are
    uniformly one line each. And the parser never enumerated it: `_iter_items` skips it by name, so it is
    absent from the 91-item target set E-03 rewrote. `test_the_readme_documents_the_canonical_spelling_and_is_not_an_item`
    asserts BOTH halves, that the file documents `- Work-Kind:` and that
    `readme not in backlog._iter_items(REPO_ROOT)`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 6 E-leaves across 2 task groups, well under the thresholds of 18 and 5. One concern throughout: move backlog's field to its new name safely. Right-sizing per leaf: E-01 dual-read, E-02 write side, E-05 the flag declaration, E-03 the corpus rewrite, E-06 the README, E-04 the tests. Each is one edit site with its own falsifiable check.

Open questions: ALL RESOLVED. OQ-01 keeps `--kind` as an alias. The decision to rename at all is the maintainer's, recorded in the superseded `a6cej0`; this plan implements it and does not relitigate it.

Scope fence: touch ONLY `agent_workflows/backlog.py`, the backlog records tree, the `backlog new` declaration in `agent_workflows/command_surface.py` (E-05 only, that one tuple), and the new test file. Do NOT touch the IPD schema, the spec contract, the check engine, or the CLI beyond backlog's own flag (child 02 owns those). Do NOT modify `Gate-Kind` handling. Do NOT rename the in-code vocabulary symbol. Do NOT make the field optional on backlog: it is required today and this is a pure rename (F5). Do NOT edit the 10 existing test modules that carry the old spelling as fixture data (F8); they must pass unedited through the dual-read window. If it seems to need more, STOP and report.

CONCURRENCY RULE, not optional: the backlog tree is live shared state and other sessions create and transition items continuously; three new items appeared in it while this plan was being written. Do the migration in ONE pass and re-count immediately. If an item is dirty or staged by someone else, leave it and report it rather than migrating it under them. Before every commit run `git diff --cached --name-only` and unstage anything that is not yours; at least one concurrent session had unrelated files STAGED while this plan was authored, so a path-scoped commit alone is not sufficient protection.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run, and never reuse this plan's recorded baseline as if freshly measured.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
