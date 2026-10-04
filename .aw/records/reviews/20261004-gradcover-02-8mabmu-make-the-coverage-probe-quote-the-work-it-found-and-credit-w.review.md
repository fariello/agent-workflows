# Review findings: plan 8mabmu

- Subject-Id: 8mabmu
- Subject-Type: ipd
- Reviewed-At: 2026-10-04
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261004T134544Z-4052083` at HEAD `d22fb2375`. The plan was
byte-identical to the sealed lane input (rev-3); no snapshot needed. `- Kind: child`. `aw ipd lint --phase author`
clean before; `review-finalize` clean after.

Re-measured in `agent_workflows/runner_shared.py`: `PROBE_SENTINEL_EXECUTIONS`/`_NO_EXECUTIONS`; `PROBE_PROMPT_TEMPLATE`
("Reply with EXACTLY ONE of these two lines and NOTHING else", "any doubt resolves to CONTAINS EXECUTIONS");
`classify_probe_reply` equality tests; `ask_orchestrator_probe` returns `(answer, detail)`; `probe_orchestrator` calls
`ask(state, excerpt, ...)` and unpacks two values; `ProbeOutcome` fields; `PROBE_VERDICT_STORE_SCHEMA_VERSION = 1`;
`_read_probe_verdict_store` and `record_probe_verdict` bodies; `orchestrator_probe_excerpt` renders
`### Child IPDs table (row cells, in document order)`; `enforce_orchestrator_probe_gate` reason text and
`record_refusal` (in `render_stream`, redacts paths). Real `axozpe` excerpt rendered (10911 chars): its ownership
sentence reads "which Order 04 carries as the last child", with no id6.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A data integrity / caching | `runner_shared._read_probe_verdict_store` returns `raw.get("entries")` with no version check; `record_probe_verdict` does `entries = dict(_read_probe_verdict_store(repo_root))` then writes `"schema_version": PROBE_VERDICT_STORE_SCHEMA_VERSION` | E-03 assumes bumping the constant retires old entries. Nothing reads the version, and the first write after the bump would relabel every old quote-less verdict as current, so old `fail`s (13 of them) would be served with no quotes and old `pass`es produced by the old prompt would be trusted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires a version check on read (non-current store reads empty) and on write (start from empty), with a test that an old entry is still a miss after a new write; F-06 added; V-03 demands that evidence. |
| PR-002 | HIGH | IN-SCOPE | Goal reachability | `axozpe` `## Required tests / validation` "which Order 04 carries as the last child rather than this plan performing it"; `Scope check` "to Order 04"; its child table row `04 \| rlhmt9`; hm1h3l A.4 "names, by id6" | The motivating false refusal names its owner by ORDER NUMBER, not id6. An id6-only rule (E-01, and spec text A.4) would not credit it, so the Concern's central claim would remain unfixed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and hm1h3l A.4 now credit an id6 or an Order number present in the table; E-05 fixture uses an Order number only; OQ-03 records the decision; Concern corrected; 1f4faf note added. |
| PR-003 | MEDIUM | IN-SCOPE | Contract consistency | hm1h3l A.3 "A quote is valid only if its text occurs ... A 'contains executions' answer with no valid quote ... is UNUSABLE"; 8mabmu E-01/V-02 | E-02 was ambiguous on whether one invalid quote among valid ones voids the answer; the spec implies invalid quotes are dropped. Voiding would turn a mostly-right model answer into `unknown` with no quotes shown. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Invalid `QUOTE:` lines are discarded and counted (count shown in the refusal); a non-`QUOTE:` line still voids; at least one valid quote required. V-02 lists the partial case. |
| PR-004 | MEDIUM | IN-SCOPE | D anti-regression | `tests/test_orchestrator_shape_gate.py` `double_asker` returns `(rs.PROBE_ANSWER_EXECUTIONS, "...")` and asserts `"orchestrator coverage probe reports that prs001"`; same seam in `tests/test_orchestrator_shape_composed.py`; neither file is in Scope-Paths | Changing the asker return shape or the reason prefix would break shipped tests the plan may not edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires accepting the 2-tuple; E-04 keeps the reason's leading sentence and appends quotes; E-05 tests the 2-tuple double. |
| PR-005 | LOW | IN-SCOPE | Evidence | conventions bullet citing `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`; file absent (`ls` fails), removed by `19313eed7` | The cited pinning test no longer exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten as a convention with the removal commit cited. |
| PR-006 | LOW | IN-SCOPE | E/G | E-01; gate | The prompt should tell the model to copy quotes exactly, since excerpts carry backticks and pipes; the gate lacked the paste-actual-output rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Credit an Order number as well as an id6? | Yes, when the Order is in the orchestrator's table | id6 only (leaves `axozpe` refused); any prose mention of a child (too loose) | `axozpe` excerpt text; the table is sent to the probe (`orchestrator_probe_excerpt`) | yes |
| D-2 | Invalid quote among valid ones: void or discard? | Discard and count | void the whole answer | hm1h3l A.3 wording | yes |
| D-3 | Enforce the store version on read and write, or move to a new store filename? | Version check in both functions | rename `_PROBE_VERDICT_STORE_NAME` (leaves an orphan file) | both functions already own the store; one constant | yes |
