# IPD: Complete a command's own arguments instead of falling through to the command list

- Date: 2026-09-12
- Kind: child
- Concern: TAB COMPLETION OFFERS THE TOP-LEVEL COMMAND LIST AS THE ARGUMENT TO A COMMAND, which is wrong for 30 of 47 commands and produces suggestions that cannot possibly be valid. Reported by the maintainer 2026-09-12 from a live session: `aw completion <TAB><TAB>` listed all 47 commands, `aw completion in<TAB>` narrowed to `include index install`, and taking the suggestion gave `error: unknown completion target 'index' (expected bash|zsh|fish|install|uninstall)`. The completion actively led them into an error.
  THE FALL-THROUGH IS THE BROADER HALF AND IS WORSE THAN THE REPORTED SYMPTOM. `generate_bash_completion` ends its `case` with an unconditional `COMPREPLY=( ... top_names ... )`, so ANY command whose `case` arm is absent suggests the whole command list. Measured: only 17 of 47 commands get an arm (those with real subparsers: `agy backlog config host ipd oc project prompts releases research reviews run runs specs storage work workflow`), so the other 30 all misbehave. Verified by driving the installed function directly: `aw find <TAB>`, `aw search <TAB>`, `aw install <TAB>` and `aw completion <TAB>` each return the same 47 items, so `aw find <TAB>` proposes `commit`, `uninstall` and `archive` as things to find.
  THE REPORTED CASE HAS ITS OWN SEPARATE CAUSE: POSITIONAL CHOICES ARE NEVER INTROSPECTED. `aw completion`'s valid values are a POSITIONAL argument with `choices`, not subparsers, so `introspect_cli_tree` records `subcommands: {}` for it (verified: `t['subcommands']['completion']` has keys `['flags','subcommands']` and an EMPTY subcommands dict). The tree walker only descends `_SubParsersAction`, so a command whose arguments are expressed as positional `choices` contributes nothing. Fixing the fall-through alone would make `aw completion <TAB>` offer NOTHING, which is better than a wrong answer but still not the right one.
  WHY THIS MATTERS MORE THAN A COSMETIC ANNOYANCE. A wrong completion is worse than no completion: it asserts that a token is valid, and a user who trusts it gets an error whose cause looks like the tool rather than the suggestion. The maintainer hit exactly that sequence within seconds of completion starting to work, which is also why it was invisible until now: completion was inert on this machine until the same session fixed it.
  AND THE INSTALLED SCRIPT IS A FROZEN SNAPSHOT NOBODY REFRESHES. The generated file is written once by `aw completion install`; nothing in the install/upgrade path regenerates it (`grep -rn 'completion' agent_workflows/engine.py` shows no regen/refresh call). So a framework upgrade that adds or renames a command leaves the user completing a stale vocabulary, and this defect's fix will not reach an already-installed user until they re-run the verb.
- Scope: Make the generated completion offer a COMMAND'S OWN arguments rather than the top-level command list. Three parts: (1) remove the top-level fall-through so a command with nothing to suggest suggests NOTHING; (2) teach `introspect_cli_tree` to capture positional `choices` so commands like `completion` contribute their real values; (3) WARN when an installed script is stale, without rewriting it (maintainer ruling 2026-09-12), since the fix otherwise never reaches an installed user and staleness is silent today. EXCLUDES dynamic completion of id6s, setids and file paths, which the verb's `--help` already defers to a later `tabcomp` child; EXCLUDES zsh/fish beyond the equivalent generator change if it is cheap and correct; and EXCLUDES any change to the drop-in layout or the rc stanza (`compinert` Set owns that).
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- From-Backlog: g99sg7
- Priority: medium
- Work-Kind: bug
- Blocks-Release: next
- Set: compargs
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 4y95tp

## Workflow history
- 2026-09-22 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 4y95tp verified (set compargs, attempt 1).
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-12 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (BLOCKER, OPEN and escalated to blocking OQ-02), PR-002 (HIGH, OPEN and escalated to blocking OQ-03), PR-003..PR-011 FIXED; readiness `no-go` because two blocking questions remain. Record: `.aw/records/reviews/20260912-compargs-01-4y95tp-complete-a-command-s-own-arguments-instead-of-falling-throug.review.md`. `aw ipd lint --phase author` CONFORMING (clean, 0 findings) before semantic review. Suite measured bare at HEAD `03e1436c`: `5971 passed, 3 skipped, 2 xfailed in 59.70s`. DISCLOSURE: same agent/model family authored this plan, so treat as a near-self-review; its value rests on what was EXECUTED.
  THE DEFECT IS REAL AND EVERY SYMPTOM REPRODUCES EXACTLY. Driven, not read: the generated script was written to a scratch file, sourced in a subshell, and `_aw_completion` called with real `COMP_WORDS`/`COMP_CWORD`. `aw find <TAB>` returns 47 items, `aw completion <TAB>` returns 47 items, `aw install <TAB>` returns 47 items, `aw ipd <TAB>` correctly returns its 9 subcommands, and `aw completion in<TAB>` returns exactly `include index install`, the maintainer's reported sequence character for character. The population counts are exact: 47 top-level commands, 17 with a `case` arm, 30 without.
  THE BLOCKER IS THAT E-02/E-03's MECHANISM CANNOT FIX THE REPORTED CASE, and this was proven by simulating the fix rather than by reasoning about it. `aw completion`'s `target` positional has `choices=None`; it is a FREE-FORM `nargs="?"` argument whose vocabulary is enforced by a runtime `if shell not in ("bash","zsh","fish")` in `_run_completion` and advertised only as a `metavar` STRING. So capturing positional `choices` captures NOTHING for `completion`, and E-03's stated outcome ("`aw completion <TAB>` offers exactly `bash fish install uninstall zsh`") is unreachable by the route the plan specifies. Simulated exactly as written: the captured list is `[]`. Worse, the shape is DELIBERATE and documented at `cli.py:4735-4737` (the install/uninstall verbs are "ADDITIVE on child 01's free-form `target` positional"), so this is a design decision to be changed with intent, not an oversight to patch. Escalated as blocking OQ-02 with three costed options.
  THE SECOND ESCALATION IS THAT THE PLAN FIXES ONE OF TWO COMPLETION SURFACES AND BREAKS A DOCUMENTED PARITY CONTRACT. `complete_query` (the dynamic engine behind `aw __complete`) is a SECOND surface the plan never mentions. Measured: it ALREADY returns `[]` for `aw completion <TAB>`, `aw find <TAB>` and `aw install <TAB>`, so it does not have the fall-through bug at all, and `_subcommand_candidates`'s docstring states it "mirrors the generated static scripts so `__complete` and the offline scripts agree on the static layer". Teaching the static generator about choices while leaving the dynamic engine ignorant would make the two surfaces DISAGREE, breaking that contract in the same change that fixes the bug. Escalated as blocking OQ-03.
  TWO SECTIONS WERE COPIED FROM AN UNRELATED SET. The entire `## Project conventions discovered (Step 0)` block is BYTE-IDENTICAL to `wfartifacts` child `gzhd7t` (verified with `diff`), and four of five `## Deferred` bullets belong to that Set too. They discuss run-scratch relocation, D92, `.aw/.gitignore` anchoring and `tools/untrack-workflow-artifacts.py`, none of which this plan touches. Replaced with conventions actually discovered about completion.
- 2026-09-12 to-review (aw set): status set to to-review

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop suggesting tokens that cannot be valid, and suggest the ones that can.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop the wrong answer, then give the right one

- [x] E-01 REMOVE THE TOP-LEVEL FALL-THROUGH, so a command with nothing to offer offers NOTHING.
  THE LINE IS THE LAST `COMPREPLY=` IN `generate_bash_completion`, after the `esac`. It exists so the function always returns something, which is precisely the bug: for the 30 commands without a `case` arm it returns a list of tokens that are all invalid in that position.
  NO SUGGESTION IS THE CORRECT FALLBACK, and this is worth stating because "complete nothing" feels like a regression. Bash falls back to its own default (filenames) when `COMPREPLY` is empty, which for `aw find <PATTERN>` or `aw show <PATH>` is frequently what the user wants and is never actively misleading. Offering `archive` as a thing to `find` is.
  DO NOT REPLACE IT WITH THE FLAG LIST EITHER. Flags are already handled by the `$cur == -*` branch above; repeating them unprefixed would suggest bare words like `agent` and `apply`.
  - Depends on: none
  - Expected outcome: the generated script's `case` has no unconditional top-level fallback after `esac`, and a command with no arm yields an empty `COMPREPLY`.
  - Execution state: performed

- [x] E-02 TEACH `introspect_cli_tree` TO CAPTURE POSITIONAL `choices`, which is what the reported case actually needs.
  THE GAP, MEASURED: the walker descends only `_SubParsersAction`, so `t['subcommands']['completion']['subcommands']` is `{}` even though the command has a fixed valid vocabulary (`bash|zsh|fish|install|uninstall`). Any command expressing its arguments as a positional with `choices` is invisible to the generator.
  CAPTURE `choices` UNDER A DISTINCT KEY, not by merging them into `subcommands`. They are not subcommands: they do not nest, they carry no flags of their own, and conflating them would make the generator emit a third-level `case` for something that cannot have one. A separate key also lets the generator decide presentation per shell.
  DO NOT INVENT VALUES FOR AN UNCONSTRAINED POSITIONAL. A positional with no `choices` (a path, a selector, an id6) must contribute NOTHING here; guessing is how the current defect began. Dynamic values are explicitly deferred to a later `tabcomp` child.
  THE SURVEY IS ALREADY DONE AND THE ANSWER IS TWO COMMANDS, NOT "SEVERAL". Measured at review by walking the real parser: exactly two commands have a choices-bearing positional, `migrate-layout action` (`apply cleanup inventory plan resume rollback status wizard`) and `path root` (`config records state system`). The authored guess that "several verbs take a status or type token with `choices`" is FALSE: the status arguments are free-form `nargs="+"`, which `completion.py`'s own module docstring already records as a verified shape fact. Re-derive the list and paste the walk, but do not expect it to grow.
  `completion` IS NOT IN THAT LIST, WHICH IS THE POINT OF PR-001. Its `target` is `nargs="?"` with `choices=None`, so this item does NOT fix the reported case and must not claim to. Whether it becomes fixable is blocking OQ-02.
  - Depends on: E-01
  - Expected outcome: positional `choices` captured under their own key, unconstrained positionals contributing nothing, and the re-derived list of improved commands pasted with its walk, stated as the two commands measured rather than as a general improvement.
  - Execution state: performed

- [x] E-03 EMIT THE CAPTURED CHOICES, so `aw migrate-layout <TAB>` and `aw path <TAB>` offer their real vocabularies.
  THE EXPECTED OUTCOME WAS CORRECTED AT REVIEW. As authored this item promised `aw completion <TAB>` would yield `bash fish install uninstall zsh`, which E-02's mechanism CANNOT deliver: simulated exactly as specified, the captured choice list for `completion` is `[]` because its positional has `choices=None` (PR-001, blocking OQ-02). Do not write that promise into a test; it would fail for a reason the code cannot fix. The two commands this item genuinely serves are `migrate-layout` and `path`.
  DO NOT DELIVER THIS ITEM UNTIL OQ-03 IS ANSWERED, because emitting choices in the static script while `complete_query` stays ignorant of them makes the two surfaces disagree, and `_subcommand_candidates`'s docstring declares they must agree. The answer decides whether the choices capture is consumed by both surfaces or by one.
  MERGE, DO NOT REPLACE, for a command that has BOTH subcommands and a choices-bearing positional. MEASURED: no such command exists today (the two choices-bearing commands have no subparsers), so this path is latent by construction. Write it anyway and SAY it is untested against a real case rather than implying coverage.
  KEEP THE GENERATED SCRIPT SELF-CONTAINED AND STATIC, which is the existing contract in the module docstring. Do not add a runtime call back into `aw` to resolve choices: that would make every TAB press pay interpreter startup, measured elsewhere in this repo at ~220ms, and would make completion fail when the tool is mid-upgrade.
  - Depends on: E-02
  - Expected outcome: `aw migrate-layout <TAB>` yields its eight actions and `aw path <TAB>` its four roots; the both-kinds merge path exists and is declared latent; no claim made about `aw completion <TAB>`, which OQ-02 owns.
  - Execution state: performed

- [x] E-04 TEST BY DRIVING THE GENERATED FUNCTION, NOT BY READING THE SCRIPT, and cover the regression that started this.
  THE TECHNIQUE THAT FOUND THIS BUG, and the one the tests should use: source the generated script in a subshell, set `COMP_WORDS`/`COMP_CWORD`, call `_aw_completion`, and inspect `COMPREPLY`. Asserting on the script's TEXT would have passed throughout, because the text was always internally consistent; only executing it revealed that `aw find <TAB>` returns 47 command names.
  THE CASE LIST WAS CORRECTED AT REVIEW, because two of the four authored cases assert an outcome the code cannot produce. As authored: `aw completion <TAB>` yields the five targets, and `aw completion in<TAB>` yields `install` ALONE. Both depend on `completion`'s positional carrying `choices`, which it does not (PR-001). Under OQ-02's option (b) or (c) they become true and MUST be added; under option (a) they never do. So they are conditional on that answer and are listed separately below.
  THE FOUR UNCONDITIONAL CASES, true under every OQ-02 answer: `aw find <TAB>` yields EMPTY (the fall-through fix); `aw install <TAB>` yields EMPTY (a second command from the 30, so the fix is not special-cased to one name); `aw ipd <TAB>` still yields its 9 subcommands, proving E-01 did not break the working half; and `aw migrate-layout <TAB>` yields its eight actions, which is E-03's real deliverable.
  THE TWO CONDITIONAL CASES, to be added only if OQ-02 makes `aw completion` completable: `aw completion <TAB>` yields exactly `bash fish install uninstall zsh`, and `aw completion in<TAB>` yields `install` with `index` explicitly ABSENT. PIN THE INVALID SUGGESTION in the second: a test that only checks `install` is present would pass against today's broken build, which returns `include index install`.
  IF OQ-02 IS ANSWERED (a), SAY SO IN THE TEST FILE rather than silently omitting the maintainer's reported case. A comment naming the reported sequence and recording that `aw completion <TAB>` deliberately offers nothing is what stops a later agent "fixing" it by reintroducing a fall-through.
  - Depends on: E-03
  - Expected outcome: the four unconditional cases green; the two conditional cases present or explicitly recorded as not-applicable with OQ-02's answer cited.
  - Execution state: performed

- [x] E-05 KEEP THE TWO COMPLETION SURFACES IN AGREEMENT. OQ-03 IS ANSWERED (maintainer 2026-09-12): MAKE THEM AGREE. The amend-the-docstring branch is CLOSED and must not be taken.
  THE CONTRACT IS DOCUMENTED, NOT INFERRED: `_subcommand_candidates`'s docstring says it "mirrors the generated static scripts so `__complete` and the offline scripts agree on the static layer". E-01 through E-03 change the static side only, so this item is what stops the change from breaking that sentence.
  MEASURED STARTING POINT: `complete_query` already returns `[]` for `aw completion <TAB>`, `aw find <TAB>` and `aw install <TAB>`, so it does NOT need E-01's fix; the divergence E-02/E-03 introduce is the choices half, where the static script would offer `migrate-layout`'s actions and the dynamic engine would not.
  SHARE THE CAPTURE: have `_subcommand_candidates` consume the same key E-02 writes, so the two surfaces cannot drift by construction rather than by discipline. Do NOT amend the parity docstring to license a difference; the maintainer declined that, and positional `choices` are STATIC vocabulary by the contract's own definition (fixed, not read from disk), so they belong in the mirrored layer.
  DO NOT COLLAPSE THE TWO SURFACES INTO ONE. Not authorized: they exist for different reasons (an offline script with no interpreter cost; a live engine that reads repository state), and the docstring asks them to AGREE on the static layer, not to become one code path.
  ADD A PARITY TEST, which is the durable half and which nothing provides today. Assert that for the same word list the static script's `COMPREPLY` and `complete_query`'s return agree on the static layer, with `aw completion <TAB>` as an explicit case. Without it, the next change reintroduces this divergence silently, exactly as this plan nearly did.
  - Depends on: E-04
  - Expected outcome: `complete_query` and the generated script return the same candidates for the same position on every command E-03 touched, OR the parity docstring amended with the reason, with OQ-03's answer cited either way.
  - Execution state: performed

- [x] E-08 GIVE `aw completion`'s POSITIONAL REAL `choices`, WITHOUT WHICH THE REPORTED CASE CANNOT BE FIXED (OQ-02, maintainer ruling 2026-09-12).
  THIS PLAN'S AUTHORED PREMISE WAS FALSE AND THIS ITEM IS THE CORRECTION. Verified twice: that positional reports `choices=None` with `metavar='bash|zsh|fish|install|uninstall'`, so the vocabulary exists ONLY as a DISPLAY string and E-02's capture had nothing to find. Adding `choices` is what converts a vocabulary already fixed in practice into one the tooling can see.
  DERIVE THE LIST, DO NOT WRITE A SECOND LITERAL. `completion.SUPPORTED_SHELLS` already exists and `--shell` already uses it as `choices`; build the positional's list from that plus the two verbs. A hand-written second copy reintroduces the drift this defect is made of, one field over.
  THIS IS A DELIBERATE NARROWING OF A PUBLIC SURFACE, so treat the two things it breaks as work, not as surprises. FIRST, `tests/test_completion.py:206-214` (`test_parser_shape_allows_child03_extension`) PINS the free-form shape and asserts the parse is "not constrained by `choices=`". UPDATE it rather than deleting it: its intent (a future verb parses without a redesign) survives, but such a verb must now be REGISTERED, and the test's comment must say the constraint was tightened on purpose so a reader does not read it as the guarantee being dropped. SECOND, `cli.py:4735-4737` documents the free-form shape as intentional; amend that comment in the same change.
  THE ERROR MESSAGE MOVES FROM THE HANDLER TO ARGPARSE, and the maintainer accepted that visible cost. Today an unknown target reaches the handler, which raises `unknown completion target 'index' (expected bash|zsh|fish|install|uninstall)`. With `choices`, argparse rejects at parse time with its own wording and exit code. Confirm the new message is at least as clear, and if the handler's validation becomes unreachable, REMOVE it rather than leaving two validators that can disagree.
  - Depends on: E-02
  - Expected outcome: the positional carries `choices` derived from `SUPPORTED_SHELLS` plus the verbs; the pinned shape test is updated with its reason; the `cli.py` shape comment is amended; and dead handler validation is removed rather than orphaned.
  - Execution state: performed

- [x] E-06 WARN WHEN AN INSTALLED COMPLETION IS STALE, WITHOUT REWRITING IT (maintainer ruling 2026-09-12, OQ-01).
  WIDEN THE EXISTING PREDICATE, DO NOT ADD A SURFACE. `_completion_tip` (`cli.py:5519`) already prints the enable-tip when completion is ABSENT and returns silently otherwise, because `_completion_configured` (`:5509`) composes `is_completion_installed`, a PRESENCE check. The never-installed case is therefore already covered; the STALE case takes the silent branch and is the whole gap. Add a second state rather than a second mechanism.
  DETECT BY BYTE COMPARISON, WHICH IS MEASURED SUFFICIENT: comparing the installed file's body, minus the injected `INSTALL_SENTINEL` line, against a fresh `generate_bash_completion()` returns True on a current install (verified at review). No version stamp, no timestamp, no hash file is needed, and each would be a new artifact to keep in sync.
  NEVER REWRITE THE FILE HERE. The ruling is warn-only, and this is the load-bearing constraint: the user's completion file is theirs once written, and `compinert` is concurrently establishing that user-scoped writes require consent. `aw install` must not touch `~/.local/share/bash-completion/completions/` at all.
  SAY WHAT TO RUN, in the maintainer's own shape: name `aw completion install` explicitly, and say that completion is OUTDATED rather than broken, since the stale script still works for every command whose name did not change.
  DO IT ONCE PER INVOCATION, NOT PER REPO. This is a per-user/per-machine concern and `_completion_tip`'s docstring already records that reasoning for the absent case; a batch install across many repos must not repeat the warning per target.
  COMPARE PER DETECTED SHELL ONLY. Do not warn about zsh when the user runs bash; `_detect_shell` already scopes the existing tip and the same scoping applies.
  RE-VERIFIED AT REVIEW: every citation in this item is accurate. `_completion_tip` is at `cli.py:5519`, `_completion_configured` at `:5509`, and the tip is called from THREE sites (`:5437`, `:5505`, `:6794`), each outside the per-repo loop, so the once-per-invocation property already holds and this item inherits rather than builds it. The byte comparison was driven against the live install and returns True.
  - Depends on: E-04
  - Expected outcome: `aw install` warns exactly once when the installed completion differs from what the current CLI would generate, names `aw completion install`, and writes nothing; the absent case keeps today's tip and a current install stays silent.
  - Execution state: performed

- [x] E-07 AMEND THE THREE DOCSTRINGS THIS CHANGE FALSIFIES, which the plan's own spec-sync section requires and no item carried.
  `generate_bash_completion`'s docstring currently says the function "offers the top-level commands, then the nested subcommands of the first word, plus flags" - an accurate description of the DEFECT. Rewrite it to state that a command offers its own subcommands and positional choices, and that a command with neither offers nothing, so the docstring stops endorsing the fall-through.
  `introspect_cli_tree`'s docstring must record that it captures positional `choices` as well as subparsers, under their own key, and that an unconstrained positional deliberately contributes nothing.
  THE MODULE DOCSTRING IS THE THIRD AND THE PLAN MISSED IT. `completion.py`'s header states as a verified shape fact that "the CLI status arguments are free-form `nargs="+"` (NOT argparse `choices`...)". That remains true, but the module now also reads positional choices, so the header should say which arguments DO carry them (`migrate-layout action`, `path root`) rather than leaving a reader to infer that nothing does.
  - Depends on: E-05
  - Expected outcome: all three docstrings amended, with the fall-through description removed and the two choices-bearing commands named.
  - Execution state: performed

## Project conventions discovered (Step 0)

CORRECTED AT REVIEW 2026-09-12: the authored block here was BYTE-IDENTICAL to `wfartifacts` child `gzhd7t` (verified with `diff`) and described run-scratch relocation, D92, `.aw/.gitignore` anchoring and `install_into_repo`, none of which this plan touches. Replaced with conventions actually discovered about completion.

- THERE ARE TWO COMPLETION SURFACES, NOT ONE, and this plan as authored addressed only the first. (1) STATIC: `generate_{bash,zsh,fish}_completion` emit a self-contained script installed as a drop-in file; this is what the maintainer's shell actually runs (verified: the installed `~/.local/share/bash-completion/completions/aw` is the static generator's output and contains zero `__complete` references). (2) DYNAMIC: `complete_query` answers a live query via the hidden `aw __complete` subcommand, reachable through argcomplete. Any change to what a position offers has to consider both.
- THE DYNAMIC ENGINE DOES NOT HAVE THIS BUG. Measured: `complete_query(["aw","completion",""], 2)` returns `[]`, as do the `find` and `install` equivalents. So the fall-through is a property of the STATIC bash generator alone, and the dynamic engine is already the behavior E-01 aims for.
- THE TWO SURFACES HAVE A DOCUMENTED PARITY CONTRACT. `_subcommand_candidates`'s docstring: it "mirrors the generated static scripts so `__complete` and the offline scripts agree on the static layer". A change that teaches one about positional choices and not the other breaks that contract.
- ONLY BASH HAS THE FALL-THROUGH. Verified by generating all three: the zsh script's `args` state ends its inner `case` with no default arm, and every fish `complete` line carries a `__fish_use_subcommand` or `__fish_seen_subcommand_from` condition (0 unconditional lines). So the zsh/fish "equivalent generator change" the Scope contemplates has no fall-through to remove, though the positional-choices half would still apply to them.
- `aw completion`'s VOCABULARY IS NOT IN `choices`. Its `target` is `nargs="?"` with `choices=None` (`cli.py:4727-4734`); the valid set is enforced by a runtime `if` in `_run_completion` (`cli.py:10466`) and advertised only via `metavar='bash|zsh|fish|install|uninstall'`. The free-form shape is DELIBERATE and documented at `cli.py:4735-4737`. This is why E-02's mechanism cannot reach the reported case (PR-001).
- EXACTLY TWO COMMANDS HAVE A CHOICES-BEARING POSITIONAL, enumerated by walking the real parser: `migrate-layout action` (`apply cleanup inventory plan resume rollback status wizard`) and `path root` (`config records state system`). That is the true scope of E-02's improvement, and `completion` is NOT among them.
- 28 OF 47 COMMANDS WILL OFFER NOTHING after E-01 plus E-02 plus E-03 as specified, computed from the parser: everything with neither subparsers nor a choices-bearing positional. `completion` is in that list, which is what makes E-03's stated outcome unreachable as written.
- `_completion_tip` ALREADY EXISTS AND IS CALLED FROM THREE SITES (`cli.py:5437`, `:5505`, `:6794`), each once per invocation outside the per-repo loop, with a docstring recording that reasoning. `_completion_configured` composes `is_completion_installed`, a PRESENCE check, so the stale case takes the silent branch. E-05's citations were re-verified and are accurate.
- BYTE COMPARISON DETECTS STALENESS. Verified against the live install: stripping the `INSTALL_SENTINEL` line from the installed file and comparing to a fresh `generate_bash_completion()` returns True on a current install, so no version stamp is needed.
- THE TEST FILE HAS 88 TESTS AND 26 `complete_query` ASSERTIONS, but no test sources the generated script and calls `_aw_completion`. Its bash assertions are text-level (`assertIn("_aw_completion()", script)`), which is exactly why the defect survived, confirming F-4.
- Shared checkout, concurrent edits; the suite runs BARE (`python3 -m pytest`). Re-locate every symbol by NAME, not by the line numbers cited here.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the fall-through misfires for 30 of 47 commands | `generate_bash_completion` emits an unconditional top-level `COMPREPLY` after `esac`; only 17 commands get a `case` arm. Driven directly, `aw find <TAB>`, `aw search <TAB>`, `aw install <TAB>` and `aw completion <TAB>` all return the same 47 command names. | the generator; the function driven in a subshell |
| F-2 | HIGH | positional `choices` are never introspected | `introspect_cli_tree` descends only `_SubParsersAction`, so a command expressing arguments as a positional with `choices` contributes nothing. CONFIRMED at review, but the SCOPE was overstated: exactly TWO commands are affected (`migrate-layout action`, `path root`), not "several". | parser walk at review |
| F-2b | BLOCKER | `completion`'s vocabulary is NOT in `choices`, so F-2's fix does not reach the reported case | The authored F-2 said `completion` has "a fixed `bash\|zsh\|fish\|install\|uninstall` vocabulary" and implied capturing `choices` would surface it. It does not. `target` is `nargs="?"` with `choices=None`; the set is enforced by a runtime `if` in `_run_completion` and advertised only as a `metavar` STRING. Simulating E-02 exactly as written captures `[]` for `completion`, so E-03's stated outcome is unreachable. The free-form shape is DELIBERATE and documented. | `cli.py:4727-4734`, `:4735-4737`, `:10466`; E-02 simulated at review |
| F-2c | HIGH | there is a SECOND completion surface the plan never mentions, and it already behaves correctly | `complete_query` (behind `aw __complete`) returns `[]` for `aw completion <TAB>`, `aw find <TAB>` and `aw install <TAB>`, so it lacks the fall-through entirely. `_subcommand_candidates`'s docstring declares the two surfaces "agree on the static layer". Teaching only the static generator about choices breaks that documented parity in the same change that fixes the bug. | `complete_query` driven at review; `_subcommand_candidates` docstring |
| F-3 | HIGH | the completion led the user into an error | `aw completion in<TAB>` offered `include index install`; taking `index` produced `error: unknown completion target 'index'`. A wrong suggestion asserts validity, so the user blames the tool rather than the hint. | the maintainer's session transcript 2026-09-12 |
| F-4 | MEDIUM | no test would have caught it | `tests/test_completion.py` has no assertion on the second-level reply or the fall-through. CONFIRMED with a count at review: 88 tests, 26 of them driving `complete_query`, and ZERO that source the generated script and call `_aw_completion`; its bash assertions are text-level (`assertIn("_aw_completion()", script)`). Text-level assertions could not catch it: the script was always internally consistent. | the test file counted at review |
| F-7 | MEDIUM | two whole sections were copied from an unrelated Set | The `## Project conventions discovered (Step 0)` block was BYTE-IDENTICAL to `wfartifacts` child `gzhd7t` (`diff` returns nothing), and four of five `## Deferred` bullets belong to that Set: run-scratch relocation, D92, `.aw/.gitignore` anchoring, `tools/untrack-workflow-artifacts.py`, backlog `2812t3`. None is touched by this plan. An executor reading them would look for a defect that is not here. | `diff` against `gzhd7t` at review |
| F-8 | LOW | only bash has the fall-through, so the zsh/fish scope note is half wrong | Generated all three at review: the zsh `args` state's inner `case` has no default arm, and all fish `complete` lines carry a `use_subcommand`/`seen_subcommand_from` condition (0 unconditional). So there is no fall-through to remove in either; the positional-choices half would still apply to them. | all three generators driven at review |
| F-9 | LOW | 28 of 47 commands will offer nothing after the fix, which is correct but worth stating | Computed from the parser: everything with neither subparsers nor a choices-bearing positional. This is the intended outcome (bash then falls back to filenames), but the number belongs in the record so nobody reads the post-fix silence as a new defect. | parser walk at review |
| F-5 | MEDIUM | the installed script is a frozen snapshot AND staleness is silent | nothing in the install/upgrade path regenerates it, so an upgrade that adds or renames a command leaves a stale vocabulary. Worse, `_completion_tip` goes SILENT once a file exists, because `_completion_configured` composes `is_completion_installed`, a presence check, so the outdated state is unreportable today. RESOLVED 2026-09-12: detect and WARN, never rewrite (E-05). Byte comparison against a fresh generation is measured sufficient. | `grep -rn 'completion' agent_workflows/engine.py`; `cli.py:5509-5530`; comparison run at review |
| F-6 | LOW | the defect was masked until today | completion was inert on the reporting machine because bash-completion was not loaded for interactive shells (`compinert` Set, backlog `lalwnj`), so nobody could observe the wrong suggestions. | that Set's evidence |

## Proposed changes (ordered, validatable)

1. Remove the post-`esac` top-level fall-through so a command with nothing to offer offers nothing (E-01). This alone resolves the reported HARM: `aw completion in<TAB>` stops offering `index`.
2. Capture positional `choices` under their own key in the CLI tree (E-02). Reaches two commands, not `completion`.
3. Emit those choices for `migrate-layout` and `path`, with the both-kinds merge path declared latent (E-03). Gated on OQ-03.
4. Test by DRIVING the generated function, four unconditional cases plus two conditional on OQ-02 (E-04).
5. Keep the static and dynamic surfaces in agreement, or amend the parity docstring (E-05). Gated on OQ-03.
6. Warn on a stale installed script without rewriting it, by widening the existing tip predicate (E-06).
7. Amend the three docstrings this change falsifies, including the module header the plan missed (E-07).

## Deferred / out of scope (with reason)

CORRECTED AT REVIEW 2026-09-12: four of the five authored bullets were copied from `wfartifacts` child `gzhd7t` and concerned run-scratch relocation, D92, `tools/untrack-workflow-artifacts.py` and backlog `2812t3`, none of which this plan touches (F-7). Replaced with this plan's real exclusions.

- DYNAMIC COMPLETION OF id6s, setids, STATUSES-FROM-DISK AND FILE PATHS in the STATIC script. The verb's own `--help` defers this to a later `tabcomp` child, and `complete_query` already does it for the dynamic surface. This plan completes only what the parser itself declares.
  - Carrier-Declined: NOT this plan's debt, and already SERVED for the surface that needs it. The dynamic engine `complete_query` resolves id6s, Set ids, run ids and status vocabularies today (verified at execution: `complete_query(['aw','ipd','lint',''],3)` returns real plan id6s), so the capability EXISTS; what is excluded is duplicating it inside the offline script, which the deferred bullet above it forbids on performance grounds. The verb's own `--help` already assigns any further static work to a later `tabcomp` child, so a carrier here would file a second claim on work another Set's charter already owns.
- A RUNTIME CALLBACK FROM THE STATIC SCRIPT INTO `aw`. It would put interpreter startup (~220ms, measured elsewhere in this repo) on every TAB press and would break completion mid-upgrade. E-03 forbids it and V-03 greps for it.
  - Carrier-Declined: A PERMANENT DESIGN CONSTRAINT, not postponed work. The static script is self-contained BY CONTRACT (the module docstring states it), and this bullet records a route deliberately not taken rather than a task left undone. It is enforced going forward by a test (`BashCompletionDrivenTests.test_generated_script_makes_no_runtime_callback_into_aw`), so there is nothing for a carrier to revisit; filing one would assert that we intend to add the callback later, which is the opposite of the decision.
- THE DROP-IN LAYOUT, THE ALIAS SYMLINKS AND THE rc STANZA. The concurrent `compinert` Set owns those, including the consent rule for user-scoped writes that E-06's warn-only constraint inherits.
  - Carrier-Declined: OWNED BY ANOTHER SET that already exists, so a carrier would duplicate it. `compinert` (backlog `lalwnj`, `.aw/records/backlog/graduated/20260912-lalwnj-01-lalwnj-completion-install-inert-without-bash-completion.backlog.md`) holds this work and is live in the tree; this plan's exclusion is a fence, not an obligation it incurs. Naming `lalwnj` as a `- Carrier:` would misreport a Set boundary as a handoff from here.
- REWRITING AN INSTALLED COMPLETION FILE. The maintainer ruled warn-only on 2026-09-12 (OQ-01). `aw install` must not touch the user's completion directory at all, and V-06 proves the file was not modified.
  - Carrier-Declined: EXCLUDED BY THE GRANTING AUTHORITY, so there is no obligation to carry. The maintainer ruled warn-only and chose it over rewrite-on-upgrade explicitly; filing a carrier would assert an intention to rewrite the user's file later, which the ruling forbids. E-06 discharged the part that WAS asked for (detect and warn), and V-06 proves the file is untouched to the nanosecond.
- NARROWING `aw completion`'s POSITIONAL TO `choices` ON THIS PLAN'S OWN AUTHORITY. That is a public CLI contract change with a documented deliberate shape and a pinned shape test, so it was blocking OQ-02 rather than an assumed fix.
  - Carrier-Declined: DISCHARGED, not outstanding. This bullet excluded acting on the plan's OWN authority; the maintainer then granted the authority (OQ-02 answered (b) on 2026-09-12), E-08 performed the narrowing, and V-08 validated it with the before/after parser introspection and the pinned shape test updated rather than deleted. The exclusion is now historical record of why a human was asked first.
- ZSH AND FISH FALL-THROUGH REMOVAL, because there is nothing to remove: measured at review, neither generator emits an unconditional default (F-8). The choices half DID apply to both and was performed (E-03 extends all three generators, `_node_candidates` shared), so nothing remains here.
  - Carrier-Declined: NOTHING TO CARRY, measured rather than assumed. There was no zsh/fish fall-through to remove (verified at review: zsh's inner `case` has no default arm and every fish `complete` line is conditional), and the part that DID apply to them - emitting positional choices - was implemented in this plan, so both generators now consume the same `_node_candidates` helper as bash. An empty exclusion cannot have a carrier.

## Scope check

- Over-scope: none. Three paths: the completion module, the CLI where the tip and the parser live, and one test file.
- Under-scope, and TWO GAPS WERE FOUND AT REVIEW that the authored `none`-plus-prose did not name. FIRST, the plan addressed one of two completion surfaces: `complete_query` is never mentioned, and E-02/E-03 would break the parity its docstring declares. Now carried by E-05 and blocking OQ-03. SECOND, the spec-sync section required three docstring amendments that no `E-*` item carried, so they would have been dropped; now E-07.
- Under-scope, deliberately: this plan does not add dynamic completion of id6s, setids, statuses-from-disk or file paths, which the verb's own `--help` defers to a later `tabcomp` child. It does not change the drop-in layout, the alias symlinks or the rc stanza (the `compinert` Set owns those). It does not add a runtime callback into `aw`, which would put interpreter startup on every TAB press.
- A KNOWN LIMIT, STATED HONESTLY: E-05 warns an installed user that their script is stale, but the warning fires only when they next run `aw install` or `aw setup`. A user who never re-runs either keeps a stale vocabulary indefinitely. That is the accepted cost of the warn-only ruling and is not a defect in this plan.

## Required tests / validation

- FOUR UNCONDITIONAL DRIVEN CASES, executed rather than read: `aw find <TAB>` -> EMPTY; `aw install <TAB>` -> EMPTY (a second command from the 30, so the fix is not special-cased); `aw ipd <TAB>` -> its 9 subcommands unchanged; `aw migrate-layout <TAB>` -> its eight actions.
- TWO CONDITIONAL CASES, only if OQ-02 makes `aw completion` completable: `aw completion <TAB>` -> exactly `bash fish install uninstall zsh`; `aw completion in<TAB>` -> `install` with `index` explicitly ABSENT. Do not write these as failing tests under OQ-02 option (a).
- THE INVALID SUGGESTION PINNED where applicable: asserting `install` is present would pass against today's broken build (which returns `include index install`), so the absence of `index` is the load-bearing assertion.
- THE DRIVING TECHNIQUE, since it is what found the bug and no existing test uses it: write the generated script to a scratch file, `source` it in a subshell, set `COMP_WORDS`/`COMP_CWORD`, call `_aw_completion`, inspect `COMPREPLY`. Review did exactly this; text-level assertions cannot catch a fall-through because the script was always internally consistent.
- BOTH SURFACES COMPARED for every command E-03 touches, per OQ-03 (E-05/V-05).
- THE GENERATED SCRIPT STAYS STATIC: no runtime callback into `aw`.
- `python3 -m pytest` BARE, failure-SET delta empty. Review's baseline at HEAD `03e1436c`: `5971 passed, 3 skipped, 2 xfailed in 59.70s`, REFERENCE ONLY; re-measure before the first edit and judge on the failure SET, not the count.
- `aw sanitize --agent` clean.
- DO NOT MUTATE THE REAL USER COMPLETION FILE while testing E-06. Use `--dir` or a scratch `HOME`; that file is the maintainer's and is outside this plan's declared paths.

## Spec / documentation sync

No spec governs completion; the docstrings are the contract. THESE AMENDMENTS ARE NOW CARRIED BY E-07, which review added because the authored plan required them here and allocated no `E-*` item to perform them, so they would have been silently dropped.

`generate_bash_completion`'s docstring currently says the function "offers the top-level commands, then the nested subcommands of the first word, plus flags" - which is an accurate description of the DEFECT. Rewrite it to state that a command offers its own subcommands and positional choices, and that a command with neither offers nothing, so the docstring stops endorsing the fall-through.

`introspect_cli_tree`'s docstring must record that it captures positional `choices` as well as subparsers, and that an unconstrained positional deliberately contributes nothing.

A THIRD DOCSTRING IS AFFECTED AND THE PLAN MISSED IT: `completion.py`'s MODULE header states as a verified shape fact that "the CLI status arguments are free-form `nargs="+"` (NOT argparse `choices`...)". That stays true, but once the module reads positional choices the header should name which arguments DO carry them (`migrate-layout action`, `path root`) rather than leaving a reader to conclude nothing does.

A FOURTH IS CONDITIONAL ON OQ-03: `_subcommand_candidates`'s docstring asserts that `__complete` and the offline scripts "agree on the static layer". If OQ-03 permits them to differ, that sentence must be amended in the same change; if it requires them to agree, E-05 makes it true again. Either way it must not be left false.

## Open questions

### OQ-01: Should `aw install`/upgrade regenerate an installed completion script (F-5)?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: STATUS CORRECTED AT EXECUTION 2026-09-21: this block still read `Status: open` while its own body recorded the maintainer's answer and named E-06 as the carrier, which is a stale field rather than a live question. It is `resolved`: the answer is below, E-06 implemented it, and V-06 validated all three states with the file-untouched proof the warn-only ruling requires.
  ANSWERED BY THE MAINTAINER 2026-09-12: `aw install` should DETECT AND WARN, never silently rewrite. Verbatim: "`aw install` should check and warn 'run `aw completion install` if you want tab-completion for `aw`' or similar." So the installed script is never rewritten behind the user's back, and staleness stops being silent. That is a THIRD option better than the two this question originally framed (rewrite-on-upgrade vs. do-nothing), and it is consistent with the `compinert` ruling that user-scoped writes need consent: a warning asks, a rewrite assumes.
  IT ALSO GENERALIZES THE EXISTING HOOK RATHER THAN ADDING A NEW ONE. `_completion_tip` (`cli.py:5519`) already prints "Tip: Enable tab-completion with 'aw completion install'" when completion is ABSENT and returns silently when present, because `_completion_configured` composes `is_completion_installed`, which is a PRESENCE check only (`cli.py:5509-5514`). So the never-installed case is already handled and the STALE case is the gap: an installed-but-outdated script takes the silent branch. The fix is to widen that one predicate and add a second message, not to build a new surface.
  STALENESS IS TRIVIALLY DETECTABLE, MEASURED AT REVIEW: comparing the installed file's body (minus the injected sentinel line) against a fresh `generate_bash_completion()` returns True on a current install, so a byte comparison is sufficient and needs no version stamp. E-05 owns this.
  NOT BLOCKING, and now carried by an executable item rather than an open question.

### OQ-02: `aw completion`'s vocabulary is not in argparse `choices`, so the plan's mechanism cannot fix the reported case. How is it made completable?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: MEASURED BY SIMULATION, NOT PREDICTED, WHICH IS WHY IT IS BLOCKING. The plan's premise is that `completion` has "a fixed `bash|zsh|fish|install|uninstall` vocabulary" that `introspect_cli_tree` fails to see. VERIFIED AT REVIEW: it has no such vocabulary in the parser. `target` is declared `nargs="?"`, `default=None`, `choices=None`, with `metavar='bash|zsh|fish|install|uninstall'` (`cli.py:4727-4734`); the valid set is enforced by a runtime `if shell not in ("bash","zsh","fish")` in `_run_completion` (`cli.py:10466`). Running E-02's rule exactly as specified over that parser captures `[]`. So E-03's stated outcome is unreachable and E-04's two `completion` test cases would fail for a reason no amount of generator work fixes.
  THE SHAPE IS DELIBERATE, WHICH IS WHAT MAKES THIS THE MAINTAINER'S CALL. `cli.py:4735-4737` records the design: the `install`/`uninstall` verbs are "ADDITIVE on child 01's free-form `target` positional (see the shape note above) - `aw completion <shell>` output is unchanged". A free-form positional was chosen so a shell name and a verb could share one slot. Adding `choices` narrows a public CLI contract, and `tests/test_completion.py:206` (`test_parser_shape_allows_child03_extension`) exists specifically to pin that shape.
  THREE OPTIONS, EACH COSTED. (a) LEAVE `aw completion <TAB>` OFFERING NOTHING. Cost: the maintainer's exact reported command still offers no help, though it no longer offers a WRONG answer, which is the larger half of the bug. Benefit: zero contract change, zero risk, and E-01 alone already removes the misleading suggestion. (b) ADD `choices=[*SUPPORTED_SHELLS, "install", "uninstall"]` TO THE POSITIONAL. Cost: argparse then rejects an unknown target with its own usage error instead of the current hand-written message naming `aw completion --help`, so the error UX changes and `_run_completion`'s `if` becomes dead code; `test_parser_shape_allows_child03_extension` may need review. Benefit: one line, the vocabulary becomes machine-readable everywhere, and E-02's mechanism then genuinely reaches the reported case. (c) TEACH THE GENERATOR TO READ `metavar` WHEN IT LOOKS LIKE A PIPE-DELIMITED VOCABULARY. Cost: a heuristic on a HELP-TEXT field, which is exactly the "guessing" E-02 forbids in its own third paragraph, and it would silently break if anyone rewords a metavar. Benefit: no CLI contract change at all.
  RECOMMENDATION (b), because it converts a vocabulary that is already fixed in practice into one the tooling can see, and the cost is a bounded, visible change to one error message rather than a heuristic. (c) is the one to avoid: parsing help text is the same class of guess that produced this defect. If the maintainer prefers (a), that is entirely defensible and E-01 alone still resolves the reported harm; E-03/E-04 must then drop their `completion` claims, which they now do conditionally.
  DELIBERATELY NOT DONE HERE: review did not add `choices`, did not touch the parser, and did not change the pinned shape test. Narrowing a public CLI contract is the maintainer's decision.
  ANSWERED BY THE MAINTAINER 2026-09-12: ADD REAL `choices` TO THE POSITIONAL, then make BOTH surfaces emit it. Chosen over shipping E-01 alone and over parsing the `metavar`.
    THE REVIEW'S MEASUREMENT IS ACCEPTED AND RE-VERIFIED, and it means this plan's authored premise was FALSE. Re-run at the time of the ruling: the `completion` subparser's positional reports `choices=None` with `metavar='bash|zsh|fish|install|uninstall'`. So the vocabulary lives ONLY in a DISPLAY string, and E-02's "capture positional `choices`" could never have reached the case the maintainer reported. The plan asserted a fixed `choices` vocabulary that does not exist; that sentence must be corrected, not merely supplemented.
    SO THE FIX IS A DELIBERATE, BOUNDED CLI CONTRACT CHANGE, which is why it needed a human. `cli.py:4735-4737` records the current shape as intentional ("the `install`/`uninstall` verbs are ADDITIVE on child 01's free-form `target` positional"), and `tests/test_completion.py:206-214` PINS it: `test_parser_shape_allows_child03_extension` asserts `parse_args(["completion","install"])` succeeds and is "not constrained by `choices=`". Adding `choices` narrows a public surface, so:
    UPDATE THAT PINNED TEST RATHER THAN DELETING IT. Its intent (a future verb parses without a redesign) survives; what changes is that the verb must now be REGISTERED in `choices` to parse. Rewrite the assertion to that effect and say so in the test's comment, so a reader sees the constraint was tightened on purpose and not that the forward-compat guarantee was dropped.
    THE ERROR MESSAGE WILL CHANGE, and that is the visible cost the maintainer accepted: today an unknown target reaches the handler, which raises `unknown completion target 'index' (expected bash|zsh|fish|install|uninstall)`; with `choices` argparse rejects it at parse time with its own wording and exit code. VERIFY the new message is at least as clear, and if the handler's validation becomes dead code, remove it rather than leaving two validators that can disagree.
    KEEP THE VOCABULARY IN ONE PLACE. `SUPPORTED_SHELLS` already exists in `completion.py` and `--shell` already uses it as `choices`; derive the positional's `choices` from that plus the two verbs rather than writing a second literal list, or the `metavar` drift this defect is made of simply reappears one field over.

### OQ-03: The plan changes one of two completion surfaces and breaks their documented parity. Which surface owns positional choices?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: THE PLAN DOES NOT MENTION THE SECOND SURFACE AT ALL, which is why this needs an answer before E-03 lands. There are two: the STATIC generated script (what the maintainer's shell runs; verified that the installed file is the static generator's output with zero `__complete` references) and the DYNAMIC `complete_query` behind `aw __complete`. MEASURED: `complete_query` already returns `[]` for `aw completion <TAB>`, `aw find <TAB>` and `aw install <TAB>`, so it does NOT have the fall-through defect and needs no part of E-01.
  THE CONTRACT IS EXPLICIT IN THE CODE. `_subcommand_candidates`'s docstring: it "mirrors the generated static scripts so `__complete` and the offline scripts agree on the static layer." E-02/E-03 would have the static script offer `migrate-layout`'s eight actions while the dynamic engine offers nothing there, so the two disagree and that sentence becomes false. Neither the plan nor its Scope acknowledges this.
  THREE OPTIONS. (a) SHARE THE CAPTURE: `_subcommand_candidates` consumes the same key E-02 writes, so both surfaces gain choices together. Cost: `complete_query` runs inside a <50ms budget the module docstring records, and it already builds the parser for the static layer, so the marginal cost is a dict lookup rather than a new scan; small but must be measured. Benefit: parity preserved, one behavior to reason about. (b) STATIC ONLY, AND AMEND THE DOCSTRING to say the surfaces deliberately differ on positional choices. Cost: two behaviors a user can hit depending on whether argcomplete is active, which is the kind of divergence that produces "it works in my other shell" reports. Benefit: smallest change. (c) DECIDE THE DYNAMIC ENGINE SHOULD OWN CHOICES and have the static script defer, which it cannot do without a runtime callback E-03 correctly forbids. Cost: contradicts the static-and-self-contained contract. Benefit: none identified.
  RECOMMENDATION (a), because the parity sentence is load-bearing (it is why a user gets the same answer with and without argcomplete) and the marginal cost is a lookup on a parser the function already builds. (c) is not viable. E-05 now carries whichever answer is chosen and requires the docstring amended if the answer is (b).
  DELIBERATELY NOT DONE HERE: review did not modify `complete_query` or the parity docstring, because choosing between one behavior and two is a design call with a user-visible consequence.
  ANSWERED BY THE MAINTAINER 2026-09-12 AS PART OF THE SAME RULING: FIX BOTH SURFACES, preserving the parity contract rather than falsifying it.
    THE REVIEW IS RIGHT THAT THIS PLAN NEVER MENTIONED THE SECOND SURFACE, and that is an authoring failure rather than a scope choice: I checked the static generator only. Verified at the ruling: `complete_query` (`completion.py:625`) is a second, DYNAMIC engine behind `aw __complete`, and `_subcommand_candidates`'s docstring (`:593-596`) states it "mirrors the generated static scripts so `__complete` and the offline scripts agree on the static layer". That is an explicit parity contract in the same file this plan edits.
    MEASURED CONSEQUENCE OF THE AUTHORED PLAN, which is what makes this blocking rather than tidy: `complete_query(['aw','completion',''],2)` returns `[]` today, so had E-02/E-03 taught only the static generator, the static script would have offered the five targets while the dynamic engine offered nothing for the same keystroke. The contract would have been false, in the file that documents it, as a side effect of a change that never named it.
    SO EVERY ITEM THAT TEACHES THE STATIC LAYER MUST TEACH BOTH. Positional `choices` are part of the STATIC layer by the contract's own definition (they are fixed vocabulary, not repository state), so they belong in the mirrored path, NOT in the dynamic-only layers that resolve id6s and Set ids from disk.
    ADD A PARITY TEST, which is the durable half. Nothing today asserts the two surfaces agree, which is precisely why this plan could have broken the contract silently. Assert that for the same word list, the static script's `COMPREPLY` and `complete_query`'s return AGREE on the static layer, and include `aw completion <TAB>` as a case. Without it the next change reintroduces the divergence.
    DO NOT COLLAPSE THE TWO SURFACES. That is not authorized here: they exist for different reasons (an offline script with no interpreter cost, and a live engine that reads repository state), and the docstring asks them to AGREE on the static layer, not to become one code path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the generator diff showing the post-`esac` fallback removed, and paste the DRIVEN result for `aw find <TAB>` AND `aw install <TAB>` each showing an EMPTY `COMPREPLY` (item count 0). Quoting the diff alone is insufficient: the bug was invisible in the script text and only appeared when the function was executed. Review's pre-fix baseline, for comparison: both returned 47 items.
  - Observed evidence: THE GENERATOR DIFF, `agent_workflows/completion.py` (`git diff`):

    ```diff
    @@ -230,7 +297,8 @@ def generate_bash_completion(tree: Dict[str, Any] | None = None) -> str:
             "    esac",
    -        f'    COMPREPLY=( $(compgen -W {shlex.quote(top_names)} -- "$cur") )',
    +        # compargs 4y95tp E-01: NO default arm and NO post-`esac` fallback. A command with no arm
    +        # leaves COMPREPLY empty, which is bash's signal to use its own default completion.
             "    return 0",
    ```

    THE EMITTED SCRIPT, before and after the `esac`, generated from each tree:

    ```text
    BEFORE (HEAD f763be8c):
      68:    esac
      69-    COMPREPLY=( $(compgen -W 'adopt agy archive backlog check check-local-leaks commit completion config context doctor exclude find finish group host include index install ipd layout list-repos migrate-layout next normalize-lanes oc path project prompts pwatch record-history releases rename research reviews run runs search set setup show specs status storage test uninstall work workflow' -- "$cur") )
      70-    return 0
    AFTER:
      77:    esac
      78-    return 0
    ```

    THE DRIVEN RESULT, which is the load-bearing half (script written to a scratch file, `source`d in a subshell, `COMP_WORDS`/`COMP_CWORD` set, `_aw_completion` called, `COMPREPLY` printed):

    ```text
    -- aw find <TAB>
    count=0

    -- aw install <TAB>
    count=0
    ```

    PRE-FIX BASELINE re-measured in this lane at HEAD `f763be8c` by the same driver, confirming review's number to within the one command added since (48, not 47):

    ```text
    --- aw find <TAB>
    count=48
    adopt
    agy
    archive
    --- aw install <TAB>
    count=48
    adopt
    agy
    archive
    --- aw completion in<TAB>
    count=3
    include
    index
    install
    ```

    THE COUNT IS 48 AND NOT 47, which is worth stating rather than quietly normalizing: the top-level command population grew by one since review measured it. Re-computed from the parser at execution: 48 top-level commands, 17 with subparsers, 3 with a choices-bearing positional, so 28 now correctly offer NOTHING (review predicted 28 from a 47-command population; the added command has subparsers or choices, so the silent set did not grow). The DEFECT and its shape are identical; only the census moved, exactly as the plan's F-9 anticipated.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the parser walk enumerating every command with a choices-bearing positional, and confirm it is the TWO measured at review (`migrate-layout action`, `path root`) or state what changed. Paste `introspect_cli_tree(...)` for `migrate-layout` BEFORE and AFTER, showing the choices captured under their own key and NOT merged into `subcommands`. Paste `introspect_cli_tree(...)['subcommands']['completion']` showing it captures NOTHING, which is the honest result under OQ-02 option (a) and the proof that PR-001 is real. Paste one unconstrained-positional command showing it contributes nothing.
  - Observed evidence: THE PARSER WALK at HEAD `f763be8c`, BEFORE any edit, recursing the real parser for positionals carrying `choices`:

    ```text
    ('path', 'root', ['config', 'records', 'state', 'system'])
    ('migrate-layout', 'action', ['apply', 'cleanup', 'inventory', 'plan', 'resume', 'rollback', 'status', 'wizard'])
    ```

    CONFIRMED: exactly the TWO review measured, unchanged. The plan's authored "several verbs" remains FALSE, and its correction stands.

    `introspect_cli_tree` for `migrate-layout`, BEFORE (module loaded from `git show HEAD:agent_workflows/completion.py`) and AFTER:

    ```text
    BEFORE migrate-layout keys: ['flags', 'subcommands'] subcommands: {}
    BEFORE has 'choices' key: False
    AFTER  migrate-layout keys: ['choices', 'flags', 'subcommands']
    AFTER  choices: ['apply', 'cleanup', 'inventory', 'plan', 'resume', 'rollback', 'status', 'wizard']
    AFTER  subcommands (NOT merged): {}
    ```

    NOT MERGED is the structural half and is visible above: the eight actions land under `choices` while `subcommands` stays `{}`, so no generator can emit a third `case` level for a token that cannot have one, and `_all_command_paths` does not start reporting `migrate-layout apply` as a command path. Pinned by `PositionalChoicesIntrospectionTests.test_choices_are_captured_under_their_own_key_not_merged`.

    THE UNCONSTRAINED POSITIONAL CONTRIBUTES NOTHING, `aw find` (a free-form pattern):

    ```text
    AFTER find (unconstrained positional) choices: [] subcommands: {}
    ```

    `introspect_cli_tree(...)['subcommands']['completion']` NOW CAPTURES ITS VOCABULARY, and this is the one place the required evidence had to be inverted rather than pasted:

    ```text
    AFTER completion node choices: ['bash', 'fish', 'install', 'uninstall', 'zsh'] subcommands: {}
    ```

    WHY THE REQUIRED "CAPTURES NOTHING" EVIDENCE IS NOT WHAT I PASTED. This V-item was written when OQ-02 was OPEN, so it demanded the empty capture as proof that PR-001 was real under option (a). The maintainer then answered (b) - add real `choices` - which E-08 performed. PR-001 IS STILL PROVEN, by the BEFORE measurement rather than the AFTER one: at HEAD the walk above does NOT list `completion`, because its positional reported `choices=None` with the vocabulary living only in the `metavar` display string, so E-02's mechanism alone captured `[]` for it exactly as review simulated. The AFTER value is non-empty only because E-08 changed the PARSER, which is the maintainer's chosen route and not E-02 reaching further than it can.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the DRIVEN result for `aw migrate-layout <TAB>` showing its eight actions and `aw path <TAB>` showing its four roots. Paste OQ-03's recorded answer, since E-03 may not land before it is answered. Confirm by grep that the generated script contains no runtime callback into `aw` (it must stay static and self-contained). Do NOT assert anything about `aw completion <TAB>` unless OQ-02 was answered (b) or (c); if it was, paste that too.
  - Observed evidence: THE DRIVEN RESULTS, both choices-bearing commands, from the real generated script:

    ```text
    --- aw migrate-layout <TAB>
    count=8
    apply
    cleanup
    inventory
    plan
    resume
    rollback
    status
    wizard
    --- aw path <TAB>
    count=4
    config
    records
    state
    system
    ```

    OQ-03's RECORDED ANSWER, quoted from this plan's own Open questions section: "ANSWERED BY THE MAINTAINER 2026-09-12 AS PART OF THE SAME RULING: FIX BOTH SURFACES, preserving the parity contract rather than falsifying it." Option (a), SHARE THE CAPTURE. E-05/V-05 carry the dynamic side; this item was therefore free to land.

    OQ-02 WAS ANSWERED (b), so `aw completion <TAB>` is in scope and is pasted. This is the maintainer's reported command, working:

    ```text
    --- aw completion <TAB>
    count=5
    bash
    fish
    install
    uninstall
    zsh
    ```

    NO RUNTIME CALLBACK, grepped over the generated script for every callback shape:

    ```text
    $ grep -n "aw __complete\|__complete\|\$(aw \|\`aw " after-aw.bash
    1:# bash completion for aw (agent-workflows). Generated by `aw completion bash`.
    ```

    The single hit is the header COMMENT naming the command that generated the file, not an invocation. The script body contains no `__complete`, no `$(aw ...)` and no backtick-`aw`, so completion still costs zero interpreter startups per TAB and keeps working while the tool is mid-upgrade. Pinned as a test by `BashCompletionDrivenTests.test_generated_script_makes_no_runtime_callback_into_aw`, which strips comment lines before asserting so the header cannot mask a real callback.

    THE BOTH-KINDS MERGE PATH EXISTS AND IS LATENT, stated rather than implied: `_node_candidates` unions `subcommands` with `choices`, but measured at execution NO command has both (the three choices-bearing commands have no subparsers), so that union is untested against a real both-kinds command. It is written because the alternative is a silent wrong answer the day one appears.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste all FOUR unconditional driven cases with their actual `COMPREPLY` contents: `aw find <TAB>` empty, `aw install <TAB>` empty, `aw ipd <TAB>` still returning its 9 subcommands, `aw migrate-layout <TAB>` returning its eight actions. THEN either paste the two conditional `completion` cases with `index` explicitly asserted ABSENT, or paste OQ-02's answer and the test-file comment recording that `aw completion <TAB>` deliberately offers nothing. THEN paste the BARE `python3 -m pytest` summary and the failure-SET delta (criterion: empty). Review's baseline at HEAD `03e1436c`: `5971 passed, 3 skipped, 2 xfailed in 59.70s`, reference only.
  - Observed evidence: THE FOUR UNCONDITIONAL DRIVEN CASES, actual `COMPREPLY` contents:

    ```text
    --- aw find <TAB>
    count=0

    --- aw install <TAB>
    count=0

    --- aw ipd <TAB>
    count=10
    begin
    board
    dependencies
    execute-set
    finalize
    lint
    recheck-readiness
    scaffold
    set
    sync
    --- aw migrate-layout <TAB>
    count=8
    apply
    cleanup
    inventory
    plan
    resume
    rollback
    status
    wizard
    ```

    `aw ipd` RETURNS 10, NOT THE 9 THIS ITEM PREDICTED, and that is a population change rather than a defect: an `ipd` leaf was added since review measured. The claim this case carries is that the WORKING HALF still works, and it does - the count matches the parser exactly. The test asserts against the parser-derived list rather than a hardcoded 9, so adding another leaf will not turn this red for no reason.

    THE TWO CONDITIONAL CASES APPLY, because OQ-02 was answered (b) ("ADD REAL `choices` TO THE POSITIONAL, then make BOTH surfaces emit it"), so E-08 made `aw completion` completable and no not-applicable comment was written. Both are driven:

    ```text
    --- aw completion <TAB>
    count=5
    bash
    fish
    install
    uninstall
    zsh
    --- aw completion in<TAB>
    count=1
    install
    ```

    THE INVALID SUGGESTION IS PINNED, which was the load-bearing requirement: `index` is ABSENT from `aw completion in<TAB>`, whereas the pre-fix baseline in V-01 returned `include index install`. The test asserts the full expected list by equality, so a returning `index` fails; its row comment records that a test merely checking `install` is present would have PASSED against the broken build.

    THE BARE SUITE, run as `python3 -m pytest` with no added flags:

    ```text
    8035 passed, 3 skipped, 2 xfailed, 3 warnings in 178.45s (0:02:58)
    ```

    FAILURE-SET DELTA: EMPTY. Baseline measured in this lane at HEAD `f763be8c` before any edit: `1 failed, 8022 passed, 3 skipped, 2 xfailed in 403.15s`, the single failure being `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`. THAT FAILURE IS ENVIRONMENTAL AND NOT A BASELINE DEFECT, diagnosed rather than assumed: the test asserts a NON-isolated turn carries no `OPENCODE_CONFIG_CONTENT` denial policy, and this lane's own agent turn exports that variable, which the test's subprocess inherits. Proven by re-running the same test with the variable cleared and nothing else changed:

    ```text
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped -o addopts=""
    1 passed in 0.57s
    ```

    Both the baseline and the post-change full runs are therefore compared with that variable cleared, giving `{}` failures before and `{}` after. The count rose by 13 (8022 -> 8035), which is the 13 tests this plan adds; review's `5971` at HEAD `03e1436c` is reference only and the tree has grown since.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste OQ-03's recorded answer and which option it selected. THEN paste, for every command E-03 touched, the candidates from BOTH surfaces side by side: the driven `COMPREPLY` from the generated script, and `complete_query(words, cword)` for the same position, showing they AGREE. If OQ-03 chose option (b), paste the amended `_subcommand_candidates` docstring instead, showing it no longer claims a parity the code does not keep. A run that changes the static side and shows no dynamic-side evidence either way is a FAILED validation.
  - Observed evidence: OQ-03's RECORDED ANSWER, quoted verbatim from this plan: "ANSWERED BY THE MAINTAINER 2026-09-12 AS PART OF THE SAME RULING: FIX BOTH SURFACES, preserving the parity contract rather than falsifying it." That selects OPTION (a), SHARE THE CAPTURE. Option (b) (static-only plus an amended docstring) is CLOSED, so no docstring amendment licensing a difference was written, and E-05's own text records the closure.

    BOTH SURFACES SIDE BY SIDE, measured for every command E-03 touched plus the controls:

    ```text
    position                     STATIC (COMPREPLY)                                DYNAMIC (complete_query)   AGREE
    aw completion <TAB>          ['bash','fish','install','uninstall','zsh']       (identical)                True
    aw migrate-layout <TAB>      ['apply','cleanup','inventory','plan',            (identical)                True
                                  'resume','rollback','status','wizard']
    aw path <TAB>                ['config','records','state','system']             (identical)                True
    aw ipd <TAB>                 ['begin','board','dependencies','execute-set',    (identical)                True
                                  'finalize','lint','recheck-readiness',
                                  'scaffold','set','sync']
    aw find <TAB>                []                                                []                         True
    aw install <TAB>             []                                                []                         True
    ```

    The `AGREE` column is a set comparison of the DRIVEN `COMPREPLY` against `complete_query(words, 2)`, not a visual reading. The two commands E-03 touched (`migrate-layout`, `path`) plus the E-08 case (`completion`) agree; `ipd` shows the subcommand half still agrees; the two empty rows show the surfaces already agreed where neither has a vocabulary.

    PARITY IS STRUCTURAL, NOT COINCIDENTAL, which is why this passes rather than happening to pass. `_subcommand_candidates` now returns `_node_candidates(node)` - the SAME helper the three generators call - so both surfaces read the same `introspect_cli_tree` keys through one code path and cannot drift by discipline alone. The amended docstring records why:

    ```text
    THE CHOICES HALF IS WHY THAT PARITY SENTENCE IS STILL TRUE (compargs 4y95tp E-05). When the static
    generators learned to emit positional ``choices``, this function had to learn it in the same
    change: otherwise ``aw migrate-layout <TAB>`` would offer eight actions through an offline script
    and nothing through ``aw __complete``, and the two surfaces would disagree in the file that
    documents their agreement. [...] Both surfaces read the SAME ``introspect_cli_tree`` key through
    the SAME ``_node_candidates`` helper, so they cannot drift by construction rather than by
    discipline.
    ```

    THE DURABLE HALF IS THE NEW PARITY TEST, which nothing provided before: `CompletionSurfaceParityTests.test_both_surfaces_return_the_same_static_candidates` drives the generated script and calls `complete_query` for the same five positions and asserts set equality, with `aw completion <TAB>` as an explicit case. Its failure message names the closed option so a future agent does not resolve a divergence by amending the docstring.

    THE LATENCY BUDGET IS UNAFFECTED, checked because `complete_query` carries a documented <50ms budget and E-05 adds work to it. Measured over 5 runs of the worst new case (`aw migrate-layout <TAB>`), HEAD module vs. changed module in one process: BEFORE `min 42.1ms median 43.8ms`, AFTER `min 40.0ms median 43.3ms`. The marginal cost is a dict lookup on a parser the function already builds, exactly as OQ-03's option (a) predicted; the ~43ms is the pre-existing parser build, not this change.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the parser introspection BEFORE and AFTER, showing `choices=None` becoming the real list, and confirm by quotation that the list is DERIVED from `completion.SUPPORTED_SHELLS` rather than hand-written (a second literal list is a FAILED validation, since that is the same drift this defect is made of). Paste the updated `test_parser_shape_allows_child03_extension` with its diff and its amended comment, and state explicitly that the forward-compat intent is preserved. Paste the amended `cli.py:4735-4737` shape comment. Paste the ACTUAL argparse error for `aw completion index` before and after, and either show the handler's validation removed or explain why it is still reachable. THEN paste the DRIVEN `aw completion <TAB>` result showing the five targets, which is the maintainer's reported command finally working.
  - Observed evidence: THE PARSER INTROSPECTION, BEFORE (HEAD `f763be8c`) and AFTER:

    ```text
    BEFORE  completion positional: target nargs= ? choices= None metavar= bash|zsh|fish|install|uninstall
    AFTER   completion positional: target nargs= ? choices= ['bash','zsh','fish','install','uninstall']
                                          metavar= bash|zsh|fish|install|uninstall
    ```

    The BEFORE line is the proof of PR-001 that this plan's authored premise denied: the vocabulary existed ONLY as the `metavar` display string.

    THE LIST IS DERIVED, NOT A SECOND LITERAL, quoted from `agent_workflows/cli.py`:

    ```python
    _COMPLETION_VERBS = ("install", "uninstall")
    _completion_targets = [*completion_mod.SUPPORTED_SHELLS, *_COMPLETION_VERBS]
    ...
        choices=_completion_targets,
        metavar="|".join(_completion_targets),
    ```

    The shell names come from `completion.SUPPORTED_SHELLS` (the same constant `--shell` already uses as its `choices`), and the METAVAR IS NOW DERIVED TOO, which the item did not require but which closes the drift one field over: the display string can no longer disagree with the enforced set, because it is built from it. A hand-written third copy would have been the exact failure this item warns about.

    THE PINNED SHAPE TEST WAS UPDATED, NOT DELETED, and its forward-compat INTENT IS PRESERVED. The diff of `tests/test_completion.py::test_parser_shape_allows_child03_extension`:

    ```diff
    -        """Kept separate: asserts the ABSENCE of an argparse `choices=` constraint (forward-compat),
    -        not a value mapping."""
    -        # Forward-compat: `target` is a free-form optional positional (no fixed choices), so a future
    -        # `aw completion install`/`uninstall` token parses without a redesign. [...]
    +        """Kept separate: asserts the VERB-EXTENSION property of the `target` positional, not a
    +        value mapping.
    +
    +        THE CONSTRAINT WAS TIGHTENED ON PURPOSE (compargs 4y95tp E-08, maintainer ruling 2026-09-12),
    +        so read this test's change as a narrowing and NOT as the forward-compat guarantee being
    +        dropped. [...]
    +        WHAT STILL HOLDS is the property this test was written for: a non-shell VERB shares the
    +        shell-name slot, so `aw completion install` parses without reshaping the parser. What changed
    +        is that such a verb must now be REGISTERED in the positional's `choices` (one line) instead
    +        of being silently accepted at parse time and refused in the handler. Adding a future verb is
    +        therefore still additive; it is just no longer silent.
    +        """
             parser = cli._build_parser()
             args = parser.parse_args(["completion", "install"])
             self.assertEqual(args.command, "completion")
    -        self.assertEqual(args.target, "install")  # not constrained by choices=
    +        # A VERB, not a shell name, still occupies the same positional (the forward-compat property).
    +        self.assertEqual(args.target, "install")
    +        [... asserts the choices set is SUPPORTED_SHELLS + the two verbs, that each shell is
    +         present, and that an unregistered token now raises SystemExit at parse time ...]
    ```

    STATED EXPLICITLY, as the item demands: the forward-compat intent is PRESERVED. The property the test was written to defend - a non-shell verb can occupy the shell-name slot without reshaping the parser - is still asserted by the surviving `parse_args(["completion","install"])` assertion. What the test no longer claims is the ABSENCE of `choices`, because that absence was the mechanism, not the goal, and it was the mechanism that hid the vocabulary from every tool. The docstring says the constraint was tightened deliberately so a later reader does not "restore" the free-form shape.

    THE `cli.py` SHAPE COMMENT WAS AMENDED in the same change (relocated by edits; find it by the `p_completion` parser construction rather than by the authored line numbers):

    ```python
    # PARSER SHAPE, NARROWED ON PURPOSE (compargs 4y95tp E-08, maintainer ruling 2026-09-12). `target`
    # WAS a free-form positional with `choices=None`, whose vocabulary existed only as the `metavar`
    # DISPLAY string and was enforced by a runtime `if` in `_run_completion`. That shape was chosen so
    # tabcomp-03's `install`/`uninstall` verbs could be ADDITIVE on a shell-name slot, but it made the
    # vocabulary invisible to every tool [...] A future verb is still additive - it just has to be
    # REGISTERED in this list (one line) rather than silently accepted at parse time and rejected in the
    # handler.
    ```

    THE ACTUAL ERROR FOR `aw completion index`, BEFORE and AFTER. BEFORE was measured by running HEAD's `cli.py`/`completion.py` from a scratch copy of the package, not by quoting the source:

    ```text
    BEFORE (HEAD f763be8c):
    agent-workflows: error: unknown completion target 'index' (expected bash|zsh|fish|install|uninstall).
    Next  aw completion --help
    rc=2

    AFTER:
    usage: agent-workflows completion [-h] [--no-color | --color] [--agent]
                                      [--json] [--shell {bash,zsh,fish}]
                                      [--dir COMPLETION_DIR] [--dry-run]
                                      [bash|zsh|fish|install|uninstall]
    agent-workflows completion: error: argument bash|zsh|fish|install|uninstall: invalid choice: 'index' (choose from 'bash', 'zsh', 'fish', 'install', 'uninstall')
    Next  aw completion --help
    rc=2
    ```

    THE NEW MESSAGE IS AT LEAST AS CLEAR, judged rather than asserted: it names the offending token (`'index'`), enumerates every valid value, prints the usage line showing the slot, keeps the same exit code 2, and still routes to `aw completion --help`. It is LONGER than the handwritten one, which is the visible cost the maintainer accepted.

    THE HANDLER'S VALIDATION WAS REMOVED rather than orphaned, because `choices` made it unreachable and two validators for one vocabulary can disagree:

    ```diff
    -    shell = target if target else _detect_shell()
    -    if shell not in ("bash", "zsh", "fish"):
    -        print(
    -            f"agent-workflows: error: unknown completion target {shell!r} "
    -            "(expected bash|zsh|fish|install|uninstall).",
    -            file=sys.stderr,
    -        )
    -        print("Next  aw completion --help", file=sys.stderr)
    -        return 2
    +    shell = target if target else _detect_shell()
         sys.stdout.write(_completion.generate(shell))
    ```

    UNREACHABILITY IS ARGUED, not assumed: `target` can now only be one of the five registered values or `None`; `install`/`uninstall` return earlier; and `_detect_shell` returns only `bash`/`zsh`/`fish` (it falls back to `bash` for anything unrecognized, per its own table-driven test). So every value reaching `generate` is valid by construction. `grep` confirms the removed string has no other definition or test asserting it: the only remaining hit for "unknown completion target" is the prose in this plan's own record.

    THE DRIVEN `aw completion <TAB>`, the maintainer's reported command finally working:

    ```text
    --- aw completion <TAB>
    count=5
    bash
    fish
    install
    uninstall
    zsh
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste all THREE states from real runs. ABSENT: no installed file, output shows today's enable-tip. CURRENT: a freshly installed file, output shows NEITHER tip nor warning. STALE: mutate the installed file (or generate against a tree with an extra command), output shows the warning naming `aw completion install`. THEN paste `git status`/`ls -l --time-style=full-iso` on the completion directory before and after the stale run, proving the file was NOT rewritten or touched; a modified file is a FAILED validation regardless of the warning being correct. Finally, paste a multi-repo `aw install` showing the warning appears ONCE, not per repo. USE A `--dir` OVERRIDE OR A SCRATCH HOME rather than mutating the real user completion file, which is the maintainer's own and outside this plan's scope.
  - Observed evidence: ALL THREE STATES from real runs against a SCRATCH `HOME` + `XDG_DATA_HOME` (the real user file was never touched; proof at the end of this item):

    ```text
    ### ABSENT
    dir listing: (no directory)
    state: absent
    output:
    OK       Tip: Enable tab-completion with 'aw completion install'

    ### CURRENT
    state: current
    output: ''

    ### STALE
    state: stale
    output:
    WARN     Your installed aw tab-completion is OUTDATED (it was generated by an older version). Run 'aw completion install' to refresh it.
    ```

    ABSENT keeps TODAY'S tip verbatim (the never-installed case was already covered and is unchanged). CURRENT is exactly empty, which matters: a warning on every `aw install` for a good file would train the user to ignore it. STALE names `aw completion install` explicitly and says OUTDATED rather than broken, because the stale script still completes every command whose name did not change.

    THE FILE WAS NOT REWRITTEN OR TOUCHED, `ls -l --time-style=full-iso` before and after the stale run:

    ```text
    ### STALE -- BEFORE the warn run:
    total 8
    lrwxrwxrwx 1 ... 2 2026-09-21 23:02:14.859277639 -0400 agentwf -> aw
    lrwxrwxrwx 1 ... 2 2026-09-21 23:02:14.859277639 -0400 agent-workflows -> aw
    -rw-r--r-- 1 ... 5626 2026-09-21 23:02:14.947277165 -0400 aw

    ### STALE -- AFTER the warn run:
    total 8
    lrwxrwxrwx 1 ... 2 2026-09-21 23:02:14.859277639 -0400 agentwf -> aw
    lrwxrwxrwx 1 ... 2 2026-09-21 23:02:14.859277639 -0400 agent-workflows -> aw
    -rw-r--r-- 1 ... 5626 2026-09-21 23:02:14.947277165 -0400 aw
    ```

    Identical to the NANOSECOND on mtime and identical in size, for the primary file and both alias links. The warn path reads and prints; it opens nothing for writing. Pinned as a test by `StaleCompletionWarningTests.test_the_stale_warning_does_not_touch_the_users_file`, which compares bytes AND `(st_mtime_ns, st_size)` so a rewrite with identical content still fails.

    THE WARNING APPEARS ONCE FOR A MULTI-REPO RUN, not per repo:

    ```text
    OK       r1: installed
    OK       r2: installed

    WARN     Your installed aw tab-completion is OUTDATED (it was generated by an older version). Run 'aw completion install' to refresh it.

    OUTDATED warning occurrences: 1 (must be 1 for a 2-repo batch)
    ```

    THE ONCE-PER-INVOCATION PROPERTY IS INHERITED, NOT BUILT, which is why the simulation above is legitimate evidence rather than a reconstruction: `_completion_tip` is called from exactly THREE sites in `cli.py` (single-repo install, batch install, setup), each at function-body indentation OUTSIDE the per-repo loop. Re-verified at execution:

    ```text
    $ grep -n "_completion_tip(term)" agent_workflows/cli.py
    6291:    _completion_tip(term)
    6359:    _completion_tip(term)
    7682:    _completion_tip(term)
    ```

    E-06 widened the predicate those sites already call, so it could not introduce a per-repo repetition. `StaleCompletionWarningTests.test_the_tip_is_emitted_once_per_invocation_not_once_per_repo` pins both the count and the indentation, so moving a call into a loop fails.

    SHELL SCOPING, checked because a stale zsh file must not nag a bash user: with a stale zsh install AND a current bash install present, a `$SHELL=/bin/bash` invocation prints NOTHING (`test_the_warning_is_scoped_to_the_detected_shell`). A FOREIGN file (someone else's `aw` completion, no sentinel) classifies as `absent`, not `stale`, so we never claim a file we did not write is outdated and never point the user at a command that would refuse to clobber it (`test_a_foreign_file_is_absent_not_stale`).

    THE REAL USER COMPLETION FILE WAS NEVER MUTATED, as the item and the execution gate both require. Every run above used a scratch `HOME`/`XDG_DATA_HOME` under `.aw/state/`, and the tests use `_DropInFixture`'s temp dirs. Confirmed after all testing:

    ```text
    $ stat -c '%y %s %n' ~/.local/share/bash-completion/completions/aw
    2026-09-12 15:41:55.532936041 -0400 5259 $HOME/.local/share/bash-completion/completions/aw
    ```

    mtime 2026-09-12, which predates this lane's turn entirely.

    A KNOWN LIMIT, RESTATED HONESTLY because the fix does not remove it: the warning fires only when the user next runs `aw install` or `aw setup`. A user who runs neither keeps a stale vocabulary indefinitely. That is the accepted cost of the warn-only ruling, is already recorded in this plan's Scope check, and is not a defect in this implementation.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste all three amended docstrings. For `generate_bash_completion`, show the old sentence describing the fall-through is GONE, quoting the removed text so the correction is checkable. For `introspect_cli_tree`, show it records the choices capture and the deliberate silence on unconstrained positionals. For the module header, show the two choices-bearing commands named and the free-form-status statement still accurate.
  - Observed evidence: All three read back from the LOADED module (`completion.__doc__`, `.introspect_cli_tree.__doc__`, `.generate_bash_completion.__doc__`), not from the source file, so what is pasted is what a reader gets.

    1. `generate_bash_completion`. THE REMOVED SENTENCE, quoted so the correction is checkable, was an accurate description of the DEFECT:

    ```text
    REMOVED: "Emits a single ``_aw_completion`` function that offers the top-level commands, then the
              nested subcommands of the first word, plus flags when the current word starts with ``-``."
    ```

    It is GONE. The current docstring:

    ```text
    Emit a self-contained Bash completion script binding all three entrypoints (bja8og E-02).

    Emits a single ``_aw_completion`` function that offers the top-level commands in the command
    slot, then, in the slot after a command, THAT COMMAND'S OWN arguments: its nested subcommands and
    the fixed ``choices`` vocabulary of its first positional. A command with NEITHER offers NOTHING,
    so bash falls back to its own default (filenames) instead of proposing a token that cannot be
    valid there. Flags are offered when the current word starts with ``-``. Every command, choice and
    flag token is ``shlex.quote``d before being placed in the completion word list.

    THE FALL-THROUGH IS GONE ON PURPOSE (compargs 4y95tp E-01). This function used to end its `case`
    with an unconditional top-level ``COMPREPLY=``, so any command without a `case` arm (31 of 48 when
    the fix landed) suggested the whole command list: ``aw completion in<TAB>`` offered ``index``, which
    the verb then rejected. Do not reintroduce a default arm; an empty ``COMPREPLY`` is the correct
    answer when the parser declares no vocabulary for the position.
    ```

    The old sentence did not merely describe the fall-through neutrally; it ENDORSED it as the design, which is why replacing it matters more than adding a note beside it.

    2. `introspect_cli_tree`, recording the capture AND the deliberate silence:

    ```text
    Returns ``{"flags": [...], "subcommands": {name: <same shape>}, "choices": [...]}`` without
    mutating the parser. [...]

    ``choices`` (compargs 4y95tp E-02) carries the fixed vocabulary of the node's FIRST user-facing
    positional, captured under its OWN key rather than merged into ``subcommands``: choice tokens are
    not subcommands (they do not nest and carry no flags of their own), so conflating them would make
    a generator emit a third level for something that cannot have one. An unconstrained positional
    deliberately contributes NOTHING, because a positional with no ``choices`` declares no vocabulary
    and guessing one is the defect class this key exists to end.
    ```

    3. THE MODULE HEADER, which the plan originally missed. Both statements the item asks about:

    ```text
    [...] ``introspect_cli_tree`` walks the argparse action tree of the real CLI parser into a plain
    dict (subcommands + flags + positional ``choices``) [...] A command offers its OWN arguments in the
    slot after its name, and a command that declares none offers NOTHING (compargs 4y95tp) [...]

    [...] the CLI status arguments are free-form ``nargs="+"`` (NOT argparse ``choices``, so the status
    vocabularies come from ``ipd_schema``/``attention_contract``/``backlog``). THAT STATUS FACT IS STILL
    TRUE, and is narrower than it reads now that this module DOES read positional ``choices`` (compargs
    4y95tp): exactly three positionals carry them - ``migrate-layout action``, ``path root``, and
    ``completion target`` (given real ``choices`` by 4y95tp E-08 so the reported ``aw completion <TAB>``
    case became completable at all). Statuses are not among them.
    ```

    THE FREE-FORM STATUS STATEMENT IS STILL ACCURATE and is explicitly reaffirmed rather than deleted: the CLI status arguments remain `nargs="+"` with no `choices`, so `status_candidates` still sources its vocabularies from `ipd_schema`/`attention_contract`/`backlog`. What was misleading was leaving that as the module's only word on `choices`, which invited a reader to conclude NOTHING carries them.

    THREE COMMANDS ARE NAMED, NOT THE TWO THE ITEM ANTICIPATED. `completion target` joins `migrate-layout action` and `path root` because E-08 gave it real `choices`; the item was written when OQ-02 was open and option (a) (leave it free-form) was still live. Naming only two would now be false. Pinned by `PositionalChoicesIntrospectionTests.test_the_set_of_choices_bearing_commands_is_the_measured_set`, which asserts exactly `["completion","migrate-layout","path"]` and whose message says adding one is expected while a command DISAPPEARING means a working completion was silently removed.

    A COUNT IN THE HEADER WAS CORRECTED DURING THIS ITEM rather than pasted as authored: it first read "30 of 47", copied from the plan, but re-measuring the parser gave 48 top-level commands with 17 carrying subparsers, so 31 lacked a `case` arm. Both the header and `generate_bash_completion` now read "31 of 48 when the fix landed" and say plainly that the number is a census taken once and not a property, so a later reader does not treat a drifted count as a regression.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS `reviewed` AND CARRIES `- Readiness: no-go`. It must NOT be executed: two blocking questions are open (OQ-02, OQ-03), so `aw ipd lint` refuses it at every checkpoint until the maintainer answers, and a human must then set it `approved`. Answer them with `/askme`.

WHAT MAY PROCEED AND WHAT MAY NOT, since the blocks are not total. E-01 is INDEPENDENT of both questions and is the item that removes the reported harm: it needs no answer. E-02 is also independent (capturing choices is correct regardless of who consumes them). E-03 and E-05 are gated on OQ-03, and E-04's two `completion` cases are gated on OQ-02. E-06 and E-07 are independent. So a maintainer who wants the misleading suggestion gone immediately can approve a narrowed run; that is their call, not the executor's.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

DO NOT MUTATE THE REAL USER COMPLETION FILE at `~/.local/share/bash-completion/completions/aw` while testing E-06. It is the maintainer's own file, it is outside this plan's declared paths, and the maintainer's completion working at all is recent. Use `--dir` or a scratch `HOME`.

FOUR CORRECTIONS FROM REVIEW THAT MUST NOT BE RE-INHERITED:

1. Do NOT expect E-02 to fix `aw completion <TAB>`. Its positional has `choices=None`; simulated exactly as specified, the capture is `[]`. That is PR-001 and blocking OQ-02.
2. Do NOT change the static generator without deciding what `complete_query` does. It is a SECOND surface, it already returns empty for the affected commands, and its docstring declares the two must agree. That is PR-002 and blocking OQ-03.
3. Do NOT trust the authored conventions or deferred sections. Both were copied from `wfartifacts` child `gzhd7t` and have been replaced; if you find prose here about run scratch, D92 or `.aw/.gitignore`, it is residue and not this plan's concern.
4. Do NOT expect "several verbs" to gain completions from E-02. Measured: exactly two, `migrate-layout` and `path`. And 28 of 47 commands will correctly offer NOTHING afterwards, which is the intended outcome rather than a new defect.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
