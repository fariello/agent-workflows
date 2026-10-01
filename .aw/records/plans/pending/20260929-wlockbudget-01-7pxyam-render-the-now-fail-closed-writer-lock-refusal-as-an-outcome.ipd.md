# IPD: Render the now-fail-closed writer lock refusal as an outcome instead of a traceback, and correct the three stale budget claims

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `bqz8kn` asks for two things: raise `commit_lock.writer_lock`'s 5s budget (whose `required=False` default DEGRADED to an unserialized commit and re-opened the pre-commit stash race) and correct the docstring claiming holders keep the lock "well under a second". THE BUDGET HALF IS ALREADY DONE, by executed plan `9bq5o4` (set `uniwait`, commit `0dac7288`), whose E-05 names this item explicitly and instructs closing it: at HEAD `writer_lock` defaults to `timeout=1800.0`, `required=True`, and its docstring now says "A self-commit can take 10s or more across a pre-commit run (measured 10.6s)". So the item must NOT be re-implemented. What `9bq5o4` left behind is a SECOND defect of its own making plus its own uncorrected documentation. MEASURED 2026-09-29 IN THIS LANE: making the wait fail closed converted expiry from a silent degrade into an UNCAUGHT `CommitLockBusy` that escapes `git_commit_helper.offer_commit` and reaches `cli.main`, which catches only `KeyboardInterrupt` and `EOFError`, so `aw commit` dies with a Python traceback rather than the refusal outcome every caller is written to render. Four of the seven inheriting call sites already branch on `STATUS_ERROR` and print "warning: self-commit skipped"; none can reach that branch because the exception unwinds past them. The user-visible result of a busy peer is therefore a crash, which is the same class of user-perceptible defect the item was filed for.
- Scope: IN: convert the expired-wait refusal at the ONE production `writer_lock` call site into the existing `CommitOutcome(STATUS_ERROR, ...)` contract so every caller's existing refusal branch runs; restore the path-identity test `commit_lock` promises and that died with `tests/test_commit_lock.py`; correct the three false claims in `ipd_lifecycle`'s `FINALIZE_LOCK_WAIT_SECONDS` comment; one CHANGELOG line. OUT: changing the 1800s budget or the `required=True` default (`9bq5o4` set both deliberately and a test pins the 1800s figure), the `ISO_RACED` retry cap, the finalize-side wait and its runner re-attempt ladder (`y2vzit` owns those), the integration lock, and `run_ledger_store.writer_lock` (a different lock on a different file).
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/ipd_lifecycle.py, tests/test_contention_wait.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: bqz8kn
- Blocks-Release: next
- Set: wlockbudget
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 7pxyam
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-606, all FIXED. Every material claim re-measured at review HEAD `1ea30f80`. THE CORE DEFECT REPRODUCED END TO END: with `{"pid": 1, "owner": "peer.test"}` in `commit_lock.lock_path(repo)` and a 0.3s budget, `offer_commit` raised `RAISED UNCAUGHT: CommitLockBusy` carrying all four actionable elements (live PID, owner, seconds waited, absolute lock path), and `cli.main` was confirmed to catch only `KeyboardInterrupt`/`EOFError`. F-1 (defaults 1800.0/True), F-2 (9bq5o4 E-05's verbatim subsumption instruction), F-4 (five call sites with a `STATUS_ERROR` branch), F-5, F-6, F-7 (all three stale claims present), F-8 (`tests/test_commit_lock.py` absent; path identity holds), F-9 and F-10 all verified. BOTH OPEN QUESTIONS RESOLVED, since both named the reviewer as owner: OQ-01's substitution CONFIRMED on new evidence the plan did not cite (`bqz8kn` is `graduated` with `- Graduated-To: wlockbudget`, so the runner already recorded this plan as the handoff); OQ-02's dedicated status DECLINED (no caller retries a busy lock, and five of seven would not see a new status unedited). FOUR CORRECTIONS, each to a claim that would have misled the executor: the Goal promised all seven verbs "exit nonzero", false for five, whose `-> None` helpers correctly warn and exit zero because the artifact rewrite succeeded (F-13); E-06 asserted a known pre-existing test failure, but the suite is fully green at `3246 passed, 2 skipped` with zero FAILED, so the old wording pre-authorized blaming a regression on inherited breakage (F-11); E-05 and V-05 demanded zero TREE-WIDE hits for "well under a second", which is unsatisfiable because backlog `bqz8kn` and `duac3v` quote it as the defect they record, and pursuing it would rewrite this plan's own provenance (F-12); and F-2 called the item `open` when it is `graduated` (F-14). Also recorded that the `with` body holds ELEVEN returns, making a widened `except Exception` the one silent failure mode worth gating. Structural preflight conforming at `author` and `review-finalize`.
- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `bqz8kn`. THE ITEM'S LITERAL ASK IS ALREADY IMPLEMENTED and this plan deliberately does not redo it: executed plan `9bq5o4` E-05 raised the budget to 1800s, flipped `required` to True, and rewrote the docstring, naming `bqz8kn` as the item it resolves. Verified at HEAD by reading `commit_lock.writer_lock`'s signature and docstring. Rather than close the item as already-done, this plan carries the RESIDUE that `9bq5o4` created and did not finish, measured in this lane: the fail-closed raise is uncaught and crashes `aw commit` (reproduced end-to-end through `cli.main`), `ipd_lifecycle`'s comment still asserts the three superseded facts `9bq5o4` falsified, and the path-identity test `commit_lock.py` says "a test asserts the two paths are identical" no longer exists (deleted in `19313eed`). All three are consequences of the same change the item asked for, so the item is the right carrier and its release gate is inherited.

## Goal

Make a busy peer produce the refusal message every `offer_commit` caller already knows how to print, instead of
a Python traceback, and leave no surviving documentation asserting the 5-second budget that no longer exists.

The user-facing property, stated PER VERB because it is not uniform and the earlier wording said it was
(corrected at review). With a live peer holding the shared lock, NO verb prints a stack trace, and each
reports according to the contract it already has:

- `aw commit` (`work_cmd.run_commit`) exits NONZERO with `aw commit: error: <message naming the holder>`,
  because it already returns 1 for any status that is not `committed` or `nothing-to-commit` (F-5).
- `aw set`, `aw specs`, `aw backlog`, `aw rename` and the two archive verbs print
  `warning: self-commit skipped: <message>` and exit ZERO. Measured at review: their shared helper
  (`status_set._offer_self_commit` and its siblings) is annotated `-> None` and its `STATUS_ERROR` branch
  writes a warning without changing the exit code. THIS IS THE CORRECT AND INTENDED BEHAVIOR, not a gap
  this plan should close: the artifact rewrite those verbs performed SUCCEEDED, and only the optional
  convenience commit was skipped, so a nonzero exit would report a failure that did not happen. The
  operator is told to commit it themselves, which is exactly what the message says.

So the honest one-line summary of the change is: a busy peer produces a refusal MESSAGE instead of a
traceback at every call site, and the exit code each verb already used for a failed self-commit is
unchanged. An earlier draft of this Goal promised "exits nonzero" for all seven, which is false for five
of them and would have made V-01's evidence impossible to produce honestly.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop the uncaught refusal

- [x] E-01 In `git_commit_helper.offer_commit`, catch `commit_lock.CommitLockBusy` around the `with _lock.writer_lock(repo_root, owner="git_commit_helper.offer_commit"):` statement and return `CommitOutcome(STATUS_ERROR, None, (), <the exception's message>)` instead of letting it propagate. Keep the raise itself in `commit_lock` untouched: `writer_lock` is a general context manager whose fail-closed contract `9bq5o4` established and a test pins, so the translation belongs at the caller that owns the `CommitOutcome` vocabulary. Place the `try` OUTSIDE the `with` so nothing inside the lock window changes, and so a `CommitLockBusy` raised by the acquisition (the only place it is raised) is the only exception caught: do NOT wrap the body, which would swallow a genuine failure from the staging and commit steps.
  - Depends on: none

  CATCHING `CommitLockBusy` SPECIFICALLY IS WHAT MAKES THE `try` PLACEMENT SAFE, AND THE BLOCK IS BIG, so this is worth stating rather than assuming. Measured at review: the `with` body contains ELEVEN `return` statements, several of them already returning `CommitOutcome(STATUS_ERROR, ...)` for a failed `git add` or a bad trailer. A `try` wrapping the `with` is transparent to every one of them (a `return` is not an exception), which is why this placement costs nothing; but it is ONLY safe because the `except` names `CommitLockBusy`. If it named `Exception` it would convert a genuine mid-commit failure inside that eleven-return body into a lock-busy message, mislabelling a real defect as contention. That is the single most damaging way to mis-implement this item, and it is invisible in the happy path.
  - Expected outcome: with a live peer holding the lock past the budget, `offer_commit` RETURNS an outcome whose `status` is `STATUS_ERROR` and whose message names the holding PID and owner, rather than raising. The five call sites that already branch on `STATUS_ERROR` (`cli._offer_records_commit`, `specs`, `status_set`, `plans_archive`, `research_archive`) reach their existing "warning: self-commit skipped" line with no edit to any of them, and `work_cmd.run_commit` reaches its `return 1` arm.
  - Execution state: performed

  NOTE THE `STATUS_ERROR` ARM IS DOUBLED AT EACH OF THE FIVE, and both halves must become live. Verified at review: each of those five has TWO `STATUS_ERROR` branches, one inside an `is_agent_or_json` block writing to stderr and one in the human path. An `--agent`/`--json` invocation takes the first and a plain invocation the second, so a reproduction driven only one way proves only one arm. Exercise at least one verb BOTH ways.

- [x] E-02 Verify by reading, and record in this plan's Findings, that the message the new outcome carries is the actionable one `commit_lock` already composes (it names the live PID, the owner string, the seconds waited, and the absolute lock path to remove if the holder is dead). Do NOT compose a second message: a caller-side rewrite would drop the lock path, which is the only part a human can act on when the holder is genuinely dead. If the text passes through unchanged, say so; if anything is lost, name what and fix the pass-through rather than the text.
  - Depends on: E-01
  - Expected outcome: a written confirmation that the operator-facing text is preserved verbatim from `commit_lock`'s raise, with the four elements enumerated, and no new message string introduced anywhere.
  - Execution state: performed

### Task group 2: restore the coverage the module promises

- [x] E-03 Add a test to `tests/test_contention_wait.py` asserting `commit_lock.lock_path(repo) == ipd_lifecycle.finalize_lock_path(repo)`. `commit_lock.py`'s comment beside `_LOCK_RELPATH` claims "a test asserts the two paths are identical so they cannot drift apart silently"; that test lived in `tests/test_commit_lock.py`, which was deleted wholesale in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), so the claim is currently false. The nearest survivor only asserts the substring `ipd_finalize_writer.lock` appears in a refusal message, which would still pass if the two directories diverged. Put it in the same file as the other surviving `writer_lock` call-site tests rather than reviving the deleted module, so the lock's coverage stays in one place.
  - Depends on: none
  - Expected outcome: one test that FAILS if either path expression is changed independently, pinning the shared-file property that `commit_lock`'s module docstring calls the whole point of not adding a second lock.
  - Execution state: performed

- [x] E-04 Add a test to `tests/test_contention_wait.py` driving `git_commit_helper.offer_commit` in a real temporary git repository with a live-peer lock payload in place, asserting it RETURNS `STATUS_ERROR` with the holder named and does NOT raise. Use the same fake-`_pid_alive` and small-`timeout` technique the neighbouring `writer_lock` tests already use so the test stays fast. This is the regression guard for E-01 and must exercise the real `offer_commit` (not a stubbed lock), because the defect was precisely that an exception crossed that function boundary.
  - Depends on: E-01
  - Expected outcome: a behavioral test that fails against pre-E-01 code with an uncaught `CommitLockBusy` and passes after, asserting on the returned outcome's status and message rather than on any code structure.
  - Execution state: performed

### Task group 3: retire the superseded claims

- [x] E-05 Correct the comment block on `ipd_lifecycle.FINALIZE_LOCK_WAIT_SECONDS`, which asserts three things that are all false at HEAD, and add the CHANGELOG line. The three: that `writer_lock` holders "keep it for well under a second" (this is the exact false premise backlog `bqz8kn` was filed against, and it survives HERE after `9bq5o4` corrected the copy in `commit_lock`); that `writer_lock` waits "(default 5 s, polling every 50 ms)" (it waits 1800s polling every 0.1s); and the heading "WHY LONGER THAN `writer_lock`'s 5 s", whose whole premise is gone because both budgets now resolve to the same `contention_wait.TIMEOUT_SECONDS`. Keep the paragraph's genuinely load-bearing content: the measured 2026-09-27 race in run `run-20260927T001634Z-258437` that motivated waiting at all, and the reason the bound stays finite. Replace the stale "why longer" heading with the accurate reason the two budgets are now one shared policy constant. Then add ONE `- Fixed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md` describing the user-visible change from E-01 (a busy peer no longer crashes the command), in the user-facing register with no em or en dashes.
  - Depends on: E-01
  - Expected outcome: no PRODUCTION SOURCE file asserts the 5-second budget or the sub-second hold time; `grep -rn "well under a second" agent_workflows/` and `grep -rn "default 5 s" agent_workflows/` each return no hits; the measured-race justification survives; and one CHANGELOG entry describes the fix in user terms.
  - Execution state: performed

  THE EXIT CRITERION IS SCOPED TO `agent_workflows/`, AND THE EARLIER TREE-WIDE VERSION WAS UNSATISFIABLE. Corrected at review. A tree-wide `rg "well under a second"` cannot reach zero hits and MUST NOT: measured at review, the phrase also appears in backlog `bqz8kn`'s own `- Summary:` and body and in DONE backlog item `duac3v`, all of which are DURABLE HISTORICAL RECORDS quoting the false claim as the defect they were filed against. Editing them would rewrite the record of why this work happened, which the repository's plan-lifecycle rules forbid. `default 5 s` is the same shape: at review its only non-plan hit is the one production line E-05 fixes, but the criterion is scoped for the same reason so a future record quoting it cannot make this item fail. Verify with `git status --short` after E-05 that no `.aw/records/` path was modified.

### Task group 4: prove no regression

- [x] E-06 Establish the suite baseline BEFORE any edit in this plan and re-measure it after, then compare. Run `python3 -m pytest` BARE (no added flags) at the unmodified HEAD of this lane and record the summary line plus the full FAILED set; run it again after E-01 through E-05 and record the same. Compare the two FAILED sets and account for every difference. This is ordered last in the checklist but its FIRST half must be performed FIRST, before any source edit, because a baseline taken afterwards cannot distinguish a failure this plan caused from one it inherited.
  - Depends on: E-05
  - Expected outcome: two pasted bare-suite summary lines with their FAILED sets, and an explicit statement of whether the sets are identical. Any new failure is either fixed or explained with evidence; a difference is never waved through as flakiness without naming the test and re-running it.
  - Execution state: performed

  THE SUITE IS GREEN, AND THIS ITEM PREVIOUSLY SAID THE OPPOSITE. Corrected at review: the earlier wording asserted "the repository has at least one known pre-existing failure, so 'the suite is green' is not the expected result and must not be asserted". MEASURED at review HEAD `1ea30f80` with a bare `python3 -m pytest`: `3246 passed, 2 skipped, 3 warnings` and ZERO `FAILED` lines. That correction matters because the old wording pre-authorized an executor to see a failure and attribute it to inherited breakage: with a green baseline, ANY failure in the after-run is caused by this plan and must be fixed, not explained away. Re-measure the baseline yourself rather than trusting this number (another lane may have integrated since), but if your baseline is NOT clean, say so explicitly and name every failing node id, because that is now the surprising result rather than the expected one.

## Project conventions discovered (Step 0)

- The shared lock FILE is one file reached by two expressions: `ipd_lifecycle.finalize_lock_path` composes `checkout_control_root(repo_root) / "state" / "runtime"` then `locks/ipd_finalize_writer.lock`, and `commit_lock._runtime_dir` derives its directory FROM that function (`_life.finalize_lock_path(repo_root).parent.parent`) before `lock_path` re-appends `_LOCK_RELPATH`. Verified identical by evaluating both on a scratch path. `commit_lock`'s module docstring section "RELATIONSHIP TO `ipd_lifecycle`'s LOCK" states sharing is deliberate, because "a second lock would have serialized each surface against itself and none against the other".
- `offer_commit` returns a `CommitOutcome` and NEVER raises for an expected refusal: every other failure path in it returns `CommitOutcome(STATUS_ERROR, ...)` (a bad trailer, a failed `git add`). The uncaught `CommitLockBusy` is the sole exception to that contract, which is why E-01 is a one-place fix rather than seven caller edits.
- `cli.main` deliberately catches only `KeyboardInterrupt` and `EOFError`, documenting that it returns 130 "instead of dumping a traceback". There is no blanket handler, so any other exception from a verb reaches the user as a traceback. This is a deliberate design (a real bug should be loud), which is why the fix is to stop RAISING for an expected condition rather than to add a catch-all in `main`.
- Test-authoring contract (`AGENTS.md`, GUIDING_PRINCIPLES P16): tests must assert observable outcomes, never read production source with `inspect`/`ast`/regex, and never pin symbol censuses. E-03 is the borderline case and stays on the right side of it: it compares two computed PATH VALUES at runtime, which is behavior, not a structural assertion about source text.
- Run the suite BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q` (which suppresses the summary line this plan must paste), or `-p no:randomly`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Where | Finding |
|---|---|---|
| F-1 | `commit_lock.writer_lock` signature | THE ITEM'S ASK IS ALREADY SHIPPED. Defaults at HEAD are `timeout: float = 1800.0`, `required: bool = True`, and the docstring reads "A self-commit can take 10s or more across a pre-commit run (measured 10.6s), so the wait defaults to 30 minutes (1800s)". Re-implementing `bqz8kn` literally would be a no-op at best. |
| F-2 | executed plan `9bq5o4` (set `uniwait`) | Its E-05 is verbatim this item's fix and DECLARES the subsumption: "`bqz8kn` ... is exactly this defect ... after execution close it with `aw backlog set done bqz8kn --evidence <this executed plan>`". Verified verbatim at review. That closure never happened, so the item is still LIVE and still release-gating; it is `graduated` rather than `open` (F-14 corrects the status word this row originally used), which is the stronger position for this plan because the runner has already recorded `wlockbudget` as the item's handoff. |
| F-3 | `git_commit_helper.offer_commit` + `cli.main` | THE RESIDUE, AND THIS PLAN'S REASON TO EXIST. Making the wait fail closed made expiry raise, and nothing catches it. Reproduced end-to-end in this lane on 2026-09-29: a live-peer payload in the lock plus `cli.main(["commit", "--no-plan", "-m", "msg", "--", "f.txt"])` terminated with `CommitLockBusy` propagating out of `cli.main`. Direct `offer_commit` call: `RAISED UNCAUGHT: CommitLockBusy`. |
| F-4 | four `offer_commit` call sites | `cli._offer_records_commit`, `specs`, `status_set`, `plans_archive` and `research_archive` each already contain `if outcome.status == _gch.STATUS_ERROR:` and print "warning: self-commit skipped". The handling exists and is DEAD for this condition because the exception unwinds past it. Confirms E-01 needs no caller edits. |
| F-5 | `work_cmd` (`aw commit` verb) | Ends with `print(f"aw commit: {outcome.status}: {outcome.message}")` and `return 1`, so once E-01 returns an outcome this verb reports a clean nonzero refusal with the holder named, with no edit. |
| F-6 | `runner_shared` coordinator backlog-close commit | Wraps its `offer_commit` call in `except Exception: return None`, so a busy lock there is already non-fatal but SILENT. E-01 converts it to the outcome path, which the surrounding code already treats as "the operator commits it". Noted so a reviewer knows this site is not left worse; narrowing that blanket suppress is `8o709f`'s job, not this plan's. |
| F-7 | `ipd_lifecycle.FINALIZE_LOCK_WAIT_SECONDS` comment | Three stale claims, all falsified by `9bq5o4`: "keep it for well under a second"; "`writer_lock` already waits (default 5 s, polling every 50 ms)"; and the heading "WHY LONGER THAN `writer_lock`'s 5 s" when both constants now resolve to `contention_wait.TIMEOUT_SECONDS` (1800.0). The first is the very sentence `bqz8kn` was filed to correct, surviving in a second location. |
| F-8 | `tests/test_commit_lock.py` | GONE, deleted in `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), so `commit_lock.py`'s comment "a test asserts the two paths are identical so they cannot drift apart silently" is currently a false claim about the suite. `tests/test_contention_wait.py` only asserts the filename substring appears in a refusal message, which cannot catch a directory divergence. Hence E-03. |
| F-9 | `run_ledger_store.writer_lock` | A DIFFERENT lock (`<ledger-path>.lock`, `platform_lock`-based), reached by `run_engine` through `self._store.writer_lock(timeout=...)`, and explicitly not this lock. Named so a reviewer does not read its call sites as in scope. |
| F-10 | `contention_wait` | `POLL_SECONDS = 0.1`, `REPORT_SECONDS = 60.0`, `TIMEOUT_SECONDS = 1800.0` are the single source of truth, with no env var or config key reaching them (`rg "os.environ|getenv"` in that module returns nothing). So the budget is not operator-tunable, which is what makes the 60s stderr progress line the only mitigation during a long wait, and what makes E-01's clean refusal the difference between a usable and an unusable outcome. |
| F-11 | THE SUITE, and E-06's own premise | ADDED AT REVIEW, correcting this plan. E-06 asserted "the repository has at least one known pre-existing failure, so 'the suite is green' is not the expected result and must not be asserted". MEASURED at review HEAD `1ea30f80`, bare `python3 -m pytest`: `3246 passed, 2 skipped, 3 warnings in 47.62s`, with ZERO `FAILED` lines. The suite IS green. This matters beyond accuracy: the old wording pre-authorized an executor to attribute a new failure to inherited breakage, which is precisely how a regression ships. With a green baseline every failure in the after-run belongs to this plan. |
| F-12 | E-05's exit criterion, and `.aw/records/backlog/` | ADDED AT REVIEW. E-05 and V-05 demanded `rg "well under a second"` return no hits TREE-WIDE. That is UNSATISFIABLE and must not be satisfied: measured, the phrase also appears in backlog `bqz8kn`'s `- Summary:` and body and in done item `duac3v`, both of which QUOTE the false claim as the defect they were filed against. An executor pursuing zero tree-wide hits would rewrite the durable record of why this plan exists. Scoped to `agent_workflows/`, where the sole surviving hit is the one line E-05 fixes. |
| F-13 | the Goal's user-facing promise, and `status_set._offer_self_commit` | ADDED AT REVIEW. The Goal promised that `aw commit` "and `aw set`, `aw specs`, `aw backlog`, `aw work`, `aw archive`) exits nonzero" on a busy lock. FALSE for five of the seven: measured, the shared self-commit helper in `status_set`, `specs`, `plans_archive`, `research_archive` and `cli` is annotated `-> None` and its `STATUS_ERROR` arm writes `warning: self-commit skipped` WITHOUT affecting the exit code. Only `work_cmd.run_commit` returns 1 (F-5). The zero exit is CORRECT (the artifact rewrite succeeded; only the optional commit was skipped), so the defect was the plan's claim, not the code. Left as-is and the Goal corrected, because changing five verbs' exit codes would be an interface change well outside a crash fix. |
| F-14 | backlog `bqz8kn`'s current status | ADDED AT REVIEW. The plan says the item is `open` in two places (F-2: "which is why the item is still `open` and still release-gating"; the workflow-history entry). Measured at review: it is `- Status: graduated` with `- Graduated-To: wlockbudget`, so the runner already recorded this plan as its handoff. `- Blocks-Release: next` and `- Work-Kind: bug` are unchanged, so the gate claim and the inheritance argument both stand; only the status word was stale. Corrected so V-06 does not send an executor looking for an `open` item. |
| F-15 | `git_commit_helper.offer_commit` | VERIFIED AT EXECUTION (E-02, V-01, V-02): the message carried by `CommitOutcome` on expired wait is `str(exc)` passed through verbatim from `CommitLockBusy`, preserving all four actionable elements (live PID, owner string, seconds waited, absolute lock path) with no new message literal introduced. |


## Proposed changes (ordered, validatable)

1. E-01: translate the expired-wait raise into `CommitOutcome(STATUS_ERROR, ...)` at `offer_commit`, the single production `writer_lock` call site. One `try`/`except CommitLockBusy` placed outside the `with`.
2. E-02: confirm by reading that the operator-facing message survives the translation with its four actionable elements intact, introducing no second message string.
3. E-03: restore the path-identity test the module promises, in `tests/test_contention_wait.py`.
4. E-04: add the behavioral regression guard that `offer_commit` returns rather than raises under a live-peer lock.
5. E-05: correct the three stale claims in `ipd_lifecycle`'s budget comment, preserving its measured-race justification, and add one user-facing CHANGELOG line.

## Deferred / out of scope (with reason)

- Raising, lowering or making configurable the 1800s budget, and the `required=True` default. `9bq5o4` chose both deliberately after review, and `tests/test_contention_wait.py` pins the 1800s figure in two places (the give-up-at-exactly-1800s helper test and the `(60s of 1800s)` progress assertion). Re-opening that trade-off is a separate decision with its own risk, and nothing measured here argues against the current values.
  - Carrier-Declined: Not an outstanding obligation but a deliberate decision to KEEP the shipped values. `9bq5o4` set them after review and two live tests pin them; nothing measured in this plan argues for a different number, so there is nothing for a future carrier to do. A change here would need new evidence, which would be its own item.
- The `ISO_RACED` retry cap, the finalize-side wait, and the runner's `finalize_with_contention_retry` ladder. Owned by `y2vzit` and `9bq5o4`; both executed and tested, and this plan's change does not touch that path.
  - Carrier-Evidence: .aw/records/plans/executed/20260926-finlockwait-01-y2vzit-make-finalize-wait-for-a-briefly-held-writer-lock-and-retry.ipd.md
- Narrowing `runner_shared`'s blanket `except Exception` around its backlog-close commit (F-6). Owned by pending plan `8o709f`, whose Scope-Paths already claim `runner_shared.py`; touching it here would collide.
  - Carrier: 8o709f
- Closing backlog `bqz8kn` as `done`. The runner sets `graduated` on verification of this authoring turn, and the authoring contract forbids setting `done`. Note for whoever executes: this plan carries the item's `Blocks-Release: next` gate, so the handoff is provable through `- From-Backlog:`.
  - Carrier: bqz8kn

## Scope check

- Over-scope: `agent_workflows/ipd_lifecycle.py` and `CHANGELOG.md` are in `Scope-Paths` although the backlog item names neither. Both are unavoidable and in the item's spirit: the item's second ask is literally "correct the docstring" for the "well under a second" claim, and `ipd_lifecycle` is where that sentence still lives after `9bq5o4` fixed the `commit_lock` copy (F-7), so skipping it would leave the item's own defect in the tree. The CHANGELOG line is required by repository convention for a user-visible behavior change (a command that crashed now refuses cleanly).
- Under-scope: the item's literal budget-and-`required` change is NOT performed, because it is already in the tree (F-1, F-2) and re-doing it would be a no-op or a regression. This is recorded as OQ-01 so a reviewer can overrule the substitution rather than discover it.

## Required tests / validation

- `python3 -m pytest tests/test_contention_wait.py` for the focused surface, run BARE. Paste the summary line and the new tests' names.
- Each new test must be shown FAILING against pre-change code (stash the source change and re-run) so it is proven to bite, per the repository's execution contract. For E-04 the pre-change failure is the uncaught `CommitLockBusy`; for E-03 it is demonstrated by temporarily perturbing one path expression, then restoring it.
- `python3 -m pytest` bare for the whole suite, with a before/after comparison of the FAILED set so any pre-existing failure is not miscounted as a regression.
- `grep -rn "well under a second" agent_workflows/` and `grep -rn "default 5 s" agent_workflows/` must return no hits after E-05. SCOPED TO PRODUCTION SOURCE, not the tree: the phrase legitimately survives in backlog items `bqz8kn` and `duac3v`, which QUOTE the false claim as the defect they record, and a durable record must not be rewritten (corrected at review; the earlier tree-wide form was unsatisfiable).
- An end-to-end manual check mirroring F-3's reproduction: with a live-peer payload written into `commit_lock.lock_path(repo)` and a short timeout, drive the real `aw commit` path and paste the actual terminal output, showing a one-line refusal naming the holder, a nonzero exit, and no traceback.
- `aw ipd lint --phase pre-transition` on this plan must report conforming before any terminal transition.

## Spec / documentation sync

No spec governs these constants: no `.spec.md` file mentions `contention_wait` or `writer_lock`, so there is no
contract document to amend and no `.spec.md` path is declared in `- Scope-Paths:`. The documentation this plan
does change is in-code (the `ipd_lifecycle` comment, E-05) plus one user-facing `CHANGELOG.md` line. No README,
`CONTRIBUTING.md` or `AGENTS.md` statement describes the lock budget, so nothing else needs updating.

## Open questions

### OQ-01: this plan substitutes the residue for the item's literal ask; is that the right call?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW IN FAVOUR OF KEEPING THE SUBSTITUTION, so the plan's `- From-Backlog: bqz8kn` provenance stands unchanged. THE DECIDING EVIDENCE IS THAT THE REPOSITORY HAS ALREADY MADE THIS CHOICE MECHANICALLY: measured at review, `bqz8kn` is `- Status: graduated` with `- Graduated-To: wlockbudget`, which is this plan's Set. The runner recorded this plan as the item's handoff before the question was asked, so redirecting the provenance now would orphan a `graduated` item whose declared successor is this very plan and would require un-graduating it. THE THREE RESIDUE DEFECTS ARE ALSO GENUINELY THIS ITEM'S, not merely adjacent: each is a DIRECT consequence of the change the item asked for. Flipping `required` to True is what turned a silent degrade into a raise (F-3, reproduced at review with the traceback captured); the item's own second ask was "correct the docstring", and `ipd_lifecycle` is where that exact sentence still lives (F-7, verified present); and the path-identity test died in the same trim that left `commit_lock` promising it (F-8, verified absent). So the item's two asks map onto this plan's work, not away from it. THE ALTERNATIVE IS REJECTED ON COST: closing `bqz8kn` with `--evidence 9bq5o4` and filing the residue fresh would drop a `- Blocks-Release: next` gate into a new ungated item (or require re-declaring it), split one coherent change across three carriers, and lose the provable `- From-Backlog:` handoff the close-legitimacy rule reads. Nothing about the E-items changes under either answer, which is why this was correctly marked non-blocking.
- Carrier-Declined: ANSWERED BY THE ACT OF REVIEWING, and now actually answered: the reviewer CONFIRMED the substitution on 2026-09-29, so nothing is left to carry. The question asked the reviewer to confirm or redirect this plan's own provenance, it was decided before execution, and its answer is recorded here, in the review record, and in this plan's workflow history. Either answer left the E-items unchanged, so no deferred work exists for a future carrier, and filing a backlog item to track "was this plan pointed at the right backlog item" would be an obligation with no content.

### OQ-02: should the expired-wait refusal be a distinct status rather than `STATUS_ERROR`?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW IN FAVOUR OF `STATUS_ERROR`, as the plan proposed, and the reviewer does NOT ask for the dedicated status. Verified the premise: `git_commit_helper` defines six statuses (`committed`, `skipped`, `declined`, `refused-dirty`, `nothing-to-commit`, `error`), so adding a seventh is a vocabulary change every consumer of `CommitOutcome.status` may branch on, and measured, all five non-`work_cmd` call sites treat anything that is not `committed` through a single `STATUS_ERROR` arm. A new status would therefore be INVISIBLE to them until each is edited, meaning the enhancement costs seven edits before it buys anything, which the plan states correctly. The retry-distinction precedent is real (`runner_shared.finalize_refusal_is_retryable` partitions refusals into a retryable allowlist for the finalize side, read at review), but it exists because the RUNNER automatically re-attempts; no `offer_commit` caller retries today, so there is no consumer for the distinction. ADDING IT NOW WOULD BE SPECULATIVE GENERALITY against a measured crash fix, and the smallest correct change is the one that makes five existing dead branches live. If a caller later wants to auto-retry a busy lock, that caller's plan is the occasion, and it can distinguish the case from the message without a new status in the meantime.
- Carrier-Declined: A REJECTED ALTERNATIVE DESIGN, not outstanding work, and the reviewer DECLINED to ask for it on 2026-09-29. The plan commits to `STATUS_ERROR`, which fully fixes the measured defect, so nothing is left undone when this plan executes and there is no residue to revisit. The distinct-status idea is speculative generality with no measured demand behind it, verified at review: no `offer_commit` caller retries a busy lock today, so nothing would consume the distinction, and five of the seven callers would not even see a new status until edited. Filing it would create a backlog item nobody can close on evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the diff of the `try`/`except CommitLockBusy` addition in `offer_commit`, showing the `try` is OUTSIDE the `with` and that the `except` names `CommitLockBusy` specifically (not `Exception`). Paste a transcript of a live-peer lock driven through the real `offer_commit` showing the RETURNED status and message (expected shape: `STATUS_ERROR` plus text naming the holding PID and owner), and confirm no traceback appears. A WORKING REPRODUCTION RECIPE, verified at review, so this evidence costs no discovery: in a scratch git repo write `{"pid": 1, "owner": "peer.test"}` into `commit_lock.lock_path(repo)` (PID 1 is always alive, so no `_pid_alive` fake is needed), shrink the budget by wrapping `commit_lock.writer_lock` with `functools.partial(orig, timeout=0.3, report_every=1000.0)`, then call `offer_commit`. At review that produced, verbatim, `RAISED UNCAUGHT: CommitLockBusy | the shared aw writer lock is held by live PID 1 (owner: peer.test); waited 0s. Wait for it to finish, or if that process is dead remove <abs path>`. State explicitly that `commit_lock.writer_lock`'s own raise was left unmodified, with the unchanged signature line quoted. ALSO paste the PER-VERB exit behavior the corrected Goal now claims: `work_cmd.run_commit` returning 1, and at least one of the five `-> None` self-commit helpers printing `warning: self-commit skipped` and NOT changing the exit code (F-13). Do NOT report "all verbs exit nonzero"; that was the earlier draft's false claim.
  - Observed evidence: Live reproduction verified; diff confirms try/except CommitLockBusy outside with.
    1. Diff of the `try`/`except CommitLockBusy` addition in `offer_commit` (`agent_workflows/git_commit_helper.py`), showing the `try` is OUTSIDE the `with` and that the `except` specifically names `_lock.CommitLockBusy`:
    ```diff
    @@ -695,7 +695,8 @@
         # still fails closed. See `commit_lock` for the reproduction and the honest limit.
         from agent_workflows import commit_lock as _lock

    +    try:
    +        with _lock.writer_lock(repo_root, owner="git_commit_helper.offer_commit"):
    ...
    +            return CommitOutcome(
    +                STATUS_ERROR,
    +                None,
    +                tuple(our_staged),
    +                f"git commit failed: {iso.detail}",
    +            )
    +    except _lock.CommitLockBusy as exc:
    +        return CommitOutcome(STATUS_ERROR, None, (), str(exc))
    ```
    2. Live reproduction transcript driving real `offer_commit` with live PID 1 holder and 0.3s timeout in temporary git repository:
    ```
    === DIRECT OFFER_COMMIT ===
    RETURNED status: error
    RETURNED message: the shared aw writer lock is held by live PID 1 (owner: peer.test); waited 0s. Wait for it to finish, or if that process is dead remove /tmp/tmpnxpjnuac/.aw/state/runtime/locks/ipd_finalize_writer.lock
    ```
    Confirmed: outcome status is `error` (`STATUS_ERROR`), message names live PID 1 and owner `peer.test`, and no traceback appears.
    3. `commit_lock.writer_lock`'s own raise was left unmodified. Unchanged signature line:
    ```python
    def writer_lock(
        repo_root: Path,
        *,
        owner: str,
        timeout: float = 1800.0,
        poll: float = 0.1,
        report_every: float = 60.0,
        required: bool = True,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.monotonic,
        report: Optional[Callable[[str], None]] = None,
    ) -> Iterator[bool]:
    ```
    4. Per-verb exit behavior:
    - `work_cmd.run_commit` (`aw commit` verb):
    ```
    === WORK_CMD.RUN_COMMIT ===
    aw commit: no plan governs this commit (--no-plan), so two plan-derived protections are SKIPPED: Scope-Paths enforcement and plan validation. Every other protection is unchanged: only the paths you named are staged, and the shared helper still snapshots the index first and commits only the intersection, so a co-worker's staged change cannot be swept in.
    aw commit: error: the shared aw writer lock is held by live PID 1 (owner: peer.test); waited 0s. Wait for it to finish, or if that process is dead remove /tmp/tmpnxpjnuac/.aw/state/runtime/locks/ipd_finalize_writer.lock
    EXIT CODE: 1
    ```
    - `status_set._offer_self_commit` (human path):
    ```
    === STATUS_SET._OFFER_SELF_COMMIT ===
    warning: self-commit skipped: the shared aw writer lock is held by live PID 1 (owner: peer.test); waited 0s. Wait for it to finish, or if that process is dead remove /tmp/tmpnxpjnuac/.aw/state/runtime/locks/ipd_finalize_writer.lock
    HELPER RETURN VALUE: None
    ```
    - `status_set._offer_self_commit` (agent mode - stderr):
    ```
    === STATUS_SET._OFFER_SELF_COMMIT (AGENT MODE - STDERR) ===
    warning: self-commit skipped: the shared aw writer lock is held by live PID 1 (owner: peer.test); waited 0s. Wait for it to finish, or if that process is dead remove /tmp/tmphlenj97z/.aw/state/runtime/locks/ipd_finalize_writer.lock
    HELPER RETURN VALUE: None
    ```
    Exit code is 0 / unaffected for `status_set._offer_self_commit`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: quote the message string actually carried by the returned outcome and enumerate the four actionable elements present in it (live PID, owner, seconds waited, absolute lock path). Confirm with a `rg` that no new refusal message literal was introduced in `git_commit_helper.py`, pasting the command and its output. If any element was lost, paste the before/after and the fix.
  - Observed evidence: Message string verified with four actionable elements; no new refusal literal in git_commit_helper.py.
    1. Message string carried by the returned outcome:
    `the shared aw writer lock is held by live PID 1 (owner: peer.test); waited 0s. Wait for it to finish, or if that process is dead remove /tmp/tmpnxpjnuac/.aw/state/runtime/locks/ipd_finalize_writer.lock`
    Four actionable elements present:
    - Live PID: `1`
    - Owner: `peer.test`
    - Seconds waited: `0s`
    - Absolute lock path: `/tmp/tmpnxpjnuac/.aw/state/runtime/locks/ipd_finalize_writer.lock`
    2. Confirming with `git diff` that no new refusal message literal was introduced in `git_commit_helper.py`:
    `git diff agent_workflows/git_commit_helper.py | grep -E '^\+[^+]' | grep -i 'writer lock'` returns exit 1 (0 lines matching). The only new text is `return CommitOutcome(STATUS_ERROR, None, (), str(exc))`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the new test's name and source, and its passing result. Then paste proof that it BITES: temporarily change one of the two path expressions (for example `_LOCK_RELPATH`), paste the resulting FAILURE output, restore, and paste the restored pass. Confirm the test compares computed path values at runtime and reads no production source text (P16).
  - Observed evidence: test_writer_lock_and_finalize_lock_paths_are_identical added, verified passing, and proven to bite.
    1. New test name and source:
    `test_writer_lock_and_finalize_lock_paths_are_identical` in `tests/test_contention_wait.py`:
    ```python
    def test_writer_lock_and_finalize_lock_paths_are_identical(self):
        """(E-03) commit_lock.lock_path and ipd_lifecycle.finalize_lock_path resolve to the identical path."""
        from agent_workflows import commit_lock, ipd_lifecycle

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(
                commit_lock.lock_path(repo),
                ipd_lifecycle.finalize_lock_path(repo),
            )
    ```
    2. Passing result:
    `tests/test_contention_wait.py` passed with `12 passed in 2.36s`.
    3. Proof that test bites:
    Temporarily changed `_LOCK_RELPATH` in `agent_workflows/commit_lock.py` to `("locks", "drifted_writer.lock")` and ran `python3 -m pytest tests/test_contention_wait.py -k test_writer_lock_and_finalize_lock_paths_are_identical`:
    ```
    FAILED tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_writer_lock_and_finalize_lock_paths_are_identical
    E AssertionError: PosixPath('/tmp/tmph9v_gfok/.aw/state/runtime/locks/drifted_writer.lock') != PosixPath('/tmp/tmph9v_gfok/.aw/state/runtime/locks/ipd_finalize_writer.lock')
    1 failed in 3.68s
    ```
    Restored `_LOCK_RELPATH = ("locks", "ipd_finalize_writer.lock")`, and re-ran: passed.
    4. Confirmed the test compares computed path values at runtime and reads no production source text (P16).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new test's name and source, its passing result, and its FAILING output against pre-change code (stash E-01, re-run), which must show the uncaught `CommitLockBusy`. Confirm the test drives the real `git_commit_helper.offer_commit` in a real temporary git repository and asserts on the returned outcome, not on a stubbed lock or on code structure.
  - Observed evidence: test_offer_commit_returns_error_outcome_on_busy_writer_lock added, fails pre-change, passes post-change.
    1. New test name and source:
    `test_offer_commit_returns_error_outcome_on_busy_writer_lock` in `tests/test_contention_wait.py`:
    ```python
    def test_offer_commit_returns_error_outcome_on_busy_writer_lock(self):
        """(E-04) offer_commit with a live peer holding writer_lock returns STATUS_ERROR and does not raise."""
        from agent_workflows import commit_lock, git_commit_helper

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            for cmd in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "test@example.com"],
                ["git", "config", "user.name", "Tester"],
            ):
                subprocess.run(cmd, cwd=repo, check=True)

            (repo / "file.txt").write_text("initial\n", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "initial commit"], cwd=repo, check=True
            )

            (repo / "file.txt").write_text("updated\n", encoding="utf-8")

            lock_path = commit_lock.lock_path(repo)
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(
                json.dumps(
                    {
                        "pid": 999999,
                        "owner": "live-peer",
                        "timestamp": "2026-09-29T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )

            orig_writer_lock = commit_lock.writer_lock

            def fast_writer_lock(*args, **kwargs):
                kwargs["timeout"] = 0.1
                kwargs["poll"] = 0.02
                return orig_writer_lock(*args, **kwargs)

            with mock.patch(
                "agent_workflows.commit_lock._pid_alive", return_value=True
            ):
                with mock.patch(
                    "agent_workflows.commit_lock.writer_lock",
                    side_effect=fast_writer_lock,
                ):
                    outcome = git_commit_helper.offer_commit(
                        repo,
                        ["file.txt"],
                        message="test commit",
                        assume_yes=True,
                    )

            self.assertEqual(git_commit_helper.STATUS_ERROR, outcome.status)
            self.assertIsNone(outcome.commit)
            self.assertEqual((), outcome.staged)
            self.assertIn("live PID 999999 (owner: live-peer)", outcome.message)
            self.assertIn("ipd_finalize_writer.lock", outcome.message)
    ```
    2. Failing output against pre-change code:
    Ran against pre-E-01 `git_commit_helper.py`:
    ```
    FAILED tests/test_contention_wait.py::ContentionWaitCallSiteTests::test_offer_commit_returns_error_outcome_on_busy_writer_lock
    ...
    agent_workflows/commit_lock.py:683: CommitLockBusy
    E agent_workflows.commit_lock.CommitLockBusy: the shared aw writer lock is held by live PID 999999 (owner: live-peer); waited 0s. Wait for it to finish, or if that process is dead remove /tmp/tmpttxrcdc2/repo/.aw/state/runtime/locks/ipd_finalize_writer.lock
    1 failed, 11 passed in 4.56s
    ```
    3. Passing output after E-01:
    `12 passed in 2.36s`.
    4. Confirmed the test drives real `git_commit_helper.offer_commit` in a real temporary git repository and asserts on returned outcome, not on stubbed lock or code structure.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the corrected `FINALIZE_LOCK_WAIT_SECONDS` comment in full, showing all three stale claims gone and the measured 2026-09-27 race justification retained. Paste `grep -rn "well under a second" agent_workflows/` and `grep -rn "default 5 s" agent_workflows/` output proving zero hits IN PRODUCTION SOURCE. Do NOT run these tree-wide and do NOT attempt to reach zero hits tree-wide: backlog `bqz8kn` and `duac3v` quote the false claim as the defect they record, and editing a durable record to satisfy a grep would destroy the provenance of this very plan (corrected at review). Paste `git status --short` showing no `.aw/records/` path modified by E-05. Paste the added CHANGELOG line and confirm it is under `## 2.0.0 (pending)`, is user-facing, and contains no em or en dash.
  - Observed evidence: Comment corrected, zero hits in production source, clean git status, and one CHANGELOG line added.
    1. Corrected `FINALIZE_LOCK_WAIT_SECONDS` comment in `agent_workflows/ipd_lifecycle.py`:
    ```python
    #: How long ``acquire_finalize_lock`` WAITS for a LIVE holder before refusing, in seconds.
    #:
    #: WHY IT WAITS AT ALL. This lock file is SHARED with ``commit_lock.writer_lock`` (``aw commit``,
    #: ``aw set``, the runners' self-commits), and it used to be checked exactly ONCE. With several
    #: drivers in one checkout that single check lost ordinary races: measured 2026-09-27, run
    #: ``run-20260927T001634Z-258437`` had TWO verified items (``8y13kn``, ``cnzrxb``) refused
    #: ``fail-gate`` because a peer's commit held the lock at the instant finalize looked, and both
    #: holder PIDs had exited moments later.
    #:
    #: SHARED TIMEOUT POLICY. Both ``acquire_finalize_lock`` and ``writer_lock`` share the same
    #: ``contention_wait.TIMEOUT_SECONDS`` budget. A self-commit or a finalize transaction can run
    #: hooks and lint over multiple seconds, so queueing callers wait for the active holder rather than
    #: failing on an ordinary race. The bound stays finite: a genuinely stuck holder still refuses with
    #: the diagnostic below, it just no longer refuses on a race it would have won a moment later.
    FINALIZE_LOCK_WAIT_SECONDS = contention_wait.TIMEOUT_SECONDS
    ```
    All three stale claims ("well under a second", "default 5 s", "WHY LONGER THAN writer_lock's 5 s") removed; measured 2026-09-27 race justification and finite bound retained.
    2. Production source grep results:
    `grep -rn "well under a second" agent_workflows/`: 0 hits.
    `grep -rn "default 5 s" agent_workflows/`: 0 hits.
    3. `git status --short` shows no `.aw/records/` paths modified by E-05:
    ```
    M CHANGELOG.md
    M agent_workflows/git_commit_helper.py
    M agent_workflows/ipd_lifecycle.py
    M tests/test_contention_wait.py
    ```
    4. Added CHANGELOG line under `## 2.0.0 (pending)`:
    `- Fixed: when another process holds the shared writer lock past the wait budget, commands now report a clean refusal message naming the lock holder instead of failing with an unhandled exception traceback.`
    Confirmed user-facing and contains no em or en dashes.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the BARE `python3 -m pytest` summary line from before the change and after it, plus the FAILED set for each, and state whether the two FAILED sets are identical. THE BASELINE IS EXPECTED TO BE CLEAN: review measured `3246 passed, 2 skipped, 3 warnings` with ZERO `FAILED` lines at HEAD `1ea30f80` (F-11), correcting this plan's earlier claim that a known pre-existing failure existed. So any failure in the AFTER run is caused by this plan and must be FIXED, not attributed to inherited breakage; and if your BEFORE run is not clean, name every failing node id explicitly, because that is now the surprising result. Compare node IDS, not totals. Also paste the focused `python3 -m pytest tests/test_contention_wait.py` summary. Confirm no flag was added to the bare invocation (no `-n0`, no extra `-q`, no `-p no:randomly`), and confirm the pre-change baseline was captured before the first source edit.
  - Observed evidence: Full suite passes bare (3525 passed, 0 failed), clean baseline (3523 passed, 0 failed), focused suite passes.
    1. Bare `python3 -m pytest` before any change:
    `3523 passed, 2 skipped, 3 warnings in 108.27s (0:01:48)`
    FAILED set: none (0 failed).
    2. Bare `python3 -m pytest` after changes:
    `3525 passed, 2 skipped, 3 warnings in 65.92s (0:01:05)`
    FAILED set: none (0 failed).
    3. FAILED sets comparison: identical (both clean, 0 failed). Net +2 passed tests corresponding to E-03 and E-04.
    4. Focused `python3 -m pytest tests/test_contention_wait.py`:
    `12 passed in 2.35s`
    5. Confirmed no flags added to bare invocation (run bare as `python3 -m pytest`), and baseline was captured prior to any edits.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution.

WHAT THE HUMAN IS APPROVING. The backlog item's literal ask (raise the 5s writer-lock budget, correct the
"well under a second" docstring) is ALREADY IN THE TREE, shipped by executed plan `9bq5o4`, and this plan
deliberately does not redo it. Verified independently at review: `writer_lock` defaults to `timeout=1800.0`,
`required=True`, and its docstring now cites the measured 10.6s hook run. What this plan fixes is the
RESIDUE that change created and did not finish, and the main defect was reproduced at review rather than
taken on trust: with a live peer holding the lock, `offer_commit` raises an uncaught `CommitLockBusy` that
escapes to `cli.main`, which catches only `KeyboardInterrupt` and `EOFError`, so a busy peer crashes the
command with a traceback. Five call sites already contain a `warning: self-commit skipped` branch that the
exception unwinds straight past. The fix is one `try`/`except CommitLockBusy` at the single production call
site, plus two restored tests and one stale comment block.

REVIEW CONFIRMED THE PROVENANCE SUBSTITUTION (OQ-01) rather than redirecting it, on evidence the plan did
not cite: backlog `bqz8kn` is `- Status: graduated` with `- Graduated-To: wlockbudget`, so the runner had
already recorded this plan as the item's handoff. Review also DECLINED the dedicated `lock-busy` status
(OQ-02), because no caller retries a busy lock today and five of seven would not see a new status without
being edited. Both questions are now `resolved`.

WHAT REVIEW CORRECTED, because the plan's own claims were wrong in ways that would have misled the executor:
the Goal promised all seven verbs "exit nonzero", which is false for five of them (they warn and exit zero,
correctly, since the artifact rewrite succeeded); E-06 asserted a known pre-existing test failure, and the
suite is in fact fully green, so the old wording would have licensed attributing a regression to inherited
breakage; and E-05's exit criterion demanded zero tree-wide hits for a phrase that durable backlog records
legitimately quote, which is unsatisfiable and whose pursuit would rewrite this plan's own provenance.

Execution contract. Commit ONLY the paths in `- Scope-Paths:` through `aw commit 7pxyam -- <paths>`; never
`git add -A`, never `-a`, never `--no-verify`, never push. Verify the staged set with
`git diff --cached --name-only` before committing, and re-verify after any failed raw commit attempt, since
this is a shared checkout and another party's restored path must never enter the commit. Paste actual runner
output for every test claim; a summary line reconstructed from memory is not evidence. An out-of-scope edit
is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop.

THE ONE WAY THIS PLAN CAN FAIL SILENTLY. Widening E-01's `except CommitLockBusy` to `except Exception` would
look equivalent and pass every test this plan adds, while converting any genuine mid-commit failure inside
the lock window into a "lock is busy" message. That window contains eleven `return` statements, several
already reporting real errors, so the mislabelling would hide a live defect as contention. V-01 requires the
`except` clause to be shown naming `CommitLockBusy` specifically.

Post-gate lifecycle. Do not claim done or move this plan to `.aw/records/plans/executed/` or mark it
`executed` until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries
pasted evidence. Make the transition through the tooled lifecycle (`aw ipd begin` / `aw ipd finalize`),
never by a hand edit or a hand `git mv`. In a managed lane the RUNNER owns the transition and `aw ipd begin`
refuses with `AW-LIFECYCLE-ROLE-001`; if that happens, record the refusal, leave the plan in `pending/` with
its evidence, and let the runner finalize. Backlog `bqz8kn` carries `- Blocks-Release: next` and this plan
inherits it, so the gate travels here through `- From-Backlog:`; the item is already `graduated` (not
`open`, corrected at review per F-14) and reaches `done` only once this plan is `executed`, at which point
the executor closes it citing this plan as evidence, alongside noting `9bq5o4` as the carrier of the budget
half (F-2). Do not set it `done` from this authoring or review turn.
