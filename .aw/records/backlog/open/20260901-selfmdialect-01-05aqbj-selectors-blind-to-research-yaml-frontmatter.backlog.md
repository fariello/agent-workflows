- Id: 05aqbj
- Status: open
- Set: selfmdialect
- Priority: medium
- Work-Kind: bug
- Summary: aw find is blind to research YAML front matter: research id6/status/set resolve by FILENAME only, so a status query returns 5 files where the index holds 52

## Workflow history
- 2026-09-01 created (aw backlog): filed by IPD e32j35 E-06: the selector understands only the bullet front-matter dialect

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
