# Review: Decide whether a driver run writes a hash-chained ledger

- Subject-Id: rdjka2
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a80075f56` in the sweep lane. The plan was committed and unchanged against its sealed lane input, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits; its two diagnostics are info-level `IPD-Z602` on E-04 and E-06.

Re-verified:

- F-01 to F-03: 0 `ledger.jsonl` files; both drivers grep 0; all eight `run_recovery` public functions take `engine` first.
- F-05: 11 / 14 states, intersection `{'failed'}`.
- F-06: zero `"kind": "run"` writers under `agent_workflows/`. The only writer is the test helper `_run_record` in `tests/test_run_recovery_cli.py`.
- F-07, live run at HEAD: `release_step ok`, `start_step ok`, then `record_step_attempt RAISED SchemaInvalidRecordError (Finding(code='RL-E041', ...))`. Afterwards `ledger.jsonl` does not exist but `ledger.jsonl.lock` does. With attempt state `succeeded` the call raises `IllegalTransitionError` instead.
- F-08: `aw run start run-abc123 --step S-01` gives rc=2 with the quoted message.
- F-10: 123 `append_jsonl(... events.jsonl` sites now (106 at authoring).
- F-12: `capture_command(actor="driver", evidence_kind="tests")` gives tool_event `(False, ['RL-E014'])` and envelope `(False, ['RL-E014','RL-E033'])`. Defaults give `(True, [])` / `(True, [])`. `host_runner`'s default branch passes neither argument.
- The `retrywire` header strings E-04 targets are present. The `run_recovery` "is still DORMANT" and "ZERO production callers today" strings are present. `plan_retry`/`retry_budget_remaining` have no caller outside `run_recovery.py`.
- `hrdmfy` is now `approved`, and its E-03 makes `start_step` append.
- `docs/recovery.md:15` says "`plan_retry` has no production callers today".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | MEDIUM | UNDER-SCOPE | Plan executability (G) / scope fence | plan `- Scope-Paths:`; E-02 `aw research new`; E-06 `aw backlog set` | E-02 writes under `.aw/records/research/` and E-06 amends a backlog item, but neither path was declared. Finalize would therefore demand a `--scope-reason` for the plan's own primary deliverable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `.aw/records/research/`, `.aw/records/backlog/` and `docs/recovery.md` (PR-207). Directory entries have in-tree precedent. |
| PR-202 | HIGH | IN-SCOPE | Testing (E) | live F-07 re-run above; `hrdmfy` E-03 "make `RunEngine.start_step` APPEND a `step_started` record" | E-06's invariant says the sequence "leaves NO file on disk", but the store leaves `ledger.jsonl.lock` behind, so a literal test fails on the unmodified tree. It also never said which attempt state to use, and `succeeded` raises a different error. Approved `hrdmfy` moves the raise from `record_step_attempt` to `start_step`, so a test that pins which method raises would break on an unrelated plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now names a legal state (`performed`), asserts the absence of `ledger.jsonl` rather than an empty directory, and wraps the whole sequence in one `pytest.raises` without pinning the raising method. V-06 and the validation list were updated to match. |
| PR-203 | MEDIUM | IN-SCOPE | Internal consistency | E-06 "does not call `aw backlog new`"; V-06 "carrier (i) created by `aw backlog new` ... carrier (ii) ... present if and only if the answer is (a)"; Proposed change 6 "file the carriers" | V-06 and Proposed change 6 still described carrier creation, which contradicts E-06's reconciliation design. Both carriers already exist, so V-06 would FAIL under answer (b) because `hegwri` exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote V-06, Proposed change 6, the Scope OUT clause, E-04's (a) branch and the post-gate text to "reconcile `1g8lbe`/`hegwri`". The `hegwri` amendment is now made by tool (`aw backlog set ... --message`). |
| PR-204 | MEDIUM | IN-SCOPE | Evidence accuracy | `agent_workflows/host_runner.py:193` `_ev.capture_command(packet.run_id, list(packet.argv), cwd=..., timeout=..., max_output_bytes=...)`; live validation `(True, [])` | F-12, the history and the Deferred entry say two call sites pass an unknown role. `host_runner` passes no actor or kind and its records validate. Carrier `1g8lbe` already says so. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected F-12 and the Deferred entry. |
| PR-205 | LOW | IN-SCOPE | Evidence accuracy | live F-07 | F-07 did not say which call raises or that a lock file remains. | all Low | FIXED | Added the review re-measurement to F-07. |
| PR-206 | LOW | IN-SCOPE | Live-artifact criteria | 123 sites vs 106 | E-01 bound the F-10 tally to a count that drifts. | all Low | FIXED | E-01 now states the property (zero chain fields); the count is context only. |
| PR-207 | MEDIUM | UNDER-SCOPE | Spec/doc sync | `docs/recovery.md:15` | Under (b), E-05 "corrects" the zero-callers claim, but it is TRUE of `plan_retry` and false only of the module as a whole. The user-facing doc repeats the claim and was not considered. An executor could write a false statement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now narrows the claim per function. Under (b) it may add at most one dash-free sentence to `docs/recovery.md`. V-05 checks both. |
| PR-208 | MEDIUM | IN-SCOPE | Executability / honesty under unattended run | E-03; approval gate | The plan depends on asking the maintainer, but `aw oc run` turns have no interaction channel. Under the old text, an unattended executor could have marked E-04 to E-06 "unperformed" with no state, or mistaken a runner prompt for an answer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now says that with no channel, OQ-01 stays open, E-03 to E-06 are marked `blocked`, and the plan stays pending. Runner prompts, comms and notes are not the maintainer's answer. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Must OQ-01 (the ledger decision) be answered before review completes? | No. It stays `Blocking: no`, `Status: open`, owned by the maintainer, and is answered at E-03. | Escalate to `Blocking: yes` now (it would block E-01/E-02, which produce the analysis the maintainer needs); answer it as the reviewer (forges a maintainer decision on a public contract) | plan OQ-01 rationale; precedent `denypush` `x2dwu5` was reviewed `go-pending-approval` with a non-blocking open OQ-01; plan-review "A NON-BLOCKING open question does NOT make a plan NO-GO" (maintainer ruling 2026-09-10) | yes |
| D-2 | Should E-06's test pin which call raises? | No. It pins the sequence-level `RL-E041` and the absence of `ledger.jsonl`. | Pin `record_step_attempt` (breaks when approved `hrdmfy` lands) | `hrdmfy` E-03 text; live re-run | yes |
