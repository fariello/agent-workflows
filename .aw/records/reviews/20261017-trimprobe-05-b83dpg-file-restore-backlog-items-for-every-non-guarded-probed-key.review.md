# Review findings: plan b83dpg

- Subject-Id: b83dpg
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `789e1ace5`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `b1mx2w` `## Rollup mutation results`: 319 distinct `budget-exhausted` keys; `## Filing plan` group 1
  is the 319-key `lrnh5f` item; z2xs98 grouped by (module, remedy shape) and captured
  `check-before.jsonl` in its E-01.
- `aw backlog new` flags match E-02 (`--summary`, `--set`, `--priority`, `--work-kind`,
  `--blocks-release`, `--body`, `--apply`); preview path matches the Scope-Paths glob.
- Only `planned` release record: `20260820-f33nrj-01-f33nrj-2-0-0.release.md`, so `--blocks-release next`
  resolves.
- `aw backlog check`: "all backlog items conform. 1078 backlog items checked."
- `tools.mutation_probe.ProbeResult` stores `baseline_failing` as an integer count only.
- Orchestrator `roi8f1` completion criterion 6 ("The Set changed no production code and no test
  file. Owner: b83dpg (E-03 (c))") is the obligation E-03 (c) must satisfy.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Rubric E (unsatisfiable evidence) | plan E-03 (d) "`aw check --agent` rule counts before E-02 and after"; `z2xs98` E-01 | No step captured the "before" counts, and E-03 runs after E-02, so the comparison could not be produced. `aw check` already reports 2 errors, so "no new error" needs a real baseline. | all Low | FIXED | E-01 now captures `check-before.jsonl` first. E-03 (d) compares per-rule counts and explains new findings, and V-01 proves the capture came before filing. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric E (wrong proof) | plan E-03 (c) "`git log --stat <Order 01 commit>^..HEAD -- agent_workflows tests`"; review F-04 (4), (6) | Other Sets' code commits (for example `work(c8bfp9)`) land on main between this Set's merges, so the range would show code changes the Set did not make. A plain `git show --stat` on a lane merge prints nothing, so a per-commit check would pass vacuously. | all Low | FIXED | E-03 (c) now finds each child's commits by id6 subject and diffs each against its first parent (`<hash>^1`); V-03 matches. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric A (dedupe false positive) | plan E-01 dedupe `rg ... .aw/records/plans/pending`; review F-04 (1) | The pending-plan search hits the Set's own `g00ljy` (2 keys named as calibration examples), which would mark those keys `owned-confirmed` by a plan that does not own their restore work. They would then be filed nowhere. | all Low | FIXED | The dedupe ignores this Set's own artifacts (`lrnh5f`, `*-trimprobe-*`). |
| PR-004 | MEDIUM | IN-SCOPE | Rubric E (unexecutable step) | plan E-02 EXCEPTION "on a test that also fails at HEAD"; `tools.mutation_probe.ProbeResult` `baseline_failing: int` | The JSON holds only a count, so "a test that also fails" cannot be identified as written. | all Low | FIXED | E-02 re-runs each such JSON's `selection` unmutated at HEAD and pastes the failing node ids; V-02 requires that output. |
| PR-005 | LOW | IN-SCOPE | Rubric G (wrong command) | plan E-01 "`aw find backlog <module stem>`", E-03 "`aw index backlog`"; review F-04 (2), (3) | `aw find` matches id6/status/Set/filename, not body text (`no artifact matched selector 'storage'`), and `aw index backlog` is unsupported. | all Low | FIXED | Removed `aw find` from the dedupe (pointing to the `aw backlog new` duplicate report as the advisory second check) and dropped `aw index backlog` with the reason. |
| PR-006 | LOW | IN-SCOPE | Rubric G (ambiguous grouping) | plan E-01 "Group the gaps by module" vs one Remedy Shape column per group; `z2xs98` Scope | A module with keys of mixed verdicts would need several remedy shapes in one row. | all Low | FIXED | Group by (module, remedy shape), as `z2xs98` did. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a key named only in this Set's own plans count as owned? | No; ignore Set-own hits in the dedupe | Count them (orphans the key); dedupe only against backlog (would miss genuine pending restore plans) | review F-04 (1); `lrnh5f` is the item this Set closes, not a restore carrier | yes |
| D-2 | How to prove the Set changed no code when main interleaves other Sets? | Per-child commits by id6 subject, each diffed against its first parent | Commit range (false positives); trust the runner's scope gate (not pasted evidence) | review F-04 (4), (6); `roi8f1` completion criterion 6 | yes |
