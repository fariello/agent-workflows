# IPD: Correct the Token control escape-hatch count in docs/cli-agent-protocol.md and document --limit with its measured per-verb reach

- Date: 2026-10-02
- Kind: child
- Concern: `docs/cli-agent-protocol.md` opens its `## Token control` section with the sentence "Two escape hatches tune the token cost:" and then lists exactly two bullets, `--fields <a,b,c>` and `--verbose`. The count contradicts the surface the repository ships and contradicts a sibling document: `docs/cli-output-contract.md` Section 6 ("Token Control and Escape Hatches") lists THREE hatches, naming `--fields`, `--limit` and `--verbose`. Measured at HEAD `c1172677c`: a parser walk finds nine leaves declaring `--limit` (`aw check`, `aw find`, `aw group`, `aw index`, `aw rename`, `aw research index`, `aw runs analyze`, `aw runs query`, `aw search`), so the flag is real and declared, not aspirational. The protocol reference is the document an agent is pointed at to learn how to bound output, and its own `## Stream truncation is honest` section already describes `--limit` bounding a stream ("When a stream is bounded (for example with `--limit`)") while its worked `find` example record carries `"next":"aw find plans --agent --limit 10"`. So the omission is confined to the `## Token control` enumeration and its count word, NOT to the whole document; the item's phrase "omits it entirely" is an overstatement this plan does not repeat (F-01).
- Scope: Correct the `## Token control` section of `docs/cli-agent-protocol.md` so its introductory count matches its own bullet list, and add a `--limit` bullet whose wording is TRUE of the measured per-verb behavior rather than promising a uniform bound the repository does not deliver. Add a behavioral guard (`tests/test_cli_agent_protocol_doc.py`) that reads the shipped document and fails if the stated hatch count disagrees with the number of hatch bullets the section actually lists, so this class of drift is caught mechanically instead of by a reader. Does NOT change any production code, does NOT wire `--limit` into any verb that currently ignores it (that is backlog `4uw9gy`'s work and needs a per-verb design decision), does NOT touch `docs/cli-output-contract.md` (already correct), does NOT touch `docs/cli-human-guide.md`, and does NOT alter any record schema, flag, or exit code.
- Scope-Paths: docs/cli-agent-protocol.md, tests/test_cli_agent_protocol_doc.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qya0k
- Set: 9qya0k
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: moegsl

## Workflow history
- 2026-10-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: moegsl verified (set 9qya0k, attempt 1).
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review: APPROVE WITH REVISIONS APPLIED; readiness go-pending-approval

- 2026-10-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Readiness go-pending-approval. Re-checked at HEAD `0f8de354f`: `## Token control` still says `Two` with two bullets; contract Section 6 still lists three; `4uw9gy` now `graduated` to `2zvxhx`.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `9qya0k`, graduating it. Every claim the item makes was RE-MEASURED in this lane at HEAD `c1172677c` rather than carried forward, and the measurement both CONFIRMED the core defect and CORRECTED two of the item's statements, which is why the wording this plan prescribes differs from the item's "SUGGESTED FIX". CONFIRMED: the count sentence says "Two" and lists two bullets while `docs/cli-output-contract.md` Section 6 lists three; nine CLI leaves declare `--limit`. CORRECTED, FIRST (F-01): the item says the protocol doc "omits it entirely", but `--limit` appears twice in that file already (the `## Stream truncation is honest` prose and the worked `find` summary record's `next` field), so the defect is scoped to the `## Token control` enumeration and this plan does not assert the broader claim. CORRECTED, SECOND (F-02): the item's constraint paragraph cites only `wdazvp` (`--limit` inert on `aw find --agent`), but the measured breadth is far wider and is ALREADY FILED as backlog `4uw9gy` (`Blocks-Release: next`), which the item does not cite because `4uw9gy` was filed later the same day; measured here, `--limit` is honored on only ONE of the nine leaves (`aw runs query`, proven below), means a DIFFERENT thing on two (`aw index` and `aw research index`, where it is an INDEX.md hot-window size and is correctly honored), and is silently discarded on the rest. That measurement is what decides the bullet's wording: a flat "`--limit <N>`: bound the stream" sentence would be a NEW false claim on eight of nine leaves, trading an undercount for a lie, so E-02 writes a bullet that states the bound and NAMES the reach caveat with a pointer to the tracking item. THE ITEM LEFT A SEQUENCING QUESTION OPEN ("or it should be written after `wdazvp` resolves") AND THIS PLAN RESOLVES IT RATHER THAN WAITING: see OQ-01. Resolved from repository evidence: `docs/cli-output-contract.md` Section 6 ALREADY ships the unqualified three-item list today, so the repository's published contract already promises `--limit` with no restriction; leaving the protocol reference at "Two" does not protect anyone from that promise, it only makes the two documents disagree about their own surface. A caveated bullet is therefore strictly more accurate than both the current undercount and the sibling document's unqualified row. Blocking status: none. Also measured that no test anywhere reads `docs/cli-agent-protocol.md` (zero matches for the filename under `tests/`), so the guard E-03 adds is this document's first behavioral coverage and nothing existing constrains the edit. `aw ipd lint --phase author` reports conforming.

## Goal

Make the agent-facing protocol reference tell the truth about its own token-control surface: three hatches enumerated as three, with the `--limit` bullet describing the bound it really provides and naming the verbs where it is not yet honored, so an agent that needs to cap an expensive records query learns the flag exists AND learns not to trust it blindly. Add the mechanical guard that keeps the stated count and the listed bullets from drifting apart again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure the reach, then write the document

- [x] E-01 RE-MEASURE THE PER-VERB `--limit` REACH AT YOUR OWN BASE COMMIT, BEFORE EDITING THE DOCUMENT, and record the result as the evidence the bullet's wording rests on.

  WHY THIS IS AN EXECUTION STEP AND NOT AUTHORING TRIVIA: the bullet E-02 writes makes a factual claim about which commands honor the flag. That claim must be true at the commit that ships it, not at the commit this plan was authored against, and backlog `4uw9gy` is `graduated` (re-checked at review) to plan `2zvxhx` (`Status: reviewed`, `Readiness: go-pending-approval`, `Blocks-Release: next`), which makes `--limit` honored on `aw check` and `aw search` under `--agent` and AMENDS `docs/cli-output-contract.md` Section 6's `--limit` bullet; plan `okiso1` (also `reviewed`) makes `aw find --agent` emit a bounded stream. So the reach is EXPECTED to change under you if either runs first. If a fix has landed, E-02's caveat must shrink to match; if none has, it stands.

  RUN EACH LEAF TWICE, with and without the flag, and compare. The nine leaves declaring `--limit` are `aw check`, `aw find`, `aw group`, `aw index`, `aw rename`, `aw research index`, `aw runs analyze`, `aw runs query`, `aw search`. For the read-only ones, a sufficient probe is the pair `aw <verb> plans --agent --limit <small-N>` against `aw <verb> plans --agent`, comparing emitted record counts. Classify `aw runs analyze` from BOTH its help text (`Maximum records per agent stream page`) and a probe; a probe that emits one `result` record with and without the flag (as measured at review, on a lane with zero runs) is INCONCLUSIVE, not evidence of IGNORED, so record it as such unless the probe has enough runs to page. Do NOT probe `aw rename` or `aw group` by MUTATING anything: they are mutating verbs and their `--limit` is the shared `"Max rows (index/find)."` argument registered by the same loop that serves `find`; read the registration and say so rather than renaming a record to find out.

  THE AUTHORING MEASUREMENT, for you to confirm or correct. `aw runs query findings --agent --limit 2` emitted a terminating summary reading `"total":4,"emitted":2,"omitted":2,"complete":false,"next":"aw runs query findings --limit 4"`, which is the bound working exactly as the protocol's own `## Stream truncation is honest` section describes. `aw find plans --agent --limit 3` emitted 1235 lines, byte-identical in count to the unflagged run. `aw check plans --agent --limit 1` emitted one result record whose `diagnostics` array carried all 70 findings. `aw index plans --agent --limit 1` emitted the same single line as the unflagged run, and on that verb `--limit` legitimately means an INDEX.md hot-window size (`--limit LIMIT  Hot-window size for INDEX.md (default 40).`), as it does on `aw research index`.
  - Depends on: none
  - Expected outcome: a recorded per-verb table of honored / ignored / different-meaning, captured as pasted command output, which either matches the authoring measurement or supersedes it. No file in the repository is modified by this step.
  - Execution state: performed

- [x] E-02 CORRECT THE `## Token control` SECTION of `docs/cli-agent-protocol.md`: fix the count word and add the `--limit` bullet in list position between `--fields` and `--verbose`, matching the order `docs/cli-output-contract.md` Section 6 already uses.

  THE EXACT DEFECT: the section's second line reads `Two escape hatches tune the token cost:` and is followed by a `--fields` bullet and a `--verbose` bullet. Change the count word to `Three` and insert the new bullet.

  THE BULLET MUST BE TRUE ON EVERY LEAF IT APPLIES TO, which is the whole difficulty and the reason E-01 precedes it. State three things: that `--limit <N>` bounds a stream to at most `N` items with the terminating `summary` carrying `total`/`emitted`/`omitted` and a `next` continuation command (which cross-references the `## Stream truncation is honest` section immediately above, already correct); that it is NOT honored uniformly across every command that accepts it, naming backlog `4uw9gy` as the tracking item so a reader can find the current state rather than trusting a sentence that will age; and that on the index-building verbs (`aw index`, `aw research index`) it carries a DIFFERENT meaning, the INDEX.md hot-window size, so a reader does not mistake those for the same bound. Write the caveat from YOUR E-01 measurement, not from the authoring paragraph above. ALSO MIRROR THE CONTRACT AS IT READS AT EXECUTION: if `2zvxhx` has landed, `docs/cli-output-contract.md` Section 6's `--limit` bullet will state a per-kind form (counts in the `result` record on `check`/`search`, in the terminating `summary` on streams), and this bullet must not contradict it. If `4uw9gy` has reached `done` and E-01 finds the flag honored wherever it is a row bound, drop the tracking-item pointer rather than cite a closed item.

  OBSERVE THE USER-FACING PROSE RULE. This is an end-user document, so write NO em dash and NO en dash; ASCII hyphens only (`docs_check.check_no_unicode_dashes` enforces this and `AGENTS.md` states it for user-facing prose). Keep the existing bullet style and the surrounding line wrapping.

  CHANGE NOTHING ELSE IN THE FILE. Do not restructure the section, do not touch `## Stream truncation is honest`, do not amend the worked example records, and do not edit `docs/cli-output-contract.md`, whose Section 6 list is already correct and is the source this plan reconciles toward.
  - Depends on: E-01
  - Expected outcome: `## Token control` states three hatches and lists three bullets, the `--limit` bullet describes the bound and its measured reach caveat, and the only changed file in the working tree is `docs/cli-agent-protocol.md`.
  - Execution state: performed

### Task group 2: guard the count against future drift

- [x] E-03 ADD `tests/test_cli_agent_protocol_doc.py`, a behavioral guard that reads the SHIPPED document and fails when its stated hatch count disagrees with the number of hatch bullets it lists.

  WHAT MAKES THIS A BEHAVIORAL TEST AND NOT A CODE-STRUCTURE PIN. `GUIDING_PRINCIPLES` P16 and the `AGENTS.md` test contract forbid tests that read PRODUCTION SOURCE with `inspect`/`ast`/regex to pin structure. This test reads a DOCUMENT, which is the artifact under test and is itself the deliverable, exactly as the existing `agent_workflows/docs_check.py` checks operate on Markdown text. It must NOT read `agent_workflows/cli.py` or assert on any symbol.

  ASSERT THE INVARIANT, NOT THE PROSE. Parse the `## Token control` section, extract the count word from its introductory sentence, map the English number word to an integer, count the top-level `- ` bullets in the section, and assert the two agree. That is a relationship between two parts of the file, so it survives rewording: an author who adds a fourth hatch and updates the word keeps the test green, while one who adds a bullet and forgets the word turns it red. Do NOT assert the literal sentence text, and do NOT assert a frozen bullet list, both of which `AGENTS.md` names as the forbidden shape ("NEVER assert that specific text, docstrings, or comment banners remain unchanged").

  ASSERT `--limit` IS ENUMERATED, as a second, independent test: the section must contain a bullet whose flag token is `--limit`. This is the regression that backlog item `9qya0k` records, and it is the one assertion that must fail at the base commit.

  ASSERT THE TWO DOCUMENTS AGREE ON THE HATCH SET, as a third test: the set of flag tokens enumerated in `docs/cli-agent-protocol.md` `## Token control` must equal the set enumerated in `docs/cli-output-contract.md` Section 6. Normalize `--verbose / --json` (the contract's combined bullet) to the hatch tokens before comparing, and document that normalization in the test. Also EXCLUDE bullets that name no flag: the contract's Section 6 opens with a `**Compact Defaults**` bullet that is not a hatch, so extract only bullets whose first token is a backticked `--flag` (measured at review: a regex `- (?:\*\*)?`(--[a-z-]+)` over each section yields `['--fields', '--verbose']` for the protocol today and `['--fields', '--limit', '--verbose']` for the contract). Locate each section by its heading text (`Token control`), not by section number, so a renumbering does not break the guard. This is what prevents the two files drifting apart again in either direction, which is the actual root cause here.

  SHOW IT RED FIRST. AUTHOR THIS MODULE BEFORE PERFORMING E-02 (it depends only on E-01), run it against the unedited document, and capture the failure; that is V-03's required evidence. Then perform E-02 and re-run. Do NOT use `git stash` to fake the base state: in a shared checkout it also stashes a co-worker's uncommitted work. If E-02 was already applied, restore only `docs/cli-agent-protocol.md` from `HEAD` into a temp copy and point the test at it via a module-level path constant for that one run, or revert just that file and re-apply your own edit, rather than reconstructing the failure from memory.
  - Depends on: E-01
  - Expected outcome: a new test module, three tests, whose `--limit`-enumeration and cross-document-agreement assertions FAIL at the base commit and PASS after E-02, with both runs captured verbatim.
  - Execution state: performed

## Project conventions discovered (Step 0)

- USER-FACING PROSE CARRIES A DASH BAN, and this document is user-facing. `AGENTS.md` restricts the no-em-dash / no-en-dash rule to user-facing prose (READMEs, CHANGELOG, end-user docs) and explicitly exempts internal and AI-facing artifacts such as this plan. `docs_check.check_no_unicode_dashes` is the deterministic enforcement, reporting a `no-unicode-dashes` finding per offending line.
- THE DOCS CHECKERS EXIST BUT ARE NOT WIRED INTO `aw check`. `agent_workflows/docs_check.py` provides `check_no_unicode_dashes`, `check_internal_links`, `check_aw_commands`, `check_doc` and `check_docs_dir`; its only consumer anywhere in the package is `release_readiness.gate_docs_checks`, which takes a caller-supplied findings sequence. Pending sibling plan `t9lcdu` is restoring that module's own test coverage and states in its own scope that wiring these modules into `aw check` or a hook is OUT of scope. So this plan adds a test module rather than a check rule, which is the convention the repository currently follows for document-level invariants, and it does not contest `t9lcdu`'s paths.
- NO TEST READS THIS DOCUMENT TODAY. A search for the filename `cli-agent-protocol` under `tests/` returns zero matches, so E-03's module is its first behavioral coverage and no existing expectation constrains E-02's edit.
- THE `--limit` ARGUMENT IS REGISTERED IN THREE PLACES, not one, which is why its meaning is not uniform. A shared loop in `cli.py` registers `--limit` with help text `"Max rows (index/find)."` for the six noun-verbs `check`, `find`, `search`, `index`, `rename`, `group`; `_p_runs_analyze` and `_p_runs_query` each register their own with their own help text and their own bound; and `p_research_index` registers it as a hot-window size. Per backlog `4uw9gy`, the only consumer of the resolved `ctx.limit` value in the package is `renderers.AgentRenderer.render_stream`, while `run_analytics_cli.emit_query_agent_stream` honors its bound by computing it independently in `run_analytics_query` (`MAX_ROW_LIMIT`, `_parse_limit`). That split is the mechanical reason eight of nine leaves ignore the flag.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence | Effect on this plan |
| --- | --- | --- | --- |
| F-01 | The item's "omits it entirely" overstates the defect. `--limit` already appears twice in `docs/cli-agent-protocol.md`. | The `## Stream truncation is honest` section reads "When a stream is bounded (for example with `--limit`)", and the worked `find` summary example carries `"next":"aw find plans --agent --limit 10"`. | The concern and scope are written against the `## Token control` ENUMERATION only. E-02 is forbidden from editing the truncation section, which is already correct. |
| F-02 | `--limit` is honored on ONE of the nine declaring leaves, means something different on two more, and is silently discarded on the rest. | Measured at HEAD `c1172677c`: `aw runs query findings --agent --limit 2` returned `"total":4,"emitted":2,"omitted":2,"complete":false` plus a `next`; `aw find plans --agent --limit 3` returned 1235 lines, equal to the unflagged count; `aw check plans --agent --limit 1` returned one record carrying all 70 diagnostics; `aw index plans --agent --limit 1` matched its unflagged output and documents `--limit` as `"Hot-window size for INDEX.md (default 40)."`, as does `aw research index`. | This is the decisive finding. It forbids a flat "`--limit` bounds the stream" bullet, which would be false on eight leaves. E-02 must caveat the reach and E-01 must re-measure it at execution time. |
| F-03 | The breadth in F-02 is ALREADY FILED and release-gated, as backlog `4uw9gy` (`- Status: open` at authoring, `graduated` to plan `2zvxhx` by review; `- Work-Kind: bug`, `- Blocks-Release: next`, Set `limitreach`), which independently measured the same nine-leaf parser walk and the same per-verb results. | `.aw/records/backlog/graduated/20261001-limitreach-01-4uw9gy-limit-inert-on-check-index-search-agent.backlog.md` (moved from `open/` since authoring). | Keeps this plan a DOCUMENTATION fix and nothing more. The `--limit` bullet cites `4uw9gy` as the tracking item so the caveat points at live state instead of rotting. No `Blocks-Release` is inherited here: item `9qya0k` carries none and is `Work-Kind: chore`, so per `AGENTS.md` it is not auto-gated. |
| F-04 | `aw find --agent --limit` is inert in BOTH output modes, not only under `--agent`. | `aw find plans --agent --limit 3` and `aw find plans --limit 3` each emitted 1235 lines, as did the unflagged run. | Noted for `wdazvp`/`okiso1`, whose scope is the `--agent` branch. This plan changes no code, so the observation is recorded rather than acted on; it is not folded into the bullet, which describes the agent protocol. |
| F-05 | `--fields`, the hatch the current bullet does document, genuinely works. | `aw check plans --agent --fields findings` returned `{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":70}`, the envelope plus the one requested field. | Confirms the section's existing two bullets are accurate, so E-02 is a pure addition plus a count correction, with no need to re-verify or reword the `--fields` and `--verbose` bullets. |
| F-06 | `aw search --agent` exits 2 when given no pattern, so a naive probe measures the wrong thing. | `aw search plans --agent --limit 3` returned `{"kind":"error","outcome":"cannot-run","exit":2,...}`; supplying a pattern (`aw search plans "the" --agent --limit 2`) returned a `clean` result record whose output was identical with and without the flag. | E-01 must probe `search` WITH a pattern. Recorded so the executor does not mistake the usage error for the inertness being measured. |
| F-07 | The sibling document this plan reconciles toward is unqualified. `docs/cli-output-contract.md` Section 6 lists `--limit <N>` as bounding "stream item emission to at most `N` items" with no per-verb restriction. | `docs/cli-output-contract.md` `## 6. Token Control and Escape Hatches`. | Resolves OQ-01 toward fixing now rather than waiting: the unqualified promise is already shipped, so a caveated bullet in the protocol reference is strictly more accurate than today's silence. Narrowing the contract's own row is NOT in scope; that belongs with `4uw9gy`'s fix. |

## Proposed changes (ordered, validatable)

1. Measure the per-verb `--limit` reach at the execution base commit and record it as pasted output (E-01). No file changes.
2. In `docs/cli-agent-protocol.md` `## Token control`, change the count word from `Two` to `Three` and insert a `--limit` bullet between the `--fields` and `--verbose` bullets, stating the bound, the measured reach caveat with its tracking item, and the different index-hot-window meaning (E-02).
3. Add `tests/test_cli_agent_protocol_doc.py` with three tests: count word agrees with bullet count, `--limit` is enumerated, and the hatch set agrees with `docs/cli-output-contract.md` Section 6 (E-03).

## Deferred / out of scope (with reason)

- WIRING `--limit` INTO THE VERBS THAT IGNORE IT. Deferred to backlog `4uw9gy`, which is `graduated` to plan `2zvxhx` (for `check` and `search`), `Work-Kind: bug` and `Blocks-Release: next`, and which states why the fix needs a per-verb design decision first: `aw check` and `aw index` emit a single result record whose payload is a diagnostics array, so "one item" has no settled meaning, and bounding an in-record array would need the summary counts to live somewhere a result record has no field for. Folding a schema decision into a documentation correction would be scope creep on a `low`-priority `chore`.
  - Carrier: 4uw9gy
- NARROWING `docs/cli-output-contract.md` SECTION 6. Out of scope by F-07. That section is the normative contract; its unqualified `--limit` row becomes true when `4uw9gy` lands, and editing a normative contract to match a temporary implementation gap is the wrong direction. This plan makes the REFERENCE agree with the contract, not the reverse.
  - Carrier: 4uw9gy
- `aw find --limit` BEING INERT IN HUMAN MODE TOO (F-04). `wdazvp` and its plan `okiso1` own the `find` token-control surface, so the observation is handed to that plan rather than filed as a third overlapping record, which would fragment one defect across three places. If `okiso1` executes without covering the human path, that is the moment to file a fresh item.
  - Carrier: no88yi
- WIRING `docs_check` INTO `aw check` OR A PRE-COMMIT HOOK. Out of scope here, and explicitly out of scope for sibling plan `t9lcdu` as well, which is restoring that module's own coverage and says so in its scope. E-03's test module is the enforcement this plan ships.
  - Carrier-Declined: This is not an obligation this plan incurs or discharges; it is a pre-existing architectural choice of the repository (the `docs_check` module has had exactly one consumer, `release_readiness.gate_docs_checks`, since it was written) that is named here only to explain why E-03 adds a test module instead of a check rule. Nothing vanishes when this plan reaches `executed`: the unwired module is unchanged by this plan and remains exactly as discoverable afterwards as before.

## Scope check

- Over-scope: none. Both declared paths are edited by the checklist: `docs/cli-agent-protocol.md` by E-02 and `tests/test_cli_agent_protocol_doc.py` by E-03.
- Under-scope: Deliberate and enumerated above. No production code changes, so the eight leaves that ignore `--limit` still ignore it after this plan; the bullet DESCRIBES that state rather than fixing it, and `4uw9gy` carries the fix with a release gate. A reviewer who wants the wiring in this plan should say so before approval, since it would change `- Scope-Paths:`, the `- Work-Kind:` (chore to bug) and the release gate.

## Required tests / validation

The bar is the BARE suite, `python3 -m pytest`, run before and after with the actual summary line pasted. THE SUITE IS NOT GREEN AT BASE: measured at review (HEAD `0f8de354f`) a bare run gave `5 failed, 4636 passed, 2 skipped, 3 warnings in 376.84s` and a re-run named four failing nodes (`test_readiness_absence_invariant.py::test_corpus_partition_pre_review_plans_lack_readiness_field`, `test_spec_review_attestation.py::...::test_every_real_spec_in_this_repository_still_conforms`, `test_selector_type_containment.py::test_must_not_refuse_matrix`, `test_run_finding_reachability.py::...::test_unreachable_binding_refusal_fires_under_perturbation`), several of them live-corpus or load-sensitive. So capture YOUR baseline as a FAILING-NODE-ID SET and treat as blocking only a failing node id absent from that set; do not compare totals. Per `AGENTS.md` do not add `-n0`, a second `-q`, or `-p no:randomly`; the configured `addopts` already supply quiet, parallel, fast-subset behavior. The new module must additionally be shown RED at the base commit and GREEN after E-02, because a guard never observed failing proves nothing. `aw sanitize --agent` must pass on the edited document, and `aw ipd lint --phase pre-transition` must report conforming.

## Spec / documentation sync

No `.spec.md` file is amended, so no spec path appears in `- Scope-Paths:` and no spec-edit announcement applies to this run. The edited file is a REFERENCE document whose normative source is `docs/cli-output-contract.md`; this plan moves the reference INTO agreement with that contract (F-07) rather than changing any contract, which is why the contract file is deliberately untouched. `CHANGELOG.md` is not edited: no user-facing behavior, flag, or output changes, and the repository's convention is that a documentation-accuracy correction with no behavior change does not earn a changelog entry. If a reviewer disagrees, the entry belongs under a documentation heading and would add `CHANGELOG.md` to `- Scope-Paths:`.

## Open questions

### OQ-01: Should the `--limit` bullet be written now, or deferred until backlog `4uw9gy` makes the flag uniformly honored?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: WRITE IT NOW, with an explicit reach caveat. Resolved at authoring from repository evidence, not deferred to a maintainer. The item raised this ("or it should be written after `wdazvp` resolves") because a bullet promising a bound the flag does not deliver would be a new false claim. Three measured facts settle it. FIRST (F-07), `docs/cli-output-contract.md` Section 6 ALREADY ships an unqualified three-hatch list naming `--limit` with no restriction, so the repository's own normative contract already makes the promise; leaving the reference at "Two" protects nobody from it and only keeps two shipped documents disagreeing about their own surface. SECOND (F-02), the flag IS honored, correctly and with full `total`/`emitted`/`omitted`/`next` accounting, on `aw runs query`, so a bullet documenting the bound is true of a real shipped surface rather than purely aspirational. THIRD (F-03), the inertness is tracked by `4uw9gy` with `Blocks-Release: next`, so the caveat has a durable referent an agent can consult for live state instead of trusting a sentence that rots. A caveated bullet is therefore strictly more accurate than both the present undercount and the contract's unqualified row. The residual risk is that `4uw9gy` lands first and makes the caveat stale, which E-01 handles by re-measuring at execution time and shrinking the caveat to match.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: Paste the per-verb probe output for all nine `--limit`-declaring leaves, each with and without the flag, taken at your base commit, and state for each whether the flag is HONORED, IGNORED, or carries a DIFFERENT meaning. Paste the base commit hash (`git rev-parse --short HEAD`). State explicitly whether your table matches the authoring measurement in F-02 or supersedes it, and if it supersedes it, name which leaves changed and confirm E-02's bullet was written from YOUR numbers. For `aw search`, show the probe used a pattern (F-06). For `aw runs analyze`, quote its help text and say whether the probe was conclusive (a one-record result with too few runs to page is INCONCLUSIVE, not IGNORED). For `aw rename` and `aw group`, state that the reach was established by reading the shared argument registration rather than by mutating a record, and quote the registered help string.
  - Observed evidence:
    Base commit hash (`git rev-parse --short HEAD`): `9af5f1030`.

    Per-verb probe measurements at base commit:

    1. `aw check`:
       Without `--limit`:
       ```
       $ aw check plans --agent
       {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"plans","findings":124,"evidence":["inventory","rules"],"diagnostics":[...124 items...],"next":"cite evidence it was discharged by finished work: add `- Carrier-Evidence: ...`"}
       ```
       With `--limit 1`:
       ```
       $ aw check plans --agent --limit 1
       {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":false,"target":"plans","findings":124,"evidence":["inventory","rules"],"diagnostics":[{"location":".aw/records/reviews/20261002-wdazvp-01-okiso1-make-aw-find-agent-emit-a-real-aw-agent-v1-record-stream-so.review.md","rule":"check.review-decision-unescalated"}],"next":"aw check plans --agent --limit 124","total":124,"emitted":1,"omitted":123}
       ```
       Classification: HONORED. Bounded `diagnostics` array payload with `total`, `emitted`, `omitted`, `complete: false`, and continuation `next`. (Delivered by executed plan `2zvxhx`).

    2. `aw search`:
       Pattern used: `"the"` (probe used pattern per F-06 to avoid exit 2 usage error).
       Without `--limit`:
       ```
       $ aw search plans "the" --agent
       {"schema":"aw.agent/v1","kind":"result","cmd":"search","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":4435,"evidence":["search-hits"],"next":"aw search plans the --agent","matches":[...4435 items...]}
       ```
       With `--limit 2`:
       ```
       $ aw search plans "the" --agent --limit 2
       {"schema":"aw.agent/v1","kind":"result","cmd":"search","outcome":"partial","exit":0,"verified":true,"complete":false,"findings":4435,"evidence":["search-hits"],"next":"aw search plans the --agent --limit 4435","matches":[{"path":".aw/records/plans/README.md","line":4,"text":"named `YYYYMMDD-HHMM-NN-<slug>.md` (the creating machine's local date and time; `NN` is a two-digit per-minute"},{"path":".aw/records/plans/README.md","line":12,"text":"- **`superseded/`** - replaced by a better/subsequent plan; kept for the record."}],"total":4435,"emitted":2,"omitted":4433}
       ```
       Classification: HONORED. Bounded `matches` array payload with `total`, `emitted`, `omitted`, `complete: false`, `outcome: partial`, and continuation `next`. (Delivered by executed plan `2zvxhx`).

    3. `aw find`:
       Without `--limit`:
       ```
       $ aw find plans --agent | wc -l
       1329
       ```
       With `--limit 3`:
       ```
       $ aw find plans --agent --limit 3 | wc -l
       1329
       ```
       Classification: IGNORED (stream bounding not honored; tracked by pending plan `okiso1` / backlog `wdazvp`).

    4. `aw runs query`:
       Without `--limit`:
       ```
       $ aw runs query findings --agent
       {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","context":{"findings_schema_version":1,"actionable":0,"cannot_determine":4}}
       {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","finding_id":"F-01",...}
       {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","finding_id":"F-02",...}
       {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","finding_id":"F-03",...}
       {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","finding_id":"F-04",...}
       {"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"clean","exit":0,"total":4,"emitted":4,"omitted":0,"complete":true}
       ```
       With `--limit 2`:
       ```
       $ aw runs query findings --agent --limit 2
       {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","context":{"findings_schema_version":1,"actionable":0,"cannot_determine":4}}
       {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","finding_id":"F-01",...}
       {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","finding_id":"F-02",...}
       {"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"partial","exit":0,"total":4,"emitted":2,"omitted":2,"complete":false,"next":"aw runs query findings --limit 4"}
       ```
       Classification: HONORED. Bounded stream item emission with terminating `summary` record carrying `total`, `emitted`, `omitted`, `complete: false`, and `next`.

    5. `aw runs analyze`:
       Help text:
       ```
       --limit LIMIT         Maximum records per agent stream page (bounded so a record stays inside its budget).
       ```
       Probe on lane with zero runs:
       Without `--limit`:
       ```
       $ aw runs analyze --list --agent
       {"schema":"aw.agent/v1","kind":"result","cmd":"runs analyze","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["report_files:0","snapshots:0","cached_runs:0"],"next":null}
       ```
       With `--limit 1`:
       ```
       $ aw runs analyze --list --agent --limit 1
       {"schema":"aw.agent/v1","kind":"result","cmd":"runs analyze","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["report_files:0","snapshots:0","cached_runs:0"],"next":null}
       ```
       Classification: INCONCLUSIVE. Probe in a zero-run lane produces one record either way; help text defines it as page size for agent stream page.

    6. `aw index`:
       Help text:
       ```
       --limit LIMIT     Max rows (index/find).
       ```
       Probe:
       ```
       $ aw index plans --agent --check
       {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"plans","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-missing"},{"location":"INDEX.md","rule":"check.stale-index-missing"}],"next":null}
       $ aw index plans --agent --check --limit 1
       {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"plans","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-missing"},{"location":"INDEX.md","rule":"check.stale-index-missing"}],"next":null}
       ```
       Classification: DIFFERENT MEANING. Configures recent-item hot-window size for `INDEX.md`.

    7. `aw research index`:
       Help text:
       ```
       --limit LIMIT     Hot-window size for INDEX.md (default 40).
       ```
       Classification: DIFFERENT MEANING. Configures recent-item hot-window size for research `INDEX.md`.

    8. `aw rename`:
       Registration: registered in `agent_workflows/cli.py:4344` in shared parser loop with `--limit, type=int, default=None, help="Max rows (index/find)."`.
       Classification: IGNORED. Mutating verb; reach established by argument registration in `cli.py` rather than mutating a record.

    9. `aw group`:
       Registration: registered in `agent_workflows/cli.py:4344` in shared parser loop with `--limit, type=int, default=None, help="Max rows (index/find)."`.
       Classification: IGNORED. Mutating verb; reach established by argument registration in `cli.py` rather than mutating a record.

    Comparison with F-02:
    This measurement SUPERSEDES the authoring measurement in F-02. In F-02, only `aw runs query` was honored. Between plan authoring and this execution, plan `2zvxhx` executed and closed backlog `4uw9gy`, making `--limit` HONORED on `aw check` and `aw search` under `--agent`. E-02's bullet was written from these numbers, reflecting `check` and `search` support while retaining the reach caveat for `find` and mutating verbs.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `git diff docs/cli-agent-protocol.md` in full. It must show the count word changed to `Three`, exactly one bullet added, that bullet naming `--limit` and sitting between the `--fields` and `--verbose` bullets, and NO other hunk in the file (in particular no change to `## Stream truncation is honest` or to any example record). Paste the rendered `## Token control` section as it now reads. Confirm the bullet's reach caveat matches V-01's measured table and cites `4uw9gy`. Paste `aw sanitize --agent` on the repository showing no `fail`, and paste a check for em and en dashes in the changed file showing zero hits (for example `python3 -c` over the file counting `\u2014` and `\u2013`, with the counts shown as 0).
  - Observed evidence:
    Full `git diff docs/cli-agent-protocol.md`:
    ```diff
    diff --git a/docs/cli-agent-protocol.md b/docs/cli-agent-protocol.md
    index 0efc562ef..d702161a6 100644
    --- a/docs/cli-agent-protocol.md
    +++ b/docs/cli-agent-protocol.md
    @@ -61,7 +61,7 @@ the full accounting so you never silently lose data:
     ## Token control

     The machine format is compact by default (short identifiers, counts instead of long lists).
    -Two escape hatches tune the token cost:
    +Three escape hatches tune the token cost:

     - `--fields <a,b,c>`: project each record down to the requested fields. The mandatory envelope
       (`schema`, `kind`, `cmd`, `exit`, `outcome`, `verified`, `complete`) is always retained. A projection
    @@ -72,6 +72,14 @@ Two escape hatches tune the token cost:
       leave a truncated record (`complete: false`) without the ready-to-run command needed to follow `next`
       and fetch the remainder. A projection never yields a record that fails validation, so `--fields` is safe
       to pass on any command.
    +- `--limit <N>`: bound payload emission to at most `N` items. For streaming commands (such as
    +  `runs query`), it bounds item emission with the terminating `summary` record carrying `total`,
    +  `emitted`, `omitted`, and a `next` continuation command (see `## Stream truncation is honest`
    +  above); for single-record commands (`check`, `search`), it bounds the in-record payload
    +  (`diagnostics`, `matches`) with the same counts and continuation. Reach is not yet uniform across
    +  every command accepting the flag (see backlog `4uw9gy`): `find` stream bounding is not yet honored,
    +  and mutating verbs (`group`, `rename`) ignore it. On index-building verbs (`index`, `research index`),
    +  it configures the recent-item hot-window size for `INDEX.md` rather than bounding output records.
     - `--verbose`: include full nested diagnostics, change details, and evidence dictionaries.

     ## Example records
    ```

    Rendered `## Token control` section as it now reads:
    ```markdown
    ## Token control

    The machine format is compact by default (short identifiers, counts instead of long lists).
    Three escape hatches tune the token cost:

    - `--fields <a,b,c>`: project each record down to the requested fields. The mandatory envelope
      (`schema`, `kind`, `cmd`, `exit`, `outcome`, `verified`, `complete`) is always retained. A projection
      additionally retains whatever the record kind requires to remain valid, including a summary's `total`,
      `emitted`, and `omitted` (so `emitted + omitted == total` remains verifiable to distinguish a bounded
      answer from a complete one) and a preview result's `applied`. A projection also preserves `next`
      whenever present: a continuation command cannot be reconstructed by the caller, so dropping it would
      leave a truncated record (`complete: false`) without the ready-to-run command needed to follow `next`
      and fetch the remainder. A projection never yields a record that fails validation, so `--fields` is safe
      to pass on any command.
    - `--limit <N>`: bound payload emission to at most `N` items. For streaming commands (such as
      `runs query`), it bounds item emission with the terminating `summary` record carrying `total`,
      `emitted`, `omitted`, and a `next` continuation command (see `## Stream truncation is honest`
      above); for single-record commands (`check`, `search`), it bounds the in-record payload
      (`diagnostics`, `matches`) with the same counts and continuation. Reach is not yet uniform across
      every command accepting the flag (see backlog `4uw9gy`): `find` stream bounding is not yet honored,
      and mutating verbs (`group`, `rename`) ignore it. On index-building verbs (`index`, `research index`),
      it configures the recent-item hot-window size for `INDEX.md` rather than bounding output records.
    - `--verbose`: include full nested diagnostics, change details, and evidence dictionaries.
    ```

    Confirmation of reach caveat:
    The bullet's reach caveat matches V-01's measured table (streaming bound on `runs query`, in-record payload bound on `check`/`search`, inert on `find`, mutating verbs `group`/`rename` ignore it, hot-window on index verbs) and cites backlog `4uw9gy`.

    `aw sanitize --agent` output:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    Unicode dash check:
    ```
    $ python3 -c 'text=open("docs/cli-agent-protocol.md").read(); print(f"em={text.count(chr(0x2014))}, en={text.count(chr(0x2013))}")'
    em=0, en=0
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the new module running RED at the base commit, before E-02's edit is applied, showing which assertions fail and that the `--limit`-enumeration test is among them; run it narrowed with `-o addopts=""` so the per-test counts are visible. Then paste it GREEN after E-02. Paste the full test file content, and confirm in prose that it reads ONLY the two Markdown documents and does not read `agent_workflows/cli.py` or any production module, does not use `inspect` or `ast` on source, and asserts a count-to-bullet RELATIONSHIP rather than frozen prose (the P16 requirement). Paste the bare `python3 -m pytest` summary line and every `FAILED` node id, for both your base commit and after the change, and compare the failing sets BY NODE ID: no node id may fail after that did not fail before, and none of the three new tests may appear among the failures. Do NOT require the passed-count delta to equal 3, since load-sensitive and live-corpus nodes move the count between runs (measured at review: 5 failures one run, 4 the next). Both runs must be YOUR OWN measurements, not any figure quoted in this plan. Finally paste `git diff --cached --name-only` before the commit showing ONLY the two declared `- Scope-Paths:` entries, and `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
    Narrowed RED run at base commit before E-02:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_cli_agent_protocol_doc.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2401120197
    rootdir: <repo-root>/.aw/worktrees/moegsl
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_protocol_and_contract_agree_on_token_control_hatches FAILED [ 33%]
    tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_token_control_enumerates_limit FAILED [ 66%]
    tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_token_control_count_word_agrees_with_bullet_count PASSED [100%]

    =================================== FAILURES ===================================
    _ CliAgentProtocolDocTests.test_protocol_and_contract_agree_on_token_control_hatches _
        self.assertEqual(
            proto_flags,
            contract_flags,
            f"Escape hatch sets disagree between protocol ({proto_flags}) "
            f"and contract ({contract_flags})",
        )
    E   AssertionError: Items in the second set but not the first:
    E   '--limit' : Escape hatch sets disagree between protocol ({'--verbose', '--fields'}) and contract ({'--limit', '--verbose', '--fields'})
    _________ CliAgentProtocolDocTests.test_token_control_enumerates_limit _________
        self.assertIn(
            "--limit",
            flags,
            f"docs/cli-agent-protocol.md ## Token control does not enumerate '--limit'. "
            f"Found flags: {flags}",
        )
    E   AssertionError: '--limit' not found in ['--fields', '--verbose'] : docs/cli-agent-protocol.md ## Token control does not enumerate '--limit'. Found flags: ['--fields', '--verbose']
    =========================== short test summary info ============================
    FAILED tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_protocol_and_contract_agree_on_token_control_hatches
    FAILED tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_token_control_enumerates_limit
    ========================= 2 failed, 1 passed in 0.12s ==========================
    ```

    Narrowed GREEN run after E-02:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_cli_agent_protocol_doc.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=1340076405
    rootdir: <repo-root>/.aw/worktrees/moegsl
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_protocol_and_contract_agree_on_token_control_hatches PASSED [ 33%]
    tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_token_control_enumerates_limit PASSED [ 66%]
    tests/test_cli_agent_protocol_doc.py::CliAgentProtocolDocTests::test_token_control_count_word_agrees_with_bullet_count PASSED [100%]

    ============================== 3 passed in 0.11s ===============================
    ```

    Full test file content (`tests/test_cli_agent_protocol_doc.py`):
    ```python
    """Behavioral guards for docs/cli-agent-protocol.md token control documentation (IPD moegsl).

    This test module verifies the token control escape hatch documentation across
    the agent protocol reference (`docs/cli-agent-protocol.md`) and the normative
    CLI output contract (`docs/cli-output-contract.md`).

    In accordance with GUIDING_PRINCIPLES P16 and AGENTS.md:
    1. This module tests the documentation artifacts under test directly, without
       inspecting production Python code, symbols, or ASTs.
    2. It asserts invariants and semantic relationships (e.g. stated count word
       matching actual top-level bullet count, and parity between reference and contract)
       rather than pinning frozen prose or literal paragraphs.
    """

    from __future__ import annotations

    import re
    import unittest
    from pathlib import Path

    REPO_ROOT = Path(__file__).resolve().parent.parent
    PROTOCOL_DOC_PATH = REPO_ROOT / "docs" / "cli-agent-protocol.md"
    CONTRACT_DOC_PATH = REPO_ROOT / "docs" / "cli-output-contract.md"

    _ENGLISH_NUMBER_WORDS = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }

    _FLAG_BULLET_RE = re.compile(r"^- (?:\*\*)?`(--[a-z-]+)")
    _COUNT_WORD_RE = re.compile(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+escape\s+hatches\b",
        re.IGNORECASE,
    )


    def _extract_token_control_section(markdown_text: str) -> str:
        """Extract lines in the Token Control section up to the next heading or thematic break."""
        lines: list[str] = []
        in_section = False
        for line in markdown_text.splitlines():
            if re.match(r"^#{1,3}\s+(?:\d+\.\s*)?Token [Cc]ontrol", line):
                in_section = True
                continue
            if in_section:
                if re.match(r"^(?:#{1,3}\s+|---)", line):
                    break
                lines.append(line)
        if not in_section:
            raise AssertionError("Could not locate 'Token Control' section heading in document")
        return "\n".join(lines)


    def _extract_hatch_flag_tokens(section_text: str) -> list[str]:
        r"""Extract backticked CLI flag tokens from top-level bullet items in a section.

        Matches top-level bullets starting with a backticked flag (e.g. `- \`--fields\``
        or `- **\`--fields\`**`), excluding non-hatch bullets such as `**Compact Defaults**`.
        Sub-bullets (indented with whitespace) are excluded so that secondary bullet
        breakdowns do not pollute top-level escape hatch enumeration.
        For composite bullets like `- **\`--verbose\` / \`--json\`**:`, this extracts the
        primary hatch flag token (`--verbose`), normalizing the composite entry.
        """
        flags: list[str] = []
        for line in section_text.splitlines():
            if not line.startswith("- "):
                continue
            m = _FLAG_BULLET_RE.match(line)
            if m:
                flags.append(m.group(1))
        return flags


    class CliAgentProtocolDocTests(unittest.TestCase):
        """Test token control escape hatch documentation accuracy and invariants."""

        def test_token_control_count_word_agrees_with_bullet_count(self) -> None:
            """The introductory count word in ## Token control must match its bullet count.

            Asserts the semantic relationship between the English number word in the
            introductory sentence ('Two escape hatches...', 'Three escape hatches...')
            and the number of top-level bullet items listed in that section.
            """
            self.assertTrue(
                PROTOCOL_DOC_PATH.is_file(),
                f"Missing protocol doc: {PROTOCOL_DOC_PATH}",
            )
            content = PROTOCOL_DOC_PATH.read_text(encoding="utf-8")
            section = _extract_token_control_section(content)

            m = _COUNT_WORD_RE.search(section)
            self.assertIsNotNone(
                m,
                "Could not find '<number> escape hatches' in ## Token control section",
            )
            word = m.group(1).lower()
            stated_count = _ENGLISH_NUMBER_WORDS.get(word)
            self.assertIsNotNone(
                stated_count,
                f"Unrecognized number word: {word!r}",
            )

            top_level_bullets = [
                line for line in section.splitlines() if line.startswith("- ")
            ]
            bullet_count = len(top_level_bullets)

            self.assertEqual(
                stated_count,
                bullet_count,
                f"Stated escape hatch count word ({word!r} -> {stated_count}) does not match "
                f"number of top-level bullets ({bullet_count}) in ## Token control",
            )

        def test_token_control_enumerates_limit(self) -> None:
            """## Token control in docs/cli-agent-protocol.md must enumerate --limit.

            Guards against regression of backlog item 9qya0k where --limit was omitted
            from the token control escape hatch list.
            """
            self.assertTrue(
                PROTOCOL_DOC_PATH.is_file(),
                f"Missing protocol doc: {PROTOCOL_DOC_PATH}",
            )
            content = PROTOCOL_DOC_PATH.read_text(encoding="utf-8")
            section = _extract_token_control_section(content)
            flags = _extract_hatch_flag_tokens(section)

            self.assertIn(
                "--limit",
                flags,
                f"docs/cli-agent-protocol.md ## Token control does not enumerate '--limit'. "
                f"Found flags: {flags}",
            )

        def test_protocol_and_contract_agree_on_token_control_hatches(self) -> None:
            """docs/cli-agent-protocol.md and docs/cli-output-contract.md must agree on hatches.

            The set of escape hatches enumerated in docs/cli-agent-protocol.md ## Token control
            must match the escape hatches enumerated in docs/cli-output-contract.md Section 6.
            Normalizes composite bullets such as '--verbose / --json' to the primary flag token.
            Non-hatch bullets (such as '**Compact Defaults**') are excluded.
            """
            self.assertTrue(
                PROTOCOL_DOC_PATH.is_file(),
                f"Missing protocol doc: {PROTOCOL_DOC_PATH}",
            )
            self.assertTrue(
                CONTRACT_DOC_PATH.is_file(),
                f"Missing contract doc: {CONTRACT_DOC_PATH}",
            )
            proto_content = PROTOCOL_DOC_PATH.read_text(encoding="utf-8")
            contract_content = CONTRACT_DOC_PATH.read_text(encoding="utf-8")

            proto_section = _extract_token_control_section(proto_content)
            contract_section = _extract_token_control_section(contract_content)

            proto_flags = set(_extract_hatch_flag_tokens(proto_section))
            contract_flags = set(_extract_hatch_flag_tokens(contract_section))

            self.assertEqual(
                proto_flags,
                contract_flags,
                f"Escape hatch sets disagree between protocol ({proto_flags}) "
                f"and contract ({contract_flags})",
            )


    if __name__ == "__main__":
        unittest.main()
    ```

    Prose confirmation:
    `tests/test_cli_agent_protocol_doc.py` reads ONLY the two documentation Markdown files (`docs/cli-agent-protocol.md` and `docs/cli-output-contract.md`). It does not import or read `agent_workflows/cli.py` or any other production module. It does not use `inspect` or `ast` to inspect source code. It asserts semantic relationships (count word matching top-level bullet count, and escape hatch set agreement between reference and contract) rather than frozen prose, adhering strictly to GUIDING_PRINCIPLES P16 and AGENTS.md test contracts.

    Full bare test suite comparison:
    - Base commit:
      `python3 -m pytest`
      Summary: `6359 passed, 2 skipped, 3 warnings in 386.21s (0:06:26)`
      Failing node IDs: none (empty set).
    - Post-change:
      `python3 -m pytest`
      Summary: `6362 passed, 2 skipped, 3 warnings in 192.36s (0:03:12)`
      Failing node IDs: none (empty set).
    - Node ID comparison: No node failed in either run. None of the three new tests failed. Passed count increased by exactly 3.

    `git diff --cached --name-only` before commit:
    ```
    docs/cli-agent-protocol.md
    tests/test_cli_agent_protocol_doc.py
    ```
    Shows ONLY the two declared `- Scope-Paths:` entries.

    `aw ipd lint --phase pre-transition` output:
    ```
    conforming: .aw/records/plans/pending/20261002-9qya0k-01-moegsl-correct-the-token-control-escape-hatch-count-in-docs-cli-age.ipd.md
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the two declared `- Scope-Paths:` and only through `aw commit <plan> -- <paths>`, never `git add -A`, never `git commit -a`, never `--no-verify`; do not push; do not create a tag or release. This is a SHARED CHECKOUT: before committing, run `git diff --cached --name-only` and unstage with `git restore --staged <path>` anything you did not modify for this task. The full suite must be run BARE and its actual output pasted, never summarized or claimed.

ORDER MATTERS. E-01 precedes E-02 because the bullet's factual claim must rest on a measurement taken at the commit that ships it, and E-03's module must be observed RED before E-02's edit is in place. E-03's module is authored before E-02 (it depends only on E-01) so its red run needs no revert; if E-02 was already applied, follow E-03's no-`git stash` instructions, and do not hold any revert across the full suite, since a restore after a multi-minute run can discard a co-worker's concurrent write.

SCOPE FENCE. The declared `- Scope-Paths:` are `docs/cli-agent-protocol.md` and `tests/test_cli_agent_protocol_doc.py`. That is a DECLARATION so finalize can reconcile edited against declared, not a stop condition: if the work genuinely requires a path outside it, make the edit and justify it at finalize with `--scope-reason`, acknowledging any declared-but-unmodified path with `--scope-ack`. Do not stop and report over a scope question. DO stop and report for a genuinely unsafe condition: an unresolvable concurrent edit to `docs/cli-agent-protocol.md`, or a base commit where `docs/cli-output-contract.md` Section 6 no longer lists three hatches (which would mean the reconciliation target moved and this plan's premise needs review). Sibling survey (re-checked at review): `t9lcdu` touches `docs/skill-selection.md` and the `docs_check`/`docs_render` modules, not either declared path; `okiso1` DOES declare `docs/cli-agent-protocol.md` (it reconciles the worked `find` example records, not `## Token control`, and its own deferred row hands the count fix to `9qya0k`); and `2zvxhx` edits `docs/cli-output-contract.md` Section 6, this plan's reconciliation target. Under `aw oc run` each runs in its own isolated worktree and integrates through the merge-and-revalidate gate, so the overlap is not a hazard; what it changes is the FACTS E-01 measures and the contract text E-02 mirrors, which E-01 and E-02 already require you to re-derive.

POST-GATE LIFECYCLE MOVE. On completion, every `E-*` must read `performed` and every `V-*` must read `pass` with concrete pasted evidence, `aw ipd lint --phase pre-transition` must report conforming, and only then does the plan move to `.aw/records/plans/executed/` through the tooled transition. Its OWNER is CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER performs `aw ipd begin`/`finalize` and the executor must NOT also run them (they refuse an agent in a managed lane with `AW-LIFECYCLE-ROLE-001`); executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll a `git mv` to `executed/` or hand-edit terminal state, and do not set backlog `9qya0k` `done` by hand. Backlog item `9qya0k` is set to `graduated` by this authoring, not `done`; it reaches `done` when this plan executes.
