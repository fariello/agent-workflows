# IPD: Make an explicit --dir at a non-project directory refuse instead of printing an empty board

- Date: 2026-09-29
- Kind: child
- Concern: `aw attention --dir <a git-but-not-AW directory>` prints `0 artifacts shown` and exits 0, which reads as "this repository has nothing needing attention" when the truth is "there is no AW project here and nothing was surveyed". The cwd path answers the SAME condition honestly (exit 3, prose naming where it looked and offering `aw install`), so the defect is not a missing message but a guard that skips the message it already has: `attention.run` reads `if not explicit_dir and not is_project_dir(repo_root)`, and the `not explicit_dir` conjunct switches the honest refusal OFF for exactly the operator who named the directory explicitly. `aw ipd board` carries the identical guard and the identical defect. Measured at base `9434331c`, all three surfaces greenwash: human prints `0 artifacts shown` rc=0, `--agent` emits `outcome:clean, exit:0, verified:true, complete:true, findings:0`, and `--check` asserts `the view is valid` rc=0. The `--agent` case is the most consequential, because a consumer forbidden by `docs/cli-output-contract.md` from inferring completion from prose reads a clean audit of a directory that was never surveyed.
- Scope: IN: (a) delete the `not explicit_dir` conjunct from the no-project guard in `attention.run`, so an explicit `--dir` at a non-project directory takes the same honest refusal the cwd path takes; (b) the identical one-conjunct fix in `cli._run_plans` (`aw ipd board`), because it is the same guard, the same three surfaces, and the same greenwash, and fixing one of two identical siblings would leave the asymmetry this plan exists to remove; (c) fix the `--check` sub-branch inside that guard, which is the ONE surface the conjunct deletion does not make honest: it asserts `the view is valid` with exit 0 on a directory it never surveyed, a false positive under the anti-greenwashing invariant, and must refuse `cannot-run`/exit 2 like the sibling machine path; (d) a behavior test pinning all surfaces of both verbs for an explicit non-project `--dir`; (e) correcting the THREE stale citations of the deleted test file `tests/test_awretrofit_project_root_climb.py` in `attention.py` and `project_context.py`, which are the evidence this plan had to re-derive and which currently point a reader at nothing. OUT: changing what counts as a project (`find_project_root` stays git-blind); converting the ~74 other `resolve_verb_repo_root` call sites that fall back to cwd silently (the recorded open design question, carried not fixed); the missing `--dir` SUBDIRECTORY climb (F-05, a second defect found while measuring, carried to its own item); the runs-root leak (F-06, likewise); and any change to the message wording, exit codes, or `NextAction` payloads the cwd path already emits, which are correct and are the reference this plan brings the `--dir` path into line with.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/cli.py, agent_workflows/project_context.py, tests/test_attention_explicit_dir_nonproject.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: xnb551
- Blocks-Release: next
- Set: xnb551
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: oq4ual

## Workflow history

- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog xnb551. The item's one-line summary is CONFIRMED and three things were added from measurement: `aw ipd board` carries the identical guard (F-02), the `--check` surface stays greenwashed after the obvious one-conjunct fix and needs its own change (F-03), and the candidate fix was applied and the full suite run green before authoring, so the blast radius is measured rather than guessed (F-04). Two further defects were found and are CARRIED, not folded in (F-05, F-06). The test file three source comments cite as locking this behavior does not exist (F-07).
- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw attention` and `aw ipd board` tell the truth when an operator points them at a directory that is not an AW project. After this plan, an explicit `--dir` at a non-project directory produces the same honest refusal the cwd path already produces on every surface (human prose and exit 3, `--agent`/`--json` `cannot-run` and exit 2, `--check` refusing rather than certifying), and a behavior test keeps all six surfaces honest.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm the premise at the execution base

- [ ] E-01 Reproduce the defect at the execution base on a directory OUTSIDE this repository, and capture the cwd path's honest answer beside it as the reference this plan copies. Create a throwaway git-but-not-AW directory and a non-git directory outside the repo tree, then for EACH run `aw attention --dir <d>` on the three surfaces (bare, `--agent`, `--check`) and record the exit code and first stdout line. Then run the SAME three surfaces with no `--dir`, with cwd set to that directory, and record the same. THE DIRECTORY MUST BE OUTSIDE THIS REPOSITORY: a target under `.aw/state/` is still inside the outer project, so `--dir` there surveys the OUTER repository's records and reports its lanes, which looks like a different bug and hides this one (measured at authoring; see F-06).
  - Depends on: none
  - Expected outcome: `--dir` greenwashes on all three surfaces (`0 artifacts shown` rc=0; `outcome:clean,exit:0,verified:true` ; `the view is valid` rc=0) while the cwd path refuses honestly on two of three (rc=3 with prose; `cannot-run` rc=2) and greenwashes only on `--check`. STOP AND REPORT if `--dir` already refuses: the premise would be stale and this plan wrong.
  - Execution state: pending

### Task group 2: Make the guard honest

- [ ] E-02 In `agent_workflows.attention.run`, change the no-project guard from `if not explicit_dir and not is_project_dir(repo_root):` to `if not is_project_dir(repo_root):`, deleting ONLY the `not explicit_dir` conjunct. Change nothing inside the guard's body on this item: the message, the exit codes (human 3, machine 2), the sanitized summary, and the `NextAction` install offer are all correct and are what the cwd path already emits. Leave the two-surface asymmetry (human 3, machine 2) exactly as it is; it is a deliberate shipped contract recorded in the branch's own comments and pinned by `NoProjectAgentEnvelopeTests`.
  - Depends on: E-01
  - Expected outcome: an explicit `--dir` at a non-project directory now reaches the same refusal the cwd path reaches; `git diff` shows one changed line in this file.
  - Execution state: pending
- [ ] E-03 Make the same one-conjunct change in `agent_workflows.cli._run_plans`, from `if not explicit_dir and not is_project_dir(root):` to `if not is_project_dir(root):`, for `aw ipd board`. This is in scope because it is the SAME guard with the SAME three surfaces and the SAME greenwash (F-02), measured at authoring, and because the two verbs are the only two that emit `no_project_message` at all, so leaving one unfixed recreates the inconsistency this plan removes. As in E-02, change nothing inside the body.
  - Depends on: E-01
  - Expected outcome: `aw ipd board --dir <non-project>` refuses like its sibling; `git diff` shows one changed line in `cli.py`.
  - Execution state: pending
- [ ] E-04 Fix the `--check` sub-branch inside `attention.run`'s no-project guard, which E-02 alone leaves greenwashed (F-03). Today that branch writes `aw attention --check: the view is valid.` with exit 0 (and a machine record with `outcome:clean, exit:0, verified:true, complete:true`) for a directory containing no project. Make it REFUSE instead: `cannot-run`, exit 2, `verified:false`, `complete:false` on the machine surfaces, and a human line on stderr saying it cannot validate a view of a directory that is not an AW project. SHAPE IT ON THE SHIPPED PRECEDENT IN THIS SAME FUNCTION, do not invent a fourth convention: `unresolved_selector_agent_record` already refuses `--check` combined with a selector matching nothing, using `kind:error, outcome:cannot-run, exit:2, verified:false, complete:false` and citing `EXIT_UNRESOLVED_SELECTOR = 2`, and its docstring states the reasoning this item reuses verbatim ("nothing was verified, and the answer is not complete, it is ABSENT"). Keep the summary PATH-FREE for the same leak reason the sibling branch documents: `agent_schema` refuses an absolute home path in any string field. NOTE this changes `--check` behavior for the CWD path too, from exit 0 to exit 2, which is intended: certifying a view of a non-project is the same false positive whichever way the directory was named.
  - Depends on: E-02
  - Expected outcome: `aw attention --check` at a non-project directory refuses with exit 2 on both the human and machine surfaces instead of asserting validity, and the machine record validates against `agent_schema`.
  - Execution state: pending

### Task group 3: Pin it, and repair the evidence trail

- [ ] E-05 Add `tests/test_attention_explicit_dir_nonproject.py`, a behavior test driving the real CLI and asserting on real exits and real output. It must cover, for BOTH a git-but-not-AW directory and a non-git directory created under `tmp_path`: (1) `aw attention --dir <d>` exits 3, writes the no-project prose to stderr, and writes NOTHING to stdout; (2) `--dir <d> --agent` exits 2, emits one `aw.agent/v1` record with `outcome:cannot-run`, `exit:2`, `verified:false`, `complete:false`, and passes `agent_schema.validate_agent_record` with zero findings; (3) `--dir <d> --format json` exits 2 with `status:cannot-run`; (4) `--dir <d> --check` exits 2 and does NOT contain `the view is valid`; (5) the same four for `aw ipd board` where the surface exists; (6) NO surface's stdout contains the tmp path or `/home/`, pinning the sanitization the sibling branch documents; (7) a POSITIVE control, so the test cannot pass by refusing everything: `--dir` at a directory that IS a real AW project still surveys it and exits 0 or 1 rather than refusing. Assert on exit codes, stdout, stderr and parsed records only; do NOT read `attention.py` or `cli.py` source with `inspect`, `ast`, regex, or substring search, and do NOT assert on line counts or symbol censuses (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: a new test file that FAILS on the base tree (the greenwash) and PASSES after E-02 through E-04, with the positive control passing in both states.
  - Execution state: pending
- [ ] E-06 Correct the three stale citations of the non-existent test file `tests/test_awstretrofit_project_root_climb.py` in the packaged source, using the exact spelling found at the base (see F-07 for the three sites: two comments in `attention.py`, one docstring in `project_context.py`). Each asserts a rule is "pinned" or "locked" by a file that does not exist, so a reader who tries to verify the claim finds nothing. Replace each with a citation of a test that ACTUALLY exists and pins the named rule, or, where none does, say plainly that the rule is unpinned. Do NOT invent a pin: if the git-blindness rule (`test_bare_git_ancestor_is_not_a_root`) has no live test, the honest text says so, and the gap is carried by F-07's item rather than papered over. Change comments and docstrings only; no behavior.
  - Depends on: E-05
  - Expected outcome: no source comment cites `tests/test_awretrofit_project_root_climb.py`; every remaining pin claim in the touched comments names a file that exists.
  - Execution state: pending

### Task group 4: Verify

- [ ] E-07 Verify nothing regressed and the carried findings are filed. Run the suite BARE as `python3 -m pytest`. Then re-run E-01's matrix and confirm every greenwash is gone. Then `aw sanitize --agent; echo rc=$?`. Then file the backlog items for F-05, F-06 and F-07 and replace this plan's `NEEDS-BACKLOG-ITEM` carrier placeholders with their id6 values.
  - Depends on: E-06
  - Expected outcome: suite green, matrix honest, sanitizer exit 0, three items filed and cited.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or by a quoted content string; a bare line number expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2). This plan cites `attention.run`, `cli._run_plans`, `project_context.resolve_verb_repo_root`, `is_project_dir`, `no_project_message` and quoted guard text; no finding depends on an offset.
- The three-state exit classification is normative: 0 clean, 1 domain findings, 2 usage error or cannot-run preventing domain inspection (`docs/cli-output-contract.md` Section 3). A non-project directory is a cannot-run, which is why E-04 refuses at 2.
- The anti-greenwashing invariant is explicit: "A record MUST NEVER report a positive outcome (`clean`, `ok`, `conforms`) for work that was `skipped`, `partial`, `unverified`, or `cannot-run`", and exit parity requires the embedded `exit` to equal the process exit code (`docs/cli-output-contract.md` Section 4). The base `--agent` record for a non-project `--dir` violates the first of these.
- The human/machine exit split on this condition is deliberate and shipped: human 3, machine 2, because `aw.agent/v1` admits only 0/1/2. Recorded at length in the guard's own comments and pinned by `tests/test_attention.py::NoProjectAgentEnvelopeTests`. This plan preserves it.
- Root detection is deliberately git-blind and must stay so: a `.aw/` tree can exist without git, and a bare `.git` ancestor with no AW marker is NOT a project (`project_context.find_project_root` docstring). This plan changes only what the FAILURE PATH does, never what counts as a project.
- Tests must exercise behavior and assert on real outputs, never read production source or count symbols (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16).
- Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md "HOW TO RUN THE SUITE").
- Commit through `aw commit oq4ual -- <paths>`; never `git add -A`, never `-a`, never push.

## Findings

| # | Location (base `9434331c`) | Finding |
| --- | --- | --- |
| F-01 | `agent_workflows.attention.run`, the guard `if not explicit_dir and not is_project_dir(repo_root):` | CONFIRMED EXACTLY AS THE BACKLOG ITEM STATES, and the cause is one conjunct. `resolve_verb_repo_root` honors an explicit `--dir` verbatim with no climb, which is correct, and then the guard's `not explicit_dir` conjunct makes the honest no-project refusal UNREACHABLE for precisely the operator who used `--dir`. Measured on a git-but-not-AW directory outside this repo: `aw attention --dir <d>` printed `0 artifacts shown` and exited 0; `--agent` emitted `{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`; `--check` printed `aw attention --check: the view is valid.` and exited 0. The SAME directory as cwd with no `--dir` exited 3 with the full prose on stderr including the `aw install` offer. A non-git directory behaves identically except the message omits the install offer. So the honest answer is already written, already sanitized, already has a machine record and a `NextAction`; the guard just declines to use it. |
| F-02 | `agent_workflows.cli._run_plans`, the guard `if not explicit_dir and not is_project_dir(root):` | NOT IN THE BACKLOG ITEM. `aw ipd board` has the IDENTICAL guard, one conjunct and all, and the identical defect. Measured: `aw ipd board --dir <non-project>` printed `CLEAN no plans found` and exited 0, and `--agent` emitted `outcome:clean, exit:0, verified:true`. These two verbs are the ONLY two in the package that call `no_project_message` at all, so they are the whole population of the honest-refusal behavior; fixing one and not the other would leave half the surface greenwashed and would make the next reader believe the difference was intentional. Added to scope as E-03. |
| F-03 | `attention.run`, the `if check:` sub-branch inside the no-project guard, writing `aw attention --check: the view is valid.` | THE OBVIOUS FIX IS INCOMPLETE, AND THIS IS THE MOST IMPORTANT FINDING FOR AN APPROVER. Deleting the conjunct (E-02) routes the explicit `--dir` case INTO this guard, and this guard then certifies the view as VALID with exit 0. Verified empirically with the candidate fix applied: `aw attention --dir <non-project> --check` still printed `the view is valid` and exited 0. Its in-source justification is "`--check` stays fail-closed-valid (nothing to violate)", which is the greenwash argument the anti-greenwashing invariant forbids: a check that surveyed nothing has not validated anything, and `--check` exists to be consumed by CI. The correct shape already exists ten screens away in the same module: `unresolved_selector_agent_record` refuses a `--check` whose selector matched nothing, with `cannot-run`/exit 2/`verified:false`/`complete:false`, and its docstring's reasoning transfers word for word ("nothing was verified, and the answer is not complete, it is ABSENT"). Added as E-04. Note this makes E-04 the one item in this plan that changes behavior for the CWD path as well. |
| F-04 | whole suite | THE BLAST RADIUS IS MEASURED, NOT ESTIMATED, and it is zero. The candidate fix (both conjunct deletions, E-02 and E-03) was applied to a clean tree at base and `python3 -m pytest` reported `3251 passed, 2 skipped, 3 warnings in 50.94s` with zero failures; the tree was then reverted to clean (`git diff --stat` empty) before this plan was written. This matters because 151 test call sites pass `dir=str(...)` and a reader could reasonably fear the fix would break every one of them; it does not, because those roots are real AW project fixtures and `is_project_dir` is true for them. CONSEQUENCE: E-05's new test is the ONLY guard this change will have, so it is load-bearing rather than decorative, and V-05 requires demonstrating it fails first. |
| F-05 | `project_context.resolve_verb_repo_root` versus `find_project_root` | A SECOND DEFECT, CARRIED NOT FIXED. `--dir` is honored "verbatim (resolved, no climb)" while the cwd path CLIMBS to the project root. So `aw attention --dir docs` (a real subdirectory of a real AW project) surveys nothing and, with this plan's fix, will REFUSE, where `cd docs && aw attention` correctly climbs and surveys the whole project. Measured at base: `--dir docs` printed `0 artifacts shown` against `454 artifacts shown` from the repo root. This plan's fix converts that silent wrong answer into a loud wrong answer, which is a strict improvement and is why it is not a blocker, but the RIGHT behavior is probably to climb from an explicit `--dir` too, or to refuse with a message naming the project root found above it. That is a behavior-design question about what `--dir` MEANS, it needs a maintainer ruling, and deciding it inside a greenwash fix would smuggle a contract change past review. |
| F-06 | `attention._resolve_runs_repo_root` | A THIRD DEFECT, CARRIED NOT FIXED, and worth naming because it will mislead whoever reproduces this one. When `--dir` points at a path INSIDE this repository (for example under `.aw/state/`), the run and lane probe walks UP from it and reports the OUTER repository's stranded lanes, so the command prints `0 artifacts shown` together with a `VIEW INVALID` header and four lane violations belonging to a different repository than the one named. Measured at base. That cross-repository leak is a separate bug from the silent success; it is also exactly why E-01 requires a target OUTSIDE the repository tree, and why a reproduction attempted under `.aw/state/` looks like a different defect entirely. |
| F-07 | `attention.py` (two comments) and `project_context.py` (one docstring), all citing `tests/test_awretrofit_project_root_climb.py` | THREE CITATIONS POINT AT A FILE THAT DOES NOT EXIST. `attention.py` claims a property "is pinned by `tests/test_awretrofit_project_root_climb.py::NoProjectSubprocessMatrixTests`" and that "the shipped assertion in `tests/test_awretrofit_project_root_climb.py` (rc 3, prose on stderr, empty stdout) keeps passing"; `project_context.find_project_root`'s docstring says the git-blindness rule is "locked by `tests/test_awretrofit_project_root_climb.py`'s `test_bare_git_ancestor_is_not_a_root`". No such file exists under `tests/`, and no test anywhere references `find_project_root`, `is_project_dir`, `no_project_message` or `resolve_verb_repo_root` by name. The only live test of this condition is `tests/test_attention.py::NoProjectAgentEnvelopeTests`, which covers the CWD path only, which is precisely why the `--dir` greenwash survived. This is directly load-bearing for THIS plan: the pins it would otherwise have trusted are absent, so every claim here rests on measurement instead. |

## Proposed changes (ordered, validatable)

1. E-01 reproduce the six-surface matrix outside the repository and capture the cwd path as the reference.
2. E-02 delete the `not explicit_dir` conjunct in `attention.run` (the fix).
3. E-03 delete the same conjunct in `cli._run_plans` for `aw ipd board`.
4. E-04 make the `--check` sub-branch refuse instead of certifying, shaped on the in-module selector-refusal precedent.
5. E-05 add the behavior test pinning all surfaces of both verbs, with a positive control.
6. E-06 correct the three citations of the deleted test file.
7. E-07 bare suite, re-run the matrix, sanitizer, file the carried items.

## Deferred / out of scope (with reason)

- Making an explicit `--dir` CLIMB to the project root the way the cwd path does, or refusing with a message that names the project root found above it (F-05). This is a question about what `--dir` means, not a bug in the guard, and it needs a maintainer ruling: `--dir` is documented as "Repo root", which arguably makes a subdirectory an operator error that should be named rather than silently climbed. This plan's fix already converts the silent wrong answer into a loud refusal, so the dangerous half is fixed here and only the convenience question is deferred.
  - Carrier: NEEDS-BACKLOG-ITEM (file at E-07 as a bug; the current behavior silently answers about the wrong scope)
- The cross-repository runs-root leak, where `--dir` at a path inside this repository reports the OUTER repository's stranded lanes (F-06). A genuinely separate defect in `_resolve_runs_repo_root`'s upward walk, on a different axis from the no-project guard, and fixing it here would mean touching lane discovery inside a one-conjunct honesty fix.
  - Carrier: NEEDS-BACKLOG-ITEM (file at E-07 as a bug)
- Restoring a real pin for the git-blindness rule that `find_project_root`'s docstring claims is locked by the deleted `tests/test_awretrofit_project_root_climb.py` (F-07). E-06 stops the source LYING about the pin, which is this plan's obligation; AUTHORING the missing test for a rule this plan does not change is a different job, and it belongs with whatever audits what deleted that file.
  - Carrier: NEEDS-BACKLOG-ITEM (file at E-07 as a chore; lost coverage rather than a user-perceptible defect)
- Converting the other `resolve_verb_repo_root` callers that fall back to cwd silently. `resolve_verb_repo_root`'s own docstring records this asymmetry and explicitly declines to settle it ("some may legitimately operate on a bare directory"), and `okm6e6` recorded the same thing before it. This plan changes only the two verbs that already emit the guidance.
  - Carrier-Declined: a recorded open design question, not a defect; no work is owed by this item.
- Changing the human/machine exit split (3 versus 2) on this condition. It is a deliberate shipped contract forced by `aw.agent/v1` admitting only 0/1/2, documented at length in the guard's comments and pinned by `NoProjectAgentEnvelopeTests`.
  - Carrier-Declined: correct as shipped; changing it would break a published contract.

## Scope check

- Over-scope: three additions beyond the item's literal text, each with a stated reason. `aw ipd board` (E-03) is added because F-02 measured the identical guard and defect in the only OTHER verb that emits this message, so the two are one behavior and not two. The `--check` refusal (E-04) is added because F-03 measured that the obvious fix leaves that surface certifying a view it never built, so stopping at E-02 would ship a half fix that a CI consumer still reads as clean. The three citation corrections (E-06) are added because F-07 found they point at a deleted file and they are the very pins this plan would otherwise have cited as evidence.
- Under-scope: two defects found while measuring are deliberately NOT fixed: the missing `--dir` subdirectory climb (F-05) and the cross-repository runs-root leak (F-06). Both are named in the approval gate, both are carried to their own items at E-07, and neither is required for this plan's fix to be a strict improvement.

## Required tests / validation

`tests/test_attention_explicit_dir_nonproject.py` (E-05) is the durable verification, and F-04 makes it load-bearing: the existing suite passes WITH the fix and WITHOUT the new test, which proves no current test observes this behavior at all. It drives the real CLI for both verbs across the human, `--agent`, `--format json` and `--check` surfaces, for both a git and a non-git non-project directory, asserts every record against `agent_schema`, asserts no tmp or home path reaches stdout, and carries a POSITIVE control (a real AW project under `--dir` still surveys and does not refuse) so it cannot pass by refusing everything.

Beyond it: E-01's before matrix and E-07's after matrix on the same six surfaces, a bare `python3 -m pytest`, and `aw sanitize --agent`.

HONEST LIMITS ON WHAT THIS PROVES. First, a green suite proves nothing about this defect on the BASE tree, because no existing test observes it (F-04); the only evidence that the fix changes anything is the before/after matrix, which is why V-01 and V-07 both demand pasted output rather than a summary. Second, the tests exercise a git and a non-git non-project directory; they do not enumerate every filesystem shape a `--dir` could name (a symlink, an unreadable directory, a nonexistent path). A nonexistent `--dir` was measured at base to print `0 artifacts shown` and exit 0, and after this fix it will refuse as a non-project, which is better but is arguably still the wrong message for a path that does not exist; that is named here rather than claimed as covered. Third, E-06 corrects citations by reading them, not by a test; nothing mechanically prevents the next stale citation.

## Spec / documentation sync

No `.spec.md` is amended, and `- Scope-Paths:` declares no spec file. The normative contract is ALREADY correct and is the authority this plan brings the code into line with: `docs/cli-output-contract.md` Section 3 classifies a condition "preventing domain inspection" as exit 2, and Section 4's anti-greenwashing invariant forbids a `clean` outcome for `cannot-run` work. The base behavior violates both; the fix conforms to both. No user-facing doc states that `--dir` at a non-project directory succeeds, so there is no doc to correct. The documentation sync in this plan is E-06, which repairs three in-source citations that point at a deleted test file.

## Open questions

### OQ-01: Should `--check` at a non-project directory refuse (exit 2), or keep exit 0?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: REFUSE, exit 2, `cannot-run` (E-04). Resolved from repository evidence rather than deferred to the maintainer, because the repository already answers it twice. First, `docs/cli-output-contract.md` Section 4 states the anti-greenwashing invariant in normative terms: a record must never report `clean` for work that was `cannot-run`. A `--check` that surveyed no project has inspected nothing, so `the view is valid` is a positive claim about unexamined ground, and Section 3 classifies a condition "preventing domain inspection" as exit 2, not 0. Second, this exact question was already settled INSIDE this module for the sibling case: `unresolved_selector_agent_record` refuses a `--check` whose selectors matched nothing, with `cannot-run`/exit 2/`verified:false`/`complete:false`, and its docstring gives the reason this item adopts ("The old record said `outcome:clean, verified:true, complete:true, findings:0` for a token that matched nothing, so a consumer recorded a typo as a CLEAN AUDIT"). A non-project `--dir` is the same failure with a different token. The in-source note that `--check` "stays fail-closed-valid (nothing to violate)" is the opposite reading and is what this item overturns; it is quoted in F-03 so a reviewer can dispute the reversal directly. THE APPROVER SHOULD KNOW this is the one change here that also alters the CWD path's `--check` from exit 0 to exit 2, and that a CI job running `aw attention --check` outside a project would newly fail, which is the intended effect.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual command output for all SIX measurements (three surfaces x {`--dir`, cwd}) for the git-but-not-AW directory, each showing its exit code and first stdout line, plus the stderr first line where one exists. Confirm in one sentence that the target directory is OUTSIDE this repository tree, and paste the command that created it. A matrix showing `--dir` already refusing is a FAILED V-01 and a STOP: the premise is stale. A matrix whose `--dir` output contains `VIEW INVALID` or any `STRANDED lane` line is ALSO a failed V-01, because that means the target was inside this repository and F-06's leak is being measured instead of this defect.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- agent_workflows/attention.py`. It must show the `not explicit_dir and ` text removed from the guard condition and NOTHING else changed by this item (E-04's `--check` change will also appear in this file; identify which hunk belongs to which item). A diff that alters the message text, either exit code, the sanitized summary, or the `NextAction` is a FAILED V-02.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git diff -- agent_workflows/cli.py` showing exactly one changed line, the same conjunct deletion. Then paste `aw ipd board --dir <non-project>` and `--dir <non-project> --agent`, showing exit 3 with prose on stderr and exit 2 with an `outcome:cannot-run` record respectively. Output still reading `no plans found` with exit 0 is a FAILED V-03.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `aw attention --dir <non-project> --check; echo rc=$?` showing a refusal and `rc=2`, and `--dir <non-project> --check --agent` showing a record with `outcome:cannot-run`, `exit:2`, `verified:false`, `complete:false`. Paste the result of validating that record through `agent_schema.validate_agent_record`, which must be an empty list. Output containing `the view is valid`, or an exit of 0, is a FAILED V-04. ALSO paste the CWD-path `--check` at a non-project directory, confirming it now refuses too, since OQ-01 accepted that change deliberately and it must be shown rather than assumed. Confirm the summary contains no absolute path.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: THE TEST MUST BE SHOWN TO FAIL FIRST, and this is the only evidence that the fix does anything, since F-04 measured that the base suite passes with the fix applied and no new test. Paste (1) the new test file's contents; (2) the output of running it against the UNFIXED tree, obtained by stashing the source changes (`git stash push agent_workflows/attention.py agent_workflows/cli.py`), running `python3 -m pytest tests/test_attention_explicit_dir_nonproject.py -o addopts=""`, and restoring; it must FAIL, and the failure must be the greenwash, not an import or fixture error; (3) the same command PASSING with the fix, with per-test counts. State explicitly that the test asserts on exits, stdout, stderr and parsed records only and reads no production source text. Confirm the POSITIVE control is present and passes in BOTH states; a suite of purely negative assertions is a FAILED V-05, because it would also pass against a build that refused unconditionally.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `git grep -n "test_awretrofit_project_root_climb"` returning NO hit in `agent_workflows/`, and paste the diff of the three corrected comments. For each, state whether it now cites a test that exists (name it, and paste a `git grep -n` locating that test) or honestly records the rule as unpinned. A corrected comment citing a second file that also does not exist is a FAILED V-06.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest`, naming any failure as pre-existing or new; F-04 records `3251 passed, 2 skipped` with the conjunct fix at base, so a comparable count plus the new tests is expected and a REGRESSION must be named rather than absorbed. Paste the re-run of E-01's full six-surface matrix showing every greenwash gone. Paste `aw sanitize --agent; echo rc=$?` ending `rc=0`. Finally, name the three backlog items filed for F-05, F-06 and F-07 by id6 and confirm every `NEEDS-BACKLOG-ITEM` placeholder in "Deferred / out of scope" has been replaced. A remaining placeholder is a FAILED V-07: an uncarried finding is a lost one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: deleting one boolean conjunct from a guard in each of two functions, changing one `--check` sub-branch from certifying to refusing, one new behavior test, and three corrected source comments. No change to what counts as an AW project, no change to the no-project message wording or its exit codes, no spec amended, no existing test modified.

THE ONE BEHAVIOR CHANGE THAT REACHES BEYOND `--dir`, stated plainly because an approver could otherwise be surprised in CI. E-04 makes `aw attention --check` at a non-project directory exit 2 instead of 0, on the CWD path as well as the `--dir` path. That is deliberate (OQ-01, resolved from `docs/cli-output-contract.md` Section 4 and the in-module selector-refusal precedent), and the practical consequence is that a job running `aw attention --check` somewhere without an AW project will newly FAIL rather than silently pass. If that is unwanted, say so at review: E-04 is separable from E-02 and E-03, which fix the `--dir` greenwash on their own.

THREE CORRECTIONS TO THE BACKLOG ITEM, all from measurement rather than reading. FIRST, the item names only `aw attention`; `aw ipd board` has the identical guard and identical defect (F-02), and those two verbs are the entire population of this behavior. SECOND, the item implies one fix; the obvious one-conjunct fix leaves `--check` still asserting `the view is valid` (F-03), which was verified empirically with the candidate patch applied. THIRD, the item's blast radius is measured at zero: the candidate fix was applied at base and the full suite reported `3251 passed, 2 skipped` before the tree was reverted (F-04). That last point cuts BOTH ways and the approver should weigh it: it means the change is safe, and it means nothing currently tests this, so E-05 is the whole guard.

WHAT THIS DELIBERATELY DOES NOT FIX, so it is not discovered later as an omission. `--dir` still does not CLIMB, so `--dir <a subdirectory of a real project>` will now REFUSE rather than survey the project above it (F-05); that is louder than today's silent empty answer, but it is not right, and it needs a ruling on what `--dir` means. And `--dir` at a path inside this repository still reports the OUTER repository's stranded lanes (F-06), a cross-repository leak on a different axis. Both are carried to their own backlog items at E-07, together with the missing git-blindness pin (F-07).

GENUINE STOP CONDITIONS: E-01 shows `--dir` already refusing (premise stale, plan wrong); E-01's `--dir` output shows `VIEW INVALID` or stranded lanes, meaning the target was inside this repository and F-06 is being measured instead; or a co-worker's concurrent edit to `attention.py` or `cli.py` cannot be safely combined. None is a scope question; each is a condition under which proceeding would record something false.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a check that was not run. V-05 specifically requires demonstrating the new test FAILING before the fix, and demonstrating the positive control passing in both states. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the four paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, make the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). In particular do NOT fix F-05 or F-06 on the way past: each is a separate defect with its own review surface, and folding either in turns a guard fix into a redesign of what `--dir` means.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit oq4ual -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize oq4ual --actor <agent/model> --message <summary> --apply` (the runner owns it when it executes this plan in a lane). This plan inherits `- Blocks-Release: next` from backlog `xnb551`; AFTER EXECUTION, and not before, set that item `done` with `--evidence` citing this executed plan. The ORDER is load-bearing: while this plan sits in `pending/`, closing `xnb551` fails closed because the gate is handed to a carrier that has not shipped, so the item stays `graduated` until `aw ipd finalize` has moved this plan to `executed/`.
