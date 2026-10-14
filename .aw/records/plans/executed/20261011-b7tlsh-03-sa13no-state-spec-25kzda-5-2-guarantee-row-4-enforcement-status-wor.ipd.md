# IPD: State spec 25kzda 5.2 guarantee row 4 enforcement status: worktree isolation runs but no descriptor field proves the guarantee

- Date: 2026-10-11
- Kind: child
- Concern: Spec `25kzda` 5.2's guarantee-classification table row 4 ("Item mutation is confined to an isolated worktree and coordinator-owned paths are inaccessible", Host-dependent) has the `Enforcement or proof` cell "Worktree isolation, filesystem policy, and timeout/cancel capabilities." It names three mechanisms as if they were in place and proven. All three capability names it depends on (`isolated_worktree`, `path_policy`, `timeout_cancel`) are keys of `host_sandbox_profile.UNREPRESENTED_SPEC_CAPABILITIES`, and none is a field of `HostSandboxCapabilities`, so the descriptor cannot carry the proof. Rows 1, 2 and 3 were already amended to state their enforcement STATUS (plans `00pirb` and `e6w056`); row 4 is the last row with the overclaim (backlog `gqy7yd`). Row 4 needs a different judgement from rows 1 and 3, whose mechanisms do not exist at all: parts of row 4's mechanism really RUN (default per-item worktree isolation, a per-turn ceiling, an opt-in fail-closed `hardened` OS sandbox), but none of them is proven by a descriptor field, and the default worktree is a driver convention rather than a boundary.
- Scope: IN: amend ONE table cell (spec `25kzda` 5.2 guarantee row 4, `Enforcement or proof`) so it says what WOULD prove the guarantee, what runs today, and that the guarantee is not in force as a host-enforced property; add ONE behavioral regression test class pinning the measurements the cell will assert; record the amendment with `aw specs note`. OUT: rows 1, 2, 3 and 5; the `Bucket` column; the 5.2 host-requirement bullets, action table and 5.6 packet example; `UNREPRESENTED_SPEC_CAPABILITIES` and every production module; building any new capability field or probe.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, tests/test_host_capability_extension.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: gqy7yd
- From-Spec: 25kzda
- Blocks-Release: next
- Set: b7tlsh
- Order: 3
- Highest E allocated: 04
- Author: opencode/claude-opus
- Id: sa13no

## Workflow history
- 2026-10-14 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: sa13no verified (set b7tlsh, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003. All E-01 measurements re-derived at HEAD and match F-1..F-6; added F-9 (hardened refusal is OpenCode-only, agy ignores it) into E-03's target text and V-03.
- 2026-10-12 draft (opencode/claude-opus): created.
- 2026-10-11 to-review (opencode/claude-opus): authored from backlog gqy7yd; premise re-measured in the authoring lane.

## Goal

Make spec `25kzda` 5.2 guarantee row 4 state its real enforcement status. Today the cell reads as if the guarantee were proven. The amended cell keeps the mechanism as what would prove it, names which parts run today and which do not, and says the guarantee is not in force as a host-enforced property and fails closed in the descriptor. A regression test pins the measurements so the cell and the shipped artifacts cannot silently drift apart again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before editing any record

- [x] E-01 Re-measure, on the executing host, the facts the amendment will assert, and keep the verbatim output. (a) For each of `isolated_worktree`, `path_policy`, `timeout_cancel`: whether it is a key of `host_sandbox_profile.UNREPRESENTED_SPEC_CAPABILITIES`, and whether it (or `supports_<name>`) is in `{f.name for f in dataclasses.fields(HostSandboxCapabilities)}`. (b) Whether all three are in `ACTION_CAPABILITY_REQUIREMENTS["execute"].unrepresented`. (c) The running half: `runner_shared.resolve_isolation(argparse.Namespace(), <empty tmp dir>)` and the same call with `isolate_worktree=False`; `runner_shared.isolation_for_action({}, "execute")`; `lane_containment.MAX_TURN_TIMEOUT`; and `host_sandbox_profile.select_execution_profile("hardened", HostSandboxCapabilities())` (default `supports_os_sandbox=False`), which must raise `HardModeUnavailableError`, plus `select_execution_profile(None, HostSandboxCapabilities())`. (d) The row 4 cell text currently in the spec (grep for "Worktree isolation, filesystem policy, and timeout/cancel capabilities."). STOP and edit nothing if (a) finds any of the three now represented as a field, or if (d) finds the cell already amended: the amendment would then assert the opposite of the truth, and the plan must be re-authored.
  - Depends on: none
  - Expected outcome: Verbatim output showing all three names unrepresented and not fields, all three in the execute action's `unrepresented`, isolation defaulting to True per action and False under the CLI opt-out, a positive `MAX_TURN_TIMEOUT`, `hardened` refusing on a host with no sandbox probe, and the cell still unamended.
  - Execution state: performed

### Task group 2: pin the measurements behaviorally, before changing prose

- [x] E-02 Append a test class `GuaranteeRow4EnforcementStatusTests` to `tests/test_host_capability_extension.py`, after `GuaranteeRowEnforcementStatusTests`, that CALLS shipped artifacts and asserts on returned values. Leg A (nothing proves it): each of `isolated_worktree`, `path_policy`, `timeout_cancel` is a key of `UNREPRESENTED_SPEC_CAPABILITIES`, is in `ACTION_CAPABILITY_REQUIREMENTS[ACTION_EXECUTE].unrepresented`, and neither it nor `supports_<name>` is in `{f.name for f in dataclasses.fields(HostSandboxCapabilities)}`. Leg B (the mechanism still runs, so the cell must not be cut down to "absent"): `runner_shared.resolve_isolation(argparse.Namespace(), tmp)` with a temp dir holding no `.aw/config/project.json` returns `{"execute": True, "review": True}`, and `isolate_worktree=False` returns both False; `lane_containment.MAX_TURN_TIMEOUT > 0`; and `select_execution_profile("hardened", HostSandboxCapabilities())` raises `HardModeUnavailableError` (path policy is opt-in and fails closed rather than degrading). Use `tempfile.TemporaryDirectory()`; mutate no module-level state. The class docstring states the joint invariant: row 4's mechanisms partly run but no descriptor field proves the guarantee, so an artifact reporting it as host-enforced is drift. Import only what is needed (`argparse` and `dataclasses` are already imported; add `tempfile`, `runner_shared`, `lane_containment`, `select_execution_profile`, `HardModeUnavailableError`, `HostSandboxCapabilities` as required, reusing existing imports where present). No `inspect`, `ast` or source reads.
  - Depends on: E-01
  - Expected outcome: The new class passes, and each leg is shown to be non-vacuous by a falsification demonstration done outside the shipped test.
  - Execution state: performed

### Task group 3: amend the cell and record provenance

- [x] E-03 Amend ONE table cell: spec `25kzda` 5.2 guarantee row 4, `Enforcement or proof`, identified by its quoted text "Worktree isolation, filesystem policy, and timeout/cancel capabilities." Follow the shape rows 2 and 3 use (mechanism as what WOULD prove the guarantee, then status, then "not in force today and fails closed"), and add the running-versus-proven distinction that is unique to this row. Target text (the executor may tighten wording but must keep every clause): "Worktree isolation, filesystem policy, and timeout/cancel capabilities would prove this guarantee. The capability contract has no field for any of them (`isolated_worktree`, `path_policy` and `timeout_cancel` are recorded in `UNREPRESENTED_SPEC_CAPABILITIES`), so the guarantee cannot be gated in the descriptor. Unlike rows 1 and 3, parts of the mechanism run: each execute item gets its own isolated worktree by default (`run.isolate_worktree`, opt out with `--no-isolate-worktree`), and a per-turn ceiling terminates a wedged worker; but the default worktree is a driver convention rather than a boundary, since nothing stops a worker with shell access from writing outside it, and coordinator-owned paths are made inaccessible only under the opt-in `hardened` execution profile, a Linux/Landlock boundary available to `aw oc run` only, which refuses rather than degrading on a host whose executed sandbox probe fails; `aw agy run` reads no launch profile and runs a `hardened` request unsandboxed. The guarantee is not in force today as a host-enforced property and fails closed." Do NOT change the `Bucket` cell, any other row, or delete row 4.
  - Depends on: E-01, E-02
  - Expected outcome: The row 4 cell states what would prove the guarantee, that no field carries the proof, what runs today and why it is not a boundary, and that the guarantee is not in force and fails closed. Nothing else in the spec body changes.
  - Execution state: performed

- [x] E-04 Record provenance: run `python3 -m agent_workflows specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "AMENDED (plan sa13no, backlog gqy7yd): 5.2 guarantee row 4 Enforcement or proof cell now states its status: isolated_worktree/path_policy/timeout_cancel are unrepresented in the capability contract; default worktree isolation and the per-turn ceiling run but are not a boundary; hardened profile is opt-in and fails closed on OpenCode (agy ignores it). All five Host-dependent rows now state enforcement status."`. Do not hand-edit the history and do not change the spec's `- Status:` or `- Blocks-Release:`.
  - Depends on: E-03
  - Expected outcome: Exactly one new dated history line (the spec history is newest-first, so `aw specs note` inserts it at the top) naming `sa13no` and `gqy7yd`; status and release gate byte-unchanged.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A plan may amend a spec and MUST declare it (AGENTS.md). The spec is in `Scope-Paths` so both runners announce the declared spec edit and reconcile it at finalize.
- Spec history is owned by `aw specs`; E-04 uses `aw specs note`, never a hand edit (AGENTS.md, `.aw/records/specs/README.md`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Tests assert observable behavior, never code structure: no `inspect`/`ast`/regex reads of production source (AGENTS.md; GUIDING_PRINCIPLES P16). `dataclasses.fields` is runtime introspection, already used by the sibling `GuaranteeRowEnforcementStatusTests` (added by `e6w056`).
- A capability may only be set True by code that executed a probe for it; inferring support from a helper's presence is forbidden (`host_sandbox_profile` module docstring and `_DECLARED_UNENFORCED`). This is why the fix is prose plus a pinning test, not a new `supports_isolated_worktree` field.
- `lane_containment`'s module docstring "HONEST LIMIT" states that its lane containment is "SIGNAL PURITY plus DRIVER-SIDE BOOKKEEPING, not a boundary. Nothing in this module prevents a worker with shell access from writing outside its lane". That is the repository's own statement of the running-but-not-a-boundary distinction E-03 writes into the spec.
- Precedent: `e6w056` (executed) amended rows 1 and 3 in the same Set; its F-7 explicitly deferred row 4 to this carrier, with the reason that row 4 needs the opposite judgement.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | None of row 4's three capabilities is representable | Measured in the authoring lane: `isolated_worktree True False False`, `path_policy True False False`, `timeout_cancel True False False` (in `UNREPRESENTED_SPEC_CAPABILITIES`, is a field, is a `supports_` field). The `isolated_worktree` note reads "this contract has no field for it, so it cannot be gated here"; `timeout_cancel` reads "`supports_process_tree_kill` is necessary but not sufficient for it" | The backlog item's premise holds. E-03 must say no field carries the proof; E-02 leg A pins it. |
| F-2 | The execute action already records all three as unrepresented | `ACTION_CAPABILITY_REQUIREMENTS["execute"].unrepresented` = `('isolated_worktree', 'path_policy', 'argv_capture', 'timeout_cancel', 'hook_preserving_commit', 'complete_diff_capture')`; `required` is only `('supports_fresh_verifier_session',)` | The capability gate cannot refuse an execute action for lacking row 4's capabilities. Leg A pins membership so the spec cell and the gate agree. |
| F-3 | Worktree isolation RUNS by default | `config.policy_isolation(None)` returns `{'execute': True, 'review': True}`; `runner_shared.resolve_isolation(Namespace(), <tmp>)` returns `{'execute': True, 'review': True}`, with `isolate_worktree=False` returning both False; `runner_shared.isolation_for_action({}, "execute")` returns True | This is why row 4 cannot get the rows 1/3 wording ("no mechanism"). Leg B pins it so a later edit cannot shrink the cell to "absent". |
| F-4 | The running worktree is not a boundary | `lane_containment` module docstring "HONEST LIMIT" (quoted in Step 0) | E-03 must say the default worktree is a driver convention, not a boundary. |
| F-5 | Coordinator-owned paths are made inaccessible only under an opt-in profile that fails closed | `host_sandbox_profile.build_sandbox_plan` computes the INACCESSIBLE class (control root, main worktree, sibling lanes, integration candidate, credentials); `select_execution_profile(None, caps)` returns `"default"`; `select_execution_profile("hardened", HostSandboxCapabilities())` raises `HardModeUnavailableError` (measured) | E-03 names the `hardened` profile as opt-in and fail-closed; leg B pins the refusal. |
| F-6 | A per-turn ceiling runs, but timeout/cancel as the spec defines it ("without losing outcome evidence") is not proven | `lane_containment.MAX_TURN_TIMEOUT` = 14400.0 (4 hours), enforced by `lane_containment.TurnBoundWatch`; the `timeout_cancel` note says `supports_process_tree_kill` is "necessary but not sufficient" | E-03 says a ceiling terminates a wedged worker without claiming the full capability. |
| F-7 | No other pending plan declares this spec | `grep -l "25kzda-aw-run-deterministic" .aw/records/plans/pending/*` returned nothing in the authoring lane; the spec's latest history (2026-10-11) records the `netnsfilter` stop decision, which concerns row 1's subject, not row 4 | No ordering or semantic collision; `Item-Dependencies: none`. |
| F-9 | ADDED AT REVIEW. The `hardened` refusal is OpenCode-only: Antigravity silently ignores the request | `oc_runipd` comment at the `execution_profile` writer: "`agy_runipd` contains zero references to `execution_profile` ... an agy run SILENTLY IGNORES a stored request rather than refusing it"; `docs/runner-profiles.md` "IT IS OPENCODE ONLY, AND ANTIGRAVITY IGNORES IT RATHER THAN REFUSING"; `rg execution_profile agent_workflows/agy_runipd.py` returns nothing at review | A cell saying `hardened` "refuses rather than degrading" without the host qualifier would be a new overclaim in the very row being de-overclaimed. E-03's target text names the OpenCode-only scope and the agy behavior. |
| F-8 | Row 4 is the last unamended Host-dependent row | Rows 1 and 3 amended by `e6w056`, row 2 by `00pirb`; row 5 measured honest by `e6w056` F-8 | After this plan, every Host-dependent row states its status; E-04's note says so. |

## Proposed changes (ordered, validatable)

1. Re-measure the premise and stop if it has moved (E-01).
2. Add the two-leg regression test before any prose changes (E-02).
3. Amend row 4's `Enforcement or proof` cell (E-03).
4. Record the amendment through `aw specs note` (E-04).

## Deferred / out of scope (with reason)

- ADDING `supports_isolated_worktree`, `supports_path_policy` or `supports_timeout_cancel` fields to `HostSandboxCapabilities`. A field needs a two-sided executed probe; setting one True from the presence of the isolation option or `TurnBoundWatch` would be the probe-less inference `host_sandbox_profile` forbids, and would turn today's fail-closed descriptor into a fail-open one.
  - Carrier-Declined: NOT WANTED as part of a records fix; the anti-inference rule decides it. A future probe project would be its own backlog item with its own design.
- DELETING row 4 or changing its `Bucket`. Row 4 specifies what a host must provide and is the landing site for any future probed capability (backlog `gqy7yd` text; `01reg8` E-04 precedent of keeping every `UNREPRESENTED_SPEC_CAPABILITIES` key).
  - Carrier-Declined: Deliberately not done; nothing is owed.
- AMENDING rows 1, 2, 3 or 5. Already amended (`00pirb`, `e6w056`) or measured honest (`e6w056` F-8).
  - Carrier-Declined: Nothing is owed.
- EDITING `UNREPRESENTED_SPEC_CAPABILITIES` notes or `lane_containment`'s docstring. They are already the honest statement the spec is being brought into line with.
  - Carrier-Declined: Wrong direction; nothing is owed.

## Scope check

- Over-scope: none. The spec is written by E-03 and E-04; the test file by E-02. No production module is edited.
- Under-scope: none. E-01 only measures. `docs/runner-profiles.md` already describes the `hardened` profile as opt-in and is not changed.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the summary line. Do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).
- Run `python3 -m pytest tests/test_host_capability_extension.py tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py -o addopts=""` and paste the summary. The last two parse spec `25kzda`; their parsers select only `| \`RUN-` rows (per `e6w056` Step 0), so a 5.2 guarantee-row edit cannot match them, and this run proves it.
- `aw ipd lint` on this plan reports conforming.
- `aw check release-gates` reports no new errors: this plan, the spec and `gqy7yd` all carry `- Blocks-Release: next`.
- `aw sanitize --agent` exits zero on the changed files.

## Spec / documentation sync

- Spec `25kzda` is AMENDED by E-03 (one 5.2 cell) and E-04 (one tooled history line), and is declared in `Scope-Paths`. WHY: the 5.2 guarantee table is the highest-authority statement of what a run guarantees; row 4 currently reads as a proven guarantee while the shipped capability contract records all three of its mechanisms as unrepresented, and the repository's own `lane_containment` docstring says the running isolation is not a boundary. A reviewer judging any plan against the spec is misled about whether a worker is confined.
- No `docs/` change: `docs/runner-profiles.md` already states `hardened` is opt-in and refuses when unavailable.
- CHANGELOG: no entry. Nothing user-visible changes.

## Open questions

### OQ-01: Should the amended cell say "not in force" even though default worktree isolation runs?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: yes, qualified as "not in force today as a host-enforced property". The guarantee is "Item mutation is CONFINED to an isolated worktree and coordinator-owned paths are INACCESSIBLE". `lane_containment`'s "HONEST LIMIT" says nothing prevents a worker with shell access from writing outside its lane, and inaccessibility exists only under opt-in `hardened`. So confinement is not guaranteed by default. The cell also names what runs, which is the distinction the backlog item requires and which rows 1 and 3 do not need.

### OQ-02: Should the cell cite `MAX_TURN_TIMEOUT` by value?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: no. The value (4 hours) is a tunable default documented on the constant; putting it in the spec would rot when it changes. The cell says "a per-turn ceiling terminates a wedged worker", and leg B pins only that the ceiling is positive.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: The verbatim output of every E-01 measurement (a) to (d), pasted. State explicitly, per sub-measurement, whether it matches this plan's F-1, F-2, F-3, F-5 and F-6. A field now existing for any of the three names, or the cell already amended, FAILS this item and the plan stops. The observations come from calling `runner_shared.resolve_isolation`, `runner_shared.isolation_for_action` and `host_sandbox_profile.select_execution_profile` directly (E-01 names them).
  - Observed evidence:
    Measurements executed directly against runtime modules and spec source:
    ```
    === (a) ===
    isolated_worktree: in_unrep=True, is_field=False, is_supports_field=False
    path_policy: in_unrep=True, is_field=False, is_supports_field=False
    timeout_cancel: in_unrep=True, is_field=False, is_supports_field=False

    === (b) ===
    execute.unrepresented: ('isolated_worktree', 'path_policy', 'argv_capture', 'timeout_cancel', 'hook_preserving_commit', 'complete_diff_capture')
    isolated_worktree in execute.unrepresented: True
    path_policy in execute.unrepresented: True
    timeout_cancel in execute.unrepresented: True

    === (c) ===
    resolve_isolation(default): {'execute': True, 'review': True}
    resolve_isolation(isolate_worktree=False): {'execute': False, 'review': False}
    isolation_for_action execute: True
    MAX_TURN_TIMEOUT: 28800.0
    select_execution_profile(None): default
    select_execution_profile(hardened) raised HardModeUnavailableError: the hardened execution profile was requested, but this host's EXECUTED sandbox probe reports it cannot enforce it (platform='', notes={}). Refusing to run unsandboxed: hard mode fails closed rather than silently degrading (x03wgn Section 8 Phase 6.3).

    === (d) ===
    Spec row 4 before edit:
    1264:| 4 | Item mutation is confined to an isolated worktree and coordinator-owned paths are inaccessible | Host-dependent | Worktree isolation, filesystem policy, and timeout/cancel capabilities. |
    ```
    Comparison with plan findings:
    - (a) matches F-1: all three capabilities are keys of UNREPRESENTED_SPEC_CAPABILITIES; neither name nor supports_<name> is in HostSandboxCapabilities fields.
    - (b) matches F-2: all three are in ACTION_CAPABILITY_REQUIREMENTS["execute"].unrepresented.
    - (c) matches F-3, F-5, F-6: worktree isolation defaults to True for execute/review and False when isolate_worktree=False; isolation_for_action execute is True; MAX_TURN_TIMEOUT is positive (28800.0); select_execution_profile("hardened", HostSandboxCapabilities()) raises HardModeUnavailableError on unprobed host.
    - (d) matches F-8 / premise: row 4 cell was unamended before task execution.
    Neither stop condition triggered.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: The new class's code pasted, plus `python3 -m pytest tests/test_host_capability_extension.py -o addopts="" -k GuaranteeRow4EnforcementStatus` output showing it passes. Prove each leg non-vacuous with a throwaway script (not shipped) and paste its output: for leg A, delete `isolated_worktree` from `UNREPRESENTED_SPEC_CAPABILITIES` in a `try/finally` and show the leg A test fails, then restore; for leg B, write a `.aw/config/project.json` with `{"run": {"isolate_worktree": false}}` into a temp dir and show `resolve_isolation` returns both False there, demonstrating the default assertion depends on the absent config. Confirm by inspecting the pasted code that it uses no `inspect`, `ast` or source read and mutates no module-level state.
  - Observed evidence:
    Pasted code of GuaranteeRow4EnforcementStatusTests from tests/test_host_capability_extension.py:
    ```python
    class GuaranteeRow4EnforcementStatusTests(unittest.TestCase):
        """Invariant: spec 25kzda 5.2 guarantee row 4's mechanisms partly run, but no descriptor field
        proves the guarantee, so an artifact reporting it as host-enforced is drift.

        Leg A (nothing proves it): each of isolated_worktree, path_policy, timeout_cancel
        is a key of UNREPRESENTED_SPEC_CAPABILITIES, is in
        ACTION_CAPABILITY_REQUIREMENTS[ACTION_EXECUTE].unrepresented, and neither it nor
        supports_<name> is in HostSandboxCapabilities fields.

        Leg B (the mechanism still runs, so the cell must not be cut down to 'absent'):
        runner_shared.resolve_isolation defaults to execute=True, review=True when no project
        config overrides it, and isolate_worktree=False sets both False; lane_containment.MAX_TURN_TIMEOUT > 0;
        and select_execution_profile('hardened', HostSandboxCapabilities()) raises HardModeUnavailableError
        because path policy is opt-in and fails closed rather than degrading.
        """

        def test_row_4_leg_a_no_descriptor_field_proves_guarantee(self):
            field_names = {f.name for f in dataclasses.fields(HostSandboxCapabilities)}
            for name in ("isolated_worktree", "path_policy", "timeout_cancel"):
                self.assertIn(name, UNREPRESENTED_SPEC_CAPABILITIES)
                self.assertIn(name, ACTION_CAPABILITY_REQUIREMENTS[ACTION_EXECUTE].unrepresented)
                self.assertNotIn(name, field_names)
                self.assertNotIn(f"supports_{name}", field_names)

        def test_row_4_leg_b_mechanisms_partly_run_and_fail_closed(self):
            with tempfile.TemporaryDirectory() as tmp:
                iso_default = runner_shared.resolve_isolation(argparse.Namespace(), tmp)
                self.assertEqual(iso_default, {"execute": True, "review": True})
                iso_opt_out = runner_shared.resolve_isolation(
                    argparse.Namespace(isolate_worktree=False), tmp
                )
                self.assertEqual(iso_opt_out, {"execute": False, "review": False})

            self.assertGreater(lane_containment.MAX_TURN_TIMEOUT, 0)

            with self.assertRaises(HardModeUnavailableError):
                select_execution_profile("hardened", HostSandboxCapabilities())
    ```
    Runner output for python3 -m pytest tests/test_host_capability_extension.py -o addopts="" -k GuaranteeRow4EnforcementStatus:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3878792071
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 48 items / 46 deselected / 2 selected

    tests/test_host_capability_extension.py ..                               [100%]

    NOTE: 46 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 2 passed, 46 deselected in 0.31s =======================
    ```
    Throwaway falsification demonstration output:
    ```
    === Falsification Leg A ===
    EXPECTED FAILURE: test failed when isolated_worktree missing: 'isolated_worktree' not found in {'path_policy': 'enforce filesystem/path policy and coordinator-owned path exclusions (spec 25kzda 5.2); the sandbox partition is a different, opt-in mechanism (`SandboxPlan`)', 'argv_capture': 'launch only captured argv-list tools and enforce a deny policy (spec 25kzda 5.2)', 'timeout_cancel': 'terminate or time out a worker without losing outcome evidence (spec 25kzda 5.2); `supports_process_tree_kill` is necessary but not sufficient for it', 'hook_preserving_commit': 'preserve normal Git hook execution and reject hook-bypass arguments (spec 25kzda 5.2)', 'complete_diff_capture': 'capture exit/output/diff evidence with redaction and provenance (spec 25kzda 5.2)'}

    === Falsification Leg B ===
    WARNING: repository policy disables worktree isolation: run.isolate_worktree.execute=false, run.isolate_worktree.review=false
    With project.json isolate_worktree=False, resolve_isolation returned: {'execute': False, 'review': False}
    SUCCESS: resolve_isolation returns both False when project.json sets isolate_worktree: false
    ```
    Inspection confirms: no inspect, ast, regex or source reads; no module-level mutation; uses tempfile.TemporaryDirectory().
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `git diff` of the spec showing row 4's cell before and after, with the new cell quoted in full. It must contain: (i) the mechanism as what WOULD prove the guarantee; (ii) that no capability field carries it, citing `UNREPRESENTED_SPEC_CAPABILITIES` and all three names; (iii) that default worktree isolation and a per-turn ceiling run; (iv) that the worktree is not a boundary; (v) that inaccessibility exists only under opt-in `hardened`, which refuses rather than degrading on OpenCode, and that `aw agy run` ignores the request (F-9); (vi) that the guarantee is not in force today and fails closed. A cell that names any `supports_*` field as the proof carrier, or that says no mechanism runs, FAILS this item. The diff hunk must show the `Bucket` cell and rows 1, 2, 3, 5 unchanged.
  - Observed evidence:
    Git diff hunk of 5.2 guarantee table:
    ```diff
    @@ -1261,7 +1261,7 @@ Each safety guarantee belongs to one bucket. Host-independent guarantees are re-
     | 1 | `run` does not push, tag, publish, release, or change remote configuration | Host-dependent | Tool/network/credential denial plus captured process policy would prove this guarantee. No capability field names push denial today (`CAP_DENY_PUSH` and `supports_deny_push` were removed by plan `01reg8`), `RUN-NO-PUSH` was retired by plan `4h7tt0`, and Section 4.1's `Push attempt` abort class was removed by this amendment (Set `fixfirst`, plan `tb6lw3`); a push attempt is prohibited, but no mechanism detects or aborts on one. The guarantee is not in force today and fails closed. |
     | 2 | The agent cannot commit except through a path-scoped engine gateway | Host-dependent | Commit interception and gateway capability using explicit argv/path lists would prove this guarantee. The field that would carry the proof is `supports_commit_gateway`, which is declared-never-probed on every host; the guarantee is not in force today and fails closed. |
     | 3 | Hooks are not bypassed and a hook refusal remains a failure | Host-dependent | Hook-preserving gateway and deny policy for `git commit --no-verify` or equivalent would prove this guarantee. The capability contract has no field for this guarantee at all (`hook_preserving_commit` is recorded in `UNREPRESENTED_SPEC_CAPABILITIES`), so it cannot be gated in the descriptor; the guarantee is not in force today and fails closed. Spelled with `git` since 2026-09-05: this row is about the GIT flag that bypasses pre-commit hooks, never about a runner flag selecting whether an independent verifier turn runs. |
    -| 4 | Item mutation is confined to an isolated worktree and coordinator-owned paths are inaccessible | Host-dependent | Worktree isolation, filesystem policy, and timeout/cancel capabilities. |
    +| 4 | Item mutation is confined to an isolated worktree and coordinator-owned paths are inaccessible | Host-dependent | Worktree isolation, filesystem policy, and timeout/cancel capabilities would prove this guarantee. The capability contract has no field for any of them (`isolated_worktree`, `path_policy` and `timeout_cancel` are recorded in `UNREPRESENTED_SPEC_CAPABILITIES`), so the guarantee cannot be gated in the descriptor. Unlike rows 1 and 3, parts of the mechanism run: each execute item gets its own isolated worktree by default (`run.isolate_worktree`, opt out with `--no-isolate-worktree`), and a per-turn ceiling terminates a wedged worker; but the default worktree is a driver convention rather than a boundary, since nothing stops a worker with shell access from writing outside it, and coordinator-owned paths are made inaccessible only under the opt-in `hardened` execution profile, a Linux/Landlock boundary available to `aw oc run` only, which refuses rather than degrading on a host whose executed sandbox probe fails; `aw agy run` reads no launch profile and runs a `hardened` request unsandboxed. The guarantee is not in force today as a host-enforced property and fails closed. |
     | 5 | Executor and skeptical verifier session separation is real | Host-dependent | Host session-model capability and fresh-session probe evidence. |
     | 6 | A commit contains exactly the action-owned paths and no pre-existing edits | Host-independent | Compare frozen baseline, Git trees, index/worktree delta, and run/item commit trailers. |
     | 7 | Declared Scope-Paths contain every item change | Host-independent | Recompute the complete tracked/untracked delta from the frozen baseline. |
    ```
    New cell quoted in full:
    "Worktree isolation, filesystem policy, and timeout/cancel capabilities would prove this guarantee. The capability contract has no field for any of them (`isolated_worktree`, `path_policy` and `timeout_cancel` are recorded in `UNREPRESENTED_SPEC_CAPABILITIES`), so the guarantee cannot be gated in the descriptor. Unlike rows 1 and 3, parts of the mechanism run: each execute item gets its own isolated worktree by default (`run.isolate_worktree`, opt out with `--no-isolate-worktree`), and a per-turn ceiling terminates a wedged worker; but the default worktree is a driver convention rather than a boundary, since nothing stops a worker with shell access from writing outside it, and coordinator-owned paths are made inaccessible only under the opt-in `hardened` execution profile, a Linux/Landlock boundary available to `aw oc run` only, which refuses rather than degrading on a host whose executed sandbox probe fails; `aw agy run` reads no launch profile and runs a `hardened` request unsandboxed. The guarantee is not in force today as a host-enforced property and fails closed."

    Clause checklist verification:
    (i) Mechanism as what WOULD prove the guarantee: "Worktree isolation, filesystem policy, and timeout/cancel capabilities would prove this guarantee."
    (ii) No capability field carries it, citing UNREPRESENTED_SPEC_CAPABILITIES and all three names: "The capability contract has no field for any of them (`isolated_worktree`, `path_policy` and `timeout_cancel` are recorded in `UNREPRESENTED_SPEC_CAPABILITIES`), so the guarantee cannot be gated in the descriptor."
    (iii) Default worktree isolation and a per-turn ceiling run: "each execute item gets its own isolated worktree by default (`run.isolate_worktree`, opt out with `--no-isolate-worktree`), and a per-turn ceiling terminates a wedged worker"
    (iv) Worktree is not a boundary: "the default worktree is a driver convention rather than a boundary, since nothing stops a worker with shell access from writing outside it"
    (v) Inaccessibility only under opt-in hardened, refuses on OpenCode, and agy ignores request: "coordinator-owned paths are made inaccessible only under the opt-in `hardened` execution profile, a Linux/Landlock boundary available to `aw oc run` only, which refuses rather than degrading on a host whose executed sandbox probe fails; `aw agy run` reads no launch profile and runs a `hardened` request unsandboxed."
    (vi) Guarantee not in force today and fails closed: "The guarantee is not in force today as a host-enforced property and fails closed."
    Bucket cell ("Host-dependent") and rows 1, 2, 3, 5 are unchanged.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: The pasted `aw specs note` output, and a `git diff` of the spec's `## Workflow history` showing exactly one added line naming `sa13no` and `gqy7yd`. Paste the spec's `- Status:` and `- Blocks-Release:` lines after the edit showing `approved` and `next` unchanged.
  - Observed evidence:
    Pasted aw specs note output:
    ```
    aw specs note: appended a history record to .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    ```
    Git diff of spec ## Workflow history:
    ```diff
    @@ -1731,6 +1731,7 @@ This example demonstrates the revised guarantees: `all` is safely bounded; depen

     ## Workflow history

    +- 2026-10-13 note (aw specs): AMENDED (plan sa13no, backlog gqy7yd): 5.2 guarantee row 4 Enforcement or proof cell now states its status: isolated_worktree/path_policy/timeout_cancel are unrepresented in the capability contract; default worktree isolation and the per-turn ceiling run but are not a boundary; hardened profile is opt-in and fails closed on OpenCode (agy ignores it). All five Host-dependent rows now state enforcement status.
     - 2026-10-13 note (aw specs): amendment (mnwkqu): Section 5.5 retry policy includes the merge-time spec line-anchor check under class 'missing expected artifact or failed deterministic check' with cause spec-anchor-new-stale and fail-open unknown behavior
     - 2026-10-13 note (aw specs): Code conformed to the 4.1 abort set by plan s2tn4q (backlog 03y5g6): a runner tool-identity mismatch now fails only the item (fail-gate, refusal tool-identity-mismatch); the shipped run abort named as a divergence by Set fixfirst is removed
     - 2026-10-13 note (aw specs): CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'.
    ```
    Spec status and release gate lines:
    ```
    - Status: approved
    - Blocks-Release: next
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

RECORDS-ONLY plus ONE test class. It edits one table cell in an approved spec, appends one tooled history line, and adds one test class. No production module or behavior changes.

EXECUTION CONTRACT. Commit only the declared paths through `aw commit <plan> -- <paths>`; never `git add -A` or a bare/`-a` commit; never push. Paste actual runner output for every test claim. Do not hand-edit the spec's `## Workflow history` or `- Status:`.

STOP CONDITION. E-01 must stop and report, editing nothing, if any of row 4's three capabilities has become a descriptor field or the cell has already been amended.

LIFECYCLE. Under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; the executor must not. Executed by hand, run `aw ipd begin sa13no` before the first edit and `aw ipd finalize sa13no --actor <agent/model> --message <summary> --apply` at the end. Never hand-move this file to `executed/`. Do not claim done until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

BACKLOG GATE. Backlog `gqy7yd` carries `- Blocks-Release: next`; this plan carries `- From-Backlog: gqy7yd` and the same gate, so the gate is handed off. The runner sets the item `graduated`; it becomes `done` only once this plan is `executed`.
