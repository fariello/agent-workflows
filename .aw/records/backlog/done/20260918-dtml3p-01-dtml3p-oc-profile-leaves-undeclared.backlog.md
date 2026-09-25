- Id: dtml3p
- Status: done
- Set: dtml3p
- Priority: medium
- Work-Kind: bug
- Summary: Declare the five oc profile CLI leaves so the conformance matrix gate stops failing

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: duplicate of 4fe3al
- 2026-09-18 created (aw backlog): Declare the five oc profile CLI leaves so the conformance matrix gate stops failing

MEASURED 2026-09-18 while executing runanalytics Order 10 (9xycbh) E-10, which runs the slow-marked gates the bare suite deselects.

`tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests` has TWO live failures:

    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set

Both report the same five parser leaves that carry no `CommandDeclaration`:

    ['oc profile add', 'oc profile default', 'oc profile list', 'oc profile remove', 'oc profile show']

PROVEN PRE-EXISTING rather than assumed, three ways. (1) Order 10 changes no code under
`agent_workflows/` at all; its diff is four new test/fixture modules plus README/docs. (2) Re-running
that test class with Order 10's work set aside still reported `2 failed, 2 passed`, identical five
leaves. (3) A sibling already pinned them: `tests/test_run_analytics_cli.py` carries
`KNOWN_UNDECLARED` with exactly these five, described in place as 'the measured pre-existing baseline
... a live failure of test_no_undeclared_parser_leaves that predates this plan and is explicitly out of
scope'.

WHY IT IS A BUG AND NOT A CHORE. The user-perceptible impact is that a fail-closed conformance gate is
RED, so it can no longer tell a reviewer whether a NEW undeclared leaf was added: the signal is already
failing, and the next genuine regression hides inside the same two failures. A sibling worked around it
by pinning a KNOWN_UNDECLARED allowlist, which is evidence the gate has stopped doing its job rather
than evidence the failure is harmless.

THE FIX is to add a `CommandDeclaration` for each of the five leaves in
`agent_workflows/command_surface.COMMAND_INVENTORY` (with the right `command_class`: `list` and
`show` are reads, `add`, `remove` and `default` are mutations) and let the scenario-row-set
assertion follow. Not done inside 9xycbh because declaring CLI leaves is outside that plan's
Scope-Paths and edits a normative inventory, which is exactly the kind of change that plan is forbidden
to make opportunistically.
