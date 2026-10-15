# Review findings: plan lyqn1t

- Subject-Id: lyqn1t
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`f7050c14f`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review. `--phase pre-transition` reported `check.ipd-uncarried-obligation` on all three Deferred rows (fixed, PR-002).

Claims verified against the tree: `runner_shared.driver_begin` launches with `env={**env_builder(), **begin_baseline_env(isolated)}`, `stdin=subprocess.DEVNULL`, `cwd=str(repo)`, and appends `--run-id` only when `run_id` is set. `runner_shared.begin_baseline_env` returns `{"AW_ISOLATED_BASELINE": "1"} if isolated else {}`. `oc_runipd.driver_begin` and `agy_runipd.driver_begin` both delegate binding `pinned_child_env`/`pinned_module_argv`. `git show 19313eed^:tests/test_lane_tool_identity.py` contains `TheBeginPinSurvivedTheMove`. The stale comment ("no live guard currently asserts this; it read the env this builds") is present in `runner_shared.driver_begin`.

Prototype run at review under gitignored `.aw/state/` (then deleted): the E-01/E-02 shape passed for `oc`/`agy` x `isolated` False/True under a cleared `os.environ`. A probe with an UNPINNED builder and the environ NOT cleared showed `AW_PIN_KEEP_ROOT` inherited from the runner (this process's env carries `AW_PIN_KEEP_ROOT` and a `PYTHONPATH` with a package root), which is PR-001. The rewritten V-02 in-process mutation (`mock.patch.object(runner_shared, 'begin_baseline_env', lambda _i: {}).start()` before `pytest.main`) made an overlay test FAIL (`1 failed`) while the same test passed unmutated (`1 passed`), with no source change.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D/E. Non-vacuity of the pin assertions | `runner_shared.pinned_child_env` starts from `os.environ.copy()`; runner env carries `AW_PIN_KEEP_ROOT=<root>` and `PYTHONPATH=<root>:...`; review probe printed `INHERITED_KEEP_ROOT <root>` for an unpinned builder | Run under `aw oc run` or from a pinned shell, the test process inherits the pin markers, so E-01's `AW_PIN_KEEP_ROOT`/`PYTHONPATH` assertions could pass with an unpinned builder (vacuous whenever the inherited root equals the package root, e.g. the main checkout), and E-03's "spied env lacks AW_PIN_KEEP_ROOT" would fail depending on environment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/E-02/E-03 now run under `mock.patch.dict(os.environ, <minus AW_PIN_KEEP_ROOT, PYTHONPATH, AW_ISOLATED_BASELINE>, clear=True)`; E-03 builds its unpinned env from that cleared environ and also asserts the root is absent from `PYTHONPATH`. |
| PR-002 | HIGH | UNDER-SCOPE | G. Lifecycle gate | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 3 obligation(s) name no durable carrier: deferred row 1, deferred row 2, deferred row 3` | The plan could not pass its own pre-transition gate, so it could not finalize after execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each Deferred row. |
| PR-003 | MEDIUM | IN-SCOPE | E. Verification feasibility | V-01 "with subtests"; `import pytest_subtests` -> `ModuleNotFoundError`; V-02 "temporarily patched ... (then reverted)" while E-04 edits `agent_workflows/runner_shared.py` | `unittest` subtests do not appear in `pytest -v` without `pytest-subtests`, so V-01's demand was not producible. V-02's source mutation of the same file E-04 edits risked a revert clobbering E-04 or a committed mutation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 uses `pytest.mark.parametrize` (four ids); V-02 now uses a demonstrated in-process mutation that never touches source, plus a `git status` check. |
| PR-004 | LOW | IN-SCOPE | E. Assertion precision | E-01 "argv contains `ipd`, `begin`, ..., `--dir`"; E-02 run-id case | Containment did not pin order or the `--dir` value, and the no-`run_id` path was not asserted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 asserts the exact post-prefix argv including `/nonexistent`; E-02 asserts `argv[-2:]` and the absence of `--run-id` without `run_id`; E-01 also asserts rc 0. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `- Scope-Paths:`; OQ-01 `Owner: none`; E-04 quoted text spans two comment lines | The gate lacked the scope fence, honesty rule, `aw ipd begin`, conditional finalize ownership, and never-tag rule; the plan file was not in Scope-Paths; `Owner: none` is a placeholder; E-04 did not locate the wrapped comment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full contract and the plan path; owner set to `plan author`; E-04 now locates the comment inside the `subprocess.run(` call above the `env=` line. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to make the pin assertions independent of the inherited runner env? | Clear `AW_PIN_KEEP_ROOT`, `PYTHONPATH`, `AW_ISOLATED_BASELINE` via `mock.patch.dict(..., clear=True)` | Assert root differs from inherited value (fails in main checkout); skip under pinned env (hides coverage) | Review probe output above; `runner_shared.pinned_child_env` | yes |
| D-2 | Parametrize vs `subTest`? | `pytest.mark.parametrize` | `subTest` (invisible in `-v` without `pytest-subtests`) | `import pytest_subtests` failed in this env | yes |
| D-3 | How to run the V-02 mutation? | In-process `mock.patch.object(...).start()` before `pytest.main` | Temporary source edit + revert (collides with E-04) | Demonstrated `1 failed` mutated vs `1 passed` unmutated | yes |
| D-4 | Accept OQ-01 (no identity pin)? | Yes, as authored | Restore `assertIs` | Backlog `o0gy5v` "only behavioral outcomes may be restored ... (P16)" | yes |
