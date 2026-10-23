# IPD: Restore behavioral test coverage for benchmark_manifest digest keys

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `g5ypvb` (Set `trimgap`, group 8 of the `wo21z5` `## Filing plan`) carries three production keys of `agent_workflows/benchmark_manifest.py` that the `wo21z5` budget probe classified `unprovable` with reason "control survived": `BenchmarkManifest.digest`, `Ceilings.digest` and `_digest`, all under operator `return-none`, with control file `tests/test_benchmark_corpus.py`. The item's remedy is "investigate probe" (is the probe applicable at all?). Investigation at authoring HEAD `db8853d1` (F-02, F-03) answers it: the probe IS applicable, and the `raise` operator is KILLED for all three keys, but `return-none` SURVIVES for all three even with the control file now restored by executed plan `78g6ic`. The cause is that every existing test compares two digests for EQUALITY (`test_round_trip_preserves_identity_and_digest` asserts `m.digest() == rt.digest()`), and `None == None` holds, so no test pins that a digest is a real value or that it distinguishes different content. That is a genuine behavioral gap, not a probe artifact: a digest that silently returned a constant would let `benchmark_reports` pool and compare runs whose configurations differ.
- Scope: Add ONE new behavioral test module, `tests/test_benchmark_manifest_digest.py`, marked `core`, that builds manifests and ceilings through the public `benchmark_manifest.build_manifest` / `make_ceilings` / `manifest_from_dict` API and asserts on the returned digests: each is a 64-character lowercase hex string, equal for equal content, different when an identity factor or a ceiling differs, unchanged when only `usage` differs, and the manifest's `identity["ceilings_digest"]` equals its ceilings' `Ceilings.digest()`. Then re-run the three `return-none` probes with the new module in the selection and record `killed`. EXCLUDES any production-code change; EXCLUDES editing `tests/test_benchmark_corpus.py` (owned by executed `78g6ic`, and pending sibling `btubm6` also avoids it); EXCLUDES other `benchmark_manifest.py` keys (`BenchmarkManifest.to_dict` is group 27, rolled up elsewhere; `Ceilings.as_dict` and `_canonical_json` are already `guarded`).
- Scope-Paths: tests/test_benchmark_manifest_digest.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: g5ypvb
- Set: trimgap
- Order: 25
- Highest E allocated: 03
- Author: opencode
- Id: ya0h23
- Approval: 2026-10-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (unsatisfiable 30s budget bar), PR-002 (probe evidence: head, baseline_failing, newly_failing attribution, base sha, committed-range diff), PR-003 (execution contract) fixed; F-02 and F-04 reproduced at 6b94e8d4a (F-06)

- 2026-10-23 to-review (opencode): authored from backlog `g5ypvb`. Re-ran `tools/mutation_probe.py` for the three keys under both `return-none` and `raise` at HEAD `db8853d1` against restored `tests/test_benchmark_corpus.py` (F-02), then prototyped the proposed assertions in-process against monkeypatched `return None` mutants and saw every mutant fail them (F-04).
- 2026-10-23 draft (opencode): created.

## Goal

Answer the backlog item's "is the probe applicable?" question with recorded evidence (it is; the gap is real) and close the gap with one small core-tier test module, so that a `return-none` mutation of any of the three digest keys turns the routine gate red. Done means all three `return-none` probes report `verdict: killed` with the new module in the `-m core` selection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: add the behavioral test module

- [ ] E-01 Before any edit, record `git rev-parse HEAD` as `<base>`. Create `tests/test_benchmark_manifest_digest.py` with `import pytest`, module-level `pytestmark = pytest.mark.core`, a module docstring naming backlog `g5ypvb` and findings `wo21z5`, and its own local `_ceilings(...)`/`_manifest(**overrides)` helpers built on `benchmark_manifest.make_ceilings` and `benchmark_manifest.build_manifest` (same keyword set as `tests/test_benchmark_corpus.py` `_sample_manifest`; do not import from that test module). Add these tests, each calling the public API and asserting on returned values: (a) `BenchmarkManifest.digest()` and `Ceilings.digest()` each return a `str` matching `^[0-9a-f]{64}$`; (b) two independently built manifests with identical arguments have equal digests, and the same for ceilings; (c) a manifest differing only in `trial` (and separately only in `reasoning_effort`) has a different `digest()`; (d) ceilings differing only in `trial_count` have a different `Ceilings.digest()`, and the manifest built on them has a different `digest()`; (e) a manifest round-tripped through `to_dict()` with only `usage["wall_time"]` changed and reloaded via `manifest_from_dict` keeps the same `digest()` (usage is a result, not identity, per the `BenchmarkManifest.digest` docstring "usage is a RESULT, not identity"); (f) `manifest.identity["ceilings_digest"]` equals `ceilings.digest()` and matches the 64-hex pattern. No test reads source, uses `inspect`/`ast`, or pins a literal digest value.
  - Depends on: none
  - Expected outcome: the new module exists and `python3 -m pytest -o addopts="" -v tests/test_benchmark_manifest_digest.py` passes every test.
  - Execution state: pending

### Task group 2: prove the gap is closed

- [ ] E-02 Run `python3 tools/mutation_probe.py --op return-none agent_workflows/benchmark_manifest.py::<key> -- -o addopts= -q -p no:randomly -m core tests/test_benchmark_corpus.py tests/test_benchmark_manifest_digest.py` for each `<key>` in `BenchmarkManifest.digest`, `Ceilings.digest`, `_digest`. `tools/mutation_probe.py` adds a detached worktree at committed `HEAD` (`git worktree add --detach <dir> HEAD`) and mutates there, so the checkout's production code is never modified but an UNCOMMITTED test module is invisible to it; therefore first commit E-01 through `aw commit ya0h23 -- tests/test_benchmark_manifest_digest.py`, then run the probes, and confirm each output's `head:` equals that commit. Record each `head:`, `selection:`, `verdict:`, `baseline_failing:` and `newly_failing` list in Findings. A probe with `baseline_failing` above 0 or a `verdict:` other than `killed`/`survived` (for example `error`) is not a result: record it, fix the cause if in scope, and re-run. If the commit's mutating `ruff --fix`/`ruff-format` pre-commit hook rewrites lines, `aw commit` re-stages and retries; record those hunks as hook churn in V-02. If a strengthened E-01 assertion needs a further commit, commit it the same way before re-probing. If any probe still reports `survived`, strengthen the E-01 assertion that should have caught it and re-run that probe; do not mark this item performed while any of the three survives.
  - Depends on: E-01
  - Expected outcome: three probe outputs, each with `head:` equal to the latest E-02 commit, `baseline_failing: 0` and `verdict: killed`, and a `newly_failing` list naming at least one test from `tests/test_benchmark_manifest_digest.py` (re-derive at execution; the count is not the bar). At review, `tests/test_benchmark_corpus.py` alone kills none of the three (F-06), so the kill must come from the new module.
  - Execution state: pending

- [ ] E-03 Run `python3 -m pytest -o addopts= --collect-only -q -m core tests/test_benchmark_manifest_digest.py` to confirm the new module is in the core tier, then run the routine bare gate `python3 -m pytest`. The conftest budget check (`conftest.pytest_sessionfinish`) prints a `CORE TIER BUDGET EXCEEDED` block on a wall-time overrun and fails the run only when enforced; the core tier already exceeded 30s on this host before this plan (sibling `s461lz` F-07: 34.93s). So paste any budget block verbatim and do not count it against this item unless a test from the new module is among its listed slowest tests.
  - Depends on: E-02
  - Expected outcome: the collect-only run lists the new module's tests as selected; the bare run exits 0 and its summary line shows `passed` with no `failed` or `error`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16): every E-01 test calls the public manifest API and asserts on its returned digest strings. Asserting the hex SHAPE and the equal/different RELATIONS is behavior (it is the contract `benchmark_reports` relies on to pool runs); pinning a literal digest value is not done, because it would break on any legitimate change to the canonical encoding.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`). A module-level `pytestmark = pytest.mark.core` puts every test in the routine gate, as `tests/test_benchmark_corpus.py` already does.
- Probe tool: `tools/mutation_probe.py` (`--op {return-none,return-true,return-false,negate-return,raise}`, pytest selection after `--`) is the tool `wo21z5` used, so E-02 is directly comparable to the original verdict.
- Sibling precedent: executed `78g6ic` restored `tests/test_benchmark_corpus.py` and added a `ResidualKeyTests` class for polarity gaps; pending `btubm6` (Order 24) adds a separate new module rather than editing that file. This plan follows `btubm6` so the two pending plans touch disjoint paths.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wo21z5` `## Budget probe results` rows for `BenchmarkManifest.digest`, `Ceilings.digest`, `_digest`: partition `P2`, operator `return-none`, selection `files`, 14 collected, survivor `survived`, control `survived`, verdict `unprovable`, reason "control survived; overwrote 1" | The original verdict means: not even the deleted control file killed the mutant. It does NOT mean no operator applies (that is the separate `no applicable operator` reason in `wo21z5` `## Method`). |
| F-02 | `tools/mutation_probe.py` at HEAD `db8853d19d13`, selection `-o addopts= -q -p no:randomly -m core tests/test_benchmark_corpus.py` (control file now restored by `78g6ic`) | `return-none`: `BenchmarkManifest.digest` `survived` (`mutant_failing: 0`), `Ceilings.digest` `survived` (0), `_digest` `survived` (0). `raise`: `BenchmarkManifest.digest` `killed` (1), `Ceilings.digest` `killed` (8), `_digest` `killed` (8). The probe is applicable; the keys are reached and partly guarded, but the `return-none` behavior is unguarded. |
| F-03 | `tests/test_benchmark_corpus.py` `ManifestResultIdentityTests.test_round_trip_preserves_identity_and_digest` ("self.assertEqual(m.digest(), rt.digest())"); `git show 19313eed^:tests/test_benchmark_corpus.py` and `git show 19313eed^:tests/test_benchmark_runners_reports.py` contain no other `.digest()` value assertion | The only digest assertion anywhere is an equality between two digests, which a constant `None` satisfies. Nothing deleted in `19313eed` would close the gap, so mining the deleted files is not a remedy; new assertions are needed. |
| F-04 | In-process prototype at HEAD `db8853d1`: the E-01 (a)+(c)+(d) assertions evaluated against the real module, then with `benchmark_manifest._digest`, `Ceilings.digest`, `BenchmarkManifest.digest` each monkeypatched to return `None` | Real module: assertions hold (`True`); usage-only change keeps the digest; `identity["ceilings_digest"] == ceilings.digest()`. Each of the three `None` mutants: assertions fail (`False`). The proposed tests kill all three mutants. |
| F-06 | review at HEAD `6b94e8d4a`: `tools/mutation_probe.py --op return-none` over `-o addopts= -q -p no:randomly -m core tests/test_benchmark_corpus.py` for the three keys; in-process re-run of all six E-01 assertions (a)-(f) against the real module and against each `return None` monkeypatch | All three probes `survived`, `baseline_failing: 0`, `mutant_failing: 0` (F-02 reproduces). Real module: (a)-(f) all hold, including (e) via `manifest_from_dict` with `usage["wall_time"] = 12.5`. `_digest -> None` fails (a), (c), (d), (f); `Ceilings.digest -> None` fails (a), (d), (f); `BenchmarkManifest.digest -> None` fails (a), (c), (d). (b) and (e) are relation checks a constant satisfies, so they guard behavior but kill no mutant; F-04 reproduces. `make_usage(0.0)` keys: `wall_time`, `tokens`, `credits_or_quota`. |
| F-05 | `agent_workflows/benchmark_reports.py` uses "t.manifest.digest()" in a run digest and `baseline.digest()`/`candidate.digest()` in comparisons | The digest is a load-bearing identity used to compare runs, so a constant digest would be a real defect; the gap is worth closing even at `chore`/`low`. |

## Proposed changes (ordered, validatable)

1. E-01 adds `tests/test_benchmark_manifest_digest.py` with six behavioral digest tests.
2. E-02 re-probes the three keys with `return-none` and records `killed`.
3. E-03 confirms the bare core gate passes.

## Deferred / out of scope (with reason)

- Changing `tools/mutation_probe.py` or the `wo21z5` classification so that "control survived" is reported differently from a genuinely inapplicable probe.
  - Carrier-Declined: no work is owed; `wo21z5` already distinguishes the two by reason string (F-01), and the item asks only whether the probe applies to these keys.
- `BenchmarkManifest.to_dict` (group 27 of the `wo21z5` filing plan, rolled up into another item).
  - Carrier-Declined: owned by a different backlog item, not `g5ypvb`.

## Scope check

- Over-scope: none. Only the new test module is declared; no production file and no existing test file changes.
- Under-scope: none. All three backlog keys are tested by E-01 and verified by E-02; the item's "investigate probe" question is answered in F-01 to F-04.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_benchmark_manifest_digest.py` passes, per-test list pasted.
- The three `tools/mutation_probe.py --op return-none` runs of E-02, full output pasted (`head`, `selection`, `baseline_failing: 0`, `verdict: killed`, `newly_failing` naming a new-module test).
- `--collect-only -m core` output for the new module, and the bare `python3 -m pytest` summary line, exit status and any budget block pasted.
- `git diff --stat <base>..HEAD -- agent_workflows/ tests/test_benchmark_corpus.py` and `git diff --stat -- agent_workflows/ tests/test_benchmark_corpus.py` both empty (no production change, owned test file untouched).

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Is the `return-none` probe applicable to these keys, or is `unprovable` a probe artifact?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: applicable. All three keys are reached and `raise` is killed (F-02); `return-none` survives only because existing tests compare digests for equality (F-03), and the prototype in F-04 shows ordinary behavioral assertions kill it. The remedy is new tests, not a probe change.

### OQ-02: Add the tests to `tests/test_benchmark_corpus.py` or to a new module?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: new module. Pending sibling `btubm6` set the precedent of a separate module to avoid editing the `78g6ic`-restored file, which keeps the two pending plans on disjoint Scope-Paths; the core tier picks up any `core`-marked module.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_benchmark_manifest_digest.py` output listing every test PASSED, and paste `<base>` plus `git diff --stat -- agent_workflows/ tests/test_benchmark_corpus.py` showing no change.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `aw commit` output naming the E-02 commit; paste the full output of all three `tools/mutation_probe.py --op return-none` runs (produced by `tools/mutation_probe.py` itself, E-02), each showing `head:` equal to that commit (or a later strengthening commit), `selection:` containing `-m core` and `tests/test_benchmark_manifest_digest.py`, `baseline_failing: 0`, `verdict: killed`, and a `newly_failing` list naming at least one test from `tests/test_benchmark_manifest_digest.py`; paste `git diff --stat <base>..HEAD -- agent_workflows/ tests/test_benchmark_corpus.py` showing no change.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `--collect-only -q -m core tests/test_benchmark_manifest_digest.py` output listing the new tests; paste the bare `python3 -m pytest` summary line showing `passed` with no `failed` or `error`, its exit status, and any `CORE TIER BUDGET EXCEEDED` block verbatim (including any "not enforced" reason).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit ya0h23 -- tests/test_benchmark_manifest_digest.py` (plus this plan when recording evidence); verify `git diff --cached --name-only`; never `git add -A`; never push. You MUST paste the ACTUAL probe and runner output into each `V-*`; never claim a mutant was killed or a test passed that you did not run. Mutation checks use `tools/mutation_probe.py` only (it mutates a disposable worktree, never the checkout), after the E-02 commit; no production file under `agent_workflows/` and not `tests/test_benchmark_corpus.py` may change. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize ya0h23` itself.
