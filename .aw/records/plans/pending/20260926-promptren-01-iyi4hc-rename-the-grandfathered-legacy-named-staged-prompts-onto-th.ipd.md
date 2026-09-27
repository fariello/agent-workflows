# IPD: Rename the grandfathered legacy-named staged prompts onto the id6-clustered grammar

- Date: 2026-09-26
- Kind: child
- Concern: 16 of the 17 tracked staged prompts still carry the grandfathered legacy `YYYYMMDD-HHMM-NN-<slug>.prompt.md` name and so have no id6: `aw find` cannot resolve them and the research they produced cannot cite them by a stable handle.
- Scope: IN: give the 8 comment-less legacy prompts a leading metadata comment, then convert each legacy prompt with `aw rename prompts <name> --to-id6 --apply`, reviewing every planned citation rewrite and reverting those that would falsify history; fix the one citation outside every scan root. OUT: lowering the prompt_id6 cutover, the prompt-library tree, regenerating the stale `STATUS.md`, any change to tooling.
- Scope-Paths: .aw/records/prompts, DECISIONS.md, .aw/system/workflows/handoff/handoff.md, .aw/records/plans/executed/20260723-instsafe-05-kemhdg-external-install-and-skills-delivery-research-spec.ipd.md, .aw/records/plans/executed/20260908-specdirs-02-1bdxcp-migrate-the-28-specs-into-status-subdirs-and-make-location-a.ipd.md, .aw/records/plans/executed/20260829-lanename-01-j4v6ga-finish-the-local-untracked-lane-rename-in-agent-facing-prose.ipd.md, .aw/records/plans/executed/20260727-untrackwf-00-wn2jto-untrack-workflow-artifacts-orchestrator.ipd.md, .aw/records/plans/executed/20260920-promptid6-01-ubac5n-mint-an-id6-for-staged-prompts-and-migrate-the-prompts-tree.ipd.md, .aw/records/plans/executed/20260829-promptmint-01-jxqdcw-aw-prompts-new-mints-a-conforming-staged-prompt-and-the-rese.ipd.md, .aw/records/plans/executed/20260924-promptadopt-01-dx0u4s-make-staged-prompts-a-full-artifact-organization-and-attenti.ipd.md, .aw/records/plans/executed/20260718-purge-personal-00-3visab-purge-personal-path-and-identity-leaks.ipd.md, .aw/records/plans/executed/20260810-awphysical-00-rma3j4-physical-aw-hierarchy-and-migration-orchestrator.ipd.md, .aw/records/plans/executed/20260810-awphysical-01-cwjnj0-physical-root-ownership-and-git-policy-contract.ipd.md, .aw/records/plans/executed/20260810-awphysical-02-sywony-policy-schema-and-deterministic-context-resolution.ipd.md, .aw/records/plans/executed/20260810-awphysical-04-ru5pmd-canonical-system-installation-and-source-checkout-mode.ipd.md, .aw/records/plans/executed/20260810-awphysical-05-1e9ggw-private-companion-attachment-and-durability.ipd.md, .aw/records/plans/executed/20260810-awphysical-06-fcgala-migration-inventory-and-mapping-tools.ipd.md, .aw/records/plans/executed/20260810-awphysical-07-nhv0qm-transactional-migration-rollback-and-resume.ipd.md, .aw/records/plans/executed/20260810-awphysical-08-mb9xn2-record-producers-and-legacy-reference-cutover.ipd.md, .aw/records/plans/executed/20260810-awphysical-09-2e2jrw-host-adapters-and-clean-delta-integration.ipd.md, .aw/records/plans/executed/20260810-awphysical-10-n3fz8b-post-migration-independent-audit.ipd.md, .aw/records/plans/executed/20260810-awphysical-11-g5zl1u-agent-workflows-source-repository-self-migration.ipd.md, .aw/records/plans/executed/20260810-awphysical-12-pszk6x-documentation-release-and-end-to-end-acceptance.ipd.md, .aw/records/reviews/20260920-promptid6-01-ubac5n-mint-an-id6-for-staged-prompts-and-migrate-the-prompts-tree.review.md, .aw/records/plans/not-executed/20260926-promptlint-01-mi4s9f-implement-aw-prompts-check-the-prompt-purity-lint-of-approve.ipd.md
- Item-Dependencies: executed:5xzld0
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: vfmklc
- Set: promptren
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: iyi4hc
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 all FIXED. Two of four validation legs were unusable at HEAD: PR-001 (HIGH) E-06 demanded zero findings from aw check prompts --all, which always emits one info check.collisions-not-checked by design, and its check all baseline quoted 9 phantom findings where 5 exist; PR-002 (HIGH) E-01/E-06 invoked aw prompts check, a verb that does not exist whose plan mi4s9f is not-executed and whose spec prompt-purity-lint is superseded. PR-003 re-pointed the 8-prompt DECISION off that superseded spec. Re-ran the whole migration in post-5xzld0 simulation: PR-004/PR-005 found the dominant edit class is twelve identical awphysical history-line citations, all UNFENCED, so fence masking protects almost nothing here; PR-006 measured that the RETIRED banner survives E-02's line-1 insertion (near miss, now a required V-02 proof); PR-007 corrected that --no-refs drops ALL rewrites and that the one refusing prompt's KEEP set is empty; PR-008 surfaced that handoff.md ships in the wheel; PR-009 fixed a two-way scope-fence error. Findings and decisions D-1..D-6 in .aw/records/reviews/20260926-promptren-01-iyi4hc-rename-the-grandfathered-legacy-named-staged-prompts-onto-th.review.md
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog vfmklc: add metadata comments to the 8 comment-less prompts, then convert the 16 legacy prompts with aw rename --to-id6, reviewing each rewrite.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give every grandfathered legacy-named staged prompt a stable id6 in both its filename and its metadata comment, using the shipped converter `aw rename prompts <name> --to-id6 --apply`, so each is resolvable by `aw find <id6>` and citable from the research it produced, without rewriting any citation that actually names a different artifact or records history.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: preconditions and baseline

- [ ] E-01 Confirm the dependency landed and capture the baseline. Verify plan `5xzld0` is in `.aw/records/plans/executed/` (its shared-legacy-prefix skip, short-handle mapping and fenced-code masking are what keep this migration from corrupting citations, see F-3). Save to `/tmp/opencode/promptren-baseline/`: `git ls-files '.aw/records/prompts/*.prompt.md'`, `python3 -m agent_workflows check prompts --all --agent`, and `python3 -m agent_workflows check all --agent`. Re-derive the legacy population: names matching `^\d{8}-\d{4}-\d{2}-` among tracked `.prompt.md` files (16 at authoring).

  DO NOT run `aw prompts check`: it does not exist and never will (see E-06; plan `mi4s9f` is `not-executed`, spec `prompt-purity-lint` is `superseded`). The authored conditional "if `5xzld0`'s sibling `mi4s9f` has landed" is dead and was removed at review (PR-002).
  - Depends on: none
  - Expected outcome: 5xzld0 executed; baseline files written; the population list recorded with its count; the two baseline finding sets recorded SEPARATELY (they differ, see E-06).
  - Execution state: pending

- [ ] E-02 Give each legacy prompt that has NO leading `<!-- aw-prompt: ... -->` comment one, BEFORE renaming, so the converter writes the id6 into the file as well as the filename (`prompts.inject_metadata_id6` only writes into an existing comment and deliberately never mints one). Measured at authoring: 8 such files, the 6 oldest `executed/` prompts (`20260722-2317-01`, `20260725-0957-01`, `20260725-2341-01`, `20260727-0655-01`, `20260730-2214-01`, `20260803-0829-01`) and the 2 `superseded/` ones (`20260717-1450-01`, `20260717-1950-01`), whose first line is the AGENTS.md-mandated `RETIRED YYYY-MM-DD: ...` header. Generate each line with `prompts.render_metadata_comment(kind=..., status=<its bucket>, created=<filename date as YYYY-MM-DD>)` (Author/Targets omitted: the renderer omits an unknown field rather than guessing) and insert it as line 1, above any `RETIRED` header, which stays as the first visible line. Kind rule: `research` when the body asks for a researched report, `session-handoff` for the two superseded session files, else `run-once`; record the chosen Kind per file. Kind MUST be one of `prompts.PROMPT_KINDS` = `("run-once", "research", "session-handoff")`; nothing validates the value, so an off-list Kind would be written silently. Do not change any other byte.

  THE `RETIRED` BANNER SURVIVES THE INSERTION, verified at review rather than assumed (PR-006). The banner is READ, not decorative: `artifact_audit._has_retired_banner` decides `CLASS_RETIRED` from it, and moving it off line 1 could have demoted both superseded prompts to `unknown`. Measured on a copy of `20260717-1950-01` with the rendered comment inserted as line 1: `_has_retired_banner` still returns True, because `_RETIRED_BANNER_RE` is multi-line-anchored (`(?m)^[ \t]*(?:<!--[ \t]*)?(?:>[ \t]*)?\**RETIRED\b`) and reads a 4096-byte header, not line 1. Re-confirm this after the edit anyway (V-02), because it is the one silent-damage path in this item.
  - Depends on: E-01
  - Expected outcome: every legacy prompt now opens with exactly one metadata comment; `aw check prompts --all` shows no finding beyond the permanent `check.collisions-not-checked` (pre-cutover filenames do not require the comment per `check_engine._prompt_requires_id6`, and `check.prompt-status-mismatch` passes because Status equals the bucket); both `RETIRED` banners still detected.
  - Execution state: pending

### Task group 2: the rename, one prompt at a time

- [ ] E-03 For EACH legacy prompt, oldest first: run the PREVIEW `python3 -m agent_workflows rename prompts <legacy-name> --to-id6`, save it under `/tmp/opencode/promptren-previews/<legacy-prefix>.txt`, and classify every `would rewrite` line by opening the cited occurrence: KEEP when the text names this prompt (its bare name, its current `.aw/records/prompts/...` path, or its short handle used to mean this prompt); REVERT-AFTER when the occurrence (a) sits inside a historical `.agents/...` path (it records where the file was, and a rewritten path would name a location that never existed), (b) names a DIFFERENT artifact that once shared the legacy prefix, (c) is a quoted command transcript or a measurement table, including this Set's own plan files, or (d) is in this plan file. Known at authoring, to be re-confirmed: `20260722-2317-01` in `DECISIONS.md` and executed plan `kemhdg` names the RESEARCH finding once filed as `.agents/docs/research/20260722-2317-01-...` (now research `0jl8pv`), not this prompt (b); `20260717-1950-01` in executed plan `3visab` sits inside `.agents/plans/pending/20260717-1950-01...` (a); `20260727-0655-01` in executed plan `wn2jto` sits inside `.agents/prompts/pending/...` and the preview prints `WARNING: full-path citation ... cannot be auto-rewritten`, so `--apply` refuses for that one (see E-04). Then apply with `python3 -m agent_workflows rename prompts <legacy-name> --to-id6 --apply --no-commit`, and immediately restore every REVERT-AFTER occurrence to its pre-rename text by hand, verified against the saved preview.
  RE-MEASURED AT REVIEW (PR-004), SIMULATING POST-`5xzld0` SEMANTICS (shared-prefix skip + short-handle mapping + fence masking + reviews/tests roots). The external citer set is 20 files and one class of it dominates: TWELVE of the awphysical executed plans (Orders 00, 01, 02, 04-12) each carry exactly ONE identical `legacy x1` hit of `20260810-1544-01`, in the SAME sentence of a `/plan-review-long` history line ("...appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS..."). That is a HISTORY LINE recording what a review did, so it is rule (c) and REVERT-AFTER for all twelve; classify them as one batch with one justification rather than twelve separate judgements, and paste the twelve `git diff` confirmations. The 13th `20260810-1544-01` citer, executed plan `jxqdcw`, carries `full x1 + whole x1 + legacy x2` in E-item prose that names the FILE; those are KEEP.

  ALSO RE-MEASURED, and NOT in the authored "known" list: `20260808-1948-01` is cited by `not-executed/` plan `mi4s9f` (`full x2`), which is NOT in `Scope-Paths` (see the Scope check). `20260829-1520-01` is cited by review record `ubac5n.review.md` (`full x1 + whole x1`), which IS declared. `20260725-0957-01` has ZERO external citers once `5xzld0`'s shared-prefix skip lands (it is the ONE shared prefix in the corpus), so its only rewrites are into this Set's own two plan files, all rule (d)/(c).

  THE FENCE-MASKING PREMISE IS ONLY PARTLY TRUE, so do not lean on it (PR-005): every one of the citations above sits OUTSIDE a fence, verified line by line with `ipd_lint._FENCE_RE` semantics, so fence masking protects almost nothing in THIS migration. The one place it does bite is `5xzld0`'s own review record, whose `20260722-2317-01` hits are all inside fences (and whose final fence is UNCLOSED, so masking runs to end of file). Classify by READING the occurrence, never by assuming a transcript is fenced.
  - Depends on: E-02
  - Expected outcome: each prompt renamed to `YYYYMMDD-<id6>-01-<id6>-<slug>.prompt.md` with `Id: <id6>` in its comment; only KEEP rewrites survive.
  - Execution state: pending

- [ ] E-04 Handle the prompts whose `--apply` refuses on an un-auto-rewritable full-path citation. RE-MEASURED AT REVIEW by calling `artifact_rename.find_unrewritable_path_citations` directly for all 16 prompts: exactly ONE prompt trips it, `20260727-0655-01`, on `.agents/prompts/pending/20260727-0655-01-untrack-workflow-artifacts.prompt.md` in a `## Workflow history` line of executed plan `wn2jto` (plus two occurrences in THIS plan file). The citation is historical (rule (a)) and must NOT change. The refusal fires because the cited directory `agents/prompts/pending` neither is a suffix of nor has as a suffix the real dir `.aw/records/prompts/executed`; `run_rename_generic` prints `error: full-path citation ... cannot auto-rewrite` and returns 2 BEFORE renaming anything.

  `--no-refs` IS A BLUNT INSTRUMENT AND THE PLAN MUST SAY SO (PR-007): it suppresses EVERY citation rewrite for that prompt, not only the refused one, so after `--no-refs --apply --no-commit` you own the full KEEP set by hand. For `20260727-0655-01` the measured KEEP set is EMPTY: its only external citer is `wn2jto`, whose single hit IS the historical `.agents/` path (rule (a)), and its remaining hits are in this plan file (rule (d)). So the correct outcome is: rename with `--no-refs`, change no citation at all, and say that explicitly rather than reporting "applied KEEP rewrites by hand" for a set of zero.

  The refusal set is a LIVE property: re-derive it at execution by reading each preview's `WARNING: full-path citation` lines rather than trusting the count one.
  - Depends on: E-03
  - Expected outcome: every legacy prompt converted; no historical path altered; each `--no-refs` prompt's KEEP set stated (empty is a valid, reportable answer).
  - Execution state: pending

- [ ] E-05 Fix the citations the reference scan cannot reach, then sweep for survivors.

  THE ONE OUT-OF-SCAN-ROOT CITATION: `.aw/system/workflows/handoff/handoff.md` cites `.aw/records/prompts/superseded/20260717-1950-01-session-handoff-resume-here.prompt.md` as its "Structural reference", and `.aw/system/` is in no scan root, so the rename leaves it dangling. Update it to the new name by hand. RE-VERIFIED AT REVIEW that this is the ONLY such file: `git grep -l` for all 16 legacy prefixes across `agent_workflows/`, `.aw/system/`, `docs/` and the root `*.md` set, excluding `.aw/records`, returns this file and nothing else. `.opencode/commands/handoff.md` and `.claude/commands/handoff.md` are thin `Read and execute @...` shims that do NOT name the prompt, so they need no edit.

  `.aw/system/` IS SHIPPED IN THE WHEEL, so this is not merely a records edit: `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` maps `".aw/system" = "agent_workflows/_data/.aw/system"`, and the sdist `include` list carries `/.aw/system`. Editing the workflow body therefore changes packaged content. The edit is still correct (a dangling path in a shipped workflow is worse than a changed one), and no test pins this line (`git grep` for the cited name across `tests/` returns nothing), but declare it as such rather than as an inert record touch.

  THEN SWEEP: `git grep -n <each old legacy name>` over the whole tracked tree, excluding `.aw/state`, `.aw/worktrees`, `opencode-recovery`, and classify every surviving hit KEEP / REVERT-AFTER (rule letter) / generated-manifest.

  `STATUS.md` IS LEFT STALE DELIBERATELY, and it is worse than stale in a way the plan must not claim away (corrected at review, PR-003): `artifact_refs._SKIP_NAMES` is `{'INDEX.md','STATUS.md','README.md'}`, so `.aw/records/plans/STATUS.md` is never rewritten, and it already carries two names the rename will break plus two that were ALREADY wrong before this plan (line 193 cites `...20260722-2317-01-token-efficient-managed-sections-research-prompt.md` and line 208 cites `...20260717-1950-01-session-handoff-resume-here.md`, both missing the `.prompt` facet, i.e. dangling at HEAD). It was last generated 2026-08-17 and is stale on far more than prompt names. Do NOT regenerate it here and do NOT count its hits as findings; name them in V-05 as generated-manifest so a reader can tell them from a missed live citation.
  - Depends on: E-04
  - Expected outcome: `handoff.md` cites the new name; no live citation of an old prompt name remains except REVERT-AFTER occurrences and the generated `STATUS.md` hits, each labelled.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 Verify: `python3 -m agent_workflows check prompts --all` reports NO finding beyond its OWN E-01 baseline, and `python3 -m agent_workflows check all` reports NO finding beyond the E-01 baseline. Re-derive BOTH baselines at execution; neither is clean, and the two are different counts.

  WHAT "CLEAN" ACTUALLY MEANS HERE, corrected at review (PR-001). `check prompts --all` does NOT report zero: it emits one permanent `info`-severity `check.collisions-not-checked` finding at location `<collisions>`, because `check_engine.check_types` deliberately qualifies every per-type run rather than rendering an unqualified clean (measured at HEAD: `"outcome":"conforms","findings":1`, exit 0, that one diagnostic). So the bar is "no finding OTHER than `check.collisions-not-checked`", and demanding zero would make a conforming run look failed. `check all` at HEAD 2026-09-27 reports 5 findings (1 `check.scope-drift` on plan `olkeju`, 3 `check.id6-identity-slot` on walkthroughs, 1 `check.system-layout-missing`), NOT the 9 this item claimed at authoring; the authored list named rules (`check.ipd-uncarried-obligation`) that no longer fire, which is exactly why the count is re-derived rather than trusted.

  Then confirm `python3 -m agent_workflows find <id6>` resolves each new id6 to exactly one prompt.

  `aw prompts check` DOES NOT EXIST AND WILL NOT (PR-002): `aw prompts` accepts only `new` (`agent-workflows prompts: error: argument prompts_command: invalid choice: 'check'`), its plan `mi4s9f` is in `not-executed/` and its spec `prompt-purity-lint` is `superseded`, both retired 2026-09-26 by maintainer decision against any prompt-purity gate. Do NOT wait for it and do NOT report its absence as a gap.
  - Depends on: E-05
  - Expected outcome: `check prompts --all` shows only `check.collisions-not-checked`; `check all` matches the E-01 baseline line for line; every new id6 resolves to exactly one prompt.
  - Execution state: pending

- [ ] E-07 Run the bare suite `python3 -m pytest` (the rename touches only records and one shipped workflow body, but `tests/test_history_order.py` reads executed plans and the suite is the regression net for any path a test hard-codes).
  - Depends on: E-06
  - Expected outcome: suite passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw rename prompts <name> --to-id6` mints via `artifact_core.mint_id6`, writes the id6 into the one metadata comment via `prompts.inject_metadata_id6`, rewrites citations via `artifact_refs.plan_reference_rewrites`, and fails loud on an un-auto-rewritable full-path citation (`artifact_rename.find_unrewritable_path_citations`).
- `check_engine.validate_prompt_content` flags a missing comment only for a filename dated at/after `cutovers.prompt_id6` (2026-09-21); all 16 legacy prompts are pre-cutover, so the comment is not REQUIRED, but `check.prompt-id-mismatch` compares a comment `Id:` with the filename id6 and `check.prompt-status-mismatch` compares `Status:` with the bucket, so a comment makes the content checkable.
- `prompts_index` reads the id from the comment first and falls back to the filename id6.
- Editing an executed plan's text is permitted only as reference rewriting and must be declared (backlog `vfmklc`); no commit may otherwise add to an executed plan.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Re-verified at HEAD 2026-09-26:

| Id | Evidence | Finding |
|---|---|---|
| F-1 | `git ls-files '.aw/records/prompts/*.prompt.md'` = 17; names matching the legacy `YYYYMMDD-HHMM-NN-` prefix = 16; only `20260920-plainlang-01-ng0ga4-...` is clustered | The brief's "15 legacy of 17 (2 already clustered)" is off by one: 16 legacy, 1 clustered. |
| F-2 | `prompts.has_metadata_comment` false for 8 files: the 6 oldest `executed/` prompts and the 2 `superseded/` ones | The brief's (and backlog's) "6 have no metadata comment" counts only the executed ones; the 2 superseded prompts, which open with a `RETIRED` header, have none either. |
| F-3 | Live previews at HEAD, e.g. `rename prompts 20260725-0957-01-external-delivery-host-probe.prompt.md --to-id6` plans `rewrite 1x '20260725-0957-01' -> '20260725-<id6>-01-<id6>-external-delivery-host-probe.prompt'` in executed plan `1bdxcp`, whose occurrence names the deferred SPEC sharing that prefix; the preview also plans 7 rewrites into pending plan `5xzld0` itself | Without `5xzld0` this migration would cross-contaminate a spec citation and expand short handles to full stems, which is why `5xzld0` is a hard dependency. |
| F-4 | `20260722-2317-01` is cited in `DECISIONS.md` and executed plan `kemhdg` as "research `20260722-2317-01`"; `git log --all --name-only` shows `.agents/docs/research/20260722-2317-01-token-efficient-managed-sections-in-agent-instruction-files.gpt-56.research.finding.md` once existed | A legacy prefix can be ambiguous HISTORICALLY even when unique on disk today, so `5xzld0`'s current-tree uniqueness check cannot see it; E-03's per-occurrence classification is the guard. |
| F-5 | `.aw/system/workflows/handoff/handoff.md` cites the superseded `20260717-1950-01-...prompt.md` by full path; `.aw/system/` is not a scan root | One live citation the tool cannot reach; E-05 fixes it by hand. |
| F-6 | `rename prompts 20260727-0655-01-... --to-id6` preview prints `WARNING: full-path citation '.agents/prompts/pending/20260727-0655-01-untrack-workflow-artifacts.prompt.md' in .../20260727-untrackwf-00-wn2jto-...ipd.md names a different directory` | `--apply` refuses for that prompt; E-04. |
| F-7 | Citing files seen in the previews (to be re-derived at execution): `DECISIONS.md`; executed plans `kemhdg`, `1bdxcp`, `j4v6ga`, `wn2jto`, `ubac5n`, `jxqdcw`, `dx0u4s`, `3visab`, and awphysical Orders 00, 01, 02, 04-12; review `ubac5n`; prompt `20260810-1530-01` | These are the executed-plan edits declared in Scope-Paths. |
| F-8 (added at review, PR-001) | `python3 -m agent_workflows check prompts --all --agent` at HEAD emits `"outcome":"conforms","findings":1` with the single diagnostic `check.collisions-not-checked` at location `<collisions>`, exit 0. `check_engine.check_types`'s docstring states the design: a per-type run does not do the cross-tree collision scan, so it emits ONE `info` finding rather than "rendering an unqualified `CONFORMS / errors 0 warnings 0`" | E-06's authored bar of "zero findings" from `check prompts --all` is UNREACHABLE BY DESIGN. The bar is "nothing beyond `check.collisions-not-checked`". Separately, `check all` reports 5 findings at HEAD (`check.scope-drift` on plan `olkeju`; 3x `check.id6-identity-slot` on walkthroughs; `check.system-layout-missing`), not the 9 the item claimed, and NONE of the authored rule names (`check.ipd-uncarried-obligation`) still fire. |
| F-9 (added at review, PR-002) | `python3 -m agent_workflows prompts check` returns `error: argument prompts_command: invalid choice: 'check' (choose from 'new')`. Its implementing plan `mi4s9f` is in `.aw/records/plans/not-executed/` with the banner "maintainer decided against any prompt-purity gate ... no replacement", and its spec `prompt-purity-lint` is in `.aw/records/specs/superseded/` with the agreeing history note | The verb does not exist and is not coming. E-01's conditional and E-06's "if available" clause were dead and are removed. NOTE the knock-on: F-2 and the 8-prompt DECISION both cite `prompt-purity-lint` P4 as live authority for the metadata comment; that spec is SUPERSEDED, so the comment convention now rests on `.aw/records/prompts/README.md` and `prompts.render_metadata_comment`'s own docstring, which is sufficient but is a different citation. |
| F-10 (added at review, PR-003) | `artifact_refs._SKIP_NAMES` is `{'INDEX.md','STATUS.md','README.md'}`. `.aw/records/plans/STATUS.md` line 193 cites `.aw/records/prompts/executed/20260722-2317-01-token-efficient-managed-sections-research-prompt.md` and line 208 cites `.aw/records/prompts/superseded/20260717-1950-01-session-handoff-resume-here.md`, BOTH missing the `.prompt` facet, so both are dangling at HEAD before this plan runs. Lines 196 and 198 cite two names this rename will break | The deferral of `STATUS.md` is right, but "stale" understates it: two of its four prompt citations are already WRONG. The deferral rationale is amended to say so, so a later reader does not attribute the pre-existing breakage to this migration. |
| F-11 (added at review, PR-008) | `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` maps `".aw/system" = "agent_workflows/_data/.aw/system"`, and the sdist `include` list carries `/.aw/system` | The `handoff.md` edit (F-5) changes SHIPPED PACKAGE CONTENT, not just a record. No test pins the cited line (`git grep` of the cited name across `tests/` is empty) and the edit is still correct, but E-05 now declares it as a packaged-content change. |
| F-12 (added at review, PR-009) | Simulating post-`5xzld0` rewriting over the 16 prompts: `20260808-1948-01` is cited `full x2 + whole x2` by `.aw/records/plans/not-executed/20260926-promptlint-01-mi4s9f-...ipd.md`, which is NOT in `- Scope-Paths:` | One citing file is undeclared, so the finalize scope reconciliation would demand a `--scope-reason` for an edit the plan in fact intends. Added to `Scope-Paths` at review. Conversely `.aw/records/plans/executed/20260908-specdirs-02-1bdxcp-...ipd.md` is declared but receives NO edit once the shared-prefix skip lands (its only hit was the `20260725-0957-01` cross-type contamination that `5xzld0` E-05 exists to stop), so it needs a `--scope-ack`, not a rewrite. |
| F-13 (added at review, PR-004 and PR-005) | Reading each occurrence's fence state with `ipd_lint._FENCE_RE` semantics: every citation in the external citer set is OUTSIDE a fence. The only fenced hits are in `5xzld0`'s own review record, whose last fence is UNCLOSED (fence toggles at lines 22, 32, 34, 39, 42 leaving `inside=True` at EOF) | Fence masking protects almost NOTHING in this migration, contrary to the framing in F-3 and the Goal. The twelve awphysical history-line citations and the `DECISIONS.md`/`kemhdg` research citations are all unfenced prose, so per-occurrence reading (E-03) is the ONLY guard for them. |

DECISION ON THE 8 COMMENT-LESS PROMPTS: add a metadata comment first (E-02). Reasons: (1) without it the id6 lives in the FILENAME ONLY, so `validate_prompt_content` has no `Id:` to compare and cannot detect a later filename/identity divergence, which is the whole point of the conversion; (2) `artifact_rename._read_existing_id6` reads a prompt's id from its comment, so a comment-less file has no in-file identity for any later tool to reuse; (3) the comment is invisible when pasted, so it costs the prompt nothing; (4) it also makes the bucket-vs-Status check apply. The alternative, filename-only, is check-clean (pre-cutover names do not require the comment) but leaves 8 prompts with an identity no content check can see.

AUTHORITY CORRECTION FOR REASON (3), applied at review (F-9): the plan cited spec `prompt-purity-lint` P4 as the live rule permitting exactly one leading HTML comment. That spec is now in `.aw/records/specs/superseded/` (retired 2026-09-26 with the maintainer's decision against a purity gate), so it is HISTORY, not a contract to cite as current authority. The convention is unchanged and is still documented where it is enforced-in-practice: `.aw/records/prompts/README.md` documents the `<!-- aw-prompt: ... -->` line and the `--to-id6` converter, and `prompts.render_metadata_comment`'s docstring records why the metadata is a comment rather than front matter. Reason (3) stands on those.

## Proposed changes (ordered, validatable)

1. Confirm `5xzld0` landed; baseline (E-01).
2. Metadata comment for the 8 comment-less prompts (E-02).
3. Preview, classify, apply, restore per prompt (E-03), with the `--no-refs` path for fail-loud ones (E-04).
4. Fix the out-of-scan-root citation and sweep for survivors (E-05).
5. `aw check prompts --all`, `aw check all`, `aw find`, suite (E-06, E-07). NOT `aw prompts check`: it does not exist (F-9).

## Deferred / out of scope (with reason)

- Lowering `cutovers.prompt_id6` / `check_engine.PROMPT_ID6_CUTOVER_DATE` now that no legacy prompt remains.
  - Carrier-Declined: grandfathering stays harmless with zero legacy prompts, and the per-repo cutover is stamped config for every installed repo, so moving it is a policy change for the maintainer, not a residue of this migration.
- Regenerating the stale tracked `.aw/records/plans/STATUS.md`.
  - Carrier-Declined: it is a generated view, skipped by the reference matcher by design (`artifact_refs._SKIP_NAMES`), last regenerated 2026-08-17 and stale on far more than prompt names; regenerating it is unrelated to this rename. AMENDED AT REVIEW (F-10): "stale" understates it. Two of its four prompt citations are ALREADY DANGLING at HEAD, both missing the `.prompt` facet (`...20260722-2317-01-token-efficient-managed-sections-research-prompt.md` and `...20260717-1950-01-session-handoff-resume-here.md`), and this rename will break two more. The decline stands, but the executor MUST NOT report those four hits as this migration's residue.

## Scope check

- Over-scope: `.aw/records/plans/executed/20260908-specdirs-02-1bdxcp-...ipd.md` is DECLARED but receives no edit once `5xzld0`'s shared-prefix skip lands (F-12): its only hit was the `20260725-0957-01` cross-type contamination that skip exists to prevent. Left declared deliberately and acknowledged at finalize with `--scope-ack`, because dropping it would mean re-deriving it if the skip behaves differently than simulated.
- Under-scope, both fixed at review:
  - the handoff workflow body (F-5) is outside every scan root and is included by hand, and it is SHIPPED PACKAGE CONTENT (F-11), not an inert record;
  - `.aw/records/plans/not-executed/20260926-promptlint-01-mi4s9f-...ipd.md` cites `20260808-1948-01` twice and was NOT declared (F-12); added to `- Scope-Paths:`.

## Required tests / validation

No new test file: this is a data migration performed by already-tested verbs. The converter's coverage lives in `tests/test_spec_id6_filenames.py` (which drives `rename ... --to-id6` preview/apply, idempotence, and the fail-loud path) and `tests/test_prompts_new.py`; `5xzld0` ADDS `tests/test_artifact_refs_rewrite.py`, which does not exist at HEAD and arrives with that dependency, so cite it as inherited rather than as present.

Validation is outcome evidence on the real tree: `aw check prompts --all` showing nothing beyond `check.collisions-not-checked` (NOT "clean": F-8), `aw check all` no worse than the V-01 baseline compared line by line, `aw find <id6>` resolving each prompt, and the bare suite, per the maintainer's outcome-only rule.

## Spec / documentation sync

NO SPEC IS AMENDED, and `- Scope-Paths:` declares no `.spec.md` file, deliberately. Re-checked at review against the whole `.aw/records/specs/` tree: no spec enumerates prompt filenames. The one spec that governed prompt CONTENT, `prompt-purity-lint`, is `superseded` (F-9) and is not amended here: amending a retired spec to reflect a records migration would resurrect a contract the maintainer retired.

ONE SPEC CITATION IS STALE IN THIS PLAN AND WAS CORRECTED RATHER THAN CARRIED: the 8-prompt DECISION cited `prompt-purity-lint` P4 as live authority; that citation now names it as history and rests the convention on `.aw/records/prompts/README.md` and `prompts.render_metadata_comment` instead. `.aw/records/specs/superseded/20260808-1958-01-prompt-purity-lint.spec.md` itself cites `20260808-1948-01` (its A4 acceptance case) but as a `.agents/prompts/pending/` HISTORICAL path, which the reference matcher will not auto-rewrite and which must stay as-is (rule (a)).

`.aw/records/prompts/README.md` already documents the clustered grammar and the `--to-id6` converter; its sentence "Legacy ... names ... remain valid and are grandfathered" stays true (the grandfather clause is not removed, only emptied of subjects). `.aw/system/workflows/handoff/handoff.md` citation fixed (E-05), and that file is SHIPPED IN THE WHEEL (F-11).

## Open questions

### OQ-01: Rename one prompt at a time or in one batch?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: One at a time (E-03). `aw rename` takes one selector per call, and a prompt renamed earlier can be a CITER of a later one (prompt `20260810-1530-01` cites `20260810-1544-01`), so per-prompt previews are the only way to review each rewrite set against the tree it will actually edit. One commit at the end is fine.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `ls .aw/records/plans/executed/ | grep 5xzld0` showing the plan; `ls /tmp/opencode/promptren-baseline/`; the pasted legacy-population list with its count; and the TWO baseline finding sets pasted SEPARATELY and in full (every `rule`+`location` pair from `check prompts --all --agent`, and every pair from `check all --agent`), not merely counts, because V-06 compares them line by line and a count cannot detect a swap.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each of the 8 files, the pasted `head -2` after the edit showing the new `<!-- aw-prompt: Kind: ... | Status: <bucket> | Created: ... -->` line 1 (and the `RETIRED` header as line 2 for the superseded pair), plus pasted `git diff --stat` showing exactly one inserted line per file, and the chosen Kind per file WITH its membership in `prompts.PROMPT_KINDS` stated. PLUS the banner proof (E-02's `RETIRED` paragraph, review PR-006): paste, for BOTH superseded prompts, the output of `python3 -c "from pathlib import Path; from agent_workflows import artifact_audit as aa; print(aa._has_retired_banner(Path('<file>')))"` returning `True` AFTER the insertion, so a demoted retirement class cannot pass unnoticed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `ls /tmp/opencode/promptren-previews/` with one file per prompt; a pasted classification table (prompt, citing file, occurrence, KEEP or REVERT-AFTER with rule letter); and for every REVERT-AFTER row the pasted `git diff <file>` showing that occurrence unchanged relative to HEAD. The twelve awphysical history-line occurrences (E-03) may share ONE table row plus one justification, but each still needs its own pasted `git diff` line proving it is unchanged; a batch claim with no per-file diff does not satisfy this item. Also state, for each prompt, whether its external citer count matched the review's simulation or differed, since a DIFFERENCE means the post-`5xzld0` behavior is not what this plan assumed and is worth reporting.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `--apply` refusal output for each fail-loud prompt (including its exit code), the pasted `--no-refs --apply` output, and EITHER the `git diff` of its KEEP citations applied by hand OR the explicit statement that its KEEP set is EMPTY with the pasted `git diff --stat` showing only the rename. For the measured case `20260727-0655-01` the expected answer is the empty set (E-04); a diff appearing there means the classification changed and must be explained.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff .aw/system/workflows/handoff/handoff.md`; the pasted output of `git grep -n` for every old legacy name, with each remaining hit labelled REVERT-AFTER (rule letter) or generated-`STATUS.md`; and, for the `STATUS.md` hits, the explicit note of WHICH were already dangling before this plan (F-10: the two `.md`-without-`.prompt` citations) versus which this rename broke, so the record does not misattribute pre-existing breakage. Also paste the re-run of the out-of-scan-root sweep (`git grep -l` over `agent_workflows/`, `.aw/system/`, `docs/` and root `*.md`, excluding `.aw/records`) confirming `handoff.md` was the only such file.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `python3 -m agent_workflows check prompts --all --agent` showing NO diagnostic other than `check.collisions-not-checked` (F-8: that one is permanent and expected; "zero findings" is the wrong bar and is not accepted as evidence either way); pasted `check all --agent` finding list compared LINE BY LINE with the V-01 baseline, with the comparison shown rather than asserted (no new `rule`+`location` pair); and pasted `python3 -m agent_workflows find <id6>` for every new id6, each returning exactly one `.prompt.md` path. Do NOT include `aw prompts check`: it does not exist (F-9), and an `invalid choice` error pasted here is not evidence of anything.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted final summary line of bare `python3 -m pytest` showing `N passed` and no failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A records migration: the 16 grandfathered legacy-named staged prompts get an id6 in their filename and in their metadata comment, via the shipped `aw rename prompts --to-id6`. The 8 prompts without a metadata comment first get one (one invisible line each). Inbound citations are rewritten by the tool and REVIEWED per occurrence; this edits the text of executed plans (listed in Scope-Paths) purely as reference rewriting, and reverts any rewrite that would falsify history (historical `.agents/` paths, a prefix that named a different artifact, transcripts). It must run after `5xzld0`.

TWO THINGS A HUMAN SHOULD KNOW BEFORE APPROVING, surfaced at review. FIRST, this is NOT purely a records change: one edited file, `.aw/system/workflows/handoff/handoff.md`, is SHIPPED IN THE WHEEL AND THE SDIST (F-11), so approving this approves a one-line change to packaged content. SECOND, the largest single class of edits is TWELVE executed awphysical plans that each carry the same `/plan-review-long` history sentence citing `20260810-1544-01` (F-13); all twelve are classified REVERT-AFTER, meaning the tool will rewrite them and the executor will put them back, so a human reading the final diff should expect twelve files touched-and-restored rather than twelve rewritten history lines.

SCOPE FENCE, a declaration for reconciliation: the `- Scope-Paths:` list, re-derived at execution from the previews. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize --scope-reason`). Declared-but-unmodified citing files are acknowledged with `--scope-ack`.

STOP AND REPORT only for a genuinely unsafe condition: a preview whose rewrite set touches a file another party is concurrently editing, or a citation whose attribution cannot be determined from the repository.

HARD MUST: paste the ACTUAL output for every `V-*`; never claim a command passed without running it. Run the suite BARE as `python3 -m pytest`.

Commit only the Scope-Paths files via `aw commit iyi4hc -- <paths>` (renames staged as moves), never `git add -A`, never push. The plan reaches `executed/` only after every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` conforms, via `aw ipd finalize` (or the runner).
