# Review findings: plan i44j8w

- Subject-Id: i44j8w
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`c7ce6e468`), so no snapshot was needed. `aw ipd lint --phase author` was clean before the review and `--phase review-finalize` is clean after it.

Evidence measured at review:

- The defect reproduces at HEAD. With `TMPDIR` set to a polluted container (`.aw/records`, `.agents/plans`, `git init`), the twelve modules named in Required tests gave `41 failed, 280 passed`, across exactly the 11 modules listed in F-01.
- The proposed mechanism works. In a gitignored scratch copy of the tree under `.aw/state/` with the E-01 helper applied (ceiling check first in each loop; `is_project_dir` refuses a ceiling):
  - polluted run: `1 failed, 320 passed`, where the one failure is `test_specs_date_containment::test_absolute_path_date_refused` and the polluted name contained a hyphen;
  - with a hyphen-free polluted name: the date-containment, nonsurveyable and no-project modules gave `36 passed`;
  - unpolluted run: `321 passed`;
  - `attention --agent` and `specs check --agent` from a polluted non-project child exited 2 with `cannot-run`;
  - full scratch suite: `4 failed, 8441 passed`. All 4 failures are scratch-copy artifacts (`doctor.version-unknown` from the scratch git, and a history commit missing from the scratch repo), and all 4 pass on the real tree.
- The E-02 basetemp mechanism works. A session-scoped autouse fixture taking `tmp_path_factory` that appends `getbasetemp()` to `AW_PROJECT_CEILING` made `find_project_root(tmp_path) is None` pass under `-n auto` and `-n0` with `--basetemp` inside the AW scratch checkout. Without the fixture, the same test fails because the climb resolves to the enclosing checkout.
- Cost: `_project_climb_ceilings()` takes about 130 microseconds per call, which is imperceptible.
- All scratch artifacts were deleted after measurement.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Verification feasibility | V-04/E-04 "private `TMPDIR`" with no naming constraint; `tests/test_specs_date_containment.py` `_assert_target_bounded`; review run with `/tmp/poll-<rand>`: `test_absolute_path_date_refused` FAILED even with the fix | An executor who named the polluted container with a hyphen (common, e.g. `poll-xyz`) could never reach the demanded `0 failed`. F-03 identified the hyphen hazard but did not carry it into the validation steps. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests, E-01(b), E-04 and V-04 now require a hyphen-free `tempfile.mkdtemp(prefix="awpoll")` container. F-03 records the re-measurement. |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Anti-regression baseline | E-04 "`python3 -m pytest` pass with zero failures"; V-04 had no pre-edit comparison | There was no pre-edit baseline, so "zero failures" was an absolute bar that would trip on unrelated suite failures, and there was no proof the polluted run failed before the fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now first records (a) the bare-suite failing-id set, (b) the polluted twelve-module baseline, and (c) the pre-edit V-01 one-liner. V-01 and V-04 compare against these, and E-04 requires no new failing ids. |
| PR-003 | MEDIUM | IN-SCOPE | E. Verification reachability | V-02 `pytest ... -k ceiling` (no test is named with `ceiling` and in the default basetemp no ceiling test exercises basetemp); E-02 offered the private `config._tmp_path_factory` | V-02 could not show that the basetemp ceiling works, and E-02 left the mechanism open, including a private-API option. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now uses the session autouse fixture demonstrated at review. E-03 adds `test_tmp_path_does_not_climb_past_basetemp`. V-02 runs it with `--basetemp=.aw/state/bt-i44j8w` (inside this AW checkout) and checks the `tests/__init__.py` backstop with `env -u`. |
| PR-004 | MEDIUM | IN-SCOPE | C. Architecture / concurrent plan | Pending plan `ivq0nr` (`nj13xp`) Scope-Paths include `agent_workflows/project_context.py` and `tests/test_nonsurveyable_root_refusal.py`; its E-04 adds a `.git` return in `find_project_root` | F-04 claimed no conflict with `nj13xp` but knew only about `tests/test_finalize_sendback.py`. The sibling plan changes the same loop, and nothing defined how the two checks compose. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 now documents the overlap. E-01 puts the ceiling check first in each loop iteration, so behavior does not depend on landing order (the runner's merge gate handles textual integration). |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy / docs sync | Spec sync cited `.aw/records/specs/implemented/20260809-2211-01-...spec.md`, but the file is in `superseded/`; `_HOME_KEYS` has no reader; the CHANGELOG entry did not name the new env var | One citation was stale. One edit was a no-op (`_HOME_KEYS`; restoration already comes from `_SANDBOX_ENV`). The new public `AW_PROJECT_CEILING` variable was undocumented. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the spec citation and recorded that no live spec governs the climb (rg result). Marked `_HOME_KEYS` optional and explained the restoration path. E-04 now documents `AW_PROJECT_CEILING` semantics, and E-01 updates the docstrings. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` read "finalize the IPD to `executed` via `aw ipd finalize`" unconditionally | The gate lacked the honesty rule, a scope-fence declaration, a path-scoped `aw commit`, never-push, and conditional runner/hand finalize ownership, and it unconditionally instructed `aw ipd finalize`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate with the full execution contract. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the basetemp ceiling be wired? | Session-scoped autouse fixture taking `tmp_path_factory` | `pytest_configure` reading the private `config._tmp_path_factory` | Review demonstration: the fixture passes under `-n auto` and `-n0`, and the private attribute is unsupported API | yes |
| D-2 | Where does the ceiling check go relative to `ivq0nr`'s `.git` check? | First statement of each loop iteration | After the marker check (it would then depend on landing order) | `ivq0nr` E-04 text; a ceiling must never itself be a root, which requires checking before markers | yes |
| D-3 | Is the global (non-test) behavior change in scope, given that a user can no longer make `/tmp` itself an AW project? | Keep it (OQ-01 as authored) | Test-only ceiling via `AW_PROJECT_CEILING` | OQ-01 rationale; `upgrade_rehearsal.py` and `leak_sanitizer.py` already treat the system temp dir as non-project territory; no live spec governs the climb | yes |
