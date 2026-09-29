# IPD: Give the archive plans matcher the shared selector vocabulary and make an unmatched target refuse

- Date: 2026-09-29
- Kind: child
- Concern: `aw archive plans <target>` has a THIRD private matcher with TWO defects, and both are SILENT, which makes them worse than the refusal the backlog item reports. FIRST, a filename or path selector matches nothing and the command exits 0 printing a SUCCESS banner: measured in this lane, `aw archive plans 20260808-0004-06-migrate-existing-plans.ipd.md` printed `✓ CLEAN  no terminal-root plan or Set matches '<filename>'` with EXIT 0, while `aw archive plans 7qx7ys` archived that same plan. An operator who scripts an archive from a filename gets a green tick and no archive. SECOND, a terse setid fails whenever the plan's `- Set:` value carries a descriptive parenthetical, because `plans_archive._find_targets` compares the RAW `- Set:` line text: measured, `aw archive plans researchorg` matched nothing while `aw archive plans 'researchorg (research-org)'` matched 3 plans. That is 77 distinct setids (136 plans) in this repository addressable only by quoting a string no documentation tells anyone to quote.
  THE TERSE-SETID HALF IS A DIVERGENCE FROM A RULE THE REPOSITORY STATES TWICE, so it is a defect rather than an undocumented choice. `plans_index.set_terse_id` is the named authority for the terse token, and `selectors._first_set_token`'s docstring says "The terse set-id: the first whitespace token before any '(' (mirrors plans_index)". `plans_refs.run_mv` honors it (`existing_terse = _idx.set_terse_id(...)`). Only this matcher does not.
  AN UNMATCHED TARGET EXITING 0 IS THE MORE DANGEROUS HALF, because it is indistinguishable from "nothing needed archiving". Measured: `aw archive plans nonexistent-token-xyz` also prints `✓ CLEAN` and exits 0, so the command cannot distinguish a typo from a clean tree. The BARE sweep legitimately exits 0 on an empty result (nothing was due); an EXPLICIT target that matched nothing is an operator error and must not report success.
  `aw archive research` IS ALREADY BETTER, which shows the fix has a working precedent in the same verb family: it routes through `selectors.resolve_for_mutation` (via `research_archive._resolve_research_for_mutation`) and accepts a filename. Measured: `aw archive research <a filename>` exits 0 and previews the archive, while `aw archive plans <a filename>` exits 0 and does nothing.
- Scope: Make `plans_archive._find_targets` resolve an EXPLICIT target through `selectors.resolve_for_mutation(repo_root, "plans", target)` so it accepts the same vocabulary as every other verb, compare a setid against the TERSE token via `plans_index.set_terse_id` rather than the raw `- Set:` line, keep the existing terminal-root restriction, and make an explicit target that matches nothing REFUSE (nonzero) instead of printing a success banner. Add the outcome tests this matcher has none of. EXCLUDES: the BARE sweep path (`sweep_candidates`, `--age`), which is a different code path with different semantics and legitimately exits 0 on an empty result; `selectors.py`; `plans_refs.py`; and `research_archive.py`.
- Scope-Paths: agent_workflows/plans_archive.py, tests/test_plans_archive_selectors.py
- Item-Dependencies: executed:eby93o
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: gyv9tf
- Blocks-Release: next
- Set: awrenamesel
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 1x4tdo

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `gyv9tf`. NEITHER DEFECT IS IN THE BACKLOG ITEM. Both were found while mapping the item's claim that "the underlying inconsistency between selector kinds across types remains": enumerating every verb's accepted selector kinds turned up a THIRD private resolver on `archive plans`, and probing it turned up a silent no-op (F-01) and a raw-`- Set:` comparison (F-03) that the item does not mention. They are carried as a separate Order rather than folded into `87m438` because they are a DIFFERENT function in a DIFFERENT module with its own terminal-root semantics, and because the exit-code change is a behavior change a reviewer may want to judge on its own. The `--exit-nonzero-on-unmatched` half is deliberately NOT presented as obvious: OQ-01 records why the bare sweep must keep exiting 0 and why only an explicit target changes.

## Goal

Stop `aw archive plans` reporting success for a target it did not archive, and let it accept the same selectors every other verb accepts, including a terse setid that today requires quoting a descriptive parenthetical.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin both silent failures

- [ ] E-01 REPRODUCE THE SILENT NO-OP AS A FAILING TEST. Create `tests/test_plans_archive_selectors.py` and add cases asserting that `aw archive plans <a terminal plan's FILENAME>` and `aw archive plans <its repo-relative PATH>` each ARCHIVE that plan (with `--apply`) and that a preview run NAMES it. At HEAD both must FAIL: measured, the command prints `✓ CLEAN  no terminal-root plan or Set matches '<filename>'` and exits 0 while the id6 form archives the same plan.
  ADD THE UNMATCHED-TARGET CASE IN THE SAME ITEM, since it is the same observable class: `aw archive plans <a token matching nothing>` must exit NONZERO. At HEAD it exits 0 with the `✓ CLEAN` banner, which is why a typo is indistinguishable from a clean tree.
  ASSERT ON THE EXIT CODE AND ON THE FILE SYSTEM, not on the banner text. The banner is presentation; the observable outcomes are the exit status and whether the plan moved into its `YYYYMM/` shard.
  DRIVE IT IN-PROCESS VIA `cli.main` UNDER `redirect_stdout`, NOT AS A SUBPROCESS. Measured hazard rather than style: an editable install can make a subprocess `python3 -m agent_workflows` in a lane import the MAIN checkout, so a subprocess assertion can pass while the tree under test is unfixed (filed as `ccbe60`). `tests/test_group_verb_policy.py` already uses the in-process shape and is the model to copy.
  SEED PLANS AT A DISPOSITION ROOT, because `_find_targets` only considers plans whose path satisfies `_at_disposition_root` (a plan already inside a `YYYYMM/` shard is not a candidate). Put fixtures directly in `.aw/records/plans/executed/` in a `git init` repo, since the mover uses git.
  - Depends on: none
  - Expected outcome: Three tests FAILING at HEAD: filename and path each silently archive nothing at exit 0, and an unmatched target reports success.
  - Execution state: pending

- [ ] E-02 REPRODUCE THE TERSE-SETID FAILURE AS A FAILING TEST. Add a case seeding two terminal plans whose front matter reads `- Set: demoset (a descriptive label)` and asserting `aw archive plans demoset` targets BOTH. At HEAD this FAILS: measured on this repository, `aw archive plans researchorg` matched nothing while `aw archive plans 'researchorg (research-org)'` matched 3 plans.
  ADD THE CONTROL: a plan whose `- Set:` is a BARE terse id must keep matching, since that is the 423-setid population that works today and must not regress.
  - Depends on: none
  - Expected outcome: Two tests, the parenthetical case FAILING at HEAD and the bare case PASSING, isolating the raw-line comparison as the cause.
  - Execution state: pending

### Task group 2: route resolution and correct the exit status

- [ ] E-03 RESOLVE AN EXPLICIT TARGET THROUGH `selectors.resolve_for_mutation` IN `plans_archive._find_targets`, THEN APPLY THE TERMINAL-ROOT FILTER. Replace the private scan's matching with the shared resolver call, keep `_at_disposition_root` as a POST-RESOLUTION filter, and keep returning a sorted list.
  KEEP THE TERMINAL-ROOT RESTRICTION, WHICH IS REAL SEMANTICS AND NOT AN ARTIFACT OF THE OLD MATCHER. Archiving is weekly sharding of TERMINAL plans, so a pending plan is not an archive candidate and a plan already inside a `YYYYMM/` shard is not either. After resolution, drop any path that is not at a disposition root. The DISTINCTION THAT MATTERS FOR THE MESSAGE: a selector that matched a real plan which is merely NOT TERMINAL is a different situation from a selector that matched nothing, and E-04's refusal must say which, or the fix trades a silent no-op for a misleading refusal.
  FOLLOW `research_archive`'s PRECEDENT, WHICH IS THE SAME SHAPE IN THE SAME VERB FAMILY: `research_archive._resolve_research_for_mutation` calls `resolve_for_mutation` and then CONFINES the result by dropping paths outside the research root and paths whose name does not parse. This item is that pattern with `_at_disposition_root` as the confinement predicate.
  THE SETID HALF FALLS OUT OF THIS AND MUST NOT BE HAND-WRITTEN AGAIN: `selectors._read_setid` already compares the TERSE token ("the first whitespace token before any '('"), so routing through the resolver fixes E-02's case without a second implementation of the terse rule. Do NOT add a local `set_terse_id` call as well; one authority, reached through the resolver.
  - Depends on: E-01, E-02
  - Expected outcome: An explicit target accepts filename, stem, path, id6 and terse setid; only terminal-root plans are returned.
  - Execution state: pending

- [ ] E-04 MAKE AN EXPLICIT TARGET THAT MATCHED NOTHING REFUSE, AND SAY WHICH REASON APPLIES. In `plans_archive.run_archive`'s `if target:` branch, return a NONZERO status instead of 0 when resolution yields no archivable plan, and distinguish the two cases in the message: the selector matched no plan at all, versus it matched a plan that is not at a terminal disposition root (naming that plan and its status).
  CHANGE ONLY THE EXPLICIT-TARGET BRANCH. The BARE sweep must keep exiting 0 on an empty result, because "no plan is old enough to archive" is a successful no-op and is how a scheduled sweep is expected to behave. This is the whole reason the change is scoped to one branch (OQ-01).
  USE THE REPOSITORY'S REFUSAL CONVENTION, not a bare `print`: the surrounding code already uses `Term().empty_result(...)` with a `NextAction`, so emit the failure through the same presentation layer rather than inventing a second style, and keep pointing at `aw find plans` as the next action since that is the verb that shows what a selector does resolve.
  - Depends on: E-03
  - Expected outcome: `aw archive plans <typo>` exits nonzero with a message naming the selector; `aw archive plans <a pending plan>` exits nonzero saying it is not terminal; a bare sweep with nothing due still exits 0.
  - Execution state: pending

### Task group 3: prove nothing legitimate broke

- [ ] E-05 PIN WHAT MUST NOT CHANGE. Add cases asserting: (a) the id6 selector still archives, which is the form that works today and the one every existing caller uses; (b) a BARE setid still targets all its members; (c) the BARE SWEEP is untouched, both that `--age` still selects by age and that an empty sweep exits 0; (d) a plan already inside a `YYYYMM/` shard is still not a candidate; (e) a foreign-type path handed to `aw archive plans` refuses, which is Order 01's guard proving it reaches this newly routed matcher.
  SEARCH FOR AND RUN EVERY EXISTING `archive` TEST BEFORE AND AFTER, because the exit-code change is the kind that breaks a caller asserting `rc == 0`. Any pre-existing test that asserts success for an unmatched explicit target is asserting the DEFECT; if one exists, report it and the proposed correction rather than silently rewriting it, since the test file may be outside this plan's `Scope-Paths`.
  - Depends on: E-03, E-04
  - Expected outcome: Every existing archive behavior preserved, the sweep provably untouched, and a foreign-type path refused.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).
- Tests must assert OBSERVABLE BEHAVIOR, never code structure: no `inspect`/`ast`/regex reads of production source, no symbol censuses (AGENTS.md, GUIDING_PRINCIPLES P16). Every test this plan adds drives a real verb through `cli.main` and asserts on exit codes and on where files ended up.
- `archive` is wired for only TWO types: `artifact_types.TYPE_BACKENDS` gives `plans` -> `plans_archive.run_archive` and `research` -> `research_archive.run_archive`; every other type reports `archive` unsupported. So `archive` has exactly two implementations and this plan touches one.
- `Term().empty_result(...)` with a `NextAction` is the established presentation for "nothing matched" in this module; a refusal should go through the same layer.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`; verify the staged set, since this checkout is shared (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | A FILENAME TARGET IS A SILENT NO-OP AT EXIT 0, which is worse than the refusal the backlog item reports because it looks like success. | `aw archive plans 20260808-0004-06-migrate-existing-plans.ipd.md` -> `✓ CLEAN  no terminal-root plan or Set matches '<filename>'`, EXIT 0. `aw archive plans 7qx7ys` -> `--- would archive 20260808-0004-06-migrate-existing-plans.ipd.md -> 202608/ ---`, EXIT 0. Same plan, opposite outcome. |
| F-02 | AN UNMATCHED TARGET IS INDISTINGUISHABLE FROM A CLEAN TREE, so the command cannot report an operator typo. | `aw archive plans nonexistent-token-xyz` -> `✓ CLEAN  no terminal-root plan or Set matches 'nonexistent-token-xyz'`, EXIT 0. |
| F-03 | A TERSE SETID FAILS WHENEVER THE `- Set:` VALUE CARRIES A DESCRIPTIVE PARENTHETICAL, because `_find_targets` compares the RAW line: `re.search(r"(?m)^- Set:\s*(.+?)\s*$", text)` then `sm.group(1) == selector`. | `aw archive plans researchorg` -> no match; `aw archive plans 'researchorg (research-org)'` -> 3 plans previewed. The record reads `- Set: researchorg (research-org)`. |
| F-04 | THE TERSE-SETID POPULATION IS LARGE, so this is not an edge case: 77 distinct setids covering 136 plans are addressable only by quoting the parenthetical, against 423 that work. | Corpus scan of `.aw/records/plans/**`: 908 plans declare a `- Set:`; 136 carry a parenthetical; distinct terse setids unaddressable = 77, addressable = 423. |
| F-05 | THE TERSE RULE IS A STATED REPOSITORY AUTHORITY THIS MATCHER IGNORES, so the divergence is a defect and not a local choice. | `plans_index.set_terse_id` is the named authority; `selectors._first_set_token` docstring: "The terse set-id: the first whitespace token before any '(' (mirrors plans_index)"; `plans_refs.run_mv` uses `_idx.set_terse_id`. Only `plans_archive._find_targets` compares the raw line. |
| F-06 | `aw archive research` ALREADY DOES THIS CORRECTLY, giving the fix a working precedent inside the same verb: it resolves through the shared resolver and then confines the result. | `research_archive._resolve_research_for_mutation` calls `selectors.resolve_for_mutation(..., deny=frozenset({selectors.MATCH_PATH}))` and then drops paths outside the research root. Measured: `aw archive research <a filename>` -> `--- would archive ... -> 202608/ ---`, EXIT 0. |
| F-07 | THE SHARED RESOLVER ALREADY ACCEPTS EVERY SELECTOR THIS VERB NEEDS, so this is a routing change and not new matching logic. | `selectors.resolve(repo,'plans',...)`: filename -> `kind=substring` n=1; stem -> `kind=substring` n=1; repo-relative path -> `kind=path` n=1; id6 -> `kind=id6` n=1; `findtier` -> `kind=setid` n=3. |
| F-08 | THE TERMINAL-ROOT RESTRICTION IS REAL SEMANTICS AND MUST SURVIVE, so the fix is resolve-then-filter rather than resolve-and-take. `_find_targets` skips any path failing `_at_disposition_root`, which is what keeps a sharded plan from being re-archived. | `_find_targets` computes `rel = p.relative_to(plans_dir)` and `continue`s unless `_at_disposition_root(list(rel.parts))`. |
| F-09 | `archive` EXISTS FOR ONLY TWO TYPES, so "make archive consistent" is a two-implementation problem and this plan closes the gap between them. | `artifact_types.backend_name(t,"archive")` -> `plans_archive.run_archive` for `plans`, `research_archive.run_archive` for `research`, `None` for the other seven. |
| F-10 | THE EXIT-CODE CHANGE MUST BE SCOPED TO THE EXPLICIT-TARGET BRANCH, because the bare sweep's empty result is a legitimate success. The two live in the same function, separated by `if target:`. | `plans_archive.run_archive` handles `if target:` first and falls through to the "Bare sweep: parse age duration and find candidates keeping sets together" path; a sweep with nothing due is a successful no-op. |
| F-11 | Baseline is clean in this lane, so any failure after the change is attributable to it. THE ABSOLUTE COUNT DRIFTS AND IS NOT A BAR: re-derive it on your own clean tree. | `python3 -m pytest` -> `3246 passed, 2 skipped, 3 warnings in 51.44s`. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_plans_archive_selectors.py` with failing cases for a filename target, a path target, and an unmatched target reporting success (E-01).
2. Add failing/control cases for a terse setid with and without a descriptive parenthetical (E-02).
3. Route `_find_targets`'s explicit-target resolution through `selectors.resolve_for_mutation`, keeping `_at_disposition_root` as a post-resolution filter (E-03).
4. Make an explicit target that matched nothing archivable exit nonzero, distinguishing "matched nothing" from "matched a non-terminal plan", leaving the bare sweep's exit status alone (E-04).
5. Add the must-not-break guards: id6, bare setid, the sweep, an already-sharded plan, and a foreign-type path refusal (E-05).

## Deferred / out of scope (with reason)

- THE PLANS `rename`/`group` SELECTOR DEFECT, which is the backlog item's own subject.
  - Carrier: 87m438
- THE CROSS-TYPE PATH GUARD this plan depends on.
  - Carrier: eby93o
- THE `roadmaps` ADDRESSABILITY DEFECT and the broken hint that works around it.
  - Carrier: 3qxuw1
- WIRING `archive` FOR THE OTHER SEVEN TYPES (F-09). Out of fence and not a defect: no type other than `plans` and `research` has an archive convention to implement, so adding the verb would mean inventing sharding policy for specs, backlog and the rest. That is a feature decision, not a selector fix.
  - Carrier-Declined: there is no shelving convention to implement for the other types; inventing one is a design decision needing its own review, not a consistency repair.
- CHANGING THE BARE SWEEP'S SELECTION OR EXIT STATUS (F-10, OQ-01). Deliberately untouched: an empty sweep is a successful no-op and a scheduled caller depends on that. Only the explicit-target branch changes.
  - Carrier-Declined: an empty sweep is correct behavior, not a defect; changing it would break scheduled callers for no gain.
- DEDUPLICATING `plans_archive` AND `research_archive` into one archive engine. Tempting after F-06 and declined: their sharding conventions, confinement predicates and set-keeping rules differ, and merging them would put both at risk in a change whose purpose is to fix one matcher's selector vocabulary.
  - Carrier-Declined: an unmeasured behavioral merge of two engines with different confinement and sharding rules; disproportionate to the defect and would obscure the source of any regression.

## Scope check

- Over-scope: none. The two declared paths are the module holding the defective matcher and a new test file dedicated to it. `agent_workflows/selectors.py` is deliberately NOT in scope: this plan CALLS `resolve_for_mutation` and must not modify it (Order 01's fence). `research_archive.py` is cited as precedent only and must stay byte-unchanged.
- Under-scope: this plan does not unify the two archive implementations, and it does not give `archive` to the seven types that lack it. Both are recorded above with reasons. It also leaves the bare sweep's behavior entirely alone, which is deliberate rather than an omission.

## Required tests / validation

- The new cases in `tests/test_plans_archive_selectors.py`: filename, path and unmatched target; terse setid with and without a parenthetical; and the five must-not-break guards.
- FAILING-FIRST CONTRAST IS MANDATORY, not optional: run E-01's and E-02's cases against UNFIXED source and paste the failures, then against the fixed tree and paste the passes. For the silent-no-op cases the failing run is also the proof that a green tick hid a no-op.
- THE EXIT-CODE CHANGE MUST BE SHOWN ON BOTH BRANCHES: paste an explicit unmatched target exiting NONZERO and a bare sweep with nothing due still exiting 0, in the same evidence block, so the scoping is demonstrated rather than claimed.
- Bare `python3 -m pytest` before and after, with both summary lines pasted. MEASURE YOUR OWN BASELINE ON A CLEAN TREE and compare against that, not against F-11's `3246`, which drifts with every intervening commit. The bar is ZERO FAILURES and a passed-count delta of exactly the new cases.
- Every pre-existing archive test run and pasted. If any asserted success for an unmatched explicit target, report it as asserting the defect and propose the correction rather than silently editing it.
- Negative proof that the fence held: `git diff --stat` shows no change to `agent_workflows/selectors.py`, `agent_workflows/plans_refs.py` or `agent_workflows/research_archive.py`.
- `aw sanitize --agent` clean (no maintainer/machine identifiers in anything authored).

## Spec / documentation sync

No spec amendment is required and no `.spec.md` file is in `Scope-Paths`, and that conclusion rests on reading the specs that govern selectors and setids rather than on a grep miss.
- Spec `z7nbn1` 1.1 ("A selector that resolves for one verb MUST resolve identically for every other verb") is what makes F-01 a defect: `aw find plans <filename>` resolves and `aw archive plans <the same filename>` matches nothing.
- Approved spec `2lcqno` N1 defines a setid as a shared grouping LABEL and N3 requires type-scoped resolution; the terse-token rule this matcher ignores is stated by `plans_index.set_terse_id` and mirrored in `selectors._first_set_token`. F-03 is a divergence from that stated authority.
- The exit-status change is a CLI CONTRACT change for one branch of one command, so it is worth a reviewer's explicit attention even though no spec text prescribes the current 0. If the executor finds a documented promise that an unmatched explicit target exits 0, STOP: that converts this from a defect fix into a contract change, and the file must be added to `Scope-Paths` and amended in the same change per the plan-may-amend-a-spec rule.
- Check `CHANGELOG.md` conventions at execution time: a user-visible exit-status change on `aw archive plans` is the kind of behavior change a release note should mention. If the repository's convention requires an entry, report that the file is outside this plan's `Scope-Paths` rather than editing it silently.

## Open questions

### OQ-01: Should an unmatched EXPLICIT target exit nonzero, given the bare sweep exits 0 on an empty result?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, YES FOR AN EXPLICIT TARGET AND NO FOR THE SWEEP, because the two cases mean different things. A bare sweep's empty result says "nothing is old enough to archive", which is a successful no-op a scheduled caller depends on. An explicit target that matched nothing says "the thing you named does not exist or is not archivable", which is an operator error the exit status must carry; today both print `✓ CLEAN` and exit 0, so a typo is indistinguishable from a clean tree (F-02). The two branches are already separated by `if target:` in `run_archive` (F-10), so the change is precisely scopeable. E-05(c) pins the sweep's behavior so the scoping cannot silently widen. RISK ACKNOWLEDGED: this is a user-visible exit-status change, so E-05 requires running every pre-existing archive test and reporting any that asserted the old success.

### OQ-02: Should a target that resolves to a real but NON-TERMINAL plan refuse differently from one that matches nothing?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, YES, TWO DISTINCT MESSAGES, because collapsing them would trade a silent no-op for a misleading refusal. After E-03 the resolver may legitimately return a PENDING plan, which is not an archive candidate (F-08); telling the operator "no plan matched" when their selector matched exactly the plan they named, and the real reason is that it is not terminal, would send them looking for a typo that does not exist. The distinction is cheap because resolution and the terminal-root filter are separate steps, so the count before and after the filter is already known at the refusal site. The message for the non-terminal case should name the plan and its status.

### OQ-03: Should the `MATCH_PATH` kind be denied here, as `research_archive` denies it?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, DO NOT DENY IT. `research_archive._resolve_research_for_mutation` passes `deny=frozenset({selectors.MATCH_PATH})` and then confines to the research root, which is one way to be type-safe; this Set takes the other, and Order 01 (`eby93o`) adds a containment guard inside `resolve_for_mutation` itself, so a path is type-safe for every caller rather than per-caller. Denying the path kind here would ALSO reject a legitimate in-tree path, which F-01's sibling case shows an operator plainly wants (`aw archive plans <a repo-relative path to a terminal plan>`), and E-01 asserts that path works. E-05(e) pins that a FOREIGN path still refuses, which is the property that matters. If Order 01 is not in the tree, that test fails and this plan is not validated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The pytest output for the filename, path and unmatched-target cases run against UNFIXED source, pasted verbatim, showing them FAILING, together with the observed HEAD behavior for each: the exact `✓ CLEAN` banner text and the exit code 0. A pass here is a FAILURE of this validation. State explicitly that the fixtures were seeded at a DISPOSITION ROOT, since a plan inside a `YYYYMM/` shard is legitimately not a candidate and would make a correct test appear to reproduce the defect.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The parenthetical-setid case FAILING at HEAD and the bare-setid control PASSING at HEAD, both pasted, with the seeded `- Set:` line text quoted for each so the record shows exactly what distinguishes them. Plus the measured contrast from the real repository (`researchorg` matching nothing while the quoted `researchorg (research-org)` matches) as corroboration.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: E-01's and E-02's cases now PASSING, pasted; plus the `git diff` of `plans_archive._find_targets` showing the `resolve_for_mutation` call and `_at_disposition_root` retained as a POST-resolution filter. Plus one `--apply` run driven BY FILENAME, pasting the plan's path before and after so the shard move is visible. Plus confirmation that no second terse-setid implementation was added (the terse comparison comes from the resolver).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: In ONE block: an explicit unmatched target exiting NONZERO with its message, an explicit target naming a PENDING plan exiting nonzero with the DIFFERENT not-terminal message naming that plan, and a bare sweep with nothing due still exiting 0. The three together are what prove the change is scoped to the explicit-target branch and that OQ-02's distinction was implemented.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pytest output for all five guards, pasted, naming each (id6, bare setid, sweep untouched including `--age`, already-sharded plan not a candidate, foreign-type path refused). For the foreign-type case, paste the refusal text and confirm Order 01's guard is present in the tree under test; if it does not refuse, report this plan as NOT validated rather than adjusting the test. Plus the pasted result of every PRE-EXISTING archive test, with an explicit statement of whether any asserted the old exit-0-on-unmatched behavior and, if so, that it was REPORTED rather than silently rewritten. Plus the bare `python3 -m pytest` summary after the change compared against the baseline YOU measured before editing (not F-11's number), with the delta shown to be exactly the new cases and zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was authored `to-review` with no `- Readiness:` field, correctly, since that value is an output of review rather than of authoring. It must not be executed on the strength of the authoring turn.

EXECUTION CONTRACT. Stay inside `Scope-Paths`: `agent_workflows/plans_archive.py` and `tests/test_plans_archive_selectors.py`. Call `selectors.resolve_for_mutation`; do NOT modify `selectors.py` (Order 01's fence), and leave `plans_refs.py` and `research_archive.py` byte-unchanged. Change the exit status ONLY in the explicit-target branch; the bare sweep must still exit 0 on an empty result. Keep `_at_disposition_root` as a post-resolution filter, and do NOT add a second terse-setid implementation. THIS PLAN DEPENDS ON `eby93o` for path type-safety (OQ-03). Commit through `aw commit <plan> -- <paths>` with the staged set verified (the checkout is shared); never `git add -A`, never push, never `--no-verify`.
EVIDENCE CONTRACT. The failing-first contrast in V-01 and V-02 is the gate: if the cases cannot be observed failing against unfixed source, stop and report rather than proceeding. V-04's three-outcome block is the second gate, because a fix that makes everything refuse would pass V-01 while breaking scheduled sweeps. Paste actual runner output for every `V-*`; never record a pass not run. Be aware of the measured hazard behind E-01's in-process requirement: an editable install can make a subprocess `python3 -m agent_workflows` import the MAIN checkout rather than this lane (`ccbe60`), so a subprocess assertion can pass against unfixed source.
POST-GATE LIFECYCLE. On completion move this plan to `.aw/records/plans/executed/` only once `aw ipd lint --phase pre-transition` conforms and every `V-*` carries inspected evidence. The runner owns the transition in a managed lane (`aw ipd begin` refuses with `AW-LIFECYCLE-ROLE-001` there). Backlog item `gyv9tf` is set `graduated`, not `done`, by the authoring flow; do not close it here.
