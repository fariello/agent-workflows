- Id: ariaau
- Status: open
- Set: malgate
- Priority: medium
- Work-Kind: chore
- Summary: Audit every gate and check for ones that exist only to stop a malicious agent (GUIDING_PRINCIPLES P15) and keep, simplify, or delete each

## Workflow history
- 2026-09-26 created (aw backlog): Filed 2026-09-26 at the maintainer's request (lifegate dvonrn D5), for hand-off to another agent.

WHAT. Apply GUIDING_PRINCIPLES P15 (added 2026-09-26: we guard against honest mistakes, never against a malicious agent) to the existing gates. For EACH gate, check, refusal, or scaffold found, decide one of: KEEP (it catches an honest mistake with a clear message), SIMPLIFY (turn it into a plain refusal with a remedy and, where a human may need one, a recorded override), or DELETE (its only purpose is stopping a deliberately hostile agent). Record the decision per item with the evidence.

START HERE (found 2026-09-26, not exhaustive):
- agent_workflows/wtiso_gate.py: five predicates that deliberately raise (check_lifecycle_role, check_hook_bypass, classify_retention, check_receipt, check_protected_refs) and a check_scope body with zero callers; their Phase-2 wiring was retired unlanded. Pinned by tests/test_containment_predicates.py.
- Plan 8zgybk (wtiso Phase 0) and research x03wgn: 'adversarial' characterization scaffolding and any tests that encode malicious-agent threat models.
- Code comments and docstrings citing a 'determined same-user agent' or 'malicious' agent as the justification for a check (grep -rn -i 'malicious\|determined same-user' agent_workflows/).
- Any hook or verb that hides, withholds, or verifies a secret from an agent.

ALREADY DECIDED, DO NOT REDO:
- The per-run driver attestation token (plan u27oh3): REMOVED by the lifegate design (backlog dvonrn). Out of scope here.
- --by-human attestation: KEEP; its spec already frames it as an honest speed bump.
- Suite-baseline adjudication: KEEP; it refuses nothing and is the model example.
- Opt-in hardened OS sandbox (host_sandbox_profile, plan 1o4eif): KEEP as optional isolation (lifegate D7).

OUTPUT. A research or decision record listing every item found with its keep/simplify/delete decision and evidence, plus one reviewed plan per non-trivial removal or simplification. Honest-limit to carry: a deletion changes behavior other plans or specs may cite, so each removal must check for and update those references.
