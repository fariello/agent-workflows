# IPD: Add a read-only aw releases readiness command that renders the GO / NO-GO report

- Date: 2026-10-12
- Kind: child
- Concern: THE RELEASE-READINESS REPORT HAS NO CALLER, SO NOBODY CAN SEE ITS VERDICT. Backlog `usggph`'s second claim reproduces at authoring HEAD `2600a93e3`: `git grep -n build_report -- '*.py' '.github' 'Makefile' '.pre-commit-config.yaml'` outside `tests/` matches only `agent_workflows/release_readiness.py` (the definition and its `__all__` entry) and an unrelated same-named function in `.aw/system/workflows/benchmark/tools/bench_env.py`. No `aw` leaf, CI step or hook builds the report (F-01). The module exists to give a GO / NO-GO verdict, and plans `dyiasf`, `wix4xe` and sibling `ttg9uz` have now made its gates truthful, yet the only way to see the verdict is a hand-typed `python3 -c` snippet. Today `docs/recovery.md` describes "the final release-readiness review" and gives no command to run it.
  A NAIVE COMMAND WOULD PRINT TWO MISLEADING ROWS, SO THE COMMAND MUST NOT GUESS ITS HUMAN INPUTS (F-02). `build_report` requires `suite_passed: bool` and takes `residual_risk_signed`/`residual_risk_signer`. The full suite is far too heavy to run inside a read command (bare suite 222s at authoring, F-04 of `ttg9uz`), and a residual-risk sign-off is a human attestation. Passing `suite_passed=False` when the operator supplied nothing would render `full_suite FAIL full suite RED`, which asserts a red suite that was never run. Passing `True` would be a forged GO. So the command takes both as explicit flags, and `gate_full_suite` must say "not supplied" rather than "RED" when it gets no result.
  WHY A `releases` LEAF AND WHY `followup`. `aw releases` already owns release records and `releases show` already reports what gates the next release (`cli.py` `p_releases`), so a read-only `releases readiness` sits beside it rather than adding a 69th top-level noun. Item `usggph` is `followup` with no `- Blocks-Release:`; both are preserved. Adding a public leaf is a public-contract decision, recorded as OQ-01 and settled by approving this plan.
- Scope: IN: (1) `release_readiness.gate_full_suite` accepts `suite_passed=None` and FAILS with a distinct "result not supplied" detail; (2) a `release_readiness.run_readiness(args)` handler that resolves and refuses a non-surveyable root like `releases.run_list`, builds the report with both subprocess gates live, prints `render()` for humans and an `aw.agent/v1` result for `--agent`/`--json`, and exits 0 on GO, 1 on NO-GO, 2 on cannot-run; (3) the `releases readiness` parser leaf, its dispatch in `cli.py`, its `CommandDeclaration`, and the two existing tests in `tests/test_releases_cli.py` that pin the `releases` subcommand set to exactly `{list, show, new}` (F-06); (4) a behavioral test file; (5) user docs and a CHANGELOG entry. OUT: running the report from release-review, CI or a hook (`uypgvi`); the inert `artifact_manifest` row (`3jkm7y`); clearing the live NO-GO causes (`5gzno3`, `r4a4ab`); any tag, publish, push or upload, which the module forbids by construction (`assert_no_release_action`).
- Scope-Paths: agent_workflows/release_readiness.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_releases_readiness_cli.py, tests/test_releases_cli.py, docs/recovery.md, docs/artifact-lifecycles.md, CHANGELOG.md
- Item-Dependencies: executed:ttg9uz
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: usggph
- Set: usggph
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: wa64wz

## Workflow history
- 2026-10-14 executed (aw agy run model=Gemini-4-Argon-High): aw agy run self-finalize: wa64wz verified (set usggph, attempt 1).
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed. Verified at 008c87f60: proposed CommandResult shape validates under agent_schema; build_report over a synthetic GO tree is GO in 1.0s and changes no file; two tests pin releases subcommands to {list, show, new}.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `usggph` in an isolated lane at HEAD `2600a93e3`. The "no caller" claim reproduced (F-01). Two findings shaped the design. FIRST, a command cannot supply the suite result or the residual-risk sign-off itself, and defaulting either one forges a row (F-02), so both become explicit flags and `gate_full_suite` gains a "not supplied" state. SECOND, the live report is NO-GO today for real reasons (F-03), so the command's exit 1 on this tree is correct. Depends on `ttg9uz` so the command never ships while three of its rows are vacuous.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give operators one read-only command, `aw releases readiness`, that prints the GO / NO-GO release-readiness report with every gate actually evaluated, returns an exit code a script can gate on, and never pretends to know a suite result or a sign-off it was not given.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure

- [x] E-01 Re-measure at the executing HEAD: confirm `ttg9uz` executed, `build_report` still has no production caller, and no `releases readiness` leaf exists.
  - Depends on: none
  - Expected outcome: a pasted transcript showing (a) `aw find plans ttg9uz` resolving under `.aw/records/plans/executed/` AND `release_readiness.gate_capability_freshness()` with no argument returning computed evidence (`claims_checked` present), proving the dependency's behavior actually landed; (b) the `git grep -n build_report` census above, still showing no caller; (c) `python3 -m agent_workflows releases readiness --help` failing as an unknown choice. IF (a) fails, STOP: mark this item `blocked`, edit nothing, report the unmet edge. IF (b) or (c) shows a caller or the leaf already exists, stop and reconcile.
  - Execution state: performed

### Task group 2: make the report honest about missing human inputs

- [x] E-02 Let `release_readiness.gate_full_suite` distinguish "no result supplied" from "suite red".
  - Depends on: E-01
  - Expected outcome: `gate_full_suite(suite_passed: Optional[bool], counts=None)`. `True` and `False` behave exactly as today (same `detail` strings `full suite green` / `full suite RED`). `None` returns `passed=False`, `detail="full suite result not supplied"`, `evidence` including `{"supplied": False}`. `build_report`'s `suite_passed` stays keyword-only and REQUIRED (no default), annotated `Optional[bool]`, so a library caller must still say something explicitly; the command passes `None` when the operator gave no flag. The existing `test_gate_full_suite_*` assertions must stay green unchanged.
  - Execution state: performed

### Task group 3: the command

- [x] E-03 Add `release_readiness.run_readiness(args)`, the handler for `aw releases readiness`.
  - Depends on: E-02
  - Expected outcome: resolve `repo_root = project_context.resolve_verb_repo_root(getattr(args, "dir", None))` and refuse through `project_context.nonsurveyable_root_refusal("releases readiness", ...)` with exit 2, copying `releases.run_list`'s refusal block (agent/json `cannot-run` record, human stderr). Then call `build_report(suite_passed=<True if --suite-passed, False if --suite-failed, else None>, residual_risk_signed=bool(signer), residual_risk_signer=signer or "", repo_root=repo_root, run_subprocess_gates=True)`. Human mode writes `report.render()` to stdout. `--agent`/`--json` emit a `result_types.CommandResult` with `command="releases readiness"`, `status="clean"` on GO or `"findings"` on NO-GO, `exit_code` 0 or 1, `summary` `"Verdict: GO"` or `"Verdict: NO-GO (<failing gates>)"`, one `Diagnostic(location=<gate name>, rule="readiness.<gate name>", detail=<gate detail>, severity="error")` per failing gate, and `data=report.to_dict()`. Any unexpected exception building the report is a cannot-run (exit 2) naming the exception type, never a GO. Imports stay inside the function, so `import agent_workflows.release_readiness` stays cheap. In human mode the cannot-run path writes one line naming the exception type to stderr and returns 2; `--agent`/`--json` emit a `cannot-run` record with `exit_code=2`. Human mode also writes ONE hint line to STDERR (stdout stays exactly `render()`) when `full_suite` reads `not supplied` or `residual_risk` reads `sign-off missing`, naming `--suite-passed`/`--suite-failed` and `--residual-risk-signer`, so a novice seeing NO-GO learns which rows are attestations they have not given rather than defects. No hint is printed for any other failing gate.
  - Execution state: performed

- [x] E-04 Register the `releases readiness` parser leaf and its dispatch in `cli.py`.
  - Depends on: E-03
  - Expected outcome: under `p_releases`'s `releases_sub`, a `readiness` subparser with `parents=[common]`, `--dir` defaulting to `argparse.SUPPRESS` (the same rule the sibling `list`/`show`/`new` leaves follow), a mutually exclusive `--suite-passed` / `--suite-failed` pair, and `--residual-risk-signer NAME`. Its help states that it is read-only, runs the leak scan and IPD lint live, never runs the test suite, never tags or publishes, and exits 0 GO / 1 NO-GO / 2 cannot-run. Add one `EXAMPLES` line to `p_releases`'s epilog. In the `args.command in ("releases", "release")` dispatch, route `releases_cmd == "readiness"` to `release_readiness.run_readiness(args)` before the bare-list fallback. The `release` alias must reach the same handler. Also make the surrounding text true: the comment above `p_releases` ("Subcommands are DELIBERATELY list/show/new only") keeps its no-`releases check` rule but names `readiness` and why it is not a second validator (it aggregates release gates; `aw check releases` validates release RECORDS); `p_releases`'s `help` and `description` mention `readiness`; its epilog "Exit codes" line adds `1 NO-GO (readiness)`. In `tests/test_releases_cli.py`, the two assertions that pin the set to `{"list", "show", "new"}` (`test_subcommands_are_exactly_list_show_new` and `ReleasesCompletionTests.test_static_scripts_carry_the_subcommands`) become `{"list", "show", "new", "readiness"}` (rename the first test to match); `test_no_releases_check_subcommand` stays unchanged and green.
  - Execution state: performed

- [x] E-05 Declare the leaf in `command_surface.COMMAND_INVENTORY`.
  - Depends on: E-04
  - Expected outcome: a `CommandDeclaration(command="releases readiness", command_class="check", human_recipe="check", agent_record_kind="result", mutation_gate="none", empty_error_renderer="renderer_boundary", legacy_flags=("--json", "--agent"), exit_contract=(0, 1, 2))`, placed in the existing releases-family block. `tests/test_command_surface_declarations.py`, `tests/test_conformance_matrix_structure.py`, `tests/test_agent_surface_conformance.py` and `tests/test_exit_contract_conformance.py` stay green with no exemption added. If one of them genuinely needs a `tests/conformance_matrix.py` entry, add it with `--scope-reason` and say why. Never add a `known_broken` entry to silence it. Expect `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[releases readiness]` to be newly COLLECTED (its universe is every `read`/`check` leaf with `agent_record_kind="result"`) and to run the leaf live at the repository root, where it exits 1 NO-GO with both subprocess gates live (about 5s); it must pass on record validity and exit parity, not on the verdict.
  - Execution state: performed

### Task group 4: prove it and document it

- [x] E-06 Add `tests/test_releases_readiness_cli.py` driving the command end to end over synthetic trees.
  - Depends on: E-05
  - Expected outcome: every arm is behavioral (no source reading, P16). Build trees with the GO-tree helper `ttg9uz` E-06 put in `tests/test_release_readiness_producers.py`, plus `git init -q` and an empty `.aw/records/plans/pending/` so both subprocess gates can pass (the shape `tests/test_release_readiness_child_pin.py` and plan `514wv3` F-04 use), with `GIT_CEILING_DIRECTORIES` set. Subprocess arms set `PYTHONPATH` to the repository root (as `tests/conformance_matrix.run_cli` and `tests/test_explicit_dir_non_project.py` do) and `stdin=DEVNULL`, since `cwd` is the synthetic tree. Arms: (a) `--suite-passed --residual-risk-signer qa` on the GO tree exits 0, human stdout contains `Verdict: GO`; (b) the same with no suite flag exits 1, the `full_suite` row reads `full suite result not supplied`, NOT `RED`, stdout contains no hint text, and stderr's hint names `--suite-passed`; (c) `--suite-failed` exits 1 with `full suite RED`; (d) no signer exits 1 with `residual_risk` failing; (e) adding one `"supported": true` to the tree's host matrix exits 1 with `capability_freshness` in the failing gates; (f) `--agent` emits a record that passes `agent_schema.validate_agent_record` with `cmd == "releases readiness"`, `exit` equal to the process exit code, and one diagnostic per failing gate; (g) `--json` output is `json.loads`-able and its `data.verdict` matches the exit code; (h) `--dir` pointing at a non-project directory exits 2; (i) `aw release readiness` (alias) gives byte-identical `--agent` output to `aw releases readiness` on the same tree; (j) the tree is byte-identical before and after a run (snapshot of every file, including under `.git/`), proving the command is read-only; (k) `aw releases --dir <tree> readiness` and `aw releases readiness --dir <tree>` resolve the same `dir` (in-process `parse_args`, the `SUPPRESS` rule); (l) `release_readiness.gate_full_suite(None)` directly returns `passed=False`, `detail == "full suite result not supplied"`, `evidence["supplied"] is False`. Run the CLI as a subprocess (`python3 -m agent_workflows ...`) for at least (a), (f) and (h), so parser, dispatch and exit code are all exercised.
  - Execution state: performed

- [x] E-07 Document the command and record it in the CHANGELOG, then run the bare suite.
  - Depends on: E-06
  - Expected outcome: `docs/recovery.md` "Release readiness (decision only)" replaces its stale paragraph (which still says the suite was deleted and points at `3rmvik`) with how to run `aw releases readiness`, what each flag attests, the exit codes, and that `artifact_manifest` is not yet computed (backlog `3jkm7y`). `docs/artifact-lifecycles.md` section 6's command block gains the `aw releases readiness` line. `CHANGELOG.md` gains an entry under the pending release's existing heading. All three are user-facing: no em or en dashes (AGENTS.md); `docs_check.check_docs_dir(Path("docs"))` reports no new finding. Then bare `python3 -m pytest`, failures compared by name against a base-commit baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or quoted string, never a bare line number (`IPD-C801`).
- Read-class verbs resolve root with `project_context.resolve_verb_repo_root` and refuse a non-surveyable root with `nonsurveyable_root_refusal`, exit 2 (`releases.run_list`, `releases.run_show`; the "anti-greenwashing invariant" in `releases._release_read_repo_root`'s docstring).
- Every parser leaf needs a `CommandDeclaration`, or `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` fails. Exemptions are a ceiling, not a convenience (`tests/conformance_matrix.py` banner "THE REGISTRY IS A CEILING").
- Exit codes: 0 clean, 1 findings/domain failure, 2 usage/cannot-run (`result_types.CommandResult.exit_code` comment). `aw workflow check-generated` uses the same `(0, 1, 2)` contract.
- `release_readiness` must never tag, publish, deploy or push (module docstring; `assert_no_release_action`; `RELEASING.md`). The command is read-only.
- User-facing prose carries no em or en dashes (AGENTS.md execution contract).
- Tests assert outcomes (AGENTS.md; P16). Synthetic trees set `GIT_CEILING_DIRECTORIES` (plan `dyiasf` PR-002).
- The suite is run BARE (`python3 -m pytest`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `build_report` has no production caller and no leaf renders the report. | `git grep -n build_report -- '*.py' '.github' 'Makefile' '.pre-commit-config.yaml'` minus `tests/` at `2600a93e3`: `agent_workflows/release_readiness.py` (def, `__all__`) and `.aw/system/workflows/benchmark/tools/bench_env.py` (an unrelated function of the same name). `aw releases --help` lists only `{list,show,new}`. |
| F-02 | The two human inputs cannot be defaulted honestly. | `gate_full_suite(False)` gives `detail="full suite RED"` and `gate_full_suite(True)` gives `full suite green`; there is no "not run" state. `gate_residual_risk` already fails closed on a missing signer (`residual-risk sign-off missing`), so only the suite gate needs the new state. |
| F-03 | On the live tree the report is NO-GO for real reasons, so exit 1 is the correct behavior here. | `build_report(suite_passed=True, run_subprocess_gates=False)` -> NO-GO on `residual_risk`; `gate_ipd_lint()` -> `passed=False` (`ipd lint exit 1`, the `r4a4ab` population); after `ttg9uz`, `capability_freshness` also fails on 19 unproven claims (`ttg9uz` F-05). `gate_leak_scan()` passes (1.9s); `gate_ipd_lint()` takes 2.4s. |
| F-04 | `docs/recovery.md` is stale about this module. | Its "Release readiness (decision only)" section says "The full release-readiness test suite was deleted in commit 19313eed ... (tracked in backlog item 3rmvik)"; plan `dyiasf` restored that suite and it now passes (`42 passed` across the three release-readiness test files). |
| F-05 | The `releases` family is the natural home and its leaves share a `--dir` rule. | `cli.py` comment above `p_releases.add_argument("--dir", ...)`: subparsers "default their own `--dir` to argparse.SUPPRESS" so `aw releases --dir X` and `aw releases list --dir X` resolve the same root. |
| F-06 | Two existing tests pin the `releases` subcommand set, so adding a leaf breaks them unless they are updated. | `tests/test_releases_cli.py` `test_subcommands_are_exactly_list_show_new` asserts `set(sub.choices) == {"list", "show", "new"}`; `ReleasesCompletionTests.test_static_scripts_carry_the_subcommands` asserts the same set from `completion.introspect_cli_tree`. The `cli.py` comment above `p_releases` reads "Subcommands are DELIBERATELY list/show/new only - there is no `releases check`". Found at review (PR-001). |
| F-07 | The proposed agent record shape is valid and the report is read-only, both demonstrated at review. | At `008c87f60`: a `CommandResult(command="releases readiness", status="findings", exit_code=1, diagnostics=[Diagnostic(location="residual_risk", rule="readiness.residual_risk", ...)], data=report.to_dict())` renders through `AgentRenderer` to a record for which `agent_schema.validate_agent_record` returns `[]`; `JsonRenderer` output carries `data.verdict` and no temp path. `build_report(suite_passed=True, residual_risk_signed=True, residual_risk_signer="qa", repo_root=<git-init tree with .aw/records/plans/pending, docs/, CHANGELOG.md, .aw/system/VERSION>)` is GO in 1.0s with both subprocess gates live, and a SHA-1 snapshot of every file in the tree, `.git/` included, is unchanged. |

## Proposed changes (ordered, validatable)

1. E-01 confirms the dependency landed and the gap still exists.
2. E-02 gives `gate_full_suite` a "not supplied" state.
3. E-03 adds the handler; E-04 the parser leaf, dispatch, family help text and the two pinned subcommand-set tests; E-05 the declaration.
4. E-06 adds the end-to-end behavioral tests.
5. E-07 updates the user docs and CHANGELOG and runs the bare suite.

## Deferred / out of scope (with reason)

- Running the report as a step in release-review Section 8, in CI or in a hook, and deciding how a standing NO-GO is treated there. That is a process decision about what gates a release; this plan only makes the report runnable.
  - Carrier: uypgvi
- The `artifact_manifest` row stays vacuous (`manifest_present`/`manifest_consistent` default `True`). The command does not take flags for it, because a flag would only move the vacuous assertion to the operator. The docs say plainly that the row is not yet computed.
  - Carrier: 3jkm7y
- The live NO-GO causes: the unproven host-matrix booleans and the live `ipd_lint` red.
  - Carrier: 5gzno3
- The live `ipd_lint` red is owned by the existing coverage item for that gate.
  - Carrier: r4a4ab

## Scope check

- Over-scope: none. `release_readiness.py` gets the suite-gate state and the handler; `cli.py` and `command_surface.py` are the minimum to add a leaf; `tests/test_releases_cli.py` only because two of its assertions pin the old subcommand set (F-06); one new test file; two docs and the CHANGELOG describe the new surface.
- Under-scope: `tests/conformance_matrix.py` is not declared, on the expectation that the derived matrix covers a `check` leaf without an entry; E-05 says how to proceed if that turns out false.

## Required tests / validation

`tests/test_releases_readiness_cli.py`, `tests/test_releases_cli.py`, the four release-readiness test files, and the command-surface and conformance files named in E-05, each under `-o addopts=""`. Then bare `python3 -m pytest`, failures compared by name against a base-commit baseline.

## Spec / documentation sync

No `.spec.md` governs `aw releases` or `release_readiness` (`git grep -l "releases show" .aw/records/specs` is empty), so none is amended. User docs `docs/recovery.md` and `docs/artifact-lifecycles.md` and `CHANGELOG.md` are updated in E-07, because a new user-visible command must be discoverable where users already read about releases and the readiness review.

## Open questions

### OQ-01: is `aw releases readiness` the right public surface, with GO=0 / NO-GO=1 / cannot-run=2?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: RESOLVED by the reviewer from repository evidence (review record D-1), for the maintainer to ratify by approving or amend before approval. The repository's evidence points here (F-05: `releases` owns release records and already reports what gates the next release; `(0, 1, 2)` is the shared check-class contract). The name of a new public leaf is still a public-contract choice and belongs to the maintainer. It is NOT blocking because approving this plan IS that ruling. A different name or placement changes only E-04 and E-05, and the reviewer can amend those in place before approval.
- Carrier-Declined: approval of this plan is the decision point; no separate durable record is needed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the HEAD sha, `aw find plans ttg9uz` output under `executed/`, the no-argument `gate_capability_freshness()` result showing `claims_checked`, the `git grep -n build_report` census, and the `releases readiness --help` invalid-choice error. Any of these contradicting E-01 makes this FAIL.
  - Observed evidence:
    ```text
    $ git rev-parse HEAD
    c85687c5ea0ea9db1e806f002850a8eb907134d2
    $ PYTHONPATH=. aw find plans ttg9uz
    ✓  executed      ttg9uz  usggph          .aw/records/plans/executed/20261012-usggph-01-ttg9uz-give-the-generated-drift-workflow-disposition-and-capability.ipd.md
    $ python3 -c "from agent_workflows import release_readiness as r; g = r.gate_capability_freshness(); print(g.name, g.passed, g.detail, sorted(g.evidence.keys()), g.evidence.get('claims_checked'))"
    capability_freshness False 19 stale claim(s) ['claims_checked', 'stale_claims'] 19
    $ git grep -n build_report -- '*.py' '.github' 'Makefile' '.pre-commit-config.yaml' ':!tests/'
    .aw/system/workflows/benchmark/tools/bench_env.py:754:def build_report(
    .aw/system/workflows/benchmark/tools/bench_env.py:847:    rep = build_report(repo, paths, args.disk_probe, args.probe_mb, warm, args.scrub)
    agent_workflows/release_readiness.py:631:def build_report(
    agent_workflows/release_readiness.py:694:    "build_report",
    $ python3 -m agent_workflows releases readiness --help
    usage: agent-workflows releases [-h] [--no-color | --color] [--no-interactive |
                                    --interactive] [--agent] [--json]
                                    [--fields FIELDS] [--verbose] [--dir DIR]
                                    {list,show,new} ...
    agent-workflows releases: error: argument releases_command: invalid choice: 'readiness' (choose from 'list', 'show', 'new')
    Next  aw releases --help
    exit=2
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff` hunk for `gate_full_suite` and `build_report`'s `suite_passed` annotation. Paste a driven probe printing `gate_full_suite(True)`, `gate_full_suite(False)` and `gate_full_suite(None)` (name, passed, detail, evidence), the last showing `full suite result not supplied`. Paste `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py -k full_suite` green with no assertion edited (`git diff <execution-base> -- tests/test_release_readiness.py` empty; the base already contains `ttg9uz`'s fixture growth).
  - Observed evidence:
    ```diff
    @@ -224,13 +224,24 @@ def gate_ipd_lint(repo_root: Optional[Path] = None) -> GateResult:
     def gate_full_suite(
    -    suite_passed: bool, counts: Optional[Dict[str, int]] = None
    +    suite_passed: Optional[bool], counts: Optional[Dict[str, int]] = None
     ) -> GateResult:
         """The full test suite gate.

         The suite (``make test``) is too heavy to re-run inside a unit test, so the aggregator
    -    accepts the harness/CI result. ``suite_passed`` MUST come from a real run.
    +    accepts the harness/CI result. ``suite_passed`` MUST come from a real run. When
    +    ``suite_passed`` is None, fails closed with "full suite result not supplied" rather
    +    than claiming a red suite that was never run.
         """
    +    if suite_passed is None:
    +        ev: Dict[str, Any] = dict(counts or {})
    +        ev["supplied"] = False
    +        return GateResult(
    +            name="full_suite",
    +            passed=False,
    +            detail="full suite result not supplied",
    +            evidence=ev,
    +        )
         return GateResult(
             name="full_suite",
             passed=bool(suite_passed),
    @@ -630,7 +641,7 @@ def aggregate(gates: Sequence[GateResult]) -> ReleaseReadinessReport:
     def build_report(
         *,
    -    suite_passed: bool,
    +    suite_passed: Optional[bool],
         suite_counts: Optional[Dict[str, int]] = None,
    ```
    ```text
    $ python3 -c "from agent_workflows import release_readiness as r
    for val in (True, False, None):
        g = r.gate_full_suite(val)
        print(val, '->', g.name, g.passed, repr(g.detail), g.evidence)"
    True -> full_suite True 'full suite green' {}
    False -> full_suite False 'full suite RED' {}
    None -> full_suite False 'full suite result not supplied' {'supplied': False}
    $ python3 -m pytest -o addopts="" -q tests/test_release_readiness.py -k full_suite
    ..                                                                       [100%]
    2 passed, 33 deselected in 0.26s
    $ git diff c85687c5ea0ea9db1e806f002850a8eb907134d2 -- tests/test_release_readiness.py
    (empty)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `git diff` of `run_readiness`. Paste a driven call (code path: `release_readiness.run_readiness`, created by E-03, invoked with an `argparse.Namespace`) over a GO tree and over the same tree without a signer, showing the human render, return codes 0 and 1, and the `--agent` record's `status`, `exit_code`, `summary` and diagnostics.
  - Observed evidence:
    ```diff
    +def run_readiness(args: Any) -> int:
    +    """``aw releases readiness``: render the read-only GO / NO-GO release-readiness report."""
    +    import sys
    +
    +    from agent_workflows.project_context import (
    +        nonsurveyable_root_refusal,
    +        resolve_verb_repo_root,
    +    )
    +    from agent_workflows.renderers import get_renderer
    +    from agent_workflows.result_types import (
    +        CommandResult,
    +        Diagnostic,
    +        NextAction,
    +        select_output,
    +    )
    +
    +    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    +    ctx = select_output(args)
    +    explicit_dir = bool(getattr(args, "dir", None))
    +    refusal = nonsurveyable_root_refusal(
    +        "releases readiness", repo_root, explicit_dir=explicit_dir
    +    )
    +    if not refusal.may_proceed:
    +        if ctx.is_agent or ctx.is_json:
    +            res = CommandResult(
    +                command="releases readiness",
    +                status="cannot-run",
    +                exit_code=2,
    +                summary=refusal.summary,
    +                next_actions=(
    +                    [
    +                        NextAction(
    +                            command=refusal.next_action_command,
    +                            description=refusal.next_action_description,
    +                        )
    +                    ]
    +                    if refusal.next_action is not None
    +                    else []
    +                ),
    +            )
    +            return get_renderer(ctx).emit(res, ctx)
    +        sys.stderr.write((refusal.human_message or "") + "\n")
    +        return 2
    +
    +    if getattr(args, "suite_passed", False):
    +        suite_passed: Optional[bool] = True
    +    elif getattr(args, "suite_failed", False):
    +        suite_passed = False
    +    else:
    +        suite_passed = None
    +
    +    raw_signer = getattr(args, "residual_risk_signer", None)
    +    signer = str(raw_signer).strip() if raw_signer else ""
    +
    +    try:
    +        report = build_report(
    +            suite_passed=suite_passed,
    +            residual_risk_signed=bool(signer),
    +            residual_risk_signer=signer or "",
    +            repo_root=repo_root,
    +            run_subprocess_gates=True,
    +        )
    +    except Exception as exc:
    +        msg = (
    +            f"aw releases readiness: could not build readiness report: "
    +            f"{type(exc).__name__}"
    +        )
    +        if ctx.is_agent or ctx.is_json:
    +            res = CommandResult(
    +                command="releases readiness",
    +                status="cannot-run",
    +                exit_code=2,
    +                summary=msg,
    +                verified=False,
    +                complete=False,
    +            )
    +            return get_renderer(ctx).emit(res, ctx)
    +        sys.stderr.write(msg + "\n")
    +        return 2
    +
    +    is_go = report.is_go
    +    exit_code = 0 if is_go else 1
    +    failing = report.failing_gates()
    +    summary = (
    +        "Verdict: GO"
    +        if is_go
    +        else f"Verdict: NO-GO ({', '.join(failing)})"
    +    )
    +
    +    if ctx.is_agent or ctx.is_json:
    +        diagnostics = [
    +            Diagnostic(
    +                location=g.name,
    +                rule=f"readiness.{g.name}",
    +                detail=g.detail,
    +                severity="error",
    +            )
    +            for g in report.gates
    +            if not g.passed
    +        ]
    +        res = CommandResult(
    +            command="releases readiness",
    +            status="clean" if is_go else "findings",
    +            exit_code=exit_code,
    +            summary=summary,
    +            diagnostics=diagnostics,
    +            data=report.to_dict(),
    +        )
    +        return get_renderer(ctx).emit(res, ctx)
    +
    +    sys.stdout.write(report.render() + "\n")
    +    needs_hint = any(
    +        (g.name == "full_suite" and "not supplied" in g.detail)
    +        or (g.name == "residual_risk" and "sign-off missing" in g.detail)
    +        for g in report.gates
    +        if not g.passed
    +    )
    +    if needs_hint:
    +        sys.stderr.write(
    +            "Hint: pass --suite-passed or --suite-failed for full_suite, and "
    +            "--residual-risk-signer <name> for residual_risk.\n"
    +        )
    +    return exit_code
    ```
    ```text
    === GO HUMAN rc=0 stderr='' ===
    # Release Readiness Report

    Verdict: GO

    | Gate | Result | Detail |
    |---|---|---|
    | full_suite | PASS | full suite green |
    | leak_scan | PASS | aw sanitize --agent exit 0 |
    | ipd_lint | PASS | aw ipd lint --all --agent exit 0 |
    | generated_drift | PASS | no canonical workflow packages to check |
    | docs_checks | PASS | docs checks pass |
    | workflow_disposition | PASS | all workflows dispositioned |
    | capability_freshness | PASS | no stale capability claims |
    | benchmark_thresholds | PASS | benchmark release invariants hold |
    | changelog_versioning | PASS | changelog entry + resolvable version present |
    | artifact_manifest | PASS | artifact manifest present and consistent |
    | residual_risk | PASS | residual risk signed off by qa |
    === GO AGENT rc=0 ===
    {"schema":"aw.agent/v1","kind":"result","cmd":"releases readiness","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"next":null}
    === GO JSON rc=0 === {'status': 'clean', 'exit_code': 0, 'summary': 'Verdict: GO', 'diagnostics': []}
    === NO_SIGNER HUMAN rc=1 stderr='Hint: pass --suite-passed or --suite-failed for full_suite, and --residual-risk-signer <name> for residual_risk.' ===
    # Release Readiness Report

    Verdict: NO-GO

    | Gate | Result | Detail |
    |---|---|---|
    | full_suite | PASS | full suite green |
    | leak_scan | PASS | aw sanitize --agent exit 0 |
    | ipd_lint | PASS | aw ipd lint --all --agent exit 0 |
    | generated_drift | PASS | no canonical workflow packages to check |
    | docs_checks | PASS | docs checks pass |
    | workflow_disposition | PASS | all workflows dispositioned |
    | capability_freshness | PASS | no stale capability claims |
    | benchmark_thresholds | PASS | benchmark release invariants hold |
    | changelog_versioning | PASS | changelog entry + resolvable version present |
    | artifact_manifest | PASS | artifact manifest present and consistent |
    | residual_risk | FAIL | residual-risk sign-off missing |

    Failing gates: residual_risk
    === NO_SIGNER AGENT rc=1 ===
    {"schema":"aw.agent/v1","kind":"result","cmd":"releases readiness","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":1,"diagnostics":[{"location":"residual_risk","rule":"readiness.residual_risk","detail":"residual-risk sign-off missing","severity":"error"}],"next":null}
    === NO_SIGNER JSON rc=1 === {'status': 'findings', 'exit_code': 1, 'summary': 'Verdict: NO-GO (residual_risk)', 'diagnostics': [{'location': 'residual_risk', 'rule': 'readiness.residual_risk', 'detail': 'residual-risk sign-off missing', 'severity': 'error'}]}
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m agent_workflows releases readiness --help` and `python3 -m agent_workflows releases --help` (showing `readiness` among the choices and the new EXAMPLES line). Paste `python3 -m agent_workflows releases readiness --suite-passed --suite-failed` exiting 2 (mutually exclusive). Paste `python3 -m agent_workflows releases readiness --agent; echo exit=$?` run at the repository root (code path: E-04 dispatch into E-03), showing a NO-GO record and `exit=1`, with the failing gates listed. Paste `python3 -m pytest -o addopts="" -q tests/test_releases_cli.py` green, plus `git diff tests/test_releases_cli.py` showing only the two pinned sets (and the one test name) changed.
  - Observed evidence:
    ```text
    $ python3 -m agent_workflows releases readiness --help
    usage: agent-workflows releases readiness [-h] [--no-color | --color]
                                              [--no-interactive | --interactive]
                                              [--agent] [--json] [--fields FIELDS]
                                              [--verbose] [--dir DIR]
                                              [--suite-passed | --suite-failed]
                                              [--residual-risk-signer NAME]

    Render the read-only GO / NO-GO release-readiness report across every release
    gate. Runs the leak scan and IPD lint live, never runs the test suite, never
    tags or publishes, and exits 0 GO / 1 NO-GO / 2 cannot-run.

    options:
      -h, --help            show this help message and exit
      --no-color            Disable ANSI color (also honored via NO_COLOR).
      --color               Force ANSI color on even when stdout is not a terminal
                            (beats NO_COLOR).
      --no-interactive      Disable interactive prompting (declining confirmations
                            and taking non-interactive defaults).
      --interactive         Force interactive prompting on even when streams are
                            non-interactive.
      --agent               Machine-readable output (aw.agent/v1 JSONL).
      --json                Emit full structured JSON representation.
      --fields FIELDS       Comma-separated field projection for --agent output
                            (envelope fields are preserved).
      --verbose             Include full nested diagnostics, change details, and
                            evidence dictionaries.
      --dir DIR             Repo root (default: current directory).
      --suite-passed        Attest that the full test suite passed in a real run.
      --suite-failed        Attest that the full test suite failed in a real run.
      --residual-risk-signer NAME
                            Signer name attesting the residual-risk sign-off.
    $ python3 -m agent_workflows releases --help
    usage: agent-workflows releases [-h] [--no-color | --color] [--no-interactive |
                                    --interactive] [--agent] [--json]
                                    [--fields FIELDS] [--verbose] [--dir DIR]
                                    {list,show,new,readiness} ...

    Owner verbs for the release records in .aw/records/releases/ (the ship-gate anchors that 'Blocks-Release: <id6|next>' resolves against): 'list' tabulates every release record, 'show' details one release plus the LIVE items gating it (the same blocker set 'aw attention' reports), 'new' scaffolds a conformant record (preview by default), and 'readiness' renders the read-only GO / NO-GO release-readiness report. Validate release records with 'aw check releases'.

    positional arguments:
      {list,show,new,readiness}
        list                List every release record (the default for a bare 'aw
                            releases').
        new                 Create a release record (dry-run by default; --apply to
                            write).
        readiness           Render the read-only GO / NO-GO release-readiness report
                            (runs leak scan and IPD lint live, never runs the test
                            suite, never tags or publishes; exits 0 GO / 1 NO-GO / 2
                            cannot-run).
        show                Show one release + its release-blockers (selector
                            defaults to 'next').

    EXAMPLES
      aw releases                  # list every release record (default)
      aw releases show next        # the planned release + everything gating it
      aw releases new --version 2.1.0 --summary "why" --apply
      aw releases readiness --suite-passed --residual-risk-signer qa

    OUTPUT & EXITS
      Exit codes: 0 clean, 1 NO-GO (readiness), 2 cannot-run/usage error (e.g. an unresolvable selector).
      Agent mode: --agent emits aw.agent/v1 JSONL.
    $ python3 -m agent_workflows releases readiness --suite-passed --suite-failed; echo exit=$?
    agent-workflows releases readiness: error: argument --suite-failed: not allowed with argument --suite-passed
    Next  aw releases readiness --help
    exit=2
    $ python3 -m agent_workflows releases readiness --agent; echo exit=$?
    {"schema":"aw.agent/v1","kind":"result","cmd":"releases readiness","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":3,"diagnostics":[{"location":"full_suite","rule":"readiness.full_suite"},{"location":"capability_freshness","rule":"readiness.capability_freshness"},{"location":"residual_risk","rule":"readiness.residual_risk"}],"next":null}
    exit=1
    $ python3 -m pytest -o addopts="" -q tests/test_releases_cli.py
    .....................................                                    [100%]
    37 passed in 3.18s
    ```
    ```diff
    diff --git a/tests/test_releases_cli.py b/tests/test_releases_cli.py
    index 07977e499..51f561c13 100644
    --- a/tests/test_releases_cli.py
    +++ b/tests/test_releases_cli.py
    @@ -316,13 +316,13 @@ class ReleasesParserTests(unittest.TestCase):
             # An argparse alias shares the parent's parser object.
             self.assertIs(self.choices["releases"], self.choices["release"])

    -    def test_subcommands_are_exactly_list_show_new(self) -> None:
    +    def test_subcommands_are_exactly_list_show_new_readiness(self) -> None:
             sub = next(
                 a
                 for a in self.choices["releases"]._actions
                 if isinstance(a, argparse._SubParsersAction)
             )
    -        self.assertEqual(set(sub.choices), {"list", "show", "new"})
    +        self.assertEqual(set(sub.choices), {"list", "show", "new", "readiness"})

         def test_no_releases_check_subcommand(self) -> None:
             """ADVERSARIAL (PR-002): `aw check releases` is the canonical validator (check_engine ->
    @@ -434,7 +434,7 @@ class ReleasesCompletionTests(_ReleasesRepoFixture):
             self.assertIn("releases", tree["subcommands"])
             self.assertEqual(
                 set(tree["subcommands"]["releases"]["subcommands"]),
    -            {"list", "show", "new"},
    +            {"list", "show", "new", "readiness"},
             )
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `CommandDeclaration` diff and `python3 -m pytest -o addopts="" -q tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py tests/test_exit_contract_conformance.py` summary lines (failures compared by name with the base: any failure also present at the base is pre-existing and must be shown by a base run). Paste `git diff --stat tests/conformance_matrix.py` (expected empty, or justified per E-05).
  - Observed evidence:
    ```diff
    diff --git a/agent_workflows/command_surface.py b/agent_workflows/command_surface.py
    index 5d82c29a5..816cdaa3a 100644
    --- a/agent_workflows/command_surface.py
    +++ b/agent_workflows/command_surface.py
    @@ -1863,6 +1863,16 @@ COMMAND_INVENTORY: Tuple[CommandDeclaration, ...] = (
             legacy_flags=("--json", "--agent", "--apply"),
             exit_contract=(0, 2),
         ),
    +    CommandDeclaration(
    +        command="releases readiness",
    +        command_class="check",
    +        human_recipe="check",
    +        agent_record_kind="result",
    +        mutation_gate="none",
    +        empty_error_renderer="renderer_boundary",
    +        legacy_flags=("--json", "--agent"),
    +        exit_contract=(0, 1, 2),
    +    ),
         # --- research verbs missing from the inventory ---
         CommandDeclaration(
             command="research pending",
    ```
    ```text
    $ python3 -m pytest -o addopts="" -q tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_agent_surface_conformance.py tests/test_exit_contract_conformance.py
    ........................................................................ [ 63%]
    ..........................................                               [100%]
    114 passed in 557.42s (0:09:17)
    $ git diff --stat tests/conformance_matrix.py
    (empty)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_releases_readiness_cli.py` listing every arm (a) to (l) passing. Paste a NEGATIVE CONTROL: with E-02's `None` branch made to return `detail="full suite RED"` in a scratch `git worktree` (removed afterwards), arm (b) fails. Paste `git grep -n -E 'getsource|import ast|ast\.parse|import inspect' tests/test_releases_readiness_cli.py` returning nothing.
  - Observed evidence:
    ```text
    $ python3 -m pytest -o addopts="" -v tests/test_releases_readiness_cli.py
    collected 12 items

    tests/test_releases_readiness_cli.py::test_arm_f_agent_mode_emits_schema_valid_record_with_exit_and_diagnostic_parity PASSED [  8%]
    tests/test_releases_readiness_cli.py::test_arm_b_no_suite_flag_reports_not_supplied_and_emits_stderr_hint PASSED [ 16%]
    tests/test_releases_readiness_cli.py::test_arm_i_release_alias_is_byte_identical_under_agent PASSED [ 25%]
    tests/test_releases_readiness_cli.py::test_arm_j_tree_is_byte_identical_before_and_after_run PASSED [ 33%]
    tests/test_releases_readiness_cli.py::test_arm_a_go_tree_exits_0_and_renders_go_verdict PASSED [ 41%]
    tests/test_releases_readiness_cli.py::test_arm_d_missing_signer_exits_1_with_residual_risk_failing PASSED [ 50%]
    tests/test_releases_readiness_cli.py::test_arm_l_gate_full_suite_none_returns_not_supplied PASSED [ 58%]
    tests/test_releases_readiness_cli.py::test_arm_k_dir_flag_resolves_identically_before_or_after_subcommand PASSED [ 66%]
    tests/test_releases_readiness_cli.py::test_arm_h_non_project_dir_exits_2 PASSED [ 75%]
    tests/test_releases_readiness_cli.py::test_arm_c_suite_failed_exits_1_with_full_suite_red PASSED [ 83%]
    tests/test_releases_readiness_cli.py::test_arm_e_unproven_host_matrix_claim_fails_capability_freshness PASSED [ 91%]
    tests/test_releases_readiness_cli.py::test_arm_g_json_output_verdict_matches_exit_code PASSED [100%]

    ============================== 12 passed in 12.59s ==============================
    $ # Negative control in scratch worktree with None branch returning detail="full suite RED":
    $ (cd .aw/worktrees/scratch-neg && PYTHONPATH=. python3 -m pytest -o addopts="" -q tests/test_releases_readiness_cli.py -k test_arm_b --tb=short; echo "neg_ctrl_exit=$?")
    F                                                                        [100%]
    =================================== FAILURES ===================================
    _____ test_arm_b_no_suite_flag_reports_not_supplied_and_emits_stderr_hint ______
    tests/test_releases_readiness_cli.py:121: in test_arm_b_no_suite_flag_reports_not_supplied_and_emits_stderr_hint
        assert "| full_suite | FAIL | full suite result not supplied |" in out
    E   AssertionError: assert '| full_suite | FAIL | full suite result not supplied |' in '# Release Readiness Report\n\nVerdict: NO-GO\n\n| Gate | Result | Detail |\n|---|---|---|\n| full_suite | FAIL | full...est present and consistent |\n| residual_risk | PASS | residual risk signed off by qa |\n\nFailing gates: full_suite\n'
    =========================== short test summary info ============================
    FAILED tests/test_releases_readiness_cli.py::test_arm_b_no_suite_flag_reports_not_supplied_and_emits_stderr_hint
    1 failed, 11 deselected in 2.92s
    neg_ctrl_exit=1
    $ git grep -n -E 'getsource|import ast|ast\.parse|import inspect' tests/test_releases_readiness_cli.py; echo "grep_exit=$?"
    grep_exit=1
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `git diff docs/recovery.md docs/artifact-lifecycles.md CHANGELOG.md`; `python3 -c "from pathlib import Path; from agent_workflows import docs_check as d; print(d.check_docs_dir(Path('docs')))"` before and after showing no new finding; `git grep -n -P '[\x{2013}\x{2014}]' -- docs/recovery.md docs/artifact-lifecycles.md` limited to the added lines showing none; and the bare `python3 -m pytest` summary line plus a by-name failure diff against the base baseline showing no new failure.
  - Observed evidence:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 97f055cb0..314b065ae 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Added: read-only `aw releases readiness` command (and `aw release readiness` alias) to evaluate and render the GO / NO-GO release-readiness report in human, `--json`, and `--agent` modes, exiting 0 on GO, 1 on NO-GO, and 2 on cannot-run. Explicit `--suite-passed` / `--suite-failed` and `--residual-risk-signer` flags supply human attestations without guessing defaults, and `release_readiness.gate_full_suite(None)` reports `full suite result not supplied` instead of `full suite RED`.
     - Fixed: the run dashboard and verifier corroboration now count an Antigravity tool call that ended in the FAILED state, matching what the live stream shows.
     - Added: `aw checkup` command and periodic CI health checks with configurable interval (`ci_checkup_interval_commits`, default 100), workflow (`ci_checkup_workflow`, default `tests.yml`), and branch (`ci_checkup_branch`, default `main`) in `project.json`, showing checkup status in run start and run end banners, `aw attention`, and `aw doctor`.
     - Added: merge-time stale spec line-anchor citation gate refuses integration of lanes that introduce new stale spec line citations (cause spec-anchor-new-stale) before the merge-and-revalidate gate, with bounded fix-it retry turns and fail-open behavior on unknown detector errors.
    diff --git a/docs/artifact-lifecycles.md b/docs/artifact-lifecycles.md
    index e11f03ff8..15f8b8ab9 100644
    --- a/docs/artifact-lifecycles.md
    +++ b/docs/artifact-lifecycles.md
    @@ -491,6 +491,7 @@ A release record is a thin anchor that other artifacts point at with `- Blocks-R
     ```sh
     aw releases new --version 2.1.0 --summary "why this release exists" --apply
     aw releases show            # the planned release and everything gating it
    +aw releases readiness --suite-passed --residual-risk-signer <name>
     aw set releases shipped <id6>
     aw check releases           # validate
     ```
    diff --git a/docs/recovery.md b/docs/recovery.md
    index 929ea63d8..8bd1cd837 100644
    --- a/docs/recovery.md
    +++ b/docs/recovery.md
    @@ -47,19 +47,29 @@ no-op.
     The final release-readiness review aggregates the gates into a GO or NO-GO verdict
     (`agent_workflows/release_readiness.py`). It NEVER tags, publishes, deploys, or pushes; those are
     separately authorized actions (see `RELEASING.md` and the release-review workflow). The review
    -runs the canonical leak scan and all IPD lint phases for real, checks the benchmark invariants,
    -the changelog and versioning, and the residual-risk sign-off, then emits the verdict.
    +runs the canonical leak scan and all IPD lint phases for real, checks generated workflow drift,
    +documentation checks, workflow dispositions, capability freshness, benchmark invariants, the
    +changelog and versioning, and the residual-risk sign-off, then emits the verdict.

    -The full release-readiness test suite was deleted in commit 19313eed, so the aggregate review
    -verdict, changelog and versioning check, and residual-risk gate currently lack dedicated test
    -coverage (tracked in backlog item 3rmvik). A partial behavioral guard survives in
    -`tests/test_release_readiness_child_pin.py`, covering only subprocess child pinning and
    -stdin denial for `gate_leak_scan` and `gate_ipd_lint`:
    +Run the read-only report from the CLI:

     ```
    -python3 -m pytest tests/test_release_readiness_child_pin.py -q
    +aw releases readiness --suite-passed --residual-risk-signer <name>
     ```

    +The command never runs the full test suite itself and never invents human attestations:
    +
    +- `--suite-passed` / `--suite-failed` (mutually exclusive): attests the outcome of a real full
    +  test suite run. If neither flag is passed, the `full_suite` gate fails with `full suite result
    +  not supplied` rather than claiming a red suite that was not run.
    +- `--residual-risk-signer NAME`: attests the human residual-risk sign-off. Without a signer, the
    +  `residual_risk` gate fails with `residual-risk sign-off missing`.
    +- `--agent` / `--json`: emits a canonical `aw.agent/v1` result record or structured JSON.
    +
    +Exit codes are `0` on `GO`, `1` on `NO-GO`, and `2` when the command cannot run (such as a
    +non-project `--dir` or conflicting flags). Note that the `artifact_manifest` row is not yet
    +computed from disk and currently defaults to passing (tracked in backlog item `3jkm7y`).
    +
     ## Responsibility boundary

     The tool resumes, recovers, and rolls back deterministically, and refuses an unsafe downgrade.
    ```
    ```text
    $ # Before E-07 edits:
    $ python3 -c "from pathlib import Path; from agent_workflows import docs_check as d; print(d.check_docs_dir(Path('docs')))"
    []
    $ # After E-07 edits:
    $ python3 -c "from pathlib import Path; from agent_workflows import docs_check as d; print(d.check_docs_dir(Path('docs')))"
    []
    $ git grep -n -P '[\x{2013}\x{2014}]' -- docs/recovery.md docs/artifact-lifecycles.md CHANGELOG.md; echo "dash_exit=$?"
    dash_exit=1
    $ python3 -m pytest
    NOTE: 292 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    =========================== short test summary info ============================
    FAILED tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository
    1 failed, 8325 passed, 4 skipped, 18 xfailed, 3 warnings in 752.02s (0:12:32)
    $ # Base commit c85687c5ea0ea9db1e806f002850a8eb907134d2 failure reproduction:
    $ (cd .aw/worktrees/scratch-base && PYTHONPATH=. python3 -m pytest -o addopts="" -p no:randomly -q tests/test_artifact_adopt.py tests/test_completion.py tests/test_status_set.py tests/test_stdin_interactive.py tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository --tb=short)
    FAILED tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository
    1 failed, 186 passed in 43.00s
    $ comm -13 <(printf '%s\n' "tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository" | sort) <(printf '%s\n' "tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository" | sort); echo "comm_exit=$?"
    comm_exit=0
    $ python3 -m pytest -o addopts="" -q tests/test_host_capability_extension.py
    ................................................                         [100%]
    48 passed in 4.02s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`); approval also rules on OQ-01's public surface.

DEPENDENCY GATE. `- Item-Dependencies: executed:ttg9uz`. E-01 enforces it by behavior as well as location: if `ttg9uz` is not executed, or `gate_capability_freshness()` still passes vacuously, mark E-01 `blocked` and edit nothing.

EXECUTION CONTRACT. OQ-01 is resolved (reviewer decision D-1, ratified by approval) and non-blocking. Commit only the declared paths plus this plan through `aw commit <plan> -- <paths>`; never `git add -A`, `-a`, `--no-verify`, `git stash` or a push; verify the staged set (shared checkout). Paste actual output.

POST-GATE LIFECYCLE. Do not mark `executed` until `aw ipd lint --phase pre-transition` conforms and all seven `V-*` read `pass` with pasted evidence. Under a runner, it owns begin/finalize; by hand use `aw ipd finalize`.

DO NOT make the command default `--suite-passed` or a signer, and do not add flags that assert the artifact manifest. Each would put a forged PASS row back into the report this Set exists to make truthful.
