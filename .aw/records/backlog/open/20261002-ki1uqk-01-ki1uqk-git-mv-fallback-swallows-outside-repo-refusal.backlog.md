- Id: ki1uqk
- Status: open
- Blocks-Release: next
- Set: ki1uqk
- Priority: medium
- Work-Kind: bug
- Summary: artifact_core.git_mv swallows git's own 'outside repository' refusal and moves the file anyway with shutil.move, leaving the index inconsistent; measured 2026-10-02 while authoring plb8jx

## Workflow history
- 2026-10-02 created (aw backlog): artifact_core.git_mv swallows git's own 'outside repository' refusal and moves the file anyway with shutil.move, leaving the index inconsistent; measured 2026-10-02 while authoring plb8jx

FILED AS THE CARRIER for the deferred `git_mv` row in plan `plb8jx` (Set `0ougsh`), which fixes the `aw research set-assign --date` traversal at the verb and deliberately leaves this helper alone.

MEASURED 2026-10-02 in a lane at HEAD `afae0d0e8`, against a temporary fixture repository nested four levels deep so the escape lands somewhere writable (a shallow fixture measures the filesystem's permissions, not the helper).

`artifact_core.git_mv` is `(repo_root / dst_rel).parent.mkdir(parents=True, exist_ok=True)`, then a `git mv` subprocess, then `if result.returncode != 0:` -> `shutil.move(str(repo_root / src_rel), str(repo_root / dst_rel))`, under the docstring "git mv (staged, not committed), with a filesystem fallback for untracked files".

GIT ITSELF REFUSES THE MOVE AND THE HELPER OVERRIDES IT. Driven directly: `git -C <repo> mv -- .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md .aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md` exits **128** with `fatal: '.aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md' is outside repository at '<repo>'`. The helper treats that as the untracked case and performs the move anyway, so a TRACKED file leaves the repository through a fallback written for untracked ones.

THE RESULTING STATE IS WORSE THAN A MOVED FILE, because the index and the filesystem disagree. After the move: `git status --short` reports ` D .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md` (an UNSTAGED deletion, because `shutil.move` staged nothing) while `git ls-files` STILL LISTS that path. The escaped copy is untracked and outside the repository, so a later `git checkout`/`restore` resurrects a stale record while the moved file lingers out of tree.

WHY THIS IS SEPARATE FROM `0ougsh` AND FROM `m5csyi`: those items are the research verbs that PLAN a bad destination (`set-assign` on the rename path, `new`/`new-comparison` on the creation path), and plan `plb8jx` closes the first at the verb so it never reaches this helper. This item is the helper itself, which is shared by every rename and archive verb in the toolkit (`research_refs._apply_renames`, `research_archive.apply_moves`, and `engine`'s installer moves), and which remains reachable by ANY other caller that plans a destination outside the repository. Neither of those items names it.

THE FIX IS NOT SIMPLY "DELETE THE FALLBACK": it exists deliberately so an untracked file can still be moved, and `git mv` exits nonzero for BOTH the untracked case and the outside-repository case. So the fix must DISTINGUISH them (for example, refuse when the destination resolves outside the repository root, using the `relative_to`/`ValueError` idiom `check_engine.resolve_evidence_artifact` uses, while keeping the fallback for a genuinely untracked source) rather than collapsing them. Whichever shape is chosen should be measured against every caller, since narrowing it is a behavior change to the toolkit's shared move primitive.
