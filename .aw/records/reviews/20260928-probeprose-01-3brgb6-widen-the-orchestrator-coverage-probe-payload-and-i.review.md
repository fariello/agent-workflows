# Review findings: plan 3brgb6

- Subject-Id: 3brgb6
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `1b29bcf8` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `"outcome":"clean"`, `findings: 0`) and `--phase
review-finalize --agent` conforms after revision with `findings: 0`. No pre-review snapshot was owed:
`git status --short` reported the plan committed and unmodified, and the lane-input copy at
`.aw/state/lane-inputs/rev-5/` is the same file. `check_engine.evaluate_durable_carrier` returned ZERO
drifts both before and after revision, and `aw check` names this plan under no rule.

EVERY MEASURED CLAIM IN THE PLAN WAS RE-DERIVED INDEPENDENTLY, over all 66 orchestrators rather than a
sample, by reimplementing the proposed extractor and payload in a scratch module and comparing against
the shipped `runner_shared` functions. SEVEN FINDINGS REPRODUCED EXACTLY, to the digit: F-06's six
no-op invariants (0 movers of 26/26/66/26/26/66 applicable), F-07's sensitivity (66 of 66 widened
movers for a `Cross-IPD validation` insertion and for a `Goal` insertion, 0 of 66 narrow; 0 of 66 for
`Open questions` and `Deferred`), F-08's disjointness (0 shared lines over 40 characters), F-09's store
accounting (26 entries, 15 `pass` / 11 `fail`, 9 keying a live orchestrator narrow and 0 widened, 0
pending orchestrators), F-11's size price (median 2,217 -> 6,561, max 10,423 -> 19,074, total
162,373 -> 480,194, +195.7% against the plan's stated +195.6%), F-12's baseline (`20 passed`) and
F-13's three contract sentences. F-02's deletion claim was confirmed at the commit
(`19313eed`, 2026-09-24, 3022 and 1615 lines, `TheExcerptHasAKnownLIMIT` present only in `19313eed^`,
and zero surviving test names `probe_cache_payload`, `probe_cache_digest` or `e_item_action_blocks`).

THE PLAN'S CORE ENGINEERING JUDGEMENT IS SOUND AND TWO CHOICES DESERVE NAMING. It widens payload and
key in ONE function so the identity `m7gvuz` E-03 exists to protect holds by construction rather than by
discipline, which is the right shape and is the reason the backlog item deferred the work rather than
doing half of it. And it refuses a `digest_version` field or dual-digest fallback explicitly, with the
correct reason stated: serving an old verdict under the old narrow key IS the stale-verdict-under-
apparent-authority failure the widening exists to close, so a compatibility shim would reintroduce the
defect while appearing to be prudence.

WHAT REVIEW FOUND IS THAT THE PLAN'S DISJOINTNESS ARGUMENT OVERSTATES ITSELF, AND THE OVERSTATEMENT
HIDES A REAL GAP OF THE SAME KIND THE PLAN EXISTS TO CLOSE.

**E-01's "EXACTLY THE COMPLEMENT" IS FALSE, AND 476 LINES FALL IN THE HOLE (PR-401, HIGH).** E-01
argued that because `e_item_action_blocks` "captures a leaf's opening line plus its INDENTED
continuation lines and nothing else", excluding every indented line "leaves exactly the complement".
Reading the shipped function shows it terminates at the FIRST blank line, the first `_SUBFIELD_RE`
match, the next leaf, or the next heading. So an indented line after a sub-field, after a blank line, or
under a non-leaf bullet is captured by NEITHER extractor. Measured over all 66 orchestrators: 827 such
lines, 476 of them (73,276 characters) inside an ALLOWLISTED section, carrying 14 matches of the plan's
own hazard pattern - 8 under `Open questions`, 2 under `Workflow history`, 1 under `Deferred`, 1 before
any H2, and one under `## Cross-IPD validation` that reads, literally, "MUST BE FLAGGED (parent-only
work no child covers)" (`yeh7gc`). I verified that string is present in the file and ABSENT from the
extracted prose for that section while the section's non-indented bullets are present. This is not a
reason to reject the plan - the disjointness PROPERTY it needs still holds, and closing the gap would
require editing the termination rule `qurgra` is concurrently re-homing - but an unstated blind spot in
a safety gate is exactly what `rmcqw8` was filed about, and filing this plan under `executed/` with the
gap recorded only in prose is precisely how the previous known limit was lost (F-02). Fixed by stating
it, carrying it, and pinning it in code.

**F-04's DENSITY CLAIM IS FALSE ON ITS OWN NUMBERS (PR-402, HIGH).** "The four highest-density
sections are all in" - computing density from the plan's own size percentages and hit counts, the top
four are `Detailed Implementation Checklist` (0.64), `Approval and execution gate` (0.39, EXCLUDED),
`Scope check` (0.36) and `Required tests / validation` (0.32). The excluded section ranks SECOND. The
allowlist is still defensible, but on CONTENT rather than on density, and a reviewer checking the
arithmetic would have found the plan asserting something its own table refutes.

**THE HAZARD METRIC IS 45% NEGATIONS, WHICH REORDERS THE RANKING (PR-403, MEDIUM).** 22 of the 49
allowlisted raw matches are sentences of the form "This orchestrator authors NO code; the children carry
the work" - the OPPOSITE of a hazard, matching only because the pattern keys on `authors`. The
contamination is uneven and therefore changes the ranking rather than just the magnitudes: `Detailed
Implementation Checklist` drops 0.63 -> 0.15 net and `Scope check` 0.36 -> 0.10, while `Required tests /
validation` barely moves (0.32 -> 0.30) and becomes the highest-NET section. Every count in the plan now
carries the qualifier.

**F-10's METHODOLOGY IS UNSTATED AND DECIDES THE ANSWER (PR-404, MEDIUM).** "Over the 61 executed
orchestrators that have an `approved` revision, comparing that revision to the final one" does not say
WHICH approved revision. Taking the OLDEST gives 16 narrow movers and 16 widened; taking the NEWEST
gives 2 and 3. I got 16/16 first and briefly believed the plan had asserted something false; it had not,
and the newest-approved reading is the correct one for this question, but an unlabelled number in a
docstring V-05 requires re-measuring is unreproducible by design.

Two further items. The gate was missing four elements the workflow's Step 4 requires (PR-405): a scope
fence as a DECLARATION with the make-and-justify disposition, the shared-checkout staged-set
verification, the inherited-release-gate statement, and conditional runner-versus-executor finalize
ownership. And OQ-02 set itself a falsification test it never ran (PR-406); I ran it over all 16
candidate orchestrators and the answer HELD, which is worth recording because the resolution was
correct while its stated reasoning ("near-zero distinguishing signal") was not.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-401 | HIGH | UNDER-SCOPE | A. Correctness / D. Anti-regression (undeclared blind spot in a safety gate) | E-01 as authored: "excluding every indented line leaves exactly the complement"; `runner_shared.e_item_action_blocks` terminates on `not stripped` (blank), `raw.startswith("- [")`, `raw.startswith("#")`, `_lint._SUBFIELD_RE.match(raw)`, and `not raw[:1].isspace()`; measured over 66 orchestrators: 827 indented non-sub-field lines reach neither extractor, 476 (73,276 chars) inside allowlisted sections, 14 matching the plan's hazard pattern; `yeh7gc` `## Cross-IPD validation` contains the indented line "MUST BE FLAGGED (parent-only work no child covers)", present in the file and ABSENT from that section's extracted prose while its non-indented bullets are present | **THE DISJOINTNESS ARGUMENT CLAIMS A COMPLEMENT IT DOES NOT HAVE, AND THE UNCOVERED SET CONTAINS THE SHARPEST HAZARD SENTENCE IN THE CORPUS.** `e_item_action_blocks` stops at the first blank line or sub-field, so "skip every indented line" excludes strictly more than that function captures. The disjointness property the plan needs still holds; what is false is the completeness implied by "exactly the complement", and the consequence is a 476-line blind spot inside the very sections being allowlisted. An orchestrator can state parent-only work in an indented line under `## Cross-IPD validation` and this change still will not send it - which is the same defect class `rmcqw8` was filed for. Left unstated, it would be filed under `executed/` as closed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now states the false claim, the correction, and the measured residue with the `yeh7gc` instance; its Expected outcome makes DISJOINTNESS the bar and requires the residue be re-measured and STATED, not treated as a failure. New finding F-16 enumerates both residues (83 non-allowlisted matches, 476 indented lines). A new `## Deferred` row carries the gap with `- Carrier: 168p5j`, citing the collision with `qurgra`'s concurrent re-homing of the termination rule as why it is not fixed here. E-04 gains an ELEVENTH pin, c3, a named synthetic-fixture limit test in the DEFAULT suite whose failure message says the gap was closed and F-16 needs updating - the shape of the deleted `TheExcerptHasAKnownLIMIT`, so the limit lives in code rather than only in a plan. V-01 requires the residual measurement as a POSITIVE output; the Goal now says "MOST, NOT ALL" and explains why. |
| PR-402 | HIGH | IN-SCOPE | F. Honest documentation / G. executability (a claim its own table refutes) | F-04 as authored: "The four highest-density sections are all in", beside its own figures `Detailed Impl Checklist` 16.4%/17, `Required tests` 30.7%/16, `Scope check` 18.9%/11, `Cross-IPD` 51.6%/4, `Completion criteria` 50.1%/1, and F-05's `Approval and execution gate` 87.9%/55; density computed from those numbers against the 162,373-char denominator: 0.64 IN, 0.39 OUT, 0.36 IN, 0.32 IN | **THE ALLOWLIST'S HEADLINE JUSTIFICATION IS ARITHMETICALLY FALSE ON THE PLAN'S OWN DATA.** The second-highest-density section is the one the plan EXCLUDES. The allowlist choice is still right, but it does not rest on density, and the plan told a reviewer to "dispute the choice against those numbers" while stating a summary those numbers contradict - which converts an invited check into a trap. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 now carries the review-measured size/raw/NET/churn table, states the correction explicitly with the actual raw-density ranking including the excluded section at second place, and replaces the false summary with the narrower true one: the highest-NET section is in, `Approval and execution gate` is excluded on the F-05 CONTENT analysis rather than on density, `Cross-IPD validation` and `Completion criteria` are in on `r07vma` 3a.1 spec grounds despite near-zero density, and `Goal` plus `Validation and cross-check` are in as zero-hit context. F-05 restates the gate exclusion as "the SECOND highest raw density, so this exclusion is the one that most needs its reason". |
| PR-403 | MEDIUM | IN-SCOPE | E. Testing / F. Honest documentation (proxy metric presented as measurement) | Measured over allowlisted prose in all 66 orchestrators: 22 of 49 raw matches (45%) are negations - `3b4f8u`, `s65hhv`, `rldro6`, `ryvoi5`, `88h0h8`, `yt93ir`, `r7xku3`, `dh5gnl`, `u5vyye`, `e6h1p3`, `5e4sb6`, `c2tvmm` all read "This orchestrator authors NO code/product code; the children carry the work"; NET density recomputed: `Detailed Impl Checklist` 0.63 -> 0.15, `Scope check` 0.36 -> 0.10, `Required tests` 0.32 -> 0.30 | **THE HAZARD PATTERN COUNTS THE SAFE CONDITION AS A HAZARD, AND UNEVENLY ENOUGH TO CHANGE THE RANKING.** The regex keys on `authors`, so the standard orchestrator scope-fence sentence matches. This does not weaken the case for widening, but it means F-03's 49 and F-04's per-section hits are UPPER BOUNDS on obligations rather than counts of them, and the section the plan ranks first on raw density is not first on net. A reader re-deriving these numbers and reading the matched sentences would conclude the metric was never inspected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New finding F-14 quantifies the contamination, names the direction, and states that no count in the plan may be cited as a hazard count without the NET qualifier. F-03, F-04 and F-05 all now point at it; F-03 additionally distinguishes the all-prose figure (54 files / 132 matches) from the allowlisted one (35 / 49) and labels the latter an upper bound. E-05 must state the caveat wherever the docstring cites a hit count, and V-05 must paste NET-versus-raw figures. |
| PR-404 | MEDIUM | IN-SCOPE | E. Testing (unreproducible measurement) / F. Honest documentation | F-10 as authored: "Over the 61 executed orchestrators that have an `approved` revision in git history, comparing that revision to the final one"; measured both readings at review - OLDEST approved revision: 16 narrow movers, 16 widened; NEWEST approved revision: 2 narrow (`jwbo2u`, `pp6y76`), 3 widened (those plus `wfjsp4`), matching the plan | **THE LOAD-BEARING "ONE EXTRA RE-PROBE" NUMBER CANNOT BE REPRODUCED FROM THE STATED METHOD, AND THE OTHER READING GIVES 16.** Most of these plans were approved, revised, and re-approved, so "the approved revision" is ambiguous and the ambiguity is worth a factor of five. I computed 16/16 first and briefly recorded the finding as unreproducible before testing the second reading. V-05 requires this number re-measured at execution, so an executor hitting the same ambiguity would either report a false mismatch or silently pick the flattering reading. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 now states the methodology as newest-approved-versus-final following renames, gives the oldest-approved alternative with its 16/16 result, explains why newest-approved is correct for this question (a verdict is keyed against the text as dispatched, not at first approval), and notes that the DELTA - widened minus narrow, which is 1 either way - is what the thrashing objection actually turns on. E-05 must record the methodology beside the number; V-05 must state which one produced its figures. |
| PR-405 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | Gate as authored: `aw ipd begin`, `aw commit` path-scoping, no-push, no-tag, no `git add -A`, bare pytest and the pre-transition condition all PRESENT; ABSENT: any out-of-scope-edit disposition, the `git diff --cached --name-only` shared-checkout verification, a statement of the inherited release gate, and conditional finalize ownership; workflow Step 4 and the 2026-09-01 scope-fence ruling | The gate covered the honesty and commit-safety rules but not four required elements. Conditional finalize ownership matters most in practice: an unconditional `aw ipd finalize` instruction makes an executor under `aw oc run` double-finalize, and the plan said only "do not move this plan" without naming who transitions it or forbidding a hand-rolled `git mv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gains a DECLARATION-style scope fence with the make-and-justify disposition (naming `--scope-reason`/`--scope-ack` and the two defensively-declared test files expected to need an ack), the shared-checkout staged-set verification with the re-verify-after-failed-commit rule, the release-gate statement (`From-Backlog: rmcqw8`, inherits none because that item is `Work-Kind: followup`), and conditional runner-versus-executor finalize ownership forbidding a hand-rolled `git mv`. Also added: a four-item "what the human is approving" summary and the three silent-failure modes (group B as tautology, an unrendered payload key, and the residual gap being lost). No "STOP and report" wording was introduced for the scope case; the stop directive is scoped to a genuinely unsafe condition. |
| PR-406 | LOW | IN-SCOPE | F. Honest documentation (an unrun self-test) / E. Testing | OQ-02 as authored resolved to EXCLUDE on the grounds that the 55 hits are "template boilerplate ... spread across 34 plans" with "near-zero distinguishing signal", and invited a disputant to "point at a specific orchestrator whose parent-only work is stated ONLY there"; that test was not run at authoring. Run at review: 16 orchestrators have hazard hits ONLY in that section, all 16 read, all boilerplate | OQ-02's ANSWER is correct and its stated REASONING was not verified and is partly wrong. The section is the second-highest raw density, not a near-zero-signal one, so the resolution rested on a characterization ("boilerplate") that nobody had checked against the sentences, while the density claim supporting it was false (PR-402). A resolved question whose basis is unverified is the pattern the workflow's HOW-question rule exists to catch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 now records that its own falsification test WAS RUN at review, names the 16-orchestrator candidate set, and reports the three boilerplate forms found with counts and example ids (12 scope-fence negations, 4 verbatim approval-template lines, the rest terminal-transition recital). It records both corrections to the authoring rationale (second-highest density, not near-zero; 88.1% not 87.9%) and states the ground as CONTENT rather than density. The disputant's bar is raised to naming an orchestrator OUTSIDE that set of 16. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-401: the indented-line gap is real and inside allowlisted sections. Fix it in this plan by widening the extractor, REPLAN the approach, or declare-carry-and-pin it? | DECLARE, CARRY (`- Carrier: 168p5j`), AND PIN IN CODE via a new c3 test. Do not widen the extractor here. | (a) Widen the extractor to include indented lines: rejected on mechanism, not on effort. Disjointness with `e_item_action_blocks` is the invariant that stops the two payload keys double-sending, and including indented lines would require changing that function's TERMINATION RULE - the shipped rule `m7gvuz` landed, which pending plan `qurgra` is concurrently re-homing into `ipd_lint.leaf_action_blocks`. One edit across two extractors with different invariants, colliding with a live plan, is how a safety gate gets broken. (b) REPLAN: rejected, the plan's core mechanism (one payload builder, key and excerpt widen together) is correct and is what the backlog item asked for; the gap is an additive limit, not a design fault. (c) Declare in prose only: rejected as insufficient, because F-02 measures exactly what that costs - the previous limit was pinned by a test, the test was deleted, and the limit vanished. | Read `e_item_action_blocks`' five termination conditions at the symbol; measured the uncovered set (827 / 476 / 14) over all 66 orchestrators; confirmed the `yeh7gc` instance present-in-file and absent-from-prose; `qurgra` confirmed pending with `- Set: 168p5j` and the termination rule in its scope; F-02's deletion confirmed at commit `19313eed`. | yes |
| D-2 | PR-402/PR-403: F-04's density summary is false and the metric is 45% negations. Correct the numbers, delete the density argument, or restate it on NET density with the correction recorded? | RESTATE ON NET DENSITY, keeping the raw figures and RECORDING the false claim as corrected rather than quietly replacing it. | (a) Silently fix the sentence: rejected. The plan invited reviewers to dispute the allowlist against those numbers, so a future reader comparing an earlier revision would find the claim changed with no note; recording the correction is what makes the invitation honest. (b) Delete the density argument entirely and rest the allowlist on the spec requirement alone: rejected, that would leave four of the seven sections unjustified, since only `Cross-IPD validation` and `Completion criteria` have spec grounds. (c) Just append the NET column: rejected as insufficient, because the FALSE summary sentence would survive beside corrected data. | Recomputed density from the plan's own F-04/F-05 figures (0.64 IN, 0.39 OUT, 0.36 IN, 0.32 IN); classified all 49 allowlisted matches by reading the enclosing sentence, finding 22 negations; recomputed NET density per section; the workflow's live-artifact convention (state the property, require re-derivation, keep the count as context). | yes |
| D-3 | PR-404: which approved-revision methodology is correct for the standing re-probe cost? | NEWEST approved revision versus final, with the oldest-approved result (16/16) recorded beside it and the reason stated. | (a) Oldest approved: rejected on meaning. A cached verdict is keyed against the text AS DISPATCHED; the oldest-approved text predates revisions unrelated to this change, so its 16 movers measure plan churn rather than cache churn. (b) Drop the number and state only the delta: rejected, the absolute is what answers "will this thrash", and a delta with no base is not checkable. | Computed both readings over the 61 executed orchestrators that have an approved revision (63 executed, 2 without); the widened-minus-narrow delta is 1 under BOTH readings, which is the figure the objection turns on, so the choice changes the presentation and not the conclusion. | yes |
| D-4 | Does the ONE-TIME cache invalidation need maintainer escalation as an irreversible act? | NO. It is reversible in the only sense that matters and its immediate blast radius is zero model calls. | Escalate as a `- Blocking: yes` question: rejected. The store is machine-local and gitignored (`probe_verdict_store_path` routes through `ipd_lifecycle.checkout_control_root` into `state/runtime/`, which `install_wizard` REFUSES to track); a miss reads `unknown` and PROBES rather than passing, so the failure direction is safe; `queued_orchestrator_targets` scopes cost to the run's QUEUE and there are ZERO pending orchestrators; and 0 of the 26 entries would key a live orchestrator after the change versus 9 before, so nothing usable is destroyed that was not already going stale. | Read `probe_verdict_store_path`, `_read_probe_verdict_store` and `queued_orchestrator_targets` at the symbol; measured the store (26 entries, 15 pass / 11 fail, 9 live-narrow, 0 live-widened) and the pending-orchestrator count (0). | yes |
| D-5 | The plan amends an APPROVED spec (`25kzda` 2.5b) and notes a second (`r07vma`). Approve that here, or require a separate spec-review first? | APPROVE IT HERE. | Split the spec amendment into its own artifact: rejected. The repository contract states a plan changing behavior a spec describes SHOULD carry the amendment in the same change and MUST declare the file in `- Scope-Paths:`, which this plan does for both. Splitting would guarantee the drift the contract exists to prevent. | AGENTS.md "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"; both spec paths present in `- Scope-Paths:`; verified verbatim that `25kzda` line 415-418 states the two-input key this change falsifies, that `r07vma` 3a limit 1 is NOT falsified (it assigns the residue to the probe, which this change makes true rather than aspirational), and that `77tr3o` R-12 states no key so needs no edit. | yes |
| D-6 | PR-406: OQ-02 was resolved without running its own falsification test. Run it, or leave the resolution resting on the authored characterization? | RUN IT. Resolution unchanged, reasoning corrected. | Accept the resolution as-is: rejected. The workflow's HOW-question rule requires a mechanism choice to cite a demonstration, and "these 55 hits are boilerplate" is a checkable claim that nobody had checked - while the density sentence supporting it was independently false (PR-402), which is exactly the pairing that should prompt verification rather than trust. | Enumerated the 16 orchestrators whose hazard hits fall only in `Approval and execution gate`, read every one, and classified all 55 gate matches: 12 scope-fence negations ("this orchestrator authors no code"), 4 verbatim "This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution", remainder terminal-transition recital. No parent-only deliverable in any of them. | yes |

No `Reversible: no` decision was taken in this round (D-1 and D-4 are the closest candidates and each
records why it is not one), so no escalation under Step 3.1 is owed. Every finding is `FIXED`; none was
deferred or left open, so no `- Blocking: yes` escalation under Step 4 is owed either. The plan's two
open questions were both already `resolved` at authoring and both remain resolved, OQ-02 with its
reasoning corrected and its self-test actually performed (D-6), so the plan carries no open question.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0` BEFORE any
  edit. `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`,
  `"findings":0` after all edits.
- `check_engine.evaluate_durable_carrier(Path("."), plan_path=..., plan_text=...)` -> `drifts: 0` both
  before and after revision (the plan already carried `Carrier-Declined:`/`Carrier:` on every deferred
  row and resolved both questions). `aw check` -> 2 repository errors, NEITHER naming this plan or Set.
- Suite baseline measured BARE: `2935 passed, 2 skipped, 3 warnings in 43.28s` (201 deselected as
  `slow`/`livecorpus`). No code, test, configuration or spec file was modified by this review.
- **F-01 confirmed at the symbol.** `probe_cache_payload` returns exactly `{"e_items",
  "child_table_rows"}`; `orchestrator_probe_excerpt` renders those two and nothing else, under the
  literal headings `### Checklist item action text` and `### Child IPDs table (row cells, in document
  order)`, and hand-reads `payload.get("e_items")` / `payload.get("child_table_rows")` so a future key
  would be hashed and never sent - which is E-03's stated concern, verified.
- **F-02 confirmed.** Both test files absent at HEAD; `git log --diff-filter=D` names `19313eed`
  (2026-09-24, "test: trim test suite from 9,136 to under 2,000 tests"); `git show 19313eed^` gives
  3022 and 1615 lines and contains `class TheExcerptHasAKnownLIMIT` at line 1270. `grep` for
  `probe_cache_payload|probe_cache_digest|e_item_action_blocks` across `tests/*.py` -> ZERO hits, so no
  surviving test pins the payload's key set.
- **F-03 re-derived, and SPLIT.** 66 plans carry `- Kind: orchestrator` (63 `executed/`, 3
  `superseded/`, 0 elsewhere), kind read from each plan's own first `- Kind:` bullet. Hazard pattern
  over ALL unattached prose: 54 files / 132 matches. Over the seven allowlisted sections: 35 / 49,
  matching the plan. The plan reported only the second pair, which understates the total gap while
  overstating how much this change closes; both are now stated.
- **F-04 re-measured per section** (size% of the 162,373-char current excerpt / raw / NET / churn over
  61 lifecycles): `Workflow history` 132.7 / 13 / 11 / 61, `Child IPDs prose` 90.5 / 5 / 5, `Approval
  and execution gate` 88.1 / 55 / 41, `Cross-IPD validation` 51.6 / 4 / 4, `Completion criteria` 50.1 /
  1 / 1, `Open questions` 49.7 / 4 / 4, `Required tests / validation` 30.7 / 16 / 15, `Goal` 21.9 / 0 /
  0, `Scope check` 18.9 / 11 / 3, `Detailed Impl Checklist` 16.5 / 17 / 4, `Validation and cross-check`
  5.9 / 0 / 0.
- **F-06 REPRODUCED EXACTLY, the load-bearing one.** Simulated conforming-execution edits over all 66:
  checkbox tick `applicable=26 widened_moved=0 narrow_moved=0`; filled `Observed evidence` 26/0/0;
  appended history line 66/0/0; `Execution state: performed` 26/0/0; `Result: pass` 26/0/0; ALL FIVE
  composed 66/0/0. So the widening does not re-open `xmqv5l`, and the narrow digest is unmoved by the
  same six, meaning the property is PRESERVED rather than newly claimed.
- **F-07 REPRODUCED EXACTLY.** Hazard sentence inserted into `## Cross-IPD validation`:
  `widened_moved=66 narrow_moved=0` of 66. Into `## Goal`: 66 / 0. Into `## Open questions`: 0 / 0.
  Into `## Deferred / out of scope`: 0 / 0.
- **F-08 REPRODUCED, and extended.** Zero extracted prose lines over 40 characters appear inside any
  `e_items` block, across all 66. Additionally verified the new key does not double-send the OTHER
  existing key: zero child-table cell strings over 25 characters appear in the extracted prose. Also
  checked and found clean: zero orchestrators have duplicate `## ` headings (so a title-keyed mapping
  cannot silently collide), and V-item text plus continuations carry ZERO hazard matches (so the
  E-only scope of `e_item_action_blocks` is not hiding a validation-side gap).
- **F-09 REPRODUCED EXACTLY.** Store read through `runner_shared.probe_verdict_store_path` (which
  resolves to the CHECKOUT's `.aw/state/runtime/`, not the lane's, confirming the `dh0uno` routing):
  26 entries, `Counter({'pass': 15, 'fail': 11})`. Entries keying a live orchestrator: 9 narrow, 0
  widened. Pending orchestrators: 0.
- **F-10 re-measured BOTH WAYS (PR-404).** 63 executed orchestrators, 61 with an `approved` revision.
  Newest-approved versus final: narrow moved 2 (`jwbo2u`, `pp6y76`), widened moved 3 (plus `wfjsp4`) -
  matching the plan. Oldest-approved versus final: 16 and 16.
- **F-11 REPRODUCED to within rounding.** Current excerpt median 2,217 / max 10,423 / total 162,373.
  Widened median 6,561 / max 19,074 / total 480,194, +195.7% (plan states 6,560 / 19,072 / 479,968 /
  +195.6%).
- **F-12 REPRODUCED.** `python3 -m pytest tests/test_orchestrator_shape_gate.py
  tests/test_orchestrator_shape_composed.py -o addopts="" -q` -> `20 passed in 1.32s`. Both assertions
  read at the symbol and confirmed satisfied by a widened excerpt (one asserts a continuation line IS
  present, the other that a `- Context:` sub-field is NOT; widening only adds and sub-fields stay out).
- **F-13 REPRODUCED verbatim.** `25kzda` states "CACHED against a digest of only what the answer
  depends on (the orchestrator's checklist item action text and its child table's row cells)" followed
  by the "Ticking a checkbox ... MUST NOT re-probe" sentence the plan correctly leaves untouched.
  `engine.py` holds "The verdict is CACHED on the parent's item text plus its child table" inside the
  managed `pointer` section, and the identical sentence appears in the generated `AGENTS.md`.
  `77tr3o` R-12 confirmed to state no key.
- **PR-401 measured** as described in the findings table: 827 / 476 / 73,276 / 14, with the 14 broken
  down by enclosing H2 (8 `Open questions`, 2 `Workflow history`, 1 `Cross-IPD validation`, 1
  `Deferred`, 1 pre-H2) and the `yeh7gc` instance shown present-in-file and absent-from-prose.
- **PR-403 measured** by classifying all 49 allowlisted matches on their enclosing sentence: 22
  negations, 27 other. NET density recomputed per section.
- **PR-406 measured** by enumerating and reading all 16 orchestrators whose hits fall only in the gate
  section, and classifying all 55 gate matches into the three boilerplate forms.
- **F-15 (new) measured** against the prompt's OWN trigger vocabulary, read from
  `PROBE_PROMPT_TEMPLATE`: 37 of 66 orchestrators would newly send text matching a positive trigger
  where their current payload matches none (10 already do), concentrated in `Required tests /
  validation` (37 files), `Completion criteria` (19), `Detailed Impl Checklist` (10), `Cross-IPD
  validation` (3), `Scope check` (2). In the opposite direction, 30 of 66 would newly send an explicit
  "this orchestrator authors NO code" sentence that 0 of 66 currently send.
- **Scope claims spot-checked.** `queued_orchestrator_targets` builds `ProbeTarget`s and names no
  payload key, supporting the plan's claim that neither host runner module needs editing. The
  `livecorpus` marker is already registered in `pyproject.toml` and already excluded by `addopts =
  "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, so E-04 adds no marker declaration;
  the plan's under-scope paragraph now says so.
- **`ipd_schema` heading constants confirmed present** for all seven allowlisted titles: `H_GOAL`,
  `H_EXECUTION`, `H_REQUIRED_TESTS`, `H_CROSS_IPD`, `H_COMPLETION`, `H_VALIDATION_ORCH`,
  `H_SCOPE_CHECK`, so E-02's "no literal strings" requirement is satisfiable as written.
- Every probe ran in-process against in-memory strings or via `git show`; no repository file was
  written by a probe, no receipt was created or deleted, and the verdict store was opened READ-ONLY.
  `git status --short` reports only the plan and this record.
