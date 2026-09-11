- Id: lmjc8h
- Status: open
- Blocks-Release: next
- Set: retiredsplit
- Priority: medium
- Work-Kind: bug
- Summary: check_collisions include_retired disagreement: aw doctor and aw check report different populations from one predicate

## Workflow history
- 2026-09-11 open (aw set): Gated per the maintainer's rule of 2026-09-11 that every bug blocks the next release. Filed ungated earlier the same session.
- 2026-09-11 created (aw backlog): Filed 2026-09-10 from an /askme round, on the maintainer's ruling that no defect may be raised without a carrier. THE DEFECT: one predicate reports two different populations to two surfaces because its callers disagree on a default. doctor.py:530 hardcodes include_retired=True while check_engine.py:1760 passes a flag defaulting to False, so aw check all and aw doctor answer the same question differently. MEASURED at HEAD 2cdc5fe5: check.setid-collision yields 38 findings on the default scope and 86 with --all, and plan drzbs9's review measured the same split as 40 vs 86 across 30 vs 65 setids a day earlier. The agentadhere collision that motivated the whole setid effort is INVISIBLE in the False branch despite 7 executed plans owning it. WHY IT OUTLIVES ITS ORIGIN: this was recorded in retired plan drzbs9's OQ-04 as supporting measurement, and drzbs9 has since been superseded by the setid-direction reversal, so the observation would have died with it. The disagreement is independent of that reversal and independent of whether the collision rule is re-scoped. Scope: settle which population each surface should report and make the two callers agree, or make the parameter explicit at both call sites so the divergence cannot be accidental.
