# IPD: Build a reproducible lost-guard census over the two suite-trim commits and triage only the behavioral gaps

- Date: 2026-09-30
- Kind: child
- Concern: Backlog `xvp5vx` asks which properties lost their ONLY guard in the suite trim `19313eed`. Nothing has audited this, and the question is currently unanswerable in a reproducible way: every prior answer (plans `t0ovw6` and `7dz3wv`, backlog items `pn7rw3`, `rcp8c4`, `gia5i7`, `ikxtkj`, `tvv8gg`, `l8upzx`, `p7k57l`, `rdl9lh`, `089bq4`, `2jz47s`) was found by hand, one symbol at a time, by whoever happened to be editing nearby. That sampling has already yielded ELEVEN filed items and one shipped regression (`39jkux`), so the population is real; what is missing is a census that can be re-derived. THE ITEM'S FRAMING IS ALSO MEASURABLY INCOMPLETE IN ONE WAY THAT CHANGES THE WORK: the trim was TWO commits, not one (`80db6750c` removed 366 code-pinning tests on 2026-09-23, `19313eed` removed 7,402 the next day), and the most-cited "lost guard" in the whole tree (`test_no_new_module_level_first_party_import_in_runner_shared`, 6 citations in `runner_shared.py`) was an `ast.parse` CODE PIN deleted by the FIRST commit, which the maintainer's own ruling says must never be restored. So a naive audit of `19313eed` alone would both misattribute that loss and propose restoring exactly what P16 forbids.
- Scope: Deliver a COMMITTED, reproducible census scanner plus a triage report, and file each genuine behavioral gap as its own backlog item. The scanner answers one question per candidate: a property whose guard the trim deleted, which NO surviving test covers, and which is a BEHAVIORAL outcome rather than a code/AST/text pin. It reports over BOTH trim commits and attributes each loss to the correct one. This plan produces a REPORT and FILED ITEMS, not fixes: no deleted test is restored here and no production behavior changes. EXCLUDES restoring any code-pinning test (maintainer ruling, carried in the item's own history); EXCLUDES the eleven already-filed instances (measured: 61 of 107 dangling citations are already owned by a live item), which the scanner must DEDUPE against rather than re-file; EXCLUDES the `docs/` citation axis, which pending plan `1jg2m2` already owns including its guard test.
- Scope-Paths: tools/lost_guard_census.py, tests/test_lost_guard_census.py, tools/README.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: xvp5vx
- Set: xvp5vx
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: oyh28b

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `xvp5vx`. Every measurement taken against this lane's working tree at HEAD `ffb8e9e45`. The item's single-commit framing is corrected by measurement (F-02), and its "prefer MUTATION as the test of coverage" instruction is accepted in principle but BOUNDED by a cost measurement that makes the naive reading impossible (F-06): one bare suite run is 203s here, so per-candidate mutation over 46 unowned candidates is roughly 2.6 hours of pure suite time and is reserved for the shortlist the cheap axes produce.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Replace hand-sampling with a re-derivable census. After this plan, one committed command answers "what did the two trim commits leave unguarded?", attributes each loss to the right commit, excludes code pins by construction, dedupes against the eleven already-filed instances, and emits a triage list; and every genuine behavioral gap it finds is a filed backlog item rather than a paragraph in a plan nobody re-runs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the committed census scanner

- [ ] E-01 Create `tools/lost_guard_census.py`, a committed scanner whose contract is REPRODUCIBILITY, following the precedent `tools/runner_fork_scan.py` sets explicitly ("the contract this file owes its callers is not 'a number' but 'the SAME number, next week, from a different machine, by a different agent'"). It must take the trim commits as ARGUMENTS defaulting to both (`80db6750c` and `19313eed`), never hardcode a single commit, and recover deleted test bodies with `git show <commit>^:<path>` rather than from any local artifact.

  IT MUST SCAN BOTH DELETED AND MODIFIED FILES. Measured (F-03): `19313eed` deleted 298 test files AND modified 20, and `80db6750c` deleted ZERO files while modifying 112. A scanner looking only at `--diff-filter=D` would therefore see NOTHING of the first trim commit and would miss the 20 modified files in the second. Compute removals per file as a multiset difference of test-function names between `<commit>^:<path>` and `<commit>:<path>`, which is the method that produced F-03's 366 and 7,402 figures.

  REPORT THE METRIC, NEVER AN UNLABELLED NUMBER, for the reason `runner_fork_scan.py` records at length (three line metrics circulated in one Set and differed by more than 2x, so a plan quoted a figure that reproduced under no metric). Headline the TEST-FUNCTION COUNT, which reproduced exactly at every measurement here.
  - Depends on: none
  - Expected outcome: `python3 tools/lost_guard_census.py --summary` prints, per trim commit, the deleted-file count, modified-file count, and net test functions removed, reproducing F-03's `80db6750c: 0 deleted / 112 modified / 366 removed` and `19313eed: 298 / 20 / 7402` exactly.
  - Execution state: pending

- [ ] E-02 Add the CODE-PIN CLASSIFIER, which is what makes this census obey the maintainer ruling BY CONSTRUCTION rather than by an auditor's good intentions. The ruling, carried verbatim in this item's own workflow history, is absolute: "Any audit of deleted tests must strictly ignore tests that pinned code, AST, or text, and must never propose restoring them." Classify each removed test function by its source segment and EXCLUDE it from every triage output when it reads production source.

  CLASSIFY ON SIGNALS MEASURED PRESENT IN THE REAL CORPUS, not invented ones: `inspect.getsource`, `inspect.getsourcelines`, `ast.parse`, `ast.walk`, `ast.unparse`, `linecache`, and a `read_text()` whose argument resolves under `agent_workflows/`. Measured with this exact signal set (F-04): 54 of `19313eed`'s removed functions classify as code pins. STATE THE SIGNAL SET'S KNOWN WEAKNESS IN THE SCANNER'S DOCSTRING AND IN THE REPORT, because it is a FLOOR AND NOT A TOTAL: the whole of `80db6750c` (366 tests) was deleted precisely for being code pins, so a classifier that found only 54 across the much larger second commit is certainly under-counting, and the honest posture is that the classifier is a cheap pre-filter whose misses are caught by the human triage step, never a proof that a candidate is behavioral.

  THE SHARPEST CASE IS ALREADY MEASURED AND MUST BE A FIXTURE, because it is the exact error this classifier exists to prevent and a plausible audit would have got it wrong (F-05): `test_no_new_module_level_first_party_import_in_runner_shared` is the most-cited missing guard in the tree (6 citations in `runner_shared.py` alone, 8 counting siblings), it is cited as living in `tests/test_orchestrator_probe_cache.py`, and its body is an `ast.parse` over `rs.__file__` walking module-level imports. It must classify as a CODE PIN and be excluded from triage.
  - Depends on: E-01
  - Expected outcome: the scanner excludes code-pinning removals from all triage output, reproduces F-04's count of 54 for `19313eed`, classifies the F-05 fixture case as a code pin, and prints the floor-not-total caveat in its report.
  - Execution state: pending

- [ ] E-03 Add the TWO CHEAP CITATION AXES, which are what make this audit tractable at all and which between them found every instance already filed. Both ask a FILESYSTEM question about repository CONTENT, which is the shape `GUIDING_PRINCIPLES.md` P16 names as its "one narrow exception" ("verifying published documentation does not cite deleted test files"); neither inspects production code for structure.
  - AXIS A, dangling PATH citations: extract every `tests/test_*.py` path cited in live non-record files and report those that do not exist. Measured (F-07): 107 distinct dangling paths, 290 hits, 68 carrying files; 85 attributable to `19313eed`, 0 to `80db6750c`, and 22 to NEITHER trim commit, which is a finding in itself and must stay a labelled category rather than being silently attributed to the trim.
  - AXIS B, dangling `::Symbol` citations: extract every `::Name` test-symbol citation and report those resolving to no live test class or function. Measured (F-08): 59 distinct, 98 hits, 23 carrying files. This axis is NOT redundant with A: a citation may name a file that still exists while the class inside it is gone, which is exactly how `gia5i7` was found (`NoRunnerImportTests`, 8 citations, exists nowhere).

  EXCLUDE THREE FALSE-POSITIVE CLASSES, each measured rather than assumed. (1) `.aw/records/` entirely: terminal plans and reviews are immutable and their citations were correct when written, which is the same bound pending plan `1jg2m2` applies. (2) ILLUSTRATIVE PLACEHOLDERS: `tests/test_x.py` and `tests/test_extra.py` are cited 2 times each from `ipd_schema.py`, `ipd_lifecycle.py` and `run_evidence.py` as EXAMPLES inside docstrings and comments, so they must never resolve and are not defects (F-09). (3) `tests/` fixture paths constructed under a `tmp_path`, which are correct as written.
  - Depends on: E-01
  - Expected outcome: `--axis a` and `--axis b` each reproduce their measured census exactly, attribution is reported per trim commit with a separate "neither" bucket, and the three excluded classes are excluded by name with the reason printed.
  - Execution state: pending

- [ ] E-04 Add the DEDUPE PASS against already-filed work, without which this plan's deliverable is a list of mostly-known problems and its triage step re-files eleven items that already exist. For each candidate, report whether any LIVE backlog item (`open`, `graduated`, or `blocked`) already names it, and emit `owned` versus `unowned` as distinct sections.

  Measured (F-10): of the 85 trim-attributable dangling paths, 28 are already named by a live item and 57 are not; narrowing to citations from SHIPPED SOURCE (`agent_workflows/` or `tools/`), 69 dangle and 46 are unowned. Those 46 are this plan's real triage population, and the ordering is informative rather than flat: `tests/test_orchestrator_probe_cache.py` (12 citations) and `tests/test_runner_item_dependencies.py` (10) dominate it.

  PREFER THE SHIPPED-SOURCE SUBSET AS THE DEFAULT TRIAGE VIEW, and say why in the report: a dangling citation inside `tests/` misleads a test author, while one inside `agent_workflows/` SHIPS to users in the installed package and is the half the maintainer has already been fixing by hand (backlog `zftbta` records 44 such citations costing repeated manual work).
  - Depends on: E-01, E-03
  - Expected outcome: the scanner emits `owned`/`unowned` sections citing the owning item's id6 where one exists, reproducing F-10's 28/57 split on all paths and 23/46 on the shipped-source subset.
  - Execution state: pending

### Task group 2: behavioral coverage, proven by mutation on a bounded shortlist

- [ ] E-05 Apply MUTATION as the coverage test, which the item names as the preferred technique ("Prefer MUTATION as the test of coverage ... since a property can look covered by a test that reads its expected value from the same place the code reads it") and which is also P16's own validity test for a test. ACCEPT THE TECHNIQUE AND BOUND ITS POPULATION, because the naive reading is not affordable and an executor who discovers that mid-run will either blow the budget or quietly skip the step.

  THE BOUND IS A MEASUREMENT, NOT A PREFERENCE (F-06): one bare suite run on this machine is `203.41s`. Mutation coverage requires at least one full suite run per candidate, so the 46 unowned shipped-source candidates cost roughly 2.6 hours of pure suite time before any analysis, and the full 107 would be over 6 hours. SO: select a shortlist of AT MOST FIVE candidates, chosen by citation count and by whether the cited property is a user-facing outcome, and mutation-prove those. Report the remainder as `triaged-not-mutated` with its reason, which is an honest partial rather than a silent one.

  MUTATE IN MEMORY, NOT ON DISK, for the reason `t0ovw6`'s review established as the method rule in this shared checkout: a `git checkout` restore after a multi-minute suite run discards whatever a co-worker wrote to that file in the interval. Use a pytest plugin (`-p`) that patches the subject in `pytest_configure` and restores it in `pytest_unconfigure`, or `mock.patch.object`, and paste `git status --short` empty before and after each run.
  - Depends on: E-04
  - Expected outcome: at most five candidates mutation-tested in memory with each run's actual pytest summary line pasted, each verdict recorded as `guarded` or `unguarded`, the tree clean before and after, and the un-mutated remainder listed as `triaged-not-mutated` with the F-06 cost as the stated reason.
  - Execution state: pending

- [ ] E-06 Add `tests/test_lost_guard_census.py`, exercising the scanner as a BEHAVIORAL test: drive the classifier and both axes over SYNTHESIZED fixture inputs and assert on returned verdicts and exit codes. Do NOT assert over the live tree's census counts: those numbers move every time any agent edits a comment, which is the measured failure `pyproject.toml`'s `livecorpus` marker exists to record (2026-09-19: one such test went red on three correctly-cleared plans, costing 2h 10m and $55.02 with nothing integrated). Anchor every input instead, per P16's "synthesize the input (the default)".

  THE CLASSIFIER NEEDS A BIDIRECTIONAL FIXTURE PAIR, because a classifier that answers "code pin" to everything would pass a one-sided test and would silently empty the triage list, which is the failure mode that would make this whole plan produce a reassuring and useless report: include the F-05 `ast.parse`-over-`rs.__file__` body, which must classify as a CODE PIN, AND a behavioral body that drives a CLI and asserts on its exit code, which must classify as BEHAVIORAL.

  CARRY NO `livecorpus` MARKER and do not read `.aw/records/`, so the test is selected by the default bare run and can actually catch a regression.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a new unmarked test file that passes in the default bare run, drives the scanner over synthesized fixtures only, and asserts both classifier directions.
  - Execution state: pending

- [ ] E-07 FILE each genuine behavioral gap as its own backlog item with `aw backlog new`, paste the real output, and record each item's id6 in this plan. This is the item's own stated deliverable ("Produce a triage list, not necessarily a fix; each real gap becomes its own item").

  FILE NOTHING FOR A CODE PIN, and file nothing already owned: E-02 and E-04 exist to make both refusals mechanical. For each filed item state the measured evidence (citation count, citing files, mutation verdict where E-05 produced one) and justify the `- Work-Kind:`, which is NOT automatic: an absent test is not by itself user-perceptible, so `chore` is the default, while a gap whose mutation proof shows WRONG USER-VISIBLE BEHAVIOR shipping is a `bug` and then MUST carry `- Blocks-Release:` per this repository's gating rule.

  ALSO FILE THE ATTRIBUTION CORRECTION the census turns up as a defect in its own right: `runner_shared.py` and its siblings cite `test_no_new_module_level_first_party_import_in_runner_shared` as a live guard 8 times, and it was deleted by `80db6750c` as a deliberate P16 retirement, so the correct fix is to state that the pin was RETIRED and will not return, never to restore it (F-05). Check first whether `rcp8c4` or `gia5i7` already covers those exact sites and extend rather than duplicate if so.
  - Depends on: E-05
  - Expected outcome: one backlog item per unowned behavioral gap and one for the misattributed-retired-pin citations, each created via `aw backlog new` with pasted output, a justified work-kind, a release gate where filed as `bug`, and its id6 recorded here; zero items filed for code pins or for already-owned instances.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A COMMITTED SCANNER IS THE ESTABLISHED SHAPE FOR A REPRODUCIBLE CENSUS, and the precedent states the reason in its own words. `tools/runner_fork_scan.py`'s header records that every plan in the `hostdedup` Set quoted a fork count and "until this file landed NONE of those numbers could be re-derived: the authoring scans were ad hoc, run in a shell and thrown away", with the orchestrator `a5wdne` recording that as PR-006. This plan's deliverable is the same shape for the same reason, which is why it is a tool and not a findings table.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Every measurement here used bare `python3 -m pytest`, or `-o addopts=""` where a per-test count was needed.
- P16 PERMITS THIS AUDIT'S AXES AND FORBIDS ITS TEMPTING OVER-REACH, and the distinction is the plan's spine. Section 16's "one narrow exception" permits content verification "where the text or file itself is the artifact under test (for example, verifying published documentation does not cite deleted test files)", which is exactly axes A and B. The same section forbids `ast.parse` over `agent_workflows/*.py` to verify wiring, which is exactly what the deleted guards did and what E-02 refuses to propose restoring.
- A TEST ASSERTING OVER THE LIVE RECORDS TREE MUST BE `livecorpus` AND IS THEN DESELECTED BY DEFAULT, which decides E-06's shape. `pyproject.toml`'s marker entry records the measured cost (2026-09-19, 2h 10m, $55.02, nothing integrated) and `addopts` excludes the marker, so a records-scanning test could not catch the next deletion anyway.
- CITE CODE BY SYMBOL OR QUOTED CONTENT, NOT BY A BARE LINE OFFSET (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This matters acutely for this plan, whose whole subject is citations that expired: `t0ovw6` measured both of its item's line offsets landing in unrelated code after a roughly four-thousand-line drift.
- THE SHARED CHECKOUT RULE DECIDES THE MUTATION METHOD. `t0ovw6`'s review established that mutating a tracked file and restoring it with `git checkout` after a suite run discards a co-worker's concurrent edits, and demonstrated the in-memory plugin form instead. E-05 adopts that rule rather than re-deriving it.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE AUDIT HAS NEVER BEEN DONE, AND THE HAND-SAMPLING IT REPLACES HAS ALREADY FOUND ELEVEN INSTANCES**, which is what establishes the population is real rather than speculative. Live or graduated items naming a trim-deleted test as a lost or falsely-cited guard: `pn7rw3`, `rcp8c4`, `gia5i7`, `ikxtkj`, `tvv8gg`, `l8upzx`, `p7k57l`, `rdl9lh`, `089bq4`, `2jz47s`, plus `nzqj6m` which asks for a sweep of one spec's criteria. Each was found incidentally by whoever was editing nearby, which is precisely the non-reproducible mode this plan ends. | `grep -rliE "dangling.*test\|cites a deleted" .aw/records/backlog/` over `open/`, `graduated/`, `blocked/`; each item's `- Summary:` read in place. |
| F-02 | **THE TRIM WAS TWO COMMITS, NOT ONE, AND THE ITEM NAMES ONLY THE SECOND.** `80db6750c` ("test: delete 366 tests that pinned code structure instead of behaviour", 2026-09-23) precedes `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) by one day. This is not pedantry: the two commits had OPPOSITE intents, so a loss attributable to the first is a deliberate P16 retirement that must NOT be restored, while a loss attributable to the second may be a genuine gap. An audit scanning only `19313eed` would misattribute every first-commit loss. | `git log -1 --format="%H %ad %s" 80db6750c`; `git show --stat` on both. |
| F-03 | THE TWO COMMITS HAVE STRUCTURALLY DIFFERENT SHAPES, which dictates that the scanner must read modified files and not only deleted ones. Measured by multiset difference of test-function names per file: `80db6750c` deleted **0** files, modified **112**, removed **366** test functions; `19313eed` deleted **298** files, modified **20**, removed **7,402**. So a `--diff-filter=D`-only scanner sees literally nothing of the first commit. The item's "roughly 7,000" figure is accurate for the second commit. | AST multiset-difference probe over `<commit>^:<path>` versus `<commit>:<path>` for every deleted and modified `tests/*.py` in each commit; `git diff --diff-filter=D/M --name-only` counts. |
| F-04 | THE CODE-PIN POPULATION IS MEASURABLE BUT THE CLASSIFIER IS A FLOOR, NOT A TOTAL, and saying so is what keeps the report honest. Scanning `19313eed`'s removed test bodies for `inspect.getsource`, `ast.parse`, `ast.walk`, `ast.unparse`, `getsourcelines` or `linecache` classifies **54** of 5,990 as code pins across 26 files, leaving 5,936 nominally behavioral. That 54 cannot be the true total, because the ENTIRE 366 of `80db6750c` were deleted for being code pins, so the signal set under-detects; the classifier is therefore specified as a cheap pre-filter whose misses the human triage step catches. | AST probe classifying each removed `test*` function by source-segment signal; the counts above; `80db6750c`'s own commit subject. |
| F-05 | **THE MOST-CITED MISSING GUARD IN THE TREE IS A CODE PIN, WAS DELETED BY THE FIRST COMMIT, AND IS CITED AS LIVING IN A FILE THE SECOND COMMIT DELETED - so a plausible audit gets BOTH facts wrong.** `runner_shared.py` cites `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared` at six sites (8 across siblings) as its live guard. Measured: the function's body is `ast.parse(Path(rs.__file__).read_text(...))` walking module-level `agent_workflows` imports, i.e. precisely the "no production source inspection" and "no architectural placement pins" shapes P16 prohibits; it was removed by `80db6750c`, NOT `19313eed`; and the file it is cited in was separately deleted by `19313eed`. The correct remedy is to record the pin as RETIRED, never to restore it. | `git log --all --oneline -S"def test_no_new_module_level_first_party_import_in_runner_shared"` returning `80db6750c` and `b816200c7`; `git show 80db6750c -- tests/test_orchestrator_probe_cache.py` with the deleted body read in full; `rg -c` giving 6 in `runner_shared.py`; `git show 19313eed^:tests/test_term.py` confirming the only other mention is itself a citation, not a definition. |
| F-06 | **PER-CANDIDATE MUTATION OVER THE FULL POPULATION IS NOT AFFORDABLE, WHICH IS WHY E-05 IS BOUNDED TO FIVE.** A bare suite run here is `203.41s` wall (`1 failed, 3457 passed, 2 skipped` - see F-11). At one suite run per candidate that is about **2.6 hours** for the 46 unowned shipped-source candidates and over **6 hours** for all 107. The item's instruction to prefer mutation is therefore adopted for a shortlist and explicitly declined for the tail, with the tail reported as `triaged-not-mutated` rather than silently dropped. | `time python3 -m pytest` on the clean lane tree; arithmetic over the F-10 candidate counts. |
| F-07 | AXIS A IS MEASURABLE TODAY AND ITS ATTRIBUTION IS NOT UNIFORM, which is why the scanner reports a "neither" bucket. Of `tests/test_*.py` paths cited in live non-record files, **166** distinct are cited and **107** do not exist, across **290** hits in **68** files. Attribution: **85** deleted by `19313eed`, **0** by `80db6750c`, and **22** by NEITHER, so roughly a fifth of the dangling citations are not the trim's doing at all and would be misattributed by an audit that assumed otherwise. | `rg -o "tests/[A-Za-z0-9_/]+\.py"` over `agent_workflows/`, `tests/`, `docs/`, `tools/`, `.github/` and the five root prose docs, each hit tested with `os.path.exists`, then set-intersected with each commit's deleted set. |
| F-08 | AXIS B FINDS A CLASS AXIS A IS STRUCTURALLY BLIND TO, so both are needed. Of `::Symbol` test-symbol citations in live non-record files, **85** distinct are cited and **59** resolve to no live test class or function, across **98** hits in **23** files, led by `::NoRunnerImportTests` (8) and `::test_no_new_module_level_first_party_import_in_runner_shared` (6). A citation can name a file that still EXISTS while the class inside it is gone, which is exactly how `gia5i7` was found. | `rg -o "::[A-Za-z_][A-Za-z0-9_]*"` over the same roots, resolved against the set of all live `ClassDef`/`FunctionDef` names parsed from `tests/`. |
| F-09 | **THREE FALSE-POSITIVE CLASSES ARE REAL AND ONE IS NON-OBVIOUS**, so excluding them is a correctness requirement rather than tidiness. `tests/test_x.py` and `tests/test_extra.py` each appear twice and MUST NOT resolve: they are illustrative placeholders inside `ipd_schema.py`'s comment "Exclude single test file assertion breakdowns (e.g. 'Add tests/test_x.py: ...')", `ipd_lifecycle.py`'s two `disregarded_unowned_paths: ['tests/test_extra.py']` docstring examples, and `run_evidence.py`'s "e.g. a fresh tests/test_x.py under a new dir". The other two classes are `.aw/records/` (immutable history) and `tmp_path` fixture paths. | `rg -n "tests/test_x.py\|tests/test_extra.py" agent_workflows/ tools/` with each hit read in context. |
| F-10 | **MOST OF THE CENSUS IS ALREADY OWNED, WHICH IS THE FINDING THAT SIZES THIS PLAN'S REAL WORK AND PREVENTS IT RE-FILING ELEVEN ITEMS.** Of the 85 trim-attributable dangling paths, **28** are already named by a live backlog item and **57** are not. Narrowing to citations from SHIPPED SOURCE (`agent_workflows/` or `tools/`): **69** dangle, of which **46** are unowned. The unowned set is concentrated, not flat: `tests/test_orchestrator_probe_cache.py` 12 citations, `tests/test_runner_item_dependencies.py` 10, `tests/test_review_findings_cascade.py` 4. Shipped-source carriers are led by `runner_shared.py` (111 hits), `agy_runipd.py` (69), `oc_runipd.py` (54), `ipd_lifecycle.py` (37). | Cross-product of the F-07 dangling set against the full text of every item under `.aw/records/backlog/{open,graduated,blocked}/`, matching on basename; per-file hit counts from the same scan. |
| F-11 | THE LANE TREE IS CLEAN BUT THE SUITE IS NOT FULLY GREEN, and the one failure is NOT this plan's and must not be attributed to it. Bare `python3 -m pytest` gives `1 failed, 3457 passed, 2 skipped, 3 warnings in 203.41s`, failing at `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`. It is a DATE-ROLLOVER flake independent of this plan: the assertion diff is `- 2026-09-30 HIST_ACTOR: exempted reason` versus `+ 2026-10-01 HIST_ACTOR`, i.e. a fixture expecting today's date while the code computed tomorrow's. `git status --short` is empty, and this plan touches no backlog code. An executor must take its own baseline and expect this node red for the same reason or fixed upstream. | `time python3 -m pytest` summary line; the narrowed `-o addopts=""` run with the date diff quoted; `git status --short` empty. |
| F-12 | THE `docs/` AXIS IS ALREADY OWNED INCLUDING ITS GUARD TEST, so this plan must not build a second one. Pending plan `1jg2m2` (Set `ikxtkj`, `- Status: reviewed`) declares `tests/test_docs_test_citations.py` in its `- Scope-Paths:` and its E-08 adds exactly the existence test P16 sanctions, bound to an enumerated published-prose list. That file does not exist yet at this HEAD, so the two plans would collide if this one also scanned `docs/`. This plan therefore reports `docs/` hits for completeness but declares no `docs/` path and adds no docs guard. | `ls tests/test_docs_test_citations.py` -> No such file; `1jg2m2`'s `- Scope-Paths:` line and its E-08 text read in place. |
| F-13 | THE COMMITTED-SCANNER PRECEDENT IS LIVE AND ITS SIBLING SHOWS THE FAILURE MODE TO AVOID. `tools/runner_fork_scan.py` ships with the reproducibility contract quoted in Step 0. Its sibling `tools/lift_drift_scan.py` still ships, but its test file `tests/test_lift_drift_scan.py` is now an EMPTY RETIRED STUB (`collected 0 items`, class body `pass`, docstring "Retired under IPD 96xtmi (source-guard cleanup). The AST drift scans pinning runner_shared.py source were deleted in favor of behavioral tests"). So the precedent for a committed scanner is good, and the precedent for its test is a cautionary one: E-06 must assert on scanner BEHAVIOR over fixtures, which is what survives a P16 cleanup, rather than on source structure, which does not. | `python3 -m pytest tests/test_lift_drift_scan.py -o addopts=""` -> `no tests ran`; the stub file read in full; `runner_fork_scan.py`'s header read. |

## Proposed changes (ordered, validatable)

1. Add `tools/lost_guard_census.py` computing removed-test-function census over BOTH trim commits, reading deleted AND modified files, reporting a labelled metric (E-01, per F-02/F-03).
2. Add the code-pin classifier that excludes P16-forbidden candidates by construction and declares itself a floor rather than a total (E-02, per F-04/F-05).
3. Add axes A and B with their three measured false-positive exclusions and a per-commit attribution including a "neither" bucket (E-03, per F-07/F-08/F-09).
4. Add the dedupe pass against live backlog items, defaulting the triage view to shipped-source citations (E-04, per F-10).
5. Mutation-prove a shortlist of at most five candidates in memory, reporting the tail as `triaged-not-mutated` with the cost reason (E-05, per F-06).
6. Add `tests/test_lost_guard_census.py` driving the scanner over synthesized fixtures with a bidirectional classifier pair and no `livecorpus` marker (E-06, per F-13).
7. File one backlog item per genuine unowned behavioral gap plus one for the misattributed retired-pin citations, with justified work-kinds (E-07, per F-05/F-10).

## Deferred / out of scope (with reason)

- RESTORING ANY DELETED TEST, which is forbidden for code pins and merely out of scope for the rest. The maintainer ruling in this item's own history is absolute for the code-pinning class ("must never propose restoring them"), and E-02 enforces it mechanically. For genuinely behavioral gaps, restoration is a test-authoring deliverable per gap, which is why the item asks for "a triage list, not necessarily a fix".
  - Carrier-Declined: The behavioral half of this IS a real obligation and it DOES need a carrier, which is exactly why E-07 files one per gap; it is declined HERE rather than left unowned. A carrier id6 cannot be cited at authoring time because the items do not exist yet, and V-07 refuses to pass without the pasted `aw backlog new` output, so the obligation cannot vanish silently at `executed`. The code-pinning half is a genuine won't-fix (P16 and the maintainer ruling both forbid the shape), so nothing is owed there.
- THE `docs/` CITATION AXIS AND ITS GUARD TEST: out of scope because pending plan `1jg2m2` already owns both, including the `tests/test_docs_test_citations.py` file it declares (F-12). Building a second docs guard would collide with a reviewed plan.
  - Carrier: 1jg2m2
- THE 22 DANGLING CITATIONS ATTRIBUTABLE TO NEITHER TRIM COMMIT: reported but not triaged here (F-07). They are real rot, but this item's subject is the trim, and their causes are separate deletions each needing its own history question.
  - Carrier-Declined: Declined HERE rather than unowned, for the same authoring-order reason as the row above: E-07 files these 22 as one triage item where no live item already names them, and a carrier id6 cannot be cited before that item exists. V-07 refuses without the pasted creation output, and the census prints them in a labelled section regardless, so they are visible rather than lost.
- THE 28 ALREADY-OWNED INSTANCES: deliberately not re-filed (F-10). Re-filing would create duplicate items for work already tracked by `pn7rw3`, `rcp8c4`, `gia5i7`, `ikxtkj`, `tvv8gg`, `l8upzx`, `p7k57l`, `rdl9lh`, `089bq4` and `2jz47s`.
  - Carrier-Declined: Each instance already has a live carrier by id6, so naming another would duplicate an existing obligation rather than track an untracked one.
- MUTATION-PROVING THE FULL CANDIDATE POPULATION: declined on a measured cost basis (F-06), not on principle. The tail is reported as `triaged-not-mutated` with its reason, so the partial is explicit.
  - Carrier-Declined: No separate carrier is owed, because the obligation travels WITH the items E-07 files: each filed gap names its own candidate, and mutation-proving it when it is taken up is strictly cheaper than proving all 46 up front merely to decide what to file. What is declined is a carrier for the UNPROVEN TAIL as a unit, which would duplicate the per-item obligations E-07 already creates.
- A `check` RULE OR PRE-COMMIT HOOK enforcing that no shipped comment cites a nonexistent test: deliberately not built here. It is an attractive follow-on and `ikxtkj` records the same idea for `docs/`, but it is a policy addition with repo-wide blast radius (69 shipped-source citations dangle today, so it would start red), and it must not land before the census establishes what the true clean state is.
  - Carrier-Declined: Declined HERE rather than unowned: E-07 files this as a follow-on item recording the 69-citation starting state, and its id6 cannot be cited at authoring time. V-07 refuses without the pasted creation output, so the option is tracked rather than forgotten.

## Scope check

- Over-scope: none. `tools/lost_guard_census.py` is the new scanner (E-01 through E-05); `tests/test_lost_guard_census.py` is its behavioral test (E-06); `tools/README.md` gains the scanner's entry alongside its `runner_fork_scan.py` precedent. NO production module under `agent_workflows/` is touched, NO deleted test is restored, NO existing test is edited or weakened, and NO shipped behavior changes, which is what keeps this a `chore`. No spec is touched (see spec sync). E-07 writes backlog items through `aw backlog new`, whose output path is tool-chosen under `.aw/records/backlog/open/`; that is a records artifact created by the sanctioned verb rather than a hand edit, so it is deliberately not declared as a code scope path, following the same reasoning `1jg2m2`'s scope check records for its own E-07.
- Under-scope: the declared paths cover every edit, and four gaps are recorded as decisions above rather than closed here. (1) No deleted test is restored; each behavioral gap leaves as a filed item. (2) The `docs/` axis stays with `1jg2m2`. (3) The 22 non-trim danglers are reported, not triaged. (4) The tail beyond E-05's five is `triaged-not-mutated`. The deliverable is therefore a REPRODUCIBLE CENSUS plus FILED ITEMS, and a reviewer should judge it on whether the census re-derives and whether the filed items are real, not on how many guards were restored.

## Required tests / validation

All validation runs BARE (`python3 -m pytest`), per the execution contract and the `addopts` already configured in `pyproject.toml`.

BASELINE, RE-MEASURED ON THIS LANE AT HEAD `ffb8e9e45` (F-11): `1 failed, 3457 passed, 2 skipped, 3 warnings in 203.41s`. THE TREE IS NOT FULLY GREEN and the one failure is a pre-existing date-rollover flake in `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, unrelated to this plan's paths. Take your own before-baseline, since the tree moves and that node may be fixed upstream; the bar is NO NEW failure, and the pre-existing one must be identified as such rather than inherited silently.

1. CENSUS REPRODUCTION: `python3 tools/lost_guard_census.py --summary` reproduces F-03 exactly for both commits (`80db6750c`: 0 deleted, 112 modified, 366 removed; `19313eed`: 298, 20, 7402). Paste the output. A figure that does not reproduce means the scanner is not the measurement this plan made, and the discrepancy must be explained before proceeding.
2. AXIS REPRODUCTION: `--axis a` and `--axis b` reproduce F-07 (107 dangling of 166 cited, 290 hits, 68 files; 85/0/22 attribution) and F-08 (59 of 85, 98 hits, 23 files). Paste both. Small drift is EXPECTED if the tree moved; state the delta and account for it by commit rather than editing the finding.
3. CLASSIFIER CORRECTNESS, both directions: the F-05 case classifies as a CODE PIN and is absent from triage output; a behavioral fixture classifies as BEHAVIORAL. Paste both verdicts. A one-sided classifier that answers "code pin" to everything would empty the triage list while appearing to work, so the negative direction is the one that matters.
4. DEDUPE CORRECTNESS: the owned/unowned split reproduces F-10 (28/57 all paths, 23/46 shipped-source) and every `owned` row names a real live item id6. Paste the split and spot-check three rows against the named items.
5. MUTATION EVIDENCE: for each of the at most five shortlisted candidates, paste the ACTUAL pytest summary line under the in-memory mutation and the verdict, plus `git status --short` empty before and after. A candidate whose mutation leaves the suite green is `unguarded`; one that reddens a surviving test is `guarded` and must NOT be filed.
6. TARGETED: `python3 -m pytest tests/test_lost_guard_census.py -o addopts=""` passes, with the per-test count stated.
7. FULL BARE SUITE: `python3 -m pytest` shows NO new failure versus the executor's own baseline, with the pre-existing `test_release_exempt_setter_roundtrip_and_parity` node identified if still red, and the count increased by exactly the number of tests E-06 adds.
8. FILED ITEMS: paste the real `aw backlog new` output for every item E-07 creates, each with its id6, work-kind and justification, and any `- Blocks-Release:` gate where filed as `bug`. Then `aw check` reports no new drift.
9. `aw ipd lint --phase pre-transition` conforms.

METHOD RULE FOR THE MUTATION PROOFS: mutate IN MEMORY, never by editing a tracked file. Use a pytest plugin patching the subject in `pytest_configure` and restoring it in `pytest_unconfigure`, or `mock.patch.object`. The reason is measured rather than stylistic: a `git checkout` restore after a 203-second suite run discards whatever a co-worker wrote to that file in the interval, which is the loss AGENTS.md's shared-checkout rule exists to prevent, and `t0ovw6`'s review established the in-memory form for exactly this case. Paste `git status --short` empty before and after each run.

## Spec / documentation sync

N/A with reason, for the SPEC half only. No spec governs the suite-trim census or either citation axis: the governing rule is `GUIDING_PRINCIPLES.md` Section 16 (P16), which is a principles document rather than a `.spec.md` artifact, and it already contains both the prohibition E-02 enforces and the "one narrow exception" sanctioning axes A and B, so nothing in it needs amending. `- Scope-Paths:` therefore declares no `.spec.md` file, and the runners' declared-spec-edit announcement should report none.

DOCUMENTATION IS NOT N/A: `tools/README.md` is declared and must gain the scanner's entry beside its `runner_fork_scan.py` precedent, because a committed scanner nobody can find is not reproducible in practice. Keep that entry free of em and en dashes, since `tools/README.md` is user-facing prose.

## Open questions

### OQ-01: Should the census also cover test files deleted by commits OTHER than the two trim commits, given that 22 of the 107 dangling citations are attributable to neither?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: REPORT THEM, TRIAGE THEM SEPARATELY. The scanner already computes them for free, because axes A and B test existence rather than attribution, so suppressing them would discard measured information and would also let a reader mistake the trim-attributed subset for the whole of the repository's citation rot. But triaging them HERE would widen this plan from "what did the trim break" to "every stale test citation in the tree", and their causes are 22 separate deletion events each needing its own history question. The split follows the precedent `1jg2m2` set for the append-only history files it reports but excludes. Not blocking: the scanner's behavior is identical either way, and the only thing the answer changes is which labelled section a row prints under.

### OQ-02: When the census finds an unowned gap whose property is genuinely behavioral, should this plan's executor file it as `chore` or as `bug` with a release gate?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE REPOSITORY'S OWN STATED TEST, PER CANDIDATE, WITH THE MUTATION VERDICT DECIDING. AGENTS.md's gating rule keys on USER-PERCEPTIBLE IMPACT, and the absence of a test is not by itself something a user can notice, so `chore` is the correct default and most rows will take it. The exception is sharp and is exactly what E-05's mutation proof produces: when a mutation shows WRONG USER-VISIBLE BEHAVIOR passing a full suite, the defect is the live behavior rather than the missing test, and this repository has already ruled that class a `bug` that MUST carry `- Blocks-Release:` while live. The precedent is in-tree and on this exact defect class: `39jkux` shipped a wrong `-vv` help string to operators and was filed as a live bug, while `pn7rw3` and `rcp8c4`, whose computed behavior is correct and whose cost falls on an editor, are both `chore`. E-07 therefore requires the executor to STATE and JUSTIFY each kind against the mutation verdict rather than defaulting silently. Not blocking: re-classifying a filed item is one `aw backlog set` call, and no item's existence depends on the answer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 tools/lost_guard_census.py --summary` output showing, per trim commit, deleted-file count, modified-file count and net test functions removed, matching F-03 exactly (`80db6750c`: 0/112/366; `19313eed`: 298/20/7402). Plus a pasted run passing a DIFFERENT commit argument, proving the commits are parameters and not hardcoded. Plus the report line naming which metric the headline count is.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted scanner output showing the code-pin count for `19313eed` matching F-04's 54; pasted classification of `test_no_new_module_level_first_party_import_in_runner_shared` as a CODE PIN together with proof it is ABSENT from the triage list; and the pasted report text carrying the floor-not-total caveat with `80db6750c`'s 366 as its stated reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `--axis a` output matching F-07 (107 dangling of 166 cited, 290 hits, 68 files, attribution 85/0/22) and `--axis b` matching F-08 (59 of 85, 98 hits, 23 files), with any drift from the moved tree stated and accounted for by commit rather than by editing the finding. Plus pasted proof that `tests/test_x.py` and `tests/test_extra.py` are absent from the output and that `.aw/records/` was not scanned.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted owned/unowned split matching F-10 (28/57 all paths; 23/46 shipped-source), plus three `owned` rows spot-checked against the live backlog items they name, each named item's path and `- Status:` pasted to prove it is live.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: for each shortlisted candidate (at most five), the ACTUAL pasted pytest summary line under the in-memory mutation, the recorded `guarded`/`unguarded` verdict, and `git status --short` empty pasted before and after. Plus the pasted `triaged-not-mutated` list for the remainder with F-06's measured suite time as the stated reason. A claimed verdict with no pasted summary line fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `python3 -m pytest tests/test_lost_guard_census.py -o addopts=""` showing passes with the count; pasted assertions proving BOTH classifier directions are covered (a code-pin fixture and a behavioral fixture); pasted confirmation the file carries no `livecorpus` marker and reads nothing under `.aw/records/`; and a pasted bare-suite line showing the node is selected by the default run.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted real `aw backlog new` output for every filed item, each with its id6, `- Work-Kind:` and the justification tied to its mutation verdict, plus `- Blocks-Release:` where filed as `bug`; pasted evidence that zero items were filed for a code-pin candidate or for an already-owned instance; and pasted `aw check` showing no new drift. Each filed id6 must also be recorded in this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the declared paths, through `aw commit <plan> -- <paths>`, never `git add -A` or `-a`, and never push. Run the suite BARE (`python3 -m pytest`) and paste ACTUAL output for every claim; a pasted summary line is required wherever a V-item asks for one, and a claimed pass without it fails that item.

THIS PLAN'S CENTRAL RISK IS A REASSURING EMPTY REPORT, so weigh it before approving. A classifier that over-detects code pins, or a dedupe that over-matches owned items, produces a census that runs clean and files nothing while 46 unowned shipped-source candidates remain. That is worse than no audit, because it would retire the question. V-02 and V-06 exist to make it visible: the classifier must be proven in BOTH directions, and the dedupe's owned rows must be spot-checked against real live items.

TWO REFUSALS ARE ABSOLUTE AND ARE NOT THE EXECUTOR'S TO RELAX. First, no deleted code-pinning test may be restored or proposed for restoration, per the maintainer ruling carried in this item's own workflow history and `GUIDING_PRINCIPLES.md` P16; when a citation names a retired pin, the fix is to record the retirement (F-05). Second, mutation proofs are staged IN MEMORY, never by editing a tracked file in this shared checkout.

THE SHARED CHECKOUT IS LIVE. Other agents may be working here concurrently. Before each commit verify the staged set with `git diff --cached --name-only` and unstage anything you did not change with `git restore --staged <path>`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms AND every `V-*` item above carries concrete pasted evidence. The runner sets the backlog item to `graduated`; do not set it `done`.
