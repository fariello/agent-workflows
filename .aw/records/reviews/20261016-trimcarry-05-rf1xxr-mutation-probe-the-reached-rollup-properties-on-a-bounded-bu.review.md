# Review findings: plan rf1xxr

- Subject-Id: rf1xxr
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `5cf4fb46a`. Plan committed and byte-identical to the lane
input (sha256 `034d1a42...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`.
Not an orchestrator. Prerequisite Order 03 (`8dyt88`) is `reviewed`, not yet executed, so `## Key reach`
does not exist yet; the plan correctly gates on `executed:8dyt88`.

Verified:
- `hpjj44` `## Triaged not mutated` holds 747 `production-key` rows; joined with `## Derived properties`:
  739 `behavioral`, 5 `pin-retired`, 3 `property-unidentifiable` (plan F4 correct); operators
  `return-none` 616, `raise` 81, `negate-return` 23, `return-false` 19, `n/a` 8. The 8 `n/a` are exactly
  the pin-retired and unidentifiable keys.
- `tools/mutation_probe.py` `main`/`probe`: CLI flags as described; verdicts `killed`, `killed-by-import`,
  `survived`, `invalid`, `error`, `timeout`; `--extra-test` reads `COMMIT^:PATH` and records
  `extra_tests_overwrote`; JSON carries `head` and `checkout_status_changed`.
- `rq3q7v` V-02 control `"wall_s": 17.26` (plan F2 correct); `hpjj44` `## Mutation totals` 3466.82s (F1).
- Live probe at review: `mutation_probe.py agent_workflows/ipd_lifecycle.py::_scope_match --op return-false --format json -- -n 2 -m "not slow and not livecorpus" tests/test_scope_match.py`
  -> `killed`, `newly_failing_total: 2`, `checkout_status_changed: []`, `wall_s: 11.46`; `git status --short`
  empty and `git worktree list` unchanged before and after.
- `.aw/state/` is gitignored (`.aw/.gitignore` `/state/`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric D (false `unguarded`) | `tools/mutation_probe.py` `probe` default `["-n", "auto", "-m", "not slow and not livecorpus"]` (no path); `pyproject.toml` `testpaths` 19-module list; review `--collect-only -m "not slow and not livecorpus"` -> `707/712 tests collected` vs with `tests/` -> `9195/9494` | E-02 told `subprocess-only` keys to use "no `--` argument (the full default selection)". That default names no path, so pytest uses the narrowed `testpaths` (about 8% of the non-slow suite). A survivor on that subset would record a false `unguarded`, and Step 0 claimed the probe "ignores `testpaths`", which is false for the no-argument case. | all Low | FIXED | Selection is always explicit: `-n auto -m "not slow and not livecorpus" tests/` for subprocess-only; Step 0 corrected with the measured counts; E-02 outcome and V-02 require an explicit path argument. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (missing input) | `.aw/.gitignore` `/state/`; V-01 "equal to Order 03's `keys.txt`"; this plan runs in its own isolated worktree | V-01 compared against Order 03's `keys.txt`, a gitignored scratch file that does not travel to this plan's worktree. | all Low | FIXED | E-01 and V-01 derive the key set from committed sources (`hpjj44` `## Triaged not mutated` and `## Key reach`). |
| PR-003 | MEDIUM | IN-SCOPE | Rubric D (stale non-probe verdicts) | E-01 assigns `key-gone`/`unguarded-unreached` from Order 03's reach without a probe | Reach is measured at Order 03's HEAD; Orders 04 and Set siblings or unrelated commits may land before this plan runs, so a no-probe verdict could rest on stale reach. | all Low | FIXED | E-01 records both heads and a `git diff --stat` over `agent_workflows tests`; affected keys fall back to `to-probe` and changed tests are listed as a caveat. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric E (honest measurement limit) | `8dyt88` E-03 `## Method` selection-limit sentence; `tools/replay_coverage_diff.py` `_make_rc_content` `patch = subprocess` | `unguarded-unreached` and OQ-01 said "no surviving test executes it", but slow/livecorpus tests were excluded, and OQ-01 mis-described subprocess reach (a key absent from `functions` was not hit in a traced subprocess either). Also the reached-key survivor selection omitted the marker filter reach was measured under. | all Low | FIXED | Verdict reason must name the non-slow selection and Order 03 head; OQ-01 resolution corrected; reached selections carry `-m "not slow and not livecorpus"`. |
| PR-005 | LOW | IN-SCOPE | Rubric G (procedure gaps) | `mutation_probe.py` `--extra-test` overwrite and `extra_tests_overwrote`; `rq3q7v` E-02 step 5 | Control not stated as conditional on survivor `survived`; restored/recreated paths are overwritten silently; retry operator selection unspecified; budget stop rule ambiguous (start vs finish); preflight only for narrowed selections; `checkout_status_changed` not recorded. | all Low | FIXED | E-02 steps clarified accordingly. |
| PR-006 | LOW | IN-SCOPE | Evidence drift | Step 0 "`return-none` 618" | Operator count was 618; measured 616 for the 747 keys. | all Low | FIXED | Corrected. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which selection for `subprocess-only` keys? | Explicit `-n auto -m "not slow and not livecorpus" tests/`. | Bare probe default (REJECTED: falls to 19-module `testpaths`); routine `make test` (REJECTED: same subset). | Review collect-only counts 707 vs 9195; `probe` default. | yes |
| D-2 | What if code changed between Order 03 and this run? | Keys in changed modules are probed rather than assigned a no-probe verdict. | Re-run Order 03 (REJECTED: out of scope); ignore (REJECTED: stale verdicts). | `8dyt88` E-02 baseline head; `run_diff` head check precedent. | yes |

No decision is `Reversible: no`. No finding left `OPEN` or `DEFERRED`.
