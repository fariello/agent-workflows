- Id: ahlgnm
- Status: open
- Set: attselratify
- Priority: medium
- Work-Kind: followup
- Summary: Ratify or relax the aw attention no-match exit contract: exit 2 and a refusing --check shipped as the fail-closed default

## Workflow history
- 2026-09-21 created (aw backlog): Ratify or relax the aw attention no-match exit contract: exit 2 and a refusing --check shipped as the fail-closed default

CARRIES OQ-01 AND OQ-02 of plan fqnj8k (attsel-01) past that plan's execution, so the maintainer's outstanding call does not vanish when the plan classes done. Both questions were NON-BLOCKING and both are IMPLEMENTED; what is outstanding is ratification, not design.

WHAT SHIPPED, 2026-09-21, at the plan's own direction ("execute with the FAIL-CLOSED form (nonzero on a no-match, --check refusing) and do not guess a relaxation"):
  * OQ-01: a selector matching no artifact exits 2 on EVERY surface (human board, --agent, --json, --format json, --check, -id, --paths, --filenames), with outcome cannot-run on the machine surfaces. Constant: attention.EXIT_UNRESOLVED_SELECTOR.
  * OQ-02: --check REFUSES rather than printing "the view is valid" about a token it never resolved, and the refusal is a SEPARATE condition from the drift set (no Drift record is appended, --json's valid flag is never flipped by an operator typo).
  * Two exemptions, so the fail-closed default does not call correct usage wrong: a BARE invocation with no selector still exits 0, and a VOCABULARY token (tree name, attention class, artifact status, priority, run state, or any TYPE_ALIASES spelling, 63 tokens derived from contract symbols) that matches nothing still exits 0.

THE PRECEDENT FOLLOWED, since the choice was between two live conventions: spec 25kzda (approved) Section 2.3 "Zero matches return exit 2" with the 2.4a status-selector exemption, as implemented by `aw runs`. The rejected alternative is `aw find`'s exit 0 with an explicit empty-result message, which is filed separately as hd5bkk.

WHAT A MAINTAINER MIGHT STILL WANT, and why this is worth a durable item rather than a closed question. `aw attention` is used interactively many times a day, and its exit code previously meant "the view is valid"; a script or shell prompt already treating nonzero as "the repo is broken" now also sees nonzero for a typo. If that turns out to be annoying in practice, RELAXING IS CHEAP AND LOCALIZED: OQ-01 is one constant (EXIT_UNRESOLVED_SELECTOR) plus its pinning tests, and OQ-02 is one branch, deliberately kept separate from the drift path precisely so it can be relaxed without touching drift. The code comment at the constant names both rejected alternatives so the reasoning is visible at the edit site.

NO CI CHANGE IS INVOLVED EITHER WAY: .github/workflows/tests.yml runs `attention --check --agent` with NO selector, so the new predicate cannot fire on it (measured unchanged, exit 1 from the repository's 27 pre-existing violations).

CLOSE THIS by either recording ratification (no code change) or filing the relaxation.
