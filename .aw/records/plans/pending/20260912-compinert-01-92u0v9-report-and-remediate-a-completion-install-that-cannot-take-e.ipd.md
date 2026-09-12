# IPD: Report and remediate a completion install that cannot take effect

- Date: 2026-09-12
- Kind: child
- Concern: `aw completion install` REPORTS SUCCESS INTO A SHELL WHERE COMPLETION CANNOT WORK, and gives the user no way to tell. Reported by the maintainer 2026-09-12: they ran the verb, saw three `OK` lines plus "Next start a new bash shell (or run `exec bash`) to pick it up", did exactly that, and `aw <TAB>` still completed nothing.
  THE INSTALL WAS CORRECT AND THE DIAGNOSIS IS ENTIRELY OUTSIDE IT. Verified: the three files exist at `~/.local/share/bash-completion/completions/` (`aw` plus `agentwf` and `agent-workflows` symlinks), and sourcing the file by hand registers `complete -F _aw_completion aw`. The lazy loader resolves ALL THREE names correctly once bash-completion is present. Nothing about the generated script or the drop-in layout is wrong.
  THE ACTUAL CAUSE IS THAT BASH-COMPLETION ITSELF IS NEVER LOADED IN AN INTERACTIVE NON-LOGIN SHELL ON THAT MACHINE. `/usr/share/bash-completion/bash_completion` exists, but the only thing sourcing it is `/etc/profile.d/bash_completion.sh`, which runs for LOGIN shells. Measured: `bash -lic` reports `BASH_COMPLETION_VERSINFO=2` and a `-D` loader installed, while `bash -ic` reports `VERSINFO=unset` and no default completion at all. The user's `~/.bashrc` contains no `bash_completion` reference and there is no `~/.bash_profile` sourcing `.bashrc`. So in a new terminal tab, tmux pane, or plain `bash`, NOTHING is completed, `git` and `ssh` included; `aw` is not special.
  WHY THIS IS OUR DEFECT ANYWAY, WHICH IS THE POINT THE MAINTAINER MADE. The verb owns a promise it does not verify. It writes into a directory whose whole purpose is AUTO-DISCOVERY BY BASH-COMPLETION, so bash-completion being loadable is a PRECONDITION of the feature working, and the verb checks nothing: `grep -n 'profile.d|BASH_COMPLETION_VERSINFO|bash_completion' agent_workflows/completion.py` returns NOTHING. It then prints an unconditional success line and an instruction ("start a new bash shell") that is precisely the action that does NOT help. A user who trusts the output concludes the tool is broken, which is the outcome measured here.
  THE HONEST CONSTRAINT THAT MAKES THIS NON-TRIVIAL, and the reason this plan exists rather than a one-line fix: `install_shell_completion`'s docstring states "NO user rc/dotfile is ever read or written", the success message advertises "(no rc/dotfile modified)", and `engine.py`'s module docstring says the installer "Does NOT silently edit user gitignores". That restraint is deliberate and is worth keeping; a `.bashrc` edit is exactly the kind of surprise the project has repeatedly refused. So the fix is DETECTION plus an OFFER, not a silent write.
- Scope: Detect whether the installed completion can actually take effect, and when it cannot, say so precisely and offer the one-line remediation instead of reporting plain success. Covers the `aw completion install` verb, the `_configure_completion` step in the setup flow, and the success/next-step messages both print. EXCLUDES writing to any user rc/dotfile without explicit consent, changing the generated script (verified correct), changing the drop-in layout or the alias symlinks (verified correct), and any change for zsh/fish beyond the equivalent detection if it is cheap and correct.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion.py
- Item-Dependencies: none
- Status: to-review
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
- 2026-09-12 to-review (aw set): status set to to-review

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop reporting success for a completion install that cannot work, and tell the user the one thing that would fix it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: detect the precondition, then report and offer

- [ ] E-01 ADD A PURE PREDICATE THAT REPORTS WHETHER THE COMPLETION FRAMEWORK CAN LOAD, returning the individual facts rather than one boolean.
  THE THREE FACTS THAT MATTER, each independently observable: (a) is a bash-completion entry script PRESENT on the box (`/usr/share/bash-completion/bash_completion`, plus the `/usr/local` and Homebrew variants); (b) is it REACHABLE FROM AN INTERACTIVE NON-LOGIN SHELL, which is the case that fails here; (c) does the user's `~/.bashrc` already source it. Returning a boolean collapses "not installed on this system" (the user must install a package) into "installed but not sourced from .bashrc" (a one-line fix), and those need different advice.
  DETECT (b) BY ASKING BASH, NOT BY GUESSING FROM FILES. The measured discriminator is `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'`: it reports `2` when the framework is loaded and EMPTY when it is not, and on the reported machine `bash -lic` gives `2` while `bash -ic` gives empty. Parsing rc files to infer this is guesswork; running the shell is the ground truth. Keep it cheap and non-interactive, and treat any failure or timeout as UNKNOWN rather than as a negative.
  DO NOT READ OR WRITE ANY RC FILE IN THIS ITEM. Fact (c) is a READ of `~/.bashrc` only, and `install_shell_completion`'s "NO user rc/dotfile is ever read or written" contract belongs to that function; put this predicate where it does not violate that promise, and if a read is unavoidable, state in the docstring that reading is not writing and why the distinction is being drawn.
  ZSH AND FISH HAVE THE SAME QUESTION WITH DIFFERENT ANSWERS. Do not force one shape onto all three: report UNKNOWN for a shell whose equivalent check is not implemented, rather than reporting a confident negative that misleads.
  - Depends on: none
  - Expected outcome: a predicate returning the three facts separately, using `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'` for reachability, reporting UNKNOWN on failure, and writing nothing anywhere.
  - Execution state: pending

- [ ] E-02 STOP PRINTING UNCONDITIONAL SUCCESS, AND MAKE THE NEXT-STEP LINE TRUE.
  THE CURRENT MESSAGE IS THE DEFECT'S DELIVERY MECHANISM. `cli.py:5610-5614` prints "`{shell}` completion installed in `{dir}` (no rc/dotfile modified). Start a new `{shell}` shell to pick it up", and the verb's own path prints "Next start a new bash shell (or run `exec bash`) to pick it up". When the framework is not loadable, BOTH sentences are false in the way that matters: the files are installed, and starting a new shell will not help. The maintainer followed that instruction and reasonably concluded the tool was broken.
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
  - Depends on: E-02
  - Expected outcome: the guarded snippet printed verbatim in the non-reachable case, PLUS an opt-in `[y/N]` offer on a TTY that appends it atomically inside PAIRED FENCE MARKERS, refuses under `--yes` and on a non-TTY, is a reported no-op on a second run detected by its opening fence, reports rather than creates an absent `~/.bashrc`, and leaves uninstall either removing the fenced range or documenting that it does not.
  - Execution state: pending

- [ ] E-04 TEST THE FOUR STATES WITHOUT DEPENDING ON THE DEVELOPER'S OWN SHELL, which is the trap this test bed sets.
  THE STATES: reachable, present-but-not-reachable, absent, and unknown. Drive them by INJECTION (a fake entry-script path, a stubbed probe result) rather than by mutating the real environment, because a test that reads the developer's actual `BASH_COMPLETION_VERSINFO` passes or fails according to whose machine it runs on. Note this box would report REACHABLE under `bash -l` and NOT-REACHABLE under a plain `bash -i`, so an environment-sensitive test is actively misleading here.
  ASSERT THE MESSAGE, NOT ONLY THE PREDICATE. The defect was a false SUCCESS STRING, so the regression test must pin that the non-reachable case does not print an `ok` status and does not tell the user to start a new shell.
  ASSERT NO RC FILE IS TOUCHED in every non-consenting path, by byte-comparing a fixture `~/.bashrc` before and after. That is the contract most at risk from this change.
  - Depends on: E-03
  - Expected outcome: four injected states covered, the false-success string pinned as a regression, and a byte-identical rc fixture proving no unconsented write.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ORDER 07 IS THE AUTHORITY AND IT IS ALREADY `implemented`: spec `20260817-2124-01-records-taxonomy-cleanup` (`u7xtni`), history line "run-artifacts -> `.aw/workflow-artifacts/`". This Set DELIVERS that decision; it does not revisit it.
- RUN SCRATCH IS UNTRACKED BECAUSE OF D92: run records carry local context, absolute home paths and session detail, so committing them publishes machine identity into permanent history. That is the reason, and it is why "just track it" is not an option.
- THIS REPO'S ROOT `.gitignore:62-68` ALREADY ENCODES THE TARGET STATE and is the best statement of intent in the tree, but it is NOT shipped: a target repo receives the framework-owned `.aw/.gitignore` instead. Never cite the root file as evidence that a target repo is protected.
- PATTERNS IN `.aw/.gitignore` ARE `.aw/`-RELATIVE AND MUST BE ANCHORED. The template's own `/inbox/` comment records the measured reason: a bare `inbox/` matched at any depth and silently swallowed the TRACKED `records/comms/shared/inbox/` lane, breaking `aw install`.
- `_ensure_aw_gitignore` IS THE ONLY PATH THAT REACHES AN ALREADY-INSTALLED REPO, because a repo that already has a `.aw/.gitignore` never re-reads the template. Every prior addition in that function carries a comment saying exactly this.
- `install_into_repo` IS THE SHARED CHOKEPOINT for every entry point (`aw install` via `engine.run()`, `aw setup` via `cli._run_setup` -> `cli._install_one`, and library callers). Wiring into `run()` reaches only one of them.
- `.aw/records/` IS TRACKED DURABLE RECORDS, NOT SCRATCH: `records/reviews/` alone holds 170 typed `.review.md` files. An agent already mistook it for the scratch home and moved run records into `.aw/records/reviews/untracked/`.
- Shared checkout, concurrent edits; the suite runs BARE (`python3 -m pytest`). Re-locate every symbol by NAME, not by the line numbers cited in these plans.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the verb never checks its own precondition | `grep -n 'profile.d\|BASH_COMPLETION_VERSINFO\|bash_completion' agent_workflows/completion.py` returns NOTHING; the drop-in dir only works if bash-completion auto-discovers it. | the grep, at authoring |
| F-2 | HIGH | the success message is unconditional and its next step is useless in the failing case | `cli.py:5610-5614` prints "installed... Start a new shell to pick it up"; restarting the shell does not help when the framework is not sourced. | the code; the maintainer's reproduction |
| F-3 | HIGH | the discriminator is measurable and cheap | `bash -lic` -> `BASH_COMPLETION_VERSINFO=2` with a `-D` loader; `bash -ic` -> unset, no default completion. | both commands run at authoring |
| F-4 | MEDIUM | the machine's own setup is the cause, and it is common | `/usr/share/bash-completion/bash_completion` exists but is sourced only by `/etc/profile.d/bash_completion.sh` (login shells); the user's `~/.bashrc` has no reference and there is no `~/.bash_profile`. | file checks + greps |
| F-5 | MEDIUM | the restraint that constrains the fix is deliberate and stated three times | `install_shell_completion`'s "NO user rc/dotfile is ever read or written"; the success line's "(no rc/dotfile modified)"; `engine.py`'s "Does NOT silently edit user gitignores". RESOLVED 2026-09-12: the maintainer authorized an OPT-IN TTY write, so the SUBSTANCE (no SILENT write) is preserved and two of those three strings must be amended rather than quietly falsified. | all three docstrings; maintainer ruling |
| F-7 | MEDIUM | A SINGLE-LINE SENTINEL CANNOT BE UNINSTALLED; PAIRED FENCES CAN | An `installed-by:` line marks where a stanza BEGINS and says nothing about where it ENDS, so uninstall must hardcode a line count or re-derive the exact text, and both break when a later release rewords it. Fences also let an UPGRADE replace the range so a stanza fix reaches existing users, where a "sentinel present -> skip" check would no-op forever. Precedent measured in the maintainer's own `~/.bashrc` 2026-09-12: `grok`'s installer uses `# >>> grok installer >>>` / `# <<< grok installer <<<`. Cost: one comment line. This also exposes an asymmetry to resolve: `uninstall_shell_completion` says "No rc/dotfile is read or written". | the two blocks side by side in `~/.bashrc`; `completion.py:931-935` |
| F-6 | LOW | THE INSTALLED ARTIFACTS ARE CORRECT AND ARE NOT THE DEFECT, recorded so nobody "fixes" them | The three files exist, sourcing registers `complete -F _aw_completion aw`, and with the framework loaded the lazy loader resolves ALL THREE entrypoint names. An earlier suspicion that the single multi-name `complete -F _aw_completion aw agentwf agent-workflows` was fragile was TESTED AND REFUTED: the per-alias symlinks (`_alias_filenames`, deliberate and documented) are what make it work. | per-name loader probe with the framework sourced |

## Proposed changes (ordered, validatable)

1. A pure predicate returning the three precondition facts separately, using `bash -ic` as the discriminator (E-01).
2. Four honest message variants, with the non-reachable case not labeled `ok` (E-02).
3. The guarded remediation snippet printed; the rc write opt-in on a TTY, wrapped in paired fence markers so it can be uninstalled and upgraded (E-03).
4. Injection-driven tests for all four states, pinning the false-success string (E-04).

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this plan does not modify the generated completion script, the drop-in layout, or the alias symlinks, all three verified CORRECT (F-6). It does not add dynamic id6/setid completion, which the verb's help already defers to a later `tabcomp` child. It does not edit any user rc file without explicit consent, and may legitimately end up printing advice only.

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

AMEND `install_shell_completion`'s DOCSTRING FOR THE CONSENTED WRITE (OQ-01 answered 2026-09-12). Its "NO user rc/dotfile is ever read or written" and the success line's "(no rc/dotfile modified)" are both about to become misleading: the FUNCTION may still write none, but the FEATURE now offers to. Either keep the write entirely outside that function and say so, or amend both strings to state that an rc write happens only on explicit TTY consent and never under `--yes`. Do not ship code whose docstring denies what the feature does.

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
  - Required evidence: paste the predicate and its three returned facts for this machine, alongside the raw discriminator output: `bash -lic 'echo ${BASH_COMPLETION_VERSINFO-}'` -> `2` and `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'` -> empty. Confirm by grep that the predicate writes nothing and that any rc access is a READ. A predicate returning a single boolean is a FAILED validation, since it cannot distinguish "install a package" from "add one line".
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the ACTUAL output of `aw completion install` in the NON-REACHABLE state and show it does NOT print an `ok` status and does NOT instruct a shell restart. Paste the reachable-state output showing today's message is preserved. Paste the absent-state and unknown-state outputs. Quote the four message variants from the diff.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the printed snippet verbatim and confirm the `BASH_COMPLETION_VERSINFO` guard is present. THE WRITE PATH IS NOW REQUIRED (OQ-01 answered), so paste ALL of: the rendered prompt showing a visible `[y/N]` default; a DECLINED run leaving a fixture `~/.bashrc` byte-identical; a non-TTY run and a `--yes` run each leaving it byte-identical; a CONSENTED run showing the appended stanza wrapped in BOTH fence markers with the file's prior content intact; a SECOND consenting run reported as a no-op with no duplicate stanza; the absent-`~/.bashrc` case REPORTING rather than creating; and the uninstall side, either removing exactly the fenced range (paste the rc file before and after, byte-identical to its pre-install state) or its docstring stating that the stanza is deliberately left with removal instructions. A stanza written with only an OPENING marker is a FAILED validation (F-7), because uninstall then cannot delete it without hardcoding its text. A missing write path is a FAILED validation, and a `--yes` run that writes is a FAILED validation regardless of anything else passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the passing tests for all four states and show each is driven by INJECTION, quoting the stub. Paste the assertion pinning that the non-reachable case prints no `ok` and no restart instruction. Paste the byte-comparison of the rc fixture. THEN paste the BARE `python3 -m pytest` summary and the failure-SET delta (criterion: empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

DO NOT DELETE A USER'S COMMITTED RUN RECORDS, anywhere in this Set. Relocation preserves history; deletion is unrecoverable and is the one outcome worse than leaving the retired directory in place.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
