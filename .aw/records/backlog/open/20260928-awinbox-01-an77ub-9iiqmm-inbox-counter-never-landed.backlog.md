- Id: an77ub
- Status: open
- Blocks-Release: next
- Set: awinbox
- Priority: high
- Work-Kind: bug
- Summary: Plan 9iiqmm is executed and its backlog item closed done, but its inbox-counter implementation never landed: both declared Scope-Paths carry zero inbox references on main and the code survives only in unreachable dangling git objects

## Workflow history
- 2026-09-28 created (aw backlog): Filed at authoring of plan dv7c49 (from backlog 3sh9d6), which found this while verifying which artifacts carry 3sh9d6's stale non-TTY claim. Filed now rather than left to the executor because check.ipd-uncarried-obligation is error-severity and refuses a - Carrier: naming a non-resolving id6.

WHAT IS WRONG. Plan `9iiqmm` (`.aw/records/plans/executed/20260908-awinbox-02-9iiqmm-count-waiting-aw-inbox-drops-in-aw-attention-by-listing-the.ipd.md`) sits in `executed/` with `- Status: executed`, a self-finalize history record, and `V-*` blocks pasting test output said to be PASSING. The feature it describes, an advisory footer line in the `aw attention` human board counting raw drops waiting in `.aw/inbox/`, DOES NOT EXIST IN THE TREE. Its backlog item `plbkp5` is closed `done` on that basis.

MEASURED 2026-09-28 in a lane worktree at base `bc7015e0`, each with the command that produced it:

1. Neither declared Scope-Path carries the work. `9iiqmm` declares `- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py`.

        $ git show main:agent_workflows/attention.py | grep -c inbox
        0
        $ git show main:tests/test_attention.py | grep -c inbox
        0

2. It is absent behaviorally, not only by grep. Against a temp repo whose `.aw/inbox/` holds four files:

        $ AW_NO_REEXEC=1 python3 -m agent_workflows attention --dir <tmp> | cat
        ## ready (1)
        - [plans] .agents/plans/pending/20260920-demo-01-aaa111-demo.md (draft)
        1 artifact shown

   No footer line. Compare the board the plan's own V-02 pastes, which includes `TODO: 4 files waiting in .aw/inbox/. Run aw adopt <path> to file one.`

3. The footer string exists in no reachable commit, ever.

        $ git log --all --oneline -S'waiting in `.aw/inbox/`' -- '*.py'
        (no output)

4. The test classes whose PASSING output the plan's V-01 and V-02 paste do not exist.

        $ grep -rn "InboxWaitingCountTests\|InboxFooterNudgeTests" tests/
        (no match)

5. The merged lane carried no code. Lane commit `1a011e17` and integrate commit `881607b6` ("integrate(aw oc run): merge verified lane 9iiqmm to main") touch only records files:

        $ git diff --stat bb714fd8..1a011e17 -- agent_workflows/attention.py tests/test_attention.py
        (empty)

RECOVERY HANDLES, AND WHY THEY ARE URGENT. An exhaustive scan of all 19224 blobs in the object store (`git cat-file --batch-all-objects --batch-check`) found the implementation, in UNREACHABLE objects only. `git log --all --find-object` reports ZERO reachable commits introducing either blob.

- blob `9effdcef169e7ad8eafc0c3b22f5432cf1384dc6` (138154 bytes) = `agent_workflows/attention.py` carrying the counter and the line `f"TODO: {waiting} {noun} waiting in \`.aw/inbox/\`. Run \`aw adopt <path>\` to file one."`
- blob `de2fbe7ceb1918551ea8f03fc0e8467f056119be` (114999 bytes) = `tests/test_attention.py` asserting both `1 file waiting` and `2 files waiting`
- dangling commits holding them: `5c55d0200686cc090338d07fe22b795970924883`, `888c20a162006ca91f6c2aa741692e85d319ee71` (both "WIP on aw/lane/9iiqmm"), and `3569ed071d9a03a5b6805fb4601ec44357683c99` ("WIP INTERRUPTED SNAPSHOT (not finished work): lane 9iiqmm")

Extract with `git cat-file blob <sha>`; do NOT expect a branch. DANGLING OBJECTS ARE `git gc`-PRUNABLE, so these shas are the difference between recovering the work and rewriting it. Do not run `git gc` before this item is resolved.

WHY `bug` AND WHY IT GATES THE RELEASE. The user-perceptible symptom is that a feature recorded as shipped, with its backlog item closed, does not run at all; that is a defect and not a chore, and per AGENTS.md a LIVE item whose work-kind is in the gating set must carry `- Blocks-Release:`. The gate is on the RECORD being false as much as on the missing line: a reader who trusts `executed` plus `done` is misled about what this repository does.

TWO THINGS THIS ITEM DOES NOT DECIDE. FIRST, whether to re-land the recovered blob as-is. `3569ed07` calls itself "not finished work", the pasted V-evidence is not trustworthy given the same record claims an execution that did not land, and three design questions the original review raised are live: the `README.md`/`.gitkeep` exclusion (that plan's F-11), singularization of a count of one (F-14), and whether the count should reach the `--agent`/`--json` surface (its OQ-04, whose severity-blind `findings` cost is independent and still true). A re-implementation needs its own review. SECOND, the SYSTEMIC question of how a lane merged, self-finalized, and closed its item while its declared Scope-Paths carried no change. That is a runner investigation needing measurement across runs, and this item reports one instance with evidence rather than diagnosing it.

RELATED. The stale non-TTY claims in the same plan and its review are backlog `3sh9d6`, corrected by plan `dv7c49` (which files this item). Those are a prose defect; this is lost code, and they are deliberately kept separate.
