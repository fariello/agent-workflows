# Review findings: plan 0brmmy

- Subject-Id: 0brmmy
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-901 (HIGH, fixed), PR-902 (HIGH, fixed), PR-903 (MEDIUM, fixed), PR-904 (MEDIUM, fixed), PR-905 (MEDIUM, fixed), PR-906 (LOW, fixed), PR-907 (LOW, fixed), PR-908 (LOW, fixed)

## Round 1

Reviewed at HEAD `4e7dd52c` in an isolated review lane. The plan file was committed and byte-identical
to the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE
semantic review; `--phase review-finalize --agent` reports `conforming` after revision, including the
new `E-06`/`E-07` and `V-06`/`V-07` pairs.

THIS IS AN UNUSUALLY WELL EVIDENCED PLAN AND ITS CENTRAL JUDGEMENT IS RIGHT. It refuses to re-fix a
bug that no longer exists, which is the honest and harder call, and I verified that refusal rather
than accepting it. I RAN THE F-01 PROBE MYSELF: a child with stdin on a real `pty.openpty` pty and
stdout on a pipe, `CI`/`AW_NONINTERACTIVE` scrubbed, calling `offer_commit` on a throwaway repo. It
printed `STDIN_ISATTY True`, `STDOUT_ISATTY False`, then `OUTCOME skipped | skipped: non-interactive;
pass --commit to commit these changes`, exit 0, with the prompt string absent from the pipe. The
fence holds, exactly as claimed, down to the wording. F-02 verifies by `git show`: commit `64c04288`
(2026-09-28 14:09) replaced the early-return-plus-`stdin_is_interactive` body with the single
`term.is_interactive(override=interactive)` call, and the pre-image is precisely the shape E-04 now
restores. F-03, F-04, F-06 and F-07 all verify; F-04 reproduces exactly (`CI=1` gives
`_is_interactive(True) -> False`, unset gives `True`).

BUT THE PLAN MISSED TWO THINGS, AND BOTH ARE ABOUT THE SAME BLIND SPOT: it counted the ambient-`CI`
failures without reading the whole list, and it asserted a published document stayed true without
opening it.

PR-901. The count is EIGHT, not six, and the two the plan never names are in
`tests/test_interactivity_resolver.py`. That is not a bookkeeping nit, which is why it is HIGH:
`InteractivityResolverOverrideTests::test_explicit_override_short_circuits_both_ways` asserts
`term.is_interactive(stdin=non_tty, output_stream=non_tty, override=True)` is True, and
`::test_explicit_override_beats_process_wide_override` asserts the same over a process-wide False.
Both fail under ambient `CI` because the env rung outranks a positive override. So the repository's
OWN resolver suite already encodes "an explicit positive override wins" - which is E-04's premise one
layer lower. The plan's position is therefore better supported than it knew, AND the repository is in
tension with itself independently of this plan. I did not resolve that: reading (a) says those tests
encode a pre-ruling expectation and should scrub `CI`; reading (b) says the `bmf32u` asymmetry was
meant for the FLAG and not for a programmatic `override=`, which would make `term.is_interactive`
itself narrower than recorded. Choosing (a) rewrites tests this plan does not declare and choosing
(b) reverses a named maintainer ruling, so both are outside a reviewer's authority. New E-07 records
the measurement and both readings; new OQ-03 puts the choice to the maintainer, non-blocking because
every E-item stands under either reading.

PR-902. The plan's Deferred section says "the ladder is NOT being changed, so the published contract
stays true", and OQ-02 treats publishing as optional polish. Opening `docs/cli-output-contract.md`
shows both are wrong: its ladder table is written in `override=` terms, rung 1 as "`--no-interactive`
(or `override=False`)" and rung 3 as "`--interactive` (or `override=True`) forces interactive mode on
when not in a forced non-interactive environment". That is a normative claim about the override
mechanism, and after E-04 a reader following it would predict `_is_interactive(True)` is False under
`CI` when the measured answer is True. So the doc edit is a CORRECTION, not a nicety. I resolved
OQ-02 rather than leaving it (the plan's own instruction was to declare the path before execution if
a reviewer disagreed, and I do), declared `docs/cli-output-contract.md`, and scoped E-06 to the
smallest edit that restores accuracy: ladder and fail-safe invariant untouched, one module-local
exception named with its reason. The plan's worry about confusing an internal parameter with the
operator flags is respected, not dismissed: E-06 must state the distinction.

THREE FINDINGS MAKE THE PLAN'S CASE STRONGER THAN IT CLAIMED, recorded because a reviewer should
correct in both directions. PR-903: F-08 warns that the `_is_pure_delegation` AST predicate may
reject E-04's early return and that V-04 "must confirm the guard's verdict rather than assume it".
That constraint does not exist - `_is_pure_delegation` is defined and NEVER CALLED, dead code, and
the only consumer of `SANCTIONED_DELEGATIONS` merely walks for any call to
`is_interactive`/`is_forced_noninteractive`. I proved it by applying E-04's exact shape and running
the file: `20 passed`. PR-905: E-04 cannot change any shipped caller's behavior today, because
`offer_commit` checks `if assume_yes: proceed = True` BEFORE `elif _is_interactive(interactive)`, and
the only non-test caller passing `interactive=` also passes `assume_yes=True`. PR-904: E-04 ALONE
clears the red `git_commit_helper` test without E-05's scrub, measured (`8 failed` -> `7 failed`, that
test gone from the FAILED list, no test edits), which matters because the plan sequences E-05 as the
item that makes the red tests pass.

I ALSO FIXED SIX PRE-EXISTING `check.ipd-uncarried-obligation` VIOLATIONS (PR-906), giving each
deferred row and open question a specific declination; OQ-01's rests on the structural fact that the
plan's `From-Backlog` link plus inherited gate already prevent silent gate loss.

ONE THING I DELIBERATELY DID NOT CHANGE: E-04's declared dependency on E-01. F-14 shows the two are
separable, but pinning the fence BEFORE touching the predicate is the right order for a change whose
worst failure mode is re-opening the original wedge, so I recorded the independence and kept the
sequencing.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing | `CI=true python3 -m pytest` at `4e7dd52c` reports `8 failed, 3238 passed, 2 skipped`; the FAILED list includes `tests/test_interactivity_resolver.py::InteractivityResolverOverrideTests::test_explicit_override_short_circuits_both_ways` and `::test_explicit_override_beats_process_wide_override`, whose assertions read `term.is_interactive(stdin=non_tty, output_stream=non_tty, override=True)` is True | The failing count is EIGHT, not six, and the two unnamed ones are in a file this plan does not declare AND assert the exact behavior E-04 relies on. The repository's own resolver suite encodes "explicit positive override wins", so the ladder and that suite are in tension independently of this plan | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | New F-10. New E-07 records the re-measured failures, states they are untouched, and names both candidate readings without choosing; new OQ-03 (`Blocking: no`, `Owner: maintainer`) puts the choice to the maintainer with its carrier declination; F-09, Scope, Scope check, Deferred and V-05 corrected from four/six to the real counts |
| PR-902 | HIGH | IN-SCOPE | A. Correctness / honest documentation | `docs/cli-output-contract.md` ladder table rung 1 "`--no-interactive` (or `override=False`)" and rung 3 "`--interactive` (or `override=True`) forces interactive mode on when not in a forced non-interactive environment" | The plan asserts "the ladder is NOT being changed, so the published contract stays true". FALSE: the document is worded in `override=` terms, so E-04 makes a published normative sentence untrue, and a reader following it would predict the wrong answer | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-11. OQ-02 RESOLVED (yes, publish - as a correction, not polish), `docs/cli-output-contract.md` added to `- Scope-Paths:`, new E-06 scoped to the minimum edit (ladder + fail-safe invariant untouched, one exception named with its reason), new V-06 demands before/after plus proof the doc now agrees with the measurement and that `term.is_interactive` was not edited; the false Deferred sentence corrected in place |
| PR-903 | MEDIUM | IN-SCOPE | E. Testing / evidence accuracy | `grep -n '_is_pure_delegation' tests/test_interactivity_resolver.py` returns only line 344 (a docstring mention) and line 363 (the definition), no call site; `test_sanctioned_delegations_are_closed_and_reach_term_resolver` only walks for any `is_interactive`/`is_forced_noninteractive` call; with E-04's exact shape applied, `python3 -m pytest tests/test_interactivity_resolver.py -o addopts=""` reported `20 passed` | F-08's stated constraint on how E-04 may be written DOES NOT EXIST: the predicate is dead code. V-04 was therefore directing the executor to satisfy and verify a guard that cannot fire | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-12 with the executed proof. The Step-0 convention corrected; V-04 no longer demands a single-originating-definition verdict on that premise and instead requires the file's real result WITH its environment stated, since the file has 2 ambient-`CI` failures E-04 neither causes nor fixes |
| PR-904 | MEDIUM | IN-SCOPE | G. Executability / sequencing | `CI=true python3 -m pytest` before (`8 failed, 3238 passed`) and with only E-04's early return applied (`7 failed, 3239 passed`), with `test_interactive_commit_prompts_and_responses` absent from the second FAILED list | E-04 ALONE clears the red `git_commit_helper` test; the plan sequences E-05 as the item that makes the red tests pass, so an executor could add an unnecessary scrub and credit it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-14. E-05 now states its real deliverables (the new direct assertion, plus whatever scrub each file actually needs) and forbids adding a no-op `delenv` to look busy; the Proposed-changes ordering note records that E-04 does not depend on E-01 while keeping that dependency deliberately |
| PR-905 | MEDIUM | IN-SCOPE | A. Correctness / risk framing | `offer_commit`'s `if assume_yes: proceed = True` precedes `elif _is_interactive(interactive):`; the only non-test `offer_commit` caller passing `interactive=` (in `runner_shared`) also passes `assume_yes=True`; the `cli` self-commit caller passes no `interactive=` | E-04 cannot change any shipped caller's behavior today, which the plan's risk framing does not say. Worth recording so a reviewer does not over-weight the change, and so the executor knows the effect is on contract and tests | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-13 recording the branch order and the single-caller measurement, stated as a reason the change is safer than framed rather than as a reason to skip validation |
| PR-906 | LOW | IN-SCOPE | Repository rules | `check_engine.check_durable_carrier` reported `check.ipd-uncarried-obligation`: "6 obligation(s) name no durable carrier" (four deferred rows plus OQ-01 and OQ-02) | Six pre-existing obligations carried no declination, so the plan failed a shipped consistency check | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A specific `Carrier-Declined` written for each (OQ-01's rests on the structural `From-Backlog` plus inherited-gate handoff; the ladder row's points at OQ-03; the `conftest.py` row is a won't-fix on correctness). OQ-02 additionally moved `open` -> `resolved` with `Owner: plan reviewer`, since a reviewer's own resolution must record the reviewer. `check_durable_carrier` now reports CLEAN |
| PR-907 | LOW | IN-SCOPE | Evidence accuracy | `CI=true python3 -m pytest` FAILED list shows FOUR `tests/test_completion.py` failures (`SetupCompletionPromptTests::test_every_input_combination_reaches_its_declared_outcome`, `RcWriteOfferTests::test_rc_write_offer_consenting`, `::test_rc_write_offer_non_consenting_and_absent`, `::test_uninstall_rc_stanza_offer`) | F-09 says three | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 corrected to four with all four test ids named and the re-measured whole-suite figure recorded |

| PR-908 | LOW | IN-SCOPE | Repository rules | `attention_contract.newest_history_record` documents newest-first as "THE WRITER'S CONTRACT" and `ipd_lifecycle._plan_status_events` reverses records on that premise; this plan's two records stood `draft` then `to-review` in file order | The `## Workflow history` was written OLDEST-FIRST, inverting the repository's newest-first contract. Latent while unread, it becomes a `check.lifecycle-transition-invalid` ("backwards transition") the moment any writer prepends a third record | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The two pre-existing records REORDERED to newest-first with their text preserved verbatim (line order only), and the review record prepended above them. `check_lifecycle_transitions` reports CLEAN |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Two resolver tests assert `override=True` wins and fail under `CI`. Fix them, fix the ladder, or raise it? | Raise it: record the measurement (E-07) and put the choice to the maintainer (OQ-03, non-blocking) | Scrub `CI` in that file (rejected: the file is not declared and its assertions bear on the ladder's contract, so a scrub would decide a contract question by editing a test); narrow `term.is_interactive` (rejected: reverses the named `bmf32u` maintainer ruling) | `bmf32u` OQ-03 resolution text (maintainer, 2026-09-28, Option A); the two failing assertions read in `tests/test_interactivity_resolver.py`; the `CI=true` FAILED list | yes |
| D-2 | Is amending `docs/cli-output-contract.md` optional polish (the plan's position) or required? | Required: resolve OQ-02 as yes, declare the path, add E-06 | Leave it to the maintainer (rejected: the plan's own instruction was to declare the path before execution if a reviewer disagreed, and the document is measurably made false by E-04); rewrite the ladder (rejected: touches the `bmf32u` ruling) | The ladder table's `override=`-worded rungs 1 and 3 in `docs/cli-output-contract.md`; the measured `_is_interactive(True) -> True` under `CI=1` after E-04's shape | yes |
| D-3 | Should review keep E-04's declared dependency on E-01 now that F-14 shows they are separable? | Keep it, and record the independence | Drop it to `none` for parallelism (rejected: E-04's worst failure mode is re-opening the original wedge, so pinning the fence first is the right order for a safety-relevant change) | F-14's measurement (E-04 alone clears the failure); F-01's probe establishing what the fence currently does | yes |
| D-4 | How far should E-06's documentation edit go? | Minimum: ladder line and fail-safe invariant untouched, one module-local exception named with its reason | Rewrite the ladder to match the new behavior (rejected: reverses the ruling for every site); delete the `override=` parentheticals (rejected: would leave the document silent on the mechanism, losing information a reader needs) | `bmf32u` OQ-03; the plan's own F-06 argument that flag and programmatic argument are different things, which E-06 is required to state | yes |
| D-5 | Should the two `test_interactivity_resolver.py` failures be lumped with F-09's ambient-`CI` failures? | No: separate them into E-07 and OQ-03 | Lump all seven as one "suite assumes no ambient CI" class (rejected: it would hide that two of them assert a contract property, and lumping is how a contract question gets silently closed as a test-hygiene chore) | The two assertions' content versus the `test_completion.py` failures, which are prompt-path assertions with no bearing on the ladder's precedence | yes |
