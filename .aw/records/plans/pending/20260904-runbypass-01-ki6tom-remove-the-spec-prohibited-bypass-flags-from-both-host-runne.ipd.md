# IPD: remove the spec-prohibited bypass flags from both host runners

- Date: 2026-09-04
- Kind: child
- Concern: Spec `25kzda` 2.1 states flatly, as a one-line prohibition rather than a preference: "There is no `--no-verify`, `--skip-audit`, `--dangerous`, or hook-bypass flag on `run`." BOTH host runners violate it, and the agy host violates it in the dangerous direction by DEFAULT. Measured at HEAD `d0919400`: `agy_runipd.py:3976` registers `--dangerously-skip-permissions`/`--dangerous` with `default=True`, so every `aw agy run` auto-approves every tool permission request unless the operator remembers `--no-dangerously-skip-permissions`, and `:3990` registers `--no-verify`/`--no-audit` to skip the turn-2 skeptical validation. The opencode host registers `--validate`/`--verify`/`--audit` as a `BooleanOptionalAction` (`:6063`), which makes argparse AUTO-GENERATE `--no-validate`/`--no-verify`/`--no-audit`, so the prohibited spelling is reachable there too even though nobody wrote it. The prohibition exists because these are the flags that turn a verified run into an unverified one; a spec that forbids them while the shipped CLI ships them with a `True` default is not a documentation gap, it is the safety statement being false.
- Scope: Bring both runners' `run`/`start` parsers into conformance with spec 2.1's prohibition, WITHOUT changing what a run actually does when the operator does not pass a flag on the opencode host. Three concerns, kept separate because they carry different blast radii: (1) remove the prohibited SPELLINGS (`--dangerous`, `--no-verify`, `--no-audit`, `--skip-audit`) while preserving each host's ability to express its real, non-prohibited intent under a conformant name; (2) flip agy's `--dangerously-skip-permissions` from `default=True` to opt-IN, which is the actual safety defect; (3) decide and record what the agy verifier default becomes once `--no-verify` is gone, since agy gates verification on `not no_verify` (defaults ON) while opencode gates on `validate` (defaults OFF) and the two must not be silently harmonized. Excludes registering spec 2.1's eight POLICY flags (`uyeko5` owns all seven missing ones), excludes `--type`/`--action`/`--json` (unbuilt, recorded by `uyeko5` F-11's sibling notes), and excludes changing the verifier's own logic.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: to-review
- Readiness: no-go
- Set: runbypass
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ki6tom
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history

- 2026-09-04 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored at the maintainer's direction, who chose "create an IPD" when asked how to route finding F-11 from the `/plan-review` of `uyeko5` (`runflags-01`). F-11 was found while auditing `uyeko5`'s flag surface against spec 2.1 and deliberately NOT folded into that plan: removing a shipped flag that defaults `True` is a permission-handling behavior change with a blast radius unrelated to registering the eight policy flags `uyeko5` owns, and widening a plan already touching the two highest-contention modules in the repo would have been the wrong trade. EVERY CLAIM BELOW WAS MEASURED AT `d0919400`, not inherited from the spec text. THE FINDING THAT SHAPED THE PLAN: the two hosts gate verification on OPPOSITE defaults and a comment at `agy_runipd.py:3077-3082` says so explicitly, so "just delete `--no-verify` on both" would silently flip agy's verification from ON to OFF or opencode's from OFF to ON depending on which spelling survived. That is why E-04 exists as its own item with an owner-facing question rather than being bundled into E-01. Also measured: `tests/test_oc_runipd.py:1981-1984` explicitly asserts `--no-verify` parses on the opencode host, so this plan MUST update a shipped test rather than claiming no test breaks.

## Goal

Make the shipped `run` parsers on both hosts satisfy spec `25kzda` 2.1's bypass-flag prohibition, and make agy's permission auto-approval opt-IN rather than opt-OUT, without silently changing either host's verification default as a side effect.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the violation, then close the safety defect

- [ ] E-01 Write the failing-first CONTRACT TEST before touching a parser: assert that NONE of spec 2.1's prohibited flag spellings is accepted by either host's `run`/`start` parser, driven by a DATA table of the prohibited names taken from the spec sentence (`--no-verify`, `--skip-audit`, `--dangerous`, `--no-audit`) rather than hand-written per flag.
  ASSERT BY PARSING, NOT BY GREP, because the opencode violation is INVISIBLE to grep: `--no-verify` appears nowhere in `oc_runipd.py`, yet `BooleanOptionalAction` over `--validate`/`--verify`/`--audit` (`:6063-6070`) makes argparse generate it, and a grep-based test would report opencode conformant while the flag parses fine. Assert that `parse_args(["start", "demo", "--no-verify"])` RAISES `SystemExit` on both hosts once conformant, and paste it FAILING at current HEAD for both.
  - Depends on: none
  - Expected outcome: one table-driven test over the spec's prohibited spellings, failing at HEAD on BOTH hosts, driven by parsing rather than by grep. Paste the failure.
  - Execution state: pending

- [ ] E-02 FLIP agy's `--dangerously-skip-permissions` FROM `default=True` TO OPT-IN. This is the real safety defect and it is independent of the naming question: today `aw agy run <selector>` passes `--dangerously-skip-permissions` to the child agent (`agy_runipd.py:2317-2318`, gated on `options.get("dangerously_skip_permissions", True)`) unless the operator remembers the negation, so a bare invocation auto-approves every tool permission request.
  TWO SITES, not one, and the second is the one a parser-only fix leaves live: the parser default (`:3979-3982`) and the OPTIONS FALLBACK at `:1686-1688` (`getattr(args, "dangerously_skip_permissions", True)`), plus the consumer's own defaulted read at `:2317`. Change all three to default to NOT skipping. Remove the now-redundant `--no-dangerously-skip-permissions` opt-out only if it becomes meaningless; if it is kept, say why.
  RESUME COMPATIBILITY: a run frozen before this change may carry no `dangerously_skip_permissions` key, and `:2317`'s `True` fallback would keep auto-approving on resume. State what you find rather than letting an in-flight run keep the old behavior silently.
  - Depends on: E-01
  - Expected outcome: a bare `aw agy run` no longer passes `--dangerously-skip-permissions` to the child; passing the flag explicitly still does; all three sites changed, shown; the frozen-state implication stated.
  - Execution state: pending

### Task group 2: remove the prohibited spellings without changing behavior by accident

- [ ] E-03 REMOVE the prohibited spellings from agy's parser: `--dangerous` (the alias at `:3978`) and `--no-verify`/`--no-audit` (`:3991-3992`). Keep the CAPABILITY under a conformant name where the capability itself is legitimate: the spec forbids the flag NAMES `--no-verify`/`--skip-audit`/`--dangerous` on `run`, and E-04 decides what agy's verification control is called and defaults to.
  DO NOT simply delete the `dest`s: `no_verify` is read from run-state options at `:2993-2995` and drives `verifier_expected` at `:3083`, and FIVE existing tests write `"no_verify"` into state options (`tests/test_agy_runipd_cli.py:154`, `:204`, `:247`, `:306`, `:520`). The run-state KEY and the CLI FLAG are different surfaces; this item removes the flag spelling, and any state-key rename is a separate migration this plan does not take on. State plainly which you changed.
  - Depends on: E-01
  - Expected outcome: `aw agy run --dangerous`, `--no-verify`, and `--no-audit` all fail to parse; the run-state `no_verify` option key still works so no frozen run changes meaning; the five tests writing that key still pass unchanged.
  - Execution state: pending

- [ ] E-04 DECIDE AND IMPLEMENT what replaces `--no-verify` on agy, which is the one item carrying a real design question rather than a mechanical edit. The two hosts DELIBERATELY disagree today and a comment says so: `agy_runipd.py:3077-3082` records that agy "gates the verifier on `not no_verify` (verification defaults ON here), whereas `oc` gates on `validate` (which defaults OFF)".
  So there are two conformant shapes and they are NOT equivalent: (a) give agy a `--validate`/`--no-validate` `BooleanOptionalAction` matching opencode's spelling but keeping agy's `default=True`, which conforms only if the auto-generated `--no-validate` is deemed outside the prohibition (the spec forbids `--no-verify`, `--skip-audit`, `--dangerous`, and hook-bypass flags by name, and does NOT name `--no-validate`); or (b) give agy a positively-named opt-out that the spec does not forbid.
  WHAT YOU MUST NOT DO is harmonize the DEFAULT as a side effect of renaming the flag. Turning agy's verification from ON to OFF to match opencode would be a silent safety regression wearing a conformance fix's clothes; turning opencode's from OFF to ON would change every existing opencode run's cost and duration. Preserve both defaults, and if you believe one is wrong, say so as a finding for a separate plan.
  NOTE THE UNRESOLVED TENSION honestly: `BooleanOptionalAction` is how the opencode host got its violation in the first place (E-01), so choosing (a) reintroduces an auto-generated negation. If `--no-validate` is also judged prohibited, only (b) is conformant. OQ-01 carries this and is BLOCKING.
  - Depends on: E-03
  - Expected outcome: agy has a conformant way to disable verification, verification still defaults ON for agy and OFF for opencode, both shown side by side, and the choice between (a) and (b) is recorded with its reasoning rather than made silently.
  - Execution state: pending

- [ ] E-05 REMOVE the prohibited spellings from opencode's parser, which requires replacing the `BooleanOptionalAction` at `:6063-6070` rather than editing a string: the action itself generates `--no-verify` and `--no-audit` from the `--verify` and `--audit` aliases. Drop the `--verify`/`--audit` ALIASES (keeping `--validate`, whose generated `--no-validate` is not a spec-prohibited name) or replace the action with explicit flags, whichever preserves today's behavior more directly; justify which.
  UPDATE THE SHIPPED TEST that pins the violation: `tests/test_oc_runipd.py:1981-1984` asserts `--no-verify` parses and sets `validate=False`, and `:1986-1989` does the same for `--no-audit`. These must become assertions that the prohibited spellings are REJECTED. Do not delete the surrounding coverage of `--validate`/`--no-validate`, which is legitimate and must keep passing.
  DO NOT change opencode's `validate` DEFAULT, which is `False` (`:6068`, and the fallback at `:2687`), and do not touch the `no_verify`/`no_audit` STATE-KEY compatibility read at `:4924` (`validate = not (opts.get("no_verify") or opts.get("no_audit"))`), which exists so a run frozen under the old option keys still resolves correctly.
  - Depends on: E-01
  - Expected outcome: `aw oc run --no-verify` and `--no-audit` fail to parse; `--validate`/`--no-validate` still work; `validate` still defaults `False`; the frozen-state compatibility read at `:4924` is untouched; the two shipped test cases now assert rejection and the rest of that test still passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PROHIBITION IS BY NAME, NOT BY CAPABILITY. Spec 2.1 `:135` forbids four specific spellings on `run`. It does not say verification cannot be disabled; it says these flags do not exist. That distinction is what makes E-04 a design question rather than a deletion.
- `BooleanOptionalAction` SILENTLY DOUBLES A FLAG'S SURFACE. Every `--x` declared with it also accepts `--no-x`, for every alias. This is how the opencode host violates a prohibition that appears nowhere in its source, and it is why E-01 must assert by PARSING rather than by grep.
- THE RUN-STATE OPTION KEY AND THE CLI FLAG ARE SEPARATE SURFACES, and both hosts already rely on the distinction: opencode reads legacy `no_verify`/`no_audit` keys at `:4924` purely so a run frozen under an older CLI still resolves. Removing a flag must not rename a state key.
- THE TWO HOSTS' VERIFICATION DEFAULTS DIVERGE DELIBERATELY and a code comment documents it (`agy_runipd.py:3077-3082`). Unlike the `--full-auto` divergence that `uyeko5` E-07 normalizes by maintainer ruling, this one has NOT been ruled on, so this plan preserves it and asks.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | agy REGISTERS TWO OF THE FOUR PROHIBITED SPELLINGS: `--dangerous` (as an alias of `--dangerously-skip-permissions`) and `--no-verify`/`--no-audit`. | `agy_runipd.py:3977-3982`, `:3990-3996`; spec `25kzda:135` |
| F-2 | **agy AUTO-APPROVES ALL TOOL PERMISSIONS BY DEFAULT, which is the safety defect rather than the naming one.** `default=True` means a bare `aw agy run` passes `--dangerously-skip-permissions` to the child agent; the operator must remember a negation to be safe. Three sites, so a parser-only fix leaves it live. | parser `agy_runipd.py:3979-3982` (`default=True`); options fallback `:1686-1688` (`getattr(..., True)`); consumer `:2317-2318` (`options.get(..., True)` then appends the flag) |
| F-3 | **THE opencode VIOLATION IS INVISIBLE TO GREP, and a grep-based conformance test would falsely pass it.** `--no-verify` appears nowhere in `oc_runipd.py`, but `--validate`/`--verify`/`--audit` is a `BooleanOptionalAction`, so argparse generates `--no-validate`/`--no-verify`/`--no-audit`. Verified by parsing an equivalent parser: `--no-verify` parses and yields `validate=False`. | `oc_runipd.py:6063-6070`; confirmed by constructing the same `add_argument` call and parsing `--no-verify` |
| F-4 | A SHIPPED TEST PINS THE VIOLATION, so this plan cannot claim "no existing test breaks". `tests/test_oc_runipd.py` explicitly asserts `--no-verify` and `--no-audit` parse and set `validate=False`. | `tests/test_oc_runipd.py:1975-1989` |
| F-5 | **THE HOSTS' VERIFICATION DEFAULTS ARE OPPOSITE AND DELIBERATE, so renaming the flag risks flipping one.** agy gates on `not no_verify` (verification ON by default); opencode gates on `validate` (OFF by default). A code comment states the difference and warns against copying the expression. This is why E-04 is its own item with a blocking question. | `agy_runipd.py:3077-3083`; `oc_runipd.py:4918-4924` (`validate = opts.get("validate", False)`) |
| F-6 | THE `no_verify` STATE KEY IS LOAD-BEARING FOR FROZEN RUNS AND FOR TESTS, independent of the CLI flag: agy reads it from run-state options to compute `verifier_expected`, opencode reads it as a legacy-compatibility fallback, and five agy tests write it directly. Removing the flag must not remove the key. | `agy_runipd.py:2993-2995`, `:3083`; `oc_runipd.py:4924`; `tests/test_agy_runipd_cli.py:154`, `:204`, `:247`, `:306`, `:520` |
| F-7 | PROVENANCE: this plan exists because `/plan-review` of `uyeko5` (`runflags-01`) audited spec 2.1's flag surface and found the prohibition violated. It was recorded there as F-11 and explicitly excluded from that plan's fence, then routed here by maintainer choice rather than fixed in place. | `uyeko5` F-11 and its "Deferred / out of scope" entry |
| F-8 | CONTENTION: both runner modules are the highest-contention files in the repo, declared by 12 other unexecuted plans including `uyeko5` itself. This plan and `uyeko5` touch the SAME parser functions, so whichever runs second must re-locate every site by symbol. No dependency edge is declared because neither strictly requires the other, but they must not run concurrently. | computed Scope-Paths intersection across `.aw/records/plans/pending/`; `uyeko5` F-8 records the same contention |

## Proposed changes (ordered, validatable)

1. Table-driven parse-based contract test over spec 2.1's four prohibited spellings, failing at HEAD on both hosts (E-01).
2. Flip agy's permission auto-approval to opt-in at all three sites (E-02).
3. Remove agy's prohibited flag spellings, leaving the run-state key intact (E-03).
4. Decide and implement agy's conformant verification control, preserving both hosts' defaults (E-04, OQ-01 blocking).
5. Remove opencode's auto-generated prohibited spellings and update the two shipped test cases that pin them (E-05).

## Deferred / out of scope (with reason)

- REGISTERING SPEC 2.1'S EIGHT POLICY FLAGS. `uyeko5` (`runflags-01`) owns all seven missing ones. This plan removes prohibited flags; that one adds required flags. Same spec section, opposite directions, and merging them would produce one plan editing every parser site for two unrelated reasons.
- `--type`, `--action`, AND `--json` ON `run`. All three are spec 2.1 grammar entries that are also unbuilt (`--action` greps to zero; `--json` exists only on `status`). Recorded so they are not mistaken for shipped, but adding them is selection/dispatch work, not bypass-flag removal.
- HARMONIZING THE TWO HOSTS' VERIFICATION DEFAULTS. Deliberately divergent and documented in code (F-5). Unlike `--full-auto`, no maintainer ruling exists, so this plan preserves both and asks rather than normalizing under cover of a conformance fix.
- RENAMING THE `no_verify` RUN-STATE OPTION KEY. Load-bearing for frozen runs and five tests (F-6). A key migration needs its own compatibility story.
- AUDITING FOR OTHER HOOK-BYPASS PATHS. Spec `:135` also forbids "hook-bypass" flags generically. This plan closes the four NAMED spellings plus the permission default; a general audit for `--no-verify`-equivalent escape hatches elsewhere in the runners is not attempted here and is stated rather than implied.

## Scope check

- Over-scope: none. Every edit removes a spec-prohibited flag spelling, fixes the permission default that makes the prohibition consequential, or updates a test that pins the violation.
- Under-scope, DELIBERATE and stated: the generic "hook-bypass flag" clause of spec `:135` is closed only for the four named spellings, not by a general audit.
- Under-scope: whether `--no-validate` (argparse-generated from the surviving `--validate`) is itself prohibited is OQ-01's second half, and the answer decides whether E-04 option (a) is conformant at all.

## Required tests / validation

- E-01's contract test, demonstrated FAILING at pre-change HEAD and passing after, for BOTH hosts, asserting by PARSING rather than by grep (F-3).
- agy: a bare `aw agy run` shown NOT passing `--dangerously-skip-permissions` to the child, and still passing it when the flag is explicit. All three sites shown changed (F-2).
- Both hosts: each of `--no-verify`, `--no-audit`, `--dangerous`, `--skip-audit` shown REJECTED by the `run`/`start` parser.
- Verification defaults shown SIDE BY SIDE and UNCHANGED: agy ON, opencode OFF (F-5). This is the regression this plan is most likely to cause.
- The five agy tests writing the `no_verify` state key pass unchanged (F-6), and opencode's frozen-state compatibility read at `:4924` is untouched.
- `tests/test_oc_runipd.py`'s two pinning cases updated to assert rejection, with the rest of that test still passing (F-4).
- Both driver suites green: `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`.
- Full suite BARE (`python3 -m pytest`), compared against YOUR OWN pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (`tests/test_run_viewer.py` shows ~15 phantom failures in a detached worktree; backlog `dh0uno`).

## Spec / documentation sync

- This plan makes the shipped CLI satisfy spec `25kzda` 2.1 `:135`. It does NOT change the spec text.
- If OQ-01 is answered such that a capability must be renamed, the new flag name is NOT in the spec's grammar block; record whether the spec's 2.1 grammar needs the conformant replacement added, and if so say that the spec edit is a follow-up rather than editing an `approved` spec inside this plan.
- If any user-facing doc enumerates `aw agy run` or `aw oc run` flags, update it; otherwise state N/A with the paths checked.

## Open questions

### OQ-01: What replaces agy's `--no-verify`, and is the argparse-generated `--no-validate` itself prohibited?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: BLOCKING because E-04 cannot be implemented without the answer and a wrong guess is a silent safety regression. Spec `:135` forbids `--no-verify`, `--skip-audit`, `--dangerous`, and "hook-bypass" flags BY NAME; it does not name `--no-validate`. If `--no-validate` is acceptable, agy can take a `--validate` `BooleanOptionalAction` with `default=True` (matching opencode's spelling while keeping agy's ON default) and the fix is mechanical. If the prohibition is read by INTENT rather than by name, then any negation that disables verification is prohibited, `BooleanOptionalAction` is the wrong mechanism on both hosts, and opencode's surviving `--no-validate` must go too, which widens this plan. The one option NOT on the table is deleting agy's ability to disable verification without saying so, or flipping either host's default while renaming the flag (F-5): both would be safety changes disguised as conformance edits. Needs the maintainer because it is a reading of an `approved` spec's intent and a safety-posture call, not a fact the repository can settle.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the contract test FAILING at pre-change HEAD, naming the prohibited spellings accepted on each host, then passing after. Paste the test's DATA table showing it is driven by spec `:135`'s list. Paste evidence the test asserts by PARSING (a `SystemExit`/parse-failure assertion), not by grepping source, since a grep test would falsely pass the opencode host (F-3).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste all THREE agy sites after the change (parser default, options fallback at `:1686`, consumer read at `:2317`). Then DEMONSTRATE the behavior change, not just the default: paste the child argv for a bare `aw agy run` showing `--dangerously-skip-permissions` ABSENT, and for an explicit invocation showing it PRESENT. A pasted default alone does not satisfy this item, because the two defaulted reads would keep auto-approving while the parser claimed otherwise. State what you found about frozen runs lacking the `dangerously_skip_permissions` key.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw agy run --dangerous`, `--no-verify`, and `--no-audit` each REJECTED. Paste the five `tests/test_agy_runipd_cli.py` cases that write the `no_verify` state key passing UNCHANGED, proving the flag was removed without removing the key (F-6). State explicitly which surface you changed (flag) and which you did not (state key).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: state which option (a) or (b) OQ-01 was answered with, and by whom. Paste agy's new verification control in `--help` and paste a run with verification DISABLED through it. Then paste the two hosts' verification defaults SIDE BY SIDE showing agy still ON and opencode still OFF (F-5) - this is the specific regression this item risks, so a passing suite does not substitute for the side-by-side. If option (a) was chosen, paste whether `--no-validate` is generated and confirm that was accepted as conformant rather than overlooked.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw oc run --no-verify` and `--no-audit` each REJECTED, and `--validate`/`--no-validate` still working. Paste `validate`'s default still `False`. Paste the diff of `tests/test_oc_runipd.py:1975-1989` showing the two pinning cases now assert rejection while the surrounding `--validate` coverage survives (F-4). Paste `oc_runipd.py:4924`'s legacy-key read UNCHANGED. Then both driver suites and the bare full suite with counts, compared against your own pre-change measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 5 E-leaves across 2 task groups, one concern throughout: make the `run` parsers satisfy spec 2.1's bypass prohibition. Right-sizing assessed per item, not by count. E-01 is the contract test; E-02 is the permission default alone, kept separate from every naming change because it is the actual safety fix and must land even if OQ-01 stalls E-04; E-03 and E-05 are the per-host spelling removals, separate because the opencode one requires replacing an argparse action and updating a shipped test while the agy one is a deletion; E-04 is isolated precisely because it carries the only real design question and the only cross-host regression risk. E-02 could be executed and validated entirely on its own, which is the point: the safety fix is not held hostage by the naming decision.

Open questions: OQ-01 (what replaces agy's `--no-verify`, and whether `--no-validate` is itself prohibited) is BLOCKING and unresolved. It gates E-04 only; E-01, E-02, E-03 and E-05 are executable without it. Per the repository's pre-execution gate, this plan MUST NOT be executed until OQ-01 is answered.

This plan is `to-review` and requires explicit human approval before execution. It declares `- Item-Dependencies: none`, but see F-8: it edits the same parser functions as `uyeko5` (`runflags-01`), so the two MUST NOT run concurrently and whichever runs second must re-locate every site by symbol.

Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `tests/test_oc_runipd.py`, and `tests/test_agy_runipd_cli.py`. Do NOT register any of spec 2.1's eight POLICY flags (`uyeko5` owns them). Do NOT rename the `no_verify` run-state option KEY or touch `oc_runipd.py:4924`'s legacy-compatibility read. Do NOT change opencode's `validate` default (`False`) or agy's verification default (ON): preserving both while renaming is the whole difficulty of E-04. Do NOT change the verifier's logic, only the flag surface that reaches it. Do NOT add `--type`, `--action`, or `--json`. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt).

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is (1) E-01's contract test observed FAILING on BOTH hosts, including the opencode host whose violation no grep can see, and (2) the two verification defaults shown side by side and UNCHANGED after E-04, because that is the regression a green suite is least likely to catch. Do NOT report the generic "hook-bypass" clause of spec `:135` as fully closed: this plan closes four named spellings plus the permission default, and no general audit was performed.

Execution contract: RE-READ both runner modules immediately before editing and locate every parser and fallback site BY SYMBOL, never by the line numbers in this plan: these are the highest-contention files in the repo and 12 other unexecuted plans declare them, `uyeko5` among them. OQ-01 is BLOCKING and must be answered before E-04. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
