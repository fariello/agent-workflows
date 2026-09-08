# IPD: Reject an unparseable actor at the setter instead of wedging finalize after the lifecycle commit

- Date: 2026-09-08
- Kind: child
- Concern: `ipd_lint._HISTORY_ATTRIB_RE` captures a history line's actor with `\((?P<actor>[^)]*)\)`, so `[^)]*` stops at the FIRST closing paren and an actor containing parens never matches at all. `_newest_executed_history` then falls through to its bare-line branch and returns `("", "")`, so IPD-S406 reports an EMPTY actor and an EMPTY summary for a line where both are plainly present. Because IPD-S406 runs as POST-TRANSITION validation, the lifecycle COMMIT already exists when it fires, and finalize lands in COMMITTED-INCOMPLETE telling the operator to "re-run the SAME command to resume" - which cannot succeed, because the offending text is now in the file and the regex still cannot parse it. The only way out is hand-editing a plan already in `executed/`, which trips the executed-transition gate too, so one bad character class costs two gate bypasses.
- Scope: Fail FAST at the setter so the committed-incomplete state cannot be reached: reject a parenthesized `--actor` in the finalize paths, mirroring the guard that ALREADY exists in `retire_orchestrator` but is missing from the four real finalize paths. Also widen the regex so the corpus of already-written parenthesized lines parses, since a setter guard alone cannot fix a line that is already on disk. Reconcile the `Author` / `actor` spellings so the tooling stops teaching the shape the linter rejects.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_authoring.py, tests/test_ipd_lint.py, tests/test_ipd_lifecycle_cli.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: to-review
- Set: actorparen
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: fn2l1u
- From-Backlog: wwdm4g
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `wwdm4g`, inheriting its `Blocks-Release: next` gate. NOTHING IN THIS ITEM IS OBSOLETE and no pending or approved plan touches it: grepping the whole pending tree and the specs tree for `HISTORY_ATTRIB`, `actorparen`, and "parenthesized actor" returns nothing, and the regex's last change is `99760832`, the commit that introduced the attribution lint. VERIFIED AT HEAD `8b4e1570` by running it rather than reading it: `_HISTORY_ATTRIB_RE` does NOT match `- 2026-08-30 executed (opencode (its_direct/pt3-claude-opus-5-1m-us)): did the work`, DOES match the slash form and returns `actor='opencode/its_direct/pt3-claude-opus-5-1m-us'`, and the full cascade reproduces: the bare-line pattern `_HISTORY_LINE_RE` DOES match the parenthesized line and yields group(1) `'executed'`, which is exactly the fallthrough that makes `_newest_executed_history` return `("", "")` and IPD-S406 (`C_EXEC_ATTRIBUTION`) report an empty actor. ONE MATERIAL DISCOVERY THAT RESHAPES THE PLAN, and it is the reason this is a narrowing-and-widening rather than a transcription: THE SETTER GUARD THE ITEM ASKS FOR ALREADY EXISTS, BUT IN EXACTLY ONE PLACE THAT IS NOT THE PATH THAT WEDGED. `retire_orchestrator` (`ipd_lifecycle.py:2008`) refuses a parenthesized actor BEFORE mutating anything (`:2079-2091`), with a comment that diagnoses this precise defect and names `oc_runipd.driver_actor` as the `key=value` precedent. I enumerated every finalize entry point and NONE of them carries that guard: `finalize_precheck` (`:1317-1477`), `finalize` (`:2241-2380`), `_finalize_transaction` (`:2380-2609`), `run_finalize` (`:2929-3054`) - all four report `paren-guard: False`. So the fix is to LIFT AN EXISTING, ALREADY-REVIEWED GUARD to the paths that need it, not to invent one. SECOND MEASUREMENT, which justifies keeping the item's option 1 alongside its option 2: 274 of 536 tracked plans carry a parenthesized `- Author:` (for example `Antigravity (Gemini 1.5 Pro)`, `assess-documentation workflow (agent)`), so the shape the tooling teaches is present in more than half the corpus. A setter guard prevents NEW wedges but cannot parse a line already written, which is why E-03 widens the regex too.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a formatting mistake in the actor string a refusal BEFORE the commit instead of a wedged transaction after it. The specific harm is not the lint finding: it is that a post-commit formatting rule converts a typo into a state whose own recovery instruction cannot work, and whose real recovery requires two `--no-verify` bypasses.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: refuse before the commit (the item's option 2)

- [ ] E-01 Lift the EXISTING parenthesized-actor refusal from `retire_orchestrator` (`agent_workflows/ipd_lifecycle.py:2079-2091`) into a single shared helper, and call it from the finalize path that actually mutates. Do NOT write a second copy of the check: the existing one is already reviewed, already carries the diagnostic message explaining the `\(([^)]*)\)` capture, and already points at the `key=value` remedy, so duplicating it would create two definitions of "valid actor" that can drift. Put the helper next to the other lifecycle validators and have `retire_orchestrator` call it too, so its behavior is byte-identical afterwards. Validate the actor BEFORE any journal write or file move: the whole point is that the refusal must precede the mutation. THE EXISTING BEHAVIOR IS PINNED BY A TEST that must keep passing UNMODIFIED: `tests/test_orchestrator_retirement.py:1624` (`test_a_parenthesized_actor_is_refused_BEFORE_any_mutation`) asserts `EXIT_CANNOT_RUN`, that the message contains `parenthesis`, that the plan file is untouched, and that HEAD did not move; its siblings at `:1593` (`test_the_actor_passes_the_attribution_lint`) and `:2010` (`test_an_empty_actor_is_refused`) constrain the same helper.
  - Depends on: none
  - Expected outcome: one shared actor validator; `retire_orchestrator`'s message and exit code are unchanged and its three existing actor tests pass unmodified; a parenthesized `--actor` is refused with a nonzero exit and NOTHING written.
  - Execution state: pending

- [ ] E-02 Call the validator from EVERY finalize entry point that accepts `--actor`, verified by enumeration rather than by picking the obvious one. Measured at HEAD `8b4e1570`, four functions handle finalize and NONE guards the actor: `finalize_precheck` (`:1317-1477`), `finalize` (`:2241-2380`), `_finalize_transaction` (`:2380-2609`), and `run_finalize` (`:2929-3054`), which is the CLI entry that reads `actor = getattr(args, "actor", None)` at `:2946`. The earliest honest refusal point is the one a caller reaches first, so guard at `run_finalize` (the CLI boundary) AND inside the transaction (so a programmatic caller cannot bypass it); a guard in only one of the two leaves either the CLI or the API unprotected. Note `_finalize_transaction` builds the history line by handing `actor` to `_ss.apply_status_change` via `argparse.Namespace(actor=actor, ...)` (`:2510`), which is the exact write this must precede.
  - Depends on: E-01
  - Expected outcome: a parenthesized actor is refused at both the CLI and the programmatic boundary, with no journal, no status write, no move, and no commit; demonstrated separately for each entry point.
  - Execution state: pending

### Task group 2: make the already-written corpus parse (the item's option 1)

- [ ] E-03 Widen `_HISTORY_ATTRIB_RE` (`agent_workflows/ipd_lint.py:179-181`) so a parenthesized actor PARSES, because a setter guard cannot repair a line already on disk and 274 of 536 tracked plans carry the parenthesized shape in `- Author:` that agents copy into `--actor`. Today the pattern is `^-\s+(?:\d{4}-\d{2}-\d{2})\s+(?P<status>\S+)\s+\((?P<actor>[^)]*)\)\s*:\s*(?P<msg>.*)$`. Anchor the actor capture on the TRAILING `):` instead of on the first `)`, as the item's option 1 suggests, and MIND THE HAZARD THE ITEM NAMES: a greedy capture must not swallow a `):` that occurs inside the SUMMARY. Test that hazard explicitly with a line whose message itself contains `):` (for example `- 2026-09-08 executed (opencode/model): fixed foo(bar): baz`), and confirm the actor is still `opencode/model` and the message is intact. Do NOT loosen the date or status portions of the pattern while here.
  - Depends on: none
  - Expected outcome: the parenthesized actor line from the item's sighting 1 parses with the full actor and full message; the slash form parses byte-identically to today; a message containing `):` is not truncated and does not shift the actor boundary.
  - Execution state: pending

- [ ] E-04 Verify the WHOLE TRACKED CORPUS still lints the same after E-03, because widening a regex that feeds a repository-wide rule can silently change findings on 536 files. Run the attribution rule across every tracked plan BEFORE and AFTER and diff the finding sets. Two outcomes are acceptable and must be distinguished in the evidence: findings that DISAPPEAR because a real actor now parses (the intended effect), and findings that APPEAR (which would be a regression and must be explained or fixed). Pay specific attention to `_GENERIC_ACTORS` (`ipd_lint.py:184`), which rejects `aw set` and `aw set, --by-human`: a widened capture must not start matching a longer string that accidentally evades that check, nor start rejecting an actor it previously accepted.
  - Depends on: E-03
  - Expected outcome: a before/after finding-set diff over all tracked plans, with every change classified as intended or fixed, and the `_GENERIC_ACTORS` rejection demonstrated still working.
  - Execution state: pending

### Task group 3: stop the tooling teaching the broken shape

- [ ] E-05 Reconcile `Author` and `actor` so the two surfaces stop disagreeing silently (the item's option 4). `aw ipd scaffold --author` accepts and preserves a parenthesized string (`agent_workflows/ipd_authoring.py`), and 274 tracked plans carry one, so an agent that copies its own `- Author:` into `--actor` produces a line the linter cannot parse; the divergence is only discovered AFTER a commit. Decide ONE documented spelling and make the authoring surface emit it. RECOMMENDED, and cheap: have `scaffold` NORMALIZE a parenthesized author to the `key=value`/slash shape `driver_actor` already uses (`oc_runipd.py:853-874`, whose docstring states the parenthesis-free rule and renders the model as `model=<model>`), so the form the tooling produces is the form the linter accepts. Do NOT retroactively rewrite the 274 existing `- Author:` lines: they are not what breaks (only `--actor` reaches the history line), and E-03 makes the parenthesized form parse anyway.
  - Depends on: E-01
  - Expected outcome: `aw ipd scaffold --author "X (Y)"` writes an author in the accepted shape, or refuses with the same guidance the actor validator gives; the choice is recorded in a comment; no existing plan file is rewritten.
  - Execution state: pending

- [ ] E-06 Sweep for OTHER readers of the actor before declaring this done, so the fix does not merely move the incompatibility (the item's option 5). Find every consumer that parses an actor out of a history line, not just the lint rule: at minimum check `ipd_lint._newest_executed_history` (`:825-841`, the fallthrough that produces `("", "")`), `_check_terminal_attribution` (`:844+`), `plan_readiness`'s history helpers, and anything reading `## Workflow history` for attribution. For each, state whether it breaks on the parenthesized form, the slash form, or neither. THIS ITEM IS A READ-AND-REPORT OBLIGATION with a code consequence only where a second reader is found to be broken; if one is, either fix it here or record it as a follow-up with its symbol named. Do not skip it: the item lists this as a precondition for choosing between options, and two independent agents already hit the first reader.
  - Depends on: E-03
  - Expected outcome: an enumerated list of actor readers with a per-reader verdict against both spellings, and either a fix or a named follow-up for any additional broken reader.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE GUARD ALREADY EXISTS, IN ONE PLACE ONLY. `retire_orchestrator` (`ipd_lifecycle.py:2008`) refuses a parenthesized actor at `:2079-2091`, before any mutation, with a message that explains the regex capture and names `oc_runipd.driver_actor` as the remedy. It is the model for E-01 and must not be duplicated.
- The `key=value`, parenthesis-free actor convention is established and documented in `driver_actor` (`oc_runipd.py:853-874`), which renders the model as `model=<model>` and appends `variant=` and `profile=` the same way, explicitly so the attribution capture cannot misparse it.
- IPD-S406's constant is `C_EXEC_ATTRIBUTION`, and the rule reads ONLY the newest `executed` history entry, so the defect is scoped to the terminal transition rather than to history generally.
- `_newest_executed_history` (`:825-841`) has a deliberate bare-line branch that returns `("", "")` so a bare `executed` line is FLAGGED rather than skipped. That design is correct; the bug is that a parenthesized line reaches it at all.
- `_GENERIC_ACTORS` (`:184`) is pinned NARROWLY on purpose (only the `aw set` defaults) with an explicit instruction not to expand it to bare tool or human names. E-04 must not disturb it.
- The finalize transaction is two-phase with a journal and explicit phases, and post-transition validation runs AFTER the lifecycle commit by design (`PHASE_COMPLETE` at `:143`). That ordering is why a lint-class failure becomes a wedged transaction, and it is why this plan fixes the input rather than the ordering (see Deferred).
- The item's INTERIM GUIDANCE is verified and worth preserving in the refusal message: the slash form `opencode/its_direct/<model>` parses, and `z2isfg` was finalized with it cleanly.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The regex genuinely cannot match a parenthesized actor: `[^)]*` stops at the first `)`. Measured, not read. | `ipd_lint.py:179-181`; measured `_HISTORY_ATTRIB_RE.match(...)` -> False for the parenthesized line, True for the slash form at `8b4e1570` |
| F-2 | The cascade to an EMPTY actor reproduces exactly as the item describes: the bare pattern matches the same line and yields group(1) `'executed'`, which is the fallthrough returning `("", "")`. | measured `_HISTORY_LINE_RE.match(...)` at `8b4e1570`; `ipd_lint.py:825-841` |
| F-3 | THE SETTER GUARD ALREADY EXISTS but only in `retire_orchestrator`, whose comment diagnoses this precise defect and names the `key=value` remedy. | `ipd_lifecycle.py:2008` (function), `:2079-2091` (the guard) |
| F-4 | NONE of the four real finalize paths guards the actor, verified by enumerating each function body: `finalize_precheck` `:1317-1477`, `finalize` `:2241-2380`, `_finalize_transaction` `:2380-2609`, `run_finalize` `:2929-3054`, all `paren-guard: False`. | measured at `8b4e1570` |
| F-5 | The unguarded actor reaches the history writer directly: `_finalize_transaction` passes it to `apply_status_change` through `argparse.Namespace(actor=actor, ...)`. | `ipd_lifecycle.py:2510` |
| F-6 | The CLI reads the actor with no validation. | `ipd_lifecycle.py:2946` |
| F-7 | THE TRAP IS SYSTEMIC, which is why the regex must widen and not only the setter guard: 274 of 536 tracked plans carry a parenthesized `- Author:` (e.g. `Antigravity (Gemini 1.5 Pro)`, `assess-documentation workflow (agent)`). | measured `git ls-files '.aw/records/plans/*.ipd.md' \| xargs grep -l '^- Author:.*('` at `8b4e1570` |
| F-8 | NOTHING covers this item: no pending or approved plan and no spec mentions `HISTORY_ATTRIB`, `actorparen`, or a parenthesized actor. | grep over `.aw/records/plans/pending/` and `.aw/records/specs/` at `8b4e1570` |
| F-9 | The regex has not changed since the attribution lint was introduced, so the defect has been live for its whole life. | `git log -S` on the pattern -> single commit `99760832` |
| F-10 | The parenthesis-free convention is already documented and implemented on the runner side, so E-05's normalization has a precedent to copy rather than a new convention to invent. | `oc_runipd.py:853-874` |
| F-11 | The failure was observed TWICE by two different agents on the same day, one of whose in-flight fix was never committed and would have been reintroduced by merging its lane. That is what makes it a shape the tooling invites rather than one agent's typo. | backlog `wwdm4g`, "THE TWO SIGHTINGS" |

## Proposed changes (ordered, validatable)

1. Extract the existing parenthesized-actor refusal into one shared validator (E-01).
2. Call it from both the CLI and the programmatic finalize boundaries (E-02).
3. Widen the attribution regex so already-written parenthesized lines parse, without swallowing a `):` in the summary (E-03).
4. Diff the attribution findings across all 536 tracked plans before and after (E-04).
5. Make `scaffold` emit an author in the shape the linter accepts (E-05).
6. Enumerate every other actor reader and report a per-reader verdict (E-06).

## Deferred / out of scope (with reason)

- MOVING IPD-S406 TO RUN BEFORE THE LIFECYCLE COMMIT (the item's option 3). This is the deepest framing and the item is right that a post-commit formatting rule is the underlying design smell, but reordering the two-phase finalize transaction is a change to the transaction's own contract, with rollback and journal-phase consequences, and it would not be validated by anything this plan tests. Fixing the INPUT (E-01/E-02) removes the reachable path to the wedge; reordering the gate is a separate, larger design item.
- REWRITING THE 274 EXISTING PARENTHESIZED `- Author:` LINES. They are not the defect: only `--actor` reaches the terminal history line, and E-03 makes the parenthesized form parse regardless. A 274-file rewrite would be pure churn with a real chance of collateral damage.
- EXPANDING `_GENERIC_ACTORS`. Pinned narrowly on purpose with an explicit instruction not to widen it to bare tool or human names. E-04 only proves it still works.
- FIXING THE EXECUTED-TRANSITION GATE bypass this defect cascades into. That is backlog `gjadwm`, whose case 2 is graduated separately as plan `i4c0c3` in this same batch, and whose case 1 is owned by approved plan `29wvmj`. Once either lands, recovering from a wedge stops needing the second bypass; this plan removes the need for the FIRST one.
- THE SIBLING RECEIPT/JOURNAL DEFECTS the item groups with this one (`xmqv5l`, `v880xk`). Separate open items outside this plan's ownership. The item's argument that the finalize-evidence model deserves one coherent review is reasonable but is a different piece of work.

## Scope check

- Over-scope: `agent_workflows/ipd_authoring.py` is in `Scope-Paths` for E-05, which implements the item's option 4 rather than its core defect. It is included because the item identifies the `Author`/`actor` divergence as the REASON agents keep writing the broken form, so fixing only the symptom would leave the generator of the mistake in place. A reviewer may cut E-05 without affecting E-01 through E-04.
- Under-scope: the gate-ordering redesign, the 274-line rewrite, and the cascading gate bypass are all left alone (see Deferred).

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_ipd_lint.py tests/test_ipd_lifecycle_cli.py tests/test_orchestrator_retirement.py` for the focused surface. NOTE the baseline already carries one KNOWN failure in `test_orchestrator_retirement.py` (`test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`); it is pre-existing and unrelated, so judge that module on the delta and do NOT claim to have fixed or broken it.
- A REAL end-to-end refusal: run `aw ipd finalize` with a parenthesized `--actor` against a fixture plan and show it exits nonzero having created no journal, no move, and no commit (`git status --porcelain` and `git log -1` before and after).
- The corpus finding-set diff from E-04 over all 536 tracked plans.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`), since a piped `$?` reports the last pipeline stage.

## Spec / documentation sync

The IPD spec defines the `## Workflow history` line grammar `- <date> <status> (<actor>): <msg>` that this plan's regex implements, so E-03 changes only WHAT THE READER ACCEPTS, never the documented grammar: the parenthesized-actor line is already legal under that grammar and the reader was simply too strict. No `.spec.md` file is therefore edited and none is declared in `Scope-Paths`. IF the executor concludes the grammar itself must state a parenthesis rule for the actor, that IS a spec amendment: declare the spec path in `Scope-Paths` BEFORE editing it and say why in this section, per the plan-may-amend-a-spec rule. The refusal message added by E-01/E-02 is operator-facing documentation in its own right and must name the accepted shape (the slash form is verified to parse) rather than only rejecting the bad one.

## Open questions

### OQ-01: Should the regex widen (E-03) as well as the setter refusing (E-01/E-02), or is the setter guard alone enough?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED IN FAVOUR OF BOTH, on evidence, and recorded so a reviewer can disagree cheaply. A setter guard alone prevents NEW wedges but cannot parse a line already written, and lines are already written: sighting 1 in the item ended with a parenthesized line committed into an executed plan, and 274 of 536 plans carry the same shape in the field agents copy from. A regex widening alone would fix parsing but still let an agent write a form the convention discourages. Doing both means new actors are clean AND old lines are readable. If a reviewer prefers the setter alone, E-03/E-04 can be cut, at the cost of leaving any already-committed parenthesized terminal line permanently unparseable.

### OQ-02: Should `scaffold` NORMALIZE a parenthesized `--author` or REFUSE it?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, with normalization recommended. Refusing is more consistent with E-01's fail-fast stance, but `--author` is a cosmetic frontmatter field that breaks nothing on its own, so refusing it would fail a harmless call and annoy every author for a defect that lives elsewhere. Normalizing quietly makes the tooling stop teaching the broken shape without penalizing anyone. The counter-argument a maintainer may prefer: silent normalization means the author string a user typed is not the one recorded, which is a small surprise of its own. Either choice satisfies E-05; the plan does not depend on which.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new shared validator's source, and paste `git diff` of `retire_orchestrator` showing it now CALLS the helper. Prove `retire_orchestrator`'s behavior is unchanged by pasting its refusal message and exit code before and after (they must be identical strings). Paste a grep proving there is exactly ONE definition of the paren check in the package.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for EACH guarded entry point separately, paste the invocation with a parenthesized `--actor`, its UNPIPED exit code, the refusal text, AND proof nothing was written: `git status --porcelain` unchanged, `git log -1` unchanged, and no finalize journal present (`ls` the journal path). One combined demonstration does not satisfy this item, because the CLI and programmatic boundaries are separate holes.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a snippet's output showing the widened pattern parsing all THREE cases with their captured groups: the parenthesized actor from the item's sighting 1 (full actor, full message), the slash form (byte-identical to today's capture), and the hazard case whose MESSAGE contains `):` (actor unchanged, message not truncated). Paste the old and new pattern side by side.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the BEFORE and AFTER attribution-finding counts over all tracked plans and the DIFF of the finding sets, with each change classified as intended (a real actor now parses) or a regression (and how it was fixed). Paste a test showing `_GENERIC_ACTORS` still rejects `aw set` and `aw set, --by-human` under the new pattern.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw ipd scaffold --author "opencode (its_direct/model)"` and the resulting `- Author:` line, showing either the normalized shape or a refusal carrying the same guidance as the actor validator. Paste the comment recording the OQ-02 choice. Paste proof no existing plan file was rewritten (`git status --porcelain` limited to `.aw/records/plans/`).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the enumerated list of actor readers found (with symbol and file:line for each) and, for each, the measured verdict against BOTH the parenthesized and slash forms. Where a second broken reader was found, paste either its fix or the named follow-up. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. A reviewer should note the plan's central discovery: the guard the item asks for already exists in `retire_orchestrator` and is simply missing from the four paths that matter (F-3, F-4), so E-01/E-02 lift reviewed code rather than inventing a rule.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD: this plan changes the actor validation that its OWN `aw ipd finalize` will run, so use the slash form for its own finalize and never reach for `--no-verify`, which is the habit this plan exists to remove. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
