- Id: jerb7j
- Status: open
- Set: runverdict
- Priority: medium
- Work-Kind: chore
- Summary: Advertise the accepted verifier verdict tokens in the verifier prompt so the schema and its fail-closed consumer cannot disagree

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan 1bfppy.

The verifier prompt's schema line advertises `"verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED"`, but `runner_shared.map_verdict` (plan `1bfppy`) recognizes a FOURTH token, `NOT CONFORMING`, as a rejection. It is mapped because the pre-existing gate honored it, so mapping it preserved behavior rather than changing it.

WHY THIS IS WORTH FILING RATHER THAN LEAVING. The mapping is now fail-closed, so an unadvertised token is no longer a safety hole: anything the table does not know is recorded NOT verified with an explicit reason. The residual defect is a CONTRACT DISAGREEMENT: the prompt asks for three values while the consumer knows four, which is the same producer/consumer drift that let the original defect exist (finding F-6 on that plan). A reader of either side cannot derive the other.

MEASURED at plan execution (2026-09-22): `NOT CONFORMING` appears NOWHERE in the repository except the gate that tested for it - not in a prompt, a test, an outcome file, or a spec - so nothing is known to emit it. Its sibling `CONFORMING` is deliberately NOT accepted (plan 1bfppy OQ-02: at HEAD it already mapped to `unverified`, so accepting it would have made the fail-closed table more permissive than the gate it replaced).

THE FIX IS A SCHEMA DECISION, NOT A CODE FIX, which is why the plan fenced it out: either advertise the tokens the consumer accepts, or drop the alias and let it fall to the fail-closed arm. Whoever owns the verifier prompt schema should decide. Note `tests/test_reporting_contract.py` asserts the prompt's verdict line VERBATIM, so a prompt edit is a deliberate, test-visible act.
