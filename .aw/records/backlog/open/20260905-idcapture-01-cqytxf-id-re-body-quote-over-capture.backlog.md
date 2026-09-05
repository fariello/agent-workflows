- Id: cqytxf
- Status: open
- Set: idcapture
- Priority: high
- Work-Kind: bug
- Summary: selectors._ID_RE harvests a body-quoted '- Id:' as an identity claim, so a doc that merely QUOTES an example id6 collides with the real artifact and makes it unresolvable to aw set/aw show (no --force escape)

## Workflow history
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
