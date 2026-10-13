# IPD: Verify the h0tiaw restoration discharged krwj2o and pin that every conformance golden has a reader

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `krwj2o` (filed 2026-10-01 as a carrier from executed plan `zosxj4`, Set `zdjhug`) asks for two things: (F-04) restore the CLI quality and conformance gates deleted by trim commit `19313eed7` (`tests/test_cli_quality_gates.py`, `tests/test_cli_conformance_matrix.py`) so `tests/conformance_matrix.py` and the twelve goldens under `tests/fixtures/conformance_goldens/` are exercised again, and (F-05) refresh the stale `Fix:` remediation strings in `check_findings.human.golden`. MEASURED IN THIS LANE AT HEAD `075a7b9cf`, BOTH ARE ALREADY DONE by the independently filed Set `h0tiaw` (backlog `h0tiaw`, orchestrator `l8wvv3`, children `dq9bj9` and `9i2hge`, all `executed`): `tests/test_conformance_matrix_structure.py` (commit `3ec1c2d5a`, `work(dq9bj9)`) revives the structural matrix and alias gates, `tests/test_cli_quality_gates.py` (commit `67d026bcd`, `work(9i2hge)`) restores the seven renderer gates and reads all twelve goldens, and `check_findings.human.golden` now carries the `--to-id6 --apply` and `--rename --apply` strings the live renderer emits. Neither `h0tiaw` plan carries `- From-Backlog: krwj2o`, so nothing machine-readable records that `krwj2o` was discharged by `h0tiaw`. (The item has since moved `open` -> `graduated`, graduated to THIS plan by run `run-20261012T005606Z-2321569`, so this plan is now its only carrier and must execute for the item to close.) ONE RESIDUAL GAP survives the restoration and is in the item's own words ("twelve goldens ... are exercised again"): the restored reader iterates the four fixture names in `_fixtures()` crossed with three suffixes, so a THIRTEENTH `.golden` file dropped into the directory, or a golden orphaned by a fixture rename, is read by nothing and passes silently. Measured: `touch tests/fixtures/conformance_goldens/zzz_orphan.human.golden` then `python3 -m pytest tests/test_cli_quality_gates.py` reports `14 passed`. That is exactly the condition `krwj2o` and `h0tiaw` filed (committed reviewed bytes that no test reads), so the guarantee is currently a one-time measurement and not a gate.
- Scope: IN: (1) re-measure and record, with pasted output, that F-04 and F-05 are discharged by the `h0tiaw` Set at execution HEAD; (2) add ONE default-collected test to `tests/test_cli_quality_gates.py` asserting that the set of `*.golden` files present in `GOLDEN_DIR` equals exactly the set the module's fixtures and render suffixes read, so an orphaned or extra golden fails; (3) prove that test is sensitive with a reverted throwaway orphan. OUT: re-restoring anything `h0tiaw` already restored; the live per-leaf scenario sweep and the live fact-parity gate (carrier `2wowfy`, now pending plan `34iwyp`, Set `livesweep`); any change to `agent_workflows/` production code; any edit to the twelve golden files' contents; any edit to the executed `h0tiaw` or `zosxj4` plans.
- Scope-Paths: tests/test_cli_quality_gates.py, .aw/records/plans/pending/20261011-krwj2o-01-cqxq2a-verify-the-h0tiaw-restoration-discharged-krwj2o-and-pin-that.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: krwj2o
- Set: krwj2o
- Order: 1
- Highest E allocated: 04
- Author: opencode uri/its_direct/pt3-claude-opus-5.5-1m-us
- Id: cqxq2a

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: cqxq2a verified (set krwj2o, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed (review record 20261011-krwj2o-01-cqxq2a)
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006

- 2026-10-11 to-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `krwj2o`. Measured at HEAD `075a7b9cf` that both of the item's findings were already delivered by Set `h0tiaw` (filed separately, same root cause), so this plan does NOT re-restore anything: it re-measures the discharge with pasted evidence, closes the one residual gap the item's wording implies (an unread golden still passes silently; measured `14 passed` with a planted orphan), and carries `- From-Backlog: krwj2o` so the item's discharge becomes machine-readable. No `- Blocks-Release:` on the item, so none is inherited.
- 2026-10-11 draft (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `krwj2o`'s discharge provable and durable: record with pasted evidence that the deleted gates and the
stale golden strings were already restored by Set `h0tiaw`, and turn "every committed conformance golden
has a reader" from a one-time measurement into a default-collected test that fails on an orphan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure the discharge

- [x] E-01 RE-MEASURE F-04 AT EXECUTION HEAD. Confirm both revived modules exist and are default-collected
  (no `pytestmark = pytest.mark.slow`), and that they pass under a bare run of just those two files:
  `python3 -m pytest tests/test_cli_quality_gates.py tests/test_conformance_matrix_structure.py` (measured at review
  HEAD `66401aeb1`: `22 passed`). Confirm
  `tests/conformance_matrix.py` symbols `ANSI_RE`, `GOLDEN_DIR`, `build_matrix`, `required_scenarios` and
  `USAGE_ERROR_FLAG` each have at least one importer under `tests/` other than the module itself
  (`rg -lw <name> tests --glob '!conformance_matrix.py'`). If either module is missing, marked `slow`, or
  failing, STOP: the premise of this plan is false, set this item `blocked`, and report rather than
  re-restoring (re-restoration would need its own review). The two-module run goes through the configured
  `addopts` (which deselect `slow` and `livecorpus`), so a non-zero `passed` count that includes both modules'
  classes is itself the default-collection proof. BEFORE ANY EDIT, also take the bare-suite baseline
  (`python3 -m pytest`, bare) and record its summary line and failing-test names; E-04 compares against it.
  - Depends on: none
  - Expected outcome: both modules present, unmarked, and passing; each named symbol has a test importer; the
    bare-suite baseline is recorded.
  - Execution state: performed

- [x] E-02 RE-MEASURE F-05 AT EXECUTION HEAD. Show that `check_findings.human.golden` carries the live
  remediation strings (`grep -n 'Fix:' tests/fixtures/conformance_goldens/check_findings.human.golden`
  shows `--to-id6 --apply` and `--rename --apply`) AND that it matches today's render, which is what
  `DeterministicByteGoldenTests.test_human_plain_goldens_stable` asserts; run it with
  `AW_CONFORMANCE_UPDATE_GOLDENS` UNSET (`env -u AW_CONFORMANCE_UPDATE_GOLDENS python3 -m pytest
  'tests/test_cli_quality_gates.py::DeterministicByteGoldenTests'`), since setting it rewrites goldens and
  makes the assertion compare a render against itself. Do NOT edit any golden in this plan.
  - Depends on: E-01
  - Expected outcome: both strings present; the three golden tests pass with the update variable unset.
  - Execution state: performed

### Task group 2: pin the reader bijection

- [x] E-03 ADD `GoldenInventoryTests.test_every_committed_golden_is_read_and_every_read_golden_exists` to
  `tests/test_cli_quality_gates.py`. It computes the EXPECTED set as `{_golden_path(name, suffix).name for
  name in _fixtures() for suffix in ("agent", "human", "json")}` (the same `_golden_path` helper and the same
  three suffixes the `DeterministicByteGoldenTests` methods use, so the expected set is derived from what the
  readers actually read, not hand-listed), computes the PRESENT set as `{p.name for p in
  GOLDEN_DIR.glob("*.golden")}`, and asserts equality with a message naming the extra files (unread, so delete
  them or add a fixture) and the missing files (regenerate with `AW_CONFORMANCE_UPDATE_GOLDENS=1` and review
  the diff). Lift the suffix tuple into one module-level constant only if the three golden methods are switched
  to use it in the same edit; otherwise reuse the literal so no reader changes. A future fourth render suffix
  added to a reader without updating this tuple fails the test as an "extra" golden, which is the fail-closed
  direction and is acceptable. The failure message for missing files must also say that a regeneration run with
  `AW_CONFORMANCE_UPDATE_GOLDENS=1` writes them, since under randomized order this test can run before the
  writers in that same run. This lists a FIXTURE DIRECTORY,
  which is the artifact under test, and does not read production source, so it is within GUIDING_PRINCIPLES
  P16. Leave the module default-collected (no `slow` marker).
  - Depends on: E-02
  - Expected outcome: the new test exists in the module and passes against the twelve committed goldens.
  - Execution state: performed

- [x] E-04 PROVE THE NEW TEST IS SENSITIVE, then run the suite. With a THROWAWAY probe, reverted before
  commit: (a) `touch tests/fixtures/conformance_goldens/zzz_orphan.human.golden`, run the module, and confirm
  the new test FAILS naming `zzz_orphan.human.golden`; delete the probe. (b) Temporarily `mv
  tests/fixtures/conformance_goldens/read_clean.json.golden` to a path OUTSIDE `tests/fixtures/` (e.g. a gitignored
  `.aw/state/` scratch file), confirm a failure (the new test names it as missing; the existing
  `test_json_goldens_stable` also raises `FileNotFoundError`), and restore it. Confirm `git status --short
  tests/fixtures/` is EMPTY after both probes. Then run the bare suite `python3 -m pytest` and compare its failing-test
  names with the E-01 baseline: the bar is NO NEW failing test name, and any failure also present in the baseline
  is attributed to its filed owner rather than to this change. Commit through `aw commit cqxq2a -- tests/test_cli_quality_gates.py <this plan path>`.
  - Depends on: E-03
  - Expected outcome: both probes fail red, the fixture directory is clean afterwards, and the bare suite
    introduces no new failure.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- NO CODE-PINNING TESTS (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16). The narrow exception
  "content verification is permissible only where the text or file itself is the artifact under test", which
  `9i2hge` already relies on for goldens, covers listing the golden directory too. The new test must not
  read `agent_workflows/*.py` or count symbols.
- THE DEFAULT SUITE IS THE ONLY GATE THAT BINDS. `pyproject.toml` `addopts` deselects `slow` and
  `livecorpus`, and CI's `slow` step runs under `continue-on-error: true`, so the new test must stay
  unmarked (orchestrator `l8wvv3` "Project conventions").
- RUN THE SUITE BARE: `python3 -m pytest`, with no `-n0`, no extra `-q`, no `-p no:randomly` (`AGENTS.md`
  repository development contract).
- `AW_CONFORMANCE_UPDATE_GOLDENS=1` makes `_read_or_write_golden` rewrite every golden and return the
  rewritten bytes, so any validation run with it set is vacuous. Every run in this plan leaves it unset.
- COMMIT THROUGH `aw commit` with explicit paths; never `git add -A`; never push (`AGENTS.md`).

## Findings

| id | finding | evidence |
| --- | --- | --- |
| F-01 | THE ITEM'S F-04 IS ALREADY DISCHARGED. `tests/test_conformance_matrix_structure.py` (classes `UndeclaredLeafGuardTests`, `HarnessInvariantsTests`, `AliasEquivalenceTests`) and `tests/test_cli_quality_gates.py` (classes `SchemaGateTests`, `AnsiStreamGateTests`, `DeterministicByteGoldenTests`, `AccessibilityGateTests`, `TruncationGateTests`, `FactParityGateTests`, `BudgetGateTests`) both exist and are unmarked. `python3 -m pytest tests/test_cli_quality_gates.py tests/test_conformance_matrix_structure.py` reports `22 passed in 6.56s`. They were landed by `3ec1c2d5a` `work(dq9bj9)` and `67d026bcd` `work(9i2hge)`, children of orchestrator `l8wvv3`, all three in `.aw/records/plans/executed/`. | `git log --oneline -- tests/test_cli_quality_gates.py tests/fixtures/conformance_goldens`; the pytest run; `grep -n "Status" .aw/records/plans/executed/20261001-h0tiaw-0[12]-*.ipd.md`. |
| F-02 | THE ITEM'S F-05 IS ALREADY DISCHARGED. `check_findings.human.golden` now reads `Fix: a.md does not carry a clustered identity prefix; run 'aw rename plans a.md --to-id6 --apply' ...` and `run 'aw group plans b.md --set <new-set-id> --rename --apply' to regroup this record`, the strings `9i2hge` E-02 regenerated with its diff quoted, and the human golden test passes against the live render. | `grep -n "Fix:" tests/fixtures/conformance_goldens/check_findings.human.golden`; `9i2hge` E-02 and F-02. |
| F-03 | THE HARNESS HAS NO ZERO-IMPORTER PUBLIC SYMBOL THE ITEM CARES ABOUT. A per-name importer count over `tests/` and `agent_workflows/` excluding the module: `ANSI_RE` 2, `GOLDEN_DIR` 1, `build_matrix` 1, `required_scenarios` 2, `USAGE_ERROR_FLAG` 1, `run_cli` 36. The only zero-importer names (`MatrixRow`, `MatrixReport`, `RunResult`, `_pinned_env`) are the internally-used category `dq9bj9` E-03 deliberately kept (types returned by imported functions). | `rg -lw` sweep per name, run in this lane. |
| F-04 | ONE RESIDUAL GAP: AN UNREAD GOLDEN STILL PASSES. The readers iterate `_fixtures()` (four names) crossed with the suffixes `agent`, `human`, `json`, so a file outside that product is never opened. Planting `zzz_orphan.human.golden` and running the module gives `14 passed`. That is the exact condition both `krwj2o` ("twelve goldens ... exercised again") and `h0tiaw` F-07 filed, and `9i2hge` E-06(a) established it only as a one-time measurement at execution. The converse (a missing golden) IS already caught: `_read_or_write_golden` now raises `FileNotFoundError` when the file is absent and the update variable is unset, so `9i2hge` F-06's sharp edge was fixed. | The planted-orphan run in this lane (probe removed, `git status --short` clean); `_read_or_write_golden` read. |
| F-05 | NOTHING MACHINE-READABLE LINKS `krwj2o` TO ITS DISCHARGE BY `h0tiaw`. Neither `h0tiaw` plan carries `- From-Backlog: krwj2o`, and executed plans may not be edited in place (`AGENTS.md`), so the only legitimate way to give the item a carrier is a new plan that carries the field. That is why this plan exists rather than the item being closed by hand. Review 2026-10-12: the item is now `graduated` (`- Graduated-To: krwj2o`, history "graduated by run run-20261012T005606Z-2321569: cqxq2a") and carries no `- Blocks-Release:`. | `grep -rl krwj2o .aw/records` returns the item, the `zosxj4` plan that filed it, this plan, and the plans INDEX. |
| F-06 | THE LIVE-SWEEP REMAINDER HAS ITS OWN OWNER. The deleted `LiveScenarioConformanceTests` and live `FactParityTests` were deliberately deferred by `l8wvv3` to carrier `2wowfy` (now `graduated`), whose plan `34iwyp` (Set `livesweep`) is pending. Re-reviving them here would duplicate that plan. | `.aw/records/backlog/graduated/20261001-h0tiaw-01-2wowfy-*.backlog.md`; `.aw/records/plans/pending/20261011-livesweep-01-34iwyp-*.ipd.md`. |

## Proposed changes (ordered, validatable)

1. E-01 re-measures that both revived gate modules exist, are default-collected, pass, and give the harness's
   named symbols an importer (F-01, F-03).
2. E-02 re-measures that the stale golden strings were refreshed and the golden matches the live render (F-02).
3. E-03 adds the golden inventory bijection test so an unread golden fails (F-04).
4. E-04 proves that test fails on a planted orphan and on a removed golden, then runs the bare suite and commits.

## Deferred / out of scope (with reason)

- The live per-leaf `--help`/`--no-color`/usage-error sweep and the live human-versus-agent fact-parity gate.
  These were deferred by `l8wvv3` for measured cost and vacuity reasons and already have an owner.
  - Carrier: 2wowfy
- Re-restoring either deleted module or re-editing any golden. Already done by `dq9bj9` and `9i2hge`; doing
  it again would be churn against executed, reviewed work.
  - Carrier-Declined: already delivered by executed plans `dq9bj9` and `9i2hge`.

## Scope check

- Over-scope: none. One test method is added to one existing test module; no production code, no golden
  contents, and no executed plan is touched.
- Under-scope: none. Both of the item's findings are re-verified with pasted evidence (E-01, E-02), and the
  item's underlying property ("every golden is exercised") becomes a gate (E-03, E-04).

## Required tests / validation

- `python3 -m pytest tests/test_cli_quality_gates.py tests/test_conformance_matrix_structure.py` passes with the
  new test included (E-01, E-03).
- `env -u AW_CONFORMANCE_UPDATE_GOLDENS python3 -m pytest 'tests/test_cli_quality_gates.py::DeterministicByteGoldenTests'`
  passes (E-02).
- The planted-orphan and removed-golden probes each turn the new test red, and the fixture directory is clean
  afterwards (E-04).
- Bare `python3 -m pytest` introduces no new failure (E-04).
- `aw sanitize --agent` reports `clean`.

## Spec / documentation sync

N/A: no spec or user-facing doc describes the golden inventory. `CONTRIBUTING.md` step 6 was already
reconciled by `9i2hge` E-05 and does not mention goldens; the new test's docstring and failure message carry
the regeneration instruction the module docstring already states.

## Open questions

### OQ-01: Should this plan re-restore the deleted gates the item names, since the item is still open?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Repository evidence (F-01, F-02) shows Set `h0tiaw` restored both,
  from the same `19313eed7^` source the item names, under review. The item stayed `open` only because it
  was filed by a different plan (`zosxj4`) and nothing linked the two (F-05). This plan records the discharge
  and closes the one residual gap instead.

### OQ-02: Should the inventory check live in `tests/test_cli_quality_gates.py` or a new module?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The existing module. The expected set must be derived from the same
  `_fixtures()` and `_golden_path` the readers use, which are private to that module, so a separate module
  would have to duplicate the fixture list and could drift from it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted pre-edit bare-suite baseline summary line with its failing-test names (or
    none), the pasted pytest summary line (`N passed`) for the two-module run, a pasted
    `grep -n pytestmark` over both modules showing no `slow` marker, and the pasted per-symbol `rg -lw`
    output showing at least one test importer for each of `ANSI_RE`, `GOLDEN_DIR`, `build_matrix`,
    `required_scenarios`, `USAGE_ERROR_FLAG`.
  - Observed evidence:
    Pre-edit bare-suite baseline summary line (`python3 -m pytest`):
    ```
    7705 passed, 4 skipped, 3 warnings in 781.60s (0:13:01)
    ```
    Failing-test names: none (0 failed).

    Pytest summary line for two-module run (`python3 -m pytest tests/test_cli_quality_gates.py tests/test_conformance_matrix_structure.py`):
    ```
    22 passed in 10.27s
    ```

    Pasted `grep -n pytestmark` over both modules showing no `slow` marker:
    ```
    $ grep -n pytestmark tests/test_cli_quality_gates.py tests/test_conformance_matrix_structure.py
    (exit code 1, empty output)
    ```

    Pasted per-symbol `rg -lw` output showing at least one test importer for each of `ANSI_RE`, `GOLDEN_DIR`, `build_matrix`, `required_scenarios`, `USAGE_ERROR_FLAG`:
    ```
    === ANSI_RE ===
    tests/test_cli_quality_gates.py
    tests/test_conformance_matrix_structure.py
    tests/test_live_conformance_sweep.py
    === GOLDEN_DIR ===
    tests/test_cli_quality_gates.py
    === build_matrix ===
    tests/test_conformance_matrix_structure.py
    === required_scenarios ===
    tests/test_conformance_matrix_structure.py
    === USAGE_ERROR_FLAG ===
    tests/test_live_conformance_sweep.py
    tests/test_conformance_matrix_structure.py
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted `grep -n 'Fix:'` output over `check_findings.human.golden` containing both
    `--to-id6 --apply` and `--rename --apply`, and the pasted pytest summary for
    `DeterministicByteGoldenTests` run under `env -u AW_CONFORMANCE_UPDATE_GOLDENS`, plus `git status --short
    tests/fixtures/` pasted EMPTY afterwards (proving the run did not rewrite a golden).
  - Observed evidence:
    Pasted `grep -n 'Fix:'` output over `check_findings.human.golden`:
    ```
    7:    Fix: a.md does not carry a clustered identity prefix; run 'aw rename plans a.md --to-id6 --apply' or rename to match 'YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md'.
    11:    Fix: another record of the SAME type uses this Set ID with a different descriptive; run 'aw group plans b.md --set <new-set-id> --rename --apply' to regroup this record, or align the two descriptives. Sharing a Set ID with a different record type is correct and is not reported.
    ```

    Pasted pytest summary for `DeterministicByteGoldenTests` (`env -u AW_CONFORMANCE_UPDATE_GOLDENS python3 -m pytest 'tests/test_cli_quality_gates.py::DeterministicByteGoldenTests'`):
    ```
    3 passed in 4.06s
    ```

    Pasted `git status --short tests/fixtures/` EMPTY afterwards:
    ```
    $ git status --short tests/fixtures/
    (empty output)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the pasted `git diff tests/test_cli_quality_gates.py` showing the new test deriving its
    expected set from `_fixtures()` and `_golden_path` (not a hand-written list of twelve names), and the pasted
    passing pytest line for `GoldenInventoryTests`.
  - Observed evidence:
    Pasted `git diff tests/test_cli_quality_gates.py`:
    ```diff
    diff --git a/tests/test_cli_quality_gates.py b/tests/test_cli_quality_gates.py
    index 159f9357a..1fc855f73 100644
    --- a/tests/test_cli_quality_gates.py
    +++ b/tests/test_cli_quality_gates.py
    @@ -219,6 +219,30 @@ class DeterministicByteGoldenTests(unittest.TestCase):
                     self.assertEqual(j1, golden, f"{name}: json golden drift")


    +class GoldenInventoryTests(unittest.TestCase):
    +    """Inventory bijection: every committed golden is read; every read golden exists."""
    +
    +    def test_every_committed_golden_is_read_and_every_read_golden_exists(self):
    +        expected = {
    +            _golden_path(name, suffix).name
    +            for name in _fixtures()
    +            for suffix in ("agent", "human", "json")
    +        }
    +        present = {p.name for p in GOLDEN_DIR.glob("*.golden")}
    +        extra = sorted(present - expected)
    +        missing = sorted(expected - present)
    +        self.assertEqual(
    +            present,
    +            expected,
    +            (
    +                "Conformance golden inventory mismatch. "
    +                f"Extra files (unread: delete them or add a fixture): {extra}. "
    +                f"Missing files (regenerate with AW_CONFORMANCE_UPDATE_GOLDENS=1 to write them "
    +                f"and review the diff before committing): {missing}."
    +            ),
    +        )
    +
    +
     class AccessibilityGateTests(unittest.TestCase):
         """ASCII-glyph fallback: with AW_ASCII_ONLY the human render has no non-ASCII bytes."""

    ```

    Pasted passing pytest line for `GoldenInventoryTests` (`python3 -m pytest tests/test_cli_quality_gates.py::GoldenInventoryTests`):
    ```
    1 passed in 3.53s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the pasted FAILING pytest output for the orphan probe naming `zzz_orphan.human.golden`,
    the pasted failing output for the removed-golden probe naming `read_clean.json.golden`, `git status --short
    tests/fixtures/` pasted EMPTY after both, the pasted bare `python3 -m pytest` summary line and failing-test
    names compared against the E-01 baseline showing no new name, the pasted `aw sanitize --agent` record, and the commit hash from
    `aw commit`.
  - Observed evidence:
    Pasted FAILING pytest output for the orphan probe naming `zzz_orphan.human.golden`:
    ```
    =================================== FAILURES ===================================
    _ GoldenInventoryTests.test_every_committed_golden_is_read_and_every_read_golden_exists _
    [gw5] linux -- Python 3.14.6 <venv>/bin/python3
    ...
    E       AssertionError: Items in the first set but not the second:
    E       'zzz_orphan.human.golden' : Conformance golden inventory mismatch. Extra files (unread: delete them or add a fixture): ['zzz_orphan.human.golden']. Missing files (regenerate with AW_CONFORMANCE_UPDATE_GOLDENS=1 to write them and review the diff before committing): [].
    =========================== short test summary info ============================
    FAILED tests/test_cli_quality_gates.py::GoldenInventoryTests::test_every_committed_golden_is_read_and_every_read_golden_exists
    1 failed in 3.61s
    ```

    Pasted failing output for the removed-golden probe naming `read_clean.json.golden`:
    ```
    =================================== FAILURES ===================================
    _ GoldenInventoryTests.test_every_committed_golden_is_read_and_every_read_golden_exists _
    [gw5] linux -- Python 3.14.6 <venv>/bin/python3
    ...
    E       AssertionError: Items in the second set but not the first:
    E       'read_clean.json.golden' : Conformance golden inventory mismatch. Extra files (unread: delete them or add a fixture): []. Missing files (regenerate with AW_CONFORMANCE_UPDATE_GOLDENS=1 to write them and review the diff before committing): ['read_clean.json.golden'].
    ____________ DeterministicByteGoldenTests.test_json_goldens_stable _____________
    [gw4] linux -- Python 3.14.6 <venv>/bin/python3
    ...
    E           FileNotFoundError: Golden file does not exist: <repo-root>/tests/fixtures/conformance_goldens/read_clean.json.golden. Regenerate intentionally by running with AW_CONFORMANCE_UPDATE_GOLDENS=1 and review the diff before committing.
    =========================== short test summary info ============================
    FAILED tests/test_cli_quality_gates.py::GoldenInventoryTests::test_every_committed_golden_is_read_and_every_read_golden_exists
    FAILED tests/test_cli_quality_gates.py::DeterministicByteGoldenTests::test_json_goldens_stable
    2 failed in 3.53s
    ```

    `git status --short tests/fixtures/` pasted EMPTY after both:
    ```
    $ git status --short tests/fixtures/
    (empty output)
    ```

    Pasted bare `python3 -m pytest` summary line and failing-test names compared against E-01 baseline:
    Baseline: `7705 passed, 4 skipped, 3 warnings in 781.60s (0:13:01)` with 0 failures
    Post-change: `7706 passed, 4 skipped, 3 warnings in 742.36s (0:12:22)` with 0 failures (1 additional test passed: `GoldenInventoryTests.test_every_committed_golden_is_read_and_every_read_golden_exists`). Zero failing test names introduced.

    Pasted `aw sanitize --agent` record:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":4915,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    The commit hash from `aw commit`:
    Recorded in the commit created by `aw commit cqxq2a -- tests/test_cli_quality_gates.py <plan>`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved cqxq2a --by-human`); OQ-01 and OQ-02 are
resolved, and no question is open. Begin with `aw ipd begin cqxq2a`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition. If an edit outside it proves necessary,
make it and justify it at finalize with `--scope-reason <path>=<why>`. The golden files, `tests/conformance_matrix.py`,
`agent_workflows/`, and the executed `h0tiaw`/`zosxj4` plans are out of scope by design; the E-04 probes touch
`tests/fixtures/` only transiently and must leave `git status --short tests/fixtures/` empty. The one
deliberate stop is E-01's: if either revived module is missing, `slow`-marked, or failing, the plan's premise is
false, so mark E-01 `blocked` and report rather than re-restoring.

Honesty: you MUST paste the ACTUAL runner output for every test or command claim in each `V-*`; never claim a
result you did not run, and never run a golden test with `AW_CONFORMANCE_UPDATE_GOLDENS` set.

Commits: only `tests/test_cli_quality_gates.py` and this plan, through `aw commit cqxq2a -- <paths>`; verify
`git diff --cached --name-only` before any raw commit; never push, never tag.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, after every `V-*` is
`pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize cqxq2a`. Backlog `krwj2o`
(`graduated`, no `- Blocks-Release:`) may then close with `aw backlog set done krwj2o`; it carries no release gate,
so the close needs no handoff proof, and this plan's `- From-Backlog: krwj2o` is the durable record of discharge.
