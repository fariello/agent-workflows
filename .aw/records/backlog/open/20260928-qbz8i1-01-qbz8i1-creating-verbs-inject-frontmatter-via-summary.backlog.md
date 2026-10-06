- Id: qbz8i1
- Status: open
- Graduated-To: qbz8i1
- Blocks-Release: next
- Set: qbz8i1
- Priority: medium
- Work-Kind: bug
- Summary: aw specs new and aw releases new write an unvalidated --summary into front matter, so a newline in it injects real metadata (a smuggled - Blocks-Release: next parses as the record gate) and both checkers report clean

## Workflow history
- 2026-10-06 open (aw set): xhr0dj returned to authoring: uncovered obligation: The Set-level gate an executor must apply after the last child; re-run graduation to complete the handoff
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: ribg85, uz05bl, xhr0dj, ynhst5
- 2026-09-28 created (aw backlog): aw specs new and aw releases new write an unvalidated --summary into front matter, so a newline in it injects real metadata (a smuggled - Blocks-Release: next parses as the record gate) and both checkers report clean

FILED AS THE CARRIER for the two out-of-scope rows in plan `dtg7dz` (a0s33b-01), which fixes the SAME defect class in the `backlog` tree only and measured these sibling trees while authoring.

MEASURED 2026-09-28 in a lane at HEAD `a019e547`, against temporary fixture repositories.

`aw specs new --summary $'legit\n- Blocks-Release: next'` exits **0** and writes a spec whose front matter contains a real `- Blocks-Release: next` bullet the author never requested. `aw specs check --agent` on that fixture then reports `"outcome":"clean","findings":0`, so nothing catches it. The same input shaped as `$'legit\n- Status: approved'` writes a SECOND `- Status:` bullet into the metadata block; `specs._read_status` returns `draft` because `_find_status_index` keeps the FIRST match, so this particular injection does not currently forge an approval, but it does leave a spec carrying two contradictory status bullets that every later reader and rewriter sees.

`aw releases new --summary $'legit\n- Blocks-Release: next'` exits **0** and writes the same smuggled bullet into a release record's front matter.

WHY NEITHER CHECKER SEES IT: the value is SPLIT before validation. The parser reads `- Summary: legit` (a safe, bounded, control-char-free line) and the smuggled bullet as separate lines, so `attention_contract.is_safe_descriptive` is handed only the safe half. This is the same mechanism measured on the backlog tree in `dtg7dz` finding F-04, and it is why the fix must live at the WRITE PATH: no post-hoc checker can recover the injected newline.

SPECS IS THE WEAKER OF THE TWO, because it has no summary rule at all. `grep -n "summary-unsafe" agent_workflows/*.py` matches only `backlog.py` and `doctor.py`, so a spec `- Scope:`/summary value is unbounded at BOTH the write path and the checker, where backlog at least catches the over-length shape after the fact (`backlog.summary-unsafe`). Closing the specs half therefore needs a new checker rule as well as a write-path guard, which is new policy and is why `dtg7dz` declined to fold it in.

THE ESTABLISHED FIX SHAPE ALREADY EXISTS IN THE SAME MODULE: `specs.run_set` refuses with `aw specs set: --gate-summary must be a bounded single control-char-free line` when `is_safe_descriptive` is False. So `specs.run_new` needs the guard its sibling setter already has.
