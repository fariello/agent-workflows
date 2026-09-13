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
- Status: reviewed
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
  THE SURVEY IS ALREADY DONE AND THE ANSWER IS TWO COMMANDS, NOT "SEVERAL". Measured at review by walking the real parser: exactly two commands have a choices-bearing positional, `migrate-layout action` (`apply cleanup inventory plan resume rollback status wizard`) and `path root` (`config records state system`). The authored guess that "several verbs take a status or type token with `choices`" is FALSE: the status arguments are free-form `nargs="+"`, which `completion.py`'s own module docstring already records as a verified shape fact. Re-derive the list and paste the walk, but do not expect it to grow.
  `completion` IS NOT IN THAT LIST, WHICH IS THE POINT OF PR-001. Its `target` is `nargs="?"` with `choices=None`, so this item does NOT fix the reported case and must not claim to. Whether it becomes fixable is blocking OQ-02.
  - Depends on: E-01
  - Expected outcome: positional `choices` captured under their own key, unconstrained positionals contributing nothing, and the re-derived list of improved commands pasted with its walk, stated as the two commands measured rather than as a general improvement.
  - Execution state: pending

- [ ] E-03 EMIT THE CAPTURED CHOICES, so `aw migrate-layout <TAB>` and `aw path <TAB>` offer their real vocabularies.
  THE EXPECTED OUTCOME WAS CORRECTED AT REVIEW. As authored this item promised `aw completion <TAB>` would yield `bash fish install uninstall zsh`, which E-02's mechanism CANNOT deliver: simulated exactly as specified, the captured choice list for `completion` is `[]` because its positional has `choices=None` (PR-001, blocking OQ-02). Do not write that promise into a test; it would fail for a reason the code cannot fix. The two commands this item genuinely serves are `migrate-layout` and `path`.
  DO NOT DELIVER THIS ITEM UNTIL OQ-03 IS ANSWERED, because emitting choices in the static script while `complete_query` stays ignorant of them makes the two surfaces disagree, and `_subcommand_candidates`'s docstring declares they must agree. The answer decides whether the choices capture is consumed by both surfaces or by one.
  MERGE, DO NOT REPLACE, for a command that has BOTH subcommands and a choices-bearing positional. MEASURED: no such command exists today (the two choices-bearing commands have no subparsers), so this path is latent by construction. Write it anyway and SAY it is untested against a real case rather than implying coverage.
  KEEP THE GENERATED SCRIPT SELF-CONTAINED AND STATIC, which is the existing contract in the module docstring. Do not add a runtime call back into `aw` to resolve choices: that would make every TAB press pay interpreter startup, measured elsewhere in this repo at ~220ms, and would make completion fail when the tool is mid-upgrade.
  - Depends on: E-02
  - Expected outcome: `aw migrate-layout <TAB>` yields its eight actions and `aw path <TAB>` its four roots; the both-kinds merge path exists and is declared latent; no claim made about `aw completion <TAB>`, which OQ-02 owns.
  - Execution state: pending

- [ ] E-04 TEST BY DRIVING THE GENERATED FUNCTION, NOT BY READING THE SCRIPT, and cover the regression that started this.
  THE TECHNIQUE THAT FOUND THIS BUG, and the one the tests should use: source the generated script in a subshell, set `COMP_WORDS`/`COMP_CWORD`, call `_aw_completion`, and inspect `COMPREPLY`. Asserting on the script's TEXT would have passed throughout, because the text was always internally consistent; only executing it revealed that `aw find <TAB>` returns 47 command names.
  THE CASE LIST WAS CORRECTED AT REVIEW, because two of the four authored cases assert an outcome the code cannot produce. As authored: `aw completion <TAB>` yields the five targets, and `aw completion in<TAB>` yields `install` ALONE. Both depend on `completion`'s positional carrying `choices`, which it does not (PR-001). Under OQ-02's option (b) or (c) they become true and MUST be added; under option (a) they never do. So they are conditional on that answer and are listed separately below.
  THE FOUR UNCONDITIONAL CASES, true under every OQ-02 answer: `aw find <TAB>` yields EMPTY (the fall-through fix); `aw install <TAB>` yields EMPTY (a second command from the 30, so the fix is not special-cased to one name); `aw ipd <TAB>` still yields its 9 subcommands, proving E-01 did not break the working half; and `aw migrate-layout <TAB>` yields its eight actions, which is E-03's real deliverable.
  THE TWO CONDITIONAL CASES, to be added only if OQ-02 makes `aw completion` completable: `aw completion <TAB>` yields exactly `bash fish install uninstall zsh`, and `aw completion in<TAB>` yields `install` with `index` explicitly ABSENT. PIN THE INVALID SUGGESTION in the second: a test that only checks `install` is present would pass against today's broken build, which returns `include index install`.
  IF OQ-02 IS ANSWERED (a), SAY SO IN THE TEST FILE rather than silently omitting the maintainer's reported case. A comment naming the reported sequence and recording that `aw completion <TAB>` deliberately offers nothing is what stops a later agent "fixing" it by reintroducing a fall-through.
  - Depends on: E-03
  - Expected outcome: the four unconditional cases green; the two conditional cases present or explicitly recorded as not-applicable with OQ-02's answer cited.
  - Execution state: pending

- [ ] E-05 KEEP THE TWO COMPLETION SURFACES IN AGREEMENT. OQ-03 IS ANSWERED (maintainer 2026-09-12): MAKE THEM AGREE. The amend-the-docstring branch is CLOSED and must not be taken.
  THE CONTRACT IS DOCUMENTED, NOT INFERRED: `_subcommand_candidates`'s docstring says it "mirrors the generated static scripts so `__complete` and the offline scripts agree on the static layer". E-01 through E-03 change the static side only, so this item is what stops the change from breaking that sentence.
  MEASURED STARTING POINT: `complete_query` already returns `[]` for `aw completion <TAB>`, `aw find <TAB>` and `aw install <TAB>`, so it does NOT need E-01's fix; the divergence E-02/E-03 introduce is the choices half, where the static script would offer `migrate-layout`'s actions and the dynamic engine would not.
  SHARE THE CAPTURE: have `_subcommand_candidates` consume the same key E-02 writes, so the two surfaces cannot drift by construction rather than by discipline. Do NOT amend the parity docstring to license a difference; the maintainer declined that, and positional `choices` are STATIC vocabulary by the contract's own definition (fixed, not read from disk), so they belong in the mirrored layer.
  DO NOT COLLAPSE THE TWO SURFACES INTO ONE. Not authorized: they exist for different reasons (an offline script with no interpreter cost; a live engine that reads repository state), and the docstring asks them to AGREE on the static layer, not to become one code path.
  ADD A PARITY TEST, which is the durable half and which nothing provides today. Assert that for the same word list the static script's `COMPREPLY` and `complete_query`'s return agree on the static layer, with `aw completion <TAB>` as an explicit case. Without it, the next change reintroduces this divergence silently, exactly as this plan nearly did.
  - Depends on: E-04
  - Expected outcome: `complete_query` and the generated script return the same candidates for the same position on every command E-03 touched, OR the parity docstring amended with the reason, with OQ-03's answer cited either way.
  - Execution state: pending

- [ ] E-08 GIVE `aw completion`'s POSITIONAL REAL `choices`, WITHOUT WHICH THE REPORTED CASE CANNOT BE FIXED (OQ-02, maintainer ruling 2026-09-12).
  THIS PLAN'S AUTHORED PREMISE WAS FALSE AND THIS ITEM IS THE CORRECTION. Verified twice: that positional reports `choices=None` with `metavar='bash|zsh|fish|install|uninstall'`, so the vocabulary exists ONLY as a DISPLAY string and E-02's capture had nothing to find. Adding `choices` is what converts a vocabulary already fixed in practice into one the tooling can see.
  DERIVE THE LIST, DO NOT WRITE A SECOND LITERAL. `completion.SUPPORTED_SHELLS` already exists and `--shell` already uses it as `choices`; build the positional's list from that plus the two verbs. A hand-written second copy reintroduces the drift this defect is made of, one field over.
  THIS IS A DELIBERATE NARROWING OF A PUBLIC SURFACE, so treat the two things it breaks as work, not as surprises. FIRST, `tests/test_completion.py:206-214` (`test_parser_shape_allows_child03_extension`) PINS the free-form shape and asserts the parse is "not constrained by `choices=`". UPDATE it rather than deleting it: its intent (a future verb parses without a redesign) survives, but such a verb must now be REGISTERED, and the test's comment must say the constraint was tightened on purpose so a reader does not read it as the guarantee being dropped. SECOND, `cli.py:4735-4737` documents the free-form shape as intentional; amend that comment in the same change.
  THE ERROR MESSAGE MOVES FROM THE HANDLER TO ARGPARSE, and the maintainer accepted that visible cost. Today an unknown target reaches the handler, which raises `unknown completion target 'index' (expected bash|zsh|fish|install|uninstall)`. With `choices`, argparse rejects at parse time with its own wording and exit code. Confirm the new message is at least as clear, and if the handler's validation becomes unreachable, REMOVE it rather than leaving two validators that can disagree.
  - Depends on: E-02
  - Expected outcome: the positional carries `choices` derived from `SUPPORTED_SHELLS` plus the verbs; the pinned shape test is updated with its reason; the `cli.py` shape comment is amended; and dead handler validation is removed rather than orphaned.
  - Execution state: pending

- [ ] E-06 WARN WHEN AN INSTALLED COMPLETION IS STALE, WITHOUT REWRITING IT (maintainer ruling 2026-09-12, OQ-01).
  WIDEN THE EXISTING PREDICATE, DO NOT ADD A SURFACE. `_completion_tip` (`cli.py:5519`) already prints the enable-tip when completion is ABSENT and returns silently otherwise, because `_completion_configured` (`:5509`) composes `is_completion_installed`, a PRESENCE check. The never-installed case is therefore already covered; the STALE case takes the silent branch and is the whole gap. Add a second state rather than a second mechanism.
  DETECT BY BYTE COMPARISON, WHICH IS MEASURED SUFFICIENT: comparing the installed file's body, minus the injected `INSTALL_SENTINEL` line, against a fresh `generate_bash_completion()` returns True on a current install (verified at review). No version stamp, no timestamp, no hash file is needed, and each would be a new artifact to keep in sync.
  NEVER REWRITE THE FILE HERE. The ruling is warn-only, and this is the load-bearing constraint: the user's completion file is theirs once written, and `compinert` is concurrently establishing that user-scoped writes require consent. `aw install` must not touch `~/.local/share/bash-completion/completions/` at all.
  SAY WHAT TO RUN, in the maintainer's own shape: name `aw completion install` explicitly, and say that completion is OUTDATED rather than broken, since the stale script still works for every command whose name did not change.
  DO IT ONCE PER INVOCATION, NOT PER REPO. This is a per-user/per-machine concern and `_completion_tip`'s docstring already records that reasoning for the absent case; a batch install across many repos must not repeat the warning per target.
  COMPARE PER DETECTED SHELL ONLY. Do not warn about zsh when the user runs bash; `_detect_shell` already scopes the existing tip and the same scoping applies.
  RE-VERIFIED AT REVIEW: every citation in this item is accurate. `_completion_tip` is at `cli.py:5519`, `_completion_configured` at `:5509`, and the tip is called from THREE sites (`:5437`, `:5505`, `:6794`), each outside the per-repo loop, so the once-per-invocation property already holds and this item inherits rather than builds it. The byte comparison was driven against the live install and returns True.
  - Depends on: E-04
  - Expected outcome: `aw install` warns exactly once when the installed completion differs from what the current CLI would generate, names `aw completion install`, and writes nothing; the absent case keeps today's tip and a current install stays silent.
  - Execution state: pending

- [ ] E-07 AMEND THE THREE DOCSTRINGS THIS CHANGE FALSIFIES, which the plan's own spec-sync section requires and no item carried.
  `generate_bash_completion`'s docstring currently says the function "offers the top-level commands, then the nested subcommands of the first word, plus flags" - an accurate description of the DEFECT. Rewrite it to state that a command offers its own subcommands and positional choices, and that a command with neither offers nothing, so the docstring stops endorsing the fall-through.
  `introspect_cli_tree`'s docstring must record that it captures positional `choices` as well as subparsers, under their own key, and that an unconstrained positional deliberately contributes nothing.
  THE MODULE DOCSTRING IS THE THIRD AND THE PLAN MISSED IT. `completion.py`'s header states as a verified shape fact that "the CLI status arguments are free-form `nargs="+"` (NOT argparse `choices`...)". That remains true, but the module now also reads positional choices, so the header should say which arguments DO carry them (`migrate-layout action`, `path root`) rather than leaving a reader to infer that nothing does.
  - Depends on: E-05
  - Expected outcome: all three docstrings amended, with the fall-through description removed and the two choices-bearing commands named.
  - Execution state: pending

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
- A RUNTIME CALLBACK FROM THE STATIC SCRIPT INTO `aw`. It would put interpreter startup (~220ms, measured elsewhere in this repo) on every TAB press and would break completion mid-upgrade. E-03 forbids it and V-03 greps for it.
- THE DROP-IN LAYOUT, THE ALIAS SYMLINKS AND THE rc STANZA. The concurrent `compinert` Set owns those, including the consent rule for user-scoped writes that E-05's warn-only constraint inherits.
- REWRITING AN INSTALLED COMPLETION FILE. The maintainer ruled warn-only on 2026-09-12 (OQ-01). `aw install` must not touch the user's completion directory at all, and V-06 proves the file was not modified.
- NARROWING `aw completion`'s POSITIONAL TO `choices` ON THIS PLAN'S OWN AUTHORITY. That is a public CLI contract change with a documented deliberate shape and a pinned shape test, so it is blocking OQ-02 rather than an assumed fix.
- ZSH AND FISH FALL-THROUGH REMOVAL, because there is nothing to remove: measured at review, neither generator emits an unconditional default (F-8). If OQ-03 sends the choices capture to both surfaces, extending the zsh/fish generators to emit choices remains in scope as the Scope line says, but no fall-through work exists there.

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
- Status: open
- Owner: none
- Resolution or deferral rationale: ANSWERED BY THE MAINTAINER 2026-09-12: `aw install` should DETECT AND WARN, never silently rewrite. Verbatim: "`aw install` should check and warn 'run `aw completion install` if you want tab-completion for `aw`' or similar." So the installed script is never rewritten behind the user's back, and staleness stops being silent. That is a THIRD option better than the two this question originally framed (rewrite-on-upgrade vs. do-nothing), and it is consistent with the `compinert` ruling that user-scoped writes need consent: a warning asks, a rewrite assumes.
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

- [ ] V-01 validates E-01
  - Required evidence: paste the generator diff showing the post-`esac` fallback removed, and paste the DRIVEN result for `aw find <TAB>` AND `aw install <TAB>` each showing an EMPTY `COMPREPLY` (item count 0). Quoting the diff alone is insufficient: the bug was invisible in the script text and only appeared when the function was executed. Review's pre-fix baseline, for comparison: both returned 47 items.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the parser walk enumerating every command with a choices-bearing positional, and confirm it is the TWO measured at review (`migrate-layout action`, `path root`) or state what changed. Paste `introspect_cli_tree(...)` for `migrate-layout` BEFORE and AFTER, showing the choices captured under their own key and NOT merged into `subcommands`. Paste `introspect_cli_tree(...)['subcommands']['completion']` showing it captures NOTHING, which is the honest result under OQ-02 option (a) and the proof that PR-001 is real. Paste one unconstrained-positional command showing it contributes nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the DRIVEN result for `aw migrate-layout <TAB>` showing its eight actions and `aw path <TAB>` showing its four roots. Paste OQ-03's recorded answer, since E-03 may not land before it is answered. Confirm by grep that the generated script contains no runtime callback into `aw` (it must stay static and self-contained). Do NOT assert anything about `aw completion <TAB>` unless OQ-02 was answered (b) or (c); if it was, paste that too.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste all FOUR unconditional driven cases with their actual `COMPREPLY` contents: `aw find <TAB>` empty, `aw install <TAB>` empty, `aw ipd <TAB>` still returning its 9 subcommands, `aw migrate-layout <TAB>` returning its eight actions. THEN either paste the two conditional `completion` cases with `index` explicitly asserted ABSENT, or paste OQ-02's answer and the test-file comment recording that `aw completion <TAB>` deliberately offers nothing. THEN paste the BARE `python3 -m pytest` summary and the failure-SET delta (criterion: empty). Review's baseline at HEAD `03e1436c`: `5971 passed, 3 skipped, 2 xfailed in 59.70s`, reference only.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste OQ-03's recorded answer and which option it selected. THEN paste, for every command E-03 touched, the candidates from BOTH surfaces side by side: the driven `COMPREPLY` from the generated script, and `complete_query(words, cword)` for the same position, showing they AGREE. If OQ-03 chose option (b), paste the amended `_subcommand_candidates` docstring instead, showing it no longer claims a parity the code does not keep. A run that changes the static side and shows no dynamic-side evidence either way is a FAILED validation.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the parser introspection BEFORE and AFTER, showing `choices=None` becoming the real list, and confirm by quotation that the list is DERIVED from `completion.SUPPORTED_SHELLS` rather than hand-written (a second literal list is a FAILED validation, since that is the same drift this defect is made of). Paste the updated `test_parser_shape_allows_child03_extension` with its diff and its amended comment, and state explicitly that the forward-compat intent is preserved. Paste the amended `cli.py:4735-4737` shape comment. Paste the ACTUAL argparse error for `aw completion index` before and after, and either show the handler's validation removed or explain why it is still reachable. THEN paste the DRIVEN `aw completion <TAB>` result showing the five targets, which is the maintainer's reported command finally working.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste all THREE states from real runs. ABSENT: no installed file, output shows today's enable-tip. CURRENT: a freshly installed file, output shows NEITHER tip nor warning. STALE: mutate the installed file (or generate against a tree with an extra command), output shows the warning naming `aw completion install`. THEN paste `git status`/`ls -l --time-style=full-iso` on the completion directory before and after the stale run, proving the file was NOT rewritten or touched; a modified file is a FAILED validation regardless of the warning being correct. Finally, paste a multi-repo `aw install` showing the warning appears ONCE, not per repo. USE A `--dir` OVERRIDE OR A SCRATCH HOME rather than mutating the real user completion file, which is the maintainer's own and outside this plan's scope.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste all three amended docstrings. For `generate_bash_completion`, show the old sentence describing the fall-through is GONE, quoting the removed text so the correction is checkable. For `introspect_cli_tree`, show it records the choices capture and the deliberate silence on unconstrained positionals. For the module header, show the two choices-bearing commands named and the free-form-status statement still accurate.
  - Observed evidence:
  - Result: pending

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
