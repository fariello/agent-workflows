# IPD: Rename the grandfathered legacy-named staged prompts onto the id6-clustered grammar

- Date: 2026-09-26
- Kind: child
- Concern: 16 of the 17 tracked staged prompts still carry the grandfathered legacy `YYYYMMDD-HHMM-NN-<slug>.prompt.md` name and so have no id6: `aw find` cannot resolve them and the research they produced cannot cite them by a stable handle.
- Scope: IN: give the 8 comment-less legacy prompts a leading metadata comment, then convert each legacy prompt with `aw rename prompts <name> --to-id6 --apply`, reviewing every planned citation rewrite and reverting those that would falsify history; fix the one citation outside every scan root. OUT: lowering the prompt_id6 cutover, the prompt-library tree, regenerating the stale `STATUS.md`, any change to tooling.
- Scope-Paths: .aw/records/prompts, DECISIONS.md, .aw/system/workflows/handoff/handoff.md, .aw/records/plans/executed/20260723-instsafe-05-kemhdg-external-install-and-skills-delivery-research-spec.ipd.md, .aw/records/plans/executed/20260908-specdirs-02-1bdxcp-migrate-the-28-specs-into-status-subdirs-and-make-location-a.ipd.md, .aw/records/plans/executed/20260829-lanename-01-j4v6ga-finish-the-local-untracked-lane-rename-in-agent-facing-prose.ipd.md, .aw/records/plans/executed/20260727-untrackwf-00-wn2jto-untrack-workflow-artifacts-orchestrator.ipd.md, .aw/records/plans/executed/20260920-promptid6-01-ubac5n-mint-an-id6-for-staged-prompts-and-migrate-the-prompts-tree.ipd.md, .aw/records/plans/executed/20260829-promptmint-01-jxqdcw-aw-prompts-new-mints-a-conforming-staged-prompt-and-the-rese.ipd.md, .aw/records/plans/executed/20260924-promptadopt-01-dx0u4s-make-staged-prompts-a-full-artifact-organization-and-attenti.ipd.md, .aw/records/plans/executed/20260718-purge-personal-00-3visab-purge-personal-path-and-identity-leaks.ipd.md, .aw/records/plans/executed/20260810-awphysical-00-rma3j4-physical-aw-hierarchy-and-migration-orchestrator.ipd.md, .aw/records/plans/executed/20260810-awphysical-01-cwjnj0-physical-root-ownership-and-git-policy-contract.ipd.md, .aw/records/plans/executed/20260810-awphysical-02-sywony-policy-schema-and-deterministic-context-resolution.ipd.md, .aw/records/plans/executed/20260810-awphysical-04-ru5pmd-canonical-system-installation-and-source-checkout-mode.ipd.md, .aw/records/plans/executed/20260810-awphysical-05-1e9ggw-private-companion-attachment-and-durability.ipd.md, .aw/records/plans/executed/20260810-awphysical-06-fcgala-migration-inventory-and-mapping-tools.ipd.md, .aw/records/plans/executed/20260810-awphysical-07-nhv0qm-transactional-migration-rollback-and-resume.ipd.md, .aw/records/plans/executed/20260810-awphysical-08-mb9xn2-record-producers-and-legacy-reference-cutover.ipd.md, .aw/records/plans/executed/20260810-awphysical-09-2e2jrw-host-adapters-and-clean-delta-integration.ipd.md, .aw/records/plans/executed/20260810-awphysical-10-n3fz8b-post-migration-independent-audit.ipd.md, .aw/records/plans/executed/20260810-awphysical-11-g5zl1u-agent-workflows-source-repository-self-migration.ipd.md, .aw/records/plans/executed/20260810-awphysical-12-pszk6x-documentation-release-and-end-to-end-acceptance.ipd.md, .aw/records/reviews/20260920-promptid6-01-ubac5n-mint-an-id6-for-staged-prompts-and-migrate-the-prompts-tree.review.md
- Item-Dependencies: executed:5xzld0
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: vfmklc
- Set: promptren
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: iyi4hc

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog vfmklc: add metadata comments to the 8 comment-less prompts, then convert the 16 legacy prompts with aw rename --to-id6, reviewing each rewrite.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give every grandfathered legacy-named staged prompt a stable id6 in both its filename and its metadata comment, using the shipped converter `aw rename prompts <name> --to-id6 --apply`, so each is resolvable by `aw find <id6>` and citable from the research it produced, without rewriting any citation that actually names a different artifact or records history.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: preconditions and baseline

- [ ] E-01 Confirm the dependency landed and capture the baseline. Verify plan `5xzld0` is in `.aw/records/plans/executed/` (its shared-legacy-prefix skip, short-handle mapping and fenced-code masking are what keep this migration from corrupting citations, see F-3). Save to `/tmp/opencode/promptren-baseline/`: `git ls-files '.aw/records/prompts/*.prompt.md'`, `python3 -m agent_workflows check prompts --all --agent`, `python3 -m agent_workflows check all --agent`, and (if `5xzld0`'s sibling `mi4s9f` has landed) `python3 -m agent_workflows prompts check --agent`. Re-derive the legacy population: names matching `^\d{8}-\d{4}-\d{2}-` among tracked `.prompt.md` files (16 at authoring).
  - Depends on: none
  - Expected outcome: 5xzld0 executed; baseline files written; the population list recorded with its count.
  - Execution state: pending

- [ ] E-02 Give each legacy prompt that has NO leading `<!-- aw-prompt: ... -->` comment one, BEFORE renaming, so the converter writes the id6 into the file as well as the filename (`prompts.inject_metadata_id6` only writes into an existing comment and deliberately never mints one). Measured at authoring: 8 such files, the 6 oldest `executed/` prompts (`20260722-2317-01`, `20260725-0957-01`, `20260725-2341-01`, `20260727-0655-01`, `20260730-2214-01`, `20260803-0829-01`) and the 2 `superseded/` ones (`20260717-1450-01`, `20260717-1950-01`), whose first line is the AGENTS.md-mandated `RETIRED YYYY-MM-DD: ...` header. Generate each line with `prompts.render_metadata_comment(kind=..., status=<its bucket>, created=<filename date as YYYY-MM-DD>)` (Author/Targets omitted: the renderer omits an unknown field rather than guessing) and insert it as line 1, above any `RETIRED` header, which stays as the first visible line. Kind rule: `research` when the body asks for a researched report, `session-handoff` for the two superseded session files, else `run-once`; record the chosen Kind per file. Do not change any other byte.
  - Depends on: E-01
  - Expected outcome: every legacy prompt now opens with exactly one metadata comment; `aw check prompts --all` shows no new finding (pre-cutover filenames do not require the comment, and `check.prompt-status-mismatch` passes because Status equals the bucket).
  - Execution state: pending

### Task group 2: the rename, one prompt at a time

- [ ] E-03 For EACH legacy prompt, oldest first: run the PREVIEW `python3 -m agent_workflows rename prompts <legacy-name> --to-id6`, save it under `/tmp/opencode/promptren-previews/<legacy-prefix>.txt`, and classify every `would rewrite` line by opening the cited occurrence: KEEP when the text names this prompt (its bare name, its current `.aw/records/prompts/...` path, or its short handle used to mean this prompt); REVERT-AFTER when the occurrence (a) sits inside a historical `.agents/...` path (it records where the file was, and a rewritten path would name a location that never existed), (b) names a DIFFERENT artifact that once shared the legacy prefix, (c) is a quoted command transcript or a measurement table, including this Set's own plan files, or (d) is in this plan file. Known at authoring, to be re-confirmed: `20260722-2317-01` in `DECISIONS.md` and executed plan `kemhdg` names the RESEARCH finding once filed as `.agents/docs/research/20260722-2317-01-...` (now research `0jl8pv`), not this prompt (b); `20260717-1950-01` in executed plan `3visab` sits inside `.agents/plans/pending/20260717-1950-01...` (a); `20260727-0655-01` in executed plan `wn2jto` sits inside `.agents/prompts/pending/...` and the preview prints `WARNING: full-path citation ... cannot be auto-rewritten`, so `--apply` refuses for that one (see E-04). Then apply with `python3 -m agent_workflows rename prompts <legacy-name> --to-id6 --apply --no-commit`, and immediately restore every REVERT-AFTER occurrence to its pre-rename text by hand, verified against the saved preview.
  - Depends on: E-02
  - Expected outcome: each prompt renamed to `YYYYMMDD-<id6>-01-<id6>-<slug>.prompt.md` with `Id: <id6>` in its comment; only KEEP rewrites survive.
  - Execution state: pending

- [ ] E-04 Handle the prompts whose `--apply` refuses on an un-auto-rewritable full-path citation (measured: `20260727-0655-01`, cited as `.agents/prompts/pending/20260727-0655-01-untrack-workflow-artifacts.prompt.md` in a `## Workflow history` line of executed plan `wn2jto`). That citation is historical (rule (a)) and must NOT change, so run the rename with `--no-refs --apply --no-commit` and apply only that prompt's KEEP rewrites by hand. Record each such prompt and why.
  - Depends on: E-03
  - Expected outcome: every legacy prompt converted; no historical path altered.
  - Execution state: pending

- [ ] E-05 Fix the one citation the reference scan cannot reach: `.aw/system/workflows/handoff/handoff.md` cites `.aw/records/prompts/superseded/20260717-1950-01-session-handoff-resume-here.prompt.md` as its "Structural reference", and `.aw/system/` is not in any scan root, so the rename leaves it dangling. Update it to the new name by hand. Re-grep the WHOLE tracked tree (`git grep -n <each old legacy name>`, excluding `.aw/state`, `.aw/worktrees`, `opencode-recovery`) for any other surviving live citation and fix or classify each the same way. The generated `.aw/records/plans/STATUS.md` is left stale deliberately (it is skipped by the matcher and last generated 2026-08-17).
  - Depends on: E-04
  - Expected outcome: no live citation of an old prompt name remains except REVERT-AFTER occurrences and `STATUS.md`.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 Verify: `python3 -m agent_workflows check prompts --all` reports zero findings; `python3 -m agent_workflows check all` reports NO finding beyond the E-01 baseline (it is NOT clean at HEAD: 9 pre-existing findings at authoring, 6 `check.ipd-uncarried-obligation` and 3 `check.id6-identity-slot`, none about prompts); `python3 -m agent_workflows find <id6>` resolves each new id6 to exactly one prompt; and, if available, `python3 -m agent_workflows prompts check` stays at zero findings (the inserted comments are the one permitted non-prompt line).
  - Depends on: E-05
  - Expected outcome: all four hold.
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

DECISION ON THE 8 COMMENT-LESS PROMPTS: add a metadata comment first (E-02). Reasons: (1) without it the id6 lives in the FILENAME ONLY, so `validate_prompt_content` has no `Id:` to compare and cannot detect a later filename/identity divergence, which is the whole point of the conversion; (2) `artifact_rename._read_existing_id6` reads a prompt's id from its comment, so a comment-less file has no in-file identity for any later tool to reuse; (3) the comment is the ONE non-prompt line the purity contract permits (spec `prompt-purity-lint` P4) and is invisible when pasted, so it costs the prompt nothing; (4) it also makes the bucket-vs-Status check apply. The alternative, filename-only, is check-clean (pre-cutover names do not require the comment) but leaves 8 prompts with an identity no content check can see.

## Proposed changes (ordered, validatable)

1. Confirm `5xzld0` landed; baseline (E-01).
2. Metadata comment for the 8 comment-less prompts (E-02).
3. Preview, classify, apply, restore per prompt (E-03), with the `--no-refs` path for fail-loud ones (E-04).
4. Fix the out-of-scan-root citation and sweep for survivors (E-05).
5. `aw check`, `aw find`, `aw prompts check`, suite (E-06, E-07).

## Deferred / out of scope (with reason)

- Lowering `cutovers.prompt_id6` / `check_engine.PROMPT_ID6_CUTOVER_DATE` now that no legacy prompt remains.
  - Carrier-Declined: grandfathering stays harmless with zero legacy prompts, and the per-repo cutover is stamped config for every installed repo, so moving it is a policy change for the maintainer, not a residue of this migration.
- Regenerating the stale tracked `.aw/records/plans/STATUS.md`.
  - Carrier-Declined: it is a generated view, skipped by the reference matcher by design, last regenerated 2026-08-17 and stale on far more than prompt names; regenerating it is unrelated to this rename.

## Scope check

- Over-scope: none.
- Under-scope: the handoff workflow body (F-5) is outside every scan root and is included by hand.

## Required tests / validation

No new test file: this is a data migration performed by already-tested verbs (`tests/test_spec_id6_filenames.py`, `tests/test_prompts_new.py`, and `5xzld0`'s `tests/test_artifact_refs_rewrite.py` cover the converter). Validation is outcome evidence on the real tree: `aw check prompts --all` clean, `aw check all` no worse than baseline, `aw find <id6>` resolving each prompt, and the bare suite, per the maintainer's outcome-only rule.

## Spec / documentation sync

N/A for specs: no spec enumerates prompt filenames. `.aw/records/prompts/README.md` already documents the clustered grammar and the `--to-id6` converter; its sentence "Legacy ... names ... remain valid and are grandfathered" stays true. `.aw/system/workflows/handoff/handoff.md` citation fixed (E-05).

## Open questions

### OQ-01: Rename one prompt at a time or in one batch?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: One at a time (E-03). `aw rename` takes one selector per call, and a prompt renamed earlier can be a CITER of a later one (prompt `20260810-1530-01` cites `20260810-1544-01`), so per-prompt previews are the only way to review each rewrite set against the tree it will actually edit. One commit at the end is fine.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `ls .aw/records/plans/executed/ | grep 5xzld0` showing the plan; `ls /tmp/opencode/promptren-baseline/`; the pasted legacy-population list with its count; and the pasted baseline `check all` finding count.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each of the 8 files, the pasted `head -2` after the edit showing the new `<!-- aw-prompt: Kind: ... | Status: <bucket> | Created: ... -->` line 1 (and the `RETIRED` header as line 2 for the superseded pair), plus pasted `git diff --stat` showing exactly one inserted line per file, and the chosen Kind per file.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `ls /tmp/opencode/promptren-previews/` with one file per prompt; a pasted classification table (prompt, citing file, occurrence, KEEP or REVERT-AFTER with rule letter); and for every REVERT-AFTER row the pasted `git diff <file>` showing that occurrence unchanged relative to HEAD.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `--apply` refusal output for each fail-loud prompt, the pasted `--no-refs --apply` output, and `git diff` of its KEEP citations applied by hand.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff .aw/system/workflows/handoff/handoff.md`, and the pasted output of `git grep -n` for every old legacy name, with each remaining hit labelled REVERT-AFTER (rule letter) or `STATUS.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `python3 -m agent_workflows check prompts --all --agent` with zero findings; pasted `check all --agent` finding list compared line by line with the E-01 baseline (no new entry); pasted `python3 -m agent_workflows find <id6>` for every new id6, each returning exactly one `.prompt.md` path; and, if the verb exists, pasted `python3 -m agent_workflows prompts check; echo rc=$?` with `rc=0`.
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

SCOPE FENCE, a declaration for reconciliation: the `- Scope-Paths:` list, re-derived at execution from the previews. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize --scope-reason`). Declared-but-unmodified citing files are acknowledged with `--scope-ack`.

STOP AND REPORT only for a genuinely unsafe condition: a preview whose rewrite set touches a file another party is concurrently editing, or a citation whose attribution cannot be determined from the repository.

HARD MUST: paste the ACTUAL output for every `V-*`; never claim a command passed without running it. Run the suite BARE as `python3 -m pytest`.

Commit only the Scope-Paths files via `aw commit iyi4hc -- <paths>` (renames staged as moves), never `git add -A`, never push. The plan reaches `executed/` only after every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` conforms, via `aw ipd finalize` (or the runner).
