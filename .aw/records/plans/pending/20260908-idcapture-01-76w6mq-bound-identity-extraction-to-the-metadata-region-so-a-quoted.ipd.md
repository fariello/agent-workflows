# IPD: Bound identity extraction to the metadata region so a quoted example id6 cannot claim a document

- Date: 2026-09-08
- Kind: child
- Concern: `selectors._ID_RE` is multiline and unanchored to position, so ANY `- Id: <id6>` line anywhere in a file claims that file's identity. A document that merely QUOTES an example metadata block is therefore read as ASSERTING the quoted id6, which collides with the real artifact and makes it unaddressable by the status verbs, with the refusal explicitly stating it is not overridable by `--force`. The trigger is ordinary prose (quoting the metadata format), so the documents most likely to break the tool are specs and research ABOUT `aw` itself. `_read_status` and `_read_setid` share the same whole-body scan and the same defect.
- Scope: Bound identity extraction to the artifact's METADATA REGION (the front-matter bullet block before the first `##` heading) for id6, status and setid alike; ADD a check rule reporting a metadata-shaped `- Id:` found outside that region so bounding surfaces the ambiguity rather than silently swallowing it (maintainer decision 2026-09-05: fix AND warn); and consolidate the near-duplicate `_FRONT_MATTER_ID_RE` so a fix cannot land in one reader and not the other. The fix is in the READER; the quoted example is legitimate cited content and must not be mangled.
- Scope-Paths: agent_workflows/selectors.py, agent_workflows/check_engine.py, tests/test_selector_zero_open.py, tests/test_id_metadata_region.py
- Item-Dependencies: none
- Status: to-review
- Set: idcapture
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 76w6mq
- From-Backlog: cqytxf

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `cqytxf`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none, despite being `Priority: high` / `Work-Kind: bug`. THE DEFECT IS FULLY LIVE, re-verified at HEAD `a2e0438a`: `_ID_RE` is unchanged (`selectors.py:111`), the research doc still quotes `- Id: uyeko5` at line 60, `selectors._read_id` on that file still returns `uyeko5`, and `aw set reviewed uyeko5` still FAILS with "Selector 'uyeko5' is a id6 collision matching multiple files (a data bug to fix, not overridable by --force)" naming both the real plan and the research doc, exit 2. ONE PART OF THE ITEM IS NOW MISLEADING AND MATTERS A LOT, because it would make a future reader think the bug was fixed: the item's second measured symptom, `aw check all` reporting `check.id6-collision` on the research doc, NO LONGER REPRODUCES. `aw check all` now reports ZERO id6-collision findings. THAT IS NOT A FIX; IT IS MASKING, and I traced it. `uyeko5` EXECUTED since the item was filed, so its plan moved to `.aw/records/plans/executed/`, and `check_engine._iter_type_files` skips retired records unless `include_retired` is passed (`check_engine.py:493`); measured `check_engine.is_retired(<the executed plan>, 'plans')` is True, and the executed plan is absent from the 70 plans the check scans while the research doc IS among the 76 research files scanned. So the collision has only ONE side visible to `aw check` and cannot be reported, while `selectors.resolve()` does NOT skip retired records and therefore still collides. NET EFFECT, which strictly worsens the item's severity rather than easing it: the repository-level detector is now BLIND to exactly the class of collision that still breaks the verbs. E-05 adds the warning rule the item asked for, which does not depend on both sides being scannable. THE BLAST RADIUS IS MEASURED AND TINY, which de-risks the reader change: scanning all 1006 tracked markdown files under `.aw/records/`, exactly ONE has a metadata-shaped `- Id:` line after its first `##` heading or more than one such line, and it is the `27rjro` research doc. So bounding the scan changes the resolved identity of exactly one file today. CONFIRMED the item's scope point 4: `_read_status` and `_read_setid` share the defect, measured on the same doc, returning `reviewed` and `runflags` harvested from the quoted block rather than from the doc's own YAML front matter.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a quotation a quotation. Identity should come from where an artifact DECLARES it, not from anywhere the pattern happens to match, so writing documentation about `aw`'s own metadata format cannot make a real plan unaddressable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: bound the region, once, for all three readers

- [ ] E-01 Define ONE metadata-region boundary helper in `selectors.py` and express it precisely, because every later item depends on exactly where the region ends. The region is the leading `- Key: value` bullet block BEFORE the first `##` heading; for a YAML-fenced document it is the leading `---` block. Handle the shapes actually present in the corpus rather than assuming one: bullet front matter (plans, specs, backlog, releases, reviews, prompts, walkthroughs) and YAML front matter (research, 105 of 107 files measured). A file with NO heading at all must still have a region (the whole leading bullet run), and a file whose first line is a `#` H1 title must not have its region truncated by that H1, since `##` is the boundary, not `#`.
  - Depends on: none
  - Expected outcome: a pure helper returning the metadata region's text for a given document, correct for bullet front matter, YAML front matter, an H1-then-bullets file, and a file with no `##` heading.
  - Execution state: pending

- [ ] E-02 Apply the region to `_read_id` (`selectors.py:245-247`), `_read_status` (`:250-252`) and `_read_setid` (`:304-309`) together, not just to id. The item's scope point 4 asks whether the other two share the defect; MEASURED AT HEAD `a2e0438a` ON THE LIVE INSTANCE, THEY DO: on the `27rjro` research doc, `_read_status` returns `reviewed` and `_read_setid` returns `runflags`, both harvested from the QUOTED plan block rather than from the doc's own YAML front matter (`status: todo`, `set: awmetastore`). Fixing only `_read_id` would leave two readers still asserting a quoted document's status and setid, which is the same bug producing wrong `aw find <status>` and `aw find <setid>` answers instead of a collision.
  - Depends on: E-01
  - Expected outcome: all three readers consult only the metadata region; on the `27rjro` doc none of them returns a value harvested from the quoted block.
  - Execution state: pending

- [ ] E-03 CONSOLIDATE the near-duplicate `_FRONT_MATTER_ID_RE` (`selectors.py:280`) with `_ID_RE` (`:111`) rather than fixing one and leaving the other, which is the item's scope point 3 and its stated reason is on the record: the comment block above the public readers records that both host runners previously carried private `_read_id` copies that DRIFTED, and that the public pair exists precisely so there is one definition per reader. MIND THE DELIBERATE DIFFERENCE, which must be preserved rather than flattened: `_ID_RE` requires exactly one space after the dash while `_FRONT_MATTER_ID_RE` uses `^-\s*Id:` and tolerates any whitespace, and the comment explains that widening the strict one was NOT an option because `_STATUS_RE`'s strictness is a documented MATCHING-BEHAVIOR CONTRACT that deliberately disagrees with `plans_index._META_RE` on 24 records. So consolidate the REGION-BOUNDING, not the whitespace tolerance: both readers must become region-bounded while keeping their own patterns. Also decide and record whether the PUBLIC readers (`read_front_matter_id` `:287-294`, `read_front_matter_status` `:297-304`), which both host drivers consume, should be region-bounded too; a driver reads PLAN front matter where the region is unambiguous, so bounding them is safe and consistent, but it is a change to a shared runner-facing reader and must be a stated decision rather than a side effect.
  - Depends on: E-02
  - Expected outcome: both id readers are region-bounded, their distinct whitespace patterns are unchanged, and the public readers' treatment is a recorded decision.
  - Execution state: pending

### Task group 2: warn rather than swallow

- [ ] E-04 Fix the LIVE INSTANCE by the reader change alone and prove the doc was not touched. The item is explicit: "Do not mangle the quoted example (it is legitimate cited content); the fix is in the reader, not the doc." After E-02, `aw set reviewed uyeko5` must resolve the single real plan, and the research doc must keep its quoted `- Id: uyeko5` line byte-for-byte. Verify with `git diff` over `.aw/records/research/` showing no change.
  - Depends on: E-02
  - Expected outcome: `aw set reviewed uyeko5` resolves exactly one file (the plan) and exits 0 in dry-run; the research doc is unmodified.
  - Execution state: pending

- [ ] E-05 Add the CHECK RULE the maintainer required, so bounding the scan surfaces the ambiguity instead of hiding it (recorded decision 2026-09-05: fix AND warn, not fix quietly). The rule reports a metadata-shaped `- Id:` found OUTSIDE the metadata region. Register it with the existing rule machinery in `check_engine.py` alongside the identity family (`check.id6-collision`, `check.id6-identity-slot`), and choose its severity deliberately: a quoted example is LEGITIMATE content, so this should WARN rather than error, or the repository would fail its own check for documenting itself. THIS RULE IS NOW MORE IMPORTANT THAN THE ITEM KNEW, because the collision detector has gone blind: `check_collisions` skips retired records (`check_engine.py:493`, `is_retired`), and since `uyeko5` executed, the plan side of the live collision is no longer scanned, so `aw check all` reports ZERO id6-collision findings while `aw set uyeko5` still fails. A rule keyed on the outside-the-region SHAPE needs only one side and therefore still fires.
  - Depends on: E-01
  - Expected outcome: a new warn-severity rule that flags the `27rjro` doc today, does not flag any conformant artifact, and fires independently of whether the colliding counterpart is retired.
  - Execution state: pending

- [ ] E-06 REPORT, and do not fix, the retired-record blindness in `check_collisions`, because it is a distinct defect discovered while verifying this item and fixing it is a separate scope decision. MEASURED: `check_engine.is_retired(<executed plan>, 'plans')` is True and `_iter_type_files` excludes it unless `include_retired=True` (`check_engine.py:493`), so a collision between a RETIRED artifact and a live one is undetectable by `aw check` while remaining fully live for `selectors.resolve()`, which does not skip retired records. State this in the plan's findings and, if the reviewer wants it fixed, expect a separate item rather than widening this fence: making `check_collisions` scan retired records changes what the repository-level check reports across the whole executed corpus and could surface a large batch of pre-existing findings.
  - Depends on: E-05
  - Expected outcome: the divergence is recorded with its measurement; no change to `_iter_type_files`' retired filtering in this plan.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-07 Test the matrix, extending the module that already owns selector behavior. `tests/test_selector_zero_open.py` holds the resolver's dialect and precedence cases and is the natural home for the resolution assertions; put the region helper's own unit cases in the new module. Cover: a doc quoting `- Id: <other-id6>` in its BODY does not resolve as that id6 (the item's first required regression); `aw set <id6>` still resolves the genuine artifact; the `27rjro` doc no longer collides; the new outside-the-region warning fires on it; `_read_status` and `_read_setid` are likewise unaffected by a quoted block; and the region helper's four shapes from E-01. PRESERVE THE PRECEDENCE CONTRACT: the resolver's documented order is path -> id6 -> setid -> status -> stem -> substring, and a doc whose quoted id6 no longer resolves via MATCH_ID6 may still match by FILENAME substring, which is correct and must be asserted rather than accidentally forbidden.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: all six cases plus the region-shape units pass, and the first regression case fails against HEAD `a2e0438a`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.py` is the ONE selector-to-file resolver for every verb (`rename`, `group`, `set`/`ipd set`/`spec set`/`backlog set`, `show`, `find`, `archive`, the set-assign/mv paths), so a change here reaches MUTATING verbs, not only readers. That is why the blast-radius measurement matters more than usual.
- There are deliberately TWO tiers of reader: strict internal ones for selector matching, and permissive PUBLIC ones (`read_front_matter_id`, `read_front_matter_status`) that both host drivers consume, created because the drivers previously carried private copies that drifted.
- `_STATUS_RE`'s strictness is a documented MATCHING-BEHAVIOR CONTRACT: its `(\S+)` deliberately disagrees with `plans_index._META_RE` on 24 of 469 plans carrying a multi-word `- Status:`. Do not harmonize the patterns while region-bounding them.
- The resolver reads a BOUNDED 4096-byte header (`_HEADER_BYTES`) for the front-matter rules, so a region boundary must be found within that window; the quoted block at line 60 of the live instance is well inside it, which is exactly why the bug bites.
- `check_collisions` covers all eight `SUPPORTED` types INCLUDING research, but `_iter_type_files` EXCLUDES retired records by default. Those two facts together are what masked the live collision.
- The precedence chain and the artifacts-not-mentions rule are the resolver's published contract; a token appearing only in a body must never resolve, which is the principle this plan extends from bodies-in-general to quoted-metadata-in-particular.
- `.aw/inbox/` was deliberately sited OUTSIDE `.aw/records/` because a dropped external report that quoted an example block was harvested the same way. That placement removed the inbox exposure only; this reader bug remains live for every tracked artifact.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The pattern is unchanged and unbounded: `_ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")`, applied to a whole file body. | `selectors.py:111` at `a2e0438a` |
| F-2 | THE COLLISION IS STILL LIVE: `aw set reviewed uyeko5` fails with "id6 collision matching multiple files ... not overridable by --force", naming the real plan and the research doc, exit 2. | measured at `a2e0438a` |
| F-3 | The reader still harvests the quotation: `selectors._read_id(<27rjro doc>)` returns `uyeko5`, while the doc's own front matter says `id: 27rjro`. | measured at `a2e0438a` |
| F-4 | THE ITEM'S SECOND SYMPTOM NO LONGER REPRODUCES, AND THAT IS MASKING RATHER THAN A FIX: `aw check all` now reports ZERO `check.id6-collision` findings. | measured at `a2e0438a` |
| F-5 | The cause of the masking: `uyeko5` EXECUTED, so its plan is retired; `check_engine.is_retired(<that plan>,'plans')` is True and `_iter_type_files` skips retired records, so only ONE side of the collision is scanned (70 plans scanned, the executed plan absent; 76 research files scanned, the doc present). | `check_engine.py:493`; measured at `a2e0438a` |
| F-6 | So the repository detector is now BLIND to a collision the verbs still hit, because `selectors.resolve()` does NOT skip retired records. That makes the item MORE severe, not less. | measured: `aw check all` clean vs `aw set uyeko5` exit 2 |
| F-7 | THE BLAST RADIUS IS ONE FILE: across all 1006 tracked markdown files under `.aw/records/`, exactly one has a metadata-shaped `- Id:` after its first `##` heading or more than one such line, and it is the `27rjro` research doc. | measured at `a2e0438a` |
| F-8 | THE ITEM'S SCOPE POINT 4 IS CONFIRMED: on the same doc `_read_status` returns `reviewed` and `_read_setid` returns `runflags`, both harvested from the quoted block instead of the doc's own `status: todo` / `set: awmetastore`. | measured at `a2e0438a` |
| F-9 | The near-duplicate reader exists and must be consolidated in the same pass, with its deliberate whitespace difference preserved. | `_ID_RE` `selectors.py:111` vs `_FRONT_MATTER_ID_RE` `:280`; the drift rationale in the comment block above the public readers |
| F-10 | The quoted content is legitimate cited material: the doc quotes a real IPD metadata block to discuss where metadata should live, which is precisely the self-documentation case the item says will keep recurring. | `.aw/records/research/20260905-awmetastore-00-27rjro-...research-prompt.md:57-61` |
| F-11 | Nothing else covers this: no pending or approved plan and no spec touches `_ID_RE`, the metadata region, or id6 over-capture. | grep over `.aw/records/plans/pending/` and `.aw/records/specs/` at `a2e0438a` |

## Proposed changes (ordered, validatable)

1. Add one metadata-region helper handling bullet and YAML front matter (E-01).
2. Bound `_read_id`, `_read_status` and `_read_setid` to that region (E-02).
3. Consolidate the near-duplicate id reader's region-bounding, preserving its whitespace pattern (E-03).
4. Confirm the live collision is resolved by the reader change alone, doc untouched (E-04).
5. Add the warn-severity outside-the-region rule (E-05).
6. Record, without fixing, the retired-record blindness in `check_collisions` (E-06).
7. Pin the six regressions plus the region-shape units (E-07).

## Deferred / out of scope (with reason)

- FIXING `check_collisions`' RETIRED-RECORD BLINDNESS (F-5, F-6). A real and newly discovered defect, but scanning retired records changes what the repository check reports across the whole executed corpus and could surface a large batch of pre-existing findings. E-06 records it for its own item rather than widening this fence.
- EDITING THE `27rjro` RESEARCH DOC. Explicitly forbidden by the item and correct: the quotation is legitimate cited content and the fix belongs in the reader.
- HARMONIZING `_STATUS_RE` WITH `plans_index._META_RE`. A separate documented contract change affecting 24 plans, unrelated to region bounding.
- TEACHING THE RESOLVER THE YAML DIALECT for MATCHING purposes (making research id6/status/setid resolvable via the content rules). That is backlog item `05aqbj`, already graduated to plan `xo3244` (Set `selfmdialect`, `- Status: to-review`, `From-Backlog: 05aqbj`). THE TWO INTERACT AND THE EXECUTOR MUST CHECK: `xo3244` makes the YAML block matchable, and this plan bounds WHERE a match may come from. They are complementary rather than conflicting (a region-bounded YAML read is exactly what both want), but both touch `selectors.py` and the same three readers, so whichever lands second must re-read the first's changes rather than assuming.
- THE `.aw/inbox/` SITING. Already done (commit `b534fee9`) and only removed the inbox exposure; nothing further here.

## Scope check

- Over-scope: `agent_workflows/check_engine.py` is in `Scope-Paths` for E-05's warning rule, which the maintainer required as a condition of the fix ("fix AND warn"), so it is in scope by that ruling rather than by the reader defect alone.
- Under-scope: the retired-record blindness is reported, not fixed. No document is edited. The public runner-facing readers' treatment is a recorded decision in E-03 rather than an assumed change.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_selector_zero_open.py tests/test_id_metadata_region.py` for the focused surface, plus any `aw find` or `check` module the change touches.
- A before/after resolution comparison over all eight `SUPPORTED` types, proving no artifact other than the one measured file changes its resolved id6, status or setid.
- `python3 -m agent_workflows check all` before and after, with the new rule's finding shown and no OTHER rule's finding count changed.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

No `.spec.md` file defines the metadata region or the identity-extraction boundary, so none is edited and none is declared in `Scope-Paths`. The authoritative documentation is in code and must be kept truthful: `selectors.py`'s module docstring describes the dialects and the precedence chain, and the `resolve()` docstring enumerates the six rules, so E-02/E-03 must state that the content rules read the METADATA REGION rather than the whole body. DECISIONS D140 governs the filename identity slot and is adjacent but untouched: this plan changes where a DECLARED id is read from, not what a filename slot means. If the executor concludes the region boundary deserves a written contract beyond a docstring (a reasonable position, since `aw check` will now enforce a rule about it), propose it as a follow-up rather than amending a spec inside this fence.

## Open questions

### OQ-01: Should the outside-the-region rule WARN or ERROR?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED with WARN recommended, and the reasoning is concrete rather than stylistic. A quoted metadata block is LEGITIMATE content that this repository produces by design (it documents its own formats), so an error-severity rule would make the repository fail its own check for correct behavior, which is precisely the failure mode recorded in backlog `gjadwm`: "a gate that false-positives on correct behavior TRAINS agents to bypass it." WARN surfaces the ambiguity, which is all the maintainer's fix-and-warn ruling requires. Counter-argument a maintainer may prefer: once the reader is bounded, an out-of-region `- Id:` is always either a quotation (harmless) or a misplaced declaration (a real defect), and erroring would force the second case to be fixed; if that is wanted, the rule needs a way to distinguish the two, which WARN does not require.

### OQ-02: Should the PUBLIC runner-facing readers be region-bounded too?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE FROM THE CODE, recorded so it is deliberate rather than incidental. `read_front_matter_id` and `read_front_matter_status` are consumed by BOTH host drivers, and their documented failure mode is that a missed read silently degrades a runner to a directory-derived status, so a change there is not free. RECOMMENDATION: bound them too, because a driver reads PLAN front matter where the region is unambiguous, and leaving them unbounded would recreate exactly the reader drift the public pair was created to end. Verify by checking every driver call site before changing them, and if any consumer legitimately needs a whole-body read, leave that one unbounded and say why.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the helper's source and its output for four inputs shown individually: a bullet-front-matter plan, a YAML-fenced research doc, a file whose first line is an H1 followed by bullets, and a file with no `##` heading at all. For each, show the returned region text and confirm it stops at the right boundary.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the three readers' returns for the `27rjro` doc BEFORE (`uyeko5` / `reviewed` / `runflags`) and AFTER (none of them harvested from the quoted block), and paste the same three readers' returns for a normal plan before and after showing them byte-identical. Both runs must be shown, not described.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff` of both id readers showing each became region-bounded while its OWN whitespace pattern is unchanged (the strict single-space one and the `\s*` one must still differ). Paste a test proving a bullet written `-  Id: abc123` with two spaces is still read by the permissive reader and still NOT by the strict one. State the OQ-02 decision and paste the evidence behind it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw set reviewed uyeko5 --dry-run` BEFORE (exit 2, collision naming two files) and AFTER (resolves the single plan), with exit codes measured UNPIPED. Paste `git diff -- .aw/records/research/` showing an EMPTY diff, proving the doc was not mangled.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new rule's registration (name and severity), its finding on the `27rjro` doc, and a full `aw check all` before/after finding-count comparison showing the new rule appears and NO other rule's count changed. Paste a conformant artifact NOT being flagged.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the measurement of the retired-record blindness at execution time: `is_retired` on an executed plan, the scanned-file counts per type, and the contrast between `aw check all` (clean) and a `selectors.resolve()` collision on the same pair. Paste `git diff -- agent_workflows/check_engine.py` limited to `_iter_type_files` showing its retired filtering was NOT changed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste all six regression cases and the region-shape units with their names and results, the first case FAILING against pre-change code, and an assertion that a doc whose quoted id6 no longer matches by id6 may still match by filename substring (proving the precedence chain was preserved rather than accidentally narrowed). Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. A reviewer should note F-4 through F-6: the item's `aw check` symptom disappeared through MASKING, not repair, and the repository detector is now blind to the very collision class the verbs still hit, which makes E-05's warning rule load-bearing rather than cosmetic.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE OVERLAP: plan `xo3244` (`selfmdialect`, `From-Backlog: 05aqbj`) also edits `selectors.py` and the same three readers, so re-read the file at execution time and compose with whatever has landed rather than assuming these coordinates; and remember this resolver serves MUTATING verbs, so a regression here misdirects a write, not merely a read. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
