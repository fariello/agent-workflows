- Id: vvc7c1
- Status: open
- Set: vvc7c1
- Priority: medium
- Kind: feature
- Summary: Records-mutating commands (aw archive, and likely group/rename/research regroup) should offer to commit their own path-scoped changes when run interactively

## Workflow history
- 2026-08-24 created (aw backlog): Records-mutating commands (aw archive, and likely group/rename/research regroup) should offer to commit their own path-scoped changes when run interactively

When a records-mutating verb (starting with 'aw archive', and probably its siblings 'aw group', 'aw rename', 'aw research set-assign/mv', 'aw ipd set', 'aw specs set') moves/renames files and regenerates an INDEX, it currently leaves the resulting changeset uncommitted. The user then has to notice and hand-commit a large, coherent set of renames + index updates (e.g. the 23-file 'aw archive' research changeset). Instead, when run interactively (a TTY), the command should PROMPT to commit the change it just made, and on yes create a path-scoped commit of ONLY the files it changed (the moved/renamed paths plus the regenerated index), never 'git add -A'/'-a', never push, with a descriptive default message. Requirements/constraints: (1) commit ONLY files the command itself touched - track them explicitly rather than committing whatever is dirty; (2) interactive-only by default (TTY): non-interactive/CI runs must NOT auto-commit unless an explicit flag like --commit is passed, and there should be a --no-commit escape hatch; (3) respect the repo contract (path-scoped, no push, no hook bypass); (4) if the tree already has unrelated staged/unstaged changes, do not fold them in - stage only this command's own paths; (5) a good default commit message per verb (e.g. 'chore(research): archive aged artifacts and regenerate index'). Evaluate whether this belongs as shared plumbing in a single 'commit-what-I-changed' helper reused by all records-mutating verbs. Origin: user request after 'aw archive' left a 23-file research changeset uncommitted.
