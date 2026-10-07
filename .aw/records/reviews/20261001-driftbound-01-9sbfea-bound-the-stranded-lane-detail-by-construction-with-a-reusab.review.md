# Review findings: plan 9sbfea

- Subject-Id: 9sbfea
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fe2ee961c` in an isolated review lane. The plan was committed and byte-identical to the lane input,
so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review, and
`--phase review-finalize` was clean after revision.

Reproduced (gitignored probes under `.aw/state/`, with no production edit):
- `attention.stranded_lane_drift(Path('.'))`: 5 rows, all `attention.lane-stranded`, lengths 262/241/241/241/241,
  all `is_safe_descriptive` True. 387 run dirs (longest `run_id` 28), 15 worktree entries (longest 41), signals
  `driver-run-suite`, `suite-failed`, `verifier`, `verifier-declined`; `lane_remedy_hint('abc123')` 41 characters;
  `escape_detail('\\'*300)` is 600 characters; `compose_bounded_detail` absent.
- `python3 -m pytest tests/test_attention_lane_detail_bound.py -o addopts="" -s`: `3 passed`; case (c) prints
  `composed length=373 ... (honest residual: 73 over bound)`.
- Today's assembly is `"{0}: {1}. {2}".format("; ".join(bits), why, lane_remedy_hint(...))`
  (`agent_workflows/attention.py`, `stranded_lane_drift`). A prototype single-budget composer held `<= 300` over a
  deterministic sweep (worst 300). Its pass-through equals today's row ONLY with per-segment joiners; a uniform
  `"; "` join does not.
- `check all --json`: 1 of 123 findings is over-bound (`check.ipd-carrier-finished-unverified`, 329 characters).
  `7stpjm` is `done` via executed `lxcexr`. `aw check plans` reported `check.ipd-carrier-finished-unverified` on this
  plan for the `7stpjm` row; after revision it reports none.
- `62pkkg` declares `- Item-Dependencies: executed:9sbfea`; `qpw45x` is `to-review`; `xhr0dj` is `draft`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A/D. Correctness, anti-regression | `agent_workflows/attention.py` `stranded_lane_drift` (`"{0}: {1}. {2}".format(...)`); review prototype | E-02/E-03 defined pass-through as `"; ".join(segments)` plus the trailer, but the live row uses `": "` before `why`, `"."` after it, and `" "` before the trailer. Implemented as written, E-04's byte-identical claim is false for every live row, or the composer cannot express the format. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires each segment to carry its own leading joiner and specifies the dropped and clipped `why` shapes. E-03/E-02/V-02 assert equality with today's literal `format(...)` assembly. The fix was verified by prototype. |
| PR-002 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | Probe counts above | F-03 (six rows, 297 max), F-04 and F-11 (25 over-bound) have all moved. E-04's "every live row is at most 297" premise and the byte-identical bar were pinned to an authoring corpus. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added review re-measurements. The byte-identical bar now applies to the set re-derived in E-01, with an over-bound live row named as the expected exception. |
| PR-003 | LOW | IN-SCOPE | G. Carrier traceability | `aw check plans` `check.ipd-carrier-finished-unverified` on this plan; `.aw/records/plans/executed/*lxcexr*` | The `7stpjm` Deferred row had no `Carrier-Evidence` after its carrier finished. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cited the executed `lxcexr`; the finding clears. |
| PR-004 | LOW | IN-SCOPE | B/G. Shared-checkout safety | V-05 "naming exactly how the revert was done"; V-03 perturbation | The red-before route allowed a working-tree revert, and the perturbation had no proof it was undone. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Red-before now comes from writing tests first or a `git show HEAD:` scratch import, with no stash and no revert. V-03 pastes `git diff` after restoring. |
| PR-005 | MEDIUM | IN-SCOPE | G. Execution contract | Approval and execution gate | The gate claimed "carries no Readiness" (stale once reviewed). It had no explicit paste-output rule, no scope fence, and no conditional finalize ownership (runner vs `aw ipd finalize`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all elements. The fence is a declaration reconciled by `--scope-reason`/`--scope-ack`. |
| PR-006 | LOW | UNDER-SCOPE | G. Traceability | Scope check "the Set's one user-facing note"; Proposed change 6 | `CHANGELOG.md` was declared but owned by no E-item and checked by no V-item. The suite bar was "green" against a non-green base. OQ owners read `this plan`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 owns the entry and V-04 quotes it (no em or en dash). The suite is compared by failure set against a re-derived baseline. OQ owners are now `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the composer reproduce today's non-uniform row format? | Each segment carries its own leading joiner; the trailer is passed with its separator | Uniform `"; "` join (changes every live row); special-casing `why` inside the composer (not reusable by Order 02) | `attention.py` `stranded_lane_drift` format string; review prototype pass-through equality | yes |
| D-2 | Must the byte-identical bar hold if a live row is already over bound at execution? | No. That row is the defect, so it is the named exception | Hold the bar unconditionally (unsatisfiable in that case) | Plan's own thesis (F-03/F-04 drift); E-01 re-derivation | yes |
