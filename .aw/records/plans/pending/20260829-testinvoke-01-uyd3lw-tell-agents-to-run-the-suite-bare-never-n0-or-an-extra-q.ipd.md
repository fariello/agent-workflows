# IPD: Tell agents to run the suite bare; never -n0 or an extra -q

- Date: 2026-08-29
- Kind: child
- Concern: Nothing in the always-loaded agent contract states how to invoke the test suite, so an agent overrode the repo's `-n auto` with `-n0` (5.5x slower) and fought its own duplicated `-q` for ~19 minutes.
- Scope: The installed agent-contract text in `agent_workflows/engine.py` (the generator that owns the `aw:block` region of AGENTS.md), the regenerated AGENTS.md block, and a test asserting the guidance is present. NO change to `pyproject.toml` addopts, to any test's behavior, or to the runner.
- Scope-Paths: agent_workflows/engine.py, AGENTS.md, tests/test_agent_contract_test_invocation.py
- Item-Dependencies: none
- Status: to-review
- Set: testinvoke
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: uyd3lw
- Blocks-Release: next

## Workflow history

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from an observed live failure during the `0soncw` review run (pid 4178108), measured on this checkout.

## Goal

Give agents one unambiguous instruction for running this repo's suite, in the always-loaded contract
where they will actually see it, so no agent again disables the repo's configured parallelism or
burns minutes fighting a verbosity flag it set itself.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: state the invocation rule where agents read it

- [ ] E-01 Add a test-invocation sentence to the agent execution contract string in
      `agent_workflows/engine.py` (the `"### Agent execution contract"` block; the pasted-output
      clause is at `engine.py:1174`). It must state: run the suite with a BARE `python3 -m pytest`
      (or `make test`), because `pyproject.toml` `addopts` already supplies `-q -n auto
      --dist=worksteal -m 'not slow'`; do NOT pass `-n0` (it disables xdist and is measurably ~5.5x
      slower here) and do NOT add another `-q` (it compounds with the configured one to `-qq`, which
      suppresses the very `N passed` summary line the contract demands you paste). Name the escape
      hatch for when the counts are needed from a narrowed run: `python3 -m pytest -o addopts=""`.
  - Depends on: none
  - Expected outcome: the generator emits the rule; no other contract wording changes.
  - Execution state: pending

- [ ] E-02 Regenerate the managed `aw:block` region of `AGENTS.md` through the normal installer path
      (NOT by hand-editing the file between the `<!-- aw:block -->` / `<!-- /aw:block -->` markers at
      `AGENTS.md:3` and `AGENTS.md:60`), so the tracked file and the generator stay byte-consistent.
  - Depends on: E-01
  - Expected outcome: AGENTS.md contains the new sentence inside the managed block, and re-running
    the generator is idempotent (no further diff).
  - Execution state: pending

### Task group 2: prove the guidance is present and honest

- [ ] E-03 Add `tests/test_agent_contract_test_invocation.py` asserting the rule reached AGENTS.md,
      following the established pattern in `tests/test_backlog_graduated.py:221`
      (`test_agents_md_documents_the_contract`): assert the required phrases are present, and assert
      the section carries no em/en dash, since this is authored user-facing prose.
  - Depends on: E-02
  - Expected outcome: the test passes and fails if the guidance is removed from the generator.
  - Execution state: pending

- [ ] E-04 Add to the same test a CONSISTENCY assertion that the guidance still matches reality:
      parse the `addopts` value out of `pyproject.toml` and assert it contains `-n auto`, so that if
      someone later changes the repo default (e.g. to serial), this test fails loudly rather than
      leaving AGENTS.md instructing agents to rely on a default that no longer exists.
  - Depends on: E-03
  - Expected outcome: the doc and the config cannot silently diverge.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The AGENTS.md guidance block is MACHINE-MANAGED. `agent_workflows/engine.py` owns the region
  between `<!-- aw:block -->` and `<!-- /aw:block -->` (`AGENTS.md:3`/`AGENTS.md:60`;
  `engine.py:219-220` define the markers). Editing AGENTS.md directly would be overwritten on the
  next install, so the fix MUST land in the generator.
- The existing precedent for "assert generator wording reached AGENTS.md" is
  `tests/test_backlog_graduated.py:221-236`, which also enforces the no-em-dash rule on the authored
  section. This plan mirrors that shape rather than inventing a new one.
- `pyproject.toml:118-121` already documents the parallel-by-default intent and the `make
  test-serial` debugging escape, but those comments sit in a file an agent has no reason to open. The
  gap is placement, not absence of intent.
- `CONTRIBUTING.md:111` documents `make test` / `-n auto` for humans; the always-loaded agent
  contract says nothing, which is why the agent improvised.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The repo configures parallel-by-default. | `pyproject.toml:122`: `addopts = "-q -n auto --dist=worksteal -m 'not slow'"` |
| F-2 | `-n0` is 5.5x slower here, measured back-to-back on the same suite. | `-n auto`: `TOTAL 26.75 s`; `-n0`: `TOTAL 147.73 s` (12 cores, `nproc`) |
| F-3 | A second `-q` suppresses the summary the contract requires. | `pytest -p no:randomly -n0 --tb=no -q -rN tests/test_backlog.py` prints only `......` with no `22 passed` line; the same run with `-o addopts=""` prints `22 passed in 0.23s` |
| F-4 | The observed loop cost real time and money. | `0soncw` review (pid 4178108) ran the serial suite at least 4 times across ~19 minutes of stall gaps, reaching `$15.19` cumulative |
| F-5 | The agent diagnosed the cause and still did not fix its own flag. | Its narration: "The `-q` config suppresses the count line", after which it escalated to `-rN`, then `-v | grep -c`, then a report hook, each at full serial cost |
| F-6 | The contract demands pasted output but never says how to obtain it. | `engine.py:1174` requires "paste the ACTUAL runner output"; no sibling clause names the invocation |

## Proposed changes (ordered, validatable)

1. Add the invocation rule to the generator's execution-contract string (E-01).
2. Regenerate the managed AGENTS.md block through the installer path (E-02).
3. Assert the guidance landed, with the no-dash rule, per existing precedent (E-03).
4. Assert the guidance cannot drift from `addopts` (E-04).

## Deferred / out of scope (with reason)

- **Changing `addopts` or the parallel default.** Out of scope: the configuration is correct; the
  defect is that agents were not told about it. Touching it would invalidate F-2's measurement.
- **Making the runner reject `-n0` in agent-issued commands.** Deferred: a tool-policy denylist on
  test flags is a runner change in `oc_runipd.py`/`agy_runipd.py`, which the wtiso Set is actively
  rewriting; adding to that surface now would collide. Guidance first, enforcement later if the
  behavior recurs after this lands.
- **The two live-state test failures.** Handled by sibling plan `i79rgh` (Order 02), because they are
  a different defect: those tests are wrong, whereas this plan's subject is agent guidance. They are
  what made the loop terminal (the suite could never come back green), but fixing them does not fix
  the invocation problem and vice versa.
- **A `make test-agent` convenience target.** Deferred: one more spelling to remember is a weaker fix
  than making the bare, obvious command correct.

## Scope check

- Over-scope: none. Three files, one of which is generated and one of which is new.
- Under-scope: this plan is guidance only. It does not PREVENT an agent from passing `-n0`; a
  determined or careless agent can still do it. That enforcement is deliberately deferred above, and
  the honest claim here is "the rule is now stated where agents load it", not "the failure mode is
  impossible".

## Required tests / validation

1. `python3 -m pytest tests/test_agent_contract_test_invocation.py` green (run BARE, per the very
   rule being added).
2. Full default suite green, counts pasted, compared against the current baseline of
   `2874 passed, 3 skipped, 4 xfailed` (excluding the two live-state failures owned by `i79rgh`).
3. Generator idempotency demonstrated: run the install/regeneration twice and show the second run
   produces no diff to AGENTS.md.
4. An adversarial check that the new test actually fires: remove the guidance sentence from
   `engine.py`, regenerate, and show the test FAILS; then restore and show it passes.

## Spec / documentation sync

- `CONTRIBUTING.md:111` already documents `make test` and `-n auto` for humans and needs no change;
  this plan adds the agent-facing equivalent. If E-04 is implemented, `pyproject.toml:118-121`'s
  comment block becomes the tested source of truth for the default and needs no edit either.
- No spec governs the agent contract text; `engine.py` is the source of truth.

## Open questions

### OQ-01: Should the rule also forbid `-p no:randomly`, which the observed run also passed?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: not blocking, because `-p no:randomly` is harmless here (no
  `pytest-randomly` in the test deps at `pyproject.toml:38`, so the flag is a no-op) and did not
  contribute to either failure mode. Recommendation: stay silent on it rather than lengthening the
  contract with a rule that buys nothing; the bare-invocation instruction already implies it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n` of the new sentence in `agent_workflows/engine.py` showing it
    inside the `### Agent execution contract` string, plus a `git diff` of that hunk proving no other
    contract wording changed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new sentence as it appears in `AGENTS.md` BETWEEN the `aw:block`
    markers, and paste the output of running the regeneration twice, showing `git diff AGENTS.md` is
    empty on the second run (idempotency). Confirm no hand-edit occurred by showing the generator
    alone produces the file content.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_agent_contract_test_invocation.py` green,
    AND the adversarial run: with the sentence deleted from `engine.py` and AGENTS.md regenerated,
    paste the FAILING output; then paste it passing again after restore. A guard never observed
    failing is not accepted as evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the test passing, then paste a run with `addopts` temporarily altered to
    drop `-n auto`, showing the consistency assertion FAILS and names the drift. Restore and show
    green. Also paste the parsed `addopts` value the test read, so the assertion is not vacuous.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents and runs are ACTIVE
in this checkout (the wtiso Set holds `.aw/worktrees/` lanes and the `0soncw`/`e32j35`/`97df1z` review
run works in the main tree), so verify the staged set before every commit and never sweep in their
uncommitted work. Run the suite BARE when validating this plan, which is the rule it installs. When
every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move this
plan to `.aw/records/plans/executed/` via `aw ipd finalize`.
