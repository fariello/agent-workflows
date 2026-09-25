# Review findings: plan 87jnym

- Subject-Id: 87jnym
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `intrecon`, the sole child, graduated from backlog `2415x6`
(`Blocks-Release: next`, `Work-Kind: bug`), also covering `tsfk8a` and its duplicate `e17a2e`.
Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE
semantic review, and `--phase review-finalize` conforms after the revisions, so nothing below is
structural. The plan file was committed and byte-identical to the lane input, so no pre-review
snapshot was needed. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check and its
bounded repair loop do not apply.

DISCLOSURE: a different model of the same family authored this plan, so treat this as near-self-review.
Its value rests on RE-MEASURING the claims against the tree rather than on reading them, and that is
exactly what produced the one serious finding: PR-001 came from running the plan's OWN proposed fix in
simulation against a real repository, on the one input the plan never tested (an agent that COMMITTED
its work). Reading the fix would not have found it; the fix is correct on the two cases the plan names.

WHAT HOLDS, AND IT IS THE SUBSTANCE OF THE PLAN. Every headline claim reproduces independently at HEAD
`bacbe7b0`. F-1: `grep -rn reconcile_item_on_interrupt agent_workflows/` returns the `def` plus one
`render_stream` DOCSTRING mention and nothing else, so the function has zero callers; the pre-dedup
call sites exist at `70a2059f^` in both drivers, with byte-identical argument lists. F-2 reproduced
BEHAVIORALLY by driving the real `oc_runipd.execute_item` with a spawn raising
`KeyboardInterrupt("clean-up-and-terminate")`: the interrupt propagates, the item ends `status running`,
`events.jsonl` holds only `['ipd-started', 'tool-identity-verified', 'suite-baseline-unavailable']`, and
`render_stream._interrupt_reason_of(item)` returns `None` (the viewer consumer the backlog names renders
nothing). F-4 reproduced on all three no-worktree inputs, including the CLEAN repo, which matters: the
`AttributeError` fires BEFORE the branch, so today the arm is 100 percent broken and not merely broken
on the dirty path. F-5 confirmed at the source: `execute_item_core` writes `{"number": attempt_no, ...}`
while the pop guard reads `.get("attempt")`, and `git show 19313eed^:tests/test_interrupt_menu.py`
shows the deleted fixture built `{"attempt": 1, ...}`, which is exactly how the defect hid. F-6
confirmed: both covering test files are gone and `grep -ln 'StopNowForce\|StopAtCheckpoint' tests/*.py`
matches no file. F-7 confirmed by MRO: none of the three sibling exception classes subclasses
`KeyboardInterrupt`, so no double-record is possible. The spec-sync `N/A` is correct: `grep -rln` over
`.aw/records/specs/` finds no spec naming `reconcile_item_on_interrupt`, `ipd-interrupted`, or
`ipd-cleaned-up-no-changes`, and the behavior E-03 restores is what `c4gd2h` R3/R18 already require, so
an amendment would change no contract (D-3).

WHAT DOES NOT HOLD. One finding, and it is in the plan's own fix rather than in HEAD.

```text
review probe, throwaway repo, work_dir=None (the arm E-01 fixes)

  HEAD behavior, all three inputs                     AttributeError 'tuple' object has no attribute 'strip'
    dirty repo                                        AttributeError
    clean repo                                        AttributeError     <- so the arm is 100% broken today
    non-git directory                                 AttributeError

  E-01-AS-SPECIFIED, simulated (unpack + rc!=0 -> True), agent COMMITTED its work then interrupted
    _run_git(repo, ['status','--porcelain'])           (0, '', '')
    E-01 holds_work                                   False              <- PR-001
    attempt['starting_head'] != HEAD                   True
    head-aware predicate holds_work                    True
    -> E-01 alone routes a COMMITTED turn to the DESTRUCTIVE no-changes arm:
       begin receipt unlinked, item -> queued, attempt popped,
       'had no files changed; cleaned up so it can run fresh'

  F-2 reproduced, real oc_runipd.execute_item, spawn raises KeyboardInterrupt
    clean-up-and-terminate / dirty     propagated, status running, events=['ipd-started','tool-identity-verified','suite-baseline-unavailable']
    clean-up-and-terminate / clean     propagated, status running, events=['ipd-started','suite-baseline-unavailable']
    just-terminate-no-cleanup          propagated, status running, events=['ipd-started','suite-baseline-unavailable']
    render_stream._interrupt_reason_of(item)           None  (all three)

  MRO check (F-7)                       StopNowForce / StopAtCheckpoint / StallTimeout: KeyboardInterrupt subclass? False, False, False
  deleted coverage (F-6)                tests/test_runner_stop_level3.py, level4.py: absent
                                        grep -ln 'StopNowForce|StopAtCheckpoint' tests/*.py -> no file
  carrier gate before revision          check.ipd-uncarried-obligation: 1 (OQ-02 open, no carrier)
  carrier gate after revision           0
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A (correctness and data integrity) / D (anti-regression) | plan `E-01` as authored; `runner_shared.reconcile_item_on_interrupt` `lane is None` arm and the no-changes branch that follows it (`ipd_lifecycle.receipt_path_for` unlink, `item["status"] = "queued"`, `attempts.pop()`); `runner_shared.turn_attempted_nothing` docstring conditions 2 and 3; `AGENTS.md` execution contract ("commit ONLY files you changed ... through `aw commit`") | E-01 AS AUTHORED REPLACES A LOUD CRASH WITH A SILENT DESTRUCTIVE CLEANUP, ON THE EXPECTED INPUT. `git status --porcelain` is EMPTY after a commit, so the corrected predicate `bool(status_out.strip())` scores a non-isolated turn that did real work AND COMMITTED IT as holding NOTHING, and routes it to the no-changes arm, which unlinks the begin receipt, resets the item to `queued` and pops the attempt. MEASURED: after one `git commit`, `_run_git(repo, ["status", "--porcelain"])` -> `(0, '', '')` and E-01's `holds_work` -> `False`, while HEAD has moved off `attempt["starting_head"]`. This is not an exotic input: the repository's own execution contract OBLIGES an executing agent to commit its work, so committed-then-interrupted is the NORMAL shape of the path this arm serves. The consequence is worse than the defect E-01 removes, because an `AttributeError` fails loudly and leaves the state alone, whereas this destroys the receipt that records the base the work was cut from and makes the agent's commit unattributable to any attempt, then prints "cleaned up so it can run fresh" to an operator whose tree is not fresh. The module ALREADY states the correct rule and the plan did not consult it: `turn_attempted_nothing`'s docstring records that on a SHARED-TREE turn `starting_head == ending_head` is the load-bearing "no commit beyond the base" condition, and warns against using `worktree_lease.holds_work` as the commit test. The plan's E-04 could not have caught this: its clean-repo case commits nothing, so both the broken and the correct predicate return the same answer. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | New E-07 (assigned by `aw ipd sync`, with matching V-07) counts a moved HEAD as work in the `lane is None` arm only, comparing `git rev-parse HEAD` to `attempt["starting_head"]`, and states the fail-safe rule for an ABSENT or unreadable `starting_head` (fall back to the dirty-tree reading, add no claim). E-01's expected outcome now says "a clean repo WITH NO NEW COMMIT". E-04 gained case (5) (clean tree, moved HEAD: preserve branch, receipt SURVIVES, attempt NOT popped) and case (6) (absent `starting_head`: no-changes arm still taken), and case (2) must now also assert the receipt was UNLINKED so the two arms are discriminated by their destructive effect rather than only by `item["status"]`. `Required tests / validation` gained the E-07 mutation run, whose discriminating property is that case (5) fails while case (2) still passes. F-9 added to the plan's Findings table; the Concern records the measurement; `Proposed changes` and the `Scope check` under-scope note record why E-07 rides here (OQ-03). |
| PR-002 | MEDIUM | IN-SCOPE | G (executability) / plan lifecycle rule | plan `OQ-02` as authored (`- Status: open`, `- Owner: maintainer`); `check_engine.evaluate_durable_carrier` on the plan -> 1 drift (`check.ipd-uncarried-obligation`, severity `error`) | AN OPEN QUESTION THE REPOSITORY COULD ANSWER WAS LEFT FOR THE MAINTAINER, AND IT TRIPPED A FAIL-CLOSED GATE. OQ-02 asked whether the attempt-pop fix should ride in this plan, stated its own default as YES, and still left `- Status: open` with `- Owner: maintainer` and no carrier field. Two costs. FIRST, the workflow's rule is to resolve from authoritative evidence rather than ask, and the evidence is decisive: the arm is unreachable today and becomes reachable through E-03 (so E-02 is part of making the rewired path correct, not an independent change), and leaving it broken makes `attempt_no = len(item.get("attempts", [])) + 1` compute 2 for a turn the runner just declared never-run, so the "run fresh" contract the arm exists to deliver is not met. SECOND, a live OQ carrying no `Carrier`/`Carrier-Evidence`/`Carrier-Declined` field is an ERROR-severity `aw check` finding (measured: 1 drift before the revision), so the plan would have shipped a red consistency check. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 resolved YES from repository evidence, with the three facts that settle it and an explicit note that the scope and priority judgement remains the maintainer's at approval (decision D-1); `- Carrier-Declined:` added. New OQ-03 records the parallel decision for E-07 (D-2), likewise resolved with a carrier-declined reason. Re-measured: `evaluate_durable_carrier` now returns 0 drifts. |
| PR-003 | MEDIUM | UNDER-SCOPE | G (executability) / 2026-09-01 maintainer scope-fence ruling | plan `## Approval and execution gate`, as authored (one paragraph ending "STOP and report if inserting the clause appears to require editing a sibling deliberate-stop handler, either host driver, or `runner_stop`") | THE GATE CARRIED THE STOP WORDING THE WORKFLOW EXPLICITLY SAYS TO FLAG, AND WAS MISSING THE REST OF THE CONTRACT. It had the commit discipline, the honesty rule and a correctly conditional lifecycle transition, but it framed a SCOPE question as a stop condition. Per the 2026-09-01 ruling a fence is a DECLARATION so the runner can reconcile afterwards and MUST NOT instruct a stop over scope; the correct requirement is that an out-of-scope edit be made and then JUSTIFIED, which `aw ipd finalize` already enforces via `--scope-reason`/`--scope-ack`. That wording propagated into 224 executed plans and contradicts the work done to stop `aw oc run` stranding unfinished turns. The gate also never said WHAT A HUMAN IS APPROVING, which for a change to the interrupt control flow of BOTH runner hosts is the costly omission: the diff is one `except` clause plus three lines in one function, and the blast radius is every interrupted item on every non-isolated run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten keeping `Size assessment: standard`: a declaration-style scope fence naming the out-of-scope surface and routing any excess to finalize-time justification; the hard-MUST honesty rule restated as a contract violation rather than a shortcut; a statement that every open question is resolved and the maintainer's remaining decision is approval itself; and the two GENUINE stop conditions kept and relabelled (the insertion seam's symbols absent, or an unresolvable concurrent edit), which the same ruling preserves. |
| PR-004 | LOW | IN-SCOPE | G (executability) | plan `E-06` as authored ("in particular in the existing `test_runner_stop_level3.py`/`test_runner_stop_level4.py` modules if present"); `ls` both -> "No such file or directory"; `grep -ln 'StopNowForce\|StopAtCheckpoint' tests/*.py` -> no match | E-06 POINTED THE EXECUTOR AT TWO FILES THAT DO NOT EXIST, hedged with "if present". They were deleted by the same trim commit `19313eed` that removed this defect's own coverage, a fact the plan states correctly in F-6 about OTHER files and then contradicts here. Minor, but it is exactly the drifted-citation class the plan's own conventions section warns about, and an executor who takes the hedge seriously spends a turn looking for them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now names `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py` and `tests/test_runner_shared.py`, and records the measurement that the two level files do not exist and that no test drives a deliberate stop through `execute_item_core`, so their absence is not mistaken for a failed run. F-10 added to the plan's Findings table. |
| PR-005 | LOW | IN-SCOPE | C (architecture and operability) | plan `Scope check`, as authored; plan `afpmdu` (`liftaudit`, `- Status: reviewed`) `- Scope-Paths:` and its E-02 editing the same executor-spawn `try`; plan `zrvtm2` (`intrmeta`, `- Item-Dependencies: executed:87jnym`) E-02 inserting into the `except KeyboardInterrupt` handler this plan adds | THE PLAN NAMED ONE CONCURRENT EDITOR AND MISSED A SECOND, AND UNDERSTATED THE FIRST. Its under-scope note said only "if `ccu3k7`'s audit lands edits ... first, re-read that `try`". Measured, `ccu3k7` has GRADUATED into plan `afpmdu`, which is `reviewed`, declares the same file, and rewrites the two sibling handlers on the very `try` E-03 inserts into; and plan `zrvtm2` declares a dependency ON THIS PLAN and inserts a call INTO the handler E-03 adds. Neither is a blocker (the runner isolates each item in its own worktree and merges through the revalidation gate, and `zrvtm2` depends on this plan rather than the reverse), so the correct fix is to record the relationship accurately, NOT to warn about file overlap as a runtime hazard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The `Scope check` under-scope bullet now names both plans with their statuses and their exact overlapping edits, states plainly that neither blocks this plan and why (worktree isolation plus the merge gate; `zrvtm2`'s dependency direction), and reduces the executor's obligation to the one thing that matters: locate the insertion point by its sibling clauses, never by a line number, and re-read the `try` if `afpmdu` landed first. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-02 (left `open`, owner `maintainer`): should the attempt-pop key fix (F-5, E-02) ride in this plan? | YES, resolved from repository evidence rather than asked. | (a) Defer E-02 to its own plan and drop the attempts assertion, as the plan offered. Rejected: the arm is unreachable today and becomes reachable through E-03, so a deferral ships a rewired path whose cleanup arm silently fails its own contract, and E-04's clean-repo case would have to ASSERT the broken behavior, which the rubric's anti-regression rule forbids (do not freeze accidental behavior policy says to replace). (b) Ask the maintainer. Rejected: the workflow says not to ask what the repository answers, and a live OQ with no carrier is additionally an ERROR-severity `aw check` finding. | `execute_item_core` writes the attempt record as `{"number": attempt_no, ...}` while the pop guard reads `.get("attempt")`; `attempt_no = len(item.get("attempts", [])) + 1` in the same function, so a surviving attempt makes the next dispatch compute 2 for a turn just declared never-run; the function's own docstring promises "removes uncompleted attempt so next time aw run runs it executes as if it never ran before". `git show 19313eed^:tests/test_interrupt_menu.py` shows the deleted fixture used `"attempt": 1`, which is why it hid. | yes |
| D-2 | PR-001: must E-07 (a commit counts as work) ride in this plan, or can it follow separately? | Ride in this plan, as E-07 with its own V-07 and its own mutation run. | Splitting it into a successor plan. Rejected on sequencing, not on size: the successor would have to land BEFORE this one to avoid a window in which a committed interrupted non-isolated turn loses its begin receipt and its attempt, which inverts the dependency and buys nothing. The defect is introduced BY E-01, so the two are one change. | Measured: after `git commit`, `_run_git(repo, ["status","--porcelain"])` -> `(0, '', '')`, so E-01's predicate returns `False` while `attempt["starting_head"] != HEAD`. `runner_shared.turn_attempted_nothing`'s docstring independently records that on a shared-tree turn `starting_head == ending_head` is the load-bearing no-commit condition, and warns against `worktree_lease.holds_work` as the commit test. `AGENTS.md` obliges an executing agent to commit its work, so the committed case is the expected one. | yes |
| D-3 | Does this plan need a spec amendment (it restores control flow in the interrupt path, which spec `c4gd2h` governs)? | No. The plan's `N/A` is correct and is kept; no `.spec.md` enters `- Scope-Paths:`. | Amending `c4gd2h`. Rejected: the spec already REQUIRES the behavior being restored, so an amendment would change no contract; and amending an `implementing` spec to describe a bug fix that brings code back into conformance would misrepresent the contract as having changed. | `grep -rln` over `.aw/records/specs/` finds no spec naming `reconcile_item_on_interrupt`, `ipd-interrupted`, or `ipd-cleaned-up-no-changes`. `c4gd2h` R3 (every item terminal or explicitly marked interrupted with its level and certainty) and R18 (an interrupted item records level, certainty, observed git state, and what a resume must do first) are what today's code violates by leaving the item `running`; E-03 restores conformance. R12's own docstring consumers (`install_stop_triggers`, `runner_stop.install_stop_signal_handlers`) already DESCRIBE the restored behavior and become true again. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent 87jnym -> {"outcome":"clean","exit":0,"findings":0}
aw ipd sync --apply                        87jnym -> assigned E-07; watermark advanced (06 -> 07)
aw ipd lint --phase review-finalize --agent 87jnym -> {"outcome":"clean","exit":0,"findings":0}   (after revisions)

HEAD at review                                  bacbe7b0  (plan authored against 877545fc)
lane input vs pending/ copy                     byte-identical -> no pre-review snapshot needed
plan Kind                                       child -> IPD-S407 orchestrator row check not applicable

F-1 REPRODUCED  grep -rn reconcile_item_on_interrupt agent_workflows/  -> def + one render_stream DOCSTRING mention
F-2 REPRODUCED  real oc_runipd.execute_item, spawn raises KeyboardInterrupt (3 messages/tree states)
                  every case: propagated, status running, no ipd-interrupted, _interrupt_reason_of -> None
F-4 REPRODUCED  work_dir=None, all three inputs -> AttributeError (INCLUDING the clean repo)
F-5 CONFIRMED   execute_item_core writes {"number": attempt_no}; pop guard reads .get("attempt")
                  19313eed^:tests/test_interrupt_menu.py fixture built {"attempt": 1}
F-6 CONFIRMED   tests/test_runner_stop_level3.py, level4.py absent; no test names StopNowForce/StopAtCheckpoint
F-7 CONFIRMED   StopNowForce / StopAtCheckpoint / StallTimeout are KeyboardInterrupt subclasses: False, False, False
spec sync N/A CONFIRMED  no .spec.md names reconcile_item_on_interrupt / ipd-interrupted / ipd-cleaned-up-no-changes

PR-001 (the one that required the probe rather than reading)
  committed-work case, E-01-as-specified simulated
    _run_git(['status','--porcelain'])           (0, '', '')
    E-01 holds_work                              False        <- routes to the DESTRUCTIVE arm
    starting_head != HEAD                        True
    head-aware holds_work                        True

carrier gate  check.ipd-uncarried-obligation   before: 1 (OQ-02 live, no carrier)   after: 0
```

### Verdict and readiness

Verdict `APPROVE WITH REVISIONS APPLIED`. All five findings `FIXED`; no finding is `OPEN`, `DEFERRED`
or `REPLAN`, so no escalation to a `- Blocking: yes` question is required and none was added. Every
open question in the plan is `resolved` and carries a carrier field. Readiness
`GO - PENDING HUMAN APPROVAL`: the plan is `reviewed`, no BLOCKER or HIGH is left unfixed, and the only
remaining step is the maintainer's sign-off, which a review may not grant.
