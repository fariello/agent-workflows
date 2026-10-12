# Review: Add an advisory check rule flagging shipped-source comments that cite nonexistent test files

- Subject-Id: ml7b9e
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Verified at HEAD `bd8b8e993`. `aw ipd lint --phase author` clean before edits and `--phase review-finalize`
clean after. Anchors resolved: `check_engine.RULE_REGISTRY["check.test-citation-dangling"]`,
`check_engine._TEST_PATH_RE`, `check_engine.check_spec_test_citations_for_text`, `check_engine.enrich_drift`,
`check_engine.rule_spec`, the `if collisions:` seam of `check_engine.check_types` with
`check_scope_path_target_stale` in its own `try/except`, `artifact_core.drift_exit_code` (`info` exempt),
`artifact_core.get_ignored_dirs`/`is_ignored_path` (`__pycache__` in the default set),
`artifact_refs.check_source_citations` (same test-file skip), `doctor.build_remediation`
(`title = detail if len(detail) < 60 else rule`), and the CHANGELOG `## 2.0.0 (pending)` section.
A throwaway re-scan reproduced F-02 exactly (`Counter({'live': 110, 'retired': 21, 'placeholder': 11})`,
47 candidate files, 0.23s); a digit-requiring hash form still exempts 21.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Correctness | Re-scan: 82 missing (file, path) pairs, 79 live, 4 mixed (`agy_runipd.py`/`oc_runipd.py` x `tests/test_runner_backlog_close.py`; `runner_shared.py` x `tests/test_orchestrator_probe_cache.py`, `tests/test_runner_refork_guard.py`) | E-03 left the order of exemption vs per-(file, path) dedup unspecified; dedup-first would hide a live claim behind an earlier retirement statement in the same file. V-03's bar ("matches live modulo dedup") was not checkable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 exempts per occurrence then dedups, reporting the first non-exempt line; E-01 records the live-pair count; V-03 requires equality; E-05 adds case (6b) with a neutering proof. Added F-07. |
| PR-002 | MEDIUM | IN-SCOPE | E. Evidence feasibility | `aw check all --agent` at `bd8b8e993` -> `exit 1`; `artifact_core.drift_exit_code` | The plan's advisory proof was exit-code parity of `aw check all`, which is already 1 on the live tree and so cannot distinguish an advisory rule from a failing one; case (9) lacked the contrastive limb. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 (9) adds the `rule_spec` severity assertion and (9b) the `warning`-swap contrastive pair; E-04/V-04 add the per-rule count delta. Added F-08. |
| PR-003 | LOW | IN-SCOPE | A. Correctness | E-03 "followed within 80 characters on the same sentence by a hex token of 7 to 40 characters" | "same sentence" was not mechanically defined and a pure `[0-9a-f]{7,40}` token matches English words (`defaced`, `deadbeef`-style). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Defined a named regex over the two-line window, whole words, hash must contain a digit; E-05 (4) adds the `defaced` negative. |
| PR-004 | LOW | IN-SCOPE | F. UX / operability | `doctor.build_remediation` "`title = detail if len(detail) < 60 else rule`" and its comment "aw doctor summary groups on (title, summary_fix)" | A path-interpolating detail would fragment `aw doctor` summaries into one group per citation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 makes `detail` a constant under 60 chars; the cited path goes in `observed`, both remedies in `recovery`. |
| PR-005 | LOW | IN-SCOPE | E. Testing | E-05 case (8) "gitignored or `__pycache__`"; `artifact_core._cached_ignored_dirs` runs `git ls-files --ignored` | A `.gitignore` in a tempdir without `git init` is never honored, so the gitignored half was unreachable as written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (8) split: `__pycache__` (no git) and a `git init` fixture for `.gitignore`, skip-with-reason if git absent. |
| PR-006 | LOW | IN-SCOPE | E. Testing (baseline) | E-07 "suite pass count equals E-01's plus the new tests"; "wall-clock increase under 1 second" vs F-05 `real 0m28.041s` | Pass-count parity is load-sensitive, and a sub-second delta on a 28s end-to-end run is below its noise, so neither bar was decidable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Compare FAILED node-id sets with re-run-alone for a post-only failure; time the new function directly with `perf_counter`, end-to-end time as context. |
| PR-007 | LOW | IN-SCOPE | G. Executability (contract) | Gate "STOP conditions: ..." | The gate had no scope-fence declaration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a scope-fence sentence (declaration, justify via `--scope-reason`), no stop-on-scope wording. |
| PR-008 | LOW | IN-SCOPE | Spec sync | F-06 "No spec or doc enumerates check rules by id"; `rg` finds rule ids in e.g. the attention-registry spec and `docs/cli-output-contract.md` | The F-06 wording overstated the measurement; the conclusion (no catalog this rule must join) still holds. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec/documentation sync section restated precisely. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Exempt before or after dedup? | Exempt per occurrence, then dedup | Dedup first (hides mixed pairs); report every occurrence (noisy) | Review re-scan found 4 mixed pairs; `check_spec_test_citations_for_text` dedups by path | yes |
| D-2 | How to prove the rule is advisory when the tree already exits 1? | `rule_spec` severity + `drift_exit_code` contrastive pair + per-rule count delta | Exit-code parity alone | `/plan-review` rubric G evidence-feasibility convention; `aw check all --agent` exit 1 at `bd8b8e993` | yes |
| D-3 | Hash token shape | Whole-word hex 7..40 containing a digit | Any hex 7..40 | Digit-requiring form re-measured to exempt the same 21 citations | yes |
| D-4 | Constant or interpolated `detail`? | Constant under 60 chars, path in `observed` | Interpolate path | `doctor.build_remediation` title fallback and summary grouping comment | yes |
