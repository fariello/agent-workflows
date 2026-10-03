- Id: pyhq6s
- Status: graduated
- Blocks-Release: next
- Set: setdispgate
- Priority: high
- Work-Kind: bug
- Summary: test_blast_radius_zero_across_pending_plans treats a legal non-plan Item-Dependencies edge as a stranded prerequisite

## Workflow history
- 2026-10-01 note (aw backlog): STATUS NOTE, so a later reader is not misled: the CODE FIX IS WRITTEN AND VALIDATED in this change, but the item is left graduated rather than done DELIBERATELY. aw backlog set done refused (correctly) because the item carries Blocks-Release: next and no satisfying evidence could be cited: resolve_evidence_artifact requires an in-tree .aw/records/ artifact, and the fix lives in tests/test_terminal_status_vocabulary.py, which is source. There is also no carrier plan to hand the gate to, because the fix was made inline while authoring the setdisp Set rather than planned. So the maintainer's choice is either to close it with --blocks-release - (the gate is genuinely satisfied: the defect is fixed and the suite is green) or to leave it graduated until a record cites it. Do NOT read graduated here as 'designed but unimplemented'.
- 2026-10-01 graduated (aw set): Fixed in the same change that exposed it: tests/test_terminal_status_vocabulary.py now parses each edge with ipd_schema.parse_item_dependencies and resolves a non-ipd target against its own records tree. Suite green (3512 passed, 2 skipped). Both probes demonstrated non-vacuous: a dangling ipd edge and a dangling spec edge each fail the test.
- 2026-10-01 created (aw backlog): Filed while authoring the fcnz1r dispatch-unification Set; the test FAILS on a legal edge, measured.

MEASURED 2026-10-01 at HEAD ec857565a. Authoring plan m94eht with the legal edge

  - Item-Dependencies: executed:m1jlwm, state:spec:approved:wy9aru

makes the suite go RED:

  FAILED tests/test_terminal_status_vocabulary.py::TestExecutionSuccessStatesNarrowingAndBlastRadius::test_blast_radius_zero_across_pending_plans
  AssertionError: pending plans must not reference stranded prerequisites: [('...m94eht...ipd.md', 'wy9aru')]

THE EDGE IS LEGAL AND THE TEST IS WRONG. Verified three ways rather than assumed:
1. ipd_schema.parse_item_dependencies accepts it: state:spec:approved:wy9aru parses to ItemDependency(kind='state', target_type='spec', status='approved', id6='wy9aru'), and ITEM_DEP_TYPES is ('ipd','spec','backlog').
2. runner_shared.preflight_dependency_findings reports NO findings for the plan (graph valid).
3. runner_shared.edge_satisfied RESOLVES the spec and enforces it:
     (False, "state:spec:approved:wy9aru: spec wy9aru is 'to-review', needs exactly 'approved'")
   So the edge is not merely tolerated, it is ENFORCED at dispatch.

ROOT CAUSE: the test globs ONLY the plans trees for every dependency id6:
    clean_id = dep_id.split(':')[-1]
    matching_exec = executed_dir.glob(f'*-{clean_id}-*.md'); matching_pending = pending_dir.glob(...)
    if not matching_exec and not matching_pending: stranded_prereqs.append(...)
Its comment says 'Strip any prefix like ipd:', showing it was written when only ipd-typed edges existed. A spec or backlog target is deliberately a graph LEAF resolved against the REPOSITORY, not the queue: validate_manifest states this explicitly ('Only IPD-typed targets must name a plan in the manifest; a spec/backlog target is a graph LEAF (spec 25kzda 2.10) and is resolved against the repository'). So the test asserts an invariant the design contradicts.

WHY IT MATTERS RATHER THAN BEING COSMETIC: it is a TRAP FOR THE NEXT AUTHOR. The failure names the authoring plan, not the test, so an author reading it concludes their own legal edge is malformed and 'fixes' it by weakening a real dependency gate. In this case the edge is the only thing preventing a plan from executing before a maintainer answers a BLOCKING spec question, so deleting it to make the suite green would silently remove a human decision gate. It also means NO plan in this repository can use the spec/backlog edge grammar without turning the suite red, i.e. a shipped grammar is untestable in practice.

SUGGESTED FIX: parse each token with ipd_schema.parse_item_dependencies instead of split(':')[-1], and resolve a non-ipd target against its own records tree (or skip it, since preflight_dependency_findings and aw check already validate those edges and would catch a genuinely dangling one). Do NOT just allowlist the id6. Note this test also only checks 'is it on disk somewhere', which the shared dependency evaluator already does better, so consider whether it should delegate rather than re-deriving.

RELATED: the runner's --with-dependencies closure separately REFUSES a non-plan target (closure_target_admission), a known gap narrower than approved spec 25kzda, already carried by approved plan yu47nf. That is a DIFFERENT defect (queue admission, not test correctness) and this item does not duplicate it: a bare run enforces the edge correctly today.
