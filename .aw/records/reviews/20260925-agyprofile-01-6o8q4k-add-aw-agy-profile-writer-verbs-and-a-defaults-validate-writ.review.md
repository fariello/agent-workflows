# Review: Add aw agy profile writer verbs and a defaults.validate writer

- Subject-Id: 6o8q4k
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `a4743424`. The target plan was committed and unchanged, so the
pre-review snapshot was correctly skipped per Step 1. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) with ONE advisory, `IPD-Z602` on
E-05 ("action text may bundle multiple concerns"), which is the deterministic linter independently
reaching the right-sizing finding I record below as PR-905. After the revisions, both
`--phase review-finalize` and the advisory are clean.

THE PROBLEM IS REAL AND FOUR OF THE FIVE FINDINGS HOLD EXACTLY. F-1: `aw agy profile` genuinely does
not exist, and argparse refuses with `invalid choice: 'profile' (choose from 'runipd', 'run',
'runagy', 'review', 'integrate', 'sessions', 'view', 'view-antigravity-jsonl', 'exec')`. F-2:
`runner_profile_wizard.RUNNER = "oc"`, `_oc_profile_add` writes `"runner": wiz.RUNNER`, and
`_oc_profile_default` / `_oc_profile_remove` both call `default_profile_for("oc")` and
`clear_default_profile(cfg, "oc")` with the literal. F-4: `resolve_verification_decision` passes
`profile=None` and its docstring says so in capitals ("NO PROFILE NAME IS PASSED"), while
`initialize_run` uses `getattr(args, "model", DEFAULT_MODEL)`. F-5: `RUNNER_REGISTRY["agy"]` is
`RunnerSpec(name='agy', aliases=('antigravity',), supports_variant=False, supports_agent=False,
validate_default=True)`, so the schema needs no change. I also drove the store end to end and
confirmed the plan's central mechanism works: `set_default_profile` derives the runner from the
PROFILE, so adding an agy profile and setting it default writes `default_profiles = {'agy': 'quiet'}`
and `resolve(cfg, runner="agy")` returns `validate=False` with provenance `default-profile`.

THEN I DROVE THE PROPOSED CLI AGAINST THE STORE, AND FOUND THE GAP THAT DOMINATES THIS REVIEW:
PROFILE NAMES ARE ONE FLAT NAMESPACE, AND THREE OF THE FIVE MIRRORED VERBS LEAK ACROSS HOSTS. The
plan parameterizes the runner for `add` and for `list` (E-01 says "`list` shows only profiles whose
`runner` matches"), but `show`, `remove` and `default` all reach the store through `cfg.get(name)` or
`set_default_profile(cfg, name)`, neither of which takes a runner. Measured on a store holding one
OC profile named `gem`:

- `aw agy profile show gem` would SUCCEED and display an OpenCode profile, because `cfg.get` is
  runner-blind (`cfg.get('gem').runner` is `'oc'`).
- `aw agy profile default gem` would write `default_profiles = {'oc': 'gem'}`, i.e. silently set the
  OPENCODE default from inside the antigravity namespace, with no error, because
  `set_default_profile` reads `profile.runner` and ignores the caller's intent.
- `aw agy profile remove gem` would DELETE the OpenCode profile.

The third is destructive and the second is worse than destructive: it is a silent cross-host
configuration change, on a store whose entire design philosophy the plan itself quotes ("making a
profile the default is a separate question that defaults to No"). `add_profile` is unaffected because
its no-clobber check is name-keyed, which I also measured: adding an agy profile named `gem` over an
oc `gem` raises `ProfileExistsError` rather than creating a second row. So the namespace really is
flat, and a runner-scoped verb set over a flat namespace needs an explicit guard. The plan has none,
and `- Scope: ... no change to runner_profiles` means the guard has to live in the CLI handlers.

THE SECOND SUBSTANTIAL FINDING IS THAT E-01's SAFETY CLAIM HAS NO GUARD AT ALL. Its expected outcome
is that `aw oc profile ...` output and exit codes are "byte-identical to today". I searched for a
test that drives those handlers and there is NONE: `grep -rn '_run_oc_profile\|_oc_profile_add'
tests/` returns nothing, and the only `tests/test_cli.py` hits for "aw oc profile" are setup-wizard
PROMPT strings, not the verbs. So E-01 refactors five handlers with a regression claim that no
existing test can falsify, and E-05(g) as authored covers only `aw oc profile list --json`. That is
one of five verbs.

E-02 ALSO BREAKS A DISPLAY SEAM THE PLAN DOES NOT MENTION. `emit_preview` styles its output by
matching literal strings, including `elif stripped == "Equivalent OpenCode launch:"` and
`elif stripped.startswith("opencode run ")`. E-02 removes exactly those lines for agy. The function
degrades gracefully (an unmatched line falls through to the plain `else`), so this is not a crash,
but `preview_lines`' own docstring records that two `cli.py` paths reuse it and that "the block is
asserted by substring in the tests", so an executor changing the block must check those assertions
rather than discover them. E-02 also proposes changing `profile_dict` to omit `opencode_args` for
agy, and `profile_dict`'s docstring says it is consumed by `--json`/`--agent` output, which makes that
a machine-readable CONTRACT change: a consumer reading `opencode_args` would get a `KeyError` instead
of a null. Omitting a key and emitting it as null are different promises, and the plan picks one
without saying it is choosing.

ON F-3 the plan overstates in a way worth correcting because its E-04 expected outcome depends on it.
It says `set_validate_default` "has no caller" and cites
`grep -rn set_validate_default agent_workflows/`. That grep is right, but the function has SEVEN test
call sites in `tests/test_runner_profiles.py`, so it is not untested dead code, it is a mutator with
no PRODUCTION caller. The distinction matters: E-04's outcome "`set_validate_default` now has a
caller in the package" is already true of the test package, so the honest bar is a caller in
`agent_workflows/`, which is what V-04 should assert.

ON OQ-01, I did not resolve it, and I want to be explicit that this is deliberate rather than an
omission. It asks which SURFACE writes agy profiles: per-host `aw agy profile` (the plan's default)
or a top-level host-neutral `aw profile`. That is a PUBLIC CLI CONTRACT decision, which the workflow
reserves to the human, and the plan is right that switching later is a registration-only change once
E-01 lands. It is correctly marked `Blocking: no`, so it does not hold the plan. I did add the
namespace-collision measurement to it, because that evidence bears on the choice: a top-level
`aw profile` noun would make the flat namespace visible instead of hiding it behind two per-host
namespaces that can reach each other's rows.

ON RIGHT-SIZING the linter and I agree. E-05 bundled eight lettered sub-tests spanning the write
path, three distinct refusals, argparse rejection, runner filtering, a round-trip, an oc regression
guard and a preview-content assertion. `IPD-Z602` flagged it independently. It is now split into the
agy write-path tests, the refusal/no-clobber tests, and the oc regression guard, which is the one
that protects E-01's claim and deserves to fail on its own.

Two things I checked and found correct, recorded so a later reader does not re-derive them. The
`--oc-agent` convention is real and load-bearing: the comment above it records that declaring
`--agent` on a `parents=[common]` subparser MUTATES the shared action object in place under this
file's `conflict_handler="resolve"`, measured to have emptied `common`'s own `--agent`. The plan
correctly says agy needs no agent field, so it never approaches that trap. And the docs' JSON
examples use `schema_version: 2`, which matches `SCHEMA_VERSION = 2` with `SUPPORTED_SCHEMA_VERSIONS
= frozenset((1, 2))`, so E-06 does not need to touch them.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | BLOCKER | UNDER-SCOPE | A. Correctness / B. Authorization boundary | Driven at review on a store holding one OC profile `gem`: `cfg.get('gem').runner` is `'oc'` (so `agy profile show gem` displays a foreign profile); `set_default_profile(cfg,'gem')` writes `default_profiles = {'oc': 'gem'}` (so `agy profile default gem` silently sets the OPENCODE default); `remove_profile(cfg,'gem',clear_default=True)` leaves `profiles` empty (so `agy profile remove gem` deletes the OC profile). `ProfileConfig.get` takes only `name`; `set_default_profile` reads `profile.runner` and takes no runner argument | PROFILE NAMES ARE ONE FLAT NAMESPACE AND THREE MIRRORED VERBS LEAK ACROSS HOSTS. E-01 parameterizes the runner for `add` and filters `list`, but `show`, `remove` and `default` all reach the store through runner-blind primitives, so each would operate on a profile belonging to the OTHER host with no error. `remove` is DESTRUCTIVE and `default` is a SILENT cross-host configuration change on the very store whose design the plan quotes as refusing implicit defaults. Since `- Scope:` forbids changing `runner_profiles`, the guard must be in the CLI handlers, and the plan has none. | C:Low (one shared guard helper); U:Low (a clear refusal naming the owning runner); S:Medium (a destructive verb crossing a namespace boundary); F:High if unguarded; Overall:Low for the FIX | FIXED | New E-04 adds ONE shared runner-scope guard used by `show`, `remove` and `default`: look up the profile, and if `profile.runner != args.profile_runner`, refuse exit 2 naming the profile, its actual runner, and the correct command, writing nothing. `default --clear` is exempt (it is already runner-scoped via `clear_default_profile(cfg, runner)`). Added F-6 with all three measurements and F-7 recording that `add_profile` is name-keyed so a name cannot be reused per host. New V-04 requires all three refusals driven with byte-unchanged store evidence. |
| PR-902 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing | `grep -rn '_run_oc_profile\|_oc_profile_add\|_oc_profile_list' tests/` returns NOTHING; the only `tests/test_cli.py` matches for `aw oc profile` are setup-wizard prompt strings (`assertIn("aw oc profile add", text)`), not the verbs; E-05(g) as authored covered only `aw oc profile list --json` | E-01'S "BYTE-IDENTICAL" CLAIM HAS NO TEST THAT COULD FALSIFY IT. The plan refactors five handlers plus `_oc_profile_result`'s command label and expects the oc surface unchanged, but zero existing tests drive any oc profile verb, so the entire regression surface for the change is one new sub-test on one verb's JSON output. A silent change to `show`, `remove`, `default` or `add` output would ship green. | C:Low; U:Low; S:Low; F:High (an unguarded refactor of five public verbs); Overall:Low (the fix is adding coverage, which cannot break anything) | FIXED | E-05 is now a DEDICATED oc regression item covering all five verbs (`add` noninteractive, `list`, `show`, `remove`, `default`) plus their exit codes and the `oc profile <verb>` command label, captured BEFORE E-01 and compared after. V-05 requires the before/after comparison pasted, and states that a pass which only exercises `list` does not satisfy the item. Added F-8 recording the measured absence of coverage. |
| PR-903 | MEDIUM | IN-SCOPE | A. Correctness / C. Architecture (machine contract) | `profile_dict`'s docstring: "Used by `aw oc profile list/show` for `--json`/`--agent` output"; `emit_preview` branches on `elif stripped == "Equivalent OpenCode launch:"` and `elif stripped.startswith("opencode run ")`; `preview_lines`' docstring: "two `aw oc profile` code paths in `cli.py` reuse this ... the block is asserted by substring in the tests" | E-02 CHANGES A MACHINE-READABLE OUTPUT SHAPE AND A DISPLAY SEAM WITHOUT SAYING SO. Omitting `opencode_args` from `profile_dict` for agy is a `--json`/`--agent` CONTRACT change: a consumer reading that key gets a `KeyError` rather than a null, and omitting-versus-null are different promises the plan picks between silently. Removing the two preview lines also removes exactly the strings `emit_preview` matches on; it degrades gracefully (the plain `else` catches them) but an executor should verify rather than discover that, and the docstring warns the block is substring-asserted. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now states the `profile_dict` decision EXPLICITLY (emit `opencode_args: null` for agy rather than omitting the key, so the JSON shape stays stable for any consumer) with the reason, requires checking `emit_preview`'s two literal branches and any substring assertions before changing the block, and cites both docstrings. V-02 now asserts the agy JSON carries `opencode_args` as null and that `emit_preview` does not crash on an agy profile. |
| PR-904 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: three sentences (approval, `aw commit`, transition); compare pending plan `t0jyb2`'s gate | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS. No statement of what a human is approving, which matters here because the change ADDS PUBLIC CLI SURFACE (a new verb namespace and a new verb under an existing one) and OQ-01 leaves the shape deliberately to the maintainer; no scope fence within the five declared paths; no stop conditions; and a transition instruction with no runner/executor ownership split. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph naming the new public surface, OQ-01's open contract choice and the honest limit that an agy profile's `model` still does not launch anything; a per-path scope fence stated as a DECLARATION with an explicit not-in-scope list; the hard-MUST honesty rule naming V-04 and V-05 as the items most exposed to faking and why; three genuine stop conditions; and the transition with conditional runner/executor ownership and no hand-rolled `git mv`. |
| PR-905 | MEDIUM | UNDER-SCOPE | G. Plan executability (right-sizing) | `aw ipd lint --phase author --detail` emitted `IPD-Z602 (line 57): E-05: action text may bundle multiple concerns (explicit multi-part enumeration with multiple independent actions or deliverables)`; E-05 as authored carried eight lettered sub-tests | THE DETERMINISTIC LINTER AND THE SEMANTIC REVIEW AGREE THAT E-05 IS OVERLOADED. Its eight sub-tests span the write path, three distinct refusal classes, argparse rejection, runner filtering, a round-trip and an oc regression guard: several independent test surfaces with different failure modes. Most consequentially, the oc regression guard (PR-902's whole remedy) was one letter inside an item whose other seven letters concern the new agy surface, so an executor could satisfy E-05 while barely testing the refactor's blast radius. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into FOUR items: E-06 the dedicated oc regression baseline (ordered first because it must be captured pre-refactor), E-07 the agy write path and runner filtering, E-08 the add-form refusals, E-09 the cross-namespace refusals. The first split left the merged refusal item still flagged by `IPD-Z602`, which was correct: the add-form refusals depend on E-03 while the cross-namespace ones depend on E-04, so they split again. Eleven items with an 11:11 E/V bijection; `- Highest E allocated:` raised to 11. `aw ipd lint --phase review-finalize` now reports `conforming` with ZERO advisories. |
| PR-906 | LOW | IN-SCOPE | F. Honest documentation | `grep -rn set_validate_default --include=*.py` finds the definition in `runner_profiles.py` and SEVEN call sites in `tests/test_runner_profiles.py` (lines 1736, 1745, 1755, 1765, 1839-1840, 2336) | F-3 OVERSTATES, AND E-04's SUCCESS BAR INHERITS THE ERROR. "has no caller" is false as stated: the mutator has no PRODUCTION caller but is well covered by tests. E-04's expected outcome, "`set_validate_default` now has a caller in the package", is therefore already satisfied by the test package, so as written it could be marked done without the new writer existing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 restated as "no caller in `agent_workflows/`; seven call sites in `tests/test_runner_profiles.py`", with the grep that distinguishes them. The validate-default item's expected outcome now requires a caller in `agent_workflows/cli.py` specifically, and its V item greps that file rather than the repository. |
| PR-907 | LOW | IN-SCOPE | E. Testing / B. Privacy | V-03 and V-04 hard-code `XDG_CONFIG_HOME=/tmp/opencode/g3/probe-agyprofile/cfg`; `aw sanitize` exists precisely to keep machine-local paths out of shared artifacts, and the repository's own `tests/__init__.py` redirects `XDG_CONFIG_HOME` to an isolated test home | THE VALIDATION EVIDENCE PRESCRIBES A HARD-CODED MACHINE-LOCAL SCRATCH PATH. It is also a path from the AUTHOR's session (`/tmp/opencode/g3/...`), so the pasted evidence would carry a foreign session directory into the plan record, and an executor on another machine would either recreate that exact path or silently deviate from the stated command. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both V items now say to use a FRESH temporary directory created by the executor (e.g. `mktemp -d`) and to paste the command with the path elided or generically named, never a hard-coded session path. The substantive assertions (rc, the written JSON keys) are unchanged. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The profile namespace is flat and three mirrored verbs can reach the other host's rows. Guard in the CLI, widen `runner_profiles`, or accept the leak? | Guard in the CLI, with one shared helper used by `show`, `remove` and `default`. | (a) Accept the leak - rejected: `agy profile remove <oc-name>` DELETES an OpenCode profile and `agy profile default <oc-name>` silently rewrites the OPENCODE default, both measured; a destructive cross-namespace verb is not a defensible shipped behavior. (b) Add runner arguments to `ProfileConfig.get` / `set_default_profile` - rejected as out of scope (`- Scope:` declares no `runner_profiles` change) and as a wider blast radius: those primitives have many callers and the oc path does not need the parameter. (c) Namespace the store per runner - rejected outright: a schema change to the shipped store, far beyond this plan, and `add_profile`'s name-keyed no-clobber would have to change with it. | Driven: `cfg.get('gem').runner == 'oc'`; `set_default_profile(cfg,'gem')` -> `{'oc': 'gem'}`; `remove_profile` empties `profiles`; `ProfileConfig.get(self, name)` and `set_default_profile(cfg, name)` signatures take no runner | yes |
| D-2 | E-02 changes `profile_dict` for agy. Omit `opencode_args` or emit it as null? | Emit `opencode_args: null`. | (a) Omit the key, as E-02 originally implied - rejected: `profile_dict`'s docstring says it feeds `--json`/`--agent` output, so a missing key is a machine-contract change that turns a consumer's read into a `KeyError`, while a null is a value that consumer can already handle. A stable shape across hosts is also what lets one consumer read both. | `profile_dict` docstring ("Used by `aw oc profile list/show` for `--json`/`--agent` output"); the repository's output contract lives in `docs/cli-output-contract.md` | yes |
| D-3 | E-01 claims byte-identical oc behavior with no test able to falsify it. Add coverage, or accept the claim? | Add a dedicated oc regression item covering all five verbs, captured before the refactor. | (a) Accept E-01's expected outcome as stated - rejected: measured, no test drives any oc profile verb, so "byte-identical" is unfalsifiable and a regression in four of five verbs would ship green. (b) Keep it as one letter of the agy test item - rejected: that is what PR-905 splits, and burying the refactor's only guard inside the new-feature tests is how it gets satisfied without being exercised. | `grep -rn '_run_oc_profile\|_oc_profile_add' tests/` returns nothing; the `aw oc profile` strings in `tests/test_cli.py` are wizard PROMPTS | yes |
| D-4 | OQ-01 asks whether the writer surface should be per-host (`aw agy profile`) or a top-level `aw profile`. Resolve it? | NO. Leave it OPEN and non-blocking for the maintainer, and add the namespace measurement to it. | (a) Resolve in favor of the plan's per-host default - rejected: this is a PUBLIC CLI CONTRACT, which the workflow reserves to the human, and the plan already records that switching later is registration-only once E-01 lands, so nothing is blocked by leaving it open. (b) Resolve in favor of `aw profile` - rejected for the same reason, and it would discard the plan's stated consistency argument with the existing `aw agy` help text. | The plan's own OQ-01 rationale; `Blocking: no`; measured namespace flatness, which is new evidence bearing on the choice and is now recorded in the question | yes |
| D-5 | F-3 says `set_validate_default` has no caller, but tests call it. Correct the finding, or leave it? | Correct it, and tighten the item's success bar to name `agent_workflows/cli.py`. | (a) Leave F-3 as written - rejected: the claim is false as stated and, worse, the expected outcome derived from it ("now has a caller in the package") is ALREADY TRUE of the test package, so the item could be marked done with no writer shipped. | `grep -rn set_validate_default --include=*.py` -> one definition in `runner_profiles.py` plus seven sites in `tests/test_runner_profiles.py`, none in any other `agent_workflows/` module | yes |
