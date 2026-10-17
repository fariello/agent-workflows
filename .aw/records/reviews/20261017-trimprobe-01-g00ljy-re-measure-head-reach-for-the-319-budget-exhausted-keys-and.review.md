# Review findings: plan g00ljy

- Subject-Id: g00ljy
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `3093b4c7c`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `b1mx2w` `## Rollup mutation results`: 747 rows, 319 with `Final verdict` `budget-exhausted`; reach
  292 `reached`, 25 `subprocess-only`, 2 `unreached` (`render_stream.py::_status_glyph_char`,
  `render_stream.py::Palette.status`); operators 278/29/8/4; 79 distinct modules (F-01 correct; backlog
  `lrnh5f` body says 54, discrepancy correctly flagged by E-01).
- `git diff --name-only 86f0d88d 476c7b7bd -- agent_workflows`: 25 files; 79 of the 319 keys are in 11
  of them (F-02 correct); 21 test files added in that range (F-02 correct). 31 production files changed
  through current HEAD, so the plan's re-measure at execution HEAD is warranted.
- `## All Candidate Production Keys` `Surviving Contexts` summed over the 292 reached keys: 25,601 (F-05).
- At current HEAD all 319 qualnames resolve via `tools.replay_coverage_diff.extract_functions` and every
  recorded operator is accepted by `tools.mutation_probe.apply_operator` (0 key-gone, 0 replaced).
- `hpjj44` `## Derived properties` has exactly one row per key for all 319, and the top-exclusive-lines
  file exists as `19313eed^:<path>` for all 319 (control file `none` will not occur at this HEAD).
- `tools.mutation_probe._node_id_to_selector("tests.test_comms_acks::<test>", ".")` yields
  `tests/test_comms_acks.py::<test>`, which collects 1 item.
- `tools/replay_coverage_diff.py` `run_baseline` stdout fields match E-02's list; `.aw/state/` is
  gitignored (`.aw/.gitignore` `/state/`); `records/research/INDEX.json`/`INDEX.md` are gitignored so
  only the doc is committed; `aw research new ... --slug budget-probe` dry run succeeds.
- Partition simulation with the plan's rule over the `86f0d88d` context counts: `P2` 259 keys at
  7,106s, `P3` 33 keys at 8,103s (largest single key N=3150, about 1,522s).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Rubric C/G (capacity) | plan `## Goal` "each probe plan fits under its own 10,800s cap"; review partition simulation `P3` 8,103s est | The partition rule bounds only `P2`; `P3` gets "the rest" with no check. Simulated `P3` is 8,103s survivor-only est, before file-level fallbacks and controls, so Order 03 may exceed its cap and the Goal's claim was unverified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now sums `P3` est_s and writes a `### Capacity warning` naming the overflow keys when above 7,200s (no auto-repartition, a further plan is a human scope call); Goal reworded to what the rule guarantees; V-03 demands the `P3` sum and warning or its absence. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (ambiguous mechanism) | E-03 "its collected item count `N` from `collect.txt`"; `tools.mutation_probe._node_id_to_selector` signature `(node_id, wt_dir)` | How a context maps to collected items (parametrize suffixes) and how to call `_node_id_to_selector` were unspecified; a context matching nothing would silently yield N=0 and an under-estimate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 specifies the call form, the exact-or-`[...]`-suffix match rule, surviving files as the selectors' file parts, and an UNMAPPED context count; V-03 demands it. |
| PR-003 | LOW | IN-SCOPE | Rubric G (edge cases) | E-03 `key-gone` and CONTROL FILE clauses | `key-gone` did not cover a deleted module file; control-file ties had no tie-break. | all Low | FIXED | Added module-absent case and path-ascending tie-break. |
| PR-004 | LOW | IN-SCOPE | Rubric E (evidence command) | V-04 "`rg -c ...` scoped to `## Probe queue`" | `rg -c` cannot scope to a section as written. | all Low | FIXED | V-04 gives a concrete `sed` range piped to `rg -c`; capacity-warning keys are bullets so they do not inflate the count. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | If `P3` is estimated over budget, should Order 01 split it into a new partition? | Record a capacity warning; do not repartition | Auto-create `P5`/split `P3` (adds a plan the Set does not have, a scope decision); ignore | Set orchestrator `roi8f1` `## Child IPDs` fixes five children; Order 02/03 E-02 already stop at cap with `budget-exhausted` and Order 05 files those keys | yes |
