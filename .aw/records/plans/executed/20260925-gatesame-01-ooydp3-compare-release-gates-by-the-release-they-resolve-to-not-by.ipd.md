# IPD: Compare release gates by the release they resolve to, not by spelling

- Date: 2026-09-25
- Kind: child
- Concern: `check_engine` compares a backlog item's `Blocks-Release` with its handoff plan's by raw string, so `next` and the release id6 `next` resolves to are treated as different gates. That fires a false `check.from-backlog-gate-mismatch` and, worse, makes `evaluate_blocking_close` REFUSE a legitimate handoff close (reproduced in a scratch repo). THE DEFECT IS ALREADY LATENT IN THE LIVE TREE, not merely hypothetical: items `hdhzr2` and `x15f0q` each say `next` against a carrier saying `f33nrj`, both resolve to the same release file, and `evaluate_blocking_close(..., 'done')` returns `legitimate=False` for BOTH of them TODAY even though they are already closed. Nothing reports it because the consistency rule skips retired carriers and the closed-without-gate rule is commit-scoped, so the refusal surfaces only when such a close is re-staged or the opt-in hook runs.
- Scope: IN: one shared helper in `check_engine.py` deciding whether two gate values denote the same release, used at the two comparison sites (`evaluate_blocking_close`'s HANDOFF branch and `check_release_gate_consistency`'s mismatch branch); tests. OUT: `check.blocks-release-dangling` (an unresolvable value stays that rule's job); `attention.py`, which already resolves before comparing and so does not share the defect.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_release_gate.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Set: gatesame
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: ooydp3
- From-Backlog: 4le6yz
- Blocks-Release: next

## Workflow history
- 2026-09-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ooydp3 verified (set gatesame, attempt 1).
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 6 findings PR-A01..PR-A06 all FIXED, 4 decisions D-1..D-4 recorded; review record written; reproduced F-1/F-2 with a control, found the defect LIVE on items hdhzr2 and x15f0q (F-4), corrected the nonexistent `basis` field to `path` (F-5), and verified all 13 existing release-gate tests pass with the fix applied; aw ipd lint --phase review-finalize conforming
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog 4le6yz. Reproduced at HEAD in a scratch repo: item `next`, plan `f33nrj`, both resolving to the same release file, yields a gate-mismatch Drift AND `evaluate_blocking_close(...,'done')` -> legitimate=False. The live tree is quiet only because the two cited carriers have since executed.

## Goal

A gate written as `next` and the same gate written as the release's id6 are one gate everywhere the toolkit compares them.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: shared comparison

- [x] E-01 Add `_same_release(repo_root, a, b) -> bool` in `check_engine.py`: True when the strings are equal, or when `releases.resolve_release(repo_root, a)` and `releases.resolve_release(repo_root, b)` both resolve and return the same path. If either does not resolve, fall back to string equality (the dangling case is `check.blocks-release-dangling`'s job, not this one's). Guard `None` explicitly: a carrier gate is legitimately `None` when the artifact carries no `- Blocks-Release:` line at all, and `_from_backlog_carrier_index` keeps that DISTINCT from the empty string on purpose, so `None` must never resolve or compare equal to a real gate.
  - VERIFIED AT REVIEW that this exact predicate gives the five answers it must: `('next','f33nrj')` True, `('f33nrj','f33nrj')` True, `('next','zzzzzz')` False where `zzzzzz` is a DIFFERENT (shipped) release, `('next','nope99')` False via the string fallback, and `('next','2.0.0')` True. That last one is a SIDE EFFECT the plan did not claim and the executor should know about: `resolve_release` also accepts a VERSION string, so the helper unifies `next`, the id6 and the version spelling. That is correct and desirable, but it widens the change beyond the two spellings in the title; do not treat a version-spelling test as out of scope.
  - Depends on: none
  - Expected outcome: the helper exists and is pure apart from the release lookup.
  - Execution state: performed

- [x] E-02 Use `_same_release` at both comparison sites: `evaluate_blocking_close`'s HANDOFF branch (the `carrier_br == blocks_release` test) and `check_release_gate_consistency`'s mismatch test (`carrier_br != item_br`). Resolve each release at most once per call, not once per carrier.
  - THE CACHING INSTRUCTION IS PRUDENCE, NOT A MEASURED FIX, and saying so keeps a later reader from mistaking it for a hot path. Measured on this repository: exactly 1 release record exists, one `resolve_release` call costs about 0.2ms, and the worst uncached case across all 259 carrier rows is about 0.05s. So caching buys little TODAY. Do it anyway, because `resolve_release` READS every release file on every call and this module has already learned this lesson twice: `_from_backlog_carrier_index`'s own docstring records a measured 54x regression (11.13s vs 207ms) from a per-item re-walk, and says `release_gate_warnings` had to learn it first. Resolve once per call, not once per carrier.
  - A THIRD SURFACE INHERITS THIS FIX FOR FREE, which is worth stating so nobody adds a third call site: `check.blocking-item-closed-without-gate` calls `evaluate_blocking_close` rather than comparing gates itself, so fixing the HANDOFF branch fixes the commit-scoped hand-edit backstop and the `aw backlog set done` setter at the same time. Do not introduce a comparison there.
  - Depends on: E-01
  - Expected outcome: no raw string comparison of two gate values remains in those two functions.
  - Execution state: performed

### Task group 2: tests

- [x] E-03 Add tests to `tests/test_check_engine_release_gate.py` (13 tests passing at review; reuse its `_create_minimal_repo` helper, which already writes one `planned` release `rel001`): (a) item `next` + open plan with `From-Backlog` and the release id6 -> no `check.from-backlog-gate-mismatch`; (b) same pair -> `evaluate_blocking_close(..., 'done')` is legitimate and its `path` field is `"HANDOFF"`; (c) plan naming a DIFFERENT release id6 -> mismatch still reported.
  - THE FIELD IS `path`, NOT `basis`. `CloseVerdict` is a NamedTuple of `(legitimate, severity, reason, fixes, path)` and the legitimacy-route name lives in `path`; there is no `basis` attribute, and asserting on one raises `AttributeError` (the reviewer hit exactly that while reproducing F-1). The plan's original wording said "basis `HANDOFF`", which would have sent the executor to a nonexistent field.
  - ADD (d) THE UNRESOLVABLE-`next` CASE, because it is the one behavior OQ-01 decides and no item tested it: with TWO `planned` releases, `resolve_release(repo,'next')` returns None by design, so the helper falls back to string equality and the pair `next`/`rel001` is STILL treated as a mismatch. Assert that, so the string fallback is pinned rather than assumed, and note `check.blocks-release-dangling` is what reports the ambiguity (verified at review: that rule fires on exactly that fixture).
  - Depends on: E-02
  - Expected outcome: all four pass; (a) and (b) fail against the pre-change comparison, and (c) and (d) pass both before and after (they are the no-regression half).
  - Execution state: performed

- [x] E-04 Run the bare suite and `python3 -m agent_workflows check release-gates --agent` on the real tree.
  - THE LIVE CHECK CANNOT DEMONSTRATE THE FIX, so report it for what it is. Measured at review: `check release-gates` is already `conforms` with 0 findings BEFORE any change, because the two real `next`-versus-id6 pairs in the tree (`hdhzr2`, `x15f0q`) sit behind executed carriers that the consistency rule skips. So a clean run after the change proves only no REGRESSION. The positive live evidence available is different and worth pasting: `evaluate_blocking_close` on those two items returns `legitimate=False` before the change and should return `legitimate=True` with `path="HANDOFF"` after it.
  - Depends on: E-03
  - Expected outcome: suite green; release-gates still conforms; the two named live items flip to legitimate.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `releases.resolve_release(repo_root, value)` is the one resolver for a `Blocks-Release` value, and it accepts THREE spellings, not two: `next`, an id6, and a VERSION string. `next` resolves only when exactly one release is `planned` (zero or many -> None, by design).
- `evaluate_blocking_close` is the ONE close-legitimacy predicate shared by the setter, `aw check` and the opt-in hook (AGENTS.md, Release gates), so fixing it there fixes every surface. Verified: `check.blocking-item-closed-without-gate` calls that predicate rather than comparing gates itself.
- `CloseVerdict` is a NamedTuple `(legitimate, severity, reason, fixes, path)`; the legitimacy route (`HANDOFF`/`SATISFIED`/`DE-GATED`) is the `path` field. There is no `basis` field.
- `attention.py` compares gate values only AFTER resolving them through `_resolve_release_version`, so it does not share this defect and needs no change.
- `check_engine` has twice learned that a per-item release/corpus re-walk is a measured performance defect (`_from_backlog_carrier_index`'s docstring records 11.13s vs 207ms, a 54x difference, and says `release_gate_warnings` learned it first), which is why E-02 resolves once per call.

## Findings

All measured at HEAD `79726960` unless stated (the plan cited `0c2e7970`, an ancestor; both were checked and the measurements agree). F-4 through F-6 were added at review.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `check_engine.evaluate_blocking_close` | A legitimate handoff close is refused when the item says `next` and the plan says the id6. | reproduced at review in a fresh scratch repo: `legitimate=False severity=error path=None`, reason `backlog item carries Blocks-Release 'next'; closing it 'done' would silently drop that release gate`; the control with both sides spelled `f33nrj` -> `legitimate=True`, reason `gate 'f33nrj' handed off to a From-Backlog plan or spec` |
| F-2 | MED | `check_engine.check_release_gate_consistency` | Same spelling difference reported as `check.from-backlog-gate-mismatch`. | same scratch repo: one Drift, `From-Backlog plan's Blocks-Release 'f33nrj' does not match backlog item aaaaaa's Blocks-Release 'next'`; the control emits zero Drifts |
| F-3 | INFO | live tree | Quiet today only because the cited carriers (`h90ij1`, `z1yefm`) are executed and terminal carriers are skipped. | `check release-gates` -> 0 findings |
| F-4 | MED | live tree (strengthens F-3) | THE DEFECT IS ALREADY LATENT IN THE REAL TREE, NOT ONLY IN A SCRATCH REPO, which raises this from a hypothetical to a live inconsistency. Items `hdhzr2` and `x15f0q` each carry `next` against a carrier carrying `f33nrj`; both resolve to the SAME release file; and `evaluate_blocking_close(..., 'done')` returns `legitimate=False` for BOTH right now, despite both items already being `done`. It is invisible because the consistency rule skips retired carriers AND the closed-without-gate rule is commit-scoped, so the refusal appears only when such a close is re-staged or the opt-in hook runs. | driven on the real tree: the only two raw-unequal (item, carrier) gate pairs are those two, each `retired=True` and `same_release=True`; `evaluate_blocking_close` -> `legitimate=False path=None` for both; `check_release_gates` -> no rules fire |
| F-5 | MED | original E-03 | THE VALIDATION NAMED A FIELD THAT DOES NOT EXIST. E-03 asked for "legitimate with basis `HANDOFF`", but `CloseVerdict` has no `basis`; the route is `path`. An executor following it literally gets `AttributeError` (the reviewer hit exactly this while reproducing F-1) and would likely weaken the assertion to just `legitimate` rather than pinning which legitimacy route matched, which is the half that proves the HANDOFF branch specifically was fixed. | `CloseVerdict._fields` -> `('legitimate', 'severity', 'reason', 'fixes', 'path')`; `v.basis` -> `AttributeError` |
| F-6 | LOW | E-01's stated scope | THE HELPER ALSO UNIFIES THE VERSION SPELLING, which the plan neither claims nor bounds. `resolve_release` accepts a version string, so `_same_release('next','2.0.0')` is True. Correct and desirable, but it means the change is broader than the title's two spellings and a version-spelling test is in scope rather than out. | driven: `same('next','2.0.0')` -> True; `resolve_release` matches `_VERSION_RE` after the id6 branch |

## Proposed changes (ordered, validatable)

1. E-01: add the shared same-release predicate.
2. E-02: route both comparison sites through it.
3. E-03: behavior tests for same, same-close, genuinely different, and unresolvable-`next`.
4. E-04: bare suite and live release-gates check.

## Deferred / out of scope (with reason)

- RECONCILING the two live items `hdhzr2` and `x15f0q` (F-4), whose gates are spelled `next` against carriers spelled `f33nrj`. The fix makes both read as legitimate handoffs, so no record edit is needed and none is proposed; they are named here so a later reader knows the latent inconsistency was found and deliberately left to resolve itself rather than overlooked. Re-spelling either record by hand would be a history edit for no benefit.
  - Carrier-Declined: nothing is outstanding. The fix resolves both without a record change, verified at review by driving the predicate; there is no residual work to hand off.
- `attention.py`'s gate comparisons. Inspected at review and NOT defective: it resolves each value through `_resolve_release_version` before comparing.
  - Carrier-Declined: nothing is outstanding; there is no defect to carry.

## Scope check

- Over-scope: none. E-03 gained a fourth case and E-04 gained a live-item assertion; neither is new scope, since both validate the same one-helper change (the string fallback OQ-01 decides, and the live effect F-4 measures).
- Under-scope: none known, and this was checked rather than assumed. A grep across the package found gate-value comparisons only in `check_engine` (the two named sites) and `attention.py`, and the latter already resolves first. The third consumer, `check.blocking-item-closed-without-gate`, delegates to `evaluate_blocking_close` and so inherits the fix without a third call site.

## Required tests / validation

- `python3 -m pytest tests/test_check_engine_release_gate.py -o addopts="" -q` plus the V-03 revert.
- Bare `python3 -m pytest`.

## Spec / documentation sync

N/A: the release-gate contract in AGENTS.md already says `next` resolves to the single planned release; this makes the code honor it. No spec text changes.

## Open questions

### OQ-01: When one side cannot be resolved, should the comparison fail closed?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No, resolved from repository evidence: an unresolvable value is already reported at error by `check.blocks-release-dangling`, so falling back to string equality here avoids double-reporting while never treating two different releases as one. Re-verified at review, including the case that makes it concrete: with TWO `planned` releases, `resolve_release(repo,'next')` returns None by design, so an item spelled `next` against a carrier spelled with an id6 is STILL treated as a mismatch and the close is STILL refused. That is the correct outcome (the item genuinely denotes no single release), and `check.blocks-release-dangling` does fire on that exact fixture. E-03 case (d) now pins it, because it was the one behavior this question decides and no item tested it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the helper's diff. A DIFF ALONE IS NOT ENOUGH: also paste the helper's observed answers on the five cases E-01 names (`('next',<id6>)` True, `(<id6>,<id6>)` True, `('next',<a DIFFERENT release id6>)` False, `('next','<unresolvable>')` False, `('next','<the version string>')` True), plus a `None` carrier gate against a real gate returning False.
  - Observed evidence: Diff of helper verified in check_engine.py and 8 test cases evaluated via Python script with expected answers.
    Diff of helper in `agent_workflows/check_engine.py`:
    ```python
    def _same_release(
        repo_root: Path,
        a: Optional[str],
        b: Optional[str],
        *,
        cache: Optional[Dict[str, Optional[Path]]] = None,
    ) -> bool:
        """True when two Blocks-Release gate values denote the same release.

        Matches if strings are equal, or if both resolve to the same release record path
        via `releases.resolve_release`. If either does not resolve, falls back to string
        equality. Guards None explicitly: a None gate (meaning no Blocks-Release line)
        never resolves or compares equal to a real gate.
        """
        if a is None or b is None:
            return a == b
        if a == b:
            return True

        from agent_workflows import releases as _releases

        def _resolve(val: str) -> Optional[Path]:
            if cache is not None:
                if val in cache:
                    return cache[val]
                target = _releases.resolve_release(repo_root, val)
                cache[val] = target
                return target
            return _releases.resolve_release(repo_root, val)

        ra = _resolve(a)
        rb = _resolve(b)
        if ra is not None and rb is not None:
            return ra == rb
        return a == b
    ```
    Observed answers from Python script on synthetic fixture with planned rel001 (v1.0.0) and shipped rel002 (v2.0.0):
    ```
    _same_release(root, 'next', 'rel001') -> True
    _same_release(root, 'rel001', 'rel001') -> True
    _same_release(root, 'next', 'rel002') -> False
    _same_release(root, 'next', 'nope99') -> False
    _same_release(root, 'next', '1.0.0') -> True
    _same_release(root, None, 'rel001') -> False
    _same_release(root, 'rel001', None) -> False
    _same_release(root, None, None) -> True
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of both sites and `grep -n "carrier_br ==\|carrier_br !=" agent_workflows/check_engine.py` showing no raw comparison remains.
  - ALSO REQUIRED: show the release is resolved at most ONCE per call rather than once per carrier (point at the caching in the diff), and confirm no comparison was added to `check.blocking-item-closed-without-gate`, which must keep delegating to `evaluate_blocking_close`.
  - Observed evidence: Both comparison sites updated with caching; grep confirmed 0 raw comparisons remain.
    Diff of both comparison sites in `agent_workflows/check_engine.py`:
    ```diff
    @@ evaluate_blocking_close:
             if item_id6:
    +            release_cache: Dict[str, Optional[Path]] = {}
                 for _p, carrier_br in find_from_backlog_artifacts(repo_root, item_id6):
    -                if carrier_br == blocks_release:
    +                if _same_release(
    +                    repo_root, carrier_br, blocks_release, cache=release_cache
    +                ):
                         return CloseVerdict(
                             True,
                             "ok",

    @@ check_release_gate_consistency:
    +    release_cache: Dict[str, Optional[Path]] = {}
         for target_id6, carriers in _from_backlog_carrier_index(repo_root).items():
             if target_id6 not in item_gate:
                 continue  # dangling From-Backlog is check.from-backlog-dangling's job (ku93tn)
             item_br, _item_path = item_gate[target_id6]
             for p, carrier_br in carriers:
                 if is_retired(p):
                     continue
    -            if carrier_br != item_br:
    +            if not _same_release(
    +                repo_root, carrier_br, item_br, cache=release_cache
    +            ):
                     kind = "spec" if str(p).endswith(".spec.md") else "plan"
    ```
    Verification that no raw comparison remains:
    ```
    $ grep -n "carrier_br ==\|carrier_br !=" agent_workflows/check_engine.py
    # Exit 1 (no lines found)
    ```
    Caching verification: `release_cache: Dict[str, Optional[Path]] = {}` is instantiated once outside the inner carrier loops in both `evaluate_blocking_close` and `check_release_gate_consistency`, and passed as `cache=release_cache` to `_same_release`. Inside `_same_release`, `_resolve(val)` reads and populates `cache[val]`, resolving each unique gate value at most once per call.
    Confirmation for `check.blocking-item-closed-without-gate`: Rule 1 in `check_release_gate_consistency` was not modified; it continues delegating exclusively to `evaluate_blocking_close` with no raw gate comparison.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the four tests passing; then restore the raw `!=` / `==` comparisons IN THE WORKTREE, paste (a) and (b) FAILING while (c) and (d) still pass, and restore. That split is the point: (c) and (d) passing in BOTH states is what proves the change did not simply stop reporting mismatches.
  - ALSO REQUIRED: paste the WHOLE file's run, whose baseline at review was `13 passed in 0.70s`, so the new count must be 17. Verified at review that all 13 existing tests still pass with the fix's suppression applied, so a regression there is a real finding rather than expected churn.
  - Observed evidence: Four tests pass; reversion to raw comparisons caused tests (a) and (b) to fail while (c) and (d) passed; whole file 20 passed.
    Four tests passing with fix:
    ```
    $ python3 -m pytest tests/test_check_engine_release_gate.py -k "test_gate_mismatch or test_evaluate_blocking_close_legitimate" -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- [sanitized]/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=3711616856
    rootdir: [sanitized]/agent-workflows
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 20 items / 16 deselected / 4 selected

    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_evaluate_blocking_close_legitimate_when_next_and_id6_resolve_to_same_release PASSED [ 25%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_gate_mismatch_unresolvable_next_falls_back_to_string_mismatch PASSED [ 50%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_gate_mismatch_not_reported_when_next_and_id6_resolve_to_same_release PASSED [ 75%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_gate_mismatch_reported_for_genuinely_different_release PASSED [100%]

    ======================= 4 passed, 16 deselected in 0.29s =======================
    ```
    Four tests run with raw comparisons restored in worktree (a and b fail, c and d pass):
    ```
    $ python3 -m pytest tests/test_check_engine_release_gate.py -k "test_gate_mismatch or test_evaluate_blocking_close_legitimate" -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- [sanitized]/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=1376185530
    rootdir: [sanitized]/agent-workflows
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 20 items / 16 deselected / 4 selected

    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_gate_mismatch_reported_for_genuinely_different_release PASSED [ 25%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_evaluate_blocking_close_legitimate_when_next_and_id6_resolve_to_same_release FAILED [ 50%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_gate_mismatch_not_reported_when_next_and_id6_resolve_to_same_release FAILED [ 75%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_gate_mismatch_unresolvable_next_falls_back_to_string_mismatch PASSED [100%]

    =================================== FAILURES ===================================
    _ TestCheckEngineReleaseGate.test_evaluate_blocking_close_legitimate_when_next_and_id6_resolve_to_same_release _
        ...
        verdict = check_engine.evaluate_blocking_close(repo, bug_file, "done")
    >   self.assertTrue(verdict.legitimate)
    E   AssertionError: False is not true

    tests/test_check_engine_release_gate.py:612: AssertionError
    _ TestCheckEngineReleaseGate.test_gate_mismatch_not_reported_when_next_and_id6_resolve_to_same_release _
        ...
        findings = check_engine.check_release_gates(repo)
        rules = [d.rule for d in findings]
    >   self.assertNotIn("check.from-backlog-gate-mismatch", rules)
    E   AssertionError: 'check.from-backlog-gate-mismatch' unexpectedly found in ['check.from-backlog-gate-mismatch']

    tests/test_check_engine_release_gate.py:566: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_evaluate_blocking_close_legitimate_when_next_and_id6_resolve_to_same_release
    FAILED tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_gate_mismatch_not_reported_when_next_and_id6_resolve_to_same_release
    ================== 2 failed, 2 passed, 16 deselected in 0.32s ==================
    ```
    Whole file run after restoring fix (note: commit 5a47dd9b added 3 tests for configurable work-kinds, bringing baseline from 13 to 16; total with 4 new tests is 20):
    ```
    $ python3 -m pytest tests/test_check_engine_release_gate.py -o addopts="" -q
    ....................                                                     [100%]
    20 passed in 1.02s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the release-gates result line, then paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - ALSO REQUIRED, because the release-gates line alone is not evidence of the fix (it is `conforms` with 0 findings BEFORE the change too): paste `evaluate_blocking_close` on the two live items `hdhzr2` and `x15f0q` showing `legitimate=True` with `path="HANDOFF"`, and state that both returned `legitimate=False` at review before the change. Do not present the clean release-gates run as proof the fix works; label it a no-regression check.
  - Observed evidence: Release-gates CLI check conforms (no-regression); bare pytest suite 2254 passed; live items hdhzr2 and x15f0q flip to legitimate=True path="HANDOFF".
    Release-gates CLI check (no-regression check):
    ```
    $ python3 -m agent_workflows check release-gates --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"release-gates","findings":0,"evidence":["inventory","rules"],"next":"aw releases list"}
    ```
    Bare pytest suite execution:
    ```
    $ python3 -m pytest
    2254 passed, 1 skipped, 3 warnings in 47.45s
    ```
    0 failed.
    Live items `hdhzr2` and `x15f0q` verification:
    Before change: both returned `legitimate=False, path=None`
    ```
    hdhzr2: legitimate=False, path=None, reason=backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate
    x15f0q: legitimate=False, path=None, reason=backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate
    ```
    After change: both return `legitimate=True, path="HANDOFF"`
    ```
    hdhzr2: legitimate=True, path=HANDOFF, reason=gate 'next' handed off to a From-Backlog plan or spec
    x15f0q: legitimate=True, path=HANDOFF, reason=gate 'next' handed off to a From-Backlog plan or spec
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. One shared predicate and two call sites in `check_engine`, which changes when the toolkit REFUSES a release-gate close. The direction is MORE PERMISSIVE in exactly one situation (two spellings that resolve to the same release file), and it is deliberately NOT more permissive anywhere else: a genuinely different release still mismatches, an unresolvable `next` still falls back to string equality and still refuses, and a `None` carrier gate never matches a real one, each verified at review. Approval also covers a side effect the plan's title does not imply: because `resolve_release` accepts a VERSION string, the helper unifies `next`, the id6 AND the version spelling (F-6). And it covers a THIRD surface implicitly, because `check.blocking-item-closed-without-gate` and the `aw backlog set done` setter both delegate to `evaluate_blocking_close`.

THIS IS A LIVE INCONSISTENCY, NOT A HYPOTHETICAL, which is the fact most relevant to priority. Items `hdhzr2` and `x15f0q` in this tree each fail `evaluate_blocking_close` TODAY while already being `done` (F-4). Nothing reports it because the consistency rule skips retired carriers and the closed-without-gate rule is commit-scoped, so the refusal is latent until such a close is re-staged or the opt-in hook runs. The fix resolves both without any record edit.

Scope fence (a DECLARATION for reconciliation, not a stop directive): within `agent_workflows/check_engine.py` only the new `_same_release` helper and the two comparison expressions it replaces (`evaluate_blocking_close`'s HANDOFF branch and `check_release_gate_consistency`'s mismatch branch); no change to `_from_backlog_carrier_index`, `is_retired`, the commit-scoped rule, or `check.blocks-release-dangling`. Within `tests/test_check_engine_release_gate.py` only the four added tests, reusing the existing `_create_minimal_repo`. `agent_workflows/releases.py` and `agent_workflows/attention.py` are expected to need NO edit (the helper CONSUMES `resolve_release` unchanged; `attention` already resolves before comparing). No backlog or release RECORD is edited. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Three claims here are specifically easy to fake and must not be: V-04's `check release-gates` line, which is `conforms` with 0 findings BEFORE the change and therefore proves only no regression; V-03's (c)/(d)-pass-in-both-states split, which is the only evidence the fix did not simply stop reporting mismatches; and V-02's caching claim, which a diff can assert without implementing.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if case (c), a genuinely different release, stops being reported after the change, stop and report, because silently unifying two real releases is strictly worse than the false refusal this plan fixes; if any of the 13 existing tests in `tests/test_check_engine_release_gate.py` fails (review verified all 13 pass with the fix's suppression applied), stop and report which, since that means a behavior this fix was believed not to touch has moved.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then set backlog item `4le6yz` `done` with `--evidence` citing the executed plan. It carries `- Blocks-Release: next`, which this plan inherits, so the gate is preserved by that handoff and no separate de-gating is required. Note the pleasing consequence: after this fix, that very close is evaluated by the predicate this plan repairs.
