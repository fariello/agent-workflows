# IPD: Render the now-fail-closed writer lock refusal as an outcome instead of a traceback, and correct the three stale budget claims

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `bqz8kn` asks for two things: raise `commit_lock.writer_lock`'s 5s budget (whose `required=False` default DEGRADED to an unserialized commit and re-opened the pre-commit stash race) and correct the docstring claiming holders keep the lock "well under a second". THE BUDGET HALF IS ALREADY DONE, by executed plan `9bq5o4` (set `uniwait`, commit `0dac7288`), whose E-05 names this item explicitly and instructs closing it: at HEAD `writer_lock` defaults to `timeout=1800.0`, `required=True`, and its docstring now says "A self-commit can take 10s or more across a pre-commit run (measured 10.6s)". So the item must NOT be re-implemented. What `9bq5o4` left behind is a SECOND defect of its own making plus its own uncorrected documentation. MEASURED 2026-09-29 IN THIS LANE: making the wait fail closed converted expiry from a silent degrade into an UNCAUGHT `CommitLockBusy` that escapes `git_commit_helper.offer_commit` and reaches `cli.main`, which catches only `KeyboardInterrupt` and `EOFError`, so `aw commit` dies with a Python traceback rather than the refusal outcome every caller is written to render. Four of the seven inheriting call sites already branch on `STATUS_ERROR` and print "warning: self-commit skipped"; none can reach that branch because the exception unwinds past them. The user-visible result of a busy peer is therefore a crash, which is the same class of user-perceptible defect the item was filed for.
- Scope: IN: convert the expired-wait refusal at the ONE production `writer_lock` call site into the existing `CommitOutcome(STATUS_ERROR, ...)` contract so every caller's existing refusal branch runs; restore the path-identity test `commit_lock` promises and that died with `tests/test_commit_lock.py`; correct the three false claims in `ipd_lifecycle`'s `FINALIZE_LOCK_WAIT_SECONDS` comment; one CHANGELOG line. OUT: changing the 1800s budget or the `required=True` default (`9bq5o4` set both deliberately and a test pins the 1800s figure), the `ISO_RACED` retry cap, the finalize-side wait and its runner re-attempt ladder (`y2vzit` owns those), the integration lock, and `run_ledger_store.writer_lock` (a different lock on a different file).
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/ipd_lifecycle.py, tests/test_contention_wait.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: bqz8kn
- Blocks-Release: next
- Set: wlockbudget
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 7pxyam

## Workflow history

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `bqz8kn`. THE ITEM'S LITERAL ASK IS ALREADY IMPLEMENTED and this plan deliberately does not redo it: executed plan `9bq5o4` E-05 raised the budget to 1800s, flipped `required` to True, and rewrote the docstring, naming `bqz8kn` as the item it resolves. Verified at HEAD by reading `commit_lock.writer_lock`'s signature and docstring. Rather than close the item as already-done, this plan carries the RESIDUE that `9bq5o4` created and did not finish, measured in this lane: the fail-closed raise is uncaught and crashes `aw commit` (reproduced end-to-end through `cli.main`), `ipd_lifecycle`'s comment still asserts the three superseded facts `9bq5o4` falsified, and the path-identity test `commit_lock.py` says "a test asserts the two paths are identical" no longer exists (deleted in `19313eed`). All three are consequences of the same change the item asked for, so the item is the right carrier and its release gate is inherited.

## Goal

Make a busy peer produce the refusal message every `offer_commit` caller already knows how to print, instead of
a Python traceback, and leave no surviving documentation asserting the 5-second budget that no longer exists.

The user-facing property: with a live peer holding the shared lock, `aw commit` (and `aw set`, `aw specs`,
`aw backlog`, `aw work`, `aw archive`) exits nonzero with a one-line explanation naming the holder, and never
prints a stack trace.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop the uncaught refusal

- [ ] E-01 In `git_commit_helper.offer_commit`, catch `commit_lock.CommitLockBusy` around the `with _lock.writer_lock(repo_root, owner="git_commit_helper.offer_commit"):` statement and return `CommitOutcome(STATUS_ERROR, None, (), <the exception's message>)` instead of letting it propagate. Keep the raise itself in `commit_lock` untouched: `writer_lock` is a general context manager whose fail-closed contract `9bq5o4` established and a test pins, so the translation belongs at the caller that owns the `CommitOutcome` vocabulary. Place the `try` OUTSIDE the `with` so nothing inside the lock window changes, and so a `CommitLockBusy` raised by the acquisition (the only place it is raised) is the only exception caught: do NOT wrap the body, which would swallow a genuine failure from the staging and commit steps.
  - Depends on: none
  - Expected outcome: with a live peer holding the lock past the budget, `offer_commit` RETURNS an outcome whose `status` is `STATUS_ERROR` and whose message names the holding PID and owner, rather than raising. The four call sites that already branch on `STATUS_ERROR` (`cli._offer_records_commit`, `specs`, `status_set`, `plans_archive`/`research_archive`) reach their existing "warning: self-commit skipped" line with no edit to any of them.
  - Execution state: pending

- [ ] E-02 Verify by reading, and record in this plan's Findings, that the message the new outcome carries is the actionable one `commit_lock` already composes (it names the live PID, the owner string, the seconds waited, and the absolute lock path to remove if the holder is dead). Do NOT compose a second message: a caller-side rewrite would drop the lock path, which is the only part a human can act on when the holder is genuinely dead. If the text passes through unchanged, say so; if anything is lost, name what and fix the pass-through rather than the text.
  - Depends on: E-01
  - Expected outcome: a written confirmation that the operator-facing text is preserved verbatim from `commit_lock`'s raise, with the four elements enumerated, and no new message string introduced anywhere.
  - Execution state: pending

### Task group 2: restore the coverage the module promises

- [ ] E-03 Add a test to `tests/test_contention_wait.py` asserting `commit_lock.lock_path(repo) == ipd_lifecycle.finalize_lock_path(repo)`. `commit_lock.py`'s comment beside `_LOCK_RELPATH` claims "a test asserts the two paths are identical so they cannot drift apart silently"; that test lived in `tests/test_commit_lock.py`, which was deleted wholesale in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), so the claim is currently false. The nearest survivor only asserts the substring `ipd_finalize_writer.lock` appears in a refusal message, which would still pass if the two directories diverged. Put it in the same file as the other surviving `writer_lock` call-site tests rather than reviving the deleted module, so the lock's coverage stays in one place.
  - Depends on: none
  - Expected outcome: one test that FAILS if either path expression is changed independently, pinning the shared-file property that `commit_lock`'s module docstring calls the whole point of not adding a second lock.
  - Execution state: pending

- [ ] E-04 Add a test to `tests/test_contention_wait.py` driving `git_commit_helper.offer_commit` in a real temporary git repository with a live-peer lock payload in place, asserting it RETURNS `STATUS_ERROR` with the holder named and does NOT raise. Use the same fake-`_pid_alive` and small-`timeout` technique the neighbouring `writer_lock` tests already use so the test stays fast. This is the regression guard for E-01 and must exercise the real `offer_commit` (not a stubbed lock), because the defect was precisely that an exception crossed that function boundary.
  - Depends on: E-01
  - Expected outcome: a behavioral test that fails against pre-E-01 code with an uncaught `CommitLockBusy` and passes after, asserting on the returned outcome's status and message rather than on any code structure.
  - Execution state: pending

### Task group 3: retire the superseded claims

- [ ] E-05 Correct the comment block on `ipd_lifecycle.FINALIZE_LOCK_WAIT_SECONDS`, which asserts three things that are all false at HEAD, and add the CHANGELOG line. The three: that `writer_lock` holders "keep it for well under a second" (this is the exact false premise backlog `bqz8kn` was filed against, and it survives HERE after `9bq5o4` corrected the copy in `commit_lock`); that `writer_lock` waits "(default 5 s, polling every 50 ms)" (it waits 1800s polling every 0.1s); and the heading "WHY LONGER THAN `writer_lock`'s 5 s", whose whole premise is gone because both budgets now resolve to the same `contention_wait.TIMEOUT_SECONDS`. Keep the paragraph's genuinely load-bearing content: the measured 2026-09-27 race in run `run-20260927T001634Z-258437` that motivated waiting at all, and the reason the bound stays finite. Replace the stale "why longer" heading with the accurate reason the two budgets are now one shared policy constant. Then add ONE `- Fixed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md` describing the user-visible change from E-01 (a busy peer no longer crashes the command), in the user-facing register with no em or en dashes.
  - Depends on: E-01
  - Expected outcome: no file in the tree asserts the 5-second budget or the sub-second hold time; `rg "well under a second"` and `rg "default 5 s"` return no hits; the measured-race justification survives; and one CHANGELOG entry describes the fix in user terms.
  - Execution state: pending

### Task group 4: prove no regression

- [ ] E-06 Establish the suite baseline BEFORE any edit in this plan and re-measure it after, then compare. Run `python3 -m pytest` BARE (no added flags) at the unmodified HEAD of this lane and record the summary line plus the full FAILED set; run it again after E-01 through E-05 and record the same. Compare the two FAILED sets and account for every difference. This is ordered last in the checklist but its FIRST half must be performed FIRST, before any source edit, because a baseline taken afterwards cannot distinguish a failure this plan caused from one it inherited; the repository has at least one known pre-existing failure, so "the suite is green" is not the expected result and must not be asserted.
  - Depends on: E-05
  - Expected outcome: two pasted bare-suite summary lines with their FAILED sets, and an explicit statement of whether the sets are identical. Any new failure is either fixed or explained with evidence; a difference is never waved through as flakiness without naming the test and re-running it.
  - Execution state: pending

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
| F-2 | executed plan `9bq5o4` (set `uniwait`) | Its E-05 is verbatim this item's fix and DECLARES the subsumption: "`bqz8kn` ... is exactly this defect ... after execution close it with `aw backlog set done bqz8kn --evidence <this executed plan>`". That closure never happened, which is why the item is still `open` and still release-gating. |
| F-3 | `git_commit_helper.offer_commit` + `cli.main` | THE RESIDUE, AND THIS PLAN'S REASON TO EXIST. Making the wait fail closed made expiry raise, and nothing catches it. Reproduced end-to-end in this lane on 2026-09-29: a live-peer payload in the lock plus `cli.main(["commit", "--no-plan", "-m", "msg", "--", "f.txt"])` terminated with `CommitLockBusy` propagating out of `cli.main`. Direct `offer_commit` call: `RAISED UNCAUGHT: CommitLockBusy`. |
| F-4 | four `offer_commit` call sites | `cli._offer_records_commit`, `specs`, `status_set`, `plans_archive` and `research_archive` each already contain `if outcome.status == _gch.STATUS_ERROR:` and print "warning: self-commit skipped". The handling exists and is DEAD for this condition because the exception unwinds past it. Confirms E-01 needs no caller edits. |
| F-5 | `work_cmd` (`aw commit` verb) | Ends with `print(f"aw commit: {outcome.status}: {outcome.message}")` and `return 1`, so once E-01 returns an outcome this verb reports a clean nonzero refusal with the holder named, with no edit. |
| F-6 | `runner_shared` coordinator backlog-close commit | Wraps its `offer_commit` call in `except Exception: return None`, so a busy lock there is already non-fatal but SILENT. E-01 converts it to the outcome path, which the surrounding code already treats as "the operator commits it". Noted so a reviewer knows this site is not left worse; narrowing that blanket suppress is `8o709f`'s job, not this plan's. |
| F-7 | `ipd_lifecycle.FINALIZE_LOCK_WAIT_SECONDS` comment | Three stale claims, all falsified by `9bq5o4`: "keep it for well under a second"; "`writer_lock` already waits (default 5 s, polling every 50 ms)"; and the heading "WHY LONGER THAN `writer_lock`'s 5 s" when both constants now resolve to `contention_wait.TIMEOUT_SECONDS` (1800.0). The first is the very sentence `bqz8kn` was filed to correct, surviving in a second location. |
| F-8 | `tests/test_commit_lock.py` | GONE, deleted in `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), so `commit_lock.py`'s comment "a test asserts the two paths are identical so they cannot drift apart silently" is currently a false claim about the suite. `tests/test_contention_wait.py` only asserts the filename substring appears in a refusal message, which cannot catch a directory divergence. Hence E-03. |
| F-9 | `run_ledger_store.writer_lock` | A DIFFERENT lock (`<ledger-path>.lock`, `platform_lock`-based), reached by `run_engine` through `self._store.writer_lock(timeout=...)`, and explicitly not this lock. Named so a reviewer does not read its call sites as in scope. |
| F-10 | `contention_wait` | `POLL_SECONDS = 0.1`, `REPORT_SECONDS = 60.0`, `TIMEOUT_SECONDS = 1800.0` are the single source of truth, with no env var or config key reaching them (`rg "os.environ|getenv"` in that module returns nothing). So the budget is not operator-tunable, which is what makes the 60s stderr progress line the only mitigation during a long wait, and what makes E-01's clean refusal the difference between a usable and an unusable outcome. |

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
- `rg "well under a second"` and `rg "default 5 s"` across the tree must return no hits after E-05.
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
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NOT blocking, because the substitution is defensible from evidence in the tree and the plan is executable as written either way. The item asks for a budget raise and a docstring fix; `9bq5o4` already did the budget raise and fixed one of the two copies of the docstring claim (F-1, F-2). Closing the item as already-done would leave three real defects its own change created: an uncaught refusal that crashes `aw commit` (F-3, measured), the same false claim surviving in `ipd_lifecycle` (F-7), and a module comment promising a test that no longer exists (F-8). Authoring a fresh unrelated item for each would scatter one change across three carriers and drop this item's release gate. The alternative a reviewer might prefer is to close `bqz8kn` with `--evidence` citing `9bq5o4` and file the residue separately; if so, this plan's E-items are unchanged and only its `- From-Backlog:` provenance moves.
- Carrier-Declined: This question is ANSWERED BY THE ACT OF REVIEWING and leaves nothing behind to carry. It asks the reviewer to confirm or redirect this plan's own provenance, so it is decided before execution and its answer is recorded in the review record and this plan's history; it cannot outlive the plan. Either answer leaves the E-items unchanged, so there is no deferred work for a future carrier to pick up, and filing a backlog item to track "was this plan pointed at the right backlog item" would be an obligation with no content.

### OQ-02: should the expired-wait refusal be a distinct status rather than `STATUS_ERROR`?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NOT blocking; `STATUS_ERROR` is chosen and is sufficient. Every caller already branches on it (F-4, F-5), so reusing it fixes the crash with zero caller edits, which is the smallest change that restores correct behavior. A dedicated status (say `lock-busy`) would let a caller distinguish "retry later" from "this will never work", which the runner's `finalize_with_contention_retry` does for the finalize side. That is a genuine enhancement and deliberately not taken here: it would require touching all seven call sites to be useful, widening a bug fix into an interface change. Recorded so the reviewer can ask for it explicitly if the retry distinction is wanted now.
- Carrier-Declined: A REJECTED ALTERNATIVE DESIGN, not outstanding work. The plan commits to `STATUS_ERROR`, which fully fixes the measured defect, so nothing is left undone when this plan executes and there is no residue to revisit. The distinct-status idea is speculative generality with no measured demand behind it (no caller today wants to distinguish the two cases), so filing it would create a backlog item nobody can close on evidence. If the reviewer wants it, it belongs in THIS plan's scope before approval rather than in a carrier afterwards.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of the `try`/`except CommitLockBusy` addition in `offer_commit`, showing the `try` is OUTSIDE the `with` and that the `except` names `CommitLockBusy` specifically (not `Exception`). Paste a transcript of a live-peer lock driven through the real `offer_commit` showing the RETURNED status and message (expected shape: `STATUS_ERROR` plus text naming the holding PID and owner), and confirm no traceback appears. State explicitly that `commit_lock.writer_lock`'s own raise was left unmodified, with the unchanged signature line quoted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: quote the message string actually carried by the returned outcome and enumerate the four actionable elements present in it (live PID, owner, seconds waited, absolute lock path). Confirm with a `rg` that no new refusal message literal was introduced in `git_commit_helper.py`, pasting the command and its output. If any element was lost, paste the before/after and the fix.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new test's name and source, and its passing result. Then paste proof that it BITES: temporarily change one of the two path expressions (for example `_LOCK_RELPATH`), paste the resulting FAILURE output, restore, and paste the restored pass. Confirm the test compares computed path values at runtime and reads no production source text (P16).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test's name and source, its passing result, and its FAILING output against pre-change code (stash E-01, re-run), which must show the uncaught `CommitLockBusy`. Confirm the test drives the real `git_commit_helper.offer_commit` in a real temporary git repository and asserts on the returned outcome, not on a stubbed lock or on code structure.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the corrected `FINALIZE_LOCK_WAIT_SECONDS` comment in full, showing all three stale claims gone and the measured 2026-09-27 race justification retained. Paste `rg "well under a second"` and `rg "default 5 s"` output proving zero hits tree-wide. Paste the added CHANGELOG line and confirm it is under `## 2.0.0 (pending)`, is user-facing, and contains no em or en dash.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the BARE `python3 -m pytest` summary line from before the change and after it, plus the FAILED set for each, and state whether the two FAILED sets are identical. Any new failure must be explained or fixed. Also paste the focused `python3 -m pytest tests/test_contention_wait.py` summary. Confirm no flag was added to the bare invocation (no `-n0`, no extra `-q`, no `-p no:randomly`), and confirm the pre-change baseline was captured before the first source edit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; it is `to-review` and carries no `- Readiness:`
field, which is `/plan-review`'s output to write and not the author's.

Execution contract. Commit ONLY the paths in `- Scope-Paths:` through `aw commit 7pxyam -- <paths>`; never
`git add -A`, never `-a`, never `--no-verify`, never push. Paste actual runner output for every test claim; a
summary line reconstructed from memory is not evidence. The reviewer should note that this plan DELIBERATELY
does not implement the backlog item's literal text (OQ-01) because that work is already in the tree, and
should either confirm the substitution or redirect the provenance.

Post-gate lifecycle. Do not move this plan to `.aw/records/plans/executed/` or mark it `executed` until
`aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted evidence. In a
runner lane the runner owns finalize; a hand executor uses `aw ipd finalize`. Backlog `bqz8kn` carries
`- Blocks-Release: next` and this plan inherits it, so the gate travels here through `- From-Backlog:`; the
item reaches `done` only once this plan is `executed`, and the executor should close it citing this plan as
evidence, alongside noting `9bq5o4` as the carrier of the budget half (F-2).
