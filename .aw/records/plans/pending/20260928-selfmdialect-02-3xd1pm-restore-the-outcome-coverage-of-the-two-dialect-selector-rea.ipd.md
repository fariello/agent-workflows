# IPD: Restore the outcome coverage of the two-dialect selector readers that the suite trim deleted

- Date: 2026-09-28
- Kind: child
- Concern: The two-dialect selector readers (`selectors._read_id`/`_read_status`/`_read_setid`, region-bounded by plan `76w6mq` and taught the YAML dialect by plan `xo3244`) are CORRECT in the code and PARTLY UNGUARDED in the suite, because commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted BOTH files that pinned them: `tests/test_id_metadata_region.py` (471 lines) and `tests/test_selector_zero_open.py` (1108 lines), which between them held the `ResearchResolvesByYamlFrontMatterTests`, `YamlFallbackIsCaseSensitiveTests`, `YamlScalarNormalizationTests` and `BoundedReaderTests` classes named in `xo3244`'s and `76w6mq`'s Scope-Paths. MEASURED BY MUTATION at HEAD `7db2d3ce` against a bare-suite baseline of `3246 passed, 2 skipped`, FOUR behavioral properties are now GREEN UNDER MUTATION, meaning the suite does not notice when they break: reverting the metadata-region bound entirely (which reinstates `76w6mq`'s original defect and restores a live `uyeko5` id6 collision across three records) passes `3246 passed, 2 skipped`; removing the YAML `id:` fallback alone passes `3246 passed, 2 skipped`; making the YAML key lookup CASE-TOLERANT (the property `xo3244` calls "THE LOAD-BEARING SAFETY PROPERTY OF THIS CHANGE") passes `3246 passed, 2 skipped`; and dropping YAML scalar normalization passes `3246 passed, 2 skipped`. Only `status` and `setid` are still guarded, and only incidentally, by `tests/test_research_archive.py` and `tests/test_cli_find.py`.
- Scope: IN: ONE new test file, `tests/test_selector_two_dialect_readers.py`, restoring OUTCOME coverage for the four measured-unguarded properties plus the two measured-guarded ones (so the file is a complete statement of the readers' contract rather than a patch over today's holes), each test proven non-vacuous by the RED-under-mutation measurement recorded in Findings. Every test drives `selectors.resolve`/`resolve_for_mutation`/the three readers on FIXTURE records in a temp repo and asserts observable answers (match KIND, matched paths, refusal text). OUT, and deliberately: any edit to `agent_workflows/selectors.py` (this plan asserts existing behavior and must not change it); restoring the two deleted files verbatim (they carry code-structure pins that `GUIDING_PRINCIPLES.md` P16 now prohibits, enumerated in Findings as X1..X4, and re-adding them would reintroduce exactly what plan `b02ohu` is removing); the two properties measured as genuinely unobservable (M3 bullet-first ordering, M4 the fence pre-filter), which are named in Deferred with the measurement that retired them rather than left implied; and the general audit of `19313eed`, which is backlog `xvp5vx`.
- Scope-Paths: tests/test_selector_two_dialect_readers.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: 7qvj1c
- Set: selfmdialect
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 3xd1pm

## Workflow history
- 2026-09-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-201 through PR-205 all fixed; full mutation census reproduced

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201 through PR-204, all FIXED. Reviewed at `86fafc93` in a lane worktree. Structural preflight conformed before and after revision.
  THE ENTIRE MUTATION CENSUS WAS REPRODUCED INDEPENDENTLY RATHER THAN TRUSTED, because every item in this plan is justified by it and a stale census would have justified the wrong tests. All six consequential mutations gave the plan's exact figures at this head: M5, M1a, M2 and M6 each `3246 passed, 2 skipped` (unguarded, as claimed); M1b `5 failed, 3241 passed`; M1c `3 failed, 3243 passed`, with the incidental failures in exactly the named `tests/test_cli_find.py` and `tests/test_research_archive.py` classes. The live-tree collision claim reproduced to the file: 0 collisions clean, and under M5 exactly one, `uyeko5`, across the three named records. F-1's corpus figures (130 / 123 / 123 / 116), E-05's trap premise (0 research records declare an id6 absent from their filename) and E-04's correction of `xo3244` (0 tracked fenced non-research records) all reproduced unchanged. `agent_workflows/selectors.py` is byte-identical to HEAD; `git diff --stat` on it is empty.
  THE ONE FINDING THAT WOULD HAVE COST AN EXECUTION CYCLE IS AN API SHAPE ERROR. `selectors.resolve_for_mutation` returns a 2-tuple `(paths, error_message)`, not a result object, so E-05's "`resolve_for_mutation` succeeds with `n=1`" written beside a `resolve` call describing `.kind`/`.paths` reads as the wrong shape; review hit `AttributeError: 'tuple' object has no attribute 'paths'` while reproducing that fixture. E-05 and V-05 now spell out the unpacking, and add that the refusal must be matched on a SUBSTRING because it interpolates per-run absolute tempdir paths.
  ONE CITATION IN THE PRODUCTION CODE IS DEAD, which upgrades half of E-06 from a precaution to a restoration: `_normalize_yaml_scalar`'s docstring names `tests/test_cli_find.py::BacktickSetValueIsPinnedTests` as the pin keeping normalization off the bullet dialect, and that class exists nowhere under `tests/` because `19313eed` removed it in the same trim that deleted this plan's two ancestors. The asymmetry is unguarded on both sides today.
  TWO EVIDENCE PRECISION CORRECTIONS: all four P16-violating pins are in `test_selector_zero_open.py` alone, and three of the four restorable classes are too (only `BoundedReaderTests` is in the other file), where the Concern implies they are spread across both; and the deleted pair also contained a `LiveTreeTests` class asserting over this repository's own records tree, which is a third independent reason not to restore verbatim and corroborates the fixture-only choice.
  NO PRODUCTION FILE WAS LEFT MODIFIED. Every mutation was applied, measured with a full bare suite, and reverted with `git checkout --`; the working tree holds only this plan's own edit.
- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `7qvj1c`. THE ITEM'S OWN CLOSING CONDITION IS SATISFIED AND THE ITEM IS STILL LIVE, WHICH IS WHY THIS PLAN EXISTS AND WHY IT IS NOT THE PLAN THE ITEM ANTICIPATED. The item says "No action needed if xo3244 lands"; `xo3244` DID land (it is in `plans/executed/`, executed 2026-09-23) and the resolver gap it describes is genuinely CLOSED, re-verified at HEAD `7db2d3ce`: over all 130 tracked research `.md` files, `_read_id` now answers for 123, `_read_setid` for 123 and `_read_status` for 116 (the 7 misses are 6 `README.md`/template files carrying no front matter at all plus one legacy doc, and the 7 status misses are research-prompt records that legitimately declare no `status:`), `aw find research reference` returns 64 records where the item's era returned 5, and repository-wide id6 collisions computed through the live reader are 0. So NOTHING in the item's requested fix remains to do, and this plan does not redo it. WHAT I FOUND INSTEAD, and did not go looking for: both test files that `76w6mq` and `xo3244` declared in their Scope-Paths were deleted 2026-09-24 by the suite trim `19313eed`, so the landed fix is now partly unguarded. I measured that rather than inferring it, with seven mutations against a bare-suite baseline of `3246 passed, 2 skipped`; four came back GREEN (the region bound, the YAML `id:` fallback, the case-sensitive key lookup, and scalar normalization) and three came back RED or unobservable. Each of the four is then proven to be a REAL observable divergence by a fixture probe, not merely an uncovered line: the region-bound revert makes a document that QUOTES an example metadata block report the foreign `ffffff`/`approved`/`quotedset` instead of its own `aaaaaa`/`reference`/`realset`, and restores a live three-way `uyeko5` collision in this very repository; the id6 revert turns an exact one-file `kind=id6` answer into an ambiguous two-file `kind=substring` answer that makes a MUTATING verb refuse; the case-tolerant lookup makes a `Kind: session-handoff` draft newly match `aw find prompts draft`, the exact perturbation `xo3244`'s comment says the case-sensitivity exists to prevent; and dropping normalization makes a backticked `set:` value unreachable by its bare setid (`n=1` becomes `n=0`). TWO CORRECTIONS TO CLAIMS A FUTURE READER MIGHT INHERIT, both re-measured. FIRST, `xo3244`'s stated headline is stale in BOTH directions: the corpus has grown, so `aw find research reference` is 64 today, and the fenced NON-research population it measured as 2 is now 0 in a tracked isolated worktree (both `Kind: session-handoff` prompts live in the gitignored `records/prompts/untracked/` lane), which is precisely why E-04 must be a FIXTURE test and cannot be a corpus census. SECOND, the mutation harness itself had a defect that silently measured the WRONG TREE and would have produced a false "already covered" verdict: a probe script placed under `.aw/tmp/` gets its own directory as `sys.path[0]`, so `import agent_workflows` walked up to the MAIN checkout's unmutated package; my first three probe runs reported a mutated reader as still answering correctly. Every measurement in this plan was re-taken after inserting the workspace root ahead of `sys.path[0]`, and E-02 requires the executor to prove its harness is measuring the workspace copy before trusting a single green result.
- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the suite notice when the two-dialect selector readers break. Two executed plans fixed a defect that made a quoted example claim a real artifact's identity and made every research metadata query silently fall through to a filename match; the tests that proved both fixes are gone, so today the repository can regress to either defect with a fully green run and nothing to say so.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the harness and prove it measures the right code

- [ ] E-01 Create `tests/test_selector_two_dialect_readers.py` with a module docstring that states what the file guards, names the two executed plans whose contract it restates (`76w6mq` for the region bound, `xo3244` for the YAML dialect), and names commit `19313eed` as what deleted its two ancestors (`tests/test_id_metadata_region.py`, `tests/test_selector_zero_open.py`). Add the shared fixture helpers every later item uses: a `unittest.TestCase` base that builds a temp repo containing `.aw/records/<type>/` directories and writes fixture records into them, plus one helper that emits a YAML-fenced research record with caller-chosen `id`/`status`/`set` values and one that emits a bullet-front-matter plan. USE FIXTURES, NOT THE LIVE CORPUS, and that choice is load-bearing rather than stylistic: the `pyproject.toml` `livecorpus` marker records that a test asserting a property over this repository's own `.aw/records/` tree can be turned red by ANY agent writing a plan, and that one such test cost run `run-20260919T194413Z-2056285` 2h 10m and $55.02 with nothing integrated. A fixture test also survives the corpus shift that already invalidated `xo3244`'s own numbers.
  DO NOT ADD A `slow` MARKER. `pyproject.toml` defines `slow` as "heavy subprocess/integration tests (spawn the CLI, install into temp repos)"; this file spawns no subprocess and installs nothing, it only writes small files into a `tempfile.TemporaryDirectory` and calls library functions, so it belongs in the default fast subset where a regression is seen on every run. Marking it would exclude it from the default `python3 -m pytest` and defeat the purpose of restoring it.
  - Depends on: none
  - Expected outcome: the file exists, collects, and its fixture helpers can produce a YAML-fenced research record and a bullet plan in a temp repo; running the file alone reports only its own tests passing.
  - Execution state: pending

- [ ] E-02 Before writing any assertion, PROVE THE HARNESS MEASURES THE WORKSPACE COPY of `agent_workflows`, and record the proof in the plan. This item exists because the defect it guards against actually occurred while authoring: a probe script under `.aw/tmp/` reported a MUTATED reader as still answering correctly, because `sys.path[0]` is the script's own directory and `import agent_workflows` therefore resolved to the MAIN checkout's unmutated package (`.../agent-workflows/agent_workflows/selectors.py`) rather than the lane's (`.../worktrees/<lane>/agent_workflows/selectors.py`); three measurements were false before it was caught, and every one of them pointed at the wrong conclusion, namely "this property is already covered". Assert inside the test module that `Path(selectors.__file__)` is under the repository root that contains the test file itself, so a future harness run in any lane fails loudly instead of measuring a sibling checkout.
  - Depends on: E-01
  - Expected outcome: a test that fails if `agent_workflows.selectors` was imported from outside the checkout holding the test file, and pasted evidence naming the resolved `selectors.__file__` observed during execution.
  - Execution state: pending

### Task group 2: restore the four properties measured as UNGUARDED

- [ ] E-03 Pin the METADATA-REGION BOUND on all three readers (restores the property mutation M5 found green; `76w6mq`'s whole purpose). Write a fixture record that DECLARES one identity in its own front matter and QUOTES a DIFFERENT metadata block in its body (the shape of a document about `aw`'s own format, which is the trigger `76w6mq` names), then assert the three readers return the DECLARED values and never the quoted ones. MEASURED VALUES to assert, taken from the probe: for a record whose YAML fence declares `id: aaaaaa`, `status: reference`, `set: realset` and whose body quotes `- Id: ffffff`, `- Status: approved`, `- Set: quotedset`, the clean readers answer `aaaaaa`/`reference`/`realset` and the unbounded readers answer `ffffff`/`approved`/`quotedset`. Assert all THREE readers, not just `_read_id`: mutation M5 showed the bound is shared and a single-reader test would leave two thirds of it green under mutation.
  ALSO ASSERT THE COLLISION CONSEQUENCE, because that is the user-visible harm and the reader values alone understate it. Build a temp repo holding the genuine artifact plus a second record that quotes the first one's id6, and assert `resolve` returns the genuine one with `kind=id6` and `n=1`. Measured in the LIVE tree: with the bound, repository-wide id6 collisions through the reader are 0; without it, `uyeko5` collides across three records (its real plan plus the two research documents that quote its metadata block), which is the exact state whose refusal `76w6mq` records as "not overridable by --force".
  - Depends on: E-02
  - Expected outcome: three reader assertions plus one resolution assertion that all pass on HEAD and all fail when the `metadata_region(...)` call is removed from the three readers.
  - Execution state: pending

- [ ] E-04 Pin the CASE-SENSITIVE YAML key lookup (restores the property mutation M2 found green, which `selectors.py`'s own comment calls "THE LOAD-BEARING SAFETY PROPERTY OF THIS CHANGE, NOT A STYLISTIC RESTRICTION"). Write a fixture prompt record in exactly the shape the `handoff` workflow emits, a `---` fence with CAPITALIZED keys (`Kind: session-handoff`, `Status: draft`, `Date:`), and assert BOTH halves of the property: that the three readers return None on it, and that `resolve(<repo>, "prompts", "draft")` therefore matches NOTHING. Assert the second half through `resolve`, not only through the readers: the reader answer is the mechanism but the user-visible claim is "a session-handoff draft does not start showing up in `aw find prompts draft`", and that is what `selectors.py`'s comment promises.
  THIS MUST BE A FIXTURE TEST AND MUST NOT BE A CORPUS CENSUS, for a measured reason that also corrects `xo3244`: that plan verified the property by counting fenced non-research records and found 2, but re-measured here the tracked count is 0, because both session-handoff prompts live in the gitignored `.aw/records/prompts/untracked/` lane and are absent from an isolated worktree. A census-shaped test would therefore pass vacuously in exactly the environment a runner executes in. ALSO assert the complementary half that keeps the test honest about WHY the readers miss: `research_contract.parse_frontmatter` DOES see those keys under their real capitalization (measured: it returns `{'Kind': 'session-handoff', 'Status': 'draft', 'Date': '2026-09-28'}`), so the miss is the case-sensitive LOOKUP and not a parse failure. Without that second assertion a future change that broke the parser outright would leave this test green.
  - Depends on: E-02
  - Expected outcome: a test asserting the readers return None on a capitalized-key fenced record, that `aw find prompts draft` matches 0 records, and that the parser nonetheless exposes the capitalized keys; it must fail when the key lookup is made case-tolerant.
  - Execution state: pending

- [ ] E-05 Pin the YAML `id:` FALLBACK as an OBSERVABLE answer (restores the property mutation M1a found green). THE OBVIOUS TEST DOES NOT WORK AND AN EXECUTOR MUST NOT WRITE IT: querying a research record by its own id6 passes WITH OR WITHOUT the fallback, because every conforming research filename EMBEDS its id6 (measured over all 130 tracked research files: zero declare an id6 absent from their own filename), so the `substring` rule reaches the same single file and the test is vacuous. Measured proof of the trap: `aw find research xecyn0 -p` returns the identical single path under both the clean and the mutated reader.
  WHAT TO ASSERT INSTEAD is the match KIND and its consequence for a MUTATING verb, using two records whose filenames BOTH conform to the research grammar and both contain the queried token: an owner named `...-01-tgt001-primary-notes.research-report.md` that declares `id: tgt001`, and a sibling named `...-02-sib001-reconciles-tgt001-findings.research-report.md` that declares `id: sib001` but cites the owner's id6 in its SLUG (an ordinary habit in this corpus, e.g. a reconciliation document named for what it reconciles). MEASURED: with the fallback, `resolve` gives `kind=id6`, `n=1`, the owner, and `resolve_for_mutation` succeeds; without it, `resolve` gives `kind=substring`, `n=2`, and `resolve_for_mutation` REFUSES with "selector 'tgt001' is ambiguous (substring) matching multiple files; pass --force to act on all:" followed by both absolute paths on their own indented lines. Assert the kind, the single path, that the winning kind is in `UNIQUE_KINDS`, and that the mutating resolution succeeds; the refusal is the harm and the kind is its cause.
  UNPACK `resolve_for_mutation` AS A 2-TUPLE, NOT AS A RESULT OBJECT. It returns `(paths, error_message)`: `error_message` is `None` on success and `paths` is `[]` on refusal. It has NO `.paths` attribute, so `res.paths` raises `AttributeError: 'tuple' object has no attribute 'paths'` (hit at review while probing this very fixture). Write `paths, err = selectors.resolve_for_mutation(...)` and assert `err is None` and `len(paths) == 1` on the clean side, `paths == []` and the refusal substring in `err` on the mutated side. MATCH THE REFUSAL LOOSELY, on a distinctive substring such as `is ambiguous (substring)`, because the full message interpolates ABSOLUTE tempdir paths that differ every run; an equality assertion on the whole string cannot pass twice.
  - Depends on: E-02
  - Expected outcome: a test that passes on HEAD and fails with an ambiguity refusal when the `_read_yaml_scalar(text, "id")` fallback is removed from `_read_id`.
  - Execution state: pending

- [ ] E-06 Pin YAML SCALAR NORMALIZATION (restores the property mutation M6 found green). Assert that a YAML `set:` value written with surrounding backticks and one written with a quote pair are both reachable by the BARE selector, and that a quoted `status:` is too. MEASURED: for fixture records declaring `set: `probeset``, `set: "quotedset"` and `status: 'reference'`, with normalization `_read_setid` answers `probeset`/`quotedset` and `_read_status` answers `reference`, and `resolve` finds each by its bare token (`kind=setid`, `n=1`; `kind=status`, `n=2`); without it the readers answer the backtick- and quote-bearing strings verbatim and the bare `probeset`/`quotedset` selectors match NOTHING (`kind=None`, `n=0`). Give the fixture filenames that contain NEITHER token, so only the front-matter value can produce the match and the test cannot pass by filename.
  ALSO ASSERT THE DELIBERATE ASYMMETRY, because normalization is correct ONLY on the YAML side and a future "consistency" edit would break a contract nothing currently guards: `selectors.py` records that the BULLET `_read_setid` returns a backticked value VERBATIM on purpose, since stripping it there flips a real query's winning KIND and SHRINKS the answer (4 substring hits become 1 setid hit). Assert that a BULLET record whose front matter reads `- Set: `bulletset`` still yields the backtick-bearing value (measured clean: `'`bulletset`'`, backticks intact), so this file states where normalization applies and where it must not.
  THE PIN `selectors.py` CITES FOR THAT ASYMMETRY IS GONE, which makes this half of E-06 a genuine restoration rather than a belt-and-braces addition. Both `_normalize_yaml_scalar`'s docstring and the deleted `YamlScalarNormalizationTests` name `tests/test_cli_find.py::BacktickSetValueIsPinnedTests` as the guard; measured at review, that class exists NOWHERE in `tests/` and `git log -S` shows `19313eed` removed it in the same trim that deleted this plan's two ancestors. So the asymmetry is currently unguarded on BOTH sides, and the code's own comment points at a test that is not there. Do NOT cite that class as existing coverage; assert the behavior instead.
  - Depends on: E-02
  - Expected outcome: tests asserting the bare selector reaches a backticked/quoted YAML value and that the bullet dialect is NOT normalized; the first fails when `_normalize_yaml_scalar` is bypassed, the second fails if normalization is extended to the bullet reader.
  - Execution state: pending

### Task group 3: keep the two incidentally-guarded properties guarded on purpose

- [ ] E-07 Pin the YAML `status:` and `set:` fallbacks DIRECTLY, so they stop depending on incidental coverage. These two are the only properties mutation found RED today, but neither is guarded by a test ABOUT them: removing the `status` fallback fails 5 tests in `tests/test_research_archive.py` and `tests/test_cli_find.py`, and removing the `setid` fallback fails 3 in `tests/test_research_archive.py`, all of which are archive/CLI tests that happen to route through the resolver. That is real coverage and this plan does not disturb it, but it is fragile in a specific way worth one cheap test each: a future change to `aw archive`'s own resolution path (backlog `mblu3p` records that `aw archive` currently BYPASSES this resolver for some verbs) could remove the incidental coverage without touching the reader, leaving these two properties as green under mutation as the other four are today. Assert, on fixture records, that a research record's `status:` and `set:` are reachable by their bare selectors with `kind=status`/`kind=setid`.
  - Depends on: E-02
  - Expected outcome: two tests asserting the `status` and `setid` YAML fallbacks by their own behavior, failing when each fallback is removed, and independent of `tests/test_research_archive.py`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `GUIDING_PRINCIPLES.md` Section 16 prohibits `inspect.getsource`, `ast.parse`, `read_text()` or regex against production code, count/census pins, docstring and banner pins, and architectural placement pins, and requires that a test be proven non-vacuous BY MUTATION ("A test is only valid if breaking the underlying behavior makes the test fail"). This plan is written to that standard: every item names the mutation that must turn it red, and the two deleted ancestor files are deliberately NOT restored verbatim because they contain pins of exactly the prohibited kinds (Findings X1..X4).
- A test that asserts a property over this repository's own `.aw/records/` tree is marked `livecorpus` and DESELECTED by default, for the measured reason in `pyproject.toml`: any agent writing a plan can turn it red, blocking integration for every concurrent lane. Hence fixture records in a temp repo throughout.
- `slow` is defined by KIND, not duration: "heavy subprocess/integration tests (spawn the CLI, install into temp repos)". This file is neither, so it stays unmarked and runs in the default fast subset.
- The suite is run BARE (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Do not add `-n0`, a second `-q` (which compounds into `-qq` and suppresses the `N passed` line this plan requires pasted), or `-p no:randomly`.
- Tests here are plain stdlib `unittest.TestCase`; pytest does NOT inject fixtures into them, so `monkeypatch` arrives as `None` (`tests/support.py`, `execution_role`). Use explicit context managers or `addCleanup`.
- `tests/support.py::execution_role` exists so a test DECLARES the execution role it exercises rather than inheriting `AW_EXECUTION_ROLE` from whatever launched pytest. This file does not drive `ipd_lifecycle.begin`/`finalize`, so it needs no role declaration; noted because a reviewer will reasonably ask.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE TWO RESOLUTION ENTRY POINTS HAVE DIFFERENT RETURN SHAPES, which is the one API detail most likely to cost an executor a wasted cycle. `selectors.resolve` returns a RESULT OBJECT with `.kind`, `.paths` and `.rejected_kind`; `selectors.resolve_for_mutation` returns a 2-TUPLE `(paths, error_message)`. Unpack the second; `.paths` on it raises `AttributeError`. See F-7.
- A REFUSAL MESSAGE INTERPOLATES ABSOLUTE PATHS, so assert on a distinctive substring of it and never on the whole string: a fixture in a `tempfile.TemporaryDirectory` produces a different path on every run.

## Findings

Baseline for every measurement below: bare `python3 -m pytest` at HEAD `7db2d3ce` in lane worktree `aw/lane/7qvj1c` gives `3246 passed, 2 skipped, 3 warnings in 54.86s` (plus the standing notice that 207 tests are deselected as `slow`/`livecorpus`). Each mutation was applied to `agent_workflows/selectors.py`, measured with a full bare suite, then reverted with `git checkout --`; the file is byte-identical to HEAD now.

INDEPENDENTLY REPRODUCED AT REVIEW, at HEAD `86fafc93`, which matters because the whole plan rests on this census and a stale census would justify the wrong tests. The baseline is UNCHANGED (`3246 passed, 2 skipped, 3 warnings`, 207 deselected), and every mutation re-run gave the plan's exact figure: M5 `3246 passed, 2 skipped`; M1a `3246 passed, 2 skipped`; M2 `3246 passed, 2 skipped`; M6 `3246 passed, 2 skipped`; M1b `5 failed, 3241 passed, 2 skipped` with the failures in `tests/test_cli_find.py::CliFindResearchStatusTests` and `tests/test_research_archive.py`; M1c `3 failed, 3243 passed, 2 skipped` with the failures in `tests/test_research_archive.py::BehavioralParityAndRefusalTests`. The live-tree collision claim also reproduced exactly: 0 collisions clean, and under M5 exactly one id6 collides, `uyeko5`, across the three named records (its plan plus `takpys` and `27rjro` under `research/reference/202609/`). `selectors.py` was restored with `git checkout --` after each and `git diff --stat` is empty. F-1's corpus figures reproduced unchanged too (130 tracked research `.md`; `_read_id` 123, `_read_setid` 123, `_read_status` 116), as did E-05's trap premise (0 research records declare an id6 absent from their own filename) and E-04's correction of `xo3244` (0 tracked fenced non-research records; the `prompts/untracked/` lane is absent in an isolated worktree).

### F-1 The backlog item's own fix is DONE; the gap is in the tests, not the code

| Claim in item `7qvj1c` | Re-measured at HEAD `7db2d3ce` | Verdict |
|---|---|---|
| all three readers return None for every research record | `_read_id` answers for 123 of 130 tracked research `.md`, `_read_setid` 123, `_read_status` 116 | NO LONGER TRUE; `xo3244` closed it |
| research id6/status/setid reachable ONLY by filename substring | `resolve` returns `kind=id6`/`kind=status`/`kind=setid` for research tokens | NO LONGER TRUE |
| 110 of 117 tracked research files are `---`fenced | 123 of 130 today (corpus grew) | TRUE, count moved |
| "No action needed if `xo3244` lands" | `xo3244` is in `plans/executed/`, executed 2026-09-23 | CONDITION MET |

The 7 non-answering research files are 6 `README.md`/template documents with no front matter plus one legacy `2026-07-12` report; the 7 status misses are `research-prompt` records that legitimately carry no `status:`. Neither is a defect.

### F-2 Mutation census: which properties the suite still notices

| # | Mutation applied to `selectors.py` | Full bare suite | Guarded? |
|---|---|---|---|
| M1 | remove the YAML fallback from ALL THREE readers (full `xo3244` revert) | `8 failed, 3238 passed, 2 skipped` | yes |
| M1a | remove the YAML fallback from `_read_id` ALONE | `3246 passed, 2 skipped` | **NO** |
| M1b | remove the YAML fallback from `_read_status` ALONE | `5 failed, 3241 passed, 2 skipped` | yes (incidental) |
| M1c | remove the YAML fallback from `_read_setid` ALONE | `3 failed, 3243 passed, 2 skipped` | yes (incidental) |
| M2 | make the YAML key lookup CASE-TOLERANT | `3246 passed, 2 skipped` | **NO** |
| M3 | consult the YAML dialect FIRST instead of on a bullet miss | `3246 passed, 2 skipped` | n/a, unobservable (F-5) |
| M4 | drop the `text.startswith("---")` fence pre-filter | `3246 passed, 2 skipped` | n/a, unobservable (F-5) |
| M5 | unbound all three readers from the metadata region (full `76w6mq` revert) | `3246 passed, 2 skipped` | **NO** |
| M6 | drop `_normalize_yaml_scalar` from the YAML path | `3246 passed, 2 skipped` | **NO** |
| M7 | teach the PUBLIC runner readers the YAML dialect | `3246 passed, 2 skipped` | **NO**, but see F-6 |

M1's 8 failures and M1b/M1c's are all in `tests/test_research_archive.py` and `tests/test_cli_find.py::CliFindResearchStatusTests`, i.e. archive/CLI tests routing through the resolver incidentally, not tests about the readers. That is why E-07 pins those two directly.

### F-3 Each unguarded property is a REAL observable divergence, not merely an uncovered line

Measured with fixture records in a temp repo (the probe harness described in E-02):

| Property | Clean behavior | Mutated behavior |
|---|---|---|
| region bound (M5) | readers answer the record's OWN `aaaaaa`/`reference`/`realset` | answer the QUOTED `ffffff`/`approved`/`quotedset` |
| region bound, live tree | 0 id6 collisions repository-wide through the reader | `uyeko5` collides across 3 records (its plan + 2 quoting research docs) |
| `id:` fallback (M1a) | `kind=id6`, `n=1`, mutating resolve succeeds | `kind=substring`, `n=2`, mutating resolve REFUSES as ambiguous |
| case sensitivity (M2) | `aw find prompts draft` matches 0 | matches the `Kind: session-handoff` draft (`kind=status`, `n=1`) |
| normalization (M6) | backticked/quoted `set:` reachable by bare token (`kind=setid`, `n=1`) | unreachable (`kind=None`, `n=0`) |

### F-4 The two deleted ancestors must NOT be restored verbatim (P16 conflict)

Recovered from `19313eed^`, both files carry pins that `GUIDING_PRINCIPLES.md` Section 16 now prohibits. Restoring them wholesale would reintroduce exactly the class plan `b02ohu` (Set `structpin`) is currently removing.

ALL FOUR PINS LIVE IN ONE OF THE TWO FILES, `tests/test_selector_zero_open.py` (1108 lines), which review confirmed by listing both files' classes at `19313eed^`. The Concern says the four restorable classes sit "between them"; in fact `ResearchResolvesByYamlFrontMatterTests`, `YamlFallbackIsCaseSensitiveTests` and `YamlScalarNormalizationTests` are ALL in `test_selector_zero_open.py`, and only `BoundedReaderTests` is in `test_id_metadata_region.py` (471 lines). This does not change the plan's shape, but an executor recovering prior art should look in the right file.

| # | Pin in the deleted file | Which file | P16 clause it violates |
|---|---|---|---|
| X1 | `PrecedenceUnchangedTests` asserts the literal `selectors._PRECEDENCE` tuple | `test_selector_zero_open.py` | count/census and structure pin (asserts a module constant's shape, not a behavior) |
| X2 | `YamlFallbackHeaderBoundTests` asserts `_HEADER_CHUNK_BYTES == 4096` | `test_selector_zero_open.py` | pins an implementation constant as a proxy for an invariant |
| X3 | `_RecordOpenCounter`-based zero-open tests assert the NUMBER of record files opened | `test_selector_zero_open.py` | explicit "no count or census pins" |
| X4 | `DialectDocumentationTests` asserts docstring phrases | `test_selector_zero_open.py` | explicit "no text, banner, or docstring pins" |

ALSO PRESENT IN THE DELETED PAIR, and worth naming so the executor does not re-derive it: `test_id_metadata_region.py::LiveTreeTests` asserted over this repository's own `.aw/records/` tree, which is exactly the shape `pyproject.toml`'s `livecorpus` marker now deselects by default for the measured integration-blocking reason. That is a THIRD reason not to restore verbatim, beside P16, and it corroborates this plan's fixture-only choice.

The BEHAVIORAL content of the deleted files is what this plan restores, re-expressed as outcome assertions: `X2`'s real invariant (a fence inside the read window is read, a straddling one reads as absent rather than as a wrong value) is preserved in spirit by E-03..E-07 driving `resolve` on real fixture files rather than asserting the constant.

### F-5 Two properties are genuinely unobservable and are NOT worth a test

Recorded so a reviewer does not read their green mutation as a coverage hole. M3 (YAML-first instead of bullet-first) changed NO answer in any probe, and the reason is structural rather than luck: the region bound means a YAML-fenced document's bullet pattern always misses, and a bullet document has no leading fence for the YAML reader to parse, so the two dialects are disjoint on every real record and the ORDER between them is unobservable. M4 (dropping the fence pre-filter) likewise changed no answer, because `research_contract.parse_frontmatter` returns None for any text lacking a leading `---` fence (measured: None for both a bullet plan and a heading-first document), making the pre-filter a pure performance guard. Neither is tested here; a test asserting an unobservable difference could only be written by pinning code.

### F-7 `resolve_for_mutation` RETURNS A 2-TUPLE, and E-05 as authored described a result object

Added at review after hitting it while reproducing the E-05 fixture. `selectors.resolve_for_mutation`
returns `(paths, error_message)`: its own docstring says so ("Returns ``(paths, error_message)``"),
`error_message` is None on success, and `paths` is `[]` on refusal. It has no `.paths` attribute, so a
test written as `res = resolve_for_mutation(...)` then `res.paths` raises
`AttributeError: 'tuple' object has no attribute 'paths'` (observed at review). E-05's original
wording, "`resolve_for_mutation` succeeds with `n=1`", reads naturally as the `resolve` result shape it
sits beside in the same sentence, and `resolve` DOES return an object with `.kind`/`.paths`. The two
sibling calls therefore have different shapes, which is precisely the kind of thing a plan should
state rather than leave the executor to discover. E-05 and V-05 now spell out the unpacking.

Measured on the E-05 fixture, both states: clean gives `paths` length 1 with `err is None`; mutated
gives `paths == []` and `err` beginning `selector 'tgt001' is ambiguous (substring) matching multiple
files; pass --force to act on all:` followed by both ABSOLUTE tempdir paths. The absolute paths are
why the refusal must be matched on a substring, not compared whole.

### F-8 The bullet-asymmetry pin `selectors.py` cites NO LONGER EXISTS

`_normalize_yaml_scalar`'s docstring and the deleted `YamlScalarNormalizationTests` both name
`tests/test_cli_find.py::BacktickSetValueIsPinnedTests` as the guard that keeps normalization off the
bullet dialect. Measured at review: that class is present nowhere under `tests/`, and
`git log --oneline -S BacktickSetValueIsPinnedTests` shows `19313eed` as the commit that removed it,
the same trim that deleted this plan's two ancestors. So the asymmetry is unguarded on both sides and
the production comment points at a test that is gone. This does not change E-06, whose second half
already asserts the bullet side, but it upgrades that half from a precaution to a restoration and it
means no executor should treat the cited class as existing coverage. The stale comment is NOT fixed
here: this plan forbids itself any `selectors.py` edit, and a comment correction is one.

### F-6 M7 is a real hole but belongs to a different contract, and is raised as OQ-01

Teaching the PUBLIC readers `read_front_matter_id`/`read_front_matter_status` the YAML dialect is observable (they answer `yyyyyy`/`reference` on a fenced record where they answer None today) and unguarded. But `xo3244` E-03 deliberately left that pair bullet-only, and the pair's contract is about the HOST RUNNERS, not about research resolution: `selectors.py` records that both drivers previously carried private copies, that the pair's failure mode is silently degrading a runner to a directory-derived status, and that its LOOSE whitespace tolerance (verified: it answers on `-  Id:` and `-\tStatus:` where the strict internal readers return None) is the reason it exists. A test for it is worth writing and is arguably a different file's job; see OQ-01.

## Proposed changes (ordered, validatable)

1. E-01, E-02: create `tests/test_selector_two_dialect_readers.py` with fixture helpers and a harness-provenance assertion, so no later measurement can silently read a sibling checkout's package.
2. E-03: pin the metadata-region bound on all three readers plus its collision consequence (closes the M5 hole, the widest one).
3. E-04: pin the case-sensitive key lookup through both the readers and `aw find prompts draft` (closes M2, the property the code itself calls load-bearing).
4. E-05: pin the `id:` fallback by match KIND and the mutating-verb refusal, avoiding the vacuous same-filename test (closes M1a).
5. E-06: pin YAML scalar normalization and the deliberate bullet-side asymmetry (closes M6).
6. E-07: pin the `status:`/`setid:` fallbacks directly so they no longer rest on archive/CLI incidental coverage.

## Deferred / out of scope (with reason)

- The PUBLIC runner readers' bullet-only contract (F-6, mutation M7). Observable and unguarded: teaching `read_front_matter_id`/`read_front_matter_status` the YAML dialect changes their answers and the suite stays green. It is nonetheless a DIFFERENT contract, about the host runners rather than about research resolution, and `xo3244` E-03 made leaving the pair bullet-only an explicit decision with its own stated reasons. Whether to pin it here, in its own file, or not at all is a scope question for the maintainer, so it is raised as a question rather than pre-decided.
  - Carrier-Declined: This row is a SCOPE QUESTION already carried by OQ-01, not deferred work with an owner. Filing an item now would presuppose the answer OQ-01 exists to ask (the recommended option is a separate file, but two other options are defensible and the choice is the maintainer's). If OQ-01 resolves toward pinning it, THAT resolution mints the carrier with the chosen shape; if it resolves toward leaving it, there is nothing to carry. Recorded here so a reviewer does not read the omission as an unmeasured gap: the hole is measured, quantified in F-6, and deliberately unassigned pending one decision.
- The general audit of what commit `19313eed` left unguarded across the whole suite. This plan is ONE measured instance of that class (the two-dialect readers) and deliberately does not attempt the sweep, which would be a different size of work entirely.
  - Carrier: xvp5vx
- M3 (bullet-first dialect ordering) and M4 (the `text.startswith("---")` fence pre-filter). Both measured green under mutation, and both measured UNOBSERVABLE, with the structural reason recorded in F-5: the two dialects are disjoint on every real record, so their order cannot change an answer, and `parse_frontmatter` already returns None for unfenced text, so the pre-filter is a pure performance guard.
  - Carrier-Declined: Nothing is owed, because there is no behavioral difference to assert. A test for either property could only be written by pinning code structure (asserting the order of two branches, or that a particular guard clause exists), which `GUIDING_PRINCIPLES.md` Section 16 prohibits outright and which plan `b02ohu` is currently removing elsewhere in the suite. Filing an item would create an obligation that cannot be discharged without violating a standing rule. These are listed rather than omitted so a future mutation census does not re-derive them as holes.
- `aw archive`'s historical resolver bypass, mentioned in F-2's interpretation because it is what made E-07's incidental coverage fragile in the first place.
  - Carrier-Declined: The work is already DONE, so declining is correct and filing would misrepresent shipped work as outstanding. Backlog `mblu3p` (filed by `xo3244`'s own execution) is `done` with `- Graduated-To: researchsel`, and plan `me227c` ("route the research mutating verbs through the one selector resolver") is in `plans/executed/`. Verified at authoring. It is named here only to explain WHY E-07 pins the `status`/`setid` fallbacks directly instead of trusting the archive tests that currently cover them incidentally.
- Any edit to `agent_workflows/selectors.py`. The readers were measured CORRECT at authoring; this plan restores assertions only, and the Approval gate makes a required production edit a STOP-and-report condition.
  - Carrier-Declined: This row records a PROHIBITION this plan places on its own execution, not deferred work, so nothing is owed. No finding in this plan measures a fault in the readers; all four holes are in the TESTS. If execution discovers a genuine reader defect, that is a new finding needing its own carrier at that time, which is exactly what the gate instructs, rather than an obligation that can be predicted and filed now.

## Scope check

- Over-scope: none. The single `Scope-Paths` entry is one new test file, and the plan explicitly forbids touching `agent_workflows/selectors.py`.
- Under-scope: the M7 public-reader hole (F-6) is left to OQ-01, and the `19313eed` sweep is left to `xvp5vx`. Both are named above with their carriers, so neither is silently dropped.

## Required tests / validation

The deliverable IS a test file, so validation is mutation-based and must be pasted, not summarized. For each of E-03..E-07 the executor must demonstrate RED-then-GREEN: apply the named mutation to `agent_workflows/selectors.py`, run the new file, paste the FAILURE; revert with `git checkout -- agent_workflows/selectors.py`, re-run, paste the PASS. A test that passes under its own mutation is vacuous and must be fixed, not accepted.

Then run the suite BARE (`python3 -m pytest`) and reconcile the count against the authoring baseline `3246 passed, 2 skipped`: the expected result is `3246 + N passed, 2 skipped` where `N` is exactly the number of tests added, with ZERO pre-existing tests newly failing. PROVE COLLECTION BY THE BARE SUITE, not by naming the file: a file pytest does not collect adds zero tests while the suite still reports green, so "it passes when I run it directly" is not evidence it runs. Finally confirm `agent_workflows/selectors.py` is byte-identical to HEAD at the end (`git diff --stat agent_workflows/selectors.py` empty), since every mutation above edited it temporarily.

## Spec / documentation sync

N/A with reason. This plan adds test coverage for behavior two executed plans already shipped and changes no contract, no CLI surface, no output format and no record grammar, so no `.spec.md` is amended and no `Scope-Paths` entry is a spec file. `CHANGELOG.md` is deliberately untouched: nothing user-visible changes. Note for a reviewer who may expect otherwise: `xo3244` DID change the changelog, because it changed what `aw find research` returns; restoring its tests changes nothing a user can observe.

## Open questions

### OQ-01: Should the PUBLIC runner readers' bullet-only contract be pinned here, in its own file, or not at all?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Measured (F-6, mutation M7): teaching `read_front_matter_id`/`read_front_matter_status` the YAML dialect is observable (they answer `yyyyyy`/`reference` on a fenced record where they answer None today) and the full bare suite stays at `3246 passed, 2 skipped`, so no test notices. Three options. (1) ADD IT HERE, cheapest, but mixes the host-runner contract into a file whose subject is the research dialect. (2) OWN FILE, cleanest, since the pair's real contract is its LOOSE whitespace tolerance (verified: it answers on `-  Id:` and `-\tStatus:` where the strict internal readers return None) PLUS its deliberate YAML abstention, and those two belong stated together; costs a second carrier. (3) LEAVE IT, defensible only if the pair is adequately protected by the runner tests that consume it, which I did NOT verify and therefore do not assert. RECOMMENDED: (2), because the property being guarded is "a driver's front-matter reader stays narrow and whitespace-tolerant", which a reader looking for it would never think to seek in a file named for the two-dialect research readers. NOT BLOCKING: this plan's seven items are complete and correct whichever option is chosen, and no item depends on the answer. It is the maintainer's call because it is a scope question, not a technical one.
- Carrier-Declined: No carrier is owed while the question is unanswered, because each candidate answer implies a DIFFERENT carrier and filing one now would presuppose the decision. Option (2), the recommendation, mints a new backlog item; option (1) folds the work into this plan's own `Scope-Paths`; option (3) creates no work at all. Minting an item today would therefore record option (2) as decided when the maintainer has not decided it, which is the same class of error as writing another role's attestation. The measurement itself is durable regardless of the outcome: F-6 quantifies the hole and names the exact mutation that exposes it, so whoever answers this has the evidence in hand and nothing is lost if the answer is "leave it".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the bare-suite line showing the file COLLECTED, i.e. a `python3 -m pytest` total of exactly `3246 + N passed, 2 skipped` with `N` stated and equal to the number of tests the file defines, plus the output of `python3 -m pytest tests/test_selector_two_dialect_readers.py -o addopts=""` showing that same `N` passing. Confirm in one line that NO `slow` or `livecorpus` marker was added and that the file writes only into a temporary directory (quote the fixture's `tempfile` call).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the resolved `agent_workflows.selectors.__file__` observed during the run, showing it is under the SAME checkout as the test file, and paste the failure produced when the provenance assertion is deliberately pointed at a different root (or state precisely why that negative case cannot be simulated and what was asserted instead). A green provenance test with no demonstrated failure mode is not evidence.
  ON THE NEGATIVE CASE, review verified the positive half is workable and notes the honest route for the negative half: `Path(selectors.__file__).resolve()` does sit under `Path(<test file>).resolve().parent.parent` in this lane, so the assertion passes as intended. The failure mode is NOT reachable by re-importing from a sibling checkout inside one process (the module is already in `sys.modules`, and importing the main checkout's copy would be an out-of-lane read this lane forbids). So the acceptable demonstration is to invert the assertion's OWN comparison in the test file for one run (compare against a deliberately wrong root such as `Path("/nonexistent")`) and paste that failure; that mutates only this plan's own scope path, not `agent_workflows/`. State which route you took.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: RED-then-GREEN for mutation M5. Paste the failure when `metadata_region(text)` is replaced by `text` in all three readers, showing the readers answering the QUOTED `ffffff`/`approved`/`quotedset`; then paste the pass after `git checkout --`. Separately paste the live-tree collision count under both states (expected: 0 clean, `uyeko5` colliding across 3 records mutated), or state why that measurement was taken differently.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: RED-then-GREEN for mutation M2. Paste the failure when the YAML key lookup is made case-tolerant, showing `aw find prompts draft` matching the session-handoff fixture (`kind=status`, `n=1`), and the pass after revert. Also paste the assertion output proving `research_contract.parse_frontmatter` DOES expose `Kind`/`Status`/`Date` under their real capitalization, so the miss is proven to be the lookup and not a parse failure.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: RED-then-GREEN for mutation M1a. Paste the failure when the `id` fallback is removed, and it MUST show the ambiguity path (`kind=substring`, 2 paths, and the `resolve_for_mutation` refusal text naming both files), not merely a changed kind. CONFIRM the test unpacks `resolve_for_mutation` as the `(paths, error_message)` 2-TUPLE it actually returns and matches the refusal on a distinctive SUBSTRING rather than the whole string, since the message interpolates per-run absolute tempdir paths; a test written against a `.paths` attribute raises `AttributeError` and FAILS this item for the wrong reason. ALSO paste evidence that the vacuous test was avoided: show that a same-filename id6 query (`aw find research <id6>` on a record whose name embeds its id6) returns the identical result under BOTH states, which is why the fixture uses a citing sibling.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: RED-then-GREEN for mutation M6. Paste the failure when `_normalize_yaml_scalar` is bypassed, showing the bare `probeset`/`quotedset` selectors resolving to `kind=None`, `n=0`, and the pass after revert. Separately paste the bullet-asymmetry assertion passing on HEAD and failing when normalization is extended to the bullet `_read_setid`, since the asymmetry is a pinned contract and a test that only checks the YAML half would let a "consistency" edit through.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: RED-then-GREEN for mutations M1b and M1c, run against the NEW FILE ALONE (`python3 -m pytest tests/test_selector_two_dialect_readers.py -o addopts=""`), so the failure is proven to come from this plan's own tests and not from the incidental `tests/test_research_archive.py` coverage. Paste both failures and both passes. Then paste the final `git diff --stat agent_workflows/selectors.py` showing it is EMPTY, confirming every mutation was reverted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTE ONLY WHAT THIS PLAN DECLARES. The single `Scope-Paths` entry, `tests/test_selector_two_dialect_readers.py`, is the whole authorized surface. Mutations to `agent_workflows/selectors.py` are a MEASUREMENT TECHNIQUE, not a deliverable: each one must be reverted immediately with `git checkout -- agent_workflows/selectors.py`, and the final `git diff --stat` on that file must be empty (V-07). If a test cannot be made to pass without editing that module, STOP and report: the readers were measured correct at authoring, so a required production edit means a real defect was found, and that is a new carrier rather than a widening of this one.

DO NOT ACCEPT A TEST THAT PASSES UNDER ITS OWN MUTATION. Every one of E-03..E-07 exists because a property is currently green under mutation, so a replacement that is ALSO green proves nothing and is worse than nothing, because it looks like coverage. Two specific traps are already measured and named: the id6 test is vacuous if the fixture filename embeds the queried id6 (E-05), and the case-sensitivity test is vacuous if written as a corpus census, because the tracked fenced non-research population is 0 in an isolated worktree (E-04). If a test cannot be made non-vacuous, leave the item incomplete and report it rather than shipping a green assertion.

HONESTY. Paste ACTUAL runner output for every RED and every GREEN; never claim a run you did not perform. Run the suite BARE (`python3 -m pytest`), not with added flags: `-n0` makes it several times slower here, a second `-q` compounds into `-qq` and suppresses the `N passed` line these validations require, and `-p no:randomly` disables the order randomization. Reconcile the final count against the authoring baseline `3246 passed, 2 skipped` and state `N` explicitly; a green total that has not MOVED means the file was not collected, which V-01 exists to catch. If a measurement in Findings fails to reproduce at execution, report the new number and correct the plan's claim rather than inheriting it; two of `xo3244`'s own numbers were stale by the time this plan was authored.

COMMIT DISCIPLINE. Commit through `aw commit <plan> -- tests/test_selector_two_dialect_readers.py`, never `git add -A`/bare/`-a`, and never push. Other agents may be working in this checkout: verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`. Take particular care that no temporarily-mutated `agent_workflows/selectors.py` is ever staged.

LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item must carry pasted evidence before this plan moves to `.aw/records/plans/executed/`. Use the tooled transition; do not hand-edit `- Status:`. This plan declares `- Item-Dependencies: none` and depends on nothing pending: both plans whose coverage it restores (`76w6mq`, `xo3244`) are already in `plans/executed/`, so it can execute at any time. It is Order 02 of Set `selfmdialect`, whose Order 01 (`xo3244`) is executed.
