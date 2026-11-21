# Review findings: ipd 8h1q1k

- Subject-Id: 8h1q1k
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T070301Z-2497766`). The target plan `.aw/records/plans/pending/20261121-8s4qhh-01-8h1q1k-land-agent-filed-defect-backlog-items-on-main-when-a-lane-st.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` findings). Inspection of backlog item `8s4qhh`, sibling plan `l7d19a`, `agent_workflows/runner_shared.py` (`execute_item`, `ProposalFilingResult`, `perform_coordinator_proposal_file`, `SuiteCheckResult`), `agent_workflows/worktree_lease.py` (`WorktreeHandle`, `_attempt_scoped_lane_id`), `agent_workflows/backlog.py` (`parse_item`, `validate_item`, `run_new`, `run_check`), `agent_workflows/check_engine.py` (`check_live_bug_gate`), `agent_workflows/artifact_core.py` (`mint_id6`, `global_id6s`), `.pre-commit-config.yaml`, and `tests/test_run_proposal_channel.py` surfaced three `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-005`), all fixed in place. Pass 2 re-checked `Scope`, `Goal`, `E-01..E-03`, `Step 0`, `Findings`, `Proposed changes`, the Mermaid diagram, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `V-01..V-03`, and `Approval and execution gate` for full internal consistency.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Approval and execution gate` | Unconditionally instructed `aw ipd finalize` and omitted hand-`git mv` prohibition, resolved-OQ precondition, `--scope-reason`/`--scope-ack`, shared-checkout safety, and honesty rule | Added all required execution-contract clauses including conditional runner/executor `aw ipd finalize 8h1q1k` ownership | PR-001, `steps/r2-executability.md`, `steps/s7-finalize.md` |
| `Scope`, `E-02`, `Step 0`, `Proposed changes`, `V-02` | Passed only `lane_base_commit` (missing `wt_handle.branch`), omitted post-proposal write ordering relative to `st_mtime` selection, and missed the `PROPOSAL_KIND_NEEDS_ATTENDED` early-return path | Added explicit `lane_branch` + `lane_base_commit` threading, post-proposal write ordering, clean no-op when absent, and `needs-attended` already-marked commit handling | PR-002, `steps/r4-engineering.md` |
| `Scope`, `E-01`, `E-02`, `E-03`, `V-01`, `V-02` | Used `git diff --name-status` without regular-file/direct-child/size guards, omitted `global_id6s` collision, `setid` error, `blocks-release-dangling`, `config.release_gate_work_kinds` + `Release-Exempt-*` support, and omitted hook-rejection proposal-only fallback | Switched to `git diff --raw -z --diff-filter=A` with `100644`/`100755`, direct-child, and `500 KiB` bounds; added full conformance/collision/gate checks and proposal-only fallback if `offer_commit` rejects the combined commit | PR-003, `steps/r3-security.md`, `steps/r4-engineering.md` |
| `Scope`, `E-02`, `E-03`, `Step 0`, `V-02`, `V-03` | Did not specify backward-compatible defaulted tuple types on `ProposalFilingResult`, omitted `prop_rec`/`agent-proposal-refused` propagation, and omitted `oc`/`agy` parametrization and no-source-inspection constraint | Specified defaulted immutable tuple fields on `ProposalFilingResult`, propagation into `item["proposal_record"]`/`attempt["proposal_record"]`/`events.jsonl`, `oc`/`agy` end-to-end tests, and zero-source-inspection constraint | PR-004, `steps/r1-references.md`, `steps/r4-engineering.md` |
| `Scope`, `Step 0`, `Proposed changes`, Mermaid diagram, `Deferred / out of scope` | Used bare module citations, omitted hook-fallback and post-proposal ordering in Mermaid diagram, and excluded non-proposal preserved lanes in `Scope` without a `Deferred / out of scope` entry or `- Carrier-Declined:` | Qualified citations to `path::Symbol`, aligned Mermaid diagram terms and branches with normative text, and documented non-proposal preserved lanes in `Deferred / out of scope` with `- Carrier-Declined:` | PR-005, `steps/p-proofread.md` Section 11.1, technical writing standard Requirements 4, 5, 12(d)-(e) |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes; extends `agent_workflows/runner_shared.py::ProposalFilingResult`, `item["proposal_record"]`, and `events.jsonl` (`agent-proposal-filed` / `agent-proposal-refused`), and changes which files coordinator proposal filing lands onto `main`.
2. Yes; touches coordinator worktree commits (`agent_workflows/git_commit_helper.py::offer_commit`), `main` fast-forward landing (`agent_workflows/ipd_lifecycle.py::land_worktree_commit`), `integration_lock`, and reading untrusted agent-authored files from an unmerged isolated lane branch.
3. No; compact and focused (`3` E-items in `1` task group across `1` production file and `1` test file).
4. Yes; `- Scope-Paths:` explicitly lists `agent_workflows/runner_shared.py`, `tests/test_run_proposal_channel.py`, and this IPD.
5. Yes; a mistake could land malformed/non-backlog/symlink/colliding files from a failing lane onto `main`, mis-select the proposal record via `st_mtime`, or cause pre-commit hooks on a lane file to block the proposal record itself from landing.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261121-8s4qhh-01-8s4qhh-runner-proposal-filing-strands-agent-filed-defect.backlog.md`, sibling plan `.aw/records/plans/pending/20261121-68ympf-01-l7d19a-truncate-proposal-summaries-on-word-boundaries-in-perform-co.ipd.md`, `agent_workflows/runner_shared.py` (`execute_item:45826-45984`, `ProposalFilingResult:51727-51743`, `perform_coordinator_proposal_file:51776-52211`, `SuiteCheckResult:52282-52300`), `agent_workflows/worktree_lease.py` (`WorktreeHandle:1026-1038`, `_attempt_scoped_lane_id:1040-1052`), `agent_workflows/backlog.py` (`parse_item:342-398`, `validate_item:439-648`, `run_new:1040-1280`, `run_check:1685-1802`), `agent_workflows/check_engine.py` (`check_live_bug_gate:7691-7809`), `agent_workflows/artifact_core.py` (`mint_id6:174-194`), `.pre-commit-config.yaml`, and `tests/test_run_proposal_channel.py`.
- Found unpopulated `item["lane_branch"]` vs. `wt_handle.branch` (`PR-002`), `st_mtime` file selection after `aw backlog new` (`PR-002`), `PROPOSAL_KIND_NEEDS_ATTENDED` early return (`PR-002`), missing `check_live_bug_gate` / `global_id6s` / `setid` checks (`PR-003`), `ProposalFilingResult` default tuple compatibility (`PR-004`), abbreviated citations, and uncarried `Scope` exclusion of non-proposal preserved lanes (`PR-005`). All fixed in place.

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-01..E-03` <-> `V-01..V-03`, `- Highest E allocated: 03`), dependency chain (`E-01 -> E-02 -> E-03`), `- Scope-Paths:` completeness, `- Item-Dependencies: none` (independent of sibling `l7d19a`), runtime reachability of `V-01..V-03` (all demand git diffs or real pytest/CLI outputs, reachable by construction), and `Approval and execution gate`.
- Found non-conforming execution contract in `Approval and execution gate` (`PR-001`). Fixed in place.

### Step R3

- Checked: full security and privacy lens (`steps/r3-security.md`). Because `perform_coordinator_proposal_file` copies files from an unmerged failing lane branch onto `main`, it crosses a trust boundary.
- Found trust-boundary gaps (`PR-003`): `git diff --name-status` does not reject symlinks (`120000`), submodules (`160000`), nested subdirectories, or oversized blobs; `backlog.validate_item` does not guard `global_id6s` collisions, `check.blocks-release-dangling`, `check.setid-length-error`, or `config.release_gate_work_kinds` + `Release-Exempt-*`; and a recovered file tripping `local-leaks` or `gitleaks` in `_gch.offer_commit` would block the proposal record itself from landing. All fixed in place.

### Step R4

- Checked: correctness and data integrity (`PR-002`: attempt-scoped `wt_handle.branch`, post-proposal write ordering avoiding `st_mtime` mis-selection, `PROPOSAL_KIND_NEEDS_ATTENDED` early return, race-retry re-validation against fresh `cur_base`), backward compatibility and observability (`PR-004`: defaulted immutable tuple fields on `ProposalFilingResult`, propagation to `prop_rec` and `events.jsonl`), testing (`E-03` expanded to cover both `oc` and `agy` hosts, all fail-closed rejections, hook-rejection fallback, `needs-attended`, and zero source inspection per `GUIDING_PRINCIPLES` P16), right-sizing (`3` E-items, `3` Scope-Paths, single cohesive bugfix), and `## Spec / documentation sync` (`N/A` verified truthful).

### Step S5

- Checked: `## Open questions` (`None.`). Every finding (`PR-001..PR-005`) has `Overall:Low` Remediation Risk and was fixed in place. Recorded `D-1` (declining non-proposal preserved lane recovery from `8h1q1k` with `- Carrier-Declined:`, `Reversible: yes`) in `### Decisions`. Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan across `Scope`, `Goal`, `E-01..E-03`, `Step 0`, `Findings`, `Proposed changes`, Mermaid diagram, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `V-01..V-03`, and `Approval and execution gate`.
- Verified `3/3` E/V bijection, `- Highest E allocated: 03`, zero unresolved questions, and clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261121-8s4qhh-01-8h1q1k-land-agent-filed-defect-backlog-items-on-main-when-a-lane-st.ipd.md:134-139; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` unconditionally instructed running `aw ipd finalize` and omitted the explicit hand-`git mv` prohibition, resolved-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, shared-checkout safety rule, and hard-MUST paste-actual-runner-output honesty rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with all required execution-contract clauses and conditional runner/executor `aw ipd finalize 8h1q1k` ownership. Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R4 / Correctness and data integrity | agent_workflows/runner_shared.py::perform_coordinator_proposal_file:51797,52005-52014,52139-52154; agent_workflows/runner_shared.py:44245-44247,45832-45839; agent_workflows/worktree_lease.py::_attempt_scoped_lane_id:1040-1047 | Three coordinator correctness hazards: (1) `execute_item` never sets `item["lane_branch"]`, so passing only `lane_base_commit` without `lane_branch=wt_handle.branch` queries the wrong branch for attempt-scoped lanes (`aw/lane/<id6>_attempt2`); (2) `perform_coordinator_proposal_file` selects `created_backlog` by `st_mtime` descending after `aw backlog new`, so writing recovered lane backlogs beforehand risks mis-selecting a recovered file as the proposal record; (3) `PROPOSAL_KIND_NEEDS_ATTENDED` returns early when `marked == target_text` before committing recovered lane defect backlogs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `Scope`, `E-02`, `Step 0`, `Proposed changes`, Mermaid diagram, `E-03`, and `V-02` to thread both `lane_branch` and `lane_base_commit` from `wt_handle`, write recovered files strictly after resolving `new_record_rel`/`record_id6`, no-op cleanly when absent, and commit recovered backlogs even when `needs-attended` sees `marked == target_text`. Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R3 / R4 / Security, validation, and availability | .aw/records/plans/pending/20261121-8s4qhh-01-8h1q1k-land-agent-filed-defect-backlog-items-on-main-when-a-lane-st.ipd.md:38-46; agent_workflows/backlog.py::validate_item:439-648; agent_workflows/artifact_core.py::mint_id6:174-194; agent_workflows/check_engine.py::check_live_bug_gate:7691-7809; .pre-commit-config.yaml:36-63 | Trust-boundary and availability gaps when copying files from an unmerged failing lane onto `main`: (1) `git diff --name-status` does not reject symlinks (`120000`), submodules (`160000`), nested subdirectories, or oversized blobs; (2) `backlog.validate_item` does not check `global_id6s` collisions, filename-to-id6 agreement, `check.setid-length-error`, `check.blocks-release-dangling`, or `config.release_gate_work_kinds` with valid `Release-Exempt-*`; (3) a recovered lane file failing a commit hook (`local-leaks`, `gitleaks`) in `_gch.offer_commit` would reject the combined commit and block the proposal record itself from landing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Hardened `E-01` (`git diff --raw -z --diff-filter=A`, regular-file modes `100644`/`100755`, direct-child containment, `500 KiB` bound) and `E-02` (full conformance/collision/release-gate/exemption checks and fail-closed retry of `[new_record_rel]` alone on hook rejection), with matching tests in `E-03` and checks in `V-01..V-03`. Recommendation strength: very strong. |
| PR-004 | MEDIUM | IN-SCOPE | R1 / R4 / Contract compatibility and observability | agent_workflows/runner_shared.py::ProposalFilingResult:51727-51743; agent_workflows/runner_shared.py:45840-45875; agent_workflows/runner_shared.py::SuiteCheckResult:52282-52300 | Plan did not specify backward-compatible defaulted immutable tuple fields on `ProposalFilingResult` (`NamedTuple`), omitted propagation into `item["proposal_record"]`/`attempt["proposal_record"]` and `agent-proposal-refused`, and omitted `oc`/`agy` end-to-end parametrization and the zero-source-inspection constraint (`GUIDING_PRINCIPLES` P16) in `E-03`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified defaulted `tuple` fields on `ProposalFilingResult`, propagation to `prop_rec` and `events.jsonl` at the `execute_item` call site, `oc`/`agy` end-to-end parametrization, and zero-source-inspection constraint in `E-02`, `E-03`, `V-02`, and `V-03`. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | Proofreading / R1 / Technical writing standard | .aw/records/plans/pending/20261121-8s4qhh-01-8h1q1k-land-agent-filed-defect-backlog-items-on-main-when-a-lane-st.ipd.md:6,60-93; .aw/records/backlog/graduated/20261121-8s4qhh-01-8s4qhh-runner-proposal-filing-strands-agent-filed-defect.backlog.md:35; .aw/system/workflows/plan-review/steps/p-proofread.md | Plan used abbreviated module citations instead of `path::Symbol`, Mermaid diagram omitted post-proposal ordering and hook-rejection fallback, and `Scope` excluded `non-proposal lane preservation paths` (mentioned in backlog `8s4qhh` Fix direction item 1) without a `Deferred / out of scope` entry and `- Carrier-Declined:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Qualified all citations to `path::Symbol`, aligned the Mermaid flowchart with the normative steps, added the non-proposal lane preservation row with `- Carrier-Declined:` in `Deferred / out of scope`, and recorded `D-1`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should plan `8h1q1k` also add a new coordinator main-commit path for non-proposal preserved lanes whose `defect_report` reports findings (mentioned in backlog `8s4qhh` Fix direction item 1), or keep `8h1q1k` scoped to proposal lanes and decline non-proposal lanes explicitly? | Keep `8h1q1k` scoped to proposal lanes (`perform_coordinator_proposal_file`) and record non-proposal preserved lanes in `## Deferred / out of scope` with `- Carrier-Declined:`. | Add a separate coordinator main-commit path for all preserved non-proposal lanes (rejected: non-proposal lanes do not publish a proposal record citing dangling IDs on `main` and remain preserved for resume/merge; adding a second coordinator landing path would broaden scope and risk interfering with lane resume). | Backlog `8s4qhh` Summary and Problem sections (specifically describing proposal filing stranding referenced defect backlogs); plan `8h1q1k` `Scope` exclusion | yes |
