- Id: e2j5w4
- Status: open
- Blocks-Release: next
- Set: id6slotgate
- Priority: high
- Work-Kind: bug
- Summary: aw check misses check.id6-identity-slot on a live D140 violation because check_collisions gates the slot pass on the caller's liveness filter

## Workflow history
- 2026-09-21 created (aw backlog): aw check misses check.id6-identity-slot on a live D140 violation because check_collisions gates the slot pass on the caller's liveness filter

MEASURED 2026-09-21 while executing IPD paw8so.

WHAT IS WRONG. `check_engine.check_collisions` builds its `records` list for the identity-slot pass with `caller_visible = include_retired or not is_retired(p, record_type)`, appending only CALLER-VISIBLE records, and then calls `_check_identity_slots(records)`. Its id6-collision sibling pass in the same loop deliberately uses EVERY file, retired or not, with the recorded reason that 'a terminal id6 is permanently cited, so a collision with one is real' (docstring, IPD sk7ggr F-3). The identity-slot pass needs that same corpus for the same reason and does not get it.

MEASURED EFFECT. `ce.check_collisions(root)` returns 15 findings, ALL `check.id6-collision` and ZERO `check.id6-identity-slot`. `ce.check_collisions(root, include_retired=True)` returns the same 15 PLUS 3 `check.id6-identity-slot`. Calling `_check_identity_slots` directly on a full record list also returns those 3. So `aw check all` reports 0 while three real violations sit on disk:

  .aw/records/walkthroughs/20260906-lanectn-04-y5od1h-missing-input-report-and-refuse-walkthrough.md
  .aw/records/walkthroughs/20260917-lanectn-07-4fodkt-whole-set-verification-of-spec-7ckptx.walkthrough.md
  .aw/records/walkthroughs/20260901-runstop-00-zpbx7o-graceful-quit-whole-set-verification.walkthrough.md

Each carries a PLAN's id6 in its own filename identity slot while declaring no `- Id:` of its own. All three plans are in `plans/executed/`, which is precisely why the liveness filter hides the pair.

WHY IT IS A BUG AND NOT A JUDGEMENT CALL. `.aw/records/walkthroughs/README.md` states the rule and names the enforcement: 'The `<id6>` in the filename identity slot is the walkthrough's OWN unique identity (DECISIONS.md D140): a walkthrough MUST mint its own id6 there and MUST NOT reuse the id6 of the plan it documents ... `aw check`/`aw doctor` enforce this via the `check.id6-identity-slot` rule.' The rule exists, is registered at severity `error`, and does not fire. D140's own 'Applied (2026-09-20, IPD sk7ggr)' paragraph records fixing exactly this class of blindness for the id6 pass; the slot pass was left behind.

USER-PERCEPTIBLE. An operator running `aw check all` is told the tree is clean of identity-slot violations when it is not, which is a wrong answer from a gate, not a slow one.

HOW IT WAS FOUND. IPD paw8so added a collision warning to `aw find`; `aw find y5od1h` now reports the cross-type claim while `aw check all` stays silent. Two of the three (`4fodkt`, `zpbx7o`) carry a typed `- Target-Id:` field, so paw8so's discriminator classifies them as documented REFERENCES and does not warn; `y5od1h` carries no typed field at all and is the p7dqwz shape verbatim.

SUGGESTED FIX. Give the identity-slot pass the same terminal-inclusive corpus the id6 pass already uses, and keep the setid pass on the caller's corpus (its comment records why widening it ships 47 legitimate findings). Note the three records above are REAL violations needing their own remediation decision; do not 'fix' the count by narrowing the rule.
