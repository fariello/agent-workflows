# IPD: Rewrite the 86 stale workflow-artifacts references in the shipped workflow bodies

- Date: 2026-09-12
- Kind: child
- Concern: THE SHIPPED WORKFLOW BODIES SEND AGENTS TO THE RETIRED PATH 86 TIMES AND ASSERT IT IS SAFE. Measured at HEAD 2026-09-12 and RE-VERIFIED at review: `grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l` -> 86 occurrences across 25 SOURCE files, and `grep -rho '\.aw/workflow-artifacts' ... | wc -l` -> ZERO. Not one shipped body has been updated since Order 07.
  THE FILE COUNT IS 25, NOT THE 27 THIS PLAN FIRST RECORDED (F-7, corrected at review). The authoring count came from `grep -rl` WITHOUT an include filter, which also matched three `assess/tools/__pycache__/scan_secrets.cpython-3*.pyc` binaries. Compiled caches are build output, not shipped bodies, and are not editable, so counting them inflated the surface. Use the `--include` filters above; the unfiltered command returns 28.
  TWO OF THOSE LINES ARE ACTIVE FALSEHOODS, which is worse than a stale path because an agent acts on them. `assess/assess.md:139` says the run record "is gitignored by default, so do NOT commit or force-add it", and `:189` repeats that the directory "contains local-only working material". In a TARGET repo neither is true today: nothing ignores the repo-root directory, so an agent that trusts the sentence writes local context into tracked working material. The maintainer's report named these exact lines.
  THE HEAVIEST FILE IS NOT `assess.md`. `release-review/00-run-protocol.md` carries 20 references and `release-review/README.md` 12, so a mechanical sweep must cover the whole tree rather than the file that happened to be noticed.
  THOSE TWO FIGURES WERE FIRST RECORDED AS 18 AND 11, AND THE DISCREPANCY IS A UNIT ERROR WORTH NAMING (F-8, corrected at review): 18 and 11 are LINE counts from `grep -c`, while 20 and 12 are OCCURRENCE counts from `grep -o`. Two references on one line are two rewrites, so OCCURRENCES is the correct unit for this plan and the aggregate 86 was already measured that way. Mixing the units in one table is how a sweep is reported complete while references remain; state the unit whenever citing a count here.
  A NAIVE `sed` WILL CORRUPT THIS. Some references are already correct in spirit but differently shaped, some sit inside code fences and example paths, and `assess/tools/scan_secrets.py` uses the string in scanner logic rather than as instruction prose. A blind substitution also risks producing `.aw/.aw/workflow-artifacts/` on any line already carrying the prefix, which is why the count of already-correct references (zero today) must be re-measured before and after.
- Scope: Rewrite every stale `workflow-artifacts/` reference in the shipped workflow tree to `.aw/workflow-artifacts/`, and make the tracking claims TRUE rather than merely re-pointed. Covers all 25 files (F-7 corrected the authored 27), prose and code fences and example paths, plus `assess/tools/scan_secrets.py`'s use of the string. EXCLUDES the installer (Order 01), the gitignore pattern (Order 02, which must land first so the "gitignored" claims are true when written), README content (Order 04), and any change to what the workflows DO beyond where they write.
- Scope-Paths: .aw/system/workflows/, tests/test_docs.py
- Item-Dependencies: none
- Status: executed
- Priority: high
- Work-Kind: bug
- Readiness: go-pending-approval
- Blocks-Release: next
- From-Backlog: o9inwt
- Set: wfartifacts
- Order: 3
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 9x1rps

## Workflow history
- 2026-09-18 executed (aw oc run): aw oc run self-finalize: 9x1rps verified (set wfartifacts, attempt 1).
- 2026-09-12 approved (aw set): status set to approved
- 2026-09-12 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 all FIXED in place, none deferred, none REPLAN. aw ipd lint conformed at --phase author before semantic review and at --phase review-finalize after every revision. THE REVIEW RE-MEASURED EVERY NUMERIC CLAIM RATHER THAN TRUSTING IT, which is what produced the findings: the 86 occurrences, the 0 prefixed, the 29 repos, the 11-file and 3-file affected repos, the 170 reviews, the 42/10 test refs and all four engine.py citations re-verified EXACTLY, but the file count was 27 and is 25 (grep -rl without --include matched three __pycache__ binaries) and two per-file figures mixed grep -c lines with grep -o occurrences (18/11 vs the true 20/12). PR-002 found the riskiest gap: Order 05 described a MOVE where both trees are populated and three workflow names collide, so it is a MERGE; no RUN_ID collides because run ids are timestamps, but that is the data's property not the design's, so a merge test is now mandatory. PR-004 NARROWED Order 04 after finding the shipped agents-README.md template is already CORRECT and a fresh install receives it, so the wrong .aw/records/README.md is local drift from the Order 11 migration and the template must NOT be edited. PR-003 named the five tests that assert the defect. Also added, per the maintainer's instruction: an isolated-worktree clause to all six execution contracts, recording that aw oc run / aw agy run default isolate_worktree True and that a hand run must allocate its own lane. Typed review records written for all six. No product code was modified by this review. HUMAN APPROVAL IS STILL REQUIRED.
- 2026-09-12 to-review (aw set): Authored as Order 07 delivery (Set wfartifacts) from backlog o9inwt: the spec's run-scratch relocation was implemented in this repo but never delivered to the shipped surface (86 stale references, installer still creating a repo-root dir with a 'DO NOT gitignore' README, 29 repos affected). Review-ready: no TODO placeholders, E/V bijection complete, every V-item demands pasted evidence.

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make every shipped instruction name the one real run-scratch home, and make its tracking claims true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure, rewrite, and re-measure

- [x] E-01 RE-MEASURE THE REFERENCE COUNTS BEFORE EDITING ANYTHING, and record them, because they are the plan's only completion criterion.
  THE TWO COMMANDS, run from the repo root: `grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l` (expected 86) and `grep -rho '\.aw/workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l` (expected 0). If your numbers differ from these, say so with both sets and proceed on yours; the corpus may have moved.
  COUNT OCCURRENCES (`grep -o`), NEVER LINES (`grep -c`), and keep the `--include` filters. Both matter and both were got wrong at authoring (F-7, F-8): dropping the filters pulls in three `__pycache__` binaries and inflates the file count from 25 to 28, and counting lines under-reports by 3 because some lines carry two references. A sweep driven by line counts reports itself complete while references remain.
  ALSO ENUMERATE THE FILES with per-file OCCURRENCE counts, so the rewrite can be checked file by file rather than only in aggregate. Re-measured at review: `release-review/00-run-protocol.md` (20), `release-review/README.md` (12), `assess/assess.md` (8, the file the maintainer reported), `08-final-ship-review.md` (5), `01-current-state.md` (5), `MANIFEST.md` (4), `benchmark/benchmark.md` (4), `index.md` (3), and the remainder 1-2 each across 25 files.
  - Depends on: none
  - Expected outcome: recorded before-counts in OCCURRENCES with the `--include` filters applied, aggregate and per-file, with any divergence from the expected 86 occurrences / 0 prefixed / 25 files stated.
  - Execution state: performed

- [x] E-02 REWRITE THE REFERENCES, AND FIX THE FALSE TRACKING CLAIMS RATHER THAN JUST RE-POINTING THEM.
  DO NOT BLIND-`sed`. Guard against producing `.aw/.aw/workflow-artifacts/` on any line that already carries the prefix (zero today, but the rewrite itself creates them, so a second pass over an already-edited file is the hazard). Check every code fence and example path, not only prose sentences.
  `assess/tools/scan_secrets.py` IS CODE, NOT INSTRUCTION. Read what the string does there before changing it; if it is a scan-exclusion path, re-pointing it wrong either scans the new tree or stops excluding the old one.
  THE CLAIM AT `assess/assess.md:139` AND `:189` MUST BECOME TRUE, not merely re-pointed. After Order 02 the framework-owned `.aw/.gitignore` ignores `.aw/workflow-artifacts/`, so "it is gitignored by default" is then accurate; state WHICH file ignores it so a reader can verify rather than trust. If Order 02 has not landed, STOP: writing the claim first is what made this defect harmful.
  - Depends on: E-01
  - Expected outcome: all 86 references re-pointed, no doubled prefix anywhere, `scan_secrets.py` handled as code with its behavior stated, and the tracking claims true with the ignoring file named.
  - Execution state: performed

- [x] E-03 RE-MEASURE AND PIN THE INVARIANT WITH A TEST, so the next body added does not reintroduce the retired path.
  THE AFTER-COUNTS MUST INVERT: the bare-reference count goes to 0 and the `.aw/`-prefixed count to at least the original 86. A residual bare reference is acceptable ONLY if it is a deliberate mention of the LEGACY path (for example in migration prose), and each such case must be named with its reason.
  ADD A GUARD TEST asserting no shipped body under `.aw/system/workflows/` contains a bare `workflow-artifacts` reference outside an explicitly allowed set, mirroring how `tests/test_docs.py` already walks the docs tree. Without it, this rewrite decays the way Order 07's did.
  - Depends on: E-02
  - Expected outcome: after-counts showing 0 bare and >=86 prefixed, every deliberate exception named, and a guard test that fails if a bare reference returns.
  - Execution state: performed

## Project conventions discovered (Step 0)

- ORDER 07 IS THE AUTHORITY AND IT IS ALREADY `implemented`: spec `20260817-2124-01-records-taxonomy-cleanup` (`u7xtni`), history line "run-artifacts -> `.aw/workflow-artifacts/`". This Set DELIVERS that decision; it does not revisit it.
- RUN SCRATCH IS UNTRACKED BECAUSE OF D92: run records carry local context, absolute home paths and session detail, so committing them publishes machine identity into permanent history. That is the reason, and it is why "just track it" is not an option.
- THIS REPO'S ROOT `.gitignore:62-68` ALREADY ENCODES THE TARGET STATE and is the best statement of intent in the tree, but it is NOT shipped: a target repo receives the framework-owned `.aw/.gitignore` instead. Never cite the root file as evidence that a target repo is protected.
- PATTERNS IN `.aw/.gitignore` ARE `.aw/`-RELATIVE AND MUST BE ANCHORED. The template's own `/inbox/` comment records the measured reason: a bare `inbox/` matched at any depth and silently swallowed the TRACKED `records/comms/shared/inbox/` lane, breaking `aw install`.
- `_ensure_aw_gitignore` IS THE ONLY PATH THAT REACHES AN ALREADY-INSTALLED REPO, because a repo that already has a `.aw/.gitignore` never re-reads the template. Every prior addition in that function carries a comment saying exactly this.
- `install_into_repo` IS THE SHARED CHOKEPOINT for every entry point (`aw install` via `engine.run()`, `aw setup` via `cli._run_setup` -> `cli._install_one`, and library callers). Wiring into `run()` reaches only one of them.
- `.aw/records/` IS TRACKED DURABLE RECORDS, NOT SCRATCH: `records/reviews/` alone holds 170 typed `.review.md` files. An agent already mistook it for the scratch home and moved run records into `.aw/records/reviews/untracked/`.
- Shared checkout, concurrent edits; the suite runs BARE (`python3 -m pytest`). Re-locate every symbol by NAME, not by the line numbers cited in these plans.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | 86 stale references, zero correct ones | `grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows` -> 86 across 25 files (the authored 27 was corrected by F-7); the `.aw/`-prefixed count is 0. Both re-measured EXACTLY at execution. | both greps, run at authoring; re-run at execution |
| F-2 | HIGH | two claims are actively false, not merely stale | `assess.md:139` "it is gitignored by default, so do NOT commit or force-add it" and `:189` "contains local-only working material"; nothing ignores it in a target repo. | the file; the absent template pattern |
| F-3 | MEDIUM | the heaviest file is not the reported one | `release-review/00-run-protocol.md` has 20 references and `release-review/README.md` 12, against `assess/assess.md`'s 8. (Corrected at execution to OCCURRENCES; the 18/11 figures first recorded here were LINE counts, which is exactly the unit error F-8 names.) | per-file counts |
| F-4 | MEDIUM | one reference is CODE, not prose | `assess/tools/scan_secrets.py` uses the string in scanner logic; re-pointing it blindly changes what gets scanned or excluded. | the file |
| F-5 | MEDIUM | a blind sweep creates doubled prefixes | any line already carrying `.aw/` becomes `.aw/.aw/workflow-artifacts/`; the rewrite itself creates such lines, so a second pass is the hazard. | mechanical property of the edit |
| F-6 | LOW | nothing guards against regression | no test asserts the shipped tree is free of the retired path, which is how Order 07's rewrite decayed unnoticed. | absence of such a test |
| F-7 | MEDIUM | the authored FILE count was 27 and is 25 | `grep -rl` without `--include` also matched three `__pycache__/*.pyc` binaries, which are build output and not editable shipped bodies. Unfiltered: 28; filtered to `*.md`/`*.py`: 25. | both commands, run at review |
| F-8 | MEDIUM | two per-file figures mixed LINE counts with OCCURRENCE counts | `00-run-protocol.md` is 18 lines but 20 occurrences; `README.md` is 11 lines but 12. The aggregate 86 is occurrences, so the table was internally inconsistent. A line-based sweep would leave 3 references behind. | `grep -c` vs `grep -o` on both files, at review |

## Proposed changes (ordered, validatable)

1. Re-measure and record before-counts, aggregate and per-file (E-01).
2. Rewrite all references, handle `scan_secrets.py` as code, and make the tracking claims true by naming the ignoring file (E-02).
3. Re-measure, name any deliberate legacy mentions, and add a guard test proven to fail on a reintroduced reference (E-03).

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this plan changes only WHERE the bodies point and whether their tracking claims are true. It does not change what any workflow DOES, does not touch the installer (Order 01), the gitignore (Order 02), the READMEs (Order 04), or any existing file's location (Order 05).

## Required tests / validation

- BOTH GREP COUNTS AFTER the rewrite: bare count 0, `.aw/`-prefixed count >= 86.
- `grep -rn '\.aw/\.aw/' .aw/system/workflows` returns NOTHING.
- The rewritten `assess.md` gitignore claims NAME the enforcing file, so a reader can verify rather than trust.
- The guard test passes, AND fails against a deliberately reintroduced bare reference (a guard that cannot fail proves nothing).
- `python3 -m pytest` BARE, failure-SET delta empty.

## Spec / documentation sync

No spec change: the bodies are being brought into line with a spec that already says this.

THE BODIES THEMSELVES ARE THE DOCUMENTATION being synced here, which is why this is its own child: 25 files is too large a surface to fold into a code change, and a reviewer needs to see the prose diff separately from the installer diff.

## Open questions

### OQ-01: Must Order 02 land before this plan executes?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: YES, AND E-02 STATES IT AS A STOP CONDITION. Resolved from the defect's own shape rather than asked: this plan WRITES the sentence "the run record is gitignored by default", and that sentence is only true once the framework-owned gitignore carries the pattern. Writing a true-sounding claim that is false is precisely the harm being repaired (`assess.md:139` has said it since Order 07 while nothing enforced it), so landing this first would reproduce the defect in a new location. The Set's `Item-Dependencies` are `none` because the runner re-checks dependencies at dispatch on ORDER, and the orchestrator's sequencing rationale plus E-02's stop condition carry the constraint. NOT BLOCKING: the constraint is recorded in the executable item itself.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste both grep commands VERBATIM (showing the `-o` flag and the `--include` filters) with their numeric output, plus the per-file enumeration. State explicitly whether the counts matched the expected 86 occurrences, 0 prefixed, and 25 files. A pasted command using `grep -c` or omitting `--include` is a FAILED validation regardless of the number it produced, because those are the two mistakes F-7 and F-8 record.
  - Observed evidence: ALL THREE EXPECTED FIGURES MATCHED EXACTLY (86 occurrences, 0 prefixed, 25 files); no divergence to report. Both commands carry `-o` and both `--include` filters, per F-7/F-8.

    ```console
    $ grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l
    86
    $ grep -rho '\.aw/workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l
    0
    $ grep -rloP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l
    25
    ```

    PER-FILE OCCURRENCE counts (`grep -ohP ... | wc -l` per file, so occurrences and not lines), all 25 files, matching the review's re-measured table including the 20/12 figures that F-8 corrected:

    ```console
    $ for f in $(grep -rloP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | sort); do printf "%s\t%s\n" "$(grep -ohP '(?<!\.aw/)workflow-artifacts' "$f" | wc -l)" "$f"; done | sort -rn
    20      .aw/system/workflows/release-review/00-run-protocol.md
    12      .aw/system/workflows/release-review/README.md
    8       .aw/system/workflows/assess/assess.md
    5       .aw/system/workflows/release-review/08-final-ship-review.md
    5       .aw/system/workflows/release-review/01-current-state.md
    4       .aw/system/workflows/release-review/MANIFEST.md
    4       .aw/system/workflows/benchmark/benchmark.md
    3       .aw/system/workflows/index.md
    2       .aw/system/workflows/verify-execution/verify-execution.md
    2       .aw/system/workflows/templates/README.md
    2       .aw/system/workflows/setup-repo/setup-repo.md
    2       .aw/system/workflows/release-review/07-implementation.md
    2       .aw/system/workflows/release-review/03-tests-regression.md
    2       .aw/system/workflows/release-review/02-quality-security-edge-cases.md
    2       .aw/system/workflows/getting-started/getting-started.md
    2       .aw/system/workflows/assess/templates/closing-report.md
    1       .aw/system/workflows/verify/verify.md
    1       .aw/system/workflows/release-review/templates/per-phase-report.md
    1       .aw/system/workflows/release-review/06-compatibility-packaging-release.md
    1       .aw/system/workflows/release-review/05-feature-usability-maintainability.md
    1       .aw/system/workflows/release-review/04-docs-specs-examples.md
    1       .aw/system/workflows/assess/tools/scan_secrets.py
    1       .aw/system/workflows/assess/lenses/secrets.md
    1       .aw/system/workflows/assess-all/assess-all.md
    1       .aw/system/workflows/advise/advise.md
    ```

    E-02'S STOP CONDITION WAS CHECKED FIRST, not assumed: Order 02 (`vh14ku`) is in `executed/` and its pattern is live in both the template and the back-fill, so writing the "it is gitignored" claim is now TRUE rather than aspirational.

    ```console
    $ git check-ignore -v .aw/workflow-artifacts/x
    .aw/.gitignore:73:/workflow-artifacts/	.aw/workflow-artifacts/x
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `grep -rn '\.aw/\.aw/' .aw/system/workflows` returning NOTHING (the doubled-prefix guard). Quote the rewritten `assess/assess.md` lines that make the gitignore claim and show they NAME the ignoring file. Paste the `scan_secrets.py` diff with one sentence on what the string does there. Quote at least one rewritten code-fence example, since fences are the shape a prose-only sweep misses.
  - Observed evidence: DOUBLED-PREFIX GUARD CLEAN (F-5): the command returns no output and exit 1, so no `.aw/.aw/` was produced anywhere.

    ```console
    $ grep -rn '\.aw/\.aw/' .aw/system/workflows; echo "exit=$?"
    exit=1
    ```

    THE TWO FALSE CLAIMS (F-2) NOW NAME THE ENFORCING FILE AND THE VERIFYING COMMAND, so a reader can check rather than trust, which is the whole failure mode: the old sentence sounded authoritative while nothing enforced it.

    ```console
    $ grep -n 'gitignore' .aw/system/workflows/assess/assess.md
    139:7. **Commit ONLY the IPD**, and NEVER push (commit-only; no remote changes). The run record in `.aw/workflow-artifacts/` is local-only working material: the framework-owned `.aw/.gitignore` ignores it (the anchored pattern `/workflow-artifacts/`, verifiable with `git check-ignore -v .aw/workflow-artifacts/`), so do NOT commit or force-add it. Do not commit unrelated changes; run `git status --short` first.
    190:(the anchored pattern `/workflow-artifacts/`; confirm with `git check-ignore -v
    ```

    Line 188-191 in full, showing the claim is attributed and independently checkable:

    ```text
    The `.aw/workflow-artifacts/` directory contains local-only working material and is out of review
    scope (never assess it as if it were the project). The framework-owned `.aw/.gitignore` ignores it
    (the anchored pattern `/workflow-artifacts/`; confirm with `git check-ignore -v
    .aw/workflow-artifacts/` rather than trusting this sentence). Do not commit or force-add it.
    ```

    THE SAME TREATMENT WAS APPLIED TO THE OTHER FIVE FILES making an unattributed tracking claim, because re-pointing `assess.md` alone would leave the identical unverifiable assertion in the heaviest files: `release-review/00-run-protocol.md` (:245, :285), `release-review/README.md` (:143), `release-review/MANIFEST.md` (:117), `release-review/01-current-state.md` (:13, :45, whose "ensure it is gitignored" run-setup instruction became "confirm", since the pattern now ships and an agent should verify rather than add a duplicate rule), and `benchmark/benchmark.md` (:178).

    `scan_secrets.py` IS CODE AND WAS DELIBERATELY LEFT BARE (F-4). The string is a member of `SKIP_DIR_NAMES`, a set of single path SEGMENT names matched by `parts = set(rel_posix.split("/")); if parts & SKIP_DIR_NAMES` in `is_skipped_path` (line 412). A segment never contains a slash, so the prefixed spelling `.aw/workflow-artifacts` could match NOTHING and would have silently stopped excluding run records from the secret scan; the bare name already matches the relocated tree AND any legacy repo-root copy. Only a comment was added:

    ```diff
    $ git diff -- .aw/system/workflows/assess/tools/scan_secrets.py
         # Agent-workflow run records are generated deliverables (they may even contain a prior
         # scan's own redacted output); scanning them just re-flags noise, not committed secrets.
    +    # DELIBERATELY BARE, not `.aw/workflow-artifacts` (wfartifacts Order 03): this set holds
    +    # single path SEGMENT names, matched by `set(rel_posix.split("/")) & SKIP_DIR_NAMES` in
    +    # `is_skipped_path`. A segment never contains a slash, so the prefixed spelling could match
    +    # NOTHING and would silently stop excluding run records; the bare name already matches the
    +    # relocated `.aw/workflow-artifacts/` AND any legacy repo-root copy, which is what we want.
         "workflow-artifacts",
    ```

    REWRITTEN CODE FENCES AND EXAMPLE PATHS, the shape a prose-only sweep misses:

    ```console
    $ sed -n '273p' .aw/system/workflows/release-review/00-run-protocol.md
    .aw/workflow-artifacts/release-review/<RUN_ID>/
    $ sed -n '63p' .aw/system/workflows/advise/advise.md
    .aw/workflow-artifacts/advise-<persona>/<RUN_ID>/
    $ grep -n 'assess-security/20260722-143012' .aw/system/workflows/assess/templates/closing-report.md
    30:  Run record: .aw/workflow-artifacts/assess-security/20260722-143012/
    43:  Run record: .aw/workflow-artifacts/assess-security/20260722-143012/
    $ grep -n -- '--out' .aw/system/workflows/assess/lenses/secrets.md
    24:  --out .aw/workflow-artifacts/assess-secrets/<RUN_ID>/scan.json
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste both grep counts AFTER the rewrite, showing 0 bare and >=86 prefixed. Name every deliberate remaining bare reference with its reason, or state that there are none. Paste the guard test's passing output, and paste it FAILING against a deliberately reintroduced bare reference, since a guard that cannot fail proves nothing.
  - Observed evidence: THE PREFIXED COUNT INVERTED AS REQUIRED (0 -> 94, above the required >=86). THE PLAIN-SUBSTRING BARE COUNT IS 11, NOT 0, AND THAT IS REPORTED RATHER THAN MASSAGED, because the plan's E-01 command matches any occurrence of the substring not immediately preceded by `.aw/`, which also matches the anchored gitignore PATTERN `/workflow-artifacts/` that the corrected prose now deliberately quotes. Measured with the PATH-reference form (the substring followed by `/` and not preceded by a slash, word character or hyphen), the count is 0.

    ```console
    $ grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l
    11
    $ grep -rho '\.aw/workflow-artifacts' .aw/system/workflows --include='*.md' --include='*.py' | wc -l
    94
    $ grep -rnoP '(?<![/\w-])workflow-artifacts/' .aw/system/workflows --include='*.md' --include='*.py' | wc -l
    0
    ```

    ALL 11 RESIDUALS ARE NAMED, and the arithmetic closes exactly against the original 86 (84 rewritten + 1 template filename + 1 code segment = 86):

    | Count | Spelling | Why it is correct as-is |
    |---|---|---|
    | 9 | `` `/workflow-artifacts/` `` | The ANCHORED GITIGNORE PATTERN, newly quoted by the corrected claims in `assess/assess.md` (x2), `release-review/00-run-protocol.md` (x2), `01-current-state.md` (x2), `README.md`, `MANIFEST.md`, `benchmark/benchmark.md`. Patterns in `.aw/.gitignore` are `.aw/`-relative, so the pattern that ignores run scratch IS written `/workflow-artifacts/`; writing `.aw/workflow-artifacts/` there would document a pattern that does not exist. |
    | 1 | `workflow-artifacts-README.md` | The installer TEMPLATE FILENAME in `templates/README.md`, an actual file under `.aw/system/workflows/templates/`. A hyphen follows, not a slash; it is not a path reference. Its parenthetical DID move to `.aw/workflow-artifacts/` (that part is a path). |
    | 1 | `"workflow-artifacts",` | `scan_secrets.py`'s `SKIP_DIR_NAMES` segment name (see V-02). Prefixing it would break the exclusion. |

    NONE of the 11 is a stale legacy-path reference, so there is no migration-prose exception to declare.

    THE GUARD TEST PASSES (9 new tests: 2 sweep assertions over all 25 shipped bodies + 6 falsifiability cases + 1 directory existence; `tests/test_docs.py` went from 14 to 23):

    ```console
    $ python3 -m pytest tests/test_docs.py -o addopts="" -q
    .......................                                                  [100%]
    23 passed in 0.31s
    ```

    AND IT FAILS AGAINST A DELIBERATELY REINTRODUCED REFERENCE. One occurrence in `verify/verify.md` was temporarily reverted to the bare spelling; the guard named the exact file and count, and the file was restored immediately afterwards (`git status` confirms only intended modifications remain):

    ```console
    $ python3 -m pytest tests/test_docs.py -o addopts="" -q -k "no_bare_run_scratch"
    E       AssertionError: Lists differ: ['.aw/system/workflows/verify/verify.md: 1 bare reference(s)'] != []
    E       First list contains 1 additional elements.
    E       First extra element 0:
    E       '.aw/system/workflows/verify/verify.md: 1 bare reference(s)'
    E       - ['.aw/system/workflows/verify/verify.md: 1 bare reference(s)']
    E       + [] : shipped workflow bodies name the RETIRED repo-root run-scratch path; write `.aw/workflow-artifacts/` instead:
    E       .aw/system/workflows/verify/verify.md: 1 bare reference(s)
    tests/test_docs.py:234: AssertionError
    FAILED tests/test_docs.py::ShippedRunScratchPathTests::test_no_bare_run_scratch_path_in_shipped_bodies
    1 failed, 22 deselected in 0.20s
    ```

    THE FULL SUITE, RUN BARE, judged on the FAILURE-SET DELTA as the contract requires. 31 tests fail, and ALL 31 FAIL IDENTICALLY AT CLEAN HEAD, measured in a throwaway detached worktree at `ab18c25b` rather than assumed:

    ```console
    $ python3 -m pytest            # my tree
    31 failed, 7989 passed, 3 skipped, 2 xfailed in 112.17s (0:01:52)

    $ python3 -m pytest            # clean HEAD ab18c25b, separate worktree
    31 failed, 7980 passed, 3 skipped, 2 xfailed in 110.77s (0:01:50)

    $ diff wfart-before.txt wfart-after.txt && echo "DELTA EMPTY: identical failure sets"
    DELTA EMPTY: identical failure sets
    ```

    The delta is EMPTY and passes rose by exactly 9, the guard tests added here. The 31 pre-existing failures are an ENVIRONMENT artifact of executing inside a managed lane, not a regression: they are lifecycle/runner tests that shell out to `aw ipd begin`, which this worker role refuses by design (`AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process must not run them`). They are reported to the driver rather than silently absorbed.

    ```console
    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

DO NOT DELETE A USER'S COMMITTED RUN RECORDS, anywhere in this Set. Relocation preserves history; deletion is unrecoverable and is the one outcome worse than leaving the retired directory in place.

ISOLATE THE WORKTREE (maintainer instruction 2026-09-12). If you run this plan through `aw oc run` / `aw agy run` you already have this: `isolate_worktree` DEFAULTS TRUE (`oc_runipd.py:3048`, `:6106`; `agy_runipd.py:2055`, `:3254`), so the agent turn, verifier and finalize happen on an `aw/lane/<id6>` branch in a fresh worktree while the main tree stays untouched, and changes return through the merge-and-revalidate gate. Do NOT pass `--no-isolate-worktree`.
IF YOU EXECUTE BY HAND, ALLOCATE ONE YOURSELF rather than editing the main checkout: `git worktree add ../aw-lane-<id6> -b aw/lane/<id6>`, work and commit there, then merge back. THIS SET MAKES THAT PARTICULARLY IMPORTANT for two measured reasons. FIRST, Order 03 rewrites 25 shipped files and Orders 01/02/05 all edit `engine.py`, so a half-finished hand run leaves the installer and the shipped bodies DISAGREEING, which is the exact defect state this Set exists to end. SECOND, this is a SHARED CHECKOUT with concurrent agents and humans, and an isolated lane is what keeps a partial rewrite of `.aw/system/workflows/` from being visible to (or swept into a commit by) someone else mid-run.
NOTE THE ONE THING ISOLATION DOES NOT COVER: Order 05 must be TESTED against scratch clones, never against a user's real repository. A worktree isolates THIS repo's tree; it does nothing to protect the OTHER repositories on the machine whose committed run records that plan is designed to move (the two counted in Order 05's findings).

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
