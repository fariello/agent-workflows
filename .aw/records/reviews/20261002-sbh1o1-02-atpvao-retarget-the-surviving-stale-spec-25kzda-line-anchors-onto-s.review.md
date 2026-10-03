# Review: Retarget the surviving stale spec 25kzda line anchors onto stable section tokens

- Subject-Id: atpvao
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `e75cde645`:

- Both dependencies are executed. `mt54wr` and `yu47nf` are both in `plans/executed/`.
- `aw check specs --source-anchors` exits 0 and reports 23 findings. 22 are spec `25kzda` and one is `check_engine.py:353`, which cites spec `pqsx96` at offset `:135`.
- No `:166` site survives in `runner_shared.py`, so the sibling-owned sites are already gone.
- The cited claims resolve to these sections:
  - "mutually exclusive with a new selector", the `--full-auto` implication, "not silently enqueued", and "legal only when contractless prompts" are in `### 2.1`.
  - "not satisfaction semantics" is in `### 2.6`.
  - "before mixed-type confirmation" is in `### 5.4`.
  - "cannot mask a failed prompt" is in `### 5.6`.
  - `RUN-HOST-CAPABILITY` is in the `### 4.2` table row and under `#### Per-host capability descriptor`.
  - `host_capability_unavailable` is in `### 5.4` and `### 5.7`, and the reporting columns are in `### 5.6`.
- `drift_exit_code([warning]) == 1` and `drift_exit_code([info]) == 0`.
- Driver files: every `25kzda` hit in `oc_runipd.py` and `agy_runipd.py` is a section citation. None is an offset.
- `tests/test_spec_citation_anchors.py` gives `7 passed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | OVER-SCOPE | Executability (G) / human decision | `aw check specs` exits 1 (`89xjll` Scope); `.github/workflows/tests.yml` has no `check specs` step; detector still flags `check_engine.py:353` (`pqsx96 :135`); `/usr/bin/time` gives about 3.5s user CPU for `--source-anchors` and about 0.6s for bare `check specs`; `mt54wr` OQ-01 is `Status: open`, `Owner: maintainer` | E-05/E-06 (the promotion) cannot meet their own bar. Bare `check specs` already exits 1 for an unrelated reason. CI never runs that verb. The census cannot reach zero, because the detector misreads one valid citation. Making the rule default-on slows the command noticeably. Separately, the decision to promote is the maintainer's: OQ-01 is still open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed E-05/E-06 and V-05/V-06. Removed `check_engine.py`, `cli.py` and `tests/test_spec_citation_anchors.py` from Scope-Paths. Filed carrier backlog `1vd74h` with all five measurements. Added F-08 and swept every reference to the promotion. |
| PR-002 | MEDIUM | UNDER-SCOPE | Correctness / Testing | `runner_shared.py` `RUN_POLICY_FLAGS` `--type` comment (`:129`, `:131`); `evaluate_unverifiable_admission` (`spec 2.1 :136`); `run_evidence.AggregatedItem` (`:938` twice); `validate_non_maskable_table` bullet (`:938`) | The detector only attributes an anchor to a spec when its comment or docstring block names the id6. These five sites are `25kzda` anchors that the detector does not see, so a sweep driven only by the detector leaves them stale. F-03 also wrongly says `:136` appears nowhere. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 adds a classified supplementary grep as a cross-check. E-02 and E-03 now name the missed sites and their target sections. V-01, V-02 and V-03 now require the grep alongside the detector output. |
| PR-003 | LOW | IN-SCOPE | Provenance | `- From-Spec: 25kzda`; `production_checks` counts plans with `From-Spec` as authored from that spec | The plan graduated from backlog `p9y51u`, not from spec `25kzda`, so `From-Spec` records a provenance that did not happen. The plan only cites that spec. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed `From-Spec`. `From-Backlog: p9y51u` stays. |
| PR-004 | LOW | IN-SCOPE | Evidence accuracy | F-04 "does not exist yet"; title "and promote the detector"; OQ-02 `Owner: none` | F-04 is stale now that `mt54wr` has executed. The title still describes the removed scope. The open question names no decider. | all Low | FIXED | Annotated F-04 as resolved since authoring. Retitled the plan. Set the OQ-02 owner to `maintainer`. |
| PR-005 | MEDIUM | IN-SCOPE | Executability (G) / live-artifact criteria | gate "POST-GATE LIFECYCLE"; Required tests "no regression against ... 3618 passed" | The gate did not say who runs finalize (runner or human), had no never-`git mv` rule, and had no reconcilable scope-fence wording. The suite bar was a fixed count from authoring time. Removing V-06 also left the full-suite run without a home. | all Low | FIXED | Added scope-fence wording and conditional finalize ownership. E-01 captures a baseline. E-04 and V-04 require an empty failure-set delta, stated as test ids, plus a `git diff --name-only` scope check. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this plan still promote `check.spec-anchor-stale`? | No. Descope it to new backlog `1vd74h`. | Keep it with a refusal path (it would always refuse: bare `check specs` exits 1 and the census is nonzero). Rewrite it to wire into `check all`/CI (that takes the maintainer's OQ-01 decision). | `mt54wr` OQ-01 (Owner: maintainer, open); measurements in PR-001 | yes |
| D-2 | Should `From-Spec: 25kzda` be kept? | Remove it | Keep it (it asserts a spec-graduation provenance that did not happen) | Workflow-history line: "Authored from backlog item `p9y51u`" | yes |
| D-3 | Is the detector sufficient as the census? | No. Add a classified grep as a cross-check. | Detector only (misses 5 sites); grep only (loses heading resolution) | `spec_citations._find_anchors_on_line` requires a context id6; grep run at review | yes |
