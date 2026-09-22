- Id: htce8t
- Status: open
- Set: htce8t
- Priority: medium
- Work-Kind: chore
- Summary: aw ipd scaffold emits a non-conforming orchestrator checklist row, so the typed-row rule cannot gate aw ipd begin

## Workflow history
- 2026-09-22 created (aw backlog): aw ipd scaffold emits a non-conforming orchestrator checklist row, so the typed-row rule cannot gate aw ipd begin

Spec r07vma R1a defines the typed child-tracking row and plan dpdyed landed the rule (ipd_lint.orchestrator_row_conformance, IPD-S407). Measured 2026-09-22 while executing dpdyed: ipd_authoring.build_skeleton(kind='orchestrator', ...) emits the checklist row '- [ ] E-01 TODO one observable action.' and the prose placeholder 'TODO: child IPD table (Order | File | What it does | Depends on).' where the child table goes, so a FRESHLY SCAFFOLDED orchestrator does not conform to the rule the same toolkit now enforces.

CONSEQUENCE, which is why this is filed rather than merely noted. aw ipd begin gates on the pre-execution lint (ipd_lifecycle.begin -> lint_file(checkpoint='pre-execution')). dpdyed therefore had to EXCLUDE pre-execution from _ORCH_ROW_BLOCKING_CHECKPOINTS, because including it refused every freshly scaffolded orchestrator at begin: it broke tests/test_orchestrator_retirement.py::TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_an_orchestrator, whose fixture is built from the REAL scaffold. The rule still fires at review-finalize (where R5's repair loop lives) and at pre-transition, so nothing is ungated; the gap is that begin cannot be gated while the scaffold itself violates the rule.

REMEDY: teach build_skeleton to emit a conforming orchestrator skeleton (a typed row plus a child table carrying an Id column), which is also spec r07vma OQ-01's proposed direction (render the authoring skeleton from the same grammar the rule enforces, so the instruction and the check cannot disagree). Then pre-execution can be added back to _ORCH_ROW_BLOCKING_CHECKPOINTS as a one-line change.

WHY dpdyed DID NOT DO IT: agent_workflows/ipd_authoring.py is not in that plan's - Scope-Paths:. tests/test_orchestrator_row_grammar.py::TheRuleActuallyFires::test_the_SHIPPED_SCAFFOLD_is_not_conforming_which_is_why_begin_is_not_gated pins the current state and FAILS LOUDLY when the scaffold is fixed, pointing the reader here.
