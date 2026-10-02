# IPD: Refuse a contradictory verification flag pair on oc run, as agy already does

- Date: 2026-09-29
- Kind: child
- Concern: On the opencode host, all six verification spellings are aliases of ONE `argparse.BooleanOptionalAction` on dest `validate`, so a contradictory pair such as `--no-verify --validate` parses SILENTLY and is resolved by argparse last-wins. Antigravity REFUSES the same pair before the run starts (`agy_runipd.verification_flag_tristate` raising `runner_shared.RunFlagRefusal`), and its docstring states the reasoning that applies verbatim to opencode: "Letting either spelling silently win would make a verification decision the operator did not make, and BOTH directions of that error are bad: one skips a check that was asked for, the other pays for a check that was declined." The result on oc is a verification decision the operator did not make, in the command whose whole purpose is deciding whether work is independently verified, silent in both directions. RE-MEASURED AT THIS HEAD rather than inherited: the item's defect reproduces exactly (F-01), and two of its claims are CORRECTED - its proposed lift-into-`runner_shared` fix is measured unusable as stated (F-05) and agy is measured to carry a NARROWER form of the same hole the item does not report (F-06).
- Scope: Give oc the pre-run refusal agy has, via a `BooleanOptionalAction` subclass in `runner_shared` that RECORDS which spellings the operator actually typed, plus one shared predicate both hosts call. Covers oc `start` and oc `resume` (both register the six spellings and both currently resolve a pair by last-wins), closes the narrower agy same-action hole F-06 measures with the same predicate, and amends spec `25kzda` Section 2.1c plus its pinning test, both of which currently DECLARE the order-dependent behavior this plan removes. ON `resume` THE REFUSAL SITS AT THE HEAD OF THE BRANCH, not merely before the `validate` write, because F-11 measures that the intervening `apply_run_policy_flags_on_resume` would otherwise let a REFUSED invocation durably flip an unrelated frozen policy. CHANGES NO DEST TABLE: all 24 cells of the per-host mapping 2.1c declares are preserved byte-for-byte, and no spelling is added, removed, or renamed on either host.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: byazcp
- Blocks-Release: next
- Set: byazcp
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: zdgc6t
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set; /plan-review by opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-B01 (HIGH, fixed), PR-B02 (MEDIUM, fixed), PR-B03 (MEDIUM, fixed), PR-B04 (MEDIUM, fixed), PR-B05 (LOW, fixed). Every one of F-01 through F-10 was re-driven at this HEAD and all ten reproduce. Three NEW findings recorded as F-11 (the resume seam E-04 named was downstream of a writing helper, so a REFUSED resume would have flipped options.full_auto durably), F-12 (the pre-commit backstop E-06 invoked does not read specs at all), and F-13 (the private argparse._StoreTrueAction subclass was unnecessary). OQ-02's resolution was corrected: the two agy checks are not disjoint on a real parse, so E-05 now specifies their ORDER. Suite at review: 3387 passed, 2 skipped in 58.22s.

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `byazcp`. EVERY measurement re-taken by driving the code at this working tree; none carried over from the item. The item's defect reproduces exactly (F-01) and its stated OBSTACLE is confirmed (F-04), but two of its claims are corrected: its suggested fix of lifting `verification_flag_tristate`'s check into `runner_shared` is measured UNUSABLE as stated, because that function reads a namespace and the namespace is precisely what cannot distinguish the spellings (F-05); and agy carries a NARROWER form of the same hole, on `--validate --no-validate`, which the item does not report and which this plan closes with the same predicate (F-06). The chosen mechanism was driven end-to-end against the real oc parser before being written down (F-03). OQ-01 records the one genuinely open authoring decision, with the measurement that resolved it.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw oc run` refuse a contradictory verification flag pair before it starts a run, instead of silently picking whichever spelling happened to come last, so that the verification decision a run acts on is always one the operator actually made. After this plan the reasoning agy's docstring already states holds on both hosts, the spec sentence that currently declares oc's order-dependence declares the refusal instead, and the narrower same-action hole this authoring measured on agy is closed by the same predicate rather than left as a second copy of the defect.

WHY THIS IS A BUG AND NOT HOUSEKEEPING, stated because the output is not wrong in the ordinary sense: nothing crashes and no value is malformed. What is wrong is that the operator's REQUEST is silently overridden in a command that costs money and time. `--validate --no-verify` skips a verifier turn the operator asked for; `--no-verify --validate` pays for one they declined. Neither prints anything, so no operator can tell which way it went, and the same typed pair means two different things on the two shipped hosts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared mechanism, in `runner_shared`, before either host uses it

- [x] E-01 Add to `agent_workflows/runner_shared.py` a `BooleanOptionalAction` subclass that RECORDS each verification spelling the operator typed, appending `option_string` to a list carried on the namespace under one module-level key constant, then delegating to `super().__call__` so the parsed `validate` value is completely unchanged. Add a second recording action for agy's separate `--no-verify`/`--no-audit` registration, recording through the same helper into the same list, because agy's two spellings are registered on a DIFFERENT action and a `BooleanOptionalAction` subclass alone cannot see them (F-06). SUBCLASS `argparse.Action` FOR THAT SECOND ONE, NOT `argparse._StoreTrueAction`: the leading-underscore name is a private stdlib symbol with no compatibility guarantee across the `>=3.9` range `pyproject.toml` declares, and nothing needs it. A `store_true` action's entire behavior is `setattr(namespace, self.dest, True)` with `nargs=0`, so a public-API subclass reproduces it in three lines while the private-inheritance form buys nothing (measured: `--no-aud` records as `--no-audit` and `no_verify` parses `True` under both forms). Record the CANONICAL spelling argparse resolves an abbreviation to, which is what `option_string` already carries and which must not be re-derived: measured, `--no-aud` arrives as `--no-audit` and `--vali` as `--validate` (F-03), so abbreviations are covered for free and a hand-written argv scan would have to reimplement argparse's prefix matching to match it. Set the attribute LAZILY, on first invocation only, so a namespace on which no verification flag was passed does not carry the key at all; that is what makes the predicate in E-02 read "operator said nothing" correctly from a namespace built by hand. NAME THE KEY WITH A LEADING UNDERSCORE and confirm it reaches no durable record: the recorded list is a PARSE artifact, not a run option, and `state.json`'s `options` block is built from named `getattr(args, ...)` reads plus `freeze_run_policy_flags`'s explicit table, never from `vars(args)` (measured at review: no `vars(args)` call exists in either runner or in `runner_shared`), so the key cannot leak into frozen state today. State that property at the constant so a future `vars(args)`-based freeze does not silently start persisting it.
  - Depends on: none
  - Expected outcome: Two action classes and one key constant in `runner_shared`, each importable and unit-drivable on a throwaway parser, recording canonical spellings and leaving `dest` values identical to today's, with NO reference to a private `argparse._*` action class.
  - Execution state: performed

- [x] E-02 Add to `agent_workflows/runner_shared.py` ONE predicate that reads the recorded spelling list and raises `runner_shared.RunFlagRefusal` when the operator typed at least one ON spelling (`--validate`, `--verify`, `--audit`) and at least one OFF spelling (`--no-validate`, `--no-verify`, `--no-audit`) in the same invocation, and returns silently otherwise. It MUST be the only copy of this decision, so both hosts consume it: a second per-host copy is how the deleted `_read_deps` pair came to be identically wrong in both drivers, a precedent `agy_runipd.resolve_verification_decision`'s own docstring cites as its reason for binding a shared helper. Compose the refusal message to name the SPELLINGS ACTUALLY TYPED, not a generic pair, since the operator who typed `--no-aud --vali` needs to see which two flags collided; keep agy's measured phrase "contradict each other" in the text so the existing assertion on that substring in `tests/test_runner_shared.py::VerificationDestAsymmetryPerHostTests` keeps testing the same contract rather than being rewritten around a new wording. REFUSE ONLY A CROSS-POLARITY PAIR: repeating one polarity (`--validate --verify`) is not a contradiction and must still parse, measured to yield `validate=True` today (F-03).
  - Depends on: E-01
  - Expected outcome: One shared predicate raising `RunFlagRefusal` on a cross-polarity pair, silent on a same-polarity repeat and on an untouched namespace, with the offending spellings in the message.
  - Execution state: performed

### Task group 2: wire the refusal on oc, both subcommands

- [x] E-03 In `agent_workflows/oc_runipd.py`, register E-01's recording action on the `--validate`/`--verify`/`--audit` argument of BOTH the `start` and the `resume` subparsers, replacing the bare `argparse.BooleanOptionalAction` in each, and leave `dest`, the option-string list, and `default=None` exactly as they are. KEEP `default=None` AND ITS COMMENT INTACT: that default is the load-bearing tri-state the `hostdefault-02` comment block at the `start` registration explains, and collapsing it would make a stored `validate: true` unreachable. Both subcommands are in scope because both register all six spellings and both resolve a pair by last-wins today, measured (F-02): oc `resume --no-verify --validate` parses to `validate=True` and then WRITES it into the frozen run state in `oc_runipd.main`'s resume branch, so the silent override survives into durable state on that path rather than only affecting one invocation.
  - Depends on: E-01
  - Expected outcome: Both oc subparsers record typed spellings; the 12 oc cells of the 2.1c dest table are unchanged, provable by re-running the existing dest-table test untouched; no other oc subcommand gains a verification spelling.
  - Execution state: performed

- [x] E-04 Call E-02's predicate on oc BEFORE anything durable exists, so a refused invocation creates no run directory, no event, and no `state.json`, AND writes no key into an EXISTING `state.json` on the resume path. Place the call for `start` at the head of `oc_runipd.initialize_run`, which is the seam `agy_runipd.initialize_run` already uses for exactly this purpose (its `hostdefault-02` comment reads "resolve THIS run's verification decision here, at the same pre-durable seam as the refusals and BEFORE the run directory is created below"). For `resume` place it as the FIRST statement of the `if args.command == "resume":` branch, ADJACENT TO `runner_shared.refuse_frozen_flags_on_resume` and BEFORE `runner_shared.apply_run_policy_flags_on_resume`, NOT merely before the `state["options"]["validate"]` write. THE NARROWER PLACEMENT IS A MEASURED DEFECT, which is why it is spelled out: `apply_run_policy_flags_on_resume` sits BETWEEN the two and it WRITES AND SAVES. Driven at review with `resume run-x --no-verify --validate --full-auto`, that helper flipped `options.full_auto` `False -> True` and `save_state` persisted it, so a refusal placed only before the `validate` write leaves a REFUSED invocation having durably mutated the frozen run. That is the same class of harm this plan exists to remove (a policy the operator's own invocation was refused for, silently applied), and it is invisible to a check that only inspects `options.validate`. The correct seam is also the one the two shipped resume refusals already use: `refuse_frozen_flags_on_resume` and the `--verify-with` refusal both fire before ANY `load_state`. NO NEW EXIT PLUMBING IS NEEDED and none may be added: measured, `runner_shared.RunFlagRefusal` subclasses `DriverError`, `oc_runipd.DriverError` IS `runner_shared.DriverError`, and `oc_runipd.main`'s `except DriverError` already prints `runipd: <message>` to stderr and returns 2 (F-07). Do NOT route the refusal through the summary-table rendering: that block is guarded on an existing `state.json`, which by construction does not exist yet on the start path.
  - Depends on: E-02, E-03
  - Expected outcome: `aw oc run --no-verify --validate <sel>` and `aw oc run --validate --no-verify <sel>` both exit 2 with the refusal on stderr, in either order, with no run directory created; a refused `resume` leaves `state.json` BYTE-IDENTICAL, including every `options` key a policy flag in the same invocation would otherwise have written; a bare invocation and a same-polarity repeat are unaffected.
  - Execution state: performed

### Task group 3: close the narrower agy hole with the same predicate

- [x] E-05 In `agent_workflows/agy_runipd.py`, register E-01's two recording actions on agy's `--validate` argument and on its separate `--no-verify`/`--no-audit` `store_true` argument, and call E-02's predicate from `verification_flag_tristate` alongside the check already there. This closes the hole measured at this HEAD and NOT reported by the item: agy refuses `--no-verify --validate` but accepts `--validate --no-validate` silently and order-dependently, returning `False` in that order and `True` in the reverse (F-06). Both agy spellings must be registered through a recording action because they sit on two different argparse actions and a single subclass sees only its own. RETAIN the existing namespace-level `no_verify`-versus-`validate` check rather than replacing it with the new predicate: its docstring records that an ABSENT attribute must read as "not passed" because several shipped tests construct partial namespaces by hand, and those namespaces carry no recorded spelling list at all, so deleting that check would silently stop refusing for every one of them. Do NOT touch `assert_verification_flags_are_distinct`, whose subject is the build-time dest collision and not the operator's flags; measured at review, that guard PASSES unchanged with the recording subclass installed, because it reads `action.dest` per option string and the subclass alters neither. ORDER THE TWO CHECKS SO THE EXISTING MESSAGE STILL WINS ON THE PAIR IT ALREADY OWNS: run the retained namespace check FIRST, then the shared predicate. Both fire on `--no-verify --validate` (measured: the namespace check on `no_verify`+`validate`, the shared predicate on the recorded `--no-verify`/`--validate` pair), so whichever runs first decides the operator-visible text, and the shipped assertion on the existing wording is in `AgyVerificationFlagSurfaceTests::test_contradictory_flag_refusal_and_partial_namespace` as well as in the `VerificationDestAsymmetryPerHostTests` method E-02 names.
  - Depends on: E-02
  - Expected outcome: Both orders of `--validate --no-validate` refuse on agy `start`; the pre-existing `--no-verify --validate` refusal and its "contradict each other" wording still hold, including for hand-built partial namespaces; `assert_verification_flags_are_distinct` and `test_tristate_parsing_options_and_distinct_flags` pass untouched.
  - Execution state: performed

### Task group 4: amend the spec that currently declares the removed behavior

- [x] E-06 Amend spec `25kzda` Section 2.1c, which this plan's change FALSIFIES and which must not be left asserting the opposite of shipped behavior. Its "OPERATOR-VISIBLE CONSEQUENCES PINNED AS NORMATIVE BEHAVIOR" item 2 currently reads that on `oc start` "contradictory flags parse silently and are order-dependent (the last specified flag wins)" with both orders spelled out; rewrite that item to declare the refusal on BOTH hosts and BOTH subcommands, naming the shared predicate as the enforcing symbol, and carry a dated measurement note as that spec's preamble requires of every dated paragraph. The dest table and the "THE ASYMMETRY IS DELIBERATE AND STRUCTURAL" paragraph MUST NOT change: the asymmetry in WHICH spellings exist per host is untouched by this plan and remains correct. Record the amendment with `aw specs note` and nothing else; do NOT use any `aw specs set` form, because this plan has no authority to change a human-approved spec's status and does not need one. If that verb refuses, STOP and report rather than hand-appending. NOTHING MECHANICAL WILL CATCH A HAND-APPEND HERE, and the honest statement of that is the point: the `status-untooled` pre-commit hook delegates to `check_engine.check_status_untooled`, whose staged diff is scoped to `_PLANS_PREFIX = ".aw/records/plans/"` and which skips any path failing `_is_plan_ipd_path`, so it never examines a `.spec.md` file at all (measured at review). The spec-side checker that does exist, `check_engine.check_spec_review_attestation`, is scoped to `- Status: reviewed` and is silent on an `approved` spec by construction. So the discipline in this item is enforced by the executor and the reviewer, not by a gate; use the verb because it is correct, not because something will refuse you.
  - Depends on: E-04, E-05
  - Expected outcome: Section 2.1c declares the refusal instead of the order-dependence, `- Status: approved` is byte-identical, the dest table is byte-identical, and the spec carries a dated history line naming this plan and backlog item `byazcp`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT. `AGENTS.md` states a plan that changes behavior a spec describes SHOULD carry the amendment in the same change, and that every `.spec.md` file it will touch MUST be listed in `- Scope-Paths:`. This plan declares `25kzda` for exactly that reason, and the obligation is unusually sharp here: Section 2.1c does not merely describe the area, it DECLARES the order-dependent behavior E-04 removes, so shipping the code without the amendment would leave an approved spec asserting the opposite of shipped behavior. Precedent is direct: plan `7dz3wv` amended this same approved spec in place, and its own E-04 is the `aw specs note` route E-06 follows.
- THE PINNING TEST IS PART OF THE CONTRACT BEING CHANGED, NOT AN OBSTACLE TO IT. `tests/test_runner_shared.py::VerificationDestAsymmetryPerHostTests::test_contradictory_pair_handling_refused_on_agy_and_order_dependent_on_oc` was authored BY plan `7dz3wv` E-02 to pin the current oc behavior deliberately, precisely so this fix would have a baseline to change; that plan's scope check says so ("oc's silent order-dependent contradictory pair is pinned but not fixed (F-08, carried by `byazcp`)"). Updating it is the intended handoff, and the test's method name itself carries the old behavior and must be renamed with it. This is NOT licence to weaken it: the 24-cell dest table in the same class must keep passing UNTOUCHED, which is what proves E-03 and E-05 changed behavior without changing the flag surface.
- CODE IS CITED BY SYMBOL, NOT BY BARE LINE OFFSET (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This bites here in a way worth naming, because it is evidence for the citation rule rather than a formality: the backlog item cites `agy_runipd.verification_flag_tristate` and the sibling guard by prose description, and plan `7dz3wv`'s own conventions section records that the same guard symbol has been cited at four DIFFERENT line offsets across the item, a walkthrough, and a review, every one of them now stale. Every citation in this plan is by symbol.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Every measurement in this plan was taken with a bare `python3 -m pytest`, whose result at authoring is recorded in F-08 as a MOVING baseline the executor re-measures rather than a literal to match; plan `7dz3wv` recorded its own baseline drifting by 212 tests in 213 commits, which is why no count here is pinned.
- `tests/test_runner_shared.py` IS THE ESTABLISHED HOME FOR A CROSS-HOST ASSERTION. It already imports `oc_runipd`, `agy_runipd` and `runner_shared` at module level and already holds both `AgyVerificationFlagSurfaceTests` and `VerificationDestAsymmetryPerHostTests`, the two classes this plan's validation extends. A cross-host refusal cannot be asserted from inside one host's test file without that file importing the other.
- `runner_shared` MAY NOT IMPORT EITHER RUNNER, enforced by AST in `tests/test_runner_shared.py::NoRunnerImportTests`, which rejects any module name containing `runipd`. This constrains E-01 and E-02's direction of dependency: the action classes and the predicate live in `runner_shared` and the hosts import THEM, never the reverse. `runner_shared.resolve_verification_decision`'s docstring documents this rule and the one peer-module exception it does take.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE REPORTED DEFECT REPRODUCES EXACTLY.** On oc `start`, `--no-verify --validate` parses to `validate=True` and `--validate --no-verify` to `validate=False`, with no refusal and no output. All six spellings resolve to dest `validate` on one `BooleanOptionalAction`, so argparse's last-wins is the whole of the behavior. | Driven: `oc_runipd.build_parser().parse_args(["start","demo","--no-verify","--validate"]).validate` -> `True`; reversed -> `False`. Dest map built by walking the `argparse._SubParsersAction` in `build_parser()._actions`: all six spellings -> `validate` on `start`. |
| F-02 | **THE DEFECT EXTENDS TO `resume`, WHICH THE ITEM DOES NOT MENTION, AND THERE IT REACHES DURABLE STATE.** oc's `resume` subparser registers the same six spellings on the same dest, so the same pair is order-dependent there; and `oc_runipd.main`'s resume branch then writes the parsed value into the frozen run, setting `state["options"]["validate"]` and `state["options"]["no_audit"]` guarded only on `getattr(args, "validate", None) is not None`. So on this path the silently-chosen value is persisted, not merely used once. This is why E-03 covers both subcommands. | Dest map for `resume` -> all six spellings -> `validate`; `oc_runipd.build_parser().parse_args(["resume","run-x","--no-verify","--validate"]).validate` -> `True`. The state write is read in `oc_runipd.main`'s resume branch, immediately after `apply_run_policy_flags_on_resume`. |
| F-03 | **THE CHOSEN MECHANISM WAS DRIVEN END-TO-END BEFORE BEING WRITTEN DOWN, AND IT WORKS ON THE REAL PARSER.** A `BooleanOptionalAction` subclass recording `option_string` was swapped onto the live oc `start` and `resume` `validate` actions, and the predicate then refused `--no-verify --validate`, `--validate --no-verify` AND the abbreviated `--no-aud --vali`, while `--validate --verify` (same polarity), `--audit` alone, a bare invocation, and a `status` invocation all passed through untouched. The dest table was re-derived after patching and was IDENTICAL. Two properties matter beyond "it works": argparse hands the action its CANONICAL spelling, so `--no-aud` arrives as `--no-audit` and abbreviations need no extra code; and the recorded list does not leak between `parse_args` calls on a reused parser. | Live patch of `action.__class__` on both subparsers' `validate` actions plus a predicate over the recorded list, run over eight argv cases with the outcome printed for each; dest map re-derived post-patch and compared; three sequential `parse_args` calls on one parser showing no accumulation. |
| F-04 | **THE ITEM'S STATED OBSTACLE IS REAL: A PARSED NAMESPACE CANNOT DISTINGUISH THE SPELLINGS.** With all six aliases on one action, the namespace carries only `validate=<bool>`; nothing records which spelling set it. So the fix genuinely requires either a custom action or an argv-level scan, exactly as the item says. This plan takes the custom action, and F-03's abbreviation result is the deciding evidence: an argv scan would have to reimplement argparse's prefix matching to handle `--no-aud`, and would silently miss it until someone typed it. | `vars()` of the parsed namespace on oc `start` contains `validate` and no spelling record; `hasattr(oc_runipd, "verification_flag_tristate")` is `False`, so oc has no equivalent check to extend. |
| F-05 | **THE ITEM'S SUGGESTED FIX IS UNUSABLE AS STATED, AND THE CORRECTION IS THE SHAPE OF THIS PLAN.** It suggests lifting `verification_flag_tristate`'s contradiction check into `runner_shared` so one predicate serves both hosts. That function's check reads TWO NAMESPACE ATTRIBUTES (`no_verify` and `validate`), which is decidable on agy only because agy registers `--no-verify` on a separate dest; on oc there is no second attribute to read, which is F-04. Lifting it verbatim would therefore produce a shared predicate that cannot fire on oc at all. The item's own goal is nevertheless honored: E-02 puts ONE predicate in `runner_shared` and both hosts call it, but it is keyed on recorded spellings rather than on dests. | Read of `agy_runipd.verification_flag_tristate`, whose body is `bool(no_verify) and validate is True` over two `getattr` reads; combined with F-04's measurement that oc's namespace has only the one attribute. |
| F-06 | **AGY CARRIES A NARROWER FORM OF THE SAME HOLE, AND THE ITEM DOES NOT REPORT IT.** Agy refuses `--no-verify --validate`, but `--validate --no-validate` is accepted silently and IS order-dependent: `verification_flag_tristate` returns `False` in that order and `True` in the reverse. The cause is the same as oc's, one polarity-pair on a single `BooleanOptionalAction`, and the existing check cannot see it because both spellings write the same dest. So "fix oc to match agy" would leave a live instance of the defect on the host the item holds up as correct; E-05 closes it with the same predicate. It also shows why E-01 needs the `store_true` subclass: agy's `--no-verify`/`--no-audit` are a different action, so a `BooleanOptionalAction` subclass alone would not see them. | Driven: `verification_flag_tristate(build_parser().parse_args(["start","demo","--validate","--no-validate"]))` -> `False`; with the two flags reversed -> `True`; neither raises. |
| F-07 | **NO NEW EXIT PLUMBING IS NEEDED ON OC, so the refusal costs one call site.** `runner_shared.RunFlagRefusal` subclasses `DriverError`; `oc_runipd.DriverError` is the same class object as `runner_shared.DriverError`; and `oc_runipd.main`'s `except DriverError` handler prints `runipd: <message>` to stderr and returns 2. Every other `RunFlagRefusal` in `runner_shared` (`--integration-retry-limit`, `--on-integration-blocked`, the `--type` refusals) relies on exactly this path. | `issubclass(runner_shared.RunFlagRefusal, runner_shared.DriverError)` -> `True`; `oc_runipd.DriverError is runner_shared.DriverError` -> `True`; read of the `except DriverError` clause at the end of `oc_runipd.main`. |
| F-08 | **THE SPEC AND A TEST BOTH CURRENTLY DECLARE THE BEHAVIOR THIS PLAN REMOVES, so neither can be left alone.** Spec `25kzda` Section 2.1c, added by plan `7dz3wv` five days ago, states as normative that on `oc start` "contradictory flags parse silently and are order-dependent (the last specified flag wins)" and spells out both orders; `tests/test_runner_shared.py::VerificationDestAsymmetryPerHostTests::test_contradictory_pair_handling_refused_on_agy_and_order_dependent_on_oc` asserts the same two values with messages saying "last flag wins". That pinning was deliberate: `7dz3wv`'s scope check names this item as the carrier of the fix. Suite baseline at authoring, bare: `3246 passed, 2 skipped`; this is a MOVING number and is not pinned (that plan's own baseline moved by 212 in 213 commits), so the executor measures their own at execution HEAD. | Read of Section 2.1c consequence 2 in the approved spec file; read of the named test method; `7dz3wv`'s scope-check line "oc's silent order-dependent contradictory pair is pinned but not fixed (F-08, carried by `byazcp`)"; `python3 -m pytest` -> `3246 passed, 2 skipped in 51.64s`. |
| F-09 | **NOTHING IN THE REPOSITORY RELIES ON THE LAST-WINS BEHAVIOR, so the compatibility surface of this change is the two tests and the spec paragraph.** A search for an invocation passing a contradictory pair found no call site in sources, tests, tooling, docs, or workflow shims; the only in-repo occurrences of such a pair are the assertions and prose that DESCRIBE the defect (the pinning test, spec 2.1c, `docs/runner-profiles.md`, and agy's own docstring). This bounds the item's stated need to measure "what invocations rely on last-wins" to the in-repo answer: none. | Repository-wide search for the two flag orders across `agent_workflows/`, `tests/`, `tools/`, `docs/`, `.aw/`, `.opencode/` and `.claude/`; every hit is a description or an assertion about the behavior, none an invocation depending on it. |
| F-10 | **`docs/runner-profiles.md` ALREADY PROMISES THE BEHAVIOR THIS PLAN IMPLEMENTS, so the change makes a shipped doc TRUE rather than requiring a doc edit.** It states host-unqualified that "Passing a contradictory pair such as `--no-verify --validate` is refused before the run starts rather than resolved by precedence, because either winner would be a verification decision you did not make." Plan `7dz3wv` recorded that sentence as affirmatively FALSE on oc (its F-14) and deliberately left it, since the file was outside its scope. After E-04 it is true on both hosts. The file is deliberately NOT in `- Scope-Paths:` because it needs no change; its separate documented gap (silence on the resume asymmetry) is carried by backlog item `d8o2cv` and is untouched here. | Read of the "BOTH HOSTS HONOR THIS CHAIN" paragraph in `docs/runner-profiles.md`; `7dz3wv` F-14 recording the same sentence as false on oc and naming `d8o2cv` as the carrier for the remaining gap. |
| F-11 | **THE ORIGINALLY-AUTHORED RESUME SEAM WAS TOO LATE, AND A REFUSED INVOCATION WOULD HAVE MUTATED FROZEN STATE.** E-04 first said to place the resume refusal "before the branch that writes `state["options"]["validate"]`". Between the head of the `resume` branch and that write sits `runner_shared.apply_run_policy_flags_on_resume`, which WRITES and whose caller SAVES. Driven at review with `resume run-x --no-verify --validate --full-auto`, that helper flipped `options.full_auto` from `False` to `True`; the only reason the original V-04 would not have caught it is that `options.validate` is exactly the key the helper leaves alone (`--validate` is not in `RUN_POLICY_FLAGS`). So a refused resume would have durably applied a policy the refusal was rejecting, and the plan's own evidence requirement was blind to it. FIXED: E-04 now names the FIRST-statement seam beside `refuse_frozen_flags_on_resume`, and V-04 requires a byte-level `state.json` comparison with `options.full_auto` named. | `runner_shared.apply_run_policy_flags_on_resume(state, parse_args(["resume","run-x","--no-verify","--validate","--full-auto"]))` on `{"validate": False, "no_audit": True, "full_auto": False}` -> returns `True` and leaves `{"full_auto": true, ..., "validate": false}`; `RUN_POLICY_FLAGS` enumerated (16 rows, no `validate`); the two shipped resume refusals (`refuse_frozen_flags_on_resume`, the `--verify-with` `DriverError`) both read at the head of the branch, before any `load_state`. |
| F-12 | **E-06's STATED BACKSTOP DOES NOT EXIST, so the "do not hand-append" discipline is unenforced and had to be stated as such.** E-06 and the gate both invoked "the untooled-status pre-commit hook" as what would refuse a hand-appended spec history line. That hook delegates to `check_engine.check_status_untooled`, whose staged diff is `git diff --cached ... -- .aw/records/plans/` (`_PLANS_PREFIX`) and which `continue`s on any path failing `_is_plan_ipd_path`, so it never reads a `.spec.md`. The one spec-side lifecycle checker, `check_spec_review_attestation`, is scoped by its own docstring to `- Status: reviewed` and is silent on an `approved` spec by construction. An invoked-but-absent gate is worse than an acknowledged gap, because an executor may skip the verb believing something will catch them. FIXED in both places, with the measurement, and stated as executor discipline. | Read of `agent_workflows/hooks/status_untooled_gate.py` (delegates to `_ce.check_status_untooled`); `_PLANS_PREFIX = ".aw/records/plans/"` at `check_engine.py`; the `if not _is_plan_ipd_path(new_path): continue` guard in the same function; `check_spec_review_attestation`'s "SCOPED TO `reviewed` AND NOTHING ELSE" paragraph. |
| F-13 | **THE `store_true` HALF OF E-01 NEEDED NO PRIVATE STDLIB SUBCLASS, and asking for one imported a compatibility risk for nothing.** E-01 first specified an `argparse._StoreTrueAction` subclass. That name is private, has no cross-version guarantee over the `requires-python = ">=3.9"` range this package declares, and buys nothing: a `store_true` action's whole behavior is `setattr(namespace, dest, True)` at `nargs=0`, which a public `argparse.Action` subclass reproduces directly. Measured equivalent under both forms (`--no-aud` records as `--no-audit`, `no_verify` parses `True`). Note this is not a blanket ban on private argparse names in this repository: `argparse._SubParsersAction` is used in ten production sites, but it is used to INSPECT a parser, which has no public equivalent, whereas subclassing a private action to reimplement three lines does. | `pyproject.toml:12` `requires-python = ">=3.9"`; a public `argparse.Action` subclass driven over `--no-aud` recording `--no-audit` and parsing `no_verify=True`; `grep argparse\._` across `agent_workflows/` returning only `_SubParsersAction` inspection sites. |

## Proposed changes (ordered, validatable)

1. `runner_shared`: a recording `BooleanOptionalAction` subclass, a recording public-`argparse.Action` store-true subclass (NOT a private `_StoreTrueAction` subclass, per F-13), and one underscore-prefixed namespace key constant (E-01). No behavior change on its own; the parsed values are identical.
2. `runner_shared`: one shared cross-polarity refusal predicate raising `RunFlagRefusal`, keyed on recorded spellings rather than on dests, with the offending spellings in its message (E-02).
3. `oc_runipd`: the recording action on the `validate` argument of both `start` and `resume`, with `dest`, alias list, and `default=None` untouched (E-03).
4. `oc_runipd`: the predicate called at the pre-durable seam for `start` and as the FIRST statement of the `resume` branch, beside `refuse_frozen_flags_on_resume` and upstream of `apply_run_policy_flags_on_resume`, reusing the existing `except DriverError` exit path (E-04, F-11).
5. `agy_runipd`: the recording actions on both of its verification registrations, and the predicate called from `verification_flag_tristate` AFTER the existing namespace check (so the shipped message keeps winning on the pair it owns), closing F-06 (E-05).
6. Spec `25kzda` Section 2.1c consequence 2 rewritten to declare the refusal on both hosts and both subcommands, with a dated measurement note recorded through `aw specs note`; dest table and asymmetry rationale untouched (E-06).

## Deferred / out of scope (with reason)

- THE `build_parser` DE-DUPLICATION IS NOT ATTEMPTED. Spec 2.1c's "THE ASYMMETRY IS DELIBERATE AND STRUCTURAL" paragraph explains why oc's alias list cannot simply be registered on agy, and that unification is a maintainer-directed refactor tracked separately. This plan makes the two hosts agree on the REFUSAL while leaving the per-host spelling surface exactly as it is, which is the smaller and independently valuable half.
  - Carrier: xvp5vx
- `docs/runner-profiles.md` IS NOT EDITED, deliberately, and F-10 is the reason: the sentence an operator reads there already promises this refusal, so the change makes the existing prose true. Its separate gap is silence on the resume asymmetry.
  - Carrier: d8o2cv
- THE RESUME ASYMMETRY ITSELF IS NOT CHANGED. agy's `resume` registers none of the six spellings and oc's registers all six; that difference is declared in 2.1c consequence 3 and is untouched. This plan changes only what happens when a pair IS accepted, never which spellings exist where.
  - Carrier-Declined: NOT A GAP THIS PLAN OPENED, and not deferred work. The per-host difference in WHICH spellings exist is a deliberate, spec-declared capability boundary with a measured structural cause (F-06's `BooleanOptionalAction` collision), not a defect awaiting a fix. Its documentation half already has a carrier (`d8o2cv`, named above); filing a second item to track "the hosts register different flags on resume" would assert future work nobody intends to do, because changing it is the de-duplication `xvp5vx` owns.
- NO CHANGE IS MADE TO THE VERIFICATION PRECEDENCE CHAIN. `runner_shared.resolve_verification_decision` and its four tiers are untouched; this plan governs only the case where the operator's own flags contradict each other, which is upstream of any tier.
  - Carrier-Declined: NOTHING IS OUTSTANDING. This row is a scope fence recording what the plan deliberately does not touch, not a deferred obligation. The chain is correct as shipped and this plan asserts no defect in it; a carrier saying "the four tiers are fine" could never be closed on evidence.
- `assert_verification_flags_are_distinct` IS LEFT EXACTLY AS IT IS. Its subject is the BUILD-TIME dest collision between the two agy registrations, not the operator's typed flags, and its own docstring explains why that hazard is decidable only at the parser. Conflating the two checks would lose that distinction.
  - Carrier-Declined: NO RESIDUAL WORK. The existing guard is measured correct and in the right place (F-06 relies on it holding), so this row records a deliberate decision NOT to merge two checks that answer different questions. There is no gap for a carrier to carry; merging them would be a regression rather than an improvement.

## Scope check

- Over-scope: none. Every file in `- Scope-Paths:` is required by an E-item: `runner_shared.py` for the mechanism, both runners for the call sites, the test file for validation, and the spec because this plan falsifies a normative sentence in it (F-08).
- Under-scope: Three gaps are recorded as deferrals above rather than closed here: the directed `build_parser` de-duplication (carried by `xvp5vx`), the `docs/runner-profiles.md` resume silence (carried by `d8o2cv`), and the per-host resume flag surface itself (declared in 2.1c consequence 3, unchanged by design). After this plan a contradictory verification pair refuses on BOTH hosts and BOTH oc subcommands, including the agy case F-06 measured and the item never reported.

## Required tests / validation

All validation runs the suite BARE (`python3 -m pytest`), per the convention recorded above. New and changed assertions live in `tests/test_runner_shared.py`, the established home for a cross-host assertion.

1. Both orders of a contradictory pair refuse on oc `start` and on oc `resume`, asserting `RunFlagRefusal` and the "contradict each other" substring, and the refusal message NAMES the typed spellings.
2. An abbreviated pair (`--no-aud --vali`) refuses, pinning F-03's canonical-spelling property so a future argv-scan rewrite cannot silently regress it.
3. A same-polarity repeat (`--validate --verify`), a single flag, and a bare invocation are NOT refused and yield today's `validate` values. Also cover the two OTHER same-polarity forms measured at review, so "same polarity never refuses" is pinned as a property and not as one example: `--verify --audit` -> `True` and `--no-verify --no-audit` -> `False` on oc, and `--no-verify --no-validate` in BOTH orders -> `False` on agy through `verification_flag_tristate`.
4. Both orders of `--validate --no-validate` refuse on agy `start` (F-06), while the pre-existing `--no-verify --validate` refusal still holds WITH ITS EXISTING MESSAGE TEXT (the E-05 ordering property), INCLUDING for a hand-built partial namespace carrying no recorded spellings.
5. The 24-cell dest table in `VerificationDestAsymmetryPerHostTests` still passes UNTOUCHED, proving the flag surface did not move. Assert additionally that no subcommand OTHER than `start`/`resume` on oc and `start` on agy gained a verification spelling, which is what pins the recording action to the registrations it was installed on (measured at review: oc `status`/`report`/`stop`/`integrate`/`audit` and agy `resume` and its four siblings register none of the six).
6. The end-to-end operator consequence: a refused `aw oc run` exits 2 with the message on stderr and creates NO run directory; and a refused `aw oc run resume` leaves `state.json` byte-identical even when the same invocation also passed a `RUN_POLICY_FLAGS` flag such as `--full-auto` (F-11).
7. The existing `test_contradictory_pair_handling_refused_on_agy_and_order_dependent_on_oc` is updated and RENAMED to describe the new contract, since its current name asserts the removed behavior.
8. A full bare suite passes, with the executor's own measured baseline pasted (F-08: not pinned to a literal).

## Spec / documentation sync

SPEC `25kzda` MUST BE AMENDED IN THE SAME CHANGE, and this is the sharp case the `AGENTS.md` rule exists for rather than a routine one: Section 2.1c consequence 2 does not merely describe this area, it DECLARES as normative that oc resolves a contradictory pair by last-wins, and spells out both orders. Shipping E-04 without E-06 would leave an approved spec asserting the opposite of shipped behavior. The amendment is confined to consequence 2; the 24-cell dest table and the "THE ASYMMETRY IS DELIBERATE AND STRUCTURAL" paragraph remain correct and must not change. It is recorded with `aw specs note`, the route plan `7dz3wv` E-04 measured to work on this exact file, leaving `- Status: approved` untouched.

NO USER-FACING DOCUMENTATION CHANGE IS REQUIRED, which is unusual enough to state with its evidence: `docs/runner-profiles.md` already tells operators this pair "is refused before the run starts rather than resolved by precedence" (F-10). That sentence is false on oc today and true after this plan, so the file is deliberately outside `- Scope-Paths:`. The remaining documented gap in that file is carried by `d8o2cv`.

## Open questions

### OQ-01: Should the refusal be a custom argparse action or an argv-level scan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT, custom action. The item names both options without choosing. Two measurements decide it. First, argparse hands an action the CANONICAL spelling of an abbreviation, so `--no-aud` arrives as `--no-audit` and `--vali` as `--validate` (F-03); an argv scan would have to reimplement argparse's prefix matching to cover those, and would silently miss them until an operator typed one. Second, the action approach was driven against the real oc parser on both subparsers, refused all three contradictory forms, left the same-polarity and single-flag cases untouched, and re-derived an IDENTICAL dest table (F-03), so it is measured rather than assumed. The cost is one subclass per action type, which E-01 needs anyway because agy's two registrations sit on different actions (F-06).

### OQ-02: Should the pre-existing namespace-level check in `verification_flag_tristate` be replaced by the shared predicate?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, keep both, and ORDER THEM. The existing check's own docstring records that an absent attribute must read as "not passed" because several shipped tests construct partial namespaces by hand. Such a namespace carries no recorded spelling list, so the new predicate cannot fire on it; replacing the old check would silently stop refusing for exactly those callers, which a review measurement confirms (a hand-built `Namespace(no_verify=True, validate=True)` is refused by the namespace check and is invisible to the shared predicate). The two checks are NOT disjoint on a real parse, which the first resolution missed: on `--no-verify --validate` BOTH fire, the namespace check on the two dests and the shared predicate on the two recorded spellings. So the order decides which message an operator sees, and E-05 now specifies the retained check FIRST so the shipped wording that two test classes assert on keeps winning on the pair it already owns. Both are cheap, so E-05 adds the predicate beside the existing check rather than in place of it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste a Python session that builds a THROWAWAY parser registering both new action classes, parses `--no-aud`, `--vali`, `--validate` and an empty argv, and prints `vars(namespace)` for each. It must show the recorded list containing the CANONICAL spellings (`--no-audit`, `--validate`), show the `dest` values identical to what a plain `BooleanOptionalAction`/`store_true` produces for the same argv, and show the key ABSENT from the namespace for the empty argv. Also paste three sequential `parse_args` calls on ONE reused parser showing the list does not accumulate across calls. Paste the two new class definitions themselves (or a `grep` over `runner_shared.py`) showing NEITHER names a private `argparse._*` action class, per F-13; a subclass of `argparse._StoreTrueAction` is a FAILED validation of this item even if it behaves correctly.
  - Observed evidence: Throwaway parser verified canonical recording, dest preservation, and non-accumulation; grep confirmed public inheritance.
```
case: ['--no-aud']
  plain vars:     {'no_verify': True, 'validate': None}
  recording vars: {'no_verify': True, 'validate': None, '_recorded_verification_flags': ['--no-audit']}
case: ['--vali']
  plain vars:     {'no_verify': False, 'validate': True}
  recording vars: {'no_verify': False, 'validate': True, '_recorded_verification_flags': ['--validate']}
case: ['--validate']
  plain vars:     {'no_verify': False, 'validate': True}
  recording vars: {'no_verify': False, 'validate': True, '_recorded_verification_flags': ['--validate']}
case: []
  plain vars:     {'no_verify': False, 'validate': None}
  recording vars: {'no_verify': False, 'validate': None}

Three sequential parse_args calls on one reused parser:
  call 1: {'no_verify': False, 'validate': True, '_recorded_verification_flags': ['--validate']}
  call 2: {'no_verify': False, 'validate': True, '_recorded_verification_flags': ['--validate']}
  call 3: {'no_verify': False, 'validate': True, '_recorded_verification_flags': ['--validate']}

$ grep -n -E "class Recording" agent_workflows/runner_shared.py
16609:class RecordingBooleanOptionalAction(argparse.BooleanOptionalAction):
16627:class RecordingStoreTrueAction(argparse.Action):
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the new test's output plus a direct session driving the predicate over: a cross-polarity pair (raises `RunFlagRefusal`, message contains "contradict each other" AND both typed spellings), a same-polarity repeat `--validate --verify` (returns silently), a single flag (silent), and a namespace with no recorded key (silent). Paste the full refusal message text for the pair so the "names the spellings actually typed" requirement is checkable, not asserted.
  - Observed evidence: Verified cross-polarity refusal, same-polarity repeat, single flag, absent key, and passing test.
```
Cross-polarity refusal message: --no-audit and --validate contradict each other: one asks to run turn-2 verification and the other asks to skip it. Pass flags of only one polarity.
Same-polarity repeat --validate --verify: returned silently
Single flag --validate: returned silently
Namespace with no recorded key: returned silently

tests/test_runner_shared.py::VerificationDestAsymmetryPerHostTests::test_contradictory_pair_handling_refused_on_both_hosts PASSED
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the re-derived dest map for oc `start` AND `resume` after the change, walking the `argparse._SubParsersAction` in `oc_runipd.build_parser()._actions`, showing all six spellings still map to `validate` on both. Paste the SAME walk over EVERY oc and agy subcommand (not only `start`/`resume`), showing the per-subcommand spelling sets unchanged from the review measurement: oc `start` and `resume` carry all six, oc `status`/`report`/`stop`/`integrate`/`audit` carry none, agy `start` carries four (`--no-verify`, `--no-audit`, `--validate`, `--no-validate`), and agy `resume`/`status`/`report`/`stop`/`integrate`/`audit` carry none. Paste the UNMODIFIED `test_verification_dest_table_per_host_and_subcommand` passing. Paste a check that `start`'s `--validate` default is still `None` (a bare `parse_args` namespace showing `validate=None`), since collapsing that tri-state would break the stored-default chain.
  - Observed evidence: Re-derived dest map for all subcommands matches baseline; start default is None; dest-table test passes.
```
=== OC SUBCOMMANDS VERIFICATION MAP ===
oc start: {'--validate': 'validate', '--no-validate': 'validate', '--verify': 'validate', '--no-verify': 'validate', '--audit': 'validate', '--no-audit': 'validate'}
oc resume: {'--validate': 'validate', '--no-validate': 'validate', '--verify': 'validate', '--no-verify': 'validate', '--audit': 'validate', '--no-audit': 'validate'}
oc status: {}
oc report: {}
oc stop: {}
oc integrate: {}
oc audit: {}

=== AGY SUBCOMMANDS VERIFICATION MAP ===
agy start: {'--no-verify': 'no_verify', '--no-audit': 'no_verify', '--validate': 'validate', '--no-validate': 'validate'}
agy resume: {}
agy status: {}
agy report: {}
agy stop: {}
agy integrate: {}
agy audit: {}

=== CHECK DEFAULT OF START --validate ===
oc start bare validate: None (is None: True)

tests/test_runner_shared.py::VerificationDestAsymmetryPerHostTests::test_verification_dest_table_per_host_and_subcommand PASSED
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste real CLI invocations, not parser probes: `aw oc run --no-verify --validate <sel>` and `aw oc run --validate --no-verify <sel>` in a scratch repo, each showing exit code 2 and the refusal on stderr; plus `aw oc run --no-aud --vali <sel>` refusing likewise. Paste evidence that NO run directory was created by the refused start (a listing of `.aw/records/runs/` before and after, or its absence). Paste one non-contradictory invocation reaching further than the refusal, proving the gate is not refusing everything. For `resume`, a check on `options.validate` alone is INSUFFICIENT and MUST NOT be accepted as this item's evidence (F-11 measured why: the intervening `apply_run_policy_flags_on_resume` writes OTHER `options` keys and leaves `validate` untouched, so that check passes on the defective placement). Instead run `aw oc run resume <run> --no-verify --validate --full-auto` against a real run directory and paste a BYTE-LEVEL comparison of `state.json` before and after (a `sha256sum` pair, or a `diff` reporting no output), showing `options.full_auto` specifically UNCHANGED alongside `options.validate`. A differing digest is a FAILED validation naming the placement, not a cosmetic note.
  - Observed evidence: CLI invocations refused with exit 2, no run directory created, and resume state.json byte-identical.
```
=== RUNS DIR BEFORE ATTEMPTS ===
runs_dir exists: False

=== 1. aw oc run --no-verify --validate pol001 ===
exit code: 2
stderr:
runipd: --no-verify and --validate contradict each other: one asks to run turn-2 verification and the other asks to skip it. Pass flags of only one polarity.

=== 2. aw oc run --validate --no-verify pol001 ===
exit code: 2
stderr:
runipd: --validate and --no-verify contradict each other: one asks to run turn-2 verification and the other asks to skip it. Pass flags of only one polarity.

=== 3. aw oc run --no-aud --vali pol001 ===
exit code: 2
stderr:
runipd: --no-audit and --validate contradict each other: one asks to run turn-2 verification and the other asks to skip it. Pass flags of only one polarity.

=== RUNS DIR AFTER REFUSED STARTS ===
runs_dir exists: False

=== 4. Non-contradictory start --prepare-only ===
exit code: 0
created run dir: ['run-20261002T004736Z-1761416']
state.json exists: True
options before resume: {'validate': False, 'full_auto': False, 'no_audit': True}
sha256 before resume: 653085bff02e8de370507f900737e062921c4ceb8a21f1ce4b6f707b5c663ca9

=== 5. aw oc run resume <run> --no-verify --validate --full-auto ===
exit code: 2
stderr:
runipd: --no-verify and --validate contradict each other: one asks to run turn-2 verification and the other asks to skip it. Pass flags of only one polarity.
sha256 after resume:  653085bff02e8de370507f900737e062921c4ceb8a21f1ce4b6f707b5c663ca9
sha match: True
diff output empty: True
options after resume: {'validate': False, 'full_auto': False, 'no_audit': True}
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste a session driving agy `start` with `--validate --no-validate` and with `--no-validate --validate`, showing `RunFlagRefusal` in BOTH orders where F-06 measured `False` and `True`. Paste the pre-existing `--no-verify --validate` case still refusing WITH ITS FULL MESSAGE TEXT, showing the retained check's shipped wording ("--no-verify (or --no-audit) and --validate contradict each other: ...") and not the shared predicate's, which proves the ordering E-05 specifies is the one implemented; the reverse order is a FAILED validation of this item because two shipped test classes assert on that text. Paste a HAND-BUILT partial `argparse.Namespace(no_verify=True, validate=True)` still refusing, proving the retained namespace check was not replaced. Paste `test_tristate_parsing_options_and_distinct_flags` AND `test_contradictory_flag_refusal_and_partial_namespace` passing unchanged, plus a direct call to `assert_verification_flags_are_distinct` on the live patched `start` subparser.
  - Observed evidence: Bidirectional refusal verified on agy start, retained namespace check message preserved, and tests pass.
```
agy start ['--validate', '--no-validate'] raised RunFlagRefusal: --validate and --no-validate contradict each other: one asks to run turn-2 verification and the other asks to skip it. Pass flags of only one polarity.
agy start ['--no-validate', '--validate'] raised RunFlagRefusal: --no-validate and --validate contradict each other: one asks to run turn-2 verification and the other asks to skip it. Pass flags of only one polarity.

Pre-existing --no-verify --validate full message:
--no-verify (or --no-audit) and --validate contradict each other: one asks to skip turn-2 verification and the other asks to run it. Pass exactly one; --no-verify is the same request as --no-validate

Hand-built partial namespace full message:
--no-verify (or --no-audit) and --validate contradict each other: one asks to skip turn-2 verification and the other asks to run it. Pass exactly one; --no-verify is the same request as --no-validate

assert_verification_flags_are_distinct(start_sub): PASSED silently

tests/test_runner_shared.py::AgyVerificationFlagSurfaceTests::test_tristate_parsing_options_and_distinct_flags PASSED
tests/test_runner_shared.py::AgyVerificationFlagSurfaceTests::test_contradictory_flag_refusal_and_partial_namespace PASSED
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste the `git diff` of the spec file. It must show consequence 2 rewritten to declare the refusal, and must show NO change to `- Status: approved`, to the dest table, or to the "THE ASYMMETRY IS DELIBERATE AND STRUCTURAL" paragraph. Paste the `aw specs note` command actually run and its output, plus the resulting history line. Paste `aw ipd lint --phase pre-transition` on this plan reporting conforming, and a FULL bare `python3 -m pytest` with the summary line, stating the measured baseline rather than matching F-08's literal.
  - Observed evidence: Spec 25kzda Section 2.1c amended and history noted via aw specs note; lint and test suite verified.
```diff
diff --git a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
index f8b339784..add5ffa9a 100644
--- a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
+++ b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
@@ -296,7 +296,7 @@ THIS IS WHY THE OC-PREFERRED RECONCILIATION RULING CANNOT BE APPLIED TO THIS SYM

 OPERATOR-VISIBLE CONSEQUENCES PINNED AS NORMATIVE BEHAVIOR:
 1. **Flag existence**: `--verify` and `--audit` exit 2 on `agy start` (unrecognized arguments), whereas `oc start` accepts both as aliases of `validate=True`.
-2. **Contradictory pairs**: Passing contradictory flags such as `--no-verify --validate` on `agy start` is refused before execution with `runner_shared.RunFlagRefusal` via `agy_runipd.verification_flag_tristate`, preventing an unintended verification decision. On `oc start`, contradictory flags parse silently and are order-dependent (the last specified flag wins: `--no-verify --validate` yields `validate=True`, while `--validate --no-verify` yields `validate=False`).
+2. **Contradictory pairs**: Passing contradictory verification flags (at least one ON spelling: `--validate`, `--verify`, `--audit`, and at least one OFF spelling: `--no-validate`, `--no-verify`, `--no-audit`) in the same invocation is refused before execution with `runner_shared.RunFlagRefusal` via `runner_shared.refuse_contradictory_verification_flags` on BOTH hosts (`oc` and `agy`) and BOTH subcommands (`start` and `resume`), preventing an unintended verification decision. On `agy start`, `verification_flag_tristate` evaluates the retained namespace check before the shared predicate, preserving the shipped diagnostic for `--no-verify --validate` while also refusing `--validate --no-validate` in either order. Repeating flags of the same polarity is permitted and resolves without contradiction. (Amended 2026-10-01 by plan `zdgc6t`, graduating backlog item `byazcp`; measured 2026-10-01 at HEAD `8ea201bf`).
 3. **Resume subcommand surface**: `agy run resume` registers NONE of the six verification spellings; the verification posture of an Antigravity run is frozen at initialization and cannot be changed on resume (passing any verification flag exits 2). In contrast, `oc run resume` registers all six spellings and honors explicit verification overrides in the resumed run state.

 ### 2.2 Type vocabulary
@@ -1637,6 +1637,7 @@ This example demonstrates the revised guarantees: `all` is safely bounded; depen

 ## Workflow history

+- 2026-10-01 note (aw specs): amend Section 2.1c consequence 2: refuse contradictory verification flags on both hosts and subcommands via shared predicate (plan zdgc6t, backlog byazcp)
```

Command executed:
`aw specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "amend Section 2.1c consequence 2: refuse contradictory verification flags on both hosts and subcommands via shared predicate (plan zdgc6t, backlog byazcp)"`
Output: `aw specs note: appended a history record to .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`

`aw ipd lint .aw/records/plans/pending/20260929-byazcp-01-zdgc6t-refuse-a-contradictory-verification-flag-pair-on-oc-run-as-a.ipd.md --phase pre-transition` reports conforming.
Bare test suite baseline: 4442 passed, 2 skipped at execution HEAD `8ea201bfaac8da65e291a3b03f7a3d431929fccd` (plus 2 new tests in `tests/test_runner_shared.py`).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the paths this plan declares, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, never push. Do not create a tag or a release. The plan is executed in E-order: the shared mechanism (E-01, E-02) lands before either host consumes it, oc's wiring (E-03, E-04) before agy's (E-05), and the spec amendment (E-06) LAST, so the spec is never left describing a behavior that is not yet shipped.

STOP CONDITIONS. If `runner_shared` cannot carry the action classes without importing a runner, STOP: `NoRunnerImportTests` enforces that boundary by AST and a workaround would be a design change this plan has no authority to make. If `aw specs note` refuses to append to the approved spec, STOP and report; do not hand-append. No hook will catch a hand-append to a spec (E-06 records the measurement: the untooled-status gate is scoped to the plans tree and never reads a `.spec.md`), so this one is on the executor. If the 24-cell dest-table test fails at any point, STOP: that is the signal the flag surface moved, which this plan explicitly promises not to do.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted evidence from a run that actually happened. The terminal transaction (workflow-history line, terminal `Status:`, `git mv`, path-scoped lifecycle commit) is a post-gate step and never a checklist item.
