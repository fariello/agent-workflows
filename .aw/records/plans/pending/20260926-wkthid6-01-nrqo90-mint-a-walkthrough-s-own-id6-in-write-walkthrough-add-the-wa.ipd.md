# IPD: Mint a walkthrough's own id6 in write_walkthrough, add the walkthrough id6 cutover, and re-id the three D140 walkthroughs

- Date: 2026-09-26
- Kind: child
- Concern: Walkthroughs are the last artifact type without id6-in-filename adoption: 11 of 24 use legacy names, the only programmatic producer (`set_records.write_walkthrough`) names the file with a caller-supplied id6 that its caller fills with the documented PLAN's id6, and three hand-written walkthroughs already reuse their plan's id6, producing 3 live `check.id6-identity-slot` errors (D140).
- Scope: IN: mint the walkthrough's own id6 in `write_walkthrough` and record the plan as `- Target-Id:`; a `walkthrough_id6` feature cutover with a `_walkthrough_requires_id6` checker twin; correct the stale `artifact_naming` docstring; re-id the 3 D140 walkthroughs and update their live citations; README, shipped template and uniform-grammar spec row. OUT: renaming the 11 grandfathered legacy walkthroughs; releases and roadmaps (already id6-bearing); any new rename verb.
- Scope-Paths: agent_workflows/set_records.py, agent_workflows/config.py, agent_workflows/check_engine.py, agent_workflows/artifact_naming.py, .aw/config/project.json, tests/test_walkthrough_id6.py, .aw/records/walkthroughs/, .aw/records/plans/executed/20260829-runstop-00-zpbx7o-runner-graceful-quit-protocol-adopt-spec-c4gd2h.ipd.md, .aw/records/plans/executed/20260901-lanectn-04-y5od1h-bounded-missing-input-repair-without-original-checkout-acces.ipd.md, .aw/records/plans/executed/20260916-lanectn-07-4fodkt-demonstrate-the-whole-set-acceptance-criteria-of-spec-7ckptx.ipd.md, .aw/system/workflows/templates/agents-docs-walkthroughs-README.md, .aw/records/specs/implemented/20260817-2147-01-uniform-artifact-naming-grammar.spec.md
- Item-Dependencies: none
- Status: to-review
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: f2u4l0
- Set: wkthid6
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: nrqo90

## Workflow history
- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-609. Reviewed in an isolated lane worktree at HEAD 74e672a2. Every claim re-measured: F-1/F-2/F-5/F-6 confirmed, F-3's count corrected (5 total findings at HEAD, not 9) and its `e2j5w4` status corrected (still `open`). Three verification defects fixed: E-09's `check.id6-identity-slot` proof is satisfied by RENAMING ALONE (measured: rule (b) exempts a renamed file with no `- Id:`), so the `- Id:` half of E-05 had no failing assertion; E-09's `aw find` assertion is FALSE as written for `y5od1h`/`4fodkt` (a review record shares the plan's stem); and E-07's citation census missed 2 of 8 citing files. E-03's cutover rationale contradicted the documented two-date contract and was corrected.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog f2u4l0: walkthroughs mint their own id6 with a walkthrough_id6 cutover; re-id the 3 D140 walkthroughs; releases/roadmaps already done.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Finish the id6 adoption for the last holdout type, walkthroughs: the walkthrough producer mints the walkthrough's OWN id6 (recording the documented plan as `- Target-Id:`), a `walkthrough_id6` cutover makes the checker require the clustered grammar going forward, and the three walkthroughs that reuse their plan's id6 today get their own identity, so `aw check all` is clean of `check.id6-identity-slot`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: outcome tests

- [ ] E-01 Add `tests/test_walkthrough_id6.py` with three outcome tests on a tmp git repo (the `_RepoTestCase` shape in `tests/test_spec_id6_filenames.py`, plus `.aw/records/plans/executed/` and `.aw/records/walkthroughs/`): (a) create an executed plan with `- Id: pl1abc`, call `set_records.write_walkthrough(repo, set_id="s", order=1, target_id6="pl1abc", slug="x", body=<render_walkthrough output>)`, and assert the returned file's name matches `YYYYMMDD-s-01-<id6>-x.walkthrough.md` with `<id6> != "pl1abc"`, the file declares `- Id: <id6>` and `- Target-Id: pl1abc`, and `check_engine.check_collisions(repo, include_retired=True)` returns no `check.id6-identity-slot` Drift; (b) with `.aw/config/project.json` `{"cutovers": {"walkthrough_id6": "2026-09-27"}}`, a walkthrough named `20260928-1200-01-late-walkthrough.walkthrough.md` yields one `check.name-nonconformant` from `check_engine.check_names(repo, "walkthroughs")` whose detail names the walkthrough cutover; (c) under the same config, `20260712-1023-01-early-walkthrough.walkthrough.md` yields none. Tests assert OUTCOMES only (returned names, file contents, Drift rule ids), not source text or docstrings.
  - Depends on: none
  - Expected outcome: (a) fails at HEAD (the name reuses `pl1abc`, and `target_id6` is not a parameter); (b) fails (walkthroughs never require id6); (c) passes.
  - Execution state: pending

### Task group 2: producer and checker

- [ ] E-02 Mint inside the producer. In `set_records.write_walkthrough`, replace the caller-supplied `id6` parameter with `target_id6` (the documented plan) and mint the walkthrough's own id6 with `artifact_core.mint_id6(repo_root, <id6s already used in the walkthroughs dir>)`, the repository-wide mint seam every producer uses (IPD sk7ggr). Build the name with that id6. Insert `- Id: <minted>` and `- Target-Id: <target_id6>` into the body's metadata block, directly after the `- Set:` bullet `render_walkthrough` emits (fall back to after the H1's blank line when no `- Set:` bullet exists), so the file satisfies D140 rule (a). Update `promote_local_checkpoints` to pass its `id6` argument as `target_id6` and rename that argument `target_id6` too (no caller in `agent_workflows/` or `tests/` today, measured, so the rename breaks nothing). Update the `write_walkthrough` docstring accordingly.
  - Depends on: E-01
  - Expected outcome: E-01 (a) passes.
  - Execution state: pending

- [ ] E-03 Add the cutover, the exact twin of `prompt_id6` (IPD ubac5n E-03). Register `"walkthrough_id6": "<the date this feature is introduced, i.e. the execution date, YYYY-MM-DD>"` in `config.KNOWN_FEATURE_CUTOVERS` with a comment in the same shape as the `prompt_id6` entry. STATE THE VALUE'S MEANING CORRECTLY, because the authored rationale had it backwards: this dict holds the FEATURE INTRODUCTION DATE (a fact about the toolkit, identical in every repository), and it is explicitly NOT the enforcement boundary. The boundary is the per-repo value stamped into `.aw/config/project.json` by `sync_cutovers_on_install`, which uses the intro date as the INPUT TO A SEARCH over `installs.jsonl` and falls back to the install date. The block comment above `KNOWN_FEATURE_CUTOVERS` says this at length and names "stamp the current install date instead" as a REJECTED option (`x75obw` OQ-03 option (b)). So do NOT justify the value by "strictly after the newest tracked walkthrough date": that reasoning describes a boundary this entry does not set. It happens to hold here (measured: newest tracked walkthrough is `20260918`, and this repo has no `installs.jsonl`, so the stamped boundary resolves to the install date, which is later), and the grandfathering of all 24 existing walkthroughs must be VERIFIED by V-03's measurement rather than asserted from the intro date. Add the non-None fallback `check_engine.WALKTHROUGH_ID6_CUTOVER_DATE` (same compact value) beside `PROMPT_ID6_CUTOVER_DATE`, and `check_engine._walkthrough_requires_id6(filename, repo_root)` as the structural twin of `_prompt_requires_id6` (config first via `config.resolve_cutover_date(repo_root, "walkthrough_id6", compact=True)`, constant fallback, unparseable leading date treated as pre-cutover). Wire it in `check_names`' `if record_type == "specs": ... elif record_type == "prompts": ...` chain, and extend the `feature, fallback, noun` selection that builds the `require_id6` detail message to a three-way mapping so the message names the walkthrough cutover and `aw rename walkthroughs <name> --to-id6 --apply` (a working converter for both legacy walkthrough shapes: the HHMM form via the `--to-id6` legacy-timestamp branch and the dated form via the dl86am branch of `artifact_rename.compute_target_name`). Stamp the same key into this repo's `.aw/config/project.json` `cutovers` object, as ubac5n did for `prompt_id6`.
  - Depends on: E-01
  - Expected outcome: E-01 (b) and (c) pass; `tests/test_config.py` still passes; and, measured on THIS tree after stamping, `check_names(repo, "walkthroughs")` reports ZERO `check.name-nonconformant` for all 24 existing walkthroughs (review pre-measured this against a simulated `20260927` boundary and got 0, so a nonzero result means the boundary landed earlier than intended and must be investigated, not waved through).
  - Execution state: pending

- [ ] E-04 Correct the stale docstring in `artifact_naming` (the paragraph beginning "id6-less legacy types (OQ documentation requirement): roadmaps, releases, and walkthroughs do not yet carry an id6"): releases already mint an id6 (`releases.render_release` calls `_core.mint_id6` and names the file `{today}-{id6}-01-{id6}-{slug}.release.md`), and the one tracked roadmap is clustered (`20260712-7ny1bg-01-7ny1bg-...roadmap.md`). Rewrite it to say walkthroughs adopt the id6-clustered grammar going forward under the `walkthrough_id6` cutover with pre-cutover legacy names grandfathered, releases mint an id6 at creation, and roadmaps have no producer and are clustered by convention (the checker does not enforce id6 for roadmaps).
  - Depends on: E-03
  - Expected outcome: the docstring matches the code.
  - Execution state: pending

### Task group 3: re-id the three D140 walkthroughs

- [ ] E-05 Give each walkthrough that reuses its plan's id6 its own identity, by hand because `aw rename --to-id6` is a measured no-op on an already-clustered name (`cli.py` collision remedy text: "`aw rename --to-id6` is a no-op on an already-clustered name"). For each of `20260901-runstop-00-zpbx7o-graceful-quit-whole-set-verification.walkthrough.md`, `20260917-lanectn-07-4fodkt-whole-set-verification-of-spec-7ckptx.walkthrough.md` and `20260906-lanectn-04-y5od1h-missing-input-report-and-refuse-walkthrough.md`: mint one id6 with `python3 -c "from pathlib import Path; from agent_workflows import artifact_core as c; print(c.mint_id6(Path('.')))"`; `git mv` the file to the same name with the plan id6 in the identity slot replaced by the minted one (keep date, setid, NN, slug; give the y5od1h file the `.walkthrough.md` facet it lacks, i.e. `...-missing-input-report-and-refuse.walkthrough.md`, since its current `...-walkthrough.md` ending is the only facet-less clustered walkthrough); add `- Id: <minted>` to its metadata bullets; and add `- Target-Id: y5od1h` to the y5od1h walkthrough, which today names its plan only in a prose `- Plan:` bullet (the other two already carry `- Target-Id:`). The maintainer's instruction in this plan's brief ("re-id the 3 D140 walkthroughs") is the decision backlog `mw0s1y` says is required before renaming these records.
  - Depends on: E-02
  - Expected outcome: three walkthroughs whose slot id6 equals their own declared `- Id:`. BOTH HALVES ARE REQUIRED AND ONLY ONE IS CHECKED BY E-09, which is why E-06 exists: measured in review, `_check_identity_slots` returns `[]` for a file that was RENAMED to a fresh id6 and declares NO `- Id:` (rule (b) applies, nobody else owns the fresh id6, so nothing fires). So renaming alone clears `check.id6-identity-slot` while leaving the D140/README requirement ("a walkthrough MUST mint its own id6 there" AND declare it) unmet. Do not treat a clean `aw check` as evidence that the `- Id:` bullets were added.
  - Execution state: pending

- [ ] E-06 ASSERT THE `- Id:` HALF WITH A CHECK THAT CAN FAIL. Add to `tests/test_walkthrough_id6.py` one outcome test over the REAL repository tree (`Path(__file__).resolve().parent.parent`, the `REPO_ROOT` shape the suite already uses): for every file under `.aw/records/walkthroughs/` whose name carries a clustered identity slot (parse with the shipped normalizer rather than a hand-written regex), assert the file declares a `- Id:` in its metadata region and that it EQUALS the slot id6. Use `check_engine._identity_declared_values` to read the declaration, so the test and the checker agree on what "declared in the metadata region" means and a quoted example cannot satisfy it. Exempt the 11 legacy names (no identity slot) explicitly, so the test states the grandfathering rather than silently skipping. This test FAILS at HEAD on the three D140 files and on any file E-05 renames without adding `- Id:`, which is the assertion the plan was missing.
  - Depends on: E-05
  - Expected outcome: fails at HEAD naming the 3 D140 walkthroughs; passes after E-05; and fails if a walkthrough is renamed without its `- Id:` bullet (verify by temporarily deleting one bullet).
  - Execution state: pending

- [ ] E-07 Update inbound citations deliberately, not wholesale. Preview with `artifact_refs.plan_reference_rewrites(Path('.'), {<old>: <new>, ...})` and classify each hit. THE CENSUS IS EIGHT FILES, NOT FIVE; the authored list named five and review measured eight (36 edits across 8 files). REWRITE the evidence citations in the three documented plans (executed `zpbx7o`, `y5od1h`, `4fodkt`), which point a reader at the walkthrough and would otherwise dangle; this is reference rewriting of an executed plan, declared in Scope-Paths. KEEP unchanged: (i) the paths inside fenced command output in executed plan `t0jyb2` (collpop), which record what `aw check` printed; (ii) the fenced driven-evaluation transcript AND the embedded `aw check --agent` JSON in executed plan `20260925-carrierauth-01-vtkfq8-...` (6 hits, NOT named by the authored list, same transcript class as `t0jyb2`); and (iii) the measurement text in backlog items `mw0s1y` and `e2j5w4`, which describe the defect as it was. The eighth file is THIS PLAN, whose own quoted filenames must also stay as written (they are the authored evidence), so the preview's hits on it are KEEP too. Since `plan_reference_rewrites` has no per-file exclusion, do NOT call `apply_reference_rewrites` on the whole edit list: apply only the edits whose `file` is one of the three documented plans, or edit those three by hand. ALSO NOTE the `y5od1h` facet fix changes the stem, so the preview emits a `bare-stem` edit alongside the `full-name` one; `apply_reference_rewrites` orders full-name first, so the pair composes correctly (verified in review), but a hand edit must handle both forms.
  - Depends on: E-06
  - Expected outcome: the three plans cite the new names; `t0jyb2`, `vtkfq8`, both backlog items and this plan are byte-identical.
  - Execution state: pending

### Task group 4: docs and proof

- [ ] E-08 Docs: in `.aw/records/walkthroughs/README.md` add one sentence that walkthroughs dated at/after the repository's `walkthrough_id6` cutover must use the clustered grammar, that a programmatic walkthrough (`set_records.write_walkthrough`) mints its own id6 and records the plan as `Target-Id:`, and that the 11 pre-cutover legacy names stay valid. Fix the shipped template `.aw/system/workflows/templates/agents-docs-walkthroughs-README.md`, which still says "Named `YYYYMMDD-HHMM-NN-<slug>-walkthrough.md` (local time)", to the clustered grammar with the same sentence. Amend spec `20260817-2147-01-uniform-artifact-naming-grammar` Section 2.1's Walkthrough row the way ubac5n amended the Prompt row (id6-clustered going forward under the `walkthrough_id6` cutover, legacy grandfathered, own id6 + `Target-Id:` per D140) and record it with `aw specs note <spec> --message "IPD nrqo90 (wkthid6): walkthroughs adopt id6-in-filename going forward ..."`.
  - Depends on: E-04
  - Expected outcome: README, template and spec agree with the code.
  - Execution state: pending

- [ ] E-09 Prove it on this repository. (1) `python3 -m agent_workflows check all --agent` shows ZERO `check.id6-identity-slot` findings and no new finding of any other rule; the HEAD baseline to compare against is 5 findings total (3 `check.id6-identity-slot`, 1 `check.scope-drift`, 1 `check.system-layout-missing`), re-measured in review, so the expected after-state is 2 findings and the two survivors are pre-existing and unrelated. THIS CHECK ALONE IS NOT SUFFICIENT: it is satisfied by renaming without declaring `- Id:` (see E-05), so E-06's test is the assertion that covers the other half. (2) `python3 -m agent_workflows check walkthroughs --all` reports no `check.name-nonconformant` for the 11 legacy walkthroughs (pre-cutover). (3) `python3 -m agent_workflows find <each minted id6>` returns exactly one walkthrough. (4) `python3 -m agent_workflows find zpbx7o` returns ONLY the plan; `find y5od1h` and `find 4fodkt` each return the plan AND its same-named REVIEW record under `.aw/records/reviews/`, and that is CORRECT, not a defect: a review record is named after the plan it reviews and legitimately shares its id6 handle. The authored "returns only the plan" assertion was FALSE for those two (measured in review) and would have made a correct outcome look like a failure; the real assertion is that NO WALKTHROUGH appears, and that the D140 collision warning `aw find` prints today is gone. Then ruff on the edited Python files and the bare suite `python3 -m pytest` (baseline re-measured in review: `2584 passed, 2 skipped`).
  - Depends on: E-07, E-08
  - Expected outcome: all hold; suite passes with no new failures against the pasted baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The id6-cutover shape is established twice (ha55fi specs, ubac5n prompts): `config.KNOWN_FEATURE_CUTOVERS` entry + `.aw/config/project.json` stamp + module constant fallback + `_<type>_requires_id6` twin + wiring in `check_names` + doc corrections.
- D140 (`DECISIONS.md`) and `.aw/records/walkthroughs/README.md`: the slot id6 is the walkthrough's own; the plan link is `- Target-Id:`. `check_engine._check_identity_slots` rule (a) compares the slot to the declared `- Id:`; rule (b) flags an undeclared slot id6 owned by another file.
- `artifact_core.mint_id6` is the one mint seam (repository-wide collision set, IPD sk7ggr).
- Editing an executed plan is permitted only as reference rewriting and must be declared.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1..F-6 authored and re-verified in review at HEAD `74e672a2`. F-7..F-10 found in review at the same HEAD.

| Id | Evidence | Finding |
|---|---|---|
| F-1 | `releases.render_release`: `id6 = _core.mint_id6(repo_root, _existing_ids(repo_root))`, `name = f"{today}-{id6}-01-{id6}-{slug}.release.md"`; `git ls-files .aw/records/roadmaps` -> one file, `20260712-7ny1bg-01-7ny1bg-...roadmap.md` | Releases and roadmaps are done; backlog `f2u4l0`'s three-holdout framing is stale for two of them. Confirmed. |
| F-2 | 26 tracked files under `.aw/records/walkthroughs/`, of which 24 are walkthroughs (the other two are `.gitkeep` and `README.md`): 11 legacy `YYYYMMDD-HHMM-NN-` names (none declare `- Id:`), 13 clustered | Confirmed "11 of 24". Note for the executor: a `git ls-files` count returns 26, so a census must exclude the two non-records. |
| F-3 | `aw check all --agent` at HEAD: 5 findings total, of which 3 are `check.id6-identity-slot` on the zpbx7o, y5od1h and 4fodkt walkthroughs (the other two are 1 `check.scope-drift` + 1 `check.system-layout-missing`, pre-existing and unrelated); `zpbx7o`/`4fodkt` carry `- Target-Id:` and no `- Id:`, `y5od1h` carries neither (only a prose `- Plan:` path) | Confirmed as to the 3 slot findings and their per-file shape. CORRECTED IN REVIEW: the total is 5, not the 9 the authored V-09 assumed. Also tracked as backlog `mw0s1y` (bug, Blocks-Release next). `e2j5w4`'s detection defect is fixed IN CODE (`check_collisions(repo)` now returns the 3 slot findings with default arguments, measured), but the ITEM IS STILL `- Status: open`, so "already fixed" is true of the code and false of the record; this plan neither closes nor is blocked by it. |
| F-7 | Measured: `_check_identity_slots([(plan,'zpbx7o','zpbx7o'), (walkthrough,None,'aaa111')])` -> `[]`; `_is_real_id6('aaa111', {'zpbx7o'})` -> `True` (rule (b) applies, no other owner, nothing fires) | E-09'S CENTRAL PROOF IS SATISFIED BY RENAMING ALONE. A walkthrough renamed to a fresh id6 but declaring no `- Id:` produces zero `check.id6-identity-slot`, so the `- Id:` half of E-05 (which is what D140 rule (a) and the README actually require) had no assertion that could fail. Closed by new E-06. |
| F-8 | `aw find y5od1h` at HEAD returns the plan, the walkthrough AND `.aw/records/reviews/20260901-lanectn-04-y5od1h-...review.md`; same for `4fodkt`; `zpbx7o` returns plan + walkthrough only | E-09's "`find <plan id6>` returns only the plan" was FALSE for two of three, because a review record is named after the plan it reviews. Left as written it would report a correct post-fix state as a failure. Corrected in E-09 (4). |
| F-9 | `artifact_refs.plan_reference_rewrites` driven on the three renames: 36 edits across 8 files, including 6 hits in executed plan `20260925-carrierauth-01-vtkfq8-...` (fenced driven-evaluation transcript + an embedded `aw check --agent` JSON) and 6 in this plan itself | THE CITATION CENSUS MISSED 2 OF 8 FILES. `vtkfq8` is the same transcript-KEEP class as `t0jyb2` but was unnamed, so an executor applying the whole preview would have rewritten a recorded transcript; and the preview also hits this plan. Corrected in E-07, which now names all eight and forbids a wholesale `apply_reference_rewrites`. |
| F-10 | `config.KNOWN_FEATURE_CUTOVERS`' block comment: "THE FEATURE INTRODUCTION DATE - the value in this dict ... DATE 1 IS THE INPUT TO A SEARCH, NOT THE BOUNDARY"; `resolve_cutover_date(repo,'spec_id6')` -> `20260829` while the dict holds `2026-08-28` | E-03's rationale ("the value must be strictly after the newest tracked walkthrough date so every existing walkthrough stays grandfathered") described the entry as if it were the enforcement boundary, which the code explicitly says it is not. The grandfathering conclusion is correct here but was reached by the wrong route, so it was asserted rather than verified. Corrected in E-03; V-03 now measures it. |
| F-4 | `set_records.write_walkthrough(repo_root, *, set_id, order, id6, slug, body)` names the file with the caller's `id6`; `promote_local_checkpoints` passes its own `id6`; `git grep` finds no caller of either outside `set_records.py` (only stale `.pyc` of a removed test) | The producer would reproduce the D140 violation if called. It is currently unused, so changing the signature is safe; the fix still matters because it is the documented recovery path. The three existing violations were hand-authored, not produced by this function. |
| F-5 | `artifact_naming` module docstring, "id6-less legacy types ... roadmaps, releases, and walkthroughs do not yet carry an id6 in most on-disk names" | Stale for releases and roadmaps. Confirmed. |
| F-6 | `templates/agents-docs-walkthroughs-README.md`: "Named `YYYYMMDD-HHMM-NN-<slug>-walkthrough.md` (local time)." | Stale shipped template; installed into other repos. Added to scope. |

The 11 legacy walkthroughs are NOT renamed: they predate the new cutover and are grandfathered by it, exactly as pre-cutover specs and prompts were, and renaming them would rewrite tracked history for no checker benefit. `aw rename walkthroughs <name> --to-id6 --apply` remains available on demand.

## Proposed changes (ordered, validatable)

1. Outcome tests (E-01).
2. Producer mints its own id6 and writes `Id`/`Target-Id` (E-02).
3. `walkthrough_id6` cutover + checker twin (E-03); docstring fix (E-04).
4. Re-id the three D140 walkthroughs (E-05), assert the `- Id:` half with a test that can fail (E-06), and update their live citations only, from the corrected 8-file census (E-07).
5. README, template, spec row (E-08); live proof, ruff, suite (E-09).

## Deferred / out of scope (with reason)

- Renaming the 11 pre-cutover legacy walkthroughs.
  - Carrier-Declined: grandfathered by the new cutover by design (same policy as ha55fi specs and ubac5n prompts); the on-demand converter exists.
- Closing backlog `mw0s1y` (the data half of the D140 violation), which E-05 performs.
  - Carrier: mw0s1y
- Closing source backlog `f2u4l0` as done.
  - Carrier: f2u4l0

## Scope check

- Over-scope: none.
- Under-scope: the shipped walkthroughs README template (F-6) and the uniform-grammar spec row are included, since ubac5n showed a surface left asserting the old grammar misleads the next author.
- `.aw/records/walkthroughs/README.md` (edited by E-08) is covered by the directory entry `.aw/records/walkthroughs/` in `- Scope-Paths:`, which `ipd_lifecycle._scope_match` treats as directory-bounded (a trailing-slash entry matches anything beneath it), so no separate declaration is needed.
- `.aw/records/plans/executed/20260925-carrierauth-01-vtkfq8-...ipd.md` is deliberately NOT declared, because E-07 leaves it byte-identical (it is a recorded transcript, KEEP). It appears in the citation preview only; do not add it to the fence, and do not edit it.
- No edit is made to `check_engine._check_identity_slots` or `_is_real_id6`. F-7 is a property of that rule, correctly documented in its own docstring; this plan works WITH it by adding E-06 rather than widening the rule, which the docstring explicitly warns against ("DO NOT 'fix' this by adding a declared-duplicate case here").

## Required tests / validation

Outcome tests only, per the maintainer's standing rule: `tests/test_walkthrough_id6.py` asserts the producer's returned name and file contents and the checker's findings (E-01), never source text or docstrings. E-06 is also an outcome test (it reads tracked RECORD files and their declared metadata, not production source). Live proof on the real tree (E-09), ruff, bare suite.

THE LOAD-BEARING EVIDENCE FOR THE DATA HALF IS E-06, NOT `aw check`. Measured in review: `check.id6-identity-slot` clears on a RENAME ALONE, so a clean `aw check all` is consistent with three walkthroughs that still declare no `- Id:`. E-09 (1) therefore proves the slot no longer collides; E-06 proves the identity was actually declared. Both are required and neither substitutes for the other.

## Spec / documentation sync

- `.aw/records/specs/implemented/20260817-2147-01-uniform-artifact-naming-grammar.spec.md` IS AMENDED (declared in Scope-Paths): its Section 2.1 Walkthrough row is the contract for walkthrough names, and ubac5n established that each type's adoption of id6-in-filename is recorded in its row; leaving it would make the implemented spec silent on a checker rule this plan adds.
- `.aw/records/walkthroughs/README.md`, `.aw/system/workflows/templates/agents-docs-walkthroughs-README.md`, `agent_workflows/artifact_naming.py` docstring.

## Open questions

### OQ-01: May the three D140 walkthroughs be renamed, given backlog mw0s1y's "DO NOT RENAME THESE RECORDS WITHOUT A MAINTAINER DECISION"?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. The maintainer's brief for this plan (2026-09-26) directs "re-id the 3 D140 walkthroughs", which is the decision `mw0s1y` asks for. The rename is by hand (E-05) because no verb re-ids a clustered name.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_walkthrough_id6.py -v` BEFORE E-02, showing (a) and (b) FAILED and (c) PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output with (a) PASSED, and the pasted first 8 lines of the file the test wrote, showing `- Id: <x>` and `- Target-Id: pl1abc` with `<x>` in the filename.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output with (b) and (c) PASSED and the (b) finding's detail line naming the walkthrough cutover; pasted `python3 -m pytest -o addopts="" tests/test_config.py -q` summary passing; pasted `grep -n walkthrough_id6 .aw/config/project.json agent_workflows/config.py`. PLUS the grandfathering MEASUREMENT, not an assertion: paste `config.resolve_cutover_date(Path('.'), "walkthrough_id6", compact=True)` (the stamped BOUNDARY, which is not the dict value) and the count of `check.name-nonconformant` from `check_names(Path('.'), "walkthroughs")`, which must be ZERO over all 24 existing walkthroughs. If the boundary resolved earlier than the newest tracked walkthrough (`20260918`), say so and stop rather than renaming grandfathered files.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff agent_workflows/artifact_naming.py` showing only the docstring paragraph changed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git status --porcelain .aw/records/walkthroughs/` showing three `R` renames, and for each new file the pasted metadata bullets with `- Id:` equal to the filename slot id6 and a `- Target-Id:` naming its plan. State explicitly that a clean `aw check` does NOT evidence the `- Id:` bullets (F-7); V-06 carries that.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new test FAILING at HEAD with its message naming the three D140 walkthroughs; paste it PASSING after E-05; then paste it FAILING again with one `- Id:` bullet temporarily deleted, restored afterwards. That third run is what proves the assertion can fail, which is the whole point of the item (a test that passes both before and after would be theatre here).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted preview hit list covering ALL EIGHT files with a KEEP/REWRITE label per hit (the count must be 8 files; if the preview returns a different set, paste it and reconcile before editing); pasted `git diff --stat` showing exactly the three documented plans changed; pasted `git diff --quiet` exit 0 for `t0jyb2`'s plan file, `vtkfq8`'s plan file, the `mw0s1y`/`e2j5w4` backlog files, and this plan.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted `grep -n walkthrough_id6` hits in the README, the template and the spec, and the pasted `aw specs note` output line.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: pasted `python3 -m agent_workflows check all --agent` diagnostics showing no `check.id6-identity-slot` entry, compared against HEAD's baseline of FIVE findings (3 slot + 1 `check.scope-drift` + 1 `check.system-layout-missing`), so the expected after-state is 2 and nothing new appeared; pasted `check walkthroughs --all` output; pasted `find <id6>` for each minted id6 (exactly one walkthrough each) and for `zpbx7o` (plan only), `y5od1h` and `4fodkt` (plan + its same-named review record, and NO walkthrough, with the D140 collision warning gone); pasted ruff output with no findings; the pasted final summary line of bare `python3 -m pytest` compared against the review-measured baseline `2584 passed, 2 skipped`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Walkthroughs adopt id6-in-filename going forward: the walkthrough writer mints the walkthrough's own id6 and links the plan by `Target-Id:`, a new `walkthrough_id6` cutover makes `aw check` require the clustered name for new walkthroughs, and the three walkthroughs that borrow their plan's id6 today are given their own (clearing the 3 `check.id6-identity-slot` findings and the data half of bug `mw0s1y`). The 11 older legacy walkthroughs stay as they are, grandfathered. Releases and roadmaps need nothing (already done).

THE ONE JUDGEMENT WORTH A MAINTAINER'S ATTENTION: this plan RENAMES three tracked records under `.aw/records/`, which backlog `mw0s1y` explicitly forbids "WITHOUT A MAINTAINER DECISION". OQ-01 treats the brief's instruction ("re-id the 3 D140 walkthroughs") as that decision. Review accepted that reading and flags it here rather than blocking, because the instruction is specific and `mw0s1y` asks for exactly this; if the maintainer intended something narrower, E-05/E-07 are the items to change.

WHAT REVIEW CHANGED. Three verification defects, each measured: (1) E-09's `check.id6-identity-slot` proof is satisfied by RENAMING ALONE, so the `- Id:` half of the repair had no assertion that could fail (new E-06 closes it); (2) E-09's `aw find` assertion was FALSE for `y5od1h`/`4fodkt`, because a review record legitimately shares the plan's name, so a correct outcome would have read as a failure; (3) E-07's citation census named 5 of 8 citing files, and one of the missing three (`vtkfq8`) is a recorded transcript that a wholesale rewrite would have corrupted. Also corrected: the HEAD finding baseline (5, not 9) and E-03's cutover rationale, which described the registry value as an enforcement boundary the code says it is not.

SCOPE FENCE, a declaration for reconciliation: the `- Scope-Paths:` list. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize --scope-reason`).

HARD MUST: paste the ACTUAL output for every `V-*`; never claim a command passed without running it. Run the suite BARE as `python3 -m pytest` (do not add `-n0`, a second `-q`, or `-p no:randomly`). A CLEAN `aw check all` IS NOT SUFFICIENT EVIDENCE that the three walkthroughs were repaired: it clears on a rename alone (F-7), so V-06's three-run sequence is the load-bearing proof and must show the test FAILING with a bullet removed.

GENUINE STOP CONDITIONS: (1) if V-03's measured cutover boundary lands at or before `20260918`, stop rather than renaming grandfathered walkthroughs; (2) if E-07's preview returns a citing-file set other than the eight named, reconcile it before applying any edit, and never call `apply_reference_rewrites` on the whole list (it would rewrite the recorded transcripts in `t0jyb2` and `vtkfq8`).

Commit only the Scope-Paths files via `aw commit nrqo90 -- <paths>`, never `git add -A`, never push. The plan reaches `executed/` only after every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` conforms, via `aw ipd finalize` (or the runner). After it executes, the maintainer or executor closes `mw0s1y` with `aw backlog set done mw0s1y --evidence <this executed plan path>`; it carries `Blocks-Release: next`, and because this plan declares `- From-Backlog: f2u4l0` (not `mw0s1y`) the HANDOFF escape does NOT apply to it, so the SATISFIED escape via `--evidence` is the required path. Verified in review: `evaluate_blocking_close` refuses that close today (the evidence path does not exist until the plan is in `executed/`) and accepts it once the cited artifact resolves, so the close must happen AFTER finalize, never before. Then graduate `f2u4l0`. Backlog `e2j5w4` is NOT closed by this plan: its detection defect is already fixed in code, but the item's status is a separate record this plan has no authority over.
