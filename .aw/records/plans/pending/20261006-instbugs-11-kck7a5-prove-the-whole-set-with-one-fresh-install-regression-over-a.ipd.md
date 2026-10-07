# IPD: Prove the whole Set with one fresh-install regression over a scratch non-Python target

- Date: 2026-10-06
- Kind: child
- Concern: Set `instbugs` fixes the present-at-HEAD defects of research report `l6cbbb` across ten children, each with its own unit-level tests. The report's defects were found TOGETHER, by one fresh install into a package.json-only target, and several of them only show up as disagreements BETWEEN children's outputs: the preset's git policy (`gi1w75`), the files actually written (`pfub72`), what the install stages (`gzsfqn`) and what `.aw/.gitignore` ignores; whether the installed bundle is free of dangling references (the `ka0g86` check, over `xzlu9b` and `jbnkkh` content); and whether the research verbs compose (`zye6k4` numbering, `ic4eg0` mode, `okw4ke` check). Defects D02 and D06 and the fixed halves of D10, D13 and D15 were fixed before this Set and have no pin in it. Nothing in the suite today installs into a non-Python target and checks these outcomes end to end.
- Scope: IN: one regression test module that builds a scratch git repo containing only `package.json`, runs a fresh `aw install` with the private-target preset non-interactively, and asserts that every original observation of the report is gone (D01 version consistency, D02, D03, D04, D05, D06, D07, D08, D09, D10 check half, D11, D12, D14, D15, N1, N2), plus the three cross-child checks; a full bare suite run; a user-facing CHANGELOG entry. OUT: re-fixing anything (a failing assertion here sends the defect back to its owning child as a corrective plan); the wheel-build proof of D01 (owned by `whz0oi`'s own test, because building a wheel is too slow for this module); D13 companion files (backlog `bh1cy5`); the D15 upgrade-warning half and the D10 rename half, which already have pins (see Findings F-07).
- Scope-Paths: tests/test_fresh_target_install_regression.py, CHANGELOG.md
- Item-Dependencies: executed:whz0oi, executed:gzsfqn, executed:ka0g86, executed:okw4ke, executed:ic4eg0, executed:zye6k4
- Status: approved
- Readiness: go-pending-approval
- Blocks-Release: f33nrj
- Work-Kind: chore
- Priority: high
- Set: instbugs
- Order: 11
- Highest E allocated: 04
- Author: antigravity/claude-opus-5.5
- Id: kck7a5
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009. Reviewed at lane HEAD `7da9f9719`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Drove the whole E-02/E-03 scenario against HEAD in a scratch target (F-05..F-09): install 2.8 s, re-install 0.8 s, doctor 1.1 s, each research verb 0.5 s. Fixed: the consent plan is NOT printed on the `-y` path, only on `--dry-run`, so the D04 assertion was unobservable as written (PR-001); D14's "tracked or staged" contradicts the post-`gzsfqn` empty-porcelain bar, now "tracked", and the inbox drop step needs `xzlu9b` (PR-002); `aw doctor --format json` does not exist, now `--json` filtered to the `ka0g86` rule id rather than "reports zero" over all diagnostics (doctor exits 1 on unrelated drift) (PR-003); the six `Item-Dependencies` edges cover all ten siblings transitively (gi1w75 via gzsfqn->pfub72, xzlu9b/jbnkkh via ka0g86) and match the orchestrator table, but E-01 checked only the six, so E-01 now confirms all ten (PR-004); D10 check-half assertion is a CLI edit with no reachable `order:`-only mismatch until `okw4ke`, made explicit, and the `aw adopt` invocation spelled out (PR-005); 15 s marker rule could not be met by a module that installs, now decided up front as `slow` (PR-006); STOP clause reframed as an unsafe-condition stop (PR-007); `- Blocks-Release: next`, since this plan is the Set's proof and the Set gates `next` (PR-008); gate gains resolved-OQ statement, honesty rule, scope fence, temp HOME and conditional finalize ownership (PR-009).
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 11 of Set `instbugs`, the whole-Set proof, from the orchestrator's Findings triage and its cross-IPD validation list.

## Goal

One test re-creates the report's situation (a fresh install into a non-Python repo) and proves every defect it found is gone and stays gone, including the ones fixed before this Set, and the full suite passes with the Set merged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [ ] E-01 Record the baseline at the execution HEAD: confirm with `aw find plans <id6>` that all ten other children of Set `instbugs` (the six direct `Item-Dependencies` and the four they reach transitively) are under `executed/`; run the bare suite `python3 -m pytest` and paste the summary line; run one manual scratch install (package.json-only temp git repo, `AW_NO_REEXEC=1`, `HOME` pointed at a temp dir, git identity in env, first `aw install . --dry-run --preset private-target -y --no-interactive` to capture the consent plan, then `aw install . --preset private-target -y --no-interactive`) and paste the consent plan's "Resolved Physical Classes" lines, `git status --short --ignored`, `stat -c '%a %n'` of any record created, and the install log tail. STOP and report if any of them is not executed, because the module's assertions would then encode the unfixed state.
  - Depends on: none
  - Expected outcome: the baseline suite summary and the manual install observations pasted with the HEAD sha.
  - Execution state: pending

### Task group 2: the regression module

- [ ] E-02 Add `tests/test_fresh_target_install_regression.py`, marked `pytestmark = pytest.mark.slow` (OQ-01). Install-level part: one module-scoped fixture builds a package.json-only temp git repo with a committed initial commit, sets `AW_NO_REEXEC=1`, `HOME` and `XDG_CONFIG_HOME` to a distinctively named temp dir and a git identity in the subprocess env, runs `python -m agent_workflows install . --dry-run --preset private-target -y --no-interactive` (captures the consent plan), then the same without `--dry-run` (captures the install output), all as subprocesses. Tests then assert on the target and the captured output, each assertion message naming its defect id:
  - D01/N2: the `installed_version` in `.aw/state/durable/install.json` equals the version printed by `python -m agent_workflows --version` in the same env, and neither that file nor `.aw/state/durable/history/installs.jsonl` contains the temp HOME path.
  - D02: `git check-ignore -q` succeeds for `.aw/state/durable/install.json` and `.aw/config/local.json`.
  - D03/N1: `git status --porcelain` after the `-y` install is empty; the captured install output's "Gitignore (run scratch)" line says "is ignored" and `git check-ignore -q .aw/workflow-artifacts/README.md` succeeds; the output does not contain "STAGED but NOT committed".
  - D04: every target path printed under "Resolved Physical Classes" in the `--dry-run` output exists after the real install (file for config classes, directory or its parent for state classes).
  - D05: `.aw/state/` holds no `install.json` or `history/installs.jsonl` at its root; each exists under `.aw/state/durable/`.
  - D06: no root `workflow-artifacts/` directory.
  - D07: the managed AGENTS.md block (between `<!-- aw:block -->` and `<!-- /aw:block -->`) names none of `python3 -m pytest`, `RELEASING.md`, `oc_runipd.py`.
  - D08/D09: no `\.agents/(plans|prompts|comms|docs|workflows)` match in the install output, `.gitignore`, `.aw/.gitignore` or any file under `.aw/records/`; the installed research README does not present `intake` as a current status.
  - D14: `git ls-files .aw/inbox/README.md` lists it; a file written to `.aw/inbox/drop.md` is reported ignored by `git check-ignore -q`.
  - D15 (TRACKING TRUTH TABLE): for each physical class in `project.json` `git_policies`, a class with policy `target-git` has every on-disk file tracked (`git ls-files`), and a class with policy `ignored` has every on-disk file reported by `git check-ignore`; in particular `state_durable` is `ignored`.
  - Dangling references: `python -m agent_workflows doctor --json --dir <target>` returns a `diagnostics` list with no entry whose `rule` is the dangling-reference rule id `ka0g86` registers (`doctor.dangling-doc-reference` per its plan; use the shipped id). Do NOT assert doctor's exit code: it exits 1 on unrelated drift in a fresh target (measured: `doctor.git-staged` before the commit).
  - Depends on: E-01
  - Expected outcome: every assertion passes; each assertion's message names the defect id so a regression points at its owner.
  - Execution state: pending

- [ ] E-03 Same module, research-composition part, in the same installed target, every subprocess run with `preexec_fn=lambda: os.umask(0o022)` (POSIX; skip on Windows): `python -m agent_workflows research new --kind research-report --set newset --slug a --apply`; then write `.aw/inbox/drop.md` and run `python -m agent_workflows adopt .aw/inbox/drop.md --type research --kind research-report --set otherset --slug b --apply --yes`. Assert both written filenames carry `-01-` and front matter `order: 01` (D12), both files have mode `0o644` (D11), and `research index --check` exits 0. Then rewrite one file's front matter to `order: 05` (leaving its filename `-01-`) and assert `research index --check` exits non-zero and its output names `order` (D10 check half, delivered by `okw4ke`). Record the module's wall time in the evidence.
  - Depends on: E-02
  - Expected outcome: all composition assertions pass; the module's wall time recorded.
  - Execution state: pending

### Task group 3: close

- [ ] E-04 Prove the module can fail: in the working tree, temporarily revert one child's fix (for example restore the `0o600` mode in `artifact_core.atomic_write`), run the module narrowed, paste the D11-named failure, then restore the file with `git checkout -- <path>` and confirm `git status` shows it clean. Add a CHANGELOG.md entry under the pending `## 2.0.0 (pending)` section describing the fixed install and research problems in user terms with no em or en dashes. Run the bare suite `python3 -m pytest` and paste its summary against the E-01 baseline, plus the narrowed `slow` run of the new module.
  - Depends on: E-03
  - Expected outcome: the mutation fails with a defect-named message and is reverted; the CHANGELOG entry exists; the full suite passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `pyproject.toml` `addopts` deselects `slow` and `livecorpus` by default; `make test-all` runs everything. A slow end-to-end install test belongs under `slow` so the default suite stays fast (precedent: `tests/test_installer.py` `pytestmark = pytest.mark.slow`).
- `aw` re-execs into a checkout's package when run inside a checkout; tests that drive an installed target set `AW_NO_REEXEC=1`.
- The suite already installs into temp git repos in other tests (`tests/support.py` `init_repo`, `run_installer`); the fixture follows that pattern and installs once per module.
- User-facing prose (CHANGELOG) carries no em or en dashes.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16): every assertion here is on installed files, git state, file modes and CLI output.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The defects were found by one composed install, not per unit. | research report `l6cbbb` (one install into a Node target); orchestrator `i99ykd` Findings table |
| F-02 | D02, D06 and the fixed halves of D10, D13, D15 have no pin in this Set. | orchestrator `i99ykd` Deferred: "`kck7a5`'s regression test pins the D02 and D06 outcomes so they cannot regress" |
| F-03 | Cross-child agreement is only observable end to end. | orchestrator `i99ykd` cross-IPD validation: "THE TRACKING TRUTH TABLE AGREES END TO END ... Performed by `kck7a5` E-02"; "THE RESEARCH VERBS COMPOSE ... Performed by `kck7a5` E-03" |
| F-04 | Wheel builds are too slow for this module. | `whz0oi` owns the wheel-build proof of D01; this module checks version consistency in the running environment |
| F-05 | (review) The consent plan is printed only on `--dry-run` or interactively. | `cli._run_install` prints `render_pre_write_plan` under `if getattr(args, "dry_run", False)`; `install_wizard.collect_policy_interactive` prints it on its interactive branch; a scratch `-y` install output contains no "Resolved Physical Classes" line, the `--dry-run` output does |
| F-06 | (review) The whole scenario reproduces the open defects at HEAD `7da9f9719`. | scratch target: `?? .aw/config/` after `-y` (D03); four state files incl. root `install.json` (D05); `installed_version` `2026.8.10` (N2); consent plan `.aw/config_project` (D04); `research new` and `adopt` both `-00-` and `0o600` (D12, D11); `research index --check` clean |
| F-07 | (review) Already-pinned fixed halves. | D15 upgrade warning: `tests/test_installer.py` asserts "ALREADY git-tracked"; D10 rename half: `tests/test_research_rename_frontmatter.py` `test_regroup_updates_set_and_order_frontmatter` |
| F-08 | (review) `aw doctor` has `--json`, not `--format json`, and exits 1 on a fresh target for unrelated reasons. | `aw doctor --help` options; scratch run rc 1 with `doctor.git-staged` diagnostics |
| F-09 | (review) Timings make a 15 s budget unreachable with margin. | scratch: install 2.8 s, re-install 0.8 s, doctor 1.1 s, `--version`/`research new`/`adopt`/`index --check` 0.5 s each, plus a `--dry-run` install; about 8 s on an idle machine before any xdist contention |

## Proposed changes (ordered, validatable)

1. Baseline (E-01).
2. Install-level regression assertions (E-02).
3. Research-composition assertions (E-03).
4. Mutation proof, CHANGELOG, full suite (E-04).

## Deferred / out of scope (with reason)

- D13 companion files: a feature, not a defect.
  - Carrier: bh1cy5
- The wheel-build proof of D01.
  - Carrier: whz0oi

## Scope check

- Over-scope: none.
- Under-scope: none; every row of the orchestrator's Findings table has an assertion here, an existing pin (F-07), or a named carrier.

## Required tests / validation

- `tests/test_fresh_target_install_regression.py` (E-02, E-03) with the mutation proof (E-04), run narrowed as `python3 -m pytest -o addopts="" -n auto tests/test_fresh_target_install_regression.py`.
- Bare `python3 -m pytest` summary line pasted against the E-01 baseline (E-04).

## Spec / documentation sync

- CHANGELOG.md entry (E-04). No spec change: each child carries its own spec sync.

## Open questions

### OQ-01: Should the regression run in the default suite or under `slow`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED at review: `slow`. The module performs two installs (dry-run and real), a doctor run and five more CLI subprocesses, measured at about 8 s idle (F-09); every existing real-install module is `slow` (`tests/test_installer.py`); the maintainer has asked for a fast default suite. It runs under `make test-all` and the narrowed command above.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the ten `aw find plans` lines showing `executed/`, the baseline suite summary line, and the manual install observations (consent plan lines, `git status --short --ignored`, modes, log tail) with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the narrowed run of the install-level tests (`python3 -m pytest -o addopts="" tests/test_fresh_target_install_regression.py -k install -v`) showing each defect-named test passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the narrowed run of the composition tests (`-k research -v`) and the module's measured wall time.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the defect-named mutation failure, the `git status` showing the mutation reverted, the CHANGELOG entry text, and the bare-suite summary line from `python3 -m pytest` against the E-01 baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one regression module and the Set's closing suite run; it carries no fix of its own.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in order (E-01 to E-04). Commit only files changed for this plan through `aw commit kck7a5 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output does not satisfy any item. Run every real install with `AW_NO_REEXEC=1`, `HOME` pointed at a temp dir, and a git identity in the environment. NO FIXES HERE: if an assertion fails because a child's fix is incomplete, do not weaken the assertion and do not patch the child's code in this plan; report the defect id and owning child and leave the corrective IPD to the maintainer (this is an unsafe-condition stop, not a scope-fence stop). SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize kck7a5`, never by a hand `git mv`.
