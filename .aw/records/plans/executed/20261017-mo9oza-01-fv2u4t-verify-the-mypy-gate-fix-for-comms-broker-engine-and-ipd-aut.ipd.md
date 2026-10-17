# IPD: Verify the mypy gate fix for comms_broker, engine and ipd_authoring and retire mo9oza from the CI slow advisory

- Date: 2026-10-17
- Kind: child
- Concern: Backlog `mo9oza` (bug, Blocks-Release next) records that the static type gate `python3 -m mypy agent_workflows` failed with 3 errors in `agent_workflows/comms_broker.py`, `agent_workflows/engine.py` and `agent_workflows/ipd_authoring.py`, which made the slow-marked test `tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit` fail and is one of the two reasons the CI "Run slow-marked tests" step in `.github/workflows/tests.yml` is held `continue-on-error: true`. Commit `b4acc832d` ("fix(ci): fix mypy errors, ...", 2026-10-16 20:28, about an hour after the item was filed at 19:22) already changed exactly those three files, and at authoring HEAD `2c8da7b8d` the gate reports `Success: no issues found in 197 source files`. What remains is to prove that fix at the executing HEAD, to drop the now-stale `mo9oza` entry from the CI advisory comment, and to record the fix in `CHANGELOG.md`, so the item can close on evidence instead of silently.
- Scope: IN: (1) re-measure the mypy gate and the slow typecheck test at the executing HEAD; (2) remove the `mo9oza` bullet from the advisory comment above the "Run slow-marked tests" step in `.github/workflows/tests.yml`, keeping `continue-on-error: true` because the other owning item `denczr` is not done (its carrier plan `gbnrdf` is still pending); (3) one `Fixed:` bullet in `CHANGELOG.md`. OUT: any edit to `agent_workflows/comms_broker.py`, `agent_workflows/engine.py` or `agent_workflows/ipd_authoring.py` (already fixed by `b4acc832d`; if E-01 finds new errors there, this plan stops and reports rather than widening scope); flipping the slow step to fail-closed (owned by the flip condition, gated on `denczr`); `pyproject.toml` `[tool.mypy]` configuration; `tests/test_typecheck_gate.py` (it already asserts the outcome this item needs).
- Scope-Paths: .github/workflows/tests.yml, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: mo9oza
- Blocks-Release: next
- Set: mo9oza
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: fv2u4t

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: fv2u4t verified (set mo9oza, attempt 1).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed
- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-17 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog mo9oza at HEAD 2c8da7b8d; measured the gate already clean (fixed by b4acc832d), so the plan verifies the fix and retires the stale CI advisory reference.

## Goal

Close backlog `mo9oza` on measured evidence: show the mypy gate and its slow regression test pass at the executing HEAD, and remove the item's now-stale entry from the CI slow-step advisory so that comment lists only the failures that still hold the step advisory.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure

- [x] E-01 Re-measure the type gate and its slow regression test at the executing HEAD.
  - Depends on: none
  - Expected outcome: a pasted transcript of (a) `git rev-parse HEAD`; (b) `python3 -m mypy --version` and `python3 -c "import filelock; print(filelock.__version__)"` (the pinned environment named in the `pyproject.toml` `[tool.mypy]` comment, "mypy 2.3.1, filelock >=4"); (c) `python3 -m mypy agent_workflows > /tmp/mypy.out 2>&1; echo rc=$?; tail -3 /tmp/mypy.out` showing `rc=0` and a last line `Success: no issues found in N source files` (the exit code is captured separately because piping into `tail` would mask it; an `[annotation-unchecked]` note line above it is expected and is not an error); (d) `python3 -m pytest -o addopts="" -m slow tests/test_typecheck_gate.py` reporting `1 passed` (the slow test is `TypecheckGateTests::test_typecheck_gate_clean_exit`); (e) `git show --stat b4acc832d -- agent_workflows/comms_broker.py agent_workflows/engine.py agent_workflows/ipd_authoring.py` naming the three files. If (c) reports any error, STOP: mark E-01 `failed`, record the errors, and do not perform E-02/E-03 (a new regression needs its own item, not a widened scope here).
  - Execution state: performed

### Task group 2: records

- [x] E-02 Remove the `mo9oza` bullet from the slow-step advisory comment in `.github/workflows/tests.yml`.
  - Depends on: E-01
  - Expected outcome: the comment block above `- name: Run slow-marked tests (ADVISORY until the known slow failures are fixed)` no longer contains the line `# - mo9oza: TypecheckGateTests.test_typecheck_gate_clean_exit`; the `denczr` bullet, the flip-condition text and `continue-on-error: true` are unchanged; the file still parses as YAML.
  - Execution state: performed

- [x] E-03 Add one `Fixed:` bullet to `CHANGELOG.md`.
  - Depends on: E-01
  - Expected outcome: one bullet in the topmost section `## 2.0.0 (pending)`, beside the other current `Fixed:` bullets, stating that the static type check (`make typecheck`, CI "static type gate") passes again after three mypy errors in the comms broker, the installer engine and IPD authoring were fixed; no em or en dashes in the added text.
  - Execution state: performed

### Task group 3: validation

- [x] E-04 Run the closing validation.
  - Depends on: E-02, E-03
  - Expected outcome: (1) `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/tests.yml'))"` exits 0; (2) `git grep -n mo9oza -- .github/` prints nothing; (3) `git diff -U0 -- CHANGELOG.md | grep '^+' | grep -c -P '[\x{2013}\x{2014}]'` prints `0`; (4) `python3 -m agent_workflows sanitize --agent` reports `"outcome": "clean"`; (5) bare `python3 -m pytest` passes (summary line pasted); (6) `git diff --name-only <pre-execution HEAD>` lists only `.github/workflows/tests.yml`, `CHANGELOG.md` and this plan (at its pending or executed path).
  - Execution state: performed

## Project conventions discovered (Step 0)

- The CI slow step is advisory by design until every owning item is done: comment "Flip condition: remove continue-on-error once -m slow reports 0 failed on the ubuntu leg, i.e. once every owning item is done." (`.github/workflows/tests.yml`). `denczr` is `graduated`, not done, so the flip is out of scope.
- The type gate is fail-closed in CI as its own job ("Run static type gate (mypy agent_workflows)", comment "FAIL-CLOSED, NOT ADVISORY"), and `tests/test_typecheck_gate.py::TypecheckGateTests` is `@pytest.mark.slow`, so the core tier never exercises it; it must be run explicitly with `-m slow`.
- The gate's clean baseline is reproducible only in the pinned environment (`pyproject.toml` comment above `[tool.mypy]`), hence E-01(b).
- Full suite runs bare as `python3 -m pytest`; narrowed runs clear defaults with `-o addopts=""` (AGENTS.md repo-local contract).
- User-facing prose (`CHANGELOG.md`) carries no em or en dashes (AGENTS.md).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The three errors were fixed after the item was filed. | Item file committed 2026-10-16 19:22; `b4acc832d` at 20:28 touches `agent_workflows/comms_broker.py` (adds `return eligible_msg_ids` at the end of `comms_broker.scan_once`), `agent_workflows/engine.py` (`phys = ctx.physical_classes or {}`), and `agent_workflows/ipd_authoring.py` (`_rp.target_subdir("plans", "to-review") or "pending"`): one fix per named module. |
| F-02 | The gate is clean at authoring HEAD. | At `2c8da7b8d` with mypy 2.3.1 and filelock 4.0.9: `Success: no issues found in 197 source files`; `python3 -m pytest -o addopts="" -m slow tests/test_typecheck_gate.py -q` gave `1 passed, 2 deselected in 3.01s`. |
| F-03 | The only live reference to the item outside records is the CI advisory comment. | `grep -rn mo9oza` (excluding `.git/` and bytecode) matched `.github/workflows/tests.yml` ("# - mo9oza: TypecheckGateTests.test_typecheck_gate_clean_exit") and records only (the item and executed plan `hguae9`). |
| F-04 | The advisory must stay advisory. | The other owning item `denczr` is `graduated` with carrier plan `gbnrdf` still in `pending/`, so the flip condition is unmet. |

## Proposed changes (ordered, validatable)

1. Re-measure the gate and slow test (E-01).
2. Drop the stale `mo9oza` advisory bullet (E-02).
3. CHANGELOG `Fixed:` bullet (E-03).
4. Closing validation (E-04).

## Deferred / out of scope (with reason)

- Removing `continue-on-error: true` from the slow step: gated on `denczr`, whose carrier `gbnrdf` is pending.
  - Carrier-Declined: owned by the existing flip condition in `.github/workflows/tests.yml` and the `denczr` carrier; not new work.
- Code changes to the three modules: already made by `b4acc832d` (F-01).
  - Carrier-Declined: work already done; nothing remains.

## Scope check

- Over-scope: none. One comment line and one changelog bullet.
- Under-scope: none. The item asks for the 3 errors to be gone; F-01/F-02 show they are, and E-01 re-proves it at execution time.

## Required tests / validation

- `python3 -m mypy agent_workflows` clean and `tests/test_typecheck_gate.py` slow test passing (E-01).
- YAML parse, dash scan, `aw sanitize --agent`, bare `python3 -m pytest`, and a diff limited to the declared paths (E-04).

## Spec / documentation sync

- `CHANGELOG.md` records the fix (E-03).
- No spec describes the CI advisory list or the mypy baseline, so no `.spec.md` is touched or declared.

## Open questions

### OQ-01: Should this plan re-fix the modules or only verify?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: verify only. `b4acc832d` made one fix in each named module and the gate is clean at HEAD (F-01, F-02). Re-editing them would be scope with nothing to do; E-01 stops the plan if a regression has appeared.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the E-01 transcript: HEAD sha, mypy and filelock versions, the mypy tail ending `Success: no issues found in N source files`, the slow-test line `1 passed`, and the `git show --stat b4acc832d` file list naming all three modules.
  - Observed evidence:
    HEAD sha:
    a3e21ca502521ac98e6a885a2fc98190cbec5b34

    mypy and filelock versions:
    mypy 2.3.1 (compiled: yes)
    4.0.9

    mypy tail:
    rc=0
    agent_workflows/cli.py:994: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
    Success: no issues found in 197 source files

    slow-test line:
    ======================= 1 passed, 2 deselected in 19.21s =======================

    git show --stat b4acc832d:
    commit b4acc832d8df0ff3450e5546b78f50261a31f692
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 16 20:28:03 2026 -0400

        fix(ci): fix mypy errors, plan uncarried obligations, and git fixture identity in tests

        AW-Runner: aw commit

     agent_workflows/comms_broker.py  | 2 ++
     agent_workflows/engine.py        | 2 +-
     agent_workflows/ipd_authoring.py | 2 +-
     3 files changed, 4 insertions(+), 2 deletions(-)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff -- .github/workflows/tests.yml` showing exactly one removed line (the `mo9oza` bullet) and no change to `continue-on-error: true` or the `denczr` bullet.
  - Observed evidence:
    diff --git a/.github/workflows/tests.yml b/.github/workflows/tests.yml
    index 8879703f0..bb7b40e9c 100644
    --- a/.github/workflows/tests.yml
    +++ b/.github/workflows/tests.yml
    @@ -87,7 +87,6 @@ jobs:
           # Advisory step running slow-marked tests: currently advisory because of known pre-existing
           # slow failures tracked by backlog items:
           # - denczr: test_second_install_nochange_leaves_clean_status_and_no_false_lines
    -      # - mo9oza: TypecheckGateTests.test_typecheck_gate_clean_exit
           # Flip condition: remove continue-on-error once -m slow reports 0 failed on the ubuntu leg,
           # i.e. once every owning item is done.
           - name: Run slow-marked tests (ADVISORY until the known slow failures are fixed)
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff -- CHANGELOG.md` showing one added `Fixed:` bullet under `## 2.0.0 (pending)`.
  - Observed evidence:
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 29eccf4b6..7f9331755 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -26,6 +26,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t

     - Added: `aw runs analyze --since WHEN --until WHEN` publishes a report covering only runs started in that window, and the dashboard gains quick date ranges (last 7, 30 or 90 days, latest month).
     - Added: a **Tokens and cost** dashboard tab showing in + out, input, output, cached and cache-write tokens separately, each with count, total, average, median and p90, plus their costs, overall and split by agent (host and model) or any other dimension.
    +- Fixed: static type checking (`make typecheck`, CI "static type gate") passes again after three mypy errors in the comms broker, the installer engine and IPD authoring were fixed.
     - Fixed: `aw install --records-backend <new>` on an installed repository no longer silently leaves existing records where no reader looks: it refuses when records would be orphaned, and `--relocate` (with `--dry-run` preview, `--relocate-resume`, `--relocate-rollback`) moves them.
     - Fixed: `aw releases readiness` no longer reports a false `workflow_disposition` NO-GO in a managed repository that adds its own workflows.
     - Fixed: `aw work begin` no longer crashes on clean-delta installs (`completely-clean-target`, `local-only`) whose plans live outside the repository.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the YAML parse exit code, the empty `git grep -n mo9oza -- .github/` output, the dash-scan count 0, the sanitize `"outcome": "clean"` line, the bare `python3 -m pytest` summary line, and the `git diff --name-only` list.
  - Observed evidence:
    YAML parse exit code:
    yaml_rc=0

    Empty git grep -n mo9oza -- .github/:
    exit 1 (no output)

    Dash-scan count:
    0

    Sanitize agent check:
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5856,"findings":0,"evidence":["leak-scan"],"next":null}

    Pytest summary line:
    753 passed in 32.19s / 753 passed in 62.40s (0:01:02)

    git diff --name-only a3e21ca502521ac98e6a885a2fc98190cbec5b34:
    .aw/records/plans/pending/20261017-mo9oza-01-fv2u4t-verify-the-mypy-gate-fix-for-comms-broker-engine-and-ipd-aut.ipd.md
    .github/workflows/tests.yml
    CHANGELOG.md
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (Status `approved`). All open questions are resolved (OQ-01).

SCOPE FENCE. `- Scope-Paths:` is the expected edit set. An out-of-scope edit is permitted only when justified at finalize with `--scope-reason <path>=<why>`; acknowledge a declared path left unmodified with `--scope-ack`. The one STOP condition is E-01's: a NEW mypy error means the premise (the gate is clean) is false, so the plan stops with E-01 `failed` rather than editing the three modules.

HONESTY. Every `V-*` evidence block MUST paste the ACTUAL runner or command output; never claim a pass that was not run.

COMMIT. Commit through `aw commit fv2u4t -- .github/workflows/tests.yml CHANGELOG.md <this plan>`; verify `git diff --cached --name-only` lists only those paths; never push.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize fv2u4t`. Never `git mv` the plan by hand. If E-01 fails, do not transition: leave the plan in `pending/` and report. This plan carries `- Blocks-Release: next` inherited from backlog `mo9oza`; closing that item `done` afterwards uses the HANDOFF route (this executed carrier).
