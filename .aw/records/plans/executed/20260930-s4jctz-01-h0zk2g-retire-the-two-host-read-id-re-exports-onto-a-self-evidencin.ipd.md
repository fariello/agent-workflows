# IPD: Retire the two host _read_id re-exports onto a self-evidencing form and correct the three false claims in their comments

- Date: 2026-09-30
- Kind: child
- Concern: Both host runners carry `from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 ...` (in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`), whose stated justification is `tests/test_runner_refork_guard.py`, DELETED in `19313eed`. Backlog `s4jctz` asked for the measurement that decides whether to delete or re-justify them. MEASURED AT HEAD `27a80985`, AND THE ANSWER IS ASYMMETRIC, which is the load-bearing result: the `agy` re-export HAS a live consumer and the `oc` re-export has NONE. `tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_read_deps_and_set` calls `driver._read_id(text)` where `driver` is `tools/ipdrunner/runagy.py`, a shim whose `for _k, _v in vars(agy_runipd).items()` loop copies EVERY non-dunder attribute into its own globals, so `runagy._read_id is agy_runipd._read_id` is True and deleting the `agy` line breaks that call with `AttributeError: module 'runagy' has no attribute '_read_id'` (measured by deleting it). Nothing anywhere reads `oc_runipd._read_id`: the only tree-wide hits for `oc_runipd._read_id` are PROSE (this item, two executed plans, and the module's own comment), `tools/ipdrunner/runipd.py` re-exports five names EXPLICITLY and `_read_id` is not among them, and deleting the `oc` line alone leaves `3387 passed, 2 skipped`. SEPARATELY, THE COMMENTS ABOVE BOTH IMPORTS MAKE THREE CLAIMS THAT ARE FALSE AT HEAD, which matters because each is the stated reason the next maintainer would not touch the line: (1) "The `as <same-name>` form alone was NOT enough (ruff removed it again on the next hook run)" - measured false on BOTH the pinned hook ruff `v0.4.4` and local `0.16.3`, where `... import read_front_matter_id as read_front_matter_id` passes `F401` clean; (2) "this module's `__all__` does not list the private readers" - true as a fact but offered as if `__all__` were unavailable, when `oc_runipd.__all__` EXISTS, already carries five underscore-prefixed entries (`_ANSI_CODES`, `_ANSI_RESET`, `_ANSI_STRIP_RE`, `_one_line`, `_strip_ansi`), and adding `"_read_id"` to it silences `F401` with NO `noqa` under both ruff versions (measured, suite `3387 passed, 2 skipped`); (3) "`_read_status` is still called locally and so needs none" - false, `hasattr` is False on BOTH hosts, `_read_status` is not imported by either, and every `read_front_matter_status` caller is inside `runner_shared`. FINALLY, the two comments' own prose contains the literal text `` `# noqa: F401` ``, which ruff parses as a directive it cannot understand and reports as `warning: Invalid # noqa directive on agent_workflows/oc_runipd.py:825` (and `:74` for `agy`) on EVERY lint of these files.
- Scope: Put each re-export on a form that carries its OWN machine-checked justification instead of a citation to a deleted file, and correct every false claim in the two comments. For `oc_runipd`, whose re-export has no consumer, KEEP the binding but move the suppression from `# noqa` onto `__all__` (the module's existing, already-underscore-carrying export list), so ruff's own export semantics justify it and there is no prose to rot. For `agy_runipd`, which has no `__all__` and one real consumer, keep the binding and RE-JUSTIFY it against that consumer by name, and pin the consumer with a real outcome test inside `tests/` so the guarantee stops depending on a file `testpaths = ["tests"]` never collects. Rewrite both comments to state what is true at HEAD (the deleted guard, the measured consumer asymmetry, and the two suppression mechanisms that were wrongly recorded as unavailable), and reword the prose so it no longer emits ruff's invalid-directive warning. DOES NOT delete either binding: `agy`'s has a live caller, and `oc`'s is retained deliberately so the two hosts keep the symmetric surface every cross-host identity test in `tests/test_runner_shared.py` and `tests/test_verifier_evidence.py` asserts for its neighbours. DOES NOT touch `selectors.py`, does NOT change which reader either name binds to (the PERMISSIVE `read_front_matter_id`, whose whitespace tolerance is a documented contract), does NOT restore the deleted guard file, and does NOT repair the 11 pre-existing failures in `tools/ipdrunner/test_runagy.py` beyond the one `_read_id`/`_read_status` assertion this plan's own change is responsible for.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tools/ipdrunner/test_runagy.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: s4jctz
- Set: s4jctz
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: h0zk2g

## Workflow history
- 2026-10-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: h0zk2g verified (set s4jctz, attempt 1).
- 2026-10-07 approved (aw set): status set to approved

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201, PR-202, PR-203. Reviewed at HEAD `fe2ee961c` in an isolated review lane; plan committed and byte-identical to the lane input, so no pre-review snapshot. Re-verified: both imports and comments unchanged; `oc_runipd.__all__` 23 entries with the five underscore names, `agy_runipd` has no `__all__`; `_read_status` absent on both hosts; `runagy._read_id is agy_runipd._read_id` True; permissive vs strict on tab input `'abc123'` vs `None`; ruff `0.16.3` AND hook-cached `0.4.4`: `as <same-name>` and `__all__` forms pass F401, bare alias fails; two `Invalid # noqa directive` warnings (`agy_runipd.py:74`, `oc_runipd.py:830`); `tools/ipdrunner/test_runagy.py` `11 failed, 14 passed`; carriers `gte0pd`, `fh8x8k` open. Fixed: E-04 would leave its target test red because `_read_deps` was deleted by `72bb113e7`, so it now drops that assertion too (PR-201); stale suite counts replaced by a pre-edit node-id comparison (bare suite now `2 failed, 5219 passed, 2 skipped`) (PR-202); bare `:825` citation re-anchored on a quoted string (IPD-C801) (PR-203).
- 2026-10-07 reviewed (aw set): plan-review: PR-201..PR-203 applied
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `s4jctz` at HEAD `27a80985`. The item asked for a measurement ("measure what actually reads `_read_id` from either host module") and the measurement came back ASYMMETRIC, which redirected the plan away from the item's own either/or framing ("either delete both lines with the `# noqa` or re-justify them against something real"): `agy`'s re-export has a live consumer through the `runagy.py` shim's `vars()` copy loop and so CANNOT be deleted, while `oc`'s has none. Three additional false claims were found in the comments themselves, each of which is the stated reason a maintainer would leave the line alone, plus a ruff invalid-directive warning emitted by the comment prose. Every measurement in this plan was taken by running it, and each mutation was reverted (`git status` clean) before the next.

## Goal

Replace a stale citation with a mechanism. Each `_read_id` re-export ends this plan justified by something a tool or a test enforces (ruff's `__all__` export semantics for `oc`, a named and newly-pinned consumer for `agy`) rather than by a comment pointing at a file deleted in `19313eed`, and the three false claims and one ruff warning those comments currently carry are gone.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-home the oc suppression onto `__all__`

- [x] E-01 In `agent_workflows/oc_runipd.py`, add `"_read_id"` to the module's existing `__all__` list and DELETE the trailing `# noqa: F401 - a DELIBERATE re-export; ...` comment from the `from agent_workflows.selectors import read_front_matter_id as _read_id` line, leaving the bare import. Keep the alias name `_read_id` and keep it bound to the PERMISSIVE public `read_front_matter_id` (not `selectors._read_id`, the strict internal reader): the two are different objects and the permissive one tolerates `-  Id:` (two spaces) and `-\tId:` where the strict one returns `None` for the tab, and `selectors`' own note records that strictness as an `aw find` matching contract. Insert `"_read_id"` in the list's existing leading underscore cluster, beside `"_ANSI_CODES"`, so the file's own ordering convention is preserved. The suppression mechanism this replaces is not a style preference: `__all__` membership makes ruff treat the name as an intentional export, which is the same fact the current comment asserts in prose and asks a reader to trust.
  - Depends on: none
  - Expected outcome: `ruff check --select F401 agent_workflows/oc_runipd.py` passes with no `noqa` present on the import line, under BOTH the hook-pinned `v0.4.4` (`.pre-commit-config.yaml`, `ruff-pre-commit` `rev: v0.4.4`) and the locally installed ruff; `agent_workflows.oc_runipd._read_id` still resolves and `is agent_workflows.selectors.read_front_matter_id` is still True; `pre-commit run ruff --files agent_workflows/oc_runipd.py` does not rewrite the line.
  - Execution state: performed

### Task group 2: re-justify the agy re-export against its real consumer and pin it

- [x] E-02 In `agent_workflows/agy_runipd.py`, KEEP the import and its `# noqa: F401`, because this module has no `__all__` to carry the export and so has no mechanism-based route available (verified at HEAD: `hasattr(agy_runipd, "__all__")` is False), but REPLACE the suppression's trailing justification text so it cites the LIVE consumer instead of the deleted file. The new text must name `tools/ipdrunner/test_runagy.py` and the shim `tools/ipdrunner/runagy.py` through which it reaches this attribute, and must name the test added by E-03 as the in-suite guard. Do NOT restore or recreate `tests/test_runner_refork_guard.py`, and do NOT delete this import: deleting it is what makes the consumer fail, which E-03's test will then hold.
  - Depends on: E-01
  - Expected outcome: the `agy_runipd` import line's justification names only artifacts that EXIST at execution time; `ruff check --select F401 agent_workflows/agy_runipd.py` still passes; `agy_runipd._read_id is selectors.read_front_matter_id` still True.
  - Execution state: performed

- [x] E-03 Add an OUTCOME test to `tests/test_runner_shared.py` pinning that BOTH hosts expose `_read_id` bound to `selectors.read_front_matter_id`, in the same object-identity style the file's neighbouring cross-host tests already use (`test_cross_host_success_bar_constants_and_tokens` asserts `assertIs(getattr(oc_runipd, name), shared)` for a list of names, and `DriverErrorUnificationTests` does the same for classes). The test must (a) assert `assertIs` for `oc_runipd._read_id` and `agy_runipd._read_id` against `selectors.read_front_matter_id`, and (b) CALL the bound reader and assert its observable return, including on the permissive spellings that distinguish it from the strict internal reader: `- Id: abc123` -> `"abc123"`, `-  Id: abc123` (two spaces) -> `"abc123"`, and `-\tId: abc123` (tab) -> `"abc123"`, the last being the case where `selectors._read_id` returns `None`, so the assertion proves WHICH reader is bound and not merely that some attribute exists. This is deliberately a behavior test and not a structural one: it must not read source text, count imports, or assert on comments (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). Place it beside the existing cross-host identity tests rather than in a new file.
  - Depends on: E-02
  - Expected outcome: the new test passes at HEAD (the bindings already exist) and FAILS if either host's import is removed; the tab case documents the permissive-versus-strict distinction by outcome. Both facts are demonstrated in V-03 by temporarily removing each import.
  - Execution state: performed

- [x] E-04 Repair the ONE assertion in `tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_read_deps_and_set` that this plan's subject matter is responsible for: it calls `driver._read_status(text)` and fails at HEAD with `AttributeError: module 'runagy' has no attribute '_read_status'`, because `_read_status` is on NEITHER host (measured: `hasattr` False on both) while the same test's `driver._read_id(text)` call succeeds. Change that one assertion to read the status through a name that exists (the shim copies every non-dunder attribute of `agy_runipd`, so any reader the host genuinely exposes is reachable; `selectors.read_front_matter_status` is the owner), or drop that single line if no host-exposed equivalent exists, and say in the test which was done and why.
  THE NEXT LINE FAILS TOO, AND IT IS THE SAME TEST (plan-review 2026-10-07, PR-201). Fixing only `_read_status` does NOT turn the test green: the following line `self.assertEqual(driver._read_deps(text), ["dep001", "dep002"])` then raises, because `_read_deps` was DELETED from both hosts by commit `72bb113e7` ("make the runners consume the shared Item-Dependencies predicate"), which retired the legacy `- Dependencies:` field the fixture still uses. Measured at review HEAD `fe2ee961c`: `hasattr(runagy, "_read_deps")` is False; the host's surviving `_read*` names are `_read_id`, `_read_order`, `_read_set`, `_read_from_backlog`, `_read_item_dependencies`, `_read_kind`; and `runagy._read_item_dependencies(text)` returns `([], None)` on this fixture's legacy `- Dependencies: [dep001, dep002]` line (and also `([], None)` on `- Item-Dependencies: executed:dep001, executed:dep002`, so it is not a drop-in reader for this assertion either). So E-04 MUST ALSO DROP the `_read_deps` assertion, recording in a one-line test comment that legacy `Dependencies:` parsing was retired by `72bb113e7` and that Item-Dependencies parsing is covered in `tests/`. Do NOT reintroduce `_read_deps` on either host. This is the same root cause as `_read_status` (a test reaching names the hosts no longer carry), inside the same test this item exists to make green, so it is in scope; the remaining 10 failing tests are not.
  Do NOT attempt the other 10 failures in that file: they are pre-existing, unrelated to `_read_id`, and out of this plan's scope (recorded under "Deferred / out of scope").
  - Depends on: E-03
  - Expected outcome: `test_read_deps_and_set` passes (with both the `_read_status` and the `_read_deps` assertions resolved as above), so the ONE out-of-suite consumer of `agy_runipd._read_id` is green and the `_read_id` assertion it makes is actually exercised rather than being masked by an earlier `AttributeError` on a different name. The file's remaining failure count drops from 11 to 10.
  - Execution state: performed

### Task group 3: correct the comments

- [x] E-05 Rewrite the comment blocks above BOTH imports (the block ending `... so the suppression is the mechanism that keeps the re-export alive. _read_status is still called locally and so needs none.` in `oc_runipd`, and its shorter twin ending `... required of BOTH runners.` in `agy_runipd`) so that every claim is true at HEAD. Each of the three corrections is a claim a maintainer would rely on, so KEEP the reasoning and fix the fact rather than deleting the paragraph: (a) the `as <same-name>` form DOES suppress `F401` on both the pinned and current ruff, so the sentence saying it "was NOT enough" must be corrected and dated, noting it may have been true of the ruff of its time; (b) `oc_runipd.__all__` EXISTS and already carries underscore entries, so it IS an available mechanism and is now the one in use there, while `agy_runipd` has no `__all__`, which is why the two hosts deliberately differ; (c) `_read_status` is on NEITHER host, so the "still called locally" clause must go. Also record the measured consumer asymmetry (`agy` has one consumer via the `runagy.py` shim, `oc` has none and is retained for cross-host symmetry) so the next reader does not re-derive it. REWORD any prose occurrence of the literal `# noqa: F401` (both blocks contain one) so ruff stops reporting the `Invalid # noqa directive` warning on the `oc_runipd` comment line beginning ``# `_read_id`'s `# noqa: F401` IS LOAD-BEARING`` (`oc_runipd.py:830` at review HEAD `fe2ee961c`, `:825` at authoring) and on its `agy_runipd` twin (`agy_runipd.py:74`); naming the rule as `F401` without the `# noqa:` prefix is sufficient.
  - Depends on: E-04
  - Expected outcome: `ruff check agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` emits ZERO `Invalid # noqa directive` warnings (two today); no sentence in either block cites `tests/test_runner_refork_guard.py` as a live requirement; the `_read_status` clause is gone.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE DEFAULT SUITE DOES NOT SEE `tools/`. `pyproject.toml` sets `testpaths = ["tests"]` and `Makefile`'s `test` and `test-all` targets both invoke `python3 -m pytest tests/` explicitly, so `tools/ipdrunner/test_runagy.py` is collected by NO standard invocation. Grepping `.github/workflows/*.yml` for `ipdrunner` or `test_runagy` returns nothing, so CI does not reach it either. This is why the one real consumer of `agy_runipd._read_id` has been failing unnoticed and why E-03 puts the guard in `tests/`.
- `agent_workflows/oc_runipd.py` HAS an `__all__` (22 entries) and `agent_workflows/agy_runipd.py` does NOT. The `oc` list already contains five underscore-prefixed names, so exporting a private name there is an established convention in that exact file and not a new precedent.
- The `as <same-name>` re-export idiom is used deliberately throughout both hosts to mark intentional re-exports against autoformatter removal; `oc_runipd`'s `runner_shared` import block (`DISPOSITION_FRESH_EXECUTION as DISPOSITION_FRESH_EXECUTION` and nine more) and `agy_runipd`'s `render_stream` block (`REFUSAL_KEY as REFUSAL_KEY` and others) are both written that way, and `agy_runipd`'s own comment states the intent: "The `as <same-name>` form marks the ones this module does not call itself as an intentional re-export, so an autoformatter cannot strip them."
- `tools/ipdrunner/runagy.py` and `tools/ipdrunner/runipd.py` are NOT symmetric, and the difference decides this plan's asymmetry. `runagy.py` re-exports with a loop, `for _k, _v in vars(agy_runipd).items(): if not _k.startswith("__"): globals()[_k] = _v`, which captures PRIVATE names including `_read_id`. `runipd.py` re-exports five names by explicit assignment (`main`, `DriverError`, `Palette`, `Heartbeat`, `PlanRecord`) and so does not expose `_read_id` at all.
- `selectors` ships TWO readers of this shape and they are NOT interchangeable: the public `read_front_matter_id` and the module-internal `selectors._read_id` are distinct objects, and on tab-separated input (`-\tId: abc123`) the public one returns `abc123` while the internal one returns `None`. `selectors.py`'s own note records the strict pair as backing an `aw find` matching contract, and `runner_shared.parse_plan_file`'s docstring warns that "swapping to the strict readers here would silently narrow which front-matter spellings both drivers accept". Both host aliases bind the PERMISSIVE one and must keep doing so.
- `runner_shared` declares no `__all__` (`hasattr` False), and `agent_workflows/__init__.py` declares no `__all__` either and imports neither host module, so neither runner is reachable through a package-level re-export surface. An external importer would have to name `agent_workflows.oc_runipd._read_id` directly.
- Three tests in the full suite fail at HEAD for reasons unrelated to this plan (`tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory`, `tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw`, and `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, the last reporting eight `config unset`/`upgrade-test` description gaps). They are absent from the DEFAULT (`not slow`) suite, which is `3387 passed, 2 skipped` clean. V-items must compare against these baselines rather than demanding a wholly green `-m ''` run.

## Findings

| # | Finding | Evidence (measured at HEAD `27a80985`) | Consequence for this plan |
|---|---|---|---|
| F-1 | The `agy` re-export HAS a live consumer, so "delete both lines" is not available | `tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_read_deps_and_set` calls `driver._read_id(text)`; `driver` is `import runagy as driver`; `runagy.py`'s `vars(agy_runipd)` loop yields `runagy._read_id is agy_runipd._read_id` -> True. Deleting the `agy` import makes that call raise `AttributeError: module 'runagy' has no attribute '_read_id'. Did you mean: '_read_kind'?` | E-02 keeps the `agy` binding and re-justifies it; the item's "delete both" option is rejected on evidence |
| F-2 | The `oc` re-export has NO consumer | Tree-wide search for `oc_runipd._read_id` returns only prose (this backlog item, executed plans `sy7uwh` and `t0ovw6`, and the module's own comment). `runipd.py` assigns five names explicitly and `hasattr(runipd, "_read_id")` is False. `'_read_id' in oc_runipd.__all__` is False. Deleting ONLY the `oc` line leaves the default suite `3387 passed, 2 skipped` | E-01 could have deleted it; it keeps it for cross-host symmetry (F-8) but removes the rotting prose justification |
| F-3 | Deleting BOTH lines passes the default suite, so the suite is not what protects them | With both imports removed: default suite `3387 passed, 2 skipped, 3 warnings in 63.25s`; full `-m ''` run `3 failed, 3591 passed, 2 skipped` where all three failures are the pre-existing ones in F-9. Both hosts still import cleanly | The guarantee is currently unheld inside `tests/`; E-03 adds the guard there |
| F-4 | CLAIM (1) IN THE COMMENT IS FALSE: the `as <same-name>` form DOES suppress `F401` | `... import read_front_matter_id as read_front_matter_id` -> `All checks passed!` on ruff `0.16.3` AND on the hook-pinned `0.4.4`; the aliased form `as _read_id` -> `F401 ... imported but unused` on both | E-05(a) corrects it; the claim is the stated reason `noqa` was thought necessary |
| F-5 | CLAIM (2) IS MISLEADING: `__all__` IS an available mechanism in `oc_runipd` | `oc_runipd.__all__` has 22 entries including `_ANSI_CODES`, `_ANSI_RESET`, `_ANSI_STRIP_RE`, `_one_line`, `_strip_ansi`. Adding `"_read_id"` and deleting the `noqa` gives `All checks passed!` on both ruff versions and default suite `3387 passed, 2 skipped` | E-01 adopts it; E-05(b) records why `agy` cannot (no `__all__`) |
| F-6 | CLAIM (3) IS FALSE: `_read_status` is on NEITHER host | `hasattr(oc_runipd, "_read_status")` False; `hasattr(agy_runipd, "_read_status")` False; neither module imports it; every `read_front_matter_status` call site is in `runner_shared` or `selectors` | E-05(c) deletes the clause. It is also the cause of F-7 |
| F-7 | The same missing `_read_status` makes the one live consumer RED at HEAD, masking its `_read_id` assertion | `test_read_deps_and_set` fails on line `self.assertEqual(driver._read_status(text), "to-review")` with `AttributeError: module 'runagy' has no attribute '_read_status'. Did you mean: '_read_set'?`. Its `_read_id` assertion is two lines EARLIER and passes, so the file's own evidence for the re-export is real but the test never reaches green | E-04 fixes that one assertion so the consumer is actually exercised |
| F-8 | Both hosts are asserted SYMMETRIC for their neighbouring shared symbols, so removing `_read_id` from one host only would be a lone asymmetry | `tests/test_runner_shared.py::test_cross_host_success_bar_constants_and_tokens` asserts `assertIs` against `runner_shared` for six function names on BOTH hosts; `DriverErrorUnificationTests` does so for `DriverError`, `StallTimeout`, `EmptyStatusSelection`; `tests/test_verifier_evidence.py::test_cross_driver_symmetry` for six more; `tests/test_agy_runipd_cli.py` asserts `assertIs(getattr(agy_runipd, name), getattr(oc_runipd, name))` | The plan keeps BOTH bindings and E-03's test asserts the pair, matching the file's established shape |
| F-9 | Three full-suite failures are pre-existing and unrelated | Run at HEAD with NO modifications: `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory`, `tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw`, `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description` (reports eight `config unset` / `upgrade-test` description gaps). Reproduced with a clean `git status` | V-items compare to this baseline; the plan must not claim to fix or be blamed for them |
| F-10 | The comment PROSE itself emits a ruff warning on every lint of these files | `ruff check --select F401 agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` -> `warning: Invalid # noqa directive on agent_workflows/agy_runipd.py:74` and the same warning on `agent_workflows/oc_runipd.py` (line 830 at review, 825 at authoring), both lines being the prose sentence beginning ``# `_read_id`'s `# noqa: F401` IS LOAD-BEARING`` and so containing the literal `` `# noqa: F401` `` | E-05 rewords both; V-05 counts the warnings to zero |
| F-11 | The deleted guard's own table confirms what the comment claims it required, so the historical justification was genuine | `git show 19313eed^:tests/test_runner_refork_guard.py` contains `Owned("read_front_matter_id", "selectors", BOTH, runner_name="_read_id")` and a `FrontMatterReaderBehaviorTests` asserting `module._read_id(text) == "abc123"` on both hosts plus `selectors._read_id(TWO_SPACES) is None` / `selectors._read_id(TAB) is None` | The re-export is not cargo cult; E-03 restores the OUTCOME half of that coverage (identity plus permissive-spelling behavior) without restoring a structural census |
| F-13 | E-04 as authored could not turn its target test green: `_read_deps` is also absent from both hosts | Review HEAD `fe2ee961c`: `hasattr(runagy, "_read_deps")` False; `git log -S"def _read_deps"` -> `72bb113e7 fix(lanetruth): make the runners consume the shared Item-Dependencies predicate`, whose diff deletes `def _read_deps` from both hosts | E-04 now drops that assertion too (PR-201) |
| F-12 | `19313eed` was a bulk suite trim, not a decision about this symbol | `git show 19313eed --stat` is titled `test: trim test suite from 9,136 to under 2,000 tests` and deletes dozens of files including `test_runner_refork_guard.py` (and trims `test_agy_runipd_cli.py` by 461 lines) | Nothing recorded a judgement that the `_read_id` guarantee should lapse, which supports re-pinning it rather than dropping it |

## Proposed changes (ordered, validatable)

1. `agent_workflows/oc_runipd.py`: add `"_read_id"` to `__all__` beside the existing underscore entries and strip the trailing `# noqa: F401 ...` from the import line (E-01).
2. `agent_workflows/agy_runipd.py`: keep the `# noqa: F401` (no `__all__` exists here) but rewrite its justification to cite `tools/ipdrunner/test_runagy.py` via `tools/ipdrunner/runagy.py`, plus E-03's in-suite guard (E-02).
3. `tests/test_runner_shared.py`: add a cross-host outcome test asserting object identity for both hosts' `_read_id` against `selectors.read_front_matter_id` AND calling it on one-space, two-space, and tab spellings (E-03).
4. `tools/ipdrunner/test_runagy.py`: fix the single `driver._read_status(...)` assertion so the file's `_read_id` coverage actually runs (E-04).
5. Both hosts: rewrite the comment blocks to correct F-4, F-5, F-6, record the F-1/F-2 asymmetry, and reword the prose that triggers F-10 (E-05).

## Deferred / out of scope (with reason)

- THE OTHER 10 FAILURES IN `tools/ipdrunner/test_runagy.py`. At HEAD that file is `11 failed, 14 passed`; E-04 fixes exactly one, the `_read_status` assertion inside the test that also exercises `_read_id`. The other 10 (seven in `AgyExecutionLifecycleTests`, plus the remainder) concern run lifecycle, stall recovery, and report commands, and have no bearing on the re-exports. Fixing them here would silently widen a `low`/`chore` plan into a test-suite rehabilitation.
  - Carrier: gte0pd
- BRINGING `tools/ipdrunner/` INTO `testpaths`. This is the root cause of F-3/F-7 (an uncollected test file rotted unnoticed) and is a genuine gap, but adding it would turn 10 further pre-existing failures red in every run and in CI, which is a maintainer decision about a shared gate rather than a side effect of this change. E-03 mitigates the specific risk by putting this plan's guarantee in `tests/`. Recorded as OQ-01.
  - Carrier: gte0pd
- RESTORING `tests/test_runner_refork_guard.py`. The maintainer ruling recorded in this item's workflow history is explicit: "We do not test to make sure code does not change or pin imports. The deleted test will not be restored." E-03 therefore pins OUTCOMES (which object is bound, and what it returns on three input spellings), not a symbol census, per AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE".
  - Carrier-Declined: This is a DECISION ALREADY TAKEN by the maintainer, not an outstanding obligation, so there is nothing for a carrier to carry forward. The ruling is recorded verbatim in backlog `s4jctz`'s own workflow history ("The deleted test will not be restored"). Filing a carrier would misrepresent a settled refusal as pending work.
- DELETING EITHER BINDING. Rejected on F-1 (the `agy` one has a live caller) and F-8 (removing only `oc`'s would leave a cross-host asymmetry in a pair whose neighbours are all asserted symmetric). The measurement the item asked for is what forecloses this, and it is recorded rather than assumed.
  - Carrier-Declined: This is the plan's ANSWER to the question backlog `s4jctz` posed, reached on measurement, not a deferral. `s4jctz` asked whether to delete or re-justify; F-1 and F-2 measure that `agy`'s re-export has a live consumer and `oc`'s has none, and the plan re-justifies both. No future work remains to hand off.
- ADDING `__all__` TO `agy_runipd`. It would make E-02's `noqa` unnecessary and unify the two hosts, but introducing a module-wide export surface to a 4172-line runner changes what `from agy_runipd import *` means and what other tooling considers public. That is a larger architectural call than a `chore` should make unilaterally. Recorded as OQ-02.
  - Carrier: fh8x8k
- UNIFYING THE TWO SHIMS' RE-EXPORT STYLE (`runagy.py`'s `vars()` loop versus `runipd.py`'s five explicit assignments). The divergence is the mechanical reason for this plan's asymmetry (F-2) and is worth a decision, but changing either shim's surface can break operator code this plan has not measured.
  - Carrier: fh8x8k
- `_read_status`'s ABSENCE FROM BOTH HOSTS AS A DESIGN QUESTION. E-04/E-05 record and work around it; whether either host SHOULD expose it (its twin `_read_id` is exposed on both) is a separate question, and asserting an answer here would change a surface on no evidence of a consumer.
  - Carrier: fh8x8k

## Scope check

- Over-scope: none. Every declared path is touched by at least one E-item: `oc_runipd.py` (E-01, E-05), `agy_runipd.py` (E-02, E-05), `tests/test_runner_shared.py` (E-03), `tools/ipdrunner/test_runagy.py` (E-04). No `.spec.md` file is in scope, so this plan declares no spec amendment.
- Under-scope: the plan does not repair the collection gap that let the one consumer rot (OQ-01) nor the 10 unrelated failures in the same file, both recorded above with reasons. It also leaves `agy_runipd` on a `noqa` rather than a mechanism, which is a real asymmetry with `oc_runipd` after E-01 and is deliberate (OQ-02): the alternative requires adding an `__all__` to that module.

## Required tests / validation

- `python3 -m pytest` (BARE, per AGENTS.md; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`). Baseline: a bare run at execution HEAD BEFORE any edit, pasted; compare the FAILING NODE-ID SET by name, and require the pass count to rise by exactly the tests E-03 adds. The authoring-time `3387 passed, 2 skipped` is stale context only: at review HEAD `fe2ee961c` the bare suite read `2 failed, 5219 passed, 2 skipped`, the two failures being `tests/test_readiness_absence_invariant.py` live-corpus tests unrelated to this plan (plan-review 2026-10-07, PR-202).
- `python3 -m pytest tests/ -m ''` for the full suite, compared by failing node id against a pre-edit run of the same command at execution HEAD (also pasted). F-9's three named failures are the authoring-time baseline and are context, not the bar.
- `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts=""` to show `test_read_deps_and_set` green and the file's failure count at 10 (from 11).
- `ruff check --select F401 agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` under the locally installed ruff AND under the hook-pinned `v0.4.4`, showing zero errors and zero `Invalid # noqa directive` warnings.
- `pre-commit run ruff --files agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` and `pre-commit run ruff-format --files ...`, to prove the hook does not re-delete the E-01 import (the exact failure mode `sy7uwh` recorded, where `ruff --fix` removed it on the next hook run).
- A negative control per host: temporarily delete each import, show the E-03 test FAILS, and restore. A guard that cannot fail is not a guard.

## Spec / documentation sync

N/A with reason. No `.spec.md` governs these two import lines: the change is a lint-suppression mechanism, a comment correction, and one added test. `Scope-Paths` declares no spec file, so the runners' spec-edit announcement and the finalize scope gate should report no declared spec edits for this plan. No user-facing documentation describes `_read_id` on either host (it is a private alias absent from both `agent_workflows/__init__.py` and `oc_runipd.__all__` at HEAD), so no README or CHANGELOG entry is warranted for a change with no observable behavior difference.

## Open questions

### OQ-01: Should `tools/ipdrunner/` be added to `testpaths` so its tests stop rotting unnoticed?

- Blocking: no
- Status: deferred
- Owner: maintainer
- Carrier: gte0pd
- Resolution or deferral rationale: DEFERRED, not silently dropped, because it is the ROOT CAUSE of this item existing: `testpaths = ["tests"]` and both `Makefile` targets naming `tests/` mean `tools/ipdrunner/test_runagy.py` is collected by no standard invocation and by no CI job, which is how a test asserting `driver._read_id(...)` sat red and unnoticed. Adding the directory would immediately turn 10 further pre-existing failures red in every developer run and in CI, so it is a decision about a SHARED gate (accept 10 red, fix them first, or leave the file uncollected and eventually delete it) that belongs to the maintainer, not to a `low`/`chore` plan. Non-blocking because E-03 mitigates the specific risk by pinning THIS plan's guarantee inside `tests/`, where it is collected.

### OQ-02: Should `agy_runipd` gain an `__all__` so its re-export needs no `noqa`, matching `oc_runipd` after E-01?

- Blocking: no
- Status: deferred
- Owner: maintainer
- Carrier: fh8x8k
- Resolution or deferral rationale: DEFERRED. E-01 can move `oc_runipd` onto a mechanism precisely because that module already has an `__all__` carrying five underscore names (F-5); `agy_runipd` has none (`hasattr` False), so E-02 must keep its `noqa`, leaving the two hosts justified differently. Adding an `__all__` to a 4172-line runner changes what `import *` exports and what other tooling treats as that module's public surface, which is disproportionate to this item and unmeasured here. Non-blocking because the `noqa` E-02 leaves in place is CORRECT and, unlike today's, cites artifacts that exist.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: (a) pasted output of `ruff check --select F401 agent_workflows/oc_runipd.py` showing `All checks passed!` under the locally installed ruff AND under the hook-pinned `v0.4.4`, with the version banner of each shown; (b) pasted output of `python3 -c` printing `'_read_id' in oc_runipd.__all__` -> `True` and `oc_runipd._read_id is selectors.read_front_matter_id` -> `True`; (c) the import line quoted from the file showing NO `# noqa` remains on it; (d) pasted `pre-commit run ruff --files agent_workflows/oc_runipd.py` plus `git diff --stat` afterwards proving the hook did NOT re-delete the import (this is the exact regression `sy7uwh` hit). Evidence that only asserts the attribute exists FAILS this item: (a) and (d) together are what prove the mechanism replaced the suppression.
  - Observed evidence:
    (a) Ruff checks under local and hook-pinned versions:
    ```
    $ ruff --version && ruff check --select F401 agent_workflows/oc_runipd.py
    ruff 0.16.3
    All checks passed!

    $ ~/.cache/pre-commit/repozypou4s9/py_env-python3.12/bin/ruff --version && ~/.cache/pre-commit/repozypou4s9/py_env-python3.12/bin/ruff check --select F401 agent_workflows/oc_runipd.py
    ruff 0.4.4
    All checks passed!
    ```
    (b) Python export and identity check:
    ```
    $ python3 -c "from agent_workflows import oc_runipd, selectors; print('_read_id in oc_runipd.__all__:', '_read_id' in oc_runipd.__all__); print('oc_runipd._read_id is selectors.read_front_matter_id:', oc_runipd._read_id is selectors.read_front_matter_id)"
    _read_id in oc_runipd.__all__: True
    oc_runipd._read_id is selectors.read_front_matter_id: True
    ```
    (c) Import line quoted from agent_workflows/oc_runipd.py (no # noqa):
    ```python
    from agent_workflows.selectors import read_front_matter_id as _read_id
    ```
    (d) Pre-commit ruff run and git diff --stat:
    ```
    $ pre-commit run ruff --files agent_workflows/oc_runipd.py
    ruff.....................................................................Passed

    $ git diff --stat agent_workflows/oc_runipd.py
     agent_workflows/oc_runipd.py | 24 ++++++++++++++----------
     1 file changed, 14 insertions(+), 10 deletions(-)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (a) the rewritten `agy_runipd` import line quoted in full, showing its justification names `tools/ipdrunner/test_runagy.py`, `tools/ipdrunner/runagy.py`, and E-03's test, and NO LONGER presents `tests/test_runner_refork_guard.py` as a live requirement; (b) pasted `ruff check --select F401 agent_workflows/agy_runipd.py` -> `All checks passed!`; (c) pasted proof the cited consumer is real, i.e. `python3 -c` importing `runagy` from `tools/ipdrunner` and printing `runagy._read_id is agy_runipd._read_id` -> `True`. A rewritten comment whose cited test does not actually reach the attribute FAILS this item.
  - Observed evidence:
    (a) Rewritten import line quoted from agent_workflows/agy_runipd.py:
    ```python
    from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - re-export for tools/ipdrunner/runagy.py (tested by tools/ipdrunner/test_runagy.py) and pinned by tests/test_runner_shared.py
    ```
    (b) Ruff F401 check:
    ```
    $ ruff check --select F401 agent_workflows/agy_runipd.py
    All checks passed!
    ```
    (c) Proof cited consumer is real:
    ```
    $ python3 -c "import sys; sys.path.insert(0, 'tools/ipdrunner'); import runagy; from agent_workflows import agy_runipd; print('runagy._read_id is agy_runipd._read_id:', runagy._read_id is agy_runipd._read_id)"
    runagy._read_id is agy_runipd._read_id: True
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (a) pasted BARE `python3 -m pytest` summary from BEFORE any edit and from AFTER, showing the new test passing, the failing node-id sets identical by name, and the passed count higher by exactly the number of tests E-03 added; (b) the NEGATIVE CONTROL, run twice, once per host: with `oc_runipd`'s import deleted, paste the new test's FAILURE; restore; with `agy_runipd`'s import deleted, paste the FAILURE; restore; then paste `git status --short` proving both files are clean again. (c) pasted evidence of the behavioral half: the test's tab-input assertion demonstrated, alongside a direct measurement showing `selectors._read_id` returns `None` for the same tab input while `selectors.read_front_matter_id` returns `abc123`, which is what proves the PERMISSIVE reader is bound. A test that passes both before and after the import is removed is not a guard and FAILS this item.
  - Observed evidence:
    (a) Bare pytest runs before and after edits:
    Before edit baseline:
    ```
    6305 passed, 2 skipped, 3 warnings in 586.11s (0:09:46)
    (0 failed)
    ```
    After edit:
    ```
    6306 passed, 2 skipped, 3 warnings in 230.78s (0:03:50)
    (0 failed; passed count rose by exactly 1, matching test_cross_host_read_id_permissive_reader_reexport)
    ```
    (b) Negative control (run twice):
    With `oc_runipd`'s import removed:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -k test_cross_host_read_id_permissive_reader_reexport
    =================================== FAILURES ===================================
    _ CrossHostReadIdReExportTests.test_cross_host_read_id_permissive_reader_reexport _
    [gw11] linux -- Python 3.14.6 <home>/venv/p3.14/bin/python3
    self = <tests.test_runner_shared.CrossHostReadIdReExportTests testMethod=test_cross_host_read_id_permissive_reader_reexport>
        def test_cross_host_read_id_permissive_reader_reexport(self):
            from agent_workflows import selectors
            # (a) Assert object identity for both hosts against selectors.read_front_matter_id
    >       self.assertIs(oc_runipd._read_id, selectors.read_front_matter_id)
    E       AttributeError: module 'agent_workflows.oc_runipd' has no attribute '_read_id'. Did you mean: '_read_kind'?
    tests/test_runner_shared.py:208: AttributeError
    FAILED tests/test_runner_shared.py::CrossHostReadIdReExportTests::test_cross_host_read_id_permissive_reader_reexport
    1 failed in 4.84s
    ```
    Restored `agent_workflows/oc_runipd.py`.
    With `agy_runipd`'s import removed:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -k test_cross_host_read_id_permissive_reader_reexport
    =================================== FAILURES ===================================
    _ CrossHostReadIdReExportTests.test_cross_host_read_id_permissive_reader_reexport _
    [gw8] linux -- Python 3.14.6 <home>/venv/p3.14/bin/python3
    self = <tests.test_runner_shared.CrossHostReadIdReExportTests testMethod=test_cross_host_read_id_permissive_reader_reexport>
        def test_cross_host_read_id_permissive_reader_reexport(self):
            from agent_workflows import selectors
            # (a) Assert object identity for both hosts against selectors.read_front_matter_id
            self.assertIs(oc_runipd._read_id, selectors.read_front_matter_id)
    >       self.assertIs(agy_runipd._read_id, selectors.read_front_matter_id)
    E       AttributeError: module 'agent_workflows.agy_runipd' has no attribute '_read_id'. Did you mean: '_read_kind'?
    tests/test_runner_shared.py:209: AttributeError
    FAILED tests/test_runner_shared.py::CrossHostReadIdReExportTests::test_cross_host_read_id_permissive_reader_reexport
    1 failed in 5.16s
    ```
    Restored `agent_workflows/agy_runipd.py`.
    Status check proving both files clean/restored:
    ```
    $ git status --short
     M agent_workflows/agy_runipd.py
     M agent_workflows/oc_runipd.py
     M tests/test_runner_shared.py
     M tools/ipdrunner/test_runagy.py
    ```
    (c) Behavioral permissive reader demonstration:
    ```
    $ python3 -c '
    from agent_workflows import selectors
    for text in ["- Id: abc123", "-  Id: abc123", "-\tId: abc123"]:
        print(repr(text), "read_front_matter_id:", repr(selectors.read_front_matter_id(text)), "selectors._read_id:", repr(selectors._read_id(text)))
    '
    '- Id: abc123' read_front_matter_id: 'abc123' selectors._read_id: 'abc123'
    '-  Id: abc123' read_front_matter_id: 'abc123' selectors._read_id: None
    '-\tId: abc123' read_front_matter_id: 'abc123' selectors._read_id: None
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (a) pasted `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -k test_read_deps_and_set` showing it PASSES (it fails at HEAD with `AttributeError: module 'runagy' has no attribute '_read_status'`); (b) pasted whole-file summary line showing `10 failed` (down from the HEAD measurement of `11 failed, 14 passed`), with the 10 remaining named so it is visible that none concerns `_read_id`; (c) a statement of WHICH remedy was taken for the `_read_status` line (rerouted to an existing reader, or dropped) and why, and confirmation that the `_read_deps` assertion was dropped with its `72bb113e7` comment, quoting the edited test body; (d) `git diff --stat tools/ipdrunner/test_runagy.py` showing only that one test changed. Claiming the file is green FAILS this item: it is not, and the deferred scope says so.
  - Observed evidence:
    (a) Targeted test run showing pass:
    ```
    $ python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -k test_read_deps_and_set
    ============================= test session starts ==============================
    tools/ipdrunner/test_runagy.py .                                         [100%]
    ======================= 1 passed, 24 deselected in 0.43s =======================
    ```
    (b) Whole-file summary and remaining 10 failures:
    ```
    FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_concurrent_work_statement_in_prompts
    FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_runagy_two_turn_execution_with_clean_verification
    FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_prepare_only_mode
    FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_explicit_run_id
    FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_default_start_subcommand_inference
    FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_runagy_status_and_report_commands
    FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_stall_timeout_and_resume_recovery
    FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_runagy_no_verify_skips_turn2
    FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_verification_blocked_sets_disposition_partial
    FAILED tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_dependency_status_execution_vs_review
    ======================== 10 failed, 15 passed in 7.38s =========================
    ```
    (c) Statement of remedy and quoted test body:
    Neither `agy_runipd` nor `runagy` exposes `_read_status` (measured `hasattr` is `False` on both hosts); status reading is owned and tested directly by `selectors.read_front_matter_status`. Because no host-exposed equivalent exists on `driver`, the assertion was dropped with an explanatory comment. The `_read_deps` assertion was also dropped because legacy `Dependencies:` parsing was retired by commit `72bb113e7` ("make the runners consume the shared Item-Dependencies predicate"), with Item-Dependencies parsing now covered in `tests/`.
    Edited test body:
    ```python
    def test_read_deps_and_set(self):
        text = textwrap.dedent(
            """
            - Date: 2026-08-24
            - Kind: child
            - Status: to-review
            - Set: "authset" (Authentication flow)
            - Order: 2
            - Dependencies: [dep001, dep002]
            - Id: a1b2c3
            """
        )
        self.assertEqual(driver._read_id(text), "a1b2c3")
        self.assertEqual(driver._read_set(text), "authset")
        self.assertEqual(driver._read_order(text), 2)
        # s4jctz / h0zk2g E-04: _read_status was dropped because neither runner host exposes it;
        # status reading is owned by selectors.read_front_matter_status and tested in tests/.
        # Legacy Dependencies: parsing was retired by 72bb113e7; Item-Dependencies parsing is covered in tests/.
    ```
    (d) Git diff stat:
    ```
    $ git diff --stat tools/ipdrunner/test_runagy.py
     tools/ipdrunner/test_runagy.py | 5 +++--
     1 file changed, 3 insertions(+), 2 deletions(-)
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: (a) pasted `ruff check agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing ZERO `Invalid # noqa directive` warnings, against the baseline of exactly two (the ``# `_read_id`'s `# noqa: F401` IS LOAD-BEARING`` prose line in each host; `oc_runipd.py:830` and `agy_runipd.py:74` at review HEAD `fe2ee961c`); (b) both rewritten comment blocks quoted in full, with a point-by-point account showing each of F-4, F-5, F-6 corrected rather than deleted, and the F-1/F-2 asymmetry recorded; (c) a re-measurement of each corrected claim pasted beside it, specifically the `as <same-name>` F401 result on both ruff versions (refuting F-4's old text) and `hasattr(oc_runipd, "_read_status")` / `hasattr(agy_runipd, "_read_status")` both `False` (refuting F-6's old text); (d) pasted full-suite `python3 -m pytest tests/ -m ''` summary before and after, with the failing node-id sets compared by name and no new failure. A comment block that merely deletes the false sentences without preserving the reasoning FAILS this item.
  - Observed evidence:
    (a) Ruff checks showing zero Invalid # noqa directive warnings:
    ```
    $ ruff check --select F401 agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    All checks passed!

    $ ~/.cache/pre-commit/repozypou4s9/py_env-python3.12/bin/ruff check --select F401 agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    All checks passed!
    ```
    (b) Both rewritten comment blocks quoted in full:
    `agent_workflows/oc_runipd.py`:
    ```python
    # `_read_id` F401 handling is re-homed onto __all__ (s4jctz / h0zk2g). Once
    # `parse_plan_file` moved to `runner_shared`, this module stopped calling `_read_id` itself.
    # Historical note (rununify 06 `sy7uwh`): `ruff --fix` previously deleted the import as unused,
    # and an earlier comment noted `as <same-name>` was not enough under the ruff of its time
    # (though modern and hook-pinned ruff v0.4.4 both recognize `as <same-name>` as an intentional export).
    # Because this module defines `__all__` containing leading-underscore names, `_read_id` is now
    # declared in `__all__`, providing an export mechanism that ruff honors without a noqa directive.
    # In contrast, `agy_runipd` has no `__all__` and retains a noqa F401 directive.
    # Consumer asymmetry: `agy_runipd._read_id` has a live caller via `tools/ipdrunner/runagy.py`
    # consumed in `tools/ipdrunner/test_runagy.py`; `oc_runipd._read_id` has no local caller, but is
    # retained for cross-host symmetry and guarded by `tests/test_runner_shared.py`.
    # (Note: `_read_status` is exposed on neither host; status reading is done via `selectors`.)
    from agent_workflows.selectors import read_front_matter_id as _read_id
    ```
    `agent_workflows/agy_runipd.py`:
    ```python
    # `_read_id` F401 suppression is retained per s4jctz / h0zk2g; see the fuller note in `oc_runipd`.
    # Once `parse_plan_file` moved to `runner_shared` this module stopped calling `_read_id` directly,
    # but `agy_runipd` lacks an `__all__` export list (unlike `oc_runipd`), so noqa F401 remains the
    # mechanism keeping the re-export alive.
    # The re-export has a live consumer: `tools/ipdrunner/runagy.py` imports and re-exports all non-dunder
    # attributes of this module, which `tools/ipdrunner/test_runagy.py` exercises. In addition, cross-host
    # parity and object identity against `selectors.read_front_matter_id` are pinned by
    # `tests/test_runner_shared.py::CrossHostReadIdReExportTests`.
    # (Historical note: tests/test_runner_refork_guard.py was deleted in 19313eed and is no longer cited
    # as a live requirement; _read_status is exposed on neither host.)
    from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - re-export for tools/ipdrunner/runagy.py (tested by tools/ipdrunner/test_runagy.py) and pinned by tests/test_runner_shared.py
    ```
    Point-by-point account:
    - F-4: Corrected the claim that `as <same-name>` was not enough; both current and pinned ruff v0.4.4 recognize `as <same-name>` as an export.
    - F-5: Corrected the claim that `__all__` is unavailable; `oc_runipd` already has `__all__` with leading-underscore names, and now includes `_read_id`.
    - F-6: Removed the false claim that `_read_status` is called locally; `_read_status` exists on neither host.
    - F-1/F-2 asymmetry: Documented that `agy` has a live caller via `tools/ipdrunner/runagy.py` exercised by `tools/ipdrunner/test_runagy.py`, while `oc` has no local caller and is retained for cross-host symmetry.
    - Literal `# noqa: F401` in prose was reworded to eliminate the ruff `Invalid # noqa directive` warning.
    (c) Re-measurement of corrected claims:
    ```
    $ echo "from agent_workflows.selectors import read_front_matter_id as read_front_matter_id" | ruff check --select F401 --stdin-filename dummy.py -
    All checks passed!

    $ echo "from agent_workflows.selectors import read_front_matter_id as read_front_matter_id" | ~/.cache/pre-commit/repozypou4s9/py_env-python3.12/bin/ruff check --select F401 --stdin-filename dummy.py -
    All checks passed!

    $ python3 -c "from agent_workflows import oc_runipd, agy_runipd; print('hasattr(oc_runipd, \"_read_status\") ->', hasattr(oc_runipd, '_read_status')); print('hasattr(agy_runipd, \"_read_status\") ->', hasattr(agy_runipd, '_read_status'))"
    hasattr(oc_runipd, "_read_status") -> False
    hasattr(agy_runipd, "_read_status") -> False
    ```
    (d) Full-suite python3 -m pytest tests/ -m '' summary before and after:
    Before edit baseline:
    ```
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    FAILED tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference
    FAILED tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership
    3 failed, 6558 passed, 2 skipped, 3 warnings in 1056.15s (0:17:36)
    ```
    After edit:
    ```
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    1 failed, 6561 passed, 2 skipped, 3 warnings in 573.32s (0:09:33)
    ```
    Node-id comparison: The single failing test is `test_corpus_verdict_neutrality_delta` (livecorpus), which was also failing at baseline. Zero new failures introduced.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract. Commit ONLY the four files named in `Scope-Paths`, through `aw commit <plan> -- <paths>`, never `git add -A` or `git commit -a`, and never push. Paste ACTUAL runner output for every V-item; do not claim a test result you did not run. Two measurement disciplines are mandatory here because this plan's own findings depend on them: FIRST, every ruff claim must be checked against BOTH the locally installed ruff and the hook-pinned `v0.4.4` from `.pre-commit-config.yaml`, since the false claim in F-4 is most likely explained by a ruff version older than either; SECOND, every temporary mutation used as a negative control (V-03) must be reverted and the revert PROVEN with `git status --short` before the next step, so no probe leaks into the commit.

This plan was authored in a shared checkout. Uncommitted changes you did not make are not yours: verify the staged set with `git diff --cached --name-only` before committing and `git restore --staged <path>` anything outside the four declared paths.

Do not mark this plan executed until `aw ipd lint --phase pre-transition` reports conforming AND all five V-items carry pasted evidence. Honesty conditions specific to this plan: do NOT report `tools/ipdrunner/test_runagy.py` as green (E-04 leaves 10 pre-existing failures there by design), do NOT report the full suite as green unless the pre-edit run was (unrelated failures pre-existed at both authoring and review, and the correct claim is "unchanged from baseline"), and do NOT describe either binding as deleted, since both are deliberately retained. On completion, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle transition and set the backlog item `s4jctz` to `graduated` only if this plan has not itself been executed; if it has, the item may close `done` (it carries no `Blocks-Release` gate, so no handoff attestation is required).
