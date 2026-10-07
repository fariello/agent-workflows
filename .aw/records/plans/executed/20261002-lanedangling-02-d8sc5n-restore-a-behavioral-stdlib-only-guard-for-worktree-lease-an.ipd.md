# IPD: Restore a behavioral stdlib-only guard for worktree_lease and correct its stale test citation

- Date: 2026-10-02
- Kind: child
- Concern: `worktree_lease.inspect_lane`'s docstring says the module's run-context-free property is "pinned by `tests/test_lane_allocation_idempotent.py::test_worktree_lease_stays_stdlib_only`". That pin does not exist, so a reader is promised enforcement that will not fire. Authoring also found the backlog item's account of HOW it was lost is WRONG in a way that changes the fix: the test function was deleted a day EARLIER than the file, by `80db6750c` ("test: delete 366 tests that pinned code structure instead of behaviour"), and the deleted body was itself a `read_text()` source-parse that `GUIDING_PRINCIPLES.md` P16 now forbids. So this is not a restore-what-was-deleted job; the old guard may not come back in its old shape.
- Scope: Replace the dangling citation in `inspect_lane`'s docstring with a citation to a NEW behavioral guard, and add that guard at `tests/test_worktree_lease_stdlib_only.py`. The guard asserts the OUTCOME (importing `worktree_lease` pulls in no first-party module beyond the package `__init__`'s own) in an isolated subprocess, reading no production source text. It also positively asserts that `lane_merged_into_target`'s function-local `runner_shared` import still works, so the guard cannot be satisfied by breaking the lazy delegation. EXCLUDES the two OTHER dangling citations of the same dead file that authoring measured in `runner_shared.py` (the signal-handler ones), which the rollup item `iosmvn` owns, and EXCLUDES re-adding the deleted test's `append_jsonl(`/`run_dir` substring assertions, which are source-parses.
- Scope-Paths: agent_workflows/worktree_lease.py, tests/test_worktree_lease_stdlib_only.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: rdl9lh
- Blocks-Release: next
- Set: lanedangling
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: d8sc5n

## Workflow history
- 2026-10-07 executed (opencode): finalize d8sc5n verified lane [Scope attribution - 166 changed path(s) OUTSIDE Scope-Paths were DISREGARDED as not attributable to this execution (evidence: run-record-exact), so no --scope-reason was demanded for them: .aw/config/project.json, .aw/records/backlog/graduated/20260921-oq05nc-01-oq05nc-os-level-push-denial-boundary.backlog.md, .aw/records/backlog/graduated/20260922-runverdict-01-ildjse-wire-run-state-machine-into-the-host-runners.backlog.md, .aw/records/backlog/graduated/20260926-lifegate-01-dvonrn-replace-location-token-lifecycle-gate.backlog.md, .aw/records/backlog/graduated/20260926-malgate-01-ariaau-audit-anti-malice-gates.backlog.md (... and 161 more; see disregarded_no_evidence_paths in the finalize evidence)]
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): status set to reviewed

- 2026-10-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed). Re-verified at lane HEAD `ad815ed28`: citation still dangling (`worktree_lease.py` `inspect_lane` docstring), `git log -S stays_stdlib_only --all -- tests/` -> `80db6750c`, `7a6bc48ac`; `merge-base --is-ancestor 80db6750c 19313eed7` rc 0; deleted body's `read_text` line confirmed; zero module-level first-party imports, one function-local in `lane_merged_into_target`; no surviving guard. E-03 as written would fail in-process (34 test modules import `runner_shared` at module level), so it now mandates a `pinned_env()` subprocess, demonstrated `BEFORE=False RET=False AFTER=True` (PR-001). E-04 now mutation-proves E-03 too (PR-002). Gate's unconditional `aw ipd finalize` made runner/executor-conditional and honesty rule added (PR-003). Seed-flag wording corrected (PR-004). Record: `.aw/records/reviews/20261002-lanedangling-02-d8sc5n-restore-a-behavioral-stdlib-only-guard-for-worktree-lease-an.review.md`.
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `rdl9lh`. GATE NOTE: the item carries `- Blocks-Release: next` and `- Work-Kind: bug`, both INHERITED here as the contract requires. THE ITEM'S CORE CLAIM VERIFIES IN FULL at HEAD `6d90b7060990c6fe86cc7ab428dc8773537c5099`: `ls tests/test_lane_allocation_idempotent.py` reports no such file, `grep -rn stays_stdlib_only tests/` exits 1 with no output, and `git log --oneline --diff-filter=D -- tests/test_lane_allocation_idempotent.py` names `19313eed7`. THE ITEM IS WRONG ON ONE POINT THAT CHANGES THE WORK, which is why E-01 re-derives it: the item attributes the loss to `19313eed` alone, but `git log -S stays_stdlib_only --all -- tests/` names `80db6750c` FIRST, and `git show 80db6750c -- tests/test_lane_allocation_idempotent.py` shows the function body being removed there (2026-09-23) a day before the file itself went (2026-09-24); `git merge-base --is-ancestor` confirms that order. The deleted body did `source = Path(WL.__file__).read_text(...)` and asserted over source lines, so it was deleted ON PURPOSE as a code-structure pin, and `GUIDING_PRINCIPLES.md` P16 ("No production source inspection") forbids bringing it back. That resolves the item's open decision ("RESTORE a behavioral guard ... or CORRECT the docstring") toward BOTH, in the one shape P16 permits. AUTHORING PROVED THE BEHAVIORAL FORM EXISTS AND IS MUTATION-SENSITIVE rather than assuming it: a subprocess probe that imports the bare package, snapshots `sys.modules`, then imports `worktree_lease`, prints `EXTRA=<none>` today and prints 26 modules (including `agent_workflows.runner_shared`) when the forbidden module-level import is injected. TWO FACTS CORRECT THE ITEM'S HAZARD FRAMING and are recorded in F-04 and F-05 rather than repeated as-is: the item says a first-party import "would create the very cycle" the header warns of, but authoring INJECTED that import and the cycle DID NOT crash in any of three entry orders (`runner_shared` imports `worktree_lease` function-locally, not at module level), while the measurable harm is a 2.10x import-cost regression (181.8ms to 382.2ms, best-of-5). So the honest claim is latent-fragility-plus-import-cost, not an immediate crash. THE ITEM'S SWEEP SUGGESTION IS DECLINED WITH EVIDENCE (F-06): all three named siblings (`2jz47s`, `gzmr54`, `p5qx91`) were each fixed by their own dedicated plan, and `tools/lost_guard_census.py --dedupe` names `rdl9lh` as the sole owner of this basename, so a per-item fix is the established pattern here.

## Goal

Make `worktree_lease`'s stdlib-only property actually enforced by a test that will fail if someone adds a module-level first-party import, and make `inspect_lane`'s docstring cite that real guard instead of a test deleted twice over, so an agent reading the docstring is told the truth about what protects the property.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure before changing anything

- [x] E-01 RE-DERIVE, at execution HEAD, the five facts the rest of this plan rests on, rather than trusting the numbers in this plan or in the backlog item. (1) That `inspect_lane`'s docstring still contains the quoted string `stays_stdlib_only`, and that `tests/test_lane_allocation_idempotent.py` is still absent. (2) WHICH COMMIT REMOVED THE TEST FUNCTION, via `git log -S stays_stdlib_only --all -- tests/`; the backlog item says `19313eed`, authoring measured `80db6750c` removed the FUNCTION first and `19313eed` the FILE a day later. If that ordering no longer reproduces, correct it and say so, because the whole "may not be restored as-written" argument depends on the earlier commit's stated purpose. (3) That the deleted body was a SOURCE PARSE, by reading it at `git show 80db6750c -- tests/test_lane_allocation_idempotent.py` and confirming it calls `read_text` on `WL.__file__`. (4) That `worktree_lease` still has ZERO module-level first-party imports and exactly ONE function-local one, in `lane_merged_into_target`. (5) That no SURVIVING test already enforces this property (search `tests/` for `stdlib_only`, `worktree_lease` plus `sys.modules`, and `first_party`). IF A SURVIVING GUARD IS FOUND, STOP AND REPORT: the fix then collapses to a one-line citation correction and this plan is over-scoped.
  - Depends on: none
  - Expected outcome: a recorded execution-HEAD measurement of all five facts with the HEAD sha stated, each either confirmed or corrected in writing, and an explicit STOP if fact (5) finds an existing guard.
  - Execution state: performed

### Task group 2: Add the guard, which is what makes the docstring fix honest

- [x] E-02 ADD a new behavioral guard file `tests/test_worktree_lease_stdlib_only.py` whose central test asserts the IMPORT-SET OUTCOME in an ISOLATED SUBPROCESS. The probe must (a) `import agent_workflows` alone and snapshot `{m for m in sys.modules if m.startswith("agent_workflows")}`, (b) then `import agent_workflows.worktree_lease`, (c) print the set difference minus `agent_workflows.worktree_lease` itself. The test asserts that difference is EMPTY. DERIVE THE BASELINE, DO NOT HARDCODE IT: authoring measured the package `__init__` pulling in `agent_workflows._compat` and `agent_workflows.versioning` (via its `from . import versioning` / `from ._compat import packaged_source_root` lines), and a hardcoded four-name allowlist would break the next time `__init__` legitimately changes, which is the brittleness that gets a guard deleted. USE A SUBPROCESS, NOT AN IN-PROCESS CHECK, and state the reason in the docstring: authoring measured that an in-process form reports a FALSE POSITIVE whenever any earlier test in the same worker already imported `runner_shared`, and `pyproject.toml`'s `addopts` runs `-n auto` with `pytest-randomly` active, so an order-dependent guard would flake. Pin the subprocess to THIS tree with `tests/support.pinned_env()`, following the established precedent in `tests/test_lane_import_root.py`, whose module docstring explains that an editable install's `.pth` can otherwise silently resolve the main checkout's package from a lane worktree. THIS IS NOT A CODE-STRUCTURE PIN: it runs the real import and asserts over real interpreter state, reading no production source text, per `GUIDING_PRINCIPLES.md` P16's "No production source inspection" bullet.
  - Depends on: E-01
  - Expected outcome: `tests/test_worktree_lease_stdlib_only.py` exists and its import-set test passes, asserting an empty first-party delta derived at runtime rather than compared against a hardcoded module list, running in a `pinned_env` subprocess.
  - Execution state: performed

- [x] E-03 ADD to the same file a SECOND, positive test that `lane_merged_into_target` still resolves its delegate through the FUNCTION-LOCAL import. This exists because E-02's assertion is satisfiable the WRONG way: deleting the lazy delegation entirely would also make the import delta empty, turning a landing predicate into a constant `False` while the guard went green. The test must assert the CONTRAST authoring measured: `agent_workflows.runner_shared` is ABSENT from `sys.modules` before the call and PRESENT after it, with the call made on a branch name that does not exist so the predicate's documented fail-toward-preservation path returns `False` without needing a fixture lane. THIS TEST MUST ALSO RUN IN A `pinned_env()` SUBPROCESS, for the same reason as E-02 and with a STRONGER effect: an in-process "absent before" assertion is not merely flaky but near-certain to fail, because review measured 34 test modules under `tests/` that import `runner_shared` at module level, and collecting even one of them (`tests/test_lane_import_root.py`) leaves `agent_workflows.runner_shared` in `sys.modules`. Pass a fresh temporary directory (the test's `tmp_path` or `tempfile.mkdtemp()`) as `repo_root` rather than `Path('.')`, so the call never touches a real repository. Review demonstrated this exact shape: a `pinned_env()` subprocess printed `FILE=<this worktree>/agent_workflows/worktree_lease.py`, `BEFORE=False`, `RET=False`, `AFTER=True`. Keep this a separate test from E-02 because it asserts a different property (lazy delegation still wired) through a different mechanism (calling the function), and because its failure means something different from E-02's.
  - Depends on: E-02
  - Expected outcome: a second passing test, run in a `pinned_env()` subprocess, demonstrating `runner_shared` is absent before and present after a `lane_merged_into_target` call, so the stdlib-only guard cannot be satisfied by removing the delegation.
  - Execution state: performed

- [x] E-04 PROVE THE GUARD IS SENSITIVE by mutation, and record the output, since an insensitive guard is exactly the hollow pin this plan exists to replace. TEMPORARILY inject `from agent_workflows import runner_shared` at module level in `agent_workflows/worktree_lease.py`, run the new test file, confirm the E-02 test FAILS, then RESTORE the file and confirm it is byte-identical (`git status --porcelain` clean for that path) and the test passes again. Authoring's run of this showed the delta going from `<none>` to 26 modules. THEN RUN A SECOND MUTATION that proves E-03, since E-03 exists precisely to catch the wrong-way fix E-02 cannot see: replace `lane_merged_into_target`'s body with a bare `return False` (removing the function-local `runner_shared` import), run the file, and confirm the E-03 test FAILS while the E-02 test still PASSES; restore the same way and re-confirm a clean `git status --porcelain` and a passing file. The contrast is the evidence: mutation 1 must turn E-02 red, mutation 2 must turn E-03 red with E-02 green. DO THIS WITH A RESTORING WRAPPER (write the mutation, run, restore in a `finally`), never by hand-editing and remembering to undo it: a mutation left behind would commit the very defect the guard forbids. Record the failure message the test actually produced, because that message is what a future engineer will have to act on.
  - Depends on: E-03
  - Expected outcome: pasted evidence of the E-02 test failing under the injected import, and of the E-03 test failing (with E-02 passing) under the removed delegation, each followed by a passing run after restoration, plus a clean `git status --porcelain agent_workflows/worktree_lease.py` after each restore, and the verbatim failure messages.
  - Execution state: performed

### Task group 3: Correct the citation the guard now backs

- [x] E-05 REPLACE the dangling citation in `inspect_lane`'s docstring. The parenthetical currently reads that the property is "pinned by `tests/test_lane_allocation_idempotent.py::test_worktree_lease_stays_stdlib_only`, which forbids this module even NAMING a run-context parameter"; it must name the new guard instead. TWO PRECISION REQUIREMENTS, because an inaccurate replacement recreates this defect in a new place. FIRST, do not carry over the "forbids ... even NAMING a run-context parameter" clause: that described the deleted body's `run_dir` substring assertion, and the new guard asserts an IMPORT SET, so repeating it would overstate what the guard checks. Describe what the new test actually asserts. SECOND, PRESERVE every other sentence in that docstring verbatim, in particular the `7ckptx` R5.5 RETENTION explanation of why the inventory cannot live here and the conclusion that retention classification belongs at the driver call site; this item changes a citation, not the module's documented design. Leave the two OTHER dangling citations of the same dead file alone (they are in `runner_shared.py`, concern signal-handler registration, and belong to `iosmvn`; see the deferred section).
  - Depends on: E-04
  - Expected outcome: `inspect_lane`'s docstring cites `tests/test_worktree_lease_stdlib_only.py` and describes the import-set property accurately, with every unrelated sentence unchanged and no reference to `stays_stdlib_only` remaining in that file.
  - Execution state: performed

### Task group 4: Prove the change is safe in the suite it ships into

- [x] E-06 RUN THE FULL FAST SUITE BARE as `python3 -m pytest`, with no added flags, and RUN THE NEW FILE TWICE UNDER DIFFERENT RANDOM SEEDS to demonstrate the order-independence F-08 identified as the specific flake risk. This is a separate item from E-02 through E-04 because those validate the new guard in isolation while this one validates that the guard behaves correctly as one test among thousands under `-n auto --dist=worksteal` with randomized ordering, which is the only configuration it will ever actually run in. If the suite shows failures, DETERMINE WHETHER THEY PRE-EXIST by re-running the same selection at the base commit before attributing anything to this change, and report the comparison either way rather than asserting the failures are unrelated.
  - Depends on: E-05
  - Expected outcome: a bare full-suite run with its `N passed` summary captured, plus two differently-seeded passing runs of the new test file, plus an explicit pre-existing-versus-caused determination for any failure observed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- P16 FORBIDS THE OBVIOUS FIX. `GUIDING_PRINCIPLES.md`'s "No production source inspection" bullet names `inspect.getsource`, `ast.parse`, `read_text()`, and substring/regex searches against `agent_workflows/*.py` as prohibited for verifying implementation details. The deleted guard did exactly `read_text()` plus substring matching, so it cannot be restored as written. The same file's P16 discussion of `F811` draws the governing line: a check is admissible when it "tests an outcome rather than code shape". An import-set probe is an outcome (what the interpreter actually loaded); a source grep for `^from agent_workflows` is code shape.
- `AGENTS.md` RESTATES THIS AS A HARD RULE for authored tests ("NEVER write or restore tests that read production source code using `inspect`, `ast`, regex, or substring search"), and explicitly says restored coverage "must always exercise the code ... and assert on real outputs, exit codes, and side effects". E-02 and E-03 are written to that standard.
- SUBPROCESS-PROBE PRECEDENT EXISTS and should be followed rather than reinvented: `tests/test_lane_import_root.py` defines a `PROBE` string, runs it under `sys.executable`, and pins resolution with `tests/support.pinned_env()`. Authoring confirmed `support.pinned_env` prepends the repo root to `PYTHONPATH`, and that the probe resolves this worktree's package even when run with `cwd` set to `tests/`.
- THE SUITE RUNS PARALLEL AND RANDOMIZED, which is what forces the subprocess form. `AGENTS.md` records that `pyproject.toml` `addopts` supplies `-n auto --dist=worksteal` and warns against disabling `pytest-randomly`. A guard reading the ambient `sys.modules` is therefore order-dependent by construction.
- RUN THE SUITE BARE. `AGENTS.md` is explicit that the suite is invoked as `python3 -m pytest` with no added flags, that `-n0` makes it several times slower, and that a second `-q` suppresses the `N passed` summary this plan's validation must paste.
- THE DEFECT CLASS IS TOOLED AND THE TOOL IS AUTHORITATIVE for the sweep question: `tools/lost_guard_census.py` has `--axis-a`, `--axis-b`, and `--dedupe` modes, and its dedupe pass prints an owning item per dangling basename.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE CITATION IS DANGLING, EXACTLY AS FILED.** `inspect_lane`'s docstring names `tests/test_lane_allocation_idempotent.py::test_worktree_lease_stays_stdlib_only` as the pin. The file does not exist and the symbol appears nowhere in `tests/`. | At HEAD `6d90b706`: `ls tests/test_lane_allocation_idempotent.py` -> "No such file or directory"; `grep -rn stays_stdlib_only tests/` -> exit 1, no output; `grep -rn stays_stdlib_only agent_workflows/` -> one hit, the docstring itself. |
| F-02 | **THE ITEM MISATTRIBUTES THE LOSS, AND THE CORRECTION IS LOAD-BEARING.** The item blames `19313eed` (the 7,402-test trim). The FUNCTION was removed a day earlier by `80db6750c`, "test: delete 366 tests that pinned code structure instead of behaviour". `19313eed` then removed the now-guardless FILE. This matters because the earlier commit's stated purpose is a deliberate rejection of the guard's SHAPE, not incidental collateral of a volume trim. | `git log --oneline -S "stays_stdlib_only" --all -- tests/` -> `80db6750c`, `7a6bc48ac`; `git show 80db6750c -- tests/...` shows `-    def test_worktree_lease_stays_stdlib_only(self):`; `git merge-base --is-ancestor 80db6750c 19313eed7` -> rc 0; dates 2026-09-23 and 2026-09-24. |
| F-03 | **THE DELETED GUARD WAS A SOURCE PARSE AND MAY NOT RETURN.** Its body read `source = Path(WL.__file__).read_text(encoding="utf-8")`, collected lines starting `import `/`from `, asserted no line contains `agent_workflows`, then asserted `"append_jsonl("` and `"run_dir"` are absent from the source text. Every one of those is a prohibited production-source read under P16. This is what converts the item's open either/or into "restore, but only in a behavioral shape". | Deleted body read at `git show 80db6750c -- tests/test_lane_allocation_idempotent.py`; `GUIDING_PRINCIPLES.md` "No production source inspection" bullet names `read_text()` and substring search explicitly. |
| F-04 | **THE ITEM'S CYCLE CLAIM OVERSTATES THE HAZARD; MEASURED, THE CYCLE DOES NOT CRASH.** The item says a first-party import here "would create the very cycle" the module header warns about. Authoring INJECTED `from agent_workflows import runner_shared` at module level and imported via three different entry points; ALL THREE exited 0 with no traceback. The reason: `runner_shared` imports `worktree_lease` FUNCTION-LOCALLY, never at module level, so there is no module-level back edge to close the loop. The fragility is REAL but LATENT (it is one hoisted import away), and the plan should say so rather than claim a crash a reviewer can disprove in one command. | Mutation run: entry `worktree_lease` rc=0, entry `runner_shared` rc=0, entry `oc_runipd` rc=0, no stderr. Module-level first-party imports of `runner_shared.py` enumerated by top-level-only AST walk: 2, neither naming `worktree_lease`. `lane_merged_into_target`'s own docstring: "THE IMPORT IS FUNCTION-LOCAL AND MUST STAY THAT WAY". |
| F-05 | **THE MEASURABLE PRESENT HARM IS IMPORT COST, 2.10x.** With the forbidden import injected, importing `worktree_lease` pulls 26 extra first-party modules (4 -> 30) and the import takes 382.2ms against 181.8ms clean, best-of-5 subprocess timings. That is the honest user-perceptible number for a module both drivers and `runner_shared` load. | Best-of-5 `subprocess.run` of `import agent_workflows.worktree_lease`: clean 181.8ms, mutated 382.2ms, delta 200.4ms. Module delta printed in full (includes `agent_workflows.runner_shared`, `engine`-adjacent modules, `render_stream`, `selectors`). |
| F-06 | **A SWEEP IS THE WRONG SHAPE HERE; THE PER-ITEM FIX IS THE ESTABLISHED PATTERN.** The item suggests a sweep "may be more economical than four separate fixes". All three named siblings already took the per-item route: `2jz47s` and `p5qx91` are `done` with their own executed plans (`iocyf3`, `nw088c`), and `gzmr54` is `graduated` with pending plan `t9lcdu`. The census tool independently names `rdl9lh` as the sole owner of this basename. | `find .aw/records -name "*2jz47s*"` etc. show one backlog item + one plan + one review each; `tools/lost_guard_census.py --dedupe` -> "tests/test_lane_allocation_idempotent.py -> Owning item: lanedangling [open] (...rdl9lh...)", match basis basename substring. |
| F-07 | **THE BEHAVIORAL FORM WORKS, IS SENSITIVE, AND THE BASELINE MUST BE DERIVED.** The probe prints `EXTRA=<none>` on the clean tree and 26 module names under mutation, so the assertion is both green today and loudly red on regression. The baseline is nonempty (`agent_workflows`, `._compat`, `.versioning`) because the package `__init__` imports them, so the test must subtract a runtime-derived baseline rather than compare against a frozen list. | Probe output clean: `EXTRA=<none>`. Bare `import agent_workflows` loads `['agent_workflows', 'agent_workflows._compat', 'agent_workflows.versioning']`; `agent_workflows/__init__.py` contains `from . import versioning` and `from ._compat import packaged_source_root`. |
| F-08 | **AN IN-PROCESS GUARD WOULD FLAKE, WHICH IS WHY E-02 MANDATES A SUBPROCESS.** Importing `runner_shared` first (as any earlier test in the same xdist worker may) and then checking ambient `sys.modules` yields a FALSE POSITIVE. With `-n auto` and `pytest-randomly` both active by default, that ordering is not hypothetical. | Direct run: after `import agent_workflows.runner_shared` then `import agent_workflows.worktree_lease`, the ambient check reports "FAIL (false positive!)". `AGENTS.md` documents the configured `-n auto --dist=worksteal` and the instruction not to pass `-p no:randomly`. |
| F-09 | **THE E-02 ASSERTION IS SATISFIABLE THE WRONG WAY, WHICH IS WHY E-03 EXISTS.** An empty import delta is also achieved by DELETING the lazy delegation in `lane_merged_into_target`, which would silently reduce the landing predicate to a constant `False` (its `except Exception` path returns `False`) while the new guard stayed green. Authoring measured the contrast E-03 pins. | Live call: `runner_shared` absent from `sys.modules` before `WL.lane_merged_into_target(Path('.'), 'definitely-no-such-branch-xyz')`, present after; return value `False`. `lane_merged_into_target` body: `from agent_workflows import runner_shared` inside a `try`, `except Exception: return False`. |
| F-10 | **TWO MORE CITATIONS OF THE SAME DEAD FILE EXIST AND ARE OWNED ELSEWHERE.** `runner_shared.py` cites `tests/test_lane_allocation_idempotent.py` in a signal-handler comment naming four test files, and makes a parallel claim in a sampler docstring ("four executed plans' guards assert `signal.signal(` appears in neither driver"). ALL FOUR named files are absent. That is a real but DIFFERENT defect (signal registration, not stdlib-only-ness), and the rollup `iosmvn` exists for the unowned remainder. | `grep -rn "test_lane_allocation_idempotent" agent_workflows/` -> 2 hits (`runner_shared.py` signal comment, `worktree_lease.py` docstring). All of `test_runner_stop`, `test_runner_stop_level3`, `test_runner_stop_level4`, `test_lane_allocation_idempotent` report MISSING. `iosmvn` summary: "Rollup tracking remaining unowned dangling test citations from the 19313eed suite trim". |
| F-11 | **ONE PENDING PLAN TOUCHES THE SAME FILE AND ALREADY ANTICIPATES THIS.** Pending plan `tjags7` (Set `voxbcx`) declares `agent_workflows/worktree_lease.py` in `- Scope-Paths:` and instructs its executor to "treat the citation as stale and re-derive which test, if any, actually enforces the property". It does not fix the citation. If `tjags7` lands after this plan, its note becomes stale-but-harmless; no `- Item-Dependencies:` edge is warranted, and OQ-01 records why. | `.aw/records/plans/pending/20261001-voxbcx-01-tjags7-...ipd.md` `- Scope-Paths: agent_workflows/worktree_lease.py, tests/test_lane_owner_record_anchoring.py`; its E-01 fourth measurement and its conventions section both describe the citation as stale. |

## Proposed changes (ordered, validatable)

1. **Re-derive the five premises at execution HEAD (E-01).** Confirm the dangling citation, re-establish the two-commit deletion ordering, confirm the deleted body was a source parse, confirm the module's current import shape, and search for a surviving guard. Stop if a surviving guard exists.
2. **Add the import-set guard (E-02).** New file `tests/test_worktree_lease_stdlib_only.py`, subprocess probe under `support.pinned_env()`, runtime-derived baseline, assertion that the first-party delta is empty.
3. **Add the lazy-delegation guard (E-03).** Second test in the same file asserting `runner_shared` is absent before and present after a `lane_merged_into_target` call, closing the wrong-way satisfaction of change 2.
4. **Mutation-prove both (E-04).** Inside a restoring wrapper, inject the forbidden import (E-02 must fail) and separately remove the lazy delegation (E-03 must fail while E-02 passes); restore after each, show the file passes, and paste the real failure messages.
5. **Correct the docstring (E-05).** Point the parenthetical at the new guard, describe the import-set property accurately instead of carrying over the `run_dir` clause, and leave every other sentence byte-identical.

## Deferred / out of scope (with reason)

- **THE TWO `runner_shared.py` SIGNAL-HANDLER CITATIONS (F-10).** Both cite the same dead file, and all four test files that comment names are absent, so the claim that guards "FORBID registering a handler" is as unbacked as the one this plan fixes. Out of scope on three grounds: it is a DIFFERENT property (SIGINT/SIGTERM registration, owned by `runstop` Phase 5 `71vjbn`), the fix needs its own judgement about whether that prohibition should be re-guarded or merely re-described, and the rollup item `iosmvn` already exists to track unowned dangling citations. Folding it in here would also push a `low`-priority single-citation fix into a second subsystem.
  - Carrier: iosmvn
- **THE DELETED GUARD'S `append_jsonl(` AND `run_dir` SUBSTRING ASSERTIONS.** Not restored in any form. They are production-source substring searches, prohibited by P16 and by `AGENTS.md`'s no-code-pinning rule. The ledger/run-context property they approximated is partly covered by the behavioral consequence this plan DOES pin: importing a ledger or run-context module would show up in E-02's import delta. The residue (a run-context parameter NAMED but imported from nowhere) is deliberately left unguarded rather than guarded by a forbidden mechanism.
  - Carrier-Declined: prohibited by GUIDING_PRINCIPLES.md P16 and AGENTS.md; no behavioral equivalent exists for unimported parameter names.
- **A GENERAL DANGLING-CITATION CHECKER.** `tools/lost_guard_census.py` already measures this class (101 distinct dangling test paths, 469 hits, at the authoring run) and `iosmvn` tracks the unowned remainder. Promoting the census to a blocking gate is a much larger decision about 101 existing violations and is not this item's concern.
  - Carrier: iosmvn
- **THE `19313eed`-VERSUS-`80db6750c` MISATTRIBUTION IN THE BACKLOG ITEM'S OWN TEXT.** F-02 corrects it here, in the plan, rather than editing the item: the production contract forbids modifying the item's requirements, and its `## Workflow history` is an append-only dated record of what the filer measured at the time.
  - Carrier-Declined: historical record in backlog item workflow history is immutable per repository contract; correction is recorded permanently in F-02 of this plan.

## Scope check

- Over-scope: none. Both declared paths are touched by an E-item (`agent_workflows/worktree_lease.py` by E-05 and transiently by E-04's restoring mutation; `tests/test_worktree_lease_stdlib_only.py` by E-02 and E-03). No other path is modified. E-01's measurements and V-*'s verifications are read-only.
- Under-scope: The two `runner_shared.py` citations in F-10 are knowingly left standing and are not in `- Scope-Paths:`; they belong to `iosmvn`. The run-context-parameter-naming half of the deleted guard is knowingly not re-pinned, for the P16 reason given above. Neither omission leaves the item's named concern (the `worktree_lease` docstring citation) unaddressed.

## Required tests / validation

- `python3 -m pytest tests/test_worktree_lease_stdlib_only.py` must pass, run BARE of extra flags beyond the path selector. Paste the real summary line.
- The full suite must be run BARE as `python3 -m pytest` and its `N passed` summary pasted, per the execution contract. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- MUTATION EVIDENCE IS MANDATORY, not optional: a guard that is not shown to fail under the injected import has not been shown to guard anything, and this plan exists precisely because a guard everyone believed in was absent. E-04's paste must show the failing run, the restoration, and a clean `git status --porcelain` for the mutated path.
- ORDER-INDEPENDENCE CHECK: run the new file twice with different random seeds (`pytest-randomly` is already active, so pass `--randomly-seed=<n>`, verified at review to work on this tree; two bare runs of the whole suite suffice if their seeds differ, otherwise pass two explicit seeds) to show the guard does not depend on what else ran first. This is the specific failure mode F-08 measured.
- `aw ipd lint` must report conforming at the `pre-transition` phase before this plan moves to `executed/`.

## Spec / documentation sync

N/A, with reason. No spec governs `worktree_lease`'s import posture; the property was asserted only in a module docstring and in the now-deleted test. `- Scope-Paths:` declares no `.spec.md` file, so the runners' spec-edit announcement has nothing to report. `GUIDING_PRINCIPLES.md` P16 is CITED as the constraint that rules out the source-parsing form but is NOT amended: this plan applies the existing principle rather than changing it. No `CHANGELOG.md` entry is proposed, since the change adds a test and corrects an internal docstring with no user-visible behavior change.

## Open questions

### OQ-01: Should this plan declare an `- Item-Dependencies:` edge on pending plan `tjags7`, which also modifies `agent_workflows/worktree_lease.py`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO EDGE. Resolved from repository evidence rather than deferred to the human. `tjags7` edits the lane-owner-record anchoring behavior and its own text already treats the citation as stale without fixing it, so the two changes do not contend for the same sentence: this plan rewrites the parenthetical inside `inspect_lane`'s docstring, and `tjags7`'s declared concern is the owner record. The runners also make the overlap a non-hazard: per `AGENTS.md`, each execute item runs in its own isolated worktree and returns through the merge-and-revalidate gate, so "two plans naming the same file is not a hazard even in PARALLEL". A dependency edge would instead impose a false ordering constraint, and `AGENTS.md` names an edge "pointing at something that will never execute" as a legitimate run-blocker, which is a cost with no corresponding benefit here. If both land, the only residue is `tjags7`'s now-obsolete note that the citation is stale, which is harmless prose and not a correctness defect.

### OQ-02: Should the new guard also assert the absence of a run-context PARAMETER name, as the deleted test did?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. The deleted test checked this with `self.assertNotIn("run_dir", source)`, a substring search over production source that P16 prohibits outright. No behavioral equivalent exists: a parameter that is merely NAMED but whose type comes from nowhere leaves no trace in the import set, in call behavior, or in any other observable the test can reach. The honest resolution is therefore to guard the part that IS observable (the import set, which is the part carrying the measured 2.10x cost and the latent cycle) and to record the unguarded residue explicitly in the deferred section rather than guard it by a forbidden mechanism or pretend it is covered. E-05 enforces the matching documentation discipline by forbidding the carried-over "even NAMING a run-context parameter" clause, so the corrected docstring will not promise this residue is pinned.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: The execution HEAD sha, plus pasted output for each of the five facts: (1) the `grep` hit showing `stays_stdlib_only` still in `worktree_lease.py` and the failed `ls` for `tests/test_lane_allocation_idempotent.py`; (2) `git log --oneline -S "stays_stdlib_only" --all -- tests/` output AND the `git merge-base --is-ancestor 80db6750c 19313eed7` exit code, with an explicit statement of whether F-02's two-commit ordering reproduced or is corrected; (3) the deleted body's `read_text` line quoted from `git show`; (4) the module's module-level first-party import count (expect 0) and the location of the single function-local one; (5) the searches for a surviving guard with their results. A bare assertion that the facts hold FAILS this item. If fact (5) found a surviving guard, the required evidence is instead the STOP report naming it.
  - Observed evidence:
    Execution HEAD sha: `d6aca9515f133266b0806332e7374c429a41b21c`
    (1) Dangling citation and absent test file:
    ```
    $ grep -n "stays_stdlib_only" agent_workflows/worktree_lease.py
    396:    `tests/test_lane_allocation_idempotent.py::test_worktree_lease_stays_stdlib_only`, which forbids
    $ ls tests/test_lane_allocation_idempotent.py
    ls: cannot access 'tests/test_lane_allocation_idempotent.py': No such file or directory
    ```
    (2) Commit deletion history and ordering:
    ```
    $ git log --oneline -S "stays_stdlib_only" --all -- tests/
    80db6750c test: delete 366 tests that pinned code structure instead of behaviour
    7a6bc48ac fix(laneorphan): lane allocation adopts or attempt-scopes instead of hard-failing
    $ git merge-base --is-ancestor 80db6750c 19313eed7
    ancestor rc=0
    ```
    F-02's two-commit ordering reproduced in full: `80db6750c` deleted the test function on 2026-09-23, and `19313eed` deleted the file on 2026-09-24; `80db6750c` is an ancestor of `19313eed7`.
    (3) Deleted test body calls `read_text` on `WL.__file__` (source parse):
    ```python
    -    def test_worktree_lease_stays_stdlib_only(self):
    -        # Plan `2c122z` E-06 DEPENDS on this: it reuses allocate_worktree for disposable candidate
    -        # worktrees, so a ledger/run-context import here would couple a low-level primitive to run
    -        # state and would misrecord candidates as lanes.
    -        source = Path(WL.__file__).read_text(encoding="utf-8")
    -        imports = [
    -            line.strip()
    -            for line in source.splitlines()
    -            if line.startswith("import ") or line.startswith("from ")
    -        ]
    -        self.assertTrue(imports)
    -        for line in imports:
    -            self.assertNotIn("agent_workflows", line, f"non-stdlib import: {line}")
    -        self.assertNotIn("append_jsonl(", source, "no ledger call in the primitive")
    -        self.assertNotIn("run_dir", source, "no run context in the primitive")
    ```
    (4) Module import counts:
    AST walk confirms module-level first-party imports: 0.
    Single function-local import at line 347 of `agent_workflows/worktree_lease.py`: `from agent_workflows import runner_shared` in `lane_merged_into_target`.
    (5) Search for surviving guards:
    `grep -rn "stdlib_only" tests/` -> 3 hits (`test_ipd_schema.py`, `test_ipd_authoring.py`, `test_ipd_lint.py`), none for `worktree_lease`.
    `grep -rn "worktree_lease" tests/ | grep "sys.modules"` -> no hits.
    `grep -rn "first_party" tests/` -> hits in `test_lost_guard_census.py` for `runner_shared`, none for `worktree_lease`.
    No surviving guard found.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted `python3 -m pytest tests/test_worktree_lease_stdlib_only.py` output showing the import-set test passing, PLUS the probe's own printed delta showing it empty. ALSO paste the test source region that derives the baseline, to demonstrate the baseline is computed at runtime and not a hardcoded module list (a hardcoded list FAILS this item, per F-07). ALSO confirm by inspection that the test spawns a subprocess via `sys.executable` and passes `support.pinned_env()`, since an in-process form is the measured flake in F-08.
  - Observed evidence:
    `python3 -m pytest tests/test_worktree_lease_stdlib_only.py` output:
    ```
    ..                                                                       [100%]
    2 passed in 14.35s
    ```
    Probe's printed delta:
    ```
    BASELINE=["agent_workflows", "agent_workflows._compat", "agent_workflows.versioning"]
    AFTER=["agent_workflows", "agent_workflows._compat", "agent_workflows.versioning", "agent_workflows.worktree_lease"]
    DELTA=[]
    ```
    Test source region dynamically computing baseline at runtime:
    ```python
            # Derive baseline at runtime rather than hardcoding module names.
            baseline = {m for m in sys.modules if m.startswith("agent_workflows")}
            import agent_workflows.worktree_lease

            after = {m for m in sys.modules if m.startswith("agent_workflows")}
            delta = sorted(list(after - baseline - {"agent_workflows.worktree_lease"}))
    ```
    Subprocess spawn confirmed via `sys.executable` and `support.pinned_env()`:
    ```python
        proc = subprocess.run(
            [sys.executable, "-c", probe],
            env=support.pinned_env(),
            capture_output=True,
            text=True,
            check=False,
        )
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted test output showing the lazy-delegation test passing, and the asserted contrast made explicit: `agent_workflows.runner_shared` NOT in `sys.modules` before the `lane_merged_into_target` call and IN `sys.modules` after it. A test that only asserts the post-call presence FAILS this item, because the before-state is what distinguishes lazy delegation from a module-level import. ALSO confirm by inspection that the before/after observation is made inside a `sys.executable` subprocess with `support.pinned_env()`; an in-process form FAILS this item, because the ambient worker's `sys.modules` already holds `runner_shared` from other test modules.
  - Observed evidence:
    `python3 -m pytest tests/test_worktree_lease_stdlib_only.py` passes `test_lane_merged_into_target_lazy_delegation`.
    Probe contrast output:
    ```
    FILE=<this-worktree>/agent_workflows/worktree_lease.py
    BEFORE=False
    RET=False
    AFTER=True
    ```
    Explicit contrast: `agent_workflows.runner_shared` is NOT in `sys.modules` before `lane_merged_into_target` is invoked (`BEFORE=False`), and IS present in `sys.modules` after the invocation (`AFTER=True`), with `ret` returning `False` on a nonexistent branch in a fresh temp directory (`RET=False`).
    Subprocess execution with `support.pinned_env()` confirmed by inspection:
    ```python
        with tempfile.TemporaryDirectory() as tmp_dir:
            proc = subprocess.run(
                [sys.executable, "-c", probe, tmp_dir],
                env=support.pinned_env(),
                capture_output=True,
                text=True,
                check=False,
            )
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: THE MUTATION TRANSCRIPT, in full: the injected line, the pasted FAILING test run under mutation including its verbatim assertion message, the pasted PASSING run after restoration, and `git status --porcelain agent_workflows/worktree_lease.py` returning empty. State the measured first-party module count under mutation (authoring saw 26 extra; context only, not a bar). PLUS THE SECOND MUTATION TRANSCRIPT: the `return False` replacement, a pasted run showing the E-03 test FAILING and the E-02 test PASSING, the passing run after restoration, and a second empty `git status --porcelain agent_workflows/worktree_lease.py`. A claim that either guard "would fail" without a pasted failing run FAILS this item.
  - Observed evidence:
    MUTATION 1 TRANSCRIPT (injected module-level import `from agent_workflows import runner_shared` in `worktree_lease.py`):
    Failing run under mutation:
    ```
    FF                                                                       [100%]
    =================================== FAILURES ===================================
    _ WorktreeLeaseStdlibOnlyTests.test_worktree_lease_imports_no_first_party_modules _
    ...
    AssertionError: Lists differ: ['agent_workflows.agent_schema', ... 'agent_workflows.term'] != []
    First list contains 27 additional elements.
    ...
    Importing agent_workflows.worktree_lease pulled in unexpected first-party modules: ['agent_workflows.agent_schema', 'agent_workflows.artifact_core', 'agent_workflows.artifact_naming', 'agent_workflows.attention_contract', 'agent_workflows.backlog', 'agent_workflows.config', 'agent_workflows.home_path_patterns', 'agent_workflows.ipd_schema', 'agent_workflows.layout', 'agent_workflows.leak_sanitizer', 'agent_workflows.lifecycle_dirs', 'agent_workflows.lifecycle_style', 'agent_workflows.model_vocab', 'agent_workflows.plans', 'agent_workflows.project_context', 'agent_workflows.project_schema', 'agent_workflows.record_placement', 'agent_workflows.record_producers', 'agent_workflows.render_stream', 'agent_workflows.research_contract', 'agent_workflows.result_types', 'agent_workflows.run_selection_policy', 'agent_workflows.runner_profiles', 'agent_workflows.runner_shared', 'agent_workflows.selectors', 'agent_workflows.status_set', 'agent_workflows.term']
    ```
    Measured first-party module delta count under mutation: 27 extra modules.
    Passing run after restoration:
    `2 passed in 12.20s`
    `git status --porcelain agent_workflows/worktree_lease.py`: clean (empty).

    MUTATION 2 TRANSCRIPT (replaced `lane_merged_into_target` body with `return False`):
    Run under mutation showing E-03 failing and E-02 passing:
    ```
    .F                                                                       [100%]
    =================================== FAILURES ===================================
    __ WorktreeLeaseStdlibOnlyTests.test_lane_merged_into_target_lazy_delegation ___
    ...
    AssertionError: False is not true : agent_workflows.runner_shared MUST be present in sys.modules after lane_merged_into_target is called
    ----------------------------- Captured stdout call -----------------------------
    FILE=<this-worktree>/agent_workflows/worktree_lease.py
    BEFORE=False
    RET=False
    AFTER=False
    =========================== short test summary info ============================
    FAILED tests/test_worktree_lease_stdlib_only.py::WorktreeLeaseStdlibOnlyTests::test_lane_merged_into_target_lazy_delegation
    1 failed, 1 passed in 11.95s
    ```
    Passing run after restoration:
    `2 passed in 11.67s`
    `git status --porcelain agent_workflows/worktree_lease.py`: clean (empty).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `git diff agent_workflows/worktree_lease.py` pasted, showing ONLY docstring lines changed, no import added or removed, and the new citation naming `tests/test_worktree_lease_stdlib_only.py`. Confirm by `grep -n "stays_stdlib_only" agent_workflows/worktree_lease.py` returning NOTHING. Confirm the diff does NOT reintroduce the "even NAMING a run-context parameter" clause (OQ-02). Confirm the `7ckptx` R5.5 RETENTION sentences and the "Retention classification belongs where the run context is, at the driver call site" conclusion are present and unchanged in the post-edit file.
  - Observed evidence:
    `git diff agent_workflows/worktree_lease.py` output:
    ```diff
    diff --git a/agent_workflows/worktree_lease.py b/agent_workflows/worktree_lease.py
    index 30bbfcb2d..488668ff8 100644
    --- a/agent_workflows/worktree_lease.py
    +++ b/agent_workflows/worktree_lease.py
    @@ -393,8 +393,8 @@ def inspect_lane(
         owner record, and one of the five `LANE_STATES`.

         STILL RUN-CONTEXT-FREE, and it must stay that way (pinned by
    -    `tests/test_lane_allocation_idempotent.py::test_worktree_lease_stays_stdlib_only`, which forbids
    -    this module even NAMING a run-context parameter). It takes no run directory and no item record, so
    +    `tests/test_worktree_lease_stdlib_only.py`, which asserts importing this module pulls in
    +    no first-party modules beyond the package baseline). It takes no run directory and no item record, so
         the spec `7ckptx` R5.5 RETENTION inventory cannot live here: measured, `inventory_lane` given
         neither answers EVERY lane unclassifiable ("no run directory or item was supplied"), so consulting
         it from this reading would make even a provably empty lane non-reclaimable. Retention
    ```
    `grep -n "stays_stdlib_only" agent_workflows/worktree_lease.py` returns exit code 1 (nothing).
    The diff modifies only docstring lines, introduces no imports, does NOT reintroduce the "even NAMING a run-context parameter" clause, and preserves the `7ckptx` R5.5 RETENTION sentences and "Retention classification belongs where the run context is, at the driver call site" verbatim.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Pasted BARE `python3 -m pytest` summary line showing the full fast suite passing with its `N passed` count and no new failures, run with no added flags (a run carrying `-n0`, a second `-q`, or `-p no:randomly` FAILS this item, per the execution contract). PLUS evidence of order-independence: two runs of the new test file under DIFFERENT random seeds, both passing, with the seeds stated. PLUS `aw ipd lint --phase pre-transition` on this plan reporting conforming. If the suite has pre-existing unrelated failures, name each one and paste the base-commit comparison showing it fails identically there; do not attribute them to this change without that comparison.
  - Observed evidence:
    Bare full fast suite run (`python3 -m pytest` with no added flags):
    ```
    5054 passed, 2 skipped, 3 warnings in 820.19s (0:13:40)
    ```
    Order-independence runs under two different seeds:
    Seed 12345:
    `python3 -m pytest tests/test_worktree_lease_stdlib_only.py --randomly-seed=12345`
    Output: `2 passed in 14.39s`
    Seed 67890:
    `python3 -m pytest tests/test_worktree_lease_stdlib_only.py --randomly-seed=67890`
    Output: `2 passed in 16.09s`
    `aw ipd lint --phase pre-transition` passes conforming with no errors.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `- Status: to-review` and carries NO `- Readiness:` field, because readiness is an output of `/plan-review` and not of authoring; its absence is the correct state and makes the auto-approve predicate fail closed. EXPLICIT HUMAN APPROVAL IS REQUIRED before execution, and the authoring turn deliberately did not set it.

Execution contract for whoever runs this: begin with `aw ipd begin`, which freezes the requirements and `- Scope-Paths:` and writes the start receipt. Commit through `aw commit <plan> -- <paths>` naming ONLY the two declared paths; never `git add -A`, never `-a`, never `--no-verify`, and never push. E-04 mutates `agent_workflows/worktree_lease.py` TRANSIENTLY and MUST restore it before any commit; verify the staged set with `git diff --cached --name-only` before committing, and re-verify after any failed raw commit attempt, since a rejecting hook can leave unstaged paths in the index. This is a shared checkout: do not revert, stage, or clean up changes you did not make.

Do NOT move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms AND every `V-*` item above carries pasted, concrete evidence with `Result: pass`. In particular, V-04's mutation transcript is not waivable: this plan exists because a guard that was believed to exist did not, and shipping a replacement guard without demonstrating it fails on regression would reproduce that exact defect. The lifecycle transition is owned conditionally: under `aw oc run` / `aw agy run` the RUNNER performs the finalize and terminal transition, so the executor must NOT run `aw ipd finalize` or `git mv` the plan itself; when executed by hand with no runner, the executor finalizes with `aw ipd finalize` (which reconciles the actually-changed paths against the frozen allowlist, requiring a `--scope-reason` for any out-of-scope path and a `--scope-ack` for any declared-but-unmodified one) and never with a hand-rolled `git mv`. When reporting any test or lint result, paste the ACTUAL runner output; never claim a pass that was not run.
