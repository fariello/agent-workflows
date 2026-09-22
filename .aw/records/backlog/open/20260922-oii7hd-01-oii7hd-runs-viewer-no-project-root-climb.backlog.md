- Id: oii7hd
- Status: open
- Blocks-Release: next
- Set: oii7hd
- Priority: medium
- Work-Kind: bug
- Summary: run_viewer_cli reads args.dir directly instead of resolve_verb_repo_root, so aw runs cannot see a run from a subdirectory

## Workflow history
- 2026-09-22 created (aw backlog): run_viewer_cli reads args.dir directly instead of resolve_verb_repo_root, so aw runs cannot see a run from a subdirectory

FOUND WHILE EXECUTING `d91i3e` (runrecon Order 01), whose finding F-15 axis (c) asserts the
OPPOSITE and is now stale.

WHAT IS WRONG. `run_viewer_cli` resolves its repo root as

    repo_root = Path(getattr(args, "dir", None) or ".")

so with no `--dir` it resolves against the CURRENT DIRECTORY and never climbs to the project root.
`agent_workflows/project_context.py::resolve_verb_repo_root` exists precisely to do that climb, and
its own docstring says a verb using it "works from any subdirectory, git-style". `aw runs` does not
use it. Consequence, measured at HEAD 23dfbf2d from a subdirectory of a repo holding a real driver
run:

    $ cd <repo>/sub
    $ aw runs show <run-id>    -> exit 2, cannot find the run
    $ aw runs repair <run-id>  -> exit 2, `error: no run matched target '<run-id>'`

Both fail. `state_root(Path("."))` from that subdirectory resolves to a project context derived from
the SUBDIRECTORY, i.e. a wholly different records root, so `discover_run_dirs` returns zero runs.

WHY IT MATTERS. Every other repo-scoped `aw` verb works from any subdirectory; `aw runs` silently
does not. The failure is not an error explaining the situation, it is an ordinary
"no run matched target", so an operator in `tests/` or `docs/` is told their run does not exist.
That is the same class of misleading refusal that backlog `zrzfkw` and `sv8z1e` were filed for on
the adjacent ledger-reader surface.

IT ALSO CORRECTS A RECORD, which is the second reason to file rather than to fix in passing. Plan
`d91i3e`'s F-15 axis (c) states that the viewer path "CLIMBS to the project root via
`resolve_verb_repo_root` (`project_context.py:314-327`)" and that from `tests/`
`aw runs repair <id>` SUCCEEDS while `aw runs show <id>` refuses. Re-measured at 23dfbf2d, that is
FALSE: `run_viewer_cli` performs no climb and both commands refuse. The divergence between the two
resolvers is real but lives in their ROOT SETS (axis (a): the ledger reader searches
`.aw/state/runs/`, `discover_run_dirs` does not), not in climbing. `d91i3e`'s own implementation is
unaffected because its detector ASKS the viewer's resolver rather than modelling it, and its V-02
evidence records this correction; but the stale claim would mislead the next reader of that plan or
of its sibling `fduoj4`.

SUGGESTED FIX, not prescribed. Route `run_viewer_cli`'s root through `resolve_verb_repo_root`
(honoring an explicit `--dir` verbatim, which that helper already does), making `aw runs` behave
like every other repo-scoped verb. NOTE THE COUPLING before doing it: the ledger readers in
`run_cli.py` resolve against `Path.cwd()` and would then disagree with the viewer in the OTHER
direction, which is exactly the open question `d91i3e` OQ-02 left for the maintainer ("should the
ledger readers ALSO climb?"). So the honest scope is BOTH surfaces or a deliberate decision to
leave one behind, not a one-line change to the viewer alone.
