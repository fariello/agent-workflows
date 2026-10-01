# IPD: State the accepted validation-result vocabulary where an author meets it, in the lint message and in the scaffolded V-item

- Date: 2026-09-30
- Kind: child
- Concern: The `- Result:` and `- Execution state:` vocabularies are CLOSED (`ipd_schema.VALIDATION_RESULTS` = `pending`/`pass`/`blocked`/`failed`; `ipd_schema.EXEC_STATES` = `pending`/`performed`/`blocked`/`failed`) and are stated NOWHERE an author writing a plan will read. The scaffolded V-item emits `- Required evidence: TODO falsifiable evidence.` with no statement of the terminal value, `ipd_schema.validation_row_error` reports the REJECTED value without naming any accepted one (`unknown validation result '{0}'`), and `ipd_lint.check_checkpoint`'s pre-transition diagnostic says only `not 'pass' at pre-transition`. Reproduced in process at HEAD `4e8643ab` by taking `ipd_authoring.build_skeleton(kind="child", ...)`, substituting the natural word `verified` for `pending` on the V-item, and linting: `author` disposition flips `conforming` -> `error` with `IPD-S402 V-01: unknown validation result 'verified'`, and at `pre-transition` the same document also reports `IPD-S404 V-01: not 'pass' at pre-transition`. Neither message names `pending`, `blocked`, or `failed`, so recovering the enum costs a source read.
- Scope: IN: (a) name the accepted vocabulary INSIDE the two row-state messages that currently reject a value without naming its alternatives (`ipd_schema.validation_row_error` and its execution twin `ipd_schema.execution_row_error`), rendered from the frozensets so the message cannot drift from the check; (b) state both vocabularies in the two scaffold section intros (`ipd_authoring._EXEC_INTRO`, `ipd_authoring._VALID_INTRO`) so an author meets them beside the rows they annotate, and REGENERATE the two byte-pinned templates from `build_skeleton`; (c) add behavioral tests for both. OUT: the enums themselves, which are unchanged (no new accepted value, no alias, so `verified` still fails); the checkpoint code `IPD-S404`, whose wording is a pinned retry trigger (F-5); `ipd_lint` itself, which needs no edit because it interpolates the schema's message; and the 1039-plan corpus, which is not rewritten (F-7).
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/ipd_authoring.py, .aw/system/workflows/assess/templates/ipd.md, .aw/system/workflows/assess/templates/orchestrator-ipd.md, tests/test_ipd_schema.py, tests/test_ipd_authoring.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: mc57em
- Set: vresultvocab
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: uh9jsk

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: uh9jsk verified (set vresultvocab, attempt 1).
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review verdict REVIEWED - OPEN QUESTIONS; PR-001..PR-008. Re-measured every one of F-1..F-8 and all hold (the IPD-S402 reproduction, the ipd_lint->ipd_schema layering, the bogus-row coverage gap, the closed-vocabulary cost, the in-vocabulary corpus property, the placeholder-tuple hazard, both precedent commits, and the manifest hash disagreement to both prefixes). Fixed one BLOCKER: E-04's negative assertion was unsatisfiable, since 'verified' is already a substring of the scaffold's 'TODO: how the executed plan is verified.' placeholder at HEAD, so the assertion is red on arrival and no correct implementation can green it; the negative is now scoped to the two intro lines and expressed token-wise against the frozenset. Fixed two HIGH: V-02's add-a-member red proof fails the coverage test first and needs three edits, not one (measured both stages); and the scope fence said 'stop and report' over a scope question, contrary to the 2026-09-01 ruling, now replaced with make-and-justify plus one genuine prerequisite stop. Added F-9: rewording IPD-S402/IPD-S401 is safe because finalize_refusal_is_retryable matches their CODES before prose, while IPD-S404 has no code fallback and a REWORDED (not appended) form measurably returns False, which sharpens F-5's deferral from caution into evidence. Withdrew OQ-01's 'silence is taken as accepting' clause, which let an unanswered question close itself; this run was non-interactive (worker role, no TTY) so OQ-01 stays open and non-blocking.
- 2026-09-30 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `mc57em`. The item offers three shapes and calls the first "the cheapest fix and probably sufficient": enumerate the vocabulary in the `IPD-S402` message; or write it into the scaffolded V-item; or accept `verified` as an alias. THE THIRD IS REJECTED ON EVIDENCE, not preference: `VALIDATION_RESULTS` is a CLOSED vocabulary whose closure is asserted by a two-sided coverage test (`tests/test_ipd_schema.py::ExecutionAndValidationStateTests::test_the_state_tables_cover_their_closed_vocabularies`), adding a member obliges a `_VALIDATION_RULES` entry plus legal and illegal rows, and an alias would make two spellings mean one thing in a corpus of 3891 live `- Result: pass` rows for no gain (F-6). THE FIRST TWO ARE BOTH TAKEN rather than one, because they answer different moments: the message helps an author who has already guessed wrong, while the scaffold intro reaches one who has not guessed yet. Doing only the message leaves the first guess uninformed; doing only the scaffold leaves every plan authored before this change (and every hand-written row) with the same bare rejection.

## Goal

Make both closed row-state vocabularies readable from the two places an author actually looks: the
diagnostic that rejected their value, and the checklist intro in the plan they are writing. Nothing
about which values are accepted changes; what changes is that recovering the enum no longer requires
opening `agent_workflows/ipd_schema.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: name the accepted values in the message that rejects one

- [x] E-01 In `agent_workflows/ipd_schema.py`, change the unknown-value branch of `validation_row_error` and of `execution_row_error` so each message names the ACCEPTED vocabulary in addition to the rejected value, rendering the list from `VALIDATION_RESULTS` / `EXEC_STATES` respectively (sorted, for a deterministic string) rather than from a hand-written literal. Follow the shape already shipped for the same problem in `validate_metadata`'s `Readiness` branch, which reads `"unrecognized readiness value (expected one of " + ", ".join(sorted(READINESS_VALUES)) + ")"`; match that phrasing so the three sibling enum rejections read alike. Keep the message a single line and keep the existing prefix (`unknown validation result '<value>'` / `unknown execution state '<value>'`) as the LEADING text, because that prefix is what a reader greps for and what existing prose cites. Change no other branch of either predicate, and change neither frozenset.
  - Depends on: none
  - Expected outcome: `validation_row_error("verified", False, False)` returns a string that contains `unknown validation result 'verified'` AND each of `pending`, `pass`, `blocked`, `failed`; `execution_row_error("done", False, False)` likewise contains `unknown execution state 'done'` and all four of `pending`, `performed`, `blocked`, `failed`; every other return value of both predicates (including `None` for a legal row) is byte-identical to HEAD.
  - Execution state: performed

  REWORDING THESE TWO MESSAGES IS SAFE AT THE FINALIZE SEND-BACK, AND IT IS SAFE STRUCTURALLY RATHER THAN BY LUCK, so do not apply F-5's caution here by analogy. `finalize_refusal_is_retryable` matches each finding line's leading CODE TOKEN before falling back to prose, and both codes these two predicates feed (`IPD-S402` via `ipd_lint.C_VALID_STATE`, `IPD-S401` via `C_EXEC_STATE`) ARE members of `retryable_finalize_finding_codes()`. Measured at review: the reworded `IPD-S402` line still yields `finalize_refusal_is_retryable(...) == True` (F-9). `IPD-S404` is the one that has no code-keyed fallback, which is why it and only it is deferred.

- [x] E-02 Add table rows to `tests/test_ipd_schema.py::ExecutionAndValidationStateTests` asserting the CONTENT of the two unknown-value messages, not merely that an error came back. The existing `("validation", ("bogus", False, False), True, ...)` and `("exec", ("bogus", False, False), True, ...)` rows only assert truthiness, so they pass against a message naming nothing; the new assertion must fail if a member of either frozenset is missing from its message. Derive the expected members from `S.VALIDATION_RESULTS` / `S.EXEC_STATES` inside the test rather than from a literal list, so adding a member to either vocabulary without reaching its message fails here. Keep the existing rows: this ADDS a content assertion to the class and removes nothing.
  - Depends on: E-01
  - Expected outcome: a test in `tests/test_ipd_schema.py` fails when the enumeration is dropped from either message and fails when a vocabulary member is added without reaching the message; both `bogus` rows still assert their truthiness as before.
  - Execution state: performed

### Task group 2: state both vocabularies in the scaffold an author starts from

- [x] E-03 In `agent_workflows/ipd_authoring.py`, extend `_EXEC_INTRO` and `_VALID_INTRO` with one sentence each naming its vocabulary and the value the terminal gate demands, rendered from `S.EXEC_STATES` / `S.VALIDATION_RESULTS` (sorted) rather than hand-spelled, so the intro cannot drift from the enum. Then REGENERATE both byte-pinned templates, `.aw/system/workflows/assess/templates/ipd.md` and `.aw/system/workflows/assess/templates/orchestrator-ipd.md`, from `build_skeleton` rather than hand-editing them, because `tests/test_ipd_templates.py::TemplateParityTests` byte-compares each file against the generator output for the fixed placeholder arguments it uses (`title` `<short title of the change>` / `<short title of the coordinated change>`, `author` `<agent/model>`, `when` `<YYYY-MM-DD>`, `set_name` `<set-id>`, `plan_id` `tmp1d6`, order 1 / 0). Do NOT add either new sentence to `_AUTHORING_PLACEHOLDERS`: that tuple means "this text is a stub an author must replace", and a sentence that is meant to SURVIVE authoring would make every finished plan read as an unresolved draft to `authoring_placeholders_resolved` and to the `check.ipd-draft-ready-to-review` nudge that consumes it.
  - Depends on: none
  - Expected outcome: a freshly scaffolded child AND orchestrator plan each state both vocabularies in prose; both templates are byte-identical to `build_skeleton` output so `TemplateParityTests` passes; a fresh scaffold still lints `conforming` at the `author` checkpoint; `authoring_placeholders_resolved` on a fully authored plan is unaffected by the new sentences.
  - Execution state: performed

- [x] E-04 Add a test to `tests/test_ipd_authoring.py` asserting that a scaffolded plan of BOTH kinds states each vocabulary member, deriving the expected members from the frozensets so a vocabulary change that misses the scaffold fails. Assert it on the OUTPUT OF `build_skeleton` (the generator), not on the template files, because `tests/test_ipd_templates.py` already owns the file-versus-generator byte parity and duplicating it here would pin the same fact twice while testing the scaffold's real behavior neither time. Include the negative direction, but SCOPE IT TO THE TWO INTRO LINES rather than to the whole document: assert that neither `_EXEC_INTRO` nor `_VALID_INTRO` (read from the module, or located in the scaffold by its heading) advertises a value outside its own frozenset, so a future edit cannot satisfy the positive assertion by pasting an illustrative list that includes a rejected value. Express the negative GENERALLY, as "no token in the intro's rendered value list is outside the frozenset", rather than by naming one word.
  - Depends on: E-03
  - Expected outcome: a test in `tests/test_ipd_authoring.py` fails if either intro stops naming its full vocabulary, fails for either kind independently, and fails if either intro advertises a value the frozenset does not contain.
  - Execution state: performed

  DO NOT WRITE `assertNotIn("verified", whole_scaffold)`: IT IS UNSATISFIABLE AND WAS MEASURED SO. The authoring text as this plan was first drafted asked for exactly that assertion, naming `verified` as "the value backlog `mc57em` measured an author reaching for". But the scaffold ALREADY contains the substring `verified` at HEAD, before any change this plan makes: the `## Required tests / validation` placeholder is the literal `TODO: how the executed plan is verified.`, and `verified` is a substring of `verified.`. Measured at review: `"verified" in build_skeleton(kind="child", ...)` returns **True** at HEAD with no E-03 edit applied, and the same for `kind="orchestrator"`. An executor writing the document-wide assertion therefore produces a test that is RED on arrival and that NO correct implementation of E-03 can turn green, which would either block the plan or (worse) invite the executor to "fix" it by deleting an unrelated placeholder. Scoping the negative to the intro lines keeps the guard the plan actually wants (an intro must not advertise a rejected value) and makes it satisfiable. A token-level check against the frozenset is also strictly stronger than pinning one word, since it catches any out-of-vocabulary value rather than only the one the backlog happened to name.

## Project conventions discovered (Step 0)

- THE VOCABULARIES ARE CLOSED AND CENTRAL: `ipd_schema.EXEC_STATES` and `ipd_schema.VALIDATION_RESULTS` are module-level frozensets, and `ipd_schema.validation_row_error` / `execution_row_error` test membership BEFORE looking up `_VALIDATION_RULES` / `_EXEC_CHECKBOX` (the `bogus` rows in `tests/test_ipd_schema.py` exist specifically to prove that order, so an unknown value returns a message instead of raising `KeyError`). Any change here must preserve that ordering.
- THE MESSAGE-NAMES-THE-ENUM PATTERN IS ALREADY SHIPPED IN THIS FILE: `validate_metadata`'s `Readiness` branch renders `", ".join(sorted(READINESS_VALUES))` into its own message, with a comment explaining that this enum's check lives in this module because this module OWNS the vocabulary. E-01 is that same pattern applied to the two row-state enums, not a new convention.
- THE TEMPLATES ARE GENERATED, NEVER HAND-EDITED: `tests/test_ipd_templates.py::TemplateParityTests` byte-compares `.aw/system/workflows/assess/templates/ipd.md` and `orchestrator-ipd.md` against `ipd_authoring.build_skeleton` output, with the failure message "regenerate it". Precedent for doing so inside a plan that changes the scaffold: commit `49d5e00f` (`citeanchor mzc019`) states the template "is REGENERATED from `build_skeleton` rather than hand-edited", and `9e3ed86e` (`planprio lkexaw`) shipped the same two-file regeneration as a two-line diff.
- THE INSTALLER OWNS THE TEMPLATE HASHES, so this plan must not hand-edit `.aw/system/managed-sections.json`. Confirmed two ways: the recorded `sha256` for `templates/ipd.md` (`87df6b29...`) ALREADY disagrees with `manifest.hash_content` of the file at HEAD (`6e0e9afe...`), so the manifest is not a gate a template edit must satisfy; and neither `9e3ed86e` nor `49d5e00f` touched that file while changing the same template.
- `ipd_authoring` IS STDLIB-ONLY BY TEST (`tests/test_ipd_authoring.py::NoDependencyTests::test_authoring_module_is_stdlib_only` re-imports it under a meta-path finder that rejects any non-stdlib top-level package other than `agent_workflows`). It already imports `ipd_schema` as `S`, so rendering the vocabularies from the frozensets in `_EXEC_INTRO`/`_VALID_INTRO` adds no import.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
| --- | --- | --- | --- |
| F-1 | The defect is real and reproduces exactly as the item describes, at HEAD. | Taking `ipd_authoring.build_skeleton(kind="child", ...)`, replacing `  - Result: pending` with `  - Result: verified`, and calling `ipd_lint.lint_text(..., checkpoint="author", directory="pending")` returns disposition `error` with the single diagnostic `IPD-S402 V-01: unknown validation result 'verified'`. At `checkpoint="pre-transition"` the same text adds `IPD-S404 V-01: not 'pass' at pre-transition` and `IPD-S404 V-01: empty Observed evidence at pre-transition`. No message names `pending`, `blocked`, or `failed`. RE-MEASURED AT REVIEW and confirmed, with one correction to the inventory above: the `pre-transition` run emits FIVE diagnostics, not three, because an untouched scaffold also reports `IPD-S404 E-01: not 'performed' at pre-transition` and the advisory `check.ipd-dependency-unresolved` (the `Item-Dependencies: unresolved` sentinel). Both extras are properties of a fresh scaffold rather than of the substituted value, so they do not weaken the finding, but an executor reproducing this at V-04 must expect them and not read them as a failed reproduction. | The plan is warranted and the two messages E-01 edits are the two the item names. V-04's end-to-end demonstration should assert on the `IPD-S402` line specifically rather than on the diagnostic COUNT. |
| F-2 | THE MESSAGE IS OWNED BY `ipd_schema`, NOT BY `ipd_lint`, so the fix belongs one layer lower than the code the item cites. | `ipd_lint.check_states` computes `err = S.validation_row_error(result, lf.checked, observed_nonempty)` and then wraps it verbatim as `Diagnostic(lf.line, 1, C_VALID_STATE, f"{lf.ident}: {err}")`. `ipd_lint` contains no copy of the wording. | Scope-Paths name `agent_workflows/ipd_schema.py` and deliberately NOT `agent_workflows/ipd_lint.py`: editing the schema's message changes the `IPD-S402` output with no linter edit at all. |
| F-3 | Both halves of the row-state contract have the same hole, so fixing only the validation half would leave the execution twin inconsistent. | `execution_row_error` returns `"unknown execution state '{0}'".format(state)` with the identical shape, and `EXEC_STATES` is the sibling frozenset. The item only names the validation half because that is the half its author hit. | E-01 fixes both. The cost is one extra line and the alternative is two sibling predicates disagreeing about whether a rejection names its alternatives. |
| F-4 | The existing `bogus` test rows CANNOT catch a regression in the new enumeration, so E-02 is not redundant coverage. | `tests/test_ipd_schema.py::ExecutionAndValidationStateTests.STATES` carries `("validation", ("bogus", False, False), True, ...)` and an exec twin; `test_every_state_combination_gets_its_verdict` asserts only `got is None` versus not-None. A message that enumerated nothing satisfies both rows. | E-02 adds a CONTENT assertion. Without it E-01 is unpinned and the next refactor can silently drop the enumeration. |
| F-5 | THE `IPD-S404` PRE-TRANSITION WORDING IS A PINNED RETRY TRIGGER and must not be reworded casually, which is why this plan does not touch it. | `runner_shared.RETRYABLE_FINALIZE_FINDING_TEXTS` is the tuple `("not 'performed' at pre-transition", "not 'pass' at pre-transition", "empty Observed evidence at pre-transition")`, with a comment stating the trigger is PROSE because the structured diagnostics are lost at the `aw ipd finalize` subprocess boundary, and that a wording change must break its test rather than silently widen the send-back. `tests/test_finalize_sendback.py::TheRetryTriggerIsAPositiveAllowlist::test_the_allowlist_texts_are_the_ones_ipd_lint_ACTUALLY_EMITS` lints a real plan at `pre-transition` and requires EVERY `C_CHECKPOINT` diagnostic to contain one of those substrings. | The second half of the item's complaint (that `IPD-S404` also names no accepted value) is deliberately DEFERRED rather than fixed here. Measured for completeness: APPENDING to those messages keeps them matching (a probe message with `(results: pending\|pass\|blocked\|failed)` appended still returns `finalize_refusal_is_retryable() == True`), so the fix is possible but it puts a run-control mechanism in the blast radius of a discoverability change, which is a trade a reviewer should make deliberately. See the deferral entry. RE-MEASURED AT REVIEW, WHICH CONFIRMED THE FINDING AND MADE THE RISK CONCRETE RATHER THAN NOTIONAL: `IPD-S404` is NOT a member of `retryable_finalize_finding_codes()` (which is exactly `{IPD-S401, IPD-S402, IPD-S403}`), so unlike `IPD-S402` it has NO code-keyed fallback and its prose is the ONLY thing keeping a pre-transition refusal retryable. Measured the failure mode the deferral exists to avoid: a message REWORDED rather than appended (`IPD-S404 V-01: Result must be 'pass' here; accepted: blocked, failed, pass, pending`) makes `finalize_refusal_is_retryable` return **False**, which would convert a bounded correction turn into a terminal failure. So the deferral is not excess caution: the safe-append and unsafe-reword cases differ by one editing choice, with no test-visible difference at author time. |
| F-6 | THE ITEM'S THIRD OPTION (accept `verified` as an alias) IS THE EXPENSIVE ONE, not the cheap one it reads as. | `VALIDATION_RESULTS` is asserted CLOSED by `test_the_state_tables_cover_their_closed_vocabularies`, which requires a LEGAL and an ILLEGAL table row per member; `_VALIDATION_RULES` would need a `verified` entry; the corpus holds thousands of `- Result: pass` rows against 0 `verified` (4080 against 0 when re-measured at review, up from 3891 the day before, which is why the ratio and not the count is the argument), and `ipd_lint.check_checkpoint` tests `!= "pass"` literally, so an alias accepted at `author` would still be refused at `pre-transition` unless that test changed too. VERIFIED AT REVIEW: `ipd_lint` contains exactly ONE `!= "pass"` comparison (`if lf.fields.get("Result") != "pass":` inside the checkpoint check), confirming the literal test the finding describes, and the three-edit cost of adding a member was measured directly (see V-02's note: frozenset member, `_VALIDATION_RULES` entry, AND a legal plus an illegal `STATES` row, or `test_the_state_tables_cover_their_closed_vocabularies` fails). | The alias is rejected and the plan says so on evidence. Note the trap in the last clause: a half-done alias would lint clean while authoring and fail only at finalize, which is strictly worse than today's immediate rejection. |
| F-7 | The corpus does not need rewriting and this plan must not rewrite it. THE PROPERTY, not the count, is what matters: EVERY `- Result:` and `- Execution state:` value in the tree is already IN vocabulary, and the great majority of plans (including every terminal one) carry the current intro sentences verbatim. | Measured 2026-09-30 at HEAD `4e8643ab` by `rg -oN --no-filename "^  - Result: .*$" .aw/records/plans/ \| sort \| uniq -c`: exactly FOUR distinct values occur (3891 `pass`, 1178 `pending`, 6 `blocked`, 2 `failed`) and every one is a member of `VALIDATION_RESULTS`; zero out-of-vocabulary values exist. `rg -lF` on each intro sentence matches roughly 930 of the ~1040 `.ipd.md` files, the remainder being plans predating the sentences. Re-derive both rather than trusting these figures, which move as plans land. RE-MEASURED AT REVIEW, WHICH IS THE POINT OF THE "re-derive" CAVEAT AND VINDICATES IT: the PROPERTY holds unchanged (still exactly four `- Result:` values, all in `VALIDATION_RESULTS`, zero out of vocabulary; and the `- Execution state:` census is likewise clean at `performed`/`pending`/`blocked` only), while every COUNT has already drifted in one day, to 4080 `pass`, 1438 `pending`, 6 `blocked`, 2 `failed`. The finding's own framing ("THE PROPERTY, not the count") is therefore correct and is what a reader should rely on; the numbers are context and must not be used as an acceptance bar. | E-03 changes the GENERATOR and the two templates only. A sweep would rewrite terminal records the execution contract forbids changing, and the vocabulary census shows it would fix nothing: no existing row is out of vocabulary. |
| F-8 | The new sentences must NOT join the authoring-placeholder tuple, and the reason is mechanical rather than stylistic. | `ipd_authoring._AUTHORING_PLACEHOLDERS` is a tuple of literal scaffold strings meaning "still a stub"; `authoring_placeholders_resolved` returns False while ANY of them is present, and it is consumed by `ipd_lint` and by `check_engine`'s `check.ipd-draft-ready-to-review` nudge (plus `check_durable_carrier`, which skips the placeholder OQ heading through the same tuple). The comment above the tuple says to keep it in lock-step when a scaffold placeholder CHANGES. | E-03 states the constraint explicitly. Adding a surviving sentence there would make every finished plan report as an unresolved draft; the sentences are not placeholders and must not be listed. |
| F-9 | **E-01's OWN BLAST RADIUS IS ZERO AT THE SEND-BACK, AND THE REASON IS STRUCTURAL RATHER THAN LUCKY.** This was not established by the plan as first drafted, which argued only that it leaves `IPD-S404` alone; the question an executor will actually ask is whether rewording `IPD-S402` can break the finalize retry path, since `IPD-S402` IS one of the codes that path classifies. The answer is no: `finalize_refusal_is_retryable`'s Arm 1 tests each finding line's leading CODE TOKEN against `retryable_finalize_finding_codes()` FIRST and falls back to the `RETRYABLE_FINALIZE_FINDING_TEXTS` prose match only when the code does not match (`if code_token in retryable_codes: continue` precedes `if not any(token in line for token in RETRYABLE_FINALIZE_FINDING_TEXTS): return False`). Measured: `retryable_finalize_finding_codes()` is `{IPD-S401, IPD-S402, IPD-S403}`, which contains `IPD-S402` (`ipd_lint.C_VALID_STATE`) and `IPD-S401` (`C_EXEC_STATE`) but NOT `IPD-S404` (`C_CHECKPOINT`). So a reworded `IPD-S402` stays retryable on its code regardless of its prose, verified by passing `pre-transition gate did NOT conform` plus `IPD-S402 V-01: unknown validation result 'verified' (expected one of blocked, failed, pass, pending)` to `finalize_refusal_is_retryable`, which returns `True`. | `runner_shared.finalize_refusal_is_retryable` Arm 1 read in full; `retryable_finalize_finding_codes()` returned `['IPD-S401','IPD-S402','IPD-S403']`; `ipd_lint.C_VALID_STATE == 'IPD-S402'` and `C_CHECKPOINT == 'IPD-S404'`; the reworded probe measured `True`. | This STRENGTHENS the plan's safety case for E-01 beyond what it claimed, and it SHARPENS F-5's asymmetry into the real reason the deferral is right: `IPD-S402` is protected by a code match and `IPD-S404` is protected by nothing but its prose, so the two messages genuinely are not equally safe to reword. Recorded so the executor does not conservatively refuse E-01 out of the same caution F-5 applies to `IPD-S404`. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/ipd_schema.py`: render the accepted vocabulary into the unknown-value message of `validation_row_error` and `execution_row_error`, from the frozensets, matching the shipped `Readiness` phrasing (E-01).
2. `tests/test_ipd_schema.py`: add a content assertion on both messages to `ExecutionAndValidationStateTests`, with the expected members derived from the frozensets (E-02).
3. `agent_workflows/ipd_authoring.py`: extend `_EXEC_INTRO` and `_VALID_INTRO` with one vocabulary sentence each, rendered from the frozensets; regenerate `.aw/system/workflows/assess/templates/ipd.md` and `.aw/system/workflows/assess/templates/orchestrator-ipd.md` from `build_skeleton` (E-03).
4. `tests/test_ipd_authoring.py`: add a scaffold-content test over both kinds, positive on every vocabulary member and negative on `verified` (E-04).

## Deferred / out of scope (with reason)

- ENUMERATING THE VOCABULARY IN THE `IPD-S404` PRE-TRANSITION MESSAGES is deferred, and this is the one deliberate narrowing of the item's complaint. Those three strings are a live run-control trigger (F-5): they decide whether a refused finalize is handed back to the agent for a bounded correction or the item is failed, the trigger is a SUBSTRING match on prose precisely because the structured diagnostics do not survive the subprocess boundary, and the comment beside the tuple asks for a deliberate update rather than an incidental one. Appending to them was measured safe (`finalize_refusal_is_retryable` still returns True with an appended parenthetical), so this is a decision about blast radius and not a capability limit: a discoverability nicety should not be the change that touches the send-back's matcher. The author-time `IPD-S402` fix already gives the guessing author the answer at their FIRST wrong guess, which is the moment the item measured; an executor reading `IPD-S404` has by then already written a value the vocabulary accepts. If a reviewer wants it, it is a two-line follow-up plan whose `Scope-Paths` must include `agent_workflows/runner_shared.py` and `tests/test_finalize_sendback.py`.
  - Carrier-Declined: NOTHING IS OWED UNTIL THE REVIEWER RULES, and filing an item now would presuppose their answer. This row is the DEFERRED HALF of `OQ-01`, whose whole subject is whether a discoverability improvement justifies editing the finalize send-back's prose matcher; that is a risk-appetite judgement only the maintainer can make, and both answers are reachable with no residue (no means today's narrower scope is final, yes means a named two-file follow-up plan). The observation is not at risk of vanishing silently either: F-5 records the exact tuple, the test that pins it, and the MEASUREMENT that appending keeps the matcher matching, so whoever revisits it does not re-derive anything. An item reading "consider also naming the enum in the terminal-gate message" could not be closed on evidence independent of that ruling.
- ACCEPTING `verified` AS AN ALIAS is rejected, not deferred, on the evidence in F-6.
  - Carrier-Declined: There is nothing to carry. This is a REJECTED option rather than deferred work: F-6 measures that the vocabulary is closed by a coverage test, that an alias needs a `_VALIDATION_RULES` entry plus legal and illegal rows, and that a half-done alias would lint clean at `author` and fail at `pre-transition`, which is strictly worse than today's immediate rejection. No future owner is owed a decision that has been made against on evidence.
- REWRITING THE EXISTING PLANS that carry the old intro sentence is out of scope (F-7): most are terminal records, and the execution contract forbids changing what an executed plan records.
  - Carrier-Declined: Nothing is owed, and filing an item would assert a defect that does not exist. F-7 measures that EVERY `- Result:` value in the corpus is already IN vocabulary (zero out-of-vocabulary values across the whole tree), so no existing plan is wrong; the old intro sentence is merely less helpful than the new one. A sweep would rewrite terminal records the execution contract forbids changing, for zero behavioral gain, so it is a prohibition on this plan rather than outstanding work.
- `.aw/system/managed-sections.json` is deliberately absent from `Scope-Paths`: the installer owns those hashes, the recorded template hash already disagrees with the file at HEAD, and the two precedent commits that changed these same templates did not touch it.
  - Carrier-Declined: Nothing is owed BY THIS PLAN. This row records a prohibition, not a defect: the manifest hash is written by the installer on the next `aw install`, which is exactly the designed flow. Recorded for honesty and explicitly NOT claimed as this plan's work: the recorded hash for `templates/ipd.md` already disagrees with the file at HEAD, so the manifest is stale independently of anything here. That is an installer-manifest freshness question on a file this plan does not own, it predates this change, and no measurement here establishes it as a defect rather than the normal post-edit pre-install state, so filing an item would assert a gap this plan did not observe.
- No user-facing document is updated. Checked: `docs/authoring.md` is about workflow validation predicates and never mentions `- Result:`; no file under `docs/` states either vocabulary. The `CHANGELOG.md` is also left alone, since this changes no behavior a user of a released version depends on (a rejected value is still rejected and an accepted one still accepted); if the maintainer wants it noted, it is one additive line and no code changes.
  - Carrier-Declined: Nothing is owed. This is a negative FINDING (the search was performed and no document states either vocabulary), not deferred work, so there is no gap for a later owner to close. The `CHANGELOG.md` half is a reviewer preference the reviewer settles at review, and satisfying it needs no code and no separate record.

## Scope check

- Over-scope: none. Every declared path is modified by an E-item: `agent_workflows/ipd_schema.py` by E-01, `tests/test_ipd_schema.py` by E-02, `agent_workflows/ipd_authoring.py` and both `.aw/system/workflows/assess/templates/*.md` by E-03, `tests/test_ipd_authoring.py` by E-04.
- Under-scope: none expected, and the two candidates were checked rather than assumed. (a) `agent_workflows/ipd_lint.py` needs NO edit because it interpolates the schema's message verbatim (F-2); if the executor finds itself editing it, that means the message was moved rather than reworded. (b) `tests/test_ipd_templates.py` needs no edit because it compares the templates against the generator and both sides move together; if it fails after E-03, the templates were hand-edited instead of regenerated. Should either file genuinely require a change, MAKE the edit and JUSTIFY it to `aw ipd finalize` with a `--scope-reason`, which is what the scope fence is for; a scope question is not a stop condition (2026-09-01 maintainer ruling, recorded because this plan originally said "stop and report" here).
- THE NEIGHBOURING HAND-WRITTEN INTRO STRINGS WERE MEASURED, NOT ASSUMED, because "leave them alone" is only safe if none of them is byte-pinned to the generator. Measured at review with `_VALID_INTRO`/`_EXEC_INTRO` read from the module: `tests/test_ipd_lint.py` carries the DIFFERENT, shorter sentence `Validation-state rule: inspect evidence separately.` and contains NEITHER full generator intro; `tests/test_oc_runipd.py` carries a TRUNCATED variant (`Validation-state rule: inspect evidence in a separate pass.` with the second clause absent) and likewise contains neither full intro; and `tests/fixtures/conforming-orchestrator.md` DOES contain the full `_VALID_INTRO` verbatim but not `_EXEC_INTRO`, and is NOT byte-compared to `build_skeleton` anywhere (it is consumed as a fixture through `tests/support.CONFORMING_ORCHESTRATOR`). So all three are independent hand-written documents and E-03 cannot break them. The fixture is named here because the plan as first drafted did not mention it and it is the only one of the three that carries a full generator sentence, so it is the one a future reader would most reasonably suspect.

## Required tests / validation

- `python3 -m pytest tests/test_ipd_schema.py tests/test_ipd_authoring.py tests/test_ipd_templates.py tests/test_ipd_lint.py tests/test_plan_priority_required.py tests/test_finalize_sendback.py -o addopts=""` for the directly affected surfaces, with per-test counts. `test_finalize_sendback.py` is included as the guard that F-5's deferral held: its allowlist pin must still pass untouched.
- `python3 -m pytest` (bare; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the fast-marker scope) for regression.
- A RED-then-GREEN falsifiability proof for BOTH new tests, since a guard never seen to fail is not evidence: revert E-01's message change and observe E-02's test fail; revert E-03's intro change and observe E-04's test fail; then restore and observe both pass. Paste the actual failure and success output with exit codes.
- An END-TO-END demonstration that the reported defect is fixed: scaffold a plan, substitute `verified` for `pending` on its V-item, lint it, and paste the diagnostic showing the accepted values now appear in it.
- `aw sanitize --agent` must report no `fail`, since this plan's evidence quotes repository paths.

## Spec / documentation sync

No `.spec.md` file is amended, and none is in `Scope-Paths`. Checked against the governing spec, `ipd-structure-and-linting` (`.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`), which is the CONTRACT this plan must not violate and which it satisfies without amendment: Section 5.3 already enumerates the four allowed validation results and their checkbox/evidence table, Section 5.2 does the same for execution states, and Section 9.2 already states that `pre-transition` demands `Result: pass`. So the vocabulary is ALREADY specified; the defect is that the specified vocabulary is not surfaced in the tool's own output. Section 10's linter-contract list (item 11, "checkbox, execution-state, validation-result, and evidence-presence combinations are legal") constrains WHAT is checked, not the wording of a diagnostic, and Section 10's own diagnostic guidance is a SHOULD about stable rule codes and source locations, which this plan preserves (the codes and positions do not move). Section 14's canonical authored example quotes the two intro sentences E-03 extends; it is illustrative prose inside a fenced block rather than a byte-pinned artifact (no test compares it to the generator, unlike the two templates), so it does not have to change for the plan to be correct. Recording the option a reviewer may prefer: refreshing that fenced example so the spec's illustration matches the shipped scaffold would be a reasonable amendment, and it would oblige adding the spec to `Scope-Paths` per the AGENTS spec-amendment rule; this plan does not do it, because an amendment to an `implemented` spec should be a deliberate reviewer call and not a side effect of a discoverability fix.

## Open questions

### OQ-01: Should `IPD-S404`'s pre-transition messages also name the vocabulary, accepting an edit to the finalize send-back's prose trigger?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: NO CARRIER IS OWED WHILE THE QUESTION IS UNANSWERED, because each answer implies different work and filing an item now would presuppose the maintainer's decision. "Yes, name the enum at the terminal gate too" is a concrete two-file follow-up plan (`agent_workflows/ipd_lint.py` plus `agent_workflows/runner_shared.py` and `tests/test_finalize_sendback.py`); "no, the author-time message is enough" creates no work at all. The mechanical half is already settled and recorded where a later reader will find it: F-5 names the pinned tuple, the test that pins it, and the measurement that an appended parenthetical still satisfies `finalize_refusal_is_retryable`, so nothing is re-derived. The judgement half is whether a discoverability nicety is worth touching a run-control matcher, which is the maintainer's risk call and cannot be delegated to a backlog item. IF the ruling is yes, that ruling is the evidence that justifies an item, and this question names `aw backlog new` as its route.
- Resolution or deferral rationale: This plan answers the item's measured case (the FIRST wrong guess, at `author`) and deliberately leaves the terminal-gate messages alone, because those three strings are matched as SUBSTRINGS by `runner_shared.RETRYABLE_FINALIZE_FINDING_TEXTS` to decide whether a refused finalize is retried or the item is failed (F-5). The repository answers the FEASIBILITY question rather than the judgement one: appending a parenthetical to those messages keeps the matcher matching (measured: `finalize_refusal_is_retryable` returns True against a probe refusal carrying `IPD-S404 V-01: not 'pass' at pre-transition (results: pending|pass|blocked|failed)`), and `tests/test_finalize_sendback.py`'s pin would catch a change that did NOT keep matching. What it cannot decide is whether a discoverability improvement is worth touching a run-control matcher at all, which is a risk-appetite call and therefore the maintainer's. NOT BLOCKING: the deferred half is strictly additive, the plan's value does not depend on it, and nothing in E-01 through E-04 changes behavior if the answer is later yes. If the answer is yes, it becomes a follow-up plan declaring `agent_workflows/ipd_lint.py`, `agent_workflows/runner_shared.py`, and `tests/test_finalize_sendback.py`.

REVIEW DISPOSITION (2026-10-01, `/plan-review`): THIS QUESTION STAYS `open`, AND THE "silence is taken as accepting the narrower scope" CLAUSE IS WITHDRAWN. That clause is struck rather than honored because it made an UNANSWERED question self-closing: it let the absence of a maintainer reply count as the maintainer's reply, which is exactly the substitution the open-question mechanism exists to prevent. This review ran NON-INTERACTIVELY (`AW_EXECUTION_ROLE=worker`, neither stdin nor stdout a TTY), so there was no channel on which to ask, and a reviewer may not answer a question whose own `- Owner:` is `maintainer` by inferring consent from its own inability to ask. The question correctly remains `- Blocking: no`, so it does NOT hold the plan: per the 2026-09-10 maintainer ruling a non-blocking open question does not make a plan `NO-GO`, and E-01 through E-04 are complete and executable with the question unanswered.

WHAT REVIEW DID ADD IS THE MISSING HALF OF THE EVIDENCE, so the maintainer can now decide from the record rather than re-deriving: the feasibility half was already settled (appending keeps the matcher matching), but the RISK half was only asserted. It is now measured in F-9 and F-5. `IPD-S404` is NOT in `retryable_finalize_finding_codes()` (`{IPD-S401, IPD-S402, IPD-S403}`), so its prose is its ONLY matcher, and a REWORDED (rather than appended) message measurably returns `finalize_refusal_is_retryable() == False`, converting a bounded correction turn into a terminal failure. The decision the maintainer is being asked for is therefore sharper than "is a nicety worth it": it is whether to accept a change whose safe and unsafe forms differ by one editing choice with no author-time test signal between them. A reviewer cannot make that call, which is why it is still here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a Python invocation importing `agent_workflows.ipd_schema` that prints `validation_row_error("verified", False, False)` and `execution_row_error("done", False, False)`, showing each output contains its original prefix AND every member of its own vocabulary. Paste `git diff` over both predicates proving (a) the enumeration is rendered from `VALIDATION_RESULTS` / `EXEC_STATES` and not hand-spelled, and (b) no other branch, no `_VALIDATION_RULES` / `_EXEC_CHECKBOX` entry, and neither frozenset changed. Additionally print `validation_row_error("pending", False, False)` and `execution_row_error("pending", False, False)` and show both are still `None`, so a legal row gained no message.
  - Observed evidence: Verified Python invocation shows both error messages contain expected prefixes and full vocabularies, legal rows return None, and git diff proves derivation from frozensets.
    Python invocation:
    ```python
    >>> import agent_workflows.ipd_schema as S
    >>> print("v_err:", S.validation_row_error("verified", False, False))
    v_err: unknown validation result 'verified' (expected one of blocked, failed, pass, pending)
    >>> print("e_err:", S.execution_row_error("done", False, False))
    e_err: unknown execution state 'done' (expected one of blocked, failed, pending, performed)
    >>> print("legal_v:", S.validation_row_error("pending", False, False))
    legal_v: None
    >>> print("legal_e:", S.execution_row_error("pending", False, False))
    legal_e: None
    ```
    git diff over both predicates in `agent_workflows/ipd_schema.py`:
    ```diff
    @@ -1176,7 +1176,11 @@ _EXEC_NOTE_REQUIRED: FrozenSet[str] = frozenset(("blocked", "failed"))

     def execution_row_error(state: str, checked: bool, has_note: bool) -> Optional[str]:
         if state not in EXEC_STATES:
    -        return "unknown execution state '{0}'".format(state)
    +        return (
    +            f"unknown execution state '{state}' (expected one of "
    +            + ", ".join(sorted(EXEC_STATES))
    +            + ")"
    +        )
         if _EXEC_CHECKBOX[state] != checked:
             return "execution checkbox does not agree with state '{0}'".format(state)
         if state in _EXEC_NOTE_REQUIRED and not has_note:
    @@ -1197,7 +1201,11 @@ def validation_row_error(
         result: str, checked: bool, observed_nonempty: bool
     ) -> Optional[str]:
         if result not in VALIDATION_RESULTS:
    -        return "unknown validation result '{0}'".format(result)
    +        return (
    +            f"unknown validation result '{result}' (expected one of "
    +            + ", ".join(sorted(VALIDATION_RESULTS))
    +            + ")"
    +        )
         want_checked, want_obs = _VALIDATION_RULES[result]
         if want_checked != checked:
             return "validation checkbox does not agree with result '{0}'".format(result)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new assertion's source. Paste its RED-then-GREEN proof: revert E-01's message change (or stub the enumeration out), run the test, paste the ACTUAL failure output and exit code; restore, re-run, paste the passing output and exit code. Then paste a SECOND red proof of the other direction that matters: temporarily add a member to `VALIDATION_RESULTS` and show the NEW CONTENT ASSERTION (not some other test) fails because the message does not name it, then revert. THAT PROBE NEEDS THREE EDITS, NOT ONE, and the reason is measured: adding a member requires (a) the frozenset member, (b) its `_VALIDATION_RULES` entry, AND (c) a LEGAL and an ILLEGAL `STATES` row in `tests/test_ipd_schema.py`, because `test_the_state_tables_cover_their_closed_vocabularies` fails FIRST otherwise and proves nothing about the message. Measured at review: with only (a) and (b), `pytest tests/test_ipd_schema.py -o addopts="" -x` exits 1 on `test_the_state_tables_cover_their_closed_vocabularies` with `Items in the second set but not the first: 'zzprobe'`; with (c) added the suite returns `26 passed` and the coverage test is silent, which is the state in which a missing enumeration is the only remaining cause of failure. Paste the output of BOTH stages so the proof is attributable to the new assertion. Paste the per-test count for `tests/test_ipd_schema.py` run with `-o addopts=""` and confirm the two pre-existing `bogus` rows are still present and passing.
  - Observed evidence: Verified test assertion source, two-sided red-then-green proof with stubbed message and 3-edit probe with coverage test silent and new assertion failing, and 27 tests passing.
    New assertion source in `tests/test_ipd_schema.py`:
    ```python
        def test_unknown_value_messages_name_accepted_vocabularies(self):
            """The unknown-value messages must name every member of the closed vocabulary (plan uh9jsk).

            Asserts content, not merely truthiness (which the `bogus` table rows cover),
            so dropping the enumeration or missing a newly added vocabulary member fails here.
            """
            val_err = S.validation_row_error("bogus", False, False)
            self.assertIsNotNone(val_err)
            self.assertTrue(
                val_err.startswith("unknown validation result 'bogus'"),
                f"expected prefix missing: {val_err!r}",
            )
            for member in S.VALIDATION_RESULTS:
                self.assertIn(
                    member,
                    val_err,
                    f"validation_row_error('bogus', ...) missing vocabulary member {member!r} from message: {val_err!r}",
                )

            exec_err = S.execution_row_error("bogus", False, False)
            self.assertIsNotNone(exec_err)
            self.assertTrue(
                exec_err.startswith("unknown execution state 'bogus'"),
                f"expected prefix missing: {exec_err!r}",
            )
            for member in S.EXEC_STATES:
                self.assertIn(
                    member,
                    exec_err,
                    f"execution_row_error('bogus', ...) missing vocabulary member {member!r} from message: {exec_err!r}",
                )
    ```
    RED-then-GREEN proof (stubbing out enumeration in `validation_row_error` to return `"unknown validation result '{0}'".format(result)`):
    RED output (exit 1):
    ```
    FAILED tests/test_ipd_schema.py::ExecutionAndValidationStateTests::test_unknown_value_messages_name_accepted_vocabularies
    E   AssertionError: 'failed' not found in "unknown validation result 'bogus'" : validation_row_error('bogus', ...) missing vocabulary member 'failed' from message: "unknown validation result 'bogus'"
    tests/test_ipd_schema.py:1894: AssertionError
    1 failed, 26 deselected in 0.35s
    ```
    GREEN output upon restore (exit 0):
    ```
    tests/test_ipd_schema.py .                                               [100%]
    1 passed, 26 deselected in 0.19s
    ```
    SECOND red proof (temporarily adding `'zzprobe'` to `VALIDATION_RESULTS` with `validation_row_error` returning the static list without `'zzprobe'`):
    Stage 1 with only (a) and (b) (exit 1):
    ```
    FAILED tests/test_ipd_schema.py::ExecutionAndValidationStateTests::test_the_state_tables_cover_their_closed_vocabularies
    E   AssertionError: Items in the second set but not the first:
    E   'zzprobe' : the validation rows and VALIDATION_RESULTS have diverged; results with no row: ['zzprobe']. FIX: add a LEGAL and an ILLEGAL row stating the new result's checkbox and evidence rules.
    tests/test_ipd_schema.py:1873: AssertionError
    1 failed, 26 deselected in 0.30s
    ```
    Stage 2 with (c) legal and illegal rows added to `STATES` (exit 1):
    ```
    tests/test_ipd_schema.py ....F......................                     [100%]
    FAILED tests/test_ipd_schema.py::ExecutionAndValidationStateTests::test_unknown_value_messages_name_accepted_vocabularies
    E   AssertionError: 'zzprobe' not found in "unknown validation result 'bogus' (expected one of blocked, failed, pass, pending)" : validation_row_error('bogus', ...) missing vocabulary member 'zzprobe' from message: "unknown validation result 'bogus' (expected one of blocked, failed, pass, pending)"
    tests/test_ipd_schema.py:1906: AssertionError
    1 failed, 26 passed in 2.69s
    ```
    (Demonstrating coverage test passes and 26 other tests pass, while the new content assertion catches the missing member).
    Reverted to clean state. Per-test count for `tests/test_ipd_schema.py` with `-o addopts=""`:
    ```
    tests/test_ipd_schema.py ...........................                     [100%]
    27 passed in 1.52s
    ```
    Pre-existing `bogus` rows in `STATES` are intact and passing.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the regenerated `## Detailed Implementation Checklist (TODO)` and `## Validation and cross-check ...` intro lines from BOTH template files. Paste passing output for `tests/test_ipd_templates.py` run with `-o addopts=""` (this is the byte-parity proof that the templates were regenerated rather than hand-edited). Paste a Python invocation that scaffolds a child and an orchestrator through `build_skeleton` and lints each with `ipd_lint.lint_text(..., checkpoint="author", directory="pending")`, showing disposition `conforming` and no diagnostics for both. Paste `rg -n "_AUTHORING_PLACEHOLDERS" -A 20 agent_workflows/ipd_authoring.py` showing neither new sentence was added to the tuple, plus the value of `authoring_placeholders_resolved` on a scaffold (must still be False) and on that same text with every placeholder replaced (must be True).
  - Observed evidence: Verified regenerated template intro lines, test_ipd_templates byte parity passes (10 passed), scaffold lint conforming for both kinds, and _AUTHORING_PLACEHOLDERS unpolluted.
    Regenerated intro lines from `.aw/system/workflows/assess/templates/ipd.md`:
    ```markdown
    ## Detailed Implementation Checklist (TODO)

    Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

    ## Validation and cross-check (verify before reporting done)

    Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.
    ```
    Regenerated intro lines from `.aw/system/workflows/assess/templates/orchestrator-ipd.md`:
    ```markdown
    ## Detailed Implementation Checklist (TODO)

    Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

    ## Validation and cross-check (verify before reporting the Set complete)

    Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.
    ```
    `python3 -m pytest tests/test_ipd_templates.py -o addopts=""` (exit 0):
    ```
    tests/test_ipd_templates.py ..........                                   [100%]
    10 passed in 0.28s
    ```
    Scaffold & lint Python check:
    ```python
    Child disposition: conforming diagnostics: []
    Orch disposition: conforming diagnostics: []
    Both scaffolds lint conforming with 0 diagnostics.
    ```
    `rg -n "_AUTHORING_PLACEHOLDERS" -A 20 agent_workflows/ipd_authoring.py`:
    ```
    126:_AUTHORING_PLACEHOLDERS = (
    127-    "- Concern: TODO.",
    128-    "- Scope: TODO.",
    129-    "- Scope-Paths: TODO",
    130-    "- Item-Dependencies: unresolved",
    131-    "- Work-Kind: unresolved",
    132-    "- Priority: unresolved",
    133-    _SECTION_BODY[
    134-        S.H_GOAL
    135-    ],  # "TODO: one or two sentences on what this plan achieves and why."
    136-    "- [ ] E-01 TODO one observable action.",
    137-    "  - Expected outcome: TODO observable result.",
    138-    "  - Required evidence: TODO falsifiable evidence.",
    139-    "### OQ-01: TODO a question",
    140-    "TODO: approval + execution gate prose",
    141-    UNASSIGNED_MARKER,  # any remaining unassigned `E-NEW` leaf means still authoring
    142-)
    ```
    `authoring_placeholders_resolved` check:
    - On scaffold: `False`
    - With placeholders replaced: `True`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new test's source. Paste its RED-then-GREEN proof against E-03's change: revert one intro sentence, run the test, paste the actual failure output and exit code, restore and paste the pass. Paste a SECOND red proof that the negative direction bites: temporarily insert `verified` INTO ONE INTRO'S RENDERED VALUE LIST (not elsewhere in the document, per E-04's scoping note), show the test fails, revert, show it passes. ALSO paste the proof that the negative assertion is SATISFIABLE in its correct state, by showing the test GREEN against an unmodified scaffold: this is the specific trap E-04 records, since the document-wide form of this assertion is red at HEAD because the `## Required tests / validation` placeholder already reads `TODO: how the executed plan is verified.`. Paste the per-test count for `tests/test_ipd_authoring.py` with `-o addopts=""`. Finally paste the END-TO-END defect demonstration: scaffold a plan, set its V-item `- Result: verified`, lint at `author`, and show the emitted `IPD-S402` diagnostic now names the accepted values; then paste the full bare `python3 -m pytest` summary line as regression evidence.
  - Observed evidence: Verified test source in test_ipd_authoring.py, red-then-green proof against E-03, negative red proof on out-of-vocab token, satisfiability on unmodified scaffold, 25 tests pass, e2e demo names accepted values, and full suite passes.
    New test source in `tests/test_ipd_authoring.py`:
    ```python
    class ScaffoldVocabularyIntroTests(unittest.TestCase):
        """Scaffolded plans must state both closed vocabularies in their section intros (plan uh9jsk)."""

        def test_scaffold_intros_state_closed_vocabularies_and_no_unaccepted_values(self):
            expected_exec = set(S.EXEC_STATES)
            expected_valid = set(S.VALIDATION_RESULTS)

            for kind in ("child", "orchestrator"):
                text = A.build_skeleton(
                    kind=kind,
                    title=f"Vocabulary Intro Test {kind}",
                    author="tester",
                    when="2026-10-01",
                    set_name="vocabprobe",
                    order=1 if kind == "child" else 0,
                    plan_id="vcb123",
                )
                lines = text.splitlines()
                exec_intro = None
                valid_intro = None
                for i, line in enumerate(lines):
                    if line.startswith("## ") and line[3:].strip() == S.H_EXECUTION:
                        for candidate in lines[i + 1 : i + 5]:
                            if candidate.startswith("Execution-state rule:"):
                                exec_intro = candidate
                                break
                    elif line.startswith("## ") and line[3:].strip() in (
                        S.H_VALIDATION_CHILD,
                        S.H_VALIDATION_ORCH,
                    ):
                        for candidate in lines[i + 1 : i + 5]:
                            if candidate.startswith("Validation-state rule:"):
                                valid_intro = candidate
                                break

                self.assertIsNotNone(
                    exec_intro, f"missing execution intro in {kind} scaffold"
                )
                self.assertIsNotNone(
                    valid_intro, f"missing validation intro in {kind} scaffold"
                )

                for state in expected_exec:
                    self.assertIn(
                        state,
                        exec_intro,
                        f"execution intro in {kind} missing member {state!r}",
                    )
                for result in expected_valid:
                    self.assertIn(
                        result,
                        valid_intro,
                        f"validation intro in {kind} missing member {result!r}",
                    )

                self.assertIn("'performed'", exec_intro)
                self.assertIn("'pass'", valid_intro)

                m_exec = re.search(r"Accepted execution states:\s*([^;]+);", exec_intro)
                self.assertIsNotNone(
                    m_exec, f"could not locate execution states list in {kind} intro"
                )
                exec_tokens = {t.strip() for t in m_exec.group(1).split(",") if t.strip()}
                unrecognized_exec = exec_tokens - expected_exec
                self.assertEqual(
                    unrecognized_exec,
                    set(),
                    f"execution intro in {kind} advertises out-of-vocabulary value: {unrecognized_exec}",
                )
                self.assertEqual(
                    exec_tokens,
                    expected_exec,
                    f"execution intro in {kind} does not match EXEC_STATES",
                )

                m_valid = re.search(r"Accepted validation results:\s*([^;]+);", valid_intro)
                self.assertIsNotNone(
                    m_valid, f"could not locate validation results list in {kind} intro"
                )
                valid_tokens = {
                    t.strip() for t in m_valid.group(1).split(",") if t.strip()
                }
                unrecognized_valid = valid_tokens - expected_valid
                self.assertEqual(
                    unrecognized_valid,
                    set(),
                    f"validation intro in {kind} advertises out-of-vocabulary value: {unrecognized_valid}",
                )
                self.assertEqual(
                    valid_tokens,
                    expected_valid,
                    f"validation intro in {kind} does not match VALIDATION_RESULTS",
                )
    ```
    RED-then-GREEN proof against E-03 (reverting vocabulary sentence in `_VALID_INTRO`):
    RED output (exit 1):
    ```
    FAILED tests/test_ipd_authoring.py::ScaffoldVocabularyIntroTests::test_scaffold_intros_state_closed_vocabularies_and_no_unaccepted_values
    E   AssertionError: 'failed' not found in 'Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.' : validation intro in child missing member 'failed'
    tests/test_ipd_authoring.py:610: AssertionError
    1 failed, 24 deselected in 0.23s
    ```
    GREEN output upon restore (exit 0):
    ```
    tests/test_ipd_authoring.py .                                            [100%]
    1 passed, 24 deselected in 0.26s
    ```
    SECOND red proof (negative direction: inserting `'verified'` into `_VALID_INTRO`'s rendered value list):
    RED output (exit 1):
    ```
    FAILED tests/test_ipd_authoring.py::ScaffoldVocabularyIntroTests::test_scaffold_intros_state_closed_vocabularies_and_no_unaccepted_values
    E   AssertionError: Items in the first set but not the second:
    E   'verified' : validation intro in child advertises out-of-vocabulary value: {'verified'}
    tests/test_ipd_authoring.py:647: AssertionError
    1 failed, 24 deselected in 0.33s
    ```
    Reverted to clean state.
    Satisfiability proof: test runs GREEN on unmodified scaffold:
    ```
    tests/test_ipd_authoring.py .........................                    [100%]
    25 passed in 1.48s
    ```
    Per-test count for `tests/test_ipd_authoring.py` with `-o addopts=""`:
    `25 passed in 1.48s`
    END-TO-END defect demonstration:
    ```
    IPD-S402 line 82: V-01: unknown validation result 'verified' (expected one of blocked, failed, pass, pending)
    ```
    Full bare `python3 -m pytest` summary line:
    `4170 passed, 2 skipped, 3 warnings in 105.17s (0:01:45)`
  - Result: pass

## Approval and execution gate

This plan is authored `to-review` and must not be executed before it is reviewed and explicitly approved.
The executor of this plan MUST: read this plan in full before editing; keep every change inside the declared
Scope-Paths, and where an out-of-scope edit proves genuinely necessary, MAKE it and then JUSTIFY it to
`aw ipd finalize` with a `--scope-reason` per out-of-scope path (and a `--scope-ack` per declared-but-unmodified
path) rather than stopping over a scope question; change neither `VALIDATION_RESULTS` nor
`EXEC_STATES` nor any `_VALIDATION_RULES` / `_EXEC_CHECKBOX` entry, since the plan's whole safety argument
is that no value's acceptance changes; leave the three `runner_shared.RETRYABLE_FINALIZE_FINDING_TEXTS`
strings and the `IPD-S404` wording untouched (F-5); REGENERATE both templates from `build_skeleton` rather
than hand-editing them; perform every RED-then-GREEN proof the `V-*` items demand rather than asserting the
guards work; paste ACTUAL runner output with exit codes for every test claim; and commit only the paths it
modified through `aw commit <plan> -- <paths>`, never `git add -A`, and never push.

THE ONE GENUINE STOP CONDITION, stated separately because it is NOT a scope question: if the executor finds
`validate_metadata`'s `Readiness` branch no longer renders its enum from `READINESS_VALUES`, or finds
`ipd_lint.check_states` no longer interpolating the schema's message verbatim, then the precedent E-01 copies
and the layering F-2 establishes have both moved, and the plan's design premise is void. That is an absent
prerequisite rather than a scope decision, so report it instead of improvising a new shape.

LIFECYCLE OWNERSHIP IS CONDITIONAL. If this plan is executed by `aw oc run` or `aw agy run` with the runner
owning the lifecycle, the executor must NOT move this file or set its terminal status: the runner performs
the atomic finalize after its own checks. If it is executed by an agent directly, that agent performs the
terminal transition itself, and only after `aw ipd lint --phase pre-transition` reports conforming and every
`V-*` above carries concrete pasted evidence with `- Result: pass`.
