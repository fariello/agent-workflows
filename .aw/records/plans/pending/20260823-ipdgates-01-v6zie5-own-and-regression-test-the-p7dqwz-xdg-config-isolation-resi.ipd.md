# IPD: Own and regression-test the p7dqwz XDG config isolation residue

- Date: 2026-08-23
- Kind: child
- Concern: When the executed IPD p7dqwz shipped its E-02/E-03 (commit 57a70b0), it ALSO edited `tests/test_empty_state_ux.py` (added `XDG_CONFIG_HOME` isolation to `ReadListVerbsEmptyStateSurfaceTests` setUp/tearDown) - OUTSIDE p7dqwz's `touch ONLY` scope fence, which named only `artifact_types.py`, `artifact_rename.py` output, the research index, docs, and `tests/test_artifact_group.py`. The change is useful (host-global Agent Workflows config can contaminate an isolation test) but was committed without authority and is currently unowned by any plan.
- Scope: Own that change prospectively and prove its necessity. Touch ONLY `tests/test_empty_state_ux.py`. Do NOT alter any application file, and do NOT edit the executed p7dqwz record.
- Status: draft
- Set: ipdgates
- Order: 1
- Highest E allocated: 01
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: v6zie5

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (decomposition of 39fz2x E-01).

## Goal

Make the previously-unauthorized `XDG_CONFIG_HOME` test isolation an OWNED, justified change of this corrective IPD, demonstrated by a regression test that FAILS without the isolation boundary (proving a hostile external Agent Workflows config could otherwise influence `ReadListVerbsEmptyStateSurfaceTests`) and PASSES with it. Cite p7dqwz and commit 57a70b0 in the test rationale so the change is no longer unowned.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Own and prove the isolation

- [ ] E-01 In `tests/test_empty_state_ux.py`, name/extract the `XDG_CONFIG_HOME` isolation clearly (a helper or documented setUp/tearDown block) and add a regression test that asserts a hostile external Agent Workflows config CANNOT influence `ReadListVerbsEmptyStateSurfaceTests` when the isolation is present, and (via the same mechanism exercised without the boundary, e.g. a sub-test that points `XDG_CONFIG_HOME` at a populated fake config) that the surface WOULD be contaminated without it. Add a docstring/comment citing p7dqwz and commit 57a70b0 as the origin of the change. Change no application file.
  - Depends on: none
  - Expected outcome: the isolation is owned by this IPD and its necessity is demonstrated by a failing-without-isolation / passing-with-isolation regression.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Commit 57a70b0 ("feat(group): ... (p7dqwz E-02, E-03)") added, in `tests/test_empty_state_ux.py` `ReadListVerbsEmptyStateSurfaceTests.setUp`, `self._old_xdg = os.environ.get("XDG_CONFIG_HOME"); os.environ["XDG_CONFIG_HOME"] = str(self.root / "cfg")`, with a matching tearDown restore - outside p7dqwz's declared scope.
- Executed IPDs are immutable; p7dqwz is cross-referenced, not edited.
- The project test stack is `unittest`-style classes run under `pytest`.

## Findings

The change itself is correct test hygiene, but it was a silent scope expansion in a terminal IPD. Owning it here (with a regression that proves it is load-bearing, not incidental) closes the concrete residue the p7dqwz verification found, without amending the terminal record.

## Proposed changes (ordered, validatable)

1. Name/extract the XDG isolation and add the failing-without / passing-with regression, citing p7dqwz + 57a70b0 (E-01).

## Deferred / out of scope (with reason)

- Editing p7dqwz or any terminal IPD: prohibited.
- Any application-code change: out of scope; this is test-ownership only.
- The broader lifecycle/scope-gate machinery: sibling Orders 02-06.

## Scope check

- Over-scope: none.
- Under-scope: none; owning the change plus a falsifiable regression is the whole concern.

## Required tests / validation

- The new regression in `tests/test_empty_state_ux.py` (failing without isolation, passing with).
- `pytest tests/test_empty_state_ux.py` and full `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- N/A (test-only ownership change; no spec or doc contract changes).

## Open questions

### OQ-01: Retain or revert the XDG isolation?

- Blocking: no
- Status: resolved
- Owner: corrective author
- Resolution or deferral rationale: RETAIN (inherited from 39fz2x OQ-01) - host-global config can contaminate the isolation test; make the reason and regression evidence explicit here so the change is owned.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the regression demonstrates contamination WITHOUT the isolation boundary and none WITH it; the test docstring/comment cites p7dqwz and 57a70b0; `git diff --name-only` for this IPD's commit shows ONLY `tests/test_empty_state_ux.py` (no application file); `pytest tests/test_empty_state_ux.py` and `pytest -n auto` are green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - own and prove the single out-of-scope test change from p7dqwz.

### Execution contract

1. Open questions RESOLVED: OQ-01 (retain) resolved.
2. Scope fence: touch ONLY `tests/test_empty_state_ux.py`. Do NOT change application code or any executed IPD. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after E-01 is performed and V-01 verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via `aw ipd finalize` if it exists by execution time, else the existing lifecycle workflow).
