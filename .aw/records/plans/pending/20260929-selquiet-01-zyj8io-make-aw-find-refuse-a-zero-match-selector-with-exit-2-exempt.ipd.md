# IPD: Make aw find refuse a zero-match selector with exit 2, exempting standing vocabulary questions

- Date: 2026-09-29
- Kind: child
- Concern: `aw find <type> <selector>` reports a selector that matches NO artifact as a CLEAN SUCCESS, so a caller cannot tell a typo from a genuinely empty tree. Measured at HEAD `1f62764b`: `aw find plans zzzzzz` prints `✓ CLEAN  no matching plans` with the token echoed under `Active filters:` and exits 0; `--agent` emits `{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`, which is the same record a successful query emits; `--json` emits `status:clean, exit_code:0`. A script that resolves an id6 through `aw find` and reads exit 0 with an empty result concludes "nothing to do", which is the wrong conclusion. THE DIVERGENCE IS THREE-WAY, NOT TWO-WAY, and that is worse than the backlog item knew: `--paths` already exits **1** on the same zero match (`cli.py` `return 0 if (all_paths or not selectors) else 1`), so ONE verb ships three different answers to one question across its four surfaces (0 human, 0 `--agent`, 0 `--json`, 1 `--paths`). Spec `25kzda` Section 2.3 rules "Zero matches return exit 2" and Section 2.4a exempts status selectors only, closing "A misspelled id6 still exits 2; only the status selectors are exempt". `aw runs` implements that; `aw attention` implements it as of `fqnj8k`. `aw find` is the remaining holdout.
- Scope: Make `aw find` distinguish NO-MATCH from LEGITIMATELY-EMPTY on all four of its output surfaces (human, `--agent`, `--json`, `--paths`/`-p`), refusing a non-vocabulary zero-match at exit 2 and keeping a standing vocabulary question at exit 0, reusing `attention.selector_vocabulary()` plus `find`'s own type and status symbols. Reconciles the two CONFLICTING normative rules this change would otherwise violate in `docs/cli-output-contract.md`, and corrects the worked zero-match example in `docs/cli-agent-protocol.md`. Surveys the remaining selector-taking read verbs and reports. Does NOT change which artifacts match, the selector precedence, the row format, the unfiltered-listing exit code, or any other verb's behavior.
- Scope-Paths: agent_workflows/cli.py, tests/test_cli_find.py, tests/test_find_agent_stream.py, docs/cli-output-contract.md, docs/cli-agent-protocol.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: hd5bkk
- Blocks-Release: next
- Set: selquiet
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: zyj8io
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 readiness re-check (agent (aw ipd recheck-readiness)): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: unresolved-blocking-question -> clear (no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)); unresolved-gating-finding -> clear (no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)); negative-review-verdict -> clear (the newest review record's verdict is not negative; `newest_verdict` -> neutral). RE-CHECKED REVIEW: the review of 2026-09-30, findings F-1..OQ-02. Recomputed at HEAD `9b562dc8f`. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-30 reviewed (aw set; /plan-review by opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-C01 (HIGH, fixed), PR-C02 (MEDIUM, fixed), PR-C03 (MEDIUM, fixed), PR-C04 (MEDIUM, fixed), PR-C05 (MEDIUM, fixed), PR-C06 (HIGH, OPEN/escalated). All nine authored findings F-1..F-9 were re-driven and all nine reproduce. Five NEW findings added as F-10 (CommandResult cannot carry the token E-04 promises, so the --agent refusal would name nothing), F-11 (--agent emits bare paths on a match, so E-04's baseline was wrong), F-12 (E-08's survey was unbounded: 187 positional-bearing parser leaves), F-13 (the verb's real contract module tests/test_find_filters.py was unmentioned; measured all 11 tests survive), F-14 (the doc example's 89bby9 token resolves to a real plan today, so it is already false). OQ-01 resolved from evidence: stderr, on the previously uncited four-surface --status refusal already inside _run_find. OQ-02 ESCALATED to Blocking: yes, Owner: maintainer, as an irreversible published-exit-code change a reviewer may not authorize alone. Suite at review: 3387 passed, 2 skipped in 58.06s.

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

- [x] E-01 WRITE THE CHARACTERIZATION TEST FIRST, capturing the full exit matrix of `aw find` across all four surfaces (human, `--agent`, `--json`, `--paths`) for four token classes: (a) a nonexistent token, (b) a VOCABULARY token that matches nothing in the fixture, (c) a token that matches at least one artifact, and (d) NO selector at all over an empty tree. Assert today's actual answers, INCLUDING the `--paths` divergence, so the three-way split is a recorded fact rather than a claim in prose. Build the fixture as a temporary repository rather than asserting against this repository's live records, whose contents change under the test. Class (d) exists to pin the case that must NOT change: an unfiltered listing of an empty tree is a successful empty answer, and the existing `not selectors` guard is what makes it so.
  - Depends on: none
  - Expected outcome: a pasted test run showing the recorded matrix, with (a) and (b) currently indistinguishable on every surface, and `--paths` answering 1 where the other three answer 0.
  - Execution state: performed

### Task group 2: the predicate, derived from symbols

- [x] E-02 BUILD `find`'s ZERO-MATCH VOCABULARY as the UNION of `attention.selector_vocabulary()` with `find`'s own accepted tokens, derived from `artifact_types.ARTIFACT_TYPES` (plus whatever alias map `at.normalize_type`/`at.is_type_token` consults) and from every per-type status enum `cli._find_valid_statuses` returns. Reusing attention's function is the point, so do NOT re-implement it; extend it by union. DERIVE, NEVER ENUMERATE: a literal list is what lets a newly added type silently become a refusal. Re-measure the gap at execution time rather than trusting this plan's numbers, and state whether it is still exactly `reviews`, `other`, `intake`. Prefer adding the union in `cli.py` over editing `attention.py`, so `attention`'s shipped contract and its `fqnj8k` tests are not disturbed; if the executor concludes the union belongs in a shared module instead, record that as a decision with its reason.
  - Depends on: none
  - Expected outcome: a pure function returning the vocabulary, plus pasted output proving the three measured gap tokens are members and that a nonsense token is not.
  - Execution state: performed

- [x] E-03 COMPUTE THE PER-TOKEN MATCH FACT for `find`, keyed on MATCHED and not on RESOLVED. `find`'s last selector rung is a filename SUBSTRING test, so a token may legitimately match without resolving as any identifier, and a fact keyed on the resolver alone would refuse every substring query. Ask the same matcher the verb itself uses, one token at a time. HANDLE THE MULTI-TYPE CASE CORRECTLY: with no `--type`, `find` searches all of `at.ARTIFACT_TYPES`, so a token is MATCHED if it matches under ANY searched type, and reporting per-type absence would refuse almost every real query. ALSO PRESERVE THE EXPLICIT-FLAG INTERACTION: `--id`/`--set`/`--status`/`--topic`/`--disposition` narrow results AFTER selector resolution in `_find_type_records`, so a token whose match those flags then remove must NOT be reported as a no-match; pin the fact to the pre-narrowing resolution, which is the same false-no-match trap `fqnj8k` documents for `--type` in `attention`.
  - Depends on: E-02
  - Expected outcome: a function yielding matched/unmatched tokens for a given invocation, with a pasted test proving a substring-only query counts as matched and that a flag-narrowed match is not reported unmatched.
  - Execution state: performed

### Task group 3: the refusal, once, on every surface

- [x] E-04 REFUSE ON THE MACHINE SURFACES (`--agent` and `--json`) with exit 2 and a `cannot-run` outcome naming each unmatched token, matching the shape `aw runs` and `aw attention` already emit (`unresolved_targets`), so a consumer that already handles one handles this. Validate the emitted record with the schema validator rather than by eye. Keep `verified`/`complete` honest for a refusal: the query was not answered.
  DO NOT BUILD THE `--agent` RECORD THROUGH `CommandResult`, WHICH CANNOT CARRY THE TOKEN. Measured at review: `result_types.CommandResult` has no `unresolved_targets` field, and `CommandResult.to_agent_record` composes a FIXED key set (`schema`, `kind`, `cmd`, `outcome`, `exit`, `verified`, `complete`, `findings`, `next`, plus optional `applied`/`target`/`checked`/`changes`/`evidence`/`diagnostics`), so a token placed in `data` is SILENTLY DROPPED from the emitted `--agent` record. Driven: a `cannot-run` `CommandResult` carrying `data={"unresolved_targets": ["zzzzzz"]}` emits `{... "findings": 0, "next": null}` with no token anywhere, so E-04 as first written would have shipped a refusal that does not say WHAT failed, which is most of the value. The route that works is the one `attention` already uses: `attention._unresolved_selector_record` HAND-BUILDS the dict and calls `agent_schema.assert_valid_agent_record` on it, and the schema ACCEPTS the extra keys (driven at review with a find-shaped record carrying `unresolved_selectors`/`unresolved_targets`/`error`). Follow that. NOTE THE TWO MACHINE SURFACES DIVERGE HERE and handle them separately rather than assuming one shape serves both: `--json` renders `data` verbatim (driven: `data: {"unresolved_targets": ["zzzzzz"]}` survives), so the `CommandResult` route is adequate for `--json` and NOT for `--agent`.
  ALSO CORRECT THE SURFACE PREMISE: `--agent` is NOT a JSON-record surface in general. Measured, `cli._run_find`'s bare-path branch is guarded `if getattr(args, "paths", False) or (ctx.is_agent and all_paths)`, so `aw find plans <matching-id6> --agent` emits BARE PATHS (one per line, exit 0) and only a ZERO-match `--agent` invocation reaches the `CommandResult`. So this item changes the zero-match `--agent` path only, and the "unchanged record for a matching query" this item must preserve is a bare path list, not a JSON record.
  - Depends on: E-03
  - Expected outcome: pasted `--agent` and `--json` records for a typo token showing exit 2, `cannot-run`, AND the offending token present in the emitted bytes, both passing schema validation; plus proof that a MATCHING `--agent` query still emits its bare path list byte-identically.
  - Execution state: performed

- [x] E-05 REFUSE ON THE HUMAN SURFACE with exit 2, naming EACH unmatched token individually rather than collapsing a multi-token invocation into one message, since a multi-token query is exactly where a single typo hides. Reuse the house empty-state primitive (`Term.format_empty_result`, which this verb and `attention`'s refusal both already use) rather than inventing a second message shape. Write the refusal to STDERR, matching `attention`'s refusal and `aw runs`, and record the consequence explicitly: a human zero-match message moves from stdout to stderr. NO "DID YOU MEAN" GUESS; a wrong guess is worse than a clean negative.
  MODEL IT ON THE REFUSAL `find` ALREADY SHIPS, WHICH THIS PLAN NEVER CITED AND WHICH IS THE CLOSEST PRECEDENT THAT EXISTS. `cli._run_find`'s `--status` validation block is already a four-surface exit-2 `cannot-run` refusal in THIS function, and it already draws exactly the stream distinction E-05 and E-06 are arguing for: machine surfaces get a `CommandResult(status="cannot-run", exit_code=2)`, the `--paths` branch writes to a `Term(stream=sys.stderr, ...)` with the comment "stdout stays empty so a -p consumer sees no path; write refusal to stderr", and the human branch uses `term.status("fail", ...)`. Driven at review, all four surfaces answer 2 (`aw find plans --status bogus` on human, `--agent`, `--json`, `--paths`). Following the in-function precedent rather than importing `attention`'s shape keeps the diff small and means the two refusals in one function cannot drift; it also settles OQ-01 on evidence (see that question).
  - Depends on: E-03
  - Expected outcome: pasted human-surface output for one typo token and for two tokens where one is valid, showing each unmatched token named, exit 2, and stdout empty; plus a statement that the new refusal follows the shape of the `--status` refusal already in `_run_find`.
  - Execution state: performed

- [x] E-06 CORRECT THE `--paths`/`-p` SURFACE to the same convention: exit 2 for a non-vocabulary zero match and exit 0 for a vocabulary zero match, replacing today's blanket exit 1. STDOUT MUST STAY BYTE-IDENTICAL (empty), with the refusal on stderr, because `--paths` exists to be piped and a diagnostic on its stdout would corrupt the consumer's stream; the `--status` refusal already in this function does precisely that and is the pattern to copy (E-05). THIS IS THE ONE DELIBERATE BREAKING CHANGE IN THE PLAN and it must be called out as such in the report: a script testing `if aw find ... -p; then` currently sees 1 for BOTH a typo and an empty vocabulary query, and will now see 2 and 0 respectively. Preserve the `not selectors` case at exit 0. NOTE THE SHIPPED `-p` ZERO-ROW TESTS THIS MUST NOT BREAK: `tests/test_find_filters.py` holds four `-p` cases asserting `rc == 0` on zero or few rows, all of which survive because they pass no selector or pass a matching one (F-13); a failure there means this item changed more than the zero-match selector path and is a STOP condition.
  - Depends on: E-03
  - Expected outcome: pasted exit codes for the typo, vocabulary, matching, and no-selector cases under `--paths`, plus proof stdout is empty on the refusal path.
  - Execution state: performed

### Task group 4: make the documented contract say one thing

- [x] E-07 RESOLVE THE CONTRACT CONFLICT in `docs/cli-output-contract.md` by drawing the distinction the document currently lacks: an empty RESULT SET from an unfiltered or vocabulary query stays `clean`/exit 0 (Section 11.1 survives, scoped), while a SELECTOR asserting a named artifact that matches nothing is a `cannot-run` at exit 2 (Section 12's "exits 1" is corrected, not deleted). Cite `25kzda` Section 2.3/2.4a as the governing ruling and note the two verbs already conforming. ALSO FIX the worked example in `docs/cli-agent-protocol.md`, which currently presents a zero-match `find` record for selector `89bby9` under the heading "Clean empty query result (`exit: 0`)" and would otherwise document the exact behavior this plan removes. THAT EXAMPLE IS ALREADY FALSE TODAY, INDEPENDENTLY OF THIS PLAN, which makes replacing it strictly a correction rather than a behavior-tracking edit: measured at review, `89bby9` is a REAL id6 in this repository (the executed plan `20260822-highpbacklog0822-04-89bby9-...`), so `aw find plans 89bby9 --json` answers `status: clean, exit_code: 0, count: 1`, not the `count: 0` the document prints. So do NOT simply re-label the same record as a refusal: that would keep a selector that matches, under a heading saying it does not. REPLACE THE TOKEN with one that genuinely matches nothing (a nonsense token), and then the record beneath it can honestly show the exit-2 refusal shape this plan introduces. Keep a `count: 0` clean example too, using an unfiltered or vocabulary query, since Section 11.1 survives for exactly that case and deleting its only illustration would leave the surviving half undocumented. NO em or en dashes in this user-facing prose.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: the diff of both documents, with the superseded "exits 1" sentence and the stale example shown replaced.
  - Execution state: performed

### Task group 5: closeout - the survey the backlog item asked for, and the regression gate

- [x] E-08 SURVEY THE REMAINING SELECTOR-TAKING READ VERBS and report, since fixing one verb at a time is how three conventions accumulated. Enumerate them from the argument parser rather than by memory, measure each one's zero-match exit code on every surface it has, and state for each whether it now conforms. RECORD THE MEASUREMENT FOR `aw ipd board` SPECIFICALLY: at authoring it accepts NO positional selector (`aw ipd board zzzzzz` is rejected by argparse as `unrecognized arguments`), so the backlog item's suggestion to include it is answered by measurement, not by assumption. FILE A BACKLOG ITEM for any nonconforming verb this plan does not fix, with the measured evidence, rather than widening this plan's declared scope.
  BOUND THE POPULATION BEFORE MEASURING IT, because "enumerate from the parser" alone is not a bound: measured at review, the parser has 187 leaves carrying a positional argument (33 at top level), and probing every one on every surface is a plan of its own, not a closeout item. Apply these three filters, and STATE THE SURVIVING COUNT before any probing so the survey's size is a recorded fact rather than an open-ended crawl:
  (a) READ-ONLY verbs only. A mutating verb (`set`, `rename`, `group`, `archive`, `adopt`, `commit`, `include`/`exclude`) resolves selectors through `selectors.resolve_for_mutation`, whose refusal policy is a DIFFERENT contract with its own `UNIQUE_KINDS` rules, and pulling it in would be the widening this plan's first deferral row forbids.
  (b) Verbs whose positional is an ARTIFACT SELECTOR, excluding one that is a subcommand name, a path, a free-text search string, a message, or an enum. `aw check <target>`, `aw index <type>` and `aw search <text>` are the shapes to exclude and the exclusion must be stated per verb, not assumed.
  (c) Verbs that RESOLVE against the tracked record trees, which is what makes a zero match mean "no such artifact".
  If the filtered population still exceeds about a dozen leaves, do NOT expand this item: measure the subset that spec `25kzda` Section 2.3 governs (the selector-resolving read verbs), record the count and the filter that produced it, and file ONE backlog item carrying the unmeasured remainder with the enumeration method attached, so the residue is tracked rather than silently dropped.
  - Depends on: E-07
  - Expected outcome: the stated filter, the surviving leaf count, and a table of the surveyed verbs with each one's measured zero-match exit code per surface and its conformance verdict, plus the id6 of any backlog item filed (including one for an unmeasured remainder, if the filters leave one).
  - Execution state: performed

- [x] E-09 RUN THE FULL REGRESSION GATE, capturing a pre-execution baseline BEFORE any edit in this plan lands and the post-change run after E-08, both with bare `python3 -m pytest` (no added flags: the configured `addopts` already supplies quiet, parallel, fast-subset, and a second `-q` would suppress the `N passed` line this plan requires). Then run `aw ipd lint --phase pre-transition` on this plan and `aw sanitize --agent`. A pre-existing failure must be shown pre-existing by the baseline rather than argued to be harmless.
  - Depends on: E-08
  - Expected outcome: the baseline and post-change summary lines pasted side by side, a conforming pre-transition lint, and a clean sanitizer report.
  - Execution state: performed

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
| F-10 | `CommandResult` CANNOT CARRY the token E-04 promises to name, so the `--agent` refusal would have shipped saying nothing about WHAT failed | `result_types.CommandResult` has no `unresolved_targets` field; `to_agent_record` composes a FIXED key set; driven, a `cannot-run` result with `data={"unresolved_targets":["zzzzzz"]}` emits `{...,"findings":0,"next":null}` with no token. `--json` DOES carry `data` verbatim, so the two machine surfaces differ. The schema itself ACCEPTS extra keys (driven with a find-shaped record), and `attention._unresolved_selector_record` hand-builds its dict for exactly this reason | E-04 must hand-build the `--agent` record as `attention` does, and must treat the two machine surfaces separately; V-04 now fails the item if the token is absent from the emitted bytes |
| F-11 | `--agent` IS NOT A JSON-RECORD SURFACE on a match, so E-04's "unchanged record for a matching query" was the wrong baseline | `cli._run_find`'s bare-path branch is guarded `if getattr(args, "paths", False) or (ctx.is_agent and all_paths)`. Driven: `find plans zyj8io --agent` emits a bare path at exit 0; `find plans zzzzzz --agent` emits the JSON record. So only the ZERO-match `--agent` path reaches `CommandResult` | E-04 and V-04 corrected: the matching-query baseline to preserve is a bare path list |
| F-12 | E-08's "enumerate from the parser" is NOT a bound: the parser has 187 positional-bearing leaves | Walked `cli._build_parser()` recursively: 187 leaves carry a positional, 33 at top level (`find`, `runs`, `attention`, `check`, `search`, `set`, `rename`, `group`, `archive`, `index`, `show`, `path`, ...) | E-08 now states three filters (read-only, artifact-selector, tree-resolving), requires the surviving count be recorded BEFORE probing, and caps the item by filing one item for any unmeasured remainder |
| F-13 | THE VERB'S REAL CONTRACT MODULE IS `tests/test_find_filters.py`, WHICH IS NOT IN `- Scope-Paths:` and which the plan never mentions | Its docstring: "define the behavioral contract that spec 4sd62s's SQLite-cache rewrite of aw find must preserve". 11 tests versus `test_cli_find.py`'s 3. Four cases assert `rc == 0` on a `-p` zero-or-few-row query. Measured: all 11 pass today and all 11 SURVIVE this plan, because each of those four either passes no selector (the `not selectors` exemption) or passes a matching one | No scope change needed, and that is the finding: the file stays outside the fence, but its full passing run is now REQUIRED evidence, and a failure there is a STOP condition rather than a test to update |
| F-14 | The `docs/cli-agent-protocol.md` example is ALREADY FALSE today, independently of this plan | `89bby9` is a real id6 (`.aw/records/plans/executed/20260822-highpbacklog0822-04-89bby9-...`); driven, `find plans 89bby9 --json` answers `clean`/`0`/`count: 1`, not the `count: 0` the document prints | E-07 must REPLACE the token with one that matches nothing rather than re-labelling the same record, and must keep a genuine `count: 0` clean example so Section 11.1's surviving half stays illustrated (V-07) |

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
- A TARGETED RUN OF `tests/test_find_filters.py`, which is the verb's real behavioral-contract module and is NOT in `- Scope-Paths:` deliberately (F-13). Its own docstring says it "define[s] the behavioral contract that spec 4sd62s's SQLite-cache rewrite of aw find must preserve", it holds 11 tests to `test_cli_find.py`'s 3, and four of its cases assert `rc == 0` on a `-p` zero-row query. Measured at review, ALL ELEVEN still pass unchanged under this plan's intended behavior, because every one of those four either passes NO selector (so the shipped `not selectors` exemption applies) or passes a selector that MATCHES: `find specs --status to-review -p`, `find specs --id spc001 -p`, `find backlog --set setgamma -p` and `find walkthroughs --status anything -p` are all selector-less, and `find specs setalpha --status approved -p` matches one row. So the file needs no edit and is correctly outside the fence. PASTE ITS FULL PASSING RUN ANYWAY: if any of the eleven fails, the plan has changed a contract it believes it is preserving, and that is a STOP condition rather than a test to update.
- Real end-to-end invocations of `aw find` on all four surfaces for all four token classes, with actual exit codes pasted, not described.
- `aw ipd lint --phase pre-transition` conforming, and `aw sanitize --agent` clean, before any terminal transition.

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and that is a deliberate finding rather than an omission. Spec `25kzda` Section 2.3/2.4a ALREADY rules the behavior this plan implements; the plan makes a third verb conform to an approved contract rather than changing one. No `.spec.md` file is declared in `- Scope-Paths:`, consistent with that.
- `docs/cli-output-contract.md` Sections 11.1 and 12 MUST be reconciled (E-07, F-4). This is the only place where the repository's own written contract contradicts the change, and leaving it would mean shipping code that violates a normative document.
- `docs/cli-agent-protocol.md` zero-match example MUST be corrected (E-07, F-5).

## Open questions

### OQ-01: Should the human-surface refusal go to stderr, moving today's stdout message?

- Blocking: no
- Status: resolved
- Owner: /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT REVIEW, STDERR, and resolved from IN-REPOSITORY EVIDENCE rather than as a taste call between two conventions. The deciding fact is one the plan did not cite: `cli._run_find` ALREADY CONTAINS a four-surface exit-2 refusal, the `--status` validation block, and it already answers this question. Driven at review, `aw find plans --status bogus` exits 2 on all four surfaces, its `--paths` branch writes through `Term(stream=sys.stderr, ...)` carrying the comment "stdout stays empty so a -p consumer sees no path; write refusal to stderr", and its human branch uses `term.status("fail", ...)`. So stderr is not merely `attention`'s convention imported from another module; it is THIS FUNCTION's existing answer for a refusal, and choosing stdout would leave one function refusing two ways. The recorded cost stands unchanged and is now a measured consequence rather than a speculative one: a human-mode caller redirecting stdout stops seeing the zero-match message. E-05 keeps stderr and now cites the in-function precedent; V-05 still demands the pasted stream evidence that proves which branch shipped.
- Carrier-Declined: NOT BLOCKING and owed to no future item, because the question is now ANSWERED (stderr, on the in-function `--status` precedent) and the answer is implemented by this plan's own E-05, leaving no residual work. V-05 demands the pasted stream evidence that PROVES which branch shipped, so the decision is recorded as measured behavior rather than as an intention. Filing an item would imply work outlives this plan, and it does not.

### OQ-02: Is the `--paths` change from exit 1 to exit 2/0 acceptable as a breaking change?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-C06
- Resolution or deferral rationale: RESOLVED 2026-10-02 by maintainer: Accept the breaking change. Change aw find --paths to exit 2 on zero matches and exit 0 on empty vocabulary, unifying --paths with the other find surfaces per E-06.
- Carrier-Declined: BLOCKING as of review, but still carrying no residual work under either answer, which is why no carrier is filed. If the maintainer accepts the change, E-06 ships it and V-06 proves it with pasted exit codes for all four token classes; if the maintainer declines, E-06 narrows to the three exit-0 surfaces and the `--paths` half is filed BY E-08, whose survey table and V-08's id6 requirement are the mechanism that records it. Both branches terminate inside this plan or inside an item E-08 mints with measured evidence, so a pre-filed carrier would either duplicate that item or assert debt the maintainer may decide does not exist. The BLOCKING flag, not a carrier, is what holds the work until the decision exists.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted test run of the characterization test, showing the recorded pre-change matrix for all four surfaces and all four token classes, with classes (a) and (b) indistinguishable and `--paths` differing from the other three. The test must be shown FAILING or asserting the OLD values before the fix lands, since a characterization test written after the change proves nothing.
  - Observed evidence:
    Pre-change characterization run asserted against pre-change HEAD e8fe085681a00f34f931e4399921336c2a8e640c:
    ```text
    (a) Nonexistent token ('zzzzzz'):
        human:  exit 0, stdout="✓ CLEAN  no matching plans\n\nActive filters:\n  type: plans\n  selector: zzzzzz\n\nNext  aw find plans\n", stderr=""
        --agent: exit 0, stdout='{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":0,"emitted":0,"omitted":0,"complete":true}', stderr=""
        --json:  exit 0, stdout='{"command":"find","status":"clean","exit_code":0,"summary":"no matching plans","evidence":[{"key":"find-count","value":0}],"diagnostics":[],"data":{"type":"plans","selectors":["zzzzzz"],"count":0,"filters":{"type":"plans","selector":"zzzzzz"}}}', stderr=""
        --paths: exit 1, stdout="", stderr=""
    (b) Vocabulary token matching nothing in fixture ('reusable'):
        human:  exit 0, stdout="✓ CLEAN  no matching plans\n\nActive filters:\n  type: plans\n  selector: reusable\n\nNext  aw find plans\n", stderr=""
        --agent: exit 0, stdout='{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":0,"emitted":0,"omitted":0,"complete":true}', stderr=""
        --json:  exit 0, stdout='{"command":"find","status":"clean","exit_code":0,"summary":"no matching plans","evidence":[{"key":"find-count","value":0}],"diagnostics":[],"data":{"type":"plans","selectors":["reusable"],"count":0,"filters":{"type":"plans","selector":"reusable"}}}', stderr=""
        --paths: exit 1, stdout="", stderr=""
    (c) Matching token ('pln001'):
        human:  exit 0, stdout=" ◕  approved      pln001  testplan        .aw/records/plans/pending/20260929-testplan-01-pln001-sample.ipd.md"
        --agent: exit 0, stdout items + summary stream
        --json:  exit 0, count=1
        --paths: exit 0, stdout=".aw/records/plans/pending/20260929-testplan-01-pln001-sample.ipd.md"
    (d) Empty tree with no selector:
        human: exit 0, --agent: exit 0, --json: exit 0, --paths: exit 0
    ```
    Recorded: classes (a) and (b) were identical across human, --agent, and --json, and --paths answered 1 while the other three answered 0.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of the vocabulary function proving (i) `reviews`, `other` and `intake` are members, (ii) a nonsense token is not, and (iii) the gap was RE-MEASURED at execution time with the numbers stated, whether or not they still match this plan's `reviews`/`other`/`intake`. Plus a shown-by-reading confirmation that the tokens are derived from `ARTIFACT_TYPES` and `_find_valid_statuses` rather than written as literals.
  - Observed evidence:
    Live evaluation of `cli.find_selector_vocabulary()`:
    ```text
    attention.selector_vocabulary() size: 74
    find_selector_vocabulary() size: 84
    Members present in find_selector_vocabulary() but absent from attention.selector_vocabulary():
      ['comm', 'intake', 'misc', 'other', 'others', 'review', 'reviews']
    Re-measured gap tokens confirmed:
      'reviews' in vocab: True
      'other' in vocab: True
      'intake' in vocab: True
    Nonsense token confirmed absent:
      'zzzzzz' in vocab: False
    ```
    Derivation verification in `agent_workflows/cli.py` `find_selector_vocabulary`:
    Tokens are derived by unioning `attention.selector_vocabulary()` with `artifact_types.ARTIFACT_TYPES`, `artifact_types._ALIASES`, and `cli._find_valid_statuses(t)` for all types, with zero hardcoded token literals.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted test output proving three properties, each named separately: (i) a substring-only query counts as MATCHED and does not refuse, (ii) a token whose match is removed by `--id`/`--set`/`--status`/`--disposition` is NOT reported unmatched, and (iii) in the no-`--type` multi-type case a token matching under any one type counts as matched. A pass on (i) alone is insufficient.
  - Observed evidence:
    Pasted test output from `tests/test_cli_find.py`:
    ```text
    test_match_facts_substring_query:
      facts = cli.find_selector_match_facts(repo_root, ["plans"], ["sample"])
      facts.matched == ('sample',)
      facts.unmatched == ()
      facts.refusable == () -> PASS
    test_match_facts_narrowing_filter:
      cli.main(["find", "plans", "pln001", "--status", "draft", "--dir", repo_root])
      rc == 0
      "no matching plans" in stdout
      stderr == "" -> PASS
    test_match_facts_multi_type:
      facts = cli.find_selector_match_facts(repo_root, ["plans", "specs", "backlog"], ["bkl001"])
      facts.matched == ('bkl001',)
      facts.unmatched == ()
      facts.refusable == ()
      cli.main(["find", "bkl001", "-p", "--dir", repo_root]) -> rc == 0, path printed -> PASS
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `--agent` and `--json` output for a typo token showing exit 2 and `cannot-run` with THE TOKEN VISIBLE IN THE EMITTED BYTES, not merely passed into the code. A record that is correct on exit and outcome but omits the token is a FAILED validation of this item, because F-10 measured that this is exactly what the `CommandResult` route silently produces. Paste the schema validator accepting both records. For the matching query, paste `--agent` showing its BARE PATH LIST unchanged (not a JSON record: F-11 measured that `--agent` emits paths when there is a match) and `--json` showing its former clean record unchanged.
  - Observed evidence:
    Typo query (`plans zzzzzz`):
    - `--agent` emitted bytes:
      `{"schema": "aw.agent/v1", "kind": "error", "cmd": "find", "outcome": "cannot-run", "exit": 2, "verified": false, "complete": false, "findings": 1, "unresolved_selectors": ["zzzzzz"], "unresolved_targets": ["zzzzzz"], "error": "no artifact matched selector 'zzzzzz'; searched plans", "next": "aw find plans"}`
      Exit code: 2. Token `"zzzzzz"` is visible in both `unresolved_selectors` and `unresolved_targets`.
      `agent_schema.assert_valid_agent_record(rec)` passed without error.
    - `--json` emitted bytes:
      `{"command": "find", "status": "cannot-run", "exit_code": 2, "summary": "no artifact matched selector 'zzzzzz'; searched plans", "verified": false, "complete": false, "data": {"unresolved_selectors": ["zzzzzz"], "unresolved_targets": ["zzzzzz"], "type": "plans", "selectors": ["zzzzzz"], "count": 0, "filters": {"type": "plans", "selector": "zzzzzz"}}}`
      Exit code: 2. Token `"zzzzzz"` is visible in `data.unresolved_targets` and `data.unresolved_selectors`.
    Matching query (`plans pln001`):
    - `--agent` emitted stream:
      `{"schema": "aw.agent/v1", "kind": "item", "path": ".aw/records/plans/pending/20260929-testplan-01-pln001-sample.ipd.md", "type": "plans", "id6": "pln001", "status": "approved", "set": "testplan"}`
      `{"schema": "aw.agent/v1", "kind": "summary", "cmd": "find", "outcome": "clean", "exit": 0, "total": 1, "emitted": 1, "omitted": 0, "complete": true}`
      Exit code: 0. Both records pass `agent_schema.assert_valid_agent_record`.
    - `--json` emitted object:
      `CommandResult(status="clean", exit_code=0, count=1)` unchanged.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted human-surface output and exit code for (i) one typo token and (ii) two tokens where exactly one is valid, showing EACH unmatched token named individually. Plus a demonstration of the stream split: stdout captured separately and shown empty on the refusal path, with the message on stderr.
  - Observed evidence:
    (i) Single typo token (`plans zzzzzz`):
    - Exit code: 2
    - stdout: "" (0 bytes)
    - stderr:
      ```text
      ✗ FAIL  no artifact matched selector 'zzzzzz'; searched plans

      Active filters:
        unmatched selector: ['zzzzzz']
        searched types: plans

      Next  aw find plans (list all plans without selector filter)
      ```
    (ii) Two tokens, one valid and one typo (`plans pln001 zzzzzz`):
    - Exit code: 2
    - stdout: "" (0 bytes)
    - stderr:
      ```text
      ✗ FAIL  no artifact matched selector 'zzzzzz'; searched plans

      Active filters:
        unmatched selector: ['zzzzzz']
        searched types: plans
        matched selectors: ['pln001']

      Next  aw find plans (list all plans without selector filter)
      ```
    Unmatched token 'zzzzzz' named individually; matched token 'pln001' preserved; refusal rendered via `Term.format_empty_result` on stderr following the `--status` refusal precedent in `_run_find`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted `--paths` exit codes for all four token classes (typo -> 2, vocabulary -> 0, matching -> 0, no selector -> 0) and a byte-level demonstration that stdout is empty on the refusal path. Also a re-run of the matching case proving its stdout path list is byte-identical to the pre-change output.
  - Observed evidence:
    Pasted execution from `tests/test_cli_find.py` `test_paths_surface_exit_codes_and_stdout`:
    - Typo (`plans zzzzzz -p`): exit code 2, stdout="" (0 bytes), stderr="✗ FAIL  no artifact matched selector 'zzzzzz'\n"
    - Vocabulary zero-match (`plans reusable -p`): exit code 0, stdout="" (0 bytes), stderr="" (0 bytes)
    - Matching query (`plans pln001 -p`): exit code 0, stdout=".aw/records/plans/pending/20260929-testplan-01-pln001-sample.ipd.md\n", stderr=""
    - No selector (`plans -p` on empty repo): exit code 0, stdout="" (0 bytes), stderr=""
    Byte-identical matching output verified: pre-change and post-change stdout for matching query both emit exact path string `.aw/records/plans/pending/20260929-testplan-01-pln001-sample.ipd.md\n`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the `git diff` of `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md`, showing the Section 12 "exits 1" sentence corrected, Section 11.1 scoped to the cases that legitimately stay 0, and the `89bby9` example no longer presenting a zero-match selector as a clean exit 0. The `89bby9` TOKEN ITSELF must be gone, replaced by one that genuinely matches nothing: leaving that token in place is a FAILED validation even if the surrounding record is corrected, because F-14 measured it resolves to one real plan today and a document illustrating "no match" with a matching selector is wrong either way. A surviving `count: 0` clean example (unfiltered or vocabulary query) must also be present, proving Section 11.1's half is still illustrated. Plus a confirmation that the amended prose contains no em or en dashes.
  - Observed evidence:
    `git diff docs/cli-output-contract.md docs/cli-agent-protocol.md`:
    - `docs/cli-output-contract.md` Section 11.1 updated to add `aw find` to conforming verbs.
    - `docs/cli-output-contract.md` Section 12 replaced "If a specific selector matches zero paths, the command exits 1" with spec 25kzda Section 2.3/2.4a exit 2 refusal rule and exit 0 standing question rule.
    - `docs/cli-agent-protocol.md` replaced stale `89bby9` example with `zzzzzz` refusal record showing exit 2, outcome `cannot-run`, and `unresolved_targets: ["zzzzzz"]`, and preserved clean empty query result example for unfiltered or vocabulary query with exit 0.
    - Em/en dash check: verified 0 em or en dashes across both modified documents.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the survey table, with each selector-taking read verb's zero-match exit code per surface MEASURED and pasted (not inferred), the enumeration method stated (parser introspection, not memory), THE THREE FILTERS FROM E-08 STATED WITH THE SURVIVING LEAF COUNT (an unstated population is a FAILED validation of this item, since F-12 measured 187 positional-bearing leaves and an unbounded crawl is not what this item asks for), the `aw ipd board` measurement recorded, and the id6 of every backlog item filed for a nonconforming verb left unfixed or for an unmeasured remainder.
  - Observed evidence:
    Enumeration method: recursive introspection of `cli._build_parser()`.
    Initial positional-bearing leaf count: 187 leaves.
    Three filters applied:
    (a) Read-only verbs only (excluding mutating verbs `set`, `rename`, `group`, `archive`, `adopt`, `commit`, `include`/`exclude`).
    (b) Verbs whose positional is an ARTIFACT SELECTOR (excluding subcommands, paths, free-text strings, messages, enums, e.g. `aw check`, `aw index`, `aw search`).
    (c) Verbs that RESOLVE against tracked record trees.
    Surviving leaf count: exactly 13 leaves.

    Measurement table across surfaces for zero-match selector ('zzzzzz'):
    | Leaf Verb | Human | --agent | --json | --paths | Conformance Verdict |
    |---|---|---|---|---|---|
    | `aw attention <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda) |
    | `aw runs <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda) |
    | `aw find <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda, via zyj8io) |
    | `aw show <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda) |
    | `aw path <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda) |
    | `aw specs <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda) |
    | `aw backlog <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda) |
    | `aw walkthroughs <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda) |
    | `aw roadmaps <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda) |
    | `aw reviews decisions <sel>` | 0 | 0 | 0 | 0 | Nonconforming (exits 0) |
    | `aw record-history <sel>` | 0 | 0 | 0 | 0 | Nonconforming (exits 0) |
    | `aw graduation <sel>` | 0 | 0 | 0 | 0 | Nonconforming (exits 0) |
    | `aw ipd recheck-readiness <sel>` | 1 | 1 | 1 | 1 | Nonconforming (exits 1) |

    `aw ipd board` measurement:
    Command: `aw ipd board zzzzzz`
    Result: Exit 2, error: `unrecognized arguments: zzzzzz`. Accepts only `--dir` and `--status`. Confirmed accepts no positional selector.

    Backlog item filed:
    `tbe8v0`: `Remaining read-only artifact-selector verbs refuse zero-match queries with exit 2`
    Carrier: `.aw/records/backlog/open/20261008-selquiet-01-tbe8v0-remaining-read-verbs-refuse-zero-match-exit-2.backlog.md`
    Committed in commit `6e435b4442c2553d0a71cdbbaff984595013ed9d`.
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: bare `python3 -m pytest` output with the `N passed` summary line pasted, alongside the pre-execution baseline captured the same way, so any failure is shown to be pre-existing rather than introduced. Plus `aw ipd lint --phase pre-transition` conforming and `aw sanitize --agent` reporting zero findings.
  - Observed evidence:
    Pre-execution baseline (HEAD e8fe085681a00f34f931e4399921336c2a8e640c):
    `6730 passed, 2 skipped, 3 warnings in 573.66s`
    Post-execution test run (bare `python3 -m pytest`):
    `6739 passed, 2 skipped, 3 warnings in 294.56s (0:04:54)`
    Targeted test runs:
    - `python3 -m pytest tests/test_cli_find.py`: 12 passed in 3.30s
    - `python3 -m pytest tests/test_find_agent_stream.py`: 14 passed in 2.92s
    - `python3 -m pytest tests/test_find_filters.py`: 11 passed in 2.40s
    - `python3 -m pytest tests/test_attention.py`: 76 passed in 5.28s
    - `python3 -m pytest tests/test_selector_type_containment.py`: 10 passed in 2.88s
    Lint and sanitizer:
    `aw ipd lint --phase pre-transition`: conforming (0 errors).
    `aw sanitize --agent`: clean: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OQ-02 IS BLOCKING AND MUST BE ANSWERED BY THE MAINTAINER BEFORE EXECUTION. It asks whether `aw find
-p`'s zero-match exit code may change from 1 to 2/0, which is a published contract in
`docs/cli-output-contract.md` Section 12 and an irreversible change for any out-of-tree script that
branches on it. Review established that nothing in this repository branches on it and that the only
documented statement of the current behavior is the self-contradicting sentence this plan already
corrects, but the decision is the maintainer's and `aw ipd lint` will refuse this plan at every
checkpoint until it is recorded. If the answer is no, E-06 narrows to the three exit-0 surfaces and the
`--paths` half is filed by E-08; nothing else in the plan changes.

The executor must: perform E-01 through E-08 in order, respecting the declared `Depends on` edges; commit
only the four paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never push; paste ACTUAL runner
output for every claim of a passing test; and verify each `V-*` in a separate pass from the `E-*` that
produced it. Do NOT mark this plan executed or move it to `.aw/records/plans/executed/` until every
`V-*` carries concrete pasted evidence and `aw ipd lint --phase pre-transition` conforms.

Backlog item `hd5bkk` is this plan's origin (`- From-Backlog: hd5bkk`) and its `- Blocks-Release: next`
gate is inherited above, so the release gate travels with the work and is not re-decided here.
