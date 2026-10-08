# Review findings: plan tb6lw3

- Subject-Id: tb6lw3
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, open), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `383ebc1ee`. The plan was committed and byte-identical to the lane
input, so there was no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review. After revision,
`--phase review-finalize` reports `IPD-Q501` (the deliberately escalated blocking OQ-02) and advisory `IPD-Z602` (info)
only. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply. Baseline for the affected tests:
`python3 -m pytest tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py
tests/test_retry_class_mapping.py tests/test_host_capability_extension.py -o addopts="" -q` -> `59 passed in 22.57s`;
`aw specs check` on spec `25kzda` -> `clean`.

Verified: the spec's 5.5 lists, 5.5 mapping table, 5.7 rows and 4.1 six-class table read as F-01/F-04 say;
`run_evidence.ABORT_CLASSES` holds the six names; `oc_runipd.run_queue` `except DriverError` sets `failed-safely`
(F-02); `runner_shared.compute_scope_reconciliation` writes "auto-reconciled by" (F-03); `RUN-COMMIT-GATEWAY`
is `UNBOUND_BY_DEPENDENCY`. Measured per-row abort state from the shipped table: always = `RUN-BASELINE-OWNERSHIP`,
`RUN-LEDGER-INTEGRITY`; conditional = `RUN-FROZEN-IDENTITY`, `RUN-COMMIT-CONTENTS`, `RUN-COMMIT-GATEWAY`,
`RUN-CROSS-TREE`; never = the other six.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric A/D (pinned transcription) | `agent_workflows/run_evidence.py` `validate_finding_table` ("a never-aborting code names abort classes", "is not one of spec 4.1's six abort classes"); `RUN-BASELINE-OWNERSHIP` `action="ABORT RUN"`, `abort_classes=("Ownership or lease conflict",)`; spec 4.2 rows | E-05 changed only `ABORT_CLASSES` and the cells that NAME removed classes. Five aborting rows keep `abort_classes` naming removed classes, so the shipped table would fail `RC-ABORT-CLASS` at runtime; `RUN-BASELINE-OWNERSHIP` "ABORT RUN" names no class in text and would have been missed; `RUN-SCOPE-DELTA` and `RUN-HOST-ATTEMPT` (timeout) still say FAIL ITEM for group (a) classes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-06/V-06 rewrites every 4.2 action cell (and contrary messages) to a stated vocabulary mapping; E-05 now moves `action`, `abort`, `abort_classes`, `message` together and requires `validate_finding_table().ok`. Added F-06. |
| PR-002 | HIGH | UNDER-SCOPE | Rubric G (spec sync); P8 | Spec 1.4 A1 "restricted to six explicitly enumerated"; 2.1 "one of the six `ABORT RUN` classes"; 2.10 "maps to the allowed run-wide identity/type ambiguity class"; 4.1 ABORT RUN definition; 4.1 containment step 6; 5.2 row 1; 5.3 step 9; 5.4 step 1; 5.6 exit row 4 | Amending only 4.1/5.5/5.7 leaves at least nine sentences restating the old set, so the spec would contradict itself. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-07/V-07: sweep with a re-derived grep and dispose of every hit; E-03 now also covers the 4.1 definition, reclassification sentence and containment step 6. Added F-07. |
| PR-003 | HIGH | IN-SCOPE | Rubric D (anti-regression; spec/code agreement) | `runner_shared.assert_child_tool_identity` "ABORTING RUN: nested `aw` tool-identity mismatch"; `oc_runipd.run_queue` `except ToolIdentityError: ... raise`; executed plan `af7i6p` OQ-02 (run-fatal, citing spec 1.4/A1) | Shipped code aborts a run on a nested-tool identity mismatch, which is not a corrupt ledger. The plan's one-member abort set would make the spec contradict shipped, deliberately chosen behavior, or silently demand a code change no child owns. Choosing is a policy decision for the maintainer. | C:Low; U:Medium; S:Medium-High; F:Medium-High; Overall:Medium-High | OPEN | Escalated as OQ-02 (`Blocking: yes`, `Finding: PR-003`) with options and a recommendation (keep it as a second abort class). Added F-08. |
| PR-004 | HIGH | IN-SCOPE | Rubric G (Scope-Paths) | `tests/test_host_capability_extension.py` `test_row_1_push_denial_enforcement_status` ("'Push attempt' is intentionally retained in ABORT_CLASSES"); `tests/test_retry_class_mapping.py` (tests `TURN_RETRY_CLASSIFICATION` only); `ytas91` Scope-Paths | E-05 would break a test outside Scope-Paths; meanwhile a declared test file pins no spec text and is owned by Order 04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope-Paths: added `tests/test_host_capability_extension.py`, removed `tests/test_retry_class_mapping.py`; E-05 names the inverted assertion. Added F-09. |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric A (classification completeness) | Spec 5.5 never-retry list "unknown commit or transaction outcome"; "changed frozen requirements, EXCEPT an additive scope widening"; 5.5a | E-01's three groups dropped two current never-retry classes, so they became unclassified, and the 5.5a carve-out lost its anchor. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both added to group (b), 5.5a carve-out kept; E-02 requires one table row per member. |
| PR-006 | MEDIUM | IN-SCOPE | Rubric A (internal consistency) | Spec 5.5 "An out-of-scope mutation therefore fails and contains the item on the first occurrence"; Set-level refusal paragraph quoting "failed deterministic check for which a bounded correction is safe" | Prose around the lists would contradict the new groups or quote a class name that no longer exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 "RECONCILE THE PROSE" clause; V-01 pastes both. |
| PR-007 | MEDIUM | IN-SCOPE | Rubric E (test retargeting) | `tests/test_run_finding_abort_partition.py` `test_validate_finding_table_catches_perturbed_abort` (`assertEqual(target_row.abort, ABORT_CONDITIONAL)` on `RUN-FROZEN-IDENTITY`), `test_spec_comparison_catches_adversarial_co_moved_drift` (`RUN-CROSS-TREE`) | After the amendment no row is conditional, so these tests fail on their precondition; "update only where they enumerate the old set" did not cover them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 says to retarget to a perturbation that proves the same property (e.g. `RUN-LEDGER-INTEGRITY` always -> never). |
| PR-008 | MEDIUM | UNDER-SCOPE | Rubric E/G (evidence strength) | Original V-01..V-05 | V-items accepted pasted prose only; nothing demanded the validator verdict, per-row abort state, or the retry-budget anchor test, and the bare-suite demand had no before/after comparison. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 adds `test_retry_budget_citation`; V-05 adds the validator one-liner and before/after failing node IDs; new V-06/V-07 derive abort state from the spec file and dispose of every grep hit. |
| PR-009 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Original "Approval and execution gate" (one sentence) | Gate lacked resolved-questions precondition, scope-fence-as-declaration, staged-set verification, and conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Execution contract added. |
| PR-010 | LOW | IN-SCOPE | Honesty (push row) | Spec 5.2 row 1 "no mechanism detects or aborts on one"; lxb1ew deferral to `oq05nc` | Group (a) lists "a push (recorded, the agent is told)" as if a mechanism existed; nothing detects a push. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 requires the bullet to state detection is unbuilt; E-02 marks the row "unbuilt" with carrier `oq05nc`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which 4.1 action does each amended group map to in 4.2 cells? | (a) RETRY then FAIL ITEM; (b) FAIL ITEM; (c) ABORT RUN | Inventing new action tokens (e.g. "STOP ITEM") | Spec 4.1 "Failure actions mean" already defines RETRY/FAIL ITEM/ABORT RUN; `run_evidence.derive_abort_from_action` keys on "ABORT RUN" only, so reusing the vocabulary keeps the derivation valid | yes |
| D-2 | Is the dependency-preflight "run ABORTED (identity/type ambiguity is fatal)" a run abort under the new policy? | No: it is a REFUSE RUN before any session, and E-07 restates spec 2.10/5.4 that way | Keep it as an abort class; route it to stop-item | `runner_shared.enforce_dependency_preflight` raises from `initialize_run_core` before dispatch; 4.2 `RUN-STRUCTURE-PREFLIGHT` already uses "REFUSE RUN at freeze before any session" | yes |
| D-3 | Should `tests/test_retry_class_mapping.py` stay in Scope-Paths? | Removed | Keep it declared | It asserts no spec text (`test_predicate_agrees_with_table`) and `ytas91` declares it | yes |
