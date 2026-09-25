# IPD: Add aw agy profile writer verbs and a defaults.validate writer

- Date: 2026-09-25
- Kind: child
- Concern: Antigravity runs resolve a stored verification choice (plan `ybkmzp`), but nothing shipped can write it: `runner_profile_wizard.RUNNER = "oc"` is baked into every `aw oc profile` handler, `aw agy profile` does not exist, and `runner_profiles.set_validate_default` has no caller, so operators must hand-edit `runner-profiles.json`.
- Scope: Parameterize the `aw oc profile` handlers by runner, register the same fixed verb set as `aw agy profile {add,list,show,remove,default}` (noninteractive `add` with `--validate/--no-validate`), add one `validate-default` verb under both namespaces that writes the host-neutral `defaults.validate` through `set_validate_default`, and replace the documented hand-edit step.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/runner_profile_wizard.py, tests/test_agy_profile_cli.py, docs/runner-profiles.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- Id: 6o8q4k
- From-Backlog: fxiqse
- Set: agyprofile
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us

## Workflow history

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

- [ ] E-02 In `runner_profile_wizard`, make `preview_lines` and `profile_dict` runner-aware: for `runner == "agy"` omit the "Equivalent OpenCode launch" block and `opencode_args`, and instead print a line stating the honest effect measured in `agy_runipd.resolve_verification_decision` ("NO PROFILE NAME IS PASSED"): an antigravity profile applies ONLY as `defaults.profiles.agy`, and today only its `validate` field changes a run (the driver launches `agy_runipd.DEFAULT_MODEL`, and `execution_profile` is ignored on that host).
  - Depends on: none
  - Expected outcome: `preview_lines("q", agy_profile)` contains no `opencode run` and does contain `defaults.profiles.agy`.
  - Execution state: pending

### Task group 2: the new verbs

- [ ] E-03 Register `aw agy profile` (alias `profiles`) under `agy_sub` with the same fixed subverbs as `oc_profile_sub` (`add`, `list`/`ls`, `show`, `remove`/`rm`, `default`), each `set_defaults(profile_runner="agy")`, and dispatch it in the `args.command in ("agy", "antigravity")` branch of `main` through `_run_oc_profile(args, profile_cmd)`, mirroring the oc branch ("if oc_cmd in (\"profile\", \"profiles\"):"). `aw agy profile add` is NONINTERACTIVE ONLY: it requires `NAME --model <provider/model> --yes`, refuses exit 2 with nothing written otherwise, accepts `--validate`/`--no-validate` (tri-state, omitted means unset), `--replace`, `--set-default`, and offers no `--variant`/`--oc-agent` (the `agy` `RunnerSpec` has `supports_variant=False, supports_agent=False`). When `--set-default` is absent, the success message warns that the profile is inert until `aw agy profile default NAME`.
  - Depends on: E-01, E-02
  - Expected outcome: `aw agy --help` lists `profile`; `aw agy profile add quiet --model google/gemini-3-pro --no-validate --set-default --yes` writes `profiles.quiet` with `runner: agy`, `validate: false` and `defaults.profiles.agy: quiet` in one `rp.save`.
  - Execution state: pending

- [ ] E-04 Add a `validate-default` subverb to BOTH `aw oc profile` and `aw agy profile`, taking exactly one of `on`, `off`, `unset`, handled by one shared `_profile_validate_default(args)` that calls `rp.set_validate_default(cfg, True|False|None)` then `rp.save`. Its output states that `defaults.validate` is HOST-NEUTRAL (applies to every host and to any profile that does not set its own `validate`) and reports the resolved value for both runners via `rp.resolve(cfg, runner=r)` so the operator sees the effect.
  - Depends on: E-01
  - Expected outcome: `aw agy profile validate-default off` then `aw oc profile validate-default unset` leave the store with no `defaults.validate` key; `set_validate_default` now has a caller in the package.
  - Execution state: pending

### Task group 3: tests and docs

- [ ] E-05 Add `tests/test_agy_profile_cli.py` driving `cli.main([...])` in-process with `XDG_CONFIG_HOME` pointed at a temp dir (the pattern `tests/test_cli.py` uses): (a) agy add with `--no-validate --set-default` writes the expected JSON and a subsequent `runner_profiles.resolve(load(), runner="agy").validate` is False with provenance naming the profile; (b) add without `--yes` or without `--model` exits 2 and leaves the store absent; (c) add of an existing name without `--replace` exits 2 and bytes are unchanged; (d) `--variant` is rejected by argparse for agy; (e) `aw agy profile list` omits an oc profile in the same store; (f) `validate-default on|off|unset` round-trips `defaults.validate` and `unset` removes it; (g) `aw oc profile list --json` output for an oc-only store is unchanged by E-01 (regression guard); (h) `aw agy profile show` output contains no `opencode run`.
  - Depends on: E-03, E-04
  - Expected outcome: all tests pass with the change; (a) fails on the unpatched tree (argparse exit 2, "invalid choice: 'profile'").
  - Execution state: pending

- [ ] E-06 Rewrite the "Setting the verification default on antigravity, by hand" section of `docs/runner-profiles.md` to document `aw agy profile add ... --set-default` and `aw agy profile validate-default`, keep the JSON as the equivalent stored form, and keep the existing statements that antigravity has no `--profile` and ignores `execution_profile`. Add a CHANGELOG `2.0.0 (pending)` bullet. User-facing prose: no em or en dashes.
  - Depends on: E-03, E-04
  - Expected outcome: `grep -n "does not exist" docs/runner-profiles.md` no longer matches the `aw agy profile` sentence; `grep -n "aw agy profile" docs/runner-profiles.md CHANGELOG.md` shows the new text.
  - Execution state: pending

- [ ] E-07 Run the bare suite `python3 -m pytest`.
  - Depends on: E-05, E-06
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
| F-3 | `set_validate_default` has no caller. | `grep -rn set_validate_default agent_workflows/` hits only its definition in `runner_profiles.py`. |
| F-4 | Antigravity consumes a profile only for the validate tier and only via `defaults.profiles.agy`. | `agy_runipd.resolve_verification_decision` passes `profile=None`; `initialize_run` uses `getattr(args, "model", DEFAULT_MODEL)`, not a profile model. |
| F-5 | The store already models agy fully (`RUNNER_REGISTRY["agy"]`, `validate_default=True`), so no schema change is needed. | `runner_profiles.RUNNER_REGISTRY`. |

## Proposed changes (ordered, validatable)

1. E-01/E-02: runner-parameterize the existing handlers and preview (no behavior change for oc).
2. E-03: register `aw agy profile` reusing those handlers.
3. E-04: one `validate-default` writer, reachable from both host namespaces.
4. E-05 tests, E-06 docs, E-07 full suite.

## Deferred / out of scope (with reason)

- An interactive TTY wizard for `aw agy profile add`. The existing wizard is built on the OpenCode model catalog (`oc_models.ModelCatalog`, `select_variant`, `ask_agent`), none of which applies to antigravity; the noninteractive form is complete for a two-field profile.
  - Carrier-Declined: low value while an agy profile carries only `model` and `validate`; revisit only if agy gains a model catalog.
- Making the agy driver launch the profile's `model` (and adding `--profile` / `as <profile>` to `aw agy run`).
  - Carrier-Declined: explicitly named as deferred dispatch-adapter work in the `agy_runipd.resolve_verification_decision` docstring; this plan only writes configuration and states the limit honestly (E-02, E-06).
- A host-neutral top-level `aw profile` noun.
  - Carrier-Declined: see OQ-01; the per-host namespaces cover the need without a new top-level noun.

## Scope check

- Over-scope: none. No change to `runner_profiles` schema or resolution, and no driver change.
- Under-scope: none relative to the backlog item; every question it lists is answered (verb shape, interaction with `aw oc profile default`, a dedicated `defaults.validate` verb).

## Required tests / validation

New `tests/test_agy_profile_cli.py` (write path, refusals, no-clobber, runner filtering, validate-default round-trip, oc regression guard), shown failing before the change, plus the bare suite.

## Spec / documentation sync

- `docs/runner-profiles.md` (E-06) and `CHANGELOG.md`.
- No `.spec.md` is amended: the store schema and resolution precedence are unchanged; this only adds writers for fields the schema already defines.

## Open questions

### OQ-01: Which surface writes agy profiles and defaults.validate?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default adopted by this plan: per-host `aw agy profile` mirroring `aw oc profile` (consistent with the existing "everything specific to the Antigravity host, grouped under one noun" help text of `aw agy`), plus `validate-default` under both namespaces sharing one handler that states it is host-neutral. The alternative, a top-level host-neutral `aw profile`, is a public CLI contract choice the maintainer may prefer; switching later is a registration change only, since the handlers are runner-parameterized by E-01.

### OQ-02: Should `aw agy profile add` default `--set-default` to on, since a non-default agy profile is inert?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The `aw oc profile` help promises "making a profile the default is a separate question that defaults to No", and silently changing which profile governs every agy run is the kind of implicit default the store design refuses. Instead the success message warns that the profile is inert until made default (E-03).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -nE 'default_profile_for\("oc"\)|clear_default_profile\(cfg, "oc"\)|"runner": wiz.RUNNER' agent_workflows/cli.py` returning no matches, and E-05 test (g) passing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste output of `python3 -c "from agent_workflows import runner_profile_wizard as w, runner_profiles as rp; p=rp.parse_profile('q',{'runner':'agy','model':'google/gemini-3-pro'}); t='\n'.join(w.preview_lines('q',p)); print('opencode run' in t, 'defaults.profiles.agy' in t)"` printing `False True`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `XDG_CONFIG_HOME=/tmp/opencode/g3/probe-agyprofile/cfg python3 -m agent_workflows agy profile add quiet --model google/gemini-3-pro --no-validate --set-default --yes; echo rc=$?` showing rc=0, then `cat` of the written `runner-profiles.json` showing `"runner": "agy"`, `"validate": false` and `"agy": "quiet"` under `defaults.profiles`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the same temp-XDG run of `aw agy profile validate-default off` then `cat` showing `"validate": false` under `defaults`, then `aw oc profile validate-default unset` and `cat` showing the key gone; plus `grep -rn "set_validate_default(" agent_workflows/cli.py` showing the new caller.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_agy_profile_cli.py` passing with the change, and the same file run against the tree with E-03's `agy_sub.add_parser("profile", ...)` registration temporarily removed showing test (a) FAILING, then restored.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `grep -n "aw agy profile" docs/runner-profiles.md CHANGELOG.md` hits, `grep -n "aw agy profile\` does not exist" docs/runner-profiles.md` returning nothing, and a `grep -nP "\x{2013}|\x{2014}"` over the changed doc lines returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run showing `passed` with 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <this plan> -- <Scope-Paths>`; never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence.
