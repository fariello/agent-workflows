- Id: ap839o
- Status: done
- Graduated-To: secbound
- Set: secbound
- Priority: low
- Work-Kind: chore
- Summary: No author-time guard refuses a new marker-located unbounded section slice in tests, so the bounded extractor can be bypassed silently

## Workflow history
- 2026-10-09 done (aw backlog): closed by aw agy run: IPD jj5ju1 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-secbound-03-jj5ju1-refuse-a-new-marker-located-unbounded-section-slice-in-tests.ipd.md); evidence .aw/records/plans/executed/20261001-secbound-03-jj5ju1-refuse-a-new-marker-located-unbounded-section-slice-in-tests.ipd.md
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: jj5ju1
- 2026-09-29 created (aw backlog): Deferred residue of Set secbound (plans 78rxzc, tr8ugt), which graduated backlog 1pgrii. Order 01 adds support.section/final_section/section_lines to tests/support.py and Order 02 converts the 12 measured sites, but NOTHING refuses a NEW unbounded marker-located slice, so the class can return exactly as 1pgrii's own history records it returning after skn8uk bounded the originating guard. Deferred rather than built for two stated reasons: the detector needs a design neither plan did (x[start:] is indistinguishable from a legitimate tail slice without knowing start came from a marker search, and an authoring AST census found the shape reachable but not trivially so), and it is the same shape as structpin Order 02 (76ic0k), whose AST guard over tests/ should land first so the two do not collide. Filed chore rather than bug: it is a missing preventative, not a user-perceptible defect.

## Why this is filed separately

Set `secbound` fixes the measured instances of this defect class. It does not stop a new one.

The class: a test locates a section by a marker and then takes everything after it, so it asserts
over text it was never written to judge. Measured at authoring HEAD `20d389df`, an AST census of
`tests/` found 44 marker-located section extractions, of which 8 take an unbounded tail and 12 take
a `split(MARKER)[0]` head whose fallback is the whole text. Two were provably wrong against real
producers (`tests/test_backlog.py` counted 4 history bullets where it asserts 2 when an item carries
a `## Suggested work` body; `tests/test_research_index.py` counts 3 where it asserts 2 the moment a
section is appended after `## Most recent`).

## Suggested work

- Add an author-time guard that refuses a NEW marker-located unbounded slice under `tests/`,
  modelled on `tests/test_carrier_scan_single_item_contract.py`, which is this repository's
  established shape for an AST guard shipped as a test (NamedTuple violation record, module
  docstring stating SCOPE and KNOWN HOLE, positive and negative fixtures over source strings).
- Sequence it AFTER `structpin` Order 02 (`76ic0k`), which adds an AST guard over `tests/` for
  production-source reads. Two guards walking `tests/` should share a shape rather than race.
- Sequence it AFTER `secbound` Order 02 (`tr8ugt`), or the guard is red on arrival against the
  sites that plan converts.

## The design problem to solve first

`x[start:]` is not by itself a defect: a legitimate tail slice looks identical. What makes it one is
that `start` came from a marker search (`.find`, `.index`, an `enumerate`/`startswith` walk) and no
upper bound was established. Detecting that needs the binding tracked from the search to the
subscript, which the authoring census did within a single function but not across functions. State
the bound in the guard's docstring rather than overclaiming, exactly as
`tests/test_carrier_scan_single_item_contract.py` records its own KNOWN HOLE.

## Sites that must NOT be flagged

- `tests/test_defect_report.py`'s `prompt[start:]` compares the tail EQUAL to
  `reporting_contract.contract_text()` to prove nothing follows the contract. The unboundedness IS
  the assertion. Plan `tr8ugt` E-07 leaves a comment at the site saying so.
- The 9 `split(SEP)` sites whose separator is a field delimiter (`":"`, `"."`, `"="`, `"---"`).
  Those are field parses whose failure mode is an immediate `IndexError`, not a widened assertion.
