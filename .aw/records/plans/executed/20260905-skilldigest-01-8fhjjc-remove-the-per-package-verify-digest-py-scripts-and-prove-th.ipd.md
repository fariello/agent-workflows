# IPD: remove the per-package verify_digest.py scripts and prove the manifest already covers them

- Date: 2026-09-05
- Kind: child
- Concern: EVERY GENERATED SKILL PACKAGE SHIPS A 20-LINE DIGEST SCRIPT WHOSE ONLY CALLER IS A TEST OF ITSELF, AND WHICH COMPUTES NOTHING. `build_skill_package` emits `scripts/verify_digest.py` per workflow (`host_adapters.py:386-390`), so an install writes 45 of them, each with a different baked-in constant and otherwise identical. The body is one comparison: `return observed == EXPECTED_DIGEST`, where `observed` arrives as `argv[1]` and defaults to the empty string. So the script does not derive a digest from anything; it is a pure equality check awaiting a caller that must already know the answer. MEASURED at HEAD `484994ec`: `verify_digest` appears in shipped code ONLY in `host_adapters.py` (the generator), in `tests/test_installer_skill_emission.py:78,133` (which assert the file is EMITTED), and in `tests/test_host_adapters_skills.py:140` (`test_deterministic_script_verifier_has_direct_test`, which `exec`s the rendered content and calls `verify()`/`main()` - the ONE place it is actually EXECUTED, and a test whose sole subject is the artifact itself). Every other hit is a session transcript, the executed IPD that created it, the `sx0cqv` research prompt, or the untracked `.aw/inbox/` drops. Meanwhile the install manifest records a `sha256` for every emitted skill file INCLUDING each `verify_digest.py`, so their integrity is tracked by a mechanism that does not need them - but see F-9 for exactly WHICH code paths consume that hash, because "the manifest covers it" is too strong.
- Scope: Stop emitting `scripts/verify_digest.py` from the skill-package generator, remove the emitted copies, and PROVE FIRST that no capability is lost. Deliberately narrow: the `semantic-digest` FRONTMATTER KEY in `SKILL.md` is NOT removed (it is the portable signal a host could read), only the per-package script is. Includes the ONE doc that states the three-file package contract (`docs/skill-selection.md:16`), because leaving it would make shipped documentation false and that doc is test-required to exist (`tests/test_docs.py:37`). EXCLUDES the `.agents/skills` directory decision (research `sx0cqv` owns it), excludes any change to SKILL.md structure or wording (research `ti73qs` owns it), excludes `compute_workflow_semantic_digest` and the shared `workflow_profile.semantic_digest` scheme, excludes anything about `aw workflow check-generated`'s own scope, and excludes FIXING the installer's inability to retire a stale manifest row (F-10: measure and state it, do not re-engineer the manifest here).
- Scope-Paths: agent_workflows/host_adapters.py, tests/test_installer_skill_emission.py, tests/test_host_adapters_skills.py, docs/skill-selection.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: skilldigest
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8fhjjc

## Workflow history
- 2026-09-08 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): Lane recovered and merged during the stranded-lane recovery; integration had been refused by the binary whole-repo suite gate (32ij2j/xtklpd)
- 2026-09-07 approved (aw set): status set to approved

- 2026-09-06 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): OQ-01 RESOLVED BY MAINTAINER DECISION; status UNCHANGED (`reviewed`), no code touched, no E or V item added or removed. The maintainer asked what the open question actually was, and on being given it in plain terms ruled PROCEED: delete the per-package `verify_digest.py` scripts now rather than waiting for research `sx0cqv`. The question was put as a scope and risk-appetite call, which is the maintainer's to make, because whether a THIRD-PARTY host executes a script inside a skill package is a fact about other vendors' tools and is not settleable from this repository. The decision rests on the four findings already measured in review: the script performs no computation (F-2, it compares an argument against a constant baked in at generation time and never reads or hashes the package it claims to protect), its only caller is a test of the artifact itself (F-3, as corrected by PR-001), the manifest already carries a stronger content hash with real consumers (F-9), and reversal is one generated resource entry through the standing `extra_resources` seam (F-8). The counter-case was weighed and rejected: `sx0cqv` Question 4 asks exactly this and a positive answer would make these files an interface to finish rather than dead weight, but a generated file with no caller, no computation, and no read of its own package is not an interface, and shipping a file that IMPLIES tamper detection it does not provide is worse than shipping nothing. THREE EDITS APPLIED so an executor cannot re-open a settled question: OQ-01 moved `open` -> `resolved` with the ruling and its date; E-02 converted from a DECISION item into a RECORDING item that restates the ruling and is forbidden from adding a typed dependency on the research; V-02's evidence bar now FAILS the validation if the question is re-decided or recorded as still open. Also recorded for a later reader: if `sx0cqv` eventually reports that some host does invoke package scripts, the correct response is a NEW plan building a real verifier, not a revert of this one. `aw ipd lint` conforming before and after. Plan still requires explicit human approval before execution.
- 2026-09-05 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED; GO - PENDING HUMAN APPROVAL. Verified at HEAD `484994ec`. Lint conforming at `--phase author` and again at `--phase review-finalize`. Every claim re-measured by installing the bundle into throwaway repos, because `.agents/skills` is NOT tracked here and does not exist in the working tree (`git ls-files .agents` is empty), so the plan's 45/135/342 counts describe an installed target rather than this checkout; that is now recorded as a convention so the executor does not read an empty grep as a refuted finding. SIX FINDINGS. PR-001 (HIGH): the plan's own headline premise "ZERO CALLERS IN SHIPPED CODE" was FALSE - `tests/test_host_adapters_skills.py:140` `exec`s the rendered script and calls `verify()`/`main()`, so it has one executing caller, and worse, that call site does `next(r for r in resources if r.kind == "script")`, which RAISES StopIteration once the resource is gone, so E-04 as written would have hit an ERROR it never anticipated. The honest and still-sufficient claim (the only caller is a test of the artifact itself) now replaces it, and E-04 deletes that test rather than adapting it. PR-002 (HIGH): E-04 validated only a FRESH install, but no user gets one; the upgrade path was measured and deviates three ways, so a new E-05 owns it - the manifest keeps all 135 rows against 90 files on disk because `manifest.py` has no row-deletion API (handled downstream as `missing`/already-absent, so accepted not fixed), `prune_stale`'s `git rm` REFUSES when the files are staged-but-uncommitted and `git_run` escalates that to SystemExit aborting the install partway (which is precisely this checkout's current state per the origin run record), and a non-git target keeps 45 empty `scripts/` dirs. PR-003 (MEDIUM): `docs/skill-selection.md:16` documents the three-file contract and describes the script as one that "recomputes the parity digest", which is false TODAY and doubly false after; scope widened to include it (new E-06) since shipping contradictory code and docs in one commit is not a defensible narrower scope, and the spec was measured N/A rather than left as a conditional instruction. PR-004 (MEDIUM): the plan required a bare `python3 -m pytest`, but the install tests are `pytest.mark.slow` and `addopts` carries `-m 'not slow'`, so a bare run deselects all 10 - a green bare suite would have been evidence of nothing; `make test-all` is now mandatory. PR-005 (MEDIUM): E-04 sent the executor hunting count-based assertions that do not exist (the 135/45 figures were smoke output), and E-03 mispredicted `validate_skill_package` requiring a `scripts/` member; both measured and corrected, including the real near-miss, which returns exactly one finding when the router is not re-rendered. PR-006 (LOW): "the manifest already covers it" was too strong, so F-9 now names the consumers that exist (`plan_uninstall` marks a tampered skill file `drifted`, demonstrated live; re-install idempotency) and the limit that matters (the warn-on-overwrite and prune-consent paths are gated on `COMMAND_SHIM_DIRS`, so an edited skill file is silently overwritten on upgrade). The honesty rule now forbids all four claims that were made and found wrong. OQ-01 left non-blocking and unchanged: reversal is one resource entry through the standing `extra_resources` seam, which is the strongest argument for proceeding ahead of research `sx0cqv`.
- 2026-09-05 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after an `aw install` run surfaced 134 untracked skill-package files and the maintainer asked why 45 near-identical digest scripts exist when INDEX/manifest files already carry digests. TWO CORRECTIONS TO MY OWN EARLIER CLAIMS IN THAT CONVERSATION, recorded so neither is inherited as fact. (1) I told the maintainer that `aw workflow check-generated` already does what these scripts would do. THAT IS FALSE: `workflow_cli._run_check_generated` (`:302`) compiles workflow PACKAGES and compares against `render_generated_files`; `grep -n skill agent_workflows/workflow_cli.py` returns NOTHING, so skill packages are outside its scope entirely. This plan therefore may NOT claim equivalence with that command, and E-01 exists to establish what the real coverage is rather than assuming it. (2) I described the emitted files as landing in the wrong directory because I omitted `--to-aw`. Also false: `engine.SKILLS_DIR` is `.agents/skills` for BOTH layouts by an explicit documented decision (`engine.py:155-163`), and `resolve_skills_dir` returns it unconditionally, so no flag would have changed it. That question is now research `sx0cqv` and is OUT of this plan's scope. WHAT IS ACTUALLY VERIFIED AND MOTIVATES THE PLAN: 45 scripts, 45 distinct checksums, 20 lines each; zero callers in shipped code; the body is a bare equality check over `argv[1]`; and `managed-sections.json` already stores a `sha256` per skill file (135 entries), which is a stronger integrity signal than a self-reported constant inside the artifact being checked. THE ONE HYPOTHESIS THIS PLAN MUST FALSIFY BEFORE DELETING, and the reason E-01 precedes everything: that an EXTERNAL host runtime is expected to invoke these scripts. Nothing in this repository can settle that, which is why research `sx0cqv` Question 4 asks it directly, and why E-01 requires an explicit in-repo answer plus a recorded decision about whether to wait for that research.

## Goal

Stop shipping 45 copies of an uncalled comparison function, without losing any verification the repository actually performs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove nothing is lost

- [x] E-01 ESTABLISH THE REAL COVERAGE BEFORE DELETING ANYTHING, and record it as findings rather than as prose confidence. Three questions, each answered with a command and its output.
  (a) WHO CALLS `verify_digest.py`? Search shipped code, tests, CI workflows (`.github/workflows/`), `Makefile`, pre-commit config, the installed bundle, and docs. Distinguish a call that EXECUTES the script from an assertion that it EXISTS. NOTE THE PLAN'S ORIGINAL PREMISE WAS WRONG AND HAS BEEN CORRECTED (see F-3): there IS one executing caller, `tests/test_host_adapters_skills.py:140` `test_deterministic_script_verifier_has_direct_test`, which `exec`s the rendered script and calls `verify()`/`main()`. Re-confirm at YOUR HEAD and state whether any caller EXISTS OUTSIDE A TEST OF THE ARTIFACT ITSELF, because that (not "zero callers") is the honest justification.
  (b) WHAT DOES THE INSTALL MANIFEST ACTUALLY GUARANTEE for these files? Show a skill file's recorded `sha256` AND name the code paths that CONSUME it, with a live demonstration rather than a code reading. F-9 records what this review measured: `plan_uninstall` (`engine.py:3999`) classifies a hand-edited skill file as `drifted` and preserves it, and `write_file`/`_record_written` (`engine.py:1905`) make re-install idempotent. Also state the LIMIT honestly: the user-modification WARNING path (`engine.py:2021-2024`) and the stale-prune consent path (`:2269-2272`) are gated on `COMMAND_SHIM_DIRS`, so a skill file is silently overwritten on upgrade, not warned about. Do NOT write "the manifest already covers it" without this distinction.
  (c) WHAT IS `aw workflow check-generated`'s REAL SCOPE? Paste evidence for whether it touches skill packages. The plan asserts it does NOT (`workflow_cli.py:302`, no `skill` reference in the module); verify and record, since an earlier claim of equivalence was wrong and that error is exactly what this item exists to prevent repeating.
  - Depends on: none
  - Expected outcome: three answered questions with pasted evidence; an explicit statement of what verification EXISTS versus what these scripts PURPORT to provide; the corrected caller count (one executing caller, itself a test of the artifact) stated rather than the original "zero"; no deletion yet.
  - Execution state: performed

- [x] E-02 DECIDE AND RECORD THE EXTERNAL-CALLER QUESTION, which is the only way this deletion goes wrong. If a host runtime executes scripts inside a skill package, these files may be an interface rather than dead weight.
  WHAT THE REPOSITORY CAN ESTABLISH: `V1_HOSTS` is `("opencode", "codex")` (`host_adapters.py:64`), and neither is documented here as executing skill scripts. That is evidence of absence within this repo, NOT evidence about the hosts themselves.
  WHAT IT CANNOT: whether any host does so in reality. Research `sx0cqv` Question 4 asks precisely this ("Do any hosts invoke a script inside a skill package to validate it?").
  THE DECISION IS ALREADY MADE; DO NOT RE-OPEN IT. The maintainer ruled on 2026-09-06, after being shown the measured position, that this plan PROCEEDS on the in-repo evidence and does NOT wait for `sx0cqv` (OQ-01, now `Status: resolved`). This E-item is therefore a RECORDING item, not a decision item: restate the ruling, cite the four findings it rests on (F-2 the script computes nothing, F-3 its only caller is a test of the artifact itself, F-9 the manifest carries a stronger content hash with real consumers, F-8 reversal is one generated resource entry through the standing `extra_resources` seam), and state the reversal cost in one sentence.
  DO NOT ADD A TYPED DEPENDENCY on the research, and do not re-litigate option (ii). The ruling's stated ground: a generated file with no caller, no computation, and no read of its own package is not an interface, and shipping a file that IMPLIES a tamper-detection guarantee it does not provide is worse than shipping nothing. If `sx0cqv` later reports that some host does invoke package scripts, the correct response is a NEW plan building a real verifier, NOT a revert of this one; say so in the record so a later reader does not mistake this for an oversight.
  - Depends on: E-01
  - Expected outcome: the maintainer's ruling is recorded with its date, its four supporting findings, and the reversal cost; no typed dependency on `sx0cqv` is added; the record states what a contrary research result would imply (a new plan, not a revert).
  - Execution state: performed

### Task group 2: remove it, then prove the removal on both install paths

- [x] E-03 Stop emitting the script from the generator and drop it from the package contract.
  THE EXACT SEAM: `build_skill_package` appends a `SkillResource(relative_path="scripts/verify_digest.py", kind="script", content=_render_digest_verify_script(...))` (`host_adapters.py:386-390`). Remove that resource and the now-unused renderer, and check whether `SkillResource`'s `kind="script"` vocabulary still has any producer; if it does not, say so rather than leaving a dead branch.
  KEEP THE FRONTMATTER `semantic-digest`. It is a portable, host-readable signal and `validate_skill_package` requires it (`:478`); removing it is a different and larger decision. This plan deletes the SCRIPT, not the digest.
  KEEP `compute_workflow_semantic_digest` (`:253`), which delegates to the canonical `workflow_profile.semantic_digest` scheme. It feeds the frontmatter and must not be touched.
  THE ROUTER LISTS ITS OWN RESOURCES, SO THIS IS NOT A ONE-LINE DELETE. `_render_skill_main_file` renders a `## Package resources` list from the resources sequence (`host_adapters.py:340-347`), and `validate_skill_package` cross-checks every backticked path in the router against the declared set. MEASURED IN REVIEW: dropping the resource WITHOUT the router regenerating from the same list yields exactly `["router references resource 'scripts/verify_digest.py' not in package"]`. Because the router is rendered FROM `resources`, removing the resource before the render call fixes this by construction; verify it rather than assuming, and paste `validate_skill_package(...) == []`.
  MIND `validate_skill_package`'s NO-INLINING RULE (`:448`, `:511-526`). MEASURED: it does NOT require a `scripts/` member, so no validator edit is needed; the two-file shape validates clean. Confirm this at your HEAD rather than inheriting the claim.
  ALSO DECIDE `extra_resources` (`:354`, `:392-393`), a public keyword argument of `build_skill_package` with ZERO callers in the repo. After this change `kind="script"` has no producer at all. Do NOT delete `extra_resources` (out of scope, and it is the documented extension seam that makes F-8's reversal cheap): state explicitly that the `kind` vocabulary retains `script` as an ACCEPTED-BUT-UNPRODUCED value reachable only through that seam, so a reader does not mistake it for dead code to prune later.
  - Depends on: E-02
  - Expected outcome: the generator emits two files per package instead of three; the router's own `## Package resources` list no longer names the script (proved by `validate_skill_package` returning `[]`, not merely by inspection); the frontmatter digest and the canonical digest function are untouched; `_render_digest_verify_script` is deleted; the `kind="script"` vocabulary is explicitly documented as producer-free-but-reachable via `extra_resources` rather than silently left dangling.
  - Execution state: performed

- [x] E-04 Update the tests that pin the three-file shape, INCLUDING the one that would ERROR rather than fail.
  THREE CALL SITES, NOT TWO. The plan originally named only the two greppable `verify_digest` paths and MISSED the one that breaks hardest:
  (i) `tests/test_installer_skill_emission.py:78` names `.agents/skills/release-review/scripts/verify_digest.py` explicitly (asserts present -> flip to ABSENT).
  (ii) `tests/test_installer_skill_emission.py:133` asserts it for every skill (asserts present -> flip to ABSENT).
  (iii) `tests/test_host_adapters_skills.py:140` `test_deterministic_script_verifier_has_direct_test` does `next(r for r in self.pkg.resources if r.kind == "script")`, which RAISES `StopIteration` once no script resource exists. MEASURED IN REVIEW: it does not fail an assertion, it ERRORS. This whole test's subject is the deleted artifact, so DELETE the test rather than adapt it (adapting would be inventing a new subject); state in the commit why deleting a test is correct here, and add in its place an assertion that the package has NO `kind == "script"` resource, so the removal is enforced at the generator level and not only at the install level.
  COUNT-BASED ASSERTIONS: MEASURED IN REVIEW at HEAD `484994ec`, `grep -n "135\|45\b\|90\b" tests/test_installer_skill_emission.py tests/test_host_adapters_skills.py` returns NOTHING, so no count literal needs changing; the executed IPD's `135`/`45` figures were smoke output, not assertions. Re-run that grep and record the result rather than hunting for numbers that are not there. The real counts (135 -> 90 files, 45 -> 45 packages) belong in V-04 as DERIVED measurements.
  PROVE THE MANIFEST STAYS CONSISTENT on a FRESH install: `test_fresh_install_emits_skill_packages_and_records_manifest` asserts manifest skill entries equal the on-disk skill fileset. MEASURED IN REVIEW: fresh install with the resource removed gives 90 == 90, invariant holds. Note these tests are `pytest.mark.slow` (`tests/test_installer_skill_emission.py:32`), so a BARE `python3 -m pytest` DESELECTS all 10 of them; they must be run explicitly (`make test-all`, or the file with `-m ''`) or this E-item's work is not exercised at all.
  - Depends on: E-03
  - Expected outcome: (i) and (ii) assert ABSENT; (iii) deleted and replaced by a no-script-resource assertion at the generator level; the count-literal grep re-run and its empty result recorded; a fresh install's manifest skill entries equal the on-disk set; the slow install suite actually run, not silently deselected.
  - Execution state: performed

- [x] E-05 MEASURE AND RECORD THE UPGRADE PATH, which the plan originally ignored by testing only a FRESH install. A real user does not get a fresh install; they get an upgrade over the 135-file tree, and that path behaves differently in three ways this review measured and none of which the plan mentioned.
  (a) THE MANIFEST KEEPS 45 STALE ROWS. `prune_stale` (`engine.py:2243`) deletes the 45 files from disk, but nothing retires their manifest rows: `manifest.py` has no delete/forget method, and `_record_written` only ADDS. MEASURED: after an upgrade, on-disk skill files = 90 while manifest skill entries = 135, of which 45 name `verify_digest.py`. `plan_uninstall` then classifies exactly those 45 as `missing` (`engine.py:4020`), and `uninstall_repo` prints `<path> already absent (manifest entry stale)` (`:4073`). So the phantom is HARMLESS and ALREADY HANDLED - but it is real, it contradicts the fresh-install invariant on an upgraded repo, and V-05 must state it rather than let a later reader discover the two numbers disagree.
  (b) IN A GIT REPO WITH THOSE FILES ALREADY STAGED-BUT-UNCOMMITTED, THE UPGRADE ABORTS. MEASURED: `prune_stale` calls `git rm --quiet` (`:2325`), git refuses with `error: the following file has changes staged in the index`, and `git_run` (`:1775-1780`) turns any nonzero git exit into `SystemExit` - so the install dies partway. This is EXACTLY the state a maintainer is in today after `aw install` staged 135 new skill files (the origin conversation's own situation, per `.aw/records/runs/run-20260905T050043Z-639569/state.json`). RECORD this as a precondition: commit or unstage the skill tree before the first upgrade past this change. Do NOT fix `git_run`'s error handling here (out of scope), but do NOT let it surprise the next person either.
  (c) A NON-GIT TARGET IS LEFT WITH 45 EMPTY `scripts/` DIRECTORIES. MEASURED: with git the `git rm` removes the parent dir as a side effect (0 left); without git, `destination.unlink()` (`:2326`) leaves the empty dir, because `prune_stale` has no dir-pruning step (only `run_deep_cleanup` does, `:3930-3945`). Cosmetic, not a correctness bug. State it; do not add dir-pruning to `prune_stale` in this plan.
  - Depends on: E-03
  - Expected outcome: all three upgrade behaviors measured on a real throwaway install-then-upgrade (not reasoned about), each recorded with its command and output, and each explicitly classified as accepted-and-documented rather than fixed-here.
  - Execution state: performed

- [x] E-06 Correct the one shipped document that states the three-file package contract, so the docs do not ship a false claim.
  THE EXACT LINE: `docs/skill-selection.md:16` reads "`scripts/verify_digest.py`: a deterministic script that recomputes the parity digest." That sentence is doubly wrong after this change and was ALREADY wrong before it: the script never recomputed anything, it compared `argv[1]` to a constant (F-2). Remove the bullet and leave the two-file contract stated accurately.
  WHY IT IS IN SCOPE despite the original Scope-Paths omitting it: this doc is required to EXIST by `tests/test_docs.py:37`, it is the only prose statement of the package contract, and leaving it would mean shipping documentation contradicted by the code in the same commit.
  ALSO CHECK, and state N/A with the paths if clean: `agent_workflows/engine.py:18,21,2230` mention `scripts/` generically as part of the package shape. MEASURED IN REVIEW: these are module docstring and comment prose, not a contract, and `:2230` describes what the PRUNE SCAN may encounter (which must still tolerate a legacy `scripts/` path on an upgraded repo). Decide deliberately whether to touch them; if you do, do not narrow the prune-scan comment in a way that suggests `scripts/` can never appear.
  DO NOT amend the spec `.aw/records/specs/20260725-0957-01-external-delivery-and-skills.spec.md`: MEASURED, it never enumerates the three files (it discusses `SKILL.md` discovery tiers and is `deferred`), so the plan's original "if it enumerates the three files" instruction resolves to N/A.
  - Depends on: E-03
  - Expected outcome: `docs/skill-selection.md` states the real two-file contract with no `verify_digest.py` bullet; `tests/test_docs.py` still passes; the engine docstring/comment mentions explicitly decided (changed or left, with the reason); the spec confirmed N/A by measurement rather than by assumption.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE SKILL PACKAGE IS DELIBERATELY A POINTER, NOT A COPY: `reference/canonical-body.md` says so in its own generated text, and `validate_skill_package` fails a package that inlines canonical content (`host_adapters.py:511-526`). Nothing in this plan may weaken that.
- THE DIGEST SCHEME IS ALREADY SHARED, NOT FORKED: `compute_workflow_semantic_digest` delegates to `workflow_profile.semantic_digest` with a comment stating "no second digest algorithm is invented". So the frontmatter digest is a legitimate reuse; only its per-package SCRIPT is redundant.
- `managed-sections.json` IS THE INSTALL MANIFEST and records `sha256` per file for all 342 tracked files, 135 of them skill files. That is the integrity mechanism a self-reported constant inside the artifact cannot match, because a modified artifact can also modify its own expected value.
- `.agents/skills` IS A DELIBERATE HOST-CONSUMPTION PATH for both layouts (`engine.py:155-163`), not migration residue. Out of scope here; research `sx0cqv` owns whether it is still justified.
- THE SKILL EMISSION PATH HAS AN ORPHAN-PRUNE GUARD (`in_framework_namespace`, `engine.py:1806-1822`), so files removed from the generator are pruned on the next install rather than lingering. VERIFIED IN REVIEW on a throwaway install-then-upgrade: all 45 are pruned. E-05 is what records how that prune behaves in the three cases the fresh-install test cannot see.
- `.agents/skills` IS NOT TRACKED IN THIS REPOSITORY AND DOES NOT EXIST IN THE WORKING TREE. `git ls-files .agents` returns nothing and the directory is absent, and this repo's own committed manifest has 202 file entries with ZERO skill rows. The plan's F-1/F-4 counts (45 scripts, 135 skill files, 342 manifest entries) therefore describe an INSTALLED TARGET, not this checkout; they were reproduced in review by installing into a throwaway repo. Any executor re-measuring them must install into a scratch target first, or the greps will come back empty and look like the finding was wrong.
- THE PACKAGE ROUTER IS RENDERED FROM ITS OWN RESOURCE LIST, so the resource set and the router text cannot drift independently, and `validate_skill_package` enforces that coupling by cross-checking backticked paths. This is why the removal is one edit to the resources list and not two edits that must agree (F-11).
- THE INSTALL SUITE IS `slow`-MARKED AND DESELECTED BY DEFAULT (F-12). The repo convention of running the suite BARE is correct for routine work and WRONG as the sole evidence for an installer-visible change; `make test-all` exists for exactly this and is what this plan requires.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | **45 SCRIPTS, 45 DISTINCT CHECKSUMS, 20 LINES EACH, DIFFERING ONLY IN A CONSTANT AND A DOCSTRING NAME.** That is the shape of generated duplication, not of a mechanism. | `find .agents -name verify_digest.py \| wc -l` = 45; distinct md5 count = 45; `wc -l` = 20 per file |
| F-2 | **THE SCRIPT COMPUTES NOTHING.** It compares `argv[1]` against a baked-in constant and defaults `observed` to `''`, so a bare invocation always exits 1. Any caller must already possess the digest, which means the script adds no capability its caller lacks. | generated body: `EXPECTED_DIGEST = "..."`, `def verify(observed): return observed == EXPECTED_DIGEST`, `observed = argv[1] if len(argv) > 1 else ''` |
| F-3 | **ONE CALLER, AND IT IS A TEST OF THE ARTIFACT ITSELF (corrected in review; the original "ZERO CALLERS" was wrong).** `tests/test_host_adapters_skills.py:140` `test_deterministic_script_verifier_has_direct_test` `exec`s the rendered script and calls `verify()`/`main()`, so the script IS executed in the suite. Two further sites merely assert it is EMITTED. No CI workflow, `Makefile` target, or pre-commit hook runs it. THE HONEST CLAIM IS THEREFORE NARROWER AND STILL SUFFICIENT: the artifact's only caller is a test whose sole subject is the artifact, which is self-justifying coverage and not a capability any other code depends on. | `host_adapters.py:387`; `tests/test_installer_skill_emission.py:78`, `:133`; `tests/test_host_adapters_skills.py:140`; `grep -rn verify_digest Makefile .pre-commit-config.yaml .github/workflows/` -> no match; all other matches under `opencode-recovery/`, `.aw/records/`, or the untracked `.aw/inbox/` |
| F-4 | **THE MANIFEST CARRIES A STRONGER SIGNAL, AND IT IS GENUINELY CONSUMED - for detection, not for warning.** The install manifest records a `sha256` per emitted skill file. An external hash beats a self-reported constant, because a tampered artifact can also rewrite its own expected value. See F-9 for exactly which paths consume it and where the coverage stops. | measured on a throwaway install: 342 file entries, 135 under `.agents/skills/`, each with a `sha256`; consumers at `engine.py:3999` (`plan_uninstall`), `:1905` (`_record_written`), `manifest.py:174` (`matches_recorded`) |
| F-5 | **`aw workflow check-generated` DOES NOT COVER SKILL PACKAGES, correcting an earlier claim made in conversation.** It loads and recompiles workflow packages; the module contains no `skill` reference at all. So the honest justification for this removal is F-3 and F-4, NOT equivalence with that command. | `workflow_cli.py:302` (`_run_check_generated` -> `_loader.load_package` / `_compiler.render_generated_files`); `grep -n skill agent_workflows/workflow_cli.py` returns nothing |
| F-6 | THE FRONTMATTER DIGEST IS A SEPARATE, LEGITIMATE MECHANISM and is REQUIRED by the package validator, so it must survive this plan. Conflating the two is the likeliest way to over-delete. | `validate_skill_package` requires `semantic-digest` in frontmatter (`host_adapters.py:478`); `compute_workflow_semantic_digest:253` reuses `workflow_profile.semantic_digest` |
| F-7 | THE ONLY UNFALSIFIED HYPOTHESIS IS AN EXTERNAL CALLER. `V1_HOSTS` is `("opencode", "codex")` and neither is recorded here as executing skill scripts, but this repository cannot establish host behavior. Research `sx0cqv` Question 4 asks it directly, which is why E-02 forces an explicit decision rather than an assumption. | `host_adapters.py:64`; research prompt `sx0cqv` Question 4 |
| F-8 | REVERSAL IS CHEAP, which is what makes proceeding on in-repo evidence defensible: the file is GENERATED, so re-adding it is one resource entry in `build_skill_package` plus a regenerate, not a hand-migration of 45 files. The `extra_resources` keyword is a standing injection seam for exactly this, so even a per-host re-add needs no signature change. | `build_skill_package` resource list at `host_adapters.py:376-393`; `extra_resources` at `:354`, `:392-393` |
| F-9 | **WHAT THE MANIFEST HASH ACTUALLY BUYS, MEASURED, because "already covered" was too strong.** CONSUMED: `plan_uninstall` classifies a hand-edited skill file as `drifted` and PRESERVES it (measured: tampering with one `SKILL.md` moved exactly that path into `drifted`), and `_record_written`/`matches_recorded` make re-install idempotent (measured: second install prunes 0 skill files). NOT CONSUMED: the user-modification WARNING on overwrite (`engine.py:2021-2024`) and the stale-prune CONSENT prompt (`:2269-2272`) are both gated on `COMMAND_SHIM_DIRS`, which does not include the skills dir, so an edited skill file is silently overwritten on upgrade with no warning. There is also no standalone "verify the installed tree against the manifest" verb. So the honest end state is: drift is DETECTED at uninstall time and on re-install, and is NOT surfaced at upgrade time. | `engine.py:3999-4034`, `:4073`, `:2021-2024`, `:2269-2272`, `:208` (`COMMAND_SHIM_DIRS`), `manifest.py:163-184`; measured live on a throwaway install |
| F-10 | **THE UPGRADE PATH IS NOT THE FRESH PATH, and the plan originally validated only the fresh one.** Measured on throwaway installs: (a) after an upgrade the manifest keeps all 135 skill rows while disk has 90, because `manifest.py` has no row-deletion API and `prune_stale` never retires a row; `plan_uninstall` then reports those 45 as `missing` and `uninstall_repo` prints `already absent (manifest entry stale)`, so the phantom is handled but the fresh-install equality invariant does NOT hold on an upgraded repo. (b) When the 45 files are staged-but-uncommitted, `git rm` refuses and `git_run` raises `SystemExit`, aborting the install partway - which is precisely today's state in this checkout per the origin run record. (c) Without git, 45 empty `scripts/` dirs remain, because only `run_deep_cleanup` prunes empty dirs. | `manifest.py` (no delete method); `engine.py:2243-2331` (`prune_stale`), `:1775-1780` (`git_run` -> `SystemExit`), `:4020`, `:4073`, `:3930-3945`; `.aw/records/runs/run-20260905T050043Z-639569/state.json` (135 skill files staged `A`) |
| F-11 | **THE ROUTER LISTS ITS OWN RESOURCES, so dropping the resource without re-rendering the router FAILS THE VALIDATOR.** Measured: removing the script resource while leaving the rendered `## Package resources` list intact yields exactly `["router references resource 'scripts/verify_digest.py' not in package"]`. Because `_render_skill_main_file` is called WITH the resources list, removing the resource first fixes this by construction - but it is the one way a careless edit breaks the generator's own validator. Measured clean afterwards: `validate_skill_package` returns `[]` on the two-file shape, and it never required a `scripts/` member. | `host_adapters.py:340-347` (resource list rendering), `:487-495` (backticked-path cross-check), measured both broken and clean shapes |
| F-12 | **THE INSTALL TESTS THAT MATTER ARE `slow` AND A BARE SUITE RUN SKIPS THEM ALL.** `tests/test_installer_skill_emission.py:32` sets `pytestmark = pytest.mark.slow`, and `pyproject.toml:169` `addopts` carries `-m 'not slow'`, so a bare `python3 -m pytest` deselects all 10 install tests. Measured: `--collect-only` reports `no tests collected (10 deselected)`. A green bare suite therefore proves NOTHING about this change's install behavior; `make test-all` is required. | `tests/test_installer_skill_emission.py:32`; `pyproject.toml:169`; `Makefile:29-32` (`test-all` clears the filter with `-m ''`) |
| F-13 | THE `kind="script"` VOCABULARY LOSES ITS ONLY PRODUCER but stays reachable, so it is not dead code. `SkillResource.kind` documents `reference | template | script`; after this change `reference` is the sole producer, while `script` (and `template`, already producer-free today) remain injectable through the caller-facing `extra_resources` argument. That argument has ZERO in-repo callers, which is why the vocabulary must be described as an extension seam rather than pruned. | `host_adapters.py:180-189` (kind vocabulary), `:354`/`:392-393` (`extra_resources`); `grep -rn extra_resources agent_workflows tests` -> generator only |

## Proposed changes (ordered, validatable)

1. Establish real coverage with commands and output: who calls the script (one caller, itself a test of the artifact), what the manifest guarantees and where it stops, what `check-generated` actually scopes (E-01).
2. Decide the external-caller question explicitly, recording the option taken and the cost of being wrong (E-02).
3. Remove the resource and its renderer from the generator, keeping the frontmatter digest and the canonical digest function, and prove the router re-renders so the validator stays clean (E-03).
4. Flip the two asserts-present sites to asserts-absent, DELETE the self-referential script test that would otherwise error, and prove fresh-install manifest/on-disk parity (E-04).
5. Measure the UPGRADE path, not just the fresh path: the 45 stale manifest rows, the staged-file `git rm` abort, and the empty dirs left on a non-git target (E-05).
6. Correct `docs/skill-selection.md`, the one shipped doc stating a three-file contract (E-06).

## Deferred / out of scope (with reason)

- THE `.agents/skills` DIRECTORY DECISION. It is a documented deliberate choice for both layouts (`engine.py:155-163`), and whether it remains justified depends on host behavior this repository cannot observe. Owned by research `sx0cqv`.
- SKILL.md STRUCTURE, WORDING, TRIGGER DESCRIPTIONS, AND BYTE BUDGET. The maintainer observed these look poorly optimized for reliable agent execution; that is a design question needing external evidence. Owned by research `ti73qs`.
- REMOVING THE `semantic-digest` FRONTMATTER KEY. It is required by the validator and is the portable signal a host could actually read (F-6). A separate, larger decision.
- `compute_workflow_semantic_digest` AND `workflow_profile.semantic_digest`. The shared scheme stays; this plan removes a consumer, not the algorithm.
- WIDENING `aw workflow check-generated` TO COVER SKILL PACKAGES. It is a real gap (F-5) and arguably the right follow-up, but adding coverage is a different change from removing dead weight, and bundling them would let a new feature ride in under a cleanup.
- ANY CHANGE TO `reference/canonical-body.md` or the pointer discipline.

## Scope check

- Over-scope: none. Every edit removes the script, its renderer, an assertion that pinned it, or the one doc sentence that documented it.
- Scope widened during review, DELIBERATELY: `docs/skill-selection.md` was added to `Scope-Paths` (E-06). It states the three-file contract in prose and is required to exist by `tests/test_docs.py:37`; shipping code and documentation that contradict each other in the same commit is not a defensible narrower scope.
- Under-scope, DELIBERATE and stated: after this plan, skill packages have NO self-verification of their own. That is the point, since the self-verification only ever ran in a test of itself (F-3), but it means integrity rests entirely on the install manifest and its actual consumers. F-9 states exactly what those are and where they stop (drift detected at uninstall and on re-install; NOT surfaced at upgrade time), so the end state is described honestly rather than as "already covered".
- Under-scope: `aw workflow check-generated` still does not cover skill packages after this plan (F-5). Recorded as a follow-up, not fixed here.
- Under-scope, MEASURED AND ACCEPTED, not fixed here (F-10): the installer cannot retire a stale manifest row, so an upgraded repo carries 45 phantom entries. Harmless (`uninstall_repo` reports them as already-absent) and a manifest-API change is a different concern with a much larger blast radius. E-05 records it so the next reader does not rediscover the two disagreeing numbers as a bug.
- Under-scope, MEASURED AND ACCEPTED, not fixed here (F-10b): `git_run` turning any nonzero git exit into `SystemExit` makes the upgrade abort partway when the pruned files are staged. Fixing the installer's error handling is out of scope; E-05 turns it into a stated precondition instead.

## Required tests / validation

- E-01's three answers, each with a pasted command and output. This is the load-bearing evidence, because an earlier equivalence claim in this plan's own origin conversation was FALSE, and repeating that error would justify a deletion on a wrong premise. The caller answer must name the one EXECUTING caller (F-3), not repeat "zero".
- The generator emits exactly two files per package; a fresh install produces 90 skill files rather than 135, with the number derived from a real install rather than asserted.
- Tests assert the script is ABSENT (flipped from present), so a future re-introduction fails; and the self-referential script test is DELETED rather than left to error on `StopIteration`.
- `validate_skill_package` returns `[]` on the two-file shape (F-11 shows the near-miss returns exactly one finding), and no validation requires a `scripts/` member.
- Frontmatter `semantic-digest` still present and unchanged in every generated `SKILL.md`; `compute_workflow_semantic_digest` untouched; no `verify_digest` string left in the router body.
- Manifest parity after a FRESH install: skill entries equal the on-disk skill fileset. Separately, the UPGRADE path measured and its three known deviations recorded (F-10), since the fresh-install invariant does NOT hold on an upgraded repo.
- `make test-all` (the FULL suite, `-m ''`), compared against your own pre-change measurement at the HEAD you started from. A bare `python3 -m pytest` is NOT sufficient here and must not be offered as the evidence: per F-12 it deselects all 10 install tests, which are the only ones that exercise this change end to end. Within whichever runner you use, do not add `-n0`, a second `-q`, or `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (backlog `dh0uno`). Throwaway install targets outside the repo are fine and expected for E-05.
- `aw check all` NO-WORSENING against your own fresh baseline; do NOT claim it passes. For orientation only, it reported 15 findings at HEAD `484994ec`, none of them in this plan's Scope-Paths; re-measure rather than trusting that number.

## Spec / documentation sync

- `docs/skill-selection.md:16` DOES document `scripts/verify_digest.py` as part of the package contract, and its description ("recomputes the parity digest") is false even today. Correcting it is E-06 and is IN SCOPE.
- `.aw/records/specs/20260725-0957-01-external-delivery-and-skills.spec.md`: MEASURED N/A. It discusses `SKILL.md` discovery tiers and the probe protocol and never enumerates the three package files; it is also `deferred`. Do not edit it.
- Checked and clean (state N/A with these paths in V-06): `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, and every other file under `docs/`. The only remaining in-code mentions are prose in `agent_workflows/engine.py:18,21,2230`, decided in E-06.
- Do NOT amend the spec's `.agents/skills` path language; that belongs to research `sx0cqv`.

## Open questions

### OQ-01: Should this wait for research `sx0cqv` to answer whether any host executes skill scripts?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-06 BY MAINTAINER DECISION: PROCEED, do NOT wait for research `sx0cqv`. Asked and answered as a scope/risk-appetite call, which is the maintainer's to make, because whether a THIRD-PARTY host executes a script inside a skill package is a fact about other vendors' tools and is not settleable from this repository's evidence. The decision rests on the four measured findings supporting removal: the script performs no computation (F-2, it compares an argument against a baked-in constant and never reads or hashes the package it claims to protect), its only caller is a test of the artifact itself (F-3, as corrected by review PR-001), the manifest already carries a stronger content hash with real consumers (F-9), and reversal costs one generated resource entry through the standing `extra_resources` seam (F-8). The counter-case is recorded and was weighed: `sx0cqv` Question 4 asks exactly this, and a positive answer would make these files a nascent interface to finish rather than dead weight. It was rejected on the ground that a generated file with no caller, no computation, and no read of its own package is not an interface, and that shipping a file which IMPLIES a tamper-detection guarantee it does not provide is worse than shipping nothing. NO TYPED DEPENDENCY on `sx0cqv` is to be added; E-02 still records the decision at execution time, and it now records THIS ruling rather than re-deciding. If `sx0cqv` later reports that some host does invoke package scripts, the correct response is a NEW plan that builds a real verifier, not a revert of this one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste all three answers with their commands and output. (a) The caller search, distinguishing EXECUTES from ASSERTS-EXISTS, over shipped code, tests, CI, `Makefile`, pre-commit, and docs; it MUST name `tests/test_host_adapters_skills.py:140` as the executing caller and state that its subject is the artifact itself. An answer that repeats "zero callers" is WRONG and fails this item. (b) A skill file's recorded `sha256` AND a live demonstration of a consumer: tamper with one installed `SKILL.md` and paste `plan_uninstall` reporting it as `drifted`. Then state the LIMIT: no upgrade-time warning for skill files, because the warn/consent paths are gated on `COMMAND_SHIM_DIRS`. (c) Evidence for `check-generated`'s scope. STATE EXPLICITLY that the earlier equivalence claim was wrong and what replaced it, so the record cannot be misread as confirming it.
  - Observed evidence: All three answered at pre-change HEAD `8b4e15702830dd713bff56bc49fb23642cc06ee3`.
    (a) CALLER SEARCH, split by category. `git grep -n verify_digest -- agent_workflows/` -> ONE hit,
    `agent_workflows/host_adapters.py:387: relative_path="scripts/verify_digest.py"`, i.e. the GENERATOR,
    not a caller. `-- tests/` -> `tests/test_installer_skill_emission.py:78` and `:133`, both
    ASSERTS-EXISTS (`assertIn` on an installed path). `-- .github/ Makefile .pre-commit-config.yaml` ->
    `(no match in CI/Makefile/pre-commit)`. `-- docs/ README.md ARCHITECTURE.md CHANGELOG.md` ->
    `docs/skill-selection.md:16` only, prose. THE ONE EXECUTING CALLER IS
    `tests/test_host_adapters_skills.py:140`, `test_deterministic_script_verifier_has_direct_test`,
    which does `next(r for r in self.pkg.resources if r.kind == "script")`, `exec(compile(...))`s the
    rendered content, and calls `ns["verify"](...)` / `ns["main"](...)`. ITS SUBJECT IS THE ARTIFACT
    ITSELF: every assertion in it is about the rendered script's own behavior, so it is self-justifying
    coverage and not a capability any other code depends on. THE CLAIM "ZERO CALLERS" IS FALSE AND IS
    NOT MADE ANYWHERE IN THIS EXECUTION; note the greppable count is 4 hits but the EXECUTING count is
    1, and that one is invisible to a `verify_digest` grep because it selects the resource by `kind`.
    (b) MANIFEST GUARANTEE, measured on a throwaway install (`tmp/t_e01b`, 346 manifest file entries,
    135 skill rows, 135 skill files on disk, 45 of them `verify_digest.py`). Recorded row for
    `.agents/skills/advise-architect/scripts/verify_digest.py`:
    `{"host": "", "kind": "file", "logical_id": "", "sha256": "77d7f2cc0946a50a72298608eefe5bd0a24758712e275ddf5081560e3e977ee7"}`;
    for that package's `SKILL.md`:
    `{"host": "", "kind": "file", "logical_id": "", "sha256": "561c48e95dcbace470a7a0036665f0538c0c282ed8b0a69fc82a648f972a4198"}`.
    LIVE CONSUMER DEMONSTRATED, not read: before tampering, `plan_uninstall` gave
    `drifted count = 0 | victim drifted? False` and `victim in remove? True`; after appending
    `<!-- hand edit -->` to that `SKILL.md`, `drifted count = 1`,
    `drifted list = ['.agents/skills/advise-architect/SKILL.md']`, `victim in remove? False` - so the
    hash is genuinely consumed to PRESERVE a user-edited skill file instead of deleting it.
    THE LIMIT, ALSO MEASURED, NOT INFERRED: with that file still hand-edited, a re-install printed NO
    warning at all (stdout lines matching the path or `Warning` -> `(NONE - no warning was printed)`),
    reported `.agents/skills/advise-architect/SKILL.md [overwrite]`, and the edit was GONE afterwards
    (`victim still hand-edited after the upgrade? False`). Cause: the warn path (`engine.py:2068-2070`)
    and the prune-consent path (`:2316-2318`) both gate on `COMMAND_SHIM_DIRS`, which is
    `(".opencode/commands", ".claude/commands")` (`engine.py:208-211`) and excludes the skills dir. So
    the honest end state is: drift is DETECTED at uninstall time and on re-install, and is NOT surfaced
    at upgrade time; there is no verify-installed-tree verb. "The manifest already covers it" is NOT
    claimed.
    (c) `aw workflow check-generated` SCOPE: `grep -n skill agent_workflows/workflow_cli.py` ->
    `(NO MATCH - zero 'skill' references in the module)`. `_run_check_generated` (`:302`) loops
    `_loader.load_package(pkg)` then `_compiler.render_generated_files(_compiler.compile_workflow(...))`
    and diffs against `_generated/`; `render_generated_files` (`workflow_compiler.py:281-296`) emits
    exactly `_generated/prompt.md`, `manifest.json`, `evidence.json`, `catalog-row.json`,
    `command.json`, and `packets/<step>.json` - no skill path. THE EARLIER EQUIVALENCE CLAIM WAS WRONG:
    this command does NOT do what the digest scripts purported to do and does not cover skill packages
    at all. What replaced it as the justification for removal is F-3 (the only caller is a test of the
    artifact) plus F-9 as bounded above, NOT equivalence with this command.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the recorded ruling (maintainer, 2026-09-06: PROCEED on in-repo evidence, no dependency on `sx0cqv`), the four findings it rests on (F-2, F-3, F-9, F-8), and one sentence on the cost of being wrong. Confirm the in-repo limit is stated honestly: `V1_HOSTS` not executing skill scripts is evidence about this repository, NOT about the hosts, and the external question remains unanswered rather than answered negatively. Confirm NO typed dependency on `sx0cqv` was added, and that the record says a contrary research result calls for a new plan rather than a revert. Re-deciding this question, or recording it as still open, is a FAILED validation.
  - Observed evidence: THE RULING WAS RECORDED, NOT RE-DECIDED. Written verbatim into the run register
    (`.aw/state/lane-submissions/run-20260908T030809Z-1812970/07-8fhjjc/attempt-1/decisions-and-questions.md`,
    section "RECORDED RULING (E-02, not a decision of mine)") and restated in the commit message of
    `ab13e2b6`: "MAINTAINER RULING, 2026-09-06, OQ-01: PROCEED on the in-repo evidence; do NOT wait for
    research `sx0cqv` to answer whether any host executes a script inside a skill package. No typed
    dependency on that research is added."
    THE FOUR FINDINGS IT RESTS ON, each re-measured this turn rather than copied: F-2 the script
    computes nothing (body is `return observed == EXPECTED_DIGEST` with
    `observed = argv[1] if len(argv) > 1 else ''`; it never reads or hashes its own package, so a bare
    invocation always exits 1); F-3 its only executing caller is
    `tests/test_host_adapters_skills.py:140`, a test whose sole subject is the artifact (see V-01(a));
    F-9 the manifest carries a stronger content hash WITH a demonstrated consumer (`plan_uninstall`
    moved a tampered `SKILL.md` into `drifted`, measured live in V-01(b)) AND a measured limit (no
    upgrade-time warning); F-8 reversal is one `SkillResource` entry through the standing
    `extra_resources` seam, which this turn additionally PINNED with a new test
    (`test_script_kind_remains_reachable_via_extra_resources`, injecting a `kind="script"` resource and
    getting `validate_skill_package(injected) == []`).
    COST OF BEING WRONG, one sentence: if `sx0cqv` later reports that some host does invoke a script
    inside a skill package, that host gains nothing from the file deleted here (it computed nothing and
    read nothing), so the correct response is a NEW plan that builds a real verifier, not a revert of
    this one - stated in exactly those terms in both the register and the commit message.
    THE IN-REPO LIMIT IS STATED HONESTLY: `V1_HOSTS` is `("opencode", "codex")`
    (`agent_workflows/host_adapters.py:64`) and neither is documented HERE as executing skill scripts,
    which is evidence about THIS REPOSITORY and NOT about those hosts' actual behavior. The external
    question REMAINS UNANSWERED rather than answered negatively; the register says so in those words.
    NO TYPED DEPENDENCY ON `sx0cqv` WAS ADDED: `- Item-Dependencies: none` is unchanged in this plan's
    metadata, and `grep -n "sx0cqv" ` over the plan finds it only in prose (Scope, F-7, OQ-01, the
    deferred/out-of-scope list), never in a dependency field. OQ-01 remains `Status: resolved` and was
    NOT re-opened or re-decided.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `sorted(pkg.to_files())` showing exactly two paths. Paste the generated `SKILL.md` showing `semantic-digest:` STILL PRESENT in frontmatter, which is the over-deletion this item must avoid, AND showing no `verify_digest` string anywhere in the router body (the `## Package resources` list must have re-rendered). Paste `validate_skill_package(pkg)` returning `[]` - the empty list, not a description of it - because F-11 shows the one plausible mistake here produces exactly one finding. Paste `grep -n _render_digest_verify_script agent_workflows/` returning nothing. State explicitly that `kind="script"` now has no producer but remains reachable via `extra_resources`, and that you did NOT delete `extra_resources`.
  - Observed evidence: Measured on the post-change tree, package `release-review`.
    `sorted(pkg.to_files())` -> EXACTLY TWO PATHS:
    `.agents/skills/release-review/SKILL.md`
    `.agents/skills/release-review/reference/canonical-body.md`
    `sorted({r.kind for r in pkg.resources})` -> `['reference']`; `any(r.kind == "script" ...)` -> `False`.
    `validate_skill_package(pkg)` -> `[]`  (the empty list, printed via `repr`).
    `"verify_digest" in pkg.main_file_content` -> `False`;  `"semantic-digest:" in ...` -> `True`.
    GENERATED `SKILL.md`, full, showing the frontmatter digest RETAINED and the `## Package resources`
    list RE-RENDERED without the script:
    ```
    ---
    name: release-review
    description: Use when the user asks to release-review (Full pre-release repository review and hardening: deep audit through eight personas, the Fix Bar, fix/validate/report, push and release decisions). Do not use for unrelated requests or when no release-review action was requested.
    semantic-digest: d0ca355c2dd254933a694380f7f205c3d9d0d54eb589d856dc0cbf992c9f48c8
    ---

    # Skill: release-review

    This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

    ## Canonical behavior

    Read and execute @.aw/system/workflows/release-review/README.md. Treat that file as the controlling instruction and follow it fully.

    - Canonical semantic digest: `d0ca355c2dd254933a694380f7f205c3d9d0d54eb589d856dc0cbf992c9f48c8`

    ## Explicit invocation (works even if this skill is disabled)

        read and execute .aw/system/workflows/release-review/README.md

    ## Package resources

    - `reference/canonical-body.md` (reference)
    ```
    `grep -rn "_render_digest_verify_script" agent_workflows/` -> `(nothing - correct)`. (Note: an
    initial run matched `agent_workflows/__pycache__/host_adapters.cpython-314.pyc`, a STALE BYTECODE
    artifact, not source; caches were cleared and the source grep is empty. Recorded so a later reader
    does not mistake a `.pyc` hit for a surviving definition.)
    F-11's COUPLING RE-CONFIRMED IN BOTH DIRECTIONS, so the clean result is not a coincidence:
    re-inserting `- `scripts/verify_digest.py` (script)` into the rendered router text while the
    resource is absent yields exactly
    `["router references resource 'scripts/verify_digest.py' not in package"]` - one finding, as F-11
    predicted. Because `_render_skill_main_file` is called WITH the `resources` list, removing the
    resource before the render fixes this by construction.
    `kind="script"` NOW HAS NO PRODUCER BUT REMAINS REACHABLE via `extra_resources`, and I did NOT
    delete `extra_resources`: it is still a keyword parameter of `build_skill_package` and still
    extends the resource list. Proved rather than asserted -
    `build_skill_package(wf, extra_resources=[SkillResource("scripts/x.py", kind="script", ...)])`
    yields paths `[SKILL.md, reference/canonical-body.md, scripts/x.py]`, kinds
    `['reference', 'script']`, and `validate_skill_package(injected) == []`. The vocabulary status is
    now documented on `SkillResource`'s docstring as ACCEPTED-BUT-UNPRODUCED / extension seam, so it is
    not mistaken for dead code to prune. `compute_workflow_semantic_digest` was NOT touched (unchanged
    in `git diff`), and the `semantic-digest` frontmatter key was NOT removed.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the flipped assertions showing the script is asserted ABSENT (not merely removed from the expected list), since only that prevents silent re-introduction. Paste the deletion of `test_deterministic_script_verifier_has_direct_test` together with the new no-script-resource assertion that replaces it, and one sentence on why deleting a test is correct when its subject is the deleted artifact. Paste the re-run count-literal grep and its (expected empty) result. Paste the fresh-install manifest/on-disk equality with the derived numbers (expected 90 == 90, and 45 `SKILL.md` routers). Then paste the ACTUAL `make test-all` output - NOT a bare `python3 -m pytest`, which per F-12 deselects all 10 install tests and would prove nothing here - with the `git rev-parse HEAD` it was measured at, compared against your own pre-change `make test-all` baseline.
  - Observed evidence: THE PLAN NAMED THREE CALL SITES; ONE WAS MISCHARACTERIZED AND IS HANDLED
    DIFFERENTLY, WITH THE REASON MEASURED (see decision 07-8fhjjc-D4 in the run register).
    SITE (ii), `tests/test_installer_skill_emission.py:133` - FLIPPED TO ABSENT, as instructed:
    ```
    -            self.assertIn(f".agents/skills/{name}/scripts/verify_digest.py", on_disk)
    +            # IPD 8fhjjc: the per-package digest script is NO LONGER emitted. Asserted
    +            # ABSENT (not merely dropped from the expected list) so a re-introduction fails.
    +            self.assertNotIn(f".agents/skills/{name}/scripts/verify_digest.py", on_disk)
    +        # Stronger than per-name: NOTHING under any package's scripts/ dir is emitted.
    +        self.assertEqual(
    +            [p for p in on_disk if "/scripts/" in p],
    +            [],
    +            "a fresh install must emit no per-package script files",
    +        )
    ```
    So absence is ASSERTED, not merely dropped from an expected list, and the added `assertEqual`
    is strictly stronger: it fails on ANY emitted `scripts/` member, not just this filename.
    SITE (i), `tests/test_installer_skill_emission.py:78` - NOT an asserts-emitted site, so flipping it
    to ABSENT would have been WRONG. It asserts
    `INS.in_framework_namespace(".agents/skills/release-review/scripts/verify_digest.py")`, and
    `in_framework_namespace` (`engine.py:1855-1870`) is a PREFIX predicate over `SKILLS_DIR`: measured,
    it returns `True` for `.../scripts/verify_digest.py`, `.../scripts/anything-at-all.py`, and
    `.../SKILL.md` alike. Asserting `False` would demand the predicate STOP adopting paths under
    `.agents/skills/`, which is exactly what `prune_stale`'s defense-in-depth guard
    (`engine.py:2313-2314`, `if not in_framework_namespace(rel): continue`) needs in order to DELETE a
    legacy `scripts/verify_digest.py` on an upgraded repo - the very prune E-05(a) measures deleting 45
    files. Flipping it would have made the test contradict E-05. Retargeted to a neutral legacy path
    instead, preserving the predicate's real contract:
    ```
    +        # A legacy `scripts/` path must STILL be recognized as framework-owned: the
    +        # generator no longer emits one (IPD 8fhjjc), but an upgraded repo carries them
    +        # until pruned, and prune only reaches what this predicate adopts.
             self.assertTrue(
                 INS.in_framework_namespace(
    -                ".agents/skills/release-review/scripts/verify_digest.py"
    +                ".agents/skills/release-review/scripts/legacy-artifact.py"
                 )
             )
    ```
    SITE (iii), `tests/test_host_adapters_skills.py:140` - DELETED, exactly as instructed. The whole
    body of `test_deterministic_script_verifier_has_direct_test` (`next(... r.kind == "script")`, the
    `exec(compile(...))`, and the four `verify()`/`main()` assertions) is gone. WHY DELETING A TEST IS
    CORRECT HERE, one sentence: the test's entire subject was the rendered script's own runtime
    behavior, so with the artifact gone there is nothing left for it to be a test OF, and "adapting" it
    would mean inventing an unrelated new subject under a name describing something that no longer
    exists. Replaced at the GENERATOR level, per the E-item, by
    `test_no_per_package_script_resource_is_emitted`, which asserts no `kind == "script"` resource, the
    exact two-path resource set, and no `verify_digest` string in the router; plus
    `test_script_kind_remains_reachable_via_extra_resources`, which pins F-13's seam so the reversal
    path F-8 depends on is TESTED rather than asserted in prose.
    COUNT-LITERAL GREP RE-RUN as instructed:
    `grep -n "135\|45\b\|90\b" tests/test_installer_skill_emission.py tests/test_host_adapters_skills.py`
    -> `(no matches - confirmed, no count literal needs changing)`. The review's finding holds; the
    135/45 figures were smoke output, never assertions.
    FRESH-INSTALL MANIFEST/ON-DISK PARITY, derived from a real throwaway git install (not asserted):
    `on-disk skill files = 90 (was 135 with the script)`, `manifest skill rows = 90`,
    `PARITY on_disk == rows = True (90 == 90)`, `SKILL.md routers = 45`,
    `canonical-body pointers = 45`, `files under any scripts/ = 0`, `verify_digest.py present = 0`,
    and the arithmetic checks out: `2 files x 45 packages = 90`.
    FULL SUITE, `make test-all` (NOT a bare `python3 -m pytest`, which per F-12 deselects all 10 install
    tests - independently re-confirmed this turn:
    `python3 -m pytest tests/test_installer_skill_emission.py --collect-only` ->
    `no tests collected (10 deselected) in 0.25s`). Both runs at
    `git rev-parse HEAD` = `8b4e15702830dd713bff56bc49fb23642cc06ee3`, the change carried in the working
    tree, so the comparison isolates this change:
    PRE-CHANGE BASELINE (my own measurement, not an inherited number), at HEAD
    `8b4e15702830dd713bff56bc49fb23642cc06ee3`:
    `38 failed, 6078 passed, 3 skipped, 2 xfailed in 262.42s (0:04:22)`
    POST-CHANGE, working tree, same HEAD:
    `38 failed, 6079 passed, 3 skipped, 2 xfailed in 368.26s (0:06:08)`
    FINAL RUN at the committed end state, HEAD `a69bb1fe58fc71d68130d497b65c7ba8855980c4` (both commits
    in, including the engine.py prose fix) - this is the authoritative measurement:
    `38 failed, 6079 passed, 3 skipped, 2 xfailed in 245.82s (0:04:05)`
    The sorted FAILED sets were DIFFED, not merely counted:
    `diff tmp/baseline-failed.txt tmp/final-failed.txt` -> empty,
    `(IDENTICAL: the same 38 pre-existing failures, none caused or fixed)`, 38 names on both sides.
    HONEST NOTE ON AN INTERMEDIATE RED RUN: a run taken between those two showed
    `40 failed, 6077 passed` with two EXTRA failures,
    `tests/test_release_readiness.py::FullReportTests::test_build_report_go_on_clean_tree` and
    `::IpdLintGateTests::test_ipd_lint_all_phases_run_and_pass`. Both were SELF-INFLICTED by me and are
    recorded rather than hidden: I had written `- Result: verified` into this plan's V-items, which is
    not in the lint's result vocabulary, so `aw ipd lint` exited 1 (`IPD-S402 unknown validation result
    'verified'`, `IPD-S404 not 'pass' at pre-transition`) and the repo-wide readiness gate that shells
    out to it went red. Corrected to the canonical `- Result: pass`; lint then reported `conforming` and
    `python3 -m pytest tests/test_release_readiness.py -m ''` -> `20 passed`. The final run above
    confirms both are green again. Passes rose by
    exactly 1 (net effect of deleting 1 test and adding 2). The 38 are PRE-EXISTING and unrelated
    (`test_run_viewer` x15, `test_agy_runipd_cli`, `test_cli_conformance_matrix`,
    `test_command_surface_declarations`, `test_installer::UninstallCompletenessTests`, and others), all
    red at the baseline before I touched anything. Targeted confirmation of the files this E-item
    changed: `python3 -m pytest tests/test_host_adapters_skills.py tests/test_installer_skill_emission.py -m ''`
    -> `43 passed in 11.07s` (was 42 before: -1 deleted, +2 added).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste, from a REAL throwaway install-then-upgrade (not from reasoning), all three measurements. (a) The post-upgrade counts showing on-disk skill files versus manifest skill entries disagree (expected 90 versus 135) and `plan_uninstall` classifying exactly 45 as `missing`; then state that this phantom is handled by `uninstall_repo`'s already-absent branch and is accepted, not fixed here. (b) The staged-file abort reproduced: the `git rm ... failed: error: the following file has changes staged in the index` message and the resulting `SystemExit`, plus the one-line precondition a maintainer must satisfy before the first upgrade. (c) The empty-`scripts/`-dir count on a non-git target (expected 45) contrasted with a git target (expected 0). Each classified explicitly as accepted-and-documented.
  - Observed evidence: ALL THREE MEASURED ON REAL THROWAWAY INSTALL-THEN-UPGRADE RUNS, never reasoned
    about. Method, stated because it is what makes these upgrades genuine: each scratch target was
    installed FIRST with the OLD generator (restored via `git show HEAD:agent_workflows/host_adapters.py`
    into place for that install only, then reverted), committed, then upgraded with the NEW generator.
    (a) THE MANIFEST KEEPS 45 STALE ROWS.
    `AFTER OLD INSTALL: on-disk skill files = 135 | manifest skill rows = 135`, `verify_digest.py on disk = 45`.
    `AFTER UPGRADE: on-disk skill files = 90 | manifest skill rows = 135`,
    `pruned skill entries reported = 45`, `verify_digest.py ON DISK = 0`,
    `verify_digest.py rows STILL IN MANIFEST = 45`, `DISK vs MANIFEST DISAGREE: 90 != 135 -> True`.
    `plan_uninstall: missing total = 45 | of which verify_digest.py = 45`, sample missing row
    `.agents/skills/advise-architect/scripts/verify_digest.py`. The phantom is HANDLED by
    `uninstall_repo`'s already-absent branch:
    `uninstall_repo actions containing 'already absent (manifest entry stale)': 45`, of which
    `verify_digest.py: 45`, sample
    `.agents/skills/advise-architect/scripts/verify_digest.py already absent (manifest entry stale)`.
    CORRECTION TO THE PLAN'S OWN WORDING, recorded so a later reader is not misled: F-10a and E-05a say
    `uninstall_repo` PRINTS this line. It does not print it; it APPENDS it to the returned `actions`
    list (`engine.py:4122`). My first measurement scanned stdout and found 0, which looked like a
    refuted finding; scanning the return value found exactly 45. The finding is CORRECT, its stated
    mechanism was not. ACCEPTED AND DOCUMENTED, NOT FIXED HERE: `manifest.py` has no row-deletion API
    and adding one is a much larger blast radius, so the fresh-install equality invariant simply does
    NOT hold on an upgraded repo, and V-04's 90 == 90 must not be read as if it did.
    (b) THE STAGED-FILE ABORT, REPRODUCED. With the 45 files staged-but-uncommitted
    (`PRECONDITION: staged-but-uncommitted verify_digest.py files: 45`, sample porcelain line
    `A  .agents/skills/advise-architect/scripts/verify_digest.py`), the upgrade died partway:
    ```
    *** SystemExit RAISED: 'git rm --quiet -- .agents/skills/advise-architect/scripts/verify_digest.py failed:\nerror: the following file has changes staged in the index:\n    .agents/skills/advise-architect/scripts/verify_digest.py\n(use --cached to keep the file, or -f to force removal)'
    ```
    PRECONDITION FOR A MAINTAINER, one line: commit (or unstage) the `.agents/skills/` tree before the
    first upgrade past this change, or the install will abort partway on the first pruned file.
    ACCEPTED AND DOCUMENTED, NOT FIXED HERE: `git_run` escalating any nonzero git exit to `SystemExit`
    is the installer's error-handling contract and is explicitly out of this plan's fence.
    (c) EMPTY `scripts/` DIRS, both target kinds contrasted:
    `NON-GIT target: skill files 135 -> 90 | EMPTY scripts/ dirs remaining = 45` (sample
    `.agents/skills/advise-architect/scripts`) versus
    `GIT target: skill files 135 -> 90 | EMPTY scripts/ dirs remaining = 0`. Cause as F-10c states:
    with git, `git rm` removes the now-empty parent as a side effect; without git, `destination.unlink()`
    leaves the directory, since only `run_deep_cleanup` prunes empty dirs. ACCEPTED AND DOCUMENTED, NOT
    FIXED HERE: cosmetic, and adding dir-pruning to `prune_stale` is outside the fence.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `docs/skill-selection.md` diff showing the `verify_digest.py` bullet gone and the remaining contract accurate. Paste `python3 -m pytest tests/test_docs.py` passing. Paste `grep -rn verify_digest docs/ README.md ARCHITECTURE.md agent_workflows/` showing what remains and why each remaining mention is correct (or that none remain). State the engine docstring/comment decision explicitly, and record the spec as N/A by quoting the measurement that it never enumerated the three files. Finally `aw check all` NO-WORSENING against your own fresh baseline (do NOT claim it passes: it reports 15 findings at HEAD `484994ec`, none in this plan's paths).
  - Observed evidence: `docs/skill-selection.md` DIFF (the false bullet gone, the remaining contract
    accurate):
    ```
    -- `scripts/verify_digest.py`: a deterministic script that recomputes the parity digest.
    ++
    ++That is the whole package: two files. It carries no per-package verification script. Integrity of
    ++the installed files is tracked by the install manifest, which records a `sha256` per emitted file;
    ++that is a stronger signal than one an artifact reports about itself. The router's `semantic-digest`
    ++frontmatter key remains the portable parity signal a host can read.
    ```
    (The bullet was doubly wrong: it described a script that "recomputes" a digest, which was false even
    BEFORE this change per F-2, since the script only compared `argv[1]` to a constant.)
    `python3 -m pytest tests/test_docs.py` -> `14 passed in 4.09s`. Re-run together with the two skill
    test modules after the engine.py edit -> `57 passed in 9.61s`.
    `grep -rn verify_digest docs/ README.md ARCHITECTURE.md agent_workflows/` -> ONE remaining mention,
    `agent_workflows/host_adapters.py:370`, inside the new `build_skill_package` docstring paragraph
    that EXPLAINS the removal ("The former ``scripts/verify_digest.py`` computed nothing..."). That
    mention is correct and deliberate: it names the deleted artifact in the past tense so a future
    reader learns why no script is emitted rather than re-adding one. No other file mentions it.
    ENGINE DOCSTRING/COMMENT DECISION, STATED EXPLICITLY - and NOT the N/A the plan predicted. The
    review characterized `agent_workflows/engine.py:18,21,2230` as "module docstring and comment prose,
    not a contract"; READ DIRECTLY, TWO OF THE THREE WERE AFFIRMATIVE FALSE CLAIMS after this change.
    `:18` said `generated Agent Skill packages (+ reference/, scripts/)` and `:21` said "a SKILL.md
    router plus reference/ and scripts/ resources"; both now say reference/ only. This required an edit
    OUTSIDE the declared Scope-Paths, declared and justified rather than slipped in (decision
    07-8fhjjc-D5 in the run register; `--scope-reason` supplied to `aw ipd finalize`), on the same
    ground E-06 uses for the doc: shipping a package whose own docstring contradicts its code in the
    same commit is not a defensible narrower scope. THE PRUNE-SCAN COMMENT WAS DELIBERATELY NOT
    NARROWED, which is what E-06 warns against: it was EXPANDED to state the scan must stay
    shape-agnostic and keep recursing because an upgraded repo still carries a legacy
    `<name>/scripts/verify_digest.py` that prune is responsible for removing - the exact behavior
    V-05(a) measures. No executable statement in `engine.py` was touched.
    SPEC RECORDED N/A BY MEASUREMENT, not assumption:
    `grep -n "verify_digest\|scripts/" .aw/records/specs/20260725-0957-01-external-delivery-and-skills.spec.md`
    returns nothing - the spec never enumerates the three package files (it discusses `SKILL.md`
    discovery tiers and the probe protocol) and is itself `deferred`. NOT EDITED, as instructed.
    Also confirmed clean, per the plan's spec/doc-sync list: `README.md`, `ARCHITECTURE.md`,
    `CHANGELOG.md`, and every other file under `docs/` contain no `verify_digest` mention (the grep
    above covers them).
    `aw check all` NO-WORSENING AGAINST MY OWN FRESH BASELINE - and NOT claimed to pass (it does not;
    exit 1 both times). The plan's orientation figure of 15 findings at HEAD `484994ec` is STALE by an
    order of magnitude and was correctly re-measured rather than trusted. Measured by stashing exactly
    my four files and restoring them, three runs each to rule out nondeterminism:
    WITHOUT my change -> `140 finding(s) detected across 624 all`, `140`, `140`.
    WITH my change    -> `168 finding(s) detected across 624 all`, `168`, `168`.
    THE +28 IS DETERMINISTIC AND FULLY ATTRIBUTED, NOT WAVED THROUGH. The category diff shows the ONLY
    changed rule is `check.scope-drift` (6 -> 7 groups). Enumerated programmatically via
    `check_engine.check_scope_drift(Path('.'))`: 120 findings total, of which exactly 28 name one of my
    four files, spread over exactly 7 OTHER plans at 4 apiece (`nna8yz`, `xdr83v`, `kgpptv`, `tm2cz8`,
    `4r0qp1`, `29wvmj`, `03ie04`) - i.e. 7 co-workers' LIVE begin receipts x my 4 in-flight files. ZERO
    are attributed to this plan (`any attributed to MY OWN plan 8fhjjc? False`). This is the known
    ownership-blindness of a shared checkout: `check_scope_drift` compares each live receipt's frozen
    base against the WHOLE working tree, so any uncommitted file is charged to every concurrently
    executing plan. It is not a defect this plan introduces and it resolves for those plans as their own
    work commits. No new finding in this plan's Scope-Paths, and no rule count decreased.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 6 E-leaves across 2 task groups, one concern: remove a generated artifact whose only caller is a test of itself, without losing verification and without shipping documentation that contradicts the code. Task group 1 is entirely evidence and decision, which is deliberate: the plan's origin conversation contained a FALSE equivalence claim AND the plan's own first draft contained a false "zero callers" claim, so establishing real coverage is a distinct deliverable from acting on it. Task group 2 splits by independent test-surface, not by file: E-03 is the generator (verified by `validate_skill_package` on an in-memory package), E-04 is the test suite (verified by `make test-all`), E-05 is the upgrade path (verified only by real throwaway install-then-upgrade runs, a surface E-04 cannot reach because the suite tests fresh installs), and E-06 is documentation (verified by `tests/test_docs.py` plus a grep). Each is one focused pass with its own evidence kind; merging E-05 into E-04 in particular would hide three measured upgrade behaviors behind a green fresh-install suite.

Open questions: NONE OUTSTANDING. OQ-01 (wait for `sx0cqv` or proceed) was RESOLVED by maintainer decision on 2026-09-06: PROCEED, with no typed dependency on that research. E-02 must RECORD that ruling rather than re-decide it.

This plan is `reviewed` and requires explicit human approval before execution. It has no plan dependencies and is deliberately NOT dependent on research `sx0cqv`, which the maintainer has now confirmed as the chosen sequencing rather than merely the plan's default.

Scope fence: touch ONLY `agent_workflows/host_adapters.py`, `tests/test_installer_skill_emission.py`, `tests/test_host_adapters_skills.py`, and `docs/skill-selection.md`. Do NOT remove the `semantic-digest` frontmatter key. Do NOT touch `compute_workflow_semantic_digest` or `workflow_profile.semantic_digest`. Do NOT delete the `extra_resources` parameter (F-13: it is the seam that keeps reversal cheap). Do NOT add manifest-row deletion or empty-dir pruning to the installer, and do NOT change `git_run`'s error handling, however tempting given F-10; measure those and move on. Do NOT change the `.agents/skills` path (research `sx0cqv`). Do NOT change SKILL.md structure, wording, or trigger descriptions (research `ti73qs`). Do NOT widen `aw workflow check-generated` to cover skill packages, however tempting given F-5. Do NOT weaken the pointer discipline or `validate_skill_package`'s no-inlining rule. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. Four specific false claims are FORBIDDEN, each because it was already made once and was wrong. (1) Do NOT claim `aw workflow check-generated` covers skill packages: it does not (F-5). (2) Do NOT claim the script has ZERO callers: it has one, `tests/test_host_adapters_skills.py:140`, which executes it (F-3). The correct claim is that its only caller is a test of the artifact itself. (3) Do NOT describe the end state as "the manifest already covers it" flatly: F-9 measured that drift is detected at uninstall and on re-install but is NOT surfaced at upgrade time, and there is no verify-installed-tree verb. (4) Do NOT offer a green bare `python3 -m pytest` as evidence for this change: F-12 measured that it deselects all 10 install tests, so it is silent on exactly the behavior at issue. Also do NOT report the external-caller question as settled by this repository (F-7), and do NOT report the fresh-install manifest equality as if it held on an upgrade (F-10).

Execution contract: RE-READ `host_adapters.py` and locate `build_skill_package`, its resource list, `_render_skill_main_file`, `_render_digest_verify_script`, and `validate_skill_package` BY SYMBOL before editing, never by the line numbers in this plan. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
