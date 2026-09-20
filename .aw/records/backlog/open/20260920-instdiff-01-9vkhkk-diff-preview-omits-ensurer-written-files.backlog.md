- Id: 9vkhkk
- Status: open
- Blocks-Release: next
- Set: instdiff
- Priority: medium
- Work-Kind: bug
- Summary: Teach the install --diff preview about the ~49 ensurer-written files it still omits, so the dry run stops under-reporting an apply

## Workflow history
- 2026-09-20 created (aw backlog): Filed by plan at61gc as the durable carrier for its F-13 deferral.

MEASURED at plan at61gc's execution (2026-09-20, HEAD f156e14c, after at61gc's fix landed): `python3 install-workflows.py --repo <throwaway> --diff --no-color` proposes 305 files while a real apply into a throwaway repo writes 353. The residual ~49 are scaffolding written by separate `ensure_*` steps the preview has never modelled: `.aw/records/**` READMEs and `.gitkeep`s, `.aw/.gitignore`, and similar.

WHY THIS IS A BUG AND NOT A CHORE, by the repository's user-perceptible-impact test: `--diff` is a DRY RUN whose entire purpose is to show an operator what an apply would write, so any file it omits is wrong output on the one surface used to decide whether to apply. The omission is directly operator-visible (a count an operator can compare), not an internal inefficiency.

SCOPE AND THE DESIGN QUESTION IT CARRIES. `engine.show_install_diffs` builds its proposed set from body members plus the generated map it is handed; the ensurer steps run later, inside `install_into_repo`, and each writes only when its target is ABSENT. So closing this means either teaching the preview about every ensurer or factoring the ensurers into a declarative member map both paths consume, and it needs an answer to what a preview should SAY about a file created only when absent (propose it? mark it conditional? omit it when present?). That is materially larger than at61gc's one-line call and is why at61gc deliberately excluded it.

PROVENANCE. Deferred by plan `at61gc` (F-13, 'THE ~49 ENSURER-WRITTEN FILES THE PREVIEW STILL OMITS'), which closed the GENERATED-member half of backlog `bplplj` (preview now reports all 92 skill files, previously 0). This item is the durable carrier for that deferral, which `check.ipd-uncarried-obligation` flags when a plan's deferred row names none.
