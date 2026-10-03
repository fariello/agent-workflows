# Review findings: plan jdaozp

- Subject-Id: jdaozp
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `a30553683`. The plan was committed and byte-identical to the lane input, so no pre-review
snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review, and
`--phase review-finalize` was clean after revision.

Re-verified (scratch probes under `/tmp`, no production edit):
- `validate_gate_ref('artifact','nosuchfile')` and `validate_gate_ref('todo','zzzzzz')` both True.
- Live gates: `adgtqb` (blocked) `artifact`/`yvvf98` -> `('plans','executed')` -> `done`; the two deferred specs
  `todo`/`ju93oc` and `todo`/`m15n3k` -> `('backlog','parked')` -> `parked`. Index: 2337 id6, 0 ambiguous,
  about 0.57s per build.
- `class_of` raises over the index population for `('plans',None)` 24, `('walkthroughs',None)` 12,
  `('research',None)` 7, `('plans','EXECUTED')` 1, two roadmaps statuses (drifted from the plan's 81-record census;
  the plan already demands re-measurement).
- `validate_gate_ref('todo','../../etc/passwd')` True; `validate_gate_ref('artifact','../x')` False; a bare
  `(root/ref).exists()` on the former is True from a tmp root.
- `validate_gate_ref('todo','T-12')` and `('todo','TODO-42')` True.
- `build_dependency_index` on an empty tmp tree: 0 owners; on a tmp tree holding one blocked backlog item: that item
  is indexed (with and without `git init`). Its body swallows every inventory exception into an empty index.
- `backlog.gate-unexpected` and the spec "gate fields present on a non-deferred spec" finding exist.
- `check.decision-ref-dangling` is registered `warning`; `check.from-backlog-dangling` is `error`.
- `RELEASE_GATE_RULES` parity test exists at `tests/test_check_engine_release_gate.py`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | B. Security (path traversal) | `agent_workflows/attention_contract.py:600` `_TODO_ID_RE` admits `..`; E-01 "FIRST probe the ref as a repo-relative path" | The prescribed path probe would resolve a `todo` ref such as `../../etc/passwd` outside the repository, silently reporting a pointer to a host file as a resolved gate (and treating file existence outside the repo as evidence). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 guard (a) contains the path route to the resolved repo root; E-05 case (14) and V-01 pin it; F-14 records the measurement. |
| PR-002 | HIGH | IN-SCOPE | E. Testing (contradictory acceptance) | E-05 case (12) vs case (3); `check_engine.build_dependency_index` | Case (12) required "a tree carrying gates but no records" to yield no finding, but the carrier is itself inventoried, and case (3) requires exactly that shape to emit an `error`. The two cases could not both pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (12) redefined as the cannot-judge case (foreign TODO-id namespace, empty index); E-06 portability wording and V-03/V-05 and Required tests swept. |
| PR-003 | HIGH | IN-SCOPE | A/C. Fail-open turned fail-loud | `check_engine.build_dependency_index` (`except Exception: return _DepIndex(owners)`); `_TODO_ID_RE` accepts `T-12` | Without a third verdict, an inventory failure would make every id6 gate an `error`, and a managed repo using its own TODO ids would get a permanent `error` per gate it cannot fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 guards (b) and (c) add an `unknown` verdict; E-02 reports only `unresolved`; F-15 records it. |
| PR-004 | MEDIUM | IN-SCOPE | D. No double report | `backlog.py` `backlog.gate-unexpected`; `specs.py` "gate fields present on a non-deferred spec" | The sweeps would also judge gate refs on non-blocked items and non-deferred specs, which are already findings. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02/E-03 restrict to live carriers; E-05 case (15); F-16. |
| PR-005 | MEDIUM | IN-SCOPE | G. Live-artifact bar | V-03 "EXACTLY THREE"; Required tests "zero ... and three ... on the three records"; F-12 "92" | The validation bars pinned live-corpus counts other lanes can move (the `class_of` raise census had already drifted at review). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bars rewritten as set equality between findings and an independent execution-time census, comparing `(rule, location)` sets; authoring numbers kept as context. |
| PR-006 | LOW | IN-SCOPE | C. Severity consistency | `check_engine.RULE_REGISTRY` `check.decision-ref-dangling` (`warning`) | A dangling `decision` gate stays `warning` while a dangling `artifact`/`todo` gate becomes `error`, and the plan did not acknowledge the asymmetry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires a registry comment stating why; V-02 demands it pasted. Decision rule tier unchanged. |
| PR-007 | MEDIUM | IN-SCOPE | G. Execution contract | Approval gate paragraph and E-07 "report it and stop" | The gate lacked a scope-fence declaration and conditional runner/executor finalize ownership, and two clauses told the executor to STOP over a non-unsafe condition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with the declaration-style fence, the unsafe-only stop, conditional finalize ownership, and no-tag; E-07's stop replaced with report-and-continue. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should a non-id6 `todo` ref be judged? | `unknown`, no finding. | Report it dangling; resolve against `TODO.md`. | Spec Section 8.4 "a TODO id"; `TODO.md` carries no TODO-id namespace (plan F-10); managed-repo portability (`jge900` PR-001). | yes |
| D-2 | What does an empty index mean? | `unknown` (inventory failed), no finding. | Treat as all-dangling. | `build_dependency_index` swallow; carrier is itself inventoried, so a working inventory is never empty when a gate exists. | yes |
| D-3 | Should a path ref escaping the root resolve? | No; containment required. | Accept any existing path. | `_ARTIFACT_REF_RE` already forbids `..` for `artifact`, so containment matches the declared intent. | yes |
| D-4 | Judge gates on non-live carriers? | No. | Judge every gate field. | Existing `backlog.gate-unexpected` / spec non-deferred finding. | yes |
