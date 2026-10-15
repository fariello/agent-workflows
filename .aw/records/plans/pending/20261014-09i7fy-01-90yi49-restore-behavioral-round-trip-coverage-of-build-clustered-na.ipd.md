# IPD: Restore behavioral round-trip coverage of build_clustered_name and parse_clustered

- Date: 2026-10-14
- Kind: child
- Concern: The clustered filename grammar's builder (`artifact_naming.build_clustered_name`) and parser (`artifact_naming.parse_clustered`) have no live test asserting they agree. `tests/test_naming_authority_single_source.py::RoundTripTests` asserted that `parse(build(c)) == c` and `build(parse(n)) == n`; the file was deleted in `19313eed`, and plan `ev7t1w` site S-03 dispositioned the `artifact_naming` module docstring as RETIRE-UNGUARDED. A future regex or builder edit can now make the package emit a name its own validator rejects with no test failing.
- Scope: IN: a new behavioral test module that calls `build_clustered_name` and `parse_clustered` and asserts the round-trip identity in both directions, plus a builder-rejects-unknown-facet outcome and a parser-rejects-typo-facet outcome; repointing the "no live guard currently asserts this" clause in the `artifact_naming` module docstring (site `ev7t1w` S-03) at the new test. OUT: any source-reading, `ast`, regex-over-source or symbol-census check (P16); the structural single-source assertions the deleted file also carried (`SingleSourceStructuralTests`, `NormalizerDriftGuardTests`), which were code pins; the research-grammar round trip (`research_contract`) and the `prompts.build_prompt_name` delegation round trip, which are separate properties not named by backlog `09i7fy`; the docstrings at `prompts.build_prompt_name` (`ev7t1w` S-20-family) and `attention.py` (S-05), which cite the structural single-source property rather than the round trip; any change to the grammar or to executable code.
- Scope-Paths: tests/test_artifact_naming_round_trip.py, agent_workflows/artifact_naming.py, .aw/records/plans/pending/20261014-09i7fy-01-90yi49-restore-behavioral-round-trip-coverage-of-build-clustered-na.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 09i7fy
- Set: 09i7fy
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: 90yi49

## Workflow history
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-15 reviewed (aw set): plan-review applied revisions

- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored review-ready from backlog `09i7fy`.

## Goal

Restore a behavioral guard that `build_clustered_name` and `parse_clustered` are mutual inverses on conformant clustered names, so the single naming authority cannot silently emit a name it refuses to parse, and update the S-03 docstring so it names that live guard instead of claiming none exists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Behavioral round-trip tests

- [ ] E-01 Create `tests/test_artifact_naming_round_trip.py` with a build-then-parse test: call `artifact_naming.build_clustered_name(date="20260823", set_id="myset", order=3, id6="abc123", slug="a-slug", artifact_type="ipd")`, assert the exact returned string `20260823-myset-03-abc123-a-slug.ipd.md`, then assert `parse_clustered` of it is not `None` and its `date`, `set`, `nn`, `id6`, `slug`, `type` groups equal the inputs (`int(nn) == 3`). Repeat for `artifact_type=None` (bare `.md`, `type` group `None`) and for every member of `artifact_naming.ARTIFACT_TYPE_FACETS` via `subTest`. Import the module (`from agent_workflows import artifact_naming`) and call both functions through the module attribute (`artifact_naming.build_clustered_name(...)`, `artifact_naming.parse_clustered(...)`), never `from agent_workflows.artifact_naming import build_clustered_name`, so the falsifiability probe in V-01 can substitute a mutant without editing production source.
  - Depends on: none
  - Expected outcome: the test calls the real builder and parser and asserts on their returned values only; it reads no source file.
  - Execution state: pending

- [ ] E-02 In the same module add a parse-then-build identity test over a fixed corpus of conformant names, at minimum `20260823-myset-03-abc123-a-slug.ipd.md`, `20260823-myset-03-abc123-a-slug.md`, `20260823-my-set-11-zzz999-longer-slug.spec.md`, and the lazy-quantifier case `20260101-foo-12-abc123-bar-01-def456-slug.ipd.md` (canonical reading set `foo`, order `12`, per the `_CLUSTERED_PREFIX_RE` comment in `artifact_naming`): for each, parse, rebuild from the groups with `build_clustered_name`, and assert the rebuilt string equals the input byte for byte. For the lazy-quantifier entry also assert `set == "foo"`, `nn == "12"` and `slug == "bar-01-def456-slug"`, because a greedy set group still round-trips that name byte for byte (it reads set `foo-12-abc123-bar`, order `01`), so identity alone would not catch the regression the `_CLUSTERED_PREFIX_RE` comment ("THE LAZY QUANTIFIER IS LOAD-BEARING") warns about.
  - Depends on: E-01
  - Expected outcome: `build(parse(name)) == name` holds for every corpus entry, including a hyphenated set id and an embedded `-NN-id6-` lookalike inside the slug.
  - Execution state: pending

- [ ] E-03 In the same module add two rejection-outcome tests: `build_clustered_name(..., artifact_type="ipdd")` raises `ValueError`, and `parse_clustered("20260823-myset-03-abc123-a-slug.ipdd.md")` returns `None` (closed facet enum, OQ-03 in the module docstring), so builder and parser agree on what is NOT legal as well as what is.
  - Depends on: E-01
  - Expected outcome: both rejection outcomes asserted via return value or raised exception.
  - Execution state: pending

### Task group 2: Repoint the S-03 citation

- [ ] E-04 Edit the `agent_workflows/artifact_naming.py` module docstring sentence beginning "the round-trip and single-source properties were asserted in ``tests/test_naming_authority_single_source.py``, deleted in ``19313eed``; no live guard currently asserts this" so it states the ROUND-TRIP property is now asserted behaviorally by ``tests/test_artifact_naming_round_trip.py`` while the structural single-source property remains unguarded (it was a source-reading pin and is deliberately not restored, P16). Keep the remaining text of the docstring, including the golden-snapshot retirement note, unchanged.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: docstring-only diff in `artifact_naming.py`; no executable line changes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Test outcomes, not code structure (AGENTS.md execution contract, GUIDING_PRINCIPLES P16): restored coverage must call functions and assert on real outputs; never read production source with `inspect`, `ast`, regex or substring search. The backlog item `09i7fy` restates this: "only behavioral outcomes may be restored, never a source-reading pin (P16)".
- The deleted file mixed behavioral and structural tests: `git show 19313eed7^:tests/test_naming_authority_single_source.py` shows `SingleSourceStructuralTests` (reads package `.py` text for the regex signature, a code pin) alongside `RoundTripTests.test_clustered_build_then_parse` and `RoundTripTests.test_clustered_parse_then_build_is_identity` (behavioral). Only the latter shape is restored.
- Existing tests use `unittest.TestCase` classes runnable under pytest (e.g. `tests/test_attention.py::NameGrammarAgreesWithTheNamingAuthorityTests`), and import the authority as `from agent_workflows import artifact_naming`.
- The suite is run bare as `python3 -m pytest` (repo-local development contract in AGENTS.md); narrowed runs use `python3 -m pytest -o addopts="" <path>` for per-test counts.
- Citation sites and dispositions are recorded in executed plan `ev7t1w` (`20261011-iosmvn-03-ev7t1w-...`) E-02 Disposition Table; S-03 is `artifact_naming.py` module docstring, RETIRE-UNGUARDED, citing `RoundTripTests` deleted in `19313eed`. That executed plan is not edited (execution contract).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Consequence |
|---|---|---|
| F-01 | `rg -n "build_clustered_name" tests/` returns no hits; `parse_clustered` appears in `tests/test_attention.py`, `tests/test_artifact_adopt.py`, `tests/test_plans_rename_selectors.py`, but none of them calls `build_clustered_name` and asserts the inverse relation. | The round-trip property is unguarded, as `ev7t1w` S-03 recorded. |
| F-02 | `artifact_naming.build_clustered_name` kebab-cases `set_id` and `slug` via `artifact_core.kebab` and formats `order` as `{order:02d}`; `artifact_naming._CLUSTERED_RE` uses a lazy `set` group and a closed `_FACET_ALT` facet group. | The inverse relation holds only for already-kebab, two-digit-order inputs; the test corpus must use conformant inputs (which is what the deleted test asserted). |
| F-04 | Review probe: under a greedy `set` group (`[a-z0-9-]+` instead of `[a-z0-9-]+?` in `artifact_naming._CLUSTERED_RE`), `20260101-foo-12-abc123-bar-01-def456-slug.ipd.md` parses as set `foo-12-abc123-bar`, order `01`, slug `slug`, and still rebuilds byte for byte. | Identity alone cannot guard the lazy quantifier; E-02 pins the canonical groups for that entry, and the V-02 probe proves it. |
| F-05 | `git show 80db6750c^:tests/test_naming_authority_single_source.py` and `git show 19313eed7^:...` both contain `RoundTripTests`, so the round-trip tests survived `80db6750c` and were removed in `19313eed`. | The E-04 docstring may keep naming `19313eed` as the deletion commit for the round trip. |
| F-03 | The `artifact_naming` module docstring currently reads "no live guard currently asserts this" for both properties. | After E-01..E-03 that is false for the round trip, so E-04 corrects it, keeping the structural property honestly marked unguarded. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_artifact_naming_round_trip.py` (E-01, E-02, E-03).
2. Correct the S-03 docstring in `agent_workflows/artifact_naming.py` (E-04).

## Deferred / out of scope (with reason)

- Structural single-source assertions (regex defined in exactly one module, normalizer byte-identity drift guard): these read source text and are code pins forbidden by P16.
  - Carrier-Declined: P16 forbids restoring source-reading pins, so there is no obligation to carry; the property stays deliberately unguarded and the module docstring says so (E-04).
- Research grammar round trip and `prompts.build_prompt_name` delegation round trip: valid behavioral properties but not the property named by backlog `09i7fy`; they belong to their own backlog items if wanted.
  - Carrier-Declined: not named by backlog `09i7fy` and no defect is recorded against them, so filing one is a maintainer's choice, not an obligation of this plan (OQ-01).
- `prompts.py` and `attention.py` "no live guard" docstrings: they cite the structural property, which stays unguarded, so they remain accurate.
  - Carrier-Declined: the docstrings are accurate as written, so nothing is outstanding.

## Scope check

- Over-scope: none.
- Under-scope: none. The backlog names exactly the round-trip identity of the two functions; E-01..E-03 cover both directions plus the closed-facet agreement, and E-04 keeps the in-code citation honest.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_artifact_naming_round_trip.py -v` passes, listing each new test.
- Falsifiability, WITHOUT editing production source: a throwaway `python3 -c` driver (not committed) that imports the new test module, substitutes a mutant through the module attribute, runs the tests with `unittest`, and prints the failures. Two mutants: (a) a builder emitting `{order:03d}` (e.g. wrapping the real `artifact_naming.build_clustered_name` and replacing `-03-` with `-003-`), which must fail the E-01 and E-02 tests; (b) `artifact_naming._CLUSTERED_RE` recompiled with the lazy `set` group `[a-z0-9-]+?` made greedy, which must fail the E-02 lazy-quantifier group assertions (measured at review: under that mutant the lazy-quantifier name still round-trips byte for byte, reading set `foo-12-abc123-bar` / order `01`, so only the explicit group assertions catch it). The working tree's `agent_workflows/artifact_naming.py` must be unchanged by the probe (`git diff --stat` shows only the E-04 docstring edit).
- `rg -n "inspect|import ast|read_text|__file__|open\(" tests/test_artifact_naming_round_trip.py` returns no hits (no source reading, P16).
- Full bare suite `python3 -m pytest` shows no failure that does not also fail on the base commit (another party's failure must not block a correct execution; compare failing test ids by name against a base-commit run when anything fails).
- `git diff -- agent_workflows/artifact_naming.py` shows only docstring lines changed.

## Spec / documentation sync

N/A: no spec describes these tests, and the grammar contract is unchanged. The only prose change is the in-code `artifact_naming` module docstring (E-04).

## Open questions

### OQ-01: Should the prompt-builder and research round trips also be restored here?

- Blocking: no
- Status: resolved
- Owner: plan author (opencode); confirmed by /plan-review
- Resolution or deferral rationale: No. Backlog `09i7fy` names only `build_clustered_name`/`parse_clustered`; the other round trips are separate properties and adding them would broaden scope (runbook Section 9 "Do not broaden scope opportunistically").

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_artifact_naming_round_trip.py -v` output showing the build-then-parse test(s) PASSED (including one `subTest` per `ARTIFACT_TYPE_FACETS` member and the `None` facet), plus the pasted output of the mutant (a) probe driver described under Required tests showing those tests FAILED under the `{order:03d}` builder, and `git diff --stat -- agent_workflows/artifact_naming.py` after the probe showing no executable change.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the parse-then-build identity test PASSED, the test source excerpt showing the four corpus names and the explicit `set == "foo"` / `nn == "12"` / `slug == "bar-01-def456-slug"` assertions on `20260101-foo-12-abc123-bar-01-def456-slug.ipd.md`, and the pasted output of the mutant (b) greedy-regex probe showing the lazy-quantifier assertion FAILED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing both rejection tests PASSED, and pasted `rg -n "inspect|import ast|read_text|__file__" tests/test_artifact_naming_round_trip.py` output showing no hits.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff -- agent_workflows/artifact_naming.py` showing only module-docstring lines changed and naming `tests/test_artifact_naming_round_trip.py`, plus the pasted summary line of a bare `python3 -m pytest` run, with any failure shown to fail identically on the base commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Open questions: OQ-01 is resolved; none remain. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no pasted output does not satisfy it. Start with `aw ipd begin 90yi49`. Commit ONLY the `- Scope-Paths:`, through `aw commit 90yi49 -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Verify the staged set with `git diff --cached --name-only` before committing. The falsifiability probes substitute mutants in-process only; never commit, or leave on disk, a mutated `artifact_naming.py`.

DO NOT WIDEN. Do not change any executable line of `artifact_naming.py` or the grammar, do not restore the structural single-source or normalizer tests (P16), do not add the research or prompts round trips (OQ-01), and do not edit the `prompts.build_prompt_name` or `attention.py` docstrings or executed plan `ev7t1w`. An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`.

POST-GATE LIFECYCLE. Execution requires explicit human approval (`aw ipd set approved 90yi49`). On completion every `V-*` carries pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` must conform before the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it; executed by hand, run `aw ipd finalize 90yi49`. Never hand-roll the move or `git mv` the plan.
