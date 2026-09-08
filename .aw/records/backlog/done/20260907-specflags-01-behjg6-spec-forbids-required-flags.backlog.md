- Id: behjg6
- Status: done
- Set: specflags
- Priority: high
- Work-Kind: bug
- Summary: Spec 25kzda 2.1 wrongly forbids operationally-required flags by name: capture the requirement instead of prohibiting it

## Workflow history
- 2026-09-08 done (aw set): OBSOLETE: the 2.1 correction this item asked for landed in 844d195c on 2026-09-06, one day BEFORE this item was created. Verified at HEAD: the prohibition sentence is gone (:162 records the supersession), the requirement is captured positively by 7ckptx R4.1c (:277) and pinned by tests/test_lane_permission_posture.py:315, and :161 keeps only the two real prohibitions. Gate RELEASED rather than transferred: ki6tom named this item as its Blocks-Release carrier, but there is no remaining work to carry.
- 2026-09-07 created (aw backlog): Spec 25kzda 2.1 wrongly forbids operationally-required flags by name: capture the requirement instead of prohibiting it

OBSOLETE 2026-09-08, VERIFIED IN-REPO. DO NOT GRADUATE THIS ITEM: the correction it asks for HAS
ALREADY LANDED, and it landed BEFORE this item was even written. This item was created 2026-09-07 while
resolving plan `ki6tom` OQ-01, on the belief that spec `25kzda` 2.1 still forbade the operationally
required flags. It did not. Commit `844d195c` (2026-09-06) had already amended 2.1, one day earlier.

WHAT THIS ITEM ASKED FOR, AND WHERE EACH PART NOW LIVES, each checked at HEAD:
  1. "2.1 stops forbidding a capability that is operationally required." DONE. The sentence "There is
     no `--no-verify`, `--skip-audit`, `--dangerous`, or hook-bypass flag on `run`" is GONE. Spec `:162`
     records the supersession explicitly and states that `--dangerous` "is REMOVED from this prohibition".
  2. "CAPTURE the requirement, with its required default and the reason." DONE, and captured in the
     right place: `:162` names `7ckptx` R4.1c as "the controlling authority on host permission posture",
     and R4.1c (`:277`) states the constraint positively as a REQUIREMENT on drivers, pinned by
     `tests/test_lane_permission_posture.py:315`. Spec `:96` states in as many words that this "is not an
     unclosed gap awaiting work: it is a decided constraint".
  3. "Distinguish prohibited spellings from required capabilities." DONE. `:161` keeps exactly the two
     prohibitions that are real (`--skip-audit`, and the GIT sense of `--no-verify` via the commit
     gateway) and `:162` explains the conflation of the two `--no-verify` senses that caused the defect.
  4. "State the per-profile-configuration end state for `--no-verify`." Already tracked by its own live
     work (`kgpptv`, approved; `f2mrsw` E-03), not by this item.

WHY THIS IS `done` AND NOT `parked`: nothing here awaits a decision or a future opportunity. The
requested change exists in the tree, so the item is satisfied rather than shelved. The evidence citation
is the spec file itself.

CONSEQUENCE FOR `ki6tom`, stated so the handoff is not silently broken: `ki6tom` was retired to
`not-executed/` on 2026-09-08 naming THIS item as the carrier of its `Blocks-Release: next` gate. That
reasoning was wrong in the same way this item was: there was no remaining work to carry. The gate is
released rather than transferred, because the contract `ki6tom` enforced was withdrawn and the
correction it pointed at had already shipped. No release blocker is lost, because none remains.

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
