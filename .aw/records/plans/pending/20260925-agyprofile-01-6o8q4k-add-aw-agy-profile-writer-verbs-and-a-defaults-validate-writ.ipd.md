# IPD: Add aw agy profile writer verbs and a defaults.validate writer

- Date: 2026-09-25
- Kind: child
- Concern: Antigravity runs resolve a stored verification choice (plan `ybkmzp`), but nothing shipped can write it: `runner_profile_wizard.RUNNER = "oc"` is baked into every `aw oc profile` handler, `aw agy profile` does not exist, and `runner_profiles.set_validate_default` has no caller, so operators must hand-edit `runner-profiles.json`.
- Scope: Parameterize the `aw oc profile` handlers by runner, register the same fixed verb set as `aw agy profile {add,list,show,remove,default}` (noninteractive `add` with `--validate/--no-validate`), GUARD the runner-scoped verbs against the flat profile namespace so a verb in one host's namespace cannot read, retarget or delete the other host's profile, add one `validate-default` verb under both namespaces that writes the host-neutral `defaults.validate` through `set_validate_default`, and replace the documented hand-edit step.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/runner_profile_wizard.py, tests/test_agy_profile_cli.py, tests/test_oc_profile_cli_regression.py, docs/runner-profiles.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- Id: 6o8q4k
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved
- From-Backlog: fxiqse
- Set: agyprofile
- Order: 1
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us

## Workflow history
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (aw set): status set to reviewed

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-907 all FIXED, OQ-01 deliberately left OPEN and non-blocking as a public CLI contract choice for the maintainer. F-1, F-2, F-4 and F-5 reproduced exactly, and the store mechanism was driven end to end (an agy profile made default resolves `validate=False` with provenance `default-profile`). One BLOCKER found by driving the proposed CLI against the store: profile names are ONE FLAT NAMESPACE, so `agy profile show/remove/default <oc-name>` would respectively display a foreign profile, DELETE it, and silently rewrite the OPENCODE default, because `cfg.get` and `set_default_profile` take no runner. Also found: E-01's byte-identical claim had NO test able to falsify it (zero tests drive any oc profile verb); E-02 silently changed a `--json` contract; and the linter's own `IPD-Z602` advisory on E-05 was correct. Record: `.aw/records/reviews/20260925-agyprofile-01-6o8q4k-add-aw-agy-profile-writer-verbs-and-a-defaults-validate-writ.review.md`.
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog fxiqse; re-measured `aw agy --help` (no `profile` choice, argparse exits 2), `RUNNER = "oc"` in the wizard, the zero callers of `set_validate_default`, and that `agy_runipd` consumes a profile only for the validate tier.

## Goal

An operator can create, inspect, default and remove antigravity runner profiles, and set or unset the host-neutral `defaults.validate`, entirely through `aw`, with the same no-clobber, single-atomic-write and explicit-default guarantees `aw oc profile` already gives, so `docs/runner-profiles.md` no longer tells anyone to hand-edit JSON.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: runner-parameterized handlers

- [ ] E-01 In `cli.py`, make `_run_oc_profile` and the handlers `_oc_profile_add`, `_oc_profile_list`, `_oc_profile_show`, `_oc_profile_remove`, `_oc_profile_default` read the runner from `args.profile_runner` (default `"oc"` via `getattr`) instead of `wiz.RUNNER` / the literal `"oc"` (every `default_profile_for("oc")`, `clear_default_profile(cfg, "oc")`, `"runner": wiz.RUNNER`). Derive the host display name ("OpenCode"/"Antigravity") and the result `command` label (`oc profile <verb>` / `agy profile <verb>`) from that runner in `_oc_profile_result`. `list` shows only profiles whose `runner` matches. Keep `wiz.RUNNER` as the oc default so existing callers and tests are untouched.
  - Depends on: none
  - Expected outcome: `aw oc profile ...` output and exit codes are byte-identical to today; the handlers contain no remaining hardcoded `"oc"` runner literal.
  - Execution state: pending

- [ ] E-02 In `runner_profile_wizard`, make `preview_lines` and `profile_dict` runner-aware: for `runner == "agy"` omit the "Equivalent OpenCode launch" BLOCK from the preview and instead print a line stating the honest effect measured in `agy_runipd.resolve_verification_decision` ("NO PROFILE NAME IS PASSED"): an antigravity profile applies ONLY as `defaults.profiles.agy`, and today only its `validate` field changes a run (the driver launches `agy_runipd.DEFAULT_MODEL`, and `execution_profile` is ignored on that host). Two constraints review measured (F-9).
  1. `profile_dict` EMITS `opencode_args: null` FOR AGY; do NOT omit the key. Its docstring records that it feeds `aw oc profile list/show` `--json`/`--agent` output, so a missing key is a machine-contract change that turns a consumer's read into a `KeyError`, while a null is a value a consumer already handles, and one stable shape is what lets one consumer read both hosts.
  2. CHECK `emit_preview` BEFORE CHANGING THE BLOCK. It styles by matching literals, including `elif stripped == "Equivalent OpenCode launch:"` and `elif stripped.startswith("opencode run ")`, which are exactly the lines being removed. An unmatched line falls through to the plain `else`, so this degrades gracefully rather than crashing, but `preview_lines`' own docstring warns that two `cli.py` paths reuse the block and that it "is asserted by substring in the tests"; find those assertions rather than discover them.
  - Depends on: none
  - Expected outcome: `preview_lines("q", agy_profile)` contains no `opencode run` and does contain `defaults.profiles.agy`; `profile_dict("q", agy_profile)["opencode_args"]` is `None`; `emit_preview` renders an agy profile without raising.
  - Execution state: pending

### Task group 2: the new verbs

- [ ] E-03 Register `aw agy profile` (alias `profiles`) under `agy_sub` with the same fixed subverbs as `oc_profile_sub` (`add`, `list`/`ls`, `show`, `remove`/`rm`, `default`), each `set_defaults(profile_runner="agy")`, and dispatch it in the `args.command in ("agy", "antigravity")` branch of `main` through `_run_oc_profile(args, profile_cmd)`, mirroring the oc branch ("if oc_cmd in (\"profile\", \"profiles\"):"). `aw agy profile add` is NONINTERACTIVE ONLY: it requires `NAME --model <provider/model> --yes`, refuses exit 2 with nothing written otherwise, accepts `--validate`/`--no-validate` (tri-state, omitted means unset), `--replace`, `--set-default`, and offers no `--variant`/`--oc-agent` (the `agy` `RunnerSpec` has `supports_variant=False, supports_agent=False`). When `--set-default` is absent, the success message warns that the profile is inert until `aw agy profile default NAME`.
  - Depends on: E-01, E-02
  - Expected outcome: `aw agy --help` lists `profile`; `aw agy profile add quiet --model google/gemini-3-pro --no-validate --set-default --yes` writes `profiles.quiet` with `runner: agy`, `validate: false` and `defaults.profiles.agy: quiet` in one `rp.save`.
  - Execution state: pending

- [ ] E-04 GUARD THE RUNNER-SCOPED VERBS AGAINST THE FLAT NAMESPACE. Profile names are ONE namespace shared by both hosts (`add_profile`'s no-clobber is name-keyed, so `gem` cannot exist twice, F-7), and the store primitives `show`/`remove`/`default` reach are runner-BLIND: `ProfileConfig.get(self, name)` takes no runner, and `set_default_profile(cfg, name)` derives the runner from the PROFILE and ignores the caller's. Measured on a store holding one OC profile `gem` (F-6): `agy profile show gem` would DISPLAY an OpenCode profile, `agy profile default gem` would write `default_profiles = {'oc': 'gem'}`, silently rewriting the OPENCODE default from inside the antigravity namespace, and `agy profile remove gem` would DELETE the OpenCode profile. Add ONE shared helper used by `_oc_profile_show`, `_oc_profile_remove` and `_oc_profile_default`: after looking the profile up, if `profile.runner != args.profile_runner`, refuse exit 2 through `_oc_profile_error` naming the profile, the runner that actually owns it, and the correct command to use, writing NOTHING. `default --clear` is EXEMPT because it is already runner-scoped (`clear_default_profile(cfg, runner)`). Do NOT change `runner_profiles`: the guard belongs in the CLI, both because `- Scope:` forbids it and because those primitives have many callers the oc path does not need to change.
  - Depends on: E-01
  - Expected outcome: with an OC profile `gem` in the store, each of `aw agy profile show gem`, `aw agy profile remove gem --yes` and `aw agy profile default gem` exits 2 with the store bytes UNCHANGED and the message naming `oc`; the oc namespace still reaches `gem` normally.
  - Execution state: pending

- [ ] E-05 Add a `validate-default` subverb to BOTH `aw oc profile` and `aw agy profile`, taking exactly one of `on`, `off`, `unset`, handled by one shared `_profile_validate_default(args)` that calls `rp.set_validate_default(cfg, True|False|None)` then `rp.save`. Its output states that `defaults.validate` is HOST-NEUTRAL (applies to every host and to any profile that does not set its own `validate`) and reports the resolved value for both runners via `rp.resolve(cfg, runner=r)` so the operator sees the effect. Note this verb is NOT runner-scoped and needs no E-04 guard: it writes one host-neutral key, which is why it is offered identically under both namespaces.
  - Depends on: E-01
  - Expected outcome: `aw agy profile validate-default off` then `aw oc profile validate-default unset` leave the store with no `defaults.validate` key; `grep -n "set_validate_default(" agent_workflows/cli.py` shows the new PRODUCTION caller (the mutator already had seven test callers, F-3, so "a caller in the package" is not the bar).
  - Execution state: pending

### Task group 3: tests and docs

- [ ] E-06 Add `tests/test_oc_profile_cli_regression.py`, the guard E-01's "byte-identical" claim needs and does not have. Measured at review (F-8): `grep -rn '_run_oc_profile\|_oc_profile_add' tests/` returns NOTHING, and the only `aw oc profile` strings in `tests/test_cli.py` are setup-wizard PROMPTS, so today no test drives any oc profile verb and a regression in the refactor would ship green. Drive `cli.main([...])` in-process with `XDG_CONFIG_HOME` on a temp dir (the `tests/test_cli.py` `CliTestBase` pattern) over ALL FIVE verbs on an oc-only store: noninteractive `add`, `list` (table and `--json`), `show`, `remove`, `default` (set and `--clear`), asserting stdout, exit codes, and that the `command` label in structured output is still `oc profile <verb>`. Capture the expected values from the tree BEFORE E-01 is applied, so the file is a true baseline rather than a description of the refactored behavior.
  - Depends on: none
  - Expected outcome: the file passes on the UNPATCHED tree (it is a baseline) and still passes after E-01 through E-05.
  - Execution state: pending

- [ ] E-07 Add `tests/test_agy_profile_cli.py` covering the agy WRITE PATH and runner filtering, driving `cli.main([...])` in-process with `XDG_CONFIG_HOME` on a temp dir: (a) agy add with `--no-validate --set-default` writes the expected JSON and a subsequent `runner_profiles.resolve(load(), runner="agy").validate` is False with provenance naming the profile; (b) `aw agy profile list` omits an oc profile in the same store; (c) `aw agy profile show` output contains no `opencode run` and its `--json` carries `opencode_args` as null (E-02.1); (d) `validate-default on|off|unset` round-trips `defaults.validate` and `unset` removes the key.
  - Depends on: E-03, E-05
  - Expected outcome: all four pass with the change; (a) fails on the unpatched tree (argparse exit 2, "invalid choice: 'profile'").
  - Execution state: pending

- [ ] E-08 Add the ADD-FORM refusal tests to `tests/test_agy_profile_cli.py`, covering E-03's noninteractive contract: an incomplete invocation must refuse exit 2 and write nothing, an existing name must not be silently overwritten, and an unsupported field must be rejected by argparse rather than stored and ignored. Assert the store is ABSENT where it was never created and BYTE-IDENTICAL where it already existed. Separate from E-07 because a refusal proves a different property (that nothing was written) than a successful write does.
  - Depends on: E-03, E-07
  - Expected outcome: add without `--yes`, add without `--model`, add of an existing name without `--replace`, and any `--variant` for agy each exit 2 with the store absent or byte-identical.
  - Execution state: pending

- [ ] E-09 Add the CROSS-NAMESPACE refusal tests for E-04's guard: with an oc-owned profile in the store, each runner-scoped verb invoked from the agy namespace must refuse exit 2, name the owning runner, and leave the store byte-identical, while the oc namespace still reaches that profile normally. This is the only coverage of the destructive case (F-6) and is a separate item from E-08 because it depends on E-04 rather than on E-03.
  - Depends on: E-04, E-07
  - Expected outcome: `aw agy profile show/remove/default` against an oc-owned name each exit 2 with byte-identical store bytes; `aw oc profile show` of the same name still succeeds.
  - Execution state: pending

- [ ] E-10 Rewrite the "Setting the verification default on antigravity, by hand" section of `docs/runner-profiles.md` to document `aw agy profile add ... --set-default` and `aw agy profile validate-default`, keeping the JSON as the equivalent stored form (its `schema_version: 2` is correct and needs no change: `SCHEMA_VERSION = 2` with `SUPPORTED_SCHEMA_VERSIONS = frozenset((1, 2))`) and keeping the existing statements that antigravity has no `--profile` and ignores `execution_profile`. Also state the shared-namespace rule the E-04 guard enforces, so an operator learns it from the docs rather than from a refusal, and add a CHANGELOG `2.0.0 (pending)` bullet. User-facing prose: no em or en dashes, and do NOT claim an agy profile's `model` selects the model a run launches, because it does not (F-4).
  - Depends on: E-03, E-04, E-05
  - Expected outcome: `grep -n "does not exist" docs/runner-profiles.md` no longer matches the `aw agy profile` sentence; `grep -n "aw agy profile" docs/runner-profiles.md CHANGELOG.md` shows the new text.
  - Execution state: pending

- [ ] E-11 Run the bare suite `python3 -m pytest`.
  - Depends on: E-06, E-08, E-09, E-10
  - Expected outcome: the summary line reports 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Profile verbs are a FIXED namespace; a profile name is never a command (comment "THE VERBS ARE FIXED, WHICH IS THE POINT" above `p_oc_profile`). The agy namespace keeps that rule.
- `--agent` is the repo-wide machine-output flag and must not be redeclared on a `parents=[common]` subparser (comment above `--oc-agent`); agy needs no agent field at all.
- `runner_profiles` mutators are pure and `rp.save` is the one atomic write; `add_profile` is the no-clobber authority (`ProfileExistsError` without `replace`). Every handler already maps `RunnerProfileError` to exit 2 in `_run_oc_profile`.
- `parse_profile` already refuses a variant/agent for a runner whose `RunnerSpec` lacks support, and `validate_model` requires `provider/model` (measured: `gemini-3.7-flash-high` is refused, `google/gemini-3-pro` accepted).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | `aw agy profile` does not exist. | `python3 -m agent_workflows agy profile --help` -> "invalid choice: 'profile' (choose from 'runipd', 'run', 'runagy', 'review', 'integrate', 'sessions', 'view', 'view-antigravity-jsonl', 'exec')". |
| F-2 | Wizard and CLI handlers hardcode oc. | `runner_profile_wizard.RUNNER = "oc"`; `_oc_profile_add` writes `"runner": wiz.RUNNER`; `_oc_profile_default` calls `rp.clear_default_profile(cfg, "oc")`. |
| F-3 | `set_validate_default` has no PRODUCTION caller. CORRECTED AT REVIEW: it has SEVEN call sites in `tests/test_runner_profiles.py`, so it is a well-tested mutator with no caller in `agent_workflows/`, not dead code. The distinction matters because "a caller in the package" is already true of the test package, so E-05's bar is a caller in `agent_workflows/cli.py` specifically. | `grep -rn set_validate_default --include=*.py` -> the definition in `runner_profiles.py` plus `tests/test_runner_profiles.py` lines 1736, 1745, 1755, 1765, 1839-1840, 2336; no other `agent_workflows/` module. |
| F-4 | Antigravity consumes a profile only for the validate tier and only via `defaults.profiles.agy`. | `agy_runipd.resolve_verification_decision` passes `profile=None`; `initialize_run` uses `getattr(args, "model", DEFAULT_MODEL)`, not a profile model. |
| F-5 | The store already models agy fully (`RUNNER_REGISTRY["agy"]`, `validate_default=True`), so no schema change is needed. Re-verified at review, and the mechanism was driven end to end: an agy profile added and made default yields `default_profiles = {'agy': 'quiet'}` and `resolve(cfg, runner="agy")` returns `validate=False` with provenance `default-profile`. | `runner_profiles.RUNNER_REGISTRY`; driven probe at review. |
| F-6 | PROFILE NAMES ARE ONE FLAT NAMESPACE AND THREE MIRRORED VERBS WOULD LEAK ACROSS HOSTS. The store primitives `show`/`remove`/`default` reach are runner-BLIND: `ProfileConfig.get(self, name)` takes no runner, and `set_default_profile(cfg, name)` derives the runner from the PROFILE. Measured on a store holding one OC profile `gem`: `cfg.get('gem').runner` is `'oc'` (so `agy profile show gem` would display a foreign profile); `set_default_profile(cfg,'gem')` writes `default_profiles = {'oc': 'gem'}` (so `agy profile default gem` would silently rewrite the OPENCODE default from the antigravity namespace); `remove_profile(cfg,'gem',clear_default=True)` empties `profiles` (so `agy profile remove gem` would DELETE the OpenCode profile). E-04 guards all three in the CLI. | Driven at review; the two primitives' signatures. |
| F-7 | `add_profile`'s no-clobber is NAME-KEYED, not (name, runner)-keyed, which is why the namespace is genuinely flat: adding an agy profile named `gem` over an existing oc `gem` raises `ProfileExistsError profile 'gem' already exists; pass replace=True`. So a name cannot be reused per host, and the E-04 guard cannot be replaced by "look up within this runner". | Driven at review. |
| F-8 | NO TEST DRIVES ANY `aw oc profile` VERB, so E-01's "byte-identical" claim had nothing that could falsify it. `grep -rn '_run_oc_profile\|_oc_profile_add\|_oc_profile_list' tests/` returns nothing; the two `aw oc profile` matches in `tests/test_cli.py` are setup-wizard PROMPT strings (`assertIn("aw oc profile add", text)`), not invocations. E-06 adds the baseline. | Driven at review. |
| F-9 | E-02 TOUCHES A MACHINE CONTRACT AND A DISPLAY SEAM. `profile_dict`'s docstring records that it feeds `aw oc profile list/show` `--json`/`--agent` output, so omitting `opencode_args` would turn a consumer's read into a `KeyError` (hence E-02.1 emits null instead). `emit_preview` styles by matching the literals `"Equivalent OpenCode launch:"` and `startswith("opencode run ")`, exactly the lines E-02 removes; an unmatched line falls through to the plain `else`, so it degrades gracefully, and `preview_lines`' docstring warns the block "is asserted by substring in the tests". | Both docstrings; `emit_preview`'s branch conditions. |

## Proposed changes (ordered, validatable)

1. E-06: capture the oc baseline FIRST, since E-01's safety claim has no guard today (F-8).
2. E-01/E-02: runner-parameterize the existing handlers and preview (no behavior change for oc).
3. E-03: register `aw agy profile` reusing those handlers.
4. E-04: guard the runner-scoped verbs against the flat namespace (F-6).
5. E-05: one `validate-default` writer, reachable from both host namespaces.
6. E-07/E-08/E-09 tests, E-10 docs, E-11 full suite.

## Deferred / out of scope (with reason)

- An interactive TTY wizard for `aw agy profile add`. The existing wizard is built on the OpenCode model catalog (`oc_models.ModelCatalog`, `select_variant`, `ask_agent`), none of which applies to antigravity; the noninteractive form is complete for a two-field profile.
  - Carrier-Declined: low value while an agy profile carries only `model` and `validate`; revisit only if agy gains a model catalog.
- Making the agy driver launch the profile's `model` (and adding `--profile` / `as <profile>` to `aw agy run`).
  - Carrier-Declined: explicitly named as deferred dispatch-adapter work in the `agy_runipd.resolve_verification_decision` docstring; this plan only writes configuration and states the limit honestly (E-02, E-06).
- A host-neutral top-level `aw profile` noun.
  - Carrier-Declined: see OQ-01; the per-host namespaces cover the need without a new top-level noun, and OQ-01 is non-blocking, so the maintainer may choose it later as a registration-only change.
- Making the profile namespace per-runner in the store (so `gem` could exist for both hosts).
  - Carrier-Declined: that is a schema change to the shipped store with `add_profile`'s name-keyed no-clobber behind it (F-7), far beyond this plan. E-04's CLI guard makes the flat namespace safe without changing it, and E-09 documents the rule so an operator is not surprised.

## Scope check

- Over-scope: none. No change to `runner_profiles` schema or resolution, and no driver change. Note E-04 deliberately guards in the CLI rather than adding a runner argument to `ProfileConfig.get` / `set_default_profile`, both because this scope forbids it and because those primitives have many callers the oc path does not need to change.
- Under-scope: none relative to the backlog item; every question it lists is answered (verb shape, interaction with `aw oc profile default`, a dedicated `defaults.validate` verb). Review ADDED two requirements the backlog did not name: the cross-namespace guard (F-6) and the oc regression baseline (F-8).
- Explicitly OUT: the `runner_profiles` schema, its resolution precedence and its mutator signatures; the agy driver (`agy_runipd`), which still launches `DEFAULT_MODEL` and ignores a profile's `model` (F-4); an interactive wizard for agy; `--profile` / `as <profile>` on `aw agy run`; and any redeclaration of `--agent` on a `parents=[common]` subparser (the measured in-place mutation trap recorded above `--oc-agent`).

## Required tests / validation

New `tests/test_oc_profile_cli_regression.py` capturing the five oc verbs BEFORE the refactor (E-06, the guard F-8 shows is missing today), and new `tests/test_agy_profile_cli.py` in two items: the write path and runner filtering (E-07) and the refusals including the three cross-namespace ones (E-08). The agy write-path test must be shown failing before the change. Then the bare suite.

## Spec / documentation sync

- `docs/runner-profiles.md` (E-06) and `CHANGELOG.md`.
- No `.spec.md` is amended: the store schema and resolution precedence are unchanged; this only adds writers for fields the schema already defines.

## Open questions

### OQ-01: Which surface writes agy profiles and defaults.validate?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default adopted by this plan: per-host `aw agy profile` mirroring `aw oc profile` (consistent with the existing "everything specific to the Antigravity host, grouped under one noun" help text of `aw agy`), plus `validate-default` under both namespaces sharing one handler that states it is host-neutral. The alternative, a top-level host-neutral `aw profile`, is a public CLI contract choice the maintainer may prefer; switching later is a registration change only, since the handlers are runner-parameterized by E-01. LEFT OPEN DELIBERATELY AT REVIEW rather than resolved: this is a public CLI contract, which is the maintainer's to decide, and nothing is blocked by leaving it open. NEW EVIDENCE BEARING ON THE CHOICE (F-6, F-7): profile names are ONE FLAT NAMESPACE, so two per-host namespaces can each reach the other's rows and need the E-04 guard to refuse. A single top-level `aw profile` noun would make that shared namespace VISIBLE in the surface instead of hiding it behind two namespaces that look independent and are not. That is an argument for the alternative the maintainer may weigh; this plan's default remains the per-host form because it matches the existing `aw agy` grouping.
- Carrier-Declined: non-blocking and fully implemented either way by this plan's runner-parameterized handlers; if the maintainer later prefers `aw profile`, it is a registration change against code this plan already makes runner-neutral, not outstanding work this plan leaves undone.

### OQ-02: Should `aw agy profile add` default `--set-default` to on, since a non-default agy profile is inert?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The `aw oc profile` help promises "making a profile the default is a separate question that defaults to No", and silently changing which profile governs every agy run is the kind of implicit default the store design refuses. Instead the success message warns that the profile is inert until made default (E-03).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -nE 'default_profile_for\("oc"\)|clear_default_profile\(cfg, "oc"\)|"runner": wiz.RUNNER' agent_workflows/cli.py` returning no matches, AND E-06's full oc regression file passing (not merely one verb): the grep alone shows the literals are gone, not that behavior is preserved.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: three pastes. (a) `python3 -c "from agent_workflows import runner_profile_wizard as w, runner_profiles as rp; p=rp.parse_profile('q',{'runner':'agy','model':'google/gemini-3-pro'}); t='\n'.join(w.preview_lines('q',p)); print('opencode run' in t, 'defaults.profiles.agy' in t)"` printing `False True`. (b) `profile_dict('q', p)["opencode_args"]` printing `None`, proving the key is EMITTED AS NULL and not omitted (E-02.1; omitting it would break `--json` consumers with a `KeyError`). (c) `emit_preview` driven on that agy profile without raising, plus a statement of which substring assertions on the preview block were checked (F-9).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: in a FRESH temporary directory the executor creates (`mktemp -d`; do NOT hard-code a scratch path, and elide or genericize the path in the pasted output), paste `XDG_CONFIG_HOME=<tmp> python3 -m agent_workflows agy profile add quiet --model google/gemini-3-pro --no-validate --set-default --yes; echo rc=$?` showing rc=0, then `cat` of the written `runner-profiles.json` showing `"runner": "agy"`, `"validate": false` and `"agy": "quiet"` under `defaults.profiles`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: on a store holding ONE oc profile `gem`, paste all three cross-namespace refusals driven through `cli.main`: `aw agy profile show gem`, `aw agy profile remove gem --yes`, `aw agy profile default gem`, each showing exit 2, a message naming `oc` as the owning runner, and the store bytes BYTE-IDENTICAL before and after (hash or `cmp` the file, do not eyeball it). Also paste `aw oc profile show gem` still succeeding, so the guard is shown to scope rather than break. A run that shows only the refusal text without the byte-unchanged evidence does not validate this item: `remove` is the destructive case and unchanged bytes are the whole claim.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the temp-XDG run of `aw agy profile validate-default off` then `cat` showing `"validate": false` under `defaults`, then `aw oc profile validate-default unset` and `cat` showing the key GONE (absent, not `null`); plus `grep -n "set_validate_default(" agent_workflows/cli.py` showing the new PRODUCTION caller. Grepping the repository is not sufficient: seven test callers already exist (F-3), so the hit must be in `agent_workflows/cli.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_oc_profile_cli_regression.py` passing on the UNPATCHED tree (proving it is a baseline and not a description of the refactored behavior), and passing again after E-01 through E-05. Name the five verbs the file covers, since the point of the item is breadth: a file that exercises only `list` does not satisfy it (F-8).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_agy_profile_cli.py` passing with the change, and the write-path test run against the tree with E-03's `agy_sub.add_parser("profile", ...)` registration temporarily removed (a hand edit, never `git stash`) showing it FAILING with argparse's `invalid choice: 'profile'`, then restored and re-run green.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the add-form refusal tests passing, and for each refusal class state the store state asserted (absent, or byte-identical). Include the `--variant` argparse rejection message for agy, which proves argparse is enforcing `supports_variant=False` rather than the profile silently storing an ignored field.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste all three cross-namespace refusals driven through `cli.main` on a store holding one oc profile, each showing exit 2, a message naming `oc`, and the store bytes BYTE-IDENTICAL before and after (hash or `cmp` the file, do not eyeball it), plus `aw oc profile show` of the same name still succeeding. A run that shows only the refusal text without the byte-unchanged evidence does not validate this item: `remove` is the destructive case and unchanged bytes are the whole claim.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `grep -n "aw agy profile" docs/runner-profiles.md CHANGELOG.md` hits, `grep -n "does not exist" docs/runner-profiles.md` no longer matching the `aw agy profile` sentence, a `grep -nP "\x{2013}|\x{2014}"` over the changed doc lines returning nothing, and a quotation of the added prose showing it does NOT claim an agy profile's `model` selects the launched model (F-4) and DOES state the shared-namespace rule.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run showing `passed` with 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Eleven items, one concern: giving antigravity profiles and the host-neutral verification default a writer surface. The count grew from seven at review for four reasons, each a measured gap rather than added ambition: the cross-namespace guard (E-04) is a BLOCKER the original plan had no item for, because three mirrored verbs would otherwise read, retarget or DELETE the other host's profile; the oc regression baseline (E-06) is the guard E-01's "byte-identical" claim needs and that no existing test provides; and the original E-05 bundled eight sub-tests spanning several independent surfaces, which the deterministic linter also flagged (`IPD-Z602`); and the refusal tests then split again (E-08/E-09) when the linter flagged the merged item too, which was right because the add-form refusals depend on E-03 while the cross-namespace ones depend on E-04. The four test items are separate because they prove different properties: a baseline, a write path, that an incomplete write refused, and that a cross-host verb refused without touching the store. No item introduces a second concern.

WHAT A HUMAN IS APPROVING. New PUBLIC CLI SURFACE: an `aw agy profile` namespace with five verbs, plus a new `validate-default` verb under BOTH host namespaces. Four things to weigh. FIRST, OQ-01 is deliberately OPEN and is yours: per-host `aw agy profile` (this plan's default) versus a single top-level `aw profile`. Review added evidence bearing on it, namely that profile names are ONE FLAT NAMESPACE (F-6, F-7), so two per-host namespaces look independent and are not; a top-level noun would make that visible instead of guarded. Switching later is a registration-only change. SECOND, the honest limit: an agy profile's `model` does NOT select the model a run launches, because the driver uses `DEFAULT_MODEL` and passes `profile=None` (F-4); today only its `validate` field changes a run, and E-02/E-09 must say so rather than imply otherwise. THIRD, review found and fixed a destructive behavior the original plan would have shipped: `aw agy profile remove <oc-name>` deleting an OpenCode profile and `aw agy profile default <oc-name>` silently rewriting the OpenCode default. FOURTH, no capability is claimed for antigravity that a probe has not established; this writes configuration only.

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The intended surface: in `agent_workflows/cli.py`, the five `_oc_profile_*` handlers plus `_run_oc_profile` and `_oc_profile_result`, the new `agy_sub` profile registration and its dispatch in the `("agy", "antigravity")` branch, the shared runner-scope guard, and the shared `_profile_validate_default`; in `agent_workflows/runner_profile_wizard.py`, only `preview_lines` and `profile_dict` (leave `RUNNER = "oc"` in place as the oc default, as E-01 says); two new test files; one section of `docs/runner-profiles.md`; one `CHANGELOG.md` bullet. EXPLICITLY NOT IN SCOPE: `agent_workflows/runner_profiles.py` in any form (schema, resolution, or mutator signatures: the guard is in the CLI by design); `agy_runipd` and `run_dispatch`; an interactive agy wizard; `--profile` / `as <profile>` on `aw agy run`; the host capability registry; and redeclaring `--agent` on any `parents=[common]` subparser (the measured in-place-mutation trap recorded above `--oc-agent`). An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-04 and V-06. V-04 must show the store BYTE-IDENTICAL after each of the three refusals, hashed or `cmp`-ed rather than eyeballed, because `remove` is the destructive case and unchanged bytes are the entire claim; a refusal message proves only that something was printed. V-06 must be run on the UNPATCHED tree first, because a "baseline" written after the refactor describes the new behavior and guards nothing, and it must name all five verbs, since a file exercising only `list` reproduces the very gap F-8 measured.

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: `ProfileConfig.get` or `set_default_profile` has gained a runner parameter, which would mean E-04's premise has changed and the guard belongs elsewhere; `add_profile`'s no-clobber has become (name, runner)-keyed, which would make the namespace non-flat and E-04 unnecessary as designed (F-7); or `agy_runipd.resolve_verification_decision` now passes a profile name, which would mean the deferred dispatch-adapter work has landed and E-02's and E-09's honest-limit wording would be FALSE rather than merely conservative.

This plan is `reviewed` and needs explicit human approval (`Status: approved`) before execution. The executor commits only the Scope-Paths via `aw commit 6o8q4k -- <paths>`, never `git add -A`, and never pushes. It carries no `- Blocks-Release:` and none is owed: backlog `fxiqse` is `Work-Kind: feature`, so the every-live-bug gate does not apply. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run` / `aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-11 carry pasted evidence.
