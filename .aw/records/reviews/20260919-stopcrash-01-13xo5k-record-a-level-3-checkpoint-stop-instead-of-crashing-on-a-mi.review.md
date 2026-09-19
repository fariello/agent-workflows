# Review findings: plan 13xo5k

- Subject-Id: 13xo5k
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in lane `review-sweep-run-20260919T133719Z-1618106` at HEAD `76018805`. The plan on disk is
BYTE-IDENTICAL to the sealed lane input (both `dd9519af...`) and already committed at `eff385cf`, with
`git status --porcelain` empty, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author`: `conforming`, exit 0, BEFORE any revision.

THE DIAGNOSIS IS CORRECT, THE TRACEBACK IS REAL, AND THE PLAN IS WORTH EXECUTING. I re-derived every
mechanical claim rather than trusting it, and the core ones held exactly: `runner_shared.py:11942` really
does read `stop.exit_code` off a `StopAtCheckpoint`; that class really sets only `self.observer`
(`sorted(vars(instance))` -> `['observer']`); the crash really lands between `_record_checkpoint_stop` and
`save_state`, so the stop is computed and then discarded; and `tests/test_runner_stop_level3.py` really
does assert over source text, with `grep -c exit_code` returning `0`. The plan's framing of the
consequence is also right and is the reason this is a bug rather than a nuisance: the GRACEFUL path fails
louder than the abrupt one, and a resume reads a state file that never learned the item stopped.

BUT THE PLAN'S LOAD-BEARING SCOPE BOUNDARY IS FALSE, AND CORRECTING IT DOUBLES THE FIX. The plan asserts,
in its Concern, in F-4, in its Scope line, and in a Deferred row, that the level-4 sibling `StopNowForce`
"DOES carry an `exit_code`" and that "its handler reads it correctly a dozen lines above" -- from which it
concludes level 4 is out of scope and is the working template the level-3 handler was miscopied from.
Both halves are false. `StopNowForce.__init__` sets exactly `level`, `requester`, `events_seen`,
`prior_completed_index`, `prior_completed_label`. Measured:
`sorted(vars(StopNowForce(level=4, events_seen=3)))` returns those five and nothing else, and
`hasattr(s, 'exit_code')` is `False`. So `runner_shared.py:11921`, in the `except runner_stop.StopNowForce`
branch, raises the IDENTICAL `AttributeError: 'StopNowForce' object has no attribute 'exit_code'`, which I
reproduced directly. BOTH deliberate-stop paths out of `spawn_executor` are dead, by one copied line each.

THAT IS THE MOST CONSEQUENTIAL FINDING IN THIS REVIEW (PR-001, BLOCKER) AND IT MAKES THE PLAN BETTER RATHER
THAN WORSE. Level 4 is the EMERGENCY stop, the thing an operator reaches for when level 3 is too slow, so
its failure mode is strictly worse than the one that prompted the plan: the harder you press, the more
certainly the runner crashes instead of recording `unknown_outcome`. Had the plan shipped as authored, it
would have fixed level 3, left level 4 crashing, and left a Deferred row on record asserting level 4 was
"out of scope and working" -- which is worse than silence, because the next reader would believe it. The
fix is two lines rather than one, in the same function, invisible to the same class of test, so it is one
defect with one shape and it belongs in this plan rather than a successor (D-1).

THE SHARPEST EVIDENCE THAT A GREEN SUITE PROVES NOTHING HERE is a test the plan never mentions.
`tests/test_runner_stop.py:922 test_verifier_stop` DOES drive a `StopNowForce` through `execute_item`, and
it PASSES today (verified: `1 passed`) while both handlers are broken. Its `fake_turn` raises only when
`fresh_session` or `log_suffix == "verify"`, so it reaches the VERIFY/RECONCILE handler, which is one of the
two that are genuinely correct. This matters operationally, not just as trivia: an executor who writes "a
test that raises a stop through `execute_item`" will reproduce this exact blind spot and get a green result
that proves nothing. V-03 now requires proof of WHICH handler ran (PR-005, F-6a).

I ALSO CLOSED TWO INVESTIGATIONS THE PLAN DEFERRED TO EXECUTION TIME, because both are answerable from the
repository now and leaving them open invited the wrong answer. FIRST (PR-003): the plan told the executor
to find out who reads `attempt["exit_code"]` before deleting the line, and to derive a value if someone
does. Nobody does. `grep -rn 'attempt\["exit_code"\]\|attempt\.get("exit_code")' agent_workflows/` finds
only the two WRITES this plan removes; the one `"exit_code"` READ in the package (`run_cli.py:451`) is
`rec.get("exit_code")` against an unrelated `tool_event` record and tolerates absence by construction; and
the normal success path never sets the key, so a dependent consumer would already be broken for every
successful item. E-01 is therefore a DELETION, which is a smaller and safer change than the plan budgeted
for. SECOND (PR-004): the plan pointed at `runner_stop.deliberate_stop_exit_code` as the prescribed source
for that value. That function is RUN-level: its signature takes `statuses` and it is called once per host
with `exit_code_statuses(state["queue"])`. Storing a whole-run exit code on a single attempt would be a
category error and a duplicate call, and an executor following the authored text could have "fixed" a
function that is not broken. Both are now recorded as resolved open questions (OQ-02, OQ-03) so the
reasoning survives rather than living only here.

ONE FURTHER CORRECTNESS TRAP THE PLAN WOULD HAVE WALKED INTO (PR-002). E-02 told the executor to assert
that the disposition equals `runner_stop.STOPPED_DISPOSITION`, correctly noting its value is
`'interrupted'`. That is right for level 3 and WRONG for level 4, whose constant is `FORCED_DISPOSITION ==
'unknown_outcome'`. Once level 4 is in scope, an executor reusing the level-3 assertion would either
assert a false expectation or paper over it. The difference is semantic and deliberate: level 3 stopped at
an observed boundary, level 4 cut mid-flight and the outcome is genuinely indeterminate, which is why
spec `c4gd2h` Section 4 point 4 and its A2 criterion require exactly those two words. E-02 and V-02 now
carry the per-level constants.

SMALLER FIXES. PR-006: the Deferred row for the broader source-text-coverage audit carried
`- Carrier: 13xo5k`, a SELF-REFERENCE that discharges nothing (once this plan is `executed` the obligation
sits in a terminal artifact, the precise state the carrier vocabulary exists to prevent); since filing the
backlog item would require writing outside the declared fence, which a reviewer may not do, it is now
`Carrier-Declined` with the reason and a named next step. Note the deferred work's justification got
STRONGER during review: the pattern hid the same bug twice, in two files. PR-007: `Scope-Paths` gained
`tests/test_runner_stop_level4.py`, without which E-04's level-4 comment would be an undeclared edit.
PR-008: the plan cited no suite baseline; measured here as `8287 passed, 3 skipped, 2 xfailed` with ZERO
failures, recorded as a reference to RE-MEASURE rather than trust. PR-009: the gate omitted the scope
fence, the honesty rule, and the staged-set re-verification, and needed an instruction to leave the tree
clean after each destructive mutation check, since committing a mutation would ship the very bug being
removed.

RIGHT-SIZING ASSESSED AND THE PLAN REMAINS CORRECTLY SIZED even after widening. Four E-items in two groups;
the code change is two one-line deletions; the bulk is E-03's coverage, which is the durable deliverable.
E-01 simultaneously widened (a second handler) and SHRANK (its investigation is now answered), so no split
is warranted. I considered splitting level 4 into its own child and rejected it (D-1): it is the same line,
in the same function, with the same root cause and the same missing test class, and splitting would leave
the emergency stop broken behind a plan asserting it was fine.

WHAT I DID NOT FIND, stated so the absence is a result. No security surface: the change deletes two
dictionary writes and adds tests; it grants nothing and crosses no trust boundary. No data-migration or
compatibility exposure, since the key being removed is provably unread and absent on the success path
already. No over-scope: every E-item traces to the crash or to the coverage gap that hid it. The plan's
`- Work-Kind: bug`, `- Priority: high` and `- Blocks-Release: next` are all correct and consistent with the
repo's "every live bug gates the next release" rule; I confirmed the gate resolves (`next` -> the single
`planned` release record).

`aw ipd lint --phase author`: `conforming` before and after revision. `--phase review-finalize`:
`conforming`. No source or test file was modified by this review; the only files touched are the plan and
this record.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | A. Correctness; D. Anti-regression | `python3 -c "from agent_workflows import runner_stop as rs; s=rs.StopNowForce(level=4, events_seen=3); print(sorted(vars(s)), hasattr(s,'exit_code'))"` -> `['events_seen','level','prior_completed_index','prior_completed_label','requester'] False`; `runner_shared.py:11921`; `runner_stop.StopNowForce.__init__` | **THE LEVEL-4 HANDLER IS BROKEN THE SAME WAY AND THE PLAN DECLARED IT OUT OF SCOPE AS "WORKING".** The plan's Concern, F-4, Scope line and a Deferred row all assert `StopNowForce` carries an `exit_code` read "correctly"; it carries no such attribute, so `:11921` raises the identical `AttributeError`. Level 4 is the EMERGENCY stop, so shipping the plan as authored would have left the worse failure mode live behind a written claim that it was fine. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | Level 4 moved IN scope across Concern, Goal, Scope, F-4 (rewritten, severity raised to BLOCKER), E-01, E-02, E-03, E-04, V-01..V-04, the Deferred row (retracted), and `Scope-Paths`. Fix is now two lines. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness; E. Testing | measured `STOPPED_DISPOSITION == 'interrupted'`, `FORCED_DISPOSITION == 'unknown_outcome'`; spec `c4gd2h` Section 4 point 4 and criterion A2 | E-02/V-02 asserted ONE disposition constant. With level 4 in scope that assertion is wrong for it: the two levels deliberately record different words, because level 3 stopped at an observed boundary while level 4's outcome is indeterminate. Reusing the level-3 constant would assert a false expectation or hide a real regression. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 and V-02 now require the level-correct constant per level, state both values, and explicitly fail a V-02 that shows the same disposition for both. |
| PR-003 | MEDIUM | IN-SCOPE | G. Executability; F. KISS | `grep -rn 'attempt\["exit_code"\]\|attempt\.get("exit_code")' agent_workflows/` -> only the two writes; `run_cli.py:451` (`rec.get("exit_code")`, a `tool_event` record) | E-01 deferred "who reads `attempt['exit_code']`?" to execution time and told the executor to derive a value if anyone does. The repository answers it: NOBODY reads it, and the sole `"exit_code"` read is `.get()` on an unrelated structure. Leaving it open invited inventing a value defensively. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Answer recorded as F-9 and OQ-03 (resolved); E-01 is now a DELETION of both lines, with V-01 still requiring the executor to RE-RUN the search rather than cite the plan. |
| PR-004 | MEDIUM | OVER-SCOPE | C. Architecture | `inspect.signature(runner_stop.deliberate_stop_exit_code)` -> `(statuses, *, success_states, stopped)`; call sites `oc_runipd.py:6901`, `agy_runipd.py:3648` with `exit_code_statuses(state["queue"])` | E-01 and F-7 pointed at `deliberate_stop_exit_code` as the source for an ATTEMPT-level value. It is a RUN-level function, already correctly called once per host and not broken. Following the authored text risked a category error (a run exit code stored on one attempt) or an executor "fixing" working code. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now forbids it and says why; F-7 rewritten; OQ-02 added and resolved, ruling the run-level exit code out of scope. |
| PR-005 | HIGH | UNDER-SCOPE | E. Testing and verification | `tests/test_runner_stop.py:922-1010`; `python3 -m pytest tests/test_runner_stop.py -o addopts="" -k test_verifier_stop -q` -> `1 passed` with both handlers broken | **AN EXISTING TEST ALREADY DRIVES A STOP THROUGH `execute_item` AND PASSES, REACHING ONLY THE CORRECT HANDLER.** The plan never mentions it, so an executor writing "a test that raises a stop through `execute_item`" would reproduce the blind spot and get a green result proving nothing. Its `fake_turn` raises only on `fresh_session`/`log_suffix == "verify"`, i.e. the verify/reconcile path. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | Added F-6a and a Step-0 convention; E-03 now requires the test to reach the FIRST turn and V-03 requires PROOF of which handler ran (return versus re-raise), plus an INDEPENDENT mutation check per level since one mutation cannot validate the other level's test. |
| PR-006 | MEDIUM | IN-SCOPE | F. Honest limits; project carrier rule | the Deferred row's authored `- Carrier: 13xo5k`; `ipd_schema` carrier vocabulary ("a note in an executed IPD is the same as not writing it anywhere") | The broader-audit row named THIS PLAN as its own carrier. A self-reference discharges nothing: this is the artifact deferring the work, and once it reaches `executed` the obligation sits in a terminal plan, exactly the state the carrier fields exist to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Converted to `Carrier-Declined` with the reason (filing a backlog item requires writing outside the declared fence, which a reviewer may not do) and a named next step (`aw backlog new`, then replace with `- Carrier: <id6>`). Its justification also strengthened: the pattern hid the same bug twice. |
| PR-007 | MEDIUM | UNDER-SCOPE | G. Executability (scope fence) | authored `- Scope-Paths:`; E-04's new level-4 obligation | With level 4 in scope, E-04 must annotate `tests/test_runner_stop_level4.py`, which the fence did not declare. An undeclared edit would surface at finalize as a scope violation needing a `--scope-reason`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `tests/test_runner_stop_level4.py` added to `- Scope-Paths:`; the scope check records why the third path is the fence catching up with the defect's extent rather than creep. |
| PR-008 | MEDIUM | UNDER-SCOPE | E. Testing | bare `python3 -m pytest` in this lane at `76018805` -> `8287 passed, 3 skipped, 2 xfailed in 96.11s` | The validation section required a baseline but recorded none, so an executor had no reference and any post-change failure count would be unanchored. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline pasted with its HEAD, marked as a reference to RE-MEASURE rather than trust, with the zero-failure end state and the no-allowance rule stated. |
| PR-009 | MEDIUM | UNDER-SCOPE | G. Executability (execution contract) | the authored gate; `.aw/system/workflows/templates/plans-README.md` contract items 1-5 | The gate carried the commit and honesty rules but omitted the resolved-questions statement and the SCOPE FENCE, and said nothing about the tree state after the deliberately destructive mutation checks. Committing a re-introduced mutation would ship the exact bug this plan removes. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate now states all three questions resolved and non-blocking, carries a declaration-style fence with `--scope-reason`/`--scope-ack` and genuine stop conditions (concurrent edits to a very high-traffic file), and requires verifying the mutation is reverted before any commit. Lifecycle wording was already correct (`aw ipd finalize`, no hand-rolled `git mv`) and was left alone. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The level-4 handler is broken too. Widen this plan, or file the level-4 fix as a separate item? | WIDEN this plan to cover both levels. | (a) File a separate child/backlog item for level 4, rejected because it is the SAME copied line in the SAME function with the SAME root cause and the SAME missing test class, so splitting doubles the ceremony for no isolation benefit and, worse, would leave the EMERGENCY stop broken behind a Deferred row on record asserting it was "out of scope and working" -- a false claim a later reader would trust. (b) Leave level 4 alone and only correct the false claim, rejected because the plan would then knowingly ship a fix for the lesser failure mode while documenting the greater one as fine. | Measured `hasattr(StopNowForce(...), 'exit_code')` -> `False`; `runner_shared.py:11921` and `:11942` are 21 lines apart in one function; both test files carry the identical source-text-only gap; `plan-review.md` 2.4 (fix in the owning plan) | yes |
| D-2 | E-01 deferred the `attempt["exit_code"]` consumer investigation to execution time. Resolve it now or leave it? | RESOLVE it now from repository evidence and record it as F-9 plus resolved OQ-03, making E-01 a deletion. | Leaving it as executor work, rejected because the authored instruction ("if it is required, derive it") biases toward inventing a value under uncertainty, and the evidence is unambiguous and cheap to obtain: zero readers package-wide, and the one `"exit_code"` read is `.get()` on an unrelated record type. V-01 still re-runs the search, so the executor is not asked to trust me. | `grep -rn 'attempt\["exit_code"\]\|attempt\.get("exit_code")' agent_workflows/` -> only the 2 writes; `run_cli.py:449-452`; the success path never sets the key | yes |
| D-3 | The broader source-text-coverage audit needs a durable carrier and the plan self-referenced. Do I file the backlog item? | NO. Convert to `Carrier-Declined` with the reason and a named next step. | (a) Keep `- Carrier: 13xo5k`, rejected as a self-reference that discharges nothing and lands the obligation in a terminal artifact. (b) File the backlog item myself with `aw backlog new`, rejected because it writes to `.aw/records/backlog/`, outside this plan's declared `Scope-Paths`, and a reviewer creating new tracked work is an expansion of the reviewed change rather than a repair of it. | `ipd_schema` carrier vocabulary comment; the plan's `- Scope-Paths:`; `plan-review.md` 2.4 (surgical edits, do not add unsupported scope) | yes |
| D-4 | Is `deliberate_stop_exit_code` itself broken, given the plan pointed at it? | NO, and record that as resolved OQ-02 to stop an executor "fixing" it. | Treating it as in scope or as the value source, rejected on its measured signature and call sites: it consumes the whole queue, is called once per host, and implements the spec `c4gd2h` A1/A4 `queued`-ignoring rule correctly. | `inspect.signature`; `oc_runipd.py:6901`; `agy_runipd.py:3648`; its docstring | yes |
