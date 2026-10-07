# IPD: Fix the fresh-target install and research-tooling defects found in a downstream install

- Date: 2026-10-06
- Kind: orchestrator
- Concern: Research report `l6cbbb` (`.aw/records/research/20261006-instbugs-00-l6cbbb-fresh-target-install-defects.research-report.md`) lists fifteen defects (D01 to D15) observed while installing AW into a private Node target. The install it describes ran a build 6424 commits stale, so every defect was RE-REPRODUCED at HEAD `474b037a9` before planning: HEAD was built with `pip install .` into a throwaway venv under `/tmp`, a scratch git repo with only `package.json` (an `npm test` script) and `.gitignore` was created, and `aw install . --preset private-target -y --no-interactive` was run with `AW_NO_REEXEC=1`, then the research verbs, `aw adopt`, and an upgrade over a simulated stale install were exercised. Eleven defects (plus two new ones found during reproduction) are present at HEAD; four are fixed at HEAD; one half of D13 is a feature request. The triage table is in Findings.
- Scope: ORCHESTRATION ONLY. This plan sequences eleven child plans and contributes no implementation, no test and no deliverable of its own. Every artifact is owned by exactly one child named in the child table. IN: dependency order, the triage that assigns each present-at-HEAD defect to exactly one child, the Set-level completion criteria with the owning child of each, and the cross-child checks with the owning child of each. OUT: everything the children do (listed per row in the child table), and the D13 companion-file feature, recorded as backlog `bh1cy5`.
- Scope-Paths: .aw/records/plans/pending/20261006-instbugs-00-i99ykd-fix-the-fresh-target-install-and-research-tooling-defects-fo.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 5891d6bc5dee78106d0c0e40f9cb0c8ed4aae79fe167b54d977f5074ae15da0b
- Coverage-Checked: 2026-10-06 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: instbugs
- Order: 0
- Highest E allocated: 11
- Author: antigravity/claude-opus-5.5
- Id: i99ykd

## Workflow history
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0
- 2026-10-07 reviewed (aw set): plan-review

- 2026-10-06 coverage pass (aw oc run): fingerprint 5891d6bc5dee, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-06 coverage fail (aw oc run): fingerprint 889a94431aa7, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003. Reviewed at HEAD `fe2ee961c` in an isolated review-sweep lane; plan committed and byte-identical to the lane input, so no pre-review snapshot. Verified: all eleven children exist in `pending/` with Orders, `- Item-Dependencies:` edges and Kind matching the child table; `aw ipd coverage i99ykd` ready; triage spot-checks at HEAD agree (`.aw/system/VERSION` = `1.2.1`; `install_wizard.py` `f"{repo_formatted}/.aw/{cls}"` and literal `"installed_version": "2026.8.10"`; `.aw/.gitignore` `/inbox/` and `/state/`; `research_cmd._next_order_for_set` returns 0 for a new set); `kck7a5` E-items pin D02 and D06 as the Deferred row claims; backlog `bh1cy5` open. Fixed: deferred row 3 `Carrier: none (...)` was a malformed carrier that made `check.ipd-uncarried-obligation` (severity `error`) fire on this plan, replaced with `Carrier-Declined:` (PR-001); live-bug release gate absent on this plan and on ten bug children, contrary to AGENTS.md 'Every live bug gates the next release' - this plan gains `- Blocks-Release: next`; the ten bug children's missing gate is recorded in the review record and reported to the maintainer, not in this plan, since those files are outside this review's ledger and the coverage gate correctly refuses parent text that implies child work (PR-002); gate gains resolved-OQ statement, pasted-output honesty rule, scope fence as declaration and conditional finalize/retirement ownership (PR-003).

- 2026-10-06 coverage pass (aw oc run): fingerprint 5891d6bc5dee, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored from research report `l6cbbb` after reproducing every defect at HEAD `474b037a9` in a throwaway venv and scratch target (evidence in Findings). The maintainer ruled the one product decision (D12 numbering) interactively on 2026-10-06; recorded in child `zye6k4` OQ-01.

## Goal

Make a fresh `aw install` into a non-Python target produce a correct, honest, leak-safe install: the version it reports is the code that runs, the consent plan and the ignore rules agree on what is tracked, every tracked file is staged, every ignored class is ignored, no installed text points at retired paths or at files the target does not have, the inbox lane exists, and the research verbs write records with correct names, frontmatter and file modes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: orchestration of the instbugs Set

- [ ] E-01 CONFIRM whz0oi REACHED executed
  - Depends on: none
  - Expected outcome: child 01 (`whz0oi`, version reporting, D01) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-02 CONFIRM gi1w75 REACHED executed
  - Depends on: none
  - Expected outcome: child 02 (`gi1w75`, consent plan paths and tracking policy, D04 and D15) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-03 CONFIRM pfub72 REACHED executed
  - Depends on: E-02
  - Expected outcome: child 03 (`pfub72`, state records written once, D05 and N2) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-04 CONFIRM gzsfqn REACHED executed
  - Depends on: E-03
  - Expected outcome: child 04 (`gzsfqn`, post-install report and staging, D03 and N1) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-05 CONFIRM xzlu9b REACHED executed
  - Depends on: none
  - Expected outcome: child 05 (`xzlu9b`, inbox lane, D14) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-06 CONFIRM jbnkkh REACHED executed
  - Depends on: none
  - Expected outcome: child 06 (`jbnkkh`, stale installed text, D08 and D09) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-07 CONFIRM ka0g86 REACHED executed
  - Depends on: E-05, E-06
  - Expected outcome: child 07 (`ka0g86`, target-neutral AGENTS.md block and dangling-reference check, D07) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-08 CONFIRM okw4ke REACHED executed
  - Depends on: none
  - Expected outcome: child 08 (`okw4ke`, research index drift detection, D10) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-09 CONFIRM ic4eg0 REACHED executed
  - Depends on: none
  - Expected outcome: child 09 (`ic4eg0`, atomic write file modes, D11) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-10 CONFIRM zye6k4 REACHED executed
  - Depends on: none
  - Expected outcome: child 10 (`zye6k4`, research numbering, D12) is `executed` with its validation evidence present.
  - Execution state: pending

- [ ] E-11 CONFIRM kck7a5 REACHED executed
  - Depends on: E-01, E-04, E-07, E-08, E-09, E-10
  - Expected outcome: child 11 (`kck7a5`, the whole-Set fresh-install regression and full suite) is `executed` with its validation evidence present.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `whz0oi` | `20261006-instbugs-01-whz0oi-report-the-version-of-the-build-that-is-actually-executing-a.ipd.md` | D01: an installed build reports its own distribution version (today it reports the stale committed `.aw/system/VERSION`), and `aw doctor` warns when a local-directory build is behind its source checkout. | none |
| 02 | `gi1w75` | `20261006-instbugs-02-gi1w75-make-the-install-consent-plan-show-real-paths-and-the-tracki.ipd.md` | D04 and D15: the consent plan shows the physical paths that are written, and the preset tables declare `state_durable` with the git policy the shipped `.aw/.gitignore` actually applies. | none |
| 03 | `pfub72` | `20261006-instbugs-03-pfub72-write-each-install-state-record-once-in-the-state-class-the.ipd.md` | D05 and N2: one writer for the install snapshot and history, in `state/durable/`, carrying the real version and no absolute paths; upgrade removes the duplicate root copies. | 02 |
| 04 | `gzsfqn` | `20261006-instbugs-04-gzsfqn-make-the-post-install-report-match-what-was-written-staged-c.ipd.md` | D03 and N1: every installer-written file in a tracked class is staged and listed; the run-scratch advisory is computed after the ignore file is written; the staged-versus-committed message is truthful. | 03 |
| 05 | `xzlu9b` | `20261006-instbugs-05-xzlu9b-install-the-inbox-lane-and-its-tracked-readme-into-every-tar.ipd.md` | D14: install creates `.aw/inbox/` with a tracked README, the ignore rule becomes `/inbox/*` plus `!/inbox/README.md` (with back-fill), and the README is packaged. | none |
| 06 | `jbnkkh` | `20261006-instbugs-06-jbnkkh-remove-retired-paths-statuses-and-naming-rules-from-installe.ipd.md` | D08 and D09: installed READMEs, the root `.gitignore` block and install messages stop citing retired `.agents/` paths, the `intake` status and the legacy spec naming, with a bundle scan test. | none |
| 07 | `ka0g86` | `20261006-instbugs-07-ka0g86-make-the-managed-agents-md-block-target-neutral-and-refuse-d.ipd.md` | D07: the managed AGENTS.md block written into a target carries no AW-repository development contract, and a check refuses installed agent docs that cite a file the target does not have. | 05, 06 |
| 08 | `okw4ke` | `20261006-instbugs-08-okw4ke-make-research-index-check-catch-order-kind-and-model-mismatc.ipd.md` | D10 (the part present at HEAD): `aw research index --check` reports `order`, `kind` and `model` filename-versus-frontmatter mismatches, as its README promises. | none |
| 09 | `ic4eg0` | `20261006-instbugs-09-ic4eg0-give-atomically-written-records-the-normal-umask-mode-instea.ipd.md` | D11: `artifact_core.atomic_write` and every other atomic writer of a tracked record produce `0o666 & ~umask` (or preserve an existing mode); private files stay private by explicit decision per site. | none |
| 10 | `zye6k4` | `20261006-instbugs-10-zye6k4-number-the-first-non-prompt-document-in-a-new-research-set-0.ipd.md` | D12: a non-prompt document opening a new research set gets `01`; `aw research new` and `aw adopt` gain `--order`; spec Section 5.1 amended (maintainer ruling 2026-10-06). | none |
| 11 | `kck7a5` | `20261006-instbugs-11-kck7a5-prove-the-whole-set-with-one-fresh-install-regression-over-a.ipd.md` | Whole-Set proof: one end-to-end regression test that builds a scratch non-Python target, installs, and asserts every original observation is gone; plus the full suite run. | 01, 04, 07, 08, 09, 10 |

WHY THE EDGES: 03 after 02 because 03 writes the durable snapshot into the class whose git policy 02 settles, and both edit `install_wizard.py`. 04 after 03 because what 04 stages depends on which state files exist and in which class. 07 after 05 and 06 because 07's dangling-reference check scans every installed agent-facing doc, so it must land after 06 fixes the stale citations and 05 adds the inbox README, or it would fail on the tree it is introduced into. 11 depends on every leaf it observes.

## Findings

Triage of report `l6cbbb`, reproduced at HEAD `474b037a9` (2026-10-06). "Present" means reproduced against a fresh HEAD build, not inferred from the stale build.

| # | Defect | Classification | Evidence at HEAD | Owner |
|---|---|---|---|---|
| D01 | Reported version is not the installed code | present-at-HEAD (different cause than the report guessed) | Fresh HEAD wheel: `pip show` gives `1.3.0rc2.dev8193+g474b037a9`, `aw --version` run from `/tmp` gives `agent-workflows 1.2.1`. The wheel's bundled `_data/.aw/system/VERSION` contains `1.2.1`, the committed file, because `[tool.hatch.build.targets.wheel.force-include]` copies `.aw/system` verbatim and nothing bakes the resolved version into it; `agent_workflows/__init__.py` `_resolve_own_version` reads that bundled file. | `whz0oi` |
| D02 | `ignored` placements not ignored | fixed-at-HEAD | Scratch install: `git status --short --ignored` shows `!! .aw/config/local.json` and `!! .aw/state/`; the `.aw/.gitignore` template carries anchored `/state/` and `/config/local.json` (engine.py template, comment beginning "The per-machine state tree and the machine-local config binding"). | none |
| D03 | Tracked placements not staged | present-at-HEAD | After `aw install ... -y` reported "Changes committed successfully", `git status --short` shows `?? .aw/config/`; `git ls-files .aw/config` is empty. `engine.prompt_and_run_commit` is passed `result["installed"]`, which does not contain the wizard-written `project.json`. | `gzsfqn` |
| D04 | Consent plan shows paths never created | present-at-HEAD | `install_wizard.py`: after resolving `ctx.physical_classes`, the loop over `ROOT_CLASSES` unconditionally overwrites each target entry with `f"{repo_formatted}/.aw/{cls}"`, i.e. `.aw/config_project`, `.aw/state_runtime`. | `gi1w75` |
| D05 | Runtime state at `.aw/state/` root, duplicated into durable | present-at-HEAD | Scratch install tree contains both `.aw/state/install.json` and `.aw/state/durable/install.json`, both `history/installs.jsonl`. Two writers: `install_history.record_install_history` (logical `state` root) and the wizard's step 3/4 (`durable_state_dir`). | `pfub72` |
| D06 | Retired root `workflow-artifacts/` created | fixed-at-HEAD | Fresh install creates only `.aw/workflow-artifacts/README.md`; an upgrade over a target with a committed stray `workflow-artifacts/README.md` removed it ("removed: superseded stray README"). Fixed by `y4pptx` (wfartifacts Order 05, commit `7eaff748c`). | none |
| D07 | AGENTS.md carries AW's own contract | present-at-HEAD | Scratch target `AGENTS.md` line 80 "HOW TO RUN THE SUITE: run it BARE, as `python3 -m pytest`"; cites `RELEASING.md`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES`, the `ipd-spec`, and `oc_runipd.py`/`runner_shared.py` symbols; none exist in the target. Source: `engine.agents_pointer_prose`. | `ka0g86` |
| D08 | Research README `intake`, dangling spec citation | present-at-HEAD | Installed `.aw/records/research/README.md` lines 38/43/44 still say `intake`; line 9 cites `.aw/records/specs/implemented/20260730-2152-01-...spec.md`, corrected for the source repo but absent in a target. Source: `.aw/system/workflows/templates/agents-docs-research-README.md`. | `jbnkkh` |
| D09 | Stale `.agents/` paths, contradictory spec naming | present-at-HEAD | Install log: "use the gitignored untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/" (engine.py) and "Read and execute .agents/workflows/index.md" (engine.py, cli.py); installed comms README line 1 `# .agents/comms/` and "spec under `.agents/docs/specs/`"; root `.gitignore` block "e.g. .agents/plans/pending/untracked/"; specs README "Named `YYYYMMDD-HHMM-NN-<slug>.md`". `.agents/skills/` is NOT stale (it is the cross-tool Agent Skills location the installer deliberately writes). | `jbnkkh` |
| D10 | set-assign leaves stale `order:`; `index --check` blind | split: rename half fixed-at-HEAD, check half present-at-HEAD | `set-assign --order 1` now rewrites `order: 01`/`02` (plan `ax8eg1`, commit `e21ba4378`). Hand-edited mismatch probe: `set` and `id` mismatches are reported, `order: 05` and `kind: findings` mismatches print `index --check: clean`. `research_index` compares only `id` and `set`. | `okw4ke` |
| D11 | Research writers create 0600 files | present-at-HEAD (research docs); fixed for INDEX | Under `umask 022`, `aw research new --apply` and `aw adopt --apply` produce `-rw-------`; `INDEX.json`/`INDEX.md` are now `-rw-r--r--`. `artifact_core.atomic_write` uses `tempfile.mkstemp` then `os.replace`. | `ic4eg0` |
| D12 | First doc in a new set gets `00` regardless of kind | present-at-HEAD | `aw research new --kind research-report --set acelmmkt` wrote `...-acelmmkt-00-...`; `aw adopt` also wrote `-00-` for a report. `research_cmd._next_order_for_set` returns 0 for an empty set. Spec `20260730-2152-01` contradicts itself (line 106 "`00` is the originating prompt" versus Section 5.1 "create a new set at `NN=00`"). Maintainer ruled 2026-10-06. | `zye6k4` |
| D13 | No adopt verb; no companion-file convention | split: adopt half fixed-at-HEAD, companion half feature request | `aw adopt` (plan `lznpv6`, Set awinbox) filed a dropped file whose body is a byte-exact suffix of the original (checked with a Python `endswith` over bytes: `True`). Companion convention: absent; recorded as backlog. | backlog `bh1cy5` |
| D14 | `.aw/inbox/` and README never installed | present-at-HEAD | Scratch install has no `.aw/inbox/`; packaged `_data/.aw/` holds only `system/`. In this repo `git check-ignore -v --no-index .aw/inbox/README.md` prints `.aw/.gitignore:28:/inbox/` while `git ls-files` lists it (force-added). | `xzlu9b` |
| D15 | Tracking-policy contradictions | split: policy contradiction present-at-HEAD; INDEX advice and upgrade warning fixed-at-HEAD | Scratch `project.json` declares `"state_durable": "target-git"` while `.aw/.gitignore` ignores `/state/` (D92 leak containment); the consent text says ".aw/state/durable created/updated" as a target delta. The research README now says INDEX files are GITIGNORED (idxuntrack `ila6vl`), and an upgrade over force-committed `state/durable/install.json` and `INDEX.json` printed "these files are ALREADY git-tracked ... git rm --cached <path>" (commit `86caa8830`). | `gi1w75` |
| N1 | (new) False "run scratch NOT ignored" advisory on fresh install | present-at-HEAD | Fresh install printed "Gitignore (run scratch): .aw/workflow-artifacts/ is NOT ignored" although `git status --ignored` shows `!! .aw/workflow-artifacts/`; the upgrade run printed "is ignored by .aw/.gitignore (correct...)". `check_gitignore(plan)` is evaluated before the framework `.aw/.gitignore` exists. | `gzsfqn` |
| N2 | (new) Durable snapshot hardcodes `installed_version` and records absolute paths | present-at-HEAD | `install_wizard.py` step 3 writes `"installed_version": "2026.8.10"` literally and `policy.to_dict()` unredacted. | `pfub72` |

## Completion criteria (the whole Set is done only when)

- `aw --version` from an installed wheel equals that wheel's distribution version, and `aw doctor` warns on a stale local-directory build. Owner: whz0oi
- The consent plan prints only paths that the install then writes, and `project.json`, the preset tables, the consent text and `.aw/.gitignore` agree that `state_durable` is not committed in a target. Owner: gi1w75
- A fresh install writes one install snapshot and one history file, under `.aw/state/durable/`, with the real version and no absolute home path; an upgrade removes the root duplicates. Owner: pfub72
- After a fresh `aw install -y`, `git status --porcelain` is empty except ignored paths, and the advisory lines are true. Owner: gzsfqn
- `.aw/inbox/README.md` is installed, tracked without `-f`, and a drop beside it is ignored. Owner: xzlu9b
- No installed agent-facing text cites a retired `.agents/` record path, the `intake` status as canonical, or the legacy spec naming as current. Owner: jbnkkh
- The managed AGENTS.md block in a target cites no file the target lacks, and a check enforces it. Owner: ka0g86
- `aw research index --check` reports order, kind and model mismatches. Owner: okw4ke
- `aw research new --apply` under `umask 022` produces a 0644 file. Owner: ic4eg0
- A lone report opening a new research set is numbered 01, and `--order` exists on `research new` and `adopt`. Owner: zye6k4
- One scratch-target regression test reproduces every original observation and passes, and the full suite passes with pasted output. Owner: kck7a5

## Cross-IPD validation


- THE TRACKING TRUTH TABLE AGREES END TO END: for each physical class, the preset git policy (`gi1w75`), the files actually written (`pfub72`), what is staged (`gzsfqn`) and what `.aw/.gitignore` ignores agree on the scratch target. Performed by `kck7a5` E-02.
- THE DANGLING-REFERENCE CHECK IS GREEN ON THE FULL INSTALLED BUNDLE, including the inbox README from `xzlu9b` and the rewritten READMEs from `jbnkkh`. Performed by `kck7a5` E-02 (the check itself is built by `ka0g86`).
- THE RESEARCH VERBS COMPOSE: a lone report filed by `aw research new` and by `aw adopt` gets `01` (`zye6k4`), mode 0644 (`ic4eg0`), and passes `aw research index --check` (`okw4ke`). Performed by `kck7a5` E-03.

## Deferred / out of scope (with reason)

- D13 COMPANION FILES. A feature request by the report's own instruction ("classify and record as backlog rather than forcing an implementation").
  - Carrier: bh1cy5
- D02, D06, the rename half of D10, the adopt half of D13, and the INDEX and upgrade-warning halves of D15 are fixed at HEAD (evidence in Findings). They are not re-fixed; `kck7a5`'s regression test pins the D02 and D06 outcomes so they cannot regress.
  - Carrier: kck7a5
- A FINAL TRIAGE REPORT FILE requested by report `l6cbbb` step 5 is satisfied by the Findings table above; no separate review record is written.
  - Carrier-Declined: not owed; the requested triage IS the Findings table of this plan, so there is no outstanding obligation to hand off.

## Scope check

- Over-scope: none. This plan writes only itself.
- Under-scope: the report's request to warn about version skew on EVERY `aw` invocation is narrowed to `aw --version` and `aw doctor` in `whz0oi` (reason recorded there).

## Required tests / validation

This plan runs no tests. The whole-Set measurement (the fresh-install regression and the bare `python3 -m pytest` run) is performed by `kck7a5`; each child carries its own behavioral tests.

## Open questions

### OQ-01: Is `state_durable` meant to be committed in a target?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED from repository evidence: NOT committed. The shipped `.aw/.gitignore` template ignores `/state/` as a leak-containment rule citing D92, records that it was "Verified 2026-09-12: the shipped sanitizer flags a real `install.json` as `home-path` + `handle` findings", and mirrors this repository's own root `.gitignore`. The preset table's `target-git` is the stale side of the contradiction. Child `gi1w75` aligns the declaration with the shipped behavior.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE `aw find plans whz0oi` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE `aw find plans gi1w75` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE `aw find plans pfub72` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE `aw find plans gzsfqn` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE `aw find plans xzlu9b` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE `aw find plans jbnkkh` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: PASTE `aw find plans ka0g86` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: PASTE `aw find plans okw4ke` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: PASTE `aw find plans ic4eg0` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: PASTE `aw find plans zye6k4` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: PASTE `aw find plans kck7a5` showing it under `executed/`, and QUOTE its V-items' `Result: pass` lines, including the pasted bare-suite summary line from its V-04.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This orchestrator carries ORCHESTRATION ONLY: its eleven E-items confirm each child reached `executed`, and every whole-Set obligation names its owning child. Execute children in dependency order through `aw oc run instbugs` or by hand; commit only files changed for the item being executed through `aw commit <plan> -- <paths>`, never `git add -A`, never push. OQ-01 is resolved; no question is open. Every `V-*` above demands PASTED output (`aw find plans <id6>` and the child's quoted `Result: pass` lines); a claim without pasted output does not satisfy it. `- Scope-Paths:` is a DECLARATION: an out-of-scope edit is justified at finalize with `--scope-reason`, not refused. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run`, once every child is `executed` the runner retires this plan with no agent turn; in a hand execution ("execute instbugs" with no runner), the executor works the checklist in order, fills each `V-*`, and transitions this plan with `aw ipd finalize` only after the last child is `executed`, never by a hand `git mv`.
