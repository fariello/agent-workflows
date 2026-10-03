# Review findings: plan l1xkrr

- Subject-Id: l1xkrr
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `bef6b9756`. The plan file was committed and byte-identical to
the lane input (`cmp`), so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean with
zero findings before review; `--phase review-finalize` was clean after revision, with two info-level
`IPD-Z602` density advisories (E-05, E-06) judged single-concern on semantic reading (one test module; one
`aw specs note` invocation). `- Kind: child`, so `IPD-S407` does not apply.

MEASURED AT REVIEW, in process: `_ORCH_ROW_RE.pattern` is
`^- \[[ x]\] (E-[0-9]{2,}) CONFIRM ([0-9a-z]{6}) REACHED ([A-Za-z][A-Za-z-]*)$` and `ORCH_ROW_CANONICAL` is
`- [ ] E-NN CONFIRM <child-id6> REACHED <status>`; the six-token datum E-02 specifies reproduces both
(`pat eq True canon eq True`). `zojfn6` is now in `executed/`, and
`build_skeleton(kind="orchestrator", ...)` emits `- [ ] E-01 CONFIRM c0ch01 REACHED executed` from the
hand-written literal in `ipd_authoring._exec_placeholder_leaf`; the child-table placeholder separately
hand-writes `c0ch01`. `render_orchestrator_row_refusal` has one definition and two call sites, all in
`ipd_lint.py` (F-03 holds). `aw specs note --help`: "Append a workflow-history record to a spec WITHOUT
changing its status".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric E (test discriminates); D | plan E-05(2), V-05 | The sensitivity proof as written (perturb the datum, assert both derived outputs change) never looks at the shipped constants, so it stays GREEN if `ORCH_ROW_CANONICAL` is reverted to an independent literal, which is exactly the drift the plan exists to stop. V-05's "revert to literals" demonstration with equal values could not fail either | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split (2) into a binding limb (shipped constants equal the shipped derivation functions applied to the shipped datum) plus the perturbation limb; required the derivations to be pure callables over any datum (E-02/E-03); V-05 now demands a one-token-different literal revert failing limb (2a) |
| PR-002 | HIGH | IN-SCOPE | Spec sync; tool reachability | plan Spec / documentation sync, Proposed change 5; `aw specs note --help` | The plan instructed amending OQ-01's `Resolution or deferral rationale` and to do it "with `aw specs note` and nothing else"; that verb only appends a workflow-history record, so the instruction was unsatisfiable without a hand edit the plan also forbade. The spec edit also had no E/V pair | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Retargeted the annotation to one workflow-history record; added E-06/V-06; reconciled Proposed changes, Conventions and Scope check |
| PR-003 | MEDIUM | IN-SCOPE | Evidence currency | F-02; `ipd_authoring._exec_placeholder_leaf` `action_line = "- [ ] E-01 CONFIRM c0ch01 REACHED executed"`; `zojfn6` in `executed/` | F-02's "third copy does not exist yet" is now false; the landed branch of E-04 is live | all Low | FIXED | Appended a review re-measurement to F-02 and E-04; V-01 notes the expected branch while still demanding re-measurement |
| PR-004 | MEDIUM | UNDER-SCOPE | Rubric D (same decay mode one level down) | `ipd_authoring.py` child-table placeholder `` `c0ch01` `` and the row literal | Rendering the row from the datum still leaves the placeholder id6 hand-written twice, so the row and the table it must resolve against can drift | all Low | FIXED | E-04 now hoists the placeholder id6 to one module-private constant used by both; V-04 asks for proof it is written once |
| PR-005 | MEDIUM | UNDER-SCOPE | Execution contract (gate) | Approval and execution gate | The gate lacked a scope-fence declaration and the lifecycle transition with conditional runner/executor ownership | all Low | FIXED | Added SCOPE FENCE and LIFECYCLE paragraphs |
| PR-006 | LOW | IN-SCOPE | Workflow history format | history block | A stray blank line split the history list | all Low | FIXED | Removed |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the spec annotation go, given `aw specs note` cannot edit OQ-01's body? | A workflow-history record via `aw specs note`. | Hand-editing OQ-01's rationale: rejected, the plan itself forbids hand edits to an approved spec and OQ-01 is maintainer-owned. Dropping the spec annotation: rejected, the residue would then be unrecorded where readers of OQ-01 look | `aw specs note --help`; spec `r07vma` OQ-01 `- Owner: maintainer` | yes |
| D-2 | Should the placeholder id6 be single-sourced too, though the plan's goal names only the grammar? | Yes, in E-04. | Leave it: rejected, it is the identical drift between two hand-written copies inside the same edit | `ipd_authoring.py` two `c0ch01` literals | yes |

No `Reversible: no` decision. OQ-01 stays `open`, `Blocking: no`, maintainer-owned, and does not hold the
plan under the 2026-09-10 ruling. No finding is left `OPEN` or `DEFERRED`.
