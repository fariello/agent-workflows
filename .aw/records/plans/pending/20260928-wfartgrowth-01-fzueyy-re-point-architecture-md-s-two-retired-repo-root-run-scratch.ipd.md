# IPD: Re-point ARCHITECTURE.md's two retired repo-root run-scratch references and restore the guard that was supposed to stop them

- Date: 2026-09-28
- Kind: child
- Concern: TWO USER-FACING ROOT DOCS STILL TEACH THE RETIRED REPO-ROOT RUN-SCRATCH PATH, AND THE GUARD THE BACKLOG ITEM EXPECTED TO EXTEND NO LONGER EXISTS. Backlog `21ct62` reported `ARCHITECTURE.md` naming a bare `workflow-artifacts/` in two places, both re-measured at this lane's HEAD `93a20264` and both still present: the run-directory section states `Every run creates `workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped;` and calls that directory `the authoritative record`, and the installer section states pruning `never touches` `` `workflow-artifacts/` run records, user code, or `.aw/records/`.`` `CONTRIBUTING.md` carries a THIRD occurrence the item did not report, in the wheel-boundary bullet `contains only the package + `_data` tree and NONE of `tests/`, `workflow-artifacts/`,`. Spec `20260817-2124-01` (`u7xtni`, Order 07) relocated run scratch to `.aw/workflow-artifacts/`, which is the ONLY path the framework-owned ignore protects, so a reader who follows these sentences creates run scratch at a path a fresh target repo does not ignore. MEASURED, not assumed: a throwaway repo installed from this lane with `install-workflows.py` reports `git check-ignore -v --no-index -- workflow-artifacts/probe` EXIT 1 (nothing ignores it) while `.aw/workflow-artifacts/probe` matches `.aw/.gitignore:75  /workflow-artifacts/`. Run records carry absolute home paths and session detail, so an unignored run tree is the D92 leak the relocation exists to prevent. SECOND, AND NOT IN THE ITEM: the guard the item's suggested fix says to extend is GONE. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) DELETED `tests/test_docs.py` entire (472 lines), taking with it `_bare_run_scratch_refs`, `ShippedRunScratchPathTests` and `ShippedRunScratchGuardFalsifiabilityTests`, the nine tests wfartifacts Order 03 (`9x1rps`) added precisely so its 86-reference sweep could not decay. `ls tests/test_docs.py` reports no such file and `rg bare_run_scratch tests/` returns nothing. The shipped tree measures CLEAN today (0 bare occurrences under `.aw/system/`), so this is latent rather than active, but the regression pin Order 03's own plan called "the regression pin: without it, the rewrite decays exactly as Order 07's did" is not protecting anything.
- Scope: IN: (a) re-point the two `ARCHITECTURE.md` occurrences to `.aw/workflow-artifacts/`; (b) correct the SAME PARAGRAPH's stale tracking claim, `File-based state makes runs recoverable, auditable, committable, and`, which D117 inverted and which would leave the section still teaching the pre-relocation policy after a path-only edit; (c) re-point the one `CONTRIBUTING.md` occurrence, which must be clean before any guard can cover the root docs; (d) restore the deleted run-scratch path guard as a new focused test file, widened from the shipped-workflow tree alone to ALSO cover `docs/` and the user-facing root docs, with an explicitly reasoned exclusion list; (e) prove the guard fails on a reintroduced reference and on each allowed spelling; (f) file backlog items for the two adjacent findings this plan deliberately does not fix. OUT: `DECISIONS.md` (40 occurrences) and `CHANGELOG.md` (5), which are DATED HISTORICAL RECORDS where a past decision legitimately names the path it then used (D19 literally decided the repo-root location); `tools/README.md` (5) and `tools/untrack-workflow-artifacts.py`, whose SUBJECT is the retired path, making the bare spelling correct there for the same reason `scan_secrets.py`'s `SKIP_DIR_NAMES` entry is deliberately bare; every other class deleted from `tests/test_docs.py` (docs-exist, dash, support-table, model-profile, benchmark-threshold, analytics-privacy), whose restoration is its own decision; the dangling `tests/test_packaging.py` reference in the CONTRIBUTING.md sentence being edited; any production code change; `.aw/records/` history.
- Scope-Paths: ARCHITECTURE.md, CONTRIBUTING.md, tests/test_run_scratch_path_guard.py, .aw/records/backlog/open/
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 21ct62
- Blocks-Release: next
- Set: wfartgrowth
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: fzueyy

## Workflow history

- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `21ct62`, inheriting its `- Blocks-Release: next` gate and its `bug` / `medium` classification. Both reported occurrences re-measured present at HEAD `93a20264`. TWO FINDINGS THE ITEM DID NOT CARRY, both measured: `CONTRIBUTING.md` holds a third occurrence, and the guard the item proposes extending (`tests/test_docs.py`, `ShippedRunScratchPathTests`) was DELETED WHOLE by `19313eed`, so the plan restores it rather than extending it. The D92 premise was verified by installing into a throwaway repo and asking git, not inferred: the retired path is unignored there (exit 1) while the live path matches `.aw/.gitignore:75`.
- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

The user-facing root documentation names only the live `.aw/workflow-artifacts/` run-scratch path and states its correct local-only tracking policy, and a restored, falsifiable guard fails the suite if any shipped workflow body, `docs/` page, or user-facing root doc reintroduces the retired repo-root spelling.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: repair the user-facing prose

- [ ] E-01 RE-POINT THE TWO `ARCHITECTURE.md` OCCURRENCES to `.aw/workflow-artifacts/`. Locate them by CONTENT, not by the offsets quoted here: the run-directory section's `Every run creates `workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped;` under the heading `### State: the authoritative run directory`, and the installer section's `` `workflow-artifacts/` run records, user code, or `.aw/records/`.`` following `Pruning is strictly scoped to the framework namespace`. Write the prefixed spelling exactly as the shipped bodies do (`.aw/workflow-artifacts/`), and re-read the result for the doubled-prefix hazard Order 03 recorded as its finding F-5: a substitution applied twice yields `.aw/.aw/workflow-artifacts/`. Do NOT touch `ARCHITECTURE.md`'s sentence about the legacy `repository-review/` migration if one is present nearby; D120 examined that sentence and VERIFIED IT CORRECT, because it describes a git-mv of a directory whose history genuinely moved.
  - Depends on: none
  - Expected outcome: `grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md` returns NOTHING, `grep -c '\.aw/workflow-artifacts/' ARCHITECTURE.md` returns 2, and `grep -n '\.aw/\.aw/' ARCHITECTURE.md` returns nothing.
  - Execution state: pending

- [ ] E-02 CORRECT THE SAME PARAGRAPH'S STALE TRACKING CLAIM, `File-based state makes runs recoverable, auditable, committable, and`, which sits three lines below the first E-01 occurrence inside the same `**Why externalize state to files:**` paragraph. THIS IS IN SCOPE FOR A NAMED REASON, not opportunism: D117 INVERTED the tracking policy (run records became local-only and gitignored), and D120 exists ONLY because the D117 sweep left exactly this class of residue behind, five separate prose defects that each still called run artifacts committed deliverables and had to be repaired by a later corrective IPD. Fixing the path while leaving the adjacent word `committable` would hand the next reader a section that names the right directory and then invites them to commit it, which is the same D92 leak by a different sentence. Replace the stale property with the true one (the run record is recoverable, auditable and LOCAL-ONLY / never committed), keeping the sentence's `enables fresh-context phase isolation` clause and its `DECISIONS.md` D7 citation intact, and keeping the prose free of em and en dashes as the user-facing convention requires. IF A REVIEWER JUDGES THIS OVER-SCOPE, it is severable: E-01 and the guard stand without it, and this item can be cut to a backlog entry instead.
  - Depends on: E-01
  - Expected outcome: the paragraph no longer asserts run records are committable, still cites D7, still carries the phase-isolation clause, and introduces no unicode dash (`python3 -c` over `docs_check.check_no_unicode_dashes` on the file reports no finding).
  - Execution state: pending

- [ ] E-03 RE-POINT THE ONE `CONTRIBUTING.md` OCCURRENCE, in the wheel-boundary bullet whose text is `contains only the package + `_data` tree and NONE of `tests/`, `workflow-artifacts/`,`. This is a PREREQUISITE, not an extra: the guard in E-04 covers the user-facing root docs, so leaving this occurrence alive would make the guard fail on a tree this plan declares clean. CHANGE ONLY THE PATH. The same sentence also names `tests/test_packaging.py`, which `19313eed` DELETED (`ls tests/test_packaging.py` reports no such file), so the bullet additionally claims enforcement by a test that does not exist; that is a DIFFERENT defect with a different owner and it is filed in E-06 rather than fixed here, because deciding what the wheel boundary is enforced by now is a packaging question, not a path question.
  - Depends on: none
  - Expected outcome: `grep -rnoP '(?<![/\w-])workflow-artifacts/' CONTRIBUTING.md` returns NOTHING, the bullet still reads as a list of excluded top-level entries, and the `tests/test_packaging.py` mention is left exactly as it was.
  - Execution state: pending

### Task group 2: restore the guard, widened

- [ ] E-04 RESTORE THE DELETED GUARD AS `tests/test_run_scratch_path_guard.py`, WIDENED TO THE DOC SURFACES. Recover the helper and both classes from before the trim with `git show 19313eed^:tests/test_docs.py` and take ONLY `_bare_run_scratch_refs`, `ShippedRunScratchPathTests` and `ShippedRunScratchGuardFalsifiabilityTests`; every other class in that file is out of scope. Keep `_bare_run_scratch_refs` BYTE-FOR-BYTE, including its docstring: it already encodes, with reasons, the three spellings that must NOT match (any slash-preceded form, which subsumes the live `.aw/` path and the anchored `.aw/.gitignore` pattern `/workflow-artifacts/`; the installer template filename `workflow-artifacts-README.md`; and the bare path SEGMENT in `scan_secrets.py`'s `SKIP_DIR_NAMES`, which must stay bare because that set is matched per segment). Follow the restorecov precedent (`6vozur`) for the shape of a restoration: a module docstring stating that this is the guard `19313eed` deleted, which plan restored it and why. THEN WIDEN THE SWEPT SURFACE from the shipped tree alone to three surfaces, each enumerated in the test so a reader can see what is covered: (1) `.aw/system/workflows/**/*.{md,py}` excluding `__pycache__`, exactly as before, since that sweep is ALSO unguarded today; (2) `docs/**/*.md`; (3) the user-facing root docs `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `RELEASING.md`, `GUIDING_PRINCIPLES.md`, `AGENTS.md`, `TODO.md`. THE EXCLUSIONS ARE PART OF THE DELIVERABLE and must be a named constant with a one-line reason each, because a silent omission is indistinguishable from a bug: `DECISIONS.md` and `CHANGELOG.md` are dated historical records where a past entry legitimately names the path it then used (D19 decided the repo-root location; rewriting it would falsify the record), and `tools/README.md` documents `tools/untrack-workflow-artifacts.py`, a migration tool whose subject IS the retired path. Keep the doubled-prefix assertion (`.aw/.aw/`) over every swept file. NOTE FOR A REVIEWER WEIGHING THIS AGAINST THE SRCGUARD RULING: the maintainer's 2026-09-26 ruling forbids tests that pin PRODUCTION SOURCE text or structure, and plan `96xtmi` explicitly placed tests that read NON-production files (specs, workflow bodies, READMEs) OUTSIDE that census. This guard reads documentation content only and never `agent_workflows/*`, so it is not the class that ruling retired.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a new test file whose sweep passes over all three surfaces on the post-E-03 tree, reporting the number of files scanned so a zero-file sweep cannot pass silently; the exclusion list is a named constant with per-entry reasons; nothing under `agent_workflows/` is read.
  - Execution state: pending

- [ ] E-05 PROVE THE GUARD CAN FAIL, per surface and per allowed spelling. A guard that cannot fail proves nothing, which is why Order 03's own validation demanded the same thing. Deliberately reintroduce ONE bare reference into ONE file of EACH of the three surfaces IN TURN (a shipped workflow body, a `docs/` page, and `ARCHITECTURE.md`), confirm the sweep fails and NAMES that file, and revert immediately, verifying with `git status --short` that nothing unintended remains. Also keep the recovered falsifiability cases green (two-references-on-one-line, the live prefixed path, the anchored gitignore pattern, the template filename, the bare segment used as code) and add one NEW case asserting an EXCLUDED file is genuinely excluded by the exclusion constant rather than by accident, by feeding the sweep a fixture that names an excluded path and showing no finding.
  - Depends on: E-04
  - Expected outcome: three separate red runs, each naming the file it was given, each reverted; every falsifiability case passes; the exclusion case passes.
  - Execution state: pending

### Task group 3: file what this plan does not fix

- [ ] E-06 VERIFY, DO NOT RE-FILE, THE TWO CARRIED OBLIGATIONS. BOTH ITEMS ALREADY EXIST: backlog `2jz47s` (`CONTRIBUTING.md` attributes the wheel ship-vs-dev boundary to `tests/test_packaging.py`, which `19313eed` deleted along with `tests/test_run_analytics_packaging.py`, so the doc promises a boundary nothing asserts, and `agent_workflows/run_analytics_spa.py` still cites that file in a user-visible message) and backlog `gzmr54` (the six remaining classes `19313eed` deleted from `tests/test_docs.py` are unrestored, leaving `agent_workflows/docs_check.py` and `docs_render.py` with no test caller at all). They were filed AT AUTHORING TIME rather than left to the executor because `check.ipd-uncarried-obligation` is an `error`-severity rule that refuses a `- Carrier:` naming an id6 that does not resolve, so a plan cannot honestly defer work to an item that does not exist yet. DO NOT CREATE A SECOND PAIR. This item's whole deliverable is verification: confirm both ids still resolve under `.aw/records/backlog/`, confirm each Deferred row's `- Carrier:` cites the right one, and confirm this plan did NOT quietly do their work. THE PROHIBITION IS THE OTHER HALF, and it is the part an executor can violate: the temptation on reading `2jz47s` is to delete or rewrite the stale `tests/test_packaging.py` attribution while already editing that sentence, and the temptation on reading `gzmr54` is to restore one more cheap-looking class while already creating a test file. Do neither. If the executor believes either is warranted, the correct move is to say so and stop.
  - Depends on: E-03
  - Expected outcome: both ids resolve, both Deferred rows cite the correct carrier, and `git diff` shows no change to the `tests/test_packaging.py` mention and no restored class beyond the run-scratch guard.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PATH-REFERENCE REGEX IS ALREADY SETTLED AND MUST BE REUSED, not re-derived. `_bare_run_scratch_refs` (recoverable from `git show 19313eed^:tests/test_docs.py`) is `re.findall(r"(?<![/\w-])workflow-artifacts/", text)`, and its docstring records why each non-match is deliberate. The unit is OCCURRENCES, not lines (Order 03 finding F-8): a line-based sweep under-reports a line carrying two references and then reports itself complete.
- A BARE SPELLING IS SOMETIMES CORRECT, so a blanket ban would be wrong. `scan_secrets.py`'s `SKIP_DIR_NAMES` holds single path SEGMENTS matched by `set(rel_posix.split("/")) & SKIP_DIR_NAMES`, and its comment states the prefixed spelling "could match NOTHING and would silently stop excluding run records". The `.aw/.gitignore` pattern is likewise written `/workflow-artifacts/` because patterns there are `.aw/`-relative, and that file's own comment explains the anchoring as protection against a bare pattern matching at any depth (the trap that once swallowed the tracked `records/comms/shared/inbox/` lane).
- THE LIVE PATH HAS ONE SOURCE OF TRUTH IN CODE: `set_records.RUN_ARTIFACTS_SUBDIR = ".aw/workflow-artifacts"` and `engine.ARTIFACTS_DIR = ".aw/workflow-artifacts/"`, with `engine.RETIRED_ROOT_ARTIFACTS_DIR = "workflow-artifacts/"` kept deliberately separate so the migration can still find what an already-installed repo carries.
- EXECUTED RECORDS ARE NOT EDITED IN PLACE (D156, and the execution contract). That is why `DECISIONS.md` and `CHANGELOG.md` are excluded from the guard rather than swept: correcting a dated entry would rewrite what the record says happened.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Collected baseline measured at this lane's HEAD: `3122/3322 tests collected (200 deselected)`.
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
| F-9 | LOW | `agent_workflows/docs_check.py` and `docs_render.py` have no test caller at all after the trim, so the doc-check engine itself is unexercised | `rg 'docs_check\|docs_render' tests/` returns nothing; both modules are imported only by the deleted `tests/test_docs.py` and, for the gate name, `agent_workflows/release_readiness.gate_docs_checks` |

## Proposed changes (ordered, validatable)

1. Re-point `ARCHITECTURE.md`'s two occurrences to `.aw/workflow-artifacts/`, checking for the doubled-prefix hazard (E-01).
2. Correct the same paragraph's `committable` claim so the section stops teaching the pre-D117 tracking policy (E-02).
3. Re-point `CONTRIBUTING.md`'s one occurrence, leaving its separate deleted-test claim untouched (E-03).
4. Restore the deleted guard as `tests/test_run_scratch_path_guard.py`, widened to the shipped tree plus `docs/` plus the user-facing root docs, with a reasoned exclusion constant (E-04).
5. Prove the guard fails per surface and that each allowed spelling and each exclusion is honored by design (E-05).
6. File backlog items for the dangling `tests/test_packaging.py` claim and for the unrestored remainder of `tests/test_docs.py` (E-06).

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
- Under-scope: the guard covers documentation surfaces only. It does not assert anything about `agent_workflows/`, deliberately, because the maintainer's 2026-09-26 ruling retired tests that pin production source.

## Required tests / validation

- `grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md CONTRIBUTING.md` returns NOTHING, and `grep -rn '\.aw/\.aw/'` over both returns nothing.
- The new guard passes over all three surfaces, reports a nonzero scanned-file count for each, and FAILS when a bare reference is reintroduced into any one of them.
- Every recovered falsifiability case passes, plus the new exclusion case.
- The new file is PROVEN COLLECTED by the bare suite, not merely by naming it directly: the collected count rises by exactly the number of tests added, measured against the recorded baseline `3122/3322 tests collected (200 deselected)` with `python3 -m pytest --collect-only -q -o addopts="" -m "not slow" | tail -1`.
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
- Owner: none
- Resolution or deferral rationale: YES, include it. `AGENTS.md` measures clean today (0 occurrences), so inclusion costs nothing now, and it is the single most-read agent-facing file in a target repo, so a retired path appearing there would be the highest-leverage version of this defect. The regeneration concern is real but points the same way: if a future managed block in `engine.py` ever emitted the bare spelling, a failing guard on `AGENTS.md` is exactly the signal wanted, and the fix would be in the emitting constant rather than in the generated file.

### OQ-02: Does restoring a deleted guard conflict with the intent of the suite trim `19313eed`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No, and there is direct precedent. The `restorecov` Set (`6vozur`, `dmxc5h`) restored outcome tests that the same commit deleted, on the reasoning that the trim removed coverage whose loss was not itself decided. This restoration is narrower: roughly seven tests, reading documentation content only, never `agent_workflows/*`, and therefore outside the census that plan `96xtmi` built for the maintainer's no-source-pinning ruling. The plan still reports the exact count delta so the cost is visible rather than asserted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -rnoP '(?<![/\w-])workflow-artifacts/' ARCHITECTURE.md` returning NOTHING, and paste the BEFORE run showing the two occurrences so the change is visible as a delta rather than asserted. Paste `grep -n '\.aw/workflow-artifacts/' ARCHITECTURE.md` showing exactly two prefixed hits, and `grep -n '\.aw/\.aw/' ARCHITECTURE.md` returning nothing. Quote both rewritten sentences in full, since a path swap that mangles the surrounding prose passes a regex and fails a reader.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: quote the rewritten `**Why externalize state to files:**` paragraph in full and state plainly that it no longer claims run records are committable, that it still cites D7, and that it still carries the phase-isolation clause. Paste the output of running `agent_workflows.docs_check.check_no_unicode_dashes` over the file (or `check_doc`) showing no dash finding, since this is user-facing prose.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -rnoP '(?<![/\w-])workflow-artifacts/' CONTRIBUTING.md` returning NOTHING, plus the BEFORE run showing the one occurrence. Quote the rewritten bullet and CONFIRM EXPLICITLY that its `tests/test_packaging.py` mention is unchanged, since this item's whole discipline is changing one thing in a sentence that carries two defects.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new file's module docstring and its exclusion constant with the per-entry reasons. Paste `git show 19313eed^:tests/test_docs.py | sed -n '/def _bare_run_scratch_refs/,/^class ShippedRunScratchPathTests/p'` beside the restored helper to show it was recovered BYTE-FOR-BYTE rather than retyped. Paste the guard passing, INCLUDING the scanned-file count for each of the three surfaces (a sweep that scanned zero files passes vacuously). Paste `rg 'agent_workflows' tests/test_run_scratch_path_guard.py` and account for every hit, or show none, so the no-production-source property is demonstrated rather than claimed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste THREE separate FAILING runs, one per surface (a shipped workflow body, a `docs/` page, `ARCHITECTURE.md`), each showing the guard naming the file and its occurrence count, and after each paste `git status --short` proving the reintroduction was reverted and nothing else changed. Paste the falsifiability cases passing, and paste the new exclusion case together with the fixture it was given, so "excluded by design" is shown rather than inferred from a green sweep.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw find backlog 2jz47s` and `aw find backlog gzmr54` (or the equivalent `ls`) showing both ids RESOLVE, and paste each item's metadata block. Quote the two `- Carrier:` lines from this plan's Deferred section beside them so the pairing is visible rather than asserted. Paste `git diff -- CONTRIBUTING.md` and state explicitly that the `tests/test_packaging.py` mention is untouched, and paste `git status --short` showing the only new test file is the run-scratch guard, so the two prohibitions are demonstrated and not merely promised. Confirm no third backlog item was created. SEPARATELY, paste the suite evidence this plan's contract requires: the collected count before and after (`python3 -m pytest --collect-only -q -o addopts="" -m "not slow" | tail -1`) against the recorded baseline `3122/3322 tests collected (200 deselected)`, showing the rise equals the number of tests added, and the BARE `python3 -m pytest` runs for this tree and for clean HEAD with the failure-set delta named as EMPTY. Do not paste a count-only claim: name the failing node sets, or state that both are empty.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped, through `aw commit <plan> -- <paths>`; never `git add -A`, never `git commit -a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash and restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result that was not run. Re-locate every symbol and every quoted sentence by CONTENT rather than by the offsets cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not on counts. Run `aw sanitize --agent` before treating any pasted output as shareable. This plan carries `- Blocks-Release: next`, inherited from backlog `21ct62`.

POST-GATE LIFECYCLE. Human approval is required before execution. On completion, `aw ipd lint --phase pre-transition` must report conforming and every `V-*` item must carry pasted evidence before the plan moves to `.aw/records/plans/executed/`. If a validation item cannot be satisfied, leave the plan in `pending/` and report the blocker; do not weaken an item to make it pass.
