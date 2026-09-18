- Id: nmg89m
- Status: open
- Blocks-Release: next
- Set: nmg89m
- Priority: medium
- Work-Kind: bug
- Summary: The mutating pre-commit hooks' exclude regex names a research path that matches zero live files, so the verbatim-preservation intent is unenforced

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): The mutating pre-commit hooks' exclude regex names a research path that matches zero live files, so the verbatim-preservation intent is unenforced

DISCOVERED while executing IPD `lqly9m` (E-05), and recorded there in F-19 and in that plan's deferred
section as explicitly NOT its own to fix.

THE DEFECT. `.pre-commit-config.yaml:29-35` excludes the research trees from all four content-MUTATING
hooks (`trailing-whitespace`, `end-of-file-fixer`, `ruff --fix`, `ruff-format`) with the stated reason
that these are "cited external research artifacts (their own formatting/punctuation is intentional)".
The regex names `\.agents/docs/research/` and `\.aw/records/docs/research/`. Measured at HEAD
`4b68a786`: `.aw/records/docs/research/` matches ZERO tracked files, because the tree was flattened to
`.aw/records/research/` (129 tracked files) in the physical-layout migration. So the exclusion no
longer protects the real research tree, and every one of those 129 files is currently subject to the
mutating hooks the comment says must not touch them.

WHY IT WAS NOT FIXED IN `lqly9m`. That plan's `Scope-Paths` does not include `.pre-commit-config.yaml`,
and the change has its own blast radius: it would newly exempt 129 tracked files from four hooks, which
is a policy decision about what the repository lints, not a bug fix. `lqly9m` instead made its own
writer (`artifact_core.atomic_write`) exempt those trees, so the toolkit does not become a second
mutator; that is a narrower guarantee and does not cover the hooks.

WHAT THE WORK IS. Decide whether the verbatim-preservation intent still holds for the flat
`.aw/records/research/` tree. If it does, add that path to the exclude regex of all four mutating hooks
(and consider whether `.aw/records/docs/research/` should be dropped as dead). If it does not, remove
the stale alternative and the comment that asserts the intent, so config and comment agree. Either way
the current state is the worst one: a comment claiming a protection the regex does not deliver.

MEASURED BASIS: `.pre-commit-config.yaml:1-10` (the stated reason), `:29-35` (the four hooks and the
regex), `git ls-files .aw/records/docs/research | wc -l` = 0, `git ls-files .aw/records/research | wc -l`
= 129.
