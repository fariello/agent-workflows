# IPD: Guarantee a run directory's log and prompt parents exist instead of obliging every caller to precreate them

- Date: 2026-09-29
- Kind: child
- Concern: `runner_shared.attempt_log_path` and `runner_shared.write_prompt` each compute a path UNDER a run-directory subdirectory (`sessions/` and `prompts/` respectively) and their write sites then open it WITHOUT creating that parent. `oc_runipd.run_opencode` computes `log_path = attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)` and opens it as `log_path.open("w", encoding="utf-8") as log` inside the same `with` that enters `turn_telemetry`; the agy twin `agy_runipd.run_agy_turn` has the IDENTICAL shape (compute, then `log_path.open("w", encoding="utf-8") as log`, with no intervening `mkdir` anywhere between them); and `write_prompt` ends in a bare `path.write_text(prompt, encoding="utf-8")`. So the directory is an UNDOCUMENTED CALLER OBLIGATION encoded nowhere except in `runner_shared.initialize_run_core`, which happens to satisfy it with `for name in ("sessions", "outcomes", "prompts"): (run_dir / name).mkdir(parents=True, exist_ok=True)`. Any caller that builds a run directory WITHOUT that initializer dies with `FileNotFoundError` at the moment of launch. REPRODUCED at this HEAD in a throwaway tempdir: `attempt_log_path` yields `<run_dir>/sessions/01-abc123-attempt-1.jsonl` with `parent exists: False`, and the open raises `FileNotFoundError: [Errno 2] No such file or directory`; `write_prompt` raises the same on `<run_dir>/prompts/01-abc123-exec-attempt-1.md`. THE FAILURE IS LATE AND THEREFORE EXPENSIVE: by the time `run_opencode` opens the log, the prompt has already been written and, with isolation on (the default), a git worktree has already been allocated, so a caller that omits the directory LEAKS A LANE AND A PROMPT before failing. TWO FURTHER FACTS THE ITEM DOES NOT RECORD, both measured here: the obligation has already been PAID TWICE as a workaround rather than fixed once (`oc_runipd.handle_audit_command` creates all three subdirectories, and `host_sandbox_profile`'s resume-argv capability probe creates `(run_dir / "sessions").mkdir(parents=True)` in PRODUCTION code, not test code); and the item's cited reproduction `tests/test_standalone_verify.py::TheVerbRunsEndToEnd` DOES NOT EXIST at this head, so the reproduction below is newly derived rather than re-run.
- Scope: Convert the undocumented caller obligation into a GUARANTEE at the two write sites that own it, plus the one shared writer. THREE changes: (1) `runner_shared.write_prompt` creates `path.parent` before `write_text`, since it both computes and writes the path and is therefore solely responsible for it; (2) `oc_runipd.run_opencode` and (3) `agy_runipd.run_agy_turn` each create `log_path.parent` before the `open("w")`, fixing both hosts rather than one. The fix is deliberately NOT placed inside `attempt_log_path`: that helper is a PURE PATH FUNCTION with read-only and record-only callers (`runner_shared.execute_item_core` calls it merely to record `"log": str(attempt_log_path(...))` into an attempt dict, and the dashboard/viewer re-root recorded log names for READING), so creating a directory there would make a pure accessor mutate the filesystem and would create `sessions/` in run directories nobody ever launches into. DOES NOT change any filename or path shape, DOES NOT alter `initialize_run_core` (its mkdir loop stays, now as defence in depth rather than as the sole guarantee), DOES NOT remove either existing caller-side workaround, and DOES NOT touch `outcomes/`, whose writers are out of scope and separately addressed below.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_dir_parents_are_guaranteed.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: hblsqo
- Blocks-Release: next
- Set: hblsqo
- Order: 1
- Highest E allocated: 04
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: z3ifg8

## Workflow history
- 2026-10-02 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: z3ifg8 verified (set hblsqo, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261001-6bolin-01-6bolin-grandfatheringandcheckertests-fails-on-89xjll-spec.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run); out-of-scope .aw/records/backlog/open/20261001-m88gwh-01-m88gwh-danglingcommitsearchtests-test-07-real-corpus-arm-.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (opencode model=its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-601..PR-605 all fixed; fix verified end to end

- 2026-09-29 /plan-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-605 all FIXED, none deferred or open. Revisions committed here; the `- Status: reviewed` transition is applied immediately after through `aw ipd set reviewed z3ifg8`, which is why this line precedes it. Reviewed at HEAD `82aab2e9`. `aw ipd lint --phase author` conformed before review and `--phase review-finalize` conforms after. THIS IS A SMALL, CORRECT, WELL-EVIDENCED PLAN AND EVERY LOAD-BEARING CLAIM REPRODUCES. I verified the defect and the prescribed fix END TO END through the REAL `run_opencode`, not only through the helper: against a bare run directory it raised `FileNotFoundError: .../run/sessions/01-probe1-attempt-1.jsonl` with `sessions/` absent, and after applying E-02's exact one-liner the fake-launch sentinel `RuntimeError("stop-before-launch")` surfaced with `sessions/` created; the probe patch was reverted and `git diff --stat` confirmed empty. CONFIRMED: F-01 and F-04 (both reproduce with the plan's exact filenames), F-02 and F-03 (both hosts assign `log_path = attempt_log_path(...)` and open it 166 and 116 body lines later respectively with NO intervening mkdir, and in both the open is the second manager of a multi-manager `with` ending `as log,`), F-05 (no `tests/test_standalone_verify.py`, no test references `handle_audit_command`), F-06 (`execute_item_core` records the string; `run_dashboard` and `run_viewer` read), F-07 (both workarounds present, including the `handle_audit_command` comment verbatim), F-08 (`agy_run.py` does `log_directory.mkdir(parents=True, exist_ok=True)` before its open), F-09, and F-10 (`298 passed`, `3246 passed, 2 skipped`). FIVE findings raised, all fixed, none HIGH. PR-601 adds the missing proof that ONE statement suffices: scanning the whole span between assignment and open for any other filesystem write found exactly one hit, the open itself (F-13). PR-602 records that `host_sandbox_profile`'s probe is a COMPLETE WORKING TEMPLATE for E-04(d)/(e) whose only needed edit is deleting the very `sessions` mkdir this plan makes unnecessary (F-14), which review drove successfully. PR-603 corrects F-11: the grep now matches THIS PLAN itself and the pending population is 144, not 50, so a naive re-derivation would read the plan's own text as contention. PR-604 corrects E-01's call-site count (12, not 9) and reframes it as context rather than a census. PR-605 adds the missing gate elements: staged-set verification for a shared checkout, the conditional finalize ownership (the gate said only "move it through the tooled transition"), a consolidated scope fence, and an approver-facing summary. Both open questions verified genuinely non-blocking: neither changes a line this plan writes, and OQ-01 is properly FILED as backlog `3kr193`, which exists. Bare suite `3246 passed, 2 skipped`. No production file was left modified by this review.
- 2026-09-29 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `hblsqo`. Every measurement in Findings was taken in this lane worktree at HEAD `b41b66ea`, against throwaway `tempfile.mkdtemp()` directories, never against the tracked runs tree. THE ITEM'S DIAGNOSIS REPRODUCES EXACTLY and its recommended one-line fix is adopted, but THREE of its statements are CORRECTED rather than copied. (1) Its cited reproduction, `tests/test_standalone_verify.py::TheVerbRunsEndToEnd`, DOES NOT EXIST at this head (no such file; no test in `tests/` references `handle_audit_command` at all), so F-05 supplies a newly derived reproduction instead. (2) It offers the fix as "one line in `run_opencode` (or in `attempt_log_path`)"; this plan takes the FORMER and explicitly REJECTS the latter, because F-06 measured read-only and record-only callers of that pure helper. (3) It asks that "the agy twin `run_agy_turn` should be checked for the same shape" - it was, it HAS the same shape, and F-03 records it, so the fix covers both hosts. The plan also adds a defect the item does not mention: `write_prompt` has the identical bug (F-04), and the item's own "LATE failure" reasoning applies to it one step earlier.
- 2026-09-29 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `<run_dir>/sessions/` and `<run_dir>/prompts/` exist BECAUSE the code that writes into them creates them, on both hosts, so any caller that assembles a run directory without `initialize_run_core` no longer dies with `FileNotFoundError` after it has already written a prompt and allocated an isolated worktree. After this plan the requirement is a guarantee rather than an invisible obligation, the two existing caller-side workarounds become redundant belt-and-braces instead of load-bearing, and a new minimal-run-directory caller (the shape `aw oc audit` needed) works without rediscovering the obligation by crashing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make each writer create the directory it writes into

- [x] E-01 In `agent_workflows/runner_shared.py`, make `write_prompt` create its own parent directory before writing. Insert `path.parent.mkdir(parents=True, exist_ok=True)` between the `path = (run_dir / "prompts" / ...)` assignment and the existing `path.write_text(prompt, encoding="utf-8")`. Extend the docstring with one sentence stating that the function GUARANTEES `prompts/` exists rather than requiring the caller to have created it, so the next reader does not delete the mkdir as redundant after seeing `initialize_run_core` also do it.

  THIS FUNCTION IS THE CLEAREST CASE IN THE PLAN AND IS INTENTIONALLY FIRST. Unlike `attempt_log_path`, `write_prompt` both COMPUTES the path and WRITES to it in the same body, so there is no pure-accessor argument against fixing it in place and no caller that wants the path without the side effect. It has at least a dozen call sites (re-measured at review: ELEVEN inside `runner_shared` itself plus one in `oc_runipd.handle_audit_command`; authoring said "one plus eight"), and the mkdir is correct for ALL of them by construction rather than by census, because the function itself performs the write, so no caller can want the path without the side effect. Do not re-derive this count as an acceptance bar; it is context.
  - Depends on: none
  - Expected outcome: `runner_shared.write_prompt(Path(tempfile.mkdtemp()), {"position": 1, "id6": "abc123", "action": "exec"}, "hi", 1)` returns the path and the file exists, where the SAME call raises `FileNotFoundError` at this head. `python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py` stays green.
  - Execution state: performed

- [x] E-02 In `agent_workflows/oc_runipd.py`, make `run_opencode` create the session-log parent before opening it. Add `log_path.parent.mkdir(parents=True, exist_ok=True)` immediately after the existing `log_path = attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)` assignment, which is well before the `with` block containing `log_path.open("w", encoding="utf-8") as log`. Placing it at the assignment rather than adjacent to the open is deliberate: the `with` header also enters `turn_telemetry`, and a statement wedged between the context managers of a single multi-manager `with` is not expressible without restructuring that header.

  DO NOT MOVE OR RESTRUCTURE THE `with` HEADER. It composes several context managers, at least `turn_telemetry(...)` and the log open, and the telemetry manager records the turn; reordering or splitting them changes what is recorded on an exception path. CONFIRMED AT REVIEW: the open is the SECOND manager in that header, appearing as `log_path.open("w", encoding="utf-8") as log,` with a trailing comma immediately before the closing `):`, so a statement genuinely cannot be placed between the managers without restructuring. The mkdir is idempotent and cheap, so it costs the existing initializer-backed callers nothing on a directory that already exists.
  ONE STATEMENT IS PROVABLY ENOUGH FOR THE WHOLE SPAN (F-13): scanning the 166 body lines between the assignment and the open for any other filesystem write found exactly one hit, the log open itself. So no second parent needs creating in that region, and the executor should not go hunting for one.
  - Depends on: none
  - Expected outcome: `run_opencode` no longer raises `FileNotFoundError` when `<run_dir>/sessions/` is absent; a minimal run directory with no subdirectories reaches the launch attempt instead of dying before it. VERIFIED AT REVIEW by applying this exact one-liner: the outcome changed from `FileNotFoundError` on the log path to the fake-launch sentinel `RuntimeError("stop-before-launch")`, with `<run_dir>/sessions/` existing afterwards (F-12). `python3 -m pytest tests/test_oc_runipd.py` stays green.
  - Execution state: performed

- [x] E-03 In `agent_workflows/agy_runipd.py`, apply the same one-line fix to the twin `run_agy_turn`, immediately after its own `log_path = attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)` assignment. The item asked for this host to be CHECKED; it was, and it has the identical defect (F-03), so it is FIXED here rather than merely noted.

  FIX BOTH HOSTS IN THE SAME CHANGE, AND DO NOT "UNIFY" THEM WHILE HERE. Leaving agy broken would mean a later agy-side caller rediscovers the same crash, and the repository's runner-unification work has already moved the shared helper into `runner_shared`; the remaining per-host code is the launch body, which this plan is not refactoring. Add the identical statement, not a new shared wrapper around the two launch bodies.
  - Depends on: none
  - Expected outcome: the agy launch path no longer requires a precreated `sessions/`; `python3 -m pytest tests/test_agy_runipd_cli.py tests/test_runner_shared.py` stays green.
  - Execution state: performed

### Task group 2: pin the guarantee so it cannot silently regress

- [x] E-04 Add `tests/test_run_dir_parents_are_guaranteed.py` pinning the guarantee BY OUTCOME on a run directory that deliberately has NO subdirectories, driving the real functions in `tempfile` fixtures and asserting on real filesystem side effects. Cover, each as its own test: (a) `write_prompt` into a bare run directory returns a path that EXISTS and whose content round-trips, and creates `prompts/`; (b) the same call is idempotent when `prompts/` already exists and does not raise or truncate a sibling; (c) `attempt_log_path` remains PURE, i.e. calling it on a bare run directory creates NOTHING on disk (assert `not (run_dir / "sessions").exists()` afterwards), which is the pin that the fix was not put in the wrong place; (d) `oc_runipd.run_opencode` on a bare run directory gets PAST the log-open and fails (if at all) for a launch-related reason rather than `FileNotFoundError` on the log path, with `<run_dir>/sessions/` existing afterwards; (e) the agy twin likewise.

  ASSERT ON BEHAVIOR AND FILESYSTEM STATE, NEVER ON SOURCE TEXT. Do NOT use `inspect`, `ast`, regex, or substring search over the production modules to check that a `mkdir` call is present, and do NOT count call sites: those are code-pinning tests, which this repository forbids (GUIDING_PRINCIPLES P16), and they would pass even if the mkdir were unreachable. Test (c) is the single most important item here, because it is the only guard against a future "simplification" that moves the mkdir into `attempt_log_path` and reintroduces the pure-accessor violation F-06 describes.
  FOR (d) AND (e), COPY `host_sandbox_profile`'s PROBE BLOCK AND DELETE ITS MKDIR LINE. That block is a COMPLETE WORKING TEMPLATE, not merely a stylistic precedent (F-14), and review drove it successfully against both the broken and the fixed code (F-12). Its ingredients, all load-bearing: a real `git init -b main` in a tempdir (the isolation path needs a repository); `options={"opencode": "/bin/false", "agy_executable": "/bin/false"}` so no real binary is resolved; a `fake_popen` that PASSES `git` and `sys.executable` THROUGH to the real `subprocess.Popen` and raises `RuntimeError("stop-before-launch")` otherwise; restoring `subprocess.Popen` in a `finally`; and an `item` of `{"id6","setid","position","action"}`. THE ONE EDIT IS TO REMOVE ITS `(run_dir / "sessions").mkdir(parents=True)` LINE, which is exactly the workaround this plan makes unnecessary, so the test's own diff from the template evidences the fix. Assert that the surfaced outcome is the sentinel (or any non-`FileNotFoundError`) AND that `<run_dir>/sessions/` exists afterwards. Do NOT assert the sentinel is the ONLY acceptable outcome: a later launch-path change could legitimately fail earlier for an unrelated reason, and the property under test is the absence of `FileNotFoundError` on the log path.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the new module passes; each of its launch-path tests demonstrably FAILS against the unpatched code (verify by reverting the one-line change locally, observing the failure, and restoring it), which is what proves the test exercises the fix rather than passing vacuously. Review pre-verified this asymmetry for the oc side (`FileNotFoundError` before, sentinel after), so a test that passes in BOTH states is wrong and must be fixed rather than accepted.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE RUN-DIRECTORY SKELETON IS CREATED IN EXACTLY ONE PLACE, and that is why the obligation is invisible. `runner_shared.initialize_run_core` does `for name in ("sessions", "outcomes", "prompts"): (run_dir / name).mkdir(parents=True, exist_ok=True)` right after minting `run_dir = state_root(repo) / run_id`. Nothing else in the package creates the skeleton, so every pre-existing launch path is reachable only through that initializer and the requirement never fires. This plan does NOT remove that loop: after the fix it is harmless defence in depth, and deleting it would make `outcomes/` (whose writers are out of scope here) newly unguaranteed.
- THE HOUSE PATTERN FOR A WRITER IS ALREADY "CREATE YOUR OWN PARENT", which makes this fix a convention rather than an invention. `agy_run.run_agy_turn`'s own logging does exactly that: `log_directory = root / "tmp" / "antigravity"` followed immediately by `log_directory.mkdir(parents=True, exist_ok=True)` and only then the `log_path.open("w", ...)`. So one of the two files in scope already contains the correct pattern a few hundred lines from the defective one; the fix makes the runner paths consistent with it.
- `attempt_log_path` IS A PURE PATH HELPER WITH NON-WRITING CALLERS, which is the whole reason the fix goes at the write sites. `runner_shared.execute_item_core` calls it only to RECORD a string into an attempt dict (`"log": str(attempt_log_path(run_dir, item, attempt_no))`), and `run_dashboard` / `run_viewer` re-root recorded log names for READING (`candidate = run_dir / "sessions" / name` guarded by `candidate.is_file()`). A mkdir inside the helper would therefore create `sessions/` as a side effect of merely NAMING a log, including in directories no turn ever launches into.
- THE SHARED HELPERS ARE SHARED DELIBERATELY AND MUST NOT BE RE-FORKED. `attempt_log_path` and `write_prompt` are defined ONCE in `runner_shared` and imported by both hosts under an explicit re-export (`attempt_log_path as attempt_log_path`), with both runners carrying the comment "`attempt_log_path` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`)". Their docstrings record that unifying them REPAIRED a live analytics defect, because `run_analytics_statistics._VERIFY_LOG_RE` is anchored `-attempt-\d+-verify\.jsonl$` and only oc's filename shape satisfies it. So this plan must not change either filename shape, and must not reintroduce a host-local definition.
- TESTS MUST EXERCISE BEHAVIOR, NOT SOURCE STRUCTURE (GUIDING_PRINCIPLES P16, restated in `AGENTS.md`): no `inspect`/`ast`/regex over production source, no caller-count or symbol-census assertions. E-04 is written to that bar, which is why it asserts on filesystem state and raised exception types rather than on the presence of a `mkdir` call.
- THE EXISTING PRECEDENT FOR TESTING A LAUNCH PATH WITHOUT LAUNCHING is `host_sandbox_profile`'s resume-argv probe: it swaps in a `fake_popen` that passes `git`, `sys.executable` and `bwrap` through to the real `subprocess.Popen` and otherwise captures argv and raises `RuntimeError("stop-before-launch")`. E-04 reuses that shape rather than inventing a second one.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S DIAGNOSIS REPRODUCES EXACTLY. `attempt_log_path` returns a path two levels down whose parent does not exist, and opening it for write raises. | Driven at HEAD `b41b66ea` in a `tempfile.mkdtemp()` directory: `computed: /tmp/tmp3gstluj1/sessions/01-abc123-attempt-1.jsonl`, `parent exists: False`, `REPRODUCED FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmp3gstluj1/sessions/01-abc123-attempt-1.jsonl'`. |
| F-02 | THE DEFECT IS A MISSING STATEMENT BETWEEN TWO EXISTING ONES, confirming the fix is one line and not a redesign. `oc_runipd.run_opencode` assigns `log_path = attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)` and later opens `log_path.open("w", encoding="utf-8") as log` inside a multi-manager `with` that also enters `turn_telemetry(...)`; no `mkdir` occurs anywhere between them. | Both statements read in `agent_workflows/oc_runipd.py`, function `run_opencode`. A scan of the whole span between the assignment and the open found no `mkdir`. |
| F-03 | THE AGY TWIN HAS THE IDENTICAL SHAPE, so the item's "should be checked" is answered YES and the fix must cover both hosts. `agy_runipd.run_agy_turn` assigns the same `attempt_log_path(...)` call and later opens `log_path.open("w", encoding="utf-8") as log`, with no intervening `mkdir`. | Read in `agent_workflows/agy_runipd.py`, function `run_agy_turn`; an explicit scan of the entire span between its assignment and its open reported `NO MKDIR between compute and open in agy_runipd.run_agy_turn`. |
| F-04 | A SECOND, UNRECORDED INSTANCE OF THE SAME DEFECT CLASS EXISTS IN `write_prompt`, and it fires one step EARLIER in the same turn. The function ends `path.write_text(prompt, encoding="utf-8")` with no parent creation. | Same fixture: `write_prompt ALSO REPRODUCES: [Errno 2] No such file or directory: '/tmp/tmp8wdgb0v4/prompts/01-abc123-exec-attempt-1.md'`. Since `oc_runipd.handle_audit_command` calls `runner_shared.write_prompt(...)` BEFORE `run_opencode`, a caller missing both directories actually fails here first, which is why the item's crash was at the log only after its own fix had created `prompts/`. |
| F-05 | THE ITEM'S CITED REPRODUCTION DOES NOT EXIST AT THIS HEAD, so it is replaced rather than re-run. There is no `tests/test_standalone_verify.py`, and no test in `tests/` references `handle_audit_command`, `plan_audit_target`, `_fresh_audit_run_dir`, or a `TheVerbRunsEndToEnd` class. | `ls tests/test_standalone_verify.py` reports `No such file or directory`; `grep -rn "handle_audit\|audit_command\|cmd_audit" tests/*.py` and `grep -rln "plan_audit_target\|_fresh_audit_run_dir" tests/` both return no matches. F-01 and F-04 are the substituted reproductions. |
| F-06 | THE FIX MUST NOT GO IN `attempt_log_path`, because that helper has callers that never write. `runner_shared.execute_item_core` uses it only to record `"log": str(attempt_log_path(run_dir, item, attempt_no))` into an attempt dict; `run_dashboard` re-roots a recorded name with `candidate = run_dir / "sessions" / name` under an `is_file()` guard, and `run_viewer` scans `run_dir / "sessions"` as a fallback. A mkdir inside the helper would create directories as a side effect of naming and reading. | Call sites read in `agent_workflows/runner_shared.py` (`execute_item_core`'s attempt dict), `agent_workflows/run_dashboard.py`, and `agent_workflows/run_viewer.py`. |
| F-07 | THE OBLIGATION HAS ALREADY BEEN PAID TWICE AS A WORKAROUND, INCLUDING IN PRODUCTION CODE, which is the strongest available evidence that it belongs in the callee. `oc_runipd.handle_audit_command` creates all three (`for sub in ("outcomes", "prompts", "sessions"): (run_dir / sub).mkdir(parents=True, exist_ok=True)`) and carries a comment explaining that `sessions/` "is not optional decoration" because `run_opencode` "does NOT create its parent"; and `host_sandbox_profile`'s resume-argv capability probe does `(run_dir / "sessions").mkdir(parents=True)`. The second is a shipped capability probe, not a test. | Both read in `agent_workflows/oc_runipd.py` and `agent_workflows/host_sandbox_profile.py`. |
| F-08 | THE HOUSE PATTERN IS ALREADY PRESENT IN A FILE IN SCOPE, so the fix restores consistency rather than introducing a style. `agy_run.run_agy_turn` does `log_directory.mkdir(parents=True, exist_ok=True)` immediately before opening its own stream log. | Read in `agent_workflows/agy_run.py`. |
| F-09 | THE FILENAME SHAPES ARE LOAD-BEARING FOR ANALYTICS AND MUST NOT CHANGE. `attempt_log_path`'s docstring records that adopting oc's `-attempt-<n>-verify.jsonl` order REPAIRED a live defect, because `run_analytics_statistics._VERIFY_LOG_RE` is anchored `-attempt-\d+-verify\.jsonl$` and a verifier session log is the sole signal of the verifier phase. This constrains the fix to adding a mkdir and nothing else. | Docstrings of `runner_shared.attempt_log_path` and `runner_shared.write_prompt`; regex comment in `agent_workflows/run_analytics_statistics.py`. |
| F-10 | THE SURFACE IS GREEN NOW, so any post-change failure is attributable to this plan. BOTH BASELINES RE-CONFIRMED AT REVIEW HEAD `82aab2e9`, unchanged. RE-DERIVE them at execution rather than comparing to these figures: the totals are live and the collected count rises by whatever E-04 adds, so compare failure sets by NODE ID. | authoring at HEAD `b41b66ea`: `298 passed in 15.11s` and `3246 passed, 2 skipped, 3 warnings in 54.90s`. Review at HEAD `82aab2e9`: `298 passed in 65.56s` (same count, slower machine) and `3246 passed, 2 skipped, 3 warnings in 49.50s`. |
| F-11 | NO PENDING PLAN CONTENDS FOR THESE SYMBOLS, so this plan can execute independently. RE-MEASURED AT REVIEW AND STILL TRUE, with two corrections to the evidence: the pending population is 144 plans, not 50, and the grep now returns exactly ONE match, THIS PLAN ITSELF (which names both symbols throughout). A re-derivation at execution must therefore exclude the plan's own file, or it will read its own text as contention. | `grep -l "attempt_log_path\|write_prompt" .aw/records/plans/pending/*.ipd.md` returns only `20260929-hblsqo-01-z3ifg8-...ipd.md`; `ls .aw/records/plans/pending/*.ipd.md \| wc -l` = 144 |
| F-12 | **REVIEW FINDING: THE DEFECT AND THE PRESCRIBED FIX WERE BOTH VERIFIED END TO END THROUGH THE REAL `run_opencode`, not only through the helper.** Using exactly the fake-`Popen` shape E-04(d) prescribes (pass `git` and `sys.executable` through, raise `RuntimeError("stop-before-launch")` otherwise) against a BARE run directory: BEFORE, `run_opencode` raised `FileNotFoundError: ... /run/sessions/01-probe1-attempt-1.jsonl` and `sessions/` did not exist afterwards. AFTER applying E-02's prescribed one-liner verbatim, the sentinel `RuntimeError("stop-before-launch")` surfaced instead and `sessions/` existed. So E-02 is verified SUFFICIENT, not merely plausible, and E-04(d) is verified FEASIBLE as specified. The probe patch was reverted immediately and `git diff --stat` confirmed empty. | review transcript: `RESULT: FileNotFoundError -> <TMP>/run/sessions/01-probe1-attempt-1.jsonl`, `sessions/ exists after: False`; then `AFTER FIX: RuntimeError -> stop-before-launch`, `AFTER FIX sessions/ exists: True` |
| F-13 | **REVIEW FINDING: THE LOG OPEN IS THE ONLY WRITE IN THE SPAN, which is the missing proof that E-02's single statement suffices.** The plan shows no `mkdir` occurs between the assignment and the open, but not that no OTHER unguarded write occurs there. Scanning the whole span for `write_text(`, `.open(`, `mkdir(`, `write_prompt(` and `touch(` found exactly one hit: the `log_path.open("w", ...)` itself. So nothing else in that region needs a parent, and one mkdir closes the whole span. | AST-free scan over `run_opencode`'s body from the `log_path = attempt_log_path(...)` assignment (body index 277) to the open (index 442): a single match, the open |
| F-14 | **REVIEW FINDING: `host_sandbox_profile`'s capability probe is not merely a precedent for E-04's technique, it is a COMPLETE WORKING TEMPLATE that already contains the workaround F-07 cites.** Its body does `run_dir = root / "run"` then `(run_dir / "sessions").mkdir(parents=True)` then builds a `state`/`item` pair and calls `invoker(state, run_dir, item, plan, prompt, sentinel)` under a swapped `subprocess.Popen`. So E-04(d)/(e) can be written by copying that block and DELETING its mkdir line, which is both the minimal-diff route and a self-evidencing one: the line removed is the workaround the plan exists to make unnecessary. | read in `agent_workflows/host_sandbox_profile.py`, the `fake_popen` probe: `captured["argv"] = cmd` / `raise RuntimeError("stop-before-launch")`, `(run_dir / "sessions").mkdir(parents=True)`, `options={"opencode": "/bin/false", "agy_executable": "/bin/false"}` |

## Proposed changes (ordered, validatable)

1. E-01: `runner_shared.write_prompt` creates `path.parent` before `write_text` (F-04, the clearest case since it both computes and writes).
2. E-02: `oc_runipd.run_opencode` creates `log_path.parent` at the assignment, not inside the multi-manager `with` (F-01, F-02).
3. E-03: `agy_runipd.run_agy_turn` gets the identical statement, so both hosts are fixed (F-03).
4. E-04: a new test module pins the guarantee by outcome, including the negative pin that `attempt_log_path` stays pure (F-06).

## Deferred / out of scope (with reason)

- `outcomes/` IS NOT GUARANTEED BY THIS PLAN, and that is a deliberate boundary rather than an oversight. Its writers are spread across `runner_shared.read_recorded_outcome`'s path helper, `lane_containment` (three separate `run_dir / "outcomes" / ...` constructions), and `oc_runipd.handle_audit_command`'s `verdict_path`; several of those paths are written by the AGENT inside a lane rather than by the driver, so the correct owner of the mkdir differs per site and needs its own analysis. The item names only the log path, and `initialize_run_core` still creates `outcomes/` for every queued run. Raised as OQ-01.
  - Carrier: 3kr193
- THE TWO EXISTING CALLER-SIDE WORKAROUNDS ARE LEFT IN PLACE (`handle_audit_command`'s three-directory loop and `host_sandbox_profile`'s `sessions` mkdir). Both become redundant, both are idempotent, and removing them is a cleanup whose only benefit is line count while its risk is unguarding `outcomes/` in the audit path. Their comments will be slightly stale in claiming the callee does not create the parent; correcting that prose is folded into no E-item deliberately, since editing `handle_audit_command`'s comment without changing its behavior adds a file to `Scope-Paths` for no testable outcome.
  - Carrier-Declined: Nothing is owed, because leaving redundant idempotent code in place is this plan's RECOMMENDED end state (OQ-02), not deferred work. Both calls are `mkdir(..., exist_ok=True)` on directories the callee will now create anyway, so they cost nothing at runtime and removing them would buy only line count while risking the audit verb's `outcomes/` guarantee while OQ-01 is open. The only genuine residue is two slightly stale explanatory comments, which is a prose inaccuracy in internal comments rather than a defect: filing an item to reword a comment would misrepresent a deliberate belt-and-braces choice as debt. If the maintainer later decides the cleanup is wanted, it is one commit and it should follow the `outcomes/` decision carried by `3kr193`, not precede it.
- NO CHANGE TO `initialize_run_core`. Its mkdir loop stays as defence in depth and as the sole remaining guarantee for `outcomes/`.
  - Carrier-Declined: This row records a DELIBERATE NON-CHANGE, so nothing is owed. The loop is not a defect: after this plan it is harmless duplication for `sessions/` and `prompts/`, and it remains the ONLY guarantee for `outcomes/`, so deleting it would newly break the very class of caller this plan exists to protect. Whether it still earns its place once `outcomes/` is settled is explicitly part of the question carried by backlog item `3kr193`, so the future decision has an owner without this row claiming separate work.
- NO FILENAME OR PATH-SHAPE CHANGE, and no re-forking of the shared helpers into per-host definitions (F-09).
  - Carrier-Declined: This row records a PROHIBITION on this plan rather than deferred work, so nothing is owed. F-09 measures that the filename shapes are load-bearing for `run_analytics_statistics._VERIFY_LOG_RE` and that unifying the two hosts' definitions REPAIRED a live defect, so preserving them is a constraint to be honored here and not a task to hand on. It is enforced inside this plan by the negative fence and by V-02's requirement that the surrounding region be otherwise unchanged.
- NO REFACTOR OF EITHER LAUNCH BODY. The two hosts' `run_opencode` / `run_agy_turn` bodies remain separate; unifying them is the runner-unification programme's concern, not this bug's.
  - Carrier-Declined: No future work is owed BY THIS PLAN, and filing an item would duplicate an existing programme. Runner unification is an established, ongoing effort in this repository with its own plans and its own Set history (the shared helpers this plan touches were moved into `runner_shared` by rununify 03 `i3d6ml`, whose comments both runners still carry), so the remaining per-host launch bodies are already that programme's scope. Adding a carrier item here would file a duplicate of work already owned elsewhere, which is worse than declining.

## Scope check

- Over-scope: none. Every file in `Scope-Paths` is touched by a named E-item: `runner_shared.py` (E-01), `oc_runipd.py` (E-02), `agy_runipd.py` (E-03), and the new `tests/test_run_dir_parents_are_guaranteed.py` (E-04). No documentation file is edited, because nothing user-facing changes.
- Under-scope: the plan does NOT guarantee `outcomes/` (deferred above, OQ-01), does NOT remove the two now-redundant caller-side workarounds, and does NOT correct the slightly stale comment in `handle_audit_command` that asserts the callee does not create the parent.
- Negative fence, stated because the tempting shortcut is to fix one place instead of three: the executor MUST NOT put the mkdir inside `attempt_log_path` (F-06 explains why, and E-04(c) tests against it), MUST NOT fix only the oc host and leave agy (F-03), MUST NOT alter either filename shape (F-09), MUST NOT restructure the multi-manager `with` header in `run_opencode` (E-02), and MUST NOT satisfy E-04 with tests that read production source text.

## Required tests / validation

- `python3 -m pytest tests/test_run_dir_parents_are_guaranteed.py` (new, E-04) passes.
- `python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` passes, with no edits to those modules.
- `python3 -m pytest` run BARE (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`; do NOT add `-n0`, a second `-q`, or `-p no:randomly`) reports zero failures and no fewer passing tests than the F-10 baseline of 3246 plus the new module's count. Paste the actual `N passed` line.
- A NEGATIVE CONTROL, which is what distinguishes a real pin from a vacuous one: revert each one-line mkdir locally, show the corresponding new test FAILING with `FileNotFoundError`, restore the line, and show it passing. Paste both outcomes. Review already performed this for the oc site and recorded the asymmetry in F-12 (`FileNotFoundError` before, `RuntimeError("stop-before-launch")` after, `sessions/` absent then present), so the executor knows the expected shape of both halves; a test that passes in BOTH states is vacuous and must be fixed, not accepted. AFTER EACH REVERT, RESTORE THE FILE AND CONFIRM WITH `git diff --stat` THAT NOTHING REMAINS MODIFIED before moving on, since a forgotten revert would commit the defect back.
- `aw sanitize --agent` reports no new findings (the new test module must use `tempfile` paths, never a machine-absolute path written into the file).

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and this is a positive finding rather than an omission. No `.spec.md` in the repository specifies the run-directory layout or which component creates its subdirectories; the layout is documented in the operator runbook prose (`tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md` Section 3 lists `sessions/`, `outcomes/`, `prompts/` as contents of the state directory) and is otherwise encoded only in `initialize_run_core`. Accordingly no `.spec.md` path appears in `Scope-Paths`, so both runners' spec-edit announcement will correctly report zero declared spec edits.
- NO USER-FACING DOCUMENTATION CHANGES, because nothing a user can observe changes: the same directories exist with the same names in the same place, merely created by a different statement. The runbook's Section 3 listing stays accurate.
- THE ONLY PROSE UPDATED IS AN INTERNAL DOCSTRING (E-01's sentence stating that `write_prompt` guarantees its parent), which exists to stop a future reader deleting the mkdir as duplicative of `initialize_run_core`.

## Open questions

### OQ-01: Should `outcomes/` receive the same guarantee, and who owns the mkdir for agent-written verdicts?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, and the plan is correct either way. The item names only the session log, and `initialize_run_core` still creates `outcomes/` for every queued run, so nothing regresses by leaving it. It is a genuinely harder question than the two fixed here: `runner_shared` computes an outcome path (`run_dir / "outcomes" / f"{int(position):02d}-{id6}.json"`) for READING, `lane_containment` constructs three more for lane plumbing, and `oc_runipd.handle_audit_command`'s `verdict_path` is written by the AGENT inside a lane rather than by the driver, so "the writer creates its own parent" does not resolve to a single site the way it does for `write_prompt`. FILED AT AUTHORING TIME rather than left as a recommendation: backlog item `3kr193` carries the decision, including the follow-on question of whether `initialize_run_core`'s mkdir loop still earns its place once `outcomes/` is settled.
- Carrier: 3kr193

### OQ-02: Should the two now-redundant caller-side workarounds be removed once the guarantee lands?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED with a recommendation of "leave them". After this plan both are idempotent no-ops on directories the callee will create anyway, so they cost nothing at runtime. Removing `handle_audit_command`'s loop would additionally unguard `outcomes/` for the audit verb while OQ-01 is open, which would trade this bug for a narrower version of itself. Their explanatory comments become slightly stale (they assert the callee does not create the parent), which is the only real cost and is a prose fix rather than a behavioral one.
- Carrier-Declined: The recommendation IS "no change", so no future work is owed and filing an item would record a settled preference as an outstanding task. Should the maintainer overrule the recommendation, the cleanup belongs after the `outcomes/` decision carried by backlog item `3kr193`, since removing `handle_audit_command`'s loop before that decision would unguard `outcomes/` for the audit verb. Recorded here so a reviewer does not read the silence as a claim that the two workarounds were overlooked.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a transcript that calls `runner_shared.write_prompt` on a FRESH `tempfile.mkdtemp()` directory containing no subdirectories, showing (a) the returned path, (b) that the file exists and its content round-trips, and (c) that `<run_dir>/prompts/` now exists. Then paste the SAME call run against the reverted code showing `FileNotFoundError`, which is the negative control proving the change is what fixed it. Finally paste the `N passed` line from `python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py` showing no existing caller needed an edit.
  - Observed evidence: verified write_prompt creates prompts/ and content round-trips; negative control fails with FileNotFoundError; existing suite green (313 passed in 25.10s).
    (1) Fresh bare tempfile run_dir with fix applied:
    ```
    >>> temp_dir = pathlib.Path(tempfile.mkdtemp())
    >>> item = {"position": 1, "id6": "abc123", "action": "exec"}
    >>> returned_path = runner_shared.write_prompt(temp_dir, item, "hi", 1)
    >>> print(f"returned_path: {returned_path}")
    returned_path: /tmp/tmpn1kqde56/prompts/01-abc123-exec-attempt-1.md
    >>> print(f"file exists: {returned_path.exists()}")
    file exists: True
    >>> print(f"content: {returned_path.read_text(encoding='utf-8')}")
    content: hi
    >>> print(f"prompts/ exists: {(temp_dir / 'prompts').exists()}")
    prompts/ exists: True
    ```
    (2) Negative control pre-fix / reverted code:
    ```
    NEGATIVE CONTROL PRE-FIX: FileNotFoundError raised: [Errno 2] No such file or directory: '/tmp/tmpe5enhy3g/prompts/01-abc123-exec-attempt-1.md'
    ```
    (3) Existing caller suite green:
    ```
    313 passed in 25.10s
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste evidence that `oc_runipd.run_opencode` on a run directory with NO `sessions/` no longer dies on the log open. Acceptable form: the E-04(d) test output, plus a transcript showing the exception that surfaces is the patched-launch sentinel (or any non-`FileNotFoundError` outcome) rather than `FileNotFoundError` on the log path, AND that `<run_dir>/sessions/` exists afterwards. Also quote the resulting source region to show the mkdir sits at the `log_path = attempt_log_path(...)` assignment and that the multi-manager `with` header entering `turn_telemetry` alongside `log_path.open("w", ...)` is UNCHANGED (a diff of that header showing zero lines changed is sufficient).
  - Observed evidence: run_opencode reaches launch and creates sessions/ on a bare run directory; negative control raises FileNotFoundError; with header unchanged.
    (1) E-04(d) test output:
    `tests/test_run_dir_parents_are_guaranteed.py::RunDirParentsGuaranteedByWritersTests::test_oc_run_opencode_guarantees_sessions_dir PASSED`
    (2) Transcript showing launch sentinel rather than FileNotFoundError and sessions/ existing:
    ```
    OC POST-FIX exception: RuntimeError: stop-before-launch
    sessions/ exists: True
    ```
    Negative control (reverted mkdir):
    ```
    AssertionError: FileNotFoundError(2, 'No such file or directory') is an instance of <class 'FileNotFoundError'> : run_opencode raised FileNotFoundError on missing sessions parent: [Errno 2] No such file or directory: '/tmp/tmplcuoljyy/run/sessions/01-probe1-attempt-1.jsonl'
    ```
    (3) Source region in `agent_workflows/oc_runipd.py`:
    ```python
        verbosity = int(options.get("verbosity") or 0)
        pal = Palette(should_color(sys.stdout))
        log_path = attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    ```
    The multi-manager `with` header entering `turn_telemetry` and `log_path.open("w", ...)` is unchanged:
    ```python
        with (
            turn_telemetry(
                run_dir,
                telemetry_identity,
                repo=state.get("repo"),
                extra_context={"model": options.get(model_key)},
            ),
            log_path.open("w", encoding="utf-8") as log,
        ):
    ```
    `git diff agent_workflows/oc_runipd.py` confirms only `log_path.parent.mkdir(parents=True, exist_ok=True)` was added.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the agy-side equivalent of V-02: the E-04(e) test output showing `run_agy_turn` reaching the launch attempt on a bare run directory with `sessions/` created afterwards, plus the `N passed` line from `python3 -m pytest tests/test_agy_runipd_cli.py tests/test_runner_shared.py`. State explicitly that BOTH hosts now carry the fix, since fixing only one is the named failure mode in the negative fence.
  - Observed evidence: run_agy_turn reaches launch and creates sessions/ on a bare run directory; negative control raises FileNotFoundError; both hosts fixed; suite green (191 passed in 10.96s).
    (1) E-04(e) test output:
    `tests/test_run_dir_parents_are_guaranteed.py::RunDirParentsGuaranteedByWritersTests::test_agy_run_agy_turn_guarantees_sessions_dir PASSED`
    (2) Transcript showing launch sentinel rather than FileNotFoundError and sessions/ existing:
    ```
    AGY POST-FIX exception: RuntimeError: stop-before-launch
    sessions/ exists: True
    ```
    Negative control (reverted mkdir):
    ```
    AssertionError: FileNotFoundError(2, 'No such file or directory') is an instance of <class 'FileNotFoundError'> : run_agy_turn raised FileNotFoundError on missing sessions parent: [Errno 2] No such file or directory: '/tmp/tmpk3o15bf6/run/sessions/01-probe1-attempt-1.jsonl'
    ```
    (3) Host test suite green:
    ```
    191 passed in 10.96s
    ```
    BOTH hosts (`oc_runipd.py` and `agy_runipd.py`) now carry the identical `log_path.parent.mkdir(parents=True, exist_ok=True)` fix immediately after `log_path = attempt_log_path(...)`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the full `python3 -m pytest tests/test_run_dir_parents_are_guaranteed.py` output including the `N passed` line and the count of tests, and paste the BARE `python3 -m pytest` summary line showing zero failures and a total no lower than the F-10 baseline of `3246 passed, 2 skipped` plus the new module's count. Separately paste the (c) purity result: the assertion that `attempt_log_path` created NOTHING, i.e. `(run_dir / "sessions").exists()` is False after calling it. Confirm by quoting the new module that it contains NO `import inspect`, NO `import ast`, and no regex or substring search over `agent_workflows/` source, and that its launch-path tests patch `subprocess.Popen` rather than executing an agent binary. Finally paste `aw sanitize --agent` showing no new findings.
  - Observed evidence: 5 passed in tests/test_run_dir_parents_are_guaranteed.py; bare suite 4441 passed; attempt_log_path purity verified; no AST/inspect; sanitizer clean.
    (1) Full pytest output for `tests/test_run_dir_parents_are_guaranteed.py`:
    ```
    .....                                                                    [100%]
    5 passed in 9.36s
    ```
    (2) Bare pytest summary line (4441 passed exceeds baseline of 3246):
    ```
    4441 passed, 2 skipped, 3 warnings in 267.81s (0:04:27)
    ```
    (3) Purity result for `attempt_log_path`:
    ```
    >>> log_path = runner_shared.attempt_log_path(run_dir, item, 1)
    >>> print(f"log_path: {log_path.name}, sessions/ exists: {(run_dir / 'sessions').exists()}")
    log_path: 01-probe1-attempt-1.jsonl, sessions/ exists: False
    ```
    (4) Structural independence confirmation:
    `tests/test_run_dir_parents_are_guaranteed.py` contains NO `import inspect`, NO `import ast`, and no regex/substring search over `agent_workflows/`. Both `test_oc_run_opencode_guarantees_sessions_dir` and `test_agy_run_agy_turn_guarantees_sessions_dir` patch `subprocess.Popen = fake_popen` within a try/finally block rather than executing an agent binary.
    (5) Sanitizer output:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed`: `/plan-review` ran on 2026-09-29 and its revisions are applied. `reviewed` is NOT approval; explicit human sign-off (`- Status: approved`) is still required before execution.

This plan is a four-item, three-line behavioral fix plus one test module, and it is cohesive because all three production edits are the SAME defect in the SAME turn's file-writing path: a writer that computes a path under a run-directory subdirectory and opens it without creating the parent. Splitting them would produce three near-identical one-line plans whose main risk is that only some land, which is exactly the half-fixed state F-03 warns about (the item itself asked for the agy twin to be checked precisely so it would not be forgotten).

WHAT THE HUMAN WOULD BE APPROVING, in one paragraph. Three identical one-line additions of `mkdir(parents=True, exist_ok=True)`, one each in `runner_shared.write_prompt`, `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn`, plus one new test module and one docstring sentence. No filename changes, no path-shape changes, no signature changes, no restructuring, and no existing test edited. THE DEFECT IS REAL AND WAS VERIFIED END TO END AT REVIEW, not merely in the helper: with a bare run directory, the real `run_opencode` raises `FileNotFoundError` on `<run_dir>/sessions/<NN>-<id6>-attempt-1.jsonl`, and after applying this plan's exact prescribed one-liner the fake-launch sentinel surfaces instead with `sessions/` created (F-12). `write_prompt` reproduces the same defect one step earlier in the same turn (F-04). The failure is LATE and therefore expensive: by the time the log opens, a prompt has been written and, with isolation on by default, a git worktree has been allocated, so a caller that omits the directory leaks a lane and a prompt before failing. The strongest evidence that this belongs in the callee is that the obligation has already been PAID TWICE as a workaround in shipped code, once in `oc_runipd.handle_audit_command` (whose comment explicitly says `run_opencode` "does NOT create its parent") and once in `host_sandbox_profile`'s capability probe (F-07).

WHAT A REVIEWER SHOULD SCRUTINIZE. FIRST, the deliberate placement: the fix goes at the two WRITE sites and NOT in `attempt_log_path`, because that helper has record-only and read-only callers (`execute_item_core` records its string; the dashboard and viewer re-root recorded names for reading), so a mkdir there would make a pure accessor create directories as a side effect of NAMING a log. E-04(c) pins that as a negative test, and it is the item a future simplification would delete. If you disagree with that placement, it is the one design choice here. SECOND, blast radius is essentially zero: all current callers reach this code through `initialize_run_core`, which already created the directories, so three idempotent mkdirs are unobservable to them; the gate says explicitly that any existing test starting to fail must be diagnosed rather than edited. THIRD, both open questions are non-blocking and neither changes a line this plan writes; `outcomes/` is deliberately excluded and is carried by backlog `3kr193`.

EXECUTION CONTRACT. Commit only the files named in `Scope-Paths`, through `aw commit <plan> -- <paths>`, never `git add -A` or `git commit -a`, and do not push. Verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`: this checkout may be shared with other agents, and another party's uncommitted work must never be swept in, reverted, or cleaned up. Run the suite BARE as `python3 -m pytest` and paste the ACTUAL summary line; do not claim a pass that was not run. Measure every exit code UNPIPED. Build every fixture under `tempfile` (never the tracked runs tree), which the authoring measurements already did. This plan touches no user-facing prose, so the em/en dash rule has no surface here beyond the internal docstring sentence in E-01.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Exactly the four paths in `Scope-Paths` plus this plan. The `## Scope check` section's negative fence states the five prohibitions and they are the load-bearing ones; restated here so they sit with the contract: do NOT put the mkdir inside `attempt_log_path` (F-06; E-04(c) tests against it), do NOT fix only the oc host (F-03), do NOT alter either filename shape (F-09), do NOT restructure `run_opencode`'s multi-manager `with` header (E-02), and do NOT satisfy E-04 with tests that read production source text (P16). ADDITIONALLY: do NOT edit `initialize_run_core`'s mkdir loop (it remains the only guarantee for `outcomes/`), do NOT remove either caller-side workaround in `oc_runipd.handle_audit_command` or `host_sandbox_profile` (OQ-02 recommends leaving them and OQ-01 is open), do NOT guarantee `outcomes/` here (carried by `3kr193`), and do NOT edit any existing test module. An out-of-scope edit that turns out to be necessary is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, and a declared path you end up not modifying needs a `--scope-ack`; neither is a reason to stop.

WHAT WOULD MAKE THIS PLAN WRONG TO EXECUTE, stated so the executor can stop rather than improvise: if the negative control in V-01 does NOT fail on reverted code, the tests are vacuous and the plan must be revised rather than marked done; and if any existing test begins failing, the cause must be diagnosed rather than the test edited, since three idempotent `mkdir(parents=True, exist_ok=True)` calls should not be observable to any current caller (all of which reach the code through `initialize_run_core`, which has already created the directories).

POST-GATE LIFECYCLE MOVE. After every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, the terminal transition is owed unconditionally but its OWNER is conditional: under `aw oc run` / `aw agy run` the RUNNER performs finalize and the executor must NOT also run it (`aw ipd begin`/`finalize` refuse an agent in a managed lane with `AW-LIFECYCLE-ROLE-001`); executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` itself. Never hand-roll the move with `git mv` to `executed/` and never hand-edit `- Status: executed`. Backlog item `hblsqo` is ALREADY `graduated` (confirmed at review, and it carries `- Blocks-Release: next` and `- Work-Kind: bug`); do not set it `done` from this plan, do not clear its release gate, and do not modify the item's requirements. This plan inherits `- Blocks-Release: next` from it, which is correct under the every-live-bug-gates-the-next-release policy and must not be dropped.

THE TWO OPEN QUESTIONS DO NOT BLOCK EXECUTION, and a reviewer should know why each is safe to leave open. OQ-01 asks whether `outcomes/` deserves the same guarantee and who owns the mkdir for agent-written verdicts; it is genuinely harder (its writers span `runner_shared`, `lane_containment` three times, and a path the AGENT writes inside a lane), it is FILED as backlog `3kr193` rather than left as prose, and nothing regresses by leaving it because `initialize_run_core` still creates `outcomes/` for every queued run. OQ-02 asks whether the two now-redundant caller-side workarounds should be removed; its recommendation is "leave them", both are idempotent `exist_ok=True` calls, and removing `handle_audit_command`'s loop before OQ-01 is settled would newly unguard `outcomes/` for the audit verb. Neither question changes a line this plan writes.
