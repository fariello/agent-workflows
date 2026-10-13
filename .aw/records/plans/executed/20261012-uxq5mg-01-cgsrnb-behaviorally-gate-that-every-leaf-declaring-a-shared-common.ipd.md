# IPD: Behaviorally gate that every leaf declaring a shared common-parent machine flag actually honors it

- Date: 2026-10-12
- Kind: child
- Concern: Nothing mechanically detects that a machine-output flag declared ONCE on the shared `common` argparse parent (`--json`, `--fields`) is accepted by a subcommand's parser yet silently not honored by its handler. That is the defect CLASS behind `xym8g8`, where `aw sanitize --json` exited 0 with zero stdout bytes, and it shipped because every existing surface test either inspects parser DECLARATION (`tests/test_fields_flag_reach.py`, `tests/test_verbose_flag_reach.py`) or drives only `--agent` (`tests/test_agent_surface_conformance.py`). Authoring swept the existing conformance universes at HEAD `85184f648` and measured the class is LIVE beyond `xym8g8`: five leaves emit no parseable JSON under `--json` (filed as `jfdk7p`) and nine leaves ignore `--fields` under `--agent` (filed as `aws1tg`). Any detector must encode `docs/cli-output-contract.md` Section 1.3's exemption for the verbatim-forwarding driver leaves (`aw oc run`, `aw agy run`, the `review`/`integrate` aliases, `aw run as`, `aw run ipd`, `aw agy sessions|view|exec`), where `--agent`/`--json` are deliberately NOT provided, or it fires on each of them.
- Scope: Add ONE new behavioral test module, `tests/test_shared_flag_honored.py`, that runs every leaf in the two existing conformance universes (`test_agent_surface_conformance.UNIVERSE` and `MUTATION_UNIVERSE`) as a real subprocess under (a) `--json`, asserting stdout parses as one JSON value, and (b) `--agent --fields cmd`, asserting no terminal record carries a key outside the preserved envelope plus `cmd`. It encodes the Section 1.3 exemption by DERIVATION (a leaf whose parser does not declare `--json` is outside the universe) and pins that derivation against the documented forwarded-leaf list so the exemption cannot silently widen. Measured-broken leaves are registered in a strict-xfail `KNOWN_BROKEN` ceiling, each citing a resolvable backlog id, so the gate turns red both when a NEW leaf regresses and when a broken leaf is FIXED without its entry being removed. Add one sentence to `docs/cli-output-contract.md` Section 1.3 naming the new gate. EXCLUDES fixing any of the measured-broken leaves (owned by `jfdk7p`, `aws1tg`, `k84fqu`), any `aw check` rule in `check_engine` (OQ-01), any `--verbose` reach assertion (OQ-02), and any change to the forwarded driver leaves.
- Scope-Paths: tests/test_shared_flag_honored.py, docs/cli-output-contract.md, .aw/records/plans/pending/20261012-uxq5mg-01-cgsrnb-behaviorally-gate-that-every-leaf-declaring-a-shared-common.ipd.md
- Scope-Exceeded: .aw/records/backlog/open/20261013-4y614a-01-4y614a-fields-flag-unhonored-in-parser-usage-refusal-for-.backlog.md (E-01 newly measured broken leaves filed in backlog)
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: uxq5mg
- Set: uxq5mg
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: cgsrnb

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: cgsrnb verified (set uxq5mg, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261013-4y614a-01-4y614a-fields-flag-unhonored-in-parser-usage-refusal-for-.backlog.md: E-01 newly measured broken leaves filed in backlog]
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `uxq5mg` (Work-Kind `chore`, no `Blocks-Release`, so none is inherited or invented). The item asks for a "check rule"; OQ-01 resolves from repository evidence that the right carrier is a CI-gating behavioral test, not an `aw check` rule, and records why. Authoring MEASURED the defect class rather than assuming it: a `--json` sweep and a `--agent --fields cmd` sweep across all 71 leaves of the two existing conformance universes at HEAD `85184f648` (F-03, F-04). The sweeps found the class is live on 13 distinct leaves beyond the `xym8g8` instance, which `wyy09f` already fixed (F-05). Those were filed as `jfdk7p` (`--json`, bug, `Blocks-Release: next`) and `aws1tg` (`--fields`, bug, `Blocks-Release: next`) rather than fixed here, because this plan is a `chore` detector and bundling nine handler fixes into it would hide release-gated bug work behind a non-gating item. The Section 1.3 exemption was verified against the parser: exactly the eleven documented forwarded leaves plus the hidden `__complete` declare no `--json` (F-02).

## Goal

Make the `xym8g8` defect class mechanically detectable: any `aw` leaf that accepts `--json` or `--fields` through the shared `common` parent but does not honor it fails CI, while the Section 1.3 verbatim-forwarding driver leaves are exempt by construction rather than by a list that can drift.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure, then build the gate

- [x] E-01 RE-DERIVE at execution HEAD, and record the HEAD sha, the four facts this plan rests on, rather than trusting the numbers written here. (1) The `--json` sweep: for every leaf in `tests.test_agent_surface_conformance.UNIVERSE` (with `tests.conformance_matrix.RUNNABLE_ARGV` extras, and the `scoped_repo_dir`-style minimal repo as cwd for `doctor` and `check`, exactly as `test_agent_surface_conformance` does) and every leaf in `MUTATION_UNIVERSE` (inside a `clone_isolated_project` of `build_installed_project_template`, exactly as `test_agent_surface_conformance_mutation` does), run `tests.conformance_matrix.run_cli(<leaf argv> + ["--json"])` and record which leaves' stdout fails `json.loads`. (2) The `--fields` sweep: same leaves with `["--agent", "--fields", "cmd"]`, recording every terminal record (`kind` in `result`/`summary`/`error`) carrying a key outside `agent_schema._PRESERVED_FIELDS | {"cmd"}`. (3) The exemption population: the set of canonical leaves (via `command_surface.discover_parser_leaves` semantics, aliases excluded) whose parser does NOT declare `--json`. (4) That `jfdk7p` and `aws1tg` still resolve via `aw find backlog <id6>`. COMPARE each to F-02, F-03 and F-04 and mark each CONFIRMED or CORRECTED. If a leaf in F-03/F-04 is now FIXED, it simply does not enter `KNOWN_BROKEN`; if a NEW broken leaf appears, file a backlog item for it (bug, `--blocks-release next`) and register it citing that id, never by widening this plan to fix it. If fact (3) now contains a leaf NOT in the Section 1.3 list (other than `__complete`), STOP and report: either the doc or the parser has drifted and that is a decision for the maintainer.
  - Depends on: none
  - Expected outcome: the execution HEAD sha, the two broken-leaf lists, the exemption population, and the backlog-resolution check, each marked CONFIRMED or CORRECTED against F-02..F-04, plus any newly filed backlog id.
  - Execution state: performed

- [x] E-02 CREATE `tests/test_shared_flag_honored.py` with the `--json` gate. Parametrize over the read universe and the mutation universe IMPORTED from `tests.test_agent_surface_conformance` (do NOT recompute or copy them: reusing the same universe and the same `EXEMPTION_REGISTRY`/`MUTATION_EXEMPTION_REGISTRY` subtraction is what keeps this gate's leaf set and the `--agent` sweep's leaf set from drifting apart), with the same fixtures and cwd rules (reuse `RUNNABLE_ARGV`, `run_cli`, `build_installed_project_template`, `clone_isolated_project`; a session-scoped minimal git repo for `doctor`/`check`). For each leaf, run the leaf with `--json` and assert `json.loads(res.stdout)` succeeds, with a failure message carrying the argv, exit code, the first 300 chars of stdout and of stderr. Assert ONLY parseability, not the payload shape: measured, some leaves (for example `ipd coverage`, `partition`, `config show`) emit a single-line agent record or a bare domain dict under `--json`, and normalizing that shape is a separate decision this plan does not make (see Deferred). Capture stdout and stderr SEPARATELY (`run_cli` already does); a combined-stream helper is the blind spot that let `xym8g8` ship (plan `wyy09f` F-06). Module docstring must name `xym8g8` as the motivating instance, cite Section 1.3 for the exemption, and state that the universe is imported, not recomputed, and why.
  - Depends on: E-01
  - Expected outcome: the new module exists, its `--json` cases run every imported leaf as a subprocess, and with no registry yet the E-01 `--json` broken leaves are exactly the failing cases (verbatim failure list recorded).
  - Execution state: performed

- [x] E-03 ADD the `--fields` gate to the same module. For each leaf in the same two universes run `--agent --fields cmd` and assert that every terminal record's key set is a subset of `agent_schema._PRESERVED_FIELDS | {"cmd"}`. IMPORT `_PRESERVED_FIELDS` rather than restating it, so a future addition to the preserved envelope (`docs/cli-output-contract.md` Section 6) cannot make this gate fire falsely. Guard against a vacuous pass: assert the leaf emitted at least one terminal record (an empty stdout under `--agent` is already a failure of `test_agent_surface_conformance`; here it must fail too, not pass because "no record has an extra key"). Skip `--fields` assertions on a leaf whose `--agent` output is registered `sanctioned_raw` in `EXEMPTION_REGISTRY`, which the imported universe already excludes; state that in a comment rather than re-deriving it.
  - Depends on: E-02
  - Expected outcome: `--fields` cases in the module, failing (before the registry exists) on exactly the E-01 `--fields` broken leaves with the unrequested keys printed, and a non-vacuity assertion present.
  - Execution state: performed

- [x] E-04 ENCODE the Section 1.3 exemption and the KNOWN_BROKEN ceiling. (a) EXEMPTION BY DERIVATION, PINNED: add a test that computes the canonical leaves whose parser declares no `--json` (aliases excluded by parser-object identity, the same rule as `command_surface.discover_parser_leaves`) and asserts that set EQUALS the Section 1.3 forwarded-leaf set (`run as`, `run ipd`, `oc runipd`, `oc review`, `oc integrate`, `agy runipd`, `agy review`, `agy integrate`, `agy sessions`, `agy view`, `agy exec`) plus the hidden `__complete` completion hook, each with a one-line reason. This is what makes the exemption a contract rather than a hole: a new leaf that forgets `parents=[common]` fails here instead of silently leaving both gates, and a forwarded leaf that starts declaring `--json` (which Section 1.3 says must not happen, because on `aw oc run start` a downstream `--agent` is an OpenCode agent NAME) fails here too. (b) KNOWN_BROKEN CEILING: a module-level dict mapping `(leaf, flag)` to a backlog id6, populated with exactly the E-01 broken set citing `jfdk7p` (`--json`) and `aws1tg` (`--fields`), applied as `pytest.mark.xfail(strict=True, reason=<id6>)` on the matching parametrized case, so a FIXED leaf whose entry was not removed turns the suite red (XPASS strict). Add a test that every KNOWN_BROKEN citation resolves via `run_cli(["find", "backlog", id6])` with exit 0 and the id6 in stdout, the same check `test_mutation_exemption_registry_contract` uses, and that every KNOWN_BROKEN key names a leaf actually present in the imported universes (no dead entries). State in a comment that the dict is a CEILING: adding an entry to silence a red case without a filed item is the prohibited failure mode, matching the `EXEMPTION_REGISTRY` rule in `tests/conformance_matrix.py`.
  - Depends on: E-03
  - Expected outcome: the exemption-pin test and the ceiling exist; the module now passes with every broken case reported as XFAIL; removing any one KNOWN_BROKEN entry makes that case FAIL; and each citation resolves.
  - Execution state: performed

- [x] E-05 PROVE THE GATE IS SENSITIVE to the exact regression it exists for and that its ceiling is strict. (1) MUTATION: through a restoring wrapper whose `finally` rewrites the original bytes, temporarily make `cli._run_check_local_leaks` drop the threaded context again (the `wyy09f` fix: pass `context=None` into `leak_sanitizer.main`), run ONLY the new module, confirm the `check-local-leaks` `--json` case FAILS (there is no separate `sanitize` case: `sanitize` is an ALIAS of `check-local-leaks`, sharing its parser object, so `command_surface.discover_parser_leaves` yields only `check-local-leaks`; measured at review). The edit must be ON DISK, because `run_cli` launches a subprocess importing the worktree package through `PYTHONPATH`, so an in-process monkeypatch cannot reach it. Measured at review: with the context dropped, `check-local-leaks --json` exits 0 with 0 stdout bytes (the `xym8g8` shape) while `--agent --fields cmd` still projects correctly, so only the `--json` case is expected to fail. Then restore and confirm the `sha256` of `agent_workflows/cli.py` equals the pre-mutation hash. (2) With a restoring wrapper on the test module, remove one KNOWN_BROKEN entry and confirm the matching case FAILS; then point one entry at a leaf that passes and confirm the strict xfail reports XPASS as a failure.
  - Depends on: E-04
  - Expected outcome: pasted evidence the gate fails under the reverted `xym8g8` fix and passes after byte-identical restoration, and that the ceiling fails both on a removed entry and on a stale entry.
  - Execution state: performed

- [x] E-06 DOCUMENT the gate. Add ONE sentence to `docs/cli-output-contract.md` Section 1.3, after the paragraph naming `tests/test_flag_surface_uniformity.py`, stating that `tests/test_shared_flag_honored.py` asserts every leaf declaring `--json`/`--fields` honors them observably and pins the forwarded-leaf exemption; write no em or en dashes (user-facing doc).
  - Depends on: E-05
  - Expected outcome: a one-sentence addition to Section 1.3 and no other doc change.
  - Execution state: performed

- [x] E-07 MEASURE the module and RUN the suite. Record the new module's wall time under the bare suite's own xdist settings (`python3 -m pytest tests/test_shared_flag_honored.py` with the configured `addopts`) and its serial time (`-o addopts="" -q`). Do NOT mark any part of the module `@pytest.mark.slow`: the `-m slow` step in `.github/workflows/tests.yml` is ADVISORY (`continue-on-error: true`), so a slow-marked gate would no longer gate anything. If the wall time is judged too costly, report the numbers to the maintainer instead of moving the gate out of the gating step. (For reference, review measured about 24s for both flags over the read universe and about 11s over the mutation universe with 8 worker threads.) Then run the full fast suite BARE as `python3 -m pytest`; for any failure, re-run the same selection at the base commit and report pre-existing versus caused.
  - Depends on: E-06
  - Expected outcome: both measured times recorded with no slow marker added, and a bare full-suite `N passed` summary with every failure attributed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `GUIDING_PRINCIPLES.md` P16: tests assert observable outcomes. Every assertion this plan adds parses real subprocess stdout. The one parser-structure assertion (E-04a, which leaves declare `--json`) follows the established precedent of `tests/test_fields_flag_reach.test_derived_reach_every_agent_leaf_accepts_fields` and asserts the exemption POPULATION against a documented contract list, not a count or a caller census.
- The shared machine flags are declared once on `cli._build_parser`'s `common` parent ("A shared parent so --no-color, --color, --agent, and --json work consistently across all subcommands `aw` itself handles"); `--fields` and `--verbose` sit on the same parent.
- The conformance universes are computed in `tests/test_agent_surface_conformance` (`compute_conformance_universe`, `compute_mutation_conformance_universe`) from `command_surface.get_all_declarations` minus `tests/conformance_matrix.EXEMPTION_REGISTRY` / `MUTATION_EXEMPTION_REGISTRY`. Those registries are documented as "A CEILING, NOT A CONVENIENCE" and require a filed item for `known_broken`; the KNOWN_BROKEN dict here follows the same rule.
- `tests/conformance_matrix.run_cli` runs `python -m agent_workflows` with `stdin=DEVNULL` and separately captured stdout/stderr, which is exactly the separation `wyy09f` F-06 identified as missing from the old combined-stream helper.
- `agent_schema.filter_record_fields` preserves `_PRESERVED_FIELDS` (`schema, kind, cmd, exit, outcome, complete, verified` plus `applied, total, emitted, omitted, next`) on every projection; Section 6 of the output contract documents the same set.
- Run the suite BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already deselects `slow` and `livecorpus`. `.github/workflows/tests.yml` runs `-m slow` as a separate step that is ADVISORY (`continue-on-error: true`), so only the fast suite gates CI.

## Findings

| Id | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | No existing test asserts a common-parent machine flag is HONORED; they assert it is DECLARED or test only `--agent`. | `tests/test_fields_flag_reach.test_derived_reach_every_agent_leaf_accepts_fields` and `tests/test_verbose_flag_reach.test_derived_reach_every_agent_leaf_accepts_verbose` check parser option strings; `test_agent_surface_conformance` appends only `["--agent"]`; `test_flag_surface_uniformity` covers color/interactivity only. `conformance_matrix.required_scenarios` lists a `json` scenario but `build_matrix` only produces declaration rows for it. | The gate is genuinely new coverage, not a duplicate. |
| F-02 | The Section 1.3 exemption population is exactly the documented forwarded leaves plus `__complete`. | Walking `cli._build_parser()` leaves (alias-deduped) for parsers lacking `--json` at HEAD `85184f648`: `run as, run ipd, oc runipd, oc review, oc integrate, agy runipd, agy review, agy integrate, agy sessions, agy view, agy exec, __complete`. Leaves using `argparse.REMAINDER` but declaring `--json` (`integration-lock`, `test`, `commit`, `pwatch`, `runners`) are NOT forwarded drivers and stay in scope. | Exemption can be derived from the parser and pinned to the doc list (E-04a); a REMAINDER heuristic would be wrong. |
| F-03 | `--json` is unhonored on five leaves in the two universes. | `run_cli(leaf + ["--json"])`, `json.loads(stdout)` fails: `config get interactive` rc 2 stdout `FAIL     Unknown config key 'interactive'...`; `config is interactive` rc 2 stdout `FAIL     Missing variable name...`; `upgrade-test env dummy` and `upgrade-test probe dummy` rc 2, 0 stdout bytes, stderr `error: not a sandbox`; `upgrade-test clean` (isolated project) rc 0 stdout `Nothing to clean.`. The other 42 read leaves and 23 mutation leaves parse. | Registered KNOWN_BROKEN citing `jfdk7p` (filed during authoring, bug, `Blocks-Release: next`). |
| F-04 | `--fields` is unhonored under `--agent` on nine leaves. | `run_cli(leaf + ["--agent","--fields","cmd"])`, terminal-record keys outside `_PRESERVED_FIELDS ∪ {cmd}`: `ipd coverage` [detail, summary]; `partition` [commands, cycles, shards, split_components]; `upgrade-test env`, `list`, `probe`, `sandboxes`, `clean` [findings]; `oc update-models` [findings]; `storage reattach` [findings]. | Registered KNOWN_BROKEN citing `aws1tg` (filed during authoring, bug, `Blocks-Release: next`). |
| F-05 | The motivating instance is already fixed and is the gate's sensitivity probe. | `check-local-leaks --json` parses (sweep row `ok check-local-leaks 0 457`); `cli._dispatch` now calls `_run_check_local_leaks(args, term, context=context)` (plan `wyy09f`, executed). | E-05 reverts that one argument to prove the gate catches the original regression. |
| F-06 | Two leaves sit outside both universes and are not swept. | Walking `--json`-declaring leaves minus both universes and both registries leaves `runs list` (`agent_record_kind="summary"`) and `path` (`raw_path`). | Recorded as under-scope; the gate deliberately reuses the existing universes rather than defining a third (see Scope check). |
| F-07 | An `aw check` rule is the wrong carrier for this property. | `check_engine.RULE_REGISTRY` rules validate RECORDS under `.aw/records/` and run in every managed target repo; the CLI parser surface is a property of this toolkit's own code, identical in every repo, with nothing repo-specific to check. CI already gates the test suite (`tests.yml` `python -m pytest tests/ -n auto`). | OQ-01 resolves to a test module. |

## Proposed changes (ordered, validatable)

1. Re-measure the sweeps, the exemption population, and the citation resolution at execution HEAD (E-01).
2. Add `tests/test_shared_flag_honored.py` with the `--json` parseability gate over the imported universes (E-02).
3. Add the `--fields` projection gate with a non-vacuity guard (E-03).
4. Pin the Section 1.3 exemption by derivation and add the strict-xfail KNOWN_BROKEN ceiling with resolvable citations (E-04).
5. Prove the gate catches the reverted `xym8g8` fix (E-05).
6. Add the one-sentence doc pointer (E-06).
7. Measure runtime without moving the gate out of the gating step, and run the bare suite (E-07).

## Deferred / out of scope (with reason)

- FIXING THE FIVE `--json` LEAVES. A bug population with its own release gate; fixing it inside a `chore` detector would hide gated work.
  - Carrier: jfdk7p
- FIXING THE NINE `--fields` LEAVES. Same reason.
  - Carrier: aws1tg
- THE `leak_sanitizer.main` `--fix` AND EXIT-2 BRANCHES EMITTING NOTHING UNDER `--agent`. Already filed; this gate's universe runs `check-local-leaks` (of which `sanitize` is an alias) without `--fix` so it neither depends on nor masks that defect.
  - Carrier: k84fqu
- NORMALIZING THE `--json` PAYLOAD SHAPE (some leaves emit a single-line agent record or a bare domain dict instead of a pretty `CommandResult`). Parseability is the property whose absence broke callers in `xym8g8`; shape uniformity is a separate contract decision no measured caller is blocked on, and asserting it would fail many leaves for a reason outside this item.
  - Carrier-Declined: No defect is measured and no caller is broken: every such leaf emits valid JSON, which is what Section 6 promises a "machine ingestion" consumer. Filing it would record a preference as an obligation (GUIDING_PRINCIPLES P6). If a maintainer wants shape uniformity it is a new contract decision, not deferred work from this item.
- AN `aw check` RULE. See F-07 and OQ-01.
  - Carrier-Declined: The backlog item's goal (detect the unreachable common-parent flag class, honoring the Section 1.3 exemption) is fully discharged by this plan's CI-gating test; an `aw check` rule would run in every managed repo over a property those repos cannot change. Nothing is owed.
- `--verbose` REACH. See OQ-02.
  - Carrier-Declined: There is no leaf-independent observable for `--verbose` (on a clean result it may legitimately change nothing), so a universal assertion would be either vacuous or false; `tests/test_verbose_flag_reach` already asserts its declaration reach and an end-to-end difference on a leaf where one exists. Nothing is owed.

## Scope check

- Over-scope: none. `tests/test_shared_flag_honored.py` is the deliverable; `docs/cli-output-contract.md` gets one pointer sentence so Section 1.3's enforcement paragraph names every test enforcing it. `tests/conformance_matrix.py` and `tests/test_agent_surface_conformance.py` are imported, not edited, and so are not in `Scope-Paths`. The backlog items `jfdk7p` and `aws1tg` were created during authoring and are not edited by execution.
- Under-scope: `runs list` and `path` (F-06) are outside both conformance universes and so are not swept; adding them means editing the shared universes, which belongs with whoever next extends `test_agent_surface_conformance`. Leaves in `EXEMPTION_REGISTRY`/`MUTATION_EXEMPTION_REGISTRY` are not swept for the same reason the `--agent` sweep skips them (each carries a typed reason). Positional/argument-dependent behavior is exercised only at each leaf's `RUNNABLE_ARGV`, so a leaf that honors `--json` on that path but drops it on another branch (the `k84fqu` shape) is not caught; that is a branch-coverage limit inherent to a per-leaf sweep.

## Required tests / validation

- `tests/test_shared_flag_honored.py` passing under the bare suite with every F-03/F-04 case reported XFAIL (strict) and every other case passing (E-02, E-03, E-04).
- The exemption-pin test asserting the no-`--json` leaf set equals the Section 1.3 list plus `__complete` (E-04).
- The citation-resolution and no-dead-entry tests for KNOWN_BROKEN (E-04).
- A mutation run reverting the `wyy09f` context threading showing the `check-local-leaks` `--json` case fails, with matching before/after `sha256` of `agent_workflows/cli.py` (E-05).
- The one-sentence Section 1.3 doc addition (E-06).
- The module's measured wall time with no slow marker, and a bare `python3 -m pytest` with its `N passed` summary pasted and any failure attributed against the base commit (E-07).

## Spec / documentation sync

No `.spec.md` is amended and none is in `Scope-Paths`: the behavior gated here is already specified by `docs/cli-output-contract.md` Sections 1.3 and 6, and this plan enforces that contract rather than changing it. `docs/cli-output-contract.md` is a user-facing doc and receives one sentence in Section 1.3 naming the new enforcing test beside `tests/test_flag_surface_uniformity.py`, so a reader of the contract can find what enforces it. If E-01 finds the parser's no-`--json` set has drifted from the Section 1.3 list, the executor STOPS and reports rather than editing either side.

## Open questions

### OQ-01: The item asks for a "check rule". Should this be an `aw check` rule in `check_engine` or a CI-gating test?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE toward a CI-gating behavioral test (F-07). `check_engine.RULE_REGISTRY` rules validate `.aw/records/` artifacts and are installed into every managed target repo, whose authors cannot change `aw`'s parser; a rule there would report a toolkit property to people with no power over it, and evaluating it requires running the CLI as subprocesses, which no existing `aw check` rule does. The precedent for CLI-surface invariants in this repo is tests (`test_agent_surface_conformance`, `test_flag_surface_uniformity`, `test_fields_flag_reach`), all gated by the `tests.yml` pytest step. The item's substantive requirement, that the detector encode the Section 1.3 exemption, is met by E-04a. The plan's title and Concern say "gate" for this reason.

### OQ-02: Should the gate also cover `--verbose`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED toward no. `--verbose` has no leaf-independent observable: `docs/cli-output-contract.md` Section 6 says it "includes full nested diagnostics, change details, and evidence dicts", which on a clean result with none of those may correctly change nothing, so a universal "output differs" assertion would be false and a weaker one vacuous. `tests/test_verbose_flag_reach.test_verbose_flag_end_to_end_observable_difference` already covers an end-to-end difference where one exists. The two flags this gate covers both have a universal observable (stdout parses; projected keys are bounded), which is what makes a sweep sound.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: The execution HEAD sha; the pasted `--json` broken-leaf list and `--fields` broken-leaf list (leaf, exit code, offending stdout prefix or unrequested keys) produced by the sweep `E-01` runs through `tests.conformance_matrix.run_cli`; the pasted exemption population; pasted `aw find backlog jfdk7p` and `aw find backlog aws1tg` output. Each of the four facts explicitly marked CONFIRMED or CORRECTED against F-02/F-03/F-04, with any newly filed backlog id named, or an explicit STOP report if fact (3) diverged from Section 1.3.
  - Observed evidence:
    Execution HEAD sha: `62dc7273d9fb3ac250d4f9d7eddae2d703ca06cc` (merge of lane a8yn86 to main).

    Fact (1) --json sweep (CONFIRMED against F-03):
    Five broken leaves in UNIVERSE (48 leaves) and MUTATION_UNIVERSE (31 leaves):
    - ('config get', 'read', 2, "FAIL     Unknown config key 'interactive'...", '', 'Expecting value: line 1 column 1 (char 0)')
    - ('config is', 'read', 2, 'FAIL     Missing variable name. Usage: aw config is <value> in <varname>\n', '', 'Expecting value: line 1 column 1 (char 0)')
    - ('upgrade-test env', 'read', 2, '', 'error: not a sandbox (no .aw-upgrade-test.json): .../dummy\n', 'Expecting value: line 1 column 1 (char 0)')
    - ('upgrade-test probe', 'read', 2, '', 'error: not a sandbox (no .aw-upgrade-test.json): .../dummy\n', 'Expecting value: line 1 column 1 (char 0)')
    - ('upgrade-test clean', 'mutation', 0, 'Nothing to clean.\n', '', 'Expecting value: line 1 column 1 (char 0)')

    Fact (2) --fields sweep (CORRECTED against F-04: F-04 confirmed on all 9 leaves, plus 4 newly measured broken leaves):
    F-04 broken leaves confirmed:
    - ('ipd coverage', 'read', 2, ['detail', 'summary'])
    - ('partition', 'read', 2, ['blocked_sets'])
    - ('upgrade-test env', 'read', 2, ['findings'])
    - ('upgrade-test list', 'read', 0, ['findings'])
    - ('upgrade-test probe', 'read', 2, ['findings'])
    - ('upgrade-test sandboxes', 'read', 0, ['findings'])
    - ('oc update-models', 'mutation', 2, ['findings'])
    - ('storage reattach', 'mutation', 1, ['findings'])
    - ('upgrade-test clean', 'mutation', 0, ['findings'])
    Newly measured broken leaves under --fields (from 91pjax resolution removing mutation exemptions, exposing usage refusal missing required arguments omitting --fields projection in parser.error):
    - ('ipd scaffold', 'mutation', 2, ['findings'])
    - ('research new', 'mutation', 2, ['findings'])
    - ('research new-comparison', 'mutation', 2, ['findings'])
    - ('storage move', 'mutation', 2, ['findings'])
    Filed in backlog as `4y614a` (bug, --blocks-release next).

    Fact (3) Exemption population (CONFIRMED against F-02 and Section 1.3):
    The 12 canonical leaves without --json declared:
    ['__complete', 'agy exec', 'agy integrate', 'agy review', 'agy runipd', 'agy sessions', 'agy view', 'oc integrate', 'oc review', 'oc runipd', 'run as', 'run ipd']
    Matches Section 1.3 forwarded leaves plus __complete exactly.

    Fact (4) Backlog item resolution (CONFIRMED):
    $ python3 -m agent_workflows find backlog jfdk7p
    ◕  open          jfdk7p  .aw/records/backlog/open/20261012-jfdk7p-01-jfdk7p-json-flag-unhonored-on-five-leaves.backlog.md
    $ python3 -m agent_workflows find backlog aws1tg
    ◕  open          aws1tg  .aw/records/backlog/open/20261012-aws1tg-01-aws1tg-fields-flag-unhonored-on-agent-leaves.backlog.md
    $ python3 -m agent_workflows find backlog 4y614a
    ◕  open          4y614a  .aw/records/backlog/open/20261013-4y614a-01-4y614a-fields-flag-unhonored-in-parser-usage-refusal-for-.backlog.md
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: The new file path and its module docstring (showing `xym8g8`, Section 1.3, and the imported-universe rationale); pasted pytest output of the `--json` cases BEFORE the KNOWN_BROKEN registry exists, whose failing set equals the V-01 `--json` broken list exactly (no more, no fewer); and proof every imported leaf is covered: the set of `--json` parametrize ids, printed in the same session, equals `set(UNIVERSE) | set(MUTATION_UNIVERSE)` (a set comparison re-derived at execution, not a count written here).
  - Observed evidence:
    File: `tests/test_shared_flag_honored.py`
    Module docstring:
    """Behavioral gate asserting that every leaf declaring a shared common-parent machine flag honors it.

    Motivated by xym8g8, where `aw sanitize --json` exited 0 with zero stdout bytes because
    subcommand handlers can accept `--json` or `--fields` declared on the shared `common`
    argparse parent yet silently fail to honor them in their handlers.

    Universes are IMPORTED directly from `tests.test_agent_surface_conformance` (both `UNIVERSE`
    and `MUTATION_UNIVERSE`), rather than recomputing or copying them. Reusing the exact same
    candidate sets and registry subtractions ensures that this gate and the `--agent` sweep
    remain synchronized and cannot drift apart.

    Exemptions are governed by docs/cli-output-contract.md Section 1.3: verbatim-forwarding
    host-driver leaves (`aw oc run`, `aw agy run`, review/integrate aliases, `aw run as`,
    `aw run ipd`, `aw agy sessions|view|exec`) declare no `--json` or `--agent` flags because
    downstream parsers own those flags. That exemption is derived from parser declaration
    and pinned against the Section 1.3 contract list.

    Broken leaves are registered in KNOWN_BROKEN with strict xfail, requiring a resolvable
    backlog item for every entry.
    """

    Pytest output of --json cases before KNOWN_BROKEN populated:
    ```
    =========================== short test summary info ============================
    FAILED tests/test_shared_flag_honored.py::test_json_flag_honored_mutation[upgrade-test clean]
    FAILED tests/test_shared_flag_honored.py::test_json_flag_honored_read[upgrade-test env]
    FAILED tests/test_shared_flag_honored.py::test_json_flag_honored_read[upgrade-test probe]
    FAILED tests/test_shared_flag_honored.py::test_json_flag_honored_read[config get]
    FAILED tests/test_shared_flag_honored.py::test_json_flag_honored_read[config is]
    5 failed, 74 passed in 25.92s
    ```
    Failing set equals V-01 --json broken leaves exactly.

    Parametrize IDs coverage check:
    ```python
    >>> read_ids = {p.id for p in _json_read_params()}
    >>> mut_ids = {p.id for p in _json_mutation_params()}
    >>> (read_ids | mut_ids) == (set(UNIVERSE) | set(MUTATION_UNIVERSE))
    True
    >>> (read_ids | mut_ids) ^ (set(UNIVERSE) | set(MUTATION_UNIVERSE))
    set()
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted pytest output of the `--fields` cases before the registry exists, whose failing set equals the V-01 `--fields` broken list exactly, with the unrequested keys visible in the failure messages; the source excerpt showing `_PRESERVED_FIELDS` is imported from `agent_schema` and the non-vacuity assertion (at least one terminal record) is present.
  - Observed evidence:
    Pytest output of --fields cases before KNOWN_BROKEN populated:
    ```
    =========================== short test summary info ============================
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_read[upgrade-test list]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[research new-comparison]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[storage reattach]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[ipd scaffold]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[oc update-models]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_read[ipd coverage]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[research new]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[upgrade-test clean]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_read[upgrade-test sandboxes]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_read[upgrade-test env]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_read[upgrade-test probe]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_mutation[storage move]
    FAILED tests/test_shared_flag_honored.py::test_fields_flag_honored_read[partition]
    13 failed, 66 passed in 35.66s
    ```
    Failure messages with unrequested keys visible:
    `AssertionError: Leaf 'storage move' terminal record #0 carries unrequested keys outside preserved envelope:`
    `  Unrequested keys: ['findings']`
    `AssertionError: Leaf 'partition' terminal record #0 carries unrequested keys outside preserved envelope:`
    `  Unrequested keys: ['blocked_sets']`

    Source excerpt from `tests/test_shared_flag_honored.py`:
    ```python
    from agent_workflows.agent_schema import _PRESERVED_FIELDS

    ...
    assert terminal_recs, (
        f"Leaf {leaf!r} emitted NO terminal record under --agent --fields cmd (vacuous pass guard)!\n"
        f"Argv: {full_argv}\n"
        f"Exit code: {res.returncode}\n"
        f"Stdout: {res.stdout[:300]!r}\n"
        f"Stderr: {res.stderr[:300]!r}"
    )

    allowed_keys = _PRESERVED_FIELDS | {"cmd"}
    for idx, r in enumerate(terminal_recs):
        unrequested = set(r.keys()) - allowed_keys
        assert not unrequested, (
            f"Leaf {leaf!r} terminal record #{idx} carries unrequested keys outside preserved envelope:\n"
            f"Unrequested keys: {sorted(unrequested)}\n"
            f"Record: {r}\n"
            f"Argv: {full_argv}\n"
            f"Exit code: {res.returncode}\n"
            f"Stderr: {res.stderr[:300]!r}"
        )
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted pytest output of the full module passing, with the XFAIL count equal to the size of KNOWN_BROKEN and every other case PASSED; the exemption-pin test passing with the asserted set printed or visible in source; the citation-resolution and no-dead-entry tests passing; and pasted output of a run with ONE KNOWN_BROKEN entry removed (in a scratch copy or via a restoring wrapper) showing that case FAILED.
  - Observed evidence:
    Full module pytest output with KNOWN_BROKEN populated:
    ```
    $ python3 -m pytest tests/test_shared_flag_honored.py
    bringing up nodes...
    ...x..x................................x...xx.......x....x.............. [ 44%]
    .x..............x..x....................xx....x.x.x...............x..... [ 89%]
    x.............x..                                                        [100%]
    143 passed, 18 xfailed in 105.80s (0:01:45)
    ```
    XFAIL count (18) equals len(KNOWN_BROKEN).

    Exemption-pin test (`test_exemption_population_pinned`), citation-resolution test (`test_known_broken_citations_resolve`), and no-dead-entry test (`test_known_broken_no_dead_entries`) all PASSED.

    Removed entry failure test:
    With `("config get", "--json"): "jfdk7p"` removed:
    ```
    $ python3 -m pytest tests/test_shared_flag_honored.py -k "test_json_flag_honored_read and config"
    bringing up nodes...
    F..x                                                                     [100%]
    =================================== FAILURES ===================================
    FAILED tests/test_shared_flag_honored.py::test_json_flag_honored_read[config get]
    1 failed, 2 passed, 1 xfailed in 6.05s
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted output of the mutation run (context threading reverted in the `cli._run_check_local_leaks` call path) showing the `check-local-leaks` `--json` case FAILED (empty stdout), then the restored run passing, with the pre-mutation and post-restoration `sha256` of `agent_workflows/cli.py` pasted and equal; pasted output showing a removed KNOWN_BROKEN entry FAILS its case and a stale entry reports a strict XPASS failure.
  - Observed evidence:
    Pre-mutation sha256 of `agent_workflows/cli.py`:
    `ff1c9b6f516f3e54c089bc464d8f83da54ec715dba472e9419eb4675b9b750f9`

    Mutation run with context=None in `cli._run_check_local_leaks`:
    ```
    FAILED tests/test_shared_flag_honored.py::test_json_flag_honored_read[check-local-leaks]
    AssertionError: Leaf 'check-local-leaks' failed to emit parseable JSON under --json!
    Argv: ['check-local-leaks', '--json']
    Exit code: 0
    Stdout prefix: ''
    Stderr prefix: 'No local leaks found. 4918 files checked.\n'
    Parse error: Expecting value: line 1 column 1 (char 0)
    ```
    Post-restoration sha256 of `agent_workflows/cli.py`:
    `ff1c9b6f516f3e54c089bc464d8f83da54ec715dba472e9419eb4675b9b750f9`
    Hashes match byte-identically.

    Strict ceiling probes:
    Removed entry (`config get --json`):
    `FAILED tests/test_shared_flag_honored.py::test_json_flag_honored_read[config get] (1 failed, 2 passed, 1 xfailed in 6.20s)`

    Stale entry on passing leaf (`status --json`):
    `FAILED tests/test_shared_flag_honored.py::test_json_flag_honored_read[status] - [XPASS(strict)] jfdk7p (1 failed, 3 passed in 14.81s)`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: The `git diff -- docs/cli-output-contract.md` hunk showing the single added sentence inside Section 1.3, and a grep of that hunk for em/en dashes returning nothing.
  - Observed evidence:
    $ git diff -- docs/cli-output-contract.md
    diff --git a/docs/cli-output-contract.md b/docs/cli-output-contract.md
    index 0bac89e7d..b84445777 100644
    --- a/docs/cli-output-contract.md
    +++ b/docs/cli-output-contract.md
    @@ -139,6 +139,7 @@ for. Use the driver's own flags there.
     execution and behavioral dispatch, verifying flag acceptance on parsed commands, pre-dispatch consumption on
     forwarded driver commands without unrecognized argument errors, exit 2 mutual exclusion on both operator and
     parser backstop paths, and `--` token passthrough.
    +`tests/test_shared_flag_honored.py` asserts every leaf declaring `--json`/`--fields` honors them observably and pins the forwarded-leaf exemption.

     ---

    Dash check on added hunk:
    Em dash present: False
    En dash present: False
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: The two measured wall times (xdist and serial) pasted from the runs; a grep of `tests/test_shared_flag_honored.py` for `mark.slow` returning nothing; and the bare `python3 -m pytest` summary line pasted verbatim with any failure attributed by a base-commit re-run.
  - Observed evidence:
    Wall times for `tests/test_shared_flag_honored.py`:
    - xdist (configured addopts): 143 passed, 18 xfailed in 131.50s (0:02:11)
    - serial (-o addopts="" -q): 143 passed, 18 xfailed in 445.14s (0:07:25)

    Grep for mark.slow in `tests/test_shared_flag_honored.py`:
    $ grep -n "mark.slow" tests/test_shared_flag_honored.py
    (empty, exit code 1)

    Bare full-suite pytest run:
    $ python3 -m pytest
    7885 passed, 4 skipped, 18 xfailed, 3 warnings in 498.00s (0:08:18)
    Zero failures.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Execution contract:

- Open questions: OQ-01 and OQ-02 are resolved; no blocking question remains.
- Scope fence: the declared `- Scope-Paths:` are `tests/test_shared_flag_honored.py`, `docs/cli-output-contract.md`, and this plan. This is a declaration, not a stop condition: an out-of-scope edit that proves necessary is made and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). A backlog item E-01 files for a NEW broken leaf is such an out-of-scope path and needs a `--scope-reason`. Do not fix any KNOWN_BROKEN leaf here: a newly measured broken leaf is filed and registered, not fixed. The E-01 STOP on an exemption-population drift is a maintainer decision about a public contract, not a scope question, and stays.
- Honesty: every `Observed evidence` MUST paste the ACTUAL runner output; never claim a pass that was not run. The E-05 mutation of `agent_workflows/cli.py` must be restored byte-identically (matching `sha256`) and never committed.
- Commit: path-scoped via `aw commit cgsrnb -- tests/test_shared_flag_honored.py docs/cli-output-contract.md <this plan>` (plus any justified out-of-scope path); never `git add -A`, never push.
- Lifecycle: start with `aw ipd begin cgsrnb --actor <you>`. The terminal transition to `executed/` happens only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with observed evidence. Under `aw oc run`/`aw agy run` the runner performs that transition, so the executor must NOT run `aw ipd finalize` itself; when executing by hand, run `aw ipd finalize cgsrnb --actor <you> --message <msg> --apply` (never a hand `git mv` to `executed/`).
