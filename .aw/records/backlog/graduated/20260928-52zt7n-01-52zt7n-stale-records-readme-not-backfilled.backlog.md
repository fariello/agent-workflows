- Id: 52zt7n
- Status: graduated
- Graduated-To: readmestale
- Set: 52zt7n
- Priority: low
- Work-Kind: followup
- Summary: A stale records-root README survives forever in an already-installed repo because the ensurer is no-clobber

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053059Z-3200713: xqf71x
- 2026-09-28 created (aw backlog): A stale records-root README survives forever in an already-installed repo because the ensurer is no-clobber

MEASURED 2026-09-28 at HEAD db024a61 while authoring plan v3cw46 (backlog 2oq6s8).

WHAT WAS MEASURED. `engine.ensure_plans_readmes` skips any target that already exists (`if readme_path.is_file(): skipped.append(f"{rel_path} [already current]")`). Confirmed empirically: after a fresh install into a scratch repo, overwriting `.aw/records/README.md` with custom text and re-running the installer reported `[no change] .aw/records/README.md` and left the custom text intact.

WHY IT MATTERS HERE. Plan `v3cw46` corrects the shipped `agents-README.md` template, which names a `.aw/records/workflows/` directory no `aw` install creates. Because the ensurer is no-clobber, that fix reaches NEW installs only: every already-installed repo keeps the stale front door, including its dead `workflows/index.md` pointer, indefinitely.

THE POLICY IS CORRECT AND IS NOT THE DEFECT. A user's own README must never be overwritten, so this is NOT a request to force-write the template. The open question is narrower: may a framework-written file still carrying the KNOWN STALE SHIPPED TEXT be repaired, and who decides?

TWO CANDIDATE REMEDIES, both with in-tree precedent.
(a) DETECT-THEN-OFFER, as the installer already does for command shims: `engine.is_shim_customized_vs_expected` compares a normalized actual against a normalized expected, so a file byte-matching a known-stale shipped version can be distinguished from a user-customized one and repaired or offered. The same shape would work here, keyed on the pre-fix template text.
(b) REPORT-ONLY via `aw doctor`, which leaves every write to the human and cannot surprise anyone. Strictly weaker but strictly safer.

A THIRD OPTION IS TO DO NOTHING, and it is defensible: the stale text misroutes a reader but breaks no tooling, and the trees it fails to mention are discoverable by listing the directory.

WHY FILED RATHER THAN FIXED IN v3cw46. Deciding whether the installer may rewrite an existing user-visible file is a policy question for the maintainer, not a side effect of a template correction, and building a back-fill mechanism inside that plan would be scope broadening. Plan v3cw46 E-05 files this item and cites it in its Deferred section.

SECOND, SMALLER FINDING FOUND IN THE SAME PASS (cosmetic, not functional). `releases` is a key in `engine._record_scaffold_dirs('aw')` but is absent from the `for key in (...)` .gitkeep loop in `engine.create_setup_artifacts`, so a fresh install creates `.aw/records/` with ten typed trees and no `releases/`. IT IS NOT BROKEN: `aw release new --apply` was run in a fresh scratch install and created the tree plus the record successfully (the producer mkdirs its parent), so nothing fails and no user is blocked. The only consequence is that the tree is absent until first use, unlike its ten siblings which ship a `.gitkeep`. Worth deciding deliberately (scaffold it for symmetry, or leave it lazily created), which is why it is recorded rather than dropped. Plan v3cw46 deliberately does NOT name `releases/` in the corrected template for this reason.
