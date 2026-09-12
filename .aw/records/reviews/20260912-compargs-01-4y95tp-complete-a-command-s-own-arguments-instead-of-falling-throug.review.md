# Review: complete a command's own arguments instead of falling through to the command list, child 4y95tp (Set compargs)

- Subject-Id: 4y95tp
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `03e1436c`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(clean, exit 0, 0 findings) before semantic review. At `--phase review-finalize` the linter reports two
`IPD-Q501` errors, which is the escalation gate working as designed: they are the two blocking questions
this review added, and they are the mechanism by which an unfixed BLOCKER stops execution rather than
merely being reported. The suite was measured bare: `5971 passed, 3 skipped, 2 xfailed in 59.70s`.

DISCLOSURE: this plan was authored in the same repository by the same model family, so treat this as a
near-self-review worth less than an independent one. Its value rests on what was EXECUTED. Nine things
were driven rather than recalled: the generated script written to a scratch file, sourced in a subshell,
and `_aw_completion` CALLED with real `COMP_WORDS`/`COMP_CWORD` for five distinct inputs; the 47/17/30
population recomputed from the live parser; `complete_query` called for the same inputs as the script;
the whole parser walked for choices-bearing positionals; E-02's rule SIMULATED against `aw completion`'s
real parser; all three shell generators produced and inspected for a fall-through; the byte-comparison
staleness check run against the live installed file; the test file counted; and the conventions block
`diff`ed against every other pending plan.

SCOPE OF THE LEDGER. The invocation named this plan only, so the ledger is that one plan. The
`compinert` Set (which owns the drop-in layout and the rc stanza) and the `wfartifacts` Set (from which
two sections were copied) were read as EVIDENCE and NOT edited.

THE DEFECT IS REAL AND EVERY REPORTED SYMPTOM REPRODUCES EXACTLY. This is the strongest part of the
plan and review changed none of it. Driven directly: `aw find <TAB>` returns 47 items, `aw completion
<TAB>` returns 47 items, `aw install <TAB>` returns 47 items, `aw ipd <TAB>` correctly returns its 9
subcommands, and `aw completion in<TAB>` returns exactly `include index install`, which is the
maintainer's reported sequence character for character. The counts are exact: 47 top-level commands, 17
with a `case` arm, 30 without. F-1, F-3 and F-4 are all confirmed, and E-01 is the right fix.

THE BLOCKER IS THAT THE PLAN'S OWN MECHANISM CANNOT FIX THE REPORTED CASE, and it was proven by
simulating the fix rather than by reasoning about it. The plan's F-2 says `aw completion` has "a fixed
`bash|zsh|fish|install|uninstall` vocabulary" that `introspect_cli_tree` fails to capture. It has no such
vocabulary in the parser: `target` is `nargs="?"`, `default=None`, `choices=None`, and the pipe-delimited
string is only its `metavar`. The valid set is enforced by a runtime `if shell not in ("bash","zsh",
"fish")` inside `_run_completion`. Running E-02's rule exactly as specified over that parser captures
`[]`, so E-03's stated outcome ("`aw completion <TAB>` offers exactly `bash fish install uninstall zsh`")
is unreachable and E-04's two `completion` cases would fail for a reason no generator work fixes.

WHY IT IS THE MAINTAINER'S CALL RATHER THAN A REPAIR. The free-form shape is DELIBERATE and documented
at `cli.py:4735-4737` ("the install/uninstall verbs are ADDITIVE on child 01's free-form `target`
positional"), and `tests/test_completion.py:206` exists specifically to pin it. Adding `choices` narrows
a public CLI contract and makes a hand-written error message dead code. Escalated as blocking OQ-02 with
three costed options.

THE SECOND ESCALATION IS THAT THE PLAN ADDRESSES ONE OF TWO COMPLETION SURFACES AND BREAKS THEIR
DOCUMENTED PARITY. `complete_query`, the dynamic engine behind `aw __complete`, is never mentioned in the
plan. Measured: it ALREADY returns `[]` for `aw completion <TAB>`, `aw find <TAB>` and `aw install
<TAB>`, so it does not have the fall-through defect and needs no part of E-01. But
`_subcommand_candidates`'s docstring states it "mirrors the generated static scripts so `__complete` and
the offline scripts agree on the static layer", and E-02/E-03 would have the static script offer
`migrate-layout`'s actions while the dynamic engine offers nothing there. The change would falsify a
sentence in the code it is editing. Escalated as blocking OQ-03.

THE ROOT CAUSE THE TWO ESCALATIONS SHARE is that the plan reasoned about ONE mechanism (argparse
`choices`) on ONE surface (the bash generator), when the vocabulary it wants lives in neither: not in
`choices` for the reported command, and not on only one surface. Everything else follows from a narrower
version of the same thing: the "several verbs" guess that is actually two (PR-004), the docstring
amendments required but unallocated (PR-005), and the zsh/fish scope note that is half wrong (PR-008).

TWO WHOLE SECTIONS WERE COPIED FROM AN UNRELATED SET, which is the finding most likely to waste an
executor's time. The `## Project conventions discovered (Step 0)` block is BYTE-IDENTICAL to
`wfartifacts` child `gzhd7t` (`diff` returns nothing), and four of five `## Deferred` bullets belong to
that Set too. They discuss run-scratch relocation, D92, `.aw/.gitignore` anchoring,
`tools/untrack-workflow-artifacts.py` and backlog `2812t3`. None is touched by this plan. An executor
reading "RUN SCRATCH IS UNTRACKED BECAUSE OF D92" while fixing tab completion would either waste effort
or conclude the plan is not about what it says.

WHAT REVIEW CHANGED. Two findings are escalated and OPEN; nine are FIXED. E-items grew 5 to 7 and
V-items 5 to 7, keeping the bijection and the suffix pairing the linter requires: E-05 now carries the
two-surface parity work and E-07 the three docstring amendments the plan required but never allocated.
The E-items were also reordered so the file reads in dependency order (the authored file placed E-05
physically before E-04 while depending on E-03). E-02's "several verbs" survey was replaced with the
measured answer (two), E-03's unreachable promise was retargeted to the two commands it genuinely
serves, and E-04's four cases were split into four unconditional and two conditional on OQ-02. The
conventions and deferred sections were replaced with content about completion.

WHAT REVIEW DID NOT CHANGE, recorded because a reviewer that rewrites a sound plan does harm: E-01 (the
fall-through removal, which is correct and independent of both blocking questions), the choice that no
suggestion is the right fallback, the refusal to add a runtime callback into `aw`, E-06's staleness
design in full (every one of its citations was re-verified and is accurate, and its byte-comparison claim
was driven against the live install), OQ-01's recorded maintainer ruling, and the plan's `- From-Backlog:
g99sg7` provenance with its inherited `- Blocks-Release: next`. All were checked and all are correct.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; G. executability | `cli.py:4727-4734` (`nargs="?"`, `choices=None`, `metavar='bash\|zsh\|fish\|install\|uninstall'`); `cli.py:10466` (the runtime `if`); `cli.py:4735-4737` (the deliberate shape); `tests/test_completion.py:206`; E-02 simulated at review capturing `[]` | **The plan's mechanism cannot fix the case it was written for, and this was proven by simulation.** F-2 asserts `aw completion` has a fixed vocabulary that `introspect_cli_tree` fails to see; it has none in the parser. The valid set is enforced by a runtime `if` and advertised only as a `metavar` STRING, so capturing positional `choices` captures NOTHING for `completion`. E-03's stated outcome is unreachable and E-04's two `completion` cases would fail for a reason no generator change fixes. The free-form shape is DELIBERATE, documented, and pinned by an existing test, so narrowing it is a public-contract decision | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED to OQ-02 with `- Blocking: yes` and `- Finding: PR-001`; refusal verified mechanically (`IPD-Q501` at line 206, exit 1). Three costed options recorded (leave it offering nothing / add `choices` to the positional / parse the `metavar`) with (b) recommended and (c) named as the one to avoid, since parsing help text is the same class of guess that produced this defect. F-2 split into F-2 (the true, narrower finding) and F-2b (the correction). E-02 now states it does NOT fix `completion`; E-03's outcome retargeted; E-04's cases split conditional |
| PR-002 | HIGH | UNDER-SCOPE | C. architecture; D. domain invariants; G. executability | `complete_query` driven at review returning `[]` for three commands; `_subcommand_candidates` docstring ("agree on the static layer"); the installed file verified to be the static generator's output with 0 `__complete` references | **The plan changes one of two completion surfaces and would falsify a parity contract documented in the code it edits.** `complete_query` (behind `aw __complete`) is never mentioned. It already returns empty for the affected commands, so it does not need E-01; but E-02/E-03 would have the static script offer `migrate-layout`'s actions while the dynamic engine offers nothing, making `_subcommand_candidates`'s "agree on the static layer" false. Neither the plan nor its scope check acknowledges a second surface exists | C:Medium; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED to OQ-03 with `- Blocking: yes` and `- Finding: PR-002`; refusal verified (`IPD-Q501` at line 218). Three options costed (share the capture / static-only plus amend the docstring / dynamic owns it, which is not viable given the no-callback constraint) with (a) recommended. New E-05 carries whichever answer is chosen and requires the docstring amended if the answer is (b); V-05 fails the validation if a run changes the static side and shows no dynamic-side evidence. Scope check's under-scope now names the gap |
| PR-003 | HIGH | IN-SCOPE | Evidence accuracy; G. executability | `diff` of the conventions block against `wfartifacts` child `gzhd7t` returning nothing; four of five deferred bullets traced to that Set | **Two whole sections were copied from an unrelated Set.** The entire `## Project conventions discovered (Step 0)` block is byte-identical to `gzhd7t`, and most of `## Deferred` belongs to it: run-scratch relocation, D92, `.aw/.gitignore` anchoring, `tools/untrack-workflow-artifacts.py`, backlog `2812t3`. None is touched here. An executor would either waste effort on a defect that is not present or distrust the plan | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both sections replaced. Conventions now record what review actually measured about completion: the two surfaces, that the dynamic one lacks the bug, the documented parity contract, that only bash has a fall-through, where `completion`'s vocabulary really lives, the two choices-bearing commands, the 28-of-47 post-fix silence, the three `_completion_tip` call sites, and the test-file counts. Deferred now lists this plan's real exclusions. Recorded as F-7 and as correction 3 in the gate's do-not-re-inherit list |
| PR-004 | MEDIUM | IN-SCOPE | Evidence accuracy | parser walk at review finding exactly two: `migrate-layout action`, `path root`; `completion.py` module docstring already recording that status args are free-form `nargs="+"` | **E-02's survey guess is wrong in a way that inflates the plan's value.** It says "several verbs take a status or type token with `choices`, so the sweep is likely to improve more than `completion`". Measured: exactly TWO commands have a choices-bearing positional, and `completion` is not one of them. The status-argument guess is contradicted by the module's own docstring, which records as a verified shape fact that those arguments are free-form | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states the measured answer with both command names and their vocabularies, tells the executor to re-derive it but not to expect growth, and names the contradicting docstring. E-03 retargeted to `migrate-layout` and `path`. Recorded as F-2 (rescoped) and as correction 4 in the gate list |
| PR-005 | MEDIUM | UNDER-SCOPE | G. executability; documentation sync | the spec-sync section requiring two docstring amendments; no `E-*` item carrying them; `completion.py` module header | **The spec-sync section requires documentation work that no execution item performs, so it would be silently dropped.** The plan mandates rewriting `generate_bash_completion`'s docstring (which currently describes the DEFECT as the design) and `introspect_cli_tree`'s, but allocates no item. A THIRD docstring is also affected and unmentioned: the module header states status args are not `choices`, which stays true but should name the arguments that now are | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added E-07 carrying all three, with V-07 requiring the removed fall-through sentence quoted so the correction is checkable. Spec-sync section now records that E-07 owns them and names a FOURTH conditional amendment (`_subcommand_candidates`'s parity sentence) that OQ-03's answer decides |
| PR-006 | MEDIUM | IN-SCOPE | G. executability | authored file order: E-05 physically between E-03 and E-04 while declaring `Depends on: E-03`; `IPD-I303` on the first renumbering attempt | **The execution checklist did not read in dependency order, and the added items initially broke the linter's suffix pairing.** E-05 sat between E-03 and E-04, so an executor working top to bottom would perform the staleness warning before the tests that validate the generator change. The linter also requires `V-N` to validate `E-N` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-items reordered to E-01..E-07 in dependency order, with the staleness item renumbered E-06 and depending on E-04, and the parity item E-05. All seven V-items now suffix-match their E-item; `aw ipd lint --phase review-finalize` re-run and the two `IPD-I303` findings are gone, leaving only the two intended `IPD-Q501` escalations |
| PR-007 | MEDIUM | IN-SCOPE | E. testing | E-04's four authored cases; PR-001's simulation | **Half of E-04's test cases assert an outcome the code cannot produce.** Two of the four (`aw completion <TAB>` yielding five targets, `aw completion in<TAB>` yielding `install` alone) depend on `completion` carrying `choices`. Writing them as unconditional tests would produce a permanently red suite under OQ-02 option (a) | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into FOUR unconditional cases true under every OQ-02 answer (`find` empty, `install` empty as a second command from the 30 so the fix is not special-cased, `ipd` unchanged, `migrate-layout` offering its actions) and TWO conditional ones. Added an instruction to record the reported case as a deliberate non-goal in the test file if OQ-02 is answered (a), so a later agent does not "fix" it by reintroducing a fall-through. V-04 matches |
| PR-008 | LOW | IN-SCOPE | Evidence accuracy | all three generators produced at review: zsh's `args` inner `case` has no default arm; 0 of the fish `complete` lines lack a `use_subcommand`/`seen_subcommand_from` condition | **The scope line's zsh/fish clause implies a fall-through exists there.** It offers "the equivalent generator change if it is cheap and correct", but measured, neither zsh nor fish has an unconditional fallback to remove. The positional-choices half would still apply to them | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-8 and as an explicit deferred bullet stating there is no fall-through work in zsh or fish, while keeping the choices extension in scope if OQ-03 sends the capture to both surfaces |
| PR-009 | LOW | IN-SCOPE | Evidence accuracy; F. UX | parser walk: 28 of 47 commands have neither subparsers nor a choices-bearing positional | **The post-fix silence is not quantified anywhere, so it could be misread as a new defect.** After E-01 plus E-02 plus E-03, 28 of 47 commands will offer nothing. That is the intended outcome (bash then falls back to filenames, which E-01 argues for correctly), but the number belongs in the record | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-9 with the computed number, in the conventions block, and as correction 4 in the gate list, stated as the intended outcome rather than a regression |
| PR-010 | LOW | IN-SCOPE | E. testing; B. safety | V-05 as authored ("mutate the installed file") against the live `~/.local/share/bash-completion/completions/aw` | **The staleness validation as written would mutate the maintainer's own completion file.** It says to mutate the installed file to produce the stale state, with no instruction to use a scratch location, even though `install_shell_completion` accepts `--dir` and the maintainer's completion working at all is recent | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-06 and the required-tests section now direct the executor to a `--dir` override or a scratch `HOME`, and the gate repeats it, noting the file is outside the plan's declared paths |
| PR-011 | LOW | IN-SCOPE | E. testing; G. executability | authored required-tests section naming no baseline; the driving technique described in E-04 but not in required-tests | Two smaller gaps: no suite baseline figure to notice a pre-existing failure against, and the subshell driving technique (the only one that catches this class of bug) was described inside an E-item but absent from the validation section that an executor reads for its method | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required-tests carries the review-measured baseline (`5971 passed, 3 skipped, 2 xfailed in 59.70s`) labelled reference-only with the failure-SET rule, spells out the driving technique step by step, and notes that no existing test uses it. A known limit is also now stated: E-06's warning only fires when the user next runs `aw install`/`aw setup` |

BOTH OPEN FINDINGS ARE DEFERRED-AS-OPEN UNDER THE FIX BAR, and every element the Bar demands is stated.
PR-001 is overall Medium-High on the FUNCTIONALITY axis with a secondary usability axis: the axis is
functionality because option (b) makes a hand-written error message dead code and changes what `aw
completion badvalue` prints, and usability because option (a) leaves the maintainer's own reported
command offering no help at all. It reaches the threshold because narrowing a public CLI contract with a
documented deliberate shape and a pinned shape test is a policy call, not a repair. The required decision
is the maintainer's choice among three options. The consequence of leaving it unresolved is that E-03 and
E-04 carry a promise the code cannot keep and an executor writes a permanently failing test.

PR-002 is overall Medium-High on FUNCTIONALITY with a secondary complexity axis: functionality because
the choice is between one user-visible behavior and two divergent ones depending on whether argcomplete
is active, and complexity because option (a) means touching a function that runs inside a documented
<50ms budget. It reaches the threshold because the alternative to deciding is shipping a change that
makes a docstring in the edited file false. The required decision is which surface owns positional
choices. The consequence of leaving it unresolved is a "works in my other shell" divergence that no test
in the plan would catch.

Effort, time, cost and tokens played no part in either deferral.

Per the escalation rule both findings are raised in the plan as open questions carrying `- Blocking: yes`
and `- Finding: <ID>`, and the refusal was verified rather than assumed: `aw ipd lint --phase
review-finalize` exits 1 with `IPD-Q501` naming OQ-02 at line 206 and OQ-03 at line 218, so the plan
cannot reach `approved` or `begin` until the maintainer answers.

ONE THING IS WORTH THE MAINTAINER'S ATTENTION BEYOND THE TWO QUESTIONS. E-01 alone removes the reported
HARM: it is independent of both blocking questions, and once the fall-through is gone `aw completion
in<TAB>` stops offering `index`. So if the maintainer wants the misleading suggestion gone before
deciding the contract question, a narrowed approval covering E-01, E-02, E-06 and E-07 is available. The
gate section now records which items are gated on which question so that choice is theirs to make rather
than an executor's to improvise.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02's mechanism does not reach `aw completion`. Add `choices` to the positional myself, or escalate? | ESCALATE as blocking OQ-02 with three costed options and a recommendation, changing no parser code. | (a) Adding `choices=[*SUPPORTED_SHELLS,"install","uninstall"]` myself, rejected because it narrows a PUBLIC CLI contract whose free-form shape is documented as deliberate at `cli.py:4735-4737` and pinned by `test_completion.py:206`, and it silently changes what `aw completion badvalue` prints. (b) Teaching the generator to parse `metavar`, rejected because it is a heuristic over a HELP-TEXT field, which is precisely the guessing E-02's own third paragraph forbids. (c) Quietly dropping the `completion` claims from E-03/E-04 without escalating, rejected because it fails SILENTLY: the maintainer's reported command would stay uncompletable and nobody would have decided that. | `cli.py:4727-4734`, `:4735-4737`, `:10466`; `tests/test_completion.py:206`; E-02 simulated at review capturing `[]` | yes |
| D-2 | The plan ignores `complete_query`. Wire the parity myself, or escalate? | ESCALATE as blocking OQ-03, and add E-05 to carry whichever answer is chosen. | (a) Extending `_subcommand_candidates` myself, rejected because it runs inside a documented <50ms budget and because choosing "one behavior" over "two documented behaviors" is a user-visible design call the plan never surfaced. (b) Amending the parity docstring myself to permit divergence, rejected as the worse half of the same call: it would weaken a contract by reviewer fiat to make a plan pass. (c) Noting it in the scope check without escalating, rejected because it fails OPEN: E-03 would land and the docstring would become false with nobody having decided it should. | `complete_query` driven at review; `_subcommand_candidates` docstring; the <50ms budget in `completion.py`'s module header | yes |
| D-3 | Two sections are copied from another Set. Delete them, or replace them with real content? | REPLACE with conventions and exclusions actually measured about completion, and record the copying as F-7. | (a) Deleting them and leaving the sections empty, rejected because Step 0 conventions are load-bearing for an executor who did not author the plan, and an empty section teaches nothing. (b) Leaving them with a note, rejected because the content is not merely stale but about a DIFFERENT subsystem, so a reader would still have to work out which half to ignore. (c) Copying `compinert`'s conventions instead, rejected as the same mistake with a nearer neighbour. | `diff` against `wfartifacts` child `gzhd7t` returning nothing; the nine replacement conventions each measured at review | yes |
| D-4 | Was reading the generator enough, or should the completion function be executed? | EXECUTE IT. Wrote the script to a scratch file, sourced it in a subshell, set `COMP_WORDS`/`COMP_CWORD`, and called `_aw_completion` for five inputs. | Reading `generate_bash_completion` alone, rejected because the plan's whole argument is that text-level reasoning missed this bug for the same reason the tests did: the script is internally consistent, so only the runtime reply reveals that `aw find <TAB>` returns 47 command names. Driving it also produced the exact `include index install` reply, which is what let review confirm the maintainer's transcript rather than trust it. Mutating the real installed completion file, rejected outright: it is the maintainer's own file in a shared environment, so the scratch copy was used. | the subshell driving harness at `/tmp/opencode`; five inputs with their item counts; no file written outside `/tmp` | yes |
| D-5 | E-02 claims "several verbs" gain completions. Accept, or measure? | MEASURE. Walked the whole parser for positional actions carrying `choices`; the answer is two. | Accepting the plan's estimate, rejected because an inflated scope claim is how a plan gets approved for value it cannot deliver, and because the plan's own module docstring already contradicted the status-argument half of the guess. Sampling a few commands rather than walking the tree, rejected as the same error at smaller scale: the interesting fact is the COMPLETE list, since E-03's outcome and E-04's cases are written from it. | the parser walk at review yielding `migrate-layout action` and `path root` only; `completion.py` module docstring on free-form status args | yes |

Every decision above is `Reversible: yes`, so recording is sufficient and no escalation is owed beyond
the two findings already escalated. None changes a published interface, migrates data, deletes anything,
or touches a released artifact; the two that COULD have (adding `choices` to a public positional,
amending a parity contract) are precisely the two that were escalated to the maintainer rather than
taken on reviewer authority.
