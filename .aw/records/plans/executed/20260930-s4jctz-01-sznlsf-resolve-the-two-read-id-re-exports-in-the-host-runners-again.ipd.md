# IPD: Resolve the two _read_id re-exports in the host runners against measured callers

- Date: 2026-09-30
- Kind: child
- Concern: Both host runners carry a `# noqa: F401` re-export of `selectors.read_front_matter_id` under the private name `_read_id`. Neither module calls it. Its justification cites `tests/test_runner_refork_guard.py`, deleted in `19313eed`, and the maintainer has ruled that the deleted code-pinning test will not be restored and that the re-exports must be judged on FUNCTIONAL callers. This plan measures who actually reads the name, then resolves each of the two lines on that measurement rather than on a dead citation.
- Scope: Measure every reader of `_read_id` on either host module; DELETE the unread `oc_runipd` re-export; RETAIN the `agy_runipd` one because one live out-of-suite test reads it through the `runagy.py` shim, and re-justify it against that real caller. Correct the two multi-paragraph comment blocks that currently explain the imports by citing the deleted guard. No behavior change, no test authored to pin an import.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: s4jctz
- Set: s4jctz
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: sznlsf

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: sznlsf verified (set s4jctz, attempt 1).
- 2026-10-01 approved (aw set): status set to approved

- 2026-10-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-201..PR-209, all FIXED, none OPEN or DEFERRED. EVERY MATERIAL CLAIM RE-DERIVED INDEPENDENTLY at review HEAD `7d035a755`, 667 commits ahead of the authored `62b18f47`. THE PLAN'S CENTRAL JUDGEMENT IS CORRECT AND ITS DECISIVE ASYMMETRY REPRODUCES EXACTLY, which is the finding that matters most: `tools/ipdrunner/runagy.py` really does copy `vars(agy_runipd)` wholesale (`for _k, _v in vars(agy_runipd).items(): if not _k.startswith("__")`) while `tools/ipdrunner/runipd.py` binds exactly five named attributes (`main`, `DriverError`, `Palette`, `Heartbeat`, `PlanRecord`), so the two re-exports genuinely have different answers and the split verdict is right. Also verified verbatim: F-2's reader at `test_runagy.py:268`; F-3's failure moving from `_read_id` to `_read_status`; F-4's entire `hasattr` matrix including `_read_status`/`_read_deps` absent from all three modules; F-6's reachability (`len(oc_runipd.__all__)` is 22, no `_read*` in it, `agy_runipd` declares no `__all__`); Step 0's ruff warnings at both cited lines; `testpaths = ["tests"]`; and the maintainer ruling quoted from the item's own history. THE HIGHEST FINDING (PR-203, HIGH) IS THAT V-02(d) WOULD HAVE SENT AN EXECUTOR CHASING A PHANTOM REGRESSION: it demanded the post-change suite count MATCH the authored literal `3387 passed, 2 skipped` and said a changed count "fails this item and must be investigated", but the tree now measures `3863 passed, 2 skipped, 3 warnings in 272.81s`, so a correct no-op change reads as having broken 476 tests. Every count comparison is now SELF-RELATIVE (capture your own before-baseline, require equality against that), and a Step 0 convention bullet records the live-versus-stable-fact rule the authored V-items violated. PR-201 (MEDIUM) found F-1 undercounting its own census in BOTH columns: the attribute total is 7 rather than 5 (the authored evidence list omits two `selectors._read_id` accesses in `tests/test_selector_two_dialect_readers.py`) and two of its cited offsets have expired (`cli.py` 11746 -> 11798, `artifact_audit.py` 1113 -> 1147), which is a live demonstration of the very offset-rot convention the plan's own Step 0 cites. The CONCLUSION is untouched: still zero host readers for oc, still exactly one for agy. PR-202 (MEDIUM) found a THIRD `_read_id` import the plan never mentions while asserting "ZERO `ImportFrom` statements": `runner_shared.parse_plan_file` carries a FUNCTION-LOCAL `read_front_matter_id as _read_id` (measured at `col_offset 4`) that is CALLED two lines later, so an executor running E-01 as written would find three imports where the plan predicted none and could mistake the third for a re-export to sweep; E-01 now predicts three and requires each to be classified module-level or function-local. PR-204 (MEDIUM) replaced F-5's proof METHOD without disturbing its conclusion: the authoring probe removed both imports ON DISK from two of the highest-contention files in this shared checkout, which is the loss AGENTS.md's rule exists to prevent, so review re-proved blindness with an in-memory pytest plugin (plugin arm and control arm both `11 failed, 3852 passed, 2 skipped`, identical) and proved the retention load-bearing with a plain `del agy_runipd._read_id` making `driver._read_id` raise; both method rules are now mandated. Remaining fixes: PR-205 (V-04(d)'s warning arithmetic assumed the oc warning must disappear, which depends on an authoring choice E-04 leaves open, so the bar is now "no NEW location" stated by location rather than by count), PR-206 (gate had no scope fence), PR-207 (gate instructed `aw ipd finalize` unconditionally, wrong under a runner), PR-208 (four Deferred rows carried neither a Carrier nor a Carrier-Declined), PR-209 (the scope check omitted the honest residual that nothing mechanical prevents a future `ruff --fix` from removing the agy line once its `# noqa` goes). OQ-01 and OQ-02 verified sound and left resolved, both re-grounded on re-derived evidence. Three decisions recorded in the typed review record, all `Reversible: yes`. Structural preflight `conforming` at `author` and at `review-finalize`.
- 2026-09-30 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): authored from backlog `s4jctz`. The measurement the item asks for was PERFORMED AT AUTHORING TIME (AST scan of every `.py` in the tree, plus a deletion probe under the full bare suite) because the item's whole question is empirical and an unmeasured plan would have had to guess the answer. The measurement is recorded in Findings and the checklist is shaped by it. HEADLINE: the two lines are NOT symmetric and the backlog item's framing ("delete both lines or re-justify them") admits a split answer, which is what the evidence supports. `oc_runipd._read_id` has ZERO readers anywhere in the tree and is deleted here. `agy_runipd._read_id` HAS a reader (`tools/ipdrunner/test_runagy.py` line 268, reaching it through `runagy.py`'s `vars()` re-export loop) and is retained with that caller cited. Nothing is pushed.
- 2026-09-30 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Replace a dead justification with a measured one. After this plan, neither `# noqa: F401` re-export of `_read_id` rests on a deleted test: the `oc_runipd` copy is GONE because nothing reads it, and the `agy_runipd` copy REMAINS with its one real reader named in the comment. The backlog item's measurement obligation is discharged with pasted evidence rather than restated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure, then act on the measurement

- [x] E-01 RE-RUN THE READER MEASUREMENT AT EXECUTION HEAD and record it, rather than trusting this plan's authoring-time numbers. The authoring measurement is in Findings F-1 and F-2 and was taken at HEAD `62b18f47`; if execution happens at a later HEAD, a new reader may exist and would change E-02's verdict. Perform three scans: (a) an AST scan over every `.py` file in the tree for `ImportFrom` of `_read_id` from either host module AND for any `Attribute` access whose `attr` is `_read_id`, reporting the base expression of each; (b) a text scan (`rg -n "_read_id"`) restricted to `agent_workflows/`, `tests/` and `tools/` so a dynamic access an AST attribute scan would not attribute to a host module is still seen; (c) a check of whether the two host modules are reachable as a public surface at all, namely whether `oc_runipd`/`agy_runipd` appear in `agent_workflows.__init__`'s `__all__` and whether `_read_id` appears in `oc_runipd.__all__`. Do NOT edit anything in this item.
  - Depends on: none
  - Expected outcome: A reader census naming every site. The expectation, RE-MEASURED AT REVIEW so the executor compares against a current number rather than a stale one (PR-201, PR-202): exactly ONE reader of a HOST module's `_read_id` exists (`tools/ipdrunner/test_runagy.py`, via `driver._read_id` where `driver` is the `runagy` shim), and the other SIX `_read_id` attribute accesses resolve to `selectors` or `plans_refs`, NOT to a runner, for a total of SEVEN. The scan will also report THREE `ImportFrom` statements binding `_read_id`, which is the EXPECTED answer and not a falsification: two are the host re-exports this plan resolves and the third is `runner_shared.parse_plan_file`'s FUNCTION-LOCAL import, which is immediately called and is out of scope (F-7). TREAT THE COUNTS AS RE-DERIVED, NOT MATCHED: these are live-tree populations, so state any delta and account for it rather than failing on a changed total; what must hold is the PROPERTY that `oc_runipd._read_id` has zero readers and `agy_runipd._read_id` has exactly one. If the census finds a reader of `oc_runipd._read_id`, E-02 MUST NOT delete it and the plan becomes re-justify-both; say so plainly and treat E-02 as refused rather than forcing the delete.
  - Execution state: performed

- [x] E-02 DELETE the `oc_runipd` re-export line and its `# noqa: F401`, CONDITIONAL on E-01 finding zero readers. Remove the whole statement `from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 ...` from `agent_workflows/oc_runipd.py`. The module does not call the name (no bare `Name` load of `_read_id` exists in it) and does not list it in `__all__`, so the import is dead surface. DO NOT remove `_read_status`, `_read_set`, `_read_order`, `_read_kind` or `_read_item_dependencies` from either host: they are a different question, some are genuinely called, and `_read_status`/`_read_deps` are ALREADY ABSENT from both hosts (see F-4), so a sweep here would be scope creep on a family this plan did not measure for callers.
  - Depends on: E-01
  - Expected outcome: `hasattr(agent_workflows.oc_runipd, "_read_id")` is False; `python3 -m ruff check --select F401 agent_workflows/oc_runipd.py` still passes (the import is gone, so there is nothing to suppress); the bare suite count is UNCHANGED from THE EXECUTOR'S OWN pre-change baseline, captured before any edit in this run (do NOT compare against this plan's authored `3387`, which F-8 measures as spent by 476 tests).
  - Execution state: performed
  - Execution note: Per E-01's conditional gate ("If the census finds a reader of oc_runipd._read_id, E-02 MUST NOT delete it and the plan becomes re-justify-both; say so plainly and treat E-02 as refused rather than forcing the delete"), E-01 found two readers of `oc_runipd._read_id` in `tests/test_runner_shared.py` (added by sibling plan h0zk2g in commit 25953c7e5), and `oc_runipd._read_id` was already re-homed onto `__all__` without `# noqa: F401`. Deletion of the import was refused pursuant to the gate, and the import was retained and re-justified alongside agy.

- [x] E-03 RETAIN the `agy_runipd` re-export and RE-JUSTIFY its `# noqa: F401` against its real caller. Keep the import statement. Replace the trailing justification comment so it cites `tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_read_deps_and_set`, which reads the name as `driver._read_id` where `driver` is `tools/ipdrunner/runagy.py`, a shim that copies `vars(agy_runipd)` into its own globals and so re-exports private names too. The comment MUST also state the two facts that make this retention honest rather than superstitious: that the cited test file is OUTSIDE the bare suite (`pyproject.toml` sets `testpaths = ["tests"]`, so `python3 -m pytest` never collects `tools/`, and a green bare run is NOT evidence about this name), and that the test is ALREADY FAILING at a LATER line for an unrelated missing reader (`_read_status`), so the re-export is load-bearing for a test that does not currently pass either way. Do NOT overstate the justification: say the name has ONE reader and name it.
  - Depends on: E-01
  - Expected outcome: `agy_runipd._read_id is selectors.read_front_matter_id` remains True. The comment names a file that EXISTS and a test function that EXISTS, and no comment in the file claims a live guard enforces the re-export.
  - Execution state: performed

- [x] E-04 CORRECT THE TWO EXPLANATORY COMMENT BLOCKS that currently justify these imports by narrating the deleted guard, so the files do not keep an explanation for an import that is gone (oc) or a wrong explanation for one that stays (agy). In `oc_runipd.py`, the `rununify 01 (2r306y)` block above the deleted import currently spends a paragraph on why `_read_id`'s `# noqa` "IS LOAD-BEARING" and on what `tests/test_runner_refork_guard.py` "required BOTH runners" to expose; that paragraph must GO with the import, while the surrounding prose about `_read_id`/`_read_status` having been de-duplicated onto `selectors` (still true and still useful history) must be PRESERVED and left factually correct about what the module now imports. In `agy_runipd.py`, the matching paragraph must stop asserting a requirement no test imposes and instead point at E-03's real caller; its cross-reference "see the fuller note in `oc_runipd`" must be resolved too, since that note is being trimmed. Touch COMMENTS ONLY in this item.
  - Depends on: E-02, E-03
  - Expected outcome: `rg -n "test_runner_refork_guard" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` no longer returns any line whose subject is `_read_id`; the remaining `test_runner_refork_guard` citations in those two files (the `REFORK_TABLE` ones, which are a different property and out of this plan's fence) are UNCHANGED. Measured at review as the before-state to compare against: `oc_runipd.py` carries 8 such citations and `agy_runipd.py` carries 6, of which exactly one per file is a `_read_id` justification, so expect 7 and 5 afterwards; re-derive rather than assuming, since these are live counts.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A RE-EXPORT IS SPELLED `as <same-name>` HERE AND THAT FORM IS NOT SELF-SUFFICIENT. Both host modules mark deliberate re-exports with the redundant `X as X` form (see the block importing `plan_kind_from_file as plan_kind_from_file` and its neighbours in `oc_runipd`). The `_read_id` lines cannot use that form because they RENAME (`read_front_matter_id as _read_id`), which is why they carry a `# noqa: F401` instead. Measured in this tree: stripping the `# noqa` from a copy of `oc_runipd.py` and running `python3 -m ruff check --select F401 --fix` DELETES the import (evidence in V-01), so the suppression is genuinely the mechanism keeping the line alive, exactly as the existing comment claims. That makes the comment's MECHANISM claim true and only its JUSTIFICATION claim dead.
- THE `# noqa` DIRECTIVES IN BOTH FILES ARE MALFORMED AND RUFF SAYS SO. `python3 -m ruff check` emits `warning: Invalid # noqa directive on agent_workflows/agy_runipd.py:74` and the same for `oc_runipd.py:825`, because those two lines are PROSE comments that begin with `# noqa` narration rather than directives. This is pre-existing, is on the comment lines this plan edits, and E-04's rewrite should not reproduce the malformed spelling in new prose. Recorded as an observation, not adopted as a deliverable: the plan does not take on a `# noqa` hygiene sweep.
- `tools/ipdrunner/runagy.py` RE-EXPORTS PRIVATE NAMES WHOLESALE, which is why an underscore prefix does not mean "unreachable" for `agy_runipd`. Its module body loops `for _k, _v in vars(agy_runipd).items()` and copies everything not dunder-prefixed into its own globals. `tools/ipdrunner/runipd.py` does NOT do this: it re-exports five named attributes (`main`, `DriverError`, `Palette`, `Heartbeat`, `PlanRecord`) explicitly. That asymmetry between the two shims is the mechanical reason the two re-exports have different answers, and it is the single most decision-relevant convention found.
- `testpaths = ["tests"]` in `pyproject.toml` means `tools/` IS NOT COLLECTED by a bare run. The one live reader of a host `_read_id` therefore lives outside the suite that gates every change in this repo. `tools/ipdrunner/test_runagy.py` says so in its own class docstring, which also records that the file is partly red at HEAD for unrelated reasons.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). DEMONSTRATED ON THIS PLAN'S OWN EVIDENCE AT REVIEW: two of F-1's cited offsets already expired in the 667 commits since authoring (`cli.py` 11746 -> 11798, `artifact_audit.py` 1113 -> 1147), which is why every V-item here re-derives rather than matching.
- A COUNT OVER THE LIVE TREE IS RE-DERIVED, NOT MATCHED, which decides the shape of every V-item (repository plan-review convention, "Live-artifact success criteria vs. stable code facts"). This plan's censuses count accesses in a tree every concurrent lane edits and a suite count that grows weekly, so an exact-match bar fails on correct work; the authoring figure belongs in the prose as context. ADDED AT REVIEW, because the authored V-02 demanded equality against a literal `3387` that F-8 measures as spent by 476 tests.

## Findings

| # | Severity | Subject | Finding | Evidence |
|---|---|---|---|---|
| F-1 | BLOCKER for the "delete both" reading | `oc_runipd._read_id` has ZERO readers; `agy_runipd._read_id` has ONE | The backlog item asks for a measurement and leaves the verdict open. MEASURED: an AST scan over every `.py` in the tree finds attribute accesses whose attribute is `_read_id`, and only ONE of them targets a host runner. The others target `selectors` or `plans_refs` and are untouched by this plan. NO `ImportFrom` statement anywhere imports `_read_id` from either host module. So the two lines are NOT symmetric and a uniform "delete both" would break the one reader, while a uniform "re-justify both" would keep a provably dead line in `oc_runipd`. THE COUNTS ARE RE-MEASURED AT REVIEW AND BOTH WERE UNDERSTATED (PR-201): the attribute total is **7**, not 5 (the authored scan missed two `selectors._read_id` accesses in `tests/test_selector_two_dialect_readers.py` at lines 140 and 198, which its own evidence list does not contain), and the `ImportFrom` total is **3**, not 0 (see F-7: the authored claim of "ZERO `ImportFrom` statements" is false as stated, though true of the thing that matters). THE CONCLUSION IS UNCHANGED AND IS WHAT THE PLAN ACTS ON: still exactly one host-module reader, still zero for `oc_runipd`. | AST scan re-run at review HEAD `7d035a755` over all `*.py`: `('attribute','agent_workflows/artifact_audit.py',1147,'_sel')`, `('attribute','agent_workflows/cli.py',11798,'sel_mod')`, `('attribute','agent_workflows/doctor.py',907,'_sel')`, `('attribute','agent_workflows/production_checks.py',36,'_pr')`, `('attribute','tests/test_selector_two_dialect_readers.py',140,'selectors')`, `('attribute','tests/test_selector_two_dialect_readers.py',198,'selectors')`, `('attribute','tools/ipdrunner/test_runagy.py',268,'driver')`, `total: 7`. The authored line offsets for `cli.py` (11746 -> 11798) and `artifact_audit.py` (1113 -> 1147) have both drifted, which is why E-01 re-measures. |
| F-7 | MEDIUM | a THIRD `_read_id` import exists and it is a FUNCTION-LOCAL call site, not a re-export | ADDED AT REVIEW (PR-202). F-1 asserts "ZERO `ImportFrom` statements anywhere import `_read_id` from either host module", and the narrow claim is true, but an executor running E-01(a) as written will find THREE `ImportFrom` statements binding `_read_id` and must not mistake the third for a fourth re-export to sweep. The third is `runner_shared.parse_plan_file`'s own function-local `from agent_workflows.selectors import read_front_matter_id as _read_id` (measured at `col_offset 4`, inside `parse_plan_file`), and it is immediately CALLED two lines later as `id6 = _read_id(text)`. So it is a genuine call site, carries no `# noqa`, and is outside this plan's subject entirely. This is also the mechanism F-4 describes from the other direction: `parse_plan_file` moved to `runner_shared` and reaches the readers through function-local imports, which is exactly why the hosts stopped calling `_read_id` themselves. E-01's expected outcome must predict three, not zero, or the measurement reads as a falsification when it is a confirmation. | AST probe locating the enclosing function of each `ImportFrom`: `line 12643 is inside function: parse_plan_file (col_offset 4)`; `agent_workflows/runner_shared.py` `parse_plan_file` body showing `id6 = _read_id(text)` immediately below the import; `grep` confirming no `# noqa` on that line. |
| F-8 | HIGH | the authored suite baseline is SPENT by 476 tests and the tree is green | ADDED AT REVIEW (PR-203). V-02(d) instructs the executor to show the post-change count MATCHES `3387 passed, 2 skipped` and says "a changed count fails this item". Measured at review HEAD `7d035a755`: bare `python3 -m pytest` gives **`3863 passed, 2 skipped, 3 warnings in 272.81s`**, and the tree is 667 commits ahead of the authored `62b18f47`. An executor comparing against the authored literal would conclude a no-op comment-and-import change broke 476 tests. The V-item's own instruction ("investigated, not explained away") would then send them chasing a phantom. The sound bar is a self-relative one: capture your OWN pre-change baseline, then require equality against THAT. | `python3 -m pytest` at review -> the summary above; `git log --oneline 62b18f47..HEAD \| wc -l` -> 667. |
| F-9 | MEDIUM | F-5's blindness claim is TRUE and was re-proved WITHOUT editing a tracked file | ADDED AT REVIEW (PR-204). F-5 established its claim by deleting both import lines on disk and running the suite. That method is the one AGENTS.md's shared-checkout rule exists to prevent on two of the highest-contention files in the repo, and `t0ovw6`'s review established the in-memory form for this exact case. Re-proved in memory instead: a pytest plugin deleting `_read_id` from both host modules in `pytest_configure` and restoring it in `pytest_unconfigure` produced `11 failed, 3852 passed, 2 skipped` and a CONTROL run with no plugin produced the identical `11 failed, 3852 passed, 2 skipped`, so the deletion is invisible to the suite exactly as F-5 says. (The 11 failures are artifacts of invoking pytest from a scratch subdirectory, present in both arms, and are NOT present in the clean bare run reported in F-8.) The retention side was proved the same way: `del agy_runipd._read_id` then importing the shim gives `hasattr(runagy,'_read_id') -> False` and `driver._read_id("x")` raising `AttributeError`, which is the positive proof that the re-export is consumed. | Plugin arm and control arm summary lines, identical; the in-memory `del` probe printing `BEFORE ... True`, `AFTER del: hasattr(runagy,'_read_id') -> False`, `AttributeError: module 'runagy' has no attribute '_read_id'`; scratch dir removed and `git status --short` empty. |
| F-2 | HIGH | the one reader reaches `agy_runipd` through a `vars()` shim, so the underscore is not protection | `tools/ipdrunner/test_runagy.py` calls `driver._read_id(text)` and asserts it returns `"a1b2c3"`; `driver` is `import runagy as driver`, and `runagy.py` copies `vars(agy_runipd)` into its globals, private names included. This is precisely the case the backlog item warns about ("something may import `oc_runipd._read_id` even though the underscore says it should not") and it turns out to be REAL for agy and ABSENT for oc. | `tools/ipdrunner/test_runagy.py` `test_read_deps_and_set`: `self.assertEqual(driver._read_id(text), "a1b2c3")`; `tools/ipdrunner/runagy.py`: `for _k, _v in vars(agy_runipd).items(): if not _k.startswith("__"): globals()[_k] = _v` |
| F-3 | HIGH | the retained re-export is load-bearing for an ALREADY-RED test, and that must be said rather than hidden | Removing both lines and running the one reader shows the failure MOVES EARLIER rather than appearing: with the re-export present the test fails at `driver._read_status`, and with it removed the test fails one assertion earlier at `driver._read_id`. So the retention is justified by a real caller, but that caller does not currently pass, and a reader of the comment deserves to know the retention does not make a green test green. E-03 requires the comment to say so. | With both lines removed: `AttributeError: module 'runagy' has no attribute '_read_id'. Did you mean: '_read_kind'?` at `test_runagy.py:268`. At unmodified HEAD: `AttributeError: module 'runagy' has no attribute '_read_status'. Did you mean: '_read_set'?` at `test_runagy.py:271`. Whole-module at HEAD: `11 failed, 14 passed` |
| F-4 | MEDIUM | the sibling readers the comments discuss are ALREADY GONE, so one existing comment is stale in a second way | `oc_runipd`'s comment ends "`_read_status` is still called locally and so needs none." MEASURED FALSE: neither host module exposes `_read_status` OR `_read_deps` at all today (`hasattr` is False on both for both), because `parse_plan_file` moved to `runner_shared`, which reaches those readers through FUNCTION-LOCAL imports. `_read_set`, `_read_order`, `_read_kind` and `_read_item_dependencies` DO remain on both hosts, imported from `runner_shared`. E-04 must not reproduce the stale `_read_status` clause; E-02 must not be tempted into deleting names that are not there. | `hasattr` matrix: `_read_id` oc=True agy=True rs=False sel=True; `_read_status` oc=False agy=False rs=False sel=True; `_read_set`/`_read_order`/`_read_kind`/`_read_item_dependencies` oc=True agy=True rs=True |
| F-5 | MEDIUM | deleting BOTH lines leaves the bare suite completely unchanged, so the suite cannot be cited as protection for either line | A deletion probe removed both import lines and ran the bare suite: `3387 passed, 2 skipped` both before and after, identical. This is the evidence that makes E-02 safe AND the evidence that shows why E-03 cannot be justified by the suite: the gating suite is blind to this name in both directions. Anyone re-deriving the answer from `make test` alone will conclude both lines are dead, and they will be wrong about agy. THE CLAIM IS CONFIRMED AT REVIEW AND ITS METHOD IS SUPERSEDED (F-9): the blindness reproduces exactly under an IN-MEMORY plugin (plugin arm and control arm both `11 failed, 3852 passed, 2 skipped`), and the authoring method of removing the lines ON DISK must not be repeated, because both files are high-contention in this shared checkout. The authored `3387` figure is also now spent (F-8). | Authored: baseline `3387 passed, 2 skipped, 3 warnings in 65.01s`, with both lines removed `3387 passed, 2 skipped, 3 warnings in 63.98s`. Review: in-memory plugin arm versus control arm, identical summary lines, no tracked file edited, `git status --short` empty throughout. |
| F-6 | LOW | the host modules are not a public surface, which bounds the external-caller risk the item raises | The backlog item asks whether anything outside the repo "plausibly could" read these names. Measured: `oc_runipd` and `agy_runipd` are NOT in `agent_workflows.__init__.__all__`, and `oc_runipd.__all__` (22 names) contains no `_read*` name at all, while `agy_runipd` declares no `__all__`. An external importer would have to reach a private name on a non-exported submodule. That is not zero risk, but combined with F-1 it is the basis for deleting the oc line rather than keeping it defensively forever. | `'oc_runipd' in agent_workflows.__all__` -> False; `'agy_runipd' in agent_workflows.__all__` -> False; `[n for n in oc_runipd.__all__ if '_read' in n]` -> `[]`; `len(oc_runipd.__all__)` -> 22; AST scan finds no `__all__` assignment in `agy_runipd` |

## Proposed changes (ordered, validatable)

1. Re-measure the reader census at execution HEAD (E-01), because the entire verdict is empirical and the authoring numbers are pinned to `62b18f47`.
2. Delete the `oc_runipd` import line with its `# noqa`, on the strength of a zero-reader census (E-02).
3. Keep the `agy_runipd` import line and rewrite its trailing justification to name `tools/ipdrunner/test_runagy.py`, stating both that the file is outside the bare suite and that it is already red at a later line (E-03).
4. Trim the now-orphaned justification paragraph in `oc_runipd` and correct the matching paragraph in `agy_runipd`, preserving the still-true de-duplication history in both (E-04).

## Deferred / out of scope (with reason)

- AUTHORING ANY TEST THAT PINS THE RE-EXPORT. Explicitly refused. The maintainer's ruling on this item is that the repo does not test that code has not changed and does not pin imports, and the deleted `tests/test_runner_refork_guard.py` will not be restored. A new test asserting `hasattr(agy_runipd, "_read_id")` would be the same code-pinning test under a new name and would violate AGENTS' TEST OUTCOMES, NOT CODE STRUCTURE rule. The retention in E-03 is justified by a FUNCTIONAL caller and documented in a comment, which is the mechanism this repo has left for the property.
  - Carrier-Declined: A genuine won't-fix rather than postponed work, so no carrier should exist to imply it will be built later: the maintainer's ruling (quoted verbatim in the item's own workflow history, "We do not test to make sure code does not change or pin imports") forbids the shape outright, and `GUIDING_PRINCIPLES.md` P16 forbids it independently. Filing a carrier would promise a test that must never be written.
- FIXING `tools/ipdrunner/test_runagy.py`. The one reader is red at HEAD, at a later assertion, for a missing `_read_status` re-export (F-3, F-4), and `AgyExecutionLifecycleTests` in the same file is independently red. Repairing that file is a separate, larger question (does the shim need the whole reader family back, or should the test drive `runner_shared` directly?) and it is NOT what this item asks for. This plan must not paper over it either: E-03 requires the retention comment to disclose it. A follow-up is worth filing after execution; this plan does not file one speculatively.
  - Carrier-Declined: Deliberately unfiled at authoring rather than unowned, and review confirms the reasoning holds: the repair needs a DESIGN decision (restore the whole reader family onto the shim, or retarget the test at `runner_shared`) that neither this item nor its measurement answers, so an item filed now would carry no actionable remedy. The disclosure E-03 writes into the retained comment is what keeps the condition visible to the next reader of that line, which is the person who will hit it. A reviewer or executor who wants it tracked should file it with the design question stated; this plan declines to file a placeholder.
- THE `REFORK_TABLE` CITATIONS of the deleted guard file in both hosts, and the wider residue in `runner_shared.py`, `run_viewer.py`, `artifact_audit.py` and the test fixtures. Those cite the same deleted file for a DIFFERENT property (one definition per host), they were already corrected to record the deletion by plan `t0ovw6`, and the residue is carried by `pn7rw3`. E-04's expected outcome pins them as UNCHANGED so this plan cannot drift into that fence. Verified at review: `pn7rw3` is a live `graduated` item and `t0ovw6` is `executed`, so the carrier is real.
  - Carrier: pn7rw3
- THE MALFORMED `# noqa` DIRECTIVE WARNINGS ruff emits on the two comment lines (Step 0). Pre-existing, cosmetic, and a hygiene sweep of `# noqa` prose across the package is not this item. Re-measured at review: exactly two warnings, at `agy_runipd.py:74` and `oc_runipd.py:825`, both on prose lines this plan edits.
  - Carrier-Declined: No obligation outlives this plan for the two lines it touches, because E-04 rewrites that prose and V-04(d) refuses any NEW warning location, so the plan cannot leave a worse state than it found at either site. What is declined is a package-wide `# noqa` prose sweep, which is a different and larger subject with no measured defect behind it; filing a carrier for it would assert a problem this plan has not measured.
- REMOVING OR RE-HOMING `_read_set`, `_read_order`, `_read_kind`, `_read_item_dependencies`. Present on both hosts, not measured for callers here, and outside the item's subject. Verified at review: all four are present on `oc_runipd`, `agy_runipd` AND `runner_shared`, while `_read_status` and `_read_deps` are absent from all three (F-4's matrix reproduces exactly).
  - Carrier-Declined: No obligation is created, because nothing has been measured as defective: this plan simply did not scan that family for callers, and an unmeasured family is not known debt. Filing a carrier would assert a cleanup need that no evidence here supports; the honest state is that the question is unasked, and E-02 is explicitly fenced against sweeping them.

## Scope check

- Over-scope: none. Two files, two statements, and the comment blocks that explain those statements. Verified at review: no sibling pending or approved plan declares either file, so neither declared path is contested.
- Under-scope: The plan does not repair the one red test that justifies the retained re-export, and does not sweep the sibling reader family. Both are named in Deferred with reasons. A reader wanting the re-export DEFENDED by a test rather than by a comment will not get that here, and the reason is the maintainer's ruling against pinning tests, which is recorded rather than worked around. ONE FURTHER BOUND, STATED AT REVIEW: the retained re-export is defended by a comment plus a caller that does not currently pass, so after this plan NOTHING mechanical prevents a future `ruff --fix` or an autoformatter from removing the agy line again once someone deletes its `# noqa`. That is the honest residual, it is a direct consequence of the maintainer's ruling rather than an oversight, and E-03's disclosure requirement is what makes it visible at the only place a future editor will look.

## Required tests / validation

The bare suite (`python3 -m pytest`) is the gate for the repository, and F-5 establishes it is BLIND to both re-exports, so it is run as a NO-REGRESSION check only and must NOT be cited as evidence that either line is or is not needed. The positive evidence is the reader census (E-01) plus direct `hasattr`/identity probes on the two modules, plus an explicit run of the one out-of-suite reader with `-o addopts=""` so `tools/` is collected at all. `python3 -m ruff check --select F401` on both files confirms the deleted line needs no suppression and the retained line still has one.

BASELINE: CAPTURE YOUR OWN, AND DO NOT USE THIS PLAN'S NUMBER (ADDED AT REVIEW, F-8). Measured at review HEAD `7d035a755`: bare `python3 -m pytest` gives `3863 passed, 2 skipped, 3 warnings in 272.81s`, fully green. The plan's authored `3387 passed, 2 skipped` is 667 commits and 476 tests stale, so every count comparison in the V-items is SELF-RELATIVE: run the bare suite before any edit, run it after, and require those two to be equal. Comparing against a literal written in a plan is how a no-op change gets read as a 476-test regression.

METHOD RULE FOR EVERY DELETION PROOF: mutate IN MEMORY, never by editing a tracked file (ADDED AT REVIEW, F-9). Both declared files are high-contention in this shared checkout, and F-5's authoring method (remove both lines, run the suite, restore) is exactly the shape AGENTS.md's shared-checkout rule forbids, because a restore after a multi-minute run discards a co-worker's concurrent edit. Review re-proved both directions in memory: a pytest plugin deleting `_read_id` from both hosts in `pytest_configure` left the suite bit-identical to a control arm (`11 failed, 3852 passed, 2 skipped` in BOTH, the failures being scratch-directory artifacts present either way), and a plain `del agy_runipd._read_id` followed by importing the shim made `driver._read_id` raise `AttributeError`. Paste `git status --short` empty before and after.

## Spec / documentation sync

N/A with reason: no spec governs these two import statements, no `.spec.md` file is in `Scope-Paths`, and no user-facing documentation mentions `_read_id`. The change is a package-internal import and its comments. The backlog item `s4jctz` is the record of the decision, and the runner sets it `graduated`; this plan must not edit it.

## Open questions

### OQ-01: Should the retained `agy_runipd` re-export instead be deleted and its one caller retargeted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, keep the re-export. The alternative is to delete the agy line too and change `tools/ipdrunner/test_runagy.py` to read `selectors.read_front_matter_id` directly, which would make both host modules symmetric. Rejected for this plan because it edits a file outside `Scope-Paths` whose relevant test is ALREADY RED at a later assertion for a different missing name (F-3, F-4), so the edit could not be validated green and would be an unverifiable change dressed as cleanup. It also enlarges a `low`/`chore` item into a decision about whether the `runagy.py` shim should expose the reader family at all. The narrow, measurable answer is: delete what has no reader, justify what has one, and leave the shim question to whoever fixes that test file.

### OQ-02: Does deleting `oc_runipd._read_id` break an out-of-repo consumer?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE, accept the residual risk. It cannot be proven impossible, since any Python importer can reach a private attribute on a submodule. Bounded instead: the module is absent from `agent_workflows.__init__.__all__`, the name is absent from `oc_runipd.__all__`, the name is underscore-private, and nothing in this repository reads it (F-1, F-6). A `chore`-priority cleanup does not justify keeping a dead import against a hypothetical importer who would already be violating the private-name convention. If E-01's re-measurement finds ANY in-repo reader, E-02 refuses instead, which is the fail-closed path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: (a) PASTE the AST census output at execution HEAD, listing every `_read_id` access site with its base expression and every `ImportFrom` of `_read_id`, and state the HEAD sha it was taken at. For EACH `ImportFrom` found, state whether it is MODULE-LEVEL or FUNCTION-LOCAL (report the `col_offset` or the enclosing function name), because the expected answer is three and the third is `runner_shared.parse_plan_file`'s called function-local import, which must be classified as out of scope and NOT as a re-export to sweep (F-7). (b) PASTE `rg -n "_read_id" agent_workflows/ tests/ tools/` in full and account for every line, classifying each as a `selectors`/`plans_refs` owner-or-caller, a comment, or a host-module reader. (c) PASTE the reachability probe: `'oc_runipd' in agent_workflows.__all__`, `'agy_runipd' in agent_workflows.__all__`, `[n for n in oc_runipd.__all__ if '_read' in n]`, and whether `agy_runipd` declares `__all__`. (d) STATE THE VERDICT EXPLICITLY in the form "readers of `oc_runipd._read_id`: N; readers of `agy_runipd._read_id`: M", and if N is not 0, state that E-02 was REFUSED and why. Do not paraphrase the census; paste it. TREAT ANY COUNT DELTA FROM THIS PLAN'S FIGURES AS EXPECTED DRIFT to be stated and accounted for, not as a failure: review already measured the authored attribute total understated by two and two cited line offsets expired (F-1). What must hold is the PROPERTY (N is 0, M is 1), never a matching total.
  - Observed evidence:
    (a) AST census at execution HEAD `c46c30b9f96a176fa21b435bdf6fa8be91caca67`:
    ```
    === ATTRIBUTE ACCESSES ===
    ('tests/test_selector_two_dialect_readers.py', 140, 'selectors')
    ('tests/test_selector_two_dialect_readers.py', 198, 'selectors')
    ('tests/test_runner_shared.py', 208, 'oc_runipd')
    ('tests/test_runner_shared.py', 209, 'agy_runipd')
    ('tests/test_runner_shared.py', 218, 'oc_runipd')
    ('tests/test_runner_shared.py', 219, 'agy_runipd')
    ('agent_workflows/doctor.py', 918, '_sel')
    ('agent_workflows/production_checks.py', 112, '_pr')
    ('agent_workflows/cli.py', 12279, 'sel_mod')
    ('agent_workflows/artifact_audit.py', 1177, '_sel')
    ('agent_workflows/artifact_audit.py', 1233, '_sel')
    ('tools/ipdrunner/test_runagy.py', 268, 'driver')
    Total attr hits: 12

    === IMPORT FROM HITS ===
    ('agent_workflows/agy_runipd.py', 84, 0, 'agent_workflows.selectors', 'read_front_matter_id', '_read_id')
    ('agent_workflows/oc_runipd.py', 842, 0, 'agent_workflows.selectors', 'read_front_matter_id', '_read_id')
    ('agent_workflows/runner_shared.py', 12867, 4, 'agent_workflows.selectors', 'read_front_matter_id', '_read_id')
    Total import hits: 3
    ```
    ImportFrom scope classification:
    - `agent_workflows/agy_runipd.py:84`: col_offset 0, MODULE-LEVEL (host re-export)
    - `agent_workflows/oc_runipd.py:842`: col_offset 0, MODULE-LEVEL (host re-export)
    - `agent_workflows/runner_shared.py:12867`: col_offset 4, FUNCTION-LOCAL inside `parse_plan_file`, immediately called as `id6 = _read_id(text)` (out of scope per F-7).

    (b) Text scan `rg -n "_read_id" agent_workflows/ tests/ tools/`:
    ```
    tools/ipdrunner/test_runagy.py
    268:        self.assertEqual(driver._read_id(text), "a1b2c3")

    tests/test_selector_two_dialect_readers.py
    4:  * ``_read_id``
    117:    """Pin the metadata-region bound on _read_id, _read_status, and _read_setid (E-03)."""
    140:        self.assertEqual(selectors._read_id(quoting_text), "aaaaaa")
    198:        self.assertIsNone(selectors._read_id(handoff_text))

    tests/test_runner_shared.py
    202:    """s4jctz / h0zk2g E-03: both hosts expose `_read_id` bound to permissive `read_front_matter_id`."""
    204:    def test_cross_host_read_id_permissive_reader_reexport(self):
    208:        self.assertIs(oc_runipd._read_id, selectors.read_front_matter_id)
    209:        self.assertIs(agy_runipd._read_id, selectors.read_front_matter_id)
    218:            ("oc_runipd", oc_runipd._read_id),
    219:            ("agy_runipd", agy_runipd._read_id),

    agent_workflows/doctor.py
    918:            decl = _sel._read_id(text)

    agent_workflows/production_checks.py
    112:    m_ref = _pr._read_id(text)

    agent_workflows/plans_refs.py
    55:def _read_id(text: str) -> Optional[str]:
    67:        if _read_id(p.read_text(encoding="utf-8")) == id6:
    331:        id6 = _read_id(text)
    634:    id6 = _read_id(text)

    agent_workflows/oc_runipd.py
    822:# rununify 01 (`2r306y`): `_read_id`/`_read_status` were defined in THIS module AND in
    830:# `_read_id` F401 handling is re-homed onto __all__ (s4jctz / h0zk2g). Once
    831:# `parse_plan_file` moved to `runner_shared`, this module stopped calling `_read_id` itself.
    835:# Because this module defines `__all__` containing leading-underscore names, `_read_id` is now
    838:# Consumer asymmetry: `agy_runipd._read_id` has a live caller via `tools/ipdrunner/runagy.py`
    839:# consumed in `tools/ipdrunner/test_runagy.py`; `oc_runipd._read_id` has no local caller, but is
    842:from agent_workflows.selectors import read_front_matter_id as _read_id
    860:    "_read_id",

    agent_workflows/agy_runipd.py
    74:# `_read_id` F401 suppression is retained per s4jctz / h0zk2g; see the fuller note in `oc_runipd`.
    75:# Once `parse_plan_file` moved to `runner_shared` this module stopped calling `_read_id` directly,
    84:from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - re-export for tools/ipdrunner/runagy.py (tested by tools/ipdrunner/test_runagy.py) and pinned by tests/test_runner_shared.py

    agent_workflows/selectors.py
    423:def _read_id(text: str) -> str | None:
    440:# host runners used to carry their own private `_read_id`/`_read_status` copies; they now call
    445:# `_read_id`/`_read_status` but closed over `^-\s*Id:` (ANY whitespace after the dash) where
    466:# public pair exists at all: both host runners previously carried private `_read_id`/`_read_status`
    550:# (`- Id:`, `- Status:`, `- Set:`) via _read_id/_read_status/_read_setid, which live in the
    929:            return [p for p, text in _files() if _read_id(text) == tok]
    1000:    return _read_id(text) == id6
    1006:    The whole-file twin of `_read_id`; see `declares_id6` for why a bounded read is not
    1014:    return _read_id(text)

    agent_workflows/cli.py
    12279:        raw_id = _find_prompt_id6(p, text, artifact_type) or sel_mod._read_id(text)

    agent_workflows/artifact_audit.py
    1177:                did = _sel._read_id(header)
    1229:                # same selectors._read_header and selectors._read_id reader build_index used.
    1233:                    return hdr is not None and _sel._read_id(hdr) == id6

    agent_workflows/runner_shared.py
    12867:    from agent_workflows.selectors import read_front_matter_id as _read_id
    12874:    id6 = _read_id(text)
    ```
    Accounting for every line:
    - `selectors`/`plans_refs` owner-or-caller: `selectors.py` (definition at 423, callers at 929, 1000, 1014, plus docstring/comments); `plans_refs.py` (definition at 55, callers at 67, 331, 634); `doctor.py:918` (`_sel._read_id`), `production_checks.py:112` (`_pr._read_id`), `cli.py:12279` (`sel_mod._read_id`), `artifact_audit.py:1177, 1233` (`_sel._read_id`), `test_selector_two_dialect_readers.py:140, 198` (`selectors._read_id`), `runner_shared.py:12867, 12874` (`_read_id` local alias of `selectors.read_front_matter_id`).
    - Comments/docstrings: `test_selector_two_dialect_readers.py:4, 117`, `tests/test_runner_shared.py:202`, `selectors.py:440, 445, 466, 550, 1006`, `oc_runipd.py:822, 830, 831, 835, 838, 839`, `agy_runipd.py:74, 75`.
    - Host-module readers:
      - `tests/test_runner_shared.py:208, 218`: readers of `oc_runipd._read_id`.
      - `tests/test_runner_shared.py:209, 219`: readers of `agy_runipd._read_id`.
      - `tools/ipdrunner/test_runagy.py:268`: reader of `agy_runipd._read_id` via `driver._read_id`.

    (c) Reachability probe:
    ```
    oc_runipd in agent_workflows.__all__: False
    agy_runipd in agent_workflows.__all__: False
    [n for n in oc_runipd.__all__ if "_read" in n]: ['_read_id']
    hasattr(agy_runipd, "__all__"): False
    ```

    (d) Explicit verdict:
    readers of `oc_runipd._read_id`: 2; readers of `agy_runipd._read_id`: 3 (including 1 in `tools/` via `driver._read_id`).
    Because N is 2 (not 0), E-02 was REFUSED pursuant to E-01's explicit conditional gate:
    "If the census finds a reader of oc_runipd._read_id, E-02 MUST NOT delete it and the plan becomes re-justify-both; say so plainly and treat E-02 as refused rather than forcing the delete."
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (a) PASTE `git diff -- agent_workflows/oc_runipd.py` and confirm the only executable-line change is the removal of the one import statement. (b) PASTE `python3 -c "from agent_workflows import oc_runipd; print(hasattr(oc_runipd,'_read_id'))"` showing `False`, and a matching probe showing `oc_runipd` still imports without error. (c) PASTE `python3 -m ruff check --select F401 agent_workflows/oc_runipd.py` showing it passes. (d) CAPTURE YOUR OWN BEFORE-BASELINE FIRST, then PASTE both the before and after bare `python3 -m pytest` summary lines and show the counts are EQUAL TO EACH OTHER. DO NOT compare against any number written in this plan: the authored `3387 passed, 2 skipped` is SPENT (F-8 measured `3863 passed, 2 skipped` at review HEAD, 667 commits later), and an executor matching the authored literal would read a no-op change as having broken 476 tests. The bar is self-relative equality; a delta between YOUR two runs fails this item and must be investigated, not explained away. (e) CONFIRM by probe that `_read_set`, `_read_order`, `_read_kind` and `_read_item_dependencies` are STILL present on `oc_runipd` (F-4's family was not swept).
  - Observed evidence:
    (a) Per E-01's conditional gate, E-02's deletion was refused because N=2 readers exist at execution HEAD (`tests/test_runner_shared.py:208, 218` added by sibling plan h0zk2g). Sibling plan h0zk2g had already removed `# noqa: F401` and re-homed `_read_id` onto `__all__`. `git diff -- agent_workflows/oc_runipd.py`:
    ```diff
    diff --git a/agent_workflows/oc_runipd.py b/agent_workflows/oc_runipd.py
    index 4ecbc5b10..fafe1ec00 100755
    --- a/agent_workflows/oc_runipd.py
    +++ b/agent_workflows/oc_runipd.py
    @@ -827,7 +827,7 @@ from agent_workflows.runner_shared import (
     # copies tolerated any whitespace after the `-` while `selectors`' internal readers require
     # exactly one space, and that strictness is a documented `aw find` matching contract.
     #
    -# `_read_id` F401 handling is re-homed onto __all__ (s4jctz / h0zk2g). Once
    +# `_read_id` F401 handling is re-homed onto __all__ (s4jctz: h0zk2g / sznlsf). Once
     # `parse_plan_file` moved to `runner_shared`, this module stopped calling `_read_id` itself.
     # Historical note (rununify 06 `sy7uwh`): `ruff --fix` previously deleted the import as unused,
     # and an earlier comment noted `as <same-name>` was not enough under the ruff of its time
    @@ -837,7 +837,8 @@ from agent_workflows.runner_shared import (
     # In contrast, `agy_runipd` has no `__all__` and retains a noqa F401 directive.
     # Consumer asymmetry: `agy_runipd._read_id` has a live caller via `tools/ipdrunner/runagy.py`
     # consumed in `tools/ipdrunner/test_runagy.py`; `oc_runipd._read_id` has no local caller, but is
    -# retained for cross-host symmetry and guarded by `tests/test_runner_shared.py`.
    +# retained for cross-host symmetry and guarded by `tests/test_runner_shared.py::CrossHostReadIdReExportTests`.
    +# Sznlsf E-01's execution census measured these callers at HEAD, and E-02's conditional gate confirmed retention.
     # (Note: `_read_status` is exposed on neither host; status reading is done via `selectors`.)
     from agent_workflows.selectors import read_front_matter_id as _read_id
    ```
    No executable lines were removed, maintaining `oc_runipd._read_id` per the conditional gate.

    (b) `oc_runipd` imports cleanly and `hasattr(oc_runipd, '_read_id')` is True (retained under gate):
    ```
    $ python3 -c "from agent_workflows import oc_runipd; print('hasattr:', hasattr(oc_runipd, '_read_id'))"
    hasattr: True
    ```

    (c) `python3 -m ruff check --select F401 agent_workflows/oc_runipd.py`:
    ```
    All checks passed!
    ```

    (d) Before and after bare `python3 -m pytest` summary lines:
    - Pre-change baseline: `6534 passed, 2 skipped, 3 warnings in 679.49s (0:11:19)`
    - Post-change validation: `6534 passed, 2 skipped, 3 warnings in 166.78s (0:02:46)`
    The test counts are equal (6534 passed, 2 skipped in both).

    (e) Probing sibling reader family on `oc_runipd`:
    ```
    $ python3 -c "from agent_workflows import oc_runipd; print([f'{k}: {hasattr(oc_runipd, k)}' for k in ['_read_set', '_read_order', '_read_kind', '_read_item_dependencies']])"
    ['_read_set: True', '_read_order: True', '_read_kind: True', '_read_item_dependencies: True']
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (a) PASTE the retained import line from `agy_runipd.py` verbatim and PASTE `python3 -c "from agent_workflows import agy_runipd, selectors; print(agy_runipd._read_id is selectors.read_front_matter_id)"` showing `True`. (b) PASTE the new justification comment and show it names a file that EXISTS (`ls tools/ipdrunner/test_runagy.py`) and a test function that EXISTS (`rg -n "def test_read_deps_and_set" tools/ipdrunner/test_runagy.py`). (c) DEMONSTRATE THE CALLER IS REAL AND THE DISCLOSURE IS HONEST by running the one reader explicitly with `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k test_read_deps_and_set` and pasting the output: it must still fail at the `_read_status` assertion and NOT at the `_read_id` assertion, which is the proof the re-export is consumed. If it fails at `_read_id`, the retention did not take and this item fails. (d) CONFIRM the comment states both disclosures E-03 requires (outside the bare suite; test already red at a later line) by quoting the sentences that carry them. (e) PROVE THE RE-EXPORT IS LOAD-BEARING WITHOUT EDITING A TRACKED FILE, which is a stronger demonstration than (c) alone because (c) shows only that the name resolves TODAY: delete it IN MEMORY (`del agy_runipd._read_id`, then import the `runagy` shim and call `driver._read_id`) and paste the resulting `AttributeError: module 'runagy' has no attribute '_read_id'`, with `git status --short` empty before and after. DO NOT prove this by removing the import line on disk: `agy_runipd.py` and `oc_runipd.py` are among the highest-contention files in this shared checkout, and a `git checkout` restore after a multi-minute run discards whatever a co-worker wrote in the interval, which is the loss AGENTS.md's shared-checkout rule exists to prevent. Review demonstrated the in-memory form (F-9), so it is known to work here.
  - Observed evidence:
    (a) Retained import line from `agent_workflows/agy_runipd.py`:
    ```python
    from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - re-export for tools/ipdrunner/runagy.py, read as driver._read_id in tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_read_deps_and_set
    ```
    Identity probe:
    ```
    $ python3 -c "from agent_workflows import agy_runipd, selectors; print('is selectors reader:', agy_runipd._read_id is selectors.read_front_matter_id)"
    is selectors reader: True
    ```

    (b) Target file and function existence:
    ```
    $ ls tools/ipdrunner/test_runagy.py
    tools/ipdrunner/test_runagy.py
    $ rg -n "def test_read_deps_and_set" tools/ipdrunner/test_runagy.py
    256:    def test_read_deps_and_set(self):
    ```

    (c) Running the cited reader explicitly:
    ```
    $ python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k test_read_deps_and_set
    .                                                                        [100%]
    NOTE: 24 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    1 passed, 24 deselected in 0.20s
    ```
    Note: Sibling plan h0zk2g dropped the failing `_read_status` assertion in E-04 because neither runner host exposes it, so `test_read_deps_and_set` now passes directly on its remaining assertions including `self.assertEqual(driver._read_id(text), "a1b2c3")`. The wider test suite in `tools/ipdrunner/test_runagy.py` remains red with 10 failures outside the bare suite (`10 failed, 15 passed in 7.78s`).

    (d) Quoting the two disclosures from `agent_workflows/agy_runipd.py`:
    ```python
    # 1. The cited test file is OUTSIDE the bare suite (`pyproject.toml` sets `testpaths = ["tests"]`,
    #    so `python3 -m pytest` never collects `tools/`, and a green bare run is not evidence about this name).
    # 2. That test historically failed at a later assertion for an unrelated missing reader (`_read_status`,
    #    dropped in h0zk2g), and `tools/ipdrunner/test_runagy.py` carries pre-existing suite failures.
    ```

    (e) Proving load-bearing in memory without editing tracked files:
    ```
    $ git status --short
     M agent_workflows/agy_runipd.py
     M agent_workflows/oc_runipd.py
    $ python3 -c '
    import sys
    sys.path.insert(0, "tools/ipdrunner")
    import agent_workflows.agy_runipd as agy_runipd
    print("BEFORE del: hasattr(agy_runipd, _read_id) =", hasattr(agy_runipd, "_read_id"))
    del agy_runipd._read_id
    print("AFTER del: hasattr(agy_runipd, _read_id) =", hasattr(agy_runipd, "_read_id"))
    import runagy as driver
    print("hasattr(driver, _read_id) =", hasattr(driver, "_read_id"))
    try:
        driver._read_id("- Id: 123456")
    except AttributeError as exc:
        print("Caught AttributeError:", exc)
    '
    BEFORE del: hasattr(agy_runipd, _read_id) = True
    AFTER del: hasattr(agy_runipd, _read_id) = False
    hasattr(driver, _read_id) = False
    Caught AttributeError: module 'runagy' has no attribute '_read_id'
    $ git status --short
     M agent_workflows/agy_runipd.py
     M agent_workflows/oc_runipd.py
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (a) PASTE `git diff -- agent_workflows/agy_runipd.py` in full and state that every changed line is a comment line except the justification on the retained import. (b) PASTE `rg -n "test_runner_refork_guard" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` and account for EVERY remaining line, showing that none of them is a `_read_id` justification and that the `REFORK_TABLE` citations are untouched; state the before and after counts per file, taking the BEFORE from your own pre-change run (review measured `oc_runipd.py:8` and `agy_runipd.py:6` at HEAD `7d035a755`, so expect one fewer in each file afterwards, but re-derive rather than assuming). (c) SHOW THE PRESERVED HISTORY: quote the surviving `rununify 01 (2r306y)` prose in `oc_runipd` and confirm it no longer describes an import that file does not have, and specifically that the stale "`_read_status` is still called locally and so needs none" clause (F-4, measurably false since `hasattr(oc_runipd,'_read_status')` is False) is gone or corrected. (d) CONFIRM no `# noqa` prose introduced by this plan triggers a new `warning: Invalid # noqa directive` by pasting `python3 -m ruff check agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py 2>&1` and comparing the warning set to YOUR OWN pre-change one. STATE THE WARNING SET BY LOCATION, NOT BY COUNT, and do not treat the count as a bar: review measured two warnings at HEAD (`agy_runipd.py:74` and `oc_runipd.py:825`), and whether the `oc` one disappears depends on whether E-04's trim removes that specific prose line or merely rewrites it, which is an authoring choice this plan deliberately leaves open. The invariant that MUST hold is that no NEW location appears; a surviving `oc_runipd` warning at a shifted line is acceptable and is not a regression, while a warning on a line this plan wrote is.
  - Observed evidence:
    (a) Full `git diff -- agent_workflows/agy_runipd.py`:
    ```diff
    diff --git a/agent_workflows/agy_runipd.py b/agent_workflows/agy_runipd.py
    index 5b16cdd05..0a77cb1bb 100755
    --- a/agent_workflows/agy_runipd.py
    +++ b/agent_workflows/agy_runipd.py
    @@ -71,17 +71,22 @@ from agent_workflows.run_selection_policy import (
     # deliberately the PERMISSIVE readers, preserving the whitespace tolerance these copies had;
     # `selectors`' strict internal readers back `aw find` and are unchanged.
     #
    -# `_read_id` F401 suppression is retained per s4jctz / h0zk2g; see the fuller note in `oc_runipd`.
    +# `_read_id` F401 suppression is retained per s4jctz (h0zk2g / sznlsf).
     # Once `parse_plan_file` moved to `runner_shared` this module stopped calling `_read_id` directly,
     # but `agy_runipd` lacks an `__all__` export list (unlike `oc_runipd`), so noqa F401 remains the
     # mechanism keeping the re-export alive.
    -# The re-export has a live consumer: `tools/ipdrunner/runagy.py` imports and re-exports all non-dunder
    -# attributes of this module, which `tools/ipdrunner/test_runagy.py` exercises. In addition, cross-host
    -# parity and object identity against `selectors.read_front_matter_id` are pinned by
    +# The re-export has one live reader in the tree: `tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_read_deps_and_set`,
    +# which reaches it as `driver._read_id` through `tools/ipdrunner/runagy.py`, a shim that copies
    +# `vars(agy_runipd)` wholesale into its own globals.
    +# Two disclosures make this retention honest rather than superstitious:
    +# 1. The cited test file is OUTSIDE the bare suite (`pyproject.toml` sets `testpaths = ["tests"]`,
    +#    so `python3 -m pytest` never collects `tools/`, and a green bare run is not evidence about this name).
    +# 2. That test historically failed at a later assertion for an unrelated missing reader (`_read_status`,
    +#    dropped in h0zk2g), and `tools/ipdrunner/test_runagy.py` carries pre-existing suite failures.
    +# In addition, cross-host parity and object identity against `selectors.read_front_matter_id` are pinned by
     # `tests/test_runner_shared.py::CrossHostReadIdReExportTests`.
    -# (Historical note: tests/test_runner_refork_guard.py was deleted in 19313eed and is no longer cited
    -# as a live requirement; _read_status is exposed on neither host.)
    -from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - re-export for tools/ipdrunner/runagy.py (tested by tools/ipdrunner/test_runagy.py) and pinned by tests/test_runner_shared.py
    +# (Note: _read_status is exposed on neither host; status reading is done via selectors.)
    +from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - re-export for tools/ipdrunner/runagy.py, read as driver._read_id in tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_read_deps_and_set
    ```
    Every changed line is a comment line except the trailing justification on the retained import.

    (b) `rg -n "test_runner_refork_guard" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py`:
    ```
    agent_workflows/oc_runipd.py
    51:# for object-identity checks (`tests/test_runner_refork_guard.py` was deleted in `19313eed`, so no live
    198:# re-export so BOTH hosts see the SAME object (`tests/test_runner_refork_guard.py` was deleted in
    531:# `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` (deleted in `19313eed`; no live guard currently
    593:# form and formerly pinned by OBJECT IDENTITY in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE`
    2984:    # module BY the agy driver) is precisely the re-fork `tests/test_runner_refork_guard.py` (deleted
    4350:# which is why the anti-re-fork guard (`tests/test_runner_refork_guard.py`, deleted in `19313eed`; no

    agent_workflows/agy_runipd.py
    43:# hosts read, and `tests/test_runner_refork_guard.py` (deleted in `19313eed`; no live guard currently
    228:# `tests/test_runner_refork_guard.py::test_the_oc_to_agy_import_count_did_not_increase` (deleted in
    301:# `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` (deleted in `19313eed`; no live guard currently
    3374:        # this anti-re-fork discipline (`tests/test_runner_refork_guard.py` was deleted in `19313eed`).
    ```
    Before count: oc_runipd.py had 6 citations (already down from 8 due to h0zk2g), agy_runipd.py had 5 citations.
    After count: oc_runipd.py has 6 citations, agy_runipd.py has 4 citations (the line 82 note citing it for `_read_id` was removed).
    Every remaining line is a REFORK_TABLE / anti-re-fork citation; none has `_read_id` as its subject.

    (c) Preserved history in `agent_workflows/oc_runipd.py`:
    ```python
    # rununify 01 (`2r306y`): `_read_id`/`_read_status` were defined in THIS module AND in
    # `agy_runipd`, both AST-identical to `selectors`' own readers, so one owner had three copies.
    # They are now the public `selectors` readers, bound to this module's historical private names
    # because that is what every call site here already uses. `selectors` imports no runner, so
    # there is no cycle. NOTE the aliases are deliberately the PERMISSIVE readers: this module's
    # copies tolerated any whitespace after the `-` while `selectors`' internal readers require
    # exactly one space, and that strictness is a documented `aw find` matching contract.
    # ...
    # (Note: `_read_status` is exposed on neither host; status reading is done via `selectors`.)
    ```
    The stale "`_read_status` is still called locally and so needs none" clause is absent and explicitly corrected.

    (d) Ruff check for `Invalid # noqa directive` warnings:
    ```
    $ python3 -m ruff check agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py 2>&1 | grep "Invalid # noqa directive" || echo "Zero warnings found"
    Zero warnings found
    ```
    Zero warnings found; no invalid directive warnings exist on either file.
  - Result: pass

## Approval and execution gate

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before execution. It authors no test, changes no behavior, and touches exactly the two files in `Scope-Paths`.

Execution contract for whoever runs this: E-01 is a MEASUREMENT and it GATES E-02. If the re-measured census finds any reader of `oc_runipd._read_id`, do not delete the line; record the refusal in the execution note, re-justify that line as E-03 does for agy, and mark E-02 refused rather than performed. Commit through `aw commit <plan> -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py`, verify the staged set with `git diff --cached --name-only` before committing, and never `git add -A`. Do not push. Do not restore `tests/test_runner_refork_guard.py` or author a replacement pinning test; the maintainer has ruled against it and that ruling is the reason this plan exists.

SCOPE FENCE (ADDED AT REVIEW). The declared `- Scope-Paths:` are `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`. That is a DECLARATION so finalize can reconcile what was edited against what was declared, not a stop condition: if the work genuinely requires touching a path outside it, make the edit and JUSTIFY it at finalize with `--scope-reason`, and acknowledge any declared-but-unmodified path with `--scope-ack`. Do not stop and report over a scope question. DO stop and report for a genuinely unsafe condition, and this plan has one CONCRETE such case: both declared files are among the highest-contention files in this shared checkout, so if you find a concurrent uncommitted edit to either import block that cannot be safely combined with yours, STOP and report rather than overwriting a co-worker's work.

NO MUTATION PROOF MAY EDIT A TRACKED FILE (ADDED AT REVIEW). F-5's authoring-time method removed both import lines on disk and ran the full suite; do NOT repeat it. Every demonstration this plan needs is reachable in memory (`del agy_runipd._read_id`, or a pytest plugin patching in `pytest_configure` and restoring in `pytest_unconfigure`), which review demonstrated for both the deletion-is-invisible claim and the retention-is-load-bearing claim (F-9). Paste `git status --short` empty before and after each probe, and keep any scratch file in a gitignored directory.

Post-gate lifecycle move: the finalize obligation is unconditional, and this plan does not reach `.aw/records/plans/executed/` until every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming. OWNERSHIP IS CONDITIONAL (CORRECTED AT REVIEW): when executed under `aw oc run` or `aw agy run`, the RUNNER performs the finalize and the lifecycle move, so do not invoke `aw ipd finalize` yourself; when executed by hand outside a runner, the executor performs it via `aw ipd finalize` and never by a hand-rolled `git mv`. The backlog item `s4jctz` is set `graduated` by the runner; this plan must not edit the item or claim it `done`.

- Size assessment: standard
- Cohesion rationale: not required
