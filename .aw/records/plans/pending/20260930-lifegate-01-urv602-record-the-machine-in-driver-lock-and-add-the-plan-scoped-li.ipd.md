# IPD: Record the machine in driver.lock and add the plan-scoped live-holder predicate

- Date: 2026-09-30
- Kind: child
- Concern: The replacement gate designed in backlog `dvonrn` D1/D2 asks one question ("is a live run currently working on THIS PLAN?") and the run records cannot answer it today. Two gaps, both measured. FIRST, `runner_shared.run_lock` writes `f"pid={os.getpid()} started={utc_now()}\n"` into `driver.lock` and `state.json` carries no machine field at all (its `host` fields name the agent program, `oc` or `agy`, not the computer), so a live run on ANOTHER machine sharing the repository is indistinguishable from a dead local one and a process probe would wrongly report "dead" for a run that is still working. The lane owner records already solve exactly this by storing `socket.gethostname()` and treating a foreign-machine record as undeterminable (`worktree_lease._owner_is_live`), so the precedent to follow is in the tree. SECOND, no predicate answers the plan-scoped question: `runner_shared.peer_drivers` reports which runs hold a lock but says nothing about a plan, and `peer_held_prerequisites` walks peer queues only for unsatisfied `executed:` dependency edges of a queued item. Without both, Order 02 would have to invent the liveness rule inline in three places and could not make the cross-machine case safe.
- Scope: Two additive, no-refusal-behavior changes that give Order 02 something to call. (1) Record the machine when a run takes its `driver.lock`, so the record reads `pid=<n> host=<machine> started=<t>`, keeping older records without `host=` readable. (2) Add ONE predicate to `runner_shared` that answers "which live run, if any, holds this plan's id6?", returning a three-valued verdict (a named holder, no holder, or undeterminable) with the machine and the reason, built from the existing `run_viewer.driver_holder_state` lock probe plus a process-existence check plus the queue-status rule (`not in TERMINAL_STATES`), and applying D3's liveness ORDER. EXCLUDES every refusal: nothing in this plan changes what any verb accepts or refuses, and the predicate has no caller until Order 02. EXCLUDES deleting the token or the location guess, which is Order 02's subject and would strand this plan's tests if done here. EXCLUDES the `--take-over` override and the nudge, which are Orders 02 and 03.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_plan_holder_predicate.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: dvonrn
- Blocks-Release: next
- Set: lifegate
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: urv602

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored while graduating backlog `dvonrn`, whose decisions D1-D8 were settled with the maintainer on 2026-09-26 and are not reopened here. Every claim in D2 and D3 was re-measured in this lane rather than inherited, and ONE measurement changes this plan's shape from the item's description. The item's D3 says the fix is to record the machine "when a run takes its driver.lock", which reads as a one-line change to one writer; measured, `driver.lock` has TWO independent writers with different shapes (`runner_shared.run_lock` writes the `pid=` record through a descriptor duped from the locked one, while `acquire_repo_scoped_lock` writes `f"{holder_label} pid={os.getpid()} started={utc_now()}\n"` for the integration lock), and only the FIRST is a run's driver lock. Writing the machine into both would put a hostname into the integration lock, which no part of this design reads and which the leak sanitizer would then have to consider on a new surface. So E-02 is deliberately scoped to `run_lock` alone and E-03 states the exclusion. A SECOND measurement sets the reader's shape: `platform_lock.LOCK_RECORD_PID_RE` is `r"(?<!\w)p?id=(\d+)"`, tolerating a missing first byte because a live Windows holder's mandatory lock makes byte 0 unreadable, so the `host=` reader must tolerate the same truncation and must not be a naive split.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the run records able to answer the one question the replacement gate asks, and make the
cross-machine case safe, without changing a single refusal.

This plan is deliberately the boring half of the Set. It ships no gate, deletes nothing, and changes no
message a user sees. Its whole value is that Order 02 can then replace a location guess and a secret token
with one call to a predicate that was built and tested on its own, against records the predicate itself
made complete.

WHY THE MACHINE FIELD IS NOT OPTIONAL, since "record the hostname" reads like polish. Backlog `dvonrn` D2
defines ALIVE as the conjunction of two facts: the `driver.lock` is held (an OS file-lock probe, which the
OS releases when the holder dies) AND the process recorded in that lock still exists. The second conjunct
is a `kill(pid, 0)`-shaped question, and it is MEANINGLESS about a process on another computer: a pid from
another machine either does not exist locally (reporting a live run dead) or happens to exist as something
unrelated (reporting a dead run live). D3 records the honest limit that on a shared drive the OS file lock
may or may not work across machines depending on the filesystem, so the lock probe alone cannot be trusted
to cover the case either. The recorded machine name is what makes the cross-machine case safe REGARDLESS
of the filesystem, by converting it from a wrong answer into an explicit "cannot tell, so refuse".

WHY THE PREDICATE IS ONE FUNCTION AND NOT THREE CALL SITES. Order 02 places the check inside
`ipd_lifecycle.begin`, `ipd_lifecycle.finalize` and `ipd_lifecycle.retire_orchestrator` (D4), and
`dvonrn` D4's own test obligation is that every entry point refuses IDENTICALLY. Three inline
implementations cannot satisfy that by construction, and the repository has already recorded this exact
hazard as a spec requirement: `7ckptx` R6.1 says a containment rule consumed by more than one surface
"MUST live in one predicate that every surface calls" and that "forking the rule is non-conforming even
when the copies agree".

FOUR FACTS ESTABLISHED AT AUTHORING. The executor re-measures each (E-01) rather than trusting this list.

1. `driver.lock` RECORDS NO MACHINE. `runner_shared.run_lock` writes exactly
   `f"pid={os.getpid()} started={utc_now()}\n"` through a stream duped from the locked descriptor. There is
   no hostname anywhere in the record.

2. `state.json` RECORDS NO MACHINE EITHER, and its `host` field is a false friend. The `host` vocabulary in
   the runner state and in `HostLabels` names the AGENT PROGRAM (`oc` / `agy`), not the computer, so a
   reader who takes it for a hostname gets a wrong answer rather than a missing one. This is why the
   machine must be recorded in `driver.lock` beside the pid it qualifies, rather than inferred.

3. THE LANE OWNER RECORDS ALREADY SOLVE THIS, and their rule is the one to copy.
   `worktree_lease.write_lane_owner` stores `socket.gethostname()`, and `worktree_lease._owner_is_live`
   returns None (undeterminable, never adopt) when `host and host != socket.gethostname()`. D3 directs this
   plan to follow that precedent. NOTE the deliberate divergence D2 requires: the lane owner files are NOT
   used as the source for this check, because they record a LANE rather than a plan, they survive after a
   run ends, and they judge liveness by process number alone.

4. THE EXISTING PEER MACHINERY IS THE RIGHT FOUNDATION AND IS INSUFFICIENT ALONE.
   `runner_shared.peer_drivers` already discovers every run directory through the correct resolver
   (`runs_repo_root`, which matters because a lane resolves `state_root` to its own nonexistent runs tree:
   its docstring records `discover_run_dirs(Path("."))` returning 0 from a lane while the resolved root
   returned 246), already probes liveness read-only through `run_viewer.driver_holder_state`, and already
   preserves a three-valued answer with `PEER_UNKNOWN` never collapsing to "no peer". What it does not do
   is answer anything about a PLAN, and `peer_held_prerequisites` answers only about unsatisfied
   `executed:` edges of a queued item. So this plan REUSES `peer_drivers` and adds the plan-keyed question
   on top, rather than writing a second discovery or a second liveness rule.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure the record shape before changing it

- [ ] E-01 RE-DERIVE THE FOUR FACTS IN YOUR OWN LANE, because every item below rests on them and a stale measurement here produces a predicate that silently answers the wrong question. Read `runner_shared.run_lock` and paste the exact record string it writes. Search `state.json` for any machine or hostname field and paste the result (expect none). Read `worktree_lease.write_lane_owner` and `_owner_is_live` and paste the foreign-machine arm. Read `platform_lock.LOCK_RECORD_PID_RE` and `read_lock_record` and paste the regex plus the docstring sentence explaining why a live Windows holder's first byte is unreadable. Then enumerate EVERY writer of a file named `driver.lock` and every writer that composes a `pid=` lock record, and state which of them is a run's driver lock and which is not.
  - Depends on: none
  - Expected outcome: the pasted record string, the pasted absence of a machine field in `state.json`, the pasted lane-owner precedent, the pasted regex with its Windows rationale, and a writer census naming `runner_shared.run_lock` as the one driver-lock writer and `acquire_repo_scoped_lock` as an integration-lock writer that this plan must NOT change. If `driver.lock` already carries a machine, STOP and report: E-02's premise has failed and the plan needs re-authoring rather than adapting.
  - Execution state: pending

### Task group 2: record the machine

- [ ] E-02 WRITE THE MACHINE INTO THE DRIVER LOCK RECORD in `runner_shared.run_lock`, so the record reads `pid=<n> host=<machine> started=<t>`, using `socket.gethostname()` exactly as `worktree_lease.write_lane_owner` does (one spelling of "this machine" in the package, not two). Keep the write mechanism untouched: it must stay the stream duped from the LOCKED descriptor, because `RunLockHandle`'s inode-identity check compares against the inode actually locked and a fresh `open()` would break that. Place `host=` BETWEEN `pid=` and `started=` rather than at the end, so the pid and the machine that qualifies it are adjacent and a truncated read that recovers the pid tends to recover its machine too. Explain in a comment WHY the machine is recorded (the cross-machine liveness case D3 measures), not merely that it is.
  - Depends on: E-01
  - Expected outcome: the record written by a real acquired lock, pasted, showing all three fields; `RunLockHandle.release` still succeeds under its inode check; and the diff shows no change to how the descriptor is obtained.
  - Execution state: pending

- [ ] E-03 ADD THE READER FOR THAT FIELD beside `platform_lock.read_lock_record_pid`, as `read_lock_record_host` (or the name that matches its sibling), returning the recorded machine or None. It MUST tolerate the SAME truncation its pid sibling does: `read_lock_record`'s docstring records that on Windows a live holder's mandatory lock over byte 0 makes the first character unreadable, so the reader must be a regex tolerant of a missing leading byte in the same way `LOCK_RECORD_PID_RE` is, never a naive `split("host=")`. An OLDER RECORD WITH NO `host=` MUST RETURN None rather than raising or guessing, because D3 requires such a record to fall through to the same-machine rule. State in the docstring that the value is a RECORDED CLAIM used to decide whether a process probe is meaningful, and is not itself a liveness signal, mirroring the discipline `_peer_pid` already states ("DIAGNOSTIC ONLY, never a liveness signal"). DO NOT add the machine to the integration lock record written by `acquire_repo_scoped_lock`: nothing in this design reads it there, and a hostname on that surface is new material for the leak sanitizer to consider for no benefit (E-01's census names it).
  - Depends on: E-02
  - Expected outcome: the reader returns the machine for a current record, None for a legacy `pid=<n> started=<t>` record, and the recorded machine for a record whose first byte is blanked; the integration lock record is unchanged in the diff.
  - Execution state: pending

### Task group 3: answer the plan-scoped question

- [ ] E-04 ADD THE ONE PREDICATE that answers "which live run holds this plan's id6?", in `runner_shared`, returning a THREE-VALUED result carrying the verdict, the run id, the recorded machine, the queue status that made it held, and a human-readable reason. The three values are HELD (a named live run has this id6 in its queue with a status NOT in `TERMINAL_STATES`), NOT HELD (nothing does), and UNDETERMINABLE (we could not tell). Build it from `peer_drivers` for discovery and lock-probe liveness rather than a second discovery, and accept an EXCLUDED run id so the holder can be let through (Order 02 passes the caller's own run id; that is a plain label, not a secret, per D2). HELD MUST INCLUDE A MERELY QUEUED ITEM: D2 requires it, because a status not yet started is exactly the case where a person finalizes the plan and the runner later picks it up again. Use `TERMINAL_STATES` (the union including legacy aliases) and not `TERMINAL_STATES_CANONICAL`, so a historical record's legacy token still reads as finished; say so in a comment, since choosing the narrower set would make a long-finished run look like a live holder.
  - Depends on: E-03
  - Expected outcome: the predicate's signature and returned type, plus a demonstration on synthetic run directories of each of the three verdicts, including the queued-not-started case reading HELD.
  - Execution state: pending

- [ ] E-05 IMPLEMENT D3's LIVENESS ORDER INSIDE THAT PREDICATE, exactly as the maintainer ruled, with each arm commented with the reason it fails closed. (1) The lock file is present but UNREADABLE (permissions or similar): UNDETERMINABLE, which Order 02 turns into a refusal, per the maintainer ruling in D3. (2) The record names a DIFFERENT machine: UNDETERMINABLE, because this computer cannot probe that computer's processes, and the reason string must name the run and the machine so Order 02's message can say "run <id> on machine <host> may still be working on this plan". (3) Same machine, OR a legacy record with no `host=`: apply D2, requiring BOTH the lock held AND the recorded process existing. Preserve the existing `PEER_UNKNOWN` discipline: a probe that cannot be answered is never reported as absent. NOTE for the executor: arm (3)'s process check is the ONLY new liveness input; do not replace the lock probe with it, because a recorded pid can be reused by an unrelated process (the reason `driver_holder_state` gives for preferring lock acquirability) while the process check exists only to catch the inverse case D2 names, a runner that died while something it started still holds the lock file open.
  - Depends on: E-04
  - Expected outcome: a table of the four liveness inputs (lock readable, machine same or different or absent, lock held, process exists) against the verdict, demonstrated by driving the predicate rather than by reading its source, with the foreign-machine reason string pasted.
  - Execution state: pending

- [ ] E-06 ADD THE BEHAVIORAL TEST FILE `tests/test_plan_holder_predicate.py`, driving the REAL functions against REAL run directories under a temporary root rather than against mocks, because a mocked lock proves nothing about the OS behavior this predicate rests on. Every arm it must cover is enumerated in V-06 and all of them are required. Assert on RETURNED VALUES and RENDERED REASON TEXT ONLY: do not read module source, do not count callers, and do not assert which module defines what (AGENTS.md; GUIDING_PRINCIPLES P16). Where the platform cannot produce an unreadable lock file (running as root defeats a permission bit) that one arm must SKIP explicitly and say so in the test docstring, never pass silently.
  - Depends on: E-05
  - Expected outcome: a new passing test file whose bare `python3 -m pytest` run is pasted, every arm V-06 enumerates present and passing, plus the mutation demonstration V-06 requires showing each verdict assertion is sensitive.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation here is by symbol or quoted string.
- ONE PREDICATE PER RULE (spec `7ckptx` R6.1): "A containment rule consumed by more than one surface MUST live in one predicate that every surface calls. Forking the rule is non-conforming even when the copies agree." This is why E-04 is one function and why Order 02 has three call sites and no second implementation.
- A READ MUST NOT MUTATE (GUIDING_PRINCIPLES P10). The predicate is read-only by construction, and the existing machinery is built for exactly this: `driver_holder_state` uses `platform_lock.probe_free` with no `O_CREAT` and no `O_TRUNC` precisely because the driver records its pid INSIDE the lock file and "a probe that truncated would destroy a live driver's own record". Adding `host=` to that record makes that property MORE load-bearing, not less.
- THREE-VALUED LIVENESS IS EXISTING PRECEDENT, not an invention of this plan. `run_viewer` already distinguishes `HOLDER_LIVE` / `HOLDER_NONE` / `HOLDER_UNKNOWN` on the rule that "failing to prove a driver is alive is not proof it is dead", and `peer_drivers` already refuses to collapse `PEER_UNKNOWN` into absence. E-04's verdict follows that shape rather than a boolean.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md; GUIDING_PRINCIPLES P16). The tempting test here is "assert the predicate is called from three places", which is a caller census and forbidden; Order 02 owns the entry-point coverage and pins it by DRIVING each entry point.
- RESOLVE THE RUNS ROOT, NEVER `state_root` DIRECTLY (`runner_shared.runs_repo_root`). Its docstring records this as "a correctness requirement rather than tidiness" because a lane resolves to its own nonexistent runs tree. E-04 must reuse `peer_drivers`, which already does this; a hand-rolled discovery would report NO HOLDER from inside a lane, which is exactly where Order 02's check runs.
- COMMENTS AND PLANS ARE NOT USER-FACING PROSE (GUIDING_PRINCIPLES P13), so the no-dash convention does not apply to anything this plan edits.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The driver lock records no machine | `run_lock` writes `f"pid={os.getpid()} started={utc_now()}\n"` | E-02 exists; without it D2's process check is meaningless across machines |
| F-2 | `state.json`'s `host` names the agent program, not the computer | The `host` vocabulary throughout the runner state and `HostLabels` means `oc` / `agy` | The machine cannot be inferred from existing state; it must be recorded beside the pid it qualifies |
| F-3 | The lane owner records already solve the cross-machine case | `write_lane_owner` stores `socket.gethostname()`; `_owner_is_live` returns None when `host and host != socket.gethostname()` with the comment "A record from another machine: we cannot tell, so treat as UNKNOWN (never adopt)" | E-02/E-05 copy this rule; D3 directs exactly this precedent |
| F-4 | Lane owner records are the wrong SOURCE for a plan-keyed check | They key on a lane, survive after a run ends, and judge liveness by pid alone | E-04 reads run records instead, as D2 requires; the owner files are untouched by this Set |
| F-5 | `peer_drivers` supplies discovery, read-only liveness, and the three-valued shape | It resolves through `runs_repo_root`, probes via `driver_holder_state`, omits proven-dead runs, and reports `PEER_UNKNOWN` distinctly | E-04 builds on it rather than writing a second discovery or a second liveness rule |
| F-6 | No existing predicate answers a PLAN-keyed liveness question | `peer_held_prerequisites` walks peer queues only for unsatisfied `executed:` IPD edges of a queued item, keyed on dependency edges | The predicate is genuinely new work, not a rename of an existing one |
| F-7 | A lane resolves the runs tree to nothing if asked naively | `runs_repo_root`'s docstring: from lane `vddpml`, `discover_run_dirs(Path("."))` returned 0 while the resolved root returned 246 | A hand-rolled discovery would report NO HOLDER from precisely where Order 02's check runs; reuse is mandatory, not stylistic |
| F-8 | A live Windows holder's lock record cannot be read from byte 0 | `read_lock_record`: the mandatory byte-0 lock makes `pid=42` read as `id=42`, which `LOCK_RECORD_PID_RE` (`r"(?<!\w)p?id=(\d+)"`) tolerates | E-03's reader must tolerate the same truncation; a naive split would fail on a live Windows holder |
| F-9 | `driver.lock` is not the only `pid=` lock record in the tree | `acquire_repo_scoped_lock` writes `f"{holder_label} pid={os.getpid()} started={utc_now()}\n"` for the integration lock | E-03 explicitly excludes it: no reader wants a machine there, and it would add a hostname surface for the leak sanitizer for no benefit |
| F-10 | The terminal vocabulary has a narrow and a wide spelling | `TERMINAL_STATES_CANONICAL` versus `TERMINAL_STATES`, the latter being the union with `TERMINAL_STATUS_ALIASES` | E-04 must use the WIDE one; the narrow one would read a long-finished run's legacy token as unfinished and report a false holder |

## Proposed changes (ordered, validatable)

1. Re-derive the four facts and census every `driver.lock` and `pid=` record writer (E-01).
2. Record `host=<machine>` in the driver lock record, between the pid and the start time (E-02).
3. Add the truncation-tolerant reader for that field, excluding the integration lock (E-03).
4. Add the one three-valued plan-keyed holder predicate, reusing `peer_drivers` (E-04).
5. Implement D3's liveness order inside it, each arm failing closed with a named reason (E-05).
6. Add the behavioral test file covering the record round trip and every verdict arm (E-06).

## Deferred / out of scope (with reason)

- DELETING THE TOKEN, `verify_driver_attestation`, `mint_driver_attestation`, `DRIVER_ATTEST_ENV`, `lane_worktree_active`, and the two gate blocks that call them. Order 02's subject. Doing it here would leave this plan's own additions untested against the behavior they replace, and would put a deletion and an addition in one reviewable unit.
  - Carrier: e25iy9
- THE `--take-over '<reason>'` OVERRIDE AND ITS HISTORY RECORD. Order 02's subject, because the override only means something once a refusal exists to override.
  - Carrier: e25iy9
- THE LANE NUDGE. Order 03's subject. It is a print and not a refusal, and D1 is explicit that it is "NUDGE, never a refusal".
  - Carrier: m47znv
- CHANGING THE WORKER-LABEL CHECK (`worker_role_active`, `AW_EXECUTION_ROLE`, the `AW-LIFECYCLE-ROLE-001` refusal). D1 keeps it verbatim: it is the one honest mistake actually observed, and D2 requires it to run FIRST. Order 02 relocates where it is checked; this plan does not touch it.
  - Carrier: e25iy9
- A DURABLE MACHINE FIELD IN `state.json`. D3's fix is scoped to `driver.lock`, where the machine sits beside the pid it qualifies and is written under the lock that proves the writer is the holder. A second copy in `state.json` would be a fork of the same fact with no reader, which GUIDING_PRINCIPLES P6 forbids and F-9's reasoning independently argues against.
  - Carrier-Declined: Nothing is owed because there is no latent work. The one reader this design has is satisfied by the lock record, and filing an item would assert the repository intends a second home for a fact it already stores once.
- MAKING THE OS FILE LOCK WORK ACROSS NETWORK FILESYSTEMS. D3 records the honest limit that on a shared drive the lock may or may not work across machines depending on the filesystem. This plan does not attempt to fix that and does not need to: the recorded machine converts the case into an explicit UNDETERMINABLE, which Order 02 turns into a refusal with an override.
  - Carrier-Declined: Nothing is owed because this is a property of NFS, SMB and cluster filesystems rather than of this repository, and no code here could establish it. The design is safe without it by failing closed, which is stated as a limit rather than hidden.
- THE LANE OWNER RECORDS UNDER `.aw/worktrees/.owners/`. F-4 records why they are the wrong source for a plan-keyed question; D2 excludes them explicitly. They keep working unchanged for lane adoption, which is their actual job.
  - Carrier-Declined: Nothing is owed because they are correct for their own purpose and no defect was found in them. Filing an item would assert latent work where the measurement found a deliberate and documented separation.

## Scope check

- Over-scope: none. `agent_workflows/runner_shared.py` holds both the lock writer (E-02) and the new predicate (E-04/E-05). `tests/test_plan_holder_predicate.py` is the one new test surface (E-06).
- Under-scope: `agent_workflows/platform_lock.py` is NOT declared, and this is the one judgement a reviewer should check first. E-03 describes the reader as belonging beside `read_lock_record_pid`, which lives there, so if the executor implements it in that module the declaration is wrong and finalize's scope reconciliation will say so. The plan's position: measure first, and if the reader genuinely belongs in `platform_lock` (because it must reuse `read_lock_record`'s Windows-truncation handling, which is private to that module's contract), STOP and re-declare rather than absorbing the path silently. Neither `agent_workflows/ipd_lifecycle.py` nor either runner host is declared, because this plan adds no caller: Order 02 owns every call site. `agent_workflows/worktree_lease.py` is not declared; F-3 uses it as a precedent to copy, not a file to change. No spec path is declared: D8 measured that the token and the location guess are specified in NO spec, and the two specs that do need amending (`7ckptx`, `llbr2b`) are amended by Order 02, which is the plan that changes the refusal they describe.

## Required tests / validation

- `tests/test_plan_holder_predicate.py` is the plan's own surface and must cover the record round trip plus all three verdicts, including the queued-not-started HELD case, the foreign-machine UNDETERMINABLE case with its reason text, the legacy-record fallback, and the excluded-run-id case.
- THE MUTATION DEMONSTRATION IS REQUIRED, not optional, because a liveness test that passes against a predicate returning a constant is worthless. For each verdict assertion, break the implementation in the smallest way that should produce the wrong verdict (collapse UNDETERMINABLE into NOT HELD; drop the queued-status arm; ignore the machine comparison) and paste the resulting failure, then restore.
- The existing lock and run-record suites must still pass, since E-02 changes a record other readers parse. Name and run at minimum `tests/test_platform_lock.py` and the run-viewer and runner-shutdown surfaces, and paste their summaries: `test_platform_lock.py` writes literal `pid=... started=...` records and asserts on them, so it is the most likely place a record-shape change surfaces.
- The full suite, run BARE as `python3 -m pytest` (AGENTS.md), with the actual `N passed` summary line pasted. Do not add `-q` (it compounds with the configured one into `-qq` and suppresses the summary line this requires), do not pass `-n0`, and do not disable test-order randomization.
- A BASELINE IS REQUIRED BEFORE ANY EDIT: run the full suite first and paste that summary too, so a pre-existing failure is not attributed to this plan.

## Spec / documentation sync

- NO SPEC IS AMENDED BY THIS PLAN, and that is a measured claim rather than an omission. Backlog `dvonrn` D8 searched every `.spec.md` for the token (`AW_DRIVER_ATTEST`, `driver-attest`, "driver attestation"), the location guess (`lane_worktree_active`), the refusal code (`AW-LIFECYCLE-ROLE-001`), the role vocabulary and lifecycle ownership, and found the token and the location guess specified in NO spec. This plan additionally changes only an internal diagnostic record and adds an uncalled predicate, neither of which any spec describes. The two specs that DO need amending (`7ckptx` R4.5 and A11, `llbr2b` 3.2 and C-8) describe the REFUSAL, which Order 02 changes; they are declared and amended there, in the same change as the behavior, as AGENTS.md requires.
- `c4gd2h` (runner lifecycle, `implementing`) IS RE-READ AND EXPECTED TO NEED NOTHING. D8 records that its R2 ("driver.lock is released on completion of any level; a lock holding a dead PID is a defect") is CONSISTENT with D2 and needs no change. This plan's E-02 adds a field to that lock's record without changing when it is taken or released, so R2's subject is untouched. The executor re-reads it and says so explicitly in V-02; if E-02 turns out to contradict it, that is a scope change to stop and re-declare, not to absorb.
- NO CHANGELOG ENTRY. Nothing user-visible changes: the lock record is an internal diagnostic, and the predicate has no caller until Order 02. The Set's user-visible change is the replaced refusal, and Order 02 carries that entry.
- NO DOCUMENTATION UPDATE. The `driver.lock` record shape is described in module docstrings (`platform_lock`'s module header names the `pid=<n> started=<t>` shape, and `run_lock`'s docstring explains the duped descriptor), which E-02 and E-03 update as part of their own diffs. No file under `docs/` describes the record; the executor confirms this by search rather than assumption.

## Open questions

### OQ-01: Does the truncation-tolerant host reader belong in `platform_lock` or in `runner_shared`?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: The plan declares `runner_shared` and states the risk plainly in its Scope check rather than hiding it. The case for `platform_lock` is strong: `read_lock_record_pid` lives there, the Windows byte-0 truncation rule is that module's own contract (`read_lock_record`'s docstring owns it), and a sibling reader in a different module would have to re-derive it, which is the fork spec `7ckptx` R6.1 forbids. The case for `runner_shared` is that `host=` is a field THIS design invented and only this design reads, so putting it beside the general-purpose primitive widens a shared module for one consumer. NOT BLOCKING because the finalize scope reconciliation catches the wrong choice mechanically: an edit to an undeclared path is refused until the executor records it, so the worst case is a stopped item rather than a silent scope breach. E-01's census is the evidence that decides it, and the plan instructs the executor to stop and re-declare rather than absorb.
- Carrier-Declined: No carrier is owed under either answer. Both placements are fully realizable in this plan as written, the predicate's behavior is identical either way, and no deliverable goes unbuilt; only the declared path changes.

### OQ-02: Should UNDETERMINABLE distinguish "unreadable lock" from "foreign machine" in its verdict, or only in its reason text?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: This plan returns ONE UNDETERMINABLE verdict carrying a distinguishing reason string, rather than two verdicts, because D3 gives both arms the SAME consequence (refuse, with the `--take-over` override available) and a caller that must not branch differently should not be handed two tokens to branch on. The existing precedent agrees: `run_viewer` has one `HOLDER_UNKNOWN` covering both "no lock primitive on this platform" and "any OSError". Against that: Order 02's message for the foreign-machine case is specified by D3 to name the machine ("run <id> on machine <host> may still be working on this plan"), so it must recover that detail from the reason text rather than from the verdict, and text is a weaker contract than a token. NOT BLOCKING because the result type carries the machine as its own FIELD, so Order 02 composes its message from structured data and the reason text is diagnostic rather than load-bearing. If a reviewer prefers two tokens, that is an additive change to one enum and one test arm.
- Carrier-Declined: No carrier is owed. Both shapes are realizable within this plan, the refusal behavior Order 02 builds is identical under either, and nothing is left unbuilt by choosing one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted `run_lock` record string; the pasted search showing `state.json` carries no machine field; the pasted `_owner_is_live` foreign-machine arm; the pasted `LOCK_RECORD_PID_RE` regex with the `read_lock_record` sentence explaining the Windows byte-0 truncation; and the writer census naming every `driver.lock` writer and every `pid=` record composer, with each classified as a run driver lock or not. An explicit statement that no machine field already exists, or a STOP if one does.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the actual record read back from a lock acquired by `run_lock`, pasted, showing `pid=`, `host=` and `started=` with the machine matching `socket.gethostname()`; a demonstration that `RunLockHandle.release` still succeeds (its inode-identity check unbroken) and that the descriptor is still the duped locked one in the diff; and the re-read of spec `c4gd2h` R2 with an explicit statement that adding a field to the record does not affect when the lock is taken or released.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: three driven reads pasted, showing the machine recovered from a current record, None from a legacy `pid=<n> started=<t>` record, and the machine still recovered from a record whose first byte is blanked (the Windows-truncation shape `platform_lock`'s own test already constructs). Plus the diff proving `acquire_repo_scoped_lock`'s integration-lock record is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the predicate's signature and result type pasted, plus driven demonstrations of all three verdicts against real run directories. Must include the QUEUED-NOT-STARTED case returning HELD (D2's requirement, and the one most likely to be implemented wrongly) and the excluded-run-id case returning NOT HELD. Plus the pasted comment or code showing `TERMINAL_STATES` (the wide union) is the set consulted, with a driven case proving a legacy alias token reads as finished rather than as a live holder.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the four-input table (lock readable, machine same or different or absent, lock held, process exists) against the verdict, every row produced by DRIVING the predicate and not by reading its source. The foreign-machine reason string pasted verbatim, showing it names both the run and the machine so Order 02 can compose D3's message. An explicit statement that the unreadable-lock arm returns UNDETERMINABLE per the maintainer ruling, with the driven evidence or the recorded reason it had to be skipped on this platform.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the new test file's bare `python3 -m pytest` result pasted; the pre-edit full-suite baseline and the post-edit full-suite `N passed` line, both pasted from a bare run; the named lock and run-record suite summaries (`tests/test_platform_lock.py` at minimum, since it asserts on literal record text). Plus the mutation demonstration: for each verdict assertion, the pasted failure produced by breaking the implementation in the smallest way that should change that verdict, and confirmation the code was restored. Assertions must be on returned values and rendered text only; state explicitly that no test reads module source, censuses callers, or asserts which module defines a symbol.
  - THE ARMS E-06 MUST COVER, enumerated here so the test's obligation lives in one place and the executor can tick them off. All seven are required and each must be a separate case. (1) A lock actually acquired through `run_lock` reports the holder. (2) The same lock released reports NOT HELD. (3) A record naming a foreign machine reports UNDETERMINABLE with that machine named in the reason. (4) A legacy record with no `host=` falls through to the same-machine rule. (5) A queue entry whose status is merely queued reports HELD, which is D2's explicit requirement and the arm most likely to be implemented wrongly. (6) A queue entry whose status is terminal reports NOT HELD, including one carrying a legacy alias token. (7) Passing the holder's own run id as excluded reports NOT HELD. Plus the unreadable-lock arm, which reports UNDETERMINABLE where the platform can produce an unreadable file and SKIPS explicitly where it cannot.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the paths declared in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim; a summary you did not run is a fabrication. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change with `git restore --staged <path>`: this checkout is shared, and a failed raw commit can leave a co-worker's restored path in the index.

THIS PLAN MUST NOT CHANGE ANY REFUSAL. That is the single property a reviewer should check hardest, because it is what makes the plan safe to execute before Order 02. The predicate has NO caller when this plan finishes; the lock record gains a field that no gate reads yet. If you find yourself editing `ipd_lifecycle.py`, or deleting the token, or making any verb accept or refuse something it did not before, STOP: that is Order 02's work and doing it here defeats the Set's sequencing.

THE ONE THING NOT TO GET WRONG is the queued-not-started case. D2 states it explicitly: HELD includes an item merely WAITING to run, because otherwise a person finalizes the plan and the runner later picks it up again. An implementation that only considers a `running` item will pass a careless test and reintroduce the double-transition this design exists to prevent.

POST-GATE LIFECYCLE MOVE. Do NOT perform a hand-rolled terminal move. In a managed lane the runner performs `aw ipd begin` and `aw ipd finalize` and an in-lane invocation is refused by design; in an unmanaged or manual run the executor finalizes with `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` after `aw ipd lint --phase pre-transition` reports conforming and every `V-*` above carries concrete pasted evidence. Never `git mv` the plan and never hand-edit `- Status:`.
