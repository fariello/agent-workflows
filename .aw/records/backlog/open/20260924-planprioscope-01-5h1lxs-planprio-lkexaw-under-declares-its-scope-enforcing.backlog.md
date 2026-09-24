- Id: 5h1lxs
- Status: open
- Blocks-Release: next
- Set: planprioscope
- Priority: high
- Work-Kind: bug
- Summary: planprio lkexaw under-declares its scope: enforcing Priority and Work-Kind at the ready-to-execute gate breaks 175 tests across 21 undeclared test files, so the verifier correctly refused it

## Workflow history
- 2026-09-24 note (aw backlog): NARROWED 2026-09-24 from 175 failures across 21 files to SEVEN, by fixing the cause rather than the symptom (lane aw/lane/lkexaw_attempt4, commit 6a89029d). 21 test files each carried their own copy of 'write a throwaway plan'; tests/support.ready_plan_text is now the one shared builder and four near-identical private copies delegate to it. Fixtures resolve REAL vocabulary values, not the grandfathered sentinel: the sentinel is advisory-satisfied rather than silent and asserts the plan predates the rule, which a fixture built milliseconds ago does not (maintainer decision). WHAT REMAINS IS NOT FIXTURE HYGIENE AND IS THE ACTUAL PRODUCT GAP: seven tests assert that a real 'aw ipd scaffold' followed by 'aw ipd set approved' lints CONFORMING. It no longer can. build_skeleton correctly emits 'Priority: unresolved' / 'Work-Kind: unresolved' (a draft has not decided them, and that sentinel is what makes the gate refuse an unfinished plan), but nothing resolves those placeholders on the approve path, so the setter now produces an unexecutable plan. That is precisely the defect test_scaffolded_ipd_set_approved_lints_conforming was written to prevent, and its own docstring says so: 'proving the setter no longer produces an unexecutable plan'. THE DECISION NEEDED, which is why this is not fixed here: either aw ipd set approved must resolve the two placeholders (prompting or defaulting, and defaulting silently writes a priority nobody chose), or the scaffold must not emit 'unresolved' for them, or the gate must treat scaffold placeholders differently from a missing field. lkexaw's E-07 touches the setter's flag surface but no item owns this path. Affected: test_status_set (scaffold+approve lints clean), test_ipd_lint x2 (the three-valued checkpoint outcome and the density advisory), test_orchestrator_row_grammar, test_orchestrator_retirement, test_novalnomerge_integration, test_work_commit.
- 2026-09-24 created (aw backlog): planprio lkexaw under-declares its scope: enforcing Priority and Work-Kind at the ready-to-execute gate breaks 175 tests across 21 undeclared test files, so the verifier correctly refused it

MEASURED by the verifier on run run-20260924T165302Z-1635336 (verdict BLOCKED), and the refusal is CORRECT: the work is quarantined on aw/lane/lkexaw and was never merged.

WHAT THE PLAN GOT RIGHT. Inside its declared fence the implementation is sound: 'python3 -m pytest tests/test_plan_priority_required.py tests/test_work_kind.py tests/test_ipd_priority.py tests/test_ipd_templates.py' -> 52 passed, exit 0.

WHAT IT MISSED. The full suite fails: 175 failed, 8686 passed. The failures span 21 test files, of which lkexaw declares THREE. Worst offenders: tests/test_ipd_lifecycle_cli.py (49), tests/test_finalize_scope_ownership.py (23), tests/test_receipt_requirement_digest.py (17), tests/test_finalize_exact_attribution.py (12), tests/test_begin_dirty_gate_scope.py (11), tests/test_finidem_double_finalize.py (11).

CAUSE. Making Priority and Work-Kind REQUIRED at the ready-to-execute gate invalidates shared test helpers (_ready_plan_text, _plan_text and siblings) that construct approved / pre-execution plans without those fields. Every test building a plan through those helpers now trips the new gate. This is a fixture-contract change disguised as a gate change, and the blast radius is the whole lifecycle suite rather than the three files the plan fenced.

WHY IT IS FILED RATHER THAN FIXED HERE. The fix is a judgement about the gate's reach: either (a) widen Scope-Paths to the 21 files and update every helper to emit the two fields, which is a large mechanical sweep the plan never budgeted, or (b) grandfather existing fixtures and enforce only on NEWLY authored plans, matching how the setid-length and id6 rules were introduced. Those are materially different products and the choice belongs to the maintainer.

CONSEQUENCE WHILE OPEN. planprio orchestrator d0cbt3 is dependency-blocked on lkexaw and cannot retire, so the Set stays open. lkexaw remains 'partial' with its lane preserved; its E/V bookkeeping is also unpopulated, but that is downstream of the scope decision and should not be ticked until the gate's reach is settled.
