# IPD: Wire the four unwired gates and install the missing pre-push hook

- Date: 2026-09-08
- Kind: child
- Concern: Four of the six shipped gate verbs are invoked by NOTHING. `precommit-scope-gate`, `prepush-authorization-gate`, `backlog-blocking-close-gate` and `ipd-dependency-statement-gate` all exist as working `aw` verbs that print correct, actionable refusals when run by hand, and none of them appears in `.pre-commit-config.yaml`. Worse, the only installed git hook is `pre-commit`: there is NO `pre-push` hook at all, so `prepush-authorization-gate` cannot fire even in principle. A guard that is never invoked is not a guard, and the backlog item judges this "very likely a bigger real-world win than any new guard" precisely because the code already exists and works.
- Scope: Wiring and installation only, gate by gate, each with its intent CONFIRMED before it is turned on. IN: register the gates that should be always-on, install a `pre-push` hook stage so the push gate can fire, and keep every honest-limit disclosure intact. OUT: any new guard, any agent-context detection, and any change to what a gate DECIDES; also out is `backlog-blocking-close-gate` if its documented opt-in status is deliberate.
- Scope-Paths: .pre-commit-config.yaml, agent_workflows/engine.py, tests/test_gate_wiring.py
- Item-Dependencies: none
- Status: to-review
- Set: commitguard
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: kbqpkn
- From-Backlog: wjl471

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `wjl471`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none, despite `Priority: high`. THIS IS ORDER 01 OF A TWO-CHILD SET because the item contains two independently valuable, independently testable halves with different risk profiles: its FINDING 2 (four gates wired to nothing) is nearly free and touches no behavior, while its MAINTAINER RULING (the MUST wording plus plan-less `aw commit`) changes an installed contract and carries a HARD ORDERING CONSTRAINT. This child is the cheap half and depends on nothing. FINDING 2 RE-VERIFIED AT HEAD `a2e0438a` and it reproduces EXACTLY as filed: grepping `.pre-commit-config.yaml` gives `ipd-executed-gate` 1 occurrence and `ipd-status-untooled-gate` 2, while `precommit-scope-gate`, `prepush-authorization-gate`, `backlog-blocking-close-gate` and `ipd-dependency-statement-gate` each give ZERO. Also confirmed the sharper half of the finding: the ONLY installed hook in the repository's git dir is `pre-commit`, so there is no `pre-push` stage for the push gate to run in. CONFIRMED the honesty pattern the item says to reuse verbatim exists and is already written: `prepush_authorization_gate.py:4` calls itself "CONVENIENCE / FEEDBACK ONLY ... explicitly NOT an authority boundary" and `:62` prints the limit out loud ("a LOCAL, OPT-IN, bypassable (`--no-verify`) FEEDBACK hook, NOT an authority boundary"), and `precommit_scope_gate.py:67` carries the same disclosure. So this plan does not need to invent that wording; it needs to avoid weakening it while turning the gates on. ONE DELIBERATE EXCLUSION CARRIED FROM THE ITEM: it warns "do not assume 'unwired' means 'forgotten'" and specifically notes `backlog-blocking-close-gate` is documented as deliberately opt-in. AGENTS.md confirms that in the repository's own words: the hook "is NOT installed by default", is wired via `engine.create_backlog_close_gate_hook(repo, install=True)`, and its honest limits are stated there. So E-04 CHECKS each gate's intent rather than wiring all four reflexively, and the plan is explicit that wiring that one may be the wrong answer.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the gates that already work actually run. The whole value here is that four correct refusals currently reach nobody, and turning them on requires no new logic, no new detection and no behavior change inside any gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish intent before turning anything on

- [ ] E-01 For EACH of the four unwired gates, determine and record whether being unwired is DELIBERATE or an oversight, before wiring any of them. The item is explicit that this must not be assumed ("do not assume 'unwired' means 'forgotten'"), and at least one case is provably deliberate: `backlog-blocking-close-gate` is documented in AGENTS.md as "NOT installed by default", installed on demand via `engine.create_backlog_close_gate_hook(repo, install=True)`, with its local-only limits stated. Read each gate's module docstring and any plan or spec that introduced it, and produce a per-gate verdict with a citation. THE OUTPUT OF THIS ITEM IS A DECISION TABLE, and a gate whose exclusion turns out to be deliberate must NOT be wired by this plan.
  - Depends on: none
  - Expected outcome: a four-row table naming each gate, its intent verdict (wire / leave opt-in), and the citation behind that verdict.
  - Execution state: pending

- [ ] E-02 Confirm each gate is SAFE to run on every commit before making it always-on, because an always-on gate that false-positives is worse than an unwired one. The repository has a recorded instance of exactly that harm: backlog `gjadwm` observes that "a gate that false-positives on correct behavior TRAINS agents to bypass it", and its own case-2 false positive was resolved with `--no-verify` twice. So for each gate to be wired, run it BY HAND against the current tree and against a representative staged change, and record whether it passes clean. A gate that refuses a legitimate current state must be fixed or left unwired, not turned on with a known false positive.
  - Depends on: E-01
  - Expected outcome: for each gate to be wired, pasted evidence of a clean run against the real tree and against a legitimate staged change; any false positive named and its gate excluded.
  - Execution state: pending

### Task group 2: wire them

- [ ] E-03 Register the gates E-01 and E-02 cleared, in `.pre-commit-config.yaml`, following the shape the two ALREADY-WIRED local hooks use so the new entries are consistent rather than novel: `local` repo, `language: system`, `pass_filenames: false`, `always_run: true`, `entry: python3 -m agent_workflows <verb>`. Keep each hook's `id` equal to its verb name, as the existing two do, so the mapping from a failing hook to the command that reproduces it is obvious. Do NOT change any gate's own code in this plan: wiring is configuration, and a gate that needs a code change to be safely wired belongs in its own item (this is exactly the relationship between `precommit-scope-gate` and any scope-attribution work in flight).
  - Depends on: E-02
  - Expected outcome: the cleared gates appear in `.pre-commit-config.yaml` in the established local-hook shape, with no gate module modified.
  - Execution state: pending

- [ ] E-04 INSTALL THE `pre-push` STAGE, which is the half of Finding 2 that no amount of config alone fixes: measured at HEAD `a2e0438a`, the only installed hook in the repository's git dir is `pre-commit`, so `prepush-authorization-gate` cannot fire even when registered. Add `pre-push` to the installed hook types (pre-commit supports `default_install_hook_types`) and register the push gate for that stage specifically, not for `pre-commit`, since a push gate on every commit would refuse work that is not being pushed. NOTE the analogous precedent already exists in flight: approved plan `29wvmj` E-06 adds `default_install_hook_types: [pre-commit, pre-merge-commit]` to this same file to close an automated-merge hole. CHECK WHETHER IT HAS LANDED and EXTEND its list rather than replacing it; if the two edits collide, STOP and report rather than reverting a sibling's work.
  - Depends on: E-03
  - Expected outcome: `pre-push` is an installed hook type, the push gate runs on push and NOT on commit, and any existing `default_install_hook_types` entries are preserved.
  - Execution state: pending

- [ ] E-05 PRESERVE EVERY HONEST-LIMIT DISCLOSURE, which is the one caveat the item says still matters: "a bypassable guard must never be DESCRIBED as a boundary, because that is how a fail-open check comes to be trusted." Verify the disclosures already present survive wiring verbatim: `prepush_authorization_gate.py:4` ("CONVENIENCE / FEEDBACK ONLY ... explicitly NOT an authority boundary") and `:62` (the printed "LOCAL, OPT-IN, bypassable (`--no-verify`) FEEDBACK hook" limit), and `precommit_scope_gate.py:67` ("NOT an authority boundary - the authoritative gate is `aw check` in CI"). If wiring a gate makes any of those sentences misleading (for example a gate described as OPT-IN that is now always-on), UPDATE THE SENTENCE to stay true rather than leaving it, and say which ones changed.
  - Depends on: E-03, E-04
  - Expected outcome: every disclosure is still accurate after wiring; any sentence made untrue by wiring is corrected and named.
  - Execution state: pending

### Task group 3: prove it stays wired

- [ ] E-06 Add a test asserting every gate verb that SHOULD be wired IS wired, driven by an explicit declared list rather than by whatever the file happens to contain, so a future gate cannot be added and silently left unwired. This is the durable deliverable: the item's Finding 2 exists because four gates accumulated with nobody noticing. The test must enumerate the gate verbs, the stage each belongs to, and an explicit EXEMPTION list for any gate deliberately left opt-in (with the reason as a comment), then assert the config matches. Assert it FAILS against HEAD `a2e0438a` for the gates E-01 cleared.
  - Depends on: E-05
  - Expected outcome: a test that fails before wiring naming the missing gates, passes after, and carries a reviewable exemption list.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Two gates ARE wired and establish the shape for the rest: they are `local` hooks with `language: system`, `pass_filenames: false`, `always_run: true`, and an `entry` of `python3 -m agent_workflows <verb>`, with `id` equal to the verb name.
- The mutating hooks in this file carry a shared `exclude` regex covering only `.agents/docs/research/`, `.aw/records/docs/research/` and `.aw/system/`; the local gates are read-only refusals and rewrite nothing, which is why they need no exclusion.
- The honesty pattern the item wants reused is already implemented, not aspirational: both `prepush_authorization_gate` and `precommit_scope_gate` state their own limits in code and in their printed output.
- `backlog-blocking-close-gate` is DOCUMENTED as deliberately opt-in in AGENTS.md, installed via `engine.create_backlog_close_gate_hook(repo, install=True)` (idempotent, no-clobber). That is a decided position, not an oversight.
- The portable authority is `aw check` plus CI, not the local hooks: AGENTS.md states git hooks are local, not cloned by default, and skippable with `--no-verify`. Wiring a gate improves feedback; it does not create an authority.
- A false-positive gate is a recorded harm here: backlog `gjadwm` records that such a gate trains agents to bypass it, which is why E-02 precedes E-03.
- `default_install_hook_types` is the pre-commit mechanism for installing a non-default stage, and approved plan `29wvmj` E-06 is already using it in this same file for `pre-merge-commit`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | FINDING 2 REPRODUCES EXACTLY: `precommit-scope-gate`, `prepush-authorization-gate`, `backlog-blocking-close-gate` and `ipd-dependency-statement-gate` each appear ZERO times in `.pre-commit-config.yaml`, while `ipd-executed-gate` appears once and `ipd-status-untooled-gate` twice. | measured at `a2e0438a` |
| F-2 | The push gate cannot fire even if registered: the ONLY installed hook in the repository's git dir is `pre-commit`, so there is no `pre-push` stage. | `ls "$(git rev-parse --git-common-dir)/hooks/"` at `a2e0438a` |
| F-3 | The gates are working code, not stubs: each is a real `aw` verb, and the item records that running the push gate by hand prints a correct, actionable refusal. | the six verbs are registered CLI subcommands; `hooks/prepush_authorization_gate.py`, `hooks/precommit_scope_gate.py` |
| F-4 | The honesty disclosures the item wants preserved already exist verbatim in code. | `hooks/prepush_authorization_gate.py:4`, `:62`; `hooks/precommit_scope_gate.py:67` |
| F-5 | ONE gate's exclusion is DELIBERATE and documented, so wiring all four reflexively would contradict the repository's own stated design: `backlog-blocking-close-gate` "is NOT installed by default" and is wired on demand. | AGENTS.md's release-gates section |
| F-6 | A false-positive always-on gate is a recorded harm in this repository, which is why safety is checked before wiring. | backlog `gjadwm` ("a gate that false-positives on correct behavior TRAINS agents to bypass it") |
| F-7 | A SIBLING PLAN IS ALREADY EDITING THE SAME FILE for the same mechanism: approved plan `29wvmj` E-06 adds `default_install_hook_types: [pre-commit, pre-merge-commit]`, so E-04 must extend rather than replace. | `.aw/records/plans/pending/20260906-integpath-01-29wvmj-...ipd.md`, `- Status: approved` |
| F-8 | Nothing covers this item's Finding 2: no pending or approved plan wires these four gates. | grep over `.aw/records/plans/pending/` at `a2e0438a` |

## Proposed changes (ordered, validatable)

1. Produce a per-gate intent verdict with citations (E-01).
2. Prove each gate to be wired runs clean against the real tree (E-02).
3. Register the cleared gates in the established local-hook shape (E-03).
4. Install the `pre-push` stage and register the push gate there only (E-04).
5. Keep every honest-limit disclosure accurate after wiring (E-05).
6. Add a declared-list wiring test with a reviewable exemption list (E-06).

## Deferred / out of scope (with reason)

- THE NEW AGENT-DETECTING COMMIT GUARD (the item's Finding 1 and its OQ-1 through OQ-4). That is the item's larger half: it needs a decision on WHERE the guard lives, WHAT accident it catches, HOW it phrases the refusal, and HOW an override is recorded. None of that is needed to turn on four gates that already work, and the item itself says the wiring "may catch most of the remaining accidents at near-zero cost". Sibling Order 02 handles the contract half; the new guard needs its own item once the maintainer rules on OQ-1's shape.
- ANY CHANGE TO WHAT A GATE DECIDES. Wiring is configuration. A gate that needs a code change to be safely wired is excluded by E-02 rather than patched here.
- THE MUST WORDING AND PLAN-LESS `aw commit`. Sibling Order 02 (`y9vpvv`) owns those, because they change an installed contract and carry a hard ordering constraint on `egqt32`'s retry landing first.
- `mjx7ne`'s `commit_gateway` / `deny_push` HOST CAPABILITIES, which the item notes grep to zero enforcement. A separate open item; wiring them is not the same act as wiring these four gates.
- SETTING `AI_AGENT` OURSELVES IN THE DRIVERS (the item's observation (a)). Belongs with the detection design, not with gate wiring.

## Scope check

- Over-scope: `agent_workflows/engine.py` is in `Scope-Paths` because the installed-hook set and the backlog close-gate installer live there, so E-04 may need to touch it; if the `pre-push` stage can be installed entirely from `.pre-commit-config.yaml`, leave `engine.py` untouched and say so.
- Under-scope: the new guard, the contract wording, and the host capabilities are all out (see Deferred). This plan delivers only the near-free half of the item.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_gate_wiring.py` plus the existing test modules for any gate wired.
- `pre-commit run --all-files` before and after, pasting both results, since this plan changes what runs on every commit and a new always-on gate must not turn the tree red.
- A real push attempt against a throwaway remote (or `pre-commit run --hook-stage pre-push`) proving the push gate now fires, and a normal commit proving it does NOT fire on commit.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

No `.spec.md` file governs which hooks are installed, so none is edited and none is declared in `Scope-Paths`. AGENTS.md DOES document the gate posture, and two of its statements must stay true: that git hooks are local, not cloned by default and skippable, so the portable authority is `aw check` plus CI; and that `backlog-blocking-close-gate` is not installed by default. If E-01 concludes that last gate SHOULD become always-on, AGENTS.md's managed block is the authority that must change with it, and it must be regenerated through `engine.py` rather than hand-edited, which is why `engine.py` is already in `Scope-Paths`. `CONTRIBUTING.md` describes the hooks for contributors and should be checked for staleness after wiring; if it enumerates the installed hooks, it enters the fence.

## Open questions

### OQ-01: Should `backlog-blocking-close-gate` become always-on, or stay opt-in as documented?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, leaning STAY OPT-IN, and E-01 will produce the evidence either way. It is the one gate whose unwired state is DOCUMENTED as deliberate (F-5), so turning it on contradicts a written position rather than closing an oversight. The argument for turning it on: it delegates to the same `evaluate_blocking_close` predicate that backs `aw backlog set` and the `aw check` rules, so it cannot disagree with them, and its purpose is to catch the hand-edit bypass that stages a done+blocking item directly. The argument against: it gates only the `done` case, the portable authority is already the `aw check` rule plus CI, and an always-on hook for a narrow bypass adds cost to every commit. A maintainer ruling is cheap here and prevents this plan silently reversing a documented decision.

### OQ-02: Should `precommit-scope-gate` be always-on given that scope attribution is being actively changed?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE BY MEASUREMENT, which is exactly what E-02 requires. Scope attribution has in-flight work (approved plan `h9cn0y` attributes a scope audit to the execution's own commits), so a scope gate turned on now could refuse legitimate commits until that lands. RECOMMENDATION: run the gate by hand against the current tree and against several legitimate staged changes first; if it is clean, wire it, and if it false-positives, leave it unwired and record the blocking condition rather than shipping a known false positive, per F-6.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the four-row decision table with, for each gate, its intent verdict and the exact citation (file:line or AGENTS.md section) behind it. A verdict with no citation does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each gate to be wired, paste the by-hand run against the real tree (command, UNPIPED exit code, output) AND against a representative legitimate staged change. Name any gate that false-positived and show it was excluded rather than wired.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `.pre-commit-config.yaml` diff showing the new entries in the established local-hook shape, and paste `git diff --stat -- agent_workflows/hooks/` proving NO gate module was modified.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the installed hook list BEFORE (only `pre-commit`) and AFTER (including `pre-push`), paste a push attempt or `pre-commit run --hook-stage pre-push` showing the push gate FIRES, and paste an ordinary commit showing it does NOT fire there. State whether `29wvmj` had landed and paste the `default_install_hook_types` value showing its entries were preserved.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste each disclosure sentence as it stands AFTER wiring, and for each state whether it remained accurate or was corrected. If a gate described as OPT-IN became always-on, paste the corrected sentence.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the test's source showing the declared gate list, the per-stage expectation and the commented exemption list; paste its FAILING output against pre-change config naming the unwired gates; paste its passing result after. Paste `pre-commit run --all-files` before and after, and the bare `python3 -m pytest` summary line compared to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. A reviewer should note this is the CHEAP half of backlog item `wjl471`: it wires existing working code and adds no guard, no detection and no contract change. OQ-01 asks the maintainer not to let this plan silently reverse a documented opt-in decision.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD: this plan changes what runs on every commit in this repository, including its own, so run `pre-commit run --all-files` BEFORE committing the new config and never reach for `--no-verify` to land a gate-wiring change. `.pre-commit-config.yaml` is also being edited by approved plan `29wvmj`, so re-read it at execution time and compose rather than overwrite. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
