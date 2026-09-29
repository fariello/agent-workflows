- Id: oev4h7
- Status: open
- Set: oev4h7
- Priority: low
- Work-Kind: followup
- Summary: aw group/rename plans write an orchestrator to a nonzero Order, the IPD-M104 mirror of r30nnz

## Workflow history
- 2026-09-29 created (aw backlog): aw group/rename plans write an orchestrator to a nonzero Order, the IPD-M104 mirror of r30nnz

MEASURED AT HEAD 62871f64 while authoring plan qhcojn (from backlog r30nnz), in a throwaway git repo driving the real CLI with PYTHONPATH pinned to the lane under test (ccbe60: a bare -m agent_workflows from a lane imports the MAIN checkout, so an unpinned measurement tests the wrong source).

THE MEASUREMENT. A seeded '- Kind: orchestrator' plan at Order 0 was moved with an explicit nonzero order:

    aw group plans hhh888 --set orchset --order 5 --rename --apply

It exited 0 with no warning, renamed 20260920-probeset-00-hhh888-orch.ipd.md to 20260920-orchset-05-hhh888-orch.ipd.md, and wrote '- Order: 5' into the front matter. 'aw ipd lint' on the result then exits 1 with:

    ! IPD-M104: Order: orchestrator Order must be 0

THIS IS THE EXACT MIRROR OF r30nnz. ipd_schema.validate_metadata carries BOTH halves of one kind-conditional rule: MetaError('Order', 'child Order must be an integer >= 1') and MetaError('Order', 'orchestrator Order must be 0'). r30nnz asks whether the write site should consult the first half; this item is the second half, in the same two verbs (plans_refs.plan_set_assign for 'aw group plans', plans_refs.run_mv for 'aw rename plans'), reached from the other side. 'aw ipd scaffold' already refuses BOTH halves (ipd_authoring.run_scaffold prints 'error: orchestrator Order must be 0' and returns 2), so the same repository disagrees with itself here too.

WHY IT WAS NOT BUILT IN qhcojn, recorded as that plan's OQ-01. The backlog item qhcojn graduates from decided exactly one question and its acceptance criteria are explicit that an orchestrator at 0 must be 'permitted unconditionally'; they say nothing about policing an orchestrator elsewhere. Adding an unasked second rule to a low-priority followup is how a narrow plan becomes unreviewable, so the measurement was filed rather than absorbed.

IF BUILT, it is likely one more clause in whatever predicate qhcojn lands, so this item should be read AFTER that plan executes: the cheap version is a second branch beside the child check at both write sites, and it inherits qhcojn's two hard constraints. FIRST, evaluate each plan's RESOLVED order, never the flag: 'aw group plans <orch> <child> <child> --set X --order 0' with the orchestrator named first is legitimate and works today (measured: -00-/-01-/-02-, exit 0), because plan_set_assign computes order = start_order + i per named plan. SECOND, require '- Kind: orchestrator' to be PRESENT: validate_metadata reads kind = fields.get('Kind') with no default, and 102 of 950 plans in this tree carry no '- Kind:' line at all (100 executed/, 2 not-executed/), so a Kind-less plan gets neither Order error and must not be refused.

SEVERITY, stated plainly. This is a followup and not a bug: no user waits on it, nothing produces a wrong answer, and the accidental path is narrow because an operator must type an explicit nonzero --order at an orchestrator. What makes it worth recording is that 'aw check' does NOT gate on the result - measured on the child case, the sweep reports check.ipd-lint-diagnostic carrying the IPD-M104 detail at 'severity: info' while printing CONFORMS and exiting 0 - so nothing stops the invalid state after a successful regroup except a per-file verb an operator has no reason to run.
