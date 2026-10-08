# IPD: Delete the dead cli._completion_configured and prove no caller loses a behavior

- Date: 2026-10-01
- Kind: child
- Concern: `cli._completion_configured` is unreachable production code that still reads as the live predicate for "is completion installed", and it has read that way for ten days. Plan `4y95tp` widened the question it answered into the three-state `absent`/`current`/`stale` classification and introduced `cli._completion_state` to ask it, deleting the one call site in `cli._completion_tip` in commit `f9a378087` (2026-09-21) without deleting the function. Measured in this worktree: `grep -rn "_completion_configured" --include="*.py" .` returns exactly three hits and NONE is a call (the definition in `cli.py`, a back-reference inside its own successor's docstring, and a docstring line in `tests/test_completion.py`). The cost is not the nine lines; it is that a reader looking for the completion-presence predicate finds two functions with no way to tell which one runs, and the dead one's docstring makes the stronger-sounding claim. Verified by history: `git log -S "if _completion_configured()"` shows the call introduced in `de51d91e8` and removed in `f9a378087`, so this is residue from a completed supersession rather than a predicate awaiting a caller.
- Scope: Delete `cli._completion_configured` outright and repoint the one stale back-reference inside `cli._completion_state`'s docstring at `completion.is_completion_installed`, which is the function that actually still performs the PRESENCE check the sentence is describing. Verify (and correct only if regressed) the test docstring in `tests/test_completion.py` that formerly named the dead function; executed plan `s2yf26` already corrected it (PR-001). Prove by full-suite run that no caller, no test, and no dynamic lookup loses a behavior. EXCLUDES touching `completion.is_completion_installed`, which has a live production caller and is NOT dead (`cli._configure_completion` calls it); EXCLUDES any change to `cli._completion_state`'s or `cli._completion_tip`'s BEHAVIOR; EXCLUDES adding any dead-code detector, lint rule, or tool (see `## Deferred`); EXCLUDES a test asserting the symbol is absent, which would be the code-pinning GUIDING_PRINCIPLES P16 forbids (see `## Deferred`).
- Scope-Paths: agent_workflows/cli.py, tests/test_completion.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: rayd4c
- Set: rayd4c
- Order: 1
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: yi24m0
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-003

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003. `s2yf26` has since EXECUTED (`00c460141`) and already corrected the test docstring, so E-02 is now verify-only and the repo-wide grep bar now expects exactly one hit (an absence assertion in `tests/test_completion_stale_notice.py`); hardcoded test counts replaced by executor-derived baselines; gate states runner/executor finalize ownership.
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `rayd4c`. The deletion was PROTOTYPED rather than reasoned about, twice, because the item's own risk claim ("near-zero") is exactly the kind of claim that deserves measurement rather than agreement. First the attribute was deleted from the live module in-process and `tests/test_completion.py` was run against it (31 passed), which proves no test reaches it even by dynamic lookup; then the real edit was applied to `cli.py` and the BARE full suite run (3692 passed, 2 skipped, unchanged from the baseline measured immediately before), after which the prototype was reverted so this turn commits only the plan. Also resolved the item's stated ordering concern against evidence rather than honoring it: the item says this "should follow s2yf26 rather than race it", but the two edits are measured non-overlapping, and plan `s2yf26`'s own E-06 already rewrites the very test docstring E-02 here touches, so a hard dependency edge would make this plan unrunnable for no benefit while a `none` edge leaves a bounded, mechanical conflict either order. Stated as F-05 so a reviewer can dispute the call.
  (Review note 2026-10-07: `s2yf26` has since executed, so F-05's ordering concern is moot; see PR-001.)
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Leave exactly one predicate in `cli.py` answering "what is the state of the installed completion script", so a reader cannot pick the wrong one. The dead function is removed, and the two docstrings that still narrate it are repointed at what actually runs.

The whole plan turns on one measured fact: the supersession is COMPLETE, not in progress. `cli._completion_state` fully replaced `cli._completion_configured` in commit `f9a378087`, which deleted the only call site; what remains is a function body that no path reaches plus two sentences describing it as live. So this is not a judgement call about whether some caller might want a PRESENCE check later: `completion.is_completion_installed` is that check, it is public, it still has a production caller in `cli._configure_completion`, and it is untouched here. The only thing being removed is a nine-line private wrapper around it that nothing calls.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: remove the dead function and repoint what narrated it

- [x] E-01 Delete `cli._completion_configured` in full (the `def` line, its one-line docstring quoting "True when OUR drop-in completion is already installed for the detected shell (jolfpj E-04)", the `try`/`except Exception` body returning `_completion.is_completion_installed(_detect_shell())` or `False`, and the two blank lines that separated it from `cli._completion_state`). Then repoint the stale back-reference in `cli._completion_state`'s own docstring: the sentence currently opening "Widens `_completion_configured`'s PRESENCE question into the three states that actually exist" must name `completion.is_completion_installed` instead, because that is the function that actually performs the PRESENCE check being contrasted and it is the one a reader can still go read. Change no behavior: `cli._completion_state`, `cli._completion_tip`, and `completion.is_completion_installed` keep their bodies byte-identical apart from that one docstring sentence.
  DO NOT ALSO DELETE `completion.is_completion_installed`, which looks adjacent but is NOT dead: it retains a live production caller in `cli._configure_completion` (the branch returning early when completion is "already ours; nothing to offer") plus two direct test callers. Deleting it is the one plausible over-reach here and it would break the setup prompt.
  - Depends on: none
  - Expected outcome: `grep -rn "_completion_configured" --include="*.py" agent_workflows/` returns zero hits; `grep -rn "_completion_configured" --include="*.py" .` returns exactly one hit, `tests/test_completion_stale_notice.DocumentationAndDocstringTests.test_test_completion_docstring_updated`'s `self.assertNotIn("_completion_configured", doc)` (a string literal inside an absence assertion owned by executed plan `s2yf26`, NOT a reference to the function; leave it untouched, it is out of scope and still passes after the deletion) (PR-001); `python3 -c "import agent_workflows.cli as c; print(hasattr(c, '_completion_configured'), c._completion_state())"` prints `False` followed by a valid verdict; `cli._completion_state`'s docstring no longer names a symbol that does not exist.
  - Execution state: performed

- [x] E-02 Correct the one test docstring that still describes the deleted function as the composing predicate. `tests/test_completion.StaleCompletionWarningTests`'s class docstring asserts that "`_completion_configured` composes `is_completion_installed`, a PRESENCE check, so a stale file took the same silent branch as a current one". After E-01 that sentence names a symbol that does not exist, so a reader of the test learns a false thing about the code under test. Preserve the sentence's MEANING, which is historically accurate and worth keeping (the gap really was that a presence check could not distinguish stale from current); change only the subject, so it describes the presence check by the name that still resolves (`completion.is_completion_installed`) and, if it refers to the historical predicate at all, marks it as removed rather than current. Amend prose only: add, remove, and weaken no assertion in that class.
  PLAN `s2yf26` HAS LANDED (executed, commit `00c460141`), and at review on 2026-10-07 the class docstring already reads "`is_completion_installed` was a PRESENCE check, so a stale file took the same silent branch as a current one", naming no deleted symbol (PR-001). So E-02 is EXPECTED to be verify-only: re-read the docstring at execution, and if it still names no `_completion_configured`, record that E-02 required no edit, leave `tests/test_completion.py` unmodified, and do NOT rewrite `s2yf26`'s wording to taste. Only if the text has regressed to naming the deleted symbol, apply the prose correction above. In a manual run, an unmodified `tests/test_completion.py` needs `--scope-ack tests/test_completion.py=E-02 verify-only, s2yf26 already corrected it` at finalize.
  - Depends on: E-01
  - Expected outcome: `grep -rn "_completion_configured" --include="*.py" .` returns ONLY the single `tests/test_completion_stale_notice.py` absence-assertion literal described in E-01, and in particular no hit in `tests/test_completion.py`; the docstring still explains why a presence check could not report staleness; `python3 -m pytest tests/test_completion.py` passes with its collected count equal to the executor's own pre-edit collection of that file (31 at review; the review-time number is context, not the bar) (PR-002).
  - Execution state: performed
  - Execution note: verify-only; s2yf26 already corrected it in commit 00c460141 and tests/test_completion.py already names is_completion_installed without referring to _completion_configured.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this plan is by symbol or by quoted string for that reason.
- NO SPEC GOVERNS SHELL COMPLETION, verified rather than assumed: `grep -rln "tab-completion\|tab completion\|shell completion\|aw completion" .aw/records/specs/` returns nothing at all. Plan `4y95tp` independently records the same conclusion ("No spec governs completion; the docstrings are the contract"), and plan `s2yf26` re-verified it. So this plan amends no spec, declares no `.spec.md` in `- Scope-Paths:`, and the docstring edits in E-01 and E-02 ARE the contract amendment.
- NO TEST MAY ASSERT THE SYMBOL IS GONE. GUIDING_PRINCIPLES P16 prohibits reading production source with `inspect`, `ast`, regex, or substring search, and prohibits symbol censuses as a proxy for correctness; AGENTS.md repeats the prohibition verbatim in the execution contract. A `assertFalse(hasattr(cli, "_completion_configured"))` test is precisely a symbol census, so the correct proof that this deletion is safe is the UNCHANGED full-suite pass, not a new assertion. This is the single most likely wrong turn for an executor who wants to "add coverage" for a deletion, which is why it is stated here and carried into `## Deferred`.
- RUN THE SUITE BARE as `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so a bare run is already quiet and already parallel. Adding another `-q` compounds into `-qq` and suppresses the `N passed` summary line that V-02 requires pasted; `-n0` makes it several times slower. A narrowed per-test count needs `-o addopts=""` rather than fighting the flags individually.
- THE DEFAULT RUN DESELECTS TWO MARKER CATEGORIES, so a bare pass is not a whole-suite pass. Measured here: the bare run reports "208 tests were deselected", and exactly one of those deselected tests is in the file this plan touches (`tests/test_completion.CompletionInstallSubprocessTests::test_module_cli_install_then_uninstall`, marked `slow`). V-02 therefore requires that one test run explicitly as well, since a `slow`-marked subprocess test of the completion CLI is exactly where an import-time break from a deletion would hide from the default run.
- THE COMPLETION TEST STYLE IS A REAL TEMP FILESYSTEM, NOT MOCKS: `_DropInFixture` in `tests/test_completion.py` builds a real temp `HOME` plus `XDG_DATA_HOME`/`XDG_CONFIG_HOME`. Nothing in this plan adds a test, but an executor reading the file should not mistake the style for something to change.

## Findings

| Id | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | LOW | `cli._completion_configured` HAS ZERO CALLERS OF ANY KIND, static or dynamic, and this is the plan's whole premise. Three independent measurements. (1) Repository-wide, `grep -rn "_completion_configured" --include="*.py" .` returns exactly three hits: the `def` in `cli.py`, the back-reference inside `cli._completion_state`'s docstring, and the `tests/test_completion.py` class docstring. None is a call. (2) Widened past Python to every tracked text file (`--include` for `.py .cfg .toml .json .md .sh .yml .yaml`), the only additional hits are in `.aw/records/` prose (this backlog item and two executed/pending plans), never in a config, manifest, hook, or workflow. (3) No dynamic-lookup vector exists: `cli.py` defines no `__all__` (`grep -c "__all__"` returns `0`), the repository contains no `getattr(cli, ...)` call at all, and the twelve `from agent_workflows.cli import ...` sites in tests name only `_build_parser`, `main`, `expand_host_review_argv`, and `expand_host_integrate_argv`. | all three greps driven in this worktree 2026-10-01 |
| F-02 | LOW | THE SUPERSESSION IS COMPLETE AND DATED, so this is residue rather than a predicate awaiting its caller. `git log -S "if _completion_configured()" -- agent_workflows/cli.py` returns exactly two commits: `de51d91e8` (2026-08-29, `feat(tabcomp-03)`) which introduced the call, and `f9a378087` (2026-09-21, the `4y95tp` work commit) which removed it. Confirmed by reading the pre-supersession file: `git show f9a378087^:agent_workflows/cli.py` contains both the `def` and a live `if _completion_configured():` inside `_completion_tip`, and the post-commit file contains only the `def`. The function has therefore been unreachable for ten days by a deliberate replacement, not by an accident that might be reverted. | both git commands driven in this worktree |
| F-03 | LOW | DELETION IS BEHAVIORALLY INERT, PROTOTYPED TWICE RATHER THAN ARGUED. (1) IN-PROCESS ATTRIBUTE REMOVAL: `del agent_workflows.cli._completion_configured` followed immediately by `pytest tests/test_completion.py -o addopts=""` in the same interpreter reported `31 passed in 22.33s`, which is a stronger result than a source-level grep because it also rules out any reflective access at test time. (2) THE REAL EDIT: applying E-01 to `cli.py` (a `1 insertion, 11 deletions` diff) and running the BARE full suite reported `3692 passed, 2 skipped, 3 warnings`, byte-identical in counts to the baseline `3692 passed, 2 skipped, 3 warnings` measured immediately before on the unmodified tree. The `slow` completion subprocess test was additionally run against the modified tree and passed. The prototype was then reverted (`git checkout -- agent_workflows/cli.py`), so no code change is committed by this authoring turn. | both prototypes driven in this worktree 2026-10-01; baseline and post-edit suite summaries captured |
| F-04 | MEDIUM | `completion.is_completion_installed` IS NOT DEAD AND MUST NOT BE SWEPT UP, which is the one real risk in an otherwise inert change. It retains a live production caller: `cli._configure_completion` tests `if _completion.is_completion_installed(shell): return  # already ours; nothing to offer.`, which is the branch that stops the setup wizard offering an install the user already has. It also has two direct test callers in `tests/test_completion.py`. So the deletion stops at the private wrapper; the public presence check survives, and E-01's docstring repoint deliberately points the reader AT it. An executor who reads "delete the dead presence check" as including this function would break the setup prompt's idempotence. | `grep -n "is_completion_installed" agent_workflows/*.py` returns the two `cli.py` call sites plus the definition and its own docstring; `grep -rn` over `tests/` returns three further hits |
| F-05 | MEDIUM | THE ITEM'S ORDERING INSTRUCTION IS NOT HONORED AS A DEPENDENCY EDGE, and a reviewer should weigh this deliberately. The backlog item says this work "should follow `s2yf26` rather than race it, since both touch the same neighborhood of `cli.py`". Measured, the two edits do not overlap: `s2yf26` (pending, `approved`) declares `- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion_stale_notice.py, README.md`, and its `cli.py` work is in `_dispatch`, `main`, `_build_parser`, and `_run_completion`, none of which this plan touches. The ONE genuine collision is `tests/test_completion.py`'s class docstring, which `s2yf26` E-06 also rewrites and which THIS plan's E-02 also rewrites, and it collides in either order. Three reasons not to declare `executed:s2yf26`: that plan is `approved` but unexecuted, so the edge would make this plan unrunnable until it lands, for a nine-line deletion; the runner gives every execute item an isolated worktree returning through merge-and-revalidate, so file overlap is not a runtime hazard (AGENTS.md states this directly and names the shared sort/dispatch symbols); and E-02 is written to be idempotent, instructing the executor to verify and record no-edit if the sentence is already corrected. The residual cost is a possible one-line textual merge conflict, which is bounded and mechanical. | `s2yf26`'s front matter and E-06 read in this worktree; `aw` queue semantics per AGENTS.md "The runners own ordering, isolation, and orchestrators" |
| F-06 | LOW | THE READER-CONFUSION COST IS REAL, which is what makes this worth doing at all rather than leaving as harmless clutter. The two functions sit ADJACENT in `cli.py` (the dead `def` immediately precedes `_completion_state`), both take no arguments, both resolve the shell through `_detect_shell()`, and both wrap a `completion` module call in `try`/`except Exception` with a soft fallback. The dead one's docstring is the more assertive of the two ("True when OUR drop-in completion is already installed"), so a reader scanning for the live predicate has no signal distinguishing them except the superseding function's own back-reference, which currently points INTO the dead one. That back-reference is why E-01 repoints rather than merely deletes: removing the function alone would leave `_completion_state`'s docstring naming a symbol that no longer exists, trading one confusion for another. | both docstrings read in `agent_workflows/cli.py`; adjacency confirmed by the prototype diff showing the deletion immediately above `def _completion_state` |
| F-07 | LOW | NO DEAD-CODE DETECTOR EXISTS IN THIS REPOSITORY, so nothing would have caught this and nothing will catch the next one. `grep -n "vulture\|F401\|unused" pyproject.toml setup.cfg` returns no hit. Recorded as a fact rather than as a proposal: adding one is a tooling decision with a false-positive budget (this codebase is full of legitimately uncalled-from-Python surfaces such as parser callbacks and host adapters), it is far outside a nine-line deletion, and it is declined in `## Deferred` rather than carried, because an unfixed defect is not what this is. | grep driven in this worktree |

## Proposed changes (ordered, validatable)

1. `agent_workflows/cli.py` loses `_completion_configured` entirely, and `_completion_state`'s docstring sentence that named it now names `completion.is_completion_installed`, the function that still performs the PRESENCE check the sentence contrasts against (E-01).
2. `tests/test_completion.py`'s `StaleCompletionWarningTests` class docstring is verified to name no deleted symbol (already true after `s2yf26`; edited only if regressed); no assertion in that class changes (E-02).
3. Nothing else changes. No test is added, no detector is introduced, `completion.is_completion_installed` is untouched, and the behavior of `_completion_state`, `_completion_tip`, and the setup prompt is byte-identical.

## Deferred / out of scope (with reason)

- A TEST ASSERTING `cli._completion_configured` IS ABSENT.
  - Carrier-Declined: SUCH A TEST MUST NOT EXIST, so there is nothing to carry. It is a symbol census over production source, prohibited by GUIDING_PRINCIPLES P16 and repeated in AGENTS.md ("NEVER assert on caller counts, symbol censuses, or module line counts as a proxy for correctness"). It would also be vacuous: it passes the moment the function is gone and can never fail for any reason a human cares about, while permanently pinning a private name. The correct evidence that this deletion is safe is the unchanged full-suite pass that F-03 measured, which is behavioral.
- ADDING A DEAD-CODE DETECTOR (vulture, ruff `F401`-class unused-symbol rules, or a custom census) SO THE NEXT ONE IS CAUGHT AUTOMATICALLY (F-07).
  - Carrier-Declined: NOT AN UNFIXED DEFECT, and declining is the honest record rather than filing an item that asserts an obligation. This is a new quality gate with a real false-positive budget in a codebase full of legitimately uncalled-from-Python surfaces (argparse callbacks, host adapters, generated shims), so it needs its own design, its own allowlist policy, and a maintainer's taste about CI noise. Filing a carrier would claim the repository owes itself the tool; it does not, and a nine-line deletion is not the place to decide it. If a maintainer wants it, that decision is the work.
- REFACTORING OR CONSOLIDATING `cli._completion_state`, `cli._completion_tip`, OR `completion.is_completion_installed` WHILE IN THE NEIGHBORHOOD.
  - Carrier-Declined: NOTHING IS WRONG WITH THEM, so there is no defect to carry. All three are live, tested, and behave as documented; `is_completion_installed` specifically still serves `cli._configure_completion` (F-04). AGENTS.md forbids broadening scope opportunistically, and the item's own framing is a deletion.
- THE BROADER QUESTION OF WHETHER OTHER SUPERSEDED PRIVATE HELPERS SURVIVE ELSEWHERE IN `cli.py`.
  - Carrier-Declined: UNMEASURED, so filing it would be the "unmeasured hunch" AGENTS.md says not to file. Nothing in this work surveyed the module for other residue, and asserting that more exists without having looked would be a claim about code this plan has not read. A real survey is the detector question above.

## Scope check

- Over-scope: none. Two E-items, both required by the item's single concern: E-01 is the deletion itself plus the back-reference it necessarily invalidates (deleting without repointing would leave `_completion_state`'s docstring naming a nonexistent symbol, which is the same class of defect being fixed), and E-02 is the one other place in the repository that still names the symbol in a way a reader would believe.
- Under-scope: THE REPOSITORY STILL HAS NO WAY TO NOTICE THE NEXT DEAD HELPER. This deletion is found-by-hand residue from one supersession, and nothing added here would catch a second. Stated so a reviewer sees the limit rather than inferring a general cleanup; the detector is declined above with its reason.
- Under-scope: `.aw/records/` PROSE STILL NAMES THE DELETED SYMBOL and is deliberately left alone. Executed plan `4y95tp` cites `_completion_configured` several times with line numbers, and AGENTS.md forbids changing what an executed plan records. Pending plan `s2yf26` names it in F-08 and its `## Deferred` carrier, which is a correct record of the handoff that produced this plan. The backlog item itself names it. None of these is code, none misleads a reader about what runs today, and rewriting them would falsify history.
- Under-scope: NO BEHAVIOR IMPROVES FOR ANY USER. This is a readability change with zero runtime effect, which is why it is `chore` and `low` and why it carries no release gate. If a reviewer wants a user-visible justification there is none, and that is the honest position rather than an argument to be constructed.

## Required tests / validation

NO NEW TEST IS WRITTEN, and that is a deliberate conclusion rather than an omission. The only test one could write for a deletion is an absence assertion over production source, which GUIDING_PRINCIPLES P16 prohibits and which would be vacuous (see `## Deferred`). The behavioral proof of a deletion is that the existing suite, which exercises every surface that could have reached the symbol, passes UNCHANGED.

Validation is therefore entirely over existing coverage, and it must be run rather than reasoned about:

- Static absence (E-01, E-02): `grep -rn "_completion_configured" --include="*.py" agent_workflows/` returns zero hits, and the repository-wide grep returns only the `tests/test_completion_stale_notice.py` absence-assertion literal (PR-001). Any other hit, including one in `tests/test_completion.py`, means E-01 or E-02 is not done.
- Import and behavior integrity (E-01): `agent_workflows.cli` imports, `hasattr(cli, "_completion_configured")` is `False`, and `cli._completion_state()` still returns a valid verdict from the enum `absent`/`current`/`stale`.
- The directly affected file (E-02): `python3 -m pytest tests/test_completion.py` passes with its collected count equal to the executor's pre-edit collection (`python3 -m pytest -o addopts="" --collect-only -q tests/test_completion.py`, 31 at review).
- THE DESELECTED COMPLETION TEST, which the bare suite does NOT run: `python3 -m pytest -o addopts="" -m "slow or livecorpus" tests/test_completion.py` must pass. This is `CompletionInstallSubprocessTests::test_module_cli_install_then_uninstall`, a `slow`-marked subprocess exercise of the completion CLI, and it is the one place an import-time break from this deletion could hide from the default run. Skipping it would leave the headline claim resting on a run that deselected 208 tests.
- The whole fast suite: `python3 -m pytest` run BARE, with the `N passed` summary pasted and compared against the pre-change baseline. The counts must be IDENTICAL, not merely green: a deletion that changes a collected count has done something beyond deleting dead code.
- The setup prompt's surviving predicate (F-04): the pass of `tests/test_completion.SetupCompletionPromptTests` and `InstallShellCompletionTests` is the evidence that `completion.is_completion_installed` was not swept up, since those classes drive the branch that calls it.

## Spec / documentation sync

NO SPEC IS AMENDED, verified rather than assumed: `grep -rln "tab-completion\|tab completion\|shell completion\|aw completion" .aw/records/specs/` returns no file at all, and plan `4y95tp` independently records "No spec governs completion; the docstrings are the contract." `- Scope-Paths:` declares no `.spec.md`, so both runners' end-of-run spec reconciliation should report zero declared and zero changed specs.

Because the docstrings ARE the contract here, they are the deliverable rather than decoration, and both edits are contract edits:

- `cli._completion_state`'s docstring stops citing a deleted symbol and cites `completion.is_completion_installed`, so the PRESENCE-versus-three-state contrast it draws remains checkable by a reader who follows the reference (E-01).
- `tests/test_completion.StaleCompletionWarningTests`'s docstring keeps its historical account of why a presence check could not report staleness, but attributes it to the function that still exists (E-02).

NO USER-FACING DOCUMENTATION CHANGES. `README.md` is not in scope and was checked: no tracked `.md` outside `.aw/records/` mentions either symbol, because both are private helpers. The AGENTS.md dash rule therefore does not bind any prose this plan authors, since docstrings are internal artifacts.

## Open questions

### OQ-01: Should this plan declare a dependency on `s2yf26` instead of `none`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, RESOLVED FROM REPOSITORY EVIDENCE rather than deferred, and recorded because the backlog item explicitly asks for the opposite. The item says this should "follow `s2yf26` rather than race it". Measured, the `cli.py` regions do not overlap at all: `s2yf26` edits `_dispatch`, `main`, `_build_parser`, and `_run_completion`, while this plan edits only `_completion_configured` and one docstring line in `_completion_state`. The single real collision is the `tests/test_completion.py` class docstring that both plans rewrite, and it collides symmetrically, so an edge does not remove the conflict, it only picks which plan absorbs it. Against that, `executed:s2yf26` would block this plan behind an approved-but-unexecuted plan indefinitely, and the runner already isolates each execute item in its own worktree with a merge-and-revalidate gate, so file adjacency is not a runtime hazard. E-02 is written to be order-independent (verify, record no-edit if already corrected), which is the actual mitigation. Full reasoning and the alternatives in F-05.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the actual `git diff agent_workflows/cli.py` showing the whole function removed AND the docstring sentence repointed, with a deletion count consistent with removing the nine-line function plus its separating blank lines (the authoring prototype measured `1 insertion, 11 deletions`; a materially larger diff means something else was changed and FAILS this item). Paste `grep -rn "_completion_configured" --include="*.py" agent_workflows/` returning NO output. Paste a driven transcript of `python3 -c "import agent_workflows.cli as c; print(hasattr(c, '_completion_configured'), c._completion_state())"` showing `False` and a verdict in `absent`/`current`/`stale`. Paste the repointed docstring sentence verbatim, showing it names `completion.is_completion_installed`.
  - Required evidence (the F-04 over-reach guard, and this item FAILS without it): paste `grep -n "is_completion_installed" agent_workflows/cli.py agent_workflows/completion.py` showing the definition AND the surviving `cli._configure_completion` call site still present, plus the pass of `python3 -m pytest tests/test_completion.py -o addopts="" -k "SetupCompletionPrompt or InstallShellCompletion"`. A diff that also removed `completion.is_completion_installed` FAILS regardless of whether the suite is green, because it breaks the setup prompt's "already ours; nothing to offer" branch.
  - Observed evidence:
    `git diff agent_workflows/cli.py` (exactly 1 insertion, 11 deletions):
    ```diff
    diff --git a/agent_workflows/cli.py b/agent_workflows/cli.py
    index 1fb7fda1d..1d1d8b2bf 100644
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -8122,20 +8122,10 @@ def _install_all(args: argparse.Namespace, term: Term) -> int:
         return 1 if failed else 0


    -def _completion_configured() -> bool:
    -    """True when OUR drop-in completion is already installed for the detected shell (jolfpj E-04)."""
    -    try:
    -        from agent_workflows import completion as _completion
    -
    -        return _completion.is_completion_installed(_detect_shell())
    -    except Exception:
    -        return False
    -
    -
     def _completion_state() -> str:
         """The detected shell's completion state: ``absent``/``current``/``stale`` (compargs 4y95tp E-06).

    -    Widens `_completion_configured`'s PRESENCE question into the three states that actually exist, so
    +    Widens `completion.is_completion_installed`'s PRESENCE question into the three states that actually exist, so
         an installed-but-outdated script stops taking the silent branch. Fails soft to ``current`` on any
         error: a diagnostic that cannot read the file must not warn about it.
         """
    ```
    `grep -rn "_completion_configured" --include="*.py" agent_workflows/` returned no output (exit 1).
    Driven transcript:
    ```
    $ python3 -c "import agent_workflows.cli as c; print(hasattr(c, '_completion_configured'), c._completion_state())"
    False current
    ```
    Repointed docstring sentence verbatim:
    `    Widens `completion.is_completion_installed`'s PRESENCE question into the three states that actually exist, so`

    F-04 over-reach guard:
    `grep -n "is_completion_installed" agent_workflows/cli.py agent_workflows/completion.py`:
    ```
    agent_workflows/cli.py:8128:    Widens `completion.is_completion_installed`'s PRESENCE question into the three states that actually exist, so
    agent_workflows/cli.py:8511:        if _completion.is_completion_installed(shell):
    agent_workflows/completion.py:1109:def is_completion_installed(shell: str, target_dir: Optional[Path] = None) -> bool:
    agent_workflows/completion.py:1121:    compargs 4y95tp E-06. ``is_completion_installed`` is a PRESENCE check, so an installed script that
    ```
    Pass of setup prompt tests:
    ```
    $ python3 -m pytest tests/test_completion.py -o addopts="" -k "SetupCompletionPrompt or InstallShellCompletion"
    ======================= 4 passed, 27 deselected in 4.72s =======================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff tests/test_completion.py` hunk (or, if `s2yf26` already corrected it, paste the current docstring plus an explicit statement that E-02 required no edit and why). Paste `grep -rn "_completion_configured" --include="*.py" .` returning ONLY the `tests/test_completion_stale_notice.py` `assertNotIn("_completion_configured", doc)` line (PR-001); any other hit FAILS this item. Paste the amended docstring showing it still explains why a presence check could not distinguish a stale script from a current one, so the historical account survives the rename. Confirm in the pasted diff that no `assert` line in `StaleCompletionWarningTests` changed: an assertion touched by a docstring correction FAILS this item.
  - Required evidence (the behavioral proof of the deletion, all three runs, and this item FAILS on a missing one): (a) `python3 -m pytest tests/test_completion.py` with its summary line, beside the executor's own pre-edit `--collect-only` count for that file, the two equal (31 at review, which is context and not the bar) (PR-002); (b) the DESELECTED completion test, `python3 -m pytest -o addopts="" -m "slow or livecorpus" tests/test_completion.py`, passing, since the bare run deselects 208 tests including that one and it is the only subprocess exercise of the completion CLI; (c) the BARE `python3 -m pytest` summary line, which must read IDENTICAL counts to the pre-change baseline the executor captures first. The baseline measured at authoring was `3692 passed, 2 skipped, 3 warnings`; the executor must capture its OWN baseline immediately before the edit, because other plans will have landed by then, and must paste BOTH numbers; the authoring number is context only. A changed collected count is a FAILED validation even if everything passes, because a pure deletion of unreachable code cannot change what is collected.
  - Observed evidence:
    `git diff tests/test_completion.py` is empty: E-02 required no edit because executed plan `s2yf26` (commit `00c460141`) had already landed and corrected the docstring.
    Current `StaleCompletionWarningTests` docstring in `tests/test_completion.py` (lines 2332-2340):
    ```python
    class StaleCompletionWarningTests(_DropInFixture):
        """An installed-but-OUTDATED completion script is reported, and never rewritten (4y95tp E-06).

        THE GAP THIS CLOSES. The generated file is written once by `aw completion install`, and NOTHING in
        the install/upgrade path regenerates it, so a framework upgrade that adds or renames a command
        leaves the user completing a vocabulary that no longer exists. Worse, it was UNREPORTABLE:
        `is_completion_installed` was a PRESENCE check, so a stale file took the same silent branch as
        a current one and the user had no way to find out before three-state classification was added.
        This defect's own fix would not have reached an already-installed user for exactly that reason.

        WARN, NEVER REWRITE (maintainer ruling 2026-09-12, OQ-01). The user's completion file is theirs
    ```
    No assert line in `StaleCompletionWarningTests` was touched.

    `grep -rn "_completion_configured" --include="*.py" .` returned ONLY the absence assertion:
    ```
    ./tests/test_completion_stale_notice.py:505:        self.assertNotIn("_completion_configured", doc)
    ```

    Behavioral runs:
    (a) Pre-edit collection: `python3 -m pytest -o addopts="" --collect-only -q tests/test_completion.py` -> 31 tests collected.
    Post-edit `python3 -m pytest tests/test_completion.py`:
    `30 passed in 19.12s` (1 deselected by -m/-k, total 31 = collected count 31).
    (b) Deselected completion test:
    ```
    $ python3 -m pytest -o addopts="" -m "slow or livecorpus" tests/test_completion.py
    ======================= 1 passed, 30 deselected in 5.31s =======================
    ```
    (c) Bare `python3 -m pytest` comparison:
    Pre-change baseline: `6737 passed, 2 skipped, 3 warnings in 373.12s (0:06:13)` (259 deselected)
    Post-edit run: `6737 passed, 2 skipped, 3 warnings in 557.41s (0:09:17)` (259 deselected)
    Counts are identical (6737 passed, 2 skipped, 3 warnings).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Two E-items in one focused pass over two files: a nine-line deletion plus one docstring sentence in `agent_workflows/cli.py`, and one docstring correction in `tests/test_completion.py`. E-02 depends on E-01 only because the docstring correction is meaningless until the symbol is gone. The work was prototyped end to end during authoring (F-03), so the executor is reproducing a measured change rather than attempting an unknown one.

EXECUTION CONTRACT. Commit only the two paths this plan declares in `- Scope-Paths:`, through `aw commit <plan> -- agent_workflows/cli.py tests/test_completion.py`, never `git add -A`, never `-a`, and never `git push`. Do not create or push a tag or a release. This checkout is shared, so verify the staged set with `git diff --cached --name-only` before committing and unstage anything you did not change with `git restore --staged <path>`. CAPTURE THE BASELINE SUITE RUN BEFORE EDITING, because V-02 requires comparing counts and a baseline taken afterwards proves nothing. Run the suite BARE as `python3 -m pytest` and paste the ACTUAL output including the `N passed` summary line; adding `-q` compounds with the configured `addopts` into `-qq` and suppresses that very line. Do not add a test asserting the symbol is absent, however tempting it is to "cover" a deletion: that is the code-pinning GUIDING_PRINCIPLES P16 forbids, and the unchanged suite is the evidence. Do not claim a validation passed without pasting its evidence. The declared scope is a DECLARATION the runner reconciles afterwards, not a stop condition. POST-GATE LIFECYCLE MOVE (PR-003): after every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition is tooled and its owner depends on dispatch: when `aw oc run`/`aw agy run` dispatched this plan the runner performs `aw ipd begin` and `aw ipd finalize` itself (an in-lane invocation is refused by design); in a manual run the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` (with the E-02 `--scope-ack` if `tests/test_completion.py` was left unmodified). Never `git mv` the plan and never hand-edit `- Status:`.
