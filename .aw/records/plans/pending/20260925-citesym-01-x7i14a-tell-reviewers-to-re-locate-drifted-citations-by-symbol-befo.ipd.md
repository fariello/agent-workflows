# IPD: Tell reviewers to re-locate drifted citations by symbol before calling them false

- Date: 2026-09-25
- Kind: child
- Concern: The review workflows (`plan-review`, `plan-review-long`, `spec-review`, `verify-execution`) mandate `path:line` evidence but never say what to do when a cited line no longer holds the cited construct, so reviewers decide per run whether line drift is a false claim or cosmetic. The AUTHORING half of backlog `yos8rq` already shipped (plan `mzc019`, spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`); the REVIEW half did not, and `mzc019` explicitly scoped it OUT ("any change to how REVIEWS cite code").
- Scope: IN: one disposition rule in the evidence step of each of the four review workflows (re-locate by symbol or quoted string; drift whose anchor resolves is at most LOW; an anchor that does not resolve is a real evidence finding), and a recommendation that the reviewer's OWN evidence cells carry a symbol beside `path:line`. The recommendation is applied to the `Evidence` field of ALL THREE workflows that declare one, not `plan-review` alone (F-6): `plan-review.md`'s `- **Evidence:** `path:line`.`, `plan-review-long/02-review-and-revise.md`'s `- Evidence: `path:line`.`, and `spec-review.md`'s `Evidence (`path:line`)`. OUT: changing the `path:line` format or the findings-table COLUMN (the table row placeholders stay as they are); any lint (the `hesb87` promotion decision owns that); the authoring rule (already in Section 10.2); retrofitting existing plans or reviews; `plan-review-long/report-template.md` and the four report-table rows, which are output FORMAT rather than evidence-gathering instructions.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/01-discover-and-snapshot.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/spec-review/spec-review.md, .aw/system/workflows/verify-execution/verify-execution.md
- Item-Dependencies: none
- Status: to-review
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: yos8rq
- Set: citesym
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: x7i14a

## Workflow history

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801..PR-807, all FIXED, no deferrals. ALL FIVE AUTHORED FINDINGS VERIFY: each of the four edit anchors exists verbatim at the quoted text, the `symbol` grep across all four workflow dirs returns only the two unrelated scope-fence sentences, `mzc019`'s Scope OUT says "any change to how REVIEWS cite code" word for word, `intent-audit.md` does say "inherited from `verify-execution.md`", and `pyproject.toml` force-includes `.aw/system` with no second source tree. THE MATERIAL FINDINGS ARE A PARITY GAP AND A TENSION WITH THE CITED AUTHORITY. (a) E-01 amends `plan-review.md`'s `Evidence` field but the two mirrors declare their own and were left alone, so the "carry a symbol" recommendation would ship on one of three findings tables; `02-review-and-revise.md` is now in Scope-Paths (PR-801). (b) The spec section this plan cites as its basis says, in terms, "REVIEW IS NOT THE REMEDY, which is why this is a contract rule rather than a reviewer instruction" - so the plan must position itself as a DISPOSITION rule for drift that has already happened, not as a verification remedy, or it contradicts its own authority (PR-802). (c) The plan's convention note about the stale `managed-sections.json` hash for `plan-review.md` is RIGHT but incomplete and slightly wrong in a way that matters: measured with the real `manifest.hash_content` normalization, `plan-review.md` and `verify-execution.md` are already stale, `spec-review.md` is NOT TRACKED AT ALL, and `01-discover-and-snapshot.md` currently MATCHES - so E-02 would introduce a NEW mismatch, whose consequence is that `aw uninstall` classifies the file as user-drifted and PRESERVES it (PR-803). Also: `spec-review.md` has a live per-line prohibition scan that an added sentence can trip (PR-804); the backlog names sites the plan silently drops without saying why (PR-805); OQ-01 owed a typed carrier and `aw check plans` reports an `error` on this plan today (PR-806); and the gate was one sentence (PR-807).
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog yos8rq; re-measured that the authoring rule shipped via mzc019 (spec Section 10.2, IPD-C801, scaffold guidance) while grep over the four review workflows finds no re-locate or drift disposition beside any "Verify material claims with `path:line`" step, so only the review half remains.

## Goal

Give every reviewer the same rule for a stale line citation, so drift stops producing inconsistent findings or wasted revision rounds, and make reviewers' own evidence survive drift.

WHAT THIS IS NOT, stated because the spec section this plan builds on rules it out explicitly. Spec `ipd-structure-and-linting` Section 10.2 says "REVIEW IS NOT THE REMEDY, which is why this is a contract rule rather than a reviewer instruction", and records that plan `216rgg` was reviewed twice with every line number measured at HEAD and still drifted. So this plan does NOT claim to prevent drift or to make review the remedy for it; the authoring rule (a) symbol / (b) quoted string / (c) line appended, already shipped by `mzc019`, is the prevention. What is missing and what this plan adds is the DISPOSITION for drift that has already happened by the time a reviewer reads it: a rule for what a stale line MEANS, so two reviewers reach the same verdict instead of each re-deriving it. That is a genuinely different question from prevention, and it is the one Section 10.2 leaves to the reader ("the correct posture toward an older plan's offset is to treat it as a HINT and locate the construct by symbol") without telling any reviewer where to find it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the rule, once per review workflow

- [ ] E-01 In `.aw/system/workflows/plan-review/plan-review.md`, section "## Step 1: Evidence and pre-review snapshot", replace item "4. Verify material claims with `path:line` evidence." with a two-part item: (a) verify by locating the cited construct by its SYMBOL or quoted string, treating the line number as a hint (spec `ipd-structure-and-linting` Section 10.2 states the same posture for authors and, for an older plan's offset, for readers); (b) disposition: anchor resolves and only the line moved = no finding, or at most one LOW batched finding per plan noting the drift; anchor does not resolve anywhere, or resolves to something that contradicts the claim = a real evidence finding at the severity of the claim it supports; a bare `path:line` with no anchor that no longer matches = search for the described construct before judging, and record which case applied.
  SAY WHICH DIRECTION IS THE COSTLIER ERROR, and cite the measured case. The disposition must state plainly that rejecting a citation the reviewer merely failed to re-locate is WORSE than under-reporting drift, because a review finding is durable and tracked while the drift is not. Measured, in this repository: backlog `88manw` (`Work-Kind: bug`, `Blocks-Release: next`, still `open`) records that plan `si24ia`'s review finding PR-305 "rejected a correct spec section citation and substituted a wrong one" - the plan cited spec section 2.1, the review declared that wrong and named 1.1 plus a line number, and the plan was right. A rule that only warns about stale lines, without naming that failure direction, does not address the one case the repository has actually measured. Note also that this is the CITED-CONSTRUCT-NOT-FOUND case in a spec rather than in code, so the rule must cover a section or heading anchor, not only a code symbol.
  - Depends on: none
  - Expected outcome: the Step 1 item carries the rule including the costlier-error direction and the `88manw` citation; no other line changes in this item.
  - Execution state: pending

- [ ] E-02 Apply the reviewer's-own-evidence recommendation to the `Evidence` field of ALL THREE workflows that declare one, which is the parity half E-01 originally carried alone (F-6). Append "plus the symbol or a quoted string, for example the symbol `mod.func_name` beside its path and line" (or equivalent wording, identical across the three) to: `plan-review.md`'s `- **Evidence:** `path:line`.`; `plan-review-long/02-review-and-revise.md`'s `- Evidence: `path:line`.`; and `spec-review.md`'s clause `Evidence (`path:line`)` in the "Classify each with Severity, Scope, Area, Evidence" sentence. Do NOT touch the findings-TABLE rows or `report-template.md`: those are output format, and `<path:line>` in a table placeholder is a column label rather than an instruction (see Scope OUT).
  - Depends on: E-01
  - Expected outcome: the three Evidence-field declarations carry the same recommendation; no table row or template changes.
  - Execution state: pending

- [ ] E-03 Mirror E-01's rule in `.aw/system/workflows/plan-review-long/01-discover-and-snapshot.md` item "4. Verify material claims with `path:line` citations.", worded identically to E-01 (the README says the long variant is "Kept in deliberate parity with the single-file" workflow, and `plan-review.md` itself says "The two variants are otherwise kept in deliberate parity").
  NOTE THIS FILE'S MANIFEST HASH CURRENTLY MATCHES, unlike the other targets, so this edit INTRODUCES a mismatch rather than adding to an existing one (F-7). That is expected and is not a defect to repair here: the recorded hash means "the content the installer LAST WROTE", and every tracked edit to a managed file diverges from it until the next install re-records. The consequence to be aware of is narrow and documented in `engine.plan_uninstall`: a file whose content no longer matches its recorded hash is classified `drifted` and PRESERVED by `aw uninstall` instead of removed, unless `--force`. Do NOT hand-edit `.aw/system/managed-sections.json` to "fix" this; it is an installer-owned artifact.
  - Depends on: E-01
  - Expected outcome: the two variants' evidence steps say the same thing.
  - Execution state: pending

- [ ] E-04 In `.aw/system/workflows/spec-review/spec-review.md`, extend the step item beginning "4. Verify material claims with `path:line` evidence. A spec's measured claim" with the same re-locate-by-symbol rule and disposition, keeping the existing "re-measure it rather than trusting it" sentence.
  THIS FILE HAS LIVE PER-LINE GUARDS, so word the addition with them in mind (F-8). `tests/test_spec_review_attestation.py` runs a NEGATIVE per-line scan: any line matching `^.*aw ipd lint.*$` must contain one of `NOT`/`not`/`NEVER`/`never`/`IPD-only`/`preflight`/`runs`, and any line mentioning `- Readiness:` must contain a prohibition token. It also forbids restating `plan-review`'s severity glosses ("likely data loss, breach, normal-path failure", "polish or small clarity improvement") and forbids the tokens `E/V-bijection` / `E/V bijection`. So do not mention `aw ipd lint` in the new sentence, and if naming a severity, name the LEVEL only and do not gloss it. Run that test file immediately after this item rather than waiting for the suite; it passed 30/30 at review and is fast.
  - Depends on: E-01
  - Expected outcome: spec-review's evidence step carries the rule, the "re-measure it rather than trusting it" sentence is retained, and `tests/test_spec_review_attestation.py` still passes 30/30.
  - Execution state: pending

- [ ] E-05 In `.aw/system/workflows/verify-execution/verify-execution.md`, extend the "**Evidence discipline**: re-open the actual `path:line` and diff" bullet with: locate the construct by symbol or quoted string when the line has moved; a moved-but-resolvable anchor is not a gap; an unresolvable one is. (`intent-audit.md` inherits this discipline by its own words "Core discipline (inherited from `verify-execution.md`)", verified at review, so it is not edited.)
  - Depends on: E-01
  - Expected outcome: verify-execution's evidence discipline carries the rule; `intent-audit.md` untouched.
  - Execution state: pending

### Task group 2: suite

- [ ] E-06 Re-verify the ONE mechanical claim this plan's own validation rests on: run `grep -rn -i "symbol" .aw/system/workflows/plan-review .aw/system/workflows/plan-review-long .aw/system/workflows/spec-review .aw/system/workflows/verify-execution` BEFORE any edit and record the output. At review it returned exactly two lines, both the unrelated scope-fence sentence "prerequisite whose symbols are absent" (in `plan-review.md` and in `plan-review-long/review-rubric.md`). V-01's "it returns none before" claim is therefore FALSE as written, and an executor checking it literally would think the baseline was already contaminated. Record the actual pre-edit matches so the after-grep is read as a delta.
  - Depends on: none
  - Expected outcome: the pre-edit `symbol` matches recorded (two unrelated scope-fence lines at review; re-derive, since the tree is live).
  - Execution state: pending

- [ ] E-07 Run the bare suite `python3 -m pytest` and record the summary line (the workflows ship in the wheel via `pyproject.toml` `".aw/system" = "agent_workflows/_data/.aw/system"`, and installer tests read them). Baseline at review: `tests/test_spec_review_attestation.py` and `tests/test_installer.py` together were 30 passed.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: no new failures relative to the pre-change baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Do NOT add prose-pin tests: `tests/test_spec_review_attestation.py` class `WorkflowPackageTests` docstring explains the repo deliberately removed tests asserting English sentences in workflow markdown ("such a test fails on every legitimate reword and catches no defect"). Validation is therefore grep plus the suite.
- `.aw/system/managed-sections.json` records a sha256 per installed file, and the hash is over a NORMALIZED view (`manifest.hash_content` -> `normalize_for_hash`), not the raw bytes, so a raw `sha256sum` comparison answers the wrong question. Re-measured at review with the real function: `plan-review/plan-review.md` (recorded `7c986280`, actual `12e2b616`) and `verify-execution/verify-execution.md` (recorded `2df1a769`, actual `2c8f3c24`) are ALREADY stale; `spec-review/spec-review.md` is NOT TRACKED AT ALL; and `plan-review-long/01-discover-and-snapshot.md` (recorded `132091c9`) currently MATCHES, so E-03 introduces a NEW mismatch. The plan's original note gave the raw-byte pair `7c98...`/`48fb...` for one file and implied the situation was uniform; it is not. Do NOT hand-edit that file: it is installer-owned, written by `manifest.record` as "the content the installer LAST WROTE".
- THE CONSEQUENCE of a stale recorded hash is specific and is worth knowing rather than guessing: `engine.plan_uninstall` classifies an owned file whose content no longer matches its record as `drifted` and `uninstall_repo` then PRESERVES it by default ("a user-EDITED (drifted) owned file is PRESERVED by default and reported, removed only when `force` is set"). It is not an install-time refusal and it gates nothing in CI. No test reads this repository's own manifest (the installer tests all build temp repos).
- `tests/test_spec_review_attestation.py` runs LIVE assertions against `.aw/system/workflows/spec-review/spec-review.md`, including a NEGATIVE per-line scan (a line mentioning `aw ipd lint` must carry one of `NOT`/`not`/`NEVER`/`never`/`IPD-only`/`preflight`/`runs`; a line mentioning `- Readiness:` must carry a prohibition token), a ban on restating `plan-review`'s severity glosses, and a ban on the tokens `E/V-bijection` / `E/V bijection`. An added sentence can trip these. It passed 30/30 at review.
- Do NOT add prose-pin tests: that same file's `WorkflowPackageTests` docstring explains the repo deliberately removed tests asserting English sentences in workflow markdown ("such a test fails on every legitimate reword and catches no defect"), and specifically removed line-number cites into `plan-review.md` because "an unrelated edit to `plan-review.md` breaks them". Validation is therefore grep plus the suite.
- Workflow text is AI-facing, so the no-dash rule for user-facing prose does not apply.

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-1 | Authoring half is DONE: spec Section 10.2 defines (a) symbol, (b) quoted string, (c) line only appended; scaffold emits it; `IPD-C801` advises. | `ipd_authoring` scaffold string "Cite code by SYMBOL"; `ipd_lint` constant `"IPD-C801"`; plan `mzc019` in `executed/` |
| F-2 | `mzc019` Scope OUT explicitly lists "any change to how REVIEWS cite code", so the review half has no other owner. | `mzc019` `- Scope:` |
| F-3 | No review workflow mentions re-locating or drift in its evidence step: grep for `symbol` across the four workflow dirs matches only the unrelated "prerequisite whose symbols are absent" scope-fence sentence. | grep over `.aw/system/workflows/{plan-review,plan-review-long,spec-review,verify-execution}` |
| F-4 | The spec already states the reader-side posture for OLD plans ("treat it as a HINT and locate the construct by symbol"), but only in the IPD spec, which reviewers are not pointed at from their evidence step. | spec Section 10.2 paragraph "ENFORCEMENT IS ADVISORY-ONLY AND DATE-GATED" |
| F-5 | There is no separate workflow source tree; `.aw/system/workflows/` is the source and is packaged into the wheel. | `pyproject.toml` force-include `".aw/system"`; `git ls-files` shows no other `plan-review.md` besides host shims |
| F-6 | THREE WORKFLOWS DECLARE AN `Evidence` FIELD AND E-01 AMENDED ONLY ONE, so the "carry a symbol beside `path:line`" recommendation would have shipped on one of three findings tables while the other two kept the bare format the plan is trying to make survivable. The two variants are explicitly held in parity, so a one-sided edit is drift by construction. | `plan-review.md` `- **Evidence:** `path:line`.`; `plan-review-long/02-review-and-revise.md` `- Evidence: `path:line`.`; `spec-review.md` "Classify each with Severity, Scope, Area, Evidence (`path:line`)"; `plan-review-long/README.md` "Kept in deliberate parity with the single-file"; `plan-review.md` "The two variants are otherwise kept in deliberate parity" |
| F-7 | THE MANIFEST-HASH SITUATION IS NOT UNIFORM AND THE ORIGINAL NOTE MEASURED IT THE WRONG WAY. The recorded hash is over a NORMALIZED view, not raw bytes. Measured with `manifest.hash_content`: `plan-review.md` and `verify-execution.md` are already stale, `spec-review.md` is NOT TRACKED, and `01-discover-and-snapshot.md` MATCHES - so one of the four edits introduces a new mismatch rather than joining an existing one. The consequence is `aw uninstall` PRESERVING the file as user-drifted, not an install refusal. | `manifest.hash_content` -> `normalize_for_hash`; recorded vs actual `7c986280`/`12e2b616`, `2df1a769`/`2c8f3c24`, absent/`09336876`, `132091c9`/`132091c9`; `engine.plan_uninstall` classifies non-matching owned files `drifted`; `uninstall_repo` docstring "PRESERVED by default and reported, removed only when `force` is set" |
| F-8 | `spec-review.md` CARRIES LIVE PER-LINE TEST GUARDS that an added sentence can trip, and E-04 is the item that adds a sentence to it. | `tests/test_spec_review_attestation.py::test_every_mention_of_a_forbidden_act_is_a_prohibition` scans `^.*aw ipd lint.*$` and `^.*- Readiness:.*$` per line; `test_the_body_does_not_restate_the_shared_severity_glosses`; `test_the_body_does_not_apply_the_ipd_ev_rubric`; 30/30 passing at review |
| F-9 | THE COSTLIER ERROR DIRECTION HAS ALREADY BEEN MEASURED IN THIS REPOSITORY AND THE PLAN DID NOT CITE IT. A reviewer rejecting a CORRECT citation is worse than one under-reporting drift, because the finding is durable and tracked while the drift is not - and it has happened: a review finding rejected a correct spec-section citation and substituted a wrong one, which the next reader then propagated. It is also a SPEC-section anchor rather than a code symbol, so the rule must cover headings and section ids too. | backlog `88manw` (`open`, `Work-Kind: bug`, `Blocks-Release: next`): "plan si24ia review finding PR-305 rejected a correct spec section citation and substituted a wrong one"; "Line 211 IS inside section 2.1. The PLAN was right and the REVIEW was wrong"; "the plan review finding is DURABLE, tracked, and wrong, so the next reader who trusts it is sent to the wrong section and may propagate the error, which is precisely what happened once already in this chain" |
| F-10 | THE PLAN'S CITED AUTHORITY RULES OUT THE FRAMING, NOT THE CHANGE. Spec Section 10.2 says "REVIEW IS NOT THE REMEDY, which is why this is a contract rule rather than a reviewer instruction" and records that `216rgg` was reviewed twice with every line measured at HEAD and drifted anyway. So the plan must present itself as a DISPOSITION rule for drift already present, which Section 10.2 leaves to the reader and points nobody at, rather than as verification that prevents drift. | spec `ipd-structure-and-linting` Section 10.2 paragraphs "REVIEW IS NOT THE REMEDY" and "ENFORCEMENT IS ADVISORY-ONLY AND DATE-GATED" ("the correct posture toward an older plan's offset is to treat it as a HINT and locate the construct by symbol") |

## Proposed changes (ordered, validatable)

1. E-01 the disposition rule in `plan-review`, including the costlier-error direction (F-9). 2. E-02 the reviewer's-own-evidence recommendation across all three `Evidence` fields (F-6). 3. E-03 `plan-review-long` step 1 parity. 4. E-04 `spec-review`, worded around its live per-line guards (F-8). 5. E-05 `verify-execution`. 6. E-06 record the pre-edit `symbol` grep baseline. 7. E-07 suite.

## Deferred / out of scope (with reason)

- A lint that checks `path:line (symbol)` citations still resolve (backlog option 3).
  - Carrier: hesb87
- Adding the rule to the `AGENTS.md` "real citations" clause via `engine.py`.
  - Carrier-Declined: the authoring contract already lives in the IPD spec and the scaffold, which is where authors meet it; widening the managed block for every installed repo is not needed for the review fix.

## Scope check

- Over-scope: none.
- Under-scope: CLOSED AT REVIEW for the `Evidence` fields. The original text left `plan-review-long/02-review-and-revise.md`'s `Evidence: `path:line`.` and `spec-review.md`'s `Evidence (`path:line`)` unedited on the reasoning that the format recommendation is "optional guidance"; that is not sustainable when the two variants are held in explicit parity and all three declare the same field, so the recommendation would ship on one findings table of three (F-6). E-02 now covers all three and `02-review-and-revise.md` is in `Scope-Paths`.
- STILL DELIBERATELY NOT EDITED, with the reason stated rather than left implicit: `plan-review-long/report-template.md`, and the four findings-TABLE rows (`plan-review.md` "Cite evidence as `path:line`" plus its `<path:line>` placeholder, and the `spec-review.md` twins). Those are OUTPUT FORMAT - a column label in a template row is not an instruction about how to gather evidence - and this plan changes the gathering rule, not the report shape. The backlog `yos8rq` enumerates them among its citation sites, so the omission is a judgement rather than an oversight; see the review record's D-2. Also not edited: `verify-execution/intent-audit.md` (inherits by its own words, verified) and `plan-review-long/review-rubric.md` (its only `symbol` hit is the unrelated scope-fence sentence).

## Required tests / validation

Grep evidence per file against E-06's recorded PRE-EDIT baseline (not against "returns none", which is false: two unrelated scope-fence lines already match `symbol`), `tests/test_spec_review_attestation.py` run immediately after E-04 because that file carries live per-line guards, `aw ipd lint` on this plan, and the bare suite. No new test (see conventions; prose pins were deliberately removed from this repository).

## Spec / documentation sync

N/A: spec `ipd-structure-and-linting` Section 10.2 already states the rule for authors and the reader posture; this plan points reviewers at it and changes no spec.

## Open questions

### OQ-01: Should a moved-but-resolvable citation produce NO finding or a LOW one?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: yos8rq
- Resolution or deferral rationale: DEFAULT: at most ONE batched LOW per plan ("N citations drifted, all re-located by symbol"), because the drift is real information for the author but must not cost a revision round. The executor writes the default; a maintainer preferring "no finding" changes one clause. REVIEW ADDS ONE PIECE OF EVIDENCE FOR THE DEFAULT rather than resolving it, because the choice is genuinely the maintainer's: backlog `88manw` measured the opposite failure actually occurring (a review rejected a CORRECT citation and the wrong correction propagated), which argues for the batched-LOW default over "no finding" - a batched note is visible to the author without implying the claim was false, whereas silence loses the information that the plan's anchors are decaying. It does NOT argue for anything above LOW, since the substance was correct in that case. The carrier is `yos8rq`, the source item, which remains the durable home for this wording decision; a maintainer changing the clause after execution should record it there.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff .aw/system/workflows/plan-review/plan-review.md` showing ONLY the Step 1 item 4 changed by this item (the Evidence field is E-02's, so it must NOT appear in this diff). Paste the new item text and confirm it contains all three of: the re-locate-by-symbol-or-quoted-string instruction, the three-case disposition, and the statement that rejecting a citation the reviewer failed to re-locate is the costlier error, citing `88manw` (F-9). Paste the after-grep for `by symbol` / `drift` and compare it against E-06's RECORDED pre-edit baseline, not against "returns none".
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the three diff hunks - `plan-review.md`'s `**Evidence:**` field, `plan-review-long/02-review-and-revise.md`'s `- Evidence:` field, and `spec-review.md`'s `Evidence (`path:line`)` clause - and quote the appended wording from each side by side to show it is identical. Paste `git diff --name-only` and confirm `plan-review-long/report-template.md` is absent, since the table/template rows are deliberately out of scope.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `01-discover-and-snapshot.md` and a side-by-side quote showing its item 4 text matches E-01's. State explicitly that this file's manifest hash matched BEFORE the edit and now does not, so the mismatch is expected and `managed-sections.json` was NOT hand-edited (F-7); paste `git diff --name-only` showing `.aw/system/managed-sections.json` is absent.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diff of `spec-review.md` showing the rule added and the "re-measure it rather than trusting it" sentence retained, AND paste `python3 -m pytest -o addopts="" tests/test_spec_review_attestation.py` run immediately after this item showing 30 passed (F-8). The per-line prohibition scan is the guard most likely to catch this edit, and discovering it in the full suite rather than here loses the attribution.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of `verify-execution.md` evidence-discipline bullet; paste `git diff --name-only` confirming `intent-audit.md` is untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the PRE-EDIT `grep -rn -i "symbol"` output over the four workflow directories with its match count, so V-01's after-grep is read as a delta. At review it was two lines, both the scope-fence sentence "prerequisite whose symbols are absent"; re-derive rather than copying that.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary line; list and baseline-compare any failing node ids against a pre-change run of the same command.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Prose-only edits to four review workflow bodies plus one mirror field, adding a single rule: when a cited line no longer holds the cited construct, re-locate it by symbol or quoted string first, and treat a resolvable-but-moved anchor as at most a batched LOW while an unresolvable one is a real evidence finding. NO CODE CHANGES, NO SPEC CHANGES, no new test. Two things a human should weigh. FIRST, the framing: spec Section 10.2 states plainly that "REVIEW IS NOT THE REMEDY" for citation drift, so this plan is deliberately NOT claiming to prevent drift - it supplies the DISPOSITION for drift already present, which that section leaves to the reader and points no reviewer at. If the maintainer reads Section 10.2 as closing the review question entirely, this plan should not execute. SECOND, OQ-01 remains open and is a real wording choice (batched LOW versus no finding); review added evidence for the batched-LOW default from `88manw` but did not decide it, and the executor writes the default.

SCOPE FENCE, stated as a DECLARATION for reconciliation, not as a stop directive. `plan-review/plan-review.md`: Step 1 item 4 and the `**Evidence:**` field. `plan-review-long/01-discover-and-snapshot.md`: item 4. `plan-review-long/02-review-and-revise.md`: the `- Evidence:` field only. `spec-review/spec-review.md`: the Step 1 item 4 and the `Evidence (`path:line`)` clause. `verify-execution/verify-execution.md`: the `**Evidence discipline**` bullet. EXPLICITLY NOT IN SCOPE: `.aw/system/managed-sections.json` (installer-owned; a hash mismatch is expected and must not be hand-repaired); `verify-execution/intent-audit.md` (inherits by its own words); `plan-review-long/report-template.md` and `review-rubric.md`; every findings-TABLE row and `<path:line>` placeholder; the `path:line` format itself; any lint (carrier `hesb87`); the authoring rule in spec Section 10.2; and retrofitting any existing plan or review record.

HARD MUST: paste the ACTUAL output for every `V-*`. Never claim a command passed without running it. Two checks here are specifically easy to mis-certify: V-01's grep, because the plan originally asserted the pre-edit grep "returns none" when it actually returns two unrelated scope-fence lines, so compare against E-06's recorded baseline and not against that claim; and V-04's test run, because `spec-review.md` carries live per-line guards that are cheap to run immediately and expensive to attribute if first seen in the full suite. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

STOP AND REPORT, for a genuinely unsafe condition only: if `tests/test_spec_review_attestation.py` fails after E-04 for a reason the new sentence cannot be reworded around, since that means the guard and the rule genuinely conflict and the maintainer owns which wins; or if a fifth workflow has acquired an `Evidence` field declaration since authoring, which would reopen the parity question E-02 settles.

This plan is `reviewed` (review complete; NOT approved) and requires explicit human approval before execution. The executor commits only the `- Scope-Paths:` files via `aw commit x7i14a -- <paths>`, never `git add -A`, and never pushes. LIFECYCLE TRANSITION: the plan reaches `executed/` only after every `V-*` carries concrete observed evidence and `aw ipd lint --phase pre-transition` conforms. Under `aw oc run` / `aw agy run` the RUNNER owns that transition and the executor must not hand-roll it; run by hand, the executor completes it with `aw ipd finalize` (never a hand-rolled `git mv`). Source item `yos8rq` is already `graduated` and carries no `- Blocks-Release:`, so no release gate is owed or inherited.
