# IPD: Resolve the two _read_id re-exports in the host runners against measured callers

- Date: 2026-09-30
- Kind: child
- Concern: Both host runners carry a `# noqa: F401` re-export of `selectors.read_front_matter_id` under the private name `_read_id`. Neither module calls it. Its justification cites `tests/test_runner_refork_guard.py`, deleted in `19313eed`, and the maintainer has ruled that the deleted code-pinning test will not be restored and that the re-exports must be judged on FUNCTIONAL callers. This plan measures who actually reads the name, then resolves each of the two lines on that measurement rather than on a dead citation.
- Scope: Measure every reader of `_read_id` on either host module; DELETE the unread `oc_runipd` re-export; RETAIN the `agy_runipd` one because one live out-of-suite test reads it through the `runagy.py` shim, and re-justify it against that real caller. Correct the two multi-paragraph comment blocks that currently explain the imports by citing the deleted guard. No behavior change, no test authored to pin an import.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: s4jctz
- Set: s4jctz
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: sznlsf

## Workflow history

- 2026-09-30 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): authored from backlog `s4jctz`. The measurement the item asks for was PERFORMED AT AUTHORING TIME (AST scan of every `.py` in the tree, plus a deletion probe under the full bare suite) because the item's whole question is empirical and an unmeasured plan would have had to guess the answer. The measurement is recorded in Findings and the checklist is shaped by it. HEADLINE: the two lines are NOT symmetric and the backlog item's framing ("delete both lines or re-justify them") admits a split answer, which is what the evidence supports. `oc_runipd._read_id` has ZERO readers anywhere in the tree and is deleted here. `agy_runipd._read_id` HAS a reader (`tools/ipdrunner/test_runagy.py` line 268, reaching it through `runagy.py`'s `vars()` re-export loop) and is retained with that caller cited. Nothing is pushed.
- 2026-09-30 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Replace a dead justification with a measured one. After this plan, neither `# noqa: F401` re-export of `_read_id` rests on a deleted test: the `oc_runipd` copy is GONE because nothing reads it, and the `agy_runipd` copy REMAINS with its one real reader named in the comment. The backlog item's measurement obligation is discharged with pasted evidence rather than restated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure, then act on the measurement

- [ ] E-01 RE-RUN THE READER MEASUREMENT AT EXECUTION HEAD and record it, rather than trusting this plan's authoring-time numbers. The authoring measurement is in Findings F-1 and F-2 and was taken at HEAD `62b18f47`; if execution happens at a later HEAD, a new reader may exist and would change E-02's verdict. Perform three scans: (a) an AST scan over every `.py` file in the tree for `ImportFrom` of `_read_id` from either host module AND for any `Attribute` access whose `attr` is `_read_id`, reporting the base expression of each; (b) a text scan (`rg -n "_read_id"`) restricted to `agent_workflows/`, `tests/` and `tools/` so a dynamic access an AST attribute scan would not attribute to a host module is still seen; (c) a check of whether the two host modules are reachable as a public surface at all, namely whether `oc_runipd`/`agy_runipd` appear in `agent_workflows.__init__`'s `__all__` and whether `_read_id` appears in `oc_runipd.__all__`. Do NOT edit anything in this item.
  - Depends on: none
  - Expected outcome: A reader census naming every site. The authoring-time expectation, which this item exists to CONFIRM OR FALSIFY rather than assume: exactly one reader of a HOST module's `_read_id` exists (`tools/ipdrunner/test_runagy.py`, via `driver._read_id` where `driver` is the `runagy` shim), and the four other `_read_id` attribute accesses in the tree resolve to `selectors` or `plans_refs`, NOT to a runner. If the census finds a reader of `oc_runipd._read_id`, E-02 MUST NOT delete it and the plan becomes re-justify-both; say so plainly and treat E-02 as refused rather than forcing the delete.
  - Execution state: pending

- [ ] E-02 DELETE the `oc_runipd` re-export line and its `# noqa: F401`, CONDITIONAL on E-01 finding zero readers. Remove the whole statement `from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 ...` from `agent_workflows/oc_runipd.py`. The module does not call the name (no bare `Name` load of `_read_id` exists in it) and does not list it in `__all__`, so the import is dead surface. DO NOT remove `_read_status`, `_read_set`, `_read_order`, `_read_kind` or `_read_item_dependencies` from either host: they are a different question, some are genuinely called, and `_read_status`/`_read_deps` are ALREADY ABSENT from both hosts (see F-4), so a sweep here would be scope creep on a family this plan did not measure for callers.
  - Depends on: E-01
  - Expected outcome: `hasattr(agent_workflows.oc_runipd, "_read_id")` is False; `python3 -m ruff check --select F401 agent_workflows/oc_runipd.py` still passes (the import is gone, so there is nothing to suppress); the bare suite count is UNCHANGED from the pre-change baseline.
  - Execution state: pending

- [ ] E-03 RETAIN the `agy_runipd` re-export and RE-JUSTIFY its `# noqa: F401` against its real caller. Keep the import statement. Replace the trailing justification comment so it cites `tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_read_deps_and_set`, which reads the name as `driver._read_id` where `driver` is `tools/ipdrunner/runagy.py`, a shim that copies `vars(agy_runipd)` into its own globals and so re-exports private names too. The comment MUST also state the two facts that make this retention honest rather than superstitious: that the cited test file is OUTSIDE the bare suite (`pyproject.toml` sets `testpaths = ["tests"]`, so `python3 -m pytest` never collects `tools/`, and a green bare run is NOT evidence about this name), and that the test is ALREADY FAILING at a LATER line for an unrelated missing reader (`_read_status`), so the re-export is load-bearing for a test that does not currently pass either way. Do NOT overstate the justification: say the name has ONE reader and name it.
  - Depends on: E-01
  - Expected outcome: `agy_runipd._read_id is selectors.read_front_matter_id` remains True. The comment names a file that EXISTS and a test function that EXISTS, and no comment in the file claims a live guard enforces the re-export.
  - Execution state: pending

- [ ] E-04 CORRECT THE TWO EXPLANATORY COMMENT BLOCKS that currently justify these imports by narrating the deleted guard, so the files do not keep an explanation for an import that is gone (oc) or a wrong explanation for one that stays (agy). In `oc_runipd.py`, the `rununify 01 (2r306y)` block above the deleted import currently spends a paragraph on why `_read_id`'s `# noqa` "IS LOAD-BEARING" and on what `tests/test_runner_refork_guard.py` "required BOTH runners" to expose; that paragraph must GO with the import, while the surrounding prose about `_read_id`/`_read_status` having been de-duplicated onto `selectors` (still true and still useful history) must be PRESERVED and left factually correct about what the module now imports. In `agy_runipd.py`, the matching paragraph must stop asserting a requirement no test imposes and instead point at E-03's real caller; its cross-reference "see the fuller note in `oc_runipd`" must be resolved too, since that note is being trimmed. Touch COMMENTS ONLY in this item.
  - Depends on: E-02, E-03
  - Expected outcome: `rg -n "test_runner_refork_guard" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` no longer returns any line whose subject is `_read_id`; the remaining `test_runner_refork_guard` citations in those two files (the `REFORK_TABLE` ones, which are a different property and out of this plan's fence) are UNCHANGED.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A RE-EXPORT IS SPELLED `as <same-name>` HERE AND THAT FORM IS NOT SELF-SUFFICIENT. Both host modules mark deliberate re-exports with the redundant `X as X` form (see the block importing `plan_kind_from_file as plan_kind_from_file` and its neighbours in `oc_runipd`). The `_read_id` lines cannot use that form because they RENAME (`read_front_matter_id as _read_id`), which is why they carry a `# noqa: F401` instead. Measured in this tree: stripping the `# noqa` from a copy of `oc_runipd.py` and running `python3 -m ruff check --select F401 --fix` DELETES the import (evidence in V-01), so the suppression is genuinely the mechanism keeping the line alive, exactly as the existing comment claims. That makes the comment's MECHANISM claim true and only its JUSTIFICATION claim dead.
- THE `# noqa` DIRECTIVES IN BOTH FILES ARE MALFORMED AND RUFF SAYS SO. `python3 -m ruff check` emits `warning: Invalid # noqa directive on agent_workflows/agy_runipd.py:74` and the same for `oc_runipd.py:825`, because those two lines are PROSE comments that begin with `# noqa` narration rather than directives. This is pre-existing, is on the comment lines this plan edits, and E-04's rewrite should not reproduce the malformed spelling in new prose. Recorded as an observation, not adopted as a deliverable: the plan does not take on a `# noqa` hygiene sweep.
- `tools/ipdrunner/runagy.py` RE-EXPORTS PRIVATE NAMES WHOLESALE, which is why an underscore prefix does not mean "unreachable" for `agy_runipd`. Its module body loops `for _k, _v in vars(agy_runipd).items()` and copies everything not dunder-prefixed into its own globals. `tools/ipdrunner/runipd.py` does NOT do this: it re-exports five named attributes (`main`, `DriverError`, `Palette`, `Heartbeat`, `PlanRecord`) explicitly. That asymmetry between the two shims is the mechanical reason the two re-exports have different answers, and it is the single most decision-relevant convention found.
- `testpaths = ["tests"]` in `pyproject.toml` means `tools/` IS NOT COLLECTED by a bare run. The one live reader of a host `_read_id` therefore lives outside the suite that gates every change in this repo. `tools/ipdrunner/test_runagy.py` says so in its own class docstring, which also records that the file is partly red at HEAD for unrelated reasons.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Severity | Subject | Finding | Evidence |
|---|---|---|---|---|
| F-1 | BLOCKER for the "delete both" reading | `oc_runipd._read_id` has ZERO readers; `agy_runipd._read_id` has ONE | The backlog item asks for a measurement and leaves the verdict open. MEASURED: an AST scan over every `.py` in the tree finds exactly FIVE accesses whose attribute is `_read_id`, and only ONE of them targets a host runner. The other four target `selectors` or `plans_refs` (`doctor.py` via `_sel`, `production_checks.py` via `_pr`, `cli.py` via `sel_mod`, `artifact_audit.py` via `_sel`) and are untouched by this plan. ZERO `ImportFrom` statements anywhere import `_read_id` from either host module. So the two lines are NOT symmetric and a uniform "delete both" would break the one reader, while a uniform "re-justify both" would keep a provably dead line in `oc_runipd`. | AST scan at HEAD `62b18f47` over all `*.py`: `('attribute','agent_workflows/doctor.py',907,'_sel')`, `('attribute','agent_workflows/production_checks.py',36,'_pr')`, `('attribute','agent_workflows/cli.py',11746,'sel_mod')`, `('attribute','agent_workflows/artifact_audit.py',1113,'_sel')`, `('attribute','tools/ipdrunner/test_runagy.py',268,'driver')`, `total: 5` |
| F-2 | HIGH | the one reader reaches `agy_runipd` through a `vars()` shim, so the underscore is not protection | `tools/ipdrunner/test_runagy.py` calls `driver._read_id(text)` and asserts it returns `"a1b2c3"`; `driver` is `import runagy as driver`, and `runagy.py` copies `vars(agy_runipd)` into its globals, private names included. This is precisely the case the backlog item warns about ("something may import `oc_runipd._read_id` even though the underscore says it should not") and it turns out to be REAL for agy and ABSENT for oc. | `tools/ipdrunner/test_runagy.py` `test_read_deps_and_set`: `self.assertEqual(driver._read_id(text), "a1b2c3")`; `tools/ipdrunner/runagy.py`: `for _k, _v in vars(agy_runipd).items(): if not _k.startswith("__"): globals()[_k] = _v` |
| F-3 | HIGH | the retained re-export is load-bearing for an ALREADY-RED test, and that must be said rather than hidden | Removing both lines and running the one reader shows the failure MOVES EARLIER rather than appearing: with the re-export present the test fails at `driver._read_status`, and with it removed the test fails one assertion earlier at `driver._read_id`. So the retention is justified by a real caller, but that caller does not currently pass, and a reader of the comment deserves to know the retention does not make a green test green. E-03 requires the comment to say so. | With both lines removed: `AttributeError: module 'runagy' has no attribute '_read_id'. Did you mean: '_read_kind'?` at `test_runagy.py:268`. At unmodified HEAD: `AttributeError: module 'runagy' has no attribute '_read_status'. Did you mean: '_read_set'?` at `test_runagy.py:271`. Whole-module at HEAD: `11 failed, 14 passed` |
| F-4 | MEDIUM | the sibling readers the comments discuss are ALREADY GONE, so one existing comment is stale in a second way | `oc_runipd`'s comment ends "`_read_status` is still called locally and so needs none." MEASURED FALSE: neither host module exposes `_read_status` OR `_read_deps` at all today (`hasattr` is False on both for both), because `parse_plan_file` moved to `runner_shared`, which reaches those readers through FUNCTION-LOCAL imports. `_read_set`, `_read_order`, `_read_kind` and `_read_item_dependencies` DO remain on both hosts, imported from `runner_shared`. E-04 must not reproduce the stale `_read_status` clause; E-02 must not be tempted into deleting names that are not there. | `hasattr` matrix: `_read_id` oc=True agy=True rs=False sel=True; `_read_status` oc=False agy=False rs=False sel=True; `_read_set`/`_read_order`/`_read_kind`/`_read_item_dependencies` oc=True agy=True rs=True |
| F-5 | MEDIUM | deleting BOTH lines leaves the bare suite completely unchanged, so the suite cannot be cited as protection for either line | A deletion probe removed both import lines and ran the bare suite: `3387 passed, 2 skipped` both before and after, identical. This is the evidence that makes E-02 safe AND the evidence that shows why E-03 cannot be justified by the suite: the gating suite is blind to this name in both directions. Anyone re-deriving the answer from `make test` alone will conclude both lines are dead, and they will be wrong about agy. | Baseline at HEAD: `3387 passed, 2 skipped, 3 warnings in 65.01s`. With both lines removed: `3387 passed, 2 skipped, 3 warnings in 63.98s`. Both modules still import cleanly with the lines removed. |
| F-6 | LOW | the host modules are not a public surface, which bounds the external-caller risk the item raises | The backlog item asks whether anything outside the repo "plausibly could" read these names. Measured: `oc_runipd` and `agy_runipd` are NOT in `agent_workflows.__init__.__all__`, and `oc_runipd.__all__` (22 names) contains no `_read*` name at all, while `agy_runipd` declares no `__all__`. An external importer would have to reach a private name on a non-exported submodule. That is not zero risk, but combined with F-1 it is the basis for deleting the oc line rather than keeping it defensively forever. | `'oc_runipd' in agent_workflows.__all__` -> False; `'agy_runipd' in agent_workflows.__all__` -> False; `[n for n in oc_runipd.__all__ if '_read' in n]` -> `[]`; `len(oc_runipd.__all__)` -> 22; AST scan finds no `__all__` assignment in `agy_runipd` |

## Proposed changes (ordered, validatable)

1. Re-measure the reader census at execution HEAD (E-01), because the entire verdict is empirical and the authoring numbers are pinned to `62b18f47`.
2. Delete the `oc_runipd` import line with its `# noqa`, on the strength of a zero-reader census (E-02).
3. Keep the `agy_runipd` import line and rewrite its trailing justification to name `tools/ipdrunner/test_runagy.py`, stating both that the file is outside the bare suite and that it is already red at a later line (E-03).
4. Trim the now-orphaned justification paragraph in `oc_runipd` and correct the matching paragraph in `agy_runipd`, preserving the still-true de-duplication history in both (E-04).

## Deferred / out of scope (with reason)

- AUTHORING ANY TEST THAT PINS THE RE-EXPORT. Explicitly refused. The maintainer's ruling on this item is that the repo does not test that code has not changed and does not pin imports, and the deleted `tests/test_runner_refork_guard.py` will not be restored. A new test asserting `hasattr(agy_runipd, "_read_id")` would be the same code-pinning test under a new name and would violate AGENTS' TEST OUTCOMES, NOT CODE STRUCTURE rule. The retention in E-03 is justified by a FUNCTIONAL caller and documented in a comment, which is the mechanism this repo has left for the property.
- FIXING `tools/ipdrunner/test_runagy.py`. The one reader is red at HEAD, at a later assertion, for a missing `_read_status` re-export (F-3, F-4), and `AgyExecutionLifecycleTests` in the same file is independently red. Repairing that file is a separate, larger question (does the shim need the whole reader family back, or should the test drive `runner_shared` directly?) and it is NOT what this item asks for. This plan must not paper over it either: E-03 requires the retention comment to disclose it. A follow-up is worth filing after execution; this plan does not file one speculatively.
- THE `REFORK_TABLE` CITATIONS of the deleted guard file in both hosts, and the wider residue in `runner_shared.py`, `run_viewer.py`, `artifact_audit.py` and the test fixtures. Those cite the same deleted file for a DIFFERENT property (one definition per host), they were already corrected to record the deletion by plan `t0ovw6`, and the residue is carried by `pn7rw3`. E-04's expected outcome pins them as UNCHANGED so this plan cannot drift into that fence.
- THE MALFORMED `# noqa` DIRECTIVE WARNINGS ruff emits on the two comment lines (Step 0). Pre-existing, cosmetic, and a hygiene sweep of `# noqa` prose across the package is not this item.
- REMOVING OR RE-HOMING `_read_set`, `_read_order`, `_read_kind`, `_read_item_dependencies`. Present on both hosts, not measured for callers here, and outside the item's subject.

## Scope check

- Over-scope: none. Two files, two statements, and the comment blocks that explain those statements.
- Under-scope: The plan does not repair the one red test that justifies the retained re-export, and does not sweep the sibling reader family. Both are named in Deferred with reasons. A reader wanting the re-export DEFENDED by a test rather than by a comment will not get that here, and the reason is the maintainer's ruling against pinning tests, which is recorded rather than worked around.

## Required tests / validation

The bare suite (`python3 -m pytest`) is the gate for the repository, and F-5 establishes it is BLIND to both re-exports, so it is run as a NO-REGRESSION check only and must NOT be cited as evidence that either line is or is not needed. The positive evidence is the reader census (E-01) plus direct `hasattr`/identity probes on the two modules, plus an explicit run of the one out-of-suite reader with `-o addopts=""` so `tools/` is collected at all. `python3 -m ruff check --select F401` on both files confirms the deleted line needs no suppression and the retained line still has one.

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

- [ ] V-01 validates E-01
  - Required evidence: (a) PASTE the AST census output at execution HEAD, listing every `_read_id` access site with its base expression and every `ImportFrom` of `_read_id`, and state the HEAD sha it was taken at. (b) PASTE `rg -n "_read_id" agent_workflows/ tests/ tools/` in full and account for every line, classifying each as a `selectors`/`plans_refs` owner-or-caller, a comment, or a host-module reader. (c) PASTE the reachability probe: `'oc_runipd' in agent_workflows.__all__`, `'agy_runipd' in agent_workflows.__all__`, `[n for n in oc_runipd.__all__ if '_read' in n]`, and whether `agy_runipd` declares `__all__`. (d) STATE THE VERDICT EXPLICITLY in the form "readers of `oc_runipd._read_id`: N; readers of `agy_runipd._read_id`: M", and if N is not 0, state that E-02 was REFUSED and why. Do not paraphrase the census; paste it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: (a) PASTE `git diff -- agent_workflows/oc_runipd.py` and confirm the only executable-line change is the removal of the one import statement. (b) PASTE `python3 -c "from agent_workflows import oc_runipd; print(hasattr(oc_runipd,'_read_id'))"` showing `False`, and a matching probe showing `oc_runipd` still imports without error. (c) PASTE `python3 -m ruff check --select F401 agent_workflows/oc_runipd.py` showing it passes. (d) PASTE the bare `python3 -m pytest` summary line and show it MATCHES the pre-change baseline captured before any edit (authoring baseline for reference: `3387 passed, 2 skipped`); a changed count fails this item and must be investigated, not explained away. (e) CONFIRM by probe that `_read_set`, `_read_order`, `_read_kind` and `_read_item_dependencies` are STILL present on `oc_runipd` (F-4's family was not swept).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: (a) PASTE the retained import line from `agy_runipd.py` verbatim and PASTE `python3 -c "from agent_workflows import agy_runipd, selectors; print(agy_runipd._read_id is selectors.read_front_matter_id)"` showing `True`. (b) PASTE the new justification comment and show it names a file that EXISTS (`ls tools/ipdrunner/test_runagy.py`) and a test function that EXISTS (`rg -n "def test_read_deps_and_set" tools/ipdrunner/test_runagy.py`). (c) DEMONSTRATE THE CALLER IS REAL AND THE DISCLOSURE IS HONEST by running the one reader explicitly with `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k test_read_deps_and_set` and pasting the output: it must still fail at the `_read_status` assertion and NOT at the `_read_id` assertion, which is the proof the re-export is consumed. If it fails at `_read_id`, the retention did not take and this item fails. (d) CONFIRM the comment states both disclosures E-03 requires (outside the bare suite; test already red at a later line) by quoting the sentences that carry them.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (a) PASTE `git diff -- agent_workflows/agy_runipd.py` in full and state that every changed line is a comment line except the justification on the retained import. (b) PASTE `rg -n "test_runner_refork_guard" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` and account for EVERY remaining line, showing that none of them is a `_read_id` justification and that the `REFORK_TABLE` citations are untouched; state the before and after counts per file. (c) SHOW THE PRESERVED HISTORY: quote the surviving `rununify 01 (2r306y)` prose in `oc_runipd` and confirm it no longer describes an import that file does not have, and specifically that the stale "`_read_status` is still called locally" clause (F-4, measurably false) is gone or corrected. (d) CONFIRM no `# noqa` prose introduced by this plan triggers a new `warning: Invalid # noqa directive` by pasting `python3 -m ruff check agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py 2>&1` and comparing the warning set to the pre-change one (two warnings at HEAD; after E-02 removes one comment block, at most one should remain, and no NEW location may appear).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before execution. It authors no test, changes no behavior, and touches exactly the two files in `Scope-Paths`.

Execution contract for whoever runs this: E-01 is a MEASUREMENT and it GATES E-02. If the re-measured census finds any reader of `oc_runipd._read_id`, do not delete the line; record the refusal in the execution note, re-justify that line as E-03 does for agy, and mark E-02 refused rather than performed. Commit through `aw commit <plan> -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py`, verify the staged set with `git diff --cached --name-only` before committing, and never `git add -A`. Do not push. Do not restore `tests/test_runner_refork_guard.py` or author a replacement pinning test; the maintainer has ruled against it and that ruling is the reason this plan exists.

Post-gate lifecycle move: after every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, the plan moves to `.aw/records/plans/executed/` via the tooled transition (`aw ipd finalize`), not by hand. The backlog item `s4jctz` is set `graduated` by the runner; this plan must not edit the item or claim it `done`.

- Size assessment: standard
- Cohesion rationale: not required
