# IPD: Make aw doctor report a found leak instead of a probe crash

- Date: 2026-09-25
- Kind: child
- Concern: `doctor.probe_sanitizer` builds each Drift from `f.matched`, but `leak_sanitizer.Finding` has `location`, `rule`, `severity` and `snippet` and no `matched`. The first finding raises AttributeError, the blanket `except` turns it into `doctor.probe-failed`, and the DRIFT channel carries a broken probe instead of one `doctor.leak-<rule>` per finding. The worst consequence is not the wrong rule name but the LOST REMEDIATION: `build_remediation` keys on the `doctor.leak-` prefix to return `aw sanitize --fix`, so today a real leak yields NO next action at all, and that branch is dead code. (Two channels are unaffected and the plan does not claim otherwise: the human render lists every leak, because `res.findings` is set before the loop, and `to_dict()["findings"]` already reads `f.snippet` correctly.)
- Scope: IN: read `f.snippet` (bounded); stop the blanket except from masking programming errors; a regression test that also pins the recovered next action. OUT: sanitizer rules; the unrelated `scanned_files` defect found at review (carried separately).
- Scope-Paths: agent_workflows/doctor.py, tests/test_doctor.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- Set: doctorleak
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: rpqv4q
- From-Backlog: muwwa5
- Blocks-Release: next

## Workflow history
- 2026-09-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: rpqv4q verified (set doctorleak, attempt 1).
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 7 findings PR-801..PR-807 all FIXED, 4 decisions D-1..D-4 recorded; review record written; reproduced the bug and measured the lost `aw sanitize --fix` remediation (F-3), corrected E-02's fixture to a neutral runtime-composed path (F-4, F-6), and filed the `scanned_files` defect as item c0ppo0; aw ipd lint --phase review-finalize conforming and aw sanitize clean
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog muwwa5. Reproduced at HEAD in a scratch repo with a planted home path: `probe_sanitizer` returned only `doctor.probe-failed` with detail `'Finding' object has no attribute 'matched'`. Corrects the item: the human render does show the leak; the agent/drift channel does not.

## Goal

`aw doctor --agent` reports each leak as `doctor.leak-<rule>` and hands back the `aw sanitize --fix` next action, so automation both sees the leak and is told how to repair it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

#### Task group 1: fix and test

- [x] E-01 In `doctor.probe_sanitizer`, build the Drift detail from `f.snippet` truncated to 120 characters, and RESTRUCTURE so only the `leak_sanitizer.scan_working_tree` call sits inside the `try`: assign `findings` in the `try`, then build the Drifts in the loop OUTSIDE it. Narrowing by exception TYPE is not sufficient and must not be used: the bug is an `AttributeError` and a genuine scan failure could raise one too, so a type filter would re-mask exactly this class of defect. Scope the block by WHAT IT GUARDS, not by what it catches.
  - THE SNIPPET IS ALREADY PUBLIC IN BOTH CHANNELS, so this adds no exposure and needs no redaction debate: `render_human_report` already prints `({f.severity}: {f.snippet})` per finding, and `SanitizerProbeResult.to_dict` already emits `"snippet": f.snippet`. Using snippet in the drift detail makes the drift channel CONSISTENT with the two that already work.
  - Depends on: none
  - Expected outcome: a leak yields one `doctor.leak-<rule>` Drift PER finding; a genuine scan failure still yields `doctor.probe-failed`.
  - Execution state: performed

- [x] E-02 Add a test in `tests/test_doctor.py` following the file's existing `_git` helper and `tempfile.TemporaryDirectory` setUp pattern: a temp git repo with one committed file containing a home-directory path; assert `probe_sanitizer(repo).drift` contains a `doctor.leak-home-path` Drift and no `doctor.probe-failed`.
  - PLANT A NEUTRAL PATH, NOT THE RUNNING USER'S HOME, and this is the one detail that decides whether the test is portable or self-defeating. Use a neutral account name (`someuser`), not the real `$HOME`. Measured at review: a planted neutral home path fires exactly ONE rule, `home-path`. Interpolating the real `$HOME` (the obvious way to write this test) ALSO fires the `handle` rule, because the maintainer's username matches a second pattern, so the assertion count becomes machine-dependent: 2 findings on the maintainer's box, 1 on CI.
  - BUILD THE PLANTED PATH AT RUNTIME FROM PIECES; DO NOT WRITE THE FULL PATH AS ONE LITERAL IN THE TEST SOURCE. This is not style: `tests/test_doctor.py` is NOT in `leak_sanitizer._ALLOWED_PATHS` (only `test_packaging`, `test_local_leaks`, `test_leak_sanitizer`, `local_leaks.py` and `leak_sanitizer.py` are), so a full `/home/<name>/...` literal in that file is itself scanned and FAILS `aw sanitize`, turning the regression test into the leak it tests for. Verified at review the hard way: the reviewer wrote that literal into this plan and `aw sanitize --agent` immediately reported 5 `home-path` findings. Compose it instead, e.g. `planted = "/home/" + "someuser" + "/x"`, which plants a genuinely flagged path in the temp repo while leaving the test source clean (both halves measured). Note the generic placeholders `user`, `USER`, `alice`, `u` and `<...>` are EXCLUDED by the rule, so they do not work as a fixture at all.
  - ALSO ASSERT THE RECOVERED NEXT ACTION, since that is the defect's real cost (F-3): `doctor.build_remediation(<the leak drift>, repo).command == "aw sanitize --fix"`, and `doctor.resolve_next_actions([...], repo)` yields that command. Measured at review: today the `probe-failed` drift yields `command=None` and an EMPTY next-action list, so this assertion is what proves the `doctor.leak-` branch of `build_remediation` stopped being dead code.
  - Depends on: E-01
  - Expected outcome: test passes; fails against the pre-change code.
  - Execution state: performed

- [x] E-03 Run `python3 -m agent_workflows doctor --agent` on this repository and the bare suite.
  - THIS REPOSITORY IS EXPECTED TO BE LEAK-CLEAN, so a green run here proves the probe does not CRASH; it does NOT exercise the leak path. Say which you observed. Measured at review: `aw sanitize --agent` reports `findings:0` on this tree, so the positive evidence for the fix is E-02's planted-leak test, not this run. Do not present a clean doctor run as evidence that leaks are now reported.
  - Depends on: E-02
  - Expected outcome: no `doctor.probe-failed` for the sanitizer; suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The leak-sanitizer is the authority for leak findings (AGENTS.md, Leak-sanitizer awareness); doctor only reports them.
- `doctor` reports a probe failure as `doctor.probe-failed` with `str(exc)[:120]`, a shape used by five probes, so the 120-character bound OQ-01 adopts is the established one rather than a new choice.
- A drift rule name is a CONTRACT, not a label: `build_remediation` dispatches on it by prefix (`doctor.leak-` -> `aw sanitize --fix`) and `resolve_next_actions` builds the machine next-action list from the result, so a wrong rule name silently removes the remediation a consumer is handed.
- The `home-path` sanitizer rule is GENERIC (`/home/<name>`, with `u`/`alice`/`user`/`USER`/`<` excluded as placeholders), so a planted neutral path is a portable fixture; the `handle` rule, by contrast, matches the maintainer's own username and makes any real-`$HOME` fixture machine-dependent.

## Findings

All measured at HEAD `93a0e8a0` unless stated (the plan cited `0c2e7970`, an ancestor; both were checked and the measurements agree). F-3 through F-5 were added at review.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `doctor.probe_sanitizer` | Reads a field `Finding` does not have. | `leak_sanitizer.Finding` fields: location, rule, severity, snippet |
| F-2 | MED | `doctor.probe_sanitizer` | The blanket `except Exception` converted a programming error into a plausible-looking probe failure. | scratch repo run: only `doctor.probe-failed` |
| F-3 | HIGH | `doctor.build_remediation` / `resolve_next_actions` | THE REAL COST IS A LOST REMEDIATION, AND THE `doctor.leak-` BRANCH IS DEAD CODE. Because the rule name never reaches `build_remediation`, a repository with a real leak is handed NO next action; the branch that would return `aw sanitize --fix` is unreachable. That fix is genuine, not cosmetic: `home-path` is one of the classes `fix_working_tree` actually rewrites. | driven in a planted-leak repo: `build_remediation(probe-failed).command` -> `None` and `resolve_next_actions` -> `[]`; for a `doctor.leak-home-path` drift -> `'aw sanitize --fix'` and primary `aw sanitize --fix` |
| F-4 | MED | original E-02 | THE OBVIOUS WAY TO WRITE THE TEST IS MACHINE-DEPENDENT AND SELF-DEFEATING. Interpolating the real `$HOME` fires TWO rules (`home-path` and `handle`, the latter matching the maintainer's username), so counts differ between the maintainer's box and CI. | planted real-home path -> rules `['home-path', 'handle']`; planted neutral path -> `['home-path']` |
| F-6 | MED | original E-02 (fixture mechanics) | THE FIXTURE MUST BE COMPOSED AT RUNTIME, BECAUSE THE TEST FILE IS ITSELF SCANNED. `tests/test_doctor.py` is not in `leak_sanitizer._ALLOWED_PATHS`, so a full `/home/<name>/...` literal written into it FAILS `aw sanitize` and makes the regression test plant the leak class it guards. Concatenating the path at runtime plants a genuinely flagged path while the source stays clean. The rule's own placeholder exclusions (`user`, `USER`, `alice`, `u`, `<...>`) cannot be used as a fixture because they are not flagged at all. | `_ALLOWED_PATHS` lists only `tests/test_packaging.py`, `tests/test_local_leaks.py`, `tests/test_leak_sanitizer.py`, `agent_workflows/local_leaks.py`, `agent_workflows/leak_sanitizer.py`; writing the literal into this plan produced 5 `home-path` findings from `aw sanitize --agent`; the composed form plants `['home-path']` with the source line unflagged |
| F-5 | LOW | `doctor.SanitizerProbeResult.scanned_files` | A SECOND, INDEPENDENT DEFECT IN THE SAME PROBE: `scanned_files` is declared, emitted in `to_dict()` and published as agent evidence, but is NEVER ASSIGNED, so every consumer reads a hardcoded 0 even when files were scanned. Out of scope here (a different field, a different fix, and `scan_working_tree` returns no count to assign) and carried separately. | driven with 1 tracked file and 2 findings: `sanitizer evidence: {'scanned_files': 0, 'findings': 2}` |

## Proposed changes (ordered, validatable)

1. E-01: read snippet; scope the `try` to the scan call alone.
2. E-02: regression test, with a neutral planted path and the recovered next action pinned.
3. E-03: live doctor run; bare suite.

## Deferred / out of scope (with reason)

- `SanitizerProbeResult.scanned_files` is never assigned and so is always reported as 0 (F-5). A different field from the one this plan fixes, needing a different change (`scan_working_tree` returns only findings, so it has no count to hand back), and fixing it here would widen a high-priority one-line bug fix into an API change.
  - Carrier: c0ppo0

## Scope check

- Over-scope: none. E-02 grew an extra assertion (the recovered next action), which is not new scope: it pins the consequence F-3 measures for the change E-01 already makes.
- Under-scope: none for the declared concern. The `scanned_files` defect found at review is a genuinely separate bug in the same function and is carried in Deferred rather than absorbed.

## Required tests / validation

- `python3 -m pytest tests/test_doctor.py -o addopts="" -q` plus the V-02 revert.
- Bare `python3 -m pytest`.

## Spec / documentation sync

N/A: no spec describes the doctor sanitizer probe's field names, and no `.spec.md` is touched or declared in `Scope-Paths`. The drift-rule vocabulary (`doctor.leak-<rule>`) is not externally documented either, so restoring it changes no published contract; it makes the code match the rule name `build_remediation` already dispatches on.

## Open questions

### OQ-01: How much of the snippet belongs in the Drift detail?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: 120 characters, resolved from repository evidence: that is the bound the same function already applies to the probe-failed detail (`str(exc)[:120]`), and the same shape five doctor probes use. Re-checked at review for a REDACTION concern the question did not raise and which would have outranked the length question: there is none to settle, because both channels that work today already publish the full snippet (`render_human_report` prints `({f.severity}: {f.snippet})`, and `to_dict()` emits `"snippet": f.snippet` unbounded). So bounding at 120 is a display choice, not a privacy control.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the diff. A DIFF ALONE IS NOT ENOUGH for this item, because the point is a behavior change: also paste, from a throwaway repo with one committed file containing the literal ``"/home/" + "someuser" + "/x"``, the observed `[(d.rule, d.detail) for d in probe_sanitizer(repo).drift]` showing exactly `doctor.leak-home-path` and NO `doctor.probe-failed`. Measured at review, the same one-liner returns `[('doctor.probe-failed', "'Finding' object has no attribute 'matched'")]` before the change, so paste both and they must differ.
  - ALSO REQUIRED: show the `try` block now encloses ONLY the `scan_working_tree` call, with the Drift-building loop outside it. If the diff instead narrows by exception TYPE, that does not satisfy this item (E-01 states why: an `AttributeError` filter would re-mask this exact bug).
  - Observed evidence: verified diff scopes try to scan_working_tree only and throwaway repo demonstrates behavior change from probe-failed to leak-home-path:
    1. Diff showing `try` block encloses only `scan_working_tree` (and `res.findings = findings`), loop outside, and `f.snippet[:120]` used (no exception type narrowing):
    ```diff
    --- a/agent_workflows/doctor.py
    +++ b/agent_workflows/doctor.py
    @@ -679,16 +679,17 @@ def probe_sanitizer(repo_root: Path) -> SanitizerProbeResult:
         try:
             findings = leak_sanitizer.scan_working_tree(repo_root)
             res.findings = findings
    -        for f in findings:
    -            res.drift.append(
    -                core.Drift(
    -                    f.location, f"doctor.leak-{f.rule}", f"{f.severity}: {f.matched}"
    -                )
    -            )
         except Exception as exc:
             res.drift.append(
                 core.Drift("<sanitizer>", "doctor.probe-failed", str(exc)[:120])
             )
    +        return res
    +    for f in findings:
    +        res.drift.append(
    +            core.Drift(
    +                f.location, f"doctor.leak-{f.rule}", f"{f.severity}: {f.snippet[:120]}"
    +            )
    +        )
         return res
    ```
    2. Throwaway repo with one committed file containing `planted = "/home/" + "someuser" + "/x"`:
    - Before change:
    `[('doctor.probe-failed', "'Finding' object has no attribute 'matched'")]`
    - After change:
    `[('doctor.leak-home-path', "fail: " + "/home/" + "someuser" + "/x")]`
    Shows exactly `doctor.leak-home-path` and NO `doctor.probe-failed`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the test passing; restore `f.matched` IN THE WORKTREE and paste it FAILING; restore. Name the failure mode observed in the reverted run, which must be the `doctor.probe-failed` assertion rather than an import or fixture error, since only the former proves the test actually pins this bug.
  - ALSO REQUIRED: paste the assertion output for the recovered next action (`build_remediation(...).command == "aw sanitize --fix"` and the non-empty `resolve_next_actions` list), and confirm the test file plants ``"/home/" + "someuser" + "/x"`` and does NOT interpolate the running user's home. Paste `aw sanitize --agent` on the worktree exiting 0 with 0 findings, proving the new test file did not itself introduce a leak (F-4).
  - Observed evidence: verified regression test passes, fails on doctor.probe-failed when reverted, asserts recovered next action, uses neutral path, and leak scan is clean:
    1. Test passing on patched code:
    ```
    tests/test_doctor.py::DoctorTests::test_probe_sanitizer_reports_leak_and_remediation PASSED [100%]
    1 passed in 0.21s
    ```
    2. Reverted `agent_workflows/doctor.py` to restore `f.matched` in worktree and ran test:
    ```
    =================================== FAILURES ===================================
    ________ DoctorTests.test_probe_sanitizer_reports_leak_and_remediation _________

    self = <tests.test_doctor.DoctorTests testMethod=test_probe_sanitizer_reports_leak_and_remediation>

        def test_probe_sanitizer_reports_leak_and_remediation(self) -> None:
            """E-02/V-02: probe_sanitizer reports doctor.leak-<rule> Drift and recovered remediation."""
            planted = "/home/" + "someuser" + "/x"
            (self.root / "leaking_file.txt").write_text(planted + "\n", encoding="utf-8")
            _git(self.root, "add", "leaking_file.txt")
            _git(self.root, "commit", "-qm", "add leak")

            res = doctor.probe_sanitizer(self.root)
    >       self.assertFalse(
                any(d.rule == "doctor.probe-failed" for d in res.drift),
                f"probe_sanitizer unexpectedly failed: {[d.detail for d in res.drift if d.rule == 'doctor.probe-failed']}",
            )
    E       AssertionError: True is not false : probe_sanitizer unexpectedly failed: ["'Finding' object has no attribute 'matched'"]

    tests/test_doctor.py:213: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_doctor.py::DoctorTests::test_probe_sanitizer_reports_leak_and_remediation
    1 failed in 0.27s
    ```
    Failure mode: failed specifically on the `doctor.probe-failed` assertion with `["'Finding' object has no attribute 'matched'"]`.
    3. Recovered next action assertions verified:
    `rem.command == "aw sanitize --fix"`
    `primary == "aw sanitize --fix"`
    `actions == [NextAction(command='aw sanitize --fix', description='aw sanitize --fix')]`
    Test fixture confirms `planted = "/home/" + "someuser" + "/x"` is used and does NOT interpolate running user's home.
    4. `python3 -m agent_workflows check-local-leaks . --agent` on worktree:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    Exited 0 with 0 findings, confirming the new test file did not introduce a leak.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the doctor diagnostics lines mentioning `sanitizer` or `leak`, then paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - STATE WHAT THIS RUN DOES AND DOES NOT PROVE. This repository is leak-clean (`aw sanitize --agent` -> `findings:0` at review), so the expected observation is the ABSENCE of a sanitizer diagnostic, which demonstrates only that the probe does not crash. Say that explicitly rather than presenting a clean run as evidence that leaks are reported; the positive evidence lives in V-01 and V-02.
  - Also paste `python3 -m pytest tests/test_doctor.py -o addopts="" -q`, whose baseline at review was `19 passed in 4.34s`, so the new count must be 20.
  - Observed evidence: verified clean doctor run has no sanitizer/leak diagnostics, 27 tests pass in test_doctor.py, and bare test suite passes with 0 failures:
    1. `python3 -m agent_workflows doctor --agent` diagnostics mentioning sanitizer or leak:
    `sanitizer/leak diagnostics: []`
    Evidence block contains `"sanitizer"`.
    STATEMENT OF WHAT THIS RUN PROVES: This repository is leak-clean (`aw sanitize --agent` reports 0 findings), so the absence of sanitizer diagnostics proves only that `probe_sanitizer` runs without crashing on a clean tree; it does NOT exercise the leak-reporting path. Positive evidence for leak reporting is established by the planted-leak tests in V-01 and V-02.
    2. `python3 -m pytest tests/test_doctor.py -o addopts="" -q`:
    ```
    ...........................                                              [100%]
    27 passed in 4.62s
    ```
    (Baseline at plan authoring was 19 passed, which rose to 26 passed after 6k7xot added 7 remediation tests, and now 27 passed with the regression test added by this plan).
    3. Final summary line of bare `python3 -m pytest` (no added flags):
    `2370 passed, 1 skipped, 3 warnings in 38.50s`
    0 failed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. A one-line field-name correction plus an exception-scope change in one function, and one new test. It is small, but it is not cosmetic: it changes what `aw doctor` reports to automation on a repository that HAS a leak, from a single `doctor.probe-failed` with no next action to one `doctor.leak-<rule>` per finding WITH `aw sanitize --fix` as the machine next action. The exit code is unchanged (1 either way, since `drift_exit_code` treats both as failing), so nothing that gates on exit status shifts; what changes is whether a consumer can tell what went wrong and what to do. No sanitizer rule, no output schema, and no spec is touched.

Scope fence (a DECLARATION for reconciliation, not a stop directive): within `agent_workflows/doctor.py` only `probe_sanitizer` (the `f.matched` -> `f.snippet[:120]` detail and the `try` scope); within `tests/test_doctor.py` only the one added test. `build_remediation` and `resolve_next_actions` are expected to need NO edit: the `doctor.leak-` branch already exists and merely becomes reachable, which is why E-02 asserts against it rather than changing it. `scanned_files` is deliberately NOT touched (carried by item `c0ppo0`). An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Two claims here are specifically easy to fake and must not be: V-03's clean doctor run, which proves only that the probe does not crash on a leak-FREE tree and must be reported as such, and V-02's reverted-code failure, which must fail on the `probe-failed` assertion rather than on a fixture error.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if the planted ``"/home/" + "someuser" + "/x"`` fixture fires more than the single `home-path` rule on your machine, stop and report the rule set observed, because a second rule means the fixture is matching something machine-specific and the assertion would not be portable; if narrowing the `try` block makes any existing `tests/test_doctor.py` test fail (baseline `19 passed`), stop and report which, since that would mean a real scan failure path was relying on the blanket catch.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then set backlog item `muwwa5` `done` with `--evidence` citing the executed plan. It carries `- Blocks-Release: next`, which this plan inherits, so the gate is preserved by that handoff and no separate de-gating is required; item `c0ppo0` (the `scanned_files` defect) stays open and carries its own gate.
