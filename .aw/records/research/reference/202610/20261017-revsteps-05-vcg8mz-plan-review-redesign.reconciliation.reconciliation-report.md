---
id: vcg8mz
created: 20261017
set: revsteps
order: 05
topic: [plan-review, runner]
model: reconciliation
kind: reconciliation-report
status: reference
outcome: informational
summary: Multi-model design review of the runner-enforced, depth-scaled plan review redesign (Synthesis of the model reports)
consumed-by: [k3yx72]
---

# Reconciliation: multi-model review of the plan-review redesign (spec `k3yx72`)

- Prompt: `y6vfto`. Design reviewed: spec `k3yx72` (draft, 2026-10-17 commit `a02f28222`).
- Reports: `r7rfdi` (opus55high), `xd85vw` (gemini4argonmedium), `p6pbfx` (gpt61solmedium),
  `2rrqp1` (gemini38flashhigh).
- Reconciler: opencode (Opus 5.5), the AUTHOR of the design under review. Weigh this synthesis with
  that conflict in mind; every finding marked "spot-checked" below was re-verified against the
  repository by the reconciler, not taken on the reporter's word.

## 1. Verdicts

| Report | Assessment | Notes on reliability |
| --- | --- | --- |
| `r7rfdi` opus55high | needs rework | Most thorough. Measured the depth floor over 1,544 plans. Same model family as the design author. |
| `p6pbfx` gpt61solmedium | needs rework | Strong on state, recovery, and split graph semantics. Did not reproduce counts. |
| `xd85vw` gemini4argonmedium | needs revision | Several valid code-level findings, BUT a large part of the report reviews a DIFFERENT design: it cites steps R8, a `light` depth, an `AW-DEPTH:` marker, a "30% of E-items" trigger, OQ-7, "Files that will change", and proofreading sections ("Cut structural fat", "Protect technical invariants") that exist in neither `k3yx72` nor `wcisgc`. It also claims "Inferred count: 0" while asserting things that are false (for example its F-09.2 claim that an Order-00 orchestrator sorts before its children is contradicted by `queue_sort_key`'s dependency-depth-first rule: orchestrators declare their children). Its answers to OQ-1 to OQ-7 answer questions the design never asked. Findings from this report are used ONLY where independently confirmed. |
| `2rrqp1` gemini38flashhigh | sound with changes | Short; several findings duplicate others. One claim (F-02 "`parse_review_text` fails closed if `- Verdict:` is absent") was not verified. |

## 2. Consensus findings (raised by two or more reports, or by one and spot-checked)

Ids in brackets are the reporting findings. "SC" = spot-checked by the reconciler.

| # | Issue | Reports | Severity (max) | Resolution adopted for the next design revision |
| --- | --- | --- | --- | --- |
| C-01 | **Re-review baseline is cumulative.** §8.2 compares S-01 with S-06 in every round, so any round-1 structural fix re-triggers forever and the two-round cap forces `no-go` on a corrected plan. | r7rfdi F-08, p6pbfx F-01 | blocker | Each round compares against the plan AT THE START OF THAT ROUND. A round with zero edits clears earlier triggers. Test: round 1 adds an E/V pair, round 2 changes nothing, review passes. |
| C-02 | **A malformed marker is treated as `AGAIN`.** Two formatting slips force a false `no-go`. | r7rfdi F-08, xd85vw F-04, (2rrqp1 F-07 adjacent) | major | On a missing or malformed last line, re-ask ONCE in the same session for the marker only (existing `perform_defect_reask` pattern). A second failure is a review PROTOCOL failure (review incomplete, plan stays `to-review`), not `AGAIN` and not `no-go`. Transport failure (timeout, nonzero exit) is handled before marker parsing. |
| C-03 | **Partial re-review rounds hide earlier findings.** Readers treat only the LAST `## Round` as live (`review_findings.ReviewDocument.current_round`), so a changed-sections-only round drops unresolved findings from the gate. | r7rfdi F-02, p6pbfx F-02 | blocker | One `## Round <n>` per review INVOCATION; re-review passes are subsections inside it. The round's canonical `### Findings` and `### Decisions` tables carry forward every finding with its final disposition. |
| C-04 | **Per-step H3 subsections blind the findings parser.** `parse_review_text` reads finding rows only under an H3 starting with `Findings`/`Decisions` (SC: `cur_section = mh3.group(1).strip().lower()`), so findings written under `### R1 References` are silently ignored and gates fail open. | xd85vw F-01, p6pbfx F-08 | blocker | Keep ONE canonical `### Findings` and `### Decisions` table per round. Step completion records go in separately named subsections that hold evidence, not findings. Amend `.aw/records/reviews/README.md` and parser tests accordingly. |
| C-05 | **S-02 rules contradict each other.** §10 adaptation 1 tells the proofreader to record ambiguities as open questions; §4.1 refuses any change to open-question ids. | xd85vw F-02, p6pbfx F-03 | blocker | S-02 records unresolved ambiguities in a `### Proofreading` subsection of the review round, NOT in the plan. S-05 promotes material ones into plan open questions. |
| C-06 | **The wording-only check is both too loose and too strict.** It misses `Execution state`, `Expected outcome`, `Depends on`, open-question `Status`, and requirement meaning without modal words; a document-wide modal-word diff fires on legitimate deduplication and on the proofreader's own instruction to normalize must/should/may. | r7rfdi F-09, p6pbfx F-03, xd85vw F-06, 2rrqp1 F-06 | major | Rename it the "structural preservation check". REFUSE changes to: metadata, H2 list, E/V ids, checkbox states, `Execution state`, open-question ids/`Status`/`Blocking`, field names under each leaf. RECORD AS RE-REVIEW INPUT (not refusal): changes to `Expected outcome`, `Depends on`, validation demands, and modal words inside E/V items. S-02 modal changes are not a runner trigger; they are an input R2/R4 must confirm. On refusal: restore the plan to its pre-S-02 content and continue (one retry max), rather than failing the review. State plainly that no structural check proves meaning was preserved. |
| C-07 | **Commit subject and history line.** Staleness detection keys on the newest commit whose subject starts `plan-review:` (SC: `plan_readiness.review_staleness_index`); auto-approve needs a review history record; spec `25kzda` 4.4 `IPD-REVIEW-HISTORY` needs exactly one review entry per review. | r7rfdi F-03, 2rrqp1 F-01, xd85vw F-11 | major | One history line and one `plan-review:` commit per review invocation, whatever the number of passes. Pre-review mechanical commits use a non-`plan-review:` subject. Fix the runner's fallback lane commit subject (`review(<host>): ...`) too. |
| C-08 | **Negative and incomplete reviews have no finalization path.** S-07 requires conforming lint, but lint refuses an open `Blocking: yes` question at every checkpoint (SC); orchestrator repair exhaustion deliberately leaves `- Readiness:` ABSENT; the `IPD-S407`/`S408` repair loops and the escalation of unfixed findings to `Blocking: yes` questions are not assigned to any step. | p6pbfx F-04, r7rfdi F-10 | major | Define three outcomes: completed-pass, completed-negative (`no-go`, findings and blockers preserved, plan stays `to-review`), and incomplete (protocol or host failure). S-07 postcondition: valid `- Readiness:` OR absent with a recorded exhausted-repair reason. Put the S407/S408 repair loops and the finding-escalation rule into named steps with postconditions (`check.review-finding-unescalated` passes). |
| C-09 | **`Blocking: no` questions do not force `no-go`.** §4's runner rule says any unresolved question gives `no-go`, contradicting `plan-review.md` (SC: "A NON-BLOCKING open question does NOT make a plan `NO-GO`"). | xd85vw F-05 | major | Only an open `Blocking: yes` question forces `no-go`. |
| C-10 | **Postconditions can be satisfied without doing the work.** Empty step subsections, a no-op proofread, a rating always at the floor, every question marked `Blocking: no`. | r7rfdi F-05, p6pbfx F-08, 2rrqp1 F-05 | major | Each step emits a typed evidence record the runner checks against the repository: R1 = resolver output the runner re-runs; R2 = one row per E/V id diffed against the parser; R3/R4 = one row per rubric item with a quote or citation the runner verifies exists; S-03 = measured signals plus reason even at the floor; S-05 = a rationale for every `Blocking: no` added or changed. State the limit: receipts raise the cost of fake compliance; they do not prove review quality. |
| C-11 | **No session/crash/resume protocol.** Antigravity falls back to `--continue` (most recent conversation) without a captured id; `max_items_per_session` (default 4) rotates sessions and would split a review mid-sequence; no rule for crash between steps, resume, or upstream edits to the plan during review. | r7rfdi F-06, p6pbfx F-05, xd85vw F-09.1, 2rrqp1 F-02 | major | Persist per review: review id, round, step, input/output digests, session id, worktree, budget used. Capture the session id after the first agent step and refuse `--continue` fallback. Count one review as one item for session rotation and never rotate mid-review. On resume: continue at the first incomplete step in the same session if resumable, else restart from S-02 in a new session. On postcondition failure: restore the plan to the S-01 snapshot. If the plan changed upstream, stop with a named refusal. Unique log names per step/round/attempt. |
| C-12 | **Depth floor does not discriminate.** Measured over 1,544 plans: "spans more than one top-level directory" holds for 1,068 because code plus `tests/` is the normal case; 0 of 30 pending plans come out `simple`. | r7rfdi F-04 (measured), xd85vw OQ-3 adjacent | major | Count distinct NON-TEST top-level directories; count production source files instead of Scope-Paths entries; add public-contract changes, non-empty `Item-Dependencies`, `Blocks-Release`, and configured sensitive paths as signals; treat `Scope-Paths: grandfathered` as at least `standard`. Publish the measured tier distribution in the spec before fixing thresholds. Recompute the floor after review edits and rerun newly required steps if it rises. |
| C-13 | **`simple` drops the engineering core.** A small plan can still break invariants, recovery, or authorization; R2 covers only executability. Leaf overload ("packing") is checked by no `standard` step. | p6pbfx F-07, 2rrqp1 F-04, xd85vw F-08 | major | A compact mandatory core at every depth (correctness, invariants, feasible validation, conceptual density/leaf overload, spec obligations). Depth scales investigation breadth (R4 full rubric, R5 personas, R6 decomposition), not whether the core runs. |
| C-14 | **Orchestrators should not be `complex`.** They carry no work; personas and decomposition have nothing to evaluate. | r7rfdi F-11, 2rrqp1 F-03, xd85vw OQ-6 | minor | Orchestrators get their own fixed profile: R1, R2 (child table, coverage, ordering), R7. Never R5/R6. |
| C-15 | **Split step breaks several contracts.** (a) A superseded original still carrying `From-Backlog` is a carrier that never executes, so a release-blocking item can never close via HANDOFF (SC: `_carrier_is_executed`). (b) Inbound `executed:<original>` dependency edges become unsatisfiable. (c) `aw ipd scaffold` output is `draft` with placeholders and cannot enter `to-review` until fully authored and coverage-checked. (d) The runner spec freezes the queue: new IPDs "never join the frozen run" (SC: `25kzda` 2.6). (e) No Set-id rule, no retirement verb, no recursion bound. (f) Splitting a human-`approved` plan discards a human decision. | r7rfdi F-07, p6pbfx F-09/F-10, xd85vw F-03, 2rrqp1 F-08 | blocker | Split is a recorded graph rewrite in one transaction: mint a NEW Set id; fully author and lint every replacement to `to-review` and pass coverage BEFORE retiring the original; remap inbound dependency edges; transfer `From-Backlog`/`From-Spec`/`Blocks-Release` and clear them on the original (or make carrier evaluation supersession-aware); retire through a tooled verb; record new ids as next-run actions (do not join the frozen queue unless `25kzda` 2.6 is amended); a split product may not be split again in the same chain; never auto-split a plan that was `approved` when the review began (leave it `no-go` with the proposal). |
| C-16 | **Citation enforcement contradicts an implemented spec.** `20260802-1904` Section 10.2 (SC) says "PROMOTION TO A GATING SEVERITY IS REFUSED" and "Existing citations are NOT retrofitted"; the design proposes both and names the wrong spec (`20260726-1340` has no Section 10.2). | r7rfdi F-01, p6pbfx F-14 | blocker | Name `20260802-1904` §10.2 as the amendment target. Keep `IPD-C801` advisory; put enforcement in the RESOLVER (does it resolve?), which avoids the form-heuristic false positives behind the refusal. R1 rewrites are forward-only (add an anchor, never delete evidence). If the maintainer wants the line-number ban to gate, that is an explicit reversal of §10.2 and must answer its measured reasons. |
| C-17 | **Citation resolver semantics are undefined.** No distinction between existing evidence and targets the plan will create; no duplicate/ambiguity policy; moved and generated files; "fails visibly when its target changes" overpromises (a function can change behavior keeping its name); "records ids never change" is false for E/V items. | p6pbfx F-11/F-12/F-13, r7rfdi F-13, 2rrqp1 F-09 | major | Typed citations: existing, proposed (names the creating item), dependency-provided (checked at begin). Unique resolution only; distinct results `ok`, `not-found`, `ambiguous`, `file-missing`, `moved-to`. Generated files cite their generator. Reword the goal: identity survives unrelated edits and broken anchors are reported; resolution does not prove the claim. |
| C-18 | **Cost.** 8 to 11 prompts is really 9 to 20 with re-review, and session context grows each turn. | r7rfdi F-14, 2rrqp1 F-10, p6pbfx alt. 2 | minor | Merge steps that gain no separate check (see section 4). Measure tokens and wall time per depth on a real run before fixing the step count. |
| C-19 | **Free-form path diverges.** The free-form checklist cannot compute the floor or run the structural check. | r7rfdi F-15, xd85vw OQ-5 | minor | Expose `aw ipd review-floor <id6>` and `aw ipd review-check <id6> --step ...`; runner and checklist call the same functions. |
| C-20 | **Smaller corrections.** "166 citations in 23 files" is unreproduced; opus55high counts 189 in 13 files with 0 in pending plans (133 in two specs), so plan review would migrate almost nothing. `- Review-Depth:` must be registered in `ipd_schema` (else `IPD-M103`), excluded from the review-staleness digest, and written in S-07 rather than mid-session. Name the lint phase (`--phase author`, "no NEW error"). "Follows the pattern of `classify_probe_reply`" is misleading (it reads the FIRST line and rejects both sentinels). Pre-review commit is conditional today. Missing review checks to carry over: volatile counts in `Expected outcome`, the code-pinning-test ban, and `## Spec / documentation sync` truthfulness. | r7rfdi F-12/F-16/F-17, xd85vw F-07/F-12, p6pbfx limits, 2rrqp1 F-07 | minor / wording | Apply as stated. |

## 3. Open-question answers

| OQ | Consensus answer |
| --- | --- |
| OQ-2 quoted-text syntax | No consensus on spelling. Candidates: `` `path` "text" `` (r7rfdi), `path::quote("<JSON string>")` (p6pbfx), `path::"text"` (2rrqp1). All agree: single line, unique match in the file, distinct `not-found`/`ambiguous` results. The JSON form has the cleanest escaping; the `path::"text"` form is most consistent with `path::Symbol`. Maintainer decision. |
| OQ-3 begin refuse vs warn | Two-tier, all three valid reports agree in substance: REFUSE when a broken citation is in `Scope-Paths`, `Item-Dependencies`, an E-item, or a V-item command/expected outcome (and is an existing-evidence citation in a post-cutover plan); WARN for narrative prose, grandfathered plans, and proposed targets. |
| OQ-4 split inheritance | Yes to all three, PLUS clear or supersession-gate the original's carrier fields and remap dependencies (C-15). Unanimous. |
| OQ-5 sensitive paths | Yes: an opt-in `.aw/config/project.json` glob list (empty default in the package; this repo seeds its own). Unanimous. |
| OQ-6 Set depth | Per plan. Orchestrators use their own fixed profile, not `complex` (three reports; p6pbfx alone keeps `complex`). Set-level R7 runs against one recorded set of member revisions. |

## 4. Challenges to fixed decisions

| Decision | Challenge | Reports | Reconciler's recommendation |
| --- | --- | --- | --- |
| MD-2 split without human approval | Narrow carve-out: do not auto-split a plan that was human-`approved` when the review began; optionally restrict to agent-authored plans. | r7rfdi, 2rrqp1 | Adopt the `approved` carve-out (it preserves MD-2 for the common case). Author-based restriction: maintainer call. |
| MD-5 citation format | The FORMAT is fine; reading MD-5 as including gating and retrofitting reverses `20260802-1904` §10.2 without engaging its evidence. | r7rfdi | Keep format; enforce via resolver; maintainer decides whether to reverse §10.2. |
| MD-6 one session | Token accumulation across 8 to 20 prompts. | 2rrqp1 | Keep MD-6 but cut prompt count (below) and measure. |

## 5. Alternatives proposed

Three reports independently propose cutting the prompt count while keeping runner enforcement. The
convergent shape:

1. Runner-local pre-pass (no agent): lint, coverage, floor, citation resolver, E/V inventory.
2. Agent prompt 1: proofread + complexity rating (marker `AW-DEPTH: <level>`).
3. Agent prompt(s) 2..k: the depth-scaled review, either as ONE prompt with per-step typed evidence
   tables (r7rfdi alt. 1, 2rrqp1 alt. 1/2) or as merged step groups (r7rfdi alt. 2: R1+R2, R3,
   R4+R5, R6+R7).
4. Agent final prompt: resolve questions + re-review marker + verdict/finalize.

That gives about 3 to 6 prompts instead of 8 to 11, and the runner checks the evidence tables (C-10),
which is what actually enforces depth. The cost is weaker protection against within-prompt
instruction drift, which is what separate prompts were for. This is the main design choice the
maintainer must make next.

## 6. Recommended next actions

1. Maintainer decisions: (a) prompt granularity (section 5); (b) OQ-2 spelling; (c) whether to
   reverse `20260802-1904` §10.2 or enforce via the resolver only (C-16); (d) the MD-2 `approved`
   carve-out; (e) same-run split requeue (amend `25kzda` 2.6) or next-run handoff.
2. Revise spec `k3yx72` in place with C-01 to C-20 and those decisions.
3. Re-run the review on the revised spec with the same four models only if decision (a) changes the
   architecture; otherwise proceed to `/spec-review`.
