# IPD: Correct the two dangling spec path citations in live source and record why the executed-plan citation must not be rewritten

- Date: 2026-09-29
- Kind: child
- Concern: Two full-path spec citations the backlog item names dangle. One is in LIVE source (`agent_workflows.agy_run`'s `--spec` help epilog) and is fixable; the other is in an IMMUTABLE executed plan and MUST NOT be rewritten. Fix the live one, correct a third live-source dangler review measured in the same file family, and record the executed-plan one as deliberately untouched.
- Scope: Repoint the two DANGLING full-path spec citations that live in editable source (`agy_run.py`'s `--spec` example, and `check_engine.py`'s I-07 provenance comment) at the real status-subdirectory paths, and add the regression test that keeps a `.aw/records/specs/<file>.spec.md` citation in tracked source from silently dangling again. EXCLUDES editing the executed plan `u06zo2` (immutable record; a `## Workflow history` pointer is the only permitted touch and even that is deferred here), EXCLUDES fixing `agy_run.resolve_spec`'s non-recursive glob (a separate live BUG this plan FILES rather than fixes), and EXCLUDES the 460+ danglers in terminal records.
- Scope-Paths: agent_workflows/agy_run.py, agent_workflows/check_engine.py, tests/test_spec_path_citations.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: ajomj3
- Set: ajomj3
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2wmwf7

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `ajomj3`. GATE NOTE: the item carries NO `- Blocks-Release:`, so this plan inherits none. `- Work-Kind: chore` is INHERITED from the item and is CORRECT for the work this plan actually does (repointing two stale comment strings changes no behavior a user can perceive), even though authoring MEASURED a genuine `bug` in the same file; that bug is FILED SEPARATELY rather than absorbed here, see OQ-02. BOTH of the item's claims VERIFY at HEAD `7d3de463`, but ONE OF THE TWO IS NOT FIXABLE AS THE ITEM IMPLIES, which is the single most important correction this plan carries. Claim 1 VERIFIES AND IS FIXABLE: `agy_run.py:122` reads `Example: python3 tools/agy_run.py --spec .aw/records/specs/20260809-2211-01-aw-project-layout.spec.md`, and that path does not exist (`ls` errors). Claim 2 VERIFIES AND MUST NOT BE FIXED IN PLACE: executed plan `u06zo2` cites the bare `.aw/records/specs/20260815-0151-01-honest-human-approval-attestation.spec.md` five times, and the file now lives at `implemented/`; but `u06zo2` is in `.aw/records/plans/executed/`, and the agent execution contract forbids changing what such a plan RECORDS. THE ITEM'S FRAMING OF CLAIM 2 IS THEREFORE WRONG IN A WAY THAT MATTERS: it reads as a typo to correct, and it is not a typo at all. The citation was CORRECT WHEN WRITTEN and a later migration invalidated it, proven by git: the plan was added at `7c68a4e3` (2026-09-20) and `git ls-tree -r --name-only 7c68a4e3` shows the spec at the FLAT `.aw/records/specs/20260815-0151-01-...spec.md` path it cites, while the `specdirs` migration `2fa65732` (2026-09-24) moved all specs into status subdirs. Rewriting it would falsify the record by making a 2026-09-20 plan appear to cite a path that did not exist until four days later. A THIRD DANGLER IN LIVE SOURCE was found by scanning rather than assumed, and it is in scope because it is the same defect class in an editable file: `check_engine.py:289` cites `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md:135` (now under `draft/`); the cited CONTENT still verifies at line 135 (I-07 "Release-gate preservation"), so only the directory is stale. THE ITEM'S "two" IS A FLOOR, NOT A CENSUS: a repo-wide scan found 470 dangling full-path spec citations across 151 files, of which 373 are in `plans/executed/` and 31 in `reviews/` (both immutable), 21 are deliberate TEST FIXTURE paths that SHOULD NOT resolve, and exactly 2 are in shipped package source. This plan fixes the 2 source citations and DELIBERATELY leaves the rest, with the reason recorded per class rather than silently. NOTHING HERE IS OBSOLETE and no pending plan or spec covers it: grepping pending plans and the specs tree for `agy_run`/spec-citation remediation returns nothing.

## Goal

Repoint the two dangling full-path spec citations that live in EDITABLE package source at their real status-subdirectory paths, add a regression test that fails when tracked source cites a nonexistent spec path, and record in this plan why the executed-plan citation the backlog item also names is deliberately left alone. Behavior is unchanged: both edits are to comment/help text.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-confirm the diagnosis at execution HEAD

- [ ] E-01 RE-MEASURE the three live-source citations and the executed-plan one at execution HEAD rather than trusting this plan's authoring measurements, because a concurrent lane may have moved a spec again and a spec's directory changes on every status transition (which is the whole root cause here). Confirm each of: (a) `.aw/records/specs/20260809-2211-01-aw-project-layout.spec.md` does NOT exist, and the real file is `.aw/records/specs/superseded/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` (NOTE THE SLUG DIFFERS, not only the directory: the real filename ends `-storage-wizard-and-state`, so this is NOT a pure directory prefix fix and a mechanical `s|specs/|specs/superseded/|` would still dangle); (b) `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md` does NOT exist and the real file is under `draft/`; (c) `u06zo2` in `plans/executed/` still cites the bare `honest-human-approval-attestation` path. If any has drifted, use the measured path and say so at finalize.
  - Depends on: none
  - Expected outcome: the three stale paths and their real locations re-confirmed at execution HEAD, with the slug difference on (a) explicitly noted, and any drift from this plan's authoring measurements reported rather than silently absorbed.
  - Execution state: pending

### Task group 2: Fix the two live-source citations

- [ ] E-02 CORRECT the `--spec` example in `agent_workflows/agy_run.py`'s argparse epilog (locate by the content string `Example: python3 tools/agy_run.py --spec`, in the `2. Spec Mode (--spec <target> | positional *.spec.md):` block) so it names a spec path that ACTUALLY RESOLVES. Use the real superseded-tree path measured in E-01, INCLUDING its full `-storage-wizard-and-state` slug. DO NOT invent a plausible-looking path and DO NOT leave a bare flat `specs/<name>.spec.md` form, because that form is precisely what cannot resolve after the `specdirs` migration. This is help text only; change no code path.
  - Depends on: E-01
  - Expected outcome: `agy_run.py`'s `--spec` example cites a path that exists on disk, verified by an existence check on the exact string now in the file.
  - Execution state: pending

- [ ] E-03 CORRECT the I-07 provenance citation in `agent_workflows/check_engine.py` (locate by the content string `I-07 IS THE RIGHT HOME AND THE FIT WAS VERIFIED`, whose following comment line carries the path) to the real `draft/` path measured in E-01, PRESERVING the `:135` line anchor only if E-01 re-confirmed that line still holds I-07's row; if the line moved, update the anchor to the re-measured line, and if the row can no longer be located by content, drop the numeric anchor and cite the `I-07` row by its content string instead (the repository's own citation rule: a line number may accompany a symbol or content anchor, never stand alone). Comment text only; change no rule logic and no rule id.
  - Depends on: E-01
  - Expected outcome: `check_engine.py`'s I-07 comment cites an existing spec path whose anchor still points at the I-07 row, with no change to any registered rule id or behavior.
  - Execution state: pending

### Task group 3: Keep it from regressing

- [ ] E-04 ADD a regression test at `tests/test_spec_path_citations.py` that scans TRACKED PACKAGE SOURCE (`agent_workflows/**/*.py` plus `tools/**/*.py`) for full-path `.aw/records/specs/...spec.md` citations and FAILS on any that does not exist on disk. It MUST FAIL FIRST: run it before E-02/E-03 and paste the failure naming both citations, then run it after and paste the pass. SCOPE IT TO PACKAGE SOURCE AND JUSTIFY THAT BOUND IN THE TEST DOCSTRING, because a broader scan would be WRONG in two measured ways: (i) `tests/` legitimately contains 21 such paths that are FIXTURE paths under `tmp_path` and are SUPPOSED not to resolve in the real tree (for example `tests/test_scope_match.py`'s `x.spec.md`, `tests/test_doctor.py`'s `draft/20260925-1111-01-test.spec.md`), so including `tests/` would assert a falsehood; and (ii) `.aw/records/plans/executed/` and `.aw/records/reviews/` hold 404 such paths that are IMMUTABLE HISTORY and correct-as-of-writing, so failing on them would demand forbidden edits. Test OUTCOMES, not code structure: this test reads repository DATA files to check a filesystem fact, and asserts nothing about how any function is written.
  - Depends on: none
  - Expected outcome: a new test that fails naming exactly the two live-source danglers before the fix and passes after, with its bound to package source justified in its docstring by the fixture-path and immutable-record reasons.
  - Execution state: pending

### Task group 4: Record what is deliberately not fixed

- [ ] E-05 RECORD, in this plan's "Deferred / out of scope" section at finalize, the per-class census of dangling spec citations this plan does NOT touch, with the COUNT and the REASON per class (immutable executed plans; immutable reviews; deliberate test fixtures; other records). Re-run the scan at execution HEAD so the numbers are current rather than copied from authoring. DO NOT open a backlog item proposing a sweep of the record trees: rewriting a citation that was correct when written falsifies history, which is exactly what E-01(c) establishes, so "unfixed" is the CORRECT terminal state for those classes and not a debt.
  - Depends on: E-01
  - Expected outcome: a per-class census with current counts and a stated reason per class, and no new item proposing to rewrite immutable records.
  - Execution state: pending

- [ ] E-06 FILE A SEPARATE BACKLOG ITEM for the genuine live BUG authoring measured in this same file, which is OUT OF SCOPE here and must not be silently fixed under a `chore`: `agy_run.resolve_spec` enumerates candidates with NON-RECURSIVE `d.glob("*.md")` over `.agents/docs/specs` and `.aw/records/specs`, so after the `specdirs` migration it can see only `README.md` and resolves ZERO of the repository's 38 specs. Measured at authoring HEAD `7d3de463`: `resolve_spec` raised `No specification matching ... found` for a bare filename, for a bare id6 (`pqsx96`), AND for a correct flat-looking full path, meaning `aw agy exec --spec` / Spec Mode is BROKEN FOR EVERY SPEC IN THE REPOSITORY. File it with `aw backlog new` as `- Work-Kind: bug`; per the repository's "every live bug gates the next release" rule it MUST carry `- Blocks-Release:` while live, and `next` resolves to the single `planned` release record (`20260820-f33nrj-01-f33nrj-2-0-0.release.md`, `- Status: planned`). In the item, cite the fix precedent rather than leaving it to be rediscovered: `specs._spec_files` already solved exactly this, and its docstring records that `rglob` ALONE IS NOT THE FIX because non-recursion was masking the absence of an ignored-path filter, so a recursive walk must also filter through `core.is_ignored_path`/`core.get_ignored_dirs` or it will start returning gitignored specs. ALSO RECORD WHY THE PRIOR SWEEP MISSED IT: executed plan `y4bdoz` ("Make every spec reader recursive") asserted "A package-wide grep ... finds exactly ONE non-recursive site, `specs.py:89`", but `tools/agy_run.py` had existed since `1ca197c7` (2026-08-16) and was graduated into the package at `4579ba87` (2026-08-28), both BEFORE that plan's 2026-09-10 review, so the audit's grep was incomplete; note too that `resolve_spec` has ZERO test coverage (no test references the symbol), which is why nothing caught it.
  - Depends on: E-01
  - Expected outcome: a new `bug` backlog item carrying a release gate, citing the measured breakage, the `specs._spec_files` fix precedent INCLUDING its ignored-path-filter coupling, and the reason the `y4bdoz` audit missed this site; created with `aw backlog new` and NOT fixed in this plan.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A SPEC'S DIRECTORY IS ITS STATUS, so any full-path spec citation is invalidated by a status transition. `specs.py`'s `_spec_files` docstring records the status-subdirectory layout (`.aw/records/specs/approved/` and siblings) and the `specdirs` migration `2fa65732` moved 38 specs out of the flat root. This makes a bare `.aw/records/specs/<name>.spec.md` citation structurally fragile, which is the root cause behind all three danglers in this plan and behind the 470 repo-wide.
- AN EXECUTED PLAN IS IMMUTABLE. The agent execution contract in `AGENTS.md` states plainly: "Never change what a plan already in `.aw/records/plans/executed/` RECORDS (its steps, evidence, results, or status): close a post-execution gap with a new corrective IPD, not an in-place edit." It permits exactly one addition, "a dated `## Workflow history` line ... that points at later work". This is what makes claim 2 of the backlog item unfixable as stated.
- THE RENAME VERB ALREADY KNOWS FULL-PATH CITATIONS CANNOT BE SAFELY AUTO-REWRITTEN, and its behavior is the precedent for treating them as hand-fix-only: `artifact_rename.find_unrewritable_path_citations` exists specifically to surface them, and `artifact_rename`'s mutation path WARNS on preview and FAILS CLOSED on `--apply` with "cannot auto-rewrite. Fix it by hand, then retry." Notably that guard is wired only into the RENAME path; a STATUS TRANSITION also moves a spec file (`aw specs set` prints `would move ... (status ...)`) and has no equivalent citation guard, which is the mechanism by which these citations rotted unnoticed.
- CITE BY SYMBOL OR CONTENT, NOT BY A BARE LINE NUMBER. The scaffold itself carries this rule (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`): a line number may be appended to a symbol or quoted-content anchor but never stand alone, because offsets expire. E-02/E-03 therefore locate their edit sites by content string, and E-03 re-verifies its `:135` anchor rather than trusting it.
- `chore` VERSUS `bug` TURNS ON USER-PERCEPTIBLE IMPACT. `AGENTS.md` states inefficiency or wrongness a user can NOTICE is a defect, and the gating work-kind set (default `bug`) obliges a live item to carry `- Blocks-Release:`. Repointing a comment string is imperceptible (`chore`); a `--spec` mode that resolves none of 38 specs is perceptible and total (`bug`), which is why E-06 files it separately instead of folding it in here.

## Findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| F-1 | MEDIUM | The item's claim 1 VERIFIES: `agy_run.py`'s `--spec` example cites a nonexistent spec. | `agent_workflows/agy_run.py:122` reads `Example: python3 tools/agy_run.py --spec .aw/records/specs/20260809-2211-01-aw-project-layout.spec.md`; `ls` on that path errors `No such file or directory`. |
| F-2 | HIGH | The item's claim 2 VERIFIES BUT IS NOT FIXABLE IN PLACE, which the item's framing obscures. `u06zo2` is an EXECUTED plan and the contract forbids changing what it records. | `.aw/records/plans/executed/20260908-lcpolicy-01-u06zo2-...ipd.md` cites the bare `.aw/records/specs/20260815-0151-01-honest-human-approval-attestation.spec.md` at lines 88, 103, 107, 148, 720; the real file is `.aw/records/specs/implemented/...`. `AGENTS.md`: "Never change what a plan already in `.aw/records/plans/executed/` RECORDS". |
| F-3 | HIGH | The executed-plan citation was CORRECT WHEN WRITTEN, so rewriting it would falsify history rather than fix a typo. This is the decisive reason claim 2 is closed as won't-fix. | Plan added at `7c68a4e3` (2026-09-20); `git ls-tree -r --name-only 7c68a4e3` lists the spec at the FLAT `.aw/records/specs/20260815-0151-01-honest-human-approval-attestation.spec.md`. The `specdirs` migration `2fa65732` (2026-09-24) moved it to `implemented/`. |
| F-4 | MEDIUM | A THIRD dangler exists in live source, same class, in an editable file, so it belongs in this plan. | The comment block opening `I-07 IS THE RIGHT HOME AND THE FIT WAS VERIFIED` in `agent_workflows/check_engine.py` (`:289`) cites the flat `20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md` path; the real file is under `draft/`. The cited CONTENT still holds: the anchored line is the `I-07` / `Release-gate preservation` row. |
| F-5 | MEDIUM | The fix for F-1 is NOT a directory prefix insertion: the real filename's SLUG also differs, so a mechanical prefix rewrite would still dangle. | Cited stem `20260809-2211-01-aw-project-layout`; real file `.aw/records/specs/superseded/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`. |
| F-6 | LOW | The item's "two" is a FLOOR, not a census; the true population is 470 across 151 files, but almost all of it is correctly left alone. | Repo-wide scan at HEAD `7d3de463`: 470 dangling full-path spec citations; 373 in `plans/executed/`, 31 in `reviews/`, 21 in `tests/` (fixtures), 14 in other terminal plan dirs, 2 in package source. |
| F-7 | HIGH | A GENUINE LIVE BUG sits in the same file as F-1 and is NOT this plan's scope: `agy_run.resolve_spec` is non-recursive, so Spec Mode resolves ZERO of 38 specs. | `agy_run.resolve_spec` builds candidates with `d.glob("*.md")` over the two specs roots; `Path('.aw/records/specs').glob('*.md')` yields only `['README.md']` while `rglob('*.spec.md')` yields 38. Calling `resolve_spec` raised `No specification matching ... found` for a bare filename, for `pqsx96`, and for a full flat path. |
| F-8 | MEDIUM | The prior "make every spec reader recursive" sweep MISSED this site while asserting completeness, and nothing caught it because the symbol is untested. | Executed `y4bdoz` asserts "A package-wide grep ... finds exactly ONE non-recursive site, `specs.py:89`" (reviewed 2026-09-10). But `tools/agy_run.py` was added `1ca197c7` (2026-08-16) and packaged `4579ba87` (2026-08-28), both earlier. `grep -rn resolve_spec tests/` returns no match. |
| F-9 | MEDIUM | The correct fix shape for F-7 is already written down, so the follow-up item should cite it rather than re-derive it: `rglob` alone would ship a NEW bug. | `specs._spec_files`'s docstring: "Ignored-path filtering via `core.is_ignored_path` / `core.get_ignored_dirs` is coupled to this recursive walk: non-recursion previously masked the lack of an ignored-path filter". |
| F-10 | LOW | The tooling already treats full-path citations as hand-fix-only, but only on the RENAME path; a STATUS TRANSITION moves a spec with no such guard. | `artifact_rename.find_unrewritable_path_citations` exists and the mutation path fails closed on `--apply`: "cannot auto-rewrite. Fix it by hand, then retry." No equivalent call exists in `specs.py`'s status-move path (`grep -rn find_unrewritable_path_citations` matches only `artifact_rename.py`). |
| F-11 | LOW | The item carries NO release gate and `chore` is the correct kind for the work actually performed here. | The item's front matter has `- Work-Kind: chore` and no `- Blocks-Release:`; both live-source edits are to comment/help text and change no behavior. |

## Proposed changes (ordered, validatable)

1. Re-measure the three live-source citations and the executed-plan one at execution HEAD, noting the slug difference on the `aw-project-layout` target (E-01).
2. Repoint `agy_run.py`'s `--spec` example at the real `superseded/` path including its full slug (E-02).
3. Repoint `check_engine.py`'s I-07 provenance comment at the real `draft/` path, re-verifying or re-anchoring `:135` (E-03).
4. Add `tests/test_spec_path_citations.py`, scoped to package source, failing-first then passing (E-04).
5. Record the per-class census of deliberately unfixed citations in this plan at finalize (E-05).
6. File the `resolve_spec` non-recursive-glob bug as a separate release-gated backlog item (E-06).

## Deferred / out of scope (with reason)

- FIXING THE EXECUTED PLAN `u06zo2`'s FIVE CITATIONS: deliberately NOT done, and this is the backlog item's claim 2 closed as won't-fix rather than deferred. The contract forbids changing what an executed plan records, and F-3 shows the citation was correct when written, so an in-place rewrite would make a 2026-09-20 plan appear to cite a path first created on 2026-09-24. The contract does permit appending a dated `## Workflow history` pointer line; even that is NOT done here, because a pointer is only worth adding when it directs a reader to later work that supersedes something, and a stale directory prefix in a provenance citation whose target is trivially findable by id6 (`aw find specs 0zb1cd`-style resolution works) does not meet that bar. If review disagrees, adding the pointer is a one-line, contract-permitted change.
  - Carrier-Declined: This row records a WON'T-FIX, not an outstanding defect, so there is nothing for a carrier to carry onward. The citation was correct when written (F-3, proven by `git ls-tree` at `7c68a4e3`) and the executed-plan record is already in its correct terminal state; filing an item would create a permanent backlog entry whose only correct resolution is to close it unfixed.
- THE OTHER ~460 DANGLERS IN RECORD TREES: out of scope by class, with counts to be refreshed at finalize by E-05. `plans/executed/` (373) and `reviews/` (31) are immutable history. `tests/` (21) are intentional fixture paths under `tmp_path` that SHOULD NOT resolve in the real tree. Terminal non-executed plan dirs (14) are equally records. None of these is a debt: for a record, a citation that was correct when written is already in its correct terminal state.
  - Carrier-Declined: Same won't-fix reasoning at population scale, and for the `tests/` subset the citations are CORRECT AS WRITTEN (deliberate `tmp_path` fixture paths that must not resolve in the real tree), so "fixing" them would break the tests. Nothing here is an outstanding obligation, so no carrier is owed.
- FIXING `agy_run.resolve_spec`'s NON-RECURSIVE GLOB: out of scope here and FILED instead (E-06). It is a `bug` (Spec Mode resolves none of 38 specs), while this plan is a `chore` inherited from the item; folding a release-gated behavioral fix into a comment-repointing chore would hide it from the release gate and blow this plan's declared scope. The fix also is not one line (F-9: it needs the ignored-path filter alongside recursion), so it deserves its own plan.
  - Carrier-Declined: NOT because it needs no carrier - it is a real live bug and it DOES - but because its carrier cannot be cited at authoring time: a `- Carrier:` value must be a resolvable id6, and the item does not exist yet. THIS PLAN'S OWN E-06 CREATES IT, and V-06 refuses to pass without the pasted `aw backlog new` output, the item's `- Work-Kind: bug`, a `- Blocks-Release:` resolving to the `planned` release, and clean `aw check release-gates`. So the obligation cannot silently vanish at `executed`: the plan cannot reach `executed` until the durable carrier provably exists. A reviewer who prefers a cited id6 should have the item filed first and this field changed to `- Carrier: <id6>`.
- ADDING A CITATION GUARD TO THE SPEC STATUS-TRANSITION PATH (F-10): out of scope, not filed. The rename path's fail-closed guard has no equivalent on `aw specs set`'s move, which is plausibly why these rotted. Recorded as an observation rather than filed, because whether a status transition should REFUSE on a stale in-tree citation is a policy question with real cost (every transition would need to scan the tree, and most stale citations live in immutable records it must not touch), and that is a maintainer's call, not an author's. See OQ-01.
  - Carrier-Declined: No carrier because there is no agreed defect to carry: whether a status transition SHOULD refuse on a stale in-tree citation is an open policy question (OQ-01), and filing work for an undecided policy would presuppose the maintainer's answer. The observation is preserved in OQ-01, which carries the same declination and the reasoning behind it. If the maintainer decides the guard is wanted, that decision is the point at which an item should be filed.

## Scope check

- Over-scope: none. `agent_workflows/agy_run.py` holds the E-02 edit site (the `--spec` epilog example); `agent_workflows/check_engine.py` holds the E-03 edit site (the I-07 provenance comment); `tests/test_spec_path_citations.py` is the new E-04 test. E-01/E-05 are read-only measurement and this plan's own prose. E-06 writes a backlog item through `aw backlog new`, whose output path is tool-chosen under `.aw/records/backlog/open/`; that is a records-tree artifact created by the sanctioned verb rather than a hand edit, and it is deliberately not listed as a code scope path.
- Under-scope: the declared paths cover every code edit. NO spec file is touched, so no spec amendment is declared and none is required: both edits repoint a citation TO a spec, changing no contract. If E-01 finds a fourth dangler in package source, the E-04 test will fail on it too; fixing it is in this plan's spirit and in `agent_workflows/` scope, and must be reported at finalize.

## Required tests / validation

- `tests/test_spec_path_citations.py` run BEFORE the fixes, output pasted, FAILING and naming both live-source citations (falsifiability proof; a test that cannot fail proves nothing).
- The same test run AFTER the fixes, output pasted, passing.
- An existence check on the exact corrected path strings now present in `agy_run.py` and `check_engine.py`, so the fix is verified against the filesystem and not by eye.
- The full suite run BARE as `python3 -m pytest` (configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`; do not add `-n0`, a second `-q`, or `-p no:randomly`), with the `N passed` summary line pasted. `check_engine.py` is a heavily depended-upon module, so a comment-only edit there must still be proven inert.
- `aw check release-gates` after E-06, to prove the new `bug` item's release gate resolves to a real release record rather than dangling.
- `aw ipd lint --phase pre-transition` conforming before any terminal transition.

## Spec / documentation sync

N/A for spec amendment, with reason: this plan repoints two CITATIONS OF specs and amends no spec's content, so no `.spec.md` path is declared in `- Scope-Paths:` and the runners' declared-spec-edit announcement should report none. No user-facing documentation changes either: both edits are to an argparse epilog and an internal code comment. The one durable record this plan adds beyond its own finalize prose is the E-06 backlog item, which is the correct home for the `resolve_spec` bug and is created with `aw backlog new` rather than hand-named.

## Open questions

### OQ-01: Should `aw specs set`'s status-move warn on stale in-tree citations, as the rename path already fails closed on them?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: This question asks the maintainer to DECIDE a policy, and it owes no implementation work unless the answer is yes; filing a carrier now would presuppose that answer. The underlying observation is not at risk of vanishing silently: the asymmetry is recorded as finding F-10 with its evidence, and the CI-time regression test E-04 already covers the package-source half of what a transition-time guard would catch, which OQ-01 argues is the better layer anyway. If the maintainer answers yes, that answer is the trigger to file the work.
- Resolution or deferral rationale: DEFERRED TO THE MAINTAINER as a policy call, and deliberately NOT filed as work. The asymmetry is real and measured (F-10): `artifact_rename` surfaces full-path citations and fails closed on `--apply`, while a status transition moves a spec with no equivalent check, which is the mechanism that let these citations rot. But the obvious fix is not obviously right. A transition-time scan would have to walk the record trees on every `aw specs set`, and the overwhelming majority of what it would find (404 of 470) lives in immutable executed plans and reviews that the operator MUST NOT edit, so the guard would mostly emit warnings whose only correct response is to ignore them - which is how a warning becomes noise and trains operators to skip real ones. A narrower variant (warn only for citations in PACKAGE SOURCE and LIVE plans) is defensible and is roughly what E-04's test achieves at CI time instead, arguably the better layer. Not blocking: this plan's fixes and its regression test stand regardless of how the policy question is answered.

### OQ-02: Is splitting the `resolve_spec` bug out of this plan correct, rather than fixing it here?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, SPLIT IT OUT. Three reasons, each grounded rather than stylistic. FIRST, work-kind: the repository's rule is that user-perceptible impact makes a defect a `bug`, and a `--spec` mode resolving ZERO of 38 specs is total, user-facing breakage (F-7), whereas this plan inherits `- Work-Kind: chore` from item `ajomj3` for repointing comment strings. A live `bug` must carry `- Blocks-Release:`; absorbing it into an ungated chore would hide it from the release gate that exists to stop shipping known bugs. SECOND, size and shape: the fix is not a one-character `glob`->`rglob` swap. `specs._spec_files`'s own docstring records that non-recursion was MASKING the absence of an ignored-path filter, so recursion without `core.is_ignored_path` would start returning gitignored specs (F-9) - a new bug, and the exact trap the earlier sweep documented. THIRD, scope honesty: `resolve_spec` has zero test coverage (F-8), so a correct fix needs real tests, which is a different deliverable from a comment repoint and would blow this plan's declared scope. E-06 therefore files it with the measurement, the fix precedent, and the reason the `y4bdoz` audit missed it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of an existence check on all four measured paths at execution HEAD (the two stale source-cited paths shown ABSENT, the two real paths shown PRESENT), plus the `grep -n` hit showing `u06zo2` still carries the bare citation, plus the recorded HEAD sha. Must explicitly state whether the real `aw-project-layout` filename still carries the `-storage-wizard-and-state` slug, since E-02 depends on it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `grep -n 'agy_run.py --spec' agent_workflows/agy_run.py` showing the new path, AND a pasted existence check (for example `ls` or `test -f`) on the exact path string now in the file, proving it resolves. A diff of the line alone is insufficient: the failure being prevented is citing a plausible path that does not exist.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `grep -n` showing `check_engine.py`'s corrected I-07 citation, a pasted existence check on that exact path, AND pasted output of reading the anchored line (for example `sed -n '<N>p' <path>`) showing it is the `I-07` / `Release-gate preservation` row, proving the anchor was re-verified rather than copied. If the anchor was dropped in favor of a content anchor, paste the line as written and state why.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: TWO pasted runs of `tests/test_spec_path_citations.py`: the BEFORE run failing and naming both live-source citations in its failure output, and the AFTER run passing. Plus the pasted `N passed` summary line from a bare `python3 -m pytest` full-suite run. Plus the test's docstring quoted, showing the package-source bound is justified by the fixture-path and immutable-record reasons. A pass-only run is NOT acceptable evidence: without the failing run the test is not shown to be falsifiable.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted scan output produced at execution HEAD showing per-class counts, and the resulting census text as written into this plan's "Deferred / out of scope" section. Counts must be from the execution-HEAD run, not copied from this plan's authoring numbers; if they differ from 470/373/31/21/14/2, the new numbers stand and the difference is noted.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `aw backlog new ...` invocation and its output naming the created item path; pasted front matter of the created item showing `- Work-Kind: bug` and a `- Blocks-Release:` value that resolves to the `planned` release record; pasted `aw check release-gates` output showing no dangling-gate finding for it; and confirmation that `agy_run.resolve_spec` itself was NOT modified by this plan (for example a pasted `git diff` of `agent_workflows/agy_run.py` showing only the epilog example line changed).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; it carries no `- Readiness:` field, whose absence is the correct unattested state (an author must never write that field, since it is `/plan-review`'s output and a hand-written value would forge a review that did not happen).

Execution contract: commit only the paths this plan declares, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and a co-worker's restored path can otherwise enter the commit. Do not create a tag or release.

TWO PROHIBITIONS SPECIFIC TO THIS PLAN, both of which an executor is likely to violate while trying to be helpful. FIRST, DO NOT EDIT `.aw/records/plans/executed/20260908-lcpolicy-01-u06zo2-...ipd.md`, nor any other file under `plans/executed/` or `reviews/`, even though the E-04 test's subject matter makes those citations conspicuous and even though the backlog item names one of them: the contract forbids it and F-3 shows the citation was correct when written. SECOND, DO NOT FIX `agy_run.resolve_spec` while inside `agy_run.py` for E-02; the non-recursive glob is a real bug sitting a few hundred lines from the edit site, and it is E-06's job to FILE it, not this plan's job to fix it. Touching it would put an ungated `bug` fix inside a `chore`.

Post-gate lifecycle: after every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, transition this plan with the sanctioned verb (`aw ipd set executed <plan>`), never by hand-editing `- Status:` or by `git mv`. The backlog item `ajomj3` is set to `graduated` by the runner upon verification; this plan must not set it `done`.
