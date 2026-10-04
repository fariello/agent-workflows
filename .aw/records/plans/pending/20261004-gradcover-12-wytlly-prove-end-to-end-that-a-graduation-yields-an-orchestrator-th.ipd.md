# IPD: Prove end to end that a graduation yields an orchestrator the runner accepts

- Date: 2026-10-04
- Kind: child
- Concern: Each child of Set `gradcover` proves its own surface, but the defect the Set exists to fix only shows across surfaces: a graduation run produced orchestrators that a later review run refused (2026-10-03). Nothing short of driving the real runner through graduate, then review, then orchestrate, over the same records, shows the surfaces agree. This is the Set's final cross-child measurement; the orchestrator `1f4faf` assigns it here rather than carrying it.
- Scope: IN: one integration test module that, inside a temp repository seeded with `--records-backend repository`, drives the real `aw oc run` entry point (in process, with the host turn and the probe replaced by scripted doubles through the existing injection seams) over a fixture backlog item through three runs: (A) graduate, where the scripted agent writes an orchestrator plus children, first with an uncovered whole-Set obligation and then, on the correction turn, with that obligation assigned to a child by id6; (B) `--action review` over the produced Set; (C) an orchestrate pass with the children marked `executed` by fixture; plus the refusal variant of (A) with the correction never made. Then the bare suite. OUT: any production code change; any real model call; changing any other test.
- Scope-Paths: tests/test_gradcover_end_to_end.py
- Item-Dependencies: executed:sbiv1j, executed:dalmk4, executed:5etev3
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 12
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: wytlly

## Workflow history

- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of orchestrator `1f4faf` (findings PR-002, PR-003): added `executed:5etev3` to `- Item-Dependencies:` because Runs B and C assert Order 04's behavior (no run-start probe on a review run; the retirement-time re-check) and Order 04 was not reachable through `sbiv1j` or `dalmk4`; added E-05/V-05, the cross-surface ONE PREDICATE parity check that the orchestrator's `## Cross-IPD validation` previously carried with no owner. This plan owns the orchestrator's Completion criteria 1, 2 and 13 (the authoring line below says 11, which is `jm27py`'s since Order 13 was added).
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 12 of Set `gradcover`, the final child, owning the whole-Set measurement named in the orchestrator's Completion criteria 1, 2 and 11.

## Goal

Show, by driving the real runner over real records, that a graduation now either hands off a Set the next review and orchestrate runs accept with no further probe call, or fails visibly with the backlog item still `open` and the uncovered passage quoted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the success path

- [ ] E-01 Write the success scenario in `tests/test_gradcover_end_to_end.py`. Seed a temp repository with one `open` backlog item (`Work-Kind: bug`, `Blocks-Release` on a fixture release). Run A: graduate it through the runner with a scripted host whose first turn writes an orchestrator, two children at `to-review`, and a `## Completion criteria` line "the full suite passes after both children" naming no owner; a scripted probe that answers "contains executions" with that line quoted; and a scripted correction turn that rewrites the line to "... Owner: `<child-2-id6>`". Assert: one correction turn spent; the backlog item ends `graduated`; a `pass` verdict is stored for the orchestrator's final digest; the refusal recorded on the first attempt quotes the line. Run B: `--action review` over the produced Set with a scripted reviewer that sets each plan `reviewed`; assert zero probe calls at run start, the orchestrator ends `reviewed`, and `IPD-REVIEW-ORCHESTRATOR-READY` passed. Run C: with the children moved to `executed` by fixture, run the orchestrate pass; assert the retirement-time re-check is served from the cache (zero probe calls) and the orchestrator is retired to `executed`.
  - Depends on: none
  - Expected outcome: all three runs complete as asserted, with the probe call counts 1 (A, first attempt) plus 1 (A, after correction), 0 (B), 0 (C).
  - Execution state: pending

### Task group 2: the refusal paths

- [ ] E-02 Write the refusal scenario: the same Run A with a correction turn that never fixes the line and `--retry-budget 1`. Assert: exactly one correction turn; the item ends `fail-gate` with code `BACKLOG-GRADUATE-SET`; the backlog item is still `open`; the lane is preserved; `aw runs` for that run shows the quoted line. Then run `aw backlog set graduated <item>` in the preserved lane's tree and assert it is refused, and `aw ipd set reviewed <orchestrator>` there and assert it is refused.
  - Depends on: E-01
  - Expected outcome: every refusal fires with the quoted line, and no record claims the Set is ready.
  - Execution state: pending

- [ ] E-03 Write the resume scenario: after E-02's refused run, integrate the preserved lane's plans into the fixture's main tree (simulating an earlier integrated handoff, the 2026-10-03 shape), then run A again with a correction that fixes the line. Assert: no `BACKLOG-GRADUATE-COUNT` duplicate refusal, no second Set written, the existing orchestrator fixed in place, the item ends `graduated`.
  - Depends on: E-02
  - Expected outcome: the resumed graduation continues the existing plans and succeeds.
  - Execution state: pending

### Task group 3: the whole suite

- [ ] E-04 Prove the scenarios can fail (revert Order 06's verifier call in a scratch copy, or monkeypatch `production_checks.backlog_graduate_set` to return no findings inside a dedicated mutation test, and paste E-02 failing), then run the bare suite and reconcile it against a baseline measured on a clean tree at this child's HEAD.
  - Depends on: E-03
  - Expected outcome: the mutation makes E-02 fail; the bare suite shows no new failing node id.
  - Execution state: pending

- [ ] E-05 Write the ONE PREDICATE parity scenario the orchestrator `1f4faf` assigns here: one fixture orchestrator whose children are all at `to-review` and whose recorded probe verdict (pre-recorded through `record_probe_verdict`, never a model call) is a FAIL with one quoted passage. Drive five surfaces over it and collect each one's findings: `aw ipd set reviewed <id6> --agent` (subprocess), `aw ipd lint --phase review-finalize --agent` (subprocess), `aw check plans --agent` (subprocess), a backlog production run whose scripted agent writes exactly that Set (in process), and `dispatch_orchestrator_item` on a copy with every child moved to `executed` by fixture (in process). Assert every surface refuses and reports the same finding code and the same quoted passage.
  - Depends on: E-01
  - Expected outcome: five refusals carrying one identical finding code and one identical quote; no surface passes the fixture.
  - Execution state: pending

## Project conventions discovered (Step 0)

- IN-PROCESS RUNNER TESTS WITH INJECTED HOSTS ARE THE ESTABLISHED PATTERN (`tests/test_backlog_production.py`, `tests/test_orchestrator_retirement.py`); the real spawn is refused under pytest by `_assert_probe_spawn_is_permitted`.
- SEED FIXTURES WITH `--records-backend repository`, or a non-interactive install may place records under `$HOME` and make controls vacuous (measured in `jei45f` F-07).
- RUN THE SUITE BARE; do not pass `-n0`, an extra `-q`, or `-p no:randomly` (`AGENTS.md` execution contract).
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The incident spanned two runs: graduations (earlier runs, items now `graduated`) and review runs on 2026-10-03 (refused). Only a test that chains production, review and orchestrate over the same records reproduces that shape. | the 11 `graduated` items and the four refused run directories named in the orchestrator |
| F-02 | The injection seams exist: production turns use the host launcher the tests already replace; the probe takes `asker`/`runner`; retirement goes through `dispatch_orchestrator_item`. | `tests/test_backlog_production.py` fixtures; `probe_orchestrator`'s `asker` parameter |

## Proposed changes (ordered, validatable)

1. Success scenario across graduate, review, orchestrate (E-01).
2. Refusal scenario with setter refusals (E-02).
3. Resume scenario over an integrated earlier handoff (E-03).
4. Mutation proof and bare suite (E-04).
5. Cross-surface parity of the one readiness predicate (E-05).

## Deferred / out of scope (with reason)

- A LIVE RUN AGAINST A REAL MODEL. Not reproducible and spends money; the scripted doubles exercise every code path a model answer reaches.
  - Carrier-Declined: tests must not spend tokens (`_assert_probe_spawn_is_permitted`)

## Scope check

- Over-scope: none. One test file.
- Under-scope: none; the Set's other surfaces are each proven by their own child.

## Required tests / validation

- Baseline bare `python3 -m pytest` on a clean tree at this child's HEAD, failing node ids recorded.
- `python3 -m pytest -o addopts="" tests/test_gradcover_end_to_end.py -q` pasted.
- The mutation run pasted.
- Bare `python3 -m pytest` after, `N passed` line pasted, reconciled against the baseline.
- `aw ipd lint` on this plan conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec or document edited. This plan measures the contract of `25kzda` 2.5b, 2.5d, 4.4, 4.9 and 5.5 and `77tr3o` R-13 as amended by Order 01.

## Open questions

### OQ-01: Should the end-to-end test be marked `slow`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: mark it `slow` only if it measures above the repository's slow threshold at execution; otherwise leave it in the default run so it guards every change. Measure and record the runtime in V-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the success scenario's assertions passing, including the probe call counts per run, the backlog item's final `- Status: graduated`, the stored verdict, and the retired orchestrator's `- Status: executed`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the refusal scenario passing, including the `BACKLOG-GRADUATE-SET` refusal text with the quote, the item's `- Status: open`, and both setter refusals' output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the resume scenario passing, including the count of Sets linked to the item (1) and the item's final `- Status: graduated`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the mutation run failing E-02 and the restored run passing; the test file's runtime; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the declared path.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the parity scenario passing, then paste, for each of the five surfaces, the finding code and quoted passage it reported (one line per surface) showing they are identical. Paste a mutation in which one surface is made to skip the shared check (monkeypatched inside the test run, never by editing production source) failing the scenario.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only the declared path through `aw commit <plan> -- <paths>`; never push. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
