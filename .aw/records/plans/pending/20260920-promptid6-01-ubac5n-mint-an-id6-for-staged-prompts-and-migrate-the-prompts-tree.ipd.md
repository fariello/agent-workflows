# IPD: Mint an id6 for staged prompts and migrate the prompts tree to the uniform clustered grammar

- Date: 2026-09-20
- Kind: child
- Concern: A STAGED PROMPT CANNOT BE CITED, because `aw prompts new` emits a name carrying no id6. `AGENTS.md` states ONE uniform artifact-naming grammar, `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`, and every tracked type has adopted it except four; prompts is one of the four. Measured 2026-09-20: 17 prompts across `pending/`, `executed/` and `superseded/`, and NOT ONE carries an id6 (`ls .aw/records/prompts/*/*.md | grep -cE '[0-9]{8}-[a-z0-9]+-[0-9]{2}-[0-9a-z]{6}-'` returns 0 once two loose-regex false positives are excluded, both of which are legacy `YYYYMMDD-HHMM-NN` names). The consequence is not cosmetic: every `aw` verb resolves an artifact BY id6, so a prompt is invisible to `aw find`, cannot be named in a `consumed-by` or `From-*` field, and cannot be paired with the research report it produced except by prose. That pairing is the normal lifecycle of a research prompt (research sets put the originating prompt at `NN=00` and cite it by id6), so the one artifact type that most needs a citable handle is the one type that has none.
- Scope: Mint an id6 in `aw prompts new`, emit the uniform clustered name, add a dated cutover so every existing prompt stays valid, and ship an on-demand converter for a legacy name. Follows the SPEC PRECEDENT exactly (IPD `ha55fi`), which migrated specs out of the same id6-less set. Includes the two documentation surfaces that would otherwise contradict the code (`.aw/records/prompts/README.md`, `agent_workflows/artifact_naming.py`'s scope docstring) and the naming spec section that enumerates the vocabulary. EXCLUDES a mass rename of the 17 existing prompts (the cutover grandfathers them, exactly as `ha55fi` left 24 legacy specs in place), EXCLUDES roadmaps/releases/walkthroughs (the other three id6-less types, each its own migration), and EXCLUDES any change to the prompt-purity contract (the single leading HTML comment and the no-body-boilerplate rule are owned by approved spec `20260808-1958-01-prompt-purity-lint` and are untouched here).
- Scope-Paths: agent_workflows/prompts.py, agent_workflows/artifact_naming.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/artifact_rename.py, .aw/config/project.json, .aw/records/prompts/README.md, .aw/records/prompts/pending/README.md, .aw/system/workflows/research-prompt/research-prompt.md, .aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md, tests/test_prompts_new.py, tests/test_naming_authority_single_source.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: promptid6
- Order: 1
- Highest E allocated: 06
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: ubac5n

## Workflow history
- 2026-09-21 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review at HEAD cd2e6adb in an isolated lane; APPROVE WITH REVISIONS APPLIED, readiness go-pending-approval; PR-201..PR-210 all FIXED in place, none deferred, none OPEN, none REPLAN. aw ipd lint CONFORMING at author and review-finalize. THE PLAN'S GOAL AND ITS MAINTAINER MANDATE ARE SOUND and its core premise verifies: 17 prompt files exist, none carries an id6, build_clustered_name already knows the 'prompt' facet, and mint_id6 is the one mint seam. BUT FOUR OF ITS SIX E-ITEMS RESTED ON MEASUREMENTS THAT NO LONGER HOLD, and two of those would have produced a WRONG IMPLEMENTATION rather than a failed one. PR-201 (BLOCKER): E-04's deliverable ALREADY EXISTS AND ALREADY CORRUPTS A PROMPT. --to-id6 is a GENERIC rename flag (cli.py:3708), so 'aw rename prompts <legacy> --to-id6' runs today; I ran it in preview against the real tree and it printed a correct rename PLUS 'would inject - Id: gym3i0' PLUS a citation rewrite. The injector (artifact_rename.py:214,241-260) anchors the bullet after the first '# ' heading when no Status/Date bullet exists, which is EVERY prompt, so the id6 lands as VISIBLE TEXT inside the pasteable prompt body, violating approved spec prompt-purity-lint R1/P4. Proven by simulating the insertion: '- Id: gym3i0' becomes line 3, directly under the H1. Nothing catches it because 'aw prompts check' IS NOT IMPLEMENTED (exits 2, 'invalid choice'). E-04 rescoped from BUILD to REPAIR, with an explicit instruction not to change specs' behavior in the shared code path. PR-202 (HIGH): E-03 would have MIRRORED A DEPRECATED MECHANISM. SPEC_ID6_CUTOVER_DATE is now only a fallback; _spec_requires_id6 (check_engine.py:744) resolves via config.resolve_cutover_date FIRST and its docstring calls the constant deprecated, and the config path is LIVE here, so the EFFECTIVE spec cutover is 20260829 from project.json and NOT the 20260828 constant the plan proposed to copy. E-03 now builds the config-driven twin, writes cutovers.prompt_id6, declares project.json, and answers the CARRIER_CUTOVER_DATE counter-precedent explicitly. PR-203 (HIGH): OQ-02's STATED EVIDENCE WAS FALSE IN BOTH HALVES. It claimed the newest legacy tracked prompt date is 20260920 and that a 20260920 legacy name remains in pending/; measured, the newest legacy name is 20260829-1520-01-session-allocation-policy and the only 20260920 prompt is the CONFORMING one, while the untracked/ lane it cited DOES NOT EXIST in a lane worktree and no 20260920-12* file exists anywhere. The 20260921 answer survives on rewritten reasoning (a cutover at or below 20260920 would make the hand-made file's conformance load-bearing); the false argument is removed with a warning not to restore it. PR-204 (HIGH): FIVE surfaces assert the legacy grammar, not three, and the two found at review were missing from Scope-Paths, including the research-prompt WORKFLOW file that an agent reads while producing a prompt. PR-205 (HIGH): BOTH declared test files DO NOT EXIST, and the real tests PIN THE LEGACY BEHAVIOR, so two of them fail BY DESIGN once E-01 lands and must be updated rather than treated as regressions. ALSO FIXED: V-03's grandfathering evidence was UNOBTAINABLE as written because a default 'aw check prompts' examines 2 of 17 files (is_retired excludes executed/ and superseded/), so it now demands the retired-inclusive call with a pasted file count plus the resolved cutover value; V-05's grep was too narrow to see three of the five surfaces and now greps the grammar instead of two phrasings; the pre-authorized test failure DOES NOT EXIST (test_standalone_verify.py reports 28 passed), replaced with the measured lane baseline; three facts about the naming spec now constrain the amendment (Status: implemented which an agent may not SET though the body may be amended, no - Id: so it must be cited by path, and an established dated-AMENDED convention to follow); and the gate gained the shared-checkout staging rule, a declaration-style scope fence naming the widened paths, and conditional runner-versus-executor finalize ownership. Ten decisions recorded as D-1..D-10 in the review record, none irreversible. E-count 6 to 6; no E-item added or removed; no product code, config, or spec touched by this review.

- 2026-09-20 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): Authored at the maintainer's explicit direction after `aw prompts new` produced a non-conforming name for a real prompt they had asked to be staged. THE MAINTAINER'S RULING, verbatim: "I want it to look like all the other files. YYYYMMDD-<setid>-<num>-<id6>-<slug>.<type>.md. plainlang = <setid> for THIS artifact. prompt = <type>." They chose "fix the tool first, then restage" from four options when asked, so this plan exists rather than a hand-rename alone. RECORDED HONESTLY: this plan REVERSES a resolved decision (`jxqdcw` OQ-02), and that reversal is the maintainer's to make and is made. Also recorded: one file was hand-renamed to the target grammar in the same session so the prompt the maintainer is about to use is correct; see E-06 and the Findings table.
- 2026-09-20 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a staged prompt a citable artifact by giving it an id6 in its filename, using the uniform
clustered grammar every other tracked type already uses, without invalidating a single existing
prompt.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: mint and emit the conforming name

- [ ] E-01 Resolve F-7 and F-8 in code: give `aw prompts new` a `--set` input and decide `NN`'s meaning, then mint an id6 through `artifact_core.mint_id6` and assemble the name with `artifact_naming.build_clustered_name(..., artifact_type="prompt")`. Default the set id from the slug when `--set` is omitted (a singleton set of one, which is how research treats a lone doc) so the verb stays usable without a new required flag.
  - Depends on: none
  - Expected outcome: `aw prompts new --kind research --slug foo` writes `YYYYMMDD-foo-01-<id6>-foo.prompt.md` into `pending/`, and `--set bar` puts `bar` in the set position. The id6 is repository-unique.
  - Execution state: pending
- [ ] E-02 Record the id6 in the existing single metadata comment so the handle is readable from inside the file, NOT only from its name. Add it as one more `Key: value` pair in the same `<!-- aw-prompt: ... -->` line. Do NOT add YAML front matter and do NOT add a second comment line; both are refused by approved spec `20260808-1958-01-prompt-purity-lint` (P4/P5, R1).
  - Depends on: E-01
  - Expected outcome: a minted prompt's first line carries `Id: <id6>` inside the one existing HTML comment; the file still has exactly one leading comment line and no body boilerplate.
  - Execution state: pending

### Task group 2: grandfather every existing prompt

- [ ] E-03 Add the prompt cutover, FOLLOWING THE SHIPPED CONFIG-DRIVEN MECHANISM RATHER THAN THE BARE CONSTANT. Enforce the clustered grammar for a prompt whose filename date is at or after the cutover, and leave a pre-cutover name conforming.
  THE PLAN ORIGINALLY SAID "add a dated cutover constant beside `SPEC_ID6_CUTOVER_DATE`", AND THAT MIRRORS A SUPERSEDED SHAPE (F-11). MEASURED AT REVIEW: `SPEC_ID6_CUTOVER_DATE` is now only a FALLBACK. The live resolver is `check_engine._spec_requires_id6(filename, repo_root)` (`check_engine.py:744`), which calls `config.resolve_cutover_date(repo_root, "spec_id6", compact=True)` FIRST and falls back to the constant only when that returns `None`; the constant's own docstring calls itself "the deprecated SPEC_ID6_CUTOVER_DATE constant". AND THE CONFIG PATH IS LIVE IN THIS REPOSITORY, which is what makes copying the constant actively wrong: `.aw/config/project.json` carries `cutovers.spec_id6 = "2026-08-29"`, so the EFFECTIVE spec cutover is `20260829`, NOT the `20260828` in the constant this plan proposed to copy. An executor who hard-codes a prompt constant would ship a boundary the maintainer cannot move without editing Python, in a repo that already moved that capability into config.
  SO BUILD IT THIS WAY: add `cutovers.prompt_id6 = "2026-09-21"` to `.aw/config/project.json`, and write `_prompt_requires_id6(filename, repo_root)` as the exact structural twin of `_spec_requires_id6` (resolve via config, fall back to a module constant, treat an unparseable leading date as pre-cutover). `config.resolve_cutover_date` needs NO change: verified at review that it already resolves an arbitrary feature key (`resolve_cutover_date(Path('.'), 'prompt_id6')` returns `None` today, which is the correct fail-open for an unconfigured feature). NOTE `.aw/config/project.json` IS NOT in `Scope-Paths` and MUST be added before this item is executed, or finalize will demand a `--scope-reason` for it.
  ALSO CONSIDER, AND RECORD, THE CARRIER_CUTOVER_DATE COUNTER-PRECEDENT rather than ignoring it: `check_engine.CARRIER_CUTOVER_DATE` (`:4687`) deliberately chose a bare constant over config, and its comment states why ("measured `None` in this repository, and an absent marker grandfathers EVERYTHING, which would leave the `error` tier unreachable"). That reasoning applies to a NEW feature key, so state explicitly which failure mode you chose: config-first risks an unconfigured `None` grandfathering every prompt, while constant-only risks an immovable boundary. The recommended resolution is config-first WITH a non-`None` module fallback, which is exactly what `_spec_requires_id6` does and which has neither failure mode.
  - Depends on: E-01
  - Expected outcome: a prompt dated on/after the cutover MUST be id6-clustered and one dated before it stays valid in either shape; the boundary is resolved through `config.resolve_cutover_date(repo_root, "prompt_id6")` with a module-constant fallback, mirroring `_spec_requires_id6` rather than the deprecated bare constant; `cutovers.prompt_id6` is written to `.aw/config/project.json`.
  - Execution state: pending
- [ ] E-04 FIX `aw rename prompts <legacy> --to-id6`, WHICH ALREADY EXISTS AND ALREADY CORRUPTS A PROMPT. Do NOT "ship" it as new work; the item was rescoped at review from BUILD to REPAIR (F-12), which changes what must be done and makes this the highest-risk item in the plan.
  MEASURED AT REVIEW, RUN AGAINST THE REAL TREE IN PREVIEW MODE: `aw rename prompts 20260829-1520-01-session-allocation-policy.prompt.md --to-id6` exits 0 and prints a complete, correct-looking plan: `would rename ... -> 20260829-gym3i0-01-gym3i0-session-allocation-policy.prompt.md`, `would inject '- Id: gym3i0'`, and `would rewrite 1x` the citation in plan `jxqdcw`. `--to-id6` is a GENERIC flag on the shared rename verb (`cli.py:3708`), not a per-type one, so prompts inherited it the day specs got it.
  THE DEFECT IS THE INJECTION, AND IT BREAKS AN APPROVED CONTRACT. `artifact_rename._update_frontmatter_metadata` (`:214`) inserts a `- Id: <id6>` BULLET, anchored after `- Status:`, else after `- Date:`, else AFTER THE FIRST `# ` HEADING (`:241-260`). A prompt has NEITHER bullet, so the third anchor fires. PROVEN by simulating the insertion on the real file: the `- Id:` line lands as line 3, immediately under the H1, i.e. as VISIBLE TEXT INSIDE THE PROMPT BODY a human pastes into a chat. That is a direct violation of approved spec `20260808-1958-01-prompt-purity-lint` R1 ("any OTHER content before the prompt body ... is a violation") and of P4's rule that the ONE HTML comment is the only permitted non-prompt content. Note nothing catches it today: `aw prompts check` IS NOT IMPLEMENTED (`aw prompts check` exits 2, "invalid choice: 'check' (choose from 'new')"), so the purity lint the spec specifies does not exist and cannot fail this.
  SO THE WORK IS: make the prompts path write the id6 into the EXISTING `<!-- aw-prompt: ... -->` comment (the same writer E-02 builds) instead of injecting a bullet, and keep `git mv` plus reference rewriting as they are. PREFER REUSING E-02's WRITER over adding a second metadata path, so the verb and the minter cannot disagree about where a prompt's id6 lives.
  DO NOT WIDEN THIS INTO THE OTHER TYPES. The bullet injection is CORRECT for a plan or a spec, which do carry front-matter bullets; only prompts forbid it. A change to the shared `_update_frontmatter_metadata` must therefore be conditioned on the artifact type, and `git diff` must show no behavior change for specs (the `ha55fi` path this borrows from).
  ALSO NOTE THE REFERENCE REWRITE IS REAL AND IS DESIRABLE: the preview showed it would update the citation inside executed plan `jxqdcw`. That is an edit to a file in `executed/`, which the repository forbids ADDING COMMITS TO as a plan but which reference-rewriting legitimately touches; if you convert a cited prompt, say so explicitly in the evidence rather than letting a surprise edit appear in the diff.
  - Depends on: E-01, E-02
  - Expected outcome: `aw rename prompts <legacy> --to-id6` converts a legacy prompt whose id6 lands ONLY in the filename and the single HTML comment, with NO `- Id:` bullet and no new pre-body line; specs' behavior is byte-unchanged; preview-then-apply both demonstrated on a fixture.
  - Execution state: pending

### Task group 3: close the documentation contradictions

- [ ] E-05 Correct EVERY place that currently asserts the id6-less choice, in ONE pass so no surface contradicts the code. THE PLAN NAMED THREE; THERE ARE FIVE, AND TWO WERE MISSING FROM BOTH THE ITEM AND `Scope-Paths` (F-13).
  THE THREE ALREADY NAMED: `prompts.py`'s module docstring (F-4, `prompts.py:8-11`), `artifact_naming.py`'s id6-less enumeration (F-5, now at `artifact_naming.py:38-43`, written in the same shape as the specs carve-out at `:45-50`), and `.aw/records/prompts/README.md:3-4` (which `jxqdcw` had corrected TOWARD the legacy form, so this reverses that edit).
  THE TWO FOUND AT REVIEW, both measured: `.aw/records/prompts/pending/README.md:5` ("Named `YYYYMMDD-HHMM-NN-<slug>.md`", note it also carries the WRONG facet, a bare `.md`), and `.aw/system/workflows/research-prompt/research-prompt.md:9` ("The verb derives the filename (`YYYYMMDD-HHMM-NN-<slug>.prompt.md`); never hand-name it"). The workflow file is the one that MATTERS MOST OPERATIONALLY, because it is what an agent reads while producing a research prompt, so leaving it stale means the next research handoff is authored against the old grammar even after the code changes. BOTH MUST BE ADDED TO `Scope-Paths` before execution.
  ALSO CHECK, AND DECIDE DELIBERATELY: `.aw/system/workflows/templates/prompts-README.md:4` and `.aw/system/workflows/templates/agents-docs-README.md:13` carry the same legacy sentence but are TEMPLATES INSTALLED INTO TARGET REPOS. Changing them changes what every managed repo is told. State explicitly whether they are in or out; if OUT, say why (a target repo's own prompts tree has no cutover and no minted id6s until it installs this version), and record that the templates will then disagree with this repo's README until a later change reconciles them.
  Amend naming spec section 5.4 with a dated entry recording the reversal and its reason (F-6).
  - Depends on: E-01, E-03
  - Expected outcome: no shipped docstring, README, workflow, or spec states that prompts carry no id6; the two newly found surfaces are corrected and were declared; the template question is answered in writing either way; the spec amendment names `jxqdcw` OQ-02 as the decision being reversed and the maintainer's instruction as the authority.
  - Execution state: pending
- [ ] E-06 Reconcile the one hand-made file (F-9): confirm `20260920-plainlang-01-ng0ga4-plain-language-reporting-instructions.prompt.md` parses under the new grammar, that its `ng0ga4` is still repository-unique, and that its in-file metadata matches what E-02 now emits. If the cutover date chosen in E-03 falls on or before 20260920, this file is post-cutover and MUST conform; verify it does rather than assuming.
  MEASURED AT REVIEW SO THE RECONCILIATION STARTS FROM FACT: the file is TRACKED, was ADDED rather than renamed (commit `bfa8cf50`, so there is no legacy predecessor to clean up), its first line already carries `Id: ng0ga4` INSIDE the single `<!-- aw-prompt: ... -->` comment (which is the placement E-02 must match, so E-02 should be written to reproduce THIS shape), and `ng0ga4` appears in exactly two files (itself and this plan), so it is unique. Note "hand-renamed" in F-9 is loose: it was hand-NAMED at creation.
  THE CUTOVER CHOSEN IN OQ-02 IS `20260921`, so this file is PRE-cutover by one day and its conformance is therefore not compelled by the checker. Say that plainly rather than implying the checker validates it, and make the field-by-field comparison against a freshly minted prompt the real evidence.
  - Depends on: E-02, E-03
  - Expected outcome: the hand-made name is indistinguishable from a verb-produced one, or the difference is named and fixed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE UNIFORM GRAMMAR IS `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`, stated in `AGENTS.md` and
  assembled by `artifact_naming.build_clustered_name` (`agent_workflows/artifact_naming.py:152`),
  which already accepts an `artifact_type` facet and already knows the `prompt` facet
  (`ARTIFACT_TYPE_FACETS` includes `"prompt"`; `TYPE_FACET` maps `"prompts": "prompt"` at
  `artifact_naming.py:94`). So the naming module can ALREADY produce the target name; nothing new is
  needed there beyond correcting its scope docstring.
- THE MINT SEAM IS `artifact_core.mint_id6(repo_root, existing=...)`
  (`agent_workflows/artifact_core.py:148`). It collision-checks REPOSITORY-WIDE and unions the
  caller's own set rather than replacing it. IPD `sk7ggr` E-01 established it as the one call site
  every mint uses, so this plan must call it and must not roll its own generator.
- THE CUTOVER MECHANISM IS CONFIG-DRIVEN NOW, AND THE CONSTANT IS A DEPRECATED FALLBACK.
  CORRECTED AT REVIEW (F-11): `check_engine.SPEC_ID6_CUTOVER_DATE` (`check_engine.py:40`) still exists,
  but `_spec_requires_id6` (`:744`) resolves through `config.resolve_cutover_date(repo_root,
  "spec_id6", compact=True)` FIRST and falls back to the constant only on `None`, and its docstring
  names the constant "deprecated". `.aw/config/project.json` carries `cutovers.spec_id6 = "2026-08-29"`
  here, so the EFFECTIVE spec boundary is `20260829`, not the constant's `20260828`. Mirror the
  RESOLVER, not the constant. The constant's claim that there was "NO pre-existing cutover mechanism
  to reuse" was true when written and is now stale.
- THERE IS A COUNTER-PRECEDENT AND IT MUST BE ANSWERED, NOT IGNORED: `CARRIER_CUTOVER_DATE`
  (`check_engine.py:4687`) deliberately chose a bare constant, because a config key measured `None`
  and "an absent marker grandfathers EVERYTHING", leaving the rule unreachable. Config-first WITH a
  non-`None` module fallback (what `_spec_requires_id6` does) avoids both failure modes.
- THE CONVERTER ALREADY EXISTS FOR PROMPTS AND IS BROKEN FOR THEM (F-12). `--to-id6` is a GENERIC flag
  on the shared rename verb (`cli.py:3708`), so `aw rename prompts <legacy> --to-id6` already runs. Its
  metadata writer injects a `- Id:` BULLET anchored after the first `# ` heading when no front-matter
  bullet exists, which for a prompt puts it inside the pasteable body and violates the purity spec. So
  the prompts work is a REPAIR of a shared code path, not a new verb beside the spec one.
- `aw prompts check` (the purity lint the approved spec specifies) IS NOT IMPLEMENTED: `aw prompts`
  accepts only `new`. So no mechanical gate protects prompt purity today, and any purity claim in this
  plan's evidence must be demonstrated by inspecting the file, never by citing a lint run.
- PROMPT LIFECYCLE IS A DIRECTORY, moved with `git mv` per `.aw/records/prompts/README.md`; this plan
  does not change that and adds no lifecycle verb.
- PROMPT PURITY IS A SEPARATE APPROVED CONTRACT (`20260808-1958-01-prompt-purity-lint`): exactly ONE
  leading `<!-- aw-prompt: ... -->` line, no YAML front matter, no body boilerplate. The id6 goes in
  the FILENAME and in that existing metadata comment; it must NOT become YAML front matter.

## Findings

| id | Finding | Evidence |
|---|---|---|
| F-1 | No prompt in the corpus carries an id6. 17 files: 2 `pending/`, 13 `executed/`, 2 `superseded/`, 0 `not-executed/`, 0 `reusable/`. | `ls .aw/records/prompts/<bucket>/*.md` per bucket, 2026-09-20 |
| F-2 | A naive id6-shaped grep reports 2 matches, and BOTH are false positives: `20260803-0829-01-revise-ipd-structure-set.prompt.md` and `20260810-0102-01-gemini-actually-validate-playbook.prompt.md`. The `-0829-01-` and `-0102-01-` runs satisfy a loose pattern; neither is an id6. A verification must not use a loose regex. | measured 2026-09-20 |
| F-3 | THE CURRENT BEHAVIOR IS DELIBERATE, NOT AN OVERSIGHT. `jxqdcw` OQ-02 resolved to emit the legacy form and CORRECTED THE README TO MATCH IT. Its stated reasons: every file in `executed/` used that shape, and `artifact_naming`'s docstring places prompts among the types it does NOT give an id6. This plan REVERSES that resolution on the maintainer's instruction; it must say so and must not present the current state as a bug nobody noticed. | `.aw/records/plans/executed/*jxqdcw*.ipd.md` OQ-02 + V-01 observed evidence |
| F-4 | `prompts.py`'s module docstring states the id6-less choice as a property with a citation (`"artifact_naming``'s own docstring places prompts among the types it does NOT give an id6, so the clustered id6 grammar is deliberately NOT used here (IPD jxqdcw OQ-02)"`). Leaving it would make the module contradict its own code. | `agent_workflows/prompts.py:8-12` |
| F-5 | `artifact_naming.py:38-42` enumerates the id6-less types as "prompts, roadmaps, releases, and walkthroughs" and says the module "does NOT add an id6 to those types (out of scope)". `:44-48` then carves specs OUT of that set with a pointer to `ha55fi`. The prompts carve-out must be written the same way, in the same place. | `agent_workflows/artifact_naming.py:36-48` |
| F-6 | The naming spec's own vocabulary section is the documentation authority for this grammar and carries an amendment log (two entries so far, 2026-09-08 and 2026-09-20). A third entry is required here, because the spec is what a reviewer checks a name against. | `.aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md` section 5.4 |
| F-7 | `NN` in the current prompts name is a PER-MINUTE SEQUENCE computed across the whole tree (`prompts.py:12-15`), which is a different quantity from `NN` in the clustered grammar (ORDER WITHIN A SET). The migration must decide which meaning `NN` carries after the change; they cannot both be true of one field. | `agent_workflows/prompts.py:12-15`; `artifact_naming.build_clustered_name(order=...)` |
| F-8 | `prompts.py` has no `--set` flag today; the tree has no concept of a prompt set. The clustered grammar REQUIRES a set id. So this is not purely a rename: the verb gains a required-or-defaulted input. | `aw prompts new --help`, 2026-09-20 |
| F-9 | One file was hand-renamed to the target grammar ahead of this plan, at the maintainer's instruction, so the prompt they are about to send is correctly named: `20260920-plainlang-01-ng0ga4-plain-language-reporting-instructions.prompt.md`. It is therefore the ONLY conforming prompt in the tree and will be a post-cutover name produced by hand rather than by the verb. E-06 reconciles it. RE-MEASURED AT REVIEW: it is TRACKED, was ADDED (not renamed) in commit `bfa8cf50`, already carries `Id: ng0ga4` inside its single `<!-- aw-prompt: ... -->` comment, and `ng0ga4` occurs in exactly two files (itself and this plan), so it is unique. | this session; `mint_id6` output `ng0ga4`; `git log --diff-filter=A` |
| F-10 | **OQ-02's STATED EVIDENCE WAS FALSE IN BOTH HALVES.** It claimed the newest legacy tracked prompt date is `20260920` and that a `20260920` legacy name remains in `pending/`. Measured: the newest legacy-named prompt is `20260829-1520-01-session-allocation-policy.prompt.md`, and the only `20260920` prompt is the CONFORMING one (F-9). The `untracked/` lane it cited as the second reason DOES NOT EXIST in a lane worktree and no `20260920-12*` file exists anywhere. The `20260921` conclusion survives on different reasoning; the argument was rewritten. | `ls .aw/records/prompts/*/*.prompt.md`; `ls .aw/records/prompts/untracked/` -> No such file or directory |
| F-11 | **E-03 WOULD HAVE MIRRORED A DEPRECATED MECHANISM.** `SPEC_ID6_CUTOVER_DATE` is now only a FALLBACK: `_spec_requires_id6` (`check_engine.py:744`) resolves via `config.resolve_cutover_date(repo_root, "spec_id6")` first and its own docstring calls the constant "deprecated". The config path is LIVE here, so the EFFECTIVE spec cutover is `20260829` (from `project.json`), not the `20260828` constant the plan proposed to copy. E-03 now builds the config-driven twin and declares `project.json`. | `check_engine.py:40,744-762`; `config.resolve_cutover_date`; `.aw/config/project.json` `cutovers` |
| F-12 | **E-04's DELIVERABLE ALREADY EXISTS AND ALREADY CORRUPTS A PROMPT.** `--to-id6` is a GENERIC rename flag (`cli.py:3708`), so `aw rename prompts <legacy> --to-id6` runs TODAY: it previews a correct rename plus `would inject '- Id: gym3i0'` plus a citation rewrite. But `_update_frontmatter_metadata` (`artifact_rename.py:214,241-260`) anchors the bullet after the first `# ` heading when no `- Status:`/`- Date:` bullet exists, which is every prompt, so the id6 lands as VISIBLE TEXT in the prompt body. That violates approved spec `prompt-purity-lint` R1/P4. Nothing catches it: `aw prompts check` IS NOT IMPLEMENTED. E-04 rescoped from BUILD to REPAIR. | live preview run; simulated insertion putting `- Id:` at line 3; `aw prompts check` -> "invalid choice" |
| F-13 | **FIVE SURFACES ASSERT THE LEGACY GRAMMAR, NOT THREE.** Beyond the three E-05 named: `.aw/records/prompts/pending/README.md:5` (also with a wrong bare `.md` facet) and `.aw/system/workflows/research-prompt/research-prompt.md:9`, the latter being what an agent reads while producing a research prompt. Two shipped TEMPLATES carry it too (`templates/prompts-README.md:4`, `templates/agents-docs-README.md:13`) and need an explicit in-or-out decision. Both new surfaces were missing from `Scope-Paths`. | `grep -rn "YYYYMMDD-HHMM-NN" --include=*.md --include=*.py .` |
| F-14 | THREE FACTS ABOUT THE NAMING SPEC THAT CONSTRAIN THE AMENDMENT: its `- Status:` is `implemented` (the one status an agent may not SET, though amending the body is permitted); it carries NO `- Id:`, so it is invisible to `discover_specs` and must be cited BY PATH; and it already uses a dated `AMENDED <date>` convention in 5.4 plus tool-attributed `## Workflow history` notes, which the amendment should follow via `aw specs note`. | spec `:4`, `:182`, `:248`; `discover_specs` does not return it; `aw find specs <stem>` does |
| F-15 | **THE PRE-AUTHORIZED TEST FAILURE DOES NOT EXIST.** The validation section claimed `tests/test_standalone_verify.py::TheAuditCannotTouchTheFinishedPlan` "has TWO failures that are PRE-EXISTING". Measured: that file reports `28 passed in 1.11s`. Pre-authorizing an absent failure licenses ignoring a real one. Replaced with the measured lane baseline (`1 failed, 7942 passed`, the failure being an ambient-environment case in `test_turn_bounds.py`). | `python3 -m pytest tests/test_standalone_verify.py`; bare suite |
| F-16 | **BOTH DECLARED TEST FILES DO NOT EXIST**, and the real ones PIN THE LEGACY BEHAVIOR. `tests/test_prompts.py` and `tests/test_artifact_naming.py` are absent; the actual files are `tests/test_prompts_new.py` and `tests/test_naming_authority_single_source.py`. Two existing tests will fail BY DESIGN once E-01 lands (one asserts the literal legacy filename, one asserts the per-minute `-01`/`-02` increment OQ-01 discards), so they must be UPDATED in the same change, not treated as regressions. | `ls tests/ | grep -iE "prompt|naming"`; `tests/test_prompts_new.py:83,183` |
| F-17 | `aw check prompts` EXAMINES ONLY 2 OF THE 17 PROMPTS by default, because `is_retired` excludes the `executed/`/`superseded/` path segments; `include_retired=True` yields 17. So V-03's "ZERO findings against the 17 grandfathered prompts" is UNOBTAINABLE from a default run and needs the retired-inclusive call. | `_iter_type_files(Path('.'),'prompts',include_retired=False)` -> 2 files; `True` -> 17 |

## Proposed changes (ordered, validatable)

1. `prompts.py`: add `--set`, mint via `artifact_core.mint_id6`, build the name via
   `artifact_naming.build_clustered_name(..., artifact_type="prompt")`, and add `Id:` to the metadata
   comment (E-01, E-02).
2. `check_engine.py` + `.aw/config/project.json`: add `_prompt_requires_id6` as the config-driven twin
   of `_spec_requires_id6`, and write `cutovers.prompt_id6 = "2026-09-21"` (E-03, revised at review:
   NOT a bare constant beside the deprecated one).
3. `artifact_rename.py`: REPAIR the existing `aw rename prompts --to-id6` so a prompt's id6 goes into
   the `<!-- aw-prompt: ... -->` comment instead of an injected `- Id:` bullet, leaving specs unchanged
   (E-04, rescoped at review from BUILD to REPAIR). `cli.py` needs no new flag; `--to-id6` already exists.
4. Docs and spec: `prompts.py` docstring, `artifact_naming.py` enumeration, BOTH prompts READMEs, the
   `research-prompt` workflow, and the naming spec 5.4 amendment (E-05).
5. Tests: UPDATE the legacy-pinning assertions in `tests/test_prompts_new.py` and extend
   `tests/test_naming_authority_single_source.py` (the two files the plan originally named do not exist).

## Deferred / out of scope (with reason)

- MASS-RENAMING THE 17 EXISTING PROMPTS. The cutover grandfathers them, which is precisely what
  `ha55fi` did for 24 legacy specs, and a bulk rename of tracked files with live citations is its own
  change with its own reference-updating risk. `--to-id6` (E-04) converts one on demand.
- ROADMAPS, RELEASES, WALKTHROUGHS. The other three id6-less types named at
  `artifact_naming.py:38`. Each needs the same treatment and each is a separate migration; doing four
  at once would make one review cover four vocabularies.
- ANY CHANGE TO PROMPT PURITY. The one-line HTML comment, the no-YAML rule and the no-boilerplate
  rule are an approved spec's contract. This plan writes one more key INTO the existing comment and
  changes nothing else about it.
- A PROMPT LIFECYCLE VERB. Movement stays `git mv` per the README.
- IMPLEMENTING `aw prompts check`, the purity lint approved spec `20260808-1958-01-prompt-purity-lint`
  specifies. Measured at review: the verb DOES NOT EXIST (`aw prompts` accepts only `new`), so the
  approved spec is unimplemented. This plan must not build it: it is a separate deliverable with its own
  spec, and folding it in would make one review cover both a naming migration and a new lint. The
  consequence to state honestly is that E-04's purity repair has NO mechanical guard, so its evidence
  must show the file contents rather than cite a lint.
- CONVERTING THE NAMING SPEC ITSELF TO AN id6 NAME. It carries no `- Id:` (F-14) and is therefore
  invisible to `discover_specs`, which is a real gap, but fixing it is `aw rename specs --to-id6` work on
  an artifact this plan only amends. Out of scope; cite it by path.
- CHANGING THE NAMING SPEC'S `- Status: implemented`. An agent may not set that status, and this plan
  amends the spec BODY only. Nothing here claims implementation.

## Scope check

- Over-scope: none. Every path in `Scope-Paths` is either the code that emits or validates the name,
  or a document that currently asserts the opposite of what this plan makes true.
- `Scope-Paths` WAS WIDENED AT REVIEW, and each addition is justified here rather than left to be
  discovered at finalize. `agent_workflows/artifact_rename.py`: E-04 is a REPAIR of the existing
  `--to-id6` path, which lives there, not in `cli.py` (F-12). `.aw/config/project.json`: E-03's cutover
  is config-resolved, so the value lands there (F-11). `.aw/records/prompts/pending/README.md` and
  `.aw/system/workflows/research-prompt/research-prompt.md`: two further surfaces asserting the legacy
  grammar that E-05 must correct (F-13). TWO DECLARED TEST PATHS WERE ALSO CORRECTED: `tests/test_prompts.py`
  and `tests/test_artifact_naming.py` DO NOT EXIST and were replaced with the real
  `tests/test_prompts_new.py` and `tests/test_naming_authority_single_source.py` (F-16); declaring a
  nonexistent path would have produced a declared-but-unmodified `--scope-ack` demand for a file that
  can never be modified.
- `agent_workflows/cli.py` STAYS DECLARED BUT MAY LEGITIMATELY GO UNTOUCHED, because `--to-id6` already
  exists and E-01's `--set` flag may be the only CLI change; if `cli.py` ends up unmodified, acknowledge
  it at finalize with `--scope-ack` rather than inventing an edit.
- Under-scope: the other three id6-less types, the 17 grandfathered names, `aw prompts check`, and the
  naming spec's own missing `- Id:`. Each is deliberate and recorded above with a reason.

## Required tests / validation

Bare `python3 -m pytest` (addopts already supplies `-q -n auto --dist=worksteal -m 'not slow'`), judged
on the failing NODE ID delta against a baseline measured in the executing worktree. AFTER minus BEFORE
must be EMPTY.

THE PRE-AUTHORIZED FAILURE THIS SECTION ORIGINALLY NAMED DOES NOT EXIST, AND THE CLAIM WAS REMOVED
(F-15). It asserted that `tests/test_standalone_verify.py::TheAuditCannotTouchTheFinishedPlan` "has TWO
failures that are PRE-EXISTING". MEASURED AT REVIEW: `python3 -m pytest tests/test_standalone_verify.py`
reports `28 passed in 1.11s`, and the whole file is green. Pre-authorizing an absent failure is worse
than silence, because it licenses an executor to ignore a real regression in that file.

THE ACTUAL BASELINE IN THIS LANE, measured at review: `1 failed, 7942 passed, 3 skipped, 2 xfailed in
105.59s`, the single failure being
`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`.
It is ENVIRONMENTAL: the assertion is `'OPENCODE_CONFIG_CONTENT' not in main_env`
(`tests/test_turn_bounds.py:310`) and that variable is set in the executing agent session. Nothing in
this plan's fence can affect it. Measure your own baseline anyway; this figure is a cross-check.

EXPECT TO UPDATE EXISTING TESTS, NOT ONLY TO ADD THEM (F-16). `tests/test_prompts_new.py` PINS THE
LEGACY BEHAVIOR and will fail by design once E-01 lands: `test_apply_writes_exactly_one_file_at_derived_path`
asserts the exact name `20260830-0930-01-token-compression.prompt.md`, and
`test_second_call_in_same_minute_increments_to_02` asserts the per-minute `-01`/`-02` sequence that
OQ-01 discards. Those are CORRECT tests of the old contract, so update them in the same change rather
than treating their failure as a regression; a reviewer should see the old assertions replaced, not
deleted.

## Spec / documentation sync

Naming spec `20260730-2152-01-agents-artifact-organization` section 5.4 is AMENDED by E-05 and is
declared in `Scope-Paths`. WHY THE AMENDMENT IS REQUIRED RATHER THAN OPTIONAL: requirement E3 makes
the type vocabularies an enumerated `[Must]`, and section 218 of that spec lists prompts as a
"subsequent adopter" of the clustered grammar; this plan makes prompts an ACTUAL adopter, so the spec
must say so or the next reviewer will check a prompt name against a spec that still exempts it. The
amendment must also record that `jxqdcw` OQ-02 is reversed, so a later reader does not treat the
reversal as drift.

THREE MEASURED FACTS ABOUT THAT SPEC THAT CHANGE HOW THE AMENDMENT MUST BE MADE (F-14), verified at
review. FIRST, ITS `- Status:` IS `implemented`, which is the one spec status AGENTS.md says an agent
may NOT set; that rule governs SETTING the status, and this plan does not change it, so amending the
BODY of an `implemented` spec is permitted. State that distinction in the amendment so a later reader
does not mistake it for an agent claiming implementation. SECOND, THE SPEC CARRIES NO `- Id:`, so it is
INVISIBLE to `discover_specs` (verified: it does not appear in that function's 17 records) and cannot
be named by an id6 selector; it IS resolvable by stem (`aw find specs agents-artifact-organization`
returns it). So cite it BY PATH in every reference, and do NOT attempt `aw specs set <id6>` on it. Do
NOT convert it to an id6 name here either; that is `aw rename specs --to-id6` work on an unrelated
artifact and would enlarge this plan's blast radius into the spec tree.
THIRD, AMEND IN THE ESTABLISHED SHAPE, which the file itself demonstrates: section 5.4 already carries
dated `AMENDED <date>` entries (`:182`) and the file carries dated `## Workflow history` notes
(`:248`). Follow that shape rather than inventing a new one, and use `aw specs note` for the history
line rather than hand-writing it, so the amendment is tool-attributed like its predecessors.

ONE MORE OBLIGATION THIS SECTION DID NOT STATE: the runner announces DECLARED spec edits before a run
starts and reconciles them at finalize, so this spec path must stay in `Scope-Paths` (it is) and the
amendment must actually be made (do not silently skip it if E-05's code edits land first). A run that
declares a spec edit and does not make it is reported at run end.

## Open questions

### OQ-01: What does `NN` mean in a prompt name after the migration?

- Blocking: yes
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ORDER WITHIN A SET. Resolved from repository evidence, not
  deferred, because the grep the question asked for settles it. TWO INCOMPATIBLE MEANINGS COLLIDED
  (F-7): `NN` was a PER-MINUTE SEQUENCE, and in the clustered grammar it is ORDER WITHIN A SET. THE
  EVIDENCE: `_STAGED_NAME_RE` has exactly ONE reader of its `nn` group, `prompts.py:119`, and it sits
  inside `_next_nn` (`prompts.py:108`), whose whole job is to compute the next free per-minute
  sequence for the minting verb itself. So the per-minute semantics have NO external consumer: nothing
  outside the mint path reads them, and no other module matches that regex (`grep -n
  _STAGED_NAME_RE agent_workflows/*.py` returns only `prompts.py:62` and `:115`). Discarding them
  therefore breaks no reader. It is also SAFE rather than merely unused: the counter existed to stop
  two prompts minted in the same minute colliding, and a repository-unique id6 in the name dissolves
  that collision outright. The executor keeps `_next_nn` only if a set genuinely needs ordering
  (a multi-prompt set), and otherwise emits `01` for a singleton, which is how research treats a lone
  doc.

### OQ-02: Where does the cutover date land, given that a conforming file already exists?

- Blocking: yes
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `20260921`, BUT THE REASONING ORIGINALLY GIVEN HERE WAS FACTUALLY
  WRONG AND WAS CORRECTED AT REVIEW (F-10). The conclusion survives; the argument for it does not, and
  an executor must not repeat the discarded version.
  THE RULE, which is unchanged: `SPEC_ID6_CUTOVER_DATE`'s own comment says "strictly AFTER the newest
  existing legacy-named spec date ... so ALL existing specs remain grandfathered".
  WHAT WAS FALSE. This question asserted that "the newest legacy prompt date in the tracked tree is
  `20260920`" and that "the tracked `pending/` tree still holds ONE `20260920`-dated legacy name".
  MEASURED AT REVIEW, BOTH ARE FALSE: the newest legacy-named tracked prompt is
  `20260829-1520-01-session-allocation-policy.prompt.md`, so the newest legacy date is `20260829`, and
  the ONLY `20260920`-dated prompt in the tree is the CONFORMING hand-made one (F-9), which is not a
  legacy name at all. The `untracked/` lane cited as the second reason DOES NOT EXIST in a lane
  worktree (`ls .aw/records/prompts/untracked/` -> "No such file or directory"), and no
  `20260920-12*` file exists anywhere in the tree, so that argument rested on a file that is not there.
  WHY `20260921` IS STILL CORRECT, on a rule the evidence actually supports. Applying the precedent's
  rule literally to the measured corpus would give `20260830`, and that is the WRONG choice here for a
  reason the precedent did not face: this tree ALREADY CONTAINS a conforming `20260920` prompt (F-9),
  and a cutover at or below `20260920` makes that file's conformance LOAD-BEARING rather than
  incidental. `20260921` keeps every existing name valid under EITHER shape, which is the property the
  precedent was actually protecting, and it forces id6 on everything minted after this plan ships.
  Choosing `20260830` would be defensible and is strictly tighter; it is NOT chosen because it buys
  nothing (no prompt exists between `20260830` and `20260920` to catch) while adding a way for the
  plan to fail on a file it did not create.
  RECORD THE DATE WHERE THE MECHANISM ACTUALLY READS IT (see E-03 as revised): the shipped resolver is
  config-driven, so the value belongs in `.aw/config/project.json` under `cutovers.prompt_id6` as
  `2026-09-21`, with a module constant only as the fallback.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual shell transcript of `aw prompts new --kind research --slug <x>` (no `--set`) and of the same with `--set <y>`, showing both written paths. Paste the id6 from each and show it is repository-unique by pasting an `aw find` or `grep -rc '\b<id6>\b'` result over the records trees. A name that lacks any of date, set, NN, id6, slug or the `.prompt.md` facet FAILS.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the first line of a freshly minted prompt showing `Id: <id6>` inside the single `<!-- aw-prompt: ... -->` comment, plus a count proving there is exactly ONE comment line and no YAML front matter (`head -3` of the file). A second metadata line, or a `---` front-matter fence, FAILS this item against the purity spec.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste checker output showing ZERO findings against ALL 17 grandfathered prompts, AND a demonstration that a post-cutover id6-less name IS refused (construct one in a temp dir or fixture and paste the refusal). Both halves are required: the grandfathering alone does not prove the rule fires.
    A DEFAULT `aw check prompts` DOES NOT SATISFY THE FIRST HALF AND MUST NOT BE PASTED AS IF IT DID (F-17). Measured at review: it examines only 2 files, because `is_retired` excludes the `executed/` and `superseded/` path segments where 15 of the 17 live. Obtain the 17-file result explicitly, e.g. `check_engine.check_names(repo_root, "prompts", include_retired=True)`, and PASTE THE FILE COUNT alongside the findings count so a reader can see all 17 were actually examined. A pasted "CONFORMS, 2 prompts checked" FAILS this item.
    ALSO PASTE THE RESOLVED CUTOVER VALUE that the code actually used, via `config.resolve_cutover_date(repo_root, "prompt_id6", compact=True)`, and show it is NOT `None`. A `None` here would grandfather every prompt forever and make the refusal half unreachable, which is the exact failure mode `CARRIER_CUTOVER_DATE`'s comment documents.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste a full `aw rename prompts <legacy> --to-id6` run, preview first and then applied, on a COPY or fixture rather than a live tracked prompt. Show the before and after filenames and the in-file metadata comment after conversion. Show `git status` proving nothing else moved.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the diff of EVERY documentation surface corrected (at least the five F-13 enumerates, plus the spec), and state the template decision explicitly.
    THE ORIGINALLY SPECIFIED GREP IS TOO NARROW AND WOULD PASS WHILE THREE SURFACES STILL LIE (F-13). Measured at review, `grep -rn "does NOT add an id6\|deliberately NOT used here" agent_workflows/ .aw/records/prompts/README.md` matches ONLY `artifact_naming.py:41` and `prompts.py:11`, so it cannot see the two READMEs or the workflow file at all. Use a grep that searches for the GRAMMAR rather than for two phrasings, over every surface: `grep -rn "YYYYMMDD-HHMM-NN" --include="*.md" --include="*.py" agent_workflows/ .aw/records/prompts/ .aw/system/workflows/research-prompt/`. Every surviving hit must be either corrected or explicitly justified (a historical citation inside an executed plan or a done backlog item is legitimate and need not change; a live instruction is not).
    The spec amendment must name `jxqdcw` OQ-02 explicitly; quote the sentence that does so. Also confirm the spec was cited BY PATH and that its `- Status: implemented` was NOT changed (F-14).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the result of parsing `20260920-plainlang-01-ng0ga4-plain-language-reporting-instructions.prompt.md` with the same parser the verb uses, showing every field it extracts. Paste its first line and compare it field by field against a freshly minted prompt's first line; name any difference. Confirm `ng0ga4` is still unique repository-wide.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN REVERSES A RECORDED DECISION (`jxqdcw` OQ-02), on the maintainer's explicit instruction
given 2026-09-20. An executor must not relitigate that reversal, and must not soften it into "the
legacy form was a bug": it was a resolved choice made on the evidence available then, and the
maintainer has since ruled the other way.

Execution contract: commit ONLY files this plan changed, path-scoped
(`git commit -m msg -- <path>`), never `git add -A`, never `-a`, and never push. THIS IS A SHARED
CHECKOUT with other agents and humans working concurrently: verify the staged set with
`git diff --cached --name-only` before every commit and `git restore --staged <path>` anything that is
not yours, and re-verify after ANY failed hook, because `pre-commit` restores unstaged changes on
rejection and can leave paths you never staged in the index.

Paste ACTUAL test output; do not claim a green suite that was not run. That rule bites hardest on E-04
and V-03 here: E-04's purity property has NO mechanical lint to cite (`aw prompts check` does not
exist), and V-03's grandfathering claim is FALSE if taken from a default `aw check prompts`, which
examines 2 of 17 files. Both must be demonstrated by pasted contents and counts, not asserted.

Both blocking open questions (OQ-01, OQ-02) are RESOLVED and recorded in this file. OQ-02's ORIGINAL
REASONING WAS MEASURED FALSE AT REVIEW and rewritten while keeping its `20260921` answer; an executor
must read the current text and must not restore the discarded argument.

SCOPE FENCE, AS A DECLARATION: the `Scope-Paths` list was WIDENED at review (adding
`artifact_rename.py`, `.aw/config/project.json`, `.aw/records/prompts/pending/README.md`,
`.aw/system/workflows/research-prompt/research-prompt.md`, and correcting two test paths that did not
exist). It exists so the runner can reconcile afterwards what changed; an out-of-scope edit is MADE and
then JUSTIFIED at finalize with `--scope-reason`, not a reason to halt. Any declared path you do not
touch needs a `--scope-ack`. The conditions that DO warrant stopping and reporting: a purity violation
you cannot fix without changing shared behavior for specs, or a spec contradiction beyond the one
amendment this plan declares.

THIS PLAN DECLARES A SPEC EDIT, and both runners announce that before the run starts and reconcile it
at finalize. The amendment must actually be made; a declared-but-unmade spec edit is reported at run end.

Post-gate lifecycle move: when every `E-*` is performed and every `V-*` verified with pasted
evidence, and `aw ipd lint --phase pre-transition` conforms, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, never by hand. IF A RUNNER IS DRIVING THIS PLAN it
owns `aw ipd begin` and `aw ipd finalize` and auto-reconciles the scope delta, so do not invoke either
yourself; an agent or human executing directly owns both calls.

This plan requires explicit human approval before execution.
