# IPD: Make reviewed to to-review a legal backward plan edge so aw commit stops refusing re-reviewed plans

- Date: 2026-09-26
- Kind: child
- Concern: SENDING A `reviewed` PLAN BACK TO `to-review` PERMANENTLY DISABLES THE TOOLED COMMIT PATH FOR THAT PLAN. `aw ipd set to-review <plan>` (and `aw set to-review`) on a `reviewed` plan SUCCEEDS and records a `to-review` history line, but `ipd_lifecycle.validate_transition("reviewed", "to-review")` returns `missing predecessor: backwards transition 'reviewed' -> 'to-review'`, because `ipd_lifecycle._LEGAL_BACKWARD_EDGES` enumerates only `approved -> reviewed` and `auto-approved -> reviewed`. `check_engine.check_lifecycle_transitions` then emits `check.lifecycle-transition-invalid` (error) on the plan's own history, and `work_cmd._validate_plan_via_engine` treats every non-warning, non-info finding for the plan as blocking, so `aw commit <plan> -- <paths>` REFUSES every later commit on it, including history-only or evidence-only edits. The only remaining route is `aw commit --no-plan`, which skips Scope-Paths enforcement: a routine re-review turns scope enforcement OFF for the rest of the plan's life. Reproduced end to end at HEAD `61ef21d8` on a scratch repo (Findings F-1).
- Scope: IN: (a) add `("reviewed", "to-review")` to `ipd_lifecycle._LEGAL_BACKWARD_EDGES`, per the maintainer's 2026-09-26 ruling (OQ-01); (b) amend the IPD spec's one-sentence enumeration of legal backward edges, which spec `2vev8j` 4.8 point 3 delegates to it, and declare that amendment; (c) correct the plans section of `docs/artifact-lifecycles.md`, whose "Moving backwards" example (`approved` -> `to-review`) names an edge the checker refuses both before and after this change; (d) behavioral tests: the scratch-repo repro through the real `aw ipd set` and `aw commit`, which FAILS before the change, plus controls proving un-enumerated backward edges (`approved -> to-review`, `reviewed -> draft`) are still refused. OUT: downgrading or scoping `aw commit`'s plan gate (Carrier-Declined, see Deferred); any other backward edge; the spec lifecycle (`attention_contract.SPEC_TRANSITIONS`, which already permits `reviewed -> to-review`).
- Scope-Paths: agent_workflows/ipd_lifecycle.py, .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md, docs/artifact-lifecycles.md, tests/test_ipd_lifecycle_backward_edges.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: qzo6dn
- Blocks-Release: next
- Set: backedge
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: pyuhnl

## Workflow history
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED, none deferred, no open question raised. Reviewed at HEAD `5a6b144e`; `aw ipd lint --phase author` conformed before revision. EVERY authored claim reproduced: the F-1 defect was re-run end to end on a scratch repo and produced the quoted refusal verbatim (`aw ipd set to-review` exit 0, then `aw commit` exit 1 naming check.lifecycle-transition-invalid), F-2s four predicate results, F-3s wrong doc example, F-4s clean live corpus and F-5s absent test coverage all hold, and both spec `2vev8j` 4.8 citations are accurate and load-bearing. WENT FURTHER AND MEASURED THE FIX (new F-6): applying the one-line frozenset addition in-process cleared the finding and made `aw commit` exit 0, while five un-enumerated backward edges (approved->to-review, reviewed->draft, approved->draft, executed->reviewed, to-review->draft) stayed REFUSED, so the fix is surgical and the rank comparison is provably still load-bearing. Three corrections: E-04 named the WRONG SECTION of the IPD spec (the sentence is in the bullet describing `## Workflow history` inside `## What an IPD MUST contain`, not in the spec own history log, where an executor could have rewritten a prior line the same bullet forbids rewriting), its hedge that `aw specs note` may refuse on an implemented spec is unfounded (`specs.run_note` reads no status), and V-04 asked for no new finding against an unstated non-zero `aw check specs` baseline of errors 1. Also established by sweep that E-05s docs fix is complete rather than a sample. Findings recorded in `.aw/records/reviews/20260926-backedge-01-pyuhnl-make-reviewed-to-to-review-a-legal-backward-plan-edge-so-aw.review.md`.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog qzo6dn on the maintainer's 2026-09-26 ruling that reviewed -> to-review is a legal backward plan edge (OQ-01). Defect re-measured at HEAD 61ef21d8: `aw ipd set to-review` on a reviewed scratch plan succeeds, and the next `aw commit <plan> -- src/f.py` refuses with check.lifecycle-transition-invalid.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A plan sent back from `reviewed` to `to-review` for re-review stays committable through `aw commit <plan> -- <paths>`, with Scope-Paths enforcement intact, while every backward edge the lifecycle contract does not enumerate still fails closed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce and prove the failure

- [ ] E-01 RE-MEASURE THE DEFECT at the executing HEAD. Paste `python3 -c` output of `ipd_lifecycle.validate_transition(a, b)` for the four pairs `(reviewed, to-review)`, `(approved, to-review)`, `(reviewed, draft)`, `(approved, reviewed)`. Then on a scratch git repo (a single conforming `reviewed` plan under `.aw/records/plans/pending/` plus one tracked `src/f.py`, committed; the fixture shape of `tests/test_work_gate_severity.py`'s `_PLAN` with `- Status: reviewed` and one `reviewed` history line), run `aw ipd set to-review <id6> --dir <repo> --message revise --yes`, modify `src/f.py`, and run `aw commit <id6> --dir <repo> -m x -- src/f.py`; paste both outputs and exit codes. If `aw commit` already succeeds, STOP and report the defect fixed.
  - Depends on: none
  - Expected outcome: only `(approved, reviewed)` is ok; the setter exits 0 and records `to-review`; `aw commit` exits 1 with `check.lifecycle-transition-invalid: recorded lifecycle transition 'reviewed' -> 'to-review' is invalid`.
  - Execution state: pending

- [ ] E-02 ADD `tests/test_ipd_lifecycle_backward_edges.py` (new) BEFORE the fix, driving BEHAVIOR only (no source-text or AST assertions, per the 2026-09-26 test-policy ruling). Cases: (1) THE REPRO, end to end through `cli.main`: the E-01 scratch repo, `ipd set to-review ... --yes` exits 0, then `commit <id6> ... -- src/f.py` exits 0 and `git show --stat HEAD` names `src/f.py`; (2) `check_engine.check_type(repo, "plans")` on that repo yields NO `check.lifecycle-transition-invalid` finding for the plan; (3) a direct `ipd_lifecycle.validate_transition("reviewed", "to-review").ok` is True; (4) CONTROLS, still refused: `validate_transition("approved", "to-review")` and `validate_transition("reviewed", "draft")` return `ok=False` with `backwards transition` in the reason, AND a scratch plan whose history records `reviewed` then `draft` still makes `aw commit <id6> -- src/f.py` exit 1 naming `check.lifecycle-transition-invalid`, so the gate provably still bites on an un-enumerated edge; (5) the existing edges `approved -> reviewed` and `auto-approved -> reviewed` remain ok. Write the history lines in the order the setter itself writes them (newest first), and build the repo with `git init` in a `tempfile.TemporaryDirectory`, isolating `AW_HOME` to a temp dir.
  - Depends on: E-01
  - Expected outcome: cases (1) to (3) FAIL against the unchanged code; cases (4) and (5) PASS both before and after.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-03 ADD `("reviewed", "to-review")` to `ipd_lifecycle._LEGAL_BACKWARD_EDGES`, and update the comment above it: it currently reads "Permits recovery of an approved or auto-approved plan back to reviewed ... All other backwards transitions fail closed". Name the new edge, cite the maintainer ruling of 2026-09-26 and backlog `qzo6dn`, and keep the fail-closed sentence. Do NOT touch the rank comparison in `validate_transition`: spec `2vev8j` 4.8 point 2 says an implementation that removes it "would permit EVERY backward edge, which is NOT what was decided", and E-02 case (4) pins that.
  - Depends on: E-02
  - Expected outcome: `validate_transition("reviewed", "to-review")` returns `TransitionCheck(ok=True, reason='')`; the E-02 file passes in full. PROVEN SUFFICIENT AT REVIEW (F-6): the one-line addition, applied in-process, cleared the `check.lifecycle-transition-invalid` finding and made `aw commit` exit 0 on the reproduction, while five un-enumerated backward edges stayed refused. So no companion change is expected; if one proves necessary, that is a signal something else regressed and should be reported rather than absorbed.
  - Execution state: pending

### Task group 3: contract and docs

- [ ] E-04 AMEND THE IPD SPEC `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`. THE SENTENCE IS IN THE BULLET THAT DESCRIBES `## Workflow history`, inside the `## What an IPD MUST contain` section -- NOT inside the spec's own `## Workflow history` section, which is a different section further down (location corrected at review, PR-002; searching the wrong section wastes a pass or risks editing the history log). Find it by its content: the bullet beginning "`## Workflow history` (append one dated line per workflow touch...", whose last sentence reads "The only legal backward lifecycle transitions are `approved -> reviewed` and `auto-approved -> reviewed` (spec `2vev8j` 4.8 / spec `25kzda` 4.5); every other backwards move fails closed." Add `reviewed -> to-review` (re-review after revision, maintainer ruling 2026-09-26) to that enumeration and keep the fail-closed clause verbatim. Record the amendment on the spec through the tool rather than hand-writing a history line: `aw specs note <spec path> --message "..."` naming this plan `pyuhnl` and the ruling. IT WILL NOT REFUSE (verified at review): `specs.run_note` reads no status, so the authored hedge about an `implemented` spec was unnecessary; if it nevertheless errors, paste the output and add no history line by hand. Note the tool writes a `note (aw specs)` label while this spec's one prior amendment used `amended (tgop8e)`; the `note` label is what the tool produces and is correct, so do not hand-edit it to match the older line.
  - Depends on: E-03
  - Expected outcome: the spec sentence enumerates exactly three legal backward edges, the fail-closed clause is byte-unchanged, and a `note` history line is appended by the tool.
  - Execution state: pending

- [ ] E-05 CORRECT `docs/artifact-lifecycles.md`, plans section, paragraph beginning "**Moving backwards.** A plan may step back (for example `approved` -> `to-review`) for revision." That example names an edge the recorded-history check refuses both before and after this plan (E-02 case 4), so the doc teaches a move that disables `aw commit`. Replace it with the enumerated set (`reviewed` -> `to-review` to re-review after revision; `approved` -> `reviewed` to recover an approval) and say that any other backward move is refused by `aw check`. User-facing prose: NO em or en dashes (AGENTS.md execution contract); the existing `->` arrows are ASCII and fine.
  - Depends on: E-03
  - Expected outcome: the paragraph names only edges `validate_transition` accepts; `grep -nP "[\x{2013}\x{2014}]" docs/artifact-lifecycles.md` shows no new hit in the edited paragraph.
  - Execution state: pending

- [ ] E-06 RUN THE BARE SUITE `python3 -m pytest` before the change (at E-01) and after E-05, and compare failing node IDs.
  - Depends on: E-05
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Backward-edge legality is ENUMERATED, not derived: spec `2vev8j` 4.8 ("the transition table must ENUMERATE which backward edges are legal instead of deriving legality from rank order") and point 3 ("Enumerate it in the plan status lifecycle contract (the IPD spec is the natural home) ... treat any edge not enumerated as illegal (fail closed)"). The code authority is `ipd_lifecycle._LEGAL_BACKWARD_EDGES`, consulted in `validate_transition` before the rank comparison.
- The spec lifecycle already permits this edge: `attention_contract.SPEC_TRANSITIONS["reviewed"]` includes `to-review`, and its comment reads "Backward moves (e.g. reviewed -> to-review) are permitted and recorded". This plan aligns plans with specs on this one edge.
- `aw commit`'s plan half blocks on every error finding for the plan (`work_cmd._validate_plan_via_engine`: warning is advisory, info is dropped, "Everything else is returned in blocking").
- Tests exercise behavior through `cli.main` on a `git init` scratch repo; `tests/test_work_gate_severity.py` is the precedent fixture for `aw commit` gate tests.
- Tests are run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Authored at HEAD `61ef21d8`; F-1 through F-5 RE-VERIFIED at review HEAD `5a6b144e` on 2026-09-26, all reproducing exactly as written (the F-1 reproduction was re-run end to end and produced the quoted refusal text verbatim). F-6 through F-8 were added at review.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle._LEGAL_BACKWARD_EDGES` via `aw commit` | The setter permits `reviewed -> to-review`; the checker then refuses every later tooled commit on the plan. | scratch repo: `ipd set to-review wk0001 --yes` -> rc 0, history gains `2026-09-26 to-review (aw set): revise`; then `commit wk0001 -- src/f.py` -> rc 1, `aw commit: refusing - 1 finding(s) ... check.lifecycle-transition-invalid: recorded lifecycle transition 'reviewed' -> 'to-review' is invalid: missing predecessor: backwards transition 'reviewed' -> 'to-review'` |
| F-2 | INFO | `validate_transition` | Only the two enumerated edges pass. | `(reviewed,to-review)` ok=False; `(approved,to-review)` ok=False; `(reviewed,draft)` ok=False; `(approved,reviewed)` ok=True |
| F-3 | MEDIUM | `docs/artifact-lifecycles.md` "Moving backwards" | The user doc's example, `approved` -> `to-review`, is an edge the checker refuses, and stays refused after this plan. | the paragraph text; F-2 row `(approved,to-review)` |
| F-4 | INFO | live corpus | The three plans the item named (`yeh7gc`, `m7gvuz`, `5e4sb6`) are now in `executed/`, and `aw check plans` shows no `check.lifecycle-transition-invalid` today (the rule scans pending-lane plans). The defect is therefore latent: it recurs on the next re-review, not on an existing file. | `ls .aw/records/plans/*/*m7gvuz*` -> `executed/`; `aw check plans | rg lifecycle-transition-invalid` -> no output |
| F-5 | INFO | tests | No test names `_LEGAL_BACKWARD_EDGES` or drives `validate_transition` for backward edges; `rg -n validate_transition tests` hits only unrelated `status_set.validate_transition_allowed` uses. | the grep |
| F-6 | INFO (ADDED at review) | the fix's sufficiency | **THE ONE-LINE FIX IS PROVEN SUFFICIENT, AND THE CONTROLS ARE PROVEN TO HOLD.** Verified at review by adding `("reviewed", "to-review")` to the frozenset in-process and re-running the full F-1 reproduction: `check_engine.check_type(repo, "plans")` no longer emits `check.lifecycle-transition-invalid` (only the pre-existing `info` lint diagnostic remains) and `aw commit wk0001 -- src/f.py` exits 0, committing. Five un-enumerated backward edges stay REFUSED after the patch (`approved -> to-review`, `reviewed -> draft`, `approved -> draft`, `executed -> reviewed`, `to-review -> draft`), and the two pre-existing edges stay ok. So E-03 needs no companion change and the rank comparison is provably still load-bearing. | in-process patch of `_LEGAL_BACKWARD_EDGES` + re-run of the E-01 scratch-repo sequence; `aw commit` exit 0 |
| F-7 | LOW (ADDED at review) | `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` | **E-04 NAMED THE WRONG SECTION.** The target sentence sits in the bullet DESCRIBING `## Workflow history`, inside `## What an IPD MUST contain`; the spec ALSO has a real `## Workflow history` section further down holding its own amendment log. An executor following the authored wording would search that log, and could edit the wrong place. Also measured: `specs.run_note` reads no status, so the authored hedge that `aw specs note` "may refuse on an `implemented` spec" is unfounded, and the tool writes a `note (aw specs)` label where this spec's prior amendment line reads `amended (tgop8e)`. | both sections located by content in the spec; `specs.run_note` body read (no status gate) |
| F-8 | LOW (ADDED at review) | `aw check specs` baseline | **V-04's "no new finding" BAR HAS A PRE-EXISTING NON-ZERO BASELINE.** `aw check specs` today reports `20 specs checked, errors 1, warnings 0`, the one error being the generic `cross-tree collisions NOT checked by a per-type run` notice naming `<collisions>` rather than any spec. An executor told to show "no new finding" may read the standing 1 as damage it caused. | `aw check specs` at review HEAD `5a6b144e` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the defect and its controls.
2. E-02 writes the failing behavioral tests plus the still-refused controls.
3. E-03 adds the one edge to `_LEGAL_BACKWARD_EDGES`.
4. E-04 amends the IPD spec's enumeration (declared spec edit).
5. E-05 corrects the user doc's wrong example.
6. E-06 compares the bare suite before and after.

## Deferred / out of scope (with reason)

- Making `aw commit`'s plan gate ignore, or scope to staged paths, a history finding unrelated to the paths being committed (the item's "should not be all-or-nothing" suggestion).
  - Carrier-Declined: the maintainer's 2026-09-26 ruling fixes the root cause (the edge is legal, so the finding no longer arises); weakening a fail-closed commit gate for a finding that will no longer exist would trade a real invariant for no benefit.
- Legalizing any other backward edge (for example `approved -> to-review`).
  - Carrier-Declined: not ruled; spec `2vev8j` 4.8 point 3 makes every un-enumerated edge illegal by default, and E-02 case (4) pins that.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/check_engine.py` and `agent_workflows/work_cmd.py` are deliberately NOT declared: both consume `validate_transition` unchanged and need no edit. CONFIRMED at review by measurement (F-6), not by reading alone: patching only the frozenset cleared the finding and unblocked `aw commit`, so neither consumer needs a change. Also confirmed that `ipd_lifecycle._LEGAL_BACKWARD_EDGES` has exactly ONE consumer (`ipd_lifecycle.validate_transition`, reached by `check_engine.check_lifecycle_transitions`); `run_state.validate_transition` and `set_state` are unrelated same-named symbols in a different lifecycle and are correctly out of scope.
- Docs sweep (checked at review): the wrong backward-edge example is confined to the ONE paragraph E-05 targets. `rg` over `docs/`, the root Markdown files and `.aw/system/` found no other prose teaching `approved -> to-review`, and `AGENTS.md`, `CONTRIBUTING.md` and the plans README name no backward edges at all, so E-05 is complete rather than a sample.
- Scope-Paths justification: `ipd_lifecycle.py` holds the edge set; the IPD spec holds the contract sentence (E-04); `docs/artifact-lifecycles.md` holds the wrong example (E-05); the new test file holds E-02.

## Required tests / validation

- `tests/test_ipd_lifecycle_backward_edges.py` (new): end-to-end repro through `aw ipd set` and `aw commit`, the check-engine finding absent, direct predicate assertions, still-refused controls through `aw commit`, and the pre-existing edges. Cases (1) to (3) shown FAILING before E-03.
- `python3 -m pytest tests/test_ipd_lifecycle_backward_edges.py tests/test_work_gate_severity.py -o addopts="" -q`.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- SPEC AMENDMENT, DECLARED: `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` is in `- Scope-Paths:`. WHY: spec `2vev8j` 4.8 point 3 delegates the enumeration of legal backward edges to "the plan status lifecycle contract (the IPD spec is the natural home)", and the IPD spec's sentence "every other backwards move fails closed" would otherwise directly contradict the shipped edge set. Editing the code without the spec would leave every future plan reviewed against a contract that calls this legal edge illegal. The amendment adds one edge to an enumeration and preserves the fail-closed rule, so no other plan's reviewed contract changes meaning.
- Spec `2vev8j` itself is NOT edited: its 4.8 already says the enumeration beyond `approved -> reviewed` "is NOT fixed here", so it stays true.
- `docs/artifact-lifecycles.md` (E-05): its example is wrong today and must match the enumerated set.

## Open questions

### OQ-01: Is `reviewed -> to-review` a legal backward edge for plans?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: YES. Maintainer ruling 2026-09-26 (recorded on backlog `qzo6dn` during batch graduation): "reviewed -> to-review IS a legal backward edge for plans (re-review after revision). Implement by adding it to ipd_lifecycle._LEGAL_BACKWARD_EDGES and amending the IPD spec; the setter already allows it." Consistent with the spec lifecycle, where `SPEC_TRANSITIONS` already allows it.

### OQ-02: Does the spec edit need a spec status change or re-approval?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No. AGENTS.md "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT" makes the declared Scope-Paths entry plus the Spec sync rationale the required mechanism, and the runners announce the declared spec edit before a run. The amendment implements a maintainer ruling rather than introducing a new design, so the spec stays `implemented`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the four `validate_transition` results and the scratch-repo `ipd set` and `aw commit` outputs with exit codes, showing the refusal names `check.lifecycle-transition-invalid` and `'reviewed' -> 'to-review'`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_ipd_lifecycle_backward_edges.py -o addopts="" -q` run BEFORE E-03, showing cases (1) to (3) FAILING and cases (4) and (5) passing, with the failure messages.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `ipd_lifecycle.py` diff; paste the same pytest command AFTER E-03 passing in full with the count; paste `python3 -m pytest tests/test_work_gate_severity.py -o addopts="" -q` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the spec diff showing three enumerated edges and the unchanged fail-closed clause, and confirm the diff touches the `## What an IPD MUST contain` bullet rather than the spec's `## Workflow history` section (PR-002). Paste the `aw specs note` output and the appended history line. Paste `aw check specs` and compare it against the BASELINE measured at review: `20 specs checked, errors 1, warnings 0`, where the single error is the generic `cross-tree collisions NOT checked by a per-type run` notice that names `<collisions>` and NOT any spec file. The bar is that this count does not RISE and that no finding names the IPD spec; do NOT read the pre-existing 1 as a regression you caused.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `docs/artifact-lifecycles.md` diff and the dash grep over the edited paragraph showing no em or en dash.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. One new legal backward plan edge, `reviewed -> to-review`, in `ipd_lifecycle._LEGAL_BACKWARD_EDGES`, the matching one-clause amendment to the IPD spec's enumeration (a declared spec edit), and a correction to the user doc's wrong example. Effect: a plan re-sent for review no longer locks itself out of `aw commit`, so Scope-Paths enforcement stays on. Every other backward edge still fails closed, and a test proves `aw commit` still refuses one. This implements the maintainer's 2026-09-26 ruling, graduates backlog `qzo6dn`, and inherits its `- Blocks-Release: next`.

WHAT THE REVIEW ESTABLISHED. The defect was reproduced end to end at review HEAD `5a6b144e`, producing the quoted refusal verbatim, and the proposed one-line fix was then applied in-process and MEASURED sufficient: the `check.lifecycle-transition-invalid` error cleared and `aw commit` exited 0, while five un-enumerated backward edges (`approved -> to-review`, `reviewed -> draft`, `approved -> draft`, `executed -> reviewed`, `to-review -> draft`) stayed refused. So a human is approving a change whose effect and whose blast radius are both measured, not argued. Note this amends a PUBLIC CONTRACT that spec `2vev8j` 4.8 itself flags as irreversible in kind (histories authored under it will rely on it), which is why the maintainer ruling is the basis rather than the author's judgement. Three review findings were fixed: E-04 named the wrong section of the spec, its hedge about `aw specs note` refusing was unfounded, and V-04's evidence bar did not account for a pre-existing non-zero `aw check specs` baseline.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/ipd_lifecycle.py` (`_LEGAL_BACKWARD_EDGES` and its comment only), the IPD spec's one enumeration sentence, the plans "Moving backwards" paragraph of `docs/artifact-lifecycles.md`, and the new test file. An edit outside the declared paths, if one proves necessary, is made and then justified at finalize with `--scope-reason` per out-of-scope path; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-02 must show the new tests FAILING before the fix.

GENUINE STOP CONDITION: if E-01 finds `aw commit` already succeeds after a `reviewed -> to-review` move, retire this plan rather than execute it.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `qzo6dn` `done` with `--evidence` citing the executed plan; its release gate travels with this plan.
