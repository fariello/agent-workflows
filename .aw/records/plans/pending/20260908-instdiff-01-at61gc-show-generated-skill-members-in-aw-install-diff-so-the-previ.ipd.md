# IPD: Show generated skill members in aw install --diff so the preview stops under-reporting 90 files it will write

- Date: 2026-09-08
- Kind: child
- Concern: `aw install --diff` is a DRY RUN whose whole purpose is to show what an apply would write, and it silently omits every generated skill-package file. Measured at HEAD `fac69fbd` in this worktree: the run path writes 52 shim members plus 90 skill members, and `--diff` builds its proposed set from body plus shims only, so it under-reports 90 files. That is a preview/apply divergence in the one surface an operator uses to decide whether to apply.
  THE CAUSE IS A SINGLE MISSING CALL, not a design gap. `install_into_repo` builds the merged map correctly (`agent_workflows/engine.py:5697` `skill_members = _build_skill_members(...)`, `:5700` `generated_members = {**shim_members, **skill_members}`, passed to `install_all` at `:5703` and `prune_stale` at `:5704`). The `--diff` branch, twenty lines earlier in the same function, does NOT: `engine.py:5856-5862` builds `body_members` and `shim_members` and calls `show_install_diffs(plan, body_members, shim_members)` with no `_build_skill_members` call. The renderer itself is fine; it is simply handed an incomplete map (`show_install_diffs` at `:3270`, proposed set built from body at `:3281-3288` and `shim_members` at `:3289-3290`).
  THIS IS THE ONLY SURVIVING PART OF BACKLOG `bplplj`, whose other five clauses shipped in `5af28bbb` (executed Set `installerskill`: orchestrator `rldro6`, child `kvfsak`). The item asked to wire emission into the installer and to extend the installer tests. Emission, the framework-namespace predicate, the prune scan, idempotency and manifest uninstall are all done and under test. The install-DIFF half was named in `kvfsak` E-05 but that item's stated deliverable was `prune_stale` only ("by passing `generated_members` (shim + skill) to `prune_stale`"), and `show_install_diffs` was never touched. So this plan closes a gap the covering plan's own text shows it did not close, rather than re-doing shipped work.
- Scope: Make the `--diff` preview build the same generated-member map the apply path builds, by calling `_build_skill_members` on the `--diff` branch and passing the merged map to `show_install_diffs`. Add a test that pins preview/apply parity so the two paths cannot diverge again. EXCLUDES any change to skill generation, to `host_adapters`, to the skills-dir resolution, to prune or uninstall behavior, and to what an apply writes: this plan changes only what the PREVIEW reports. Excludes the cosmetic `shim_members` parameter rename discussed in OQ-01.
- Scope-Paths: agent_workflows/engine.py, tests/test_installer_skill_emission.py
- Item-Dependencies: none
- Status: to-review
- Set: instdiff
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: at61gc
- From-Backlog: bplplj

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `bplplj`, NARROWED to one surviving gap. The item carries no `- Blocks-Release:` so none is inherited or invented.
  THE ITEM IS ~95 PERCENT OBSOLETE AND I VERIFIED THAT BEFORE WRITING ANYTHING. Its central factual claim, that `install_all` "today writes only `body_members` + `shim_members`", is no longer true of the run path: `install_into_repo` merges skill members into the generated map at `engine.py:5697-5704`, and `_build_skill_members` (`:5595`) calls the canonical `host_adapters.generate_adapter_bundle` at `:5616` and returns `bundle.skill_files()` at `:5625`. I did not take the executed plan's word for the rest either: I ran its test file, `python3 -m pytest tests/test_installer_skill_emission.py -o addopts=""` -> `10 passed in 21.73s`, covering the resolver, the namespace predicate, the prune scan, fresh install plus manifest, idempotent re-install, orphan prune (tracked and untracked), and manifest uninstall. So emission, hosts, prune, idempotency and uninstall are all genuinely delivered and this plan must not re-implement any of them.
  HOW I ESTABLISHED THE SURVIVING GAP RATHER THAN ASSUMING IT. `show_install_diffs` has exactly ONE call site, `engine.py:5862`, and I read the eight lines around it: that branch builds `body_members` and `shim_members` and never calls `_build_skill_members`. Then I measured the omission instead of reasoning about it, by calling the real generators against this repository's own workflow manifest: `shim members: 52`, `skill members: 90`, `overlap: 0`. Ninety files an apply would write are invisible to the preview. I also read `kvfsak` E-05 and V-05 to be sure this was a genuine gap and not something I had missed: E-05's text scopes itself to `prune_stale` and its evidence is re-install and orphan-prune output, with nothing about the diff renderer.
  ONE THING I FOUND THAT THE ITEM DOES NOT SAY, and it shapes the test. The existing skill test file is `pytestmark = pytest.mark.slow` (`tests/test_installer_skill_emission.py:32`), so it is EXCLUDED from the bare default run that this repository's contract uses to judge a change. A parity test added there would not run in the suite that gates execution. E-02 therefore requires the new test be reachable in the bare run, which means it must not inherit that mark; the honest way to get that is a pure in-memory parity assertion needing no real git repo, which is also faster and less brittle than another end-to-end install.

## Goal

Make the `aw install --diff` preview report exactly the file set an apply would write, so an operator deciding from the dry run is not missing 90 files, and pin that parity with a test so the two code paths cannot silently diverge again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the preview build the same map as the apply

- [ ] E-01 CALL `_build_skill_members` ON THE `--diff` BRANCH AND PASS THE MERGED MAP TO `show_install_diffs`, so the preview's proposed set is the same set the apply writes.
  MIRROR THE APPLY PATH EXACTLY RATHER THAN INVENTING A SECOND COMPOSITION. `install_into_repo` already establishes the shape twenty lines below: build `skill_members` from `_build_skill_members(workflows, plan.source_root, target_layout)`, then merge as `{**shim_members, **skill_members}`. Use the SAME call with the SAME arguments and the SAME merge order. A different argument set or a different merge order here would be a second answer to one question, which is how the two paths drifted in the first place.
  THE `--diff` BRANCH ALREADY HAS EVERY INPUT IT NEEDS, so this adds no new resolution and no new I/O decision: `target_layout`, `workflows` (from `parse_manifest`), and `plan.source_root` are all already in scope on that branch. Verify that by reading it before editing; if any input is missing, STOP and report rather than resolving it a second way.
  DO NOT CHANGE `show_install_diffs` ITSELF. Its body is correct: it unions body members with whatever generated map it is handed. The defect is the argument, not the renderer.
  DO NOT CHANGE WHAT AN APPLY WRITES. This plan alters the PREVIEW only. If a diff appears after this change that an apply would not produce, that is a bug in this change, not a discovery about the apply path.
  - Depends on: none
  - Expected outcome: the `--diff` branch builds `skill_members` through `_build_skill_members` and passes the merged shim-plus-skill map to `show_install_diffs`; `show_install_diffs`'s own body is unmodified; no change to `install_all`, `prune_stale`, or any generator.
  - Execution state: pending

### Task group 2: pin the parity so it cannot regress

- [ ] E-02 ADD A PREVIEW/APPLY PARITY TEST THAT RUNS IN THE BARE SUITE, asserting that the member map the `--diff` branch composes equals the map the apply branch composes.
  ASSERT PARITY BETWEEN THE TWO PATHS, NOT A HARDCODED COUNT. The measured 52 shims and 90 skills are true today and will change the moment a workflow is added or removed, so a test pinning either number is a test that fails for the wrong reason. Assert that the preview's generated map EQUALS the apply's generated map, which is the property that actually matters and which stays true as the corpus grows.
  THE TEST MUST BE REACHABLE IN A BARE `python3 -m pytest`. `tests/test_installer_skill_emission.py:32` sets `pytestmark = pytest.mark.slow` for the whole module, and the repository's configured `addopts` excludes `slow`, so anything inheriting that mark does not run in the suite that gates this change. Either place the parity test where it is not `slow` or give it an explicit non-slow marker; state which was done and prove it by showing the test executing in a bare run.
  PREFER AN IN-MEMORY ASSERTION OVER A SECOND END-TO-END INSTALL. The composition is a pure function of `workflows`, `source_root` and `target_layout`, so the parity can be proven by calling the generators directly, with no temporary git repo. That is what makes it fast enough to be non-slow, and it is a narrower claim that fails for exactly one reason.
  ASSERT NON-EMPTINESS TOO. Two empty maps are equal, so a parity assertion alone would pass vacuously if generation broke or a fixture produced no workflows. Require that the skill map is non-empty, so the test cannot pass by measuring nothing.
  - Depends on: E-01
  - Expected outcome: a test asserting the preview's generated member map equals the apply's, that the skill portion is non-empty, and that runs in a bare `python3 -m pytest`; no hardcoded file counts.
  - Execution state: pending

- [ ] E-03 DEMONSTRATE THE FIX END TO END AGAINST A REAL INSTALL, so the claim is about observed behavior and not only about map equality.
  SHOW THE BEFORE AND THE AFTER. Run the `--diff` preview on a throwaway repository with the change reverted and again with it applied, and show that the skills directory paths are ABSENT from the first and PRESENT in the second. Map equality (E-02) proves the composition; this proves the operator-visible output actually changed.
  CONFIRM THE APPLY PATH DID NOT MOVE. Install into a throwaway repository and show the on-disk skill file set is the same as before this change. The whole safety claim of this plan is that only the preview changed, and an unverified claim of no-change is exactly the kind this repository's validation rule exists to reject.
  REUSE THE EXISTING END-TO-END HARNESS rather than writing a third one: `tests/test_installer_skill_emission.py` already imports `SOURCE_WORKFLOWS`, `git` and `init_repo` from `tests.support` (`:24`) and builds throwaway repositories that way. This item may legitimately live in that slow module, since it is an end-to-end check by nature; E-02 is the one that must be fast.
  - Depends on: E-02
  - Expected outcome: pasted `--diff` output before and after showing skill paths appearing, plus evidence that an apply's on-disk skill file set is unchanged by this plan.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE APPLY PATH IS THE TEMPLATE AND IT IS TWENTY LINES AWAY. `engine.py:5697-5704` composes `generated_members = {**shim_members, **skill_members}` and passes it to both `install_all` (`:2182`) and `prune_stale` (`:2294`). The `--diff` branch at `:5856-5862` is the outlier.
- `_build_skill_members` (`engine.py:5595`) IS THE ONLY PRODUCTION SKILL-MAP BUILDER and it delegates to the canonical `host_adapters.generate_adapter_bundle` (`:5616`), taking only `bundle.skill_files()` (`:5625`). There is no second generator to choose between, so this plan calls it and nothing else.
- `install_all` AND `prune_stale` STILL NAME THEIR PARAMETER `shim_members` while receiving a map that also carries skills. That is pre-existing and cosmetic; see OQ-01. It is deliberately NOT changed here.
- THE SKILL TEST MODULE IS `slow`-MARKED WHOLESALE (`tests/test_installer_skill_emission.py:32`), and the repository's `addopts` excludes `slow`, so a test added there does not run in the bare suite. This is the single most important convention for E-02.
- SKILLS LAND IN ONE SHARED DIRECTORY FOR BOTH LAYOUTS, `.agents/skills` (`host_adapters.SHARED_SKILLS_DIR` at `host_adapters.py:60`, `engine.resolve_skills_dir` at `:174`). The item's "across hosts" phrasing was already resolved to a single shared dir by `kvfsak`, so there is no per-host emission to add.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `fac69fbd`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `agent_workflows/engine.py:5856-5862` | THE DEFECT. The `--diff` branch builds only `body_members` and `shim_members` and calls `show_install_diffs(plan, body_members, shim_members)`; `_build_skill_members` is never called on this branch. | source read |
| F-2 | HIGH | measured via the real generators | THE PREVIEW UNDER-REPORTS 90 FILES. Calling the production generators against this repository's manifest gives `shim members: 52`, `skill members: 90`, `overlap: 0`, so every one of the 90 is missing from the preview rather than coincidentally covered by a shim path. | ran `generate_shim_members` and `_build_skill_members` |
| F-3 | N/A | `agent_workflows/engine.py:5697-5704` | THE APPLY PATH IS CORRECT and is the template: it composes `{**shim_members, **skill_members}` and passes it to `install_all` and `prune_stale`. So the fix is a missing call, not a design change. | source read |
| F-4 | N/A | `agent_workflows/engine.py:3270-3290`, single call site at `:5862` | THE RENDERER IS NOT AT FAULT. `show_install_diffs` unions body members with whatever generated map it receives; it has exactly one caller, which is the one passing an incomplete map. | source read, grep for call sites |
| F-5 | N/A | executed `kvfsak` E-05 (`:58-61`) and V-05 | THE COVERING PLAN DID NOT CLOSE THIS. E-05's stated deliverable is passing the merged map to `prune_stale`; its evidence is re-install and orphan-prune output. The diff renderer is not mentioned in either. This is why the gap is real and not a re-do. | that plan's own text |
| F-6 | MED | `tests/test_installer_skill_emission.py:32` | THE EXISTING SKILL TESTS DO NOT RUN IN THE BARE SUITE. `pytestmark = pytest.mark.slow` applies to the whole module and the configured `addopts` excludes `slow`. A parity test added there would not run in the suite that gates this change. | source read |
| F-7 | N/A | `tests/test_installer_skill_emission.py` | THE REST OF THE ITEM IS GENUINELY DELIVERED, verified by running it rather than by trusting the plan record: `10 passed in 21.73s` covering resolver, namespace, prune scan, fresh install, idempotency, both orphan cases, and manifest uninstall. | ran the file |
| F-8 | LOW | `engine.py:2185`, `:2297` | `install_all` and `prune_stale` name their parameter `shim_members` while receiving a shim-plus-skill map, so the name now understates the contents. Pre-existing, cosmetic, and deliberately out of scope (OQ-01). | source read |

## Proposed changes (ordered, validatable)

1. E-01 calls `_build_skill_members` on the `--diff` branch and passes the merged shim-plus-skill map to `show_install_diffs`, mirroring the apply path's composition exactly.
2. E-02 adds a preview/apply parity test that runs in the bare suite and asserts map equality plus non-emptiness, with no hardcoded counts.
3. E-03 demonstrates the change end to end: skill paths appear in the preview where they previously did not, and an apply's on-disk result is unchanged.

## Deferred / out of scope (with reason)

- RENAMING THE `shim_members` PARAMETER on `install_all` and `prune_stale` to something like `generated_members`. OQ-01. It is purely cosmetic, it is pre-existing rather than introduced here, and it would touch two signatures plus their call sites and tests, turning a one-line correctness fix into a refactor. A correctness fix and a rename should not share a review.
- ANY CHANGE TO SKILL GENERATION, `host_adapters`, `build_skill_package`, or `generate_adapter_bundle`. All shipped in `5af28bbb` and are under test. This plan consumes them unchanged.
- ANY CHANGE TO PRUNE, UNINSTALL, OR IDEMPOTENCY. Delivered by `kvfsak` E-05/E-07 and pinned by the existing tests, which I ran. Re-implementing them is exactly the waste the obsolescence check exists to prevent.
- PER-HOST SKILL EMISSION. Not pending work: `kvfsak` resolved skills to ONE shared directory for both layouts (`host_adapters.py:60`, `engine.py:174`), so the item's "across hosts" clause is already answered.
- ADAPTER-METADATA FILE EMISSION. Deliberately excluded by `kvfsak` OQ-02 Option A, and pinned by `::test_no_adapter_metadata_files_emitted`. Not reopened here.

## Scope check

- Over-scope: none. Both declared paths are modified: `agent_workflows/engine.py` by E-01, `tests/test_installer_skill_emission.py` by E-03 (and possibly E-02, depending on where the non-slow test lands).
- Under-scope: stated rather than left as `none`. If E-02's parity test lands in a NEW test file rather than the declared one (a legitimate way to escape the module-wide `slow` mark), that new path is outside `- Scope-Paths:` and must be declared before execution or justified at finalize with `--scope-reason`. Decide at execution and say which. Also under-scope by design: the `shim_members` parameter name stays misleading (OQ-01, F-8).

## Required tests / validation

`python3 -m pytest` bare in the executing worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS rather than totals. The new parity test MUST appear in that bare run; if it does not, E-02 is not done, regardless of whether it passes when invoked directly. Additionally run the existing slow skill suite explicitly, `python3 -m pytest tests/test_installer_skill_emission.py -o addopts=""`, to prove this change did not disturb emission, prune, idempotency or uninstall; its pre-change baseline is `10 passed`. For E-03, paste real `--diff` output from a throwaway repository before and after the change.

## Spec / documentation sync

No spec governs the `--diff` renderer's member set, and this plan amends no spec: it makes one code path agree with another that is already correct, changing no contract. That is the justification to record, per the rule that a plan touching behavior a spec describes must carry the amendment.
VERIFY RATHER THAN ASSUME, since a wrong answer here means a silent contract change. Before executing, grep `.aw/records/specs/` for any spec that describes `aw install`'s dry-run or preview output. If one specifies what `--diff` reports, then making the preview complete is a CONTRACT change and that spec file must be added to `- Scope-Paths:` before the run starts, because both runners announce declared spec edits at run start and the finalize scope gate reconciles declared against actual. My reading is that none does, but the executor must confirm and state the result.
No user-facing documentation change is expected: the fix makes `--diff` behave the way its existing help already implies. If any doc states the preview's contents explicitly, correct it there rather than leaving it contradicted.

## Open questions

### OQ-01: Should `install_all` and `prune_stale` rename `shim_members` to `generated_members`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as NO, not in this plan. Both parameters (`engine.py:2185`, `:2297`) now receive a map carrying shims AND skills, so the name understates the contents and mildly misleads a reader. But it is pre-existing, it changes no behavior, and renaming it would touch two public-ish signatures plus their call sites and tests, which would make a one-line correctness fix into a refactor and put an operator-facing bug fix behind a cosmetic review. Recorded so a later reader sees it was noticed and judged rather than missed. It is small and safe enough to fold into any future change that already touches those signatures.

### OQ-02: Where should the non-slow parity test live?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 states the REQUIREMENT (the test must run in a bare `python3 -m pytest`) and any placement satisfying it is acceptable. The question is only which placement. The constraint is that `tests/test_installer_skill_emission.py:32` marks the entire module `slow`, so adding a test there and expecting it in the bare run would be wrong. Two options: a new small test module for the pure-composition parity assertion, or an explicit per-test override in the existing module. Prefer whichever this repository already does elsewhere for a fast test living beside slow ones, and note that a new file is a `- Scope-Paths:` change (see the Scope check).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the modified `--diff` branch showing the `_build_skill_members` call and the merged map handed to `show_install_diffs`. Paste a diff of `show_install_diffs`'s body proving it is UNCHANGED. Paste a diff of `install_all` and `prune_stale` proving they are unchanged. Paste the apply path (`engine.py:5697-5704`) beside the new preview code so a reviewer can see the two compositions are identical in call, arguments and merge order.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new test's source. Paste it EXECUTING IN A BARE `python3 -m pytest` run (show the node id in the output, not just a passing count from a direct invocation), which is the property F-6 makes load-bearing. Paste the assertion showing parity is compared between the two composed maps and that the skill portion is asserted non-empty. Confirm by inspection that no file count is hardcoded. Paste the test FAILING with E-01 reverted, since a parity test that passes both before and after would be proving nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `--diff` output from a throwaway repository BEFORE the change, showing no `.agents/skills/...` paths, and AFTER, showing them present. Paste the on-disk skill file set from an apply before and after the change, showing it IDENTICAL, which is this plan's central safety claim. Paste `python3 -m pytest tests/test_installer_skill_emission.py -o addopts=""` showing the pre-existing `10 passed` still passing. Paste the bare full-suite summary line with the worktree baseline beside it and a node-id comparison.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the paths in `- Scope-Paths:` (plus a new test file if OQ-02 resolves that way, which must then be declared or justified). Do NOT modify `show_install_diffs`'s body. Do NOT modify `install_all`, `prune_stale`, `_build_skill_members`, `generate_adapter_bundle`, `build_skill_package`, or `resolve_skills_dir`. Do NOT rename the `shim_members` parameter (OQ-01, resolved). Do NOT change what an apply writes: this plan changes the PREVIEW only. Do NOT re-implement emission, prune, uninstall, or idempotency; they shipped in `5af28bbb` and are pinned by tests I ran. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `engine.py` is large and under concurrent edit, so find `show_install_diffs`, `install_into_repo`, `_build_skill_members`, `install_all`, `prune_stale`, and `resolve_skills_dir` by name. The `--diff` branch is identifiable by `if plan.diff:` inside `install_into_repo`'s caller loop, not by its line number.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved at61gc --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, backlog `bplplj` (which this plan carries as `- From-Backlog:`) may be closed `done`: this plan delivers its last surviving clause, the rest having shipped in `5af28bbb`. That item carries no release gate, so none is inherited.
