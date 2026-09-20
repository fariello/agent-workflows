# IPD: Mint an id6 for staged prompts and migrate the prompts tree to the uniform clustered grammar

- Date: 2026-09-20
- Kind: child
- Concern: A STAGED PROMPT CANNOT BE CITED, because `aw prompts new` emits a name carrying no id6. `AGENTS.md` states ONE uniform artifact-naming grammar, `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`, and every tracked type has adopted it except four; prompts is one of the four. Measured 2026-09-20: 17 prompts across `pending/`, `executed/` and `superseded/`, and NOT ONE carries an id6 (`ls .aw/records/prompts/*/*.md | grep -cE '[0-9]{8}-[a-z0-9]+-[0-9]{2}-[0-9a-z]{6}-'` returns 0 once two loose-regex false positives are excluded, both of which are legacy `YYYYMMDD-HHMM-NN` names). The consequence is not cosmetic: every `aw` verb resolves an artifact BY id6, so a prompt is invisible to `aw find`, cannot be named in a `consumed-by` or `From-*` field, and cannot be paired with the research report it produced except by prose. That pairing is the normal lifecycle of a research prompt (research sets put the originating prompt at `NN=00` and cite it by id6), so the one artifact type that most needs a citable handle is the one type that has none.
- Scope: Mint an id6 in `aw prompts new`, emit the uniform clustered name, add a dated cutover so every existing prompt stays valid, and ship an on-demand converter for a legacy name. Follows the SPEC PRECEDENT exactly (IPD `ha55fi`), which migrated specs out of the same id6-less set. Includes the two documentation surfaces that would otherwise contradict the code (`.aw/records/prompts/README.md`, `agent_workflows/artifact_naming.py`'s scope docstring) and the naming spec section that enumerates the vocabulary. EXCLUDES a mass rename of the 17 existing prompts (the cutover grandfathers them, exactly as `ha55fi` left 24 legacy specs in place), EXCLUDES roadmaps/releases/walkthroughs (the other three id6-less types, each its own migration), and EXCLUDES any change to the prompt-purity contract (the single leading HTML comment and the no-body-boilerplate rule are owned by approved spec `20260808-1958-01-prompt-purity-lint` and are untouched here).
- Scope-Paths: agent_workflows/prompts.py, agent_workflows/artifact_naming.py, agent_workflows/check_engine.py, agent_workflows/cli.py, .aw/records/prompts/README.md, .aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md, tests/test_prompts.py, tests/test_artifact_naming.py
- Item-Dependencies: none
- Status: to-review
- Set: promptid6
- Order: 1
- Highest E allocated: 06
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: ubac5n

## Workflow history

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

- [ ] E-03 Add a dated cutover constant beside `SPEC_ID6_CUTOVER_DATE` in `check_engine.py`, chosen by the SAME rule its comment states: strictly after the newest existing legacy prompt date, so all 17 existing prompts stay valid. Enforce the clustered grammar for a prompt whose filename date is at or after it, and leave a pre-cutover name conforming.
  - Depends on: E-01
  - Expected outcome: `aw check` accepts all 17 existing legacy prompt names and refuses a NEW post-cutover prompt that lacks an id6.
  - Execution state: pending
- [ ] E-04 Ship the on-demand converter `aw rename prompts <legacy> --to-id6`, mirroring the spec verb at `cli.py:3654`: mint an id6, derive the clustered name, `git mv`, and update the in-file metadata comment. Preview by default.
  - Depends on: E-01, E-02
  - Expected outcome: a legacy prompt converts in one command; the converted file's name and metadata agree; nothing else in the tree changes.
  - Execution state: pending

### Task group 3: close the documentation contradictions

- [ ] E-05 Correct all three places that currently assert the id6-less choice, in ONE pass so no surface contradicts the code: `prompts.py`'s module docstring (F-4), `artifact_naming.py`'s id6-less enumeration (F-5, written in the same shape as the specs carve-out immediately below it), and `.aw/records/prompts/README.md`'s naming paragraph (which `jxqdcw` had corrected TOWARD the legacy form, so this reverses that edit). Amend naming spec section 5.4 with a dated entry recording the reversal and its reason (F-6).
  - Depends on: E-01, E-03
  - Expected outcome: no shipped docstring, README, or spec states that prompts carry no id6; the spec amendment names `jxqdcw` OQ-02 as the decision being reversed and the maintainer's instruction as the authority.
  - Execution state: pending
- [ ] E-06 Reconcile the one hand-renamed file (F-9): confirm `20260920-plainlang-01-ng0ga4-plain-language-reporting-instructions.prompt.md` parses under the new grammar, that its `ng0ga4` is still repository-unique, and that its in-file metadata matches what E-02 now emits. If the cutover date chosen in E-03 falls on or before 20260920, this file is post-cutover and MUST conform; verify it does rather than assuming.
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
- THE CUTOVER PATTERN ALREADY EXISTS, once, for specs: `check_engine.SPEC_ID6_CUTOVER_DATE`
  (`agent_workflows/check_engine.py:40`) is a compact `YYYYMMDD` string, and its own comment records
  both the mechanism ("require_id6 iff filename date >= this") and the choice rule ("strictly AFTER
  the newest existing legacy-named spec date ... so ALL existing specs remain grandfathered"). That
  comment also states there was "NO pre-existing name-conformance cutover mechanism in this module to
  reuse (verified)", so this plan adds the SECOND instance and should mirror it rather than invent a
  different shape.
- THE CONVERTER PATTERN ALREADY EXISTS: `aw rename specs <legacy> --to-id6` (`cli.py:3654`). The
  prompts equivalent belongs beside it.
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
| F-9 | One file was hand-renamed to the target grammar ahead of this plan, at the maintainer's instruction, so the prompt they are about to send is correctly named: `20260920-plainlang-01-ng0ga4-plain-language-reporting-instructions.prompt.md`. It is therefore the ONLY conforming prompt in the tree and will be a post-cutover name produced by hand rather than by the verb. E-06 reconciles it. | this session; `mint_id6` output `ng0ga4` |

## Proposed changes (ordered, validatable)

1. `prompts.py`: add `--set`, mint via `artifact_core.mint_id6`, build the name via
   `artifact_naming.build_clustered_name(..., artifact_type="prompt")`, and add `Id:` to the metadata
   comment (E-01, E-02).
2. `check_engine.py`: add the prompt cutover constant and its conformance rule (E-03).
3. `cli.py`: add `aw rename prompts --to-id6` (E-04).
4. Docs and spec: `prompts.py` docstring, `artifact_naming.py` enumeration, prompts README, naming
   spec 5.4 amendment (E-05).
5. Tests: extend `tests/test_prompts.py` and `tests/test_artifact_naming.py` (V items below).

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

## Scope check

- Over-scope: none. Every path in `Scope-Paths` is either the code that emits or validates the name,
  or a document that currently asserts the opposite of what this plan makes true.
- Under-scope: the other three id6-less types, and the 17 grandfathered names. Both are deliberate
  and are recorded above with reasons.

## Required tests / validation

Bare `python3 -m pytest` (addopts already supplies `-q -n auto --dist=worksteal -m 'not slow'`).
NOTE FOR THE EXECUTOR, measured 2026-09-20: `tests/test_standalone_verify.py::TheAuditCannotTouchTheFinishedPlan`
has TWO failures that are PRE-EXISTING and unrelated to this plan (proven by stashing an unrelated
file and reproducing them unchanged). Do not attribute them to this work, and do not "fix" them here.

## Spec / documentation sync

Naming spec `20260730-2152-01-agents-artifact-organization` section 5.4 is AMENDED by E-05 and is
declared in `Scope-Paths`. WHY THE AMENDMENT IS REQUIRED RATHER THAN OPTIONAL: requirement E3 makes
the type vocabularies an enumerated `[Must]`, and section 218 of that spec lists prompts as a
"subsequent adopter" of the clustered grammar; this plan makes prompts an ACTUAL adopter, so the spec
must say so or the next reviewer will check a prompt name against a spec that still exempts it. The
amendment must also record that `jxqdcw` OQ-02 is reversed, so a later reader does not treat the
reversal as drift.

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
- Resolution or deferral rationale: `20260921`. Resolved from repository evidence. The rule stated in
  `SPEC_ID6_CUTOVER_DATE`'s own comment is "strictly AFTER the newest existing legacy-named spec date
  ... so ALL existing specs remain grandfathered"; applied here, the newest legacy prompt date in the
  tracked tree is `20260920`, so the cutover is `20260921`. MEASURED, which is what rules out the
  tighter `20260920`: after the rename in E-06 the tracked `pending/` tree still holds ONE
  `20260920`-dated legacy name, and it is not a prompt this plan renames. `aw prompts new` also wrote
  the handoff document produced this same session into the GITIGNORED `untracked/` quarantine lane
  under a legacy `20260920-1245-01-...` name, and that lane is out of this plan's reach by design
  (`prompts.py`'s docstring: this module "never writes to or promotes from the gitignored
  ``untracked/`` quarantine lane"). A cutover of `20260920` would therefore demand conformance from
  at least one name that nothing in this plan converts. `20260921` grandfathers every existing prompt,
  which is exactly the property the precedent chose, and leaves the one hand-renamed conforming file
  (F-9) harmlessly pre-cutover since it conforms anyway.

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
  - Required evidence: paste `aw check` (or the targeted checker) output showing ZERO findings against the 17 grandfathered prompts, AND a demonstration that a post-cutover id6-less name IS refused (construct one in a temp dir or fixture and paste the refusal). Both halves are required: the grandfathering alone does not prove the rule fires.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste a full `aw rename prompts <legacy> --to-id6` run, preview first and then applied, on a COPY or fixture rather than a live tracked prompt. Show the before and after filenames and the in-file metadata comment after conversion. Show `git status` proving nothing else moved.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the diff of all four documentation surfaces. Then paste a grep proving NO shipped surface still claims prompts carry no id6: `grep -rn "does NOT add an id6\|deliberately NOT used here" agent_workflows/ .aw/records/prompts/README.md`. A surviving claim FAILS. The spec amendment must name `jxqdcw` OQ-02 explicitly; quote the sentence that does so.
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
(`git commit -m msg -- <path>`), never `git add -A`, never push. Paste ACTUAL test output; do not
claim a green suite that was not run. Both blocking open questions (OQ-01, OQ-02) must be resolved and
recorded IN THIS FILE before any code is written, because each one decides a field's meaning that the
rest of the work depends on.

Post-gate lifecycle move: when every `E-*` is performed and every `V-*` verified with pasted
evidence, and `aw ipd lint --phase pre-transition` conforms, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, never by hand.

This plan requires explicit human approval before execution.
