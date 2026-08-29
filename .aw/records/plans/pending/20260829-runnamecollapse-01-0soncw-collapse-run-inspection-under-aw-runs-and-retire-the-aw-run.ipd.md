# IPD: Collapse run inspection under aw runs and retire the aw run noun

- Date: 2026-08-29
- Kind: child
- Concern: `aw run list` and `aw runs` are byte-identical duplicates, and the verb `aw run` runs nothing; collapse all run inspection under `aw runs` and retire the `aw run` noun.
- Scope: The CLI naming surface only: the `run` parser group in `agent_workflows/cli.py`, the dispatch in `agent_workflows/run_cli.py`, the `command_surface` declarations, the tests that invoke the verb, and the one workflow doc that cites it. No change to ledger semantics, storage, or the run viewer's rendering.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/run_cli.py, agent_workflows/command_surface.py, agent_workflows/completion.py, .aw/system/workflows/exec-set/exec-set.md, tests/test_run_recovery_cli.py, tests/test_run_evidence_completion.py, tests/test_run_viewer.py, tests/test_completion.py
- Item-Dependencies: none
- Status: to-review
- Set: runnamecollapse
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 0soncw
- From-Backlog: q5pdiy

## Workflow history

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `q5pdiy` per the maintainer's decision to collapse inspection under `aw runs`.

## Goal

Make one job have one name. Today `aw run list` and `aw runs` emit byte-identical output, and the
whole `aw run` noun is a read-only inspector holding a name that reads like "run an agent". This plan
moves every `aw run` subcommand under `aw runs`, deletes the duplicate `list`, and retires `aw run`
behind a deprecation stub, so the name is free for a future driver verb WITHOUT this plan taking on
the default-host design that a real `aw run` would additionally require.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: characterize before moving anything

- [ ] E-01 Add a characterization test that pins the CURRENT observable surface before any rename: for
      each of the twelve `run` leaves declared in `command_surface.py:759-880`
      (`show`, `evidence`, `verify-ledger`, `start`, `next`, `record`, `resume`, `cancel`, `status`,
      `finalize`, `decisions`, `questions`), assert the leaf parses and returns its documented exit
      class on a fixture ledger. This is the safety net that proves the move preserves behaviour, so
      it must be written and passing BEFORE E-03 changes any parser wiring.
  - Depends on: none
  - Expected outcome: a new test class fails if any leaf's parse or exit class changes, and passes at
    current HEAD unmodified.
  - Execution state: pending

- [ ] E-02 Add an adversarial duplicate-detection test asserting that no two distinct CLI invocations
      render byte-identical output for the run family. Seed it with the known pair
      (`aw run list` vs `aw runs`) so it FAILS at current HEAD, proving the guard actually fires, and
      keep it as the standing regression once E-04 removes the duplicate.
  - Depends on: none
  - Expected outcome: the test fails at HEAD naming the duplicate pair, and passes after E-04.
  - Execution state: pending

### Task group 2: move the surface

- [ ] E-03 Register every `run` subcommand under the `runs` parser group in `cli.py`, keeping each
      leaf's arguments, help text, and epilog identical. The       `runs` parser currently takes bare
      `targets` positionals (`cli.py:1667`) while the ledger leaves take a single required
      `target`, so the two argument shapes must coexist: preserve the existing bare
      `aw runs [targets...]` viewer behaviour and only treat the first positional as a subcommand
      when it exactly matches a registered leaf name.
  - Depends on: E-01
  - Expected outcome: every `aw runs <leaf> <target>` invocation behaves exactly as `aw run <leaf>
    <target>` did, and bare `aw runs`/`aw runs <run-id>` still renders the viewer.
  - Execution state: pending

- [ ] E-04 Delete the duplicate `list` registration (`cli.py:1548`) and drop `list`/`summary`/
      `viewer` from the alias tuple in `run_cli.run_cli` (`run_cli.py:49-52`), so exactly one spelling
      renders the viewer table.
  - Depends on: E-03
  - Expected outcome: `aw run list` no longer exists as a distinct rendering path; E-02's duplicate
    test passes.
  - Execution state: pending

- [ ] E-05 Retire the `aw run` noun as a deprecation stub rather than deleting it outright: keep the
      parser registered so a stale invocation gets an actionable message naming the `aw runs`
      replacement and a nonzero exit, instead of argparse's bare "invalid choice". Do NOT silently
      forward, because silent aliases are how the duplicate in E-04 survived unnoticed.
  - Depends on: E-03, E-04
  - Expected outcome: `aw run show X` prints a message naming `aw runs show X` and exits nonzero;
    no ledger work is performed.
  - Execution state: pending

### Task group 3: keep the declared surface honest

- [ ] E-06 Update `command_surface.py` so the declarations track reality: rename the twelve
      `run <leaf>` declarations to `runs <leaf>` preserving each one's `command_class`,
      `human_recipe`, `mutation_gate`, and `exit_contract` verbatim, and ADD the missing top-level
      `runs` declaration. `aw runs` is currently undeclared entirely (`grep -n 'command="runs'
      agent_workflows/command_surface.py` returns nothing) while all twelve `run *` leaves are
      declared, so the invested surface is the undeclared one.
  - Depends on: E-03, E-05
  - Expected outcome: `tests/test_cli_conformance_matrix.py` passes and the declared set matches the
    parser leaves for this family.
  - Execution state: pending

- [ ] E-07 Update the help/description text that names the old verb: the `"run"` and `"run <leaf>"`
      entries in the `cli.py:99` help dictionary, the `run_cli.py` module docstring and its usage
      string, and the three citations in `.aw/system/workflows/exec-set/exec-set.md:47-49`
      (`aw run status|decisions|questions <run-id>`). Note: the copies of that doc under
      `.aw/worktrees/*/` are other agents' lane checkouts and MUST NOT be touched.
  - Depends on: E-03, E-05
  - Expected outcome: no user-facing help or workflow doc instructs a reader to run `aw run <leaf>`.
  - Execution state: pending

- [ ] E-08 Update the tests that invoke the verb to the new spelling: `tests/test_run_recovery_cli.py`,
      `tests/test_run_evidence_completion.py` (lines 611-704), `tests/test_run_viewer.py`, and the
      `("run", "runs", ...)` completion expectations in `tests/test_completion.py:269,297,381`. Retain
      at least one test asserting the E-05 deprecation stub's message and exit code, so the retirement
      itself stays covered.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: full default suite green with no reference to a live `aw run <leaf>` path.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw runs` is the invested surface: it is the spelling the maintainer uses, and it reads
  `.aw/records/runs/<id>/events.jsonl`, the format the drivers actually write. The collapse direction
  is therefore "retire the duplicate and relocate the ledger surface", NOT "rename `runs` to `run`".
- The command surface is normatively declared in `command_surface.COMMAND_INVENTORY` and checked by
  `tests/test_cli_conformance_matrix.py` and `tests/test_command_surface_declarations.py`; a parser
  leaf added without a declaration is a test failure, so E-06 is mandatory, not cosmetic.
- `tests/test_command_surface_declarations.py` is `slow`-marked and EXCLUDED from the default run, and
  it carries a PRE-EXISTING failure (42 undeclared parser leaves, including `agy exec`, `completion`,
  `commit`, `finish`). That failure predates this plan. Do not adopt it and do not claim to fix it;
  just do not make it worse.
- The drivers' own verbs are `aw oc run` / `aw agy run` (`cli.py:2724,2786` register `run` as an alias
  inside those families). Retiring the top-level `aw run` noun does NOT touch them.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | `aw run list` and `aw runs` are byte-identical, not merely similar. | `python3 -m agent_workflows run list > a; python3 -m agent_workflows runs > b; diff a b` produced zero output over 967 lines. |
| F-2 | The duplication is structural: one renderer, four spellings. | `run_cli.py:49-52` maps `list`, `runs`, `summary`, and `viewer` all to `run_viewer.run_viewer_cli`. |
| F-3 | `aw run` runs nothing; it is inspection plus ledger transaction verbs. | `run_cli.py:46-82` dispatches only show/evidence/verify-ledger/start/next/record/resume/cancel/status/finalize/decisions/questions. |
| F-4 | The migration is cheap, contradicting an earlier assessment that called it a breaking migration needing its own spec. | One parser site (`cli.py:1390-1560`), one dispatch site (`cli.py:8274`), three test files invoking the verb (`grep -rln 'cli.main(["run"\|_cli("run"' tests/*.py`), one workflow doc (`exec-set.md:47-49`), zero shims or hooks. No production code shells `aw run <sub>`. |
| F-5 | `aw runs` is undeclared in the normative command surface while all twelve `run *` leaves are declared. | `grep -n 'command="runs' agent_workflows/command_surface.py` -> no matches; `grep -c 'command="run ' ...` -> 12. |
| F-6 | A real `aw run` meaning "run on the default host" is blocked on a concept that does not exist. | `project_schema.py` has `enabled_hosts` (default `["opencode","claude","antigravity"]`) but no default or preferred host field, and nothing in the pipeline defines one. |

## Proposed changes (ordered, validatable)

1. Pin the current twelve-leaf surface with a characterization test (E-01) and make the duplicate
   detectable with a test that fails at HEAD (E-02).
2. Re-register the leaves under `runs`, preserving arguments and exit contracts (E-03).
3. Remove the duplicate `list` path (E-04).
4. Turn `aw run` into a loud deprecation stub, not a silent alias (E-05).
5. Reconcile `command_surface.py` and every help/doc citation (E-06, E-07).
6. Migrate the test spellings and keep the stub covered (E-08).

## Deferred / out of scope (with reason)

- **Making `aw run <selector>` actually run something.** Deferred: it requires a default-host
  resolution concept that does not exist (F-6). This plan only FREES the name; it deliberately does
  not claim it. Conflating the two would make a cheap rename depend on an undesigned feature.
- **Wiring the run ledger.** Deferred by explicit maintainer decision on 2026-08-29: it overlaps wtiso
  Phase 2 (`rchpms`) and spec `25kzda` is still `to-review`. This plan changes only the NAME of the
  inspection surface, not whether the ledger it inspects is ever populated.
- **The pre-existing 42 undeclared parser leaves** in the slow-marked declaration test. Out of scope:
  not caused by this work, and fixing it is a separate sweep.
- **The `aw ledger start|next|record|...` split** floated in discussion (moving the transaction verbs
  to their own noun). Deferred: it is a second, larger taxonomy decision, and doing it inside this
  plan would mean two renames landing at once with no way to bisect a regression.

## Scope check

- Over-scope: none. Every E-item touches only the naming surface or its tests.
- Under-scope: the plan does not deliver a working `aw run` driver verb, by design (see Deferred). A
  reader expecting `aw run <thing>` to launch an agent after this lands will not get it; the name is
  merely freed and guarded by a deprecation stub.

## Required tests / validation

1. `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_evidence_completion.py
   tests/test_run_viewer.py tests/test_completion.py tests/test_cli_conformance_matrix.py -q` green.
2. The full default suite green, with the actual counts pasted (baseline for comparison:
   `2865 passed, 3 skipped, 4 xfailed`).
3. E-02's duplicate-output test demonstrated FAILING at pre-change HEAD and passing after, pasting
   both runs. A guard never seen to fail is not evidence.
4. Manual confirmation that bare `aw runs` and `aw runs <run-id>` still render the viewer table
   unchanged, by diffing against output captured before the change.

## Spec / documentation sync

- `.aw/system/workflows/exec-set/exec-set.md:47-49` must be updated (E-07); it is the only tracked
  workflow doc citing `aw run <leaf>`.
- Spec `25kzda` describes `aw run` as the deterministic run-and-verify surface. It is `to-review` and
  NOT to be edited by this plan; if the maintainer approves this collapse, that spec's naming section
  should be reconciled when the spec itself is reviewed. Flagged, not silently changed.
- No README or CHANGELOG entry is required until the collapse actually ships, since the retirement is
  a stub rather than a removal.

## Open questions

### OQ-01: Should the retired `aw run` stub be permanent or time-boxed?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: E-05 ships a stub either way, so execution is not blocked. The
  question is only whether a later release deletes it. Recommendation: keep it until a real driver
  `aw run` exists, because the stub is exactly what prevents a stale `aw run show` from being read as
  the future "run something" verb.

### OQ-02: Do the twelve leaves belong under `aw runs`, or do the ten transaction verbs belong under a separate `aw ledger` noun?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: not blocking, because moving everything to `aw runs` first is a
  strict improvement and is reversible. Deliberately deferred rather than decided here (see Deferred);
  a second split can follow once this one is proven.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the characterization test run showing all twelve leaves asserted, plus
    the `git stash`-style demonstration that it passes at pre-change HEAD unmodified. List the twelve
    leaf names actually covered, so a missing leaf is visible.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste TWO runs of the duplicate-detection test: one at pre-change HEAD showing
    it FAIL and naming the `run list` / `runs` pair, and one after E-04 showing it pass. A guard that
    was never observed failing is not accepted as evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: for each of the twelve leaves, paste the exit code of `aw runs <leaf> <target>`
    alongside the pre-change exit code of `aw run <leaf> <target>` on the same fixture, showing them
    equal. Also paste bare `aw runs` and `aw runs <run-id>` output diffed against captures taken
    before the change (expect zero diff).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the output of `aw run list` after the change (expect the E-05 stub, not a
    table) and confirm exactly one spelling renders the viewer, by showing `grep -n` of the alias
    tuple in `run_cli.py` with `list`/`summary`/`viewer` gone.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw run show <target>; echo rc=$?` showing the actionable message that
    names `aw runs show <target>` and a NONZERO rc. Additionally show that no ledger write occurred
    (the stub must not touch the store): paste the target dir listing before and after, identical.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_cli_conformance_matrix.py -q` green, plus
    `grep -c 'command="runs' agent_workflows/command_surface.py` showing 13 (twelve leaves plus the
    previously missing top-level `runs`) and `grep -c 'command="run '` showing 0.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `grep -rn 'aw run ' --include='*.md' .` filtered to TRACKED files
    (excluding `.aw/worktrees/`, `.aw/records/runs/`, `opencode-recovery/`, and other agents' lanes)
    showing zero live instructions to use `aw run <leaf>`; and `grep -n 'aw run' agent_workflows/run_cli.py`
    showing the docstring and usage string updated.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the full default suite result with actual counts (compare against the
    `2865 passed, 3 skipped, 4 xfailed` baseline; any drop in passed count must be explained), and
    paste the specific test asserting the deprecation stub's message and exit code.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. It is a user-facing
CLI naming change: even though no production code shells `aw run <sub>` (F-4), a human's muscle memory
and any personal scripts do, which is exactly why E-05 ships a loud stub instead of a silent removal.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents work concurrently in
this checkout, so verify the staged set before every commit and never sweep in their uncommitted work
or their `.aw/worktrees/*/` lane copies. When every `V-*` item carries pasted evidence and
`aw ipd lint --phase pre-transition` conforms, move this plan to `.aw/records/plans/executed/` via
`aw ipd finalize`; do not hand-move it, and do not mark it executed on the strength of the execution
checkmarks alone.
