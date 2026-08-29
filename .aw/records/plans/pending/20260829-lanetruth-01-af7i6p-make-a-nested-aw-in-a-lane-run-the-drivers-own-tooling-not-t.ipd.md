# IPD: make a nested aw in a lane run the runner's own tooling, not the lane branch copy

- Date: 2026-08-29
- Kind: child
- Concern: Under worktree isolation the runner invokes nested `aw` with `cwd` set to the lane worktree and the command `[sys.executable, "-m", "agent_workflows", ...]`. Python prepends the cwd to `sys.path` for `-m`, so `agent_workflows` resolves to the LANE BRANCH's checked-out copy. Every lifecycle fix is therefore void inside a lane until that lane rebases, and a lane that legitimately edits `agent_workflows/` has the runner execute that unreviewed code to perform the very transition meant to gate it.
- Scope: Pin every runner-spawned nested `aw` invocation to the tooling the RUNNER itself is running, in both drivers, and add a guard so the hijack cannot recur. Behavior of the nested verbs is unchanged; only which code implements them changes. Excludes the host-agent `Popen` (the agent turn SHOULD run in the lane) and excludes any change to lane allocation or teardown.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_tool_identity.py
- Item-Dependencies: none
- Status: to-review
- Set: lanetruth
- Order: 1
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: af7i6p
- Blocks-Release: next
- From-Backlog: tfx39h

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog `tfx39h`, filed this session after the defect was measured in run-20260829T153858Z-3207626. Ordered FIRST in the `lanetruth` Set because until it lands, any other lifecycle fix is unverifiable inside a lane whose base predates it.
- 2026-08-29 /plan-review of orchestrator y0gg8o (opencode (its_direct/pt3-claude-opus-5-1m-us)): CROSS-REFERENCE, two corrections owned by `y0gg8o`. (1) MECHANISM: `-P` ALONE IS INSUFFICIENT and OQ-01's "prefer `-P`" resolution is too weak as written. Measured at review with three distinct packages (a decoy lane copy, a parent checkout copy, and a default-path copy): from the lane cwd, plain `python3 -m agent_workflows` imported the LANE copy (the defect, reproduced), and `python3 -P -m agent_workflows` imported the DEFAULT-PATH (site-packages) copy, NOT the parent's. `-P` suppresses the cwd entry; it does not pin to the parent. It appears correct on THIS checkout only because the install is editable (`pip show agent-workflows` reports an "Editable project location" equal to this repo root), so site-packages and the parent's checkout are the same files. Adding the parent's own package root (`Path(agent_workflows.__file__).parent.parent`) to the child `PYTHONPATH` alongside `-P` resolved to the parent's copy, verified in both directions. E-01 must pin POSITIVELY, and E-04's identity assertion must be validated against that, or it will fail closed on a legitimate non-editable install. The orchestrator's completion criterion 2 now demands a POSITIVE four-way demonstration (parent path/version, child path/version, equality, and proof the lane copy existed and was not imported); "not the lane's copy" is explicitly not sufficient. Also verified: `-P` is accepted by python3.11 and python3.12, but `requires-python = ">=3.9"` and CI matrices 3.9-3.14 (`.github/workflows/tests.yml:31,172`), so the `PYTHONSAFEPATH=1` fallback named in OQ-01 is REQUIRED, not optional, and its equivalence must be evidenced on the floor version rather than assumed. (2) BLAST RADIUS: F1/the Concern imply all nested `aw` is lane-shadowed. `driver_begin` is NOT: it runs with `cwd=str(repo)` (oc_runipd.py:370) and the lane is allocated only AFTER begin returns (:1958 then :1987). The genuinely lane-shadowed invocation is `driver_finalize` (`cwd=finalize_repo`, :2214) plus the `run_checked` helpers. F3's observed `ipd-finalize-refused` is consistent with this narrower reading. Fix all four call sites as planned, but do not validate against the overbroad claim.

## Goal

Make the tool the runner invokes be the tool the runner IS. Today a nested `aw` inside a lane silently runs the lane branch's version of the lifecycle machinery against the real repository, so a fix can be verified green in `main` and still not apply where it matters, and two lanes in one run can enforce different lifecycle rules depending on their base commits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the interpreter's import path

- [ ] E-01 Introduce ONE shared helper in `oc_runipd.py` that builds the argv prefix for a nested `aw` invocation, pinning module resolution to the runner's own installation. Use `[sys.executable, "-P", "-m", "agent_workflows", ...]` (or the equivalent `PYTHONSAFEPATH=1` in the child env when `-P` is unavailable on the supported interpreter floor). `-P` suppresses the cwd entry on `sys.path`, which is exactly the hijack vector, while leaving the real package resolvable. Route all four existing nested-`aw` call sites (oc_runipd.py:248, :317, :356, :425) through the helper. Do NOT change the host-agent `Popen`: the agent turn is supposed to run in the lane.
  - Depends on: none
  - Expected outcome: all four oc call sites build argv through the one helper; a nested `aw` launched with `cwd` inside a lane resolves `agent_workflows` to the runner's own module path, not the lane's.
  - Execution state: pending

- [ ] E-02 Apply the same pinning symmetrically in `agy_runipd.py` at its three nested-`aw` call sites (agy_runipd.py:421, :481, :548), reusing the shared helper rather than duplicating the logic. Keeping the two drivers symmetric is a hard requirement; a one-driver-only fix is a defect.
  - Depends on: E-01
  - Expected outcome: all three agy call sites route through the same helper; no driver-local reimplementation exists.
  - Execution state: pending

### Task group 2: prove it and prevent recurrence

- [ ] E-03 Add `tests/test_lane_tool_identity.py` asserting that a nested `aw` invoked for a lane reports the RUNNER's module path and version even when the lane's checked-out `agent_workflows/` differs. Construct the adversarial case explicitly: a directory containing a DECOY `agent_workflows/__init__.py`, used as the child `cwd`. The test must show the decoy is imported WITHOUT the fix and the real package WITH it. Include an AST/source guard asserting every `-m agent_workflows` invocation in both drivers carries the pinning flag, so a future call site cannot silently omit it, and a symmetry assertion so a one-driver fix fails.
  - Depends on: E-01, E-02
  - Expected outcome: the new module passes; the decoy-import assertion FAILS against pre-fix argv and passes after; the AST guard FAILS when an unpinned `-m agent_workflows` call site is injected.
  - Execution state: pending

- [ ] E-04 Add a runtime identity assertion: before the first nested `aw` of a run, the runner verifies the child's reported module path/version matches its own and FAILS CLOSED with a named diagnostic on mismatch, rather than proceeding. This converts a silent wrong-code execution into a loud refusal, which is the posture spec `25kzda` requires. Record the check's outcome in the run ledger so a run can be audited after the fact.
  - Depends on: E-01, E-02
  - Expected outcome: a deliberately mismatched child is refused with the named diagnostic and the run records it; a matching child proceeds silently with the outcome recorded.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The hijack is real and measured. In `.aw/worktrees/8zgybk` (lane base `5e78e33`): `sys.path[0]` is `''`, `agent_workflows` resolves to the WORKTREE copy, `python3 -m agent_workflows --version` reports `1.3.0rc2.dev1429+g5e78e33` (the lane's base, not the runner's), and `grep -c AW_NONINTERACTIVE agent_workflows/ipd_lifecycle.py` returns 0, i.e. the `g40w37` TTY fix was ABSENT from the code that actually ran.
- `-P` is verified to fix it without breaking resolution. From a directory containing a decoy `agent_workflows/__init__.py`: default `python3 -c "import agent_workflows"` imports the DECOY; `python3 -P -c` imports the real installed package. So the flag suppresses exactly the cwd entry and nothing else that matters here.
- The call sites are `driver_begin`, `driver_finalize`, and two `run_checked`-style helpers; `driver_finalize` (oc_runipd.py:412-446) passes `cwd=str(repo)` where the caller supplies `finalize_repo = Path(work_dir) if (work_dir and wt_handle) else repo` (oc_runipd.py:2198, called at :2212-2214). So the lane cwd is deliberate for path resolution and must be PRESERVED; only import resolution changes.
- Both `aw ipd begin` and `aw ipd finalize` already accept `--dir`, so the lane can be addressed by flag rather than by cwd. This is a viable alternative to `-P` and is recorded under OQ-01, but `-P` is preferred because it fixes ALL nested invocations at once rather than per-verb.
- `stdin=subprocess.DEVNULL` is already set on these calls by `g40w37`; the pinning change must not disturb it.
- Prior art for the test shape: `tests/test_lane_session_isolation.py` (from `c0e9599`) demonstrates the required pattern of an AST guard plus a cross-driver symmetry assertion, and of proving a test fails without the fix.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `oc_runipd.py:425-446` + `:2198`/`:2212` | `driver_finalize` runs `[sys.executable, "-m", "agent_workflows", ...]` with `cwd` = the lane worktree, so `-m` resolves the package from the lane branch. | measured in `.aw/worktrees/8zgybk`: `-m` resolves to the worktree copy |
| F2 | HIGH | `.aw/worktrees/8zgybk` | The lane ran a PRE-FIX copy of `ipd_lifecycle.py`: version `g5e78e33`, `AW_NONINTERACTIVE` guard absent, while `main` had both the callee guard and `stdin=DEVNULL`. | `--version` + `grep -c` in the lane |
| F3 | HIGH | run-20260829T153858Z-3207626 | Consequence observed: `ipd-finalize-refused` at 18:06:42Z with an interactive scope prompt and `exit_code=-15` (the runner's SIGTERM), 11 minutes AFTER `6332a04` landed at 17:55:25Z. The fix was bypassed by executing stale code, not defeated. | events.jsonl + `git log -1 --format=%aI 6332a04` |
| F4 | HIGH | conceptual, same call sites | A lane whose plan legitimately EDITS `agent_workflows/` (routine in this repo) has the runner execute that lane's UNREVIEWED, in-progress lifecycle code to perform the transition that is supposed to gate it. A mid-edit broken module would take the runner's own state transitions with it. | `wtiso` children declare `agent_workflows/*.py` in Scope-Paths |
| F5 | MED | `agy_runipd.py:421,481,548` | The same shape exists in the agy driver, so fixing only `oc` would leave the defect live on the other host. | three `sys.executable` nested invocations |

## Proposed changes (ordered, validatable)

1. Add one shared argv-prefix helper with the pinning flag (E-01), so there is a single place the invariant lives.
2. Route both drivers through it (E-01, E-02), keeping them symmetric.
3. Prove the fix adversarially with a decoy package and guard against new unpinned call sites (E-03).
4. Convert residual mismatch into a loud, recorded refusal (E-04).

## Deferred / out of scope (with reason)

- The host-agent `Popen` (the actual agent turn) deliberately runs in the lane with the lane's code visible; that is the point of isolation. Only nested `aw` control-plane invocations are pinned.
- Backlog `dh0uno` (inner `aw` resolving `.aw/state` / `.aw/records/runs` relative to the lane) is a sibling facet about which STATE FILES an inner `aw` reaches; this plan is about which CODE it IS. `dh0uno` is `graduated` and owned by the `wtiso` Set. Fixing this plan reduces `dh0uno`'s blast radius but does not close it, and this plan must not claim to.
- Rebasing or rewriting existing lane branches. Out of scope and unnecessary: pinning makes a stale lane base harmless for control-plane purposes.
- The `--dir`-everywhere alternative (see OQ-01), recorded as a rejected-for-now option with its reason.

## Scope check

- Over-scope: none. Both driver modules carry findings; the test module is new and required by E-03.
- Under-scope: `dh0uno` and lane rebasing are named under Deferred with reasons.

## Required tests / validation

- The new `tests/test_lane_tool_identity.py` must pass AND be shown to fail pre-fix (decoy import + AST guard + symmetry).
- `tests/test_lane_session_isolation.py` must pass unchanged (same two modules were changed by `c0e9599`).
- `python3 -m pytest -n auto` and `python3 -m pytest -m "" -n auto` against the Set's recorded baseline: fast `2871 passed, 3 skipped, 4 xfailed`; full `4 failed, 3198 passed, 3 skipped, 4 xfailed` where those 4 are the PRE-EXISTING CLI-surface failures. Do not claim them as caused or fixed.
- An end-to-end check: run a lane whose base predates `6332a04` and show a runner-spawned `aw ipd finalize` exhibiting the FIXED behavior (sub-second non-interactive refusal), proving the pin defeats the stale-code path that F3 measured.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- Spec `25kzda` section 5.2 (safety policy) and 6.1.4 (no-push/hook guarantees require owning process launch) are strengthened by this change: pinning is a precondition for the engine genuinely owning the control plane. No spec text change is required by this plan, but the executor should note in the plan record that 6.1.4's premise now holds more tightly.
- No user-facing docs describe the nested invocation mechanism, so no doc updates are required. If a walkthrough is written, it belongs in `.aw/records/walkthroughs/`.

## Open questions

### OQ-01: `-P` / `PYTHONSAFEPATH` versus passing `--dir` and running from the main repo

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Prefer `-P`. Both `aw ipd begin` and `aw ipd finalize` accept `--dir` (verified), so the alternative is viable, but it fixes only the verbs that happen to expose the flag and must be re-applied to every future call site, whereas `-P` fixes import resolution for ALL nested invocations at one choke point and is enforceable by the E-03 AST guard. `-P` is verified to import the real package from a decoy-containing cwd. If the supported interpreter floor predates `-P` (3.11), the executor uses `PYTHONSAFEPATH=1` in the child environment, which is equivalent; the executor must state which mechanism shipped.

### OQ-02: Should a mismatch be fatal to the whole run or only to the item?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Lean run-fatal. A tool-identity mismatch means the control plane itself is not what the runner believes, which is one of the repository-wide integrity classes spec `25kzda` section 1.4/A1 reserves `ABORT RUN` for, rather than an item-local fault. E-04 implements a loud refusal; whether it aborts the run or quarantines the item is the maintainer's risk call, and the executor must not silently choose the weaker option.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the shared helper's source and `grep -n` output showing all four oc call sites (previously oc_runipd.py:248, :317, :356, :425) routing through it. Paste a launched child's argv containing the pinning flag, and confirm `stdin=subprocess.DEVNULL` is still present at each site (the `g40w37` guarantee must not regress).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -n` output for all three agy call sites showing they use the same helper, plus a diff or assertion demonstrating no driver-local duplicate of the pinning logic exists.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new test module passing. Then paste PROOF OF FALSIFIABILITY in both directions: (a) with the pin removed, the decoy `agent_workflows` is imported and the test FAILS; (b) with an unpinned `-m agent_workflows` call site injected, the AST guard FAILS; (c) with only one driver fixed, the symmetry assertion FAILS. Restore and paste the passing run.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the refusal path firing on a deliberately mismatched child, showing the named diagnostic and the run-ledger record. Paste the matching-child case proceeding with its outcome recorded. State explicitly whether the refusal is run-fatal or item-local and cite the OQ-02 decision it implements.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. This is a SHARED CHECKOUT: at authoring time a concurrent session had uncommitted work in `agent_workflows/` and `tests/`, and a path-scoped commit still commits whatever is already staged for those paths. Re-read both driver modules before editing rather than reusing a stale view.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
