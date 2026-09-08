- Id: f8m2z2
- Status: graduated
- Set: findtwotier
- Priority: medium
- Work-Kind: feature
- Summary: re-author aw find as two-tier filesystem-first (maintainer ruling 2026-08-31 displaced e32j35's index-first design): filename listing 20ms vs 357ms, content fallback mandatory for status queries and 8 legacy records

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to the findtier Set: 826o13 (Order 01, filename-first candidate filter) and 3i6rso (Order 02, report records whose declared Id or Set is absent from their filename). Every measurement re-verified and THREE MOVED. (1) The timing gap WIDENED: 6ms for a filename listing versus 429ms for aw find, against the item's 20ms/357ms, because the corpus grew to 582 indexed plans. (2) The status-query trap re-measured: -iname '*approved*' returns 5 files NONE of which is approved, while 17 pending plans genuinely are (item recorded 3 and 16). (3) The absent-from-filename set is NINE, not 8, and the ninth is NOT a legacy name: it is uyeko5 'declared' by research prompt 27rjro, the quoted-example parser artifact owned by cqytxf/76w6mq, so it must not be counted as a permanent exception. THE ARTIFACTS-NOT-REFERENCES CONTRACT WAS TESTED: -iname '*wtiso*' returns 12 files including the different Set wtisoland, while aw find plans wtiso returns 3. THE DESIGN IS CONSTRAINED BY THE ITEM'S OWN INHERITED CORRECTION: PrecedenceForcesFrontMatterReadsTests proves a stem or substring query cannot be read-free while _PRECEDENCE is frozen, so tier 1 is authored as a CANDIDATE FILTER rather than a precedence change, and the mandatory content fallback stays. Order 02 exists because the exception set must be VISIBLE and shrinking before that fallback can ever be retired. Noted overlap: three pending plans (76w6mq, xo3244, paw8so) already edit selectors.py. No Blocks-Release on the item, so neither plan inherits one.
- 2026-09-01 created (aw backlog): filed by IPD e32j35: its OQ-03 resolution re-scoped the design but the plan's E-items still encoded the displaced index-first premise

FILED BY IPD `e32j35` DURING EXECUTION. That plan carried the maintainer's 2026-08-31 re-scope in its
OQ-03 resolution AND in its Findings, and both say the same thing in the plan's own words: "this plan
needs re-authoring, not just re-approval", because "E-01/E-02/E-04 rest on the index-first premise the
maintainer just displaced". The re-scope was recorded rather than implemented, deliberately, since a
change of that size is AUTHORING. This item is that authoring work, so the requirement is not carried
only inside a plan whose remaining E-items were withdrawn.

THE DESIGN THE MAINTAINER RULED FOR, measured with them on 2026-08-31:

- TIER 1, a plain filename listing (`find <records dirs> -iname '*<term>*'`) answers the common case
  in ~20ms against ~357ms for `aw find plans <id6>` at the time, over 449 plan files. The directory
  listing, not a manifest, is the cheap path, and it needs NO freshness primitive because it reads the
  filesystem directly. This is what displaced `e32j35`'s index-first premise.
- TIER 2, the existing bounded-header content scan, entered when tier 1 yields nothing AND always for
  status queries. It costs full price but runs rarely.

THE FALLBACK IS NOT OPTIONAL, and each reason was measured, not assumed:

- STATUS QUERIES ARE IMPOSSIBLE FROM FILENAMES. `Status:` is content. `-iname '*approved*'` returned 3
  files, NONE of them approved (an `open` backlog item about the word, a `done` item, and a plan
  literally named `auto-approved` whose status is `executed`), while 16 plans in `pending/` genuinely
  were `approved`.
- 8 RECORDS CARRY AN Id/Set ABSENT FROM THEIR FILENAME. Re-verified 2026-09-01 at this item's filing:
  8 of 751 records scanned (1.1%). Five are plans with pre-id6-grammar legacy names (`4o5lt9`,
  `wvlk84`, `lus9ou`, `8q6yr9`, `7qx7ys`) and three are grandfathered legacy spec names (`4w7d6s`,
  `25kzda`, `5tapom`). `find -iname '*lus9ou*'` returns ZERO hits while `aw find plans lus9ou` finds
  it. Note `25kzda` is a spec this repo cites constantly, so filename-only matching would make it
  uncitable.
- QUOTING MUST BE NORMALIZED. One apparent ninth miss was a false positive from front matter reading
  `` set: `awoptimize` `` with backticks. Compare stripped, or the tool reports phantom drift.

TWO REQUIREMENTS THE MAINTAINER ADDED, neither implied by the original plan:

1. SEMANTICS AS A CONTRACT: `find` returns matching ARTIFACTS, never references. `aw find plans
   123abc` must return only the artifact that IS `123abc`, never ones that mention, cite or concern
   it. Today's behavior already conforms (1 record for `y6mfgo` while 6 plans mention it; a `wtiso`
   query correctly EXCLUDES the different Set `wtisoland`) and any rewrite MUST preserve it. This is
   the argument against a naive `find | grep`, which conflates the two: the maintainer's own trial of
   `-iname '*wtiso*'` returned `wtisoland` plans, a session-handoff prompt and a research report.
2. RAISE NON-CONFORMING FILENAMES rather than silently tolerating them, because the long-term prize is
   being able to TRUST filenames and retire the content fallback, which is only reachable if the
   exception set is visible and shrinking. There is NO signal today: both a legacy plan name and a
   legacy spec name return `is_conformant=True` from the shipped normalizer, so `check_engine`'s
   naming rule skips them (`check_engine.py:462`). WANTED: an ADVISORY report naming every record
   whose `Id`/`Set` is absent from its filename, with the exact `aw rename` that would fix it.
   EXPLICITLY NOT auto-rename: `executed/` plan bodies are immutable by policy and the grandfathered
   specs are a documented decision, so each rename is a maintainer call per record.

WHAT `e32j35` ALREADY LANDED, so this item does not redo it: the text-free path enumeration
(`selectors._iter_paths`) that tier 1 needs, sharing ONE traversal with the header-reading view; the
`Status:` parity constraint documented at both regexes; and the research dialect exclusion (see
`05aqbj`).

A CORRECTION THIS ITEM MUST INHERIT, found while executing `e32j35` and proven in
`tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests`: a stem or substring QUERY
cannot be made read-free while PRECEDENCE stays frozen, because `stem`/`substring` sit LAST and the
resolver must first prove that `setid`/`status` did not match, which requires front matter. A token
really can be both a Set id and a filename fragment. So a two-tier design that wants tier 1 to answer
WITHOUT reading must state explicitly what happens to precedence - either it changes (a matching
change needing sign-off) or tier 1 is a candidate FILTER whose winner is still decided by the frozen
order. The original plan's E-05 target overlooked this; do not re-inherit the oversight.

RELATED. `e32j35` (findidx) is the displaced plan; `05aqbj` is the research front-matter dialect gap;
`h2ceme` asks that `aw find` flag a duplicate id6 and explicitly notes it "should probably be folded
into that re-authoring"; `ila6vl` is the decision to stop tracking the INDEX manifests, whose basis
cites this re-scope as having removed the speed argument for the index.
