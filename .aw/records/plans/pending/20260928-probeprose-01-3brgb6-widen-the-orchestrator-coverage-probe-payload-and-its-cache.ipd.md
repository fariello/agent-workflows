# IPD: Widen the orchestrator coverage probe payload and its cache key together to the prose sections a coverage question turns on

- Date: 2026-09-28
- Kind: child
- Concern: The orchestrator coverage probe's whole justification for spending a MODEL call is that the dangerous case is PROSE, and the payload it sends cannot see prose stated outside a checklist item. `runner_shared.probe_cache_payload` returns exactly two keys, `e_items` and `child_table_rows`, so a Goal, a `## Cross-IPD validation` bullet or a `## Required tests / validation` line saying "this orchestrator's E-02 runs the cross-IPD validation after all children land" is never sent, and the model is asked to judge coverage from evidence it was not given. Measured over the 66 `- Kind: orchestrator` plans in `.aw/records/plans/`: 35 of them carry at least one parent-only-work sentence, 49 sentences in total, in prose the probe cannot read. Spec `r07vma` Section 3a limit 1 names `## Completion criteria` and `## Cross-IPD validation` as exactly the places an obligation can still be written and assigns them to this probe, so the gap is a contract the probe does not currently meet.
  THE LIMIT WAS DELIBERATE AND ITS REASON IS STILL BINDING. `m7gvuz` E-03 requires the payload be EXACTLY the inputs `probe_cache_digest` keys on, because a payload the key does not cover means editing that thing serves a STALE verdict under apparent authority, which is the one way the cache can be actively wrong rather than merely useless. Widening the payload alone breaks that identity; widening BOTH changes a shipped cache's key shape, which is `8tgg6g`'s artifact and was outside `m7gvuz`'s `Scope-Paths`. So the narrow-but-honest behavior was chosen and the gap filed. This plan is the change that was deferred: it widens payload and key TOGETHER, in one function, so the identity holds by construction.
  THE NAMED PIN NO LONGER EXISTS, which changes what "closing this" costs. Backlog `rmcqw8` says the limit is pinned by `tests/test_orchestrator_probe.py::TheExcerptHasAKnownLIMIT`, whose failure message names the required simultaneous change. Both `tests/test_orchestrator_probe.py` (3022 lines) and `tests/test_orchestrator_probe_cache.py` (1615 lines) were DELETED on 2026-09-24 by commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"). So the guard rail this work was supposed to trip is gone, nothing in the surviving suite pins the payload's key set, and the five `xmqv5l` no-op invariants the backlog item asks to re-prove have no home to be re-proven in. Re-establishing them behaviorally is therefore part of this change and not a bonus.
- Scope: Widen `probe_cache_payload` to carry an EVIDENCE-CHOSEN, allowlisted set of the orchestrator's unattached prose sections, so `probe_cache_digest` and `orchestrator_probe_excerpt` both widen with it from the one function they already share; re-establish the five `xmqv5l` no-op invariants plus the new move-on-hazard invariants in a behavioral test module, since the suite that held them was deleted; accept the one-time cache invalidation with its measured cost; and amend the two spec sentences and the one managed-`AGENTS.md` sentence that state the old key, so no contract describes a key that no longer exists.
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/runner_shared.py, agent_workflows/engine.py, AGENTS.md, tests/test_orchestrator_probe_payload.py, tests/test_orchestrator_shape_gate.py, tests/test_orchestrator_shape_composed.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: rmcqw8
- Set: probeprose
- Order: 1
- Highest E allocated: 07
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: 3brgb6

## Workflow history

- 2026-09-28 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): authored from backlog `rmcqw8`. Every measurement below was taken in lane `rmcqw8` against this worktree at the lane's HEAD; the corpus figures are re-derivable with the commands each V-item names.
  TWO THINGS A REVIEWER SHOULD ATTACK FIRST. (1) THE SECTION ALLOWLIST IS A JUDGEMENT, and it is the only part of this plan that is not mechanical: F-04 gives the size, hazard-density and churn numbers per candidate section and F-05 gives the four exclusions with their reasons, so dispute the choice against those numbers rather than against the idea. (2) THE BACKLOG ITEM'S NAMED PIN IS GONE (F-02), so the "re-prove the five invariants in `tests/test_orchestrator_probe_cache.py`" instruction cannot be followed literally; E-04 re-establishes them in a new module instead, and a reviewer should check that substitution is faithful rather than convenient.
- 2026-09-28 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Let the orchestrator coverage probe read the prose its own justification rests on, without letting the cache serve a stale verdict. One function, `probe_cache_payload`, gains an allowlisted `prose_sections` key; the digest and the prompt excerpt both widen from it automatically, because both already read that one function. The allowlist is chosen from measured hazard density rather than taste, the five `xmqv5l` no-op invariants are re-proven in a test module that survives, and the one-time cache invalidation is accepted with its cost measured at ONE extra re-probe across the entire historical corpus.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one extractor, one payload, one key

- [ ] E-01 Add a public UNATTACHED-SECTION-PROSE extractor to `ipd_lint` (suggested name `unattached_section_prose(text) -> dict[str, str]`, sited beside `parse`, which already owns what a leaf IS), returning each `## ` section's prose that belongs to no checklist item.
  IT MUST BE DISJOINT FROM `runner_shared.e_item_action_blocks` BY CONSTRUCTION, NOT BY COINCIDENCE, because the two payload keys must not double-send the same bytes. The construction that achieves it: walk `ipd_lint._structural_lines` (so a fenced or block-quoted line is not mistaken for prose, the same view `check_engine._deferred_section_obligations` already walks), key on `_H2_RE`, and SKIP four line classes - any line matching `_H3_RE`, any line matching `_LEAF_RE` (a leaf's own opening line), any line matching `_SUBFIELD_RE`, and ANY INDENTED LINE. The last one is what makes disjointness structural: `e_item_action_blocks` captures a leaf's opening line plus its INDENTED continuation lines and nothing else, so excluding every indented line leaves exactly the complement. Pre-verified in this lane: across all 66 orchestrators, ZERO extracted prose lines longer than 40 characters also appear inside any `e_items` block.
  `ipd_lint` AND NOT `runner_shared`, for the reason pending plan `qurgra` (`- Set: 168p5j`) records for its sibling helper: `ipd_lint` already owns `_structural_lines`, `_H2_RE`, `_H3_RE`, `_LEAF_RE` and `_SUBFIELD_RE`, and `runner_shared` reaches `ipd_lint` function-locally already (`e_item_action_blocks` does exactly that). Putting the rule where its primitives live keeps one definition of document structure.
  - Depends on: none
  - Expected outcome: `ipd_lint.unattached_section_prose` exists, returns a section-title-keyed mapping over the structural view, and its output shares no line with `runner_shared.e_item_action_blocks` on any orchestrator in the corpus.
  - Execution state: pending

- [ ] E-02 Widen `runner_shared.probe_cache_payload` to a THIRD key, `prose_sections`, holding the extractor's output filtered to a module-level ALLOWLIST constant (suggested name `PROBE_PROSE_SECTIONS`), and leave `probe_cache_digest` untouched so the key moves automatically because it hashes the payload.
  THE ALLOWLIST IS SEVEN SECTIONS, CHOSEN ON THE F-04 MEASUREMENTS AND ON SPEC TEXT, not on judgement alone: `Goal`, `Detailed Implementation Checklist (TODO)`, `Required tests / validation`, `Cross-IPD validation`, `Completion criteria (the whole Set is done only when)`, `Validation and cross-check (verify before reporting the Set complete)`, `Scope check`. The last two of those five middle ones are REQUIRED rather than chosen: spec `r07vma` Section 3a limit 1 names `## Completion criteria` and `## Cross-IPD validation` as places an obligation can still be written and assigns them to this probe, so excluding them would leave the probe not meeting a contract that already exists.
  SPELL THE SECTION TITLES THROUGH `ipd_schema`'s `H_*` CONSTANTS (`H_GOAL`, `H_EXECUTION`, `H_REQUIRED_TESTS`, `H_CROSS_IPD`, `H_COMPLETION`, `H_VALIDATION_ORCH`, `H_SCOPE_CHECK`), never as literal strings, because `ipd_schema` is the one definition of a heading and a literal copy silently stops matching when a heading is reworded.
  DETERMINISM, to the same standard the existing two keys meet: the mapping is serialized by `json.dumps(..., sort_keys=True)` already, so no extra sorting is needed; keep the value as the raw prose string per section and do not normalize whitespace, since a normalization step is a second rule nothing else shares.
  - Depends on: E-01
  - Expected outcome: `probe_cache_payload(text)` returns exactly `{"e_items", "child_table_rows", "prose_sections"}`; `probe_cache_digest` MOVES for an orchestrator whose allowlisted prose changes and does NOT move for one whose non-allowlisted prose changes; no literal heading string is introduced in `runner_shared`.
  - Execution state: pending

- [ ] E-03 Render the new key in `orchestrator_probe_excerpt` and tell the model what it is now reading, so the excerpt and the key stay the same two-then-three inputs BY CONSTRUCTION.
  THE RENDERER MUST BECOME KEY-COMPLETE, not merely extended: today it hand-reads `payload.get("e_items")` and `payload.get("child_table_rows")`, so a future fourth key would be hashed and never sent, which is the silent divergence `m7gvuz` E-03 exists to prevent. Render every key the payload returns (a per-key section with a stable heading, in sorted key order) so an unrendered key becomes impossible rather than merely unlikely, and add the assertion in E-04 that proves it.
  UPDATE THE PROMPT'S CLOSING SENTENCE, which currently states the excerpt "is its checklist item action text plus its child table, which is everything the question depends on". That sentence becomes false. Replace it with one naming the three parts, and keep the change to that sentence: the prompt's instruction body already tells the model that prose counts ("a sentence like 'the database must be migrated before the children run' is work no child covers"), and this is the first version where that instruction is actually satisfiable.
  THE PROMPT IS NOT PART OF THE DIGEST AND MUST NOT BECOME PART OF IT. A prompt reword is not a reason to re-probe; the digest covers the PAYLOAD, and `render_probe_prompt` takes the rendered excerpt as an argument. Do not fold the template into `probe_cache_payload` to "make them consistent".
  - Depends on: E-02
  - Expected outcome: the excerpt contains a section per payload key including the new prose, the prompt's closing sentence names three parts, and `render_probe_prompt`'s relationship to the digest is unchanged.
  - Execution state: pending

### Task group 2: prove the invariants the deleted suite used to hold

- [ ] E-04 Create `tests/test_orchestrator_probe_payload.py` and pin the widened contract BEHAVIORALLY, over the live orchestrator corpus rather than over one fixture, because the properties at issue are properties of real plans.
  TEN PINS, in three groups. GROUP A, the five `xmqv5l` NO-OP INVARIANTS the backlog item names, each applied to every orchestrator that the edit applies to and each asserting the digest is UNCHANGED: (a1) ticking every `- [ ] E-NN`/`V-NN` to `[x]`; (a2) filling an empty `- Observed evidence:`; (a3) appending a `## Workflow history` line; (a4) `- Execution state: pending` to `performed`; (a5) `- Result: pending` to `pass`. Plus (a6), the composite: ALL FIVE at once, which is what a conforming self-execution actually does. GROUP B, the new SENSITIVITY: (b1) a hazard sentence inserted into an ALLOWLISTED section MOVES the digest on every orchestrator; (b2) a prose edit in a NON-allowlisted section (`Open questions`, `Deferred / out of scope`) moves it on NONE. GROUP C, the IDENTITY that makes the widening safe: (c1) `set(probe_cache_payload(t))` equals the expected three keys AND every one of those keys is represented in `orchestrator_probe_excerpt(t)`, so a key can never be hashed without being sent; (c2) the disjointness of E-01, asserted as zero shared lines over the corpus.
  PRE-VERIFIED IN THIS LANE, so these are pins on measured behavior and not hopes: with the seven-section allowlist, A1-A6 move 0 of 26/26/66/26/26/66 applicable orchestrators, B1 moves 66 of 66 (both for a `Cross-IPD validation` insertion and a `Goal` insertion), B2 moves 0 of 66 for both excluded sections, and C2 finds 0 shared lines.
  MARK THE CORPUS-READING TESTS APPROPRIATELY. `pyproject.toml` `addopts` already excludes `-m 'not slow and not livecorpus'`, and a test that walks all 66 orchestrators is exactly what `livecorpus` is for; put the corpus-wide sweeps behind it and keep at least one synthetic-fixture version of A6, B1 and C1 in the DEFAULT suite, so a bare `python3 -m pytest` still fails if the contract breaks.
  - Depends on: E-03
  - Expected outcome: the new module exists; run bare it passes; run with `-m livecorpus` the corpus sweeps pass; and reverting E-02 makes group B fail.
  - Execution state: pending

- [ ] E-05 Record the ONE-TIME CACHE INVALIDATION and the ALLOWLIST RATIONALE in the code that implements them, with the numbers, so the next reader can dispute the choice instead of re-deriving it.
  THE INVALIDATION IS ACCEPTED, NOT VERSIONED, and the cost is measured rather than assumed. Widening the payload changes every key at once, so all 26 entries in `.aw/state/runtime/orchestrator-probe-verdicts.json` stop matching; 9 of those 26 currently key a live orchestrator's text and 0 would after the change. The real cost is bounded by what a run can QUEUE, and there are ZERO `- Kind: orchestrator` plans in `.aw/records/plans/pending/` today, so the immediate cost is zero model calls. A miss is `unknown`, which PROBES (`probe_orchestrator` asks on a miss) and blocks only if the answer blocks, so the invalidation clears nothing and can only cost re-probes. Do NOT add a `digest_version` field or a dual-digest fallback: serving an old verdict under the old narrow key is precisely the stale-verdict-under-apparent-authority failure this widening exists to close.
  THE STANDING COST IS ALSO MEASURED AND IS SMALL. Over the 61 executed orchestrators that have an `approved` revision in git history, comparing that revision to the final one: the shipped narrow digest moved on 2, the widened digest moves on 3. ONE extra re-probe across the entire historical corpus. State that number, because the obvious objection to widening a cache key is that it will thrash, and it does not.
  AND RECORD THE PAYLOAD-SIZE PRICE HONESTLY, since it is the real cost: median excerpt 2,217 -> 6,560 characters (roughly 554 -> 1,640 tokens at 4 characters per token), largest 10,423 -> 19,072 (roughly 2,606 -> 4,768), total corpus 162,373 -> 479,968 (+195.6%). That is a tripling of a per-orchestrator prompt that is asked once per run per orchestrator and cached thereafter.
  - Depends on: E-02
  - Expected outcome: `probe_cache_payload` and `probe_cache_digest` docstrings state what the third key is, why each allowlisted section is in and each excluded one is out, the accepted invalidation with its 26/9/0 and 61/2/3 numbers, and the refused versioned-digest alternative.
  - Execution state: pending

### Task group 3: make every contract describe the key that now exists

- [ ] E-06 Amend the two spec sentences that state the old key, declaring both files in `Scope-Paths` (done) and recording each amendment with `aw specs note` rather than a bare edit.
  SPEC `25kzda` SECTION 2.5b IS DIRECTLY FALSIFIED by this change: "The verdict is CACHED against a digest of only what the answer depends on (the orchestrator's checklist item action text and its child table's row cells)". Amend the parenthetical to name the three inputs and keep the following sentence ("Ticking a checkbox, filling evidence, or appending workflow history MUST NOT re-probe") EXACTLY as it stands, because it is still true and E-04's group A is its proof.
  SPEC `r07vma` SECTION 3a LIMIT 1 IS NOT FALSIFIED AND MUST NOT BE REWRITTEN. It says the shape check does not parse continuation lines, `## Completion criteria` or `## Cross-IPD validation`, and that "that residue is the semantic probe's job". This change makes that sentence TRUE where it was previously aspirational, so the amendment is an added note recording that the probe now actually reads those two sections, not an edit to the limit.
  DO NOT TOUCH `77tr3o` R-12. It delegates the mechanism, the caching and the override to `25kzda` 2.5b by reference and states no key of its own, so amending it would create a second description of one rule.
  - Depends on: E-02
  - Expected outcome: `25kzda` 2.5b names the three digest inputs; `r07vma` carries a dated note pointing at this plan; `77tr3o` is unmodified; both amended specs carry an `aw specs note` history record.
  - Execution state: pending

- [ ] E-07 Amend the ALWAYS-LOADED sentence in the managed `AGENTS.md` block and regenerate the file, because it currently tells every agent in every managed repo the old key.
  THE SENTENCE IS "The verdict is CACHED on the parent's item text plus its child table, so an unmodified orchestrator is never re-probed while the real fix re-probes automatically and a ticked checkbox does not." It lives in `agent_workflows/engine.py`, inside the `pointer` section rendered by `engine.agents_managed_sections`, and is NOT hand-editable in `AGENTS.md`: `AGENTS.md` is generated, so editing it alone is undone by the next install.
  THE PROCEDURE, and the verification that it actually landed: edit the constant in `engine.py`, re-run `aw install .`, then confirm `git diff -- AGENTS.md` shows ONLY that sentence changing and that the rendered body matches the file. The renderer is layout-sensitive - measured in this lane, `agents_managed_sections(target_layout="aw")`'s `pointer` body is present verbatim in `AGENTS.md` while the `legacy` and `modern` renderings are not - so verify against the `aw` layout and do not conclude from a `legacy` mismatch that the install failed. `tests/test_installer.py`'s idempotent-rerun guard is the standing regression check.
  KEEP THE AMENDED SENTENCE AT ITS CURRENT LENGTH OR SHORTER. This block is loaded into every agent turn in every managed repo, so a sentence that grows to enumerate seven section titles costs tokens on every turn forever; say "plus the prose sections a coverage question turns on" and let the code hold the list.
  - Depends on: E-06
  - Expected outcome: `engine.py`'s sentence names the widened key, `aw install .` regenerates `AGENTS.md` with that one sentence changed, and the rendered `aw`-layout body matches the file.
  - Execution state: pending

## Project conventions discovered (Step 0)

- PAYLOAD AND KEY IDENTITY IS THE INVARIANT THIS WHOLE AREA IS BUILT AROUND, stated in `probe_cache_payload`'s own docstring ("if the probe reads something the key does not cover, editing that thing serves a stale verdict") and again in `orchestrator_probe_excerpt` ("RENDERED FROM `probe_cache_payload`, WHICH IS THE POINT"). Both functions already read the one payload builder, so this plan widens that builder and changes no second place.
- THE EXCLUSION OF EXECUTION STATE IS STRUCTURAL, NOT TEXTUAL. `ipd_lint.parse` puts a leaf's checkbox in `Leaf.checked` and its indented `- Key: value` lines in `Leaf.fields`, which is why ticking a box or filling evidence cannot move the digest. The new extractor must inherit that discipline by skipping `_SUBFIELD_RE` and every indented line rather than by pattern-matching state words.
- A CORPUS-WIDE TEST BELONGS BEHIND A MARKER. `pyproject.toml` sets `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, so a sweep over every orchestrator must be marked `livecorpus` and mirrored by a synthetic case in the default suite; and the suite is run BARE per the execution contract (no `-n0`, no extra `-q`).
- `AGENTS.md` IS GENERATED FROM `engine.py`. Editing the file directly is reverted by the next `aw install .`, and the renderer takes a `target_layout` whose `aw` value is the one this repository matches.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The gap reproduces exactly as filed, and the payload's key set is the whole of it. | `probe_cache_payload` returns `['child_table_rows', 'e_items']` for every orchestrator, measured on `m7gvuz`'s own plan file. `orchestrator_probe_excerpt` renders those two keys and nothing else, under the literal headings `### Checklist item action text` and `### Child IPDs table (row cells, in document order)`. |
| F-02 | THE PIN THE BACKLOG ITEM RELIES ON NO LONGER EXISTS, and neither does the module it says to re-prove the invariants in. | `tests/test_orchestrator_probe.py` and `tests/test_orchestrator_probe_cache.py` are both absent at HEAD. `git log --diff-filter=D` names commit `19313eed`, 2026-09-24, "test: trim test suite from 9,136 to under 2,000 tests", deleting 3022 and 1615 lines respectively. `TheExcerptHasAKnownLIMIT` and its "if this now PASSES, the payload was widened" failure message exist only in `19313eed^`. Grep for `probe_cache_payload`/`probe_cache_digest`/`e_item_action_blocks` across `tests/` returns ZERO hits, so no surviving test pins the payload's key set at all. |
| F-03 | The scale of the blind spot, measured over the whole live corpus rather than the ten-plan sample the backlog item cites. | 66 plans carrying `- Kind: orchestrator` under `.aw/records/plans/`, by directory: 63 `executed/`, 3 `superseded/`, 0 `pending/`, 0 `not-executed/`, 0 `reusable/`. With a parent-only-work sentence pattern (`this orchestrator/parent/plan ... must|carries|performs|produces|runs|establishes|records|verifies|authors|reconciles|closes`, `before any child`, `after the/every/all child(ren)`), 35 of 66 orchestrators carry at least one such sentence in prose the current payload cannot see, 49 sentences in total. |
| F-04 | The allowlist is chosen on measurement. Per candidate section, taken with the E-01 extractor: prose size as a percentage of the current total excerpt, hazard sentences found, and execution-time churn (how many of 61 approved-to-final orchestrator lifecycles changed that section's prose). | `Detailed Implementation Checklist (TODO)` unattached prose: 16.4%, 17 hits, 0/61 churn. `Required tests / validation`: 30.7%, 16, 0/61. `Scope check`: 18.9%, 11, 1/61. `Cross-IPD validation`: 51.6%, 4, 1/61. `Completion criteria`: 50.1%, 1, 1/61. `Goal`: 21.9%, 0, 0/61. `Validation and cross-check`: 5.9%, 0, 0/61. The four highest-density sections are all in; `Cross-IPD validation` and `Completion criteria` are in on spec grounds (`r07vma` 3a.1) despite low density; `Goal` and `Validation and cross-check` are in as cheap context that frames the question the model is answering. |
| F-05 | The four biggest sections are EXCLUDED, and each exclusion has a reason that is not "it is big". Same extractor, same denominators as F-04. | `Workflow history` (132.7% of the current excerpt, 61/61 churn) is excluded because including it would re-probe on every appended history line, which is the exact `xmqv5l` defect the digest was built to avoid. `Child IPDs, sequence, and dependencies` prose (90.5%, lowest density at 0.03 hits per kilochar) is excluded because the table's ROW CELLS are already a payload key and the surrounding paragraphs are explanation of the table, which `probe_cache_digest`'s docstring already states are not the table. `Approval and execution gate` (87.9%, 0.39 hits per kilochar) is excluded because its 55 apparent hits are template boilerplate ("This ORCHESTRATOR and each child MUST ...") spread across 34 plans, so it would add the largest remaining section in exchange for near-zero distinguishing signal and would push the probe toward the false positives that are its dominant cost. `Open questions` (49.7%, 3 hits in 3 files, 2/61 churn) is excluded because a question is by definition not an obligation and it churns as questions resolve. |
| F-06 | The widening does not re-open `xmqv5l`, measured against the real corpus and not a fixture. | With the seven-section allowlist, the widened digest is UNCHANGED by: a checkbox tick (0 of 26 applicable), a filled `Observed evidence` (0/26), an appended `## Workflow history` line (0/66), `Execution state: performed` (0/26), `Result: pass` (0/26), and ALL FIVE applied together as a conforming self-execution would (0/66). The shipped narrow digest is likewise unchanged by all six, so the property is preserved rather than newly claimed. |
| F-07 | The widening is SENSITIVE in exactly the intended direction. | A hazard sentence inserted into `## Cross-IPD validation` moves the widened digest on 66 of 66 orchestrators and the shipped digest on 0 of 66; the same insertion into `## Goal` likewise 66 and 0. A prose edit in `## Open questions` or `## Deferred / out of scope` moves the widened digest on 0 of 66, so the exclusions are real and not incidental. |
| F-08 | The new extractor is DISJOINT from the existing E-item extractor by construction. | Over all 66 orchestrators, zero extracted prose lines longer than 40 characters also appear inside any `e_items` action block. The reason is structural: `e_item_action_blocks` reads a leaf's opening line plus its INDENTED continuation lines only, and the extractor skips every indented line, every `_LEAF_RE` line, every `_SUBFIELD_RE` line and every `### ` heading. |
| F-09 | The cache-invalidation cost is small and is bounded by what a run can queue. | `.aw/state/runtime/orchestrator-probe-verdicts.json` holds 26 entries (15 `pass`, 11 `fail`, recorded 2026-09-19 through 2026-09-26). 9 of the 26 still key a current orchestrator's text; 0 would after the widening. But `queued_orchestrator_targets` is scoped to the run's QUEUE, and there are ZERO `- Kind: orchestrator` plans in `.aw/records/plans/pending/`, so the immediate cost is zero model calls. A miss reads `unknown` and PROBES, so nothing is cleared by the invalidation. |
| F-10 | The STANDING re-probe cost is one extra probe across the whole history, which answers the obvious "this will thrash the cache" objection. | Over the 61 executed orchestrators that have an `approved` revision in git history, comparing that revision to their final one: the shipped digest moved on 2 (`jwbo2u`, `pp6y76`), the widened digest moves on 3 (those two plus `wfjsp4`). One additional re-probe, historically. |
| F-11 | The payload-size price is a roughly threefold increase, stated because it is the real cost of this change. | Current excerpt: median 2,217 characters, max 10,423, corpus total 162,373. Widened: median 6,560, max 19,072, total 479,968 (+195.6%). At four characters per token that is roughly 554 -> 1,640 tokens median and 2,606 -> 4,768 at the worst plan, for one cached yes/no question per orchestrator per run. |
| F-12 | Two surviving tests assert on the excerpt and both should keep passing, but they are declared because a widening is exactly the change that would break them. | `tests/test_orchestrator_shape_composed.py::TestProbeSurvivedAndStillBlocks` asserts a continuation line IS in the excerpt and a `- Context:` sub-field is NOT; `tests/test_orchestrator_shape_gate.py` asserts "Establish the characterization baseline" IS in the excerpt. Both are satisfied by a widened excerpt, since widening only adds and the sub-field stays excluded. Measured at HEAD: `python3 -m pytest tests/test_orchestrator_shape_gate.py tests/test_orchestrator_shape_composed.py -o addopts="" -q` -> `20 passed`. |
| F-13 | Three contracts state the narrow key in prose, and one of them is loaded into every agent turn. | Spec `25kzda` 2.5b: "CACHED against a digest of only what the answer depends on (the orchestrator's checklist item action text and its child table's row cells)". `agent_workflows/engine.py`, in the managed `pointer` section: "The verdict is CACHED on the parent's item text plus its child table". The same sentence appears in this repository's generated `AGENTS.md`. Spec `77tr3o` R-12 states no key, delegating to `25kzda` 2.5b, so it needs no edit. |

## Proposed changes (ordered, validatable)

1. `ipd_lint`: add `unattached_section_prose(text)`, walking the structural view and excluding headings, leaf opening lines, sub-fields and every indented line (E-01).
2. `runner_shared`: add the `PROBE_PROSE_SECTIONS` allowlist, spelled through `ipd_schema`'s `H_*` constants, and a third `prose_sections` payload key; the digest moves with it automatically (E-02).
3. `runner_shared`: make `orchestrator_probe_excerpt` render EVERY payload key, and correct the prompt's closing sentence about what the excerpt is (E-03).
4. `tests/test_orchestrator_probe_payload.py`: ten behavioral pins - six no-op invariants, two sensitivity cases, two identity properties - with corpus sweeps behind `livecorpus` and synthetic mirrors in the default suite (E-04).
5. `runner_shared` docstrings: the allowlist rationale, the accepted one-time invalidation with its numbers, and the refused versioned-digest alternative (E-05).
6. Specs `25kzda` 2.5b (amend the key) and `r07vma` (dated note that the probe now reads the two sections 3a.1 assigns it), each recorded with `aw specs note` (E-06).
7. `engine.py` managed-block sentence plus the regenerated `AGENTS.md` (E-07).

## Deferred / out of scope (with reason)

- FRONT-MATTER `- Concern:` AND `- Scope:` ARE NOT INCLUDED IN THE PAYLOAD, though they measurably carry some signal (7 hazard sentences between them, 53.6% of the current excerpt in size). They are a different extraction surface (`doc.meta_fields`, not section prose), so including them would add a second mechanism to a change whose whole point is that one function holds the payload. If a reviewer wants them, they are a one-line addition to the same payload builder and should be argued on F-04's numbers.
  - Carrier-Declined: Deliberately refused for this change rather than handed off. Adding a second extraction surface to the payload builder is the kind of scope creep that makes the identity invariant harder to prove, and the door is left open by construction (the payload is one function, so a later plan adds one key). No carrier is needed for a refusal.
- WIDENING `ipd_lifecycle.frozen_region_digest` IS NOT PART OF THIS PLAN. That digest is the begin-receipt validity key and deliberately excludes prose sections; pending plan `qurgra` (`- Set: 168p5j`, `- From-Backlog: 168p5j`) owns its adjacent first-line-only defect. Bundling the two would put one change across two safety gates with different invariants.
  - Carrier: 168p5j
- THE PROBE'S FALSE-POSITIVE RATE IS NOT MEASURED HERE. Sending three times the prose necessarily changes how often the model answers `CONTAINS EXECUTIONS`, and this plan cannot measure that without spending model calls on the live corpus. The direction of the risk is stated rather than hidden: the gate's prompt already resolves doubt to `CONTAINS EXECUTIONS`, and `25kzda` 2.5b's remedy for a positive finding is to ADD A CHILD, so an over-fire costs an authoring round trip and not lost work.
  - Carrier-Declined: A model-cost measurement is a separate empirical exercise requiring live probe runs over the corpus, and it gates nothing this plan claims. The plan states the risk direction and the bounded remedy instead of asserting a number it did not measure.
- NO CHANGE TO THE FOUR-STATE ANSWER, THE STALENESS RULE, THE MODEL GUARD, OR THE OVERRIDE. `classify_probe_reply`, `read_probe_verdict`, `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS` and `--allow-uncovered-orchestrator-work` are untouched; this plan changes WHAT is asked about, not how an answer is judged.
  - Carrier-Declined: An explicit fence rather than an obligation. Nothing is owed because nothing is deferred.
- BACKFILLING OR RE-PROBING THE 26 EXISTING STORE ENTRIES is out of scope. The store is machine-local and gitignored, a stale entry simply stops matching, and rewriting recorded LLM verdicts by hand would be a hand-edit of evidence the execution contract forbids.
  - Carrier-Declined: The invalidation is self-healing by design (a miss probes), so there is no residual work to carry.

## Scope check

- Over-scope: none. `agent_workflows/engine.py` and `AGENTS.md` are declared because F-13's sentence is generated from the former into the latter and editing only one of them either leaves the contract false or is reverted by the next install. The two spec files are declared because `25kzda` 2.5b is directly falsified by this change and `r07vma` 3a.1 assigns this probe the two sections the change finally lets it read; the repository contract requires a declared spec edit rather than a silent one. `tests/test_orchestrator_shape_gate.py` and `tests/test_orchestrator_shape_composed.py` are declared defensively per F-12: both assert on excerpt contents and both should keep passing unmodified, so a declared-but-unmodified reconciliation is the expected outcome.
- Under-scope: none known. `agent_workflows/ipd_lint.py` gains the extractor, `agent_workflows/runner_shared.py` gains the allowlist plus the payload key plus the renderer and prompt change plus the recorded rationale, `tests/test_orchestrator_probe_payload.py` holds the pins, and the four contract files are amended. Specifically NOT needed: `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, because both reach the gate through `runner_shared.enforce_orchestrator_probe_gate` and neither constructs a payload; and `agent_workflows/ipd_lifecycle.py`, because `frozen_region_digest` is a different key and is explicitly deferred. If the executor finds either claim false, that is a finding to report rather than a silent widening.

## Required tests / validation

- `python3 -m pytest` run BARE, per the execution contract: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Paste the actual summary line. Take a BASELINE before any edit and compare failing NODE IDS, not totals.
- `python3 -m pytest tests/test_orchestrator_probe_payload.py -m livecorpus -o addopts=""` for the corpus sweeps, whose output must include the applicable-orchestrator counts rather than only a pass count.
- `python3 -m pytest tests/test_orchestrator_shape_gate.py tests/test_orchestrator_shape_composed.py -o addopts="" -q`, whose measured baseline at HEAD is `20 passed` (F-12), to prove the two surviving excerpt assertions still hold.
- A REVERT-PROOF for the sensitivity pins: run group B against the pre-change `probe_cache_payload` and show it FAILS there, so the pins are regression tests and not tautologies.
- `aw ipd lint --phase pre-transition` on this plan, plus `aw check` for the consistency and release-gate rule families (this plan carries `From-Backlog: rmcqw8` and inherits no `Blocks-Release`, and `aw check` is what proves the second half of that claim).
- `git diff -- AGENTS.md` after `aw install .`, showing exactly one sentence changed.
- `aw sanitize --agent` before treating anything as shareable, since the E-05 evidence quotes machine-local store contents.

## Spec / documentation sync

`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 2.5b MUST be amended, and the reason is that it states the cache key this plan changes: "The verdict is CACHED against a digest of only what the answer depends on (the orchestrator's checklist item action text and its child table's row cells), so an unmodified orchestrator is never re-probed and a genuine fix re-probes automatically." After this change the parenthetical is false. The amendment names the three inputs and leaves the following sentence ("Ticking a checkbox, filling evidence, or appending workflow history MUST NOT re-probe") untouched, because E-04's group A is its proof and weakening it would discard the `xmqv5l` guarantee.

`.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md` gains a dated `aw specs note` rather than an edit to its requirements. Its Section 3a limit 1 says the shape check "deliberately does not parse the continuation lines, the `## Completion criteria` section, or the `## Cross-IPD validation` section, and an obligation can still be written there. That residue is the semantic probe's job." That sentence stays exactly as written; the note records that as of this plan the probe actually reads those two sections, so the division of labour the spec describes is now implemented rather than intended.

`agent_workflows/engine.py` plus the regenerated `AGENTS.md`: the always-loaded managed block tells every agent in every managed repo that "The verdict is CACHED on the parent's item text plus its child table". That is a public contract sentence about a mechanism this plan changes, and it is generated, so the source constant is what gets edited and the file is regenerated with `aw install .`.

NOT AMENDED, deliberately: spec `77tr3o` R-12, which states the OBLIGATION (the premise must be checked before a run relies on it) and explicitly delegates the mechanism, the caching, the four-state answer and the override to `25kzda` Section 2.5b. It names no key, so amending it would create a second description of one rule and invite the two to drift.

## Open questions

### OQ-01: Should the seven-section allowlist live in `runner_shared` or in `ipd_schema` beside the `H_*` heading constants it is built from?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to `runner_shared` for this change, with the reasoning recorded so a reviewer can overturn it on evidence rather than preference. The allowlist is not a fact about an IPD's structure (which is what `ipd_schema` owns) but a fact about what THIS probe's question depends on, so siting it in `ipd_schema` would put a probe policy in the module every consumer of document structure imports. The heading STRINGS still come from `ipd_schema`'s `H_*` constants, so there is no duplicated literal either way. If a second consumer ever needs the same section set, that is the moment to lift it.

### OQ-02: Should `Approval and execution gate` be included after all, given it produced the most pattern hits of any section?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to EXCLUDE, on the measurement rather than on size alone. Its 55 hits are concentrated in template boilerplate repeated across 34 plans ("This ORCHESTRATOR and each child MUST ..."), so the marginal signal per character is low while the section is the third largest at 87.9% of the current excerpt. Including a large block of identical boilerplate in a prompt whose dominant cost is its FALSE-POSITIVE rate is the wrong trade. A reviewer who disagrees should point at a specific orchestrator whose parent-only work is stated ONLY there, which would falsify the boilerplate reading.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session showing `ipd_lint.unattached_section_prose` on a real orchestrator, with (a) a `## Cross-IPD validation` bullet PRESENT in the output, (b) an E-item continuation line ABSENT from it, (c) an indented `- Expected outcome:` sub-field ABSENT, and (d) a line inside a fenced code block ABSENT. Then paste the corpus disjointness sweep: for every `- Kind: orchestrator` plan under `.aw/records/plans/`, count prose lines over 40 characters that also appear inside any `e_item_action_blocks` block, printing the orchestrator count and the total, which must be 0.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `sorted(runner_shared.probe_cache_payload(text))` for a real orchestrator showing exactly `['child_table_rows', 'e_items', 'prose_sections']`. Paste the digest MOVING for the same plan with a sentence added to an allowlisted section and NOT MOVING with a sentence added to `## Open questions`, printing all four digests. Paste a grep over `agent_workflows/runner_shared.py` showing the seven section titles appear only as `ipd_schema` `H_*` references and not as literal strings.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `orchestrator_probe_excerpt` output for a real orchestrator showing a rendered section for each of the three payload keys, including prose that the pre-change excerpt did not contain (quote one sentence and show it absent from the pre-change output). Paste the key-completeness assertion: for every orchestrator in the corpus, every key of `probe_cache_payload` has a corresponding rendered section, proven by a check that FAILS when a synthetic fourth key is injected. Paste the amended prompt closing sentence and confirm `render_probe_prompt` still takes the excerpt as an argument (so the template is not hashed).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the bare `python3 -m pytest` summary line with the pre-change baseline beside it and any differing failing NODE IDS named. Paste `python3 -m pytest tests/test_orchestrator_probe_payload.py -m livecorpus -o addopts=""` output including the per-invariant applicable/moved counts for groups A, B and C. Then paste the REVERT-PROOF: group B's assertions run against the pre-change payload builder, FAILING, which is what makes them regression tests.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the committed docstring prose, and paste a FRESH re-measurement of each number it states, taken at execution rather than copied from this plan: the store's entry count and verdict split read through `runner_shared.probe_verdict_store_path`; how many entries still key a live orchestrator's text before and after the widening; the count of `- Kind: orchestrator` plans in `.aw/records/plans/pending/`; the 61-lifecycle approved-to-final comparison with the shipped-moved and widened-moved counts; and the median/max/total excerpt sizes before and after. Any number that has moved since authoring must be CORRECTED in the docstring, not reconciled in prose.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff` for both spec files. The `25kzda` diff must show only the 2.5b parenthetical changing and must leave the "Ticking a checkbox ... MUST NOT re-probe" sentence byte-identical. The `r07vma` diff must show only an added `## Workflow history` note and no change to Section 3a limit 1's text. Paste `git diff` for `77tr3o` showing it is EMPTY. Paste the `aw specs note` invocations and their output.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff -- agent_workflows/engine.py AGENTS.md` after running `aw install .`, showing exactly one sentence changed in each and the new sentence no longer than the old. Paste a check that the rendered body matches the file: `engine.agents_managed_sections(target_layout="aw")`'s `pointer` body is a substring of `AGENTS.md` (True), and note that the `legacy` and `modern` renderings are not, which is expected for this repository's layout. Paste `python3 -m pytest tests/test_installer.py -o addopts="" -q` passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is one cohesive change to one mechanism: the probe's payload gains a third key, the digest and the excerpt widen with it because both read the one payload builder, the invariants that make the widening safe are re-proven in a module that survives, and every contract that states the old key is corrected in the same change. Execution follows the repository contract: `aw ipd begin` before any edit, commits only through `aw commit` limited to the declared `- Scope-Paths:`, no push, no tag, no `git add -A`, bare `python3 -m pytest` with the actual output pasted, and no claim of a passing suite that was not run. The declared spec edits are announced by the runner before the run starts and reconciled at finalize. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence.
