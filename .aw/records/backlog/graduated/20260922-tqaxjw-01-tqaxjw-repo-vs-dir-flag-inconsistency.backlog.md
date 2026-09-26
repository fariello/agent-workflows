- Id: tqaxjw
- Status: graduated
- Graduated-To: runsrepo
- Set: tqaxjw
- Priority: low
- Work-Kind: chore
- Summary: aw oc run takes --repo while aw runs takes --dir for the same repository root, so a copy-pasted invocation fails

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into plan 8y13kn (Set runsrepo), re-verified live at HEAD.
- 2026-09-22 created (aw backlog): Filed by aw oc run while executing plan zyw4n3.

MEASURED 2026-09-22 while executing plan `zyw4n3`, writing an end-to-end validation script that runs `aw oc run` and then inspects the run it just made with `aw runs`.

WHAT IS WRONG. The two commands spell the SAME concept, the target repository root, with DIFFERENT flags:

    $ aw oc run start --help
      --repo REPO           Target Git repository root (default: current ...
    $ aw runs --help
      --dir DIR             Target Git repository root (default: current directory).

The help TEXT is word-for-word identical ("Target Git repository root"), so this is one concept with two names rather than two concepts. Consequently the obvious next command after a run fails:

    $ aw runs run-20260922T093150Z-3668798 --repo /path/to/repo
    aw runs: error: unrecognized arguments: --repo /path/to/repo

WHY IT MATTERS. `aw oc run`'s own closing footer tells the operator to run `aw runs <run-id>` for more info, and an operator working on a repository that is not the current directory will naturally carry `--repo` across, because that is the flag they just used. The failure is immediate and recoverable, so this is low priority, but it is exactly the kind of avoidable surface friction a consistent CLI removes. It also bites a SCRIPT: my validation script had to be corrected after hitting it.

POSSIBLE FIX: accept `--repo` as an alias of `--dir` on `aw runs` (and vice versa where absent), which is backward compatible in both directions, rather than renaming either flag and breaking existing invocations.

WHERE: the `aw runs` argument parser (`agent_workflows/run_viewer.py`'s CLI) versus the shared runner flag table used by `aw oc run start`.
