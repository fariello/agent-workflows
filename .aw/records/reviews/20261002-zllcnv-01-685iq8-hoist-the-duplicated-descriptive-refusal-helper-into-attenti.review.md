# Review findings: plan 685iq8

- Subject-Id: 685iq8
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `99d432546` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Re-verified (gitignored probe, no production edit):
- `def _refuse_unsafe_descriptive` at `agent_workflows/backlog.py:772`, `agent_workflows/specs.py:35` and
  `agent_workflows/status_set.py:1878` (which delegates to backlog via a function-local import). There is also a
  function-local `from agent_workflows.specs import _refuse_unsafe_descriptive` at `agent_workflows/releases.py:1367`,
  with two calls passing `""`.
- Cross product of the 8 real verbs, 2 modes and 12 values (the plan's 9 plus `"a\x85b"`, `"\ta"`, `"a\u2028b"`):
  the three helpers diverged 14 times, every divergence at `verb=""`.
- `attention_contract` imports only `re`, `typing` and `lifecycle_dirs` (`agent_workflows/attention_contract.py:42-45`).
  `releases.py:22` already imports it as `A`.
- `python3 -m pytest -o addopts="" tests/test_backlog_descriptive_safety.py tests/test_specs_releases_descriptive_safety.py tests/test_status_set_descriptive_safety.py`
  -> `53 passed`.
- `aw releases new --dir <scratch> --version $'a\nstatus: shipped' --summary x` -> `aw releases new: --version must not contain embedded newlines`.
- Carriers resolve: `303k5n` (open backlog), `deftzy` (pending plan), `m5csyi` (graduated).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing (proof of preservation) | E-03 to E-05 alias every route to one function; E-06/V-03..V-05 compared routes "against the E-01 baseline" while E-01 only asserts live-route agreement | After the hoist, all four routes call the same function, so comparing one route to another is tautological. The only real pre-hoist record was transient pasted output, so the tests themselves could not detect a body changed during the move. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now freezes the baseline as an 18-row literal suffix table in the test file, captured from the unmodified `specs` copy. Every later assertion and V-item compares against that table, never route against route. |
| PR-002 | MEDIUM | IN-SCOPE | E. Test lifecycle | E-01 "pinning that `backlog` emits the leading `': '`" | E-01's empty-verb assertion describes pre-hoist state. Kept in the committed file, it fails after E-03 by design, which would leave the new test file red. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | It now lives in its own named test that E-06 replaces with the post-hoist unprefixed pin. Its pre-hoist pass is pasted in V-01 as the record. |
| PR-003 | LOW | IN-SCOPE | G. Doc sync carried in an E-item | `specs.py:30` banner "ported from backlog dtg7dz"; plan's Spec/documentation sync | The Spec/documentation sync section required updating the banner at E-04, but E-04 never said to. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to E-04. |
| PR-004 | LOW | IN-SCOPE | G. Live-artifact criterion | V-06 (b) | The full-suite check had no baseline to compare against, and the tree may not be all-green. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Failing node ids are now compared against a bare run made before any edit. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the pre-hoist behavior be frozen so post-hoist tests are not tautological? | A literal `(bound_length, value) -> suffix` table, with each verb applied as a prefix | A full 8x2x9 literal table (exact but bulky); a pickled snapshot file (adds an undeclared fixture path) | Probe shows the message depends on the verb only through its prefix (0 nonempty-verb divergences); the plan's Scope-Paths allow only the one test file | yes |
