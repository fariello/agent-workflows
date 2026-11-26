# Review findings: ipd m7jcis

- Subject-Id: m7jcis
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261124T195133Z-1320375`). The target plan `.aw/records/plans/pending/20261122-cliverbs-01-m7jcis-add-per-state-runner-profile-routing-path-host-fallback-and.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0). The review read spec `ogd2nv` (R-07, R-08, AC-04), backlog item `i8dc07`, orchestrator `lmlji2`, sibling `xocj8i`, `agent_workflows/runner_profiles.py`, `agent_workflows/run_dispatch.py`, `agent_workflows/agy_runipd.py`, the `aw oc profile` / `aw agy profile` parsers and handlers in `agent_workflows/cli.py`, `agent_workflows/runner_profile_wizard.py`, `agent_workflows/command_surface.py`, `tests/conformance_matrix.py`, `tests/test_runner_profiles.py`, `tests/test_completion.py`, `tests/test_cli.py`, and `docs/runner-profiles.md`.

### Step T

1. Yes; the plan adds public library APIs (`resolve_for_state`, `run_dispatch.dispatch_for_state`) that Order 03 (`xocj8i`) wires into every verb-first command, and a new top-level CLI command (`aw profile`).
2. Partly; it changes which host a runner launches (host-selection precedence, a new `AW_HOST` environment override, `PATH` detection), but touches no commit, worktree-isolation, merge, or sandbox code.
3. Moderate; `6` E-items in `4` task groups across `4` production files, `1` document, and `3` test files after review.
4. Yes after review; `- Scope-Paths:` now lists `tests/test_runner_profiles.py`, `agent_workflows/command_surface.py`, `tests/conformance_matrix.py`, and `docs/runner-profiles.md`.
5. Moderate; `runner_profiles.py` is read by both host runners and `aw run`, and its store fails closed on any unknown key, so a schema mistake refuses every run for the user.

AW-TIER: standard

### Step R1

- Checked: every symbol and path the plan cites: `SCHEMA_VERSION` (line 232), `SUPPORTED_SCHEMA_VERSIONS` (254) and the comment above it naming the bump the "REQUIRED COMPANION of the first plan that makes the key consumable", `ALLOWED_DOCUMENT_KEYS` (279), `PROVENANCE_VALUES` (717), `from_document` (1186), `_replace` (1349), `remove_profile` (1393), `resolve` (1516); `run_dispatch.RUNNER_ADAPTERS` (112, `oc` only), `adapter_for` (123), `dispatch` (302); no top-level `profile` parser in `cli.py`; `AW_HOST` absent from `agent_workflows/`.
- Measured: `set_default_profile` on a version 1 config returns a version 1 config, so mutators preserve the loaded schema version.
- Found the missing schema storage and version bump (`PR-001`), nonexistent test globs and the `slow` marker on `tests/test_cli.py` (`PR-011`), and the stale documentation (`PR-016`).

### Step R2

- Checked: E/V bijection (`6/6` after `aw ipd sync --apply` assigned E-05 and E-06), dependency order, `- Item-Dependencies: none` (correct for Order 01), V-item evidence demands, and the approval gate.
- Found missing parser-leaf declarations (`PR-014`), unqualified `AC-04` and an incomplete gate (`PR-012`), and unstated exit-code ownership (`PR-013`).

### Step R3

- Checked: `AW_HOST` is a user-controlled value that selects a host; the plan now canonicalizes it through `canonical_runner` and refuses an unknown value instead of ignoring it, so a typo cannot silently route work to a different host. `PATH` detection only checks for two fixed binary names through `shutil.which`; no value from the environment reaches a subprocess argv.

### Step R4

- Checked: correctness of the precedence against host capability, the existing docstring contracts, and store compatibility.
- Found the undispatchable `agy` host (`PR-002`), duplicated field resolution in dispatch (`PR-003`), the docstring contradictions (`PR-004`), undefined `AW_HOST` semantics (`PR-005`), dangling state references on profile removal (`PR-006`), missing provenance values (`PR-007`), no CLI for `default_runner` (`PR-008`), unstated runner choice in host-neutral leaves (`PR-009`), and the `aw-profile` name collision (`PR-010`).

### Step R7

- Checked: `xocj8i` consumes `dispatch_for_state` and owns its own verbs, completions, `command_surface` entries, and `docs/cli-output-contract.md`, but not `aw profile` leaves or `docs/runner-profiles.md`; `p06t7i` does not touch runner profiles. Completion tables in `tests/test_completion.py` pin `aw oc profile <TAB>`, which the plan now leaves unchanged (`PR-015`).

### Step S5

- Checked: `## Open questions`. OQ-01 (Antigravity dispatch adapter) is resolved for this plan's behavior from repository evidence; the Set-scope question is carried by `xocj8i` in `## Deferred` and raised to the maintainer as a non-gating question. No blocking question remains.

### Pass 2

- Re-checked the complete revised plan: front matter, `## Goal` and its Mermaid flowchart, `E-01..E-06`, `## Project conventions discovered (Step 0)`, `## Findings`, `## Proposed changes`, `## Deferred`, `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-06`, and `## Approval and execution gate`.
- Replaced the `E-NEW` placeholders and cross-references with the assigned ids, filled V-05 and V-06, and added the module docstring example update to E-01.
- `aw ipd lint --phase author --agent` returned `clean` with one `IPD-Z603` info advisory (6 E-items against guidance of about 5). Accepted: E-05 and E-06 are small single-file steps, and a further split would add a dependency edge without reducing risk.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | UNDER-SCOPE | R1 / Schema storage and version | agent_workflows/runner_profiles.py:232, 240-254, 279; tests/test_runner_profiles.py:3576, 3976 | The store refuses unknown top-level keys and its own comment requires a version bump with the first consumed new key; the plan named neither where per-state bindings live nor the bump, and the tests pinning the constants were outside Scope-Paths. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | E-01 adds a top-level `states` key, `SCHEMA_VERSION = 3`, a write-version-3-only-with-a-binding rule (mutators preserve version), omission when empty (digest stable), and the constant-test updates; `tests/test_runner_profiles.py` joins Scope-Paths. |
| PR-002 | HIGH | IN-SCOPE | R4 / Undispatchable host | agent_workflows/run_dispatch.py:112-130; agent_workflows/agy_runipd.py:2207-2211 | `RUNNER_ADAPTERS` registers only `oc` and `agy_runipd` has no `as <profile>` clause, so an `agy` host chosen by `AW_HOST`, a state profile, or `PATH` resolves but cannot launch. | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | E-05 routes a resolved `agy` to the existing `adapter_for` refusal (exit 2, before any host starts); OQ-01 resolved; a Deferred row carries the adapter work to `xocj8i`. |
| PR-003 | MEDIUM | IN-SCOPE | R4 / Duplicated resolution | agent_workflows/run_dispatch.py:1-40 ("RESOLUTION IS NOT DUPLICATED HERE") | `dispatch_for_state` as drafted resolved model and variant, which the host driver resolves again. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 resolves only runner and profile name and forwards `as <profile>`; V-05 checks no `--model`/`--variant` is injected. |
| PR-004 | MEDIUM | IN-SCOPE | R4 / Contradicted contracts | agent_workflows/runner_profiles.py `resolve` docstring and refusal text; agent_workflows/run_dispatch.py docstring ("FAIL CLOSED, NEVER FALL BACK"); spec ogd2nv R-07 | The `PATH` fallback contradicts two shipped contracts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 keeps `resolve(generic=True)` and `aw run ipd` unchanged and updates the `resolve` text; E-05 updates the `run_dispatch.py` paragraph. |
| PR-005 | MEDIUM | IN-SCOPE | R3 / AW_HOST semantics | `grep -rn AW_HOST agent_workflows/` (no match); runner_profiles.py RunnerSpec aliases `opencode`, `antigravity` | The plan gave no validation rule for `AW_HOST` and no rule for a state profile on another host or an explicit `--as`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 canonicalizes through `canonical_runner`, refuses unknown values, treats empty as unset, applies a state profile only on a matching host, and lets `--as` decide its host. |
| PR-006 | MEDIUM | UNDER-SCOPE | R4 / Dangling state references | agent_workflows/runner_profiles.py:1393 (`remove_profile`), 1078 (`_validate_referential_integrity`) | `remove_profile` handles only per-runner default references, so removing a state-bound profile would leave a store that load refuses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 extends the explicit-decision rule (`clear_default`/`replacement`) to state bindings; E-04 (a) and V-01 test it. |
| PR-007 | MEDIUM | UNDER-SCOPE | R4 / Closed provenance set | agent_workflows/runner_profiles.py:717; tests/test_runner_profiles.py:2184, 2300 | New tiers had no provenance values, and tests fail any value outside the closed set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds `env-host`, `state-profile`, `path-detected`. |
| PR-008 | MEDIUM | UNDER-SCOPE | R4 / No CLI for default_runner | agent_workflows/runner_profile_wizard.py:627 (only setter) | The R-07 refusal must name a working fix, but no command sets `default_runner`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds `aw profile default-runner HOST` and `--clear`. |
| PR-009 | MEDIUM | IN-SCOPE | R4 / Runner choice in host-neutral leaves | agent_workflows/cli.py:20303 (`_guard_profile_runner`), 20321 (`_run_oc_profile`), 20472 (`profile_runner`) | Shared handlers read `profile_runner` and refuse cross-host operations; the plan did not say how each `aw profile` leaf picks a runner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states the rule per leaf and the `profile <verb>` result `command`. |
| PR-010 | LOW | IN-SCOPE | R4 / Name collision | agent_workflows/aw_profile.py (`aw-profile` console script) | `aw profile` and the run-trace `aw-profile` script share a name. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 adds a disambiguation sentence to `docs/runner-profiles.md`. |
| PR-011 | MEDIUM | IN-SCOPE | R1 / Test commands | `ls tests/test_run_dispatch*.py` (no match); tests/test_cli.py:930 (`RunDispatchHelpSurfaceTests`, module `pytestmark = pytest.mark.slow`) | Test globs named nonexistent files, the new test file had no core marker, and validation lacked the bare core tier and the sanitizer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests lists real files, `-o addopts=""` for `tests/test_cli.py`, bare `python3 -m pytest`, mypy, and `aw sanitize --agent`; E-04 requires `pytest.mark.core`. |
| PR-012 | LOW | IN-SCOPE | R2 / Qualified ids and gate | plan `## Spec / documentation sync`; .aw/system/workflows/plan-review/steps/s7-finalize.md (gate contract) | `AC-04` was unqualified, the gate was incomplete, and spec `ogd2nv` is still `to-review`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cited as `ogd2nv AC-04`; full gate added; Spec sync notes the spec status. |
| PR-013 | LOW | IN-SCOPE | R2 / Exit-code ownership | spec ogd2nv R-07 (exit 2); agent_workflows/run_dispatch.py `EXIT_CANNOT_RUN`, `dispatch()` | The plan did not say who maps a resolution error to exit 2. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 maps `RunnerProfileError`/`RunDispatchError` to `EXIT_CANNOT_RUN` (2), as `dispatch()` does. |
| PR-014 | HIGH | UNDER-SCOPE | R2 / Parser-leaf declarations | tests/test_command_surface_declarations.py (`test_zero_undeclared_parser_leaves`); agent_workflows/command_surface.py:2271-2345; tests/conformance_matrix.py:190-191, 466-475 | New `aw profile` leaves fail the declaration test unless declared, and positional leaves need conformance exemptions; neither path was in scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds the declarations and exemptions; both paths join Scope-Paths; V-03 runs the conformance tests. |
| PR-015 | MEDIUM | IN-SCOPE | R7 / Completion tables | tests/test_completion.py:443-461 (`aw oc profile <TAB>`) | Adding leaves to `aw oc profile` would break pinned completion expectations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 keeps `set-state`/`clear-state` only under `aw profile`; V-03 runs `tests/test_completion.py`. |
| PR-016 | MEDIUM | UNDER-SCOPE | R1 / Stale user docs | docs/runner-profiles.md:25 (`schema_version: 2` example), 265 (version paragraph); xocj8i Scope-Paths (only `docs/cli-output-contract.md`) | A version 3 store makes the user docs stale, and no sibling owns `docs/runner-profiles.md`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-06 updates `docs/runner-profiles.md`; path joins Scope-Paths; V-06 checks the diff. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where do per-state bindings live in the store? | A new top-level `states` map (state name to profile name), mirroring `roles`. | Nested under `defaults` (rejected: `defaults` holds per-field values, and a state binding may cross runners like `roles`). | runner_profiles.py `roles` precedent (DECISION 01-btot17-D2); unknown-key refusal at line 279; reversible before any store is written at version 3. | Yes |
| D-2 | How is `plan` stored? | An input alias for `graduate` only; the stored document holds canonical names and refuses a stored `plan` key. | Store both names (rejected: one state could carry two bindings). | Spec ogd2nv R-07 lists `graduate`/`plan` as one state. | Yes. |
| D-3 | Where does `PATH` host detection apply? | Only in `resolve_for_state` (verb-first commands); `resolve(generic=True)` and `aw run ipd` keep requiring `default_runner`. | Apply everywhere (rejected: changes shipped `aw run ipd` behavior that R-07 does not ask to change). | Spec ogd2nv R-07 scope; run_dispatch.py "FAIL CLOSED, NEVER FALL BACK". | Yes. |
| D-4 | What happens when the resolved host is `agy`? | Refuse through the existing `adapter_for` message, exit 2, before any host starts; adapter work deferred and carried by `xocj8i`. | Build an Antigravity adapter here (rejected: needs `agy_runipd.py` changes outside the Set's declared scope and changes `aw run ipd` for `default_runner: agy`). | run_dispatch.py:112-130; agy_runipd.py:2207-2211 ("the deferred dispatch-adapter work"); a later adapter turns the refusal into a launch. | Yes |
