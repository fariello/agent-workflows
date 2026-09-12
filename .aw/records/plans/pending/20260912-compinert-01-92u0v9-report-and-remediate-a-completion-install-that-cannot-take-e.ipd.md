# IPD: Report and remediate a completion install that cannot take effect

- Date: 2026-09-12
- Kind: child
- Concern: `aw completion install` REPORTS SUCCESS INTO A SHELL WHERE COMPLETION CANNOT WORK, and gives the user no way to tell. Reported by the maintainer 2026-09-12: they ran the verb, saw three `OK` lines plus "Next start a new bash shell (or run `exec bash`) to pick it up", did exactly that, and `aw <TAB>` still completed nothing.
  THE INSTALL WAS CORRECT AND THE DIAGNOSIS IS ENTIRELY OUTSIDE IT. Verified: the three files exist at `~/.local/share/bash-completion/completions/` (`aw` plus `agentwf` and `agent-workflows` symlinks), and sourcing the file by hand registers `complete -F _aw_completion aw`. The lazy loader resolves ALL THREE names correctly once bash-completion is present. Nothing about the generated script or the drop-in layout is wrong.
  THE ACTUAL CAUSE IS THAT BASH-COMPLETION ITSELF IS NEVER LOADED IN AN INTERACTIVE NON-LOGIN SHELL ON THAT MACHINE. `/usr/share/bash-completion/bash_completion` exists, but the only thing sourcing it is `/etc/profile.d/bash_completion.sh`, which runs for LOGIN shells. Measured: `bash -lic` reports `BASH_COMPLETION_VERSINFO=2` and a `-D` loader installed, while `bash -ic` reports `VERSINFO=unset` and no default completion at all. The user's `~/.bashrc` contains no `bash_completion` reference and there is no `~/.bash_profile` sourcing `.bashrc`. So in a new terminal tab, tmux pane, or plain `bash`, NOTHING is completed, `git` and `ssh` included; `aw` is not special.
  WHY THIS IS OUR DEFECT ANYWAY, WHICH IS THE POINT THE MAINTAINER MADE. The verb owns a promise it does not verify. It writes into a directory whose whole purpose is AUTO-DISCOVERY BY BASH-COMPLETION, so bash-completion being loadable is a PRECONDITION of the feature working, and the verb checks nothing: `grep -n 'profile.d|BASH_COMPLETION_VERSINFO|bash_completion' agent_workflows/completion.py` returns NOTHING. It then prints an unconditional success line and an instruction ("start a new bash shell") that is precisely the action that does NOT help. A user who trusts the output concludes the tool is broken, which is the outcome measured here.
  THE HONEST CONSTRAINT THAT MAKES THIS NON-TRIVIAL, and the reason this plan exists rather than a one-line fix: `install_shell_completion`'s docstring states "NO user rc/dotfile is ever read or written", the success message advertises "(no rc/dotfile modified)", and `engine.py`'s module docstring says the installer "Does NOT silently edit user gitignores". That restraint is deliberate and is worth keeping; a `.bashrc` edit is exactly the kind of surprise the project has repeatedly refused. So the fix is DETECTION plus an OFFER, not a silent write.
- Scope: Detect whether the installed completion can actually take effect, and when it cannot, say so precisely and offer the one-line remediation instead of reporting plain success. Covers the `aw completion install` verb, the `_configure_completion` step in the setup flow, and the success/next-step messages both print. EXCLUDES writing to any user rc/dotfile without explicit consent, changing the generated script (verified correct), changing the drop-in layout or the alias symlinks (verified correct), and any change for zsh/fish beyond the equivalent detection if it is cheap and correct.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion.py, README.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- From-Backlog: lalwnj
- Priority: medium
- Work-Kind: bug
- Blocks-Release: next
- Set: compinert
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 92u0v9

## Workflow history
- 2026-09-12 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED, none deferred, no open question added; readiness `go-pending-approval`. Record: `.aw/records/reviews/20260912-compinert-01-92u0v9-report-and-remediate-a-completion-install-that-cannot-take-e.review.md`. `aw ipd lint --phase author` CONFORMING (clean, 0 findings) before semantic review. DISCLOSURE: same agent/model family authored this plan, so this is a near-self-review; its value rests on what was EXECUTED, not re-read. TEN things were run: the F-1 grep was re-run verbatim; both discriminator commands were run bare AND under `env -i` with a fake HOME; `~/.bashrc` was read; its mtime was stat'd; `aw completion install --dry-run` was run to capture the real message; the nine no-rc-write promise sites were enumerated by grep; `_configure_completion` and `_configure_runner_profiles` were read for the `--yes` precedent; `install_wizard`'s `os.replace` shape was located; the README section its own test pins was read; and the probe cost was timed.
  THE PLAN'S DIAGNOSIS IS CORRECT AND ITS DESIGN IS SOUND, which is why every finding is a correction rather than a rejection. F-1 re-verified exactly (the grep returns only unrelated `generate_bash_completion` hits, so the precondition is checked nowhere), F-2 re-verified at both message sites, and the false pairing is real: `aw completion install --dry-run` prints four green `OK` lines and the useless next step.
  BUT THE MACHINE THE PLAN WAS MEASURED ON HAS SINCE BEEN FIXED BY HAND, and that invalidates the plan's central measurement rather than its thesis. Measured at review: `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'` now returns `2`, NOT empty, because `~/.bashrc` (mtime 2026-09-12 16:46) now contains the remediation stanza this plan proposes to offer, already wrapped in the exact paired fences E-03 prescribes. So an executor following V-01 literally cannot reproduce the stated `-ic` -> empty result, would see its evidence criterion fail, and might "fix" a predicate that is correct. The pre-fix state was reproduced under `env -i HOME=<empty> bash -ic` (unset) versus `bash -lic` (2), which is the durable way to demonstrate the discriminator and is now what the plan requires.
  THE ONE SUBSTANTIVE GAP was an undercount that would have shipped a self-contradicting tree: the plan names TWO strings to amend for the consented write, and there are NINE promise sites, one of them user-facing README prose (`README.md:76`) pinned by the plan's own test file (`tests/test_completion.py:1098-1103`) and NOT in the declared `Scope-Paths`. Fixed by declaring `README.md` and enumerating all nine.
- 2026-09-12 to-review (aw set): status set to to-review

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop reporting success for a completion install that cannot work, and tell the user the one thing that would fix it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: detect the precondition, then report and offer

- [ ] E-01 ADD A PURE PREDICATE THAT REPORTS WHETHER THE COMPLETION FRAMEWORK CAN LOAD, returning the individual facts rather than one boolean.
  THE THREE FACTS THAT MATTER, each independently observable: (a) is a bash-completion entry script PRESENT on the box (`/usr/share/bash-completion/bash_completion`, plus the `/usr/local` and Homebrew variants); (b) is it REACHABLE FROM AN INTERACTIVE NON-LOGIN SHELL, which is the case that fails here; (c) does the user's `~/.bashrc` already source it. Returning a boolean collapses "not installed on this system" (the user must install a package) into "installed but not sourced from .bashrc" (a one-line fix), and those need different advice.
  DETECT (b) BY ASKING BASH, NOT BY GUESSING FROM FILES. The discriminator is `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'`: it reports `2` when the framework is loaded and EMPTY when it is not. Parsing rc files to infer this is guesswork; running the shell is the ground truth. Keep it cheap and non-interactive (measured at review: 0.227s real on this box), and treat any failure or timeout as UNKNOWN rather than as a negative.
  THE AUTHORING MEASUREMENT IS STALE AND THE FIX MACHINE IS NOW THE FIXED MACHINE, which is the single most important correction on this item. The plan was authored against a box where `bash -ic` returned EMPTY. Re-measured at review, `bash -ic` returns `2` and so does `bash -lic`, because `~/.bashrc` (mtime 2026-09-12 16:46, AFTER authoring) now carries the very remediation stanza E-03 proposes, already inside the paired fences E-03 specifies. DO NOT "fix" the predicate when the live box reports reachable: that is the correct answer for this box today. Reproduce the FAILING state hermetically instead, which is also how E-04 must drive it: `env -i HOME=<empty-dir> TERM=dumb bash -ic 'echo "[${BASH_COMPLETION_VERSINFO-unset}]"'` reports `[unset]` while the same command with `-lic` reports `[2]`. Both were run at review.
  A CONSEQUENCE FOR E-03 THAT IS EASY TO MISS: on THIS machine the stanza is already present, so the offer must not fire and the no-duplicate detection must recognize a stanza the tool did not write. Treat a hand-added stanza as already-satisfied rather than appending a second one.
  DO NOT READ OR WRITE ANY RC FILE IN THIS ITEM. Fact (c) is a READ of `~/.bashrc` only, and `install_shell_completion`'s "NO user rc/dotfile is ever read or written" contract belongs to that function; put this predicate where it does not violate that promise, and if a read is unavoidable, state in the docstring that reading is not writing and why the distinction is being drawn.
  ZSH AND FISH HAVE THE SAME QUESTION WITH DIFFERENT ANSWERS. Do not force one shape onto all three: report UNKNOWN for a shell whose equivalent check is not implemented, rather than reporting a confident negative that misleads.
  - Depends on: none
  - Expected outcome: a predicate returning the three facts separately, using `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'` for reachability, reporting UNKNOWN on failure, and writing nothing anywhere.
  - Execution state: pending

- [ ] E-02 STOP PRINTING UNCONDITIONAL SUCCESS, AND MAKE THE NEXT-STEP LINE TRUE.
  THE CURRENT MESSAGE IS THE DEFECT'S DELIVERY MECHANISM, AND THERE ARE TWO SITES, BOTH RE-VERIFIED AT REVIEW. The setup-flow site is `cli.py:5610-5613` ("`{shell}` completion installed in `{dir}` (no rc/dotfile modified). Start a new `{shell}` shell to pick it up"), and the VERB site is `cli.py:10501-10510` (a green `OK` line plus a separate `term.line` "Next  start a new `{shell}` shell (or run `exec {shell}`) to pick it up"). Both must change; fixing only one leaves the defect reachable by the other entry point. Measured at review, `aw completion install --shell bash --dry-run` emits FOUR consecutive `OK` lines and no caveat.
  When the framework is not loadable, both sentences are false in the way that matters: the files are installed, and starting a new shell will not help. The maintainer followed that instruction and reasonably concluded the tool was broken.
  SAY WHAT IS TRUE IN EACH CASE. Framework reachable: keep today's message. Framework present but NOT reachable interactively: report the files were written AND that completion will not take effect until bash-completion is sourced for interactive shells, then print the exact remediation. Framework absent: name the package to install rather than implying a shell restart suffices. UNKNOWN: say the install completed and that we could not verify it will take effect, without asserting either way.
  KEEP THE STATUS LABEL HONEST. An install that cannot take effect is not `ok`; it is `warn` at most, because the user's next action depends on knowing. Do not bury the condition in a trailing clause of a green line, which is how the current message hid it.
  - Depends on: E-01
  - Expected outcome: four distinct outcomes reported, the non-reachable case NOT labeled `ok`, and no message instructing a shell restart that would not help.
  - Execution state: pending

- [ ] E-03 OFFER THE ONE-LINE REMEDIATION, AND DO NOT APPLY IT WITHOUT CONSENT.
  THE REMEDIATION IS SMALL AND WORTH PRINTING VERBATIM so a user can paste it:
      if ! shopt -oq posix && [[ -z ${BASH_COMPLETION_VERSINFO-} ]]; then
        [[ -r /usr/share/bash-completion/bash_completion ]] && . /usr/share/bash-completion/bash_completion
      fi
  THE `BASH_COMPLETION_VERSINFO` GUARD IS LOAD-BEARING, not decoration: without it the snippet re-sources the framework in a login shell that already loaded it. Include the guard whenever the snippet is printed or written.
  OFFER THE WRITE, OPT-IN ON A TTY. DECIDED BY THE MAINTAINER 2026-09-12 (OQ-01); this is no longer the executor's call. The prompt DEFAULTS TO NO, `--yes` must NOT consent to it, and a non-TTY run must write nothing. Print-only is NO LONGER an acceptable outcome for this item: the maintainer weighed it against pasting four lines on every new machine and chose the offer.
  THE PROMPT DEFAULT IS `[y/N]`, WHICH IS DELIBERATELY THE OPPOSITE OF THE FIRST-RUN PROMPTS FLIPPED EARLIER THE SAME DAY. Those flipped prompts (`Install shell completion?`, `Set up a runner profile now?`) write inside the framework's OWN directories; this one writes to a file the framework does not own and has three times promised not to touch. Use `term.yes_no_suffix(False)` so the rendered default is visibly `N`, and do NOT "harmonize" it to yes later without a fresh ruling.
  `--yes` MUST NOT CONSENT, and the precedent is already in the tree: `_configure_completion` and `_configure_runner_profiles` both return early under `--yes` on the stated reasoning that preauthorizing install mutations is not the same as authorizing a user-scoped choice. An rc write is further from an install mutation than either of those, so treating `--yes` as consent here would be the largest silent-write regression in the feature.
  APPENDING IS NOT IDEMPOTENT BY NATURE, so detect your own prior stanza before writing and refuse to duplicate it. A second consenting run must be a no-op that says so.
  USE PAIRED FENCE MARKERS, NOT A SINGLE SENTINEL LINE (F-7, and this supersedes the earlier `installed-by:` guidance for the RC STANZA only; the drop-in FILES keep their single-line sentinel, which is correct for a whole-file check). Emit an opening and a CLOSING marker around the stanza, e.g. `# >>> agent-workflows (aw completion install) >>>` and `# <<< ... <<<`.
  THE REASON IS REMOVABILITY, AND IT IS NOT COSMETIC. A single sentinel records where the block STARTS and nothing about where it ENDS, so `uninstall_shell_completion` cannot delete the stanza without hardcoding its line count or re-deriving its exact text; both break the moment a later release reweords it. Fences let uninstall delete a RANGE with no knowledge of the contents, let an upgrade REPLACE that range in place so a stanza fix actually reaches existing users, and make the no-duplicate test provable rather than approximate. Measured precedent on the maintainer's own machine 2026-09-12: `grok`'s installer uses exactly this shape (`# >>> grok installer >>>` / `# <<< grok installer <<<`) in the same `~/.bashrc`, so the convention is already proven in the wild and is one comment line dearer.
  THIS CREATES AN OBLIGATION ON UNINSTALL that today's code does not have: `uninstall_shell_completion`'s docstring states "No rc/dotfile is read or written", which becomes an ASYMMETRY the moment install writes one (install adds a stanza, uninstall abandons it forever). Either extend uninstall to remove the fenced range under the same consent rules, or state in its docstring that the rc stanza is deliberately left and tell the user how to remove it. Do NOT ship an install that writes with an uninstall that silently does not clean up.
  WRITE ATOMICALLY AND NEVER TRUNCATE. This is the user's login shell configuration: a partial write costs them a working shell. Append via a read-modify-write to a temp file plus `os.replace`, the same shape `install_wizard._persist_policy` uses, and preserve the file's existing trailing-newline state rather than normalizing it.
  IF `~/.bashrc` DOES NOT EXIST, CREATING IT IS A BIGGER ACT THAN APPENDING and interacts with shell startup order (a new `~/.bashrc` can change which rc files bash reads). Report rather than create, and say why.
  THIS IS THE FIRST RC WRITE IN THE CODEBASE, SO THERE IS NO IN-TREE PRECEDENT TO COPY. Verified at review: `grep -rn "bashrc" agent_workflows/*.py` yields only PROMISES NOT to write one. `install_wizard`'s `os.replace` calls (`:886`, `:897`, `:909`) are the atomic-write SHAPE to mirror, but every one of them writes a file the framework OWNS under `.aw/`, never a user dotfile, so the shape transfers and the authority does not. Do not cite them as precedent for touching `~/.bashrc`; the authority for that is the maintainer's OQ-01 ruling alone.
  DETECT A STANZA THIS TOOL DID NOT WRITE, because one already exists on the maintainer's box (verified at review, hand-added with these exact fences). Key the no-duplicate check on the OPENING FENCE TEXT, not on an `installed-by:` sentinel and not on authorship, so a hand-added stanza is recognized as already-satisfied and reported as a no-op instead of being duplicated. That is the opposite of the drop-in FILE rule, where a foreign file is refused; here a foreign-but-equivalent stanza means the user already did the work.
  - Depends on: E-02
  - Expected outcome: the guarded snippet printed verbatim in the non-reachable case, PLUS an opt-in `[y/N]` offer on a TTY that appends it atomically inside PAIRED FENCE MARKERS, refuses under `--yes` and on a non-TTY, is a reported no-op on a second run detected by its opening fence, reports rather than creates an absent `~/.bashrc`, and leaves uninstall either removing the fenced range or documenting that it does not.
  - Execution state: pending

- [ ] E-04 TEST THE FOUR STATES WITHOUT DEPENDING ON THE DEVELOPER'S OWN SHELL, which is the trap this test bed sets.
  THE STATES: reachable, present-but-not-reachable, absent, and unknown. Drive them by INJECTION (a fake entry-script path, a stubbed probe result) rather than by mutating the real environment, because a test that reads the developer's actual `BASH_COMPLETION_VERSINFO` passes or fails according to whose machine it runs on.
  THE ENVIRONMENT-SENSITIVITY TRAP IS NOW PROVEN, NOT HYPOTHETICAL, AND THE AUTHORED WORDING OF IT IS WRONG. This plan originally said this box reports REACHABLE under `bash -l` and NOT-REACHABLE under plain `bash -i`. Re-measured at review, this box now reports REACHABLE under BOTH, because `~/.bashrc` gained the remediation stanza after authoring. That is exactly why injection is mandatory: the same test would have passed at authoring and failed today, or vice versa, with no code change. If any test does shell out, it MUST pin `HOME` to a fixture directory via `env -i` rather than inheriting the developer's, and the hermetic pair measured at review is `env -i HOME=<empty> bash -ic` -> unset versus the same with `-lic` -> 2.
  ASSERT THE MESSAGE, NOT ONLY THE PREDICATE. The defect was a false SUCCESS STRING, so the regression test must pin that the non-reachable case does not print an `ok` status and does not tell the user to start a new shell.
  ASSERT NO RC FILE IS TOUCHED in every non-consenting path, by byte-comparing a fixture `~/.bashrc` before and after. That is the contract most at risk from this change.
  - Depends on: E-03
  - Expected outcome: four injected states covered, the false-success string pinned as a regression, and a byte-identical rc fixture proving no unconsented write.
  - Execution state: pending

## Project conventions discovered (Step 0)

CORRECTED AT REVIEW: eight of the nine bullets here were COPIED FROM AN UNRELATED SET (`wfartifacts`, the run-scratch relocation) and described gitignore templates, `_ensure_aw_gitignore`, `install_into_repo` and D92 run-record tracking, none of which this plan touches. They are removed rather than left, because a Step-0 section is where an executor looks to learn the local rules and eight wrong rules is worse than none. The one that genuinely applied (shared checkout, bare suite, re-locate by name) is kept and the rest are replaced with conventions measured against THIS feature at review.

- THE NO-RC-WRITE PROMISE IS STATED NINE TIMES ACROSS THREE FILES INCLUDING THE README, enumerated in the spec-sync table below. It is the most-repeated promise in this feature, which is why the consented write is a documentation change as much as a code change.
- A DROP-IN FILE IS SENTINEL-GATED AND A FOREIGN FILE IS REFUSED: `INSTALL_SENTINEL = "# installed-by: agent-workflows (aw completion install)"` (`completion.py:756`), checked at `:843` and enforced at `:886`. The RC STANZA takes the opposite stance by design (F-7 fences, and a foreign-but-equivalent stanza means the user already did the work), so do not unify the two policies.
- `--yes` DOES NOT CONSENT TO A USER-SCOPED CHOICE, and the precedent is explicit in code: `_configure_completion` returns early under `--yes`/non-TTY (`cli.py:5570-5571`) and `_configure_runner_profiles` does the same with the stated reason "`--yes` preauthorizes install mutations, NOT a model/default choice" (`cli.py:5648-5651`).
- THE FIRST-RUN COMPLETION PROMPT DEFAULTS TO YES (`cli.py:5583-5590`, "DEFAULT YES (maintainer request 2026-09-12)") BECAUSE IT WRITES INSIDE THE FRAMEWORK'S OWN DIRECTORY. The rc prompt must default to NO for precisely the reason that one defaults to yes; the polarity difference is deliberate and is recorded in E-03.
- THE ATOMIC-WRITE SHAPE IS `install_wizard`'s temp-file-plus-`os.replace` (`:886`, `:897`, `:909`), but every one of those writes a framework-owned file under `.aw/`. There is NO in-tree precedent for writing a user dotfile (F-9).
- Shared checkout, concurrent edits; the suite runs BARE (`python3 -m pytest`). Re-locate every symbol by NAME, not by the line numbers cited in these plans, which were accurate at review and drift constantly.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the verb never checks its own precondition | `grep -n 'profile.d\|BASH_COMPLETION_VERSINFO\|bash_completion' agent_workflows/completion.py` returns NOTHING; the drop-in dir only works if bash-completion auto-discovers it. | the grep, at authoring |
| F-2 | HIGH | the success message is unconditional and its next step is useless in the failing case | `cli.py:5610-5614` prints "installed... Start a new shell to pick it up"; restarting the shell does not help when the framework is not sourced. | the code; the maintainer's reproduction |
| F-3 | HIGH | the discriminator is measurable and cheap | `bash -lic` -> `BASH_COMPLETION_VERSINFO=2` with a `-D` loader; `bash -ic` -> unset, no default completion. STALE AS OF REVIEW: see F-8, both now return `2` on this box. The discriminator itself is confirmed working and costs 0.227s. | both commands run at authoring; re-run at review |
| F-4 | MEDIUM | the machine's own setup WAS the cause, and the class is common | `/usr/share/bash-completion/bash_completion` exists (verified at review) but is sourced only by `/etc/profile.d/bash_completion.sh` (login shells). SUPERSEDED IN PART: at review `~/.bashrc:20-33` DOES now reference it, so this particular box is fixed; there is still no `~/.bash_profile` (verified). The defect class is unchanged for every un-fixed machine. | file checks + greps, re-run at review |
| F-5 | HIGH | the restraint that constrains the fix is stated NINE times, not three, and one is user-facing README prose | Enumerated at review by `grep -rn "never edits\|no rc/dotfile\|NO user rc/dotfile\|never touch\|does NOT modify your"`: `completion.py:31`, `:728`, `:865`, `:934`; `cli.py:5561`, `:5581`, `:5612`, `:10482`, `:10506`; and `README.md:76` ("**never edits `~/.bashrc`...**"). The README claim is PINNED BY THIS PLAN'S OWN TEST FILE (`tests/test_completion.py:1098-1103`), and `README.md` was NOT in the declared `Scope-Paths`. Severity raised from MEDIUM: shipping the consented write while six or seven of these still deny it leaves the tree self-contradicting, and the README is the one a user reads. | the grep; the README section; the test |
| F-8 | HIGH | THE PLAN'S CENTRAL MEASUREMENT IS STALE BECAUSE THE REPORTING MACHINE WAS FIXED BY HAND AFTER AUTHORING | Measured at review: `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'` returns `2`, not empty, and `~/.bashrc` (mtime 2026-09-12 16:46) now carries the remediation stanza this plan proposes, wrapped in the exact paired fences E-03 prescribes (`~/.bashrc:20-33`). An executor following V-01 literally would find its stated evidence unreproducible and might "correct" a working predicate. The failing state reproduces hermetically: `env -i HOME=<empty> bash -ic` -> `[unset]` vs `-lic` -> `[2]`. Consequence for E-03: the offer must treat an existing hand-added stanza as satisfied, not append a duplicate. | both probes; `stat` on `~/.bashrc`; the stanza itself |
| F-9 | MEDIUM | THERE IS NO IN-TREE PRECEDENT FOR WRITING A USER DOTFILE, so E-03 is the first | `grep -rn "bashrc" agent_workflows/*.py` returns ONLY promises not to write one. `install_wizard`'s `os.replace` (`:886`, `:897`, `:909`) is the right atomic SHAPE but every call writes a framework-owned file under `.aw/`, never a user dotfile. The shape transfers; the authority does not, and the only authority is the OQ-01 ruling. | the grep; the three call sites |
| F-7 | MEDIUM | A SINGLE-LINE SENTINEL CANNOT BE UNINSTALLED; PAIRED FENCES CAN | An `installed-by:` line marks where a stanza BEGINS and says nothing about where it ENDS, so uninstall must hardcode a line count or re-derive the exact text, and both break when a later release rewords it. Fences also let an UPGRADE replace the range so a stanza fix reaches existing users, where a "sentinel present -> skip" check would no-op forever. Precedent measured in the maintainer's own `~/.bashrc` 2026-09-12: `grok`'s installer uses `# >>> grok installer >>>` / `# <<< grok installer <<<`. Cost: one comment line. This also exposes an asymmetry to resolve: `uninstall_shell_completion` says "No rc/dotfile is read or written". | the two blocks side by side in `~/.bashrc`; `completion.py:931-935` |
| F-6 | LOW | THE INSTALLED ARTIFACTS ARE CORRECT AND ARE NOT THE DEFECT, recorded so nobody "fixes" them | The three files exist, sourcing registers `complete -F _aw_completion aw`, and with the framework loaded the lazy loader resolves ALL THREE entrypoint names. An earlier suspicion that the single multi-name `complete -F _aw_completion aw agentwf agent-workflows` was fragile was TESTED AND REFUTED: the per-alias symlinks (`_alias_filenames`, deliberate and documented) are what make it work. | per-name loader probe with the framework sourced |

## Proposed changes (ordered, validatable)

1. A pure predicate returning the three precondition facts separately, using `bash -ic` as the discriminator (E-01).
2. Four honest message variants, with the non-reachable case not labeled `ok` (E-02).
3. The guarded remediation snippet printed; the rc write opt-in on a TTY, wrapped in paired fence markers so it can be uninstalled and upgraded (E-03).
4. Injection-driven tests for all four states, pinning the false-success string (E-04).

## Deferred / out of scope (with reason)

CORRECTED AT REVIEW: all four entries here were COPIED FROM THE UNRELATED `wfartifacts` SET (run-scratch relocation, `tools/untrack-workflow-artifacts.py`, backlog `2812t3`, and a Set-wide prohibition on deleting run records). None of them bears on shell completion, and the last one ("Order 05 relocates and never deletes") cites an Order that does not exist in this Set, which has exactly one child. Replaced with this plan's real exclusions.

- ZSH AND FISH REMEDIATION. E-01 must report UNKNOWN for a shell whose reachability check is not implemented rather than a confident negative, but this plan does not build the zsh `compinit` or fish equivalents. Their preconditions differ in kind (zsh needs `compinit` to have run, fish auto-loads), so a shared shape would be wrong; scope covers "the equivalent detection if it is cheap and correct" and nothing more.
- CHANGING THE GENERATED SCRIPT, THE DROP-IN LAYOUT, OR THE ALIAS SYMLINKS. All three verified CORRECT and NOT the defect (F-6, re-confirmed at review). Recorded as deferred so nobody "fixes" them.
- DYNAMIC id6/setid COMPLETION. Already deferred by the verb's own help to a later `tabcomp` child.
- FIXING THE REPORTING MACHINE. Already fixed by hand before review (F-8); this plan changes the TOOL so the next machine is told the truth.
- `engine.py`'s GITIGNORE RESTRAINT. Quoted as evidence of the project's pattern, not a site to amend: its claim concerns gitignores and remains true.

## Scope check

- Over-scope: none. `README.md` was ADDED to `Scope-Paths` at review and is in scope for exactly one reason: it carries promise site 9 (`README.md:76`), which the consented write would falsify, and amending it without declaring it would have been an undeclared out-of-scope edit caught only at finalize.
- Under-scope, stated rather than left as `none`: this plan does not modify the generated completion script, the drop-in layout, or the alias symlinks, all three verified CORRECT (F-6). It does not add dynamic id6/setid completion, which the verb's help already defers to a later `tabcomp` child. It does not edit any user rc file without explicit consent. It does NOT fix the reporting machine, which was already fixed by hand before review (F-8), and it does not attempt to detect or migrate a hand-added stanza beyond recognizing it as satisfied.
- A NOTE ON `engine.py`, cited in the Concern and F-5 for its "Does NOT silently edit user gitignores" restraint: that file is NOT in `Scope-Paths` and needs no edit, because its claim is about GITIGNORES, not rc files, and stays true. It is quoted as evidence of the project's pattern of restraint, not as a site to amend.

## Required tests / validation

- THE FOUR STATES, each driven by injection rather than by the ambient environment: reachable, present-but-not-reachable, absent, unknown.
- THE REGRESSION THAT MATTERS: in the non-reachable state the output has NO `ok` status and NO "start a new shell" instruction. That false pairing is the whole defect.
- NO UNCONSENTED RC WRITE: a fixture `~/.bashrc` byte-identical after a non-TTY run and after a `--yes` run.
- IDEMPOTENCE if a write path exists: a second consenting run adds no duplicate stanza.
- THE SNIPPET carries the `BASH_COMPLETION_VERSINFO` guard wherever it is printed or written.
- `python3 -m pytest` BARE, failure-SET delta empty.
- `aw sanitize --agent` clean.

## Spec / documentation sync

No spec governs shell completion; the verb's `--help` text and these messages ARE the contract, which is why E-02 treats the message as a deliverable rather than as cosmetics.

AMEND EVERY PROMISE SITE, AND THERE ARE NINE, NOT TWO (F-5, raised at review; the authored text named only two and that undercount is what would have shipped a self-contradicting tree). Enumerated by grep at review, each must be either amended or deliberately left with a stated reason:

| # | Site | Current claim |
|---|---|---|
| 1 | `completion.py:31` | "never touch `~/.bashrc`/`~/.zshrc`/..." (module docstring) |
| 2 | `completion.py:728` | "The core promise: we NEVER edit `~/.bashrc`..." |
| 3 | `completion.py:865` | "NO user rc/dotfile is ever read or written" (`install_shell_completion`) |
| 4 | `completion.py:934` | "No rc/dotfile is read or written" (`uninstall_shell_completion`) |
| 5 | `cli.py:5561` | "Never edits an rc/dotfile" (`_configure_completion`) |
| 6 | `cli.py:5581` | "does NOT modify your ~/.bashrc, ~/.zshrc, or config.fish" (PROMPT TEXT the user reads) |
| 7 | `cli.py:5612` | "(no rc/dotfile modified)" (setup-flow success line) |
| 8 | `cli.py:10482` | "Never edits a user rc/dotfile" (verb docstring) |
| 9 | `README.md:76` | "**never edits `~/.bashrc`, `~/.zshrc`, or `config.fish`**" (USER-FACING) |

SITE 9 IS THE ONE MOST LIKELY TO BE MISSED AND IT IS TEST-ENFORCED. `README.md` is now DECLARED in `Scope-Paths` (added at review; it was absent, so amending it would have been an undeclared out-of-scope edit). Note `tests/test_completion.py:1098-1103` asserts README content for this feature, so the README and the tests move together.
SITE 6 IS PROMPT TEXT, NOT A DOCSTRING: a user reads it at the moment of consent, so leaving it stale is worse than a stale comment. If the write offer lives in the same flow, this sentence must state the new truth precisely.
SITE 4 IS THE UNINSTALL ASYMMETRY E-03 already names: whichever way that is resolved, this string must match the resolution.
THE PRECISE FORM IS PRESERVED-SUBSTANCE, NOT DELETION: the promise that still holds is NO SILENT WRITE. Prefer wording like "never writes a user rc/dotfile except the fenced stanza appended on explicit TTY consent, never under `--yes` and never non-interactively" over striking the promise, because the restraint is the reason the maintainer's ruling was safe to give.

ALSO UPDATE THAT DOCSTRING if E-01's rc READ lands anywhere it can be read as covering: the current sentence is "NO user rc/dotfile is ever read or written", and a read would make that literally false even though the spirit (never WRITE) is preserved. Either keep the read out of that function or amend the sentence to distinguish reading from writing. Leaving a docstring that contradicts the code is the failure mode this project has already hit twice today.

## Open questions

### OQ-01: Should the fix offer to write the stanza into `~/.bashrc`, or only print it?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: ANSWERED BY THE MAINTAINER 2026-09-12: OFFER THE WRITE, OPT-IN ON A TTY. Put to them with the tension stated (three docstrings promise the tool never touches user rc files, against the friction of pasting four lines on every new machine while completion stays dead in an interactive shell), and they chose the offer over print-only and over an offer defaulting to yes.
  SO THE PROMPT DEFAULTS TO NO, which is the part that keeps the promise meaningful: nothing is written unless a human on a TTY says yes, `--yes` does not consent, and a non-TTY writes nothing. That preserves the SUBSTANCE of the no-dotfile contract (no silent write) while removing the manual step, and it is why the third option, defaulting the prompt to yes, was rejected even though the same session flipped other prompts to yes: those write inside the framework's own directories, this one does not.
  THE DOCSTRING MUST BE AMENDED, NOT LEFT TO CONTRADICT THE CODE. `install_shell_completion` says "NO user rc/dotfile is ever read or written"; once this lands, that sentence needs to distinguish that FUNCTION (which still writes no rc file) from the new consented path, or the write must live outside it. The spec-sync section carries this.
  NOT BLOCKING now that it is answered; E-03 states the decided shape and V-03 demands the evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate and its three returned facts for this machine. DO NOT expect `bash -ic` to be empty: measured at review it returns `2`, because `~/.bashrc` was fixed by hand after this plan was authored (F-8), so the honest evidence is the HERMETIC pair, `env -i HOME=<empty-dir> TERM=dumb bash -ic 'echo "[${BASH_COMPLETION_VERSINFO-unset}]"'` -> `[unset]` beside the same command with `-lic` -> `[2]`, plus the live box's own `bash -ic` -> `2` stated as the reachable case. Confirm by grep that the predicate writes nothing and that any rc access is a READ. A predicate returning a single boolean is a FAILED validation, since it cannot distinguish "install a package" from "add one line". Reporting `-ic` -> empty on this box would be FABRICATED evidence; report what the command actually prints.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the ACTUAL output of `aw completion install` in the NON-REACHABLE state and show it does NOT print an `ok` status and does NOT instruct a shell restart. Paste the reachable-state output showing today's message is preserved. Paste the absent-state and unknown-state outputs. Quote the four message variants from the diff. COVER BOTH MESSAGE SITES SEPARATELY, since a fix to one leaves the defect reachable by the other: the setup flow (`cli.py:5610-5613`) and the verb (`cli.py:10501-10510`, whose `Next  start a new ... shell` line is a separate `term.line` call). For reference, the pre-change verb output measured at review was four consecutive `OK` lines with no caveat.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the printed snippet verbatim and confirm the `BASH_COMPLETION_VERSINFO` guard is present. THE WRITE PATH IS NOW REQUIRED (OQ-01 answered), so paste ALL of: the rendered prompt showing a visible `[y/N]` default; a DECLINED run leaving a fixture `~/.bashrc` byte-identical; a non-TTY run and a `--yes` run each leaving it byte-identical; a CONSENTED run showing the appended stanza wrapped in BOTH fence markers with the file's prior content intact; a SECOND consenting run reported as a no-op with no duplicate stanza; the absent-`~/.bashrc` case REPORTING rather than creating; and the uninstall side, either removing exactly the fenced range (paste the rc file before and after, byte-identical to its pre-install state) or its docstring stating that the stanza is deliberately left with removal instructions. A stanza written with only an OPENING marker is a FAILED validation (F-7), because uninstall then cannot delete it without hardcoding its text. A missing write path is a FAILED validation, and a `--yes` run that writes is a FAILED validation regardless of anything else passing.
    ALSO REQUIRED, because this box is already in the post-fix state (F-8): show that a PRE-EXISTING stanza this tool did not write is detected as satisfied and reported as a no-op, NOT duplicated. The maintainer's live `~/.bashrc:20-33` is exactly that case and must be exercised against a COPY, never against the real file. Do NOT write to the real `~/.bashrc` during validation; every write assertion belongs in a fixture HOME.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the passing tests for all four states and show each is driven by INJECTION, quoting the stub. Paste the assertion pinning that the non-reachable case prints no `ok` and no restart instruction. Paste the byte-comparison of the rc fixture. Confirm by grep that no test reads the ambient `BASH_COMPLETION_VERSINFO` or the developer's real `HOME`; any test that shells out must pin `HOME` via `env -i` (F-8: this box flipped from not-reachable to reachable between authoring and review with no code change, so an ambient-environment test would have silently reversed its verdict). THEN paste the BARE `python3 -m pytest` summary and the failure-SET delta (criterion: empty). FOR REFERENCE, review measured the pre-change baseline bare at HEAD `8e81ab9c`: `5971 passed, 3 skipped, 2 xfailed`; re-measure your own rather than quoting that.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

NEVER WRITE TO THE REAL `~/.bashrc` WHILE BUILDING OR VALIDATING THIS. Every write assertion belongs in a fixture HOME; the maintainer's live file already carries a hand-added stanza (`~/.bashrc:20-33`, verified at review) and is a co-worker's artifact in the sense that matters. Read it if you must, copy it to a fixture to exercise the already-present case, and modify only the copy. (This replaces a "do not delete run records" clause copied from the unrelated `wfartifacts` Set, which cited an Order 05 this single-child Set does not have.)

THE ONE PROMISE THAT MUST SURVIVE THIS PLAN IS "NO SILENT WRITE", NOT "NO WRITE". The maintainer authorized the offer on that basis. So if any ambiguity arises at execution time, resolve it toward: nothing written without a human typing yes on a TTY, `--yes` never consenting, non-TTY never writing, and every one of the nine promise strings telling the truth afterwards.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
