# IPD: Restore behavioral coverage of global_id6s quoted-Id over-collection

- Date: 2026-10-14
- Kind: child
- Concern: `artifact_core.global_id6s` deliberately returns a conservative SUPERSET (it collects an id6 QUOTED inside a fenced code block), and no live test asserts that since `tests/test_id6_global_mint.py` was deleted in `19313eed`.
- Scope: Add one behavioral test module that drives `global_id6s` and `mint_id6` against a temp records tree and asserts the over-collection outcome; refresh the stale "no live guard" sentence in the `global_id6s` docstring.
- Scope-Paths: tests/test_id6_global_mint.py, agent_workflows/artifact_core.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: s8eaay
- Set: s8eaay
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: ztx39t
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-15 draft (opencode): created.
- 2026-10-15 to-review (opencode): authored from backlog s8eaay; behavior measured in-lane before writing.

## Goal

Restore a behavioral guard for the documented property that `artifact_core.global_id6s` over-collects quoted `- Id:` tokens (safe for minting, wrong for checking), so a future change that silently turns it into an exact census, or reuses a bounded checker reader for minting, is noticed by a failing test rather than by a minted duplicate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Restore the behavioral test

- [ ] E-01 Create `tests/test_id6_global_mint.py` with a test that materializes a temp repo containing `.aw/records/research/20260101-demo-01-own111-r.research-report.md` (YAML front matter `id: own111`, body with a fenced ```` ```markdown ```` block quoting `- Id: qut111` / `- Status: approved`), calls `artifact_core.global_id6s(root)`, and asserts both `own111` and `qut111` are in the returned set, with an assertion message explaining the superset is deliberate for minting (sk7ggr E-07) and pointing at `76w6mq`/`xvon5j` if a reader is ever bounded.
  - Depends on: none
  - Expected outcome: the new test exists, uses only `tempfile`, `pathlib` and `agent_workflows.artifact_core` calls, and reads no production source (no `inspect`, `ast`, regex or substring search over `.py` files).
  - Execution state: pending
- [ ] E-02 In the same module add a second test that drives `artifact_core.mint_id6(root, _rng=...)` against the same tree. NOTE THE RNG GRANULARITY: `generate_id6` calls `_rng(ID6_ALPHABET)` once PER CHARACTER (six calls per candidate), so the pinned `_rng` must be a per-character iterator, e.g. `chars = iter("qut111" "fre111"); _rng = lambda _alphabet: next(chars)`, which yields candidate `qut111` first and `fre111` second. Assert the minted id6 is `fre111` (the quoted id6 is refused). In the same test, as the in-suite negative control, run the identical pinned `_rng` (fresh iterator) against a sibling tree whose fixture omits the fenced quote and assert it mints `qut111`, so the test proves the refusal comes from the quotation and not from the rng.
  - Depends on: E-01
  - Expected outcome: the test asserts `mint_id6` returns `fre111` on the quoting tree and `qut111` on the non-quoting tree. Demonstrated at review (HEAD `6372c22ef`): exactly those two values were returned, and `global_id6s` returned `['own111', 'qut111']` and `['own111']` respectively.
  - Execution state: pending

### Task group 2: Docstring accuracy

- [ ] E-03 Update the sentence in the `artifact_core.global_id6s` docstring that reads "``tests/test_id6_global_mint.py`` (deleted in ``19313eed``; no live guard currently asserts this)" so it states that the restored module (backlog `s8eaay`, plan `ztx39t`) asserts the superset behavior. Change no code.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/artifact_core.py` shows a docstring-only change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- GUIDING_PRINCIPLES P16 and AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": restored coverage must call the code and assert on outputs; the deleted module's sibling `test_generate_id6_keeps_its_injectable_signature` used `inspect.signature` and is a source/structure pin, so it is deliberately NOT restored.
- The suite runs bare as `python3 -m pytest` (addopts supply `-q -n auto`); do not add `-n0`, `-q`, or `-p no:randomly`.
- Commits go through `aw commit <plan> -- <paths>`; never push.
- `artifact_core.generate_id6` takes `(existing, _rng)`; `artifact_core.mint_id6(repo_root, existing=None, _rng=None)` unions `global_id6s(repo_root)` with `existing` and delegates to `generate_id6`, so pinning `_rng` is the supported way to force a collision.

## Findings

| Ref | Evidence |
|---|---|
| F-01 | `19313eed^:tests/test_id6_global_mint.py` contained `test_the_mint_set_over_collects_quoted_ids_and_that_is_deliberate`, which built exactly the research tree described in E-01 and asserted `own111` and `qut111` in `core.global_id6s(root)`. It was deleted by `19313eed` ("test: trim test suite"). |
| F-02 | Plan `ev7t1w` (`20261011-iosmvn-03-ev7t1w-...`, Findings row S-01) classified the site `RETIRE-UNGUARDED`: `rg -n "global_id6s" tests/` returns empty; this lane confirms only `tests/test_specs_date_containment.py` mentions `mint_id6`/`global_id6s` and it does not assert the superset. |
| F-03 | Measured in this lane on 2026-10-15: building the E-01 tree in a `tempfile.TemporaryDirectory` and calling `artifact_core.global_id6s(d)` returned `['own111', 'qut111']`, so the property still holds and the restored test will pass against current code. |
| F-04 | The `global_id6s` docstring names `artifact_adopt.scan_body_identities` / `_BULLET_ID_RE` as the deliberately unbounded reader and states "no live guard currently asserts this", which becomes false once E-01 lands (hence E-03). |

## Proposed changes (ordered, validatable)

1. New `tests/test_id6_global_mint.py` with the two behavioral tests (E-01, E-02).
2. Docstring-only refresh in `agent_workflows/artifact_core.py` (E-03).

## Deferred / out of scope (with reason)

- Restoring the other tests from the deleted module (forced cross-tree and terminal collisions) is out of scope: backlog `s8eaay` names only the over-collection property (site S-01). Other sites are owned by their own backlog items.
- The `inspect.signature` pin of `generate_id6` is not restored: it is a code-structure pin forbidden by P16.
- Bounding `scan_body_identities` is explicitly not wanted (owned/decided by `76w6mq` and `xvon5j`).

## Scope check

- Over-scope: none.
- Under-scope: none; both observable halves of the property (the set contents and the mint refusal) are covered.

## Required tests / validation

- Run `python3 -m pytest -o addopts="" -v tests/test_id6_global_mint.py` and paste the output showing both named tests passing.
- Run the full suite bare `python3 -m pytest` and paste the summary line showing no new failures.
- Negative check: temporarily point the test at a tree whose quoted id is removed (or invert one assertion locally, not committed) to confirm the test can fail; paste the failing output, then revert.

## Spec / documentation sync

N/A: no spec describes `global_id6s`; the only documentation touched is the in-code docstring sentence that refers to the deleted test (E-03).

## Open questions

None. Whether to restore the signature pin was resolved from AGENTS.md/P16 (no); the fixture shape was resolved from F-01 and verified by F-03.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest tests/test_id6_global_mint.py` showing the over-collection test passing, plus pasted output of a local (uncommitted) negative run where the `qut111` assertion fails when the quoted block is removed from the fixture; and `rg -n "import inspect|inspect\.|import ast|ast\.parse|read_text\(.*\.py" tests/test_id6_global_mint.py` returning no match (exit 1).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the `mint_id6` refusal test passing, and the test source excerpt showing the per-character pinned `_rng`, the `fre111` assertion on the quoting tree, and the `qut111` assertion on the non-quoting control tree.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff agent_workflows/artifact_core.py` showing only docstring lines changed, and pasted bare `python3 -m pytest` summary line with no new failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Open questions: none. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit ztx39t -- tests/test_id6_global_mint.py agent_workflows/artifact_core.py`, verifying `git diff --cached --name-only` first; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Revert any temporary negative-check edit before committing. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize ztx39t` only after every `V-*` records `pass` and `aw ipd lint --phase pre-transition` conforms.
