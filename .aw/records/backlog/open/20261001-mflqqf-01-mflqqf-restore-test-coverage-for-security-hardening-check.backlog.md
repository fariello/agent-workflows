- Id: mflqqf
- Status: open
- Graduated-To: mflqqf
- Set: mflqqf
- Priority: high
- Work-Kind: security
- Summary: Restore test coverage for security hardening checkers and packaging boundary

## Workflow history
- 2026-10-06 open (aw set): u57rfv returned to authoring: uncovered obligation: This plan runs no test itself; validation is an inspection of what the children actually produced; re-run graduation to complete the handoff
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: d0lg63, gqyold, u57rfv
- 2026-10-01 created (aw backlog): Restore test coverage for security hardening checkers and packaging boundary

Measured at execution HEAD (4e6cae0959d870fdd6cc0568f89a4dac57029f74):

1. Searching tests/ for the seven checker functions in agent_workflows/security_hardening.py:
- check_local_server_binding: 0 test matches
- check_external_file_access: 0 test matches
- check_skill_least_privilege: 0 test matches
- check_evidence_redaction: 0 test matches
- check_real_home_excluded: 0 test matches
- check_untrusted_text_isolated: 0 test matches
- check_destructive_tool_gated: 0 test matches
The former suite tests/test_security_hardening.py was deleted in commit 19313eed.

2. Searching tests/ for packaging boundary tests:
- tests/test_packaging.py was deleted in commit 19313eed.
- Zero test files match force-include or hatch.build.
- No test builds a wheel and asserts its contents.

Work-Kind rationale:
- Selected: security. Shipped runtime security boundaries and packaging boundaries lack dedicated test guards.
- Rejected bug: Missing tests are not user-perceptible runtime defects.
- Rejected chore: Fails to reflect the security sensitivity of these boundaries.
- Rejected followup: Not trailing work from an active plan.
