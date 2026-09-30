# IPD: Re-point ARCHITECTURE.md's two retired repo-root run-scratch references and restore the guard that was supposed to stop them

- Date: 2026-09-28
- Kind: child
- Concern: TWO USER-FACING ROOT DOCS STILL TEACH THE RETIRED REPO-ROOT RUN-SCRATCH PATH, AND THE GUARD THE BACKLOG ITEM EXPECTED TO EXTEND NO LONGER EXISTS. Backlog `21ct62` reported `ARCHITECTURE.md` naming a bare `workflow-artifacts/` in two places, both re-measured at this lane's HEAD `93a20264` and both still present: the run-directory section states `Every run creates `workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped;` and calls that directory `the authoritative record`, and the installer section states pruning `never touches` `` `workflow-artifacts/` run records, user code, or `.aw/records/`.`` `CONTRIBUTING.md` carries a THIRD occurrence the item did not report, in the wheel-boundary bullet `contains only the package + `_data` tree and NONE of `tests/`, `workflow-artifacts/`,`. Spec `20260817-2124-01` (`u7xtni`, Order 07) relocated run scratch to `.aw/workflow-artifacts/`, which is the ONLY path the framework-owned ignore protects, so a reader who follows these sentences creates run scratch at a path a fresh target repo does not ignore. MEASURED, not assumed: a throwaway repo installed from this lane with `install-workflows.py` reports `git check-ignore -v --no-index -- workflow-artifacts/probe` EXIT 1 (nothing ignores it) while `.aw/workflow-artifacts/probe` matches `.aw/.gitignore:75  /workflow-artifacts/`. Run records carry absolute home paths and session detail, so an unignored run tree is the D92 leak the relocation exists to prevent. SECOND, AND NOT IN THE ITEM: the guard the item's suggested fix says to extend is GONE. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) DELETED `tests/test_docs.py` entire (472 lines), taking with it `_bare_run_scratch_refs`, `ShippedRunScratchPathTests` and `ShippedRunScratchGuardFalsifiabilityTests`, the nine tests wfartifacts Order 03 (`9x1rps`) added precisely so its 86-reference sweep could not decay. `ls tests/test_docs.py` reports no such file and `rg bare_run_scratch tests/` returns nothing. The shipped tree measures CLEAN today (0 bare occurrences under `.aw/system/`), so this is latent rather than active, but the regression pin Order 03's own plan called "the regression pin: without it, the rewrite decays exactly as Order 07's did" is not protecting anything.
- Scope: IN: (a) re-point the two `ARCHITECTURE.md` occurrences to `.aw/workflow-artifacts/`; (b) correct the SAME PARAGRAPH's stale tracking claim, `File-based state makes runs recoverable, auditable, committable, and`, which D117 inverted and which would leave the section still teaching the pre-relocation policy after a path-only edit; (c) re-point the one `CONTRIBUTING.md` occurrence, which must be clean before any guard can cover the root docs; (d) restore the deleted run-scratch path guard as a new focused test file, widened from the shipped-workflow tree alone to ALSO cover `docs/` and the root user-facing docs, the last DERIVED as a glob minus an explicitly reasoned exclusion constant rather than enumerated (corrected at review, PR-701), with a non-emptiness assertion PER SURFACE (PR-702); (e) prove the guard fails per surface and on each allowed spelling, in a THROWAWAY COPY of the tree rather than by mutating tracked files (PR-703); (f) VERIFY the two already-existing carrier items for the adjacent findings this plan deliberately does not fix, creating nothing new. OUT: `DECISIONS.md` (40 occurrences) and `CHANGELOG.md` (5), which are DATED HISTORICAL RECORDS where a past decision legitimately names the path it then used (D19 literally decided the repo-root location), and which are the exclusion constant's only two entries; `tools/README.md` (5) and `tools/untrack-workflow-artifacts.py`, owned by pending plan `cf7f8z` and today carrying the bare spelling correctly because its SUBJECT is the retired path, for the same reason `scan_secrets.py`'s `SKIP_DIR_NAMES` entry is deliberately bare (note, per F-12, that the file is UNREACHABLE by any of this guard's three surfaces, so it gets NO exclusion entry); every other class deleted from `tests/test_docs.py` (docs-exist, dash, support-table, model-profile, benchmark-threshold, analytics-privacy), whose restoration is its own decision; the dangling `tests/test_packaging.py` reference in the CONTRIBUTING.md sentence being edited; any production code change; `.aw/records/` history.
- Scope-Paths: ARCHITECTURE.md, CONTRIBUTING.md, tests/test_run_scratch_path_guard.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 21ct62
- Blocks-Release: next
- Set: wfartgrowth
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: fzueyy
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): status set to reviewed

- 2026-09-28 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701 through PR-709 (all FIXED, none deferred). Reviewed at HEAD `086df9f2`; `aw ipd lint` conforming at `--phase author` before revision and `--phase review-finalize` after. EVERY MEASURED CLAIM IN THE PLAN REPRODUCED, including the D92 leak premise re-verified by installing this tree into a throwaway repo (`git check-ignore` exit 1 on the retired path, matching `.aw/.gitignore:75` on the live one). The findings concern the GUARD'S SHAPE, not the diagnosis: review built the guard and ran it against a copy of the tree, finding that an enumerated root-doc allowlist passes after `ARCHITECTURE.md` is renamed away (PR-701) and that one shared scanned-counter passes with `docs/` removed entirely (PR-702), both the same silent-decay class this plan exists to repair; that E-05's falsification wrote to tracked files in a shared checkout (PR-703); and that a mechanical restoration would carry four unused production imports into a file the plan declares free of them (PR-704). Review then ran the corrected design green over all three surfaces and red once per surface, in temporary copies, touching no tracked file. Three LOW evidence and consistency defects were also fixed: a collected baseline already 120 tests stale, a collect command using the wrong marker expression, an `rg` pattern that escaped its alternation pipe and could never match, and a `Proposed changes` line instructing the executor to file backlog items that E-06 forbids. A scope fence and approval summary were added (PR-709). Both open questions UPHELD with `Owner` corrected from `none` to `plan author`. Findings recorded in `.aw/records/reviews/20260928-wfartgrowth-01-fzueyy-re-point-architecture-md-s-two-retired-repo-root-run-scratch.review.md`.
- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `21ct62`, inheriting its `- Blocks-Release: next` gate and its `bug` / `medium` classification. Both reported occurrences re-measured present at HEAD `93a20264`. TWO FINDINGS THE ITEM DID NOT CARRY, both measured: `CONTRIBUTING.md` holds a third occurrence, and the guard the item proposes extending (`tests/test_docs.py`, `ShippedRunScratchPathTests`) was DELETED WHOLE by `19313eed`, so the plan restores it rather than extending it. The D92 premise was verified by installing into a throwaway repo and asking git, not inferred: the retired path is unignored there (exit 1) while the live path matches `.aw/.gitignore:75`.
- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

The user-facing root documentation names only the live `.aw/workflow-artifacts/` run-scratch path and states its correct local-only tracking policy, and a restored, falsifiable guard fails the suite if any shipped workflow body, `docs/` page, or user-facing root doc reintroduces the retired repo-root spelling.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: repair the user-facing prose

- [x] E-01 RE-POINT THE TWO `ARCHITECTURE.md` OCCURRENCES to `.aw/workflow-artifacts/`. Locate them by CONTENT, not by the offsets quoted here: the run-directory section's `Every run creates `workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped;` under the heading `### State: the authoritative run directory`, and the installer section's `` `workflow-artifacts/` run records, user code, or `.aw/records/`.`` following `Pruning is strictly scoped to the framework namespace`. Write the prefixed spelling exactly as the shipped bodies do (`.aw/workflow-artifacts/`), and re-read the result for the doubled-prefix hazard Order 03 recorded as its finding F-5: a substitution applied twice yields `.aw/.aw/workflow-artifacts/`. Do NOT touch `ARCHITECTURE.md`'s sentence about the legacy `repository-review/` migration if one is present nearby; D120 examined that sentence and VERIFIED IT CORRECT, because it describes a git-mv of a directory whose history genuinely moved.
  - Depends on: none
  - Expected outcome: `grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md` returns NOTHING, `grep -c '\.aw/workflow-artifacts/' ARCHITECTURE.md` returns 2, and `grep -n '\.aw/\.aw/' ARCHITECTURE.md` returns nothing.
  - Execution state: performed

- [x] E-02 CORRECT THE SAME PARAGRAPH'S STALE TRACKING CLAIM, `File-based state makes runs recoverable, auditable, committable, and`, which sits three lines below the first E-01 occurrence inside the same `**Why externalize state to files:**` paragraph. THIS IS IN SCOPE FOR A NAMED REASON, not opportunism: D117 INVERTED the tracking policy (run records became local-only and gitignored), and D120 exists ONLY because the D117 sweep left exactly this class of residue behind, five separate prose defects that each still called run artifacts committed deliverables and had to be repaired by a later corrective IPD. Fixing the path while leaving the adjacent word `committable` would hand the next reader a section that names the right directory and then invites them to commit it, which is the same D92 leak by a different sentence. Replace the stale property with the true one (the run record is recoverable, auditable and LOCAL-ONLY / never committed), keeping the sentence's `enables fresh-context phase isolation` clause and its `DECISIONS.md` D7 citation intact, and keeping the prose free of em and en dashes as the user-facing convention requires. IF A REVIEWER JUDGES THIS OVER-SCOPE, it is severable: E-01 and the guard stand without it, and this item can be cut to a backlog entry instead.
  - Depends on: E-01
  - Expected outcome: the paragraph no longer asserts run records are committable, still cites D7, still carries the phase-isolation clause, and introduces no unicode dash (`python3 -c` over `docs_check.check_no_unicode_dashes` on the file reports no finding).
  - Execution state: performed

- [x] E-03 RE-POINT THE ONE `CONTRIBUTING.md` OCCURRENCE, in the wheel-boundary bullet whose text is `contains only the package + `_data` tree and NONE of `tests/`, `workflow-artifacts/`,`. This is a PREREQUISITE, not an extra: the guard in E-04 covers the user-facing root docs, so leaving this occurrence alive would make the guard fail on a tree this plan declares clean. CHANGE ONLY THE PATH. The same sentence also names `tests/test_packaging.py`, which `19313eed` DELETED (`ls tests/test_packaging.py` reports no such file), so the bullet additionally claims enforcement by a test that does not exist; that is a DIFFERENT defect with a different owner and it is filed in E-06 rather than fixed here, because deciding what the wheel boundary is enforced by now is a packaging question, not a path question.
  - Depends on: none
  - Expected outcome: `grep -rnoP '(?<![/\w-])workflow-artifacts/' CONTRIBUTING.md` returns NOTHING, the bullet still reads as a list of excluded top-level entries, and the `tests/test_packaging.py` mention is left exactly as it was.
  - Execution state: performed

### Task group 2: restore the guard, widened

- [x] E-04 RESTORE THE DELETED GUARD AS `tests/test_run_scratch_path_guard.py`, WIDENED TO THE DOC SURFACES. Recover the helper and both classes from before the trim with `git show 19313eed^:tests/test_docs.py` and take ONLY `_bare_run_scratch_refs`, `ShippedRunScratchPathTests` and `ShippedRunScratchGuardFalsifiabilityTests`; every other class in that file is out of scope. Keep `_bare_run_scratch_refs` BYTE-FOR-BYTE, including its docstring: it already encodes, with reasons, the three spellings that must NOT match (any slash-preceded form, which subsumes the live `.aw/` path and the anchored `.aw/.gitignore` pattern `/workflow-artifacts/`; the installer template filename `workflow-artifacts-README.md`; and the bare path SEGMENT in `scan_secrets.py`'s `SKIP_DIR_NAMES`, which must stay bare because that set is matched per segment). Follow the restorecov precedent (`6vozur`) for the shape of a restoration: a module docstring stating that this is the guard `19313eed` deleted, which plan restored it and why. THEN WIDEN THE SWEPT SURFACE from the shipped tree alone to three surfaces, each enumerated in the test so a reader can see what is covered: (1) `.aw/system/workflows/**/*.{md,py}` excluding `__pycache__`, exactly as before, since that sweep is ALSO unguarded today; (2) `docs/**/*.md`; (3) the user-facing root docs, derived as GLOB-MINUS-EXCLUSIONS per the paragraph below. Keep the doubled-prefix assertion (`.aw/.aw/`) over every swept file. NOTE FOR A REVIEWER WEIGHING THIS AGAINST THE SRCGUARD RULING: the maintainer's 2026-09-26 ruling forbids tests that pin PRODUCTION SOURCE text or structure, and plan `96xtmi` explicitly placed tests that read NON-production files (specs, workflow bodies, READMEs) OUTSIDE that census. This guard reads documentation content only and never `agent_workflows/*`, so it is not the class that ruling retired.

    THE RECOVERED HELPER AND CLASSES NEED EXACTLY FOUR FREE NAMES, MEASURED AT REVIEW, NOT THREE AND NOT SEVEN (PR-704, F-10). The sibling review of `cf7f8z` found a restoration recipe that produced 13 `NameError`s because the recovered class closed over module-level helpers the plan never named, so review ran the same AST free-variable pass here rather than assume: `_bare_run_scratch_refs` closes over `re`; `ShippedRunScratchPathTests` over `REPO_ROOT`, `_bare_run_scratch_refs` and `unittest`; `ShippedRunScratchGuardFalsifiabilityTests` over `_bare_run_scratch_refs` and `unittest`. So the needed imports are `re`, `unittest`, and `REPO_ROOT`. Take `REPO_ROOT` from `tests.support` (`from tests.support import REPO_ROOT`), which defines it identically as `Path(__file__).resolve().parent.parent` and is the repository's shared convention, rather than re-deriving it. Do NOT carry the deleted file's other imports (`docs_check as dc`, `docs_render as dr`, `host_adapters as ha`, `host_capability_registry as hcr`, `Path`): none of the three recovered symbols references any of them, so carrying them would ship unused imports that imply dependencies this guard does not have AND would make a file the plan declares free of production-source reads import three production modules.

    THE ROOT-DOC SURFACE IS A GLOB MINUS A REASONED EXCLUSION CONSTANT, NOT AN ENUMERATED ALLOWLIST (PR-701, F-11). An allowlist of seven filenames DECAYS SILENTLY, which is the exact failure class this plan exists to repair: measured at review by renaming `ARCHITECTURE.md` in a scratch copy, an enumerated sweep guarded by `if not p.is_file(): continue` reported `scanned=6 offenders=[]` and PASSED, having silently stopped covering the file this plan is named after, while a `root.glob("*.md")` sweep minus the exclusion set picked the renamed file up. A new root doc is likewise covered by default under the glob and invisible to an allowlist. So build the surface as `sorted(REPO_ROOT.glob("*.md"))` filtered by a named exclusion constant, and assert the derived surface is NON-EMPTY. THE EXCLUSION CONSTANT IS PART OF THE DELIVERABLE and must carry a one-line reason per entry, because a silent omission is indistinguishable from a bug: `DECISIONS.md` and `CHANGELOG.md` are dated historical records where a past entry legitimately names the path it then used (D19 decided the repo-root location; rewriting it would falsify the record). Review measured that the glob-minus-exclusions form yields exactly `AGENTS.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES.md`, `README.md`, `RELEASING.md`, `TODO.md`, identical to the allowlist this item previously carried, so the change costs no coverage today and only removes the decay mode. DO NOT put `tools/README.md` in the exclusion constant: it is not a root `*.md`, not under `docs/`, and not under `.aw/system/workflows/`, so no surface reaches it and an entry naming it would be an inert line asserting a fact the structure already provides. That also dissolves the cross-plan reconciliation `cf7f8z`'s review raised in its PR-B02 (see F-12): with no `tools/README.md` entry there is no stale reason for either landing order to reconcile.

    COUNT THE SCANNED FILES PER SURFACE, NEVER IN ONE SHARED TOTAL (PR-702, F-11). The recovered `test_no_bare_run_scratch_path_in_shipped_bodies` asserts `self.assertTrue(scanned, "no shipped bodies were scanned")`, which is the right instinct on ONE surface and becomes a hole on three: measured at review by moving `docs/` aside in a scratch copy, a single shared counter reported `scanned=160` and PASSED while the `docs/` surface contributed ZERO files and was silently unguarded. Assert non-emptiness PER SURFACE (three separate assertions, or one parameterized over a mapping of surface name to paths), and name the surface in every failure message so a red run says which surface the offender is on.

    BUILD THE SWEEP AS A ROOT-PARAMETERIZED FUNCTION, because E-05 depends on it (PR-703). Express the three surfaces and the sweep as a helper taking the tree root as an argument (defaulting to `REPO_ROOT`), not as methods that hard-code `REPO_ROOT` internally. Review verified the whole guard, green and red, against a scratch copy of the tree this way; without the parameter E-05 has no way to prove a red run except by editing tracked files in a shared checkout.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a new test file whose sweep passes over all three surfaces on the post-E-03 tree, asserting a non-empty scanned count PER SURFACE (not one shared total) so a vanished surface cannot pass silently; the root-doc surface derived as `glob("*.md")` minus a named exclusion constant carrying a per-entry reason, with no `tools/README.md` entry; the only imports are `re`, `unittest` and `REPO_ROOT` from `tests.support`; the sweep is root-parameterized; nothing under `agent_workflows/` is imported or read.
  - Execution state: performed

- [x] E-05 PROVE THE GUARD CAN FAIL, per surface and per allowed spelling, WITHOUT MUTATING A TRACKED FILE. A guard that cannot fail proves nothing, which is why Order 03's own validation demanded the same thing. Poison ONE file of EACH of the three surfaces IN TURN (a shipped workflow body, a `docs/` page, `ARCHITECTURE.md`) and confirm the sweep fails, NAMES that file with its occurrence count, and NAMES THE SURFACE, while the other two surfaces stay green. Also keep the recovered falsifiability cases green (two-references-on-one-line, the live prefixed path, the anchored gitignore pattern, the template filename, the bare segment used as code) and add one NEW case asserting an EXCLUDED file is genuinely excluded by the exclusion constant rather than by accident, by feeding the sweep a fixture that names an excluded path and showing no finding.

    DO THE POISONING IN A THROWAWAY COPY OF THE TREE, NOT IN THE CHECKOUT (PR-703, F-13). The method this item previously carried, "reintroduce ONE bare reference ... and revert immediately, verifying with `git status --short`", writes to a TRACKED file in a checkout `AGENTS.md` states other agents and humans may be using concurrently, and its safety rests on a revert the plan cannot guarantee runs (a failing assertion, a timeout, or an interrupted turn leaves the poison in place, and `git status --short` is then read AFTER the damage rather than preventing it). Because E-04 now requires the sweep to be root-parameterized, the honest method costs nothing: copy the three surfaces into a temporary directory (`shutil.copytree` ignoring `__pycache__`, under `tempfile.TemporaryDirectory`), poison the copy, and call the sweep with that root. Review PERFORMED this, and it is the evidence F-13 rests on: green over the post-fix tree at `shipped: scanned=153, docs: scanned=28, root-docs: scanned=7`, then three separate reds, each naming exactly its own file and surface while the other two stayed green, with no tracked file written at any point. PREFER ENCODING THIS AS A PERMANENT TEST rather than as a one-off manual probe: a falsification that lives in the test file runs on every future suite run, whereas one performed once at execution time protects nothing afterwards. The recovered `ShippedRunScratchGuardFalsifiabilityTests` already works this way at string level; the temp-tree cases extend the same discipline to the sweep itself.
  - Depends on: E-04
  - Expected outcome: three red results, one per surface, each naming its file, occurrence count and surface while the other two surfaces stay green, produced against a temporary copy with `git status --short` EMPTY throughout (not restored afterwards, never dirtied); every recovered falsifiability case passes; the exclusion case passes.
  - Execution state: performed

### Task group 3: file what this plan does not fix

- [x] E-06 VERIFY, DO NOT RE-FILE, THE TWO CARRIED OBLIGATIONS. NOTE THE SCOPE CONSEQUENCE, CORRECTED AT REVIEW (PR-708, F-15): because this item creates nothing, `.aw/records/backlog/open/` was REMOVED from `- Scope-Paths:`, since a declared-but-unmodified path is exactly what `aw ipd finalize` refuses to complete without a `--scope-ack` for, and acknowledging a path the plan never intended to write is noise rather than a reconciliation. BOTH ITEMS ALREADY EXIST: backlog `2jz47s` (`CONTRIBUTING.md` attributes the wheel ship-vs-dev boundary to `tests/test_packaging.py`, which `19313eed` deleted along with `tests/test_run_analytics_packaging.py`, so the doc promises a boundary nothing asserts, and `agent_workflows/run_analytics_spa.py` still cites that file in a user-visible message) and backlog `gzmr54` (the six remaining classes `19313eed` deleted from `tests/test_docs.py` are unrestored, leaving `agent_workflows/docs_check.py` and `docs_render.py` with no test caller at all). They were filed AT AUTHORING TIME rather than left to the executor because `check.ipd-uncarried-obligation` is an `error`-severity rule that refuses a `- Carrier:` naming an id6 that does not resolve, so a plan cannot honestly defer work to an item that does not exist yet. DO NOT CREATE A SECOND PAIR. This item's whole deliverable is verification: confirm both ids still resolve under `.aw/records/backlog/`, confirm each Deferred row's `- Carrier:` cites the right one, and confirm this plan did NOT quietly do their work. THE PROHIBITION IS THE OTHER HALF, and it is the part an executor can violate: the temptation on reading `2jz47s` is to delete or rewrite the stale `tests/test_packaging.py` attribution while already editing that sentence, and the temptation on reading `gzmr54` is to restore one more cheap-looking class while already creating a test file. Do neither. If the executor believes either is warranted, the correct move is to say so and stop.
  - Depends on: E-03
  - Expected outcome: both ids resolve, both Deferred rows cite the correct carrier, and `git diff` shows no change to the `tests/test_packaging.py` mention and no restored class beyond the run-scratch guard.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE PATH-REFERENCE REGEX IS ALREADY SETTLED AND MUST BE REUSED, not re-derived. `_bare_run_scratch_refs` (recoverable from `git show 19313eed^:tests/test_docs.py`) is `re.findall(r"(?<![/\w-])workflow-artifacts/", text)`, and its docstring records why each non-match is deliberate. The unit is OCCURRENCES, not lines (Order 03 finding F-8): a line-based sweep under-reports a line carrying two references and then reports itself complete.
- A BARE SPELLING IS SOMETIMES CORRECT, so a blanket ban would be wrong. `scan_secrets.py`'s `SKIP_DIR_NAMES` holds single path SEGMENTS matched by `set(rel_posix.split("/")) & SKIP_DIR_NAMES`, and its comment states the prefixed spelling "could match NOTHING and would silently stop excluding run records". The `.aw/.gitignore` pattern is likewise written `/workflow-artifacts/` because patterns there are `.aw/`-relative, and that file's own comment explains the anchoring as protection against a bare pattern matching at any depth (the trap that once swallowed the tracked `records/comms/shared/inbox/` lane).
- THE LIVE PATH HAS ONE SOURCE OF TRUTH IN CODE: `set_records.RUN_ARTIFACTS_SUBDIR = ".aw/workflow-artifacts"` and `engine.ARTIFACTS_DIR = ".aw/workflow-artifacts/"`, with `engine.RETIRED_ROOT_ARTIFACTS_DIR = "workflow-artifacts/"` kept deliberately separate so the migration can still find what an already-installed repo carries.
- EXECUTED RECORDS ARE NOT EDITED IN PLACE (D156, and the execution contract). That is why `DECISIONS.md` and `CHANGELOG.md` are excluded from the guard rather than swept: correcting a dated entry would rewrite what the record says happened.
- THE SUITE RUNS BARE, AND ITS MARKER EXPRESSION IS `not slow and not livecorpus`, NOT `not slow` (corrected at review, PR-706). `pyproject.toml`'s `[tool.pytest.ini_options] addopts` reads `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; a `-m "not slow"` reproduction therefore collects a DIFFERENT, larger set (measured at review: 3242 collected / 200 deselected under `-m "not slow"` versus 3237 / 205 under the real expression), so a delta computed with the wrong marker is off by the five `livecorpus` tests before this plan changes anything.
- DO NOT TRANSCRIBE A COLLECTED TOTAL AS AN ACCEPTANCE BAR (PR-705). The figure this plan was authored with, `3122/3322 (200 deselected)`, had ALREADY DRIFTED to `3237/3442 (205 deselected)` when review measured it, 120 tests in a few days, and the same failure mode was recorded three times in the sibling plans of this sweep (drifts of 60, 138 and 93). A collected count is a LIVE population, so the bar is the PROPERTY (the rise equals the number of tests this plan adds) with the baseline RE-DERIVED at execution time; any number written here is context only and is already stale.
- A NEW TEST FILE MUST BE PROVEN COLLECTED, not merely proven passing when named directly. Plan `6vozur`'s review (PR-701) restored a file under a non-conforming name and the bare suite reported an unchanged, fully green run with all six tests uncollected.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| F-1 | MEDIUM | `ARCHITECTURE.md` names the retired repo-root path twice, once while calling that directory "the authoritative record" | `grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md` returns two occurrences, in `Every run creates `workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped;` and in `` `workflow-artifacts/` run records, user code, or `.aw/records/`.`` |
| F-2 | MEDIUM | The retired path is genuinely UNIGNORED in a fresh target repo, so F-1 is a D92 leak route and not cosmetic | measured by installing this lane's `install-workflows.py` into a throwaway git repo: `git check-ignore -v --no-index -- workflow-artifacts/probe` EXITS 1 with no output, while `.aw/workflow-artifacts/probe` matches `.aw/.gitignore:75  /workflow-artifacts/` |
| F-3 | LOW | This repo's own root `.gitignore` carries a bare `workflow-artifacts/` (a D117-era artifact), so the leak lands on a TARGET repo reader rather than on a reader working inside this checkout | `git check-ignore -v --no-index -- workflow-artifacts/probe` in this worktree matches `.gitignore:52  workflow-artifacts/`; the fresh install in F-2 has no such line. Stated so the item's claim is not overread |
| F-4 | MEDIUM | `CONTRIBUTING.md` carries a THIRD occurrence, unreported by the backlog item, and it must be fixed for any root-doc guard to pass | `grep -rnoP '(?<![/\w-])workflow-artifacts/' CONTRIBUTING.md` returns one occurrence, in `contains only the package + `_data` tree and NONE of `tests/`, `workflow-artifacts/`,` |
| F-5 | HIGH | The guard the item's suggested fix says to EXTEND does not exist: `19313eed` deleted `tests/test_docs.py` entire, including all nine run-scratch guard tests Order 03 added as its regression pin | `git show 19313eed --stat` lists `tests/test_docs.py | 472 ---`; `ls tests/test_docs.py` reports no such file; `rg bare_run_scratch tests/` returns nothing; the symbols are still recoverable from `git show 19313eed^:tests/test_docs.py` |
| F-6 | LOW | The shipped tree the deleted guard protected measures CLEAN today, so F-5 is latent rather than active | `grep -rhoP '(?<![/\w-])workflow-artifacts/' .aw/system/ \| wc -l` returns 0; `docs/` returns 0 |
| F-7 | LOW | The paragraph holding F-1's first occurrence also asserts run records are "committable", which D117 inverted and D120 was created to sweep out of five other places | `ARCHITECTURE.md` reads `File-based state makes runs recoverable, auditable, committable, and`; D120 in `DECISIONS.md` records correcting exactly this class of residue, naming five prose defects that still called run artifacts committed deliverables |
| F-8 | LOW | The `CONTRIBUTING.md` sentence being edited also attributes enforcement to a deleted test, a second defect in one sentence | `ls tests/test_packaging.py` reports no such file; `git show 19313eed --stat` lists it at `503 ---`; `agent_workflows/run_analytics_spa.py` still cites it in a user-visible message |
| F-9 | LOW | `agent_workflows/docs_check.py` and `docs_render.py` have no test caller at all after the trim, so the doc-check engine itself is unexercised | `rg -l 'docs_check\|docs_render' tests/` returns nothing (CORRECTED AT REVIEW, PR-707: as originally written the pattern escaped the alternation pipe, so it searched for the LITERAL string `docs_check\|docs_render` and would have returned nothing even had callers existed; review confirmed the claim holds under the correct `rg -l 'docs_check\|docs_render'` alternation, verified by running both forms against a file that does contain `docs_check`). Both modules are imported only by the deleted `tests/test_docs.py` and, for the gate name, `agent_workflows/release_readiness.gate_docs_checks` |
| F-10 | MEDIUM | ADDED AT REVIEW (PR-704). The restoration recipe named no dependency set, the same gap that cost `cf7f8z`'s recipe 13 `NameError`s. Review ran an AST free-variable pass: the three recovered symbols close over `re`, `unittest`, `REPO_ROOT` and each other, and NONE of the deleted file's four production-module imports (`docs_check`, `docs_render`, `host_adapters`, `host_capability_registry`) is referenced | `_bare_run_scratch_refs: free = ['re']`; `ShippedRunScratchPathTests: free = ['REPO_ROOT', '_bare_run_scratch_refs', 'unittest']`; `ShippedRunScratchGuardFalsifiabilityTests: free = ['_bare_run_scratch_refs', 'unittest']`; `tests/support.py` defines `REPO_ROOT = Path(__file__).resolve().parent.parent`, identical to the deleted file's own derivation |
| F-11 | MEDIUM | ADDED AT REVIEW (PR-701, PR-702). Two silent-decay holes in the guard's shape as specified, each measured in a scratch copy. An ENUMERATED seven-filename root-doc allowlist plus `if not p.is_file(): continue` PASSES after `ARCHITECTURE.md` is renamed away, reporting `scanned=6 offenders=[]`; and ONE SHARED `scanned` counter across three surfaces PASSES at `scanned=160` when `docs/` vanishes entirely | rename probe: enumerated sweep `scanned=6 offenders=[]` PASS while a `glob("*.md")`-minus-exclusions sweep picked the renamed file up at `scanned=7`; docs-removal probe: `docs surface scanned=0` yet combined `scanned=160` PASS. Measured equivalence today: glob-minus-exclusions yields exactly the seven names the allowlist carried |
| F-12 | LOW | ADDED AT REVIEW. The cross-plan reconciliation `cf7f8z`'s review raised as its PR-B02 does NOT arise, because no surface this guard sweeps reaches `tools/README.md` and the corrected exclusion constant names no such entry, so there is no stale reason for either landing order to fix | `tools/README.md` is not a root `*.md`, not under `docs/`, not under `.aw/system/workflows/`; `cf7f8z`'s E-05 records the ordering obligation on the premise that `fzueyy`'s exclusion constant would name the file and carry a reason its rewrite invalidates |
| F-13 | MEDIUM | ADDED AT REVIEW (PR-703). E-05's falsification method wrote a bare reference into a TRACKED file in a shared checkout and relied on a revert the plan cannot guarantee runs. Review performed the whole falsification against a temporary copy instead, proving the safe method is available and sufficient | green over the post-fix tree at `shipped: scanned=153, docs: scanned=28, root-docs: scanned=7`; three reds against separate temp copies, each naming only its own file and surface (`.aw/system/workflows/plan-review/plan-review.md`, `docs/architecture.md`, `ARCHITECTURE.md`) while the other two surfaces stayed green; no tracked file written |
| F-14 | LOW | ADDED AT REVIEW (PR-705, PR-706). The plan's transcribed collected baseline had drifted 120 tests by review, and the command it prescribes uses the WRONG marker expression, collecting a set five tests larger than the bare suite does | authored baseline `3122/3322 (200 deselected)` versus measured `3237/3442 (205 deselected)` at HEAD `086df9f2`; `pyproject.toml` `addopts` reads `-m 'not slow and not livecorpus'` while the plan's command passes `-m "not slow"`, measured at `3242/3442 (200 deselected)` |
| F-15 | LOW | ADDED AT REVIEW. The plan's `- Scope-Paths:` declares `.aw/records/backlog/open/`, but E-06 (as revised at authoring) creates NOTHING there: both carrier items already exist and the item's whole deliverable is verification. A declared-but-unmodified path is what `aw ipd finalize` demands a `--scope-ack` for | `- Scope-Paths: ARCHITECTURE.md, CONTRIBUTING.md, tests/test_run_scratch_path_guard.py, .aw/records/backlog/open/` beside E-06's `DO NOT CREATE A SECOND PAIR` and its expected outcome `both ids resolve`; both files present under `.aw/records/backlog/open/` already |

## Proposed changes (ordered, validatable)

1. Re-point `ARCHITECTURE.md`'s two occurrences to `.aw/workflow-artifacts/`, checking for the doubled-prefix hazard (E-01).
2. Correct the same paragraph's `committable` claim so the section stops teaching the pre-D117 tracking policy (E-02).
3. Re-point `CONTRIBUTING.md`'s one occurrence, leaving its separate deleted-test claim untouched (E-03).
4. Restore the deleted guard as `tests/test_run_scratch_path_guard.py`, widened to the shipped tree plus `docs/` plus the root user-facing docs, the last derived as a glob minus a reasoned exclusion constant, with a non-emptiness assertion PER SURFACE (E-04).
5. Prove the guard fails per surface, in a temporary copy rather than in the checkout, and that each allowed spelling and each exclusion is honored by design (E-05).
6. VERIFY (not re-file) the two already-existing carrier items `2jz47s` and `gzmr54`, and confirm this plan did neither of their jobs (E-06). Corrected at review, PR-708: this line previously read "File backlog items", contradicting E-06's own `DO NOT CREATE A SECOND PAIR` instruction, which is exactly the residue a reader acts on.

## Deferred / out of scope (with reason)

- `DECISIONS.md` (40 occurrences) and `CHANGELOG.md` (5). These are dated historical records. D19 decided the repo-root location and D117 through D120 record its inversion; a sweep would rewrite what those entries say happened, which the executed-record rule (D156) forbids in spirit and which would destroy the provenance a future reader needs to understand why the path moved.
  - Carrier-Declined: Nothing is owed. These files are CORRECT as they stand: a dated entry naming the path that decision then used is accurate history, not stale documentation, so there is no outstanding work to carry. Filing an item would schedule the falsification of a record.
- `tools/README.md` (5 occurrences) and `tools/untrack-workflow-artifacts.py`. The tool's SUBJECT is the retired repo-root directory, and its `ARTIFACTS = "workflow-artifacts"` constant is what makes it able to find one. The bare spelling is correct there for the same reason `scan_secrets.py`'s segment entry is.
  - Carrier-Declined: Nothing is owed. The bare spelling is load-bearing here, exactly as `scan_secrets.py`'s `SKIP_DIR_NAMES` comment records for its own entry: prefixing it would break the tool's ability to find what it migrates. There is no defect behind this row.
- The rest of `tests/test_docs.py`. Restoring six further unrelated test classes is a separate decision with its own risk and its own count impact (F-9).
  - Carrier: gzmr54
- The dangling `tests/test_packaging.py` attribution in the sentence E-03 edits. Deciding what enforces the wheel boundary now is a packaging question, not a path question (F-8).
  - Carrier: 2jz47s
- Any change to `agent_workflows/`. F-8 notes a stale citation inside `run_analytics_spa.py`, which is production code and outside this plan's declared paths.
  - Carrier: 2jz47s

## Scope check

- Over-scope: E-02 and E-03 edit prose the backlog item did not name. Both are argued, not assumed: E-03 is a hard PREREQUISITE, because the guard this plan restores covers the user-facing root docs and would fail on the `CONTRIBUTING.md` occurrence; E-02 sits inside the very paragraph E-01 edits and is the residue class D120 was created to sweep, so leaving it would ship a section that names the right path and then invites the reader to commit it. E-02 is explicitly marked severable if a reviewer disagrees.
- Under-scope: the guard covers documentation surfaces only. It does not assert anything about `agent_workflows/`, deliberately, because the maintainer's 2026-09-26 ruling retired tests that pin production source. RECORDED AT REVIEW SO THE LIMIT IS NOT OVERREAD: `agent_workflows/engine.py` carries twelve bare occurrences today and EVERY ONE IS CORRECT, because each names the retired path AS ITS SUBJECT (`RETIRED_ROOT_ARTIFACTS_DIR = "workflow-artifacts/"`, the migration docstrings that describe moving off it, and the `.aw/.gitignore` comments explaining why the live pattern is anchored). So the exclusion of production source costs no real coverage here and is not a gap a later plan should "close"; a guard over `engine.py` would report twelve false positives on its first run.
- Under-scope, accepted: `tools/README.md`'s five occurrences remain unguarded by any surface. That is correct while plan `cf7f8z` owns that file, and after its E-05 rewrite the file would measure clean, at which point a later plan may choose to widen the guard's surface to `tools/`. This plan does not, because widening onto a file another pending plan is actively rewriting would collide.

## Required tests / validation

- `grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md CONTRIBUTING.md` returns NOTHING, and `grep -rn '\.aw/\.aw/'` over both returns nothing.
- The new guard passes over all three surfaces, reports a nonzero scanned-file count for each, and FAILS when a bare reference is reintroduced into any one of them.
- Every recovered falsifiability case passes, plus the new exclusion case.
- The new file is PROVEN COLLECTED by the bare suite, not merely by naming it directly. RE-DERIVE THE BASELINE FIRST on the pre-change tree, then measure the post-change count, using the REAL marker expression: `python3 -m pytest --collect-only -q -o addopts="" -m "not slow and not livecorpus" | tail -1`. The BAR IS THE PROPERTY, that the rise equals exactly the number of tests this plan adds; the figures `3237/3442 (205 deselected)` measured at review on 2026-09-28 are CONTEXT ONLY and will have drifted (the plan was authored against `3122/3322`, already 120 tests stale by review). A count that fails to rise means the file was not collected, which is the `6vozur` failure this check exists to catch.
- `python3 -m pytest` BARE, judged on the FAILURE-SET DELTA against clean HEAD rather than on counts, since this lane's environment can fail lifecycle tests for reasons unrelated to this change.
- `aw sanitize --agent` before treating any pasted output as shareable.

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and that is a measured conclusion rather than an omission. Spec `20260817-2124-01` (`u7xtni`, implemented) already RULES that run scratch lives at `.aw/workflow-artifacts/`; this plan brings two documents into line with a contract that is already correct, so there is no contract to change. No `.spec.md` file appears in `- Scope-Paths:`, which is what the runners' spec-edit announcement and the finalize scope gate reconcile against.
- `ARCHITECTURE.md` and `CONTRIBUTING.md` ARE the documentation deliverable here; both are declared in `- Scope-Paths:`.
- No `CHANGELOG.md` entry is proposed: the user-visible behavior does not change, and the file is also an excluded historical surface for this plan's guard.

## Open questions

### OQ-01: Should the root-doc guard also cover `AGENTS.md`, given that its content is regenerated from managed blocks in `engine.py`?

- Blocking: no
- Status: resolved
- Owner: plan author (UPHELD at review by the reviewer; the maintainer was not asked, and `Owner` was corrected from `none` per the `/plan-review` rule that a resolved question records who chose)
- Resolution or deferral rationale: YES, include it, and after PR-701 the question is largely MOOT BY CONSTRUCTION: the root-doc surface is now `glob("*.md")` minus a two-entry exclusion constant, so `AGENTS.md` is covered because it is a root markdown file and not because anyone listed it. `AGENTS.md` measures clean today (0 occurrences, re-measured at review), so inclusion costs nothing now, and it is the single most-read agent-facing file in a target repo, so a retired path appearing there would be the highest-leverage version of this defect. The regeneration concern is real but points the same way, and review MEASURED which direction: `engine.py` carries twelve bare occurrences, every one correctly naming the retired path as its subject, and NONE of them reaches the emitted managed-block prose (`AGENTS.md` is clean). So if a future managed block ever did emit the bare spelling, a failing guard on `AGENTS.md` is exactly the signal wanted, and the fix would be in the emitting constant rather than in the generated file.

### OQ-02: Does restoring a deleted guard conflict with the intent of the suite trim `19313eed`?

- Blocking: no
- Status: resolved
- Owner: plan author (UPHELD at review; `Owner` corrected from `none` for the same reason as OQ-01)
- Resolution or deferral rationale: No, and there is direct precedent. The `restorecov` Set (`6vozur`, `dmxc5h`) restored outcome tests that the same commit deleted, on the reasoning that the trim removed coverage whose loss was not itself decided. This restoration is narrower: roughly seven tests, reading documentation content only, never `agent_workflows/*`, and therefore outside the census that plan `96xtmi` built for the maintainer's no-source-pinning ruling. VERIFIED AT REVIEW, not assumed: an AST free-variable pass over the three recovered symbols shows they reference only `re`, `unittest`, `REPO_ROOT` and each other, so the restored file imports no production module at all (F-10), and the sweep asserts on file CONTENT rather than on any code structure. The plan still reports the exact count delta so the cost is visible rather than asserted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md` returning NOTHING, and paste the BEFORE run showing the two occurrences so the change is visible as a delta rather than asserted. Paste `grep -n '\.aw/workflow-artifacts/' ARCHITECTURE.md` showing exactly two prefixed hits, and `grep -n '\.aw/\.aw/' ARCHITECTURE.md` returning nothing. Quote both rewritten sentences in full, since a path swap that mangles the surrounding prose passes a regex and fails a reader.
  - Observed evidence: grep before/after output, prefixed counts, and quoted sentences:
    BEFORE:
    ```
    $ grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md
    ARCHITECTURE.md:147:workflow-artifacts/
    ARCHITECTURE.md:201:workflow-artifacts/
    ```

    AFTER:
    ```
    $ grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md
    (empty, exit 1)

    $ grep -n '\.aw/workflow-artifacts/' ARCHITECTURE.md
    147:Every run creates `.aw/workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped;
    201:`.aw/workflow-artifacts/` run records, user code, or `.aw/records/`.

    $ grep -n '\.aw/\.aw/' ARCHITECTURE.md
    (empty, exit 1)
    ```

    Rewritten sentence 1 (line 147):
    "Every run creates `.aw/workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped; `release-review` for the runbook)."

    Rewritten sentence 2 (lines 199-201):
    "Pruning is strictly scoped to the framework namespace (`.aw/system/workflows/` plus generated shim files) and never touches `.aw/workflow-artifacts/` run records, user code, or `.aw/records/`."
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: quote the rewritten `**Why externalize state to files:**` paragraph in full and state plainly that it no longer claims run records are committable, that it still cites D7, and that it still carries the phase-isolation clause. Paste the output of running `agent_workflows.docs_check.check_no_unicode_dashes` over the file (or `check_doc`) showing no dash finding, since this is user-facing prose.
  - Observed evidence: rewritten state paragraph and unicode dash check output:
    Rewritten paragraph in full:
    ```markdown
    **Why externalize state to files:** long multi-step LLM runs degrade when state lives
    only in context. File-based state makes runs recoverable, auditable, local-only (never
    committed), and enables fresh-context phase isolation. This is a load-bearing
    architectural decision (see `DECISIONS.md` D7).
    ```
    Verification of requirements:
    1. No longer claims run records are committable: replaced with `local-only (never committed)`.
    2. Still cites D7: `(see `DECISIONS.md` D7)`.
    3. Still carries the phase-isolation clause: `and enables fresh-context phase isolation`.

    Unicode dash check:
    ```
    $ python3 -c 'from pathlib import Path; from agent_workflows import docs_check as dc; print(dc.check_no_unicode_dashes(Path("ARCHITECTURE.md").read_text("utf-8"), "ARCHITECTURE.md"))'
    []
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `grep -rnoP '(?<![/\w-])workflow-artifacts/' CONTRIBUTING.md` returning NOTHING, plus the BEFORE run showing the one occurrence. Quote the rewritten bullet and CONFIRM EXPLICITLY that its `tests/test_packaging.py` mention is unchanged, since this item's whole discipline is changing one thing in a sentence that carries two defects.
  - Observed evidence: grep before/after output and quoted bullet with packaging test unchanged:
    BEFORE:
    ```
    $ grep -rnoP '(?<![/\w-])workflow-artifacts/' CONTRIBUTING.md
    CONTRIBUTING.md:251:workflow-artifacts/
    ```

    AFTER:
    ```
    $ grep -rnoP '(?<![/\w-])workflow-artifacts/' CONTRIBUTING.md
    (empty, exit 1)

    $ grep -n '\.aw/workflow-artifacts/' CONTRIBUTING.md
    251:  contains only the package + `_data` tree and NONE of `tests/`, `.aw/workflow-artifacts/`,

    $ grep -n '\.aw/\.aw/' CONTRIBUTING.md
    (empty, exit 1)
    ```

    Rewritten bullet in full:
    ```markdown
    - **Build a wheel:** `python -m build --wheel` (needs `pip install build`). The
      ship-vs-dev boundary is enforced by `tests/test_packaging.py`, which asserts the wheel
      contains only the package + `_data` tree and NONE of `tests/`, `.aw/workflow-artifacts/`,
      the source `.aw/records/` tree (docs, plans, prompts), or the meta docs, and that no runtime
      dependency is declared.
    ```
    Confirmation: `tests/test_packaging.py` mention is completely unchanged.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new file's module docstring and its exclusion constant with the per-entry reasons, and CONFIRM the constant contains no `tools/README.md` entry (F-12). Paste `git show 19313eed^:tests/test_docs.py | sed -n '/def _bare_run_scratch_refs/,/^class ShippedRunScratchPathTests/p'` beside the restored helper to show it was recovered BYTE-FOR-BYTE rather than retyped. Paste the guard passing, INCLUDING A SEPARATE scanned-file count for EACH of the three surfaces, and paste the three per-surface non-emptiness assertions themselves, since F-11 measured that one shared counter passes while a whole surface is silently empty. Paste the file's complete import block and show it is exactly `re`, `unittest` and `REPO_ROOT` from `tests.support`, with NO `docs_check`, `docs_render`, `host_adapters` or `host_capability_registry` carried over (F-10). Paste `rg 'agent_workflows' tests/test_run_scratch_path_guard.py` and account for every hit, or show none, so the no-production-source property is demonstrated rather than claimed. SHOW THE ROOT-DOC SURFACE IS DERIVED, not enumerated: paste the derivation expression and the seven filenames it yields on today's tree.
  - Observed evidence: module docstring, exclusion constant, helper comparison, and test counts:
    Module docstring:
    ```python
    """Restored and widened run-scratch path guard.

    This is the regression guard deleted by `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"),
    restored under plan `fzueyy` (Set `wfartgrowth`).

    Order 07 (spec `20260817-2124-01`) moved run scratch from a repo-root `workflow-artifacts/` to
    `.aw/workflow-artifacts/`. Order 03 (`9x1rps`) added the original regression guard in `tests/test_docs.py`
    to prevent recurrence of the D92 leak (where unignored run records carrying sensitive home paths and
    session detail could be created).

    Under plan `fzueyy`, this guard is restored and widened from the shipped workflow tree alone to three
    surfaces:
    1. Shipped workflow bodies: `.aw/system/workflows/**/*.{md,py}` excluding `__pycache__`.
    2. Documentation pages: `docs/**/*.md`.
    3. Root user-facing docs: `*.md` in repository root, derived via glob minus an explicit exclusion constant.
    """
    ```

    Exclusion constant with per-entry reasons:
    ```python
    ROOT_DOC_EXCLUSIONS: dict[str, str] = {
        "DECISIONS.md": "Dated historical record; past decisions (e.g. D19) legitimately name the path in use at the time.",
        "CHANGELOG.md": "Dated historical record; past release notes legitimately name the path in use at the time.",
    }
    ```
    Confirmation: `ROOT_DOC_EXCLUSIONS` contains no `tools/README.md` entry.

    Byte-for-byte comparison of recovered helper against 19313eed^:tests/test_docs.py:
    ```python
    def _bare_run_scratch_refs(text: str) -> list[str]:
        """Return every BARE `workflow-artifacts/` PATH reference in ``text``.

        THE UNIT IS OCCURRENCES, NOT LINES (wfartifacts Order 03, finding F-8): some lines carry
        two references, so a line-based sweep under-reports and reports itself complete while
        references remain.

        THREE SPELLINGS ARE DELIBERATELY NOT MATCHED, because none of them is a stale path:

        1. `.aw/workflow-artifacts/` - the live, correct path (the negative lookbehind).
        2. `/workflow-artifacts/` as the ANCHORED GITIGNORE PATTERN. Patterns in the
           framework-owned `.aw/.gitignore` are `.aw/`-relative, so the pattern that ignores run
           scratch is written `/workflow-artifacts/` and a body naming it is CORRECT. Any
           slash-preceded form is therefore allowed, which subsumes case 1.
        3. `workflow-artifacts-README.md`, the installer TEMPLATE FILENAME under
           `.aw/system/workflows/templates/` (a hyphen, not a slash, follows), plus the bare
           segment name in `assess/tools/scan_secrets.py`'s `SKIP_DIR_NAMES` (no trailing slash),
           which must stay bare because that set is matched per path SEGMENT.
        """

        return re.findall(r"(?<![/\w-])workflow-artifacts/", text)
    ```
    Verification script:
    `Original length: 1246; Restored length: 1246; Identical byte-for-byte: True`

    Guard passing on current tree with per-surface counts:
    ```
    shipped: scanned=154, offenders=[]
    docs: scanned=28, offenders=[]
    root-docs: scanned=7, offenders=[]
    ```

    Per-surface non-emptiness assertions:
    ```python
    self.assertTrue(
        results["shipped"]["scanned"] > 0,
        "no files were scanned for surface 'shipped'",
    )
    self.assertTrue(
        results["docs"]["scanned"] > 0,
        "no files were scanned for surface 'docs'",
    )
    self.assertTrue(
        results["root-docs"]["scanned"] > 0,
        "no files were scanned for surface 'root-docs'",
    )
    ```

    Complete import block of tests/test_run_scratch_path_guard.py:
    ```python
    import re
    import unittest

    from tests.support import REPO_ROOT
    ```
    (NO `docs_check`, `docs_render`, `host_adapters`, or `host_capability_registry` carried over)

    No production source reads:
    ```
    $ rg 'agent_workflows' tests/test_run_scratch_path_guard.py
    (empty, exit 1)
    ```

    Root-doc surface derivation expression:
    ```python
    def _root_docs(root=REPO_ROOT):
        for path in sorted(root.glob("*.md")):
            if path.name not in ROOT_DOC_EXCLUSIONS:
                yield path
    ```
    Filenames yielded on today's tree (7 files):
    `['AGENTS.md', 'ARCHITECTURE.md', 'CONTRIBUTING.md', 'GUIDING_PRINCIPLES.md', 'README.md', 'RELEASING.md', 'TODO.md']`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste THREE separate FAILING results, one per surface (a shipped workflow body, a `docs/` page, `ARCHITECTURE.md`), each showing the guard naming the file, its occurrence count AND its surface, and each also showing the other two surfaces still GREEN so the failure is proven localized. State explicitly that the poisoning was done in a TEMPORARY COPY and paste `git status --short` showing the checkout was never dirtied (an EMPTY status throughout, not a status that is clean again after a revert, per F-13). Paste the falsifiability cases passing, and paste the new exclusion case together with the fixture it was given, so "excluded by design" is shown rather than inferred from a green sweep. State whether the three temp-tree cases were encoded as PERMANENT tests or performed as one-off probes, and if the latter, say why the guard's own falsification is not itself guarded.
  - Observed evidence: three temp-tree falsification runs, clean git status, and pytest output:
    Three separate failing results (in temporary copies, checkout never dirtied):

    Probe 1: Shipped workflow body poisoned (.aw/system/workflows/plan-review/plan-review.md):
    ```
    Surface shipped (scanned=154): ['.aw/system/workflows/plan-review/plan-review.md: 1 bare reference(s)']
    Surface docs (scanned=28): GREEN
    Surface root-docs (scanned=7): GREEN
    ```

    Probe 2: Docs page poisoned (docs/architecture.md):
    ```
    Surface shipped (scanned=154): GREEN
    Surface docs (scanned=28): ['docs/architecture.md: 1 bare reference(s)']
    Surface root-docs (scanned=7): GREEN
    ```

    Probe 3: Root-doc poisoned (ARCHITECTURE.md):
    ```
    Surface shipped (scanned=154): GREEN
    Surface docs (scanned=28): GREEN
    Surface root-docs (scanned=7): ['ARCHITECTURE.md: 1 bare reference(s)']
    ```

    Checkout status:
    The poisoning was performed strictly inside temporary copies created via `tempfile.TemporaryDirectory()` and never in the tracked working tree. `git status --short` was never dirtied by any test poisoning throughout:
    ```
    $ git status --short
     M ARCHITECTURE.md
     M CONTRIBUTING.md
    ?? tests/test_run_scratch_path_guard.py
    ```

    Falsifiability cases passing (10 passed):
    ```
    $ python3 -m pytest -v tests/test_run_scratch_path_guard.py -k Falsifiability
    ============================== 10 passed in 3.98s ==============================
    ```

    New exclusion case and fixture:
    ```python
    def test_sweep_honors_root_doc_exclusions(self):
        tmpdir, tmp = self._create_temp_tree()
        self.addCleanup(tmpdir.cleanup)
        # Poison an excluded root doc with a bare run scratch reference
        target = tmp / "DECISIONS.md"
        target.write_text(target.read_text(encoding="utf-8") + "\nworkflow-artifacts/\n", encoding="utf-8")
        results = sweep_surfaces(tmp)
        self.assertTrue(results["root-docs"]["scanned"] > 0)
        self.assertEqual(results["root-docs"]["offenders"], [])
    ```

    Permanent vs probe choice:
    The three temp-tree falsification cases were encoded as PERMANENT tests (`test_sweep_detects_poisoned_shipped_body`, `test_sweep_detects_poisoned_docs_page`, `test_sweep_detects_poisoned_root_doc`) in `ShippedRunScratchGuardFalsifiabilityTests`, so the sweep's falsification is continuously guarded on every test run.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `aw find backlog 2jz47s` and `aw find backlog gzmr54` (or the equivalent `ls`) showing both ids RESOLVE, and paste each item's metadata block. Quote the two `- Carrier:` lines from this plan's Deferred section beside them so the pairing is visible rather than asserted. Paste `git diff -- CONTRIBUTING.md` and state explicitly that the `tests/test_packaging.py` mention is untouched, and paste `git status --short` showing the only new test file is the run-scratch guard, so the two prohibitions are demonstrated and not merely promised. Confirm no third backlog item was created. SEPARATELY, paste the suite evidence this plan's contract requires: RE-DERIVE the collected baseline on the pre-change tree and measure it again after, both with the REAL marker expression `python3 -m pytest --collect-only -q -o addopts="" -m "not slow and not livecorpus" | tail -1` (F-14: the `-m "not slow"` form this plan originally prescribed collects five extra tests, and the transcribed `3122/3322` baseline was already 120 tests stale at review). Judge on the PROPERTY, that the rise equals the number of tests this file adds, and state both figures you measured rather than comparing against any number written in this plan. Then paste the BARE `python3 -m pytest` runs for this tree and for clean HEAD with the failure-set delta named as EMPTY. Do not paste a count-only claim: name the failing node sets, or state that both are empty.
  - Observed evidence: carrier resolution, prohibitions check, collection delta, and test runs:
    Backlog carrier resolution:
    ```
    $ aw find backlog 2jz47s
    ◕  open          2jz47s  .aw/records/backlog/open/20260928-2jz47s-01-2jz47s-contributing-cites-deleted-packaging-test.backlog.md

    Metadata block for 2jz47s:
    - Id: 2jz47s
    - Status: open
    - Set: 2jz47s
    - Priority: medium
    - Work-Kind: followup
    - Summary: CONTRIBUTING.md attributes the wheel ship-vs-dev boundary to tests/test_packaging.py, which commit 19313eed deleted, so nothing asserts that boundary

    $ aw find backlog gzmr54
    ◕  open          gzmr54  .aw/records/backlog/open/20260928-gzmr54-01-gzmr54-restore-remaining-test-docs-classes.backlog.md

    Metadata block for gzmr54:
    - Id: gzmr54
    - Status: open
    - Set: gzmr54
    - Priority: medium
    - Work-Kind: followup
    - Summary: The six remaining test classes commit 19313eed deleted from tests/test_docs.py are unrestored, leaving agent_workflows/docs_check.py and docs_render.py with no test caller at all
    ```

    Deferred carrier pairing from plan Deferred section:
    Line 131: - Carrier: gzmr54
    Line 133: - Carrier: 2jz47s

    Prohibitions verified:
    ```
    $ git diff -- CONTRIBUTING.md
    -  contains only the package + `_data` tree and NONE of `tests/`, `workflow-artifacts/`,
    +  contains only the package + `_data` tree and NONE of `tests/`, `.aw/workflow-artifacts/`,
    ```
    (The `tests/test_packaging.py` attribution in that sentence is completely untouched)

    $ git status --short shows only the declared files and no third backlog item:
    ```
    M ARCHITECTURE.md
    M CONTRIBUTING.md
    M .aw/records/plans/pending/20260928-wfartgrowth-01-fzueyy-re-point-architecture-md-s-two-retired-repo-root-run-scratch.ipd.md
    ?? tests/test_run_scratch_path_guard.py
    ```

    Test suite collection measurement:
    Pre-change baseline:
    `3324/3531 tests collected (207 deselected) in 34.32s`
    Post-change:
    `3338/3545 tests collected (207 deselected) in 1.63s`
    Rise: exactly +14 tests collected (3324 -> 3338, 3531 -> 3545), matching the 14 tests in tests/test_run_scratch_path_guard.py.

    Bare pytest runs:
    Clean HEAD:
    `3322 passed, 2 skipped, 3 warnings in 179.77s (0:02:59)`
    Failing node set at clean HEAD: empty (0 failing tests).
    Post-change:
    `3336 passed, 2 skipped, 3 warnings in 192.90s (0:03:12)`
    Failing node set post-change: empty (0 failing tests).
    Failure-set delta: EMPTY.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN WOULD BE APPROVING. Three prose edits and one new test file. `ARCHITECTURE.md` stops naming a retired run-scratch directory in two sentences (one of which calls it "the authoritative record") and stops calling run records "committable" in the adjoining paragraph; `CONTRIBUTING.md` stops naming it in one wheel-boundary bullet; and a deleted regression guard returns as `tests/test_run_scratch_path_guard.py`, widened from the shipped workflow tree to also cover `docs/` and the root user-facing docs. NO PRODUCTION CODE CHANGES and no user-visible behavior changes. The leak premise was MEASURED, not inferred: in a repo freshly installed from this tree, `git check-ignore` exits 1 on the retired path (nothing ignores it) and matches `.aw/.gitignore:75` on the live one, so a reader following the current sentences writes run records, which carry absolute home paths and session detail, to an unignored path. THE ONE JUDGEMENT A HUMAN MAY WANT TO OVERRULE is E-02, the `committable` correction: it edits a word the backlog item did not name, it is argued from D117/D120 rather than from the item, and the plan marks it severable, so cutting it to a backlog entry leaves E-01 and the guard standing.

SCOPE FENCE (a DECLARATION for the runner to reconcile against, not a stop directive). Modify exactly `ARCHITECTURE.md`, `CONTRIBUTING.md` and the new `tests/test_run_scratch_path_guard.py`, which is what `- Scope-Paths:` declares. Specifically DO NOT: touch `DECISIONS.md` or `CHANGELOG.md` (dated records; a sweep would falsify history); touch `tools/README.md` or `tools/untrack-workflow-artifacts.py` (owned by plan `cf7f8z`, and the bare spelling is load-bearing there today); restore any further class from the deleted `tests/test_docs.py` (carrier `gzmr54`); repair the `tests/test_packaging.py` attribution in the very bullet E-03 edits (carrier `2jz47s`); change anything under `agent_workflows/`; write to `.aw/records/backlog/` (both carriers already exist, and E-06 only verifies them); or edit any file to produce a red run in E-05, which now uses a temporary copy. An out-of-scope edit that proves NECESSARY is made and then JUSTIFIED with `aw ipd finalize --scope-reason`, not avoided by stopping.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped, through `aw commit <plan> -- <paths>`; never `git add -A`, never `git commit -a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash and restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result that was not run. Re-locate every symbol and every quoted sentence by CONTENT rather than by the offsets cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not on counts. Run `aw sanitize --agent` before treating any pasted output as shareable. This plan carries `- Blocks-Release: next`, inherited from backlog `21ct62`.

POST-GATE LIFECYCLE. Human approval is required before execution. On completion, `aw ipd lint --phase pre-transition` must report conforming and every `V-*` item must carry pasted evidence before the plan moves to `.aw/records/plans/executed/`. If a validation item cannot be satisfied, leave the plan in `pending/` and report the blocker; do not weaken an item to make it pass.
