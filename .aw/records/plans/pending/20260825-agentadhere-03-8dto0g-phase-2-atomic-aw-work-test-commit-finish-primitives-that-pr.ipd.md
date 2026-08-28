# IPD: Phase 2: atomic aw work/test/commit/finish primitives that produce evidence at the action boundary

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 2 + section 4.3/7.4: reliable adherence requires replacing a sequence of remembered duties with a smaller number of atomic actions that make the compliant path the EASY path and produce evidence at the action boundary. Today the workflow is a chain of separate remembered steps (start work, run tests, commit path-scoped, finalize), each an independent failure opportunity. There is no `aw work`/`aw test`/`aw commit`/`aw finish` wrapper that validates-then-acts and captures evidence.
- Scope: Add atomic workflow primitives (findings 7.4), each validating before mutating and calling the phase-1 `aw check` engine: (1) `aw work begin <ipd>` - validate the plan and create/associate an isolated worktree; (2) `aw test <ipd> -- <cmd>` - execute the test, capture stdout/stderr + exit + env metadata, bind evidence to the tree/commit; (3) `aw commit <ipd> -- <paths>` - compute allowed paths, refuse out-of-scope staged changes, run the checker, commit ONLY declared scope (REUSE the selfcommit `git_commit_helper` - no forked commit path); (4) `aw finish <ipd>` - check required evidence and perform valid non-authoritative transitions. Raw actions either blocked (where interception is reliable) or caught by a later deterministic failure; the wrapper must be the faster path. This child builds the primitives + their evidence capture; it does NOT build event-derived state (phase 3), hooks (phase 4), or CI (phase 5). Honest limit: local evidence is forgeable by a privileged local agent (findings 6.6); CI reproduction (phase 5) is the High-confidence boundary.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/work_cmd.py, agent_workflows/git_commit_helper.py, agent_workflows/worktree_lease.py, agent_workflows/ipd_lifecycle.py, tests/
- Status: approved
- Set: agentadhere
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 8dto0g
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 approved (aw set): status set to approved

- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 gate execution contract added, PR-002 V-01..V-04 concrete falsifiable evidence, PR-003 split 2 E-items into 4 (one per primitive) for conceptual density, PR-004 OQ-01 resolved + sequencing MUST, PR-005 Status draft->reviewed
- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add atomic `aw work begin` / `aw test` / `aw commit` / `aw finish` primitives that validate-then-act via the phase-1 engine and capture evidence at the action boundary, making the compliant path the easy path. `aw commit` reuses the selfcommit path-scoped helper.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: work

- [x] E-01 Add `aw work begin <ipd>`: validate the plan via the phase-1 `aw check` engine (fail closed on findings) and create/associate an isolated worktree via `worktree_lease.allocate_worktree` + `LeaseTable`. Reuse the existing lease/worktree machinery (worktree_lease.py:70,144); do not fork a second worktree path.
  - Depends on: none
  - Expected outcome: `aw work begin <ipd>` on a clean, eligible plan validates it and allocates/associates an isolated worktree with a recorded lease; on a plan with `aw check` findings it fails closed and prints the findings.
  - Execution note: `work_cmd.run_work_begin` validates the plan via `check_engine.check_type(repo_root, "plans")` filtered to the plan (advisory info-severity nudges excluded) and fails closed on any blocking finding; on success it calls `worktree_lease.allocate_worktree` (the SHARED machinery, no second path) and writes a lease JSON under the gitignored `.aw/state/work/<id6>/`.
  - Execution state: performed

### Task group 2: test

- [x] E-02 Add `aw test <ipd> -- <cmd>`: execute `<cmd>`, capture stdout, stderr, exit code, and env metadata (command line, cwd, timestamp, git HEAD/tree of the worktree), and bind that evidence record to the tree/commit under the plan's run-record location. Honestly label the evidence as locally-produced and forgeable by a privileged local agent (findings 6.6); non-forgeable/CI-reproduced evidence is deferred to phases 5/7.
  - Depends on: E-01
  - Expected outcome: `aw test <ipd> -- <cmd>` runs the command and writes an evidence record capturing command/stdout/stderr/exit/env bound to the current tree/commit; the record is retrievable by later `aw finish`.
  - Execution note: `work_cmd.run_test` runs the command, writes `test-evidence.json` (schema `aw.work-evidence/v1`) under `.aw/state/work/<id6>/` capturing command/cwd/exit_code/stdout/stderr/started_at/ended_at and git_head/git_tree, with `assurance: local-forgeable` (honest label). Exit mirrors the command's own exit. `aw finish` reads this exact record.
  - Execution state: performed

### Task group 3: commit

- [x] E-03 Add `aw commit <ipd> -- <paths>`: compute the plan's allowed scope from its `Scope-Paths`, refuse when the staged index contains any out-of-scope change, run the phase-1 `aw check` engine, and commit ONLY the declared in-scope paths by REUSING the selfcommit `git_commit_helper.offer_commit` (path-scoped `git add -- <paths>`, never `add -A`/`-a`, never `--no-verify`, never push). Do NOT fork a second commit path. (Cross-set dependency: `git_commit_helper` is delivered by selfcommit child cv1rfd and does not exist yet - see OQ-01 and the scope fence.)
  - Depends on: E-02
  - Expected outcome: `aw commit <ipd> -- <paths>` commits only in-scope paths via the shared helper; an out-of-scope staged change is refused with a clear message; the commit call uses no `add -A`/`-a` and no push.
  - Execution note: `git_commit_helper` EXISTS in the tree (the selfcommit set landed it; verified at start), so the OQ-01 sequencing prerequisite is satisfied and no thin internal committer was needed. `work_cmd.run_commit` computes the plan's Scope-Paths (via `ipd_schema.parse_scope_paths`), refuses when any staged OR requested path is out of scope (using `ipd_lifecycle._scope_match` + `_is_implicitly_allowed`), runs the phase-1 engine, then commits ONLY the declared paths through `git_commit_helper.offer_commit` (no forked commit path, no add -A/-a, no push).
  - Execution state: performed

### Task group 4: finish

- [x] E-04 Add `aw finish <ipd>`: check that the plan's required evidence (from `aw test`, E-02) is present and bound to the current tree, then perform only VALID NON-AUTHORITATIVE transitions - it does NOT perform the authoritative terminal `executed` transition (that stays with `aw ipd finalize` per the plans-README contract) and does NOT push or tag. Refuse with a clear message when required evidence is absent.
  - Depends on: E-03
  - Expected outcome: `aw finish <ipd>` transitions the plan only when the required bound evidence exists and refuses otherwise; it never performs the authoritative terminal transition, never pushes, never tags.
  - Execution note: `work_cmd.run_finish` hard-refuses `--to executed`/`done` (rc=2, points to `aw ipd finalize`), refuses when evidence is absent, when the evidence is bound to a STALE tree (git_tree != current), or when it records a FAILING run; on a valid `--to <status>` it delegates to the TOOLED `status_set.run_set_command` (writes an attributed history line, so it does not trip the untooled-status gate). It contains no git push/tag invocation.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `worktree_lease.py` already manages isolated worktrees (and lists `.aw/records/runs/` as ignored) - reuse for `aw work begin`.
- `ipd_lifecycle.py` performs the finalize transition + path-scoped commit today; `aw finish`/`aw commit` should build on it, not duplicate.
- The selfcommit `git_commit_helper` (selfcommit set) is the path-scoped committer to reuse for `aw commit` - creates a cross-set dependency; sequence selfcommit first.

## Findings

Each primitive validates-then-acts using the phase-1 engine, turning remembered duties into one command that also emits evidence. The commit primitive is the highest-leverage (enforces path-scope deterministically), and it must reuse the shared helper.

## Proposed changes (ordered, validatable)

1. `work_cmd.py` (or similar) + `cli.py`: `aw work begin`, `aw test`, `aw commit`, `aw finish`.
2. Reuse `worktree_lease`, `git_commit_helper`, `ipd_lifecycle`, and the phase-1 engine.
3. `tests/`: per-command behavior + evidence capture + scope refusal.

## Deferred / out of scope (with reason)

- Event-derived state (phase 3), hooks (phase 4), CI (phase 5): separate children.
- Trusted CI test runner / non-forgeable evidence (phase 7): deferred set; local evidence here is honestly labeled forgeable.

## Scope check

- Over-scope: none.
- Under-scope: none (the four primitives + evidence capture are the phase-2 deliverable).

## Required tests / validation

- `aw work begin` validates the plan and creates/associates a worktree.
- `aw test` captures command/exit/output/env and binds it to a tree/commit.
- `aw commit` commits only declared-scope paths, refuses out-of-scope staged changes, and uses the shared helper (no `add -A`, no push).
- `aw finish` performs non-authoritative transitions only when required evidence exists; refuses otherwise.

## Spec / documentation sync

- Document the atomic commands in AGENTS.md (make them the default path) and each `--help`.

## Open questions

### OQ-01: Should `aw commit` hard-depend on the selfcommit helper, or ship a minimal internal committer if selfcommit has not landed?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED (consistent with orchestrator 3b4f8u OQ-01) - hard-depend on the selfcommit `git_commit_helper.offer_commit` (delivered by selfcommit child cv1rfd, which does NOT exist in the tree yet). Sequence the selfcommit set BEFORE this child; this child is not runnable until `agent_workflows/git_commit_helper.py` exists. If scheduling forces it, the child-scope note permits a THIN internal committer to be replaced later by the shared helper - but never leave a second permanent commit path. This is a sequencing constraint on execution, not a blocker for review.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: (a) `aw work begin <clean-eligible-plan>` allocates/associates an isolated worktree and records a lease - paste the command output showing the worktree path and the `worktree_lease` entry; (b) run against a plan that has `aw check` findings and paste output showing it FAILS CLOSED (nonzero exit, findings printed, NO worktree allocated); (c) grep/import proof that `aw work begin` calls `worktree_lease.allocate_worktree`/`LeaseTable` and does not define a second worktree path (paste the import/grep).
  - Observed evidence: |
    (a) `aw work begin vw0001 --dir .` ->
        "aw work begin: validated 20260828-vw-01-vw0001-demo.ipd.md; allocated worktree
        /tmp/opencode/vev/.aw/worktrees/vw0001 (branch aw/lane/vw0001, base 6c708f39c2f5)";
        a lease JSON is written to `.aw/state/work/vw0001/work-lease.json` (test asserts plan_id +
        worktree_path present) and `git worktree list` shows the vw0001 worktree.
    (b) On a badly-named plan (check.name-nonconformant): `aw work begin bad001` ->
        "aw work begin: refusing to start - 1 finding(s) on badname.ipd.md:
          check.name-nonconformant: filename does not match the plans grammar" (rc=1); NO lease/worktree
        allocated (test_work_begin_fails_closed_on_findings asserts the lease file does not exist).
    (c) Single-worktree-path proof: `work_cmd` imports `worktree_lease as _wl` and calls
        `_wl.allocate_worktree` (test_work_begin_uses_shared_worktree_lease asserts the source contains
        "worktree_lease" + "allocate_worktree"); no second `git worktree add` path is defined in work_cmd.
    Unit tests tests/test_work_primitives.py::WorkPrimitivesTest (work-begin cases) PASS in the full run
    "2486 passed, 1 skipped".
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: (a) `aw test <ipd> -- <cmd>` on a passing command writes an evidence record - paste the record showing captured command line, stdout, stderr, exit code, and env metadata (cwd, timestamp, git HEAD/tree) bound to the current tree/commit; (b) the same for a FAILING command, showing the nonzero exit is captured faithfully (evidence is not silently "passed"); (c) the record is retrievable by `aw finish` (show the binding key/path); (d) confirm the evidence carries the honest locally-produced/forgeable label (paste the field).
  - Observed evidence: |
    (a) `aw test vw0001 --dir . -- python -c "print('ok')"` ->
        "aw test: recorded evidence for vw0001 (exit 0, PASS) bound to tree a2e00bb6cd8a; local-forgeable,
        not a CI-reproduced authority boundary". The record `.aw/state/work/vw0001/test-evidence.json`
        captures command=["python","-c","print('ok')"], cwd, exit_code=0, stdout, stderr, git_head,
        git_tree, started_at, ended_at (test_test_captures_passing_evidence asserts these fields).
    (b) A FAILING command `python -c "import sys;sys.exit(3)"` -> "exit 3, FAIL" (rc=1); the record's
        exit_code == 3 (test_test_captures_failing_exit_faithfully) - not silently passed.
    (c) The record path is `.aw/state/work/<id6>/test-evidence.json`; `aw finish` reads exactly this
        (run_finish -> _evidence_path); V-04 exercises the retrieval.
    (d) The evidence carries "assurance": "local-forgeable" (honest label per findings 6.6);
        test_test_captures_passing_evidence asserts rec["assurance"] == "local-forgeable".
    Unit tests tests/test_work_primitives.py (test cases) PASS ("2486 passed, 1 skipped").
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: (a) `aw commit <ipd> -- <in-scope-paths>` commits ONLY those paths - paste `git show --stat` of the resulting commit proving no extra files; (b) with an out-of-scope change staged, `aw commit` REFUSES with a clear message and makes NO commit (paste output + `git log` showing HEAD unchanged); (c) proof it delegates to `git_commit_helper.offer_commit` and uses no `add -A`/`-a` and no push (paste the import/grep and the absence of a forked commit path); (d) the phase-1 `aw check` engine is invoked before the commit (paste evidence).
  - Observed evidence: |
    (a) `aw commit vw0001 --dir . -m "a" -- src/a.py` -> "aw commit: committed 1 path(s): 1ff00b9..."
        and `git show --stat HEAD` -> " src/a.py | 1 +\n 1 file changed, 1 insertion(+)" (ONLY the
        in-scope path; test_commit_only_in_scope_paths asserts the .ipd.md is NOT in the commit and the
        -m message is honored).
    (b) With `outofscope.txt` staged: `aw commit ... -- src/g.py` ->
        "aw commit: refusing - out-of-scope change(s) present:\n  outofscope.txt\n  declared
        Scope-Paths: src/, tests/" (rc=1); HEAD unchanged (test_commit_refuses_out_of_scope_staged
        asserts rev-parse HEAD before == after).
    (c) run_commit calls `_gch.offer_commit` (test_commit_delegates_to_shared_helper asserts
        "_gch.offer_commit" in the source and no `git commit`/`_git(repo_root, ["commit"` forked path);
        offer_commit itself does path-scoped `git add -- <paths>`, never add -A/-a, never --no-verify,
        never push (git_commit_helper contract).
    (d) run_commit calls `_validate_plan_via_engine` (the phase-1 check_engine.check_type) BEFORE
        offer_commit and refuses on blocking findings (visible in the source; the validate-then-act
        order).
    Unit tests tests/test_work_primitives.py (commit cases) PASS ("2486 passed, 1 skipped").
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: (a) `aw finish <ipd>` with required bound evidence present performs a VALID non-authoritative transition - paste output and the resulting plan state; (b) `aw finish <ipd>` with required evidence ABSENT refuses with a clear message and changes nothing (paste output + unchanged plan state); (c) proof `aw finish` does NOT perform the authoritative terminal `executed` transition (that remains `aw ipd finalize`), does NOT push, and does NOT tag (paste the code path / absence of push/tag/finalize-executed calls).
  - Observed evidence: |
    (a) With evidence present and bound to the current tree, `aw finish wk0001 --dir . --to reviewed` ->
        "aw finish: transitioned wk0001 -> reviewed (evidence-bound, non-authoritative)" (rc=0) and the
        plan file then contains "- Status: reviewed" (test_finish_transitions_non_authoritative_with_evidence).
    (b) With evidence ABSENT, `aw finish wk0001 --to reviewed` -> "aw finish: refusing - no test
        evidence bound for wk0001. Run `aw test wk0001 -- <command>` first." (rc=1); the plan's
        "- Status: approved" is unchanged (test_finish_refuses_when_evidence_absent). ALSO: a STALE-tree
        evidence is refused ("refusing - the recorded test evidence is bound to a STALE tree ...",
        test_finish_refuses_stale_tree_evidence).
    (c) `aw finish wk0001 --to executed` -> "aw finish: refusing to set 'executed' - the authoritative
        terminal transition is performed only by `aw ipd finalize`, never by `aw finish`." (rc=2)
        (test_finish_refuses_executed). run_finish delegates a valid transition to the TOOLED
        status_set.run_set_command (attributed history line) and contains no git push/tag invocation
        (test_finish_never_pushes_or_tags asserts no '"push"'/'"tag"'/'git push'/'git tag' in the source).
    Unit tests tests/test_work_primitives.py (finish cases) PASS ("2486 passed, 1 skipped").
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: four E-items, one per primitive, each a single focused pass with its own verification surface (E-01 `aw work begin`, E-02 `aw test`, E-03 `aw commit`, E-04 `aw finish`). Kept as one child because the four primitives form one cohesive "atomic workflow-primitive" surface sharing the phase-1 engine, `worktree_lease`, `git_commit_helper`, and `ipd_lifecycle`; they do not warrant four separate child IPDs.

### Open questions resolved

- OQ-01 (hard-depend on the selfcommit helper vs. ship a thin internal committer): RESOLVED - hard-depend on `git_commit_helper.offer_commit` (selfcommit child cv1rfd), sequence the selfcommit set before this child. The helper does NOT exist in the tree today, so this child is NOT runnable until selfcommit lands (or, per the child scope note, ships a thin internal committer to be replaced later). This is a sequencing constraint, not a review blocker.

### Execution contract

- Scope fence: touch ONLY the files in `Scope-Paths` - `agent_workflows/cli.py`, `agent_workflows/work_cmd.py` (new), `agent_workflows/git_commit_helper.py` (delivered by selfcommit cv1rfd - REUSE, do not re-create if it exists; if it is absent this child is blocked - STOP and report per OQ-01), `agent_workflows/worktree_lease.py`, `agent_workflows/ipd_lifecycle.py`, and `tests/`. REUSE `worktree_lease` (work begin), `git_commit_helper` (commit), and `ipd_lifecycle` (finish transitions); do NOT fork a second worktree, commit, or finalize path, and do NOT build event-derived state (phase 3), hooks (phase 4), or CI (phase 5). If the work seems to need files outside this fence, STOP and report.
- Sequencing MUST: the selfcommit set (child cv1rfd) MUST land `agent_workflows/git_commit_helper.py` before E-03 runs; if it is not present, STOP and report rather than forking a permanent second commit path.
- Authority honesty (hard MUST): `aw finish` performs ONLY valid non-authoritative transitions - it MUST NOT perform the authoritative terminal `executed` transition (that stays with `aw ipd finalize`), MUST NOT push, and MUST NOT tag. Local evidence from `aw test` is honestly labeled forgeable (findings 6.6); do not describe it as an authority boundary.
- Honesty rule (hard MUST): when a V-item reports a test/command/`aw check` run passed, paste the ACTUAL runner output; never claim a pass you did not run.
- Commit rule: commit ONLY this child's own changed files, path-scoped (`git commit -m <msg> -- <paths>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically).
