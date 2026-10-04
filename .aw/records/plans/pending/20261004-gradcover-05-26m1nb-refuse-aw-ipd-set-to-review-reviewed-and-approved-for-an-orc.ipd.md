# IPD: Refuse aw ipd set to-review, reviewed and approved for an orchestrator that is not ready

- Date: 2026-10-04
- Kind: child
- Concern: `- Status: to-review` is defined as "complete enough to critique" (`.aw/records/plans/README.md`), but for an orchestrator plan nothing checks that when the status is written. `status_set.run_set_command` validates transition legality, approval attestations, terminal-reopen and the finalize delegation; it never asks whether an orchestrator's children exist, are ready, or cover the work. So 13 orchestrators sit at `to-review` that the runner refuses on sight. Spec `77tr3o` R-13 and spec `25kzda` 2.5d (both added by Order 01) require `aw ipd set` to refuse a `to-review`, `reviewed`, `approved` or `auto-approved` target on an orchestrator that fails the shared check. Separately, `aw ipd scaffold --kind orchestrator` already writes `- Status: draft` (measured 2026-10-03), but a Set-wide `aw ipd set to-review <setid>` processes plans in an order where the orchestrator may be checked before its children have moved, which would refuse a valid one-command transition. Finally, an orchestrator found not ready cannot be sent back to authoring at all: `ipd_lifecycle.validate_transition('to-review', 'draft')` returns `ok=False` ("missing predecessor") because `_LEGAL_BACKWARD_EDGES` enumerates only `approved -> reviewed`, `auto-approved -> reviewed` and `reviewed -> to-review`; spec `ipd-spec` as amended by Order 01 (E.1) makes every backward move between non-terminal statuses legal, provided it is loud (reason required, warning printed, `APPROVAL WITHDRAWN` recorded when leaving `approved`).
- Scope: IN: in `status_set.run_set_command`, for every matched plan record whose `- Kind:` is `orchestrator` and whose normalized target is `to-review`, `reviewed`, `approved` or `auto-approved`, call `orchestrator_readiness.review_readiness(..., ask=False)` and refuse with the shared human rendering or `aw.agent/v1` record; when the selection includes both an orchestrator and some of its children, apply the children first and evaluate the orchestrator after them in the same invocation; refuse the whole invocation atomically if the orchestrator then fails (no partial write); make every backward move between non-terminal statuses legal in `ipd_lifecycle._LEGAL_BACKWARD_EDGES`, requiring a reason and warning loudly on each; a regression test. OUT: backward transitions (`reviewed -> to-review` etc. remain allowed unconditionally so a plan can always be sent back); the `draft` target; any non-plan record type; terminal transitions (the finalize delegation is unchanged); the scaffold (it already writes `draft` for both kinds, which this plan pins with a test rather than changes).
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/ipd_lifecycle.py, tests/test_orchestrator_status_gate.py
- Item-Dependencies: executed:qs00nc
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 5
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 26m1nb

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 05 of Set `gradcover`. Implements spec `77tr3o` R-13 and `25kzda` 2.5d's `aw ipd set` consumer as amended by Order 01. The maintainer asked that the refusal be "VERY PRECISE, AGENT and human FRIENDLY", explaining why and what to do; the message text is the shared remedy data from Order 03 so every surface says the same thing.

## Goal

Make it impossible to record an orchestrator plan as ready for review, reviewed or approved through the setter while its Set is not ready, with a refusal that names each failing child or passage and the exact command or edit that fixes it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the gate

- [ ] E-01 In `status_set.run_set_command`, after records are matched and transition legality is validated and before any file is written, identify matched plan records with `- Kind: orchestrator` (read from the metadata block through `ipd_lint.parse`, never a whole-file substring scan) whose normalized target is one of `to-review`, `reviewed`, `approved`, `auto-approved` AND is a forward move from the current status. For each, evaluate `orchestrator_readiness.review_readiness(repo_root, path, ask=False)` as it WOULD be after the invocation's other matched records are applied (E-02). If any orchestrator is not ready, write nothing for ANY record in the invocation, print the shared human rendering per orchestrator (or the `aw.agent/v1` record under `--agent`/`--json`), and exit 1.
  - Depends on: none
  - Expected outcome: `aw ipd set to-review <orchestrator>` on a fixture whose child is `draft` exits 1, writes nothing, and prints a line naming the child id6 and `aw ipd set to-review <child-id6>`; the same on a ready fixture with a recorded pass verdict succeeds.
  - Execution state: pending

- [ ] E-02 Make the evaluation in E-01 see the invocation's pending child transitions: when the matched records include children of the orchestrator (same `- Set:`), compute the children's post-transition statuses and pass them to `review_readiness` as an override map (add a keyword parameter to the Order 03 function if needed, defaulting to none, so the function stays the single implementation), so `aw ipd set to-review <setid>` succeeds in one command when the only thing missing was the children's own status. Process the writes children first, orchestrator last.
  - Depends on: E-01
  - Expected outcome: `aw ipd set to-review <setid>` over a fixture Set whose children and orchestrator are all `draft` and otherwise ready (with a recorded pass) succeeds and writes all of them; with one child failing lint, it writes none and names that child.
  - Execution state: pending

- [ ] E-03 Leave backward and same-status moves alone: a target that is not a forward move into the ready statuses (for example `approved -> reviewed`, `reviewed -> to-review`, any move to `draft`) is never refused by this gate, so a plan can always be sent back for rework.
  - Depends on: E-02
  - Expected outcome: `aw ipd set to-review <orchestrator>` from `reviewed` on a not-ready fixture succeeds (a legal backward move); `aw ipd set draft <orchestrator>` always succeeds.
  - Execution state: pending

- [ ] E-05 Implement spec `ipd-spec` as amended by Order 01 (E.1): replace `ipd_lifecycle._LEGAL_BACKWARD_EDGES` with every backward pair among `draft`, `to-review`, `reviewed`, `approved`, `auto-approved` (terminal statuses untouched); in `status_set.run_set_command`, require `--message` for any backward plan move (refuse with exit 2 and the exact flag to add when it is missing), print a warning line `DEMOTED <id6>: <from> -> <to>: <reason>` (adding `APPROVAL WITHDRAWN` when the source is `approved` or `auto-approved`) on the human surface and a `warning` record on the agent surface, and write the history line `demoted <from> -> <to>: <reason>` (with `APPROVAL WITHDRAWN` when applicable). Keep the terminal-reopen guard unchanged.
  - Depends on: E-03
  - Expected outcome: `aw ipd set draft <approved plan> --message "<why>"` succeeds, warns and records `APPROVAL WITHDRAWN`; the same without `--message` is refused naming `--message`; `aw ipd set approved <executed plan>` is still refused by the terminal-reopen guard.
  - Execution state: pending

### Task group 2: pin it

- [ ] E-04 Add `tests/test_orchestrator_status_gate.py` driving `python3 -m agent_workflows ipd set` as a subprocess against fixture repositories under `tempfile` (records backend `repository`), with probe verdicts pre-recorded into the fixture's verdict store through `record_probe_verdict` (never a model call). Cases: each of the four forward targets refused for a not-ready orchestrator; the human output contains the child id6 or quoted passage and the remedy command, and does not suggest deleting the checklist; the `--agent` record validates with `agent_schema.validate_agent_record` and carries no absolute path; nothing on disk changed after a refusal (compare file bytes before and after); the one-command Set transition of E-02 in both its succeed and refuse forms; the no-loop case of OQ-03 (promote, demote, then a second promotion on unchanged text refused); the backward and `draft` moves of E-03; the E-05 cases (each backward pair legal with `--message`, refused without it, `APPROVAL WITHDRAWN` recorded when leaving `approved`, a terminal reopen still refused); a non-orchestrator child plan unaffected; and `aw ipd scaffold --kind orchestrator` (dry run) still emits `- Status: draft`. Prove the test can fail by disabling the gate and pasting the failure.
  - Depends on: E-05
  - Expected outcome: the new file passes; the mutation fails it; no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- READ `- Kind:` FROM THE METADATA BLOCK, never by substring. `status_set` has a fallback `"- Kind: orchestrator" in text` type sniff for unplaced files; the `/plan-review` workflow warns that a whole-file scan misclassifies child plans that quote the bullet (`m7gvuz`). Use `ipd_lint.parse(text).meta_fields["Kind"]`, as `status_set` already does for other metadata through `ipd_lint.parse`.
- THE SETTER IS ATOMIC PER INVOCATION FOR OTHER GATES. The terminal-reopen guard refuses the whole invocation and lists every offending plan before writing (`setterguard 4bc1nd` block); follow the same all-or-nothing shape.
- LEGAL BACKWARD EDGES ARE DEFINED ONCE in `ipd_lifecycle._LEGAL_BACKWARD_EDGES`; consult it through the existing predicate rather than re-listing.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | No orchestrator gate exists in the setter. `run_set_command` contains gates for plan `executed` (delegated to finalize), terminal reopen (`setterguard 4bc1nd`), approval attestation (`apprvguard d7bnhc`, inside `validate_transition_allowed`), and descriptive-field safety; none reads the child table or the verdict store. | the gate blocks in `run_set_command` and `validate_transition_allowed` |
| F-02 | The scaffold already writes `draft` for both kinds. `aw ipd scaffold --kind orchestrator` and `--kind child` dry runs on 2026-10-03 both printed `- Status: draft` and the history line `draft (<author>): created.` | the two dry-run outputs |
| F-03 | Graduation writes plans directly rather than via `aw ipd set`, so the production path is gated separately by Order 06; this plan covers the setter, `aw ipd lint` covers hand edits (Order 03's `IPD-S408` at `review-finalize`/`pre-execution`), and the runner refuses at retirement (Order 04). Those three together close the bypass the maintainer named ("agent instructions as well"). | `build_backlog_production_prompt` tells the agent to use `aw ipd scaffold`, then the agent edits the file; no `aw ipd set` call is required by the prompt |

## Proposed changes (ordered, validatable)

1. Add the orchestrator readiness gate to `run_set_command`, all-or-nothing, using the shared check and its rendering (E-01).
2. Evaluate against the invocation's pending child statuses, children first (E-02).
3. Exempt backward and `draft` moves (E-03).
4. Make every non-terminal backward move legal, reasoned and loud (E-05).
5. Subprocess tests with pre-recorded verdicts and a mutation proof (E-04).

## Deferred / out of scope (with reason)

- GATING `aw set` (the generic cross-type setter) separately. It routes plan records through the same `run_set_command`, so the gate applies to both spellings with no extra code; E-04 includes one `aw set to-review <orchestrator>` case to prove it.
  - Carrier-Declined: covered by construction and tested here
- THE PRODUCTION PATH. Order 06.
  - Carrier: r2wa38
- THE BACKLOG AND SPEC SETTERS. Order 10.
  - Carrier: sbiv1j

## Scope check

- Over-scope: none. Two production modules (the setter and the edge table) and one test file. A keyword parameter may be added to the Order 03 function for E-02; if so, that edit is in `agent_workflows/orchestrator_readiness.py`, which is NOT in this plan's Scope-Paths and must be justified at finalize with `--scope-reason`.
- Under-scope: after this plan, 13 orchestrators already at `to-review` remain so; the setter only gates new transitions. Order 09 handles them.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_orchestrator_status_gate.py tests/test_status_set.py tests/test_orchestrator_readiness.py tests/test_ipd_lifecycle_backward_edges.py -q` pasted.
- Mutation run pasted.
- On the real tree, paste `python3 -m agent_workflows ipd set reviewed axozpe --dry-run` (or the setter's preview mode) showing the refusal names `axozpe`'s quoted passages; if the setter has no dry-run, run it in a throwaway copy of the repository and paste the output, then discard the copy.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `77tr3o` R-13, spec `25kzda` 2.5d (setter consumer) and spec `ipd-spec`'s enumerated backward edges (E.1), all as amended by Order 01. No spec edited here. `.aw/records/plans/README.md` describes `to-review` as "complete enough to critique"; that definition is now enforced for orchestrators and needs no wording change. Order 11 updates the authoring guidance.

## Open questions

### OQ-01: Should an absent coverage verdict refuse the setter, or should the setter ask the probe itself?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: REFUSE, and name `aw ipd coverage <id6>` as the remedy. A status setter that spends a model call (and may take minutes) is surprising and makes `aw ipd set` network-dependent. `aw ipd coverage` is the explicit, one-time cost, after which the setter reads the recorded verdict. This matches `25kzda` 2.5d, which lists only the production action and `aw ipd coverage` as consumers that may ask.

### OQ-03: Can a loud demotion start a promote/demote loop?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: NO, by construction, which the maintainer required (2026-10-04: demote loudly "so long as we ensure that the system does not get stuck in a demotion loop"). For an orchestrator, this plan's promotion gate and Order 09's demotion both call the one readiness function over the one verdict cached against the plan's text, so for unchanged text it cannot both allow promotion and require demotion; a second move needs an edit. No runner writes `approved` (`25kzda` 4.5), so an automated demotion is never followed by an automated re-approval, and `--full-auto`'s `auto-approved` is gated by the same check through `IPD-REVIEW-ORCHESTRATOR-READY` (Order 07). E-04 pins this with a test that runs promote then demote then promote on unchanged text and asserts the second promotion is refused.

### OQ-02: Should a Set-wide transition write the children even when the orchestrator is refused?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: NO, all or nothing. A partial write would leave children `to-review` under a `draft` orchestrator with no record of why, which is harder to recover from than a refusal that changed nothing. The shipped terminal-reopen guard takes the same shape.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `run_set_command`. Paste test output for the four refused targets, one human refusal text in full, and the file-bytes-unchanged assertion passing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the one-command Set transition test in both forms, showing all files written in the success case and none written in the refuse case, with the refusal naming the failing child.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the backward-move and `draft`-move test output showing success on a not-ready fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test file passing with its count; the `aw set` (generic setter) case passing; the scaffold `draft` case passing; the mutation failing and the revert passing; a grep for source-structure reads returning nothing; the real-tree refusal for `axozpe`. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the three declared paths (plus `orchestrator_readiness.py` if E-02 needed it, with its scope reason).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of `_LEGAL_BACKWARD_EDGES` and of the setter's backward-move handling. Paste `validate_transition` results for every backward pair (all ok) and for `executed -> approved` (refused). Paste one `aw ipd set draft <approved fixture> --message ...` run showing the `DEMOTED ... APPROVAL WITHDRAWN` warning and the history line, and the same run without `--message` refused. Paste `tests/test_ipd_lifecycle_backward_edges.py` passing, updated if it pinned the old three-edge set (name the changed assertion).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
