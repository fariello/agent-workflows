# IPD: remove the per-package verify_digest.py scripts and prove the manifest already covers them

- Date: 2026-09-05
- Kind: child
- Concern: EVERY GENERATED SKILL PACKAGE SHIPS A 20-LINE DIGEST SCRIPT THAT NOTHING CALLS AND THAT COMPUTES NOTHING. `build_skill_package` emits `scripts/verify_digest.py` per workflow (`host_adapters.py:386-390`), so an install writes 45 of them, each with a different baked-in constant and otherwise identical. The body is one comparison: `return observed == EXPECTED_DIGEST`, where `observed` arrives as `argv[1]` and defaults to the empty string. So the script does not derive a digest from anything; it is a pure equality check awaiting a caller that must already know the answer. MEASURED: `verify_digest` appears in shipped code ONLY in `host_adapters.py` (the generator) and in `tests/test_installer_skill_emission.py:78,133` (which assert the file is EMITTED, not that it works); every other hit in the repo is a session transcript or the executed IPD that created it. Meanwhile `.aw/system/managed-sections.json` already records a `sha256` for all 135 skill files INCLUDING each `verify_digest.py`, so the integrity of these scripts is itself tracked by a mechanism that does not need them.
- Scope: Stop emitting `scripts/verify_digest.py` from the skill-package generator, remove the emitted copies, and PROVE FIRST that no capability is lost. Deliberately narrow: the `semantic-digest` FRONTMATTER KEY in `SKILL.md` is NOT removed (it is the portable signal a host could read), only the per-package script is. EXCLUDES the `.agents/skills` directory decision (research `sx0cqv` owns it), excludes any change to SKILL.md structure or wording (research `ti73qs` owns it), excludes `compute_workflow_semantic_digest` and the shared `workflow_profile.semantic_digest` scheme, and excludes anything about `aw workflow check-generated`'s own scope.
- Scope-Paths: agent_workflows/host_adapters.py, tests/test_installer_skill_emission.py, tests/test_host_adapters_skills.py
- Item-Dependencies: none
- Status: to-review
- Set: skilldigest
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8fhjjc

## Workflow history

- 2026-09-05 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after an `aw install` run surfaced 134 untracked skill-package files and the maintainer asked why 45 near-identical digest scripts exist when INDEX/manifest files already carry digests. TWO CORRECTIONS TO MY OWN EARLIER CLAIMS IN THAT CONVERSATION, recorded so neither is inherited as fact. (1) I told the maintainer that `aw workflow check-generated` already does what these scripts would do. THAT IS FALSE: `workflow_cli._run_check_generated` (`:302`) compiles workflow PACKAGES and compares against `render_generated_files`; `grep -n skill agent_workflows/workflow_cli.py` returns NOTHING, so skill packages are outside its scope entirely. This plan therefore may NOT claim equivalence with that command, and E-01 exists to establish what the real coverage is rather than assuming it. (2) I described the emitted files as landing in the wrong directory because I omitted `--to-aw`. Also false: `engine.SKILLS_DIR` is `.agents/skills` for BOTH layouts by an explicit documented decision (`engine.py:155-163`), and `resolve_skills_dir` returns it unconditionally, so no flag would have changed it. That question is now research `sx0cqv` and is OUT of this plan's scope. WHAT IS ACTUALLY VERIFIED AND MOTIVATES THE PLAN: 45 scripts, 45 distinct checksums, 20 lines each; zero callers in shipped code; the body is a bare equality check over `argv[1]`; and `managed-sections.json` already stores a `sha256` per skill file (135 entries), which is a stronger integrity signal than a self-reported constant inside the artifact being checked. THE ONE HYPOTHESIS THIS PLAN MUST FALSIFY BEFORE DELETING, and the reason E-01 precedes everything: that an EXTERNAL host runtime is expected to invoke these scripts. Nothing in this repository can settle that, which is why research `sx0cqv` Question 4 asks it directly, and why E-01 requires an explicit in-repo answer plus a recorded decision about whether to wait for that research.

## Goal

Stop shipping 45 copies of an uncalled comparison function, without losing any verification the repository actually performs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove nothing is lost

- [ ] E-01 ESTABLISH THE REAL COVERAGE BEFORE DELETING ANYTHING, and record it as findings rather than as prose confidence. Three questions, each answered with a command and its output.
  (a) WHO CALLS `verify_digest.py`? Search shipped code, tests, CI workflows, `Makefile`, pre-commit config, the installed bundle, and any docs. Distinguish a call that EXECUTES the script from an assertion that it EXISTS. The plan's premise is that only the latter exist (`tests/test_installer_skill_emission.py:78,133`); confirm or refute.
  (b) WHAT DOES `managed-sections.json` ACTUALLY GUARANTEE for these files? Show that a skill file's `sha256` is recorded and that a modified skill file is DETECTED by whatever consumes that manifest. If nothing consumes it for drift detection, say so plainly, because then this plan removes one unused mechanism while leaving another unused, which is still an improvement but must not be described as "the manifest already covers it".
  (c) WHAT IS `aw workflow check-generated`'s REAL SCOPE? Paste evidence for whether it touches skill packages. The plan asserts it does NOT (`workflow_cli.py:302`, no `skill` reference in the module); verify and record, since an earlier claim of equivalence was wrong and that error is exactly what this item exists to prevent repeating.
  - Depends on: none
  - Expected outcome: three answered questions with pasted evidence; an explicit statement of what verification EXISTS versus what these scripts PURPORT to provide; no deletion yet.
  - Execution state: pending

- [ ] E-02 DECIDE AND RECORD THE EXTERNAL-CALLER QUESTION, which is the only way this deletion goes wrong. If a host runtime executes scripts inside a skill package, these files may be an interface rather than dead weight.
  WHAT THE REPOSITORY CAN ESTABLISH: `V1_HOSTS` is `("opencode", "codex")` (`host_adapters.py:64`), and neither is documented here as executing skill scripts. That is evidence of absence within this repo, NOT evidence about the hosts themselves.
  WHAT IT CANNOT: whether any host does so in reality. Research `sx0cqv` Question 4 asks precisely this ("Do any hosts invoke a script inside a skill package to validate it?").
  SO CHOOSE EXPLICITLY, and record which: (i) proceed now on the in-repo evidence, accepting that a future host convention would require re-adding a generated file, which is cheap because it is generated; or (ii) block this plan on `sx0cqv` landing. Do NOT proceed silently as if the question did not exist. If you choose (i), state the reversal cost in one sentence so a later reader can weigh it.
  - Depends on: E-01
  - Expected outcome: a recorded decision naming the option taken, its evidence, and the cost of being wrong; if (ii), the plan gains a typed dependency on the research instead of proceeding.
  - Execution state: pending

### Task group 2: remove it

- [ ] E-03 Stop emitting the script from the generator and drop it from the package contract.
  THE EXACT SEAM: `build_skill_package` appends a `SkillResource(relative_path="scripts/verify_digest.py", kind="script", content=_render_digest_verify_script(...))` (`host_adapters.py:386-390`). Remove that resource and the now-unused renderer, and check whether `SkillResource`'s `kind="script"` vocabulary still has any producer; if it does not, say so rather than leaving a dead branch.
  KEEP THE FRONTMATTER `semantic-digest`. It is a portable, host-readable signal and `validate_skill_package` requires it (`:478`); removing it is a different and larger decision. This plan deletes the SCRIPT, not the digest.
  KEEP `compute_workflow_semantic_digest` (`:253`), which delegates to the canonical `workflow_profile.semantic_digest` scheme. It feeds the frontmatter and must not be touched.
  MIND `validate_skill_package` AND ITS PARITY RULE (`:448`, `:511-526`): it enforces that authoritative behavior is never inlined and that the package shape is exactly `SKILL.md` plus `reference/` plus `scripts/`. If a validation asserts a `scripts/` member exists, it must be updated in the same change or the generator will fail its own validator.
  - Depends on: E-02
  - Expected outcome: the generator emits two files per package instead of three; the frontmatter digest and the canonical digest function are untouched; `validate_skill_package` passes on the new shape; no dead renderer or unreachable `kind` branch is left behind.
  - Execution state: pending

- [ ] E-04 Update the tests that pin the three-file shape, and prove the emitted tree matches the manifest afterwards.
  TWO KNOWN ASSERTIONS: `tests/test_installer_skill_emission.py:78` names `.agents/skills/release-review/scripts/verify_digest.py` explicitly, and `:133` asserts it for every skill. Both must change from "asserts present" to "asserts ABSENT", which is what makes the removal enforced rather than merely done.
  ALSO CHECK `tests/test_host_adapters_skills.py` and the file-count assertions: the executed IPD that created this recorded `num skill files: 135` / `num SKILL.md: 45`, so a count-based assertion will move from 135 to 90. Find every such number rather than only the two greppable paths.
  PROVE THE MANIFEST STAYS CONSISTENT: after a fresh install, the `managed-sections.json` skill entries must equal the on-disk skill fileset, which is the invariant `test_fresh_install_emits_skill_packages_and_records_manifest` already asserts. A stale manifest entry for a file no longer emitted would leave a phantom the prune path might chase.
  - Depends on: E-03
  - Expected outcome: tests assert the script is absent; every count-based assertion updated; a fresh install's manifest skill entries equal the on-disk set with no orphan; full suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SKILL PACKAGE IS DELIBERATELY A POINTER, NOT A COPY: `reference/canonical-body.md` says so in its own generated text, and `validate_skill_package` fails a package that inlines canonical content (`host_adapters.py:511-526`). Nothing in this plan may weaken that.
- THE DIGEST SCHEME IS ALREADY SHARED, NOT FORKED: `compute_workflow_semantic_digest` delegates to `workflow_profile.semantic_digest` with a comment stating "no second digest algorithm is invented". So the frontmatter digest is a legitimate reuse; only its per-package SCRIPT is redundant.
- `managed-sections.json` IS THE INSTALL MANIFEST and records `sha256` per file for all 342 tracked files, 135 of them skill files. That is the integrity mechanism a self-reported constant inside the artifact cannot match, because a modified artifact can also modify its own expected value.
- `.agents/skills` IS A DELIBERATE HOST-CONSUMPTION PATH for both layouts (`engine.py:155-163`), not migration residue. Out of scope here; research `sx0cqv` owns whether it is still justified.
- THE SKILL EMISSION PATH HAS AN ORPHAN-PRUNE GUARD (`in_framework_namespace`), so files removed from the generator are expected to be pruned on the next install rather than lingering; E-04's manifest check is what proves that works for this removal.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | **45 SCRIPTS, 45 DISTINCT CHECKSUMS, 20 LINES EACH, DIFFERING ONLY IN A CONSTANT AND A DOCSTRING NAME.** That is the shape of generated duplication, not of a mechanism. | `find .agents -name verify_digest.py \| wc -l` = 45; distinct md5 count = 45; `wc -l` = 20 per file |
| F-2 | **THE SCRIPT COMPUTES NOTHING.** It compares `argv[1]` against a baked-in constant and defaults `observed` to `''`, so a bare invocation always exits 1. Any caller must already possess the digest, which means the script adds no capability its caller lacks. | generated body: `EXPECTED_DIGEST = "..."`, `def verify(observed): return observed == EXPECTED_DIGEST`, `observed = argv[1] if len(argv) > 1 else ''` |
| F-3 | **ZERO CALLERS IN SHIPPED CODE.** `verify_digest` appears only in the generator and in two test assertions that it is EMITTED; every other hit is a session transcript or the executed IPD that introduced it. No CI step, `Makefile` target, or pre-commit hook runs it. | `host_adapters.py:387`; `tests/test_installer_skill_emission.py:78`, `:133`; all other matches under `opencode-recovery/` or `.aw/records/plans/executed/` |
| F-4 | **THE MANIFEST ALREADY CARRIES A STRONGER SIGNAL.** `managed-sections.json` records `sha256` for all 135 skill files, including each `verify_digest.py`. An external hash is strictly better than a self-reported constant, because an artifact that is tampered with can also rewrite its own expected value. | `.aw/system/managed-sections.json`: 342 file entries, 135 with `skills` in the key, each carrying `sha256` |
| F-5 | **`aw workflow check-generated` DOES NOT COVER SKILL PACKAGES, correcting an earlier claim made in conversation.** It loads and recompiles workflow packages; the module contains no `skill` reference at all. So the honest justification for this removal is F-3 and F-4, NOT equivalence with that command. | `workflow_cli.py:302` (`_run_check_generated` -> `_loader.load_package` / `_compiler.render_generated_files`); `grep -n skill agent_workflows/workflow_cli.py` returns nothing |
| F-6 | THE FRONTMATTER DIGEST IS A SEPARATE, LEGITIMATE MECHANISM and is REQUIRED by the package validator, so it must survive this plan. Conflating the two is the likeliest way to over-delete. | `validate_skill_package` requires `semantic-digest` in frontmatter (`host_adapters.py:478`); `compute_workflow_semantic_digest:253` reuses `workflow_profile.semantic_digest` |
| F-7 | THE ONLY UNFALSIFIED HYPOTHESIS IS AN EXTERNAL CALLER. `V1_HOSTS` is `("opencode", "codex")` and neither is recorded here as executing skill scripts, but this repository cannot establish host behavior. Research `sx0cqv` Question 4 asks it directly, which is why E-02 forces an explicit decision rather than an assumption. | `host_adapters.py:64`; research prompt `sx0cqv` Question 4 |
| F-8 | REVERSAL IS CHEAP, which is what makes proceeding on in-repo evidence defensible: the file is GENERATED, so re-adding it is one resource entry in `build_skill_package` plus a regenerate, not a hand-migration of 45 files. | `build_skill_package` resource list at `host_adapters.py:376-393` |

## Proposed changes (ordered, validatable)

1. Establish real coverage with commands and output: who calls the script, what the manifest guarantees, what `check-generated` actually scopes (E-01).
2. Decide the external-caller question explicitly, recording the option taken and the cost of being wrong (E-02).
3. Remove the resource and its renderer from the generator, keeping the frontmatter digest and the canonical digest function (E-03).
4. Flip the tests from asserts-present to asserts-absent, update every count, and prove manifest/on-disk parity after a fresh install (E-04).

## Deferred / out of scope (with reason)

- THE `.agents/skills` DIRECTORY DECISION. It is a documented deliberate choice for both layouts (`engine.py:155-163`), and whether it remains justified depends on host behavior this repository cannot observe. Owned by research `sx0cqv`.
- SKILL.md STRUCTURE, WORDING, TRIGGER DESCRIPTIONS, AND BYTE BUDGET. The maintainer observed these look poorly optimized for reliable agent execution; that is a design question needing external evidence. Owned by research `ti73qs`.
- REMOVING THE `semantic-digest` FRONTMATTER KEY. It is required by the validator and is the portable signal a host could actually read (F-6). A separate, larger decision.
- `compute_workflow_semantic_digest` AND `workflow_profile.semantic_digest`. The shared scheme stays; this plan removes a consumer, not the algorithm.
- WIDENING `aw workflow check-generated` TO COVER SKILL PACKAGES. It is a real gap (F-5) and arguably the right follow-up, but adding coverage is a different change from removing dead weight, and bundling them would let a new feature ride in under a cleanup.
- ANY CHANGE TO `reference/canonical-body.md` or the pointer discipline.

## Scope check

- Over-scope: none. Every edit removes the script, its renderer, or an assertion that pinned it.
- Under-scope, DELIBERATE and stated: after this plan, skill packages have NO self-verification of their own. That is the point, since the self-verification never ran, but it means integrity rests entirely on `managed-sections.json` and whatever consumes it. E-01(b) must state plainly whether anything does, so the end state is described honestly rather than as "already covered".
- Under-scope: `aw workflow check-generated` still does not cover skill packages after this plan (F-5). Recorded as a follow-up, not fixed here.

## Required tests / validation

- E-01's three answers, each with a pasted command and output. This is the load-bearing evidence, because an earlier equivalence claim in this plan's own origin conversation was FALSE, and repeating that error would justify a deletion on a wrong premise.
- The generator emits exactly two files per package; a fresh install produces 90 skill files rather than 135, with the number derived from a real install rather than asserted.
- Tests assert the script is ABSENT (flipped from present), so a future re-introduction fails.
- `validate_skill_package` passes on the two-file shape, and no validation still requires a `scripts/` member.
- Frontmatter `semantic-digest` still present and unchanged in every generated `SKILL.md`; `compute_workflow_semantic_digest` untouched.
- Manifest parity after a fresh install: `managed-sections.json` skill entries equal the on-disk skill fileset, with no orphan entry for a removed file.
- Full suite BARE (`python3 -m pytest`), compared against your own pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (backlog `dh0uno`).
- `aw check all` NO-WORSENING against your own fresh baseline; do NOT claim it passes.

## Spec / documentation sync

- `.aw/records/specs/20260725-0957-01-external-delivery-and-skills.spec.md` describes the skill-package shape; if it enumerates the three files, update it to two and note why.
- If any README or workflow doc documents `scripts/verify_digest.py` as part of the package contract, update it; otherwise state N/A with the paths checked.
- Do NOT amend the spec's `.agents/skills` path language; that belongs to research `sx0cqv`.

## Open questions

### OQ-01: Should this wait for research `sx0cqv` to answer whether any host executes skill scripts?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT BLOCKING because E-02 forces the decision explicitly at execution time and either answer is defensible on the evidence available then. The case for proceeding now: zero callers in shipped code (F-3), the script computes nothing (F-2), the manifest already carries a stronger external hash (F-4), and reversal is one generated resource entry (F-8). The case for waiting: `sx0cqv` Question 4 asks exactly this, and if some host does invoke a package script, these files are a nascent interface rather than dead weight, in which case the right change is to make them DO something rather than to delete them. Chosen default is PROCEED, on the ground that a generated artifact with no caller and no computation is not an interface, and that re-adding it costs one line. The maintainer may prefer to sequence this after the research; if so, add a typed dependency rather than leaving the plan ambiguous.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste all three answers with their commands and output. (a) The caller search, distinguishing EXECUTES from ASSERTS-EXISTS, over shipped code, tests, CI, `Makefile`, pre-commit, and docs. (b) A skill file's `sha256` in `managed-sections.json` AND a demonstration of whether anything actually consumes it for drift detection; if nothing does, state that plainly rather than implying coverage. (c) Evidence for `check-generated`'s scope. STATE EXPLICITLY that the earlier equivalence claim was wrong and what replaced it, so the record cannot be misread as confirming it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the recorded decision naming which option was taken (proceed on in-repo evidence, or block on `sx0cqv`), the evidence it rests on, and one sentence on the cost of being wrong. If proceeding, confirm the in-repo limit is stated honestly: `V1_HOSTS` not executing skill scripts is evidence about this repository, NOT about the hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a generated package showing exactly two files. Paste a generated `SKILL.md` showing `semantic-digest` STILL PRESENT, which is the over-deletion this item must avoid. Paste `validate_skill_package` passing on the new shape. Paste evidence no dead renderer or unreachable `kind="script"` branch remains, or state that the `kind` vocabulary retains another producer.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the flipped assertions showing the script is asserted ABSENT (not merely removed from the expected list), since only that prevents silent re-introduction. Paste the real emitted file count from a fresh install (expected 90, derived not asserted) and every count-based assertion you updated. Paste the manifest/on-disk parity check with no orphan entry. Then `aw check all` no-worsening against your own baseline and the bare full suite with counts compared against your own pre-change measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 4 E-leaves across 2 task groups, one concern: remove an uncalled generated artifact without losing verification. Task group 1 is entirely evidence and decision, which is deliberate: the plan's origin conversation contained a FALSE equivalence claim, so establishing real coverage is a distinct deliverable from acting on it. Task group 2 is the removal (generator, then the tests that pin it). E-03 and E-04 are separate because the generator change is small while the test update has to find every count-based assertion, not just the two greppable paths.

Open questions: OQ-01 (wait for `sx0cqv` or proceed) is non-blocking, with a recorded default of PROCEED and E-02 forcing an explicit decision at execution time. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It has no plan dependencies. It is deliberately NOT dependent on research `sx0cqv`, but OQ-01 records that the maintainer may prefer to sequence it after that research lands.

Scope fence: touch ONLY `agent_workflows/host_adapters.py`, `tests/test_installer_skill_emission.py`, and `tests/test_host_adapters_skills.py`. Do NOT remove the `semantic-digest` frontmatter key. Do NOT touch `compute_workflow_semantic_digest` or `workflow_profile.semantic_digest`. Do NOT change the `.agents/skills` path (research `sx0cqv`). Do NOT change SKILL.md structure, wording, or trigger descriptions (research `ti73qs`). Do NOT widen `aw workflow check-generated` to cover skill packages, however tempting given F-5. Do NOT weaken the pointer discipline or `validate_skill_package`'s no-inlining rule. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. Do NOT justify this removal by claiming `aw workflow check-generated` covers skill packages: it does not (F-5), and that false claim is what this plan's E-01 exists to correct. Do NOT describe the end state as "the manifest already covers it" unless E-01(b) actually demonstrated a consumer of those hashes; if none exists, say the packages now have no self-verification and that the previous self-verification never ran. Do NOT report the external-caller question as settled by this repository (F-7).

Execution contract: RE-READ `host_adapters.py` and locate `build_skill_package`, its resource list, and `validate_skill_package` BY SYMBOL before editing, never by the line numbers in this plan. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
