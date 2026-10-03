- Id: 7jl2bf
- Status: open
- Set: hostcite
- Priority: low
- Work-Kind: chore
- Summary: Decide whether aw check --source-anchors should resolve <file>.py:<line> offsets in tracked source, not only spec anchors

## Workflow history
- 2026-10-02 created (aw backlog): Filed while authoring plan fnbtta (backlog ma8aig), which carries gyam7x OQ-01 forward. The sample the question asked for is now measured and is recorded in fnbtta F-01/F-05/F-06.

THE QUESTION, carried from gyam7x OQ-01 through backlog ma8aig: should a mechanical check refuse a `<file>:<line>` citation that points past end of file in tracked source?

IT IS LARGELY ALREADY ANSWERED AND ALREADY BUILT, which is the finding that reframes this item. `aw check --source-anchors` exists and is backed by `spec_citations.stale_spec_anchors`; its `_resolve_offset` returns FOUR verdicts, `past_eof`, `in_fence`, `blank_line` and `valid`. So it implements BOTH the cheap half (an offset beyond the file's length is wrong) AND the half ma8aig calls 'not mechanically decidable at all' (a citation landing on a blank or meaningless line), the latter via its `blank_line` arm. The sibling `artifact_refs.check_source_citations` separately scans `.py` sources for dangling FILENAME citations and reports 0 at HEAD.

THE ACTUAL GAP IS SUBJECT, NOT MECHANISM. `stale_spec_anchors` resolves offsets into `.spec.md` files only, via `specs.discover_specs`, so a `<host>.py:<line>` offset in a Python comment is invisible to it, and `check_source_citations` checks that a cited FILE exists but never resolves the OFFSET. Nothing in the tree resolves a Python-source line offset. So the decision owed is whether to widen the existing checker's subject to tracked `.py` files, and under what severity.

THE SAMPLE ma8aig ASKED TO HAVE IN HAND BEFORE DECIDING, measured 2026-10-02 at HEAD 6e299712f while authoring plan fnbtta, by resolving every `<file>.py:<line>` citation under agent_workflows/, tools/ and tests/ against the file it names: 51 resolvable offsets across 19 files, of which 12 are defective. 5 are PAST EOF (3 in agy_runipd.py citing oc_runipd.py at 8766/8645/8834 against a 5487-line file; 2 in runner_shared.py citing 6993 and 6645). 7 land on blank or punctuation-only lines (check_engine.py and hooks/status_untooled_gate.py both citing status_set.py:504, a blank line; git_commit_helper.py citing cli.py:2696, a bare ')'; runner_shared.py citing oc_runipd.py:2979, a bare '),'; and three in tests/). Within runner_shared.py alone the figure is 15 offsets across 8 citing sites, EVERY ONE wrong, 6 past EOF.

WHAT THE SAMPLE SUGGESTS, stated as input to the decision rather than as the decision: a length check alone would have caught 5 of the 12, and the blank-line arm the existing checker ALREADY HAS would have caught 7 more, i.e. the combination catches all 12. That is a materially stronger case than ma8aig's own estimate, which assumed the expensive half needed new work.

WHAT THIS ITEM MUST DECIDE, and why it is not just a code change: (1) the SEVERITY, where the spec-anchor precedent is `info`/advisory (`check.spec-anchor-stale`) and the citation-form precedent IPD-C801 is advisory-and-date-gated precisely because any check over prose false-positives, and spec ipd-structure-and-linting Section 10.2 warns that 'a gate that false-positives trains authors to bypass it'; (2) whether a HISTORICAL citation is exempt, which matters because a legitimate comment may cite a construct as it stood at a named commit, where no current offset can be correct and a past-EOF verdict would be a false positive; (3) whether the rule reports at all on an offset the repository's own policy says should not be there, since Section 10.2 form (c) permits a trailing offset appended to a symbol; (4) whether a CUTOVER date gates it, as IPD-C801's does, so it reports on code being edited rather than on a corpus nobody is touching.

RELATED, same defect class, each with its own carrier: plan fnbtta fixes the 8 sites in runner_shared.py only (comments, no behavior). 3tov52 owns deleted-TEST citations in runner_shared.py and agy_runipd.py. rdl9lh (bug, Blocks-Release: next) owns a docstring citing a guard test deleted in 19313eed and records this as 'a KNOWN CLASS rather than an isolated instance'. nzqj6m owns a dangling-citation sweep in the uonrjg criteria. A widened checker is the only one of these that would prevent recurrence rather than fix an instance.
