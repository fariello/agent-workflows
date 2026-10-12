# IPD: Make reviews decisions, record-history, graduation and ipd recheck-readiness refuse a zero-match selector with exit 2

- Date: 2026-10-12
- Kind: child
- Concern: Four selector-taking verbs answer a selector that names NO artifact anywhere in the repository with a success-shaped or wrong-code answer, so a caller cannot tell a typo from a legitimately empty answer. Re-measured in this lane at HEAD `ebcbf0676` with token `zzzzzz` (which resolves to nothing under any `artifact_types.ARTIFACT_TYPES` member): `aw reviews decisions zzzzzz` exits 0 on human, `--agent` (`outcome:clean, verified:true`) and `--json`; `aw record-history zzzzzz` exits 0 on all three (`✓ CLEAN  no sidecar history for id6 zzzzzz`); `aw graduation zzzzzz` exits 0 on all three and tells the operator `nothing yet ... Proceed.`; `aw ipd recheck-readiness zzzzzz` exits 1 on all three (`outcome:findings`, rule `readiness.selector-unresolved`). Spec `25kzda` Section 2.3 rules "Zero matches return exit 2", Section 2.4a exempts only standing-question selectors, and `docs/cli-output-contract.md` Section 11.1 already states the read-verb convention (a named-artifact assertion that matches nothing is a `cannot-run` at exit 2). `aw find`, `aw attention` and `aw runs` conform; these four do not.
- Scope: Make the four verbs refuse, at exit 2 with a `cannot-run` outcome naming each offending token on every surface they have (human, `--agent`, `--json`), a selector token that matches NO artifact in any tracked record tree AND is not a standing-vocabulary token, through ONE shared predicate and ONE shared emitter. Keep every legitimately empty answer at exit 0: a selector naming a REAL artifact that simply has no review, no sidecar history, or no linked plan/spec is a correct "nothing yet" answer, not an error. Update the `ipd recheck-readiness` exit contract declaration and docstring, the `graduation` help text that promises it "never refuses", the one shipped test that pins the defect, the read-verb contract doc, and the CHANGELOG. Does NOT touch `aw find`, `aw attention`, `aw runs`, `aw show` (filed separately as `upryxf`), any mutating `set`/`rename`/`group` verb, or what any verb matches when the selector DOES resolve.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/reviews.py, agent_workflows/readiness_recheck.py, agent_workflows/command_surface.py, tests/test_read_verb_zero_match_refusal.py, tests/test_graduation_forward_links.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: executed:zyj8io
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: tbe8v0
- Blocks-Release: next
- Set: selquiet
- Order: 2
- Highest E allocated: 09
- Author: opencode/its_direct-pt3-claude-opus-5.5-1m-us
- Id: yxsfjc
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Record: .aw/records/reviews/20261012-selquiet-02-yxsfjc-make-reviews-decisions-record-history-graduation-and-ipd-rec.review.md Round 1

- 2026-10-12 draft (opencode/its_direct-pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode/its_direct-pt3-claude-opus-5.5-1m-us): Authored from backlog item `tbe8v0`, graduating it. Every exit code in the Concern was re-driven in this lane at HEAD `ebcbf0676` rather than copied from the item. One fact the item did not state was found and filed rather than absorbed: `aw show zzzzzz` exits 1 on every surface, although `zyj8io`'s E-08 survey table recorded it as exit 2 and conforming; that is filed as backlog `upryxf` (same Set, same release gate) because the item names only four verbs and widening to a fifth would change scope this graduation does not own.

## Goal

Make these four verbs answer the question they were asked. A caller who names an artifact is asserting
it exists; when it does not exist anywhere, that is the answer, and it must not be spelled the same way
as "it exists and has nothing yet". Bring them onto the one convention `25kzda` Section 2.3/2.4a and
`docs/cli-output-contract.md` Section 11.1 already state, which `aw find`/`aw attention`/`aw runs`
already implement, without turning any legitimate "nothing yet" answer into an error.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [ ] E-01 CAPTURE THE PRE-CHANGE BASELINE before any edit lands: (a) bare `python3 -m pytest` summary line; (b) the exit code and first line of stdout/stderr of each of the four verbs on each of its three surfaces (human, `--agent`, `--json`) for four token classes, driven against the live repository: UNKNOWN (`zzzzzz`), REAL-BUT-EMPTY (an id6 that resolves to an artifact but has no review / no sidecar history / no linked plan; pick per verb and state which), VOCABULARY (`approved`), and MATCHING (`f36de0` for `reviews decisions` and `record-history`, `25kzda` for `graduation`, a pending plan id6 for `recheck-readiness`, matching the conformance matrix's own `RUNNABLE_ARGV` choices where one exists). Run `recheck-readiness` WITHOUT `--apply` so nothing is written.
  - Depends on: none
  - Expected outcome: a pasted baseline suite summary and a pasted 4 verbs x 3 surfaces x 4 classes matrix showing UNKNOWN currently answers 0, 0, 0, 1 for the four verbs respectively.
  - Execution state: pending

### Task group 2: one predicate, one emitter

- [ ] E-02 ADD THE SHARED PREDICATE AND EMITTER in `agent_workflows/cli.py` beside `find_selector_match_facts`, so the four verbs cannot drift from each other or from `aw find`. (i) A predicate (suggested name `selector_tokens_naming_no_artifact(repo_root, tokens) -> Tuple[str, ...]`) built ONLY from the EXISTING `find_selector_match_facts` and `find_selector_vocabulary`. Reuse is the point: `find_selector_match_facts` already keys on MATCHED (filename-substring rung included, so a review filename fragment matches) and already subtracts the vocabulary. Do NOT write a second resolver or a literal vocabulary list. BUT DO NOT CALL IT ONCE OVER ALL TYPES (F-11): that resolves every type even for a token found in the first, costing about 1.3 to 1.4s per REAL token, which would make the common real-but-empty answer several times slower. Instead: drop tokens in `find_selector_vocabulary()` (case-folded) and tokens that are an existing file path first, at no resolution cost; then for the remaining tokens loop `artifact_types.ARTIFACT_TYPES` in order, calling `find_selector_match_facts(repo_root, [t], remaining, vocabulary=())` per type and removing the tokens it reports `matched`, stopping as soon as none remain. What is left is refusable. This gives the same answer as the all-types call (a token is matched if any type matches it) while a real token stops at its first matching type. (ii) An emitter (suggested name `emit_zero_match_selector_refusal(ctx, cmd, tokens, next_cmd, next_desc, searched)`) that renders the refusal on every surface exactly as `_run_find`'s refusal block already does: `--agent` HAND-BUILDS the `aw.agent/v1` record (`kind:error`, `outcome:cannot-run`, `exit:2`, `verified:false`, `complete:false`, `findings:N`, `unresolved_selectors`, `unresolved_targets`, `error`, `next`) and validates it with `agent_schema.assert_valid_agent_record`, because `CommandResult.to_agent_record` drops `data` and would emit a refusal that does not name the token (`zyj8io` F-10); `--json` uses `CommandResult(status="cannot-run", exit_code=2, ...)` carrying the tokens in `data`; the human surface writes `Term.format_empty_result(..., status="fail")` to STDERR with stdout empty. Every token is passed through `agent_schema.redact_home_paths` before it enters a record or the `error`/`next` strings, per `docs/cli-output-contract.md`'s leak-posture rule for fields carrying an inbound user-supplied token. Returns 2.
  - Depends on: none
  - Expected outcome: two functions in `cli.py`, no change to `_run_find`'s behavior, and pasted output proving the predicate returns `('zzzzzz',)` for `zzzzzz` and `()` for `f36de0`, `25kzda`, `selquiet`, `approved`, and an existing file path, that it returns exactly what `find_selector_match_facts(repo, list(ARTIFACT_TYPES), [tok]).refusable` returns for each of those tokens plus `none01` and `ZZZZZZ`, and its wall time per real token (expected well under the 1.3s all-types cost; F-11).
  - Execution state: pending

### Task group 3: wire each verb, only on its empty path

Each verb consults the predicate ONLY when it is about to report an empty answer, so a non-empty answer pays nothing and is byte-identical to today.

- [ ] E-03 WIRE `aw reviews decisions` (`reviews.run_decisions`). When a selector was given and `_resolve_selector_paths` returned no paths, and the selector token is refusable by the E-02 predicate, return the E-02 emitter's refusal (cmd `reviews decisions`, next `aw reviews decisions`). A token that names a real artifact with no review keeps today's exit-0 answer and today's explanatory note unchanged, INCLUDING when no review records exist at all (the "no review records exist yet" note). Whether to refuse depends only on the predicate: an unknown token is refused even in a repository with no reviews, because "no reviews exist" does not make a typo name an artifact. `--irreversible` filtering happens AFTER resolution and must never cause a refusal (the `fqnj8k`/`zyj8io` false-no-match lesson). Update the function's docstring, which today says the verb exits 0 "whether or not any decision was found", to state the exit-2 case. Its declared `exit_contract=(0, 2)` already includes 2 and stays unchanged.
  - Depends on: E-02
  - Expected outcome: `aw reviews decisions zzzzzz` exits 2 on all three surfaces naming `zzzzzz`; a real-but-unreviewed id6 and `--irreversible` with a matching selector still exit 0.
  - Execution state: pending

- [ ] E-04 WIRE `aw record-history` (`cli._run_record_history`). When `rh.read_for` returns no records AND the id6 is refusable by the E-02 predicate, return the refusal (cmd `record-history`, next `aw find <id6>`). A REAL artifact with no sidecar history keeps today's clean exit-0 empty answer: the sidecar is machine-local and does not survive a clone (the verb's own help text says so), so absence there is legitimate. An id6 that HAS sidecar records but whose artifact was since deleted keeps printing them at exit 0, because the predicate is consulted only when records are empty. Its declared `exit_contract=(0, 1, 2)` already includes 2 and stays unchanged.
  - Depends on: E-02
  - Expected outcome: `aw record-history zzzzzz` exits 2 on all three surfaces naming `zzzzzz`; a real id6 without sidecar entries still exits 0 with `no sidecar history`.
  - Execution state: pending

- [ ] E-05 WIRE `aw graduation` (`cli._run_graduation`). When `cluster.has_any_link` is false AND the source token is refusable by the E-02 predicate, return the refusal (cmd `graduation`, next `aw find <source>`) INSTEAD of `nothing yet ... Proceed.`: telling an operator to proceed with authoring for a source that does not exist is the most harmful of the four wrong answers. A REAL source with no linked plan or spec keeps the affirmative `nothing yet ... Proceed.` answer at exit 0, which is the case `jxxec8` OQ-02 designed it for. `--kind` narrows link fields only and must not affect whether the source token is judged to exist. AMEND the parser help text in `cli.py` (the `"graduation"` description containing "it shows and never refuses") so it says the view refuses only a source id6 that names no artifact, and keeps every other "advisory, adds no uniqueness rule" statement. Its declared `exit_contract=(0, 2)` already includes 2 and stays unchanged.
  - Depends on: E-02
  - Expected outcome: `aw graduation zzzzzz` exits 2 on all three surfaces naming `zzzzzz`; a real source with no links still exits 0 with `nothing yet ... Proceed.`; the help text no longer claims the verb never refuses.
  - Execution state: pending

- [ ] E-06 UPDATE THE ONE SHIPPED TEST THAT PINS THE DEFECT. `tests/test_graduation_forward_links.py::test_case_6_no_source_at_all` asserts `rc == 0` and `nothing yet ... Proceed.` for `none01`, a token its fixture never creates, so after E-05 it would correctly fail. Do NOT weaken it: keep its stated intent (the affirmative zero answer) by writing a real source record for `none01` into the fixture (for example a graduated backlog item with `- Id: none01` and no `Graduated-To`) so it still asserts exit 0 and the `Proceed.` text, and leave its `graduation_cluster` assertions unchanged. The new UNKNOWN-source case is covered in E-07, not here. No other test in the suite asserts exit 0 on an unknown token for these verbs: measured, `tests/test_resolver_bypass_sites_climb.py` drives `record-history test01` and `graduation b00001`, both of which have records or links in its fixture and so never reach the predicate; `tests/test_review_record_classifier.py` drives `recheck-readiness` by file path; `tests/conformance_matrix.py` `RUNNABLE_ARGV` uses `f36de0` and `25kzda`, both real artifacts.
  - Depends on: E-05
  - Expected outcome: the fixture diff, and the test passing with its original assertions intact.
  - Execution state: pending

- [ ] E-07 WIRE `aw ipd recheck-readiness` (`readiness_recheck.run_recheck_readiness`), changing its unresolved-selector exit from 1 to 2. Split `_resolve`'s `missing` list with the E-02 predicate: VOCABULARY tokens (for example `approved`, `reviewed`) that matched no plan are a standing question and are DROPPED (not refused; if nothing else remains the existing "no plans to re-check" clean exit-0 path applies), while refusable tokens trigger the E-02 refusal (cmd `ipd recheck-readiness`, next `aw find plans`). REFUSE THE WHOLE INVOCATION BEFORE ANY PLAN IS RE-CHECKED OR WRITTEN when any token is refusable, including a mixed invocation where other tokens resolved (OQ-01): today a mixed invocation with `--apply` writes the resolved plans and then exits 1, which is a partial mutation reported as a failure. A token that resolves to a real artifact that is NOT a plan and matches no plan (F-12: for example backlog `adgtqb`; a spec id6 usually matches its citing plans by substring and is then simply re-checked) is NOT refusable by the shared predicate; it keeps today's per-token `readiness.selector-unresolved` diagnostic but now exits 2 with `cannot-run` too, refused before any write exactly like an unknown token, so no exit 1 remains (state this explicitly in the docstring). The `--stale-findings` half runs inside the same per-path loop, so the refuse-before-write rule covers its review-record amendments as well. Then update `agent_workflows/command_surface.py`'s `ipd recheck-readiness` declaration `exit_contract` from `(0, 1, 2)` to `(0, 2)` and its comment ("1 a named selector resolved to nothing") to match, and the `run_recheck_readiness` docstring's exit contract. Run `python3 -m pytest tests/test_exit_contract_conformance.py tests/test_command_surface_declarations.py` to prove the declaration still matches observed behavior.
  - Depends on: E-02
  - Expected outcome: `aw ipd recheck-readiness zzzzzz` exits 2 on all three surfaces naming `zzzzzz`; `aw ipd recheck-readiness <real-plan-id6> zzzzzz --apply --stale-findings` exits 2 and writes nothing (`git status` unchanged); `aw ipd recheck-readiness approved` exits 0; a non-plan artifact id6 that matches no plan (F-12) exits 2; the conformance tests pass.
  - Execution state: pending

### Task group 4: behavioral tests

- [ ] E-08 ADD `tests/test_read_verb_zero_match_refusal.py`, a behavioral test module that builds a temporary repository fixture and DRIVES each verb through `cli.main` (or a subprocess), asserting on exit codes, stdout/stderr bytes and parsed records only, never on source text (GUIDING_PRINCIPLES P16). For each of the four verbs and each of its three surfaces cover: UNKNOWN token -> exit 2, `cannot-run`, token present in the emitted bytes (`--agent` record passes `agent_schema.assert_valid_agent_record`; human stdout empty and token on stderr); REAL-BUT-EMPTY token -> exit 0 and today's clean answer; VOCABULARY token -> not refused; MATCHING token -> exit 0 unchanged. Add the verb-specific cases from E-03..E-07: `reviews decisions --irreversible` with a matching selector is not refused; `record-history` for an id6 with sidecar records but no artifact still prints them at exit 0; `graduation --kind` does not change existence judgement; `recheck-readiness --apply --stale-findings` with one real plan (carrying a re-checkable `- Readiness: no-go`, so the write WOULD happen without the refusal) and one unknown token exits 2 and leaves the plan file and its review record byte-identical; a non-plan artifact id6 that matches no plan exits 2; `reviews decisions <unknown>` in a fixture with NO review records still exits 2. Also cover a home-path-shaped unknown token being redacted in the `--agent` record.
  - Depends on: E-03, E-04, E-06, E-07
  - Expected outcome: a new test module whose pasted run passes, and which FAILS against the pre-change code (shown by running it with the E-03..E-07 edits stashed in a scratch worktree, or by quoting the pre-change exit codes from E-01 that each assertion contradicts).
  - Execution state: pending

### Task group 5: contract text and closeout

- [ ] E-09 SYNC THE DOCUMENTS AND RUN THE REGRESSION GATE. In `docs/cli-output-contract.md` Section 11.1 "Precedent and Scope", extend the sentence naming the verbs that follow the convention (today `aw attention` and `aw find`) to include `aw reviews decisions`, `aw record-history`, `aw graduation` and `aw ipd recheck-readiness`, and state the shared predicate's rule: a selector that names a real artifact with nothing to report is a clean empty answer, while one naming no artifact anywhere is refused. Add one `CHANGELOG.md` entry under the pending release describing the four exit changes, calling out that `aw ipd recheck-readiness` moves from exit 1 to exit 2 and now refuses a mixed invocation before writing anything. No em or en dashes in either user-facing text. Then run bare `python3 -m pytest` and compare against the E-01 baseline, `aw ipd lint --phase pre-transition` on this plan, `aw check release-gates`, and `aw sanitize --agent`.
  - Depends on: E-08
  - Expected outcome: the diff of both documents; baseline and post-change suite summary lines side by side; conforming pre-transition lint; clean sanitizer report.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE GOVERNING RULE IS ALREADY WRITTEN. Spec `25kzda` (`approved`) Section 2.3: "Zero matches return exit 2." Section 2.4a exempts standing-question selectors only: "A misspelled id6 still exits 2; only the status selectors are exempt." `docs/cli-output-contract.md` Section 11.1 applies the same discriminator to read verbs ("Assertions that a named artifact exists ... exits 2 ... with `outcome: "cannot-run"`, `verified: false`, and `complete: false`").
- THE PREDICATE ALREADY EXISTS AND MUST BE REUSED. `cli.find_selector_match_facts` (from `zyj8io` E-03) computes per-token MATCHED facts across any set of types, and `cli.find_selector_vocabulary` derives the exempt vocabulary from contract symbols. Driven in this lane across all `ARTIFACT_TYPES`: `zzzzzz` -> refusable `('zzzzzz',)`; `tbe8v0`, `f36de0`, `25kzda`, `selquiet`, `reusable`, `approved` -> refusable `()`.
- THE REFUSAL SHAPE ALREADY EXISTS. `cli._run_find`'s `if facts.refusable:` block hand-builds the `--agent` record (with the reason, `CommandResult` cannot carry the token, recorded as `zyj8io` F-10), uses `CommandResult` for `--json`, and writes the human refusal through `Term.format_empty_result` on stderr. `run_viewer._unresolvable_target_refusal` and `attention._unresolved_selector_record` are the same shape.
- A DECLARED EXIT CONTRACT IS CHECKED. `tests/conformance_matrix.required_scenarios` obliges a `domain_failure` scenario for a read/check leaf whose `exit_contract` includes 1, and `tests/test_exit_contract_conformance.py` checks observed exits against declarations, so dropping 1 from `ipd recheck-readiness` must be reflected in `command_surface.py`.
- REPORTING IS NOT JUDGING. `reviews.run_decisions`'s docstring and its `command_surface` comment state the verb has "no exit 1" because it reports rather than judges; a refusal at exit 2 is a usage-class answer, not a finding, so that reasoning survives.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | Three verbs report an unknown selector as a clean success | Driven: `reviews decisions zzzzzz`, `record-history zzzzzz`, `graduation zzzzzz` exit 0 on human, `--agent`, `--json`, each `--agent` record carrying `outcome:clean, verified:true` | Wire each through the shared refusal (E-03..E-05) |
| F-2 | `ipd recheck-readiness` uses exit 1 for an unknown selector | Driven: exit 1, `outcome:findings`, rule `readiness.selector-unresolved`; `readiness_recheck.run_recheck_readiness` ends `return 1 if missing else 0` | Move to 2 and update the declared contract (E-07) |
| F-3 | `graduation`'s unknown-source answer actively instructs the operator to proceed | Driven human output: `nothing yet: no plan or spec links to source zzzzzz. Proceed.` | The most harmful of the four; refusal replaces it only for a non-existent source (E-05) |
| F-4 | A REAL artifact with nothing to report is a legitimate empty answer for all four verbs | Sidecar is machine-local and not cloned (`record-history` help text); `jxxec8` OQ-02 designed the affirmative zero answer for a real source; a plan without a review is normal | The predicate is "names no artifact anywhere", not "this verb found nothing" (E-02) |
| F-5 | `recheck-readiness` with `--apply` performs a PARTIAL mutation then reports failure on a mixed invocation | `run_recheck_readiness` processes `paths` from `_resolve` and writes them before computing the `missing`-driven exit | Refuse before any write (E-07, OQ-01) |
| F-6 | `recheck-readiness` treats a vocabulary token matching no plan as missing | Its `_resolve` appends any token `selectors.resolve_selectors(repo_root, "plans", [tok])` returns nothing for, so `approved` with no approved plan exits 1 | Vocabulary tokens are dropped, not refused (E-07) |
| F-7 | One shipped test pins the defect | `tests/test_graduation_forward_links.py::test_case_6_no_source_at_all` asserts rc 0 for `none01`, which its `setUp` never creates | Give the fixture a real `none01` source so the test keeps its intent (E-06) |
| F-8 | The conformance live sweep is unaffected | `tests/conformance_matrix.RUNNABLE_ARGV` drives `reviews decisions f36de0`, `record-history f36de0`, `graduation 25kzda`; `f36de0` and `25kzda` are real artifacts (`.aw/records/plans/executed/20260929-agentemitswp-01-f36de0-...`, spec `25kzda`) | No conformance-matrix edit needed; E-07 still re-runs the conformance tests for the declaration change |
| F-9 | `zyj8io`'s survey misrecorded `aw show` | Driven: `aw show zzzzzz` exits 1 on human, `--agent` (rule `show.not_found`), `--json`; the `zyj8io` V-08 table records 2 and Conforming | Out of this item's four-verb scope; filed as backlog `upryxf` with `Blocks-Release: next` |
| F-10 | Predicate cost is paid only on the empty path | `find_selector_match_facts` across all types is a full selector resolution; `aw find zzzzzz --agent` end-to-end measured `real 0m1.915s` in this lane | Consult it only when the verb is about to answer empty, so non-empty answers are unchanged in cost (Task group 3 preamble); V-09 records the empty-path wall time |
| F-11 | (Review PR-001.) The empty path is NOT only the unknown-token path: a REAL-BUT-EMPTY token reaches it too, and an all-types call costs it the full resolution even though it matches early | Measured at review (HEAD `c4246a696`): `find_selector_match_facts(repo, list(ARTIFACT_TYPES), [tok])` takes 1.33s for `f36de0`, 1.44s for `tbe8v0`, 1.70s for `zzzzzz`; looping types and stopping at the first hit finds `h0tiaw` and `f36de0` in `plans` after 0.31s and 0.20s. End to end today: `record-history h0tiaw --agent` 0.33s, `reviews decisions h0tiaw --agent` 0.45s, `ipd recheck-readiness zzzzzz --agent` 0.62s, so an all-types call would make the common real-but-empty answer about 4x slower | E-02 drops vocabulary and file-path tokens first, then resolves type by type with early exit; V-02 and V-09 record the real-but-empty wall time |
| F-12 | (Review PR-003.) `recheck-readiness` on a real NON-plan artifact currently exits 1 | Driven: `aw ipd recheck-readiness adgtqb --agent` (`adgtqb` is backlog `idxuntrack-01`, matching no plan) -> `outcome:findings`, `exit:1`, rule `readiness.selector-unresolved` | E-07's non-plan case uses `adgtqb` (or any id6 re-derived the same way), not a spec id6, because a spec id6 is usually cited by its plans and resolves as a plan through the substring rung (`aw ipd recheck-readiness 25kzda` exits 0 re-checking 13 plans) |
| F-13 | (Review PR-005.) The `ipd recheck-readiness` exit contract has never shipped in a release | `git log -S'"ipd recheck-readiness"' -- agent_workflows/command_surface.py` -> first commit `af3b5b2e9`; `git tag --contains af3b5b2e9` is empty (latest tags `v1.1.0`, `v1.2.0-recreated`, `v1.3.0-rc.1`) | OQ-02's 1 -> 2 move changes no published contract; the CHANGELOG still records it under the pending release |

## Proposed changes (ordered, validatable)

1. Capture the baseline suite and the 4x3x4 exit matrix (E-01).
2. Add the shared predicate and emitter in `cli.py`, reusing `find_selector_match_facts` (E-02).
3. Wire `reviews decisions` (E-03), `record-history` (E-04), `graduation` with its help text (E-05).
4. Re-point the one defect-pinning graduation test to a real source (E-06).
5. Wire `ipd recheck-readiness`, refuse before write, update its declared exit contract (E-07).
6. Add the behavioral test module (E-08).
7. Sync the contract doc and CHANGELOG, then run the regression gate (E-09).

## Deferred / out of scope (with reason)

- `aw show` exits 1 on a zero-match selector (F-9).
  - Carrier: upryxf
- Refactoring `_run_find` onto the new shared emitter. Its behavior is correct and shipped; moving it would put a fifth verb's bytes at risk for no defect.
  - Carrier-Declined: No defect exists to carry. `aw find`'s refusal is measured conforming (`aw find plans zzzzzz --agent` exits 2 in this lane) and covered by `tests/test_cli_find.py`; converging the two code paths is a tidiness preference, not owed work, and E-02 already copies its shape so the two cannot disagree on the emitted contract.
- Mutating selector verbs (`set`, `rename`, `group`, `archive`). They resolve through `selectors.resolve_for_mutation`, a different refusal contract.
  - Carrier-Declined: Not part of this item, which lists exactly four read verbs, and the mutating verbs already fail closed on an unresolved selector through `resolve_for_mutation`'s own policy; nothing measured here shows a defect there.

## Scope check

- Over-scope: none. `cli.py` holds the shared helpers, `_run_record_history`, `_run_graduation` and the graduation help text; `reviews.py` holds `run_decisions`; `readiness_recheck.py` holds `run_recheck_readiness`; `command_surface.py` holds the declared exit contract that must match; the two test paths are the new module and the one pinning test; the doc and CHANGELOG state the user-facing contract.
- Under-scope: `agent_workflows/attention.py` and `agent_workflows/selectors.py` are deliberately NOT declared; the predicate is built from `cli.py`'s existing functions. If execution finds it cannot be, make the edit and justify it at finalize with `--scope-reason <path>=<why>`, recording why in this plan. `tests/test_exit_contract_conformance.py` and `tests/test_command_surface_declarations.py` are run, not edited.

## Required tests / validation

- Bare `python3 -m pytest`, with its `N passed` summary line pasted beside the E-01 baseline captured the same way.
- Targeted runs of `tests/test_read_verb_zero_match_refusal.py`, `tests/test_graduation_forward_links.py`, `tests/test_resolver_bypass_sites_climb.py`, `tests/test_review_record_classifier.py`, `tests/test_cli_find.py`, `tests/test_exit_contract_conformance.py` and `tests/test_command_surface_declarations.py`.
- Real end-to-end invocations of all four verbs on all three surfaces for the four token classes, with actual exit codes pasted.
- `aw ipd lint --phase pre-transition`, `aw check release-gates`, `aw sanitize --agent`.

## Spec / documentation sync

- NO SPEC AMENDMENT. Spec `25kzda` Section 2.3/2.4a already rules this behavior and `docs/cli-output-contract.md` Section 11.1 already states it for read verbs; this plan makes four more verbs conform. The sidecar spec (`20260818-1525-02-sidecar-metadata-and-history`, R3/AC2) specifies what `aw record-history` returns for a known id6 and states no exit code for an unknown one, so it is unaffected. No `.spec.md` path is in `- Scope-Paths:`.
- `docs/cli-output-contract.md` Section 11.1 names the conforming verbs and must name these four (E-09).
- `CHANGELOG.md` records the exit changes, including the one exit 1 -> 2 move (E-09).
- The `aw graduation` parser help text in `cli.py` must stop claiming the verb "never refuses" (E-05).

## Open questions

### OQ-01: Should a mixed `recheck-readiness` invocation (one real plan, one unknown token) refuse entirely, or re-check the real plan and then exit 2?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: RESOLVED: refuse the whole invocation before any re-check or write. Evidence: spec `25kzda` Section 2.3 step 7 freezes the complete selected set before dispatch and rejects a bad selector before any session starts; `selectors.resolve_for_mutation` likewise refuses before mutating. A partial write reported as a failure (F-5) leaves the operator unsure what changed. Reversible: the alternative is a small change confined to `run_recheck_readiness`. A reviewer who prefers partial processing should say so; E-07 and E-08 name the behavior explicitly so the choice is visible.

### OQ-02: Is moving `ipd recheck-readiness` from exit 1 to exit 2 an acceptable change to a published exit contract?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: RESOLVED from the backlog item, which names this verb and its exit-1 behavior as the nonconformance to fix under `Blocks-Release: next`. Verified at review (F-13): the verb's exit contract was introduced after the latest release tag, so no published release carries the exit 1 being removed. In-repo consumers were checked: no workflow, doc or test branches on its exit 1 (`.aw/system/workflows/plan-review/plan-review.md` documents preview/`--apply` usage only; `tests/test_review_record_classifier.py` asserts rc 0 on path selectors). The change is called out in `CHANGELOG.md` (E-09). If the maintainer reads the item differently, a reviewer should escalate this to Blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted pre-change bare `python3 -m pytest` summary line and the pasted 4 verbs x 3 surfaces x 4 token classes matrix of exit codes, captured BEFORE any edit (state the HEAD), showing UNKNOWN at 0/0/0/1 for `reviews decisions`/`record-history`/`graduation`/`recheck-readiness`. Observed by driving the CLI entry points `reviews.run_decisions`, `cli._run_record_history`, `cli._run_graduation`, `readiness_recheck.run_recheck_readiness`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of the predicate for `zzzzzz` (refusable), and for `f36de0`, `25kzda`, `selquiet`, `approved` and an existing file path (all not refusable); pasted equality against `find_selector_match_facts(repo, list(ARTIFACT_TYPES), [tok]).refusable` for each of those plus `none01` and `ZZZZZZ`; the predicate's pasted wall time for `f36de0` and `zzzzzz`; plus the `git diff` of `cli.py` showing the predicate calls `find_selector_match_facts` and `find_selector_vocabulary` rather than carrying a token literal, and that `_run_find` is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `aw reviews decisions zzzzzz` on human (exit 2, stdout empty, token on stderr), `--agent` (exit 2, `cannot-run`, `zzzzzz` in `unresolved_targets`), `--json` (exit 2, `cannot-run`); plus a real-but-unreviewed id6 and `aw reviews decisions f36de0 --irreversible` each exiting 0.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `aw record-history zzzzzz` on all three surfaces exiting 2 and naming the token; plus a real id6 with no sidecar entry still exiting 0 with `no sidecar history`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `aw graduation zzzzzz` on all three surfaces exiting 2, naming the token, and NOT printing `Proceed.`; a real source with no links still printing `nothing yet ... Proceed.` at exit 0; and the amended `aw graduation --help` text with "never refuses" gone.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the `git diff` of `tests/test_graduation_forward_links.py` showing only fixture setup added to `test_case_6_no_source_at_all` with its `assertEqual(rc, 0)` and `Proceed.` assertions unchanged, and a pasted passing run of that module.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted `aw ipd recheck-readiness zzzzzz` on all three surfaces exiting 2; `aw ipd recheck-readiness <real-plan-id6> zzzzzz --apply --stale-findings`, run in a temporary fixture repository whose real plan carries `- Readiness: no-go` that would otherwise be rewritten, exiting 2 with that fixture's `git status --porcelain` identical before and after; `aw ipd recheck-readiness approved` exiting 0; a non-plan artifact id6 matching no plan (F-12, e.g. `adgtqb`) exiting 2; the `command_surface.py` diff showing `exit_contract=(0, 2)`; and a pasted passing run of `tests/test_exit_contract_conformance.py tests/test_command_surface_declarations.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: a pasted passing run of `tests/test_read_verb_zero_match_refusal.py` with its test count, plus proof the module exercises behavior (it calls `cli.main` or a subprocess and asserts on exit codes and output bytes; no `inspect`/`ast`/source reads) and proof it would fail pre-change (a pasted failing run against pre-change code, or a per-assertion mapping to the E-01 pre-change exit codes it contradicts).
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: the `git diff` of `docs/cli-output-contract.md` and `CHANGELOG.md` with zero em/en dashes in the added text; the baseline and post-change bare `python3 -m pytest` summary lines side by side, any failure shown pre-existing by the baseline; the end-to-end wall time of `aw graduation zzzzzz --agent` (F-10), and of `aw record-history <real-id6-without-sidecar> --agent` and `aw reviews decisions <real-unreviewed-id6> --agent` before and after the change (F-11; the real-but-empty path must not regress by the full all-types cost); conforming `aw ipd lint --phase pre-transition`; clean `aw check release-gates`; and an `aw sanitize --agent` record with `findings:0`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Open questions: OQ-01 and OQ-02 are resolved; none remain.
Prerequisite: `zyj8io` is executed (verified at review: it is under `plans/executed/`). Start with `aw ipd begin yxsfjc`.
The executor must perform E-01 through E-09 in order, respecting the declared `Depends on` edges.
`- Scope-Paths:` is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is
made and justified with `--scope-reason`, not a reason to stop. STOP and report only if a co-worker's
uncommitted change occupies a region you must edit and the two cannot be safely combined. HONESTY RULE:
every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no output does not satisfy it;
verify each `V-*` in a separate pass from the `E-*` that produced it. Commit only through
`aw commit yxsfjc -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify the staged set with
`git diff --cached --name-only` first, and never push. E-01 and E-07 drive `recheck-readiness` WITHOUT
`--apply` against the live repository; the `--apply` cases run only in a temporary fixture. The terminal
transition is MANDATORY and its owner is conditional: under `aw oc run` / `aw agy run` the runner
performs the finalize after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`;
executed by hand, the executor runs `aw ipd finalize yxsfjc` once `aw ipd lint --phase pre-transition`
conforms and every `V-*` records concrete pasted evidence with Result: pass. Never hand-roll the move or
`git mv` this plan into `executed/`.

Backlog item `tbe8v0` is this plan's origin (`- From-Backlog: tbe8v0`) and its `- Blocks-Release: next`
gate is inherited above, so the release gate travels with the work.
