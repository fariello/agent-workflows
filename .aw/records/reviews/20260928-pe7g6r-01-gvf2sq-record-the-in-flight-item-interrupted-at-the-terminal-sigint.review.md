# Review: record the in-flight item interrupted at the terminal SIGINT rung instead of resetting it to queued, child gvf2sq (Set pe7g6r)

- Subject-Id: gvf2sq
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4b98aaa6`. `aw ipd lint --phase author --agent` reported `clean` BEFORE semantic
review and `--phase review-finalize --agent` after every revision. Every claim was re-measured by
driving the REAL `oc_runipd.execute_item` with the REAL `_terminal` message against temporary fixture
repositories, not read off the plan.

THE DIAGNOSIS IS CORRECT AND REPRODUCES EXACTLY. F-1: `tests/test_runner_stop_triggers.py` is deleted by
`19313eed`, so the item's node id is unrunnable. F-2: `reconcile_item_on_interrupt` has exactly one live
caller in `runner_shared.execute_item_core`'s `except KeyboardInterrupt as exc:` arm, and the baseline
`24 passed` reproduces. F-3: `_terminal` raises literally `stop level 4 (now-force) requested by signal
pid=<n>`, and `"just-terminate-no-cleanup" in msg` is `False`, so it falls to the default arm. F-4
reproduces end to end: clean tree leaves `status 'queued'` with events ending
`ipd-cleaned-up-no-changes`, zero attempts, no `stopped` record and no `ipd-interrupted`; the dirty tree
leaves `'interrupted'` with the `ipd-interrupted` event. F-5: `queued` is absent from
`TERMINAL_STATES_CANONICAL` (which does list `interrupted`), confirmed by direct membership test. F-7's
premise holds: `runner_stop._sigint` raises `KeyboardInterrupt("clean-up-and-terminate")` for
`INTERRUPT_ACTION_CLEANUP` (= 3) and `test_no_worktree_clean_repo_cleans_up` pins that arm. F-8 holds:
`grep` for `install_stop_triggers`, `install_stop_signal_handlers` and `SIGINT_LADDER` across `tests/`
returns nothing. Every cited symbol resolves. This is a real, correctly located, user-visible defect and
the author measured it honestly, including correctly refusing to re-fix the already-fixed `running` bug.

TWO FINDINGS CHANGE WHAT THE FIX MUST DO, and both were found by driving the surrounding code rather
than the defect.

FIRST, AND IT DEFEATS THE PLAN'S OWN STATED PURPOSE: E-02 PRESCRIBES `CERTAINTY_KNOWN`, WHICH LEAVES THE
R19 GATE JUST AS BLIND AS `queued` DID (PR-001). The plan's entire motivation, stated in its Concern, F-5
and OQ-01, is that `queued` bypasses `requeue_interrupted`'s spec-R19 indeterminate gate so a
force-stopped turn is re-run blindly. But that gate does NOT key on `status == "interrupted"`. It keys on
`runner_stop.is_indeterminate(item)`, whose entire body is
`item["stopped"]["certainty"] == CERTAINTY_INDETERMINATE`. Measured directly:
`is_indeterminate({"stopped":{"certainty":"known"}})` is `False`. So an item written `interrupted` with a
`CERTAINTY_KNOWN` record is flipped straight back to `queued` with `recovery_next = True` and re-run
blindly, which is the exact outcome the plan says it exists to prevent. The plan would have satisfied its
own tests (which assert only `interrupted` plus the event) while leaving the harm it documents in place.
The correct value is `CERTAINTY_INDETERMINATE`, and the repository already has the purpose-built
constructor for it: `runner_stop.forced_disposition`, whose docstring says it is "The INDETERMINATE record
for an item cut by a level-4 stop (spec R18, R21, R22)", sets `requires_reconciliation` and
`resume_action`, and deliberately refuses to invent a `last_completed_event`. Note this is not a
reviewer's preference over an author's: the plan's own F-6 argues that a level-4 force stop leaves the
outcome UNESTABLISHED, which is the definition of indeterminate, so the plan's prose and its prescribed
constant contradict each other. Fixed by re-specifying E-02 to build the record through
`forced_disposition` and by making V-02 and E-03 assert `is_indeterminate(item)` is True, which is the
assertion that actually proves the motivating harm is closed.

SECOND, A FOURTH RAISER WITH THE IDENTICAL DEFECT IS NOT MENTIONED ANYWHERE IN THE PLAN (PR-002).
`grep -rn "raise KeyboardInterrupt" agent_workflows/` returns FOUR sites, not three:
`render_stream.install_exit_signal_handler` raises `KeyboardInterrupt("Terminated by SIGTERM")`. That
string matches neither sentinel, so it takes the same destructive default arm, and I measured it with the
same probe: clean tree, `status 'queued'`, `ipd-cleaned-up-no-changes`, no `ipd-interrupted`, zero
attempts. It is not dead code: both hosts call `install_exit_signal_handler()` in `main`
(`oc_runipd.py:5064`, `agy_runipd.py:3974`). So a `kill <driver-pid>` during a turn silently discards
recovery state in exactly the way this plan exists to stop, and a sentinel installed only in `_terminal`
leaves it open. This is distinct from the deferred `wqk5s2` SIGTERM half, which is about a level-3 ladder
`KeyError: 'stopped'`; this is the SIGTERM *fallback handler* reaching the reconcile arm. The plan's own
E-01 rationale ("the message is the only channel `reconcile_item_on_interrupt` receives") applies verbatim.
Added as F-10 with the measurement, and handled by requiring E-01/E-02 to make the ROUTING robust for both
raisers, with the SIGTERM site either carrying the sentinel or being explicitly excluded with a reason.

A THIRD FINDING IS STRUCTURAL AND WOULD HAVE FAILED CI (PR-003). `aw check` reports
`check.ipd-uncarried-obligation` (severity `error`, deterministic) against THIS plan:
"4 obligation(s) name no durable carrier ... once this plan reaches `executed` it classes `done` in
`aw attention` and this vanishes with no record". All four `Deferred / out of scope` rows are prose only
and carry no `- Carrier:`, `- Carrier-Evidence:` or `- Carrier-Declined:` field. Two of them DO name an
id6 in prose (`wqk5s2`, `xuc9v0`), which is exactly the shape the rule exists to catch, since prose is
not machine-readable. One complication the plan could not have known it had: `xuc9v0` is `done`, so it
cannot serve as a carrier at all and that row needs a different disposition. Fixed by adding typed fields
to all four rows.

A FOURTH IS SMALL BUT OPERATOR-VISIBLE (PR-004). E-02 sets `attempt["interrupt_reason"]` to the sentinel
token itself. `render_stream` prints that value raw to an operator:
`diag_lines.append(f"  • {id6}: interrupted ({_interrupt_reason_of(it)})")`. A token chosen to be
machine-matchable (`unrequested-force-stop`) therefore becomes user-facing prose in a diagnostics block.
The existing arms happen to read acceptably (`clean-up-and-terminate`), so this is a real consideration
rather than a hypothetical; the plan now requires the executor to check how the chosen token renders and
says the reason field may carry human-readable text while the MATCH is on the constant.

Things I checked and did NOT raise. The shared-core placement is right: both hosts delegate to
`execute_item_core`, so `runner_shared` is the correct and only edit site, and no host file is needed.
The `attempt`-not-`item` placement of `interrupt_reason` is correct per `render_stream._interrupt_reason_of`'s
docstring. E-04's asymmetry argument is sound and its cited anchors exist (`INTERRUPT_ACTION_CLEANUP` at
`runner_stop.py:1797`, the pinning test at `tests/test_interrupt_reconcile.py:111`). `SUCCESS_STATES` exists
as cited. The decision to route on a sentinel in the message rather than by passing a typed parameter is
defensible given `reconcile_item_on_interrupt`'s existing signature takes `msg: str`, though I note in
passing that a typed argument would be strictly better; the plan's approach matches the two existing arms,
so consistency wins and I did not raise it as a finding. The deliberate exclusions (the `running` root
cause, the `wqk5s2` level-3 half, reviving the deleted file, the exit-130/143 mapping) are all correctly
scoped out.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness; D. Domain invariants | `agent_workflows/runner_stop.py:1543-1560` (`is_indeterminate` reads `stopped["certainty"] == CERTAINTY_INDETERMINATE`); `runner_stop.forced_disposition` at `:1463`; driven: `is_indeterminate({"stopped":{"certainty":"known"}})` -> `False` | E-02 prescribes writing the `stopped` record with `runner_stop.CERTAINTY_KNOWN`. The spec-R19 gate the plan cites as its ENTIRE motivation keys on `is_indeterminate`, i.e. on `certainty == "indeterminate"`, NOT on `status == "interrupted"`. So the fix as specified leaves the item flipped back to `queued` by `requeue_interrupted` and re-run blindly, which is precisely the harm F-5 and OQ-01 say it prevents. The plan's own F-6 (a level-4 stop leaves the outcome unestablished) contradicts its prescribed constant. The new tests as specified would have passed while the documented harm persisted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now builds the record through `runner_stop.forced_disposition` (the purpose-built level-4 indeterminate constructor, which also sets `requires_reconciliation` and `resume_action`) instead of a hand-built `CERTAINTY_KNOWN` dict; E-03 and V-02 now require asserting `runner_stop.is_indeterminate(item)` is True and that `requeue_interrupted` does NOT re-queue the item, which is the assertion that actually proves the motivation. F-5 extended to state the gate's real key. |
| PR-002 | HIGH | UNDER-SCOPE | A. Correctness; C. Architecture | `agent_workflows/render_stream.py:3486` (`raise KeyboardInterrupt("Terminated by SIGTERM")`); live callers `oc_runipd.py:5064` and `agy_runipd.py:3974`; driven with the same probe: clean tree -> `queued`, `ipd-cleaned-up-no-changes`, no `ipd-interrupted` | The plan treats the terminal rung as the only unsentinelled raiser. There are FOUR `raise KeyboardInterrupt` sites in `agent_workflows/`, and the fourth, `render_stream.install_exit_signal_handler`'s SIGTERM fallback, has the IDENTICAL defect and is live on both hosts. A sentinel added only inside `_terminal` leaves `kill <driver-pid>` silently discarding recovery state. Distinct from the deferred `wqk5s2` SIGTERM half, which is a level-3 ladder `KeyError`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-10 with the measurement; Scope's IN clause and E-01 now cover the routing for BOTH unsentinelled raisers, requiring the SIGTERM site to carry the sentinel or be excluded with a stated reason; E-03 requires a case driving the SIGTERM message; the `wqk5s2` deferral row now says explicitly which SIGTERM concern is NOT this one. |
| PR-003 | HIGH | IN-SCOPE | G. Executability; project rule (`check.ipd-uncarried-obligation`) | `aw check` -> `check.ipd-uncarried-obligation` (error, deterministic) on this plan: "4 obligation(s) name no durable carrier ... 4 row(s)/question(s) with no `Carrier`, `Carrier-Evidence`, or `Carrier-Declined` field"; `xuc9v0` resolves to `.aw/records/backlog/done/` | All four `Deferred / out of scope` rows are prose only with no typed carrier field, so the plan fails a deterministic repository check today and its deferred obligations would vanish from `aw attention` on execution. Two rows name an id6 in prose, which is exactly the unreadable shape the rule exists to catch. Additionally `xuc9v0` is `done` and therefore cannot serve as a carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Typed fields added to all four rows: `Carrier: wqk5s2` for the level-3 half; `Carrier-Declined` for the trim-revival row (a decision not to do work, nothing outstanding); `Carrier-Declined` for the slow-marker row, citing that `xuc9v0` is already `done` and this plan's own tests are the local mitigation; `Carrier-Declined` for the exit-code row (no obligation, unaffected by this change). `aw check` re-run clean for this plan after the edit. |
| PR-004 | LOW | IN-SCOPE | F. UX | `agent_workflows/render_stream.py:3447` (`f"  • {id6}: interrupted ({_interrupt_reason_of(it)})"`) | E-02 sets `attempt["interrupt_reason"]` to the raw sentinel token, and that value is printed verbatim to an operator in the diagnostics block. A token chosen for machine matching becomes user-facing prose. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires checking how the chosen value renders in that diagnostics line and permits the reason field to carry human-readable text while the MATCH stays on the shared constant; V-02 requires pasting the rendered diagnostics line. |

### Deferred and open

No finding is left `OPEN`, `DEFERRED`, or `REPLAN`, so `check.review-finding-unescalated` has nothing to
fire on and no `Blocking: yes` escalation is owed. The plan's own deferrals (level-3 `wqk5s2`, the trim,
the slow marker, the exit-code mapping) now carry typed carrier fields per PR-003 and are the PLAN's
deferrals, not unfixed review findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the level-4 `stopped` record carry `CERTAINTY_KNOWN` (as the plan wrote) or `CERTAINTY_INDETERMINATE`? | `CERTAINTY_INDETERMINATE`, built through `runner_stop.forced_disposition`. | (a) Keeping `CERTAINTY_KNOWN`, rejected because it provably leaves the R19 gate blind, defeating the plan's stated purpose; (b) changing `is_indeterminate` to also key on status, rejected outright because its docstring records that reading status instead of the explicit flag "would make the item inert" and it is "THE ONE PREDICATE every level-4 gate branches on", so widening it would change every level-4 gate at once; (c) hand-building an indeterminate dict, rejected because `forced_disposition` already exists for exactly this record and also sets `requires_reconciliation`/`resume_action`. | `runner_stop.is_indeterminate` body measured directly; `forced_disposition`'s docstring ("The INDETERMINATE record for an item cut by a level-4 stop (spec R18, R21, R22)"); the existing correct precedent at `runner_shared._record_forced_stop`, which the `StopNowForce` arm already uses for the deliberate level-4 path; the plan's own F-6. | yes |
| D-2 | Is the SIGTERM fallback raiser in scope, or a separate carrier? | In scope. It is the same defect, in the same reconcile arm, closed by the same routing change, and the plan's declared `Scope-Paths` already covers where the fix lands. | Filing a new backlog carrier, rejected because leaving it open would ship a fix whose own stated guarantee ("whatever the working tree looks like") is false for a live signal path on both hosts; folding it into `wqk5s2`, rejected because that item is about a level-3 ladder `KeyError`, a different mechanism. | `render_stream.py:3486` measured to take the destructive arm with the identical clean-tree outcome; `install_exit_signal_handler()` called in both hosts' `main`; `runner_stop.py:1980` documents SIGTERM's separate contract. | yes |
| D-3 | Should `reconcile_item_on_interrupt` keep routing on a message substring at all, rather than taking a typed parameter? | Keep the message routing for this plan. | A typed `reason`/`kind` parameter, which would be structurally better and unspoofable; rejected as out of scope here because the function's signature already takes `msg: str`, both existing arms route this way, and changing the contract would widen a high-risk interrupt-path fix into a signature change across its caller. Noted in the review prose rather than as a finding. | `reconcile_item_on_interrupt`'s signature and its two existing `in msg` arms; the plan's E-01 rationale that the message is the only channel available. | yes |
| D-4 | Does `xuc9v0` work as the carrier the slow-marker row implies? | No. That row takes `Carrier-Declined` with the reason stated. | `Carrier: xuc9v0`, rejected on measurement: it resolves to `.aw/records/backlog/done/`, and the rule requires an OPEN backlog item or a NON-TERMINAL plan, so a `done` item would be a dangling handoff claim. | `find .aw/records -name "*xuc9v0*"` -> `.aw/records/backlog/done/20260923-xuc9v0-01-xuc9v0-slow-marked-failures-invisible-by-default.backlog.md`; `check_engine`'s `_CARRIER_TARGET_TYPES` and finished-carrier handling. | yes |
