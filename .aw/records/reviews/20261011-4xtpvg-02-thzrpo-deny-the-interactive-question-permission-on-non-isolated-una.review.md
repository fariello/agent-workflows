# Review findings: plan thzrpo

- Subject-Id: thzrpo
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `8fc33dcd8`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`: `clean` before review;
`--phase review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Demonstrations ran in a detached worktree under `/tmp/opencode/`, which was removed afterwards. In that worktree,
E-05's selection was prototyped by passing `{"question": "deny"}` to `build_permission_policy_env` on non-isolated turns:
- 40 launcher-touching test files: `3 failed, 635 passed` both before and after (the same 3 pre-existing
  `test_commit_run_trailers_env.py` failures). With `--durations=0`,
  `test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_terminates_silent_child_and_marks_interrupted`
  took 61.89s against 2.15s at baseline. No other test moved by more than 1.5s.
- With the test's fake `--opencode` given an argv guard (exit 2 unless `argv[1] == "run"`), it gave `1 passed in 2.98s`.
- `run_opencode`, driven with `observe_opencode_policy` patched and a sentinel-raising `Popen`, decoded
  `{"permission": {"question": "deny"}}` for the non-isolated case and both denials for the isolated case.
- `opencode run --help` (1.18.35) lists `-i/--interactive` and `--attach` as opt-in. Neither occurs in
  `oc_runipd.py`'s launch argv.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D/E anti-regression (suite cost) | `oc_runipd.observe_opencode_policy` (`_POLICY_PROBE_TIMEOUT_SECONDS = 30.0`); `tests/test_oc_runipd.py` `StallWatchdogTests` fake `time.sleep(60)`; review prototype | Once E-05 probes non-isolated turns, a fake host that ignores its argv makes both probe calls wait out the 30s timeout. One existing test goes from 2s to 62s on every bare run. F-9 found no failures, but it did not measure durations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-09/V-09: give the fake an argv guard (demonstrated, 2.98s) and compare durations against an E-01 baseline. `tests/test_oc_runipd.py` was added to `- Scope-Paths:`. OQ-03 and D-3 record the choice. |
| PR-002 | MEDIUM | IN-SCOPE | E testing (harness feasibility) | E-06 original ("`subprocess.Popen` replaced by a fake"); `run_opencode` runs `git` before launch; `lane_containment.record_host_posture` item fallback | The harness left two things unstated: git calls must reach the real `Popen`, and a bare item gets `host_posture` on the item, not on an attempt. An executor could build a fake that breaks on git or read the wrong field. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now specifies the demonstrated harness: git delegated, sentinel raise, `/bin/false` host, and read from `item["host_posture"]`. |
| PR-003 | MEDIUM | UNDER-SCOPE | E testing (R4.3 coverage) | `build_permission_policy_env` `POLICY_SOURCE_OVERRIDE` branch; E-06 (a)-(e) | The loud-override path for an unparseable operator value was untested for the new turn class. R4.3 is one of the three requirements the new R4.1d invokes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added case (f), and the counts became six tests in E-06 and V-06. |
| PR-004 | LOW | IN-SCOPE | G gate challenge left unanswered | Gate "WHAT A REVIEWER SHOULD CHALLENGE HARDEST" | The gate asked a reviewer to check whether any launch path gives the child an answerer. The plan did not record the answer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11, OQ-02 (resolved: none) and D-2. A review answer line was added to the gate. |
| PR-005 | LOW | UNDER-SCOPE | G execution contract / sibling coupling | `15db4k` E-03 moves the `RESIDUAL LIMITS:` paragraph and rewrites `CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL`; thzrpo gate lacked a scope-fence declaration; A8d traceability | The plan did not mention the sibling's relocation of the paragraph that E-04(b) edits. The gate had no scope-fence declaration. V-07 did not check that A8d is traced (`check.spec-criteria-uncovered`). V-03 did not check the record's layers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added an ordering note in both directions, a scope-fence declaration, the `aw check` traceability evidence in V-07, and the layers evidence in V-03. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the posture record be read from the attempt or the item in E-06? | Read `item["host_posture"]` for a bare item. | Seed an attempt list. Rejected because the bare item is what the demonstrated harness produces. | `lane_containment.record_host_posture` fallback; review demo. | yes |
| D-2 | Must the plan narrow to unattended runs only (the gate's challenge)? | No. Every driver child is unanswerable. | Add an attended-mode exemption. Rejected because no such launch path exists. | F-11: `run_opencode` argv and `popen_kwargs`; `opencode run --help`; `host_sandbox_profile._capture_turn_argv`. | yes |
| D-3 | How should the new probe cost on fake-host tests be absorbed? | Edit the fake (argv guard). | Skip the probe on non-isolated turns, which violates R4.2. Lower the probe timeout, which changes production for a test. Accept the 60s cost on every run. | Review prototype timings (F-10). | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
