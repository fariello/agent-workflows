# IPD: Start the cutover code patch with the log-format loader and writer switch

- Date: 2026-11-09
- Kind: child
- Concern: The attended cutover `cxxmyv` wrote the whole code switch to the log format inside one attended turn (its task group 2: E-03, E-04, E-07, E-16). Spec `4sd62s` 5.2 makes the cutover ONE commit and C10a forbids a second on-disk format on `main` before it, so the switch cannot land early. It CAN be prepared early as an inert patch file, exactly as `90iqr1` prepares the documentation: a `.patch` file changes no on-disk format and no behavior until `cxxmyv` applies it. This plan (round-3 split, research `nj8zdp`) starts that cumulative code patch with `cxxmyv` E-03 and adds the guard test that keeps it applying.
- Scope: In a scratch worktree (docs patch applied as the base), switch `artifact_meta`'s loader and writer to the log format, move the legacy loader into the new `m0001` migration module, delete the legacy write path and set the schema to 2; write the result as `.aw/system/cutover/metastore-code.cutover.patch`; add the core guard test. No live code changes.
- Scope-Paths: .aw/records/plans/pending/20261109-metastore-255-2k5t16-start-the-cutover-code-patch-with-the-log-format-loader-and.ipd.md, .aw/system/cutover/metastore-code.cutover.patch, tests/test_metastore_cutover_code_patch.py
- Item-Dependencies: executed:1ajqaa, executed:87rvs2, executed:90iqr1, executed:aqc3m6, executed:clors0, executed:dcerjg, executed:g5hpbb, executed:iog3cw, executed:rdg0qv, executed:w13bkp, executed:ya4ee4, executed:zgyna1
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 255
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2k5t16

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from cxxmyv (round 3, research nj8zdp guidance).

## Goal

Produce the first version of an inert, guarded patch that switches the toolkit's metadata loader and writer to the event-log format, so `cxxmyv` applies it inside the one cutover commit instead of writing it during the attended turn.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scratch worktree

- [ ] E-01 Create the scratch worktree and its base, per the procedure in Step 0: `git worktree add --detach .aw/state/2k5t16/scratch HEAD`; inside it, `git apply --index .aw/system/cutover/metastore-docs.cutover.patch`, then record the base tree with `git write-tree` in F-01. No code patch exists yet, so there is nothing else to apply.
  - Depends on: none
  - Expected outcome: the scratch worktree holds HEAD plus the documentation patch, staged; F-01 holds the base tree id.
  - Execution state: pending

### Task group 2: the switch (scratch worktree only; was `cxxmyv` E-03, in three steps)

- [ ] E-02 In `agent_workflows/artifact_meta.py`, switch the loader and writer to the log format: `artifact_meta.append` and `artifact_meta.create` write `meta/<id6>.jsonl` with the spec 4.3 write order (log, in-file mirror, disposition, cache), and the loader reads logs.
  - Depends on: E-01
  - Expected outcome: a fixture setter run writes the log and then the mirror.
  - Execution state: pending

- [ ] E-03 Move the legacy (bullet-block) loader unchanged out of `agent_workflows/artifact_meta.py` into the new module `agent_workflows/migrations/m0001_metadata_v2.py`, and point every legacy-loader caller inside the migration at it.
  - Depends on: E-02
  - Expected outcome: the legacy loader exists only in `m0001_metadata_v2.py`.
  - Execution state: pending

- [ ] E-04 Delete the legacy write path: the legacy branch of `artifact_meta.append` with `artifact_meta.LegacyRender` and the path-keyed target (`2xwb9b`); switch `write_legacy` off and remove the value writers that `9o83cr` E-08 folded into it (`xexn45`, `9o83cr`); set `chain.CURRENT_METADATA_SCHEMA` to 2 (`dcerjg`).
  - Depends on: E-03
  - Expected outcome: no module outside `artifact_meta.py` (log format only) and `migrations/m0001_metadata_v2.py` can produce a bullet block or a `## Workflow history` line.
  - Execution state: pending

### Task group 3: package and guard

- [ ] E-05 In the scratch worktree run `git add -A` and write `git diff --cached --binary <F-01 base tree>` to `.aw/system/cutover/metastore-code.cutover.patch` in the executing checkout; remove the scratch worktree (`git worktree remove --force .aw/state/2k5t16/scratch`). Add `tests/test_metastore_cutover_code_patch.py` (marked `core`): on a temporary `GIT_INDEX_FILE` filled by `git read-tree HEAD`, it runs `git apply --cached` of the docs patch and then `git apply --cached --check` of the code patch, and asserts both exit 0. It reads and applies the two patches; it does not read production source. Commit through `aw commit 2k5t16 -- <this plan> .aw/system/cutover/metastore-code.cutover.patch tests/test_metastore_cutover_code_patch.py`; never push.
  - Depends on: E-04
  - Expected outcome: the code patch exists and touches only the E-02 to E-04 files; the guard test passes on HEAD and fails if either patch stops applying.
  - Execution state: pending

## Project conventions discovered (Step 0)

- SCRATCH PROCEDURE shared by the four code-patch parts (`2k5t16`, `g45vyv`, `x1mmdp`, `0zylig`): (1) `git worktree add --detach .aw/state/<id6>/scratch HEAD` (gitignored state root, `90iqr1` OQ-03); (2) in it, `git apply --index` the docs patch, then `BASE=$(git write-tree)`; (3) if the code patch exists, `git apply --index` it; (4) edit; (5) `git add -A` and `git diff --cached --binary $BASE` over the code patch; (6) `git worktree remove --force`. The code patch is therefore relative to HEAD plus the docs patch, and `cxxmyv` applies the docs patch first, then the code patch. No scratch commit is made.
- C10a and spec 5.2: an inert patch file under `.aw/system/cutover/` changes no on-disk metadata format; `cxxmyv` applies and deletes it inside the cutover commit.
- Placing the patch under `.aw/system/` ships it in the wheel and sdist (`90iqr1` E-09); `cxxmyv` deletes it at the cutover.
- Tests exercise code and assert on outcomes; applying a patch is an outcome test.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | (written by E-01) | Base tree id of the scratch worktree (HEAD plus docs patch). |
| F-02 | `rg -n "class LegacyRender\|def append\b\|def create\b" agent_workflows/artifact_meta.py` (2026-11-09) | `LegacyRender`, `append` and `create` exist in `artifact_meta.py`; `agent_workflows/migrations/` does not exist yet at this HEAD (it is created by `dcerjg` or by E-03 here, whichever is first; re-check at execution). |

## Proposed changes (ordered, validatable)

1. E-01: scratch worktree with the docs patch as base.
2. E-02 to E-04: the loader and writer switch in three steps.
3. E-05: write the code patch, add the guard test, commit.

## Deferred / out of scope (with reason)

- Applying the code patch: inside the one cutover commit.
  - Carrier: cxxmyv
- Log-only writers and ledger retirement (`cxxmyv` E-04).
  - Carrier: g45vyv
- Test builder switch (`cxxmyv` E-07).
  - Carrier: x1mmdp
- `Kind` option renames (`cxxmyv` E-16).
  - Carrier: 0zylig

## Scope check

- Over-scope: none. No live code changes.
- Under-scope: none. `cxxmyv` E-03 maps to E-02 (loader, writer), E-03 (legacy loader move) and E-04 (legacy write path, schema).

## Required tests / validation

- The new guard test (E-05); fixture setter runs in the scratch worktree (V-02, V-04).

## Spec / documentation sync

No spec change. Spec 5.2 and C10a are kept: nothing here changes `main`'s format.

## Open questions

### OQ-01: Is preparing the code switch as a patch allowed by spec 5.2 and C10a?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. C10a requires `main` to read exactly one format at every commit; an unapplied patch file is data, not code that runs, so `main` still reads only the legacy format until `cxxmyv`'s single commit applies it. It is the same design `90iqr1` OQ-01 uses for the documentation. Recommendation strength: strong. RESOLVED 2026-11-11 by the user via /askme: accept the patch design (the code switch is prepared in advance as an unapplied patch and applied at the attended cutover). No reason was given.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git worktree add` and `git apply --index` commands with exit status 0, and the base tree id recorded in F-01.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a behavioral fixture test run in the scratch worktree (pytest output with PASSED lines) showing `append` and `create` write `meta/<id6>.jsonl` and then the in-file mirror.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git diff --cached --stat` in the scratch worktree showing the legacy loader removed from `artifact_meta.py` and added to `migrations/m0001_metadata_v2.py`, and `rg -n` of the legacy loader's function name over `agent_workflows/` showing its definition only in `m0001_metadata_v2.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n 'LegacyRender|write_legacy' agent_workflows/` in the scratch worktree (no definition left), the diff hunk setting `CURRENT_METADATA_SCHEMA = 2`, and a fixture test run showing no setter run on a log-format fixture leaves a bullet block or a `## Workflow history` line in the file. The repository-wide AC-1 audit is `cxxmyv`'s.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-code.cutover.patch` (file list), `python3 -m pytest -o addopts="" -v tests/test_metastore_cutover_code_patch.py` with each test PASSED, the same run after corrupting one hunk of a scratch copy of the code patch showing FAILED, `git worktree list` showing the scratch worktree removed, and the `aw commit` output naming the commit hash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after every plan in `- Item-Dependencies:` is `executed` and this plan is `approved`. Code is edited ONLY in the scratch worktree; the executing checkout changes only by this plan, the code patch and the guard test.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Honesty rule: paste the ACTUAL output of every command named above; never claim a result you did not run.

Commits: commit only through `aw commit 2k5t16 -- <paths>`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
