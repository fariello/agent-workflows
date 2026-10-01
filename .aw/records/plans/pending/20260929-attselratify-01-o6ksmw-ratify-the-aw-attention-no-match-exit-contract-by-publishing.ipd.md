# IPD: Ratify the aw attention no-match exit contract by publishing it, pinning every surface, and recording the decision

- Date: 2026-09-29
- Kind: child
- Concern: THE FAIL-CLOSED NO-MATCH CONTRACT `aw attention` SHIPPED ON 2026-09-21 IS UNPUBLISHED, LARGELY UNPINNED, AND CONTRADICTED BY THE ONE DOCUMENT THAT DOES SPEAK TO IT, so the maintainer is being asked to ratify a contract they cannot read and a future change to it would be silent. Backlog `ahlgnm` carries OQ-01/OQ-02 of executed plan `fqnj8k` forward and says plainly what is outstanding: "ratification, not design". Authoring MEASURED the shipped behavior rather than trusting the item, and the behavior is exactly as described (exit 2 on all nine surfaces for a non-vocabulary no-match; `--check` refusing separately from drift; bare and vocabulary invocations still exit 0). What authoring ALSO found is three gaps that make ratification hard and relaxation dangerous, none of which the item names. FIRST, `docs/cli-output-contract.md` STATES THE OPPOSITE. Section 11.1 ("Empty Result Convention (Read and List Verbs)") mandates that a read or list verb matching zero records emit `outcome: "clean"`, `exit: 0`, `findings: 0`, `verified: true`, `complete: true`; `aw attention` deliberately emits `outcome: "cannot-run"`, `exit: 2`, `verified: false`, `complete: false` instead. Section 11.4 separately says "invalid selectors MUST exit `2`". So the published contract already says both things, nothing records which governs a zero-match versus an invalid selector, and Section 12's closing line adds a THIRD answer for `aw find` ("exits `1`" on a zero-match selector, which is not what `aw find` does either, measured: exit 0). SECOND, THE VOCABULARY EXEMPTION HAS ZERO TEST COVERAGE. It is the entire mechanism that stops the fail-closed default calling correct usage wrong, it is DERIVED (74 tokens at HEAD) rather than a literal list, and `rg selector_vocabulary tests/` returns nothing; so do `refusable`, `selector_match_facts`, `format_unresolved_selector_message` and `unresolved_selector_agent_record`. A tree or status added to `attention_contract` later, or a refactor of the derivation, can silently turn a legitimate standing question into an operator-error refusal with no test going red. THIRD, FIVE OF THE NINE DECLARED SURFACES ARE UNPINNED. `tests/test_attention.py::SelectorNoMatchIsReportedTests` covers the human board, `--format json`, and the bare exemption; `--agent`, `--check`, `--check --agent`, `-id`, `--paths` and `--filenames` are asserted nowhere, and the list-mode STDOUT-stays-clean property (the one that keeps a pipe uncorrupted) is asserted nowhere at all.
- Scope: RATIFY THE SHIPPED BEHAVIOR AND MAKE IT READABLE AND TAMPER-EVIDENT. No production behavior changes; `agent_workflows/attention.py` is NOT edited and is deliberately absent from `- Scope-Paths:`. IN, four things. (1) Publish the verb's own no-match contract in `docs/cli-output-contract.md`, reconciling Section 11.1's zero-match rule with Section 11.4's invalid-selector rule by stating the DISTINCTION the code already draws (a standing question about repository state versus an assertion that a named artifact exists), so the document stops contradicting the shipped verb. (2) Pin the five unpinned surfaces and the list-mode clean-STDOUT property behaviorally. (3) Pin the VOCABULARY EXEMPTION as a derived property, so the exemption cannot be emptied, narrowed, or divorced from its contract sources without a test failing. (4) Record the ratification in `DECISIONS.md` and one `CHANGELOG.md` line, since the item's closing instruction is to "close this by either recording ratification (no code change) or filing the relaxation" and this plan takes the first branch. OUT, each with a reason. RELAXING the contract, which is the maintainer's call and is routed to OQ-01 rather than guessed; `fqnj8k`'s own execution contract already refused to guess it and nothing has changed that. FIXING `aw find`'s divergent exit 0, which is owned by backlog `hd5bkk` (`Work-Kind: bug`, `Blocks-Release: next`) with its own survey requirement; correcting Section 12's wrong claim about `aw find` is likewise left to that item, because the honest correction depends on which way `hd5bkk` resolves. AMENDING spec `25kzda`, whose Sections 2.3/2.4a govern `aw <host> run` and are PRECEDENT for this verb rather than its contract; widening them to cover every read verb is a contract change this plan has no mandate for. The `--dir`-at-a-subdirectory under-report (backlog `5gmi12`) and the malformed-artifact invisibility (`fyeg6a`), which are separate defects reached through the same verb.
- Scope-Paths: docs/cli-output-contract.md, tests/test_attention.py, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: ahlgnm
- Set: attselratify
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: o6ksmw
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901, PR-902, PR-903, PR-904, PR-905 all fixed. Reviewed at HEAD `c1cacc29`. All nine authored findings were re-measured and the central one holds exactly: the nine-surface refusal matrix reproduces byte for byte, including exit 2 everywhere and a measured 0-byte STDOUT on the three list modes. F-02, F-03, F-04, F-05, F-06, F-07 and F-09 each verify as quoted (Section 11.1 and Section 12 say what the plan says; all five symbols have ZERO test hits; the vocabulary is 74; `aw find` really does exit 0). THREE MEASURED ERRORS WERE CORRECTED. PR-901: F-01's "a bare invocation exits 0" is FALSE in this repository, where it exits 1 from five pre-existing lane diagnostics, and true only in a drift-free repo; since E-01/V-01 made exit 0 a pass-or-stop criterion, an executor would have halted a correct plan on a correct tree, and F-01 as written also contradicted F-08. The exemption is now stated as "no refusal" and tested on `outcome`. PR-902: E-03 named FOUR derivation sources where the production function uses SIX, measurably leaving 19 of 74 tokens unpinned, all of them run-status words, including the very `abandoned` token E-01 probes. PR-903: V-03's prescribed bite test on `TRACKED_TREES` is a measured NO-OP (emptying it changes the vocabulary by zero tokens, because `TYPE_ALIASES` covers every tree name), so it would have passed against a broken subject. The bite tests are also moved to in-memory patching so the out-of-scope production file is never written to, even temporarily.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog item `ahlgnm` (which this authoring pass itself moved to `graduated`; its history records "graduated by run run-20260928T235941Z-1396311: o6ksmw"), which carries NO `- Blocks-Release:` gate, so this plan correctly carries none either (AGENTS.md: inherit the item's gate "if it has one"; do not invent one). The item's `- Work-Kind: followup` and `- Priority: medium` are inherited through `--from-backlog`.
  THE ITEM WAS VERIFIED BY EXECUTION, NOT TRANSCRIBED, and it holds up on its central claim. Every surface it lists was driven at HEAD `869d34ba` in this lane and every one behaves as recorded (see F-01). An executor should NOT re-litigate whether the fail-closed form shipped; it did, exactly as described.
  WHAT AUTHORING FOUND THAT THE ITEM DOES NOT SAY, and it is why this plan is four deliverables rather than a one-line status change. The item frames the outstanding work as a pure decision with no code consequence ("close this by either recording ratification (no code change) or filing the relaxation"). That framing is incomplete in a way that matters to the DECISION ITSELF: the contract is contradicted by `docs/cli-output-contract.md` Section 11.1 (F-02), and the vocabulary exemption the maintainer would be ratifying is pinned by NO TEST WHATSOEVER (F-04). Ratifying an unpublished, unpinned contract records an intention, not a contract. So this plan ratifies AND closes the gaps that make the ratification mean something, while leaving the relaxation question itself to the maintainer at OQ-01.
  ONE OF THE ITEM'S NUMBERS IS WRONG AND IS CORRECTED HERE rather than copied. It says the vocabulary is "63 tokens derived from contract symbols"; measured at HEAD it is 74 (F-05). The mechanism is right and the count is stale, which is itself the argument for pinning the vocabulary as a DERIVED property rather than as a number: E-03 deliberately asserts no count.

## Goal

Turn the fail-closed no-match behavior `aw attention` already ships into a contract a maintainer can read, a test suite can defend, and a future change must announce: published in `docs/cli-output-contract.md` with the Section 11.1 contradiction resolved, pinned on all nine surfaces plus the vocabulary exemption, and recorded as a dated decision, so `ahlgnm` closes on a ratification that is worth something rather than on a note.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure, then publish the contract

- [x] E-01 RE-DRIVE THE FULL SURFACE MATRIX AT THE EXECUTION BASE and write the results into this plan's validation evidence, because every sentence E-02 publishes must trace to a measurement taken at execution time and not to this authoring pass. Drive `aw attention` (via `python3 -m agent_workflows attention`, so no installed-package shadowing is possible) with a NON-VOCABULARY unmatched token on each of the nine surfaces the item enumerates: the human board, `--agent`, `--json`, `--format json`, `--check`, `--check --agent`, `-id`, `--paths`, `--filenames`. For each, record the exit code, whether the diagnostic went to STDOUT or STDERR, and for the three list modes whether STDOUT is EMPTY (that is the pipe-safety property, and it is the one this plan must not publish without checking). Then drive the two exemptions: a BARE invocation with no selector, and at least four VOCABULARY tokens drawn from DIFFERENT derivation sources so one source failing is visible (a `TRACKED_TREES` name, an `ATTENTION_CLASSES` value, a `CLASS_MAPS` native status, and a `_RUN_STATUS_ALIASES` run word; `reusable`, `ready`, `shipped` and `abandoned` are a known-good set, measured at authoring).
  TEST THE EXEMPTION AS "NO REFUSAL", NOT AS "EXIT 0", because in a tree with drift the exemption still exits 1 and an executor checking for a literal `0` would wrongly conclude the behavior moved and STOP (F-01b, measured: a bare invocation exits 1 in this repository from five pre-existing lane diagnostics, while the same invocation exits 0 in a drift-free fixture repo). So for BOTH exemption classes record the exit code AND the machine record's `outcome`, and judge the exemption on `outcome` being `clean` or `findings` (never `cannot-run`) and on the absence of `unresolved_selectors`. Drive the bare and vocabulary cases in a THROWAWAY DRIFT-FREE REPOSITORY as well, where exit 0 IS the correct expectation, and record both columns; the shipped fixture `tests/test_attention.py::_attsel_repo` is a known-good builder for that repo and is the same one the existing pin uses. Also record the MIXED case (one matched token plus one unmatched token in the same invocation) and whether the record names both. Finally, read back the SHAPE of the machine record on one surface and confirm against `agent_schema.assert_valid_agent_record` rather than by eye. DO NOT EDIT ANY FILE IN THIS ITEM.
  - Depends on: none
  - Expected outcome: a written nine-row surface table plus an exemption table, each row carrying an actual exit code, the machine `outcome`, and the stream, produced by commands pasted into V-01; the exemption rows carry BOTH a live-tree and a drift-free-repo column. A REFUSAL row (one of the nine) disagreeing with F-01 STOPS execution and is reported, because a divergence there means the behavior moved and the ratification question itself has changed. An EXEMPTION row showing exit 1 with `outcome: findings` in the live tree is NOT a divergence and must NOT stop execution: that is the drift code doing its job on top of a working exemption (F-01b). Only `outcome: cannot-run` or a present `unresolved_selectors` on an exemption row is a real divergence.
  - Execution state: performed

- [x] E-02 PUBLISH THE VERB'S NO-MATCH CONTRACT IN `docs/cli-output-contract.md` AND RESOLVE THE SECTION 11.1 CONTRADICTION, using only figures E-01 produced. THE CONTRADICTION IS THE POINT OF THIS ITEM, so fix it rather than appending a tenth section that disagrees with the ninth. Section 11.1 currently mandates, for any "query, find, search, or list verb" matching zero records, a record with `outcome: "clean"`, `exit: 0`, `findings: 0`, `verified: true`, `complete: true`; Section 11.4 separately mandates that "invalid selectors MUST exit `2`". Amend Section 11.1 to state the DISCRIMINATOR the code already implements, in the terms the code already uses: a zero-result for a token that is a STANDING QUESTION ABOUT REPOSITORY STATE (a tree name, an attention class, an artifact status, a priority, a run state, or a bare invocation with no selector at all) is the Section 11.1 clean-empty case and is NOT REFUSED; a zero-result for a token ASSERTING THAT A NAMED ARTIFACT EXISTS (an id6, a setid, a filename fragment) is the Section 11.4 refusal case and exits 2 with `outcome: "cannot-run"`, `verified: false`, `complete: false`.
  WORD THE EXEMPT SIDE AS "NOT REFUSED", NOT AS "EXITS 0", and state why in the document: the exemption skips the refusal, after which the verb's ORDINARY exit code still applies, so a standing-question token in a repository that also has contract drift correctly exits 1 through the drift path and not 0 (F-01b, measured: a bare invocation exits 1 in this repository and 0 in a drift-free one). Publishing a flat "exits 0" would mint a THIRD wrong statement in this same document, which is the exact defect F-02 and F-03 record; say instead that the exempt case yields `outcome: "clean"` with exit 0 when nothing else is wrong, and that a concurrent drift finding still reports itself normally. State that the refusal is a SEPARATE CONDITION from a contract finding, so it neither appends a drift record nor flips the `--json` `valid` flag, since that separation is what keeps an operator typo from reading as repository damage. State the LIST-MODE STREAM RULE explicitly with the reason, because it is a hard requirement and not a preference: on `-id`, `--paths` and `--filenames` the diagnostic goes to STDERR and STDOUT stays EMPTY, so a refusal can never corrupt a pipe. Cite the authority BY SYMBOL: `attention.EXIT_UNRESOLVED_SELECTOR`, `attention.selector_vocabulary`, `attention.SelectorMatchFacts.refusable`, and the shipped precedent `run_viewer.emit_unresolvable_target_refusal`. Name spec `25kzda` Sections 2.3/2.4a as the PRECEDENT followed, and say plainly that the spec governs `aw <host> run` rather than this verb, so a reader does not mistake a precedent for a binding contract. DO NOT touch Section 12's claim about `aw find`: it is wrong (F-03) and its correction belongs to backlog `hd5bkk`, whose resolution decides what the true statement is. Write it as USER-FACING prose with NO em or en dashes (AGENTS.md).
  - Depends on: E-01
  - Expected outcome: `git diff docs/cli-output-contract.md` shows Section 11.1 amended so it no longer mandates exit 0 for the assertion case, the discriminator stated once in terms of standing question versus named-artifact assertion, the exempt side worded as NOT REFUSED (with the drift-still-applies sentence, so the document does not publish a flat and falsifiable "exits 0"), the list-mode STDERR/empty-STDOUT rule stated with its pipe reason, four symbols cited, `25kzda` named as precedent with its scope limit stated and its `reviews`-specific subject not overstated, and Section 12 UNCHANGED. No `.py` file touched by this item.
  - Execution state: performed

### Task group 2: pin what a relaxation would have to break on purpose

- [x] E-03 PIN THE VOCABULARY EXEMPTION AS A DERIVED PROPERTY, in `tests/test_attention.py`, because it is the load-bearing half of the contract and today has ZERO coverage (F-04). Assert, by CALLING `attention.selector_vocabulary()` and driving `attention.run`, all of the following. (1) EVERY value of ALL SIX derivation sources is present in the returned set: every `attention_contract.TRACKED_TREES` name, every `attention_contract.ATTENTION_CLASSES` value, every native status key across `attention_contract.CLASS_MAPS`, every `backlog.PRIORITIES` value, every `attention._RUN_STATUS_ALIASES` KEY AND VALUE, and the `run_viewer.ABANDONED` token. Iterate the SOURCE SYMBOLS so a value added to any of them joins the assertion automatically; that is the property that makes the exemption survive a later contract addition, and it is the exact regression this pins.
  SIX SOURCES, NOT FOUR: the earlier wording named four and MEASURABLY left 19 of the 74 tokens unpinned, every one of them a run-status word (review 2026-09-30, PR-902). Measured: the four named sources cover 39 of 74; adding item (2)'s `TYPE_ALIASES` reaches 55; the remaining 19 (`abandoned`, `completed`, `dependency-blocked`, the six `fail-*`, `failed`, `failed-safely`, `integration-blocked`, `interrupted`, the three `merge-*`, `not-run`, `partial`, `substantially-complete`) come only from `_RUN_STATUS_ALIASES` and `run_viewer.ABANDONED`. That gap matters twice over: it is the source E-01 draws its `abandoned` probe token from, so the plan tests a token its own pin would not protect; and the stated property "a value added to any of them joins the assertion automatically" would be FALSE for a new run status, which is precisely the regression class the plan exists to prevent. NOTE `run_viewer.ABANDONED` is the string `'abandoned?'` and the production code strips the trailing `?`; assert the STRIPPED token, and read it through the symbol rather than hardcoding either spelling. Guard the `run_viewer` import the way production does, so a missing optional symbol fails the test loudly rather than silently narrowing what is asserted. (2) Every `attention.TYPE_ALIASES` key and value is present, including the type names the CLI accepts but the scanner cannot answer with an item (`roadmaps` and `walkthroughs` are the measured cases), because refusing those would call an operator wrong for using a name the verb's own `-t` flag documents. (3) A vocabulary token that matches NOTHING still exits 0, driven end to end in a temporary repository built so the token genuinely matches nothing, on at least the human board and one machine surface. (4) `SelectorMatchFacts.refusable` EXCLUDES a vocabulary token and INCLUDES a non-vocabulary unmatched token, asserted on a constructed `SelectorMatchFacts` so the predicate is tested directly rather than only through the CLI. (5) Case-insensitivity: an upper-case spelling of a vocabulary token is still exempt. ASSERT THIS THROUGH THE CALL PATH, NOT BY SET MEMBERSHIP: the returned set holds lowercase tokens ONLY, so `'REUSABLE' in attention.selector_vocabulary()` is False while `attention.run` with the selector `REUSABLE` exits 0 (both measured at review). A membership assertion would therefore either fail against correct code or, if written the other way, pin a property the set does not have; drive the verb. DO NOT ASSERT A VOCABULARY COUNT or an exact token list: the set is derived and grows by design, the item's own "63" is already stale at 74 (F-05), and a count assertion would fail on every unrelated contract addition, which is churn rather than protection. DO NOT read `attention.py` source with `inspect`, `ast`, regex or substring search, and do not assert on symbol censuses or comment text (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16).
  - Depends on: E-01
  - Expected outcome: new test coverage in `tests/test_attention.py` that passes at the base (it pins shipped behavior, so it must go green immediately) and that FAILS if the vocabulary stops deriving from any one of its SIX sources, if a `TYPE_ALIASES` spelling loses its exemption, if a RUN STATUS loses its exemption (the class four sources alone leave uncovered), if `refusable` starts including vocabulary tokens, or if the case-folding is dropped. State for each per-source assertion whether it is a genuine BITE test or a coverage assertion made redundant by another source, since `TRACKED_TREES` is measurably fully redundant with `TYPE_ALIASES` (PR-903).
  - Execution state: performed

- [x] E-04 PIN THE FIVE UNPINNED SURFACES AND THE LIST-MODE STREAM RULE, in `tests/test_attention.py`, extending the existing `SelectorNoMatchIsReportedTests` neighborhood rather than starting a parallel harness (it already owns `_attsel_repo`, `_attsel_args` and `_attsel_run`, and a second fixture would drift from it). For a NON-VOCABULARY unmatched token, assert on each of `--agent`, `--check`, `--check --agent`, `-id`, `--paths` and `--filenames`: the exit code equals `attention.EXIT_UNRESOLVED_SELECTOR`, and the stream carrying the diagnostic is the one E-02 published. For the three LIST MODES specifically, assert STDOUT IS EXACTLY EMPTY, since that is the pipe-safety property and asserting only the exit code would let a future change print a diagnostic into a pipe without failing. For `--check` and `--check --agent`, assert TWO further things that are the whole of OQ-02 and are asserted nowhere today: that the success sentence `aw attention --check: the view is valid.` is ABSENT (the refusal must not claim validity about a token it never resolved), and that the refusal did NOT append a drift or violation record, so the refusal stays separate from the drift set. For `--check --agent`, assert the emitted record validates through `agent_schema.assert_valid_agent_record` and carries `outcome: "cannot-run"` with `verified: false` and `complete: false`, rather than hand-checking fields. Also pin the MIXED case: one matched token plus one unmatched token exits 2 and the record names the unmatched token in `unresolved_selectors` AND the matched one in `matched_selectors`, so a partial refusal stays diagnosable. Behavior only; no source introspection.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_attention.py -k <the selector tests> -o addopts=""` green, covering all nine surfaces rather than three, with the list-mode empty-STDOUT and the two `--check` properties asserted; each new assertion fails if the corresponding behavior is relaxed.
  - Execution state: performed

### Task group 3: record the ratification and verify

- [x] E-05 RECORD THE RATIFICATION AS A DATED DECISION in `DECISIONS.md`, appended as the next `### D<NNN>` entry under the existing newest-at-the-bottom convention (D156 is last at authoring; read the file and take the next integer rather than assuming 157, since another agent may have appended one). Follow the file's own three-part shape exactly: `- **Context:**` naming plan `fqnj8k`, backlog `ahlgnm`, and the measured behavior; `- **Decision:**` stating that the FAIL-CLOSED form is ratified, that the discriminator is standing question versus named-artifact assertion, and that the two exemptions (bare invocation, vocabulary token) are part of the ratified contract rather than concessions; `- **Applied:**` naming the files this plan changed. RECORD THE REJECTED ALTERNATIVES, because the whole value of the entry is that the next reader does not re-open a settled question: exit 1 folded into the drift code (rejected: `agent_schema`'s parity rule makes `exit:1` incompatible with `cannot-run`, so it would force a `findings` outcome for a request that was never answered, and would be indistinguishable from a genuine contract violation) and exit 0 with a message only, the live `aw find` convention (rejected: a script resolving an id6 and getting exit 0 with empty output concludes "nothing to do"). STATE THE RELAXATION ROUTE HONESTLY, since the item's strongest point is that relaxing must stay cheap: name `attention.EXIT_UNRESOLVED_SELECTOR` and the single `--check` branch as the edit sites, and note that E-03/E-04's pins are what a relaxation must deliberately update, which is the intended cost and not an obstacle. DO NOT write this entry as if it attests a human decision the maintainer has not made: the `- **Decision:**` line must say the behavior is ratified BY THIS PLAN'S APPROVAL, and OQ-01 remains the maintainer's route to overturn it. Then add ONE `CHANGELOG.md` line in the existing entry style, describing the published contract and the new coverage, with no em or en dashes.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: one new `### D<NNN>` entry appended to `DECISIONS.md` in the file's own Context/Decision/Applied shape naming both rejected alternatives and the relaxation route, plus exactly one added `CHANGELOG.md` line. Nothing already in `DECISIONS.md` is rewritten (it is append-only; GUIDING_PRINCIPLES P4).
  - Execution state: performed

- [x] E-06 VERIFY THE WHOLE CHANGE AND CLOSE OUT. Confirm no em or en dash entered the user-facing prose: `git diff docs/cli-output-contract.md CHANGELOG.md | grep -nP '[\x{2013}\x{2014}]'` must print nothing. Run the suite BARE as `python3 -m pytest` and paste the ACTUAL summary line, having first recorded a pre-change baseline count so the delta is the tests this plan added and not a number asserted from memory. Re-drive the nine-surface matrix ONE MORE TIME after all edits and confirm every exit code is unchanged from E-01, which is the proof that this plan altered no behavior; state that explicitly. COMPARE LIKE WITH LIKE: re-drive in the SAME tree state E-01 used, and note that the drift-dependent EXEMPTION rows may legitimately differ if another agent landed or fixed a lane mid-execution (F-01b), so judge those rows on `outcome` never being `cannot-run` rather than on a literal exit code, and say which tree each column was taken in. The nine REFUSAL rows must be identical, and those are the no-behavior-change proof. Run `python3 -m agent_workflows attention --check --agent` with NO selector and report its exit code, confirming the CI invocation at `.github/workflows/tests.yml` is untouched by this plan (it passes no selector, so the refusal predicate cannot fire on it); expect 1 rather than 0 in a drifty tree and report the exit code without treating either value as a failure. Run `aw sanitize --agent; echo rc=$?`. Run `aw ipd lint --phase pre-transition` on this plan and paste the conformance line.
  - Depends on: E-05
  - Expected outcome: no en or em dash in the diffed user-facing prose; suite green with the summary pasted and the delta explained; the nine REFUSAL rows of the surface matrix identical to E-01's, stated as the no-behavior-change proof, with any drift-dependent exemption-row difference explained rather than treated as a regression; the bare `--check --agent` exit code reported (1 in a drifty tree is expected); sanitizer rc 0; `aw ipd lint --phase pre-transition` conforming.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string; a line offset expires before this plan executes, so the Findings table's offsets are approximate and are always paired with a symbol or quote (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `DECISIONS.md` is APPEND-ONLY with newest entries at the bottom, numbered `### D<N>` (D156 is last at authoring), and each entry carries `- **Context:**`, `- **Decision:**` and `- **Applied:**`. GUIDING_PRINCIPLES P4 is the authority; E-05 follows the shape rather than inventing one.
- User-facing prose (`docs/`, `CHANGELOG.md`, `README.md`) must contain NO em or en dashes; internal artifacts such as this plan, its findings, and commit messages are exempt and should spend no effort avoiding them (AGENTS.md).
- Tests must exercise BEHAVIOR and assert on real outputs, exit codes and side effects. Reading production source with `inspect`, `ast`, regex or substring search is forbidden outright, as is asserting that comment or docstring text is unchanged (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). This is why E-03 iterates the CONTRACT SYMBOLS and calls the functions instead of grepping them.
- Run the suite BARE as `python3 -m pytest`. Do not add `-n0` (disables xdist, several times slower here), a second `-q` (compounds into `-qq` and suppresses the summary line this plan must paste), or `-p no:randomly` (AGENTS.md "HOW TO RUN THE SUITE"). For a narrowed run, clear the configured defaults explicitly with `-o addopts=""`.
- Invoke the CLI as `python3 -m agent_workflows ...` inside this checkout, or set `AW_NO_REEXEC=1`: a bare `aw` in a worktree prints a re-exec notice because the `aw` on PATH imports the package from the main checkout, which would measure the wrong tree.
- The vocabulary exemption is DERIVED from `attention_contract.TRACKED_TREES`, `attention_contract.ATTENTION_CLASSES`, `attention_contract.CLASS_MAPS`, `attention.TYPE_ALIASES`, `backlog.PRIORITIES` and `attention._RUN_STATUS_ALIASES`, never a literal list, precisely so a token added to a contract joins the exemption automatically. Any test that pins it must preserve that property.
- Commit through `aw commit o6ksmw -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, never push.

## Findings

| # | Location (at authoring) | Finding |
| --- | --- | --- |
| F-01 | `attention.EXIT_UNRESOLVED_SELECTOR`; driven at HEAD `869d34ba` in this lane | THE ITEM'S CENTRAL CLAIM REPRODUCES EXACTLY, so ratification is a real question and not a stale one. Driving `python3 -m agent_workflows attention zzzzzz` on all nine surfaces: human board exit 2 (diagnostic on STDERR, STDOUT empty), `--agent` exit 2 (compact record on STDOUT), `--json` and `--format json` exit 2 (indented record on STDOUT), `--check` exit 2 (STDERR, and the `the view is valid.` sentence ABSENT), `--check --agent` exit 2 (record on STDOUT), `-id`/`--paths`/`--filenames` all exit 2 with STDOUT measured at 0 bytes. The machine record carries `kind: error`, `outcome: cannot-run`, `verified: false`, `complete: false`, `findings: 1`, and BOTH `unresolved_selectors` and `unresolved_targets`. It carries NO `diagnostics` key and NO `valid` key, so the refusal genuinely does not travel through the drift path. The mixed case (`attention ahlgnm zzzzzz --agent`) exits 2 and names `matched_selectors: ["ahlgnm"]` beside the unresolved one. Both exemptions hold: `reusable`, `shipped`, `roadmaps`, `walkthroughs` and `abandoned` each exit 0 (three of them with real output, `reusable` with `0 artifacts shown`). |
| F-01b | `attention.run`; driven at review HEAD `c1cacc29` and in `tests/test_attention.py::_attsel_repo` | THE BARE-INVOCATION EXEMPTION IS NOT "EXIT 0"; IT IS "EXIT 0 UNLESS THE TREE HAS DRIFT", and stating it unconditionally sets a stop condition an executor WILL trip on in this very repository (review 2026-09-30, PR-901). What the exemption actually does is skip the REFUSAL predicate, after which the ordinary drift exit code still applies. MEASURED IN THIS TREE: a bare `python3 -m agent_workflows attention` exits **1**, not 0, with `outcome: findings`, `findings: 5`, from five pre-existing lane diagnostics (one `attention.lane-superseded`, four `attention.lane-stranded`). MEASURED IN A DRIFT-FREE REPOSITORY (the shipped `_attsel_repo` fixture): bare, bare `--agent`, bare `--check` and bare `--check --agent` all exit **0**, which is what the existing pin asserts and what the exemption genuinely guarantees. So the correct statement of the exemption is about the REFUSAL, not about the exit code, and E-01/V-01 must test the refusal's absence rather than a literal `0`. This also reconciles F-01 with F-08, which measured `1` for the same invocation class and which F-01 as written contradicts. |
| F-02 | `docs/cli-output-contract.md` Section 11.1, "Agent Protocol (`aw.agent/v1`): The handler MUST emit a structured `result` (or `summary`) record with: `outcome: \"clean\"`, `exit: 0`, `findings: 0`, `verified: true`, `complete: true`" | THE ONE PUBLISHED DOCUMENT THAT SPEAKS TO THIS MANDATES THE OPPOSITE OF WHAT SHIPPED, AND THE ITEM DOES NOT MENTION IT. Section 11.1 governs "a query, find, search, or list verb" matching zero records, which `aw attention` with a selector plainly is, and it requires `clean`/`0`/`true`/`true`. The shipped verb emits `cannot-run`/`2`/`false`/`false`. Section 11.4 in the SAME document then says "invalid selectors MUST exit `2`", so the document already contains both rules with nothing distinguishing a zero-match from an invalid selector, and Section 3 states the bare `0`/`1`/`2` classification without mentioning selectors at all. CONSEQUENCE FOR THE RATIFICATION DECISION, which is why this is F-02 and not a footnote: a maintainer reading the docs to decide whether to ratify finds the docs already forbidding the behavior, and an agent citing Section 11.1 in a future review would be correctly citing a published contract against shipped code. Resolving this is E-02 and is the single most valuable deliverable here. |
| F-03 | `docs/cli-output-contract.md` Section 12, "If a specific selector matches zero paths, the command exits `1` (or exits `0` when listing empty unfiltered sets in human mode)" | A THIRD PUBLISHED ANSWER EXISTS AND IS FALSE OF THE VERB IT DESCRIBES, which bounds what E-02 may safely touch. Section 12 governs `aw find` and claims exit 1 on a zero-match selector. Measured: `python3 -m agent_workflows find plans zzzzzz` prints `CLEAN  no matching plans` and exits 0, on both the human and the `--agent` surface. So the document describes a behavior `aw find` does not have, in a third direction from both Section 11.1 and the shipped `attention`. DELIBERATELY NOT FIXED HERE: `aw find`'s zero-match is owned by backlog `hd5bkk` (`Work-Kind: bug`, `Blocks-Release: next`), which requires a survey of every selector-taking read verb; the honest correction to Section 12 depends on which way that item resolves, and correcting it now would either pre-empt that decision or replace one wrong sentence with another. E-02 therefore states the `attention` contract and leaves Section 12 alone, and this finding is the reason a reviewer should read that omission as intentional. |
| F-04 | `tests/`, measured by `rg` over five symbol names | THE EXEMPTION MECHANISM IS ENTIRELY UNPINNED, WHICH INVERTS THE ITEM'S RISK ASSESSMENT. `rg selector_vocabulary tests/`, `rg refusable tests/`, `rg selector_match_facts tests/`, and `rg 'format_unresolved_selector_message|unresolved_selector_agent_record' tests/` each return ZERO hits. The ONLY coverage is `tests/test_attention.py::SelectorNoMatchIsReportedTests::test_selector_no_match_is_reported`, a single test asserting the human board, `--format json`, and the bare-invocation exemption, plus two matched-token controls. So five of the nine declared surfaces, the list-mode clean-STDOUT property, the `--check` non-assertion-of-validity property, the drift separation, the mixed-token case, and the entire derived vocabulary are asserted NOWHERE. The item says relaxing is cheap because it is "one constant plus its pinning tests"; the pinning tests it refers to are three surfaces, so today a relaxation could half-land (relaxing the board while leaving `--check` refusing, or vice versa) and the suite would stay green. That is a worse position than either ratifying or relaxing deliberately. |
| F-05 | `attention.selector_vocabulary`, driven | THE ITEM'S TOKEN COUNT IS STALE, WHICH IS AN ARGUMENT FOR PINNING THE PROPERTY AND NOT THE NUMBER. The item states "63 tokens derived from contract symbols"; `len(attention.selector_vocabulary())` returns 74 at HEAD. The derivation is exactly as the item describes (6 `TRACKED_TREES`, 22 `TYPE_ALIASES` keys plus their values, 5 `ATTENTION_CLASSES`, every `CLASS_MAPS` native status, `backlog.PRIORITIES`, and the run-status alias table plus `run_viewer.ABANDONED`), so nothing is wrong with the mechanism; the set simply grew, which is the mechanism working. E-03 therefore asserts SOURCE COVERAGE and never a count, and this finding is why. |
| F-06 | `attention.run`, the comment "AND IT IS A SEPARATE CONDITION FROM DRIFT, deliberately"; `attention.py:60-83` preamble | THE ENTIRE RATIONALE LIVES IN CODE COMMENTS AND NOWHERE A MAINTAINER LOOKS. The 24-line comment block above `EXIT_UNRESOLVED_SELECTOR` names both rejected alternatives and the relaxation route, and the comment at the refusal site explains why the condition is kept out of the drift path so OQ-02 can be relaxed without touching drift. This is good engineering and it is INVISIBLE to the decision: `rg EXIT_UNRESOLVED_SELECTOR docs/ AGENTS.md README.md CHANGELOG.md` returns nothing, and no `.spec.md` states the verb's contract. So the ratification has no durable home unless this plan makes one, which is E-02 plus E-05. |
| F-07 | `.aw/records/specs/approved/20260826-25kzda-...spec.md` Section 2.3 ("Zero matches return exit 2") and Section 2.4a | THE PRECEDENT IS REAL AND ITS SCOPE LIMIT IS REAL TOO, and both must be stated or the citation misleads. Section 2.3 does say "Zero matches return exit 2", and the carve-out does use exactly the reasoning `attention.selector_vocabulary` reuses ("a standing question about repository state rather than an assertion that a named item exists ... A misspelled id6 still exits 2; only the status selectors are exempt"). READ THE CARVE-OUT'S SUBJECT PRECISELY when E-02 cites it: the sentence is written about `aw reviews` specifically ("`reviews` matching nothing means the repository has nothing awaiting review ... This is the one deliberate exception to the Section 2.3 rule"), and it generalizes to status selectors only in its closing clause. So cite it as the reasoning this verb ADOPTS and extends from one verb's status selectors to a derived vocabulary, not as a rule already written for a token class this size; overstating it would be citing a narrow exception as a broad mandate. BUT the spec's own `- Scope:` is "the behavior of the single canonical runner verb `aw oc run` / `aw agy run`", so it does not govern `aw attention` and this plan must NOT be read as implementing it. Confirmed by execution that the sibling verb implements it: `python3 -m agent_workflows runs totalgibberish` exits 2 with `error: no run matched target 'totalgibberish'`. So the precedent is two-verb and live, and E-02 cites it as precedent with the scope limit stated rather than as authority. AMENDING the spec to cover read verbs generally is OUT OF SCOPE: that is a contract change affecting every plan reviewed against `25kzda`, and it is not this plan's mandate. |
| F-08 | `.github/workflows/tests.yml`, the `attention-check` job step "aw attention --check (cross-tree attention view; fail closed)" | CI IS UNAFFECTED EITHER WAY, CONFIRMING THE ITEM. The step runs `python -m agent_workflows attention --check --agent` with NO selector, and a bare invocation is exempt, so the refusal predicate cannot fire on it. Measured in this lane: that exact command exits 1 with `outcome: findings`, `findings: 2`, from two pre-existing lane diagnostics (`attention.lane-superseded`, `attention.lane-stranded`), which is the drift path and not the refusal path. The item's claim of "exit 1 from the repository's 27 pre-existing violations" is directionally right and its COUNT has moved, which is normal for a live tree; E-06 therefore reports an exit code and never a count. |
| F-09 | `attention.run`, the `selector_facts` block; driven | A DOWNSTREAM FILTER THAT EMPTIES A MATCHED RESULT STILL EXITS 0, which is correct and is worth pinning as the boundary of the contract. Measured: `attention ahlgnm --status done` and `attention ahlgnm -t plans` each print `0 artifacts shown` and exit 0, because the match fact is computed against the UNFILTERED scan before `--type`/`--status` narrow anything. That is deliberate (the code comment records that a fact computed post-filter reported `sv0sf3` as a typo under `-t plans`), and it means "matched but filtered to empty" is a clean empty result while "never matched" is a refusal. E-02 must not blur the two, and E-04's controls should keep at least one of these cases green so a future change cannot collapse them. |

## Proposed changes (ordered, validatable)

1. Re-drive the nine surfaces and both exemptions at the execution base, so every published sentence traces to a fresh measurement and any drift since authoring stops execution (E-01).
2. Amend `docs/cli-output-contract.md` Section 11.1 to state the standing-question versus named-artifact-assertion discriminator, the drift separation, and the list-mode STDERR rule, citing four symbols and naming `25kzda` as precedent with its scope limit; leave Section 12 to `hd5bkk` (E-02).
3. Pin the vocabulary exemption as a DERIVED property over ALL SIX contract sources (including the run-status table and the stripped `ABANDONED` token, which together contribute 19 tokens four sources alone would miss), plus the `TYPE_ALIASES` spellings, the end-to-end exit 0 in a drift-free repo, the `refusable` predicate, and case-insensitivity driven through the verb, with no count assertion (E-03).
4. Pin the five unpinned surfaces, the list-mode empty-STDOUT property, the two `--check` properties (no validity claim, no drift record), the schema validity of the `--check --agent` record, and the mixed-token case (E-04).
5. Append one dated `DECISIONS.md` entry recording the ratification, both rejected alternatives, and the relaxation route, plus one `CHANGELOG.md` line (E-05).
6. Verify: no en or em dash, bare suite with the summary pasted, the nine-surface matrix unchanged as the no-behavior-change proof, bare `--check --agent` exit code, sanitizer, and `aw ipd lint --phase pre-transition` (E-06).

## Deferred / out of scope (with reason)

- RELAXING THE CONTRACT (the item's own alternative branch). DEFERRED TO THE MAINTAINER, not dropped: OQ-01 carries it with the edit sites named and the cost measured. `fqnj8k`'s execution contract already said "do not guess a relaxation", and nothing measured here changes that; an agent choosing to relax would be substituting its own judgement for a maintainer's on an interactive verb's exit code.
  - Carrier: ahlgnm
- `aw find`'s ZERO-MATCH EXIT 0, and the consequent wrong claim in `docs/cli-output-contract.md` Section 12. Owned by backlog `hd5bkk` (`Work-Kind: bug`, `Blocks-Release: next`; `- Status: graduated` at review, not `open` as first written), which explicitly requires surveying every selector-taking read verb (including `aw ipd board`) in one pass, "since fixing one at a time is how the codebase ended up with three conventions". Correcting Section 12 here would pre-empt that decision (F-03).
  - Carrier: hd5bkk
- AMENDING SPEC `25kzda` to make Section 2.3 govern read verbs generally. Out of mandate: it is scoped to `aw oc run` / `aw agy run` (F-07), and widening it changes the contract every plan is reviewed against. If the maintainer wants one repository-wide zero-match rule, that is a spec change and belongs with `hd5bkk`'s survey, not with a ratification of one verb.
  - Carrier: hd5bkk
- THE `--dir`-AT-A-SUBDIRECTORY UNDER-REPORT (`0 artifacts shown`, exit 0, from a project subdirectory). Owned by backlog `5gmi12` (`- Status: open` at review). A genuinely different defect: the scan finds nothing because it looked in the wrong place, not because a selector matched nothing.
  - Carrier: 5gmi12
- THE MALFORMED-ARTIFACT INVISIBILITY, where a file too broken to parse is no `Item` on any surface. Owned by backlog `fyeg6a` (`- Status: graduated` at review, not `open` as first written). `fqnj8k` already stopped such a file being MISREPORTED as a typo (the match fact consults drift locations); making it an item is the remaining half and is that item's.
  - Carrier: fyeg6a
- THE UNSCANNED `roadmaps`/`walkthroughs` TREES, which is why those two tokens need a vocabulary exemption at all. Owned by backlog `rtbcok` (`- Status: graduated` at review, not `open` as first written). E-03 pins the exemption; it does not make those trees visible.
  - Carrier: rtbcok
- ANY CHANGE TO `agent_workflows/attention.py`. Deliberately excluded from `- Scope-Paths:`: this plan ratifies shipped behavior, so a production edit would contradict its own premise and would make E-06's no-behavior-change proof impossible.
  - Carrier-Declined: Nothing is owed by this plan. This is not deferred WORK but the plan's own defining constraint: there is no production defect here to hand onward, because the behavior in question already shipped and is what this plan ratifies. Naming a carrier would assert an outstanding code obligation that does not exist. The one genuinely outstanding question about that file's behavior is the relaxation, carried by `ahlgnm` on the first row above.

## Scope check

- Over-scope: none. Each of the four declared paths is touched by a named E-item: `docs/cli-output-contract.md` by E-02, `tests/test_attention.py` by E-03 and E-04, `DECISIONS.md` and `CHANGELOG.md` by E-05. No production module is declared or edited, which is the plan's central claim about itself and is proved by E-06 re-driving E-01's matrix unchanged.
- Under-scope: DELIBERATE AND NAMED. This plan does not DECIDE whether the contract should be fail-closed; it ratifies the shipped form and routes the overturn to OQ-01. A reviewer who believes the relaxation must happen in the same change as the documentation should say so, and the correct response is to retire this plan to `superseded/` in favor of a plan carrying the maintainer's answer, NOT to widen this one: the documentation and pins E-02 through E-04 write are exactly what a relaxation would have to update, so this plan lowers rather than raises the cost of the other branch.
- It is also under-scope by one deliberate omission worth flagging: the repository now has three published statements about zero-match exit codes (Section 11.1, Section 11.4, Section 12) and this plan reconciles only the first two. The third is `hd5bkk`'s (F-03).

## Required tests / validation

- `tests/test_attention.py`, extended (E-03, E-04): the vocabulary exemption over ALL SIX derivation sources (`TRACKED_TREES`, `ATTENTION_CLASSES`, `CLASS_MAPS`, `backlog.PRIORITIES`, `_RUN_STATUS_ALIASES` keys and values, and the stripped `run_viewer.ABANDONED` token) plus `TYPE_ALIASES`, the end-to-end exit 0 for an unmatched vocabulary token IN A DRIFT-FREE FIXTURE REPO (where 0 is the correct expectation; see F-01b), the `refusable` predicate's include/exclude behavior, case-insensitivity driven through the call path rather than by set membership (the returned set is lowercase-only, so `'REUSABLE' in vocab` is False while `attention.run` with `REUSABLE` exits 0 - measured at review, and a test asserting the former would pin the wrong thing); and the refusal on `--agent`, `--check`, `--check --agent`, `-id`, `--paths`, `--filenames`, with empty STDOUT on the three list modes, the absent validity sentence and absent drift record under `--check`, schema validity of the `--check --agent` record, and the mixed matched-plus-unmatched case. Behavior only; no source introspection; no vocabulary count.
- The existing pin must keep passing UNCHANGED: `tests/test_attention.py::SelectorNoMatchIsReportedTests::test_selector_no_match_is_reported`. This plan changes no behavior, so any movement in it is a real regression and must stop execution.
- At least one control asserting F-09's boundary stays green: a MATCHED token whose result is emptied by a downstream `--status` or `-t` filter still exits 0, so the refusal and the clean-empty cases cannot collapse into each other.
- The full suite BARE: `python3 -m pytest`, with a pre-change baseline recorded and the ACTUAL post-change summary line pasted.
- The nine-surface matrix re-driven after all edits and shown IDENTICAL to E-01's, which is the no-behavior-change proof.
- `python3 -m agent_workflows attention --check --agent` with no selector: exit code reported (expected 1 from pre-existing tree diagnostics, not from this plan), confirming the CI step is unaffected.
- `git diff docs/cli-output-contract.md CHANGELOG.md | grep -nP '[\x{2013}\x{2014}]'` printing nothing.
- `aw sanitize --agent; echo rc=$?` reporting rc 0.
- `aw ipd lint --phase pre-transition` conforming with zero findings.

## Spec / documentation sync

- NO `.spec.md` FILE IS AMENDED and none is declared in `- Scope-Paths:`. That is a checked judgement, not an omission. The spec that speaks to this behavior, `25kzda`, is scoped to `aw oc run` / `aw agy run` (F-07) and is cited here as PRECEDENT; amending it to govern every read verb would change the contract every other plan is reviewed against, and would pre-empt `hd5bkk`'s required survey. No spec states the `aw attention` verb's own output contract, which is exactly the gap E-02 fills in `docs/` instead.
- `docs/cli-output-contract.md` IS AMENDED, and the amendment is a CORRECTION rather than an addition: Section 11.1 currently mandates behavior the shipped verb does not have (F-02), so leaving it while adding a new section would leave the repository publishing two contradictory rules and would let a future reviewer cite the wrong one in good faith. Section 12's separate wrong claim about `aw find` is deliberately left to `hd5bkk` (F-03), and E-02's expected outcome requires that file region to show no diff.
- `DECISIONS.md` gains one appended entry (E-05) and nothing in it is rewritten (append-only; GUIDING_PRINCIPLES P4). `CHANGELOG.md` gains one line. Both are user-facing prose and carry no em or en dashes.

## Open questions

### OQ-01: Does the maintainer ratify the fail-closed no-match contract, or relax it now that it has been lived with for over a week?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: ahlgnm
- Resolution or deferral rationale: THIS IS THE QUESTION BACKLOG `ahlgnm` EXISTS TO CARRY, and it is non-blocking because the plan is executable either way: the documentation, the pins, and the decision entry are all things a relaxation would need too, so nothing here is wasted if the answer is "relax". THE PLAN PROCEEDS ON RATIFICATION, for the reason `fqnj8k` gave and this plan re-verified: the fail-closed form shipped at the approved plan's own direction, it behaves exactly as recorded (F-01), the two exemptions keep correct usage exit 0, and CI is untouched (F-08), so there is no measured harm on the table, only an anticipated annoyance. WHAT THE MAINTAINER GIVES UP BY RATIFYING: a shell prompt or script that already treats a nonzero `aw attention` as "the repository is broken" now also sees nonzero for a typo, on a verb used interactively many times a day. WHAT RELAXATION WOULD COST, stated so the choice is costed rather than vibed: `attention.EXIT_UNRESOLVED_SELECTOR` plus the single `--check` branch, plus the pins E-03 and E-04 add (which is the intended cost of a pin and the reason a relaxation would then be deliberate and visible rather than half-landed, which F-04 shows is today's actual risk). If the answer is "relax", the correct response is to retire this plan to `superseded/` in favor of one carrying that answer, not to edit this one mid-flight.

### OQ-02: Should `docs/cli-output-contract.md` Section 11.1 gain the discriminator, or should the attention contract be stated in a new section that Section 11.1 points at?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: RESOLVED IN FAVOR OF AMENDING SECTION 11.1, decidable from repository evidence and so not a maintainer question. Section 11.1's text is a MANDATE over "a query, find, search, or list verb", and `aw attention` with a selector is unambiguously in that class, so a new section stating the opposite would leave two live contradictory rules with no precedence between them, which is the F-02 defect duplicated rather than fixed. The discriminator also is not attention-specific: it is `25kzda` Section 2.4a's own reasoning, already implemented by `aw runs` as well, so it belongs in the general convention. E-02 therefore amends 11.1 and adds no parallel section. NOTE the deliberate limit: amending 11.1 makes it correct about the ASSERTION versus STANDING-QUESTION split, and it does NOT make `aw find` conform (F-03); the document will still describe a `find` behavior that does not exist until `hd5bkk` resolves, and E-02's expected outcome requires Section 12 to stay untouched so that remains visibly someone else's open work rather than silently papered over.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL commands and their exit codes for all nine surfaces with a non-vocabulary unmatched token, showing for each whether the diagnostic landed on STDOUT or STDERR, and showing a measured BYTE COUNT of STDOUT for `-id`, `--paths` and `--filenames` (must be 0). For the two EXEMPTION classes (bare invocation, and at least four vocabulary tokens from four different derivation sources) paste, for each, the exit code AND the machine record's `outcome`, in BOTH the live tree and a throwaway drift-free repository; the pass condition is `outcome` never `cannot-run` and `unresolved_selectors` absent, NOT a literal exit 0, because a drifty tree legitimately returns 1 here (F-01b). Paste the mixed matched-plus-unmatched invocation's record. Paste the output of validating one emitted record through `agent_schema.assert_valid_agent_record`. State explicitly whether every REFUSAL row agrees with F-01; if a refusal row disagrees, the item FAILS and execution stops. An exemption row at exit 1 with `outcome: findings` is expected in a drifty tree and is not a failure; say so rather than stopping.
  - Observed evidence: PASS. All nine surfaces and exemption classes measured:
    Commands executed at execution base:
    ```
    human board      | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    --agent          | exit: 2 | stream: STDOUT | stdout bytes:    377 | stderr bytes:      0
    --json           | exit: 2 | stream: STDOUT | stdout bytes:    419 | stderr bytes:      0
    --format json    | exit: 2 | stream: STDOUT | stdout bytes:    419 | stderr bytes:      0
    --check          | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    --check --agent  | exit: 2 | stream: STDOUT | stdout bytes:    377 | stderr bytes:      0
    -id              | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    --paths          | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    --filenames      | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    ```
    List mode STDOUT byte count measured exactly 0 bytes on -id, --paths, and --filenames.
    Every REFUSAL row agrees with F-01 (exit 2 across all nine surfaces; list modes empty stdout).

    Exemptions in live tree vs. drift-free repository (_attsel_repo fixture):
    ```
    === LIVE TREE (drifty repository) ===
    bare (live)                      | exit: 1 | outcome: N/A      | unres in rec: N/A
    bare --agent (live)              | exit: 1 | outcome: findings | unres in rec: False
    reusable --agent (live, tree)    | exit: 0 | outcome: clean    | unres in rec: False
    ready --agent (live, class)      | exit: 0 | outcome: clean    | unres in rec: False
    shipped --agent (live, status)   | exit: 0 | outcome: clean    | unres in rec: False
    abandoned --agent (live, run)    | exit: 0 | outcome: clean    | unres in rec: False

    === DRIFT-FREE REPOSITORY ===
    bare (drift-free)                | exit: 0 | outcome: N/A      | unres in rec: N/A
    bare --agent (drift-free)        | exit: 0 | outcome: clean    | unres in rec: False
    reusable --agent (drift-free)    | exit: 0 | outcome: clean    | unres in rec: False
    ready --agent (drift-free)       | exit: 0 | outcome: clean    | unres in rec: False
    shipped --agent (drift-free)     | exit: 0 | outcome: clean    | unres in rec: False
    abandoned --agent (drift-free)   | exit: 0 | outcome: clean    | unres in rec: False
    ```
    Bare invocation exit 1 in live tree is expected from 9 pre-existing lane diagnostics (F-01b); outcome is `findings` and `unresolved_selectors` is absent (never `cannot-run`). All vocabulary tokens exit 0 with `outcome: clean`.

    Mixed matched-plus-unmatched invocation:
    `python3 -m agent_workflows attention ahlgnm zzzzzz --agent`
    Exit code: 2
    Record: `{"schema": "aw.agent/v1", "kind": "error", "cmd": "attention", "outcome": "cannot-run", "exit": 2, "verified": false, "complete": false, "findings": 1, "unresolved_selectors": ["zzzzzz"], "unresolved_targets": ["zzzzzz"], "error": "no artifact matched selector 'zzzzzz'; searched the tracked record trees backlog, plans, prompts, releases, research, specs", "next": "aw next", "matched_selectors": ["ahlgnm"]}`
    `matched_selectors`: `["ahlgnm"]`
    `unresolved_selectors`: `["zzzzzz"]`

    Schema validation via `agent_schema.assert_valid_agent_record`:
    Record validated with zero assertion errors on both mixed record and single-selector refusal record.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff docs/cli-output-contract.md`. Show that Section 11.1 no longer mandates exit 0 for the named-artifact-assertion case, that the standing-question versus assertion discriminator appears exactly once, that the drift-separation property is stated, and that the list-mode STDERR rule appears WITH its pipe-corruption reason. Show that the EXEMPT side is worded as NOT REFUSED rather than as a flat "exits 0", and that the amendment says a concurrent drift finding still reports itself, so the document does not publish a claim a drifty repository falsifies (F-01b); quote the sentence. Show the four cited symbols (`attention.EXIT_UNRESOLVED_SELECTOR`, `attention.selector_vocabulary`, `attention.SelectorMatchFacts.refusable`, `run_viewer.emit_unresolvable_target_refusal`) present in the diff. Show `25kzda` named as precedent WITH the sentence limiting its scope to the runner verbs. Prove Section 12 is untouched by showing the diff contains no hunk in that region. Paste `git diff docs/cli-output-contract.md | grep -nP '[\x{2013}\x{2014}]'` producing empty output.
  - Observed evidence: PASS. git diff on docs/cli-output-contract.md verified:
    `git diff docs/cli-output-contract.md`:
    ```diff
    diff --git a/docs/cli-output-contract.md b/docs/cli-output-contract.md
    index 6ab565c5b..b0ec09358 100644
    --- a/docs/cli-output-contract.md
    +++ b/docs/cli-output-contract.md
    @@ -345,13 +345,23 @@ mutation feedback, and error states across all `aw` verbs.

     ### 11.1 Empty Result Convention (Read and List Verbs)
     When a query, find, search, or list verb matches zero records or produces an empty result set:
    -- **Never Fail Silently / Blank**: The handler MUST NOT print blank output or an uninformative raw string.
    -- **Interactive Human TTY**: Handlers MUST use `Term.empty_result(summary, filters=..., next_action=...)`.
    +- **Discriminator (Standing Question vs. Named-Artifact Assertion)**:
    +  The convention distinguishes between two kinds of zero-match requests:
    +  - **Standing questions about repository state**: A query asking about a category of artifacts (a tree name, an attention class, an artifact status, a priority, a run state, or a bare invocation with no selector at all) is a standing question. A zero-match result indicates the repository currently has zero artifacts in that state; this is a clean empty result and is **not refused**.
    +  - **Assertions that a named artifact exists**: A query specifying an artifact identifier (an id6, a setid, or a filename fragment) asserts that a specific artifact exists. If that selector matches zero records, the invocation is treated under Section 11.4 as an unresolved selector refusal and exits 2 (`attention.EXIT_UNRESOLVED_SELECTOR`) with `outcome: "cannot-run"`, `verified: false`, and `complete: false`.
    +- **Precedent and Scope**:
    +  Spec `25kzda` Sections 2.3 and 2.4a established the precedent for this distinction, observing that an empty status query such as `reviews` matching nothing is a successful answer rather than an error, while a misspelled id6 exits 2. Spec `25kzda` specifically governs the runner verbs `aw oc run` and `aw agy run` rather than read verbs generally, so its status-selector carve-out serves as precedent rather than a binding contract. The read verb `aw attention` follows and extends this pattern by deriving its exempt vocabulary via `attention.selector_vocabulary` and evaluating `attention.SelectorMatchFacts.refusable`, following the shipped precedent in `run_viewer.emit_unresolvable_target_refusal`.
    +- **Not Refused vs. Exit Codes (Drift Separation)**:
    +  The standing-question exemption is worded as **not refused** rather than flatly "exits 0". The exemption skips the refusal predicate, after which the verb's ordinary exit classification still applies. In a repository without drift or findings, the exempt query yields `outcome: "clean"` with exit 0. However, if the repository concurrently contains contract drift or policy violations, a concurrent drift finding still reports itself normally and exits 1 through the drift path. Conversely, a selector refusal is a separate condition from a contract finding: it neither appends a drift record nor flips the `--json` `valid` flag, ensuring an operator typo is never misreported as repository damage.
    +- **List-Mode Stream Rule (Pipe Safety)**:
    +  For list modes targeting machine ingestion (`-id`, `--paths`, `--filenames`), a selector refusal emits its diagnostic message to `stderr` while `stdout` remains strictly empty (0 bytes). This prevents error text from corrupting shell pipes or downstream tool consumers.
    +- **Never Fail Silently / Blank**: For non-refused empty results, the handler MUST NOT print blank output or an uninformative raw string.
    +- **Interactive Human TTY**: For non-refused empty queries, handlers MUST use `Term.empty_result(summary, filters=..., next_action=...)`.
       The render displays:
       1. Outcome line with clean status (e.g. `✓ CLEAN  no matching <type>`).
       2. `Active filters:` section echoing all applied selectors, types, sets, or flags.
       3. `Next` recommendation offering a broadening query (e.g. searching without selectors) or helpful navigation.
    -- **Agent Protocol (`aw.agent/v1`)**: The handler MUST emit a structured `result` (or `summary`) record with:
    +- **Agent Protocol (`aw.agent/v1`)**: For non-refused empty queries, when nothing else is wrong, the handler MUST emit a structured `result` (or `summary`) record with:
       - `outcome: "clean"`, `exit: 0`, `findings: 0`, `verified: true`, `complete: true`.
       - Evidence/data carrying the zero count and active filter dictionary.
       - `next`: the suggested broadening or fallback command.
    ```

    Verification points:
    - Section 11.1 no longer mandates exit 0 for named-artifact-assertion: it specifies exit 2 (`attention.EXIT_UNRESOLVED_SELECTOR`) with `outcome: "cannot-run"`.
    - Discriminator appears once under `Discriminator (Standing Question vs. Named-Artifact Assertion)`.
    - Drift separation property is stated explicitly.
    - List-mode stream rule appears with pipe-corruption reason.
    - Exempt side worded as "not refused": "The standing-question exemption is worded as **not refused** rather than flatly "exits 0". The exemption skips the refusal predicate, after which the verb's ordinary exit classification still applies. In a repository without drift or findings, the exempt query yields `outcome: "clean"` with exit 0. However, if the repository concurrently contains contract drift or policy violations, a concurrent drift finding still reports itself normally and exits 1 through the drift path."
    - All four symbols cited: `attention.EXIT_UNRESOLVED_SELECTOR`, `attention.selector_vocabulary`, `attention.SelectorMatchFacts.refusable`, `run_viewer.emit_unresolvable_target_refusal`.
    - Spec `25kzda` cited as precedent with scope limitation: "Spec `25kzda` specifically governs the runner verbs `aw oc run` and `aw agy run` rather than read verbs generally, so its status-selector carve-out serves as precedent rather than a binding contract."
    - Section 12 is untouched: no diff hunks in lines 388-396.
    - `git diff docs/cli-output-contract.md | grep -nP '[\x{2013}\x{2014}]'` returned empty (exit 1).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the narrowed test run (`python3 -m pytest tests/test_attention.py -k <vocabulary test selector> -o addopts=""`) with its pass line. Then prove each assertion BITES rather than merely passing. DO THIS BY PATCHING THE SOURCE SYMBOL IN MEMORY (`unittest.mock.patch.object` over `attention_contract.CLASS_MAPS`, `attention.TYPE_ALIASES`, `backlog.PRIORITIES`, or `attention._RUN_STATUS_ALIASES`), NOT by editing `agent_workflows/attention.py`: the file is outside `- Scope-Paths:`, the gate forbids changing it, and an in-memory patch proves the same property without ever writing to it.
    CHOOSE A SOURCE THAT ACTUALLY BITES, and verify the choice rather than assuming it. MEASURED at review (PR-903): emptying `TRACKED_TREES` changes the vocabulary by ZERO tokens, because every tree name is independently contributed by `TYPE_ALIASES`, so a bite-test on that source PASSES AGAINST A BROKEN SUBJECT and proves nothing. Measured deltas from a 74-token baseline: `TRACKED_TREES` 0, `ATTENTION_CLASSES` 1 (only `ready` is unique to it), `PRIORITIES` 3, `TYPE_ALIASES` 16, `CLASS_MAPS` 22. So use `CLASS_MAPS` or `TYPE_ALIASES` for a bite that cannot be mistaken, and if a per-source assertion is written for `TRACKED_TREES` state explicitly that the redundancy makes it a coverage assertion rather than a bite test. Also show the `refusable` bite: make it treat a vocabulary token as refusable (again by patching, on a constructed `SelectorMatchFacts`) and show that assertion fails.
    Then paste `git diff --stat agent_workflows/attention.py` showing EMPTY, since this plan must change no production file. Also paste the measured `len(attention.selector_vocabulary())` and confirm NO test asserts that number.
  - Observed evidence: PASS. Narrowed test run and in-memory bite tests verified:
    Narrowed test run:
    `python3 -m pytest tests/test_attention.py -k SelectorVocabulary -o addopts="" -v`
    ```
    tests/test_attention.py::SelectorVocabularyExemptionTests::test_selector_match_facts_refusable PASSED [ 20%]
    tests/test_attention.py::SelectorVocabularyExemptionTests::test_unmatched_vocabulary_token_exits_clean_in_drift_free_repo PASSED [ 40%]
    tests/test_attention.py::SelectorVocabularyExemptionTests::test_vocabulary_includes_type_aliases PASSED [ 60%]
    tests/test_attention.py::SelectorVocabularyExemptionTests::test_vocabulary_derives_from_all_six_sources PASSED [ 80%]
    tests/test_attention.py::SelectorVocabularyExemptionTests::test_case_insensitivity_via_call_path PASSED [100%]
    ====================== 5 passed, 48 deselected in 2.05s =======================
    ```

    Bite test results (via in-memory mocking, without touching `agent_workflows/attention.py`):
    - `CLASS_MAPS` (measured delta: 22 tokens): patching `att.A.CLASS_MAPS` to `{}` during derivation causes `test_vocabulary_derives_from_all_six_sources` to fail with:
      `AssertionError: 'draft' not found in frozenset(...) : CLASS_MAPS token draft missing from vocabulary`
    - `TYPE_ALIASES` (measured delta: 16 tokens): patching `att.TYPE_ALIASES` to `{}` during derivation causes `test_vocabulary_includes_type_aliases` to fail with:
      `AssertionError: 'plan' not found in frozenset(...) : TYPE_ALIASES key plan missing from vocabulary`
    - `ATTENTION_CLASSES` (measured delta: 1 token): patching `att.A.ATTENTION_CLASSES` to `()` during derivation causes `test_vocabulary_derives_from_all_six_sources` to fail with:
      `AssertionError: 'ready' not found in frozenset(...) : ATTENTION_CLASSES token ready missing from vocabulary`
    - `PRIORITIES` (measured delta: 3 tokens): patching `backlog.PRIORITIES` to `()` during derivation causes `test_vocabulary_derives_from_all_six_sources` to fail with:
      `AssertionError: 'high' not found in frozenset(...) : PRIORITIES token high missing from vocabulary`
    - `_RUN_STATUS_ALIASES` (measured delta: 18 tokens): patching `att._RUN_STATUS_ALIASES` to `{}` during derivation causes `test_vocabulary_derives_from_all_six_sources` to fail with:
      `AssertionError: 'substantially-complete' not found in frozenset(...) : _RUN_STATUS_ALIASES key substantially-complete missing from vocabulary`
    - `run_viewer.ABANDONED` (measured delta: 1 token): removing `abandoned` from derived set causes `test_vocabulary_derives_from_all_six_sources` to fail with:
      `AssertionError: 'abandoned' not found in frozenset(...) : run_viewer.ABANDONED token abandoned missing from vocabulary`
    - `TRACKED_TREES` (measured delta: 0 tokens): redundant with `TYPE_ALIASES`, tested as coverage assertion.
    - `SelectorMatchFacts.refusable` bite: constructed `SelectorMatchFacts` with empty vocabulary treats `reusable` as refusable, causing `assert "reusable" not in smf.refusable` to raise `AssertionError`.

    Production code check:
    `git diff --stat agent_workflows/attention.py` output is strictly EMPTY.

    Vocabulary size check:
    `len(attention.selector_vocabulary())` is 74. Confirmed no test asserts 74.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the narrowed test run covering the surface tests with its pass line, and paste the list of test names so a reviewer can see all nine surfaces are named rather than three. Show the list-mode tests asserting STDOUT is exactly empty (quote the assertion). Show the `--check` tests asserting BOTH that `aw attention --check: the view is valid.` is absent AND that no drift or violation record was appended. Show the `--check --agent` test routing its record through `agent_schema.assert_valid_agent_record`. Paste the run of the PRE-EXISTING `test_selector_no_match_is_reported` showing it still passes unmodified, and paste the F-09 control (matched token emptied by a downstream filter) showing exit 0.
  - Observed evidence: PASS. Nine surfaces and control tests passed:
    Narrowed test run:
    `python3 -m pytest tests/test_attention.py -k SelectorNoMatch -o addopts="" -v`
    ```
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_surface_check_no_match PASSED [ 10%]
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_surface_json_no_match PASSED [ 20%]
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_downstream_filter_emptied_match_exits_clean PASSED [ 30%]
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_surface_paths_list_mode_no_match PASSED [ 40%]
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_surface_agent_no_match PASSED [ 50%]
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_selector_no_match_is_reported PASSED [ 60%]
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_surface_mixed_matched_and_unmatched PASSED [ 70%]
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_surface_filenames_list_mode_no_match PASSED [ 80%]
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_surface_id_list_mode_no_match PASSED [ 90%]
    tests/test_attention.py::SelectorNoMatchIsReportedTests::test_surface_check_agent_no_match PASSED [100%]
    ====================== 10 passed, 43 deselected in 2.21s =======================
    ```

    All nine surfaces covered:
    1. Human board: `test_selector_no_match_is_reported`
    2. `--agent`: `test_surface_agent_no_match`
    3. `--json`: `test_surface_json_no_match`
    4. `--format json`: `test_selector_no_match_is_reported`
    5. `--check`: `test_surface_check_no_match`
    6. `--check --agent`: `test_surface_check_agent_no_match`
    7. `-id`: `test_surface_id_list_mode_no_match`
    8. `--paths`: `test_surface_paths_list_mode_no_match`
    9. `--filenames`: `test_surface_filenames_list_mode_no_match`

    List-mode tests asserting STDOUT is exactly empty:
    `self.assertEqual(out, "")` quoted from `test_surface_id_list_mode_no_match`, `test_surface_paths_list_mode_no_match`, and `test_surface_filenames_list_mode_no_match`.

    `--check` and `--check --agent` non-validity and drift separation:
    - `self.assertNotIn("aw attention --check: the view is valid.", err)`
    - `self.assertNotIn("aw attention --check: the view is valid.", out)`
    - `self.assertNotIn("drift", err.lower())`
    - `self.assertNotIn("the view is valid.", out)`
    - `self.assertNotIn("diagnostics", payload)`

    `--check --agent` schema routing:
    `agent_schema.assert_valid_agent_record(payload)` called and passed.

    Pre-existing test passed unmodified:
    `test_selector_no_match_is_reported PASSED`

    F-09 control passed:
    `test_downstream_filter_emptied_match_exits_clean PASSED` (exits 0 with `0 artifacts shown`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the appended `DECISIONS.md` entry in full. Show it uses the next unused `D<N>` integer (paste the `rg '^### D[0-9]+' DECISIONS.md | tail -3` that establishes it), carries all three of `- **Context:**`, `- **Decision:**` and `- **Applied:**`, names BOTH rejected alternatives with their reasons, and names the relaxation route. Prove nothing pre-existing was rewritten: paste `git diff DECISIONS.md` and show it is purely additive (no deleted lines). Paste the one added `CHANGELOG.md` line and `git diff CHANGELOG.md` showing exactly one insertion. Paste the en/em dash grep over both files producing empty output.
  - Observed evidence: PASS. D157 appended to DECISIONS.md and line added to CHANGELOG.md:
    Next integer established via `rg '^### D[0-9]+' DECISIONS.md | tail -3`:
    ```
    DECISIONS.md:2572:### D154. Every live bug blocks the next release, and inefficiency a user can NOTICE is a bug, so both rulings are written down instead of re-derived per session
    DECISIONS.md:2580:### D155. Four-case installer section consent (self-heal stale manifest hashes, preserve unrecorded user drift, warn on held-back sections)
    DECISIONS.md:2591:### D156. Executed plans: never rewrite the record, but a dated pointer line may be appended (narrows D69)
    ```
    Next unused entry integer is D157.

    Appended `DECISIONS.md` entry:
    ```markdown
    ### D157. Ratify the aw attention no-match exit contract (fail-closed exit 2 on named-artifact assertions, exempt standing questions)

    - **Context:** Executed plan `fqnj8k` (2026-09-21) shipped fail-closed exit 2 behavior for unmatched selectors on `aw attention`. Backlog `ahlgnm` carried OQ-01 and OQ-02 forward for ratification rather than design. Authoring and execution verified the shipped behavior on all nine surfaces (exit 2 for unmatched non-vocabulary selectors; diagnostic on stderr for human board, `--check`, and list modes; clean empty 0-byte stdout on `-id`, `--paths`, `--filenames`; exit 2 machine record on `--agent`, `--json`, `--format json`, and `--check --agent`). The investigation revealed that `docs/cli-output-contract.md` Section 11.1 contradicted this by mandating exit 0 for empty queries without distinguishing assertions from standing questions, and the derived vocabulary exemption mechanism had zero test coverage across its six sources.
    - **Decision:** The fail-closed exit 2 contract is ratified by the approval and execution of plan `o6ksmw` (OQ-01 remains the maintainer route for any future relaxation). The discriminator is established between a standing question about repository state (a tree name, attention class, artifact status, priority, run state, or bare invocation) which is not refused, and an assertion that a named artifact exists (an id6, setid, or filename fragment) which exits 2 (`attention.EXIT_UNRESOLVED_SELECTOR`) with `outcome: "cannot-run"`. The bare invocation and vocabulary exemptions are ratified parts of the contract rather than concessions. Two alternatives were rejected: (1) folding into exit 1 drift code, rejected because `agent_schema` parity forbids `exit: 1` with `cannot-run`, would misreport a typo as repository damage, and would be indistinguishable from contract violations; (2) exit 0 with a message only (`aw find` convention), rejected because downstream scripts querying an artifact by id6 and receiving exit 0 with empty output conclude nothing is wrong or nothing to do. If a future relaxation is chosen, the relaxation route is straightforward: update `attention.EXIT_UNRESOLVED_SELECTOR` and the single `--check` refusal branch in `agent_workflows/attention.py`, and update the pins in `tests/test_attention.py`.
    - **Applied:** `docs/cli-output-contract.md` (amended Section 11.1 with discriminator, drift separation, pipe safety, and symbol citations); `tests/test_attention.py` (pinned all nine surfaces, list-mode clean stdout, `--check` non-validity, schema compliance, mixed selectors, and derived vocabulary over all six contract sources); `DECISIONS.md` (this entry); `CHANGELOG.md` (one line). Executed per IPD `o6ksmw` (Set `attselratify`, Order 01, backlog `ahlgnm`).
    ```

    `git diff DECISIONS.md` is purely additive (+9 lines, -0 lines).

    `git diff CHANGELOG.md` shows exactly one insertion:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 6403de993..5a36caae0 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Added: ratified and published the `aw attention` fail-closed no-match exit contract in `docs/cli-output-contract.md`, distinguishing standing questions from named-artifact assertions, and pinned all nine surfaces plus derived vocabulary exemption sources in `tests/test_attention.py` (D157).
     - Fixed: `aw attention` now emits a degraded blocked item for a malformed artifact failing its status parse, allowing every CLI surface to name and select it while preserving drift violations.
    ```

    Dash check:
    `git diff docs/cli-output-contract.md CHANGELOG.md DECISIONS.md | grep -nP '[\x{2013}\x{2014}]'` returned empty (exit 1).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the pre-change baseline suite summary line and the post-change BARE `python3 -m pytest` summary line, and state the delta with the reason (the tests E-03/E-04 added). RE-DERIVE the baseline at the executing HEAD rather than trusting a count from this plan or from another plan's review: it was `3371 passed, 2 skipped` at review HEAD `c1cacc29` and it moves with unrelated work, so treat that as context and not as the bar. Any NEW failure fails this item. Paste the re-driven nine-surface matrix and state explicitly that every REFUSAL row's exit code is identical to V-01's, naming that as the no-behavior-change proof, and explain any exemption-row difference as tree drift rather than behavior change (F-01b); paste `git diff --stat` showing that the only changed files are the four in `- Scope-Paths:` and that no `agent_workflows/*.py` appears. Paste `python3 -m agent_workflows attention --check --agent` (no selector) with its exit code. Paste `aw sanitize --agent; echo rc=$?` showing rc 0. Paste the `aw ipd lint --phase pre-transition` conformance line with zero findings.
  - Observed evidence: PASS. Suite runs, re-driven matrix, and checks verified:
    Pre-change baseline suite summary line:
    `3902 passed, 2 skipped, 3 warnings in 77.79s (0:01:17)`

    Post-change bare `python3 -m pytest` summary line:
    `3916 passed, 2 skipped, 3 warnings in 78.59s (0:01:18)`

    Delta: +14 passed tests, exactly accounting for the 14 new tests added by E-03 and E-04 (9 surface/filter tests and 5 vocabulary tests).

    Re-driven nine-surface matrix:
    ```
    human board      | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    --agent          | exit: 2 | stream: STDOUT | stdout bytes:    377 | stderr bytes:      0
    --json           | exit: 2 | stream: STDOUT | stdout bytes:    419 | stderr bytes:      0
    --format json    | exit: 2 | stream: STDOUT | stdout bytes:    419 | stderr bytes:      0
    --check          | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    --check --agent  | exit: 2 | stream: STDOUT | stdout bytes:    377 | stderr bytes:      0
    -id              | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    --paths          | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    --filenames      | exit: 2 | stream: STDERR | stdout bytes:      0 | stderr bytes:    227
    ```
    Every REFUSAL row's exit code is identical to V-01's (exit 2 across all nine surfaces; list modes empty stdout). This serves as the no-behavior-change proof.

    CI invocation check:
    `python3 -m agent_workflows attention --check --agent` (no selector)
    Exit code: 1
    Output: `{"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":9,"evidence":["attention"],"diagnostics":[{"location":"aw/lane/3brgb6","rule":"attention.lane-superseded"},...],"next":null}`
    Exit code 1 reflects 9 pre-existing repository lane diagnostics and confirms the CI invocation is untouched by this plan.

    Sanitizer check:
    `aw sanitize --agent; echo rc=$?`
    Output:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    `rc=0`

    Scope check:
    `git diff --stat` confirms only the Scope-Paths files and this plan are touched, with no `agent_workflows/*.py` appearing.

    IPD lint check:
    `aw ipd lint --phase pre-transition` passes conforming with zero findings.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the four files named in `- Scope-Paths:`, through `aw commit o6ksmw -- <paths>`; never `git add -A`, never `git commit -a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change with `git restore --staged <path>`; other agents and humans may be working in this checkout concurrently. If a raw `git commit` is ever attempted and a hook rejects it, RE-VERIFY the staged set before retrying, since `pre-commit`'s stash restore can leave paths you never staged in the index.

THIS PLAN MUST CHANGE NO PRODUCTION BEHAVIOR, and that is a gate rather than an aspiration. `agent_workflows/attention.py` is deliberately absent from `- Scope-Paths:`. If execution concludes the contract cannot be published or pinned without a production edit, STOP and report rather than widening scope: that conclusion means the ratification question has changed and the maintainer needs to see it. THE PRODUCTION FILE IS NEVER EDITED, NOT EVEN TEMPORARILY: V-03's bite tests are performed by patching the source symbols IN MEMORY with `unittest.mock.patch.object`, which proves the same property without writing to a file outside `- Scope-Paths:` (an earlier wording invited a temporary edit-and-restore, which is a needless window in which a crash or an interrupted turn leaves a modified production file behind). `git diff --stat agent_workflows/attention.py` must be empty at every point, not merely at the end.

DO NOT WRITE AN ATTESTATION FIELD THIS PLAN HAS NOT EARNED. Specifically, neither the AUTHOR nor the EXECUTOR may add or alter a `- Readiness:` line: that field is an OUTPUT of `/plan-review` and its absence is the correct, silent, fail-closed state for an authored plan (AGENTS.md; `aw ipd lint` refuses an unattested value at `IPD-M107`). It was absent through authoring, as required, and was written by `/plan-review` on 2026-09-30 as that workflow's own attested output; that is the one legitimate way it may appear, and an executor must still not touch it. E-05's `DECISIONS.md` entry records a ratification made BY THIS PLAN'S APPROVAL and must not be phrased as a human attestation the maintainer has not given; OQ-01 remains their route to overturn it.

POST-GATE LIFECYCLE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and EVERY `V-*` item carries concrete pasted evidence, including the actual suite summary line. Backlog item `ahlgnm` goes to `graduated` and NOT `done` when this plan is handed off; it closes `done` only once this plan has executed, since the ratification it asks for is recorded by E-05 and not by authoring.
