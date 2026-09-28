# IPD: Render one authoritative reason per unmet dependency and restore the diagnostics block the status rename silenced

- Date: 2026-09-28
- Kind: child
- Concern: `render_stream.render_run_summary_table`'s dependency-block diagnostics arm renders two contradictory reasons for a cascade-blocked item, and at current HEAD renders NOTHING AT ALL because the status it keys on is no longer written.
- Scope: Make `cascade_dependency_blocked` write the same `unsatisfied_dependency_reasons` map the drain path writes, drop the contradictory placeholder in the two renderers that read the pair, key both on the canonical status vocabulary rather than the retired legacy token, and pin all three behaviors with tests.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/render_stream.py, tests/test_dependency_block_reporting.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: fvsyqk
- Blocks-Release: next
- Set: fvsyqk
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 5o1jye

## Workflow history

- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog item `fvsyqk`. Measured the filed defect, and measured a STRICTLY WORSE second defect on the same lines (the arm is dead at HEAD), so the plan fixes both producers, both renderers, and the status key.

## Goal

An operator reading a run's exit summary at 3am must be told, for each unmet dependency of a blocked item, exactly ONE reason, and must be told it AT ALL. Today the dependency arm of the diagnostics block does neither: for a cascade-blocked item it composes two disagreeing parentheticals, and since the terminal-status rename it is unreachable in a live run, so the entire arm renders silence. This plan makes the two producers of `unsatisfied_dependencies` agree on one shape, removes the placeholder that manufactured the contradiction, re-points the renderers at the status the runner actually writes, and leaves behind the behavioral tests whose absence let the arm die unnoticed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the two producers agree

- [ ] E-01 In `runner_shared.cascade_dependency_blocked`, write `item["unsatisfied_dependency_reasons"]` alongside `item["unsatisfied_dependencies"]`, and make the dependency TOKEN bare. Today the function appends `f"{edge.canonical()} (target {st})"` into `dead` and writes no reason map; change it to accumulate the bare `edge.canonical()` in the token list and the per-edge prose (`f"target {edge.id6} is {st}"`) in a parallel dict, so this producer's output is shape-identical to the drain path's in `oc_runipd`/`agy_runipd`. Keep writing the `dependency-blocked` event with the same key names it writes today, and keep the event's `dependencies` value carrying the SAME token list the item does, so the durable stream and the item never disagree.
  - Depends on: none
  - Expected outcome: `cascade_dependency_blocked` sets both keys; a cascade-blocked item's `unsatisfied_dependencies` contains `executed:aaa111` (no embedded parenthetical) and its `unsatisfied_dependency_reasons` maps that exact token to `target aaa111 is reviewed`.
  - Execution state: pending

- [ ] E-02 In the same function, preserve the reason text's INFORMATION rather than only its shape: the prose must still name the target's status, because that status is the operator's actual next question (which prerequisite died, and how). Confirm by reading `dependency_status_detailed`'s reason strings that the new prose is consistent in register with the drain path's (it writes target-status prose too), and do NOT invent a second vocabulary for the same fact.
  - Depends on: E-01
  - Expected outcome: a written comparison, recorded in this plan's V-02 evidence, of the reason string this function now writes against the strings `dependency_status_detailed` writes, showing both name the target and its status.
  - Execution state: pending

### Task group 2: stop the renderers contradicting themselves

- [ ] E-03 In `render_stream.render_run_summary_table`'s diagnostics block, remove the `reasons.get(d, 'blocked')` placeholder: render `f"{d} ({reason})"` only when a reason WAS recorded for `d`, and bare `d` otherwise. This is the same repair `run_selection_policy.derive_item_disposition` already applies to its own line (`"{0} ({1})".format(d, why[d]) if d in why else str(d)`), so the two surfaces stop diverging. Keep the `"unmet dependencies"` fallback for the empty-list case exactly as it is: that one is not a per-dependency placeholder and it is the `5e4sb6` repair's safety net.
  - Depends on: none
  - Expected outcome: a cascade-produced item renders one parenthetical, not two; a drain-produced item still renders its mapped reason parenthesized exactly once.
  - Execution state: pending

- [ ] E-04 Key BOTH surfaces that read this pair on the status the runner actually writes. `render_stream`'s arm tests `st == "dependency-blocked"` and `runner_shared.write_report`'s `## Dependency blocks (why)` section tests `item.get("status") == "dependency-blocked"`, but every producer writes `fail-depend` (canonical since `statusvocab` `cyamvi`), so both are dead in a live run. Accept BOTH tokens rather than swapping one for the other, because `TERMINAL_STATUS_ALIASES` keeps the legacy spelling readable forever for run directories already frozen on disk; route through the existing `canonical_terminal_status` where the module already imports it, or compare against both tokens where it does not, and do NOT add a first-party import to `render_stream` that its import-purity guards forbid.
  - Depends on: none
  - Expected outcome: an item whose status is `fail-depend` renders its dependency diagnostics in the exit summary table AND gets a `## Dependency blocks (why)` section in `execution-report.md`; an item carrying the legacy `dependency-blocked` still does too.
  - Execution state: pending

### Task group 3: pin it so it cannot die silently again

- [ ] E-05 Add `tests/test_dependency_block_reporting.py` asserting on BEHAVIOR (build a state, call the real renderer and the real `write_report`, read the output), never on source text. It must pin, as separate cases: (a) the cascade producer's output shape, written by calling `cascade_dependency_blocked` itself rather than by hand-building the dict, so the test fails if the producer regresses; (b) that the rendered diagnostics line for that item contains NO second parenthetical and specifically not the substring `(blocked)`; (c) that a drain-shaped item still renders its mapped reason exactly once; (d) that BOTH the canonical `fail-depend` and the legacy `dependency-blocked` render diagnostics, the canonical case being the regression that this plan's F-02 measures as shipped-broken; and (e) the same canonical/legacy pair for `write_report`'s `## Dependency blocks (why)` section.
  - Depends on: E-01, E-03, E-04
  - Expected outcome: a new test module whose cases fail on HEAD before the fix and pass after, covering both producers, both renderers, and both status spellings.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE ANTI-RE-FORK DISCIPLINE governs where a dependency rule may live. `runner_shared.cascade_dependency_blocked` and `dependency_status_detailed` are DEFINED once in `runner_shared` and RE-EXPORTED by both hosts (`oc_runipd` and `agy_runipd` both carry `cascade_dependency_blocked as cascade_dependency_blocked`), and `agy_runipd`'s own comment records that agy "carried a broken `dependency_status_detailed` for months" as a re-fork. So E-01's edit belongs in `runner_shared` and reaches both hosts by construction; adding a per-host branch would be the exact defect those comments exist to prevent.
- `render_stream` IS A PURE RENDERER and its import surface is deliberately narrow. `render_run_summary_table`'s docstring states it "must not import a runner to reach `queue_sort_key`", and `run_selection_policy.derive_item_disposition` duck-types its refusal reader rather than importing `render_stream`, explicitly to protect "a module whose two-import purity other plans depend on". E-04 must therefore not reach for a runner import; comparing against both status tokens locally is the conforming shape.
- THE ADDITIVE-KEY CONVENTION for this exact pair is already recorded at both drain sites: "an ADDITIVE companion key. The flat `unsatisfied_dependencies` list[str] keeps its exact shape and meaning, so every existing consumer is untouched; the reasons live alongside it" (`revgate` Order 03, `7nkcgp` E-04). E-01 brings the third producer into that convention rather than inventing a fourth shape.
- LEGACY STATUS TOKENS STAY READABLE FOREVER. `runner_shared.TERMINAL_STATUS_ALIASES` maps `"dependency-blocked" -> "fail-depend"`, and the amendment note on spec `25kzda` states legacy tokens "remain readable forever for backward compatibility on historical run records (via TERMINAL_STATUS_ALIASES), but are no longer written by the runner." This is why E-04 ACCEPTS both tokens instead of replacing one.
- A GUARD THAT CANNOT FAIL IS NOT EVIDENCE, and a guard must assert on behavior rather than on source text. Both are `r2i1b1`'s own recorded standard for this very code ("asserting on BEHAVIOR (render a state, read the output) rather than on source text, because a guard that greps for `if status in` ..."), and its V-06/V-07 required a mutation check. E-05 and V-05 adopt both.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE FILED DEFECT IS REAL AND REPRODUCES EXACTLY AS DESCRIBED, once the item is given the status the renderer still keys on.** Rendering a queue entry with `status: "dependency-blocked"`, `unsatisfied_dependencies: ["executed:aaa111 (target reviewed)"]` and no reason map produces the line `• eee555: dependency-blocked (executed:aaa111 (target reviewed) (blocked))`. Two parenthetical reasons, one embedded by the producer and one manufactured by the renderer's `reasons.get(d, 'blocked')` fallback, with nothing telling the reader which is authoritative. | Called the real `render_stream.render_run_summary_table` on that state with `Palette(False)`; the quoted line is its verbatim output. |
| F-02 | **A STRICTLY WORSE SECOND DEFECT SITS ON THE SAME LINES AND IS THE ONE A LIVE RUN ACTUALLY HITS: the arm is DEAD at HEAD.** Every producer writes the canonical `fail-depend` (`runner_shared.cascade_dependency_blocked`, and the drain arms in `oc_runipd` and `agy_runipd` all assign `item["status"] = "fail-depend"`), while the renderer's condition is `elif st == "dependency-blocked"`. Rendering the SAME two items with `fail-depend` produces NO DIAGNOSTIC LINES AT ALL: not a double-explained reason, no reason whatsoever. So the item's "on the surface an operator reads at 3am" is optimistic; today that surface reads silence. Fixing only the double-gloss would leave the arm dead and the fix unobservable in production. | `rg` for `item["status"] = ` in both hosts and `runner_shared` returns only `fail-depend` for this disposition; a side-by-side render of the identical queue under both spellings printed two diagnostic lines for `dependency-blocked` and `<<< NO DIAGNOSTIC LINES AT ALL >>>` for `fail-depend`. |
| F-03 | **THE SAME DEAD-KEY DEFECT ALSO SILENCES THE WRITTEN REPORT'S DEDICATED SECTION, so the second surface an operator reads is affected too.** `runner_shared.write_report` builds `## Dependency blocks (why)` gated on `item.get("status") == "dependency-blocked"`. Under the canonical `fail-depend` the section is ABSENT from `execution-report.md` entirely; under the legacy token it appears and renders correctly. This is the section `revgate` `7nkcgp` E-04 added expressly to "name the ROOT CAUSE in the report an operator actually reads, not only in events.jsonl", and a comment inside `dispatch_orchestrator_item` still asserts the section "is gated on `status == "dependency-blocked"`, which is `terminal_status`'s default" - but that default is now `fail-depend`, so the comment describes a coupling that the rename severed. Hence E-04 covers BOTH surfaces rather than only the summary table. | Called the real `runner_shared.write_report` with `labels=OC_HOST_LABELS` on both spellings of the same queue: `<<< NO 'Dependency blocks (why)' SECTION >>>` for `fail-depend`, and a correctly rendered section for `dependency-blocked`. Read of `dispatch_orchestrator_item`'s `terminal_status: str = "fail-depend"` default against its own comment. |
| F-04 | **THE REGRESSION WAS INTRODUCED BY `statusvocab` `cyamvi` AND THE MISS IS VISIBLE IN ITS OWN DIFF.** That commit widened THREE status tuples in `render_stream.py` (the `execution_index` completion set, the `FAILED` branch, and the `BLOCKED` branch, all gaining `fail-depend`) but left the diagnostics arm's `== "dependency-blocked"` equality untouched. So the run-level BANNER correctly says `BLOCKED` while the block that would explain WHY says nothing: the two halves of one screen were updated inconsistently in a single commit. | `git show 6b94a4d9 -- agent_workflows/render_stream.py` shows `fail-depend` added to three tuples and no change to the diagnostics arm; `cyamvi`'s `- Scope-Paths:` does declare `agent_workflows/render_stream.py`. |
| F-05 | **THE GUARD THAT EXISTED TO CATCH EXACTLY THIS CLASS WAS DELETED ONE DAY BEFORE THE BREAKING COMMIT.** `r2i1b1` E-07 built `tests/test_refusal_surfacing.py::TestNoFieldNameMismatch` for "the defect class F-4 actually found: a branch whose rendering condition reads a field the producing code never writes", and `TestNoStatusAllowlist` for the allowlist shape. `tests/test_refusal_surfacing.py` was DELETED in `19313eed` ("trim test suite from 9,136 to under 2,000 tests", 2026-09-24); `cyamvi` landed 2026-09-25. Neither class exists in `tests/` at HEAD. This explains why a green suite tolerated the break, and it is the argument for E-05 pinning behavior rather than trusting the next rename. | `rg` for both class names across `tests/` returns nothing; `git log --diff-filter=D -- tests/test_refusal_surfacing.py` returns `19313eed`; `git merge-base --is-ancestor 19313eed 6b94a4d9` confirms the deletion precedes the rename. |
| F-06 | **NO CURRENT TEST EXERCISES THE DEPENDENCY ARM AT ALL, so E-05 is net-new coverage and not a duplicate.** Only three test modules call `render_run_summary_table` (`test_finalize_sendback.py`, `test_interrupt_attempt_metadata.py`, `test_spec_production.py`) and `rg -c unsatisfied_dep` across all three returns zero matches. `tests/test_run_summary_table.py`, despite its name, tests `run_viewer.render_steps_table` and the `Landed` column, not this renderer. A new module is therefore the right home; no existing file is being bypassed. | `rg -rn "render_run_summary_table" tests/` lists exactly those three; `rg -c "unsatisfied_dep"` on them reports no matches; read of `test_run_summary_table.py`'s imports (`run_viewer`, `ArtifactAudit`, `landed_verdict`) and docstring. |
| F-07 | **THE PREFERRED FIX DIRECTION IN THE ITEM IS THE CORRECT ONE, AND BOTH HALVES ARE NEEDED.** The item names two candidates and prefers making `cascade_dependency_blocked` write the reason map "since it makes the two producers agree". Confirmed: the drain path in both hosts writes a bare token plus a map, so aligning the cascade removes the divergence at the source. But the renderer half is ALSO required, because a run directory frozen by today's driver already contains cascade-embedded tokens with no map, and the renderer is what those runs are read back through. Doing only the producer leaves historical runs double-explained; doing only the renderer leaves two producers writing two shapes for the next consumer to trip over. | Read of the drain arms in `oc_runipd`/`agy_runipd` (bare `missing` + `why` map) against `cascade_dependency_blocked` (embedded token, no map); read of the item's own "Candidate fixes" sentence. |
| F-08 | **A SIBLING RENDERER ALREADY IMPLEMENTS E-03's REPAIR AND PINS IT, so this plan is copying a settled in-repo decision rather than inventing one.** `run_selection_policy.derive_item_disposition` renders `"{0} ({1})".format(d, why[d]) if d in why else str(d)`, its comment names the same two producers and the same measured HEAD `7562ca6c`, and `tests/test_run_selection_policy.py` pins it with a row whose FORBIDDEN substring is `(unsatisfied)`. That comment also explicitly records that `render_stream`'s block "carries the same fallback shape (`reasons.get(d, "blocked")`) and the same wart; that block is outside this plan's fence, so the divergence is REPORTED rather than edited here" - which is this backlog item's provenance. | Read of `derive_item_disposition`'s dependency arm and comment; read of the `_DISPOSITION_LINES` row "a dependency token that ALREADY CARRIES its reason, with no map" and its paired "the OTHER producer's shape" row. |
| F-09 | **NO PENDING PLAN HOLDS A FENCE OVER THESE PATHS AND THE PREVIOUS FENCE OWNER IS RETIRED.** `orchprobe` `r2i1b1`, the plan the item names as owning this diagnostics work, is `- Status: executed`, so it holds no expression now. One pending plan declares `agent_workflows/render_stream.py`: `4po0sc` (`- Scope-Paths: agent_workflows/render_stream.py, tests/test_zero_dispatch_outcome.py`), and it edits the `COMPLETED`/success BRANCH of the outcome banner, a different expression in a different function region from the diagnostics arm, with a disjoint test file. Per AGENTS.md the runner isolates each item in its own worktree and merges through a revalidation gate, so a shared file is not a hazard; the honest statement is that the two edits do not touch the same expression. | `rg -l` over `.aw/records/plans/pending/` for `render_stream.py` in `- Scope-Paths:` returns only `4po0sc`; read of its `- Scope-Paths:` and of its F-03, which names the success-branch tuple; read of `r2i1b1`'s `- Status:`. |
| F-10 | **THE `fail-depend` SPELLING IS ALSO WHAT THE PRODUCER-SIDE TESTS ALREADY ASSERT, so E-01 must not regress them.** `tests/test_terminal_status_vocabulary.py` asserts `blocked[0]["status"] == "fail-depend"` after calling `cascade_dependency_blocked` in two places, and `tests/test_runner_shared.py` asserts `state["queue"][1]["status"] == "fail-depend"`. None of them asserts on the TOKEN TEXT, so making the token bare breaks no existing assertion; `tests/test_oc_runipd.py` reads the returned id6 list only. This bounds E-01's blast radius to the renderers. | `rg` for `fail-depend` and `cascade_dependency_blocked` across `tests/`; read of each assertion's subject. |

## Proposed changes (ordered, validatable)

1. `runner_shared.cascade_dependency_blocked` (E-01, E-02): accumulate bare canonical tokens in `dead` and a parallel `reasons` dict naming each dead target's status; write both onto the item; keep the event's key names and keep its `dependencies` value equal to the item's token list.
2. `render_stream.render_run_summary_table` (E-03): drop the `reasons.get(d, 'blocked')` placeholder in favor of parenthesizing only a reason that was actually recorded, leaving the empty-list `"unmet dependencies"` fallback intact.
3. `render_stream.render_run_summary_table` (E-04): accept the canonical `fail-depend` as well as the legacy `dependency-blocked` in the diagnostics arm's condition, without adding a runner import.
4. `runner_shared.write_report` (E-04): accept the same pair in the `## Dependency blocks (why)` gate.
5. `tests/test_dependency_block_reporting.py` (E-05): new behavioral module covering both producers, both renderers, and both status spellings, with a mutation check demonstrating each case can fail.

## Deferred / out of scope (with reason)

- RESTORING `r2i1b1`'s DELETED GUARDS (`TestNoStatusAllowlist`, `TestNoFieldNameMismatch`) IS OUT OF SCOPE. F-05 establishes they were deleted wholesale in a suite-wide trim (`19313eed`) covering far more than this arm; reinstating them is a decision about that trim's scope and about AST-derived structural guards generally, which is a separate concern with its own test-count budget. This plan pins the behavior it fixes and records the causal history in F-05 so the question is filed rather than lost.
  - Carrier: 1bxw6o
- AUDITING EVERY OTHER SURFACE FOR THE SAME DEAD-STATUS-KEY CLASS IS OUT OF SCOPE. F-04 shows `cyamvi` updated three tuples and missed one equality; a repo-wide sweep for `== "dependency-blocked"` and its siblings across every renderer would be a different plan with a different blast radius. This plan fixes the two surfaces the item's defect actually reaches (the summary table and the written report) and names the class in F-03/F-04 so a follow-up can be scoped from evidence.
  - Carrier: cxrpwv
- CHANGING THE `unsatisfied_dependencies` KEY NAME, SHAPE, OR THE `dependency-blocked` EVENT NAME IS OUT OF SCOPE. The additive-key convention is deliberate and `runner_shared` records that the event name "is KEPT for continuity with the 28 already on disk". This plan changes the token's CONTENT for one producer, never the contract.
  - Carrier-Declined: There is nothing to carry. This row records a PROHIBITION on this plan rather than an outstanding defect: the additive-key shape and the retained event name are the CORRECT state, deliberately chosen by `revgate` `7nkcgp` and by `runner_shared`'s own continuity note, so no future work is owed and a carrier would name an obligation that does not exist. V-01 enforces it inside this plan by requiring the event's key names and its `dependencies` value be shown unchanged.
- NORMALIZING HISTORICAL RUN DIRECTORIES ON DISK IS OUT OF SCOPE. Legacy records stay readable, which is what E-04's both-tokens acceptance delivers; rewriting frozen `state.json` files would mutate durable history.
  - Carrier-Declined: Nothing is owed. Leaving frozen run records untouched is not a gap but the committed contract: spec `25kzda`'s 2026-09-25 amendment note states legacy tokens "remain readable forever", and OQ-02 records why a reader must accept both spellings. E-04 makes every such record render correctly WITHOUT rewriting it, so there is no residual work for a carrier to hold; a plan that mutated durable history would be the defect.

## Scope check

- Over-scope: none. Each declared path carries a specific E-item: `runner_shared.py` for E-01/E-02 (producer) and E-04 (written report), `render_stream.py` for E-03/E-04 (summary table), and the new test module for E-05.
- Under-scope: NONE DECLARED BUT UNMODIFIED IS EXPECTED. The executor MUST verify at finalize that `git diff --cached --name-only` lists exactly the three declared paths. If the fix in E-04 turns out to require a shared helper that a third module must expose, that is a SCOPE CHANGE and must be reported through the reconciliation gate rather than absorbed silently.

## Required tests / validation

- `python3 -m pytest` run BARE, per the execution contract, with the `N passed` summary line pasted. Do not add flags.
- The new module run alone for per-test visibility, using `python3 -m pytest -o addopts="" tests/test_dependency_block_reporting.py -v` (clearing the configured defaults explicitly rather than fighting them flag by flag).
- Targeted regression of the producer-side suites F-10 bounds: `python3 -m pytest -o addopts="" tests/test_terminal_status_vocabulary.py tests/test_runner_shared.py tests/test_oc_runipd.py`.
- Targeted regression of the sibling renderer's pins, which must remain green and must not be edited: `python3 -m pytest -o addopts="" tests/test_run_selection_policy.py`.
- A MUTATION CHECK per V-05: revert each of the three production edits in turn, show the corresponding new case FAILS, restore, show it passes.

## Spec / documentation sync

NO SPEC AMENDMENT IS OWED, and no `.spec.md` is declared in `- Scope-Paths:`. The reasoning is recorded here rather than left implicit, because declaring a spec edit is what makes both runners announce it before the run and an UNDECLARED spec edit is reported at run end as a violation.

Spec `25kzda` governs run reporting, and its 2026-09-25 amendment note already states the canonical terminal vocabulary and that legacy tokens "remain readable forever for backward compatibility on historical run records (via TERMINAL_STATUS_ALIASES), but are no longer written by the runner." E-04 IMPLEMENTS that sentence on two surfaces that were left behind by it; it does not change it. Spec `25kzda` Section 5.6 enumerates the allowed per-ITEM outcomes and the run EXIT CODES: this plan writes no new item outcome value, changes no status token, and touches no exit-code path, so neither enumeration moves. The per-dependency REASON PROSE inside a diagnostics line is not enumerated by any approved spec, which is corroborated by `revgate` `7nkcgp` having added the `## Dependency blocks (why)` section and its reason strings with no spec in its scope.

No user-facing documentation describes this line's exact text, so no README or CHANGELOG entry is owed for a repair that makes an existing line correct and reachable.

## Open questions

### OQ-01: Should the cascade's reason prose match the drain path's wording exactly, or only its register?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONLY ITS REGISTER, and the plan is authored that way. The two producers answer the same question from different data: the drain path reads `dependency_status_detailed`, which distinguishes an out-of-queue target ("not in this run") from an in-run one, while the cascade only ever fires on an in-queue entry whose status it has in hand. Forcing byte-identical strings would require the cascade to route through the other predicate, which is a behavior change to a gating function and is exactly the kind of unrequested widening the scope rules forbid. E-02 therefore requires consistency of register and that the prose name the target's status, and V-02 demands the comparison be pasted so a reviewer can dispute the wording on evidence. Note that `run_selection_policy.derive_item_disposition` derives its EXTERNAL disposition code from the substring `"not in this run"`, so the cascade's prose must NOT invent that phrase; naming the target's status keeps it clear of that coupling.

### OQ-02: Does accepting two status tokens in the renderers entrench the legacy spelling?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and the alternative would lose data. The spec amendment quoted in the spec-sync section commits to legacy tokens remaining READABLE forever while no longer being WRITTEN, and `runner_shared.TERMINAL_STATUS_ALIASES` is the mechanism. A renderer is a READER of run directories already frozen on disk, so narrowing it to the canonical token alone would make every historical `dependency-blocked` record render silence, which is the same class of harm F-02 measures. Accepting both is therefore the conforming choice, not a concession. Consistency with the rest of the codebase supports this: `TERMINAL_STATES` is deliberately the UNION of canonical and legacy tokens "so nothing that reads it narrows."

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session that builds a two-item state (a prerequisite at `reviewed`, a dependent `queued` with `executed:<prereq>`), calls the REAL `runner_shared.cascade_dependency_blocked`, and prints the dependent's `unsatisfied_dependencies` and `unsatisfied_dependency_reasons`. The token list must contain NO parenthesis, and the reason map must be keyed by that exact bare token and must name the prerequisite's status. Also paste the `dependency-blocked` event as written to `events.jsonl`, showing its `dependencies` value equals the item's token list.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the cascade's new reason string beside the reason strings `dependency_status_detailed` produces for a comparable in-run unmet edge, obtained by calling both functions and printing both, not by quoting source. State in one sentence why the two are consistent in register, and show that the cascade's prose does NOT contain the substring `not in this run` (which `run_selection_policy` keys its EXTERNAL disposition code on, per OQ-01).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diagnostics line rendered by the REAL `render_stream.render_run_summary_table` for a CASCADE-PRODUCED item (produced by calling `cascade_dependency_blocked`, not hand-built), showing exactly one parenthetical reason and NOT containing the substring `(blocked)`. In the same paste, show a DRAIN-SHAPED item (bare token plus map) still rendering its mapped reason parenthesized exactly once, so the fix is not "stop printing reasons". Also paste the empty-`unsatisfied_dependencies` case still rendering `unmet dependencies`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste, for BOTH the canonical `fail-depend` and the legacy `dependency-blocked` on an otherwise identical queue: (a) the summary table's diagnostics lines, and (b) the presence of `## Dependency blocks (why)` in the `execution-report.md` written by the REAL `runner_shared.write_report` (called with `labels=OC_HOST_LABELS`). All four must be non-empty. Paste the same four probes run against HEAD BEFORE the fix, showing the two canonical cases empty, so the regression F-02 and F-03 measure is demonstrated and not merely asserted.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_dependency_block_reporting.py -v` passing with every case named. Then a MUTATION CHECK, one per production edit: (i) restore the `reasons.get(d, 'blocked')` placeholder and show the double-explain case FAIL; (ii) narrow the diagnostics condition back to `== "dependency-blocked"` and show the canonical-status case FAIL; (iii) restore the embedded-reason token in `cascade_dependency_blocked` and show the producer-shape case FAIL. Revert each and show the module green. A case that cannot fail is not evidence. Finally paste a BARE `python3 -m pytest` with its `N passed` summary line, and the targeted runs of `tests/test_terminal_status_vocabulary.py`, `tests/test_runner_shared.py`, `tests/test_oc_runipd.py` and `tests/test_run_selection_policy.py` all green, confirming F-10's bounded blast radius and that the sibling renderer's pins were not disturbed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `- Status: to-review` and requires explicit human approval before execution. No `- Readiness:` field is written here: that field is an OUTPUT of `/plan-review` and hand-writing it would forge the attestation the auto-approve predicate reads.

EXECUTION CONTRACT. Commit only the three paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` immediately before committing, and re-verify after any failed commit attempt, since a rejecting hook can leave a co-worker's restored path in the index. Paste ACTUAL runner output for every test claim; a claimed pass with no pasted output fails this plan's validation regardless of the code's state.

POST-GATE LIFECYCLE. Do not mark this plan executed or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries concrete pasted evidence with `Result: verified`. The V-04 and V-05 mutation evidence is not optional: the defect this plan fixes survived a green suite for days precisely because no test rendered this arm (F-05, F-06), so a fix landing without a demonstrably failing-then-passing test repeats the original failure mode.

BACKLOG HANDOFF. This plan carries `- From-Backlog: fvsyqk` and inherits that item's `- Blocks-Release: next`, so executing it is what lets item `fvsyqk` close without dropping its release gate. The item itself must NOT be set `done` by this plan; the runner moves it to `graduated` on verification.
