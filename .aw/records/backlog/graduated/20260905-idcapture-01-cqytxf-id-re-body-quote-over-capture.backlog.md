- Id: cqytxf
- Status: graduated
- Set: idcapture
- Priority: high
- Work-Kind: bug
- Summary: selectors._ID_RE harvests a body-quoted '- Id:' as an identity claim, so a doc that merely QUOTES an example id6 collides with the real artifact and makes it unresolvable to aw set/aw show (no --force escape)

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan 76w6mq (Set idcapture, .aw/records/plans/pending/20260908-idcapture-01-76w6mq-...ipd.md), which carries From-Backlog: cqytxf. This item carries no Blocks-Release, so the plan inherits none. Status graduated (design handed off), NOT done. THE DEFECT IS FULLY LIVE, re-verified 2026-09-08 at HEAD a2e0438a: _ID_RE is unchanged at selectors.py:111, the 27rjro research doc still quotes '- Id: uyeko5' at line 60, selectors._read_id on that file still returns uyeko5, and 'aw set reviewed uyeko5' still FAILS with 'id6 collision matching multiple files (a data bug to fix, not overridable by --force)' naming both the real plan and the research doc, exit 2. ONE OF THIS ITEM'S TWO MEASURED SYMPTOMS NO LONGER REPRODUCES, AND IT IS MASKING RATHER THAN A FIX. This is the most important correction to record, because a future reader would otherwise conclude the bug was fixed: 'aw check all' now reports ZERO check.id6-collision findings. I traced the cause. uyeko5 EXECUTED since this item was filed, so its plan moved to .aw/records/plans/executed/, and check_engine._iter_type_files EXCLUDES retired records unless include_retired is passed (check_engine.py:493). Measured: check_engine.is_retired(<that executed plan>, 'plans') is True, the executed plan is ABSENT from the 70 plans the check scans, while the research doc IS among the 76 research files scanned. So the collision now has only ONE side visible to aw check and cannot be reported, while selectors.resolve() does NOT skip retired records and therefore still collides. NET EFFECT: the repository-level detector is now BLIND to exactly the class of collision that still breaks the verbs, which makes this item MORE severe than filed, not less. The plan's E-05 (the warning rule this item's maintainer decision required) is therefore load-bearing rather than cosmetic, because a rule keyed on the outside-the-region SHAPE needs only one side and still fires. THAT RETIRED-RECORD BLINDNESS IS A SEPARATE DEFECT and is deliberately NOT fixed by the plan: making check_collisions scan retired records would change what the repository check reports across the whole executed corpus and could surface a large batch of pre-existing findings, so the plan's E-06 records it for its own item. SCOPE POINT 4 IS CONFIRMED, measured on the same doc: _read_status returns 'reviewed' and _read_setid returns 'runflags', both harvested from the QUOTED block rather than the doc's own YAML front matter (status: todo, set: awmetastore), so all three readers share the whole-body scan defect and the plan bounds all three together. THE BLAST RADIUS IS MEASURED AND TINY, which de-risks the reader change considerably: across all 1006 tracked markdown files under .aw/records/, exactly ONE has a metadata-shaped '- Id:' after its first '##' heading or more than one such line, and it is the 27rjro doc. So bounding the scan changes the resolved identity of exactly one file today. SCOPE POINT 3 (consolidate with _FRONT_MATTER_ID_RE at selectors.py:280) is graduated with one refinement recorded: the two patterns differ DELIBERATELY in whitespace tolerance, and the comment block above the public readers explains that widening the strict one was rejected because _STATUS_RE's strictness is a documented matching-behavior contract disagreeing with plans_index._META_RE on 24 records, so the plan consolidates the REGION-BOUNDING and preserves the distinct patterns. NOTED OVERLAP the executor must handle: plan xo3244 (Set selfmdialect, From-Backlog: 05aqbj, to-review) also edits selectors.py and the same three readers to teach them the YAML dialect. The two are complementary (a region-bounded YAML read is what both want) but whichever lands second must re-read the first's changes.
- 2026-09-05 created (aw backlog): selectors._ID_RE harvests a body-quoted '- Id:' as an identity claim, so a doc that merely QUOTES an example id6 collides with the real artifact and makes it unresolvable to aw set/aw show (no --force escape)

Problem: `selectors._ID_RE` (`agent_workflows/selectors.py:110`) is
`re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")`, applied to a whole file body via `_read_id`. It is
multiline and unanchored to position, so ANY line anywhere in a document claims that document's
identity. A doc that merely QUOTES an example metadata block is therefore read as asserting the
quoted id6.

MEASURED, LIVE IN THIS REPO (2026-09-05, at HEAD b977b43b):
`.aw/records/research/20260905-awmetastore-00-27rjro-where-aw-metadata-should-live.research-prompt.md`
has front matter `id: 27rjro` (line 2) but quotes an example IPD block containing `- Id: uyeko5` at
line 60. `uyeko5` is the real id6 of
`.aw/records/plans/pending/20260903-runflags-01-uyeko5-wire-the-spec-2-1-run-flag-surface-onto-both-host-runners.ipd.md`.
Result:

    $ aw set reviewed uyeko5
    FAIL  Selector 'uyeko5' is a id6 collision matching multiple files
          (a data bug to fix, not overridable by --force):
      .../plans/pending/20260903-runflags-01-uyeko5-...ipd.md
      .../research/20260905-awmetastore-00-27rjro-...research-prompt.md

    $ aw check all      # -> Issue: check.id6-collision on the research doc

Severity: a real plan's id6 becomes UNADDRESSABLE by the status verbs, and the refusal explicitly
says it is not overridable by `--force`, so there is no operator escape hatch. The trigger is
ordinary prose (quoting the metadata format), which means the docs MOST likely to break the tool are
specs/research about `aw` itself. Self-inflicted on this repo by construction.

Scope of the fix:
1. Bound identity extraction to the artifact's METADATA REGION rather than the whole body (the front
   matter block, or the leading `- Key: value` bullet region before the first `##` heading), so a
   quotation deeper in the document cannot assert identity.
2. Add a `check` rule that REPORTS a metadata-shaped `- Id:` found outside the metadata region, so
   bounding the scan surfaces the ambiguity instead of silently swallowing it (maintainer decision
   2026-09-05: fix AND warn, not fix quietly).
3. Consolidate with `_FRONT_MATTER_ID_RE` (`selectors.py:273`), a near-duplicate with looser
   whitespace (`^-\s*Id:`). The comment at `:257` records that host runners previously carried
   private `_read_id` copies that drifted; a fix landing in only one of the two regexes recreates
   exactly that drift.
4. Consider whether `_read_status`/`_read_setid` share the defect (same whole-body scan shape) and
   fix them in the same pass if so.

Also fix the LIVE instance: the `27rjro` research doc's collision must stop being reported. Do not
mangle the quoted example (it is legitimate cited content); the fix is in the reader, not the doc.

Validation: a regression test that a doc quoting `- Id: <other-id6>` in its BODY does not resolve as
that id6; that `aw set <id6>` still resolves the genuine artifact; that `aw check all` reports no
`check.id6-collision` for `27rjro`; and a test for the new outside-the-metadata-region warning.

Discovered while siting the `.aw/inbox/` raw-drop lane (commit b534fee9): a dropped external report
that quoted an example block was harvested the same way, which is WHY the inbox lane was placed
outside `.aw/records/`. That placement removes the inbox exposure only; this reader bug remains live
for every tracked artifact.
