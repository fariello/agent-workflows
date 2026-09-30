# IPD: Enforce the no-duplicate-top-level-definition property in CI with ruff F811, whose local hook already catches it unenforced

- Date: 2026-09-30
- Kind: child
- Concern: A DUPLICATE TOP-LEVEL DEFINITION IS INVISIBLE TO REVIEW AND SILENTLY WINS AT RUNTIME, AND THE ONE TOOL THAT ALREADY DETECTS IT IS NOT ENFORCED ANYWHERE THE REPOSITORY CANNOT BYPASS. Backlog `s6om7k` records the measured instance: while lifting `locked_run` in plan `li44r9`, a wrapper was written near `run_lock` and a SECOND `locked_run` definition was left roughly 4,300 lines further down the same module, so Python's last-definition-wins made the wrapper UNREACHABLE. The symbol read as lifted in a diff and behaved as forked at runtime. The item proposes a repo-wide AST assertion over `agent_workflows/` as the fix; that specific instrument is FORBIDDEN here (`GUIDING_PRINCIPLES` P16 names `ast.parse` over production source by name, and the 2026-09-26 maintainer ruling in backlog `1bxw6o` says "we test outcomes and functionality, never code structure or script text. Do not restore code-pinning guards"). This plan therefore delivers the item's PROPERTY through the sanctioned instrument instead: ruff's `F811` already detects the class, the repository's pinned `v0.4.4` pre-commit hook already RUNS it, and the gap is that ruff appears in NO CI workflow, so the only thing standing between this class and `main` is a local hook that `--no-verify` skips, that a fresh clone lacks until `pre-commit install`, and that does not run at all for the fast-forward and automated-merge paths the integration flow uses.
- Scope: Add ruff `F811` as a named fail-closed CI gate over `agent_workflows/` and `tests/`, and record in `GUIDING_PRINCIPLES` P16 that a linter detecting a real runtime defect is not the code-pinning shape P16 prohibits. NOT in scope: adopting ruff's other 8,000+ default findings, adding any AST or source-reading test, or changing either runner.
- Scope-Paths: .github/workflows/tests.yml, GUIDING_PRINCIPLES.md, .aw/records/plans/pending/20260930-s6om7k-01-szkgb8-enforce-the-no-duplicate-top-level-definition-property-in-ci.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: s6om7k
- Set: s6om7k
- Order: 1
- Highest E allocated: 04
- Author: aw oc run
- Id: szkgb8

## Workflow history

- 2026-09-30 draft (aw oc run): created.
- 2026-09-30 to-review (aw oc run): authored from backlog `s6om7k`; graduated with the item's suggested AST fix REPLACED by a ruff `F811` CI gate after measuring that the suggested instrument is prohibited by P16 and that the sanctioned one already detects the exact reconstructed defect.

## Goal

Make the property backlog `s6om7k` asks for - no module in `agent_workflows/` defines the same top-level symbol twice - enforced on a surface no contributor can bypass, by promoting the ruff `F811` check the repository ALREADY runs locally into a named fail-closed CI step. Deliver it WITHOUT writing the AST-over-production-source test the item suggests, because that instrument is prohibited, and record why the chosen one is not prohibited so the next author does not re-litigate it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the gate is landable before wiring it

- [ ] E-01 Re-measure, at execution HEAD, the two facts this plan's design rests on, and ABORT with the measurement recorded if either has changed: (a) `ruff check --select F811 agent_workflows/` exits 0, so the gate can be added without a cleanup tranche; (b) `ruff check --select F811 --target-version py312 tests/` exits 0, while the same command WITHOUT `--target-version py312` fails with two `invalid-syntax` errors in `tests/test_check_engine_spec_criteria.py` (f-string backslash and reused quote, both legal only on 3.12+). Fact (b) is the reason E-02 must pin `--target-version`; if (b) no longer holds because that file was fixed, DROP the flag and say so rather than carrying a now-unnecessary pin.
  - Depends on: none
  - Expected outcome: both commands' exit codes and tail output pasted. Baseline confirmed clean, or a concrete divergence recorded and the plan stopped before it edits CI.
  - Execution state: pending

- [ ] E-02 Reconstruct the ORIGINAL defect and prove the gate catches it, so the gate is validated against the real bug rather than a toy. Rebuild the exact shadowed module from history in a gitignored scratch directory under `.aw/state/`: take `git show 12a5c05b:agent_workflows/oc_runipd.py` (the commit that LIFTED `locked_run`, whose own message records "A duplicate locked_run definition I introduced was caught by the new"), extract the stale `locked_run` function block from `git show 12a5c05b^:agent_workflows/oc_runipd.py`, and re-insert that block at a top-level boundary several thousand lines BELOW the wrapper. Run BOTH the ambient ruff and the version the hook actually pins (`v0.4.4`) against it. Delete the scratch directory when done; it must not be committed.
  - Depends on: E-01
  - Expected outcome: both ruff invocations report `F811 Redefinition of unused locked_run from line <wrapper line>` at the stale definition's line and exit 1. This proves the gate would have caught the originating instance, which is the claim the whole plan turns on.
  - Execution state: pending

### Task group 2: wire the gate and record the policy

- [ ] E-03 Add a named fail-closed `F811` step to `.github/workflows/tests.yml`. Put it in the EXISTING `attention-check` job rather than creating a new job or extending the 18-cell `unittest` matrix: that job is already the repository's single-run, read-only, fail-closed gate lane (its own comment says "matching the secret-scan / local-leaks single-job precedent ... not per Python matrix"), and a redefinition is a property of the source text, so running it once is sufficient and running it 18 times buys nothing. The step must install ruff pinned to the SAME version as the pre-commit hook (`ruff==0.4.4`, from `.pre-commit-config.yaml`'s `rev: v0.4.4`), select ONLY `F811`, cover `agent_workflows/` and `tests/`, and pass `--target-version py312` if and only if E-01 fact (b) still holds. Write a comment stating that the version is pinned to the hook deliberately so local and CI verdicts cannot diverge, that the selection is narrow because the repository has 8,061 other default ruff findings and adopting them is a separate decision, and that `F811` is NOT auto-fixable so the `--fix` the local hook passes can never silently delete one of the two definitions.
  - Depends on: E-02
  - Expected outcome: `tests.yml` carries one new named step. `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/tests.yml'))"` parses clean, and the step's own command run locally exits 0 against the current tree.
  - Execution state: pending

- [ ] E-04 Add one paragraph to `GUIDING_PRINCIPLES.md` Section 16 recording that a LINTER RULE DETECTING A REAL RUNTIME DEFECT IS NOT A CODE-STRUCTURE PIN, and why the distinction is not a loophole. State the test: `F811` reports a condition under which the shipped module's behavior is already wrong (one of two definitions is unreachable, so the exported symbol is not the one the author wrote), which is an OUTCOME; a census or placement pin reports only that source LOOKS different from a remembered shape, which is what P16 forbids. State the consequence explicitly so it cannot be read as general permission: this does NOT re-open `inspect`/`ast`/regex reads of production source in TESTS, and the deleted guards named in backlog items `xvp5vx`, `baskrx`, `s4jctz` and `1bxw6o` stay deleted. Cite this plan's id and the backlog item so the reasoning is traceable.
  - Depends on: E-03
  - Expected outcome: P16 carries the new paragraph; a future author asking "may I AST-walk production source to check for duplicates?" reads the answer (no; the linter gate already covers it) instead of re-deciding.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE ITEM'S SUGGESTED FIX IS PROHIBITED, WHICH IS THE CENTRAL AUTHORING DECISION. `GUIDING_PRINCIPLES.md` Section 16 ("Test outcomes and behavior, never code structure or text") forbids "No production source inspection", naming `inspect.getsource`, `inspect.getsourcelines`, `ast.parse`, `read_text()` and substring/regex searches "against production code (`agent_workflows/*.py`)". Backlog `s6om7k`'s SUGGESTED FIX is "a few lines of AST over `ast.Module.body`" over exactly that directory. `AGENTS.md`'s own execution contract repeats the prohibition in clause (1). So the item's property is wanted and its instrument is not; see DECISION D-1.
- THE PROHIBITION IS A SETTLED MAINTAINER RULING, not a reviewer's reading. Backlog `1bxw6o` was closed with "Maintainer ruling: retired by suite trim; we test outcomes and functionality, never code structure or script text. Do not restore code-pinning guards." Commit `80db6750` ("test: delete 366 tests that pinned code structure instead of behaviour") is the enforcement, and `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") is what deleted `tests/test_hostdedup_identical_lift.py`, the guard the item credits with catching the instance. That file is GONE: `ls tests/ | grep -i hostdedup` returns only `test_hostdedup_third_host.py`.
- THE REPOSITORY ALREADY RUNS THE DETECTOR AND ALREADY TRUSTS IT. `.pre-commit-config.yaml` carries `astral-sh/ruff-pre-commit` at `rev: v0.4.4` with `id: ruff, args: [--fix]`. Ruff's default selection is `E4,E7,E9,F`, and `F811` (redefinition-while-unused) is in `F`. So the class is already detected on every local `git commit`; nothing needs inventing, only enforcing.
- P16 ALREADY CARRIES AN EXCEPTION THIS FITS ALONGSIDE, and it is worth naming so E-04's paragraph is an extension rather than a contradiction: "The one narrow exception: Content verification is permissible only where the text or file itself is the artifact under test". The sanctioned AST precedent in the suite, `tests/test_carrier_scan_single_item_contract.py`, walks `agent_workflows/` source and survives; its docstring fences its scope tightly and declares its own KNOWN HOLE. That file is precedent that a source-reading guard CAN be legitimate when it detects a real defect class, which is the shape of E-04's argument.
- RUFF IS IN NO CI WORKFLOW. `grep -rn "ruff\|pre-commit" .github/workflows/` matches ONE line, a comment in `local-leaks.yml` about a different hook. So the detector's only enforcement is local, and local enforcement has four measured holes: `--no-verify` skips it; a fresh clone has no hooks until `pre-commit install`; `default_stages: [pre-commit]` is pinned in `.pre-commit-config.yaml`, and only the executed-transition gate opts into `pre-merge-commit`, so ruff does NOT run on an automated merge; and the config's own comment records that `pre-merge-commit` "does NOT run for a fast-forward merge (no commit is created)", which is the `git merge --ff-only` path `AGENTS.md` prescribes for publishing to `main`.
- `.github/workflows/tests.yml` HAS AN ESTABLISHED PLACE FOR A GATE LIKE THIS. The `attention-check` job is a single-OS, single-Python, read-only, fail-closed lane whose comment states the pattern: "matching the secret-scan / local-leaks single-job precedent; read-only; writes nothing; no secrets ... (not per Python matrix)". It already hosts five `python -m agent_workflows check ...` steps. Adding a sixth named step there follows the precedent; adding a job or a matrix leg does not.
- `.aw/state/` IS GITIGNORED and is the correct place for E-02's scratch reconstruction: `git check-ignore -v .aw/state/` reports `.aw/.gitignore:62:/state/`.
- CITE BY SYMBOL OR QUOTED STRING, not by a bare line number (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`), which is why every citation above names a file plus a quoted string or a symbol.

## Findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | **HIGH** | **THE ITEM'S SUGGESTED FIX CANNOT BE IMPLEMENTED AS WRITTEN.** The suggested "few lines of AST over `ast.Module.body`" applied to `agent_workflows/` is the exact instrument P16 prohibits by name. An executor following the item literally would write a test that a reviewer must reject, so the plan MUST substitute an instrument rather than transcribe the suggestion. This is the reason this plan is not a ten-line test. | `GUIDING_PRINCIPLES.md` P16 "No production source inspection" naming `ast.parse` and scoping it to "production code (`agent_workflows/*.py`)"; `AGENTS.md` clause (1) of "TEST OUTCOMES, NOT CODE STRUCTURE"; the item's own "SUGGESTED FIX" line. |
| F-02 | **HIGH** | **THE DETECTOR ALREADY EXISTS, IS ALREADY PINNED, AND ALREADY CATCHES THE EXACT ORIGINAL DEFECT.** Reconstructing the real shadowed `oc_runipd.py` from `12a5c05b` (wrapper at line 2695, stale copy re-inserted at 7036) and running the hook's own pinned ruff makes ruff report `F811 Redefinition of unused `locked_run`` against the re-inserted `oc_runipd.locked_run` copy, naming the surviving wrapper `oc_runipd.locked_run` as the "previous definition", and exit 1. So no new instrument is needed; this is an ENFORCEMENT gap, not a detection gap. | Ambient `ruff 0.16.3` and the hook's cached `ruff 0.4.4` (`~/.cache/pre-commit/repozypou4s9/py_env-python3.12/bin/ruff`) both reporting that finding on the reconstruction; `12a5c05b`'s message "A duplicate locked_run definition I introduced was caught by the new"; `git show 12a5c05b -- agent_workflows/oc_runipd.py` showing `+def locked_run` at diff line 425 and `-def locked_run` at 748. |
| F-03 | **HIGH** | **THE DETECTOR IS ENFORCED ONLY LOCALLY, AND EVERY PATH THAT REACHES `main` IN THIS REPOSITORY CAN MISS IT.** `grep -rn "ruff" .github/workflows/` returns nothing but an unrelated comment. Four holes, each from the repo's own config: `--no-verify`; a fresh clone before `pre-commit install`; `default_stages: [pre-commit]` so ruff is absent from the automated-merge stage; and the config's own note that `pre-merge-commit` "does NOT run for a fast-forward merge", which is exactly `git merge --ff-only`, the publish path `AGENTS.md` prescribes. A lane integrated by fast-forward therefore reaches `main` having had ruff run only on the contributor's own machine, if at all. | `grep -rn "ruff\|pre-commit" .github/workflows/` -> one comment line in `local-leaks.yml`; `.pre-commit-config.yaml` `default_stages: [pre-commit]` and its `stages: [pre-commit, pre-merge-commit]` on the executed-transition gate ALONE; the same file's "Honest limit: `pre-merge-commit` does NOT run for a fast-forward merge (no commit is created)". |
| F-04 | MEDIUM | **`F811` COVERS EVERY REALISTIC SHAPE OF THIS DEFECT, INCLUDING THE ONES A NAIVE READING WOULD EXPECT IT TO MISS.** Pyflakes says "redefinition of UNUSED", which invites the guess that a large module calling the symbol between its two definitions escapes. Measured: it does not. Flagged in all four probes - name called by another function between the definitions; name listed in `__all__`; differing arity; and the full 8,200-line reconstruction. The reason is that the relevant binding is the module-level one, and a call inside a function body does not consume it at definition time. | Four scratch probes under `.aw/state/`, each reporting `F811` and exit 1; the reconstruction in F-02. |
| F-05 | MEDIUM | **THE GATE IS LANDABLE TODAY WITH NO CLEANUP TRANCHE, BUT ONLY IF IT IS NARROWLY SELECTED.** `ruff check --select F811 agent_workflows/` exits 0 and prints "All checks passed!", and an independent AST sweep over every `agent_workflows/**/*.py` finds `files_with_dups: 0 dup_symbols: 0`, so the property HOLDS at HEAD and the gate goes green immediately. By contrast `ruff check agent_workflows/` (full default selection) reports **8,061 errors**, so a broad lint gate is a different, much larger decision and must not be smuggled in. | `ruff check --no-cache --select F811 agent_workflows/` exit 0; `ruff check --no-cache agent_workflows/` "Found 8061 errors"; the AST sweep's zero counts. |
| F-06 | MEDIUM | **`tests/` NEEDS `--target-version py312` OR THE GATE FAILS FOR AN UNRELATED REASON.** `ruff check --select F811 tests/` reports two `invalid-syntax` errors, both in `tests/test_check_engine_spec_criteria.py` at the `f"p_{sentinel.strip('\"-') or 'dash'}"` expression: a backslash in an f-string and a reused outer quote, each legal only from 3.12. Ruff infers the target from `requires-python = ">=3.9"`. With `--target-version py312` the same command prints "All checks passed!". The syntax errors are real-but-tolerated (the suite is CI-run on 3.9 through 3.14, so that file evidently is not parsed on 3.9 in a way that breaks it); fixing them is NOT this plan's scope, so the flag is the correct move and E-01 re-checks whether it is still needed. | `ruff check --no-cache --select F811 tests/` -> "Found 2 errors", both `invalid-syntax` at `tests/test_check_engine_spec_criteria.py:236`; the same command with `--target-version py312` -> "All checks passed!"; `pyproject.toml` `requires-python = ">=3.9"`. |
| F-07 | MEDIUM | **`F811` IS NOT AUTO-FIXABLE, WHICH IS WHAT MAKES THE EXISTING `--fix` HOOK SAFE TO RELY ON.** The local hook runs `ruff --fix`. If `F811`'s fix were automatic, the hook would silently DELETE one of two definitions, which for the `locked_run` case would have removed either the wrapper or the stale copy at random and buried the defect instead of surfacing it. Measured: `ruff check --select F811 --fix` on a duplicate leaves the file byte-for-byte unchanged and still exits 1, and the output's "help: Remove definition" is advice, not an applied fix. | `ruff check --no-cache --select F811 --fix` on a two-definition probe: exit 1, file content identical before and after. |
| F-08 | LOW | **ONE GENUINE HOLE, STATED RATHER THAN DISCOVERED LATER.** If the first definition is CONSUMED at module level between the two (`ALIAS = f`), the binding is used, so `F811` does not fire - and the shadowing is nonetheless real: the module was executed and `f()` returns the second body while `ALIAS()` returns the first. Three NON-holes are legitimately silent and must not be "fixed": a version-conditional `if/else` definition, a `try/except ImportError` fallback, and `@typing.overload` stubs. So the gate catches the measured defect class and the shapes it plausibly takes, and is not a completeness claim. | Probe `ALIAS = f` between two `def f`: `F811` not flagged, while importing the module yields `f() -> 2` and `ALIAS() -> 1`; conditional, try/except and `@overload` probes each correctly silent. |
| F-09 | LOW | **THE ITEM IS CORRECT THAT NOTHING GUARDS THE GENERAL PROPERTY, AND ITS ONE NAMED WITNESS IS DELETED.** The item credits `tests/test_hostdedup_identical_lift.py::test_no_host_defines_a_lifted_symbol_twice`. That file no longer exists (deleted in the `19313eed` trim); only `tests/test_hostdedup_third_host.py` survives. Pending plan `vbhat9` independently reaches the same conclusion, declining to restore it because "`AGENTS.md`'s no-code-pinning rule would in any case disallow rebuilding as-was" and naming `s6om7k` as the adjacent tracked item. So this plan is the agreed carrier, and it must not restore that file. | `ls tests/ | grep -i hostdedup` -> `test_hostdedup_third_host.py` only; pending plan `20260929-deadshared-01-vbhat9-...ipd.md` naming `s6om7k` and declining restoration. |

## Proposed changes (ordered, validatable)

1. **Re-measure the baseline (E-01).** Confirm `F811` is clean over `agent_workflows/` and over `tests/` with the py312 target, and that the target flag is still required. Abort before touching CI if either has moved.
2. **Prove the gate against the real defect (E-02).** Reconstruct the historical shadowed `oc_runipd.py` from `12a5c05b` and show both the ambient and the hook-pinned ruff flag it. This is the plan's central evidence: the gate is validated against the bug that motivated the item, not against a toy.
3. **Wire the fail-closed CI step (E-03).** One named step in the existing `attention-check` job, ruff pinned to `0.4.4` to match the hook, `--select F811` only, over `agent_workflows/` and `tests/`, with `--target-version py312` per E-01.
4. **Record the policy boundary (E-04).** One P16 paragraph distinguishing a linter that detects a real runtime defect from a code-structure pin, and stating explicitly that this does not re-open source-reading tests or the deleted guards.

## Deferred / out of scope (with reason)

Every row below is a DECISION rather than an open obligation, so each carries an explicit `- Carrier-Declined:` reason. None of them hands work forward, and that is the point: this plan delivers the item's property in full, and the rows record the alternatives it deliberately does not take.

- **A repo-wide AST test over `agent_workflows/`, as the item literally suggests.**
  - Carrier-Declined: PROHIBITED, so there is nothing to carry. `GUIDING_PRINCIPLES` P16 names `ast.parse` over production source, and backlog `1bxw6o` closed with a maintainer ruling against restoring code-pinning guards. Filing a carrier would record the repository as still owing work it has decided not to do. The item's PROPERTY is delivered here by the ruff gate, so the item is satisfied rather than deferred. See D-1.
- **Adopting ruff's other default rules.**
  - Carrier-Declined: NOT THIS PLAN'S QUESTION AND NOT A GAP THIS PLAN OPENS. `ruff check agent_workflows/` reports 8,061 findings, so adopting them is a tree-wide lint-policy decision with its own risk and its own review, and it existed before this plan and is unchanged by it. Narrowing to `F811` is what makes this gate landable green today (F-05); a carrier would imply the narrow gate is a partial delivery of a broad one, which misstates the design.
- **Fixing the two `invalid-syntax` findings in `tests/test_check_engine_spec_criteria.py`.**
  - Carrier-Declined: NO LIVE DEFECT, so no carrier is owed. The two findings are ruff parsing that file at the inferred 3.9 target; CI runs the suite on 3.9 through 3.14 and it passes, so nothing is broken for a user. `--target-version py312` is the honest workaround and E-01 re-checks whether it is still needed. If a future author wants ruff at the declared floor, that is a new preference rather than an outstanding obligation of this plan.
- **Closing hole F-08 (module-level consumption between definitions).**
  - Carrier-Declined: NO AVAILABLE INSTRUMENT, which makes a carrier a promise nobody could keep. Catching it needs dataflow analysis `F811` does not perform, and the only alternative is the AST walk P16 prohibits, so filing a carrier would park work whose sole implementation is forbidden. The measured defect is not of this shape, and the hole is recorded in the gate's own comment following the KNOWN HOLE precedent `tests/test_carrier_scan_single_item_contract.py` sets in its docstring.
- **Restoring `tests/test_hostdedup_identical_lift.py`.**
  - Carrier-Declined: ALREADY DECIDED ELSEWHERE, so a carrier would duplicate a live record. Pending plan `vbhat9` declines the same restoration, states that "`AGENTS.md`'s no-code-pinning rule would in any case disallow rebuilding as-was", and names `s6om7k` as the adjacent tracked item; the suite-trim consequences are tracked by `xvp5vx` and `baskrx`. This plan is the carrier those records point at.
- **Adding the gate to the `unittest` matrix or a new job.**
  - Carrier-Declined: REJECTED ON THE MERITS, not postponed. A duplicate definition is a property of the source text, so it cannot vary across the 18 OS/Python cells, and the `attention-check` job's own comment states the single-run precedent ("not per Python matrix"). Running it 18 times would buy nothing and slow every PR.

## Scope check

- Over-scope: none. Two files are edited plus this plan itself. The gate is selected to ONE rule so it cannot become a general lint adoption, and no production module and no test file is touched.
- Under-scope: the gate does not catch F-08's module-level-consumption shape, and it does not retroactively prove history clean (it binds future commits). Both are stated rather than implied. It also does not remove the local hook, which stays as the fast feedback path; CI becomes the authority.

## Required tests / validation

No new test file is authored, and that is deliberate: the deliverable IS a CI gate, and the sanctioned way to validate it is to run the gate's own command and to demonstrate it fails on a known-bad input. Specifically:

- `ruff check --select F811 agent_workflows/` and the `tests/` equivalent must exit 0 at HEAD (E-01), so the gate is green when it lands.
- The E-02 reconstruction must make BOTH the ambient and the `0.4.4` ruff exit 1 on the real historical defect. This is the deliberate-break demonstration: the gate is proven to have teeth against the exact bug the item records, rather than asserted to.
- `.github/workflows/tests.yml` must parse as YAML after the edit, and the new step's command must be run locally and exit 0.
- The full suite must be run BARE (`python3 -m pytest`) and its `N passed` summary pasted, to show two documentation/CI edits regress nothing. No `-n0`, no extra `-q`, no `-p no:randomly` (`AGENTS.md` "HOW TO RUN THE SUITE").
- `aw ipd lint` on this plan must report conforming, and `aw check plans` must report no finding for `szkgb8`.

## Spec / documentation sync

- `GUIDING_PRINCIPLES.md` Section 16 is AMENDED by E-04. This is the load-bearing documentation change, not incidental: P16 as written would be read to forbid this plan's own gate, so landing the gate without amending P16 leaves the repository's stated policy contradicting its shipped CI. The amendment NARROWS nothing and PERMITS nothing new in tests; it draws the line between "detects a condition under which shipped behavior is wrong" and "asserts source looks like a remembered shape".
- No `.spec.md` file is touched, so nothing is declared in `Scope-Paths` for the specs tree and no spec-edit announcement is expected at run start. The `ipd-structure-and-linting` spec is CITED for its Section 10.2 citation rule but not modified.
- `CONTRIBUTING.md` is deliberately NOT edited: it already directs contributors to install pre-commit, and the new step is a CI gate that needs no contributor action. Adding prose about a step that simply passes would be noise.

## Open questions

### OQ-01: Should the gate cover `tests/` as well as `agent_workflows/`, given the item names only `agent_workflows/`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT AUTHORING - cover both. The item's suggested fix names `agent_workflows/`, but a duplicate top-level `def` in a test module is the same defect with a worse failure mode: a shadowed test function is silently NOT RUN, so it reports green while asserting nothing, which is precisely the false-green class this repository keeps filing items about. The cost of including `tests/` is one measured flag (`--target-version py312`, F-06) and no cleanup, since the directory is already clean under `F811`. Note the deliberate asymmetry with `tests/test_carrier_scan_single_item_contract.py`, whose docstring fences itself to `agent_workflows/` because widening it would flag legitimate test code; that reasoning is specific to its call-shape analysis and does not transfer, because a duplicate definition is never legitimate in either tree.

### OQ-02: Should the CI step pin ruff to the hook's `0.4.4`, or track latest?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT AUTHORING - pin to `0.4.4`, matching `.pre-commit-config.yaml`'s `rev: v0.4.4`. An unpinned CI ruff would eventually disagree with the local hook, producing the worst outcome for a contributor: a commit that passes every local check and reds `main` for a rule their own toolchain does not report. Both versions were measured to agree on the reconstruction (F-02), so pinning costs nothing today. The maintenance consequence is stated honestly: whoever bumps the hook's `rev` must bump this step too, and the step's comment says so.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output and exit codes of `ruff check --no-cache --select F811 agent_workflows/` (expect exit 0, "All checks passed!"), `ruff check --no-cache --select F811 tests/` (expect the two `invalid-syntax` findings at `tests/test_check_engine_spec_criteria.py`, or a recorded note that they are gone), and `ruff check --no-cache --select F811 --target-version py312 tests/` (expect exit 0). Plus an explicit statement of whether `--target-version py312` is still required, which E-03 depends on.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted `F811` finding from BOTH ruff invocations against the reconstructed module, each naming the stale definition's line and the wrapper's line, with both exit codes shown as 1. Plus the ambient and pinned `ruff --version` output, so it is clear which two binaries were used. Plus confirmation that the scratch directory was removed (`git status --short` showing nothing under `.aw/state/`, and no scratch path in the staged set).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the new step quoted verbatim from `.github/workflows/tests.yml`, showing the pinned `ruff==0.4.4`, `--select F811`, both directories, and the comment covering the version pin, the narrow selection, and the non-auto-fixability. PLUS `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/tests.yml'))"` exiting 0. PLUS the step's own command executed locally, exit 0. PLUS a DELIBERATE-BREAK demonstration on the real gate, not on a reconstruction: introduce a duplicate top-level `def` into a file the gate covers, run the step's exact command, paste the `F811` failure and exit 1, revert, re-run, paste the pass. A gate that has not been observed failing has not been validated.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new P16 paragraph quoted verbatim, showing (a) the outcome-versus-shape test, (b) the explicit statement that source-reading TESTS remain prohibited, (c) the named items whose deleted guards stay deleted, and (d) a citation of `szkgb8` and backlog `s6om7k`. PLUS the bare `python3 -m pytest` summary line with its `N passed` count, proving the two edits regress nothing. PLUS `aw check plans --agent` output showing no finding for `szkgb8`, and `aw ipd lint` reporting conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, deliberately: that field is an output of `/plan-review`, and writing one at authoring would forge the attestation the auto-approve predicate reads first. Absence is the correct state and makes the gate fail closed.

Execution contract for whoever runs this: commit ONLY the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never a push. E-02 writes scratch under gitignored `.aw/state/` and MUST delete it; verify `git diff --cached --name-only` before committing so no scratch file and no co-worker's path enters the commit. Do not claim done, and do not move this plan to `.aw/records/plans/executed/`, until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence - including V-03's deliberate-break demonstration, which is the only item that proves the delivered gate actually refuses the defect it exists to catch.

One decision is recorded for a reviewer to dispute directly rather than being buried in prose:

**D-1: the item's suggested fix is replaced, not implemented.** Backlog `s6om7k` asks for an AST sweep over `agent_workflows/`. Options considered: (a) implement it as written - REJECTED, `GUIDING_PRINCIPLES` P16 prohibits `ast.parse` over production source by name and backlog `1bxw6o` closed with a maintainer ruling against restoring code-pinning guards, so the work would be rejected at review; (b) do nothing and close the item as unactionable - REJECTED, the property is genuinely unguarded (F-09) and the defect was real and shipped; (c) promote the existing ruff `F811` detector to a fail-closed CI gate - CHOSEN, because it delivers the item's property, needs no new instrument, was measured to catch the exact original defect (F-02), lands green today (F-05), and is bypass-resistant in the ways the local hook is not (F-03); (d) build an import-graph rule inside `aw check` - REJECTED as disproportionate, since that is the instrument prior reviews proposed for import-layering questions ruff cannot see, whereas this class already has a shipped detector. The reviewer's dispute surface is narrow and explicit: if the maintainer considers a linter rule to be within P16's prohibition, then option (b) is the only remaining honest answer and this plan should be retired to `not-executed` rather than weakened - which is exactly why E-04 amends P16 in the same change rather than leaving the contradiction for a later author to trip over.
