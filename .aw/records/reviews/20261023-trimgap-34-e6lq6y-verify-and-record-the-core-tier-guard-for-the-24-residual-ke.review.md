# Review findings: plan e6lq6y

- Subject-Id: e6lq6y
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e19e6895b`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `tools.mutation_probe.apply_operator(src, qualname, op)` returns changed source for all 24 F-02 keys with
  the stated operators (24 rows, all True).
- F-02 `wall_s` column sums to 2203.36s, matching the stated 2203.4s total.
- F-03 carrier assignments: every one of the 16 named non-1z19cn keys appears in its named sibling plan
  (`v44udc`, `sbcmke`, `j77z5h`, `qx3ppg`); the three benchmark keys are in `1z19cn` (reviewed this run).
- `y4bt1c` and `33f8tn` exist in `executed/` and name `validate_envelope_header`/`_dispatch` and
  `resolve_source_root`/`migrate_local_lanes_to_untracked` respectively.
- `wo21z5` `## Method` step 5 names the longest-existing-file-prefix rule of
  `tools.mutation_probe._node_id_to_selector`, which E-01 cites.
- `tools/replay_coverage_diff.py baseline` prints `head:` and `functions:` lines and writes `baseline.json`
  with per-function `contexts` (`dynamic_context = test_function`), so E-01 and V-01 are producible.
- `.aw/state/` is gitignored (`.aw/.gitignore` `/state/`), so `sel.tsv` scratch is not committed.
- `19313eed` resolves as a commit, so E-05's `19313eed^` mining source exists.
- Probe verdicts are `survived`, `killed-by-import`, `killed`, `error`, `invalid` (`tools/mutation_probe.py`).
- Probes not re-run at review (about 37 minutes of probing; that measurement is the plan's own work).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Execution contract (rubric G) | plan `## Approval and execution gate` | Gate lacked the hard-MUST paste-actual-output wording, a declarative scope fence with `--scope-reason`/`--scope-ack` (the latter is the expected case when E-05 adds nothing), the no-production-change rule, and runner versus hand `aw ipd finalize` ownership; it implied a hand move to `executed/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the Set's standard contract (sibling `92tzo6`). |
| PR-002 | LOW | IN-SCOPE | Rubric E (evidence feasibility) | plan V-06, Required tests `<execution base>` | `<execution base>` was cited by V-06 and Required tests but recorded by no item. | all Low | FIXED | E-01 records the baseline's printed `head` as `<execution base>`; V-01 demands it pasted. |
| PR-003 | LOW | IN-SCOPE | Rubric D/E | plan E-05 trigger list; `tools/mutation_probe.py` `verdict = "killed-by-import"`; plan Goal | E-05's trigger named only `survived` and dirty baselines, leaving `killed-by-import` (only collection errors) and `error`/`invalid` unhandled; the Goal demanded 24 direct kills, contradicting the E-05 restore path. | all Low | FIXED | E-05 enumerates every non-`killed` verdict; Goal now accepts a kill from either E-02..E-04 or the E-05 re-probe. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Treat `killed-by-import` as guarded? | No: route it to E-05 | Accept it as a kill | `tools/mutation_probe.py` assigns it when every confirmed newly failing id is a collection error, which is not a behavioral assertion | yes |
| D-2 | Re-run the 24 probes during review? | No; verify feasibility and carriers only | Re-run all probes | Probing at execution HEAD is the plan's E-02..E-04; review verified operator applicability and tool output shape | yes |
