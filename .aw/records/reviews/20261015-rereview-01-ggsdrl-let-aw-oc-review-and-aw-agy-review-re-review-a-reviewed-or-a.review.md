# Review findings: plan ggsdrl

- Subject-Id: ggsdrl
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (lane input sha matched the pending file), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` conforming after revisions.

Re-verified at review HEAD:
- `runner_shared.enforce_requested_action` refuses any item whose derived action differs ("--action review is illegal for ...").
- `runner_action('ipd','reviewed'|'approved'|'auto-approved', for_legality=True)` all return `execute`; `action_for('orchestrator','reviewed', for_legality=True)` returns `orchestrate`.
- `initialize_run_core`: `preflight_items` feeds only `enforce_requested_action`; the queue loop re-derives `action_for(kind, status ...)` and runs `if status == "reviewed" and full_auto and p_path:` auto-approve; several refusal gates (`enforce_freeze_time_refusal`, `enforce_orchestrator_shape_gate`, red-CI, spec-edit ack, orchestrator probe) run after queue build; `--prepare-only` returns before the probe gate.
- The post-review finish path calls `set_plan_approved` for a `reviewed` IPD under `full_auto` regardless of `options.action == "review"`.
- `review_has_positive_evidence` returns True on a non-empty `git status --porcelain`.
- `classify_review_writes` admits paths carrying the item's id6; `commit_review_lane_output` commits them in the sweep lane.
- `cli.expand_host_review_argv(['jmogmv','--yes'])` returns `['jmogmv', '--yes', '--action', 'review']` (already passes through).
- Neither `oc_runipd` nor `agy_runipd` `start` parser has `-y/--yes` today.
- `is_interactive_run` returns False under `--unattended` and `--full-auto`.
- Spec `25kzda`: 2.6 re-review bullet at line 525; the `reviewed, --action review` row is in 3.3 Specs (line 741), NOT in 3.2 IPDs; 2.1 line 231 "cannot force a status transition"; 2.6 alias bullet "cannot force a transition"; 4.4 intro and `IPD-REVIEW-LEGAL-TRANSITION` row.
- `ipd-spec` line 23 "For any other plan no tool demotes automatically".
- `docs/cli-reference.md` does not exist; `docs/artifact-lifecycles.md` "Moving backwards" paragraph is the operator-facing home.
- Scratch-repo demonstration: `aw ipd set to-review abc123 --message "re-review requested via oc review" --yes --no-commit --dir <tmp>` on an `approved` plan carrying `- Approval:` and `- Readiness:` printed `DEMOTED abc123: approved -> to-review: APPROVAL WITHDRAWN: re-review requested via oc review`, set `to-review`, removed both fields, and wrote the history line.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / C. Architecture | `agent_workflows/runner_shared.py` `initialize_run_core` (later refusal gates after queue build; `--prepare-only` return); `commit_review_lane_output` | E-04 demoted and committed the plan at run start in `initialize_run_core`. That writes `main` outside the review-lane merge, mutates the plan under `--prepare-only`, and withdraws approval even when a later refusal gate stops the run. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now only freezes `action: review` plus a `rereview: true` queue flag and writes nothing. New E-08 demotes at dispatch, inside the review lane, before lane inputs are materialized, with `--no-commit`, so the demotion lands with the review output. Added OQ-02 recording the choice. |
| PR-002 | HIGH | UNDER-SCOPE | B. Approval integrity | `runner_shared.py` post-review bridge calling `set_plan_approved` when `is_review ... and full_auto` | Scope said the `--full-auto` shortcut is skipped, but the plan covered only the queue-build site. The post-review bridge would auto-approve the freshly re-reviewed plan, which defeats "must be approved again". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-09(b) skips `rereview` items in the bridge. E-05(h) and V-09 prove it. F-4 now names both sites. |
| PR-003 | HIGH | UNDER-SCOPE | D. Anti-regression | `runner_shared.review_has_positive_evidence` (dirty `git status --porcelain` counts); `reconcile_disposition` IPD review branch | The demotion dirties the lane, so a review turn that does nothing passes the zero-output guard and the plan ends `reviewed` with no review and no Readiness. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-09(a) requires a `rereview` item to end `reviewed` with a `- Readiness:` line present, else `fail-gate`. E-05(g) covers it. Added F-7. |
| PR-004 | MEDIUM | IN-SCOPE | G. Executability | `initialize_run_core` queue loop `action = action_for(kind, status or "approved", ...)` | E-03 overrode only `preflight_items`. The queue builder re-derives the action on its own, so the item would still be frozen as `execute`. E-04 relied on the demoted status to derive `review`, which no longer happens at queue build after PR-001. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 passes a local `rereview_ids` set to the queue build. E-04 sets `action = "review"` explicitly for those ids. Added F-6. |
| PR-005 | MEDIUM | IN-SCOPE | Evidence | spec `25kzda` line 741 (in `### 3.3 Specs`); `### 3.2 IPDs` lines 711-728 | Concern and E-06 cited a 3.2 legality row `reviewed, --action review` for IPDs. That row is in 3.3 Specs. 3.2 has no such row. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern now cites 2.6 and 4.4 and states 3.2 has no row. E-06 ADDS the 3.2 rows and leaves 3.3 alone. |
| PR-006 | MEDIUM | UNDER-SCOPE | Spec sync | spec `25kzda` line 231 (2.1) and line 531 (2.6 alias bullet) | Both sentences say `--action review` / `aw <host> review` "cannot force a status transition". The new demotion contradicts them, and E-06 did not amend either. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 amends both to name the operator-confirmed re-review demotion as the exception. Spec sync section updated. |
| PR-007 | LOW | IN-SCOPE | Evidence / G | `agent_workflows/cli.py` `expand_host_review_argv`; `p_oc_review` / `p_agy_review` descriptions | E-02 told the executor to make `expand_host_review_argv` pass `--yes` through. It already forwards the tail verbatim (measured). Meanwhile the alias help text ("refuses rather than executing when a selected plan is already past review") becomes stale and was not covered. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 records the measurement, drops the no-op change, and updates both alias descriptions. |
| PR-008 | LOW | IN-SCOPE | G. Right-sizing / docs | `docs/cli-reference.md` (absent); `docs/artifact-lifecycles.md` "Moving backwards" | E-06 targeted a docs file that does not exist and bundled two spec amendments with three docs edits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split out E-10 (plan-review.md, `docs/artifact-lifecycles.md`, CHANGELOG) with V-10 and a dash scan. Scope-Paths now lists `docs/artifact-lifecycles.md`. |
| PR-009 | LOW | IN-SCOPE | F. UX / clarity | plan Scope "a NAMED IPD"; `runner_shared.is_status_selector` | "NAMED" left the setid case undefined. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Defined as reached through a non-status selector (id6, path or setid), keyed on `is_status_selector`. E-05(d) covers `reviews` and `all`. |
| PR-010 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the hard-MUST paste-actual-output rule, the resolved-questions statement, and the conditional lifecycle-transition ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all three. The scope fence stays a declaration, and STOP applies only to an unsafe concurrent edit. |
| PR-011 | LOW | IN-SCOPE | Evidence | backlog `dbr23q` body | F-5 said the `--yes`/interactive ruling is "recorded on backlog `dbr23q`". The backlog records the reviewed-and-approved need but not the confirmation ruling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 now says the ruling was given in the authoring session and recorded in this plan, and that the backlog records the need. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Demote at run start or at dispatch? | At dispatch, in the review lane, uncommitted, before lane inputs | Run start with a direct commit to main (writes main outside the merge; mutates under `--prepare-only`; withdraws approval on later refusal); after the review turn (reviewer would read the stale Readiness) | `initialize_run_core` gate order; `commit_review_lane_output` / `classify_review_writes`; the existing orchestrator-readiness demotion uses `--no-commit --dir <tree>` | yes |
| D-2 | Does a setid selector count as "named"? | Yes, any non-status selector | id6/path only (setid would then refuse, which is surprising because the operator typed the Set) | `runner_shared.is_status_selector` is the existing named-vs-sweep discriminator used by the draft gate (spec 2.5a) | yes |
| D-3 | How does the queue carry the re-review fact? | Additive `rereview: true` key, absent otherwise | Re-derive from status at dispatch (cannot tell a re-review from a normal reviewed item) | Queue entries already carry additive keys such as `NEEDS_INPUT_KEY` | yes |
| D-4 | What proves a re-review actually reviewed? | Plan ends `reviewed` AND carries a `- Readiness:` line | Rely on `review_has_positive_evidence` (satisfied by the demotion alone) | `review_has_positive_evidence` dirty-tree rung; demotion strips Readiness (scratch demonstration) | yes |
| D-5 | May `--full-auto` auto-approve a re-reviewed plan? | No, never | Allow it as for a normal review (contradicts "must be approved again" and the maintainer's confirmation requirement) | Plan Scope; F-5 ruling; post-review bridge site | yes |
| D-6 | Where do operator docs go? | `docs/artifact-lifecycles.md` "Moving backwards" | Create `docs/cli-reference.md` (new file for one entry) | `docs/` listing; the paragraph already documents `reviewed -> to-review` re-review | yes |
