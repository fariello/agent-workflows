# Review findings: plan y2vzit

- Subject-Id: y2vzit
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f9b5bc9c` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize` conforms after. No
pre-review snapshot was needed: the plan was committed and unmodified, and the lane-input copy at
`.aw/state/lane-inputs/rev-8/` is byte-identical to the tracked file.

THE DIAGNOSIS IS CORRECT AND I RE-DERIVED ALL OF IT FROM THE CODE. `acquire_finalize_lock` really has no
loop: it reads the lock file once, and `if alive: raise TransactionLockError(...)` immediately. The refusal
really does interpolate `data.get("plan_id")`, which is `None` for a `commit_lock.try_acquire` holder
because that function writes `owner` and no `plan_id` - so `(plan None)` is exactly what a `writer_lock`
holder produces. `finalize_refusal_is_retryable` really is a positive allowlist with two arms
(`RETRYABLE_FINALIZE_SUMMARY`, `RETRYABLE_STALE_RECEIPT_SUMMARY`) and no lock class. The lock file really
is shared (`commit_lock._LOCK_RELPATH` with the comment "The lock file is SHARED with
`ipd_lifecycle.finalize_lock_path`"), and `writer_lock` really does claim "A self-commit holds the lock for
well under a second" while arguing FROM that premise for its short 5s budget. The integration-lock
precedent is real and its docstring says what the plan says it says: "EXPIRY DEFERS, IT DOES NOT FAIL ...
Failing the lane on a lock timeout would discard a completed validation, which is the very cost this
serialization exists to avoid."

I ALSO CONFIRMED THE PLAN'S LOAD-BEARING SAFETY CLAIM RATHER THAN LEAVING IT TO THE EXECUTOR. All three
`acquire_finalize_lock` call sites (`ipd_lifecycle.py:3400`, `:3937`, `:4190`) take the lock immediately
before entering their transaction inside `try:`/`finally: release_finalize_lock(...)`; the journal's first
write (`journal["phase"] = PHASE_MUTATING`) is at `:4416`, INSIDE `_finalize_transaction`; and a grep for
`write_text`/`unlink`/`git_mv`/`subprocess.run`/`_atomic_write` between the main path's entry and its lock
acquisition returns nothing. So "nothing is mutated" holds, which is what makes the refusal a transient
precondition rather than a 5.5 lease conflict. V-03 still requires the executor to re-derive it at the
executing HEAD, because that is the kind of claim that rots.

WHAT I FOUND THAT THE PLAN HAD NOT, in descending order of consequence.

FIRST, AND IT WOULD HAVE COST TWO MINUTES ON EVERY SUITE RUN. E-01 sets a 120-second DEFAULT wait, and
`tests/test_ipd_lifecycle_cli.py::...::test_lock_contention_and_stale_reclamation` spawns a real
`time.sleep(60)` child, writes its PID into the lock, and asserts `acquire_finalize_lock` raises. Measured
at review, that test passes in 0.25s:

```text
1 passed, 37 deselected in 0.25s
```

With a 120s default and no explicit `timeout` at that call site, the assertion would block for the full
budget before raising. The file carries no `pytest.mark.slow`, so that lands in every bare run. The plan
declared the file in `- Scope-Paths:` and described ADDING cases to the class, but never said an existing
assertion must change, so an executor following it literally would have shipped the hang. E-05 now starts by
fixing that test with an explicit short timeout, keeping its intent and its "the liveness probe must OBSERVE
the holder, never kill it" assertion, and V-01 requires the narrowed timing pasted against the 0.25s
baseline.

SECOND, THE PLAN NAMED THE TERMINAL STATUS BY ITS ALIAS. The plan says an exhausted contention "ends
`fail-gate`", but the WRITER writes `failed-safely`: `FINALIZE_RETRY_EXHAUSTED_STATUS: str =
"failed-safely"` and `item["status"] = FINALIZE_RETRY_EXHAUSTED_STATUS`, with `TERMINAL_STATUS_ALIASES`
mapping `"failed-safely": "fail-gate"` on READ. That is precisely why the observed run record shows
`fail-gate`. An executor taking the plan literally could write the literal into a writer and bypass the
alias layer the statusvocab work established, whose own comment documents the read/write asymmetry
deliberately. E-03 now says to reuse the constant, and V-03 requires a grep showing no new `fail-gate`
literal entered a writer.

THIRD, THERE ARE TWO REFUSAL ARMS AND THE RE-ATTEMPT DESIGN DID NOT SAY WHICH. `handle_finalize_refusal` is
called at `runner_shared.py:29638` and `:29694`. The first is the LANE arm, reached after the lane's
integration decision, where `driver_finalize` runs with `repo` set to the lane worktree; that function's own
`lanetruth af7i6p` comment says "`repo` here is the LANE worktree ... `cwd=str(repo)` below keeps it that
way DELIBERATELY, because finalize must resolve paths against the tree it is finalizing". A re-attempt that
re-resolved `repo` to main, or that re-ran the surrounding integration step, would be a materially more
dangerous operation than the one the plan describes. E-03 now requires the arm to be named in the code
comment and the lane `repo` argument preserved; E-05 adds a lane-arm test and V-03 demands it.

FOURTH, A DEADLOCK I CHECKED FOR AND DID NOT FIND, recorded because a bounded wait on a lock your own
transaction later takes is a deadlock rather than a delay. `ipd_lifecycle`'s only `commit_lock` use is
`coordinator_worktree`, which acquires no lock, and the module never calls `writer_lock` or `try_acquire`.
So a waiting finalize cannot be waiting on itself. That is now F-9 with an explicit instruction not to add
such an acquisition without revisiting it.

FIFTH, THE CHANGELOG HAS TWO PENDING SECTIONS. E-06 said "the unreleased section"; `CHANGELOG.md:7` is
`## 2.0.0 (pending)` and `:74` is `## 1.3.0 (pending)`. E-06 now names 2.0.0 explicitly and V-06 checks the
placement plus the no-dashes rule (noting `grep` exits 1 on the passing case).

ON THE ONE CITATION I COULD NOT OPEN, stated rather than glossed. The run record the Concern cites
(`run-20260926T051642Z-116672`) is not readable from this lane: `.aw/records/runs` does not exist here and
`aw runs` reports "no matching runs found", because run directories are per-checkout runtime state and the
`gate_answer_record` docstring notes `<run_dir>` is gitignored. I did NOT treat that as a false citation.
Backlog `duac3v` independently records the same event line, the peer run id, the 19-second gap, the peer's
commit SHA and timestamps, and is candid that "the exact holder is NOT recorded" and that "By 05:4x the PID
was gone and the lock file is absent now". That is enough to establish the mechanism, which the code
independently confirms. Recorded as F-8 so a later reader does not chase a run directory that no longer
exists.

ON SPEC `25kzda` 5.5, WHERE THE PLAN EXPLICITLY INVITED DISAGREEMENT. It said that if `/plan-review`
disagrees that 5.5 is silent, the fix is to amend 5.5 in this plan rather than drop the re-attempt. I AGREE
WITH THE PLAN and did not amend it, and I wrote the reason into the spec-sync section so the judgement is
checkable: 5.5's never-retry entry is "overlapping ownership or lease conflict", which describes two actors
claiming the same PATHS, while this refusal is raised before any path is claimed or any journal phase is
written; and the repository already contains the governing precedent in code at the same layer for the same
class of refusal, with a reason that applies verbatim.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing | `python3 -m pytest tests/test_ipd_lifecycle_cli.py -o addopts="" -q -k lock_contention` -> `1 passed, 37 deselected in 0.25s`; the test body spawns `[sys.executable, "-c", "import time; time.sleep(60)"]`, writes its PID into the lock, then `with self.assertRaises(LC.TransactionLockError)`; no `pytestmark` in the file | **E-01'S 120-SECOND DEFAULT WOULD HANG AN EXISTING TEST AND ADD TWO MINUTES TO EVERY BARE SUITE RUN.** The test holds the lock with a real 60s live process and asserts an immediate raise. The plan declared the file and described ADDING cases, but never stated that an existing assertion must be given an explicit timeout, so an executor following it literally ships the hang. This is the most likely way the change would be noticed only after landing. | C:Low; U:Low; S:Low; F:Medium (a silently much slower suite is how a timeout regression hides); the FIX is Low | FIXED | E-01 now warns about it with the measurement and forbids "fixing" it by lowering the production default. E-05's FIRST step is to pass an explicit short `timeout` at that assertion while keeping its intent and its liveness assertion, and to confirm the stale-reclaim half still returns immediately. V-01 requires the narrowed timing pasted against the 0.25s baseline. Recorded as F-5 and in "Project conventions discovered". |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness / C. Architecture | `FINALIZE_RETRY_EXHAUSTED_STATUS: str = "failed-safely"` (`runner_shared.py:6356`); `item["status"] = FINALIZE_RETRY_EXHAUSTED_STATUS` (`:6606`); `TERMINAL_STATUS_ALIASES` `"failed-safely": "fail-gate"` with its documented read/write asymmetry | **THE PLAN NAMED THE TERMINAL STATUS BY ITS READ ALIAS, NOT THE TOKEN A WRITER WRITES.** "ends `fail-gate`" is what a READER sees; the writer writes `failed-safely`. An executor could write the literal `fail-gate` into the writer, bypassing the alias layer statusvocab established on purpose, and producing a status the write-side vocabulary does not use. | C:Low; U:Low; S:Low; F:Low | FIXED | E-03 now requires `FINALIZE_RETRY_EXHAUSTED_STATUS` (or an equally deliberate canonical token) rather than the literal, and notes E-04's `cause` field is what distinguishes the two regardless of which token a reader sees. V-03 requires a grep showing no new `fail-gate` literal in a writer. Recorded as F-6. |
| PR-003 | MEDIUM | UNDER-SCOPE | A. Correctness / B. Safety | `handle_finalize_refusal` called at `runner_shared.py:29638` (LANE arm, after the lane integration decision) and `:29694` (non-lane `self_finalize and not work_dir and integration.earned`); `driver_finalize`'s `lanetruth af7i6p` comment: "`repo` here is the LANE worktree ... `cwd=str(repo)` below keeps it that way DELIBERATELY" | **THE RE-ATTEMPT DID NOT SAY WHICH REFUSAL ARM IT RUNS UNDER, AND ONE OF THEM FINALIZES AGAINST A LANE WORKTREE.** E-03 says it "re-attempts the SAME `driver_finalize` call", but the two arms differ in exactly the argument that matters. A re-attempt that re-resolved `repo` to main would finalize against the wrong tree; one sited outside its arm could re-run the surrounding integration step. Neither is what the plan intends, and neither would be obvious from the diff. | C:Medium (two arms, one lane-shadowed); U:Low; S:Medium if the wrong tree is finalized; F:Medium; Overall:Medium for the mistake, Low for the fix | FIXED | E-03 now requires the arm to be named in the code comment, forbids re-running the integration or merge step, and requires the SAME lane `repo` argument. E-05 adds a lane-arm case and V-03 demands it be pasted, with "a re-attempt that re-runs integration, or finalizes against main instead of the lane, is a defect to fix rather than to explain". Recorded as F-7. |
| PR-004 | LOW | IN-SCOPE | G. Executability | `CHANGELOG.md:7` `## 2.0.0 (pending)`; `:74` `## 1.3.0 (pending)`; E-06 said only "the unreleased section" | **TWO PENDING SECTIONS EXIST AND E-06 NAMED NEITHER.** An entry landing under 1.3.0 would be recorded against a version this change is not part of. | C:Low; U:Low; S:Low; F:Low | FIXED | E-06 names `## 2.0.0 (pending)` with its line number and explicitly excludes 1.3.0; it also specifies the `- Fixed:` prefix and the no-em-or-en-dash rule. V-06 checks the placement and the dash grep, noting `rc=1` is the passing case. |
| PR-005 | LOW | IN-SCOPE | E. Testing / G. Executability | E-05's "show it by reverting the hunk" and V-01's "with the wait reverted"; E-05's two-process test as authored asserts only that the parent "must succeed"; `acquire_finalize_lock` called positionally at three production and three test sites, with two name assertions in `tests/test_orchestrator_retirement.py` | **THREE SMALLER GAPS IN THE VALIDATION PLAN.** (a) A revert-in-place is the only work-losing step in this plan and the obvious wrong reflex (`git stash`) would move a co-worker's uncommitted changes in a shared checkout. (b) The two-process test could pass VACUOUSLY: if the child released before the parent's first probe, the parent succeeds without ever waiting, and the test proves nothing. (c) Nothing guarded the signature, though six call sites pass the two arguments positionally and two tests assert on the function's name. | C:Low; U:Low; S:Medium-High if a stash moves a peer's work; the FIX is Low | FIXED | E-05 prescribes a throwaway detached worktree with the gitignored paths and teardown, forbids `git stash` with the reason, and requires the two-process test to assert the parent's elapsed time EXCEEDS the child's hold. E-01 pins the signature as backward compatible (keyword-only additions, no rename) with all six call sites and both name assertions named, and V-01 requires `tests/test_orchestrator_retirement.py` passing as the guard. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is spec `25kzda` 5.5 silent on a lock-contention finalize refusal, or does its never-retry list cover it? The plan explicitly invited the reviewer to amend 5.5 instead of dropping the re-attempt. | SILENT: agree with the plan, amend no spec, and RECORD the reasoning in the spec-sync section so the judgement is checkable. | (a) Amend 5.5 to name lock contention as retryable: rejected as unnecessary and as the larger change; 5.5's never-retry entry is "overlapping ownership or lease conflict", which is about two actors claiming the same PATHS, and this refusal precedes any path claim. (b) Drop the re-attempt to stay conservative: rejected, it preserves the measured 24-minute loss and contradicts the in-code precedent. (c) Leave the plan's bare assertion that 5.5 is silent: rejected, it was an unsupported claim about a spec, and the whole point of the plan's invitation was to get it adjudicated. | 5.5's never-retry wording; all three `acquire_finalize_lock` sites taking the lock immediately before `_finalize_transaction`; the journal's first write at `ipd_lifecycle.py:4416` being inside the transaction; `integrate_under_repository_lock`'s "EXPIRY DEFERS, IT DOES NOT FAIL ... Failing the lane on a lock timeout would discard a completed validation" | yes |
| D-2 | E-01's 120s default breaks an existing test. Lower the default, or fix the test? | FIX THE TEST (explicit short `timeout` at that assertion); keep the production default at 120s. | (a) Lower the production default to keep the test fast: rejected outright, that is tuning production behavior to suit a test and would reintroduce the defect (a `pre-commit` window alone measured 10.6s, and several peers can queue). (b) Mark the test `slow` so the bare suite skips it: rejected, it would hide a two-minute regression AND remove a live guard from the run that would notice it. (c) Leave it undeclared and let the executor discover it: rejected, that is how the hang ships. | The measured 0.25s current runtime; the 60s live sleeper in the test body; no `pytestmark` in the file; the 10.6s `pre-commit` measurement in backlog `duac3v` | yes |
| D-3 | The cited run record is unreadable in this checkout. Treat the Concern's measurement as unverified? | NO: accept it, corroborated by backlog `duac3v` plus the code, and RECORD the unreadability as F-8. | (a) Raise it as an evidence finding: rejected, and the plan-review contract is explicit that rejecting a citation the reviewer merely failed to re-locate is worse than under-reporting drift; the mechanism is independently confirmed in code and the backlog item carries the event line, peer run id, SHA and timestamps. (b) Ask the maintainer for the run directory: rejected, the backlog item already records that the PID is gone and the lock file absent, so nothing could be re-measured from it now. (c) Say nothing: rejected, a later reader would otherwise chase a path that does not exist. | `ls -d .aw/records/runs` -> No such file or directory; `aw runs` -> "no matching runs found"; backlog `duac3v`'s OBSERVED paragraph including its own admission that the holder is unrecorded | yes |
| D-4 | A bounded wait converts a fast failure into a slow one. Is that trade acceptable without asking the maintainer? | YES: accept it and STATE it in the gate as the risk a human is approving, with the bounds that contain it. | (a) Ask the maintainer: rejected, the repository already made this exact trade for the same class of refusal at the same layer (the integration lock waits up to 1800s and defers), so the precedent answers it; asking would spend the maintainer's time on a settled principle. (b) Use a much shorter budget to limit the slowdown: rejected, 5s is already known too short (the `pre-commit` window alone is 10.6s), which is the defect. (c) Say nothing about it: rejected, a human approving this should see that a stuck holder now costs up to 120s plus three re-attempts instead of failing at once. | `INTEGRATION_LOCK_TIMEOUT_SECONDS = 1800.0` and its docstring; the 10.6s `pre-commit` measurement; every wait and re-attempt in this design being bounded and counted | yes |
| D-5 | Could a waiting finalize deadlock against a lock its own transaction takes? | NO, verified; record it as F-9 with a forward-looking warning. | (a) Assume it cannot and say nothing: rejected, this is the failure mode that turns a bounded wait from a delay into a hang, and a future author adding a `writer_lock` acquisition inside the transaction would create it silently. (b) Add a defensive re-entrancy check: rejected as unnecessary complexity for a condition that does not exist, and `writer_lock` already has its own re-entrancy handling for its own callers. | `rg "writer_lock\|commit_lock" agent_workflows/ipd_lifecycle.py` -> one hit, the `coordinator_worktree` import at `:4414`; `coordinator_worktree` acquiring no lock | yes |

### Deferred and open

- (none DEFERRED among findings). All five findings were FIXED in place. PR-001 is `HIGH` and is FIXED, so no
  finding at or above the repository's gate threshold (no `review_findings_gate` configured in
  `.aw/config/project.json`, so the default `HIGH` applies) is left unfixed, and nothing is owed an escalated
  `- Blocking: yes` question.
- No `Reversible: no` decision was taken. D-1 and D-4 are the consequential ones; both are reversible (a spec
  amendment can still be written later, and the budget is one constant).
- The plan's single open question (OQ-01, the 120s budget) is `resolved` and `Blocking: no`, and I did not
  reopen it: the budget is evidence-based and, as its own rationale says, reversible in one constant. Its two
  Deferred entries both carry reasoned values and I overturned neither: F-4's carrier `bqz8kn` is verified to
  exist (`open`, `bug`, `Blocks-Release: next`), and a "who holds which lock" status verb is genuinely not
  needed to close this defect once E-02 names the holder in the message.

HONEST LIMITS, stated because they bound what this round proves. I read the code and ran targeted probes; I
applied NO product edit and wrote no test, so that the wait actually waits, that the classification arm is
correct, that the re-attempt preserves the lane `repo`, and that the suite stays green and FAST are all still
E-01 through E-06's work and their evidence. I did NOT run the bare suite for this plan; I ran the one
narrowed case that establishes PR-001 (`0.25s`) and read the affected test bodies, which is proportionate for
a review but is a hole rather than a clearance. I could NOT open the cited run directory (F-8), so the
original incident is corroborated from the backlog item and the code, not re-measured; the 10.6s `pre-commit`
figure underpinning the 120s budget is likewise the backlog item's measurement and not mine. Nothing I did
exercises the real composite failure (two concurrent drivers, one finalizing while the other self-commits
through a full hook run), and no test in the plan does either, which is now stated in the plan's validation
section. Finally, my PR-003 conclusion that the two arms differ only in the lane argument rests on
`handle_finalize_refusal`'s own docstring plus reading both call sites; I did not drive either arm.
