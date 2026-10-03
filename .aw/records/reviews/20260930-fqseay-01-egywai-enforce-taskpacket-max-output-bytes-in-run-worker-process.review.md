# Review findings: plan egywai

- Subject-Id: egywai
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `13b124b59`. The plan file was committed and the tree
clean (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE any edit;
`--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:` bullet
reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

I RE-DERIVED EVERY LOAD-BEARING MEASUREMENT INDEPENDENTLY rather than trusting the plan's findings,
and ALL TWELVE authoring findings reproduce. The plan's diagnosis is excellent and the correction it
makes of its own backlog item (that the item's "missing keyword" framing hides a regression) is its
real contribution:

- F-01 reproduces to the byte: a `TaskPacket` declaring `max_output_bytes=100` against
  `print('A'*50000)` returned `exit 0`, `len(stdout) == 50001`, `len(stderr) == 0`.
- F-02 reproduces: `capture_command` with `max_output_bytes=10` records `stdout_len 10`,
  `truncated True`, `max_bytes 10`, so the producer side genuinely needs no change.
- F-03 reproduces decisively, and it is the finding that justifies the plan's shape: the bounded
  record gave `gate ok=False` with the single finding `EV-TRUNCATED-OUTPUT`, and
  `host_launchers.host_result_can_finalize(raw, bounded_event)` returned
  `(False, 'evidence gate rejected: EV-TRUNCATED-OUTPUT')`.
- F-04 reproduces: `stdout_len 10` against `stderr_len 100` under one bound. (Note `emzbut` F-09
  recorded `stderr_len 101` for the same probe; I measured 100, matching THIS plan. The difference is
  a trailing newline in the other plan's command, not a contradiction in either.)
- F-05 reproduces: the `RunnerFn` branch returned 50000 unbounded bytes under a declared bound of 100.
- F-06 reproduces: `rg -ln` over `tests/` returns only `tests/test_hostdedup_third_host.py`, whose
  `host_runner_map` hits are a local dict unrelated to the module; `grep -rn "TaskPacket("` outside
  `.aw/` returns only the class definition; `host_launchers` has no importer.
- F-07 reproduces both halves: the `_fields` tuple is exactly as quoted with no truncation signal, and
  a `RawWorkerResult` with `stdout=""` plus a real diff classifies `completed`, which is what makes
  "do not touch `classify_worker_state`" correct.
- F-09 reproduces exactly, and the plan's literal strings are right: through the REAL
  `capture_command`, bound 6 gives `'AAAAA\ufffd'` and bound 7 gives `'AAAAAé'`, the same two values
  the `encode -> slice -> decode(errors='replace')` arithmetic produces, so both branches will agree.
  The re-encode-larger wart reproduces (`'é\ufffd'` from a 3-byte bound re-encodes to 5) and so does
  idempotence.
- F-10 reproduces: bound `0` yields `stdout_len 0`, `truncated True`, and BOTH `EV-MISSING-OUTPUT` and
  `EV-TRUNCATED-OUTPUT`; bound `-5` yields `stdout_len 6` with `truncated True`.
- F-12 reproduces: `rg -rln` over `.aw/records/specs/` returns nothing for `max_output_bytes`,
  `host_runner` or `TaskPacket`, and the one `7ckptx` hit is a timeout-naming sentence.
- F-08 reproduces: `emzbut` is `- Status: approved`, declares `agent_workflows/host_runner.py` in its
  `- Scope-Paths:`, and its E-04 text really does say "DO NOT FORWARD `packet.max_output_bytes` HERE
  ... it is carried to `fqseay`". Both carriers resolve and both gates are intact: `lijmwy` is `open`
  with `- Blocks-Release: next`, and `fqseay` is already `graduated` with the same gate.

PR-001 IS A BLOCKER AND IT IS A DEFECT IN THE PRESCRIBED FIX, NOT A DOCUMENTATION GAP. E-03 told the
executor to give `evidence_gate` a new `declared_bound: Optional[int] = None` keyword, and E-05 then
demanded that `host_launchers.host_result_can_finalize` return `(True, ...)` for a completed bounded
worker. Those two requirements are mutually unsatisfiable under the declared scope.
`host_result_can_finalize` is the ONLY caller of `evidence_gate` anywhere in the tree (verified:
`grep -rn "evidence_gate" --include=*.py agent_workflows/ tests/` yields exactly one non-definition
hit), it calls `_hr.evidence_gate(tool_event)` with a single positional argument, and
`agent_workflows/host_launchers.py` is NOT in `- Scope-Paths:`. I implemented the keyword exactly as
E-03 specified and measured all three surfaces: the direct gate returned `ok=True` with
`declared_bound=100` and `ok=False` without it, while `host_result_can_finalize` STILL returned
`(False, 'evidence gate rejected: EV-TRUNCATED-OUTPUT')`. So the plan could not have satisfied its own
V-05 without an undeclared fourth file edit, and an executor would have discovered that only after
writing E-01 through E-04.

The remedy was DEMONSTRATED rather than proposed. `run_evidence.build_tool_event` already writes
`if max_bytes is not None: rec["max_bytes"] = int(max_bytes)`, and `capture_command` passes
`max_bytes=max_output_bytes`, so key PRESENCE is exactly the caller-declared-a-bound signal (F-14,
measured: present with value 100 under a bound, absent entirely without one). I implemented
`evidence_gate` reading that key and measured: (a) bounded with `max_bytes` present -> `ok=True`, no
findings; (b) the same record with the key deleted -> `ok=False`, `['EV-TRUNCATED-OUTPUT']`; (c) bound
`0` -> `ok=False`, `['EV-MISSING-OUTPUT', 'EV-TRUNCATED-OUTPUT']`; (d) nonzero exit under a bound ->
`ok=False`, `['EV-FAILED-EXIT']`; and `host_result_can_finalize` -> `(True, 'completed with a verified
side effect')` with `host_launchers.py` untouched. E-03, its Expected outcome, E-05's case list, V-03,
V-05, OQ-01 and the scope-check paragraph were all rewritten to this mechanism, and OQ-01 now carries
the rejected keyword as a fourth enumerated option with the measurement that killed it.

I was careful that this is NOT OQ-01's already-rejected option (2), and the plan now says why: option
(2) put the exemption inside the SHARED `validate_evidence`, where every caller inherits it and any
producer setting `max_bytes` exempts itself. The chosen form puts it in the CONSUMER, so it applies
only where `require_full_output=True` was opted into, and `evidence_gate` is the only
`validate_evidence` call in `host_runner.py`. The honest cost is recorded in the plan: the gate now
trusts a record field rather than a caller's parameter, which is a real trust shift and is the price
of reaching the only production caller without widening scope.

PR-003 is the kind of staleness that actively misleads. F-11 recorded a pre-existing suite failure
(a midnight date-rollover flake in `test_release_exempt_setter_roundtrip_and_parity`) and the plan
told the executor in THREE places to expect it and not fix it. Re-measured at review on a clean tree,
a bare `python3 -m pytest` reports `3610 passed, 2 skipped, 3 warnings in 198.71s` with 208
deselected: fully green, and 153 tests larger than at authoring. The flake was exactly the
date-boundary artifact F-11 diagnosed and it has since passed. Left standing, the instruction would
license an executor to wave through a real regression. F-11 is now marked superseded (kept so its
reasoning stays auditable), F-15 records the new measurement, and the Project-conventions bullet,
Required tests and V-05 all demand a re-derived baseline against a green bar.

PR-002, PR-004 and PR-005 are smaller. E-05's case (b) said "the same record with NO declared bound",
which an executor could reasonably implement by capturing WITHOUT a bound: that record is not
truncated at all, so it would pass the gate for the wrong reason and prove nothing; the item now
mandates deleting the one key from a real bounded record, which is the shape I measured. E-01's
instruction to check "the three `_replace` sites" is right for `RawWorkerResult` but a grep returns a
FOURTH hit, `host_launchers.resume_task_packet`, which operates on a `TaskPacket` and names its
fields; the item now names it so the extra hit is not mistaken for a missed site. And the gate was
missing three Step 4 elements (an open-questions statement, a scope fence, and the conditional
runner/executor finalize ownership, where it previously implied the executor always transitions), all
added in place.

TWO THINGS I DELIBERATELY DID NOT CHANGE. F-08's reasoning that `- Item-Dependencies:` is correctly
`none` holds: the two edits are behaviorally independent, the risk is textual, and the `truncated`
read is a MAPPING key that survives `emzbut`'s move of the TEXT out of the mapping, which I confirmed
by reading that plan's E-04. And the deliberate stderr asymmetry is correctly scoped out: the plan
pins it with a test so `lijmwy`'s owner sees the expectation fail knowingly, which is the right
treatment for a bound that will still cover only half the capture after this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | G (executability) / A (correctness) | `agent_workflows/host_launchers.py` `host_result_can_finalize`, the call `ev = _hr.evidence_gate(tool_event)`; the plan's E-03 and E-05 | E-03's prescribed `declared_bound=` keyword cannot reach `evidence_gate`'s only caller, which passes one positional argument and lives in a file outside `- Scope-Paths:`, so E-05's required `host_result_can_finalize` -> `(True, ...)` was unreachable and the plan contradicted its own validation | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now reads the declaration off the record's `max_bytes` key (demonstrated at review: all four gate cases correct and the finalize path passing with `host_launchers.py` untouched); rewrote E-03, its Expected outcome, E-05, V-03, V-05, OQ-01 and the scope check; added F-13 and F-14 |
| PR-002 | MEDIUM | IN-SCOPE | E (testing) | the plan's E-05 case (b) | "the SAME truncated record with NO declared bound" is satisfiable by capturing without a bound, which produces an untruncated record that passes the gate for the wrong reason and proves nothing about the narrowing | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now mandates building case (b) by deleting `max_bytes` from a real bounded record, the shape measured at review; V-05 demands the code be quoted to confirm it |
| PR-003 | MEDIUM | IN-SCOPE | E (testing) / G (live-artifact criteria) | the plan's F-11, its Project-conventions baseline bullet, Required tests, and V-05 | F-11 pre-authorizes a suite failure that no longer occurs; re-measured the suite is fully green (`3610 passed, 2 skipped`), so the standing instruction to expect and ignore a failure would license waving through a real regression | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Marked F-11 superseded (kept for auditability), added F-15 with the re-measurement, and corrected all three executor-facing instructions to demand a re-derived baseline against a green bar |
| PR-004 | LOW | IN-SCOPE | G (executability) | `agent_workflows/host_launchers.py` `resume_task_packet`; the plan's E-01 | E-01 tells the executor to check "the three `_replace` sites", but a tree-wide grep returns four; the fourth is on `TaskPacket` and is unaffected, and an executor could read the mismatch as a missed site | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now names the fourth site, states it operates on a `TaskPacket` and names its fields, and says to check it so the extra grep hit is expected |
| PR-005 | MEDIUM | UNDER-SCOPE | G (execution contract) | the plan's "Approval and execution gate" section | the gate lacked an open-questions statement and a scope fence, and its lifecycle sentence instructed the executor to perform the terminal transition unconditionally, omitting that a runner owns the finalize when one is driving | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the open-questions statement, a declaration-style scope fence naming the two excluded files and the genuinely-unsafe stop conditions, the explicit `Status`/`Readiness` statement, and conditional runner/executor finalize ownership |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-03's keyword mechanism is unreachable from the only caller; fix the mechanism in-plan, add `host_launchers.py` to Scope-Paths, or escalate to the maintainer? | Fix the mechanism in-plan: read `max_bytes` off the record | Add `agent_workflows/host_launchers.py` to `- Scope-Paths:` and pass the keyword there; escalate as a blocking question on which mechanism the maintainer prefers | The alternative mechanism is strictly smaller (no second file, no signature change) and I DEMONSTRATED it end to end rather than reasoning about it: all four gate cases behave correctly and `host_result_can_finalize` returns `(True, 'completed with a verified side effect')` with `host_launchers.py` untouched. The declaration was already persisted by `build_tool_event`'s `max_bytes` branch, so nothing new is invented. Widening scope to a third file to rescue a keyword that buys only explicitness would be the larger change | yes |
| D-2 | Does the trust shift (gate trusts a record field rather than a caller parameter) need a maintainer ruling? | No; proceed and record the cost explicitly in OQ-01 and the gate section | Raise a blocking open question asking the maintainer to choose between the two mechanisms | The shift is bounded and auditable: the exemption fires only when `EV-TRUNCATED-OUTPUT` is the sole finding, `max_bytes` is written only from `capture_command`'s own parameter, and the exemption lives in the single consumer rather than the shared validator, so no other caller inherits it. The plan's own gate section already flags the gate change as the part deserving maintainer scrutiny at approval, which is the right place for this; blocking a plan whose alternative was measured unexecutable would park a release-gating bug fix for no gain | yes |
| D-3 | F-11's pre-authorized failure is spent; delete the row, or supersede it? | Supersede it in place and add F-15 with the new measurement | Delete F-11 as now-false; silently leave it and only fix the instructions | A finding was TRUE when written and deleting it destroys the reasoning trail a later reader needs to understand why the instruction existed; but leaving it unmarked would let an executor cite it to excuse a regression. Marking it superseded with a pointer to F-15 keeps both properties. This mirrors the repository's rule against rewriting an executed plan's record | yes |
