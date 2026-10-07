# IPD: Remove retired paths, statuses and naming rules from installed READMEs, ignore blocks and install messages

- Date: 2026-10-06
- Kind: child
- Concern: Defects D08 and D09 of research report `l6cbbb`, present at HEAD `474b037a9` in a scratch `.aw`-layout target. D08: the installed `.aw/records/research/README.md` (from `.aw/system/workflows/templates/agents-docs-research-README.md`) still lists `intake | landed, not yet triaged | hot root` and says "Hot states (`intake`/`active`)" and "`INDEX.md` shows the most-recent-N plus intake", although `research_contract.STATUSES` is `{"todo", "active", "reference", "archive"}` and `intake` survives only in `STATUS_NORMALIZATIONS` (`{"intake": "todo"}`); it never says hot states are statuses in the flat root rather than directories; and it cites `.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md`, which no target has (specs are not installed). D09: the install prints "use the gitignored untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/." (`engine.py`) and "Read and execute .agents/workflows/index.md, then the workflow body." (`engine.py`; also `cli.py` "Or from any agent: 'Read and execute .agents/workflows/index.md'"); the installed comms README begins `# .agents/comms/` and says "See the agent-comms convention spec under `.agents/docs/specs/`" (template text in `engine.py`); the root `.gitignore` `aw:untracked` block says "the .agents/plans lifecycle rules say IPDs live under .agents/plans/" and "e.g. .agents/plans/pending/untracked/"; the installed specs README (`agents-docs-specs-README.md`) says specs are "Named `YYYYMMDD-HHMM-NN-<slug>.md`", contradicting the installed AGENTS.md (new specs use the id6 grammar via `aw specs new`).
- Scope: IN: make every one of those texts LAYOUT-AWARE (the `.aw` layout names `.aw/...` paths; a kept legacy `.agents/` layout keeps its own paths, since `--keep-legacy` is supported) or layout-neutral; switch the research README to `todo`, state that hot states are statuses in the flat root (not directories), and label `intake` as a legacy alias; replace the uninstalled spec citation with a reference that resolves in a target (`aw research --help` and the installed `.aw/system/workflows/index.md`); make the specs README state the current id6 grammar minted by `aw specs new` with legacy names grandfathered; repair an already-installed target's research and specs READMEs when (and only when) they are byte-for-byte a known shipped stale text, reusing the `classify_records_root_readme` known-stale pattern; add a bundle-scan test. OUT: `.agents/skills/` (the cross-tool Agent Skills location the installer deliberately writes; NOT retired); the installed workflow bundle `.aw/system/**` (a verbatim copy of this repository's workflow bodies, whose `.agents/` mentions are owned by those bodies' own plans and by Order 07's dangling-reference check); code docstrings and comments citing `.agents/docs/specs/...` (not installed into targets, not agent-facing in a target); the managed AGENTS.md block (Order 07 `ka0g86`).
- Scope-Paths: .aw/system/workflows/templates/agents-docs-research-README.md, .aw/system/workflows/templates/agents-docs-specs-README.md, .aw/records/specs/README.md, agent_workflows/engine.py, agent_workflows/cli.py, tests/test_installed_text_current.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Blocks-Release: f33nrj
- Set: instbugs
- Order: 6
- Highest E allocated: 06
- Author: antigravity/claude-opus-5.5
- Id: jbnkkh
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0
- 2026-10-07 reviewed (aw set): plan-review

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Reviewed at lane HEAD `62409e724`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Re-measured the stale-string inventory with a scratch install (F-06) and an upgrade (F-07). Fixed: no-clobber READMEs are never repaired on upgrade, so existing installs (the reporter's case) would stay stale; added E-06 known-stale repair mirroring `xqf71x` (PR-001); research template should be synced from the already-corrected repo copy, which also fixes the weekly-vs-monthly shard text the plan missed (PR-002); this repo's own specs README carries the same stale naming line (PR-003); `cli._orient` is a once-per-run message needing layout-neutral text, and `InstallPlan` has no layout so the resolver call is named (PR-004); installed `.aw/system/**` bundle scope stated (PR-005); `- Blocks-Release: next` (PR-006); gate gains honesty rule, scope fence, temp HOME and conditional finalize ownership (PR-007).
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 06 of Set `instbugs` after grepping a fresh HEAD install (`474b037a9`) and the install log for every stale string the report names, and locating each string's source.

## Goal

Nothing an install writes or prints for an `.aw`-layout target points at the retired `.agents/` record layout, names a non-canonical research status as current, or contradicts the current spec naming grammar, and a test keeps it that way.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [x] E-01 Re-measure at the execution HEAD: fresh `.aw`-layout install into a temp git repo with output captured; run `grep -rnE "\.agents/(plans|prompts|comms|docs|workflows)" AGENTS.md .gitignore .aw/.gitignore .aw/records <log>` and `grep -n "intake" .aw/records/research/README.md` and `grep -n "Named" .aw/records/specs/README.md`. Also run `aw setup` (or the `_orient` path) and capture its 'Or from any agent' line, since `cli._orient` prints a stale index path too.
  - Depends on: none
  - Expected outcome: the inventory of stale strings pasted (the report's list plus any others found). The AGENTS.md hits are recorded and left to Order 07.
  - Execution state: performed

### Task group 2: fix

- [x] E-02 Research README template: SYNC it from this repository's own `.aw/records/research/README.md`, which already carries the corrected content (review diff: it has `| \`todo\` (legacy \`intake\`) |`, "Hot states (`todo`/`active`)", the shelf-status vs pipeline-position split, monthly `YYYYMM` shards, setid-length bounds, and the `research.frontmatter-key-repeated` check), rather than hand-editing the stale template line by line. While syncing, make the result TARGET-CORRECT: the only spec citation (`.aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md`, which no target has) becomes "see `aw research --help` and `.aw/system/workflows/index.md`"; add one sentence that `todo`/`active` are STATUS values of documents kept flat in this directory's root, not subdirectories, and that external material is dropped in `.aw/inbox/` and filed with `aw adopt`. No em or en dashes (user-facing prose). Note that `research_contract`'s module docstring still says weekly `YYYYMM-Www` while `research_archive` implements monthly `YYYYMM`; the README follows the implementation.
  - Depends on: E-01
  - Expected outcome: the installed research README names only `research_contract.STATUSES` members as statuses (plus `intake` labelled legacy), describes monthly `YYYYMM` shards, and cites only paths a target has.
  - Execution state: performed

- [x] E-03 Specs README template AND this repository's own `.aw/records/specs/README.md` (which carries the same stale "Named `YYYYMMDD-HHMM-NN-<slug>.md` (local time)." line): state that new specs are created with `aw specs new` and named `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md`, and that legacy `YYYYMMDD-HHMM-NN-<slug>.spec.md` names remain valid (grandfathered). Edit only that paragraph in this repository's copy (it is longer than the template; do not replace it with the template).
  - Depends on: E-02
  - Expected outcome: the installed specs README and this repository's specs README agree with the installed AGENTS.md on spec naming.
  - Execution state: performed

- [x] E-04 Layout-aware engine and CLI text: derive the paths in the post-install "untracked lanes" note (`engine.warn_tracking_and_scan`), the "Universal fallback ... Read and execute <workflows index>" line (`engine.print_summary`), the comms README template heading and spec pointer (`engine._COMMS_README_TEMPLATE`, emitted by `collect_scaffold_members`, which already knows `dirs['comms']`), and the root `.gitignore` `aw:untracked` block examples (`engine.UNTRACKED_SAFETY_BODY` via `untracked_safety_sections`) from the target layout. `InstallPlan` carries no layout field, so the print helpers call `engine.resolve_target_layout(plan.repo_root)` (the same resolver `install_into_repo` uses); `untracked_safety_sections` and `_COMMS_README_TEMPLATE` take the layout as a parameter. `cli._orient` prints once per `aw setup` run and may cover several repos, so make it layout-NEUTRAL instead ("Read and execute the workflows index under `.aw/system/workflows/` (or `.agents/workflows/` in a legacy layout)"), so an `.aw` target reads `.aw/records/prompts/untracked/`, `.aw/records/comms/untracked/`, `.aw/system/workflows/index.md`, `.aw/records/plans/...`; the comms README drops the uninstalled-spec pointer in favor of its own content. UPGRADE REACH: the root `.gitignore` block is merged by `engine.merge_aw_block` with a manifest own-hash, so an unedited old block is refreshed automatically, while a user-edited one is preserved with a warning (correct; do not override it). The comms README, by contrast, is written by `_create_if_absent` (no-clobber) and the research/specs READMEs by `ensure_docs_readmes` (no-clobber), so an upgrade NEVER repairs them (review measurement F-07). That repair is E-06.
  - Depends on: E-03
  - Expected outcome: in an `.aw` target, none of these texts contains `.agents/plans`, `.agents/prompts`, `.agents/comms`, `.agents/docs` or `.agents/workflows`; in a `--keep-legacy` target they still name the legacy paths that exist there.
  - Execution state: performed

- [x] E-06 Repair known-stale installed READMEs on upgrade, mirroring plan `xqf71x`'s records-root mechanism (`engine.RETIRED_RECORDS_ROOT_README_HASHES` + `engine.classify_records_root_readme` + the backed-up overwrite in `engine.ensure_plans_readmes`): pin the normalized hashes (`manifest_mod.hash_content`) of the PREVIOUSLY SHIPPED texts of the research README template, the specs README template and `_COMMS_README_TEMPLATE` (enumerate them by census over `git log -p` of each source, as `xqf71x` F-02 did, and record the commits in a comment), and in `ensure_docs_readmes` and the comms README write path classify an existing file as `current` / `known-stale` / `user-owned`, overwriting only `known-stale` after a backup and leaving `user-owned` untouched with `[preserved]`. Generalize the classifier to take the hash set as an argument rather than copying it.
  - Depends on: E-04
  - Expected outcome: an upgrade over a target holding the pre-plan research, specs and comms READMEs replaces them (backup written) and lists them `[overwrite]`; the same upgrade over a hand-edited copy lists `[preserved]` and changes nothing.
  - Execution state: performed

### Task group 3: pin it

- [x] E-05 Add `tests/test_installed_text_current.py`: (a) fresh `.aw`-layout install into a temp git repo with captured stdout; scan the captured output, root `.gitignore`, `.aw/.gitignore` and every file under `.aw/records/` for `\.agents/(plans|prompts|comms|docs|workflows)` and fail on any hit (the managed AGENTS.md block is scanned by Order 07's test, not here); (b) parse the installed research README's status table and assert every status token is in `research_contract.STATUSES` or is explicitly labelled as a legacy alias present in `STATUS_NORMALIZATIONS`; (c) upgrade case: install with the PRE-plan engine's outputs (seed the old `aw:untracked` block AND write the pre-plan research, specs and comms README bytes, recorded as test fixtures), reinstall, assert the scan is clean and each README is listed `[overwrite]`; (d) the same with a one-line user edit to each README, asserting `[preserved]` and unchanged bytes; (e) a `--keep-legacy` target still names `.agents/` paths in the untracked-lanes note and the fallback line. Prove (a) can fail by restoring the old post-install note and pasting the failure.
  - Depends on: E-06
  - Expected outcome: the new tests pass; the mutation fails (a); no test reads production source (the scan reads INSTALLED output in a temp repo, which is the product's observable behavior).
  - Execution state: performed

## Project conventions discovered (Step 0)

- The installer supports both layouts (`--to-aw`, `--keep-legacy`); `agents_pointer_prose(target_layout)` and `update_agents_pointer(..., target_layout=...)` already branch on the layout, so the fix reuses that value.
- `research_contract` is the status authority (`STATUSES`, `HOT_STATUSES`, `STATUS_NORMALIZATIONS`); the rename to `todo` was rstodo Order `p3o9je`.
- `.agents/skills/` is written on purpose for cross-tool skill discovery (scratch install wrote `.agents/skills/*/SKILL.md`); it is excluded from the scan.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Research README template uses `intake` and cites an uninstalled spec. | `agents-docs-research-README.md` line 38 "| `intake` | landed, not yet triaged | hot root |", lines 43-44, line 9 spec path |
| F-02 | Install log prints retired lane paths and fallback. | scratch log line "or use the gitignored untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/."; upgrade log "Read and execute .agents/workflows/index.md, then the workflow body." |
| F-03 | Installed comms README and root `.gitignore` block cite `.agents/`. | scratch `.aw/records/comms/README.md` line 1 `# .agents/comms/`, line 52 "spec under `.agents/docs/specs/`"; root `.gitignore` "e.g. .agents/plans/pending/untracked/" |
| F-04 | Specs README naming is the legacy grammar. | scratch `.aw/records/specs/README.md` line 6 "Named `YYYYMMDD-HHMM-NN-<slug>.md` (local time)." |
| F-05 | The INDEX "COMMITTED" advice the report quotes is already gone. | installed research README: "Both are GENERATED, GITIGNORED, LOCAL views" (D15 second half fixed at HEAD) |
| F-06 | (review) Re-measured at lane HEAD `62409e724`: a fresh `.aw` install (temp HOME) has exactly these hits: log "untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/." and "Read and execute .agents/workflows/index.md"; root `.gitignore` lines 10 and 23; `.aw/records/comms/README.md` lines 1 and 52. Sources: `engine.UNTRACKED_SAFETY_BODY`, `engine.warn_tracking_and_scan`, `engine.print_summary`, `engine._COMMS_README_TEMPLATE`; plus `cli._orient` "Or from any agent: 'Read and execute .agents/workflows/index.md'". | scratch install + `grep -rnoE` |
| F-07 | (review) Upgrades never repair these READMEs: after committing an install and appending a line to the research README, a re-install printed `[no change] .aw/records/research/README.md` and `[no change] .aw/records/specs/README.md` and left both bytes unchanged. Without E-06, the plan fixes new installs only, while the downstream install that reported D08/D09 is an existing one. | scratch upgrade; `engine.ensure_docs_readmes` `if readme_path.is_file(): skipped.append(...)`; `engine._create_if_absent` |
| F-08 | (review) This repository's own `.aw/records/research/README.md` is already corrected (todo, monthly shards, pipeline position) and diverges from the shipped template, so the template is the stale copy. This repository's `.aw/records/specs/README.md` carries the same stale "Named `YYYYMMDD-HHMM-NN-<slug>.md`" line as the template. | `diff` template vs repo copy |

## Proposed changes (ordered, validatable)

1. Research README template synced from the corrected repo copy, made target-correct (E-02).
2. Specs README, template and repo copy (E-03).
3. Layout-aware engine and CLI text (E-04).
4. Known-stale README repair on upgrade (E-06).
5. Bundle scan, status and upgrade tests (E-05).

## Deferred / out of scope (with reason)

- THE MANAGED AGENTS.md BLOCK and the general dangling-reference check (which also covers `.agents/` mentions inside the installed `.aw/system/**` bundle).
  - Carrier: ka0g86

## Scope check

- Over-scope: none.
- Under-scope: code docstrings in `agent_workflows/*.py` that cite `.agents/docs/specs/...` are not installed into a target and are not agent-facing there; left alone. The `research_contract` module docstring's weekly-shard wording is stale but is code, not installed text; left alone. E-02's `.aw/inbox/` pointer names a directory that sibling `xzlu9b` (Order 05) creates in targets; no `- Item-Dependencies:` edge is added because the pointer is correct prose either way (the AGENTS.md block already names the lane) and the orchestrator `i99ykd` child table records this plan as dependency-free; if `xzlu9b` has not executed, the executor states so in V-02.

## Required tests / validation

- `tests/test_installed_text_current.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- N/A for specs: the READMEs are brought into line with existing specs and `research_contract`. This repository's `.aw/records/specs/README.md` naming paragraph is corrected (E-03).

## Open questions

### OQ-01: Should legacy-layout targets also be moved off `.agents/` text?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: no. A `--keep-legacy` target really has `.agents/` paths, so naming them there is correct; the defect is naming them in an `.aw` target.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: PASTE the pre-edit grep inventory with the HEAD sha.
  - Observed evidence:
```
Pre-edit inventory measured at HEAD 0a2f8634091c4b4d721faf9bfae3432480817c84:
1. Root .gitignore:
# <!-- aw:untracked -->
# agent-workflows git-tracks IPDs, prompts, and research by default; use an
# untracked/ sibling or an untracked marker for provisional or sensitive work:
.agents/prompts/untracked/
.agents/comms/untracked/
*.untracked
*.untracked.*
*untracked*/**
# <!-- /aw:untracked -->

2. Installed comms README (.aw/records/comms/README.md):
Line 1: # .agents/comms/
Line 178: See the agent-comms convention spec under `.agents/docs/specs/` for the full definition.

3. Installed research README (.aw/records/research/README.md):
Line 37: spec `.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md`
Line 66: | `intake` | landed, not yet triaged | hot root |
Line 68: | `reference` | cold but it mattered (durable provenance) | `reference/YYYYMM-Www/` weekly shard |
Line 69: | `archive` | cold and just-in-case (dead-end, rejected) | `archive/YYYYMM-Www/` weekly shard |
Line 71: Hot states (`intake`/`active`) stay flat at this directory's root and cluster by name. Cold states live in weekly `YYYYMM-Www` shards.

4. Installed specs README (.aw/records/specs/README.md):
Line 5: Named `YYYYMMDD-HHMM-NN-<slug>.md` (local time).

5. Post-install log / CLI guidance:
- warn_tracking_and_scan: 'or use the gitignored untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/.'
- _orient: 'Or from any agent: 'Read and execute .agents/workflows/index.md''
- print_summary: 'Universal fallback ... Read and execute .agents/workflows/index.md, then the workflow body.'
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the installed research README's states table, shard sentence, the new flat-root sentence and citation from a post-edit fresh install, plus `grep -n 'specs/' <installed research README>` returning nothing.
  - Observed evidence:
```
1. States table in installed .aw/records/research/README.md:
### Shelf status

`status:` frontmatter, tool-owned for answer documents, is one of:

| State | Meaning | On disk |
|-------|---------|---------|
| `todo` (legacy `intake`) | landed, not yet triaged | hot root |
| `active` | informing in-flight work | hot root |
| `reference` | cold but it mattered (durable provenance) | `reference/YYYYMM/` monthly shard |
| `archive` | cold and just-in-case (dead-end, rejected) | `archive/YYYYMM/` monthly shard |

2. Shard sentence and flat-root sentence:
Hot states (`todo`/`active`) are status values of documents kept flat at this directory's root (not subdirectories) and cluster by name. Cold states live in monthly `YYYYMM` shards. `INDEX.md` shows the most-recent-N plus todo and includes `reference`; `archive` is excluded from the hot glance but present in `INDEX.json`.

3. Target-correct citation:
Research artifacts follow the grammar (see `aw research --help` and `.aw/system/workflows/index.md`):

4. Inbox pointer:
External artifacts, prompts, or research from outside the repository are dropped in `.aw/inbox/` and adopted with `aw adopt` into this records tree. (Note: sibling xzlu9b owns creating .aw/inbox/; pointer is correct prose either way).

5. grep -n 'specs/' on installed research README:
0 hits (empty).
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the installed specs README naming paragraph and the `git diff` of this repository's `.aw/records/specs/README.md`.
  - Observed evidence:
```
1. Installed specs README naming paragraph:
New specs are created with `aw specs new` and named `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md`. Legacy `YYYYMMDD-HHMM-NN-<slug>.spec.md` names remain valid (grandfathered).

2. git diff .aw/records/specs/README.md:
diff --git a/.aw/records/specs/README.md b/.aw/records/specs/README.md
index 82dfb5d4d..f769f36c3 100644
--- a/.aw/records/specs/README.md
+++ b/.aw/records/specs/README.md
@@ -3,7 +3,7 @@
  Design specifications and RFC-style documents. This is the `spec` workflow's home for detailed
  proposals that are larger than an IPD and describe a design or contract before implementation.

-Named `YYYYMMDD-HHMM-NN-<slug>.md` (local time).
+New specs are created with `aw specs new` and named `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md`. Legacy `YYYYMMDD-HHMM-NN-<slug>.spec.md` names remain valid (grandfathered).

  Specs describe intended design and rationale. When a spec is implemented, the implementation plan
  (IPD) and its walkthrough carry the execution record; the spec remains as the design reference.
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the E-01 grep re-run on a post-edit fresh `.aw` install and its log (no hits outside AGENTS.md), and the same lines from a `--keep-legacy` install showing legacy paths, plus the new `cli._orient` line.
  - Observed evidence:
```
1. Grep re-run on fresh .aw install and log:
0 retired path hits in installed target files outside AGENTS.md and uninstalled .aw/system/workflows/** bodies.
Post-install log:
Note: agent-workflows git-tracks IPDs, prompts, and research by default.
  This is deliberate (durable, travels with the repo, auditable), but it means you and
  especially your agents should be careful what goes into those files. For sensitive or
  provisional content, use a safety valve instead of committing it:
    - name it with the untracked marker: foo.untracked.md / scratch.untracked / a
      directory whose name contains 'untracked' (see the .gitignore block);
    - or use the gitignored untracked lanes: .aw/records/prompts/untracked/ and .aw/records/comms/untracked/.
...
Universal fallback (any agent):
  Read and execute .aw/system/workflows/index.md, then the workflow body.

2. Lines from --keep-legacy install:
    - or use the gitignored untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/.
...
Universal fallback (any agent):
  Read and execute .agents/workflows/index.md, then the workflow body.

3. cli._orient line:
term.say("  Or from any agent: 'Read and execute the workflows index under .aw/system/workflows/ (or .agents/workflows/ in a legacy layout)'")
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE the census (commit list and hash per source text), then an upgrade over a seeded pre-plan target listing the three READMEs `[overwrite]` with the backup paths, and an upgrade over a hand-edited copy listing `[preserved]` with `cmp` showing bytes unchanged.
  - Observed evidence:
```
1. Census of historical template hashes (manifest_mod.hash_content):
- Research README template (agents-docs-research-README.md):
  28af2a1b5bc6ead0f982eba1161b843263c8d368727a3fd81a2bf75346ac4761 (f4322ea25ce3)
  d7bcf56ff1becef6a471840a1a31bcb92d8a0133b39210ebb607b3c5e151893f (0bc466182913)
  2b356d40150f909a65960ad21fee7630d73d2c313d22603fb36a6a595bfef3e9 (324ef2eb4cea)
  bd65fd0abf7ea822f9e8b747f17624056ac0faf45024e4e029a4f1ad2a86eeb7 (e2a362bf46a8)
  aee37f6b670a6b4d4628664c39343de93c7e0bf31d8513c9623e8a2a9c3d629b (f296f6f403c2)
- Specs README template (agents-docs-specs-README.md):
  b15c3f096387acba7a9db151e889789d932d99daa31541b5c9226f657688188f (324ef2eb4cea)
  c51070d154caa8c96183c03ff7d17374728daa8bfa3daa5963dddde200cade8c (e2a362bf46a8)
  c87a4e82e737915e72317be42de62a4d9c89789644d7a662a375d9dee15ed116 (f296f6f403c2)
- Comms README template (_COMMS_README_TEMPLATE):
  73aa23045e247db4210cab5759b7a4993c4776179b7f6d71ed0a6421cb9ba235 (15df1952fde5 / 3fb5dd3b)
  60abf532757860d74e0296fbd41ab290dc8fd0eaba80b986264f299d5fbf4725 (a4b6df4cea5c / 9bb36273)
  e20b45953b4860749b8c4b44a655cd67ab83cb9c21b1b48d7863c8637ab5324d (c3bff2528b76 / 06b22eebd)

2. Upgrade over seeded pre-plan target:
[overwrite] .aw/records/research/README.md
[overwrite] .aw/records/specs/README.md
[overwrite] .aw/records/comms/README.md
Backups saved to .agent-workflows-installer-backups/

3. Upgrade over hand-edited copy:
[preserved] .aw/records/research/README.md
[preserved] .aw/records/specs/README.md
[preserved] .aw/records/comms/README.md
Bytes verified identical (cmp identical).
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
```
1. Narrowed test run (tests/test_installed_text_current.py):
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=1675402257
rootdir: <worktree-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collecting 5 items                                                             collected 5 items

tests/test_installed_text_current.py::InstalledTextCurrentTests::test_installed_research_readme_status_table PASSED [ 20%]
tests/test_installed_text_current.py::InstalledTextCurrentTests::test_upgrade_preserves_user_customized_readmes PASSED [ 40%]
tests/test_installed_text_current.py::InstalledTextCurrentTests::test_fresh_install_clean_scan PASSED [ 60%]
tests/test_installed_text_current.py::InstalledTextCurrentTests::test_upgrade_replaces_known_stale_readmes PASSED [ 80%]
tests/test_installed_text_current.py::InstalledTextCurrentTests::test_keep_legacy_retains_legacy_paths PASSED [100%]

============================== 5 passed in 44.74s ==============================

2. Mutation test failure:
=================================== FAILURES ===================================
___________ InstalledTextCurrentTests.test_fresh_install_clean_scan ____________
...
E       AssertionError: Lists differ: ['stdout/stderr:364: - or use the gitignor[73 chars]d/.'] != []
E       First list contains 1 additional elements.
E       First extra element 0:
E       'stdout/stderr:364: - or use the gitignored untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/.'
...
=========================== short test summary info ============================
FAILED tests/test_installed_text_current.py::InstalledTextCurrentTests::test_fresh_install_clean_scan
============================== 1 failed in 6.23s ===============================

3. Bare pytest summary line against baseline:
Baseline: 6255 passed, 2 skipped, 3 warnings in 303.58s
Post-edit: 6260 passed, 2 skipped, 3 warnings in 580.94s (0:09:40)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: D08 and D09 are the same defect class (installed text that names retired or wrong things) with one shared test fixture and scan.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in dependency order (E-01, E-02, E-03, E-04, E-06, E-05). Commit only files changed for this plan through `aw commit jbnkkh -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output does not satisfy any item. Run every real install with `AW_NO_REEXEC=1` and `HOME` pointed at a temp dir. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize jbnkkh`, never by a hand `git mv`.
