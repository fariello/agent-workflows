# Review findings: plan 8wfzb5

- Subject-Id: 8wfzb5
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `84d0b3798` (after the `hguae9` review commit). Plan committed and
byte-identical to the lane input, so no pre-review snapshot. Orchestrator (`- Kind: orchestrator`).
`aw ipd lint --phase author --agent`: `clean`. `aw ipd coverage 8wfzb5`: "ready for review" before and after
revisions (the edit changed the fingerprint; the re-check passed and rewrote `- Coverage-Fingerprint:`).
No `IPD-S407` / `IPD-S408` findings, so no repair loop was needed.

Re-verified: all five children exist in `pending/` at `to-review`, carry `- Set: testprune`, Orders 1..5, and
chain `executed:hguae9` -> `qqrgv3` -> `tv72xy` -> `83nnyn` -> `c8bfp9` -> `vgus66`, matching the child table.
The child-owned work: `qqrgv3` E-07 creates the decision table with an empty "Recorded deletions" table;
`tv72xy` E-08 appends deletions; `83nnyn` records consolidation rows; `c8bfp9` E-10 measures under-120s, and its
OQ-02 makes a recorded miss acceptable for maintainer decision; `vgus66` E-03 (core per-module), E-04..E-06
(mutation sample at least 20 plus every defect-citing test, restorations), E-07 (flakes), E-08 (final
measurements), E-09 (finalize table, final report, CHANGELOG).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G (accuracy vs child contract) | plan "Completion criteria" (pre-review) "median wall under 120s. Owner: c8bfp9"; `c8bfp9` OQ-02; `vgus66` E-08 "or the miss recorded" | The Set criterion stated a hard 120s bar while both owning children accept a recorded miss for maintainer decision. A reader of the orchestrator would believe the Set cannot complete without 120s, or that a miss is a failure. | all Low | FIXED | Criterion now states the bar OR the recorded miss, the no-weakening rule, and both owners. |
| PR-002 | MEDIUM | UNDER-SCOPE | G (traceability) | plan "Completion criteria" (pre-review); `tv72xy` Goal; `vgus66` E-07, E-09 | The whole-Set criteria omitted the Set's first stated goal (no structure-pin tests remain), the flake check, and the CHANGELOG/final report, and attributed deletion recording to `qqrgv3` alone though `tv72xy`/`83nnyn` append and `vgus66` finalizes. | all Low | FIXED | Added the pin, flake, and CHANGELOG/report criteria with owners; deletion-record criterion names every owner. |
| PR-003 | LOW | IN-SCOPE | D (baseline definition) | criterion "coverage does not drop" (pre-review); `qqrgv3` `Item-Dependencies: executed:hguae9` | "Does not drop" had no stated baseline; `hguae9` adds tests before `qqrgv3` measures, so the comparison point matters. | all Low | FIXED | Baseline named: `qqrgv3`'s measurement on post-`hguae9` main. |
| PR-004 | LOW | IN-SCOPE | G (execution contract) | plan gate (pre-review) | The gate lacked the by-hand path (perform E-01..E-05 in order, paste quoted child evidence, `aw ipd finalize`, path-scoped `aw commit`), the runner-retirement note, and the dependency hold on `hguae9`. | all Low | FIXED | Gate rewritten. |

`aw ipd lint --phase review-finalize`: `conforming` after the coverage re-check.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is a 120s miss a Set failure? | No: a recorded miss goes to the maintainer, as the children already say. | Hard bar (REJECTED: contradicts `c8bfp9` OQ-02, `Owner: maintainer`, and `vgus66` E-08). | `c8bfp9` OQ-02; `vgus66` E-08 expected outcome. | yes |
| D-2 | Which coverage baseline? | `qqrgv3`'s measurement on post-`hguae9` main. | Research `7ry5kv` / `offdhr` (REJECTED: pre-`hguae9`, and `offdhr` is lines-only per `qqrgv3` F-1). | `qqrgv3` Concern and `Item-Dependencies`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
