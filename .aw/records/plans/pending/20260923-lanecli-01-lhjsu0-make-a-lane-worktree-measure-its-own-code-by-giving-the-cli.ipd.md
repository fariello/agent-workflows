# IPD: Make a lane worktree measure its own code by giving the CLI and subprocess tests a tree-relative import root instead of the editable install's absolute main-checkout pin

- Date: 2026-09-23
- Kind: child
- Concern: THREE OPEN `high`/`Blocks-Release: next` BUGS ARE ONE DEFECT WITH THREE VICTIMS, AND IT IS LIVE AT HEAD `22cf67d9`. The editable install writes an ABSOLUTE path to the MAIN checkout (`_editable_impl_agent_workflows.pth` resolves `agent_workflows` to the main tree), and the `aw` console script runs under a fixed interpreter (its shebang names an absolute virtualenv `python3`, not a tree-relative one), so neither honors the tree it is invoked in. MEASURED FROM A LANE WORKTREE: `python3 -c "import agent_workflows; print(agent_workflows.__file__)"` run from a NEUTRAL cwd resolves to the MAIN checkout's `agent_workflows/__init__.py`, not the lane's. So `uin96r` ("the `aw` console script resolves `agent_workflows` from the main checkout, so a lane worktree's edits are invisible to CLI evidence"), `0vbdll` ("a lane worktree's own code is invisible to the installed `aw`, so an agent measures the main checkout and reports the wrong result") and `ccbe60` ("subprocess CLI tests run from a worktree silently exercise the MAIN checkout") are the same root cause seen from the CLI, the agent, and the test suite.
  WHY IT IS USUALLY INVISIBLE, WHICH IS WHAT MAKES IT DANGEROUS. From a lane's ROOT directory the current working directory precedes the editable path on `sys.path`, so the lane's own package wins and everything looks correct; I verified `agent_workflows.__file__` resolves INSIDE the lane when run from the lane root. Step outside the root, or let any tool run from a neutral cwd, and the resolution silently flips to main. A defect that behaves correctly in the common interactive case and incorrectly under a subprocess is exactly the shape that produces confidently wrong evidence.
  THE HARM IS FALSE EVIDENCE, NOT A CRASH, AND THE EXECUTION CONTRACT DEPENDS ON THE THING THAT IS BROKEN. `AGENTS.md` requires an agent to paste ACTUAL runner output and forbids claiming success it did not run; an agent in a lane that runs `aw <verb>` to demonstrate its change is, at that moment, exercising main's code and pasting main's behavior as proof of the lane's. The failure direction is the bad one: the change looks verified. `uin96r`'s own filing says it "silently produces FALSE EVIDENCE", and `ccbe60` generalizes it to the suite, where a subprocess CLI test asserts against a tree the test did not modify.
  I ALSO HIT A SECOND-ORDER SYMPTOM WORTH RECORDING, because it tells an executor the shadowing is real rather than theoretical. Importing from a lane SUBDIRECTORY loaded MAIN's `agent_workflows/__init__.py` while the lane's own `agent_workflows/selectors.py` shadowed the STDLIB `selectors` module, producing `AttributeError: module 'selectors' has no attribute 'SelectSelector'` from inside `subprocess`. That is two trees' code executing in one interpreter, which is a stronger statement than "the wrong tree wins".
  A FOURTH ITEM IS ADJACENT AND DELIBERATELY NOT CLAIMED HERE. `caf5ed` (`low`/`chore`) records that six scope-drift test arrangements dirty the MAIN checkout and "would pass vacuously under lane-scoped measurement". It is a consequence of the same confusion but its fix is test hygiene rather than import resolution, so it is named in the deferred section rather than absorbed.
- Scope: Make the tree a command runs in be the tree it measures, for the CLI and for subprocess tests. IN: (a) decide the mechanism per OQ-01 and implement it, so `aw` and `python3 -m agent_workflows` invoked anywhere inside a worktree resolve THAT worktree's package; (b) make subprocess CLI tests exercise the tree under test rather than the absolute pin (`ccbe60`); (c) add a guard test that FAILS if resolution silently falls back to another tree, since the defect's whole character is silence. OUT: `caf5ed`'s six scope-drift arrangements (test hygiene, not resolution); changing how the package is installed for END USERS, since a normal non-editable install has no second tree and no defect; and any change to `aw`'s repo-root resolution for RECORDS (`--dir`/`resolve_verb_repo_root`), which is a separate axis and is not what any of these three items measures.
- Scope-Paths: tests/test_lane_import_root.py, tests/support.py, conftest.py
- Item-Dependencies: none
- Status: to-review
- Set: lanecli
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: lhjsu0
- From-Backlog: uin96r
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from `uin96r` and covering `0vbdll` and `ccbe60`, which are the same root cause seen from the CLI, the agent and the suite; all three are `high`/`Blocks-Release: next` and the gate is INHERITED. Verified the defect live rather than trusting the filings: from a lane worktree with a neutral cwd, `agent_workflows` resolves to the MAIN checkout.
  THE MEASUREMENT THAT MATTERS MOST is the one that explains why this survived: from a lane's ROOT the cwd precedes the editable path so the lane wins and everything looks right, and only a neutral cwd or a subprocess exposes the flip. Any fix must therefore be tested from a NON-root cwd, or it will appear to work while changing nothing.
  I DELIBERATELY LEFT `- Scope-Paths:` WITHOUT A PRODUCTION MODULE, because OQ-01 has not been answered and the honest mechanism may be packaging configuration or a test-harness change rather than a code edit. Whoever executes must declare the file they actually touch before touching it, which the finalize scope gate will check.

## Goal

Make a command invoked inside a worktree measure that worktree's code, so CLI evidence an agent pastes is evidence about the change it made.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: characterize the resolution precisely

- [ ] E-01 MAP EXACTLY WHEN RESOLUTION FLIPS, before choosing a fix. The defect is conditional on cwd, and a fix aimed at the wrong condition will look successful.
  MEASURE FOUR CASES and paste all four: import from the lane ROOT; from a lane SUBDIRECTORY; from a NEUTRAL cwd outside every checkout; and through the `aw` CONSOLE SCRIPT rather than `python3 -m`. At authoring, the lane root resolved INSIDE the lane while a neutral cwd resolved to MAIN.
  RECORD THE TWO MECHANISMS SEPARATELY, because they need different fixes: the `.pth` file's ABSOLUTE path to the main checkout, and the console script's FIXED interpreter shebang. A change addressing only one leaves the other.
  REPRODUCE THE STDLIB SHADOWING, since it proves two trees can execute in one interpreter: import from a lane subdirectory and show the `selectors` collision (`AttributeError: module 'selectors' has no attribute 'SelectSelector'`). Note whether it still reproduces; if it does not, say so.
  CONFIRM `ccbe60`'s SUITE CLAIM CONCRETELY: find a subprocess CLI test and show which tree its child process imports. Do not infer it from the `.pth` file.
  - Depends on: none
  - Expected outcome: a four-case resolution table with pasted output, the two mechanisms named separately, the shadowing reproduced or reported absent, and one named subprocess test shown to exercise the wrong tree.
  - Execution state: pending

### Task group 2: make the tree authoritative

- [ ] E-02 IMPLEMENT THE CHOSEN MECHANISM, per OQ-01, so an invocation inside a worktree resolves that worktree's package from ANY cwd within it.
  DO NOT FIX THIS BY TELLING AGENTS TO RUN `python3 -m agent_workflows` FROM THE LANE ROOT. That is the current accidental behavior, it is what made the defect invisible, and an instruction cannot hold: `AGENTS.md` already asks agents to paste real CLI output and this defect silently falsifies it. A fix must be mechanical.
  IT MUST NOT BREAK A NORMAL INSTALL. An end user with a single non-editable install has no second tree and no defect; whatever is added must be inert there. State how you verified that, not merely that you intended it.
  IT MUST FAIL LOUDLY, NEVER FALL BACK SILENTLY. If the tree-relative root cannot be determined, the honest outcome is an error naming the ambiguity, because a silent fallback to main is precisely the defect. This is the single most important property of the fix.
  PREFER A SEAM THAT ALSO COVERS SUBPROCESSES, since `ccbe60`'s victims are child processes that inherit an environment rather than a Python-level `sys.path` edit made in the parent.
  - Depends on: E-01
  - Expected outcome: from every cwd inside a worktree, `aw` and `python3 -m agent_workflows` resolve THAT tree's package; a normal single-tree install is provably unaffected; an undeterminable root errors rather than falling back.
  - Execution state: pending

- [ ] E-03 MAKE SUBPROCESS CLI TESTS EXERCISE THE TREE UNDER TEST (`ccbe60`). A test that spawns the CLI must assert against the tree it modified, or it is asserting about main.
  FIND THE SHARED SPAWN HELPER FIRST and fix it once. `tests/support.py` is the likely home; if each test spawns ad hoc, say so, because that changes the size of this item and may warrant splitting.
  A TEST THAT PASSES BOTH BEFORE AND AFTER PROVES NOTHING HERE. `ccbe60` says these tests "silently exercise the MAIN checkout", so at least one must be shown to change behavior under the fix, or the claim is unverified.
  - Depends on: E-02
  - Expected outcome: subprocess CLI tests provably exercise the tree under test, with at least one test demonstrated to have been measuring main before the change; the spawn path is fixed in one shared place if one exists.
  - Execution state: pending

### Task group 3: keep it fixed

- [ ] E-04 ADD A GUARD THAT FAILS ON SILENT CROSS-TREE RESOLUTION. Nothing today would notice a regression, which is why three separate items had to be filed by hand after three separate incidents.
  ASSERT THE PROPERTY, NOT THE IMPLEMENTATION: that a command invoked inside a tree resolves that tree's package. A test pinned to the `.pth` file's contents or a specific `sys.path` index would pass while the property broke.
  RUN IT FROM A NON-ROOT CWD, because from the lane root the buggy and fixed behavior are indistinguishable (E-01). A guard written from the root would be vacuous, which is the same class of defect as the role-guard test in `rolevac` `8i0xa7`.
  - Depends on: E-02, E-03
  - Expected outcome: a guard test failing against pre-E-02 code and passing after, exercised from a NON-root cwd, asserting the property rather than the mechanism.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE EXECUTION CONTRACT DEPENDS ON CLI EVIDENCE: `AGENTS.md` requires pasting actual runner output and forbids claiming unrun success. This defect silently falsifies exactly that evidence, which is why three `high` bugs point at it.
- LANE WORKTREES ARE THE NORMAL EXECUTION MODE: `aw oc run` isolates each item in its own worktree by default, so "measured in a lane" is the common case and not an edge case.
- `agent_workflows/selectors.py` SHADOWS THE STDLIB `selectors` MODULE when two trees mix in one interpreter, which is both a symptom to test for and a hazard for any fix that manipulates `sys.path` rather than the interpreter's root.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `_editable_impl_agent_workflows.pth`, the `aw` console script | The editable install pins an ABSOLUTE path to the MAIN checkout and the console script runs under a fixed interpreter, so neither honors the invoking tree. | from a lane worktree with a neutral cwd, `agent_workflows.__file__` resolves to the MAIN checkout's `__init__.py` |
| F-2 | HIGH | resolution order | The defect is cwd-conditional: from a lane ROOT the cwd precedes the editable path so the lane wins and the bug is invisible; a neutral cwd or a subprocess flips it to main. Any fix or guard tested only from the root proves nothing. | lane-root import resolved inside the lane; neutral-cwd import resolved to main |
| F-3 | HIGH | two trees in one interpreter | Importing from a lane SUBDIRECTORY loaded MAIN's `__init__.py` while the LANE's `agent_workflows/selectors.py` shadowed the stdlib, crashing inside `subprocess`. Two trees' code executed in one process. | `AttributeError: module 'selectors' has no attribute 'SelectSelector'`, naming the lane's `selectors.py` as the shadow |
| F-4 | HIGH | subprocess CLI tests (`ccbe60`) | Tests that spawn the CLI assert against the tree the absolute pin selects, not the tree they modified, so a lane-local change is untested and a main-local change is silently credited. | `ccbe60`'s filing; to be confirmed per-test by E-01 |
| F-5 | MED | three separate backlog filings | Nothing detects this class, which is why `uin96r`, `0vbdll` and `ccbe60` were each filed by hand after separate incidents. A guard is part of the fix, not a nicety. | three independent items, same root cause |

## Proposed changes (ordered, validatable)

1. E-01 produces the four-case resolution table and names the two mechanisms separately.
2. E-02 makes the invoking tree authoritative from any cwd within it, inert for a normal install, erroring rather than falling back.
3. E-03 makes subprocess CLI tests exercise the tree under test, proving at least one was measuring main.
4. E-04 adds a non-root-cwd guard that fails on silent cross-tree resolution.

## Deferred / out of scope (with reason)

- `caf5ed`'s SIX SCOPE-DRIFT ARRANGEMENTS that dirty the MAIN checkout and "would pass vacuously under lane-scoped measurement". Same confusion, but the fix is test hygiene rather than import resolution; keeping it separate avoids coupling a `low`/`chore` cleanup to three `high` bugs.
- CHANGING THE INSTALL FOR END USERS. A single non-editable install has one tree and no defect; widening to packaging policy would risk shipped behavior to fix a developer-and-agent problem.
- `aw`'s RECORDS ROOT RESOLUTION (`--dir`, `resolve_verb_repo_root`). A different axis: which repo's RECORDS a verb reads, not which tree's CODE executes. None of the three items measures it, and conflating them would grow scope without evidence. (Note `oii7hd` separately reports a records-root defect; it is not this.)
- INSTRUCTING AGENTS TO RUN FROM THE LANE ROOT. E-02 states why: it is the accidental behavior that hid the defect, and instruction cannot enforce it.

## Scope check

- Over-scope: `- Scope-Paths:` deliberately lists NO production module, because OQ-01 may resolve to a packaging or harness change. Whatever file E-02 actually edits MUST be declared before the edit; do not let the finalize scope gate discover it.
- Under-scope: if E-02's mechanism requires touching `agent_workflows/__init__.py` or the packaging configuration, those are undeclared today and must be added deliberately, with the reason recorded, rather than quietly widened.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- E-04's guard MUST be demonstrated FAILING against pre-E-02 code, exercised from a NON-root cwd. Per F-2 a guard run from the lane root cannot distinguish fixed from broken.
- E-03 MUST name at least one subprocess test whose behavior changes under the fix; if none does, `ccbe60`'s claim is unconfirmed and that must be reported rather than assumed.
- Verify a normal single-tree install is unaffected, and state how it was verified rather than asserting intent.

## Spec / documentation sync

- If E-02 changes how the CLI resolves its own package, `AGENTS.md`'s evidence guidance and any developer-setup documentation describing the editable install should record it, since the current silent behavior is what agents have been reasoning against.
- No `.spec.md` edit is anticipated. If OQ-01's answer changes a documented run or host contract, declare that spec file in `- Scope-Paths:` before editing, per the spec-amendment rule.

## Open questions

### OQ-01: Which mechanism makes the invoking tree authoritative?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer if it changes packaging
- Resolution or deferral rationale: NOT blocking, because E-01's measurement constrains the choice and E-02 requires the fail-loudly property whichever is chosen, so the plan terminates correctly either way. Candidates, each with a real cost. (a) A `PYTHONPATH`-style environment root exported by the runner for lane subprocesses: covers `ccbe60`'s child processes naturally, but only helps runner-spawned work, not a human typing `aw` in a lane. (b) A tree-relative resolution inside the console entry point: covers every invocation, but must not reintroduce F-3's stdlib shadowing and must stay inert for a normal install. (c) A per-worktree editable install: conceptually cleanest and needs no code, but multiplies install state per lane and the runner creates lanes constantly. Recommend measuring (b) first since it covers the most invocations, and note that (a) may be needed ALONGSIDE it for subprocesses regardless.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the four-case table pasted (lane root, lane subdir, neutral cwd, console script) showing which tree each resolves; the two mechanisms named; the stdlib shadowing reproduced or reported absent; one named subprocess test shown to exercise the wrong tree.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted resolution from at least TWO non-root cwds inside a lane, both selecting the lane's package; a demonstration that an undeterminable root ERRORS rather than falling back to main; and the stated method by which a normal single-tree install was verified unaffected.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the named subprocess test pasted BEFORE (exercising main) and AFTER (exercising the tree under test); if the shared spawn helper was fixed, the symbol name; if no test changed behavior, that reported explicitly as an unconfirmed claim.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the guard pasted FAILING against pre-E-02 code and PASSING after, with the command showing a NON-root cwd; plus the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, declaring any additional file OQ-01's answer requires before editing it, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
