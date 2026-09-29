# IPD: Make aw find refuse a zero-match selector with exit 2, exempting standing vocabulary questions

- Date: 2026-09-29
- Kind: child
- Concern: `aw find <type> <selector>` reports a selector that matches NO artifact as a CLEAN SUCCESS, so a caller cannot tell a typo from a genuinely empty tree. Measured at HEAD `1f62764b`: `aw find plans zzzzzz` prints `✓ CLEAN  no matching plans` with the token echoed under `Active filters:` and exits 0; `--agent` emits `{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`, which is the same record a successful query emits; `--json` emits `status:clean, exit_code:0`. A script that resolves an id6 through `aw find` and reads exit 0 with an empty result concludes "nothing to do", which is the wrong conclusion. THE DIVERGENCE IS THREE-WAY, NOT TWO-WAY, and that is worse than the backlog item knew: `--paths` already exits **1** on the same zero match (`cli.py` `return 0 if (all_paths or not selectors) else 1`), so ONE verb ships three different answers to one question across its four surfaces (0 human, 0 `--agent`, 0 `--json`, 1 `--paths`). Spec `25kzda` Section 2.3 rules "Zero matches return exit 2" and Section 2.4a exempts status selectors only, closing "A misspelled id6 still exits 2; only the status selectors are exempt". `aw runs` implements that; `aw attention` implements it as of `fqnj8k`. `aw find` is the remaining holdout.
- Scope: Make `aw find` distinguish NO-MATCH from LEGITIMATELY-EMPTY on all four of its output surfaces (human, `--agent`, `--json`, `--paths`/`-p`), refusing a non-vocabulary zero-match at exit 2 and keeping a standing vocabulary question at exit 0, reusing `attention.selector_vocabulary()` plus `find`'s own type and status symbols. Reconciles the two CONFLICTING normative rules this change would otherwise violate in `docs/cli-output-contract.md`, and corrects the worked zero-match example in `docs/cli-agent-protocol.md`. Surveys the remaining selector-taking read verbs and reports. Does NOT change which artifacts match, the selector precedence, the row format, the unfiltered-listing exit code, or any other verb's behavior.
- Scope-Paths: agent_workflows/cli.py, tests/test_cli_find.py, docs/cli-output-contract.md, docs/cli-agent-protocol.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: hd5bkk
- Blocks-Release: next
- Set: selquiet
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: zyj8io

## Workflow history

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog item `hd5bkk`, graduating it. Every claim below was MEASURED in this lane at HEAD `1f62764b`, not read off the backlog item. Three facts were found that the item did not state and that change the shape of the fix. FIRST, the divergence is THREE-WAY within `aw find` itself: `--paths` exits 1 where the other three surfaces exit 0, so the fix must unify four surfaces rather than change one exit code. SECOND, `docs/cli-output-contract.md` carries two MUTUALLY CONTRADICTORY normative rules about exactly this case - Section 11.1 mandates `exit: 0` with `outcome: "clean"` for an empty read/list result, while Section 12 mandates "If a specific selector matches zero paths, the command exits `1`" - so the current code is simultaneously compliant and non-compliant with its own contract, and any fix must resolve the conflict rather than silently break one half. THIRD, `attention.selector_vocabulary()` is reusable but NOT sufficient alone: measured, it omits three tokens `find` legitimately accepts (`reviews` and `other`, which are members of `artifact_types.ARTIFACT_TYPES`, and `intake`, a research status), so reusing it unmodified would newly call three valid queries typos. `aw ipd board` was surveyed and takes NO positional selector (argparse rejects it: `unrecognized arguments: zzzzzz`), so it is measured out of scope rather than assumed in.

## Goal

Make `aw find` answer the question it was asked. When a caller names an artifact, they are asserting it
exists; if it does not, that is the answer and it must not be spelled the same way as "this tree is
empty". Bring the verb onto the one exit convention the repository already ruled for selector-resolving
verbs (`25kzda` Section 2.3/2.4a), which `aw runs` and `aw attention` already implement, and keep
legitimate standing questions like `aw find plans reusable` a quiet success.

FOUR FACTS ESTABLISHED AT AUTHORING, so the executor does not re-derive them and does not inherit a
premise that measurement has already falsified.

1. THE VERB DISAGREES WITH ITSELF ACROSS ITS OWN SURFACES. Measured at HEAD `1f62764b`:

   ```text
   $ aw find plans zzzzzz            -> "✓ CLEAN  no matching plans", exit 0
   $ aw find plans zzzzzz --agent    -> outcome:clean, exit:0, findings:0, verified:true
   $ aw find plans zzzzzz --json     -> status:clean, exit_code:0
   $ aw find plans zzzzzz --paths    -> (no stdout), exit 1
   ```

   So this is not "change 0 to 2 in one place". The single `return 0 if (all_paths or not selectors)
   else 1` in `cli._run_find` is the `--paths` answer, and the `CommandResult(status="clean",
   exit_code=0, ...)` a few lines below it is the answer for the other three.

2. A VOCABULARY TOKEN CAN LEGITIMATELY MATCH NOTHING, AND ONE DOES IN THIS REPOSITORY RIGHT NOW.
   Measured: `aw find plans reusable` prints `no matching plans` and exits 0, because
   `.aw/records/plans/reusable/` holds only `README.md`. `reusable` is a real plan disposition, so
   asking "which plans are reusable?" and hearing "none" is a SUCCESSFUL answer, not a typo. A blunt
   fail-closed change would newly make that query nonzero. This is the same exemption
   `25kzda` Section 2.4a draws and the same one `attention.selector_vocabulary()` implements.

3. `attention.selector_vocabulary()` IS THE RIGHT BASE BUT HAS A MEASURED GAP FOR THIS VERB. Computed
   in-lane against the live symbols:

   ```text
   vocabulary size: 74
   artifact_types.ARTIFACT_TYPES members absent from it: ['reviews', 'other']
   find --status enum values absent from it: ['intake']   (research)
   ```

   `reviews` and `other` are `find` types (`at.ARTIFACT_TYPES`) that `attention`'s `TYPE_ALIASES` does
   not carry, and `intake` is a research status `cli._find_valid_statuses` accepts. Reusing the
   function unmodified would turn three valid queries into refusals, so the predicate must UNION
   attention's vocabulary with `find`'s own type and status symbols. It must derive them FROM THOSE
   SYMBOLS, never from a literal list, so a type or status added later joins automatically.

4. THE DOCUMENTED CONTRACT IS SELF-CONTRADICTORY ON THIS EXACT CASE, and both halves are normative
   prose in `docs/cli-output-contract.md`:

   - Section 11.1 ("Empty Result Convention (Read and List Verbs)"): an empty result MUST emit
     `outcome: "clean"`, `exit: 0`, `findings: 0`, `verified: true`, `complete: true`.
   - Section 12 ("Exit Classification"): "If one or more matching paths are found, the command exits
     `0`. If a specific selector matches zero paths, the command exits `1`."

   Section 11.1 describes an empty RESULT SET; Section 12 describes a zero-match SELECTOR. The
   distinction this plan builds is precisely the one the document never drew, which is why the code
   ended up implementing both. The fix is not complete until the document states one rule.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin today's behavior before changing it

- [ ] E-01 WRITE THE CHARACTERIZATION TEST FIRST, capturing the full exit matrix of `aw find` across all four surfaces (human, `--agent`, `--json`, `--paths`) for four token classes: (a) a nonexistent token, (b) a VOCABULARY token that matches nothing in the fixture, (c) a token that matches at least one artifact, and (d) NO selector at all over an empty tree. Assert today's actual answers, INCLUDING the `--paths` divergence, so the three-way split is a recorded fact rather than a claim in prose. Build the fixture as a temporary repository rather than asserting against this repository's live records, whose contents change under the test. Class (d) exists to pin the case that must NOT change: an unfiltered listing of an empty tree is a successful empty answer, and the existing `not selectors` guard is what makes it so.
  - Depends on: none
  - Expected outcome: a pasted test run showing the recorded matrix, with (a) and (b) currently indistinguishable on every surface, and `--paths` answering 1 where the other three answer 0.
  - Execution state: pending

### Task group 2: the predicate, derived from symbols

- [ ] E-02 BUILD `find`'s ZERO-MATCH VOCABULARY as the UNION of `attention.selector_vocabulary()` with `find`'s own accepted tokens, derived from `artifact_types.ARTIFACT_TYPES` (plus whatever alias map `at.normalize_type`/`at.is_type_token` consults) and from every per-type status enum `cli._find_valid_statuses` returns. Reusing attention's function is the point, so do NOT re-implement it; extend it by union. DERIVE, NEVER ENUMERATE: a literal list is what lets a newly added type silently become a refusal. Re-measure the gap at execution time rather than trusting this plan's numbers, and state whether it is still exactly `reviews`, `other`, `intake`. Prefer adding the union in `cli.py` over editing `attention.py`, so `attention`'s shipped contract and its `fqnj8k` tests are not disturbed; if the executor concludes the union belongs in a shared module instead, record that as a decision with its reason.
  - Depends on: none
  - Expected outcome: a pure function returning the vocabulary, plus pasted output proving the three measured gap tokens are members and that a nonsense token is not.
  - Execution state: pending

- [ ] E-03 COMPUTE THE PER-TOKEN MATCH FACT for `find`, keyed on MATCHED and not on RESOLVED. `find`'s last selector rung is a filename SUBSTRING test, so a token may legitimately match without resolving as any identifier, and a fact keyed on the resolver alone would refuse every substring query. Ask the same matcher the verb itself uses, one token at a time. HANDLE THE MULTI-TYPE CASE CORRECTLY: with no `--type`, `find` searches all of `at.ARTIFACT_TYPES`, so a token is MATCHED if it matches under ANY searched type, and reporting per-type absence would refuse almost every real query. ALSO PRESERVE THE EXPLICIT-FLAG INTERACTION: `--id`/`--set`/`--status`/`--topic`/`--disposition` narrow results AFTER selector resolution in `_find_type_records`, so a token whose match those flags then remove must NOT be reported as a no-match; pin the fact to the pre-narrowing resolution, which is the same false-no-match trap `fqnj8k` documents for `--type` in `attention`.
  - Depends on: E-02
  - Expected outcome: a function yielding matched/unmatched tokens for a given invocation, with a pasted test proving a substring-only query counts as matched and that a flag-narrowed match is not reported unmatched.
  - Execution state: pending

### Task group 3: the refusal, once, on every surface

- [ ] E-04 REFUSE ON THE MACHINE SURFACES (`--agent` and `--json`) with exit 2 and a `cannot-run` outcome naming each unmatched token, matching the shape `aw runs` and `aw attention` already emit (`unresolved_targets`), so a consumer that already handles one handles this. Validate the emitted record with the schema validator rather than by eye. Keep `verified`/`complete` honest for a refusal: the query was not answered.
  - Depends on: E-03
  - Expected outcome: pasted `--agent` and `--json` records for a typo token showing exit 2 and `cannot-run`, both passing schema validation, and unchanged records for a matching query.
  - Execution state: pending

- [ ] E-05 REFUSE ON THE HUMAN SURFACE with exit 2, naming EACH unmatched token individually rather than collapsing a multi-token invocation into one message, since a multi-token query is exactly where a single typo hides. Reuse the house empty-state primitive (`Term.format_empty_result`, which this verb and `attention`'s refusal both already use) rather than inventing a second message shape. Write the refusal to STDERR, matching `attention`'s refusal and `aw runs`, and record the consequence explicitly: a human zero-match message moves from stdout to stderr. NO "DID YOU MEAN" GUESS; a wrong guess is worse than a clean negative.
  - Depends on: E-03
  - Expected outcome: pasted human-surface output for one typo token and for two tokens where one is valid, showing each unmatched token named, exit 2, and stdout empty.
  - Execution state: pending

- [ ] E-06 CORRECT THE `--paths`/`-p` SURFACE to the same convention: exit 2 for a non-vocabulary zero match and exit 0 for a vocabulary zero match, replacing today's blanket exit 1. STDOUT MUST STAY BYTE-IDENTICAL (empty), with the refusal on stderr, because `--paths` exists to be piped and a diagnostic on its stdout would corrupt the consumer's stream. THIS IS THE ONE DELIBERATE BREAKING CHANGE IN THE PLAN and it must be called out as such in the report: a script testing `if aw find ... -p; then` currently sees 1 for BOTH a typo and an empty vocabulary query, and will now see 2 and 0 respectively. Preserve the `not selectors` case at exit 0.
  - Depends on: E-03
  - Expected outcome: pasted exit codes for the typo, vocabulary, matching, and no-selector cases under `--paths`, plus proof stdout is empty on the refusal path.
  - Execution state: pending

### Task group 4: make the documented contract say one thing

- [ ] E-07 RESOLVE THE CONTRACT CONFLICT in `docs/cli-output-contract.md` by drawing the distinction the document currently lacks: an empty RESULT SET from an unfiltered or vocabulary query stays `clean`/exit 0 (Section 11.1 survives, scoped), while a SELECTOR asserting a named artifact that matches nothing is a `cannot-run` at exit 2 (Section 12's "exits 1" is corrected, not deleted). Cite `25kzda` Section 2.3/2.4a as the governing ruling and note the two verbs already conforming. ALSO FIX the worked example in `docs/cli-agent-protocol.md`, which currently presents a zero-match `find` record for selector `89bby9` under the heading "Clean empty query result (`exit: 0`)" and would otherwise document the exact behavior this plan removes. NO em or en dashes in this user-facing prose.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: the diff of both documents, with the superseded "exits 1" sentence and the stale example shown replaced.
  - Execution state: pending

### Task group 5: closeout - the survey the backlog item asked for, and the regression gate

- [ ] E-08 SURVEY THE REMAINING SELECTOR-TAKING READ VERBS and report, since fixing one verb at a time is how three conventions accumulated. Enumerate them from the argument parser rather than by memory, measure each one's zero-match exit code on every surface it has, and state for each whether it now conforms. RECORD THE MEASUREMENT FOR `aw ipd board` SPECIFICALLY: at authoring it accepts NO positional selector (`aw ipd board zzzzzz` is rejected by argparse as `unrecognized arguments`), so the backlog item's suggestion to include it is answered by measurement, not by assumption. FILE A BACKLOG ITEM for any nonconforming verb this plan does not fix, with the measured evidence, rather than widening this plan's declared scope.
  - Depends on: E-07
  - Expected outcome: a table of selector-taking read verbs with each one's measured zero-match exit code per surface and its conformance verdict, plus the id6 of any backlog item filed.
  - Execution state: pending

- [ ] E-09 RUN THE FULL REGRESSION GATE, capturing a pre-execution baseline BEFORE any edit in this plan lands and the post-change run after E-08, both with bare `python3 -m pytest` (no added flags: the configured `addopts` already supplies quiet, parallel, fast-subset, and a second `-q` would suppress the `N passed` line this plan requires). Then run `aw ipd lint --phase pre-transition` on this plan and `aw sanitize --agent`. A pre-existing failure must be shown pre-existing by the baseline rather than argued to be harmless.
  - Depends on: E-08
  - Expected outcome: the baseline and post-change summary lines pasted side by side, a conforming pre-transition lint, and a clean sanitizer report.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE GOVERNING RULING IS A SPEC, NOT A PRECEDENT-BY-EXAMPLE. Spec `25kzda` (`Status: approved`) Section 2.3 states "Zero matches return exit 2. Unknown or unclassifiable files return exit 2." Section 2.4a carves the single exemption: an empty status-selector result "is a success, not an error ... because `reviews` is a standing question about repository state rather than an assertion that a named item exists. A misspelled id6 still exits 2; only the status selectors are exempt."
- THE EXEMPTION ALREADY HAS AN IMPLEMENTATION TO REUSE. `attention.selector_vocabulary()` derives the standing-question token set from contract symbols (`A.TRACKED_TREES`, `TYPE_ALIASES`, `A.ATTENTION_CLASSES`, each `A.CLASS_MAPS` status enum, `backlog.PRIORITIES`, `_RUN_STATUS_ALIASES`) and its docstring states the derivation is the point: a token added to a contract "later joins this vocabulary automatically and so cannot silently become an 'error'".
- THE REFUSAL SHAPE ALSO EXISTS. `attention.SelectorMatchFacts` keeps `unmatched` and `invalid` as separate facts with a `refusable` property that subtracts the vocabulary; `attention.EXIT_UNRESOLVED_SELECTOR` is 2; `attention._emit_unresolved_selector_refusal` routes one predicate to every surface, choosing stdout for machine surfaces and stderr for human and list modes. Its comment states why the split matters: "A list mode exists to be piped into another command, so a diagnostic on ITS stdout would corrupt the pipe."
- `fqnj8k`'s HARD-WON LESSON APPLIES HERE AND MUST NOT BE RELEARNED. Its `selector_match_facts` docstring records that a match fact computed AFTER a narrowing filter reports a FALSE no-match, measured (the same filter matched a token over the full 1063-item scan and 0 items over the `-t plans` 661-item scan), and concludes "Reporting a FALSE no-match is a WORSE defect than the silence this fix removes". `find` has the same trap in a different place: `_find_type_records` applies `--id`/`--set`/`--status`/`--disposition` AFTER selector resolution.
- `find`'s EMPTY-STATE RENDERING IS ALREADY THE HOUSE PRIMITIVE. `cli._run_find` composes `summary_text` and an `Active filters:` dictionary and the human path renders through `Term.empty_result`/`format_empty_result`, the same primitive `attention`'s refusal reuses, so the refusal needs no new message vocabulary.
- `--check` ON `find` IS DELIBERATELY INERT. A comment at the `CommandResult` site records that `find`'s parser accepts `--check` and "deliberately leaves that flag INERT rather than quietly giving it meaning (paw8so F-14)". This plan must not give it meaning either.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The zero-match exit code differs ACROSS SURFACES OF THE SAME VERB, three ways | `aw find plans zzzzzz` exits 0 on human/`--agent`/`--json` and 1 on `--paths` | The fix is a four-surface unification, not a one-line exit change (E-04..E-06) |
| F-2 | A vocabulary token matches nothing in THIS repository today | `aw find plans reusable` -> `no matching plans`, exit 0; `reusable/` holds only `README.md` | A blunt fail-closed change breaks a legitimate query; the exemption is mandatory, not optional (E-02) |
| F-3 | `attention.selector_vocabulary()` omits three tokens `find` accepts | Computed in-lane: `ARTIFACT_TYPES` members `reviews`, `other` absent; research status `intake` absent | Reuse is correct but must be UNIONed with `find`'s own symbols (E-02) |
| F-4 | `docs/cli-output-contract.md` states two contradictory rules for this case | Section 11.1 mandates `exit: 0` for an empty read result; Section 12 mandates "matches zero paths, the command exits `1`" | Any fix violates one half unless the document is corrected in the same change (E-07) |
| F-5 | The agent-protocol doc's worked example documents the defect | `docs/cli-agent-protocol.md` shows a zero-match `find` record for `89bby9` under "Clean empty query result (`exit: 0`)" | Must be updated or the docs contradict the shipped behavior (E-07) |
| F-6 | `find` narrows results AFTER selector resolution | `_find_type_records` applies `--id`/`--set`/`--status`/`--disposition` to `results` after resolution | The match fact must be pinned pre-narrowing or valid queries get false refusals (E-03) |
| F-7 | `find`'s last rung is a filename substring test | `_find_type_records` highlights substring matches; resolution falls through to it | The fact must key on MATCHED, not RESOLVED, or every substring query refuses (E-03) |
| F-8 | `aw ipd board` takes no positional selector | `aw ipd board zzzzzz` -> argparse `unrecognized arguments: zzzzzz`; its parser adds only `--dir` and `--status` | The backlog item's inclusion of it is answered by measurement; it is out of scope (E-08) |
| F-9 | The no-selector empty listing is already correct | `return 0 if (all_paths or not selectors) else 1` exempts the unfiltered case | Must be PRESERVED; it is the Section 11.1 case that legitimately stays 0 (E-01 class (d)) |

## Proposed changes (ordered, validatable)

1. Characterize the current four-surface, four-token-class exit matrix in `tests/test_cli_find.py` (E-01).
2. Add the vocabulary predicate, unioning `attention.selector_vocabulary()` with `find`'s type and status symbols (E-02).
3. Add the per-token match fact, computed pre-narrowing and keyed on matched-not-resolved (E-03).
4. Wire the refusal into the machine surfaces at exit 2 with a `cannot-run` record (E-04).
5. Wire the refusal into the human surface at exit 2 on stderr, naming each token (E-05).
6. Bring `--paths` onto the same convention, replacing blanket exit 1, stdout byte-identical (E-06).
7. Reconcile the conflicting contract sections and the stale protocol example (E-07).
8. Survey the remaining selector-taking read verbs, file backlog items for any not fixed (E-08).

## Deferred / out of scope (with reason)

- WIDENING THE FIX TO EVERY SELECTOR-TAKING VERB AT ONCE. `fqnj8k` deferred `find` on the stated ground that widening "would make one change to N contracts at once", and the same reasoning bounds this plan to `find`. The remainder is not dropped: E-08 SURVEYS every selector-taking read verb, measures its zero-match exit per surface, and FILES A BACKLOG ITEM for each nonconforming verb this plan does not fix.
  - Carrier-Declined: The obligation is DISCHARGED INSIDE THIS PLAN rather than handed off, so there is nothing for a pre-authored carrier to hold. E-08 is a required execution item and V-08 refuses it without a pasted per-verb measurement table plus the id6 of every item filed, so the carrier for any residual work is MINTED BY EXECUTION with the evidence attached. Filing a placeholder item now would have to guess which verbs diverge, and the measurement that answers that does not exist yet; a guessed item is worse than a measured one because it cannot be closed on evidence. If E-08 measures that every other verb already conforms, the correct outcome is NO item at all, which a pre-filed carrier would misrepresent as outstanding debt.
- `aw ipd board`. Measured to accept no positional selector (F-8), so there is no zero-match selector case to fix. If it later gains one, it inherits the convention this plan documents.
  - Carrier-Declined: Nothing is owed because there is no defect: measured in this lane, `aw ipd board zzzzzz` is rejected by argparse (`unrecognized arguments: zzzzzz`) and its parser adds only `--dir` and `--status`, so the verb has no zero-match selector path to diverge. The backlog item suggested surveying it; that survey is DONE and its answer is recorded here and in F-8. An item asserting future work would misrepresent a measured absence as a pending task. Should the verb ever gain a positional selector, the convention E-07 writes into `docs/cli-output-contract.md` governs it at that point.
- GIVING `--check` MEANING ON `find`. Deliberately inert per `paw8so` F-14, and repurposing it would be a second contract change smuggled into this one.
  - Carrier-Declined: This row records a PROHIBITION on this plan, not deferred work, so nothing is owed. `paw8so` F-14 already decided the flag stays inert and wrote the reason at the code site; this plan merely declines to overturn a standing decision it did not make and has no evidence against. Giving the flag meaning would be a public-contract change on a surface no finding here measures as faulty, and that is a maintainer's call rather than tracked debt.
- A "DID YOU MEAN" SUGGESTION for a near-miss token. A wrong guess is worse than a clean negative, and `fqnj8k` made the same call for `attention`. Consistency matters more than convenience here.
  - Carrier-Declined: A settled design conclusion, not an unbuilt piece, so no future work is owed. `fqnj8k`'s shipped code states the same reasoning at its own decision site ("NO 'DID YOU MEAN' GUESS. A wrong guess is worse than a clean negative"), and diverging here would reintroduce across two verbs exactly the inconsistency this plan exists to remove. Filing an item would imply the repository intends to add suggestions, which no evidence supports.
- CHANGING WHICH ARTIFACTS MATCH, the selector precedence, or the row format. This plan changes only the answer given when the match set is empty.
  - Carrier-Declined: A scope fence, not deferred work. No finding in this plan measures a fault in matching, precedence, or row rendering, so there is no defect to carry; the fence is enforced by `- Scope-Paths:` and by V-06's requirement that a matching query's stdout stay byte-identical to the pre-change output.

## Scope check

- Over-scope: none. `agent_workflows/cli.py` carries `_run_find` and `_find_type_records`; `tests/test_cli_find.py` is the verb's test module; the two docs are the normative statements this change must not leave contradicting the code (F-4, F-5).
- Under-scope: `agent_workflows/attention.py` is deliberately NOT declared. E-02 extends the vocabulary by UNION from `cli.py`, leaving `attention`'s shipped contract and its `fqnj8k` tests untouched. If the executor finds the union genuinely cannot be built without editing `attention.py`, that is a scope change: stop, record it, and re-declare rather than editing an undeclared file.

## Required tests / validation

- `python3 -m pytest` run BARE, with the pasted `N passed` summary line, against a pre-execution baseline captured the same way, so a pre-existing failure is not mistaken for a regression.
- Targeted runs of `tests/test_cli_find.py` and `tests/test_attention.py`, the latter because E-02 consumes `attention.selector_vocabulary()` and must not perturb it.
- Real end-to-end invocations of `aw find` on all four surfaces for all four token classes, with actual exit codes pasted, not described.
- `aw ipd lint --phase pre-transition` conforming, and `aw sanitize --agent` clean, before any terminal transition.

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and that is a deliberate finding rather than an omission. Spec `25kzda` Section 2.3/2.4a ALREADY rules the behavior this plan implements; the plan makes a third verb conform to an approved contract rather than changing one. No `.spec.md` file is declared in `- Scope-Paths:`, consistent with that.
- `docs/cli-output-contract.md` Sections 11.1 and 12 MUST be reconciled (E-07, F-4). This is the only place where the repository's own written contract contradicts the change, and leaving it would mean shipping code that violates a normative document.
- `docs/cli-agent-protocol.md` zero-match example MUST be corrected (E-07, F-5).

## Open questions

### OQ-01: Should the human-surface refusal go to stderr, moving today's stdout message?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-05 PROPOSES stderr, for consistency with `attention`'s refusal and `aw runs`, whose stated reason is that a refusal must never land in a stream a caller parses. The cost is real and is recorded rather than hidden: `aw find`'s human zero-match message moves from stdout to stderr, so a human-mode caller redirecting stdout stops seeing it. The alternative (human refusal on stdout, exit 2) keeps today's stream and still fixes the exit code. Either is defensible; the plan proceeds with stderr and defers to the reviewer, and the choice changes one line in E-05 rather than the design.
- Carrier-Declined: NOT BLOCKING and owed to no future item, because both branches are implemented by this plan's own E-05 and neither leaves residual work. The question is which of two shipped conventions to follow, so the reviewer answers it by amending one line of E-05 before execution; V-05 then demands the pasted stream evidence that PROVES which branch shipped, so the decision is recorded as measured behavior rather than as an intention. Filing an item would imply work outlives this plan, and it does not.

### OQ-02: Is the `--paths` change from exit 1 to exit 2/0 acceptable as a breaking change?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-06 proposes it because leaving `--paths` at 1 preserves the three-way split inside one verb, which is the defect. A script currently reading exit 1 for both a typo and an empty vocabulary query will read 2 and 0. The plan judges this acceptable because `--paths` exit 1 is documented only by the Section 12 sentence that F-4 shows is already contradicted, so no consistent contract is being broken. If the reviewer disagrees, the narrower fix is to unify the three exit-0 surfaces and file the `--paths` half as its own item; E-08's survey format is designed to carry exactly that record.
- Carrier-Declined: NOT BLOCKING and carrying no residual work under either answer. If the reviewer accepts the change, E-06 ships it and V-06 proves it with pasted exit codes for all four token classes; if the reviewer declines, E-06 narrows to the three exit-0 surfaces and the `--paths` half is filed BY E-08, whose survey table and V-08's id6 requirement are the mechanism that records it. Both branches terminate inside this plan or inside an item E-08 mints with measured evidence, so a pre-filed carrier would either duplicate that item or assert debt the reviewer may decide does not exist.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted test run of the characterization test, showing the recorded pre-change matrix for all four surfaces and all four token classes, with classes (a) and (b) indistinguishable and `--paths` differing from the other three. The test must be shown FAILING or asserting the OLD values before the fix lands, since a characterization test written after the change proves nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of the vocabulary function proving (i) `reviews`, `other` and `intake` are members, (ii) a nonsense token is not, and (iii) the gap was RE-MEASURED at execution time with the numbers stated, whether or not they still match this plan's `reviews`/`other`/`intake`. Plus a shown-by-reading confirmation that the tokens are derived from `ARTIFACT_TYPES` and `_find_valid_statuses` rather than written as literals.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted test output proving three properties, each named separately: (i) a substring-only query counts as MATCHED and does not refuse, (ii) a token whose match is removed by `--id`/`--set`/`--status`/`--disposition` is NOT reported unmatched, and (iii) in the no-`--type` multi-type case a token matching under any one type counts as matched. A pass on (i) alone is insufficient.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `--agent` and `--json` output for a typo token showing exit 2 and `cannot-run` with the token named, pasted output of the schema validator accepting both records, and pasted `--agent`/`--json` output for a MATCHING query proving it still emits its former clean record unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted human-surface output and exit code for (i) one typo token and (ii) two tokens where exactly one is valid, showing EACH unmatched token named individually. Plus a demonstration of the stream split: stdout captured separately and shown empty on the refusal path, with the message on stderr.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `--paths` exit codes for all four token classes (typo -> 2, vocabulary -> 0, matching -> 0, no selector -> 0) and a byte-level demonstration that stdout is empty on the refusal path. Also a re-run of the matching case proving its stdout path list is byte-identical to the pre-change output.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the `git diff` of `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md`, showing the Section 12 "exits 1" sentence corrected, Section 11.1 scoped to the cases that legitimately stay 0, and the `89bby9` example no longer presenting a zero-match selector as a clean exit 0. Plus a confirmation that the amended prose contains no em or en dashes.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the survey table, with each selector-taking read verb's zero-match exit code per surface MEASURED and pasted (not inferred), the enumeration method stated (parser introspection, not memory), the `aw ipd board` measurement recorded, and the id6 of every backlog item filed for a nonconforming verb left unfixed.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: bare `python3 -m pytest` output with the `N passed` summary line pasted, alongside the pre-execution baseline captured the same way, so any failure is shown to be pre-existing rather than introduced. Plus `aw ipd lint --phase pre-transition` conforming and `aw sanitize --agent` reporting zero findings.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is deliberate: that field is
an output of `/plan-review` and writing it at authoring time would forge the attestation a gate reads.

The executor must: perform E-01 through E-08 in order, respecting the declared `Depends on` edges; commit
only the four paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never push; paste ACTUAL runner
output for every claim of a passing test; and verify each `V-*` in a separate pass from the `E-*` that
produced it. Do NOT mark this plan executed or move it to `.aw/records/plans/executed/` until every
`V-*` carries concrete pasted evidence and `aw ipd lint --phase pre-transition` conforms.

Backlog item `hd5bkk` is this plan's origin (`- From-Backlog: hd5bkk`) and its `- Blocks-Release: next`
gate is inherited above, so the release gate travels with the work and is not re-decided here.
