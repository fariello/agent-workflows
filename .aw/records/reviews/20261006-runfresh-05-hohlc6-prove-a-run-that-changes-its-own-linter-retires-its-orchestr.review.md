# Review findings: plan hohlc6

- Subject-Id: hohlc6
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T030816Z-4078927` at HEAD `2d4bf988f`. The plan was
committed and byte-identical to the sealed lane input (rev-6); no snapshot needed. `- Kind: child`. `aw ipd lint
--phase author` clean before; `review-finalize` clean after (an `IPD-Z602` advisory on E-03 was resolved by splitting it).
Dependencies `re15ol` and `vvqr34` are reviewed, not executed; `loaded_code.py` and `restart_decision` do not exist yet.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E testing / G | E-01 "make the child's lane integrate to the fixture's `main`"; integration revalidates with `runner_shared.SUITE_CHECK_ARGV` (bare pytest) in the fixture; self-finalize needs a receipt and E/V evidence | The lane + self-finalize path is unspecified and drags in gates unrelated to the mechanism. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Use `--no-isolate-worktree --no-self-finalize --no-validate` (precedent `tests/test_runner_stop_triggers_e2e._spawn_driver`); the fake turn commits on `main`. |
| PR-002 | HIGH | IN-SCOPE | A correctness | `checkout_pin.check_and_reexec` re-execs on a cwd/import mismatch; Order 02 `restartable` = imported root is the repo | A package copy that is not at the fixture root makes the run non-restartable, so the enabled case would be vacuous. | Low | FIXED | Package copied to the fixture root; spawn from the fixture with `PYTHONPATH=<fixture>`; OQ-01 amended. |
| PR-003 | MEDIUM | IN-SCOPE | E | `ipd_lifecycle._assert_rollup_touched_only_owned_paths`; `coverage_record.is_current` / `probe_cache_digest` | A dirty orchestrator refuses retirement for an unrelated reason; a coverage record from the real package might not match. | Low | FIXED | Fake turn commits; coverage written with the fixture's own module; F-03 added. |
| PR-004 | MEDIUM | IN-SCOPE | E | E-02 "a fresh `tool-identity-verified` event"; `assert_child_tool_identity` is called only under `if self_finalize` in `execute_item_core` | The demanded event is unreachable in a `--no-self-finalize` run. | Low | FIXED | Removed from E-02; covered by new E-05 (PR-008). |
| PR-005 | MEDIUM | IN-SCOPE | E | E-02 "compare the `state.json` snapshot saved by the restart with the final one" | The resumed process overwrites that snapshot; there is no readable copy. | Low | FIXED | Compare against an independent expectation and a `--prepare-only` options baseline; session map asserted. |
| PR-006 | LOW | IN-SCOPE | G | `--records-backend repository` / `aw install` in E-01; gate wording; slow marking | An install is unneeded; the gate lacked contract parts; the bare suite would deselect a `slow` file silently. | Low | FIXED | Records written directly; gate completed; `-m slow` command stated. |
| PR-007 | MEDIUM | IN-SCOPE | G right-sizing | `aw ipd lint` `IPD-Z602` on E-03 | E-03 bundled the mutation proof with the suite reconciliation. | Low | FIXED | Split into E-03 (mutation) and E-04 (bare suite) with V-03/V-04. |
| PR-008 | MEDIUM | UNDER-SCOPE | D / cross-child | spec `25kzda` 5.3b point 7; `re15ol` conventions defer the fresh-pin assertion to this plan | After PR-004 no plan in the Set proved the pin is re-established after a restart. | Low | FIXED | E-05: two-phase exec case asserting two `tool-identity-verified` events; `re15ol` cross-reference updated with a dated history note. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Fake host in a subprocess? | Fixture-local executable via `--opencode`/`--agy` | in-process patch (cannot cross the process boundary) | `tests/test_runner_stop_triggers_e2e._spawn_driver` | yes |
| D-2 | Lanes and self-finalize in the fixture? | Off | on (pulls in the revalidate suite run and finalize evidence) | `SUITE_CHECK_ARGV`; finalize gate | yes |
| D-3 | Where is 5.3b point 7 proved? | `hohlc6` E-05 | leave unproved; add to `re15ol` (already reviewed) | `re15ol` conventions note | yes |
