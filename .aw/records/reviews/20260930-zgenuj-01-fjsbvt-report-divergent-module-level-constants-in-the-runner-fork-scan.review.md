# Review findings: plan fjsbvt

- Subject-Id: fjsbvt
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `de95e6a03`. The plan file was committed and the tree
clean (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE any edit;
`--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:` bullet
reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

I RE-DERIVED EVERY LOAD-BEARING MEASUREMENT INDEPENDENTLY. The plan's diagnosis is correct, its
design reasoning is sound, and its one genuinely novel argument (that the `getattr` mechanism the
backlog item prescribes is unavailable to this tool) is both true and well evidenced:

- F-04's structural claim holds by reading: `top_level_defs` filters on
  `ast.FunctionDef`/`ast.AsyncFunctionDef`/`ast.ClassDef`, and `census` builds `co_defined` from
  `set(defs[OC]) & set(defs[AGY])`, so no module-level constant can ever be a census member. The
  constants-only route into any report really is the per-fork closure section.
- F-05 reproduces exactly and is the plan's best finding. Run with `cwd=/` and `tools/` on
  `sys.path`, `package_dir()` returned THIS lane's `agent_workflows` while `import agent_workflows`
  resolved to the main checkout, two different trees. The `spec_from_file_location` rescue the plan
  also tested fails the same way: the loaded `oc_runipd`'s own `runner_shared` resolved to the main
  checkout. So a `getattr` comparison would silently report values from a tree the scanner is not
  parsing, which is exactly the reproducibility violation the plan names. Confirmed independently
  that the scanner contains no `importlib`/`__import__`/`import_module` today.
- F-08's false-positive class reproduces by construction: a fixture shared module defining
  `MSG` and `ALIAS` to the same string, with each host referencing a different one, makes
  `_value_differs` return `True` for two references that resolve to ONE value. So static resolution
  is justified even though the live tree currently has no instance.
- F-07 re-verifies UNCHANGED: over the 8 three-way names, 7 differ by source text and 0 by resolved
  value, so the plan's correction of the backlog item's "9 of 10" figure (right about the three-way
  class, over-generalized to the host pair) is accurate.
- F-10 holds: `lift_drift_scan` calls exactly `normalize`, `top_level_defs`, `free_names` and
  `is_pure_delegation`, and neither `_value_differs` nor `census`, so an additive change cannot
  break it.
- F-11 holds: `rg -l runner_fork_scan` tree-wide returns only the two `tools/` files, so E-05 really
  is the scanner's first test of any kind.
- E-04's docstring claims hold verbatim, including the quoted "most important limitation" sentence,
  the `FULL_AUTO_ACTOR` worked example, the "READ THE CLOSURE REPORT BEFORE ACTING" line, the
  measuring-instrument contract and the five-entry `USAGE` block. Re-measured, `set_plan_approved`
  is no longer among the 8 listed forks and `--triples` reports only `StallWatchdog`, so the cited
  current-state example genuinely no longer reproduces from the tool's own output.

I ALSO VERIFIED E-05's PRESCRIBED MECHANISM rather than assuming it, because a test approach that
cannot drive the code under test would have been a blocker. A three-module fixture tree in a temp dir
plus an `rfs.package_dir` override drives `module_tree`, `module_index`, `_value_differs` AND
`census(None)` over the fixtures: a constants-only tree gave `co_defined=0`, and adding one co-defined
`def` gave `co_defined=1, real_forks=['f']`. `census` calls `repo_wide_sweep`, which globs the fixture
dir too, so a minimal tree is sufficient. One trap worth recording, which my own first probe hit:
`census` returns `co_defined` as an INT count, not a list, so a test reading it as a list raises
`TypeError: 'int' object is not iterable`. I noted that in E-05 so the executor does not lose a cycle
to it.

PR-001 IS THE FINDING THAT MATTERED AND IT CUTS BOTH WAYS. Re-measured one day after authoring, the
host-pair `UPPER_CASE` population is 18 rather than F-01's 19, and `DEPENDENCY_BLOCK_RECOVERY_HINT`
has been DELETED from all three modules: `rg` finds no assignment of it anywhere, `getattr` returns
absent on `oc_runipd`, `agy_runipd` and `runner_shared` alike, and `_value_differs` now returns `None`
(not answerable) where F-02 measured `True`. Ground truth is therefore ONE divergent host-pair
constant, `FULL_AUTO_ACTOR`, and the three-way matches-neither set is still empty.

That STRENGTHENS the plan's case: the closure section now flags ZERO divergent constants (8 real
forks, 91 distinct closure-reachable names, 0 flagged `VALUE-DIFFERS-PER-HOST`) while ground truth has
one, so coverage of this defect class has reached exactly zero, which is the end state F-04 predicts
and calls structural. It simultaneously BROKE the plan's bar: E-01 required "the 19 names measured in
F-01", E-02 required the divergent list to be "exactly
`['DEPENDENCY_BLOCK_RECOVERY_HINT', 'FULL_AUTO_ACTOR']`", and E-03 required a section naming "both
divergent names". All three would now FAIL against a correct implementation, and V-01/V-02/V-03
demanded the same literals as evidence. Per the re-derivation convention these are live-artifact
counts and belong in prose as context, never as the bar, so I restated each as an
agreement-with-ground-truth property re-derived in the execution lane, kept `FULL_AUTO_ACTOR` as the
one stable expectation (it is the symbol the docstring teaches with and the reason the section
exists), marked F-01, F-02, F-06 and F-09 stale-but-auditable with pointers to the new F-14, and put
the re-derivation hazard at the top of the gate rather than leaving it as a footnote.

PR-002 is the same class as PR-001 and the same remedy. F-12 recorded a pre-existing suite failure
(the `test_release_exempt_setter_roundtrip_and_parity` date-rollover assertion) and V-05 told the
executor to attribute failures against that baseline. Re-measured on a clean tree the suite is FULLY
GREEN: `3629 passed, 2 skipped, 3 warnings in 138.40s`, 208 deselected, and 149 tests larger than at
authoring. Left standing, that instruction would license waving a real regression through as the known
flake. Corrected in the Project-conventions bullet, Required tests and V-05, with F-12 marked
superseded and F-15 recording the new measurement.

PR-003 is a false premise an executor would have copied into code. E-01 described its three binding
shapes as "the three binding shapes `module_index` already handles", but `module_index`'s `ast.Assign`
arm binds only `if isinstance(target, ast.Name)` and walks no `ast.Tuple`/`ast.List` elements, so a
module-scope tuple unpack is invisible to it today. An executor following that sentence would have
looked for a handler to mirror and found none. E-01 now says to implement the tuple shape fresh and
records the consequence the plan had not considered: a tuple-unpacked name has no single RHS node, so
it cannot be resolved and belongs in E-02's `unresolved` set. Since the real population has no
instance (its one `ast.Tuple` is a tuple VALUE on a single `ast.Name` target), E-05 gains a fixture
for it and V-01 demands the transcript.

PR-004 is the gate. It was missing an open-questions statement and a scope fence, and its lifecycle
paragraph told the executor to perform the terminal transition without noting that a runner owns the
finalize when one is driving. All three added in place, along with the explicit
`Status`/`Readiness` statement.

ONE THING I DELIBERATELY DID NOT CHANGE. The plan's choice to keep the scanner a measuring instrument
rather than add a gate is correct and well argued: the docstring makes a nonzero exit a contract
violation, the enforcing guard already ships in `tests/test_runner_shared.py` from `gjni4c`, and
`90z361` (now `approved`, verified) extends it. I also confirmed no file collision with `90z361`,
whose `Scope-Paths` are the three `agent_workflows` modules plus `tests/test_runner_shared.py`, none
of which this plan touches.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G (live-artifact success criteria) | the plan's E-01, E-02, E-03 Expected outcomes and V-01, V-02, V-03; `agent_workflows/runner_shared.py` (three prose-only mentions of `DEPENDENCY_BLOCK_RECOVERY_HINT`, no assignment) | three expected-outcome literals are live-artifact counts that drifted in one day (population 19 -> 18, divergent set now `['FULL_AUTO_ACTOR']` alone because `DEPENDENCY_BLOCK_RECOVERY_HINT` was deleted from all three modules), so each would fail against a correct implementation | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Restated E-01/E-02/E-03 and V-01/V-02/V-03 as agreement-with-ground-truth properties re-derived in the lane, keeping `FULL_AUTO_ACTOR` as the one stable expectation; marked F-01/F-02/F-06/F-09 stale-but-auditable; added F-14; updated the Concern; led the gate with the re-derivation hazard |
| PR-002 | MEDIUM | IN-SCOPE | E (testing) / G | the plan's F-12, its Project-conventions bullet, Required tests and V-05 | F-12 pre-authorizes a suite failure that no longer occurs (re-measured `3629 passed, 2 skipped`, fully green), so the standing attribute-against-the-flake instruction would license waving through a real regression | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Marked F-12 superseded, added F-15 with the re-measurement, corrected all three executor-facing instructions to demand a re-derived baseline against a green bar |
| PR-003 | MEDIUM | IN-SCOPE | G (executability) / A | `tools/runner_fork_scan.py` `module_index`, whose `ast.Assign` arm binds only `if isinstance(target, ast.Name)` | E-01 attributes a tuple/list-target binding shape to `module_index`, which does not handle it, so an executor would look for a handler to mirror and find none; the plan also had not considered that a tuple-unpacked name has no single RHS to resolve | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now says to implement the shape fresh and route such names to `unresolved`; added F-16 with the RHS shape census showing no live instance; E-05 gains a fixture and V-01 the transcript |
| PR-004 | MEDIUM | UNDER-SCOPE | G (execution contract) | the plan's "Approval and execution gate" section | the gate lacked an open-questions statement and a scope fence, and instructed the terminal transition unconditionally, omitting that a runner owns the finalize when one is driving | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the open-questions statement, a declaration-style scope fence with genuinely-unsafe stop conditions, the explicit `Status`/`Readiness` statement, and conditional runner/executor finalize ownership |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's worked example (`DEPENDENCY_BLOCK_RECOVERY_HINT`) was deleted from the tree mid-flight; does the plan still have a premise worth executing? | Yes, and the premise is STRONGER: restate the bars and proceed | Mark the plan REPLAN as premise-stale; shrink it to a docstring correction only | Measured: the closure section now flags ZERO divergent constants while ground truth has one, which is precisely the zero-coverage end state F-04 predicts as structural, so the gap the plan closes is wider than at authoring rather than narrower. `FULL_AUTO_ACTOR` remains live and divergent and is reported in no section, so the plan's central deliverable still has a real subject | yes |
| D-2 | Should the plan's remaining numeric expectations be deleted, or kept as context with a re-derivation instruction? | Kept as context, with the bar restated as agreement with a lane-derived `getattr` ground truth | Delete every count; pin the review-time counts as the new literals | Pinning review-time counts would repeat the exact defect one day later, since this population demonstrably moves. Deleting them loses the executor's sanity check, and the plan's own method (comparing the tool against an independent `getattr` probe) is the right bar and was already present in V-02; I generalized it rather than inventing a mechanism | yes |
| D-3 | E-05 prescribes driving `census()` over fixtures via a `package_dir` override; verify it or trust it? | Verify it, and record the `co_defined`-is-an-int trap found while doing so | Trust the plan's assertion that the mechanism works | A test approach that cannot drive the code under test would have been a blocker, and the plan's own F-11 establishes there is no existing test to copy the pattern from, so nothing in-tree demonstrated it. My first probe misread `co_defined` as a list and raised `TypeError`, which is exactly the cycle an executor would have lost; recording it costs one sentence | yes |
