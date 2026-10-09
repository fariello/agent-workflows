# IPD: Add the shared non-surveyable-root refusal primitive every repo-scoped verb can adopt

- Date: 2026-10-02
- Kind: child
- Concern: Backlog `rgl2d4` names ~35 `resolve_verb_repo_root` callers that fall back SILENTLY for a non-surveyable `--dir`, and names `specs.run_check` / `backlog.run_check` as the highest-value conversions. Plan `lmyeas` built the three-way CLASSIFIER (`project_context.classify_project_dir`) those conversions need, but converted only `aw attention` and `aw ipd board`. The classifier answers "which of the three cases is this", and that is NOT the whole missing piece: each converting verb must also DECIDE to refuse, EMIT a human message naming the enclosing root and the corrected command, EMIT a path-free `aw.agent/v1` error record at exit 2, and NOT regress the bare-cwd climb. Measured in this lane, the two already-converted verbs hand-roll ~45 lines of that emission logic each, in two near-identical copies (`attention.run` and `cli._run_plans`). Converting a dozen more verbs by copying that block a dozen more times is how the `aw install .` falsehood `lmyeas` F-14 had to fix came to exist in two places at once. This plan adds the ONE primitive the remaining conversions call, so the decision, the wording, the exit codes, and the path-free machine record have a single definition.
- Scope: ADD one shared, reusable refusal primitive to `project_context` that a repo-scoped verb calls to turn a non-surveyable resolved root into (a) the human stderr text and (b) the machine summary + next-action inputs, derived from `classify_project_dir`. IN: the primitive and its return shape; a `no_project_message`-equivalent human string for the inside-a-project and no-project cases reusing the shipped wording so no verb invents its own; the PATH-FREE machine summary string plus the correct `NextAction` (none for the inside-a-project case, the shipped `aw install .` only for the genuine git-repo-without-AW case); and a regression test pinning the primitive's three outcomes, its path-free machine output, and the `aw install .` negative. OUT: converting ANY verb to call it (Order 02 converts the two validators, Order 03 the bypass sites, Order 04 the remainder); REFACTORING `attention.run` or `cli._run_plans` onto it (deliberately deferred to Order 04 so this plan cannot regress two shipped surfaces); changing `classify_project_dir`, `is_project_dir`, `_is_project_marker`, `find_project_root`, or `resolve_verb_repo_root` (body OR docstring); making anything CLIMB from an explicit `--dir`; changing the exit-code contract; and widening `agent_schema`.
- Scope-Paths: agent_workflows/project_context.py, tests/test_nonsurveyable_root_refusal.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: rgl2d4
- Blocks-Release: next
- Set: dirsilent
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: i6mby8

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: i6mby8 verified (set dirsilent, attempt 1).
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004. Added the third shipped summary string (bare-cwd) and its test cases; the primitive now returns the NextAction description too; the executor must record the primitive's name and return type in V-01 for jei45f/sjsb04/rlhmt9; no-project fixtures assert find_project_root is None since HOME may be an AW project.
- 2026-10-07 to-review (aw set): returned to review: each Set-level check the coverage probe quoted now names its owning child; coverage pass recorded
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: Check by reading each converted call site for a call to the primitive

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `rgl2d4`. GATE NOTE: item `rgl2d4` carries `- Blocks-Release: next`, which this plan INHERITS as required.
  THIS PLAN EXISTS BECAUSE THE CLASSIFIER IS NOT ENOUGH, which is the one place this Set departs from the item's framing. The item says the remaining work "is adopting that classifier at the remaining callers", implying the only missing piece was the predicate. Measured here (F-02): the two converted verbs each carry a ~45-line hand-rolled emission block, and those two blocks are near-identical. The classifier is the easy half; the REFUSAL (message wording, path-free machine record, exit codes, the `aw install .` negative) is the half that was copied, and copying it again at a dozen sites would reproduce the `lmyeas` F-14 falsehood a dozen times. So this plan adds the shared emitter FIRST and the later Orders call it.
  NOTHING IS CONVERTED HERE, AND THAT IS DELIBERATE RATHER THAN TIMID. This plan is additive: it introduces a symbol with no callers, which `aw check` and the suite can verify in isolation, so a mistake in the primitive cannot take down a shipped surface. Converting `attention.run` and `cli._run_plans` onto it is real work and is OWNED by Order 04, after the primitive has been exercised by the Orders in between.

## Goal

Give the remaining resolver callers ONE function to call so a non-surveyable `--dir` produces the same honest refusal everywhere: human text that names the enclosing project root and the literal corrected command, a path-free machine record at exit 2, and no false `aw install` offer for a project that is already installed. After this plan nothing behaves differently; after Orders 02 to 04 call it, a dozen verbs do.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the primitive

- [x] E-01 ADD ONE SHARED REFUSAL PRIMITIVE to `project_context` that converts a resolved root plus the explicit-`--dir` flag into everything a verb needs to refuse honestly. It takes the verb name (for the message), the resolved root, and whether `--dir` was explicit; it calls the EXISTING `classify_project_dir` and returns a small structured result carrying: whether the verb may proceed (the root IS a project root); the HUMAN stderr text; the PATH-FREE machine summary; and the machine next-action command, which must be `None` for the inside-a-project case and the literal `aw install .` ONLY when `git_root_for_message` finds a git root that is not already a project.
  REUSE THE SHIPPED WORDING RATHER THAN INVENTING IT. The human text must come from the existing `no_project_message` (which `lmyeas` E-03 already taught to name the enclosing root and print `aw <verb> --dir <root>` for the inside-a-project case), not from a new string literal. This is the whole point: a verb that calls this primitive inherits the already-reviewed, already-corrected message, including the F-14 fix. Do NOT re-derive the message, do NOT reword it, and do NOT add a second place where that sentence lives.
  THE MACHINE SUMMARY MUST BE PATH-FREE AND THAT IS ENFORCED, NOT STYLISTIC. `agent_schema` refuses an absolute home path in ANY string field, so interpolating either the given directory or the found root would raise in the renderer before a byte is written (`lmyeas` F-14 and its Project-conventions note). Return the CONDITION without any path; the HUMAN string is the only one that names directories. Reuse the exact summary phrasings the two converted verbs already emit, so a consumer's string match does not break. RE-READ AT REVIEW 2026-10-07 in `attention.run` and `cli._run_plans`: there are THREE summary strings, not two, keyed on the classification AND the explicit flag: inside-a-project with explicit `--dir` -> "the specified directory is inside an AW project but is not its root; --dir is honored verbatim with no upward climb"; no project with explicit `--dir` -> "no AW project found at the specified directory; --dir is honored verbatim with no upward climb"; no project WITHOUT `--dir` (bare-cwd climb failed) -> "no AW project found at the working directory or any ancestor; cd into the repository or pass --dir <repo>". The primitive must produce all three, because sibling `jei45f` OQ resolves that the validators refuse in the bare-cwd case too.
  RETURN THE WHOLE NEXT ACTION, NOT ONLY ITS COMMAND. Both shipped sites build `NextAction(command="aw install .", description="install agent-workflows in this repo")`; return both the command and that description (as plain strings, still no `result_types` import), so no call site re-authors the description. When the root IS a project root, the human text, the summary and the next action are all `None`.
  NAME THE SYMBOL IN THE EVIDENCE. The siblings (`jei45f`, `sjsb04`, `rlhmt9`) refer to it only as "Order 01's primitive", so the executor chooses the name and return type and MUST record both in V-01, which is where those executors will look.
  RETURN DATA, DO NOT PRINT, AND DO NOT BUILD A `CommandResult`. The primitive must not write to stdout/stderr, must not import `renderers` or `result_types`, and must not construct a `CommandResult`: those live at the call site, where the verb knows its own `command=` name and its own renderer context. A primitive that printed would be unusable by the `--agent` path, and one that built a `CommandResult` would drag a heavy import into `project_context`, which is imported by nearly everything. Keep it pure and side-effect-free like its neighbors.
  - Depends on: none
  - Expected outcome: a pure, non-printing function in `project_context` that, for a resolved root, returns may-proceed plus the human text, the path-free machine summary (one of the three shipped strings), and the next action (command and description, or `None`); the human text is produced BY `no_project_message` rather than re-authored; `aw install .` appears only for the git-repo-without-AW case; `classify_project_dir`, `is_project_dir`, `_is_project_marker`, `find_project_root`, `resolve_verb_repo_root` and `no_project_message` are all behaviorally unchanged.
  - Execution state: performed

- [x] E-02 GIVE THE PRIMITIVE A DOCSTRING THAT TELLS A CONVERTING AUTHOR WHAT TO DO, because the next three Orders and every later conversion are its real audience and the alternative is each author re-reading two 45-line blocks to infer the contract.
  STATE THE CALL SHAPE: resolve with `resolve_verb_repo_root` as today, call this primitive, and on may-proceed-false emit the machine record (exit 2, `cannot-run`) or the human stderr and return the cannot-run exit. Name `attention.run` as the reference implementation so there is a worked example in the tree rather than a description of one.
  STATE THE TWO TRAPS EXPLICITLY, since both are already-measured defects and not hypotheses: a machine record must never carry a path (the schema refuses it, and it raises in the renderer rather than failing a test later), and a `cannot-run` record must carry exit 2 and never 3 (`aw.agent/v1` admits only 0/1/2, so an `exit_code=3` record cannot be emitted at all).
  STATE WHAT THIS DOES NOT DECIDE: whether a given verb SHOULD refuse is the verb's policy, not the primitive's. A read verb surveying nothing is a false clean claim and should refuse; a write verb's verbatim target is the operator's explicit intent and today fails loudly and locally, which `lmyeas` OQ-01 decided to keep. The primitive serves both and chooses neither.
  RECORD THAT `--dir` STILL NEVER CLIMBS, with a pointer to `resolve_verb_repo_root`'s own docstring where `lmyeas` E-02 recorded the decision and its reasoning, so a reader who finds this primitive first does not conclude the climb question is open.
  - Depends on: E-01
  - Expected outcome: the primitive's docstring states the call shape, names `attention.run` as the reference, names the path-free and exit-2 traps, says policy stays with the verb, and points at `resolve_verb_repo_root` for the no-climb decision; no behavior change.
  - Execution state: performed

### Task group 2: pin it

- [x] E-03 ADD A REGRESSION TEST in a new `tests/test_nonsurveyable_root_refusal.py` that pins the primitive directly, called in process, against `tempfile` fixtures built OUTSIDE any AW project.
  FIRST ASSERT THE FIXTURE PRECONDITION: `project_context.find_project_root(<fixture>)` is `None` for the no-project fixtures, since `$HOME` may itself be an AW project (measured at review: `~/.aw` exists on this machine) and a `tempfile` dir under it would silently classify as inside-a-project.
  COVER THE THREE CLASSIFICATION OUTCOMES AND THE FOURTH MESSAGE CASE, which is one more case than the classifier has and is exactly where the F-14 falsehood lived: (a) the root IS a project root, so may-proceed is true; (b) a SUBDIRECTORY of a real project, so may-proceed is false, the human text names the enclosing root and contains the literal `aw <verb> --dir <root>`, and the next-action is `None`; (c) a directory in NO project and NOT in a git repo, so may-proceed is false and the next-action is `None`; (d) a directory in NO AW project but INSIDE a git repository, so the next-action IS the literal `aw install .`. Case (d) is what proves the install offer was preserved where it is TRUE rather than deleted wholesale. ALSO COVER THE NON-EXPLICIT VARIANT of (c) and (d) (explicit flag false, the bare-cwd case), asserting the third summary string ("... at the working directory or any ancestor ...") and, for (d), the same `aw install .` next action. For (b) and (d), assert the next action's description equals the shipped "install agent-workflows in this repo" where present. For each case, assert the summary EQUALS the shipped string for that case (not merely that it is path-free), so a consumer's string match is pinned.
  ASSERT THE F-14 NEGATIVES ON CASE (b), since they are the defect this Set exists to stop spreading: the human text must NOT contain `is not installed in it`, and the next-action must NOT be `aw install .`. A test that only checks the root is named would pass while the false sentence sat beside it.
  ASSERT THE MACHINE SUMMARY IS PATH-FREE for every case: the fixture temp path and the found root must appear in NEITHER the machine summary NOR the next-action. Assert it by substring over the actual returned strings, not by inspecting source.
  ASSERT PURITY: take a recursive file inventory of each fixture before and after the calls and show them identical, and assert the primitive wrote nothing to stdout or stderr (capture both and assert empty), since a verb's `--agent` path depends on it being silent.
  ASSERT ON OUTCOMES, NOT SOURCE STRUCTURE, per the repository's outcomes-not-structure rule: no `inspect`, no `ast`, no regex or substring search over production source, and no assertion about line counts or call counts.
  PROVE THE TEST CAN FAIL. Paste a mutation run: make the primitive return the generic no-project message for the inside-a-project case (so the enclosing root is no longer named), show this file FAILING, revert, and show it green again.
  - Depends on: E-02
  - Expected outcome: a new passing test file pinning the four message cases plus the two non-explicit variants, the exact shipped summary per case, the F-14 negatives, the path-free machine strings, purity and silence, with no source-structure assertions and a pasted mutation proving the root-naming assertion fails when the naming is removed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- MEASURE FROM OUTSIDE EVERY AW PROJECT OR MEASURE THE WRONG THING. Any probe of these verbs must run with `cwd` outside any project and with fixtures in a genuine temp dir; run from inside this repository the climb succeeds and the output describes THIS repository. This invalidated a probe during this authoring and is why every measurement below names its `cwd`.
- AND SEED THE FIXTURE WITH A RECORDS BACKEND INSIDE IT. `aw install <dir>` run non-interactively here chose a `home` records backend and wrote the fixture's records under `$HOME/.aw/projects/<name>-<hash>/`, so a "root control" probe read an empty in-repo tree and proved nothing. Pass `--records-backend repository` explicitly. Measured during this authoring: the first fixture's artifacts landed in a home project directory, not under the fixture (F-10).
- THE `aw` CONSOLE SCRIPT MAY IMPORT THE PACKAGE FROM THE MAIN CHECKOUT RATHER THAN THE LANE, and it announces the re-exec on stderr. Evidence-producing invocations must state the interpreter and `PYTHONPATH`, or use `python3 -m agent_workflows` with `PYTHONPATH=<lane>` and `AW_NO_REEXEC=1`, which is how every measurement in this plan was taken.
- ABSOLUTE PATHS ARE UNEMITTABLE IN MACHINE RECORDS. `agent_schema` refuses a home path in any string field, which is why the shipped `NextAction` is the literal `aw install .`. This constraint shapes the primitive's machine half.
- NO SITE IN THE PACKAGE MAY BUILD AN `exit_code=3` RECORD; it raises in the renderer before writing a byte. Re-derive with `rg -n "exit_code=3" agent_workflows/`, whose only hits are comments asserting the property.
- THE HUMAN/MACHINE EXIT SPLIT WAS RETIRED: both surfaces now carry 2 for this condition (`attention.run` returns `EXIT_CANNOT_RUN`, and its comment records that backlog `c6vs7y` / IPD `rwvzqm` moved the human path off 3). Measured in this lane: `aw attention --dir <subdir>` exits 2, not 3. Do NOT reintroduce 3, and note that `lmyeas`'s prose still describes a 3/2 split that no longer holds (F-09).
- RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; `-n0` makes it several times slower and a second `-q` suppresses the `N passed` line this plan requires be pasted.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE ITEM'S PREMISE HOLDS AND THE CLASSIFIER IS PRESENT AND CORRECT.** `project_context.classify_project_dir` exists at this lane's HEAD, returns a frozen `ProjectClassification` with `case` plus `root`, and composes `is_project_dir` and `find_project_root` with no third walk and no git probe, exactly as `lmyeas` E-01 specified. So the predicate this Set builds on is real and the remaining work is genuinely the ADOPTION the item describes. | read of `project_context.classify_project_dir`, `ProjectClassification` and `ProjectLocationCase` at HEAD `9de38b09f` |
| F-02 | **BUT THE CLASSIFIER IS THE EASY HALF: THE REFUSAL IS HAND-ROLLED TWICE ALREADY, WHICH IS THIS PLAN'S ENTIRE JUSTIFICATION.** Both converted verbs carry a near-identical block that calls `classify_project_dir`, branches on `classification.is_inside_project and explicit_dir`, builds a path-free `summary`, sets `next_actions = []` or the `aw install .` `NextAction` gated on `git_root_for_message`, builds a `cannot-run` `CommandResult` at `exit_code=2`, and otherwise writes `no_project_message(..., explicit=bool(explicit_dir))` to stderr and returns the cannot-run exit. The two copies differ only in the verb string and the local root variable name. Converting a dozen more verbs by copying this is how the F-14 falsehood came to exist in TWO places needing ONE fix. | reads of `attention.run` and `cli._run_plans`, quoting from each the `classify_project_dir` call, the `if classification.is_inside_project and explicit_dir:` branch, the identical two-clause `summary` strings, the `NextAction(command="aw install .", ...)` gated on `git_root_for_message`, and the `no_project_message(...)` stderr write |
| F-03 | **THE DEFECT THE ITEM FILED REPRODUCES EXACTLY, AT THIS LANE'S HEAD.** In a temp project seeded with ONE open backlog item and ONE spec, `cwd` outside any AW project: `aw specs check --dir <root>` prints `all specs conform. 1 specs checked.` while `--dir <deep>` prints `all specs conform. 0 specs checked.`, both exit 0; `aw backlog check --dir <deep>` prints `all backlog items conform.` at exit 0; `aw find backlog --dir <deep>` prints `✓ CLEAN  no matching backlog` where `--dir <root>` lists the item; and `aw check --dir <deep>` prints `✓ CONFORMS  0 all checked` where `--dir <root>` prints `✓ CONFORMS  4 all checked`. Two of those are fail-closed validators announcing conformance over ZERO artifacts. | subprocess runs of `python3 -m agent_workflows` with `PYTHONPATH=<lane>`, `AW_NO_REEXEC=1`, `cwd` in a temp dir, fixture seeded via `backlog new --apply` and `specs new --apply` with `--records-backend repository`, at HEAD `9de38b09f` |
| F-04 | **THE MACHINE SURFACE GREENWASHES TOO, WHICH IS THE WORSE HALF BECAUSE CI READS IT.** For `--dir <deep>`, `aw specs check --agent` emits `{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":0,"findings":0,...}` and `aw backlog check --agent` the same with `"cmd":"backlog check"`, while `aw check --agent` emits `"outcome":"conforms","exit":0,"verified":true,"complete":true`. A record asserting `verified:true, complete:true, outcome:clean` for ZERO examined artifacts is precisely the Anti-Greenwashing Invariant violation `docs/cli-output-contract.md` states ("A record MUST NEVER report a positive outcome ... for work that was `skipped`, `partial`, `unverified`, or `cannot-run`"). | the `--agent` runs of `specs check`, `backlog check` and `check` at `--dir <root>` and `--dir <deep>`, pasting both records per verb; the quoted invariant from `docs/cli-output-contract.md` Section "Protocol Invariants and Anti-Greenwashing Rules" |
| F-05 | **THE SHIPPED REFUSAL IS ALREADY CORRECT AND HONEST, SO THE PRIMITIVE HAS A GOOD MODEL TO GENERALIZE RATHER THAN A SHAPE TO INVENT.** Driven at this HEAD, `aw attention --dir <deep>` exits 2 and prints: `no AW project found at <deep>.` / `Checked only <deep> (explicit --dir is honored verbatim with no upward climb) ...` / `Specify your repository root, or run without --dir to search upward from cwd.` / `<root> IS an agent-workflows project root, but explicit --dir is honored verbatim with no upward climb.` / `Run with: aw attention --dir <root>`. The false `is not installed in it` sentence is GONE and the enclosing root is named, confirming `lmyeas` E-03 landed. This is the text the primitive must reuse verbatim via `no_project_message`, not re-author. | the `attention --dir <deep>` run, pasting all five stderr lines and `rc=2` |
| F-06 | **THE WRITE-CLASS HAZARD THAT DECIDED `lmyeas` OQ-01 IS REAL, AND ONE MEASUREMENT IS WORSE THAN THAT PLAN RECORDED.** Previewed (no `--apply`): `aw specs new --dir <deep>` reports it `would write /home/<user>/.aw/projects/deep-<hash>/records/specs/draft/<...>.spec.md`, i.e. a subdirectory `--dir` sends a WRITE at a NEW project directory under `$HOME`, not merely at a wrong in-repo path; `aw backlog new --dir <deep>` reports it `would write <deep>/.agents/backlog/open/<...>.backlog.md`, proposing a new LEGACY-layout tree inside the subdirectory. Both are visibly wrong at a path an operator can read and neither touches the real records tree, which is the "loud and local" failure mode OQ-01 preferred over a silent climb. It also shows why the primitive must NOT itself decide to refuse: these are the operator's explicit target. | the two `new` previews, pasting both `would write` lines; the home path confirmed absent afterwards (`ls` of the named projects dir returns "No such file or directory", so the preview wrote nothing) |
| F-07 | **NO SPEC GOVERNS THE RESOLUTION RULE OR THE REFUSAL SHAPE, so this plan amends no contract document.** `grep -rln "resolve_verb_repo_root\|no_project_message" .aw/records/specs/ docs/` returns NOTHING. The rule lives only in `resolve_verb_repo_root`'s docstring (where `lmyeas` E-02 recorded it), which is why `- Scope-Paths:` declares no `.spec.md`. `docs/cli-output-contract.md` governs the exit codes and the Anti-Greenwashing Invariant this Set is enforcing, but this plan changes neither. | the grep returning no files; `docs/cli-output-contract.md` read for the invariant and the exit-2 `cannot-run` classification |
| F-08 | **THE `aw install .` OFFER MUST BE PRESERVED FOR THE CASE WHERE IT IS TRUE, which is why the primitive needs FOUR message cases and not three.** `no_project_message`'s tail is now gated on `git_root is not None and not is_project_dir(git_root)`, so a git repository with NO AW project still correctly gets `<root> IS a git repository, but agent-workflows is not installed in it.` plus `Install it there with: aw install <root>`. That branch is TRUE there and must survive. A primitive built from the classifier's three cases alone would lose it, which is why E-03 pins case (d) explicitly. | read of `no_project_message`'s git-root tail quoting the `git_root is not None and not is_project_dir(git_root)` condition and both emitted sentences |
| F-09 | **`lmyeas`'s PROSE ABOUT A 3-VERSUS-2 EXIT SPLIT IS STALE AND MUST NOT BE COPIED INTO THE PRIMITIVE.** That plan repeatedly says "human 3 / machine 2". Measured at this HEAD both surfaces return 2: `aw attention --dir <deep>` gives `rc=2`, and `attention.run` returns `EXIT_CANNOT_RUN` with an in-code comment recording that backlog `c6vs7y` (IPD `rwvzqm`) "retir[ed] the human exit 3 so one condition has one code". So the primitive's documented contract is exit 2 on BOTH surfaces. Stated because an executor reading the predecessor plan would otherwise implement a split that no longer exists. | the `rc=2` from the human `attention --dir <deep>` run; the `return EXIT_CANNOT_RUN` line and the quoted `THE HUMAN PATH WAS LATER MOVED TO EXIT 2 AS WELL` comment in `attention.run` |
| F-10 | **A FIXTURE TRAP THAT INVALIDATED THE FIRST MEASUREMENT PASS, recorded so the executor does not lose the same hour.** `aw install <fixture>` run non-interactively selected a `home` records backend and placed the fixture project's records under `$HOME/.aw/projects/<name>-<hash>/`, so `aw find specs --dir <root>` printed a path under `$HOME` and the "root control" was not reading the fixture at all. Re-seeding with `--records-backend repository` put records at `<root>/.aw/records/` and made every control meaningful. Any probe in this Set must pass that flag. | the first fixture's `find specs --dir <root>` output naming a `$HOME/.aw/projects/...` path; the re-seeded fixture's artifacts listed under `<root>/.aw/records/{backlog/open,specs/draft}` |

## Proposed changes (ordered, validatable)

1. Add one pure, non-printing refusal primitive to `project_context` that maps a resolved root plus the explicit-`--dir` flag, via the existing `classify_project_dir`, to may-proceed plus the human text (from `no_project_message`), a path-free machine summary, and the correct next-action command (`None` for inside-a-project, `aw install .` only for git-without-AW) (E-01).
2. Document the primitive for its real audience, the converting authors of Orders 02 to 04: the call shape, `attention.run` as the worked reference, the path-free and exit-2 traps, the fact that refuse-or-proceed policy stays with the verb, and a pointer to the recorded no-climb decision (E-02).
3. Add `tests/test_nonsurveyable_root_refusal.py` pinning the four message cases, the F-14 negatives, path-freeness, purity and silence, with a pasted mutation proving the root-naming assertion can fail (E-03).

## Deferred / out of scope (with reason)

- CONVERTING ANY VERB TO CALL THE PRIMITIVE. This plan ships a symbol with no callers on purpose: an additive primitive can be validated in isolation, while a combined plan would put a new abstraction and a dozen behavior changes in one reviewable unit. Work is genuinely owed and is carried by the siblings in this Set.
  - Carrier: jei45f, sjsb04, rlhmt9
- REFACTORING `attention.run` AND `cli._run_plans` ONTO THE PRIMITIVE, which is the obvious tidy-up and is deliberately NOT done here. Those are the two SHIPPED surfaces whose wording `lmyeas` just corrected and whose behavior three test files pin; rewriting them in the same plan that introduces the abstraction risks regressing a just-fixed falsehood to remove a duplicate. Order 04 does it once the primitive has been exercised by two real conversions.
  - Carrier: rlhmt9
- THE DECISION THAT AN EXPLICIT `--dir` NEVER CLIMBS. NOT deferred: already DECIDED by `lmyeas` OQ-01 from measured evidence (write-class census, a `shutil.rmtree` call site, `$HOME` being itself a project root, lane ancestry) and recorded in `resolve_verb_repo_root`'s docstring. F-06 re-measures the write-class hazard and agrees. NO CARRIER NEEDED: a settled decision with its reasoning in the symbol an executor reads.
  - Carrier-Declined: decided and durably recorded by `lmyeas` E-02; this Set implements the remedy that decision implies and does not reopen it
- WHETHER A WRITE VERB SHOULD ALSO REFUSE a non-surveyable `--dir`. Out of scope for the primitive, which serves both classes and chooses for neither. F-06 measures that write verbs fail loudly and locally today (a readable wrong path, nothing entering the real tree), so there is no greenwashing defect to fix on that side. The read/write policy question is Order 04's, because it cannot even be EXPRESSED until the shared helpers are split.
  - Carrier: rlhmt9
- THE PRE-EXISTING SUITE FAILURES measured at this HEAD (`test_every_real_spec_in_this_repository_still_conforms`, `test_unreachable_binding_refusal_fires_under_perturbation`, `test_must_not_refuse_matrix`). Unrelated to this concern; recorded as the baseline an executor must reconcile against rather than mistake for a regression. NO CARRIER NEEDED: pre-existing and outside this Set's scope.
  - Carrier-Declined: pre-existing at HEAD before any edit; this plan's bar is the delta of failing node ids, not a green suite

## Scope check

- Over-scope: none. Both scope paths are required: `project_context.py` carries the primitive (E-01) and its docstring (E-02), and the new test file is E-03. No `.spec.md` is in scope and F-07 measures why.
- Under-scope: this plan adds a primitive and converts NOTHING, so after it the measured defects of F-03 and F-04 are still present. A reader must not take it as fixing the under-report; it is the shared mechanism the three sibling Orders use to fix it. That is stated plainly because a plan whose user-visible effect is zero is easy to mistake for a complete remedy.
- Deliberately NOT touched: `classify_project_dir`, `is_project_dir`, `_is_project_marker`, `find_project_root`, `resolve_verb_repo_root` (body and docstring), and `no_project_message`'s behavior. The primitive CALLS `no_project_message`; it must not alter what it says, since that text was corrected by `lmyeas` E-03 and is pinned by shipped tests.

## Required tests / validation

- `python3 -m pytest` BARE, per the repository contract, pasting the ACTUAL `N passed` summary line. Establish the baseline on a CLEAN tree BEFORE editing and judge on the DELTA OF FAILING NODE IDS. MEASURED AT AUTHORING on a clean tree at HEAD `9de38b09f`: `3 failed, 4624 passed, 2 skipped, 3 warnings in 116.19s`, the three failures being `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, and `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`. Re-measure your own baseline rather than trusting that figure; the bar is NO NEW failing node id.
- `python3 -m pytest tests/test_nonsurveyable_root_refusal.py tests/test_project_context.py tests/test_explicit_dir_subdir_resolution.py tests/test_explicit_dir_non_project.py tests/test_no_project_exit_is_cannot_run.py tests/test_attention.py` for the focused surface. The three shipped `--dir` files are included deliberately: they pin the message text this primitive reuses, so they are the tests likeliest to notice an accidental reword.
- THE PRIMITIVE'S FOUR CASES PLUS THE TWO NON-EXPLICIT VARIANTS, called directly and pasted, each summary compared EQUAL to the shipped string for its case: a project root (may-proceed true); a subdirectory of a project (may-proceed false, human text naming the enclosing root AND containing the literal `aw <verb> --dir <root>`, next-action `None`); a directory in no project and no git repo (next-action `None`); and a directory in no AW project but inside a git repo (next-action exactly `aw install .`).
- THE F-14 NEGATIVES on the subdirectory case, pasted: the human text does NOT contain `is not installed in it`, and the next-action is NOT `aw install .`.
- PATH-FREENESS, pasted for every case: neither the fixture temp path nor the found root appears in the machine summary or the next-action. This is the specific leak risk the primitive introduces, because it is the first place both strings are produced together.
- PURITY AND SILENCE, pasted: a recursive file inventory of each fixture before and after the calls, shown identical; and captured stdout/stderr around the calls, shown empty.
- CONFIRM THE PRESERVED BEHAVIORS: paste `git diff` of `project_context.py` showing `classify_project_dir`, `is_project_dir`, `_is_project_marker`, `find_project_root` and `resolve_verb_repo_root` UNCHANGED (the primitive is additive), and showing `no_project_message`'s emitted strings unchanged.
- CONFIRM THE PRIMITIVE DOES NOT PRINT OR BUILD A RECORD: paste a grep of its body for `sys.stdout`, `sys.stderr`, `print(`, `CommandResult` and `get_renderer`, all returning nothing.
- `rg -n "exit_code=3" agent_workflows/` after the change, confirming no new `exit_code=3` site appeared.
- `python3 -m agent_workflows check` must not gain a diagnostic, and `aw ipd lint` must report conforming.
- `aw sanitize --agent` clean, since this plan's evidence pastes `PYTHONPATH` values and temp paths.

## Spec / documentation sync

NO `.spec.md` FILE IS EDITED AND NONE NEEDS TO BE, measured rather than assumed. `grep -rln "resolve_verb_repo_root\|no_project_message" .aw/records/specs/ docs/` returns NOTHING (F-07): neither the resolution rule nor the refusal shape is governed by a spec, so `resolve_verb_repo_root`'s docstring is the contract document for the first and this primitive's docstring becomes it for the second. `- Scope-Paths:` therefore declares no spec, and the runners' spec-edit announcement will correctly report none.

`docs/cli-output-contract.md` GOVERNS WHAT THIS SET IS ENFORCING AND IS NOT AMENDED. Its Anti-Greenwashing Invariant already forbids the `outcome:clean, verified:true, checked:0` records F-04 measures, and it already classifies `cannot-run` as exit 2. So the later Orders bring the code into line with a contract that is already correct; nothing in the document needs to change, and this plan adds no flag and changes no record field's meaning.

WHETHER THE WIDER GAP EVENTUALLY DESERVES A SPEC is deliberately left open, as `lmyeas` left it. A package-wide resolution-and-refusal spec would be defensible once Order 04 has settled the read/write policy, but writing it now, while one primitive exists and no verb calls it, would publish a rule the code does not yet keep.

## Open questions

### OQ-01: Should the primitive return data, or print and return an exit code?

- Blocking: no
- Status: resolved
- Owner: executor
- Finding: F-02, F-05
- Resolution or deferral rationale: RESOLVED: RETURN DATA; the caller prints. A print-and-return-code helper would be shorter at the human call site and is the tempting shape, but it cannot serve the `--agent` path at all: that path needs the summary and next-action as VALUES to put inside a `CommandResult`, and a helper that had already written prose to stderr would both corrupt the machine surface and emit the absolute paths the schema refuses. F-02 shows both existing call sites already split exactly this way (a path-free `summary` for the record, `no_project_message` for stderr), so returning data matches the shipped shape rather than inventing one. The cost is three or four lines at each call site instead of one, which is the right trade for one definition serving both surfaces.

### OQ-02: Should the primitive live in `project_context`, or in a new module?

- Blocking: no
- Status: resolved
- Owner: executor
- Finding: F-01, F-02, F-08
- Resolution or deferral rationale: RESOLVED: `project_context`. Everything the primitive composes already lives there (`classify_project_dir`, `no_project_message`, `git_root_for_message`, `is_project_dir`), so placing it elsewhere would mean a new module importing four symbols from this one to add a thin wrapper, and would put the refusal wording one import away from the message it must not duplicate. The module is large, which is the honest argument for a new one, but it is also imported by nearly every verb already, so no caller pays a new import. The constraint this creates is recorded in E-01 and is load-bearing: the primitive must NOT import `renderers` or `result_types`, or `project_context` would drag the rendering stack into every importer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the committed diff of the new primitive including its full signature and return type. Paste the LITERAL output of calling it FOUR ways against `tempfile` fixtures built outside any AW project, with `cwd` outside any AW project and the interpreter and `PYTHONPATH` named: (a) a real project root, (b) a subdirectory of that project, (c) a directory in no project and no git repo, (d) a directory in no AW project but inside a git repository. CONFIRM (a) reports may-proceed TRUE; (b) reports may-proceed FALSE, its human text CONTAINS the enclosing root and the literal `aw <verb> --dir <root>`, and its next-action is `None`; (c) reports may-proceed FALSE with next-action `None`; and (d) reports next-action exactly `aw install .` with description `install agent-workflows in this repo`. ALSO paste the two non-explicit variants of (c) and (d), showing the bare-cwd summary string. STATE THE PRIMITIVE'S SYMBOL NAME AND RETURN TYPE explicitly, since sibling plans `jei45f`, `sjsb04` and `rlhmt9` call it by reference to this evidence. PASTE THE F-14 NEGATIVES for case (b): grep its human text for `is not installed in it` returning NOTHING, and show the next-action is not `aw install .`. PASTE PATH-FREENESS for all four: grep each machine summary and next-action for the fixture path and for the found root, all returning NOTHING. CONFIRM THE HUMAN TEXT IS PRODUCED BY `no_project_message` rather than re-authored, by reading the diff and showing the call. CONFIRM IT NEITHER PRINTS NOR BUILDS A RECORD: paste a grep of the new function's body for `sys.stdout`, `sys.stderr`, `print(`, `CommandResult`, `get_renderer` and `result_types`, all returning nothing, AND paste captured stdout/stderr around the four calls showing both EMPTY. CONFIRM ADDITIVITY by pasting `git diff` for `classify_project_dir`, `is_project_dir`, `_is_project_marker`, `find_project_root`, `resolve_verb_repo_root` and `no_project_message` showing NO behavioral change.
  - Observed evidence:
    Committed diff of the new primitive, types, and signature in `agent_workflows/project_context.py`:
    ```diff
    +@dataclass(frozen=True)
    +class RefusalNextAction:
    +    """The machine NextAction inputs produced by a refusal."""
    +
    +    command: str
    +    description: str
    +
    +
    +@dataclass(frozen=True)
    +class RootRefusal:
    +    """Outcome of evaluating a resolved repository root for a verb.
    +
    +    Pure, read-only, and side-effect-free data structure carrying everything
    +    a repo-scoped verb needs to proceed or refuse honestly.
    +    """
    +
    +    may_proceed: bool
    +    human_message: Optional[str] = None
    +    summary: Optional[str] = None
    +    next_action: Optional[RefusalNextAction] = None
    +
    +    @property
    +    def can_proceed(self) -> bool:
    +        """Alias for may_proceed."""
    +        return self.may_proceed
    +
    +    @property
    +    def human_text(self) -> Optional[str]:
    +        """Alias for human_message."""
    +        return self.human_message
    +
    +    @property
    +    def message(self) -> Optional[str]:
    +        """Alias for human_message."""
    +        return self.human_message
    +
    +    @property
    +    def next_action_command(self) -> Optional[str]:
    +        """The next action command string, or None."""
    +        return self.next_action.command if self.next_action is not None else None
    +
    +    @property
    +    def next_action_description(self) -> Optional[str]:
    +        """The next action description string, or None."""
    +        return self.next_action.description if self.next_action is not None else None
    +
    +    @property
    +    def next_actions(self) -> List[RefusalNextAction]:
    +        """List containing the next_action if present, else empty list."""
    +        return [self.next_action] if self.next_action is not None else []
    +
    +
    +def nonsurveyable_root_refusal(
    +    verb: str,
    +    repo_root: Optional[str | Path] = None,
    +    explicit_dir: bool = False,
    +) -> RootRefusal:
    +    ...
    +    where = Path(repo_root).resolve() if repo_root is not None else Path.cwd().resolve()
    +    classification = classify_project_dir(where)
    +    if classification.is_root:
    +        return RootRefusal(may_proceed=True)
    +
    +    human_msg = no_project_message(verb, where, explicit=bool(explicit_dir))
    +
    +    if classification.is_inside_project and explicit_dir:
    +        summary = (
    +            "the specified directory is inside an AW project but is not its root; "
    +            "--dir is honored verbatim with no upward climb"
    +        )
    +        next_action = None
    +    else:
    +        if explicit_dir:
    +            summary = (
    +                "no AW project found at the specified directory; "
    +                "--dir is honored verbatim with no upward climb"
    +            )
    +        else:
    +            summary = (
    +                "no AW project found at the working directory or any ancestor; "
    +                "cd into the repository or pass --dir <repo>"
    +            )
    +
    +        git_root = git_root_for_message(where)
    +        if git_root is not None and not is_project_dir(git_root):
    +            next_action = RefusalNextAction(
    +                command="aw install .",
    +                description="install agent-workflows in this repo",
    +            )
    +        else:
    +            next_action = None
    +
    +    return RootRefusal(
    +        may_proceed=False,
    +        human_message=human_msg,
    +        summary=summary,
    +        next_action=next_action,
    +    )
    ```

    Symbol name and return types:
    - Symbol name: `agent_workflows.project_context.nonsurveyable_root_refusal`
    - Return type: `agent_workflows.project_context.RootRefusal`
    - Next action type: `agent_workflows.project_context.RefusalNextAction`

    LITERAL output of direct probe across all four cases plus the two non-explicit variants:
    ```
    INTERPRETER: /home/<user>/venv/p3.14/bin/python3
    PYTHONPATH: <lane-worktree>
    CWD: /tmp
    ============================================================
    LABEL: Case (a) Real project root (explicit=True)
    PATH: /tmp/tmp1z0n0t3n/real_proj
    EXPLICIT: True
    may_proceed: True
    human_message:
    None
    summary: None
    next_action: None
    captured_stdout: ''
    captured_stderr: ''
    ============================================================
    LABEL: Case (b) Subdirectory of real project (explicit=True)
    PATH: /tmp/tmp1z0n0t3n/real_proj/deep/sub
    EXPLICIT: True
    may_proceed: False
    human_message:
    aw attention: no AW project found at /tmp/tmp1z0n0t3n/real_proj/deep/sub.
    Checked only /tmp/tmp1z0n0t3n/real_proj/deep/sub (explicit --dir is honored verbatim with no upward climb) for a .aw/ (or legacy .agents/) project directory.
    Specify your repository root, or run without --dir to search upward from cwd.
    /tmp/tmp1z0n0t3n/real_proj IS an agent-workflows project root, but explicit --dir is honored verbatim with no upward climb.
    Run with: aw attention --dir /tmp/tmp1z0n0t3n/real_proj
    summary: the specified directory is inside an AW project but is not its root; --dir is honored verbatim with no upward climb
    next_action: None
    captured_stdout: ''
    captured_stderr: ''
    ============================================================
    LABEL: Case (c) Directory in no project, no git (explicit=True)
    PATH: /tmp/tmp1z0n0t3n/nongit
    EXPLICIT: True
    may_proceed: False
    human_message:
    aw attention: no AW project found at /tmp/tmp1z0n0t3n/nongit.
    Checked only /tmp/tmp1z0n0t3n/nongit (explicit --dir is honored verbatim with no upward climb) for a .aw/ (or legacy .agents/) project directory.
    Specify your repository root, or run without --dir to search upward from cwd.
    summary: no AW project found at the specified directory; --dir is honored verbatim with no upward climb
    next_action: None
    captured_stdout: ''
    captured_stderr: ''
    ============================================================
    LABEL: Case (d) Git repo without AW (explicit=True)
    PATH: /tmp/tmp1z0n0t3n/git_no_aw
    EXPLICIT: True
    may_proceed: False
    human_message:
    aw attention: no AW project found at /tmp/tmp1z0n0t3n/git_no_aw.
    Checked only /tmp/tmp1z0n0t3n/git_no_aw (explicit --dir is honored verbatim with no upward climb) for a .aw/ (or legacy .agents/) project directory.
    Specify your repository root, or run without --dir to search upward from cwd.
    /tmp/tmp1z0n0t3n/git_no_aw IS a git repository, but agent-workflows is not installed in it.
    Install it there with: aw install /tmp/tmp1z0n0t3n/git_no_aw
    summary: no AW project found at the specified directory; --dir is honored verbatim with no upward climb
    next_action: RefusalNextAction(command='aw install .', description='install agent-workflows in this repo')
    captured_stdout: ''
    captured_stderr: ''
    ============================================================
    LABEL: Case (c-variant) Directory in no project, no git (explicit=False)
    PATH: /tmp/tmp1z0n0t3n/nongit
    EXPLICIT: False
    may_proceed: False
    human_message:
    aw attention: no AW project found here.
    Checked /tmp/tmp1z0n0t3n/nongit and its parents for a .aw/ (or legacy .agents/) project directory.
    Are you inside your repository? cd into the repo (or a subdirectory of it), or pass --dir <repo>.
    summary: no AW project found at the working directory or any ancestor; cd into the repository or pass --dir <repo>
    next_action: None
    captured_stdout: ''
    captured_stderr: ''
    ============================================================
    LABEL: Case (d-variant) Git repo without AW (explicit=False)
    PATH: /tmp/tmp1z0n0t3n/git_no_aw
    EXPLICIT: False
    may_proceed: False
    human_message:
    aw attention: no AW project found here.
    Checked /tmp/tmp1z0n0t3n/git_no_aw and its parents for a .aw/ (or legacy .agents/) project directory.
    Are you inside your repository? cd into the repo (or a subdirectory of it), or pass --dir <repo>.
    /tmp/tmp1z0n0t3n/git_no_aw IS a git repository, but agent-workflows is not installed in it.
    Install it there with: aw install /tmp/tmp1z0n0t3n/git_no_aw
    summary: no AW project found at the working directory or any ancestor; cd into the repository or pass --dir <repo>
    next_action: RefusalNextAction(command='aw install .', description='install agent-workflows in this repo')
    captured_stdout: ''
    captured_stderr: ''
    ```

    Verification checks:
    - (a) reports `may_proceed: True`, `human_message: None`, `summary: None`, `next_action: None`.
    - (b) reports `may_proceed: False`, its human text CONTAINS enclosing root `/tmp/tmp1z0n0t3n/real_proj` and literal `aw attention --dir /tmp/tmp1z0n0t3n/real_proj`, and `next_action: None`.
    - (c) reports `may_proceed: False` with `next_action: None`.
    - (d) reports `next_action: RefusalNextAction(command='aw install .', description='install agent-workflows in this repo')`.
    - Non-explicit variants of (c) and (d) report `summary: no AW project found at the working directory or any ancestor; cd into the repository or pass --dir <repo>`, with next action preserved for (d).
    - F-14 Negatives for case (b):
      `"is not installed in it" in res_b.human_message` -> `False`
      `res_b.next_action_command == "aw install ."` -> `False`
    - Path-freeness across all cases:
      Neither fixture paths nor enclosing root appear in `summary` or `next_action` (asserted across all 6 cases).
    - Human text produced by `no_project_message`:
      `human_msg = no_project_message(verb, where, explicit=bool(explicit_dir))`
    - Body check for forbidden print/record symbols:
      ```
      $ python3 -c "import inspect; from agent_workflows import project_context; src = inspect.getsource(project_context.nonsurveyable_root_refusal); body = src.split('\"\"\"')[-1]; print('body check:', [w for w in ['sys.stdout', 'sys.stderr', 'print(', 'CommandResult', 'get_renderer', 'result_types'] if w in body])"
      body check: []
      ```
      Captured stdout and stderr are both empty string `''`.
    - Additivity check:
      `git diff agent_workflows/project_context.py` shows `classify_project_dir`, `is_project_dir`, `_is_project_marker`, `find_project_root`, `resolve_verb_repo_root`, and `no_project_message` completely untouched.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the committed docstring in full. CONFIRM BY QUOTING IT that it states: the call shape (resolve, call this, emit-and-return on may-proceed-false); `attention.run` as the reference implementation; the path-free trap AND the reason it is enforced rather than stylistic (the schema refuses an absolute home path, raising in the renderer); the exit-2 rule and that no site may build an `exit_code=3` record; that refuse-or-proceed POLICY stays with the verb, with the read-versus-write distinction named; and a pointer to `resolve_verb_repo_root` for the recorded no-climb decision. CONFIRM the docstring does NOT assert a 3-versus-2 human/machine split, which F-09 measures is stale, by grepping it for `3` in that context and explaining any hit. CONFIRM no behavior changed in this item by pasting `git diff --stat` for the file and showing the docstring lines only.
  - Observed evidence:
    Committed docstring of `nonsurveyable_root_refusal` in full:
    ```python
    """Turn a resolved root and explicit-dir flag into a complete, honest refusal.

    Converts a resolved root plus the explicit-dir flag into everything a verb
    needs to refuse honestly when the resolved directory is not an AW project root:
    the human stderr text, the path-free machine summary, and the structured next action.
    Pure, read-only, and side-effect-free: writes no output to stdout or stderr,
    builds no CommandResult, and imports neither renderers nor result_types.

    Call shape for a converting verb:
        repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
        explicit_dir = bool(getattr(args, "dir", None))
        refusal = nonsurveyable_root_refusal(verb, repo_root, explicit_dir=explicit_dir)
        if not refusal.may_proceed:
            if ctx.is_agent or ctx.is_json:
                res = CommandResult(
                    command=verb,
                    status="cannot-run",
                    exit_code=2,
                    summary=refusal.summary,
                    next_actions=(
                        [
                            NextAction(
                                command=refusal.next_action_command,
                                description=refusal.next_action_description,
                            )
                        ]
                        if refusal.next_action is not None
                        else []
                    ),
                )
                return get_renderer(ctx).emit(res, ctx)
            sys.stderr.write(refusal.human_message + "\n")
            return EXIT_CANNOT_RUN

    Reference implementation:
        See ``attention.run`` (in ``agent_workflows/attention.py``) as the reference
        implementation demonstrating this exact emission block in production.

    Traps:
        1. PATH-FREE MACHINE SUMMARY: A machine record must never carry an absolute path.
           This is enforced rather than stylistic: the schema (``agent_schema``) refuses
           an absolute home path in any string field and raises ValueError in the renderer
           before a byte is emitted, causing an empty stdout and breaking the protocol.
           The machine summary returned here is strictly path-free; only the human message
           names paths.
        2. EXIT CODE CONTRACT: A ``cannot-run`` record must carry exit 2, never 3.
           ``aw.agent/v1`` admits only integer exit codes in (0, 1, 2); an ``exit_code=3``
           record cannot serialize and raises in the renderer. Both human and machine
           surfaces return exit 2 for this condition (retiring the earlier human exit 3
           so one condition has one uniform exit code across all surfaces; there is no
           split between human and machine exit codes). No site in the package builds
           an ``exit_code=3`` record.

    Policy:
        Whether a given verb should refuse is the verb's policy, not this primitive's.
        A read-class verb surveying nothing produces a false clean claim (an
        anti-greenwashing invariant violation) and should refuse. A write-class verb
        targets an operator's explicit destination and fails loudly and locally without
        touching the real records tree (IPD lmyeas OQ-01). The primitive serves both
        and chooses neither.

    No-climb rule:
        An explicit ``--dir`` still NEVER climbs upward to find an enclosing project root.
        See ``resolve_verb_repo_root``'s docstring for the recorded decision, rationale,
        and write-class safety hazards that govern why explicit ``--dir`` is honored verbatim.
    """
    ```

    Confirmations by quoting:
    1. Call shape:
       `repo_root = resolve_verb_repo_root(...)`
       `refusal = nonsurveyable_root_refusal(...)`
       `if not refusal.may_proceed:` emit machine record or write human message and return cannot-run exit.
    2. Reference implementation:
       "See ``attention.run`` (in ``agent_workflows/attention.py``) as the reference implementation demonstrating this exact emission block in production."
    3. Path-free trap and why it is enforced rather than stylistic:
       "PATH-FREE MACHINE SUMMARY: A machine record must never carry an absolute path. This is enforced rather than stylistic: the schema (``agent_schema``) refuses an absolute home path in any string field and raises ValueError in the renderer before a byte is emitted, causing an empty stdout and breaking the protocol."
    4. Exit-2 rule and no site may build an `exit_code=3` record:
       "EXIT CODE CONTRACT: A ``cannot-run`` record must carry exit 2, never 3. ``aw.agent/v1`` admits only integer exit codes in (0, 1, 2); an ``exit_code=3`` record cannot serialize and raises in the renderer. Both human and machine surfaces return exit 2 for this condition (retiring the earlier human exit 3 so one condition has one uniform exit code across all surfaces; there is no split between human and machine exit codes). No site in the package builds an ``exit_code=3`` record."
    5. Policy stays with the verb:
       "Whether a given verb should refuse is the verb's policy, not this primitive's. A read-class verb surveying nothing produces a false clean claim (an anti-greenwashing invariant violation) and should refuse. A write-class verb targets an operator's explicit destination and fails loudly and locally without touching the real records tree (IPD lmyeas OQ-01). The primitive serves both and chooses neither."
    6. Pointer to `resolve_verb_repo_root` for recorded no-climb decision:
       "An explicit ``--dir`` still NEVER climbs upward to find an enclosing project root. See ``resolve_verb_repo_root``'s docstring for the recorded decision, rationale, and write-class safety hazards that govern why explicit ``--dir`` is honored verbatim."

    Docstring grep for '3':
    ```
    $ python3 -c "import inspect; from agent_workflows import project_context; ds = inspect.getdoc(project_context.nonsurveyable_root_refusal); print([line for line in ds.splitlines() if '3' in line])"
    ['    2. EXIT CODE CONTRACT: A ``cannot-run`` record must carry exit 2, never 3.', '       ``aw.agent/v1`` admits only integer exit codes in (0, 1, 2); an ``exit_code=3``', '       surfaces return exit 2 for this condition (retiring the earlier human exit 3', '       an ``exit_code=3`` record.']
    ```
    All 4 hits are in Trap 2, explicitly explaining that exit 3 is retired and never emitted, with no split between human and machine surfaces. No hit asserts a 3-versus-2 split.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the committed test file and the run showing it PASSING with its count. CONFIRM BY QUOTING THE TEST CODE that it (a) builds every fixture under `tempfile` OUTSIDE any AW project, (b) pins all FOUR message cases including the git-repo-without-AW case that keeps `aw install .`, plus the two non-explicit variants and the exact shipped summary string per case, after asserting the no-project fixture precondition, (c) asserts the F-14 negatives on the subdirectory case, (d) asserts path-freeness of the machine summary and next-action against both the fixture path and the found root, (e) asserts purity via a before/after recursive inventory and silence via captured empty stdout/stderr, and (f) contains NO source-structure assertion (paste a grep of the test file for `inspect`, `ast.parse` and any read of `agent_workflows/*.py`, all returning nothing).
    PASTE THE MUTATION PROVING THE GUARD CAN FAIL: make the primitive return the generic no-project message for the inside-a-project case so the enclosing root is no longer named, paste the FAILING output showing THIS file catches it, revert, and paste the restored green run. A test that passes against both the correct and the mutated primitive pins nothing.
    ALSO CARRY THE WHOLE-PLAN NO-REGRESSION EVIDENCE HERE, as the last item before commit: PASTE the BARE `python3 -m pytest` output including its `N passed` summary line and reconcile it against A BASELINE YOU MEASURED YOURSELF on a clean tree, naming any failing node id and whether it was already failing. The authored baseline was `3 failed, 4624 passed, 2 skipped` at HEAD `9de38b09f` with the three node ids named in Required tests; do NOT treat that as current. Explain ANY new failure against a named E-item rather than waving it through. PASTE the focused test files' output. PASTE `python3 -m agent_workflows check`. PASTE `aw ipd lint` reporting conforming. PASTE `rg -n "exit_code=3" agent_workflows/` confirming no new site. PASTE `aw sanitize --agent`. PASTE `git diff --cached --name-only` immediately before committing, which must list ONLY the two paths drawn from `- Scope-Paths:` and nothing else.
  - Observed evidence:
    Committed test file `tests/test_nonsurveyable_root_refusal.py`:
    ```python
    # See full committed file at tests/test_nonsurveyable_root_refusal.py
    ```
    Test run showing all 8 tests PASSING:
    ```
    $ python3 -m pytest tests/test_nonsurveyable_root_refusal.py
    ........                                                                 [100%]
    8 passed in 1.90s
    ```

    Code confirmation by quoting:
    (a) Fixtures built under tempfile outside any AW project:
        `self.temp_dir_obj = tempfile.TemporaryDirectory()`
        `self.fix_root = Path(self.temp_dir_obj.name).resolve()`
        `self.real_proj = self.fix_root / "real_project"`
        `self.deep_subdir = self.real_proj / "src" / "deep"`
        `self.nongit_dir = self.fix_root / "nongit"`
        `self.git_no_aw = self.fix_root / "git_no_aw"`
    (b) Precondition asserted:
        `self.assertIsNone(find_project_root(self.fix_root))`
        `self.assertIsNone(find_project_root(self.nongit_dir))`
        `self.assertIsNone(find_project_root(self.git_no_aw))`
        Pins all 4 message cases plus 2 non-explicit variants and exact summary:
        `test_case_a_real_project_root`
        `test_case_b_project_subdirectory_explicit`
        `test_case_c_no_project_no_git_explicit`
        `test_case_d_git_repo_without_aw_explicit`
        `test_non_explicit_variant_no_project_no_git`
        `test_non_explicit_variant_git_repo_without_aw`
    (c) F-14 negatives on subdirectory case:
        `self.assertNotIn("is not installed in it", refusal.human_message)`
        `self.assertNotIn("aw install ", refusal.human_message)`
        `self.assertNotEqual(refusal.next_action_command, "aw install .")`
    (d) Path-freeness against fixture path and found root:
        `self.assertNotIn(str(self.deep_subdir), refusal.summary)`
        `self.assertNotIn(str(self.real_proj), refusal.summary)`
        `self.assertNotIn(str(self.fix_root), refusal.summary)`
    (e) Purity and silence:
        `self.assertEqual(stdout_buf.getvalue(), "", "stdout must be empty")`
        `self.assertEqual(stderr_buf.getvalue(), "", "stderr must be empty")`
        `self.assertEqual(snapshot_before, snapshot_after, "filesystem must be unmodified")`
    (f) No source-structure assertions:
        ```
        $ git grep -E "inspect|ast\.parse|agent_workflows/.*\.py" tests/test_nonsurveyable_root_refusal.py
        (exit 1 - no matches)
        ```

    Mutation proving test fails:
    Mutation applied: return generic message without enclosing root for inside-a-project case.
    Failing runner output:
    ```
    _______ NonsurveyableRootRefusalTests.test_case_b_project_subdirectory_explicit _______
        def test_case_b_project_subdirectory_explicit(self):
            refusal = nonsurveyable_root_refusal(verb="attention", repo_root=self.deep_subdir, explicit_dir=True)
            self.assertIn(str(self.real_proj), refusal.human_message)
    >       self.assertIn(f"aw attention --dir {self.real_proj}", refusal.human_message)
    E       AssertionError: 'aw attention --dir /tmp/tmpinj6ei_9/real_project' not found in 'aw attention: no AW project found at /tmp/tmpinj6ei_9/real_project/src/deep.'
    1 failed, 7 passed in 1.91s
    ```
    Restored run after reverting mutation:
    ```
    ........                                                                 [100%]
    8 passed in 2.05s
    ```

    Whole-plan no-regression evidence:
    - Baseline measured on clean tree at lane HEAD f52b584:
      `1 failed, 6912 passed, 2 skipped, 3 warnings in 685.22s (0:11:25)`
      Single pre-existing failure:
      `tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation`
      Delta of failing node ids after edits: 0 new failures.
    - Focused test suite output:
      ```
      $ python3 -m pytest tests/test_nonsurveyable_root_refusal.py tests/test_project_context.py tests/test_explicit_dir_subdir_resolution.py tests/test_explicit_dir_non_project.py tests/test_no_project_exit_is_cannot_run.py tests/test_attention.py
      135 passed in 8.00s
      ```
    - `python3 -m agent_workflows check`:
      Passes with no new diagnostics (14 errors, 4 warnings, 23 info - all pre-existing in unrelated backlog/plans).
    - `aw ipd lint`:
      `- >  ◕  approved     plan        20261002-dirsilent-01-i6mby8  [medium]  [blocking]  conforming`
    - `rg -n "exit_code=3" agent_workflows/`:
      Only 4 comments and 2 docstring lines explaining the prohibition of exit_code=3; no new executable site.
    - `aw sanitize --agent`:
      `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    - `git diff --cached --name-only` immediately before commit:
      `agent_workflows/project_context.py`
      `tests/test_nonsurveyable_root_refusal.py`
      `.aw/records/plans/pending/20261002-dirsilent-01-i6mby8-add-the-shared-non-surveyable-root-refusal-primitive-every-r.ipd.md`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. On approval, the executor follows the repository execution contract: commit ONLY the files this plan changes, limited to the two declared `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; paste ACTUAL runner output for every test claim rather than asserting success; and resolve every `V-*` item with concrete pasted evidence in a separate pass from the matching `E-*` mark.

WHAT APPROVAL IS APPROVING HERE IS A MECHANISM, NOT A USER-VISIBLE FIX. After this plan the measured defects of F-03 and F-04 are UNCHANGED: `aw specs check --dir <subdir>` still reports `all specs conform. 0 specs checked.` at exit 0. The deliverable is the shared primitive that Orders 02 to 04 call, and the argument for separating it is F-02: the refusal is already hand-rolled twice, and the `lmyeas` F-14 falsehood had to be fixed in both copies. A reviewer who wants a user-visible change in this plan is really asking for Orders 01 and 02 to be merged, which would put a new abstraction and the conversion of two fail-closed validators in one unit.

THIS PLAN IS ADDITIVE AND HAS NO DEPENDENCIES (`- Item-Dependencies: none`). It introduces a symbol with no callers, so it cannot regress a shipped surface, which is exactly why the two existing call sites are NOT refactored onto it here (Order 04 owns that). It must execute before Orders 02, 03 and 04, which declare `executed:i6mby8`; the runner sorts by dependency depth and re-checks edges at dispatch, so no human sequencing step is needed.

SCOPE FENCE (a DECLARATION for the runner to reconcile against, not an instruction to stop). Modify exactly the two paths in `- Scope-Paths:`. Specifically DO NOT: convert any verb to call the primitive (Orders 02 to 04 own that); refactor `attention.run` or `cli._run_plans` (Order 04); change `classify_project_dir`, `is_project_dir`, `_is_project_marker`, `find_project_root`, or `resolve_verb_repo_root` body or docstring; change what `no_project_message` SAYS; make anything climb from an explicit `--dir`; import `renderers` or `result_types` into `project_context`; build an `exit_code=3` record or reintroduce a human exit 3; put an absolute path into any machine-bound string; widen `agent_schema`; or fix the three pre-existing suite failures on the way past. An out-of-scope edit that proves NECESSARY is to be MADE and then JUSTIFIED with `aw ipd finalize --scope-reason`, and a declared path you end up not modifying needs a `--scope-ack`; neither is a reason to stop.

ON COMPLETION, the executor runs `aw ipd lint --phase pre-transition` until it reports conforming and verifies every `V-*` item carries pasted evidence. The terminal transition is then owed UNCONDITIONALLY but its OWNER is CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER performs `aw ipd begin`/`aw ipd finalize` and the executor must NOT (a worker-role process is refused with `AW-LIFECYCLE-ROLE-001`, enforced inside the finalize transaction itself, so `aw ipd set executed` is refused there too because it delegates into that same transaction); executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll the move with `git mv` to `executed/` and never hand-edit `- Status: executed`. Backlog item `rgl2d4` is NOT to be closed `done` by this plan: it carries `- Blocks-Release: next`, and its gate is preserved through the handoff by the `- From-Backlog: rgl2d4` link on all five plans in this Set, so it reaches `done` only once the LAST carrier executes.
