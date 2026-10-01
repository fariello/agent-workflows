- Id: rgl2d4
- Status: open
- Blocks-Release: next
- Set: dirsilent
- Priority: medium
- Work-Kind: bug
- Summary: The other ~35 resolve_verb_repo_root callers fall back silently for a non-surveyable --dir: specs check and backlog check report conformance having examined ZERO artifacts at a project subdirectory

## Workflow history
- 2026-09-30 created (aw backlog): Filed while authoring plan lmyeas (from backlog 5gmi12), which scoped this but deliberately converted only the two verbs that already guard.

MEASURED in lane 5gmi12 at HEAD 950ae59ff while authoring IPD lmyeas (its F-03 and F-09), from a cwd OUTSIDE any AW project, fixtures under a temp dir, via 'python3 -m agent_workflows' with PYTHONPATH=<lane> and AW_NO_REEXEC=1.

REPRODUCTION, in a temp project holding one open backlog item and one spec, where <deep> is <root>/src/deep:
  aw find backlog  --dir <root>  -> lists the item                              exit 0
  aw find backlog  --dir <deep>  -> lists NOTHING                               exit 0
  aw specs check   --dir <root>  -> 'all specs conform. 1 specs checked.'       exit 0
  aw specs check   --dir <deep>  -> 'all specs conform. 0 specs checked.'       exit 0
  aw backlog check --dir <deep>  -> 'all backlog items conform.'                exit 0

WHY THIS IS A BUG AND NOT MERELY AN EMPTY ANSWER: 'specs check' and 'backlog check' are FAIL-CLOSED VALIDATORS. Announcing conformance having examined ZERO artifacts is the Anti-Greenwashing Invariant violation docs/cli-output-contract.md names outright ('A record MUST NEVER report a positive outcome for work that was skipped, partial, unverified, or cannot-run'), and these are exactly the surfaces a CI step calls. A human reading 'all specs conform' has no signal that nothing was checked.

ROOT CAUSE, the same one as backlog 5gmi12: resolve_verb_repo_root honors an explicit --dir VERBATIM with no climb, while a bare invocation climbs via find_project_root. Only 'aw attention' and 'aw ipd board' pair the resolver with is_project_dir and emit guidance; every other caller takes the cwd/verbatim fallback SILENTLY. That gap is already recorded in resolve_verb_repo_root's own docstring, which explicitly declines to settle whether all the silent callers should guide.

WHAT IS ALREADY DONE AND WHAT REMAINS: plan lmyeas (from 5gmi12) DECIDES the resolution rule (verbatim, never climb, because ~19 of the resolver's 37 invocations are WRITE-class, one is a shutil.rmtree, and $HOME is itself commonly a project root) and ADDS the shared three-way classifier (is-a-root / inside-a-project-naming-that-root / in-no-project) that these verbs need. It converts only 'attention' and 'ipd board'. WHAT REMAINS HERE is adopting that classifier at the remaining callers.

START WITH THE TWO VALIDATORS: specs.run_check and backlog.run_check are the highest-value conversions because they are fail-closed gates whose false 'conform' is the most dangerous output in the set.

A PREREQUISITE THE CONVERSION MUST HANDLE, measured in lmyeas F-04: several call sites are SHARED HELPERS serving read AND write verbs through ONE resolve call (releases._release_repo_root, research_archive._roots, research_refs._repo_root, plans_index._dirs, prompts_index._dirs, research_index._roots). A per-verb READ/WRITE policy cannot even be EXPRESSED until those helpers are split, so the split is part of this work rather than a surprise during it.

DO NOT 'FIX' THIS BY CLIMBING. lmyeas decided against it with measured evidence; a climb would retarget worktree allocation, git_mv, lifecycle moves and a recursive delete at an ancestor project, and the climb target can be $HOME or (from a runner lane) the shared checkout. The correct remedy is refuse-and-name-the-root, the shape backlog.run_set's --gate-dir branch already uses.

SUB-CASE, doctor.run RESOLUTION DRIFT (lmyeas F-09): 'aw doctor' reads --dir but BYPASSES the resolver entirely with its own 'Path(getattr(args,"dir",None) or os.getcwd())'. So it neither climbs from cwd like its siblings nor inherits any decision recorded at the resolver, and it will silently drift from every sibling verb as they are converted. Route it through resolve_verb_repo_root as part of this work.
