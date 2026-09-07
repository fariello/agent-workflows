- Id: behjg6
- Status: open
- Blocks-Release: next
- Set: specflags
- Priority: high
- Work-Kind: bug
- Summary: Spec 25kzda 2.1 wrongly forbids operationally-required flags by name: capture the requirement instead of prohibiting it

## Workflow history
- 2026-09-07 created (aw backlog): Spec 25kzda 2.1 wrongly forbids operationally-required flags by name: capture the requirement instead of prohibiting it

MAINTAINER RULING 2026-09-07, recorded while resolving plan `ki6tom` OQ-01: the spec is WRONG in
forbidding these flags. `--dangerous` (and its `--dangerously-skip-permissions` spelling) is 100%
NEEDED on the antigravity host, and the fact that it is needed should have been CAPTURED somewhere
rather than expressed as a prohibition the operational reality then has to violate.

THE CONTRADICTION, IN THE REPOSITORY'S OWN RECORDS. Spec `25kzda` 2.1 (`:135`, `:140`) forbids four
spellings on `run` BY NAME: `--no-verify`, `--skip-audit`, `--dangerous`, and "hook-bypass" flags. But
approved spec `7ckptx` R4.1c FORBIDS ANY PLAN from flipping agy's `--dangerously-skip-permissions`
default, on recorded operational evidence and a maintainer ruling dated 2026-09-01, and
`tests/test_lane_permission_posture.py:315` PINS that default with a failure message naming R4.1c.
So one approved spec forbids the flag by name while another approved spec plus a shipped test
guarantee the capability and its default. Both cannot be right.

WHY IT MATTERS BEYOND TIDINESS. A prohibition that operational reality must violate produces exactly
the failure `ki6tom` walked into: that plan's self-declared centerpiece (E-02) was authored as a
safety fix that turned out to be PROHIBITED work, because it read 2.1's by-name prohibition as the
governing constraint and would have flipped the default `7ckptx` protects. The review caught it, but
only after the plan had taught its reader that a decided constraint was an open defect. A spec that
misdescribes a required capability actively manufactures wrong plans.

WHAT DONE LOOKS LIKE: 2.1 stops forbidding a capability that is operationally required and instead
CAPTURES the requirement, distinguishing (i) spellings genuinely prohibited on the `run` surface from
(ii) capabilities that must exist, with their required defaults and the reason. The distinction the
correction must preserve is the one `ki6tom` E-02 relies on: a prohibited NAME for a REQUIRED
capability is a naming question, not a safety question, so removing an alias while the capability and
its default survive stays legitimate. `7ckptx` R4.1c and the pinning test are the authority on the
default and must not be weakened to achieve consistency; 2.1 is the side that moves.

ALSO IN SCOPE, because it is the same defect one layer down: `--no-verify` on agy. Its real need is
PER-MODEL ROUTING, not a global bypass, and that capability is being built (`kgpptv` gives the
verifier its own frozen profile; `f2mrsw` E-03 resolves a per-profile `validate` tri-state). Plan
`ki6tom` E-04 is DEFERRED until both land, so this correction should state the end state: verification
is controlled by CONFIGURATION per profile, and no CLI bypass is needed for it.

RELATED: `dk16dx` (spec-amendment visibility at run start and end) is the mechanism that makes any
amendment to `25kzda` visible; this item is a specific amendment that will use it.
