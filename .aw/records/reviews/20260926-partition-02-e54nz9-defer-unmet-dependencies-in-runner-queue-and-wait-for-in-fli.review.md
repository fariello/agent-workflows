# Review findings: plan e54nz9

- Subject-Id: e54nz9
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | high | OVER-SCOPE | C (canonical mechanisms) | `oc_runipd.run_queue` selection loop "for item in sorted(queued, key=lambda it: queue_sort_key(it, by_id))"; `agy_runipd.run_queue` same | Original E-02 in-queue deferral re-implements behavior selection already has: a blocked item never delays independent work. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Maintainer ruling 2026-09-26 (asked): narrow to the peer wait. E-02 removed; convention recorded; F-4. |
| PR-002 | high | IN-SCOPE | A (correctness) / C | `runner_shared._peer_pid` ("DIAGNOSTIC ONLY, never a liveness signal"); `runner_shared.peer_drivers`; no pid key in 40 recent `state.json` | Original E-01 would read a PID field no run records and rebuild peer detection that exists, using the signal the code rejects as unsafe (PID reuse). | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | E-01 rebuilt on `peer_drivers` (`flock` liveness), `PEER_UNKNOWN` never starts a wait; F-5. |
| PR-003 | high | UNDER-SCOPE | G (executability) | `grep -n "^def run_queue"` -> `oc_runipd.py:3382`, `agy_runipd.py:2755`; no `run_queue_core` in `runner_shared` | Insertion points named functions that do not exist; the drain arm is per-host and both host modules were missing from Scope-Paths. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | E-03 wires both hosts' drain arms with one shared call; Scope-Paths extended; F-6. |
| PR-004 | medium | IN-SCOPE | A | status census over recent runs; no `attempting`/`verifying`/`merging` literal in `runner_shared` | Non-existent status names as the "in flight" test; a name list would also drift. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | "Held" is now "not in `TERMINAL_STATES`"; F-7. |
| PR-005 | medium | IN-SCOPE | C (time/failure) | item durations p50 17.0 / p90 46.7 min over 194 items; `INTEGRATION_LOCK_TIMEOUT_SECONDS = 1800.0` | 900s bound is shorter than a median item. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Bound 1800s, matching the existing peer-wait precedent; OQ-01 revised; F-8. |
| PR-006 | medium | UNDER-SCOPE | C / F (silent failure) / E | `runner_stop.poll_stop`; depblock `akzy45` drain-arm parity comment | No stop-awareness in a wait of up to 30 min, no event trail, no both-host test, no no-peer regression pin, no changelog. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | E-02 polls stop and emits start/end events; E-04 cases (e)-(g); E-05 changelog; F-9. |
| PR-007 | low | IN-SCOPE | G (execution contract) | original gate section | Gate lacked the scope-fence declaration, honesty rule, path-scoped commit, and conditional finalize ownership. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Gate rewritten with all elements. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | What bound should the peer wait use? | 1800s, 5s poll, 30s progress | 900s (author); unbounded | measured item durations (p50 17 min); `INTEGRATION_LOCK_TIMEOUT_SECONDS` | yes |
| D-2 | Does an UNKNOWN (unprobeable) peer start a wait? | No | Treat unknown as live | `peer_drivers` docstring: failing to prove liveness is not proof of death, and equally not proof of life; a wait must rest on a proven holder | yes |
| D-3 | Does the wait require a spec 25kzda 2.9 amendment? | No, satisfaction is unchanged; amend only if an executor reads 2.9 as forbidding a wait | Amend now | 2.9 governs satisfaction ("evaluated from frozen repository state"), which stays disk-authoritative via `edge_satisfied` | yes |
