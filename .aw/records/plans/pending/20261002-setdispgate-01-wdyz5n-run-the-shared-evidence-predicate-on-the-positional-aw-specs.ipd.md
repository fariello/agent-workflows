# IPD: Run the shared evidence predicate on the positional aw specs set implemented spelling

- Date: 2026-10-02
- Kind: child
- Concern: `aw specs set implemented <id6>` (the POSITIONAL spelling) moves a spec from `implementing` to `implemented` at exit 0 with NO `--evidence` citation, while `aw specs set <path> --status implemented` refuses the identical transition at exit 1. `AGENTS.md` states an agent "may NOT set `implemented` (needs cited evidence)", so the positional spelling lets an agent assert a spec is implemented with no cited executed IPD: a forged attestation of the same class the `Readiness` and `--by-human` rules exist to prevent. `specs.run_set` enforces the gate via `auth.get("evidence")` plus `specs._evidence_resolvable`; `status_set.validate_transition_allowed` has NO evidence branch at all. The bypass spelling is the shorter, more idiomatic one an agent is likelier to type. Two FURTHER surfaces share the hole and were measured here but are absent from the backlog item: `aw set implemented <id6>` and `aw set specs implemented <id6>` both exit 0 too, and neither even declares `--evidence`, so on those surfaces the gate is unreachable by any argument.
- Scope: IN: make the `implementing -> implemented` evidence requirement fire on every surface reaching `status_set.validate_transition_allowed`, by CONSUMING the existing `specs._evidence_resolvable` predicate rather than writing a second copy; register `--evidence` on the untyped `aw set` parser and declare it in that command's `CommandDeclaration`, so the refusal is satisfiable rather than merely unreachable; repair the one existing test this breaks; and pin the parity as paired outcome tests on both spellings. OUT, each with a reason recorded under "Deferred": the `deferred` gate-kind validation bypass (a separate measured defect under its own release-gated carrier `fv4b6s`); removing the `cli.main` dispatch fork itself (the durable fix, gated on a blocking maintainer decision); changing what `_evidence_resolvable` ACCEPTS; the post-write `validate_spec` conformance refusal; and the three pre-existing suite failures this plan neither causes nor fixes.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_specs_evidence_gate_parity.py, tests/test_status_set.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: h4fiwa
- Blocks-Release: next
- Set: setdispgate
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: wdyz5n

## Workflow history

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `h4fiwa`. The item's measurement was re-reproduced at this tree's HEAD `31b5ed6b9` rather than trusted, and the reproduction WIDENED it: two further surfaces (`aw set implemented`, `aw set specs implemented`) share the bypass and were not in the item. The fix's blast radius was measured by applying the fix in-memory and running the five candidate specs/status modules, which identified exactly ONE breaking test by name. Both of the item's open design questions (`_evidence_resolvable`'s accepted layout, and whether the repair can use `aw set --evidence`) were resolved from measurement and are recorded in "Findings".
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the `implementing -> implemented` evidence requirement unbypassable, so no spec reaches
`implemented` without a resolvable executed-IPD citation regardless of which spelling or which `set`
surface was used, and so the policy `AGENTS.md` already states is actually enforced by the code.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: close the predicate hole

- [ ] E-01 In `status_set.validate_transition_allowed`, add the `implementing -> implemented` evidence requirement to the EXISTING `rec.record_type == "specs"` block, by consuming the SAME authority-table condition and the SAME resolvability predicate `specs.run_set` already consumes. `specs.run_set` reads `auth = A.TRANSITION_AUTHORITY.get(f"->{new}", {})` then `if auth.get("evidence"):` and requires `_evidence_resolvable(path, ev)`; the specs block in `validate_transition_allowed` already computes that identical `auth` dict for the `by_human`/`human_token` and `review_record` conditions, so the new branch reads one more key off a dict it already holds.

    CONSUME THE EXISTING PREDICATE; DO NOT WRITE A SECOND ONE. This is the whole point: the prior instances of this class were each fixed by DUPLICATING behavior into the second path, which is why instances keep being found. The precedent is EXACT, in-tree, and sits in the very function being edited: the `->reviewed` attestation branch immediately above already does `from agent_workflows import specs as _specs` and calls `_specs._review_attestation_refusal(...)`, under a comment stating that "a gate installed in only one of them is bypassed by choosing the other". Follow that shape: a local import of `specs` and a call to `specs._evidence_resolvable(rec.path, ev)`.

    PLACE IT INSIDE THE EXISTING `if old_status and old_status != norm_status:` GUARD, beside the sibling authority branches. That guard is load-bearing in a way that is cheap to get wrong: it makes a NO-OP re-set exempt, and the authority table governs TRANSITIONS, not identity. MEASURED: `attention_contract.transition_allowed("implemented", "implemented")` is `False` and the only legal source of `implemented` is `implementing`, so the guard cannot mask a real transition. The `->reviewed` branch's own comment records the same reasoning for the same guard.

    USE `rec.path` AS THE PREDICATE'S FIRST ARGUMENT, not a reconstructed path. `_evidence_resolvable` walks up from that path via `specs._spec_repo_root` to find the repo root, and `read_artifact_record` supplies a real on-disk path, so passing `rec.path` is correct and needs no `repo_root` plumbing.

    THE REFUSAL MUST WRITE NOTHING. This function is called from `run_set_command`'s pre-flight loop, BEFORE the dry-run branch and BEFORE `apply_status_change`, which is what makes a refusal leave the spec byte-identical and un-relocated. Return `(False, <one-line reason>)` in the established shape; do not raise, and do not print.

    PRESERVE THE REASON TEXT IN SUBSTANCE. `specs.run_set` writes `aw specs set: implementing -> implemented requires a resolvable --evidence citation (an existing .agents/plans/executed/ IPD path); refused.`. This function serves several verbs so its prefix differs and `validate_transition_allowed` returns a ONE-LINE reason; keep the phrase `requires a resolvable --evidence citation` so one needle matches both surfaces, and name the recovery.
  - Depends on: none
  - Expected outcome: `aw specs set implemented <id6>` with no `--evidence` exits 1 and leaves the spec in `implementing/` byte-identical; with an unresolvable `--evidence` exits 1 and writes nothing; with a resolvable citation exits 0 and relocates the file; `aw specs set <path> --status implemented` behaves identically in all three cases.
  - Execution state: pending

- [ ] E-02 Make the gate SATISFIABLE on the untyped `aw set` surface, by registering `--evidence` on the `p_set` parser in `cli.py` and adding it to the `command="set"` `CommandDeclaration.legacy_flags` in `command_surface.py`. WITHOUT THIS, E-01 CONVERTS ONE BUG INTO ANOTHER: `aw set implemented <id6>` and `aw set specs implemented <id6>` both reach `run_set_command` and so both start refusing, but `p_set` declares no `--evidence` (MEASURED: `aw set --help` does not mention it, and passing it exits 2 with `unrecognized arguments: --evidence`), so on those surfaces the transition would become impossible by ANY argument rather than merely gated.

    THE PRECEDENT IS EXACT AND RECENT. Executed plan `47ttnv` E-03 and E-06 did precisely this pair of steps for the release-gate close predicate: make the flag REACH the predicate on the second path, then DECLARE it on the `CommandDeclaration` because "a flag that decides whether a release gate may be released should be declared rather than merely tolerated". The same reasoning applies verbatim to a flag that decides whether an implementation attestation may be written.

    HELP TEXT MUST NAME THE ARTIFACT CLASS, not just the flag. `p_specs_set`'s existing registration says "Resolvable implementation-evidence citation (for implemented)". Match that, and add that the citation must be an existing executed-IPD path, since that is what the predicate actually enforces and an operator told only "resolvable" cannot guess the executed/ requirement.

    DO NOT make the flag-agreement test bidirectional and do not touch any other `CommandDeclaration`. The `set` declaration gains exactly one entry.
  - Depends on: E-01
  - Expected outcome: `aw set --help` lists `--evidence`; `aw set implemented <id6> --evidence <resolvable executed-IPD path>` exits 0 and relocates the spec; the same call without the flag exits 1; `command_surface.get_declaration("set").legacy_flags` contains `--evidence` and no existing declared-minus-accepted agreement test regresses.
  - Execution state: pending

### Task group 2: repair the one test this breaks

- [ ] E-03 Repair `tests/test_status_set.py::SharedLifecycleRenderingTests::test_status_transition_color_rendering_and_ansi_controls`, which reaches `implemented` through the BYPASS as a FIXTURE STEP and therefore breaks the moment E-01 lands. THIS IS NOT OPTIONAL CLEANUP: without it this plan cannot satisfy its own V-06 bare-suite requirement.

    MEASURED, NOT PREDICTED. The fix was applied in-memory and the five candidate modules (`tests/test_status_set.py`, `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_spec_review_attestation.py`, `tests/test_specs_from_backlog.py`) were run: `2 failed, 157 passed`, and ONE of those two failures is the pre-existing `test_every_real_spec_in_this_repository_still_conforms` (F-06). So this test is the WHOLE test-side cost. It calls `self.create_spec(..., status="implementing")` then `self._echo(["set", "implemented", "bbb222"])` and asserts the bold-green-46 `implemented` token appears in both the set output and a subsequent `find`. Its subject is COLOR RENDERING; reaching `implemented` is incidental to it.

    THE REPAIR IS TO MAKE THE FIXTURE'S CITATION LEGITIMATE, NEVER TO WEAKEN THE GATE. A fixture that needs a gate disabled is telling you the fixture is wrong. Write a real executed-IPD file into the test repo's `.aw/records/plans/executed/` and pass `--evidence <that relative path>`. MEASURED: with E-01 and E-02 applied, `cli.main(["set","implemented","bbb222","--evidence",<rel>, ...])` exits 0 and the asserted needle `\033[1;38;5;46mimplemented\033[0m` IS present, so the test's actual subject survives intact. Do NOT switch the assertion to a different status, which would silently delete the `done`-class color coverage, and do NOT delete the spec leg of the test.

    `self._echo` APPENDS `--yes --dir <root>`, so pass `--evidence` inside the `argv` list it is given. The repo root is `self.repo_root`; write the evidence artifact relative to it and cite the repo-relative path, because `_evidence_resolvable` joins the citation onto the root it derives from the spec.
  - Depends on: E-01, E-02
  - Expected outcome: `test_status_transition_color_rendering_and_ansi_controls` passes with E-01 and E-02 applied, still asserting the bold-46 `implemented` token in BOTH the `set` output and the `find` output, with the fixture citing a real executed-IPD path; no assertion weakened or removed.
  - Execution state: pending

### Task group 3: pin the parity on every surface

- [ ] E-04 Author `tests/test_specs_evidence_gate_parity.py` pinning the refusal on BOTH spellings and on BOTH untyped surfaces. Drive `cli.main` and assert on exit code, the spec's resulting LOCATION, and its resulting CONTENT. Pass `--no-commit` and `--yes` on every invocation. Model the helper shape on `tests/test_backlog_positional_close_gate.py` (one temp repo per test, `cli.main` under `redirect_stdout`/`redirect_stderr`), which is the established template for exactly this both-spellings property.

    THE PAIRING IS THE POINT AND IS NOT DECORATION. For each case, run BOTH spellings against IDENTICAL fresh repos and assert the SAME exit code and the SAME resulting on-disk state. A test pinning only the positional spelling would still pass if a later change broke the `--status` spelling instead, which is the very drift this plan exists to close.

    COVER, on each of `aw specs set implemented <id6>` and `aw specs set <path> --status implemented`: (a) no `--evidence` refuses, rc 1, file byte-identical AND still in `implementing/`; (b) an unresolvable `--evidence` refuses identically; (c) a RESOLVABLE `--evidence` succeeds, exits 0, and relocates the file into `implemented/`. CASE (c) IS NOT OPTIONAL: without it a "fix" that refuses unconditionally would pass (a) and (b) while breaking the verb entirely, and that is the single likeliest way to get this wrong.

    ADD the two untyped surfaces, `aw set implemented <id6>` and `aw set specs implemented <id6>`, each asserting the refusal without `--evidence` and the success with it (the latter is what proves E-02 landed). ADD the NO-OP fence: an already-`implemented` spec re-set to `implemented` must NOT be retroactively refused, since `old == new` is not a transition. ADD the negative fence: an unrelated spec transition that is not evidence-gated (for example `draft -> to-review`) still succeeds with no `--evidence`, which is what bounds this gate's blast radius.

    ASSERT THE ABSENCE OF THE WRITE, NOT ONLY THE EXIT CODE. A test checking only `rc == 1` would pass against a half-fix that refuses AFTER relocating the file. Read the file back from its original path and assert byte-identical content and an unchanged status directory.

    NO CODE-PINNING. Do not read production source with `inspect`, `ast`, regex or substring search, do not count callers, and do not assert docstring or comment text (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16).
  - Depends on: E-01, E-02
  - Expected outcome: a new module whose cases pass on both spellings and both untyped surfaces after E-01 and E-02, with every refusal case asserting content and location as well as exit code, and with the pre-fix failure output pasted for the positional cases so the fix's effect is attributable.
  - Execution state: pending

- [ ] E-05 Confirm no OTHER test pinned the bypass as correct behavior, by running the five candidate modules individually and pasting each result. The modules are `tests/test_status_set.py`, `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_spec_review_attestation.py` and `tests/test_specs_from_backlog.py`, chosen because they are the modules that drive specs transitions.

    THE RISK THIS ITEM EXISTS TO CATCH is a second fixture of the `E-03` shape that the in-memory probe missed because the probe patched only one function. If one is found, repair it the SAME way E-03 does (supply a legitimate citation, or construct the `implemented` state directly on disk), never by weakening the gate, and say so explicitly in the evidence.

    NOTE the one EXPECTED failure and do not chase it: `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` is RED AT BASE on this tree for an unrelated reason (F-06), already filed as backlog `6bolin`. Confirm it fails identically before and after; do not fix it here.
  - Depends on: E-01, E-02
  - Expected outcome: each of the five modules' results pasted; any test broken by the newly-firing gate named, repaired by supplying legitimate evidence or constructing the state directly, with the repair justified; no gate weakened; `6bolin`'s failure confirmed identical before and after.
  - Execution state: pending

### Task group 4: record the user-visible change

- [ ] E-06 Add ONE `CHANGELOG.md` entry in the file's established voice, describing the user-visible effect: `aw specs set` and `aw set` now refuse to mark a spec implemented unless a resolvable evidence citation is supplied, whichever spelling is used, and `aw set` now accepts `--evidence` so that citation can be given. THIS IS A BEHAVIOR CHANGE A USER CAN HIT (a command that used to succeed now refuses), so it belongs in the changelog.

    Name no private predicate and no internal function. Write no em or en dashes (user-facing prose, `AGENTS.md`).

    DO NOT CLOSE THE BACKLOG ITEM. `h4fiwa` carries `- Blocks-Release: next` and this plan is its `- From-Backlog:` carrier, so the HANDOFF route closes the gate automatically once this plan is `executed`; MEASURED via `check_engine.evaluate_blocking_close`, which today reports the gate "handed off to From-Backlog carrier(s) ... but the work has not shipped" and names `aw backlog set h4fiwa --status graduated` as the fix. Leaving the item alone is therefore correct: the runner sets it `graduated` on verification, and an agent must never set it `done`.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: one CHANGELOG entry naming the refusal and the new `aw set --evidence` flag, containing no em or en dash; `h4fiwa` left untouched at `- Status: open` with its gate intact.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE FORK IS ON `--status` PRESENCE, NOT ON ARGUMENT SHAPE. `cli.main`'s specs branch reads `if getattr(args, "status", None) is None:` and routes to `status_set.run_set_command(args.args, scoped_type="specs", ...)`, else sets `args.path` from `args.args[0]` and calls `specs.run_set(args)`. Both spellings share ONE subparser (`p_specs_set`), which is why `--evidence` is ACCEPTED by both while only one READS it.
- THE FIX SHAPE IS ALREADY ESTABLISHED IN THE FUNCTION BEING EDITED. `status_set.validate_transition_allowed`'s specs block already consumes a shared specs predicate for the `->reviewed` attestation (`from agent_workflows import specs as _specs; _specs._review_attestation_refusal(...)`), under a comment stating the governing rule: "the positional `aw specs set reviewed <selector>` spelling routes HERE while the `--status` spelling routes to the forked `specs.run_set` ... so a gate installed in only one of them is bypassed by choosing the other". This plan extends that pattern to one more gate; it invents nothing.
- OUTCOME TESTS ONLY (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16). A gate is verified by DRIVING the verb and reading the exit code plus the file on disk, never by asserting that a call to a predicate appears in the source.
- RUN THE SUITE BARE as `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; `-n0` is forbidden and a second `-q` suppresses the `N passed` line this plan requires pasted.
- `aw` re-execs into the outer checkout's package unless `AW_NO_REEXEC=1` is set; inside this lane it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- A release-blocking backlog item is closed by the HANDOFF route when a `- From-Backlog:` carrier carrying the same gate reaches `executed`. This plan IS that carrier for `h4fiwa`, so it closes the gate by executing, not by calling a setter (E-06).

## Findings

Rows marked MEASURED were reproduced by driving the real surfaces in scratch git repositories at this tree's HEAD `31b5ed6b9`, with the fixture reset between spellings.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (MEASURED) | Identical `implementing` spec fixture, no `--evidence`. `specs.run_set` via the `--status` spelling -> `rc=1`, stderr `aw specs set: implementing -> implemented requires a resolvable --evidence citation (an existing .agents/plans/executed/ IPD path); refused.`, file unchanged. `status_set.validate_transition_allowed(rec, "implemented", ...)` -> `allowed=True, reason=None`. End-to-end through `cli.main`: `aw specs set implemented abc123` -> `rc=0`, stdout `implementing → ✓ implemented`, file RELOCATED to `.aw/records/specs/implemented/` carrying `- Status: implemented`. | **THE BACKLOG ITEM'S CLAIM IS CONFIRMED EXACTLY, AT BOTH THE PREDICATE AND THE CLI LEVEL.** The gate is reachable through only one of the two spellings of one verb, and the ungated one is the shorter, more idiomatic spelling. `validate_transition_allowed` consults the same `TRANSITION_AUTHORITY` dict for `by_human` and `review_record` but never reads its `evidence` key. |
| F-02 | HIGH (MEASURED, WIDER THAN FILED) | Same fixture, through `cli.main`: `aw set implemented abc123` -> `rc=0`, file relocated to `implemented/`. `aw set specs implemented abc123` -> `rc=0`, file relocated. `aw set --help` does NOT list `--evidence`; passing it exits 2 with `unrecognized arguments: --evidence`. | **THE BYPASS HAS THREE SURFACES, NOT ONE, AND TWO OF THEM CANNOT EVEN ACCEPT THE CITATION.** All three reach `run_set_command`, so E-01 fixes all three in one stroke. But on the two untyped surfaces that would make the transition IMPOSSIBLE rather than gated, since the flag is unregistered. This is why E-02 exists and why it is not optional polish: without it, E-01 trades a gate bypass for a dead verb. This finding is NOT in the backlog item. |
| F-03 | MEDIUM (MEASURED; RESOLVES A PRIOR OPEN QUESTION) | Direct calls to `specs._evidence_resolvable` in a scratch repo: `.aw/records/plans/executed/<f>.ipd.md` -> `True`; `.agents/plans/executed/<f>.ipd.md` -> `True`; `.aw/records/plans/pending/<f>.ipd.md` -> `False`. | **THE PREDICATE ACCEPTS BOTH LAYOUTS, SO THE GATE IS NOT BROKEN AND NO CARRIER IS OWED FOR IT.** The existing refusal MESSAGE names only `.agents/plans/executed/`, the pre-`.aw/` layout, which makes a correct refusal needlessly confusing for an operator whose plans live under `.aw/records/`. That is a WORDING defect, not a behavior defect. E-01 states the modern path in the new message; it does NOT change the predicate's acceptance set, which would be a contract change deserving its own review. A pending sibling plan left this as an open question (its OQ-01); it is answered here from measurement. |
| F-04 | HIGH (MEASURED BLAST RADIUS) | The E-01 fix applied in-memory (monkeypatching `validate_transition_allowed` to consult `TRANSITION_AUTHORITY`'s `evidence` key plus `_evidence_resolvable`), then `python3 -m pytest` over the five specs/status modules: `2 failed, 157 passed in 66.90s`. The two: `test_status_set.py::SharedLifecycleRenderingTests::test_status_transition_color_rendering_and_ansi_controls` (caused by the fix) and `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` (pre-existing, see F-06). | **THE TEST-SIDE COST IS EXACTLY ONE TEST, MEASURED RATHER THAN GUESSED.** That test reaches `implemented` through the bypass as a FIXTURE STEP while its actual subject is color rendering, so the correct repair supplies a legitimate citation (E-03). This is the specific risk a sibling plan flagged as a possibility without measuring; it is measured here, and the target is named. |
| F-05 | MEDIUM (MEASURED REPAIR VIABILITY) | With the fix plus `--evidence` registered, `cli.main(["set","implemented","bbb222","--evidence",<rel executed-IPD path>,"--yes","--dir",<root>,"--no-commit"])` -> `rc=0`, the asserted needle `\033[1;38;5;46mimplemented\033[0m` present in the output, file relocated to `implemented/`. The same via `aw specs set implemented bbb222 --evidence <rel>` -> `rc=0`, needle present. | **THE E-03 REPAIR IS PROVEN TO WORK BEFORE BEING PROPOSED, including that it preserves the broken test's ACTUAL subject.** The bold-green-46 `done`-class color token still appears, so the repair keeps the coverage rather than deleting it. This also demonstrates case (c) of E-04 (a resolvable citation must still SUCCEED), which is the assertion that stops an unconditional-refusal "fix" from passing. |
| F-06 | N/A (BASELINE) | Bare `python3 -m pytest` at HEAD `31b5ed6b9`: `3 failed, 4624 passed, 2 skipped, 3 warnings in 266.51s`. The three: `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `test_selector_type_containment.py::test_must_not_refuse_matrix`, `test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`. Each is already filed (`6bolin`, `bxnhdj`, `8jeh4x` respectively). | **THE BASE IS NOT GREEN, SO THE BAR IS AN UNCHANGED FAILURE SET BY NAME, NEVER A COUNT.** All three failures are pre-existing, unrelated to this plan, and already carried by their own backlog items. RE-DERIVE the baseline before editing and compare SETS BY NAME: a count comparison would hide a real regression behind a concurrently-fixed failure, and this repository has a known clock-dependent test that is red for part of every day. Do NOT fix another item's failure here. |
| F-07 | LOW (SCOPE FENCE, MEASURED) | `attention_contract.TRANSITION_AUTHORITY` carries `"evidence": True` on exactly one entry, `->implemented`; every other spec status has `evidence: False`. `transition_allowed("implemented","implemented")` is `False`, and the only legal source of `implemented` is `implementing`. | **THE GATE'S BLAST RADIUS IS PROVABLY ONE TRANSITION.** So E-01 cannot disturb an unrelated spec transition, and the `old != new` guard cannot mask a legitimate one. This is what makes the fix small and reviewable, and it is why E-04 includes a no-op fence and an unrelated-transition fence rather than asserting the bound in prose. |
| F-08 | LOW (NO SPEC AMENDMENT OWED) | `attention_contract.APPROVAL_FLOOR` already states the contract this plan makes true: "The implementing -> implemented transition requires a RESOLVABLE evidence citation ... aw specs enforces presence + format + resolvability". `AGENTS.md` states the agent-facing half ("may NOT set `implemented` (needs cited evidence)"). | **THE DOCUMENTED CONTRACT IS ALREADY CORRECT; ONLY THE CODE IS BEHIND IT.** So this plan brings code up to a documented contract rather than changing a contract, which is why no `.spec.md` is amended and why `AGENTS.md` needs no edit. Only `CHANGELOG.md` is owed, for the user-visible refusal (E-06). |

## Proposed changes (ordered, validatable)

1. `agent_workflows/status_set.py` (+ a local import of `agent_workflows/specs.py`): the specs block of `validate_transition_allowed` consumes `TRANSITION_AUTHORITY`'s `evidence` key and `specs._evidence_resolvable`, so `implementing -> implemented` refuses without a resolvable citation on every surface reaching this function (E-01).
2. `agent_workflows/cli.py` and `agent_workflows/command_surface.py`: register and declare `--evidence` on the untyped `aw set` surface, so the newly-firing gate is satisfiable there rather than unreachable (E-02).
3. `tests/test_status_set.py`: repair the one fixture that reached `implemented` through the bypass, by citing a real executed IPD (E-03).
4. `tests/test_specs_evidence_gate_parity.py`: new paired-spelling outcome tests across both spellings and both untyped surfaces, including the resolvable-citation success case and two fences (E-04).
5. The five specs/status modules: confirm no other test pinned the bypass; repair any that did, the same way (E-05).
6. `CHANGELOG.md`: one entry naming the refusal and the new `aw set --evidence` flag (E-06).

## Deferred / out of scope (with reason)

- THE `deferred` GATE-KIND VALIDATION BYPASS IS NOT FIXED HERE. The positional spelling also writes an out-of-vocabulary `- Gate-Kind:` that the `--status` spelling refuses. It is a genuinely separate defect with its own measurement and its own release-gated backlog item, and folding it in would widen a one-bug fix whose blast radius is measured (F-04) into a two-bug fix whose combined radius is not. It also lands in a different place: the gate WRITE path rather than the transition-authority check.
  - Carrier: fv4b6s
- THE DISPATCH FORK ITSELF IS NOT REMOVED. `cli.main` still routes on `--status` presence and both engines still exist. This plan UNIONS one refusal across the fork rather than removing the fork, deliberately: this bug is release-gated and must be able to ship now, while removing the fork is gated on a blocking maintainer decision about the history sidecar. Shipping the gate fix behind that decision would hold a release blocker hostage to a design question. That durable fix is the root-cause remedy and is the reason this class has recurred.
  - Carrier: fcnz1r
- THE PREDICATE'S ACCEPTANCE SET IS NOT CHANGED. F-03 measured that `_evidence_resolvable` already accepts both the `.aw/records/` and legacy `.agents/` layouts and rejects a non-executed plan path, so nothing is broken. Widening or narrowing what counts as satisfying evidence is a contract change about what satisfies a policy gate and deserves its own review rather than riding along inside a bypass fix. E-01 corrects only the refusal message's WORDING, which F-03 proved stale.
  - Carrier-Declined: This owes nothing durable. The predicate's behavior is correct as measured, so there is no defect to carry: the only thing F-03 found was a message naming an outdated path, and E-01 fixes that wording in the same change. A carrier would track work that does not exist.
- THE POST-WRITE `validate_spec` CONFORMANCE REFUSAL, a third `specs.run_set`-only refusal, is not unioned here. It is a different shape (a whole-result re-validation rather than a per-transition authority gate), it was not the measured bypass, and it lands after the write rather than before it, so it needs its own fail-closed analysis.
  - Carrier: m94eht
- THE THREE PRE-EXISTING SUITE FAILURES (F-06) ARE NEITHER CAUSED NOR FIXED HERE. Each already has its own backlog item. Fixing another item's failure inside this plan would make this plan's own regression evidence unattributable, which is precisely what the compare-sets-by-name rule protects.
  - Carrier: 6bolin
- THE FLAG-AGREEMENT TEST IS NOT MADE BIDIRECTIONAL. E-02 adds one entry to one declaration; making the agreement check bidirectional would fail on flags this plan deliberately does not touch and belongs to its own item.
  - Carrier: fcnz1r

## Scope check

- Over-scope: none. Every path in `- Scope-Paths:` is edited by a numbered E-item: `agent_workflows/status_set.py` (E-01), `agent_workflows/specs.py` (E-01, the predicate is made reachable from the shared engine), `agent_workflows/cli.py` (E-02), `agent_workflows/command_surface.py` (E-02), `tests/test_status_set.py` (E-03), `tests/test_specs_evidence_gate_parity.py` (E-04), `CHANGELOG.md` (E-06). E-05 is a verification item that edits nothing unless it finds a second broken fixture.
- Under-scope: E-05 may need to repair an additional existing test module if it finds a second fixture of the E-03 shape. F-04's in-memory probe measured only one, but the probe patched a single function and cannot prove the absence of a fixture reached by another route, so the possibility is real while its target is not knowable at authoring time. If one is found, declare the actual path at execution time and record the widening in the transition message; this note is the authorization. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5). The backlog item `h4fiwa` is deliberately NOT edited (E-06), so it is not declared.

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. RE-DERIVE the baseline before any edit and compare FAILURE SETS BY NAME, never counts (F-06). The bar is: the three pre-existing failures unchanged, plus no new failure.
- The new `tests/test_specs_evidence_gate_parity.py` run alone with `-o addopts=""` so per-test names are visible, every case named; PLUS the pre-fix demonstration that the positional and untyped cases FAIL before E-01, with that failure output pasted so the fix's effect is attributable.
- The five modules named in E-05, each run individually with its result pasted, and any repair justified in the evidence.
- A direct re-measurement of the original bypass AFTER the fix, pasted: the exact invocations from F-01 and F-02 must now refuse, and the legitimate `--evidence` forms must still succeed and relocate the file.
- `AW_NO_REEXEC=1 aw specs check` and `AW_NO_REEXEC=1 aw sanitize --agent`, each expected to exit 0.
- `AW_NO_REEXEC=1 aw check release-gates`, with its result pasted, since this plan is the release-gate carrier for `h4fiwa`.
- `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw attention --check`: both may exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET. Re-derive before and after; do not fix another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- A GREEN SUITE IS NOT BY ITSELF EVIDENCE THE GATE LANDED. The suite is green today WITH the bypass live, and a fix that silently failed to wire the predicate would leave it green. So the load-bearing evidence is V-01's and V-02's direct re-measurement of the refusals plus V-04's pre-fix failure demonstration; do not substitute the suite for either.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing.

## Spec / documentation sync

NO `.spec.md` FILE IS AMENDED, and that is a measured finding rather than an omission (F-08). The
contract this plan makes enforceable is ALREADY stated correctly in two places:
`attention_contract.APPROVAL_FLOOR` says the `implementing -> implemented` transition "requires a
RESOLVABLE evidence citation ... presence + format + resolvability", and `AGENTS.md` says an agent "may
NOT set `implemented` (needs cited evidence)". The code is being brought up to the documented contract,
not the reverse, so no requirement changes and no amendment is owed. `- Scope-Paths:` therefore declares
no `.spec.md`, and the run-end spec-edit reconciliation should report no declared and no actual spec
edits.

`AGENTS.md` NEEDS NO EDIT for the same reason: its statement is already true as policy and becomes true
as enforcement. `CHANGELOG.md` IS written (E-06) because a command that used to succeed now refuses,
which is a user-visible behavior change.

## Open questions

### OQ-01: should the untyped `aw set` surface accept `--evidence`, or should it refuse and redirect to `aw specs set`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED IN FAVOR OF ACCEPTING IT (E-02), from in-tree precedent plus measurement, so no maintainer decision is needed. The alternative (let the untyped surfaces refuse and tell the operator to use `aw specs set --evidence`) is defensible as fail-closed, but it would leave `aw set implemented <id6>` PERMANENTLY DEAD for specs: measured, `p_set` rejects `--evidence` at exit 2, so after E-01 there would be no argument that makes that surface work. The precedent is exact and recent: executed plan `47ttnv` faced the identical choice for the release-gate close predicate and registered plus DECLARED the flag, recording that "a flag that decides whether a release gate may be released should be declared rather than merely tolerated". The same holds for a flag deciding whether an implementation attestation may be written. Accepting it also costs nothing in safety, because the gate is the PREDICATE, not the flag's absence: an unresolvable citation still refuses (E-04 case (b) pins this). Reversible: removing the registration later is a one-line change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste rc and stderr for `aw specs set implemented <id6>` with (a) no `--evidence`, (b) an unresolvable `--evidence`, (c) a resolvable `--evidence`, each followed by the spec's path read back proving whether it moved and, for (a) and (b), that its content is byte-identical to before the call. Paste the same three for the `--status` spelling, and confirm the refusal reason on both contains `requires a resolvable --evidence citation`. Paste the new refusal message in full and confirm it names `.aw/records/plans/executed/` rather than only the legacy path (F-03).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw set --help` output showing `--evidence` registered. Paste rc for `aw set implemented <id6>` and `aw set specs implemented <id6>` WITHOUT the flag (both must be 1, spec unmoved) and WITH a resolvable citation (both must be 0, spec relocated to `implemented/`). Paste the value of `command_surface.get_declaration("set").legacy_flags` showing `--evidence` present, and paste a run of the existing declared-minus-accepted agreement test(s) for the `set` family showing no regression.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest "tests/test_status_set.py::SharedLifecycleRenderingTests::test_status_transition_color_rendering_and_ansi_controls" -o addopts=""` passing WITH E-01 and E-02 applied. Paste the diff of the repair and confirm in words that (i) the fixture now cites a real executed-IPD path, (ii) the bold-46 `implemented` assertions in BOTH the `set` and `find` legs are retained byte-unchanged, and (iii) no gate was weakened and no assertion deleted.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_specs_evidence_gate_parity.py -o addopts=""` naming every case as passed. Paste the PRE-FIX run of the same file (via `git stash` or a scratch checkout) showing the positional and untyped refusal cases FAILING, so the fix's effect is attributable rather than asserted. Confirm explicitly that the file contains the resolvable-citation SUCCESS case, the no-op fence, and the unrelated-transition fence, and that no test reads production source or counts callers.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste individual results for `tests/test_status_set.py`, `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_spec_review_attestation.py` and `tests/test_specs_from_backlog.py`. For any test the newly-firing gate broke beyond E-03's, give its name, the repair, and an explicit statement that the repair supplied legitimate evidence or constructed the state directly and did NOT weaken the gate. Confirm `GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` fails identically before and after (F-06) and was not touched.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line with its re-derived baseline alongside, and compare the FAILURE SETS BY NAME (not counts), showing the three pre-existing failures unchanged and no new failure. Paste the `CHANGELOG.md` hunk diffed, plus a search over that hunk for em and en dashes returning nothing. Paste `AW_NO_REEXEC=1 aw check release-gates`, `AW_NO_REEXEC=1 aw specs check` and `AW_NO_REEXEC=1 aw sanitize --agent`. Read back `h4fiwa` showing `- Status: open` and `- Blocks-Release: next` still present, proving this plan did NOT close its own carrier item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before any
execution. It carries `- Blocks-Release: next` inherited from backlog `h4fiwa` because it fixes a live
bug (`AGENTS.md`: we do not ship known bugs), and it is gated on NOTHING: it unions one refusal across
the existing dispatch fork rather than removing the fork, so it can be reviewed, approved and executed
independently of the larger unification work and of that work's blocking design question. That
independence is deliberate, so a release blocker is not held hostage to a design decision.

TWO THINGS A REVIEWER SHOULD WEIGH. FIRST, E-02 WIDENS A USER-FACING SURFACE by registering a new flag
on `aw set`; OQ-01 records why the alternative leaves that surface permanently dead for specs, but the
choice is reversible in one line if a reviewer prefers the redirect. SECOND, this plan OVERLAPS a
pending sibling plan that also claims these fixes as part of a larger Set; that sibling is `to-review`,
depends on two other children, and declares its carrier as the parent item rather than `h4fiwa`, so no
artifact currently carries `h4fiwa`'s gate but this one (measured through
`check_engine.evaluate_blocking_close`). If the maintainer prefers the Set to own this fix, retire THIS
plan to `superseded/` and add `- From-Backlog: h4fiwa` plus the gate to that sibling; do not simply
delete this plan, which would leave the release-gated item with no carrier.

Execution contract (`AGENTS.md`): commit ONLY the files this plan changed, limited to its declared
`Scope-Paths` plus any E-05 repair declared at execution time, through `aw commit <plan> -- <paths>`;
never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste ACTUAL runner output for
every test claim. Verify the staged set with `git diff --cached --name-only` before committing, and
re-verify after any failed commit attempt, because a rejecting hook can leave paths in the index that
you never staged.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence before the plan moves to
`.aw/records/plans/executed/`. Do NOT set backlog item `h4fiwa` to any status: this plan is its
`- From-Backlog:` carrier, so reaching `executed` closes its gate through the HANDOFF route and the
runner sets the item `graduated` on verification. An agent must never set it `done`.
