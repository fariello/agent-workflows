# IPD: Run the shared evidence predicate on the positional aw specs set implemented spelling

- Date: 2026-10-02
- Kind: child
- Concern: `aw specs set implemented <id6>` (the POSITIONAL spelling) moves a spec from `implementing` to `implemented` at exit 0 with NO `--evidence` citation, while `aw specs set <path> --status implemented` refuses the identical transition at exit 1. `AGENTS.md` states an agent "may NOT set `implemented` (needs cited evidence)", so the positional spelling lets an agent assert a spec is implemented with no cited executed IPD: a forged attestation of the same class the `Readiness` and `--by-human` rules exist to prevent. `specs.run_set` enforces the gate via `auth.get("evidence")` plus `specs._evidence_resolvable`; `status_set.validate_transition_allowed` has NO evidence branch at all. The bypass spelling is the shorter, more idiomatic one an agent is likelier to type. Two FURTHER surfaces share the hole and were measured here but are absent from the backlog item: `aw set implemented <id6>` and `aw set specs implemented <id6>` both exit 0 too, and neither even declares `--evidence`, so on those surfaces the gate is unreachable by any argument.
- Scope: IN: make the `implementing -> implemented` evidence requirement fire on every surface reaching `status_set.validate_transition_allowed`, by CONSUMING the existing `specs._evidence_resolvable` predicate rather than writing a second copy; register `--evidence` on the untyped `aw set` parser and declare it in that command's `CommandDeclaration`, so the refusal is satisfiable rather than merely unreachable; repair the one existing test this breaks; and pin the parity as paired outcome tests on both spellings. OUT, each with a reason recorded under "Deferred": the `deferred` gate-kind validation bypass (a separate measured defect under its own release-gated carrier `fv4b6s`); removing the `cli.main` dispatch fork itself (the durable fix, gated on a blocking maintainer decision); changing what `_evidence_resolvable` ACCEPTS; the post-write `validate_spec` conformance refusal; and the three pre-existing suite failures this plan neither causes nor fixes.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_specs_evidence_gate_parity.py, tests/test_status_set.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
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
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: wdyz5n verified (set setdispgate, attempt 1).
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Re-measured F-01/F-02 at review HEAD 9ccffaca3. Found the --status spelling already refuses an implemented no-op, so E-04's no-op fence is unpaired by design; required the stale legacy path fixed in both messages; replaced a nonexistent set agreement test with an E-04 assertion; surfaced that aw set --evidence also feeds the backlog close gate; corrected the stale h4fiwa open expectation (it is graduated); named m94eht as the overlapping sibling; added the scope fence and finalize ownership; replaced git stash with a scratch worktree.

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `h4fiwa`. The item's measurement was re-reproduced at this tree's HEAD `31b5ed6b9` rather than trusted, and the reproduction WIDENED it: two further surfaces (`aw set implemented`, `aw set specs implemented`) share the bypass and were not in the item. The fix's blast radius was measured by applying the fix in-memory and running the five candidate specs/status modules, which identified exactly ONE breaking test by name. Both of the item's open design questions (`_evidence_resolvable`'s accepted layout, and whether the repair can use `aw set --evidence`) were resolved from measurement and are recorded in "Findings".
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the `implementing -> implemented` evidence requirement unbypassable, so no spec reaches
`implemented` without a resolvable executed-IPD citation regardless of which spelling or which `set`
surface was used, and so the policy `AGENTS.md` already states is actually enforced by the code.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: close the predicate hole

- [x] E-01 In `status_set.validate_transition_allowed`, add the `implementing -> implemented` evidence requirement to the EXISTING `rec.record_type == "specs"` block, by consuming the SAME authority-table condition and the SAME resolvability predicate `specs.run_set` already consumes. `specs.run_set` reads `auth = A.TRANSITION_AUTHORITY.get(f"->{new}", {})` then `if auth.get("evidence"):` and requires `_evidence_resolvable(path, ev)`; the specs block in `validate_transition_allowed` already computes that identical `auth` dict for the `by_human`/`human_token` and `review_record` conditions, so the new branch reads one more key off a dict it already holds.

    CONSUME THE EXISTING PREDICATE; DO NOT WRITE A SECOND ONE. This is the whole point: the prior instances of this class were each fixed by DUPLICATING behavior into the second path, which is why instances keep being found. The precedent is EXACT, in-tree, and sits in the very function being edited: the `->reviewed` attestation branch immediately above already does `from agent_workflows import specs as _specs` and calls `_specs._review_attestation_refusal(...)`, under a comment stating that "a gate installed in only one of them is bypassed by choosing the other". Follow that shape: a local import of `specs` and a call to `specs._evidence_resolvable(rec.path, ev)`.

    PLACE IT INSIDE THE EXISTING `if old_status and old_status != norm_status:` GUARD, beside the sibling authority branches. That guard is load-bearing in a way that is cheap to get wrong: it makes a NO-OP re-set exempt, and the authority table governs TRANSITIONS, not identity. MEASURED: `attention_contract.transition_allowed("implemented", "implemented")` is `False` and the only legal source of `implemented` is `implementing`, so the guard cannot mask a real transition. The `->reviewed` branch's own comment records the same reasoning for the same guard.

    USE `rec.path` AS THE PREDICATE'S FIRST ARGUMENT, not a reconstructed path. `_evidence_resolvable` walks up from that path via `specs._spec_repo_root` to find the repo root, and `read_artifact_record` supplies a real on-disk path, so passing `rec.path` is correct and needs no `repo_root` plumbing.

    THE REFUSAL MUST WRITE NOTHING. This function is called from `run_set_command`'s pre-flight loop, BEFORE the dry-run branch and BEFORE `apply_status_change`, which is what makes a refusal leave the spec byte-identical and un-relocated. Return `(False, <one-line reason>)` in the established shape; do not raise, and do not print.

    PRESERVE THE REASON TEXT IN SUBSTANCE. `specs.run_set` writes `aw specs set: implementing -> implemented requires a resolvable --evidence citation (an existing .agents/plans/executed/ IPD path); refused.`. This function serves several verbs so its prefix differs and `validate_transition_allowed` returns a ONE-LINE reason; keep the phrase `requires a resolvable --evidence citation` so one needle matches both surfaces, and name the recovery.

    CORRECT THE STALE PATH IN BOTH MESSAGES, NOT ONLY THE NEW ONE (F-03). The new `status_set` reason MUST name `.aw/records/plans/executed/` (the legacy `.agents/plans/executed/` may be named beside it). ALSO update the existing `specs.run_set` message the same way: otherwise the two spellings emit DIFFERENT recovery paths for the same refusal, which is the very drift this plan exists to close, and V-01 asks both to be confirmed. This is the `agent_workflows/specs.py` edit `Scope-Paths` declares. No in-tree test pins the old wording (searched `tests/` for `agents/plans/executed/ IPD` and `resolvable --evidence`: no hits at review HEAD `9ccffaca3`), so the wording change breaks nothing.

    DO NOT RE-READ `TRANSITION_AUTHORITY` A SECOND TIME. The specs block already binds `auth = ac.TRANSITION_AUTHORITY.get(f"->{norm_status}", {})`; read `auth.get("evidence")` off that binding.

    FORWARDED-NAMESPACE CALLERS ARE SAFE BUT MUST STAY SO. `work_cmd.run_finish` and `status_set`'s `Item-Dependencies` writer call `run_set_command` with a hand-built `argparse.Namespace` carrying no `evidence` attribute; both are `scoped_type="plans"`, never reach the specs block, and so are unaffected. Read the flag with `getattr(args, "evidence", None)` (never `args.evidence`) so a future hand-built specs namespace refuses cleanly instead of raising `AttributeError`.
  - Depends on: none
  - Expected outcome: `aw specs set implemented <id6>` with no `--evidence` exits 1 and leaves the spec in `implementing/` byte-identical; with an unresolvable `--evidence` exits 1 and writes nothing; with a resolvable citation exits 0 and relocates the file; `aw specs set <path> --status implemented` behaves identically in all three cases.
  - Execution state: performed

- [x] E-02 Make the gate SATISFIABLE on the untyped `aw set` surface, by registering `--evidence` on the `p_set` parser in `cli.py` and adding it to the `command="set"` `CommandDeclaration.legacy_flags` in `command_surface.py`. WITHOUT THIS, E-01 CONVERTS ONE BUG INTO ANOTHER: `aw set implemented <id6>` and `aw set specs implemented <id6>` both reach `run_set_command` and so both start refusing, but `p_set` declares no `--evidence` (MEASURED: `aw set --help` does not mention it, and passing it exits 2 with `unrecognized arguments: --evidence`), so on those surfaces the transition would become impossible by ANY argument rather than merely gated.

    THE PRECEDENT IS EXACT AND RECENT. Executed plan `47ttnv` E-03 and E-06 did precisely this pair of steps for the release-gate close predicate: make the flag REACH the predicate on the second path, then DECLARE it on the `CommandDeclaration` because "a flag that decides whether a release gate may be released should be declared rather than merely tolerated". The same reasoning applies verbatim to a flag that decides whether an implementation attestation may be written.

    HELP TEXT MUST NAME THE ARTIFACT CLASS, not just the flag. `p_specs_set`'s existing registration says "Resolvable implementation-evidence citation (for implemented)". Match that, and add that the citation must be an existing executed-IPD path, since that is what the predicate actually enforces and an operator told only "resolvable" cannot guess the executed/ requirement.

    DO NOT make the flag-agreement test bidirectional and do not touch any other `CommandDeclaration`. The `set` declaration gains exactly one entry.

    THE NEW FLAG ALSO REACHES THE BACKLOG CLOSE-GATE ON `aw set`, AND THAT IS INTENDED. `run_set_command`'s backlog arm already reads `getattr(args, "evidence", None)` into `check_engine.evaluate_blocking_close` (and the Close-Evidence write in `apply_status_change` reads it too), so registering `--evidence` on `p_set` makes `aw set done <backlog-item> --evidence <path>` able to take the SATISFIED route, matching `aw backlog set done`. Say so in the help text (the citation also satisfies a backlog release gate) so the flag's two meanings are not a surprise, and pin it with one E-04 case. Use `dest="evidence"` so both arms read the same attribute.

    NO AGREEMENT TEST COVERS THE `set` DECLARATION TODAY. The declared-minus-accepted assertions in `tests/` (`test_backlog_handoff_close.py`, `test_prompts_new.py`, `test_group_verb_policy.py`, `test_runs_repo_alias.py`) cover other verbs only, so there is no existing `set` test to "not regress". E-04 therefore carries one assertion of its own: `set(get_declaration("set").legacy_flags) - <option strings accepted by the real `aw set` subparser>` is empty and `--evidence` is in `legacy_flags`, deriving the accepted set from the built parser's `_actions` exactly as `test_backlog_handoff_close.py` does (that drives the parser; it is not source-reading).
  - Depends on: E-01
  - Expected outcome: `aw set --help` lists `--evidence`; `aw set implemented <id6> --evidence <resolvable executed-IPD path>` exits 0 and relocates the spec; the same call without the flag exits 1; `command_surface.get_declaration("set").legacy_flags` contains `--evidence` and is a subset of the options the real `aw set` parser accepts.
  - Execution state: performed

### Task group 2: repair the one test this breaks

- [x] E-03 Repair `tests/test_status_set.py::SharedLifecycleRenderingTests::test_status_transition_color_rendering_and_ansi_controls`, which reaches `implemented` through the BYPASS as a FIXTURE STEP and therefore breaks the moment E-01 lands. THIS IS NOT OPTIONAL CLEANUP: without it this plan cannot satisfy its own V-06 bare-suite requirement.

    MEASURED, NOT PREDICTED. The fix was applied in-memory and the five candidate modules (`tests/test_status_set.py`, `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_spec_review_attestation.py`, `tests/test_specs_from_backlog.py`) were run: `2 failed, 157 passed`, and ONE of those two failures is the pre-existing `test_every_real_spec_in_this_repository_still_conforms` (F-06). So this test is the WHOLE test-side cost. It calls `self.create_spec(..., status="implementing")` then `self._echo(["set", "implemented", "bbb222"])` and asserts the bold-green-46 `implemented` token appears in both the set output and a subsequent `find`. Its subject is COLOR RENDERING; reaching `implemented` is incidental to it.

    THE REPAIR IS TO MAKE THE FIXTURE'S CITATION LEGITIMATE, NEVER TO WEAKEN THE GATE. A fixture that needs a gate disabled is telling you the fixture is wrong. Write a real executed-IPD file into the test repo's `.aw/records/plans/executed/` and pass `--evidence <that relative path>`. MEASURED: with E-01 and E-02 applied, `cli.main(["set","implemented","bbb222","--evidence",<rel>, ...])` exits 0 and the asserted needle `\033[1;38;5;46mimplemented\033[0m` IS present, so the test's actual subject survives intact. Do NOT switch the assertion to a different status, which would silently delete the `done`-class color coverage, and do NOT delete the spec leg of the test.

    `self._echo` APPENDS `--yes --dir <root>`, so pass `--evidence` inside the `argv` list it is given. The repo root is `self.repo_root`; write the evidence artifact relative to it and cite the repo-relative path, because `_evidence_resolvable` joins the citation onto the root it derives from the spec.
  - Depends on: E-01, E-02
  - Expected outcome: `test_status_transition_color_rendering_and_ansi_controls` passes with E-01 and E-02 applied, still asserting the bold-46 `implemented` token in BOTH the `set` output and the `find` output, with the fixture citing a real executed-IPD path; no assertion weakened or removed.
  - Execution state: performed

### Task group 3: pin the parity on every surface

- [x] E-04 Author `tests/test_specs_evidence_gate_parity.py` pinning the refusal on BOTH spellings and on BOTH untyped surfaces. Drive `cli.main` and assert on exit code, the spec's resulting LOCATION, and its resulting CONTENT. Pass `--no-commit` and `--yes` on every invocation. Model the helper shape on `tests/test_backlog_positional_close_gate.py` (one temp repo per test, `cli.main` under `redirect_stdout`/`redirect_stderr`), which is the established template for exactly this both-spellings property.

    THE PAIRING IS THE POINT AND IS NOT DECORATION. For each case, run BOTH spellings against IDENTICAL fresh repos and assert the SAME exit code and the SAME resulting on-disk state. A test pinning only the positional spelling would still pass if a later change broke the `--status` spelling instead, which is the very drift this plan exists to close.

    COVER, on each of `aw specs set implemented <id6>` and `aw specs set <path> --status implemented`: (a) no `--evidence` refuses, rc 1, file byte-identical AND still in `implementing/`; (b) an unresolvable `--evidence` refuses identically; (c) a RESOLVABLE `--evidence` succeeds, exits 0, and relocates the file into `implemented/`. CASE (c) IS NOT OPTIONAL: without it a "fix" that refuses unconditionally would pass (a) and (b) while breaking the verb entirely, and that is the single likeliest way to get this wrong.

    ADD the two untyped surfaces, `aw set implemented <id6>` and `aw set specs implemented <id6>`, each asserting the refusal without `--evidence` and the success with it (the latter is what proves E-02 landed). ADD the NO-OP fence: an already-`implemented` spec re-set to `implemented` through the POSITIONAL spelling (and `aw set`) must NOT be retroactively refused, since `old == new` is not a transition. THIS FENCE IS DELIBERATELY NOT PAIRED, and the test must say why: MEASURED at review HEAD `9ccffaca3`, `aw specs set <path> --status implemented` on an already-`implemented` spec ALREADY exits 1 with the evidence refusal, because `specs.run_set`'s `if auth.get("evidence"):` is not guarded by `old != new`. That is a pre-existing `--status`-spelling behavior this plan does NOT change (the root-cause unification is carried by `fcnz1r`/`m94eht`); assert the positional no-op succeeds and do NOT assert the `--status` no-op either way, so the test neither pins nor contradicts it. ADD the `aw set` backlog leg E-02 names: on a release-gated backlog item, `aw set done <item> --evidence <in-tree artifact>` closes via the SATISFIED route (rc 0) where the same call without it refuses. ADD the declaration-agreement assertion E-02 names. ADD the negative fence: an unrelated spec transition that is not evidence-gated (for example `draft -> to-review`) still succeeds with no `--evidence`, which is what bounds this gate's blast radius.

    ASSERT THE ABSENCE OF THE WRITE, NOT ONLY THE EXIT CODE. A test checking only `rc == 1` would pass against a half-fix that refuses AFTER relocating the file. Read the file back from its original path and assert byte-identical content and an unchanged status directory.

    NO CODE-PINNING. Do not read production source with `inspect`, `ast`, regex or substring search, do not count callers, and do not assert docstring or comment text (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16).
  - Depends on: E-01, E-02
  - Expected outcome: a new module whose cases pass on both spellings and both untyped surfaces after E-01 and E-02, with every refusal case asserting content and location as well as exit code, and with the pre-fix failure output pasted for the positional cases so the fix's effect is attributable.
  - Execution state: performed

- [x] E-05 Confirm no OTHER test pinned the bypass as correct behavior, by running the five candidate modules individually and pasting each result. The modules are `tests/test_status_set.py`, `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_spec_review_attestation.py` and `tests/test_specs_from_backlog.py`, chosen because they are the modules that drive specs transitions.

    THE RISK THIS ITEM EXISTS TO CATCH is a second fixture of the `E-03` shape that the in-memory probe missed because the probe patched only one function. If one is found, repair it the SAME way E-03 does (supply a legitimate citation, or construct the `implemented` state directly on disk), never by weakening the gate, and say so explicitly in the evidence.

    NOTE the one EXPECTED failure and do not chase it: `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` is RED AT BASE on this tree for an unrelated reason (F-06), already filed as backlog `6bolin`. Confirm it fails identically before and after; do not fix it here.
  - Depends on: E-01, E-02
  - Expected outcome: each of the five modules' results pasted; any test broken by the newly-firing gate named, repaired by supplying legitimate evidence or constructing the state directly, with the repair justified; no gate weakened; `6bolin`'s failure confirmed identical before and after.
  - Execution state: performed

### Task group 4: record the user-visible change

- [x] E-06 Add ONE `CHANGELOG.md` entry in the file's established voice, describing the user-visible effect: `aw specs set` and `aw set` now refuse to mark a spec implemented unless a resolvable evidence citation is supplied, whichever spelling is used, and `aw set` now accepts `--evidence` so that citation can be given. THIS IS A BEHAVIOR CHANGE A USER CAN HIT (a command that used to succeed now refuses), so it belongs in the changelog.

    Name no private predicate and no internal function. Write no em or en dashes (user-facing prose, `AGENTS.md`).

    DO NOT CLOSE THE BACKLOG ITEM. `h4fiwa` carries `- Blocks-Release: next` and this plan is its `- From-Backlog:` carrier, so the HANDOFF route closes the gate automatically once this plan is `executed`; MEASURED via `check_engine.evaluate_blocking_close`, which today reports the gate "handed off to From-Backlog carrier(s) ... but the work has not shipped" and names `aw backlog set h4fiwa --status graduated` as the fix. Leaving the item alone is therefore correct: it is ALREADY `graduated` (set by run `run-20261001T221821Z-1985969` naming `wdyz5n`), the gate closes through the HANDOFF route once this plan is `executed`, and an agent must never set it `done`.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: one CHANGELOG entry naming the refusal and the new `aw set --evidence` flag, containing no em or en dash; `h4fiwa` left untouched, its `- Status:` unchanged from its pre-execution value (`graduated` at review HEAD `9ccffaca3`, `Graduated-To: setdispgate`) and its `- Blocks-Release: next` intact.
  - Execution state: performed

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

- Over-scope: none. Every path in `- Scope-Paths:` is edited by a numbered E-item: `agent_workflows/status_set.py` (E-01), `agent_workflows/specs.py` (E-01, the existing `specs.run_set` refusal message is corrected to name `.aw/records/plans/executed/`; the predicate itself is consumed unchanged), `agent_workflows/cli.py` (E-02), `agent_workflows/command_surface.py` (E-02), `tests/test_status_set.py` (E-03), `tests/test_specs_evidence_gate_parity.py` (E-04), `CHANGELOG.md` (E-06). E-05 is a verification item that edits nothing unless it finds a second broken fixture.
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

- [x] V-01 validates E-01
  - Required evidence: paste rc and stderr for `aw specs set implemented <id6>` with (a) no `--evidence`, (b) an unresolvable `--evidence`, (c) a resolvable `--evidence`, each followed by the spec's path read back proving whether it moved and, for (a) and (b), that its content is byte-identical to before the call. Paste the same three for the `--status` spelling, and confirm the refusal reason on both contains `requires a resolvable --evidence citation`. Paste BOTH refusal messages in full (the positional and the `--status` spelling) and confirm EACH names `.aw/records/plans/executed/` rather than only the legacy path (F-03).
  - Observed evidence:
    --- Positional spelling: aw specs set implemented sp0001 ---
    Case (a) no --evidence:
      rc: 1
      stdout: FAIL     Validation error on 20261002-setbeta-01-sp0001-test.spec.md: implementing -> implemented requires a resolvable --evidence citation (an existing .aw/records/plans/executed/ IPD path). Refusing before making changes.
      stderr: (empty)
      path read back: .aw/records/specs/implementing/20261002-setbeta-01-sp0001-test.spec.md
      content byte-identical: True
    Case (b) unresolvable --evidence .aw/records/plans/executed/nonexistent.ipd.md:
      rc: 1
      stdout: FAIL     Validation error on 20261002-setbeta-01-sp0001-test.spec.md: implementing -> implemented requires a resolvable --evidence citation (an existing .aw/records/plans/executed/ IPD path). Refusing before making changes.
      stderr: (empty)
      path read back: .aw/records/specs/implementing/20261002-setbeta-01-sp0001-test.spec.md
      content byte-identical: True
    Case (c) resolvable --evidence .aw/records/plans/executed/20261002-setbeta-01-ex0001-test.ipd.md:
      rc: 0
      stdout: -    spec        20261002-setbeta-01-sp0001  implementing → ✓  implemented
      stderr: (empty)
      path read back: .aw/records/specs/implemented/20261002-setbeta-01-sp0001-test.spec.md
      content updated to Status: implemented

    --- Status spelling: aw specs set <path> --status implemented ---
    Case (a) no --evidence:
      rc: 1
      stdout: (empty)
      stderr: aw specs set: implementing -> implemented requires a resolvable --evidence citation (an existing .aw/records/plans/executed/ IPD path); refused.
      path read back: .aw/records/specs/implementing/20261002-setbeta-01-sp0001-test.spec.md
      content byte-identical: True
    Case (b) unresolvable --evidence .aw/records/plans/executed/nonexistent.ipd.md:
      rc: 1
      stdout: (empty)
      stderr: aw specs set: implementing -> implemented requires a resolvable --evidence citation (an existing .aw/records/plans/executed/ IPD path); refused.
      path read back: .aw/records/specs/implementing/20261002-setbeta-01-sp0001-test.spec.md
      content byte-identical: True
    Case (c) resolvable --evidence .aw/records/plans/executed/20261002-setbeta-01-ex0001-test.ipd.md:
      rc: 0
      stdout: aw specs set: .../.aw/records/specs/implemented/20261002-setbeta-01-sp0001-test.spec.md -> implemented
      stderr: (empty)
      path read back: .aw/records/specs/implemented/20261002-setbeta-01-sp0001-test.spec.md

    Refusal messages in full:
    Positional: "FAIL     Validation error on 20261002-setbeta-01-sp0001-test.spec.md: implementing -> implemented requires a resolvable --evidence citation (an existing .aw/records/plans/executed/ IPD path). Refusing before making changes."
    Status: "aw specs set: implementing -> implemented requires a resolvable --evidence citation (an existing .aw/records/plans/executed/ IPD path); refused."
    Both contain "requires a resolvable --evidence citation" and name ".aw/records/plans/executed/".
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `aw set --help` output showing `--evidence` registered. Paste rc for `aw set implemented <id6>` and `aw set specs implemented <id6>` WITHOUT the flag (both must be 1, spec unmoved) and WITH a resolvable citation (both must be 0, spec relocated to `implemented/`). Paste the value of `command_surface.get_declaration("set").legacy_flags` showing `--evidence` present, and paste the E-04 declaration-agreement case passing (declared minus the real `aw set` parser's accepted options is empty). Paste `aw set done <release-gated backlog item> --evidence <in-tree artifact>` rc 0 and the same without `--evidence` refusing, showing the flag reaches the backlog close gate on this surface too.
  - Observed evidence:
    1. aw set --help output:
       [--graduated-to GRADUATED_TO] [--evidence EVIDENCE]
       --evidence EVIDENCE   Resolvable implementation-evidence citation (for specs implemented; satisfies a backlog release gate on done).

    2. Untyped setter executions without and with --evidence:
       aw set implemented sp0001 without --evidence -> rc: 1, loc: implementing
       aw set implemented sp0001 with --evidence -> rc: 0, loc: implemented
       aw set specs implemented sp0001 without --evidence -> rc: 1, loc: implementing
       aw set specs implemented sp0001 with --evidence -> rc: 0, loc: implemented

    3. command_surface.get_declaration("set").legacy_flags:
       ('--message', '--by-human', '--actor', '--scope-reason', '--scope-ack', '--gate-kind', '--gate-ref', '--gate-summary', '--blocks-release', '--evidence', '--dry-run', '--json', '--agent')
       '--evidence' in decl.legacy_flags is True.
       Real aw set parser accepted option strings contains '--evidence'.
       set(decl.legacy_flags) - accepted == set() (empty set).
       tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_set_declaration_agreement PASSED.

    4. Backlog release-gate close with --evidence:
       aw set done bk0001 without --evidence -> rc: 1, loc: open (refused)
       aw set done bk0001 with --evidence -> rc: 0, loc: done (closed SATISFIED)
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest "tests/test_status_set.py::SharedLifecycleRenderingTests::test_status_transition_color_rendering_and_ansi_controls" -o addopts=""` passing WITH E-01 and E-02 applied. Paste the diff of the repair and confirm in words that (i) the fixture now cites a real executed-IPD path, (ii) the bold-46 `implemented` assertions in BOTH the `set` and `find` legs are retained byte-unchanged, and (iii) no gate was weakened and no assertion deleted.
  - Observed evidence:
    $ python3 -m pytest "tests/test_status_set.py::SharedLifecycleRenderingTests::test_status_transition_color_rendering_and_ansi_controls" -o addopts=""
    ============================= test session starts ==============================
    rootdir: ...
    tests/test_status_set.py .                                               [100%]
    ============================== 1 passed in 1.63s ===============================

    Diff of repair:
    --- a/tests/test_status_set.py
    +++ b/tests/test_status_set.py
    @@ -1813,7 +1813,18 @@ class SharedLifecycleRenderingTests(StatusSetTestBase):
                 "setbeta",
                 status="implementing",
             )
    -        _rc, set_out = self._echo(["set", "implemented", "bbb222"])
    +        (self.repo_root / ".aw" / "records" / "plans" / "executed").mkdir(
    +            parents=True, exist_ok=True
    +        )
    +        ev_plan = self.create_plan(
    +            "20260822-setbeta-02-ev1234-evidence.ipd.md",
    +            "ev1234",
    +            "setbeta",
    +            status="executed",
    +            disposition="executed",
    +        )
    +        rel_ev = str(ev_plan.relative_to(self.repo_root))
    +        _rc, set_out = self._echo(["set", "implemented", "bbb222", "--evidence", rel_ev])
             _rc2, find_out = self._echo(["find", "specs", "bbb222"], confirm=False)
             needle = "\033[1;38;5;46mimplemented\033[0m"
             self.assertIn(needle, set_out)

    Confirmation:
    (i) The fixture now creates and cites a real executed IPD path (rel_ev).
    (ii) The bold-46 'implemented' assertions in both set and find legs ('self.assertIn(needle, set_out)' and 'self.assertIn(needle, find_out)') are retained byte-unchanged.
    (iii) No gate was weakened and no assertion was deleted.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_specs_evidence_gate_parity.py -o addopts=""` naming every case as passed. Paste the PRE-FIX run of the same file against the base commit's source (a scratch `git worktree add` at the pre-execution HEAD with the new test file copied in; NEVER a bare `git stash`, which in a shared checkout sweeps other parties' changes) showing the positional and untyped refusal cases FAILING, so the fix's effect is attributable rather than asserted. Confirm explicitly that the file contains the resolvable-citation SUCCESS case, the positional no-op fence (and that it does NOT assert the `--status` no-op either way), the unrelated-transition fence, the `aw set` backlog `--evidence` leg, and the declaration-agreement assertion, and that no test reads production source or counts callers.
  - Observed evidence:
    Post-fix test run with every case named:
    $ python3 -m pytest tests/test_specs_evidence_gate_parity.py -v -o addopts=""
    tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_paired_case_b_unresolvable_evidence_refuses_and_writes_nothing PASSED [ 12%]
    tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_set_declaration_agreement PASSED [ 25%]
    tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_positional_no_op_fence PASSED [ 37%]
    tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_paired_case_a_no_evidence_refuses_and_writes_nothing PASSED [ 50%]
    tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_aw_set_backlog_done_evidence_leg PASSED [ 62%]
    tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_untyped_set_implemented_parity PASSED [ 75%]
    tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_unrelated_transition_negative_fence PASSED [ 87%]
    tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_paired_case_c_resolvable_evidence_succeeds_and_relocates PASSED [100%]
    ============================== 8 passed in 2.89s ===============================

    Pre-fix run against base commit source (showing positional and untyped failures):
    $ python3 -m pytest tests/test_specs_evidence_gate_parity.py -o addopts=""
    FAILED tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_set_declaration_agreement
    FAILED tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_untyped_set_implemented_parity (AssertionError: 0 != 1 : aw set implemented without evidence must refuse)
    FAILED tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_paired_case_a_no_evidence_refuses_and_writes_nothing (AssertionError: 0 != 1 : Positional spelling should refuse with rc 1)
    FAILED tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_aw_set_backlog_done_evidence_leg (SystemExit: 2 on unrecognized argument --evidence)
    FAILED tests/test_specs_evidence_gate_parity.py::SpecsEvidenceGateParityTests::test_paired_case_b_unresolvable_evidence_refuses_and_writes_nothing (AssertionError: 0 != 1 : Positional spelling should refuse with rc 1)
    ========================= 5 failed, 3 passed in 2.78s ==========================

    Confirmation:
    The test module contains:
    - Resolvable-citation SUCCESS case: test_paired_case_c_resolvable_evidence_succeeds_and_relocates
    - Positional no-op fence: test_positional_no_op_fence (with explicit documentation and no assertion on --status either way)
    - Unrelated-transition fence: test_unrelated_transition_negative_fence (draft -> to-review)
    - aw set backlog --evidence leg: test_aw_set_backlog_done_evidence_leg
    - Declaration-agreement assertion: test_set_declaration_agreement
    - No test reads production source using inspect/ast/regex/line-count or counts callers.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste individual results for `tests/test_status_set.py`, `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_spec_review_attestation.py` and `tests/test_specs_from_backlog.py`. For any test the newly-firing gate broke beyond E-03's, give its name, the repair, and an explicit statement that the repair supplied legitimate evidence or constructed the state directly and did NOT weaken the gate. Confirm `GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` fails identically before and after (F-06) and was not touched.
  - Observed evidence:
    Individual results:
    1. tests/test_status_set.py:
       106 passed in 47.65s
    2. tests/test_specs_verbs.py:
       20 passed in 0.89s
    3. tests/test_specs_status_dirs.py:
       8 passed in 1.73s
    4. tests/test_spec_review_attestation.py:
       30 passed in 2.25s
    5. tests/test_specs_from_backlog.py:
       8 passed in 0.79s
    Total: 172 passed across all 5 candidate modules.

    No tests beyond E-03's were broken by the newly-firing gate.
    GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms in tests/test_spec_review_attestation.py was not touched and passes:
    tests/test_spec_review_attestation.py . [1 passed in 1.73s]
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line with its re-derived baseline alongside, and compare the FAILURE SETS BY NAME (not counts), showing the three pre-existing failures unchanged and no new failure. Paste the `CHANGELOG.md` hunk diffed, plus a search over that hunk for em and en dashes returning nothing. Paste `AW_NO_REEXEC=1 aw check release-gates`, `AW_NO_REEXEC=1 aw specs check` and `AW_NO_REEXEC=1 aw sanitize --agent`. Read back `h4fiwa` showing its `- Status:` unchanged from the pre-execution read (expected `graduated`) and `- Blocks-Release: next` still present, proving this plan did NOT close its own carrier item. Paste `git grep -n 'agents/plans/executed/ IPD' -- agent_workflows/` returning nothing, proving neither refusal message still names only the legacy path.
  - Observed evidence:
    1. Bare `python3 -m pytest` summary comparison:
       Re-derived pre-execution baseline (at HEAD 0bd481ad14):
         6560 passed, 2 skipped, 3 warnings in 291.56s
       Post-fix execution result:
         6568 passed, 2 skipped, 3 warnings in 286.70s (0:04:46)
       Failure sets by name:
         Baseline failure set: set() (empty)
         Post-fix failure set: set() (empty)
         New failures: none. Net difference is exactly +8 passed (the 8 new tests in tests/test_specs_evidence_gate_parity.py).

    2. CHANGELOG.md hunk diff:
       diff --git a/CHANGELOG.md b/CHANGELOG.md
       index a88340d6f..c64508c3e 100644
       --- a/CHANGELOG.md
       +++ b/CHANGELOG.md
       @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

        Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

       +- Fixed: aw specs set and aw set now refuse to mark a spec implemented unless a resolvable evidence citation is supplied, whichever spelling is used, and aw set now accepts --evidence so that citation can be given.
        - Added: documented CommandDeclaration.exit_contract as enumerating codes produced by a command's own return path while excluding signal-derived codes (130/143), pinned by a conformance gate on the universal 130 floor (D162).
        - Fixed: failed backlog or spec mutations no longer record phantom history events in the sidecar log if their durable file write fails, preventing false transition records from being shown to operators.

       Em and en dash search over CHANGELOG hunk:
         Dashes found: [] (clean, zero em or en dashes)

    3. Repository checks:
       AW_NO_REEXEC=1 aw check release-gates:
         AW check  release-gates                                                  2672 ms
         ✓ CONFORMS  355 release-gates checked
         Evidence
           backlog  230   specs  21   plans  103   releases  1
           errors  0   warnings  0   info  0
         Next  aw releases list
         Agent output: --agent

       AW_NO_REEXEC=1 aw specs check:
         aw specs check: all specs conform. 40 specs checked.

       AW_NO_REEXEC=1 aw sanitize --agent:
         {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}

    4. Read back h4fiwa:
       aw find backlog h4fiwa:
         ●  graduated     h4fiwa  .aw/records/backlog/graduated/20261001-setdispgate-01-h4fiwa-positional-specs-implemented-skips-evidence-gate.backlog.md
       Front-matter check:
         - Id: h4fiwa
         - Status: graduated
         - Graduated-To: setdispgate
         - Blocks-Release: next
       Carrier item remains graduated and unclosed.

    5. Refusal message legacy path check:
       git grep -n 'agents/plans/executed/ IPD' -- agent_workflows/:
         agent_workflows/attention_contract.py:623:    ".agents/plans/executed/ IPD path), not merely a well-formed string; aw specs enforces presence + "
       Neither refusal message names the legacy path; both specs.py:769 and status_set.py:787 now cite (.aw/records/plans/executed/ IPD path). The single occurrence in attention_contract.py is non-user-facing docstring contract commentary preserved per DECISION 19-wdyz5n-D1 to strictly maintain the 7-file Scope-Paths fence.
  - Result: pass

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
choice is reversible in one line if a reviewer prefers the redirect. SECOND, this plan OVERLAPS pending
plan `m94eht` (setdisp Order 04, "make aw specs set --status a thin adapter delegating to the shared
engine"), which also edits `specs.py`, `status_set.py` and `cli.py`; at review HEAD `9ccffaca3` it is
`- Status: draft`, depends on `executed:m1jlwm` and `state:spec:approved:wy9aru`, and carries
`- From-Backlog: fcnz1r` rather than `h4fiwa`, so no artifact carries `h4fiwa`'s gate but this one.
Whichever of the two executes SECOND must consume the evidence branch the first installed rather than
add a second copy. If the maintainer prefers the Set to own this fix, retire THIS plan to
`superseded/` and add `- From-Backlog: h4fiwa` plus the gate to `m94eht`; do not simply delete this
plan, which would leave the release-gated item with no carrier.

SCOPE FENCE: `- Scope-Paths:` is a DECLARATION so finalize can reconcile what was edited against what
was declared, not a stop condition. An out-of-scope edit the work genuinely requires (for example an
E-05 fixture repair in a module not listed) is made and then justified at finalize with
`--scope-reason`; a declared-but-unmodified path is acknowledged with `--scope-ack`. STOP and report
only for a genuinely unsafe condition: an unresolvable concurrent edit to a declared path, or an
absent prerequisite symbol (`specs._evidence_resolvable`, `status_set.validate_transition_allowed`).

Execution contract (`AGENTS.md`): commit ONLY the files this plan changed, limited to its declared
`Scope-Paths` plus any E-05 repair declared at execution time, through `aw commit <plan> -- <paths>`;
never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste ACTUAL runner output for
every test claim. Verify the staged set with `git diff --cached --name-only` before committing, and
re-verify after any failed commit attempt, because a rejecting hook can leave paths in the index that
you never staged.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence before the plan moves to
`.aw/records/plans/executed/`. Under `aw oc run` / `aw agy run` the RUNNER performs the finalize and
the move, so do not invoke it yourself; executed by hand, the executor performs it via
`aw ipd finalize`. Never hand-edit the status line or hand-move the file, and never tag or release.
Do NOT set backlog item `h4fiwa` to any status: it is already `graduated` and this plan is its
`- From-Backlog:` carrier, so reaching `executed` makes its gate closable through the HANDOFF route.
An agent must never set it `done`.
