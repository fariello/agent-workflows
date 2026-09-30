# IPD: Document the resume-subcommand verification flag asymmetry in docs/runner-profiles.md

- Date: 2026-09-30
- Kind: child
- Concern: `docs/runner-profiles.md` is the operator-facing reference for the verification flag surface, and its "BOTH HOSTS HONOR THIS CHAIN" paragraph is silent on the `resume` subcommand while making two inaccurate claims about `start`.
- Scope: Correct and extend one paragraph of `docs/runner-profiles.md`, plus one row of its troubleshooting table. Operator-facing prose only. No behavior, no code, no test, and no spec is changed.
- Scope-Paths: docs/runner-profiles.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: d8o2cv
- Set: d8o2cv
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: gyd8sq

## Workflow history

- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `d8o2cv`, graduating it. Every load-bearing claim re-measured at this HEAD by driving both parsers over all 24 (host, subcommand, spelling) cells; see Findings.

## Goal

Make `docs/runner-profiles.md` tell an operator the truth about the verification flag surface: that the `resume` subcommand differs per host and that an Antigravity run's verification posture cannot be changed on resume at all, and that a contradictory flag pair is refused on Antigravity but silently resolved by last-wins on opencode. The spec half of this work is already shipped (spec `25kzda` Section 2.1c, added by executed plan `7dz3wv`); this plan is the operator-facing half, deliberately separate because user-facing prose has a different audience and review standard than a normative spec section.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: correct the two inaccurate claims already in the paragraph

- [ ] E-01 In the "BOTH HOSTS HONOR THIS CHAIN" paragraph of `docs/runner-profiles.md`, correct the lead-in clause "The flags differ only in spelling", which understates a per-host EXISTENCE difference as a mere naming difference. Measured (F-03): `--verify` and `--audit` are not registered on `aw agy run start` at all and exit 2 with `unrecognized arguments`, so an operator who reads "only in spelling" and reaches for `aw agy run --verify` gets a usage error rather than the alias the sentence implies. Reword the lead-in to say the two hosts accept DIFFERENT SETS of spellings, keeping the existing enumeration that follows it (which is itself accurate about which spellings each host accepts) substantially intact rather than rewriting it. Do NOT change the first two sentences of the paragraph ("BOTH HOSTS HONOR THIS CHAIN" and the stored-per-model-choice sentence): the tri-state resolution chain they describe genuinely is host-neutral and remains correct.
  - Depends on: none
  - Expected outcome: The paragraph no longer claims the per-host difference is confined to spelling, and a reader can tell that `--verify` and `--audit` exist on opencode only.
  - Execution state: pending

- [ ] E-02 In the same paragraph, correct the affirmatively FALSE host-unqualified sentence "Passing a contradictory pair such as `--no-verify --validate` is refused before the run starts rather than resolved by precedence, because either winner would be a verification decision you did not make." Measured (F-04): that is true on antigravity and FALSE on opencode, where the pair parses silently and is resolved by argparse last-wins, so `--no-verify --validate` yields `validate=True` and `--validate --no-verify` yields `validate=False`. Host-qualify the sentence so the refusal is attributed to antigravity and the opencode behavior is stated as the order-dependent last-wins it actually is, preserving the existing "a verification decision you did not make" rationale as the reason the antigravity refusal exists. THIS SENTENCE IS COUPLED TO PENDING PLAN `zdgc6t` and the coupling must be honored rather than discovered later: that plan's E-04 makes opencode refuse the pair too, which would make this corrected sentence stale in the opposite direction. See DECISION-01 and OQ-01 for why the correction is still made now rather than deferred, and do not silently resolve that coupling differently at execution time.
  - Depends on: E-01
  - Expected outcome: The doc no longer promises an operator a refusal on a host that will silently honor the pair; each host's actual behavior is attributed to that host.
  - Execution state: pending

### Task group 2: fill the documented silence on resume

- [ ] E-03 Add to the same paragraph (or as a short labelled continuation of it, whichever reads better in place) the `resume` subcommand asymmetry the file is currently silent on, stating three measured facts and no more: (1) `aw oc run resume` accepts all six spellings and an explicit flag there overrides the frozen decision for the rest of the run; (2) `aw agy run resume` registers NONE of the six, so any of them exits 2 with `unrecognized arguments`; (3) the practical consequence is that an Antigravity run's verification posture is fixed when the run is created and cannot be changed on resume. Say WHY that asymmetry lands hardest on antigravity, because it is the non-obvious part: antigravity is the host that verifies BY DEFAULT (`runner_profiles.RUNNER_REGISTRY['agy'].validate_default` is `True`, against `False` for opencode, measured in F-05), so it is precisely the operator resuming a long antigravity run and wanting to SKIP the verifier turn who has no flag to reach for. Keep this to a few sentences: this file is an operator guide, and the exhaustive per-cell mapping already has a normative home in spec `25kzda` Section 2.1c, which this prose must not duplicate.
  - Depends on: E-02
  - Expected outcome: An operator reading the verification section learns that `resume` differs by host, which host refuses, and that an antigravity run's posture is frozen at creation.
  - Execution state: pending

- [ ] E-04 Add one row to the "When something is wrong" table in `docs/runner-profiles.md` covering a verification flag passed to `aw agy run resume`, so the exit-2 an operator actually hits is explained where they will look for it. Follow the shape of the adjacent shipped row "`--verify-with` passed to `resume` | Exit 2. The verifier launch is frozen at creation; omit the flag to use it, or start a new run.", which is exact precedent for documenting a frozen-at-creation refusal on resume in that table. The new row must name the outcome (exit 2, unrecognized arguments) and the operator's remedy (the posture is frozen at creation, so start a new run with the posture you want). Do NOT add a row for opencode resume: it accepts the flags, so there is nothing that goes wrong. VERIFY THE TABLE'S PREAMBLE STILL HOLDS before adding the row, and if it does not, report rather than weakening it: the preamble promises every listed situation "fails BEFORE the run has any durable side effect: no run id, no run directory, no partial state", and an argparse-level exit 2 on resume satisfies it only because parsing precedes any state write.
  - Depends on: E-03
  - Expected outcome: The troubleshooting table explains the exit 2 an operator gets from `aw agy run resume --no-verify`, with the remedy, and its no-durable-side-effect preamble remains true of every row including the new one.
  - Execution state: pending

## Project conventions discovered (Step 0)

- NO TEST MAY PIN THIS PROSE, and this is a hard prohibition rather than a preference. `AGENTS.md` states under "TEST OUTCOMES, NOT CODE STRUCTURE" that an author must "NEVER assert that specific text, docstrings, or comment banners remain unchanged in a script", and `GUIDING_PRINCIPLES` P16 is the governing principle. A test that greps `docs/runner-profiles.md` for a sentence is exactly that prohibited shape. This plan therefore ships NO test, and its validation is the pasted `git diff` plus DRIVEN evidence that each documented fact matches live behavior (the parser probe in F-02). The honest limit is stated in "Deferred / out of scope": the prose can rot without any test failing, and the durable guard against that is the behavioral pin on the 24 dest cells that already exists in the spec's test, not a prose assertion.
- USER-FACING PROSE MUST CONTAIN NO EM OR EN DASHES. `AGENTS.md` confines that rule to user-facing prose, and `docs/runner-profiles.md` is squarely inside it. Measured at this HEAD: the file currently contains zero of each, so the edit must not introduce the first one.
- A PLAN THAT CHANGES NO BEHAVIOR AMENDS NO SPEC. `AGENTS.md` requires a plan to declare every `.spec.md` it touches in `- Scope-Paths:`, and the converse discipline applies here: spec `25kzda` Section 2.1c is already correct and complete on the resume asymmetry, so it is deliberately NOT in `- Scope-Paths:` and must not be edited. See "Spec / documentation sync".
- CITE BY SYMBOL OR QUOTED STRING, NOT BY BARE LINE NUMBER: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this plan names a quoted sentence or a symbol for that reason.

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-01 | **THE ITEM'S CORE CLAIM REPRODUCES EXACTLY.** `docs/runner-profiles.md` documents the per-host spelling difference for `start` in its "BOTH HOSTS HONOR THIS CHAIN" paragraph and says nothing whatever about `resume`. | Read of the paragraph; grep of the whole file for `resume` returns hits only in the "Durability: a running run does not change under you" section (about frozen launch identity and `--verify-with`) and the one troubleshooting row for `--verify-with`, none of which mention a verification posture flag. |
| F-02 | **ALL 24 (host, subcommand, spelling) CELLS MEASURED AT THIS HEAD, matching spec `25kzda` Section 2.1c cell for cell.** opencode accepts all six spellings on BOTH `start` and `resume` (`--validate`/`--verify`/`--audit` to `validate=True`, the three negations to `False`). antigravity `start` accepts `--validate`/`--no-validate` to `validate`, accepts `--no-verify`/`--no-audit` to a separate `no_verify=True`, and exits 2 on `--verify` and `--audit`. antigravity `resume` exits 2 on ALL SIX. | Driven: `build_parser().parse_args()` for both `oc_runipd` and `agy_runipd` over the cross product of two subcommands and six spellings, printing `validate`, `no_verify`, or the `SystemExit` code. Confirmed end to end at the CLI: `aw agy run resume --no-verify <run>` exits 2 with `runagy: error: unrecognized arguments: --no-verify`. |
| F-03 | **"The flags differ only in spelling" UNDERSTATES AN EXISTENCE DIFFERENCE**, which is a second inaccuracy in the paragraph that the backlog item does not report. `--verify` and `--audit` are not registered on agy `start` at all, so they are not spelled differently there, they are absent. An operator trusting that clause and typing `aw agy run --verify` gets a usage error. | Driven: agy `start --verify` and `start --audit` both exit 2 (F-02 probe). Spec `25kzda` Section 2.1c records the same two cells as "*Unregistered* (`None`) ... Exits with return code 2". |
| F-04 | **THE PARAGRAPH MAKES AN AFFIRMATIVELY FALSE HOST-UNQUALIFIED CLAIM, independently recorded by an executed plan's review as F-14 and assigned to THIS item.** The sentence "Passing a contradictory pair such as `--no-verify --validate` is refused before the run starts rather than resolved by precedence" is true on agy and false on oc. | Driven: `oc_runipd.build_parser().parse_args(['start','--validate','--no-verify','x.ipd.md'])` yields `validate=False` and the reverse order yields `validate=True`, with no refusal; `hasattr(oc_runipd,'verification_flag_tristate')` is `False` while the agy attribute is `True`, so oc has no equivalent check. Executed plan `7dz3wv` records the identical measurement as its F-14 and its Scope check names `d8o2cv` as the carrier. |
| F-05 | **THE ASYMMETRY LANDS HARDEST ON THE HOST THAT VERIFIES BY DEFAULT**, which is what makes the silence worth fixing rather than merely incomplete. agy is the verify-by-default host, so the operator most likely to want a verification flag on resume is on the host that has none. | Driven: `runner_profiles.RUNNER_REGISTRY['agy'].validate_default` is `True` and `['oc'].validate_default` is `False`. The doc's own tri-state section already states this floor ("off on opencode and on on antigravity"), so the new prose is consistent with shipped text rather than introducing a new claim. |
| F-06 | **THE NORMATIVE HALF IS ALREADY SHIPPED AND PINNED, so this plan adds no new contract and needs no test of its own.** Spec `25kzda` Section 2.1c ("The verification flag surface is PER HOST") carries the 24-cell dest table and three "OPERATOR-VISIBLE CONSEQUENCES", whose consequence 3 states the resume asymmetry in full. It is pinned by a live passing test. | Read of Section 2.1c, added by executed plan `7dz3wv` per the spec's dated history note. Ran `python3 -m pytest tests/test_runner_shared.py -k VerificationDestAsymmetryPerHost`: `4 passed`. |
| F-07 | **THE TROUBLESHOOTING TABLE HAS EXACT PRECEDENT for documenting a frozen-at-creation resume refusal**, so E-04 follows a shipped shape rather than inventing one. The table already carries the row "`--verify-with` passed to `resume` \| Exit 2. The verifier launch is frozen at creation; omit the flag to use it, or start a new run." | Read of the "When something is wrong" table. The neighbouring "Durability" section states the governing reason in prose: "`resume` never re-resolves". |
| F-08 | **A PENDING PLAN COLLIDES WITH E-02 AND ASSERTS THE FILE NEEDS NO CHANGE.** Pending plan `zdgc6t` (`- Status: to-review`, `- From-Backlog: byazcp`, `- Blocks-Release: next`) makes oc refuse the contradictory pair on BOTH subcommands, which would make the currently-false sentence true. Its F-10 therefore records `docs/runner-profiles.md` as deliberately outside its `- Scope-Paths:` "because it needs no change", and names `d8o2cv` as the carrier for the remaining gap. Its E-03 confirms it leaves oc `resume`'s six spellings, `dest`, and `default=None` untouched. | Read of `zdgc6t` front matter, its E-03 and E-04 items, its F-10 row, and its "NO USER-FACING DOCUMENTATION CHANGE IS REQUIRED" paragraph in the spec-sync section. |
| F-09 | **THE RESUME PROSE (E-03) IS IMMUNE TO `zdgc6t`; ONLY E-02's SENTENCE IS COUPLED.** `zdgc6t` E-03 explicitly preserves oc resume's option-string list and `dest`, and nothing in it registers any spelling on agy `resume`. So "oc resume accepts all six, agy resume accepts none" stays true after `zdgc6t` executes, and the whole coupling reduces to the single contradictory-pair sentence. | Read of `zdgc6t` E-03 ("leave `dest`, the option-string list, and `default=None` exactly as they are") and E-05 (its only agy change is on `start`, wiring `verification_flag_tristate`). |

## Proposed changes (ordered, validatable)

1. Reword the paragraph's "differ only in spelling" lead-in to name a per-host difference in WHICH spellings exist (E-01, from F-03).
2. Host-qualify the contradictory-pair sentence so the refusal is attributed to antigravity and opencode's last-wins order-dependence is stated (E-02, from F-04).
3. State the `resume` asymmetry and its practical consequence for the verify-by-default host (E-03, from F-01, F-02, F-05).
4. Add one troubleshooting row for a verification flag on `aw agy run resume` (E-04, from F-02, F-07).

All four changes are confined to `docs/runner-profiles.md`. Nothing else in the repository is touched.

## Decisions taken while authoring

### DECISION-01: correct the coupled false sentence now rather than deferring it to `zdgc6t`

- Question: E-02's sentence is false today but pending plan `zdgc6t` would make it true, and `zdgc6t` F-10 asserts this file "needs no change" for that reason (F-08). Should this plan correct it now, or leave it?
- Options considered: (a) correct it now, accepting that `zdgc6t` will later need a second edit to this sentence; (b) leave it entirely to `zdgc6t`; (c) reword it into something vague enough to be true either way.
- Selected: (a), correct it now.
- Why: `zdgc6t` is `to-review`, not approved, so its execution is not guaranteed and may be revised; option (b) therefore leaves an affirmative falsehood in shipped operator documentation for an unbounded period, on the strength of a plan that may never run. The executed review that assigned this defect to `d8o2cv` made exactly this ranking, recording that "a wrong statement misleads an operator where a silence merely fails to help". Option (c) is rejected because deliberately vague prose about whether a command refuses is worse for an operator than either true statement. The cost of (a) is one later edit to one sentence, which is cheap and is now flagged in OQ-01 for whoever reviews `zdgc6t`.
- Reversibility: fully reversible; a single sentence in one documentation file, no behavior and no contract.
- Confidence: high
- Human review requested: yes, on the ordering only. If the maintainer prefers `zdgc6t` to own this sentence outright, drop E-02 and this plan still delivers E-01, E-03, and E-04, which are the item's actual subject and are entirely independent of `zdgc6t` (F-09).

## Deferred / out of scope (with reason)

- NO TEST IS ADDED, and the resulting exposure is stated rather than hidden: nothing will fail if this prose later drifts from behavior, because pinning documentation text is the prohibited code-structure shape (see "Project conventions discovered"). The behavioral facts themselves ARE guarded, by the 24-cell dest test that spec `25kzda` Section 2.1c cites and that passes at this HEAD (F-06), so a change to the flag surface breaks a test even though a change to this paragraph does not. Judged the correct trade rather than a gap to close.
  - Carrier-Declined: There is no outstanding work to carry, and creating a carrier for it would record an obligation the repository forbids discharging. `AGENTS.md` prohibits asserting "that specific text, docstrings, or comment banners remain unchanged", so a prose-pinning test must never be written by anyone; naming a carrier would park a permanently undischargeable task. The behavioral contract underneath the prose is already pinned by a live passing test (F-06).
- THE CODE ASYMMETRY IS NOT FIXED. This plan does not give agy `resume` the six spellings, and does not make oc refuse a contradictory pair. The first is a capability decision belonging to a code plan rather than a documentation one (and is not requested by the item, whose own text judges the current behavior "a clean exit 2, not a silent wrong answer"); the second is carried by pending plan `zdgc6t` (F-08).
  - Carrier: zdgc6t
- SPEC `25kzda` IS NOT AMENDED. Section 2.1c already states the resume asymmetry correctly and completely (F-06), so there is nothing to amend, and this plan changes no behavior that any spec describes.
  - Carrier-Evidence: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- `zdgc6t`'s F-10 ROW IS NOT EDITED. E-02 makes that row's claim ("the file already promises the behavior this plan implements") stale, but another plan's findings table is not this plan's to rewrite, and `zdgc6t` is under review where a reviewer can see OQ-01.
  - Carrier: zdgc6t

## Scope check

- Over-scope: none. `docs/runner-profiles.md` is the only file in `- Scope-Paths:` and every E-item edits it. E-01, E-02, and E-04 go beyond the backlog item's literal "SUGGESTED FIX" of one or two sentences about resume, but they are NOT opportunistic broadening: the executed review of `7dz3wv` assigned its F-14 (the false refusal claim) to carrier `d8o2cv` explicitly, and F-03's inaccuracy sits in the same clause of the same paragraph, so fixing it separately would mean two plans editing one paragraph.
- Under-scope: Three gaps are deliberately left, each recorded above with its carrier: the agy resume capability itself, oc's silent contradictory pair (`zdgc6t`), and the absence of any regression guard on this prose. After this plan, the operator documentation states the per-host `start` and `resume` surfaces accurately and the troubleshooting table explains the exit 2 an operator will actually hit.

## Required tests / validation

There is no code change, so there is no new unit test and none is permitted (see "Project conventions discovered"). Validation is by pasted diff plus DRIVEN behavioral evidence that every documented fact matches this HEAD, plus the repository-wide checks that govern a documentation edit:

- Re-run the 24-cell parser probe from F-02 and paste its output, so each documented cell is shown true at execution time rather than trusted from this plan's text.
- Run a FULL bare `python3 -m pytest` and paste the summary line, stating the measured baseline rather than matching any literal recorded here (a documentation-only change must not move it).
- Run `aw sanitize --agent` and paste the result, since the edited file is public operator documentation.
- Run `aw check` and paste the outcome.
- Confirm the edited file still contains zero em dashes and zero en dashes, by driven count and not by eye.
- Run `aw ipd lint --phase pre-transition` on this plan and paste the conforming result.

## Spec / documentation sync

THIS PLAN IS ITSELF THE DOCUMENTATION SYNC. It closes the operator-facing half of a gap whose normative half is already shipped: spec `25kzda` Section 2.1c declares the per-host verification flag contract for both `start` and `resume`, including the 24-cell dest table and the three operator-visible consequences, and was added by executed plan `7dz3wv` graduating backlog item `xdgorn`.

NO SPEC IS AMENDED, DELIBERATELY. Section 2.1c is already correct on every fact this plan documents (F-02 reproduces its table cell for cell), and this plan changes no behavior, so there is nothing for a spec to catch up with. `docs/runner-profiles.md` is therefore the only entry in `- Scope-Paths:`, and no `.spec.md` path appears there.

THE DIVISION OF LABOUR IS INTENTIONAL AND SHOULD BE PRESERVED: the spec carries the exhaustive per-cell mapping and the structural argument for why the asymmetry cannot be refactored away, while this file carries the few sentences an operator needs. E-03 must not import the table into the guide.

## Open questions

### OQ-01: should E-02's sentence be corrected here, or left to pending plan `zdgc6t`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Resolved from repository evidence in favour of correcting it here; see DECISION-01 for the full reasoning and the fallback. Recorded as a question rather than silently decided because it creates a known follow-on obligation for a plan this one does not own: if `zdgc6t` executes after this plan, its E-04 makes opencode refuse the pair, and whoever executes it must then update this same sentence again and should not be surprised by finding it host-qualified. Non-blocking because E-01, E-03, and E-04 are provably independent of `zdgc6t` (F-09), so this plan is executable and useful whichever way the ordering falls.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the `git diff` of `docs/runner-profiles.md` showing the "differ only in spelling" clause replaced by wording that names a difference in which spellings exist. Paste driven output showing agy `start --verify` and `start --audit` each exit 2, confirming the new wording is the true one. Paste the unchanged first two sentences of the paragraph to show the host-neutral resolution chain was not disturbed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the `git diff` hunk for the contradictory-pair sentence, showing the refusal attributed to antigravity and opencode's last-wins stated. Paste driven output for BOTH orders on BOTH hosts at this HEAD: oc `start --validate --no-verify` yielding `validate=False` and `start --no-verify --validate` yielding `validate=True` with no refusal, and the agy refusal still occurring, so the new sentence is shown true of shipped behavior rather than asserted. State explicitly in the evidence whether pending plan `zdgc6t` has executed as of this run, since that decides whether the sentence is correct as written or already superseded (F-08, OQ-01); if it HAS executed, STOP and report rather than writing prose this plan measured against a different HEAD.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the `git diff` hunk adding the resume prose. Paste the full 24-cell probe output from F-02 re-run at execution time, and check off against it each of the three documented facts: all six spellings accepted on oc `resume`, all six exiting 2 on agy `resume`, and the frozen-at-creation consequence. Paste driven `runner_profiles.RUNNER_REGISTRY['agy'].validate_default` and `['oc'].validate_default` to show the verify-by-default claim is true. Confirm by driven count that the added prose introduced no em dash and no en dash, and quote the sentence count to show the guide did not absorb the spec's table.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the `git diff` hunk adding the table row, and the rendered row text. Paste the end-to-end CLI evidence for the documented situation (`aw agy run resume --no-verify <run>` exiting 2 with the `unrecognized arguments` message), captured from the CLI and not only from `parse_args`. Demonstrate the table preamble still holds for the new row by showing no run directory or state file is created by that refused invocation. Then paste, from the same run: a FULL bare `python3 -m pytest` summary line with the measured baseline stated, `aw sanitize --agent`, `aw check`, and `aw ipd lint --phase pre-transition` on this plan reporting conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only `docs/runner-profiles.md`, through `aw commit <this plan> -- docs/runner-profiles.md`, never `git add -A` and never `git commit -a`, and never push. This is a shared checkout: do not revert, stage, or clean any change you did not make. When reporting tests, paste the ACTUAL runner output; do not claim a passing suite you did not run. Run the suite BARE as `python3 -m pytest`, with no added flags.

USER-FACING PROSE RULES APPLY TO EVERY WORD ADDED. The edited file is operator documentation, so the added prose must contain no em or en dashes, and must not leak any local path, username, or hostname. Run `aw sanitize --agent` before treating the edit as done.

DO NOT EXPAND THIS PLAN INTO A CODE CHANGE. If execution reveals that the documented behavior has changed since authoring (most plausibly because pending plan `zdgc6t` executed first, see F-08 and OQ-01), STOP and report rather than editing code to match the prose or writing prose that contradicts a re-measurement.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted evidence from a run that actually happened. The terminal transaction (workflow-history line, terminal `Status:`, `git mv`, path-scoped lifecycle commit) is a post-gate step and never a checklist item.
