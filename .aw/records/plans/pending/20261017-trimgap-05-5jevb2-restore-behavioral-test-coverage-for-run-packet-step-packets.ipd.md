# IPD: Restore behavioral test coverage for run_packet step packets and outcome envelopes

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `aq04yg` (Set `trimgap`, group 5 of the `b1mx2w` filing plan) records that all 10 candidate production keys in `agent_workflows/run_packet.py` (396 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. Their behavioral tests lived in `tests/test_run_packet_gates.py`, deleted wholesale by the suite trim `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"). The only surviving caller, `tests/test_core_module_coverage.py::test_run_packet_envelope`, constructs a `StepOutcomeEnvelope` and reads two attributes back, and calls `_normalize` once; it never calls `to_dict`, `build_step_packet`, `validate_outcome_envelope`, or `apply_outcome_envelope`. So a mutation that, for example, made `validate_outcome_envelope` accept a foreign actor, made `apply_outcome_envelope` mutate the ledger on unsupported prose, or made the packet digest ignore a changed requirement would pass the routine suite.
- Scope: Add ONE new behavioral test module, `tests/test_run_packet_restored_behavior.py`, that drives the 10 keys through their public call surfaces and asserts on real return values, raised exceptions, and durable ledger side effects. The 10 keys: `StepPacket.to_dict`, `StepOutcomeEnvelope.to_dict`, `_compute_packet_digest`, `BoundRequirement.to_dict`, `StepPacket.to_json`, `_normalize`, `build_step_packet`, `validate_outcome_envelope`, `StepPacket.render_prompt`, `apply_outcome_envelope`. Restores the outcome-envelope and step-packet cases of the deleted `19313eed^:tests/test_run_packet_gates.py` (classes `TestStepPacketRendering`, `TestOutcomeEnvelopeLegality`, `TestStepPacketEdgeCases`) in pytest form, plus a small number of branch cases the deleted file did not pin. EXCLUDES any change to `agent_workflows/run_packet.py` or any other production file, EXCLUDES editing `tests/test_core_module_coverage.py`, and EXCLUDES the deleted `TestHumanDecisionGates` class, which tests `agent_workflows/run_gates.py` and belongs to the sibling backlog item `ziuj5c`.
- Scope-Paths: tests/test_run_packet_restored_behavior.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: aq04yg
- Set: trimgap
- Order: 5
- Highest E allocated: 06
- Author: opencode
- Id: 5jevb2
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Readiness go-pending-approval. Review record .aw/records/reviews/20261017-trimgap-05-5jevb2-restore-behavioral-test-coverage-for-run-packet-step-packets.review.md

- 2026-10-17 to-review (opencode): authored from backlog `aq04yg`. Ran the deleted `19313eed^:tests/test_run_packet_gates.py` unchanged against HEAD `92bdf4171` (20 tests, OK) and measured each extra branch by direct call before writing any expected outcome (Findings F-02 through F-06), so the expected values below are observed and not inferred from docstrings.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 10 `unguarded-unreached` `run_packet` keys from backlog `aq04yg` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on outputs, exceptions, and ledger records. Done means a mutation that breaks packet contract fields, digest determinism or sensitivity, budget enforcement, serialization, envelope validation codes, or fail-closed application turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: new behavioral test module

- [ ] E-01 Create `tests/test_run_packet_restored_behavior.py` with `pytestmark = pytest.mark.core`, importing `agent_workflows.run_packet`, `run_freeze`, `run_engine`, `run_ledger_store` and `run_ledger_schema`. Add a module docstring naming backlog `aq04yg`, findings `b1mx2w`, and the deleted source file `tests/test_run_packet_gates.py` at `19313eed^`. Add two pytest fixtures restored from the deleted file's `setUp` methods: `packet_workflow` (the three-step `test-step-packet-wf` workflow dict with permissions, three requirements, and steps `S-01`..`S-03`) plus `frozen_reqs` (`run_freeze.freeze_requirements` of the deleted file's `raw_requirements`), and `released_engine(tmp_path)` (a `run_ledger_store.RunLedgerStore(tmp_path / "run.jsonl")` seeded with the `run` and `requirement_set` records, a `run_engine.RunEngine` over the one-step `envelope-test-wf`, with `S-01` released and started). Use `tmp_path` only; spawn no subprocess.
  - Depends on: none
  - Expected outcome: the file exists, is collected by a bare `python3 -m pytest` (it carries the `core` marker), and imports cleanly.
  - Execution state: pending

- [ ] E-02 Add step-packet contract tests restored from the deleted `test_golden_packet_contains_every_contract_field`, `test_packet_omits_unrelated_bulk_context`, and `test_unknown_step_id_raises_key_error`. Using `packet_workflow`/`frozen_reqs`, `run_packet.build_step_packet(..., step_id="S-01", run_id="run-12345678", attempt=1, frozen_requirements=frozen_reqs)` must yield: `run_id`, `workflow_id == "test-step-packet-wf"`, `step_id`, `attempt`, a timestamp accepted by `run_ledger_schema.is_timestamp`; `action`, `expected_artifacts == ("agent_workflows/run_packet.py",)`, `evidence_contract == ("test_report", "artifact")`, `stop_conditions`, `depends_on == ()`; `scope_fence` holding `allowed_paths`, `forbidden_paths` and `mutation_boundary == "product"`; `allowed_files == ("agent_workflows/**", "tests/**")`; bound requirement ids exactly `["R-01"]` (not R-02/R-03); an exit checklist of at least 3 items mentioning action and evidence; `trace == {"S-01": ["R-01"]}`; `run_ledger_schema.is_sha256(packet_digest)`. `render_prompt()` contains the S-01 action, the `## Bound Requirements & Success Criteria`, `## Expected Artifacts`, `## Required Evidence Contract`, `## Allowed Scope & Tools`, `## Stop Conditions` and `## Step Exit Checklist` headings, a `- [ ] ` checklist line, the `mutation_boundary: product` scope line, and does NOT contain the S-02 or S-03 actions. A workflow wrapped as `{"workflow": {...}}` yields the same `workflow_id`. `step_id="S-99"` raises `KeyError`. Explicit `allowed_tools=("view_file",)` is reflected in `allowed_tools`; omitting it yields `run_packet.DEFAULT_ALLOWED_TOOLS`. Also assert a minimal packet (`{"id": "m", "steps": [{"id": "S", "action": "act"}]}`) with no requirements, artifacts, evidence or stop conditions renders a prompt WITHOUT the `## Bound Requirements & Success Criteria`, `## Expected Artifacts`, `## Required Evidence Contract` and `## Stop Conditions` headings (the empty-section branches of `render_prompt`). It still contains `## Allowed Scope & Tools` (the default tools are non-empty) and `## Step Exit Checklist` (always present); measured at review.
  - Depends on: E-01
  - Expected outcome: packet contract, prompt rendering (both populated and empty-section branches), wrapper unwrapping, tool defaulting, and unknown-step tests pass.
  - Execution state: pending

- [ ] E-03 Add requirement-binding and digest tests. (a) Restored `test_packet_digest_changes_when_bound_requirement_changes`, with EVERY build in the test passing the same explicit `timestamp="2026-01-01T00:00:00Z"`: rebuilding with a revised frozen R-01 text changes `packet_digest`, and rebuilding with identical inputs yields an equal digest AND an equal `to_json()`. Do NOT restore the deleted test's timestamp-less builds verbatim: the timestamp is part of the digest (measured at review: builds one second apart differ), so without a pinned timestamp the stability assertion is flaky across a second boundary, and the sensitivity assertion can pass from timestamp drift alone even when a mutant ignores the requirement text. (b) Digest round trip: `run_packet._compute_packet_digest(packet.to_dict()) == packet.packet_digest` (the function drops `packet_digest` before hashing), and changing any one field of `to_dict()` (for example `action`) yields a different digest. (c) Binding branches, each asserted by the `BoundRequirement` produced: a raw requirement with no frozen set binds `category == "must"`, its `text`, and `digest == hashlib.sha256(text.encode()).hexdigest()`; a raw requirement given `"description"` and no `"text"` binds the description text; a raw requirement whose text differs from a frozen item only by whitespace binds to that frozen item's text and digest, which reaches `_normalize`. Use `run_freeze.freeze_requirements({"must": ["first thing", "second thing"]})` with the raw text `"  second\n  thing "` as the step's FIRST `satisfies` entry, so the positional fallback (`frozen_must_items[idx]`) would bind `first thing` instead; the assertion `text == "second thing"` therefore fails if `_normalize` stops normalizing (measured at review: binds `second thing`, digest `731e4810...`); a `satisfies` id that is neither frozen nor raw, given a frozen set, binds the frozen must item at its position (positional fallback branch; measured at review: `satisfies: ["X-9", "Y-9"]` against that frozen set binds `first thing`, `second thing`); a `satisfies` id that equals a frozen id (for example `M-01`) binds that frozen item directly; and `_normalize("  a \n\t b  ") == "a b"`.
  - Depends on: E-01
  - Expected outcome: digest determinism and sensitivity (timestamp pinned), digest round trip, and all five binding branches pass.
  - Execution state: pending

- [ ] E-04 Add serialization and budget tests. (a) Restored `test_packet_serialization_roundtrip`: for the deleted file's `wf-roundtrip` workflow at `attempt=2`, `json.loads(packet.to_json())` carries `run_id`, `step_id`, `attempt == 2`, two `bound_requirements`, `depends_on == ["S-00"]`, `expected_artifacts`, `evidence_contract`, `allowed_files == ["src/**"]`, and `scope_fence["forbidden_paths"] == ["secret/**"]`; `to_json(indent=None)` contains no newline and parses to the same object; and `parsed["bound_requirements"][0]` has exactly the keys `id`, `category`, `text`, `digest` (`BoundRequirement.to_dict`). (b) `to_dict()` returns plain lists (not tuples) for every sequence field, so `json.dumps(packet.to_dict())` succeeds without a custom encoder. (c) Restored `test_packet_size_budget_enforcement`: `budget_bytes=8192` builds and the rendered prompt is under 8192 bytes; `budget_bytes=50` raises `run_packet.PacketBudgetExceededError`, which is a `run_packet.RunPacketError`.
  - Depends on: E-01
  - Expected outcome: JSON round trip, compact-indent form, key shape, list typing, and both budget outcomes pass.
  - Execution state: pending

- [ ] E-05 Add `validate_outcome_envelope` and `StepOutcomeEnvelope.to_dict` tests (pure, no engine). (a) `to_dict()` of a minimal `StepOutcomeEnvelope("r", "s", 1, "blocked")` equals `{"run_id": "r", "step_id": "s", "attempt": 1, "status": "blocked", "actor": "executor", "evidence_ids": [], "artifacts": []}` exactly (optional keys omitted when falsy), and with `prose`, `block_reason`, `failure_reason`, `timestamp` set, each appears. (b) Restored acceptance: `performed` with an evidence id and required kinds, `blocked` with `block_reason`, and `failed` with `failure_reason` each return `ok is True` with an `envelope` whose fields match; a plain mapping input is accepted the same as the NamedTuple. (c) One parametrized row per rejection code, asserting `ok is False` and the code present in `findings`: raw string -> `OE-UNSUPPORTED-PROSE` with `envelope is None`; `{"prose": ...}` without status -> `OE-UNSUPPORTED-PROSE`; mapping missing `attempt` -> `OE-INVALID-STRUCTURE` with `where == "attempt"`; `attempt=True` -> `OE-INVALID-STRUCTURE`; `status="bogus"` -> `OE-INVALID-STATUS`; foreign actor -> `OE-FOREIGN-ACTOR`; mismatched run id -> `OE-RUN-MISMATCH`; mismatched step id -> `OE-STEP-MISMATCH`; `attempt=5` vs expected 1 -> `OE-WRONG-ATTEMPT`; `performed` with empty `evidence_ids` and required kinds -> `OE-MISSING-EVIDENCE`. (d) Controls: `performed` with empty evidence but NO required kinds is ok; non-mapping entries in `artifacts` and non-string entries in `evidence_ids` are dropped from the returned envelope.
  - Depends on: E-01
  - Expected outcome: exact `to_dict` shape, three accepted statuses, 10 rejection rows, and the controls pass.
  - Execution state: pending

- [ ] E-06 Add `apply_outcome_envelope` tests against `released_engine`, restored from the deleted `TestOutcomeEnvelopeLegality`. (a) A `performed` envelope with evidence and artifacts `({"path": "output.txt", "sha256": "d"*64}, {"path": "nosha.txt"})` returns a snapshot with `state == "performed"`, `engine.step_state("S-01") == "performed"`, and the ledger (`store.read_records()`) gains exactly one `step_attempt` and exactly one `artifact_ref` record whose `path == "output.txt"` (the sha-less artifact is not recorded). (b) Fail-closed, one parametrized row per typed exception, each asserting the exception type AND that the ledger record count and `engine.step_state("S-01") == "running"` are unchanged afterwards: unsupported prose inputs (the deleted file's four inputs) -> `run_packet.OutcomeEnvelopeError`; prose string -> `UnsupportedProseError`; foreign actor -> `ForeignActorError`; `attempt=5` -> `WrongAttemptError`; empty evidence with `required_evidence_kinds=["test_report"]` -> `MissingEvidenceError`; `status="bogus"` -> `InvalidOutcomeEnvelopeError`; mismatched `run_id` -> `InvalidOutcomeEnvelopeError`.
  - Depends on: E-01
  - Expected outcome: the accepted application writes exactly the expected ledger records, and every rejection raises its typed exception while leaving the ledger and step state unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). No `inspect`, `ast`, regex over production source, or docstring pinning. Every assertion calls the function and checks a return value, an exception, or a ledger record. The prompt headings in E-02 are the rendered output a model consumes, asserted only for presence or absence as section-branch evidence, not for prose wording.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`), under a 30s budget. The new module must carry `pytestmark = pytest.mark.core` and stay fast (no subprocess); the deleted module ran its 20 tests in 0.189s (F-02).
- Sibling plan `33f8tn` (`trimgap` Order 9) sets the precedent this plan follows: one new `*_restored_behavior.py` core-marked module per backlog item, no production edits, mutation spot-checks as reverted scratch edits.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows for `agent_workflows/run_packet.py::*`; `rg run_packet tests/` | Exactly 10 `run_packet` keys, all `unreached` / `unguarded-unreached` (6 `cost-cap`, 4 `budget-exhausted` in the probe table, all unreached). The only test referencing the module is `tests/test_core_module_coverage.py::test_run_packet_envelope`, which constructs a `StepOutcomeEnvelope` and calls `_normalize`, reaching none of the serialization, validation, building or application bodies. |
| F-02 | `git show 19313eed^:tests/test_run_packet_gates.py \| PYTHONPATH=. python3 -` at HEAD `92bdf4171` | The deleted module runs unchanged: `Ran 20 tests in 0.189s`, `OK`. Its step-packet and envelope cases therefore still describe current behavior and can be restored with their original inputs. `19313eed^:tests/test_host_runner.py` contains no `run_packet` reference, so there is nothing to mine there for this module. |
| F-03 | direct calls | `_compute_packet_digest(packet.to_dict()) == packet.packet_digest` is True; two builds with the same explicit timestamp give equal digests and equal `to_json()`. |
| F-04 | direct calls | Raw requirement without frozen set binds `category="must"` with sha256 of its text; raw text `"  second\n  thing "` against frozen `M-02 "second thing"` binds `M-02`'s text and digest via `_normalize`; `_normalize("  a \n\t b  ") == "a b"`. Review correction: `freeze_requirements` of the deleted file's `raw_requirements` yields `M-01`, `M-02`, `M-03`, `SC-01`, `V-01`, `O-01` (three must items, not two). |
| F-05 | direct calls | Minimal `StepOutcomeEnvelope.to_dict()` is exactly `{run_id, step_id, attempt, status, actor: "executor", evidence_ids: [], artifacts: []}`; `attempt=True` yields `OE-INVALID-STRUCTURE` at `attempt`; `status="bogus"` yields `OE-INVALID-STATUS`; `ATTEMPT_STATES` is `blocked`, `failed`, `performed`. |
| F-06 | direct call of `apply_outcome_envelope` on a seeded engine | A `performed` envelope with one sha-bearing and one sha-less artifact appends exactly `['step_attempt', 'artifact_ref']` and leaves `step_state("S-01") == "performed"`. |

## Proposed changes (ordered, validatable)

1. E-01 creates the core-marked module and fixtures.
2. E-02 covers `build_step_packet` contract fields and `StepPacket.render_prompt`.
3. E-03 covers requirement binding, `_normalize`, and `_compute_packet_digest`.
4. E-04 covers `StepPacket.to_dict`, `StepPacket.to_json`, `BoundRequirement.to_dict`, and the size budget.
5. E-05 covers `validate_outcome_envelope` and `StepOutcomeEnvelope.to_dict`.
6. E-06 covers `apply_outcome_envelope` and its fail-closed ledger behavior.

## Deferred / out of scope (with reason)

- The deleted `TestHumanDecisionGates` cases exercise `agent_workflows/run_gates.py`, not `run_packet`; restoring them is the scope of the sibling backlog item for `run_gates`.
  - Carrier: ziuj5c
- Editing or replacing the shallow `tests/test_core_module_coverage.py::test_run_packet_envelope` is out of scope: it is harmless, owned by the core-coverage plan that wrote it, and this plan's module supersedes its reach without changing it.
  - Carrier-Declined: no work is owed; the reach gap this item records is closed by E-01 to E-06.

## Scope check

- Over-scope: none. One new test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none. All 10 keys named by `aq04yg` are covered by E-02 to E-06.

## Required tests / validation

- `python3 -m pytest tests/test_run_packet_restored_behavior.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest`: every test passes, with the summary line pasted. The core-tier WALL-TIME budget is already exceeded on this host before this plan adds anything (measured at review: `753 passed in 43.70s`, `CORE TIER BUDGET EXCEEDED`), a known defect tracked by backlog `o58dro`, so the budget line is reported and not a pass/fail bar for this plan; the bar is that the new module itself runs in under 1s (`python3 -m pytest tests/test_run_packet_restored_behavior.py -o addopts="" -q` duration pasted; the deleted cases ran `20 passed in 0.70s` at review).
- Reach: `COVERAGE_FILE=/tmp/opencode/cov5jevb2 python3 -m pytest tests/test_run_packet_restored_behavior.py -o addopts="" -p no:cacheprovider --cov=agent_workflows.run_packet --cov-report=term-missing` shows the bodies of all 10 keys executed (every line of `build_step_packet`, `validate_outcome_envelope`, `apply_outcome_envelope`, `render_prompt`, and the four `to_dict`/`to_json` methods absent from the Missing column, or each remaining missed line named and explained); paste the output. `COVERAGE_FILE` outside the repo keeps an untracked `.coverage` out of the worktree.
- Mutation spot-check: temporarily apply, in scratch edits not committed, one mutation per group (make `build_step_packet` skip the budget check; make `_compute_packet_digest` return a constant; make `_normalize` return its input unchanged; make `StepPacket.to_dict` drop `depends_on`; make `validate_outcome_envelope` skip the `actor not in authorized_actors` check; make `apply_outcome_envelope` call `engine.record_step_attempt` before validation), run the new module, and paste the failure for each; then revert and confirm `git diff agent_workflows/` is empty.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Should the new module be core-marked, or only non-slow?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: core-marked. The routine gate a bare `python3 -m pytest` runs is the core tier (`conftest.pytest_collection_modifyitems`), so non-core coverage would still be absent from the merge gate. The restored cases ran in 0.189s (F-02), well inside the 30s core budget; V-01 requires the runtime be shown.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --stat` (and `git status --short`) showing only `tests/test_run_packet_restored_behavior.py` added; paste the bare `python3 -m pytest` summary line showing every test passed with the new module included (`python3 -m pytest --collect-only -q | rg -c test_run_packet_restored_behavior` nonzero), the module's own run time under 1s, and the core-tier wall-time line as observed (an overrun is reported against `o58dro`, not a failure of this item).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing the packet-contract, prompt-rendering, empty-section, wrapper, tool-default and unknown-step tests as PASSED, and the failures produced by making `build_step_packet` ignore `allowed_tools` and by making `render_prompt` drop the `if self.stop_conditions:` guard so the heading is always emitted (each reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing the digest and binding tests as PASSED, and the failures produced by making `_compute_packet_digest` return a constant string and by making `_normalize` return its input unchanged (each reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` output listing the serialization and budget tests as PASSED, and the failures produced by making `StepPacket.to_dict` drop `depends_on` and by removing the budget check in `build_step_packet` (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` output listing the `to_dict` shape test, three acceptance cases, all 10 rejection rows and the controls as PASSED, and the failure produced by removing the `actor not in authorized_actors` check in `validate_outcome_envelope` (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `-v` output listing the application and fail-closed rows as PASSED; the failure produced by moving `engine.record_step_attempt` ahead of validation in `apply_outcome_envelope` (reverted afterwards); the coverage output showing all 10 keys' bodies executed; and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:
- All open questions are resolved (OQ-01).
- Scope fence: `tests/test_run_packet_restored_behavior.py` is the only declared path; an out-of-scope edit is made and justified at finalize (`--scope-reason`), not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (return values, raised exceptions, ledger records), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). Do not pin behavior the deleted file did not pin and the plan does not name (for example, `apply_outcome_envelope` with an unknown `step_id` raises a bare `KeyError` at review, outside the typed `OutcomeEnvelopeError` hierarchy; leave it untested here rather than freeze it).
- Mutation spot-checks are scratch edits to `agent_workflows/run_packet.py` that must be reverted before commit and must not appear in the diff; confirm with an empty `git diff agent_workflows/`.
- Commit only through `aw commit 5jevb2 -- tests/test_run_packet_restored_behavior.py`, verify `git diff --cached --name-only` lists only that path, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming with every V-item at `Result: pass`, then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
