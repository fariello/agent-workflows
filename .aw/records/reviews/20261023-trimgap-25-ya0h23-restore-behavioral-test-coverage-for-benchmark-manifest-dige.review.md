# Review findings: plan ya0h23

- Subject-Id: ya0h23
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `6b94e8d4a`. The plan was byte-identical to the lane input and already committed at `eea26ee60` (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 25), one new test module.

Verified at the lane HEAD:
- `benchmark_manifest._digest`, `Ceilings.digest`, `BenchmarkManifest.digest` (docstring "usage is a RESULT, not identity"), `make_ceilings`, `build_manifest` (writes `identity["ceilings_digest"] = ceilings.digest()`) and `manifest_from_dict` exist as described. `tests/test_benchmark_corpus.py` `_sample_manifest` uses the keyword set the plan cites.
- `tests/test_benchmark_manifest_digest.py` does not exist; sibling `btubm6` declares a different path (`tests/test_benchmark_corpus_restored_behavior.py`), so Scope-Paths are disjoint.
- The plan already handled the probe-sees-committed-HEAD trap (E-02 commits first), unlike several siblings.
- Re-ran the three `return-none` probes over the control file under `-m core`: all `survived`, `baseline_failing: 0` (F-02 reproduces).
- Re-ran all six E-01 assertions in-process against the real module and each `return None` monkeypatch: real module passes all; each mutant fails (a) and (d) plus one or two others (F-04 reproduces; recorded as plan F-06).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Validation (satisfiable bar) | old E-03 "passes within the core tier's 30s budget"; sibling `s461lz` F-07 bare run 34.93s | The core tier already exceeds 30s on this host before this plan, so E-03's bar was unsatisfiable for reasons outside scope; V-03 also did not show the module is core-collected. | all Low | FIXED | E-03/V-03 require a `--collect-only -m core` listing and an exit-0 bare run; a budget block is pasted verbatim and counts only if a new-module test is among the slowest. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (evidence sufficiency) | old E-02 "`mutant_failing` at least 1"; old V-02; old V-01 diff | V-02 did not demand `head:`, `baseline_failing: 0` or that the kill come from the new module (a count is not attribution), and did not handle `error` verdicts; the no-production-change diff checked only the working tree, which is empty after a commit. | all Low | FIXED | E-01 records `<base>`; E-02/V-02 demand `head:`, `baseline_failing: 0` and a `newly_failing` entry from the new module; `<base>..HEAD` diff added. |
| PR-003 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` | Gate lacked the paste-actual-output rule, scope-fence declaration wording with `--scope-ack`, staged-set check, and conditional finalize ownership; it implied a hand move to `executed/`. | all Low | FIXED | Gate rewritten as a full execution contract. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does a pre-existing core-tier wall-time overrun fail this plan? | No, record it verbatim; it counts only if a new-module test is among the slowest | Keep the 30s bar (unsatisfiable on this host) | `conftest.pytest_sessionfinish`; sibling `s461lz` D-2, `di5puw` D-2 | yes |
| D-2 | Keep assertions (b) and (e), which kill no `return-none` mutant? | Keep | Drop them as non-killing | They pin the equal-content and usage-is-not-identity contracts `benchmark_reports` relies on (plan F-05); behavior coverage, not only mutant kills, is the item's remedy | yes |
