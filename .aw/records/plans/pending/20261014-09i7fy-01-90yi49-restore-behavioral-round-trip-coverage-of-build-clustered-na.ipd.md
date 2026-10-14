# IPD: Restore behavioral round-trip coverage of build_clustered_name and parse_clustered

- Date: 2026-10-14
- Kind: child
- Concern: The clustered filename grammar's builder (`artifact_naming.build_clustered_name`) and parser (`artifact_naming.parse_clustered`) have no live test asserting they agree. `tests/test_naming_authority_single_source.py::RoundTripTests` asserted that `parse(build(c)) == c` and `build(parse(n)) == n`; the file was deleted in `19313eed`, and plan `ev7t1w` site S-03 dispositioned the `artifact_naming` module docstring as RETIRE-UNGUARDED. A future regex or builder edit can now make the package emit a name its own validator rejects with no test failing.
- Scope: IN: a new behavioral test module that calls `build_clustered_name` and `parse_clustered` and asserts the round-trip identity in both directions, plus a builder-rejects-unknown-facet outcome and a parser-rejects-typo-facet outcome; repointing the "no live guard currently asserts this" clause in the `artifact_naming` module docstring (site `ev7t1w` S-03) at the new test. OUT: any source-reading, `ast`, regex-over-source or symbol-census check (P16); the structural single-source assertions the deleted file also carried (`SingleSourceStructuralTests`, `NormalizerDriftGuardTests`), which were code pins; the research-grammar round trip (`research_contract`) and the `prompts.build_prompt_name` delegation round trip, which are separate properties not named by backlog `09i7fy`; the docstrings at `prompts.build_prompt_name` (`ev7t1w` S-20-family) and `attention.py` (S-05), which cite the structural single-source property rather than the round trip; any change to the grammar or to executable code.
- Scope-Paths: tests/test_artifact_naming_round_trip.py, agent_workflows/artifact_naming.py, .aw/records/plans/pending/20261014-09i7fy-01-90yi49-restore-behavioral-round-trip-coverage-of-build-clustered-na.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 09i7fy
- Set: 09i7fy
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: 90yi49

## Workflow history

- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored review-ready from backlog `09i7fy`.

## Goal

Restore a behavioral guard that `build_clustered_name` and `parse_clustered` are mutual inverses on conformant clustered names, so the single naming authority cannot silently emit a name it refuses to parse, and update the S-03 docstring so it names that live guard instead of claiming none exists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Behavioral round-trip tests

- [ ] E-01 Create `tests/test_artifact_naming_round_trip.py` with a build-then-parse test: call `artifact_naming.build_clustered_name(date="20260823", set_id="myset", order=3, id6="abc123", slug="a-slug", artifact_type="ipd")`, assert the exact returned string `20260823-myset-03-abc123-a-slug.ipd.md`, then assert `parse_clustered` of it is not `None` and its `date`, `set`, `nn`, `id6`, `slug`, `type` groups equal the inputs (`int(nn) == 3`). Repeat for `artifact_type=None` (bare `.md`, `type` group `None`) and for every member of `artifact_naming.ARTIFACT_TYPE_FACETS` via `subTest`.
  - Depends on: none
  - Expected outcome: the test calls the real builder and parser and asserts on their returned values only; it reads no source file.
  - Execution state: pending

- [ ] E-02 In the same module add a parse-then-build identity test over a fixed corpus of conformant names, at minimum `20260823-myset-03-abc123-a-slug.ipd.md`, `20260823-myset-03-abc123-a-slug.md`, `20260823-my-set-11-zzz999-longer-slug.spec.md`, and the lazy-quantifier case `20260101-foo-12-abc123-bar-01-def456-slug.ipd.md` (canonical reading set `foo`, order `12`, per the `_CLUSTERED_PREFIX_RE` comment in `artifact_naming`): for each, parse, rebuild from the groups with `build_clustered_name`, and assert the rebuilt string equals the input byte for byte.
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
| F-03 | The `artifact_naming` module docstring currently reads "no live guard currently asserts this" for both properties. | After E-01..E-03 that is false for the round trip, so E-04 corrects it, keeping the structural property honestly marked unguarded. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_artifact_naming_round_trip.py` (E-01, E-02, E-03).
2. Correct the S-03 docstring in `agent_workflows/artifact_naming.py` (E-04).

## Deferred / out of scope (with reason)

- Structural single-source assertions (regex defined in exactly one module, normalizer byte-identity drift guard): these read source text and are code pins forbidden by P16.
- Research grammar round trip and `prompts.build_prompt_name` delegation round trip: valid behavioral properties but not the property named by backlog `09i7fy`; they belong to their own backlog items if wanted.
- `prompts.py` and `attention.py` "no live guard" docstrings: they cite the structural property, which stays unguarded, so they remain accurate.

## Scope check

- Over-scope: none.
- Under-scope: none. The backlog names exactly the round-trip identity of the two functions; E-01..E-03 cover both directions plus the closed-facet agreement, and E-04 keeps the in-code citation honest.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_artifact_naming_round_trip.py -v` passes, listing each new test.
- Falsifiability: temporarily changing the builder's `{order:02d}` to `{order:03d}` in a scratch copy (not committed) makes the new tests fail; revert before commit.
- `rg -n "inspect|import ast|read_text|__file__" tests/test_artifact_naming_round_trip.py` returns no hits (no source reading).
- Full bare suite `python3 -m pytest` passes.
- `git diff -- agent_workflows/artifact_naming.py` shows only docstring lines changed.

## Spec / documentation sync

N/A: no spec describes these tests, and the grammar contract is unchanged. The only prose change is the in-code `artifact_naming` module docstring (E-04).

## Open questions

### OQ-01: Should the prompt-builder and research round trips also be restored here?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Backlog `09i7fy` names only `build_clustered_name`/`parse_clustered`; the other round trips are separate properties and adding them would broaden scope (runbook Section 9 "Do not broaden scope opportunistically").

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_artifact_naming_round_trip.py -v` output showing the build-then-parse test(s) PASSED, plus pasted output of the same run against a scratch builder mutation (`{order:03d}`) showing it FAILED, proving the test is falsifiable.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the parse-then-build identity test PASSED, and the test source excerpt showing the four corpus names including `20260101-foo-12-abc123-bar-01-def456-slug.ipd.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing both rejection tests PASSED, and pasted `rg -n "inspect|import ast|read_text|__file__" tests/test_artifact_naming_round_trip.py` output showing no hits.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff -- agent_workflows/artifact_naming.py` showing only module-docstring lines changed and naming `tests/test_artifact_naming_round_trip.py`, plus the pasted `N passed` summary line of a bare `python3 -m pytest` run.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths through `aw commit 90yi49 -- <paths>`; never push. Move to `.aw/records/plans/executed/` through the tooled lifecycle only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted observed evidence with `Result: pass`.
