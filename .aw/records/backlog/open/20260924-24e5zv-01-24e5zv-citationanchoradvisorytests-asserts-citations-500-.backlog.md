- Id: 24e5zv
- Status: open
- Blocks-Release: next
- Set: 24e5zv
- Priority: medium
- Work-Kind: bug
- Summary: CitationAnchorAdvisoryTests asserts citations > 500 across pending plans, failing as pending corpus shrinks

## Workflow history
- 2026-09-24 created (aw backlog): CitationAnchorAdvisoryTests asserts citations > 500 across pending plans, failing as pending corpus shrinks

tests/test_ipd_lint.py CitationAnchorAdvisoryTests.test_the_detector_discriminates_on_the_real_corpus_with_the_gate_disabled asserts citations > 500 across SOURCE_PLANS pending/*.ipd.md. As plans transition to executed, the pending count dropped to 449, failing the test suite.
