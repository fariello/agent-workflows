- Id: 24e5zv
- Status: done
- Set: 24e5zv
- Priority: medium
- Work-Kind: bug
- Summary: CitationAnchorAdvisoryTests asserts citations > 500 across pending plans, failing as pending corpus shrinks

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by b165ba2d: floor lowered to 100 (tests/test_ipd_lint.py)
- 2026-09-24 created (aw backlog): CitationAnchorAdvisoryTests asserts citations > 500 across pending plans, failing as pending corpus shrinks

tests/test_ipd_lint.py CitationAnchorAdvisoryTests.test_the_detector_discriminates_on_the_real_corpus_with_the_gate_disabled asserts citations > 500 across SOURCE_PLANS pending/*.ipd.md. As plans transition to executed, the pending count dropped to 449, failing the test suite.
