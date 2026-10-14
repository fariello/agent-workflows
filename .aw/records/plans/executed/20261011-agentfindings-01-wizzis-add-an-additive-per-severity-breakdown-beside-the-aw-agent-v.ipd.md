# IPD: Add an additive per-severity breakdown beside the aw.agent/v1 findings count

- Date: 2026-10-11
- Kind: child
- Concern: The aw.agent/v1 `findings` integer is severity-blind, so a clean, exit-0 record carrying one warning-severity Diagnostic reports `findings: 1`, and an agent has no in-record way to tell gating problems from advisories.
- Scope: Add one additive, optional `findings_by_severity` object (`{"error": n, "warning": n, "info": n}`) to every aw.agent/v1 record built by `CommandResult.to_agent_record` that carries diagnostics, leave the `findings` integer's derivation and meaning unchanged, and document the new field in the agent protocol and output contract docs.
- Scope-Paths: agent_workflows/result_types.py, docs/cli-agent-protocol.md, docs/cli-output-contract.md, tests/test_agent_findings_severity.py, tests/fixtures/conformance_goldens/check_findings.agent.golden
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: 3ouico
- Set: agentfindings
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: wizzis

## Workflow history
- 2026-10-14 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: wizzis verified (set agentfindings, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored review-ready from backlog 3ouico; route decision (additive breakdown, no v2 bump) resolved from repository evidence in OQ-01.

## Goal

Give every explicit `--agent` consumer a severity breakdown of the diagnostics behind `findings`, so a warning- or info-severity advisory can reach an agent without being indistinguishable from a gating problem, and do it additively so no existing aw.agent/v1 consumer sees a changed field meaning.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Record derivation

- [x] E-01 In `agent_workflows/result_types.py`, `CommandResult.to_agent_record`, directly after the existing `# Findings count` block (the `findings_count = (len(self.diagnostics) if self.diagnostics else self.data.get("findings", 0))` assignment), add: when `self.diagnostics` is non-empty, set `rec["findings_by_severity"] = {"error": e, "warning": w, "info": i}` where each count tallies `Diagnostic.severity`, with any severity outside `warning`/`info` (including empty) counted as `error` (fail closed, matching `Diagnostic.severity`'s `"error"` default and `artifact_core.drift_exit_code`'s treatment of non-info as gating). All three keys are always present when the object is emitted. Do NOT change the `findings` derivation. Emit nothing when `self.diagnostics` is empty (the `data["findings"]` fallback has no severity information to report). The key MUST be set before the existing `# Field filtering` block so `--fields` projection governs it like any other optional key (dropped unless requested), and before `_schema.assert_valid_agent_record`.
  - Depends on: none
  - Expected outcome: A record built from diagnostics carries `findings_by_severity` whose three values sum to `findings`; a record with no diagnostics carries no such key; `findings` is byte-for-byte unchanged for every input.
  - Execution state: performed
- [x] E-05 Regenerate the one committed agent golden the new key changes. The `check_findings` fixture in `tests/test_cli_quality_gates.py` `_fixtures` carries two default-severity diagnostics, so `DeterministicByteGoldenTests.test_agent_goldens_stable` FAILS after E-01 (measured at review with E-01 applied in-process: `1 failed, 13 passed` for `tests/test_cli_quality_gates.py`, diff `...,"findings_by_severity":{"error":2,...}`). Run `AW_CONFORMANCE_UPDATE_GOLDENS=1 python3 -m pytest tests/test_cli_quality_gates.py -o addopts=""`, then confirm with `git status --short tests/fixtures/` that ONLY `check_findings.agent.golden` changed and that its diff is exactly the insertion of `"findings_by_severity":{"error":2,"warning":0,"info":0}` and nothing else. The `.json` and `.human` goldens must not change (`CommandResult.to_dict` and the human renderer do not read the new key). If any other golden changes, revert that file and investigate rather than committing it.
  - Depends on: E-01
  - Expected outcome: `tests/test_cli_quality_gates.py` passes again with the single golden updated by exactly the new key.
  - Execution state: performed

### Task group 2: Behavioral tests

- [x] E-02 Create `tests/test_agent_findings_severity.py` that builds `CommandResult` objects and calls `to_agent_record` (and `AgentRenderer().render`), asserting on the returned record: (a) the backlog's measured case, `status="clean"`, `exit_code=0`, one `severity="warning"` Diagnostic, yields `outcome == "clean"`, `exit == 0`, `findings == 1`, `findings_by_severity == {"error": 0, "warning": 1, "info": 0}`; (b) a mixed set (two error, one warning, one info) yields `{"error": 2, "warning": 1, "info": 1}` summing to `findings == 4`; (c) a diagnostic with an unrecognized severity string is counted under `error`; (d) a result with no diagnostics and `data={"findings": 3}` yields `findings == 3` and no `findings_by_severity` key; (e) a clean result with no diagnostics yields `findings == 0` and no `findings_by_severity` key; (f) `OutputContext(mode=OutputMode.AGENT, fields=["findings_by_severity"])` retains the key and the mandatory envelope; (g) every produced record passes `agent_schema.validate_agent_record` with an empty error list.
  - Depends on: E-01
  - Expected outcome: The new test file passes against the E-01 implementation and fails (case a, b, c) against the pre-change code.
  - Execution state: performed

### Task group 3: Documentation

- [x] E-03 In `docs/cli-agent-protocol.md`, add a short subsection (after `## Outcomes and exit codes`, before `## Stream truncation is honest`) titled `## Findings and severity` stating: `findings` counts every diagnostic regardless of severity and its meaning is unchanged; `findings_by_severity` is an optional, additive object present only when the record carries diagnostics, with keys `error`, `warning`, `info` summing to `findings`; the exit code, not `findings`, is the verdict, so a `findings` count of nonzero beside `exit: 0` means advisories only. Also update the `Domain findings (exit: 1)` example record under `## Example records` to carry the new key, since every real record with diagnostics will now carry it and the example would otherwise misdescribe the output. Write no em or en dashes (user-facing doc).
  - Depends on: E-01
  - Expected outcome: The protocol doc names and defines `findings_by_severity` and its sum invariant.
  - Execution state: performed
- [x] E-04 In `docs/cli-output-contract.md`, add one sentence beside the existing compact-record field description (near the `### Domain Findings Result (exit: 1)` example section) defining `findings_by_severity` identically to E-03, so the normative contract and the protocol summary agree, and add the key to that section's example record. No em or en dashes.
  - Depends on: E-03
  - Expected outcome: Both docs define the field with the same keys and the same sum invariant.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The aw.agent/v1 stability rule is stated in `docs/cli-agent-protocol.md` `## Stability`: "Additive, optional fields within `aw.agent/v1` are backward compatible. Any breaking change to record shape or field meaning bumps the version to `aw.agent/v2`." This decides the route (OQ-01).
- `Diagnostic.severity` in `agent_workflows/result_types.py` is a free string defaulting to `"error"`, documented as `"error", "warning", "info"`.
- `artifact_core.drift_exit_code` gates on `severity != "info"`, so empty or unknown severities are treated as gating; E-01 mirrors that fail-closed posture by bucketing unknowns as `error`.
- `agent_schema.filter_record_fields` keeps `_PRESERVED_FIELDS | set(fields)`, so a new optional key is projectable via `--fields` with no schema change, and `agent_schema.validate_agent_record` does not reject unknown keys.
- `tests/test_cli_quality_gates.py` `BudgetGateTests` caps agent records at `BYTE_BUDGET = 1200`; the added object is about 45 bytes and is emitted only when diagnostics exist.
- `tests/test_cli_quality_gates.py` `FactParityGateTests.test_outcome_family_and_findings_parity` asserts `rec["findings"] == len(result.diagnostics)`; E-01 keeps that true.
- Repo test command: bare `python3 -m pytest` (AGENTS.md repo development contract).
- Behavioral tests only (P16): tests call `to_agent_record`/`AgentRenderer.render` and assert on returned records, never on source text.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | `findings` is `len(self.diagnostics)` with no severity filter. | `result_types.CommandResult.to_agent_record`, `# Findings count` block. |
| F2 | The exit code is already severity-correct, so the defect is the count's ambiguity, not the verdict. | `artifact_core.drift_exit_code`. |
| F3 | Non-error diagnostics are emitted today by at least these modules (grep of `severity="warning"`/`severity="info"` at HEAD 87488334e): `artifact_adopt`, `attention` (order_notices), `check_engine`, `cli`, `doctor`, `ipd_lifecycle`, `ipd_lint`, `readiness_recheck`, `research_refs`, `reviews`, `status_set`. Redefining `findings` would change the published number for every one of them. | grep survey during authoring. |
| F4 | No pending plan declares `agent_workflows/result_types.py` in Scope-Paths (per backlog 3ouico), so this plan is the carrier. | backlog 3ouico EVIDENCE section. |

## Proposed changes (ordered, validatable)

1. E-01: additive `findings_by_severity` derivation in `to_agent_record`; E-05: regenerate the one agent golden it changes.
2. E-02: behavioral tests over the record outputs.
3. E-03, E-04: document the field in the protocol summary and the normative contract.

## Deferred / out of scope (with reason)

- Changing the MEANING of `findings` (counting only non-info or only error diagnostics): a field-meaning change that the `## Stability` clause says requires `aw.agent/v2`; out of scope for an additive fix, see OQ-01.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Converting plan qp8fn1's scalar inbox Evidence key into a warning Diagnostic: that is qp8fn1's own scope; this plan only removes the obstacle it named.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Hand-built records that bypass `to_agent_record` (for example stream `summary` records): they do not derive `findings` from `Diagnostic` objects, so there is no severity to break down.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: the committed agent golden `check_findings.agent.golden` changes with the new key; added at review as E-05 / V-05 and to Scope-Paths. The backlog's survey requirement is satisfied by F3, and the additive-vs-v2 decision by OQ-01.

## Required tests / validation

- `python3 -m pytest tests/test_agent_findings_severity.py -o addopts=""` passes (V-02).
- `python3 -m pytest tests/test_cli_quality_gates.py tests/test_agent_field_projection.py tests/test_cli_agent_protocol_doc.py -o addopts=""` passes (no regression of parity, budget, projection, doc-agreement gates).
- Bare `python3 -m pytest` full fast suite: no failure that is absent from a baseline run on the same HEAD before editing (compare failing test ids by name; at review this lane's baseline carried 39 environment-dependent failures, context only).
- `aw ipd lint` on this plan conforms.

## Spec / documentation sync

- `docs/cli-agent-protocol.md` and `docs/cli-output-contract.md` updated (E-03, E-04). No `.spec.md` is touched: no approved spec defines the `findings` derivation (grep of approved/implementing/implemented specs for `findings` beside `aw.agent/v1` found none).

## Open questions

### OQ-01: Change the meaning of `findings`, or add a breakdown beside it?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: Additive breakdown. `docs/cli-agent-protocol.md` `## Stability` states that a changed field meaning bumps to `aw.agent/v2` while additive optional fields are compatible, and F3 shows a redefinition would move the published number for at least eleven emitting modules. The backlog item names the additive route as a valid sibling. A future v2 redefinition remains possible and is not foreclosed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Paste `git diff -- agent_workflows/result_types.py` showing the `findings_by_severity` block added after the `# Findings count` block and the `findings_count` assignment unchanged, PLUS pasted stdout of `python3 -c` constructing `CommandResult(command="x", status="clean", exit_code=0, diagnostics=[Diagnostic(location="a", rule="r", detail="d", severity="warning")]).to_agent_record()` showing `"outcome": "clean"`, `"exit": 0`, `"findings": 1`, `"findings_by_severity": {"error": 0, "warning": 1, "info": 0}` (code path: `CommandResult.to_agent_record`).
  - Observed evidence: git diff -- agent_workflows/result_types.py:
    @@ -435,6 +435,18 @@ class CommandResult:
             )
             rec["findings"] = int(findings_count)

    +        if self.diagnostics:
    +            severity_counts = {"error": 0, "warning": 0, "info": 0}
    +            for d in self.diagnostics:
    +                sev = getattr(d, "severity", None)
    +                if sev == "warning":
    +                    severity_counts["warning"] += 1
    +                elif sev == "info":
    +                    severity_counts["info"] += 1
    +                else:
    +                    severity_counts["error"] += 1
    +            rec["findings_by_severity"] = severity_counts
    +
             # Changes
             if self.changes:
                 if is_verbose:
    python3 -c CommandResult(...).to_agent_record() output:
    {"schema": "aw.agent/v1", "kind": "result", "cmd": "x", "outcome": "clean", "exit": 0, "verified": true, "complete": true, "findings": 1, "findings_by_severity": {"error": 0, "warning": 1, "info": 0}, "diagnostics": [{"location": "a", "rule": "r"}], "next": null}
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Pasted runner output of `python3 -m pytest tests/test_agent_findings_severity.py -o addopts="" -v` listing every case (a) through (g) as PASSED, plus pasted output of the full bare `python3 -m pytest` run showing its summary line, with its failing test ids compared BY NAME against a baseline bare run on the same HEAD before editing and zero new failures.
  - Observed evidence: python3 -m pytest tests/test_agent_findings_severity.py -o addopts="" -v:
    tests/test_agent_findings_severity.py::AgentFindingsSeverityTests::test_case_g_all_produced_records_pass_schema_validation PASSED [ 14%]
    tests/test_agent_findings_severity.py::AgentFindingsSeverityTests::test_case_f_fields_projection_retains_severity_and_envelope PASSED [ 28%]
    tests/test_agent_findings_severity.py::AgentFindingsSeverityTests::test_case_a_single_warning_diagnostic_clean_exit_zero PASSED [ 42%]
    tests/test_agent_findings_severity.py::AgentFindingsSeverityTests::test_case_b_mixed_severity_diagnostics_sum_to_findings PASSED [ 57%]
    tests/test_agent_findings_severity.py::AgentFindingsSeverityTests::test_case_e_clean_result_no_diagnostics_omits_severity_breakdown PASSED [ 71%]
    tests/test_agent_findings_severity.py::AgentFindingsSeverityTests::test_case_c_unrecognized_severity_counted_under_error PASSED [ 85%]
    tests/test_agent_findings_severity.py::AgentFindingsSeverityTests::test_case_d_data_findings_fallback_omits_severity_breakdown PASSED [100%]
    7 passed in 0.14s.
    Full suite run compared against baseline bare run on same HEAD before editing:
    Baseline: 8357 passed, 4 skipped, 18 xfailed, 3 warnings in 568.67s (0:09:28)
    Post-change: 8364 passed, 4 skipped, 18 xfailed, 3 warnings in 403.98s (0:06:43)
    Zero failures in both baseline and post-change, exactly 7 new passing tests from tests/test_agent_findings_severity.py.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Paste `git diff -- docs/cli-agent-protocol.md` showing the `## Findings and severity` section naming `findings_by_severity`, its three keys, and the sum invariant, plus pasted output of `python3 -m pytest tests/test_cli_agent_protocol_doc.py -o addopts=""` passing.
  - Observed evidence: git diff -- docs/cli-agent-protocol.md:
    +## Findings and severity
    +
    +`findings` counts every diagnostic regardless of severity and its meaning is unchanged. `findings_by_severity` is an optional, additive object present only when the record carries diagnostics, with keys `error`, `warning`, `info` summing to `findings`. The exit code, not `findings`, is the verdict, so a `findings` count of nonzero beside `exit: 0` means advisories only.
    ...
    -{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":2,"diagnostics":[{"location":"a.md","rule":"check.name-nonconformant"}],"next":"aw group plans x --set y"}
    +{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":2,"findings_by_severity":{"error":2,"warning":0,"info":0},"diagnostics":[{"location":"a.md","rule":"check.name-nonconformant"}],"next":"aw group plans x --set y"}
    Doc test runner output: python3 -m pytest tests/test_cli_agent_protocol_doc.py -o addopts="" -> 3 passed in 0.11s.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Paste `git diff -- docs/cli-output-contract.md` showing the added definition with the same keys and sum invariant as V-03, plus pasted output of `grep -nP '[\x{2013}\x{2014}]'` over the added lines of both docs returning nothing.
  - Observed evidence: git diff -- docs/cli-output-contract.md:
    +`findings_by_severity` is an optional, additive object present only when the record carries diagnostics, with keys `error`, `warning`, `info` summing to `findings`.
    -{"schema":"aw.agent/v1","kind":"result","cmd":"check specs","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":2,"diagnostics":[{"location":"specs/01.md","rule":"spec.draft"},{"location":"specs/02.md","rule":"spec.title"}],"next":"aw check specs --fix"}
    +{"schema":"aw.agent/v1","kind":"result","cmd":"check specs","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":2,"findings_by_severity":{"error":2,"warning":0,"info":0},"diagnostics":[{"location":"specs/01.md","rule":"spec.draft"},{"location":"specs/02.md","rule":"spec.title"}],"next":"aw check specs --fix"}
    git diff -U0 docs/cli-agent-protocol.md docs/cli-output-contract.md | grep '^+[^+]' | grep -nP '[\x{2013}\x{2014}]' exited 1 with zero output (no em or en dashes found in added lines).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Paste the regeneration command and its output, `git status --short tests/fixtures/` showing only `check_findings.agent.golden` modified, `git diff -- tests/fixtures/conformance_goldens/check_findings.agent.golden` showing only the `findings_by_severity` insertion, and `python3 -m pytest tests/test_cli_quality_gates.py -o addopts=""` passing WITHOUT the update env var.
  - Observed evidence: AW_CONFORMANCE_UPDATE_GOLDENS=1 python3 -m pytest tests/test_cli_quality_gates.py -o addopts="" -> 15 passed in 0.86s.
    git status --short tests/fixtures/:
     M tests/fixtures/conformance_goldens/check_findings.agent.golden
    git diff -- tests/fixtures/conformance_goldens/check_findings.agent.golden:
    -{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"plans","checked":41,"findings":2,"evidence":["checked:41"],"diagnostics":[{"location":"a.md","rule":"check.name-nonconformant"},{"location":"b.md","rule":"check.setid-collision"}],"next":"aw group plans x --set y"}
    +{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"plans","checked":41,"findings":2,"findings_by_severity":{"error":2,"warning":0,"info":0},"evidence":["checked:41"],"diagnostics":[{"location":"a.md","rule":"check.name-nonconformant"},{"location":"b.md","rule":"check.setid-collision"}],"next":"aw group plans x --set y"}
    Without update env var: python3 -m pytest tests/test_cli_quality_gates.py -o addopts="" -> 15 passed in 0.52s.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:
- Open questions: OQ-01 is resolved; none are open.
- Scope fence: `- Scope-Paths:` is a declaration, not a stop condition. An out-of-scope edit is made and justified at finalize with `--scope-reason <path>=<why>`; a declared path left unmodified needs `--scope-ack`.
- Commit only the edited Scope-Paths through `aw commit wizzis -- <paths>`; never `git add -A`; never push. Check `git diff --cached --name-only` before committing and re-check after any failed commit.
- You MUST paste ACTUAL runner output; never claim a result you did not run, and never mark a `V-*` `pass` from its E-item checkmark.
- Lifecycle: begin with `aw ipd begin`. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan moves to `executed/` through the tooled lifecycle, never a hand `git mv`. Under `aw oc run` / `aw agy run` the driver self-finalizes and the executor does NOT run `aw ipd finalize`; when executing by hand outside a runner, the executor runs `aw ipd finalize wizzis`.
