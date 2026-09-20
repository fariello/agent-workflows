- Id: qbfor9
- Status: open
- Blocks-Release: next
- Set: qbfor9
- Priority: medium
- Work-Kind: bug
- Summary: aw attention --runs Run column hardcodes six lifecycle colors that contradict spec uonrjg Section 5, and two of its run states have no semantic stage at all

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing plan f9t5hz (lifeglyph-05).

FOUND WHILE EXECUTING PLAN `f9t5hz` (`lifeglyph-05`), which converted `attention.py`'s
ARTIFACT lifecycle rendering to the shared resolver. The `--runs` Run column is a SECOND,
independent lifecycle presentation in the same file that no plan in the `lifeglyph` Set
declares, so it survives the conversion and leaves criterion A17 ("No second lifecycle color
or glyph table remains") unsatisfiable for this module.

WHERE: `agent_workflows/attention.py`, two sites, both inside the `runs_mode` branches:
`_render_item_row` (the `run_code = {...}` dict) and `_render_table_row` (the `run_raw ==`
if/elif ladder). Both paint a RUNNER ITEM STATE, which spec `uonrjg` Section 7.2 covers and
`lifecycle_style.FAMILY_RUNNER_ITEM` already maps.

MEASURED 2026-09-20 by resolving each hardcoded value against the shared table. Five of the
six CONTRADICT the spec:

    running   hardcoded  51   spec stage active   ->  220   CONTRADICTS
    queued    hardcoded 220   spec stage ready    ->   45   CONTRADICTS
    merging   hardcoded 201   spec stage unknown  ->  244   CONTRADICTS
    done      hardcoded  40   spec stage unknown  ->  244   CONTRADICTS
    blocked   hardcoded 214   spec stage blocked  ->  208   CONTRADICTS
    failed    hardcoded 196   spec stage failed   ->  196   SAME

TWO OF THOSE ARE A DEEPER PROBLEM THAN A WRONG NUMBER. `merging` and `done` are NOT members
of `lifecycle_style`'s runner-item vocabulary at all, so they resolve to the `unknown` stage
(`?`, gray 244) rather than to a stage of their own. They are produced by
`attention.get_active_runs_map`, which maps driver states onto its own six-word vocabulary
(`running`/`queued`/`merging`/`done`/`failed`/`blocked`). So a naive conversion here would
REGRESS the display, printing `?` where an operator reads `merging` today. Compare
`integrating` (the spec's own word for merge/rebase work, `⇄`, 220) and `complete`/`verified`
(its words for done): the likely fix is that `get_active_runs_map` should emit the spec's
vocabulary, or that a small translation table should sit at the boundary. That is a decision,
not a mechanical substitution, which is why this is filed rather than fixed in passing.

NOTE `queued` IS ALREADY WRONG IN A WAY A USER CAN SEE, independent of the conversion: 220 is
this spec's AMBER for the five ACTIVE subtypes, so a queued (not yet started) item currently
renders in the color reserved for work in progress, while the spec assigns it `ready` (45,
cyan). Section 5's stated purpose is precisely to stop readiness and activity collapsing into
one color.

WHY IT IS NOT IN `f9t5hz`'s SCOPE: that plan's `- Scope:` is the ARTIFACT status path (the
local `_STATUS_COLOR_256` table and its three lifecycle sites). Converting the Run column
would have meant either changing `get_active_runs_map`'s vocabulary or adding a translation
layer, both outside the declared scope and both requiring the vocabulary decision above.
Checked at execution: `grep` across all eight `lifeglyph` children shows NONE declares this
surface. Sibling `qdd5jq` owns the RUNNERS' own displays and its scope fence explicitly says
"do NOT edit `attention.py`, whose table is `f9t5hz`'s", so the Run column falls between the
two children rather than inside either.
