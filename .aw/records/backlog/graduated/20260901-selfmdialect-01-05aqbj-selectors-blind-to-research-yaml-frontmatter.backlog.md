- Id: 05aqbj
- Status: graduated
- Blocks-Release: next
- Set: selfmdialect
- Priority: medium
- Work-Kind: bug
- Summary: aw find is blind to research YAML front matter: research id6/status/set resolve by FILENAME only, so a status query returns 5 files where the index holds 52

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan xo3244 (Set selfmdialect, .aw/records/plans/pending/20260908-selfmdialect-01-xo3244-...ipd.md), which carries From-Backlog: 05aqbj and inherits this item's Blocks-Release: next. Status graduated (design handed off), NOT done: no code is written yet. THE PLAN TAKES OPTION 1 (teach the resolver both dialects), which this item itself calls the recommended shape, and treats the 5 -> 52 result shift as an ACCEPTED contract change carried to the maintainer as a non-blocking open question rather than as a side effect. Options 2 and 3 are recorded as deliberately rejected. NOTHING IN THIS ITEM IS OBSOLETE. Re-verified at HEAD 44d4950d: aw find research reference still returns 5 records, while parsing front matter over the same tree gives reference 52 / archive 31 / todo 21 / active 1 across 105 YAML-parsable docs of 113 .md files, and research/INDEX.json independently holds 105 entries with the same distribution. The resolver still reads only the bullet dialect (selectors._read_id :246-248, _read_status :251-253, _read_setid :305-310), the module docstring still argues at length for the exclusion (:11-31), and tests/test_selector_zero_open.py:371-416 still pins today's filename-only behavior. TWO NEW MEASUREMENTS THAT MATERIALLY DE-RISK THE WORK. FIRST, the blast radius outside research is provably ZERO: enumerating every candidate the resolver walks per type and counting headers that open a --- fence gives plans 0/527, specs 0/28, backlog 0/158, releases 0/1, reviews 0/69, prompts 0/16, walkthroughs 0/17, research 105/107. No non-research record can take the new branch, so this cannot perturb aw find plans or any MUTATING verb's selector resolution, which was the main risk. SECOND, this item's instruction to NORMALIZE QUOTING (a set: value reading backtick-awoptimize-backtick) does NOT reproduce anywhere in the current corpus: checking every parsed front-matter value for backticks and stray quotes across all 105 docs found ZERO anomalies. The plan still implements the strip (the observation was real and it is nearly free) but labels it a defensive GUARD rather than a fix for a live defect, and says so explicitly, so nobody later reports it as unreproducible. Also confirmed sufficient and unchanged: the bounded 4096-byte header read covers every research front-matter block (0 docs parse from full text but fail from the header), which matters because parse_frontmatter returns None on a missing closing fence and a straddling block would read as no-metadata. Note 8 of 113 research .md files have no front matter at all (READMEs, INDEX.md, a template, prototype READMEs) and must keep resolving by filename.
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

FILED BY IPD `e32j35` E-06, which was narrowed to documentation precisely because closing this gap
CHANGES RESULTS and is therefore a semantic decision the maintainer should make, not a side effect of
a performance change.

THE GAP. `selectors.py` is the ONE selector-to-file resolver for every verb, and it understands only
the BULLET front-matter dialect (`- Id:`, `- Status:`, `- Set:`) used by plans, specs, backlog and the
rest. Research docs use YAML front matter instead (`id:`, `status:`, `set:` between `---` fences,
parsed by `research_contract.parse_frontmatter` via `research_index._scan_docs`). So for research the
three content-derived rules MATCH_ID6 / MATCH_SETID / MATCH_STATUS never fire at all.

MEASURED 2026-09-01 on this repo (103 research docs scanned by the selector):

- `0` of 103 research files carry a `- Id:` bullet; `101` carry a YAML `id:`.
- `aw find research <id6>` therefore does NOT resolve via MATCH_ID6. It succeeds only because the
  id6 also appears in the FILENAME, i.e. it lands on MATCH_SUBSTRING, the explicit last-resort rule.
- `aw find research reference` returns `5` files, matched by FILENAME. `research/INDEX.json` holds
  `52` entries with `status: reference`. So the status selector is not merely slow for research, it
  is answering a different question than a reader would expect.

WHY THIS IS A BUG AND NOT A CURIOSITY. Two records with identical metadata resolve differently based
only on which dialect their type happens to use, and the failure is SILENT: a research status query
returns a plausible-looking short list rather than an error, so nothing signals that the metadata was
never consulted. A user cannot tell a genuine 5-file answer from a 52-file answer that was missed.

WHAT A FIX MUST DECIDE, since each option changes user-visible behavior:

1. TEACH THE RESOLVER BOTH DIALECTS (recommended shape): have the header reader try the bullet
   pattern and then the YAML block, so research metadata becomes matchable. CONSEQUENCE, and it must
   be accepted deliberately: `aw find research reference` goes from 5 results to 52. That is more
   CORRECT but it is a contract change, so it needs a changelog note and probably a maintainer call.
2. LEAVE RESEARCH FILENAME-ONLY and say so in `aw find --help`, so the limitation is at least honest
   rather than invisible. Cheapest, but keeps a real inconsistency between types.
3. ROUTE RESEARCH THROUGH ITS OWN INDEX for these rules. Rejected during e32j35's review: it produces
   the same 5 -> 52 shift as option 1 while ALSO coupling `find` to manifest freshness, and drift is
   routine here.

IMPLEMENTATION NOTES already established, so a later pass need not rediscover them:

- Reuse `research_contract.parse_frontmatter`; do not write a second YAML reader, or the two will
  drift about what counts as valid front matter.
- NORMALIZE QUOTING before comparing. Verified during e32j35's maintainer session that a research
  `set:` value can read `` `awoptimize` `` with backticks, which produces a phantom mismatch if
  compared raw.
- The bounded 4KB header read (`selectors._HEADER_BYTES`) is sufficient for a YAML front-matter block
  too, so this needs no change to the read strategy.
- Any change here must keep the PRECEDENCE contract (path -> id6 -> setid -> status -> stem ->
  substring) intact, and must preserve the rule that `find` returns matching ARTIFACTS, never
  artifacts that merely MENTION the token.

RELATED. `e32j35` (findidx) is the plan that found and documented this while deliberately not fixing
it; its `selectors.py` module docstring carries the reason inline, and
`tests/test_selector_zero_open.py::ResearchStaysFilesystemResolvedTests` pins today's behavior so a
future change to it is a deliberate, visible act rather than an accident.
