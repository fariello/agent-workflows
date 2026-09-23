- Id: mgz3f1
- Status: open
- Set: mgz3f1
- Priority: medium
- Work-Kind: followup
- Summary: The records-only re-derivation carve-out does not cover a backfill that also writes Blocks-Release, so lc4unl-shaped lanes still strand

## Workflow history
- 2026-09-22 created (aw backlog): The records-only re-derivation carve-out does not cover a backfill that also writes Blocks-Release, so lc4unl-shaped lanes still strand

MEASURED 2026-09-23 while executing plan `kl18sz`, which landed the records-only front-matter re-derivation carve-out (spec `25kzda` Section 2.1a).

THE CARVE-OUT'S ALLOW-LIST IS EXACTLY `- Work-Kind:` and `- Priority:`, deliberately, because those are the two keys the measured `8u6770` incident needed and because an allow-list is the safety property. Measured against the SIBLING lane the plan itself names as the same archetype (F-6), the carve-out therefore does NOT fire:

    $ # aw/lane/lc4unl survives as dangling commit b1223b4f
    $ # classify its two conflicting plan paths
    not-this-shape | the incoming side added front-matter key(s) ['Blocks-Release'] that are NOT on the
    re-derivable allow-list (['Priority', 'Work-Kind']); a key with lifecycle, gate, identity or
    attestation meaning must never be written by an automated integration

THE REFUSAL IS CORRECT AND MUST NOT BE 'FIXED' BY WIDENING THE ALLOW-LIST. `- Blocks-Release:` carries a RELEASE GATE, and `kl18sz` F-9 plus the new spec section both state that an integration able to write a gate field automatically would be strictly worse than the conflict it resolves. `tests/test_records_only_lane_rederive.py` fails if the allow-list is widened to include it, deliberately.

SO THE GAP IS REAL BUT ITS FIX IS NOT OBVIOUS, which is why this is filed rather than patched. A `lc4unl`-shaped lane (one that backfills descriptive metadata AND a release gate in the same edit) still strands on a genuine conflict and still needs a human. Options a future plan should weigh: (a) accept it, on the ground that a release-gate write genuinely deserves a human; (b) split such a backfill into two commits at AUTHORING time, so the descriptive half re-derives and only the gate half can conflict; (c) extend the classifier to re-derive the allow-listed subset and REFUSE the rest, which E-04's all-or-nothing rule currently forbids for good reason.

NOTE the second `lc4unl` path classifies `no added front-matter key`, i.e. its conflict is elsewhere in the file, so it was never a candidate for this shape at all.

Raised by an executor during a non-interactive `aw oc run` turn; the decision between (a), (b) and (c) is a maintainer's, since it trades operator toil against automated writes to a gate field.
