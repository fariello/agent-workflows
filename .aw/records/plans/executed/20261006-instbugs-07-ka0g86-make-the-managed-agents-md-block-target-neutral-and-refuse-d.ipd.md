# IPD: Make the managed AGENTS.md block target-neutral and refuse dangling references in installed agent docs

- Date: 2026-10-06
- Kind: child
- Concern: Defect D07 of research report `l6cbbb`, present at HEAD `474b037a9` and re-measured at review HEAD `3a03589f8`. `engine.agents_pointer_prose(target_layout)` emits ONE managed `aw:pointer` section that is written both into this repository's `AGENTS.md` and into every target's `AGENTS.md` (`engine.update_agents_pointer` -> `engine.agents_managed_sections`). That section carries material that is only true of agent-workflows itself: the "HOW TO RUN THE SUITE: run it BARE, as `python3 -m pytest` (or `make test`)" paragraph and its `pyproject.toml` `addopts` reasoning; mandates to read `RELEASING.md`, `CONTRIBUTING.md` and `GUIDING_PRINCIPLES` P12/P16; a citation of the `ipd-spec` doc under `.aw/records/specs/` (specs are not installed into targets); and runner guarantees cited "BY SYMBOL in `oc_runipd.py` ... `runner_shared.py`", source files a target does not contain. In a scratch Node target (package.json only) the installed `AGENTS.md` is 125 lines and line 80 instructs agents to run `python3 -m pytest`, which is wrong for that project, and several mandated files do not exist. Nothing detects a managed doc that points at a path the target lacks.
- Scope: IN: split the managed `aw:pointer` prose into target-neutral content (stays in `agents_pointer_prose`) and agent-workflows-only content (moves BELOW `<!-- /aw:block -->` in this repository's own `AGENTS.md`, the repo-local region that already exists and is never installed); rephrase the runner-guarantees paragraph to point at `aw host capabilities` and `aw oc run --help` instead of source symbols; point the IPD contract at the installed `ipd-lifecycle` workflow, `.aw/records/plans/README.md` and `aw ipd --help` instead of an uninstalled spec; replace the hard-coded test command with "run the project's own test command (see `/setup-repo` or the project's docs)"; repoint the two existing tests that pin AW-only text to `agents_pointer_prose`; add a dangling-reference probe reported by `aw doctor` (advisory `info` severity) and as a post-install advisory line, scanning the managed `AGENTS.md` block and the installed records READMEs; tests. OUT: the retired `.agents/` strings in installed READMEs and install messages (Order 06 `jbnkkh`); the inbox README (Order 05 `xzlu9b`, which this plan's check must find present); rewriting the content of the AW-only paragraphs (they move verbatim); the installed workflow bundle `.aw/system/**` (see Deferred); the `aw:reporting` section (measured: it cites no path).
- Scope-Paths: agent_workflows/engine.py, agent_workflows/doctor.py, agent_workflows/check_engine.py, agent_workflows/cli.py, AGENTS.md, tests/test_suite_instruction_marker_parity.py, tests/test_agents_block_target_neutral.py
- Item-Dependencies: executed:xzlu9b, executed:jbnkkh
- Status: executed
- Readiness: go-pending-approval
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: high
- Set: instbugs
- Order: 7
- Highest E allocated: 06
- Author: antigravity/claude-opus-5.5
- Id: ka0g86

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ka0g86 verified (set instbugs, attempt 1).
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

- [x] E-01 Re-measure at the execution HEAD with `AW_NO_REEXEC=1`, `HOME` pointed at a temp dir and a git identity in the environment: (a) fresh install (`aw install <dir> --preset private-target -y --no-interactive`) into a temp git repo containing only `package.json`; (b) the same with a committed `.agents/workflows/index.md` and `--keep-legacy` (legacy layout). For each, paste `wc -l AGENTS.md`, `grep -nE "python3 -m pytest|pyproject|RELEASING.md|CONTRIBUTING.md|GUIDING_PRINCIPLES|oc_runipd.py|runner_shared.py|records/specs/|ipd-spec" AGENTS.md`, and the list of path tokens (per the E-04 token rule) inside the managed block that do not exist in the target. STOP and report if the block is already target-neutral.
  - Depends on: none
  - Expected outcome: the inventory of AW-only paragraphs and dangling paths for both layouts pasted with the HEAD sha.
  - Execution state: performed

### Task group 2: fix

- [x] E-02 Split `engine.agents_pointer_prose`: move the AW-only paragraphs out of the function, verbatim, into this repository's `AGENTS.md` BELOW `<!-- /aw:block -->` under a new repo-local heading (e.g. `## Repository development contract (repo-local rule)`, placed beside the existing "Research prompts about THIS repository (repo-local rule)" section and carrying the same "REPO-LOCAL AND MUST NOT BE INSTALLED" banner). The AW-only set is exactly: the "HOW TO RUN THE SUITE" paragraph; the "(see `RELEASING.md`)" clause and the "See `CONTRIBUTING.md` and the ... README for detail" sentence of the execution contract; the "(see GUIDING_PRINCIPLES P16)" and "(see GUIDING_PRINCIPLES P12)" citations; the `oc_runipd.py`/`runner_shared.py`/`cnwy8g` symbol citations of the runner paragraph; the "lives in the `ipd-spec` doc under `.aw/records/specs/`" clause. The surrounding GENERAL rules (tooled commit path, no-code-pinning tests rules (1)-(4), self-contained questions, release-only-after-human-GO) stay in the managed block; only their AW-specific citations move. Then regenerate this repository's managed block with the normal install path (`AW_NO_REEXEC=1 python3 -m agent_workflows install . --no-interactive -y` or the equivalent `engine.update_agents_pointer` call; stage only `AGENTS.md` from its output) so the managed region equals the new `agents_managed_block(target_layout="aw")`.
  - Depends on: E-01
  - Expected outcome: `agents_pointer_prose` output for both layouts contains none of the E-01 AW-only tokens; this repository's `AGENTS.md` contains every moved paragraph or clause verbatim in the repo-local region, and its managed region is byte-equal to the regenerated block.
  - Execution state: performed

- [x] E-03 Rephrase the target-neutral remainder: the runner-guarantees paragraph points at `aw host capabilities` and `aw oc run --help` rather than source symbols (keeping the behavioral claims: dependency-depth ordering, dispatch re-check, orchestrator retirement, isolated worktrees); the IPD contract points at the installed `ipd-lifecycle` workflow (`<workflows_dir>/ipd-lifecycle/ipd-lifecycle.md`), `<plans_dir>/README.md` and `aw ipd --help` rather than a spec path; the test-command guidance says to use the project's own test command (discovered by `/setup-repo` or the project's docs) and to paste its actual output. Layout correctness: in the `legacy` branch the two hard-coded `.aw/` paths (`.aw/inbox/` in the inbox paragraph and `.aw/records/plans/pending/` in the TODO.md sentence) become layout-variable (the inbox paragraph is emitted only for the `aw` layout, matching `xzlu9b`'s aw-only inbox; the pending path uses `{plans_dir}/pending/`).
  - Depends on: E-02
  - Expected outcome: every path token (E-04 rule) in the managed block exists in a fresh target of either layout.
  - Execution state: performed

- [x] E-04 Add the dangling-reference probe `doctor.probe_installed_doc_references(repo_root) -> List[core.Drift]`, wired into `doctor.collect_doctor_report`. Scan set: the managed region of the target's `AGENTS.md` (from `<!-- aw:block -->` to `<!-- /aw:block -->`, via the existing `engine` aw-block parser) and every `.aw/records/**/README.md` (legacy: `.agents/**/README.md` outside `.agents/workflows/` and `.agents/skills/`), plus `.aw/inbox/README.md` when present. Token rule (one function, one docstring): a backticked span is a PATH CANDIDATE iff it contains no whitespace, `<`, `*`, or `...`, does not start with `/` (slash commands), and either starts with a known install root (`.aw/`, `.agents/`, `.opencode/`, `.claude/`) or matches a relative file shape with a `.md|.py|.toml|.json|.yaml|.yml` extension; a candidate DANGLES iff it exists neither relative to the repo root nor relative to the scanned file's directory. A small `_DANGLING_REF_ALLOWLIST` constant (one comment per entry) covers tokens the tooling creates lazily or that are generated/gitignored (measured candidates: `INDEX.json`, `INDEX.md`, `TODO.md` which the block names as deprecated). Each dangle is `Drift(<scanned file rel path>, "doctor.dangling-doc-reference", "<token>")` registered in `check_engine.RULE_REGISTRY` at `info` severity, so `aw doctor`'s exit code is unchanged by introduction (same posture as `doctor.artifact-status-location-drift`). Install advisory: after `engine.print_summary` in `cli._install_one`, call the probe once and print one advisory line per dangle (`warn` status, path and token), or nothing when clean; it never fails the install.
  - Depends on: E-03
  - Expected outcome: a fresh target of each layout reports zero `doctor.dangling-doc-reference` findings once `xzlu9b` and `jbnkkh` are executed; a planted missing path is reported with its file and token; `aw doctor`'s exit code is not changed by the new rule alone.
  - Execution state: performed

- [x] E-06 Repoint the existing tests that pin AW-only text to the installed block: `tests/test_suite_instruction_marker_parity.py` asserts the `addopts` marker filter appears in `engine.agents_pointer_prose`; after E-02 that text lives in this repository's repo-local region, so the test must assert it against this repository's `AGENTS.md` repo-local region (text after `<!-- /aw:block -->`; `AGENTS.md` is the artifact under test, as the test's own P16 note already argues for the prose) and must assert `agents_pointer_prose` for both layouts no longer contains `pyproject.toml`. Before editing, re-run `grep -rln "agents_pointer_prose\|agents_managed_block\|update_agents_pointer" tests/` and run each listed test file narrowed against the E-02/E-03 change; repoint any other test asserting a moved string the same way and add its path at finalize with `--scope-reason`.
  - Depends on: E-03
  - Expected outcome: no existing test fails because of the move; the parity guarantee (managed suite instruction quotes the configured marker filter) still holds, now for this repository's repo-local copy.
  - Execution state: performed

### Task group 3: pin it

- [x] E-05 Add `tests/test_agents_block_target_neutral.py` (mark `slow` if it runs real installs, matching `tests/test_installer.py`): (a) fresh install of each layout into a temp git repo with only `package.json` (legacy via a committed `.agents/workflows/index.md` plus `--keep-legacy`); assert the installed managed block contains none of `python3 -m pytest`, `pyproject.toml`, `RELEASING.md`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES`, `oc_runipd.py`, `runner_shared.py`, `ipd-spec`; (b) run `aw doctor --json --dir <target>` and assert zero diagnostics with rule `doctor.dangling-doc-reference`; (c) append a backticked reference to a nonexistent `docs/missing.md` inside an installed `.aw/records/plans/README.md` and assert the probe reports exactly that token with that file as location; (d) call the probe on a tmp tree whose AGENTS.md managed block names `.aw/nope/README.md` and assert one finding, and that a placeholder (`<id6>`), glob, slash command and allowlisted token produce none; (e) assert this repository's `AGENTS.md` repo-local region (text after `<!-- /aw:block -->`) contains "HOW TO RUN THE SUITE" and its managed region does not. Prove (a) can fail by restoring the "HOW TO RUN THE SUITE" paragraph into `agents_pointer_prose` and pasting the failure, then revert.
  - Depends on: E-04, E-06
  - Expected outcome: the new tests pass, the mutation fails (a); no test reads production source (all assertions are on installed files, the repository's `AGENTS.md`, probe return values and command output).
  - Execution state: performed

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
  - Carrier-Evidence: .aw/records/plans/executed/20261006-instbugs-05-xzlu9b-install-the-inbox-lane-and-its-tracked-readme-into-every-tar.ipd.md
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

- [x] V-01 validates E-01
  - Required evidence: PASTE, for both layouts, the pre-edit `wc -l`, grep inventory and dangling-path list with the HEAD sha.
  - Observed evidence:
    Pre-edit execution HEAD sha: `aa776905dc015252dcf84af5ea65887442ee6ae3`.
    Modern layout (`aw`):
    `wc -l AGENTS.md`: 125 lines.
    Grep inventory of AW-only tokens:
    ```
    AGENTS.md:80:HOW TO RUN THE SUITE: run it BARE, as `python3 -m pytest` (or `make test`). Do NOT pass `-n0` (it disables xdist and makes the suite 4x-6x slower); do NOT pass `-q` (it compounds the `-q` in `pyproject.toml` into `-qq` and hides the test-pass summary); do NOT pass `-p no:randomly` (it disables test-order randomization). The test commands throughout this plan assume the `pyproject.toml` defaults.
    AGENTS.md:88:  aw oc run all                                # or a setid; oc_runipd.py verifies dependency depth
    AGENTS.md:89:  aw oc run --no-isolate-worktree <setid>      # runner_shared.py opt-out
    AGENTS.md:90:  aw agy run all                               # Antigravity equivalent (same queue semantics)
    AGENTS.md:95:When you execute a task or plan here you MUST: commit ONLY files you changed, limited to the paths you name, through `aw commit <plan> -- <paths>` (or `aw commit --no-plan -m <msg> -- <paths>` when no plan governs the change), never `git add -A`/bare/`-a`, and never push; when you report tests passed, paste the ACTUAL runner output (never claim success you did not run); write no em or en dashes in USER-FACING prose you author (READMEs, CHANGELOG, docs meant for end users) - this keeps user-facing text from reading as machine-written; it does NOT apply to internal or AI-facing artifacts (IPDs/plans, research findings, prompts, specs, walkthroughs, commit messages, code comments), where you should spend no effort avoiding dashes. When asked to REVIEW or report, do NOT modify or commit anything: report and wait. Never change what a plan already in `.aw/records/plans/executed/` RECORDS (its steps, evidence, results, or status): close a post-execution gap with a new corrective IPD, not an in-place edit. You MAY append a dated `## Workflow history` line to it that points at later work (for example 'partly replaced by <id6>'), since that adds to the record without rewriting it. Never create or push a git tag, a GitHub Release, or a registry/PyPI upload except inside release-review Section 9 after an explicit human GO; no ad-hoc `git tag` or `git push --follow-tags`. See `CONTRIBUTING.md` and the release-review README for detail.
    AGENTS.md:98:TEST OUTCOMES, NOT CODE STRUCTURE (NO CODE-PINNING TESTS): every test you author, restore, or validate must test observable behavior and outcomes (see GUIDING_PRINCIPLES P16). Tests that pin code structure have no business existing: (1) NEVER write or restore tests that read production source code using `inspect`, `ast`, regex, or substring search; (2) NEVER assert on caller counts, symbol censuses, or module line counts as a proxy for correctness; (3) NEVER assert that specific text, docstrings, or comment banners remain unchanged in a script; (4) restored coverage must always exercise the code (calling functions, driving CLI commands, running subprocesses) and assert on real outputs, exit codes, and side effects.
    AGENTS.md:104:When you author or execute an Implementation Plan Document (IPD), do NOT hand-number ids or hand-place checklists: use the tools and follow the canonical spec. `aw ipd scaffold` writes a conformant skeleton, `aw ipd sync` assigns `E-*`/`V-*` ids + validation skeletons, and `aw ipd lint` deterministically checks structure/state. The EXACT structural contract (section order, the execution + validation checklists, the E/V bijection, states, metadata, and the lifecycle transaction) lives in the `ipd-spec` doc under `.aw/records/specs/`; the `ipd-lifecycle` workflow gates execution and the terminal transition. Completion rule: do NOT claim done or move a plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every validation item is verified with concrete evidence (tests run, actual output pasted).
    ```
    Dangling paths in target:
    `oc_runipd.py`, `runner_shared.py`, `pyproject.toml`, `CONTRIBUTING.md`, `RELEASING.md`.

    Legacy layout (`legacy`):
    `wc -l AGENTS.md`: 125 lines.
    Same AW-only tokens plus dangling `.aw/inbox/` and `.aw/records/plans/pending/`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the E-01 grep re-run on a post-edit fresh target of each layout (no hits); `grep -n "HOW TO RUN THE SUITE\|<!-- /aw:block -->" AGENTS.md` in this repository showing the suite line number is greater than the close marker's; and the output of a one-liner asserting `engine.agents_managed_block(target_layout="aw").strip()` is a substring of this repository's `AGENTS.md`.
  - Observed evidence:
    Post-edit fresh target grep re-run for AW-only tokens (`python3 -m pytest|pyproject|RELEASING.md|CONTRIBUTING.md|GUIDING_PRINCIPLES|oc_runipd.py|runner_shared.py|ipd-spec`):
    - Layout `aw`: 0 hits (excluding legitimate installed specs README `.aw/records/specs/README.md`)
    - Layout `legacy`: 0 hits
    `grep -n "HOW TO RUN THE SUITE\|<!-- /aw:block -->" AGENTS.md` in this repository:
    ```
    125:<!-- /aw:block -->
    255:deliberately BELOW the `<!-- /aw:block -->` marker, outside every managed block, because it names
    286:deliberately BELOW the `<!-- /aw:block -->` marker, outside every managed block, because it contains
    289:HOW TO RUN THE SUITE: run it BARE, as `python3 -m pytest` (or `make test`). Do NOT bolt on flags to 'help'...
    ```
    Suite line 289 > close marker line 125.
    Substring one-liner output:
    ```
    OK: agents_managed_block is exact substring of AGENTS.md
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the rephrased runner, IPD-contract and test-command paragraphs from a post-edit fresh target of each layout, and the legacy target's dangling list showing neither `.aw/inbox/` nor `.aw/records/plans/pending/`.
  - Observed evidence:
    Layout `aw`:
    ```markdown
    ### The runners own ordering, isolation, and orchestrators (do NOT re-derive this)
    Before you warn a human about running plans unattended, know what `aw oc run` / `aw agy run` ALREADY GUARANTEE, and consult `aw host capabilities` and `aw oc run --help` rather than inferring runtime behavior from plan prose.

    ### Authoring and executing IPDs
    When you author or execute an Implementation Plan Document (IPD), do NOT hand-number ids or hand-place checklists: use the tools and follow the canonical spec. `aw ipd scaffold` writes a conformant skeleton, `aw ipd sync` assigns `E-*`/`V-*` ids + validation skeletons, and `aw ipd lint` deterministically checks structure/state. The EXACT structural contract (section order, the execution + validation checklists, the E/V bijection, states, metadata, and the lifecycle transaction) is described in `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md`, `.aw/records/plans/README.md`, and `aw ipd --help`; the `ipd-lifecycle` workflow gates execution and the terminal transition. Completion rule: do NOT claim done or move a plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every validation item is verified with concrete evidence (tests run, actual output pasted).

    HOW TO RUN THE TEST SUITE: run the project's own test command (discovered by `/setup-repo` or the project's docs), and paste the actual runner output (never claim success you did not run).
    ```
    Layout `legacy`:
    ```markdown
    ### The runners own ordering, isolation, and orchestrators (do NOT re-derive this)
    Before you warn a human about running plans unattended, know what `aw oc run` / `aw agy run` ALREADY GUARANTEE, and consult `aw host capabilities` and `aw oc run --help` rather than inferring runtime behavior from plan prose.

    ### Authoring and executing IPDs
    When you author or execute an Implementation Plan Document (IPD), do NOT hand-number ids or hand-place checklists: use the tools and follow the canonical spec. `aw ipd scaffold` writes a conformant skeleton, `aw ipd sync` assigns `E-*`/`V-*` ids + validation skeletons, and `aw ipd lint` deterministically checks structure/state. The EXACT structural contract (section order, the execution + validation checklists, the E/V bijection, states, metadata, and the lifecycle transaction) is described in `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md`, `.agents/plans/README.md`, and `aw ipd --help`; the `ipd-lifecycle` workflow gates execution and the terminal transition. Completion rule: do NOT claim done or move a plan to `.agents/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every validation item is verified with concrete evidence (tests run, actual output pasted).

    HOW TO RUN THE TEST SUITE: run the project's own test command (discovered by `/setup-repo` or the project's docs), and paste the actual runner output (never claim success you did not run).
    ```
    Legacy target managed block check:
    `.aw/inbox/` in managed block: False
    `.aw/records/plans/pending/` in managed block: False
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE `aw doctor --json` filtered to rule `doctor.dangling-doc-reference` on a fresh target of each layout (empty) and on the planted-missing-path target (the finding naming file and token); the install output's advisory line for the planted case (or the clean case printing none); and `check_engine.rule_spec("doctor.dangling-doc-reference").severity` printing `info`.
  - Observed evidence:
    Fresh target modern layout (`aw`) `doctor --json` diagnostics with `doctor.dangling-doc-reference`:
    ```json
    []
    ```
    Fresh target legacy layout (`legacy`) `doctor --json` diagnostics with `doctor.dangling-doc-reference`:
    ```json
    []
    ```
    Planted missing path (`docs/missing.md` in `.aw/records/plans/README.md`) `doctor --json`:
    ```json
    [
      {
        "location": ".aw/records/plans/README.md",
        "rule": "doctor.dangling-doc-reference",
        "detail": "docs/missing.md",
        "severity": "info",
        "fix": "the installed doc .aw/records/plans/README.md references 'docs/missing.md' which does not exist in the target repository."
      }
    ]
    ```
    Install output advisory line for planted case:
    `WARN     .aw/records/plans/README.md: dangling reference to missing path docs/missing.md`
    Install output advisory line for clean case: none printed.
    Rule spec severity:
    ```
    $ python3 -c "from agent_workflows import check_engine; print(check_engine.rule_spec('doctor.dangling-doc-reference').severity)"
    info
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
    Narrowed run of new test file:
    ```
    $ python3 -m pytest -o addopts="" -m slow tests/test_agents_block_target_neutral.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=254275969
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 5 items

    tests/test_agents_block_target_neutral.py .....                          [100%]

    ============================== 5 passed in 20.81s ==============================
    ```
    Mutation failure (`HOW TO RUN THE SUITE: run it BARE, as python3 -m pytest` restored to `agents_pointer_prose`):
    ```
    FAIL: test_fresh_install_managed_block_contains_no_aw_only_tokens (tests.test_agents_block_target_neutral.AgentsBlockTargetNeutralTests.test_fresh_install_managed_block_contains_no_aw_only_tokens) (layout='aw')
    (a) Assert installed managed block contains none of the AW-only tokens in either layout.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "tests/test_agents_block_target_neutral.py", line 113, in test_fresh_install_managed_block_contains_no_aw_only_tokens
        self.assertNotIn(tok, managed_block, f"AW-only token {tok!r} found in installed managed block for layout {layout}")
    AssertionError: 'python3 -m pytest' unexpectedly found in ... : AW-only token 'python3 -m pytest' found in installed managed block for layout aw
    ```
    Bare-suite summary line against baseline:
    Baseline: `6772 passed, 2 skipped, 3 warnings in 463.67s (0:07:43)`
    Observed: `6772 passed, 2 skipped, 3 warnings in 180.14s (0:03:00)`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE the `grep -rln` census of tests touching the pointer prose, the narrowed run of each listed file after the change (all pass), and the diff of `tests/test_suite_instruction_marker_parity.py`.
  - Observed evidence:
    `grep -rln` census:
    ```
    $ grep -rln "agents_pointer_prose\|agents_managed_block\|update_agents_pointer" tests/
    tests/test_suite_instruction_marker_parity.py
    tests/test_authoring_coverage_guidance.py
    ```
    Narrowed test run of listed files:
    ```
    $ python3 -m unittest tests/test_suite_instruction_marker_parity.py tests/test_authoring_coverage_guidance.py
    .......
    ----------------------------------------------------------------------
    Ran 7 tests in 9.266s

    OK
    ```
    Diff of `tests/test_suite_instruction_marker_parity.py`:
    ```diff
    --- a/tests/test_suite_instruction_marker_parity.py
    +++ b/tests/test_suite_instruction_marker_parity.py
    @@ -3,9 +3,9 @@
     P16 compliance note:
     pyproject.toml is build configuration, not production code (agent_workflows/*.py).
     P16's narrow exception permits content verification where the text or file itself is
    -the artifact under test, which applies here because the instruction text emitted by
    -engine.agents_pointer_prose is the installed artifact. Asserting on the return value
    -of agents_pointer_prose is a behavioral assertion on a pure function.
    +the artifact under test, which applies here because the instruction text in this repository's
    +AGENTS.md is the repo-local rule artifact, and agents_pointer_prose return values are tested
    +behaviorally.
     Production source (agent_workflows/engine.py) is not read with read_text(), inspect,
     ast, or substring search.
     """
    @@ -31,27 +31,37 @@ def extract_configured_marker_expr(pyproject_content: str) -> str:


     class SuiteInstructionMarkerParityTests(unittest.TestCase):
    -    """Ensure engine.agents_pointer_prose accurately quotes pyproject addopts marker filter."""
    +    """Ensure AGENTS.md repo-local region accurately quotes pyproject addopts marker filter."""

         def test_instruction_quotes_configured_addopts_marker_filter(self):
             pyproject_path = REPO_ROOT / "pyproject.toml"
             content = pyproject_path.read_text(encoding="utf-8")
             marker_expr = extract_configured_marker_expr(content)

    -        # Assert over both supported layouts (aw and legacy)
    -        for layout in ("aw", "legacy"):
    -            prose = engine.agents_pointer_prose(target_layout=layout)
    +        # 1. Configured marker expression appears in this repository's AGENTS.md repo-local region
    +        agents_content = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    +        parsed = engine.parse_aw_block(agents_content)
    +        self.assertTrue(parsed.found, "AGENTS.md must contain well-formed aw:block")
    +        repo_local = parsed.after

    -            # 1. Configured marker expression appears verbatim in prose
    -            self.assertIn(
    -                marker_expr,
    -                prose,
    -                f"Configured marker expression {marker_expr!r} missing in layout={layout} prose",
    -            )
    +        self.assertIn(
    +            marker_expr,
    +            repo_local,
    +            f"Configured marker expression {marker_expr!r} missing in AGENTS.md repo-local region",
    +        )

    -            # 2. Exact stale fragment -m 'not slow' does not appear
    +        # 2. Exact stale fragment -m 'not slow' does not appear in repo-local region
    +        self.assertNotIn(
    +            "-m 'not slow'",
    +            repo_local,
    +            f"Stale marker fragment \"-m 'not slow'\" found in AGENTS.md repo-local region",
    +        )
    +
    +        # 3. agents_pointer_prose for both layouts no longer contains pyproject.toml
    +        for layout in ("aw", "legacy"):
    +            prose = engine.agents_pointer_prose(target_layout=layout)
                 self.assertNotIn(
    -                "-m 'not slow'",
    +                "pyproject.toml",
                     prose,
    -                f"Stale marker fragment \"-m 'not slow'\" found in layout={layout} prose",
    +                f"Layout {layout} pointer prose must not contain pyproject.toml",
                 )
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: making the block neutral and adding the check that proves it neutral are one deliverable; the check without the cleanup would fail on every install, and the cleanup without the check would regress silently.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in dependency order (E-01, E-02, E-03, E-04, E-06, E-05). Commit only files changed for this plan through `aw commit ka0g86 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout (E-02's self-install may touch other managed files; stage only `AGENTS.md` from it). HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output does not satisfy any item. Run every real install with `AW_NO_REEXEC=1`, `HOME` pointed at a temp dir, and a git identity in the environment. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize ka0g86`, never by a hand `git mv`.
