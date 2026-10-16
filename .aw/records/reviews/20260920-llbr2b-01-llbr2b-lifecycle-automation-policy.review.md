# Review findings: spec llbr2b

- Subject-Id: llbr2b
- Subject-Type: spec
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `ad9213cc6` in a non-interactive review-sweep lane (no human channel). Structural
preflight `aw specs check` CONFORMED before semantic review and after revisions. The spec was committed
and unchanged, so no pre-review snapshot was needed. `aw ipd lint` was never invoked against the spec; no
`- Readiness:` was added; status and history were left to `aw specs set` / `aw specs note`.

RE-MEASURED at `ad9213cc6`: `attention_contract.SPEC_TRANSITIONS`, `BACKLOG_TRANSITIONS` and
`TRANSITION_AUTHORITY` (keys `->reviewed`, `->approved`, `->implementing`, `->implemented`,
`->deferred`); `ipd_schema.APPROVAL_STATUSES` / `READY_TO_EXECUTE` and the `Approval` iff `approved`
check; `ipd_lifecycle._LEGAL_BACKWARD_EDGES`; `runner_shared.set_plan_approved` (one definition, host
wrappers bind `HostLabels`); host `FULL_AUTO_ACTOR` reading `<HOST>_HOST_LABELS.full_auto_actor`;
`runner_shared.FULL_AUTO_APPROVAL_MESSAGE`; `oc_runipd.finalize_orchestrator` (zero callers, actor
`aw oc run step=orchestrator-rollup`); `run_selection_policy` draft verdict `WAIVES = ("draft-admission",)`;
`status_set` folding `--allow-open-questions` into the actor; every `pinned_module_argv(` and
`argv_builder(` site in `runner_shared.py`; `ipd_lifecycle` single non-`status_set` caller of
`apply_status_change`; the five `Constrained-by` spec paths (all resolve); commit `0f0eb2b4` exists.
Symbols cited in 3.1-3.8 all still resolve; most line numbers have moved (files grew by tens of
thousands of lines), batched as SR-006.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-001 | HIGH | UNDER-SCOPE | A, F (inventory exhaustiveness) | `agent_workflows/runner_shared.py` `execute_item_core` (`"--status", "implementing"`, `"--status", "graduated"`, rollback `"--status", "open"`); `runner_shared.handle_review_orchestrator_readiness` (`"ipd", "set", "to-review"`); commits `d4dbf0f9a`, `716548ded` post-date `2c316ef0` | The inventory, which the spec itself calls a SAFETY property because an unlisted pair is PERMITTED under 5.2, omits four automated lifecycle-status writes that landed after `2c316ef0`: `spec:approved->implementing`, `backlog:open->graduated`, `backlog:graduated->open` rollback, and `ipd:reviewed->to-review` orchestrator demotion. An implementing Set built from 3.1-3.8 would leave them ungoverned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Section 3.10 listing them (plus the `0owirm` close as A-5) by symbol; 3.9's snapshot limit now records the measured drift; new criterion 14 requires the implementing Set to re-run the searches at its own HEAD and paste the output. |
| SR-002 | HIGH | IN-SCOPE | A, G | `runner_shared.set_plan_approved`; `oc_runipd.set_plan_approved` / `agy_runipd.set_plan_approved` wrappers; `runner_shared.HostLabels.full_auto_actor` comment ("deleted in `gjni4c`"); backlog `zf999x` done | 3.8 D-1 and D-2 describe as LIVE two divergences that have since been fixed (performer consolidated by `li44r9`; third constant deleted by `gjni4c`), and 3.1's "Performed by" names two copies. 7.3's argument rests on these as current evidence, so a planner would schedule already-done work and misread the motivation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 3.1 row and a dated "status at `ad9213cc6`" block under 3.8 record D-1/D-2 resolved and D-3 unchanged; the original table is kept as history. 7.3's requirement is unchanged (it still holds as a general rule). |
| SR-003 | HIGH | IN-SCOPE | B, D (contract-closed set) | `attention_contract.SPEC_TRANSITIONS["deferred"]` includes `approved`; `ipd_lifecycle._LEGAL_BACKWARD_EDGES`; `TRANSITION_AUTHORITY` keyed `->approved` / `->implemented` | 6.4 named only `reviewed->approved` and `implementing->implemented`, but 5.1 makes every unlisted pair PERMITTED, so `spec:deferred->approved` (a legal edge) would have been an automation-permitted route to human `approved`, contradicting 6.4's own rationale and 5.4. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 6.4 rows re-keyed on the target with a wildcard source (`ipd:*->approved`, `spec:*->approved`, `spec:*->implemented`), with a paragraph stating why and that it matches today's `TRANSITION_AUTHORITY` shape. This sharpens 6.4's stated intent; it does not change what the spec decides. |
| SR-004 | MEDIUM | UNDER-SCOPE | E | `runner_shared.perform_coordinator_proposal_file` (`"ipd", "scaffold"`, `"backlog", "new"`) | Automated artifact CREATION is neither inventoried nor excluded; whether it is on the policy surface is a scope decision the spec does not make. | C:Low; U:Low; S:Low; F:Low; Overall:Low | OPEN | Raised as OQ-06 in new Section 5.7 (owner maintainer, not blocking, recommendation: out of scope) and explicitly excluded from 3.10 pending the ruling. Below the `high` gate threshold. |
| SR-005 | MEDIUM | UNDER-SCOPE | C | spec 7.2, 6.5; Section 9 criteria 1-11 | Two MUSTs had no acceptance criterion: 7.2's per-verdict-path fail direction, and 6.5's requirement that the SHIPPED DEFAULT closes every 6.4 pair (criterion 6 covers only override refusal, which 6.5 itself says is insufficient). Open questions OQ-03/OQ-05 also had no in-spec disposition block (owner, blocking, closing evidence). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added criteria 12 and 13; added Section 5.7 dispositioning OQ-03, OQ-05, OQ-06. |
| SR-006 | LOW | IN-SCOPE | A (citations) | e.g. spec cites `oc_runipd.py:875` for `set_plan_approved`, now `:1088`; `attention_contract.py:486` for `TRANSITION_AUTHORITY`, now `:581`; `ipd_schema.py:267` for `READY_TO_EXECUTE`, now `:384` | Most `path:line` hints in 3.1-3.8 have drifted; every cited symbol still resolves. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a CITATION CONVENTION paragraph to Section 3 making the symbol authoritative and the line a hint at the measured HEAD; individual numbers left as historical measurements. |
| SR-007 | LOW | IN-SCOPE | A, G | `tests/test_runner_item_dependencies.py` and `tests/test_lane_tool_identity.py` absent (deleted in `19313eed`); spec 3.9 / 5.2 cross-references "Section 8, criterion" while criteria are in Section 9 | 7.4 relied on a deleted test as the import-discipline guard; 3.6 relied on a deleted test as the reason `finalize_orchestrator` is retained; two cross-references pointed at the wrong section. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 7.4 and 3.6 now state the tests are gone and what the implementing Set must ship instead; cross-references corrected to Section 9; 5.6 no longer asserts the spec "is at to-review" (stale after this transition). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Is re-keying 6.4 with a wildcard source a design change requiring the maintainer? | No; it is a sharpening of the stated intent. | Raise as an OQ, rejected: 6.4's own rationale ("asserts a human approved something no human approved") is source-independent, and `TRANSITION_AUTHORITY` already enforces `->approved` regardless of source. | `attention_contract.TRANSITION_AUTHORITY`; spec 5.4 ruling | yes - spec is pre-approval |
| D-2 | Rewrite the stale 3.8 table in place or annotate? | Annotate with a dated status block; keep the measured table as history. | Rewrite, rejected: it would erase the evidence 7.3's requirement was derived from. | spec 3.8; plan `li44r9`, `gjni4c` executed | yes |
| D-3 | Should artifact creation be added to the inventory? | No; raise as OQ-06 with an out-of-scope recommendation. | Add to 3.10, rejected: deciding scope is the maintainer's. | spec 5.5 scope-only pattern | yes |

### Verdict

`REVIEWED - OPEN QUESTIONS`. Seven findings: six FIXED in place, one MEDIUM (SR-004) left OPEN as OQ-06,
below the `high` gate threshold, so this record arms NO gating finding. The spec still carries two
unattested design answers (OQ-03, OQ-05) and the new OQ-06; each has a recommendation that the
maintainer's `--by-human` approval would adopt. Ready for the human approval gate on that basis.
