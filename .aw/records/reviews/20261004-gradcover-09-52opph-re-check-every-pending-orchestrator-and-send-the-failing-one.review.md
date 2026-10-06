# Review findings: plan 52opph

- Subject-Id: 52opph
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in lane `review-sweep-run-20261006T040814Z-944` at HEAD `07d8024a6`. The plan was committed and byte-identical
to the sealed lane input (rev-10); no snapshot needed. `- Kind: child`. `aw ipd lint --phase author` clean before;
`review-finalize` clean after.

Re-measured: the pending orchestrator population via `ipd_lint.parse` (17, including this Set's `1f4faf`); each Set via
`runner_shared.read_set_membership`, `find_unauthored_child_rows` and `ipd_lint.orchestrator_row_conformance`; every
source backlog item's status and gate; `attention_contract.BACKLOG_TRANSITIONS` and `SPEC_TRANSITIONS`; `qs00nc` E-03
(`aw ipd coverage` commits by default, `--no-commit` only), E-04/E-06 (`IPD-S408`, `check.orchestrator-not-review-ready`);
`8mabmu` E-07 (could-not-ask writes nothing, dirty plan skipped); `26m1nb` E-05 (backward edges, `--message`, Readiness strip,
`APPROVAL WITHDRAWN`); hm1h3l 2.5d condition 2 text.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G executability | `qs00nc` E-03 and round-2 PR-009 (`--commit` replaced by default-commit plus `--no-commit`) | E-01 passes `--commit`, which `aw ipd coverage` will not accept; the sweep's first command would fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Command corrected; `--no-commit` forbidden here. |
| PR-002 | HIGH | IN-SCOPE | A correctness | `8mabmu` E-07 (could-not-ask/unknown write nothing; dirty plan skipped); `hm1h3l` 2.5d UNAVAILABILITY | A host outage or unusable answer reads as "not ready" under the plan's binary rule and would demote approved Sets for no reason. | Overall:Low | FIXED | Three-way result; unmeasured is retried once and never demoted. |
| PR-003 | HIGH | IN-SCOPE | A correctness | `read_set_membership('denypush')` includes `d5ntkj` (`not-executed/`), not in `l4vw9o`'s table; `set_retirement_terminal_statuses` | "Every child that is not `executed`" includes terminal `not-executed`/`superseded` children, which the setter refuses and which are not unfinished work; a finding about a non-table child would withdraw an approval on a reason 2.5d does not give. | Overall:Low | FIXED | Only `pending/` children are set; a finding naming a non-table or terminal child stops for the maintainer. |
| PR-004 | MEDIUM | UNDER-SCOPE | C operability | three approved orchestrators may be queued by an active run | Demoting a plan held by a live run strands its lane. | Overall:Low | FIXED | `aw runs --active --agent` check before each Set; held Sets skipped and reported. |
| PR-005 | MEDIUM | IN-SCOPE | G execution contract | `aw backlog set open` moves the file between `backlog/graduated/` and `backlog/open/`; AGENTS.md commit rules | Commit discipline unspecified: setter `--no-commit`/`--yes`, both paths of a move, per-Set commits, staged-set verification. | Overall:Low | FIXED | Stated in E-02/E-03; V-02 and Required tests show renames and terminal dirs untouched. |
| PR-006 | MEDIUM | IN-SCOPE | F stakeholder | `95jk4s` 4 executed + 1 approved; `l4vw9o`; `9wzlou` | Partly executed Sets lose remaining approvals; the report named only orchestrators and could not be disputed without verbatim quotes. | Overall:Low | FIXED | Report lists every withdrawn approval (orchestrator and child), the executed/demoted split, and verbatim quotes. |
| PR-007 | LOW | IN-SCOPE | evidence | population 17 (incl. `1f4faf`); `9wzlou` also from `25kzda`; `wy9aru` is `to-review` | F-01/F-03 stale; spec-rollback legality asserted as unknown though measurable. | Overall:Low | FIXED | Re-measured facts appended as context; `SPEC_TRANSITIONS['implementing']` contains `approved`. |
| PR-008 | LOW | IN-SCOPE | G execution contract | gate section; Scope sentence | Gate lacked dependency stop, scope fence, paste-actual-output, finalize form; Scope had a garbled sentence and Proposed change 2 said `to-review`/`reviewed` only. | Overall:Low | FIXED | Rewritten. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is a could-not-ask / unusable probe answer a demotion trigger? | No; unmeasured, retried once, reported | treat as fail (demotes on outages) | `hm1h3l` 2.5d UNAVAILABILITY; `8mabmu` E-07 | yes |
| D-2 | What happens to terminal-directory Set members? | Never set; a finding naming one, or a non-table child, stops for the maintainer | demote them (setter refuses; withdraws approvals on a non-contract reason) | 2.5d condition 2 judges table children; `d5ntkj` measurement | yes |
| D-3 | Demote a Set held by an active run? | Skip and report | demote anyway | AGENTS.md runner contract; lane stranding | yes |
