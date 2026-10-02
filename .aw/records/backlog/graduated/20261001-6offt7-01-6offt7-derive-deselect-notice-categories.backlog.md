- Id: 6offt7
- Status: graduated
- Graduated-To: 6offt7
- Set: 6offt7
- Priority: low
- Work-Kind: chore
- Summary: Derive deselected category names in tests/deselect_notice.py instead of hardcoding

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: qsz23k
- 2026-10-01 created (aw backlog): Derive deselected category names in tests/deselect_notice.py instead of hardcoding

tests/deselect_notice.py hardcodes the deselected category names in its runtime notice (the default run skips 'slow' and 'livecorpus'). That string is correct today, so this is not a live staleness bug, but a duplicated-source concern: the notice restates the category list rather than deriving it from pyproject addopts. When a third category is added, the notice silently under-reports. This notice is credited as the runtime mitigation for stale instructions, but tests/test_suite_instruction_marker_parity.py does not cover it (it verifies engine instruction prose). Filed per IPD zb81ah E-06.
