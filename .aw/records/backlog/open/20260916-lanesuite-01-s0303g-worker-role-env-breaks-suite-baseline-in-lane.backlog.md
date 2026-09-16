- Id: s0303g
- Status: open
- Set: lanesuite
- Priority: medium
- Work-Kind: bug
- Summary: AW_EXECUTION_ROLE=worker in a lane makes 19 suite tests fail, so a worker cannot get a trustworthy bare-suite baseline

## Workflow history
- 2026-09-16 created (aw backlog): Found while executing dirtygates Order 01 (d7qoxv) in an isolated lane.

MEASURED 2026-09-16 in lane `aw/lane/d7qoxv_attempt2` at commit 4350ebc, BEFORE any edit.

A bare `python3 -m pytest` inside a runner-launched lane reports `19 failed, 7290 passed`. Unsetting one variable makes the same tree at the same commit report `7309 passed, 3 skipped, 2 xfailed`, zero failures:

    $ python3 -m pytest                              -> 19 failed, 7290 passed
    $ env -u AW_EXECUTION_ROLE python3 -m pytest     -> 7309 passed, 0 failed

The failures are all lifecycle/integration tests that invoke `aw ipd begin`/`finalize` in a fixture repository (`test_ipd_lifecycle_cli`, `test_worker_role_refusal`, `test_oc_runipd` and `test_agy_runipd_cli` worktree/integration classes, `test_novalnomerge_integration`). The refusal text is the expected one: `AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process must not run them`. So the guard is working as designed on the PRODUCT path; the problem is that it also fires for tests that legitimately drive the lifecycle inside a throwaway fixture repo, because the selector is inherited from the process environment.

WHY IT MATTERS, and it is not cosmetic. Every plan's validation section asks the executor to compare a full-suite failure set against a baseline from the same commit. In a lane the honest bare baseline is 19 red, so an executing agent must either (a) notice the cause, (b) mistake them for pre-existing repository breakage and reason from a polluted baseline, or (c) mistake them for damage IT caused and start chasing them. This turn hit exactly that and had to establish the cause before it could trust any measurement.

POSSIBLE SHAPES, not a decision: have the affected tests neutralize the selector for their own fixture subprocesses (most surgical, keeps the product guard fully armed); or have the role check ignore a repo it can see is not the managed checkout; or document the `env -u` workaround in the execution contract so every executor knows. The first looks right, since the tests own their fixture repositories and the guard should stay armed everywhere else.
