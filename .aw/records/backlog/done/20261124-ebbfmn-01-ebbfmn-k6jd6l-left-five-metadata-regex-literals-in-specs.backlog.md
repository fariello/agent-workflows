- Id: ebbfmn
- Status: done
- Set: ebbfmn
- Work-Kind: followup
- Priority: medium
- Summary: k6jd6l left five ^- metadata regex literals in specs.py and backlog.py; Order 249 n2cvf0 expected none and only records them as delete (follow-on), with no plan to edit them (found by 786w7r)
- Short-Description: k6jd6l left five ^- metadata regex literals in specs.py and backlog.py; Order 249 n2cvf0 expected none and only records them as delete (follow-on), with no plan to edit them (found by 786w7r)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-25 done (aw backlog): closed by aw agy run: IPD fkvrc7 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261124-metastore-303-fkvrc7-replace-surviving-specs-and-backlog-front-matter-regexes-via.ipd.md); evidence .aw/records/plans/executed/20261124-metastore-303-fkvrc7-replace-surviving-specs-and-backlog-front-matter-regexes-via.ipd.md
- 2026-11-25 graduated (aw set): Carried by metastore Order 303 (fkvrc7) ahead of 9o83cr
- 2026-11-24 created (aw backlog): k6jd6l left five ^- metadata regex literals in specs.py and backlog.py; Order 249 n2cvf0 expected none and only records them as delete (follow-on), with no plan to edit them (found by 786w7r)

Measured 2026-11-24 at 56e9d649f by 786w7r with the LIT search: specs._SPEC_ID_RE, specs._TOP_KEY_RE, the '^- Status:' re.match in specs.run_migrate, specs._SPEC_ID_BULLET_RE, backlog._TOP_KEY_RE. selectors.py has none. _TOP_KEY_RE drives the duplicate-bullet rules (IPD 1znlxy, 7ohskw), so it reads front-matter metadata. 0xsx2n (Order 46) is the finishing item and has no edit item for these. Fix: give them an owning child plan before 9o83cr E-14.
