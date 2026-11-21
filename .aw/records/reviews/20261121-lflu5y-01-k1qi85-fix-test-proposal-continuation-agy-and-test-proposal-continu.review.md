# Review findings: ipd k1qi85

- Subject-Id: k1qi85
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: REJECT - NEEDS REPLAN

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T064614Z-2150223`). The target plan `.aw/records/plans/pending/20261119-lflu5y-01-k1qi85-fix-test-proposal-continuation-agy-and-test-proposal-continu.ipd.md` was committed and unchanged, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` non-blocking `IPD-C802` info advisories on template boilerplate). Inspection of backlog `lflu5y`, `tests/test_fixfirst_end_to_end.py`, `tests/test_turn_fix_it.py`, `tests/slow_allowlist.txt`, `pyproject.toml`, `agent_workflows/lane_containment.py`, `agent_workflows/runner_shared.py`, `agent_workflows/backlog.py`, `agent_workflows/worktree_lease.py`, `git log` commit `5ca9a65a2`, and live pytest execution (`python3 -m pytest tests/test_fixfirst_end_to_end.py -k "test_proposal_continuation" -v`) surfaced two `BLOCKER` and two `HIGH` findings (`PR-001..PR-004`). Three findings (`PR-001..PR-003`) are marked `REPLAN` because the motivating bug (`lflu5y`) was already fixed on `main` by commit `5ca9a65a2` (2026-11-20) and `E-03`'s `.aw/records/backlog/open` assertion is empirically false and would break both currently passing tests; `PR-004` (missing execution-contract clauses in `Approval and execution gate`) was fixed in place. Verdict: `REJECT - NEEDS REPLAN`; Readiness: `no-go`.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Approval and execution gate` | Single paragraph directing "finalize the plan lifecycle to `executed/`" without conditional runner/executor `aw ipd finalize` ownership, hand-`git mv` prohibition, resolved-OQ precondition, `--scope-reason`/`--scope-ack` variance rule, honesty rule, or shared-checkout safety | Structured bulleted execution contract covering `no-go` replan notice, preconditions, `--scope-reason`/`--scope-ack` variance rule, hard-MUST paste-actual-runner-output honesty rule, shared-checkout safety, conditional runner/executor `aw ipd finalize k1qi85` ownership, and hand-`git mv` prohibition | PR-004, `steps/r2-executability.md`, `steps/s7-finalize.md` |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| P-01 | `Concern`, `Scope`, `E-01..E-03`, `Findings` | Plan assumes pre-`5ca9a65a2` failure state (7-char `prp1agy`, driver-side outcome path) and assumes `perform_coordinator_proposal_file` writes to `.aw/records/backlog/open/` in `_make_test_repo` | Maintainer decision: retire `k1qi85` (`not-executed`/`superseded`) and close backlog `lflu5y` citing commit `5ca9a65a2`, OR replan `k1qi85` as a narrower test-hardening plan fixing the vacuous `git branch --contains aw/lane/<idA>` assertion (rc=129) | Retire `k1qi85` and close backlog `lflu5y` citing commit `5ca9a65a2`, and file a small separate follow-up backlog item if hardening the vacuous `git branch --contains` check is desired | very strong |

### Step T

1. No; touches only test fixture `tests/test_fixfirst_end_to_end.py` and does not change any spec, public CLI, or production contract.
2. No; touches no private-data sanitizer, commit helper, worktree isolation implementation, merge-to-main code, or sandbox profile.
3. No; small (`3` E-items across `2` task groups and `1` test file in `- Scope-Paths:`).
4. Yes; `- Scope-Paths:` explicitly lists `tests/test_fixfirst_end_to_end.py` and this plan.
5. Yes; executing `E-03` as written would break two currently passing end-to-end runner proposal-continuation tests (`test_proposal_continuation_oc` and `test_proposal_continuation_agy`) on `main`.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261117-lflu5y-01-lflu5y-fix-test-proposal-continuation-agy-oc.backlog.md`, `tests/test_fixfirst_end_to_end.py` (`_run_proposal_continuation`, lines 1099-1285), `tests/test_turn_fix_it.py` (`_make_test_repo`, `_write_plan`), `tests/slow_allowlist.txt` (lines 145-146), `pyproject.toml` (`addopts`), `agent_workflows/lane_containment.py` (`lane_submission_root`, `project_worker_paths`), `agent_workflows/runner_shared.py` (`execute_item_core`, `perform_coordinator_proposal_file`), `agent_workflows/backlog.py` (line 816), `agent_workflows/worktree_lease.py` (`lane_branch_name`), `git show 5ca9a65a2 -- tests/test_fixfirst_end_to_end.py`, and live execution of `python3 -m pytest tests/test_fixfirst_end_to_end.py -k "test_proposal_continuation" -v`.
- Found that commit `5ca9a65a2` (2026-11-20) already implemented `E-01` and `E-02` on `main` (`PR-001`), that `F-03`/`E-03` contradicts live `agent_workflows/backlog.py` behavior (`PR-002`: files into `.agents/backlog/open/`, not `.aw/records/backlog/open/`), and that `git branch --contains aw/lane/prp1oc` currently exits `129` (`error: malformed object name aw/lane/prp1oc`) because `aw/lane/prp1oc` is absent after `run_queue` (`PR-003`).

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-01..E-03` <-> `V-01..V-03`, `- Highest E allocated: 03`), `- Scope-Paths:`, `- Item-Dependencies: none`, runtime reachability of `V-01..V-03`, and `Approval and execution gate`.
- Found `V-03` demands `.aw/records/backlog/open` output that is unreachable without changing `_make_test_repo` or creating `.aw/records/backlog/` (`PR-002`), and `Approval and execution gate` omitted required execution-contract clauses (`PR-004`, fixed in place).

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). Plan scopes edits solely to isolated `tempfile.TemporaryDirectory` test code in `tests/test_fixfirst_end_to_end.py`, with no credentials, outbound calls, or production trust-boundary changes.

### Step R4

- Checked: correctness and anti-regression (`PR-001` obsolete fix already landed in `5ca9a65a2`; `PR-002` executing `E-03` would actively regress two passing tests on `main`; `PR-003` vacuous `git branch --contains` check returning rc=129 on `main`), testing completeness, right-sizing, and `## Spec / documentation sync` (`N/A` truthful for a test-only plan).

### Step S5

- Checked: `## Open questions` (`None open.`). `PR-001`, `PR-002`, and `PR-003` are classified `REPLAN` (cannot be repaired with bounded edits without either retiring `k1qi85` or re-scoping it into a new test-hardening plan, which is the maintainer's decision). Per `agent_workflows/check_engine.py::_REVIEW_UNESCALATED_RULE` (line 10191), `replan` findings do not require an `IPD-Q501` blocking question in the plan; `- Readiness: no-go` and `Verdict: REJECT - NEEDS REPLAN` fail closed against approval and execution.

### Pass 2

- Re-checked the updated plan front matter (`- Status: reviewed`, `- Readiness: no-go`, `- Review-Depth: standard`), `## Workflow history`, and `Approval and execution gate`, plus verified `aw ipd lint --phase review-finalize --agent` passes cleanly with zero errors or warnings.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R4 / Obsolete premise (already fixed on `main`) | .aw/records/plans/pending/20261119-lflu5y-01-k1qi85-fix-test-proposal-continuation-agy-and-test-proposal-continu.ipd.md:5-6,38-46,69-73; tests/test_fixfirst_end_to_end.py::_run_proposal_continuation:1099-1220; commit `5ca9a65a2` | The motivating failure (`AssertionError: 1 != 3`), 7-character `prp1agy` fixture IDs, missing `lane_containment` import, and driver-side `outcomes/` writes described in `Concern`, `F-01`, `F-02`, `F-05`, `E-01`, and `E-02` were already fixed on `main` by commit `5ca9a65a2` (2026-11-20). `tests/test_fixfirst_end_to_end.py::_run_proposal_continuation` already imports `lane_containment` (line 1100), uses 6-character `host_tag = host_label[:2]` IDs (`prp1oc`/`prp1ag`, lines 1102-1105), writes isolated outcomes under `lane_containment.lane_submission_root(Path(work_dir), st["run_id"], itm, att)` (lines 1170-1219), and passes both `test_proposal_continuation_oc` and `test_proposal_continuation_agy` on unmodified `main` (`python3 -m pytest tests/test_fixfirst_end_to_end.py -k "test_proposal_continuation" -v`: `2 passed in 3.45s`). | C:Medium; U:Low; S:Low; F:High; Overall:High | REPLAN | Retire `k1qi85` (`not-executed`/`superseded`) and close backlog `lflu5y` citing commit `5ca9a65a2`, or replan solely around the residual vacuous branch assertion (`PR-003`). Recommendation strength: very strong. |
| PR-002 | BLOCKER | IN-SCOPE | R1 / R4 / False backlog path claim (would break passing tests) | .aw/records/plans/pending/20261119-lflu5y-01-k1qi85-fix-test-proposal-continuation-agy-and-test-proposal-continu.ipd.md:5-6,30,50,71,84,139; tests/test_turn_fix_it.py::_make_test_repo:54-65; agent_workflows/backlog.py:816; tests/test_fixfirst_end_to_end.py::_run_proposal_continuation:1258 | `F-03`, `E-03`, and `V-03` claim `perform_coordinator_proposal_file` files proposals into `.aw/records/backlog/open/` and instruct replacing `self.assertIn(".agents/backlog/open", log_out)` with `self.assertIn(".aw/records/backlog/open", log_out)` plus checking `.aw/records/backlog/open/*.backlog.md`. Live execution proves the opposite: `_make_test_repo` creates neither `.aw/records/backlog/` nor `.aw/config/project.json`, so `agent_workflows/backlog.py` (line 816) falls back to `.agents/backlog/open/` (observed: `.agents/backlog/open/20261121-<id6>-01-<id6>-proposal-from-prp1ag-update-tool.backlog.md`). Executing `E-03` as written would break both currently passing tests. | C:Low; U:Low; S:Low; F:High; Overall:High | REPLAN | Minimum replacement if targeting `.aw/records/backlog/open/`: create `.aw/records/backlog/` or `.aw/config/project.json` in `_run_proposal_continuation`'s temp repo before asserting `.aw/records/backlog/open/`; otherwise keep `.agents/backlog/open` or retire `k1qi85`. Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R1 / R4 / Vacuous branch containment check | .aw/records/plans/pending/20261119-lflu5y-01-k1qi85-fix-test-proposal-continuation-agy-and-test-proposal-continu.ipd.md:50,72,78; tests/test_fixfirst_end_to_end.py::_run_proposal_continuation:1260-1267 | On current `main`, `tests/test_fixfirst_end_to_end.py:1260-1267` runs `git branch --contains aw/lane/<idA>` with `check=False` and never asserts `returncode == 0`. Live probing shows `aw/lane/prp1oc` does not exist after `run_queue` (`git show-ref` lists only `refs/heads/main`), so `git branch --contains aw/lane/prp1oc` exits `129` (`error: malformed object name aw/lane/prp1oc`) with empty `stdout`, making `self.assertNotIn("main", contains_out.stdout)` pass vacuously. `E-03` also omitted asserting `returncode == 0` on both `git branch --contains` calls and verifying `refs/heads/aw/lane/<idA>` exists. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium-High | REPLAN | Minimum shape of a follow-up test-hardening replacement (if the human chooses to harden rather than retire): (1) commit a lane-local file in `idA`'s `work_dir` during `fake_turn` so `aw/lane/<idA>` holds unmerged work and is preserved, (2) verify `git show-ref --verify refs/heads/aw/lane/<idA>` exits `0`, and (3) assert `returncode == 0` on both `git branch --contains aw/lane/<idA>` (excluding `main`) and `git branch --contains main` (excluding `aw/lane/<idA>`). Recommendation strength: strong. |
| PR-004 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261119-lflu5y-01-k1qi85-fix-test-proposal-continuation-agy-and-test-proposal-continu.ipd.md:143-148; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` directed "finalize the plan lifecycle to `executed/`" without conditional runner/executor `aw ipd finalize k1qi85` ownership or explicit hand-`git mv` prohibition, and omitted resolved-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, hard-MUST paste-actual-runner-output honesty rule, and shared-checkout safety rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` in place with all required execution-contract clauses and `no-go` replan notice. Recommendation strength: very strong. |

### Decisions

None.
