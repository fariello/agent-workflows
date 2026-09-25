# Review findings: plan afpmdu

- Subject-Id: afpmdu
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `liftaudit`, the sole child, graduated from backlog `ccu3k7`
(`Blocks-Release: next`, `Work-Kind: bug`). Structural preflight `aw ipd lint --phase author --agent`
reported `conforming` (exit 0) BEFORE semantic review, and `--phase review-finalize` conforms after the
revisions, so nothing below is structural. The plan file was committed and unchanged (byte-identical to
the lane input), so no pre-review snapshot was needed.

DISCLOSURE: a different model of the same family authored this plan, so treat this as near-self-review.
Its value rests on RE-MEASURING the claims against the tree rather than on reading them, and that is
what produced all three serious findings: PR-001 came from running the plan's own proposed guard
against the tree in simulation, PR-002 from testing the status the lift writes against the coherence
predicate that reads it, and PR-003 from classifying every hit the plan's own `grep` instruction returns.

WHAT HOLDS, AND IT IS THE SUBSTANCE OF THE PLAN. Both headline defects reproduce EXACTLY as authored,
re-measured independently at HEAD `8e74dcac`. F-1: driving each host's real `run_queue` over two queued
approved plans with the launcher replaced by a fake that raises a deliberate stop yields, on all four
host/level combinations, `dispatched=['qa0001', 'qa0002']` - the second IPD is dispatched after an
operator asked the run to stop. F-2: calling `_record_forced_stop` without `git_status_fn` returns
`git_state` = `<unobserved: git_status() missing 1 required keyword-only argument: 'run_checked'>`.
The plan's correction of `ccu3k7` is also right and is the kind of honesty that makes a plan
trustworthy: the run exit code is NOT a discriminator (`deliberate_stop_exit_code(['interrupted',
'queued'], stopped=True)` is `1`, so the fixed run exits 1 too), and the plan says so rather than
claiming a cleaner win. F-12 is verified: `grep -ln 'StopNowForce\|StopAtCheckpoint' tests/*.py`
returns nothing, so no test in the tree drives a deliberate stop, which is exactly why a green suite
never saw F-1. The pre-lift bodies confirm the intended behavior (`70a2059f^:oc_runipd.py`,
`execute_item`: `item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` then `raise`), the
surviving verify-path handler pair in `execute_item_core` still does exactly that, and E-01's reuse
premise checks out (`runner_fork_scan.normalize`/`top_level_defs`/`free_names`/`is_pure_delegation` all
import cleanly by path with no module-level side effects). All four deferrals name live carriers that
exist (`zt2b16`, `2415x6`, `tm5vnx`, and plans `cdxcbh`/`87jnym`).

WHAT DOES NOT HOLD. Three things, each found by measuring rather than reading, and the first is a
self-contradiction that would have failed the plan at its own last step.

```text
arity scan over runner_shared top-level defs, HEAD 8e74dcac
  MISSING _record_forced_stop  -> git_status(...)  line 25058: missing ['run_checked']    <- F-2, fixed by E-03
  MISSING route_recovery_turn  -> save_state(...)  line 24928: missing ['write_report']   <- F-4, DEFERRED to zt2b16
  arity violations: 2

same scan with E-03 SIMULATED in memory (git_status_fn made required, fallback call removed)
  MISSING route_recovery_turn  -> save_state(...): missing ['write_report']
  arity violations: 1        <- so E-05's authored "arity violations: 0" was UNREACHABLE

runner_shutdown.KNOWN_ITEM_STATUSES
  'unknown_outcome' in KNOWN_ITEM_STATUSES                      False
  observe_ledger([unknown_outcome, queued])  -> (False, 'items in an undefined state: qa0001=unknown_outcome')
  observe_ledger([interrupted,      queued]) -> (True,  '2 item(s), all in a defined state')

_record_forced_stop delegation, per host
  oc/agy _record_checkpoint_stop   one-line: return runner_shared._record_checkpoint_stop(..., git_status_fn=git_status)
  oc/agy _record_forced_stop       FULL SECOND COPY of the body, calling its own bound git_status(repo)
  execute_item_core rebinding set  23 names; _record_forced_stop is NOT among them -> host copies UNREACHABLE

behavioral probe, real run_queue, two queued approved plans, launcher raises the stop
  RESULT oc_runipd  level 3: dispatched=['qa0001', 'qa0002'] rc=1 statuses=[('qa0001','interrupted'),     ('qa0002','interrupted')]
  RESULT oc_runipd  level 4: dispatched=['qa0001', 'qa0002'] rc=1 statuses=[('qa0001','unknown_outcome'), ('qa0002','unknown_outcome')]
  RESULT agy_runipd level 3: dispatched=['qa0001', 'qa0002'] rc=1 statuses=[('qa0001','interrupted'),     ('qa0002','interrupted')]
  RESULT agy_runipd level 4: dispatched=['qa0001', 'qa0002'] rc=1 statuses=[('qa0001','unknown_outcome'), ('qa0002','unknown_outcome')]
  level-4 captured stdout+stderr contains 'STOPPED'            False
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | E (verification) / A (correctness) | plan `E-05` as authored vs plan `F-4` and its `Deferred / out of scope` entry; `runner_shared.route_recovery_turn` calling `save_state(run_dir, state)`; `runner_shared.save_state` requiring keyword-only `write_report` | THE PLAN'S OWN GUARD WOULD HAVE BEEN RED ON ARRIVAL, ON A DEFECT THE SAME PLAN DEFERS. E-05 asked for a guard asserting `arity violations: 0` over every `runner_shared` top-level def. But F-4 DEFERS `route_recovery_turn -> save_state` missing `write_report` to carrier `zt2b16`, and that call is in exactly the resolved-signature class the arity check reports. Measured: 2 violations at HEAD, and 1 remaining after simulating E-03's fix. So E-05 as written could not pass, and the executor reaching it would face a choice the plan does not authorize: fix a deferral that belongs to another carrier and is entangled with `zt2b16`'s classifier, weaken the guard ad hoc, or stall at the final item having already landed E-02 and E-03. This is the worst failure shape for a plan (a contradiction that surfaces only at the last step, after the risky edits are committed) and it is invisible to the structural linter, which checks no semantic claim. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now asserts set EQUALITY against an EXACT one-entry allowlist (`route_recovery_turn -> save_state missing ['write_report']`), names `zt2b16` as that entry's carrier in the assertion message, and explicitly forbids a count-based or subset assertion (which would silently absorb a NEW defect of the very class the guard exists to catch). E-01's and E-03's expected outcomes now state `arity violations: 2` then `1` with both entries named; V-01 and V-03 require the full list pasted and a THIRD entry reported rather than absorbed; the `Deferred` entry and `Scope check` under-scope note record the consequence and say the allowlist should be emptied when `zt2b16` lands. F-13 added. |
| PR-002 | HIGH | IN-SCOPE | D (anti-regression / domain invariants) | `runner_shutdown.KNOWN_ITEM_STATUSES`; `runner_shutdown.observe_ledger`; the status-representation design note above `runner_stop.FORCED_DISPOSITION`; spec `c4gd2h` R3 | F-1 IS AN INVARIANT VIOLATION, NOT ONLY A COST LEAK, AND THE PLAN UNDERSTATED IT. The plan described the level-4 harm as a wrong label ("`unknown_outcome` is not `interrupted`, so `requeue_interrupted` skips it"). Measured, it is worse on two counts. FIRST, `unknown_outcome` is NOT in `runner_shutdown.KNOWN_ITEM_STATUSES`, so spec R3's coherence observation REFUSES the ledger the shipped code writes: `observe_ledger` returns `(False, 'items in an undefined state: ...')` where the correct status returns `(True, ...)`. SECOND, `runner_stop`'s own design note enumerates this exact outcome as REJECTED option (i) - "a NEW per-item status `unknown_outcome` makes the item INERT ... never reconciled, never refused, never reported, and never run" - and records the decision to carry indeterminacy as the `certainty` flag beside status `interrupted`. So the lift did not merely mislabel: it implemented the option the module documents as broken and warns a future reader never to cause. Understating this matters for the TEST DESIGN: E-04's assertions (a) and (b) both key on the dispatch leak, so a fix that halted the run while still writing `unknown_outcome` would pass every one of them. Separately, the lost stop is invisible in the run summary (`exit_reason` derives from `wind_down`/`stopped_at_checkpoint`, neither set; measured: `STOPPED` appears zero times in a level-4 run's whole output), so the operator-facing report is silent too. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | The Concern now records both measurements verbatim (the `KNOWN_ITEM_STATUSES` membership, both `observe_ledger` results, and the rejected-option-(i) citation) and states that E-02 restores a RECORDED decision rather than inventing one. E-04 gained assertion (d) `runner_shutdown.observe_ledger(run_dir)` coherent - which fails today for a reason DISTINCT from the dispatch leak and so independently pins the status choice - and assertion (e) that the run output contains `STOPPED`. E-04's expected outcome and V-04 now require naming WHICH assertion each reverted test fails on, so a test that only ever fails on (a) is visibly insufficient. F-14 added. |
| PR-003 | MEDIUM | IN-SCOPE | G (executability) | `oc_runipd._record_forced_stop`, `agy_runipd._record_forced_stop` (full body copies) vs `oc_runipd._record_checkpoint_stop`, `agy_runipd._record_checkpoint_stop` (one-line delegating wrappers); `grep -n 'getattr(driver_module' agent_workflows/runner_shared.py` | E-03'S CALLER CHECK WAS BUILT ON A FALSE PREMISE ABOUT THE HOST WRAPPERS. E-03 said the callers are "the two in `execute_item_core` ... and the hosts' `_record_forced_stop` wrappers", and instructed: "if a host wrapper calls the shared one WITHOUT `git_status_fn`, pass its own `git_status` there". Measured, they are not wrappers and they are not callers: each host holds a FULL SECOND COPY of the body calling its own bound `git_status(repo)`, unlike its `_record_checkpoint_stop` sibling which genuinely delegates. They are also UNREACHABLE, because `execute_item_core` calls the bare `_record_forced_stop`, which is absent from its 23-name `getattr(driver_module, ...)` rebinding set and so resolves to the shared definition. Two concrete harms from the wrong premise: the instructed grep returns six hits of which two are `def` lines, so an executor following the text could read a definition as a caller and "fix" it; and the plan's own scope fence then invites declaring a host file in `Scope-Paths`, widening a two-handler change into host deduplication that `recovone` (`cdxcbh`) already claims `_record_forced_stop` as residue for. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now states that at review the ONLY callers of the shared definition were the two in `execute_item_core`, both already passing `git_status_fn=git_status`, so no caller changes and `runner_shared.py` stays the only file E-03 touches; a dedicated paragraph records that the host functions are unreachable second copies rather than delegating wrappers, contrasts them with their `_record_checkpoint_stop` siblings, forbids deleting or converting them here (naming `cdxcbh`'s residue list), and warns that the grep returns `def` lines. V-03 now requires each grep hit CLASSIFIED and an explicit statement that no host file was edited. The scope fence's host clause was rewritten accordingly. F-15 added. |
| PR-004 | MEDIUM | IN-SCOPE | G (executability) / E (verification) | plan `E-04`; `oc_runipd.execute_item._spawn_executor` and `agy_runipd`'s counterpart; `runner_shared.execute_item_core` calling `spawn_executor(prompt_path, work_dir, tracker, plan_path, attempt_no, session_id, use_continue)` | E-04'S RECORDER COULD NOT IDENTIFY THE ITEM THE WAY THE PLAN IMPLIES. E-04 said to patch "the launcher to record the dispatched id6", but the two hosts' launchers have DIFFERENT signatures and `execute_item_core` reaches them through each host's `_spawn_executor` closure, which passes NEITHER `state` NOR `item` - so no argument position yields an id6, and a recorder keyed on one would either break on one host or silently record nothing, making assertion (a) vacuous. Assertion (a) is one of the two the plan designates as proving the fix, so a vacuous version is a test that passes for the wrong reason. Also, E-04's `CheckpointObserver` construction used `detector=lambda: 3`, a zero-argument lambda, where `observe(line)` calls `self.detector(line)`; the field is required so the argument cannot be dropped. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now requires the recorder to read the id6 of the single item whose persisted `status` is `running` out of `run_dir/state.json`, states that this is what makes assertion (a) host-neutral, and explicitly forbids keying on an argument position. The `detector` lambda was corrected to `lambda line: True`. Both were validated by the review probe, which uses exactly this shape on both hosts. |
| PR-005 | MEDIUM | IN-SCOPE | G (executability) | plan `## Scope check` over-scope bullet, as authored | THE SCOPE FENCE CARRIED THE WORDING THE WORKFLOW EXPLICITLY SAYS TO FLAG. It ended "if E-03's caller check finds a host wrapper that must pass `git_status_fn`, declare that host file in `- Scope-Paths:` before editing it", framing a scope question as a gate to clear before proceeding. Per the 2026-09-01 maintainer ruling a fence is a DECLARATION so the runner can reconcile afterwards, and MUST NOT instruct a stop over a scope question; the correct requirement is that an out-of-scope edit be made and then JUSTIFIED, which `aw ipd finalize` already enforces via `--scope-reason`/`--scope-ack`. The earlier mandate propagated stop wording into 224 executed plans and contradicts the work done to stop `aw oc run` stranding unfinished turns. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The over-scope bullet now states the fence as a declaration, records (from PR-003) that no host module is expected to change, and routes any necessary out-of-scope edit to finalize-time justification rather than to a stop. The gate's own scope paragraph matches. The three GENUINE stop conditions (a third arity entry, a real call site that cannot supply `git_status_fn`, a spec that contradicts E-02) are kept and relabelled as unsafe-or-unresolvable conditions, which the same ruling preserves. |
| PR-006 | MEDIUM | UNDER-SCOPE | G (executability) | plan `## Approval and execution gate`, as authored | THE GATE WAS ONE PARAGRAPH AND WAS MISSING MOST OF THE EXECUTION CONTRACT. It had the commit discipline, the honesty rule, and the lifecycle transition (correctly conditional on runner-versus-executor), but carried no statement of WHAT A HUMAN IS APPROVING, no scope fence, no reference to its own resolved OQ-01 despite that question being a deliberate disagreement with an EXECUTED plan's recorded expectation, and no bare-suite instruction. For a change to the control flow of an operator stop on both runner hosts, the absent "what am I approving" is the costly omission: the diff is two handlers and the blast radius is every stopped run. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten keeping `Size assessment: standard`: what a human is approving and why it is not a routine refactor; the one deliberate disagreement with executed plan `13xo5k` recorded as resolved via OQ-01 with the do-not-edit-the-executed-record rule; a declaration-style scope fence naming the intended surface and routing excess to `--scope-reason`; the hard-MUST honesty rule with the BARE `python3 -m pytest` instruction and the explicit prohibition on `-n0`, a second `-q`, and `-p no:randomly`; the three genuine stop conditions; and path-scoped `aw commit` with never-push. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: E-05's guard cannot assert `arity violations: 0` while F-4 defers a violation of that class. Widen this plan to fix F-4, or scope the guard? | Scope the guard to an EXACT one-entry allowlist naming F-4 and its carrier `zt2b16`. | (a) Widen this plan to fix `route_recovery_turn`. Rejected: the shared copy also resolves `classify_recovery_disposition` to a body that raises `AttributeError` on every real lane, so a `write_report` fix alone produces a working wrapper around a broken classifier - the plan's own F-4 says this and `cdxcbh` E-05 owns the injection. (b) Drop the arity half of E-05. Rejected: it guards the class that produced `ccu3k7` defects 3 and 4 and is the cheaper half of the guard. | `runner_shared.route_recovery_turn` calls `save_state(run_dir, state)`; `runner_shared.save_state` requires keyword-only `write_report`. Plan `cdxcbh` `- Scope:` clause (c) and its E-05 already own adding the `save_state` injection, and its F-4 records the same measurement. Measured after simulating E-03: exactly one violation remains, so a one-entry allowlist is exact rather than open-ended. | yes |
| D-2 | PR-002: the level-4 status writes `unknown_outcome`, which `runner_shutdown` does not know. Is restoring `reconcile_disposition` the right fix, or should `unknown_outcome` be added to `KNOWN_ITEM_STATUSES`? | Restore `reconcile_disposition` (status `interrupted`, indeterminacy on the record's `certainty` flag), exactly as E-02 already proposed; add NOTHING to `KNOWN_ITEM_STATUSES`. | Adding `unknown_outcome` to `KNOWN_ITEM_STATUSES`. Rejected: it would satisfy the coherence check while leaving the item INERT, since no dequeue, requeue, or reconcile path selects that status - which is broken option (i) verbatim, and it would also silently bypass `requeue_interrupted`'s R19 indeterminate gate rather than applying it. | The decision is already RECORDED in the tree and needed no invention: the design note above `runner_stop.FORCED_DISPOSITION` enumerates both naive options as broken, states "THE DECISION: carry the indeterminacy as an EXPLICIT PER-ITEM FLAG ... ALONGSIDE the status `interrupted`", and says it was "VERIFIED against the drivers rather than reasoned about". `reconcile_disposition`'s deliberate-stop branch returns `STOPPED_DISPOSITION` for BOTH levels, and the pre-lift host bodies routed through it. | yes |
| D-3 | PR-003: both hosts hold unreachable duplicate `_record_forced_stop` bodies. Delete or convert them in this plan? | Neither. Record the duplication (in E-03's prose, F-15, and the commit message) and leave the copies untouched. | (a) Convert them to delegating wrappers like their `_record_checkpoint_stop` siblings. Rejected: that is host deduplication, it would put two host modules in a four-path plan whose whole change is two handlers, and `cdxcbh` already lists `_record_forced_stop` in its OUT clause as scanner residue, so the concern has an owner. (b) Delete them as dead code. Rejected: unreachable-today is not unreachable-tomorrow, deletion is the less reversible option, and nothing in scope requires it. | `execute_item_core` calls the bare `_record_forced_stop` and the name is absent from its 23-entry `getattr(driver_module, ...)` rebinding set, so the shared definition is what runs; the host copies are correct in themselves and reached by nobody. Plan `cdxcbh` `- Scope:` OUT clause names `_record_forced_stop` as residue. | yes |
| D-4 | Does this plan need a spec amendment (it changes deliberate-stop control flow, which spec `c4gd2h` governs)? | No. The plan's `N/A` is correct and is kept. | Amending `c4gd2h`. Rejected: the spec already requires the behavior being restored, so an amendment would change no contract. | `c4gd2h` R3 (every item terminal or explicitly marked interrupted with level and certainty), R18/R19 (record certainty; refuse a blind resume of an indeterminate item), R21/R22 (distinguish deliberate stop from crash; never record a stopped item as successful), and the level table's "The only difference between 3 and 4 is outcome CERTAINTY". Today's code violates R3 and R19; E-02 restores conformance. The plan's existing STOP condition (report rather than edit the spec if `c4gd2h` describes the handler as returning) is the right residual guard and was retained. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent afpmdu -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent afpmdu -> {"outcome":"clean","exit":0,"findings":0}   (after revisions)

HEAD at review                                 8e74dcac  (plan authored against 877545fc)
lane input vs pending/ copy                    byte-identical -> no pre-review snapshot needed

F-1 REPRODUCED (real run_queue, both hosts, both levels)   all four: dispatched=['qa0001','qa0002']
F-2 REPRODUCED (_record_forced_stop, no git_status_fn)      git_state = '<unobserved: git_status()
                                                            missing 1 required keyword-only
                                                            argument: run_checked>'
F-12 REPRODUCED  grep -ln 'StopNowForce|StopAtCheckpoint' tests/*.py -> no file
exit-code correction CONFIRMED  deliberate_stop_exit_code(['interrupted','queued'], stopped=True) -> 1

arity scan, runner_shared, at HEAD              2 violations   <- plan's E-05 asserted 0   PR-001
  with E-03 simulated in memory                 1 violation    (route_recovery_turn -> save_state)
'unknown_outcome' in KNOWN_ITEM_STATUSES        False                                      PR-002
observe_ledger([unknown_outcome, queued])       (False, 'items in an undefined state: ...')
observe_ledger([interrupted, queued])           (True,  '2 item(s), all in a defined state')
level-4 run output contains 'STOPPED'           False                                      PR-002
host _record_forced_stop                        full body copies, NOT delegating wrappers  PR-003
  in execute_item_core's getattr rebinding set  no (23 names, absent) -> host copies unreachable
_spawn_executor closure passes state or item    no -> id6 unavailable by arg position      PR-004

pre-lift host body (70a2059f^:oc_runipd.py, execute_item, spawn path)
  item['status'], _ = reconcile_disposition(repo, item, run_dir, 1)  then  raise     (both handlers)
HEAD shared body (execute_item_core, spawn path)
  item['status'] = runner_stop.FORCED_DISPOSITION / STOPPED_DISPOSITION  then  return
HEAD shared body (execute_item_core, VERIFY path)  still reconcile_disposition + raise  (unchanged, correct)
execute_item_core handler verbs (AST)           try@26212 -> Return,Return,Return   <- spawn, defective
                                                try@26491 -> Raise,Raise,Expr      <- verify, correct
finally: block wrapping the region              present (27887-27891), suppress-only -> raise is safe
provenance  git log -S'interrupted by deliberate force stop' -> 70a2059f only  (F-1 attribution holds)

runner_fork_scan reuse premise                  normalize/top_level_defs/free_names/is_pure_delegation
                                                all import by path, no module-level side effects
carriers resolve                                zt2b16, 2415x6, tm5vnx (backlog, graduated);
                                                cdxcbh, 87jnym (plans, pending)
```

NOT RE-RUN AT REVIEW, stated rather than implied: the suite. This review changed only planning prose,
so no suite baseline is claimed, confirmed, or refuted here; E-06 requires a bare `python3 -m pytest`
with the summary line pasted at execution.

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001 through PR-006 all FIXED, none deferred, none open. OQ-01 was
already resolved from repository evidence by the author and was independently confirmed (the pre-lift
bodies `raise`; `13xo5k`'s own findings say the re-raise is deliberate), so this plan carries NO open
questions and nothing required escalation as a `- Blocking: yes` question.

Readiness `go-pending-approval`. What a human should weigh at approval, none of it a finding. FIRST,
this plan deliberately CONTRADICTS an executed plan's recorded expectation: `13xo5k` V-03 certified the
spawn-path `return` as correct, and this plan restores the `raise`. The evidence is strongly on this
plan's side (the pre-lift bodies, `13xo5k`'s own F-5 and conventions, the behavioral probe, and spec
R3/R19 conformance), and `13xo5k`'s record is correctly left unedited with the disagreement cited
instead. SECOND, the change is small but its blast radius is every deliberately stopped run on both
hosts, and no test in the tree currently covers that path at all (F-12), which is why E-04's four
behavioral tests matter more than the two-handler diff suggests. THIRD, `agent_workflows/runner_shared.py`
is also named by `cdxcbh` and `87jnym`; that is not a hazard (each execute item gets an isolated
worktree and returns through the merge-and-revalidate gate) but the three plans do touch adjacent
regions of one function, so running them serially is the lower-surprise order.
