# IPD: Complete a command's own arguments instead of falling through to the command list

- Date: 2026-09-12
- Kind: child
- Concern: TAB COMPLETION OFFERS THE TOP-LEVEL COMMAND LIST AS THE ARGUMENT TO A COMMAND, which is wrong for 30 of 47 commands and produces suggestions that cannot possibly be valid. Reported by the maintainer 2026-09-12 from a live session: `aw completion <TAB><TAB>` listed all 47 commands, `aw completion in<TAB>` narrowed to `include index install`, and taking the suggestion gave `error: unknown completion target 'index' (expected bash|zsh|fish|install|uninstall)`. The completion actively led them into an error.
  THE FALL-THROUGH IS THE BROADER HALF AND IS WORSE THAN THE REPORTED SYMPTOM. `generate_bash_completion` ends its `case` with an unconditional `COMPREPLY=( ... top_names ... )`, so ANY command whose `case` arm is absent suggests the whole command list. Measured: only 17 of 47 commands get an arm (those with real subparsers: `agy backlog config host ipd oc project prompts releases research reviews run runs specs storage work workflow`), so the other 30 all misbehave. Verified by driving the installed function directly: `aw find <TAB>`, `aw search <TAB>`, `aw install <TAB>` and `aw completion <TAB>` each return the same 47 items, so `aw find <TAB>` proposes `commit`, `uninstall` and `archive` as things to find.
  THE REPORTED CASE HAS ITS OWN SEPARATE CAUSE: POSITIONAL CHOICES ARE NEVER INTROSPECTED. `aw completion`'s valid values are a POSITIONAL argument with `choices`, not subparsers, so `introspect_cli_tree` records `subcommands: {}` for it (verified: `t['subcommands']['completion']` has keys `['flags','subcommands']` and an EMPTY subcommands dict). The tree walker only descends `_SubParsersAction`, so a command whose arguments are expressed as positional `choices` contributes nothing. Fixing the fall-through alone would make `aw completion <TAB>` offer NOTHING, which is better than a wrong answer but still not the right one.
  WHY THIS MATTERS MORE THAN A COSMETIC ANNOYANCE. A wrong completion is worse than no completion: it asserts that a token is valid, and a user who trusts it gets an error whose cause looks like the tool rather than the suggestion. The maintainer hit exactly that sequence within seconds of completion starting to work, which is also why it was invisible until now: completion was inert on this machine until the same session fixed it.
  AND THE INSTALLED SCRIPT IS A FROZEN SNAPSHOT NOBODY REFRESHES. The generated file is written once by `aw completion install`; nothing in the install/upgrade path regenerates it (`grep -rn 'completion' agent_workflows/engine.py` shows no regen/refresh call). So a framework upgrade that adds or renames a command leaves the user completing a stale vocabulary, and this defect's fix will not reach an already-installed user until they re-run the verb.
- Scope: Make the generated completion offer a COMMAND'S OWN arguments rather than the top-level command list. Three parts: (1) remove the top-level fall-through so a command with nothing to suggest suggests NOTHING; (2) teach `introspect_cli_tree` to capture positional `choices` so commands like `completion` contribute their real values; (3) decide and record whether the installed script is refreshed on upgrade, since the fix otherwise never reaches an installed user. EXCLUDES dynamic completion of id6s, setids and file paths, which the verb's `--help` already defers to a later `tabcomp` child; EXCLUDES zsh/fish beyond the equivalent generator change if it is cheap and correct; and EXCLUDES any change to the drop-in layout or the rc stanza (`compinert` Set owns that).
- Scope-Paths: agent_workflows/completion.py, tests/test_completion.py
- Item-Dependencies: none
- Status: to-review
- From-Backlog: g99sg7
- Priority: medium
- Work-Kind: bug
- Blocks-Release: next
- Set: compargs
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 4y95tp

## Workflow history
- 2026-09-12 to-review (aw set): status set to to-review

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop suggesting tokens that cannot be valid, and suggest the ones that can.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop the wrong answer, then give the right one

- [ ] E-01 REMOVE THE TOP-LEVEL FALL-THROUGH, so a command with nothing to offer offers NOTHING.
  THE LINE IS THE LAST `COMPREPLY=` IN `generate_bash_completion`, after the `esac`. It exists so the function always returns something, which is precisely the bug: for the 30 commands without a `case` arm it returns a list of tokens that are all invalid in that position.
  NO SUGGESTION IS THE CORRECT FALLBACK, and this is worth stating because "complete nothing" feels like a regression. Bash falls back to its own default (filenames) when `COMPREPLY` is empty, which for `aw find <PATTERN>` or `aw show <PATH>` is frequently what the user wants and is never actively misleading. Offering `archive` as a thing to `find` is.
  DO NOT REPLACE IT WITH THE FLAG LIST EITHER. Flags are already handled by the `$cur == -*` branch above; repeating them unprefixed would suggest bare words like `agent` and `apply`.
  - Depends on: none
  - Expected outcome: the generated script's `case` has no unconditional top-level fallback after `esac`, and a command with no arm yields an empty `COMPREPLY`.
  - Execution state: pending

- [ ] E-02 TEACH `introspect_cli_tree` TO CAPTURE POSITIONAL `choices`, which is what the reported case actually needs.
  THE GAP, MEASURED: the walker descends only `_SubParsersAction`, so `t['subcommands']['completion']['subcommands']` is `{}` even though the command has a fixed valid vocabulary (`bash|zsh|fish|install|uninstall`). Any command expressing its arguments as a positional with `choices` is invisible to the generator.
  CAPTURE `choices` UNDER A DISTINCT KEY, not by merging them into `subcommands`. They are not subcommands: they do not nest, they carry no flags of their own, and conflating them would make the generator emit a third-level `case` for something that cannot have one. A separate key also lets the generator decide presentation per shell.
  DO NOT INVENT VALUES FOR AN UNCONSTRAINED POSITIONAL. A positional with no `choices` (a path, a selector, an id6) must contribute NOTHING here; guessing is how the current defect began. Dynamic values are explicitly deferred to a later `tabcomp` child.
  SURVEY WHAT ELSE THIS FIXES, and record the count: several verbs take a status or type token with `choices`, so the sweep is likely to improve more than `completion`. Name them in the evidence rather than claiming a general improvement.
  - Depends on: E-01
  - Expected outcome: positional `choices` captured under their own key, unconstrained positionals contributing nothing, and a recorded list of every command whose completion improves as a result.
  - Execution state: pending

- [ ] E-03 EMIT THE CAPTURED CHOICES, so `aw completion <TAB>` offers exactly `bash fish install uninstall zsh`.
  MERGE, DO NOT REPLACE, for a command that has BOTH subcommands and a choices-bearing positional; if none exists today, say so and still write the code so the case is handled rather than latent.
  KEEP THE GENERATED SCRIPT SELF-CONTAINED AND STATIC, which is the existing contract in the module docstring. Do not add a runtime call back into `aw` to resolve choices: that would make every TAB press pay interpreter startup, measured elsewhere in this repo at ~220ms, and would make completion fail when the tool is mid-upgrade.
  - Depends on: E-02
  - Expected outcome: `aw completion <TAB>` yields the five real targets and nothing else; a command with both subcommands and choices offers the union.
  - Execution state: pending

- [ ] E-04 TEST BY DRIVING THE GENERATED FUNCTION, NOT BY READING THE SCRIPT, and cover the regression that started this.
  THE TECHNIQUE THAT FOUND THIS BUG, and the one the tests should use: source the generated script in a subshell, set `COMP_WORDS`/`COMP_CWORD`, call `_aw_completion`, and inspect `COMPREPLY`. Asserting on the script's TEXT would have passed throughout, because the text was always internally consistent; only executing it revealed that `aw find <TAB>` returns 47 command names.
  THE FOUR CASES: `aw completion <TAB>` yields exactly the five targets; `aw find <TAB>` yields EMPTY (the fall-through regression); a subcommand-bearing command such as `aw ipd <TAB>` still yields its subcommands, so E-01 did not break the working half; and `aw completion in<TAB>` yields `install` ALONE, which is the maintainer's exact reported sequence and must no longer offer `include index`.
  PIN THE INVALID SUGGESTION EXPLICITLY: assert that `index` is NOT in the reply for `aw completion in<TAB>`. A test that only checks `install` is present would pass against today's broken build.
  - Depends on: E-03
  - Expected outcome: four executed cases green, including an explicit assertion that the reported invalid suggestion is absent.
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
| F-1 | HIGH | the fall-through misfires for 30 of 47 commands | `generate_bash_completion` emits an unconditional top-level `COMPREPLY` after `esac`; only 17 commands get a `case` arm. Driven directly, `aw find <TAB>`, `aw search <TAB>`, `aw install <TAB>` and `aw completion <TAB>` all return the same 47 command names. | the generator; the function driven in a subshell |
| F-2 | HIGH | positional `choices` are never introspected | `introspect_cli_tree` descends only `_SubParsersAction`, so `completion`'s `subcommands` is `{}` despite a fixed `bash\|zsh\|fish\|install\|uninstall` vocabulary. Fixing F-1 alone would make it offer nothing. | `t['subcommands']['completion']` inspected |
| F-3 | HIGH | the completion led the user into an error | `aw completion in<TAB>` offered `include index install`; taking `index` produced `error: unknown completion target 'index'`. A wrong suggestion asserts validity, so the user blames the tool rather than the hint. | the maintainer's session transcript 2026-09-12 |
| F-4 | MEDIUM | no test would have caught it | `tests/test_completion.py` has no assertion on the second-level reply or the fall-through. Text-level assertions could not catch it: the script was always internally consistent. | grep over the test file |
| F-5 | MEDIUM | the installed script is a frozen snapshot | nothing in the install/upgrade path regenerates it, so an upgrade that adds or renames a command leaves a stale vocabulary, and this fix will not reach an installed user until they re-run `aw completion install`. | `grep -rn 'completion' agent_workflows/engine.py` |
| F-6 | LOW | the defect was masked until today | completion was inert on the reporting machine because bash-completion was not loaded for interactive shells (`compinert` Set, backlog `lalwnj`), so nobody could observe the wrong suggestions. | that Set's evidence |

## Proposed changes (ordered, validatable)

1. Remove the post-`esac` top-level fall-through so a command with nothing to offer offers nothing (E-01).
2. Capture positional `choices` under their own key in the CLI tree (E-02).
3. Emit those choices, merged with subcommands where both exist (E-03).
4. Test by DRIVING the generated function, pinning the reported invalid suggestion as absent (E-04).

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this plan does not add dynamic completion of id6s, setids, statuses-from-disk or file paths, which the verb's own `--help` defers to a later `tabcomp` child. It does not change the drop-in layout, the alias symlinks or the rc stanza (the `compinert` Set owns those). It does not add a runtime callback into `aw`, which would put interpreter startup on every TAB press.

## Required tests / validation

- FOUR DRIVEN CASES, executed rather than read: `aw completion <TAB>` -> exactly the five targets; `aw find <TAB>` -> EMPTY; `aw ipd <TAB>` -> its subcommands unchanged; `aw completion in<TAB>` -> `install` with `index` explicitly ABSENT.
- THE INVALID SUGGESTION PINNED: asserting `install` is present would pass against today's broken build, so the absence of `index` is the load-bearing assertion.
- THE GENERATED SCRIPT STAYS STATIC: no runtime callback into `aw`.
- `python3 -m pytest` BARE, failure-SET delta empty.
- `aw sanitize --agent` clean.

## Spec / documentation sync

No spec governs completion; `generate_bash_completion`'s docstring is the contract and must be amended. It currently says the function "offers the top-level commands, then the nested subcommands of the first word, plus flags" - which is an accurate description of the DEFECT. Rewrite it to state that a command offers its own subcommands and positional choices, and that a command with neither offers nothing, so the docstring stops endorsing the fall-through.

`introspect_cli_tree`'s docstring must record that it captures positional `choices` as well as subparsers, and that an unconstrained positional deliberately contributes nothing.

## Open questions

### OQ-01: Should `aw install`/upgrade regenerate an installed completion script (F-5)?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: RAISED, NOT RESOLVED, AND DELIBERATELY LEFT TO THE MAINTAINER, because it is a scope-and-behavior decision rather than a fact. THE FACT is settled: nothing regenerates the installed script today, so this plan's fix reaches an already-installed user only when they re-run `aw completion install`, and any future command rename silently leaves them completing a vocabulary that no longer exists. THE DECISION is whether the installer should rewrite a file in the user's home directory on every upgrade. Arguments both ways are real: regenerating keeps completion honest and is a file this tool already owns and sentinels, but it also means an upgrade touches `~/.local/share/...` without asking, and the `compinert` Set is concurrently establishing that user-scoped writes want consent. NOT MARKED BLOCKING because Orders E-01 through E-04 are complete and correct without it; the staleness is a pre-existing condition this plan neither creates nor worsens. If the maintainer wants it, it is a small addition to the install path plus a test; if not, the honest alternative is a line in `aw doctor` reporting that the installed completion is older than the CLI.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the generator diff showing the post-`esac` fallback removed, and paste the DRIVEN result for `aw find <TAB>` showing an EMPTY `COMPREPLY` (item count 0). Quoting the diff alone is insufficient: the bug was invisible in the script text and only appeared when the function was executed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `introspect_cli_tree(...)['subcommands']['completion']` BEFORE and AFTER, showing the choices now captured under their own key and NOT merged into `subcommands`. Paste the recorded list of every command whose completion improves, with counts. Paste one unconstrained-positional command showing it contributes nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the DRIVEN result for `aw completion <TAB>` showing exactly `bash fish install uninstall zsh`. Confirm by grep that the generated script contains no runtime callback into `aw` (it must stay static and self-contained).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste all four driven cases with their actual `COMPREPLY` contents, including `aw completion in<TAB>` -> `install` with an explicit assertion that `index` is ABSENT, and `aw ipd <TAB>` still returning its subcommands. THEN paste the BARE `python3 -m pytest` summary and the failure-SET delta (criterion: empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

DO NOT DELETE A USER'S COMMITTED RUN RECORDS, anywhere in this Set. Relocation preserves history; deletion is unrecoverable and is the one outcome worse than leaving the retired directory in place.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
