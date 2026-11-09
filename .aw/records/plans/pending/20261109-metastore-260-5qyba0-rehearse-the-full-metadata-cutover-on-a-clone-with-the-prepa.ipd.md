# IPD: Rehearse the full metadata cutover on a clone with the prepared patches

- Date: 2026-11-09
- Kind: child
- Concern: `cxxmyv` E-17 rehearsed the whole cutover on a clone during the attended turn, after the code switch had been written there. With the switch now prepared as the docs and code patches (`90iqr1` family and `2k5t16` family) and the demonstrations as a script (`33vxoi`), the rehearsal can run BEFORE the attended cutover turn, on a `git clone --no-hardlinks` copy, without touching this checkout or `main` (spec `4sd62s` 5.2, C10a). It proves the one-commit mechanism (`clors0` E-19 extra-path argument) on a full copy, and rehearses the demonstration script on a migrated tree. Round-3 split, research `nj8zdp`.
- Scope: In a gitignored clone of the maintainer's main checkout: apply both patches, copy the sidecar and the description journal, run both test tiers on the switched unmigrated tree, run `aw migrate metadata --apply` without `--force` with the extra-path argument, check the one commit and both tiers, run the demonstration script; record the exact invocation for `cxxmyv`. Edits only this plan.
- Scope-Paths: .aw/records/plans/pending/20261109-metastore-260-5qyba0-rehearse-the-full-metadata-cutover-on-a-clone-with-the-prepa.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:87rvs2, executed:90iqr1, executed:aqc3m6, executed:clors0, executed:dcerjg, executed:g5hpbb, executed:iog3cw, executed:rdg0qv, executed:w13bkp, executed:ya4ee4, executed:zgyna1, executed:tub3ir, executed:0zylig, executed:33vxoi
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Attended: required
- Set: metastore
- Order: 260
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 5qyba0

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from cxxmyv (round 3, research nj8zdp guidance).

## Goal

Prove, on a full copy of this repository and before the attended turn, that the prepared patches plus `aw migrate metadata --apply` produce ONE commit that passes every hook and both test tiers, and that the demonstration script runs on the migrated tree; hand `cxxmyv` the exact invocation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: prepare the clone

- [ ] E-01 In the maintainer's main checkout, record `git status --porcelain | sha256sum` in F-01, then `git clone --no-hardlinks` it to the gitignored `tmp/cxxmyv-rehearsal`. In the clone, apply `.aw/system/cutover/metastore-docs.cutover.patch` and then `.aw/system/cutover/metastore-code.cutover.patch` with `git apply` (working tree only, not committed), delete the two patch files, `tests/test_metastore_cutover_patch.py` and `tests/test_metastore_cutover_code_patch.py` (as `cxxmyv` E-08 does), and copy the history sidecar and the `tub3ir` description journal into the clone so no new model call is made.
  - Depends on: none
  - Expected outcome: the clone holds the switched, patched, unmigrated tree with the sidecar and journal; this checkout is untouched.
  - Execution state: pending

### Task group 2: rehearse

- [ ] E-02 In the clone, rehearse `cxxmyv` E-09 on the switched, unmigrated tree: run the bare core gate and `make test-all`; the only allowed failures are the tests `x1mmdp` F-03 lists ("run `aw migrate metadata`" refusals). Then run `aw migrate metadata` (dry run). Any other failure or a census refusal stops here: report it as a defect in the patch-writing plan that owns the failing file.
  - Depends on: E-01
  - Expected outcome: both tiers pass except the listed refusals; the dry run is clean.
  - Execution state: pending

- [ ] E-03 In the clone, run `aw migrate metadata --apply` without `--force`, passing the task group 2 paths (every file the two patches touched or deleted) through the `clors0` E-19 extra-path argument (spec 5.2 step 7 as amended there), and let the migration's one `aw commit --no-plan` run through every installed hook. If the docs patch's hunks under `.aw/records/` (the records READMEs) trip the uncommitted-records preflight, find a form that needs no `--force`. Stop condition: if no form produces ONE commit containing both the migration and the patched paths without `--force` and without `--no-verify`, stop and report to the maintainer; do not write a new mechanism. Record the exact invocation in F-02.
  - Depends on: E-02
  - Expected outcome: one commit holds the migrated records and every patched path and passes every installed hook; F-02 holds the invocation.
  - Execution state: pending

- [ ] E-04 In the clone, on the migrated commit, run the bare core gate and `make test-all` (0 failed), then `bash .aw/system/cutover/metastore-acceptance-demo.sh` from this checkout against the clone (`all` section, with the `tub3ir` F-02 before values) and record each criterion's pass or fail in F-03. A failing criterion is reported against the plan that owns it; it does not stop this plan unless the script itself is broken (then report against `33vxoi`).
  - Depends on: E-03
  - Expected outcome: both tiers pass on the migrated clone; F-03 has one row per criterion.
  - Execution state: pending

### Task group 3: clean up

- [ ] E-05 Delete the clone and every demo clone the script made; confirm `git status --porcelain | sha256sum` of this checkout equals F-01; commit this plan's findings through `aw commit 5qyba0 -- <this plan>`; never push.
  - Depends on: E-04
  - Expected outcome: no clone remains; this checkout is unchanged apart from this plan; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The sidecar lives only in the main checkout (spec 5.2 step 1, 3c), so this plan is `Attended: required` and runs there; all mutation happens in the clone.
- The step-1 preflight refuses uncommitted change under `.aw/records/` (`dcerjg` E-04 condition (2)); E-03 must show a form that passes it.
- `cxxmyv` Step 0 records that the one-commit mechanism is proven only by this rehearsal (its review's named feasibility risk).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | (written by E-01) | `git status --porcelain | sha256sum` of this checkout before the rehearsal. |
| F-02 | (written by E-03) | The exact `clors0` E-19 extra-path invocation that puts the migration and the patched paths in one commit. `cxxmyv` E-10 uses it. |
| F-03 | (written by E-04) | Per-criterion result of the demonstration script on the migrated clone. |

## Proposed changes (ordered, validatable)

1. E-01: clone with both patches, sidecar and journal.
2. E-02 to E-04: pre-migration tiers, the apply and its one commit, post-migration tiers and demo script.
3. E-05: clean up and commit findings.

## Deferred / out of scope (with reason)

- The real migration and the one cutover commit in this checkout (spec 5.2, C10a).
  - Carrier: cxxmyv

## Scope check

- Over-scope: none.
- Under-scope: none. `cxxmyv` E-17 maps to E-01, E-03, E-04 and E-05; E-02 adds an early rehearsal of `cxxmyv` E-09, which `cxxmyv` still runs for real.

## Required tests / validation

- Both tiers twice in the clone, the migration apply, the demo script (V-02 to V-04).

## Spec / documentation sync

No spec change. If F-02 shows the spec 5.2 step 7 text (amended by `clors0` E-19) is incomplete, stop and report rather than amend.

## Open questions

None open.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste F-01, the clone command line, both `git apply` commands with exit 0, `git -C tmp/cxxmyv-rehearsal status --short | wc -l`, and `ls -l` of the copied sidecar and journal in the clone.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the core gate and `make test-all` summary lines in the clone with each failing node id listed beside its `x1mmdp` F-03 row, and the dry-run result line showing no census refusal.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `aw migrate metadata --apply` output (no `--force`), the commit output with every hook result, `git show --stat` listing the migrated records and the patched paths in one commit, and F-02 as written.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the core gate and `make test-all` summary lines on the migrated clone with 0 failed, and F-03 with one row per AC label the script printed.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `ls tmp/` showing no rehearsal or demo clone, the after `git status --porcelain | sha256sum` equal to F-01, and the `aw commit` output naming the commit hash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only with the maintainer present, in the main checkout that holds the history sidecar, after every plan in `- Item-Dependencies:` is `executed`. The runner must not dispatch this plan unattended (`- Attended: required`). Never pass `--force` or `--no-verify`.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`).

Honesty rule: paste the ACTUAL output of every command named above; never claim a result you did not run.

Commits: in this checkout, commit only through `aw commit 5qyba0 -- <this plan>`; never push.

Lifecycle: the attending executor runs `aw ipd finalize 5qyba0` after every `V-*` is `pass`; never `git mv` the plan by hand.
