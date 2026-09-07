# IPD: Surface a per-item refusal reason and its remedy in the run summary and aw runs

- Date: 2026-09-07
- Kind: child
- Concern: A run can refuse an item for a reason no surface reports. Measured 2026-09-07: the end-of-run summary's diagnostics block (`render_stream.py:2124-2150`) keys on a HARDCODED status allowlist (`dependency-blocked`, `failed-safely`, `integration-blocked`, `merge-conflict`, `interrupted`), so any other refusal produces a table row and NO diagnostic line. `aw runs`' `Issue` column (`run_viewer.py:1497`) is computed only from `missing_entirely`/`location_mismatch`/`status_mismatch`, all of which describe a plan being in the wrong DIRECTORY, so a semantic refusal leaves the column reading `no`. And neither surface has any field for a REMEDY: both report what happened, never what to do about it. This is a defect today, independent of the probe that motivated finding it, which is why it is Order 01 and depends on nothing.
- Scope: The two READ surfaces and the state they read. IN: a per-item `refusal` record (reason code, human reason, remedy) written into run state by whatever refuses; the summary's diagnostics block rendering it for ANY status rather than an allowlist; `aw runs` reporting it in the `Issue` column and in its detail view. OUT: adding any new refusal (child 03 does that); changing what any existing gate decides; the verdict cache (child 02).
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/run_viewer.py, agent_workflows/runner_shared.py, tests/test_run_order_announcement.py, tests/test_refusal_surfacing.py
- Item-Dependencies: none
- Status: to-review
- Set: orchprobe
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: r2i1b1

## Workflow history
- 2026-09-07 to-review (aw set): Authored and ready for critique: lint conforming, E/V bijection, every V-item demands pasted evidence. Set records the REJECTED syntactic-linter shape and why (it cannot separate legitimate orchestration from parent-only work, and its false positives push agents to delete the orchestration checklist), plus the deferred positive-assertion shape and its backfill cost.

- 2026-09-07 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make any refusal a run produces visible in both the end-of-run summary and `aw runs`, carrying not just what happened but what the reader should do next. After this child, a new refusal kind is surfaced by construction rather than by remembering to extend an allowlist.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: a refusal record that carries its own remedy

- [ ] E-01 Define ONE shared refusal record in `runner_shared.py` and have both hosts import it: a reason CODE (stable, machine-readable), a human REASON (what happened), and a REMEDY (what to do next). Store it on the queue item so it is durable in run state rather than only printed. The remedy field is the point: `AGENTS.md` records that a gate saying only "X is forbidden" gets complied with by DELETION, so every refusal this system produces must name the constructive action.
  - Depends on: none
  - Expected outcome: a single definition, imported by `oc_runipd` and `agy_runipd`, with the remedy as a required field rather than an optional one.
  - Execution state: pending

- [ ] E-02 Make the summary's diagnostics block render a refusal record for ANY status, replacing the hardcoded allowlist at `render_stream.py:2138-2145`. Keep the three existing special cases working verbatim (their wording is asserted by existing tests), but add a general branch so an item carrying a refusal record is reported whatever its status. Locate by SYMBOL, not line number.
  - Depends on: E-01
  - Expected outcome: an item with a refusal record always yields a diagnostic line; the existing dependency-blocked, integration-blocked, merge-conflict, and interrupted wording is unchanged.
  - Execution state: pending

- [ ] E-03 Make `aw runs` report it. The `Issue` column must read YES for an item carrying a refusal record, and the reason plus remedy must appear in the detail view. Today `has_issue` (`run_viewer.py:1497`) is a three-term expression about directory mismatches; extend it without changing what those three terms mean.
  - Depends on: E-01
  - Expected outcome: `aw runs` on a run containing a refused item shows YES and prints the reason and remedy; a clean run is unchanged.
  - Execution state: pending

- [ ] E-04 Add a REGRESSION GUARD against the allowlist shape returning. A test must fail if the summary's diagnostics block regains a closed set of statuses, because that is the exact defect F-1 records and it would silently re-hide every future refusal. Assert on behavior (an unknown status with a refusal record still yields a line), not on source text.
  - Depends on: E-02
  - Expected outcome: a test that fails if a new refusal kind would be invisible.
  - Execution state: pending

- [ ] E-05 Confirm both hosts share every symbol added, by OBJECT IDENTITY rather than grep, per the anti-re-fork discipline `2r306y`/`818uru` established. `agy_runipd` already imports ~46 names from `oc_runipd` (backlog `cnwy8g`), so a new symbol must not deepen that.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: pasted proof that each new symbol is one object shared by both hosts and defined in `runner_shared`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The wording rule is load-bearing, not stylistic. A refusal that names only the prohibition invites the destructive fix; the remedy field exists to make the constructive one obvious.
- `render_stream.py` is the ONE definition of runner wording, imported by both hosts, precisely so an improvement cannot re-fork (its own docstring cites the `Heartbeat` divergence as the failure it prevents).
- ~14 `test_run_viewer` failures are the known `agrlvw` live-repo fixture (those tests read the real repo's gitignored run records). Compare failing NODE IDS against the executing worktree's own baseline, never totals.
- Suite bare: `python3 -m pytest`. Work in an isolated worktree; this repo has concurrent agents.

## Findings

| Id | Severity | Location (2026-09-07) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `render_stream.py:2138-2145` | The diagnostics block keys on a hardcoded status allowlist, so any new refusal kind yields no line. | source read |
| F-2 | HIGH | `run_viewer.py:1497` | `has_issue` covers only directory mismatches, so a semantic refusal reads `no`. | source read |
| F-3 | HIGH | both | No remedy field exists anywhere, so advice has nowhere to live. | source read |

## Proposed changes (ordered, validatable)

1. E-01 defines the record (shared, remedy required).
2. E-02 and E-03 make each surface read it.
3. E-04 guards the allowlist shape from returning.
4. E-05 proves one definition across hosts.

## Deferred / out of scope (with reason)

- Adding any new refusal: child 03. This child makes refusals VISIBLE; producing one is separate.
- The verdict cache: child 02.
- Reworking the `agrlvw` live-repo test fixtures: agy has in-flight work there and it is a different defect.

## Scope check

- Over-scope: `tests/test_run_order_announcement.py` is in scope only for cases E-02 changes; do not refactor it.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured there and pasted, comparing failing NODE IDS not totals.

## Spec / documentation sync

N/A: this child changes no documented contract, it fixes two surfaces that already promised to report problems. Child 03 owns the spec sync for the gate it adds.

## Open questions

### OQ-01: Should an existing refusal be retrofitted to carry a remedy?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: E-02 keeps the existing wording verbatim because tests assert it. Whether `dependency-blocked` should ALSO gain a remedy ("run the prerequisite first, or clear the edge") is a nice-to-have the executor may do if it costs nothing, and must NOT do if it means rewriting asserted strings. Record which was chosen.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the record definition and a `python3 -c` showing both hosts resolve it to the SAME object, plus proof the remedy field is required (constructing one without it fails).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste rendered summary output for (a) an item with a refusal record and an UNKNOWN status, showing a diagnostic line, and (b) each of the four existing special cases, showing their wording byte-identical to before.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw runs` output for a run containing a refused item, showing `Issue` = YES and the reason plus remedy in the detail view; and for a clean run, showing no change.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the guard test passing, AND a mutation check: reintroduce the allowlist, show the guard FAILS, revert, show it passes. A guard that cannot fail is not evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted object-identity output for every symbol added, and confirmation that the count of names `agy_runipd` imports from `oc_runipd` did not increase.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved r2i1b1 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
