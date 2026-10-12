# Review findings: plan masjx4

- Subject-Id: masjx4
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `eecf0c8f1`. The pending plan matched the sealed lane input byte for byte and was already committed, so no snapshot was needed. `aw ipd lint --phase author` reported `clean`. `- Kind: child`.

The cited symbols resolve: `runner_shared.StallWatchdog.__init__` (`self._last_activity = time.monotonic()`, `check_interval` clamp `timeout / 4.0`), `.touch`, and `._run` (`idle >= self.timeout`, which consults `progress_checker` before reaping); `oc_runipd` `StallWatchdog(process, timeout=stall_timeout)` with `watchdog.touch()` per stdout line; and `StallWatchdogTests` in `tests/test_oc_runipd.py`, with both tests and the cited child loop and `"0.5"` argument.

Rehearsal in the review lane, every edit reverted afterwards (`git status --short` clean):
- E-01 and E-02 applied: `2 passed in 7.03s`.
- Hardened test, `touch` made a no-op: `1 failed, 1 passed`, so it is falsifiable.
- Original test, `touch` made a no-op: `1 passed`, so it is vacuous today, confirming F2.
- 12 CPU burners and 20 concurrent runs: the hardened test passed 20 of 20, and so did the ORIGINAL test, so the recipe does not reproduce the flake on this host.
- `time.sleep(1.0)` injected after the child's imports: the hardened config gave `1 passed` and the original `0.5` config gave `1 failed`.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E (proof of fix) | Review load run: the ORIGINAL test passed 20/20 under 12 burners on a 12-core host | V-02(b)'s load recipe cannot show the fix addresses the defect, because the old test also passes it. The only discriminating evidence was missing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added V-02(d): a deterministic contrast where an injected 1.0s startup sleep fails the original 0.5s config and passes the hardened one, demonstrated at review. The load run is kept as supporting evidence only. Added F5 and F6. |
| PR-002 | MEDIUM | IN-SCOPE | E (evidence feasibility) | V-03 "bare full-suite run ... showing zero failures" | The repository suite may carry unrelated failures, which makes "zero failures" unsatisfiable or misleading. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now requires base and final summaries with an explicit empty failure-set delta, and no failure inside `StallWatchdogTests`. |
| PR-003 | MEDIUM | IN-SCOPE | G (execution contract) | Gate "Move this plan to `.aw/records/plans/executed/` only after ..." | The gate implied a hand move. It had no scope fence, no paste-actual-output rule, no staged-set check, and no conditional runner ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate as EXECUTION CONTRACT (sabotage edits never committed, burners killed), SCOPE FENCE, and POST-GATE LIFECYCLE. |
| PR-004 | LOW | UNDER-SCOPE | G (lifecycle gate) | Pre-transition lint would report `check.ipd-uncarried-obligation` for the two deferred rows | The deferred rows had no carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each. The uncarried count is now 0. |
| PR-005 | LOW | IN-SCOPE | Plan contract | OQ-01 `- Owner: none` | The owner was inaccurate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What proves the fix, given the load recipe does not reproduce the flake here? | A deterministic injected-startup-sleep contrast, with the load run as support. | Drop the load run; require more burners or runs until the old test fails. | Review rehearsal: the old test passed 20/20 under load, and the injected 1.0s sleep failed old and passed new. | yes |
| D-2 | Keep 3.0s and 8 x 0.5s? | Keep. | Larger margins. | Rehearsal passed under every condition tried, and OQ-01 already records the escalation rule. | yes |
