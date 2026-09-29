# IPD: Convert the measured unbounded-section sites onto the bounded extractor

- Date: 2026-09-29
- Kind: child
- Concern: THE SITES BACKLOG `1pgrii` WAS FILED FOR ARE STILL THERE, AND AT LEAST TWO ARE DEMONSTRABLY WRONG TODAY. The item's own history line says the originating guard was "Bounded in place while executing skn8uk with a control test; this item records the class of defect for the other guards written the same way." An authoring census of `tests/` found 44 marker-located section extractions, of which 8 take an UNBOUNDED tail and 12 take a `split(MARKER)[0]` head whose fallback is the whole text. Two are provably defective against real producers, not hypothetically: `tests/test_backlog.py::test_set_transitions_status_moves_file_and_appends_history` counts `- ` lines to end of file and yields `4 != 2` when the real `backlog.run_new`/`run_set` pair writes an item with a `## Suggested work` body; and `tests/test_research_index.py::test_n_honored` counts `- ` bullets to end of file and yields 3 instead of 2 the moment any section is appended after `## Most recent`. A third, `tests/test_project_layout.py::test_e06`, bounds D130 at a literal `### D131.` and FALLS BACK to end of file, where 3 of its 5 required topics are satisfiable by unrelated later text; it survives only because the other 2 happen to be unique to D130. Order 01 (`78rxzc`) ships the mechanism; nothing consumes it until this plan does, and an unused helper is worse than none because it implies a protection that is not in force.
- Scope: Convert the measured sites onto `support.section` / `support.final_section` / `support.section_lines`, each conversion behavior-preserving and individually justified, and record at each excluded site WHY it is excluded. IN: the 8 unbounded-tail sites, the 3 `split(MARKER)[0]` head sites whose marker is a section heading, and the one `enumerate`/`break` walk that is the same defect spelled with a loop. EXCLUDES `tests/test_defect_report.py`'s `prompt[start:]`, where the unboundedness IS the assertion (it compares the tail EQUAL to `reporting_contract.contract_text()` to prove nothing follows the contract) and converting it would delete the property. EXCLUDES the 9 `split(SEP)[0]` sites whose separator is not a section heading (`":"`, `"."`, a literal id6), which are field parses and not section reads. EXCLUDES adding any author-time guard against a NEW unbounded slice, which needs its own design and is filed as a follow-up here. EXCLUDES every production module: this plan touches only files under `tests/`.
- Scope-Paths: tests/test_backlog.py, tests/test_research_index.py, tests/test_project_layout.py, tests/test_plans_board.py, tests/test_oc_runipd.py, tests/test_lifecycle_style.py, tests/test_completion.py, tests/test_plan_review_feasibility_rule.py, tests/test_orchestrator_retirement.py, tests/test_merge_conflict_sendback.py, tests/test_status_set.py, tests/test_defect_report.py
- Item-Dependencies: executed:78rxzc
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 1pgrii
- Blocks-Release: next
- Set: secbound
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: tr8ugt

## Workflow history

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `1pgrii` as the second half of Set `secbound`. Order 01 adds the helper; this plan is the only thing that makes it load-bearing. The E-items are grouped by WHAT THE CONVERSION PROVES rather than by file, because two sites are live defects that must go green on a new assertion (E-01, E-02), one is a false-green whose bound must start REFUSING (E-03), three read a genuinely terminal tail and must declare it (E-04), and the rest are uniformity conversions that must change no outcome (E-05, E-06). Every site was driven at authoring, and the sites that are CORRECT TODAY are labelled as such rather than reported as bugs.
- 2026-09-29 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Leave no test in the suite asserting over a section whose extent it did not establish, and leave at
each converted site a call that says out loud where the section ends.

Two sites must change OUTCOME (they are wrong today and a new assertion must prove the fix). The rest
must change NOTHING observable, and the evidence for each is the same test passing before and after.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the two sites that are wrong today

- [ ] E-01 FIX `tests/test_backlog.py`'s HISTORY READS, WHICH MISCOUNT A REAL ITEM'S RECORDS. Two call sites share the defect: `test_set_transitions_status_moves_file_and_appends_history` does `after = text.split("## Workflow history", 1)[1]` then asserts `len(inline) == 2` over every `- ` line to end of file, and `BacklogNoteVerbTests._records` does the same split and filters with `attention_contract.HISTORY_RECORD_RE`, serving five assertions. Convert BOTH to `support.section(text, "## Workflow history", "\n## ")`. THEN ADD THE ASSERTION THAT PROVES THE FIX, because a conversion that changes no test outcome does not demonstrate a bug was fixed: extend the transition test (or add a sibling) to create the item through the REAL `backlog.run_new` WITH a `--body` carrying a `## Suggested work` bullet list, transition it through the REAL `backlog.run_set`, and assert the history count is still 2. Measured at authoring: that exact fixture yields `AssertionError: 4 != 2` against the current code, with `- bound the guard` and `- add a control test` counted as history records. NOTE `_records` is the narrower of the two (the dated grammar excludes plain bullets) but is not safe: 69 of 1751 live records carry a DATED bullet after the bounded section.
  - Depends on: none
  - Expected outcome: both sites call `support.section`; the new body-bearing case passes at 2 and is shown to FAIL at 4 before the conversion; `python3 -m pytest tests/test_backlog.py` green with a count one or more higher than before.
  - Execution state: pending

- [ ] E-02 FIX `tests/test_research_index.py::test_n_honored`, WHICH COUNTS BULLETS TO END OF FILE. It does `recent_block = md.split("## Most recent")[1]` then asserts exactly 2 bullets starting `- ` + backtick. `## Most recent` IS the last section `research_index.build_index_md` emits today, so the test passes, but the bound is accidental: appending a section with bullets of the same shape makes the count 3. Measured at authoring by driving the real `build_index_md(entries, limit=2)` and appending `\n## Stale (needs review)\n\n- ` + one bullet: the count goes to 3 while the assertion demands 2. Convert to `support.final_section(md, "## Most recent", next_marker="## ")`, which is the honest statement: the caller relies on the section being terminal, so make that premise explicit and let it fail if the renderer grows a section.
  - Depends on: none
  - Expected outcome: the site uses `final_section`; the existing assertion still passes; adding a trailing section to the rendered output now REFUSES with a clear message instead of silently miscounting, demonstrated and pasted.
  - Execution state: pending

### Task group 2: the false-green bound

- [ ] E-03 MAKE `tests/test_project_layout.py::test_e06` REFUSE INSTEAD OF FALLING BACK TO END OF FILE. It finds `### D130.`, finds `### D131.`, and does `content[d130_start:d130_end] if d130_end != -1 else content[d130_start:]`. That `else` is the defect: rename or remove D131 and the "D130 section" becomes 71,763 chars instead of 2,170, and 3 of the 5 fixture-declared required topics (`physical .aw/`, `durable`, `runtime`) are present in the text AFTER D130, so they would be satisfied from the wrong record. Measured at authoring: with D130's body replaced by a placeholder AND D131 renamed, the test reports only `project.json` and `local.json` missing, so 3 of 5 topic checks pass vacuously. Convert to `support.section(content, "### D130.", "### D131.")`, deleting the fallback. KEEP the existing falsifiability assertion at the end of that test (`assertIn("nonexistent_architectural_topic_99999", d130_text)` inside `assertRaises`), which is already good practice and must not be lost in the edit.
  - Depends on: none
  - Expected outcome: the `else content[d130_start:]` fallback is gone; the test passes unchanged against the real `DECISIONS.md`; renaming `### D131.` in a scratch copy now raises `SectionBoundError` instead of extracting 71,763 chars, demonstrated and pasted; the falsifiability assertion is still present.
  - Execution state: pending

### Task group 3: the genuinely terminal tails, declared

- [ ] E-04 CONVERT THE THREE TERMINAL-TAIL SITES TO `final_section`, WHICH IS A STATEMENT OF PREMISE AND NOT A RENAME. (a) `tests/test_plans_board.py`'s `sets = out[out.index("## Sets"):]`, where `plans.render_status_index` emits the Sets view last: measured, the tail is 421 of 826 chars, and appending a `## Recently touched` section grows it to 495 while the `assertLess` keeps passing on first-occurrence luck. (b) `tests/test_oc_runipd.py`'s `block = out_mixed[out_mixed.index(pol.SUMMARY_HEADER):].splitlines()`, which sums per-disposition counts with a regex over the tail: the summary block from `run_selection_policy.render_disposition_summary` is followed by `render_continuation_hint`'s output, so the tail ALREADY includes a different producer's text (measured: 1604 chars, of which 485 belong to the Session Continuity block). For this one prefer `support.section(out, pol.SUMMARY_HEADER, "\n  total: ")` if the `total:` line is a reliable terminator (it is emitted unconditionally by `render_disposition_summary`, verified at authoring: the bounded read is 1119 chars and the counted total is unchanged at 4), and use `final_section` only if bounding proves fragile; state which you chose and why. (c) `tests/test_oc_runipd.py`'s `_disposition_lines` helper, which walks `lines[start + 1:]` with a `break` on the first non-`- ` line: the `break` IS a bound, so convert for uniformity only and confirm the extracted block is byte-identical before and after.
  - Depends on: none
  - Expected outcome: all three sites use a `support` entry point; each test passes unchanged; for (a) the appended-section refusal is demonstrated; for (b) the chosen terminator is named with its justification and the counted total is shown unchanged; for (c) the extracted block is shown identical.
  - Execution state: pending

### Task group 4: the uniformity conversions, which must change nothing

- [ ] E-05 CONVERT THE THREE LINE-ORIENTED / ALREADY-BOUNDED SITES TO `section_lines` OR `section`, CHANGING NO OUTCOME. (a) `tests/test_lifecycle_style.py::_parse_spec_section5` finds `## 5. ` by `enumerate`/`startswith` and walks with `break` on `## 6.`: that is bounded, but silently, and it makes NO assertion that the terminator exists, so a renamed Section 6 would widen the table scan from 22 rows to 118 (measured). Convert to `support.section_lines(text, "## 5. ", "## 6. ")`, which refuses instead. (b) `tests/test_plan_review_feasibility_rule.py::test_long_form_plan_review_feasibility_rule` does `content[start_idx:end_idx] if end_idx != -1 else content[start_idx:]`, the same fallback shape as E-03; convert and delete the fallback. Its SIBLING test in the same file already asserts `assertNotEqual(end_idx, -1)` before slicing, which is the correct behavior spelled by hand, so the conversion makes the two consistent. NOTE that file's module docstring records a deliberate P16 exemption (it reads workflow bodies, not `agent_workflows/*`); do not disturb it. (c) `tests/test_completion.py`'s `lines[esac_index + 1:]` walk: verified SAFE today (the generated script has exactly one `esac` at line 79 of 84, the 3 following non-comment lines contain 0 of the script's 24 `COMPREPLY=` lines), so convert for uniformity and report it as a uniformity change, NOT as a bug fixed.
  - Depends on: none
  - Expected outcome: all three sites converted; each file's tests pass with an unchanged count; for (a) the renamed-terminator refusal demonstrated; for (c) the report explicitly states no defect existed.
  - Execution state: pending

- [ ] E-06 CONVERT THE THREE SECTION-HEADING `split(MARKER)[0]` HEAD SITES, WHOSE FALLBACK IS THE WHOLE TEXT. When the marker is absent, `[0]` is the entire input, which breaks in both directions: an equality assertion between two such heads compares whole files and can pass vacuously, while an `assertNotIn` starts failing on unrelated tail content, which is `1pgrii`'s original shape. (a) `tests/test_backlog.py`'s two `.split("\n## Workflow history")[0]` head-equality pairs (the parked-metadata comparison and the header-prose comparison) and (b) `tests/test_status_set.py`'s `text.split("\n## ", 1)[0].splitlines()`: for these, extract the head with an explicit presence assertion for the marker rather than inventing a fourth helper (Order 01 records in its Scope check why no `head_before()` was built for 3 callers). (c) `tests/test_merge_conflict_sendback.py`'s `q_adj.lower().split("## conflict details")[0]`, which is the one caller needing `anchored=False`: it lowercases the whole subject first, so its marker matches no line start in the original text. Measured: with the marker renamed, `"unknown" in head` flips from False to True, i.e. the assertion goes red on tail content it never meant to read.
  - Depends on: none
  - Expected outcome: all three converted with an explicit marker-presence assertion or `anchored=False` as appropriate; each file's tests pass with an unchanged count; the `assertNotIn` site shown to still refuse its real target.
  - Execution state: pending

### Task group 5: record the exclusions where a reader will stand

- [ ] E-07 LEAVE A ONE-LINE COMMENT AT EACH DELIBERATELY EXCLUDED SITE, AND CONFIRM THE DEFERRED CARRIER IS STILL LIVE. The exclusion that matters is `tests/test_defect_report.py`'s `prompt[start:]`, which compares the tail EQUAL to `reporting_contract.contract_text()` with the failure message "text was added AFTER the reporting contract": the unbounded read IS the assertion, and a future agent sweeping for unbounded slices would break a working test. Add a comment naming this plan and stating that the unboundedness is load-bearing. Do the same at any site this plan leaves converted-but-notable. THEN CHECK, do not re-file, the deferred author-time guard: it was filed at authoring as `ap839o` and both plans in this Set carry it as their `Carrier`. Read it with `aw find backlog ap839o`, confirm its status is still live (`open`, `blocked` or `graduated`) and that nothing has superseded it, and if its `## Suggested work` no longer matches what this plan actually left undone, append a `aw backlog note` recording the difference rather than editing the item's requirements.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: the `tests/test_defect_report.py` comment quoted, naming this plan and the reason; `ap839o` read and its live status pasted, with a `note` appended if its scope drifted from what this plan left undone; `python3 -m pytest tests/test_defect_report.py` green (the comment changes no behavior).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/support.py` is imported both as `from tests import support` and as `from tests.support import <name>`; both spellings are live across the suite, so follow whichever each converted file already uses rather than introducing a second style into one file.
- `agent_workflows/plan_readiness.py`'s docstring is the repository's own record of this defect class in production (an unbounded `rfind` slice that ran to end of file across 13 headings and returned a non-history line for 35 of 35 pending plans), and it explicitly reuses `attention._history_section_lines` rather than hand-rolling a fourth parser. That is the precedent this Set follows for the suite.
- `tests/test_plan_review_feasibility_rule.py` opens with an "Exemption from source-text-pin prohibition" docstring justifying itself against a deletion sweep: it reads WORKFLOW BODIES, not `agent_workflows/*`. Preserve that docstring; the conversion in E-05(b) does not change what the test reads.
- `GUIDING_PRINCIPLES.md` P16 prohibits reading production source in a test. Every site this plan converts reads either a RECORD written by a CLI under test, or rendered CLI OUTPUT, or a non-production document (`DECISIONS.md`, a workflow body, a spec). None reads `agent_workflows/*.py`, and the conversions must not change that.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | HIGH | THE BACKLOG SITE IS A LIVE MISCOUNT, DRIVEN AGAINST REAL WRITERS. `test_set_transitions_status_moves_file_and_appends_history` asserts exactly 2 history bullets over an unbounded tail. Creating the item through `backlog.run_new` with `--body "## Suggested work\n\n- bound it\n- control test\n"` and transitioning it with `backlog.run_set` yields 4. | driven probe at HEAD `20d389df`: `AssertionError: 4 != 2 : ['- 2026-09-29 set (aw backlog): finished', '- 2026-09-29 created (aw backlog): an item', '- bound the guard', '- add a control test']` |
| F-02 | HIGH | THE RESEARCH-INDEX SITE IS ONE APPENDED SECTION FROM RED. `test_n_honored` counts 2 bullets after `## Most recent`; driving the real `build_index_md(entries, limit=2)` and appending `## Stale (needs review)` with one same-shaped bullet makes the count 3. | driven probe: `build_index_md` emits no heading after `## Most recent` today; with one appended section the bullet count is 3 against an assertion of 2 |
| F-03 | HIGH | THE D130 SITE IS A FALSE GREEN WAITING ON A RENAME, AND 3 OF ITS 5 CHECKS ARE ALREADY SATISFIABLE FROM THE WRONG PLACE. `content[d130_start:d130_end] if d130_end != -1 else content[d130_start:]` falls back to 73,887 chars (bounded: 2,170). `physical .aw/`, `durable` and `runtime` all appear after D130; only `project.json` and `local.json` are unique to it. | driven probe: bounded 2,170 vs EOF 73,887; a gutted-D130-plus-renamed-D131 probe reports only 2 of 5 topics missing |
| F-04 | MEDIUM | THE PLANS-BOARD AND SUMMARY TAILS ARE ACCIDENTALLY BOUNDED BY BEING LAST, AND ONE ALREADY READS A SECOND PRODUCER'S OUTPUT. `render_status_index`'s Sets tail is 421 of 826 chars and grows to 495 when a section is appended, with the assertion still passing. The `pol.SUMMERY_HEADER` tail in `tests/test_oc_runipd.py` is 1604 chars of which 485 is `render_continuation_hint`'s Session Continuity block, so the test is already reading text a different function emitted; bounding at the unconditional `  total: ` line gives 1119 chars and the same counted total of 4. | driven probes of `plans.render_status_index` and of `driver.run_queue`'s captured stdout |
| F-05 | MEDIUM | THE `split(MARKER)[0]` HEAD FORM FAILS IN BOTH DIRECTIONS, SO THE THREE SECTION-HEADING CALLERS MUST BE CONVERTED DELIBERATELY RATHER THAN SWEPT. With the marker absent the head is the WHOLE text: an equality assertion then compares whole files (can pass vacuously), and an `assertNotIn` goes red on tail content. | probes: renamed marker makes the head equal the whole text; the `assertNotIn` probe flips False to True |
| F-06 | MEDIUM | THE ANCHORING DEFECT IS REAL AT THE `## Workflow history` SITES SPECIFICALLY, WHICH IS WHY ORDER 01 ANCHORS BY DEFAULT. 33 of 1806 tracked records contain that heading's text in body prose earlier than the real heading; for the worked case the unanchored offset is 463 and the heading is at 2038. The backlog sites this plan converts read records written by the CLI under test (short, no quoting prose), so anchoring is a correctness improvement rather than a fix to a live failure there; say so rather than overclaiming. | corpus sweep at authoring: 33 of 1806; example `.aw/records/backlog/done/20260918-yvp951-...backlog.md` |
| F-07 | LOW | TWO SITES ARE CORRECT TODAY AND MUST BE REPORTED AS UNIFORMITY CONVERSIONS. `tests/test_completion.py`'s `esac` walk is safe (one `esac` at line 79 of 84; 3 non-comment lines after it; 0 of the 24 `COMPREPLY=` lines among them). `tests/test_oc_runipd.py::_disposition_lines` already breaks on the first non-`- ` line, so it IS bounded, just silently. | driven probe of `completion.generate_bash_completion()`; the helper's own `break` |
| F-08 | LOW | ONE SITE THAT LOOKS LIKE THE BUG IS THE ASSERTION ITSELF AND MUST BE EXCLUDED WITH A COMMENT. `tests/test_defect_report.py` compares `prompt[start:]` EQUAL to `RC.contract_text()`; its message is "text was added AFTER the reporting contract". Bounding it would delete the property. | the site's `assertEqual` and failure message |
| F-09 | LOW | THE 9 REMAINING `split(SEP)[0]`/`[1]` SITES ARE FIELD PARSES, NOT SECTION READS, AND ARE OUT OF SCOPE. Their separators are `":"`, `"."`, `"="`, `"---"`, `"\n\n"` or a literal id6 (`tests/test_check_engine.py`, `tests/test_lane_import_root.py`, `tests/test_completion.py`, `tests/test_term.py`, `tests/test_attention.py`, `tests/test_research_cmd_create.py`, `tests/support.py`). Converting them would be a rename with no bound to gain. | authoring census: 44 marker-located extractions total, 8 unbounded tails, 12 `[0]` heads of which 3 are section headings |

### Why the conversions are split by what they prove

An E-item that says "convert 14 sites" produces one diff a reviewer cannot judge, because the sites are
not the same kind of change. Two must change OUTCOME and need a new assertion to prove the fix (E-01,
E-02). One must delete a fallback that is measurably a false green (E-03). Three rely on being last and
must say so (E-04). Six must change NOTHING, and the evidence for each is a test count that did not move
(E-05, E-06). Grouping by property means each V-item can demand the right evidence: a new failing-then-
passing case for the first group, an unchanged count for the last.

### Why no site is converted "for tidiness" without a stated verdict

Two of the sites in scope are CORRECT TODAY (F-07). They are converted for uniformity, so one rule
governs every section read in the suite and the next author has no correct-looking precedent to copy for
an unbounded slice. But a plan that reported them as bugs fixed would be dishonest, and a plan that
silently converted them would leave a reader unable to tell which conversions mattered. Each V-item
therefore states the verdict for its sites: defect fixed, false green closed, premise declared, or
uniformity only.

## Proposed changes (ordered, validatable)

1. E-01 fixes the backlog history miscount and adds the body-bearing case that proves it.
2. E-02 declares the research-index tail terminal so it refuses instead of miscounting.
3. E-03 deletes the D130 end-of-file fallback.
4. E-04 declares the three terminal tails (and bounds the summary block at its `total:` line if that holds).
5. E-05 converts the three line-oriented / hand-bounded sites.
6. E-06 converts the three section-heading head splits.
7. E-07 records the deliberate exclusions and files the deferred author-time guard.

E-01 through E-06 are independent of one another and may be performed in any order. E-07 depends on all
of them, since it records what was and was not done.

## Deferred / out of scope (with reason)

- AN AUTHOR-TIME GUARD REFUSING A NEW MARKER-LOCATED UNBOUNDED SLICE IN `tests/` is the residue that keeps this class from returning. It is deferred rather than built because it needs a detector design neither plan in this Set has done (`x[start:]` is not distinguishable from a legitimate tail slice without knowing that `start` came from a marker search), and because it is the same shape as `structpin` Order 02 (`76ic0k`), which adds an AST guard over `tests/` and should land first so the two do not collide. Filed at authoring as `ap839o`; E-07 verifies it is still live and un-superseded rather than re-filing it.
  - Carrier: ap839o
- `tests/test_defect_report.py`'s `prompt[start:]` is PERMANENTLY excluded, per F-08. E-07 leaves a comment at the site so a future sweep does not break it.
  - Carrier-Declined: A CORRECT SITE, not deferred work. The unbounded read IS the assertion that the reporting contract is last in the prompt, so there is nothing to fix and a carrier would invite a future agent to "finish the sweep" by deleting a working property.
- THE 9 NON-SECTION `split(SEP)` SITES are out of scope, per F-09: their separators are field delimiters, so there is no section extent to establish.
  - Carrier-Declined: NO DEFECT EXISTS. `line.split(":", 1)[1]` is a field parse whose failure mode is an `IndexError` a test would see immediately, not a silently widened assertion. Filing an item would promise a conversion with no property to gain.
- BOUNDING THE PRODUCTION READERS is already owned elsewhere: `attention._history_section_lines` and `selectors.metadata_region` are the shipped authorities, and plan `xvon5j` (Set `idcapture`) is finishing the remaining unbounded identity readers with those exact modules in its `Scope-Paths`.
  - Carrier: xvon5j

## Scope check

- Over-scope: the 12 declared `Scope-Paths` entries are a wide surface for one plan, and that is deliberate rather than accidental: the defect is ONE class spread across files, and converting a subset would leave the helper half-adopted and the next author with a correct-looking unbounded precedent to copy. Every path is a test file, no production module is touched, and one path (`tests/test_defect_report.py`) is declared for a COMMENT only. If any file turns out to need more than its declared conversion, STOP and report rather than widening.
- Under-scope: nothing new is prevented (the author-time guard is deferred with a carrier to file), and the 9 field-parse splits are left alone with the reason recorded. The `tests/test_oc_runipd.py` summary site may end up on `final_section` rather than a bounded `section` if the `total:` terminator proves unreliable; E-04 requires the choice to be stated, so the residue is visible either way.

## Required tests / validation

Per-file runs for every touched file, with the test count BEFORE and AFTER, because the whole claim for
groups 4 and 5 is that nothing moved. For E-01 the count must RISE (a new case is added) and the new
case must be shown RED against the unconverted code first.

Then the bare suite. The authoring baseline at HEAD `20d389df` was `3246 passed, 2 skipped` with 207
deselected; Order 01 lands first and adds tests, so re-derive the baseline at execution rather than
using this number. Run it BARE as `python3 -m pytest`: `pyproject.toml` `addopts` already supplies `-q -n
auto --dist=worksteal -m 'not slow'`, and adding a second `-q` suppresses the `N passed` line this plan
requires pasted.

Every refusal introduced by a conversion (E-02, E-03, E-05(a)) must be DEMONSTRATED against a scratch
copy of the real input, not asserted, and the input must be confirmed restored afterwards.

## Spec / documentation sync

No `.spec.md` amendment is owed and no spec path appears in `Scope-Paths`. No spec describes the suite's
section-reading conventions. `GUIDING_PRINCIPLES.md` P16 is the governing policy and is complied with,
not changed: every converted site reads a record, rendered CLI output, or a non-production document, and
none reads `agent_workflows/*.py`. No user-facing documentation changes, so the em-dash prose rule does
not bind the comments this plan writes.

## Open questions

### OQ-01: Should the `tests/test_oc_runipd.py` summary site be bounded at the `total:` line, or declared terminal?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM A DRIVEN MEASUREMENT as BOUND IT AT THE `total:` LINE, with `final_section` named as the fallback if execution finds that terminator unreliable. The decisive fact is that `final_section` would be FALSE here: the tail after `pol.SUMMARY_HEADER` is 1604 chars, of which 485 belong to `render_continuation_hint`'s Session Continuity block, so the section is NOT terminal and declaring it so would refuse immediately. `render_disposition_summary` appends its `  total: {matched} matched, ...` line UNCONDITIONALLY as the last element of its returned lines, and its docstring states the reason ("The counts are RESTATED as a total rather than left for the reader to add up, so the block's own guarantee (nothing matched is omitted) is checkable on its face by a `tail` reader"), which makes it a documented, deliberate terminator rather than an incidental string. Driven at authoring: bounding there gives 1119 chars instead of 1604 and the summed per-disposition count is unchanged at 4. E-04 requires the executor to state which option was taken, because if `render_disposition_summary` ever drops the total line the honest answer changes and the plan should not pretend otherwise.

### OQ-02: Should this plan also convert the sites in files it does not otherwise touch, to finish the census in one pass?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as NO, the census is already fully accounted for and nothing is left unexplained. The authoring census found 44 marker-located extractions: 8 unbounded tails and 12 `[0]` heads, of which this plan converts 8 tails plus 3 section-heading heads plus 1 `enumerate`/`break` walk, excludes 1 tail permanently with a comment (F-08), and excludes 9 heads as field parses with the reason recorded (F-09). So there is no residual set to "finish"; every site has a verdict. The reason this matters is that a plan claiming to convert "all of them" would be making a completeness claim its own detector cannot support (the detector is syntactic and cannot see a marker search whose result flows through an intermediate variable across functions), whereas a plan that enumerates its sites and states a verdict for each is checkable. If execution's own re-run of the census finds a site this plan does not list, STOP and report it rather than silently converting it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: VERDICT: DEFECT FIXED. Paste the diff for both `tests/test_backlog.py` sites. Paste the NEW body-bearing case's source, showing it drives the real `backlog.run_new` with a `--body` carrying a `## Suggested work` list and the real `backlog.run_set`. Paste that case FAILING against the pre-conversion read (`4 != 2`, with the four bullets listed) and then PASSING after, which is what distinguishes a fix from a rename. Paste `python3 -m pytest tests/test_backlog.py` before and after with both counts, showing the count ROSE. Confirm `BacklogNoteVerbTests`' five assertions still pass and state whether any of them changed outcome (expected: none).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: VERDICT: LATENT DEFECT CLOSED. Paste the diff. Paste `python3 -m pytest tests/test_research_index.py` before and after with counts, showing them equal (the existing assertion must not change outcome). Then paste the demonstration that the bound is now live: append a section with one same-shaped bullet to REAL `build_index_md` output and show `final_section` refusing, beside the pre-conversion behavior counting 3 against an assertion of 2. Confirm no fixture file was left modified.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: VERDICT: FALSE GREEN CLOSED. Paste the diff, showing the `else content[d130_start:]` fallback deleted. Paste `python3 -m pytest tests/test_project_layout.py` before and after with counts. Paste the refusal demonstration on a SCRATCH copy of `DECISIONS.md` with `### D131.` renamed, and confirm the real `DECISIONS.md` is byte-identical afterwards (`git diff DECISIONS.md` empty). RE-MEASURE and paste your own bounded and fallback lengths (authoring: 2,170 and 73,887) and your own count of which required topics are satisfiable from text after D130 (authoring: 3 of 5). Confirm the existing falsifiability assertion is still present, quoted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: VERDICT: PREMISE DECLARED. For (a), paste the diff and the refusal demonstration on appended `render_status_index` output, with the pre-conversion contrast (tail grows 421 to 495 and the assertion still passes) re-measured by you. For (b), STATE WHICH OPTION YOU TOOK (bounded at `  total: ` or `final_section`) and WHY, paste the bounded length and the summed count before and after (authoring: 1604 to 1119 chars, count unchanged at 4), and confirm the Session Continuity text is no longer inside the read. For (c), paste proof the extracted block is IDENTICAL before and after. Paste `python3 -m pytest tests/test_plans_board.py tests/test_oc_runipd.py` before and after with counts, showing them equal.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: VERDICT: (a) SILENT BOUND MADE EXPLICIT, (b) FALLBACK DELETED, (c) UNIFORMITY ONLY. Paste all three diffs. For (a), paste the refusal demonstration with `## 6. ` renamed in a scratch copy, plus your own row counts bounded versus to-EOF (authoring: 22 versus 118), and confirm the real spec file is unmodified. For (b), confirm the module docstring's P16 exemption paragraph is untouched, quoted, and that the sibling test's existing `assertNotEqual(end_idx, -1)` still passes. For (c), state explicitly that NO DEFECT EXISTED and paste your own re-measurement (`esac` count and position, non-comment lines after it, `COMPREPLY=` lines among them versus in the whole script). Paste per-file pytest counts before and after, equal in all three.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: VERDICT: WHOLE-TEXT FALLBACK REMOVED. Paste all three diffs. For each, show the marker-presence assertion (or `anchored=False`) explicitly. Paste per-file pytest counts before and after, equal in all three. For the `tests/test_merge_conflict_sendback.py` site, paste proof the `assertNotIn` still refuses its real target (drive `runner_shared.merge_conflict_question` and show the bounded head and the tail, with `unknown` absent from the head and present in the tail), and state why `anchored=False` is required there (the subject is lowercased before splitting, so the marker matches no line start in the original text).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the comment added at `tests/test_defect_report.py`, showing it names this plan and states that the unboundedness is the assertion. Paste `python3 -m pytest tests/test_defect_report.py` before and after with equal counts. Paste `aw find backlog ap839o` showing the deferred author-time guard is still live and un-superseded, and state whether its `## Suggested work` still matches what this Set actually left undone; if it does not, paste the `aw backlog note` you appended. Confirm you did NOT re-file it and did NOT edit its requirements. FINALLY paste the bare `python3 -m pytest` summary line with your observed counts and confirm that, across the whole plan, no test changed from passing to failing and no test was deleted or renamed to avoid a conversion.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

DO NOT EXECUTE BEFORE ORDER 01 REACHES `executed`. This plan declares `- Item-Dependencies: executed:78rxzc` and the dependency is load-bearing rather than cosmetic: every E-item calls `support.section`, `support.final_section` or `support.section_lines`, none of which exist until Order 01 lands. The runner re-checks dependencies at dispatch and will mark this item `dependency-blocked` rather than run it; an agent executing the Set by hand must honor the same order.

EXECUTE ONLY WHAT THIS PLAN DECLARES. The 12 `Scope-Paths` entries are the whole authorized surface, and one of them (`tests/test_defect_report.py`) is declared for a COMMENT ONLY. If a conversion turns out to need a change this plan did not predict, or if your own re-run of the census finds a site not listed in Findings, STOP and report it: the correct response is a decision about that site, which may belong to a new carrier, and never a silent extra conversion.

DO NOT MAKE A TEST PASS BY WEAKENING IT. Three conversions introduce a REFUSAL (E-02, E-03, E-05(a)), and a refusal that fires during execution means a producer really has changed shape; the answer is to report it, never to restore a fallback or delete the assertion. Equally, do not delete or rename a test to avoid converting it: V-07 requires a confirmation that none was.

DO NOT CONVERT `tests/test_defect_report.py`'s `prompt[start:]`. Its unboundedness IS the assertion that the reporting contract is the last thing in the prompt. E-07 adds a comment saying so precisely because a later sweep would otherwise break it.

HONESTY, AND THE VERDICT PER SITE. Paste actual runner output; never claim a test run you did not perform. Two of the sites in scope are CORRECT TODAY (`tests/test_completion.py`'s `esac` walk, `_disposition_lines`' `break`) and must be reported as uniformity conversions, not as bugs fixed. Every figure in this plan (4 versus 2, 3 versus 2, 2,170 versus 73,887, 421 versus 495, 1604 versus 1119, 22 versus 118, 33 of 1806, 69 of 1751, the 44-site census) is an AUTHORING measurement: re-measure at execution and report your own number, stating plainly if it differs.

COMMIT DISCIPLINE. Commit through `aw commit <plan> -- <paths>`, path-scoped to the files this plan names, never `git add -A`/bare/`-a`, and never push. Other agents may be working in this checkout: verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`. Prefer one commit per task group so a reviewer can read the outcome-changing conversions separately from the uniformity ones.

LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item must carry pasted evidence before this plan moves to `.aw/records/plans/executed/`. Use the tooled transition; do not hand-edit `- Status:`.
