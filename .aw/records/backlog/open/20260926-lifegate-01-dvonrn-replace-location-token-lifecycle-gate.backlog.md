- Id: dvonrn
- Status: open
- Graduated-To: lifegate
- Blocks-Release: next
- Set: lifegate
- Priority: high
- Work-Kind: bug
- Summary: replace the location-plus-token lifecycle gate with one plan-scoped 'a live runner holds this plan' check, allow begin/finalize anywhere, and nudge toward the lane

## Workflow history
- 2026-10-06 open (aw set): u4glub returned to authoring: uncovered obligation: Four checks span the children and cannot be performed by any child alone, which is why they live here.; re-run graduation to complete the handoff
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053059Z-3200713: e25iy9, m47znv, u4glub, urv602
- 2026-09-27 same-status (aw set): bug gates the next release (AGENTS.md: every live bug gates the next release)
- 2026-09-27 open (aw set): Design complete: all decisions D1-D8 settled with the maintainer on 2026-09-26; ready to graduate into a plan.
- 2026-09-26 created (aw backlog): Draft design, decisions being recorded one at a time with the maintainer (2026-09-26). Not yet ready to graduate.

STATUS: DESIGN COMPLETE 2026-09-26. Every decision D1-D8 below was settled with the maintainer one at a time; ready to graduate into a plan.

## Problem

The terminal lifecycle gate added by executed plan u27oh3 (spec c4gd2h) blocks aw ipd finalize and orchestrator retirement in any checkout under .aw/worktrees/ or on an aw/lane/* branch unless a per-run secret token (AW_DRIVER_ATTEST) is presented. It guesses 'a runner owns this' from the folder path, so it wrongly blocks a human's own feature worktree placed under .aw/worktrees/ (measured 2026-09-26: feat-partition, AW-LIFECYCLE-ROLE-001) and blocks recovery of a lane whose runner died. The token only stops honest actors (u27oh3's own honest limit: a same-user agent can read the token file), and honest actors are already stopped by the worker label and a clear message. Guiding principle being added alongside this: we never try to mitigate a malicious agent.

## Decisions

### D1 (DECIDED 2026-09-26): no location rule; refuse only when someone else is actively working on the plan

- begin and finalize are ALLOWED ANYWHERE: inside a lane, on a feature branch, or in main.
- Doing them in the lane/branch is PREFERRED (the plan's move to executed/ travels with the code and lands on main in one reviewed merge) but it is a preference, never enforced.
- The runner itself already finalizes INSIDE its lane (runner_shared: finalize_repo = Path(work_dir), then sync_receipt_into_worktree, then finalize), which is the preferred shape and stays.
- The only reason to refuse: a LIVE runner currently holds this plan and the caller is not that runner. Refuse with the run named and two choices (wait, or aw <host> run stop <run-id>), plus a deliberate override --take-over '<reason>' that records the reason in the plan's history.
- The runner's own agent stays refused by its existing worker label (AW_EXECUTION_ROLE=worker) and the existing 'this is the runner's step, you are done' message. That was the only honest mistake actually observed.
- The runner itself needs NO new label or token: it is the recorded holder (the owner file names its process), so the check lets the holder through by a plain comparison, not a security measure.
- NUDGE, never a refusal: when begin/finalize runs in main and a lane or feature branch for the same plan exists, print one line such as 'a lane for this plan exists; finalizing there keeps main cleaner'.
- Delete: the per-run token (driver-attest.token), minting/passing/withholding it, verify_driver_attestation, and lane_worktree_active's path/branch guess as a gate.

### D2 (DECIDED 2026-09-26): what 'holds this plan' means and how it is found

- HELD = some run is ALIVE and has this plan's id6 in its queue with a status that is NOT finished (not in TERMINAL_STATES). 'Not finished' INCLUDES merely waiting to run (queued): otherwise a person could finalize it and the runner would later pick it up again.
- ALIVE = BOTH (a) the run's driver.lock is held (the OS file-lock probe, run_viewer.driver_holder_state, which the OS releases when the holder dies) AND (b) the process recorded in that driver.lock still exists. (b) catches a runner that died while something it started still holds the lock file open.
- Keyed on the PLAN, not the folder, so one check covers: inside a lane, in main while a lane for that plan runs, and on a feature branch.
- Source is the RUN records (.aw/records/runs/<run>/state.json + driver.lock), reusing runner_shared.peer_drivers and the queue lookup plan e54nz9 added. The lane owner files (.aw/worktrees/.owners/) are NOT used for this: they record a lane rather than a plan, survive after a run ends, and judge liveness by process number alone.
- THE RUNNER'S OWN CALL: when the runner calls begin/finalize it passes its own run id; the check IGNORES that one run when looking for holders, so the runner does not block itself. This is a plain label, not a secret: anyone could pass it, which is accepted because we only guard against honest mistakes and nobody passes another run's id by accident. It replaces the random token.
- ORDER: the existing worker-label check (AW_EXECUTION_ROLE=worker, 'this is the runner's step, you are done') runs FIRST. The runner's own agent never receives the run id, so it never gets the exception.

### D3 (DECIDED 2026-09-26): when liveness cannot be determined, and runs on other machines

Stale owner files are moot after D2 (liveness comes from driver.lock plus process existence, and a dead run's lock is released by the OS).

- GAP FOUND: run records do NOT capture the machine. `driver.lock` holds only `pid=<n> started=<t>` (runner_shared writes `f"pid={os.getpid()} started={utc_now()}\n"`), and state.json has no machine field (its `host` fields mean the agent program, oc/agy, not the computer). Without it, a live runner on ANOTHER machine sharing the repo (shared drive, cluster) is indistinguishable from a dead local one, and the process check would wrongly say 'dead'. The lane owner files already record `host` (socket.gethostname()) and treat a foreign-machine record as 'cannot tell'; follow that precedent.
- FIX: record the machine when a run takes its driver.lock: `pid=<n> host=<machine> started=<t>`. Older records without `host=` stay readable.
- LIVENESS ORDER:
  1. Lock file unreadable (permissions or similar): REFUSE (maintainer ruling).
  2. Record names a DIFFERENT machine: cannot check that machine's processes, so REFUSE with 'run <id> on machine <host> may still be working on this plan', plus the `--take-over '<reason>'` override.
  3. Same machine, or an older record with no `host=`: apply D2 (lock held AND process exists).
- HONEST LIMIT: on a shared drive the OS file lock may or may not work across machines, depending on the filesystem (NFS, SMB, cluster filesystems differ). The recorded machine name is what makes the cross-machine case safe regardless.

### D4 (DECIDED 2026-09-26): every entry point passes the one check, placed in the core functions

Entry points measured 2026-09-26:

| Entry point | Lands in | Worker-label check today |
| --- | --- | --- |
| `aw ipd begin` | CLI handler -> `ipd_lifecycle.begin` | CLI handler only (`_refuse_worker_role_verb("begin")`) |
| `aw ipd finalize` | CLI handler -> `ipd_lifecycle.finalize` | CLI handler AND inside `finalize` |
| `aw set executed` / `aw ipd set executed` | `status_set._delegate_plan_executed_to_finalize` -> `ipd_lifecycle.finalize` | inside `finalize` |
| orchestrator retirement (runner or `aw set`) | `ipd_lifecycle.retire_orchestrator` | inside `retire_orchestrator` |
| the runner's own begin/finalize | subprocess `aw ipd begin` / `aw ipd finalize` | via the CLI handlers |

Finalize, `aw set executed` and retirement converge on `_finalize_transaction`; `begin` has no shared layer below its CLI handler, so a direct `ipd_lifecycle.begin` caller skips the label check today (none exists yet).

- Place BOTH the worker-label check and the new 'held by a live run' check INSIDE the core functions `ipd_lifecycle.begin`, `ipd_lifecycle.finalize` (which covers `aw set executed`), and `ipd_lifecycle.retire_orchestrator`. The CLI handlers only pass through the caller's run id and any `--take-over` reason, so no caller can route around the check.
- Retirement: a runner retiring an orchestrator is itself the live holder of that plan, so it passes its own run id exactly as its begin/finalize calls do.
- TEST: one test drives EVERY entry point in the table against a plan held by a live run and asserts each refuses identically (and that each proceeds when the caller passes the holder's run id), so a future new caller cannot silently skip the check.

### D5 (DECIDED 2026-09-26): other gates that exist only against malicious agents

- REMOVE the driver token as part of THIS design (confirmed by the maintainer).
- Do NOT sweep other gates here. They are audited separately in backlog `ariaau` (malgate), handed off to another agent: keep / simplify / delete each, starting with `wtiso_gate.py`'s raising stubs, the `8zgybk`/`x03wgn` adversarial scaffolding, and 'determined same-user agent' justifications.
- Already kept as honest: `--by-human` (its spec calls it a speed bump), suite-baseline adjudication (refuses nothing).
- Going forward: any review that touches a gate applies P15.

### D6 (DECIDED 2026-09-26): the principle is written

Added as GUIDING_PRINCIPLES.md section 15, "Guard against honest mistakes, never against a malicious agent" (commit `40868bb1`). It records the earlier rulings it generalizes (2026-09-08 `daexj1` OQ-02 'mitigating sloppiness, not malice', reaffirmed 2026-09-20; spec `honest-human-approval-attestation`).

### D7 (DECIDED 2026-09-26): the opt-in OS sandbox (1o4eif) stays, as optional isolation only

- KEEP `host_sandbox_profile` and the hardened profile (plan `1o4eif`, executed) exactly as shipped: opt-in, off by default, Linux only, selected by an explicit request (`oc_runipd` wraps argv only "iff the hardened profile was explicitly requested").
- REFRAME, do not rebuild: it is OPTIONAL ISOLATION an operator may choose, NOT "the real fix for malicious agents" and NOT something any gate relies on. Nothing in this design (and nothing new) may depend on it being on. This matches P15: if real isolation is ever required it comes from the OS, never from our own checks.
- Documentation that frames it as the answer to a 'determined same-user agent' (for example `ipd_lifecycle`'s honest-limit comments pointing at `1o4eif`) is updated when the token code it sits beside is deleted in this design, and elsewhere by the `ariaau` audit.

### D8 (DECIDED 2026-09-26): specs this design touches (enumerated by search, not assumed)

Searched every `.spec.md` for the token (`AW_DRIVER_ATTEST`, `driver-attest`, 'driver attestation'), the location guess (`lane_worktree_active`), the refusal (`AW-LIFECYCLE-ROLE-001`), the role (`AW_EXECUTION_ROLE`, 'worker role', `worker_role_active`), and lifecycle ownership (begin receipt, self-finalize, 'runner owns').

FINDING: the per-run token and the location guess added by plan `u27oh3` are specified in NO spec. They exist only in that plan and in code. So removing them needs no spec amendment by itself. The earlier assumption that `c4gd2h` must be amended was WRONG: `c4gd2h` (runner lifecycle: graceful quit) holds stop-protocol rules, not lifecycle-role rules; its R2 ('driver.lock is released on completion of any level; a lock holding a dead PID is a defect') is CONSISTENT with D2 and needs no change.

MUST AMEND (declare each in the plan's `- Scope-Paths:` and say why in its spec-sync section):
- `7ckptx` (worker lane containment, approved). Its R4.5 ('an isolated turn's child environment MUST carry the execution-role selector that causes driver-owned lifecycle verbs to refuse inside a lane') and acceptance A11 ('an in-lane invocation of a driver-owned lifecycle verb refuses with the documented code ... the driver's own invocation still succeeds') stay TRUE for the worker label, but 'refuse inside a lane' must be restated as: refused for a worker-labelled caller (unchanged), and for anyone else ONLY while a live run holds the plan (D1/D2), anywhere, not by location. R4.5's existing honest-limit wording ('an environment selector and not a hardened boundary') already matches P15 and stays.

MUST UPDATE if it is still `to-review` when the plan executes, otherwise note-amend:
- `llbr2b` (lifecycle automation policy, to-review). Its section 3.2 note ('A worker-role process is refused outright at the CLI wrapper') becomes wrong once D4 moves the check into the core functions, and its invariant C-8 ('worker/coordinator ROLE ... INVARIANT') must add the new 'held by a live run' refusal as a second lifecycle invariant.

READ, NO CHANGE EXPECTED (the plan re-checks each at execution):
- `77tr3o` (orchestrator retirement, approved): mentions the `aw set executed` worker-role bypass as out of its scope; D4 closes that path, so the plan may add a one-line history note pointing at it.
- `25kzda` (run-and-verify, approved): `IPD-EXEC-BEGIN-RECEIPT` and the begin-receipt staleness rules are unchanged by this design.
- `c4gd2h` (runner lifecycle, implementing): consistent, as above.
- `pqsx96` (draft), `i4gpto` (draft): mention begin receipts only; unaffected.

ALSO UPDATE (not specs): `GUIDING_PRINCIPLES.md` P15 already cites this design; code comments that point to `1o4eif` as the fix for a 'determined same-user agent' beside the deleted token code (see D7).

## Honest limits

Guidance for honest actors only. It is not, and is not meant to be, a security boundary.
