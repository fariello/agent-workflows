# Review findings: plan we3kkb

- Subject-Id: we3kkb
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `45777dc77`. Plan committed and byte-identical to the lane
input (sha256 `1db8c7ba...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`.
Not an orchestrator.

Verified:
- `ast` recount of `def test*` names at `19313eed^` vs HEAD: missing 4 / 19 / 79 / 34 (F1). There are no duplicate
  names in any deleted file. Missing names elsewhere in `tests/`: `test_agent_and_json_streams_are_ansi_free`
  (`tests/test_cli_quality_gates.py`) and `test_format_duration` (`tests/test_agy_run.py`), which matches F2.
- Lane-manifest missing names are `test_its_docstring_states_it_has_no_consumer`, `test_part_i_...`,
  `test_part_ii_...`, `test_restored_copy_passes_again`. All four are named with reasons in the HEAD
  module docstring (items 1, 3, 4). The backlog's `test_part_iii_lane_inputs_file_has_no_write_bit` is
  absent at `19313eed^`, which only has `test_part_iii_a_change_is_a_new_revision_not_an_edit`.
- Ran the E-01 replay command: exit 0. Results: `pass` 21/21, `pass` 20/20, `fail` 76/3, `pass` 34/34;
  `overwrote_head_path` true for all four; `git status --short` empty afterwards. Nodeids have the form
  `tests.<module>[.<Class>]::<name>`.
- Executed `dyiasf` accounts for every deleted class of `test_release_readiness.py` (`## Deferred`
  "ACCOUNTING OF THE DELETED FILE", F-07).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric D (silent false negative) | plan E-02 rule (5); `8dyt88` E-04 `replay-unverified` class | Rule (5) made `covered-by-shared-reach` the fallback whenever the re-diff row lists no exclusive function. A re-diff that errored or ran 0 tests also lists none, so an unmeasured file would be declared covered. Names that replayed `skipped` or had no nodeid had no rule. | all Low | FIXED | Rule (5) now treats a non-`pass`/`fail` or `tests_count` 0 re-diff as `gap`. New rule (6) makes `skipped`/`not-run` a `gap`. E-02 outcome updated. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (executability) | plan E-02 rule (2) grep-only; executed `dyiasf` `## Deferred` accounting and F-07; HEAD `test_release_readiness.py` names share none with the deleted file | `test_release_readiness.py` was rebuilt under new names, so the grep-only `moved` rule could never fire. The 19 names would therefore fall to `gap`/`covered`, even though `dyiasf` records which ones were restored, not restored, or refused. | all Low | FIXED | Rule (2) now accepts an executed rebuild plan's mapping to a named HEAD test. Explicitly-not-restored arms route to rule (1). F4 cites the accounting. |
| PR-003 | LOW | IN-SCOPE | Rubric G (join key) | `tools/deleted_test_replay.py` `_parse_junit_xml` nodeid `tests.<module>[.<Class>]::<name>` (review replay) | The name-to-outcome join was unspecified. | all Low | FIXED | E-01 matches on the part after `::` (names are unique per file) and records `not-run` when nothing matches. |
| PR-004 | LOW | IN-SCOPE | Rubric G (verification strength) | plan V-01, V-02 | V-01 had no before snapshot of the worktree list. V-02 only re-verified the evidence for two of the seven classes. | all Low | FIXED | V-01 takes the list before and after and counts `not-run` names. V-02 now names the evidence for every class. Review measurements are recorded as F5. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Class for a passing name in a file whose re-diff is unmeasured, or for a skipped/not-run name? | `gap` (filed by Order 06). | `covered-by-shared-reach` (REJECTED: unmeasured); a new class (REJECTED: Order 06 already files `gap`, so no downstream change is needed). | `8dyt88` D-1 `replay-unverified` precedent. | yes |
| D-2 | May a rebuild plan's accounting establish `moved` without a same-named test? | Yes, with the replacing HEAD nodeid and a body comparison. | Grep only (REJECTED: cannot fire for a renamed suite). | Executed `dyiasf` accounting. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
