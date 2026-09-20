- Id: 5u7mug
- Status: open
- Blocks-Release: next
- Set: 5u7mug
- Priority: high
- Work-Kind: bug
- Summary: aw set accepts done/open/parked for research and refuses the real todo/reference/archive vocabulary

## Workflow history
- 2026-09-20 created (aw backlog): aw set accepts done/open/parked for research and refuses the real todo/reference/archive vocabulary

MEASURED 2026-09-20 while executing plan `9zvl2w` (which touched the same function for an unrelated reason).

`status_set.TYPE_STATUSES["research"]` is `{'active', 'done', 'open', 'parked'}`, but the OWNING contract `research_contract.STATUSES` is `{'active', 'archive', 'reference', 'todo'}`. Only `active` is in both. So the setter:

1. REFUSES every real research status but one. Measured:

       $ aw set reference cnkyvn --dry-run
       FAIL  Validation error ...: Status 'reference' is not valid for research
             (valid: ['active', 'done', 'open', 'parked']). Refusing before making changes.

2. ACCEPTS three words that are NOT research statuses and writes them into the front matter. Measured:

       $ aw set done cnkyvn --dry-run
       -    research    20260726-awdeliv-00-cnkyvn  draft -> done  (dry-run)

USER-PERCEPTIBLE: a maintainer cannot promote a research doc to `reference` or `archive` through `aw set` at all, and can silently write an invalid status that `aw check` and the research readers will not recognize. That is a wrong answer, not an inefficiency, hence `bug`.

FIX SHAPE: derive the research row from `research_contract.STATUSES` (+ `STATUS_NORMALIZATIONS`) the way the `backlog` row already derives from `backlog.STATUSES` (`status_set.py:79`, 'identical by construction (GUIDING_PRINCIPLES P8)'). Decide explicitly whether the three non-vocabulary words stay as accepted ALIASES (`done`->`reference`? `parked`->`archive`? `open`->`todo`?) or are dropped; do not guess, because any existing doc already carrying one needs a migration answer.

NOT FIXED IN `9zvl2w`: that plan's scope is lifecycle PRESENTATION (spec `uonrjg`), and this is a transition-validation vocabulary defect with a migration question attached.
