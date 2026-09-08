# IPD: Add a filename-first tier to aw find as a candidate filter under the frozen precedence

- Date: 2026-09-08
- Kind: child
- Concern: `aw find` READS RECORD FILE BODIES TO ANSWER A QUESTION THE FILENAME USUALLY ANSWERS, AND THE GAP IS 70x. Re-measured at HEAD: `find .aw/records -iname '*lus9ou*'` returns in 6ms while `aw find plans lus9ou` takes 429ms. The item's own figures were 20ms against 357ms over 449 plan files; the corpus has since grown (582 plans indexed) and the ratio widened rather than closed, so the maintainer's 2026-08-31 ruling that the DIRECTORY LISTING is the cheap path still holds and is the design this plan implements.
  THE MANDATORY FALLBACK IS NOT NEGOTIABLE AND BOTH OF ITS REASONS RE-MEASURED TRUE. FIRST, STATUS QUERIES ARE IMPOSSIBLE FROM FILENAMES: `find -iname '*approved*'` returns FIVE files, NONE of which is an approved plan (two `apprvguard` plans about the word, one `w6mqc0` plan about writing it, and one literally named `auto-approved` whose status is `executed`), while SEVENTEEN plans in `pending/` genuinely carry `- Status: approved`. SECOND, RECORDS EXIST WHOSE DECLARED IDENTITY IS ABSENT FROM THEIR FILENAME: measured NINE at HEAD (the item recorded 8 of 751), and one of them is `25kzda`, a spec this repository cites constantly, so filename-only matching would make it uncitable.
  THE NINTH IS NEW AND IS NOT A LEGACY NAME, which matters for how this plan counts its exception set. Eight are genuine pre-id6-grammar names (`4o5lt9`, `wvlk84`, `lus9ou`, `8q6yr9`, `7qx7ys`, and grandfathered specs `4w7d6s`, `25kzda`, `5tapom`). The ninth is `uyeko5` "declared" by research prompt `27rjro`, which is the QUOTED-EXAMPLE parser artifact owned by `cqytxf`/`76w6mq`. So the exception set is 8 real plus 1 artifact that another plan is removing, and this plan must not count that one as a permanent exception.
  THE SEMANTIC CONTRACT THIS MUST NOT BREAK IS MEASURABLE AND WAS TESTED. `find` returns matching ARTIFACTS, never references. Measured: `find .aw/records -iname '*wtiso*'` returns TWELVE files including the DIFFERENT Set `wtisoland`, a `wtisodebt` item, and unrelated docs, while `aw find plans wtiso` correctly returns THREE. That is the exact argument against a naive `find | grep` and is the property a filename tier most endangers.
  THE CORRECTION THIS PLAN MUST INHERIT, AND IT DECIDES THE DESIGN. The item records, and `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` proves, that a stem or substring query CANNOT be made read-free while `_PRECEDENCE` (`selectors.py:71`) stays frozen: `stem` and `substring` sit LAST, so the resolver must first establish that `setid` and `status` did not match, and both live in front matter. A token really can be both a Set id and a filename fragment. So a two-tier design has exactly two honest shapes, and the item says so: either precedence CHANGES (a matching-behavior change needing sign-off) or tier 1 is a CANDIDATE FILTER whose winner is still decided by the frozen order. This plan takes the filter shape, because changing precedence would silently change which record wins for existing queries.
- Scope: Add a filename-first CANDIDATE FILTER that reduces how many files the resolver must open, without changing `_PRECEDENCE`, without changing which record wins any query, and without weakening the artifacts-not-references contract. The mandatory content fallback stays, and status queries continue to read front matter. EXCLUDES the non-conforming-filename report (Order 02), any precedence change, and any change to `aw search`.
- Scope-Paths: agent_workflows/selectors.py, tests/test_selector_zero_open.py, tests/test_cli_find.py
- Item-Dependencies: none
- Status: to-review
- Set: findtier
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 826o13
- From-Backlog: f8m2z2

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `f8m2z2` as Order 01 of a two-child Set. EVERY MEASUREMENT RE-VERIFIED AT HEAD rather than trusted, and three numbers moved. (1) The timing gap WIDENED: 6ms filename listing versus 429ms `aw find`, against the item's 20ms/357ms, because the corpus grew to 582 indexed plans. (2) The status-query trap re-measured: `-iname '*approved*'` returns 5 files, NONE approved, while 17 pending plans genuinely are; the item recorded 3 and 16. (3) The absent-from-filename set is NINE, not the item's 8, and the ninth is NOT a legacy name: it is `uyeko5` "declared" by research prompt `27rjro`, the quoted-example parser artifact owned by `cqytxf`/`76w6mq`, so it must not be counted as a permanent exception. THE ARTIFACTS-NOT-REFERENCES CONTRACT WAS TESTED, not assumed: `-iname '*wtiso*'` returns 12 files including the different Set `wtisoland`, while `aw find plans wtiso` returns 3. THE DESIGN IS CONSTRAINED BY THE ITEM'S OWN INHERITED CORRECTION: `PrecedenceForcesFrontMatterReadsTests` proves a stem or substring query cannot be read-free while `_PRECEDENCE` is frozen, so tier 1 is authored as a CANDIDATE FILTER rather than a precedence change. NOTED OVERLAP the executor must handle: three pending plans (`76w6mq`, `xo3244`, `paw8so`) already edit `selectors.py`, and `76w6mq`/`xo3244` both touch the same three readers; whichever lands last must re-read the others.

## Goal

Make the common lookup stop opening hundreds of files, without changing which record any query returns.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the contract before optimizing

- [ ] E-01 PIN THE ARTIFACTS-NOT-REFERENCES CONTRACT AS TESTS BEFORE TOUCHING THE RESOLVER, because it is the property a filename tier most endangers and the item elevates it to a contract.
  THE MEASURED CASES TO PIN: `aw find plans wtiso` must return the three `wtiso` Set plans and must NOT return `wtisoland` or `wtisodebt`; `aw find plans <id6>` must return only the artifact that IS that id6, never one that merely mentions it. The item's example is that `y6mfgo` resolves to one record while six plans mention it.
  PIN THE PER-KIND SEMANTICS TOO, since the filter must not blur them: `setid` is deliberately MULTI-target, `id6`/`path`/`stem` are UNIQUE_KINDS whose multi-match is a data bug, and `substring` is the explicit last resort. Those are documented at `selectors.py:52-58` and are what "the winner is still decided by the frozen order" means concretely.
  RUN THESE AGAINST HEAD FIRST and confirm they pass, so any later failure is attributable to this plan.
  - Depends on: none
  - Expected outcome: tests pinning the artifacts-not-references contract and the per-kind semantics, all green at HEAD before any change.
  - Execution state: pending

- [ ] E-02 MEASURE THE ACTUAL COST STRUCTURE BEFORE CHOOSING WHAT TO FILTER, because the item's own history shows the obvious optimization was displaced once already.
  MEASURE, DO NOT ASSUME: how many files `aw find plans <id6>` OPENS today, and how many it STATS. The item's predecessor `e32j35` recorded 938 opens across 469 distinct files end to end, and noted that the DISPLAY layer is a second, larger reader than the resolver. Re-measure both halves separately, because filtering the resolver while the display layer still scans every plan would produce no user-visible gain and would be a wasted change.
  NOTE THE DISPLAY LAYER MAY BE THE REAL COST AND IS NOT IN THIS PLAN'S SCOPE. `cli._find_type_records` calls `plans_index.scan_plans` for plans, which reads files independently of the resolver. If the measurement shows the display layer dominates, SAY SO and record it as a finding: this plan's value would then be smaller than the item implies, and that is a fact the maintainer should have.
  STATE THE BASELINE YOU WILL BE JUDGED AGAINST: wall-clock for an id6 query, a setid query, a status query, and a substring query, each before any change.
  - Depends on: E-01
  - Expected outcome: measured open/stat counts and per-query-kind timings for the resolver AND the display layer, with an explicit finding if the display layer dominates.
  - Execution state: pending

### Task group 2: add the filter without changing semantics

- [ ] E-03 ADD TIER 1 AS A CANDIDATE FILTER, NOT AS A NEW PRECEDENCE RULE. This is the item's inherited correction and the single most important constraint in the plan.
  THE SHAPE: for the kinds a filename CAN bound (`id6`, `stem`, `substring`), narrow the candidate set by filename BEFORE any body read, then let the EXISTING `_PRECEDENCE` loop decide the winner over that narrowed set. Do not reorder `_PRECEDENCE` (`selectors.py:71`) and do not short-circuit it.
  WHY NOT A PRECEDENCE CHANGE: `PrecedenceForcesFrontMatterReadsTests` proves the resolver must establish that `setid` and `status` did not match before `stem`/`substring` can win, and a token can legitimately be both a Set id and a filename fragment. Reordering would change which record wins for existing queries, which is a matching-behavior change requiring sign-off. The filter shape gets most of the speed with none of that risk.
  THE FILTER MUST BE A SUPERSET, NEVER A SUBSET. A filename filter may only REMOVE files that cannot possibly match; if it can remove a file that WOULD have matched, the optimization is a correctness bug. The nine records whose declared identity is absent from their filename are exactly the counterexample: for an `id6` query, filename filtering would drop `lus9ou`'s legacy-named plan. So the filter must either be skipped for kinds where a body-only match is possible, or must union the filename candidates with a body-read pass over the exception set.
  STATUS QUERIES MUST BYPASS TIER 1 ENTIRELY, measured: `-iname '*approved*'` finds 5 files of which 0 are approved, against 17 real ones. There is no filename signal for status.
  - Depends on: E-02
  - Expected outcome: a filename candidate filter that provably only removes non-matches, `_PRECEDENCE` unchanged, status queries bypassing it, and the nine absent-from-filename records still resolvable.
  - Execution state: pending

- [ ] E-04 NORMALIZE QUOTING WHEN COMPARING, which the item calls out as a measured false-positive source rather than a theoretical one.
  THE MEASURED CASE: one apparent ninth miss in the item's audit was a false positive because front matter read `` set: `awoptimize` `` WITH BACKTICKS. Compare stripped values, or the tool reports phantom drift.
  THIS MATTERS MORE FOR ORDER 02 THAN HERE, but the normalization belongs wherever the comparison lives, so implement it once in the shared reader rather than twice.
  - Depends on: E-03
  - Expected outcome: quoting normalized at the comparison site, with a test covering a backtick-quoted front-matter value.
  - Execution state: pending

### Task group 3: prove the speed AND the semantics

- [ ] E-05 PROVE NO QUERY CHANGED ITS ANSWER, which is the acceptance bar this plan must clear before any timing claim matters.
  RUN A DIFFERENTIAL OVER THE WHOLE CORPUS: for every tracked record's id6, every setid, and a sample of stems and substrings, compare the resolved path set BEFORE and AFTER. It must be IDENTICAL. This is mechanical and is the only way to prove a resolver optimization is safe; a handful of hand-picked cases is not sufficient for a change to a matching engine.
  INCLUDE THE NINE ABSENT-FROM-FILENAME RECORDS EXPLICITLY in that differential, and name them in the evidence: `4o5lt9`, `wvlk84`, `lus9ou`, `8q6yr9`, `7qx7ys`, `4w7d6s`, `25kzda`, `5tapom`, plus the `uyeko5`/`27rjro` artifact. They are the cases a filename filter breaks first.
  ALSO ASSERT THE E-01 CONTRACT TESTS STILL PASS, unchanged.
  - Depends on: E-04
  - Expected outcome: a corpus-wide differential showing identical resolution before and after, with the nine exception records named and passing, and the E-01 contract tests green.
  - Execution state: pending

- [ ] E-06 REPORT THE ACTUAL SPEEDUP HONESTLY, INCLUDING IF IT IS SMALL. The item's predecessor was displaced precisely because a speed argument did not survive contact with the maintainer's measurements.
  PASTE BEFORE AND AFTER TIMINGS for all four query kinds from E-02's baseline, plus the open/stat counts. If the display layer dominates (E-02's finding), state plainly that the user-visible improvement is smaller than the resolver improvement, and by how much.
  DO NOT CLAIM A TIER-1 SPEEDUP FOR A STATUS QUERY. Status bypasses tier 1 by construction (E-03), so its timing should be UNCHANGED, and reporting an improvement there would mean the bypass is not working.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline measured on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Inside a lane worktree roughly 32 further failures are environmental. Criterion: AFTER minus BEFORE is EMPTY.
  - Depends on: E-05
  - Expected outcome: honest before/after timings and open counts per query kind, an unchanged status-query timing, an explicit statement if the gain is small, and an empty bare-suite delta.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE TIMING GAP IS REAL AND WIDER THAN FILED: 6ms filename listing versus 429ms `aw find` at HEAD (item recorded 20ms/357ms), because the corpus grew to 582 indexed plans.
- THE FALLBACK IS MANDATORY FOR TWO MEASURED REASONS: status is not in filenames (5 filename hits, 0 approved, versus 17 real), and NINE records carry a declared identity absent from their filename, including `25kzda` which this repo cites constantly.
- THE NINTH IS AN ARTIFACT, NOT A LEGACY NAME: `uyeko5` "declared" by research prompt `27rjro` is the quoted-example parser bug owned by `cqytxf`/`76w6mq`. Do not count it as a permanent exception.
- `_PRECEDENCE` IS FROZEN AND THAT IS SEMANTICS, NOT LAZINESS: `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` proves a stem or substring query cannot be read-free because `setid`/`status` must be eliminated first, and a token can be both a Set id and a filename fragment.
- THE PER-KIND SEMANTICS ARE DOCUMENTED AT `selectors.py:52-58`: `setid` is deliberately multi-target; `path`/`id6`/`stem` are `UNIQUE_KINDS` whose multi-match is a data bug; `substring` is the explicit last resort.
- ARTIFACTS, NOT REFERENCES, IS A CONTRACT AND IS MEASURABLE: `-iname '*wtiso*'` returns 12 including the different Set `wtisoland`; `aw find plans wtiso` returns 3.
- `e32j35` ALREADY LANDED THE TEXT-FREE ENUMERATION this plan needs (`selectors._iter_paths`, `:397`) sharing ONE traversal with the header-reading view. Consume it.
- THE DISPLAY LAYER IS A SECOND, LARGER READER: `cli._find_type_records` calls `plans_index.scan_plans` independently of the resolver. `e32j35` measured 938 opens across 469 files end to end.
- QUOTING MUST BE NORMALIZED: a backtick-quoted `` set: `awoptimize` `` produced a phantom miss in the item's own audit.
- THREE PENDING PLANS EDIT `selectors.py` (`76w6mq`, `xo3244`, `paw8so`); `76w6mq` and `xo3244` touch the same three readers. Whichever lands last must re-read the others.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the gap is real and widened | 6ms for `find -iname '*lus9ou*'` versus 429ms for `aw find plans lus9ou`, against the item's 20ms/357ms; the corpus grew to 582 indexed plans. | timed at HEAD |
| F-2 | HIGH | status cannot come from filenames | `-iname '*approved*'` returns 5 files, NONE approved (two `apprvguard`, one `w6mqc0`, one literally named `auto-approved` whose status is `executed`); 17 pending plans genuinely are. | measured at HEAD |
| F-3 | HIGH | nine records' identity is absent from their filename | Eight legacy (`4o5lt9`, `wvlk84`, `lus9ou`, `8q6yr9`, `7qx7ys`, `4w7d6s`, `25kzda`, `5tapom`) plus one artifact. Filename-only matching would make `25kzda` uncitable. | scan of all tracked records at HEAD |
| F-4 | HIGH | the ninth is a parser artifact, not a legacy name | `uyeko5` is "declared" by research prompt `27rjro` via a quoted example; owned by `cqytxf`/`76w6mq`, so it is temporary and must not be counted as a permanent exception. | the `27rjro` document; `cqytxf` |
| F-5 | HIGH | precedence cannot be reordered without sign-off | `PrecedenceForcesFrontMatterReadsTests` proves `stem`/`substring` cannot be read-free while `setid`/`status` must be eliminated first; a token can be both. So tier 1 must be a FILTER. | `tests/test_selector_zero_open.py:184`; `selectors.py:71` |
| F-6 | HIGH | the artifacts-not-references contract is measurable | `-iname '*wtiso*'` returns 12 files including the different Set `wtisoland` and a `wtisodebt` item; `aw find plans wtiso` returns 3. | both run at HEAD |
| F-7 | MEDIUM | the filter must be a superset filter | It may only remove files that cannot match. For an `id6` query, naive filename filtering would drop `lus9ou`'s legacy-named plan, which is a correctness bug rather than an optimization. | F-3's exception set |
| F-8 | MEDIUM | the display layer may dominate the cost | `cli._find_type_records` uses `plans_index.scan_plans`, a reader independent of the resolver; `e32j35` measured 938 opens across 469 files end to end. Filtering only the resolver may yield little user-visible gain. | `e32j35`'s recorded measurement |
| F-9 | MEDIUM | the enumeration this needs already exists | `selectors._iter_paths` (`:397`) is text-free and shares one traversal with the header-reading view, landed by `e32j35`. | read at HEAD |
| F-10 | LOW | quoting caused a phantom miss once | A backtick-quoted `` set: `awoptimize` `` was a false positive in the item's audit. | the item's record |
| F-11 | LOW | three pending plans edit this file | `76w6mq`, `xo3244`, `paw8so` all declare `selectors.py`; two touch the same readers. | their `Scope-Paths` |

## Proposed changes (ordered, validatable)

1. Pin the artifacts-not-references contract and the per-kind semantics at HEAD (E-01).
2. Measure the real cost structure, resolver versus display layer, per query kind (E-02).
3. Add tier 1 as a superset-only candidate filter under the frozen precedence, with status bypassing it (E-03).
4. Normalize quoting at the comparison site (E-04).
5. Prove a corpus-wide differential of identical resolution, naming the nine exception records (E-05).
6. Report the speedup honestly, including if it is small (E-06).

## Deferred / out of scope (with reason)

- THE NON-CONFORMING-FILENAME REPORT. Order 02 (`3i6rso`) owns the item's second added requirement. Split because it is a reporting surface with its own test bed, and because it is what makes the exception set VISIBLE and shrinking, which is a different deliverable from making lookups faster.
- CHANGING `_PRECEDENCE`. Forbidden here: `PrecedenceForcesFrontMatterReadsTests` proves the order is semantics, and reordering would change which record wins existing queries, needing sign-off the item explicitly flags.
- THE DISPLAY LAYER (`cli._find_type_records` / `plans_index.scan_plans`). `e32j35` deferred it and it remains a separate reader; E-02 MEASURES whether it dominates and reports, but this plan does not change it. If it dominates, that is a finding for a follow-up rather than a scope expansion.
- `aw search`. A content search legitimately returns every mention; only `find` claims to return the artifact that IS the selector.
- THE INDEX-FIRST DESIGN. Displaced by the maintainer in `faf2e18b` and superseded (`e32j35`), and `ila6vl` is untracking the INDEX manifests, which removes the speed argument for them entirely. Do not reintroduce a manifest-freshness primitive.
- THE `uyeko5`/`27rjro` PARSER ARTIFACT. Owned by `cqytxf`/`76w6mq`. This plan must TOLERATE it in the exception set, not fix it, and must not count it as permanent.
- THE RESEARCH YAML DIALECT. `05aqbj`/`xo3244` own teaching the readers both front-matter dialects; this plan consumes whatever reader exists.

## Scope check

- Over-scope: none. One resolver filter, one normalization, two test modules.
- Scope-Paths justification: `agent_workflows/selectors.py` holds `_PRECEDENCE` (`:71`), the per-kind semantics comment (`:52-58`), `_iter_paths` (`:397`) and `resolve`, which is where the candidate filter and the quoting normalization belong (E-03, E-04); `tests/test_selector_zero_open.py` holds `PrecedenceForcesFrontMatterReadsTests`, the proof that constrains the design and that must stay green, plus the open-count assertions E-02 and E-06 extend; `tests/test_cli_find.py` is where the artifacts-not-references contract tests belong (E-01) since it exercises the verb an operator runs. `cli.py` and `plans_index.py` are deliberately NOT declared: the display layer is measured and reported, not changed.
- Under-scope, stated rather than left as `none`: this plan does not add the filename report, does not change precedence, does not touch the display layer, does not alter `aw search`, does not reintroduce an index-first design, does not fix the `27rjro` parser artifact, and does not teach the readers a second dialect. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- A CORPUS-WIDE RESOLUTION DIFFERENTIAL (E-05): for every tracked id6, every setid, and a sample of stems and substrings, the resolved path set must be IDENTICAL before and after. Hand-picked cases are NOT sufficient for a matching-engine change.
- THE NINE EXCEPTION RECORDS named individually and shown resolving: `4o5lt9`, `wvlk84`, `lus9ou`, `8q6yr9`, `7qx7ys`, `4w7d6s`, `25kzda`, `5tapom`, and the `uyeko5`/`27rjro` artifact.
- THE ARTIFACTS-NOT-REFERENCES CONTRACT: `aw find plans wtiso` returns the three `wtiso` plans and NOT `wtisoland` or `wtisodebt`, before and after.
- `PrecedenceForcesFrontMatterReadsTests` GREEN, with its own summary line, since it is the proof that constrains this design.
- BEFORE/AFTER TIMINGS AND OPEN COUNTS for an id6 query, a setid query, a status query and a substring query. The STATUS query's timing must be UNCHANGED, since it bypasses tier 1 by construction.
- AN EXPLICIT STATEMENT if the display layer dominates the end-to-end cost, with the measured split.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`selectors.py`'s PRECEDENCE COMMENT BLOCK (`:52-58`) is the authoritative prose on what each match kind means and must gain a statement that tier 1 is a CANDIDATE FILTER which never changes the winner, and WHY (citing the frozen-precedence proof). Without that, the next reader optimizing this path will reorder `_PRECEDENCE` and silently change which record wins.

The filter's superset-only property must be stated AT THE CODE as an invariant, not left implicit: it may only remove files that cannot match, and the nine absent-from-filename records are the standing counterexample. That sentence is what stops a future change from turning an optimization into a correctness bug.

`_iter_paths`'s docstring already records that the text-free and text-bearing walks stay identical by construction; extend it to note the filter consumes it, so the relationship is findable from either end.

No spec change is expected: `aw find`'s behavior is defined by its own help text and these comments rather than by a spec. If the executor finds spec text promising read-free lookups, that is a false claim to report rather than to edit.

## Open questions

### OQ-01: Should tier 1 be a candidate filter or a precedence change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A CANDIDATE FILTER, decided by the proof the item itself inherited. `PrecedenceForcesFrontMatterReadsTests` demonstrates that `stem` and `substring` cannot be answered without first eliminating `setid` and `status`, both of which live in front matter, because one token can legitimately be both a Set id and a filename fragment. Reordering `_PRECEDENCE` would therefore change which record wins for existing queries, which is a matching-behavior change the item explicitly says needs sign-off. The filter shape captures most of the speed (it reduces how many files are opened) while leaving the winner determined by the frozen order, so it needs no sign-off and cannot silently change an answer. The cost is that the theoretical "zero opens" target is unreachable, which the item already recorded as unreachable anyway.

### OQ-02: May the filter ever remove a file that would have matched?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NEVER; IT IS A SUPERSET-ONLY FILTER AND THIS IS A CORRECTNESS INVARIANT, not a quality goal. The nine records whose declared identity is absent from their filename are the standing counterexample: for an `id6` query, filtering by filename would drop `lus9ou`'s legacy-named plan and `25kzda`'s grandfathered spec, and the latter is cited constantly, so the tool would start failing on its most-referenced spec. E-03 therefore requires the filter either to be SKIPPED for kinds where a body-only match is possible, or to union filename candidates with a body pass over the exception set. E-05's corpus-wide differential is what proves the invariant held, and a hand-picked sample is explicitly insufficient.

### OQ-03: What if the display layer, not the resolver, dominates the cost?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DELIBERATELY OPEN, because it decides whether this plan is worth executing and only a measurement can answer it. `e32j35` recorded 938 opens across 469 distinct files END TO END, and noted that `cli._find_type_records` calls `plans_index.scan_plans` as a SECOND reader independent of the resolver. If that second reader dominates, then filtering the resolver improves an internal number while an operator still waits roughly as long, and the honest conclusion would be that the display layer is the real target and this plan should be re-scoped or deferred. E-02 measures both halves and E-06 requires the split to be stated plainly, including if the gain is small. It is non-blocking because the resolver improvement is real and safe regardless; it is the plan's VALUE, not its correctness, that hangs on the answer, and that is a judgement for the maintainer once the numbers exist.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL passing output of the contract tests at HEAD, before any change. Quote the `wtiso` assertion showing `wtisoland` and `wtisodebt` are EXCLUDED, and the id6 assertion showing a mentioning plan is excluded. Paste the per-kind semantics assertions (setid multi-target, id6 unique, substring last resort).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the measured open and stat counts for an id6 query, split between the RESOLVER and the DISPLAY layer, plus wall-clock timings for all four query kinds. State explicitly which half dominates. If the display layer dominates, paste that as a finding with the measured split, since OQ-03 turns on it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the filter implementation and quote the code showing `_PRECEDENCE` is NOT reordered (plus a diff proving it unchanged). Quote the superset-only invariant as written at the code. Paste proof that a STATUS query bypasses tier 1 (both the code path and an unchanged timing). Paste resolution of at least three of the nine exception records showing they still resolve.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the normalization code and the ACTUAL passing output of a test using a backtick-quoted front-matter value, showing no phantom miss.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the corpus-wide differential's summary: how many id6s, setids, stems and substrings were compared, and that the resolved path sets were IDENTICAL. Name the nine exception records individually with their before/after resolution. Paste `PrecedenceForcesFrontMatterReadsTests`'s own summary line, green. Any single difference is a FAILED validation, not a caveat.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste before/after timings and open counts for all four query kinds. Confirm the STATUS query timing is UNCHANGED and say so explicitly, since a change there means the bypass leaked. If the gain is small because the display layer dominates, state that plainly with the numbers rather than reporting the resolver improvement alone. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION, but OQ-03 may make it not worth executing, and that is deliberate: if E-02 shows the display layer dominates the end-to-end cost, the honest outcome is to report that and let the maintainer decide whether to proceed, re-scope, or defer. The resolver change is safe either way; its VALUE is what the measurement decides.

IT CARRIES NO `Blocks-Release`, because backlog `f8m2z2` carries none. It is `Work-Kind: feature` at `Priority: medium` and the maintainer did not gate it; stated so a reader does not assume a gate was dropped.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Do NOT reorder `_PRECEDENCE`. Do NOT let the filter remove a file that could match; the corpus-wide differential is the proof, and a hand-picked sample is not. RE-READ the other pending `selectors.py` edits before starting (`76w6mq`, `xo3244`, `paw8so`): if any has landed, this plan's changes must sit on top of them rather than reverting them. Re-locate every symbol by NAME rather than by the line numbers cited here. Paste ACTUAL timings and counts; never claim a speedup you did not measure. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the corpus-wide differential and the nine named exception records.
