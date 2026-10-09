# Review findings: spec wy9aru

- Subject-Id: wy9aru
- Subject-Type: spec
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5b449d000` in an interactive session. Structural preflight `aw specs check` CONFORMED
(exit 0) before semantic review and after revisions. The spec was committed and unchanged, so no
pre-review snapshot was needed. `aw ipd lint` was never invoked against the spec; no `- Readiness:` was
added; status and history were left to `aw specs set` / `aw specs note`.

RE-MEASURED by driving the real CLI in a scratch git repository (`aw specs set` both spellings, fixture
reset between runs): positional and `--status` `specs set implemented` without `--evidence` BOTH refuse,
file unchanged; positional and `--status` `specs set deferred --gate-kind bogus-kind` BOTH refuse,
nothing written; `aw prompts set` is registered; a positional specs selector matching two specs refuses
with `ambiguous ... pass --force`. By source: `cli.main` still forks `aw backlog set` / `aw specs set` on
`getattr(args, "status", None) is None` (`agent_workflows/cli.py`, the `backlog_cmd == "set"` and
`specs_cmd == "set"` branches) to `status_set.run_set_command` versus `backlog.run_set` / `specs.run_set`;
`backlog.run_set` still relocates by `atomic_write` + `src.unlink()` (`agent_workflows/backlog.py`, the
`moving` block); `specs.run_set` now calls `status_set.inherit_from_backlog_release_gate(...,
verb_label="aw specs set")`; backlog history stamps `core.utc_history_date()`. Every cited artifact's
status was re-read with `aw find`: `h4fiwa` done, `fv4b6s` graduated, `68sur3` done, `2wae2x`/`fnb8pl`/
`lq2w86` done, `jbipfa`/`ulepef`/`nvsz19` executed, `r74211`/`t1gbwg`/`19lmbe`/`mbjuv5`/`4ynlcg` done.
`aw record-history` exists and reads `.aw/records/history.jsonl` (341 lines in this checkout).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-001 | MEDIUM | IN-SCOPE | A (claims current) | spec Section 1 items 4-5, Section 2 E-1..E-6; plans `wdyz5n`, `ju3rhs`, `c6f6sj`, `7z3ovv`, `5ivkdh` executed | The motivating evidence is STALE: E-1, E-2 and E-3 no longer reproduce, E-4's clock divergence is fixed, and E-5/E-6 are already deduplicated. A reader would believe two live gate bypasses exist. The thesis (the entry-point fork) still holds, measured. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section 1 records items 4-5 as fixed by `setdispgate`; new row E-1r records the re-measurement and that the fork itself is unchanged; 4.7 table rows updated. |
| SR-002 | MEDIUM | IN-SCOPE | A, G | spec Sections 4.3, 4.6, 6, 7; `aw find` statuses | Sequencing prerequisites and Section 7 owners carry stale statuses (`jbipfa` "reviewed", `ulepef` "to-review", `nvsz19` "approved", eight backlog owners "open"); all have since executed or closed. A planner would wait on finished work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Statuses updated in 4.3, 4.6, 6 (with a note that the order constraint is met) and every Section 7 row. |
| SR-003 | HIGH | UNDER-SCOPE | E | spec OQ-1 (`Blocking: yes`, no `Status:`); plan `m94eht` E-03 "CANNOT BE PERFORMED UNTIL THAT ANSWER EXISTS" | OQ-1 blocked approval and an approved child plan, with no recorded answer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Asked the maintainer: KEEP, type-conditional. Recorded in OQ-1 and 4.3. |
| SR-004 | MEDIUM | UNDER-SCOPE | E, D | spec OQ-2 "Proceeding on that reading unless the maintainer objects" | A widening of an approval-gated verb's accepted selectors was left to silent default. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Asked the maintainer: WIDEN. Recorded in OQ-2 and 4.5 with the measured ambiguity refusal and the `--by-human` floor. |
| SR-005 | MEDIUM | UNDER-SCOPE | C | spec 3b AC-1..AC-6 vs 4.3, 4.5 | Two ruled behaviors had no acceptance criterion: the type-conditional sidecar (4.3) and the selector widening with its ambiguity refusal (4.5). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added AC-7 (sidecar on backlog/specs via either spelling, none on plans, after the durable write) and AC-8 (selector vocabulary, ambiguity refusal without `--force`, `--by-human` on every match). |
| SR-006 | LOW | IN-SCOPE | G | spec has no link to its graduated Set; `setdisp` plans carry `- From-Spec: wy9aru` | The spec does not name the plan Set already graduated from it, or the direction of dependency. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added 6a naming Set `setdisp` Orders 00-06 with statuses and direction. |
| SR-007 | LOW | IN-SCOPE | B | spec 3 C5 (SHOULD) without AC | C5 has no acceptance criterion; justified in 3c but not at the criterion. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | C5 now states "no acceptance criterion by design, see 3c". |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Does the spec's thesis survive now that its two headline bypasses are fixed? | Yes; keep the spec, record the fixes as history. | Retire the spec as overtaken, rejected: the entry-point fork is measured unchanged, and five recurrences of one class is the reason, not any single instance. | `cli.main` set-fork branches; `backlog.run_set` relocation block | yes - spec is pre-approval |

### Verdict

`APPROVE WITH REVISIONS APPLIED`. Seven findings, all FIXED: two stale-evidence findings repaired, the
blocking OQ-1 and non-blocking OQ-2 answered interactively by the maintainer, two acceptance criteria
added for ruled behaviors, and the graduated Set linked. No finding remains open at or above the gate
threshold. Ready for the human approval gate.
