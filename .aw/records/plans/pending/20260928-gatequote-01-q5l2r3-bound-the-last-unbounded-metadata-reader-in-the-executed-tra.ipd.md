# IPD: Bound the last unbounded metadata reader in the executed-transition gate and pin vnzm27's reported shape

- Date: 2026-09-28
- Kind: child
- Concern: Backlog `vnzm27` reports that `executed_transition_gate._has_executed_status` reads a QUOTED `- Status: executed` inside a fenced evidence block as the plan's own terminal status, falsely refusing a commit. THAT DEFECT IS ALREADY FIXED and this plan does NOT re-fix it: plan `kecxnb` (Set `fencegate`, executed 2026-09-26) bounded that function to `selectors.metadata_region`, and `vnzm27`'s exact reported shape (a V-item pasting four children's real `- Status: executed` lines in a fence, own status `approved`) now measures `False` at HEAD `1553abce`. What `kecxnb` did NOT fix is the reader SITTING BESIDE IT IN THE SAME FILE: `_plan_id_of` still reads the FIRST `^- Id:` in the WHOLE document, so one record's two fields are read under two different boundary rules. That residual is not cosmetic and not merely a false REFUSAL: measured at HEAD, it causes the gate to WRONGLY ACCEPT a raw hand-moved plan, because a fenced quote of another plan's `- Id:` makes the gate attribute the transition to the quoted id6 and a merge carrying `lifecycle(<quoted-id6>): finalize` then authorizes a plan that was never finalized. That is a false ACCEPT in the exact prevention layer `vnzm27` says MUST NOT be relaxed.
- Scope: IN: bound `_plan_id_of` to `selectors.metadata_region` in `agent_workflows/hooks/executed_transition_gate.py`; add regression tests for the false-accept and for `vnzm27`'s reported shape. OUT: every other unbounded reader in the toolkit (carried by `axayfn`); the gate's detection, journal, and merge-evidence logic; any relaxation of the gate.
- Scope-Paths: agent_workflows/hooks/executed_transition_gate.py, tests/test_executed_transition_gate.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: vnzm27
- Blocks-Release: next
- Set: gatequote
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: q5l2r3

## Workflow history

- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog vnzm27. Measured at HEAD 1553abce that vnzm27's REPORTED defect is already fixed by kecxnb, and that the sibling reader `_plan_id_of` in the same file is still unbounded and produces a measured FALSE ACCEPT. Re-aimed the plan at that residual rather than re-fixing a fixed function.
- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Both metadata reads in the executed-transition gate are bounded to the record's own metadata region, so a fenced quotation can neither cause a false refusal (already true) nor a false accept (this plan), and `vnzm27`'s reported shape is pinned by a test so it cannot regress.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: bound the residual reader and pin both directions

- [ ] E-01 Bound `_plan_id_of` (`agent_workflows.hooks.executed_transition_gate._plan_id_of`) to the record's own metadata region: read the id6 from `selectors.metadata_region(text)` instead of from the whole text, taking the FIRST `- Id:` bullet there, exactly as the neighbouring `_has_executed_status` already does.
  - TAKE THE FIRST BULLET IN THE REGION, not any match, for the same load-bearing reason `kecxnb` recorded for its own fix: `selectors.metadata_region` returns the WHOLE input for a record presenting no `##` heading (its docstring documents this as deliberate and correct for 25 of 1614 tracked records), so an any-match-in-region implementation is still unbounded for a headingless record.
  - DO NOT WIDEN THE EXISTING PATTERN while moving it. The current regex is `(?m)^- Id:\s*([0-9a-z]{6})\s*$`: exact-case `- Id:`, no leading-whitespace tolerance, anchored end. Keep it byte-identical and change only the TEXT it is applied to. Adding `[ \t]*` tolerance or a case-insensitive flag here would make the reader match MORE quoted shapes, which is the opposite of this plan's direction.
  - REGRESSION RISK IS MEASURED AT ZERO, which is what makes this safe: over all 867 tracked `.ipd.md` plans at HEAD `1553abce`, the unbounded read and a region-bounded read return the SAME id6 for every single file (`divergent=0`), and neither returns `None` for any file (`unbounded_None=0 bounded_None=0`). So no plan in the tree changes how it is read.
  - Depends on: none
  - Expected outcome: a fenced `- Id:` quotation no longer decides which plan the gate thinks is transitioning; the metadata `- Id:` still does.
  - Execution state: pending

- [ ] E-02 Add regression tests to `tests/test_executed_transition_gate.py` covering BOTH directions the gate can fail in, and covering `vnzm27`'s own reported shape.
  - (a) THE FALSE ACCEPT, which is the severity claim of this plan and must be a test rather than prose: in a temp repo, stage a plan into `executed/` whose metadata `- Id:` is `3v7wo6` but whose PREAMBLE fences `- Id: bbbbbb`, inside a merge whose incoming side carries only `lifecycle(bbbbbb): finalize`. Assert `check()` REFUSES (exit 1). Measured against the pre-change code this returns `(0, [])`, i.e. it wrongly accepts.
  - (b) THE MISATTRIBUTION, cheaper and more direct: the same plan text staged into `executed/` with no merge, asserting the refusal message names `3v7wo6` and NOT `bbbbbb`. Measured against the pre-change code the message names `bbbbbb`.
  - (c) `vnzm27`'S REPORTED SHAPE, as a unit case on `_has_executed_status`: a plan whose own metadata status is `approved` and whose `## Validation` section fences a `grep -m1 '^- Status:'` transcript containing four `- Status: executed` lines returns `False`. This PASSES at HEAD and is a pin, not a fix; label it as such in the test name or docstring so a reader does not mistake it for the defect being fixed here. Its value is that `vnzm27` is the item this plan closes, and its reported shape should have a named test.
  - (d) THE GATE STILL REFUSES A GENUINE RAW TRANSITION: a plan with a clean metadata `- Id:` hand-`git mv`ed into `executed/` with no journal and no merge is still refused. This guards the direction that matters most, since a bug in E-01 that made `_plan_id_of` return `None` would change refusals into a different refusal, and one that made it return a wrong id could skip them.
  - Depends on: E-01
  - Expected outcome: (a), (b) fail against the pre-change reader and pass after; (c) and (d) pass both before and after.
  - Execution state: pending

- [ ] E-03 Run the bare suite (`python3 -m pytest`) and confirm no regression.
  - Depends on: E-02
  - Expected outcome: green, with any failure named as pre-existing at the base commit or new.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.metadata_region` is the toolkit's ONE metadata boundary for identity/status reads, and its docstring states the purpose in exactly the terms this plan needs: "a document that merely QUOTES a metadata block ... cannot be read as ASSERTING the quoted values. Identity comes from where an artifact declares it, not from anywhere the pattern happens to match."
- `metadata_region` returns the WHOLE input when the input contains no `##` heading (deliberate, documented, correct for 25 of 1614 tracked records), so every caller must still take the FIRST bullet rather than any match in the region. `kecxnb` recorded this as its F-4 and it applies identically here.
- The gate is a LOCAL best-effort prevention whose own refusal text names `--no-verify` and the `aw check`/`aw doctor` proclint detector as the backstop. That bounds severity to MED, and it is also why a FALSE ACCEPT matters more than a false refusal here: an operator notices a refusal and works around it, whereas a wrongly accepted raw transition is silent.
- `artifact_core.finalize_commit_subject` is the one definition of the `lifecycle(<id6>): finalize` subject that both the producer and this gate's matcher consume, so the false-accept test must compose the subject through it rather than hardcoding the string.
- AGENTS.md's execution contract requires a bare `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so adding `-n0`, a second `-q`, or `-p no:randomly` is forbidden.

## Findings

All measured at HEAD `1553abce` in this lane worktree.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | INFO | `executed_transition_gate._has_executed_status` | `vnzm27`'S REPORTED DEFECT IS ALREADY FIXED, so this plan must not re-fix it. The function reads `selectors.metadata_region(text)` and matches the first `- Status:` bullet there. | driven on `vnzm27`'s exact shape (own status `approved`, a fenced four-line `grep -m1 '^- Status:'` transcript of `- Status: executed`) -> `False`; the same text with metadata `executed` -> `True` |
| F-2 | INFO | plan `kecxnb`, backlog `4vhe5o` | The fix landed via `kecxnb` (Set `fencegate`), which graduated from backlog `4vhe5o`, a DUPLICATE of `vnzm27` filed one day later. `4vhe5o` is `done`; `vnzm27` was left `open` and still carries `- Blocks-Release: next`, so the release is gated on an item whose reported symptom no longer reproduces. | `4vhe5o` history: "closed by aw oc run: IPD kecxnb executed"; `aw find backlog` shows `vnzm27` `open` |
| F-3 | MED | `executed_transition_gate._plan_id_of` | THE SIBLING READER IN THE SAME FILE IS STILL UNBOUNDED, so the file reads one record's two fields under two different boundary rules. It applies `(?m)^- Id:\s*([0-9a-z]{6})\s*$` to the WHOLE staged text and takes the first match. | driven: text whose preamble fences `- Id: bbbbbb` above metadata `- Id: 3v7wo6` -> returns `bbbbbb` |
| F-4 | MED | `executed_transition_gate.check` | F-3 IS A FALSE ACCEPT, NOT ONLY A MISLABEL, which is what raises this above cosmetic. A plan hand-staged into `executed/`, inside a merge whose incoming side finalized only `bbbbbb`, is ACCEPTED because the gate binds the merge evidence to the quoted id6. `vnzm27` explicitly says the gate "is otherwise correct and MUST NOT be relaxed or bypassed"; this is a silent relaxation already present. | driven end to end in a temp repo: incoming side carries only `lifecycle(bbbbbb): finalize`, plan's real `- Id:` is `3v7wo6` -> `check()` returns exit `0` |
| F-5 | LOW | `executed_transition_gate.check` refusal text | The same misread also MISATTRIBUTES a genuine refusal, printing the quoted id6 and telling the operator to run `aw ipd finalize <wrong-id6>`, a command that cannot succeed for the plan actually being committed. | driven with no merge in progress: refusal names `bbbbbb`, plan's real `- Id:` is `3v7wo6` |
| F-6 | INFO | 867 tracked plans | THE FIX CANNOT REGRESS ANY EXISTING PLAN, which is what makes it cheap. Bounded and unbounded reads agree on every tracked plan, and neither returns `None` for any of them. | `plans=867 unbounded_None=0 bounded_None=0 divergent=0` |
| F-7 | INFO | backlog `axayfn` | THE BROADER UNBOUNDED-READER SET IS ALREADY TRACKED and must not be absorbed here. `axayfn` is `open`, `Work-Kind: bug`, `Blocks-Release: next`, and names `check_engine._ITEM_ID_RE`, `runner_shared.discover_specs`, and `status_set._ID_RE`. It does NOT name `_plan_id_of`, which is why this plan is the right carrier for that one reader. | read `.aw/records/backlog/open/20260921-idcapture-01-axayfn-*.backlog.md` |
| F-8 | INFO | `check_engine._status_meta` | The sibling STATUS reader `kecxnb` carried out to `pyk78c` is also fixed now (`_status_meta` delegates to the bounded `_metadata_status`), so no status-side residual remains. | driven: a record with no front-matter status quoting a fenced `- Status: executed` -> `None` |

## Proposed changes (ordered, validatable)

1. E-01: bound `_plan_id_of` to `selectors.metadata_region`, keeping the existing pattern byte-identical.
2. E-02: tests for the false accept (a), the misattribution (b), `vnzm27`'s reported shape as a pin (c), and the preserved genuine refusal (d).
3. E-03: bare suite.

## Deferred / out of scope (with reason)

- The three other unbounded identity readers (`check_engine._ITEM_ID_RE`, `runner_shared.discover_specs`, `status_set._ID_RE`) and the live `uyeko5` id6 collision they manufacture. A different set of modules with different consumers, and already filed.
  - Carrier: axayfn
- Every other unbounded metadata reader found while scoping this plan and NOT covered by `axayfn`: `cli._artifact_status` (backs `aw search --status`, live-divergent on one review record), `artifact_audit.read_declared_status` (reached from `doctor`, live-divergent on four records), `ipd_schema.read_readiness` (the forged-attestation field, latent), and the four `attention.py` bullet readers (latent, escaping only because `_record_for` routes research to a YAML parser). Out of scope: none is in this file, and `vnzm27` is about this gate. These need a NEW backlog item; this plan does not file one, and that gap is stated here so a reviewer can decide.
  - Carrier: none (unfiled; flagged for the reviewer)
- Relaxing, widening, or adding an exemption to the gate. `vnzm27` forbids it and this plan moves strictly in the opposite direction.
  - Carrier: none (explicitly rejected)

## Scope check

- Over-scope: RE-AIMED RATHER THAN WIDENED, and a reviewer should check this judgement first. The backlog item's literal ask (make the status read fence-aware) is already satisfied, so executing it verbatim would be a no-op change to a function that already reads the way the item asks. This plan instead fixes the one remaining unbounded reader IN THE SAME FILE, which is the same defect class, the same file, and the same declared `- Scope-Paths:` `kecxnb` used. Nothing outside those two paths is touched. If a reviewer judges that closing `vnzm27` should be a records-only act with no code change, this plan should be superseded rather than trimmed, because its value is entirely F-3/F-4.
- Under-scope: DELIBERATE, on the reader set. Seven-plus unbounded readers exist elsewhere in the toolkit; fixing them here would make a MED one-function change into a cross-module sweep whose blast radius includes `doctor`, `aw search`, and `attention`. Three are carried by `axayfn` and the rest are flagged unfiled above.

## Required tests / validation

- `python3 -m pytest tests/test_executed_transition_gate.py tests/test_executed_transition_gate_e2e.py -o addopts=""` (the narrow suite plus the e2e suite that covers this gate's merge paths, since E-01 changes a function both reach).
- Bare `python3 -m pytest`.
- A worktree revert of E-01 to prove tests (a) and (b) genuinely fail against the pre-change reader.

## Spec / documentation sync

N/A with reason: no spec text changes. The `ipd-lifecycle` spec already makes a plan's identity its metadata `- Id:`, and `selectors.metadata_region`'s docstring already states the boundary rule this plan applies; this change makes one more reader obey the contract as written rather than amending the contract. No `.spec.md` path is in `- Scope-Paths:`.

## Open questions

### OQ-01: Should closing `vnzm27` also de-gate it, given its reported symptom no longer reproduces?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, keep the gate and let it ride on this plan. Resolved from the repository's own rule rather than by preference: AGENTS.md states a `bug`-kind item MUST carry `- Blocks-Release:` while live, and that a graduating plan inherits it. This plan carries `- Blocks-Release: next` and `- From-Backlog: vnzm27`, which is the HANDOFF path the close-legitimacy rule accepts, so `vnzm27` goes to `graduated` now and can close `done` once this plan is `executed` with the gate provably preserved. De-gating would have been the right answer only if this plan made no code change, which F-3 and F-4 show is not the case.

### OQ-02: Are the unbounded readers outside `axayfn`'s three (notably `cli._artifact_status` and `artifact_audit.read_declared_status`, both live-divergent) worth a new backlog item?

- Blocking: no
- Status: open
- Owner: human
- Resolution or deferral rationale: NOT RESOLVED HERE because filing it is a scope and priority decision that belongs to the maintainer, and because it is genuinely outside this plan's file. The facts are recorded above so the decision is cheap: both are live-divergent today on tracked records (`aw search --status` wrongly matches a review record that only quotes `- Status: open`; `doctor`'s audit reads a declared status off four quoted bullets), and `ipd_schema.read_readiness` is latent but reads the exact attestation field AGENTS.md singles out as forgeable. Non-blocking: this plan is correct and complete without that decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual `git diff` of `_plan_id_of`. The diff MUST show the regex string UNCHANGED and only the searched text changed; if the pattern string differs in any byte, this item FAILS regardless of test results (E-01 forbids widening it).
  - ALSO REQUIRED: paste a `python3 -c` (or heredoc) run driving `_plan_id_of` on the fenced-preamble text (`- Id: bbbbbb` fenced above metadata `- Id: 3v7wo6`) returning `3v7wo6`, AND on a HEADINGLESS record of the same shape also returning `3v7wo6`. The headingless case is the only one distinguishing a correct first-bullet implementation from a plausible any-match-in-region one; an any-match implementation passes the first and fails the second.
  - ALSO REQUIRED: re-run the corpus measurement and paste its output, showing `divergent=0` and `bounded_None=0` over all tracked `.ipd.md` plans AFTER the change. A nonzero `bounded_None` means some plan's id is now unreadable, which would turn its refusal into the no-readable-Id branch; that is a regression and must fail this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the passing run of `python3 -m pytest tests/test_executed_transition_gate.py tests/test_executed_transition_gate_e2e.py -o addopts=""` with its summary line.
  - ALSO REQUIRED (the load-bearing half): revert E-01 IN THE WORKTREE, re-run, and paste the ACTUAL failure output for (a) and (b). (a) must fail by the gate returning exit `0` where the test expects `1`, and (b) must fail on the refusal message naming `bbbbbb`. Name the observed failure mode explicitly and confirm it is a behavioral assertion failure, not an import, fixture, or git-setup error. Then restore. A reverted run in which (a) and (b) still PASS means the tests do not actually exercise the defect and this item FAILS.
  - ALSO REQUIRED: confirm test (c) is labelled as a PIN of `vnzm27`'s already-fixed reported shape and not as the defect this plan fixes, and paste the line or docstring that says so. State plainly that (c) and (d) pass in BOTH the reverted and restored runs.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed. For any failure, paste its node id and evidence that it fails identically at the base commit (pre-existing) or admit it is new. Do not paste a narrowed run in place of the bare one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING, AND THE FIRST THING TO CHECK. This plan does NOT do what its backlog item asks, because that work is already done, and a reviewer should accept or reject that re-aiming before reading anything else. `vnzm27` asks for `_has_executed_status` to stop reading a fenced `- Status: executed` as the plan's own; plan `kecxnb` did exactly that and `vnzm27`'s reported shape measures `False` at HEAD (F-1). What is approved instead is a one-function change to the reader BESIDE it, `_plan_id_of`, which is still unbounded and which measurably causes the gate to WRONGLY ACCEPT a raw hand-moved plan when a merge finalized a DIFFERENT plan whose id6 the record happens to quote (F-4). The direction is strictly TIGHTENING: it makes the gate refuse something it currently accepts, and `vnzm27` itself insists the gate must not be relaxed.

SEVERITY IS HONESTLY MED, and the reasoning cuts both ways so it belongs in front of the approver. Against MED: the gate is a LOCAL best-effort hook, skippable with `--no-verify` and backstopped by the `aw check`/`aw doctor` proclint detector, and the exploiting shape (a plan quoting another plan's `- Id:` in its own preamble, above its metadata, while being integrated in a merge that finalized that other plan) does not occur anywhere in the tree today. Against LOW: a false ACCEPT in a prevention layer is silent, unlike the false REFUSAL `kecxnb` fixed, and the misattributed refusal (F-5) hands the operator a `aw ipd finalize <wrong-id6>` command that cannot work, which is exactly the kind of dead-end remedy that trains `--no-verify` habits.

Scope fence (a DECLARATION for reconciliation, not a stop directive): within `agent_workflows/hooks/executed_transition_gate.py`, only `_plan_id_of`. No change to `_has_executed_status`, `_staged_plan_executed_transitions`, `_finalize_evidence_ok`, `_merge_incoming_commits`, `_intree_finalize_evidence_ok`, `check`, or `main`. `tests/test_executed_transition_gate.py` gains cases and keeps its existing five. `agent_workflows/selectors.py` is expected to need NO edit: the fix CONSUMES `metadata_region` unchanged, and adding a second local region parser is the precise drift that helper exists to prevent. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Two claims here are specifically easy to fake and must not be: V-01's HEADINGLESS case, the only one separating a correct first-bullet implementation from a plausible any-match one, and V-02's REVERTED run, since four passing tests against the fixed code prove nothing about whether the tests can detect the defect at all.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if the corpus measurement in V-01 shows any plan whose id6 becomes unreadable (`bounded_None` nonzero), STOP and report rather than adding a fallback to the unbounded read, because a silent fallback restores the defect for exactly the records that need the bound. If test (d) regresses, that is, a genuine raw `git mv` into `executed/` stops being refused, STOP and report: loosening the real gate is strictly worse than the misattribution this plan fixes. If a reviewer concludes `vnzm27` warrants no code change at all, do not execute a trimmed version of this plan; supersede it and close the item on the records side, since F-3 and F-4 are this plan's entire justification.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then set backlog item `vnzm27` `done` with `--evidence` citing the executed plan. It carries `- Blocks-Release: next`, which this plan inherits via `- From-Backlog: vnzm27`, so the gate is preserved by that handoff and no separate de-gating is required (OQ-01). Item `axayfn` stays open and carries its own state; the unfiled readers listed under Deferred remain the reviewer's call (OQ-02).
