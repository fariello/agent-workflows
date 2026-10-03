# Review findings: plan 2kyw59

- Subject-Id: 2kyw59
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `72b8d317c`. The plan file was committed and clean
(`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

I RE-DERIVED EVERY LOAD-BEARING MEASUREMENT INDEPENDENTLY rather than trusting the plan's findings, and
the plan's CLASSIFICATION is sound and is its real contribution. The three-class reading of the backlog
item's census reproduces exactly:

- F-02 reproduces: on a bare run directory `recorded_outcome_path` returns `.../run/outcomes/01-abc123.json`
  with `outcomes/ exists after: False`, and `read_recorded_outcome` returns `None` with the directory
  still absent. The readers are pure.
- F-03 reproduces by reading the bodies: `perform_defect_reask` passes `outcome_path` only to
  `read_defect_report_outcome`, and `read_defect_report_outcome` opens `if not path.is_file(): return None`.
  Neither writes.
- F-04 reproduces end to end: collecting into a bare run directory gave `run_dir/outcomes exists BEFORE
  collect: False` then `AFTER collect: True`, submission `outcome` with `result: collected`, and the
  destination re-read as `{"disposition": "executed"}`. `_copy_file`'s first statement really is
  `destination.parent.mkdir(parents=True, exist_ok=True)`.
- F-05 reproduces: with `lane_root=None`, `prompt_outcome` is the absolute `.../run/outcomes/01-abc123.json`,
  `lane_submission_root` and `lane_outcome` are both `None`, and `run_dir/outcomes exists after
  prepare_lane_submission_dir: False`.
- F-06 reproduces: `build_verifier_prompt` computes both paths itself and leaves `outcomes/` absent for
  `audit=False` (prompt len 5154) and `audit=True` (prompt len 6774).
- F-07 reproduces: an AST enumeration of `handle_audit_command`'s filesystem calls returns exactly
  `atomic_write_json` twice, the `(run_dir / sub).mkdir` loop, `write_prompt`, `allocate_isolation_worktree`,
  and `candidate.read_text`. It never writes the verdict.
- F-08 reproduces: the loop is verbatim at `runner_shared.py` beside `mint_run_dir`, and the `resume`
  branches in both hosts load state and call `run_queue` directly, reaching no initializer.

SO THE PLAN'S ANSWER TO THE BACKLOG ITEM IS CORRECT AND BETTER THAN EITHER OPTION THE ITEM OFFERED. What
I found instead are three problems in HOW it executes that answer, one of which is a real defect in the
prescribed code.

PR-001 IS THE ONE THAT MATTERS AND IT IS A DEFECT IN THE PRESCRIBED FIX, NOT A DOCUMENTATION GAP. E-01
told the executor to write `Path(paths.prompt_outcome).parent.mkdir(parents=True, exist_ok=True)` and
justified it on the premise that `prompt_outcome` "is already an absolute driver-side path on that branch
by construction". That premise is true only on the NON-ISOLATED branch, and the guard E-01 reused
(`if paths.lane_submission_root is None or paths.lane_outcome is None`) is not what separates the two: on
the ISOLATED branch `project_worker_paths` returns `prompt_outcome` as a LANE-RELATIVE string, measured as
`.aw/state/lane-submissions/r1/01-abc123/attempt-1/outcomes/01-abc123.json` with `is_absolute: False`. I
ran that exact expression under a throwaway cwd and it created SEVEN directories there. The plan's own
validation could not have caught it: `.aw/.gitignore:62` ignores `/state/`, so the pollution never appears
in `git status`, and E-04(b) asserts only that `run_dir/outcomes` is absent, which stays true while the
junk tree is created somewhere else entirely. I then applied the corrected form (branch on
`paths.lane_root is None`, guard the `mkdir` with `is_absolute()`), re-measured, and confirmed the
non-isolated parent is created, the isolated `run_dir/outcomes` stays `False`, nothing is created relative
to cwd, and `tests/test_defect_report.py tests/test_attempt_lane_facts.py` gives `30 passed`. Both halves
are required and E-04(f) now pins them; the probe patch was reverted and `git diff --stat` confirmed empty.

PR-005 IS THE COROLLARY AND IS WHY PR-001 IS NOT SELF-FIXING. E-04's five cases were chosen against the
hazards the AUTHOR anticipated, and none of them can observe a cwd-relative side effect: (a) and (d) check
a directory now exists, (b) and (c) check a directory does not exist under `run_dir`, (e) checks a file
landed. A reviewer who fixed only E-01 would ship a correct statement with no test standing behind it, and
the next refactor that "simplifies" the two-condition guard back to one would reintroduce the defect
silently. Test (f) is therefore added, with the third mutation in the negative-control list to prove it
load-bearing against the SUPERSEDED form specifically.

PR-002 IS AN UNDISCLOSED BEHAVIOR CHANGE THAT THE SUITE CANNOT SURFACE. E-02 makes a prompt BUILDER touch
the filesystem, which the plan rightly flags as its one arguable choice, but it did not measure the cost.
Two existing callers pass a fabricated `run_dir`: `tools/ipdrunner/test_runagy.py` passes `Path("/tmp/run")`
and `tests/test_defect_report.py::PromptDemandTests._prompt` passes `Path("/tmp/r")`. With E-02 applied I
observed both `/tmp/run/outcomes` and `/tmp/r/outcomes` created on this machine, both having been absent.
Neither test FAILS, so nothing in the suite reports it, and `pyproject.toml`'s `testpaths = ["tests"]` means
a bare run never even collects the first one. I did not reject the design (the ownership argument is sound
and the alternatives genuinely are worse) but a function that materializes a directory under a path a
caller only NAMED must say so where the approver reads, so it is now disclosed in E-02, recorded as F-13,
and demanded by V-02.

PR-003 IS AN OVERCLAIM OF WHAT THE PLAN BUYS. The Goal and gate read as though two live gaps are being
closed, and `z3ifg8`'s successfully-reviewed precedent reinforces that reading, because ITS defect was a
reproducible `FileNotFoundError`. Neither of this plan's gaps is reachable at this head:
`handle_audit_command` runs its three-directory loop 41 lines before it calls `build_verifier_prompt`, and
`prepare_lane_submission_dir` is reached only from `build_prompt`, which runs inside a run that
`initialize_run_core` already initialized. The backlog item says this plainly ("not a live crash") and the
plan did not carry that forward. It matters for approval, not for correctness: a maintainer pricing a
`low`/`chore` robustness change should not be reading it as a bug fix.

PR-004: F-09's baseline was already stale. The authoring figure was `3506 passed, 2 skipped` two days ago;
a bare run at review HEAD gives `3538 passed, 2 skipped, 3 warnings in 72.24s`. The plan's own F-09 prose
told the executor to re-derive, but the validation section and V-04 then set `3506 plus the new module's
count` as the BAR, which is a live-artifact count used as an acceptance criterion and is the exact pattern
the workflow's re-derivation convention forbids. Also corrected: the quoted `addopts` omitted
`and not livecorpus`, which the shipped value carries.

WHAT I DID NOT WEAKEN. The three-class classification is the plan's contribution and I confirmed all of it
rather than trimming any of it. The refusal to put a mkdir in any reader is correct and well-grounded, in
`recorded_outcome_path`'s own "OPPOSITE answers" docstring, in spec `7ckptx` R2.4/R2.5, and in
`run_analytics_sources.read_outcomes`'s `if not base.is_dir()` early return; E-03's docstring deliverable is
the right carrier for it and I strengthened nothing away. OQ-01's "keep the loop" resolution is correct and
independently verified. I also added the cross-reference the plan was missing in the other direction:
pending sibling `z8ex9f` F-02 explicitly depends on `prepare_lane_submission_dir` leaving an EMPTY lane-side
tree, so E-01's prohibition on over-creating protects a sibling as well as a spec requirement.

ONE INCIDENTAL CORRECTION, recorded rather than filed as a finding: E-04's fixture guidance worried that
`build_verifier_prompt` with `audit=True` would need a `state["audit"]` payload. It does not; a bare
`state = {"run_id": "run-test"}` rendered the full 6774-char audit prompt, so (d) can use one minimal
`state` for both arms. Added to E-04's fixture note.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness (the prescribed statement has an unsafe branch) | `lane_containment.project_worker_paths` returns `prompt_outcome=f"{rel_root}/{outcomes_rel}"` on the isolated branch, measured as `.aw/state/lane-submissions/r1/01-abc123/attempt-1/outcomes/01-abc123.json` with `is_absolute: False`. Running E-01's prescribed `Path(paths.prompt_outcome).parent.mkdir(parents=True, exist_ok=True)` under a throwaway cwd created 7 directories there. `.aw/.gitignore:62` ignores `/state/` | **E-01's prescribed expression creates a bogus directory tree under the PROCESS CWD whenever it is reached with isolated paths, and the pollution is invisible to `git status`.** The guard E-01 reused does not separate the branches on the property that matters: `lane_submission_root`/`lane_outcome` are non-`None` exactly when `prompt_outcome` is RELATIVE, so any reordering of those fields reaches the unsafe path. E-01's justification ("already an absolute driver-side path on that branch by construction") is true of the branch it intended and false of the string it dereferences | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now prescribes the explicit `if paths.lane_root is None:` branch with an `is_absolute()` guard, given as a code block, with both halves explained as load-bearing. The corrected form was applied and measured at review (non-isolated parent created, isolated `run_dir/outcomes` still `False`, cwd untouched, `30 passed`), then reverted. New F-12 records it; the negative fence adds the prohibition; E-04 gains case (f) and V-01 requires the cwd transcript |
| PR-002 | MEDIUM | IN-SCOPE | C. Architecture (an undisclosed purity change the suite cannot catch) | `tools/ipdrunner/test_runagy.py::test_concurrent_work_statement_in_prompts` passes `Path("/tmp/run")`; `tests/test_defect_report.py::PromptDemandTests._prompt` passes `Path("/tmp/r")`. With E-02 applied, running them created `/tmp/run/outcomes` and `/tmp/r/outcomes`, both previously absent, and both suites still passed. `pyproject.toml` sets `testpaths = ["tests"]` | **E-02 makes a pure prompt builder materialize a directory under any path a caller merely NAMES, and two existing callers name fabricated ones.** The plan identified E-02 as its one arguable choice but never measured the cost, so an approver weighing it was shown the argument and not the consequence. No test fails, so the suite will never surface it, and one of the two callers is outside `testpaths` and is never collected by a bare run | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now discloses the impurity and the two measured call sites, states why it is accepted rather than hidden, and notes that `tools/ipdrunner/` is outside `testpaths`. New F-13 records the measurement. V-02 requires the executor to state the impurity in one sentence and report whether the two fabricated paths gained a directory, framed as a disclosure whose expected answer is yes. E-04 gains the rule that every fixture path be a `tempfile` path so the module does not add a third instance |
| PR-003 | MEDIUM | IN-SCOPE | G. Plan executability (the gate overstates what the change buys) | `oc_runipd.handle_audit_command` runs `for sub in ("outcomes", "prompts", "sessions")` 41 lines before its `build_verifier_prompt` call; `initialize_run_core`'s three-directory loop runs immediately after `mint_run_dir` and before any prompt build; `prepare_lane_submission_dir` is reached only from `runner_shared.build_prompt`. Backlog `3kr193`: "no known caller is currently broken. This is the symmetry question, not a live crash" | **Neither gap this plan closes is reachable on a shipped path, and neither the Goal nor the approver-facing summary said so.** The sibling precedent makes the omission actively misleading, because `z3ifg8` fixed a reproducible `FileNotFoundError` and this plan presents itself in the same frame. A maintainer approving a `low`/`chore` item should be pricing robustness, not a defect | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal gains a "WHAT THIS PLAN DOES NOT BUY" paragraph naming both pre-creating callers and the item's own "not a live crash", and stating that the value is removing the ordering dependency rather than avoiding a crash. New F-14 records the reachability measurement. The approver summary gains the same correction, so the gate and the Goal agree |
| PR-004 | LOW | IN-SCOPE | E. Testing (a live count used as an acceptance criterion) | Authoring F-09: `3506 passed, 2 skipped` at `eb9ef3f62`. Re-measured at review HEAD `72b8d317c`: `3538 passed, 2 skipped, 3 warnings in 72.24s`. Shipped `addopts` is `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'` | **The validation section and V-04 set "no fewer than the F-09 baseline of 3506 plus the new module's count" as the bar, and that number was stale within two days.** F-09's own prose correctly said to re-derive, so the plan contradicted itself, and the stale half is the one an executor is graded against. The quoted `addopts` also omitted `and not livecorpus` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 now carries both measurements, labels the number as context, and says to compare failure sets by node id. The validation bullet and V-04 now require ZERO FAILURES plus a freshly re-derived pre-change baseline and node-id comparison, with no numeric bar. `addopts` quotation corrected |
| PR-005 | MEDIUM | UNDER-SCOPE | D. Anti-regression (no test can observe the PR-001 hazard) | E-04's five cases assert only on `run_dir`-relative existence ((a), (b), (d)), reader purity under `run_dir` (c), and a landed file (e). None observes the process cwd, and `.aw/state/` being gitignored means `git status` cannot either | **With PR-001 fixed, nothing would have pinned the fix, so the next simplification of the two-condition guard would reintroduce a cwd-polluting defect silently.** The plan's own negative-control discipline is the right instinct and its case list predates the hazard, so the gap is in coverage rather than in method | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 gains case (f): an ISOLATED `prepare_lane_submission_dir` run with cwd set to a throwaway empty directory must leave that directory EMPTY, asserted on the directory LISTING rather than on one hardcoded name, with `contextlib.chdir` or a `try/finally` so a failure cannot strand the suite. The negative-control list gains a THIRD mutation (restore the superseded unguarded form, show (f) failing) and now requires six pasted outcomes; V-04 requires naming which test failed under each of the three mutations; the "wrong to execute" list covers (f) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: the parent must come from somewhere. Guard the string derivation, or grow `prepare_lane_submission_dir`'s signature to take `run_dir` and `item` and recompute the path? | GUARD the string derivation: branch on `paths.lane_root is None` and require `is_absolute()` | (a) Add `run_dir` and `item` parameters and recompute `run_dir / "outcomes" / item_slug(item)`, eliminating the relative-string hazard by construction; (b) add the `is_absolute()` guard alone without changing the branch predicate; (c) add a new absolute field to `WorkerPaths` | Option (a) is the cleanest in isolation and I rejected it on blast radius: `WorkerPaths` is constructed in exactly two places and `prepare_lane_submission_dir` has exactly one caller (`runner_shared.build_prompt`), so the change is small, but it moves a signature in a spec-governed module (`7ckptx` R2.6 declares the shared-code home) for a plan whose whole merit is narrowness, and it would put `runner_shared`'s call site in scope for a second edit. Option (b) leaves the branch keyed on two fields whose nullity is incidental to the property being tested, so a later reader cannot see WHY the guard is there; the measured hazard is precisely that the existing guard looks sufficient. Option (c) widens a NamedTuple every caller destructures for one internal use. The chosen form states the predicate the code actually depends on (`lane_root is None` means non-isolated) and asserts the invariant separately (`is_absolute()`), so each half is independently readable, and E-04(f) makes removing either one fail. Both halves verified at review against the real functions | yes |
| D-2 | PR-002: E-02 makes a prompt builder impure for every caller, including two that pass fabricated paths. Accept with disclosure, move the mkdir to the launch sites, or reject? | ACCEPT with disclosure, and require the executor to report the measured side effect | (a) Move the mkdir to each `spawn_verifier`/launch call site, keeping the builder pure; (b) reject E-02 and leave the verifier path relying on `handle_audit_command`'s existing loop; (c) accept silently, since no test fails | Option (a) was the plan's own stated alternative and it really is worse here, but for a reason worth recording precisely: the in-run verifier prompt is built inside `_run_verifier_turn` and the audit prompt inside `handle_audit_command`, which are different functions in different modules, so "the launch site" is two sites and one of them is the host-specific file the scope fence correctly forbids touching. Option (b) abandons the plan's answer to the backlog item, which is sound. Option (c) is the finding: an impurity no test can observe is exactly the kind of change that must be written down, because the next reader's only evidence will be the prose. Disclosure keeps the accepted cost auditable without widening scope, and V-02 now makes the executor re-measure it rather than take my word | yes |
| D-3 | PR-005: should case (f) assert that no `.aw` directory appears under cwd, or that the cwd listing is empty? | Assert the LISTING is empty | (a) Assert `not (Path.cwd() / ".aw").exists()`, naming the directory the measured hazard creates; (b) assert on a recursive glob count | Option (a) pins the CURRENT lane layout rather than the property, and the property is "creates nothing relative to cwd". If `lane_submission_root` ever stops nesting under `.aw/state/`, the named assertion keeps passing while the hazard returns under a different prefix, which is the same class of mistake as pinning a filename instead of a behavior. An empty-listing assertion cannot be satisfied by relocating the junk. Option (b) is equivalent but noisier. The directory used must be a fresh throwaway so "empty" is meaningful, which E-04(f) states | yes |
| D-4 | PR-004: F-09's number is stale. Update it to the review measurement, or remove the numeric bar? | Keep BOTH numbers as context and remove the numeric BAR entirely | (a) Replace 3506 with 3538 and keep "no fewer than the baseline plus the new module's count"; (b) delete the figure altogether | Option (a) reproduces the defect on a two-day clock: the suite total is a live population that every merged lane moves, and this plan will sit in `pending/` awaiting human approval, so any number written now is wrong by execution. The workflow's own re-derivation convention names this exact pattern. Option (b) loses useful context, since knowing the tree was green at both authoring and review is what makes "any new failure is attributable to this plan" a sound inference. Keeping both figures as CONTEXT while making the criterion "zero failures, compared by node id against a freshly re-derived baseline" preserves the inference and removes the drifting bar | yes |
