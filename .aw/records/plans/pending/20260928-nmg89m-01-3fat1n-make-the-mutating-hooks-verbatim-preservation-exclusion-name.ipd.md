# IPD: Make the mutating hooks' verbatim-preservation exclusion name the live research tree

- Date: 2026-09-28
- Kind: child
- Concern: `.pre-commit-config.yaml` excludes the research trees from all four content-MUTATING hooks (`trailing-whitespace`, `end-of-file-fixer`, `ruff --fix`, `ruff-format`) on the stated ground that they are "cited external research artifacts (their own formatting/punctuation is intentional)". The regex names `.agents/docs/research/` and `.aw/records/docs/research/`, and BOTH match zero tracked files: the first tree does not exist in this repo at all and the second was flattened to `.aw/records/research/` by spec `20260817-2124-01`. So the exclusion protects NOTHING, and all 139 tracked files of the real research tree are subject to the four hooks the comment says must not touch them. This is not latent: driven at HEAD `e203df44`, an as-delivered research `.md` carrying trailing whitespace and no final newline IS rewritten by the fixers, and a research `.py` IS reformatted by `ruff-format`. The toolkit's own writer already exempts these trees (`artifact_core._VERBATIM_PRESERVED_SEGMENTS`), so the repository currently holds two contradictory answers to one policy question.
- Scope: IN: point the four mutating hooks' exclude regex at the live `.aw/records/research/` tree; drop the dead `.aw/records/docs/research/` alternative; add a test pinning the hook config against `artifact_core._VERBATIM_PRESERVED_SEGMENTS` so the two cannot drift again. OUT: the SAFETY hooks (`gitleaks`, `check-added-large-files`, `local-leaks`), which must keep applying everywhere; the `.aw/system/` alternative in the same regex; the two local IPD gates; `engine.py`'s installed-target config templates (they ship no mutating hooks); reformatting or normalizing any research file.
- Scope-Paths: .pre-commit-config.yaml, tests/test_precommit_verbatim_exclusions.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: nmg89m
- Blocks-Release: next
- Set: nmg89m
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 3fat1n

## Workflow history

- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog nmg89m. Resolved the item's open policy question (keep the intent, fix the regex) from repository evidence rather than deferring it, and drove both failure modes end to end through the real pinned hooks instead of asserting the regex by inspection. Added a config-versus-code parity test because the stale path proves inspection alone does not hold.
- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

The four content-mutating pre-commit hooks actually exclude the research tree that exists, so an as-delivered research artifact is no longer rewritten at commit time, and a test ties the hook config to the writer's own verbatim-preserved path list so the next layout move cannot silently re-open the hole.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the exclusion name the tree that exists

- [ ] E-01 In `.pre-commit-config.yaml`, replace the dead `\.aw/records/docs/research/` alternative with the live `\.aw/records/research/` in the `exclude:` regex of ALL FOUR content-mutating hooks (`trailing-whitespace`, `end-of-file-fixer`, `ruff`, `ruff-format`).
  - THE EDIT IS THE SAME ON ALL FOUR AND MUST BE APPLIED TO ALL FOUR. The four `exclude:` values are byte-identical today (`'^(\.agents/docs/research/|\.aw/records/docs/research/|\.aw/system/)'`, occurrences measured at 4), so a single find-and-replace of that exact string is correct. Fixing three of four would leave one hook still rewriting the tree, which is the current bug at 25 percent strength.
  - DROP `\.aw/records/docs/research/` RATHER THAN KEEPING IT BESIDE THE NEW PATH. It is not a legacy read path that might still be populated: spec `20260817-2124-01` G4 states the legacy `.agents/` inputs map DIRECTLY to the final targets with "no intermediate `.aw/records/docs/` migration hop", and its Non-goals explicitly refuse to build one. So no supported layout can ever place a file there, and keeping the alternative preserves the exact misleading text this plan exists to remove.
  - KEEP `\.agents/docs/research/`, even though it also matches zero files here (this repo has no `.agents/` tree at all). It is the LEGACY layout a managed target repo can still be on, and `research_contract.resolve_research_root` still falls back to it, so it is a live read path elsewhere and its presence is correct rather than stale.
  - KEEP `\.aw/system/` and its comment untouched. It is a separate justification in the same regex (a relocated copy whose source copies are still linted) and is out of scope.
  - DO NOT TOUCH THE SAFETY HOOKS. `gitleaks`, `check-added-large-files`, and `local-leaks` carry no exclude and must keep applying to these paths; the config comment already promises this, and weakening it would let a secret land in a research file.
  - Depends on: none
  - Expected outcome: `.aw/records/research/` is excluded from all four mutating hooks; `.aw/records/docs/research/` appears nowhere in the file; the safety hooks are unchanged.
  - Execution state: pending

- [ ] E-02 Update the file's leading comment block so the stated reason matches the regex it explains.
  - The comment currently reads "`.agents/docs/research/` and `.aw/records/docs/research/`: cited external research artifacts ... the `.aw/` path mirrors the legacy one after the physical-layout migration". That parenthetical is the FALSE claim that hid this bug for the whole life of the defect, since the migration flattened the path instead of mirroring it. Name the two paths the regex now carries and say the `.aw/` one is the CURRENT flat tree with the legacy `.agents/` path retained for a target repo still on that layout.
  - STATE THE WRITER-SIDE TWIN, so a future reader finds it: note that `artifact_core._VERBATIM_PRESERVED_SEGMENTS` carries the same policy for the toolkit's own writer and that `tests/test_precommit_verbatim_exclusions.py` (E-03) pins the two together. Without this pointer the next layout move updates one and not the other, which is precisely how this defect arose.
  - Depends on: E-01
  - Expected outcome: the comment and the regex agree, and both name the writer-side twin and its pin.
  - Execution state: pending

### Task group 2: stop the config and the writer drifting apart again

- [ ] E-03 Add `tests/test_precommit_verbatim_exclusions.py` asserting that every mutating hook's `exclude` regex covers every tree in `artifact_core._VERBATIM_PRESERVED_SEGMENTS` that is a LIVE path in this repository, and that no named path is dead.
  - (a) PARITY, the load-bearing case: parse `.pre-commit-config.yaml` with `yaml.safe_load`, select the hooks whose ids are in `{trailing-whitespace, end-of-file-fixer, ruff, ruff-format}`, and for each, assert `re.search(exclude, "<tree>/x.py")` matches for `.aw/records/research` and `.agents/docs/research`. Build the probe paths from `_VERBATIM_PRESERVED_SEGMENTS` rather than hardcoding them, so adding a tree to the writer's tuple FAILS this test until the hook config is updated too. Measured against the pre-change config, `.aw/records/research/x.py` is NOT EXCLUDED by all four hooks, so this case fails today.
  - (b) NO DEAD PATH: assert every path alternative in the regex either resolves to a directory that exists in this repo OR is on a short allowlist of intentionally-retained legacy paths (`.agents/docs/research/`, which is legitimately absent here and present in a target repo on the legacy layout). This is the case that would have caught the original bug, and it must name the allowlist reason in its failure message so a future reader does not simply extend the allowlist to silence it.
  - (c) THE SAFETY HOOKS STAY UNEXCLUDED: assert `gitleaks`, `check-added-large-files`, and `local-leaks` carry no `exclude` covering these trees. This guards the direction where a well-meaning later edit copies the exclusion onto every hook and lets a secret through.
  - (d) ASSERT THE HOOK ID SET IS COMPLETE: assert the four mutating ids are all FOUND in the parsed config, so a hook being renamed upstream (or removed) fails loudly instead of making (a) vacuously pass over an empty selection. A silently empty selection is the standard way a config test rots into a no-op.
  - MATCH ON THE REGEX, NOT ON THE LITERAL STRING. Asserting the exact regex text would fail on any harmless reordering and would not actually test coverage; driving `re.search` over probe paths tests the property. Note `pre-commit` applies `exclude` as a `re.search` against the repo-relative path, which is what (a) reproduces.
  - Depends on: E-02
  - Expected outcome: (a) and (b) fail against the pre-change config and pass after; (c) and (d) pass both before and after.
  - Execution state: pending

- [ ] E-04 Run the bare suite (`python3 -m pytest`) and confirm no regression.
  - Depends on: E-03
  - Expected outcome: green, with any failure named as pre-existing at the base commit or new.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/test_executed_transition_gate_e2e.py::PreCommitConfigStageRegistrationTests` is the PRECEDENT for asserting facts about `.pre-commit-config.yaml` from a test: it parses the file with `yaml.safe_load`, drives a table of `(case, read, expected, why)` rows, and its docstring states plainly that it is "a CONFIGURATION assertion only" and not evidence the hook fires. E-03 follows that shape, including the same honesty about what a config assertion does and does not prove.
- That same class records exactly why a config fact needs a test rather than inspection: a key `pre-commit` does not recognize is "SILENTLY IGNORED", so the failure is "invisible in CI". A stale path inside an `exclude` regex fails the same silent way, which is the argument for E-03(b).
- `artifact_core._VERBATIM_PRESERVED_SEGMENTS` already carries this exact policy for the toolkit's own writer, and its comment cites `.pre-commit-config.yaml` as the authority ("`.pre-commit-config.yaml` deliberately excludes these from every content-MUTATING hook because 'their own formatting/punctuation is intentional'"). It lists THREE trees including the live `.aw/records/research`, so the writer side is already correct and only the hook side is stale.
- `normalize_artifact_markdown`'s docstring documents the opposite-facing decision for non-research records, deliberately making the writer AGREE with the mutating hooks ("their exclude regex does not cover the `.aw/records` trees where agents write most"). That confirms the exclusion's narrowness is intentional and that this plan must widen it only to the research trees, not to `.aw/records` generally.
- AGENTS.md's execution contract requires a BARE `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so `-n0`, a second `-q`, and `-p no:randomly` are forbidden. A narrowed run needs `-o addopts=""` to report per-test counts.

## Findings

All measured in this lane worktree at HEAD `e203df44`, driving the REAL hooks at their pinned revisions (`pre-commit-hooks` v4.6.0, `ruff-pre-commit` v0.4.4) via `pre-commit run <id> --files <paths>`, not by reading the regex.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `.pre-commit-config.yaml` `exclude:` on the four mutating hooks | BOTH `.aw/` ALTERNATIVES NAME NOTHING. The regex's `.aw/records/docs/research/` matches zero tracked files, and so does `.agents/docs/research/`: this repo has no `.agents/` tree at all. The live tree is `.aw/records/research/` with 139 tracked files, and it is matched by no alternative. | `git ls-files .aw/records/docs/research \| wc -l` = 0; `git ls-files .agents \| wc -l` = 0; `git ls-files .aw/records/research \| wc -l` = 139 |
| F-2 | MED | `trailing-whitespace`, `end-of-file-fixer` | THE FIXERS REALLY DO REWRITE THE LIVE TREE, which is what makes this a defect and not a tidiness note. Identical probe files (trailing whitespace plus no final newline) placed in the live and the dead tree: the hooks reported `Fixing .aw/records/research/_probe.md` and its md5 CHANGED, while the copy in `.aw/records/docs/research/` was untouched and its md5 was unchanged. | md5 before both `8548333a...`; after, live `3ceef342...` and dead `8548333a...`; `od -c` confirms the live probe gained a stripped line and a final newline |
| F-3 | MED | `ruff-format` | `ruff-format` REWRITES A RESEARCH `.py`. Appending `x   =   1` to the tracked research prototype `broker.py` and running the hook reported "files were modified by this hook / 1 file reformatted" and the file came back as `x = 1`. | `pre-commit run ruff-format --files <research prototype>/broker/broker.py` -> modified; `git diff --stat` shows the change; reverted with `git checkout --` |
| F-4 | INFO | 139 tracked research files | NO EXISTING FILE IS CURRENTLY DIRTY, so this is preventive and there is no migration backlog. All four hooks pass over the whole tracked research tree today with zero rewrites, and an independent scan finds zero trailing-whitespace and zero end-of-file violations across all 139 files. | all four `pre-commit run <id> --files $(git ls-files .aw/records/research)` -> `Passed`, `git status` empty; scan: `trailing-whitespace violations: 0`, `eof violations: 0` |
| F-5 | LOW | `ruff`/`ruff-format` file-type filter | THE `ruff` EXPOSURE IS NARROWER THAN THE FILE COUNT SUGGESTS and the honest number is 2, not 139. `pre-commit` applies its own `types` filter before the exclude, so both ruff hooks skip `.md`, `.json`, and `.ts` in this tree ("no files to check / Skipped") and reach only the 2 tracked `.py` files. The whitespace fixers, by contrast, reach all 139. A naive measurement that invokes `ruff` on explicit filenames bypasses that filter and reports 4 files would-reformat plus dozens of parse errors on `.md`; that number is an artifact of the measurement, not the hook's reach. | `pre-commit run ruff --files <research README.md>` -> `Skipped`; same for `MANIFEST.json` and `opencode-peer.ts`; `git ls-files .aw/records/research \| grep -c '\.py$'` = 2 |
| F-6 | MED | `.pre-commit-config.yaml` leading comment | THE COMMENT ASSERTS A PROTECTION THE REGEX DOES NOT DELIVER, and its stated mechanism is factually wrong: it says "the `.aw/` path mirrors the legacy one after the physical-layout migration", but the migration FLATTENED `docs/research` to `research`. This is the false premise that let the stale path survive review. | `.pre-commit-config.yaml` comment lines 1-5; `layout_inventory._RECORDS_SUBPATH_REWRITES` contains `("docs/research/", "research/")` |
| F-7 | INFO | spec `20260817-2124-01` (`records-taxonomy-cleanup`, `implemented`) | `.aw/records/docs/research/` IS UNREACHABLE BY DESIGN, not merely unpopulated, so dropping it loses no legacy read path. G4 requires the legacy mapping be updated "IN PLACE (no intermediate `.aw/records/docs/` migration hop)" and the Non-goals refuse "NOT building an intermediate-layout (`.aw/records/docs/`) -> final migration path". | spec G4 and Non-goals, read at `.aw/records/specs/implemented/20260817-2124-01-records-taxonomy-cleanup.spec.md` |
| F-8 | INFO | `artifact_core._VERBATIM_PRESERVED_SEGMENTS` | THE REPOSITORY ALREADY HOLDS THE ANSWER TO THE ITEM'S POLICY QUESTION. The writer's tuple lists `.aw/records/research`, `.aw/records/docs/research`, and `.agents/docs/research`, and its comment defers to `.pre-commit-config.yaml` as the authority for the policy. So the intent demonstrably still holds for the flat tree, and only the hook config failed to follow it. | `agent_workflows/artifact_core.py` `_VERBATIM_PRESERVED_SEGMENTS` and the comment above it |
| F-9 | INFO | `research_contract.resolve_research_root` | `.agents/docs/research` MUST BE KEPT in the regex. It is a live fallback read root for a target repo still on the legacy layout ("falls back to the legacy `.agents/docs/research`"), so its zero match count HERE is not evidence it is dead. | `research_contract.resolve_research_root` docstring and body |
| F-10 | INFO | the candidate fix | THE FIX WORKS, driven before writing it into the plan. With `.aw/records/docs/research/` replaced by `.aw/records/research/` in all four hooks, the F-2 probe is `Skipped` with an unchanged md5, and the F-3 `ruff-format` probe is `Skipped` leaving `x   =   1` in place. Config reverted afterwards. | re-ran both probes under the edited config; `before=8548333a... after=8548333a... same=YES`; `tail` still shows `x   =   1`; `git checkout -- .pre-commit-config.yaml` |
| F-11 | INFO | `engine.py` config templates | THE SHIPPED TEMPLATES NEED NO CHANGE, so this stays a dev-repo fix. `_LOCAL_LEAKS_PRECOMMIT_TEMPLATE` and its sibling blocks install only `repo: local` hooks (`local-leaks`, the two IPD gates); they carry no mutating hooks and therefore no exclude regex to correct. | read `engine.PRE_COMMIT_CONFIG` templates and blocks |
| F-12 | LOW | `tests/` | NO TEST COVERS THIS REGEX TODAY, which is why a stale path survived a layout migration. The only test that parses this config asserts stage registration and never reads `exclude`. | `grep -rn "exclude" tests/test_executed_transition_gate_e2e.py` -> no match; no test references `_VERBATIM_PRESERVED_SEGMENTS` |
| F-13 | INFO | `.pre-commit-config.yaml` | E-03's NARROW SCOPE LOSES NOTHING, which retires the idea of a general config audit rather than deferring it. The four mutating hooks carry the ONLY `exclude` (or `files`) keys in the entire config, so a "every named path must exist" check over the whole file would have exactly the same four subjects E-03(b) already covers. | enumerated every hook's `exclude`/`files` key from the parsed YAML: 4 keys, all four the mutating hooks, all byte-identical |
| F-14 | INFO | `.aw/system/` | `.aw/system/` IS NOT STALE, so it is correctly left alone rather than swept into this fix. Unlike both research alternatives it names a directory that exists and holds 160 tracked files. | `git ls-files .aw/system \| wc -l` = 160; directory probe -> EXISTS, while `.agents/docs/research` -> ABSENT |

## Proposed changes (ordered, validatable)

1. E-01: in all four mutating hooks, swap the dead `\.aw/records/docs/research/` for the live `\.aw/records/research/`, keeping `\.agents/docs/research/` and `\.aw/system/` and leaving the safety hooks alone.
2. E-02: correct the leading comment so its stated reason matches the regex, and point at the writer-side twin and its new pin.
3. E-03: add `tests/test_precommit_verbatim_exclusions.py` with the parity, no-dead-path, safety-hooks-unexcluded, and hook-ids-present cases.
4. E-04: bare suite.

## Deferred / out of scope (with reason)

- Normalizing, reformatting, or otherwise touching any of the 139 research files. F-4 measures zero current violations, so there is nothing to clean, and mutating as-delivered artifacts is the exact harm this plan prevents.
  - Carrier-Declined: No defect exists to carry. This row records a deliberate NON-action, and the measurement supporting it is F-4 (zero trailing-whitespace and zero end-of-file violations across all 139 tracked files), so there is no cleanup backlog for a carrier to own.
- The `\.aw/system/` alternative in the same regex. A separate justification (a relocated bundle whose source copies are still linted) that is not stale and not this item's subject.
  - Carrier-Declined: No defect found, measured rather than assumed: `.aw/system/` EXISTS in this repo with 160 tracked files, so unlike `.aw/records/docs/research/` this alternative matches real files and its exclusion works as written. Nothing to carry.
- Extending the E-03 parity idea to a general "every path named in any hook's exclude must exist" check across the whole config.
  - Carrier-Declined: VACUOUS AS SCOPED, which is why this needs no carrier and the plan's earlier framing of it as a reviewer question was wrong. Measured: the four mutating hooks carry the ONLY `exclude` (or `files`) keys in the whole config, so E-03(b) already covers every path-naming key present. A general check would have no additional subject until a fifth such key is added.
- Adding the verbatim exclusion to a managed TARGET repo's installed config. F-11 shows the shipped templates install no mutating hooks, so there is no hole there today; if a future template ships one, that plan owns this policy.
  - Carrier-Declined: No present defect to carry. The templates install only `repo: local` hooks (`local-leaks` and the two IPD gates), none of which mutate content, so there is no exclusion to add and nothing for a carrier to track. A future template that ships a mutating hook owns this policy at that time.
- Any relaxation of the SAFETY hooks (`gitleaks`, `check-added-large-files`, `local-leaks`) over these trees. The config comment promises they apply everywhere and E-03(c) pins it.
  - Carrier-Declined: Explicitly rejected as a direction, not deferred. This is a thing the plan forbids rather than an outstanding obligation, and E-03(c) converts the prohibition into a test, so there is no unfixed defect for a carrier to own.

## Scope check

- Over-scope: E-03 IS THE ONE ADDITION BEYOND THE ITEM'S LITERAL ASK, and a reviewer should judge it first. The backlog item asks only to decide the policy and fix (or delete) the regex; a two-line edit would satisfy it. The new test file is justified by F-12 plus the defect's own history: the path went stale during a layout migration and nothing failed, so a fix without a pin is one migration away from regressing identically. If the reviewer disagrees, E-03 and its V-03 can be dropped without touching E-01/E-02, which stand alone.
- Under-scope: DELIBERATE and narrow. The plan scopes E-03 to the verbatim-preserved set rather than auditing the config generally, and it leaves `.aw/system/` alone. Neither omission hides a defect: F-13 measures that the four mutating hooks carry the config's ONLY path-naming keys, so the narrow check already covers every subject a general one would have, and `.aw/system/` exists with 160 tracked files so its exclusion is not stale.

## Required tests / validation

- `python3 -m pytest tests/test_precommit_verbatim_exclusions.py tests/test_executed_transition_gate_e2e.py -o addopts=""` (the new test plus the existing config-parsing test, which reads the same file).
- Bare `python3 -m pytest`.
- A worktree revert of E-01 to prove E-03(a) and E-03(b) genuinely fail against the pre-change regex.
- Behavioral re-drive of F-2 and F-3 through the real hooks under the fixed config, since a regex assertion alone does not prove the hook stops firing.

## Spec / documentation sync

N/A with reason: no spec text changes, and no `.spec.md` path is in `- Scope-Paths:`. Spec `20260817-2124-01` already mandates the flat `.aw/records/research` layout and already refuses the intermediate `.aw/records/docs/` hop (F-7); this plan makes one config file obey that implemented spec rather than amending any contract. The user-facing promise in the config's own comment block is corrected by E-02, which is documentation-in-place rather than a docs tree change.

## Open questions

### OQ-01: Does the verbatim-preservation intent still hold for the flat `.aw/records/research/` tree, or should the exclusion and its comment be deleted instead?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE INTENT HOLDS; fix the regex. Resolved from repository evidence rather than preference, which is why it is not left for the human. `artifact_core._VERBATIM_PRESERVED_SEGMENTS` (F-8) already lists the flat `.aw/records/research` as verbatim-preserved and its comment defers to `.pre-commit-config.yaml` as the authority for that policy, so the toolkit's own writer is ALREADY honoring the intent for the live tree; deleting the hook exclusion would leave the repository enforcing the policy in its writer and contradicting it in its hooks. The underlying reason is also unchanged: these are externally authored artifacts cited as delivered, and `aw research`'s own contract treats them that way. The item's alternative ("remove the stale alternative and the comment that asserts the intent") would additionally mean accepting that `ruff-format` may rewrite a cited prototype, which F-3 shows it will.

### OQ-02: Should `.agents/docs/research/` be dropped as dead too, given it also matches zero files in this repo?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, keep it. Its zero match count here is not evidence of deadness: `research_contract.resolve_research_root` still falls back to `.agents/docs/research` for a target repo on the legacy layout (F-9), and `_VERBATIM_PRESERVED_SEGMENTS` retains it for the same reason. Only `.aw/records/docs/research/` is unreachable BY DESIGN (F-7, spec G4 plus Non-goals), which is the distinction that makes dropping one and keeping the other correct rather than arbitrary. E-03(b) encodes exactly this asymmetry as an allowlist with a stated reason.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual `git diff` of `.pre-commit-config.yaml`. The diff MUST show exactly four changed `exclude:` lines, each gaining `\.aw/records/research/` and losing `\.aw/records/docs/research/`, with `\.agents/docs/research/` and `\.aw/system/` retained in every one. Paste the output of a grep for `exclude:` showing all four final values, and confirm they are byte-identical to each other.
  - ALSO REQUIRED: paste evidence that `.aw/records/docs/research` appears NOWHERE in the final file, and that the three safety hooks (`gitleaks`, `check-added-large-files`, `local-leaks`) are untouched by the diff.
  - ALSO REQUIRED (the load-bearing half, because a regex assertion does not prove a hook stopped firing): re-drive F-2 and F-3 through the REAL hooks and paste the actual output. For F-2, write a probe file with trailing whitespace and no final newline into `.aw/records/research/`, record its md5, run `pre-commit run trailing-whitespace --files <probe>` and `pre-commit run end-of-file-fixer --files <probe>`, and paste both the hook output and the md5 BEFORE and AFTER, which must be IDENTICAL. For F-3, append a deliberately unformatted line to a tracked research `.py`, run `pre-commit run ruff-format --files <that file>`, and paste output plus a `tail` showing the line UNCHANGED. Then delete the probe and `git checkout --` the `.py`, and paste a `git status --short` proving the tree is clean again. A run in which the hooks report `Passed` rather than `Skipped` is NOT sufficient evidence on its own, since a clean file passes either way; the md5 equality and the surviving unformatted line are the actual proof.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the final comment block and state, line by line, which claim each regex alternative now corresponds to. Confirm explicitly that the phrase asserting the `.aw/` path "mirrors the legacy one" is GONE, since F-6 identifies it as factually wrong, and that no new claim about the safety hooks was weakened.
  - ALSO REQUIRED: quote the sentence that names `artifact_core._VERBATIM_PRESERVED_SEGMENTS` and the new test file, which is the pointer E-02 exists to add.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the passing run of `python3 -m pytest tests/test_precommit_verbatim_exclusions.py tests/test_executed_transition_gate_e2e.py -o addopts=""` with its summary line and per-test counts.
  - ALSO REQUIRED (the load-bearing half): revert E-01's regex change IN THE WORKTREE, re-run the new test file, and paste the ACTUAL failure output for (a) and (b). (a) must fail by reporting that `.aw/records/research/x.py` is not excluded by all four hooks; (b) must fail by naming `.aw/records/docs/research/` as a dead path. Name the observed failure mode explicitly and confirm each is a behavioral assertion failure, not an import, YAML-parse, or fixture error. Then restore. A reverted run in which (a) and (b) still PASS means the test cannot detect the defect and this item FAILS.
  - ALSO REQUIRED: state plainly that (c) and (d) pass in BOTH the reverted and the restored runs, and paste the evidence that (d) is not vacuous: show that the test FAILS if the mutating-hook id set is made to select nothing (for example by temporarily renaming one id in a copy of the parsed data, or by an explicit assertion on the selected count that you paste). A parity test over an empty selection passes while proving nothing, and that is the specific rot this case exists to prevent.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed. For any failure, paste its node id and evidence that it fails identically at the base commit (pre-existing) or admit it is new. Do not paste a narrowed run in place of the bare one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. A one-line policy correction in `.pre-commit-config.yaml` plus a test that pins it. The defect is real and measured, not inferred from the regex: the four content-mutating hooks currently rewrite files in `.aw/records/research/` (F-2, F-3), a tree the config's own comment says must be preserved as delivered. The plan resolves the backlog item's open policy question rather than handing it back, and OQ-01 records the evidence: the toolkit's own writer already exempts the flat tree and cites this very config as the authority, so deleting the exclusion would leave the repository contradicting itself. The reviewer's real decision is OQ-01's direction (keep the intent) and whether E-03's new test file is wanted.

SEVERITY IS HONESTLY MED, and the case cuts both ways. Against MED: F-4 measures zero currently-dirty files, so nothing is damaged today and the fix is preventive; F-5 further narrows the `ruff` half of the exposure to 2 `.py` files rather than 139, because `pre-commit`'s type filter skips `.md` and `.json` before the exclude is consulted. Against LOW: the whitespace fixers DO reach all 139, the damage they do is a SILENT mutation of an externally authored artifact at commit time (the citation loses fidelity with no operator signal), and the repository currently ships a comment promising a protection it does not provide, which is worse than having no comment.

Scope fence (a DECLARATION for reconciliation, not a stop directive): in `.pre-commit-config.yaml`, only the four mutating hooks' `exclude:` values and the leading comment block. No change to `default_install_hook_types`, `default_stages`, any `repo:`/`rev:` pin, the `gitleaks` or `check-added-large-files` hooks, or the three `repo: local` hooks. `agent_workflows/artifact_core.py` is expected to need NO edit: it is already correct (F-8) and the new test CONSUMES its tuple. `agent_workflows/engine.py` is expected to need NO edit (F-11). An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Three claims here are specifically easy to fake and must not be: V-01's md5 BEFORE and AFTER pair (a `Skipped` line alone does not prove the file survived), V-03's REVERTED run (a passing test against fixed config proves nothing about whether it can detect the defect), and V-03's non-vacuity check on the hook id selection. Note also that measuring `ruff` by invoking it on explicit filenames BYPASSES `pre-commit`'s type filter and reports a much larger, wrong exposure (F-5); drive the hooks through `pre-commit run` only.

BE CAREFUL WITH PROBE FILES AND THE SHARED CHECKOUT. V-01 requires writing a throwaway file under `.aw/records/research/` and temporarily dirtying a tracked research `.py`. Delete the probe and restore the `.py` with a path-scoped `git checkout -- <path>`, never a bare `git reset`, `git stash`, or `git clean`, and paste a clean `git status --short` afterwards. Never commit a probe file.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if the V-01 re-drive shows the mutating hooks STILL rewriting a research file under the fixed regex, STOP and report rather than widening the exclusion further or adding a second mechanism, because that would mean `pre-commit` is not applying `exclude` the way E-03(a) models and the test would then be pinning a false model. If E-03(b) cannot distinguish the intentionally-retained `.agents/docs/research/` from a genuinely dead path without an allowlist that would also hide a future stale entry, STOP and report the design problem rather than deleting case (b); a no-dead-path check that cannot fail is worse than none. If making any part of this pass appears to require excluding these trees from a SAFETY hook, STOP: that is the one change this plan forbids outright.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then set backlog item `nmg89m` `done` with `--evidence` citing the executed plan. It carries `- Blocks-Release: next`, which this plan inherits via `- From-Backlog: nmg89m`, so the gate is preserved by that handoff and no separate de-gating is required.
