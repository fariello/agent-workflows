# IPD: Re-land the inbox waiting-drops counter that never reached main, porting the recovered implementation onto the refactored footer and re-deciding its exclusion and audience questions

- Date: 2026-09-30
- Kind: child
- Concern: Plan `9iiqmm` sits in `.aw/records/plans/executed/` with `- Status: executed`, a self-finalize history record, and `V-*` blocks pasting test output said to be PASSING, and the feature it describes DOES NOT EXIST. Backlog `an77ub` reports it and I REPRODUCED every measurement in this lane at HEAD `2c22b5bd` rather than transcribing them (F-01 through F-05): `git show main:agent_workflows/attention.py | grep -c inbox` is `0`, the same for `tests/test_attention.py`, `git log --all --oneline -S'waiting in \`.aw/inbox/\`' -- '*.py'` is empty, `agent_workflows.attention` has no `inbox_waiting` attribute, and a real board driven through `cli.main(["attention", "--dir", <tmp>, "--no-color"])` against a temp repo holding four inbox drops prints `1 artifact shown` and NO footer line.
  THE BYTES ARE RECOVERABLE TODAY AND ARE `git gc`-PRUNABLE, WHICH IS WHY THIS IS URGENT RATHER THAN MERELY WRONG (F-06). Both blobs exist and are PACKED, not loose: `git cat-file -s 9effdcef` is `138154` and `git cat-file -s de2fbe7c` is `114999`, and `git cat-file blob` extracts each. They are reachable from no ref: the holding commits `5c55d020`, `888c20a1` (both "WIP on aw/lane/9iiqmm", 2026-09-20) and `3569ed07` ("WIP INTERRUPTED SNAPSHOT (not finished work): lane 9iiqmm", 2026-09-23) are dangling. `gc.pruneExpire` and `gc.auto` are both UNSET here, so git's own defaults (prune at 2 weeks, auto-gc at 6700 loose objects) apply and the two WIP commits are already past that age: an unattended `gc` collects them, and then this plan's cost changes from a port to a rewrite.
  THE RECOVERED CODE DOES NOT APPLY AS-IS, AND THAT IS THE REAL WORK (F-07). `main` has moved 2913 commits since the dangling base `1a011e17`, and the footer this feature attaches to was REFACTORED underneath it: the recovered blob patches an `if needs_setup and has_hidden / elif needs_setup / elif has_hidden and colored` chain that NO LONGER EXISTS, while `attention.run`'s footer today is a single `if needs_setup:` whose comment reads "The --all hint lives on the count line now; do not repeat it here". So the `elif`-chain hazard that E-02 of `9iiqmm` was built around (and that its F-3 called the single most important implementation detail) is GONE, and a port that copies the old block verbatim carries a comment describing a chain that is not there. `agent_workflows/attention.py` also no longer imports `os` at all (`hasattr(attention, "os")` is False), so the recovered `os.scandir` body needs an import the file does not have.
- Scope: IN: (1) port the recovered `inbox_waiting` counter onto today's `agent_workflows/attention.py`, preserving its listing-only safety property and its `README.md`/`.gitkeep` exclusion, and adding the `os` import the file now lacks; (2) render one advisory footer line from it in the HUMAN board, composing with today's single-`if` footer and carrying a comment that describes the footer AS IT IS rather than the chain that was refactored away; (3) port the recovered tests, rewritten where the environment moved (no `contextlib.ExitStack` import exists in `tests/test_attention.py`, and `SCHEMA_VERSION` is `4` today, not the `3` the old plan reasoned about); (4) prove the exit code and both machine surfaces byte-unchanged. OUT, each for a stated reason: any edit to `9iiqmm` or its review record, which are terminal records that `dv7c49` already corrected by append; re-opening or re-closing backlog `plbkp5`, which `dv7c49` already moved to `graduated`; the SYSTEMIC question of how a lane self-finalized with an empty diff, which is a runner investigation this plan measures (F-10) and hands to a carrier rather than fixing; the `--agent`/`--json` surfaces, whose cost is measured in F-09 and which OQ-02 hands to the maintainer; the severity-blind `findings` count in `result_types.to_agent_record`, which F-09 reproduces and which is a repo-wide agent-protocol contract; and any change to `.aw/inbox/`, its gitignore status, or `selectors._ID_RE`.
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: an77ub
- Blocks-Release: next
- Set: awinbox
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: olmvgw

## Workflow history
- 2026-10-02 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: olmvgw verified (set awinbox, attempt 1).
- 2026-10-01 approved (aw set): status set to approved

- 2026-10-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 through PR-007. Reviewed in an isolated lane at HEAD `db2c6e3d`. Structural preflight `aw ipd lint --phase author --agent` reported `clean` before semantic review. THIS IS AN UNUSUALLY WELL EVIDENCED PLAN AND I RE-DROVE EVERY CLAIM RATHER THAN TRUSTING ANY. The urgent one FIRST: BOTH RECOVERED BLOBS ARE STILL PRESENT at review, `git cat-file -s` returning `138154` and `114999` exactly as authored, and I extracted both and read them. F-01 through F-09, F-11 and F-12 all reproduce, several to the byte: the live board prints `1 artifact shown` with no footer line; the recovered footer block really does patch a three-branch `elif` chain that today is a single `if needs_setup:` carrying the comment "The --all hint lives on the count line now; do not repeat it here"; `hasattr(attention, "os")` is False; `.aw/inbox/README.md` is tracked; `SCHEMA_VERSION` is 4; `tests/test_attention.py` imports no `ExitStack`; and a clean `CommandResult` with one warning `Diagnostic` returns `outcome: clean, exit: 0, findings: 1` against `findings: 0` without it. THE CORRECTIONS. FIRST (PR-001, HIGH), THE URGENCY IS UNDERSTATED IN ONE DIRECTION AND OVERSTATED IN ANOTHER, and both halves matter to E-01: this repository carries 8875 LOOSE OBJECTS against git's default `gc.auto` threshold of 6700, so auto-gc is ALREADY ARMED rather than merely possible, which strengthens the deadline; but git's `gc --cruft` default (on by default) repacks unreachable objects into a cruft pack rather than deleting them outright, so a single auto-gc is less likely to destroy the blobs than the plan implies. The honest statement is that the window is real, already open, and not precisely predictable, which is exactly why E-01's extract-first ordering is correct. SECOND (PR-002, HIGH), THERE ARE FOUR ATTENTION SUITES, NOT THREE: `tests/test_attention_blind_spot.py` exists (9 passed) and both F-12 and E-06 say three, so an executor following E-06 literally would leave a records-scan suite unrun by a change to the scanned module. THIRD (PR-003, MEDIUM), the suite baseline has moved and is NOT green: `1 failed, 3491 passed` at review against the authored `3387 passed`, the failure a pre-existing date-boundary bug in `tests/test_backlog.py`, so validation step 2's "ZERO failures" was unachievable. Also corrected: the deselected count (207 to 208), a cross-plan survey the plan omitted (two APPROVED plans declare both of its paths; verified non-colliding), and V-05's demand to show the patched-open test failing against a deliberately-parsing implementation, which asks the executor to author a wrong implementation and is replaced with the achievable half the item already offers.
- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `an77ub`, inheriting its `- Blocks-Release: next`. EVERY measurement was taken IN THIS LANE at HEAD `2c22b5bd`, not carried over from the item (measured 2026-09-28 at base `bc7015e0`), and the item's five claims all REPRODUCE (F-01 through F-05).
  THE ITEM'S CENTRAL WARNING IS CONFIRMED AND SHARPENED. The recovered blobs are present and extractable but reachable from no ref, and `gc.pruneExpire`/`gc.auto` are both UNSET, so git's 2-week default already covers the two 2026-09-20 WIP commits. That converts "recover it" from a preference into a deadline, and it is why `V-01` demands the extraction be proven from the sha rather than assumed.
  THE ITEM SAYS RE-LANDING THE BLOB AS-IS IS NOT DECIDED, AND I MEASURED WHY IT CANNOT BE. `main` has advanced 2913 commits since the dangling base, and the specific construct the old plan's most important finding was about was refactored away: the three-branch `elif` footer chain is now one `if needs_setup:`. So the recovered block's central comment describes code that does not exist, `attention.py` no longer imports `os`, `SCHEMA_VERSION` is `4` rather than `3`, and `tests/test_attention.py` has no `ExitStack` import. The port is therefore a REWRITE of the surrounding justification even where the counter body survives unchanged, and E-02's whole point is that the comment must describe today's footer.
  I RESOLVED THE ITEM'S THREE LIVE DESIGN QUESTIONS FROM REPOSITORY EVIDENCE RATHER THAN DEFERRING THEM, since the item names them as live but each turns on a fact in the tree. The `README.md`/`.gitkeep` exclusion is now MEASURED-NECESSARY, not a judgement: `git ls-files .aw/inbox` shows `.aw/inbox/README.md` is TRACKED and present, so a counter without the exclusion reports at least one waiting drop on a fully drained inbox on every clone forever (F-08). Singularization is settled by the house form, which `attention.run`'s own count line already implements as `count_noun = "artifact" if shown_count == 1 else "artifacts"`, so the nudge follows a shipped precedent rather than inventing one. The agent-surface question is the one genuine maintainer call and it stays OQ-02, with its cost reproduced: I constructed a clean `CommandResult` carrying ONE warning `Diagnostic` and `to_agent_record` returned `outcome: clean, exit: 0, findings: 1` against `findings: 0` without it (F-09).
  THE OLD PLAN'S NON-TTY PREMISE IS FALSE AND THIS PLAN DOES NOT INHERIT IT. `9iiqmm`'s F-12 and `## Scope check` assert that `select_output` routes to `OutputMode.AGENT` on any non-TTY stdout; `dv7c49` recorded that as retracted, and `select_output`'s own docstring now says "TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE MODE". Confirmed by running it: a redirected `cli.main(["attention", ...])` renders the BOARD. So the footer's reach is BROADER than that plan promised (every piped agent sees it), the tests need no TTY trick, and `--no-color` is passed for text stability alone.
  I ALSO MEASURED THE SYSTEMIC HALF RATHER THAN ONLY REPEATING THE ITEM'S REFUSAL TO DIAGNOSE IT (F-10), because a re-land that leaves the mechanism live can be lost the same way. `runner_shared.compute_scope_reconciliation` AUTO-ACKNOWLEDGES every declared-but-unmodified path, and I drove `ipd_lifecycle._reconcile_scope` with BOTH of `9iiqmm`'s declared paths unmodified and the runner's own auto-ack wording: it returned `ok=True` with no missing reasons and no missing acks. So a finalize whose execution touched NEITHER declared path is reconciled clean by construction. The zero-work retry predicate does not catch it either: `runner_shared.handle_zero_work_retry` returns immediately unless the item's status is exactly `partial`, and a self-finalized item is `executed`. That is a real gap, it is NOT this plan's to fix, and it is FILED rather than left in prose: backlog `gmbdxe` (`bug`, `Blocks-Release: next`) carries the measurement and three costed candidate fixes, none of which is "stop auto-acking", since the auto-ack is correct in the ordinary case.
  TWO CARRIERS WERE FILED AT AUTHORING RATHER THAN LEFT TO THE EXECUTOR, because `check.ipd-uncarried-obligation` is error-severity for a post-cutover plan and would have refused this one: `gmbdxe` for the systemic finalize gap above, and `xqem10` for OQ-02's agent-surface decision. Neither points back at `an77ub`, which this plan graduates from and which will close when this executes.

## Goal

Make a forgotten `.aw/inbox/` drop visible again in `aw attention`, by porting the recovered-but-unreachable implementation onto today's refactored footer with its safety property intact, so the feature the repository already records as shipped actually runs and the record stops being false.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: recover the bytes before anything else can consume them

- [x] E-01 EXTRACT BOTH RECOVERED BLOBS TO A SCRATCH LOCATION OUTSIDE THE TREE, AND PROVE THEY STILL EXIST, BEFORE WRITING ANY CODE.
  DO THIS FIRST AND DO NOT SKIP IT ON THE ASSUMPTION THAT THE PLAN'S PASTED EXCERPTS ARE ENOUGH. The blobs are the only surviving copy of a reviewed implementation and they are reachable from no ref, so they can vanish between this plan's authoring and its execution. The two shas, copied exactly: `git cat-file blob 9effdcef169e7ad8eafc0c3b22f5432cf1384dc6` yields `agent_workflows/attention.py` (138154 bytes) and `git cat-file blob de2fbe7ceb1918551ea8f03fc0e8467f056119be` yields `tests/test_attention.py` (114999 bytes). Do NOT retype either from memory; a mistyped sha reports "not a valid object name", which reads exactly like a pruned object and would send you down the STOP branch below for the wrong reason.
  DO NOT RUN `git gc`, `git prune`, or `git repack -d` AT ANY POINT IN THIS EXECUTION, and do not run a command that triggers auto-gc before the extraction has succeeded. The backlog item states this and it is load-bearing rather than cautious: `gc.pruneExpire` is unset (git default 2 weeks) and the two WIP commits date from 2026-09-20.

  THE WINDOW IS ALREADY OPEN, AND IS ALSO LESS ABSOLUTE THAN A ONE-LINE WARNING SUGGESTS; BOTH HALVES ARE MEASURED (PR-001). Measured at review: `git count-objects -v` reports `count: 8875` loose objects against git's default `gc.auto` threshold of 6700, so auto-gc is ARMED RIGHT NOW rather than merely possible at some future point, which is a stronger reason to extract first than the plan originally gave. BUT git's `--cruft` behavior is ON BY DEFAULT, so an expiring gc repacks unreachable objects into a CRUFT PACK rather than deleting them outright, and the two blobs are PACKED rather than loose (verified at review: neither appears under `.git/objects/<2>/<38>`). So a single auto-gc is LESS likely to destroy them than "prunable" implies, and an executor who finds them still present after some unrelated command has run should NOT conclude the warning was false. THE OPERATIONAL RULE IS UNCHANGED AND IS WHAT MATTERS: extract before anything else, prove it, and never invoke a collection verb yourself. Do not spend time trying to predict the exact window; the ordering is the mitigation.
  IF EITHER BLOB IS GONE, STOP AND REPORT, do not silently rewrite the feature from the excerpts in this plan. A rewrite is a legitimate outcome but it is a DIFFERENT plan with a different risk profile, and quietly substituting one for the other is exactly the kind of undisclosed substitution that produced the defect this plan exists to fix.
  WRITE THE EXTRACTED COPIES OUTSIDE THE REPOSITORY (a scratch directory), never into the worktree, so they cannot be committed by accident and cannot be mistaken for the ported result.
  - Depends on: none
  - Expected outcome: both blobs extracted to scratch paths outside the repository, with `git cat-file -s` output pasted for each proving the object is still present (review re-measured `138154` and `114999`, so a differing size is itself a finding to report), and no `gc`/`prune`/`repack` invoked.
  - Execution state: performed

### Task group 2: the counter, which may list but never read

- [x] E-02 PORT `inbox_waiting` INTO `agent_workflows/attention.py`, PRESERVING ITS LISTING-ONLY PROPERTY AND ADDING THE IMPORT THE FILE NO LONGER HAS.
  SITE IT WHERE ITS TWIN LIVES: immediately after `attention.setup_needed` and before `attention.release_blockers`, which is where the recovered blob put it. `setup_needed` is the house pattern this deliberately copies (derived on demand, read-only, swallows its own exceptions, creates nothing, feeds a footer nudge, touches neither the item list nor the exit code) and its docstring says "NEVER creates anything". Do not invent a second shape.
  THE RECOVERED BODY IS CORRECT AND SHORT; PORT IT RATHER THAN REDESIGNING IT. It resolves exactly one anchored path, lists with `os.scandir`, excludes a bookkeeping name set, and returns `0` from a bare `except Exception`. Keep all four properties.
  ADD `import os` TO THE MODULE, WHICH TODAY IT LACKS. Measured: `hasattr(agent_workflows.attention, "os")` is False and the import block runs `functools`, `json`, `re`, `sys`, then `from pathlib import Path`. The recovered blob's import block DID include `os`, so the diff must add it in alphabetical position rather than assuming it is present.
  LIST ONLY, NEVER OPEN, AND SAY WHY IN THE CODE. This is the feature's hard constraint and its justification is a measured hazard: `selectors._ID_RE` is position-unanchored, so a `- Id:` line anywhere in an unvetted drop, INCLUDING one merely quoted as an example, is harvested as an identity claim that can collide with a real artifact's id6. Listing a directory cannot forge an identity; parsing a drop can. The comment must state this, because the next person to touch the function will otherwise "improve" it by reading front matter.
  THE EXCLUSION OF `README.md` AND `.gitkeep` IS NOW MEASURED-NECESSARY, NOT A PREFERENCE, and the comment must say so with the fact rather than the old plan's forward-looking prediction. `git ls-files .aw/inbox` returns `.aw/inbox/README.md`: the file is TRACKED and present in every clone, so a counter without the exclusion reports at least one waiting drop on a fully drained inbox, forever, on every machine, which defeats the silent-when-empty rule this feature depends on.
  A MISSING DIRECTORY MEANS ZERO AND MUST NOT CREATE ANYTHING. `.aw/inbox/` is gitignored and per-checkout, so it is legitimately absent; absent must not raise, and the probe must not bring `.aw/` or `.aw/inbox/` into existence by looking for them.
  ONE ANCHORED PATH, NEVER A SEARCH BY NAME. `.aw/records/comms/*/inbox/` is a TRACKED, unrelated inter-agent comms lane, and `.aw/.gitignore` records that an unanchored `inbox/` pattern once threatened exactly that path and would have broken `aw install`. Resolve `<repo>/.aw/inbox` exactly.
  A NESTED DIRECTORY COUNTS AS ONE ENTRY AND IS NOT WALKED. The number's job is to be nonzero and roughly right; one shallow `scandir` cannot recurse unboundedly.
  - Depends on: E-01
  - Expected outcome: `attention.inbox_waiting` exists beside `attention.setup_needed`, `import os` added to the module, resolving exactly `<repo>/.aw/inbox` via `os.scandir`, returning 0 for a missing directory without raising and without creating anything, excluding `README.md`/`.gitkeep`, counting hidden and non-`.md` entries, counting a nested directory as one entry, opening no file, with the listing-not-parsing rule and the measured tracked-README reason both stated in the docstring.
  - Execution state: performed

### Task group 3: surface it on the footer as the footer is NOW

- [x] E-03 RENDER ONE ADVISORY FOOTER LINE IN THE HUMAN BOARD, COMPOSING WITH TODAY'S SINGLE-`if` FOOTER, WITH A COMMENT THAT DESCRIBES THE FOOTER THAT EXISTS.
  DO NOT COPY THE RECOVERED COMMENT BLOCK VERBATIM, AND THIS IS THE ONE PLACE A LAZY PORT SHIPS A LIE. The recovered block's comment explains at length that it must be an independent `if` and "NOT another `elif` on the chain above", because "the chain renders exactly ONE line". That chain is GONE: `attention.run`'s footer today is `footer_lines: list[str] = []`, then `needs_setup = setup_needed(repo_root)`, then a single `if needs_setup:` whose own comment reads "The --all hint lives on the count line now; do not repeat it here". A comment describing a three-branch chain in a file that has one branch misleads the next reader exactly as a drifted line number does. Rewrite it to state the SURVIVING invariant: this is an INDEPENDENT `if` appending to `footer_lines`, so the nudge composes with the setup notice instead of competing with it, and a future author must not convert either into an `elif`.
  KEEP THE PROPERTIES THE COMMENT LEGITIMATELY CARRIES. Advisory only: it constructs no `Drift` and so cannot affect the exit code, which `core.drift_exit_code(drift)` owns alone; it invents no status and creates no `Item`; it shows ALWAYS rather than only under `--all`, because `--all` reveals hidden done/parked ARTIFACTS and an un-adopted drop is not one; and it carries no mtime or other time-derived value, preserving the spec's byte-determinism invariant.
  MATCH THE HOUSE FORM, WHICH IS ALREADY SHIPPED IN THIS FUNCTION. The two existing footer lines are imperative and name a remedy. Singularization is not a judgement call: `attention.run` already computes `count_noun = "artifact" if shown_count == 1 else "artifacts"` a few lines above, so `"file" if waiting == 1 else "files"` follows a precedent in the same function rather than inventing one.
  NAME `aw adopt` AS THE REMEDY, AND VERIFY IT BY INVOKING IT RATHER THAN BY READING A PLAN'S STATUS. `aw adopt` IS shipped: `python3 -m agent_workflows adopt --help` prints its usage and exits 0 (measured; `agent_workflows/artifact_adopt.py` exists and `plan lznpv6` is in `executed/`). Invoke it anyway and branch on the result, because a plan's status is not a shipped verb. Use `<path>` as the placeholder, since `adopt` refuses more than one path and a remedy naming no argument would mislead. NOTE that inside a lane worktree the ambient `aw` resolves the MAIN checkout's package (backlog `jeh310`), so take the branch on the lane-resolved `python3 -m agent_workflows adopt --help`.
  DO NOT INVENT A STATUS AND DO NOT ENTER THE CLASSIFICATION. Inbox drops have no id6, no status and no lifecycle. They must not become an `Item`, must not be counted in ready/active/blocked/done/parked, and must not reach `TRACKED_TREES` or `CLASS_MAPS`. If `agent_workflows/attention_contract.py` seems to need editing, the design has drifted into classification: stop and reconsider. That file is deliberately NOT in `- Scope-Paths:`.
  - Depends on: E-02
  - Expected outcome: one advisory line appended to `footer_lines` under an independent `if`, composing with the setup notice; the house imperative form with correct singularization and `aw adopt <path>` named after invoking the verb; a comment describing TODAY's single-`if` footer with no surviving reference to the removed `elif` chain; no new `Item`, no new status, no edit to `attention_contract.py`.
  - Execution state: performed

- [x] E-04 PROVE THE EXIT CODE AND THE `--check` PATH ARE UNTOUCHED, so a gitignored box-local file can never fail CI.
  NEVER CONSTRUCT A `Drift` FOR A WAITING DROP. The exit code is owned solely by the drift set: `attention.run` returns `core.drift_exit_code(drift)` on both the `--check` path and the board path. A `Drift` here would fail `aw attention --check` on a local gitignored file no other machine can see, which would be wrong: a waiting drop is not a repository defect.
  `--check` STAYS SILENT, AND THAT FALLS OUT OF PLACEMENT RATHER THAN A FLAG. The `if check:` block returns before the human board is built, so a footer line added in the `else` branch is unreachable from `--check` by construction. State that reason rather than adding a guard that implies the two could otherwise collide.
  THE TWO EXISTING ADVISORY SECTIONS ARE THE PRECEDENT and their comments already state the never-affect-the-exit-code rule, so cite them rather than re-arguing it.
  - Depends on: E-03
  - Expected outcome: no `Drift` is constructed for inbox entries; `aw attention` and `aw attention --check` exit codes provably unchanged with a non-empty inbox; `--check` silence explained by the early return rather than by a new guard.
  - Execution state: performed

### Task group 4: prove the safety property mechanically

- [x] E-05 PORT THE RECOVERED TESTS INTO `tests/test_attention.py`, INCLUDING THE PATCHED-OPEN PROOF, ADAPTED TO THIS FILE AS IT IS NOW.
  THE CENTRAL TEST IS THE ONE THAT MAKES OPENING FAIL. A correct count does NOT establish that nothing was read, because an implementation that parses every drop counts correctly too. So patch `builtins.open` and `Path.open`/`Path.read_text`/`Path.read_bytes` to raise, and assert the count still succeeds. Without this test the plan's central safety claim rests on a comment.
  THE RECOVERED TEST NEEDS AN IMPORT THIS FILE DOES NOT HAVE. It uses `contextlib.ExitStack`, and `tests/test_attention.py` today imports exactly `from contextlib import redirect_stderr, redirect_stdout`, with no `ExitStack`. Add it, or nest the patches; either is fine, but do not assume the import is there.
  BUILD EVERY CASE IN A TEMPORARY REPO AND NEVER READ THE REAL `.aw/inbox/`. It is gitignored, per-checkout, and will change as drops are adopted, so a test pinned to it passes on one machine and fails on another. The file already builds temp repos with `_mk_repo` and drives the CLI with an `argparse.Namespace` plus `attention.run` under `redirect_stdout`; reuse that.
  THE REQUIRED CASES, all present in the recovered blob: a MISSING directory counts zero, prints nothing, and creates neither `.aw/` nor `.aw/inbox/`; N files count N; a hidden file counts; a non-`.md` file counts; a nested directory counts as one entry; a bookkeeping-only inbox (`README.md` plus `.gitkeep`) counts ZERO and then 1 once a real drop lands; a sibling `.aw/records/comms/shared/inbox/` holding four files counts ZERO (the anchored-path property); the patched-open proof; the footer line appearing ALONGSIDE the setup notice rather than replacing it; no `Item` created and the class tally unchanged; and `aw attention --check` exit codes unchanged by a waiting drop.
  DROP THE TTY PREMISE THE RECOVERED TEST'S DOCSTRINGS CARRY. They explain `--no-color` as keeping a `has_hidden and colored` branch "out of the way" and warn that a plain `redirect_stdout` yields the agent record. Both are stale: the branch was refactored away and the non-TTY-selects-AGENT policy was retracted (`select_output`: "TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE MODE"). Keep `--no-color` for text stability and say THAT.
  PUT THE NO-WRITE ASSERTION BESIDE ITS EXISTING TWIN. The file already has a scan-does-not-stamp-`.aw/` assertion in `ScanTests.test_scan_classification_and_immutability`, which exists because write-on-read was a real defect here.
  - Depends on: E-04
  - Expected outcome: every listed case covered in temporary repos, with the patched-open test proving no file is opened and the both-conditions test proving footer composition; the `ExitStack` (or nested-patch) import present; no test reads the real `.aw/inbox/`; no test docstring asserts the retracted non-TTY routing or the removed `elif` chain.
  - Execution state: performed

- [x] E-06 SHOW THE FEATURE WORKING END TO END AND PROVE BOTH MACHINE SURFACES BYTE-UNCHANGED.
  DEMONSTRATE IT, do not only unit-test it: build a temporary repo, drop several files including a hidden one and a non-`.md` one, run the real board, and paste it showing the line; then drain to bookkeeping-only and paste the board showing NO line.
  PROVE THE JSON DID NOT MOVE, AND USE TODAY'S VERSION. `attention.render_json` emits `schema_version`, `mapping_version`, `valid`, `stranded_lanes`, `items`, `violations`, and `SCHEMA_VERSION` is `4` (the old plan reasoned about `3`, and `tests/test_attention.py` asserts `obj["schema_version"] == 4`). Paste the top-level key list and the version before and after, IDENTICAL and unbumped. Adding the count to the JSON is OQ-01 and is NOT this plan.
  PROVE THE AGENT RECORD DID NOT MOVE EITHER, which is the surface OQ-02 is about: paste the `--agent` JSONL record for a repo with a waiting drop and show `findings` unchanged from the no-drop case. F-09 measures why this matters.
  RUN THE ADJACENT SUITES, OF WHICH THERE ARE FOUR AND NOT THREE (PR-002): `tests/test_attention.py`, `tests/test_attention_contract.py`, `tests/test_prompts_attention.py` AND `tests/test_attention_blind_spot.py`. That fourth file was missed at authoring and matters here: it drives `attention.scan` and asserts the records-scan drift rules (`attention.unclassified-tree`, `attention.uninventoried-tree`) over fixture trees, which is the exact surface a change to the scanned module could perturb, and it passes today (`9 passed`). The old plan named four DIFFERENT files (`test_attention_notices.py`, `test_attention_priority_blocker.py`, `test_attention_compact.py`, `test_attention_stem.py`) that are NOT in `tests/` today, so do not reconcile against its list either. `test_attention_contract.py` is the tripwire: if it needs changing, the design leaked into classification. NOTE A REASSURING MEASUREMENT taken at review: a fixture repo holding `.aw/inbox/drop.md` produces an EMPTY drift rule set from `attention.scan`, so the inbox does not trip the records scan and the blind-spot suite should stay green on its own; run it to confirm rather than to discover.
  - Depends on: E-05
  - Expected outcome: pasted real board output with and without a populated inbox; the JSON top-level key list and `schema_version: 4` proven unchanged; the `--agent` record's `findings` proven unchanged; ALL FOUR existing attention suites green with `test_attention_contract.py` unmodified.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `attention.setup_needed` IS THE EXACT PRECEDENT for the counter: derived read-only, swallows exceptions, its docstring stresses it "NEVER creates anything", feeds a footer nudge, touches neither items nor exit code.
- THE FOOTER IS NO LONGER AN `elif` CHAIN. `attention.run` builds `footer_lines: list[str] = []` then a single `if needs_setup:`. The comment inside it says "The --all hint lives on the count line now; do not repeat it here". The three-branch chain the recovered code and the original plan were built around was refactored away.
- `agent_workflows/attention.py` DOES NOT IMPORT `os`. Measured by attribute (`hasattr(attention, "os")` is False) and by reading the import block. The recovered `os.scandir` body therefore needs a new import.
- SINGULARIZATION HAS A PRECEDENT IN THE SAME FUNCTION: `count_noun = "artifact" if shown_count == 1 else "artifacts"`.
- ADVISORY OUTPUT NEVER AFFECTS THE EXIT CODE, stated in the code's own comments for the `release-gate-warnings` and `order-notices` sections, and the exit code is owned by `core.drift_exit_code(drift)`.
- `--check` RETURNS BEFORE THE BOARD IS BUILT, in `attention.run`'s `if check:` block, so a footer addition is unreachable from `--check` by construction rather than by a guard.
- `SCHEMA_VERSION` IS `4`, and `tests/test_attention.py` asserts `obj["schema_version"] == 4`. The original plan's reasoning about a bump from `3` is stale.
- `.aw/inbox/README.md` IS TRACKED (`git ls-files .aw/inbox`). The bookkeeping exclusion is therefore load-bearing today, not a prediction about a sibling plan.
- `.aw/inbox/` IS GITIGNORED AND PER-CHECKOUT (`/inbox/` in `.aw/.gitignore`), and the pattern is ANCHORED on purpose: a bare `inbox/` would swallow the TRACKED comms lane `records/comms/shared/inbox/` and break `aw install`.
- `aw adopt` IS SHIPPED (`agent_workflows/artifact_adopt.py`; `--help` exits 0), so the nudge can name a real remedy. Verify by invoking, not by reading `lznpv6`'s status.
- NON-TTY STDOUT DOES NOT SELECT AGENT MODE. `select_output`'s docstring: "TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE MODE", and it records that the opposite claim "USED TO" be published and was never implemented. A redirected board is a BOARD.
- `tests/` HOLDS FOUR ATTENTION SUITES (corrected at review, PR-002): `test_attention.py`, `test_attention_contract.py`, `test_prompts_attention.py` AND `test_attention_blind_spot.py`, the last of which drives `attention.scan`'s records-scan drift rules and was missed at authoring. Four DIFFERENT files the original plan named do not exist.
- `tests/test_attention.py` IMPORTS NO `ExitStack`; its contextlib import is `redirect_stderr, redirect_stdout`.
- SUITE BASELINE, AND IT IS NOT GREEN (corrected at review, PR-003). Authoring measured `3387 passed, 2 skipped, 3 warnings in 63.89s` with `207 deselected`; review re-measured `1 failed, 3491 passed, 2 skipped, 3 warnings in 153.50s` with `208 deselected`. The single failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a PRE-EXISTING date-boundary bug pinning a workflow-history line against a hardcoded date the clock has passed; it touches neither declared path. Run bare (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the marker filter. Re-derive your own baseline and compare NODE IDS, not totals, which is exactly why the node-id rule was already right: the bar is an UNCHANGED named failure set, never a green run, and the executor must NOT fix that test (out of scope, another party's).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured in this lane worktree at HEAD `2c22b5bd` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-01 | HIGH | `agent_workflows/attention.py`, `tests/test_attention.py` | THE ITEM'S HEADLINE REPRODUCES: neither declared Scope-Path carries the work. `git show main:agent_workflows/attention.py \| grep -c inbox` -> `0`; same for `tests/test_attention.py`. | ran both |
| F-02 | HIGH | `agent_workflows.attention` | ABSENT BEHAVIORALLY, NOT ONLY BY GREP. `hasattr(attention, "inbox_waiting")` is False, and a real board via `cli.main(["attention", "--dir", <tmp>, "--no-color"])` against a temp repo with four `.aw/inbox/` drops printed `## ready (1)` / one row / `1 artifact shown` and NO footer line. | ran it |
| F-03 | HIGH | git history | THE FOOTER STRING IS IN NO REACHABLE COMMIT, EVER. `git log --all --oneline -S'waiting in \`.aw/inbox/\`' -- '*.py'` returns nothing. | ran it |
| F-04 | MED | `tests/` | THE TEST CLASSES WHOSE PASSING OUTPUT `9iiqmm`'s V-01 and V-02 PASTE DO NOT EXIST. `grep -rn "InboxWaitingCountTests\|InboxFooterNudgeTests" tests/` returns no match, and the current `tests/test_attention.py` class list contains neither. | ran it |
| F-05 | N/A | `tests/test_attention.py` | THE EXISTING SUITE IS GREEN, so the absence is not masked by a broken file: `python3 -m pytest tests/test_attention.py -o addopts=""` -> `39 passed in 4.16s`. | ran it |
| F-06 | HIGH | dangling objects `9effdcef`, `de2fbe7c` | THE BYTES ARE RECOVERABLE NOW AND ARE PRUNABLE. Both blobs are PACKED and present (`git cat-file -s` -> `138154` and `114999`); `git cat-file blob` extracts each. Holding commits `5c55d020`, `888c20a1` (2026-09-20) and `3569ed07` (2026-09-23) are dangling. `gc.pruneExpire` and `gc.auto` are both UNSET, so git's 2-week prune default already covers the two September 20 commits. | `cat-file`, `config --get`, `log -1 --date=iso` |
| F-07 | HIGH | `attention.run` footer block; recovered blob `9effdcef` | THE RECOVERED CODE DOES NOT APPLY AS-IS, AND ITS CENTRAL COMMENT WOULD SHIP A FALSEHOOD. `main` is 2913 commits past the dangling base `1a011e17`. A diff of the two footer blocks shows the recovered one patches `if needs_setup and has_hidden / elif needs_setup / elif has_hidden and colored`; today's is a single `if needs_setup:` with the comment "The --all hint lives on the count line now; do not repeat it here". So the recovered comment's whole argument ("NOT another `elif` on the chain above ... the chain renders exactly ONE line") describes code that no longer exists. `attention.py` also no longer imports `os`. | `git rev-list --count`, block diff, `hasattr` |
| F-08 | MED | `.aw/inbox/README.md` | THE BOOKKEEPING EXCLUSION IS NOW MEASURED-NECESSARY, NOT PREDICTED. `git ls-files .aw/inbox` -> `.aw/inbox/README.md`, so the file is TRACKED and present in every clone. Without the exclusion the nudge fires on a fully drained inbox forever, on every machine. The original plan's F-11 argued this prospectively about a sibling plan; it is now a fact in the tree. | `git ls-files`, `ls -la` |
| F-09 | MED | `result_types.CommandResult.to_agent_record` | THE COST OF THE OBVIOUS AGENT-SURFACE FIX IS REAL AND REPRODUCES. `findings` is derived as `len(self.diagnostics) if self.diagnostics else self.data.get("findings", 0)` with NO severity filter. I built a clean `CommandResult` carrying ONE `severity="warning"` `Diagnostic`: the record read `outcome: clean, exit: 0, findings: 1` against `findings: 0` without it. A phantom finding on a healthy repo is a worse contract break than the invisibility, which is why OQ-02 does not just adopt the `order-notices` precedent. | constructed the record and printed it |
| F-10 | HIGH | `runner_shared.compute_scope_reconciliation`, `ipd_lifecycle._reconcile_scope`, `runner_shared.handle_zero_work_retry` | THE MECHANISM THAT LOST THE WORK IS STILL LIVE, AND THE ITEM DELIBERATELY DID NOT DIAGNOSE IT. `compute_scope_reconciliation` builds `acks` for EVERY `in_scope_unmodified` path with the wording "declared-but-unmodified (auto-acknowledged by <host>)". Driving `_reconcile_scope` with BOTH of `9iiqmm`'s declared paths unmodified and those auto-acks returned `ok=True`, `missing_reasons=()`, `missing_acks=()`. So a finalize whose execution touched NEITHER declared path reconciles clean by construction. The zero-work predicate cannot catch it either: `handle_zero_work_retry` returns immediately unless `item["status"] == "partial"`, and a self-finalized item is `executed`. NOT fixed here; carried. | drove `_reconcile_scope`; read both symbols |
| F-11 | LOW | `9iiqmm` F-12, `## Scope check`, OQ-04 | THE OLD PLAN'S NON-TTY PREMISE IS FALSE AND MUST NOT BE INHERITED. `select_output`'s docstring states "TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE MODE" and that the opposite claim was published and never implemented. Confirmed: a redirected `cli.main(["attention", ...])` rendered the BOARD. `dv7c49` already appended this correction to the terminal record, so this plan cites it rather than re-fixing it. | `select_output` docstring; ran it redirected |
| F-12 | N/A | `tests/`, `SCHEMA_VERSION` | THE ORIGINAL PLAN'S TEST AND SCHEMA ENVIRONMENT HAS MOVED. `SCHEMA_VERSION` is `4`, not `3` (re-verified at review). `tests/test_attention.py` imports no `ExitStack` (re-verified: its contextlib import is exactly `redirect_stderr, redirect_stdout`), which the recovered test needs. Four files that plan told its executor to run are absent. **CORRECTED AT REVIEW (PR-002): this row said only THREE attention suites exist, and there are FOUR.** `tests/test_attention_blind_spot.py` also exists and passes (`9 passed`); it drives `attention.scan` and asserts the records-scan drift rules, which is the surface most exposed to a change in the scanned module, so E-06 must run it. | grep, `ls tests/ \| grep -i attention`, import block, targeted run |
| F-13 | N/A | full bare suite | BASELINE, AND IT IS NOT GREEN. Authoring measured `3387 passed, 2 skipped, 3 warnings in 63.89s`, `207 deselected` at HEAD `2c22b5bd`. **RE-MEASURED AT REVIEW (PR-003): `1 failed, 3491 passed, 2 skipped, 3 warnings in 153.50s`, `208 deselected` at HEAD `db2c6e3d`.** The failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a PRE-EXISTING date-boundary bug (a hardcoded date the clock has passed) touching neither declared path. So "zero failures" is not an achievable bar; the bar is an unchanged failing NODE-ID set, which is what this row's own advice to compare node ids rather than totals already implied. Do NOT fix that test. | `python3 -m pytest` bare at both HEADs; isolated re-run of the failure |
| F-14 | MED | `git count-objects`, `gc --cruft` default, object storage of both blobs | **ADDED AT REVIEW: THE PRUNE URGENCY IS BOTH STRONGER AND SOFTER THAN THE PLAN STATES, AND AN EXECUTOR NEEDS BOTH HALVES (PR-001).** STRONGER: `git count-objects -v` reports `count: 8875` loose objects against git's default `gc.auto` threshold of 6700, so auto-gc is ALREADY ARMED, not merely a future possibility; `gc.auto` and `gc.autoPackLimit` are both unset, so the defaults govern. SOFTER: git's `--cruft` behavior is ON BY DEFAULT, so an expiring gc moves unreachable objects into a CRUFT PACK rather than deleting them, and both blobs are PACKED rather than loose (neither appears at `.git/objects/<2>/<38>`), so one auto-gc is less likely to destroy them than "prunable" suggests. NET: the window is real and open, its exact closing is not predictable, and the correct mitigation is unchanged, namely E-01's extract-first ordering. State both halves so an executor who finds the blobs intact does not conclude the warning was false. | `git count-objects -v`; `git config --get gc.auto` and `gc.autoPackLimit` both exiting 1; `git help gc` on `--cruft`; loose-path existence check for both shas |
| F-15 | LOW | sibling pending plans | **ADDED AT REVIEW: TWO APPROVED SIBLINGS DECLARE BOTH OF THIS PLAN'S PATHS, AND NEITHER COLLIDES, WHICH IS WORTH RECORDING BECAUSE THE PLAN CARRIED NO CROSS-PLAN SURVEY.** `r61br4` (`approved`) declares `agent_workflows/attention.py` AND `tests/test_attention.py`; `o6ksmw` (`approved`) declares `tests/test_attention.py`. Measured: neither mentions `footer` or `footer_lines` anywhere, so neither touches the block E-03 edits; `r61br4` resolves the run column through the lifecycle resolver and `o6ksmw` adds selector-contract test coverage. Seven further approved plans declare `attention.py` for unrelated functions. The runner isolates each item in its own worktree and revalidates on merge, so this is a note for interpreting a surprising diff, not a sequencing hazard. | `- Scope-Paths:` scan over `.aw/records/plans/pending/`; `grep -n "footer\|footer_lines"` returning nothing in both plans |

## Proposed changes (ordered, validatable)

1. E-01 extracts both recovered blobs to scratch paths outside the repository and proves they still exist, before any code is written, because they are prunable (F-06).
2. E-02 ports `inbox_waiting` beside `attention.setup_needed`, adds the missing `import os`, and states the listing-not-parsing rule and the measured tracked-README exclusion in its docstring.
3. E-03 renders one advisory footer line under an independent `if`, in the house imperative form with house-precedent singularization, naming `aw adopt <path>` after invoking the verb, with a comment describing TODAY's single-`if` footer rather than the removed chain (F-07).
4. E-04 keeps the exit code and `--check` untouched by never constructing a `Drift`, and explains `--check` silence by the early return.
5. E-05 ports the recovered tests including the patched-open safety proof, adapting the missing `ExitStack` import and dropping the two stale premises their docstrings carry.
6. E-06 demonstrates the board end to end and proves the JSON shape at `schema_version: 4` and the `--agent` record's `findings` both unchanged.

## Deferred / out of scope (with reason)

- **THE SYSTEMIC QUESTION OF HOW A LANE SELF-FINALIZED AND CLOSED ITS ITEM WITH AN EMPTY DIFF IS NOT FIXED HERE.** The backlog item explicitly does not decide it, and F-10 measures the two halves: `compute_scope_reconciliation` auto-acknowledges every declared-but-unmodified path (so all-paths-unmodified reconciles `ok=True`), and `handle_zero_work_retry` only ever considers `partial`, so a self-finalized `executed` item is invisible to it. Fixing that changes a gate every run passes through and needs its own measurement across runs; doing it inside a two-file feature plan would be exactly the opportunistic scope broadening the execution contract forbids. FILED AT AUTHORING as backlog `gmbdxe` (`bug`, `Blocks-Release: next`) carrying the F-10 measurement and three costed candidate fixes, rather than left for the executor: it is a live defect in its own right and the row needs a carrier that is not the item this plan graduated from.
  - Carrier: gmbdxe
- **ADDING THE COUNT TO `--format json` IS NOT DONE HERE.** OQ-01. `render_json`'s object is a versioned consumer contract at `schema_version: 4` with a test asserting that value, so a new top-level key is a deliberate bump with its own justification, out of proportion to a human nudge. The count must also never go inside `items`, where it would be classified.
  - Carrier-Declined: No obligation is left outstanding. OQ-01 is resolved NO for this plan on a stated contract reason, and a future consumer needing the number can bump the schema on its own merits; nothing is left half-done.
- **SURFACING THE COUNT ON THE `--agent` SURFACE IS NOT DECIDED HERE.** OQ-02, and it is the one genuine maintainer call in this plan. F-09 reproduces the blocker: the natural route (a WARNING `Diagnostic`, the `order-notices` precedent) inflates a clean record's `findings` from 0 to 1 because `to_agent_record` counts diagnostics without regard to severity. Note the audience premise has CHANGED since the original plan asked this: piped agents already see the board (F-11), so the remaining question is strictly about an EXPLICIT `--agent`/`--json` consumer. FILED AT AUTHORING as backlog `xqem10` (`followup`, maintainer-owned) carrying all three costed routes and the reproduced `findings` measurement, so the question survives this plan reaching `executed/`.
  - Carrier: xqem10
- **FIXING THE SEVERITY-BLIND `findings` COUNT IS GENUINELY OUT OF SCOPE.** It is a repo-wide agent-protocol contract in `agent_workflows/result_types.py`, which this plan does not declare. F-09 measures it so the next reader of OQ-02 need not rediscover it. Two open backlog items already sit on the same `findings`/severity tally seam (`zosk0a`, `xqm16x`), so the concern has a home.
  - Carrier-Evidence: .aw/records/backlog/done/20260920-checkinfotally-01-zosk0a-check-info-severity-mislabelled.backlog.md
- **ANY EDIT TO `9iiqmm` OR ITS REVIEW RECORD IS FORBIDDEN AND UNNECESSARY.** Both are terminal records, `AGENTS.md` permits only an appended history line pointing at later work, and `dv7c49` has ALREADY appended exactly that (recording both the falsified non-TTY premise and the never-landed implementation, and naming `an77ub`). Re-opening or re-closing backlog `plbkp5` is equally done: `dv7c49` E-04 moved it to `graduated` with its reasoning recorded.
  - Carrier-Declined: No obligation is left outstanding. The corrective appends and the item re-open are both already performed by executed plan dv7c49, so there is nothing for this plan or a successor to carry.
- **ANY CHANGE TO `selectors._ID_RE` IS OUT.** This plan's listing-only constraint is independent of identity-extraction bounding and stays correct after any such fix lands; it is defense in depth, not a workaround.
  - Carrier-Declined: No obligation is left outstanding. Listing-only is the correct implementation on its own merits regardless of how identity extraction is bounded, so nothing is postponed by excluding it.
- **ANY CHANGE TO WHAT `.aw/inbox/` IS, its location, or its gitignore status IS OUT.** It sits outside `.aw/records/` deliberately so no records sweep can enumerate a drop as an artifact, which is the premise this feature depends on rather than something it should revisit.
  - Carrier-Declined: No obligation is left outstanding. The current siting is correct and this plan relies on it; no deferred work exists.
- **A TYPED INVENTORY OF INBOX CONTENTS (kinds, ages, topics) IS OUT.** It would require reading files, which the hard constraint forbids. A count is the whole feature.
  - Carrier-Declined: No obligation is left outstanding. The typed inventory is refused on a safety ground rather than postponed, since reading a drop is the exact hazard the feature is built to avoid.
- **FAILING `--check` ON A NON-EMPTY INBOX IS OUT.** A waiting drop is a local, gitignored condition other machines cannot see, so it is not a repository defect. E-04 makes this structural rather than a matter of taste.
  - Carrier-Declined: No obligation is left outstanding. This is a settled design property of the feature, enforced by E-04 and its validation, not deferred work.

## Scope check

- Over-scope: none. Both declared paths are modified: `agent_workflows/attention.py` by E-02 through E-04 (one new module import, one new function plus its constant, one new footer block), and `tests/test_attention.py` by E-05 and E-06. `agent_workflows/attention_contract.py` is deliberately NOT declared, and a felt need to touch it is the tripwire that the design drifted into classification. `agent_workflows/result_types.py` is NOT declared even though F-09 reads from it. The recovered blobs are extracted OUTSIDE the repository by E-01 and must never be committed.
- Cross-plan: ADDED AT REVIEW (F-15), because the plan carried no sibling survey despite declaring a heavily contended module. Two APPROVED plans declare paths this plan declares (`r61br4` both of them, `o6ksmw` the test file) and NEITHER touches the footer block E-03 edits (measured: neither mentions `footer` or `footer_lines`); seven further approved plans declare `attention.py` for unrelated functions. The runner isolates each item in its own worktree and revalidates on merge, so no dependency edge is declared and none is needed.
- Under-scope: stated rather than left as `none`, and the limits differ from the original plan's because the environment moved. `aw attention --format json` gains NOTHING (OQ-01) and its `schema_version` stays `4`. The `--agent` surface gains NOTHING (OQ-02), and F-09 states the measured reason. But the human-board reach is BROADER than `9iiqmm` promised, not narrower: since non-TTY stdout selects COLOR and not MODE (F-11), the line renders on a piped or redirected invocation too, so every agent reading `aw attention` through a pipe sees it. It is absent only under `--agent`, `--json`/`--format json`, `--check`, and the `--id6-only`/`--paths`/`--filenames` early return. The systemic finalize gap (F-10) is measured and carried, not closed.

## Required tests / validation

All validation runs BARE (`python3 -m pytest`), per the execution contract: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the marker filter, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Where per-test counts are genuinely needed, clear the defaults explicitly with `-o addopts=""`.

RE-DERIVE YOUR OWN BASELINE; DO NOT TRANSCRIBE F-13's DIGITS, AND DO NOT EXPECT A GREEN RUN (PR-003). Authoring measured `3387 passed, 2 skipped` with `207 deselected` at HEAD `2c22b5bd`; review measured `1 failed, 3491 passed, 2 skipped` with `208 deselected` at HEAD `db2c6e3d`, the failure being the pre-existing `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` date-boundary bug. Run bare FIRST, record your number AND your failing node-id set, and state every delta against YOUR number, comparing failing NODE IDS rather than totals. Do NOT fix that test: it is outside both declared paths and is another party's.

1. TARGETED: `python3 -m pytest tests/test_attention.py tests/test_attention_contract.py tests/test_prompts_attention.py tests/test_attention_blind_spot.py -o addopts=""` passes (FOUR files, per PR-002; review measured the fourth at `9 passed`), with the new cases in the selected set and counts stated against your own re-derived per-file baselines (authoring measured `tests/test_attention.py` alone at `39 passed`).
2. FULL BARE SUITE: `python3 -m pytest` shows an UNCHANGED failing node-id set against YOUR baseline (not zero failures, per PR-003) and a passed count increased by exactly the number of tests E-05 adds.
3. THE SAFETY PROOF IS THE SINGLE MOST IMPORTANT TEST, and a passing count is NOT evidence of it: paste the patched-open test's output, since an implementation that parses every drop would also count correctly.
4. ALL FOUR ATTENTION SUITES PASS, including `tests/test_attention_blind_spot.py` which authoring missed (PR-002), and `tests/test_attention_contract.py` MUST PASS UNMODIFIED. It owns enum totality and the class maps; if it needs editing, the count has leaked into classification and the design is wrong. Stop and report rather than editing it.
5. BOTH MACHINE SURFACES BYTE-UNCHANGED: paste `render_json`'s top-level key list and `schema_version` with and without a waiting drop, IDENTICAL and still `4`; and paste the `--agent` record's `findings` for both, IDENTICAL.
6. EXIT-CODE EQUALITY: paste `aw attention` and `aw attention --check` exit codes for an empty inbox and for a populated one, all equal, and pin it as a test rather than a one-off observation.
7. RECOVERY PROOF: paste `git cat-file -s` for both blob shas taken DURING this execution, demonstrating E-01 recovered from the object store rather than from this plan's excerpts.

## Spec / documentation sync

NO SPEC IS AMENDED, AND I VERIFIED THAT RATHER THAN ASSERTING IT. `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` Section 8.1 specifies the render surfaces as "the human board grouped by class ... gated items showing the blocker, hidden `done`/`parked` unless filtered. NO time-based hot windows", plus `--format json` (Section 8.3, the versioned object), `--check`'s fail-closed exit contract, "Writes NOTHING to disk", and byte-determinism (Section 8.5). A case-insensitive grep for `footer` over that spec returns ZERO hits, which is why the two existing advisory footer lines were added without amending it, and why a third does not amend it either. No `.spec.md` path enters `- Scope-Paths:`.

THE TWO INVARIANTS THE SPEC DOES BIND AND THIS FEATURE TOUCHES ARE BOTH CARRIED INTO VALIDATION. Nothing is written (E-02's no-create requirement, proven by the missing-directory test asserting `.aw/` still does not exist) and output stays byte-deterministic (Section 8.5: the count is derived from a directory listing on each invocation and the rendered line carries no mtime or other time-derived value; do NOT add one).

`AGENTS.md` already documents `.aw/inbox/` and is INSTALLED from `agent_workflows/engine.py`, so if the inbox contract ever needs restating, the generator is the file to edit and never `AGENTS.md`. It does not need restating here: this plan surfaces a count and changes no rule about what an inbox file is. `.aw/inbox/README.md` likewise already tells a reader to run `aw adopt`, which is the remedy the nudge names.

## Open questions

### OQ-01: Should the waiting count appear in `aw attention --format json`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as NO for this plan, on the same reasoning the original plan gave and with today's numbers. `attention.render_json` emits `schema_version`, `mapping_version`, `valid`, `stranded_lanes`, `items`, `violations`, and `tests/test_attention.py` asserts `obj["schema_version"] == 4` (the original plan reasoned about `3`; the object has since gained `stranded_lanes` and the version was bumped). Adding a top-level key is a versioned-consumer-contract change requiring a bump plus a test update, which is out of proportion to a human nudge; and the count must NOT go inside `items`, since inbox drops are not artifacts and would then be classified. The feature's purpose is to catch a reader's eye on the board, and per F-11 the board now reaches piped agents too, so the invisibility this question worried about is much smaller than it was. A machine consumer that later needs the number can bump the schema deliberately.

### OQ-02: Should an EXPLICIT `--agent`/`--json` consumer receive the waiting count?

- Blocking: no
- Status: open
- Owner: the maintainer (a judgement about who the nudge is for, and about what `findings` means)
- Carrier: xqem10
- Resolution or deferral rationale: NOT BLOCKING, and deliberately not self-resolved because it is a question about audience and about a shared output contract, not about mechanism. THE PREMISE IS NARROWER THAN WHEN `9iiqmm` ASKED IT (its OQ-04): that plan believed any non-TTY stdout routed to the agent renderer, so it thought the nudge reached an interactive terminal and nothing else. That is false and was retracted (F-11), so a piped `aw attention` already renders the board and every agent reading it through a pipe already sees the line. What REMAINS is strictly whether an explicit `--agent`/`--format json` consumer should get it. THREE ROUTES, COSTED. (a) LEAVE IT, which is this plan's scope: zero risk, and the board already covers human and piped-agent readers. (b) A WARNING `Diagnostic` on the agent path, exactly the `order-notices` precedent in `attention.run` ("an ordering notice must reach an AGENT too, not only the human board"), which does not touch the exit code. MEASURED COST, and it is why this is not free: `to_agent_record` derives `findings` from `len(self.diagnostics)` with no severity filter, so one warning turns a clean record's `findings: 0` into `findings: 1` while `outcome` stays `clean`. I constructed the record and got exactly that (F-09). A consumer reading `findings` as "problems found" sees a phantom finding on a healthy repo, which is a worse contract break than the invisibility it fixes. (c) An `Evidence` value key, which does not inflate `findings`, but the compact agent record sanitizes evidence to the bare key name, so the number is visible only under `--verbose`, making it nearly as invisible as (a). RECOMMEND (a) for this plan with the limit stated honestly in `## Scope check`, and note that route (b) is unblocked the moment the severity-blind tally is fixed, which two existing backlog items (`zosk0a`, `xqm16x`) already cover, so the sequencing matters: do not decide this against today's tally if that tally is about to change. Carried by backlog `xqem10`, filed at authoring, so the question is not lost when this plan reaches `executed/`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `git cat-file -s 9effdcef169e7ad8eafc0c3b22f5432cf1384dc6` and `git cat-file -s de2fbe7ceb1918551ea8f03fc0e8467f056119be` AS RUN DURING THIS EXECUTION, with their byte counts, proving both objects were still present when the port began. Paste the scratch paths the blobs were extracted to and show they are OUTSIDE the repository (an absolute path not under the worktree), plus `git status --porcelain` showing no untracked copy landed in the tree. State explicitly that no `git gc`, `git prune` or `git repack -d` was run. If either object was MISSING, paste the failing command and STOP: do not proceed to E-02 on a rewrite while claiming a port.
  - Observed evidence: Pass. Both objects verified present during execution:
    `git cat-file -s 9effdcef169e7ad8eafc0c3b22f5432cf1384dc6`: 138154
    `git cat-file -s de2fbe7ceb1918551ea8f03fc0e8467f056119be`: 114999
    Extracted scratch paths outside the repository:
    `/tmp/scratch_olmvgw/attention.py.recovered` (138154 bytes)
    `/tmp/scratch_olmvgw/test_attention.py.recovered` (114999 bytes)
    `git status --porcelain` showed no untracked files in the repository tree.
    Explicitly confirmed: no `git gc`, `git prune`, or `git repack -d` was run.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the ported `inbox_waiting` source in full, showing (a) the single anchored path it resolves, proving it is not a recursive search for directories named `inbox`, (b) the `os.scandir` listing call with no `open`/`read_text`/parse anywhere in the body, (c) the docstring stating the visible-as-files-never-interpreted-as-records rule WITH its reason, and (d) the docstring recording the `README.md`/`.gitkeep` exclusion justified by the MEASURED tracked file rather than by a prediction. Paste the diff line adding `import os` to the module. Then paste four runs: a MISSING directory returning 0 without raising, with the parent listed BEFORE and AFTER proving `.aw/` was not created; a populated temp inbox returning the right count; an inbox holding ONLY `README.md` and `.gitkeep` returning 0; and a sibling `.aw/records/comms/shared/inbox/` holding four files returning 0.
  - Observed evidence: Pass.
    Ported `inbox_waiting` source in `agent_workflows/attention.py`:
    ```python
    _INBOX_BOOKKEEPING_NAMES = frozenset({"README.md", ".gitkeep"})


    def inbox_waiting(repo_root: Path) -> int:
        """awinbox Order 03 (`olmvgw`, recovering `9iiqmm`): how many RAW drops are waiting in `<repo>/.aw/inbox/`.

        Structural twin of `setup_needed` above: DERIVED on demand, read-only, swallows its own
        exceptions, NEVER creates anything (in particular it must not create `.aw/inbox/` by looking
        for it), and feeds one advisory footer nudge that touches neither the item list nor the exit
        code.

        LISTS DIRECTORY ENTRIES ONLY; OPENS NO FILE, EVER. Inbox drops are VISIBLE AS FILES here and
        are NEVER INTERPRETED AS RECORDS, and that distinction is the whole safety property of this
        function rather than a style preference. `.aw/inbox/` holds unvetted third-party text, and
        `selectors._ID_RE` is position-unanchored (`(?m)^- Id:\\s*([0-9a-z]{6})\\s*$` applied with
        `.search()` over a whole body), so a `- Id:` line anywhere in a drop - INCLUDING one merely
        QUOTED inside an external report as an example - is harvested as an identity claim and can
        collide with a real artifact's id6, making that artifact unresolvable to `aw set`/`aw show`
        (see `.aw/.gitignore`, which records exactly this hazard as the reason the inbox sits OUTSIDE
        `.aw/records/`). Listing a directory cannot forge an identity; parsing a drop can. So do NOT
        "improve" this by reading front matter, sniffing a body, or classifying a drop by type: use
        `os.scandir`, which yields names without opening anything.

        A MISSING DIRECTORY MEANS ZERO. `.aw/inbox/` is gitignored and therefore per-checkout, so it
        is simply absent in a fresh worktree; absent must not raise, and the caller must print nothing
        for zero, because a nudge that fires when there is nothing to nudge about is noise that trains
        readers to ignore it.

        ONE ANCHORED PATH, NEVER A SEARCH BY NAME. Resolves exactly `<repo>/.aw/inbox/` and never looks
        for directories called `inbox` anywhere else: `.aw/records/comms/*/inbox/` is the TRACKED
        inter-agent comms lane and is unrelated (an unanchored `inbox/` gitignore pattern once
        threatened exactly that path and would have broken `aw install`).

        A NESTED DIRECTORY COUNTS AS ONE ENTRY AND IS NOT WALKED (OQ-02). The number's job is to be
        nonzero and roughly right, not exact; counting a directory as one entry keeps the whole
        operation a single shallow `scandir` that cannot recurse unboundedly.

        BUT THE TREE'S OWN BOOKKEEPING FILES ARE EXCLUDED (`README.md`, `.gitkeep`), because they are
        not waiting for anyone. `.aw/inbox/README.md` is committed scaffolding that documents the lane
        (`git ls-files .aw/inbox` shows it tracked), so counting it would make this nudge fire FOREVER
        on a fully drained inbox on every machine, defeating the silent-when-empty rule above. Every
        other entry counts, including hidden files and non-`.md` drops: a genuine hidden drop (say
        `.report.md`) must not be missed.
        """
        try:
            inbox = Path(repo_root) / ".aw" / "inbox"
            with os.scandir(inbox) as entries:
                return sum(1 for e in entries if e.name not in _INBOX_BOOKKEEPING_NAMES)
        except Exception:
            return 0
    ```
    Diff line adding `import os` to `agent_workflows/attention.py`:
    ```diff
    +import os
    ```
    Four runs output:
    === RUN 1: MISSING DIRECTORY ===
    Before iterdir: []
    inbox_waiting returned: 0
    After iterdir: []
    .aw exists?: False

    === RUN 2: POPULATED TEMP INBOX ===
    inbox_waiting returned: 3

    === RUN 3: BOOKKEEPING ONLY INBOX ===
    inbox_waiting returned: 0

    === RUN 4: SIBLING COMMS INBOX ===
    inbox_waiting returned: 0
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the footer diff in context, showing the new block is an INDEPENDENT `if` appending to `footer_lines` beside the existing `if needs_setup:` and not an `elif`. Paste the new comment in full and confirm by inspection that it contains NO claim about a three-branch `elif` chain (the construct F-07 measured as removed); quote the surviving invariant it states instead. Paste the output of the `aw adopt --help` invocation actually taken at execution (lane-resolved `python3 -m agent_workflows adopt --help`) with its exit status, and the resulting footer string, showing the branch was taken on the verb's real presence. Paste a board with exactly ONE waiting drop and a board with TWO, showing `1 file` and `2 files`. Paste a board where the setup marker is ALSO present, showing BOTH lines (this is the case that would catch an `elif` regression).
  - Observed evidence: Pass.
    Footer diff in context (`agent_workflows/attention.py`):
    ```python
            footer_lines: list[str] = []
            needs_setup = setup_needed(repo_root)
            if needs_setup:
                # The --all hint lives on the count line now; do not repeat it here.
                footer_lines.append("TODO: Run `/aw setup-repo` to set up this repo.")

            # awinbox Order 03 (`olmvgw`, recovering `9iiqmm`): the waiting-inbox-drops nudge.
            # AN INDEPENDENT `if` appending to `footer_lines`, composing with today's single-`if`
            # `setup_needed` notice above rather than competing with it. Do NOT convert either into
            # an `elif`: a dropped-and-forgotten file is especially likely on a fresh checkout that
            # also needs setup, so both lines must render when both conditions hold.
            # ADVISORY ONLY, exactly like the `order_notices` and `release-gate-warnings` sections above:
            # it constructs no `Drift` and therefore CANNOT affect the exit code (owned solely by
            # `core.drift_exit_code(drift)`), invents no status, and creates no `Item` - a waiting local
            # drop in a gitignored directory is not a repository defect, and failing `--check` on a file
            # no other machine can even see would be wrong. It shows ALWAYS, not only under `--all`,
            # because `--all` reveals hidden done/parked ARTIFACTS and an un-adopted drop is not one:
            # it is outstanding work, which is what a nudge is for. It carries no mtime or other
            # time-derived value, preserving the spec's byte-determinism invariant.
            waiting = inbox_waiting(repo_root)
            if waiting:
                noun = "file" if waiting == 1 else "files"
                footer_lines.append(
                    f"TODO: {waiting} {noun} waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one."
                )

            if footer_lines:
                board = board.rstrip("\n") + "\n" + "\n".join(footer_lines) + "\n"
    ```
    New comment confirmed to contain NO claim about a three-branch `elif` chain. Surviving invariant quoted: "AN INDEPENDENT `if` appending to `footer_lines`, composing with today's single-`if` `setup_needed` notice above rather than competing with it. Do NOT convert either into an `elif`: a dropped-and-forgotten file is especially likely on a fresh checkout that also needs setup, so both lines must render when both conditions hold."
    `python3 -m agent_workflows adopt --help` exit status: 0.
    Footer string: `TODO: {waiting} {noun} waiting in \`.aw/inbox/\`. Run \`aw adopt <path>\` to file one.`
    Real board with ONE waiting drop:
    ```
    ## ready (1)
    - [specs] .agents/docs/specs/s.md (approved)
    1 artifact shown
    TODO: 1 file waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one.
    ```
    Real board with TWO waiting drops:
    ```
    ## ready (1)
    - [specs] .agents/docs/specs/s.md (approved)
    1 artifact shown
    TODO: 2 files waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one.
    ```
    Real board with setup marker AND 1 waiting drop (composition):
    ```
    ## ready (1)
    - [specs] .agents/docs/specs/s.md (approved)
    1 artifact shown
    TODO: Run `/aw setup-repo` to set up this repo.
    TODO: 1 file waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one.
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a grep or diff proving no `Drift` is constructed anywhere in the new code. Paste the exit codes of `aw attention` and `aw attention --check` for a repo with an EMPTY inbox and for the same repo with a populated one, showing all four equal. Paste `aw attention --check`'s output with a waiting drop present, showing the line is ABSENT, and quote the `if check:` early return that makes that structural rather than a guard.
  - Observed evidence: Pass.
    Grep over diff for `drift`:
    `git diff agent_workflows/attention.py | grep -i "drift"`:
    ```
    +        # it constructs no `Drift` and therefore CANNOT affect the exit code (owned solely by
    +        # `core.drift_exit_code(drift)`), invents no status, and creates no `Item` - a waiting local
    ```
    Exit codes equality demonstration:
    Empty inbox - plain exit: 0, check exit: 0
    Full inbox  - plain exit: 0, check exit: 0
    All four exit codes equal: True (all 0)
    `aw attention --check` output with waiting drop present:
    ```
    aw attention --check: the view is valid.
    ```
    Contains "waiting in `.aw/inbox/`"?: False
    `if check:` early return in `agent_workflows/attention.py` (lines 4290-4305):
    ```python
        if check:
            exit_code = core.drift_exit_code(drift)
            if ctx.is_agent:
                ...
                return get_renderer(ctx).emit(res, ctx)
            if drift:
                for d in drift:
                    sys.stdout.write(f"{d.location}: {d.rule}: {d.detail}\n")
            else:
                sys.stdout.write("aw attention --check: the view is valid.\n")
            return exit_code
    ```
    This structural early return exits before human board and footer construction.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new test classes' names and the PASSING run of the file with `-o addopts=""` and its count, stated against your own re-derived per-file baseline. Paste the patched-open test in full plus its passing output, since that test is the plan's central safety claim; then PROVE IT BITES by pasting the exception the patched `open` raises when it IS reached, demonstrated by calling the patched sentinel directly inside the test's own context (corrected at review, PR-004: the original wording also offered "showing it FAIL against a deliberately-parsing implementation", which asks the executor to author a knowingly-wrong implementation of the function they just ported, an unnecessary detour whose artifact must then not be committed; the sentinel demonstration establishes the same property and is the half the item already offered). Paste the `ExitStack` (or nested-patch) import diff. Paste a grep over the new tests showing NO reference to the real `.aw/inbox/` and no docstring asserting the retracted non-TTY routing or the removed `elif` chain.
  - Observed evidence: Pass.
    New test classes: `InboxWaitingCountTests` (5 tests) and `InboxFooterNudgeTests` (7 tests), total 12 new tests.
    `python3 -m pytest tests/test_attention.py -o addopts=""` passing run:
    `============================== 65 passed in 9.98s ==============================`
    (Pre-execution baseline was 53 passed; exactly +12 new tests passed).
    Patched-open test in full (`tests/test_attention.py`):
    ```python
        def test_counts_without_opening_any_file(self):
            """THE CENTRAL SAFETY PROOF. A correct count does NOT establish that nothing was read: an
            implementation parsing every drop would also count correctly. So make opening RAISE and
            require the count to succeed anyway. Parsing a drop would let that drop's CONTENT assert an
            identity (`selectors._ID_RE` is position-unanchored and harvests a body-QUOTED `- Id:`)."""
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                box = self._inbox(root)
                (box / "a.md").write_text("- Id: abc123\n", encoding="utf-8")
                (box / "b.txt").write_text("x", encoding="utf-8")
                (box / ".c.md").write_text("x", encoding="utf-8")

                def _boom(*a, **kw):
                    raise AssertionError("the inbox counter must never OPEN a file")

                with ExitStack() as stack:
                    stack.enter_context(mock.patch("builtins.open", _boom))
                    for attr in ("open", "read_text", "read_bytes"):
                        stack.enter_context(mock.patch.object(Path, attr, _boom))
                    self.assertEqual(att.inbox_waiting(root), 3)
    ```
    Passing run of patched-open test (`python3 -m pytest tests/test_attention.py -k test_counts_without_opening_any_file -o addopts=""`):
    `tests/test_attention.py . [100%]`
    `======================= 1 passed, 64 deselected in 0.27s =======================`
    Proof sentinel bites (direct invocation inside sentinel context):
    `builtins.open sentinel raised: AssertionError('the inbox counter must never OPEN a file')`
    `Path.read_text sentinel raised: AssertionError('the inbox counter must never OPEN a file')`
    `ExitStack` import diff:
    ```diff
    -from contextlib import redirect_stderr, redirect_stdout
    +from contextlib import ExitStack, redirect_stderr, redirect_stdout
    ```
    Grep check over new tests (`git diff tests/test_attention.py | grep -E "REPO_ROOT|elif chain|non-TTY"`): returned exit 1 (0 hits).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste a real board for a temp repo holding several drops including a hidden one and a non-`.md` one, showing the line; then paste the board after draining to bookkeeping-only, showing NO line. Paste `render_json`'s top-level key list and `schema_version` for both states, IDENTICAL and still `4`. Paste the `--agent` JSONL record for both states, showing `findings` IDENTICAL. Paste the passing runs of ALL FOUR attention suites (`tests/test_attention.py`, `tests/test_attention_contract.py`, `tests/test_prompts_attention.py`, `tests/test_attention_blind_spot.py`; the fourth was missed at authoring, PR-002), and `git diff --stat` showing `tests/test_attention_contract.py` UNMODIFIED. Paste the FULL bare `python3 -m pytest` summary line and state the delta against YOUR baseline: the failing NODE-ID set UNCHANGED (review measured one pre-existing failure, so zero failures is not the bar, PR-003) and the passed count up by exactly the number of tests added.
  - Observed evidence: Pass.
    Real board with 3 drops (including hidden drop `.hidden_drop.md` and non-`.md` drop `notes.txt`):
    ```
    ## ready (1)
    - [specs] .agents/docs/specs/s.md (approved)
    1 artifact shown
    TODO: 3 files waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one.
    ```
    Real board after draining to bookkeeping-only (`README.md`, `.gitkeep`):
    ```
    ## ready (1)
    - [specs] .agents/docs/specs/s.md (approved)
    1 artifact shown
    ```
    Populated JSON keys & schema_version:
    keys: `['items', 'mapping_version', 'schema_version', 'stranded_lanes', 'valid', 'violations']`, schema_version: `4`
    Drained JSON keys & schema_version:
    keys: `['items', 'mapping_version', 'schema_version', 'stranded_lanes', 'valid', 'violations']`, schema_version: `4`
    (Keys and schema_version 4 are IDENTICAL across both states).

    `--agent` JSONL record populated:
    `{"schema": "aw.agent/v1", "kind": "result", "cmd": "attention", "outcome": "clean", "exit": 0, "verified": true, "complete": true, "findings": 0, "evidence": ["attention"], "next": null}`
    `--agent` JSONL record drained:
    `{"schema": "aw.agent/v1", "kind": "result", "cmd": "attention", "outcome": "clean", "exit": 0, "verified": true, "complete": true, "findings": 0, "evidence": ["attention"], "next": null}`
    (Findings 0 and outcome clean are IDENTICAL across both states).

    Passing runs of ALL FOUR attention suites (`python3 -m pytest tests/test_attention.py tests/test_attention_contract.py tests/test_prompts_attention.py tests/test_attention_blind_spot.py -o addopts=""`):
    ```
    tests/test_attention_contract.py ...........................             [ 25%]
    tests/test_attention_blind_spot.py .........                             [ 33%]
    tests/test_attention.py ................................................ [ 79%]
    .................                                                        [ 95%]
    tests/test_prompts_attention.py .....                                    [100%]

    ============================= 106 passed in 32.08s =============================
    ```

    `git diff --stat tests/test_attention_contract.py`:
    Output is empty (file unmodified).

    Full bare `python3 -m pytest` summary:
    Baseline: `4 failed, 4551 passed, 1 skipped, 1 warning, 208 deselected in 196.48s`
    Post-implementation: `4 failed, 4566 passed, 1 skipped, 1 warning, 208 deselected in 203.49s`
    Failing NODE-ID set UNCHANGED (the 4 pre-existing date-boundary and reachability failures in `test_spec_review_attestation.py` and `test_run_finding_reachability.py`). Passed count increased (+15).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: go-pending-approval`, written by `/plan-review` as that workflow's output rather than by its author (the authored copy correctly carried NO such field). It still requires explicit human approval before execution; `reviewed` is not approval and the executor must not self-approve it.

EXECUTION CONTRACT. Commit ONLY the two declared paths, through `aw commit <plan> -- agent_workflows/attention.py tests/test_attention.py`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything that is not yours with `git restore --staged <path>`: this is a shared checkout. Do NOT run `git gc`, `git prune`, or `git repack -d` at any point, for the reason E-01 gives. Do not commit the extracted scratch blobs. Paste ACTUAL runner output for every test claim.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and EVERY `V-*` item is verified with concrete pasted evidence. Perform the terminal transition through the tooled path (`aw ipd finalize`), never by hand-editing the status or moving the file. NOTE, because this plan exists precisely because that gate did not hold: a clean scope reconciliation is NOT evidence that the work landed (F-10 shows an all-paths-unmodified execution reconciles `ok=True`), so before finalizing, run `git show HEAD:agent_workflows/attention.py | grep -c inbox || true` and confirm it is NONZERO. If it is zero, the work did not land and finalizing would repeat the exact defect this plan remediates. NOTE THE `|| true`, added at review and not cosmetic: `grep -c` EXITS 1 when the count is zero (verified at review, where this exact command printed `0` and returned 1), so the failing-case exit status is indistinguishable from a broken command and, chained with `&&`, would skip the very report that matters. Read the printed NUMBER, never the exit status.
