# IPD: Make the managed AGENTS.md block target-neutral and refuse dangling references in installed agent docs

- Date: 2026-10-06
- Kind: child
- Concern: Defect D07 of research report `l6cbbb`, present at HEAD `474b037a9` and re-measured at review HEAD `3a03589f8`. `engine.agents_pointer_prose(target_layout)` emits ONE managed `aw:pointer` section that is written both into this repository's `AGENTS.md` and into every target's `AGENTS.md` (`engine.update_agents_pointer` -> `engine.agents_managed_sections`). That section carries material that is only true of agent-workflows itself: the "HOW TO RUN THE SUITE: run it BARE, as `python3 -m pytest` (or `make test`)" paragraph and its `pyproject.toml` `addopts` reasoning; mandates to read `RELEASING.md`, `CONTRIBUTING.md` and `GUIDING_PRINCIPLES` P12/P16; a citation of the `ipd-spec` doc under `.aw/records/specs/` (specs are not installed into targets); and runner guarantees cited "BY SYMBOL in `oc_runipd.py` ... `runner_shared.py`", source files a target does not contain. In a scratch Node target (package.json only) the installed `AGENTS.md` is 125 lines and line 80 instructs agents to run `python3 -m pytest`, which is wrong for that project, and several mandated files do not exist. Nothing detects a managed doc that points at a path the target lacks.
- Scope: IN: split the managed `aw:pointer` prose into target-neutral content (stays in `agents_pointer_prose`) and agent-workflows-only content (moves BELOW `<!-- /aw:block -->` in this repository's own `AGENTS.md`, the repo-local region that already exists and is never installed); rephrase the runner-guarantees paragraph to point at `aw host capabilities` and `aw oc run --help` instead of source symbols; point the IPD contract at the installed `ipd-lifecycle` workflow, `.aw/records/plans/README.md` and `aw ipd --help` instead of an uninstalled spec; replace the hard-coded test command with "run the project's own test command (see `/setup-repo` or the project's docs)"; repoint the two existing tests that pin AW-only text to `agents_pointer_prose`; add a dangling-reference probe reported by `aw doctor` (advisory `info` severity) and as a post-install advisory line, scanning the managed `AGENTS.md` block and the installed records READMEs; tests. OUT: the retired `.agents/` strings in installed READMEs and install messages (Order 06 `jbnkkh`); the inbox README (Order 05 `xzlu9b`, which this plan's check must find present); rewriting the content of the AW-only paragraphs (they move verbatim); the installed workflow bundle `.aw/system/**` (see Deferred); the `aw:reporting` section (measured: it cites no path).
- Scope-Paths: agent_workflows/engine.py, agent_workflows/doctor.py, agent_workflows/check_engine.py, agent_workflows/cli.py, AGENTS.md, tests/test_suite_instruction_marker_parity.py, tests/test_agents_block_target_neutral.py
- Item-Dependencies: executed:xzlu9b, executed:jbnkkh
- Status: approved
- Readiness: go-pending-approval
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: high
- Set: instbugs
- Order: 7
- Highest E allocated: 06
- Author: antigravity/claude-opus-5.5
- Id: ka0g86
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009. Reviewed at lane HEAD `3a03589f8`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Re-measured D07 with a scratch `private-target` install (125-line `AGENTS.md`, line 80 `python3 -m pytest`) and a `--keep-legacy` install, and prototyped the extraction rule on both (F-06..F-08). Fixed: two existing tests pin the AW-only text to `agents_pointer_prose` and would break, now repointed by new E-06 (PR-001); E-04's extraction rule was undefined and, applied naively to the bundle, reports 433 hits, so the token rule is specified, the scan scope is the managed block plus `.aw/records/**/README.md`, and the bundle is deferred (PR-002); probe severity, rule registry and doctor exit-code effect specified as advisory `info` (PR-003); legacy layout cites `.aw/inbox/` and `.aw/records/plans/pending/`, both absent there, now in E-03 (PR-004); the "TEST OUTCOMES" paragraph is half general rule, so only its P16 citation is AW-only (PR-005); install advisory call site named and `cli.py` added (PR-006); E-02 regeneration path named and verbatim-preservation check made behavioral (PR-007); `- Blocks-Release: next` (PR-008); gate gains resolved-OQ statement, honesty rule, scope fence, temp HOME and conditional finalize ownership (PR-009).
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 07 of Set `instbugs` after reading the 125-line `AGENTS.md` a HEAD (`474b037a9`) install wrote into a package.json-only scratch target, and locating each AW-only paragraph in `engine.agents_pointer_prose`.

## Goal

The managed `AGENTS.md` block an install writes into any target contains only guidance that is true in that target, this repository keeps its own AW-only rules in its repo-local region, and `aw doctor` plus the install report flag any installed agent doc that points at a path the target does not have.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD with `AW_NO_REEXEC=1`, `HOME` pointed at a temp dir and a git identity in the environment: (a) fresh install (`aw install <dir> --preset private-target -y --no-interactive`) into a temp git repo containing only `package.json`; (b) the same with a committed `.agents/workflows/index.md` and `--keep-legacy` (legacy layout). For each, paste `wc -l AGENTS.md`, `grep -nE "python3 -m pytest|pyproject|RELEASING.md|CONTRIBUTING.md|GUIDING_PRINCIPLES|oc_runipd.py|runner_shared.py|records/specs/|ipd-spec" AGENTS.md`, and the list of path tokens (per the E-04 token rule) inside the managed block that do not exist in the target. STOP and report if the block is already target-neutral.
  - Depends on: none
  - Expected outcome: the inventory of AW-only paragraphs and dangling paths for both layouts pasted with the HEAD sha.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 Split `engine.agents_pointer_prose`: move the AW-only paragraphs out of the function, verbatim, into this repository's `AGENTS.md` BELOW `<!-- /aw:block -->` under a new repo-local heading (e.g. `## Repository development contract (repo-local rule)`, placed beside the existing "Research prompts about THIS repository (repo-local rule)" section and carrying the same "REPO-LOCAL AND MUST NOT BE INSTALLED" banner). The AW-only set is exactly: the "HOW TO RUN THE SUITE" paragraph; the "(see `RELEASING.md`)" clause and the "See `CONTRIBUTING.md` and the ... README for detail" sentence of the execution contract; the "(see GUIDING_PRINCIPLES P16)" and "(see GUIDING_PRINCIPLES P12)" citations; the `oc_runipd.py`/`runner_shared.py`/`cnwy8g` symbol citations of the runner paragraph; the "lives in the `ipd-spec` doc under `.aw/records/specs/`" clause. The surrounding GENERAL rules (tooled commit path, no-code-pinning tests rules (1)-(4), self-contained questions, release-only-after-human-GO) stay in the managed block; only their AW-specific citations move. Then regenerate this repository's managed block with the normal install path (`AW_NO_REEXEC=1 python3 -m agent_workflows install . --no-interactive -y` or the equivalent `engine.update_agents_pointer` call; stage only `AGENTS.md` from its output) so the managed region equals the new `agents_managed_block(target_layout="aw")`.
  - Depends on: E-01
  - Expected outcome: `agents_pointer_prose` output for both layouts contains none of the E-01 AW-only tokens; this repository's `AGENTS.md` contains every moved paragraph or clause verbatim in the repo-local region, and its managed region is byte-equal to the regenerated block.
  - Execution state: pending

- [ ] E-03 Rephrase the target-neutral remainder: the runner-guarantees paragraph points at `aw host capabilities` and `aw oc run --help` rather than source symbols (keeping the behavioral claims: dependency-depth ordering, dispatch re-check, orchestrator retirement, isolated worktrees); the IPD contract points at the installed `ipd-lifecycle` workflow (`<workflows_dir>/ipd-lifecycle/ipd-lifecycle.md`), `<plans_dir>/README.md` and `aw ipd --help` rather than a spec path; the test-command guidance says to use the project's own test command (discovered by `/setup-repo` or the project's docs) and to paste its actual output. Layout correctness: in the `legacy` branch the two hard-coded `.aw/` paths (`.aw/inbox/` in the inbox paragraph and `.aw/records/plans/pending/` in the TODO.md sentence) become layout-variable (the inbox paragraph is emitted only for the `aw` layout, matching `xzlu9b`'s aw-only inbox; the pending path uses `{plans_dir}/pending/`).
  - Depends on: E-02
  - Expected outcome: every path token (E-04 rule) in the managed block exists in a fresh target of either layout.
  - Execution state: pending

- [ ] E-04 Add the dangling-reference probe `doctor.probe_installed_doc_references(repo_root) -> List[core.Drift]`, wired into `doctor.collect_doctor_report`. Scan set: the managed region of the target's `AGENTS.md` (from `<!-- aw:block -->` to `<!-- /aw:block -->`, via the existing `engine` aw-block parser) and every `.aw/records/**/README.md` (legacy: `.agents/**/README.md` outside `.agents/workflows/` and `.agents/skills/`), plus `.aw/inbox/README.md` when present. Token rule (one function, one docstring): a backticked span is a PATH CANDIDATE iff it contains no whitespace, `<`, `*`, or `...`, does not start with `/` (slash commands), and either starts with a known install root (`.aw/`, `.agents/`, `.opencode/`, `.claude/`) or matches a relative file shape with a `.md|.py|.toml|.json|.yaml|.yml` extension; a candidate DANGLES iff it exists neither relative to the repo root nor relative to the scanned file's directory. A small `_DANGLING_REF_ALLOWLIST` constant (one comment per entry) covers tokens the tooling creates lazily or that are generated/gitignored (measured candidates: `INDEX.json`, `INDEX.md`, `TODO.md` which the block names as deprecated). Each dangle is `Drift(<scanned file rel path>, "doctor.dangling-doc-reference", "<token>")` registered in `check_engine.RULE_REGISTRY` at `info` severity, so `aw doctor`'s exit code is unchanged by introduction (same posture as `doctor.artifact-status-location-drift`). Install advisory: after `engine.print_summary` in `cli._install_one`, call the probe once and print one advisory line per dangle (`warn` status, path and token), or nothing when clean; it never fails the install.
  - Depends on: E-03
  - Expected outcome: a fresh target of each layout reports zero `doctor.dangling-doc-reference` findings once `xzlu9b` and `jbnkkh` are executed; a planted missing path is reported with its file and token; `aw doctor`'s exit code is not changed by the new rule alone.
  - Execution state: pending

- [ ] E-06 Repoint the existing tests that pin AW-only text to the installed block: `tests/test_suite_instruction_marker_parity.py` asserts the `addopts` marker filter appears in `engine.agents_pointer_prose`; after E-02 that text lives in this repository's repo-local region, so the test must assert it against this repository's `AGENTS.md` repo-local region (text after `<!-- /aw:block -->`; `AGENTS.md` is the artifact under test, as the test's own P16 note already argues for the prose) and must assert `agents_pointer_prose` for both layouts no longer contains `pyproject.toml`. Before editing, re-run `grep -rln "agents_pointer_prose\|agents_managed_block\|update_agents_pointer" tests/` and run each listed test file narrowed against the E-02/E-03 change; repoint any other test asserting a moved string the same way and add its path at finalize with `--scope-reason`.
  - Depends on: E-03
  - Expected outcome: no existing test fails because of the move; the parity guarantee (managed suite instruction quotes the configured marker filter) still holds, now for this repository's repo-local copy.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_agents_block_target_neutral.py` (mark `slow` if it runs real installs, matching `tests/test_installer.py`): (a) fresh install of each layout into a temp git repo with only `package.json` (legacy via a committed `.agents/workflows/index.md` plus `--keep-legacy`); assert the installed managed block contains none of `python3 -m pytest`, `pyproject.toml`, `RELEASING.md`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES`, `oc_runipd.py`, `runner_shared.py`, `ipd-spec`; (b) run `aw doctor --json --dir <target>` and assert zero diagnostics with rule `doctor.dangling-doc-reference`; (c) append a backticked reference to a nonexistent `docs/missing.md` inside an installed `.aw/records/plans/README.md` and assert the probe reports exactly that token with that file as location; (d) call the probe on a tmp tree whose AGENTS.md managed block names `.aw/nope/README.md` and assert one finding, and that a placeholder (`<id6>`), glob, slash command and allowlisted token produce none; (e) assert this repository's `AGENTS.md` repo-local region (text after `<!-- /aw:block -->`) contains "HOW TO RUN THE SUITE" and its managed region does not. Prove (a) can fail by restoring the "HOW TO RUN THE SUITE" paragraph into `agents_pointer_prose` and pasting the failure, then revert.
  - Depends on: E-04, E-06
  - Expected outcome: the new tests pass, the mutation fails (a); no test reads production source (all assertions are on installed files, the repository's `AGENTS.md`, probe return values and command output).
  - Execution state: pending

## Project conventions discovered (Step 0)

- This repository's `AGENTS.md` already separates a managed block (between `<!-- aw:block -->` and `<!-- /aw:block -->`) from a repo-local region below it; its "Research prompts about THIS repository (repo-local rule)" section says "THIS SECTION IS REPO-LOCAL AND MUST NOT BE INSTALLED INTO A MANAGED TARGET REPO"; that region is the home for AW-only rules.
- `engine.agents_pointer_prose(target_layout)` and `engine.update_agents_pointer(..., target_layout=...)` already branch on layout; `engine.resolve_target_layout` decides it; the fix reuses that value.
- `aw doctor` aggregates probes in `doctor.collect_doctor_report`; a new probe follows the `probe_*` pattern there; advisory findings use `info` severity, which `artifact_core.drift_exit_code` exempts (precedent `doctor.probe_artifact_audit`).
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The managed block hard-codes this repository's test command. | `engine.agents_pointer_prose` string "HOW TO RUN THE SUITE: run it BARE, as `python3 -m pytest` (or `make test`)."; scratch target `AGENTS.md` line 80 (re-measured at `3a03589f8`) |
| F-02 | The managed block cites source files a target lacks. | `agents_pointer_prose` text "verifiable BY SYMBOL in `oc_runipd.py` or ... in `runner_shared.py`" |
| F-03 | The managed block mandates files a Node target lacks. | scratch target has no `RELEASING.md`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES.md`; the IPD contract cites "the `ipd-spec` doc under `{specs_dir}/`", and no spec is installed |
| F-04 | Nothing detects dangling references in installed docs. | `doctor.collect_doctor_report` calls `probe_environment`, `probe_git`, `probe_attention`, `probe_sanitizer`, `probe_artifacts` (which calls `probe_artifact_audit`); none scans installed docs for paths |
| F-05 | Order dependency. | the check must pass on a fresh target, which requires the inbox README (Order 05) and the de-staled READMEs (Order 06) to be present first |
| F-06 | Two existing tests pin AW-only text to `agents_pointer_prose`. | `tests/test_suite_instruction_marker_parity.py` asserts the `addopts` marker expression is `assertIn(... engine.agents_pointer_prose(target_layout=layout))`; `tests/test_authoring_coverage_guidance.py` asserts orchestrator-coverage sentences (target-neutral, unaffected) |
| F-07 | Measured dangles at review HEAD, `.aw` layout, token rule of E-04. | managed block: `.aw/inbox/`, `CONTRIBUTING.md`, `RELEASING.md`, `TODO.md`, `oc_runipd.py`, `pyproject.toml`, `runner_shared.py`; READMEs: comms `.agents/docs/specs/` (jbnkkh), plans `CONTRIBUTING.md`, research `.aw/records/specs/implemented/...agents-artifact-organization.spec.md` (jbnkkh), `INDEX.json`/`INDEX.md` (generated) |
| F-08 | Legacy layout block hard-codes two `.aw/` paths. | `--keep-legacy` scratch install: dangles `.aw/inbox/` and `.aw/records/plans/pending/` (from the TODO.md sentence "write a plan under `.aw/records/plans/pending/`") |
| F-09 | The installed workflow bundle is out of reach for a zero-finding bar. | same token rule over `.aw/system/**/*.md`: 433 hits, 117 distinct, mostly artifact-name examples (`persona-review.md`, `05-decisions.md`) and conditional discovery lists ("`TODO.md`, `TODOS.md`, ..."); every `.agents/` hit there is labelled "legacy" |

## Proposed changes (ordered, validatable)

1. Move AW-only paragraphs and clauses to the repo-local region (E-02).
2. Rephrase the neutral remainder and fix legacy-layout paths (E-03).
3. Dangling-reference probe in doctor and install advisory (E-04).
4. Repoint the existing parity test (E-06).
5. Behavior tests with mutation proof (E-05).

## Deferred / out of scope (with reason)

- Retired `.agents/` strings in installed READMEs and messages are fixed elsewhere.
  - Carrier: jbnkkh
  - Carrier-Evidence: .aw/records/plans/executed/20261006-instbugs-06-jbnkkh-remove-retired-paths-statuses-and-naming-rules-from-installe.ipd.md
- The inbox README existence is delivered elsewhere.
  - Carrier: xzlu9b
- The whole-Set fresh-install regression that re-runs this check end to end.
  - Carrier: kck7a5
- Scanning the installed workflow bundle `.aw/system/**` for dangling references: F-09 shows the token rule cannot tell an example artifact name or a conditional discovery list from a real reference there, so a zero-finding bar is unreachable without per-file semantics; the managed block and records READMEs are the surfaces an agent is told to obey unconditionally.
  - Carrier-Declined: not owed; the bundle's references are conditional ("if present", "legacy") by construction and no defect is known in them.

## Scope check

- Over-scope: none.
- Under-scope: the check is advisory at install time and `info` in doctor (it does not fail an install or change doctor's exit code), because a user's own README edits could legitimately reference paths outside the tool's knowledge; `aw doctor` reports it for follow-up.

## Required tests / validation

- `tests/test_agents_block_target_neutral.py` (E-05) with the mutation proof.
- `tests/test_suite_instruction_marker_parity.py` repointed (E-06).
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline; plus `python3 -m pytest -o addopts="" -m slow tests/test_agents_block_target_neutral.py tests/test_installer.py -n auto` if E-05 is marked `slow`.

## Spec / documentation sync

- N/A for specs: no spec states the managed block's contents. Spec `ipd-structure-and-linting` item 11 asks for the always-loaded structural prose to be a "thin pointer", which this change moves toward and does not contradict. This repository's `AGENTS.md` is updated by E-02 (content moved, not changed).

## Open questions

### OQ-01: Should the AW-only paragraphs be deleted from targets or offered as an optional preset?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: removed from targets. They describe this repository's own suite, release process and source files, which no target has; an optional preset would reintroduce dangling references. They remain in force here via the repo-local region.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE, for both layouts, the pre-edit `wc -l`, grep inventory and dangling-path list with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the E-01 grep re-run on a post-edit fresh target of each layout (no hits); `grep -n "HOW TO RUN THE SUITE\|<!-- /aw:block -->" AGENTS.md` in this repository showing the suite line number is greater than the close marker's; and the output of a one-liner asserting `engine.agents_managed_block(target_layout="aw").strip()` is a substring of this repository's `AGENTS.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the rephrased runner, IPD-contract and test-command paragraphs from a post-edit fresh target of each layout, and the legacy target's dangling list showing neither `.aw/inbox/` nor `.aw/records/plans/pending/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE `aw doctor --json` filtered to rule `doctor.dangling-doc-reference` on a fresh target of each layout (empty) and on the planted-missing-path target (the finding naming file and token); the install output's advisory line for the planted case (or the clean case printing none); and `check_engine.rule_spec("doctor.dangling-doc-reference").severity` printing `info`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE the `grep -rln` census of tests touching the pointer prose, the narrowed run of each listed file after the change (all pass), and the diff of `tests/test_suite_instruction_marker_parity.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: making the block neutral and adding the check that proves it neutral are one deliverable; the check without the cleanup would fail on every install, and the cleanup without the check would regress silently.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in dependency order (E-01, E-02, E-03, E-04, E-06, E-05). Commit only files changed for this plan through `aw commit ka0g86 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout (E-02's self-install may touch other managed files; stage only `AGENTS.md` from it). HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output does not satisfy any item. Run every real install with `AW_NO_REEXEC=1`, `HOME` pointed at a temp dir, and a git identity in the environment. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize ka0g86`, never by a hand `git mv`.
