# Review findings: plan urv602

- Subject-Id: urv602
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
reports `clean` at `author` and `review-finalize` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator child-row check does not apply.

THIS IS A CAREFULLY EVIDENCED PLAN AND ITS ARCHITECTURE IS RIGHT. Every one of F-1 through F-9 reproduces
against the tree: `run_lock` writes exactly `f"pid={os.getpid()} started={utc_now()}\n"` through a duped
stream; `acquire_repo_scoped_lock` is a genuinely separate writer with a `holder_label` prefix, so E-02's
narrow scoping is correct; `worktree_lease._owner_is_live` really does return None when
`host and host != socket.gethostname()` with the comment the plan quotes; `peer_drivers` really does resolve
through `runs_repo_root` and preserve `PEER_UNKNOWN`; and `peer_held_prerequisites` really is keyed on
unsatisfied `executed:` edges and answers nothing about a plan. The decision to add ONE predicate rather
than three inline copies is correct and correctly grounded in spec `7ckptx` R6.1. The deferral rows are
honest, each declining a carrier with a reason rather than parking work.

BUT THE PREDICATE'S CENTRAL RULE WOULD HAVE BEEN WRONG, AND WRONG IN THE EXACT DIRECTION THAT DEFEATS THE
SET. That is PR-001. E-04 instructed HELD as "a status NOT in `TERMINAL_STATES`". Measured:
`'interrupted' in TERMINAL_STATES` is **True**, and so is `'interrupted' in TERMINAL_STATES_CANONICAL`. So
an INTERRUPTED item reads NOT HELD. An interrupted item is not finished: `interrupt_item` sets
`item["recovery_next"] = True`, `runner_shutdown.KNOWN_ITEM_STATUSES` lists `interrupted` under its own
`# in-flight / recoverable` banner beside `queued` and `running`, and `requeue_interrupted`'s docstring
records that `run_queue` calls it "UNCONDITIONALLY on every start and every resume" to flip such items back
to `queued`. So the predicate would have told Order 02 "nobody is working on this plan" about a run that is
about to resume and pick it up, a person would transition the plan, and the runner would transition it
again. That is precisely the double-transition this Set exists to prevent, reintroduced by the gate built
to stop it.

The fix is not to swap one set for another, because BOTH candidate sets contain `interrupted`. E-04 now
specifies an explicit in-flight ALLOWLIST (`queued`, `running`, `interrupted`, `integration-deferred`,
`merge-retry`, derived from that `# in-flight / recoverable` banner), and treats an UNRECOGNIZED status as
UNDETERMINABLE rather than NOT HELD, so a status added later fails closed instead of silently opening a
hole. I kept the plan's F-10 reasoning rather than deleting it, because its comparison of the wide and
narrow sets is sound and only its conclusion was unusable for this question; E-04 now records why a
`TERMINAL_STATES` membership test must not be reintroduced as a simplification.

THE SECOND REAL DEFECT IS INHERITED, NOT AUTHORED, WHICH IS WHY IT WAS EASY TO MISS (PR-002).
`peer_drivers` wraps its discovery in `except Exception: return []`, and its own comment justifies that
precisely: "An unreadable runs tree is not evidence of solitude, but it is also not a peer we can name ...
the caller never REFUSES on this query, so a failure costs a missing report line and never a run." This
plan's predicate BREAKS that stated premise, because Order 02 refuses on its answer. Building on
`peer_drivers` as instructed would turn an unreadable runs tree into NOT HELD and silently permit the gated
transition. E-05 now requires discovery failure to surface as UNDETERMINABLE, while explicitly NOT changing
`peer_drivers`' contract for its existing callers (whose dependence on never refusing is legitimate), and
E-06 arm (11) pins it. This is a good example of why "reuse the existing machinery" needs the reused
function's FAILURE shape checked, not only its success shape.

A MANDATED IMPLEMENTATION DETAIL RESTED ON A FALSE PREMISE (PR-003). E-03 required the host reader to
tolerate a missing leading byte "in the same way `LOCK_RECORD_PID_RE` is" and FORBADE a naive
`split("host=")`. But the Windows mandatory lock loses only BYTE 0 (`read_lock_record`'s fallback seeks to
offset 1), and E-02 places `host=` between `pid=` and `started=`, so the `h` of `host=` is never at byte 0.
Measured: the forbidden `split("host=")` recovers `mybox` correctly from both `pid=1234 host=mybox
started=t` and its truncated form `id=1234 host=mybox started=t`. So the mandate was dead code and the
prohibition was unfounded. I did not simply delete the requirement: E-03 now permits either form, forbids
CLAIMING the tolerance is load-bearing (a false rationale a later author would preserve), states the real
invariant (`host=` is not the first field), and names the coupling if a future change moves it there.

I ALSO ADDED THE COMPATIBILITY CHECK THE PLAN DID NOT ASK FOR (PR-004), which is the risk E-02 actually
carries. Inserting a field into a record that every existing lock-record consumer parses could shadow
`LOCK_RECORD_PID_RE` (`r"(?<!\w)p?id=(\d+)"`, a SEARCH). I measured it across the legacy record, the new
record, the truncated new record, an fqdn host, a hyphenated host, a host containing digits, a host
literally containing `id=`, and the integration-lock record: the pid is recovered correctly in every case.
So the change is safe, and E-03/E-06 now require re-deriving that rather than assuming it, because a silent
break here would affect every consumer rather than only this design.

ONE STALE IN-TREE COMMENT WILL ACTIVELY MISLEAD THE EXECUTOR (PR-005), so I named it rather than leaving it
to be discovered. The comment beside `NEEDS_INPUT_TOKEN` asserts "`interrupted` is already precedent for a
status the runner uses that is absent from that set (measured: `'interrupted' in TERMINAL_STATES` ->
False)". That is FALSE at this HEAD; `interrupted` entered the canonical set via `6b94a4d9d` "statusvocab:
rename the terminal status vocabulary so a label names its refusing authority". An executor who trusts it
over their own measurement reintroduces PR-001. I deliberately did NOT fix the comment: it belongs to the
statusvocab owner, and editing it is outside what this plan is for. E-01 now names it and instructs the
executor not to let it override their measurement.

BOTH OPEN QUESTIONS WERE ADDRESSED TO THE REVIEWER, SO I ANSWERED THEM RATHER THAN LEAVING THEM OPEN, and
both are recorded as decisions below. OQ-01 (where the host reader lives) turned out to be decided by
PR-003: its argument for `runner_shared` rested on the truncation coupling that does not exist, so with that
removed the reader is a plain sibling accessor over a record format `platform_lock` already documents, and
splitting two accessors of one format across two modules is the fork shape R6.1 warns about. I declared
`agent_workflows/platform_lock.py` in `- Scope-Paths:` so the choice needs no stop-and-re-declare. OQ-02
(one UNDETERMINABLE verdict or two) I RATIFIED as the plan had it, on the plan's own reasoning plus
`run_viewer`'s single `HOLDER_UNKNOWN` precedent, with one strengthening: the result must carry a
machine-readable REASON CODE, because this review took the undeterminable causes from three to five and
free-text discrimination is a weak contract for a refusing caller to parse.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness) / D (anti-regression) | Measured `'interrupted' in TERMINAL_STATES` -> True (and in `TERMINAL_STATES_CANONICAL` -> True); `runner_shared.interrupt_item` `item["recovery_next"] = True`; `runner_shutdown.KNOWN_ITEM_STATUSES` `# in-flight / recoverable` banner; `runner_shared.requeue_interrupted` docstring "UNCONDITIONALLY on every start and every resume" | **E-04'S HELD RULE WOULD REPORT A LIVE, RESUMABLE HOLDER AS ABSENT, REINTRODUCING THE EXACT DOUBLE-TRANSITION THE SET EXISTS TO PREVENT.** E-04 instructed HELD as "status NOT in `TERMINAL_STATES`". `interrupted` is IN that set, yet an interrupted item carries `recovery_next = True` and is flipped back to `queued` by `requeue_interrupted` on every start and resume. So the predicate would answer "no live run is working on this plan" about a run about to resume it; a person then transitions the plan and the runner transitions it again. Neither candidate set is usable, since both contain `interrupted`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now specifies an explicit in-flight ALLOWLIST (`queued`, `running`, `interrupted`, `integration-deferred`, `merge-retry`) derived from the `# in-flight / recoverable` banner, treats an UNRECOGNIZED status as UNDETERMINABLE so a later addition fails closed, and records why a `TERMINAL_STATES` membership test must not be reintroduced. F-10 corrected and new F-11 records the measurement. E-01 re-derives it with a STOP if the vocabulary moved; E-06 arms (8)(9)(10) pin interrupted, the other in-flight statuses, and the unrecognized case; V-04 demands the measurement pasted beside the allowlist; the gate names it as a trap. |
| PR-002 | HIGH | IN-SCOPE | A / C (operability) | `runner_shared.peer_drivers` `except Exception: ... return []` and its comment "the caller never REFUSES on this query, so a failure costs a missing report line and never a run" | **BUILDING ON `peer_drivers` INHERITS A FAILURE SHAPE THAT IS UNSAFE FOR A REFUSING CALLER.** `peer_drivers` returns `[]` on ANY discovery failure by deliberate design, justified in-code on the premise that no caller refuses on its answer. This plan breaks that premise: Order 02 refuses. So an unreadable runs tree would arrive as an empty peer list, read as NOT HELD, and silently permit the gated transition. The plan instructed reuse without accounting for it. | C:Low; U:Medium; S:Low; F:Low; Overall:Medium | FIXED | E-05 now requires the predicate to distinguish "discovery succeeded, no holder" from "discovery failed" and return UNDETERMINABLE for the latter, either by surfacing the failure in its own discovery (still reusing `runs_repo_root` and `driver_holder_state`, so neither resolver nor liveness rule is forked) or via a variant, and explicitly NOT by changing `peer_drivers`' contract for its existing callers. New F-12 records it; E-01 measures the failure arm; E-06 arm (11) and V-05 pin the UNDETERMINABLE outcome; the gate names it as a second trap. |
| PR-003 | MEDIUM | IN-SCOPE | A / F (honest documentation) | `platform_lock.read_lock_record` (fallback `stream.seek(1)`); measured `split("host=")` recovering `mybox` from both `pid=1234 host=mybox started=t` and `id=1234 host=mybox started=t` | **E-03 MANDATED A TOLERANCE THAT IS DEAD CODE AND FORBADE AN IMPLEMENTATION THAT WORKS, on a false premise.** It required the host reader to tolerate a missing leading byte "in the same way `LOCK_RECORD_PID_RE` is" and forbade a naive split. But only byte 0 is lost, and E-02 places `host=` after `pid=`, so the host token is never truncated. Left unfixed, the plan would have recorded a false rationale into a docstring and a later author would have preserved it as load-bearing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now permits either implementation (regex preferred for symmetry, NOT for correctness), forbids claiming the tolerance is load-bearing for `host=`, states the real invariant (`host=` is not the first field) and names the coupling if a future change moves it to the front. F-8 corrected with the measurement; the authoring history line carries a dated inline correction so the record is not silently rewritten. |
| PR-004 | MEDIUM | UNDER-SCOPE | D (anti-regression) | `platform_lock.LOCK_RECORD_PID_RE` = `r"(?<!\w)p?id=(\d+)"`; measured across 8 record shapes | **THE PLAN NEVER REQUIRED CHECKING THAT E-02'S RECORD CHANGE LEAVES THE EXISTING PID READER WORKING,** which is the one real compatibility risk it carries, since every existing lock-record consumer parses that record. Measured clean (legacy, new, truncated new, fqdn host, hyphenated host, host with digits, host containing `id=`, integration-lock record all recover the pid correctly), but an unverified assumption here would break consumers far outside this design. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires re-deriving the pid-reader compatibility across those shapes; E-06 requires a test asserting `read_lock_record_pid` still recovers the pid from the new record and its truncated form; new F-13 records the measurement. |
| PR-005 | LOW | IN-SCOPE | F | Comment beside `runner_shared.NEEDS_INPUT_TOKEN`: "measured: `'interrupted' in TERMINAL_STATES` -> False"; contradicted by measurement; `interrupted` added to the canonical set by `6b94a4d9d` | **A STALE IN-TREE COMMENT ASSERTS THE OPPOSITE OF PR-001'S MEASUREMENT AND SITS IN THE FILE E-04 EDITS.** An executor who trusts it over their own measurement reintroduces the BLOCKER, and the comment is persuasive because it presents itself as measured. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now names the comment, quotes it, records that it is false at this HEAD with the commit that made it so, and instructs the executor not to let it override their own measurement. New F-14 records it. DELIBERATELY NOT corrected in code: it belongs to the statusvocab owner and is outside this plan's purpose; recorded so the next reader is not misled. |
| PR-006 | LOW | IN-SCOPE | G (execution contract) | Plan `## Approval and execution gate` as authored | **THE GATE LACKED SCOPE-FENCE RECONCILIATION SEMANTICS.** It stated path-scoped commit, never-push, the honesty rule and the lifecycle move correctly (including the conditional runner/executor ownership, which is right), but said nothing about what to do when an out-of-scope edit proves necessary, leaving an executor to infer a stop where the 2026-09-01 ruling requires make-and-justify. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now states the fence as a declaration reconciled at `aw ipd finalize` with `--scope-reason`, and `--scope-ack` for a declared path left unmodified (naming `platform_lock.py` as the live case), while keeping the plan's genuine stop conditions (changing a refusal; E-01's premise failures) stated separately, which the ruling preserves as a different case. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-04's `not in TERMINAL_STATES` rule misreports a resumable `interrupted` item as absent. What replaces it? | An explicit IN-FLIGHT ALLOWLIST (`queued`, `running`, `interrupted`, `integration-deferred`, `merge-retry`), with an unrecognized status returning UNDETERMINABLE. | (a) Use `TERMINAL_STATES_CANONICAL` instead: REJECTED, it also contains `interrupted`, so it fails identically. (b) Keep `not in TERMINAL_STATES` and special-case `interrupted`: REJECTED, it leaves the same latent trap for the next in-flight status added and encodes no reason. (c) Add `interrupted` to a new "unfinished" set derived by subtraction from `TERMINAL_STATES`: REJECTED, a subtraction fails OPEN (a newly added terminal-ish token silently becomes a non-holder), which is the unsafe direction for a gate. (d) Treat ANY status as HELD unless provably `executed`: REJECTED as too wide, it would report a `fail-gate` or `not-run` item as a live holder and refuse legitimate transitions. | Measured `'interrupted' in TERMINAL_STATES` and `... in TERMINAL_STATES_CANONICAL` both True; `runner_shutdown.KNOWN_ITEM_STATUSES`' own `# in-flight / recoverable` banner enumerates exactly the five; `interrupt_item` sets `recovery_next = True`; `requeue_interrupted` is called unconditionally on every start and resume per its docstring. | yes |
| D-2 | `peer_drivers` returns `[]` on discovery failure. Reuse it as instructed, or change the approach? | Do NOT read an empty list as absence; surface discovery failure as UNDETERMINABLE, without changing `peer_drivers`' own contract. | (a) Reuse as instructed: REJECTED, it converts an unreadable runs tree into NOT HELD and silently permits the gated transition, which is the failure the Set exists to prevent. (b) Change `peer_drivers` to raise or return a tri-state: REJECTED as an unrequested contract change to a function whose existing callers legitimately depend on never refusing, and whose in-code comment states that dependence. (c) Write a fully independent discovery: REJECTED, it would fork `runs_repo_root` and the liveness rule, which spec `7ckptx` R6.1 forbids and which F-7's lane-resolution hazard makes actively dangerous. | `peer_drivers`' `except Exception: return []` and its comment "the caller never REFUSES on this query"; Order 02 refuses on this predicate's answer per the plan's own Concern and D4; `runs_repo_root`'s docstring recording 0-vs-246 run dirs from a lane. | yes |
| D-3 | OQ-01: does the host reader belong in `platform_lock` or `runner_shared`? | `platform_lock`, beside `read_lock_record_pid`; `agent_workflows/platform_lock.py` declared in `- Scope-Paths:`. | `runner_shared`: REJECTED once PR-003 removed its premise. The case for it was that the reader needs `read_lock_record`'s private Windows-truncation handling, making it a coupling question; measured, `host=` is never truncated, so there is no private contract to inherit and the reader is a plain sibling accessor. Leaving it undeclared and asking the executor to stop-and-re-declare: REJECTED, the question was addressed to the reviewer, and resolving it costs one declared path while a stop costs an execution round trip. | `read_lock_record_pid` and the new reader parse the SAME record through the SAME `read_lock_record` primitive; `platform_lock`'s module header already documents the `pid=<n> started=<t>` shape that E-02 changes; spec `7ckptx` R6.1 on not splitting one rule across surfaces. | yes |
| D-4 | OQ-02: one UNDETERMINABLE verdict or two (unreadable lock vs foreign machine)? | ONE verdict, RATIFYING the plan's choice, plus a required machine-readable REASON CODE field. | Two verdicts: REJECTED on the plan's own sound reasoning (D3 gives both arms the same consequence, and `run_viewer`'s single `HOLDER_UNKNOWN` already collapses "no lock primitive" and "any OSError") plus the R6.1 concern that two tokens invite divergent handling in three call sites. Leaving discrimination to the free-text reason alone, as authored: REJECTED, this review took the undeterminable causes from three to five (adding discovery failure and unrecognized status), and prose is a weak contract for a refusing caller to parse. | D3's identical consequence for both arms; `run_viewer.driver_holder_state`'s single `HOLDER_UNKNOWN` docstring covering both causes; the plan's own requirement that the result carry the machine as a field; the two causes this review added (F-12 and E-04's unrecognized-status arm). | yes |
| D-5 | Verdict and readiness, given one BLOCKER and one HIGH both now fixed and no blocking open questions. | `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`. | `REJECT - NEEDS REPLAN`: REJECTED, the plan's architecture is sound and both serious findings were repairable with bounded edits to the rule and the discovery shape, which is the documented test for REPLAN; nothing about the Set's sequencing or the one-predicate design needed rethinking. `REVIEWED - OPEN QUESTIONS`: REJECTED, both OQs are now `resolved`. Bare `NO-GO`: REJECTED, the workflow reserves it for genuine not-ready conditions and says a reviewed clean plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL`. | Workflow readiness vocabulary; the 2026-09-10 maintainer ruling (plan `qhy3i3` OQ-01) that a non-blocking open question does not force `no-go`; zero findings left OPEN or DEFERRED at or above the `high` gate threshold, so no escalation to a `Blocking: yes` question is owed; `aw ipd lint` clean at `author` and `review-finalize`. | yes |
