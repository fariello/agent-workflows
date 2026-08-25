# IPD: Reduce tools ipdrunner runipd to a thin compatibility shim

- Date: 2026-08-24
- Kind: child
- Concern: After the core moves into the package (child 01), the original `tools/ipdrunner/runipd.py` must not keep a second copy of the logic (that would drift). But existing invocations - `python3 tools/ipdrunner/runipd.py ...`, the runbook at `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md`, and any operator muscle memory - must keep working. The established repo pattern for this is a thin backwards-compatible shim (see `tools/antigravity_execute_ipd.py` delegating to `agy_run`, and `tools/watch-agy.py` delegating to `pwatch`).
- Scope: Reduce `tools/ipdrunner/runipd.py` to a thin shim that imports `agent_workflows.oc_runipd` and delegates `main()`, re-exporting any names external callers rely on, so `python3 tools/ipdrunner/runipd.py ...` behaves identically with zero duplicated logic. Child 03 of the awocrunner Set; depends on child 01.
- Scope-Paths: tools/ipdrunner/runipd.py, tests/test_oc_runipd_shim.py
- Status: to-review
- Set: awocrunner
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 4tlkgj

## Workflow history
- 2026-08-25 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 03 of awocrunner Set (thin compat shim).

## Goal

Keep every existing `python3 tools/ipdrunner/runipd.py ...` invocation working while ensuring the driver logic exists in exactly one place (`agent_workflows.oc_runipd`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Replace the script body with a delegating shim

- [ ] E-01 Replace the body of `tools/ipdrunner/runipd.py` with a thin shim: add the repo root / package to `sys.path` if needed, `from agent_workflows import oc_runipd`, re-export the public names external callers may import (e.g. `main`, `DriverError`, and any classes the runbook/tests reference), and make `if __name__ == "__main__": raise SystemExit(oc_runipd.main(sys.argv[1:]))`. Remove ALL duplicated logic - the shim must contain no runner implementation, mirroring `tools/antigravity_execute_ipd.py`.
  - Depends on: none
  - Expected outcome: `python3 tools/ipdrunner/runipd.py <args>` runs the packaged runner; the file is a small delegating shim with no copied logic.
  - Execution state: pending

### Task group 2: Shim-parity test

- [ ] E-02 Add `tests/test_oc_runipd_shim.py` asserting that invoking the shim (via `runpy`/subprocess on `tools/ipdrunner/runipd.py`) for a non-mutating command (e.g. `status`/`report`/`--help`) yields the same result as `agent_workflows.oc_runipd.main([...])`, and that the shim re-exports the expected public names.
  - Depends on: E-01
  - Expected outcome: passing test proving the shim and the packaged runner are the same code path.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Backwards-compat shim precedent: `tools/antigravity_execute_ipd.py` inserts the tools dir on `sys.path`, imports `agy_run`, re-exports its classes, and delegates; `tools/watch-agy.py` delegates to `pwatch`. This child follows the same shape but delegates to the packaged `agent_workflows.oc_runipd`.
- The runbook `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md` documents `python3 tools/ipdrunner/runipd.py ...` invocations; those must keep working (doc text is updated in child 04 if needed, but the shim must preserve the behavior regardless).
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Maintainer | Leaving the full logic in `tools/ipdrunner/runipd.py` after packaging creates two divergent copies; it must become a delegating shim. |
| F-02 | Med | Operator | Existing `python3 tools/ipdrunner/runipd.py ...` invocations and runbook steps must not break; a shim preserves them. |

## Proposed changes (ordered, validatable)

1. Rewrite `tools/ipdrunner/runipd.py` as a thin shim delegating to `agent_workflows.oc_runipd`.
2. Add a shim-parity test.

## Deferred / out of scope (with reason)

- The packaged core (child 01) and the `aw oc` subcommand (child 02) are prerequisites, not part of this child.
- Doc updates that point operators at `aw oc runipd` are child 04; this child only guarantees the legacy path keeps working.

## Scope check

- Over-scope: none. One file rewrite plus a parity test.
- Under-scope: none. Fully preserves backward compatibility with no duplicated logic.

## Required tests / validation

- `python3 -m pytest tests/test_oc_runipd_shim.py` green.
- Manual: `python3 tools/ipdrunner/runipd.py --help` and `python3 tools/ipdrunner/runipd.py status <run-id>` behave identically to the `aw oc runipd` equivalents.
- `python3 -m pytest tests/` green overall.
- `pre-commit run --files tools/ipdrunner/runipd.py tests/test_oc_runipd_shim.py`.

## Spec / documentation sync

- Doc text pointing to the new command is child 04. N/A here beyond preserving the shim behavior the runbook relies on.

## Open questions

### OQ-01: Keep the `tools/ipdrunner/runipd.py` shim indefinitely, or deprecate it later?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED (non-blocking). Keep the shim now for zero-friction backward compatibility, consistent with the other tools' compat shims. A future deprecation (once `aw oc runipd` is the documented default) can be decided separately; it does not gate this Set.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the full contents of the new `tools/ipdrunner/runipd.py` shim pasted (showing it is small, imports `agent_workflows.oc_runipd`, and contains no runner logic); pasted output of `python3 tools/ipdrunner/runipd.py --help`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest tests/test_oc_runipd_shim.py` output showing the parity/re-export tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (preserve the legacy invocation via a thin shim with a single source of truth), confined to the shim file and its parity test.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and deferred (keep the shim now). No blocking open question remains.
2. Scope fence: touch ONLY `tools/ipdrunner/runipd.py` and `tests/test_oc_runipd_shim.py`. The shim must contain NO runner logic - delegate only. Do NOT modify the packaged core (child 01) or cli.py (child 02). If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (`python3 -m pytest ...`, the shim `--help`); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
